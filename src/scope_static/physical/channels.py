from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping

import numpy as np

from ..numerics import NUMERICAL_ZERO, positive_floor, probability_floor


Array = np.ndarray

READOUT_MECHANISM_IDS = {"M13", "M14", "M15", "M16"}


@dataclass(frozen=True)
class MechanismSpec:
    """Oracle physical mechanism attached to a local teacher location."""

    mechanism_id: str
    name: str
    num_qubits: int
    parameters: Mapping[str, object] = field(default_factory=dict)
    instruction: str | None = None
    qubits: tuple[int, ...] = ()
    circuit_id: int = 0
    probe_indices: tuple[int, ...] = ()

    def audit_dict(self) -> dict[str, object]:
        return {
            "mechanism_id": self.mechanism_id,
            "name": self.name,
            "num_qubits": int(self.num_qubits),
            "parameters": {str(key): _json_value(value) for key, value in self.parameters.items()},
            "instruction": self.instruction,
            "qubits": [int(q) for q in self.qubits],
            "circuit_id": int(self.circuit_id),
            "probe_indices": [int(idx) for idx in self.probe_indices],
        }


def mechanism_channel(spec: MechanismSpec) -> dict[str, object]:
    """Return a lightweight channel representation for PTM/fingerprint audits."""

    mech = str(spec.mechanism_id)
    params = dict(spec.parameters)
    if mech == "M0":
        p_x = float(params.get("p_x", params.get("p", 0.002) / 3.0))
        p_y = float(params.get("p_y", params.get("p", 0.002) / 3.0))
        p_z = float(params.get("p_z", params.get("p", 0.002) / 3.0))
        return {"kind": "kraus", "kraus": pauli_stochastic_kraus({"X": p_x, "Y": p_y, "Z": p_z})}
    if mech == "M1":
        return {"kind": "unitary", "unitary": rzz_unitary(float(params.get("epsilon", 0.04)))}
    if mech == "M2":
        return {"kind": "unitary", "unitary": rx_unitary(float(params.get("epsilon", 0.035)))}
    if mech == "M3":
        return {"kind": "unitary", "unitary": rz_unitary(float(params.get("epsilon", 0.035)))}
    if mech == "M4":
        return {"kind": "kraus", "kraus": amplitude_damping_kraus(float(params.get("gamma", 0.015)))}
    if mech == "M5":
        return {"kind": "kraus", "kraus": custom_non_pauli_kraus(float(params.get("eta", 0.02)))}
    if mech == "M6":
        return {"kind": "kraus", "kraus": two_qubit_depolarizing_kraus(float(params.get("p", 0.006)))}
    if mech == "M7":
        return {
            "kind": "unitary",
            "unitary": rxx_ryy_unitary(
                theta_x=float(params.get("epsilon_x", params.get("epsilon", 0.025))),
                theta_y=float(params.get("epsilon_y", float(params.get("epsilon", 0.025)) * 0.7)),
            ),
        }
    if mech == "M8":
        if int(spec.num_qubits) == 2:
            return {"kind": "unitary", "unitary": rzz_unitary(float(params.get("epsilon", 0.02)))}
        return {"kind": "unitary", "unitary": rz_unitary(float(params.get("epsilon", 0.02)))}
    if mech == "M9":
        return {"kind": "kraus", "kraus": correlated_relaxation_kraus(float(params.get("gamma", 0.01)))}
    if mech == "M10":
        axis = str(params.get("axis", "rx")).lower()
        angle = float(params.get("epsilon", params.get("epsilon_mean", 0.03)))
        return {"kind": "unitary", "unitary": rx_unitary(angle) if axis == "rx" else rz_unitary(angle)}
    if mech == "M11":
        return {"kind": "kraus", "kraus": pauli_stochastic_kraus({"Z": float(params.get("p_z", params.get("p", 0.0025)))})}
    if mech == "M12":
        axis = str(params.get("axis", "rx")).lower()
        angle = float(params.get("epsilon", 0.028))
        return {"kind": "unitary", "unitary": rx_unitary(angle) if axis == "rx" else rz_unitary(angle)}
    if mech in READOUT_MECHANISM_IDS:
        p = float(params.get("p", 0.02))
        p0_to_1 = p if mech in {"M13", "M15", "M16"} else NUMERICAL_ZERO
        p1_to_0 = p if mech in {"M14", "M15"} else NUMERICAL_ZERO
        if mech == "M16":
            p1_to_0 = 0.5 * p
        return {
            "kind": "readout",
            "matrix": readout_bias_matrix(
                p0_to_1=float(params.get("p0_to_1", p0_to_1)),
                p1_to_0=float(params.get("p1_to_0", p1_to_0)),
            ),
        }
    if mech == "M17":
        return {"kind": "kraus", "kraus": pauli_stochastic_kraus({"X": float(params.get("p", 0.018))})}
    if mech == "M18":
        return {"kind": "unitary", "unitary": rx_unitary(float(params.get("epsilon", 0.025)))}
    if mech == "M19":
        return {"kind": "kraus", "kraus": weak_type4_mixing_kraus(float(params.get("eta", 0.006)))}
    raise ValueError(f"unknown physical mechanism id {spec.mechanism_id!r}")


def rzz_unitary(theta: float) -> Array:
    """Return RZZ(theta) = exp(-i theta ZZ / 2)."""

    phase_minus = np.exp(-0.5j * float(theta))
    phase_plus = np.exp(0.5j * float(theta))
    return np.diag([phase_minus, phase_plus, phase_plus, phase_minus]).astype(np.complex128)


def rx_unitary(theta: float) -> Array:
    half = 0.5 * float(theta)
    c = math.cos(half)
    s = math.sin(half)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=np.complex128)


def rz_unitary(theta: float) -> Array:
    half = 0.5 * float(theta)
    return np.diag([np.exp(-1j * half), np.exp(1j * half)]).astype(np.complex128)


def rxx_unitary(theta: float) -> Array:
    return _two_pauli_rotation(theta, "X")


def ryy_unitary(theta: float) -> Array:
    return _two_pauli_rotation(theta, "Y")


def rxx_ryy_unitary(*, theta_x: float, theta_y: float) -> Array:
    return ryy_unitary(float(theta_y)) @ rxx_unitary(float(theta_x))


def pauli_stochastic_kraus(probabilities: Mapping[str, float]) -> list[Array]:
    """Kraus operators for a one-qubit stochastic Pauli channel."""

    paulis = _single_qubit_paulis()
    probs = {str(key).upper(): float(value) for key, value in probabilities.items()}
    error_probability = sum(probability_floor(probs.get(key, NUMERICAL_ZERO)) for key in ("X", "Y", "Z"))
    if error_probability > 1.0 + 1e-12:
        raise ValueError("stochastic Pauli probabilities sum to more than one")
    kraus = [math.sqrt(positive_floor(1.0 - error_probability)) * paulis["I"]]
    for key in ("X", "Y", "Z"):
        p = probability_floor(probs.get(key, NUMERICAL_ZERO))
        if p >= NUMERICAL_ZERO:
            kraus.append(math.sqrt(p) * paulis[key])
    return [np.asarray(k, dtype=np.complex128) for k in kraus]


def amplitude_damping_kraus(gamma: float) -> list[Array]:
    g = probability_floor(float(gamma))
    return [
        np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - g)]], dtype=np.complex128),
        np.array([[0.0, math.sqrt(g)], [0.0, 0.0]], dtype=np.complex128),
    ]


def custom_non_pauli_kraus(eta: float) -> list[Array]:
    """A small coherent/non-Pauli CPTP perturbation for hard optional tests."""

    e = probability_floor(float(eta))
    base = amplitude_damping_kraus(e)
    rotate = rz_unitary(0.37) @ rx_unitary(0.23)
    return [item @ rotate for item in base]


def two_qubit_depolarizing_kraus(probability: float) -> list[Array]:
    p = probability_floor(float(probability))
    paulis = _single_qubit_paulis()
    labels = [(left, right) for left in ("I", "X", "Y", "Z") for right in ("I", "X", "Y", "Z")]
    non_identity = [(left, right) for left, right in labels if not (left == "I" and right == "I")]
    kraus = [math.sqrt(positive_floor(1.0 - p)) * np.eye(4, dtype=np.complex128)]
    each = p / len(non_identity)
    for left, right in non_identity:
        kraus.append(math.sqrt(each) * np.kron(paulis[left], paulis[right]))
    return kraus


def correlated_relaxation_kraus(gamma: float) -> list[Array]:
    g = probability_floor(float(gamma))
    k0 = np.diag([1.0, 1.0, 1.0, math.sqrt(1.0 - g)]).astype(np.complex128)
    k1 = np.zeros((4, 4), dtype=np.complex128)
    k1[0, 3] = math.sqrt(g)
    return [k0, k1]


def weak_type4_mixing_kraus(eta: float) -> list[Array]:
    e = probability_floor(float(eta))
    rotate = rz_unitary(0.17) @ rx_unitary(0.11)
    paulis = _single_qubit_paulis()
    return [
        math.sqrt(positive_floor(1.0 - 2.0 * e)) * rotate,
        math.sqrt(e) * paulis["X"] @ rotate,
        math.sqrt(e) * paulis["Z"] @ rotate,
    ]


def readout_bias_matrix(*, p0_to_1: float, p1_to_0: float) -> Array:
    p01 = probability_floor(float(p0_to_1))
    p10 = probability_floor(float(p1_to_0))
    return np.array([[1.0 - p01, p01], [p10, 1.0 - p10]], dtype=np.float64)


def _single_qubit_paulis() -> dict[str, Array]:
    return {
        "I": np.eye(2, dtype=np.complex128),
        "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        "Y": np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128),
        "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
    }


def _two_pauli_rotation(theta: float, label: str) -> Array:
    one = _single_qubit_paulis()
    pauli = np.kron(one[label], one[label])
    return (math.cos(0.5 * float(theta)) * np.eye(4) - 1j * math.sin(0.5 * float(theta)) * pauli).astype(np.complex128)


def _json_value(value: object) -> object:
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)

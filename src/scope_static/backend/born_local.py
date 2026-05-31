from __future__ import annotations

import math
import re
from typing import Iterable

import numpy as np

from ..numerics import NUMERICAL_ZERO
from scope_static.backend.channels import MechanismSpec, mechanism_channel, rx_unitary, ry_unitary, rz_unitary, rzz_unitary
from scope_static.backend.mechanism_catalog import IMPLEMENTED_MECHANISM_IDS


BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH = 1
BORN_LOCAL_DEPTH_SEMANTICS = (
    "Born-local uses one explicit local context: probe preparation, one ideal "
    "local operation when applicable, one mechanism channel/readout, then the "
    "local POVM. It does not compose hidden depth layers."
)
BORN_LOCAL_UNSUPPORTED_MECHANISM_REASONS = {
    "M11": (
        "spectator_crosstalk_rz_or_zz needs an explicit spectator contract "
        "covering victim qubit, aggressor operation or edge, and whether the "
        "observable local support is the one-qubit RZ victim or the two-qubit "
        "ZZ spectator pair"
    )
}

BORN_LOCAL_SUPPORTED_MECHANISMS = tuple(mech for mech in IMPLEMENTED_MECHANISM_IDS if mech not in BORN_LOCAL_UNSUPPORTED_MECHANISM_REASONS)


def born_local_outcome_probabilities(
    spec: MechanismSpec,
    probe_name: str,
    *,
    theta: float = 0.18,
    circuit_depth: int = BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH,
    num_qubits: int | None = None,
    physical_qubits: Iterable[int] | None = None,
) -> np.ndarray:
    """Exact local Born probabilities for one mechanism under one probe.

    The returned vector is ordered as ``[p0, p1]`` for one-qubit mechanisms and
    ``[p00, p01, p10, p11]`` for two-qubit mechanisms, with the mechanism qubit
    order matching ``physical_qubits``/``spec.qubits``.
    """

    _validate_born_local_circuit_depth(circuit_depth)
    qubits = _qubit_tuple(spec, physical_qubits)
    width = int(spec.num_qubits)
    if width not in {1, 2}:
        raise ValueError("Born-local teacher only supports one- and two-qubit mechanisms")
    if spec.mechanism_id not in set(BORN_LOCAL_SUPPORTED_MECHANISMS):
        raise ValueError(f"Born-local teacher does not support mechanism {spec.mechanism_id!r}")
    n = _num_qubits(num_qubits, qubits)
    if width == 1:
        return _one_qubit_probabilities(spec, str(probe_name), theta=float(theta), num_qubits=n, qubit=qubits[0])
    return _two_qubit_probabilities(spec, str(probe_name), theta=float(theta), num_qubits=n, qubits=qubits[:2])


def born_local_probability_tables(
    spec: MechanismSpec,
    probe_names: Iterable[str],
    *,
    theta: float = 0.18,
    circuit_depth: int = BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH,
    num_qubits: int | None = None,
    physical_qubits: Iterable[int] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return outcome and marginal-``P(bit=1)`` tables for local probes."""

    _validate_born_local_circuit_depth(circuit_depth)
    names = [str(name) for name in probe_names]
    qubits = _qubit_tuple(spec, physical_qubits)
    width = int(spec.num_qubits)
    outcomes = np.asarray(
        [
            born_local_outcome_probabilities(
                spec,
                name,
                theta=float(theta),
                circuit_depth=int(circuit_depth),
                num_qubits=num_qubits,
                physical_qubits=qubits,
            )
            for name in names
        ],
        dtype=np.float64,
    )
    marginals = np.asarray([outcome_marginals(row, width=width) for row in outcomes], dtype=np.float64)
    return outcomes, marginals


def outcome_marginals(probabilities: np.ndarray, *, width: int) -> np.ndarray:
    probs = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if int(width) == 1:
        return np.asarray([float(probs[1])], dtype=np.float64)
    if int(width) != 2:
        raise ValueError("outcome marginals only supports one- and two-qubit outcomes")
    return np.asarray(
        [
            float(probs[2] + probs[3]),
            float(probs[1] + probs[3]),
        ],
        dtype=np.float64,
    )


def outcome_zz_correlation(probabilities: np.ndarray) -> float:
    probs = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if probs.size != 4:
        return 0.0
    return float(probs[0] - probs[1] - probs[2] + probs[3])


def _validate_born_local_circuit_depth(circuit_depth: int) -> None:
    if int(circuit_depth) != BORN_LOCAL_EFFECTIVE_CIRCUIT_DEPTH:
        raise ValueError(
            "Born-local effective circuit depth is exactly 1; "
            "use the configured circuit_depth only as artifact provenance."
        )


def _one_qubit_probabilities(
    spec: MechanismSpec,
    probe_name: str,
    *,
    theta: float,
    num_qubits: int,
    qubit: int,
) -> np.ndarray:
    context = _one_qubit_context(probe_name, qubit=qubit, num_qubits=num_qubits)
    rho = _density(_state(context["prep"]))
    rho = _apply_ideal_one_qubit_operation(rho, spec, qubit=qubit)
    channel = mechanism_channel(spec)
    if channel["kind"] == "readout":
        true_probs = _measure_one_qubit(rho, context["meas"])
        return _normalize_probabilities(true_probs @ np.asarray(channel["matrix"], dtype=np.float64))
    rho = _apply_channel(rho, channel)
    return _measure_one_qubit(rho, context["meas"])


def _two_qubit_probabilities(
    spec: MechanismSpec,
    probe_name: str,
    *,
    theta: float,
    num_qubits: int,
    qubits: tuple[int, int],
) -> np.ndarray:
    context = _two_qubit_context(probe_name, qubits=qubits, num_qubits=num_qubits)
    rho = np.kron(_density(_state(context["prep_left"])), _density(_state(context["prep_right"])))
    if bool(context["active_rzz"]):
        rho = _apply_unitary(rho, rzz_unitary(float(theta)))
        rho = _apply_channel(rho, mechanism_channel(spec))
    return _measure_two_qubit(rho, str(context["meas_left"]), str(context["meas_right"]))


def _apply_ideal_one_qubit_operation(rho: np.ndarray, spec: MechanismSpec, *, qubit: int) -> np.ndarray:
    instruction = str(spec.instruction or "").lower()
    if instruction == "rx":
        return _apply_unitary(rho, rx_unitary(0.13 + 0.01 * (int(qubit) % 3)))
    if instruction == "ry":
        return _apply_unitary(rho, ry_unitary(0.11 + 0.01 * (int(qubit) % 3)))
    if instruction == "rz":
        return _apply_unitary(rho, rz_unitary(0.09 + 0.01 * (int(qubit) % 2)))
    return rho


def _apply_channel(rho: np.ndarray, channel: dict[str, object]) -> np.ndarray:
    kind = str(channel["kind"])
    if kind == "unitary":
        return _apply_unitary(rho, np.asarray(channel["unitary"], dtype=np.complex128))
    if kind == "kraus":
        out = np.zeros_like(rho, dtype=np.complex128)
        for kraus in channel["kraus"]:  # type: ignore[index]
            k = np.asarray(kraus, dtype=np.complex128)
            out = out + k @ rho @ k.conj().T
        return out
    if kind == "readout":
        return rho
    raise ValueError(f"unknown channel kind {kind!r}")


def _apply_unitary(rho: np.ndarray, unitary: np.ndarray) -> np.ndarray:
    u = np.asarray(unitary, dtype=np.complex128)
    return u @ rho @ u.conj().T


def _measure_one_qubit(rho: np.ndarray, axis: str) -> np.ndarray:
    projectors = _projectors(axis)
    return _normalize_probabilities([np.trace(projector @ rho).real for projector in projectors])


def _measure_two_qubit(rho: np.ndarray, left_axis: str, right_axis: str) -> np.ndarray:
    left = _projectors(left_axis)
    right = _projectors(right_axis)
    raw = []
    for left_bit in (0, 1):
        for right_bit in (0, 1):
            projector = np.kron(left[left_bit], right[right_bit])
            raw.append(float(np.trace(projector @ rho).real))
    return _normalize_probabilities(raw)


def _normalize_probabilities(values: Iterable[float]) -> np.ndarray:
    probs = np.asarray(list(values), dtype=np.float64)
    probs = np.nan_to_num(probs, nan=NUMERICAL_ZERO, posinf=1.0, neginf=NUMERICAL_ZERO)
    probs = np.maximum(probs, NUMERICAL_ZERO)
    probs = np.minimum(probs, 1.0)
    total = float(np.sum(probs))
    if total <= NUMERICAL_ZERO:
        return np.full_like(probs, 1.0 / max(1, probs.size), dtype=np.float64)
    return probs / total


def _density(state: np.ndarray) -> np.ndarray:
    ket = np.asarray(state, dtype=np.complex128).reshape(-1, 1)
    return ket @ ket.conj().T


def _state(label: str) -> np.ndarray:
    text = str(label)
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    if text == "Zp":
        return np.asarray([1.0, 0.0], dtype=np.complex128)
    if text == "Zm":
        return np.asarray([0.0, 1.0], dtype=np.complex128)
    if text == "Xp":
        return inv_sqrt2 * np.asarray([1.0, 1.0], dtype=np.complex128)
    if text == "Xm":
        return inv_sqrt2 * np.asarray([1.0, -1.0], dtype=np.complex128)
    if text == "Yp":
        return inv_sqrt2 * np.asarray([1.0, 1.0j], dtype=np.complex128)
    if text == "Ym":
        return inv_sqrt2 * np.asarray([1.0, -1.0j], dtype=np.complex128)
    raise ValueError(f"unknown local prep state {label!r}")


def _projectors(axis: str) -> tuple[np.ndarray, np.ndarray]:
    axis_text = str(axis).upper()
    if axis_text == "Z":
        plus = _state("Zp")
        minus = _state("Zm")
    elif axis_text == "X":
        plus = _state("Xp")
        minus = _state("Xm")
    elif axis_text == "Y":
        plus = _state("Yp")
        minus = _state("Ym")
    else:
        raise ValueError(f"unknown measurement axis {axis!r}")
    return _density(plus), _density(minus)


def _one_qubit_context(probe_name: str, *, qubit: int, num_qubits: int) -> dict[str, str]:
    parsed = _parse_rzz_tomography_probe(probe_name)
    if parsed is not None:
        side = _selected_tomography_side(parsed, int(qubit), int(num_qubits))
        if side == "left":
            return {"prep": str(parsed["prep_left"]), "meas": str(parsed["meas_left"])}
        if side == "right":
            return {"prep": str(parsed["prep_right"]), "meas": str(parsed["meas_right"])}
        return {"prep": "Zp", "meas": "Z"}
    return {
        "prep": _non_tomography_prep(probe_name, qubit=int(qubit)),
        "meas": _non_tomography_measurement_axis(probe_name, qubit=int(qubit)),
    }


def _two_qubit_context(probe_name: str, *, qubits: tuple[int, int], num_qubits: int) -> dict[str, object]:
    parsed = _parse_rzz_tomography_probe(probe_name)
    if parsed is not None:
        left, right = int(qubits[0]), int(qubits[1])
        active = right == left + 1 and _parity_matches(left, str(parsed["parity"]))
        if active:
            return {
                "prep_left": str(parsed["prep_left"]),
                "prep_right": str(parsed["prep_right"]),
                "meas_left": str(parsed["meas_left"]),
                "meas_right": str(parsed["meas_right"]),
                "active_rzz": True,
            }
        left_context = _one_qubit_context(probe_name, qubit=left, num_qubits=num_qubits)
        right_context = _one_qubit_context(probe_name, qubit=right, num_qubits=num_qubits)
        return {
            "prep_left": left_context["prep"],
            "prep_right": right_context["prep"],
            "meas_left": left_context["meas"],
            "meas_right": right_context["meas"],
            "active_rzz": False,
        }
    return {
        "prep_left": _non_tomography_prep(probe_name, qubit=int(qubits[0])),
        "prep_right": _non_tomography_prep(probe_name, qubit=int(qubits[1])),
        "meas_left": _non_tomography_measurement_axis(probe_name, qubit=int(qubits[0])),
        "meas_right": _non_tomography_measurement_axis(probe_name, qubit=int(qubits[1])),
        "active_rzz": True,
    }


def _parse_rzz_tomography_probe(name: str) -> dict[str, str] | None:
    base = _probe_base_name(name)
    match = re.match(r"rzz_tomo_p([XYZ][pm])([XYZ][pm])_m([XYZ])([XYZ])_(even|odd)$", base)
    if match is None:
        return None
    prep_left, prep_right, meas_left, meas_right, parity = match.groups()
    return {
        "prep_left": prep_left,
        "prep_right": prep_right,
        "meas_left": meas_left,
        "meas_right": meas_right,
        "parity": parity,
    }


def _selected_tomography_side(parsed: dict[str, str], qubit: int, num_qubits: int) -> str | None:
    start = 0 if str(parsed["parity"]) == "even" else 1
    for left in range(start, max(0, int(num_qubits) - 1), 2):
        if int(qubit) == left:
            return "left"
        if int(qubit) == left + 1:
            return "right"
    return None


def _parity_matches(left: int, parity: str) -> bool:
    return (int(left) % 2 == 0 and str(parity) == "even") or (int(left) % 2 == 1 and str(parity) == "odd")


def _non_tomography_prep(probe_name: str, *, qubit: int) -> str:
    base = _probe_base_name(probe_name)
    if base in {"x_basis", "full_x"}:
        return "Xp"
    if base in {"y_basis", "full_y"}:
        return "Yp"
    if base == "alternating_x" and int(qubit) % 2 == 0:
        return "Xp"
    return "Zp"


def _non_tomography_measurement_axis(probe_name: str, *, qubit: int) -> str:
    base = _probe_base_name(probe_name)
    if base in {"x_measure", "full_x"}:
        return "X"
    if base in {"y_measure", "full_y"}:
        return "Y"
    if base.startswith("alt_") and len(base) == len("alt_xz"):
        left_axis = base[-2].upper()
        right_axis = base[-1].upper()
        if left_axis in {"X", "Y", "Z"} and right_axis in {"X", "Y", "Z"}:
            return left_axis if int(qubit) % 2 == 0 else right_axis
    if base.startswith("rzz_int_basis_"):
        suffix = base[len("rzz_int_basis_") :].lower()
        if suffix in {"x", "y", "z"}:
            return suffix.upper()
        if suffix in {"xz", "yz", "xy", "yx"}:
            return suffix[0].upper() if int(qubit) % 2 == 0 else suffix[1].upper()
    return "Z"


def _probe_base_name(name: str) -> str:
    text = str(name)
    return text.split(":", 1)[1] if ":" in text else text


def _qubit_tuple(spec: MechanismSpec, physical_qubits: Iterable[int] | None) -> tuple[int, ...]:
    raw = tuple(int(value) for value in (physical_qubits if physical_qubits is not None else spec.qubits))
    if not raw:
        return tuple(range(int(spec.num_qubits)))
    return raw


def _num_qubits(num_qubits: int | None, qubits: tuple[int, ...]) -> int:
    if num_qubits is not None:
        return max(1, int(num_qubits))
    return max(1, max(qubits) + 1 if qubits else 1)

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping

import numpy as np

from ..numerics import NUMERICAL_ZERO, positive_floor, probability_floor
from qec_twin.mechanisms.catalog import READOUT_MECHANISM_IDS
from qec_twin.mechanisms.catalog import mechanism_label_namespace, mechanism_public_label


Array = np.ndarray
M13_DEFAULT_EPSILON_SPAN = 0.018
M13_DEFAULT_DRIFT_VISIBILITY_SCALE = 5.0
ROTATION_AXIS_ALIASES = {
    "x": "rx",
    "rx": "rx",
    "y": "ry",
    "ry": "ry",
    "z": "rz",
    "rz": "rz",
}


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
        public_label = mechanism_public_label(self.mechanism_id)
        label_namespace = mechanism_label_namespace(self.mechanism_id)
        record = {
            "legacy_catalog_id": self.mechanism_id,
            "public_label": public_label,
            "label_namespace": label_namespace,
            "mechanism_id": self.mechanism_id,
            "name": self.name,
            "num_qubits": int(self.num_qubits),
            "parameters": {str(key): _json_value(value) for key, value in self.parameters.items()},
            "instruction": self.instruction,
            "qubits": [int(q) for q in self.qubits],
            "circuit_id": int(self.circuit_id),
            "probe_indices": [int(idx) for idx in self.probe_indices],
        }
        if self.mechanism_id == "M11":
            overlay = _m11_overlay_payload_from_parameters(self.parameters, public_label=public_label)
            if overlay:
                record.update(overlay)
        if self.mechanism_id == "M13":
            record.update(_m13_drift_overlay_payload_from_spec(self, public_label=public_label))
        return record


def canonical_single_qubit_axis(value: object | None, *, default: str = "rx") -> str:
    raw = default if value is None else value
    text = str(raw).strip().lower()
    axis = ROTATION_AXIS_ALIASES.get(text)
    if axis is None:
        raise ValueError("single-qubit rotation axis must be one of x/rx, y/ry, or z/rz")
    return axis


def mechanism_operation_axis(spec: MechanismSpec) -> str:
    params = dict(spec.parameters)
    default = _instruction_default_axis(spec.instruction)
    if spec.mechanism_id == "M14":
        return canonical_single_qubit_axis(
            params.get("operation_axis", params.get("instruction", params.get("axis", default))),
            default="rx",
        )
    return canonical_single_qubit_axis(
        params.get("operation_axis", params.get("axis", default)),
        default="rx",
    )


def mechanism_error_axis(spec: MechanismSpec) -> str:
    params = dict(spec.parameters)
    if spec.mechanism_id == "M14":
        return canonical_single_qubit_axis(params.get("error_axis", params.get("channel_axis")), default="rz")
    if spec.mechanism_id == "M13":
        operation_axis = mechanism_operation_axis(spec)
        requested_axis = canonical_single_qubit_axis(
            params.get("error_axis", params.get("channel_axis", operation_axis)),
            default=operation_axis,
        )
        if requested_axis != operation_axis:
            raise ValueError("M13 drifted coherent overrotation requires channel axis to match operation_axis")
        return operation_axis
    return mechanism_operation_axis(spec)


def _instruction_default_axis(instruction: object | None) -> str:
    text = str(instruction or "rx").strip().lower()
    return ROTATION_AXIS_ALIASES.get(text, "rx")


def mechanism_definition_contract(spec: MechanismSpec) -> dict[str, object]:
    params = dict(spec.parameters)
    if spec.mechanism_id == "M13":
        operation_axis = mechanism_operation_axis(spec)
        channel_axis = mechanism_error_axis(spec)
        epsilon = _m13_epsilon(params)
        epsilon_mean = _m13_epsilon_mean(params)
        epsilon_span = _m13_epsilon_span(params)
        scale = _m13_drift_visibility_scale(params)
        effective_span = _m13_effective_drift_span(params)
        offsets = _m13_drift_offsets(params)
        weights = _m13_drift_weights(params, count=len(offsets))
        return {
            "mechanism_id": "M13",
            "formal_name": "drifted_coherent_overrotation",
            "definition": "context-dependent coherent overrotation attached to the declared operation axis, represented as a row-visible drift mixture",
            "contract_role": "context_conditioned_family",
            "operation_axis": operation_axis,
            "channel_axis": channel_axis,
            "error_axis": channel_axis,
            "drift_parameter": "epsilon",
            "epsilon": epsilon,
            "epsilon_mean": epsilon_mean,
            "epsilon_span": epsilon_span,
            "drift_visibility_scale": scale,
            "effective_epsilon_span": effective_span,
            "angle_offsets": [float(value) for value in offsets],
            "mixture_weights": [float(value) for value in weights],
            "channel_representation": "random_unitary_kraus_mixture" if effective_span > 0.0 else "unitary",
            "drift_overlay_payload_present": bool(effective_span > 0.0),
            "row_level_visible_geometry": "mean_rotation_plus_drift_mixture_curvature",
            "context_dependent": True,
            "operation_dependent": False,
            "single_context_exact_recovery_required": False,
            "claims_standalone_flat_mechanism": False,
            "well_defined": True,
        }
    if spec.mechanism_id == "M14":
        operation_axis = mechanism_operation_axis(spec)
        channel_axis = mechanism_error_axis(spec)
        return {
            "mechanism_id": "M14",
            "formal_name": "operation_dependent_error",
            "definition": "coherent error generator attached to a visible operation axis",
            "operation_axis": operation_axis,
            "channel_axis": channel_axis,
            "error_axis": channel_axis,
            "epsilon": float(params.get("epsilon", 0.028)),
            "context_dependent": False,
            "operation_dependent": True,
            "distinct_from_axis_overrotation": bool(channel_axis != operation_axis),
            "well_defined": bool(channel_axis != operation_axis),
        }
    if spec.mechanism_id == "M11":
        carrier = "rzz_unitary" if int(spec.num_qubits) == 2 else "rz_unitary"
        return {
            "mechanism_id": "M11",
            "formal_name": "spectator_crosstalk_overlay",
            "definition": "non-flat spectator overlay represented scientifically as base_mechanism plus spectator_overlay metadata",
            "contract_role": "overlay_family",
            "overlay_family": "spectator_crosstalk",
            "sampling_surrogate": {
                "carrier_channel": carrier,
                "claims_exact_physical_overlay_channel": False,
                "claims_standalone_flat_mechanism": False,
            },
            "leaf_exact_effect_supported": False,
            "primary_flat_cluster_target": False,
            "well_defined": True,
        }
    return {
        "mechanism_id": str(spec.mechanism_id),
        "formal_name": str(spec.name),
        "instruction": spec.instruction,
        "well_defined": True,
    }


def _m11_overlay_payload_from_parameters(parameters: Mapping[str, object], *, public_label: str) -> dict[str, object]:
    params = dict(parameters)
    if not bool(params.get("spectator_overlay_present", False)):
        return {}
    strength = _first_present(params, "spectator_strength", "strength", "coupling_strength")
    overlay = {
        "present": True,
        "base_mechanism": _first_present(params, "base_mechanism"),
        "victim_relative_location": _first_present(params, "victim_relative_location"),
        "aggressor_relative_location": _first_present(params, "aggressor_relative_location"),
        "coupling_axis": _first_present(params, "coupling_axis"),
        "timing_context": _first_present(params, "timing_context"),
        "spectator_strength": strength,
        "victim_qubit": _first_present(params, "victim_qubit"),
        "aggressor_qubit": _first_present(params, "aggressor_qubit"),
    }
    compact_overlay = {key: _json_value(value) for key, value in overlay.items() if value is not None}
    out = {
        "contract_role": "overlay_family",
        "overlay_family": "spectator_crosstalk",
        "public_effect_family": "spectator_overlay",
        "public_overlay_class": f"{public_label}_overlay",
        "nonflat_public_label": f"spectator_overlay_{public_label}",
        "spectator_overlay_present": True,
        "spectator_overlay": compact_overlay,
        "base_mechanism": compact_overlay.get("base_mechanism"),
        "victim_relative_location": compact_overlay.get("victim_relative_location"),
        "aggressor_relative_location": compact_overlay.get("aggressor_relative_location"),
        "coupling_axis": compact_overlay.get("coupling_axis"),
        "timing_context": compact_overlay.get("timing_context"),
        "spectator_strength": compact_overlay.get("spectator_strength"),
        "claims_standalone_flat_mechanism": bool(params.get("claims_standalone_flat_mechanism", False)),
    }
    if compact_overlay.get("victim_qubit") is not None:
        out["victim_qubit"] = compact_overlay["victim_qubit"]
    if compact_overlay.get("aggressor_qubit") is not None:
        out["aggressor_qubit"] = compact_overlay["aggressor_qubit"]
    return out


def _m13_drift_overlay_payload_from_spec(spec: MechanismSpec, *, public_label: str) -> dict[str, object]:
    params = dict(spec.parameters)
    operation_axis = mechanism_operation_axis(spec)
    channel_axis = mechanism_error_axis(spec)
    epsilon = _m13_epsilon(params)
    epsilon_mean = _m13_epsilon_mean(params)
    epsilon_span = _m13_epsilon_span(params)
    scale = _m13_drift_visibility_scale(params)
    effective_span = _m13_effective_drift_span(params)
    offsets = _m13_drift_offsets(params)
    weights = _m13_drift_weights(params, count=len(offsets))
    overlay = {
        "present": bool(effective_span > 0.0),
        "operation_axis": operation_axis,
        "channel_axis": channel_axis,
        "epsilon": epsilon,
        "epsilon_mean": epsilon_mean,
        "epsilon_span": epsilon_span,
        "drift_visibility_scale": scale,
        "effective_epsilon_span": effective_span,
        "angle_offsets": [float(value) for value in offsets],
        "mixture_weights": [float(value) for value in weights],
        "channel_representation": "random_unitary_kraus_mixture" if effective_span > 0.0 else "unitary",
    }
    compact_overlay = {key: _json_container_value(value) for key, value in overlay.items() if value is not None}
    return {
        "contract_role": "context_conditioned_family",
        "public_effect_family": "context_conditioned_drift",
        "public_overlay_class": f"{public_label}_drift_overlay",
        "nonflat_public_label": f"context_conditioned_drift_{public_label}",
        "drift_overlay_present": bool(effective_span > 0.0),
        "drift_overlay": compact_overlay,
        "operation_axis": operation_axis,
        "channel_axis": channel_axis,
        "drift_strength": float(effective_span),
        "claims_standalone_flat_mechanism": False,
        "single_context_exact_recovery_required": False,
    }


def _first_present(values: Mapping[str, object], *keys: str) -> object | None:
    for key in keys:
        if values.get(key) is not None:
            return values.get(key)
    return None


def mechanism_channel(spec: MechanismSpec) -> dict[str, object]:
    """Return a lightweight channel representation for PTM/fingerprint audits."""

    mech = str(spec.mechanism_id)
    params = dict(spec.parameters)
    if mech == "M0":
        p_x = float(params.get("p_x", params.get("p", 0.002) / 3.0))
        p_y = float(params.get("p_y", params.get("p", 0.002) / 3.0))
        p_z = float(params.get("p_z", params.get("p", 0.002) / 3.0))
        return {"kind": "kraus", "kraus": pauli_stochastic_kraus({"X": p_x, "Y": p_y, "Z": p_z})}
    if mech in READOUT_MECHANISM_IDS:
        p = float(params.get("p", 0.02))
        p0_to_1 = p if mech in {"M1", "M3", "M16"} else NUMERICAL_ZERO
        p1_to_0 = p if mech in {"M2", "M3"} else NUMERICAL_ZERO
        if mech == "M16":
            p1_to_0 = 0.5 * p
        return {
            "kind": "readout",
            "matrix": readout_bias_matrix(
                p0_to_1=float(params.get("p0_to_1", p0_to_1)),
                p1_to_0=float(params.get("p1_to_0", p1_to_0)),
            ),
        }
    if mech == "M4":
        return {"kind": "kraus", "kraus": amplitude_damping_kraus(float(params.get("gamma", 0.015)))}
    if mech == "M5":
        return {"kind": "kraus", "kraus": pauli_stochastic_kraus({"Z": float(params.get("p_z", params.get("p", 0.0025)))})}
    if mech == "M6":
        return {"kind": "unitary", "unitary": rx_unitary(float(params.get("epsilon", 0.035)))}
    if mech == "M7":
        return {"kind": "unitary", "unitary": rz_unitary(float(params.get("epsilon", 0.035)))}
    if mech == "M8":
        return {"kind": "unitary", "unitary": rzz_unitary(float(params.get("epsilon", 0.04)))}
    if mech == "M9":
        return {"kind": "kraus", "kraus": two_qubit_depolarizing_kraus(float(params.get("p", 0.006)))}
    if mech == "M10":
        return {
            "kind": "unitary",
            "unitary": rxx_ryy_unitary(
                theta_x=float(params.get("epsilon_x", params.get("epsilon", 0.025))),
                theta_y=float(params.get("epsilon_y", float(params.get("epsilon", 0.025)) * 0.7)),
            ),
        }
    if mech == "M11":
        if int(spec.num_qubits) == 2:
            return {"kind": "unitary", "unitary": rzz_unitary(float(params.get("epsilon", 0.02))), "definition_contract": mechanism_definition_contract(spec)}
        return {"kind": "unitary", "unitary": rz_unitary(float(params.get("epsilon", 0.02))), "definition_contract": mechanism_definition_contract(spec)}
    if mech == "M12":
        return {"kind": "kraus", "kraus": correlated_relaxation_kraus(float(params.get("gamma", 0.01)))}
    if mech == "M13":
        axis = mechanism_error_axis(spec)
        angle = _m13_epsilon(params)
        contract = mechanism_definition_contract(spec)
        effective_span = float(contract.get("effective_epsilon_span", 0.0))
        if effective_span <= 0.0:
            return {"kind": "unitary", "unitary": _axis_unitary(axis, angle), "definition_contract": contract}
        weights = [float(value) for value in contract.get("mixture_weights", [0.25, 0.5, 0.25])]  # type: ignore[arg-type]
        return {
            "kind": "kraus",
            "kraus": drifted_axis_mixture_kraus(axis, epsilon=angle, effective_span=effective_span, weights=weights),
            "definition_contract": contract,
        }
    if mech == "M14":
        axis = mechanism_error_axis(spec)
        angle = float(params.get("epsilon", 0.028))
        return {"kind": "unitary", "unitary": _axis_unitary(axis, angle), "definition_contract": mechanism_definition_contract(spec)}
    if mech == "M15":
        return {"kind": "kraus", "kraus": custom_non_pauli_kraus(float(params.get("eta", 0.02)))}
    if mech == "M17":
        return {"kind": "kraus", "kraus": reset_to_state_kraus(float(params.get("p", 0.018)), target_state=1)}
    if mech == "M18":
        return {"kind": "unitary", "unitary": rx_unitary(float(params.get("epsilon", 0.025)))}
    if mech == "M19":
        return {"kind": "kraus", "kraus": weak_type4_mixing_kraus(float(params.get("eta", 0.006)))}
    if mech == "M20":
        return {"kind": "unitary", "unitary": ry_unitary(float(params.get("epsilon", 0.03)))}
    if mech == "M21":
        return {"kind": "unitary", "unitary": controlled_phase_error_unitary(float(params.get("epsilon", 0.035)))}
    if mech == "M22":
        return {"kind": "unitary", "unitary": rxx_unitary(float(params.get("epsilon", 0.022)))}
    if mech == "M23":
        return {"kind": "unitary", "unitary": ryy_unitary(float(params.get("epsilon", 0.019)))}
    if mech == "M24":
        return {"kind": "kraus", "kraus": thermal_excitation_kraus(float(params.get("gamma_up", params.get("p", 0.006))))}
    if mech == "M25":
        return {"kind": "kraus", "kraus": pauli_stochastic_kraus({"X": float(params.get("p", 0.006))})}
    if mech == "M26":
        return {"kind": "kraus", "kraus": pauli_stochastic_kraus({"Y": float(params.get("p", 0.006))})}
    if mech == "M27":
        return {"kind": "unitary", "unitary": single_axis_rotation(float(params.get("epsilon", 0.026)), {"X": 1.0, "Z": 1.0})}
    if mech == "M28":
        return {"kind": "unitary", "unitary": two_pauli_rotation(float(params.get("epsilon", 0.015)), "X", "Y")}
    if mech == "M29":
        return {"kind": "unitary", "unitary": two_pauli_rotation(float(params.get("epsilon", 0.018)), "Z", "X")}
    if mech == "M30":
        return {"kind": "unitary", "unitary": two_pauli_rotation(float(params.get("epsilon", 0.016)), "Z", "Y")}
    if mech == "M31":
        return {"kind": "unitary", "unitary": two_pauli_rotation(float(params.get("epsilon", 0.017)), "X", "Z")}
    if mech == "M32":
        return {"kind": "unitary", "unitary": two_pauli_rotation(float(params.get("epsilon", 0.014)), "Y", "Z")}
    if mech == "M33":
        return {"kind": "unitary", "unitary": two_pauli_rotation(float(params.get("epsilon", 0.013)), "Y", "X")}
    if mech == "M34":
        return {"kind": "kraus", "kraus": leakage_relaxation_surrogate_kraus(float(params.get("p", 0.004)))}
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


def ry_unitary(theta: float) -> Array:
    half = 0.5 * float(theta)
    c = math.cos(half)
    s = math.sin(half)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)


def rz_unitary(theta: float) -> Array:
    half = 0.5 * float(theta)
    return np.diag([np.exp(-1j * half), np.exp(1j * half)]).astype(np.complex128)


def rxx_unitary(theta: float) -> Array:
    return two_pauli_rotation(theta, "X", "X")


def ryy_unitary(theta: float) -> Array:
    return two_pauli_rotation(theta, "Y", "Y")


def rxx_ryy_unitary(*, theta_x: float, theta_y: float) -> Array:
    return ryy_unitary(float(theta_y)) @ rxx_unitary(float(theta_x))


def controlled_phase_error_unitary(theta: float) -> Array:
    return np.diag([1.0, 1.0, 1.0, np.exp(-1j * float(theta))]).astype(np.complex128)


def _axis_unitary(axis: str, theta: float) -> Array:
    text = canonical_single_qubit_axis(axis)
    if text == "ry":
        return ry_unitary(float(theta))
    if text == "rz":
        return rz_unitary(float(theta))
    return rx_unitary(float(theta))


def drifted_axis_mixture_kraus(
    axis: str,
    *,
    epsilon: float,
    effective_span: float,
    weights: list[float] | tuple[float, ...] | None = None,
) -> list[Array]:
    span = abs(float(effective_span))
    if span <= 0.0:
        return [_axis_unitary(axis, float(epsilon))]
    raw_weights = list(weights) if weights is not None else [0.25, 0.5, 0.25]
    if len(raw_weights) != 3:
        raw_weights = [0.25, 0.5, 0.25]
    clean = [max(0.0, float(value)) for value in raw_weights]
    total = sum(clean)
    if total <= 0.0:
        clean = [0.25, 0.5, 0.25]
        total = 1.0
    normalized = [value / total for value in clean]
    offsets = (-span, 0.0, span)
    return [
        math.sqrt(weight) * _axis_unitary(axis, float(epsilon) + float(offset))
        for weight, offset in zip(normalized, offsets)
    ]


def single_axis_rotation(theta: float, components: Mapping[str, float]) -> Array:
    paulis = _single_qubit_paulis()
    operator = np.zeros((2, 2), dtype=np.complex128)
    norm_sq = 0.0
    for label, value in components.items():
        coeff = float(value)
        operator = operator + coeff * paulis[str(label).upper()]
        norm_sq += coeff * coeff
    norm = math.sqrt(max(norm_sq, NUMERICAL_ZERO))
    generator = operator / norm
    return (math.cos(0.5 * float(theta)) * np.eye(2) - 1j * math.sin(0.5 * float(theta)) * generator).astype(np.complex128)


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


def phase_damping_kraus(gamma_phi: float) -> list[Array]:
    """Pauli-Z dephasing, parameterized by the Z-error PROBABILITY ``gamma_phi``
    (NOT the canonical phase-damping rate lambda).

    Kraus {sqrt(1-g) I, sqrt(g) Z}: rho -> (1-g) rho + g Z rho Z, contracting the
    Bloch x,y components by (1-2g). A valid, standard Pauli dephasing channel, but
    its argument is a Z-flip probability: it equals ``phase_damping_canonical_kraus``
    with lambda = 4 g (1 - g) for g <= 1/2 (for g > 1/2 they differ by a coherence
    sign, as (1-2g) < 0). For PHYSICAL T1/T2 modeling use ``thermal_relaxation_kraus``
    (which honors 1/T2 = 1/(2 T1) + 1/Tphi).
    """
    g = probability_floor(float(gamma_phi))
    paulis = _single_qubit_paulis()
    return [
        math.sqrt(positive_floor(1.0 - g)) * paulis["I"],
        math.sqrt(g) * paulis["Z"],
    ]


def phase_damping_canonical_kraus(lam: float) -> list[Array]:
    """Canonical phase-damping channel (Nielsen & Chuang), rate ``lam`` in [0,1]:
    K0 = diag(1, sqrt(1-lam)), K1 = diag(0, sqrt(lam)). Populations unchanged;
    off-diagonal coherence contracted by sqrt(1-lam)."""
    l = probability_floor(float(lam))
    return [
        np.array([[1.0, 0.0], [0.0, math.sqrt(positive_floor(1.0 - l))]], dtype=np.complex128),
        np.array([[0.0, 0.0], [0.0, math.sqrt(l)]], dtype=np.complex128),
    ]


def thermal_relaxation_kraus(t: float, t1: float, t2: float) -> list[Array]:
    """Canonical zero-temperature T1/T2 thermal-relaxation channel over gate time
    ``t`` (the standard thermal_relaxation_error). Amplitude damping with
    gamma = 1 - exp(-t/T1) composed with canonical phase damping with
    lambda_phi = 1 - exp(-2 t / Tphi), where 1/Tphi = 1/T2 - 1/(2 T1). Requires the
    physical bound T2 <= 2 T1. Exact map: rho00 -> rho00 + gamma rho11,
    rho11 -> (1-gamma) rho11, rho01 -> exp(-t/T2) rho01."""
    t_, t1_, t2_ = float(t), float(t1), float(t2)
    if not (t1_ > 0.0 and t2_ > 0.0):
        raise ValueError(f"T1, T2 must be positive (T1={t1_}, T2={t2_})")
    if t2_ > 2.0 * t1_ + 1e-12:
        raise ValueError(f"unphysical T2 > 2 T1 (T2={t2_}, T1={t1_})")
    gamma = 1.0 - math.exp(-t_ / t1_)
    inv_tphi = 1.0 / t2_ - 1.0 / (2.0 * t1_)
    lam_phi = 1.0 - math.exp(-2.0 * t_ * inv_tphi) if inv_tphi > 0.0 else 0.0
    ad = amplitude_damping_kraus(gamma)
    pd = phase_damping_canonical_kraus(lam_phi)
    return [p @ a for a in ad for p in pd]  # rho -> PD(AD(rho)); exact thermal map


def thermal_excitation_kraus(gamma_up: float) -> list[Array]:
    g = probability_floor(float(gamma_up))
    return [
        np.array([[math.sqrt(1.0 - g), 0.0], [0.0, 1.0]], dtype=np.complex128),
        np.array([[0.0, 0.0], [math.sqrt(g), 0.0]], dtype=np.complex128),
    ]


def reset_to_state_kraus(probability: float, *, target_state: int) -> list[Array]:
    p = probability_floor(float(probability))
    target = int(target_state)
    if target not in {0, 1}:
        raise ValueError("target_state must be 0 or 1")
    k0 = math.sqrt(positive_floor(1.0 - p)) * np.eye(2, dtype=np.complex128)
    k1 = np.zeros((2, 2), dtype=np.complex128)
    k2 = np.zeros((2, 2), dtype=np.complex128)
    k1[target, 0] = math.sqrt(p)
    k2[target, 1] = math.sqrt(p)
    return [k0, k1, k2]


def leakage_relaxation_surrogate_kraus(probability: float) -> list[Array]:
    p = probability_floor(float(probability))
    return [damp @ phase for damp in amplitude_damping_kraus(p) for phase in phase_damping_kraus(p)]


_QUTRIT_KETS = {k: np.eye(3, dtype=np.complex128)[k] for k in range(3)}


def _qutrit_op(a: int, b: int) -> Array:
    """The 3x3 outer product ``|a><b|`` on the qutrit basis ``{|0>,|1>,|2>}``."""
    return np.outer(_QUTRIT_KETS[a], _QUTRIT_KETS[b].conj())


def _lindbladian_super(hamiltonian: Array, jumps: list[Array]) -> Array:
    """Column-stacking Lindbladian superoperator ``L`` (``vec(A rho B)=(B^T kron A) vec(rho)``).

    ``L = -i(I kron H - H^T kron I) + Σ_k (J_k* kron J_k - 1/2(I kron J_k^dag J_k +
    (J_k^dag J_k)^T kron I))`` -- the generator of the dissipative dynamics
    ``drho/dt = -i[H, rho] + Σ_k (J_k rho J_k^dag - 1/2{J_k^dag J_k, rho})``. Acts on
    the column-stacked ``vec(rho)`` (Fortran order). Source: Wood-Gambetta Lindblad
    leakage model (1704.03081 Eqs.67-68); identical algebra to the validated
    reference ``outputs/teacher_prereg/wg_leakage_channel_reference.py``.
    """
    d = hamiltonian.shape[0]
    eye = np.eye(d, dtype=np.complex128)
    lind = -1j * (np.kron(eye, hamiltonian) - np.kron(hamiltonian.T, eye))
    for jump in jumps:
        jdj = jump.conj().T @ jump
        lind += np.kron(jump.conj(), jump) - 0.5 * (np.kron(eye, jdj) + np.kron(jdj.T, eye))
    return lind


def leakage_channel_super(theta: float, g_seep: float, g_heat: float = 0.0, *, t: float = 1.0) -> Array:
    """The full Wood-Gambetta leakage channel as a column-stacking superoperator ``E = exp(L t)``.

    ``E`` is the exact integral of the Lindbladian generated by a COHERENT ``|1><->|2>``
    exchange plus (optional) dissipative seepage / heating jumps:

      - Hamiltonian ``H = theta (|1><2| + |2><1|)``  -> coherent leakage, carries C_L>0
      - jump ``J_seep = sqrt(g_seep) |1><2|``         -> dissipative seepage ``|2>->|1>`` (WG_L2)
      - jump ``J_heat = sqrt(g_heat) |2><1|``         -> incoherent heating  ``|1>->|2>`` (C_L=0)

    The matrix-exponential ``exp(L t)`` (``scipy.linalg.expm``) is the channel's physical
    action; ``leakage_kraus`` Choi-factorizes it into operator-sum form. CPTP by
    construction (it is the exponential of a Lindbladian).
    """
    import scipy.linalg as _sla  # local import: the WG-channel path is the only scipy user

    hamiltonian = float(theta) * (_qutrit_op(1, 2) + _qutrit_op(2, 1))
    jumps: list[Array] = []
    if float(g_seep) > 0.0:
        jumps.append(math.sqrt(float(g_seep)) * _qutrit_op(1, 2))  # |2> -> |1>  seepage
    if float(g_heat) > 0.0:
        jumps.append(math.sqrt(float(g_heat)) * _qutrit_op(2, 1))  # |1> -> |2>  heating
    return _sla.expm(_lindbladian_super(hamiltonian, jumps) * float(t))


def _super_to_kraus(superop: Array, *, tol: float = NUMERICAL_ZERO) -> list[Array]:
    """Operator-sum (Kraus) decomposition of a 3-level column-stacking superoperator.

    Builds the Choi matrix ``C = Σ_ij E(|i><j|) kron |i><j|`` and eigendecomposes it
    (Hermitian, PSD for a CPTP map): each eigenpair ``(w_k >= tol, V_k)`` yields a Kraus
    ``K_k = sqrt(w_k) reshape(V_k, (3,3))`` (C/row-major, matching the Choi's
    ``kron(E(|i><j|), |i><j|)`` output-outer / input-inner index order). Negligible
    eigenvalues (``<= tol``, the ``NUMERICAL_ZERO`` floor) are dropped, so the returned
    Kraus count is the channel rank (typically 2-5), not a fixed 3.
    """
    dim = 3
    choi = np.zeros((dim * dim, dim * dim), dtype=np.complex128)
    for i in range(dim):
        for j in range(dim):
            choi += np.kron(_apply_super(superop, _qutrit_op(i, j)), _qutrit_op(i, j))
    eigvals, eigvecs = np.linalg.eigh(choi)
    kraus: list[Array] = []
    for k in range(len(eigvals)):
        if eigvals[k] > tol:
            kraus.append(np.sqrt(eigvals[k]) * eigvecs[:, k].reshape(dim, dim, order="C"))
    return kraus


def _apply_super(superop: Array, rho: Array) -> Array:
    """Apply a column-stacking superoperator: ``E(rho) = unvec(S vec(rho))`` (Fortran order)."""
    dim = rho.shape[0]
    return (superop @ rho.reshape(-1, order="F")).reshape(dim, dim, order="F")


def leakage_kraus(theta: float, g_seep: float, g_heat: float = 0.0) -> list[Array]:
    """Full Wood-Gambetta 3-level (qutrit) leakage channel on the basis ``{|0>,|1>,|2>}``.

    The exact ``exp(Lindbladian)`` channel (operator-sum form), with ``|0>`` inert. It
    fixes the two confirmed toys of the prior ``leakage_kraus(l1, l2)``: (#1) the old
    channel was purely INCOHERENT (generated zero ``|1>-|2>`` coherence ``C_L`` -- the
    non-Pauli signal the whole program targets); (#2) its ``l1`` was 2x off the
    field-standard Wood-Gambetta leakage rate. The mechanism is now the canonical WG
    leakage model (1704.03081 Eqs.55-58 unitary + 70-73 dissipative):

      - ``theta``  = COHERENT ``|1><->|2>`` exchange strength (Hamiltonian
        ``H = theta(|1><2| + |2><1|)``) -> generates leakage **and** ``C_L>0`` (the
        faithful coherent mechanism; WG unitary-leakage, the dominant non-Pauli signal).
      - ``g_seep`` = dissipative seepage rate (jump ``|1><2|``, ``|2>->|1>``) -> WG_L2.
      - ``g_heat`` = OPTIONAL incoherent heating rate (jump ``|2><1|``, ``|1>->|2>``,
        ``C_L=0``). Default 0. Lets the SAME channel produce coherent (``theta``) vs
        incoherent (``g_heat``) leakage at a matched WG_L1 -- a built-in ablation that
        isolates the coherent contribution.

    The field-standard WG rates (1704.03081 Eq.2) are diagnostics of the returned
    channel ``E``, NOT input arguments:
      ``WG_L1 = (1/d1) Tr[Π2 E(Π1)]`` (leakage out of ``{|0>,|1>}``, ``d1=2``),
      ``WG_L2 = (1/d2) Tr[Π1 E(Π2)]`` (seepage back, ``d2=1``).
    At ``theta=0, g_seep=0, g_heat=0`` the channel is the 3x3 identity (the ``{|0>,|1>}``
    restriction is the 2x2 identity); ``theta>0`` carries ``C_L>0`` while
    ``theta=0, g_heat>0`` is the incoherent-leakage limit (``C_L=0``). CPTP by
    construction (the exponential of a Lindbladian; the Choi is PSD). Returns the
    rank-many ``(3,3)`` complex128 Kraus (the file's house format); the count is the
    channel rank, not a fixed 3. The 3x3 numpy algebra here is the single source of
    truth -- ``mechanisms.qutrit_teachers.leakage_kraus_torch`` only lifts it to torch
    CUDA for the engine. Validated against an independent qutip Lindbladian oracle at
    the channel level in ``outputs/teacher_prereg/check_wg_leakage_channel.py``.
    """
    superop = leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    return _super_to_kraus(superop)


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


def two_pauli_rotation(theta: float, left_label: str, right_label: str) -> Array:
    one = _single_qubit_paulis()
    pauli = np.kron(one[str(left_label).upper()], one[str(right_label).upper()])
    return (math.cos(0.5 * float(theta)) * np.eye(4) - 1j * math.sin(0.5 * float(theta)) * pauli).astype(np.complex128)


def _json_value(value: object) -> object:
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)


def _json_container_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return _json_value(value)


def _m13_epsilon(params: Mapping[str, object]) -> float:
    return float(params.get("epsilon", params.get("epsilon_mean", 0.03)))


def _m13_epsilon_mean(params: Mapping[str, object]) -> float:
    return float(params.get("epsilon_mean", params.get("epsilon", 0.03)))


def _m13_epsilon_span(params: Mapping[str, object]) -> float:
    if params.get("epsilon_span") is not None:
        return abs(float(params.get("epsilon_span")))
    if params.get("drift_span") is not None:
        return abs(float(params.get("drift_span")))
    return M13_DEFAULT_EPSILON_SPAN


def _m13_drift_visibility_scale(params: Mapping[str, object]) -> float:
    if params.get("drift_visibility_scale") is None:
        return M13_DEFAULT_DRIFT_VISIBILITY_SCALE
    return max(0.0, float(params.get("drift_visibility_scale")))


def _m13_effective_drift_span(params: Mapping[str, object]) -> float:
    return float(_m13_epsilon_span(params) * _m13_drift_visibility_scale(params))


def _m13_drift_offsets(params: Mapping[str, object]) -> tuple[float, ...]:
    span = _m13_effective_drift_span(params)
    if span <= 0.0:
        return (0.0,)
    return (-float(span), 0.0, float(span))


def _m13_drift_weights(params: Mapping[str, object], *, count: int) -> tuple[float, ...]:
    raw = params.get("drift_mixture_weights")
    values: list[float] = []
    if isinstance(raw, (list, tuple)):
        values = [max(0.0, float(value)) for value in raw]
    if len(values) != int(count) or sum(values) <= 0.0:
        if int(count) == 1:
            values = [1.0]
        else:
            values = [0.25, 0.5, 0.25]
    total = sum(values)
    return tuple(float(value / total) for value in values)

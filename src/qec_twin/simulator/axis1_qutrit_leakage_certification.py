from __future__ import annotations

"""Dense qutrit/ququart certification for Axis-1 leakage lowering.

This module certifies registered MCWF/MPS leakage carrier terms against small
dense independent oracles. It is a verification surface only: it does not emit a
dense channel payload, does not replace the computational-subspace evidence
path, and does not add a scored metric.
"""

import hashlib
import json
import math
from typing import Any

import numpy as np
import torch

from qec_twin.forward.channels import leakage_channel_super
from qec_twin.forward.joint_lindbladian import liouvillian_superop
from qec_twin.simulator.analog_schedule import SubstepSchedule
from qec_twin.simulator.axis1_carrier_program import (
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    axis1_carrier_program_manifest,
)
from qec_twin.simulator.axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_context import axis1_local_lindblad_context_from_schedule
from qec_twin.simulator.axis1_mcwf_mps_execution import _hamiltonian_group_gates
from qec_twin.simulator.axis1_state_evidence import _require_cuda_device


AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_SCHEMA = (
    "qec_twin.simulator.axis1_qutrit_leakage_oracle_certification.v1"
)
AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_REPRESENTABILITY = (
    "axis1_one_site_qutrit_leakage_dense_oracle_certification_no_payload"
)
AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_SCHEMA = (
    "qec_twin.simulator.axis1_two_site_leakage_hamiltonian_certification.v1"
)
AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_REPRESENTABILITY = (
    "axis1_two_site_leakage_hamiltonian_dense_oracle_certification_no_payload"
)
_SUPEROP_DIFF_GATE = 2.0e-12
_UNITARY_DIFF_GATE = 2.0e-12
_WRONG_UNIT_CONTROL_MIN = 1.0e-6
_TWO_SITE_TRANSPORT_LEVELS = {
    "LEAK_EXCHANGE_11_02": ((1, 1), (0, 2)),
    "LEAK_MOBILITY_12_21": ((1, 2), (2, 1)),
    "LEAK_TRANSPORT_30_12": ((3, 0), (1, 2)),
    "LEAK_TRANSPORT_31_22": ((3, 1), (2, 2)),
}
_TWO_SITE_CONDITIONAL_PHASE_FAMILIES = frozenset(
    {"LEAK_COND_PHASE_LEFT2_RIGHTZ", "LEAK_COND_PHASE_LEFTZ_RIGHT2"}
)
_TWO_SITE_CERTIFIABLE_FAMILIES = frozenset(_TWO_SITE_TRANSPORT_LEVELS) | (
    _TWO_SITE_CONDITIONAL_PHASE_FAMILIES
)


def axis1_qutrit_leakage_oracle_certification_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    superop_diff_gate: float = _SUPEROP_DIFF_GATE,
    wrong_unit_control_min: float = _WRONG_UNIT_CONTROL_MIN,
) -> dict[str, Any]:
    """Certify one-site qutrit leakage lowering against `leakage_channel_super`.

    Public Axis-1 leakage context supplies per-ns generator parameters. The dense
    Wood-Gambetta oracle consumes dimensionless unit-time parameters, so the
    certified conversion is explicit:

    ``theta = leak_exchange_12_rad_per_ns * dt_ns``,
    ``g_seep = leak_seep_21_per_ns * dt_ns``, and
    ``g_heat = leak_heat_12_per_ns * dt_ns``.
    """

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(
        schedule,
        allow_multilevel_leakage_context=True,
    )
    context = axis1_local_lindblad_context_from_schedule(schedule)
    if not context.include_leakage:
        raise ValueError("qutrit leakage certification requires public leakage context")

    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )
    substep, site, leakage_terms = _one_site_leakage_slice(program)
    dt_ns = _positive_dt_ns(substep)
    params = _dimensionless_params_from_terms(leakage_terms, dt_ns=dt_ns)

    S_lowered = _lowered_qutrit_superop(
        params["omega_12_rad_per_ns"],
        params["seep_rate_per_ns"],
        params["heat_rate_per_ns"],
        dt_ns=dt_ns,
        device=dev,
    )
    S_oracle = leakage_channel_super(
        params["theta"],
        params["g_seep"],
        params["g_heat"],
    )
    diff = float(np.max(np.abs(S_lowered - S_oracle)))

    S_wrong = leakage_channel_super(
        params["omega_12_rad_per_ns"],
        params["seep_rate_per_ns"],
        params["heat_rate_per_ns"],
    )
    wrong_diff = float(np.max(np.abs(S_lowered - S_wrong)))
    gate = float(superop_diff_gate)
    control_min = float(wrong_unit_control_min)
    passed = bool(diff <= gate and wrong_diff >= control_min)
    payload: dict[str, Any] = {
        "schema": AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_REPRESENTABILITY,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "gpu_required": True,
        "device": dev,
        "backend_contract": AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
        "carrier_program": {
            "schema": program["schema"],
            "content_hash": program["content_hash"],
            "backend_contract": program["backend_contract"],
            "requires_scalable_backend": bool(program["requires_scalable_backend"]),
        },
        "certified_substep": {
            "substep_id": str(substep["substep_id"]),
            "substep_kind": str(substep["substep_kind"]),
            "site": int(site),
            "dt_ns": dt_ns,
            "term_families": [str(term["operator_family"]) for term in leakage_terms],
        },
        "parameter_conversion": {
            "policy": "per_ns_generator_rates_times_dt_ns",
            "omega_12_rad_per_ns": params["omega_12_rad_per_ns"],
            "seep_rate_per_ns": params["seep_rate_per_ns"],
            "heat_rate_per_ns": params["heat_rate_per_ns"],
            "theta": params["theta"],
            "g_seep": params["g_seep"],
            "g_heat": params["g_heat"],
            "epistemic_class": "a/c",
        },
        "oracle_comparison": {
            "reference": "qec_twin.forward.channels.leakage_channel_super",
            "lowered_generator": "carrier_LEAK_terms_to_qutrit_liouvillian_superop",
            "max_abs_superop_diff": diff,
            "max_abs_superop_diff_gate": gate,
            "gate_role": "heuristic_certification_gate_not_metric",
            "passed": bool(diff <= gate),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        },
        "wrong_unit_negative_control": {
            "role": "negative_control_not_metric",
            "wrong_policy": "dimensionless_values_without_dt",
            "max_abs_superop_diff": wrong_diff,
            "min_expected_diff": control_min,
            "passed": bool(wrong_diff >= control_min),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "claims_dense_qutrit_oracle_certification": True,
        "claims_dense_channel_payload": False,
        "claims_exact_continuous_time_mcwf": False,
        "claims_axis1_full_completion": False,
        "claims_axis2_source_timeline": False,
        "claims_dem_decoder_semantics": False,
        "claims_production_scalable_backend": False,
        "comparison_outcome_is_metric": False,
        "scored_quantity_policy": "verification gate only; no new scored quantity",
        "scope": (
            "one-site qutrit leakage lowering certification only; no transport, "
            "no leaked-readout scoring, no DEM/decoder integration, no Axis-2 "
            "source timeline, and no production scalable backend claim"
        ),
        "epistemic_classes": {
            "operator_mapping": "a",
            "per_ns_to_dimensionless_conversion": "a",
            "numeric_superop_gate": "c",
            "wrong_unit_negative_control": "c",
        },
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_two_site_leakage_hamiltonian_certification_manifest(
    schedule: SubstepSchedule,
    *,
    local_dims: tuple[int, ...] | list[int] | None = None,
    device: str = "cuda",
    unitary_diff_gate: float = _UNITARY_DIFF_GATE,
    wrong_unit_control_min: float = _WRONG_UNIT_CONTROL_MIN,
) -> dict[str, Any]:
    """Certify two-site leakage Hamiltonian lowering against a dense oracle.

    The certified object is the same-support Hamiltonian block consumed by the
    fixed-microstep MCWF/MPS path. The dense oracle is a separately constructed
    two-site matrix exponential over the declared local dimensions. This is a
    code-correctness gate, not channel evidence, not a DEM/decoder artifact, and
    not a metric.
    """

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(
        schedule,
        allow_multilevel_leakage_context=True,
    )
    context = axis1_local_lindblad_context_from_schedule(schedule)
    if not context.include_leakage:
        raise ValueError("two-site leakage certification requires public leakage context")

    dims = _normalize_local_dims_for_schedule(local_dims, num_qubits=schedule.num_qubits)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    )
    substep, support, terms = _two_site_hamiltonian_slice(program)
    dt_ns = _positive_dt_ns(substep)

    groups = _hamiltonian_group_gates(
        substep,
        dt_ns=dt_ns,
        local_dims=dims,
        device=dev,
    )
    matching_groups = [
        group for group in groups if tuple(int(q) for q in group["support"]) == support
    ]
    if len(matching_groups) != 1:
        raise ValueError(
            "two-site leakage certification requires exactly one lowered "
            f"Hamiltonian group on support {support!r}"
        )
    lowered_gate = torch.as_tensor(
        matching_groups[0]["gate"],
        dtype=torch.complex128,
        device=dev,
    )
    oracle_gate = _independent_two_site_hamiltonian_gate(
        terms,
        support=support,
        local_dims=dims,
        dt_ns=dt_ns,
        device=dev,
        wrong_unit_for_leakage=False,
    )
    wrong_gate = _independent_two_site_hamiltonian_gate(
        terms,
        support=support,
        local_dims=dims,
        dt_ns=dt_ns,
        device=dev,
        wrong_unit_for_leakage=True,
    )
    diff = float(torch.max(torch.abs(lowered_gate - oracle_gate)).item())
    wrong_diff = float(torch.max(torch.abs(lowered_gate - wrong_gate)).item())
    gate = float(unitary_diff_gate)
    control_min = float(wrong_unit_control_min)
    passed = bool(diff <= gate and wrong_diff >= control_min)
    leakage_terms = [
        term for term in terms if str(term["operator_family"]).upper().startswith("LEAK_")
    ]
    payload: dict[str, Any] = {
        "schema": AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": (
            AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_REPRESENTABILITY
        ),
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "gpu_required": True,
        "device": dev,
        "backend_contract": AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
        "carrier_program": {
            "schema": program["schema"],
            "content_hash": program["content_hash"],
            "backend_contract": program["backend_contract"],
            "requires_scalable_backend": bool(program["requires_scalable_backend"]),
        },
        "certified_substep": {
            "substep_id": str(substep["substep_id"]),
            "substep_kind": str(substep["substep_kind"]),
            "support": list(support),
            "local_dims": list(dims),
            "dt_ns": dt_ns,
            "term_families": [str(term["operator_family"]) for term in terms],
            "leakage_term_families": [
                str(term["operator_family"]) for term in leakage_terms
            ],
            "lowered_group_family": str(
                matching_groups[0]["term"]["operator_family"]
            ),
        },
        "parameter_conversion": {
            "policy": "per_ns_two_site_hamiltonian_rates_times_dt_ns",
            "conditional_phase_relative_phase_policy": (
                "relative_phase_over_gate_equals_2_times_omega_rad_per_ns_times_dt_ns"
            ),
            "epistemic_class": "a/c",
        },
        "oracle_comparison": {
            "reference": "independent_dense_two_site_hamiltonian_matrix_exp",
            "lowered_generator": "mcwf_mps_connected_support_cluster_group_gate",
            "max_abs_unitary_diff": diff,
            "max_abs_unitary_diff_gate": gate,
            "gate_role": "heuristic_certification_gate_not_metric",
            "passed": bool(diff <= gate),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        },
        "wrong_unit_negative_control": {
            "role": "negative_control_not_metric",
            "wrong_policy": "treat_public_leakage_rate_as_dimensionless_angle",
            "max_abs_unitary_diff": wrong_diff,
            "min_expected_diff": control_min,
            "passed": bool(wrong_diff >= control_min),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "claims_dense_two_site_leakage_oracle_certification": True,
        "claims_dense_channel_payload": False,
        "claims_dense_channel_evidence": False,
        "claims_exact_continuous_time_mcwf": False,
        "claims_axis1_full_completion": False,
        "claims_axis2_source_timeline": False,
        "claims_dem_decoder_semantics": False,
        "claims_production_scalable_backend": False,
        "comparison_outcome_is_metric": False,
        "scored_quantity_policy": "verification gate only; no new scored quantity",
        "scope": (
            "two-site leakage Hamiltonian lowering certification only; no "
            "collapse/no-jump MCWF error bound, no record evidence, no "
            "DEM/decoder integration, no Axis-2 source timeline, and no "
            "production scalable backend claim"
        ),
        "epistemic_classes": {
            "operator_mapping": "a",
            "per_ns_to_gate_angle_conversion": "a",
            "numeric_unitary_gate": "c",
            "wrong_unit_negative_control": "c",
        },
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _one_site_leakage_slice(program: dict[str, Any]) -> tuple[dict[str, Any], int, tuple[dict[str, Any], ...]]:
    leakage_steps: list[tuple[dict[str, Any], tuple[dict[str, Any], ...]]] = []
    for substep in program["program"]["substeps"]:
        terms = tuple(
            term
            for term in substep.get("terms", ())
            if str(term["operator_family"]).upper().startswith("LEAK_")
            and abs(float(term.get("coefficient", 0.0))) > 0.0
        )
        if terms:
            leakage_steps.append((substep, terms))
    if len(leakage_steps) != 1:
        raise ValueError(
            "qutrit leakage certification requires exactly one leakage-bearing substep"
        )
    substep, terms = leakage_steps[0]
    sites: set[int] = set()
    if any(len(tuple(term.get("support", ()))) != 1 for term in terms):
        raise ValueError(
            "qutrit leakage certification supports one-site leakage terms only"
        )
    for term in terms:
        sites.add(int(term["support"][0]))
    if len(sites) != 1:
        raise ValueError(
            "qutrit leakage certification requires exactly one leakage-certified site"
        )
    return substep, next(iter(sites)), terms


def _positive_dt_ns(substep: dict[str, Any]) -> float:
    dt = substep.get("dt_ns")
    if dt is None:
        raise ValueError("qutrit leakage certification requires positive dt_ns")
    out = float(dt)
    if not math.isfinite(out) or out <= 0.0:
        raise ValueError(f"qutrit leakage certification requires positive dt_ns, got {dt!r}")
    return out


def _dimensionless_params_from_terms(
    terms: tuple[dict[str, Any], ...],
    *,
    dt_ns: float,
) -> dict[str, float]:
    omega = 0.0
    seep_rate = 0.0
    heat_rate = 0.0
    for term in terms:
        family = str(term["operator_family"]).upper()
        coeff = float(term["coefficient"])
        if family == "LEAK_EXCHANGE_12":
            omega += coeff
        elif family == "LEAK_SEEP_21":
            seep_rate += coeff * coeff
        elif family == "LEAK_HEAT_12":
            heat_rate += coeff * coeff
        else:
            raise ValueError(f"unsupported qutrit leakage family {family!r}")
    return {
        "omega_12_rad_per_ns": float(omega),
        "seep_rate_per_ns": float(seep_rate),
        "heat_rate_per_ns": float(heat_rate),
        "theta": float(omega * dt_ns),
        "g_seep": float(seep_rate * dt_ns),
        "g_heat": float(heat_rate * dt_ns),
    }


def _lowered_qutrit_superop(
    omega_12_rad_per_ns: float,
    seep_rate_per_ns: float,
    heat_rate_per_ns: float,
    *,
    dt_ns: float,
    device: str,
) -> np.ndarray:
    cdt = torch.complex128
    H_list: list[torch.Tensor] = []
    c_list: list[torch.Tensor] = []
    if float(omega_12_rad_per_ns) != 0.0:
        h = torch.zeros((3, 3), dtype=cdt, device=device)
        h[1, 2] = float(omega_12_rad_per_ns)
        h[2, 1] = float(omega_12_rad_per_ns)
        H_list.append(h)
    if float(seep_rate_per_ns) > 0.0:
        c = torch.zeros((3, 3), dtype=cdt, device=device)
        c[1, 2] = math.sqrt(float(seep_rate_per_ns))
        c_list.append(c)
    if float(heat_rate_per_ns) > 0.0:
        c = torch.zeros((3, 3), dtype=cdt, device=device)
        c[2, 1] = math.sqrt(float(heat_rate_per_ns))
        c_list.append(c)
    if not H_list and not c_list:
        raise ValueError("qutrit leakage certification needs at least one leakage term")
    L = liouvillian_superop(H_list, c_list, device=device)
    S = torch.linalg.matrix_exp(L * float(dt_ns))
    return S.detach().cpu().numpy()


def _stable_payload_hash(payload: dict[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    data = json.dumps(
        without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _normalize_local_dims_for_schedule(
    local_dims: tuple[int, ...] | list[int] | None,
    *,
    num_qubits: int,
) -> tuple[int, ...]:
    if local_dims is None:
        dims = (3,) * int(num_qubits)
    else:
        dims = tuple(int(dim) for dim in local_dims)
    if len(dims) != int(num_qubits):
        raise ValueError(
            f"local_dims length {len(dims)} does not match schedule num_qubits {num_qubits}"
        )
    if any(dim < 2 for dim in dims):
        raise ValueError(f"local_dims must all be >= 2, got {dims!r}")
    return dims


def _two_site_hamiltonian_slice(
    program: dict[str, Any],
) -> tuple[dict[str, Any], tuple[int, int], tuple[dict[str, Any], ...]]:
    candidates: list[tuple[dict[str, Any], tuple[int, int], tuple[dict[str, Any], ...]]] = []
    for substep in program["program"]["substeps"]:
        leakage_terms = tuple(
            term
            for term in substep.get("terms", ())
            if str(term.get("operator_family", "")).upper()
            in _TWO_SITE_CERTIFIABLE_FAMILIES
            and abs(float(term.get("coefficient", 0.0))) > 0.0
        )
        if not leakage_terms:
            continue
        supports = {tuple(int(q) for q in term.get("support", ())) for term in leakage_terms}
        if len(supports) != 1:
            raise ValueError(
                "two-site leakage certification requires one leakage support"
            )
        support = next(iter(supports))
        if len(support) != 2:
            raise ValueError(
                f"two-site leakage certification requires two-site support, got {support!r}"
            )
        h_terms = tuple(
            term
            for term in substep.get("terms", ())
            if str(term.get("kind")) == "hamiltonian"
            and tuple(int(q) for q in term.get("support", ())) == support
        )
        if not h_terms:
            raise ValueError("two-site leakage certification found no Hamiltonian terms")
        candidates.append((substep, support, h_terms))
    if len(candidates) != 1:
        raise ValueError(
            "two-site leakage certification requires exactly one leakage-bearing "
            "two-site substep"
        )
    return candidates[0]


def _independent_two_site_hamiltonian_gate(
    terms: tuple[dict[str, Any], ...],
    *,
    support: tuple[int, int],
    local_dims: tuple[int, ...],
    dt_ns: float,
    device: str,
    wrong_unit_for_leakage: bool,
) -> torch.Tensor:
    d0 = int(local_dims[support[0]])
    d1 = int(local_dims[support[1]])
    hamiltonian = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    for term in terms:
        family = str(term["operator_family"]).upper()
        coefficient = float(term["coefficient"])
        if wrong_unit_for_leakage and family in _TWO_SITE_CERTIFIABLE_FAMILIES:
            coefficient = coefficient / float(dt_ns)
        hamiltonian = hamiltonian + _independent_two_site_hamiltonian_term(
            family,
            coefficient=coefficient,
            dims=(d0, d1),
            device=device,
        )
    return torch.linalg.matrix_exp((-1.0j * float(dt_ns)) * hamiltonian)


def _independent_two_site_hamiltonian_term(
    family: str,
    *,
    coefficient: float,
    dims: tuple[int, int],
    device: str,
) -> torch.Tensor:
    family = str(family).upper()
    d0, d1 = int(dims[0]), int(dims[1])
    out = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    if family == "CTRL_CZ":
        out[1 * d1 + 1, 1 * d1 + 1] = float(coefficient)
        return out
    if family in {"ZZ", "FSIM_PHASE"}:
        out[1 * d1 + 1, 1 * d1 + 1] = float(coefficient)
        return out
    if family in _TWO_SITE_TRANSPORT_LEVELS:
        left, right = _TWO_SITE_TRANSPORT_LEVELS[family]
        left_index = _require_two_site_level(left, dims=(d0, d1), family=family)
        right_index = _require_two_site_level(right, dims=(d0, d1), family=family)
        if left_index == right_index:
            raise ValueError(f"{family} needs distinct levels")
        out[left_index, right_index] = float(coefficient)
        out[right_index, left_index] = float(coefficient)
        return out
    if family == "LEAK_COND_PHASE_LEFT2_RIGHTZ":
        if d0 < 3:
            raise ValueError(
                "LEAK_COND_PHASE_LEFT2_RIGHTZ requires left local_dim >= 3"
            )
        out[2 * d1 + 0, 2 * d1 + 0] = float(coefficient)
        out[2 * d1 + 1, 2 * d1 + 1] = -float(coefficient)
        return out
    if family == "LEAK_COND_PHASE_LEFTZ_RIGHT2":
        if d1 < 3:
            raise ValueError(
                "LEAK_COND_PHASE_LEFTZ_RIGHT2 requires right local_dim >= 3"
            )
        out[0 * d1 + 2, 0 * d1 + 2] = float(coefficient)
        out[1 * d1 + 2, 1 * d1 + 2] = -float(coefficient)
        return out
    raise ValueError(
        f"unsupported two-site leakage certification Hamiltonian family {family!r}"
    )


def _require_two_site_level(
    level: tuple[int, int],
    *,
    dims: tuple[int, int],
    family: str,
) -> int:
    left, right = int(level[0]), int(level[1])
    d0, d1 = int(dims[0]), int(dims[1])
    if left < 0 or left >= d0 or right < 0 or right >= d1:
        raise ValueError(
            f"{family} references level {level!r} outside local_dims {dims!r}"
        )
    return left * d1 + right


__all__ = [
    "AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_REPRESENTABILITY",
    "AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_SCHEMA",
    "AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_REPRESENTABILITY",
    "AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_SCHEMA",
    "axis1_two_site_leakage_hamiltonian_certification_manifest",
    "axis1_qutrit_leakage_oracle_certification_manifest",
]

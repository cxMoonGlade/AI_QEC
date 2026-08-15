from __future__ import annotations

"""Independent dense checks for Axis-1 two-site leakage Hamiltonians.

The reference level maps are hand-typed in this module and the reference Hamiltonian
uses a fresh ket-bra constructor. Neither the carrier's private level dictionary nor
its grouping/lifting helpers are imported. The carrier side exposes only the per-term
operator being tested; the grouped gate is reconstructed locally for the declared
single-support cluster.

Wrong-level controls probe transport families, sign-flip controls probe conditional
phase families, and a scalar-rescale control provides a weaker additional check. The
gate compares generators and ``exp(-i H dt)`` with max-absolute and Frobenius distances,
and checks Hermiticity. It is GPU-only implementation evidence. The cited papers are
candidate physical context for the level maps; exact source-to-row literature closure
must be completed before this result supports a physical mechanism claim.
"""

import hashlib
import json
import math
from typing import Any

import numpy as np
import torch

from ..carrier.joint_lindbladian import liouvillian_superop
from ..mechanisms.qutrit_leakage import leakage_channel_super
from .analog_schedule import SubstepSchedule
from .axis1_carrier_program import (
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    axis1_carrier_program_manifest,
)
from .axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from .axis1_context import axis1_local_lindblad_context_from_schedule

# Import only the carrier's per-term operator builder
# (the object under test). We do NOT import ``_hamiltonian_group_gates`` (the lowering path that
# was both verifier and verified) and we do NOT import any level dict / lift helper. A grep for
# ``_hamiltonian_group_gates`` in this module returns nothing -- that is the acceptance gate.
from .axis1_mcwf_mps_execution import _hamiltonian_matrix_for_term
from .axis1_state_evidence import _require_cuda_device


AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_SCHEMA = (
    "error_coupling_simulator.frontend.qutrit_leakage_reference_certification.v1"
)
AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_REPRESENTABILITY = (
    "axis1_one_site_qutrit_leakage_dense_oracle_certification_no_payload"
)
AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_SCHEMA = (
    "error_coupling_simulator.frontend.two_site_leakage_hamiltonian_certification.v1"
)
AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_REPRESENTABILITY = (
    "axis1_two_site_leakage_hamiltonian_dense_oracle_certification_no_payload"
)
_SUPEROP_DIFF_GATE = 2.0e-12
_UNITARY_DIFF_GATE = 2.0e-12
# Independent-reference operator-identity gate, witnessed numerically.
_INDEPENDENT_REFERENCE_DIFF_GATE = 1.0e-10
_WRONG_UNIT_CONTROL_MIN = 1.0e-6
# Level-discriminating control gate: a wrong-level / sign-flip
# reference must produce a genuinely different gate.
_WRONG_PHYSICS_CONTROL_MIN = 1.0e-3

# Conditional-phase families (kept for slice classification / payload introspection).
_TWO_SITE_CONDITIONAL_PHASE_FAMILIES = frozenset(
    {"LEAK_COND_PHASE_LEFT2_RIGHTZ", "LEAK_COND_PHASE_LEFTZ_RIGHT2"}
)

# -----------------------------------------------------------------------------------------------
# Hand-typed reference level maps. They are not imported from the carrier. A divergence
# between this table and the carrier's private ``_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS`` is a finding,
# not a bug in this module.
# -----------------------------------------------------------------------------------------------
# Ordered transport pairs (level_left, level_right) <-> (level_left', level_right'); coherent
# excitation-number-conserving exchange  H = coeff * (|p><p'| + |p'><p|).
_REF_TRANSPORT_PAIRS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "LEAK_EXCHANGE_11_02": ((1, 1), (0, 2)),   # Varbanov 2002.07119  |11> <-> |02|
    "LEAK_MOBILITY_12_21": ((1, 2), (2, 1)),   # Varbanov mobility    |12> <-> |21|
    "LEAK_TRANSPORT_30_12": ((3, 0), (1, 2)),  # Miao 2211.04728      |30> <-> |12| (ququart)
    "LEAK_TRANSPORT_31_22": ((3, 1), (2, 2)),  # Miao 2211.04728      |31> <-> |22| (ququart)
}
# Conditional leaked-neighbor phase: a leaked level (2) on one site imprints +/- coeff (a Z) on the
# neighbor's |0>/|1> (Miao phi~0.65pi; Varbanov phi_L). Diagonal, sign-asymmetric.
_REF_COND_PHASE: dict[str, dict[tuple[int, int], float]] = {
    "LEAK_COND_PHASE_LEFT2_RIGHTZ": {(2, 0): +1.0, (2, 1): -1.0},
    "LEAK_COND_PHASE_LEFTZ_RIGHT2": {(0, 2): +1.0, (1, 2): -1.0},
}
_REF_TWO_SITE_LEAKAGE_FAMILIES = frozenset(_REF_TRANSPORT_PAIRS) | frozenset(_REF_COND_PHASE)
# Non-leakage two-site control Hamiltonians the lowered cluster may also contain. The diagonal
# CZ/ZZ generator is hand-typed here (|11><11| coefficient) so the cluster reference imports no
# carrier physics; CTRL_CZ uses coefficient pi/dt (so exp(-i dt H) = diag(1,1,1,-1) on the
# computational 2x2 block), matching the standard CZ convention.
_TWO_SITE_DIAGONAL_CONTROL_FAMILIES = frozenset({"CTRL_CZ", "ZZ", "FSIM_PHASE"})


def axis1_qutrit_leakage_oracle_certification_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    superop_diff_gate: float = _SUPEROP_DIFF_GATE,
    wrong_unit_control_min: float = _WRONG_UNIT_CONTROL_MIN,
) -> dict[str, Any]:
    """Certify one-site qutrit leakage lowering against ``leakage_channel_super``.

    Unchanged from the shipped one-site cert (already non-circular: the oracle is the
    independent ``leakage_channel_super``). Carried here so the module stays a drop-in.
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
            "reference": (
                "error_coupling_simulator.mechanisms.qutrit_leakage."
                "leakage_channel_super"
            ),
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
    unitary_diff_gate: float = _INDEPENDENT_REFERENCE_DIFF_GATE,
    wrong_unit_control_min: float = _WRONG_UNIT_CONTROL_MIN,
    wrong_physics_control_min: float = _WRONG_PHYSICS_CONTROL_MIN,
) -> dict[str, Any]:
    """Certify two-site leakage Hamiltonian lowering against an INDEPENDENT hand-typed oracle.

    The checked objects are the carrier per-term operators (built by
    ``_hamiltonian_matrix_for_term``) AND the in-cert reconstruction of the lowered group gate. The
    reference is hand-typed here rather than imported from the carrier; and the
    lowered group gate is rebuilt in this module (single same-support cluster sum), so NO
    ``_hamiltonian_group_gates`` import is involved. Code-correctness gate only -- not channel
    evidence, not a DEM/decoder artifact, not a metric.
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
    d0 = int(dims[support[0]])
    d1 = int(dims[support[1]])

    leakage_terms = [
        term for term in terms if str(term["operator_family"]).upper().startswith("LEAK_")
    ]
    if not leakage_terms:
        raise ValueError("two-site leakage certification found no LEAK_ Hamiltonian terms")

    # ---- (1) PER-FAMILY operator certification: carrier op vs hand-typed reference. ----
    # The carrier op comes from `_hamiltonian_matrix_for_term`
    # (under test); the reference comes from the hand-typed table + fresh ket-bra constructor.
    family_reports: list[dict[str, Any]] = []
    family_pass = True
    family_op_diffs: list[float] = []
    family_control_diffs: list[float] = []
    for term in leakage_terms:
        report = _certify_leakage_family_operator(
            term,
            dims=(d0, d1),
            dt_ns=dt_ns,
            wrong_physics_control_min=float(wrong_physics_control_min),
            independent_reference_diff_gate=float(_INDEPENDENT_REFERENCE_DIFF_GATE),
            device=dev,
        )
        family_reports.append(report)
        family_pass = family_pass and bool(report["passed"])
        family_op_diffs.append(float(report["max_abs_unitary_diff"]))
        family_control_diffs.append(float(report["wrong_physics_control"]["max_abs_unitary_diff"]))

    # ---- (2) LOWERED GROUP GATE certification, reconstructed in-cert (no grouping import). ----
    # The certified slice is by construction a single same-support two-site cluster (see
    # `_two_site_hamiltonian_slice`: one leakage support; all H-terms on that exact support), so the
    # connected-cluster lowering reduces to a plain operator sum on the shared support. We rebuild it
    # HERE from the per-term carrier operators and exponentiate once -- this is independent of
    # `_hamiltonian_group_gates`, yet certifies the same realized two-site gate the MCWF/MPS path uses.
    lowered_gate, carrier_families = _reconstruct_lowered_group_gate(
        terms,
        support=support,
        dims=(d0, d1),
        dt_ns=dt_ns,
        device=dev,
    )
    ref_cluster_gate = _independent_reference_cluster_gate(
        terms,
        support=support,
        dims=(d0, d1),
        dt_ns=dt_ns,
        device=dev,
        wrong_unit_for_leakage=False,
    )
    wrong_unit_cluster_gate = _independent_reference_cluster_gate(
        terms,
        support=support,
        dims=(d0, d1),
        dt_ns=dt_ns,
        device=dev,
        wrong_unit_for_leakage=True,
    )
    cluster_diff = float(torch.max(torch.abs(lowered_gate - ref_cluster_gate)).item())
    wrong_unit_diff = float(torch.max(torch.abs(lowered_gate - wrong_unit_cluster_gate)).item())

    cluster_gate = float(unitary_diff_gate)
    control_min = float(wrong_unit_control_min)
    cluster_pass = bool(cluster_diff <= cluster_gate)
    wrong_unit_pass = bool(wrong_unit_diff >= control_min)
    passed = bool(family_pass and cluster_pass and wrong_unit_pass)

    lowered_group_family = "H_CLUSTER[" + "+".join(carrier_families) + "]"
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
            "lowered_group_family": lowered_group_family,
        },
        "independence": {
            "reference_origin": "hand_typed_independent_level_map",
            "literature_closure_status": "pending_exact_source_to_row_audit",
            "reference_anchors": [
                "Wood-Gambetta 1704.03081",
                "Varbanov 2002.07119",
                "Miao 2211.04728",
            ],
            "imports_hamiltonian_group_gates": False,
            "imports_carrier_level_dict": False,
            "carrier_object_under_test": (
                "error_coupling_simulator.frontend.axis1_mcwf_mps_execution."
                "_hamiltonian_matrix_for_term"
            ),
            "lowered_gate_reconstruction": (
                "in_module_single_same_support_cluster_sum_then_matrix_exp"
            ),
            "decircularization_note": (
                "reference level maps and cluster sum are independent of the carrier; "
                "a shared wrong level map cannot pass"
            ),
        },
        "parameter_conversion": {
            "policy": "per_ns_two_site_hamiltonian_rates_times_dt_ns",
            "conditional_phase_relative_phase_policy": (
                "relative_phase_over_gate_equals_2_times_omega_rad_per_ns_times_dt_ns"
            ),
            "epistemic_class": "a/c",
        },
        "per_family_oracle_certification": {
            "reference": "hand_typed_independent_two_site_ketbra_reference",
            "carrier_operator": (
                "error_coupling_simulator.frontend.axis1_mcwf_mps_execution."
                "_hamiltonian_matrix_for_term"
            ),
            "independent_reference_diff_gate": float(_INDEPENDENT_REFERENCE_DIFF_GATE),
            "wrong_physics_control_min": float(wrong_physics_control_min),
            "max_abs_unitary_diff": (max(family_op_diffs) if family_op_diffs else 0.0),
            "min_wrong_physics_control_diff": (
                min(family_control_diffs) if family_control_diffs else 0.0
            ),
            "passed": bool(family_pass),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
            "families": family_reports,
        },
        "oracle_comparison": {
            "reference": "independent_hand_typed_two_site_cluster_gate",
            "lowered_generator": (
                "in_cert_single_support_cluster_sum_of_carrier_per_term_operators"
            ),
            "max_abs_unitary_diff": cluster_diff,
            "max_abs_unitary_diff_gate": cluster_gate,
            "gate_role": "heuristic_certification_gate_not_metric",
            "passed": bool(cluster_pass),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        },
        "wrong_physics_negative_control": {
            "role": "level_discriminating_negative_control_not_metric",
            "wrong_policy": (
                "wrong_level_for_transport_or_sign_flip_for_conditional_phase_per_family"
            ),
            "min_abs_unitary_diff": (
                min(family_control_diffs) if family_control_diffs else 0.0
            ),
            "min_expected_diff": float(wrong_physics_control_min),
            "passed": bool(family_pass),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "wrong_unit_negative_control": {
            "role": "negative_control_not_metric",
            "wrong_policy": "treat_public_leakage_rate_as_dimensionless_angle",
            "max_abs_unitary_diff": wrong_unit_diff,
            "min_expected_diff": control_min,
            "passed": bool(wrong_unit_pass),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "claims_dense_two_site_leakage_oracle_certification": True,
        "claims_independent_two_site_leakage_oracle_certification": True,
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
            "independent_reference_operator_identity": "a",
            "numeric_unitary_gate": "c",
            "wrong_physics_negative_control": "c",
            "wrong_unit_negative_control": "c",
        },
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


# ----------------------------------------------------------------------------------------------
# Independent (hand-typed, no shared carrier code) reference machinery.
# ----------------------------------------------------------------------------------------------
def _ref_two_site_ketbra(
    a: tuple[int, int],
    b: tuple[int, int],
    *,
    dims: tuple[int, int],
    device: str,
) -> torch.Tensor:
    """|a><b| on (d0 x d1) with index = level0*d1 + level1; a,b are (level0, level1) tuples.

    Fresh from-scratch constructor -- shares NO helper with the carrier. The ``level0*d1+level1``
    convention is the standard qubit-0-major kron order, asserted here for the reference; the
    point of the cert is that the carrier must INDEPENDENTLY produce the same matrix.
    """
    d0, d1 = int(dims[0]), int(dims[1])
    D = d0 * d1
    out = torch.zeros((D, D), dtype=torch.complex128, device=device)
    out[a[0] * d1 + a[1], b[0] * d1 + b[1]] = 1.0
    return out


def _ref_transport_hamiltonian(
    family: str,
    *,
    coefficient: float,
    dims: tuple[int, int],
    device: str,
    pairs_override: tuple[tuple[int, int], tuple[int, int]] | None = None,
) -> torch.Tensor:
    pairs = pairs_override if pairs_override is not None else _REF_TRANSPORT_PAIRS[family]
    left, right = pairs
    _require_ref_level(left, dims=dims, family=family)
    _require_ref_level(right, dims=dims, family=family)
    return float(coefficient) * (
        _ref_two_site_ketbra(left, right, dims=dims, device=device)
        + _ref_two_site_ketbra(right, left, dims=dims, device=device)
    )


def _ref_conditional_phase_hamiltonian(
    family: str,
    *,
    coefficient: float,
    dims: tuple[int, int],
    device: str,
    sign_flip: bool = False,
) -> torch.Tensor:
    d0, d1 = int(dims[0]), int(dims[1])
    out = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    for (level0, level1), sign in _REF_COND_PHASE[family].items():
        _require_ref_level((level0, level1), dims=dims, family=family)
        s = -sign if sign_flip else sign
        out[level0 * d1 + level1, level0 * d1 + level1] = float(coefficient) * float(s)
    return out


def _ref_diagonal_control_hamiltonian(
    family: str,
    *,
    coefficient: float,
    dims: tuple[int, int],
    device: str,
) -> torch.Tensor:
    """Hand-typed diagonal CZ/ZZ generator: H = coeff * |11><11| (the |1>x|1> level).

    For CTRL_CZ the carrier passes coefficient = pi/dt, so exp(-i dt H) imprints exp(-i pi) = -1 on
    |11> -- the standard CZ. Typed here so the cluster reference imports no carrier physics.
    """
    d0, d1 = int(dims[0]), int(dims[1])
    if d0 < 2 or d1 < 2:
        raise ValueError(f"{family} reference requires local_dims >= 2, got {dims!r}")
    out = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    out[1 * d1 + 1, 1 * d1 + 1] = float(coefficient)
    return out


def _require_ref_level(
    level: tuple[int, int],
    *,
    dims: tuple[int, int],
    family: str,
) -> None:
    d0, d1 = int(dims[0]), int(dims[1])
    if not (0 <= int(level[0]) < d0 and 0 <= int(level[1]) < d1):
        raise ValueError(
            f"{family} reference level {level!r} outside local_dims {dims!r}"
        )


def _reference_hamiltonian_for_term(
    term: dict[str, Any],
    *,
    dims: tuple[int, int],
    device: str,
) -> torch.Tensor:
    """Hand-typed reference Hamiltonian for a single carrier term (leakage or diagonal control).

    The term's ``coefficient`` is used as-is; the wrong-unit control is applied by the caller
    (``_independent_reference_cluster_gate``) by rescaling the coefficient before this call.
    """
    family = str(term["operator_family"]).upper()
    coefficient = float(term["coefficient"])
    if family in _REF_TRANSPORT_PAIRS:
        return _ref_transport_hamiltonian(
            family, coefficient=coefficient, dims=dims, device=device
        )
    if family in _REF_COND_PHASE:
        return _ref_conditional_phase_hamiltonian(
            family, coefficient=coefficient, dims=dims, device=device
        )
    if family in _TWO_SITE_DIAGONAL_CONTROL_FAMILIES:
        return _ref_diagonal_control_hamiltonian(
            family, coefficient=coefficient, dims=dims, device=device
        )
    raise ValueError(
        f"unsupported two-site reference Hamiltonian family {family!r}"
    )


def _certify_leakage_family_operator(
    term: dict[str, Any],
    *,
    dims: tuple[int, int],
    dt_ns: float,
    wrong_physics_control_min: float,
    independent_reference_diff_gate: float,
    device: str,
) -> dict[str, Any]:
    """Carrier per-term operator vs hand-typed reference + a level-discriminating control."""
    family = str(term["operator_family"]).upper()
    coefficient = float(term["coefficient"])

    carrier_h = _hamiltonian_matrix_for_term(
        term, support=(0, 1), local_dims=dims, device=device
    )
    ref_h = _reference_hamiltonian_for_term(term, dims=dims, device=device)

    hermiticity = float(
        torch.linalg.matrix_norm(
            carrier_h - carrier_h.conj().transpose(-1, -2)
        ).item()
    )
    op_diff = float(torch.linalg.matrix_norm(carrier_h - ref_h).item())
    carrier_u = _matrix_exp_gate(carrier_h, dt_ns)
    ref_u = _matrix_exp_gate(ref_h, dt_ns)
    unitary_diff = float(torch.linalg.matrix_norm(carrier_u - ref_u).item())

    # Level-discriminating control.
    if family in _REF_TRANSPORT_PAIRS:
        control_kind = "wrong_level"
        wrong_h = _ref_transport_hamiltonian(
            family,
            coefficient=coefficient,
            dims=dims,
            device=device,
            pairs_override=_wrong_level_pairs(family),
        )
    elif family in _REF_COND_PHASE:
        control_kind = "sign_flip"
        wrong_h = _ref_conditional_phase_hamiltonian(
            family,
            coefficient=coefficient,
            dims=dims,
            device=device,
            sign_flip=True,
        )
    else:
        raise ValueError(f"no level-discriminating control for family {family!r}")
    wrong_u = _matrix_exp_gate(wrong_h, dt_ns)
    control_diff = float(torch.linalg.matrix_norm(carrier_u - wrong_u).item())

    op_pass = bool(op_diff <= independent_reference_diff_gate)
    unitary_pass = bool(unitary_diff <= independent_reference_diff_gate)
    hermitian_pass = bool(hermiticity <= _UNITARY_DIFF_GATE)
    control_pass = bool(control_diff >= float(wrong_physics_control_min))
    passed = bool(op_pass and unitary_pass and hermitian_pass and control_pass)
    return {
        "operator_family": family,
        "coefficient": coefficient,
        "max_abs_generator_diff": op_diff,
        "max_abs_unitary_diff": unitary_diff,
        "hermiticity_residual": hermiticity,
        "independent_reference_diff_gate": float(independent_reference_diff_gate),
        "generator_matches_reference": op_pass,
        "unitary_matches_reference": unitary_pass,
        "hermitian": hermitian_pass,
        "wrong_physics_control": {
            "control_kind": control_kind,
            "max_abs_unitary_diff": control_diff,
            "min_expected_diff": float(wrong_physics_control_min),
            "passed": control_pass,
        },
        "passed": passed,
        "comparison_outcome_is_metric": False,
    }


def _wrong_level_pairs(
    family: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """A genuinely different transport level map: perturb the left pair's leading level by +/-1.

    Stays in-range (decrement if > 0 else increment) so the reference is well-formed but WRONG.
    Transport exchange is (left<->right)-symmetric, so a transposed ordered pair would be inert --
    hence we perturb a LEVEL, not the ordering.
    """
    left, right = _REF_TRANSPORT_PAIRS[family]
    if int(left[0]) > 0:
        bad_left0 = int(left[0]) - 1
    else:
        bad_left0 = int(left[0]) + 1
    return ((bad_left0, int(left[1])), right)


def _reconstruct_lowered_group_gate(
    terms: tuple[dict[str, Any], ...],
    *,
    support: tuple[int, int],
    dims: tuple[int, int],
    dt_ns: float,
    device: str,
) -> tuple[torch.Tensor, list[str]]:
    """Rebuild the carrier's lowered two-site gate WITHOUT importing the grouping path.

    The certified slice is a single same-support two-site cluster (guaranteed by
    `_two_site_hamiltonian_slice`), so the connected-cluster lowering reduces to summing each
    per-term carrier operator on the shared support and exponentiating once. We Hermitize the sum
    (as the carrier's grouping does) and exponentiate -- this reproduces the realized gate while
    importing only the per-term operator builder under test.
    """
    d0, d1 = int(dims[0]), int(dims[1])
    h_cluster = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    families: list[str] = []
    for term in terms:
        term_support = tuple(int(q) for q in term.get("support", ()))
        if term_support != tuple(int(q) for q in support):
            raise ValueError(
                "in-cert lowered-gate reconstruction requires every Hamiltonian term on the "
                f"single certified support {support!r}, got {term_support!r}"
            )
        h_cluster = h_cluster + _hamiltonian_matrix_for_term(
            term, support=(0, 1), local_dims=dims, device=device
        )
        families.append(str(term["operator_family"]).upper())
    h_cluster = 0.5 * (h_cluster + h_cluster.conj().transpose(-1, -2))
    return _matrix_exp_gate(h_cluster, dt_ns), families


def _independent_reference_cluster_gate(
    terms: tuple[dict[str, Any], ...],
    *,
    support: tuple[int, int],
    dims: tuple[int, int],
    dt_ns: float,
    device: str,
    wrong_unit_for_leakage: bool,
) -> torch.Tensor:
    """Hand-typed reference for the full lowered cluster gate (leakage + diagonal controls)."""
    d0, d1 = int(dims[0]), int(dims[1])
    h_cluster = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    for term in terms:
        family = str(term["operator_family"]).upper()
        coefficient = float(term["coefficient"])
        if wrong_unit_for_leakage and family in _REF_TWO_SITE_LEAKAGE_FAMILIES:
            coefficient = coefficient / float(dt_ns)
        proxy = {"operator_family": family, "coefficient": coefficient}
        h_cluster = h_cluster + _reference_hamiltonian_for_term(
            proxy, dims=(d0, d1), device=device
        )
    h_cluster = 0.5 * (h_cluster + h_cluster.conj().transpose(-1, -2))
    return _matrix_exp_gate(h_cluster, dt_ns)


def _matrix_exp_gate(hamiltonian: torch.Tensor, dt_ns: float) -> torch.Tensor:
    return torch.linalg.matrix_exp((-1.0j * float(dt_ns)) * hamiltonian)


# ----------------------------------------------------------------------------------------------
# Slice + parameter helpers (carried from the shipped cert; one-site path is unchanged).
# ----------------------------------------------------------------------------------------------
def _one_site_leakage_slice(
    program: dict[str, Any],
) -> tuple[dict[str, Any], int, tuple[dict[str, Any], ...]]:
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
            in _REF_TWO_SITE_LEAKAGE_FAMILIES
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


__all__ = [
    "AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_REPRESENTABILITY",
    "AXIS1_TWO_SITE_LEAKAGE_HAMILTONIAN_CERTIFICATION_SCHEMA",
    "AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_REPRESENTABILITY",
    "AXIS1_QUTRIT_LEAKAGE_CERTIFICATION_SCHEMA",
    "axis1_two_site_leakage_hamiltonian_certification_manifest",
    "axis1_qutrit_leakage_oracle_certification_manifest",
]

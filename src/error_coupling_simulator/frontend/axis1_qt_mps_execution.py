from __future__ import annotations

"""Restricted QT/MPS execution adapter for Axis-1 carrier programs.

This is the first executable computational-subspace MPS slice behind the
`qt_mps_state_record` contract. It is intentionally narrow: supported
Hamiltonian/control terms, local product-channel collapse branches, and Z-record
execution. It is still a declared product-formula approximation to the summed
substep generator, not dense joint-L channel evidence.
"""

import hashlib
import json
import math
import operator
import sys
from functools import lru_cache
from numbers import Real
from typing import Any

import numpy as np
import torch

from ..carrier.mps.probability import (
    RawProbabilityMass,
    multiply_probability_values,
    one_minus_exp_neg_probability,
    sample_raw_probability_mass,
    validate_raw_probability_mass,
)
from ..carrier.mps.controls import (
    normalize_mps_bool,
    normalize_mps_choice,
    normalize_mps_device,
    normalize_mps_index,
    normalize_mps_index_sequence,
    normalize_mps_max_bond,
    normalize_optional_mps_nonnegative_real,
    normalize_optional_mps_index,
)
from ..numerics import NUMERICAL_ZERO, scaled_product_ratio
from .analog_schedule import (
    COMPILER_SCHEDULE_SEAL_SCHEMA,
    SubstepSchedule,
    has_valid_compiler_schedule_seal,
)
from .axis1_carrier_program import (
    axis1_carrier_program_manifest,
    axis1_carrier_substep_summary,
    axis1_reset_basis,
)
from .axis1_channel_evidence import (
    _coverage_manifest,
    _validate_schedule_for_axis1_channel_evidence,
)
from .axis1_record_evidence import (
    AXIS1_RECORD_EVIDENCE_REPRESENTABILITY,
    AXIS1_RECORD_EVIDENCE_SCHEMA,
    Axis1ReadoutResetInstrumentSpec,
    axis1_measurement_record_evidence_manifest,
)
from .axis1_record_layout import (
    Axis1MeasurementBoundaryLayout,
    Axis1ScheduleRecordLayout,
    _validate_axis1_projected_record_payload,
    axis1_record_layout_from_schedule,
    materialize_binary_records,
    project_axis1_xor_records,
)
from .axis1_selection import (
    AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES,
    axis1_selection_layers_in_schedule_order,
    axis1_selection_partition_manifest,
    build_axis1_schedule_selection_plan,
)
from .axis1_state_evidence import _require_cuda_device
from ..mechanisms.axis1_primitives import default_axis1_primitive_registry
from ..carrier.mps.capped_two_site import (
    apply_capped_two_site_unitary,
)
from ..carrier.mps.state import (
    commit_mps_candidate_,
    max_mps_bond,
    mps_norm_squared,
)
from ..carrier.mps.truncation import (
    aggregate_exact_branch_truncation_events,
    aggregate_sampled_truncation_events,
    build_mps_truncation_ledger,
)


AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_restricted_execution.v6"
)
AXIS1_QT_MPS_BOND_SWEEP_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_bond_sweep.v4"
)
AXIS1_QT_MPS_TRAJECTORY_SWEEP_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_trajectory_seed_sweep.v4"
)
AXIS1_QT_MPS_RESTRICTED_EVIDENCE_BUNDLE_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_restricted_evidence_bundle.v4"
)
AXIS1_QT_MPS_RESOURCE_PROBE_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_resource_probe.v4"
)
_AXIS1_QT_MPS_RESTRICTED_ACCEPTANCE_POLICY_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_restricted_acceptance_policy.v2"
)
_AXIS1_QT_MPS_RECORD_MATERIALIZATION_PREFLIGHT_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_record_materialization_preflight.v2"
)
AXIS1_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY = (
    "axis1_qt_mps_restricted_control_hamiltonian_z_record_product_channel"
)
AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT = "qt_mps_state_record"
_FINITE_STEP_ORDER_FIRST = "first_order"
_FINITE_STEP_ORDER_STRANG = "strang_second_order"
_FINITE_STEP_ORDERS = (_FINITE_STEP_ORDER_FIRST, _FINITE_STEP_ORDER_STRANG)
_TOTAL_PROBABILITY_RESIDUAL_GATE = 1.0e-8
_DENSE_RECORD_CERTIFICATION_GATE = 1.0e-8
_DEFAULT_MAX_RECORD_MATERIALIZATION_OUTCOMES = 4096
_FULL_BINARY_RECORD_SUPPORT_POLICY = "full_binary_record_support"
_OBSERVED_EMPIRICAL_RECORD_SUPPORT_POLICY = "observed_empirical_outcomes_only"
_UNION_RECORD_SUPPORT_ALIGNMENT_POLICY = (
    "union_of_emitted_records_missing_probability_zero"
)
_QT_RESOURCE_PROBE_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema",
        "source_kind",
        "source_hash",
        "schedule_representability",
        "representability",
        "backend_contract",
        "gpu_required",
        "device",
        "workload",
        "bond_values",
        "reference_bond",
        "trajectory_count",
        "rng_seeds",
        "max_branches",
        "max_record_materialization_outcomes",
        "record_materialization_preflight",
        "workload_schema",
        "workload_content_hash",
        "workload_passed",
        "microstep_count",
        "finite_step_order",
        "convergence_record_probability_gate",
        "seed_record_frequency_spread_gate",
        "dense_record_frequency_gate",
        "worst_cut_discarded_weight_gate",
        "total_discarded_weight_gate",
        "min_peak_allocated_gib",
        "min_peak_reserved_gib",
        "resource_probe_policy",
        "claims_qt_mps_backend_execution",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "claims_production_scalable_backend",
        "scored_quantity_policy",
        "passed",
        "verdict",
        "content_hash",
    }
)


def _require_qt_unit_probability_mass(
    values: list[float] | tuple[float, ...],
    *,
    name: str,
) -> RawProbabilityMass:
    mass = validate_raw_probability_mass(values, name=name)
    if mass.residual_from_one > _TOTAL_PROBABILITY_RESIDUAL_GATE:
        raise ValueError(
            f"{name} raw probability mass must sum to one within "
            f"{_TOTAL_PROBABILITY_RESIDUAL_GATE}; got {mass.total!r}"
        )
    return mass


def _qt_exact_conditioned_branch_weight(
    parent_weight: float,
    raw_candidate_mass: float,
    raw_partition_total: float,
    *,
    name: str,
) -> float:
    """Propagate an exact branch through an accepted raw QT partition."""

    conditioned = scaled_product_ratio(
        parent_weight,
        raw_candidate_mass,
        raw_partition_total,
        name=name,
    )
    if not math.isfinite(conditioned) or not 0.0 <= conditioned <= 1.0:
        raise ValueError(
            f"{name} must be finite and lie in [0, 1], got {conditioned!r}"
        )
    return float(conditioned)


def _normalize_finite_step_order(value: str) -> str:
    return normalize_mps_choice(
        value,
        name="finite_step_order",
        choices=_FINITE_STEP_ORDERS,
    )


def _finite_step_policy_name(finite_step_order: str) -> str:
    order = _normalize_finite_step_order(finite_step_order)
    if order == _FINITE_STEP_ORDER_STRANG:
        return "strang_hamiltonian_collapse_product_formula_v1"
    return "operator_family_product_formula_v1"


_QT_MPS_SCORED_QUANTITY_POLICY = (
    "restricted QT/MPS execution is a verification gate only; no new "
    "scored quantity"
)
_QT_MPS_COMPLETED_SCOPE = (
    "restricted QT/MPS Hamiltonian/control/Z-record execution only; no "
    "nonzero exact summed-generator claim, no dense channel evidence, no "
    "DEM/decoder semantics, no Axis-2 source timeline, no production "
    "scalable backend claim"
)
_QT_MPS_BLOCKED_SCOPE = (
    "restricted QT/MPS Hamiltonian/control/Z-record slice failed closed; "
    "unsupported Lindblad terms, non-Z measurements, two-qubit "
    "control families outside the frontend set, DEM/decoder semantics, "
    "and Axis-2 timelines are not implemented here"
)


def _qt_restricted_approximation_book(
    *,
    max_bond: int | None,
    microstep_count: int,
    finite_step_order: str,
    trajectory_count: int | None,
    rng_seed: int | None,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    finite_step_policy = _finite_step_policy_name(finite_step_order)
    truncation = {
        "max_bond": max_bond,
        "discarded_weight_ledger_complete": bool(max_bond is None),
        "ledger_policy": (
            "complete_zero_ledger_when_no_explicit_truncation_requested"
            if max_bond is None
            else "quimb_actual_svd_split_per_two_site_unitary_gate"
        ),
        "worst_cut_discarded_weight_gate": worst_cut_discarded_weight_gate,
        "total_discarded_weight_gate": total_discarded_weight_gate,
        "gate_role": "heuristic_policy_gate_not_metric",
        "epistemic_class": "c",
    }
    if execution is not None:
        ledger = execution["mps_truncation_ledger"]
        truncation["discarded_weight_ledger_complete"] = bool(
            ledger["discarded_weight_ledger_complete"]
        )
        truncation["aggregation_context_complete"] = bool(
            ledger.get("aggregation", {}).get("context_complete", False)
        )
    return {
        "schema": (
            "error_coupling_simulator.frontend."
            "qt_mps_restricted_approximation_book.v1"
        ),
        "hamiltonian_product_formula": {
            "status": "operator_family_order_product_formula",
            "finite_step_policy": finite_step_policy,
            "finite_step_order": finite_step_order,
            "microstep_count": microstep_count,
            "exact_joint_generator_claim": False,
            "epistemic_class": "c",
        },
        "collapse_terms": {
            "supported": "local_T1_T1_UP_T2_RD_product_channel_branches",
            "finite_step_policy": finite_step_policy,
            "finite_step_order": finite_step_order,
            "microstep_count": microstep_count,
            "exact_summed_generator_claim": False,
            "epistemic_class": "c",
        },
        "mps_truncation": truncation,
        "record_branching": {
            "basis": "Z",
            "branch_enumeration": (
                "sampled_seeded_trajectories"
                if trajectory_count is not None
                else "exact_for_emitted_branch_table"
            ),
            "claims_dem_decoder_semantics": False,
            "epistemic_class": "a/c",
        },
        "trajectory_sampling": {
            "mode": (
                "sampled_product_channel_trajectories"
                if trajectory_count is not None
                else "exact_branch_enumeration"
            ),
            "rng_backend": (
                "torch.Generator(cuda)"
                if trajectory_count is not None
                else "not_used"
            ),
            "rng_seed_required_for_acceptance": trajectory_count is not None,
            "rng_seed_was_explicit": bool(
                trajectory_count is not None and rng_seed is not None
            ),
            "single_trajectory_density_claim": False,
            "epistemic_class": "c",
        },
    }


def _qt_restricted_epistemic_classes() -> dict[str, str]:
    return {
        "program_consumption": "a",
        "restricted_mps_execution": "c",
        "local_collapse_channel_forms": "a/c",
        "production_backend_status": "a",
    }


def axis1_qt_mps_restricted_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    max_bond: int | None = None,
    max_branches: int = 4096,
    max_record_materialization_outcomes: int = (
        _DEFAULT_MAX_RECORD_MATERIALIZATION_OUTCOMES
    ),
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
    trajectory_count: int | None = None,
    rng_seed: int | None = None,
    dense_oracle_certification: bool = True,
) -> dict[str, Any]:
    """Execute the currently supported QT/MPS slice for an Axis-1 schedule."""

    device = normalize_mps_device(device)
    max_bond = normalize_mps_max_bond(max_bond)
    max_branches = normalize_mps_index(
        max_branches,
        name="max_branches",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        microstep_count,
        name="microstep_count",
        minimum=1,
    )
    step_order = _normalize_finite_step_order(finite_step_order)
    finite_step_policy = _finite_step_policy_name(step_order)
    trajectory_count = normalize_optional_mps_index(
        trajectory_count,
        name="trajectory_count",
        minimum=1,
    )
    rng_seed = normalize_optional_mps_index(rng_seed, name="rng_seed")
    dense_oracle_certification = normalize_mps_bool(
        dense_oracle_certification,
        name="dense_oracle_certification",
    )
    worst_cut_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        worst_cut_discarded_weight_gate,
        name="worst_cut_discarded_weight_gate",
    )
    total_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        total_discarded_weight_gate,
        name="total_discarded_weight_gate",
    )
    record_budget = _normalize_max_record_materialization_outcomes(
        max_record_materialization_outcomes
    )
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    record_layout = axis1_record_layout_from_schedule(schedule)
    record_materialization = _record_materialization_preflight(
        record_layout,
        max_record_materialization_outcomes=record_budget,
        trajectory_count=trajectory_count,
    )
    dev = _require_cuda_device(device)
    base = {
        "schema": AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY,
        "backend_contract": AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": dev,
        "carrier_program": _program_summary(program),
        "max_bond": None if max_bond is None else int(max_bond),
        "max_branches": max_branches,
        "max_record_materialization_outcomes": record_budget,
        "record_materialization_preflight": record_materialization,
        "microstep_count": microstep_count,
        "finite_step_order": step_order,
        "trajectory_count": trajectory_count,
        "rng_seed": rng_seed,
        "worst_cut_discarded_weight_gate": (
            None
            if worst_cut_discarded_weight_gate is None
            else float(worst_cut_discarded_weight_gate)
        ),
        "total_discarded_weight_gate": (
            None
            if total_discarded_weight_gate is None
            else float(total_discarded_weight_gate)
        ),
        "dense_oracle_certification_requested": dense_oracle_certification,
        "claims_qt_mps_backend_execution": False,
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": _QT_MPS_SCORED_QUANTITY_POLICY,
        "approximation_book": _qt_restricted_approximation_book(
            max_bond=max_bond,
            microstep_count=microstep_count,
            finite_step_order=step_order,
            trajectory_count=trajectory_count,
            rng_seed=rng_seed,
            worst_cut_discarded_weight_gate=(
                worst_cut_discarded_weight_gate
            ),
            total_discarded_weight_gate=total_discarded_weight_gate,
        ),
        "epistemic_classes": _qt_restricted_epistemic_classes(),
    }
    unsupported = _unsupported_substeps(program)
    if unsupported:
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "execution_status": "blocked",
            "certification_status": "not_evaluated",
            "diagnostic_only": False,
            "qt_mps_backend_executed": False,
            "blocked_reason": unsupported[0]["reason"],
            "blocked_substeps": unsupported,
            "mps_execution": None,
            "dense_jointL_record_certification": {
                "executed": False,
                "reason": (
                    "qt_mps_backend_blocked_before_dense_record_certification"
                ),
                "blocked_reason": unsupported[0]["reason"],
                "comparison_outcome_is_metric": False,
            },
            "restricted_acceptance_policy": _blocked_restricted_acceptance_policy(
                blocked_reason=unsupported[0]["reason"],
                finite_step_order=step_order,
                finite_step_policy=finite_step_policy,
                microstep_count=int(microstep_count),
                trajectory_count=trajectory_count,
                rng_seed=rng_seed,
                max_bond=max_bond,
                worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
                total_discarded_weight_gate=total_discarded_weight_gate,
            ),
            "scope": _QT_MPS_BLOCKED_SCOPE,
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    execution = (
        _execute_sampled_program(
            program,
            record_layout=record_layout,
            device=dev,
            max_bond=max_bond,
            microstep_count=int(microstep_count),
            finite_step_order=step_order,
            trajectory_count=int(trajectory_count),
            rng_seed=rng_seed,
        )
        if trajectory_count is not None
        else _execute_program(
            program,
            record_layout=record_layout,
            device=dev,
            max_bond=max_bond,
            max_branches=int(max_branches),
            microstep_count=int(microstep_count),
            finite_step_order=step_order,
        )
    )
    base["approximation_book"] = _qt_restricted_approximation_book(
        max_bond=max_bond,
        microstep_count=microstep_count,
        finite_step_order=step_order,
        trajectory_count=trajectory_count,
        rng_seed=rng_seed,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
        execution=execution,
    )
    certification = (
        _dense_record_certification(
            schedule,
            program=program,
            execution=execution,
            device=dev,
        )
        if dense_oracle_certification
        else {
            "executed": False,
            "reason": "dense_oracle_certification_not_requested",
            "comparison_outcome_is_metric": False,
        }
    )
    acceptance = _restricted_acceptance_policy(
        program=program,
        execution=execution,
        record_materialization_preflight=record_materialization,
        certification=certification,
        finite_step_order=step_order,
        finite_step_policy=finite_step_policy,
        max_bond=max_bond,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    (
        passed,
        certification_status,
        diagnostic_only,
        blocked_reason,
    ) = _validate_completed_qt_acceptance_policy(
        acceptance,
        execution=execution,
        sampled=trajectory_count is not None,
    )
    payload = {
        **base,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "execution_status": "completed",
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "qt_mps_backend_executed": True,
        "claims_qt_mps_backend_execution": True,
        "blocked_reason": blocked_reason,
        "blocked_substeps": [],
        "mps_execution": execution,
        "dense_jointL_record_certification": certification,
        "restricted_acceptance_policy": acceptance,
        "scope": _QT_MPS_COMPLETED_SCOPE,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qt_mps_bond_sweep_manifest(
    schedule: SubstepSchedule,
    *,
    bond_values: tuple[int, ...] | list[int],
    device: str = "cuda",
    max_branches: int = 4096,
    max_record_materialization_outcomes: int = (
        _DEFAULT_MAX_RECORD_MATERIALIZATION_OUTCOMES
    ),
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    convergence_record_probability_gate: float | None = None,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
    dense_oracle_certification: bool = True,
) -> dict[str, Any]:
    """Run a finite-bond convergence sweep for the restricted QT/MPS slice."""

    device = normalize_mps_device(device)
    bonds = _normalize_bond_sweep_values(bond_values)
    max_branches = normalize_mps_index(
        max_branches,
        name="max_branches",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        microstep_count,
        name="microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(finite_step_order)
    dense_oracle_certification = normalize_mps_bool(
        dense_oracle_certification,
        name="dense_oracle_certification",
    )
    convergence_record_probability_gate = normalize_optional_mps_nonnegative_real(
        convergence_record_probability_gate,
        name="convergence_record_probability_gate",
    )
    worst_cut_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        worst_cut_discarded_weight_gate,
        name="worst_cut_discarded_weight_gate",
    )
    total_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        total_discarded_weight_gate,
        name="total_discarded_weight_gate",
    )
    record_budget = _normalize_max_record_materialization_outcomes(
        max_record_materialization_outcomes
    )
    record_materialization = _record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=record_budget,
    )
    expected_record_layout = axis1_record_layout_from_schedule(schedule)
    expected_carrier_program = _program_summary(
        axis1_carrier_program_manifest(
            schedule,
            backend_contract=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        )
    )
    runs = [
        axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device=device,
            max_bond=bond,
            max_branches=max_branches,
            max_record_materialization_outcomes=record_budget,
            microstep_count=microstep_count,
            finite_step_order=finite_step_order,
            worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
            total_discarded_weight_gate=total_discarded_weight_gate,
            trajectory_count=None,
            rng_seed=None,
            dense_oracle_certification=dense_oracle_certification,
        )
        for bond in bonds
    ]
    run_passed = [
        _validate_qt_restricted_child(
            run,
            context=f"bond sweep child {index}",
            expected_trajectory_mode="exact_branch_enumeration",
            expected_schedule=schedule,
            expected_source_kind=schedule.source_kind,
            expected_source_hash=schedule.source_hash,
            expected_schedule_representability=schedule.representability,
            expected_carrier_program=expected_carrier_program,
            expected_device=str(device),
            expected_max_bond=bond,
            expected_max_branches=max_branches,
            expected_record_budget=record_budget,
            expected_record_materialization_preflight=record_materialization,
            expected_record_layout=expected_record_layout,
            expected_microstep_count=microstep_count,
            expected_finite_step_order=finite_step_order,
            expected_trajectory_count=None,
            expected_rng_seed=None,
            expected_worst_cut_discarded_weight_gate=(
                worst_cut_discarded_weight_gate
            ),
            expected_total_discarded_weight_gate=total_discarded_weight_gate,
            expected_dense_oracle_certification=dense_oracle_certification,
        )
        for index, (bond, run) in enumerate(zip(bonds, runs, strict=True))
    ]
    backend_executed = all(
        _require_exact_bool_field(run, "qt_mps_backend_executed")
        for run in runs
    )
    reference = runs[-1]
    comparison = _bond_sweep_comparison(
        runs,
        convergence_record_probability_gate=convergence_record_probability_gate,
    )
    reference_calibration = _bond_sweep_reference_calibration(reference)
    reference_exact_bond = _require_exact_bool_field(
        reference["restricted_acceptance_policy"]["mps_truncation"],
        "accepted_as_exact_bond_representation",
    )
    accepted = bool(
        all(run_passed)
        and _require_exact_bool_field(comparison["convergence_gate"], "evaluated")
        and _require_exact_bool_field(comparison["convergence_gate"], "passed")
        and _require_exact_bool_field(
            reference_calibration, "accepted_as_dense_calibrated_reference"
        )
        and reference_exact_bond
    )
    payload = {
        "schema": AXIS1_QT_MPS_BOND_SWEEP_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": (
            "axis1_qt_mps_restricted_finite_bond_convergence_sweep"
        ),
        "backend_contract": AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": str(device),
        "bond_values": list(bonds),
        "reference_bond": int(bonds[-1]),
        "max_branches": max_branches,
        "max_record_materialization_outcomes": record_budget,
        "record_materialization_preflight": record_materialization,
        "microstep_count": int(microstep_count),
        "finite_step_order": _normalize_finite_step_order(finite_step_order),
        "convergence_record_probability_gate": (
            None
            if convergence_record_probability_gate is None
            else float(convergence_record_probability_gate)
        ),
        "worst_cut_discarded_weight_gate": (
            None
            if worst_cut_discarded_weight_gate is None
            else float(worst_cut_discarded_weight_gate)
        ),
        "total_discarded_weight_gate": (
            None
            if total_discarded_weight_gate is None
            else float(total_discarded_weight_gate)
        ),
        "dense_oracle_certification_requested": dense_oracle_certification,
        "convergence_policy": {
            **comparison,
            "reference_dense_calibration": reference_calibration,
            "accepted_as_restricted_convergence_evidence": accepted,
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "runs": runs,
        "run_summaries": [_bond_sweep_run_summary(run) for run in runs],
        "claims_qt_mps_backend_execution": backend_executed,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scored_quantity_policy": "bond sweep convergence gate only; no new scored quantity",
    }
    payload["passed"] = accepted
    payload["verdict"] = "pass" if accepted else "fail"
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qt_mps_trajectory_seed_sweep_manifest(
    schedule: SubstepSchedule,
    *,
    trajectory_count: int,
    rng_seeds: tuple[int, ...] | list[int],
    device: str = "cuda",
    max_bond: int | None = None,
    max_branches: int = 4096,
    max_record_materialization_outcomes: int = (
        _DEFAULT_MAX_RECORD_MATERIALIZATION_OUTCOMES
    ),
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
    seed_record_frequency_spread_gate: float | None = None,
    dense_record_frequency_gate: float | None = None,
) -> dict[str, Any]:
    """Run explicit-seed sampled trajectory sweeps for restricted QT/MPS records."""

    device = normalize_mps_device(device)
    max_bond = normalize_mps_max_bond(max_bond)
    max_branches = normalize_mps_index(
        max_branches,
        name="max_branches",
        minimum=1,
    )
    seeds = _normalize_trajectory_sweep_seeds(rng_seeds)
    trajectory_count = normalize_mps_index(
        trajectory_count,
        name="trajectory_count",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        microstep_count,
        name="microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(finite_step_order)
    seed_record_frequency_spread_gate = normalize_optional_mps_nonnegative_real(
        seed_record_frequency_spread_gate,
        name="seed_record_frequency_spread_gate",
    )
    dense_record_frequency_gate = normalize_optional_mps_nonnegative_real(
        dense_record_frequency_gate,
        name="dense_record_frequency_gate",
    )
    worst_cut_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        worst_cut_discarded_weight_gate,
        name="worst_cut_discarded_weight_gate",
    )
    total_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        total_discarded_weight_gate,
        name="total_discarded_weight_gate",
    )
    record_budget = _normalize_max_record_materialization_outcomes(
        max_record_materialization_outcomes
    )
    record_materialization = _record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=record_budget,
        trajectory_count=trajectory_count,
    )
    expected_record_layout = axis1_record_layout_from_schedule(schedule)
    expected_carrier_program = _program_summary(
        axis1_carrier_program_manifest(
            schedule,
            backend_contract=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        )
    )
    runs = [
        axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device=device,
            max_bond=max_bond,
            max_branches=max_branches,
            max_record_materialization_outcomes=record_budget,
            microstep_count=microstep_count,
            finite_step_order=finite_step_order,
            worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
            total_discarded_weight_gate=total_discarded_weight_gate,
            trajectory_count=int(trajectory_count),
            rng_seed=seed,
            dense_oracle_certification=True,
        )
        for seed in seeds
    ]
    for index, (seed, run) in enumerate(zip(seeds, runs, strict=True)):
        _validate_qt_restricted_child(
            run,
            context=f"seed sweep child {index}",
            expected_trajectory_mode="sampled_product_channel_trajectories",
            expected_schedule=schedule,
            expected_source_kind=schedule.source_kind,
            expected_source_hash=schedule.source_hash,
            expected_schedule_representability=schedule.representability,
            expected_carrier_program=expected_carrier_program,
            expected_device=str(device),
            expected_max_bond=max_bond,
            expected_max_branches=max_branches,
            expected_record_budget=record_budget,
            expected_record_materialization_preflight=record_materialization,
            expected_record_layout=expected_record_layout,
            expected_microstep_count=microstep_count,
            expected_finite_step_order=finite_step_order,
            expected_trajectory_count=trajectory_count,
            expected_rng_seed=seed,
            expected_worst_cut_discarded_weight_gate=(
                worst_cut_discarded_weight_gate
            ),
            expected_total_discarded_weight_gate=total_discarded_weight_gate,
            expected_dense_oracle_certification=True,
        )
    backend_executed = all(
        _require_exact_bool_field(run, "qt_mps_backend_executed")
        for run in runs
    )
    seed_comparison = _trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=seed_record_frequency_spread_gate,
    )
    dense_calibration = _trajectory_seed_sweep_dense_calibration(
        schedule,
        runs,
        device=str(runs[0]["device"]),
        dense_record_frequency_gate=dense_record_frequency_gate,
    )
    all_sampled_runs_accepted = all(
        _require_exact_bool_field(
            run["restricted_acceptance_policy"],
            "accepted_for_sampled_execution_evidence",
        )
        for run in runs
    )
    seed_spread_gate = seed_comparison["seed_spread_gate"]
    if not isinstance(seed_spread_gate, dict):
        raise TypeError("seed_spread_gate must be a mapping")
    seed_spread_evaluated = _require_exact_bool_field(
        seed_spread_gate,
        "evaluated",
    )
    if seed_spread_evaluated:
        seed_spread_passed = _require_exact_bool_field(
            seed_spread_gate,
            "passed",
        )
    else:
        raw_seed_spread_passed = seed_spread_gate.get("passed")
        if raw_seed_spread_passed is not None:
            _require_exact_bool_field(seed_spread_gate, "passed")
        seed_spread_passed = False
    dense_calibration_accepted = _require_exact_bool_field(
        dense_calibration,
        "accepted_as_dense_calibrated_trajectory_evidence",
    )
    accepted_restricted = bool(
        all_sampled_runs_accepted
        and seed_spread_evaluated
        and seed_spread_passed
    )
    accepted_dense = dense_calibration_accepted
    payload = {
        "schema": AXIS1_QT_MPS_TRAJECTORY_SWEEP_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": "axis1_qt_mps_restricted_seeded_trajectory_sweep",
        "backend_contract": AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": str(runs[0]["device"]),
        "trajectory_count": int(trajectory_count),
        "rng_seeds": list(seeds),
        "max_bond": None if max_bond is None else int(max_bond),
        "max_branches": max_branches,
        "max_record_materialization_outcomes": record_budget,
        "record_materialization_preflight": record_materialization,
        "microstep_count": int(microstep_count),
        "finite_step_order": _normalize_finite_step_order(finite_step_order),
        "seed_record_frequency_spread_gate": (
            None
            if seed_record_frequency_spread_gate is None
            else float(seed_record_frequency_spread_gate)
        ),
        "dense_record_frequency_gate": (
            None
            if dense_record_frequency_gate is None
            else float(dense_record_frequency_gate)
        ),
        "worst_cut_discarded_weight_gate": (
            None
            if worst_cut_discarded_weight_gate is None
            else float(worst_cut_discarded_weight_gate)
        ),
        "total_discarded_weight_gate": (
            None
            if total_discarded_weight_gate is None
            else float(total_discarded_weight_gate)
        ),
        "dense_oracle_certification_requested": True,
        "seed_sweep_policy": {
            **seed_comparison,
            "dense_reference_calibration": dense_calibration,
            "all_sampled_runs_accepted": all_sampled_runs_accepted,
            "accepted_as_restricted_seed_sweep_evidence": accepted_restricted,
            "accepted_as_dense_calibrated_trajectory_evidence": accepted_dense,
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "runs": runs,
        "run_summaries": [_trajectory_seed_sweep_run_summary(run) for run in runs],
        "claims_qt_mps_backend_execution": backend_executed,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scored_quantity_policy": (
            "trajectory seed sweep gates are empirical verification gates only; "
            "no new scored quantity"
        ),
    }
    payload["passed"] = accepted_restricted
    payload["verdict"] = "pass" if accepted_restricted else "fail"
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qt_mps_restricted_evidence_bundle_manifest(
    schedule: SubstepSchedule,
    *,
    bond_values: tuple[int, ...] | list[int],
    trajectory_count: int,
    rng_seeds: tuple[int, ...] | list[int],
    device: str = "cuda",
    max_branches: int = 4096,
    max_record_materialization_outcomes: int = (
        _DEFAULT_MAX_RECORD_MATERIALIZATION_OUTCOMES
    ),
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    convergence_record_probability_gate: float | None = None,
    seed_record_frequency_spread_gate: float | None = None,
    dense_record_frequency_gate: float | None = None,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
) -> dict[str, Any]:
    """Bundle finite-bond and trajectory seed-sweep gates for restricted QT/MPS."""

    device = normalize_mps_device(device)
    bonds = _normalize_bond_sweep_values(bond_values)
    seeds = _normalize_trajectory_sweep_seeds(rng_seeds)
    max_branches = normalize_mps_index(
        max_branches,
        name="max_branches",
        minimum=1,
    )
    trajectory_count = normalize_mps_index(
        trajectory_count,
        name="trajectory_count",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        microstep_count,
        name="microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(finite_step_order)
    convergence_record_probability_gate = normalize_optional_mps_nonnegative_real(
        convergence_record_probability_gate,
        name="convergence_record_probability_gate",
    )
    seed_record_frequency_spread_gate = normalize_optional_mps_nonnegative_real(
        seed_record_frequency_spread_gate,
        name="seed_record_frequency_spread_gate",
    )
    dense_record_frequency_gate = normalize_optional_mps_nonnegative_real(
        dense_record_frequency_gate,
        name="dense_record_frequency_gate",
    )
    worst_cut_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        worst_cut_discarded_weight_gate,
        name="worst_cut_discarded_weight_gate",
    )
    total_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        total_discarded_weight_gate,
        name="total_discarded_weight_gate",
    )
    record_budget = _normalize_max_record_materialization_outcomes(
        max_record_materialization_outcomes
    )
    record_materialization = _record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=record_budget,
    )
    sampled_record_materialization = _record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=record_budget,
        trajectory_count=trajectory_count,
    )
    reference_bond = int(max(bonds))
    bond_sweep = axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=bonds,
        device=device,
        max_branches=max_branches,
        max_record_materialization_outcomes=record_budget,
        microstep_count=microstep_count,
        finite_step_order=finite_step_order,
        convergence_record_probability_gate=convergence_record_probability_gate,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
        dense_oracle_certification=True,
    )
    trajectory_sweep = axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=trajectory_count,
        rng_seeds=seeds,
        device=device,
        max_bond=reference_bond,
        max_branches=max_branches,
        max_record_materialization_outcomes=record_budget,
        microstep_count=microstep_count,
        finite_step_order=finite_step_order,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
        seed_record_frequency_spread_gate=seed_record_frequency_spread_gate,
        dense_record_frequency_gate=dense_record_frequency_gate,
    )
    bond_passed = _require_exact_bool_field(bond_sweep, "passed")
    trajectory_passed = _require_exact_bool_field(trajectory_sweep, "passed")
    bond_backend_executed = _validate_qt_aggregate_child(
        bond_sweep,
        accepted=bond_passed,
        context="bond sweep",
        expected_schema=AXIS1_QT_MPS_BOND_SWEEP_SCHEMA,
        expected_representability=(
            "axis1_qt_mps_restricted_finite_bond_convergence_sweep"
        ),
        expected_source_kind=schedule.source_kind,
        expected_source_hash=schedule.source_hash,
        expected_schedule_representability=schedule.representability,
        expected_device=str(device),
        expected_fields={
            "bond_values": list(bonds),
            "reference_bond": reference_bond,
            "max_branches": max_branches,
            "max_record_materialization_outcomes": record_budget,
            "record_materialization_preflight": record_materialization,
            "microstep_count": microstep_count,
            "finite_step_order": finite_step_order,
            "convergence_record_probability_gate": (
                convergence_record_probability_gate
            ),
            "worst_cut_discarded_weight_gate": (
                worst_cut_discarded_weight_gate
            ),
            "total_discarded_weight_gate": total_discarded_weight_gate,
            "dense_oracle_certification_requested": True,
        },
    )
    trajectory_backend_executed = _validate_qt_aggregate_child(
        trajectory_sweep,
        accepted=trajectory_passed,
        context="trajectory seed sweep",
        expected_schema=AXIS1_QT_MPS_TRAJECTORY_SWEEP_SCHEMA,
        expected_representability=(
            "axis1_qt_mps_restricted_seeded_trajectory_sweep"
        ),
        expected_source_kind=schedule.source_kind,
        expected_source_hash=schedule.source_hash,
        expected_schedule_representability=schedule.representability,
        expected_device=str(device),
        expected_fields={
            "trajectory_count": trajectory_count,
            "rng_seeds": list(seeds),
            "max_bond": reference_bond,
            "max_branches": max_branches,
            "max_record_materialization_outcomes": record_budget,
            "record_materialization_preflight": sampled_record_materialization,
            "microstep_count": microstep_count,
            "finite_step_order": finite_step_order,
            "seed_record_frequency_spread_gate": (
                seed_record_frequency_spread_gate
            ),
            "dense_record_frequency_gate": dense_record_frequency_gate,
            "worst_cut_discarded_weight_gate": (
                worst_cut_discarded_weight_gate
            ),
            "total_discarded_weight_gate": total_discarded_weight_gate,
            "dense_oracle_certification_requested": True,
        },
    )
    bond_policy = bond_sweep.get("convergence_policy")
    if not isinstance(bond_policy, dict):
        raise TypeError("bond sweep convergence_policy must be a mapping")
    trajectory_policy = trajectory_sweep.get("seed_sweep_policy")
    if not isinstance(trajectory_policy, dict):
        raise TypeError("trajectory seed sweep seed_sweep_policy must be a mapping")
    bond_accepted = _require_exact_bool_field(
        bond_policy, "accepted_as_restricted_convergence_evidence"
    )
    trajectory_accepted = _require_exact_bool_field(
        trajectory_policy, "accepted_as_restricted_seed_sweep_evidence"
    )
    if bond_accepted != bond_passed:
        raise ValueError("bond sweep policy acceptance must agree with passed")
    if trajectory_accepted != trajectory_passed:
        raise ValueError(
            "trajectory seed sweep policy acceptance must agree with passed"
        )
    _validate_qt_bond_sweep_acceptance(
        bond_sweep,
        accepted=bond_accepted,
        expected_bonds=bonds,
        expected_schedule=schedule,
        context="bond sweep",
    )
    _validate_qt_seed_sweep_acceptance(
        trajectory_sweep,
        accepted=trajectory_accepted,
        expected_seeds=seeds,
        expected_trajectory_count=trajectory_count,
        expected_schedule=schedule,
        expected_device=str(device),
        context="trajectory seed sweep",
    )
    accepted_restricted = bool(bond_accepted and trajectory_accepted)
    accepted_dense = bool(
        _require_exact_bool_field(
            bond_policy["reference_dense_calibration"],
            "accepted_as_dense_calibrated_reference",
        )
        and _require_exact_bool_field(
            trajectory_policy,
            "accepted_as_dense_calibrated_trajectory_evidence",
        )
    )
    if bond_backend_executed != _qt_run_summaries_backend_execution_claim(
        bond_sweep,
        expected_count=len(bonds),
        context="bond sweep",
    ):
        raise ValueError("bond sweep backend claim does not match run summaries")
    if trajectory_backend_executed != _qt_run_summaries_backend_execution_claim(
        trajectory_sweep,
        expected_count=len(seeds),
        context="trajectory seed sweep",
    ):
        raise ValueError(
            "trajectory seed sweep backend claim does not match run summaries"
        )
    bundle_backend_executed = bool(
        bond_backend_executed and trajectory_backend_executed
    )
    payload = {
        "schema": AXIS1_QT_MPS_RESTRICTED_EVIDENCE_BUNDLE_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": "axis1_qt_mps_restricted_bond_and_seed_sweep_bundle",
        "backend_contract": AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": str(bond_sweep["device"]),
        "bond_values": list(bonds),
        "reference_bond": reference_bond,
        "max_branches": max_branches,
        "max_record_materialization_outcomes": record_budget,
        "record_materialization_preflight": record_materialization,
        "trajectory_count": int(trajectory_count),
        "rng_seeds": list(seeds),
        "microstep_count": int(microstep_count),
        "finite_step_order": _normalize_finite_step_order(finite_step_order),
        "convergence_record_probability_gate": (
            None
            if convergence_record_probability_gate is None
            else float(convergence_record_probability_gate)
        ),
        "seed_record_frequency_spread_gate": (
            None
            if seed_record_frequency_spread_gate is None
            else float(seed_record_frequency_spread_gate)
        ),
        "dense_record_frequency_gate": (
            None
            if dense_record_frequency_gate is None
            else float(dense_record_frequency_gate)
        ),
        "worst_cut_discarded_weight_gate": (
            None
            if worst_cut_discarded_weight_gate is None
            else float(worst_cut_discarded_weight_gate)
        ),
        "total_discarded_weight_gate": (
            None
            if total_discarded_weight_gate is None
            else float(total_discarded_weight_gate)
        ),
        "bundle_policy": {
            "accepted_as_restricted_bundle_evidence": accepted_restricted,
            "accepted_as_dense_calibrated_bundle_evidence": accepted_dense,
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "bond_sweep": bond_sweep,
        "trajectory_seed_sweep": trajectory_sweep,
        "claims_qt_mps_backend_execution": bundle_backend_executed,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scored_quantity_policy": (
            "restricted QT/MPS evidence bundle combines verification gates only; "
            "no new scored quantity"
        ),
    }
    payload["passed"] = accepted_restricted
    payload["verdict"] = "pass" if accepted_restricted else "fail"
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qt_mps_resource_probe_manifest(
    schedule: SubstepSchedule,
    *,
    bond_values: tuple[int, ...] | list[int],
    trajectory_count: int,
    rng_seeds: tuple[int, ...] | list[int],
    device: str = "cuda",
    max_branches: int = 4096,
    max_record_materialization_outcomes: int = (
        _DEFAULT_MAX_RECORD_MATERIALIZATION_OUTCOMES
    ),
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    convergence_record_probability_gate: float | None = None,
    seed_record_frequency_spread_gate: float | None = None,
    dense_record_frequency_gate: float | None = None,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
    min_peak_allocated_gib: float | None = None,
    min_peak_reserved_gib: float | None = None,
) -> dict[str, Any]:
    """Run a restricted QT/MPS evidence bundle and report actual CUDA memory."""

    device = normalize_mps_device(device)
    bonds = _normalize_bond_sweep_values(bond_values)
    seeds = _normalize_trajectory_sweep_seeds(rng_seeds)
    max_branches = normalize_mps_index(
        max_branches,
        name="max_branches",
        minimum=1,
    )
    trajectory_count = normalize_mps_index(
        trajectory_count,
        name="trajectory_count",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        microstep_count,
        name="microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(finite_step_order)
    convergence_record_probability_gate = normalize_optional_mps_nonnegative_real(
        convergence_record_probability_gate,
        name="convergence_record_probability_gate",
    )
    seed_record_frequency_spread_gate = normalize_optional_mps_nonnegative_real(
        seed_record_frequency_spread_gate,
        name="seed_record_frequency_spread_gate",
    )
    dense_record_frequency_gate = normalize_optional_mps_nonnegative_real(
        dense_record_frequency_gate,
        name="dense_record_frequency_gate",
    )
    worst_cut_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        worst_cut_discarded_weight_gate,
        name="worst_cut_discarded_weight_gate",
    )
    total_discarded_weight_gate = normalize_optional_mps_nonnegative_real(
        total_discarded_weight_gate,
        name="total_discarded_weight_gate",
    )
    min_peak_allocated_gib = normalize_optional_mps_nonnegative_real(
        min_peak_allocated_gib,
        name="min_peak_allocated_gib",
    )
    min_peak_reserved_gib = normalize_optional_mps_nonnegative_real(
        min_peak_reserved_gib,
        name="min_peak_reserved_gib",
    )
    record_budget = _normalize_max_record_materialization_outcomes(
        max_record_materialization_outcomes
    )
    record_materialization = _record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=record_budget,
    )
    dev = _require_cuda_device(device)
    torch_dev = torch.device(dev)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(torch_dev)
    torch.cuda.synchronize(torch_dev)
    bundle = axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=bonds,
        trajectory_count=trajectory_count,
        rng_seeds=seeds,
        device=dev,
        max_branches=max_branches,
        max_record_materialization_outcomes=record_budget,
        microstep_count=microstep_count,
        finite_step_order=finite_step_order,
        convergence_record_probability_gate=convergence_record_probability_gate,
        seed_record_frequency_spread_gate=seed_record_frequency_spread_gate,
        dense_record_frequency_gate=dense_record_frequency_gate,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    torch.cuda.synchronize(torch_dev)
    peak_allocated = int(torch.cuda.max_memory_allocated(torch_dev))
    peak_reserved = int(torch.cuda.max_memory_reserved(torch_dev))
    resource_policy = _resource_probe_policy(
        peak_allocated_bytes=peak_allocated,
        peak_reserved_bytes=peak_reserved,
        min_peak_allocated_gib=min_peak_allocated_gib,
        min_peak_reserved_gib=min_peak_reserved_gib,
    )
    bundle_passed = _require_exact_bool_field(bundle, "passed")
    resource_accepted = _require_exact_bool_field(
        resource_policy, "accepted_as_resource_probe"
    )
    bundle_backend_executed = _validate_qt_aggregate_child(
        bundle,
        accepted=bundle_passed,
        context="resource-probe workload",
        expected_schema=AXIS1_QT_MPS_RESTRICTED_EVIDENCE_BUNDLE_SCHEMA,
        expected_representability=(
            "axis1_qt_mps_restricted_bond_and_seed_sweep_bundle"
        ),
        expected_source_kind=schedule.source_kind,
        expected_source_hash=schedule.source_hash,
        expected_schedule_representability=schedule.representability,
        expected_device=dev,
        expected_fields={
            "bond_values": list(bonds),
            "reference_bond": int(max(bonds)),
            "max_branches": max_branches,
            "max_record_materialization_outcomes": record_budget,
            "record_materialization_preflight": record_materialization,
            "trajectory_count": trajectory_count,
            "rng_seeds": list(seeds),
            "microstep_count": microstep_count,
            "finite_step_order": finite_step_order,
            "convergence_record_probability_gate": (
                convergence_record_probability_gate
            ),
            "seed_record_frequency_spread_gate": (
                seed_record_frequency_spread_gate
            ),
            "dense_record_frequency_gate": dense_record_frequency_gate,
            "worst_cut_discarded_weight_gate": (
                worst_cut_discarded_weight_gate
            ),
            "total_discarded_weight_gate": total_discarded_weight_gate,
        },
    )
    _validate_qt_bundle_policy_consistency(
        bundle,
        accepted=bundle_passed,
        expected_schedule=schedule,
        context="resource-probe workload",
    )
    passed = bool(bundle_passed and resource_accepted)
    payload = {
        "schema": AXIS1_QT_MPS_RESOURCE_PROBE_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": "axis1_qt_mps_resource_probe_actual_execution_no_padding",
        "backend_contract": AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": dev,
        "workload": "restricted_bond_and_seed_sweep_bundle",
        "bond_values": list(bonds),
        "reference_bond": int(max(bonds)),
        "trajectory_count": trajectory_count,
        "rng_seeds": list(seeds),
        "max_branches": max_branches,
        "max_record_materialization_outcomes": record_budget,
        "record_materialization_preflight": record_materialization,
        "workload_schema": bundle["schema"],
        "workload_content_hash": bundle["content_hash"],
        "workload_passed": bundle_passed,
        "microstep_count": microstep_count,
        "finite_step_order": finite_step_order,
        "convergence_record_probability_gate": (
            None
            if convergence_record_probability_gate is None
            else float(convergence_record_probability_gate)
        ),
        "seed_record_frequency_spread_gate": (
            None
            if seed_record_frequency_spread_gate is None
            else float(seed_record_frequency_spread_gate)
        ),
        "dense_record_frequency_gate": (
            None
            if dense_record_frequency_gate is None
            else float(dense_record_frequency_gate)
        ),
        "worst_cut_discarded_weight_gate": (
            None
            if worst_cut_discarded_weight_gate is None
            else float(worst_cut_discarded_weight_gate)
        ),
        "total_discarded_weight_gate": (
            None
            if total_discarded_weight_gate is None
            else float(total_discarded_weight_gate)
        ),
        "min_peak_allocated_gib": (
            None
            if min_peak_allocated_gib is None
            else float(min_peak_allocated_gib)
        ),
        "min_peak_reserved_gib": (
            None
            if min_peak_reserved_gib is None
            else float(min_peak_reserved_gib)
        ),
        "resource_probe_policy": resource_policy,
        "claims_qt_mps_backend_execution": bundle_backend_executed,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scored_quantity_policy": (
            "CUDA memory resource probe is an execution/resource gate only; "
            "no new scored quantity"
        ),
    }
    payload["passed"] = passed
    payload["verdict"] = "pass" if passed else "fail"
    payload["content_hash"] = _stable_payload_hash(payload)
    _validate_qt_resource_probe_manifest(
        payload,
        expected_schedule=schedule,
        expected_bundle=bundle,
        expected_bonds=bonds,
        expected_trajectory_count=trajectory_count,
        expected_seeds=seeds,
        expected_device=dev,
        expected_max_branches=max_branches,
        expected_max_record_materialization_outcomes=record_budget,
        expected_microstep_count=microstep_count,
        expected_finite_step_order=finite_step_order,
        expected_convergence_record_probability_gate=(
            convergence_record_probability_gate
        ),
        expected_seed_record_frequency_spread_gate=(
            seed_record_frequency_spread_gate
        ),
        expected_dense_record_frequency_gate=dense_record_frequency_gate,
        expected_worst_cut_discarded_weight_gate=(
            worst_cut_discarded_weight_gate
        ),
        expected_total_discarded_weight_gate=total_discarded_weight_gate,
        expected_min_peak_allocated_gib=min_peak_allocated_gib,
        expected_min_peak_reserved_gib=min_peak_reserved_gib,
        expected_peak_allocated_bytes=peak_allocated,
        expected_peak_reserved_bytes=peak_reserved,
        expected_bundle_backend_executed=bundle_backend_executed,
    )
    return payload


def _execute_program(
    program: dict[str, Any],
    *,
    record_layout: Axis1ScheduleRecordLayout,
    device: str,
    max_bond: int | None,
    max_branches: int,
    microstep_count: int,
    finite_step_order: str,
) -> dict[str, Any]:
    import quimb.tensor as qtn

    step_order = _normalize_finite_step_order(finite_step_order)
    finite_step_policy = _finite_step_policy_name(step_order)
    expected_gate_occurrences = (
        _qt_expected_actual_split_occurrences(
            program,
            microstep_count=int(microstep_count),
            finite_step_order=step_order,
        )
        if max_bond is not None
        else ()
    )
    num_qubits = int(program["program"]["num_qubits"])
    z0 = np.array([1.0, 0.0], dtype=np.complex128)
    initial = qtn.MPS_product_state([z0] * num_qubits)
    initial.apply_to_arrays(
        lambda x: torch.as_tensor(x, dtype=torch.complex128, device=device)
    )
    branches: list[tuple[tuple[int, ...], float, Any]] = [((), 1.0, initial)]
    applied: list[dict[str, Any]] = []
    truncation_events: list[dict[str, Any]] = []
    max_observed_bond = max_mps_bond(branch[2] for branch in branches)
    measurement_keys = list(record_layout.measurement_keys)
    measurement_targets = list(record_layout.measurement_targets)
    static_branch_upper = 1
    for substep in program["program"]["substeps"]:
        next_branches: list[tuple[tuple[int, ...], float, Any]] = []
        summary = axis1_carrier_substep_summary(substep)
        static_branch_upper = _static_exact_branch_upper_after_substep(
            static_branch_upper,
            substep=substep,
            microstep_count=microstep_count,
            max_branches=max_branches,
        )
        if str(substep["substep_kind"]) == "reset":
            branches = _reset_branches_for_operations(
                branches,
                substep,
                device=device,
                max_branches=max_branches,
            )
            max_observed_bond = max(
                max_observed_bond,
                max_mps_bond(branch[2] for branch in branches),
            )
            applied.append(
                {
                    **summary,
                    "finite_step_policy": "boundary_only_no_generator_evolution",
                    "reset_boundary_policy": "nonselective_pauli_reset_internal_branches_no_record",
                    "static_branch_count_upper_bound_after_substep": (
                        static_branch_upper
                    ),
                    "max_observed_bond_after_substep": max_mps_bond(
                        branch[2] for branch in branches
                    ),
                }
            )
            continue
        if str(substep["substep_kind"]) != "measurement":
            branches = _evolve_branches(
                branches,
                substep,
                device=device,
                max_bond=max_bond,
                max_branches=max_branches,
                microstep_count=microstep_count,
                finite_step_order=step_order,
                truncation_events=truncation_events,
            )
            max_observed_bond = max(
                max_observed_bond,
                max_mps_bond(branch[2] for branch in branches),
            )
            applied.append(
                {
                    **summary,
                    "finite_step_policy": finite_step_policy,
                    "finite_step_order": step_order,
                    "microstep_count": int(microstep_count),
                    "static_branch_count_upper_bound_after_substep": (
                        static_branch_upper
                    ),
                    "max_observed_bond_after_substep": max_mps_bond(
                        branch[2] for branch in branches
                    ),
                }
            )
            continue

        boundary = record_layout.boundary_for_substep_id(substep["substep_id"])
        outcomes = _measurement_records(boundary.width)
        evolved_branches = (
            _evolve_branches(
                branches,
                substep,
                device=device,
                max_bond=max_bond,
                max_branches=max_branches,
                microstep_count=microstep_count,
                finite_step_order=step_order,
                truncation_events=truncation_events,
            )
            if _substep_has_evolution_terms(substep)
            else [(bits, weight, mps.copy()) for bits, weight, mps in branches]
        )
        for bits, weight, evolved in evolved_branches:
            projected_outcomes: list[tuple[list[int], Any]] = []
            raw_probabilities: list[float] = []
            for outcome in outcomes:
                projected, probability = _project_z_mps(
                    evolved,
                    targets=list(boundary.targets),
                    outcome_bits=outcome,
                    device=device,
                )
                projected_outcomes.append((outcome, projected))
                raw_probabilities.append(float(probability))
            mass = _require_qt_unit_probability_mass(
                raw_probabilities,
                name="QT exact measurement partition",
            )
            for outcome_index in mass.positive_indices:
                outcome, projected = projected_outcomes[outcome_index]
                probability = mass.values[outcome_index]
                projected = _apply_z_measurement_reset_if_requested(
                    projected,
                    boundary,
                    outcome_bits=outcome,
                    device=device,
                )
                next_branches.append(
                    (
                        bits + tuple(int(bit) for bit in outcome),
                        _qt_exact_conditioned_branch_weight(
                            weight,
                            probability,
                            mass.total,
                            name="QT exact measurement branch mass",
                        ),
                        projected,
                    )
                )
                if len(next_branches) > int(max_branches):
                    raise ValueError("restricted QT/MPS branch cap exceeded")
        branches = next_branches
        max_observed_bond = max(
            max_observed_bond,
            max_mps_bond(branch[2] for branch in branches),
        )
        applied.append(
            {
                **summary,
                "finite_step_policy": finite_step_policy,
                "finite_step_order": step_order,
                "microstep_count": int(microstep_count),
                "static_branch_count_upper_bound_after_substep": (
                    static_branch_upper
                ),
                "max_observed_bond_after_substep": max_mps_bond(
                    branch[2] for branch in branches
                ),
            }
        )

    probability_by_record: dict[tuple[int, ...], float] = {}
    for bits, weight, _mps in branches:
        probability_by_record[bits] = probability_by_record.get(bits, 0.0) + weight
    records = (
        _measurement_records(len(measurement_keys))
        if measurement_keys
        else [()]
    )
    probabilities = [
        float(probability_by_record.get(tuple(record), 0.0))
        for record in records
    ]
    projected_records = project_axis1_xor_records(record_layout, records)
    detector_names = list(projected_records.detector_names)
    detector_records = [list(row) for row in projected_records.detector_records]
    logical_names = list(projected_records.observable_names)
    logical_records = [list(row) for row in projected_records.observable_records]
    total = float(sum(probabilities))
    return {
        "initial_state": "computational_zero_mps",
        "site_order": list(range(num_qubits)),
        "physical_dimension": 2,
        "mps_library": "quimb.tensor.MatrixProductState",
        "array_backend": "torch_cuda_complex128",
        "hamiltonian_evolution_policy": "operator_family_order_product_formula",
        "collapse_evolution_policy": "local_product_channel_branching",
        "finite_step_policy": {
            "name": finite_step_policy,
            "order": step_order,
            "microstep_count": int(microstep_count),
            "microstep_dt_policy": "equal_substeps_dt_ns_div_microstep_count",
            "exact_summed_lindbladian_claim": False,
            "comparison_outcome_is_metric": False,
        },
        "trajectory_sampling": {
            "mode": "exact_branch_enumeration",
            "trajectory_count": None,
            "rng_seed": None,
            "rng_seed_required_for_acceptance": False,
            "rng_seed_was_explicit": False,
            "rng_backend": "not_used",
            "measurement_sampling_policy": "exact_joint_binary_branch_enumeration",
            "record_support_policy": _FULL_BINARY_RECORD_SUPPORT_POLICY,
            "probability_semantics": "exact_enumerated_branch_probabilities",
            "comparison_outcome_is_metric": False,
        },
        "exact_joint_generator_claim": False,
        "exact_summed_lindbladian_claim": False,
        "measurement_basis": "Z",
        "measurement_keys": measurement_keys,
        "measurement_targets": measurement_targets,
        "measurement_records": [list(record) for record in records],
        "record_probabilities": probabilities,
        "record_count": len(records),
        "total_probability": total,
        "total_probability_residual": abs(total - 1.0),
        "mps_truncation_ledger": build_mps_truncation_ledger(
            max_bond=max_bond,
            local_dims=(2,) * num_qubits,
            max_observed_bond=max_observed_bond,
            truncation_events=truncation_events,
            aggregation=aggregate_exact_branch_truncation_events(
                truncation_events,
                expected_gate_occurrences=(
                    expected_gate_occurrences if max_bond is not None else ()
                ),
            ),
        ),
        "applied_substeps": applied,
        "detector_records_emitted": bool(detector_names),
        "detector_names": detector_names,
        "detector_records": detector_records,
        "logical_observables_emitted": bool(logical_names),
        "logical_observable_names": logical_names,
        "logical_observable_records": logical_records,
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
        "claims_dense_channel_evidence": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
    }


def _execute_sampled_program(
    program: dict[str, Any],
    *,
    record_layout: Axis1ScheduleRecordLayout,
    device: str,
    max_bond: int | None,
    microstep_count: int,
    finite_step_order: str,
    trajectory_count: int,
    rng_seed: int | None,
) -> dict[str, Any]:
    import quimb.tensor as qtn

    step_order = _normalize_finite_step_order(finite_step_order)
    finite_step_policy = _finite_step_policy_name(step_order)
    expected_gate_occurrences = (
        _qt_expected_actual_split_occurrences(
            program,
            microstep_count=int(microstep_count),
            finite_step_order=step_order,
        )
        if max_bond is not None
        else ()
    )
    ntraj = int(trajectory_count)
    if ntraj <= 0:
        raise ValueError("trajectory_count must be positive")
    seed = 0 if rng_seed is None else int(rng_seed)
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    num_qubits = int(program["program"]["num_qubits"])
    z0 = np.array([1.0, 0.0], dtype=np.complex128)
    initial = qtn.MPS_product_state([z0] * num_qubits)
    initial.apply_to_arrays(
        lambda x: torch.as_tensor(x, dtype=torch.complex128, device=device)
    )

    records_by_bits: dict[tuple[int, ...], int] = {}
    applied: list[dict[str, Any]] = []
    for substep in program["program"]["substeps"]:
        summary = axis1_carrier_substep_summary(substep)
        if str(substep["substep_kind"]) == "reset":
            applied.append(
                {
                    **summary,
                    "finite_step_policy": "boundary_only_no_generator_evolution",
                    "reset_boundary_policy": (
                        "sampled_pauli_reset_internal_outcome_no_record"
                    ),
                    "sampled_trajectory_count": ntraj,
                    "max_observed_bond_after_substep": 0,
                }
            )
        else:
            applied.append(
                {
                    **summary,
                    "finite_step_policy": finite_step_policy,
                    "finite_step_order": step_order,
                    "microstep_count": int(microstep_count),
                    "sampled_trajectory_count": ntraj,
                    "sampled_collapse_term_count": 0,
                    "max_observed_bond_after_substep": 0,
                }
            )
    truncation_events: list[dict[str, Any]] = []
    max_observed_bond = max_mps_bond((initial,))
    measurement_keys = list(record_layout.measurement_keys)
    measurement_targets = list(record_layout.measurement_targets)

    for trajectory_index in range(ntraj):
        bits: tuple[int, ...] = ()
        state = initial.copy()
        for substep_index, substep in enumerate(program["program"]["substeps"]):
            collapse_count = 0
            if str(substep["substep_kind"]) == "reset":
                state = _sample_reset_for_operations(
                    state,
                    substep,
                    device=device,
                    generator=generator,
                )
            elif _substep_has_evolution_terms(substep):
                dt_micro = float(substep["dt_ns"]) / float(microstep_count)
                for microstep_index in range(int(microstep_count)):
                    if step_order == _FINITE_STEP_ORDER_STRANG:
                        _apply_hamiltonian_terms(
                            state,
                            substep,
                            device=device,
                            max_bond=max_bond,
                            branch_bits=bits,
                            truncation_events=truncation_events,
                            dt_ns=0.5 * dt_micro,
                            microstep_index=microstep_index,
                            microstep_count=int(microstep_count),
                            hamiltonian_pass_index=0,
                            trajectory_index=trajectory_index,
                        )
                        state, sampled = _sample_collapse_terms(
                            state,
                            substep,
                            device=device,
                            generator=generator,
                            dt_ns=dt_micro,
                        )
                        _apply_hamiltonian_terms(
                            state,
                            substep,
                            device=device,
                            max_bond=max_bond,
                            branch_bits=bits,
                            truncation_events=truncation_events,
                            dt_ns=0.5 * dt_micro,
                            microstep_index=microstep_index,
                            microstep_count=int(microstep_count),
                            hamiltonian_pass_index=1,
                            trajectory_index=trajectory_index,
                        )
                    else:
                        _apply_hamiltonian_terms(
                            state,
                            substep,
                            device=device,
                            max_bond=max_bond,
                            branch_bits=bits,
                            truncation_events=truncation_events,
                            dt_ns=dt_micro,
                            microstep_index=microstep_index,
                            microstep_count=int(microstep_count),
                            hamiltonian_pass_index=0,
                            trajectory_index=trajectory_index,
                        )
                        state, sampled = _sample_collapse_terms(
                            state,
                            substep,
                            device=device,
                            generator=generator,
                            dt_ns=dt_micro,
                        )
                    collapse_count += sampled
            max_observed_bond = max(
                max_observed_bond,
                max_mps_bond((state,)),
            )
            if str(substep["substep_kind"]) != "reset":
                applied[substep_index]["sampled_collapse_term_count"] = max(
                    int(applied[substep_index]["sampled_collapse_term_count"]),
                    int(collapse_count),
                )
            applied[substep_index]["max_observed_bond_after_substep"] = max(
                int(applied[substep_index]["max_observed_bond_after_substep"]),
                max_mps_bond((state,)),
            )
            if str(substep["substep_kind"]) != "measurement":
                continue
            boundary = record_layout.boundary_for_substep_id(substep["substep_id"])
            outcome, state = _sample_z_measurement(
                state,
                targets=list(boundary.targets),
                device=device,
                generator=generator,
            )
            state = _apply_z_measurement_reset_if_requested(
                state,
                boundary,
                outcome_bits=outcome,
                device=device,
            )
            bits = bits + tuple(int(bit) for bit in outcome)
        if len(bits) != record_layout.measurement_width:
            raise ValueError(
                "sampled QT/MPS outcome width does not match immutable Record layout"
            )
        records_by_bits[bits] = records_by_bits.get(bits, 0) + 1

    records = sorted(records_by_bits)
    record_counts = [int(records_by_bits[record]) for record in records]
    probabilities = [float(count) / float(ntraj) for count in record_counts]
    projected_records = project_axis1_xor_records(record_layout, records)
    detector_names = list(projected_records.detector_names)
    detector_records = [list(row) for row in projected_records.detector_records]
    logical_names = list(projected_records.observable_names)
    logical_records = [list(row) for row in projected_records.observable_records]
    return {
        "initial_state": "computational_zero_mps",
        "site_order": list(range(num_qubits)),
        "physical_dimension": 2,
        "mps_library": "quimb.tensor.MatrixProductState",
        "array_backend": "torch_cuda_complex128",
        "hamiltonian_evolution_policy": "operator_family_order_product_formula",
        "collapse_evolution_policy": "local_product_channel_branching",
        "finite_step_policy": {
            "name": finite_step_policy,
            "order": step_order,
            "microstep_count": int(microstep_count),
            "microstep_dt_policy": "equal_substeps_dt_ns_div_microstep_count",
            "exact_summed_lindbladian_claim": False,
            "comparison_outcome_is_metric": False,
        },
        "trajectory_sampling": {
            "mode": "sampled_product_channel_trajectories",
            "trajectory_count": ntraj,
            "rng_seed": seed,
            "rng_seed_required_for_acceptance": True,
            "rng_seed_was_explicit": rng_seed is not None,
            "rng_seed_default_policy": "default_zero_when_not_provided",
            "rng_backend": "torch.Generator(cuda)",
            "measurement_sampling_policy": (
                "sequential_conditional_single_site_z_v1"
            ),
            "record_support_policy": _OBSERVED_EMPIRICAL_RECORD_SUPPORT_POLICY,
            "zero_frequency_records_emitted": False,
            "probability_semantics": "empirical_record_frequencies",
            "comparison_outcome_is_metric": False,
        },
        "exact_joint_generator_claim": False,
        "exact_summed_lindbladian_claim": False,
        "measurement_basis": "Z",
        "measurement_keys": measurement_keys,
        "measurement_targets": measurement_targets,
        "measurement_records": [list(record) for record in records],
        "record_counts": record_counts,
        "record_probabilities": probabilities,
        "record_count": len(records),
        "total_probability": float(sum(probabilities)),
        "total_probability_residual": abs(float(sum(probabilities)) - 1.0),
        "mps_truncation_ledger": build_mps_truncation_ledger(
            max_bond=max_bond,
            local_dims=(2,) * num_qubits,
            max_observed_bond=max_observed_bond,
            truncation_events=truncation_events,
            aggregation=aggregate_sampled_truncation_events(
                truncation_events,
                trajectory_count=ntraj,
                expected_gate_occurrences=(
                    expected_gate_occurrences if max_bond is not None else ()
                ),
            ),
        ),
        "applied_substeps": applied,
        "detector_records_emitted": bool(detector_names),
        "detector_names": detector_names,
        "detector_records": detector_records,
        "logical_observables_emitted": bool(logical_names),
        "logical_observable_names": logical_names,
        "logical_observable_records": logical_records,
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
        "claims_dense_channel_evidence": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
    }


_DENSE_RECORD_EVIDENCE_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema",
        "verdict",
        "source_kind",
        "source_hash",
        "schedule_representability",
        "representability",
        "compiler_provenance",
        "primitive_registry",
        "selection_plan",
        "selection_partition",
        "readout_reset_instrument_spec",
        "coverage",
        "metric_reference",
        "representability_limits",
        "record_evidence",
        "probability_residual_passed",
        "passed",
        "content_hash",
    }
)
_DENSE_RECORD_EVIDENCE_FIELDS = frozenset(
    {
        "initial_state",
        "device",
        "dtype",
        "num_qubits",
        "applied_channel_count",
        "application_semantics",
        "same_substep_window_semantics",
        "measurement_basis",
        "measurement_bases",
        "measurement_basis_semantics",
        "reset_steps",
        "readout_reset_instrument_spec",
        "readout_assignment_steps",
        "measurement_keys",
        "measurement_steps",
        "measurement_records",
        "record_probabilities",
        "record_count",
        "total_probability",
        "total_probability_residual",
        "total_probability_residual_threshold",
        "applied_layers",
        "applied_steps",
        "detector_records_emitted",
        "logical_observables_emitted",
        "detector_names",
        "logical_observable_names",
        "detector_records",
        "logical_observable_records",
        "detector_marginals",
        "logical_observable_marginals",
        "claims_b8_artifact",
        "claims_decoder_integration",
        "claims_full_schedule_coverage",
        "claims_overlapping_window_joint_generator",
        "claims_axis2_source_projection",
        "record_layout_ref",
        "detector_observable_boundary",
        "epistemic_classes",
    }
)
_DENSE_RECORD_APPLIED_STEP_FIELDS = frozenset(
    {
        "application_index",
        "parallel_layer_index",
        "selection_id",
        "substep_id",
        "row_kind",
        "participant",
        "coupling_edges",
        "primitive_names",
        "mechanism_pair",
        "context_mechanisms",
        "ideal_controls",
        "lowered_mechanisms",
        "dt_ns",
        "channel_assembly",
    }
)
_DENSE_RECORD_IDEAL_CONTROL_FIELDS = frozenset(
    {
        "name",
        "gate_name",
        "generator_kind",
        "coefficient",
        "support",
        "source_step_indices",
        "epistemic_class",
    }
)
_DENSE_RECORD_LOWERED_MECHANISM_FIELDS = frozenset(
    {
        "name",
        "generator_kind",
        "coefficient",
        "support",
        "epistemic_class",
    }
)
_DENSE_RECORD_CHANNEL_ASSEMBLY_FIELDS = frozenset(
    {
        "assembled_by",
        "assembly_semantics",
        "contains_ideal_control_hamiltonian",
        "ideal_control_names",
        "contains_serialized_channel_payload",
        "num_kraus",
        "dimension",
        "factorization",
        "component_local_qubits",
        "component_dimensions",
        "component_num_kraus",
    }
)


def _require_dense_exact_field_set(
    value: Any,
    expected_fields: frozenset[str],
    *,
    context: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise TypeError(f"{context} must be an exact mapping")
    if set(value) != expected_fields:
        missing = sorted(expected_fields.difference(value))
        extra = sorted(set(value).difference(expected_fields))
        raise ValueError(
            f"{context} fields do not match registered production shape; "
            f"missing={missing!r} extra={extra!r}"
        )
    return value


def _dense_record_expected_reset_steps(
    schedule: SubstepSchedule,
) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    semantics = {
        "R": "nonselective_z_reset_to_zero_no_record",
        "RZ": "nonselective_z_reset_to_zero_no_record",
        "RX": "nonselective_x_reset_to_plus_eigenstate_no_record",
        "RY": "nonselective_y_reset_to_plus_eigenstate_no_record",
    }
    for substep in schedule.substeps:
        if substep.kind != "reset":
            continue
        for operation in substep.operations:
            if operation.name not in semantics:
                raise ValueError(
                    "trusted Dense Record schedule contains an unsupported reset "
                    f"operation {operation.name!r}"
                )
            expected.append(
                {
                    "substep_id": substep.substep_id,
                    "operation": operation.to_manifest(),
                    "reset_semantics": semantics[operation.name],
                }
            )
    return expected


def _dense_record_expected_measurement_steps(
    schedule: SubstepSchedule,
) -> list[dict[str, Any]]:
    return [
        {
            "substep_id": substep.substep_id,
            "operation": operation.to_manifest(),
            "measurement_keys": list(operation.measurement_keys),
            "reset_after_measurement": bool(
                operation.reset_after_measurement
            ),
        }
        for substep in schedule.substeps
        if substep.kind == "measurement"
        for operation in substep.operations
    ]


def _validate_dense_generator_records(
    records: Any,
    *,
    expected_fields: frozenset[str],
    participant_count: int,
    epistemic_class: str,
    context: str,
) -> list[dict[str, Any]]:
    if type(records) is not list:
        raise TypeError(f"{context} must be an exact list")
    for index, item in enumerate(records):
        item_context = f"{context}[{index}]"
        record = _require_dense_exact_field_set(
            item,
            expected_fields,
            context=item_context,
        )
        for name in ("name", "generator_kind", "epistemic_class"):
            _require_nonempty_text_field(record, name, context=item_context)
        if record["epistemic_class"] != epistemic_class:
            raise ValueError(
                f"{item_context}.epistemic_class is not registered"
            )
        coefficient = record.get("coefficient")
        if (
            isinstance(coefficient, bool)
            or not isinstance(coefficient, Real)
            or not math.isfinite(float(coefficient))
        ):
            raise TypeError(f"{item_context}.coefficient must be a finite real")
        support = record.get("support")
        if type(support) is not list or not support:
            raise TypeError(f"{item_context}.support must be a nonempty exact list")
        if any(
            type(site) is not int
            or site < 0
            or site >= participant_count
            for site in support
        ):
            raise ValueError(f"{item_context}.support is outside the local window")
        if len(set(support)) != len(support):
            raise ValueError(f"{item_context}.support repeats a local site")
        if expected_fields is _DENSE_RECORD_IDEAL_CONTROL_FIELDS:
            if record["generator_kind"] not in {
                "hamiltonian",
                "su2_axis_hamiltonian",
            }:
                raise ValueError(f"{item_context}.generator_kind is not registered")
            if record["name"] != f"CTRL_{record['gate_name']}":
                raise ValueError(f"{item_context}.name is not bound to gate_name")
            source_indices = record.get("source_step_indices")
            if type(source_indices) is not list or any(
                type(step) is not int or step < 0 for step in source_indices
            ):
                raise TypeError(
                    f"{item_context}.source_step_indices must be exact integers"
                )
        elif record["generator_kind"] not in {"hamiltonian", "collapse"}:
            raise ValueError(f"{item_context}.generator_kind is not registered")
    return records


def _validate_dense_channel_assembly(
    assembly: Any,
    *,
    ideal_controls: list[dict[str, Any]],
    participant_count: int,
    num_qubits: int,
    context: str,
) -> None:
    channel = _require_dense_exact_field_set(
        assembly,
        _DENSE_RECORD_CHANNEL_ASSEMBLY_FIELDS,
        context=context,
    )
    _require_bound_qt_field(
        channel,
        "assembled_by",
        expected=(
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        context=context,
    )
    _require_bound_qt_field(
        channel,
        "assembly_semantics",
        expected="single_joint_generator_expm",
        context=context,
    )
    _require_bound_qt_field(
        channel,
        "contains_ideal_control_hamiltonian",
        expected=bool(ideal_controls),
        context=context,
    )
    _require_bound_qt_field(
        channel,
        "ideal_control_names",
        expected=[str(record["name"]) for record in ideal_controls],
        context=context,
    )
    _require_bound_qt_field(
        channel,
        "contains_serialized_channel_payload",
        expected=False,
        context=context,
    )
    _require_bound_qt_field(
        channel,
        "dimension",
        expected=int(2**num_qubits),
        context=context,
    )
    _require_bound_qt_field(
        channel,
        "factorization",
        expected="coupling_component_tensor_product_exact",
        context=context,
    )
    num_kraus = channel.get("num_kraus")
    if type(num_kraus) is not int or num_kraus <= 0:
        raise TypeError(f"{context}.num_kraus must be a positive exact integer")
    components = channel.get("component_local_qubits")
    dimensions = channel.get("component_dimensions")
    component_kraus = channel.get("component_num_kraus")
    if not all(type(value) is list for value in (components, dimensions, component_kraus)):
        raise TypeError(f"{context} component metadata must use exact lists")
    if not components or not (
        len(components) == len(dimensions) == len(component_kraus)
    ):
        raise ValueError(f"{context} component metadata lengths are inconsistent")
    seen_sites: set[int] = set()
    for component_index, sites in enumerate(components):
        if type(sites) is not list or not sites:
            raise TypeError(
                f"{context}.component_local_qubits[{component_index}] must be "
                "a nonempty exact list"
            )
        if any(
            type(site) is not int
            or site < 0
            or site >= participant_count
            for site in sites
        ):
            raise ValueError(f"{context} component contains an invalid local site")
        if seen_sites.intersection(sites) or len(set(sites)) != len(sites):
            raise ValueError(f"{context} components overlap or repeat a local site")
        seen_sites.update(sites)
        if type(dimensions[component_index]) is not int or dimensions[
            component_index
        ] != 2 ** len(sites):
            raise ValueError(f"{context} component dimension is inconsistent")
        if (
            type(component_kraus[component_index]) is not int
            or component_kraus[component_index] <= 0
        ):
            raise TypeError(
                f"{context} component Kraus counts must be positive exact integers"
            )
    if sum(component_kraus) != num_kraus:
        raise ValueError(f"{context}.num_kraus is not the component-count sum")


def _validate_dense_record_applied_metadata(
    record: dict[str, Any],
    *,
    schedule: SubstepSchedule,
    selection_layers: tuple[Any, ...],
    context: str,
) -> None:
    expected_layers = [
        {
            "parallel_layer_index": layer_index,
            "substep_id": layer.substep_id,
            "selection_ids": list(layer.selection_ids),
            "window_count": len(layer.selections),
            "same_substep_semantics": (
                "parallel_disjoint_local_windows_or_single_union_support"
            ),
        }
        for layer_index, layer in enumerate(selection_layers)
    ]
    _require_bound_qt_field(
        record,
        "applied_layers",
        expected=expected_layers,
        context=context,
    )
    expected_selections = [
        (layer_index, selection)
        for layer_index, layer in enumerate(selection_layers)
        for selection in layer.selections
    ]
    _require_bound_qt_field(
        record,
        "applied_channel_count",
        expected=len(expected_selections),
        context=context,
    )
    applied_steps = record.get("applied_steps")
    if type(applied_steps) is not list:
        raise TypeError(f"{context}.applied_steps must be an exact list")
    if len(applied_steps) != len(expected_selections):
        raise ValueError(f"{context}.applied_steps count is not schedule-bound")
    for application_index, (layer_index, selection) in enumerate(
        expected_selections
    ):
        step_context = f"{context}.applied_steps[{application_index}]"
        step = _require_dense_exact_field_set(
            applied_steps[application_index],
            _DENSE_RECORD_APPLIED_STEP_FIELDS,
            context=step_context,
        )
        for field, expected in (
            ("application_index", application_index),
            ("parallel_layer_index", layer_index),
            ("selection_id", selection.selection_id),
            ("substep_id", selection.substep_id),
            ("row_kind", selection.row_kind),
            ("participant", list(selection.participant)),
            ("coupling_edges", [list(edge) for edge in selection.coupling_edges]),
            ("primitive_names", list(selection.primitive_names)),
            ("mechanism_pair", list(selection.mechanism_pair)),
            ("context_mechanisms", list(selection.context_mechanisms)),
            ("dt_ns", float(selection.dt_ns_nominal)),
        ):
            _require_bound_qt_field(
                step,
                field,
                expected=expected,
                context=step_context,
            )
        ideal_controls = _validate_dense_generator_records(
            step.get("ideal_controls"),
            expected_fields=_DENSE_RECORD_IDEAL_CONTROL_FIELDS,
            participant_count=len(selection.participant),
            epistemic_class="a",
            context=f"{step_context}.ideal_controls",
        )
        _validate_dense_generator_records(
            step.get("lowered_mechanisms"),
            expected_fields=_DENSE_RECORD_LOWERED_MECHANISM_FIELDS,
            participant_count=len(selection.participant),
            epistemic_class="c",
            context=f"{step_context}.lowered_mechanisms",
        )
        _validate_dense_channel_assembly(
            step.get("channel_assembly"),
            ideal_controls=ideal_controls,
            participant_count=len(selection.participant),
            num_qubits=int(schedule.num_qubits),
            context=f"{step_context}.channel_assembly",
        )


def _validate_dense_record_marginals(
    record: dict[str, Any],
    *,
    rows_field: str,
    marginals_field: str,
    context: str,
) -> None:
    rows = record[rows_field]
    probabilities = record["record_probabilities"]
    width = len(rows[0]) if rows else 0
    expected = [
        sum(float(probability) * int(row[column]) for row, probability in zip(
            rows,
            probabilities,
            strict=True,
        ))
        for column in range(width)
    ]
    marginals = record.get(marginals_field)
    if type(marginals) is not list or len(marginals) != len(expected):
        raise ValueError(f"{context}.{marginals_field} has the wrong shape")
    for index, (actual, expected_value) in enumerate(
        zip(marginals, expected, strict=True)
    ):
        if (
            isinstance(actual, bool)
            or not isinstance(actual, Real)
            or not math.isfinite(float(actual))
        ):
            raise TypeError(
                f"{context}.{marginals_field}[{index}] must be a finite real"
            )
        if abs(float(actual) - expected_value) > NUMERICAL_ZERO:
            raise ValueError(
                f"{context}.{marginals_field}[{index}] is not probability-bound"
            )


def _validated_dense_record_evidence(
    schedule: SubstepSchedule,
    dense: Any,
    *,
    device: str,
    context: str,
) -> dict[str, Any]:
    dense = _require_dense_exact_field_set(
        dense,
        _DENSE_RECORD_EVIDENCE_TOP_LEVEL_FIELDS,
        context=context,
    )
    selection_plan = build_axis1_schedule_selection_plan(schedule)
    selection_layers = axis1_selection_layers_in_schedule_order(
        schedule,
        selection_plan.selections,
        consumer_name="Axis-1 selected-window evidence",
    )
    _require_bound_qt_field(
        dense,
        "schema",
        expected=AXIS1_RECORD_EVIDENCE_SCHEMA,
        context=context,
    )
    _require_bound_qt_field(
        dense,
        "representability",
        expected=AXIS1_RECORD_EVIDENCE_REPRESENTABILITY,
        context=context,
    )
    _require_bound_qt_field(
        dense,
        "source_kind",
        expected=schedule.source_kind,
        context=context,
    )
    _require_bound_qt_field(
        dense,
        "source_hash",
        expected=schedule.source_hash,
        context=context,
    )
    _require_bound_qt_field(
        dense,
        "schedule_representability",
        expected=schedule.representability,
        context=context,
    )
    _require_bound_qt_field(dense, "passed", expected=True, context=context)
    _require_bound_qt_field(dense, "verdict", expected="pass", context=context)
    _require_bound_qt_field(
        dense,
        "probability_residual_passed",
        expected=True,
        context=context,
    )
    _validate_qt_payload_content_hash(dense, context=context)
    expected_instrument = Axis1ReadoutResetInstrumentSpec().to_manifest()
    static_top_level_fields = {
        "compiler_provenance": {
            "schedule_seal_schema": COMPILER_SCHEDULE_SEAL_SCHEMA,
            "schedule_seal_valid": has_valid_compiler_schedule_seal(schedule),
            "schedule_seal_public": False,
            "generated_substeps": all(
                substep.generated_by_compiler for substep in schedule.substeps
            ),
        },
        "primitive_registry": default_axis1_primitive_registry().to_manifest(),
        "selection_plan": selection_plan.to_manifest(),
        "selection_partition": axis1_selection_partition_manifest(
            selection_layers
        ),
        "coverage": _coverage_manifest(schedule, selection_plan),
        "metric_reference": "docs/METRICS.md#forward-fidelity--coupling-metrics",
        "representability_limits": (
            "selected local or union-support joint channels plus exact Pauli-basis "
            "measurement branch enumeration; detector/logical records only when "
            "public XOR wiring is present, no .b8 artifact, no decoder output, "
            "no Axis-2 source timeline, no leakage/qutrit integration"
        ),
    }
    for field, expected in static_top_level_fields.items():
        _require_bound_qt_field(
            dense,
            field,
            expected=expected,
            context=context,
        )
    _require_bound_qt_field(
        dense,
        "readout_reset_instrument_spec",
        expected=expected_instrument,
        context=context,
    )
    record_context = f"{context}.record_evidence"
    record = _require_dense_exact_field_set(
        dense.get("record_evidence"),
        _DENSE_RECORD_EVIDENCE_FIELDS,
        context=record_context,
    )
    layout = axis1_record_layout_from_schedule(schedule)
    expected_measurement_bases = sorted(set(layout.measurement_bases))
    static_record_fields = {
        "initial_state": "computational_zero_density_matrix",
        "dtype": "complex128",
        "application_semantics": (
            "schedule_order_selected_joint_channels_with_parallel_disjoint_or_union_support_layers_then_measurements"
        ),
        "same_substep_window_semantics": (
            "selected windows sharing a substep must either be qubit-disjoint or represented "
            "as a single union-support joint channel; overlapping selected windows fail closed"
        ),
        "measurement_basis": (
            "Z" if expected_measurement_bases == ["Z"] else "mixed_pauli"
        ),
        "measurement_basis_semantics": (
            "X/Y measurements and resets are implemented by exact basis rotation "
            "before Z-branch enumeration and rotation back afterward"
        ),
        "reset_steps": _dense_record_expected_reset_steps(schedule),
        "readout_assignment_steps": [],
        "measurement_steps": _dense_record_expected_measurement_steps(schedule),
        "total_probability_residual_threshold": _TOTAL_PROBABILITY_RESIDUAL_GATE,
        "detector_observable_boundary": (
            "public schedule XOR wiring only; no decoder output"
        ),
        "epistemic_classes": {
            "joint_channel_application_semantics": "a",
            "measurement_branch_enumeration": "a",
            "readout_assignment_map_application": "a",
            "readout_assignment_probability_values": "a",
            "reset_flip_channel_application": "a",
            "reset_flip_probability_values": "a",
            "probability_residual_threshold": "c",
            "detector_logical_xor_projection": "a",
            "b8_non_emission": "a",
        },
    }
    for field, expected in static_record_fields.items():
        _require_bound_qt_field(
            record,
            field,
            expected=expected,
            context=record_context,
        )
    _require_bound_qt_field(
        record,
        "device",
        expected=normalize_mps_device(device),
        context=record_context,
    )
    _require_bound_qt_field(
        record,
        "num_qubits",
        expected=schedule.num_qubits,
        context=record_context,
    )
    _require_bound_qt_field(
        record,
        "measurement_keys",
        expected=list(layout.measurement_keys),
        context=record_context,
    )
    _require_bound_qt_field(
        record,
        "measurement_bases",
        expected=expected_measurement_bases,
        context=record_context,
    )
    _require_bound_qt_field(
        record,
        "record_layout_ref",
        expected=dict(schedule.record_layout_ref),
        context=record_context,
    )
    _require_bound_qt_field(
        record,
        "readout_reset_instrument_spec",
        expected=expected_instrument,
        context=record_context,
    )
    _validate_dense_record_applied_metadata(
        record,
        schedule=schedule,
        selection_layers=selection_layers,
        context=record_context,
    )
    execution = {
        "measurement_keys": record.get("measurement_keys"),
        "measurement_targets": list(layout.measurement_targets),
        "measurement_records": record.get("measurement_records"),
        "record_probabilities": record.get("record_probabilities"),
        "record_count": record.get("record_count"),
        "total_probability": record.get("total_probability"),
        "total_probability_residual": record.get(
            "total_probability_residual"
        ),
    }
    _validate_qt_record_execution_payload(
        execution,
        sampled=False,
        trajectory_count=None,
    )
    residual = record.get("total_probability_residual")
    if not _is_finite_nonnegative_real(residual):
        raise ValueError(
            f"{context}.record_evidence.total_probability_residual must be "
            "a finite nonnegative real"
        )
    expected_residual = abs(1.0 - float(execution["total_probability"]))
    if (
        abs(float(residual) - expected_residual) > NUMERICAL_ZERO
        or float(residual) > _TOTAL_PROBABILITY_RESIDUAL_GATE
    ):
        raise ValueError(
            f"{context}.record_evidence probability residual is inconsistent"
        )
    _validate_axis1_projected_record_payload(
        layout,
        record,
        context=record_context,
    )
    _validate_dense_record_marginals(
        record,
        rows_field="detector_records",
        marginals_field="detector_marginals",
        context=record_context,
    )
    _validate_dense_record_marginals(
        record,
        rows_field="logical_observable_records",
        marginals_field="logical_observable_marginals",
        context=record_context,
    )
    for claim in (
        "claims_b8_artifact",
        "claims_decoder_integration",
        "claims_full_schedule_coverage",
        "claims_overlapping_window_joint_generator",
        "claims_axis2_source_projection",
    ):
        _require_bound_qt_field(
            record,
            claim,
            expected=False,
            context=record_context,
        )
    return record


def _dense_record_certification(
    schedule: SubstepSchedule,
    *,
    program: dict[str, Any],
    execution: dict[str, Any],
    device: str,
) -> dict[str, Any]:
    if execution.get("trajectory_sampling", {}).get("mode") != "exact_branch_enumeration":
        return {
            "executed": False,
            "reason": "sampled_trajectory_empirical_probabilities_not_exact_dense_certified",
            "comparison_outcome_is_metric": False,
        }
    if _require_exact_bool_field(program, "requires_scalable_backend"):
        return {
            "executed": False,
            "reason": "schedule_contains_scalable_required_rows",
            "comparison_outcome_is_metric": False,
        }
    if not execution["measurement_keys"]:
        return {
            "executed": False,
            "reason": "schedule_has_no_measurement_records",
            "comparison_outcome_is_metric": False,
        }
    try:
        dense = axis1_measurement_record_evidence_manifest(schedule, device=device)
    except Exception as exc:  # pragma: no cover - defensive manifest explanation.
        return {
            "executed": False,
            "reason": "dense_jointL_record_evidence_unavailable",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "comparison_outcome_is_metric": False,
        }
    dense_record = _validated_dense_record_evidence(
        schedule,
        dense,
        device=device,
        context="dense record evidence",
    )
    dense_schema = dense["schema"]
    dense_hash = dense["content_hash"]
    carrier_records = _normalize_record_matrix(
        execution["measurement_records"],
        name="carrier_measurement_records",
    )
    oracle_records = _normalize_record_matrix(
        dense_record["measurement_records"],
        name="oracle_measurement_records",
    )
    mps_probs = _normalize_probability_distribution(
        execution["record_probabilities"],
        name="carrier_record_probabilities",
    )
    dense_probs = _normalize_probability_distribution(
        dense_record["record_probabilities"],
        name="oracle_record_probabilities",
    )
    if len(carrier_records) != len(mps_probs):
        raise ValueError(
            "carrier_record_probabilities length must match measurement_records"
        )
    if len(oracle_records) != len(dense_probs):
        raise ValueError(
            "oracle_record_probabilities length must match measurement_records"
        )
    if oracle_records != carrier_records:
        return {
            "executed": True,
            "passed": False,
            "reason": "measurement_record_order_mismatch",
            "dense_evidence_schema": dense_schema,
            "dense_evidence_content_hash": dense_hash,
            "comparison_outcome_is_metric": False,
        }
    residual = max(
        (abs(a - b) for a, b in zip(dense_probs, mps_probs, strict=True)),
        default=0.0,
    )
    threshold = _DENSE_RECORD_CERTIFICATION_GATE
    return {
        "executed": True,
        "passed": bool(residual <= threshold),
        "dense_evidence_schema": dense_schema,
        "dense_evidence_content_hash": dense_hash,
        "dense_representability": dense["representability"],
        "comparison_object": "record_probabilities",
        "max_abs_probability_difference": float(residual),
        "threshold": threshold,
        "threshold_epistemic_class": "c",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }


def _blocked_restricted_acceptance_policy(
    *,
    blocked_reason: str,
    finite_step_order: str,
    finite_step_policy: str,
    microstep_count: int,
    trajectory_count: int | None,
    rng_seed: int | None,
    max_bond: int | None,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
) -> dict[str, Any]:
    truncation_gate = _truncation_gate_result(
        {
            "explicit_truncation_requested": max_bond is not None,
            "discarded_weight_ledger_complete": False,
            "discarded_weight_sum": 0.0,
            "worst_cut_discarded_weight": 0.0,
        },
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    return {
        "schema": _AXIS1_QT_MPS_RESTRICTED_ACCEPTANCE_POLICY_SCHEMA,
        "policy_role": "restricted_execution_acceptance_not_metric",
        "execution_status": "blocked",
        "certification_status": "not_evaluated",
        "diagnostic_only": False,
        "accepted_for_restricted_execution": False,
        "accepted_for_exact_dense_probability_evidence": False,
        "accepted_for_sampled_execution_evidence": False,
        "accepted_for_production_scalable_backend": False,
        "blocked_reason": str(blocked_reason),
        "finite_step": {
            "order": _normalize_finite_step_order(finite_step_order),
            "policy": str(finite_step_policy),
            "microstep_count": int(microstep_count),
            "dense_window_certification_status": "not_executed_backend_blocked",
            "exact_summed_lindbladian_claim": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "trajectory": {
            "mode": (
                "sampled_product_channel_trajectories"
                if trajectory_count is not None
                else "exact_branch_enumeration"
            ),
            "trajectory_count": None if trajectory_count is None else int(trajectory_count),
            "rng_seed": None if rng_seed is None else int(rng_seed),
            "rng_seed_required_for_acceptance": bool(trajectory_count is not None),
            "rng_seed_was_explicit": False,
            "accepted_as_exact_probability_evidence": False,
            "accepted_as_empirical_record_evidence": False,
            "single_trajectory_density_claim": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "mps_truncation": {
            "max_bond": None if max_bond is None else int(max_bond),
            "gate": truncation_gate,
            "accepted_as_exact_bond_representation": bool(max_bond is None),
            "accepted_as_finite_bond_candidate": False,
            "accepted_as_production_error_bound": False,
            "epistemic_class": "c",
        },
        "overcap": {
            "dense_fallback_forbidden": True,
            "accepted_as_restricted_overcap_execution": False,
            "accepted_as_production_scalable_backend": False,
            "epistemic_class": "a/c",
        },
        "production_blockers": [
            "restricted_backend_failed_closed",
            "production_error_control_policy_not_established",
            "large_code_acceptance_not_established",
        ],
        "scored_quantity_policy": "policy ledger only; no new scored quantity",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }


def _restricted_acceptance_policy(
    *,
    program: dict[str, Any],
    execution: dict[str, Any],
    record_materialization_preflight: dict[str, Any],
    certification: dict[str, Any],
    finite_step_order: str,
    finite_step_policy: str,
    max_bond: int | None,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
) -> dict[str, Any]:
    step_order = _normalize_finite_step_order(finite_step_order)
    sampling = execution["trajectory_sampling"]
    if not isinstance(sampling, dict):
        raise TypeError("trajectory_sampling must be a mapping")
    mode = sampling["mode"]
    if not isinstance(mode, str):
        raise TypeError("trajectory_sampling.mode must be a string")
    if mode not in {
        "exact_branch_enumeration",
        "sampled_product_channel_trajectories",
    }:
        raise ValueError("trajectory_sampling.mode is not registered")
    exact_branch_enumeration = mode == "exact_branch_enumeration"
    sampled_trajectories = mode == "sampled_product_channel_trajectories"
    rng_seed_was_explicit = _require_exact_bool_field(
        sampling,
        "rng_seed_was_explicit",
    )
    rng_seed_required_for_acceptance = _require_exact_bool_field(
        sampling,
        "rng_seed_required_for_acceptance",
        default=sampled_trajectories,
    )
    sampling_comparison_is_metric = _require_exact_bool_field(
        sampling,
        "comparison_outcome_is_metric",
        default=False,
    )
    if rng_seed_required_for_acceptance != sampled_trajectories:
        raise ValueError(
            "trajectory_sampling.rng_seed_required_for_acceptance must agree "
            "with sampled execution"
        )
    if sampling_comparison_is_metric:
        raise ValueError(
            "trajectory_sampling.comparison_outcome_is_metric must be false"
        )
    expected_measurement_sampling_policy = (
        "sequential_conditional_single_site_z_v1"
        if sampled_trajectories
        else "exact_joint_binary_branch_enumeration"
    )
    if sampling.get("measurement_sampling_policy") != (
        expected_measurement_sampling_policy
    ):
        raise ValueError(
            "trajectory_sampling.measurement_sampling_policy does not match "
            "the registered execution mode"
        )
    expected_record_support_policy = (
        _OBSERVED_EMPIRICAL_RECORD_SUPPORT_POLICY
        if sampled_trajectories
        else _FULL_BINARY_RECORD_SUPPORT_POLICY
    )
    if sampling.get("record_support_policy") != expected_record_support_policy:
        raise ValueError(
            "trajectory_sampling.record_support_policy does not match the "
            "registered execution mode"
        )
    expected_probability_semantics = (
        "empirical_record_frequencies"
        if sampled_trajectories
        else "exact_enumerated_branch_probabilities"
    )
    if sampling.get("probability_semantics") != expected_probability_semantics:
        raise ValueError(
            "trajectory_sampling.probability_semantics does not match the "
            "registered execution mode"
        )
    if sampled_trajectories:
        if _require_exact_bool_field(
            sampling,
            "zero_frequency_records_emitted",
        ):
            raise ValueError(
                "trajectory_sampling.zero_frequency_records_emitted must be false"
            )
    elif "zero_frequency_records_emitted" in sampling:
        raise ValueError(
            "exact branch execution cannot report sampled zero-frequency policy"
        )
    if sampled_trajectories:
        sampling_trajectory_count = _normalize_nonnegative_index(
            sampling["trajectory_count"],
            name="trajectory_sampling.trajectory_count",
        )
        if sampling_trajectory_count <= 0:
            raise ValueError("trajectory_sampling.trajectory_count must be positive")
        normalized_rng_seed = _normalize_integer_index(
            sampling.get("rng_seed"),
            name="trajectory_sampling.rng_seed",
        )
    else:
        if sampling.get("trajectory_count") is not None:
            raise ValueError(
                "exact branch execution must report trajectory_count=None"
            )
        if sampling.get("rng_seed") is not None or rng_seed_was_explicit:
            raise ValueError(
                "exact branch execution cannot report a trajectory RNG seed"
            )
        sampling_trajectory_count = None
        normalized_rng_seed = None
    _validate_qt_record_materialization_preflight_payload(
        record_materialization_preflight,
        execution=execution,
        sampled=sampled_trajectories,
        trajectory_count=sampling_trajectory_count,
    )
    has_measurement_records = _validate_qt_record_execution_payload(
        execution,
        sampled=sampled_trajectories,
        trajectory_count=sampling_trajectory_count,
    )
    requires_scalable = _require_exact_bool_field(
        program,
        "requires_scalable_backend",
    )
    raw_residual = execution["total_probability_residual"]
    residual_is_valid = _is_finite_nonnegative_real(raw_residual)
    residual = float(raw_residual) if residual_is_valid else None
    residual_ok = bool(
        residual_is_valid
        and residual is not None
        and residual <= _TOTAL_PROBABILITY_RESIDUAL_GATE
    )
    dense_executed = _require_exact_bool_field(
        certification,
        "executed",
    )
    dense_passed = (
        _require_exact_bool_field(certification, "passed")
        if dense_executed
        else _require_exact_bool_field(certification, "passed", default=False)
    )
    certification_comparison_is_metric = _require_exact_bool_field(
        certification,
        "comparison_outcome_is_metric",
    )
    if not dense_executed and dense_passed:
        raise ValueError("non-executed dense certification cannot pass")
    dense_positive_evidence_valid = False
    if dense_executed and dense_passed:
        dense_schema = _require_nonempty_text_field(
            certification,
            "dense_evidence_schema",
            context="certification",
        )
        dense_content_hash = _require_nonempty_text_field(
            certification,
            "dense_evidence_content_hash",
            context="certification",
        )
        comparison_object = _require_nonempty_text_field(
            certification,
            "comparison_object",
            context="certification",
        )
        if dense_schema != AXIS1_RECORD_EVIDENCE_SCHEMA:
            raise ValueError(
                "certification.dense_evidence_schema is not the registered Record oracle"
            )
        _normalize_sha256_text(
            dense_content_hash,
            name="certification.dense_evidence_content_hash",
        )
        if comparison_object != "record_probabilities":
            raise ValueError(
                "certification.comparison_object must be record_probabilities"
            )
        if certification_comparison_is_metric:
            raise ValueError(
                "QT dense max-probability residual is not a registered scored metric"
            )
        observed_difference = normalize_optional_mps_nonnegative_real(
            certification["max_abs_probability_difference"],
            name="certification.max_abs_probability_difference",
        )
        threshold = normalize_optional_mps_nonnegative_real(
            certification["threshold"],
            name="certification.threshold",
        )
        if observed_difference is None or threshold is None:
            raise ValueError("passing certification requires numeric evidence")
        if threshold != _DENSE_RECORD_CERTIFICATION_GATE:
            raise ValueError(
                "certification.threshold must equal the registered dense Record gate"
            )
        if dense_passed != (observed_difference <= threshold):
            raise ValueError(
                "certification.passed must equal "
                "max_abs_probability_difference <= threshold"
            )
        dense_positive_evidence_valid = bool(dense_schema and dense_content_hash)
    dense_status = _dense_certification_status(certification)
    exact_dense_probability_candidate = bool(
        exact_branch_enumeration
        and has_measurement_records
        and dense_executed
        and dense_passed
        and dense_positive_evidence_valid
        and not requires_scalable
    )
    sampled_execution_candidate = bool(
        sampled_trajectories
        and has_measurement_records
        and residual_ok
        and rng_seed_was_explicit
        and not requires_scalable
        and not (dense_executed and not dense_passed)
    )
    accepted_restricted = bool(
        residual_ok
        and (
            exact_dense_probability_candidate
            or sampled_execution_candidate
        )
    )
    ledger = execution["mps_truncation_ledger"]
    explicit_truncation = _require_exact_bool_field(
        ledger,
        "explicit_truncation_requested",
    )
    truncation_ledger_complete = _require_exact_bool_field(
        ledger,
        "discarded_weight_ledger_complete",
    )
    accepted_as_exact_bond_representation = _require_exact_bool_field(
        ledger,
        "accepted_as_exact_bond_representation",
    )
    normalized_max_bond = (
        None
        if max_bond is None
        else normalize_mps_max_bond(max_bond, allow_none=False)
    )
    if explicit_truncation != (normalized_max_bond is not None):
        raise ValueError(
            "explicit_truncation_requested must agree with max_bond"
        )
    exact_bond_dimension_sufficient = _normalize_nonnegative_index(
        ledger["exact_bond_dimension_sufficient"],
        name="exact_bond_dimension_sufficient",
    )
    if exact_bond_dimension_sufficient <= 0:
        raise ValueError("exact_bond_dimension_sufficient must be positive")
    expected_exact_bond_representation = bool(
        normalized_max_bond is None
        or normalized_max_bond >= exact_bond_dimension_sufficient
    )
    if accepted_as_exact_bond_representation != expected_exact_bond_representation:
        raise ValueError(
            "accepted_as_exact_bond_representation must agree with max_bond"
        )
    n_truncating_ops = _normalize_nonnegative_index(
        ledger["n_truncating_ops"],
        name="n_truncating_ops",
    )
    truncation_gate = _truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    discarded_sum = truncation_gate["observed_total_discarded_weight"]
    worst_discarded = truncation_gate["observed_worst_cut_discarded_weight"]
    if not explicit_truncation:
        if n_truncating_ops != 0 or discarded_sum != 0.0 or worst_discarded != 0.0:
            raise ValueError(
                "unbounded MPS execution cannot report truncation loss"
            )
    if (
        n_truncating_ops == 0
        and discarded_sum is not None
        and worst_discarded is not None
        and (discarded_sum != 0.0 or worst_discarded != 0.0)
    ):
        raise ValueError(
            "zero truncating operations cannot carry nonzero truncation loss"
        )
    if worst_discarded is not None and worst_discarded > 0.0 and n_truncating_ops == 0:
        raise ValueError(
            "positive worst-cut loss requires a truncating operation"
        )
    truncation_observations_valid = bool(
        discarded_sum is not None and worst_discarded is not None
    )
    truncation_detected = bool(
        discarded_sum is not None and discarded_sum > 0.0
    )
    observed_lossless_finite_bond = bool(
        explicit_truncation
        and truncation_ledger_complete
        and truncation_observations_valid
        and n_truncating_ops == 0
        and discarded_sum == 0.0
        and worst_discarded == 0.0
    )
    truncation_gate_failed = bool(
        truncation_gate["evaluated"] and not truncation_gate["passed"]
    )
    truncation_gate_complete = bool(
        truncation_gate["worst_cut_discarded_weight_gate"] is not None
        and truncation_gate["total_discarded_weight_gate"] is not None
    )
    finite_bond_candidate = bool(
        explicit_truncation
        and truncation_ledger_complete
        and truncation_gate_complete
        and truncation_gate["evaluated"]
        and truncation_gate["passed"]
    )
    finite_bond_policy_ok = bool(
        not explicit_truncation
        or observed_lossless_finite_bond
        or finite_bond_candidate
    )
    if truncation_gate_failed or not finite_bond_policy_ok:
        accepted_restricted = False
    if requires_scalable:
        accepted_restricted = False
    exact_dense_probability_evidence = bool(
        accepted_restricted and exact_dense_probability_candidate
    )
    sampled_execution = bool(
        accepted_restricted and sampled_execution_candidate
    )
    production_blockers = [
        "production_error_control_policy_not_established",
        "large_code_acceptance_not_established",
    ]
    if not residual_is_valid:
        production_blockers.append("invalid_total_probability_residual")
    elif not residual_ok:
        production_blockers.append("total_probability_residual_exceeds_gate")
    if not exact_dense_probability_evidence and not requires_scalable:
        production_blockers.append(f"dense_window_certification:{dense_status}")
    if requires_scalable:
        production_blockers.append("overcap_large_code_policy_not_established")
        production_blockers.append("overcap_independent_record_oracle_unavailable")
    if sampled_trajectories:
        production_blockers.append("sampled_probabilities_not_exact_dense_evidence")
        if not rng_seed_was_explicit:
            production_blockers.append("sampled_trajectory_rng_seed_not_explicit")
    if explicit_truncation:
        production_blockers.append("finite_bond_error_bound_not_established")
    if truncation_detected:
        production_blockers.append("nonzero_mps_truncation_discarded_weight")
    if truncation_gate_failed:
        production_blockers.append("finite_bond_candidate_gate_failed")
    if (
        explicit_truncation
        and not observed_lossless_finite_bond
        and not truncation_gate["evaluated"]
    ):
        production_blockers.append("finite_bond_candidate_gate_not_evaluated")
    elif (
        explicit_truncation
        and not observed_lossless_finite_bond
        and not truncation_gate_complete
    ):
        production_blockers.append("finite_bond_candidate_gate_incomplete")
    if not truncation_ledger_complete:
        production_blockers.append("incomplete_mps_truncation_aggregation_context")
    if requires_scalable:
        certification_status = "unavailable"
        diagnostic_only = True
        blocked_reason = "overcap_independent_record_oracle_unavailable"
    elif accepted_restricted:
        certification_status = "accepted"
        diagnostic_only = False
        blocked_reason = None
    elif not residual_is_valid:
        certification_status = "rejected"
        diagnostic_only = False
        blocked_reason = "invalid_total_probability_residual"
    elif not residual_ok:
        certification_status = "rejected"
        diagnostic_only = False
        blocked_reason = "total_probability_residual_exceeds_gate"
    elif dense_executed and not dense_passed:
        certification_status = "rejected"
        diagnostic_only = False
        blocked_reason = "dense_record_certification_failed"
    elif truncation_gate_failed or not finite_bond_policy_ok:
        certification_status = "rejected"
        diagnostic_only = False
        blocked_reason = "mps_truncation_policy_failed"
    else:
        certification_status = "unavailable"
        diagnostic_only = True
        blocked_reason = "independent_record_oracle_unavailable"
    return {
        "schema": _AXIS1_QT_MPS_RESTRICTED_ACCEPTANCE_POLICY_SCHEMA,
        "policy_role": "restricted_execution_acceptance_not_metric",
        "execution_status": "completed",
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "blocked_reason": blocked_reason,
        "accepted_for_restricted_execution": accepted_restricted,
        "accepted_for_exact_dense_probability_evidence": exact_dense_probability_evidence,
        "accepted_for_sampled_execution_evidence": sampled_execution,
        "accepted_for_production_scalable_backend": False,
        "total_probability_residual_gate": _TOTAL_PROBABILITY_RESIDUAL_GATE,
        "total_probability_residual_is_finite_nonnegative_real": residual_is_valid,
        "total_probability_residual_gate_epistemic_class": "c",
        "finite_step": {
            "order": step_order,
            "policy": str(finite_step_policy),
            "microstep_count": int(execution["finite_step_policy"]["microstep_count"]),
            "dense_window_certification_status": dense_status,
            "dense_window_certification_executed": dense_executed,
            "dense_window_certification_passed": dense_passed if dense_executed else None,
            "exact_summed_lindbladian_claim": False,
            "comparison_outcome_is_metric": certification_comparison_is_metric,
            "epistemic_class": "c",
        },
        "trajectory": {
            "mode": mode,
            "trajectory_count": sampling["trajectory_count"],
            "rng_seed": normalized_rng_seed,
            "rng_seed_required_for_acceptance": rng_seed_required_for_acceptance,
            "rng_seed_was_explicit": rng_seed_was_explicit,
            "accepted_as_exact_probability_evidence": exact_dense_probability_evidence,
            "accepted_as_empirical_record_evidence": sampled_execution,
            "single_trajectory_density_claim": False,
            "comparison_outcome_is_metric": sampling_comparison_is_metric,
            "epistemic_class": "a/c",
        },
        "mps_truncation": {
            "explicit_truncation_requested": explicit_truncation,
            "max_bond": None if max_bond is None else int(max_bond),
            "exact_bond_dimension_sufficient": exact_bond_dimension_sufficient,
            "exact_bond_policy": str(ledger["exact_bond_policy"]),
            "accepted_as_exact_bond_representation": (
                accepted_as_exact_bond_representation
            ),
            "discarded_weight_ledger_complete": truncation_ledger_complete,
            "discarded_weight_sum": discarded_sum,
            "worst_cut_discarded_weight": worst_discarded,
            "n_truncating_ops": n_truncating_ops,
            "truncation_detected": truncation_detected,
            "observed_lossless_finite_bond_execution": (
                observed_lossless_finite_bond
            ),
            "gate": truncation_gate,
            "candidate_gate_complete": truncation_gate_complete,
            "accepted_as_finite_bond_candidate": finite_bond_candidate,
            "accepted_as_restricted_risk_ledger": bool(
                truncation_ledger_complete and truncation_observations_valid
            ),
            "accepted_as_production_error_bound": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": str(ledger["epistemic_class"]),
        },
        "overcap": {
            "requires_scalable_backend": requires_scalable,
            "dense_fallback_forbidden": True,
            "dense_certification_used_for_overcap": False,
            "accepted_as_restricted_overcap_execution": False,
            "accepted_as_production_scalable_backend": False,
            "epistemic_class": "a/c",
        },
        "production_blockers": production_blockers,
        "scored_quantity_policy": "policy ledger only; no new scored quantity",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }


def _dense_certification_status(certification: dict[str, Any]) -> str:
    executed = _require_exact_bool_field(certification, "executed")
    passed = (
        _require_exact_bool_field(certification, "passed")
        if executed
        else _require_exact_bool_field(certification, "passed", default=False)
    )
    if executed:
        return "passed" if passed else "failed"
    reason = str(certification.get("reason", "not_executed"))
    if reason == "schedule_contains_scalable_required_rows":
        return "skipped_overcap_dense_fallback_forbidden"
    if reason == "sampled_trajectory_empirical_probabilities_not_exact_dense_certified":
        return "skipped_sampled_trajectory_not_exact_probability_evidence"
    if reason == "schedule_has_no_measurement_records":
        return "not_applicable_no_measurement_records"
    if reason == "dense_oracle_certification_not_requested":
        return "not_requested"
    return f"not_executed:{reason}"


def _normalize_bond_sweep_values(values: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    normalized = [normalize_mps_max_bond(value, allow_none=False) for value in values]
    bonds = tuple(sorted({int(value) for value in normalized}))
    if len(bonds) < 2:
        raise ValueError("bond_values must contain at least two distinct positive integers")
    if any(value <= 0 for value in bonds):
        raise ValueError("bond_values must be positive")
    return bonds


def _normalize_trajectory_sweep_seeds(values: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    seeds = normalize_mps_index_sequence(values, name="rng_seeds")
    if len(seeds) < 2:
        raise ValueError("rng_seeds must contain at least two explicit seeds")
    if len(set(seeds)) != len(seeds):
        raise ValueError("rng_seeds must be distinct")
    return seeds


def _validate_completed_qt_acceptance_policy(
    policy: dict[str, Any],
    *,
    execution: dict[str, Any],
    sampled: bool,
) -> tuple[bool, str, bool, str | None]:
    schema = _require_nonempty_text_field(policy, "schema", context="QT policy")
    if schema != _AXIS1_QT_MPS_RESTRICTED_ACCEPTANCE_POLICY_SCHEMA:
        raise ValueError("direct QT restricted acceptance policy schema is not registered")
    policy_role = _require_nonempty_text_field(
        policy,
        "policy_role",
        context="QT policy",
    )
    if policy_role != "restricted_execution_acceptance_not_metric":
        raise ValueError("direct QT restricted acceptance policy_role is not registered")
    execution_status = _require_nonempty_text_field(
        policy,
        "execution_status",
        context="QT policy",
    )
    if execution_status != "completed":
        raise ValueError("direct QT policy execution_status must be completed")
    accepted = _require_exact_bool_field(
        policy,
        "accepted_for_restricted_execution",
    )
    diagnostic_only = _require_exact_bool_field(policy, "diagnostic_only")
    certification_status = _require_nonempty_text_field(
        policy,
        "certification_status",
        context="QT policy",
    )
    blocked_reason = policy["blocked_reason"]
    if blocked_reason is not None and not isinstance(blocked_reason, str):
        raise TypeError("QT policy blocked_reason must be text or None")
    if accepted:
        state_valid = (
            certification_status == "accepted"
            and not diagnostic_only
            and blocked_reason is None
        )
    elif certification_status == "rejected":
        state_valid = not diagnostic_only and bool(blocked_reason)
    elif certification_status in {"not_evaluated", "unavailable"}:
        state_valid = diagnostic_only and bool(blocked_reason)
    else:
        state_valid = False
    if not state_valid:
        raise ValueError("direct QT restricted acceptance policy state is inconsistent")
    production_accepted = _require_exact_bool_field(
        policy,
        "accepted_for_production_scalable_backend",
    )
    if production_accepted:
        raise ValueError("restricted QT/MPS policy cannot claim production acceptance")
    expected_mode = (
        "sampled_product_channel_trajectories"
        if sampled
        else "exact_branch_enumeration"
    )
    sampling = execution.get("trajectory_sampling")
    if not isinstance(sampling, dict):
        raise TypeError("QT execution trajectory_sampling must be a mapping")
    actual_mode = _require_nonempty_text_field(
        sampling,
        "mode",
        context="QT execution trajectory_sampling",
    )
    if actual_mode != expected_mode:
        raise ValueError("QT execution trajectory mode does not match requested route")
    trajectory = policy.get("trajectory")
    if not isinstance(trajectory, dict):
        raise TypeError("QT policy trajectory must be a mapping")
    policy_mode = _require_nonempty_text_field(
        trajectory,
        "mode",
        context="QT policy trajectory",
    )
    if policy_mode != actual_mode:
        raise ValueError("QT policy trajectory mode must match actual execution")
    exact_accepted = _require_exact_bool_field(
        policy,
        "accepted_for_exact_dense_probability_evidence",
    )
    sampled_accepted = _require_exact_bool_field(
        policy,
        "accepted_for_sampled_execution_evidence",
    )
    if exact_accepted != (accepted and not sampled):
        raise ValueError("exact evidence acceptance must match exact execution state")
    if sampled_accepted != (accepted and sampled):
        raise ValueError("sampled evidence acceptance must match sampled execution state")
    return accepted, certification_status, diagnostic_only, blocked_reason


def _require_bound_qt_field(
    values: dict[str, Any],
    field: str,
    *,
    expected: Any,
    context: str,
) -> Any:
    if field not in values:
        raise ValueError(f"{context}.{field} is required")
    actual = values[field]
    if isinstance(expected, bool):
        actual = _require_exact_bool_field(values, field)
    elif expected is None:
        if actual is not None:
            raise ValueError(f"{context}.{field} does not match requested value")
        return None
    elif isinstance(expected, int):
        if isinstance(actual, bool):
            raise TypeError(f"{context}.{field} must be an integer, not bool")
        try:
            actual = int(operator.index(actual))
        except TypeError as exc:
            raise TypeError(f"{context}.{field} must be an integer") from exc
    elif isinstance(expected, float):
        if isinstance(actual, bool) or not isinstance(actual, Real):
            raise TypeError(f"{context}.{field} must be a real number")
        actual = float(actual)
        if not math.isfinite(actual):
            raise ValueError(f"{context}.{field} must be finite")
    elif isinstance(expected, str):
        if not isinstance(actual, str):
            raise TypeError(f"{context}.{field} must be text")
    elif isinstance(expected, list):
        if type(actual) is not list:
            raise TypeError(f"{context}.{field} must be a list")
        if _stable_payload_hash({"bound": actual}) != _stable_payload_hash(
            {"bound": expected}
        ):
            raise ValueError(
                f"{context}.{field} does not match requested value and types"
            )
        return actual
    elif isinstance(expected, dict):
        if type(actual) is not dict:
            raise TypeError(f"{context}.{field} must be a mapping")
        if _stable_payload_hash({"bound": actual}) != _stable_payload_hash(
            {"bound": expected}
        ):
            raise ValueError(
                f"{context}.{field} does not match requested value and types"
            )
        return actual
    if actual != expected:
        raise ValueError(f"{context}.{field} does not match requested value")
    return actual


def _validate_qt_payload_content_hash(
    payload: dict[str, Any],
    *,
    context: str,
) -> None:
    declared = _normalize_sha256_text(
        payload.get("content_hash"),
        name=f"{context}.content_hash",
    )
    computed = _stable_payload_hash(payload)
    if declared != computed:
        raise ValueError(f"{context}.content_hash does not authenticate payload")


def _validate_qt_applied_substeps(
    execution: dict[str, Any],
    *,
    trusted_program: dict[str, Any],
    sampled: bool,
    trajectory_count: int | None,
    max_branches: int,
    microstep_count: int,
    finite_step_order: str,
    context: str,
) -> None:
    applied = execution.get("applied_substeps")
    if type(applied) is not list:
        raise TypeError(f"{context} applied_substeps must be an exact list")
    substeps = trusted_program["program"]["substeps"]
    if len(applied) != len(substeps):
        raise ValueError(
            f"{context} applied_substeps count does not match carrier program"
        )
    finite_step_policy = _finite_step_policy_name(finite_step_order)
    exact_branch_upper = 1
    for index, (entry, substep) in enumerate(
        zip(applied, substeps, strict=True)
    ):
        item_context = f"{context} applied_substeps[{index}]"
        if type(entry) is not dict:
            raise TypeError(f"{item_context} must be an exact mapping")
        summary = axis1_carrier_substep_summary(substep)
        _require_qt_canonical_fields(entry, summary, context=item_context)
        kind = str(substep["substep_kind"])
        collapse_term_count = sum(
            1
            for term in substep.get("terms", ())
            if str(term.get("kind")) == "collapse"
            and abs(float(term.get("coefficient", 0.0))) > 0.0
        )
        if not sampled:
            exact_branch_upper = _static_exact_branch_upper_after_substep(
                exact_branch_upper,
                substep=substep,
                microstep_count=microstep_count,
                max_branches=max_branches,
            )
        expected_fields: dict[str, Any]
        dynamic_integer_fields: tuple[str, ...]
        if sampled and kind == "reset":
            expected_fields = {
                "finite_step_policy": "boundary_only_no_generator_evolution",
                "reset_boundary_policy": (
                    "sampled_pauli_reset_internal_outcome_no_record"
                ),
                "sampled_trajectory_count": trajectory_count,
            }
            dynamic_integer_fields = ("max_observed_bond_after_substep",)
        elif sampled:
            expected_fields = {
                "finite_step_policy": finite_step_policy,
                "finite_step_order": finite_step_order,
                "microstep_count": microstep_count,
                "sampled_trajectory_count": trajectory_count,
            }
            dynamic_integer_fields = (
                "sampled_collapse_term_count",
                "max_observed_bond_after_substep",
            )
        elif kind == "reset":
            expected_fields = {
                "finite_step_policy": "boundary_only_no_generator_evolution",
                "reset_boundary_policy": (
                    "nonselective_pauli_reset_internal_branches_no_record"
                ),
                "static_branch_count_upper_bound_after_substep": (
                    exact_branch_upper
                ),
            }
            dynamic_integer_fields = ("max_observed_bond_after_substep",)
        else:
            expected_fields = {
                "finite_step_policy": finite_step_policy,
                "finite_step_order": finite_step_order,
                "microstep_count": microstep_count,
                "static_branch_count_upper_bound_after_substep": (
                    exact_branch_upper
                ),
            }
            dynamic_integer_fields = ("max_observed_bond_after_substep",)
        expected_keys = (
            set(summary) | set(expected_fields) | set(dynamic_integer_fields)
        )
        if set(entry) != expected_keys:
            raise ValueError(
                f"{item_context} fields do not match the registered execution shape"
            )
        for field, expected in expected_fields.items():
            _require_bound_qt_field(
                entry,
                field,
                expected=expected,
                context=item_context,
            )
        for field in dynamic_integer_fields:
            value = normalize_mps_index(
                entry.get(field),
                name=f"{item_context}.{field}",
                minimum=(
                    1
                    if field == "max_observed_bond_after_substep"
                    else 0
                ),
            )
            if field == "sampled_collapse_term_count":
                collapse_upper = collapse_term_count * microstep_count
                if value > collapse_upper:
                    raise ValueError(
                        f"{item_context}.sampled_collapse_term_count exceeds "
                        "the trusted program collapse upper bound"
                    )


def _bounded_binary_branch_upper(
    current: int,
    *,
    exponent: int,
    cap: int,
) -> int:
    if current >= cap or exponent <= 0:
        return min(current, cap)
    if exponent >= cap.bit_length():
        return cap
    return min(cap, current * (1 << exponent))


def _static_exact_branch_upper_after_substep(
    current: int,
    *,
    substep: dict[str, Any],
    microstep_count: int,
    max_branches: int,
) -> int:
    """Return the cap-aware binary branch upper implied by trusted program data."""

    current = normalize_mps_index(
        current,
        name="current_static_branch_upper",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        microstep_count,
        name="microstep_count",
        minimum=1,
    )
    max_branches = normalize_mps_index(
        max_branches,
        name="max_branches",
        minimum=1,
    )
    kind = str(substep["substep_kind"])
    if kind == "reset":
        exponent = sum(
            len(operation.get("targets", ()))
            for operation in substep.get("operation_records", ())
        )
    else:
        collapse_term_count = sum(
            1
            for term in substep.get("terms", ())
            if str(term.get("kind")) == "collapse"
            and abs(float(term.get("coefficient", 0.0))) > 0.0
        )
        exponent = collapse_term_count * microstep_count
        if kind == "measurement":
            exponent += sum(
                len(operation.get("measurement_keys", ()))
                for operation in substep.get("operation_records", ())
            )
    return _bounded_binary_branch_upper(
        current,
        exponent=exponent,
        cap=max_branches,
    )


def _validate_qt_truncation_ledger(
    execution: dict[str, Any],
    *,
    trusted_program: dict[str, Any],
    expected_schedule: SubstepSchedule,
    sampled: bool,
    trajectory_count: int | None,
    max_bond: int | None,
    microstep_count: int,
    finite_step_order: str,
    context: str,
) -> dict[str, Any]:
    ledger = execution.get("mps_truncation_ledger")
    if type(ledger) is not dict:
        raise TypeError(f"{context} mps_truncation_ledger must be an exact mapping")
    max_observed_bond = normalize_mps_index(
        ledger.get("max_observed_bond"),
        name=f"{context}.mps_truncation_ledger.max_observed_bond",
        minimum=1,
    )
    applied = execution.get("applied_substeps")
    if type(applied) is not list:
        raise TypeError(f"{context} applied_substeps must be an exact list")
    substep_max_bonds = [
        normalize_mps_index(
            entry.get("max_observed_bond_after_substep"),
            name=(
                f"{context}.applied_substeps[{index}]."
                "max_observed_bond_after_substep"
            ),
            minimum=1,
        )
        for index, entry in enumerate(applied)
    ]
    derived_max_observed_bond = max([1, *substep_max_bonds])
    if max_observed_bond != derived_max_observed_bond:
        raise ValueError(
            f"{context} ledger max_observed_bond does not match applied substeps"
        )
    if max_bond is None:
        events: list[dict[str, Any]] = []
        expected_occurrences: tuple[dict[str, Any], ...] = ()
    else:
        events_value = ledger.get("truncation_events")
        if type(events_value) is not list:
            raise TypeError(
                f"{context} finite-cap truncation_events must be an exact list"
            )
        events = events_value
        expected_occurrences = _qt_expected_actual_split_occurrences(
            trusted_program,
            microstep_count=microstep_count,
            finite_step_order=finite_step_order,
        )
    aggregation = (
        aggregate_sampled_truncation_events(
            events,
            trajectory_count=normalize_mps_index(
                trajectory_count,
                name=f"{context}.trajectory_count",
                minimum=1,
            ),
            expected_gate_occurrences=expected_occurrences,
        )
        if sampled
        else aggregate_exact_branch_truncation_events(
            events,
            expected_gate_occurrences=expected_occurrences,
        )
    )
    canonical = build_mps_truncation_ledger(
        max_bond=max_bond,
        local_dims=(2,) * int(expected_schedule.num_qubits),
        max_observed_bond=max_observed_bond,
        truncation_events=events,
        aggregation=aggregation,
    )
    allowed_max_observed_bond = (
        max_bond
        if max_bond is not None
        else int(canonical["exact_bond_dimension_sufficient"])
    )
    if max_observed_bond > allowed_max_observed_bond:
        raise ValueError(
            f"{context} max_observed_bond exceeds the requested or exact bond bound"
        )
    _require_qt_exact_payload(
        ledger,
        canonical,
        context=f"{context} mps_truncation_ledger",
    )
    return canonical


def _validate_qt_restricted_child(
    run: dict[str, Any],
    *,
    context: str,
    expected_trajectory_mode: str,
    expected_schedule: SubstepSchedule,
    expected_source_kind: str,
    expected_source_hash: str,
    expected_schedule_representability: str,
    expected_carrier_program: dict[str, Any],
    expected_device: str,
    expected_max_bond: int | None,
    expected_max_branches: int,
    expected_record_budget: int,
    expected_record_materialization_preflight: dict[str, Any],
    expected_record_layout: Axis1ScheduleRecordLayout,
    expected_microstep_count: int,
    expected_finite_step_order: str,
    expected_trajectory_count: int | None,
    expected_rng_seed: int | None,
    expected_worst_cut_discarded_weight_gate: float | None,
    expected_total_discarded_weight_gate: float | None,
    expected_dense_oracle_certification: bool,
) -> bool:
    expected_top_level_fields = {
        "schema",
        "source_kind",
        "source_hash",
        "schedule_representability",
        "representability",
        "backend_contract",
        "gpu_required",
        "device",
        "carrier_program",
        "max_bond",
        "max_branches",
        "max_record_materialization_outcomes",
        "record_materialization_preflight",
        "microstep_count",
        "finite_step_order",
        "trajectory_count",
        "rng_seed",
        "worst_cut_discarded_weight_gate",
        "total_discarded_weight_gate",
        "dense_oracle_certification_requested",
        "claims_qt_mps_backend_execution",
        "claims_production_scalable_backend",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "scored_quantity_policy",
        "approximation_book",
        "epistemic_classes",
        "verdict",
        "passed",
        "execution_status",
        "certification_status",
        "diagnostic_only",
        "qt_mps_backend_executed",
        "blocked_reason",
        "blocked_substeps",
        "mps_execution",
        "dense_jointL_record_certification",
        "restricted_acceptance_policy",
        "scope",
        "content_hash",
    }
    if type(run) is not dict:
        raise TypeError(f"{context} must be an exact mapping")
    if set(run) != expected_top_level_fields:
        raise ValueError(f"{context} fields do not match registered shape")
    schema = _require_nonempty_text_field(run, "schema", context=context)
    if schema != AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA:
        raise ValueError(f"{context} execution schema is not registered")
    _require_bound_qt_field(
        run, "source_kind", expected=expected_source_kind, context=context
    )
    _require_bound_qt_field(
        run, "source_hash", expected=expected_source_hash, context=context
    )
    _require_bound_qt_field(
        run,
        "schedule_representability",
        expected=expected_schedule_representability,
        context=context,
    )
    _require_bound_qt_field(
        run,
        "representability",
        expected=AXIS1_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY,
        context=context,
    )
    _require_bound_qt_field(
        run,
        "backend_contract",
        expected=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        context=context,
    )
    _require_bound_qt_field(run, "gpu_required", expected=True, context=context)
    _require_bound_qt_field(
        run, "device", expected=expected_device, context=context
    )
    _require_bound_qt_field(
        run, "max_bond", expected=expected_max_bond, context=context
    )
    _require_bound_qt_field(
        run, "max_branches", expected=expected_max_branches, context=context
    )
    _require_bound_qt_field(
        run,
        "max_record_materialization_outcomes",
        expected=expected_record_budget,
        context=context,
    )
    _require_bound_qt_field(
        run,
        "microstep_count",
        expected=expected_microstep_count,
        context=context,
    )
    _require_bound_qt_field(
        run,
        "finite_step_order",
        expected=expected_finite_step_order,
        context=context,
    )
    _require_bound_qt_field(
        run,
        "trajectory_count",
        expected=expected_trajectory_count,
        context=context,
    )
    _require_bound_qt_field(
        run, "rng_seed", expected=expected_rng_seed, context=context
    )
    _require_bound_qt_field(
        run,
        "worst_cut_discarded_weight_gate",
        expected=expected_worst_cut_discarded_weight_gate,
        context=context,
    )
    _require_bound_qt_field(
        run,
        "total_discarded_weight_gate",
        expected=expected_total_discarded_weight_gate,
        context=context,
    )
    _require_bound_qt_field(
        run,
        "dense_oracle_certification_requested",
        expected=expected_dense_oracle_certification,
        context=context,
    )
    carrier_program = run.get("carrier_program")
    _require_qt_exact_payload(
        carrier_program,
        expected_carrier_program,
        context=f"{context} carrier_program",
    )
    trusted_program = axis1_carrier_program_manifest(
        expected_schedule,
        backend_contract=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    _require_qt_exact_payload(
        expected_carrier_program,
        _program_summary(trusted_program),
        context=f"{context} trusted carrier program",
    )
    if axis1_record_layout_from_schedule(expected_schedule) != expected_record_layout:
        raise ValueError(
            f"{context} expected Record layout is not bound to trusted schedule"
        )
    passed = _require_exact_bool_field(run, "passed")
    verdict = _require_nonempty_text_field(run, "verdict", context=context)
    expected_verdict = "pass" if passed else "fail"
    if verdict != expected_verdict:
        raise ValueError(f"{context} verdict must agree with passed")
    execution_status = _require_nonempty_text_field(
        run, "execution_status", context=context
    )
    certification_status = _require_nonempty_text_field(
        run, "certification_status", context=context
    )
    diagnostic_only = _require_exact_bool_field(run, "diagnostic_only")
    backend_executed = _require_exact_bool_field(run, "qt_mps_backend_executed")
    backend_claimed = _require_exact_bool_field(
        run, "claims_qt_mps_backend_execution"
    )
    if backend_claimed != backend_executed:
        raise ValueError(f"{context} backend claim must agree with execution")
    for field in (
        "claims_production_scalable_backend",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
    ):
        if _require_exact_bool_field(run, field):
            raise ValueError(f"{context} cannot assert {field}")
    if backend_executed != (execution_status == "completed"):
        raise ValueError(
            f"{context} backend execution must agree with execution_status"
        )
    _require_bound_qt_field(
        run,
        "scored_quantity_policy",
        expected=_QT_MPS_SCORED_QUANTITY_POLICY,
        context=context,
    )
    _require_qt_exact_payload(
        run.get("epistemic_classes"),
        _qt_restricted_epistemic_classes(),
        context=f"{context} epistemic_classes",
    )
    completed_execution = (
        run.get("mps_execution")
        if execution_status == "completed"
        else None
    )
    if completed_execution is not None and type(completed_execution) is not dict:
        raise TypeError(f"{context} mps_execution must be an exact mapping")
    expected_approximation_book = _qt_restricted_approximation_book(
        max_bond=expected_max_bond,
        microstep_count=expected_microstep_count,
        finite_step_order=expected_finite_step_order,
        trajectory_count=expected_trajectory_count,
        rng_seed=expected_rng_seed,
        worst_cut_discarded_weight_gate=(
            expected_worst_cut_discarded_weight_gate
        ),
        total_discarded_weight_gate=expected_total_discarded_weight_gate,
        execution=completed_execution,
    )
    _require_qt_exact_payload(
        run.get("approximation_book"),
        expected_approximation_book,
        context=f"{context} approximation_book",
    )
    expected_scope = (
        _QT_MPS_COMPLETED_SCOPE
        if execution_status == "completed"
        else _QT_MPS_BLOCKED_SCOPE
    )
    _require_bound_qt_field(
        run,
        "scope",
        expected=expected_scope,
        context=context,
    )
    expected_blocked_substeps = (
        []
        if execution_status == "completed"
        else _unsupported_substeps(trusted_program)
    )
    _require_qt_exact_json_value(
        run.get("blocked_substeps"),
        expected_blocked_substeps,
        context=f"{context} blocked_substeps",
    )

    acceptance = run.get("restricted_acceptance_policy")
    if not isinstance(acceptance, dict):
        raise TypeError(f"{context} restricted_acceptance_policy must be a mapping")
    policy_schema = _require_nonempty_text_field(
        acceptance,
        "schema",
        context=f"{context} policy",
    )
    if policy_schema != _AXIS1_QT_MPS_RESTRICTED_ACCEPTANCE_POLICY_SCHEMA:
        raise ValueError(f"{context} policy schema is not registered")
    policy_role = _require_nonempty_text_field(
        acceptance,
        "policy_role",
        context=f"{context} policy",
    )
    if policy_role != "restricted_execution_acceptance_not_metric":
        raise ValueError(f"{context} policy_role is not registered")
    accepted = _require_exact_bool_field(
        acceptance, "accepted_for_restricted_execution"
    )
    production_accepted = _require_exact_bool_field(
        acceptance,
        "accepted_for_production_scalable_backend",
    )
    if production_accepted:
        raise ValueError(f"{context} policy cannot claim production acceptance")
    if accepted != passed:
        raise ValueError(f"{context} accepted state must agree with passed")
    if expected_trajectory_mode not in {
        "exact_branch_enumeration",
        "sampled_product_channel_trajectories",
    }:
        raise ValueError(f"{context} expected trajectory mode is not registered")
    trajectory = acceptance.get("trajectory")
    if not isinstance(trajectory, dict):
        raise TypeError(f"{context} policy trajectory must be a mapping")
    policy_trajectory_mode = _require_nonempty_text_field(
        trajectory,
        "mode",
        context=f"{context} policy trajectory",
    )
    if policy_trajectory_mode != expected_trajectory_mode:
        raise ValueError(f"{context} policy trajectory mode does not match sweep")
    exact_accepted = _require_exact_bool_field(
        acceptance,
        "accepted_for_exact_dense_probability_evidence",
    )
    sampled_accepted = _require_exact_bool_field(
        acceptance,
        "accepted_for_sampled_execution_evidence",
    )
    expected_exact_acceptance = bool(
        passed and expected_trajectory_mode == "exact_branch_enumeration"
    )
    expected_sampled_acceptance = bool(
        passed
        and expected_trajectory_mode == "sampled_product_channel_trajectories"
    )
    if exact_accepted != expected_exact_acceptance:
        raise ValueError(f"{context} exact acceptance tier must agree with child")
    if sampled_accepted != expected_sampled_acceptance:
        raise ValueError(f"{context} sampled acceptance tier must agree with child")
    policy_truncation_preview = acceptance.get("mps_truncation")
    if not isinstance(policy_truncation_preview, dict):
        raise TypeError(f"{context} policy mps_truncation must be a mapping")
    _require_exact_bool_field(
        policy_truncation_preview,
        "accepted_as_exact_bond_representation",
    )
    if execution_status == "completed":
        execution = run.get("mps_execution")
        if not isinstance(execution, dict):
            raise TypeError(f"{context} mps_execution must be a mapping")
        sampling = execution.get("trajectory_sampling")
        if not isinstance(sampling, dict):
            raise TypeError(f"{context} trajectory_sampling must be a mapping")
        execution_trajectory_mode = _require_nonempty_text_field(
            sampling,
            "mode",
            context=f"{context} trajectory_sampling",
        )
        if execution_trajectory_mode != expected_trajectory_mode:
            raise ValueError(
                f"{context} execution trajectory mode does not match sweep"
            )
        sampled = (
            expected_trajectory_mode
            == "sampled_product_channel_trajectories"
        )
        expected_execution_keys = {
            "initial_state",
            "site_order",
            "physical_dimension",
            "mps_library",
            "array_backend",
            "hamiltonian_evolution_policy",
            "collapse_evolution_policy",
            "finite_step_policy",
            "trajectory_sampling",
            "exact_joint_generator_claim",
            "exact_summed_lindbladian_claim",
            "measurement_basis",
            "measurement_keys",
            "measurement_targets",
            "measurement_records",
            "record_probabilities",
            "record_count",
            "total_probability",
            "total_probability_residual",
            "mps_truncation_ledger",
            "applied_substeps",
            "detector_records_emitted",
            "detector_names",
            "detector_records",
            "logical_observables_emitted",
            "logical_observable_names",
            "logical_observable_records",
            "claims_b8_artifact",
            "claims_decoder_integration",
            "claims_dense_channel_evidence",
            "claims_axis2_source_timeline",
            "claims_production_scalable_backend",
        }
        if sampled:
            expected_execution_keys.add("record_counts")
        if set(execution) != expected_execution_keys:
            raise ValueError(
                f"{context} mps_execution fields do not match registered shape"
            )
        execution_constants = {
            "initial_state": "computational_zero_mps",
            "site_order": list(range(int(expected_schedule.num_qubits))),
            "physical_dimension": 2,
            "mps_library": "quimb.tensor.MatrixProductState",
            "array_backend": "torch_cuda_complex128",
            "hamiltonian_evolution_policy": (
                "operator_family_order_product_formula"
            ),
            "collapse_evolution_policy": "local_product_channel_branching",
            "exact_joint_generator_claim": False,
            "exact_summed_lindbladian_claim": False,
            "measurement_basis": "Z",
            "claims_b8_artifact": False,
            "claims_decoder_integration": False,
            "claims_dense_channel_evidence": False,
            "claims_axis2_source_timeline": False,
            "claims_production_scalable_backend": False,
        }
        for field, expected in execution_constants.items():
            _require_bound_qt_field(
                execution,
                field,
                expected=expected,
                context=f"{context} mps_execution",
            )
        expected_sampling = {
            "mode": expected_trajectory_mode,
            "trajectory_count": expected_trajectory_count,
            "rng_seed": expected_rng_seed,
            "rng_seed_required_for_acceptance": sampled,
            "rng_seed_was_explicit": bool(
                sampled and expected_rng_seed is not None
            ),
            "rng_backend": (
                "torch.Generator(cuda)" if sampled else "not_used"
            ),
            "measurement_sampling_policy": (
                "sequential_conditional_single_site_z_v1"
                if sampled
                else "exact_joint_binary_branch_enumeration"
            ),
            "record_support_policy": (
                _OBSERVED_EMPIRICAL_RECORD_SUPPORT_POLICY
                if sampled
                else _FULL_BINARY_RECORD_SUPPORT_POLICY
            ),
            "probability_semantics": (
                "empirical_record_frequencies"
                if sampled
                else "exact_enumerated_branch_probabilities"
            ),
            "comparison_outcome_is_metric": False,
        }
        if sampled:
            expected_sampling.update(
                rng_seed_default_policy="default_zero_when_not_provided",
                zero_frequency_records_emitted=False,
            )
        _require_qt_exact_payload(
            sampling,
            expected_sampling,
            context=f"{context} trajectory_sampling",
        )
        _validate_qt_record_execution_payload(
            execution,
            sampled=sampled,
            trajectory_count=expected_trajectory_count,
        )
        expected_measurement_keys = list(expected_record_layout.measurement_keys)
        if execution.get("measurement_keys") != expected_measurement_keys:
            raise ValueError(
                f"{context} measurement_keys do not match frozen Record layout"
            )
        expected_measurement_targets = list(
            expected_record_layout.measurement_targets
        )
        if execution.get("measurement_targets") != expected_measurement_targets:
            raise ValueError(
                f"{context} measurement_targets do not match frozen Record layout"
            )
        _validate_axis1_projected_record_payload(
            expected_record_layout,
            execution,
            context=context,
        )
        child_preflight = run.get("record_materialization_preflight")
        _validate_qt_record_materialization_preflight_payload(
            child_preflight,
            execution=execution,
            sampled=sampled,
            trajectory_count=expected_trajectory_count,
        )
        _require_qt_exact_payload(
            child_preflight,
            expected_record_materialization_preflight,
            context=f"{context} record_materialization_preflight",
        )
        finite_step = execution.get("finite_step_policy")
        _require_qt_exact_payload(
            finite_step,
            {
                "name": _finite_step_policy_name(
                    expected_finite_step_order
                ),
                "order": expected_finite_step_order,
                "microstep_count": expected_microstep_count,
                "microstep_dt_policy": (
                    "equal_substeps_dt_ns_div_microstep_count"
                ),
                "exact_summed_lindbladian_claim": False,
                "comparison_outcome_is_metric": False,
            },
            context=f"{context} finite_step_policy",
        )
        _validate_qt_applied_substeps(
            execution,
            trusted_program=trusted_program,
            sampled=sampled,
            trajectory_count=expected_trajectory_count,
            max_branches=expected_max_branches,
            microstep_count=expected_microstep_count,
            finite_step_order=expected_finite_step_order,
            context=context,
        )
        _validate_qt_truncation_ledger(
            execution,
            trusted_program=trusted_program,
            expected_schedule=expected_schedule,
            sampled=sampled,
            trajectory_count=expected_trajectory_count,
            max_bond=expected_max_bond,
            microstep_count=expected_microstep_count,
            finite_step_order=expected_finite_step_order,
            context=context,
        )
        certification = run.get("dense_jointL_record_certification")
        if not isinstance(certification, dict):
            raise TypeError(
                f"{context} dense_jointL_record_certification must be a mapping"
            )
        _require_exact_bool_field(certification, "executed")
        expected_certification = (
            _dense_record_certification(
                expected_schedule,
                program=trusted_program,
                execution=execution,
                device=expected_device,
            )
            if expected_dense_oracle_certification
            else {
                "executed": False,
                "reason": "dense_oracle_certification_not_requested",
                "comparison_outcome_is_metric": False,
            }
        )
        _require_qt_exact_payload(
            certification,
            expected_certification,
            context=f"{context} dense certification",
        )
        expected_acceptance = _restricted_acceptance_policy(
            program=trusted_program,
            execution=execution,
            record_materialization_preflight=child_preflight,
            certification=certification,
            finite_step_order=expected_finite_step_order,
            finite_step_policy=_finite_step_policy_name(
                expected_finite_step_order
            ),
            max_bond=expected_max_bond,
            worst_cut_discarded_weight_gate=(
                expected_worst_cut_discarded_weight_gate
            ),
            total_discarded_weight_gate=expected_total_discarded_weight_gate,
        )
        _require_qt_exact_payload(
            acceptance,
            expected_acceptance,
            context=f"{context} acceptance policy",
        )
    else:
        if execution_status != "blocked":
            raise ValueError(f"{context} non-completed child must be blocked")
        if not expected_blocked_substeps:
            raise ValueError(
                f"{context} blocked child has no trusted unsupported substep"
            )
        expected_blocked_reason = str(
            expected_blocked_substeps[0]["reason"]
        )
        _require_bound_qt_field(
            run,
            "blocked_reason",
            expected=expected_blocked_reason,
            context=context,
        )
        if run.get("mps_execution") is not None:
            raise ValueError(f"{context} blocked mps_execution must be None")
        _require_qt_exact_payload(
            run.get("dense_jointL_record_certification"),
            {
                "executed": False,
                "reason": (
                    "qt_mps_backend_blocked_before_dense_record_certification"
                ),
                "blocked_reason": expected_blocked_reason,
                "comparison_outcome_is_metric": False,
            },
            context=f"{context} blocked dense certification",
        )
        _require_qt_exact_payload(
            acceptance,
            _blocked_restricted_acceptance_policy(
                blocked_reason=expected_blocked_reason,
                finite_step_order=expected_finite_step_order,
                finite_step_policy=_finite_step_policy_name(
                    expected_finite_step_order
                ),
                microstep_count=expected_microstep_count,
                trajectory_count=expected_trajectory_count,
                rng_seed=expected_rng_seed,
                max_bond=expected_max_bond,
                worst_cut_discarded_weight_gate=(
                    expected_worst_cut_discarded_weight_gate
                ),
                total_discarded_weight_gate=(
                    expected_total_discarded_weight_gate
                ),
            ),
            context=f"{context} blocked acceptance policy",
        )
        _require_qt_exact_payload(
            run.get("record_materialization_preflight"),
            expected_record_materialization_preflight,
            context=f"{context} blocked record_materialization_preflight",
        )

    policy_finite_step = acceptance.get("finite_step")
    if not isinstance(policy_finite_step, dict):
        raise TypeError(f"{context} policy finite_step must be a mapping")
    _require_bound_qt_field(
        policy_finite_step,
        "order",
        expected=expected_finite_step_order,
        context=f"{context} policy finite_step",
    )
    _require_bound_qt_field(
        policy_finite_step,
        "microstep_count",
        expected=expected_microstep_count,
        context=f"{context} policy finite_step",
    )
    _require_bound_qt_field(
        trajectory,
        "trajectory_count",
        expected=expected_trajectory_count,
        context=f"{context} policy trajectory",
    )
    _require_bound_qt_field(
        trajectory,
        "rng_seed",
        expected=expected_rng_seed,
        context=f"{context} policy trajectory",
    )
    policy_truncation = acceptance.get("mps_truncation")
    if not isinstance(policy_truncation, dict):
        raise TypeError(f"{context} policy mps_truncation must be a mapping")
    _require_bound_qt_field(
        policy_truncation,
        "max_bond",
        expected=expected_max_bond,
        context=f"{context} policy mps_truncation",
    )
    policy_truncation_gate = policy_truncation.get("gate")
    if not isinstance(policy_truncation_gate, dict):
        raise TypeError(f"{context} policy truncation gate must be a mapping")
    _require_bound_qt_field(
        policy_truncation_gate,
        "worst_cut_discarded_weight_gate",
        expected=expected_worst_cut_discarded_weight_gate,
        context=f"{context} policy truncation gate",
    )
    _require_bound_qt_field(
        policy_truncation_gate,
        "total_discarded_weight_gate",
        expected=expected_total_discarded_weight_gate,
        context=f"{context} policy truncation gate",
    )

    policy_execution_status = _require_nonempty_text_field(
        acceptance, "execution_status", context=f"{context} policy"
    )
    policy_certification_status = _require_nonempty_text_field(
        acceptance, "certification_status", context=f"{context} policy"
    )
    policy_diagnostic_only = _require_exact_bool_field(
        acceptance, "diagnostic_only"
    )
    blocked_reason = run["blocked_reason"]
    if blocked_reason is not None and not isinstance(blocked_reason, str):
        raise TypeError(f"{context} blocked_reason must be text or None")
    policy_blocked_reason = acceptance["blocked_reason"]
    if policy_blocked_reason is not None and not isinstance(
        policy_blocked_reason,
        str,
    ):
        raise TypeError(f"{context} policy blocked_reason must be text or None")
    if (
        policy_execution_status != execution_status
        or policy_certification_status != certification_status
        or policy_diagnostic_only != diagnostic_only
    ):
        raise ValueError(f"{context} policy state must match child state")
    if policy_blocked_reason != blocked_reason:
        raise ValueError(f"{context} policy blocked_reason must match child")

    if passed:
        state_valid = (
            execution_status == "completed"
            and certification_status == "accepted"
            and not diagnostic_only
        )
    elif execution_status in {"blocked", "failed"}:
        state_valid = (
            certification_status in {"not_evaluated", "unavailable"}
            and not diagnostic_only
        )
    elif execution_status == "completed" and certification_status == "rejected":
        state_valid = not diagnostic_only
    elif execution_status == "completed" and certification_status in {
        "not_evaluated",
        "unavailable",
    }:
        state_valid = diagnostic_only
    else:
        state_valid = False
    if not state_valid:
        raise ValueError(f"{context} child state machine is inconsistent")
    if passed and blocked_reason is not None:
        raise ValueError(f"{context} passing child cannot carry blocked_reason")
    if not passed and not blocked_reason:
        raise ValueError(f"{context} failing child requires blocked_reason")
    _validate_qt_payload_content_hash(run, context=context)
    return passed


def _qt_run_summaries_backend_execution_claim(
    child: dict[str, Any],
    *,
    expected_count: int,
    context: str,
) -> bool:
    summaries = child.get("run_summaries")
    if not isinstance(summaries, list):
        raise TypeError(f"{context} run_summaries must be a list")
    if len(summaries) != expected_count:
        raise ValueError(f"{context} run_summaries count does not match request")
    backend_states: list[bool] = []
    for index, summary in enumerate(summaries):
        if not isinstance(summary, dict):
            raise TypeError(f"{context} run_summaries[{index}] must be a mapping")
        backend_states.append(
            _require_exact_bool_field(summary, "qt_mps_backend_executed")
        )
    return all(backend_states)


def _require_qt_canonical_fields(
    declared: dict[str, Any],
    canonical: dict[str, Any],
    *,
    context: str,
) -> None:
    missing = [field for field in canonical if field not in declared]
    if missing:
        raise ValueError(
            f"{context} is missing canonical fields: {', '.join(missing)}"
        )
    declared_fields = {field: declared[field] for field in canonical}
    try:
        declared_hash = _stable_payload_hash({"derived": declared_fields})
        canonical_hash = _stable_payload_hash({"derived": canonical})
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} contains non-canonical values") from exc
    if declared_hash != canonical_hash:
        mismatched = [
            field
            for field in canonical
            if declared_fields[field] != canonical[field]
        ]
        raise ValueError(
            f"{context} does not match raw sweep evidence; "
            f"mismatched canonical fields: {', '.join(mismatched)}"
        )


def _require_qt_exact_payload(
    declared: Any,
    canonical: dict[str, Any],
    *,
    context: str,
) -> None:
    if type(declared) is not dict:
        raise TypeError(f"{context} must be an exact mapping")
    if set(declared) != set(canonical):
        raise ValueError(f"{context} fields do not match the canonical payload")
    _require_qt_canonical_fields(declared, canonical, context=context)


def _require_qt_exact_json_value(
    declared: Any,
    canonical: Any,
    *,
    context: str,
) -> None:
    if type(declared) is not type(canonical):
        raise TypeError(f"{context} has the wrong exact container type")
    try:
        declared_hash = _stable_payload_hash({"value": declared})
        canonical_hash = _stable_payload_hash({"value": canonical})
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} contains non-canonical values") from exc
    if declared_hash != canonical_hash:
        raise ValueError(f"{context} does not match the canonical value")


def _validate_qt_bond_sweep_acceptance(
    child: dict[str, Any],
    *,
    accepted: bool,
    expected_bonds: tuple[int, ...],
    expected_schedule: SubstepSchedule,
    context: str,
) -> None:
    policy = child.get("convergence_policy")
    if not isinstance(policy, dict):
        raise TypeError(f"{context} convergence_policy must be a mapping")
    runs = child.get("runs")
    if not isinstance(runs, list):
        raise TypeError(f"{context} runs must be a list")
    summaries = child.get("run_summaries")
    if not isinstance(summaries, list):
        raise TypeError(f"{context} run_summaries must be a list")
    if len(runs) != len(expected_bonds) or len(summaries) != len(expected_bonds):
        raise ValueError(f"{context} run evidence count does not match request")
    expected_program = _program_summary(
        axis1_carrier_program_manifest(
            expected_schedule,
            backend_contract=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        )
    )
    expected_layout = axis1_record_layout_from_schedule(expected_schedule)
    record_budget = _normalize_max_record_materialization_outcomes(
        child.get("max_record_materialization_outcomes")
    )
    expected_preflight = _record_materialization_preflight_for_schedule(
        expected_schedule,
        max_record_materialization_outcomes=record_budget,
    )
    device = normalize_mps_device(child.get("device"))
    max_branches = normalize_mps_index(
        child.get("max_branches"),
        name=f"{context}.max_branches",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        child.get("microstep_count"),
        name=f"{context}.microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(
        child.get("finite_step_order")
    )
    convergence_gate = normalize_optional_mps_nonnegative_real(
        child.get("convergence_record_probability_gate"),
        name=f"{context}.convergence_record_probability_gate",
    )
    worst_gate = normalize_optional_mps_nonnegative_real(
        child.get("worst_cut_discarded_weight_gate"),
        name=f"{context}.worst_cut_discarded_weight_gate",
    )
    total_gate = normalize_optional_mps_nonnegative_real(
        child.get("total_discarded_weight_gate"),
        name=f"{context}.total_discarded_weight_gate",
    )
    dense_requested = normalize_mps_bool(
        child.get("dense_oracle_certification_requested"),
        name=f"{context}.dense_oracle_certification_requested",
    )
    run_acceptance: list[bool] = []
    for index, (run, summary, bond) in enumerate(
        zip(runs, summaries, expected_bonds, strict=True)
    ):
        if not isinstance(run, dict):
            raise TypeError(f"{context} runs[{index}] must be a mapping")
        run_passed = _validate_qt_restricted_child(
            run,
            context=f"{context} runs[{index}]",
            expected_trajectory_mode="exact_branch_enumeration",
            expected_schedule=expected_schedule,
            expected_source_kind=expected_schedule.source_kind,
            expected_source_hash=expected_schedule.source_hash,
            expected_schedule_representability=expected_schedule.representability,
            expected_carrier_program=expected_program,
            expected_device=device,
            expected_max_bond=bond,
            expected_max_branches=max_branches,
            expected_record_budget=record_budget,
            expected_record_materialization_preflight=expected_preflight,
            expected_record_layout=expected_layout,
            expected_microstep_count=microstep_count,
            expected_finite_step_order=finite_step_order,
            expected_trajectory_count=None,
            expected_rng_seed=None,
            expected_worst_cut_discarded_weight_gate=worst_gate,
            expected_total_discarded_weight_gate=total_gate,
            expected_dense_oracle_certification=dense_requested,
        )
        _require_qt_exact_payload(
            summary,
            _bond_sweep_run_summary(run),
            context=f"{context} run_summaries[{index}]",
        )
        summary_passed = _require_exact_bool_field(summary, "passed")
        run_accepted = _require_exact_bool_field(
            summary,
            "accepted_for_restricted_execution",
        )
        run_acceptance.append(run_passed and summary_passed and run_accepted)
    canonical_comparison = _bond_sweep_comparison(
        runs,
        convergence_record_probability_gate=convergence_gate,
    )
    _require_qt_canonical_fields(
        policy,
        canonical_comparison,
        context=f"{context} convergence comparison",
    )
    gate = canonical_comparison["convergence_gate"]
    evaluated = _require_exact_bool_field(gate, "evaluated")
    if evaluated:
        gate_passed = _require_exact_bool_field(gate, "passed")
    else:
        if gate.get("passed") is not None:
            raise TypeError(
                f"{context} unevaluated convergence gate passed must be None"
            )
        gate_passed = False
    reference_exact = _require_exact_bool_field(
        summaries[-1],
        "accepted_as_exact_bond_representation",
    )
    reference_calibration = policy.get("reference_dense_calibration")
    if not isinstance(reference_calibration, dict):
        raise TypeError(
            f"{context} reference_dense_calibration must be a mapping"
        )
    canonical_reference_calibration = _bond_sweep_reference_calibration(
        runs[-1]
    )
    _require_qt_exact_payload(
        reference_calibration,
        canonical_reference_calibration,
        context=f"{context} reference dense calibration",
    )
    reference_calibrated = _require_exact_bool_field(
        canonical_reference_calibration,
        "accepted_as_dense_calibrated_reference",
    )
    for field, expected in (
        ("accepted_as_production_error_bound", False),
        ("accepted_for_production_scalable_backend", False),
        ("comparison_outcome_is_metric", False),
        ("epistemic_class", "c"),
    ):
        _require_bound_qt_field(
            policy,
            field,
            expected=expected,
            context=f"{context} convergence_policy",
        )
    derived_acceptance = bool(
        all(run_acceptance)
        and evaluated
        and gate_passed
        and reference_calibrated
        and reference_exact
    )
    if accepted != derived_acceptance:
        raise ValueError(
            f"{context} run_summaries and gates do not reconstruct acceptance"
        )
    _require_qt_exact_payload(
        policy,
        {
            **canonical_comparison,
            "reference_dense_calibration": canonical_reference_calibration,
            "accepted_as_restricted_convergence_evidence": (
                derived_acceptance
            ),
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        context=f"{context} convergence_policy",
    )


def _validate_qt_seed_sweep_acceptance(
    child: dict[str, Any],
    *,
    accepted: bool,
    expected_seeds: tuple[int, ...],
    expected_trajectory_count: int,
    expected_schedule: SubstepSchedule,
    expected_device: str,
    context: str,
) -> None:
    policy = child.get("seed_sweep_policy")
    if not isinstance(policy, dict):
        raise TypeError(f"{context} seed_sweep_policy must be a mapping")
    runs = child.get("runs")
    if not isinstance(runs, list):
        raise TypeError(f"{context} runs must be a list")
    summaries = child.get("run_summaries")
    if not isinstance(summaries, list):
        raise TypeError(f"{context} run_summaries must be a list")
    if len(runs) != len(expected_seeds) or len(summaries) != len(expected_seeds):
        raise ValueError(f"{context} run evidence count does not match request")
    expected_program = _program_summary(
        axis1_carrier_program_manifest(
            expected_schedule,
            backend_contract=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        )
    )
    expected_layout = axis1_record_layout_from_schedule(expected_schedule)
    record_budget = _normalize_max_record_materialization_outcomes(
        child.get("max_record_materialization_outcomes")
    )
    expected_preflight = _record_materialization_preflight_for_schedule(
        expected_schedule,
        max_record_materialization_outcomes=record_budget,
        trajectory_count=expected_trajectory_count,
    )
    device = normalize_mps_device(expected_device)
    max_bond = normalize_mps_max_bond(child.get("max_bond"))
    max_branches = normalize_mps_index(
        child.get("max_branches"),
        name=f"{context}.max_branches",
        minimum=1,
    )
    microstep_count = normalize_mps_index(
        child.get("microstep_count"),
        name=f"{context}.microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(
        child.get("finite_step_order")
    )
    seed_gate = normalize_optional_mps_nonnegative_real(
        child.get("seed_record_frequency_spread_gate"),
        name=f"{context}.seed_record_frequency_spread_gate",
    )
    dense_gate = normalize_optional_mps_nonnegative_real(
        child.get("dense_record_frequency_gate"),
        name=f"{context}.dense_record_frequency_gate",
    )
    worst_gate = normalize_optional_mps_nonnegative_real(
        child.get("worst_cut_discarded_weight_gate"),
        name=f"{context}.worst_cut_discarded_weight_gate",
    )
    total_gate = normalize_optional_mps_nonnegative_real(
        child.get("total_discarded_weight_gate"),
        name=f"{context}.total_discarded_weight_gate",
    )
    dense_requested = normalize_mps_bool(
        child.get("dense_oracle_certification_requested"),
        name=f"{context}.dense_oracle_certification_requested",
    )
    run_acceptance: list[bool] = []
    for index, (run, summary, seed) in enumerate(
        zip(runs, summaries, expected_seeds, strict=True)
    ):
        if not isinstance(run, dict):
            raise TypeError(f"{context} runs[{index}] must be a mapping")
        run_passed = _validate_qt_restricted_child(
            run,
            context=f"{context} runs[{index}]",
            expected_trajectory_mode="sampled_product_channel_trajectories",
            expected_schedule=expected_schedule,
            expected_source_kind=expected_schedule.source_kind,
            expected_source_hash=expected_schedule.source_hash,
            expected_schedule_representability=expected_schedule.representability,
            expected_carrier_program=expected_program,
            expected_device=device,
            expected_max_bond=max_bond,
            expected_max_branches=max_branches,
            expected_record_budget=record_budget,
            expected_record_materialization_preflight=expected_preflight,
            expected_record_layout=expected_layout,
            expected_microstep_count=microstep_count,
            expected_finite_step_order=finite_step_order,
            expected_trajectory_count=expected_trajectory_count,
            expected_rng_seed=seed,
            expected_worst_cut_discarded_weight_gate=worst_gate,
            expected_total_discarded_weight_gate=total_gate,
            expected_dense_oracle_certification=dense_requested,
        )
        _require_qt_exact_payload(
            summary,
            _trajectory_seed_sweep_run_summary(run),
            context=f"{context} run_summaries[{index}]",
        )
        summary_passed = _require_exact_bool_field(summary, "passed")
        run_accepted = _require_exact_bool_field(
            summary,
            "accepted_for_sampled_execution_evidence",
        )
        run_acceptance.append(run_passed and summary_passed and run_accepted)
    canonical_comparison = _trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=seed_gate,
    )
    _require_qt_canonical_fields(
        policy,
        canonical_comparison,
        context=f"{context} seed comparison",
    )
    gate = canonical_comparison["seed_spread_gate"]
    evaluated = _require_exact_bool_field(gate, "evaluated")
    if evaluated:
        gate_passed = _require_exact_bool_field(gate, "passed")
    else:
        if gate.get("passed") is not None:
            raise TypeError(
                f"{context} unevaluated seed spread gate passed must be None"
            )
        gate_passed = False
    dense_calibration = policy.get("dense_reference_calibration")
    if not isinstance(dense_calibration, dict):
        raise TypeError(f"{context} dense_reference_calibration must be a mapping")
    canonical_dense_calibration = _trajectory_seed_sweep_dense_calibration(
        expected_schedule,
        runs,
        device=device,
        dense_record_frequency_gate=dense_gate,
    )
    _require_qt_exact_payload(
        dense_calibration,
        canonical_dense_calibration,
        context=f"{context} dense reference calibration",
    )
    declared_dense_accepted = _require_exact_bool_field(
        policy,
        "accepted_as_dense_calibrated_trajectory_evidence",
    )
    canonical_dense_accepted = _require_exact_bool_field(
        canonical_dense_calibration,
        "accepted_as_dense_calibrated_trajectory_evidence",
    )
    if declared_dense_accepted != canonical_dense_accepted:
        raise ValueError(
            f"{context} dense acceptance does not match raw sweep evidence"
        )
    for field, expected in (
        ("accepted_as_production_error_bound", False),
        ("accepted_for_production_scalable_backend", False),
        ("comparison_outcome_is_metric", False),
        ("epistemic_class", "c"),
    ):
        _require_bound_qt_field(
            policy,
            field,
            expected=expected,
            context=f"{context} seed_sweep_policy",
        )
    all_runs_accepted = all(run_acceptance)
    declared_all_runs_accepted = _require_exact_bool_field(
        policy,
        "all_sampled_runs_accepted",
    )
    if declared_all_runs_accepted != all_runs_accepted:
        raise ValueError(
            f"{context} run_summaries do not match all-sampled-runs acceptance"
        )
    derived_acceptance = bool(
        all_runs_accepted and evaluated and gate_passed
    )
    if accepted != derived_acceptance:
        raise ValueError(
            f"{context} run_summaries and gates do not reconstruct acceptance"
        )
    _require_qt_exact_payload(
        policy,
        {
            **canonical_comparison,
            "dense_reference_calibration": canonical_dense_calibration,
            "all_sampled_runs_accepted": all_runs_accepted,
            "accepted_as_restricted_seed_sweep_evidence": (
                derived_acceptance
            ),
            "accepted_as_dense_calibrated_trajectory_evidence": (
                canonical_dense_accepted
            ),
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        context=f"{context} seed_sweep_policy",
    )


def _validate_qt_bundle_policy_consistency(
    bundle: dict[str, Any],
    *,
    accepted: bool,
    expected_schedule: SubstepSchedule,
    context: str,
) -> None:
    policy = bundle.get("bundle_policy")
    if not isinstance(policy, dict):
        raise TypeError(f"{context} bundle policy must be a mapping")
    declared_restricted = _require_exact_bool_field(
        policy,
        "accepted_as_restricted_bundle_evidence",
    )
    declared_dense = _require_exact_bool_field(
        policy,
        "accepted_as_dense_calibrated_bundle_evidence",
    )
    bonds = _normalize_bond_sweep_values(bundle.get("bond_values"))
    seeds = _normalize_trajectory_sweep_seeds(bundle.get("rng_seeds"))
    trajectory_count = normalize_mps_index(
        bundle.get("trajectory_count"),
        name=f"{context}.trajectory_count",
        minimum=1,
    )
    max_branches = normalize_mps_index(
        bundle.get("max_branches"),
        name=f"{context}.max_branches",
        minimum=1,
    )
    record_budget = _normalize_max_record_materialization_outcomes(
        bundle.get("max_record_materialization_outcomes")
    )
    microstep_count = normalize_mps_index(
        bundle.get("microstep_count"),
        name=f"{context}.microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(
        bundle.get("finite_step_order")
    )
    convergence_gate = normalize_optional_mps_nonnegative_real(
        bundle.get("convergence_record_probability_gate"),
        name=f"{context}.convergence_record_probability_gate",
    )
    seed_gate = normalize_optional_mps_nonnegative_real(
        bundle.get("seed_record_frequency_spread_gate"),
        name=f"{context}.seed_record_frequency_spread_gate",
    )
    dense_gate = normalize_optional_mps_nonnegative_real(
        bundle.get("dense_record_frequency_gate"),
        name=f"{context}.dense_record_frequency_gate",
    )
    worst_gate = normalize_optional_mps_nonnegative_real(
        bundle.get("worst_cut_discarded_weight_gate"),
        name=f"{context}.worst_cut_discarded_weight_gate",
    )
    total_gate = normalize_optional_mps_nonnegative_real(
        bundle.get("total_discarded_weight_gate"),
        name=f"{context}.total_discarded_weight_gate",
    )
    device = normalize_mps_device(bundle.get("device"))
    exact_preflight = _record_materialization_preflight_for_schedule(
        expected_schedule,
        max_record_materialization_outcomes=record_budget,
    )
    sampled_preflight = _record_materialization_preflight_for_schedule(
        expected_schedule,
        max_record_materialization_outcomes=record_budget,
        trajectory_count=trajectory_count,
    )

    bond = bundle.get("bond_sweep")
    seed = bundle.get("trajectory_seed_sweep")
    if not isinstance(bond, dict) or not isinstance(seed, dict):
        raise TypeError(f"{context} nested sweeps must be mappings")
    bond_policy = bond.get("convergence_policy")
    seed_policy = seed.get("seed_sweep_policy")
    if not isinstance(bond_policy, dict) or not isinstance(seed_policy, dict):
        raise TypeError(f"{context} nested sweep policies must be mappings")
    bond_accepted = _require_exact_bool_field(
        bond_policy,
        "accepted_as_restricted_convergence_evidence",
    )
    seed_accepted = _require_exact_bool_field(
        seed_policy,
        "accepted_as_restricted_seed_sweep_evidence",
    )
    bond_backend = _validate_qt_aggregate_child(
        bond,
        accepted=bond_accepted,
        context=f"{context} bond sweep",
        expected_schema=AXIS1_QT_MPS_BOND_SWEEP_SCHEMA,
        expected_representability=(
            "axis1_qt_mps_restricted_finite_bond_convergence_sweep"
        ),
        expected_source_kind=expected_schedule.source_kind,
        expected_source_hash=expected_schedule.source_hash,
        expected_schedule_representability=expected_schedule.representability,
        expected_device=device,
        expected_fields={
            "bond_values": list(bonds),
            "reference_bond": bonds[-1],
            "max_branches": max_branches,
            "max_record_materialization_outcomes": record_budget,
            "record_materialization_preflight": exact_preflight,
            "microstep_count": microstep_count,
            "finite_step_order": finite_step_order,
            "convergence_record_probability_gate": convergence_gate,
            "worst_cut_discarded_weight_gate": worst_gate,
            "total_discarded_weight_gate": total_gate,
            "dense_oracle_certification_requested": True,
        },
    )
    seed_backend = _validate_qt_aggregate_child(
        seed,
        accepted=seed_accepted,
        context=f"{context} trajectory seed sweep",
        expected_schema=AXIS1_QT_MPS_TRAJECTORY_SWEEP_SCHEMA,
        expected_representability=(
            "axis1_qt_mps_restricted_seeded_trajectory_sweep"
        ),
        expected_source_kind=expected_schedule.source_kind,
        expected_source_hash=expected_schedule.source_hash,
        expected_schedule_representability=expected_schedule.representability,
        expected_device=device,
        expected_fields={
            "trajectory_count": trajectory_count,
            "rng_seeds": list(seeds),
            "max_bond": bonds[-1],
            "max_branches": max_branches,
            "max_record_materialization_outcomes": record_budget,
            "record_materialization_preflight": sampled_preflight,
            "microstep_count": microstep_count,
            "finite_step_order": finite_step_order,
            "seed_record_frequency_spread_gate": seed_gate,
            "dense_record_frequency_gate": dense_gate,
            "worst_cut_discarded_weight_gate": worst_gate,
            "total_discarded_weight_gate": total_gate,
            "dense_oracle_certification_requested": True,
        },
    )
    _validate_qt_bond_sweep_acceptance(
        bond,
        accepted=bond_accepted,
        expected_bonds=bonds,
        expected_schedule=expected_schedule,
        context=f"{context} bond sweep",
    )
    _validate_qt_seed_sweep_acceptance(
        seed,
        accepted=seed_accepted,
        expected_seeds=seeds,
        expected_trajectory_count=trajectory_count,
        expected_schedule=expected_schedule,
        expected_device=device,
        context=f"{context} trajectory seed sweep",
    )
    if bond_backend != _qt_run_summaries_backend_execution_claim(
        bond,
        expected_count=len(bonds),
        context=f"{context} bond sweep",
    ):
        raise ValueError(f"{context} bond backend claim does not match runs")
    if seed_backend != _qt_run_summaries_backend_execution_claim(
        seed,
        expected_count=len(seeds),
        context=f"{context} trajectory seed sweep",
    ):
        raise ValueError(f"{context} seed backend claim does not match runs")

    derived_restricted = bool(bond_accepted and seed_accepted)
    derived_dense = bool(
        _require_exact_bool_field(
            bond_policy["reference_dense_calibration"],
            "accepted_as_dense_calibrated_reference",
        )
        and _require_exact_bool_field(
            seed_policy,
            "accepted_as_dense_calibrated_trajectory_evidence",
        )
    )
    if (
        declared_restricted != derived_restricted
        or accepted != derived_restricted
    ):
        raise ValueError(
            f"{context} bundle policy and nested sweeps do not reconstruct "
            "bundle acceptance"
        )
    if declared_dense != derived_dense:
        raise ValueError(
            f"{context} dense bundle policy does not match nested sweeps"
        )
    declared_backend = _require_exact_bool_field(
        bundle,
        "claims_qt_mps_backend_execution",
    )
    if declared_backend != bool(bond_backend and seed_backend):
        raise ValueError(
            f"{context} backend claim does not match nested sweep execution"
        )
    _require_qt_exact_payload(
        policy,
        {
            "accepted_as_restricted_bundle_evidence": derived_restricted,
            "accepted_as_dense_calibrated_bundle_evidence": derived_dense,
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        context=f"{context} bundle policy",
    )


def _validate_qt_resource_probe_manifest(
    manifest: dict[str, Any],
    *,
    expected_schedule: SubstepSchedule,
    expected_bundle: dict[str, Any],
    expected_bonds: tuple[int, ...] | list[int],
    expected_trajectory_count: int,
    expected_seeds: tuple[int, ...] | list[int],
    expected_device: str,
    expected_max_branches: int,
    expected_max_record_materialization_outcomes: int,
    expected_microstep_count: int,
    expected_finite_step_order: str,
    expected_convergence_record_probability_gate: float | None,
    expected_seed_record_frequency_spread_gate: float | None,
    expected_dense_record_frequency_gate: float | None,
    expected_worst_cut_discarded_weight_gate: float | None,
    expected_total_discarded_weight_gate: float | None,
    expected_min_peak_allocated_gib: float | None,
    expected_min_peak_reserved_gib: float | None,
    expected_peak_allocated_bytes: int,
    expected_peak_reserved_bytes: int,
    expected_bundle_backend_executed: bool,
) -> None:
    context = "QT/MPS resource probe manifest"
    if type(manifest) is not dict:
        raise TypeError(f"{context} must be an exact mapping")
    if set(manifest) != _QT_RESOURCE_PROBE_TOP_LEVEL_FIELDS:
        missing = sorted(_QT_RESOURCE_PROBE_TOP_LEVEL_FIELDS.difference(manifest))
        extra = sorted(set(manifest).difference(_QT_RESOURCE_PROBE_TOP_LEVEL_FIELDS))
        raise ValueError(
            f"{context} fields do not match registered shape; "
            f"missing={missing!r} extra={extra!r}"
        )

    bonds = _normalize_bond_sweep_values(expected_bonds)
    seeds = _normalize_trajectory_sweep_seeds(expected_seeds)
    trajectory_count = normalize_mps_index(
        expected_trajectory_count,
        name=f"{context}.expected_trajectory_count",
        minimum=1,
    )
    max_branches = normalize_mps_index(
        expected_max_branches,
        name=f"{context}.expected_max_branches",
        minimum=1,
    )
    record_budget = _normalize_max_record_materialization_outcomes(
        expected_max_record_materialization_outcomes
    )
    microstep_count = normalize_mps_index(
        expected_microstep_count,
        name=f"{context}.expected_microstep_count",
        minimum=1,
    )
    finite_step_order = _normalize_finite_step_order(
        expected_finite_step_order
    )
    device = normalize_mps_device(expected_device)
    convergence_gate = normalize_optional_mps_nonnegative_real(
        expected_convergence_record_probability_gate,
        name=f"{context}.expected_convergence_record_probability_gate",
    )
    seed_gate = normalize_optional_mps_nonnegative_real(
        expected_seed_record_frequency_spread_gate,
        name=f"{context}.expected_seed_record_frequency_spread_gate",
    )
    dense_gate = normalize_optional_mps_nonnegative_real(
        expected_dense_record_frequency_gate,
        name=f"{context}.expected_dense_record_frequency_gate",
    )
    worst_gate = normalize_optional_mps_nonnegative_real(
        expected_worst_cut_discarded_weight_gate,
        name=f"{context}.expected_worst_cut_discarded_weight_gate",
    )
    total_gate = normalize_optional_mps_nonnegative_real(
        expected_total_discarded_weight_gate,
        name=f"{context}.expected_total_discarded_weight_gate",
    )
    min_allocated = normalize_optional_mps_nonnegative_real(
        expected_min_peak_allocated_gib,
        name=f"{context}.expected_min_peak_allocated_gib",
    )
    min_reserved = normalize_optional_mps_nonnegative_real(
        expected_min_peak_reserved_gib,
        name=f"{context}.expected_min_peak_reserved_gib",
    )
    peak_allocated = normalize_mps_index(
        expected_peak_allocated_bytes,
        name=f"{context}.expected_peak_allocated_bytes",
        minimum=0,
    )
    peak_reserved = normalize_mps_index(
        expected_peak_reserved_bytes,
        name=f"{context}.expected_peak_reserved_bytes",
        minimum=0,
    )
    if type(expected_bundle_backend_executed) is not bool:
        raise TypeError(f"{context}.expected_bundle_backend_executed must be bool")

    if type(expected_bundle) is not dict:
        raise TypeError(f"{context} expected evidence bundle must be an exact mapping")
    bundle_schema = _require_nonempty_text_field(
        expected_bundle,
        "schema",
        context=f"{context} expected evidence bundle",
    )
    if bundle_schema != AXIS1_QT_MPS_RESTRICTED_EVIDENCE_BUNDLE_SCHEMA:
        raise ValueError(f"{context} workload schema is not registered")
    _validate_qt_payload_content_hash(
        expected_bundle,
        context=f"{context} expected evidence bundle",
    )
    bundle_content_hash = _normalize_sha256_text(
        expected_bundle.get("content_hash"),
        name=f"{context}.expected_bundle.content_hash",
    )
    bundle_passed = _require_exact_bool_field(expected_bundle, "passed")
    bundle_verdict = _require_nonempty_text_field(
        expected_bundle,
        "verdict",
        context=f"{context} expected evidence bundle",
    )
    if bundle_verdict != ("pass" if bundle_passed else "fail"):
        raise ValueError(f"{context} expected bundle verdict must agree with passed")
    bundle_backend_executed = _require_exact_bool_field(
        expected_bundle,
        "claims_qt_mps_backend_execution",
    )
    if bundle_backend_executed != expected_bundle_backend_executed:
        raise ValueError(
            f"{context} expected bundle backend claim does not match "
            "authenticated workload"
        )

    record_materialization = _record_materialization_preflight_for_schedule(
        expected_schedule,
        max_record_materialization_outcomes=record_budget,
    )
    resource_policy = _resource_probe_policy(
        peak_allocated_bytes=peak_allocated,
        peak_reserved_bytes=peak_reserved,
        min_peak_allocated_gib=min_allocated,
        min_peak_reserved_gib=min_reserved,
    )
    resource_accepted = _require_exact_bool_field(
        resource_policy,
        "accepted_as_resource_probe",
    )
    passed = bool(bundle_passed and resource_accepted)
    canonical = {
        "schema": AXIS1_QT_MPS_RESOURCE_PROBE_SCHEMA,
        "source_kind": expected_schedule.source_kind,
        "source_hash": expected_schedule.source_hash,
        "schedule_representability": expected_schedule.representability,
        "representability": (
            "axis1_qt_mps_resource_probe_actual_execution_no_padding"
        ),
        "backend_contract": AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": device,
        "workload": "restricted_bond_and_seed_sweep_bundle",
        "bond_values": list(bonds),
        "reference_bond": int(max(bonds)),
        "trajectory_count": trajectory_count,
        "rng_seeds": list(seeds),
        "max_branches": max_branches,
        "max_record_materialization_outcomes": record_budget,
        "record_materialization_preflight": record_materialization,
        "workload_schema": bundle_schema,
        "workload_content_hash": bundle_content_hash,
        "workload_passed": bundle_passed,
        "microstep_count": microstep_count,
        "finite_step_order": finite_step_order,
        "convergence_record_probability_gate": convergence_gate,
        "seed_record_frequency_spread_gate": seed_gate,
        "dense_record_frequency_gate": dense_gate,
        "worst_cut_discarded_weight_gate": worst_gate,
        "total_discarded_weight_gate": total_gate,
        "min_peak_allocated_gib": min_allocated,
        "min_peak_reserved_gib": min_reserved,
        "resource_probe_policy": resource_policy,
        "claims_qt_mps_backend_execution": bundle_backend_executed,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scored_quantity_policy": (
            "CUDA memory resource probe is an execution/resource gate only; "
            "no new scored quantity"
        ),
        "passed": passed,
        "verdict": "pass" if passed else "fail",
    }
    canonical["content_hash"] = _stable_payload_hash(canonical)
    _require_qt_exact_payload(
        manifest,
        canonical,
        context=context,
    )


def _validate_qt_aggregate_child(
    child: dict[str, Any],
    *,
    accepted: bool,
    context: str,
    expected_schema: str,
    expected_representability: str,
    expected_source_kind: str,
    expected_source_hash: str,
    expected_schedule_representability: str,
    expected_device: str,
    expected_fields: dict[str, Any],
) -> bool:
    scored_quantity_policies = {
        "axis1_qt_mps_restricted_finite_bond_convergence_sweep": (
            "bond sweep convergence gate only; no new scored quantity"
        ),
        "axis1_qt_mps_restricted_seeded_trajectory_sweep": (
            "trajectory seed sweep gates are empirical verification gates only; "
            "no new scored quantity"
        ),
        "axis1_qt_mps_restricted_bond_and_seed_sweep_bundle": (
            "restricted QT/MPS evidence bundle combines verification gates only; "
            "no new scored quantity"
        ),
    }
    if expected_representability not in scored_quantity_policies:
        raise ValueError(f"{context} representability has no scored-quantity policy")
    common_fields = {
        "schema",
        "source_kind",
        "source_hash",
        "schedule_representability",
        "representability",
        "backend_contract",
        "gpu_required",
        "device",
        "claims_qt_mps_backend_execution",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "claims_production_scalable_backend",
        "scored_quantity_policy",
        "passed",
        "verdict",
        "content_hash",
    }
    representability_fields = {
        "axis1_qt_mps_restricted_finite_bond_convergence_sweep": {
            "convergence_policy",
            "runs",
            "run_summaries",
        },
        "axis1_qt_mps_restricted_seeded_trajectory_sweep": {
            "seed_sweep_policy",
            "runs",
            "run_summaries",
        },
        "axis1_qt_mps_restricted_bond_and_seed_sweep_bundle": {
            "bundle_policy",
            "bond_sweep",
            "trajectory_seed_sweep",
        },
    }
    expected_keys = (
        common_fields
        | set(expected_fields)
        | representability_fields[expected_representability]
    )
    if type(child) is not dict:
        raise TypeError(f"{context} aggregate child must be an exact mapping")
    if set(child) != expected_keys:
        missing = sorted(expected_keys.difference(child))
        extra = sorted(set(child).difference(expected_keys))
        raise ValueError(
            f"{context} aggregate fields do not match registered shape; "
            f"missing={missing!r} extra={extra!r}"
        )
    schema = _require_nonempty_text_field(child, "schema", context=context)
    if schema != expected_schema:
        raise ValueError(f"{context} aggregate schema is not registered")
    _require_bound_qt_field(
        child,
        "representability",
        expected=expected_representability,
        context=context,
    )
    _require_bound_qt_field(
        child,
        "scored_quantity_policy",
        expected=scored_quantity_policies[expected_representability],
        context=context,
    )
    _require_bound_qt_field(
        child, "source_kind", expected=expected_source_kind, context=context
    )
    _require_bound_qt_field(
        child, "source_hash", expected=expected_source_hash, context=context
    )
    _require_bound_qt_field(
        child,
        "schedule_representability",
        expected=expected_schedule_representability,
        context=context,
    )
    _require_bound_qt_field(
        child,
        "backend_contract",
        expected=AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        context=context,
    )
    _require_bound_qt_field(
        child, "device", expected=expected_device, context=context
    )
    _require_bound_qt_field(child, "gpu_required", expected=True, context=context)
    backend_execution_claim = _require_exact_bool_field(
        child,
        "claims_qt_mps_backend_execution",
    )
    for field, expected in (
        ("claims_exact_joint_lindblad_generator", False),
        ("claims_dense_channel_evidence", False),
        ("claims_dem_decoder_semantics", False),
        ("claims_axis2_source_timeline", False),
        ("claims_production_scalable_backend", False),
    ):
        _require_bound_qt_field(
            child, field, expected=expected, context=context
        )
    for field, expected in expected_fields.items():
        _require_bound_qt_field(
            child, field, expected=expected, context=context
        )
    passed = _require_exact_bool_field(child, "passed")
    verdict = _require_nonempty_text_field(child, "verdict", context=context)
    expected_verdict = "pass" if passed else "fail"
    if verdict != expected_verdict:
        raise ValueError(f"{context} verdict must agree with passed")
    if accepted != passed:
        raise ValueError(f"{context} accepted state must agree with passed")
    _validate_qt_payload_content_hash(child, context=context)
    return backend_execution_claim


def _bond_sweep_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    execution = run.get("mps_execution") or {}
    ledger = execution.get("mps_truncation_ledger") or {}
    acceptance = run.get("restricted_acceptance_policy") or {}
    truncation = acceptance.get("mps_truncation", {})
    return {
        "schema": run.get("schema"),
        "content_hash": run.get("content_hash"),
        "max_bond": run.get("max_bond"),
        "verdict": run.get("verdict"),
        "passed": _require_exact_bool_field(run, "passed"),
        "qt_mps_backend_executed": _require_exact_bool_field(
            run, "qt_mps_backend_executed"
        ),
        "carrier_program": run.get("carrier_program"),
        "measurement_keys": execution.get("measurement_keys"),
        "measurement_targets": execution.get("measurement_targets"),
        "measurement_records": execution.get("measurement_records"),
        "record_probabilities": execution.get("record_probabilities"),
        "record_count": execution.get("record_count"),
        "total_probability": execution.get("total_probability"),
        "total_probability_residual": execution.get("total_probability_residual"),
        "dense_jointL_record_certification": run.get(
            "dense_jointL_record_certification"
        ),
        "exact_bond_dimension_sufficient": ledger.get(
            "exact_bond_dimension_sufficient"
        ),
        "exact_bond_policy": ledger.get("exact_bond_policy"),
        "accepted_as_exact_bond_representation": truncation.get(
            "accepted_as_exact_bond_representation"
        ),
        "discarded_weight_sum": ledger.get("discarded_weight_sum"),
        "worst_cut_discarded_weight": ledger.get("worst_cut_discarded_weight"),
        "accepted_for_restricted_execution": acceptance.get(
            "accepted_for_restricted_execution"
        ),
        "accepted_for_production_scalable_backend": acceptance.get(
            "accepted_for_production_scalable_backend"
        ),
    }


def _trajectory_seed_sweep_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    execution = run.get("mps_execution") or {}
    sampling = execution.get("trajectory_sampling") or {}
    acceptance = run.get("restricted_acceptance_policy") or {}
    return {
        "schema": run.get("schema"),
        "content_hash": run.get("content_hash"),
        "rng_seed": sampling.get("rng_seed"),
        "trajectory_count": sampling.get("trajectory_count"),
        "verdict": run.get("verdict"),
        "passed": _require_exact_bool_field(run, "passed"),
        "qt_mps_backend_executed": _require_exact_bool_field(
            run, "qt_mps_backend_executed"
        ),
        "carrier_program": run.get("carrier_program"),
        "measurement_keys": execution.get("measurement_keys"),
        "measurement_targets": execution.get("measurement_targets"),
        "record_count": execution.get("record_count"),
        "measurement_records": execution.get("measurement_records"),
        "record_counts": execution.get("record_counts"),
        "record_probabilities": execution.get("record_probabilities"),
        "total_probability": execution.get("total_probability"),
        "total_probability_residual": execution.get("total_probability_residual"),
        "dense_jointL_record_certification": run.get(
            "dense_jointL_record_certification"
        ),
        "accepted_for_sampled_execution_evidence": acceptance.get(
            "accepted_for_sampled_execution_evidence"
        ),
        "accepted_for_production_scalable_backend": acceptance.get(
            "accepted_for_production_scalable_backend"
        ),
    }


def _record_probability_map(
    records: Any,
    probabilities: Any,
    *,
    context: str,
) -> tuple[dict[tuple[int, ...], float], int]:
    try:
        raw_records = list(records)
    except TypeError:
        raw_records = records
    if isinstance(raw_records, list) and len(raw_records) == 1:
        try:
            empty_record = list(raw_records[0]) == []
        except TypeError:
            empty_record = False
        if empty_record:
            normalized_probabilities = _normalize_probability_distribution(
                probabilities,
                name=f"{context}.record_probabilities",
            )
            if len(normalized_probabilities) != 1:
                raise ValueError(
                    f"{context}.record_probabilities length must match "
                    "measurement_records"
                )
            return {(): normalized_probabilities[0]}, 0
    normalized_records = _normalize_record_matrix(
        raw_records,
        name=f"{context}.measurement_records",
    )
    normalized_probabilities = _normalize_probability_distribution(
        probabilities,
        name=f"{context}.record_probabilities",
    )
    if len(normalized_records) != len(normalized_probabilities):
        raise ValueError(
            f"{context}.record_probabilities length must match measurement_records"
        )
    width = len(normalized_records[0])
    return (
        {
            tuple(record): probability
            for record, probability in zip(
                normalized_records,
                normalized_probabilities,
                strict=True,
            )
        },
        width,
    )


def _trajectory_seed_sweep_comparison(
    runs: list[dict[str, Any]],
    *,
    seed_record_frequency_spread_gate: float | None,
) -> dict[str, Any]:
    if not runs:
        raise ValueError("trajectory seed sweep requires at least one run")
    comparisons: list[dict[str, Any]] = []
    violations: list[str] = []
    probability_maps: list[dict[tuple[int, ...], float]] = []
    record_width: int | None = None
    for run_index, run in enumerate(runs):
        execution = run.get("mps_execution") or {}
        records = execution.get("measurement_records")
        probs = execution.get("record_probabilities")
        sampling = execution.get("trajectory_sampling") or {}
        if not _require_exact_bool_field(run, "qt_mps_backend_executed"):
            comparisons.append(
                {
                    "rng_seed": sampling.get("rng_seed"),
                    "compared_on_union_support": False,
                    "reason": "run_not_executed",
                    "comparison_outcome_is_metric": False,
                }
            )
            violations.append("run_not_executed")
            continue
        if records is None or probs is None:
            comparisons.append(
                {
                    "rng_seed": sampling.get("rng_seed"),
                    "compared_on_union_support": False,
                    "reason": "record_probability_payload_missing",
                    "comparison_outcome_is_metric": False,
                }
            )
            violations.append("record_probability_payload_missing")
            continue
        probability_map, width = _record_probability_map(
            records,
            probs,
            context=f"seed sweep run {run_index}",
        )
        if record_width is None:
            record_width = width
        elif width != record_width:
            comparisons.append(
                {
                    "rng_seed": sampling.get("rng_seed"),
                    "compared_on_union_support": False,
                    "reason": "measurement_record_width_mismatch",
                    "comparison_outcome_is_metric": False,
                }
            )
            violations.append("measurement_record_width_mismatch")
            continue
        probability_maps.append(probability_map)
        comparisons.append(
            {
                "rng_seed": sampling.get("rng_seed"),
                "compared_on_union_support": True,
                "emitted_record_count": len(probability_map),
                "comparison_object": "record_probabilities",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        )
    observed = 0.0
    union_support = sorted(
        {
            record
            for probability_map in probability_maps
            for record in probability_map
        }
    )
    if probability_maps:
        observed = max(
            (
                max(
                    probability_map.get(record, 0.0)
                    for probability_map in probability_maps
                )
                - min(
                    probability_map.get(record, 0.0)
                    for probability_map in probability_maps
                )
                for record in union_support
            ),
            default=0.0,
        )
    evaluated = seed_record_frequency_spread_gate is not None
    if evaluated and observed > float(seed_record_frequency_spread_gate):
        violations.append("seed_record_frequency_spread_exceeds_gate")
    return {
        "comparison_object": "record_probabilities",
        "record_support_alignment_policy": (
            _UNION_RECORD_SUPPORT_ALIGNMENT_POLICY
        ),
        "union_record_support_size": len(union_support),
        "comparisons": comparisons,
        "max_record_frequency_spread_across_seeds": float(observed),
        "seed_spread_gate": {
            "evaluated": evaluated,
            "seed_record_frequency_spread_gate": (
                None
                if seed_record_frequency_spread_gate is None
                else float(seed_record_frequency_spread_gate)
            ),
            "observed_max_record_frequency_spread": float(observed),
            "passed": None if not evaluated else not violations,
            "violations": violations,
            "gate_role": "heuristic_seed_sweep_frequency_spread_gate_not_metric",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def _trajectory_seed_sweep_dense_calibration(
    schedule: SubstepSchedule,
    runs: list[dict[str, Any]],
    *,
    device: str,
    dense_record_frequency_gate: float | None,
) -> dict[str, Any]:
    reference = runs[0]
    requires_scalable = _require_exact_bool_field(
        reference["carrier_program"], "requires_scalable_backend"
    )
    if requires_scalable:
        return {
            "status": "not_available_overcap",
            "executed": False,
            "passed": None,
            "accepted_as_dense_calibrated_trajectory_evidence": False,
            "dense_record_frequency_gate": (
                None
                if dense_record_frequency_gate is None
                else float(dense_record_frequency_gate)
            ),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        }
    if dense_record_frequency_gate is None:
        return {
            "status": "not_requested",
            "executed": False,
            "passed": None,
            "accepted_as_dense_calibrated_trajectory_evidence": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        }
    try:
        dense = axis1_measurement_record_evidence_manifest(schedule, device=device)
    except ValueError as exc:
        return {
            "status": "failed",
            "executed": False,
            "passed": False,
            "reason": "dense_jointL_record_evidence_unavailable",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "accepted_as_dense_calibrated_trajectory_evidence": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        }
    dense_record = _validated_dense_record_evidence(
        schedule,
        dense,
        device=device,
        context="seed dense Record evidence",
    )
    dense_records = dense_record["measurement_records"]
    dense_probability_map, dense_record_width = _record_probability_map(
        dense_records,
        dense_record["record_probabilities"],
        context="dense Record evidence",
    )
    violations: list[str] = []
    residuals: list[float] = []
    total_variation_distances: list[float] = []
    for run_index, run in enumerate(runs):
        execution = run.get("mps_execution") or {}
        if not _require_exact_bool_field(run, "qt_mps_backend_executed"):
            violations.append("run_not_executed")
            continue
        probability_map, width = _record_probability_map(
            execution.get("measurement_records"),
            execution.get("record_probabilities"),
            context=f"dense calibration run {run_index}",
        )
        if width != dense_record_width:
            violations.append("measurement_record_width_mismatch")
            continue
        union_support = set(dense_probability_map) | set(probability_map)
        absolute_differences = [
            abs(
                probability_map.get(record, 0.0)
                - dense_probability_map.get(record, 0.0)
            )
            for record in union_support
        ]
        residuals.append(max(absolute_differences, default=0.0))
        total_variation_distances.append(
            0.5 * math.fsum(absolute_differences)
        )
    observed = float(max(residuals, default=0.0))
    if observed > float(dense_record_frequency_gate):
        violations.append("dense_record_frequency_difference_exceeds_gate")
    passed = not violations
    return {
        "status": "passed" if passed else "failed",
        "executed": True,
        "passed": passed,
        "accepted_as_dense_calibrated_trajectory_evidence": passed,
        "dense_evidence_schema": dense["schema"],
        "dense_evidence_content_hash": dense["content_hash"],
        "comparison_object": "record_probabilities",
        "record_support_alignment_policy": (
            _UNION_RECORD_SUPPORT_ALIGNMENT_POLICY
        ),
        "dense_record_frequency_gate": float(dense_record_frequency_gate),
        "observed_max_abs_frequency_difference": observed,
        "observed_max_total_variation_distance": float(
            max(total_variation_distances, default=0.0)
        ),
        "total_variation_convention": "TV = 1/2 * sum_i |p_i - q_i|",
        "violations": violations,
        "gate_role": "heuristic_dense_record_frequency_gate_not_metric",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def _resource_probe_policy(
    *,
    peak_allocated_bytes: int,
    peak_reserved_bytes: int,
    min_peak_allocated_gib: float | None,
    min_peak_reserved_gib: float | None,
) -> dict[str, Any]:
    min_peak_allocated_gib = normalize_optional_mps_nonnegative_real(
        min_peak_allocated_gib,
        name="min_peak_allocated_gib",
    )
    min_peak_reserved_gib = normalize_optional_mps_nonnegative_real(
        min_peak_reserved_gib,
        name="min_peak_reserved_gib",
    )
    allocated_gib = float(peak_allocated_bytes) / float(1024**3)
    reserved_gib = float(peak_reserved_bytes) / float(1024**3)
    allocated_evaluated = min_peak_allocated_gib is not None
    reserved_evaluated = min_peak_reserved_gib is not None
    violations: list[str] = []
    if allocated_evaluated and allocated_gib < float(min_peak_allocated_gib):
        violations.append("peak_allocated_gib_below_gate")
    if reserved_evaluated and reserved_gib < float(min_peak_reserved_gib):
        violations.append("peak_reserved_gib_below_gate")
    evaluated = allocated_evaluated or reserved_evaluated
    return {
        "measurement_backend": "torch.cuda.max_memory_allocated_and_reserved",
        "memory_pressure_source": "actual_restricted_qt_mps_execution_only_no_padding",
        "peak_allocated_bytes": int(peak_allocated_bytes),
        "peak_reserved_bytes": int(peak_reserved_bytes),
        "peak_allocated_gib": allocated_gib,
        "peak_reserved_gib": reserved_gib,
        "min_peak_allocated_gib": (
            None if min_peak_allocated_gib is None else float(min_peak_allocated_gib)
        ),
        "min_peak_reserved_gib": (
            None if min_peak_reserved_gib is None else float(min_peak_reserved_gib)
        ),
        "gate_evaluated": evaluated,
        "gate_passed": None if not evaluated else not violations,
        "violations": violations,
        "accepted_as_resource_probe": bool(not evaluated or not violations),
        "accepted_for_production_scalable_backend": False,
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def _bond_sweep_comparison(
    runs: list[dict[str, Any]],
    *,
    convergence_record_probability_gate: float | None,
) -> dict[str, Any]:
    reference = runs[-1]
    reference_execution = reference.get("mps_execution") or {}
    reference_records = reference_execution.get("measurement_records")
    reference_probs = reference_execution.get("record_probabilities")
    comparisons: list[dict[str, Any]] = []
    violations: list[str] = []
    observed_deltas: list[float] = []
    if reference_records is None or reference_probs is None:
        violations.append("reference_run_has_no_record_probabilities")
    for run in runs[:-1]:
        execution = run.get("mps_execution") or {}
        records = execution.get("measurement_records")
        probs = execution.get("record_probabilities")
        if not _require_exact_bool_field(run, "qt_mps_backend_executed"):
            comparisons.append(
                {
                    "max_bond": run.get("max_bond"),
                    "compared_to_reference": False,
                    "reason": "run_not_executed",
                    "comparison_outcome_is_metric": False,
                }
            )
            violations.append("non_reference_run_not_executed")
            continue
        if records != reference_records or probs is None or reference_probs is None:
            comparisons.append(
                {
                    "max_bond": run.get("max_bond"),
                    "compared_to_reference": False,
                    "reason": "measurement_record_order_mismatch",
                    "comparison_outcome_is_metric": False,
                }
            )
            violations.append("measurement_record_order_mismatch")
            continue
        delta = max(
            (
                abs(float(a) - float(b))
                for a, b in zip(probs, reference_probs, strict=True)
            ),
            default=0.0,
        )
        observed_deltas.append(float(delta))
        comparisons.append(
            {
                "max_bond": run.get("max_bond"),
                "reference_bond": reference.get("max_bond"),
                "compared_to_reference": True,
                "comparison_object": "record_probabilities",
                "max_abs_probability_difference": float(delta),
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        )
    observed = float(max(observed_deltas, default=0.0))
    evaluated = convergence_record_probability_gate is not None
    if evaluated and observed > float(convergence_record_probability_gate):
        violations.append("record_probability_difference_exceeds_gate")
    return {
        "comparison_object": "record_probabilities",
        "reference_bond": reference.get("max_bond"),
        "comparisons": comparisons,
        "max_abs_probability_difference_vs_reference": observed,
        "convergence_gate": {
            "evaluated": evaluated,
            "convergence_record_probability_gate": (
                None
                if convergence_record_probability_gate is None
                else float(convergence_record_probability_gate)
            ),
            "observed_max_abs_probability_difference": observed,
            "passed": None if not evaluated else not violations,
            "violations": violations,
            "gate_role": "heuristic_bond_sweep_convergence_gate_not_metric",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "accepted_as_production_error_bound": False,
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def _bond_sweep_reference_calibration(reference: dict[str, Any]) -> dict[str, Any]:
    certification = reference.get("dense_jointL_record_certification", {})
    status = _dense_certification_status(certification)
    executed = _require_exact_bool_field(certification, "executed")
    passed = (
        _require_exact_bool_field(certification, "passed")
        if executed
        else _require_exact_bool_field(certification, "passed", default=False)
    )
    accepted = bool(executed and passed)
    return {
        "status": status,
        "executed": executed,
        "passed": passed if executed else None,
        "accepted_as_dense_calibrated_reference": accepted,
        "dense_evidence_schema": certification.get("dense_evidence_schema"),
        "dense_evidence_content_hash": certification.get("dense_evidence_content_hash"),
        "comparison_outcome_is_metric": _require_exact_bool_field(
            certification,
            "comparison_outcome_is_metric",
        ),
        "epistemic_class": "a/c",
    }


def _truncation_gate_result(
    ledger: dict[str, Any],
    *,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
) -> dict[str, Any]:
    worst_gate = normalize_optional_mps_nonnegative_real(
        worst_cut_discarded_weight_gate,
        name="worst_cut_discarded_weight_gate",
    )
    total_gate = normalize_optional_mps_nonnegative_real(
        total_discarded_weight_gate,
        name="total_discarded_weight_gate",
    )
    gate_values = {
        "worst_cut_discarded_weight_gate": worst_gate,
        "total_discarded_weight_gate": total_gate,
    }
    ledger_complete = _require_exact_bool_field(
        ledger,
        "discarded_weight_ledger_complete",
    )
    raw_worst = ledger["worst_cut_discarded_weight"]
    raw_total = ledger["discarded_weight_sum"]
    worst_is_valid = _is_finite_nonnegative_real(raw_worst)
    total_is_valid = _is_finite_nonnegative_real(raw_total)
    worst = float(raw_worst) if worst_is_valid else None
    total = float(raw_total) if total_is_valid else None
    violations: list[str] = []
    if not ledger_complete:
        violations.append("incomplete_truncation_aggregation_context")
    if not worst_is_valid:
        violations.append("invalid_worst_cut_discarded_weight")
    if not total_is_valid:
        violations.append("invalid_discarded_weight_sum")
    if (
        gate_values["worst_cut_discarded_weight_gate"] is not None
        and worst is not None
        and worst > gate_values["worst_cut_discarded_weight_gate"]
    ):
        violations.append("worst_cut_discarded_weight_exceeds_gate")
    if (
        gate_values["total_discarded_weight_gate"] is not None
        and total is not None
        and total > gate_values["total_discarded_weight_gate"]
    ):
        violations.append("total_discarded_weight_exceeds_gate")
    evaluated = bool(
        any(value is not None for value in gate_values.values())
        or not ledger_complete
        or not worst_is_valid
        or not total_is_valid
    )
    return {
        "evaluated": evaluated,
        **gate_values,
        "observed_worst_cut_discarded_weight": worst,
        "observed_total_discarded_weight": total,
        "passed": None if not evaluated else not violations,
        "violations": violations,
        "gate_role": "heuristic_finite_bond_policy_gate_not_metric",
        "accepted_as_production_error_bound": False,
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


_MISSING = object()


def _require_exact_bool_field(
    values: dict[str, Any],
    name: str,
    *,
    default: Any = _MISSING,
) -> bool:
    if name in values:
        value = values[name]
    elif default is not _MISSING:
        value = default
    else:
        raise KeyError(name)
    if type(value) is not bool:
        raise TypeError(f"{name} must be an actual bool")
    return value


def _require_nonempty_text_field(
    values: dict[str, Any],
    name: str,
    *,
    context: str,
) -> str:
    value = values[name]
    if not isinstance(value, str) or not value:
        raise TypeError(f"{context}.{name} must be a nonempty string")
    return value


def _is_finite_nonnegative_real(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        normalized = float(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return bool(math.isfinite(normalized) and normalized >= 0.0)


def _normalize_probability_distribution(
    values: Any,
    *,
    name: str,
) -> list[float]:
    try:
        raw_values = list(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of real probabilities") from exc
    if not raw_values:
        raise ValueError(f"{name} must be nonempty")

    probabilities: list[float] = []
    for index, value in enumerate(raw_values):
        item_name = f"{name}[{index}]"
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{item_name} must be a real probability")
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError(f"{item_name} must be finite")
        if normalized < 0.0:
            raise ValueError(f"{item_name} must be nonnegative")
        probabilities.append(normalized)
    if abs(math.fsum(probabilities) - 1.0) > NUMERICAL_ZERO:
        raise ValueError(
            f"{name} must sum to one within NUMERICAL_ZERO={NUMERICAL_ZERO}"
        )
    return probabilities


def _normalize_sha256_text(value: Any, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a lowercase SHA-256 hex string")
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex string")
    return value


def _normalize_record_matrix(values: Any, *, name: str) -> list[list[int]]:
    try:
        raw_records = list(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of bit records") from exc
    if not raw_records:
        raise ValueError(f"{name} must be nonempty")
    records: list[list[int]] = []
    expected_width: int | None = None
    for record_index, raw_record in enumerate(raw_records):
        try:
            raw_values = list(raw_record)
        except TypeError as exc:
            raise TypeError(f"{name}[{record_index}] must be an iterable") from exc
        if not raw_values:
            raise ValueError(f"{name}[{record_index}] must be nonempty")
        if expected_width is None:
            expected_width = len(raw_values)
        elif len(raw_values) != expected_width:
            raise ValueError(f"{name} records must have equal width")
        record: list[int] = []
        for value_index, value in enumerate(raw_values):
            item_name = f"{name}[{record_index}][{value_index}]"
            if isinstance(value, bool):
                raise TypeError(f"{item_name} must be an integer bit, not bool")
            try:
                normalized = operator.index(value)
            except TypeError as exc:
                raise TypeError(f"{item_name} must be an integer bit") from exc
            normalized = int(normalized)
            if normalized not in {0, 1}:
                raise ValueError(f"{item_name} must be zero or one")
            record.append(normalized)
        records.append(record)
    if len({tuple(record) for record in records}) != len(records):
        raise ValueError(f"{name} must not contain duplicate outcomes")
    return records


def _normalize_count_vector(values: Any, *, name: str) -> list[int]:
    try:
        raw_values = list(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of counts") from exc
    if not raw_values:
        raise ValueError(f"{name} must be nonempty")
    return [
        _normalize_nonnegative_index(value, name=f"{name}[{index}]")
        for index, value in enumerate(raw_values)
    ]


def _normalize_measurement_keys(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("measurement_keys must be a list or tuple")
    keys: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"measurement_keys[{index}] must be text")
        if not value:
            raise ValueError(f"measurement_keys[{index}] must be nonempty")
        keys.append(value)
    if len(set(keys)) != len(keys):
        raise ValueError("measurement_keys must not contain duplicates")
    return keys


def _normalize_measurement_targets(values: Any) -> list[int]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("measurement_targets must be a list or tuple")
    return [
        _normalize_nonnegative_index(
            value,
            name=f"measurement_targets[{index}]",
        )
        for index, value in enumerate(values)
    ]


def _validate_qt_record_execution_payload(
    execution: dict[str, Any],
    *,
    sampled: bool,
    trajectory_count: int | None,
) -> bool:
    measurement_keys = _normalize_measurement_keys(
        execution.get("measurement_keys", ())
    )
    measurement_targets = _normalize_measurement_targets(
        execution.get("measurement_targets", ())
    )
    if len(measurement_targets) != len(measurement_keys):
        raise ValueError(
            "measurement_targets length must match measurement_keys"
        )
    probabilities = _normalize_probability_distribution(
        execution.get("record_probabilities", ()),
        name="record_probabilities",
    )
    raw_records = execution.get("measurement_records", ())
    try:
        raw_record_count = len(raw_records)
    except TypeError as exc:
        raise TypeError("measurement_records must be a sized iterable") from exc
    record_count = _normalize_nonnegative_index(
        execution.get("record_count"),
        name="record_count",
    )
    if record_count != raw_record_count:
        raise ValueError("record_count must match measurement_records")
    total_probability = execution.get("total_probability")
    if not _is_finite_nonnegative_real(total_probability):
        raise ValueError("total_probability must be a finite nonnegative real")
    if abs(float(total_probability) - math.fsum(probabilities)) > NUMERICAL_ZERO:
        raise ValueError(
            "total_probability must equal the sum of record_probabilities"
        )
    residual = execution.get("total_probability_residual")
    if type(residual) is not float or not math.isfinite(residual) or residual < 0.0:
        raise TypeError(
            "total_probability_residual must be an exact finite nonnegative float"
        )
    expected_residual = abs(float(total_probability) - 1.0)
    if residual != expected_residual:
        raise ValueError(
            "total_probability_residual must equal abs(total_probability - 1)"
        )

    if not measurement_keys:
        try:
            no_measurement_records = [list(record) for record in raw_records]
        except TypeError as exc:
            raise TypeError("measurement_records must be an iterable") from exc
        if (
            no_measurement_records != [[]]
            or len(probabilities) != 1
            or abs(probabilities[0] - 1.0) > NUMERICAL_ZERO
        ):
            raise ValueError(
                "no-measurement execution must carry exactly one empty Record "
                "with probability one within NUMERICAL_ZERO"
            )
        if sampled:
            counts = _normalize_count_vector(
                execution.get("record_counts", ()),
                name="record_counts",
            )
            if trajectory_count is None or counts != [trajectory_count]:
                raise ValueError(
                    "no-measurement sampled record_counts must equal trajectory_count"
                )
        return False

    records = _normalize_record_matrix(
        raw_records,
        name="measurement_records",
    )
    expected_record_width = len(measurement_keys)
    for index, record in enumerate(records):
        if len(record) != expected_record_width:
            raise ValueError(
                f"measurement_records[{index}] width must match measurement_keys"
            )
    if len(records) != len(probabilities):
        raise ValueError(
            "record_probabilities length must match measurement_records"
        )
    if sampled:
        if trajectory_count is None:
            raise ValueError("sampled Record execution requires trajectory_count")
        counts = _normalize_count_vector(
            execution.get("record_counts", ()),
            name="record_counts",
        )
        if len(counts) != len(probabilities):
            raise ValueError("record_counts length must match record_probabilities")
        if any(count <= 0 for count in counts):
            raise ValueError(
                "observed-only sampled record_counts must be strictly positive"
            )
        if sum(counts) != trajectory_count:
            raise ValueError("record_counts must sum to trajectory_count")
        if records != sorted(records):
            raise ValueError(
                "sampled measurement_records must be lexicographically sorted"
            )
        for index, (probability, count) in enumerate(zip(probabilities, counts)):
            expected = float(count) / float(trajectory_count)
            if abs(probability - expected) > NUMERICAL_ZERO:
                raise ValueError(
                    "record_probabilities"
                    f"[{index}] must equal record_counts[{index}] / trajectory_count"
                )
    else:
        expected_records = [
            list(record)
            for record in materialize_binary_records(expected_record_width)
        ]
        if records != expected_records:
            raise ValueError(
                "exact measurement_records must emit canonical LSB-first full "
                "binary Record support"
            )
    return True


def _normalize_nonnegative_index(value: Any, *, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"{name} must be an integer") from exc
    if normalized < 0:
        raise ValueError(f"{name} must be nonnegative")
    return int(normalized)


def _normalize_integer_index(value: Any, *, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        return int(operator.index(value))
    except TypeError as exc:
        raise TypeError(f"{name} must be an integer") from exc


def _normalize_max_record_materialization_outcomes(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError(
            "max_record_materialization_outcomes must be an integer, not bool"
        )
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(
            "max_record_materialization_outcomes must be an integer"
        ) from exc
    if normalized <= 0:
        raise ValueError("max_record_materialization_outcomes must be positive")
    if normalized > sys.maxsize:
        raise ValueError(
            "max_record_materialization_outcomes must not exceed sys.maxsize"
        )
    return int(normalized)


def _validate_qt_record_materialization_preflight_payload(
    preflight: Any,
    *,
    execution: dict[str, Any],
    sampled: bool,
    trajectory_count: int | None,
) -> None:
    if not isinstance(preflight, dict):
        raise TypeError("record materialization preflight must be a mapping")
    if preflight.get("schema") != (
        _AXIS1_QT_MPS_RECORD_MATERIALIZATION_PREFLIGHT_SCHEMA
    ):
        raise ValueError("preflight schema is not registered")
    expected_support_policy = (
        _OBSERVED_EMPIRICAL_RECORD_SUPPORT_POLICY
        if sampled
        else _FULL_BINARY_RECORD_SUPPORT_POLICY
    )
    if preflight.get("record_support_policy") != expected_support_policy:
        raise ValueError(
            "preflight record_support_policy does not match execution"
        )
    if preflight.get("trajectory_count") != trajectory_count:
        raise ValueError("preflight trajectory_count does not match execution")
    measurement_keys = _normalize_measurement_keys(
        execution.get("measurement_keys", ())
    )
    width = _normalize_nonnegative_index(
        preflight.get("total_measurement_width"),
        name="preflight.total_measurement_width",
    )
    if width != len(measurement_keys):
        raise ValueError(
            "preflight total_measurement_width does not match measurement_keys"
        )
    boundary_count = _normalize_nonnegative_index(
        preflight.get("measurement_boundary_count"),
        name="preflight.measurement_boundary_count",
    )
    if (width == 0 and boundary_count != 0) or (
        width > 0 and not 1 <= boundary_count <= width
    ):
        raise ValueError(
            "preflight measurement_boundary_count is inconsistent with width"
        )
    if sampled:
        if trajectory_count is None:
            raise ValueError("sampled preflight requires trajectory_count")
        expected_upper_bound = (
            trajectory_count
            if width >= trajectory_count.bit_length()
            else 1 << width
        )
    else:
        expected_upper_bound = 1 << width
    upper_bound = _normalize_nonnegative_index(
        preflight.get("materialized_outcome_count_upper_bound"),
        name="preflight.materialized_outcome_count_upper_bound",
    )
    if upper_bound != expected_upper_bound:
        raise ValueError(
            "preflight materialized_outcome_count_upper_bound does not match "
            "the execution strategy"
        )
    requires_full_support = _require_exact_bool_field(
        preflight,
        "requires_full_binary_support_materialization",
    )
    if requires_full_support != (not sampled):
        raise ValueError(
            "preflight full-support flag does not match execution strategy"
        )
    budget = _normalize_max_record_materialization_outcomes(
        preflight.get("max_record_materialization_outcomes")
    )
    if upper_bound > budget:
        raise ValueError("preflight upper_bound exceeds its declared budget")
    for field in (
        "within_budget",
        "checked_before_cuda",
        "checked_before_record_allocation",
    ):
        if not _require_exact_bool_field(preflight, field):
            raise ValueError(f"preflight {field} must be true")


def _record_materialization_preflight_for_schedule(
    schedule: SubstepSchedule,
    *,
    max_record_materialization_outcomes: int,
    trajectory_count: int | None = None,
) -> dict[str, Any]:
    _validate_schedule_for_axis1_channel_evidence(schedule)
    return _record_materialization_preflight(
        axis1_record_layout_from_schedule(schedule),
        max_record_materialization_outcomes=max_record_materialization_outcomes,
        trajectory_count=trajectory_count,
    )


def _record_materialization_preflight(
    record_layout: Axis1ScheduleRecordLayout,
    *,
    max_record_materialization_outcomes: int,
    trajectory_count: int | None = None,
) -> dict[str, Any]:
    budget = _normalize_max_record_materialization_outcomes(
        max_record_materialization_outcomes
    )
    normalized_trajectory_count = normalize_optional_mps_index(
        trajectory_count,
        name="trajectory_count",
        minimum=1,
    )
    total_measurement_width = int(record_layout.measurement_width)
    measurement_boundary_count = len(record_layout.boundaries)
    requires_full_support = normalized_trajectory_count is None
    if requires_full_support:
        if total_measurement_width >= budget.bit_length():
            raise ValueError(
                "record materialization outcome budget exceeded: "
                f"total_measurement_width={total_measurement_width} requires more "
                "than max_record_materialization_outcomes="
                f"{budget} outcomes"
            )
        materialized_outcome_count_upper_bound = 1 << total_measurement_width
        record_support_policy = _FULL_BINARY_RECORD_SUPPORT_POLICY
    else:
        if total_measurement_width >= normalized_trajectory_count.bit_length():
            materialized_outcome_count_upper_bound = normalized_trajectory_count
        else:
            materialized_outcome_count_upper_bound = 1 << total_measurement_width
        record_support_policy = _OBSERVED_EMPIRICAL_RECORD_SUPPORT_POLICY
    if materialized_outcome_count_upper_bound > budget:
        raise ValueError(
            "record materialization outcome budget exceeded: "
            "record support may contain up to "
            f"{materialized_outcome_count_upper_bound} outcomes, exceeding "
            f"max_record_materialization_outcomes={budget}"
        )
    return {
        "schema": _AXIS1_QT_MPS_RECORD_MATERIALIZATION_PREFLIGHT_SCHEMA,
        "record_support_policy": record_support_policy,
        "trajectory_count": normalized_trajectory_count,
        "measurement_boundary_count": measurement_boundary_count,
        "total_measurement_width": total_measurement_width,
        "materialized_outcome_count_upper_bound": (
            materialized_outcome_count_upper_bound
        ),
        "requires_full_binary_support_materialization": requires_full_support,
        "max_record_materialization_outcomes": budget,
        "within_budget": True,
        "checked_before_cuda": True,
        "checked_before_record_allocation": True,
    }


def _qt_expected_actual_split_occurrences(
    program: dict[str, Any],
    *,
    microstep_count: int,
    finite_step_order: str,
) -> tuple[dict[str, Any], ...]:
    """Build the complete capped two-site occurrence inventory before execution."""

    count = int(microstep_count)
    if count < 1:
        raise ValueError("microstep_count must be positive")
    step_order = _normalize_finite_step_order(finite_step_order)
    pass_indices = (0, 1) if step_order == _FINITE_STEP_ORDER_STRANG else (0,)
    occurrences: list[dict[str, Any]] = []
    for substep in program["program"]["substeps"]:
        if str(substep["substep_kind"]) == "reset":
            continue
        two_site_terms: list[tuple[int, dict[str, Any], tuple[int, int]]] = []
        for term_index, term in enumerate(substep.get("terms", ())):
            if str(term["kind"]) != "hamiltonian":
                continue
            support = tuple(int(q) for q in term["support"])
            family = str(term["operator_family"]).upper()
            if len(support) != 2:
                continue
            if family not in {"ZZ", "FSIM_PHASE"} and not family.startswith("CTRL_"):
                continue
            two_site_terms.append((int(term_index), term, support))
        if not two_site_terms:
            continue
        dt_micro = float(substep["dt_ns"]) / float(count)
        dt_effective = (
            0.5 * dt_micro
            if step_order == _FINITE_STEP_ORDER_STRANG
            else dt_micro
        )
        for microstep_index in range(count):
            for pass_index in pass_indices:
                for term_index, term, support in two_site_terms:
                    occurrences.append(
                        {
                            "substep_id": str(substep["substep_id"]),
                            "term_index": int(term_index),
                            "operator_family": str(term["operator_family"]),
                            "support": [int(support[0]), int(support[1])],
                            "microstep_index": int(microstep_index),
                            "microstep_count": int(count),
                            "hamiltonian_pass_index": int(pass_index),
                            "dt_ns_effective": float(dt_effective),
                        }
                    )
    return tuple(occurrences)


def _unsupported_substeps(program: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for substep in program["program"]["substeps"]:
        kind = str(substep["substep_kind"])
        if kind not in {"idle", "one_qubit_gate", "two_qubit_gate", "measurement", "reset"}:
            out.append(_unsupported(substep, "substep_kind_not_supported_by_restricted_qt_mps"))
            continue
        for term in substep.get("terms", ()):
            term_kind = str(term["kind"])
            family = str(term["operator_family"]).upper()
            if term_kind == "collapse" and family not in {"T1", "T1_UP", "T2", "RD"}:
                out.append(_unsupported(substep, f"unsupported_collapse_family:{family}"))
                break
            if term_kind == "hamiltonian" and not _is_supported_qt_hamiltonian_term(term):
                out.append(_unsupported(substep, f"unsupported_hamiltonian_family:{family}"))
                break
            if term_kind == "measurement_boundary":
                continue
            if term_kind == "instrument" and family in {"RESET_Z", "RESET_X", "RESET_Y"}:
                continue
            if term_kind not in {"hamiltonian", "collapse", "measurement_boundary", "instrument"}:
                out.append(_unsupported(substep, f"unsupported_term_kind:{term_kind}"))
                break
        if kind == "measurement":
            records = list(substep.get("operation_records", ()))
            if len(records) != 1:
                out.append(_unsupported(substep, "measurement_requires_one_operation_record"))
                continue
            op = records[0]
            if str(op.get("basis", "Z")).upper() != "Z":
                out.append(_unsupported(substep, "restricted_qt_mps_supports_z_measurement_only"))
        if kind == "reset":
            for op in substep.get("operation_records", ()):
                if axis1_reset_basis(str(op.get("name", ""))) is None:
                    out.append(_unsupported(substep, "restricted_qt_mps_supports_pauli_reset_only"))
                    break
    return out


def _unsupported(substep: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "substep_id": str(substep["substep_id"]),
        "substep_kind": str(substep["substep_kind"]),
        "reason": str(reason),
    }


def _is_supported_qt_hamiltonian_term(term: dict[str, Any]) -> bool:
    """Return whether the restricted QT executor has an actual lowering path."""

    family = str(term["operator_family"]).upper()
    support = tuple(term["support"])
    if family in {"ZZ", "FSIM_PHASE"} and len(support) == 2:
        return True
    # COH_* is deliberately absent. The restricted QT executor has no coherent-family
    # apply branch, so support must not be inferred from the broader MCWF lowering surface.
    if not family.startswith("CTRL_"):
        return False
    gate = family.removeprefix("CTRL_")
    if len(support) == 1:
        try:
            _one_qubit_gate_matrix(gate)
        except ValueError:
            return False
        return True
    return len(support) == 2 and gate in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES


def _apply_hamiltonian_terms(
    mps,
    substep: dict[str, Any],
    *,
    device: str,
    max_bond: int | None,
    branch_bits: tuple[int, ...],
    truncation_events: list[dict[str, Any]],
    dt_ns: float | None = None,
    microstep_index: int = 0,
    microstep_count: int = 1,
    hamiltonian_pass_index: int = 0,
    trajectory_index: int | None = None,
    branch_ordinal: int | None = None,
    incoming_branch_weight: float | None = None,
) -> None:
    dt = float(substep["dt_ns"] if dt_ns is None else dt_ns)
    for term_index, term in enumerate(substep.get("terms", ())):
        if str(term["kind"]) != "hamiltonian":
            continue
        family = str(term["operator_family"]).upper()
        support = tuple(int(q) for q in term["support"])
        # Fail-closed (2026-06-30, 5-model review glm PT1, confirmed at runtime): this qt verification
        # executor lowers only ZZ/FSIM_PHASE/CTRL_*. Coherent COH_* families have NO apply branch here,
        # so accepting them in preflight and falling through would SILENTLY DROP
        # their evolution. Reject loudly rather than drop. (The MCWF carrier lowers COH_* via the
        # connected-cluster join; the qt path does not yet.)
        if family.startswith("COH_"):
            raise ValueError(
                f"qt executor cannot lower coherent family {family!r}: no COH_* apply path on the qt "
                "verification executor (would silently drop). Use the MCWF carrier for coherent terms."
            )
        if family in {"ZZ", "FSIM_PHASE"}:
            phase = np.exp(-1j * float(term["coefficient"]) * dt)
            gate = torch.diag(
                torch.tensor([1.0, 1.0, 1.0, phase], dtype=torch.complex128, device=device)
            )
            _apply_two_site_gate(
                mps,
                gate,
                support=support,
                substep=substep,
                term=term,
                term_index=term_index,
                branch_bits=branch_bits,
                device=device,
                max_bond=max_bond,
                dt_ns=dt,
                microstep_index=microstep_index,
                microstep_count=microstep_count,
                hamiltonian_pass_index=hamiltonian_pass_index,
                truncation_events=truncation_events,
                trajectory_index=trajectory_index,
                branch_ordinal=branch_ordinal,
                incoming_branch_weight=incoming_branch_weight,
            )
            continue
        if family.startswith("CTRL_"):
            gate_name = family.removeprefix("CTRL_")
            fraction = dt / float(substep["dt_ns"])
            if len(support) == 1:
                gate = torch.as_tensor(
                    _one_qubit_gate_matrix(gate_name),
                    dtype=torch.complex128,
                    device=device,
                )
                gate = _fractional_unitary(gate, fraction=fraction, device=device)
                mps.gate_(gate, where=support[0], contract=True)
                continue
            gate = _fractional_unitary(
                _two_qubit_gate_matrix(gate_name, device=device),
                fraction=fraction,
                device=device,
            )
            _apply_two_site_gate(
                mps,
                gate,
                support=support,
                substep=substep,
                term=term,
                term_index=term_index,
                branch_bits=branch_bits,
                device=device,
                max_bond=max_bond,
                dt_ns=dt,
                microstep_index=microstep_index,
                microstep_count=microstep_count,
                hamiltonian_pass_index=hamiltonian_pass_index,
                truncation_events=truncation_events,
                trajectory_index=trajectory_index,
                branch_ordinal=branch_ordinal,
                incoming_branch_weight=incoming_branch_weight,
            )


def _apply_two_site_gate(
    mps,
    gate: torch.Tensor,
    *,
    support: tuple[int, ...],
    substep: dict[str, Any],
    term: dict[str, Any],
    term_index: int,
    branch_bits: tuple[int, ...],
    device: str,
    max_bond: int | None,
    dt_ns: float,
    microstep_index: int,
    microstep_count: int,
    truncation_events: list[dict[str, Any]],
    hamiltonian_pass_index: int = 0,
    trajectory_index: int | None = None,
    branch_ordinal: int | None = None,
    incoming_branch_weight: float | None = None,
) -> None:
    if len(support) != 2:
        raise ValueError(f"restricted QT/MPS expected a two-site support, got {support!r}")
    if max_bond is not None:
        candidate, event = apply_capped_two_site_unitary(
            mps,
            gate,
            support=(int(support[0]), int(support[1])),
            max_bond=max_bond,
            context={
                "substep_id": str(substep["substep_id"]),
                "substep_kind": str(substep["substep_kind"]),
                "term_index": int(term_index),
                "operator_family": str(term["operator_family"]),
                "branch_record_prefix": list(branch_bits),
                "trajectory_index": (
                    None if trajectory_index is None else int(trajectory_index)
                ),
                "branch_ordinal": (
                    None if branch_ordinal is None else int(branch_ordinal)
                ),
                "incoming_branch_weight": (
                    None
                    if incoming_branch_weight is None
                    else float(incoming_branch_weight)
                ),
                "array_backend": f"torch_{device}_complex128",
                "dt_ns_effective": float(dt_ns),
                "microstep_index": int(microstep_index),
                "microstep_count": int(microstep_count),
                "hamiltonian_pass_index": int(hamiltonian_pass_index),
                "epistemic_class": "c",
            },
        )
        event["ledger_method"] = "quimb_actual_svd_split_per_two_site_unitary_gate"
        event["discarded_weight_sum"] = float(
            event["actual_discarded_weight_fraction_sum"]
        )
        event["worst_cut_discarded_weight"] = float(
            event["worst_actual_discarded_weight_fraction"]
        )
        event["discarded_weight_units"] = "fraction_of_pre_split_weight"
        event["compatibility_aliases"] = {
            "discarded_weight_sum": "actual_discarded_weight_fraction_sum",
            "worst_cut_discarded_weight": "worst_actual_discarded_weight_fraction",
        }
        event["n_truncated_cuts"] = sum(
            1
            for record in event["split_records"]
            if float(record["actual_discarded_weight_raw"]) > 0.0
        )
        commit_mps_candidate_(mps, candidate)
        truncation_events.append(event)
        return
    mps.gate_(
        gate,
        where=support,
        contract="auto-mps",
        max_bond=None,
        cutoff=0.0,
    )


def _evolve_branches(
    branches: list[tuple[tuple[int, ...], float, Any]],
    substep: dict[str, Any],
    *,
    device: str,
    max_bond: int | None,
    max_branches: int,
    microstep_count: int,
    finite_step_order: str,
    truncation_events: list[dict[str, Any]],
) -> list[tuple[tuple[int, ...], float, Any]]:
    step_order = _normalize_finite_step_order(finite_step_order)
    evolved = [(bits, weight, mps.copy()) for bits, weight, mps in branches]
    dt_micro = float(substep["dt_ns"]) / float(microstep_count)
    for microstep_index in range(int(microstep_count)):
        if step_order == _FINITE_STEP_ORDER_STRANG:
            evolved = _apply_hamiltonian_to_branches(
                evolved,
                substep,
                device=device,
                max_bond=max_bond,
                dt_ns=0.5 * dt_micro,
                microstep_index=microstep_index,
                microstep_count=int(microstep_count),
                hamiltonian_pass_index=0,
                truncation_events=truncation_events,
            )
            evolved = _apply_collapse_terms_to_branches(
                evolved,
                substep,
                device=device,
                max_branches=max_branches,
                dt_ns=dt_micro,
            )
            evolved = _apply_hamiltonian_to_branches(
                evolved,
                substep,
                device=device,
                max_bond=max_bond,
                dt_ns=0.5 * dt_micro,
                microstep_index=microstep_index,
                microstep_count=int(microstep_count),
                hamiltonian_pass_index=1,
                truncation_events=truncation_events,
            )
            continue
        evolved = _apply_hamiltonian_to_branches(
            evolved,
            substep,
            device=device,
            max_bond=max_bond,
            dt_ns=dt_micro,
            microstep_index=microstep_index,
            microstep_count=int(microstep_count),
            hamiltonian_pass_index=0,
            truncation_events=truncation_events,
        )
        evolved = _apply_collapse_terms_to_branches(
            evolved,
            substep,
            device=device,
            max_branches=max_branches,
            dt_ns=dt_micro,
        )
    return evolved


def _substep_has_evolution_terms(substep: dict[str, Any]) -> bool:
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        if kind == "hamiltonian":
            return True
        if kind == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0:
            return True
    return False


def _reset_branches_for_operations(
    branches: list[tuple[tuple[int, ...], float, Any]],
    substep: dict[str, Any],
    *,
    device: str,
    max_branches: int,
) -> list[tuple[tuple[int, ...], float, Any]]:
    evolved = list(branches)
    for op in substep.get("operation_records", ()):
        basis = axis1_reset_basis(str(op.get("name", "")))
        if basis is None:
            raise ValueError(f"unsupported restricted QT/MPS reset operation {op!r}")
        for target in op.get("targets", ()):
            next_branches: list[tuple[tuple[int, ...], float, Any]] = []
            for bits, weight, mps in evolved:
                for (
                    outcome_bit,
                    reset_state,
                    probability,
                    partition_total,
                ) in _reset_target_branches(
                    mps,
                    target=int(target),
                    basis=basis,
                    device=device,
                ):
                    next_branches.append(
                        (
                            bits,
                            _qt_exact_conditioned_branch_weight(
                                weight,
                                probability,
                                partition_total,
                                name="QT exact reset branch mass",
                            ),
                            reset_state,
                        )
                    )
                    if len(next_branches) > int(max_branches):
                        raise ValueError("restricted QT/MPS branch cap exceeded")
            evolved = next_branches
    return evolved


def _sample_reset_for_operations(
    mps,
    substep: dict[str, Any],
    *,
    device: str,
    generator: torch.Generator,
):
    state = mps
    for op in substep.get("operation_records", ()):
        basis = axis1_reset_basis(str(op.get("name", "")))
        if basis is None:
            raise ValueError(f"unsupported restricted QT/MPS reset operation {op!r}")
        for target in op.get("targets", ()):
            branches = _reset_target_branches(
                state,
                target=int(target),
                basis=basis,
                device=device,
            )
            probabilities = [
                float(probability)
                for _bit, _state, probability, _partition_total in branches
            ]
            mass = _require_qt_unit_probability_mass(
                probabilities,
                name="QT sampled reset partition",
            )
            index = sample_raw_probability_mass(
                mass,
                device=device,
                generator=generator,
            )
            state = branches[index][1]
    return state


def _reset_target_branches(
    mps,
    *,
    target: int,
    basis: str,
    device: str,
) -> list[tuple[int, Any, float, float]]:
    rotated = mps.copy()
    pre = _reset_pre_rotation(basis, device=device)
    if pre is not None:
        rotated.gate_(pre, where=int(target), contract=True)
    candidates: list[tuple[int, Any]] = []
    raw_probabilities: list[float] = []
    for bit in (0, 1):
        projected, probability = _project_z_mps(
            rotated,
            targets=[int(target)],
            outcome_bits=[bit],
            device=device,
        )
        candidates.append((bit, projected))
        raw_probabilities.append(float(probability))
    mass = _require_qt_unit_probability_mass(
        raw_probabilities,
        name="QT reset projective partition",
    )
    out: list[tuple[int, Any, float, float]] = []
    for candidate_index in mass.positive_indices:
        bit, projected = candidates[candidate_index]
        if bit == 1:
            projected.gate_(_one_qubit_torch_gate("X", device=device), where=int(target), contract=True)
        if pre is not None:
            projected.gate_(
                pre.conj().transpose(-1, -2),
                where=int(target),
                contract=True,
            )
        out.append(
            (
                bit,
                projected,
                mass.values[candidate_index],
                mass.total,
            )
        )
    return out


def _apply_z_measurement_reset_if_requested(
    mps,
    boundary: Axis1MeasurementBoundaryLayout,
    *,
    outcome_bits: list[int],
    device: str,
):
    if len(outcome_bits) != boundary.width:
        raise ValueError("QT/MPS measurement outcome width does not match Record boundary")
    reset = mps
    for target, bit, basis, requested in zip(
        boundary.targets,
        outcome_bits,
        boundary.bases,
        boundary.reset_after,
        strict=True,
    ):
        if not requested:
            continue
        if str(basis).upper() != "Z":
            raise ValueError("restricted QT/MPS measurement reset supports Z basis only")
        if int(bit) == 1:
            reset.gate_(_one_qubit_torch_gate("X", device=device), where=int(target), contract=True)
    return reset


def _reset_pre_rotation(basis: str, *, device: str) -> torch.Tensor | None:
    b = str(basis).upper()
    if b == "Z":
        return None
    if b == "X":
        return _one_qubit_torch_gate("H", device=device)
    if b == "Y":
        return _one_qubit_torch_gate("H", device=device) @ _one_qubit_torch_gate(
            "S_DAG",
            device=device,
        )
    raise ValueError(f"unsupported restricted QT/MPS reset basis {basis!r}")


def _one_qubit_torch_gate(gate: str, *, device: str) -> torch.Tensor:
    return torch.as_tensor(
        _one_qubit_gate_matrix(gate),
        dtype=torch.complex128,
        device=device,
    )


def _apply_hamiltonian_to_branches(
    branches: list[tuple[tuple[int, ...], float, Any]],
    substep: dict[str, Any],
    *,
    device: str,
    max_bond: int | None,
    dt_ns: float,
    microstep_index: int,
    microstep_count: int,
    hamiltonian_pass_index: int,
    truncation_events: list[dict[str, Any]],
) -> list[tuple[tuple[int, ...], float, Any]]:
    evolved: list[tuple[tuple[int, ...], float, Any]] = []
    for branch_ordinal, (bits, weight, mps) in enumerate(branches):
        out = mps.copy()
        _apply_hamiltonian_terms(
            out,
            substep,
            device=device,
            max_bond=max_bond,
            branch_bits=bits,
            truncation_events=truncation_events,
            dt_ns=dt_ns,
            microstep_index=microstep_index,
            microstep_count=int(microstep_count),
            hamiltonian_pass_index=int(hamiltonian_pass_index),
            branch_ordinal=branch_ordinal,
            incoming_branch_weight=float(weight),
        )
        evolved.append((bits, weight, out))
    return evolved


def _apply_collapse_terms_to_branches(
    branches: list[tuple[tuple[int, ...], float, Any]],
    substep: dict[str, Any],
    *,
    device: str,
    max_branches: int,
    dt_ns: float,
) -> list[tuple[tuple[int, ...], float, Any]]:
    evolved = list(branches)
    for term in substep.get("terms", ()):
        if str(term["kind"]) != "collapse":
            continue
        next_branches: list[tuple[tuple[int, ...], float, Any]] = []
        for bits, weight, mps in evolved:
            candidates: list[Any] = []
            raw_probabilities: list[float] = []
            for kraus in _collapse_kraus(term, dt_ns, device=device):
                branched = mps.copy()
                support = tuple(int(q) for q in term["support"])
                branched.gate_(kraus, where=support[0], contract=True)
                probability = mps_norm_squared(branched)
                candidates.append(branched)
                raw_probabilities.append(float(probability))
            mass = _require_qt_unit_probability_mass(
                raw_probabilities,
                name="QT exact Kraus partition",
            )
            for candidate_index in mass.positive_indices:
                branched = candidates[candidate_index]
                probability = mass.values[candidate_index]
                branched.multiply_(1.0 / (probability**0.5), spread_over=1)
                next_branches.append(
                    (
                        bits,
                        _qt_exact_conditioned_branch_weight(
                            weight,
                            probability,
                            mass.total,
                            name="QT exact Kraus branch mass",
                        ),
                        branched,
                    )
                )
                if len(next_branches) > int(max_branches):
                    raise ValueError("restricted QT/MPS branch cap exceeded")
        evolved = next_branches
    return evolved


def _sample_collapse_terms(
    mps,
    substep: dict[str, Any],
    *,
    device: str,
    generator: torch.Generator,
    dt_ns: float | None = None,
) -> tuple[Any, int]:
    state = mps
    sampled_count = 0
    for term in substep.get("terms", ()):
        if str(term["kind"]) != "collapse":
            continue
        kraus_ops = _collapse_kraus(
            term,
            float(substep["dt_ns"] if dt_ns is None else dt_ns),
            device=device,
        )
        candidates: list[Any] = []
        probabilities: list[float] = []
        support = tuple(int(q) for q in term["support"])
        for kraus in kraus_ops:
            branched = state.copy()
            branched.gate_(kraus, where=support[0], contract=True)
            probability = mps_norm_squared(branched)
            candidates.append(branched)
            probabilities.append(float(probability))
        mass = _require_qt_unit_probability_mass(
            probabilities,
            name="QT sampled Kraus partition",
        )
        index = sample_raw_probability_mass(
            mass,
            device=device,
            generator=generator,
        )
        selected = candidates[index]
        selected.multiply_(1.0 / (mass.values[index] ** 0.5), spread_over=1)
        state = selected
        if len(kraus_ops) > 1:
            sampled_count += 1
    return state, sampled_count


def _sample_z_measurement(
    mps,
    *,
    targets: list[int],
    device: str,
    generator: torch.Generator,
) -> tuple[list[int], Any]:
    state = mps
    sampled_bits: list[int] = []
    for target in targets:
        candidates: list[Any] = []
        probabilities: list[float] = []
        for bit in (0, 1):
            projected, probability = _project_z_mps(
                state,
                targets=[int(target)],
                outcome_bits=[bit],
                device=device,
            )
            candidates.append(projected)
            probabilities.append(float(probability))
        mass = _require_qt_unit_probability_mass(
            probabilities,
            name="QT conditional single-site measurement partition",
        )
        bit = sample_raw_probability_mass(
            mass,
            device=device,
            generator=generator,
        )
        sampled_bits.append(int(bit))
        state = candidates[bit]
    return sampled_bits, state


def _sample_index(
    probabilities: list[float],
    *,
    device: str,
    generator: torch.Generator,
) -> int:
    mass = validate_raw_probability_mass(
        probabilities,
        name="categorical candidate probabilities",
    )
    return sample_raw_probability_mass(mass, device=device, generator=generator)


def _collapse_kraus(
    term: dict[str, Any],
    dt_ns: float,
    *,
    device: str,
) -> tuple[torch.Tensor, ...]:
    family = str(term["operator_family"]).upper()
    coeff = abs(float(term["coefficient"]))
    if coeff == 0.0:
        return (torch.eye(2, dtype=torch.complex128, device=device),)
    rate = multiply_probability_values(coeff, coeff, name=f"{family} rate")
    if family in {"T1", "T1_UP"}:
        exponent = multiply_probability_values(
            rate,
            float(dt_ns),
            name=f"{family} rate-duration exponent",
        )
        p = one_minus_exp_neg_probability(exponent, name=f"{family} decay")
        if family == "T1":
            return (
                torch.tensor(
                    [[1.0, 0.0], [0.0, np.sqrt(1.0 - p)]],
                    dtype=torch.complex128,
                    device=device,
                ),
                torch.tensor(
                    [[0.0, np.sqrt(p)], [0.0, 0.0]],
                    dtype=torch.complex128,
                    device=device,
                ),
            )
        return (
            torch.tensor(
                [[np.sqrt(1.0 - p), 0.0], [0.0, 1.0]],
                dtype=torch.complex128,
                device=device,
            ),
            torch.tensor(
                [[0.0, 0.0], [np.sqrt(p), 0.0]],
                dtype=torch.complex128,
                device=device,
            ),
        )
    if family in {"T2", "RD"}:
        gamma = multiply_probability_values(0.5, rate, name=f"{family} gamma")
        exponent = multiply_probability_values(
            gamma,
            float(dt_ns),
            name=f"{family} rate-duration exponent",
        )
        decay = one_minus_exp_neg_probability(exponent, name=f"{family} decay")
        p = multiply_probability_values(0.5, decay, name=f"{family} branch mass")
        return (
            np.sqrt(1.0 - p) * torch.eye(2, dtype=torch.complex128, device=device),
            np.sqrt(p)
            * torch.diag(
                torch.tensor([1.0, -1.0], dtype=torch.complex128, device=device)
            ),
        )
    raise ValueError(f"unsupported restricted QT/MPS collapse family {family!r}")


@lru_cache(maxsize=None)
def _cached_two_qubit_gate_matrix_numpy(name: str) -> np.ndarray:
    """Build one bounded, CPU-only Stim tableau matrix per gate name."""

    import stim

    circuit = stim.Circuit(f"{name} 0 1")
    matrix = np.asarray(
        circuit.to_tableau().to_unitary_matrix(endian="big"),
        dtype=np.complex128,
    )
    matrix.setflags(write=False)
    return matrix


def _two_qubit_gate_matrix(gate: str, *, device: str) -> torch.Tensor:
    name = str(gate).upper()
    if name not in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES:
        raise ValueError(f"unsupported two-qubit QT/MPS control gate {gate!r}")
    # Copy before conversion: callers receive independent mutable tensors while
    # the tiny cache retains no Torch or CUDA allocation and cannot be corrupted.
    matrix = np.array(
        _cached_two_qubit_gate_matrix_numpy(name),
        dtype=np.complex128,
        copy=True,
    )
    return torch.as_tensor(
        matrix,
        dtype=torch.complex128,
        device=device,
    )


def _fractional_unitary(
    unitary: torch.Tensor,
    *,
    fraction: float,
    device: str,
) -> torch.Tensor:
    f = float(fraction)
    if abs(f - 1.0) <= 1.0e-15:
        return torch.as_tensor(unitary, dtype=torch.complex128, device=device)
    u = torch.as_tensor(unitary, dtype=torch.complex128, device=device)
    eigvals, eigvecs = torch.linalg.eig(u)
    angles = torch.angle(eigvals).to(torch.float64)
    fractional = torch.exp(1j * f * angles).to(torch.complex128)
    out = eigvecs @ torch.diag(fractional) @ torch.linalg.inv(eigvecs)
    return out.to(dtype=torch.complex128, device=device)


def _project_z_mps(
    mps,
    *,
    targets: list[int],
    outcome_bits: list[int],
    device: str,
) -> tuple[Any, float]:
    projected = mps.copy()
    for target, bit in zip(targets, outcome_bits, strict=True):
        projected.gate_(_z_projector(int(bit), device=device), where=int(target), contract=True)
    norm = mps_norm_squared(projected)
    mass = validate_raw_probability_mass((norm,), name="QT projective branch norm")
    norm = mass.values[0]
    if norm == 0.0:
        return projected, 0.0
    projected.multiply_(1.0 / (norm**0.5), spread_over=1)
    return projected, float(norm)


def _z_projector(bit: int, *, device: str) -> torch.Tensor:
    if int(bit) == 0:
        return torch.diag(torch.tensor([1.0, 0.0], dtype=torch.complex128, device=device))
    if int(bit) == 1:
        return torch.diag(torch.tensor([0.0, 1.0], dtype=torch.complex128, device=device))
    raise ValueError(f"invalid Z branch bit {bit!r}")


def _measurement_records(num_targets: int) -> list[list[int]]:
    return [list(record) for record in materialize_binary_records(int(num_targets))]


def _one_qubit_gate_matrix(gate: str) -> np.ndarray:
    inv_sqrt2 = 1.0 / np.sqrt(2.0)
    g = str(gate).upper()
    if g in {"H", "H_XZ"}:
        return inv_sqrt2 * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
    if g == "H_XY":
        return np.array([[0.0, 1.0], [1.0j, 0.0]], dtype=np.complex128)
    if g == "C_XYZ":
        return inv_sqrt2 * np.array([[1.0, -1.0j], [1.0, 1.0j]], dtype=np.complex128)
    if g == "C_ZYX":
        return inv_sqrt2 * np.array([[1.0, 1.0], [1.0j, -1.0j]], dtype=np.complex128)
    if g == "X":
        return np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    if g == "Y":
        return np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
    if g == "Z":
        return np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    if g in {"S", "SQRT_Z"}:
        return np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128)
    if g in {"S_DAG", "SQRT_Z_DAG"}:
        return np.array([[1.0, 0.0], [0.0, -1.0j]], dtype=np.complex128)
    if g == "SQRT_X":
        return inv_sqrt2 * np.array([[1.0, -1.0j], [-1.0j, 1.0]], dtype=np.complex128)
    if g == "SQRT_X_DAG":
        return inv_sqrt2 * np.array([[1.0, 1.0j], [1.0j, 1.0]], dtype=np.complex128)
    if g == "SQRT_Y":
        return inv_sqrt2 * np.array([[1.0, -1.0], [1.0, 1.0]], dtype=np.complex128)
    if g == "SQRT_Y_DAG":
        return inv_sqrt2 * np.array([[1.0, 1.0], [-1.0, 1.0]], dtype=np.complex128)
    raise ValueError(f"unsupported one-qubit QT/MPS control gate {gate!r}")


def _program_summary(program: dict[str, Any]) -> dict[str, Any]:
    substeps = list(program.get("program", {}).get("substeps", ()))
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": bool(program.get("requires_scalable_backend")),
        "routes": sorted({str(step.get("route")) for step in substeps}),
        "substep_count": len(substeps),
    }


def _stable_payload_hash(payload: dict[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    data = json.dumps(
        without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


__all__ = [
    "AXIS1_QT_MPS_BOND_SWEEP_SCHEMA",
    "AXIS1_QT_MPS_RESTRICTED_EVIDENCE_BUNDLE_SCHEMA",
    "AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY",
    "AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA",
    "AXIS1_QT_MPS_RESOURCE_PROBE_SCHEMA",
    "AXIS1_QT_MPS_TRAJECTORY_SWEEP_SCHEMA",
    "axis1_qt_mps_bond_sweep_manifest",
    "axis1_qt_mps_restricted_evidence_bundle_manifest",
    "axis1_qt_mps_restricted_execution_manifest",
    "axis1_qt_mps_resource_probe_manifest",
    "axis1_qt_mps_trajectory_seed_sweep_manifest",
]

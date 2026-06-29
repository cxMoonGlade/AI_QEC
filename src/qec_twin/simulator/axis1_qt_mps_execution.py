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
from typing import Any

import numpy as np
import torch

from qec_twin.simulator.analog_schedule import SubstepSchedule
from qec_twin.simulator.axis1_carrier_program import axis1_carrier_program_manifest
from qec_twin.simulator.axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_qt_mps_contract import (
    AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT,
)
from qec_twin.simulator.axis1_record_evidence import (
    axis1_measurement_record_evidence_manifest,
)
from qec_twin.simulator.axis1_selection import (
    AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES,
)
from qec_twin.simulator.axis1_state_evidence import _require_cuda_device


AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA = (
    "qec_twin.simulator.axis1_qt_mps_restricted_execution.v1"
)
AXIS1_QT_MPS_BOND_SWEEP_SCHEMA = "qec_twin.simulator.axis1_qt_mps_bond_sweep.v1"
AXIS1_QT_MPS_TRAJECTORY_SWEEP_SCHEMA = (
    "qec_twin.simulator.axis1_qt_mps_trajectory_seed_sweep.v1"
)
AXIS1_QT_MPS_RESTRICTED_EVIDENCE_BUNDLE_SCHEMA = (
    "qec_twin.simulator.axis1_qt_mps_restricted_evidence_bundle.v1"
)
AXIS1_QT_MPS_RESOURCE_PROBE_SCHEMA = (
    "qec_twin.simulator.axis1_qt_mps_resource_probe.v1"
)
AXIS1_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY = (
    "axis1_qt_mps_restricted_control_hamiltonian_z_record_product_channel"
)
AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT = "qt_mps_state_record"
_FINITE_STEP_ORDER_FIRST = "first_order"
_FINITE_STEP_ORDER_STRANG = "strang_second_order"
_FINITE_STEP_ORDERS = (_FINITE_STEP_ORDER_FIRST, _FINITE_STEP_ORDER_STRANG)
_TOTAL_PROBABILITY_RESIDUAL_GATE = 1.0e-8


def _exact_bond_dimension_sufficient(num_sites: int) -> int:
    """Conservative sufficient bond cap for exact qubit-MPS representation."""

    return int(2 ** ((int(num_sites) + 1) // 2))


def _normalize_finite_step_order(value: str) -> str:
    order = str(value)
    if order not in _FINITE_STEP_ORDERS:
        allowed = ", ".join(_FINITE_STEP_ORDERS)
        raise ValueError(f"finite_step_order must be one of: {allowed}")
    return order


def _finite_step_policy_name(finite_step_order: str) -> str:
    order = _normalize_finite_step_order(finite_step_order)
    if order == _FINITE_STEP_ORDER_STRANG:
        return "strang_hamiltonian_collapse_product_formula_v1"
    return "operator_family_product_formula_v1"


def axis1_qt_mps_restricted_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    max_bond: int | None = None,
    max_branches: int = 4096,
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
    trajectory_count: int | None = None,
    rng_seed: int | None = None,
    dense_oracle_certification: bool = True,
) -> dict[str, Any]:
    """Execute the currently supported QT/MPS slice for an Axis-1 schedule."""

    dev = _require_cuda_device(device)
    if int(microstep_count) <= 0:
        raise ValueError("microstep_count must be positive")
    if int(max_branches) <= 0:
        raise ValueError("max_branches must be positive")
    if max_bond is not None and int(max_bond) <= 0:
        raise ValueError("max_bond must be positive when provided")
    step_order = _normalize_finite_step_order(finite_step_order)
    finite_step_policy = _finite_step_policy_name(step_order)
    if trajectory_count is not None and int(trajectory_count) <= 0:
        raise ValueError("trajectory_count must be positive when provided")
    if (
        worst_cut_discarded_weight_gate is not None
        and float(worst_cut_discarded_weight_gate) < 0.0
    ):
        raise ValueError("worst_cut_discarded_weight_gate must be nonnegative")
    if (
        total_discarded_weight_gate is not None
        and float(total_discarded_weight_gate) < 0.0
    ):
        raise ValueError("total_discarded_weight_gate must be nonnegative")
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT,
    )
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
        "max_branches": int(max_branches),
        "microstep_count": int(microstep_count),
        "finite_step_order": step_order,
        "trajectory_count": None if trajectory_count is None else int(trajectory_count),
        "rng_seed": None if rng_seed is None else int(rng_seed),
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
        "dense_oracle_certification_requested": bool(dense_oracle_certification),
        "claims_qt_mps_backend_execution": True,
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": (
            "restricted QT/MPS execution is a verification gate only; no new "
            "scored quantity"
        ),
        "approximation_book": {
            "schema": "qec_twin.simulator.axis1_qt_mps_restricted_approximation_book.v1",
            "hamiltonian_product_formula": {
                "status": "operator_family_order_product_formula",
                "finite_step_policy": finite_step_policy,
                "finite_step_order": step_order,
                "microstep_count": int(microstep_count),
                "exact_joint_generator_claim": False,
                "epistemic_class": "c",
            },
            "collapse_terms": {
                "supported": "local_T1_T1_UP_T2_RD_product_channel_branches",
                "finite_step_policy": finite_step_policy,
                "finite_step_order": step_order,
                "microstep_count": int(microstep_count),
                "exact_summed_generator_claim": False,
                "epistemic_class": "c",
            },
            "mps_truncation": {
                "max_bond": None if max_bond is None else int(max_bond),
                "discarded_weight_ledger_complete": True,
                "ledger_policy": (
                    "complete_zero_ledger_when_no_explicit_truncation_requested"
                    if max_bond is None
                    else "cuda_shadow_state_schmidt_tail_per_two_site_gate"
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
                "gate_role": "heuristic_policy_gate_not_metric",
                "epistemic_class": "c",
            },
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
                "rng_seed_required_for_acceptance": bool(trajectory_count is not None),
                "rng_seed_was_explicit": bool(
                    trajectory_count is not None and rng_seed is not None
                ),
                "single_trajectory_density_claim": False,
                "epistemic_class": "c",
            },
        },
        "epistemic_classes": {
            "program_consumption": "a",
            "restricted_mps_execution": "c",
            "local_collapse_channel_forms": "a/c",
            "production_backend_status": "a",
        },
    }
    unsupported = _unsupported_substeps(program)
    if unsupported:
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "qt_mps_backend_executed": False,
            "blocked_reason": unsupported[0]["reason"],
            "blocked_substeps": unsupported,
            "mps_execution": None,
            "restricted_acceptance_policy": _blocked_restricted_acceptance_policy(
                blocked_reason=unsupported[0]["reason"],
                finite_step_order=step_order,
                finite_step_policy=finite_step_policy,
                microstep_count=int(microstep_count),
                trajectory_count=trajectory_count,
                max_bond=max_bond,
                worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
                total_discarded_weight_gate=total_discarded_weight_gate,
            ),
            "scope": (
                "restricted QT/MPS Hamiltonian/control/Z-record slice failed closed; "
                "unsupported Lindblad terms, non-Z measurements, two-qubit "
                "control families outside the frontend set, DEM/decoder semantics, "
                "and Axis-2 timelines are not implemented here"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    execution = (
        _execute_sampled_program(
            program,
            record_layout_ref=schedule.record_layout_ref,
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
            record_layout_ref=schedule.record_layout_ref,
            device=dev,
            max_bond=max_bond,
            max_branches=int(max_branches),
            microstep_count=int(microstep_count),
            finite_step_order=step_order,
        )
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
        certification=certification,
        finite_step_order=step_order,
        finite_step_policy=finite_step_policy,
        max_bond=max_bond,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    passed = bool(acceptance["accepted_for_restricted_execution"])
    payload = {
        **base,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "qt_mps_backend_executed": True,
        "blocked_reason": None,
        "blocked_substeps": [],
        "mps_execution": execution,
        "dense_jointL_record_certification": certification,
        "restricted_acceptance_policy": acceptance,
        "scope": (
            "restricted QT/MPS Hamiltonian/control/Z-record execution only; no "
            "nonzero exact summed-generator claim, no dense channel evidence, no "
            "DEM/decoder semantics, no Axis-2 source timeline, no production "
            "scalable backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qt_mps_bond_sweep_manifest(
    schedule: SubstepSchedule,
    *,
    bond_values: tuple[int, ...] | list[int],
    device: str = "cuda",
    max_branches: int = 4096,
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    convergence_record_probability_gate: float | None = None,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
    dense_oracle_certification: bool = True,
) -> dict[str, Any]:
    """Run a finite-bond convergence sweep for the restricted QT/MPS slice."""

    bonds = _normalize_bond_sweep_values(bond_values)
    if convergence_record_probability_gate is not None and float(
        convergence_record_probability_gate
    ) < 0.0:
        raise ValueError("convergence_record_probability_gate must be nonnegative")
    runs = [
        axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device=device,
            max_bond=bond,
            max_branches=max_branches,
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
    reference = runs[-1]
    comparison = _bond_sweep_comparison(
        runs,
        convergence_record_probability_gate=convergence_record_probability_gate,
    )
    reference_calibration = _bond_sweep_reference_calibration(reference)
    accepted = bool(
        comparison["convergence_gate"]["evaluated"]
        and comparison["convergence_gate"]["passed"]
        and reference_calibration["accepted_as_dense_calibrated_reference"]
        and reference["restricted_acceptance_policy"]["mps_truncation"][
            "accepted_as_exact_bond_representation"
        ]
    )
    payload = {
        "schema": AXIS1_QT_MPS_BOND_SWEEP_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "representability": (
            "axis1_qt_mps_restricted_finite_bond_convergence_sweep"
        ),
        "backend_contract": AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": str(device),
        "bond_values": list(bonds),
        "reference_bond": int(bonds[-1]),
        "microstep_count": int(microstep_count),
        "finite_step_order": _normalize_finite_step_order(finite_step_order),
        "convergence_policy": {
            **comparison,
            "reference_dense_calibration": reference_calibration,
            "accepted_as_restricted_convergence_evidence": accepted,
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "run_summaries": [_bond_sweep_run_summary(run) for run in runs],
        "claims_qt_mps_backend_execution": True,
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
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
    seed_record_frequency_spread_gate: float | None = None,
    dense_record_frequency_gate: float | None = None,
) -> dict[str, Any]:
    """Run explicit-seed sampled trajectory sweeps for restricted QT/MPS records."""

    seeds = _normalize_trajectory_sweep_seeds(rng_seeds)
    if int(trajectory_count) <= 0:
        raise ValueError("trajectory_count must be positive")
    if (
        seed_record_frequency_spread_gate is not None
        and float(seed_record_frequency_spread_gate) < 0.0
    ):
        raise ValueError("seed_record_frequency_spread_gate must be nonnegative")
    if dense_record_frequency_gate is not None and float(dense_record_frequency_gate) < 0.0:
        raise ValueError("dense_record_frequency_gate must be nonnegative")
    runs = [
        axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device=device,
            max_bond=max_bond,
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
        bool(
            run.get("restricted_acceptance_policy", {}).get(
                "accepted_for_sampled_execution_evidence", False
            )
        )
        for run in runs
    )
    accepted_restricted = bool(
        all_sampled_runs_accepted
        and seed_comparison["seed_spread_gate"]["evaluated"]
        and seed_comparison["seed_spread_gate"]["passed"]
    )
    accepted_dense = bool(
        dense_calibration["accepted_as_dense_calibrated_trajectory_evidence"]
    )
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
        "microstep_count": int(microstep_count),
        "finite_step_order": _normalize_finite_step_order(finite_step_order),
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
        "run_summaries": [_trajectory_seed_sweep_run_summary(run) for run in runs],
        "claims_qt_mps_backend_execution": True,
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
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    convergence_record_probability_gate: float | None = None,
    seed_record_frequency_spread_gate: float | None = None,
    dense_record_frequency_gate: float | None = None,
    worst_cut_discarded_weight_gate: float | None = None,
    total_discarded_weight_gate: float | None = None,
) -> dict[str, Any]:
    """Bundle finite-bond and trajectory seed-sweep gates for restricted QT/MPS."""

    bonds = _normalize_bond_sweep_values(bond_values)
    reference_bond = int(max(bonds))
    bond_sweep = axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=bonds,
        device=device,
        max_branches=max_branches,
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
        rng_seeds=rng_seeds,
        device=device,
        max_bond=reference_bond,
        microstep_count=microstep_count,
        finite_step_order=finite_step_order,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
        seed_record_frequency_spread_gate=seed_record_frequency_spread_gate,
        dense_record_frequency_gate=dense_record_frequency_gate,
    )
    bond_policy = bond_sweep["convergence_policy"]
    trajectory_policy = trajectory_sweep["seed_sweep_policy"]
    accepted_restricted = bool(
        bond_policy["accepted_as_restricted_convergence_evidence"]
        and trajectory_policy["accepted_as_restricted_seed_sweep_evidence"]
    )
    accepted_dense = bool(
        bond_policy["reference_dense_calibration"][
            "accepted_as_dense_calibrated_reference"
        ]
        and trajectory_policy["accepted_as_dense_calibrated_trajectory_evidence"]
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
        "reference_bond": reference_bond,
        "trajectory_count": int(trajectory_count),
        "rng_seeds": list(_normalize_trajectory_sweep_seeds(rng_seeds)),
        "microstep_count": int(microstep_count),
        "finite_step_order": _normalize_finite_step_order(finite_step_order),
        "bundle_policy": {
            "accepted_as_restricted_bundle_evidence": accepted_restricted,
            "accepted_as_dense_calibrated_bundle_evidence": accepted_dense,
            "accepted_as_production_error_bound": False,
            "accepted_for_production_scalable_backend": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "bond_sweep": _nested_evidence_summary(bond_sweep),
        "trajectory_seed_sweep": _nested_evidence_summary(trajectory_sweep),
        "claims_qt_mps_backend_execution": True,
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

    dev = _require_cuda_device(device)
    if min_peak_allocated_gib is not None and float(min_peak_allocated_gib) < 0.0:
        raise ValueError("min_peak_allocated_gib must be nonnegative")
    if min_peak_reserved_gib is not None and float(min_peak_reserved_gib) < 0.0:
        raise ValueError("min_peak_reserved_gib must be nonnegative")
    torch_dev = torch.device(dev)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(torch_dev)
    torch.cuda.synchronize(torch_dev)
    bundle = axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=bond_values,
        trajectory_count=trajectory_count,
        rng_seeds=rng_seeds,
        device=dev,
        max_branches=max_branches,
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
    passed = bool(bundle["passed"] and resource_policy["accepted_as_resource_probe"])
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
        "workload_schema": bundle["schema"],
        "workload_content_hash": bundle["content_hash"],
        "workload_passed": bool(bundle["passed"]),
        "resource_probe_policy": resource_policy,
        "claims_qt_mps_backend_execution": True,
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
    return payload


def _execute_program(
    program: dict[str, Any],
    *,
    record_layout_ref: dict[str, Any],
    device: str,
    max_bond: int | None,
    max_branches: int,
    microstep_count: int,
    finite_step_order: str,
) -> dict[str, Any]:
    import quimb.tensor as qtn

    step_order = _normalize_finite_step_order(finite_step_order)
    finite_step_policy = _finite_step_policy_name(step_order)
    num_qubits = int(program["program"]["num_qubits"])
    z0 = np.array([1.0, 0.0], dtype=np.complex128)
    initial = qtn.MPS_product_state([z0] * num_qubits)
    initial.apply_to_arrays(
        lambda x: torch.as_tensor(x, dtype=torch.complex128, device=device)
    )
    branches: list[tuple[tuple[int, ...], float, Any]] = [((), 1.0, initial)]
    applied: list[dict[str, Any]] = []
    truncation_events: list[dict[str, Any]] = []
    max_observed_bond = _max_branch_bond(branches)
    measurement_keys: list[str] = []
    measurement_targets: list[int] = []
    for substep in program["program"]["substeps"]:
        next_branches: list[tuple[tuple[int, ...], float, Any]] = []
        summary = _substep_summary(substep)
        if str(substep["substep_kind"]) == "reset":
            branches = _reset_branches_for_operations(
                branches,
                substep,
                device=device,
                max_branches=max_branches,
            )
            max_observed_bond = max(max_observed_bond, _max_branch_bond(branches))
            applied.append(
                {
                    **summary,
                    "finite_step_policy": "boundary_only_no_generator_evolution",
                    "reset_boundary_policy": "nonselective_pauli_reset_internal_branches_no_record",
                    "branch_count_after_substep": len(branches),
                    "max_observed_bond_after_substep": _max_branch_bond(branches),
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
            max_observed_bond = max(max_observed_bond, _max_branch_bond(branches))
            applied.append(
                {
                    **summary,
                    "finite_step_policy": finite_step_policy,
                    "finite_step_order": step_order,
                    "microstep_count": int(microstep_count),
                    "max_observed_bond_after_substep": _max_branch_bond(branches),
                }
            )
            continue

        boundary = _measurement_boundary(substep)
        measurement_keys.extend(boundary["measurement_keys"])
        measurement_targets.extend(boundary["measurement_targets"])
        outcomes = _measurement_records(len(boundary["measurement_targets"]))
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
            for outcome in outcomes:
                projected, probability = _project_z_mps(
                    evolved,
                    targets=boundary["measurement_targets"],
                    outcome_bits=outcome,
                    device=device,
                )
                if probability <= 1.0e-15:
                    continue
                projected = _apply_z_measurement_reset_if_requested(
                    projected,
                    substep,
                    outcome_bits=outcome,
                    device=device,
                )
                next_branches.append(
                    (
                        bits + tuple(int(bit) for bit in outcome),
                        weight * probability,
                        projected,
                    )
                )
                if len(next_branches) > int(max_branches):
                    raise ValueError("restricted QT/MPS branch cap exceeded")
        branches = next_branches
        max_observed_bond = max(max_observed_bond, _max_branch_bond(branches))
        applied.append(
            {
                **summary,
                "finite_step_policy": finite_step_policy,
                "finite_step_order": step_order,
                "microstep_count": int(microstep_count),
                "branch_count_after_substep": len(branches),
                "max_observed_bond_after_substep": _max_branch_bond(branches),
            }
        )

    probability_by_record: dict[tuple[int, ...], float] = {}
    for bits, weight, _mps in branches:
        probability_by_record[bits] = probability_by_record.get(bits, 0.0) + weight
    records = _measurement_records(len(measurement_keys)) if measurement_keys else [()]
    probabilities = [float(probability_by_record.get(tuple(record), 0.0)) for record in records]
    detector_records, detector_names = _xor_records(
        [list(record) for record in records],
        measurement_keys,
        record_layout_ref.get("detectors", ()),
    )
    logical_records, logical_names = _xor_records(
        [list(record) for record in records],
        measurement_keys,
        record_layout_ref.get("observables", ()),
    )
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
        "mps_truncation_ledger": _truncation_ledger(
            max_bond=max_bond,
            num_sites=num_qubits,
            max_observed_bond=max_observed_bond,
            truncation_events=truncation_events,
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
    record_layout_ref: dict[str, Any],
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
    truncation_events: list[dict[str, Any]] = []
    max_observed_bond = _max_branch_bond([((), 1.0, initial)])
    measurement_keys: list[str] = []
    measurement_targets: list[int] = []
    boundary_seen = False

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
                _max_branch_bond([(bits, 1.0, state)]),
            )
            if trajectory_index == 0:
                applied.append(
                    {
                        **_substep_summary(substep),
                        "finite_step_policy": finite_step_policy,
                        "finite_step_order": step_order,
                        "microstep_count": int(microstep_count),
                        "sampled_trajectory_count": ntraj,
                        "sampled_collapse_term_count": collapse_count,
                        "max_observed_bond_after_substep": _max_branch_bond(
                            [(bits, 1.0, state)]
                        ),
                    }
                )
            else:
                applied[substep_index]["sampled_collapse_term_count"] = max(
                    int(applied[substep_index]["sampled_collapse_term_count"]),
                    int(collapse_count),
                )
                applied[substep_index]["max_observed_bond_after_substep"] = max(
                    int(applied[substep_index]["max_observed_bond_after_substep"]),
                    _max_branch_bond([(bits, 1.0, state)]),
                )
            if str(substep["substep_kind"]) != "measurement":
                continue
            boundary = _measurement_boundary(substep)
            if not boundary_seen:
                measurement_keys.extend(boundary["measurement_keys"])
                measurement_targets.extend(boundary["measurement_targets"])
                boundary_seen = True
            outcome, state = _sample_z_measurement(
                state,
                targets=boundary["measurement_targets"],
                device=device,
                generator=generator,
            )
            state = _apply_z_measurement_reset_if_requested(
                state,
                substep,
                outcome_bits=outcome,
                device=device,
            )
            bits = bits + tuple(int(bit) for bit in outcome)
        records_by_bits[bits] = records_by_bits.get(bits, 0) + 1

    records = _measurement_records(len(measurement_keys)) if measurement_keys else [()]
    record_counts = [int(records_by_bits.get(tuple(record), 0)) for record in records]
    probabilities = [float(count) / float(ntraj) for count in record_counts]
    detector_records, detector_names = _xor_records(
        [list(record) for record in records],
        measurement_keys,
        record_layout_ref.get("detectors", ()),
    )
    logical_records, logical_names = _xor_records(
        [list(record) for record in records],
        measurement_keys,
        record_layout_ref.get("observables", ()),
    )
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
        "mps_truncation_ledger": _truncation_ledger(
            max_bond=max_bond,
            num_sites=num_qubits,
            max_observed_bond=max_observed_bond,
            truncation_events=truncation_events,
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
    if bool(program["requires_scalable_backend"]):
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
    dense_record = dense["record_evidence"]
    dense_probs = [float(x) for x in dense_record["record_probabilities"]]
    mps_probs = [float(x) for x in execution["record_probabilities"]]
    if dense_record["measurement_records"] != execution["measurement_records"]:
        return {
            "executed": True,
            "passed": False,
            "reason": "measurement_record_order_mismatch",
            "dense_evidence_schema": dense["schema"],
            "dense_evidence_content_hash": dense["content_hash"],
            "comparison_outcome_is_metric": False,
        }
    residual = max(
        (abs(a - b) for a, b in zip(dense_probs, mps_probs, strict=True)),
        default=0.0,
    )
    threshold = 1.0e-8
    return {
        "executed": True,
        "passed": bool(residual <= threshold),
        "dense_evidence_schema": dense["schema"],
        "dense_evidence_content_hash": dense["content_hash"],
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
    max_bond: int | None,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
) -> dict[str, Any]:
    truncation_gate = _truncation_gate_result(
        {
            "explicit_truncation_requested": max_bond is not None,
            "discarded_weight_sum": 0.0,
            "worst_cut_discarded_weight": 0.0,
        },
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    return {
        "schema": "qec_twin.simulator.axis1_qt_mps_restricted_acceptance_policy.v1",
        "policy_role": "restricted_execution_acceptance_not_metric",
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
    certification: dict[str, Any],
    finite_step_order: str,
    finite_step_policy: str,
    max_bond: int | None,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
) -> dict[str, Any]:
    step_order = _normalize_finite_step_order(finite_step_order)
    sampling = execution["trajectory_sampling"]
    mode = str(sampling["mode"])
    exact_branch_enumeration = mode == "exact_branch_enumeration"
    sampled_trajectories = mode == "sampled_product_channel_trajectories"
    rng_seed_was_explicit = bool(sampling.get("rng_seed_was_explicit", False))
    requires_scalable = bool(program["requires_scalable_backend"])
    residual_ok = bool(
        float(execution["total_probability_residual"])
        <= _TOTAL_PROBABILITY_RESIDUAL_GATE
    )
    dense_executed = bool(certification.get("executed", False))
    dense_passed = bool(certification.get("passed", False))
    dense_status = _dense_certification_status(certification)
    exact_dense_probability_evidence = bool(
        exact_branch_enumeration and dense_executed and dense_passed and not requires_scalable
    )
    restricted_overcap_execution = bool(
        requires_scalable and residual_ok and exact_branch_enumeration
    )
    sampled_execution = bool(sampled_trajectories and residual_ok and rng_seed_was_explicit)
    accepted_restricted = bool(
        residual_ok
        and (
            exact_dense_probability_evidence
            or restricted_overcap_execution
            or sampled_execution
            or dense_status == "not_applicable_no_measurement_records"
        )
    )
    ledger = execution["mps_truncation_ledger"]
    explicit_truncation = bool(ledger["explicit_truncation_requested"])
    discarded_sum = float(ledger["discarded_weight_sum"])
    truncation_detected = bool(discarded_sum > 0.0)
    truncation_gate = _truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    truncation_gate_failed = bool(
        truncation_gate["evaluated"] and not truncation_gate["passed"]
    )
    finite_bond_candidate = bool(
        explicit_truncation and truncation_gate["evaluated"] and truncation_gate["passed"]
    )
    if truncation_gate_failed:
        accepted_restricted = False
    production_blockers = [
        "production_error_control_policy_not_established",
        "large_code_acceptance_not_established",
    ]
    if not exact_dense_probability_evidence and not requires_scalable:
        production_blockers.append(f"dense_window_certification:{dense_status}")
    if requires_scalable:
        production_blockers.append("overcap_large_code_policy_not_established")
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
    return {
        "schema": "qec_twin.simulator.axis1_qt_mps_restricted_acceptance_policy.v1",
        "policy_role": "restricted_execution_acceptance_not_metric",
        "accepted_for_restricted_execution": accepted_restricted,
        "accepted_for_exact_dense_probability_evidence": exact_dense_probability_evidence,
        "accepted_for_sampled_execution_evidence": sampled_execution,
        "accepted_for_production_scalable_backend": False,
        "total_probability_residual_gate": _TOTAL_PROBABILITY_RESIDUAL_GATE,
        "total_probability_residual_gate_epistemic_class": "c",
        "finite_step": {
            "order": step_order,
            "policy": str(finite_step_policy),
            "microstep_count": int(execution["finite_step_policy"]["microstep_count"]),
            "dense_window_certification_status": dense_status,
            "dense_window_certification_executed": dense_executed,
            "dense_window_certification_passed": dense_passed if dense_executed else None,
            "exact_summed_lindbladian_claim": False,
            "comparison_outcome_is_metric": bool(
                certification.get("comparison_outcome_is_metric", False)
            ),
            "epistemic_class": "c",
        },
        "trajectory": {
            "mode": mode,
            "trajectory_count": sampling["trajectory_count"],
            "rng_seed": sampling["rng_seed"],
            "rng_seed_required_for_acceptance": bool(
                sampling.get("rng_seed_required_for_acceptance", sampled_trajectories)
            ),
            "rng_seed_was_explicit": rng_seed_was_explicit,
            "accepted_as_exact_probability_evidence": exact_dense_probability_evidence,
            "accepted_as_empirical_record_evidence": sampled_execution,
            "single_trajectory_density_claim": False,
            "comparison_outcome_is_metric": bool(
                sampling.get("comparison_outcome_is_metric", False)
            ),
            "epistemic_class": "a/c",
        },
        "mps_truncation": {
            "explicit_truncation_requested": explicit_truncation,
            "max_bond": None if max_bond is None else int(max_bond),
            "exact_bond_dimension_sufficient": int(
                ledger["exact_bond_dimension_sufficient"]
            ),
            "exact_bond_policy": str(ledger["exact_bond_policy"]),
            "accepted_as_exact_bond_representation": bool(
                ledger["accepted_as_exact_bond_representation"]
            ),
            "discarded_weight_ledger_complete": bool(
                ledger["discarded_weight_ledger_complete"]
            ),
            "discarded_weight_sum": discarded_sum,
            "worst_cut_discarded_weight": float(ledger["worst_cut_discarded_weight"]),
            "truncation_detected": truncation_detected,
            "gate": truncation_gate,
            "accepted_as_finite_bond_candidate": finite_bond_candidate,
            "accepted_as_restricted_risk_ledger": bool(
                ledger["discarded_weight_ledger_complete"]
            ),
            "accepted_as_production_error_bound": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": str(ledger["epistemic_class"]),
        },
        "overcap": {
            "requires_scalable_backend": requires_scalable,
            "dense_fallback_forbidden": True,
            "dense_certification_used_for_overcap": False,
            "accepted_as_restricted_overcap_execution": restricted_overcap_execution,
            "accepted_as_production_scalable_backend": False,
            "epistemic_class": "a/c",
        },
        "production_blockers": production_blockers,
        "scored_quantity_policy": "policy ledger only; no new scored quantity",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }


def _dense_certification_status(certification: dict[str, Any]) -> str:
    if bool(certification.get("executed", False)):
        return "passed" if bool(certification.get("passed", False)) else "failed"
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
    bonds = tuple(sorted({int(value) for value in values}))
    if len(bonds) < 2:
        raise ValueError("bond_values must contain at least two distinct positive integers")
    if any(value <= 0 for value in bonds):
        raise ValueError("bond_values must be positive")
    return bonds


def _normalize_trajectory_sweep_seeds(values: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    seeds = tuple(int(value) for value in values)
    if len(seeds) < 2:
        raise ValueError("rng_seeds must contain at least two explicit seeds")
    if len(set(seeds)) != len(seeds):
        raise ValueError("rng_seeds must be distinct")
    return seeds


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
        "passed": bool(run.get("passed", False)),
        "qt_mps_backend_executed": bool(run.get("qt_mps_backend_executed", False)),
        "record_count": execution.get("record_count"),
        "total_probability_residual": execution.get("total_probability_residual"),
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
        "passed": bool(run.get("passed", False)),
        "qt_mps_backend_executed": bool(run.get("qt_mps_backend_executed", False)),
        "record_count": execution.get("record_count"),
        "measurement_records": execution.get("measurement_records"),
        "record_counts": execution.get("record_counts"),
        "record_probabilities": execution.get("record_probabilities"),
        "total_probability_residual": execution.get("total_probability_residual"),
        "accepted_for_sampled_execution_evidence": acceptance.get(
            "accepted_for_sampled_execution_evidence"
        ),
        "accepted_for_production_scalable_backend": acceptance.get(
            "accepted_for_production_scalable_backend"
        ),
    }


def _trajectory_seed_sweep_comparison(
    runs: list[dict[str, Any]],
    *,
    seed_record_frequency_spread_gate: float | None,
) -> dict[str, Any]:
    reference_execution = runs[0].get("mps_execution") or {}
    reference_records = reference_execution.get("measurement_records")
    comparisons: list[dict[str, Any]] = []
    violations: list[str] = []
    probability_rows: list[list[float]] = []
    if reference_records is None:
        violations.append("reference_run_has_no_record_probabilities")
    for run in runs:
        execution = run.get("mps_execution") or {}
        records = execution.get("measurement_records")
        probs = execution.get("record_probabilities")
        sampling = execution.get("trajectory_sampling") or {}
        if not bool(run.get("qt_mps_backend_executed", False)):
            comparisons.append(
                {
                    "rng_seed": sampling.get("rng_seed"),
                    "compared_to_reference_record_order": False,
                    "reason": "run_not_executed",
                    "comparison_outcome_is_metric": False,
                }
            )
            violations.append("run_not_executed")
            continue
        if records != reference_records or probs is None:
            comparisons.append(
                {
                    "rng_seed": sampling.get("rng_seed"),
                    "compared_to_reference_record_order": False,
                    "reason": "measurement_record_order_mismatch",
                    "comparison_outcome_is_metric": False,
                }
            )
            violations.append("measurement_record_order_mismatch")
            continue
        probability_rows.append([float(value) for value in probs])
        comparisons.append(
            {
                "rng_seed": sampling.get("rng_seed"),
                "compared_to_reference_record_order": True,
                "comparison_object": "record_probabilities",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        )
    observed = 0.0
    if probability_rows:
        columns = zip(*probability_rows, strict=True)
        observed = max((max(column) - min(column) for column in columns), default=0.0)
    evaluated = seed_record_frequency_spread_gate is not None
    if evaluated and observed > float(seed_record_frequency_spread_gate):
        violations.append("seed_record_frequency_spread_exceeds_gate")
    return {
        "comparison_object": "record_probabilities",
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
    requires_scalable = bool(reference.get("carrier_program", {}).get("requires_scalable_backend"))
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
    dense_record = dense["record_evidence"]
    dense_records = dense_record["measurement_records"]
    dense_probs = [float(value) for value in dense_record["record_probabilities"]]
    violations: list[str] = []
    residuals: list[float] = []
    for run in runs:
        execution = run.get("mps_execution") or {}
        if execution.get("measurement_records") != dense_records:
            violations.append("measurement_record_order_mismatch")
            continue
        probs = [float(value) for value in execution.get("record_probabilities", ())]
        residuals.append(
            max(
                (abs(a - b) for a, b in zip(probs, dense_probs, strict=True)),
                default=0.0,
            )
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
        "dense_record_frequency_gate": float(dense_record_frequency_gate),
        "observed_max_abs_frequency_difference": observed,
        "violations": violations,
        "gate_role": "heuristic_dense_record_frequency_gate_not_metric",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def _nested_evidence_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": evidence.get("schema"),
        "content_hash": evidence.get("content_hash"),
        "representability": evidence.get("representability"),
        "verdict": evidence.get("verdict"),
        "passed": bool(evidence.get("passed", False)),
        "claims_qt_mps_backend_execution": bool(
            evidence.get("claims_qt_mps_backend_execution", False)
        ),
        "claims_exact_joint_lindblad_generator": bool(
            evidence.get("claims_exact_joint_lindblad_generator", False)
        ),
        "claims_dense_channel_evidence": bool(
            evidence.get("claims_dense_channel_evidence", False)
        ),
        "claims_production_scalable_backend": bool(
            evidence.get("claims_production_scalable_backend", False)
        ),
    }


def _resource_probe_policy(
    *,
    peak_allocated_bytes: int,
    peak_reserved_bytes: int,
    min_peak_allocated_gib: float | None,
    min_peak_reserved_gib: float | None,
) -> dict[str, Any]:
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
        if not bool(run.get("qt_mps_backend_executed", False)):
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
    executed = bool(certification.get("executed", False))
    passed = bool(certification.get("passed", False))
    accepted = bool(executed and passed)
    return {
        "status": status,
        "executed": executed,
        "passed": passed if executed else None,
        "accepted_as_dense_calibrated_reference": accepted,
        "dense_evidence_schema": certification.get("dense_evidence_schema"),
        "dense_evidence_content_hash": certification.get("dense_evidence_content_hash"),
        "comparison_outcome_is_metric": bool(
            certification.get("comparison_outcome_is_metric", False)
        ),
        "epistemic_class": "a/c",
    }


def _truncation_gate_result(
    ledger: dict[str, Any],
    *,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
) -> dict[str, Any]:
    gate_values = {
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
    }
    evaluated = any(value is not None for value in gate_values.values())
    worst = float(ledger.get("worst_cut_discarded_weight", 0.0))
    total = float(ledger.get("discarded_weight_sum", 0.0))
    violations: list[str] = []
    if (
        gate_values["worst_cut_discarded_weight_gate"] is not None
        and worst > float(gate_values["worst_cut_discarded_weight_gate"])
    ):
        violations.append("worst_cut_discarded_weight_exceeds_gate")
    if (
        gate_values["total_discarded_weight_gate"] is not None
        and total > float(gate_values["total_discarded_weight_gate"])
    ):
        violations.append("total_discarded_weight_exceeds_gate")
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


def _max_branch_bond(branches: list[tuple[tuple[int, ...], float, Any]]) -> int:
    out = 1
    for _bits, _weight, mps in branches:
        sizes = list(mps.bond_sizes())
        if sizes:
            out = max(out, max(int(x) for x in sizes))
    return int(out)


def _truncation_ledger(
    *,
    max_bond: int | None,
    num_sites: int,
    max_observed_bond: int,
    truncation_events: list[dict[str, Any]],
) -> dict[str, Any]:
    exact_bond = _exact_bond_dimension_sufficient(num_sites)
    if max_bond is None:
        return {
            "explicit_truncation_requested": False,
            "exact_bond_dimension_sufficient": exact_bond,
            "exact_bond_policy": "unbounded_no_explicit_cap",
            "accepted_as_exact_bond_representation": True,
            "discarded_weight_ledger_complete": True,
            "discarded_weight_sum": 0.0,
            "worst_cut_discarded_weight": 0.0,
            "n_truncating_ops": 0,
            "max_observed_bond": int(max_observed_bond),
            "ledger_scope": "no_explicit_mps_truncation_requested",
            "epistemic_class": "a",
        }
    discarded = [float(event["discarded_weight_sum"]) for event in truncation_events]
    worst = [
        float(record["discarded_weight"])
        for event in truncation_events
        for record in event.get("cut_records", ())
    ]
    return {
        "explicit_truncation_requested": True,
        "max_bond": int(max_bond),
        "exact_bond_dimension_sufficient": exact_bond,
        "exact_bond_policy": (
            "finite_cap_at_or_above_conservative_exact_sufficient_bond"
            if int(max_bond) >= exact_bond
            else "finite_cap_below_conservative_exact_sufficient_bond"
        ),
        "accepted_as_exact_bond_representation": bool(int(max_bond) >= exact_bond),
        "discarded_weight_ledger_complete": True,
        "ledger_method": "cuda_shadow_state_schmidt_tail_per_two_site_hamiltonian_gate",
        "discarded_weight_sum": float(sum(discarded)),
        "worst_cut_discarded_weight": float(max(worst, default=0.0)),
        "n_truncating_ops": sum(1 for value in discarded if value > 0.0),
        "n_tracked_two_site_ops": len(truncation_events),
        "max_observed_bond": int(max_observed_bond),
        "truncation_events": truncation_events,
        "ledger_scope": (
            "finite_max_bond_cuda_shadow_state_tail_ledger; records Schmidt-tail "
            "weight before each supported two-site Hamiltonian/control gate"
        ),
        "epistemic_class": "c",
    }


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
            if term_kind == "hamiltonian" and not _is_supported_hamiltonian_term(term):
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
                if _reset_basis(str(op.get("name", ""))) is None:
                    out.append(_unsupported(substep, "restricted_qt_mps_supports_pauli_reset_only"))
                    break
    return out


def _unsupported(substep: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "substep_id": str(substep["substep_id"]),
        "substep_kind": str(substep["substep_kind"]),
        "reason": str(reason),
    }


def _is_supported_hamiltonian_term(term: dict[str, Any]) -> bool:
    family = str(term["operator_family"]).upper()
    support = tuple(term["support"])
    if family in {"ZZ", "FSIM_PHASE"} and len(support) == 2:
        return True
    if family.startswith("COH_"):
        # Coherent families: 1-site for over-rotation, 2-site for parasitic/crosstalk
        if len(support) == 1 and family in {"COH_RX", "COH_RY", "COH_RZ", "COH_H"}:
            return True
        if len(support) == 2 and family in {
            "COH_XX_YY",
            "COH_XX",
            "COH_YY",
            "COH_XY",
            "COH_ZX",
            "COH_ZY",
            "COH_XZ",
            "COH_YZ",
            "COH_YX",
            "COH_CROSSTALK_ZZ",
        }:
            return True
        return False
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
) -> None:
    dt = float(substep["dt_ns"] if dt_ns is None else dt_ns)
    for term_index, term in enumerate(substep.get("terms", ())):
        if str(term["kind"]) != "hamiltonian":
            continue
        family = str(term["operator_family"]).upper()
        support = tuple(int(q) for q in term["support"])
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
                truncation_events=truncation_events,
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
                truncation_events=truncation_events,
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
) -> None:
    if len(support) != 2:
        raise ValueError(f"restricted QT/MPS expected a two-site support, got {support!r}")
    if max_bond is not None:
        truncation_events.append(
            _shadow_truncation_event(
                mps,
                gate,
                support=support,
                substep=substep,
                term=term,
                term_index=term_index,
                branch_bits=branch_bits,
                device=device,
                max_bond=int(max_bond),
                dt_ns=dt_ns,
                microstep_index=microstep_index,
                microstep_count=microstep_count,
            )
        )
    mps.gate_(
        gate,
        where=support,
        contract="auto-mps",
        max_bond=max_bond,
        cutoff=0.0,
    )


def _shadow_truncation_event(
    mps,
    gate: torch.Tensor,
    *,
    support: tuple[int, ...],
    substep: dict[str, Any],
    term: dict[str, Any],
    term_index: int,
    branch_bits: tuple[int, ...],
    device: str,
    max_bond: int,
    dt_ns: float,
    microstep_index: int,
    microstep_count: int,
) -> dict[str, Any]:
    shadow = mps.copy()
    shadow.gate_(
        gate,
        where=support,
        contract="auto-mps",
        max_bond=None,
        cutoff=0.0,
    )
    cut_records = _shadow_schmidt_tail_records(
        shadow,
        support=support,
        max_bond=max_bond,
        device=device,
    )
    discarded = [float(record["discarded_weight"]) for record in cut_records]
    return {
        "substep_id": str(substep["substep_id"]),
        "substep_kind": str(substep["substep_kind"]),
        "term_index": int(term_index),
        "operator_family": str(term["operator_family"]),
        "support": list(support),
        "branch_record_prefix": list(branch_bits),
        "max_bond": int(max_bond),
        "dt_ns_effective": float(dt_ns),
        "microstep_index": int(microstep_index),
        "microstep_count": int(microstep_count),
        "ledger_method": "cuda_shadow_state_schmidt_tail",
        "cut_records": cut_records,
        "discarded_weight_sum": float(sum(discarded)),
        "worst_cut_discarded_weight": float(max(discarded, default=0.0)),
        "n_truncated_cuts": sum(1 for value in discarded if value > 0.0),
        "epistemic_class": "c",
    }


def _shadow_schmidt_tail_records(
    mps,
    *,
    support: tuple[int, ...],
    max_bond: int,
    device: str,
) -> list[dict[str, Any]]:
    dense = mps.to_dense()
    if not isinstance(dense, torch.Tensor):
        dense = torch.as_tensor(dense, dtype=torch.complex128, device=device)
    dense = dense.to(device=device, dtype=torch.complex128).reshape(-1)
    norm = torch.linalg.vector_norm(dense)
    if float(norm.detach().cpu().item()) > 0.0:
        dense = dense / norm
    n = int(mps.L)
    state = dense.reshape((2,) * n)
    left = min(int(q) for q in support)
    right = max(int(q) for q in support)
    records: list[dict[str, Any]] = []
    for cut in range(left + 1, right + 1):
        matrix = state.reshape(2**cut, 2 ** (n - cut))
        svals = torch.linalg.svdvals(matrix)
        total = torch.sum(torch.abs(svals) ** 2)
        discarded = (
            torch.sum(torch.abs(svals[int(max_bond) :]) ** 2)
            if int(max_bond) < int(svals.numel())
            else torch.zeros((), dtype=torch.float64, device=device)
        )
        records.append(
            {
                "cut_index": int(cut),
                "left_sites": list(range(cut)),
                "right_sites": list(range(cut, n)),
                "pre_truncation_rank": int(svals.numel()),
                "kept_rank": min(int(max_bond), int(svals.numel())),
                "discarded_weight": float(discarded.real.detach().cpu().item()),
                "total_schmidt_weight": float(total.real.detach().cpu().item()),
            }
        )
    return records


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
        basis = _reset_basis(str(op.get("name", "")))
        if basis is None:
            raise ValueError(f"unsupported restricted QT/MPS reset operation {op!r}")
        for target in op.get("targets", ()):
            next_branches: list[tuple[tuple[int, ...], float, Any]] = []
            for bits, weight, mps in evolved:
                for outcome_bit, reset_state, probability in _reset_target_branches(
                    mps,
                    target=int(target),
                    basis=basis,
                    device=device,
                ):
                    if probability <= 1.0e-15:
                        continue
                    next_branches.append((bits, weight * probability, reset_state))
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
        basis = _reset_basis(str(op.get("name", "")))
        if basis is None:
            raise ValueError(f"unsupported restricted QT/MPS reset operation {op!r}")
        for target in op.get("targets", ()):
            branches = _reset_target_branches(
                state,
                target=int(target),
                basis=basis,
                device=device,
            )
            probabilities = [float(probability) for _bit, _state, probability in branches]
            if not probabilities:
                raise ValueError("sampled reset had no nonzero branch")
            index = _sample_index(probabilities, device=device, generator=generator)
            state = branches[index][1]
    return state


def _reset_target_branches(
    mps,
    *,
    target: int,
    basis: str,
    device: str,
) -> list[tuple[int, Any, float]]:
    rotated = mps.copy()
    pre = _reset_pre_rotation(basis, device=device)
    if pre is not None:
        rotated.gate_(pre, where=int(target), contract=True)
    out: list[tuple[int, Any, float]] = []
    for bit in (0, 1):
        projected, probability = _project_z_mps(
            rotated,
            targets=[int(target)],
            outcome_bits=[bit],
            device=device,
        )
        if probability <= 1.0e-15:
            continue
        if bit == 1:
            projected.gate_(_one_qubit_torch_gate("X", device=device), where=int(target), contract=True)
        if pre is not None:
            projected.gate_(
                pre.conj().transpose(-1, -2),
                where=int(target),
                contract=True,
            )
        out.append((bit, projected, float(probability)))
    return out


def _apply_z_measurement_reset_if_requested(
    mps,
    substep: dict[str, Any],
    *,
    outcome_bits: list[int],
    device: str,
):
    records = list(substep.get("operation_records", ()))
    if len(records) != 1:
        return mps
    op = records[0]
    if not bool(op.get("reset_after_measurement", False)):
        return mps
    if str(op.get("basis", "Z")).upper() != "Z":
        raise ValueError("restricted QT/MPS measurement reset supports Z basis only")
    reset = mps
    for target, bit in zip(op.get("targets", ()), outcome_bits, strict=True):
        if int(bit) == 1:
            reset.gate_(_one_qubit_torch_gate("X", device=device), where=int(target), contract=True)
    return reset


def _reset_basis(name: str) -> str | None:
    op_name = str(name).upper()
    if op_name in {"R", "RZ"}:
        return "Z"
    if op_name == "RX":
        return "X"
    if op_name == "RY":
        return "Y"
    return None


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
    truncation_events: list[dict[str, Any]],
) -> list[tuple[tuple[int, ...], float, Any]]:
    evolved: list[tuple[tuple[int, ...], float, Any]] = []
    for bits, weight, mps in branches:
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
            for kraus in _collapse_kraus(term, dt_ns, device=device):
                branched = mps.copy()
                support = tuple(int(q) for q in term["support"])
                branched.gate_(kraus, where=support[0], contract=True)
                probability = _norm_sq(branched)
                if probability <= 1.0e-15:
                    continue
                branched.multiply_(1.0 / (probability**0.5), spread_over=1)
                next_branches.append((bits, weight * probability, branched))
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
            probability = _norm_sq(branched)
            if probability <= 1.0e-15:
                continue
            candidates.append(branched)
            probabilities.append(float(probability))
        if not candidates:
            continue
        index = _sample_index(probabilities, device=device, generator=generator)
        selected = candidates[index]
        selected.multiply_(1.0 / (probabilities[index] ** 0.5), spread_over=1)
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
    outcomes = _measurement_records(len(targets))
    candidates: list[Any] = []
    probabilities: list[float] = []
    kept_outcomes: list[list[int]] = []
    for outcome in outcomes:
        projected, probability = _project_z_mps(
            mps,
            targets=targets,
            outcome_bits=outcome,
            device=device,
        )
        if probability <= 1.0e-15:
            continue
        kept_outcomes.append(outcome)
        candidates.append(projected)
        probabilities.append(float(probability))
    if not candidates:
        raise ValueError("sampled Z measurement had no nonzero outcome branch")
    index = _sample_index(probabilities, device=device, generator=generator)
    return kept_outcomes[index], candidates[index]


def _sample_index(
    probabilities: list[float],
    *,
    device: str,
    generator: torch.Generator,
) -> int:
    probs = torch.tensor(probabilities, dtype=torch.float64, device=device)
    total = torch.sum(probs)
    if float(total.detach().cpu().item()) <= 0.0:
        raise ValueError("cannot sample from a zero-probability branch set")
    probs = probs / total
    return int(torch.multinomial(probs, 1, generator=generator).detach().cpu().item())


def _collapse_kraus(term: dict[str, Any], dt_ns: float, *, device: str) -> tuple[torch.Tensor, ...]:
    family = str(term["operator_family"]).upper()
    coeff = abs(float(term["coefficient"]))
    if coeff == 0.0:
        return (torch.eye(2, dtype=torch.complex128, device=device),)
    rate = coeff * coeff
    if family in {"T1", "T1_UP"}:
        p = 1.0 - float(np.exp(-rate * float(dt_ns)))
        p = max(0.0, min(1.0, p))
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
        gamma = 0.5 * rate
        p = 0.5 * (1.0 - float(np.exp(-gamma * float(dt_ns))))
        p = max(0.0, min(0.5, p))
        return (
            np.sqrt(1.0 - p) * torch.eye(2, dtype=torch.complex128, device=device),
            np.sqrt(p)
            * torch.diag(
                torch.tensor([1.0, -1.0], dtype=torch.complex128, device=device)
            ),
        )
    raise ValueError(f"unsupported restricted QT/MPS collapse family {family!r}")


def _two_qubit_gate_matrix(gate: str, *, device: str) -> torch.Tensor:
    import stim

    name = str(gate).upper()
    if name not in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES:
        raise ValueError(f"unsupported two-qubit QT/MPS control gate {gate!r}")
    circuit = stim.Circuit(f"{name} 0 1")
    return torch.as_tensor(
        circuit.to_tableau().to_unitary_matrix(endian="big"),
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
    norm = _norm_sq(projected)
    if norm <= 1.0e-15:
        return projected, 0.0
    projected.multiply_(1.0 / (norm**0.5), spread_over=1)
    return projected, float(norm)


def _norm_sq(mps) -> float:
    return float((mps.H & mps).contract(all).real)


def _z_projector(bit: int, *, device: str) -> torch.Tensor:
    if int(bit) == 0:
        return torch.diag(torch.tensor([1.0, 0.0], dtype=torch.complex128, device=device))
    if int(bit) == 1:
        return torch.diag(torch.tensor([0.0, 1.0], dtype=torch.complex128, device=device))
    raise ValueError(f"invalid Z branch bit {bit!r}")


def _measurement_boundary(substep: dict[str, Any]) -> dict[str, Any]:
    records = list(substep.get("operation_records", ()))
    if len(records) != 1:
        raise ValueError("restricted QT/MPS measurement requires one operation record")
    op = records[0]
    return {
        "measurement_keys": [str(key) for key in op.get("measurement_keys", ())],
        "measurement_targets": [int(q) for q in op.get("targets", ())],
    }


def _measurement_records(num_targets: int) -> list[list[int]]:
    n = int(num_targets)
    return [[(index >> bit) & 1 for bit in range(n)] for index in range(2**n)]


def _xor_records(
    measurement_records: list[list[int]],
    measurement_keys: list[str],
    definitions,
) -> tuple[list[list[int]], list[str]]:
    key_to_index = {str(key): i for i, key in enumerate(measurement_keys)}
    records: list[list[int]] = []
    names: list[str] = []
    for definition in definitions:
        keys = [str(key) for key in definition.get("keys", ())]
        indices = [key_to_index[key] for key in keys]
        names.append(str(definition.get("name", f"xor{len(names)}")))
        records.append([sum(row[index] for index in indices) % 2 for row in measurement_records])
    transposed = [list(row) for row in zip(*records, strict=False)] if records else []
    return transposed, names


def _substep_summary(substep: dict[str, Any]) -> dict[str, Any]:
    h_families = [
        str(term["operator_family"])
        for term in substep.get("terms", ())
        if str(term["kind"]) == "hamiltonian"
    ]
    c_families = [
        str(term["operator_family"])
        for term in substep.get("terms", ())
        if str(term["kind"]) == "collapse" and abs(float(term["coefficient"])) > 0.0
    ]
    return {
        "substep_id": str(substep["substep_id"]),
        "substep_kind": str(substep["substep_kind"]),
        "route": str(substep["route"]),
        "route_reason": str(substep["route_reason"]),
        "support": list(substep["support"]),
        "dt_ns": substep["dt_ns"],
        "hamiltonian_operator_families": h_families,
        "hamiltonian_term_count": len(h_families),
        "nonzero_collapse_operator_families": c_families,
        "nonzero_collapse_term_count": len(c_families),
        "measurement_boundary_count": len(
            [
                term
                for term in substep.get("terms", ())
                if str(term["kind"]) == "measurement_boundary"
            ]
        ),
    }


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

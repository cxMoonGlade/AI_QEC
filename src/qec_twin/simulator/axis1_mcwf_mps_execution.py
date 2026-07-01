from __future__ import annotations

"""Fixed-microstep MCWF-over-MPS execution for Axis-1 carrier programs.

This is the first real execution slice behind ``mcwf_mps_state_record``. It is
deliberately narrower than the full contract: it executes fixed-microstep
trajectories with declared local dimensions, computational-subspace families
lifted into those dimensions, and the first registered one-site qutrit leakage
families. Mixed-dimension finite-bond ledgers remain a future slice.
"""

import hashlib
import json
import math
from typing import Any, Sequence

import numpy as np
import torch

from qec_twin.simulator.analog_schedule import SubstepSchedule
from qec_twin.simulator.axis1_carrier_program import (
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    axis1_carrier_program_manifest,
)
from qec_twin.simulator.axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_mcwf_mps_contract import (
    AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT,
    axis1_mcwf_mps_state_record_contract_manifest,
)
from qec_twin.simulator.axis1_state_evidence import _require_cuda_device
from qec_twin.simulator.axis1_ideal_controls import (
    _one_qubit_generator_and_coefficient,
    _two_qubit_generator_and_coefficient,
)
from qec_twin.simulator.axis1_qt_mps_execution import (
    _is_supported_hamiltonian_term,
    _max_branch_bond,
    _measurement_boundary,
    _measurement_records,
    _norm_sq,
    _reset_basis,
    _sample_index,
    _substep_summary,
    _truncation_ledger,
    _xor_records,
)


AXIS1_MCWF_MPS_EXECUTION_SCHEMA = (
    "qec_twin.simulator.axis1_mcwf_mps_state_record_execution.v1"
)
AXIS1_MCWF_MPS_EXECUTION_REPRESENTABILITY = (
    "axis1_mcwf_mps_fixed_microstep_local_dims_state_record"
)
AXIS1_MCWF_MPS_EXECUTION_BACKEND_CONTRACT = AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT
_FINITE_STEP_ORDER_FIRST = "first_order"
_FINITE_STEP_ORDER_STRANG = "strang_second_order"
_FINITE_STEP_ORDERS = (_FINITE_STEP_ORDER_FIRST, _FINITE_STEP_ORDER_STRANG)
_TOTAL_PROBABILITY_RESIDUAL_GATE = 1.0e-12
_ONE_SITE_LEAKAGE_HAMILTONIAN_FAMILIES = frozenset({"LEAK_EXCHANGE_12"})
_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS = {
    "LEAK_EXCHANGE_11_02": ((1, 1), (0, 2)),
    "LEAK_MOBILITY_12_21": ((1, 2), (2, 1)),
    "LEAK_TRANSPORT_30_12": ((3, 0), (1, 2)),
    "LEAK_TRANSPORT_31_22": ((3, 1), (2, 2)),
}
_TWO_SITE_CONDITIONAL_PHASE_FAMILIES = frozenset(
    {"LEAK_COND_PHASE_LEFT2_RIGHTZ", "LEAK_COND_PHASE_LEFTZ_RIGHT2"}
)
_LEAKAGE_COLLAPSE_FAMILIES = frozenset({"LEAK_SEEP_21", "LEAK_HEAT_12"})

# --------------------------------------------------------------------------- #
# Coherent Pauli-tensor families (Step 8): over-rotation + parasitic + crosstalk
# --------------------------------------------------------------------------- #
ONE_SITE_COHERENT_FAMILIES = frozenset({"COH_RX", "COH_RY", "COH_RZ"})
TWO_SITE_COHERENT_FAMILIES = frozenset(
    {
        "COH_XX_YY",
        "COH_XX",
        "COH_YY",
        "COH_ZX",
    }
)
CROSSTALK_COHERENT_FAMILIES = frozenset({"COH_CROSSTALK_ZZ"})
COHERENT_PAULI_FAMILIES = (
    ONE_SITE_COHERENT_FAMILIES | TWO_SITE_COHERENT_FAMILIES | CROSSTALK_COHERENT_FAMILIES
)

# Two-site joint (collective/Dicke) collapse families (M12 Phase-B). Distinguished from the one-site
# collapse families (T1/T1_UP/T2/RD/LEAK_*) so the support-arity preflight can fail closed on a
# mis-supported request instead of deferring the error to the operator builder at runtime.
TWO_SITE_COLLAPSE_FAMILIES = frozenset({"CORR_RELAX"})

# First-order MCWF no-jump truncation (K0 = I - 1/2 c^dag c dt) does not preserve probability: the
# per-microstep mass residual is 1/4 dt^2 <(sum_k c_k^dag c_k)^2> = O(dt^2). At gamma*dt ~ 1 with too
# few microsteps the step is grossly non-CPTP (|11> probability mass -> 2.0 for CORR_RELAX at
# g=0.05, dt=20, microstep_count=1 — M12 Phase-B 5-model review; quantified in
# outputs/twin_validation/cert_m12_phaseB_convergence.py). This (c)-class heuristic tripwire (a
# go/no-go gate, NOT a premise or error bound) fail-closes when the state-independent worst-case
# per-microstep bound 1/4 dt_micro^2 (sum_k ||c_k^dag c_k||_op)^2 exceeds the budget; because that
# bound dominates the runtime residual, passing the preflight guarantees the runtime residual stays
# within budget. The measured convergence law (1-F_e ~ 4x per microstep doubling) makes the required
# microstep_count computable and it is reported in the fail-closed payload. Pass
# mass_residual_budget=None to disable for a deliberate convergence study (the only sanctioned use of
# the grossly-truncated single-microstep regime).
_MCWF_FIRST_ORDER_MASS_RESIDUAL_BUDGET = 0.1


def axis1_mcwf_mps_state_record_execution_manifest(
    schedule: SubstepSchedule,
    *,
    local_dims: Sequence[int] | None = None,
    device: str = "cuda",
    max_bond: int | None = None,
    microstep_count: int = 1,
    finite_step_order: str = _FINITE_STEP_ORDER_FIRST,
    trajectory_count: int = 1,
    rng_seed: int | None = None,
    initial_levels: Sequence[int] | None = None,
    leaked_readout_b: float = 1.0,
    mass_residual_budget: float | None = _MCWF_FIRST_ORDER_MASS_RESIDUAL_BUDGET,
) -> dict[str, Any]:
    """Execute the first fixed-microstep MCWF/MPS Axis-1 slice.

    The implementation samples at most one collapse jump per microstep from the
    substep's collapse list. It is a finite-step quantum-jump approximation to
    the summed same-substep generator, not dense joint-L channel evidence.

    ``mass_residual_budget`` fail-closes (verdict ``"fail"``) before execution when the first-order
    no-jump truncation is grossly non-CPTP at the requested ``microstep_count`` (the worst-case
    per-microstep probability-mass residual bound exceeds the budget); the fail payload reports the
    required ``microstep_count``. Pass ``None`` to disable for a deliberate convergence study.
    """

    dev = _require_cuda_device(device)
    if max_bond is not None and int(max_bond) <= 0:
        raise ValueError("max_bond must be positive when provided")
    if int(microstep_count) <= 0:
        raise ValueError("microstep_count must be positive")
    if int(trajectory_count) <= 0:
        raise ValueError("trajectory_count must be positive")
    step_order = _normalize_finite_step_order(finite_step_order)
    _validate_schedule_for_axis1_channel_evidence(
        schedule,
        allow_multilevel_leakage_context=True,
    )
    dims = _normalize_local_dims(local_dims, num_sites=int(schedule.num_qubits))
    levels = _normalize_initial_levels(initial_levels, local_dims=dims)
    readout_b = _normalize_leaked_readout_b(leaked_readout_b)
    contract = axis1_mcwf_mps_state_record_contract_manifest(
        schedule,
        local_dims=dims,
        device=dev,
    )
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT,
    )
    base: dict[str, Any] = {
        "schema": AXIS1_MCWF_MPS_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_MCWF_MPS_EXECUTION_REPRESENTABILITY,
        "backend_contract": AXIS1_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": dev,
        "carrier_program": _program_summary(program),
        "mcwf_mps_contract": _contract_summary(contract),
        "local_hilbert_space": dict(contract["local_hilbert_space"]),
        "max_bond": None if max_bond is None else int(max_bond),
        "microstep_count": int(microstep_count),
        "mass_residual_budget": (
            None if mass_residual_budget is None else float(mass_residual_budget)
        ),
        "finite_step_order": step_order,
        "trajectory_count": int(trajectory_count),
        "rng_seed": None if rng_seed is None else int(rng_seed),
        "initial_levels": list(levels),
        "leaked_readout_b": readout_b,
        "claims_mcwf_mps_backend_execution": False,
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": (
            "fixed-microstep MCWF/MPS execution is a verification surface only; "
            "no new scored quantity"
        ),
        "approximation_book": {
            "schema": "qec_twin.simulator.axis1_mcwf_mps_execution_approximation_book.v1",
            "unraveling_policy": {
                "name": "fixed_microstep_first_order_quantum_jump_mcwf",
                "finite_step_order": step_order,
                "microstep_count": int(microstep_count),
                "same_substep_generator_policy": (
                    "collapse jump candidates are sampled jointly per microstep "
                    "from the substep collapse list; this is not sequential "
                    "finite-channel composition"
                ),
                "exact_continuous_time_claim": False,
                "exact_joint_lindblad_channel_claim": False,
                "epistemic_class": "c",
            },
            "mps_truncation": {
                "max_bond": None if max_bond is None else int(max_bond),
                "accepted_as_production_error_bound": False,
                "epistemic_class": "c",
            },
        },
        "epistemic_classes": {
            "program_consumption": "a",
            "fixed_microstep_mcwf_execution": "c",
            "backend_execution_status": "a/c",
            "production_backend_status": "a",
        },
    }
    if max_bond is not None and any(dim != 2 for dim in dims):
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "mcwf_mps_backend_executed": False,
            "blocked_reason": "mcwf_mps_multilevel_finite_bond_ledger_not_implemented",
            "blocked_substeps": [],
            "mps_execution": None,
            "restricted_acceptance_policy": _blocked_acceptance_policy(
                blocked_reason="mcwf_mps_multilevel_finite_bond_ledger_not_implemented",
                rng_seed=rng_seed,
                trajectory_count=int(trajectory_count),
            ),
            "scope": (
                "MCWF/MPS multilevel execution currently supports no-explicit-"
                "truncation runs only. A finite-bond mixed-dimension discarded-"
                "weight ledger is required before accepting max_bond with "
                "qutrit/ququart local_dims."
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload
    unsupported = _unsupported_substeps(program, local_dims=dims)
    if unsupported:
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "mcwf_mps_backend_executed": False,
            "blocked_reason": unsupported[0]["reason"],
            "blocked_substeps": unsupported,
            "mps_execution": None,
            "restricted_acceptance_policy": _blocked_acceptance_policy(
                blocked_reason=unsupported[0]["reason"],
                rng_seed=rng_seed,
                trajectory_count=int(trajectory_count),
            ),
            "scope": (
                "fixed-microstep MCWF/MPS execution failed closed for unsupported "
                "terms or record boundaries"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    if mass_residual_budget is not None:
        residual_blocks = _first_order_mass_residual_blocks(
            program,
            local_dims=dims,
            microstep_count=int(microstep_count),
            device=dev,
            budget=float(mass_residual_budget),
        )
        if residual_blocks:
            payload = {
                **base,
                "verdict": "fail",
                "passed": False,
                "mcwf_mps_backend_executed": False,
                "blocked_reason": residual_blocks[0]["reason"],
                "blocked_substeps": residual_blocks,
                "mps_execution": None,
                "restricted_acceptance_policy": _blocked_acceptance_policy(
                    blocked_reason=residual_blocks[0]["reason"],
                    rng_seed=rng_seed,
                    trajectory_count=int(trajectory_count),
                ),
                "scope": (
                    "fixed-microstep MCWF/MPS execution failed closed: the first-order no-jump "
                    "truncation is grossly non-CPTP at this microstep_count (raise microstep_count "
                    "to required_microstep_count, or pass mass_residual_budget=None to override for "
                    "a deliberate convergence study)"
                ),
            }
            payload["content_hash"] = _stable_payload_hash(payload)
            return payload

    execution = _execute_sampled_mcwf_program(
        program,
        record_layout_ref=schedule.record_layout_ref,
        device=dev,
        max_bond=max_bond,
        microstep_count=int(microstep_count),
        finite_step_order=step_order,
        trajectory_count=int(trajectory_count),
        rng_seed=rng_seed,
        local_dims=dims,
        initial_levels=levels,
        leaked_readout_b=readout_b,
    )
    from qec_twin.simulator.axis1_mcwf_dense_certification import (
        dense_jointL_record_certification,
        restricted_acceptance_policy,
    )

    certification = dense_jointL_record_certification(
        schedule, execution, program, device=dev
    )
    acceptance = restricted_acceptance_policy(
        execution=execution,
        certification=certification,
        program=program,
        rng_seed=rng_seed,
        trajectory_count=int(trajectory_count),
    )
    passed = bool(acceptance["accepted_for_restricted_execution"])
    payload = {
        **base,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "mcwf_mps_backend_executed": True,
        "claims_mcwf_mps_backend_execution": True,
        "blocked_reason": None if passed else acceptance["blocked_reason"],
        "blocked_substeps": [],
        "mps_execution": execution,
        "restricted_acceptance_policy": acceptance,
        "scope": (
            "fixed-microstep MCWF/MPS state/record execution for qubit or "
            "declared multilevel local_dims; no exact joint-L channel evidence, "
            "no DEM/decoder semantics, no Axis-2 source timeline, and no "
            "production scalable backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _execute_sampled_mcwf_program(
    program: dict[str, Any],
    *,
    record_layout_ref: dict[str, Any],
    device: str,
    max_bond: int | None,
    microstep_count: int,
    finite_step_order: str,
    trajectory_count: int,
    rng_seed: int | None,
    local_dims: tuple[int, ...],
    initial_levels: tuple[int, ...],
    leaked_readout_b: float,
) -> dict[str, Any]:
    import quimb.tensor as qtn

    step_order = _normalize_finite_step_order(finite_step_order)
    ntraj = int(trajectory_count)
    seed = 0 if rng_seed is None else int(rng_seed)
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    num_qubits = int(program["program"]["num_qubits"])
    if len(local_dims) != num_qubits:
        raise ValueError(
            f"local_dims length {len(local_dims)} does not match program num_qubits {num_qubits}"
        )
    product_vectors = [
        _basis_vector(dim, level)
        for dim, level in zip(local_dims, initial_levels, strict=True)
    ]
    initial = qtn.MPS_product_state(product_vectors)
    initial.apply_to_arrays(
        lambda x: torch.as_tensor(x, dtype=torch.complex128, device=device)
    )

    records_by_bits: dict[tuple[int, ...], int] = {}
    records_by_levels: dict[tuple[int, ...], int] = {}
    applied: list[dict[str, Any]] = []
    truncation_events: list[dict[str, Any]] = []
    jump_family_counts: dict[str, int] = {}
    microstep_mass_residuals: list[float] = []
    max_observed_bond = _max_branch_bond([((), 1.0, initial)])
    measurement_keys: list[str] = []
    measurement_targets: list[int] = []

    for trajectory_index in range(ntraj):
        bits: tuple[int, ...] = ()
        levels: tuple[int, ...] = ()
        state = initial.copy()
        for substep_index, substep in enumerate(program["program"]["substeps"]):
            jump_count = 0
            if str(substep["substep_kind"]) == "reset":
                state = _sample_reset_for_operations_multilevel(
                    state,
                    substep,
                    local_dims=local_dims,
                    device=device,
                    generator=generator,
                )
            elif _substep_has_mcwf_terms(substep):
                dt_micro = float(substep["dt_ns"]) / float(microstep_count)
                for microstep_index in range(int(microstep_count)):
                    state, record = _mcwf_microstep(
                        state,
                        substep,
                        device=device,
                        generator=generator,
                        max_bond=max_bond,
                        truncation_events=truncation_events,
                        dt_ns=dt_micro,
                        finite_step_order=step_order,
                        microstep_index=microstep_index,
                        microstep_count=int(microstep_count),
                        branch_bits=bits,
                        local_dims=local_dims,
                    )
                    microstep_mass_residuals.append(
                        float(record["probability_mass_residual"])
                    )
                    family = str(record["selected_jump_family"])
                    if family != "NO_JUMP":
                        jump_family_counts[family] = jump_family_counts.get(family, 0) + 1
                        jump_count += 1
            max_observed_bond = max(
                max_observed_bond,
                _max_branch_bond([(bits, 1.0, state)]),
            )
            if trajectory_index == 0:
                applied.append(
                    {
                        **_substep_summary(substep),
                        "unraveling_policy": "fixed_microstep_first_order_quantum_jump_mcwf",
                        "finite_step_order": step_order,
                        "microstep_count": int(microstep_count),
                        "sampled_trajectory_count": ntraj,
                        "sampled_jump_count_max_over_trajectories": int(jump_count),
                        "max_jumps_per_microstep": 1,
                        "max_observed_bond_after_substep": _max_branch_bond(
                            [(bits, 1.0, state)]
                        ),
                    }
                )
            else:
                applied[substep_index]["sampled_jump_count_max_over_trajectories"] = max(
                    int(applied[substep_index]["sampled_jump_count_max_over_trajectories"]),
                    int(jump_count),
                )
                applied[substep_index]["max_observed_bond_after_substep"] = max(
                    int(applied[substep_index]["max_observed_bond_after_substep"]),
                    _max_branch_bond([(bits, 1.0, state)]),
                )
            if str(substep["substep_kind"]) != "measurement":
                continue
            boundary = _aggregating_measurement_boundary(substep)
            if trajectory_index == 0:
                measurement_keys.extend(boundary["measurement_keys"])
                measurement_targets.extend(boundary["measurement_targets"])
            outcome_levels, outcome_bits, state = _sample_measurement_multilevel(
                state,
                targets=boundary["measurement_targets"],
                bases=boundary["measurement_bases"],
                local_dims=local_dims,
                device=device,
                generator=generator,
                leaked_readout_b=float(leaked_readout_b),
            )
            state = _apply_measurement_reset_if_requested_multilevel(
                state,
                substep,
                outcome_levels=outcome_levels,
                local_dims=local_dims,
                device=device,
            )
            bits = bits + tuple(int(bit) for bit in outcome_bits)
            levels = levels + tuple(int(level) for level in outcome_levels)
        records_by_bits[bits] = records_by_bits.get(bits, 0) + 1
        if levels:
            records_by_levels[levels] = records_by_levels.get(levels, 0) + 1

    records = _measurement_records(len(measurement_keys)) if measurement_keys else [()]
    record_counts = [int(records_by_bits.get(tuple(record), 0)) for record in records]
    probabilities = [float(count) / float(ntraj) for count in record_counts]
    level_records = sorted(records_by_levels)
    level_record_counts = [
        int(records_by_levels.get(tuple(record), 0)) for record in level_records
    ]
    level_record_probabilities = [
        float(count) / float(ntraj) for count in level_record_counts
    ]
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
        "initial_state": "local_basis_product_mps",
        "initial_levels": list(initial_levels),
        "site_order": list(range(num_qubits)),
        "physical_dimension": None if len(set(local_dims)) != 1 else int(local_dims[0]),
        "local_dims": list(local_dims),
        "mps_library": "quimb.tensor.MatrixProductState",
        "array_backend": "torch_cuda_complex128",
        "unraveling_policy": "fixed_microstep_first_order_quantum_jump_mcwf",
        "hamiltonian_evolution_policy": "connected_support_cluster_hamiltonian_sum_matrix_exp",
        "collapse_evolution_policy": "joint_first_order_jump_competition_per_microstep",
        "same_substep_generator_policy": (
            "Hamiltonian terms and collapse jump candidates are consumed from the "
            "same compiler-generated carrier substep"
        ),
        "finite_step_policy": {
            "name": _mcwf_finite_step_policy_name(step_order),
            "order": step_order,
            "microstep_count": int(microstep_count),
            "microstep_dt_policy": "equal_substeps_dt_ns_div_microstep_count",
            "hamiltonian_grouping_policy": (
                "connected_support_cluster_terms_are_summed_before_matrix_exp"
            ),
            "exact_summed_lindbladian_claim": False,
            "comparison_outcome_is_metric": False,
        },
        "trajectory_sampling": {
            "mode": "sampled_fixed_microstep_mcwf_trajectories",
            "trajectory_count": ntraj,
            "rng_seed": seed,
            "rng_seed_required_for_acceptance": True,
            "rng_seed_was_explicit": rng_seed is not None,
            "rng_seed_default_policy": "default_zero_when_not_provided",
            "rng_backend": "torch.Generator(cuda)",
            "probability_semantics": "empirical_record_frequencies",
            "single_trajectory_density_claim": False,
            "comparison_outcome_is_metric": False,
        },
        "jump_sampling": {
            "max_jumps_per_microstep": 1,
            "jump_family_counts": dict(sorted(jump_family_counts.items())),
            "probability_mass_residual_max": float(
                max(microstep_mass_residuals, default=0.0)
            ),
            "probability_mass_residual_mean": float(
                sum(microstep_mass_residuals) / len(microstep_mass_residuals)
                if microstep_mass_residuals
                else 0.0
            ),
            "probability_mass_residual_gate_role": (
                "diagnostic_runtime_crosscheck_of_preflight_mass_residual_gate"
            ),
            "epistemic_class": "c",
        },
        "exact_joint_generator_claim": False,
        "exact_summed_lindbladian_claim": False,
        "measurement_basis": "Z",
        "multilevel_measurement_policy": {
            "name": "computational_level_sample_then_binary_record",
            "bit_mapping": "level_0_to_bit_0_level_1_to_bit_1_level_ge_2_to_bit_1_with_leaked_readout_b",
            "leaked_readout_b": float(leaked_readout_b),
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "measurement_keys": measurement_keys,
        "measurement_targets": measurement_targets,
        "measurement_records": [list(record) for record in records],
        "record_counts": record_counts,
        "record_probabilities": probabilities,
        "level_records": [list(record) for record in level_records],
        "level_record_counts": level_record_counts,
        "level_record_probabilities": level_record_probabilities,
        "record_count": len(records),
        "total_probability": total,
        "total_probability_residual": abs(total - 1.0),
        "mps_truncation_ledger": _mcwf_mps_truncation_ledger(
            max_bond=max_bond,
            local_dims=local_dims,
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


def _mcwf_microstep(
    mps,
    substep: dict[str, Any],
    *,
    device: str,
    generator: torch.Generator,
    max_bond: int | None,
    truncation_events: list[dict[str, Any]],
    dt_ns: float,
    finite_step_order: str,
    microstep_index: int,
    microstep_count: int,
    branch_bits: tuple[int, ...],
    local_dims: tuple[int, ...],
) -> tuple[Any, dict[str, Any]]:
    state = mps.copy()
    if finite_step_order == _FINITE_STEP_ORDER_STRANG:
        _apply_hamiltonian_terms_multilevel(
            state,
            substep,
            device=device,
            max_bond=max_bond,
            branch_bits=branch_bits,
            truncation_events=truncation_events,
            dt_ns=0.5 * float(dt_ns),
            microstep_index=microstep_index,
            microstep_count=microstep_count,
            local_dims=local_dims,
        )
        state, record = _sample_joint_jump_or_nojump(
            state,
            substep,
            dt_ns=float(dt_ns),
            device=device,
            generator=generator,
            local_dims=local_dims,
        )
        _apply_hamiltonian_terms_multilevel(
            state,
            substep,
            device=device,
            max_bond=max_bond,
            branch_bits=branch_bits,
            truncation_events=truncation_events,
            dt_ns=0.5 * float(dt_ns),
            microstep_index=microstep_index,
            microstep_count=microstep_count,
            local_dims=local_dims,
        )
        return state, record
    _apply_hamiltonian_terms_multilevel(
        state,
        substep,
        device=device,
        max_bond=max_bond,
        branch_bits=branch_bits,
        truncation_events=truncation_events,
        dt_ns=float(dt_ns),
        microstep_index=microstep_index,
        microstep_count=microstep_count,
        local_dims=local_dims,
    )
    return _sample_joint_jump_or_nojump(
        state,
        substep,
        dt_ns=float(dt_ns),
        device=device,
        generator=generator,
        local_dims=local_dims,
    )


def _apply_hamiltonian_terms_multilevel(
    mps,
    substep: dict[str, Any],
    *,
    device: str,
    max_bond: int | None,
    branch_bits: tuple[int, ...],
    truncation_events: list[dict[str, Any]],
    dt_ns: float,
    microstep_index: int,
    microstep_count: int,
    local_dims: tuple[int, ...],
) -> None:
    dt = float(dt_ns)
    all_qubit_dims = all(dim == 2 for dim in local_dims)
    for group in _hamiltonian_group_gates(
        substep,
        dt_ns=dt,
        local_dims=local_dims,
        device=device,
    ):
        _apply_mps_gate(
            mps,
            group["gate"],
            support=group["support"],
            substep=substep,
            term=group["term"],
            term_index=group["term_index"],
            branch_bits=branch_bits,
            device=device,
            max_bond=max_bond,
            dt_ns=dt,
            microstep_index=microstep_index,
            microstep_count=microstep_count,
            truncation_events=truncation_events,
            track_shadow=all_qubit_dims,
        )


def _connected_support_clusters(
    supports: list[tuple[int, ...]],
) -> list[list[int]]:
    """Partition term indices into connected components of the support-overlap graph.

    ``supports[i]`` is the (ascending) support tuple of term ``i``. Two terms are
    adjacent iff their supports share >=1 qubit; the returned clusters are the
    TRANSITIVE closure (so ``(0,1)`` and ``(1,2)`` land in one cluster, even though
    ``(0,)`` and ``(2,)`` do not directly overlap). Each cluster is a list of term
    indices, and the clusters are returned in order of FIRST appearance so the gate
    sequence is deterministic and stable w.r.t. term order. (W-A fix, ADR Axis-1.)
    """
    n = len(supports)
    parent = list(range(n))

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:  # path compression
            parent[x], x = root, parent[x]
        return root

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # Map each qubit to the first term index that touches it; union on collision.
    qubit_owner: dict[int, int] = {}
    for i, support in enumerate(supports):
        for q in support:
            if q in qubit_owner:
                union(qubit_owner[q], i)
            else:
                qubit_owner[q] = i

    clusters: dict[int, list[int]] = {}
    order: list[int] = []
    for i in range(n):
        r = find(i)
        if r not in clusters:
            clusters[r] = []
            order.append(r)
        clusters[r].append(i)
    return [clusters[r] for r in order]


def _lift_hamiltonian_to_cluster(
    hamiltonian: torch.Tensor,
    *,
    term_support: tuple[int, ...],
    cluster_support: tuple[int, ...],
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    """Embed ``hamiltonian`` (defined on ``term_support`` in the carrier's
    qubit-0-major kron order) into the ``cluster_support`` Hilbert space: identity on
    the cluster qubits NOT in ``term_support``, the term operator on its own qubits,
    in the cluster's ASCENDING-qubit ordering.

    Algebra (the reused kron-then-leg-permute pattern of
    ``forward.exact.circuit_sim.embed_operator``, generalized to a multi-site source
    operator + mixed local dims): ``full = kron(H, I_rest)`` (qubit order
    ``term_support + absent``), reshape to per-qubit legs, then permute the legs into
    the cluster's ascending order and reshape back. ``term_support`` MUST be a subset
    of ``cluster_support`` and both ascending.
    """
    term_support = tuple(int(q) for q in term_support)
    cluster_support = tuple(int(q) for q in cluster_support)
    if not set(term_support).issubset(cluster_support):
        raise ValueError(
            f"term_support {term_support!r} is not a subset of cluster_support "
            f"{cluster_support!r}"
        )

    H = torch.as_tensor(hamiltonian, dtype=torch.complex128, device=device).contiguous()
    expected_term_dim = 1
    for q in term_support:
        expected_term_dim *= int(local_dims[q])
    if H.shape != (expected_term_dim, expected_term_dim):
        raise ValueError(
            f"term Hamiltonian shape {tuple(H.shape)} != "
            f"({expected_term_dim}, {expected_term_dim}) for support {term_support!r}"
        )

    absent = tuple(q for q in cluster_support if q not in set(term_support))
    full_order = term_support + absent  # qubit order produced by the kron below
    n = len(full_order)

    rest_dim = 1
    for q in absent:
        rest_dim *= int(local_dims[q])

    # Step 1: kron-in the identity for the absent cluster qubits.
    if rest_dim > 1:
        eye_rest = torch.eye(rest_dim, dtype=torch.complex128, device=device)
        full = torch.kron(H.contiguous(), eye_rest.contiguous())
    else:
        full = H

    # Step 2: reshape to per-qubit legs and permute into cluster ascending order.
    leg_dims = [int(local_dims[q]) for q in full_order]
    cluster_dim = 1
    for d in leg_dims:
        cluster_dim *= d
    perm_q = [full_order.index(q) for q in cluster_support]  # cluster-pos -> current-pos
    perm = perm_q + [n + p for p in perm_q]
    full = (
        full.reshape(leg_dims + leg_dims)
        .permute(*perm)
        .contiguous()
        .reshape(cluster_dim, cluster_dim)
    )
    return full


def _hamiltonian_group_gates(
    substep: dict[str, Any],
    *,
    dt_ns: float,
    local_dims: tuple[int, ...],
    device: str,
) -> tuple[dict[str, Any], ...]:
    """Connected-cluster joint exponentiation (the W-A fix). Same signature + return
    shape as before (one ``{"support", "gate", "term_index", "term"}`` dict per gate).

    Hamiltonian terms are partitioned into connected components of the support-overlap
    graph (transitive closure). For each cluster the member Hamiltonians (each built on
    its OWN support by ``_hamiltonian_matrix_for_term``) are LIFTED to the cluster's
    combined support, SUMMED into one ``H_cluster``, Hermitized, and exponentiated ONCE
    (``gate = matrix_exp(-i dt H_cluster)``) on ``cluster_support``. Disjoint clusters
    => separate gates (they commute, so the product is exact and the dense ``expm``
    dimension stays minimal). Co-supported terms are the same-support special case (a
    single-cluster lift that is a no-op permutation). This retains the within-substep
    cross-terms ``[H_i, H_j]`` that the previous exact-support grouping dropped
    (Lie-Trotter), per the Axis-1 joint-generator requirement (Jaschke 1804.09796 App.A).
    """
    term_records: list[dict[str, Any]] = []
    for term_index, term in enumerate(substep.get("terms", ())):
        if str(term["kind"]) != "hamiltonian":
            continue
        support = tuple(int(q) for q in term["support"])
        hamiltonian = _hamiltonian_matrix_for_term(
            term,
            support=support,
            local_dims=local_dims,
            device=device,
        )
        term_records.append(
            {
                "term_index": int(term_index),
                "support": support,
                "hamiltonian": hamiltonian,
                "family": str(term["operator_family"]).upper(),
            }
        )

    if not term_records:
        return ()

    supports = [rec["support"] for rec in term_records]
    clusters = _connected_support_clusters(supports)

    out: list[dict[str, Any]] = []
    for member_idx_list in clusters:
        members = [term_records[i] for i in member_idx_list]

        cluster_qubits: set[int] = set()
        for rec in members:
            cluster_qubits.update(rec["support"])
        cluster_support = tuple(sorted(cluster_qubits))
        cluster_dim = 1
        for q in cluster_support:
            cluster_dim *= int(local_dims[q])

        h_cluster = torch.zeros(
            (cluster_dim, cluster_dim), dtype=torch.complex128, device=device
        )
        families: list[str] = []
        term_indices: list[int] = []
        for rec in members:
            h_lifted = _lift_hamiltonian_to_cluster(
                rec["hamiltonian"],
                term_support=rec["support"],
                cluster_support=cluster_support,
                local_dims=local_dims,
                device=device,
            )
            h_cluster = h_cluster + h_lifted
            families.append(rec["family"])
            term_indices.append(rec["term_index"])

        h_cluster = 0.5 * (h_cluster + h_cluster.conj().transpose(-1, -2))
        gate = torch.linalg.matrix_exp((-1.0j * float(dt_ns)) * h_cluster)

        member_supports = tuple(rec["support"] for rec in members)
        out.append(
            {
                "support": cluster_support,
                "gate": gate,
                "term_index": min(term_indices),
                "term": {
                    "kind": "hamiltonian",
                    "support": list(cluster_support),
                    "operator_family": "H_CLUSTER[" + "+".join(families) + "]",
                    "coefficient": None,
                    "coefficient_source": "connected_support_cluster_hamiltonian_sum",
                    "provenance": {
                        "substep_id": str(substep["substep_id"]),
                        "families": list(families),
                        "term_indices": list(term_indices),
                        "member_supports": [list(s) for s in member_supports],
                        "cluster_support": list(cluster_support),
                        "grouping_policy": (
                            "connected_support_cluster_summed_before_matrix_exp"
                        ),
                    },
                    "epistemic_class": "a/c",
                },
            }
        )
    return tuple(out)


def _hamiltonian_matrix_for_term(
    term: dict[str, Any],
    *,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    family = str(term["operator_family"]).upper()
    coefficient = float(term["coefficient"])
    if family.startswith("CTRL_"):
        return _control_hamiltonian_matrix(
            family,
            coefficient=coefficient,
            support=support,
            local_dims=local_dims,
            device=device,
        )
    if family in {"ZZ", "FSIM_PHASE"}:
        return _zz_hamiltonian_matrix(
            coefficient=coefficient,
            support=support,
            local_dims=local_dims,
            device=device,
        )
    if family == "LEAK_EXCHANGE_12":
        if len(support) != 1:
            raise ValueError(f"LEAK_EXCHANGE_12 requires one-site support, got {support!r}")
        return _one_site_level_exchange_hamiltonian(
            coefficient=coefficient,
            local_dim=local_dims[support[0]],
            levels=(1, 2),
            device=device,
        )
    if family in _TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS:
        if len(support) != 2:
            raise ValueError(f"{family} requires two-site support, got {support!r}")
        return _two_site_level_exchange_hamiltonian(
            coefficient=coefficient,
            dims=(local_dims[support[0]], local_dims[support[1]]),
            levels=_TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS[family],
            device=device,
        )
    if family in _TWO_SITE_CONDITIONAL_PHASE_FAMILIES:
        if len(support) != 2:
            raise ValueError(f"{family} requires two-site support, got {support!r}")
        return _two_site_conditional_phase_hamiltonian(
            coefficient=coefficient,
            dims=(local_dims[support[0]], local_dims[support[1]]),
            family=family,
            device=device,
        )
    if family in COHERENT_PAULI_FAMILIES:
        return _embed_coherent_generator(
            family,
            coefficient=coefficient,
            support=support,
            local_dims=local_dims,
            device=device,
        )
    raise ValueError(f"unsupported MCWF Hamiltonian family {family!r}")


def _control_hamiltonian_matrix(
    family: str,
    *,
    coefficient: float,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    gate_name = str(family).upper().removeprefix("CTRL_")
    if len(support) == 1:
        generator, _ = _one_qubit_generator_and_coefficient(
            gate_name,
            1.0,
            device=device,
        )
        return float(coefficient) * _lift_one_site_hamiltonian(
            generator,
            local_dim=local_dims[support[0]],
            device=device,
        )
    if len(support) == 2:
        generator, _ = _two_qubit_generator_and_coefficient(
            gate_name,
            1.0,
            device=device,
        )
        return float(coefficient) * _lift_two_site_hamiltonian(
            generator,
            dims=(local_dims[support[0]], local_dims[support[1]]),
            device=device,
        )
    raise ValueError(f"CTRL Hamiltonian requires one- or two-site support, got {support!r}")


def _zz_hamiltonian_matrix(
    *,
    coefficient: float,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    if len(support) != 2:
        raise ValueError(f"ZZ/FSIM_PHASE requires two-site support, got {support!r}")
    d0 = int(local_dims[support[0]])
    d1 = int(local_dims[support[1]])
    out = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    out[1 * d1 + 1, 1 * d1 + 1] = float(coefficient)
    return out


def _pauli_2level(axis: str, *, device: str) -> torch.Tensor:
    """Return the 2x2 Pauli operator for axis in {X, Y, Z, H} on device."""
    cdt = torch.complex128
    a = str(axis).upper()
    if a == "X":
        return torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=cdt, device=device)
    if a == "Y":
        return torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=cdt, device=device)
    if a == "Z":
        return torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=cdt, device=device)
    if a == "H":
        inv = 1.0 / math.sqrt(2.0)
        return inv * torch.tensor([[1.0, 1.0], [1.0, -1.0]], dtype=cdt, device=device)
    raise ValueError(f"unsupported coherent Pauli axis {axis!r}")


def _coherent_family_generator(family: str, *, coefficient: float, device: str) -> torch.Tensor:
    r"""Return the Hermitian Pauli-tensor generator H for a coherent family on the
    PURE computational subspace (2x2 for 1-site, 4x4 for 2-site).

    DERIVATION (notation per docs/TWIN.md / docs/METRICS.md):

    M6 coherent_rx_overrotation (COH_RX) — the canonical 1-site example:
      H_M6 = (coeff / 2) * X,    X = [[0,1],[1,0]]  (Nielsen & Chuang Eq. 2.1)
      Convention: R_x(theta) = exp(-i theta X/2) so that eps = coeff * dt_ns is the
      over-rotation angle in radians  (N&C Eq. 4.4-4.7).
      Mechanism ground: Kaufmann-Rojkov-Reiter arXiv:2307.08741 Eq. 2
        H_theta = sum_k theta_k P_k;  the single-qubit theta_X X term IS M6 (COH_RX).
      Error gate: U_M6 = exp(-i H_M6 dt) = RX(eps),  eps = coeff * dt_ns.
      Leading 1-F_e: sin^2(eps/2) = eps^2/4 + O(eps^4)  (METRICS.md /d convention, d=2).

    For two-site families (COH_XX, COH_YY, ..., COH_XX_YY):
      H = (coeff / 4) * sum_{(P,Q) in pairs} (P (x) Q)
      where (x) is the tensor product of 2x2 Pauli operators; the 1/4 = (1/2)^2
      preserves the R_{PQ}(eps)-convention for two-qubit coherent over-rotations.

    M22 coherent_cxx_parasitic_coupling (COH_XX) — 2-site derivation:
      H_M22 = (coeff / 4) * (X (x) X),   X = [[0,1],[1,0]]  (Nielsen & Chuang Eq. 2.1)
      factor 1/4 = (1/2)^2: two-qubit over-rotation convention
        R_{PQ}(eps_cat) = exp(-i (eps_cat/2)(P (x) Q))
        carrier eps = coeff * dt_ns is the per-tensor angle; catalog eps_cat = eps/2
        (error_mechanisms.md line 113 "exp(-i eps XX/2)").
      Mechanism ground:
        - Pure X(x)X as canonical su(4) non-local Cartan axis: Zhang-Vala-Sastry-Whaley
          arXiv:quant-ph/0209120 Eq. 7 (p = span of 9 Pauli-tensor basis elements),
          Eq. 10 (Cartan a = {XX, YY, ZZ}), Eq. 11/16 (canonical form).
        - Pure XX gate written explicitly: Kraus-Cirac arXiv:quant-ph/0011050 Eq. 24
          U_d = e^{-i alpha S_x} = cos(a)*1 - i*sin(a)*(sigma_x (x) sigma_x).
        - Device-physical transverse interaction: Geller-Martinis arXiv:1405.1915 Eq. 57
          delta_H = g * sigma_x (x) sigma_x  (gmon/Xmon tunable-coupler).
      (X(x)X)^2 = I4,  Tr(X(x)X) = 0,  eigenvalues +/-1 each x2.
      Error gate: U_M22 = exp(-i H_M22 dt) = cos(eps/4)*I4 - i*sin(eps/4)*(X(x)X),
                  eps = coeff * dt_ns.
      EXACT 1-F_e (d=4): 1 - |Tr(U_M22)/4|^2 = sin^2(eps/4).
        (Nielsen arXiv:quant-ph/0205035 Eq. 16; Tr(X(x)X)=0 so Tr(U)=4*cos(eps/4).)
      LEADING 1-F_e: ||(eps/4)(X(x)X)||_F^2 / 4 = eps^2/16 + O(eps^4).

    For crosstalk families (COH_CROSSTALK_ZZ):
      H = (coeff / 4) * (Z (x) Z)  — the Z-Z parasitic coupling generator.

    The generator is embedded into the full local_dims space (qubit/qutrit/ququart)
    by ``_embed_coherent_generator``, which pads with the zero generator on leaked
    levels >= 2 (identity on those levels — no leakage drive from Pauli over-rotation).
    """
    fam = str(family).upper()
    coeff = float(coefficient)
    cdt = torch.complex128
    # Mapping from 1q family names to Pauli axes
    _ONE_Q_FAMILY_TO_AXIS = {
        "COH_RX": "X",
        "COH_RY": "Y",
        "COH_RZ": "Z",
    }
    if fam in ONE_SITE_COHERENT_FAMILIES:
        axis = _ONE_Q_FAMILY_TO_AXIS[fam]
        P = _pauli_2level(axis, device=device)
        return (0.5 * coeff) * P
    pairs: tuple[tuple[str, str], ...] = ()
    if fam in TWO_SITE_COHERENT_FAMILIES:
        pairs = (
            (("X", "X"),)
            if fam == "COH_XX"
            else (("Y", "Y"),)
            if fam == "COH_YY"
            else (("Z", "X"),)
            if fam == "COH_ZX"
            else (("X", "X"), ("Y", "Y"))
        )
    elif fam in CROSSTALK_COHERENT_FAMILIES:
        pairs = (("Z", "Z"),)
    out = torch.zeros((4, 4), dtype=cdt, device=device)
    for left_axis, right_axis in pairs:
        Pl = _pauli_2level(left_axis, device=device)
        Pr = _pauli_2level(right_axis, device=device)
        out = out + torch.kron(Pl.contiguous(), Pr.contiguous())
    return (0.25 * coeff) * out


def _embed_coherent_generator(
    family: str,
    *,
    coefficient: float,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    """Embed the Pauli-tensor generator into the term's support Hilbert space using
    the actual local_dims (qubit/qutrit/...)."""
    fam = str(family).upper()
    coeff = float(coefficient)
    cdt = torch.complex128
    if fam in ONE_SITE_COHERENT_FAMILIES:
        if len(support) != 1:
            raise ValueError(f"{fam} requires one-site support, got {support!r}")
        dim = int(local_dims[support[0]])
        if dim < 2:
            raise ValueError(f"{fam} requires local_dim >= 2, got {dim}")
        gen2 = _coherent_family_generator(fam, coefficient=coeff, device=device)
        out = torch.zeros((dim, dim), dtype=cdt, device=device)
        out[:2, :2] = gen2
        return out
    if fam in TWO_SITE_COHERENT_FAMILIES or fam in CROSSTALK_COHERENT_FAMILIES:
        if len(support) != 2:
            raise ValueError(f"{fam} requires two-site support, got {support!r}")
        d0 = int(local_dims[support[0]])
        d1 = int(local_dims[support[1]])
        if d0 < 2 or d1 < 2:
            raise ValueError(f"{fam} requires both local_dims >= 2, got ({d0}, {d1})")
        gen4 = _coherent_family_generator(fam, coefficient=coeff, device=device)
        out = torch.zeros((d0 * d1, d0 * d1), dtype=cdt, device=device)
        for left_in in (0, 1):
            for right_in in (0, 1):
                col = left_in * d1 + right_in
                qcol = left_in * 2 + right_in
                for left_out in (0, 1):
                    for right_out in (0, 1):
                        row = left_out * d1 + right_out
                        qrow = left_out * 2 + right_out
                        out[row, col] = gen4[qrow, qcol]
        return out
    raise ValueError(f"unsupported coherent family {family!r}")


def _one_site_level_exchange_hamiltonian(
    *,
    coefficient: float,
    local_dim: int,
    levels: tuple[int, int],
    device: str,
) -> torch.Tensor:
    dim = int(local_dim)
    left, right = int(levels[0]), int(levels[1])
    if left < 0 or left >= dim or right < 0 or right >= dim:
        raise ValueError(
            "one-site leakage exchange level outside local_dim: "
            f"levels={levels!r} local_dim={local_dim!r}"
        )
    if left == right:
        raise ValueError(f"one-site leakage exchange needs distinct levels: {levels!r}")
    out = torch.zeros((dim, dim), dtype=torch.complex128, device=device)
    out[left, right] = float(coefficient)
    out[right, left] = float(coefficient)
    return out


def _two_site_level_exchange_hamiltonian(
    *,
    coefficient: float,
    dims: tuple[int, int],
    levels: tuple[tuple[int, int], tuple[int, int]],
    device: str,
) -> torch.Tensor:
    d0, d1 = int(dims[0]), int(dims[1])
    left, right = tuple((int(a), int(b)) for a, b in levels)
    for level0, level1 in (left, right):
        if level0 < 0 or level0 >= d0 or level1 < 0 or level1 >= d1:
            raise ValueError(
                "two-site leakage exchange level outside local_dims: "
                f"levels={levels!r} dims={dims!r}"
            )
    left_index = left[0] * d1 + left[1]
    right_index = right[0] * d1 + right[1]
    if left_index == right_index:
        raise ValueError(f"two-site leakage exchange needs distinct levels: {levels!r}")
    out = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
    out[left_index, right_index] = float(coefficient)
    out[right_index, left_index] = float(coefficient)
    return out


def _two_site_conditional_phase_hamiltonian(
    *,
    coefficient: float,
    dims: tuple[int, int],
    family: str,
    device: str,
) -> torch.Tensor:
    d0, d1 = int(dims[0]), int(dims[1])
    out = torch.zeros((d0 * d1, d0 * d1), dtype=torch.complex128, device=device)
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
    raise ValueError(f"unsupported conditional phase family {family!r}")


def _lift_one_site_hamiltonian(
    hamiltonian: torch.Tensor,
    *,
    local_dim: int,
    device: str,
) -> torch.Tensor:
    dim = int(local_dim)
    if dim < 2:
        raise ValueError("local_dim must be >= 2")
    out = torch.zeros((dim, dim), dtype=torch.complex128, device=device)
    out[:2, :2] = torch.as_tensor(hamiltonian, dtype=torch.complex128, device=device)
    return out


def _lift_two_site_hamiltonian(
    hamiltonian: torch.Tensor,
    *,
    dims: tuple[int, int],
    device: str,
) -> torch.Tensor:
    left_dim, right_dim = int(dims[0]), int(dims[1])
    out = torch.zeros((left_dim * right_dim, left_dim * right_dim), dtype=torch.complex128, device=device)
    qham = torch.as_tensor(hamiltonian, dtype=torch.complex128, device=device)
    for left_in in (0, 1):
        for right_in in (0, 1):
            col = left_in * right_dim + right_in
            qcol = left_in * 2 + right_in
            for left_out in (0, 1):
                for right_out in (0, 1):
                    row = left_out * right_dim + right_out
                    qrow = left_out * 2 + right_out
                    out[row, col] = qham[qrow, qcol]
    return out


def _apply_mps_gate(
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
    track_shadow: bool,
) -> None:
    if max_bond is not None and track_shadow:
        from qec_twin.simulator.axis1_qt_mps_execution import _shadow_truncation_event

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
        where=support if len(support) > 1 else support[0],
        contract="auto-mps" if len(support) > 1 else True,
        max_bond=max_bond if len(support) > 1 else None,
        cutoff=0.0,
    )


def _sample_joint_jump_or_nojump(
    mps,
    substep: dict[str, Any],
    *,
    dt_ns: float,
    device: str,
    generator: torch.Generator,
    local_dims: tuple[int, ...],
) -> tuple[Any, dict[str, Any]]:
    collapse_terms = [
        term
        for term in substep.get("terms", ())
        if str(term["kind"]) == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0
    ]
    if not collapse_terms:
        return (
            mps,
            {
                "selected_jump_family": "NO_JUMP",
                "candidate_count": 1,
                "probability_mass": 1.0,
                "probability_mass_residual": 0.0,
            },
        )
    candidates: list[Any] = []
    probabilities: list[float] = []
    families: list[str] = []

    nojump = mps.copy()
    for term in collapse_terms:
        support = tuple(int(q) for q in term["support"])
        if len(support) == 1:
            nojump.gate_(
                _nojump_first_order_kraus(
                    term,
                    dt_ns,
                    local_dim=local_dims[support[0]],
                    device=device,
                ),
                where=support[0],
                contract=True,
            )
        else:  # 2-site joint collapse (M12 Phase-B): apply on the joint support
            nojump.gate_(
                _joint_nojump_first_order_kraus(
                    term, dt_ns, support, local_dims=local_dims, device=device
                ),
                where=support,
                contract="auto-mps",
                max_bond=None,
            )
    p0 = _norm_sq(nojump)
    if p0 > 1.0e-15:
        candidates.append(nojump)
        probabilities.append(float(p0))
        families.append("NO_JUMP")

    for term in collapse_terms:
        support = tuple(int(q) for q in term["support"])
        jump = mps.copy()
        if len(support) == 1:
            jump.gate_(
                (float(dt_ns) ** 0.5)
                * _collapse_operator(term, local_dim=local_dims[support[0]], device=device),
                where=support[0],
                contract=True,
            )
        else:  # 2-site joint collapse (M12 Phase-B)
            jump.gate_(
                (float(dt_ns) ** 0.5)
                * _joint_collapse_operator(term, support, local_dims=local_dims, device=device),
                where=support,
                contract="auto-mps",
                max_bond=None,
            )
        p = _norm_sq(jump)
        if p <= 1.0e-15:
            continue
        candidates.append(jump)
        probabilities.append(float(p))
        families.append(str(term["operator_family"]).upper())
    if not candidates:
        raise ValueError("MCWF microstep has no nonzero no-jump or jump candidate")
    total = float(sum(probabilities))
    index = _sample_index(probabilities, device=device, generator=generator)
    selected = candidates[index]
    selected.multiply_(1.0 / (probabilities[index] ** 0.5), spread_over=1)
    return (
        selected,
        {
            "selected_jump_family": families[index],
            "candidate_count": len(candidates),
            "probability_mass": total,
            "probability_mass_residual": abs(total - 1.0),
        },
    )


def _collapse_operator(
    term: dict[str, Any],
    *,
    local_dim: int,
    device: str,
) -> torch.Tensor:
    family = str(term["operator_family"]).upper()
    coeff = float(term["coefficient"])
    dim = int(local_dim)
    op = torch.zeros((dim, dim), dtype=torch.complex128, device=device)
    if family == "T1":
        op[0, 1] = coeff
        return op
    if family == "T1_UP":
        op[1, 0] = coeff
        return op
    if family in {"T2", "RD"}:
        op[1, 1] = coeff
        return op
    if family == "LEAK_SEEP_21":
        if dim < 3:
            raise ValueError("LEAK_SEEP_21 requires local_dim >= 3")
        op[1, 2] = coeff
        return op
    if family == "LEAK_HEAT_12":
        if dim < 3:
            raise ValueError("LEAK_HEAT_12 requires local_dim >= 3")
        op[2, 1] = coeff
        return op
    raise ValueError(f"unsupported MCWF collapse family {family!r}")


def _nojump_first_order_kraus(
    term: dict[str, Any],
    dt_ns: float,
    *,
    local_dim: int,
    device: str,
) -> torch.Tensor:
    c = _collapse_operator(term, local_dim=local_dim, device=device)
    ident = torch.eye(int(local_dim), dtype=torch.complex128, device=device)
    return ident - 0.5 * float(dt_ns) * (c.conj().transpose(-1, -2) @ c)


def _joint_collapse_operator(
    term: dict[str, Any],
    support: tuple[int, ...],
    *,
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    """2-site JOINT (collective/Dicke) collapse operator (M12 Phase-B).

    CORR_RELAX = correlated_two_qubit_relaxation: ``c = coeff * (sigma^- (x) I + I (x) sigma^-)``,
    ``coeff = sqrt(gamma_corr)``, ``sigma^- = |0><1|`` on the computational {0,1} block, ZERO on leaked
    levels >= 2 (same embed discipline as the coherent two-site families). Built on the
    ``(d_i * d_j)`` joint Hilbert space of ``support=(i, j)`` in the carrier's qubit-0-major kron order.
    Grounded in M12 Phase-A (`cert_m12_correlated_relaxation.py`) — the channel this trajectory seam
    must reproduce under Monte-Carlo.
    """
    family = str(term["operator_family"]).upper()
    coeff = float(term["coefficient"])
    if len(support) != 2:
        raise ValueError(f"two-site collapse {family!r} requires two-site support, got {support!r}")
    cdt = torch.complex128
    di = int(local_dims[support[0]])
    dj = int(local_dims[support[1]])
    if family == "CORR_RELAX":
        sm_i = torch.zeros((di, di), dtype=cdt, device=device)
        sm_i[0, 1] = 1.0  # |0><1| on site i (computational block; zero on leaked levels >= 2)
        sm_j = torch.zeros((dj, dj), dtype=cdt, device=device)
        sm_j[0, 1] = 1.0
        eye_i = torch.eye(di, dtype=cdt, device=device)
        eye_j = torch.eye(dj, dtype=cdt, device=device)
        return coeff * (
            torch.kron(sm_i.contiguous(), eye_j.contiguous())
            + torch.kron(eye_i.contiguous(), sm_j.contiguous())
        )
    raise ValueError(f"unsupported MCWF two-site collapse family {family!r}")


def _joint_nojump_first_order_kraus(
    term: dict[str, Any],
    dt_ns: float,
    support: tuple[int, ...],
    *,
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    """2-site first-order no-jump Kraus ``I - 1/2 c^dag c dt`` for a joint collapse (M12 Phase-B)."""
    c = _joint_collapse_operator(term, support, local_dims=local_dims, device=device)
    d = int(c.shape[0])
    ident = torch.eye(d, dtype=torch.complex128, device=device)
    return ident - 0.5 * float(dt_ns) * (c.conj().transpose(-1, -2) @ c)


def _basis_vector(dim: int, level: int) -> np.ndarray:
    d = int(dim)
    l = int(level)
    out = np.zeros(d, dtype=np.complex128)
    out[l] = 1.0
    return out


def _lift_one_site_gate(
    gate: torch.Tensor,
    *,
    local_dim: int,
    device: str,
) -> torch.Tensor:
    dim = int(local_dim)
    if dim < 2:
        raise ValueError("local_dim must be >= 2")
    out = torch.eye(dim, dtype=torch.complex128, device=device)
    out[:2, :2] = torch.as_tensor(gate, dtype=torch.complex128, device=device)
    return out


def _lift_two_site_gate(
    gate: torch.Tensor,
    *,
    dims: tuple[int, int],
    device: str,
) -> torch.Tensor:
    left_dim, right_dim = int(dims[0]), int(dims[1])
    out = torch.eye(left_dim * right_dim, dtype=torch.complex128, device=device)
    qgate = torch.as_tensor(gate, dtype=torch.complex128, device=device)
    for left_in in (0, 1):
        for right_in in (0, 1):
            col = left_in * right_dim + right_in
            qcol = left_in * 2 + right_in
            for left_out in (0, 1):
                for right_out in (0, 1):
                    row = left_out * right_dim + right_out
                    qrow = left_out * 2 + right_out
                    out[row, col] = qgate[qrow, qcol]
    return out


def _zz_phase_gate(
    *,
    coefficient: float,
    dt_ns: float,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
    device: str,
) -> torch.Tensor:
    if len(support) != 2:
        raise ValueError(f"ZZ/FSIM_PHASE requires two-site support, got {support!r}")
    d0 = int(local_dims[support[0]])
    d1 = int(local_dims[support[1]])
    diag = torch.ones(d0 * d1, dtype=torch.complex128, device=device)
    phase = complex(np.exp(-1j * float(coefficient) * float(dt_ns)))
    diag[1 * d1 + 1] = phase
    return torch.diag(diag)


def _leak_exchange_12_gate(
    *,
    coefficient: float,
    dt_ns: float,
    local_dim: int,
    device: str,
) -> torch.Tensor:
    dim = int(local_dim)
    if dim < 3:
        raise ValueError("LEAK_EXCHANGE_12 requires local_dim >= 3")
    theta = float(coefficient) * float(dt_ns)
    out = torch.eye(dim, dtype=torch.complex128, device=device)
    c = math.cos(theta)
    s = math.sin(theta)
    out[1, 1] = c
    out[2, 2] = c
    out[1, 2] = -1.0j * s
    out[2, 1] = -1.0j * s
    return out


def _two_site_level_exchange_gate(
    *,
    coefficient: float,
    dt_ns: float,
    dims: tuple[int, int],
    levels: tuple[tuple[int, int], tuple[int, int]],
    device: str,
) -> torch.Tensor:
    d0, d1 = int(dims[0]), int(dims[1])
    left, right = tuple((int(a), int(b)) for a, b in levels)
    for level0, level1 in (left, right):
        if level0 < 0 or level0 >= d0 or level1 < 0 or level1 >= d1:
            raise ValueError(
                "two-site leakage exchange level outside local_dims: "
                f"levels={levels!r} dims={dims!r}"
            )
    left_index = left[0] * d1 + left[1]
    right_index = right[0] * d1 + right[1]
    if left_index == right_index:
        raise ValueError(f"two-site leakage exchange needs distinct levels: {levels!r}")
    theta = float(coefficient) * float(dt_ns)
    out = torch.eye(d0 * d1, dtype=torch.complex128, device=device)
    c = math.cos(theta)
    s = math.sin(theta)
    out[left_index, left_index] = c
    out[right_index, right_index] = c
    out[left_index, right_index] = -1.0j * s
    out[right_index, left_index] = -1.0j * s
    return out


_SUPPORTED_MCWF_MEASUREMENT_BASES = ("X", "Z")


def _aggregating_measurement_boundary(substep: dict[str, Any]) -> dict[str, Any]:
    """Aggregate ALL operation_records of a measurement substep into a single ordered
    boundary: ``measurement_keys``, ``measurement_targets``, and per-target
    ``measurement_bases`` (in operation/record then per-record-target order).

    This is the multi-record generalisation of the shared single-record
    ``_measurement_boundary`` (``axis1_qt_mps_execution._measurement_boundary``), used by
    the MCWF execute loop and the dense certification. The shared single-record helper is
    left untouched so the qt_mps callers keep their byte-identical single-record contract.

    Distinct-qubit measurements within a terminal readout substep commute, so the
    per-target rotate-then-sample sequence the MCWF sampler applies in this order is exact.
    """
    keys: list[str] = []
    targets: list[int] = []
    bases: list[str] = []
    for op in substep.get("operation_records", ()):
        op_keys = [str(key) for key in op.get("measurement_keys", ())]
        op_targets = [int(q) for q in op.get("targets", ())]
        if len(op_keys) != len(op_targets):
            raise ValueError(
                "measurement operation keys do not match targets in aggregating boundary: "
                f"keys={op_keys!r} targets={op_targets!r}"
            )
        basis = str(op.get("basis", "Z")).upper()
        keys.extend(op_keys)
        targets.extend(op_targets)
        bases.extend([basis] * len(op_targets))
    return {
        "measurement_keys": keys,
        "measurement_targets": targets,
        "measurement_bases": bases,
    }


def _x_basis_rotation_local(local_dim: int, *, device: str) -> torch.Tensor:
    """The Hadamard X<->Z basis rotation embedded in the local (qudit) space: the 2x2
    H = (1/sqrt2)[[1,1],[1,-1]] on the computational {|0>,|1>} block and identity on every
    leaked level >= 2 (a basis rotation must NOT touch leaked populations). Applying H then
    Z-projecting is equivalent to projecting onto the X eigenbasis on the qubit block.
    """
    dim = int(local_dim)
    if dim < 2:
        raise ValueError(f"X-basis rotation requires local_dim >= 2, got {dim}")
    inv = 1.0 / math.sqrt(2.0)
    out = torch.eye(dim, dtype=torch.complex128, device=device)
    out[0, 0] = inv
    out[0, 1] = inv
    out[1, 0] = inv
    out[1, 1] = -inv
    return out


def _sample_measurement_multilevel(
    mps,
    *,
    targets: Sequence[int],
    bases: Sequence[str] | None = None,
    local_dims: tuple[int, ...],
    device: str,
    generator: torch.Generator,
    leaked_readout_b: float,
) -> tuple[tuple[int, ...], tuple[int, ...], Any]:
    state = mps
    levels: list[int] = []
    bits: list[int] = []
    target_tuple = tuple(int(q) for q in targets)
    if bases is None:
        basis_tuple: tuple[str, ...] = tuple("Z" for _ in target_tuple)
    else:
        basis_tuple = tuple(str(b).upper() for b in bases)
    if len(basis_tuple) != len(target_tuple):
        raise ValueError(
            f"measurement bases {basis_tuple!r} do not match targets {target_tuple!r}"
        )
    for target, basis in zip(target_tuple, basis_tuple, strict=True):
        if basis not in _SUPPORTED_MCWF_MEASUREMENT_BASES:
            raise ValueError(
                "MCWF/MPS multi-record measurement supports only X/Z bases (bounded "
                f"d3/5q slice); got basis {basis!r}"
            )
        if basis == "X":
            # Terminal measurement: rotate the X-target site into the Z eigenbasis with H
            # (no rotate-back needed). Distinct-qubit targets commute, so doing this per
            # target in sequence before its own Z-level sampling is exact.
            state = state.copy()
            state.gate_(
                _x_basis_rotation_local(local_dims[target], device=device),
                where=int(target),
                contract=True,
            )
        level, state = _sample_one_site_level(
            state,
            site=target,
            local_dim=local_dims[target],
            device=device,
            generator=generator,
        )
        levels.append(level)
        bits.append(
            _sample_level_bit(
                level,
                leaked_readout_b=float(leaked_readout_b),
                device=device,
                generator=generator,
            )
        )
    return tuple(levels), tuple(bits), state


def _sample_one_site_level(
    mps,
    *,
    site: int,
    local_dim: int,
    device: str,
    generator: torch.Generator,
) -> tuple[int, Any]:
    candidates: list[Any] = []
    probabilities: list[float] = []
    for level in range(int(local_dim)):
        candidate = mps.copy()
        candidate.gate_(
            _level_projector(level, local_dim=local_dim, device=device),
            where=int(site),
            contract=True,
        )
        p = _norm_sq(candidate)
        candidates.append(candidate)
        probabilities.append(float(max(p, 0.0)))
    if sum(probabilities) <= 0.0:
        raise ValueError("cannot sample a measurement with zero total Born weight")
    index = _sample_index(probabilities, device=device, generator=generator)
    selected = candidates[index]
    selected.multiply_(1.0 / (probabilities[index] ** 0.5), spread_over=1)
    return int(index), selected


def _sample_level_bit(
    level: int,
    *,
    leaked_readout_b: float,
    device: str,
    generator: torch.Generator,
) -> int:
    l = int(level)
    if l <= 0:
        return 0
    if l == 1:
        return 1
    b = float(leaked_readout_b)
    if b <= 0.0:
        return 0
    if b >= 1.0:
        return 1
    draw = torch.rand((), dtype=torch.float64, device=device, generator=generator)
    return int(bool(draw < b))


def _level_projector(level: int, *, local_dim: int, device: str) -> torch.Tensor:
    op = torch.zeros(
        (int(local_dim), int(local_dim)),
        dtype=torch.complex128,
        device=device,
    )
    op[int(level), int(level)] = 1.0
    return op


def _sample_reset_for_operations_multilevel(
    mps,
    substep: dict[str, Any],
    *,
    local_dims: tuple[int, ...],
    device: str,
    generator: torch.Generator,
) -> Any:
    state = mps
    for op in substep.get("operation_records", ()):
        basis = _reset_basis(str(op.get("name", "")))
        if basis is None:
            continue
        for target in op.get("targets", ()):
            site = int(target)
            dim = int(local_dims[site])
            level, state = _sample_one_site_level(
                state,
                site=site,
                local_dim=dim,
                device=device,
                generator=generator,
            )
            state.gate_(
                _reset_operator(
                    target_vector=_reset_target_vector(
                        basis,
                        local_dim=dim,
                        device=device,
                    ),
                    from_level=level,
                    local_dim=dim,
                    device=device,
                ),
                where=site,
                contract=True,
            )
            norm = _norm_sq(state)
            if norm > 0.0:
                state.multiply_(1.0 / (norm ** 0.5), spread_over=1)
    return state


def _reset_target_vector(
    basis: str,
    *,
    local_dim: int | None,
    device: str,
) -> torch.Tensor:
    dim = 2 if local_dim is None else int(local_dim)
    out = torch.zeros(dim, dtype=torch.complex128, device=device)
    b = str(basis).upper()
    if b == "Z":
        out[0] = 1.0
    elif b == "X":
        inv = 1.0 / math.sqrt(2.0)
        out[0] = inv
        out[1] = inv
    elif b == "Y":
        inv = 1.0 / math.sqrt(2.0)
        out[0] = inv
        out[1] = 1.0j * inv
    else:
        raise ValueError(f"unsupported reset basis {basis!r}")
    return out


def _reset_operator(
    *,
    target_vector: torch.Tensor,
    from_level: int,
    local_dim: int,
    device: str,
) -> torch.Tensor:
    op = torch.zeros(
        (int(local_dim), int(local_dim)),
        dtype=torch.complex128,
        device=device,
    )
    op[:, int(from_level)] = torch.as_tensor(
        target_vector,
        dtype=torch.complex128,
        device=device,
    )
    return op


def _apply_measurement_reset_if_requested_multilevel(
    mps,
    substep: dict[str, Any],
    *,
    outcome_levels: tuple[int, ...],
    local_dims: tuple[int, ...],
    device: str,
) -> Any:
    records = list(substep.get("operation_records", ()))
    if len(records) != 1:
        return mps
    op = records[0]
    if not bool(op.get("reset_after_measurement", False)):
        return mps
    reset_basis = str(op.get("basis", "Z")).upper()
    if reset_basis not in {"Z", "X", "Y"}:
        raise ValueError(
            "MCWF/MPS multilevel measurement reset supports Pauli measurement basis only"
        )
    # Asymmetry note (single-record reset-after-measurement only; the d3/5q terminal readout
    # has reset_after=None so this path is inert there): the carrier accepts X/Y reset here,
    # but the dense LEVEL oracle only CERTIFIES Z-basis post-measurement reset (it raises
    # level_oracle_measurement_reset_supports_z_basis_only otherwise). So an X/Y reset-after
    # run EXECUTES but comes back honestly uncertified (executed=False) -- never a false pass.
    targets = tuple(int(q) for q in op.get("targets", ()))
    state = mps
    for site, level in zip(targets, outcome_levels, strict=True):
        dim = int(local_dims[site])
        state.gate_(
            _reset_operator(
                target_vector=_reset_target_vector(
                    str(reset_basis),
                    local_dim=dim,
                    device=device,
                ),
                from_level=int(level),
                local_dim=dim,
                device=device,
            ),
            where=site,
            contract=True,
        )
        norm = _norm_sq(state)
        if norm > 0.0:
            state.multiply_(1.0 / (norm ** 0.5), spread_over=1)
    return state


def _mcwf_mps_truncation_ledger(
    *,
    max_bond: int | None,
    local_dims: tuple[int, ...],
    max_observed_bond: int,
    truncation_events: list[dict[str, Any]],
) -> dict[str, Any]:
    if all(dim == 2 for dim in local_dims):
        return _truncation_ledger(
            max_bond=max_bond,
            num_sites=len(local_dims),
            max_observed_bond=max_observed_bond,
            truncation_events=truncation_events,
        )
    exact_bond = _exact_mixed_dim_bond_sufficient(local_dims)
    if max_bond is not None:
        raise ValueError("finite-bond multilevel ledger should fail closed before execution")
    return {
        "explicit_truncation_requested": False,
        "local_dims": list(local_dims),
        "exact_bond_dimension_sufficient": exact_bond,
        "exact_bond_policy": "unbounded_no_explicit_cap_mixed_local_dims",
        "accepted_as_exact_bond_representation": True,
        "discarded_weight_ledger_complete": True,
        "discarded_weight_sum": 0.0,
        "worst_cut_discarded_weight": 0.0,
        "n_truncating_ops": 0,
        "max_observed_bond": int(max_observed_bond),
        "ledger_scope": "no_explicit_mps_truncation_requested_mixed_local_dims",
        "epistemic_class": "a/c",
    }


def _exact_mixed_dim_bond_sufficient(local_dims: tuple[int, ...]) -> int:
    if len(local_dims) <= 1:
        return max(1, int(local_dims[0]) if local_dims else 1)
    out = 1
    for cut in range(1, len(local_dims)):
        left = math.prod(int(dim) for dim in local_dims[:cut])
        right = math.prod(int(dim) for dim in local_dims[cut:])
        out = max(out, min(int(left), int(right)))
    return int(out)


def _first_order_mass_residual_blocks(
    program: dict[str, Any],
    *,
    local_dims: tuple[int, ...],
    microstep_count: int,
    device: str,
    budget: float,
) -> list[dict[str, Any]]:
    """Deterministic preflight against a grossly non-CPTP first-order MCWF step.

    The no-jump Kraus ``K0 = I - 1/2 c^dag c dt`` leaks probability mass; the per-microstep residual
    is ``1/4 dt^2 <(sum_k c_k^dag c_k)^2>``. Its state-independent worst case is bounded by
    ``1/4 dt_micro^2 (sum_k ||c_k^dag c_k||_op)^2`` (operator norm; embedding preserves it, so the
    per-operator norms can be summed on each operator's own small support). When that bound exceeds
    ``budget`` the requested ``microstep_count`` is too coarse; return a blocked-substep entry that
    reports the minimum ``microstep_count`` that resolves it. Empty when every MCWF substep is within
    budget. The same operator builders the sampler uses are called here, so the bound matches the
    execution path exactly.
    """
    out: list[dict[str, Any]] = []
    m = int(microstep_count)
    for substep_index, substep in enumerate(program["program"]["substeps"]):
        collapse_terms = [
            term
            for term in substep.get("terms", ())
            if str(term["kind"]) == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0
        ]
        if not collapse_terms:
            continue
        dt_sub = float(substep["dt_ns"])
        dt_micro = dt_sub / float(m)
        norm_sum = 0.0
        for term in collapse_terms:
            support = tuple(int(q) for q in term["support"])
            if len(support) == 1:
                c = _collapse_operator(term, local_dim=local_dims[support[0]], device=device)
            else:
                c = _joint_collapse_operator(term, support, local_dims=local_dims, device=device)
            cdc = c.conj().transpose(-1, -2) @ c
            norm_sum += float(torch.linalg.eigvalsh(cdc).max().real)
        if norm_sum <= 0.0:
            continue
        bound = 0.25 * (dt_micro ** 2) * (norm_sum ** 2)
        if bound > float(budget):
            required = int(math.ceil(dt_sub * norm_sum / (2.0 * float(budget) ** 0.5)))
            out.append(
                {
                    "substep_index": int(substep_index),
                    "substep_kind": str(substep.get("substep_kind", "")),
                    "reason": (
                        "mcwf_first_order_mass_residual_exceeds_budget:"
                        f"{bound:.3e}>{float(budget):.3e}"
                    ),
                    "first_order_mass_residual_bound": float(bound),
                    "mass_residual_budget": float(budget),
                    "microstep_count": m,
                    "required_microstep_count": int(max(required, m + 1)),
                }
            )
    return out


def _unsupported_substeps(
    program: dict[str, Any],
    *,
    local_dims: tuple[int, ...],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for substep in program["program"]["substeps"]:
        kind = str(substep["substep_kind"])
        if kind not in {"idle", "one_qubit_gate", "two_qubit_gate", "measurement", "reset"}:
            out.append(_unsupported(substep, "substep_kind_not_supported_by_mcwf_mps"))
            continue
        if substep.get("dt_ns") is None and kind not in {"measurement", "reset"}:
            out.append(_unsupported(substep, "positive_duration_required_for_mcwf_evolution"))
            continue
        for term in substep.get("terms", ()):
            term_kind = str(term["kind"])
            family = str(term["operator_family"]).upper()
            support = tuple(int(q) for q in term.get("support", ()))
            if family in _ONE_SITE_LEAKAGE_HAMILTONIAN_FAMILIES | _LEAKAGE_COLLAPSE_FAMILIES:
                if len(support) != 1:
                    out.append(_unsupported(substep, f"unsupported_mcwf_leakage_support:{family}"))
                    break
                if local_dims[support[0]] < 3:
                    out.append(_unsupported(substep, f"mcwf_leakage_requires_local_dim_at_least_3:{family}"))
                    break
            elif family in _TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS:
                if len(support) != 2:
                    out.append(_unsupported(substep, f"unsupported_mcwf_leakage_support:{family}"))
                    break
                required = _TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS[family]
                dims = (local_dims[support[0]], local_dims[support[1]])
                max_left = max(int(level[0]) for level in required)
                max_right = max(int(level[1]) for level in required)
                if dims[0] <= max_left or dims[1] <= max_right:
                    out.append(_unsupported(substep, f"mcwf_leakage_requires_declared_local_levels:{family}"))
                    break
            elif family in _TWO_SITE_CONDITIONAL_PHASE_FAMILIES:
                if len(support) != 2:
                    out.append(_unsupported(substep, f"unsupported_mcwf_leakage_support:{family}"))
                    break
                dims = (local_dims[support[0]], local_dims[support[1]])
                if family == "LEAK_COND_PHASE_LEFT2_RIGHTZ" and dims[0] < 3:
                    out.append(_unsupported(substep, f"mcwf_leakage_requires_declared_local_levels:{family}"))
                    break
                if family == "LEAK_COND_PHASE_LEFTZ_RIGHT2" and dims[1] < 3:
                    out.append(_unsupported(substep, f"mcwf_leakage_requires_declared_local_levels:{family}"))
                    break
            elif family.startswith("LEAK_"):
                out.append(_unsupported(substep, f"unsupported_mcwf_leakage_family:{family}"))
                break
            if term_kind == "collapse" and family not in {
                "T1",
                "T1_UP",
                "T2",
                "RD",
                "LEAK_SEEP_21",
                "LEAK_HEAT_12",
                "CORR_RELAX",  # M12 Phase-B: 2-site joint (collective/Dicke) collapse
            }:
                out.append(_unsupported(substep, f"unsupported_mcwf_collapse_family:{family}"))
                break
            if (
                term_kind == "collapse"
                and family in TWO_SITE_COLLAPSE_FAMILIES
                and len(support) != 2
            ):
                out.append(
                    _unsupported(substep, f"two_site_collapse_requires_two_site_support:{family}")
                )
                break
            if (
                term_kind == "hamiltonian"
                and family not in _ONE_SITE_LEAKAGE_HAMILTONIAN_FAMILIES
                and family not in _TWO_SITE_LEAKAGE_HAMILTONIAN_LEVELS
                and family not in _TWO_SITE_CONDITIONAL_PHASE_FAMILIES
                and not _is_supported_hamiltonian_term(term)
            ):
                out.append(_unsupported(substep, f"unsupported_mcwf_hamiltonian_family:{family}"))
                break
            if term_kind == "measurement_boundary":
                continue
            if term_kind == "instrument" and family in {"RESET_Z", "RESET_X", "RESET_Y"}:
                continue
            if term_kind not in {"hamiltonian", "collapse", "measurement_boundary", "instrument"}:
                out.append(_unsupported(substep, f"unsupported_mcwf_term_kind:{term_kind}"))
                break
        if kind == "measurement":
            records = list(substep.get("operation_records", ()))
            # Multi-record terminal readout (e.g. the d3 XZZX 9-qubit data readout in mixed
            # X/Z basis) is supported: every operation_record may carry its own basis, and
            # distinct-qubit targets commute. Only X and Z are in this bounded slice;
            # anything else (Y, ...) fails closed.
            for record in records:
                basis = str(record.get("basis", "Z")).upper()
                if basis not in _SUPPORTED_MCWF_MEASUREMENT_BASES:
                    out.append(
                        _unsupported(
                            substep,
                            "mcwf_mps_measurement_supports_x_or_z_basis_only",
                        )
                    )
                    break
        if kind == "reset":
            for op in substep.get("operation_records", ()):
                if _reset_basis(str(op.get("name", ""))) is None:
                    out.append(_unsupported(substep, "mcwf_mps_first_slice_supports_pauli_reset_only"))
                    break
    return out


def _substep_has_mcwf_terms(substep: dict[str, Any]) -> bool:
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        if kind == "hamiltonian":
            return True
        if kind == "collapse" and abs(float(term.get("coefficient", 0.0))) > 0.0:
            return True
    return False


def _restricted_acceptance_policy(
    *,
    execution: dict[str, Any],
    rng_seed: int | None,
    trajectory_count: int,
) -> dict[str, Any]:
    residual = float(execution["total_probability_residual"])
    residual_ok = residual <= _TOTAL_PROBABILITY_RESIDUAL_GATE
    seed_explicit = rng_seed is not None
    accepted = bool(residual_ok and seed_explicit)
    blockers: list[str] = []
    if not seed_explicit:
        blockers.append("sampled_trajectory_rng_seed_not_explicit")
    if not residual_ok:
        blockers.append("total_probability_residual_exceeds_gate")
    blockers.extend(
        [
            "production_error_control_policy_not_established",
            "multilevel_leakage_error_control_not_established",
            "finite_step_error_bound_not_established",
        ]
    )
    return {
        "schema": "qec_twin.simulator.axis1_mcwf_mps_restricted_acceptance_policy.v1",
        "policy_role": "restricted_execution_acceptance_not_metric",
        "accepted_for_restricted_execution": accepted,
        "accepted_for_sampled_execution_evidence": bool(accepted),
        "accepted_for_exact_dense_probability_evidence": False,
        "accepted_for_production_scalable_backend": False,
        "blocked_reason": None if accepted else blockers[0],
        "trajectory": {
            "mode": "sampled_fixed_microstep_mcwf_trajectories",
            "trajectory_count": int(trajectory_count),
            "rng_seed": None if rng_seed is None else int(rng_seed),
            "rng_seed_required_for_acceptance": True,
            "rng_seed_was_explicit": seed_explicit,
            "single_trajectory_density_claim": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        },
        "finite_step": {
            "exact_summed_lindbladian_claim": False,
            "accepted_as_error_bound": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "probability": {
            "total_probability_residual": residual,
            "total_probability_residual_gate": _TOTAL_PROBABILITY_RESIDUAL_GATE,
            "gate_role": "heuristic_execution_sanity_gate_not_metric",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "production_blockers": blockers,
        "scored_quantity_policy": "policy ledger only; no new scored quantity",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }


def _blocked_acceptance_policy(
    *,
    blocked_reason: str,
    rng_seed: int | None,
    trajectory_count: int,
) -> dict[str, Any]:
    return {
        "schema": "qec_twin.simulator.axis1_mcwf_mps_restricted_acceptance_policy.v1",
        "policy_role": "restricted_execution_acceptance_not_metric",
        "accepted_for_restricted_execution": False,
        "accepted_for_sampled_execution_evidence": False,
        "accepted_for_exact_dense_probability_evidence": False,
        "accepted_for_production_scalable_backend": False,
        "blocked_reason": str(blocked_reason),
        "trajectory": {
            "mode": "sampled_fixed_microstep_mcwf_trajectories",
            "trajectory_count": int(trajectory_count),
            "rng_seed": None if rng_seed is None else int(rng_seed),
            "rng_seed_required_for_acceptance": True,
            "rng_seed_was_explicit": rng_seed is not None,
            "single_trajectory_density_claim": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        },
        "production_blockers": [
            str(blocked_reason),
            "production_error_control_policy_not_established",
        ],
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }


def _normalize_local_dims(
    local_dims: Sequence[int] | None,
    *,
    num_sites: int,
) -> tuple[int, ...]:
    if local_dims is None:
        return tuple(2 for _ in range(int(num_sites)))
    dims = tuple(int(dim) for dim in local_dims)
    if len(dims) != int(num_sites):
        raise ValueError(f"local_dims must have length {int(num_sites)}, got {len(dims)}")
    if any(dim < 2 for dim in dims):
        raise ValueError(f"local_dims entries must be >= 2, got {dims!r}")
    return dims


def _normalize_initial_levels(
    initial_levels: Sequence[int] | None,
    *,
    local_dims: tuple[int, ...],
) -> tuple[int, ...]:
    if initial_levels is None:
        return tuple(0 for _ in local_dims)
    levels = tuple(int(level) for level in initial_levels)
    if len(levels) != len(local_dims):
        raise ValueError(
            f"initial_levels must have length {len(local_dims)}, got {len(levels)}"
        )
    for level, dim in zip(levels, local_dims, strict=True):
        if level < 0 or level >= dim:
            raise ValueError(f"initial level {level} outside local dimension {dim}")
    return levels


def _normalize_leaked_readout_b(value: float) -> float:
    b = float(value)
    if not 0.0 <= b <= 1.0:
        raise ValueError("leaked_readout_b must lie in [0, 1]")
    return b


def _normalize_finite_step_order(value: str) -> str:
    order = str(value)
    if order not in _FINITE_STEP_ORDERS:
        allowed = ", ".join(_FINITE_STEP_ORDERS)
        raise ValueError(f"finite_step_order must be one of: {allowed}")
    return order


def _mcwf_finite_step_policy_name(order: str) -> str:
    step_order = _normalize_finite_step_order(order)
    if step_order == _FINITE_STEP_ORDER_STRANG:
        return "connected_support_cluster_hamiltonian_sum_strang_mcwf_split_v2"
    return "connected_support_cluster_hamiltonian_sum_first_order_mcwf_split_v2"


def _unsupported(substep: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "substep_id": str(substep["substep_id"]),
        "substep_kind": str(substep["substep_kind"]),
        "reason": str(reason),
    }


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


def _contract_summary(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": contract.get("schema"),
        "content_hash": contract.get("content_hash"),
        "representability": contract.get("representability"),
        "backend_contract": contract.get("backend_contract"),
        "contract_valid": bool(contract.get("contract_valid")),
        "contract_manifest_implementation_status": contract.get(
            "implementation_status"
        ),
        "execution_manifest_status": "fixed_microstep_local_dims_execution_or_fail_closed",
        "claims_production_scalable_backend": bool(
            contract.get("claims_production_scalable_backend", False)
        ),
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
    "AXIS1_MCWF_MPS_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_MCWF_MPS_EXECUTION_REPRESENTABILITY",
    "AXIS1_MCWF_MPS_EXECUTION_SCHEMA",
    "axis1_mcwf_mps_state_record_execution_manifest",
]

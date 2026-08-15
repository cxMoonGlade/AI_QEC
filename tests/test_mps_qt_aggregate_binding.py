"""Corruption firewall for QT/MPS sweep and aggregate request binding."""

from __future__ import annotations

import copy
from typing import Any, Callable

import pytest


def _measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=2)
    builder.measure((0, 1), key=("m0", "m1"), duration_ns=1.0)
    return circuit_ir_to_substep_schedule(builder.build())


def _unsupported_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mx", basis="X")
    return circuit_ir_to_substep_schedule(builder.build())


def _rehash(qt: Any, payload: dict[str, Any]) -> dict[str, Any]:
    payload["content_hash"] = qt._stable_payload_hash(payload)
    return payload


def _dense_record_oracle_payload(
    qt: Any,
    schedule: Any,
    *,
    device: str,
) -> dict[str, Any]:
    layout = qt.axis1_record_layout_from_schedule(schedule)
    selection_plan = qt.build_axis1_schedule_selection_plan(schedule)
    selection_layers = qt.axis1_selection_layers_in_schedule_order(
        schedule,
        selection_plan.selections,
        consumer_name="Axis-1 selected-window evidence",
    )
    records = [
        list(record)
        for record in qt.materialize_binary_records(layout.measurement_width)
    ]
    probabilities = [1.0] + [0.0] * (len(records) - 1)
    projected = qt.project_axis1_xor_records(layout, records)
    instrument = qt.Axis1ReadoutResetInstrumentSpec().to_manifest()
    applied_layers = [
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
    applied_steps = []
    for layer_index, layer in enumerate(selection_layers):
        for selection in layer.selections:
            lowered_mechanisms = [
                {
                    "name": name,
                    "generator_kind": (
                        "hamiltonian"
                        if name in {"DR", "ZZ", "FSIM_SWAP", "FSIM_PHASE"}
                        else "collapse"
                    ),
                    "coefficient": 0.0,
                    "support": (
                        [1]
                        if name.endswith("_B")
                        else list(range(len(selection.participant)))
                    ),
                    "epistemic_class": "c",
                }
                for name in selection.primitive_names
            ]
            applied_steps.append(
                {
                    "application_index": len(applied_steps),
                    "parallel_layer_index": layer_index,
                    "selection_id": selection.selection_id,
                    "substep_id": selection.substep_id,
                    "row_kind": selection.row_kind,
                    "participant": list(selection.participant),
                    "coupling_edges": [
                        list(edge) for edge in selection.coupling_edges
                    ],
                    "primitive_names": list(selection.primitive_names),
                    "mechanism_pair": list(selection.mechanism_pair),
                    "context_mechanisms": list(selection.context_mechanisms),
                    "ideal_controls": [],
                    "lowered_mechanisms": lowered_mechanisms,
                    "dt_ns": float(selection.dt_ns_nominal),
                    "channel_assembly": {
                        "assembled_by": (
                            "error_coupling_simulator.carrier.joint_lindbladian."
                            "assemble_substep_channel"
                        ),
                        "assembly_semantics": "single_joint_generator_expm",
                        "contains_ideal_control_hamiltonian": False,
                        "ideal_control_names": [],
                        "contains_serialized_channel_payload": False,
                        "num_kraus": 1,
                        "dimension": int(2 ** schedule.num_qubits),
                        "factorization": (
                            "coupling_component_tensor_product_exact"
                        ),
                        "component_local_qubits": [
                            list(range(len(selection.participant)))
                        ],
                        "component_dimensions": [
                            int(2 ** len(selection.participant))
                        ],
                        "component_num_kraus": [1],
                    },
                }
            )
    detector_records = [list(row) for row in projected.detector_records]
    logical_records = [list(row) for row in projected.observable_records]

    def marginals(rows: list[list[int]]) -> list[float]:
        width = len(rows[0]) if rows else 0
        return [
            sum(
                probability * row[column]
                for row, probability in zip(rows, probabilities, strict=True)
            )
            for column in range(width)
        ]

    measurement_bases = sorted(set(layout.measurement_bases))
    record_evidence = {
        "initial_state": "computational_zero_density_matrix",
        "device": qt.normalize_mps_device(device),
        "dtype": "complex128",
        "num_qubits": int(schedule.num_qubits),
        "applied_channel_count": len(applied_steps),
        "application_semantics": (
            "schedule_order_selected_joint_channels_with_parallel_disjoint_or_union_support_layers_then_measurements"
        ),
        "same_substep_window_semantics": (
            "selected windows sharing a substep must either be qubit-disjoint or represented "
            "as a single union-support joint channel; overlapping selected windows fail closed"
        ),
        "measurement_basis": "Z" if measurement_bases == ["Z"] else "mixed_pauli",
        "measurement_bases": measurement_bases,
        "measurement_basis_semantics": (
            "X/Y measurements and resets are implemented by exact basis rotation "
            "before Z-branch enumeration and rotation back afterward"
        ),
        "reset_steps": qt._dense_record_expected_reset_steps(schedule),
        "readout_reset_instrument_spec": instrument,
        "readout_assignment_steps": [],
        "measurement_keys": list(layout.measurement_keys),
        "measurement_steps": qt._dense_record_expected_measurement_steps(schedule),
        "measurement_records": records,
        "record_probabilities": probabilities,
        "record_count": len(records),
        "total_probability": 1.0,
        "total_probability_residual": 0.0,
        "total_probability_residual_threshold": 1.0e-8,
        "applied_layers": applied_layers,
        "applied_steps": applied_steps,
        "detector_records_emitted": bool(projected.detector_names),
        "logical_observables_emitted": bool(projected.observable_names),
        "detector_names": list(projected.detector_names),
        "logical_observable_names": list(projected.observable_names),
        "detector_records": detector_records,
        "logical_observable_records": logical_records,
        "detector_marginals": marginals(detector_records),
        "logical_observable_marginals": marginals(logical_records),
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
        "claims_full_schedule_coverage": False,
        "claims_overlapping_window_joint_generator": False,
        "claims_axis2_source_projection": False,
        "record_layout_ref": dict(schedule.record_layout_ref),
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
    payload = {
        "schema": qt.AXIS1_RECORD_EVIDENCE_SCHEMA,
        "verdict": "pass",
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": qt.AXIS1_RECORD_EVIDENCE_REPRESENTABILITY,
        "compiler_provenance": {
            "schedule_seal_schema": qt.COMPILER_SCHEDULE_SEAL_SCHEMA,
            "schedule_seal_valid": qt.has_valid_compiler_schedule_seal(schedule),
            "schedule_seal_public": False,
            "generated_substeps": all(
                substep.generated_by_compiler for substep in schedule.substeps
            ),
        },
        "primitive_registry": qt.default_axis1_primitive_registry().to_manifest(),
        "selection_plan": selection_plan.to_manifest(),
        "selection_partition": qt.axis1_selection_partition_manifest(
            selection_layers
        ),
        "readout_reset_instrument_spec": instrument,
        "coverage": qt._coverage_manifest(schedule, selection_plan),
        "metric_reference": "docs/METRICS.md#forward-fidelity--coupling-metrics",
        "representability_limits": (
            "selected local or union-support joint channels plus exact Pauli-basis "
            "measurement branch enumeration; detector/logical records only when "
            "public XOR wiring is present, no .b8 artifact, no decoder output, "
            "no Axis-2 source timeline, no leakage/qutrit integration"
        ),
        "record_evidence": record_evidence,
        "probability_residual_passed": True,
        "passed": True,
    }
    return _rehash(qt, payload)


def _direct_child(
    qt: Any,
    schedule: Any,
    *,
    max_bond: int | None,
    max_branches: int = 4096,
    max_record_materialization_outcomes: int,
    microstep_count: int,
    finite_step_order: str,
    worst_cut_discarded_weight_gate: float | None,
    total_discarded_weight_gate: float | None,
    trajectory_count: int | None,
    rng_seed: int | None,
    dense_oracle_certification: bool,
    device: str = "cuda",
) -> dict[str, Any]:
    sampled = trajectory_count is not None
    mode = (
        "sampled_product_channel_trajectories"
        if sampled
        else "exact_branch_enumeration"
    )
    keys = ["m0", "m1"]
    targets = [0, 1]
    if sampled:
        records = [[0, 0]]
        counts: list[int] | None = [int(trajectory_count)]
        probabilities = [1.0]
    else:
        records = [
            list(record)
            for record in qt.materialize_binary_records(len(keys))
        ]
        counts = None
        probabilities = [1.0, 0.0, 0.0, 0.0]
    layout = qt.axis1_record_layout_from_schedule(schedule)
    projected = qt.project_axis1_xor_records(layout, records)
    preflight = qt._record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=max_record_materialization_outcomes,
        trajectory_count=trajectory_count,
    )
    program = qt.axis1_carrier_program_manifest(
        schedule,
        backend_contract=qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    sampling = {
        "mode": mode,
        "trajectory_count": trajectory_count,
        "rng_seed": rng_seed,
        "rng_seed_required_for_acceptance": sampled,
        "rng_seed_was_explicit": sampled,
        "rng_backend": "torch.Generator(cuda)" if sampled else "not_used",
        "measurement_sampling_policy": (
            "sequential_conditional_single_site_z_v1"
            if sampled
            else "exact_joint_binary_branch_enumeration"
        ),
        "record_support_policy": (
            "observed_empirical_outcomes_only"
            if sampled
            else "full_binary_record_support"
        ),
        "probability_semantics": (
            "empirical_record_frequencies"
            if sampled
            else "exact_enumerated_branch_probabilities"
        ),
        "comparison_outcome_is_metric": False,
    }
    if sampled:
        sampling["rng_seed_default_policy"] = "default_zero_when_not_provided"
        sampling["zero_frequency_records_emitted"] = False
    expected_occurrences = (
        qt._qt_expected_actual_split_occurrences(
            program,
            microstep_count=microstep_count,
            finite_step_order=finite_step_order,
        )
        if max_bond is not None
        else ()
    )
    truncation_events: list[dict[str, Any]] = []
    aggregation = (
        qt.aggregate_sampled_truncation_events(
            truncation_events,
            trajectory_count=int(trajectory_count),
            expected_gate_occurrences=expected_occurrences,
        )
        if sampled
        else qt.aggregate_exact_branch_truncation_events(
            truncation_events,
            expected_gate_occurrences=expected_occurrences,
        )
    )
    ledger = qt.build_mps_truncation_ledger(
        max_bond=max_bond,
        local_dims=(2,) * int(schedule.num_qubits),
        max_observed_bond=1,
        truncation_events=truncation_events,
        aggregation=aggregation,
    )
    applied_substeps: list[dict[str, Any]] = []
    static_branch_upper = 1
    for substep in program["program"]["substeps"]:
        summary = qt.axis1_carrier_substep_summary(substep)
        kind = str(substep["substep_kind"])
        if not sampled:
            static_branch_upper = (
                qt._static_exact_branch_upper_after_substep(
                    static_branch_upper,
                    substep=substep,
                    microstep_count=microstep_count,
                    max_branches=max_branches,
                )
            )
        if sampled and kind == "reset":
            applied_substeps.append(
                {
                    **summary,
                    "finite_step_policy": (
                        "boundary_only_no_generator_evolution"
                    ),
                    "reset_boundary_policy": (
                        "sampled_pauli_reset_internal_outcome_no_record"
                    ),
                    "sampled_trajectory_count": int(trajectory_count),
                    "max_observed_bond_after_substep": 1,
                }
            )
        elif sampled:
            applied_substeps.append(
                {
                    **summary,
                    "finite_step_policy": qt._finite_step_policy_name(
                        finite_step_order
                    ),
                    "finite_step_order": finite_step_order,
                    "microstep_count": microstep_count,
                    "sampled_trajectory_count": int(trajectory_count),
                    "sampled_collapse_term_count": 0,
                    "max_observed_bond_after_substep": 1,
                }
            )
        elif kind == "reset":
            applied_substeps.append(
                {
                    **summary,
                    "finite_step_policy": (
                        "boundary_only_no_generator_evolution"
                    ),
                    "reset_boundary_policy": (
                        "nonselective_pauli_reset_internal_branches_no_record"
                    ),
                    "static_branch_count_upper_bound_after_substep": (
                        static_branch_upper
                    ),
                    "max_observed_bond_after_substep": 1,
                }
            )
        else:
            applied = {
                **summary,
                "finite_step_policy": qt._finite_step_policy_name(
                    finite_step_order
                ),
                "finite_step_order": finite_step_order,
                "microstep_count": microstep_count,
                "static_branch_count_upper_bound_after_substep": (
                    static_branch_upper
                ),
                "max_observed_bond_after_substep": 1,
            }
            applied_substeps.append(applied)
    execution: dict[str, Any] = {
        "initial_state": "computational_zero_mps",
        "site_order": list(range(int(schedule.num_qubits))),
        "physical_dimension": 2,
        "mps_library": "quimb.tensor.MatrixProductState",
        "array_backend": "torch_cuda_complex128",
        "hamiltonian_evolution_policy": (
            "operator_family_order_product_formula"
        ),
        "collapse_evolution_policy": "local_product_channel_branching",
        "finite_step_policy": {
            "name": qt._finite_step_policy_name(finite_step_order),
            "order": finite_step_order,
            "microstep_count": microstep_count,
            "microstep_dt_policy": (
                "equal_substeps_dt_ns_div_microstep_count"
            ),
            "exact_summed_lindbladian_claim": False,
            "comparison_outcome_is_metric": False,
        },
        "trajectory_sampling": sampling,
        "exact_joint_generator_claim": False,
        "exact_summed_lindbladian_claim": False,
        "measurement_basis": "Z",
        "measurement_keys": keys,
        "measurement_targets": targets,
        "measurement_records": records,
        "record_probabilities": probabilities,
        "record_count": len(records),
        "total_probability": 1.0,
        "total_probability_residual": 0.0,
        "detector_records_emitted": bool(projected.detector_names),
        "detector_names": list(projected.detector_names),
        "detector_records": [list(row) for row in projected.detector_records],
        "logical_observables_emitted": bool(projected.observable_names),
        "logical_observable_names": list(projected.observable_names),
        "logical_observable_records": [
            list(row) for row in projected.observable_records
        ],
        "mps_truncation_ledger": ledger,
        "applied_substeps": applied_substeps,
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
        "claims_dense_channel_evidence": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
    }
    if counts is not None:
        execution["record_counts"] = counts
    if dense_oracle_certification and not sampled:
        dense = _dense_record_oracle_payload(
            qt,
            schedule,
            device=device,
        )
        certification = {
            "executed": True,
            "passed": True,
            "dense_evidence_schema": qt.AXIS1_RECORD_EVIDENCE_SCHEMA,
            "dense_evidence_content_hash": dense["content_hash"],
            "dense_representability": qt.AXIS1_RECORD_EVIDENCE_REPRESENTABILITY,
            "comparison_object": "record_probabilities",
            "max_abs_probability_difference": 0.0,
            "threshold": qt._DENSE_RECORD_CERTIFICATION_GATE,
            "threshold_epistemic_class": "c",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        }
    else:
        certification = {
            "executed": False,
            "reason": (
                "sampled_trajectory_empirical_probabilities_not_exact_dense_certified"
                if sampled
                else "dense_oracle_certification_not_requested"
            ),
            "comparison_outcome_is_metric": False,
        }
    policy = qt._restricted_acceptance_policy(
        program=program,
        execution=execution,
        record_materialization_preflight=preflight,
        certification=certification,
        finite_step_order=finite_step_order,
        finite_step_policy=qt._finite_step_policy_name(finite_step_order),
        max_bond=max_bond,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
    )
    payload = {
        "schema": qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY,
        "backend_contract": qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": device,
        "carrier_program": qt._program_summary(program),
        "max_bond": max_bond,
        "max_branches": max_branches,
        "max_record_materialization_outcomes": max_record_materialization_outcomes,
        "record_materialization_preflight": preflight,
        "microstep_count": microstep_count,
        "finite_step_order": finite_step_order,
        "trajectory_count": trajectory_count,
        "rng_seed": rng_seed,
        "dense_oracle_certification_requested": dense_oracle_certification,
        "worst_cut_discarded_weight_gate": worst_cut_discarded_weight_gate,
        "total_discarded_weight_gate": total_discarded_weight_gate,
        "verdict": "pass",
        "passed": True,
        "execution_status": "completed",
        "certification_status": "accepted",
        "diagnostic_only": False,
        "qt_mps_backend_executed": True,
        "claims_qt_mps_backend_execution": True,
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": qt._QT_MPS_SCORED_QUANTITY_POLICY,
        "approximation_book": qt._qt_restricted_approximation_book(
            max_bond=max_bond,
            microstep_count=microstep_count,
            finite_step_order=finite_step_order,
            trajectory_count=trajectory_count,
            rng_seed=rng_seed,
            worst_cut_discarded_weight_gate=(
                worst_cut_discarded_weight_gate
            ),
            total_discarded_weight_gate=total_discarded_weight_gate,
            execution=execution,
        ),
        "epistemic_classes": qt._qt_restricted_epistemic_classes(),
        "blocked_reason": None,
        "blocked_substeps": [],
        "mps_execution": execution,
        "dense_jointL_record_certification": certification,
        "restricted_acceptance_policy": policy,
        "scope": qt._QT_MPS_COMPLETED_SCOPE,
    }
    return _rehash(qt, payload)


def _install_dense_record_oracle(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
) -> None:
    def dense(schedule: Any, *, device: str) -> dict[str, Any]:
        return _dense_record_oracle_payload(
            qt,
            schedule,
            device=device,
        )

    monkeypatch.setattr(qt, "axis1_measurement_record_evidence_manifest", dense)


def _install_direct_children(monkeypatch: pytest.MonkeyPatch, qt: Any) -> None:
    _install_dense_record_oracle(monkeypatch, qt)

    def run(schedule: Any, **kwargs: Any) -> dict[str, Any]:
        return _direct_child(qt, schedule, **kwargs)

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    monkeypatch.setattr(
        qt,
        "_bond_sweep_comparison",
        lambda *_args, **kwargs: {
            "reference_bond": 2,
            "convergence_gate": {
                "evaluated": True,
                "passed": True,
                "convergence_record_probability_gate": kwargs[
                    "convergence_record_probability_gate"
                ],
            },
        },
    )
    monkeypatch.setattr(
        qt,
        "_bond_sweep_reference_calibration",
        lambda *_args, **_kwargs: {
            "accepted_as_dense_calibrated_reference": True,
        },
    )
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_comparison",
        lambda *_args, **kwargs: {
            "seed_spread_gate": {
                "evaluated": True,
                "passed": True,
                "seed_record_frequency_spread_gate": kwargs[
                    "seed_record_frequency_spread_gate"
                ],
            },
        },
    )
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_dense_calibration",
        lambda *_args, **kwargs: {
            "accepted_as_dense_calibrated_trajectory_evidence": True,
            "dense_record_frequency_gate": kwargs["dense_record_frequency_gate"],
        },
    )


def _mutate_and_rehash(
    qt: Any,
    payload: dict[str, Any],
    mutation: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    corrupted = copy.deepcopy(payload)
    mutation(corrupted)
    return _rehash(qt, corrupted)


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(lambda child: child.__setitem__("max_bond", 9), id="bond"),
        pytest.param(
            lambda child: child.__setitem__("source_hash", "f" * 64),
            id="source",
        ),
        pytest.param(
            lambda child: child.__setitem__("max_branches", 17),
            id="max_branches",
        ),
        pytest.param(
            lambda child: child["record_materialization_preflight"].__setitem__(
                "total_measurement_width", 1
            ),
            id="preflight",
        ),
        pytest.param(
            lambda child: child["carrier_program"].__setitem__(
                "content_hash", "f" * 64
            ),
            id="carrier_program",
        ),
    ],
)
def test_qt_bond_sweep_rejects_rehashed_child_request_corruption(
    monkeypatch: pytest.MonkeyPatch,
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    _install_dense_record_oracle(monkeypatch, qt)
    corrupted_children = 0

    def run(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal corrupted_children
        corrupted = _mutate_and_rehash(
            qt,
            _direct_child(qt, schedule_arg, **kwargs),
            mutation,
        )
        corrupted_children += 1
        return corrupted

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    monkeypatch.setattr(
        qt,
        "_bond_sweep_comparison",
        lambda *_args, **_kwargs: {
            "convergence_gate": {"evaluated": True, "passed": True},
        },
    )
    monkeypatch.setattr(
        qt,
        "_bond_sweep_reference_calibration",
        lambda *_args, **_kwargs: {
            "accepted_as_dense_calibrated_reference": True,
        },
    )

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            schedule,
            bond_values=(1, 2),
            max_branches=11,
            convergence_record_probability_gate=0.0,
        )
    assert corrupted_children == 2


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(lambda child: child.__setitem__("rng_seed", 101), id="seed"),
        pytest.param(
            lambda child: child.__setitem__("trajectory_count", 99),
            id="trajectory_count",
        ),
        pytest.param(lambda child: child.__setitem__("max_bond", 1), id="bond"),
        pytest.param(
            lambda child: child["mps_execution"]["trajectory_sampling"].__setitem__(
                "rng_seed", 101
            ),
            id="execution_seed",
        ),
    ],
)
def test_qt_seed_sweep_rejects_rehashed_child_request_corruption(
    monkeypatch: pytest.MonkeyPatch,
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    corrupted_children = 0

    def run(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal corrupted_children
        corrupted = _mutate_and_rehash(
            qt,
            _direct_child(qt, schedule_arg, **kwargs),
            mutation,
        )
        corrupted_children += 1
        return corrupted

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_comparison",
        lambda *_args, **_kwargs: {
            "seed_spread_gate": {"evaluated": True, "passed": True},
        },
    )
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_dense_calibration",
        lambda *_args, **_kwargs: {
            "accepted_as_dense_calibrated_trajectory_evidence": True,
        },
    )

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
            schedule,
            trajectory_count=5,
            rng_seeds=(3, 7),
            max_bond=2,
            seed_record_frequency_spread_gate=0.0,
        )
    assert corrupted_children == 2


def test_qt_bundle_rejects_rehashed_child_workload_corruption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    _install_direct_children(monkeypatch, qt)
    bond = qt.axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        convergence_record_probability_gate=0.0,
    )
    seed = qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=5,
        rng_seeds=(3, 7),
        max_bond=2,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )
    bond["bond_values"] = [1, 9]
    _rehash(qt, bond)
    monkeypatch.setattr(qt, "axis1_qt_mps_bond_sweep_manifest", lambda *_a, **_k: bond)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        lambda *_a, **_k: seed,
    )

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=5,
            rng_seeds=(3, 7),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


@pytest.mark.parametrize(
    ("mutation", "error_type"),
    [
        pytest.param(
            lambda bond, _seed: bond.__setitem__("convergence_policy", []),
            TypeError,
            id="bond-policy-shape",
        ),
        pytest.param(
            lambda _bond, seed: seed.__setitem__("seed_sweep_policy", []),
            TypeError,
            id="seed-policy-shape",
        ),
        pytest.param(
            lambda _bond, seed: seed["seed_sweep_policy"].__setitem__(
                "accepted_as_restricted_seed_sweep_evidence", False
            ),
            ValueError,
            id="seed-policy-acceptance",
        ),
        pytest.param(
            lambda bond, _seed: bond["convergence_policy"].__setitem__(
                "accepted_as_restricted_convergence_evidence", False
            ),
            ValueError,
            id="bond-policy-acceptance",
        ),
    ],
)
def test_qt_bundle_rejects_rehashed_policy_shape_or_acceptance_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    mutation: Callable[[dict[str, Any], dict[str, Any]], None],
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    _install_direct_children(monkeypatch, qt)
    bond = qt.axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        convergence_record_probability_gate=0.0,
    )
    seed = qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=5,
        rng_seeds=(3, 7),
        max_bond=2,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )
    mutation(bond, seed)
    _rehash(qt, bond)
    _rehash(qt, seed)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_bond_sweep_manifest",
        lambda *_args, **_kwargs: bond,
    )
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        lambda *_args, **_kwargs: seed,
    )

    with pytest.raises(error_type):
        qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=5,
            rng_seeds=(3, 7),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


def test_qt_resource_probe_rejects_rehashed_bundle_provenance_corruption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    _install_direct_children(monkeypatch, qt)
    bundle = qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=5,
        rng_seeds=(3, 7),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )
    bundle["source_hash"] = "e" * 64
    _rehash(qt, bundle)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_a, **_k: bundle,
    )
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(qt.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(qt.torch.cuda, "reset_peak_memory_stats", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "synchronize", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_allocated", lambda _device: 1)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_reserved", lambda _device: 1)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_resource_probe_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=5,
            rng_seeds=(3, 7),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


@pytest.mark.parametrize("corrupted_child", ["bond", "trajectory"])
def test_qt_bundle_rejects_rehashed_backend_claim_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    corrupted_child: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    _install_direct_children(monkeypatch, qt)
    bond = qt.axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        convergence_record_probability_gate=0.0,
    )
    seed = qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=5,
        rng_seeds=(3, 7),
        max_bond=2,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )
    corrupted = bond if corrupted_child == "bond" else seed
    corrupted["claims_qt_mps_backend_execution"] = False
    _rehash(qt, corrupted)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_bond_sweep_manifest",
        lambda *_args, **_kwargs: bond,
    )
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        lambda *_args, **_kwargs: seed,
    )

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=5,
            rng_seeds=(3, 7),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


def test_qt_resource_probe_rejects_rehashed_nested_backend_claim_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    _install_direct_children(monkeypatch, qt)
    bundle = qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=5,
        rng_seeds=(3, 7),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )
    bundle["claims_qt_mps_backend_execution"] = False
    _rehash(qt, bundle)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: bundle,
    )
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(qt.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(qt.torch.cuda, "reset_peak_memory_stats", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "synchronize", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_allocated", lambda _device: 1)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_reserved", lambda _device: 1)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_resource_probe_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=5,
            rng_seeds=(3, 7),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


def test_qt_bond_sweep_rejects_when_any_nonreference_child_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    calls: list[dict[str, Any]] = []

    def run(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        child = _direct_child(qt, schedule_arg, **kwargs)
        calls.append(child)
        if len(calls) == 1:
            execution = child["mps_execution"]
            execution["record_probabilities"] = [0.9, 0.1, 0.0, 0.0]
            program = qt.axis1_carrier_program_manifest(
                schedule_arg,
                backend_contract=(
                    qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
                ),
            )
            certification = qt._dense_record_certification(
                schedule_arg,
                program=program,
                execution=execution,
                device=kwargs["device"],
            )
            policy = qt._restricted_acceptance_policy(
                program=program,
                execution=execution,
                record_materialization_preflight=child[
                    "record_materialization_preflight"
                ],
                certification=certification,
                finite_step_order=kwargs["finite_step_order"],
                finite_step_policy=qt._finite_step_policy_name(
                    kwargs["finite_step_order"]
                ),
                max_bond=kwargs["max_bond"],
                worst_cut_discarded_weight_gate=kwargs[
                    "worst_cut_discarded_weight_gate"
                ],
                total_discarded_weight_gate=kwargs[
                    "total_discarded_weight_gate"
                ],
            )
            child["dense_jointL_record_certification"] = certification
            child["restricted_acceptance_policy"] = policy
            child.update(
                verdict="fail",
                passed=False,
                certification_status=policy["certification_status"],
                diagnostic_only=policy["diagnostic_only"],
                blocked_reason=policy["blocked_reason"],
            )
            _rehash(qt, child)
        return child

    _install_direct_children(monkeypatch, qt)
    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)

    manifest = qt.axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        max_branches=11,
        convergence_record_probability_gate=0.0,
    )

    assert [summary["passed"] for summary in manifest["run_summaries"]] == [
        False,
        True,
    ]
    assert manifest["passed"] is False
    assert manifest["verdict"] == "fail"
    assert (
        manifest["convergence_policy"][
            "accepted_as_restricted_convergence_evidence"
        ]
        is False
    )


def test_qt_bond_sweep_recomputes_child_acceptance_from_execution_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    corrupted_children = 0

    def run(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal corrupted_children
        child = _direct_child(qt, schedule_arg, **kwargs)
        ledger = child["mps_execution"]["mps_truncation_ledger"]
        ledger.update(
            discarded_weight_sum=1.0,
            worst_cut_discarded_weight=1.0,
            n_truncating_ops=1,
        )
        corrupted = _rehash(qt, child)
        corrupted_children += 1
        return corrupted

    _install_direct_children(monkeypatch, qt)
    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            schedule,
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
            worst_cut_discarded_weight_gate=0.0,
            total_discarded_weight_gate=0.0,
        )
    assert corrupted_children == 2


def test_qt_bond_sweep_binds_child_record_fields_to_frozen_schedule_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    corrupted_children = 0

    def run(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal corrupted_children
        child = _direct_child(qt, schedule_arg, **kwargs)
        execution = child["mps_execution"]
        execution["measurement_keys"] = ["forged_m0", "forged_m1"]
        execution["measurement_targets"] = [1, 0]
        corrupted = _rehash(qt, child)
        corrupted_children += 1
        return corrupted

    _install_direct_children(monkeypatch, qt)
    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            schedule,
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )
    assert corrupted_children == 2


@pytest.mark.parametrize(
    ("field", "forged_value"),
    [
        pytest.param(
            "dense_evidence_schema",
            "error_coupling_simulator.frontend.forged_record_oracle.v1",
            id="schema",
        ),
        pytest.param("dense_evidence_content_hash", "e" * 64, id="hash"),
        pytest.param("comparison_object", "state_fidelity", id="comparison"),
    ],
)
def test_qt_bond_sweep_rejects_rehashed_forged_dense_oracle_identity(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    forged_value: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _measurement_schedule()
    corrupted_children = 0

    def run(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal corrupted_children
        child = _direct_child(qt, schedule_arg, **kwargs)
        child["dense_jointL_record_certification"][field] = forged_value
        corrupted = _rehash(qt, child)
        corrupted_children += 1
        return corrupted

    _install_direct_children(monkeypatch, qt)
    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            schedule,
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )
    assert corrupted_children == 2


def test_qt_blocked_aggregates_do_not_claim_backend_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _unsupported_measurement_schedule()
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(qt.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(qt.torch.cuda, "reset_peak_memory_stats", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "synchronize", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_allocated", lambda _device: 1)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_reserved", lambda _device: 1)

    bond = qt.axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
    )
    bundle = qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=2,
        rng_seeds=(3, 5),
    )
    resource = qt.axis1_qt_mps_resource_probe_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=2,
        rng_seeds=(3, 5),
    )

    assert bond["passed"] is False
    assert all(
        summary["qt_mps_backend_executed"] is False
        for summary in bond["run_summaries"]
    )
    assert bond["claims_qt_mps_backend_execution"] is False
    assert bundle["passed"] is False
    assert bundle["bond_sweep"]["claims_qt_mps_backend_execution"] is False
    assert (
        bundle["trajectory_seed_sweep"]["claims_qt_mps_backend_execution"]
        is False
    )
    assert bundle["claims_qt_mps_backend_execution"] is False
    assert resource["passed"] is False
    assert resource["claims_qt_mps_backend_execution"] is False


def test_qt_exact_record_validator_rejects_lexicographic_noncanonical_order() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    execution = {
        "measurement_keys": ["m0", "m1"],
        "measurement_targets": [0, 1],
        "measurement_records": [[0, 0], [0, 1], [1, 0], [1, 1]],
        "record_probabilities": [1.0, 0.0, 0.0, 0.0],
        "record_count": 4,
        "total_probability": 1.0,
        "total_probability_residual": 0.0,
    }

    with pytest.raises(ValueError):
        qt._validate_qt_record_execution_payload(
            execution,
            sampled=False,
            trajectory_count=None,
        )

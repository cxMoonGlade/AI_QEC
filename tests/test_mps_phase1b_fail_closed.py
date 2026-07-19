"""GREEN regression firewall for restricted-MPS Phase 1B false-green defects."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
import sys
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from tests._support.mcwf_artifact_certification import (
    passing_mcwf_artifact_certification,
)


def _rehash_manifest(payload: dict[str, Any]) -> None:
    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    encoded = json.dumps(
        without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    payload["content_hash"] = hashlib.sha256(encoded).hexdigest()


def _mcwf_ordered_measurement_metadata(
    bases: tuple[str, ...] = ("Z",),
    *,
    reset_after: tuple[bool, ...] | None = None,
) -> dict[str, Any]:
    ordered_bases = list(bases)
    ordered_reset = (
        [False] * len(ordered_bases)
        if reset_after is None
        else list(reset_after)
    )
    if len(ordered_reset) != len(ordered_bases):
        raise ValueError("test fixture reset mask must match its ordered bases")
    if not ordered_bases:
        summary = "none"
    elif all(basis == "X" for basis in ordered_bases):
        summary = "X"
    elif all(basis == "Z" for basis in ordered_bases):
        summary = "Z"
    else:
        summary = "mixed_pauli"
    return {
        "measurement_bases": ordered_bases,
        "reset_after": ordered_reset,
        "measurement_basis": summary,
        "measurement_basis_semantics": (
            "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
            "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
        ),
    }


class _CudaReached(RuntimeError):
    pass


class _MappingLikeNonDict:
    def __getitem__(self, _key: str) -> Any:
        raise AssertionError("non-dict trajectory sampling must not be indexed")

    def get(self, _key: str, _default: Any = None) -> Any:
        raise AssertionError("non-dict trajectory sampling must not be read")

    def __iter__(self):
        raise AssertionError("non-dict trajectory sampling must not be iterated")

    def __bool__(self) -> bool:
        raise AssertionError("non-dict trajectory sampling must not be coerced")


def _install_qt_bond_must_not_run_counters(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
) -> dict[str, int]:
    calls = {"comparison": 0, "calibration": 0}

    def comparison(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["comparison"] += 1
        raise AssertionError("bond comparison must not run for an invalid child")

    def calibration(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["calibration"] += 1
        raise AssertionError("bond calibration must not run for an invalid child")

    monkeypatch.setattr(qt, "_bond_sweep_comparison", comparison)
    monkeypatch.setattr(qt, "_bond_sweep_reference_calibration", calibration)
    return calls


def _install_qt_seed_must_not_run_counters(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
) -> dict[str, int]:
    calls = {"comparison": 0, "calibration": 0}

    def comparison(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["comparison"] += 1
        raise AssertionError("seed comparison must not run for an invalid child")

    def calibration(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["calibration"] += 1
        raise AssertionError("seed calibration must not run for an invalid child")

    monkeypatch.setattr(qt, "_trajectory_seed_sweep_comparison", comparison)
    monkeypatch.setattr(qt, "_trajectory_seed_sweep_dense_calibration", calibration)
    return calls


@pytest.fixture(scope="module")
def carrier_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    return circuit_ir_to_substep_schedule(builder.build())


@pytest.fixture(scope="module")
def honest_carrier_qt_child(carrier_measurement_schedule):
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        axis1_qt_mps_restricted_execution_manifest,
    )

    return axis1_qt_mps_restricted_execution_manifest(
        carrier_measurement_schedule,
        device="cuda",
    )


@pytest.fixture(scope="module")
def honest_carrier_mcwf_child(carrier_measurement_schedule):
    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        axis1_mcwf_mps_state_record_execution_manifest,
    )

    return axis1_mcwf_mps_state_record_execution_manifest(
        carrier_measurement_schedule,
        device="cuda",
        trajectory_count=4,
        rng_seed=17,
    )


def _six_bit_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=6)
    builder.measure(
        tuple(range(6)),
        key=tuple(f"m{i}" for i in range(6)),
        duration_ns=1.0,
    )
    return circuit_ir_to_substep_schedule(builder.build())


def _one_bit_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0", duration_ns=1.0)
    return circuit_ir_to_substep_schedule(builder.build())


def _qt_authenticated_dense_record(
    qt: Any,
    schedule: Any,
    *,
    probabilities: list[float] | None = None,
) -> dict[str, Any]:
    from test_mps_qt_aggregate_binding import _dense_record_oracle_payload

    payload = _dense_record_oracle_payload(qt, schedule, device="cuda")
    if probabilities is not None:
        payload["record_evidence"]["record_probabilities"] = probabilities
        _rehash_manifest(payload)
    return payload


def _two_boundary_six_bit_measurement_schedule():
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=3)
    builder.measure(
        tuple(range(3)),
        key=tuple(f"first_m{i}" for i in range(3)),
        duration_ns=1.0,
    )
    builder.tick()
    builder.measure(
        tuple(range(3)),
        key=tuple(f"second_m{i}" for i in range(3)),
        duration_ns=1.0,
    )
    return circuit_ir_to_substep_schedule(builder.build())


def _ledger(*, explicit_truncation: bool = False) -> dict[str, Any]:
    return {
        "explicit_truncation_requested": explicit_truncation,
        "exact_bond_dimension_sufficient": 4,
        "exact_bond_policy": (
            "finite_cap_below_conservative_exact_sufficient_bond"
            if explicit_truncation
            else "unbounded_no_requested_truncation"
        ),
        "accepted_as_exact_bond_representation": not explicit_truncation,
        "discarded_weight_ledger_complete": True,
        "discarded_weight_sum": 0.0,
        "worst_cut_discarded_weight": 0.0,
        "n_truncating_ops": 0,
        "epistemic_class": "c",
    }


def _mcwf_metric_certification(**overrides: Any) -> dict[str, Any]:
    sampling_halfwidth = 0.5 * math.sqrt(math.log(200.0) / 4.0)
    certification = {
        "executed": True,
        "passed": True,
        "passed_gross": True,
        "comparison_outcome_is_metric": True,
        "comparison_object": "record_probabilities",
        "metric": "total_variation_distance",
        "metric_convention": (
            "TV = 1/2 * sum_i |p_i - q_i| "
            "(Born vs empirical record frequencies)"
        ),
        "oracle": (
            "error_coupling_simulator.frontend.axis1_record_evidence."
            "axis1_measurement_record_evidence_manifest"
        ),
        "oracle_independent_of_carrier_grouping": True,
        "value": 0.0,
        "gate": 1.0e-6,
        "gross_gate": 0.1,
        "gross_gate_ceiling": 0.45,
        "sampling_finite_shot_halfwidth": sampling_halfwidth,
        "sampling_support_size": 1,
        "effective_gate_including_sampling_ci": 1.0e-6,
        "gross_effective_gate_including_sampling_ci": 0.45,
        "sampling_ci_method": (
            "per_bin_two_sided_hoeffding_capped_at_gross_tv_ceiling"
        ),
        "sampling_confidence": 0.99,
        "trajectory_count": 2,
        "dense_evidence_schema": (
            "error_coupling_simulator.frontend.measurement_record_evidence.v1"
        ),
        "dense_evidence_content_hash": "a" * 64,
    }
    certification.update(overrides)
    if certification["comparison_object"] == (
        "measurement_basis_level_and_emitted_binary_record_populations"
    ):
        if "metric" not in overrides:
            certification["metric"] = (
                "maximum_component_total_variation_distance"
            )
        if "component_values" not in overrides:
            certification["component_values"] = {
                "declared_basis_eigenlabel_tv": certification["value"],
                "emitted_binary_record_tv": certification["value"],
            }
        if "readout_model_independent" not in overrides:
            certification["readout_model_independent"] = False
        if "sampling_ci_method" not in overrides:
            certification["sampling_ci_method"] = (
                "bonferroni_two_component_per_bin_two_sided_hoeffding_"
                "capped_at_gross_tv_ceiling"
            )
        if "sampling_finite_shot_halfwidth" not in overrides:
            support_size = int(certification["sampling_support_size"])
            trajectory_count = int(certification["trajectory_count"])
            alpha = 1.0 - float(certification["sampling_confidence"])
            certification["sampling_finite_shot_halfwidth"] = (
                0.5
                * support_size
                * math.sqrt(
                    math.log(4.0 * support_size / alpha)
                    / (2.0 * trajectory_count)
                )
            )
        if "gross_effective_gate_including_sampling_ci" not in overrides:
            certification["gross_effective_gate_including_sampling_ci"] = min(
                certification["gross_gate"]
                + certification["sampling_finite_shot_halfwidth"],
                certification["gross_gate_ceiling"],
            )
    if "metric_convention" not in overrides:
        certification["metric_convention"] = {
            "within_substep_window_channel": (
                "1 - F_pro; F_pro = Uhlmann fidelity of trace-normalised "
                "Choi states J/D (composed_vs_joint_infidelity convention)"
            ),
            "record_probabilities": (
                "TV = 1/2 * sum_i |p_i - q_i| "
                "(Born vs empirical record frequencies)"
            ),
            "measurement_basis_level_and_emitted_binary_record_populations": (
                "max(TV_label, TV_binary), with each TV = 1/2 * sum_i "
                "|p_i - q_i|; joint pass is the logical AND of the "
                "declared-basis eigenlabel and emitted binary Record TV gates"
            ),
        }[certification["comparison_object"]]
    return certification


def _mcwf_channel_certification(**overrides: Any) -> dict[str, Any]:
    certification = {
        "executed": True,
        "passed": True,
        "passed_gross": True,
        "comparison_outcome_is_metric": True,
        "comparison_object": "within_substep_window_channel",
        "metric": "process_infidelity_one_minus_Fe",
        "metric_convention": (
            "1 - F_pro; F_pro = Uhlmann fidelity of trace-normalised "
            "Choi states J/D (composed_vs_joint_infidelity convention)"
        ),
        "oracle": (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        "oracle_independent_of_carrier_grouping": True,
        "value": 0.0,
        "gate": 1.0e-6,
        "gross_gate": 0.1,
        "choi_trace_distance": 0.0,
    }
    certification.update(overrides)
    return certification


def _mcwf_evaluator_only_diagnostics(**overrides: Any) -> dict[str, Any]:
    diagnostics = {
              "schema": (
                  "error_coupling_simulator.frontend."
                  "mcwf_mps_evaluator_only_diagnostics.v2"
              ),
              "visibility": (
                  "evaluator_only_not_emitted_record_or_downstream_estimator_input"
              ),
              "level_record_semantics": (
                  "schedule-ordered local measurement eigenlabel tuples: "
                  "X columns use 0=|+>,1=|-> and preserve leaked level labels >=2; "
                  "Z columns use computational local levels"
              ),
        "level_records": [],
        "level_record_counts": [],
        "level_record_probabilities": [],
        "jump_family_counts": {},
    }
    diagnostics.update(overrides)
    return diagnostics


def _qt_dense_certification(**overrides: Any) -> dict[str, Any]:
    certification = {
        "executed": True,
        "passed": True,
        "dense_evidence_schema": (
            "error_coupling_simulator.frontend.measurement_record_evidence.v1"
        ),
        "dense_evidence_content_hash": "b" * 64,
        "comparison_object": "record_probabilities",
        "max_abs_probability_difference": 0.0,
        "threshold": 1.0e-8,
        "comparison_outcome_is_metric": False,
    }
    certification.update(overrides)
    return certification


def _qt_policy(
    *,
    residual: Any = 0.0,
    certification: dict[str, Any] | None = None,
    sampling: dict[str, Any] | None = None,
    ledger: dict[str, Any] | None = None,
    requires_scalable_backend: bool = False,
    execution_overrides: dict[str, Any] | None = None,
    preflight_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _restricted_acceptance_policy,
    )

    selected_ledger = _ledger() if ledger is None else ledger
    raw_sampling = sampling or {
        "mode": "exact_branch_enumeration",
        "trajectory_count": None,
        "rng_seed": None,
        "rng_seed_was_explicit": False,
    }
    sampled = raw_sampling.get("mode") == (
        "sampled_product_channel_trajectories"
    )
    sampling_contract = {
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
        "rng_seed_required_for_acceptance": sampled,
        "comparison_outcome_is_metric": False,
        **raw_sampling,
    }
    if sampled:
        sampling_contract.setdefault("zero_frequency_records_emitted", False)
        trajectory_count = int(sampling_contract["trajectory_count"])
        default_records = [[0]]
        default_counts: list[int] | None = [trajectory_count]
        default_probabilities = [1.0]
    else:
        default_records = [[0], [1]]
        default_counts = None
        default_probabilities = [1.0, 0.0]
    execution = {
        "total_probability_residual": residual,
        "total_probability": 1.0,
        "trajectory_sampling": sampling_contract,
        "finite_step_policy": {"microstep_count": 1},
        "measurement_keys": ["m0"],
        "measurement_targets": [0],
        "measurement_records": default_records,
        "record_probabilities": default_probabilities,
        "record_count": len(default_records),
        "mps_truncation_ledger": selected_ledger,
    }
    if default_counts is not None:
        execution["record_counts"] = default_counts
    overrides = execution_overrides or {}
    execution.update(overrides)
    if "measurement_records" in overrides and "record_count" not in overrides:
        execution["record_count"] = len(execution["measurement_records"])
    if "measurement_keys" in overrides and "measurement_targets" not in overrides:
        execution["measurement_targets"] = [
            0 for _key in execution["measurement_keys"]
        ]
    width = len(execution["measurement_keys"])
    if sampled:
        upper_bound = min(1 << width, int(sampling_contract["trajectory_count"]))
    else:
        upper_bound = 1 << width
    preflight = {
        "schema": (
            "error_coupling_simulator.frontend."
            "qt_mps_record_materialization_preflight.v2"
        ),
        "record_support_policy": sampling_contract["record_support_policy"],
        "trajectory_count": sampling_contract["trajectory_count"],
        "measurement_boundary_count": 1 if width else 0,
        "total_measurement_width": width,
        "materialized_outcome_count_upper_bound": upper_bound,
        "requires_full_binary_support_materialization": not sampled,
        "max_record_materialization_outcomes": max(upper_bound, 1),
        "within_budget": True,
        "checked_before_cuda": True,
        "checked_before_record_allocation": True,
    }
    preflight.update(preflight_overrides or {})
    return _restricted_acceptance_policy(
        program={"requires_scalable_backend": requires_scalable_backend},
        execution=execution,
        record_materialization_preflight=preflight,
        certification=certification or _qt_dense_certification(),
        finite_step_order="first_order",
        finite_step_policy="operator_family_product_formula_v1",
        max_bond=1 if selected_ledger["explicit_truncation_requested"] else None,
        worst_cut_discarded_weight_gate=None,
        total_discarded_weight_gate=None,
    )


@pytest.mark.parametrize(
    "preflight_overrides",
    [
        pytest.param(
            {"schema": "retired.preflight.v1"},
            id="schema",
        ),
        pytest.param(
            {"record_support_policy": "full_binary_record_support"},
            id="support-policy",
        ),
        pytest.param(
            {"trajectory_count": 99},
            id="trajectory-count",
        ),
        pytest.param(
            {"total_measurement_width": 9},
            id="measurement-width",
        ),
        pytest.param(
            {"materialized_outcome_count_upper_bound": 99},
            id="upper-bound",
        ),
        pytest.param(
            {"checked_before_cuda": False},
            id="cuda-order",
        ),
        pytest.param(
            {"checked_before_record_allocation": False},
            id="allocation-order",
        ),
    ],
)
def test_qt_v6_acceptance_binds_strategy_aware_preflight(
    preflight_overrides: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):
        _qt_policy(
            sampling={
                "mode": "sampled_product_channel_trajectories",
                "trajectory_count": 2,
                "rng_seed": 7,
                "rng_seed_was_explicit": True,
            },
            certification={
                "executed": False,
                "passed": False,
                "reason": "sampled_not_exact_dense_certified",
                "comparison_outcome_is_metric": False,
            },
            preflight_overrides=preflight_overrides,
        )


@pytest.mark.parametrize(
    ("sampling_overrides", "execution_overrides"),
    [
        pytest.param(
            {},
            {
                "measurement_records": [[0], [1]],
                "record_counts": [2, 0],
                "record_probabilities": [1.0, 0.0],
                "record_count": 2,
            },
            id="sampled-zero-frequency-row",
        ),
        pytest.param(
            {},
            {
                "measurement_records": [[1], [0]],
                "record_counts": [1, 1],
                "record_probabilities": [0.5, 0.5],
                "record_count": 2,
            },
            id="sampled-record-order",
        ),
        pytest.param(
            {"record_support_policy": "full_binary_record_support"},
            {},
            id="sampled-support-policy",
        ),
        pytest.param(
            {"measurement_sampling_policy": "retired_joint_table"},
            {},
            id="sampled-measurement-policy",
        ),
        pytest.param(
            {"zero_frequency_records_emitted": True},
            {},
            id="sampled-zero-frequency-claim",
        ),
        pytest.param(
            {},
            {"record_count": 2},
            id="sampled-record-count-link",
        ),
        pytest.param(
            {},
            {"measurement_targets": []},
            id="sampled-target-layout-link",
        ),
    ],
)
def test_qt_sampled_v6_sparse_contract_fails_closed(
    sampling_overrides: dict[str, Any],
    execution_overrides: dict[str, Any],
) -> None:
    sampling = {
        "mode": "sampled_product_channel_trajectories",
        "trajectory_count": 2,
        "rng_seed": 7,
        "rng_seed_was_explicit": True,
        **sampling_overrides,
    }

    with pytest.raises(ValueError):
        _qt_policy(
            sampling=sampling,
            certification={
                "executed": False,
                "passed": False,
                "reason": "sampled_not_exact_dense_certified",
                "comparison_outcome_is_metric": False,
            },
            execution_overrides=execution_overrides,
        )


@pytest.mark.parametrize(
    ("sampling_overrides", "execution_overrides"),
    [
        pytest.param(
            {"record_support_policy": "observed_empirical_outcomes_only"},
            {},
            id="exact-support-policy",
        ),
        pytest.param(
            {"measurement_sampling_policy": "retired_joint_table"},
            {},
            id="exact-measurement-policy",
        ),
        pytest.param(
            {},
            {
                "measurement_records": [[0]],
                "record_probabilities": [1.0],
                "record_count": 1,
            },
            id="exact-incomplete-support",
        ),
        pytest.param(
            {},
            {"record_count": 999},
            id="exact-record-count-link",
        ),
        pytest.param(
            {},
            {
                "measurement_keys": ["m0", "m1"],
                "measurement_records": [
                    [0, 0],
                    [0, 1],
                    [1, 0],
                    [1, 1],
                ],
                "record_probabilities": [1.0, 0.0, 0.0, 0.0],
            },
            id="exact-lexicographic-not-lsb-first",
        ),
        pytest.param(
            {},
            {"measurement_targets": [999, 0]},
            id="exact-target-layout-link",
        ),
    ],
)
def test_qt_exact_v6_full_support_contract_fails_closed(
    sampling_overrides: dict[str, Any],
    execution_overrides: dict[str, Any],
) -> None:
    sampling = {
        "mode": "exact_branch_enumeration",
        "trajectory_count": None,
        "rng_seed": None,
        "rng_seed_was_explicit": False,
        **sampling_overrides,
    }

    with pytest.raises(ValueError):
        _qt_policy(
            sampling=sampling,
            execution_overrides=execution_overrides,
        )


def _mcwf_policy(
    *,
    normalization_residual: Any = 0.0,
    runtime_mass_residual: Any = 0.0,
    certification: dict[str, Any] | None = None,
    rng_seed: Any = 17,
    ledger: dict[str, Any] | None = None,
    requires_scalable_backend: Any = False,
    trajectory_count: int = 2,
    mass_residual_budget: Any = 0.1,
    worst_cut_discarded_weight_gate: Any = None,
    total_discarded_weight_gate: Any = None,
    execution_overrides: dict[str, Any] | None = None,
    artifact_certification_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from error_coupling_simulator.certify.axis1_mps import (
        restricted_acceptance_policy,
    )

    execution = {
        "total_probability_residual": normalization_residual,
        "trajectory_sampling": {
            "mode": "sampled_fixed_microstep_mcwf_trajectories",
            "trajectory_count": trajectory_count,
        },
        "jump_sampling": {
            "probability_mass_residual_max": runtime_mass_residual
        },
        "finite_step_policy": {
            "microstep_count": 1,
            "order": "first_order",
        },
        "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(),
        "measurement_keys": ["m0"],
        "measurement_targets": [0],
        **_mcwf_ordered_measurement_metadata(),
        "measurement_records": [[0]],
        "record_counts": [trajectory_count],
        "record_probabilities": [1.0],
        "multilevel_measurement_policy": {
            "name": "declared_basis_eigenlabel_sample_then_binary_record",
            "bit_mapping": (
                "eigenlabel_0_to_bit_0_eigenlabel_1_to_bit_1_"
                "eigenlabel_ge_2_to_bit_1_with_probability_leaked_readout_b"
            ),
            "leaked_readout_b": 1.0,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "c",
        },
        "local_dims": [2],
        "mps_truncation_ledger": _ledger() if ledger is None else ledger,
    }
    overrides = execution_overrides or {}
    execution.update(overrides)
    raw_keys = execution.get("measurement_keys")
    if "measurement_keys" in overrides and isinstance(raw_keys, (list, tuple)):
        if "measurement_targets" not in overrides:
            execution["measurement_targets"] = [0 for _key in raw_keys]
        default_metadata = _mcwf_ordered_measurement_metadata(
            tuple("Z" for _key in raw_keys)
        )
        for field, value in default_metadata.items():
            if field not in overrides:
                execution[field] = value
    program = {"requires_scalable_backend": requires_scalable_backend}
    artifact_certification = passing_mcwf_artifact_certification(
        program,
        local_dims=list(execution["local_dims"]),
    )
    if artifact_certification_overrides:
        import error_coupling_simulator.certify.axis1_mps as certification_module

        artifact_certification.update(artifact_certification_overrides)
        artifact_certification["content_hash"] = (
            certification_module._mcwf_reference_packet_content_hash(
                artifact_certification
            )
        )
    return restricted_acceptance_policy(
        execution=execution,
        certification=certification or _mcwf_metric_certification(),
        program=program,
        declared_local_dims=list(execution["local_dims"]),
        rng_seed=rng_seed,
        trajectory_count=trajectory_count,
        mass_residual_budget=mass_residual_budget,
        worst_cut_discarded_weight_gate=worst_cut_discarded_weight_gate,
        total_discarded_weight_gate=total_discarded_weight_gate,
        dynamics_artifact_reference_certification=artifact_certification,
    )


def test_mcwf_policy_requires_post_execution_artifact_integrity() -> None:
    policy = _mcwf_policy(
        artifact_certification_overrides={
            "post_execution_integrity_verified": False,
        }
    )

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["blocked_reason"] == (
        "dynamics_artifact_reference_certification:"
        "post_execution_integrity_not_verified"
    )


def test_mcwf_policy_rejects_incomplete_artifact_reference_coverage() -> None:
    with pytest.raises(ValueError, match="coverage state is inconsistent"):
        _mcwf_policy(
            artifact_certification_overrides={"all_terms_covered": False}
        )


@pytest.mark.parametrize(
    "execution_overrides",
    [
        pytest.param(
            {"level_records": []},
            id="top_level_level_records",
        ),
        pytest.param(
            {
                "jump_sampling": {
                    "probability_mass_residual_max": 0.0,
                    "jump_family_counts": {"LEAK_SEEP_21": 1},
                }
            },
            id="jump_sampling_family_counts",
        ),
    ],
)
def test_mcwf_policy_rejects_retired_evaluator_diagnostic_layout(
    execution_overrides: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):
        _mcwf_policy(execution_overrides=execution_overrides)


@pytest.mark.parametrize(
    "invalid_residual",
    ["0.0", float("nan"), float("inf"), float("-inf"), -1.0, False, True],
)
def test_qt_probability_residual_must_be_finite_nonnegative_real(
    invalid_residual: Any,
) -> None:
    with pytest.raises(TypeError):
        _qt_policy(residual=invalid_residual)


def test_qt_true_overcap_without_independent_oracle_is_diagnostic_only() -> None:
    policy = _qt_policy(
        requires_scalable_backend=True,
        certification={
            "executed": False,
            "reason": "schedule_contains_scalable_required_rows",
            "comparison_outcome_is_metric": False,
        },
    )

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["certification_status"] == "unavailable"
    assert policy["diagnostic_only"] is True
    assert policy["blocked_reason"] == (
        "overcap_independent_record_oracle_unavailable"
    )
    assert policy["overcap"][
        "accepted_as_restricted_overcap_execution"
    ] is False


def test_mcwf_true_overcap_rejects_forged_passing_dense_certification() -> None:
    policy = _mcwf_policy(requires_scalable_backend=True)

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_as_restricted_overcap_execution"] is False
    assert policy["certification_status"] == "unavailable"
    assert policy["diagnostic_only"] is True
    assert "overcap_large_code_policy_not_established" in policy["production_blockers"]


@pytest.mark.parametrize(
    "effective_overrides",
    [
        {
            "effective_gate_including_sampling_ci": 1.0,
            "passed": True,
            "passed_gross": False,
        },
        {
            "gross_effective_gate_including_sampling_ci": 1.0,
            "passed": False,
            "passed_gross": True,
        },
    ],
    ids=["strict_only", "gross_only"],
)
def test_mcwf_policy_rejects_injected_effective_gates(
    effective_overrides: dict[str, Any],
) -> None:
    certification = _mcwf_metric_certification(
        value=0.9,
        gate=1.0e-6,
        gross_gate=0.1,
        **effective_overrides,
    )

    with pytest.raises(ValueError):
        _mcwf_policy(certification=certification)


def test_mcwf_metric_family_must_match_execution_payload() -> None:
    with pytest.raises(ValueError):
        _mcwf_policy(
            execution_overrides=_canonical_mcwf_channel_execution(),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dense_evidence_schema", "forged"),
        ("dense_evidence_content_hash", "forged"),
        ("threshold", 1.0),
    ],
)
def test_qt_dense_positive_evidence_uses_fixed_identity_and_threshold(
    field: str,
    value: Any,
) -> None:
    with pytest.raises(ValueError):
        _qt_policy(certification=_qt_dense_certification(**{field: value}))


def test_qt_sampled_policy_rejects_negative_probability() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    with pytest.raises(ValueError):
        qt._normalize_probability_distribution(
            [-1.0, 2.0],
            name="record_probabilities",
        )


def test_qt_sampled_policy_binds_probabilities_to_counts() -> None:
    sampling = {
        "mode": "sampled_product_channel_trajectories",
        "trajectory_count": 2,
        "rng_seed": 7,
        "rng_seed_was_explicit": True,
        "rng_seed_required_for_acceptance": True,
        "comparison_outcome_is_metric": False,
    }
    certification = {
        "executed": False,
        "passed": False,
        "reason": "sampled_trajectory_empirical_probabilities_not_exact_dense_certified",
        "comparison_outcome_is_metric": False,
    }

    with pytest.raises(ValueError):
        _qt_policy(
            sampling=sampling,
            certification=certification,
            execution_overrides={
                "measurement_records": [[0], [1]],
                "record_counts": [1, 1],
                "record_probabilities": [0.75, 0.25],
            },
        )


@pytest.mark.parametrize(
    ("sampling_override", "error_type"),
    [
        ({"rng_seed": None, "rng_seed_was_explicit": True}, TypeError),
        ({"rng_seed": True, "rng_seed_was_explicit": True}, TypeError),
        ({"rng_seed_required_for_acceptance": False}, ValueError),
        ({"comparison_outcome_is_metric": True}, ValueError),
    ],
)
def test_qt_sampled_policy_binds_seed_and_sampling_semantics(
    sampling_override: dict[str, Any],
    error_type: type[Exception],
) -> None:
    sampling = {
        "mode": "sampled_product_channel_trajectories",
        "trajectory_count": 2,
        "rng_seed": 7,
        "rng_seed_was_explicit": True,
        "rng_seed_required_for_acceptance": True,
        "comparison_outcome_is_metric": False,
    }
    sampling.update(sampling_override)
    certification = {
        "executed": False,
        "passed": False,
        "reason": "sampled_trajectory_empirical_probabilities_not_exact_dense_certified",
        "comparison_outcome_is_metric": False,
    }

    with pytest.raises(error_type):
        _qt_policy(
            sampling=sampling,
            certification=certification,
            execution_overrides={"record_counts": [2]},
        )


def test_qt_record_width_must_match_measurement_layout() -> None:
    sampling = {
        "mode": "sampled_product_channel_trajectories",
        "trajectory_count": 2,
        "rng_seed": 7,
        "rng_seed_was_explicit": True,
        "rng_seed_required_for_acceptance": True,
        "comparison_outcome_is_metric": False,
    }
    certification = {
        "executed": False,
        "passed": False,
        "reason": "sampled_trajectory_empirical_probabilities_not_exact_dense_certified",
        "comparison_outcome_is_metric": False,
    }

    with pytest.raises(ValueError):
        _qt_policy(
            sampling=sampling,
            certification=certification,
            execution_overrides={
                "measurement_keys": ["m0", "m1"],
                "measurement_records": [[0]],
                "record_counts": [2],
                "record_probabilities": [1.0],
            },
        )


@pytest.mark.parametrize(
    ("invalid_key", "error_type"),
    [(None, TypeError), ("", ValueError), (7, TypeError)],
)
def test_qt_policy_rejects_invalid_measurement_key_elements(
    invalid_key: Any,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        _qt_policy(
            execution_overrides={
                "measurement_keys": [invalid_key],
                "measurement_records": [[0]],
                "record_probabilities": [1.0],
            },
        )


@pytest.mark.parametrize(
    ("invalid_key", "error_type"),
    [(None, TypeError), ("", ValueError), (7, TypeError)],
)
def test_mcwf_policy_rejects_invalid_measurement_key_elements(
    invalid_key: Any,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        _mcwf_policy(
            execution_overrides={
                "measurement_keys": [invalid_key],
                "measurement_records": [[0]],
                "record_counts": [2],
                "record_probabilities": [1.0],
            },
        )


def test_mcwf_policy_rejects_wrong_metric_convention() -> None:
    with pytest.raises(ValueError):
        _mcwf_policy(
            certification=_mcwf_metric_certification(
                metric_convention="wrong metric convention",
            ),
        )


def test_qt_no_measurement_execution_without_independent_comparator_is_diagnostic() -> None:
    policy = _qt_policy(
        certification={
            "executed": False,
            "passed": False,
            "reason": "schedule_has_no_measurement_records",
            "comparison_outcome_is_metric": False,
        },
        execution_overrides={
            "measurement_keys": [],
            "measurement_records": [[]],
            "record_probabilities": [1.0],
        },
    )

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["certification_status"] == "unavailable"
    assert policy["diagnostic_only"] is True
    assert policy["blocked_reason"] == "independent_record_oracle_unavailable"


def test_qt_public_no_measurement_and_carrier_remain_diagnostic_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import torch

    if not torch.cuda.is_available():
        pytest.skip("public QT/MPS execution is CUDA-only")

    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    schedule = circuit_ir_to_substep_schedule(builder.build())
    direct = qt.axis1_qt_mps_restricted_execution_manifest(schedule)

    assert direct["verdict"] == "fail"
    assert direct["passed"] is False
    assert direct["execution_status"] == "completed"
    assert direct["certification_status"] == "unavailable"
    assert direct["diagnostic_only"] is True
    assert direct["blocked_reason"] == "independent_record_oracle_unavailable"
    assert direct["mps_execution"]["measurement_records"] == [[]]
    assert direct["mps_execution"]["record_probabilities"] == pytest.approx(
        [1.0],
        abs=1.0e-12,
    )

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: direct,
    )
    wrapped = carrier.axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=(
            carrier.AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
    )

    assert wrapped["verdict"] == "fail"
    assert wrapped["passed"] is False
    assert wrapped["execution_status"] == "completed"
    assert wrapped["certification_status"] == "unavailable"
    assert wrapped["diagnostic_only"] is True
    assert wrapped["blocked_reason"] == "independent_record_oracle_unavailable"


def test_qt_sampled_policy_cannot_override_executed_dense_failure() -> None:
    policy = _qt_policy(
        sampling={
            "mode": "sampled_product_channel_trajectories",
            "trajectory_count": 2,
            "rng_seed": 7,
            "rng_seed_was_explicit": True,
            "rng_seed_required_for_acceptance": True,
            "comparison_outcome_is_metric": False,
        },
        certification=_qt_dense_certification(
            passed=False,
            max_abs_probability_difference=0.9,
        ),
        execution_overrides={
            "measurement_records": [[0], [1]],
            "record_counts": [1, 1],
            "record_probabilities": [0.5, 0.5],
        },
    )

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["certification_status"] == "rejected"


@pytest.mark.parametrize("policy_kind", ["qt", "mcwf"])
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("discarded_weight_sum", 0.5),
        ("worst_cut_discarded_weight", 0.5),
        ("n_truncating_ops", 1),
    ],
)
def test_unbounded_ledger_cannot_report_truncation_loss(
    policy_kind: str,
    field: str,
    value: Any,
) -> None:
    corrupted = _ledger()
    corrupted[field] = value

    with pytest.raises(ValueError):
        if policy_kind == "qt":
            _qt_policy(ledger=corrupted)
        else:
            _mcwf_policy(ledger=corrupted)


def test_qt_child_evidence_flags_follow_restricted_acceptance() -> None:
    corrupted = _ledger(explicit_truncation=True)
    corrupted.update(
        discarded_weight_sum=0.2,
        worst_cut_discarded_weight=0.2,
        n_truncating_ops=1,
    )
    policy = _qt_policy(
        sampling={
            "mode": "sampled_product_channel_trajectories",
            "trajectory_count": 2,
            "rng_seed": 7,
            "rng_seed_was_explicit": True,
            "rng_seed_required_for_acceptance": True,
            "comparison_outcome_is_metric": False,
        },
        certification={
            "executed": False,
            "passed": False,
            "reason": "sampled_trajectory_empirical_probabilities_not_exact_dense_certified",
            "comparison_outcome_is_metric": False,
        },
        ledger=corrupted,
        execution_overrides={
            "measurement_records": [[0], [1]],
            "record_counts": [1, 1],
            "record_probabilities": [0.5, 0.5],
        },
    )

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_for_sampled_execution_evidence"] is False
    assert policy["trajectory"]["accepted_as_empirical_record_evidence"] is False


@pytest.mark.parametrize(
    "invalid_residual",
    ["0.0", float("nan"), float("inf"), float("-inf"), -1.0, False, True],
)
def test_mcwf_normalization_residual_must_be_finite_nonnegative_real(
    invalid_residual: Any,
) -> None:
    policy = _mcwf_policy(normalization_residual=invalid_residual)

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["certification_status"] == "rejected"
    assert policy["probability"][
        "normalization_invariant_is_finite_nonnegative_real"
    ] is False
    assert policy["blocked_reason"] == "normalization_invariant_invalid"


@pytest.mark.parametrize(
    "invalid_residual",
    ["0.0", float("nan"), float("inf"), float("-inf"), -1.0, False, True],
)
def test_mcwf_runtime_mass_residual_must_be_finite_nonnegative_real(
    invalid_residual: Any,
) -> None:
    policy = _mcwf_policy(runtime_mass_residual=invalid_residual)

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["probability"][
        "runtime_candidate_mass_residual_is_finite_nonnegative"
    ] is False
    assert policy["probability"]["runtime_candidate_mass_residual"] is None
    assert policy["blocked_reason"] == "runtime_probability_mass_residual_invalid"


@pytest.mark.parametrize("invalid_flag", [float("nan"), float("inf"), 1, "false"])
@pytest.mark.parametrize(
    ("route", "field"),
    [
        ("qt", "executed"),
        ("qt", "passed"),
        ("mcwf", "executed"),
        ("mcwf", "passed_gross"),
    ],
)
def test_dense_certification_flags_require_actual_booleans(
    route: str,
    field: str,
    invalid_flag: Any,
) -> None:
    certification = {
        "executed": True,
        "passed": True,
        "passed_gross": True,
        "comparison_outcome_is_metric": True,
    }
    certification[field] = invalid_flag

    with pytest.raises(TypeError):
        if route == "qt":
            _qt_policy(certification=certification)
        else:
            _mcwf_policy(certification=certification)


@pytest.mark.parametrize(
    ("route", "field"),
    [
        ("qt", "executed"),
        ("qt", "passed"),
        ("qt", "comparison_outcome_is_metric"),
        ("mcwf", "executed"),
        ("mcwf", "passed"),
        ("mcwf", "passed_gross"),
        ("mcwf", "comparison_outcome_is_metric"),
    ],
)
def test_dense_certification_requires_mandatory_verdict_fields(
    route: str,
    field: str,
) -> None:
    certification = (
        _qt_dense_certification()
        if route == "qt"
        else _mcwf_metric_certification()
    )
    certification.pop(field)

    with pytest.raises(KeyError):
        if route == "qt":
            _qt_policy(certification=certification)
        else:
            _mcwf_policy(certification=certification)


def test_qt_seed_evidence_flag_rejects_truthy_nonboolean() -> None:
    with pytest.raises(TypeError):
        _qt_policy(
            sampling={
                "mode": "sampled_product_channel_trajectories",
                "trajectory_count": 2,
                "rng_seed": 17,
                "rng_seed_was_explicit": float("nan"),
            },
            certification={
                "executed": False,
                "reason": (
                    "sampled_trajectory_empirical_probabilities_not_exact_dense_certified"
                ),
                "comparison_outcome_is_metric": False,
            },
        )


def test_mcwf_explicit_seed_rejects_bool_as_integer() -> None:
    with pytest.raises(TypeError):
        _mcwf_policy(rng_seed=True)


@pytest.mark.parametrize(
    "missing_key",
    [
        "discarded_weight_ledger_complete",
        "discarded_weight_sum",
        "worst_cut_discarded_weight",
    ],
)
def test_truncation_gate_requires_every_mandatory_ledger_value(
    missing_key: str,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    ledger = _ledger(explicit_truncation=True)
    ledger.pop(missing_key)
    with pytest.raises(KeyError):
        _truncation_gate_result(
            ledger,
            worst_cut_discarded_weight_gate=1.0,
            total_discarded_weight_gate=1.0,
        )


def test_truncation_ledger_complete_flag_requires_actual_boolean() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    ledger = _ledger(explicit_truncation=True)
    ledger["discarded_weight_ledger_complete"] = float("nan")
    with pytest.raises(TypeError):
        _truncation_gate_result(
            ledger,
            worst_cut_discarded_weight_gate=1.0,
            total_discarded_weight_gate=1.0,
        )


@pytest.mark.parametrize("route", ["qt", "mcwf"])
def test_lossless_finite_bond_claim_requires_truncating_operation_count(
    route: str,
) -> None:
    ledger = _ledger(explicit_truncation=True)
    ledger.pop("n_truncating_ops")

    with pytest.raises(KeyError):
        if route == "qt":
            _qt_policy(ledger=ledger)
        else:
            _mcwf_policy(ledger=ledger)


def test_qt_probability_residual_accepts_consistent_structural_tolerance() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    boundary_total = 1.0 + 0.5 * qt.NUMERICAL_ZERO
    representable_residual = abs(boundary_total - 1.0)
    assert representable_residual <= qt.NUMERICAL_ZERO
    assert _qt_policy(
        residual=representable_residual,
        execution_overrides={
            "total_probability": boundary_total,
            "record_probabilities": [boundary_total, 0.0],
        },
    )[
        "accepted_for_restricted_execution"
    ] is True


def test_mcwf_probability_and_truncation_gates_include_equality_boundary() -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    assert _mcwf_policy(normalization_residual=mcwf._NORMALIZATION_INVARIANT_GATE)[
        "accepted_for_restricted_execution"
    ] is True
    gate = qt._truncation_gate_result(
        {
            "discarded_weight_ledger_complete": True,
            "discarded_weight_sum": 0.2,
            "worst_cut_discarded_weight": 0.1,
        },
        worst_cut_discarded_weight_gate=0.1,
        total_discarded_weight_gate=0.2,
    )
    assert gate["passed"] is True


@pytest.mark.parametrize(
    "invalid_free_vram",
    [
        None,
        False,
        True,
        "unknown",
        float("nan"),
        float("inf"),
        float("-inf"),
        -1.0,
        0.0,
    ],
)
def test_auto_router_fails_toward_mcwf_on_invalid_free_vram(
    monkeypatch: pytest.MonkeyPatch,
    invalid_free_vram: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    schedule = SimpleNamespace(num_qubits=2, substeps=())
    monkeypatch.setattr(
        carrier,
        "_available_vram_bytes",
        lambda _device: invalid_free_vram,
    )
    chosen, decision = carrier._select_dense_or_mcwf(
        schedule,
        "cuda",
        {"requires_scalable_backend": False},
    )

    assert chosen == carrier.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    assert decision["schema"] == (
        "error_coupling_simulator.frontend.carrier_auto_routing_decision.v3"
    )
    assert decision["use_dense"] is False
    assert decision["available_vram_is_finite_positive"] is False
    assert decision["free_vram_bytes"] is None
    assert decision["free_vram_gib"] is None
    assert decision["dense_vram_budget_bytes"] is None
    assert decision["dense_vram_budget_gib"] is None
    assert "invalid_available_vram_bytes" in decision["route_reasons"]


def test_auto_routed_carrier_envelope_uses_v4_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf_execution

    monkeypatch.setattr(carrier, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(carrier, "_available_vram_bytes", lambda _device: 0)
    monkeypatch.setattr(mcwf_execution, "_require_cuda_device", lambda _device: "cuda")

    manifest = carrier.axis1_carrier_execution_manifest(
        _six_bit_measurement_schedule(),
        execution_backend_contract=carrier.AXIS1_CARRIER_AUTO_BACKEND_CONTRACT,
        execution_backend_options={
            "local_dims": [3] * 6,
            "max_bond": 1,
        },
    )

    assert manifest["schema"] == (
        "error_coupling_simulator.frontend.carrier_auto_routed_execution.v4"
    )


def test_mcwf_completed_and_blocked_acceptance_policies_use_v6_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf_execution

    expected_schema = (
        "error_coupling_simulator.frontend."
        "mcwf_mps_restricted_acceptance_policy.v6"
    )
    completed_policy = _mcwf_policy()

    monkeypatch.setattr(mcwf_execution, "_require_cuda_device", lambda _device: "cuda")
    blocked_manifest = mcwf_execution.axis1_mcwf_mps_state_record_execution_manifest(
        _six_bit_measurement_schedule(),
        local_dims=[3] * 6,
        max_bond=1,
    )

    assert completed_policy["schema"] == expected_schema
    assert blocked_manifest["execution_status"] == "blocked"
    assert blocked_manifest["restricted_acceptance_policy"]["schema"] == expected_schema


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("accepted_for_restricted_execution", "false"),
        ("diagnostic_only", "false"),
    ],
)
def test_direct_mcwf_manifest_rejects_truthy_nonboolean_policy_state(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: str,
) -> None:
    policy = _completed_direct_mcwf_policy()
    policy[field] = corrupted_value

    with pytest.raises(TypeError):
        _run_direct_mcwf_with_policy(monkeypatch, policy)


def _run_direct_mcwf_with_policy(
    monkeypatch: pytest.MonkeyPatch,
    policy: dict[str, Any],
) -> dict[str, Any]:
    import error_coupling_simulator.certify.axis1_mps as dense
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    monkeypatch.setattr(mcwf, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(
        mcwf,
        "_first_order_mass_residual_blocks",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        mcwf,
        "_execute_sampled_mcwf_program",
        lambda *_args, **_kwargs: {
            "fixture": "execution",
            "trajectory_sampling": {
                "mode": "sampled_fixed_microstep_mcwf_trajectories"
            },
        },
    )
    monkeypatch.setattr(
        dense,
        "dense_jointL_record_certification",
        lambda *_args, **_kwargs: {"fixture": "certification"},
    )
    def _policy_stub(**kwargs):
        returned = copy.deepcopy(policy)
        returned.setdefault(
            "dynamics_artifact_reference_certification",
            kwargs["dynamics_artifact_reference_certification"],
        )
        return returned

    monkeypatch.setattr(
        dense,
        "restricted_acceptance_policy",
        _policy_stub,
    )

    return mcwf.axis1_mcwf_mps_state_record_execution_manifest(
        _six_bit_measurement_schedule(),
        trajectory_count=1,
        rng_seed=11,
    )


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("certification_status", "accepted"),
        ("blocked_reason", None),
        ("accepted_for_production_scalable_backend", True),
        ("accepted_for_exact_dense_probability_evidence", True),
        ("accepted_for_sampled_execution_evidence", True),
    ],
)
def test_direct_mcwf_manifest_rejects_inconsistent_policy_state(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: Any,
) -> None:
    policy = _completed_direct_mcwf_policy()
    policy[field] = corrupted_value

    with pytest.raises(ValueError):
        _run_direct_mcwf_with_policy(monkeypatch, policy)


def test_direct_mcwf_stable_payload_hash_rejects_nonfinite_values() -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    with pytest.raises(ValueError):
        mcwf._stable_payload_hash({"value": float("nan")})


def _completed_direct_mcwf_policy(**overrides: Any) -> dict[str, Any]:
    policy = {
        "schema": (
            "error_coupling_simulator.frontend."
            "mcwf_mps_restricted_acceptance_policy.v6"
        ),
        "policy_role": "restricted_execution_acceptance_not_metric",
        "execution_status": "completed",
        "certification_status": "rejected",
        "diagnostic_only": False,
        "accepted_for_restricted_execution": False,
        "accepted_for_sampled_execution_evidence": False,
        "accepted_for_exact_dense_probability_evidence": False,
        "accepted_for_production_scalable_backend": False,
        "blocked_reason": "fixture_rejected",
        "trajectory": {"mode": "sampled_fixed_microstep_mcwf_trajectories"},
    }
    policy.update(overrides)
    return policy


def test_direct_mcwf_manifest_requires_policy_trajectory_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _completed_direct_mcwf_policy()
    del policy["trajectory"]

    with pytest.raises(TypeError):
        _run_direct_mcwf_with_policy(monkeypatch, policy)


def test_direct_mcwf_manifest_binds_policy_to_actual_trajectory_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _completed_direct_mcwf_policy()
    policy["trajectory"]["mode"] = "exact_branch_enumeration"

    with pytest.raises(ValueError):
        _run_direct_mcwf_with_policy(monkeypatch, policy)


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("schema", "corrupted.policy.v99"),
        ("policy_role", "metric"),
        ("execution_status", "blocked"),
    ],
)
def test_direct_mcwf_manifest_pins_completed_policy_identity(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: str,
) -> None:
    policy = _completed_direct_mcwf_policy(**{field: corrupted_value})

    with pytest.raises(ValueError):
        _run_direct_mcwf_with_policy(monkeypatch, policy)


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("accepted_for_exact_dense_probability_evidence", True),
        ("accepted_for_sampled_execution_evidence", False),
    ],
)
def test_direct_mcwf_manifest_enforces_sampled_only_acceptance_tier(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: bool,
) -> None:
    policy = _completed_direct_mcwf_policy(
        certification_status="accepted",
        accepted_for_restricted_execution=True,
        accepted_for_sampled_execution_evidence=True,
        blocked_reason=None,
    )
    policy[field] = corrupted_value

    with pytest.raises(ValueError):
        _run_direct_mcwf_with_policy(monkeypatch, policy)


def test_qt_seed_sweep_rejects_truthy_nonboolean_child_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def corrupted_run(schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=True,
            schedule=schedule,
            trajectory_count=kwargs["trajectory_count"],
            rng_seed=kwargs["rng_seed"],
        )
        child["restricted_acceptance_policy"][
            "accepted_for_sampled_execution_evidence"
        ] = "false"
        return child

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        corrupted_run,
    )

    with pytest.raises(TypeError):
        qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
            _six_bit_measurement_schedule(),
            trajectory_count=2,
            rng_seeds=(3, 5),
            seed_record_frequency_spread_gate=0.0,
        )


@pytest.mark.parametrize(
    "corrupted_field",
    ["seed_evaluated", "seed_passed", "dense_accepted"],
)
def test_qt_seed_sweep_rejects_truthy_nonboolean_gate_flags(
    monkeypatch: pytest.MonkeyPatch,
    corrupted_field: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def accepted_run(schedule: Any, **kwargs: Any) -> dict[str, Any]:
        return _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=True,
            schedule=schedule,
            trajectory_count=kwargs["trajectory_count"],
            rng_seed=kwargs["rng_seed"],
        )

    seed_gate = {
        "evaluated": "false" if corrupted_field == "seed_evaluated" else True,
        "passed": "false" if corrupted_field == "seed_passed" else True,
    }
    dense_accepted: Any = (
        "false" if corrupted_field == "dense_accepted" else True
    )
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        accepted_run,
    )
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_comparison",
        lambda *_args, **_kwargs: {
            "seed_spread_gate": seed_gate,
            "comparison_outcome_is_metric": False,
        },
    )
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_dense_calibration",
        lambda *_args, **_kwargs: {
            "accepted_as_dense_calibrated_trajectory_evidence": dense_accepted,
            "comparison_outcome_is_metric": False,
        },
    )

    with pytest.raises(TypeError):
        qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
            _six_bit_measurement_schedule(),
            trajectory_count=2,
            rng_seeds=(3, 5),
            seed_record_frequency_spread_gate=0.0,
        )


def test_qt_bond_sweep_rejects_truthy_nonboolean_reference_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def corrupted_run(schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
            schedule=schedule,
        )
        child["restricted_acceptance_policy"]["mps_truncation"][
            "accepted_as_exact_bond_representation"
        ] = "false"
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        corrupted_run,
    )

    with pytest.raises(TypeError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )


def test_qt_bond_sweep_rejects_failed_reference_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def failed_run(schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
            schedule=schedule,
        )
        return _reject_qt_child_with_dense_record_disagreement(
            qt,
            schedule,
            child,
        )

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", failed_run)
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

    manifest = qt.axis1_qt_mps_bond_sweep_manifest(
        _six_bit_measurement_schedule(),
        bond_values=(1, 2),
        convergence_record_probability_gate=0.0,
    )

    assert manifest["passed"] is False
    assert manifest["verdict"] == "fail"
    assert manifest["convergence_policy"][
        "accepted_as_restricted_convergence_evidence"
    ] is False


def test_qt_seed_sweep_rejects_failed_children_with_forged_nested_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def failed_run(schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=True,
            schedule=schedule,
            trajectory_count=kwargs["trajectory_count"],
            rng_seed=kwargs["rng_seed"],
        )
        child.update(
            verdict="fail",
            passed=False,
            certification_status="rejected",
            blocked_reason="fixture_rejected",
        )
        child["restricted_acceptance_policy"].update(
            certification_status="rejected",
            blocked_reason="fixture_rejected",
            accepted_for_restricted_execution=False,
        )
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", failed_run)
    calls = _install_qt_seed_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
            _six_bit_measurement_schedule(),
            trajectory_count=2,
            rng_seeds=(3, 5),
            seed_record_frequency_spread_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


def test_qt_evidence_bundle_rejects_truthy_nonboolean_child_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _one_bit_measurement_schedule()
    bond, trajectory = _qt_canonical_aggregate_children(
        monkeypatch,
        qt,
        schedule,
    )
    bond["convergence_policy"][
        "accepted_as_restricted_convergence_evidence"
    ] = "false"
    bond["content_hash"] = qt._stable_payload_hash(bond)
    monkeypatch.setattr(
        qt, "axis1_qt_mps_bond_sweep_manifest", lambda *_args, **_kwargs: bond
    )
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        lambda *_args, **_kwargs: trajectory,
    )

    with pytest.raises(TypeError):
        qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=2,
            rng_seeds=(3, 5),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


@pytest.mark.parametrize("child_kind", ["bond", "trajectory"])
def test_qt_evidence_bundle_rejects_failed_child_with_forged_acceptance(
    monkeypatch: pytest.MonkeyPatch,
    child_kind: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _one_bit_measurement_schedule()
    bond, trajectory = _qt_canonical_aggregate_children(
        monkeypatch,
        qt,
        schedule,
    )
    child = bond if child_kind == "bond" else trajectory
    child["passed"] = False
    child["verdict"] = "fail"
    child["content_hash"] = qt._stable_payload_hash(child)
    monkeypatch.setattr(qt, "axis1_qt_mps_bond_sweep_manifest", lambda *_a, **_k: bond)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        lambda *_a, **_k: trajectory,
    )

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=2,
            rng_seeds=(3, 5),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


def test_qt_resource_probe_rejects_truthy_nonboolean_workload_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(qt.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(qt.torch.cuda, "reset_peak_memory_stats", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "synchronize", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_allocated", lambda _device: 1)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_reserved", lambda _device: 1)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: {
            "schema": "corrupted.bundle.v1",
            "content_hash": "bundle",
            "passed": "false",
        },
    )

    with pytest.raises(TypeError):
        qt.axis1_qt_mps_resource_probe_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            trajectory_count=2,
            rng_seeds=(3, 5),
        )


def test_qt_resource_probe_rejects_workload_verdict_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(qt.torch.cuda, "empty_cache", lambda: None)
    monkeypatch.setattr(qt.torch.cuda, "reset_peak_memory_stats", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "synchronize", lambda _device: None)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_allocated", lambda _device: 1)
    monkeypatch.setattr(qt.torch.cuda, "max_memory_reserved", lambda _device: 1)
    schedule = _one_bit_measurement_schedule()
    bundle = _qt_canonical_bundle_fixture(monkeypatch, qt, schedule)
    bundle["verdict"] = "fail"
    bundle["content_hash"] = qt._stable_payload_hash(bundle)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: bundle,
    )

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_resource_probe_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=2,
            rng_seeds=(3, 5),
            convergence_record_probability_gate=0.0,
            seed_record_frequency_spread_gate=0.0,
            dense_record_frequency_gate=0.0,
        )


def test_carrier_auto_envelope_rejects_truthy_nonboolean_child_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    schedule = SimpleNamespace(source_kind="fixture", source_hash="fixture-hash")
    monkeypatch.setattr(carrier, "_require_cuda_device", lambda _device: "cuda")
    monkeypatch.setattr(
        carrier,
        "axis1_carrier_program_manifest",
        lambda _schedule: {"requires_scalable_backend": False},
    )
    monkeypatch.setattr(
        carrier,
        "_select_dense_or_mcwf",
        lambda *_args: (carrier.AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT, {}),
    )
    monkeypatch.setattr(
        carrier,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: {
            "verdict": "fail",
            "passed": "false",
            "blocked_reason": "corrupted_child",
        },
    )

    with pytest.raises(TypeError):
        carrier._axis1_auto_routed_execution_manifest(
            schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options=None,
        )


def test_carrier_mcwf_wrapper_rejects_truthy_nonboolean_child_verdict(
    monkeypatch: pytest.MonkeyPatch,
    carrier_measurement_schedule,
    honest_carrier_mcwf_child,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    schedule = carrier_measurement_schedule
    monkeypatch.setattr(carrier, "_require_cuda_device", lambda _device: "cuda")
    child = copy.deepcopy(honest_carrier_mcwf_child)
    child["passed"] = "false"
    _rehash_manifest(child)
    monkeypatch.setattr(
        mcwf,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: child,
    )

    with pytest.raises(TypeError):
        carrier._axis1_mcwf_mps_execution_manifest(
            schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_carrier_qt_wrapper_rejects_truthy_nonboolean_dense_execution_flag(
    monkeypatch: pytest.MonkeyPatch,
    carrier_measurement_schedule,
    honest_carrier_qt_child,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = carrier_measurement_schedule
    child = copy.deepcopy(honest_carrier_qt_child)
    child["dense_jointL_record_certification"]["executed"] = "false"
    _rehash_manifest(child)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: child,
    )

    with pytest.raises(TypeError):
        carrier._axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options=None,
        )


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("blocked_reason", "policy_only_blocker"),
        ("accepted_for_production_scalable_backend", True),
        ("accepted_for_exact_dense_probability_evidence", True),
        ("accepted_for_sampled_execution_evidence", True),
    ],
)
def test_carrier_restricted_policy_binds_blocker_and_acceptance_implications(
    field: str,
    corrupted_value: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    policy = {
        "execution_status": "completed",
        "certification_status": "rejected",
        "diagnostic_only": False,
        "blocked_reason": "child_blocker",
        "accepted_for_restricted_execution": False,
        "accepted_for_exact_dense_probability_evidence": False,
        "accepted_for_sampled_execution_evidence": False,
        "accepted_for_production_scalable_backend": False,
    }
    policy[field] = corrupted_value

    with pytest.raises(ValueError):
        carrier._validate_restricted_policy_state(
            policy,
            execution_status="completed",
            certification_status="rejected",
            diagnostic_only=False,
            blocked_reason="child_blocker",
            context="fixture/MPS",
        )


def _carrier_route_policy(
    *,
    route_kind: str,
    mode: str,
) -> dict[str, Any]:
    exact = mode == "exact_branch_enumeration"
    policy = {
        "schema": (
            "error_coupling_simulator.frontend."
            + (
                "mcwf_mps_restricted_acceptance_policy.v6"
                if route_kind == "mcwf"
                else "qt_mps_restricted_acceptance_policy.v2"
            )
        ),
        "policy_role": "restricted_execution_acceptance_not_metric",
        "execution_status": "completed",
        "certification_status": "accepted",
        "diagnostic_only": False,
        "blocked_reason": None,
        "accepted_for_restricted_execution": True,
        "accepted_for_exact_dense_probability_evidence": exact,
        "accepted_for_sampled_execution_evidence": not exact,
        "accepted_for_production_scalable_backend": False,
        "trajectory": {"mode": mode},
    }
    if route_kind == "mcwf":
        policy.update(
            {
                "accepted_as_restricted_overcap_execution": False,
                "gross_strict_gate_split": {},
                "dense_jointL_record_certification": {},
                "finite_step": {},
                "mps_truncation": {},
                "probability": {},
                "dynamics_artifact_reference_certification": {},
                "production_blockers": [],
                "scored_quantity_policy": "fixture policy identity only",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "a/c",
            }
        )
    return policy


@pytest.mark.parametrize(
    ("route_kind", "mode"),
    [
        ("mcwf", "sampled_fixed_microstep_mcwf_trajectories"),
        ("qt", "exact_branch_enumeration"),
        ("qt", "sampled_product_channel_trajectories"),
    ],
)
def test_carrier_accepts_only_route_bound_policy_identity_and_tier(
    route_kind: str,
    mode: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    carrier._validate_restricted_policy_state(
        _carrier_route_policy(route_kind=route_kind, mode=mode),
        execution_status="completed",
        certification_status="accepted",
        diagnostic_only=False,
        blocked_reason=None,
        context=f"fixture/{route_kind}",
        route_kind=route_kind,
    )


@pytest.mark.parametrize(
    ("route_kind", "mode", "field", "corrupted_value"),
    [
        (
            "mcwf",
            "sampled_fixed_microstep_mcwf_trajectories",
            "schema",
            "corrupted.mcwf.policy.v99",
        ),
        (
            "mcwf",
            "sampled_fixed_microstep_mcwf_trajectories",
            "accepted_for_sampled_execution_evidence",
            False,
        ),
        (
            "mcwf",
            "sampled_fixed_microstep_mcwf_trajectories",
            "accepted_for_exact_dense_probability_evidence",
            True,
        ),
        (
            "qt",
            "exact_branch_enumeration",
            "accepted_for_exact_dense_probability_evidence",
            False,
        ),
        (
            "qt",
            "exact_branch_enumeration",
            "accepted_for_sampled_execution_evidence",
            True,
        ),
        (
            "qt",
            "sampled_product_channel_trajectories",
            "accepted_for_exact_dense_probability_evidence",
            True,
        ),
        (
            "qt",
            "sampled_product_channel_trajectories",
            "accepted_for_sampled_execution_evidence",
            False,
        ),
        (
            "qt",
            "sampled_product_channel_trajectories",
            "schema",
            "corrupted.qt.policy.v99",
        ),
    ],
)
def test_carrier_rejects_route_policy_schema_or_tier_corruption(
    route_kind: str,
    mode: str,
    field: str,
    corrupted_value: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    policy = _carrier_route_policy(route_kind=route_kind, mode=mode)
    policy[field] = corrupted_value
    with pytest.raises(ValueError):
        carrier._validate_restricted_policy_state(
            policy,
            execution_status="completed",
            certification_status="accepted",
            diagnostic_only=False,
            blocked_reason=None,
            context=f"fixture/{route_kind}",
            route_kind=route_kind,
        )


def test_carrier_mcwf_wrapper_rejects_inconsistent_child_state_machine() -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier

    with pytest.raises(ValueError):
        carrier._validate_restricted_child_state_machine(
            passed=True,
            child_verdict="pass",
            backend_executed=True,
            execution_status="completed",
            certification_status="rejected",
            diagnostic_only=False,
            blocked_reason=None,
            context="fixture/mcwf",
        )


@pytest.mark.parametrize(
    "corruption",
    [
        "backend_not_executed",
        "policy_state_mismatch",
        "trajectory_mode_mismatch",
    ],
)
def test_carrier_mcwf_wrapper_binds_backend_and_policy_state(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
    carrier_measurement_schedule,
    honest_carrier_mcwf_child,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as mcwf

    schedule = carrier_measurement_schedule
    monkeypatch.setattr(carrier, "_require_cuda_device", lambda _device: "cuda")
    child = copy.deepcopy(honest_carrier_mcwf_child)
    if corruption == "backend_not_executed":
        child["mcwf_mps_backend_executed"] = False
    elif corruption == "trajectory_mode_mismatch":
        child["mps_execution"]["trajectory_sampling"]["mode"] = (
            "exact_branch_enumeration"
        )
    else:
        child["restricted_acceptance_policy"]["execution_status"] = "blocked"
        child["restricted_acceptance_policy"]["certification_status"] = "not_evaluated"
    _rehash_manifest(child)
    monkeypatch.setattr(
        mcwf,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: child,
    )

    with pytest.raises(ValueError):
        carrier._axis1_mcwf_mps_execution_manifest(
            schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    "corruption",
    [
        "backend_not_executed",
        "policy_state_mismatch",
        "trajectory_mode_mismatch",
        "execution_claim_mismatch",
    ],
)
def test_carrier_qt_wrapper_binds_backend_and_policy_state(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
    carrier_measurement_schedule,
    honest_carrier_qt_child,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = carrier_measurement_schedule
    child = copy.deepcopy(honest_carrier_qt_child)
    if corruption == "backend_not_executed":
        child["qt_mps_backend_executed"] = False
    elif corruption == "trajectory_mode_mismatch":
        child["mps_execution"]["trajectory_sampling"]["mode"] = (
            "sampled_product_channel_trajectories"
        )
    elif corruption == "execution_claim_mismatch":
        child["claims_qt_mps_backend_execution"] = False
    else:
        child["restricted_acceptance_policy"]["execution_status"] = "blocked"
        child["restricted_acceptance_policy"]["certification_status"] = "not_evaluated"
    _rehash_manifest(child)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: child,
    )

    with pytest.raises(ValueError):
        carrier._axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options=None,
        )


def test_carrier_qt_wrapper_rejects_child_verdict_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    carrier_measurement_schedule,
    honest_carrier_qt_child,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = carrier_measurement_schedule
    child = copy.deepcopy(honest_carrier_qt_child)
    child["verdict"] = "pass"
    _rehash_manifest(child)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: child,
    )

    with pytest.raises(ValueError):
        carrier._axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options=None,
        )


def test_mcwf_dense_certification_rejects_nonboolean_overcap_flag() -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    with pytest.raises(TypeError):
        dense_jointL_record_certification(
            SimpleNamespace(),
            {},
            {"requires_scalable_backend": "true"},
        )


def test_mcwf_dense_certification_rejects_truthy_nonboolean_seed_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_certify_record_path",
        lambda *_args, **_kwargs: {
            "executed": True,
            "passed": True,
            "passed_gross": True,
            "comparison_outcome_is_metric": True,
        },
    )

    with pytest.raises(TypeError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": "false",
                    "trajectory_count": 2,
                },
                "evaluator_only_diagnostics": (
                    _mcwf_evaluator_only_diagnostics()
                ),
                "measurement_keys": ["m0"],
            },
            {"requires_scalable_backend": False},
        )


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("record_tv_gate", float("nan"), ValueError),
        ("record_gross_tv_gate", float("nan"), ValueError),
        ("process_infidelity_gate", float("inf"), ValueError),
        ("gross_gate", True, TypeError),
        ("record_sampling_confidence", float("nan"), ValueError),
    ],
)
def test_mcwf_dense_certification_rejects_invalid_metric_gate_inputs(
    field: str,
    value: Any,
    error_type: type[Exception],
) -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    kwargs = {field: value}
    with pytest.raises(error_type):
        dense_jointL_record_certification(
            SimpleNamespace(),
            {},
            {"requires_scalable_backend": True},
            **kwargs,
        )


@pytest.mark.parametrize("owner", ["carrier", "oracle"])
@pytest.mark.parametrize(
    "invalid_probabilities",
    [[float("nan")], [2.0], [-1.0]],
    ids=["nan", "unnormalized", "negative"],
)
def test_mcwf_dense_record_certification_rejects_invalid_probability_distributions(
    monkeypatch: pytest.MonkeyPatch,
    owner: str,
    invalid_probabilities: list[float],
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf
    import error_coupling_simulator.frontend.axis1_record_evidence as record_evidence

    tv_calls = 0

    def tv_sentinel(*_args: Any, **_kwargs: Any) -> float:
        nonlocal tv_calls
        tv_calls += 1
        raise AssertionError("TV comparison must not run for invalid distributions")

    monkeypatch.setattr(mcwf, "_total_variation_distance", tv_sentinel)

    carrier_probabilities = [1.0]
    oracle_probabilities = [1.0]
    if owner == "carrier":
        carrier_probabilities = invalid_probabilities
    else:
        oracle_probabilities = invalid_probabilities

    monkeypatch.setattr(
        record_evidence,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: {
            "schema": (
                "error_coupling_simulator.frontend."
                "measurement_record_evidence.v1"
            ),
            "content_hash": "d" * 64,
            "record_evidence": {
                "measurement_records": [[0]],
                "record_probabilities": oracle_probabilities,
            },
        },
    )

    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 2,
                },
                "evaluator_only_diagnostics": (
                    _mcwf_evaluator_only_diagnostics()
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "measurement_records": [[0]],
                "record_counts": [2],
                "record_probabilities": carrier_probabilities,
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )

    assert tv_calls == 0


@pytest.mark.parametrize("owner", ["carrier", "oracle"])
@pytest.mark.parametrize(
    "invalid_probabilities",
    [[float("nan")], [2.0], [-1.0]],
    ids=["nan", "unnormalized", "negative"],
)
def test_qt_dense_record_certification_rejects_invalid_probability_distributions(
    monkeypatch: pytest.MonkeyPatch,
    owner: str,
    invalid_probabilities: list[float],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    carrier_probabilities = [1.0]
    oracle_probabilities = [1.0]
    if owner == "carrier":
        carrier_probabilities = invalid_probabilities
    else:
        oracle_probabilities = invalid_probabilities
    schedule = _one_bit_measurement_schedule()
    dense = _qt_authenticated_dense_record(qt, schedule)
    if owner == "oracle":
        dense["record_evidence"]["record_probabilities"] = [
            *oracle_probabilities,
            0.0,
        ]
        if all(math.isfinite(value) for value in oracle_probabilities):
            _rehash_manifest(dense)
    normalization_names: list[str] = []
    original_normalize = qt._normalize_probability_distribution

    def tracked_normalize(values: Any, *, name: str) -> list[float]:
        normalization_names.append(name)
        return original_normalize(values, name=name)

    monkeypatch.setattr(qt, "_normalize_probability_distribution", tracked_normalize)
    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: dense,
    )

    with pytest.raises(ValueError):
        qt._dense_record_certification(
            schedule,
            program={"requires_scalable_backend": False},
            execution={
                "trajectory_sampling": {"mode": "exact_branch_enumeration"},
                "measurement_keys": ["m0"],
                "measurement_records": [[0]],
                "record_probabilities": carrier_probabilities,
            },
            device="cuda",
        )

    if owner == "carrier":
        assert "carrier_record_probabilities" in normalization_names
    elif all(math.isfinite(value) for value in oracle_probabilities):
        assert "record_probabilities" in normalization_names
    else:
        assert normalization_names == []


def test_qt_dense_record_certification_rejects_nonboolean_overcap_flag() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    with pytest.raises(TypeError):
        qt._dense_record_certification(
            SimpleNamespace(),
            program={"requires_scalable_backend": "false"},
            execution={
                "trajectory_sampling": {"mode": "exact_branch_enumeration"},
                "measurement_keys": [],
            },
            device="cuda",
        )


def test_mcwf_policy_rejects_nonfinite_claim_bearing_metric() -> None:
    certification = _mcwf_metric_certification(
        value=float("nan"),
        passed=False,
        passed_gross=False,
    )

    with pytest.raises(ValueError):
        _mcwf_policy(certification=certification)


@pytest.mark.parametrize(
    "missing_field",
    [
        "dense_evidence_schema",
        "dense_evidence_content_hash",
        "comparison_object",
        "max_abs_probability_difference",
        "threshold",
    ],
)
def test_qt_policy_requires_bound_dense_evidence_for_passing_certification(
    missing_field: str,
) -> None:
    certification = _qt_dense_certification()
    certification.pop(missing_field)

    with pytest.raises(KeyError):
        _qt_policy(certification=certification)


def test_qt_policy_rejects_dense_verdict_threshold_mismatch() -> None:
    certification = _qt_dense_certification(
        max_abs_probability_difference=0.2,
        threshold=1.0e-8,
        passed=True,
    )

    with pytest.raises(ValueError):
        _qt_policy(certification=certification)


def test_mcwf_policy_rejects_passing_nonmetric_certification() -> None:
    certification = {
        "executed": True,
        "passed": True,
        "passed_gross": True,
        "comparison_outcome_is_metric": False,
    }

    with pytest.raises(ValueError):
        _mcwf_policy(certification=certification)


@pytest.mark.parametrize(
    ("overrides", "mismatch_field"),
    [
        (
            {
                "value": 0.05,
                "gate": 1.0e-6,
                "gross_gate": 0.1,
                "passed": True,
                "passed_gross": True,
            },
            "certification.passed",
        ),
        (
            {
                "value": 0.5,
                "gate": 1.0e-6,
                "gross_gate": 0.1,
                "passed": False,
                "passed_gross": True,
            },
            "certification.passed_gross",
        ),
    ],
)
def test_mcwf_policy_rejects_metric_verdict_gate_mismatch(
    overrides: dict[str, Any],
    mismatch_field: str,
) -> None:
    certification = _mcwf_metric_certification(**overrides)

    with pytest.raises(ValueError):
        _mcwf_policy(certification=certification)


@pytest.mark.parametrize(
    ("field", "replacement", "error_type"),
    [
        ("comparison_object", None, KeyError),
        ("metric", None, KeyError),
        ("metric_convention", None, KeyError),
        ("oracle", None, KeyError),
        ("oracle_independent_of_carrier_grouping", None, KeyError),
        ("oracle_independent_of_carrier_grouping", False, ValueError),
        ("metric", "not_a_metric", ValueError),
    ],
)
def test_mcwf_policy_requires_bound_independent_metric_identity(
    field: str,
    replacement: Any,
    error_type: type[Exception],
) -> None:
    certification = _mcwf_metric_certification()
    if replacement is None:
        certification.pop(field)
    else:
        certification[field] = replacement

    with pytest.raises(error_type):
        _mcwf_policy(certification=certification)


def test_mcwf_policy_rejects_unknown_trajectory_sampling_mode() -> None:
    with pytest.raises(ValueError):
        _mcwf_policy(
            execution_overrides={
                "trajectory_sampling": {
                    "mode": "",
                    "trajectory_count": 2,
                }
            },
        )


def test_mcwf_dense_level_certification_rejects_record_count_length_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: {(0,): 1.0},
    )
    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 1,
                },
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=[[0], [1]],
                    level_record_counts=[1],
                    level_record_probabilities=[1.0],
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )


@pytest.mark.parametrize(
    ("invalid_count", "error_type"),
    [(True, TypeError), ("1", TypeError), (1.5, TypeError), (-1, ValueError)],
)
def test_mcwf_dense_level_certification_rejects_invalid_counts(
    monkeypatch: pytest.MonkeyPatch,
    invalid_count: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    oracle_calls = 0

    def oracle_sentinel(*_args: Any, **_kwargs: Any) -> dict[tuple[int, ...], float]:
        nonlocal oracle_calls
        oracle_calls += 1
        raise AssertionError("dense oracle must not run for invalid counts")

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        oracle_sentinel,
    )
    with pytest.raises(error_type):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 1,
                },
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=[[0]],
                    level_record_counts=[invalid_count],
                    level_record_probabilities=[1.0],
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )

    assert oracle_calls == 0


@pytest.mark.parametrize(
    "oracle_distribution",
    [
        {(0,): float("nan")},
        {(0,): float("inf")},
        {(0,): -1.0, (1,): 2.0},
        {(0,): 2.0},
        {},
    ],
    ids=["nan", "inf", "negative", "unnormalized", "empty"],
)
def test_mcwf_dense_level_certification_rejects_invalid_oracle_distribution(
    monkeypatch: pytest.MonkeyPatch,
    oracle_distribution: dict[tuple[int, ...], float],
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    tv_calls = 0

    def tv_sentinel(*_args: Any, **_kwargs: Any) -> float:
        nonlocal tv_calls
        tv_calls += 1
        raise AssertionError("TV comparison must not run for invalid oracle data")

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: oracle_distribution,
    )
    monkeypatch.setattr(mcwf, "_total_variation_distance_dict", tv_sentinel)
    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 1,
                },
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=[[0]],
                    level_record_counts=[1],
                    level_record_probabilities=[1.0],
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )

    assert tv_calls == 0


def test_mcwf_sampled_record_certification_binds_counts_to_probabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf
    import error_coupling_simulator.frontend.axis1_record_evidence as record_evidence

    monkeypatch.setattr(
        record_evidence,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: {
            "schema": (
                "error_coupling_simulator.frontend.measurement_record_evidence.v1"
            ),
            "content_hash": "d" * 64,
            "record_evidence": {
                "measurement_records": [[0], [1]],
                "record_probabilities": [0.5, 0.5],
            },
        },
    )
    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 2,
                },
                "evaluator_only_diagnostics": (
                    _mcwf_evaluator_only_diagnostics()
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "measurement_records": [[0], [1]],
                "record_counts": [1, 1],
                "record_probabilities": [0.9, 0.1],
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )


def test_mcwf_record_gross_tv_gate_controls_record_certification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf
    import error_coupling_simulator.frontend.axis1_record_evidence as record_evidence

    monkeypatch.setattr(
        record_evidence,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: {
            "schema": (
                "error_coupling_simulator.frontend.measurement_record_evidence.v1"
            ),
            "content_hash": "d" * 64,
            "record_evidence": {
                "measurement_records": [[0], [1]],
                "record_probabilities": [1.0, 0.0],
            },
        },
    )
    certification = mcwf.dense_jointL_record_certification(
        SimpleNamespace(),
        {
            "trajectory_sampling": {
                "mode": "sampled_fixed_microstep_mcwf_trajectories",
                "rng_seed_was_explicit": True,
                "trajectory_count": 10_000,
            },
            "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(),
            "measurement_keys": ["m0"],
            "measurement_targets": [0],
            **_mcwf_ordered_measurement_metadata(),
            "measurement_records": [[0], [1]],
            "record_counts": [8_500, 1_500],
            "record_probabilities": [0.85, 0.15],
            "local_dims": [2],
        },
        {"requires_scalable_backend": False},
        declared_local_dims=[2],
        record_tv_gate=1.0e-6,
        record_gross_tv_gate=0.1,
    )

    assert certification["value"] == pytest.approx(0.15)
    assert certification["gross_gate"] == pytest.approx(0.1)
    assert certification["passed"] is False
    assert certification["passed_gross"] is False


def test_mcwf_sampled_level_certification_binds_counts_to_trajectory_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: {(0,): 1.0},
    )
    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 2,
                },
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=[[0]],
                    level_record_counts=[1],
                    level_record_probabilities=[0.5],
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )


@pytest.mark.parametrize(
    ("metric_result", "invalid_field"),
    [
        ((float("nan"), 0.0), "process_infidelity"),
        ((-1.0, 0.0), "process_infidelity"),
        ((1.1, 0.0), "process_infidelity"),
        ((0.0, float("inf")), "choi_trace_distance"),
    ],
)
def test_mcwf_dense_channel_certification_rejects_invalid_metric_postcondition(
    monkeypatch: pytest.MonkeyPatch,
    metric_result: tuple[float, float],
    invalid_field: str,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_build_carrier_channel_window",
        lambda *_args, **_kwargs: {
            "carrier_superop": None,
            "oracle_kraus": None,
            "dim": 2,
        },
    )
    monkeypatch.setattr(
        mcwf,
        "_process_infidelity_and_choi_distance",
        lambda *_args, **_kwargs: metric_result,
    )
    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "exact_branch_enumeration",
                    "rng_seed_was_explicit": False,
                    "trajectory_count": 1,
                },
                "evaluator_only_diagnostics": (
                    _mcwf_evaluator_only_diagnostics()
                ),
                "measurement_keys": [],
                "measurement_targets": [],
                **_mcwf_ordered_measurement_metadata(()),
            },
            {"requires_scalable_backend": False},
        )


def test_mcwf_policy_rejects_nonstring_nonmetric_reason() -> None:
    with pytest.raises(TypeError):
        _mcwf_policy(
            certification={
                "executed": False,
                "passed": False,
                "passed_gross": False,
                "comparison_outcome_is_metric": False,
                "reason": float("nan"),
            }
        )


_INVALID_OPTIONAL_GATES = [
    pytest.param("0.1", TypeError, id="numeric-string"),
    pytest.param(False, TypeError, id="false"),
    pytest.param(True, TypeError, id="true"),
    pytest.param(-1.0, ValueError, id="negative"),
    pytest.param(float("nan"), ValueError, id="nan"),
    pytest.param(float("inf"), ValueError, id="posinf"),
    pytest.param(float("-inf"), ValueError, id="neginf"),
]


@pytest.mark.parametrize(
    ("gate_name", "surface"),
    [
        ("convergence_record_probability_gate", "bond"),
        ("seed_record_frequency_spread_gate", "seed"),
        ("dense_record_frequency_gate", "seed"),
        ("min_peak_allocated_gib", "resource"),
        ("min_peak_reserved_gib", "resource"),
    ],
)
@pytest.mark.parametrize(("invalid_gate", "error_type"), _INVALID_OPTIONAL_GATES)
def test_qt_mps_optional_gates_reject_invalid_values_before_delegate(
    monkeypatch: pytest.MonkeyPatch,
    gate_name: str,
    surface: str,
    invalid_gate: Any,
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    delegate_calls = 0

    def delegate_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal delegate_calls
        delegate_calls += 1
        raise RuntimeError("DELEGATE_SENTINEL")

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        delegate_sentinel,
    )
    monkeypatch.setattr(qt, "_require_cuda_device", delegate_sentinel)
    schedule = _six_bit_measurement_schedule()
    with pytest.raises(error_type):
        if surface == "bond":
            qt.axis1_qt_mps_bond_sweep_manifest(
                schedule,
                bond_values=(1, 2),
                **{gate_name: invalid_gate},
            )
        elif surface == "seed":
            qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
                schedule,
                trajectory_count=1,
                rng_seeds=(0, 1),
                **{gate_name: invalid_gate},
            )
        else:
            qt.axis1_qt_mps_resource_probe_manifest(
                schedule,
                bond_values=(1, 2),
                trajectory_count=1,
                rng_seeds=(0, 1),
                **{gate_name: invalid_gate},
            )

    assert delegate_calls == 0


@pytest.mark.parametrize(
    "nested_gate_name",
    [
        "convergence_record_probability_gate",
        "seed_record_frequency_spread_gate",
        "dense_record_frequency_gate",
    ],
)
def test_resource_probe_validates_nested_gates_before_cuda(
    monkeypatch: pytest.MonkeyPatch,
    nested_gate_name: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    cuda_calls = 0

    def cuda_sentinel(*_args: Any, **_kwargs: Any) -> str:
        nonlocal cuda_calls
        cuda_calls += 1
        raise RuntimeError("CUDA_SENTINEL")

    monkeypatch.setattr(qt, "_require_cuda_device", cuda_sentinel)
    with pytest.raises(ValueError):
        qt.axis1_qt_mps_resource_probe_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            trajectory_count=1,
            rng_seeds=(0, 1),
            **{nested_gate_name: float("nan")},
        )

    assert cuda_calls == 0


def _qt_record_run(
    probabilities: list[float],
    *,
    max_bond: int,
    rng_seed: int,
) -> dict[str, Any]:
    return {
        "max_bond": max_bond,
        "qt_mps_backend_executed": True,
        "carrier_program": {"requires_scalable_backend": False},
        "mps_execution": {
            "measurement_records": [[0], [1]],
            "record_probabilities": probabilities,
            "trajectory_sampling": {"rng_seed": rng_seed},
        },
    }


def test_maximum_probability_gates_keep_inclusive_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from math import inf, nextafter

    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    delta = 0.125
    below_delta = nextafter(delta, -inf)
    runs = [
        _qt_record_run([0.375, 0.625], max_bond=1, rng_seed=0),
        _qt_record_run([0.5, 0.5], max_bond=2, rng_seed=1),
    ]

    bond_equal = qt._bond_sweep_comparison(
        runs,
        convergence_record_probability_gate=delta,
    )
    bond_below = qt._bond_sweep_comparison(
        runs,
        convergence_record_probability_gate=below_delta,
    )
    assert bond_equal["convergence_gate"]["passed"] is True
    assert bond_below["convergence_gate"]["passed"] is False

    seed_equal = qt._trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=delta,
    )
    seed_below = qt._trajectory_seed_sweep_comparison(
        runs,
        seed_record_frequency_spread_gate=below_delta,
    )
    assert seed_equal["seed_spread_gate"]["passed"] is True
    assert seed_below["seed_spread_gate"]["passed"] is False

    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda _schedule, *, device: dense,
    )
    schedule = _one_bit_measurement_schedule()
    dense = _qt_authenticated_dense_record(
        qt,
        schedule,
        probabilities=[0.5, 0.5],
    )
    dense_equal = qt._trajectory_seed_sweep_dense_calibration(
        schedule,
        runs,
        device="cuda",
        dense_record_frequency_gate=delta,
    )
    dense_below = qt._trajectory_seed_sweep_dense_calibration(
        schedule,
        runs,
        device="cuda",
        dense_record_frequency_gate=below_delta,
    )
    assert dense_equal["passed"] is True
    assert dense_below["passed"] is False


@pytest.mark.parametrize(
    "gate_name",
    ["min_peak_allocated_gib", "min_peak_reserved_gib"],
)
def test_minimum_resource_gates_keep_inclusive_boundaries(
    gate_name: str,
) -> None:
    from math import inf, nextafter

    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    equal_kwargs = {
        "min_peak_allocated_gib": 1.0,
        "min_peak_reserved_gib": 1.0,
    }
    equal = qt._resource_probe_policy(
        peak_allocated_bytes=1024**3,
        peak_reserved_bytes=1024**3,
        **equal_kwargs,
    )
    assert equal["gate_passed"] is True

    failing_kwargs = dict(equal_kwargs)
    failing_kwargs[gate_name] = nextafter(1.0, inf)
    above = qt._resource_probe_policy(
        peak_allocated_bytes=1024**3,
        peak_reserved_bytes=1024**3,
        **failing_kwargs,
    )
    assert above["gate_passed"] is False


@pytest.mark.parametrize(
    "invalid_observation",
    [False, True, -1.0, float("nan"), float("inf"), float("-inf")],
)
@pytest.mark.parametrize(
    "field",
    ["discarded_weight_sum", "worst_cut_discarded_weight"],
)
def test_invalid_truncation_observation_fails_without_declared_gate(
    field: str,
    invalid_observation: Any,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    ledger = _ledger(explicit_truncation=True)
    ledger[field] = invalid_observation
    gate = _truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=None,
        total_discarded_weight_gate=None,
    )

    assert gate["evaluated"] is True
    assert gate["passed"] is False
    assert f"invalid_{field}" in gate["violations"]


def test_truncation_gate_rejects_the_next_float_above_the_inclusive_boundary() -> None:
    from math import inf, nextafter

    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    gate = _truncation_gate_result(
        {
            "discarded_weight_ledger_complete": True,
            "discarded_weight_sum": nextafter(0.2, inf),
            "worst_cut_discarded_weight": nextafter(0.1, inf),
        },
        worst_cut_discarded_weight_gate=0.1,
        total_discarded_weight_gate=0.2,
    )

    assert gate["evaluated"] is True
    assert gate["passed"] is False


class _IndexSixtyFour:
    def __index__(self) -> int:
        return 64


def test_record_materialization_budget_accepts_index_integers() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _normalize_max_record_materialization_outcomes,
    )

    assert _normalize_max_record_materialization_outcomes(64) == 64
    assert _normalize_max_record_materialization_outcomes(_IndexSixtyFour()) == 64


def test_qt_record_materialization_preflight_uses_registered_schema() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    preflight = qt._record_materialization_preflight_for_schedule(
        _six_bit_measurement_schedule(),
        max_record_materialization_outcomes=64,
    )

    assert preflight["schema"] == (
        "error_coupling_simulator.frontend."
        "qt_mps_record_materialization_preflight.v2"
    )
    assert preflight["record_support_policy"] == "full_binary_record_support"
    assert preflight["materialized_outcome_count_upper_bound"] == 64
    assert preflight["requires_full_binary_support_materialization"] is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("process_infidelity_gate", 2.0e-6),
        ("gross_gate", 0.11),
        ("record_tv_gate", 2.0e-6),
        ("record_gross_tv_gate", 0.21),
        ("record_sampling_confidence", 0.9999),
    ],
)
def test_mcwf_builder_gate_overrides_may_only_tighten_defaults(
    field: str,
    value: float,
) -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    with pytest.raises(ValueError):
        dense_jointL_record_certification(
            SimpleNamespace(),
            {},
            {"requires_scalable_backend": True},
            **{field: value},
        )


@pytest.mark.parametrize(
    ("oracle_overrides", "error_type"),
    [
        ({"schema": None, "content_hash": "e" * 64}, ValueError),
        (
            {
                "schema": (
                    "error_coupling_simulator.frontend."
                    "measurement_record_evidence.v1"
                ),
                "content_hash": None,
            },
            TypeError,
        ),
    ],
    ids=["missing_schema", "missing_hash"],
)
def test_mcwf_record_certification_requires_registered_oracle_provenance(
    monkeypatch: pytest.MonkeyPatch,
    oracle_overrides: dict[str, Any],
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf
    import error_coupling_simulator.frontend.axis1_record_evidence as record_evidence

    monkeypatch.setattr(
        record_evidence,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: {
            **oracle_overrides,
            "record_evidence": {
                "measurement_records": [[0]],
                "record_probabilities": [1.0],
            },
        },
    )

    with pytest.raises(error_type):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 1,
                },
                "evaluator_only_diagnostics": (
                    _mcwf_evaluator_only_diagnostics()
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "measurement_records": [[0]],
                "record_counts": [1],
                "record_probabilities": [1.0],
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )


def test_qt_dense_record_certification_rejects_boolean_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    schedule = _one_bit_measurement_schedule()
    dense = _qt_authenticated_dense_record(qt, schedule)

    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: dense,
    )

    with pytest.raises(TypeError):
        qt._dense_record_certification(
            schedule,
            program={"requires_scalable_backend": False},
            execution={
                "trajectory_sampling": {"mode": "exact_branch_enumeration"},
                "measurement_keys": ["m0"],
                "measurement_records": [[False]],
                "record_probabilities": [1.0],
            },
            device="cuda",
        )


def test_mcwf_dense_record_certification_rejects_boolean_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf
    import error_coupling_simulator.frontend.axis1_record_evidence as record_evidence

    monkeypatch.setattr(
        record_evidence,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: {
            "schema": (
                "error_coupling_simulator.frontend.measurement_record_evidence.v1"
            ),
            "content_hash": "1" * 64,
            "record_evidence": {
                "measurement_records": [[0]],
                "record_probabilities": [1.0],
            },
        },
    )

    with pytest.raises(TypeError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 1,
                },
                "evaluator_only_diagnostics": (
                    _mcwf_evaluator_only_diagnostics()
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "measurement_records": [[False]],
                "record_counts": [1],
                "record_probabilities": [1.0],
                "local_dims": [2],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[2],
        )


def test_mcwf_dense_level_certification_rejects_float_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: {(0,): 1.0},
    )
    with pytest.raises(TypeError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 1,
                },
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=[[0.9]],
                    level_record_counts=[1],
                    level_record_probabilities=[1.0],
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "local_dims": [3],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[3],
        )


@pytest.mark.parametrize(
    "invalid_budget",
    [
        None,
        False,
        True,
        64.0,
        "64",
        Decimal("64"),
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_record_materialization_budget_rejects_nonintegers(
    invalid_budget: Any,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _normalize_max_record_materialization_outcomes,
    )

    with pytest.raises(TypeError):
        _normalize_max_record_materialization_outcomes(invalid_budget)


@pytest.mark.parametrize("invalid_budget", [0, -1, sys.maxsize + 1])
def test_record_materialization_budget_rejects_out_of_domain_integers(
    invalid_budget: int,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _normalize_max_record_materialization_outcomes,
    )

    with pytest.raises(ValueError):
        _normalize_max_record_materialization_outcomes(invalid_budget)


def test_all_qt_mps_resource_surfaces_declare_the_same_record_budget() -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    for name in (
        "axis1_qt_mps_restricted_execution_manifest",
        "axis1_qt_mps_bond_sweep_manifest",
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        "axis1_qt_mps_resource_probe_manifest",
    ):
        parameter = inspect.signature(getattr(qt, name)).parameters[
            "max_record_materialization_outcomes"
        ]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default == 4096


def _install_qt_no_execution_sentinels(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
) -> dict[str, int]:
    calls = {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}

    def cuda_sentinel(_device: str) -> str:
        calls["cuda"] += 1
        raise _CudaReached

    def records_sentinel(_width: int) -> list[list[int]]:
        calls["records"] += 1
        raise RuntimeError("RECORD_ALLOCATION_SENTINEL")

    def exact_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["exact"] += 1
        raise RuntimeError("EXACT_EXECUTION_SENTINEL")

    def sampled_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["sampled"] += 1
        raise RuntimeError("SAMPLED_EXECUTION_SENTINEL")

    monkeypatch.setattr(qt, "_require_cuda_device", cuda_sentinel)
    monkeypatch.setattr(qt, "_measurement_records", records_sentinel)
    monkeypatch.setattr(qt, "_execute_program", exact_sentinel)
    monkeypatch.setattr(qt, "_execute_sampled_program", sampled_sentinel)
    return calls


@pytest.mark.parametrize("trajectory_count", [None, 64])
def test_record_budget_rejects_exact_and_sampled_before_cuda_or_allocation(
    monkeypatch: pytest.MonkeyPatch,
    trajectory_count: int | None,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    kwargs: dict[str, Any] = {
        "max_record_materialization_outcomes": 63,
        "trajectory_count": trajectory_count,
    }
    if trajectory_count is not None:
        kwargs["rng_seed"] = 0

    with pytest.raises(
        ValueError,
    ):
        qt.axis1_qt_mps_restricted_execution_manifest(
            _six_bit_measurement_schedule(),
            **kwargs,
        )

    assert calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}


def test_record_budget_counts_total_width_across_measurement_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    with pytest.raises(
        ValueError,
    ):
        qt.axis1_qt_mps_restricted_execution_manifest(
            _two_boundary_six_bit_measurement_schedule(),
            max_record_materialization_outcomes=63,
        )

    assert calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}


@pytest.mark.parametrize("budget", [64, 65])
@pytest.mark.parametrize("trajectory_count", [None, 1])
def test_record_budget_equality_and_above_reach_cuda_only_after_preflight(
    monkeypatch: pytest.MonkeyPatch,
    budget: int,
    trajectory_count: int | None,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    kwargs: dict[str, Any] = {
        "max_record_materialization_outcomes": budget,
        "trajectory_count": trajectory_count,
    }
    if trajectory_count is not None:
        kwargs["rng_seed"] = 0

    with pytest.raises(_CudaReached):
        qt.axis1_qt_mps_restricted_execution_manifest(
            _six_bit_measurement_schedule(),
            **kwargs,
        )

    assert calls == {"cuda": 1, "records": 0, "exact": 0, "sampled": 0}


def test_carrier_record_budget_blocks_before_either_cuda_seam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    carrier_cuda_calls = 0

    def carrier_cuda_sentinel(_device: str) -> str:
        nonlocal carrier_cuda_calls
        carrier_cuda_calls += 1
        raise RuntimeError("CARRIER_CUDA_SENTINEL")

    monkeypatch.setattr(carrier, "_require_cuda_device", carrier_cuda_sentinel)
    qt_calls = _install_qt_no_execution_sentinels(monkeypatch, qt)

    with pytest.raises(
        ValueError,
    ):
        carrier.axis1_carrier_execution_manifest(
            _six_bit_measurement_schedule(),
            execution_backend_contract=(
                carrier.AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "max_record_materialization_outcomes": 63,
            },
        )

    assert carrier_cuda_calls == 0
    assert qt_calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}


def test_resource_probe_record_budget_blocks_before_cuda_accounting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    calls = _install_qt_no_execution_sentinels(monkeypatch, qt)
    cuda_accounting_calls = {
        "empty_cache": 0,
        "reset_peak_memory_stats": 0,
        "synchronize": 0,
    }

    def accounting_sentinel(name: str):
        def sentinel(*_args: Any, **_kwargs: Any) -> None:
            cuda_accounting_calls[name] += 1
            raise RuntimeError(f"{name.upper()}_SENTINEL")

        return sentinel

    for name in cuda_accounting_calls:
        monkeypatch.setattr(qt.torch.cuda, name, accounting_sentinel(name))

    with pytest.raises(
        ValueError,
    ):
        qt.axis1_qt_mps_resource_probe_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            trajectory_count=1,
            rng_seeds=(0, 1),
            max_record_materialization_outcomes=63,
        )

    assert calls == {"cuda": 0, "records": 0, "exact": 0, "sampled": 0}
    assert cuda_accounting_calls == {
        "empty_cache": 0,
        "reset_peak_memory_stats": 0,
        "synchronize": 0,
    }


def test_mcwf_exact_level_certification_fails_closed_without_probability_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: {(0,): 1.0},
    )

    certification = mcwf.dense_jointL_record_certification(
        SimpleNamespace(),
        {
            "trajectory_sampling": {
                "mode": "exact_branch_enumeration",
                "rng_seed_was_explicit": False,
                "trajectory_count": 1,
            },
            "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                level_records=[[0]],
                level_record_counts=[1],
            ),
            "measurement_keys": ["m0"],
            "measurement_targets": [0],
            **_mcwf_ordered_measurement_metadata(),
            "local_dims": [3],
        },
        {"requires_scalable_backend": False},
        declared_local_dims=[3],
    )

    assert certification == {
        "executed": False,
        "passed": False,
        "passed_gross": False,
        "reason": "exact_level_probability_payload_not_registered",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def test_mcwf_exact_record_certification_fails_closed_without_probability_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf
    import error_coupling_simulator.frontend.axis1_record_evidence as record_evidence

    def oracle_sentinel(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("exact MCWF record payload reached dense oracle")

    monkeypatch.setattr(
        record_evidence,
        "axis1_measurement_record_evidence_manifest",
        oracle_sentinel,
    )

    certification = mcwf.dense_jointL_record_certification(
        SimpleNamespace(),
        {
            "trajectory_sampling": {
                "mode": "exact_branch_enumeration",
                "rng_seed_was_explicit": False,
                "trajectory_count": 1,
            },
            "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(),
            "measurement_keys": ["m0"],
            "measurement_targets": [0],
            **_mcwf_ordered_measurement_metadata(),
            "measurement_records": [[0]],
            "record_probabilities": [1.0],
            "local_dims": [2],
        },
        {"requires_scalable_backend": False},
        declared_local_dims=[2],
    )

    assert certification == {
        "executed": False,
        "passed": False,
        "passed_gross": False,
        "reason": "exact_record_probability_payload_not_registered",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def test_mcwf_level_support_bound_counts_repeated_measurement_targets() -> None:
    trajectory_count = 4
    support_size = 4
    sampling_halfwidth = 0.5 * support_size * math.sqrt(
        math.log(4.0 * support_size / 0.01) / (2.0 * trajectory_count)
    )
    certification = _mcwf_metric_certification(
        comparison_object=(
            "measurement_basis_level_and_emitted_binary_record_populations"
        ),
        oracle=(
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        readout_model_independent=False,
        sampling_support_size=support_size,
        sampling_finite_shot_halfwidth=sampling_halfwidth,
        trajectory_count=trajectory_count,
        dense_evidence_schema=(
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel:measurement_basis_level_populations.v2"
        ),
        dense_evidence_content_hash=None,
    )

    policy = _mcwf_policy(
        certification=certification,
        trajectory_count=trajectory_count,
        execution_overrides={
            "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                level_records=[[0, 0], [0, 1], [1, 0], [1, 1]],
                level_record_counts=[1, 1, 1, 1],
                level_record_probabilities=[0.25, 0.25, 0.25, 0.25],
            ),
            "measurement_keys": ["m0", "m1"],
            "measurement_targets": [0, 0],
            "local_dims": [3],
        },
    )

    assert policy["accepted_for_restricted_execution"] is True
    assert policy["dense_jointL_record_certification"][
        "sampling_support_size"
    ] == support_size


def test_mcwf_level_certification_rejects_outcome_outside_target_dimension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: {(3,): 1.0},
    )

    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 2,
                },
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=[[3]],
                    level_record_counts=[2],
                    level_record_probabilities=[1.0],
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "local_dims": [3],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[3],
        )


def test_mcwf_level_certification_rejects_oracle_outcome_outside_target_dimension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: {(0,): 0.99, (3,): 0.01},
    )

    with pytest.raises(ValueError):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            {
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories",
                    "rng_seed_was_explicit": True,
                    "trajectory_count": 2,
                },
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=[[0]],
                    level_record_counts=[2],
                    level_record_probabilities=[1.0],
                ),
                "measurement_keys": ["m0"],
                "measurement_targets": [0],
                **_mcwf_ordered_measurement_metadata(),
                "local_dims": [3],
            },
            {"requires_scalable_backend": False},
            declared_local_dims=[3],
        )


@pytest.mark.parametrize(
    ("payload_overrides", "error_type"),
    [
        ({"measurement_targets": [True]}, TypeError),
        ({"measurement_targets": [-1]}, ValueError),
        ({"measurement_targets": [1]}, ValueError),
        ({"local_dims": [True]}, TypeError),
    ],
    ids=["bool_target", "negative_target", "outside_target", "bool_local_dim"],
)
def test_mcwf_level_certification_rejects_invalid_layout_indices(
    monkeypatch: pytest.MonkeyPatch,
    payload_overrides: dict[str, Any],
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    monkeypatch.setattr(
        mcwf,
        "_dense_jointL_level_distribution",
        lambda *_args, **_kwargs: {(0,): 1.0},
    )
    execution = {
        "trajectory_sampling": {
            "mode": "sampled_fixed_microstep_mcwf_trajectories",
            "rng_seed_was_explicit": True,
            "trajectory_count": 2,
        },
        "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
            level_records=[[0]],
            level_record_counts=[2],
            level_record_probabilities=[1.0],
        ),
        "measurement_keys": ["m0"],
        "measurement_targets": [0],
        **_mcwf_ordered_measurement_metadata(),
        "local_dims": [3],
    }
    execution.update(payload_overrides)

    with pytest.raises(error_type):
        mcwf.dense_jointL_record_certification(
            SimpleNamespace(),
            execution,
            {"requires_scalable_backend": False},
            declared_local_dims=[3],
        )


@pytest.mark.parametrize(
    ("invalid_dimension", "error_type"),
    [(-1, ValueError), (0, ValueError), (True, TypeError)],
)
def test_mcwf_policy_rejects_invalid_exact_bond_sufficient_dimension(
    invalid_dimension: Any,
    error_type: type[Exception],
) -> None:
    ledger = _ledger()
    ledger["exact_bond_dimension_sufficient"] = invalid_dimension

    with pytest.raises(error_type):
        _mcwf_policy(ledger=ledger)


def test_mcwf_channel_policy_accepts_canonical_no_measurement_sentinel() -> None:
    policy = _mcwf_policy(
        certification=_mcwf_channel_certification(),
        execution_overrides={
            "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(),
            "measurement_keys": [],
            "measurement_targets": [],
            "measurement_records": [[]],
            "record_counts": [2],
            "record_probabilities": [1.0],
        },
    )

    assert policy["accepted_for_restricted_execution"] is True
    assert policy["dense_jointL_record_certification"]["comparison_object"] == (
        "within_substep_window_channel"
    )


@pytest.mark.parametrize(
    ("execution_overrides", "error_type"),
    [
        ({"measurement_records": []}, ValueError),
        ({"measurement_records": [[0]]}, ValueError),
        ({"record_counts": [1]}, ValueError),
        ({"record_counts": [True]}, TypeError),
        ({"record_probabilities": [0.5]}, ValueError),
        ({"measurement_targets": [0]}, ValueError),
        (
            {
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_record_counts=[2]
                )
            },
            ValueError,
        ),
        (
            {
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_record_probabilities=[1.0]
                )
            },
            ValueError,
        ),
        (
            {
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_records=""
                )
            },
            TypeError,
        ),
        (
            {
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_record_counts=""
                )
            },
            TypeError,
        ),
        (
            {
                "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                    level_record_probabilities={}
                )
            },
            TypeError,
        ),
    ],
    ids=[
        "missing_record_sentinel",
        "nonempty_record_sentinel",
        "wrong_count",
        "boolean_count",
        "wrong_probability",
        "target_residue",
        "level_count_residue",
        "level_probability_residue",
        "level_records_wrong_empty_type",
        "level_counts_wrong_empty_type",
        "level_probabilities_wrong_empty_type",
    ],
)
def test_mcwf_channel_policy_rejects_noncanonical_no_measurement_residue(
    execution_overrides: dict[str, Any],
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.certify.axis1_mps as mcwf

    execution = {
        "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(),
        "measurement_keys": [],
        "measurement_targets": [],
        **_mcwf_ordered_measurement_metadata(()),
        "measurement_records": [[]],
        "record_counts": [2],
        "record_probabilities": [1.0],
        "local_dims": [2],
    }
    execution.update(execution_overrides)

    with pytest.raises(error_type):
        mcwf._validate_metric_family_execution_payload(
            execution,
            sampled=True,
            trajectory_count=2,
            declared_local_dims=[2],
            program={"requires_scalable_backend": False},
        )


def _run_direct_qt_with_policy(
    monkeypatch: pytest.MonkeyPatch,
    policy: dict[str, Any],
    *,
    trajectory_count: int | None = None,
) -> dict[str, Any]:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    sampled = trajectory_count is not None
    mode = (
        "sampled_product_channel_trajectories"
        if sampled
        else "exact_branch_enumeration"
    )
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    execution = {
        "trajectory_sampling": {
            "mode": mode,
            "trajectory_count": trajectory_count,
        },
        "mps_truncation_ledger": {
            "discarded_weight_ledger_complete": True,
            "aggregation": {"context_complete": True},
        },
    }
    execute_name = "_execute_sampled_program" if sampled else "_execute_program"
    monkeypatch.setattr(
        qt,
        execute_name,
        lambda *_args, **_kwargs: execution,
    )
    monkeypatch.setattr(
        qt,
        "_dense_record_certification",
        lambda *_args, **_kwargs: {"fixture": "certification"},
    )
    monkeypatch.setattr(
        qt,
        "_restricted_acceptance_policy",
        lambda **_kwargs: policy,
    )

    return qt.axis1_qt_mps_restricted_execution_manifest(
        _six_bit_measurement_schedule(),
        trajectory_count=trajectory_count,
        rng_seed=11 if sampled else None,
    )


def _accepted_qt_direct_policy(*, sampled: bool = False) -> dict[str, Any]:
    return {
        "schema": (
            "error_coupling_simulator.frontend."
            "qt_mps_restricted_acceptance_policy.v2"
        ),
        "policy_role": "restricted_execution_acceptance_not_metric",
        "execution_status": "completed",
        "certification_status": "accepted",
        "diagnostic_only": False,
        "blocked_reason": None,
        "accepted_for_restricted_execution": True,
        "accepted_for_exact_dense_probability_evidence": not sampled,
        "accepted_for_sampled_execution_evidence": sampled,
        "accepted_for_production_scalable_backend": False,
        "trajectory": {
            "mode": (
                "sampled_product_channel_trajectories"
                if sampled
                else "exact_branch_enumeration"
            ),
        },
    }


def test_direct_qt_completed_payload_binds_backend_execution_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _run_direct_qt_with_policy(
        monkeypatch,
        _accepted_qt_direct_policy(),
    )
    assert manifest["qt_mps_backend_executed"] is True
    assert manifest["claims_qt_mps_backend_execution"] is True
    assert (
        manifest["claims_qt_mps_backend_execution"]
        is manifest["qt_mps_backend_executed"]
    )


def test_direct_qt_manifest_rejects_unregistered_policy_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _accepted_qt_direct_policy()
    policy["schema"] = "corrupted.qt.policy.v2"

    with pytest.raises(ValueError):
        _run_direct_qt_with_policy(monkeypatch, policy)


def test_direct_qt_manifest_rejects_unregistered_policy_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _accepted_qt_direct_policy()
    policy["policy_role"] = "corrupted_policy_role"

    with pytest.raises(ValueError):
        _run_direct_qt_with_policy(monkeypatch, policy)


def test_direct_qt_manifest_requires_completed_policy_execution_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _accepted_qt_direct_policy()
    policy["execution_status"] = "blocked"

    with pytest.raises(ValueError):
        _run_direct_qt_with_policy(monkeypatch, policy)


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("certification_status", "rejected"),
        ("diagnostic_only", True),
        ("blocked_reason", "forged_blocker"),
    ],
)
def test_direct_qt_manifest_rejects_inconsistent_accepted_policy_state(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: Any,
) -> None:
    policy = _accepted_qt_direct_policy()
    policy[field] = corrupted_value

    with pytest.raises(ValueError):
        _run_direct_qt_with_policy(monkeypatch, policy)


def test_direct_qt_manifest_forbids_production_policy_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _accepted_qt_direct_policy()
    policy["accepted_for_production_scalable_backend"] = True

    with pytest.raises(ValueError):
        _run_direct_qt_with_policy(monkeypatch, policy)


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("accepted_for_exact_dense_probability_evidence", False),
        ("accepted_for_sampled_execution_evidence", True),
        ("trajectory_mode", "sampled_product_channel_trajectories"),
    ],
)
def test_direct_qt_exact_execution_binds_exact_acceptance_tier(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: Any,
) -> None:
    policy = _accepted_qt_direct_policy()
    if field == "trajectory_mode":
        policy["trajectory"]["mode"] = corrupted_value
    else:
        policy[field] = corrupted_value

    with pytest.raises(ValueError):
        _run_direct_qt_with_policy(monkeypatch, policy)


def _qt_restricted_child_fixture(
    *,
    max_bond: int | None,
    sampled: bool,
    schedule: Any | None = None,
    trajectory_count: int = 2,
    rng_seed: int = 7,
) -> dict[str, Any]:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    if schedule is None:
        schedule = _six_bit_measurement_schedule()
    layout = qt.axis1_record_layout_from_schedule(schedule)
    program = qt.axis1_carrier_program_manifest(
        schedule,
        backend_contract=qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    trajectory_count = trajectory_count if sampled else None
    rng_seed = rng_seed if sampled else None
    mode = (
        "sampled_product_channel_trajectories"
        if sampled
        else "exact_branch_enumeration"
    )
    records = (
        [[0] * layout.measurement_width]
        if sampled
        else [
            list(record)
            for record in qt.materialize_binary_records(
                layout.measurement_width
            )
        ]
    )
    probabilities = [1.0] + [0.0] * (len(records) - 1)
    projected = qt.project_axis1_xor_records(layout, records)
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
            microstep_count=1,
            finite_step_order="first_order",
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
                    microstep_count=1,
                    max_branches=4096,
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
                    "finite_step_policy": "operator_family_product_formula_v1",
                    "finite_step_order": "first_order",
                    "microstep_count": 1,
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
                "finite_step_policy": "operator_family_product_formula_v1",
                "finite_step_order": "first_order",
                "microstep_count": 1,
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
            "name": "operator_family_product_formula_v1",
            "order": "first_order",
            "microstep_count": 1,
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
        "measurement_keys": list(layout.measurement_keys),
        "measurement_targets": list(layout.measurement_targets),
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
    if sampled:
        execution["record_counts"] = [trajectory_count]
    preflight = qt._record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=4096,
        trajectory_count=trajectory_count,
    )
    certification = qt._dense_record_certification(
        schedule,
        program=program,
        execution=execution,
        device="cuda",
    )
    policy = qt._restricted_acceptance_policy(
        program=program,
        execution=execution,
        record_materialization_preflight=preflight,
        certification=certification,
        finite_step_order="first_order",
        finite_step_policy="operator_family_product_formula_v1",
        max_bond=max_bond,
        worst_cut_discarded_weight_gate=None,
        total_discarded_weight_gate=None,
    )
    payload = {
        "schema": qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY,
        "backend_contract": qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": "cuda",
        "carrier_program": qt._program_summary(program),
        "max_bond": max_bond,
        "max_branches": 4096,
        "max_record_materialization_outcomes": 4096,
        "record_materialization_preflight": preflight,
        "microstep_count": 1,
        "finite_step_order": "first_order",
        "trajectory_count": trajectory_count,
        "rng_seed": rng_seed,
        "worst_cut_discarded_weight_gate": None,
        "total_discarded_weight_gate": None,
        "dense_oracle_certification_requested": True,
        "verdict": (
            "pass" if policy["accepted_for_restricted_execution"] else "fail"
        ),
        "passed": policy["accepted_for_restricted_execution"],
        "execution_status": "completed",
        "certification_status": policy["certification_status"],
        "diagnostic_only": policy["diagnostic_only"],
        "blocked_reason": policy["blocked_reason"],
        "blocked_substeps": [],
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
            microstep_count=1,
            finite_step_order="first_order",
            trajectory_count=trajectory_count,
            rng_seed=rng_seed,
            worst_cut_discarded_weight_gate=None,
            total_discarded_weight_gate=None,
            execution=execution,
        ),
        "epistemic_classes": qt._qt_restricted_epistemic_classes(),
        "mps_execution": execution,
        "dense_jointL_record_certification": certification,
        "restricted_acceptance_policy": policy,
        "scope": qt._QT_MPS_COMPLETED_SCOPE,
    }
    payload["content_hash"] = qt._stable_payload_hash(payload)
    return payload


def _reject_qt_child_with_dense_record_disagreement(
    qt: Any,
    schedule: Any,
    child: dict[str, Any],
) -> dict[str, Any]:
    execution = child["mps_execution"]
    probabilities = list(execution["record_probabilities"])
    if len(probabilities) < 2:
        raise ValueError("dense disagreement fixture requires two Record outcomes")
    probabilities[0] = 0.9
    probabilities[1] = 0.1
    execution["record_probabilities"] = probabilities
    program = qt.axis1_carrier_program_manifest(
        schedule,
        backend_contract=qt.AXIS1_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    certification = qt._dense_record_certification(
        schedule,
        program=program,
        execution=execution,
        device=child["device"],
    )
    policy = qt._restricted_acceptance_policy(
        program=program,
        execution=execution,
        record_materialization_preflight=child[
            "record_materialization_preflight"
        ],
        certification=certification,
        finite_step_order=child["finite_step_order"],
        finite_step_policy=qt._finite_step_policy_name(
            child["finite_step_order"]
        ),
        max_bond=child["max_bond"],
        worst_cut_discarded_weight_gate=child[
            "worst_cut_discarded_weight_gate"
        ],
        total_discarded_weight_gate=child["total_discarded_weight_gate"],
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
    child["content_hash"] = qt._stable_payload_hash(child)
    return child


def _qt_canonical_aggregate_children(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
    schedule: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    dense = _qt_authenticated_dense_record(qt, schedule)
    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: dense,
    )

    def direct_child(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        sampled = kwargs["trajectory_count"] is not None
        return _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=sampled,
            schedule=schedule_arg,
            trajectory_count=kwargs["trajectory_count"],
            rng_seed=kwargs["rng_seed"],
        )

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        direct_child,
    )
    bond = qt.axis1_qt_mps_bond_sweep_manifest(
        schedule,
        bond_values=(1, 2),
        convergence_record_probability_gate=0.0,
    )
    trajectory = qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
        schedule,
        trajectory_count=2,
        rng_seeds=(3, 5),
        max_bond=2,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )
    return bond, trajectory


def _qt_canonical_bundle_fixture(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
    schedule: Any,
) -> dict[str, Any]:
    dense = _qt_authenticated_dense_record(qt, schedule)
    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: dense,
    )

    def direct_child(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        sampled = kwargs["trajectory_count"] is not None
        return _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=sampled,
            schedule=schedule_arg,
            trajectory_count=kwargs["trajectory_count"],
            rng_seed=kwargs["rng_seed"],
        )

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        direct_child,
    )
    return qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
        schedule,
        bond_values=(1, 2),
        trajectory_count=2,
        rng_seeds=(3, 5),
        convergence_record_probability_gate=0.0,
        seed_record_frequency_spread_gate=0.0,
        dense_record_frequency_gate=0.0,
    )


def test_qt_bond_sweep_rejects_unregistered_execution_child_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def run(_schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
        )
        child["schema"] = "corrupted.qt.execution.v2"
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    calls = _install_qt_bond_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


def test_qt_bond_sweep_rejects_unregistered_child_policy_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def run(_schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
        )
        child["restricted_acceptance_policy"]["schema"] = (
            "corrupted.qt.policy.v2"
        )
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    calls = _install_qt_bond_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


def test_qt_bond_sweep_rejects_unregistered_child_policy_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def run(_schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
        )
        child["restricted_acceptance_policy"]["policy_role"] = "corrupted_role"
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    calls = _install_qt_bond_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


def test_qt_bond_sweep_binds_child_and_policy_blocked_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def run(_schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
        )
        child["blocked_reason"] = "forged_child_blocker"
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    calls = _install_qt_bond_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


def test_qt_bond_sweep_forbids_child_production_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def run(_schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
        )
        child["restricted_acceptance_policy"][
            "accepted_for_production_scalable_backend"
        ] = True
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    calls = _install_qt_bond_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            _six_bit_measurement_schedule(),
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("accepted_for_exact_dense_probability_evidence", False),
        ("accepted_for_sampled_execution_evidence", True),
        ("policy_mode", "sampled_product_channel_trajectories"),
        ("execution_mode", "sampled_product_channel_trajectories"),
    ],
)
def test_qt_bond_sweep_requires_exact_child_tier(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _one_bit_measurement_schedule()
    dense = _qt_authenticated_dense_record(qt, schedule)
    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        lambda *_args, **_kwargs: dense,
    )

    def run(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=False,
            schedule=schedule_arg,
        )
        if field == "policy_mode":
            child["restricted_acceptance_policy"]["trajectory"]["mode"] = (
                corrupted_value
            )
        elif field == "execution_mode":
            child["mps_execution"]["trajectory_sampling"]["mode"] = (
                corrupted_value
            )
        else:
            child["restricted_acceptance_policy"][field] = corrupted_value
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    calls = _install_qt_bond_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_bond_sweep_manifest(
            schedule,
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


@pytest.mark.parametrize(
    ("field", "corrupted_value"),
    [
        ("accepted_for_sampled_execution_evidence", False),
        ("accepted_for_exact_dense_probability_evidence", True),
        ("policy_mode", "exact_branch_enumeration"),
        ("execution_mode", "exact_branch_enumeration"),
    ],
)
def test_qt_seed_sweep_requires_sampled_child_tier(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    corrupted_value: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def run(_schedule: Any, **kwargs: Any) -> dict[str, Any]:
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=True,
            schedule=_schedule,
            trajectory_count=kwargs["trajectory_count"],
            rng_seed=kwargs["rng_seed"],
        )
        if field == "policy_mode":
            child["restricted_acceptance_policy"]["trajectory"]["mode"] = (
                corrupted_value
            )
        elif field == "execution_mode":
            child["mps_execution"]["trajectory_sampling"]["mode"] = (
                corrupted_value
            )
        else:
            child["restricted_acceptance_policy"][field] = corrupted_value
        child["content_hash"] = qt._stable_payload_hash(child)
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    calls = _install_qt_seed_must_not_run_counters(monkeypatch, qt)

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
            _six_bit_measurement_schedule(),
            trajectory_count=2,
            rng_seeds=(3, 5),
            seed_record_frequency_spread_gate=0.0,
        )

    assert calls == {"comparison": 0, "calibration": 0}


def test_qt_blocked_child_reaches_carrier_as_structured_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_carrier_execution as carrier
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="mx", basis="X")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")

    child = qt.axis1_qt_mps_restricted_execution_manifest(schedule)
    assert child["qt_mps_backend_executed"] is False
    assert child["claims_qt_mps_backend_execution"] is False
    assert (
        child["claims_qt_mps_backend_execution"]
        is child["qt_mps_backend_executed"]
    )
    certification = child["dense_jointL_record_certification"]
    assert certification == {
        "executed": False,
        "reason": "qt_mps_backend_blocked_before_dense_record_certification",
        "blocked_reason": child["blocked_reason"],
        "comparison_outcome_is_metric": False,
    }

    manifest = carrier.axis1_carrier_execution_manifest(
        schedule,
        execution_backend_contract=(
            carrier.AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
    )

    assert manifest["verdict"] == "fail"
    assert manifest["passed"] is False
    assert manifest["execution_status"] == "blocked"
    assert manifest["certification_status"] == "not_evaluated"
    assert manifest["qt_mps_backend_executed"] is False
    assert manifest["claims_qt_mps_backend_execution"] is False
    assert (
        manifest["claims_qt_mps_backend_execution"]
        is manifest["qt_mps_backend_executed"]
    )
    assert manifest["dense_probe_executed"] is False
    assert manifest["blocked_reason"] == child["blocked_reason"]


def test_qt_evidence_bundle_pins_aggregate_child_schemas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule = _six_bit_measurement_schedule()
    bond, trajectory = _qt_canonical_aggregate_children(
        monkeypatch,
        qt,
        schedule,
    )
    bond["schema"] = "corrupted.qt_bond_sweep.v2"
    bond["content_hash"] = qt._stable_payload_hash(bond)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_bond_sweep_manifest",
        lambda *_args, **_kwargs: bond,
    )
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        lambda *_args, **_kwargs: trajectory,
    )
    acceptance_calls = {"bond": 0, "seed": 0}

    def bond_acceptance_sentinel(*_args: Any, **_kwargs: Any) -> None:
        acceptance_calls["bond"] += 1
        raise AssertionError("bond acceptance must not run for an invalid schema")

    def seed_acceptance_sentinel(*_args: Any, **_kwargs: Any) -> None:
        acceptance_calls["seed"] += 1
        raise AssertionError("seed acceptance must not run for an invalid schema")

    monkeypatch.setattr(
        qt,
        "_validate_qt_bond_sweep_acceptance",
        bond_acceptance_sentinel,
    )
    monkeypatch.setattr(
        qt,
        "_validate_qt_seed_sweep_acceptance",
        seed_acceptance_sentinel,
    )

    with pytest.raises(ValueError):
        qt.axis1_qt_mps_restricted_evidence_bundle_manifest(
            schedule,
            bond_values=(1, 2),
            trajectory_count=2,
            rng_seeds=(3, 5),
        )

    assert acceptance_calls == {"bond": 0, "seed": 0}


def _install_qt_seed_sweep_gate_fixture(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
    *,
    seed_spread_gate: Any,
) -> None:
    def run(schedule: Any, **kwargs: Any) -> dict[str, Any]:
        seed = kwargs["rng_seed"]
        trajectory_count = kwargs["trajectory_count"]
        child = _qt_restricted_child_fixture(
            max_bond=kwargs["max_bond"],
            sampled=True,
            schedule=schedule,
            trajectory_count=trajectory_count,
            rng_seed=seed,
        )
        return child

    monkeypatch.setattr(qt, "axis1_qt_mps_restricted_execution_manifest", run)
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_comparison",
        lambda *_args, **_kwargs: {"seed_spread_gate": seed_spread_gate},
    )
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_dense_calibration",
        lambda *_args, **_kwargs: {
            "accepted_as_dense_calibrated_trajectory_evidence": True,
        },
    )


def test_qt_seed_sweep_requires_mapping_seed_spread_gate_before_child_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    _install_qt_seed_sweep_gate_fixture(
        monkeypatch,
        qt,
        seed_spread_gate=_MappingLikeNonDict(),
    )

    with pytest.raises(TypeError):
        qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
            _six_bit_measurement_schedule(),
            trajectory_count=2,
            rng_seeds=(3, 5),
        )


@pytest.mark.parametrize("passed", [None, True], ids=["none", "true"])
def test_qt_seed_sweep_unevaluated_gate_cannot_accept_regardless_of_passed_field(
    monkeypatch: pytest.MonkeyPatch,
    passed: bool | None,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    _install_qt_seed_sweep_gate_fixture(
        monkeypatch,
        qt,
        seed_spread_gate={"evaluated": False, "passed": passed},
    )

    manifest = qt.axis1_qt_mps_trajectory_seed_sweep_manifest(
        _six_bit_measurement_schedule(),
        trajectory_count=2,
        rng_seeds=(3, 5),
    )

    assert manifest["seed_sweep_policy"][
        "accepted_as_restricted_seed_sweep_evidence"
    ] is False
    assert manifest["passed"] is False
    assert manifest["verdict"] == "fail"


@pytest.mark.parametrize(
    "gate_overrides",
    [
        pytest.param(
            {"process_infidelity_gate": 1.0e-6, "gross_gate": 0.0},
            id="process_before_gross",
        ),
        pytest.param(
            {"record_tv_gate": 1.0e-6, "record_gross_tv_gate": 0.0},
            id="record_before_gross",
        ),
    ],
)
def test_mcwf_dense_builder_rejects_inverted_gate_order_before_route(
    gate_overrides: dict[str, float],
) -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    with pytest.raises(ValueError):
        dense_jointL_record_certification(
            SimpleNamespace(),
            {},
            {"requires_scalable_backend": True},
            **gate_overrides,
        )


def test_mcwf_dense_builder_requires_mapping_trajectory_sampling_before_cuda() -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    with pytest.raises(TypeError):
        dense_jointL_record_certification(
            SimpleNamespace(),
            {"trajectory_sampling": _MappingLikeNonDict()},
            {"requires_scalable_backend": False},
        )


def test_mcwf_dense_builder_rejects_unseeded_sampled_record_before_oracle() -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    certification = dense_jointL_record_certification(
        SimpleNamespace(),
        {
            "trajectory_sampling": {
                "mode": "sampled_fixed_microstep_mcwf_trajectories",
                "rng_seed_was_explicit": False,
                "trajectory_count": 1,
            },
            "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(),
            "measurement_keys": ["m0"],
            "measurement_targets": [0],
            **_mcwf_ordered_measurement_metadata(),
            "local_dims": [2],
        },
        {"requires_scalable_backend": False},
        declared_local_dims=[2],
    )

    assert certification == {
        "executed": False,
        "passed": False,
        "passed_gross": False,
        "reason": "sampled_record_rng_seed_not_explicit",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


@pytest.mark.parametrize(
    ("policy_kwargs", "error_type"),
    [
        (
            {"mass_residual_budget": True},
            TypeError,
        ),
        (
            {"mass_residual_budget": "0.1"},
            TypeError,
        ),
        (
            {"mass_residual_budget": math.inf},
            ValueError,
        ),
        (
            {"mass_residual_budget": -0.1},
            ValueError,
        ),
        (
            {
                "execution_overrides": {
                    "trajectory_sampling": _MappingLikeNonDict()
                }
            },
            TypeError,
        ),
        (
            {
                "execution_overrides": {
                    "trajectory_sampling": {
                        "mode": "sampled_fixed_microstep_mcwf_trajectories",
                        "trajectory_count": 1,
                    }
                }
            },
            ValueError,
        ),
    ],
    ids=[
        "budget_bool",
        "budget_string",
        "budget_infinite",
        "budget_negative",
        "sampling_nonmapping",
        "sampling_count_mismatch",
    ],
)
def test_mcwf_policy_rejects_corrupted_controls_before_certification(
    policy_kwargs: dict[str, Any],
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        _mcwf_policy(**policy_kwargs)


@pytest.mark.parametrize(
    "case",
    [
        "nonexecuted_passing",
        "metric_not_executed",
        "unknown_comparison_object",
        "wrong_oracle",
        "metric_family_execution_mismatch",
    ],
)
def test_mcwf_policy_rejects_corrupted_metric_identity(
    case: str,
) -> None:
    if case == "nonexecuted_passing":
        certification = _mcwf_metric_certification(
            executed=False,
            passed=True,
            passed_gross=False,
            comparison_outcome_is_metric=False,
        )
    elif case == "metric_not_executed":
        certification = _mcwf_metric_certification(
            executed=False,
            passed=False,
            passed_gross=False,
        )
    elif case == "unknown_comparison_object":
        certification = _mcwf_metric_certification(
            comparison_object="forged_comparison_object",
            metric_convention="forged_convention",
        )
    elif case == "wrong_oracle":
        certification = _mcwf_metric_certification(oracle="forged.oracle")
    else:
        certification = _mcwf_channel_certification()

    with pytest.raises(ValueError):
        _mcwf_policy(certification=certification)


@pytest.mark.parametrize(
    "certification_overrides",
    [
        pytest.param(
            {"gate": 2.0e-6, "effective_gate_including_sampling_ci": 2.0e-6},
            id="strict_gate_loosened",
        ),
        pytest.param(
            {"gross_gate": 0.21},
            id="gross_gate_loosened",
        ),
        pytest.param(
            {"effective_gate_including_sampling_ci": None},
            id="missing_effective_strict",
        ),
        pytest.param(
            {"gross_effective_gate_including_sampling_ci": None},
            id="missing_effective_gross",
        ),
        pytest.param(
            {"gross_gate_ceiling": None},
            id="missing_gross_ceiling",
        ),
        pytest.param(
            {"sampling_finite_shot_halfwidth": None},
            id="missing_sampling_halfwidth",
        ),
        pytest.param(
            {"sampling_support_size": None},
            id="missing_sampling_support",
        ),
        pytest.param(
            {"sampling_ci_method": "forged_sampling_method"},
            id="wrong_sampling_method",
        ),
        pytest.param(
            {"sampling_confidence": None},
            id="missing_sampling_confidence",
        ),
        pytest.param(
            {
                "sampling_confidence": 0.9995,
                "sampling_finite_shot_halfwidth": (
                    0.5 * math.sqrt(math.log(4000.0) / 4.0)
                ),
            },
            id="loosened_sampling_confidence",
        ),
        pytest.param(
            {
                "trajectory_count": 3,
                "sampling_finite_shot_halfwidth": (
                    0.5 * math.sqrt(math.log(200.0) / 6.0)
                ),
            },
            id="certification_count_mismatch",
        ),
        pytest.param(
            {
                "gross_gate_ceiling": 0.44,
                "gross_effective_gate_including_sampling_ci": 0.44,
            },
            id="wrong_gross_ceiling",
        ),
        pytest.param(
            {
                "sampling_support_size": 2,
                "sampling_finite_shot_halfwidth": (
                    math.sqrt(math.log(200.0) / 4.0)
                ),
            },
            id="support_mismatch",
        ),
        pytest.param(
            {
                "sampling_finite_shot_halfwidth": (
                    0.5 * math.sqrt(math.log(200.0) / 4.0) + 0.01
                )
            },
            id="halfwidth_mismatch",
        ),
        pytest.param(
            {"dense_evidence_schema": "forged.schema"},
            id="wrong_dense_schema",
        ),
        pytest.param(
            {"dense_evidence_content_hash": None},
            id="missing_dense_hash",
        ),
    ],
)
def test_mcwf_policy_rejects_corrupted_record_metric_budget(
    certification_overrides: dict[str, Any],
) -> None:
    certification = _mcwf_metric_certification(**certification_overrides)

    with pytest.raises(ValueError):
        _mcwf_policy(certification=certification)


def _canonical_mcwf_channel_execution() -> dict[str, Any]:
    return {
        "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(),
        "measurement_keys": [],
        "measurement_targets": [],
        "measurement_records": [[]],
        "record_counts": [2],
        "record_probabilities": [1.0],
    }


@pytest.mark.parametrize(
    "certification_overrides",
    [
        pytest.param(
            {"gate": 2.0e-6},
            id="strict_gate_loosened",
        ),
        pytest.param(
            {"gross_gate": 0.11},
            id="gross_gate_loosened",
        ),
        pytest.param(
            {"sampling_support_size": 1},
            id="record_override_present",
        ),
        pytest.param(
            {"gross_gate": 0.0},
            id="gross_below_strict",
        ),
    ],
)
def test_mcwf_policy_rejects_corrupted_channel_metric_budget(
    certification_overrides: dict[str, Any],
) -> None:
    certification = _mcwf_channel_certification(**certification_overrides)

    with pytest.raises(ValueError):
        _mcwf_policy(
            certification=certification,
            execution_overrides=_canonical_mcwf_channel_execution(),
        )


def _mcwf_level_policy_fixture(
    **certification_overrides: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    certification = _mcwf_metric_certification(
        comparison_object=(
            "measurement_basis_level_and_emitted_binary_record_populations"
        ),
        oracle=(
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        readout_model_independent=False,
        dense_evidence_schema=(
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel:measurement_basis_level_populations.v2"
        ),
        dense_evidence_content_hash=None,
    )
    certification.update(certification_overrides)
    execution = {
        "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
            level_records=[[0]],
            level_record_counts=[2],
            level_record_probabilities=[1.0],
        ),
        "measurement_keys": ["m0"],
        "measurement_targets": [0],
        "local_dims": [3],
    }
    return certification, execution


@pytest.mark.parametrize(
    "certification_overrides",
    [
        pytest.param(
            {"readout_model_independent": True},
            id="joint_falsely_claims_readout_independence",
        ),
        pytest.param(
            {"dense_evidence_schema": "forged.level.schema"},
            id="wrong_level_schema",
        ),
    ],
)
def test_mcwf_policy_rejects_corrupted_level_metric_identity(
    certification_overrides: dict[str, Any],
) -> None:
    certification, execution = _mcwf_level_policy_fixture(
        **certification_overrides
    )

    with pytest.raises(ValueError):
        _mcwf_policy(
            certification=certification,
            execution_overrides=execution,
        )


def test_mcwf_policy_requires_unbounded_ledger_to_claim_exact_representation() -> None:
    ledger = _ledger()
    ledger["accepted_as_exact_bond_representation"] = False

    with pytest.raises(
        ValueError,
    ):
        _mcwf_policy(ledger=ledger)


def test_mcwf_policy_rejects_zero_truncating_ops_with_nonzero_total_loss() -> None:
    ledger = _ledger(explicit_truncation=True)
    ledger["discarded_weight_sum"] = 0.1

    with pytest.raises(
        ValueError,
    ):
        _mcwf_policy(ledger=ledger)


def test_mcwf_policy_rejects_positive_worst_cut_without_truncating_op() -> None:
    ledger = _ledger(explicit_truncation=True)
    ledger["discarded_weight_sum"] = None
    ledger["worst_cut_discarded_weight"] = 0.1

    with pytest.raises(
        ValueError,
    ):
        _mcwf_policy(ledger=ledger)


def test_mcwf_policy_rejects_incomplete_one_sided_finite_bond_gate() -> None:
    ledger = _ledger(explicit_truncation=True)
    ledger.update(
        {
            "discarded_weight_sum": 0.1,
            "worst_cut_discarded_weight": 0.05,
            "n_truncating_ops": 1,
        }
    )

    policy = _mcwf_policy(
        ledger=ledger,
        worst_cut_discarded_weight_gate=0.1,
    )

    assert policy["accepted_for_restricted_execution"] is False
    assert "finite_bond_candidate_gate_incomplete" in policy["production_blockers"]


def test_mcwf_policy_surfaces_valid_normalization_residual_above_gate() -> None:
    policy = _mcwf_policy(normalization_residual=1.0e-6)

    assert policy["accepted_for_restricted_execution"] is False
    assert policy["blocked_reason"] == "normalization_invariant_exceeds_gate"


def test_mcwf_dense_builder_returns_overcap_reason_before_sampling_payload() -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    certification = dense_jointL_record_certification(
        SimpleNamespace(),
        {},
        {"requires_scalable_backend": True},
    )

    assert certification == {
        "executed": False,
        "passed": False,
        "passed_gross": False,
        "reason": "schedule_contains_scalable_required_rows",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def test_mcwf_dense_builder_rejects_unseeded_sampled_level_before_oracle() -> None:
    from error_coupling_simulator.certify.axis1_mps import (
        dense_jointL_record_certification,
    )

    certification = dense_jointL_record_certification(
        SimpleNamespace(),
        {
            "trajectory_sampling": {
                "mode": "sampled_fixed_microstep_mcwf_trajectories",
                "rng_seed_was_explicit": False,
                "trajectory_count": 1,
            },
            "evaluator_only_diagnostics": _mcwf_evaluator_only_diagnostics(
                level_records=[[0]],
            ),
            "measurement_keys": ["m0"],
            "measurement_targets": [0],
            **_mcwf_ordered_measurement_metadata(),
            "local_dims": [3],
        },
        {"requires_scalable_backend": False},
        declared_local_dims=[3],
    )

    assert certification == {
        "executed": False,
        "passed": False,
        "passed_gross": False,
        "reason": "sampled_level_record_rng_seed_not_explicit",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }


def test_mcwf_policy_acceptance_status_branches_remain_fail_closed() -> None:
    no_budget = _mcwf_policy(mass_residual_budget=None)
    assert no_budget["certification_status"] == "not_evaluated"
    assert "mass_residual_budget_not_declared_diagnostic_only" in no_budget[
        "production_blockers"
    ]

    excessive_runtime_residual = _mcwf_policy(runtime_mass_residual=0.2)
    assert excessive_runtime_residual["certification_status"] == "rejected"
    assert "runtime_probability_mass_residual_exceeds_budget" in (
        excessive_runtime_residual["production_blockers"]
    )

    unseeded = _mcwf_policy(rng_seed=None)
    assert "sampled_trajectory_rng_seed_not_explicit" in unseeded[
        "production_blockers"
    ]

    nonmetric = _mcwf_policy(
        certification={
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "comparison_outcome_is_metric": False,
            "reason": "fixture_oracle_unavailable",
        }
    )
    assert nonmetric["certification_status"] == "unavailable"
    assert nonmetric["dense_jointL_record_certification"]["metric"] is None

    gross_failed = _mcwf_policy(
        certification=_mcwf_metric_certification(
            value=0.5,
            passed=False,
            passed_gross=False,
        )
    )
    assert gross_failed["certification_status"] == "rejected"
    assert gross_failed["diagnostic_only"] is False


def test_mcwf_policy_truncation_blocker_branches_remain_fail_closed() -> None:
    incomplete = _ledger(explicit_truncation=True)
    incomplete["discarded_weight_ledger_complete"] = False
    incomplete_policy = _mcwf_policy(ledger=incomplete)
    assert "incomplete_mps_truncation_aggregation_context" in incomplete_policy[
        "production_blockers"
    ]
    assert "finite_bond_candidate_gate_failed" in incomplete_policy[
        "production_blockers"
    ]

    unevaluated = _ledger(explicit_truncation=True)
    unevaluated["n_truncating_ops"] = 1
    unevaluated_policy = _mcwf_policy(ledger=unevaluated)
    assert "finite_bond_candidate_gate_not_evaluated" in unevaluated_policy[
        "production_blockers"
    ]

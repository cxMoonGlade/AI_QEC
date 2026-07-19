from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any

import pytest

import error_coupling_simulator.certify.axis1_mps as CERTIFICATION


_DIAGNOSTICS_SCHEMA = (
    "error_coupling_simulator.frontend."
    "mcwf_mps_evaluator_only_diagnostics.v1"
)
_DIAGNOSTICS_VISIBILITY = (
    "evaluator_only_not_emitted_record_or_downstream_estimator_input"
)


class _FalsyCanonicalLocalDims(list[int]):
    def __init__(self) -> None:
        super().__init__([2])

    def __bool__(self) -> bool:
        return False


def _registered_diagnostics() -> dict[str, Any]:
    return {
        "schema": _DIAGNOSTICS_SCHEMA,
        "visibility": _DIAGNOSTICS_VISIBILITY,
        "level_records": [[0]],
        "level_record_counts": [2],
        "level_record_probabilities": [1.0],
        "jump_family_counts": {},
    }


def _carrier_program(
    *,
    measurement_keys: list[str] | None = None,
    measurement_targets: list[int] | None = None,
    num_qubits: int = 1,
) -> dict[str, Any]:
    keys = [] if measurement_keys is None else list(measurement_keys)
    targets = [] if measurement_targets is None else list(measurement_targets)
    substeps: list[dict[str, Any]] = []
    if keys or targets:
        substeps.append(
            {
                "substep_kind": "measurement",
                "operation_records": [
                    {
                        "measurement_keys": keys,
                        "targets": targets,
                    }
                ],
            }
        )
    return {
        "requires_scalable_backend": False,
        "program": {
            "num_qubits": num_qubits,
            "substeps": substeps,
        },
    }


def _measured_execution(
    *,
    local_dim: int,
    diagnostics_case: str = "valid",
) -> dict[str, Any]:
    execution = {
        "total_probability_residual": 0.0,
        "trajectory_sampling": {
            "mode": "sampled_fixed_microstep_mcwf_trajectories",
            "rng_seed_was_explicit": True,
            "trajectory_count": 2,
        },
        "jump_sampling": {"probability_mass_residual_max": 0.0},
        "measurement_keys": ["m0"],
        "measurement_targets": [0],
        "measurement_records": [[0]],
        "record_counts": [2],
        "record_probabilities": [1.0],
        "local_dims": [local_dim],
        "mps_truncation_ledger": _uncapped_ledger(),
    }
    diagnostics = _registered_diagnostics()
    if diagnostics_case == "container_omitted":
        return execution
    if diagnostics_case == "container_none":
        execution["evaluator_only_diagnostics"] = None
        return execution
    if diagnostics_case == "level_omitted":
        diagnostics.pop("level_records")
    elif diagnostics_case == "level_none":
        diagnostics["level_records"] = None
    elif diagnostics_case == "level_empty":
        diagnostics["level_records"] = []
    elif diagnostics_case != "valid":
        raise ValueError(f"unknown diagnostics case {diagnostics_case!r}")
    execution["evaluator_only_diagnostics"] = diagnostics
    return execution


def _uncapped_ledger() -> dict[str, Any]:
    return {
        "explicit_truncation_requested": False,
        "exact_bond_dimension_sufficient": 1,
        "exact_bond_policy": "unbounded_no_requested_truncation",
        "accepted_as_exact_bond_representation": True,
        "discarded_weight_ledger_complete": True,
        "discarded_weight_sum": 0.0,
        "worst_cut_discarded_weight": 0.0,
        "n_truncating_ops": 0,
        "epistemic_class": "c",
    }


def _record_metric_certification() -> dict[str, Any]:
    sampling_halfwidth = 0.5 * math.sqrt(math.log(200.0) / 4.0)
    return {
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


def _channel_metric_certification() -> dict[str, Any]:
    return {
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


def _policy(
    execution: dict[str, Any],
    certification: dict[str, Any],
    *,
    declared_local_dims: list[int] | None = None,
    program: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if declared_local_dims is None:
        declared_local_dims = list(execution.get("local_dims", ()))
    return CERTIFICATION.restricted_acceptance_policy(
        execution=execution,
        certification=certification,
        program=(
            {"requires_scalable_backend": False}
            if program is None
            else program
        ),
        declared_local_dims=declared_local_dims,
        rng_seed=17,
        trajectory_count=2,
        mass_residual_budget=0.1,
    )


@pytest.mark.parametrize(
    "local_dims_case",
    ["omitted", "none", "falsy_canonical"],
)
def test_measured_execution_rejects_missing_declared_local_dims(
    local_dims_case: str,
) -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )
    accepted = CERTIFICATION.restricted_acceptance_policy(
        execution=execution,
        certification=_record_metric_certification(),
        program={"requires_scalable_backend": False},
        declared_local_dims=[2],
        rng_seed=17,
        trajectory_count=2,
        mass_residual_budget=0.1,
    )
    assert accepted["accepted_for_restricted_execution"] is True
    if local_dims_case == "omitted":
        execution.pop("local_dims")
    elif local_dims_case == "none":
        execution["local_dims"] = None
    else:
        execution["local_dims"] = _FalsyCanonicalLocalDims()

    with pytest.raises(ValueError):
        CERTIFICATION.restricted_acceptance_policy(
            execution=execution,
            certification=_record_metric_certification(),
            program={"requires_scalable_backend": False},
            declared_local_dims=[2],
            rng_seed=17,
            trajectory_count=2,
            mass_residual_budget=0.1,
        )


def test_policy_rejects_forged_qubit_local_dims_for_declared_multilevel_run() -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )

    with pytest.raises(ValueError):
        CERTIFICATION.restricted_acceptance_policy(
            execution=execution,
            certification=_record_metric_certification(),
            program={"requires_scalable_backend": False},
            declared_local_dims=[3],
            rng_seed=17,
            trajectory_count=2,
            mass_residual_budget=0.1,
        )


def test_dense_certification_rejects_forged_qubit_local_dims_before_routing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record_path_calls = 0

    def forbidden_record_path(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal record_path_calls
        record_path_calls += 1
        return {"unexpected": "binary downgrade"}

    monkeypatch.setattr(
        CERTIFICATION,
        "_certify_record_path",
        forbidden_record_path,
    )

    with pytest.raises(ValueError):
        CERTIFICATION.dense_jointL_record_certification(
            SimpleNamespace(),
            _measured_execution(
                local_dim=2,
                diagnostics_case="container_omitted",
            ),
            {"requires_scalable_backend": False},
            declared_local_dims=[3],
        )

    assert record_path_calls == 0


def test_policy_rejects_deleted_compiled_measurement_layout() -> None:
    execution = _measured_execution(
        local_dim=3,
        diagnostics_case="container_omitted",
    )
    execution.update(
        {
            "measurement_keys": [],
            "measurement_targets": [],
            "measurement_records": [[]],
            "record_counts": [2],
            "record_probabilities": [1.0],
        }
    )

    with pytest.raises(ValueError):
        CERTIFICATION.restricted_acceptance_policy(
            execution=execution,
            certification=_channel_metric_certification(),
            program=_carrier_program(
                measurement_keys=["m0"],
                measurement_targets=[0],
            ),
            declared_local_dims=[3],
            rng_seed=17,
            trajectory_count=2,
            mass_residual_budget=0.1,
        )


def test_policy_rejects_measurement_target_outside_declared_sites() -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )
    execution["measurement_targets"] = [1]

    with pytest.raises(ValueError):
        _policy(
            execution,
            _record_metric_certification(),
            declared_local_dims=[2],
        )


def test_dense_certification_rejects_program_target_mismatch_before_routing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    level_path_calls = 0

    def forbidden_level_path(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal level_path_calls
        level_path_calls += 1
        return {"unexpected": "unbound level route"}

    monkeypatch.setattr(
        CERTIFICATION,
        "_certify_level_path",
        forbidden_level_path,
    )
    execution = _measured_execution(local_dim=3)
    execution["local_dims"] = [3, 3]
    execution["measurement_targets"] = [1]

    with pytest.raises(ValueError):
        CERTIFICATION.dense_jointL_record_certification(
            SimpleNamespace(),
            execution,
            _carrier_program(
                measurement_keys=["m0"],
                measurement_targets=[0],
                num_qubits=2,
            ),
            declared_local_dims=[3, 3],
        )

    assert level_path_calls == 0


def test_policy_rejects_declared_dims_length_mismatching_program_sites() -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )

    with pytest.raises(ValueError):
        _policy(
            execution,
            _record_metric_certification(),
            declared_local_dims=[2],
            program=_carrier_program(
                measurement_keys=["m0"],
                measurement_targets=[0],
                num_qubits=2,
            ),
        )


@pytest.mark.parametrize(
    "diagnostics_case",
    [
        "container_omitted",
        "container_none",
        "level_omitted",
        "level_none",
        "level_empty",
    ],
)
def test_dense_certification_rejects_multilevel_measurement_without_levels(
    monkeypatch: pytest.MonkeyPatch,
    diagnostics_case: str,
) -> None:
    record_path_calls = 0

    def forbidden_record_path(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal record_path_calls
        record_path_calls += 1
        return {"unexpected": "binary downgrade"}

    monkeypatch.setattr(
        CERTIFICATION,
        "_certify_record_path",
        forbidden_record_path,
    )

    with pytest.raises(ValueError):
        CERTIFICATION.dense_jointL_record_certification(
            SimpleNamespace(),
            _measured_execution(
                local_dim=3,
                diagnostics_case=diagnostics_case,
            ),
            {"requires_scalable_backend": False},
            declared_local_dims=[3],
        )

    assert record_path_calls == 0


@pytest.mark.parametrize(
    "diagnostics_case",
    [
        "container_omitted",
        "container_none",
        "level_omitted",
        "level_none",
        "level_empty",
    ],
)
def test_policy_rejects_multilevel_binary_metric_downgrade(
    diagnostics_case: str,
) -> None:
    with pytest.raises(ValueError):
        _policy(
            _measured_execution(
                local_dim=3,
                diagnostics_case=diagnostics_case,
            ),
            _record_metric_certification(),
        )


def test_dense_certification_retains_registered_qubit_binary_record_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = {"route": "registered qubit binary record path"}
    monkeypatch.setattr(
        CERTIFICATION,
        "_certify_record_path",
        lambda *_args, **_kwargs: sentinel,
    )
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )

    result = CERTIFICATION.dense_jointL_record_certification(
        SimpleNamespace(),
        execution,
        _carrier_program(
            measurement_keys=["m0"],
            measurement_targets=[0],
        ),
        declared_local_dims=[2],
    )

    assert result is sentinel
    policy = _policy(
        execution,
        _record_metric_certification(),
        declared_local_dims=[2],
        program=_carrier_program(
            measurement_keys=["m0"],
            measurement_targets=[0],
        ),
    )
    assert policy["accepted_for_restricted_execution"] is True
    assert policy["dense_jointL_record_certification"]["comparison_object"] == (
        "record_probabilities"
    )


def test_multilevel_no_measurement_channel_path_does_not_require_level_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution = _measured_execution(
        local_dim=3,
        diagnostics_case="container_omitted",
    )
    execution.update(
        {
            "measurement_keys": [],
            "measurement_targets": [],
            "measurement_records": [[]],
            "record_counts": [2],
            "record_probabilities": [1.0],
        }
    )
    sentinel = {"route": "registered no-measurement channel path"}
    monkeypatch.setattr(
        CERTIFICATION,
        "_certify_channel_path",
        lambda *_args, **_kwargs: sentinel,
    )

    result = CERTIFICATION.dense_jointL_record_certification(
        SimpleNamespace(),
        execution,
        _carrier_program(),
        declared_local_dims=[3],
    )

    assert result is sentinel
    policy = _policy(
        execution,
        _channel_metric_certification(),
        declared_local_dims=[3],
        program=_carrier_program(),
    )
    assert policy["accepted_for_restricted_execution"] is True
    assert policy["dense_jointL_record_certification"]["comparison_object"] == (
        "within_substep_window_channel"
    )

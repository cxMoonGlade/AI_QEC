from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any

import pytest

import error_coupling_simulator.certify.axis1_mps as CERTIFICATION
from tests._support.mcwf_artifact_certification import (
    passing_mcwf_artifact_certification,
)


_DIAGNOSTICS_SCHEMA = (
    "error_coupling_simulator.frontend."
    "mcwf_mps_evaluator_only_diagnostics.v2"
)
_DIAGNOSTICS_VISIBILITY = (
    "evaluator_only_not_emitted_record_or_downstream_estimator_input"
)
_MEASUREMENT_BASIS_SEMANTICS = (
    "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
    "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
)
_LEVEL_RECORD_SEMANTICS = (
    "schedule-ordered local measurement eigenlabel tuples: "
    "X columns use 0=|+>,1=|-> and preserve leaked level labels >=2; "
    "Z columns use computational local levels"
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
        "level_record_semantics": _LEVEL_RECORD_SEMANTICS,
        "level_records": [[0]],
        "level_record_counts": [2],
        "level_record_probabilities": [1.0],
        "jump_family_counts": {},
    }


def _carrier_program(
    *,
    measurement_keys: list[str] | None = None,
    measurement_targets: list[int] | None = None,
    measurement_bases: list[str] | None = None,
    reset_after: list[bool] | None = None,
    num_qubits: int = 1,
) -> dict[str, Any]:
    keys = [] if measurement_keys is None else list(measurement_keys)
    targets = [] if measurement_targets is None else list(measurement_targets)
    bases = (
        ["Z"] * len(keys)
        if measurement_bases is None
        else list(measurement_bases)
    )
    reset_mask = (
        [False] * len(keys) if reset_after is None else list(reset_after)
    )
    substeps: list[dict[str, Any]] = []
    if keys or targets:
        if not (len(keys) == len(targets) == len(bases) == len(reset_mask)):
            raise ValueError("measurement layout vectors must have equal length")
        operation_records = []
        for key, target, basis, reset in zip(
            keys,
            targets,
            bases,
            reset_mask,
            strict=True,
        ):
            operation_record = {
                "measurement_keys": [key],
                "targets": [target],
                "basis": basis,
            }
            if reset:
                operation_record["reset_after_measurement"] = True
            operation_records.append(operation_record)
        substeps.append(
            {
                "substep_kind": "measurement",
                "operation_records": operation_records,
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
        "measurement_bases": ["Z"],
        "reset_after": [False],
        "measurement_basis": "Z",
        "measurement_basis_semantics": _MEASUREMENT_BASIS_SEMANTICS,
        "measurement_records": [[0]],
        "record_counts": [2],
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


def _policy(
    execution: dict[str, Any],
    certification: dict[str, Any],
    *,
    declared_local_dims: list[int] | None = None,
    program: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if declared_local_dims is None:
        declared_local_dims = list(execution.get("local_dims", ()))
    execution.setdefault(
        "finite_step_policy",
        {"microstep_count": 1, "order": "first_order"},
    )
    policy_program = (
        {"requires_scalable_backend": False}
        if program is None
        else program
    )
    return CERTIFICATION.restricted_acceptance_policy(
        execution=execution,
        certification=certification,
        program=policy_program,
        declared_local_dims=declared_local_dims,
        rng_seed=17,
        trajectory_count=2,
        mass_residual_budget=0.1,
        dynamics_artifact_reference_certification=(
            passing_mcwf_artifact_certification(
                policy_program,
                local_dims=declared_local_dims,
            )
        ),
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
    accepted = _policy(
        execution,
        _record_metric_certification(),
        declared_local_dims=[2],
    )
    assert accepted["accepted_for_restricted_execution"] is True
    if local_dims_case == "omitted":
        execution.pop("local_dims")
    elif local_dims_case == "none":
        execution["local_dims"] = None
    else:
        execution["local_dims"] = _FalsyCanonicalLocalDims()

    with pytest.raises(ValueError):
        _policy(
            execution,
            _record_metric_certification(),
            declared_local_dims=[2],
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
            "measurement_bases": [],
            "reset_after": [],
            "measurement_basis": "none",
            "measurement_records": [[]],
            "record_counts": [2],
            "record_probabilities": [1.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="execution measurement keys must match carrier program",
    ):
        CERTIFICATION.restricted_acceptance_policy(
            execution=execution,
            certification=_record_metric_certification(),
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


@pytest.mark.parametrize(
    ("field", "reordered_value"),
    (
        pytest.param(
            "measurement_bases",
            ["Z", "X"],
            id="ordered-measurement-bases",
        ),
        pytest.param(
            "reset_after",
            [False, True],
            id="ordered-reset-mask",
        ),
    ),
)
def test_policy_rejects_reordered_compiled_measurement_semantics(
    field: str,
    reordered_value: list[str] | list[bool],
) -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )
    execution.update(
        {
            "measurement_keys": ["mx", "mz"],
            "measurement_targets": [0, 1],
            "measurement_bases": ["X", "Z"],
            "reset_after": [True, False],
            "measurement_basis": "mixed_pauli",
            "measurement_records": [[0, 0]],
            "local_dims": [2, 2],
        }
    )
    program = _carrier_program(
        measurement_keys=["mx", "mz"],
        measurement_targets=[0, 1],
        measurement_bases=["X", "Z"],
        reset_after=[True, False],
        num_qubits=2,
    )

    honest_policy = _policy(
        execution,
        _record_metric_certification(),
        declared_local_dims=[2, 2],
        program=program,
    )
    assert honest_policy["accepted_for_restricted_execution"] is True

    execution[field] = reordered_value
    with pytest.raises(ValueError):
        _policy(
            execution,
            _record_metric_certification(),
            declared_local_dims=[2, 2],
            program=program,
        )


@pytest.mark.parametrize(
    ("field", "reordered_value"),
    (
        pytest.param(
            "measurement_bases",
            ["Z", "X"],
            id="ordered-measurement-bases",
        ),
        pytest.param(
            "reset_after",
            [False, True],
            id="ordered-reset-mask",
        ),
    ),
)
def test_dense_certification_rejects_reordered_measurement_semantics_before_routing(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    reordered_value: list[str] | list[bool],
) -> None:
    record_path_calls = 0

    def forbidden_record_path(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal record_path_calls
        record_path_calls += 1
        return {"unexpected": "unbound ordered measurement layout"}

    monkeypatch.setattr(
        CERTIFICATION,
        "_certify_record_path",
        forbidden_record_path,
    )
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )
    execution.update(
        {
            "measurement_keys": ["mx", "mz"],
            "measurement_targets": [0, 1],
            "measurement_bases": ["X", "Z"],
            "reset_after": [True, False],
            "measurement_basis": "mixed_pauli",
            "measurement_records": [[0, 0]],
            "local_dims": [2, 2],
        }
    )
    execution[field] = reordered_value

    with pytest.raises(ValueError):
        CERTIFICATION.dense_jointL_record_certification(
            SimpleNamespace(),
            execution,
            _carrier_program(
                measurement_keys=["mx", "mz"],
                measurement_targets=[0, 1],
                measurement_bases=["X", "Z"],
                reset_after=[True, False],
                num_qubits=2,
            ),
            declared_local_dims=[2, 2],
        )

    assert record_path_calls == 0


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


def test_no_measurement_mcwf_path_is_unavailable_without_registered_linear_metric() -> None:
    execution = _measured_execution(
        local_dim=3,
        diagnostics_case="container_omitted",
    )
    execution.update(
        {
            "measurement_keys": [],
            "measurement_targets": [],
            "measurement_bases": [],
            "reset_after": [],
            "measurement_basis": "none",
            "measurement_records": [[]],
            "record_counts": [2],
            "record_probabilities": [1.0],
        }
    )
    result = CERTIFICATION.dense_jointL_record_certification(
        SimpleNamespace(),
        execution,
        _carrier_program(),
        declared_local_dims=[3],
    )

    assert result == {
        "executed": False,
        "passed": False,
        "passed_gross": False,
        "reason": (
            "mcwf_normalized_candidate_law_has_no_registered_linear_channel_metric"
        ),
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }
    assert "within_substep_window_channel" not in CERTIFICATION._MCWF_METRIC_IDENTITIES
    for retired_name in (
        "_certify_channel_path",
        "_build_carrier_channel_window",
        "_carrier_first_order_window_superop",
        "_process_infidelity_and_choi_distance",
    ):
        assert not hasattr(CERTIFICATION, retired_name)

    policy = _policy(
        execution,
        result,
        declared_local_dims=[3],
        program=_carrier_program(),
    )
    assert policy["certification_status"] == "unavailable"
    assert policy["diagnostic_only"] is True
    assert policy["accepted_for_restricted_execution"] is False
    assert policy["accepted_for_sampled_execution_evidence"] is False
    assert policy["accepted_for_exact_dense_probability_evidence"] is False
    assert policy["dense_jointL_record_certification"]["reason"] == result["reason"]


def test_mcwf_policy_rejects_and_does_not_emit_retired_choi_companion() -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )
    certification = _record_metric_certification()
    policy = _policy(
        execution,
        certification,
        program=_carrier_program(
            measurement_keys=["m0"],
            measurement_targets=[0],
        ),
    )
    assert "choi_trace_distance" not in policy[
        "dense_jointL_record_certification"
    ]
    assert policy["gross_strict_gate_split"]["strict_gate_role"] == (
        "strict_record_tv_numerical_tripwire_not_exact_evidence"
    )

    forged = dict(certification)
    forged["choi_trace_distance"] = 0.0
    with pytest.raises(ValueError, match="retired.*Choi"):
        _policy(
            execution,
            forged,
            program=_carrier_program(
                measurement_keys=["m0"],
                measurement_targets=[0],
            ),
        )


def _joint_level_binary_metric_certification() -> dict[str, Any]:
    support_size = 1
    trajectory_count = 2
    confidence = 0.99
    halfwidth = 0.5 * support_size * math.sqrt(
        math.log(4.0 * support_size / (1.0 - confidence))
        / (2.0 * trajectory_count)
    )
    return {
        "executed": True,
        "passed": True,
        "passed_gross": True,
        "comparison_outcome_is_metric": True,
        "comparison_object": (
            "measurement_basis_level_and_emitted_binary_record_populations"
        ),
        "metric": "maximum_component_total_variation_distance",
        "metric_convention": (
            "max(TV_label, TV_binary), with each TV = 1/2 * sum_i "
            "|p_i - q_i|; joint pass is the logical AND of the "
            "declared-basis eigenlabel and emitted binary Record TV gates"
        ),
        "oracle": (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel"
        ),
        "oracle_independent_of_carrier_grouping": True,
        "readout_model_independent": False,
        "component_values": {
            "declared_basis_eigenlabel_tv": 0.0,
            "emitted_binary_record_tv": 0.0,
        },
        "value": 0.0,
        "gate": 1.0e-6,
        "gross_gate": 0.1,
        "gross_gate_ceiling": 0.45,
        "sampling_finite_shot_halfwidth": halfwidth,
        "sampling_support_size": support_size,
        "effective_gate_including_sampling_ci": 1.0e-6,
        "gross_effective_gate_including_sampling_ci": 0.45,
        "sampling_ci_method": (
            "bonferroni_two_component_per_bin_two_sided_hoeffding_"
            "capped_at_gross_tv_ceiling"
        ),
        "sampling_confidence": confidence,
        "trajectory_count": trajectory_count,
        "dense_evidence_schema": (
            "error_coupling_simulator.carrier.joint_lindbladian."
            "assemble_substep_channel:measurement_basis_level_populations.v2"
        ),
        "dense_evidence_content_hash": None,
    }


def test_policy_artifact_validation_reads_execution_dims_before_metric_gate() -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )
    execution["finite_step_policy"] = {
        "microstep_count": 1,
        "order": "first_order",
    }
    program = _carrier_program(
        measurement_keys=["m0"],
        measurement_targets=[0],
    )
    packet = passing_mcwf_artifact_certification(program, local_dims=[2])

    with pytest.raises(ValueError, match="independently declared nonempty"):
        CERTIFICATION.restricted_acceptance_policy(
            execution=execution,
            certification=_record_metric_certification(),
            program=program,
            declared_local_dims=None,
            rng_seed=17,
            trajectory_count=2,
            mass_residual_budget=0.1,
            dynamics_artifact_reference_certification=packet,
        )


@pytest.mark.parametrize(
    ("execution_update", "exception", "match"),
    [
        ({"local_dims": [True]}, ValueError, "exact integers >= 2"),
        ({"finite_step_policy": []}, TypeError, "must be a mapping"),
    ],
)
def test_policy_rejects_invalid_artifact_validation_inputs(
    execution_update: dict[str, Any],
    exception: type[Exception],
    match: str,
) -> None:
    execution = _measured_execution(
        local_dim=2,
        diagnostics_case="container_omitted",
    )
    execution.setdefault(
        "finite_step_policy",
        {"microstep_count": 1, "order": "first_order"},
    )
    execution.update(execution_update)
    program = _carrier_program(
        measurement_keys=["m0"],
        measurement_targets=[0],
    )
    packet = passing_mcwf_artifact_certification(program, local_dims=[2])

    with pytest.raises(exception, match=match):
        CERTIFICATION.restricted_acceptance_policy(
            execution=execution,
            certification=_record_metric_certification(),
            program=program,
            declared_local_dims=None,
            rng_seed=17,
            trajectory_count=2,
            mass_residual_budget=0.1,
            dynamics_artifact_reference_certification=packet,
        )


def test_policy_requires_readout_independence_when_metric_identity_declares_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metric, convention, oracle, _ = CERTIFICATION._MCWF_METRIC_IDENTITIES[
        "record_probabilities"
    ]
    monkeypatch.setitem(
        CERTIFICATION._MCWF_METRIC_IDENTITIES,
        "record_probabilities",
        (metric, convention, oracle, True),
    )

    with pytest.raises(ValueError, match="readout_model_independent must be true"):
        _policy(
            _measured_execution(
                local_dim=2,
                diagnostics_case="container_omitted",
            ),
            _record_metric_certification(),
        )


@pytest.mark.parametrize(
    ("case", "exception", "match"),
    [
        ("not_mapping", TypeError, "requires component_values"),
        ("wrong_fields", ValueError, "fields must be exact"),
        ("wrong_max", ValueError, "maximum component TV"),
    ],
)
def test_policy_rejects_invalid_joint_component_values(
    case: str,
    exception: type[Exception],
    match: str,
) -> None:
    certification = _joint_level_binary_metric_certification()
    if case == "not_mapping":
        certification["component_values"] = None
    elif case == "wrong_fields":
        certification["component_values"] = {
            "declared_basis_eigenlabel_tv": 0.0,
        }
    elif case == "wrong_max":
        certification["component_values"] = {
            "declared_basis_eigenlabel_tv": 0.25,
            "emitted_binary_record_tv": 0.0,
        }
        certification["value"] = 0.0
    else:  # pragma: no cover - parametrization is exhaustive.
        raise AssertionError(case)

    with pytest.raises(exception, match=match):
        _policy(
            _measured_execution(local_dim=3),
            certification,
            declared_local_dims=[3],
            program=_carrier_program(
                measurement_keys=["m0"],
                measurement_targets=[0],
            ),
        )


def test_policy_rejects_component_values_for_nonjoint_and_nonmetric_rows() -> None:
    nonjoint = _record_metric_certification()
    nonjoint["component_values"] = {
        "declared_basis_eigenlabel_tv": 0.0,
        "emitted_binary_record_tv": 0.0,
    }
    with pytest.raises(ValueError, match="non-joint certification"):
        _policy(
            _measured_execution(
                local_dim=2,
                diagnostics_case="container_omitted",
            ),
            nonjoint,
        )

    nonmetric = _record_metric_certification()
    nonmetric.update(
        {
            "executed": False,
            "passed": False,
            "passed_gross": False,
            "comparison_outcome_is_metric": False,
            "reason": "diagnostic",
            "component_values": {},
        }
    )
    with pytest.raises(ValueError, match="non-metric certification"):
        _policy(
            _measured_execution(
                local_dim=2,
                diagnostics_case="container_omitted",
            ),
            nonmetric,
        )

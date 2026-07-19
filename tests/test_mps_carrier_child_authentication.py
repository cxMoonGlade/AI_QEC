from __future__ import annotations

import copy
import hashlib
import json
from contextlib import contextmanager

import pytest

from error_coupling_simulator.frontend import (
    AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    CircuitBuilder,
    axis1_carrier_execution_manifest,
    axis1_mcwf_mps_state_record_execution_manifest,
    axis1_qt_mps_restricted_execution_manifest,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.frontend import axis1_mcwf_mps_execution as mcwf_execution
from error_coupling_simulator.frontend import axis1_qt_mps_execution as qt_execution
from error_coupling_simulator.frontend import axis1_carrier_execution as carrier_execution


_FORGED_CHILD_TARGETS = {
    "qt": (
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
    ),
    "mcwf": (
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
    ),
    "carrier": (
        carrier_execution,
        "axis1_carrier_execution_manifest",
    ),
}


@contextmanager
def _rejects_forged_child_without_mutation(
    expected_exception,
    route,
    monkeypatch,
    schedule,
    forged,
):
    owner, attribute = _FORGED_CHILD_TARGETS[route]
    delegated_child = getattr(owner, attribute)
    calls = []

    def counted_child(*args, **kwargs):
        calls.append((args, kwargs))
        return delegated_child(*args, **kwargs)

    monkeypatch.setattr(owner, attribute, counted_child)
    forged_before = copy.deepcopy(forged)
    schedule_before = copy.deepcopy(schedule)

    with pytest.raises(expected_exception):
        yield

    assert forged == forged_before
    assert schedule == schedule_before
    assert len(calls) == 1
    delegated_args, _delegated_kwargs = calls[0]
    assert len(delegated_args) == 1
    assert delegated_args[0] is schedule


def _rehash(payload: dict[str, object]) -> None:
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


@pytest.fixture(scope="module")
def measurement_schedule():
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    return circuit_ir_to_substep_schedule(builder.build())


@pytest.fixture(scope="module")
def projected_measurement_schedule():
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    builder.observable("logical0", xor=("m0",), index=0)
    return circuit_ir_to_substep_schedule(builder.build())


@pytest.fixture(scope="module")
def dense_measurement_schedule():
    builder = CircuitBuilder(num_qubits=1)
    builder.idle(0, duration_ns=1.0)
    builder.measure(0, key="m0")
    return circuit_ir_to_substep_schedule(builder.build())


@pytest.fixture(scope="module")
def honest_qt_child(measurement_schedule):
    return axis1_qt_mps_restricted_execution_manifest(
        measurement_schedule,
        device="cuda",
    )


@pytest.fixture(scope="module")
def honest_qt_capped_child(measurement_schedule):
    return axis1_qt_mps_restricted_execution_manifest(
        measurement_schedule,
        device="cuda",
        max_bond=2,
    )


@pytest.fixture(scope="module")
def honest_mcwf_child(measurement_schedule):
    return axis1_mcwf_mps_state_record_execution_manifest(
        measurement_schedule,
        device="cuda",
        local_dims=[3],
        max_bond=2,
        trajectory_count=4,
        rng_seed=17,
    )


@pytest.fixture(scope="module")
def honest_multilevel_mcwf_child(measurement_schedule):
    return axis1_mcwf_mps_state_record_execution_manifest(
        measurement_schedule,
        device="cuda",
        local_dims=[3],
        initial_levels=[2],
        trajectory_count=4,
        rng_seed=17,
    )


@pytest.fixture(scope="module")
def honest_mcwf_carrier_child(measurement_schedule):
    return axis1_carrier_execution_manifest(
        measurement_schedule,
        device="cuda",
        execution_backend_contract=(
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        execution_backend_options={
            "local_dims": [3],
            "initial_levels": [2],
            "trajectory_count": 4,
            "rng_seed": 17,
        },
    )


@pytest.fixture(scope="module")
def honest_dense_carrier_child(dense_measurement_schedule):
    return axis1_carrier_execution_manifest(
        dense_measurement_schedule,
        device="cuda",
        execution_backend_contract=AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
    )


@pytest.fixture(scope="module")
def honest_projected_qt_child(projected_measurement_schedule):
    return axis1_qt_mps_restricted_execution_manifest(
        projected_measurement_schedule,
        device="cuda",
    )


@pytest.fixture(scope="module")
def honest_projected_mcwf_child(projected_measurement_schedule):
    return axis1_mcwf_mps_state_record_execution_manifest(
        projected_measurement_schedule,
        device="cuda",
        local_dims=[3],
        initial_levels=[2],
        trajectory_count=4,
        rng_seed=17,
    )


def test_qt_carrier_rejects_child_from_wrong_source_hash(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["source_hash"] = "f" * 64
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_child_from_wrong_source_kind(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["source_kind"] = "stim_circuit"
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_child_from_wrong_backend_contract(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["backend_contract"] = "mcwf_mps_state_record"
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_child_from_wrong_device(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["device"] = "cuda:1"
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            device="cuda",
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_child_with_wrong_requested_option(
    monkeypatch,
    measurement_schedule,
    honest_qt_capped_child,
):
    forged = copy.deepcopy(honest_qt_capped_child)
    forged["max_bond"] = 3
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={"max_bond": 2},
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("max_bond", 1),
        ("max_branches", 4095),
        ("max_record_materialization_outcomes", 4095),
        ("microstep_count", 2),
        ("finite_step_order", "strang_second_order"),
        ("worst_cut_discarded_weight_gate", 0.1),
        ("total_discarded_weight_gate", 0.1),
        ("trajectory_count", 1),
        ("rng_seed", 1),
        ("dense_oracle_certification_requested", False),
    ),
)
def test_qt_carrier_rejects_child_with_wrong_default_option(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_qt_child)
    forged[field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_child_with_invalid_content_hash(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["content_hash"] = "0" * 64
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_incomplete_exact_record_support(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    execution = forged["mps_execution"]
    execution["measurement_records"] = execution["measurement_records"][:1]
    execution["record_probabilities"] = execution["record_probabilities"][:1]
    execution["record_count"] = 1
    execution["total_probability"] = sum(execution["record_probabilities"])
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_forged_record_materialization_preflight(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["record_materialization_preflight"]["checked_before_cuda"] = False
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_forged_measurement_sampling_policy(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["mps_execution"]["trajectory_sampling"][
        "measurement_sampling_policy"
    ] = "legacy_independent_site_sampling"
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("content_hash", "f" * 64),
        ("backend_contract", "mcwf_mps_state_record"),
        ("requires_scalable_backend", True),
    ),
)
def test_qt_carrier_rejects_child_from_wrong_carrier_program(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_qt_child)
    forged["carrier_program"][field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_mcwf_carrier_rejects_child_from_wrong_source_hash(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged["source_hash"] = "f" * 64
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("source_kind", "stim_circuit"),
        (
            "schedule_representability",
            "fixture_schedule",
        ),
        ("representability", "fixture_execution"),
        ("backend_contract", "qt_mps_state_record"),
        ("gpu_required", False),
        ("device", "cuda:1"),
        ("max_bond", 3),
        ("microstep_count", 2),
        ("finite_step_order", "strang_second_order"),
        ("trajectory_count", 5),
        ("rng_seed", 18),
    ),
)
def test_mcwf_carrier_rejects_wrong_child_provenance_or_option(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged[field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_rejects_child_with_invalid_content_hash(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged["content_hash"] = "0" * 64
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("content_hash", "f" * 64),
        ("backend_contract", "qt_mps_state_record"),
        ("requires_scalable_backend", True),
    ),
)
def test_mcwf_carrier_rejects_child_from_wrong_carrier_program(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged["carrier_program"][field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    "field",
    (
        "claims_production_scalable_backend",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
    ),
)
def test_mcwf_carrier_rejects_forbidden_child_claim(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
    field,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged[field] = True
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_rejects_multilevel_metric_family_downgrade(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["mps_execution"].pop("evaluator_only_diagnostics")
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_rejects_wrong_nested_trajectory_count(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["mps_execution"]["trajectory_sampling"]["trajectory_count"] = 5
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    ("container", "field", "bad_value"),
    (
        ("trajectory_sampling", "rng_seed", 18),
        ("finite_step_policy", "order", "strang_second_order"),
        ("finite_step_policy", "microstep_count", 2),
        (
            "multilevel_measurement_policy",
            "leaked_readout_b",
            0.5,
        ),
        (None, "initial_levels", [1]),
        (None, "local_dims", [2]),
    ),
)
def test_mcwf_carrier_rejects_wrong_nested_execution_option(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
    container,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    execution = forged["mps_execution"]
    target = execution if container is None else execution[container]
    target[field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_rejects_rehashed_false_green_runtime_mass_policy(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["mps_execution"]["jump_sampling"][
        "probability_mass_residual_max"
    ] = 0.5
    probability_policy = forged["restricted_acceptance_policy"]["probability"]
    probability_policy["runtime_candidate_mass_residual"] = 0.5
    probability_policy["runtime_candidate_mass_residual_within_budget"] = True
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_rejects_rehashed_impossible_unbounded_truncation_loss(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    ledger = forged["mps_execution"]["mps_truncation_ledger"]
    ledger["discarded_weight_sum"] = 0.2
    ledger["worst_cut_discarded_weight"] = 0.2
    ledger["n_truncating_ops"] = 1
    truncation_policy = forged["restricted_acceptance_policy"]["mps_truncation"]
    truncation_policy["discarded_weight_sum"] = 0.2
    truncation_policy["worst_cut_discarded_weight"] = 0.2
    truncation_policy["truncation_detected"] = True
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_binds_measurement_identity_to_requested_schedule(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["mps_execution"]["measurement_keys"] = ["shadow_m0"]
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_requires_type_exact_canonical_policy(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["restricted_acceptance_policy"]["probability"][
        "runtime_candidate_mass_residual_within_budget"
    ] = 1
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_rejects_extra_field_in_canonical_policy(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["restricted_acceptance_policy"]["content_hash"] = "f" * 64
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_qt_carrier_rejects_rehashed_forbidden_detector_projection(
    monkeypatch,
    measurement_schedule,
    honest_qt_child,
):
    """A schedule with no detectors cannot acquire detector rows in a child."""

    forged = copy.deepcopy(honest_qt_child)
    execution = forged["mps_execution"]
    execution["detector_records_emitted"] = True
    execution["detector_names"] = ["shadow_detector"]
    execution["detector_records"] = [[0], [1]]
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_mcwf_carrier_rejects_rehashed_forbidden_detector_rows(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    """The parent reconstructs detector rows even when the child hash is valid."""

    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["mps_execution"]["detector_records"] = [[1], [0]]
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_rejects_rehashed_child_from_wrong_source_hash(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged["source_hash"] = "f" * 64
    _rehash(forged)
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "carrier", monkeypatch, measurement_schedule, forged
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema", "error_coupling_simulator.frontend.carrier_execution.v1"),
        ("source_kind", "stim_circuit"),
        ("schedule_representability", "shadow_schedule"),
        ("representability", "shadow_carrier"),
        ("execution_backend_contract", AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT),
        ("device", "cuda:1"),
    ],
)
def test_auto_router_rejects_rehashed_child_envelope_drift(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged[field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "carrier", monkeypatch, measurement_schedule, forged
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    ("gpu_required", "expected_exception"),
    [(False, ValueError), (1, TypeError)],
)
def test_auto_router_requires_exact_true_gpu_child_claim(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
    gpu_required,
    expected_exception,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged["gpu_required"] = gpu_required
    _rehash(forged)
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        expected_exception, "carrier", monkeypatch, measurement_schedule, forged
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    "field",
    [
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "claims_scalable_backend_completed",
        "claims_production_scalable_backend",
        "claims_exact_joint_lindblad_generator",
        "claims_qt_mps_backend_execution",
        "claims_qutip_cuquantum_execution",
    ],
)
def test_auto_router_rejects_rehashed_false_claim_boundary_promotion(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
    field,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged[field] = True
    _rehash(forged)
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "carrier", monkeypatch, measurement_schedule, forged
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_rejects_unauthenticated_child_payload(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged["source_hash"] = "f" * 64
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "carrier", monkeypatch, measurement_schedule, forged
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_rejects_rehashed_untrusted_route_carrier_program(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged["carrier_program"]["content_hash"] = "f" * 64
    _rehash(forged)
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "carrier", monkeypatch, measurement_schedule, forged
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_authenticates_trusted_dense_route_program(
    monkeypatch,
    dense_measurement_schedule,
    honest_dense_carrier_child,
):
    forged = copy.deepcopy(honest_dense_carrier_child)
    forged["carrier_program"]["backend_contract"] = (
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    )
    _rehash(forged)
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError,
        "carrier",
        monkeypatch,
        dense_measurement_schedule,
        forged,
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            dense_measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options=None,
        )


def test_auto_router_rejects_dense_child_added_false_claim_promotion(
    monkeypatch,
    dense_measurement_schedule,
    honest_dense_carrier_child,
):
    forged = copy.deepcopy(honest_dense_carrier_child)
    forged["claims_production_scalable_backend"] = True
    _rehash(forged)
    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )
    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError,
        "carrier",
        monkeypatch,
        dense_measurement_schedule,
        forged,
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            dense_measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options=None,
        )


def test_qt_carrier_rejects_rehashed_wrong_detector_xor_rows(
    monkeypatch,
    projected_measurement_schedule,
    honest_projected_qt_child,
):
    forged = copy.deepcopy(honest_projected_qt_child)
    forged["mps_execution"]["detector_records"] = [[1], [0]]
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, projected_measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            projected_measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_rehashed_wrong_logical_observable_names(
    monkeypatch,
    projected_measurement_schedule,
    honest_projected_qt_child,
):
    forged = copy.deepcopy(honest_projected_qt_child)
    forged["mps_execution"]["logical_observable_names"] = ["shadow_logical"]
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "qt", monkeypatch, projected_measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            projected_measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


def test_qt_carrier_rejects_type_inexact_projected_record_bits(
    monkeypatch,
    projected_measurement_schedule,
    honest_projected_qt_child,
):
    forged = copy.deepcopy(honest_projected_qt_child)
    forged["mps_execution"]["logical_observable_records"][1][0] = True
    _rehash(forged)
    monkeypatch.setattr(
        qt_execution,
        "axis1_qt_mps_restricted_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        TypeError, "qt", monkeypatch, projected_measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            projected_measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
            ),
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("detector_names", ["shadow_d0"]),
        (
            "logical_observable_records",
            [[1], [0]],
        ),
    ],
)
def test_mcwf_carrier_rejects_rehashed_projection_disagreement(
    monkeypatch,
    projected_measurement_schedule,
    honest_projected_mcwf_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_projected_mcwf_child)
    forged["mps_execution"][field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, projected_measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            projected_measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("measurement_sampling_policy", "legacy_full_binary_materialization"),
        ("record_support_policy", "full_binary_record_support"),
        ("zero_frequency_records_emitted", True),
        ("zero_frequency_records_emitted", 0),
    ],
    ids=["measurement_policy", "support_policy", "zero_flag", "zero_flag_type"],
)
def test_mcwf_carrier_binds_sparse_record_sampling_contract(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["mps_execution"]["trajectory_sampling"][field] = bad_value
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError, "mcwf", monkeypatch, measurement_schedule, forged
    ):
        axis1_carrier_execution_manifest(
            measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )

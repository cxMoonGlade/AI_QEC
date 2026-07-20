from __future__ import annotations

import copy
import hashlib
import json
from contextlib import contextmanager

import pytest

from error_coupling_simulator.certify.axis1_mps import (
    _mcwf_truncation_gate_result,
)
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
    *,
    match=None,
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

    with pytest.raises(expected_exception, match=match):
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
def ordered_xz_measurement_schedule():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.tick()
    builder.measure(0, key="mx", basis="X", reset=True)
    builder.measure(1, key="mz", basis="Z")
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
def honest_ordered_xz_mcwf_child(ordered_xz_measurement_schedule):
    return axis1_mcwf_mps_state_record_execution_manifest(
        ordered_xz_measurement_schedule,
        device="cuda",
        local_dims=[2, 2],
        initial_levels=[0, 0],
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
def honest_blocked_mcwf_carrier_child(measurement_schedule):
    return axis1_carrier_execution_manifest(
        measurement_schedule,
        device="cuda",
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


@pytest.fixture(scope="module")
def honest_ordered_xz_mcwf_carrier_child(ordered_xz_measurement_schedule):
    return axis1_carrier_execution_manifest(
        ordered_xz_measurement_schedule,
        device="cuda",
        execution_backend_contract=(
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        execution_backend_options={
            "local_dims": [2, 2],
            "initial_levels": [0, 0],
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
        (
            "finite_step_order",
            "symmetric_hamiltonian_first_order_collapse",
        ),
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
        (
            "finite_step_policy",
            "order",
            "symmetric_hamiltonian_first_order_collapse",
        ),
        ("finite_step_policy", "microstep_count", 2),
        (
            "multilevel_measurement_policy",
            "leaked_readout_b",
            0.5,
        ),
        (
            "multilevel_measurement_policy",
            "name",
            "computational_level_sample_then_binary_record",
        ),
        (
            "multilevel_measurement_policy",
            "bit_mapping",
            "level_0_to_bit_0_level_1_to_bit_1",
        ),
        (None, "claims_b8_artifact", True),
        (None, "claims_decoder_integration", True),
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
def test_mcwf_carrier_rejects_rehashed_ordered_measurement_semantics_drift(
    monkeypatch,
    ordered_xz_measurement_schedule,
    honest_ordered_xz_mcwf_child,
    field,
    reordered_value,
):
    forged = copy.deepcopy(honest_ordered_xz_mcwf_child)
    forged["mps_execution"][field] = reordered_value
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError,
        "mcwf",
        monkeypatch,
        ordered_xz_measurement_schedule,
        forged,
    ):
        axis1_carrier_execution_manifest(
            ordered_xz_measurement_schedule,
            execution_backend_contract=(
                AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
            ),
            execution_backend_options={
                "local_dims": [2, 2],
                "initial_levels": [0, 0],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_mcwf_carrier_forwards_ordered_measurement_semantics(
    honest_ordered_xz_mcwf_carrier_child,
):
    record_execution = honest_ordered_xz_mcwf_carrier_child["record_execution"]

    assert record_execution["measurement_keys"] == ["mx", "mz"]
    assert record_execution["measurement_targets"] == [0, 1]
    assert record_execution["measurement_bases"] == ["X", "Z"]
    assert record_execution["reset_after"] == [True, False]
    assert record_execution["measurement_basis"] == "mixed_pauli"
    assert record_execution["measurement_basis_semantics"] == (
        "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
        "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
    )
    assert record_execution["multilevel_measurement_policy"]["name"] == (
        "declared_basis_eigenlabel_sample_then_binary_record"
    )
    assert honest_ordered_xz_mcwf_carrier_child["state_execution"][
        "initial_levels"
    ] == [0, 0]
    assert "evaluator_only_diagnostics" not in record_execution
    artifact = honest_ordered_xz_mcwf_carrier_child[
        "dynamics_artifact_reference_certification"
    ]
    assert artifact["passed"] is True
    assert artifact["post_execution_integrity_verified"] is True
    assert honest_ordered_xz_mcwf_carrier_child[
        "restricted_acceptance_policy"
    ]["dynamics_artifact_reference_certification"] == artifact
    assert honest_ordered_xz_mcwf_carrier_child["mcwf_mps_execution"][
        "dynamics_artifact_reference_certification"
    ] == artifact


def test_mcwf_carrier_explicit_none_mass_budget_returns_diagnostic_manifest(
    measurement_schedule,
):
    manifest = axis1_carrier_execution_manifest(
        measurement_schedule,
        device="cuda",
        execution_backend_contract=(
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        execution_backend_options={
            "local_dims": [3],
            "initial_levels": [0],
            "mass_residual_budget": None,
            "trajectory_count": 4,
            "rng_seed": 17,
        },
    )

    assert manifest["record_execution"]["executed"] is True
    assert manifest["passed"] is False
    assert manifest["diagnostic_only"] is True
    policy = manifest["restricted_acceptance_policy"]
    assert policy["certification_status"] == "not_evaluated"
    assert policy["probability"]["runtime_candidate_mass_residual_budget"] is None
    assert "mass_residual_budget_not_declared_diagnostic_only" in policy[
        "production_blockers"
    ]


def test_mcwf_carrier_rejects_rehashed_unknown_direct_child_field(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged["shadow_field"] = "forged"
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError,
        "mcwf",
        monkeypatch,
        measurement_schedule,
        forged,
        match="fields must be exact",
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


def test_mcwf_carrier_rejects_all_rehashed_direct_packet_mirrors(
    monkeypatch,
    measurement_schedule,
    honest_multilevel_mcwf_child,
):
    forged = copy.deepcopy(honest_multilevel_mcwf_child)
    forged_packet = copy.deepcopy(
        forged["dynamics_artifact_reference_certification"]
    )
    forged_packet["reference_operator_source_sha256"] = "0" * 64
    _rehash(forged_packet)
    forged["dynamics_artifact_reference_certification"] = copy.deepcopy(
        forged_packet
    )
    forged["restricted_acceptance_policy"][
        "dynamics_artifact_reference_certification"
    ] = copy.deepcopy(forged_packet)
    _rehash(forged)
    monkeypatch.setattr(
        mcwf_execution,
        "axis1_mcwf_mps_state_record_execution_manifest",
        lambda *_args, **_kwargs: forged,
    )

    with _rejects_forged_child_without_mutation(
        ValueError,
        "mcwf",
        monkeypatch,
        measurement_schedule,
        forged,
        match="sealed-input authority",
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


def test_mcwf_carrier_treats_explicit_none_dimensions_as_defaults(
    measurement_schedule,
):
    manifest = axis1_carrier_execution_manifest(
        measurement_schedule,
        execution_backend_contract=(
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        execution_backend_options={
            "local_dims": None,
            "initial_levels": None,
            "trajectory_count": 2,
            "rng_seed": 17,
        },
    )

    assert manifest["mcwf_mps_backend_executed"] is True
    assert manifest["local_hilbert_space"]["local_dims"] == [2]
    assert manifest["state_execution"]["initial_levels"] == [0]


def test_mcwf_carrier_rejects_rehashed_blocked_policy_payload_drift(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged["restricted_acceptance_policy"]["production_blockers"].append(
        "forged_blocker"
    )
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


def test_mcwf_carrier_rejects_self_consistent_forged_block_reason(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged["blocked_reason"] = "forged_block_reason"
    policy = forged["restricted_acceptance_policy"]
    policy["blocked_reason"] = "forged_block_reason"
    policy["production_blockers"][0] = "forged_block_reason"
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


def test_mcwf_carrier_rejects_rehashed_blocked_execution_claim_payload(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_child,
):
    forged = copy.deepcopy(honest_mcwf_child)
    forged["mps_execution"] = {
        "claims_b8_artifact": 1,
        "claims_decoder_integration": "truthy",
    }
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


@pytest.mark.parametrize(
    ("fixture_name", "options", "expected_passed"),
    [
        (
            "honest_mcwf_carrier_child",
            {
                "local_dims": [3],
                "initial_levels": [2],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
            True,
        ),
        (
            "honest_blocked_mcwf_carrier_child",
            {
                "local_dims": [3],
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
            False,
        ),
    ],
)
def test_auto_router_accepts_honest_mcwf_child(
    monkeypatch,
    request,
    measurement_schedule,
    fixture_name,
    options,
    expected_passed,
):
    honest = copy.deepcopy(request.getfixturevalue(fixture_name))
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
        lambda *_args, **_kwargs: honest,
    )

    manifest = carrier_execution._axis1_auto_routed_execution_manifest(
        measurement_schedule,
        device="cuda",
        instrument_spec=None,
        execution_backend_options=options,
    )

    assert manifest["resolved_backend_contract"] == (
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    )
    assert manifest["passed"] is expected_passed
    assert manifest["execution"] == honest


def test_auto_router_accepts_honest_ordered_xz_mcwf_child(
    monkeypatch,
    ordered_xz_measurement_schedule,
    honest_ordered_xz_mcwf_carrier_child,
):
    honest = copy.deepcopy(honest_ordered_xz_mcwf_carrier_child)
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
        lambda *_args, **_kwargs: honest,
    )

    manifest = carrier_execution._axis1_auto_routed_execution_manifest(
        ordered_xz_measurement_schedule,
        device="cuda",
        instrument_spec=None,
        execution_backend_options={
            "local_dims": [2, 2],
            "initial_levels": [0, 0],
            "trajectory_count": 4,
            "rng_seed": 17,
        },
    )

    record = manifest["execution"]["record_execution"]
    assert manifest["passed"] is True
    assert record["executed"] is True
    assert record["measurement_bases"] == ["X", "Z"]
    assert record["reset_after"] == [True, False]
    assert record["measurement_basis"] == "mixed_pauli"


def test_public_auto_router_executes_real_ordered_xz_mcwf_child(
    monkeypatch,
    ordered_xz_measurement_schedule,
):
    """Public auto routing must preserve real MCWF X/Z/reset Record semantics."""

    monkeypatch.setattr(
        carrier_execution,
        "_available_vram_bytes",
        lambda _device: 0.0,
    )
    manifest = axis1_carrier_execution_manifest(
        ordered_xz_measurement_schedule,
        device="cuda",
        execution_backend_contract=(
            carrier_execution.AXIS1_CARRIER_AUTO_BACKEND_CONTRACT
        ),
        execution_backend_options={
            "local_dims": [2, 2],
            "initial_levels": [0, 0],
            "trajectory_count": 8,
            "rng_seed": 2307,
        },
    )

    assert manifest["resolved_backend_contract"] == (
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    )
    assert manifest["passed"] is True
    assert manifest["auto_routing"]["route_reasons"] == [
        "invalid_available_vram_bytes"
    ]
    child = manifest["execution"]
    assert child["passed"] is True
    artifact = manifest["dynamics_artifact_reference_certification"]
    assert artifact == child["dynamics_artifact_reference_certification"]
    assert artifact == child["restricted_acceptance_policy"][
        "dynamics_artifact_reference_certification"
    ]
    assert artifact == child["mcwf_mps_execution"][
        "dynamics_artifact_reference_certification"
    ]
    assert artifact["passed"] is True
    assert artifact["post_execution_integrity_verified"] is True
    record = child["record_execution"]
    assert record["executed"] is True
    assert record["measurement_basis"] == "mixed_pauli"
    assert record["measurement_bases"] == ["X", "Z"]
    assert record["reset_after"] == [True, False]
    assert record["measurement_records"] == [[0, 0]]
    assert record["record_counts"] == [8]
    assert record["record_probabilities"] == [1.0]


def test_auto_router_rejects_all_rehashed_artifact_packet_mirrors(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    """Outer auth must rebuild authority, not trust mutually consistent mirrors."""

    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged_packet = copy.deepcopy(
        forged["dynamics_artifact_reference_certification"]
    )
    forged_packet["carrier_operator_source_sha256"] = "f" * 64
    _rehash(forged_packet)
    forged["dynamics_artifact_reference_certification"] = copy.deepcopy(
        forged_packet
    )
    forged["restricted_acceptance_policy"][
        "dynamics_artifact_reference_certification"
    ] = copy.deepcopy(forged_packet)
    forged["mcwf_mps_execution"][
        "dynamics_artifact_reference_certification"
    ] = copy.deepcopy(forged_packet)
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
        ValueError,
        "carrier",
        monkeypatch,
        measurement_schedule,
        forged,
        match="sealed-input authority",
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
        ("schema", "error_coupling_simulator.frontend.carrier_execution.v4"),
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
    ("field", "bad_value"),
    [
        ("measurement_keys", ["mz", "mx"]),
        ("measurement_targets", [1, 0]),
        ("measurement_bases", ["Z", "X"]),
        ("reset_after", [False, True]),
        ("measurement_records", [[0]]),
        ("evaluator_only_diagnostics", {"level_records": [[0, 0]]}),
        ("level_records", [[0, 0]]),
        ("level_record_counts", [4]),
    ],
)
def test_auto_router_rejects_rehashed_mcwf_record_layout_drift(
    monkeypatch,
    ordered_xz_measurement_schedule,
    honest_ordered_xz_mcwf_carrier_child,
    field,
    bad_value,
):
    forged = copy.deepcopy(honest_ordered_xz_mcwf_carrier_child)
    forged["record_execution"][field] = bad_value
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
        ValueError,
        "carrier",
        monkeypatch,
        ordered_xz_measurement_schedule,
        forged,
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            ordered_xz_measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [2, 2],
                "initial_levels": [0, 0],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_rejects_rehashed_duplicate_mcwf_histogram_rows(
    monkeypatch,
    ordered_xz_measurement_schedule,
    honest_ordered_xz_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_ordered_xz_mcwf_carrier_child)
    record = forged["record_execution"]
    row = list(record["measurement_records"][0])
    record["measurement_records"] = [row, list(row)]
    record["record_counts"] = [2, 2]
    record["record_probabilities"] = [0.5, 0.5]
    record["detector_records"] = [[], []]
    record["logical_observable_records"] = [[], []]
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
        ValueError,
        "carrier",
        monkeypatch,
        ordered_xz_measurement_schedule,
        forged,
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            ordered_xz_measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [2, 2],
                "initial_levels": [0, 0],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_rejects_self_consistent_histogram_not_emitted_by_direct(
    monkeypatch,
    ordered_xz_measurement_schedule,
    honest_ordered_xz_mcwf_carrier_child,
):
    """A valid histogram shape must still be bound to the seeded direct run."""

    forged = copy.deepcopy(honest_ordered_xz_mcwf_carrier_child)
    record = forged["record_execution"]
    honest_row = list(record["measurement_records"][0])
    record["measurement_records"] = [
        [1 - int(bit) for bit in honest_row]
    ]
    record["record_counts"] = [4]
    record["record_probabilities"] = [1.0]
    record["detector_records"] = [[]]
    record["logical_observable_records"] = [[]]
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
        ValueError,
        "carrier",
        monkeypatch,
        ordered_xz_measurement_schedule,
        forged,
        match="seeded direct MCWF execution",
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            ordered_xz_measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [2, 2],
                "initial_levels": [0, 0],
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


@pytest.mark.parametrize(
    ("path", "bad_value"),
    [
        (("restricted_acceptance_policy", "schema"),
         "error_coupling_simulator.frontend.mcwf_mps_restricted_acceptance_policy.v6"),
        (("restricted_acceptance_policy", "accepted_for_production_scalable_backend"), True),
        (("restricted_acceptance_policy", "probability",
          "runtime_candidate_mass_residual_budget"), 0.2),
        (("restricted_acceptance_policy", "mps_truncation", "gate",
          "worst_cut_discarded_weight_gate"), 0.1),
        (("execution_status",), "failed"),
        (("execution_backend_options", "rng_seed"), 18),
        (("record_execution", "trajectory_sampling", "rng_seed"), 18),
        (("local_hilbert_space", "local_dims"), [2]),
        (("record_execution", "claims_b8_artifact"), True),
        (("record_execution", "multilevel_measurement_policy", "name"),
         "computational_level_sample_then_binary_record"),
        (("state_execution", "initial_levels"), [1]),
        (("mcwf_mps_execution", "claims_production_scalable_backend"), True),
        (("state_execution", "evidence_schema"), "forged_schema"),
        (("mcwf_mps_execution", "schema"),
         "error_coupling_simulator.frontend.mcwf_mps_state_record_execution.v7"),
        (("mcwf_mps_execution", "content_hash"), "f" * 64),
        (("state_execution", "evidence_content_hash"), "e" * 64),
        (("state_execution", "level_records"), [[2]]),
        (("evaluator_only_diagnostics",), {"level_records": [[2]]}),
        (("record_execution", "shadow_payload"), {"ok": True}),
        (("shadow_field",), 1),
    ],
)
def test_auto_router_rejects_rehashed_mcwf_policy_and_provenance_drift(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
    path,
    bad_value,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    target = forged
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = bad_value
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
    "path",
    [
        ("record_execution", "trajectory_sampling", "shadow_field"),
        ("state_execution", "finite_step_policy", "shadow_field"),
        ("state_execution", "mps_truncation_ledger", "shadow_field"),
        ("restricted_acceptance_policy", "shadow_field"),
        (
            "restricted_acceptance_policy",
            "gross_strict_gate_split",
            "shadow_field",
        ),
        (
            "restricted_acceptance_policy",
            "dense_jointL_record_certification",
            "shadow_field",
        ),
        (
            "restricted_acceptance_policy",
            "dense_jointL_record_certification",
            "component_values",
            "shadow_field",
        ),
        ("restricted_acceptance_policy", "trajectory", "shadow_field"),
        ("restricted_acceptance_policy", "finite_step", "shadow_field"),
        ("restricted_acceptance_policy", "mps_truncation", "shadow_field"),
        ("restricted_acceptance_policy", "probability", "shadow_field"),
    ],
)
def test_auto_router_rejects_unknown_nested_mcwf_fields(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
    path,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    target = forged
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = "forged"
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
        ValueError,
        "carrier",
        monkeypatch,
        measurement_schedule,
        forged,
        match="fields must be exact",
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


def test_auto_router_binds_self_consistent_sampling_provenance_to_request(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged["execution_backend_options"]["rng_seed"] = 18
    forged["record_execution"]["trajectory_sampling"]["rng_seed"] = 18
    forged["restricted_acceptance_policy"]["trajectory"]["rng_seed"] = 18
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


def test_auto_router_rejects_self_consistent_false_green_runtime_mass_policy(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged["record_execution"]["jump_sampling"][
        "probability_mass_residual_max"
    ] = 0.5
    probability = forged["restricted_acceptance_policy"]["probability"]
    probability["runtime_candidate_mass_residual"] = 0.5
    probability["runtime_candidate_mass_residual_within_budget"] = True
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


def test_auto_router_rejects_self_consistent_uncapped_truncation_loss(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    ledger = forged["state_execution"]["mps_truncation_ledger"]
    ledger["discarded_weight_sum"] = 0.2
    ledger["worst_cut_discarded_weight"] = 0.2
    ledger["n_truncating_ops"] = 1
    truncation = forged["restricted_acceptance_policy"]["mps_truncation"]
    truncation["discarded_weight_sum"] = 0.2
    truncation["worst_cut_discarded_weight"] = 0.2
    truncation["truncation_detected"] = True
    truncation["gate"] = _mcwf_truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=None,
        total_discarded_weight_gate=None,
    )
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
        ValueError,
        "carrier",
        monkeypatch,
        measurement_schedule,
        forged,
        match="uncapped MCWF Carrier cannot report truncation loss",
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


def test_auto_router_freezes_canonical_options_before_delegation(
    monkeypatch,
    measurement_schedule,
    honest_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_mcwf_carrier_child)
    forged["execution_backend_options"]["rng_seed"] = 18
    forged["record_execution"]["trajectory_sampling"]["rng_seed"] = 18
    forged["restricted_acceptance_policy"]["trajectory"]["rng_seed"] = 18
    _rehash(forged)

    monkeypatch.setattr(
        carrier_execution,
        "_select_dense_or_mcwf",
        lambda *_args: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
            {"schema": "test_auto_routing_decision"},
        ),
    )

    def mutate_delegated_options(*_args, **kwargs):
        kwargs["execution_backend_options"]["rng_seed"] = 18
        return forged

    monkeypatch.setattr(
        carrier_execution,
        "axis1_carrier_execution_manifest",
        mutate_delegated_options,
    )

    with pytest.raises(ValueError):
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


def test_auto_router_rejects_rehashed_blocked_mcwf_policy_payload(
    monkeypatch,
    measurement_schedule,
    honest_blocked_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_blocked_mcwf_carrier_child)
    forged["restricted_acceptance_policy"]["production_blockers"].append(
        "forged_blocker"
    )
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
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_rejects_self_consistent_forged_block_reason(
    monkeypatch,
    measurement_schedule,
    honest_blocked_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_blocked_mcwf_carrier_child)
    forged_reason = "forged_but_self_consistent_block"
    forged["blocked_reason"] = forged_reason
    forged["state_execution"]["reason"] = forged_reason
    forged["record_execution"]["reason"] = forged_reason
    policy = forged["restricted_acceptance_policy"]
    policy["blocked_reason"] = forged_reason
    policy["production_blockers"][0] = forged_reason
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
        ValueError,
        "carrier",
        monkeypatch,
        measurement_schedule,
        forged,
        match="blocked_reason must match trusted preflight",
    ):
        carrier_execution._axis1_auto_routed_execution_manifest(
            measurement_schedule,
            device="cuda",
            instrument_spec=None,
            execution_backend_options={
                "local_dims": [3],
                "max_bond": 2,
                "trajectory_count": 4,
                "rng_seed": 17,
            },
        )


def test_auto_router_rejects_rehashed_blocked_mcwf_record_payload(
    monkeypatch,
    measurement_schedule,
    honest_blocked_mcwf_carrier_child,
):
    forged = copy.deepcopy(honest_blocked_mcwf_carrier_child)
    forged["record_execution"]["measurement_records"] = [[1]]
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
                "max_bond": 2,
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

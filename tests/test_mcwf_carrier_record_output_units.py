from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from error_coupling_simulator.carrier.records import RecordBatch
from error_coupling_simulator.frontend import CircuitBuilder
from error_coupling_simulator.frontend import axis1_carrier_execution as carrier_execution
from error_coupling_simulator.frontend import axis1_mcwf_mps_execution as mcwf_execution
from error_coupling_simulator.frontend import circuit_ir_to_substep_schedule


_BACKEND_OPTIONS = {
    "local_dims": [2, 2],
    "initial_levels": [0, 0],
    "trajectory_count": 4,
    "rng_seed": 17,
}
_DIRECT_SCHEMA = (
    "error_coupling_simulator.frontend.mcwf_mps_state_record_execution.v8"
)
_DIRECT_HASH = "d" * 64
_MATERIALIZATION_ORDER = "carrier_histogram_grouped_canonical_support_order"
_UNIT_RUNTIME_IDENTITY = {
    "cuda_visible_devices": "0",
    "logical_device_index": 0,
    "gpu_name": "unit-test-gpu",
    "gpu_uuid": "GPU-unit-test",
    "pci_bus_id": 1,
    "compute_capability": [12, 0],
    "total_memory_bytes": 1024,
    "torch_cuda_build_version": "13.0",
    "loaded_cuda_runtime_version": None,
    "loaded_cuda_runtime_version_status": "not_attested",
    "cudnn_runtime": 99999,
    "nvidia_driver": "999.0.0",
}
_UNIT_BUILD_IDENTITY = {
    "schema": "error_coupling_simulator.carrier.package_build_identity.v1",
    "distribution": "error-coupling-simulator",
    "version": "0+unit-test",
    "package_tree_sha256": "b" * 64,
    "git_commit": "unit-test",
}
_UNIT_SOURCE_IDENTITY = {
    "module": "error_coupling_simulator.frontend.axis1_carrier_execution",
    "package_relative_file": "frontend/axis1_carrier_execution.py",
    "resolved_import_origin": (
        "/unit-test/error_coupling_simulator/frontend/axis1_carrier_execution.py"
    ),
    "sha256": "5" * 64,
}
_REAL_MCWF_RECORD_BUILD_IDENTITY = carrier_execution._mcwf_record_build_identity
_REAL_MCWF_RECORD_SOURCE_IDENTITY = (
    carrier_execution._mcwf_record_source_implementation_identity
)
_REAL_MCWF_RECORD_RUNTIME_IDENTITY = carrier_execution._mcwf_record_runtime_identity
_PROVENANCE_FIELDS = {
    "backend",
    "representability",
    "record_semantics",
    "source_kind",
    "source_hash",
    "carrier_execution_schema",
    "carrier_execution_content_hash",
    "direct_execution_schema",
    "direct_execution_content_hash",
    "restricted_acceptance_policy_content_hash",
    "measurement_keys",
    "measurement_targets",
    "measurement_bases",
    "reset_after",
    "measurement_basis",
    "record_layout_schema",
    "record_layout_content_hash",
    "detector_names",
    "observable_names",
    "detector_xor_columns",
    "observable_xor_columns",
    "trajectory_count",
    "rng_seed",
    "device",
    "local_dims",
    "initial_levels",
    "microstep_count",
    "finite_step_order",
    "mass_residual_budget",
    "max_bond",
    "worst_cut_discarded_weight_gate",
    "total_discarded_weight_gate",
    "leaked_readout_b",
    "state_dtype",
    "record_dtype",
    "estimated_peak_record_array_payload_bytes",
    "max_record_array_payload_bytes",
    "estimated_record_support_upper_bound",
    "estimated_record_support_cells",
    "max_record_support_cells",
    "execution_status",
    "certification_status",
    "diagnostic_only",
    "accepted_for_restricted_execution",
    "materialization_order",
    "original_trajectory_order_preserved",
}


@pytest.fixture(autouse=True)
def _stub_record_publication_runtime_identity(monkeypatch) -> None:
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_runtime_identity",
        lambda _device: copy.deepcopy(_UNIT_RUNTIME_IDENTITY),
        raising=False,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_build_identity",
        lambda: copy.deepcopy(_UNIT_BUILD_IDENTITY),
        raising=False,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_source_implementation_identity",
        lambda: copy.deepcopy(_UNIT_SOURCE_IDENTITY),
        raising=False,
    )


@pytest.fixture()
def projected_xz_schedule():
    builder = CircuitBuilder(num_qubits=2)
    builder.measure(0, key="mx", basis="X", reset=True)
    builder.measure(1, key="mz", basis="Z")
    builder.detector("parity", xor=("mx", "mz"))
    builder.detector("z_copy", xor=("mz",))
    builder.observable("logical_x", xor=("mx",), index=0)
    return circuit_ir_to_substep_schedule(builder.build())


def _stable_hash(payload: dict[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    encoded = json.dumps(
        without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _rehash(payload: dict[str, Any]) -> dict[str, Any]:
    payload["content_hash"] = _stable_hash(payload)
    return payload


def _accepted_carrier(schedule) -> dict[str, Any]:
    program = carrier_execution.axis1_carrier_program_manifest(
        schedule,
        backend_contract=(
            carrier_execution.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
    )
    record_execution = {
        "executed": True,
        "reason": None,
        "measurement_keys": ["mx", "mz"],
        "measurement_targets": [0, 1],
        "measurement_bases": ["X", "Z"],
        "reset_after": [True, False],
        "measurement_basis": "mixed_pauli",
        "measurement_basis_semantics": (
            "measurement_bases and reset_after are schedule-ordered "
            "one-per-Record-column; X measurement rotates into Z, projects, "
            "then rotates back unless reset prepares |+>"
        ),
        "multilevel_measurement_policy": {},
        # Canonical sorted unique empirical support. Counts, not probabilities,
        # are the materialization authority.
        "measurement_records": [[0, 0], [0, 1], [1, 0]],
        "record_counts": [2, 1, 1],
        "record_probabilities": [0.5, 0.25, 0.25],
        # These are already compiler-sealed XOR projections. They are not raw
        # round-major syndromes and must never pass through s_to_det.
        "detector_records": [[0, 0], [1, 1], [1, 0]],
        "logical_observable_records": [[0], [0], [1]],
        "trajectory_sampling": {
            "mode": "sampled_fixed_microstep_mcwf_trajectories",
            "trajectory_count": 4,
            "rng_seed": 17,
        },
        "jump_sampling": {},
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
    }
    carrier = {
        "schema": carrier_execution.AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": (
            carrier_execution.AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY
        ),
        "execution_backend_contract": (
            carrier_execution.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        "gpu_required": True,
        "device": "cuda",
        "execution_backend_options": copy.deepcopy(_BACKEND_OPTIONS),
        "execution_status": "completed",
        "certification_status": "accepted",
        "diagnostic_only": False,
        "verdict": "pass",
        "passed": True,
        "blocked_reason": None,
        "dense_probe_executed": False,
        "qt_mps_backend_executed": False,
        "mcwf_mps_backend_executed": True,
        "qutip_cuquantum_probe_executed": False,
        "carrier_program": carrier_execution._restricted_mps_program_summary(
            program
        ),
        "local_hilbert_space": {},
        "state_execution": {},
        "record_execution": record_execution,
        "mcwf_mps_execution": {
            "schema": _DIRECT_SCHEMA,
            "content_hash": _DIRECT_HASH,
            "execution_status": "completed",
            "certification_status": "accepted",
            "diagnostic_only": False,
            "passed": True,
            "mcwf_mps_backend_executed": True,
        },
        "dynamics_artifact_reference_certification": {},
        "restricted_acceptance_policy": {
            "accepted_for_restricted_execution": True,
        },
        "claims_mcwf_mps_backend_execution": True,
        "claims_qt_mps_backend_execution": False,
        "claims_qutip_cuquantum_execution": False,
        "claims_production_scalable_backend": False,
        "claims_scalable_backend_completed": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": "no new scored quantity",
        "epistemic_classes": {},
        "scope": "unit fixture for authenticated Record materialization",
    }
    return _rehash(carrier)


def _authority(
    carrier: dict[str, Any],
    *,
    direct_content_hash: str | None = None,
    record_execution_content_hash: str | None = None,
    policy_content_hash: str | None = None,
):
    direct = carrier.get("mcwf_mps_execution")
    record_execution = carrier.get("record_execution")
    policy = carrier.get("restricted_acceptance_policy")
    return carrier_execution._Axis1McwfMpsRecordBinding(
        carrier_content_hash=carrier["content_hash"],
        direct_content_hash=(
            direct.get("content_hash")
            if direct_content_hash is None and isinstance(direct, dict)
            else direct_content_hash
        ),
        record_execution_content_hash=(
            carrier_execution._stable_payload_hash(
                {"record_execution": record_execution}
            )
            if record_execution_content_hash is None
            else record_execution_content_hash
        ),
        restricted_acceptance_policy_content_hash=(
            carrier_execution._stable_payload_hash(
                {"policy": policy}
            )
            if policy_content_hash is None
            else policy_content_hash
        ),
    )


def _produced(carrier: dict[str, Any]):
    child = copy.deepcopy(carrier)
    return child, _authority(child)


def _materialize(
    carrier: dict[str, Any],
    schedule,
    *,
    cap: int,
    binding=None,
    options: dict[str, Any] | None = None,
) -> RecordBatch:
    requested_options = copy.deepcopy(_BACKEND_OPTIONS if options is None else options)
    preflight = carrier_execution._preflight_mcwf_record_materialization(
        schedule,
        device="cuda",
        execution_backend_options=requested_options,
        max_record_array_payload_bytes=cap,
    )
    return carrier_execution._materialize_mcwf_carrier_record_batch(
        carrier,
        preflight=preflight,
        binding=_authority(carrier) if binding is None else binding,
    )


def _zero_width_case(projection: str):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0", basis="Z")
    if projection == "detector":
        builder.detector("d0", xor=("m0",))
    else:
        builder.observable("l0", xor=("m0",), index=0)
    schedule = circuit_ir_to_substep_schedule(builder.build())
    options = {
        "local_dims": [2],
        "initial_levels": [0],
        "trajectory_count": 4,
        "rng_seed": 17,
    }
    carrier = _accepted_carrier(schedule)
    carrier["execution_backend_options"] = copy.deepcopy(options)
    record = carrier["record_execution"]
    record.update(
        {
            "measurement_keys": ["m0"],
            "measurement_targets": [0],
            "measurement_bases": ["Z"],
            "reset_after": [False],
            "measurement_basis": "Z",
            "measurement_records": [[0], [1]],
            "record_counts": [2, 2],
            "record_probabilities": [0.5, 0.5],
            "detector_records": (
                [[0], [1]] if projection == "detector" else [[], []]
            ),
            "logical_observable_records": (
                [[], []] if projection == "detector" else [[0], [1]]
            ),
        }
    )
    _rehash(carrier)
    return schedule, options, carrier


def test_record_preflight_rejects_rehashed_program_mutation_before_cuda(
    monkeypatch,
    projected_xz_schedule,
):
    preflight = carrier_execution._preflight_mcwf_record_materialization(
        projected_xz_schedule,
        device="cuda",
        execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
        max_record_array_payload_bytes=48,
    )
    sealed_content_hash = preflight.carrier_program_content_hash
    preflight.carrier_program["scope"] = "mutated_after_record_preflight"
    _rehash(preflight.carrier_program)
    cuda_checks = []
    monkeypatch.setattr(
        mcwf_execution,
        "_require_cuda_device",
        lambda device: cuda_checks.append(device),
    )

    with pytest.raises(
        ValueError,
        match="declared content hash changed after compile",
    ):
        carrier_execution._execute_mcwf_carrier_record_batch(
            projected_xz_schedule,
            preflight=preflight,
        )

    assert preflight.carrier_program_content_hash == sealed_content_hash
    assert cuda_checks == []


def test_record_path_rechecks_program_after_delegated_carrier(
    monkeypatch,
    projected_xz_schedule,
):
    preflight = carrier_execution._preflight_mcwf_record_materialization(
        projected_xz_schedule,
        device="cuda",
        execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
        max_record_array_payload_bytes=48,
    )
    forged = _accepted_carrier(projected_xz_schedule)

    def mutate_program_and_return_carrier(*_args, **kwargs):
        program = kwargs["precompiled_program"]
        program["scope"] = "mutated_by_record_delegated_carrier"
        _rehash(program)
        return _produced(forged)

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        mutate_program_and_return_carrier,
    )

    with pytest.raises(
        ValueError,
        match="declared content hash changed after compile",
    ):
        carrier_execution._execute_mcwf_carrier_record_batch(
            projected_xz_schedule,
            preflight=preflight,
        )


def test_record_path_rechecks_program_after_materialization(
    monkeypatch,
    projected_xz_schedule,
):
    preflight = carrier_execution._preflight_mcwf_record_materialization(
        projected_xz_schedule,
        device="cuda",
        execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
        max_record_array_payload_bytes=48,
    )
    forged = _accepted_carrier(projected_xz_schedule)
    original_materialize = carrier_execution._materialize_mcwf_carrier_record_batch

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(forged),
    )

    def mutate_program_after_materialization(*args, **kwargs):
        record_batch = original_materialize(*args, **kwargs)
        preflight.carrier_program["scope"] = "mutated_during_record_materialization"
        _rehash(preflight.carrier_program)
        return record_batch

    monkeypatch.setattr(
        carrier_execution,
        "_materialize_mcwf_carrier_record_batch",
        mutate_program_after_materialization,
    )

    with pytest.raises(
        ValueError,
        match="declared content hash changed after compile",
    ):
        carrier_execution._execute_mcwf_carrier_record_batch(
            projected_xz_schedule,
            preflight=preflight,
        )


def test_materializes_grouped_sealed_xz_projection_as_immutable_record_batch(
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    # 4 * shots * (detector_width + observable_width) = 4 * 4 * 3 = 48.
    record = _materialize(carrier, projected_xz_schedule, cap=48)

    assert isinstance(record, RecordBatch)
    np.testing.assert_array_equal(
        record.det,
        [[0, 0], [0, 0], [1, 1], [1, 0]],
    )
    np.testing.assert_array_equal(record.obs, [[0], [0], [0], [1]])
    assert record.det.dtype == np.uint8
    assert record.obs.dtype == np.uint8
    assert record.det.flags.c_contiguous and not record.det.flags.writeable
    assert record.obs.flags.c_contiguous and not record.obs.flags.writeable

    provenance = dict(record.provenance)
    assert set(provenance) == _PROVENANCE_FIELDS
    assert provenance["backend"] == (
        carrier_execution.AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    )
    assert provenance["representability"] == (
        carrier_execution.AXIS1_MCWF_MPS_RECORD_OUTPUT_REPRESENTABILITY
    )
    assert provenance["measurement_keys"] == ["mx", "mz"]
    assert provenance["measurement_targets"] == [0, 1]
    assert provenance["measurement_bases"] == ["X", "Z"]
    assert provenance["reset_after"] == [True, False]
    assert provenance["measurement_basis"] == "mixed_pauli"
    assert provenance["trajectory_count"] == 4
    assert provenance["execution_status"] == "completed"
    assert provenance["certification_status"] == "accepted"
    assert provenance["diagnostic_only"] is False
    assert provenance["accepted_for_restricted_execution"] is True
    assert provenance["direct_execution_schema"] == _DIRECT_SCHEMA
    assert provenance["direct_execution_content_hash"] == _DIRECT_HASH
    assert provenance["materialization_order"] == _MATERIALIZATION_ORDER
    assert provenance["original_trajectory_order_preserved"] is False
    assert provenance["detector_names"] == ["parity", "z_copy"]
    assert provenance["observable_names"] == ["logical_x"]
    assert provenance["detector_xor_columns"] == [[0, 1], [1]]
    assert provenance["observable_xor_columns"] == [[0]]
    assert len(provenance["record_layout_content_hash"]) == 64
    assert provenance["estimated_peak_record_array_payload_bytes"] == 48
    assert provenance["max_record_array_payload_bytes"] == 48
    assert provenance["mass_residual_budget"] == 0.1
    assert provenance["max_bond"] is None
    assert provenance["worst_cut_discarded_weight_gate"] is None
    assert provenance["total_discarded_weight_gate"] is None
    assert provenance["leaked_readout_b"] == 1.0
    assert provenance["estimated_record_support_upper_bound"] == 4
    assert provenance["estimated_record_support_cells"] > 0
    assert provenance["max_record_support_cells"] > 0
    assert "evaluator" not in json.dumps(provenance, sort_keys=True).lower()


def test_materialization_cap_rejects_before_output_allocation(
    monkeypatch,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)

    def forbidden_empty(*_args, **_kwargs):
        raise AssertionError("output allocation ran before the materialization cap")

    monkeypatch.setattr(np, "empty", forbidden_empty)
    with pytest.raises((TypeError, ValueError), match="materializ|byte|cap"):
        _materialize(carrier, projected_xz_schedule, cap=47)


def test_public_materialization_preflights_cap_before_mcwf_execution(
    monkeypatch,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran before the allocation preflight")

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    with pytest.raises(ValueError, match="materializ|byte|budget"):
        carrier_execution.axis1_mcwf_mps_record_batch(
            projected_xz_schedule,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=47,
        )
    assert calls == 0


def test_public_materialization_preflights_support_cells_before_mcwf_execution(
    monkeypatch,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran before the support-cell preflight")

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    with pytest.raises(ValueError, match="support|cell|budget"):
        carrier_execution.axis1_mcwf_mps_record_batch(
            projected_xz_schedule,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
            max_record_support_cells=1,
        )
    assert calls == 0


def test_materializer_rejects_unaccepted_evidence_before_expansion(
    monkeypatch,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    carrier.update(
        {
            "execution_status": "completed",
            "certification_status": "rejected",
            "diagnostic_only": False,
            "verdict": "fail",
            "passed": False,
            "blocked_reason": None,
        }
    )
    carrier["restricted_acceptance_policy"][
        "accepted_for_restricted_execution"
    ] = False
    carrier["mcwf_mps_execution"].update(
        {
            "execution_status": "completed",
            "certification_status": "rejected",
            "diagnostic_only": False,
            "passed": False,
        }
    )
    _rehash(carrier)

    def forbidden_repeat(*_args, **_kwargs):
        raise AssertionError("unaccepted evidence reached expansion")

    monkeypatch.setattr(np, "repeat", forbidden_repeat)
    with pytest.raises(ValueError, match="accepted|pass|certification"):
        _materialize(carrier, projected_xz_schedule, cap=48)


def test_materializer_rejects_rehashed_self_consistent_forged_record_law(
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    authority = _authority(carrier)
    record = carrier["record_execution"]
    record["record_counts"] = [1, 1, 2]
    record["record_probabilities"] = [0.25, 0.25, 0.5]
    _rehash(carrier)

    with pytest.raises(ValueError, match="binding|content|Record"):
        _materialize(
            carrier,
            projected_xz_schedule,
            cap=48,
            binding=authority,
        )


def test_materializer_does_not_allocate_repeat_support_buffers(
    monkeypatch,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)

    def forbidden_repeat(*_args, **_kwargs):
        raise AssertionError("bounded materialization must not allocate np.repeat buffers")

    monkeypatch.setattr(np, "repeat", forbidden_repeat)
    record = _materialize(carrier, projected_xz_schedule, cap=48)
    assert record.n_shots == 4


def test_materializer_streams_order_and_xor_without_aggregate_projection(
    monkeypatch,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)

    def forbidden_projector(*_args, **_kwargs):
        raise AssertionError("materializer allocated an aggregate support projection")

    monkeypatch.setattr(
        carrier_execution,
        "project_axis1_xor_records",
        forbidden_projector,
    )
    record = _materialize(carrier, projected_xz_schedule, cap=48)
    assert record.n_shots == 4


@pytest.mark.parametrize(
    "corruption",
    ["bool_count", "wrong_count_sum", "probability_mismatch", "wrong_projection", "unsorted", "duplicate", "evaluator_truth"],
)
def test_materializer_fails_closed_on_noncanonical_histogram_or_projection(
    projected_xz_schedule,
    corruption: str,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    record = carrier["record_execution"]
    if corruption == "bool_count":
        record["record_counts"] = [True, 1, 2]
    elif corruption == "wrong_count_sum":
        record["record_counts"] = [1, 1, 1]
    elif corruption == "probability_mismatch":
        record["record_probabilities"] = [0.5, 0.2, 0.3]
    elif corruption == "wrong_projection":
        record["detector_records"][1] = [0, 1]
    elif corruption == "unsorted":
        for field in (
            "measurement_records",
            "record_counts",
            "record_probabilities",
            "detector_records",
            "logical_observable_records",
        ):
            values = record[field]
            record[field] = [values[1], values[0], values[2]]
    elif corruption == "duplicate":
        record["measurement_records"][1] = [0, 0]
        record["detector_records"][1] = [0, 0]
        record["logical_observable_records"][1] = [0]
    elif corruption == "evaluator_truth":
        record["evaluator_only_diagnostics"] = {"level_records": [[0, 0]]}
    _rehash(carrier)

    with pytest.raises((TypeError, ValueError)):
        _materialize(carrier, projected_xz_schedule, cap=48)


@pytest.mark.parametrize(
    "corruption",
    [
        "identity",
        "options_type",
        "options_value",
        "program_summary",
        "record_type",
        "record_binding",
        "record_unexecuted",
        "claim_b8",
        "claim_decoder",
        "policy_type",
        "direct_type",
        "policy_binding",
        "policy_unaccepted",
        "direct_schema",
        "direct_binding",
        "direct_hash_invalid",
        "direct_mirror_value",
        "direct_mirror_type",
        "metadata_type",
        "metadata_value",
        "basis_summary",
        "basis_semantics",
        "observable_projection",
        "counts_type",
        "probabilities_type",
        "sampling_type",
        "trajectory_type",
        "trajectory_zero",
        "trajectory_mismatch",
        "trajectory_mode",
        "seed_mismatch",
        "seed_type",
        "support_length",
        "probability_bool",
        "probability_text",
        "probability_negative",
        "count_sum",
        "probability_sum",
    ],
)
def test_materializer_rejects_authenticated_semantic_corruption(
    projected_xz_schedule,
    corruption: str,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    options = copy.deepcopy(_BACKEND_OPTIONS)
    binding_overrides: dict[str, str] = {}
    record = carrier["record_execution"]
    policy = carrier["restricted_acceptance_policy"]
    direct = carrier["mcwf_mps_execution"]

    if corruption == "identity":
        carrier["source_hash"] = "0" * 64
    elif corruption == "options_type":
        carrier["execution_backend_options"] = None
    elif corruption == "options_value":
        carrier["execution_backend_options"]["trajectory_count"] = 5
    elif corruption == "program_summary":
        carrier["carrier_program"]["program_content_hash"] = "0" * 64
    elif corruption == "record_type":
        carrier["record_execution"] = None
    elif corruption == "record_binding":
        binding_overrides["record_execution_content_hash"] = (
            carrier_execution._stable_payload_hash(
                {"record_execution": copy.deepcopy(record)}
            )
        )
        record["record_counts"] = [1, 1, 2]
        record["record_probabilities"] = [0.25, 0.25, 0.5]
    elif corruption == "record_unexecuted":
        record["executed"] = False
    elif corruption == "claim_b8":
        record["claims_b8_artifact"] = True
    elif corruption == "claim_decoder":
        record["claims_decoder_integration"] = True
    elif corruption == "policy_type":
        carrier["restricted_acceptance_policy"] = None
    elif corruption == "direct_type":
        carrier["mcwf_mps_execution"] = None
    elif corruption == "policy_binding":
        binding_overrides["policy_content_hash"] = (
            carrier_execution._stable_payload_hash(
                {"policy": copy.deepcopy(policy)}
            )
        )
        policy["accepted_for_restricted_execution"] = False
    elif corruption == "policy_unaccepted":
        policy["accepted_for_restricted_execution"] = False
    elif corruption == "direct_schema":
        direct["schema"] = "unregistered.direct.v0"
    elif corruption == "direct_binding":
        binding_overrides["direct_content_hash"] = direct["content_hash"]
        direct["content_hash"] = "e" * 64
    elif corruption == "direct_hash_invalid":
        direct["content_hash"] = "g" * 64
    elif corruption == "direct_mirror_value":
        direct["execution_status"] = "failed"
    elif corruption == "direct_mirror_type":
        direct["passed"] = 1
    elif corruption == "metadata_type":
        record["measurement_keys"] = tuple(record["measurement_keys"])
    elif corruption == "metadata_value":
        record["measurement_keys"] = ["wrong", "mz"]
    elif corruption == "basis_summary":
        record["measurement_basis"] = "Z"
    elif corruption == "basis_semantics":
        record["measurement_basis_semantics"] = "forged"
    elif corruption == "observable_projection":
        record["logical_observable_records"][2] = [0]
    elif corruption == "counts_type":
        record["record_counts"] = tuple(record["record_counts"])
    elif corruption == "probabilities_type":
        record["record_probabilities"] = tuple(record["record_probabilities"])
    elif corruption == "sampling_type":
        record["trajectory_sampling"] = None
    elif corruption == "trajectory_type":
        record["trajectory_sampling"]["trajectory_count"] = True
    elif corruption == "trajectory_zero":
        record["trajectory_sampling"]["trajectory_count"] = 0
    elif corruption == "trajectory_mismatch":
        record["trajectory_sampling"]["trajectory_count"] = 5
    elif corruption == "trajectory_mode":
        record["trajectory_sampling"]["mode"] = "forged"
    elif corruption == "seed_mismatch":
        record["trajectory_sampling"]["rng_seed"] = 18
    elif corruption == "seed_type":
        options["rng_seed"] = 1
        carrier["execution_backend_options"]["rng_seed"] = 1
        record["trajectory_sampling"]["rng_seed"] = True
    elif corruption == "support_length":
        record["record_probabilities"] = record["record_probabilities"][:-1]
    elif corruption == "probability_bool":
        record["record_probabilities"][0] = True
    elif corruption == "probability_text":
        record["record_probabilities"][0] = "0.5"
    elif corruption == "probability_negative":
        record["record_probabilities"][0] = -0.5
    elif corruption == "count_sum":
        record["record_counts"] = [1, 1, 1]
        record["record_probabilities"] = [0.25, 0.25, 0.25]
    elif corruption == "probability_sum":
        offset = 5e-13
        record["record_probabilities"] = [
            0.5 + offset,
            0.25 + offset,
            0.25 + offset,
        ]

    _rehash(carrier)
    authority = _authority(carrier, **binding_overrides)
    with pytest.raises((TypeError, ValueError)):
        _materialize(
            carrier,
            projected_xz_schedule,
            cap=48,
            binding=authority,
            options=options,
        )


def test_materializer_requires_exact_internal_types(projected_xz_schedule) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    preflight = carrier_execution._preflight_mcwf_record_materialization(
        projected_xz_schedule,
        device="cuda",
        execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
        max_record_array_payload_bytes=48,
    )
    authority = _authority(carrier)
    with pytest.raises(TypeError, match="Carrier mapping"):
        carrier_execution._materialize_mcwf_carrier_record_batch(
            [],
            preflight=preflight,
            binding=authority,
        )
    with pytest.raises(TypeError, match="sealed preflight"):
        carrier_execution._materialize_mcwf_carrier_record_batch(
            carrier,
            preflight=object(),
            binding=authority,
        )
    with pytest.raises(TypeError, match="same-call binding"):
        carrier_execution._materialize_mcwf_carrier_record_batch(
            carrier,
            preflight=preflight,
            binding=object(),
        )


@pytest.mark.parametrize("projection", ["detector", "observable"])
def test_materializer_preserves_a_legitimate_zero_width_projection(
    projection: str,
) -> None:
    schedule, options, carrier = _zero_width_case(projection)

    materialized = _materialize(
        carrier,
        schedule,
        cap=16,
        options=options,
    )
    assert materialized.det.shape == (
        (4, 1) if projection == "detector" else (4, 0)
    )
    assert materialized.obs.shape == (
        (4, 0) if projection == "detector" else (4, 1)
    )


def test_materializer_normalizes_default_seed_to_zero(projected_xz_schedule) -> None:
    options = {
        "local_dims": [2, 2],
        "initial_levels": [0, 0],
        "trajectory_count": 4,
    }
    carrier = _accepted_carrier(projected_xz_schedule)
    carrier["execution_backend_options"] = copy.deepcopy(options)
    carrier["record_execution"]["trajectory_sampling"]["rng_seed"] = 0
    _rehash(carrier)

    materialized = _materialize(
        carrier,
        projected_xz_schedule,
        cap=48,
        options=options,
    )
    assert materialized.provenance["rng_seed"] == 0


def test_materializer_rejects_record_batch_shot_count_drift(
    monkeypatch,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)

    class WrongShotBatch:
        n_shots = 0

    monkeypatch.setattr(
        carrier_execution,
        "RecordBatch",
        lambda **_kwargs: WrongShotBatch(),
    )
    with pytest.raises(ValueError, match="shot count"):
        _materialize(carrier, projected_xz_schedule, cap=48)


def test_writer_emits_little_endian_b8_and_hash_bound_manifest_atomically(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def accepted_manifest(*args, **kwargs):
        calls.append((args, kwargs))
        return _produced(carrier)

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        accepted_manifest,
    )
    out_dir = tmp_path / "mcwf_records"
    result = carrier_execution.write_axis1_mcwf_mps_record_samples(
        projected_xz_schedule,
        out_dir,
        device="cuda",
        execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
        max_record_array_payload_bytes=48,
    )

    assert isinstance(result, carrier_execution.Axis1McwfMpsRecordSampleResult)
    assert len(calls) == 1
    assert calls[0][0] == (projected_xz_schedule,)
    assert calls[0][1]["_return_record_binding"] is True
    expected_det = np.array([[0, 0], [0, 0], [1, 1], [1, 0]], dtype=np.uint8)
    expected_obs = np.array([[0], [0], [0], [1]], dtype=np.uint8)
    det_path = out_dir / "detection_events.b8"
    obs_path = out_dir / "obs_flips_actual.b8"
    carrier_evidence_path = out_dir / "axis1_mcwf_mps_carrier_execution.json"
    carrier_program_path = out_dir / "axis1_mcwf_mps_carrier_program.json"
    assert result.carrier_evidence == carrier_evidence_path
    assert result.carrier_program_evidence == carrier_program_path
    persisted_carrier = json.loads(carrier_evidence_path.read_text())
    persisted_program = json.loads(carrier_program_path.read_text())
    assert persisted_carrier == carrier
    assert persisted_program["content_hash"] == carrier["carrier_program"][
        "content_hash"
    ]
    assert persisted_carrier["restricted_acceptance_policy"] == carrier[
        "restricted_acceptance_policy"
    ]
    assert det_path.read_bytes() == np.packbits(
        expected_det, axis=1, bitorder="little"
    ).tobytes()
    assert obs_path.read_bytes() == np.packbits(
        expected_obs, axis=1, bitorder="little"
    ).tobytes()

    manifests = list(out_dir.glob("*.json"))
    assert len(manifests) == 3
    manifest = json.loads(result.sample_summary.read_text())
    assert manifest["schema"] == carrier_execution.AXIS1_MCWF_MPS_RECORD_OUTPUT_SCHEMA
    assert manifest["representability"] == (
        carrier_execution.AXIS1_MCWF_MPS_RECORD_OUTPUT_REPRESENTABILITY
    )
    assert manifest["verdict"] == "pass" and manifest["passed"] is True
    assert manifest["carrier_execution_content_hash"] == carrier["content_hash"]
    assert manifest["materialization_order"] == _MATERIALIZATION_ORDER
    assert manifest["original_trajectory_order_preserved"] is False
    assert "incremental NumPy Record arrays only" in manifest[
        "record_array_payload_bound_scope"
    ]
    assert manifest["publication_status"] == "prepared_for_atomic_publication"
    assert manifest["claims_offline_durability_confirmation"] is False
    assert manifest["atomic_publication"][
        "parent_directory_fsync_required_after_rename"
    ] is True
    assert manifest["atomic_publication"][
        "parent_directory_fsync_success_attested_in_bundle"
    ] is False
    assert manifest["atomic_publication"]["durability_confirmation"] == (
        "successful_writer_return_only_not_self_attested_in_bundle"
    )
    assert manifest["atomic_publication"]["durability_failure_policy"] == (
        "preserve_published_directory_raise_without_path_cleanup"
    )
    assert manifest["atomic_publication"][
        "complete_artifact_set_visible_after_single_rename"
    ] is True
    assert manifest["record_layout"]["detectors"][0]["name"] == "parity"
    assert manifest["record_layout"]["observables"][0]["name"] == "logical_x"
    assert len(manifest["record_layout"]["content_hash"]) == 64
    assert manifest["build_identity"] == _UNIT_BUILD_IDENTITY
    assert manifest["source_implementation"] == _UNIT_SOURCE_IDENTITY
    assert manifest["build_identity_scope"] == (
        "disk_package_tree_matches_package_import_time_digest_at_"
        "validation_checkpoints"
    )
    assert manifest["source_implementation_identity_scope"] == (
        "disk_source_file_matches_module_import_time_digest_at_"
        "validation_checkpoints"
    )
    assert manifest["claims_runtime_code_object_attestation"] is False
    assert manifest["environment_identity"]["authoritative_lock_status"] == "bound"
    assert manifest["environment_identity"]["authoritative_lock_scope"] == (
        "lock_hash_bound_only"
    )
    assert manifest["environment_identity"][
        "authoritative_lock_conformance_checked"
    ] is False
    assert manifest["environment_identity"][
        "claims_reproducible_environment"
    ] is False
    assert manifest["environment_identity"]["runtime"] == _UNIT_RUNTIME_IDENTITY
    assert manifest["atomic_publication"][
        "target_parent_renameat2_noreplace_probe"
    ] == "passed_before_mcwf_execution"
    assert manifest["atomic_publication"][
        "sealed_identity_revalidation_required_after_execution"
    ] is True
    assert manifest["atomic_publication"][
        "sealed_identity_revalidation_success_attested_in_bundle"
    ] is False
    assert set(manifest["atomic_publication"]) == {
        "protocol",
        "manifest_written_last_in_stage",
        "complete_artifact_set_visible_after_single_rename",
        "staging_directory_fsync_required_before_rename",
        "staging_directory_fsync_success_attested_in_bundle",
        "staged_artifact_set_policy",
        "artifact_file_fsync_required_at_each_seal_checkpoint",
        "artifact_file_fsync_success_attested_in_bundle",
        "staged_artifact_set_revalidation_required_after_stage_fsync",
        "staged_artifact_set_revalidation_success_attested_in_bundle",
        "published_artifact_set_recheck_after_rename_required",
        "published_artifact_set_recheck_after_rename_success_attested_in_bundle",
        "published_artifact_set_recheck_after_parent_fsync_required",
        "published_artifact_set_recheck_after_parent_fsync_success_attested_in_bundle",
        "parent_directory_fsync_required_after_rename",
        "parent_directory_fsync_success_attested_in_bundle",
        "destination_no_clobber",
        "unsupported_atomic_noreplace_fails_closed",
        "target_parent_renameat2_noreplace_probe",
        "target_parent_identity_fields",
        "sealed_parent_dirfd_held_since_preflight",
        "rename_on_sealed_parent_dirfd_required",
        "parent_fsync_on_sealed_parent_dirfd_required",
        "return_path_parent_identity_recheck_required_after_parent_fsync",
        "published_destination_identity_match_required_after_rename",
        "published_destination_identity_match_success_attested_in_bundle",
        "published_destination_identity_recheck_after_parent_fsync_required",
        "published_destination_identity_recheck_success_attested_in_bundle",
        "published_destination_identity_recheck_after_final_artifact_recheck_required",
        "published_destination_identity_recheck_after_final_artifact_recheck_success_attested_in_bundle",
        "rename_exception_policy",
        "sealed_identity_revalidation_required_after_execution",
        "sealed_identity_revalidation_required_before_atomic_rename",
        "sealed_identity_revalidation_required_after_final_artifact_recheck",
        "sealed_identity_revalidation_success_attested_in_bundle",
        "durability_confirmation",
        "durability_failure_policy",
    }
    assert manifest["atomic_publication"][
        "published_destination_identity_match_success_attested_in_bundle"
    ] is False
    assert manifest["atomic_publication"][
        "published_destination_identity_recheck_success_attested_in_bundle"
    ] is False
    assert manifest["atomic_publication"][
        "published_destination_identity_recheck_after_final_artifact_recheck_success_attested_in_bundle"
    ] is False
    assert manifest["atomic_publication"]["staged_artifact_set_policy"] == (
        "exact_regular_files_bound_by_st_dev_st_ino_st_mode_st_size_"
        "st_mtime_ns_st_ctime_ns_sha256"
    )
    for field in (
        "staging_directory_fsync_success_attested_in_bundle",
        "artifact_file_fsync_success_attested_in_bundle",
        "staged_artifact_set_revalidation_success_attested_in_bundle",
        "published_artifact_set_recheck_after_rename_success_attested_in_bundle",
        "published_artifact_set_recheck_after_parent_fsync_success_attested_in_bundle",
    ):
        assert manifest["atomic_publication"][field] is False
    top_level_publication_claim_keys = {
        key
        for key in manifest
        if any(token in key for token in ("publication", "durability", "rename"))
    }
    assert top_level_publication_claim_keys == {
        "publication_status",
        "claims_offline_durability_confirmation",
        "atomic_publication",
    }
    assert manifest["offline_audit_scope"] == (
        "public_record_gate_and_binding_not_evaluator_replay"
    )
    assert manifest["claims_evaluator_oracle_replay"] is False
    assert manifest["metric_and_gate_policy"][
        "direct_execution_summary_locator"
    ].endswith("#/mcwf_mps_execution")
    assert (
        manifest["metric_and_gate_policy"]["evaluator_replay_available"] is False
    )
    assert manifest["run_configuration"]["rng_seed"] == 17
    assert manifest["run_configuration"]["state_dtype"] == "torch.complex128"
    for field, path in (
        ("detection_events", det_path),
        ("obs_flips_actual", obs_path),
    ):
        assert manifest["artifacts"][field]["status"] == "written"
        assert manifest["artifacts"][field]["sha256"] == hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    carrier_entry = manifest["artifacts"]["carrier_execution"]
    assert carrier_entry["file"] == carrier_evidence_path.name
    assert carrier_entry["sha256"] == hashlib.sha256(
        carrier_evidence_path.read_bytes()
    ).hexdigest()
    assert carrier_entry["schema"] == carrier["schema"]
    assert carrier_entry["content_hash"] == carrier["content_hash"]
    assert carrier_entry["contains_restricted_acceptance_policy"] is True
    assert carrier_entry["contains_carrier_program_summary"] is True
    assert carrier_entry["contains_evaluator_only_truth"] is False
    assert carrier_entry["restricted_acceptance_policy_locator"].endswith(
        "#/restricted_acceptance_policy"
    )
    assert carrier_entry["carrier_program_summary_locator"].endswith(
        "#/carrier_program"
    )
    assert carrier_entry["direct_execution_summary_locator"].endswith(
        "#/mcwf_mps_execution"
    )
    assert carrier_entry["record_execution_locator"].endswith("#/record_execution")
    program_entry = manifest["artifacts"]["carrier_program"]
    assert program_entry["file"] == carrier_program_path.name
    assert program_entry["sha256"] == hashlib.sha256(
        carrier_program_path.read_bytes()
    ).hexdigest()
    assert program_entry["content_hash"] == persisted_program["content_hash"]
    assert program_entry["contains_complete_sealed_program"] is True
    assert manifest["content_hash"] == _stable_hash(manifest)

    bad = copy.deepcopy(carrier)
    trusted_binding = _authority(carrier)
    bad["record_execution"]["detector_records"][1] = [0, 1]
    _rehash(bad)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: (bad, trusted_binding),
    )
    rejected_dir = tmp_path / "rejected"
    with pytest.raises((TypeError, ValueError)):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            rejected_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert not rejected_dir.exists() or not any(rejected_dir.iterdir())


def test_writer_rejects_existing_output_directory_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "already-present"
    out_dir.mkdir()
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran before output preflight")

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    with pytest.raises(ValueError, match="fresh output directory"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0


def test_writer_rechecks_program_after_publication_preflight_before_publish(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    captured_preflights = []
    real_record_preflight = (
        carrier_execution._preflight_mcwf_record_materialization
    )
    real_publication_validation = (
        carrier_execution._validate_mcwf_record_publication_preflight
    )
    publish_calls = []

    def capture_record_preflight(*args, **kwargs):
        preflight = real_record_preflight(*args, **kwargs)
        captured_preflights.append(preflight)
        return preflight

    def mutate_after_publication_validation(*args, **kwargs):
        real_publication_validation(*args, **kwargs)
        program = captured_preflights[0].carrier_program
        program["scope"] = "mutated_after_publication_preflight"
        _rehash(program)

    def observed_publish(*args, **kwargs):
        publish_calls.append((args, kwargs))
        raise AssertionError("changed program must not reach publication")

    monkeypatch.setattr(
        carrier_execution,
        "_preflight_mcwf_record_materialization",
        capture_record_preflight,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    monkeypatch.setattr(
        carrier_execution,
        "_validate_mcwf_record_publication_preflight",
        mutate_after_publication_validation,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_publish_mcwf_record_samples",
        observed_publish,
    )

    with pytest.raises(
        ValueError,
        match="declared content hash changed after compile",
    ):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            tmp_path / "not-published",
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert len(captured_preflights) == 1
    assert publish_calls == []


def test_writer_rechecks_program_before_atomic_publication(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    captured_preflights = []
    validation_calls = 0
    real_record_preflight = (
        carrier_execution._preflight_mcwf_record_materialization
    )
    real_publication_validation = (
        carrier_execution._validate_mcwf_record_publication_preflight
    )

    def capture_record_preflight(*args, **kwargs):
        preflight = real_record_preflight(*args, **kwargs)
        captured_preflights.append(preflight)
        return preflight

    def mutate_during_staged_publication_validation(*args, **kwargs):
        nonlocal validation_calls
        real_publication_validation(*args, **kwargs)
        validation_calls += 1
        if validation_calls == 2:
            program = captured_preflights[0].carrier_program
            program["scope"] = "mutated_before_atomic_publication"
            _rehash(program)

    monkeypatch.setattr(
        carrier_execution,
        "_preflight_mcwf_record_materialization",
        capture_record_preflight,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    monkeypatch.setattr(
        carrier_execution,
        "_validate_mcwf_record_publication_preflight",
        mutate_during_staged_publication_validation,
    )
    out_dir = tmp_path / "atomic-publication-rejected"

    with pytest.raises(
        ValueError,
        match="declared content hash changed after compile",
    ):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert validation_calls >= 2
    assert not out_dir.exists()


def test_writer_freezes_relative_output_path_before_long_running_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    initial_directory = tmp_path / "initial"
    changed_directory = tmp_path / "changed"
    initial_directory.mkdir()
    changed_directory.mkdir()
    monkeypatch.chdir(initial_directory)
    carrier = _accepted_carrier(projected_xz_schedule)

    def change_cwd_then_return(*_args, **_kwargs):
        monkeypatch.chdir(changed_directory)
        return _produced(carrier)

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        change_cwd_then_return,
    )
    result = carrier_execution.write_axis1_mcwf_mps_record_samples(
        projected_xz_schedule,
        Path("relative-output"),
        device="cuda",
        execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
        max_record_array_payload_bytes=48,
    )

    assert result.out_dir == initial_directory / "relative-output"
    assert result.sample_summary.is_file()
    assert not (changed_directory / "relative-output").exists()


def test_writer_stages_complete_directory_and_removes_it_on_write_failure(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    out_dir = tmp_path / "published"

    real_streaming_writer = carrier_execution._write_canonical_json_streaming

    def fail_manifest_write(path: Path, payload: dict[str, Any]):
        assert not out_dir.exists()
        assert path.parent != out_dir
        if path.name == "axis1_mcwf_mps_sample_summary.json":
            assert (path.parent / "axis1_mcwf_mps_carrier_execution.json").is_file()
            assert (path.parent / "axis1_mcwf_mps_carrier_program.json").is_file()
            raise OSError("injected manifest write failure")
        real_streaming_writer(path, payload)

    monkeypatch.setattr(
        carrier_execution,
        "_write_canonical_json_streaming",
        fail_manifest_write,
    )
    with pytest.raises(OSError, match="injected manifest"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert not out_dir.exists()
    assert not list(tmp_path.glob(".published.tmp-*"))


def test_writer_rejects_missing_required_staged_artifact_before_manifest(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_streaming_writer = carrier_execution._write_canonical_json_streaming

    def remove_program_after_carrier_write(path: Path, payload: dict[str, Any]):
        real_streaming_writer(path, payload)
        if path.name == "axis1_mcwf_mps_carrier_execution.json":
            (path.parent / "axis1_mcwf_mps_carrier_program.json").unlink()

    monkeypatch.setattr(
        carrier_execution,
        "_write_canonical_json_streaming",
        remove_program_after_carrier_write,
    )
    out_dir = tmp_path / "missing-required-artifact"
    with pytest.raises(RuntimeError, match="required staged artifact"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert not out_dir.exists()
    assert not list(tmp_path.glob(".missing-required-artifact.tmp-*"))


def test_writer_rejects_symlinked_required_staged_artifact(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_streaming_writer = carrier_execution._write_canonical_json_streaming

    def replace_program_with_symlink(path: Path, payload: dict[str, Any]):
        real_streaming_writer(path, payload)
        if path.name == "axis1_mcwf_mps_carrier_execution.json":
            program = path.parent / "axis1_mcwf_mps_carrier_program.json"
            program.unlink()
            program.symlink_to(path.name)

    monkeypatch.setattr(
        carrier_execution,
        "_write_canonical_json_streaming",
        replace_program_with_symlink,
    )
    out_dir = tmp_path / "symlinked-required-artifact"
    with pytest.raises(RuntimeError, match="required staged artifact"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert not out_dir.exists()
    assert not list(tmp_path.glob(".symlinked-required-artifact.tmp-*"))


def test_artifact_seal_requires_successful_file_fsync(
    monkeypatch,
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"sealed\n")
    expected_sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    stage_fd = os.open(
        tmp_path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )

    def fail_file_fsync(_descriptor: int) -> None:
        raise OSError("injected artifact file fsync failure")

    monkeypatch.setattr(carrier_execution.os, "fsync", fail_file_fsync)
    try:
        with pytest.raises(OSError, match="artifact file fsync"):
            carrier_execution._seal_required_mcwf_record_artifact(
                stage_fd,
                artifact.name,
                expected_sha256=expected_sha256,
            )
    finally:
        os.close(stage_fd)


@pytest.mark.parametrize(
    "mutation",
    [
        "delete_manifest",
        "tamper_detection_events",
        "rewrite_detection_events_same_content",
        "add_extra_file",
    ],
)
def test_writer_revalidates_exact_staged_artifact_set_after_directory_fsync(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
    mutation: str,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_fsync_directory = carrier_execution._fsync_directory

    def mutate_then_fsync(stage_path: Path) -> None:
        if mutation == "delete_manifest":
            (stage_path / "axis1_mcwf_mps_sample_summary.json").unlink()
        elif mutation == "tamper_detection_events":
            detection_events = stage_path / "detection_events.b8"
            payload = detection_events.read_bytes()
            detection_events.write_bytes(bytes([payload[0] ^ 1, *payload[1:]]))
        elif mutation == "rewrite_detection_events_same_content":
            detection_events = stage_path / "detection_events.b8"
            detection_events.write_bytes(detection_events.read_bytes())
        else:
            (stage_path / "evaluator_truth.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
        real_fsync_directory(stage_path)

    monkeypatch.setattr(
        carrier_execution,
        "_fsync_directory",
        mutate_then_fsync,
    )
    out_dir = tmp_path / f"staged-set-{mutation}"
    with pytest.raises(RuntimeError, match="staged artifact set"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert not out_dir.exists()


def test_writer_rejects_missing_environment_lock_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran without an environment lock")

    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_authoritative_environment_lock",
        lambda: tmp_path / "missing-environment.lock",
        raising=False,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    out_dir = tmp_path / "missing-lock-output"
    with pytest.raises(FileNotFoundError, match="environment lock"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert not out_dir.exists()


def test_writer_rejects_nonhex_environment_lock_hash_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran with an invalid lock hash")

    monkeypatch.setattr(
        carrier_execution,
        "file_sha256",
        lambda _path: "z" * 64,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    out_dir = tmp_path / "invalid-lock-hash-output"
    with pytest.raises(ValueError, match="environment lock hash is invalid"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert not out_dir.exists()


def test_writer_rejects_missing_atomic_noreplace_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran without atomic no-replace")

    def unavailable_noreplace():
        raise OSError("renameat2 unavailable")

    monkeypatch.setattr(
        carrier_execution,
        "_require_atomic_noreplace_publication",
        unavailable_noreplace,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    out_dir = tmp_path / "missing-noreplace-output"
    with pytest.raises(OSError, match="renameat2 unavailable"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert not out_dir.exists()


def test_writer_rejects_missing_target_parent_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran without an output parent")

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    out_dir = tmp_path / "missing-parent" / "output"
    with pytest.raises(FileNotFoundError, match="target parent"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert not out_dir.parent.exists()


def test_target_parent_identity_uses_one_stat_snapshot(
    monkeypatch,
    tmp_path: Path,
) -> None:
    expected_stat = tmp_path.stat()

    def forbidden_second_lookup(_path: Path) -> bool:
        raise AssertionError("parent identity must not perform a second path lookup")

    monkeypatch.setattr(Path, "is_dir", forbidden_second_lookup)
    assert carrier_execution._mcwf_record_target_parent_identity(tmp_path) == (
        int(expected_stat.st_dev),
        int(expected_stat.st_ino),
    )


def test_writer_probes_target_filesystem_noreplace_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0
    probed_parents: list[Path] = []

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran without a target filesystem probe")

    def unsupported_target(parent: Path, **_kwargs) -> None:
        probed_parents.append(parent)
        raise OSError("target filesystem rejects renameat2 noreplace")

    monkeypatch.setattr(
        carrier_execution,
        "_probe_atomic_noreplace_publication",
        unsupported_target,
        raising=False,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    out_dir = tmp_path / "unsupported-target-output"
    with pytest.raises(OSError, match="target filesystem"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert probed_parents == [out_dir.parent]
    assert not out_dir.exists()


def test_target_filesystem_probe_cleans_first_private_directory_if_second_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    first_probe = tmp_path / ".probe-source"
    calls = 0

    def fail_second_mkdtemp(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            first_probe.mkdir()
            return str(first_probe)
        raise OSError("injected second probe allocation failure")

    monkeypatch.setattr(
        carrier_execution,
        "_require_atomic_noreplace_publication",
        lambda: object(),
    )
    monkeypatch.setattr(carrier_execution.tempfile, "mkdtemp", fail_second_mkdtemp)

    with pytest.raises(OSError, match="second probe allocation"):
        carrier_execution._probe_atomic_noreplace_publication(tmp_path)
    assert not first_probe.exists()


def test_target_filesystem_probe_real_success_leaves_no_private_directories(
    tmp_path: Path,
) -> None:
    carrier_execution._probe_atomic_noreplace_publication(tmp_path)
    assert not list(tmp_path.glob(".mcwf-noreplace-*"))


def test_target_filesystem_probe_rejects_collision_leg_false_success(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        lambda *_args, **_kwargs: None,
    )
    with pytest.raises(OSError, match="failed to preserve"):
        carrier_execution._probe_atomic_noreplace_publication(tmp_path)
    assert not list(tmp_path.glob(".mcwf-noreplace-*"))


def test_target_filesystem_probe_cleans_both_legs_on_success_leg_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls = 0

    def fail_success_leg(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise FileExistsError(errno.EEXIST, "collision preserved")
        raise OSError(errno.ENOTSUP, "injected success-leg failure")

    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        fail_success_leg,
    )
    with pytest.raises(OSError, match="successful no-replace rename"):
        carrier_execution._probe_atomic_noreplace_publication(tmp_path)
    assert calls == 2
    assert not list(tmp_path.glob(".mcwf-noreplace-*"))


def test_target_filesystem_probe_rejects_success_leg_wrong_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls = 0

    def no_op_success_leg(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise FileExistsError(errno.EEXIST, "collision preserved")

    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        no_op_success_leg,
    )
    with pytest.raises(OSError, match="invalid rename result"):
        carrier_execution._probe_atomic_noreplace_publication(tmp_path)
    assert calls == 2
    assert not list(tmp_path.glob(".mcwf-noreplace-*"))


def test_writer_rejects_loaded_package_tree_drift_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran with stale loaded package code")

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_build_identity",
        _REAL_MCWF_RECORD_BUILD_IDENTITY,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_PACKAGE_TREE_SHA256_AT_IMPORT",
        "a" * 64,
        raising=False,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_fresh_package_tree_sha256",
        lambda: "b" * 64,
    )

    out_dir = tmp_path / "loaded-package-drift-output"
    with pytest.raises(RuntimeError, match="loaded package tree"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert not out_dir.exists()


def test_source_identity_rejects_missing_file_hash(monkeypatch) -> None:
    monkeypatch.setattr(carrier_execution, "file_sha256", lambda _path: None)
    with pytest.raises(RuntimeError, match="source-file SHA-256"):
        _REAL_MCWF_RECORD_SOURCE_IDENTITY()


def test_source_identity_rejects_disk_drift_from_package_import(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        carrier_execution,
        "_MCWF_RECORD_SOURCE_SHA256_AT_IMPORT",
        "a" * 64,
        raising=False,
    )
    monkeypatch.setattr(carrier_execution, "file_sha256", lambda _path: "b" * 64)
    with pytest.raises(RuntimeError, match="loaded source file"):
        _REAL_MCWF_RECORD_SOURCE_IDENTITY()


def test_git_identity_uses_full_validated_head(monkeypatch) -> None:
    calls: list[list[str]] = []

    class Result:
        returncode = 0
        stdout = "a" * 40 + "\n"

    def full_head(command, **_kwargs):
        calls.append(command)
        return Result()

    monkeypatch.setattr(carrier_execution.subprocess, "run", full_head)
    assert carrier_execution._mcwf_record_fresh_git_commit() == "a" * 40
    assert calls == [["git", "rev-parse", "HEAD"]]


def test_git_identity_rejects_short_or_unavailable_head(monkeypatch) -> None:
    class Result:
        returncode = 0
        stdout = "deadbee\n"

    monkeypatch.setattr(
        carrier_execution.subprocess,
        "run",
        lambda *_args, **_kwargs: Result(),
    )
    with pytest.raises(RuntimeError, match="Git HEAD identity"):
        carrier_execution._mcwf_record_fresh_git_commit()


def test_writer_rejects_build_identity_drift_after_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    executed = False

    def produced_after_marking_execution(*_args, **_kwargs):
        nonlocal executed
        executed = True
        return _produced(carrier)

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        produced_after_marking_execution,
    )
    changed = copy.deepcopy(_UNIT_BUILD_IDENTITY)
    changed["package_tree_sha256"] = "c" * 64
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_build_identity",
        lambda: copy.deepcopy(changed if executed else _UNIT_BUILD_IDENTITY),
    )

    out_dir = tmp_path / "build-drift-output"
    with pytest.raises(RuntimeError, match="build identity changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert not out_dir.exists()


def test_writer_rejects_source_identity_drift_after_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    executed = False

    def produced_after_marking_execution(*_args, **_kwargs):
        nonlocal executed
        executed = True
        return _produced(carrier)

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        produced_after_marking_execution,
    )
    changed = copy.deepcopy(_UNIT_SOURCE_IDENTITY)
    changed["sha256"] = "6" * 64
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_source_implementation_identity",
        lambda: copy.deepcopy(changed if executed else _UNIT_SOURCE_IDENTITY),
    )

    out_dir = tmp_path / "source-drift-output"
    with pytest.raises(RuntimeError, match="source implementation changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert not out_dir.exists()


def test_writer_rejects_runtime_identity_drift_after_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    executed = False

    def produced_after_marking_execution(*_args, **_kwargs):
        nonlocal executed
        executed = True
        return _produced(carrier)

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        produced_after_marking_execution,
    )
    changed = copy.deepcopy(_UNIT_RUNTIME_IDENTITY)
    changed["gpu_uuid"] = "GPU-changed"
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_runtime_identity",
        lambda _device: copy.deepcopy(
            changed if executed else _UNIT_RUNTIME_IDENTITY
        ),
    )

    out_dir = tmp_path / "runtime-drift-output"
    with pytest.raises(RuntimeError, match="runtime identity changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert not out_dir.exists()


def test_writer_rejects_environment_lock_drift_after_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    lock_path = tmp_path / "authoritative.lock"
    lock_path.write_text("sealed-before-execution\n", encoding="utf-8")
    carrier = _accepted_carrier(projected_xz_schedule)

    def mutate_lock_then_return(*_args, **_kwargs):
        lock_path.write_text("changed-during-execution\n", encoding="utf-8")
        return _produced(carrier)

    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_authoritative_environment_lock",
        lambda: lock_path,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        mutate_lock_then_return,
    )

    out_dir = tmp_path / "environment-drift-output"
    with pytest.raises(RuntimeError, match="environment lock changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert not out_dir.exists()


def test_writer_rejects_environment_lock_drift_after_staging_before_rename(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    lock_path = tmp_path / "authoritative.lock"
    lock_path.write_text("sealed-before-execution\n", encoding="utf-8")
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_authoritative_environment_lock",
        lambda: lock_path,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_fsync_directory = carrier_execution._fsync_directory
    directory_fsync_calls = 0

    def mutate_lock_after_staging_fsync(path: Path) -> None:
        nonlocal directory_fsync_calls
        real_fsync_directory(path)
        directory_fsync_calls += 1
        if directory_fsync_calls == 1:
            lock_path.write_text("changed-after-staging\n", encoding="utf-8")

    monkeypatch.setattr(
        carrier_execution,
        "_fsync_directory",
        mutate_lock_after_staging_fsync,
    )

    out_dir = tmp_path / "pre-rename-environment-drift-output"
    with pytest.raises(RuntimeError, match="environment lock changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert not out_dir.exists()
    assert not list(tmp_path.glob(".pre-rename-environment-drift-output.tmp-*"))
    assert directory_fsync_calls == 1


def test_writer_rejects_target_parent_replacement_after_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    target_parent = tmp_path / "target-parent"
    target_parent.mkdir()
    moved_parent = tmp_path / "preflighted-parent"
    carrier = _accepted_carrier(projected_xz_schedule)

    def replace_parent_then_return(*_args, **_kwargs):
        target_parent.rename(moved_parent)
        target_parent.mkdir()
        return _produced(carrier)

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        replace_parent_then_return,
    )

    out_dir = target_parent / "parent-drift-output"
    with pytest.raises(RuntimeError, match="target parent changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert not out_dir.exists()


def test_parent_replaced_after_stage_before_second_validation_cleans_sealed_stage(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    target_parent = tmp_path / "target-parent"
    target_parent.mkdir()
    moved_parent = tmp_path / "preflighted-parent"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_validate = carrier_execution._validate_mcwf_record_publication_preflight
    validation_calls = 0

    def replace_parent_before_second_validation(*args, **kwargs) -> None:
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 2:
            target_parent.rename(moved_parent)
            target_parent.mkdir()
        real_validate(*args, **kwargs)

    monkeypatch.setattr(
        carrier_execution,
        "_validate_mcwf_record_publication_preflight",
        replace_parent_before_second_validation,
    )
    out_dir = target_parent / "stage-cleanup-output"
    with pytest.raises(RuntimeError, match="target parent changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert validation_calls == 2
    assert not list(moved_parent.glob(".stage-cleanup-output.tmp-*"))
    assert not list(target_parent.glob(".stage-cleanup-output.tmp-*"))
    assert not out_dir.exists()


def test_parent_replaced_inside_final_rename_window_cannot_publish_substitute(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    target_parent = tmp_path / "target-parent"
    target_parent.mkdir()
    moved_parent = tmp_path / "preflighted-parent"
    out_dir = target_parent / "rename-window-output"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_atomic_rename = carrier_execution._atomic_rename_directory_noreplace
    attacker_stage_paths: list[Path] = []

    def replace_parent_before_final_rename(source, destination, *args, **kwargs):
        if Path(destination).name == out_dir.name:
            stage_name = Path(source).name
            target_parent.rename(moved_parent)
            target_parent.mkdir()
            attacker_stage = target_parent / stage_name
            attacker_stage.mkdir()
            (attacker_stage / "attacker.txt").write_text(
                "not a claim bundle\n",
                encoding="utf-8",
            )
            attacker_stage_paths.append(attacker_stage)
        return real_atomic_rename(source, destination, *args, **kwargs)

    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        replace_parent_before_final_rename,
    )
    with pytest.raises(RuntimeError, match="target parent changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert len(attacker_stage_paths) == 1
    assert (attacker_stage_paths[0] / "attacker.txt").is_file()
    assert not out_dir.exists()
    assert (
        moved_parent
        / out_dir.name
        / "axis1_mcwf_mps_sample_summary.json"
    ).is_file()


def test_parent_replaced_after_rename_cannot_fsync_wrong_inode_and_return(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    target_parent = tmp_path / "target-parent"
    target_parent.mkdir()
    moved_parent = tmp_path / "preflighted-parent"
    out_dir = target_parent / "post-rename-parent-drift-output"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_atomic_rename = carrier_execution._atomic_rename_directory_noreplace

    def replace_parent_after_final_rename(source, destination, *args, **kwargs):
        result = real_atomic_rename(source, destination, *args, **kwargs)
        if Path(destination).name == out_dir.name:
            target_parent.rename(moved_parent)
            target_parent.mkdir()
        return result

    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        replace_parent_after_final_rename,
    )
    with pytest.raises(RuntimeError, match="target parent changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert not out_dir.exists()
    assert (
        moved_parent
        / out_dir.name
        / "axis1_mcwf_mps_sample_summary.json"
    ).is_file()


def test_final_rename_rejects_substituted_stage_entry_in_sealed_parent(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "substituted-stage-output"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_atomic_rename = carrier_execution._atomic_rename_directory_noreplace
    stolen_names: list[str] = []

    def substitute_stage_before_final_rename(source, destination, *args, **kwargs):
        if Path(destination).name == out_dir.name:
            parent_fd = kwargs["source_dir_fd"]
            stolen_name = f"{Path(source).name}.stolen"
            os.rename(
                Path(source).name,
                stolen_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            os.mkdir(Path(source).name, mode=0o700, dir_fd=parent_fd)
            substitute = Path(f"/proc/self/fd/{parent_fd}") / Path(source).name
            (substitute / "attacker.txt").write_text(
                "not a claim bundle\n",
                encoding="utf-8",
            )
            stolen_names.append(stolen_name)
        return real_atomic_rename(source, destination, *args, **kwargs)

    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        substitute_stage_before_final_rename,
    )
    with pytest.raises(RuntimeError, match="published directory identity"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert len(stolen_names) == 1
    assert (out_dir / "attacker.txt").is_file()
    assert not (out_dir / "axis1_mcwf_mps_sample_summary.json").exists()
    assert (tmp_path / stolen_names[0] / "axis1_mcwf_mps_sample_summary.json").is_file()


def test_exception_after_successful_rename_preserves_published_bundle(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "rename-return-failure-output"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_atomic_rename = carrier_execution._atomic_rename_directory_noreplace

    def raise_after_final_rename(source, destination, *args, **kwargs):
        result = real_atomic_rename(source, destination, *args, **kwargs)
        if Path(destination).name == out_dir.name:
            raise OSError("injected exception after successful rename")
        return result

    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        raise_after_final_rename,
    )
    with pytest.raises(OSError, match="after successful rename"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert (out_dir / "axis1_mcwf_mps_sample_summary.json").is_file()
    assert (out_dir / "axis1_mcwf_mps_carrier_execution.json").is_file()
    assert (out_dir / "axis1_mcwf_mps_carrier_program.json").is_file()


def test_published_entry_replaced_after_parent_fsync_cannot_return_success(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "post-fsync-entry-drift-output"
    moved_bundle = tmp_path / "sealed-published-bundle"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_fsync_directory_fd = carrier_execution._fsync_directory_fd

    def replace_entry_after_parent_fsync(directory_fd: int) -> None:
        real_fsync_directory_fd(directory_fd)
        out_dir.rename(moved_bundle)
        out_dir.mkdir()
        (out_dir / "attacker.txt").write_text(
            "not a claim bundle\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(
        carrier_execution,
        "_fsync_directory_fd",
        replace_entry_after_parent_fsync,
    )
    with pytest.raises(RuntimeError, match="published directory identity"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert (out_dir / "attacker.txt").is_file()
    assert (
        moved_bundle / "axis1_mcwf_mps_sample_summary.json"
    ).is_file()


def test_writer_rechecks_artifact_set_after_successful_rename(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "post-rename-artifact-drift"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_atomic_rename = carrier_execution._atomic_rename_directory_noreplace

    def tamper_after_final_rename(source, destination, *args, **kwargs):
        result = real_atomic_rename(source, destination, *args, **kwargs)
        if Path(destination).name == out_dir.name:
            detection_events = out_dir / "detection_events.b8"
            payload = detection_events.read_bytes()
            detection_events.write_bytes(bytes([payload[0] ^ 1, *payload[1:]]))
        return result

    monkeypatch.setattr(
        carrier_execution,
        "_atomic_rename_directory_noreplace",
        tamper_after_final_rename,
    )
    with pytest.raises(RuntimeError, match="staged artifact set"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert out_dir.is_dir()
    assert (out_dir / "axis1_mcwf_mps_sample_summary.json").is_file()


def test_writer_rechecks_artifact_set_after_parent_fsync(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "post-parent-fsync-artifact-drift"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_fsync_directory_fd = carrier_execution._fsync_directory_fd

    def tamper_after_parent_fsync(directory_fd: int) -> None:
        real_fsync_directory_fd(directory_fd)
        detection_events = out_dir / "detection_events.b8"
        payload = detection_events.read_bytes()
        detection_events.write_bytes(bytes([payload[0] ^ 1, *payload[1:]]))

    monkeypatch.setattr(
        carrier_execution,
        "_fsync_directory_fd",
        tamper_after_parent_fsync,
    )
    with pytest.raises(RuntimeError, match="staged artifact set"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert out_dir.is_dir()
    assert (out_dir / "axis1_mcwf_mps_sample_summary.json").is_file()


def test_published_entry_replaced_after_final_artifact_recheck_cannot_return_success(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "post-final-artifact-entry-drift"
    moved_bundle = tmp_path / "post-final-artifact-sealed-bundle"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_validator = carrier_execution._validate_mcwf_record_staged_artifact_set
    calls = 0

    def replace_entry_after_final_artifact_recheck(stage_fd: int, expected) -> None:
        nonlocal calls
        real_validator(stage_fd, expected)
        calls += 1
        if calls == 4:
            out_dir.rename(moved_bundle)
            out_dir.mkdir()
            (out_dir / "attacker.txt").write_text(
                "not a claim bundle\n",
                encoding="utf-8",
            )

    monkeypatch.setattr(
        carrier_execution,
        "_validate_mcwf_record_staged_artifact_set",
        replace_entry_after_final_artifact_recheck,
    )
    with pytest.raises(RuntimeError, match="published directory identity"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert calls == 4
    assert (out_dir / "attacker.txt").is_file()
    assert (
        moved_bundle / "axis1_mcwf_mps_sample_summary.json"
    ).is_file()


def test_writer_revalidates_build_identity_after_final_pre_rename_artifact_check(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "post-artifact-build-drift"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    drifted = False
    validation_calls = 0
    changed_build_identity = copy.deepcopy(_UNIT_BUILD_IDENTITY)
    changed_build_identity["package_tree_sha256"] = "c" * 64
    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_build_identity",
        lambda: copy.deepcopy(
            changed_build_identity if drifted else _UNIT_BUILD_IDENTITY
        ),
    )
    real_validator = carrier_execution._validate_mcwf_record_staged_artifact_set

    def drift_after_second_artifact_check(stage_fd: int, expected) -> None:
        nonlocal drifted, validation_calls
        real_validator(stage_fd, expected)
        validation_calls += 1
        if validation_calls == 2:
            drifted = True

    monkeypatch.setattr(
        carrier_execution,
        "_validate_mcwf_record_staged_artifact_set",
        drift_after_second_artifact_check,
    )
    with pytest.raises(RuntimeError, match="build identity changed"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert validation_calls == 2
    assert not out_dir.exists()


def test_final_artifact_validator_rejects_extra_file_injected_while_hashing(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    out_dir = tmp_path / "intra-validator-extra-file"
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_validator = carrier_execution._validate_mcwf_record_staged_artifact_set
    real_seal = carrier_execution._seal_required_mcwf_record_artifact
    validation_calls = 0
    final_validation_active = False
    injected = False

    def mark_final_validation(stage_fd: int, expected) -> None:
        nonlocal final_validation_active, validation_calls
        validation_calls += 1
        final_validation_active = validation_calls == 4
        try:
            real_validator(stage_fd, expected)
        finally:
            final_validation_active = False

    def inject_extra_after_first_final_seal(stage_fd: int, name: str, **kwargs):
        nonlocal injected
        seal = real_seal(stage_fd, name, **kwargs)
        if final_validation_active and not injected:
            extra_fd = os.open(
                "evaluator_truth.json",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
                0o600,
                dir_fd=stage_fd,
            )
            try:
                os.write(extra_fd, b"{}\n")
            finally:
                os.close(extra_fd)
            injected = True
        return seal

    monkeypatch.setattr(
        carrier_execution,
        "_validate_mcwf_record_staged_artifact_set",
        mark_final_validation,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_seal_required_mcwf_record_artifact",
        inject_extra_after_first_final_seal,
    )
    with pytest.raises(RuntimeError, match="staged artifact set"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert validation_calls == 4
    assert injected is True
    assert (out_dir / "evaluator_truth.json").is_file()


def test_writer_rejects_missing_runtime_identity_without_publishing(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran without sealed runtime identity")

    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )

    def unavailable_runtime(_device: str):
        raise RuntimeError("GPU runtime identity unavailable")

    monkeypatch.setattr(
        carrier_execution,
        "_mcwf_record_runtime_identity",
        unavailable_runtime,
    )
    out_dir = tmp_path / "missing-runtime-output"
    with pytest.raises(RuntimeError, match="runtime identity unavailable"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert not out_dir.exists()
    assert not list(tmp_path.glob(".missing-runtime-output.tmp-*"))


def test_runtime_identity_rejects_empty_cuda_build_version(monkeypatch) -> None:
    class Properties:
        uuid = "GPU-unit-test"
        name = "unit-test-gpu"
        pci_bus_id = 1
        major = 12
        minor = 0
        total_memory = 1024

    monkeypatch.setattr(carrier_execution.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(carrier_execution.torch.cuda, "current_device", lambda: 0)
    monkeypatch.setattr(
        carrier_execution.torch.cuda,
        "get_device_properties",
        lambda _index: Properties(),
    )
    monkeypatch.setattr(carrier_execution.torch.version, "cuda", "")
    monkeypatch.setattr(
        carrier_execution.Path,
        "read_text",
        lambda _path, **_kwargs: "NVRM Kernel Module  999.0.0\n",
    )
    monkeypatch.setattr(
        carrier_execution.torch.backends.cudnn,
        "version",
        lambda: 99999,
    )

    with pytest.raises(RuntimeError, match="CUDA UUID/build identity"):
        _REAL_MCWF_RECORD_RUNTIME_IDENTITY("cuda")


def test_writer_rejects_missing_dependency_version_before_mcwf_execution(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    calls = 0
    real_distribution_version = carrier_execution._distribution_version

    def forbidden_manifest(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("MCWF execution ran without dependency identity")

    def missing_quimb(distribution: str):
        if distribution == "quimb":
            return None
        return real_distribution_version(distribution)

    monkeypatch.setattr(
        carrier_execution,
        "_distribution_version",
        missing_quimb,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        forbidden_manifest,
    )
    out_dir = tmp_path / "missing-dependency-output"
    with pytest.raises(RuntimeError, match="distribution identity.*quimb"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )
    assert calls == 0
    assert not out_dir.exists()


def test_writer_atomic_noreplace_preserves_concurrently_created_empty_directory(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    out_dir = tmp_path / "raced-output"
    original_freshness_check = (
        carrier_execution._require_fresh_mcwf_record_output_directory
    )
    checks = 0

    def create_racing_directory_after_final_check(root: Path) -> None:
        nonlocal checks
        original_freshness_check(root)
        checks += 1
        if checks == 3:
            root.mkdir()

    monkeypatch.setattr(
        carrier_execution,
        "_require_fresh_mcwf_record_output_directory",
        create_racing_directory_after_final_check,
    )
    with pytest.raises(FileExistsError):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert out_dir.is_dir()
    assert not any(out_dir.iterdir())
    assert not list(tmp_path.glob(".raced-output.tmp-*"))


def test_writer_preserves_published_directory_without_path_cleanup_on_parent_fsync_failure(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    out_dir = tmp_path / "durability-failure"
    parent_calls = 0
    published_cleanup_attempted = False

    def fail_first_parent_fsync(_directory_fd: int) -> None:
        nonlocal parent_calls
        parent_calls += 1
        raise OSError("injected parent fsync failure")

    def forbid_published_path_cleanup(*_args, **_kwargs):
        nonlocal published_cleanup_attempted
        published_cleanup_attempted = True
        raise AssertionError("published directory must never be cleaned")

    monkeypatch.setattr(
        carrier_execution,
        "_fsync_directory_fd",
        fail_first_parent_fsync,
    )
    monkeypatch.setattr(
        carrier_execution,
        "_remove_unpublished_mcwf_record_stage",
        forbid_published_path_cleanup,
    )
    with pytest.raises(OSError, match="injected parent fsync"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert parent_calls == 1
    assert published_cleanup_attempted is False
    assert out_dir.is_dir()
    assert (out_dir / "axis1_mcwf_mps_sample_summary.json").is_file()
    assert not list(tmp_path.glob(".durability-failure.tmp-*"))


@pytest.mark.parametrize("projection", ["detector", "observable"])
def test_writer_emits_only_the_nonempty_zero_width_projection(
    monkeypatch,
    tmp_path: Path,
    projection: str,
) -> None:
    schedule, options, carrier = _zero_width_case(projection)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    out_dir = tmp_path / f"{projection}-only"
    result = carrier_execution.write_axis1_mcwf_mps_record_samples(
        schedule,
        out_dir,
        device="cuda",
        execution_backend_options=copy.deepcopy(options),
        max_record_array_payload_bytes=16,
    )

    manifest = json.loads(result.sample_summary.read_text())
    if projection == "detector":
        assert result.detection_events is not None
        assert result.obs_flips_actual is None
        assert manifest["artifacts"]["detection_events"]["bit_width"] == 1
        assert manifest["artifacts"]["obs_flips_actual"] is None
    else:
        assert result.detection_events is None
        assert result.obs_flips_actual is not None
        assert manifest["artifacts"]["detection_events"] is None
        assert manifest["artifacts"]["obs_flips_actual"]["bit_width"] == 1


def test_writer_rejects_missing_b8_for_nonzero_projection(
    monkeypatch,
    tmp_path: Path,
    projected_xz_schedule,
) -> None:
    carrier = _accepted_carrier(projected_xz_schedule)
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_write_b8_optional = carrier_execution.write_b8_optional

    def omit_detection_events(path: Path, bits: np.ndarray):
        if path.name == "detection_events.b8":
            return None
        return real_write_b8_optional(path, bits)

    monkeypatch.setattr(
        carrier_execution,
        "write_b8_optional",
        omit_detection_events,
    )
    out_dir = tmp_path / "missing-nonzero-b8"
    with pytest.raises(RuntimeError, match="artifact presence.*detector"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            projected_xz_schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(_BACKEND_OPTIONS),
            max_record_array_payload_bytes=48,
        )

    assert not out_dir.exists()


def test_writer_rejects_unexpected_b8_for_zero_width_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    schedule, options, carrier = _zero_width_case("detector")
    monkeypatch.setattr(
        carrier_execution,
        "_axis1_mcwf_mps_execution_manifest",
        lambda *_args, **_kwargs: _produced(carrier),
    )
    real_write_b8_optional = carrier_execution.write_b8_optional

    def emit_zero_width_artifact(path: Path, bits: np.ndarray):
        if int(bits.shape[1]) == 0:
            path.write_bytes(b"")
            return path
        return real_write_b8_optional(path, bits)

    monkeypatch.setattr(
        carrier_execution,
        "write_b8_optional",
        emit_zero_width_artifact,
    )
    out_dir = tmp_path / "unexpected-zero-width-b8"
    with pytest.raises(RuntimeError, match="artifact presence.*observable"):
        carrier_execution.write_axis1_mcwf_mps_record_samples(
            schedule,
            out_dir,
            device="cuda",
            execution_backend_options=copy.deepcopy(options),
            max_record_array_payload_bytes=16,
        )

    assert not out_dir.exists()

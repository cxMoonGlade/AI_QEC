"""GPU contract for materializing MCWF Carrier histograms as real Records.

The MCWF child intentionally emits only an authenticated, canonical histogram.
These tests require the public Record wrapper to expand that histogram exactly
once, in grouped support order, rather than drawing a second sample.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest
import torch

from error_coupling_simulator.carrier import RecordBatch
from error_coupling_simulator.frontend import (
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    Axis1LocalLindbladContextSpec,
    CircuitBuilder,
    axis1_carrier_execution_manifest,
    axis1_mcwf_mps_record_batch,
    circuit_ir_to_substep_schedule,
    write_axis1_mcwf_mps_record_samples,
)


_MATERIALIZATION_ORDER = "carrier_histogram_grouped_canonical_support_order"
_SUMMARY_SCHEMA = (
    "error_coupling_simulator.frontend.mcwf_mps_record_sample_summary.v1"
)


def _mixed_xz_projected_schedule():
    builder = CircuitBuilder(num_qubits=2)
    builder.measure(0, key="mx", basis="X", reset=False)
    builder.measure(1, key="mz", basis="Z", reset=False)
    builder.detector("d_mixed", xor=("mx", "mz"))
    builder.observable("logical_z", xor=("mz",), index=0)
    return circuit_ir_to_substep_schedule(builder.build())


def _no_measurement_schedule():
    builder = CircuitBuilder(num_qubits=1)
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=0.0,
            gamma_1_per_ns=0.01,
        )
    )
    builder.idle(0, duration_ns=1.0)
    return circuit_ir_to_substep_schedule(builder.build())


def _execution_options(*, trajectory_count: int, seed: int) -> dict[str, object]:
    return {
        "local_dims": [2, 2],
        "initial_levels": [0, 0],
        "microstep_count": 4,
        "finite_step_order": "first_order",
        "trajectory_count": trajectory_count,
        "rng_seed": seed,
        "mass_residual_budget": 0.1,
    }


def _expanded_child_rows(
    record_execution: dict[str, object],
    field: str,
) -> np.ndarray:
    rows = np.asarray(record_execution[field], dtype=np.uint8)
    counts = np.asarray(record_execution["record_counts"], dtype=np.int64)
    return np.repeat(rows, counts, axis=0)


def _unpack_file(path: Path, *, shots: int, width: int) -> np.ndarray:
    packed_width = (width + 7) // 8
    packed = np.frombuffer(path.read_bytes(), dtype=np.uint8).reshape(
        shots,
        packed_width,
    )
    return np.unpackbits(
        packed,
        axis=1,
        count=width,
        bitorder="little",
    )


def test_mixed_xz_carrier_histogram_materializes_once_and_writes_little_endian_b8(
    tmp_path: Path,
):
    if not torch.cuda.is_available():
        pytest.fail(
            "MCWF Carrier Record materialization is GPU-gated; CUDA-MISSING is not a release basis",
            pytrace=False,
        )

    schedule = _mixed_xz_projected_schedule()
    options = _execution_options(trajectory_count=32, seed=19073)
    carrier = axis1_carrier_execution_manifest(
        schedule,
        device="cuda",
        execution_backend_contract=(
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        execution_backend_options=options,
    )
    child = carrier["record_execution"]
    assert carrier["mcwf_mps_backend_executed"] is True
    assert child["executed"] is True
    assert child["measurement_keys"] == ["mx", "mz"]
    assert child["measurement_bases"] == ["X", "Z"]
    assert child["measurement_basis"] == "mixed_pauli"
    assert child["claims_b8_artifact"] is False

    record_batch = axis1_mcwf_mps_record_batch(
        schedule,
        device="cuda",
        execution_backend_options=options,
        max_record_array_payload_bytes=4_096,
    )
    assert isinstance(record_batch, RecordBatch)
    assert record_batch.n_shots == options["trajectory_count"]
    assert record_batch.provenance["materialization_order"] == (
        _MATERIALIZATION_ORDER
    )

    expanded_measurements = _expanded_child_rows(child, "measurement_records")
    expanded_detectors = _expanded_child_rows(child, "detector_records")
    expanded_observables = _expanded_child_rows(
        child,
        "logical_observable_records",
    )
    np.testing.assert_array_equal(record_batch.det, expanded_detectors)
    np.testing.assert_array_equal(record_batch.obs, expanded_observables)

    mx = expanded_measurements[:, 0]
    mz = expanded_measurements[:, 1]
    np.testing.assert_array_equal(record_batch.det[:, 0], mx ^ mz)
    np.testing.assert_array_equal(record_batch.obs[:, 0], mz)

    assert record_batch.det.flags.writeable is False
    assert record_batch.obs.flags.writeable is False
    with pytest.raises(ValueError):
        record_batch.det[0, 0] ^= np.uint8(1)
    with pytest.raises(FrozenInstanceError):
        record_batch.det = np.array(record_batch.det, copy=True)

    written = write_axis1_mcwf_mps_record_samples(
        schedule,
        tmp_path / "records",
        device="cuda",
        execution_backend_options=options,
        max_record_array_payload_bytes=4_096,
    )
    np.testing.assert_array_equal(written.record_batch.det, record_batch.det)
    np.testing.assert_array_equal(written.record_batch.obs, record_batch.obs)
    assert written.sample_manifest["schema"] == _SUMMARY_SCHEMA
    assert written.sample_manifest["materialization_order"] == (
        _MATERIALIZATION_ORDER
    )
    assert written.sample_manifest["claims_b8_artifact"] is True
    assert written.sample_manifest["claims_dem_artifact"] is False
    assert written.sample_manifest["claims_decoder_integration"] is False
    assert written.sample_summary.is_file()
    assert written.carrier_evidence.is_file()
    assert written.carrier_program_evidence.is_file()
    assert written.detection_events is not None
    assert written.obs_flips_actual is not None
    environment = written.sample_manifest["environment_identity"]
    assert environment["authoritative_lock_status"] == "bound"
    runtime = environment["runtime"]
    assert runtime["gpu_name"] == torch.cuda.get_device_properties(0).name
    assert runtime["gpu_uuid"] == str(torch.cuda.get_device_properties(0).uuid)
    assert runtime["compute_capability"] == list(
        torch.cuda.get_device_capability(0)
    )
    assert runtime["nvidia_driver"]
    assert runtime["torch_cuda_build_version"] == torch.version.cuda
    assert runtime["loaded_cuda_runtime_version"] is None
    assert runtime["loaded_cuda_runtime_version_status"] == "not_attested"
    carrier_artifact = written.sample_manifest["artifacts"]["carrier_execution"]
    assert carrier_artifact["file"] == written.carrier_evidence.name
    assert carrier_artifact["carrier_program_summary_locator"].endswith(
        "#/carrier_program"
    )
    assert carrier_artifact["record_execution_locator"].endswith(
        "#/record_execution"
    )
    program_artifact = written.sample_manifest["artifacts"]["carrier_program"]
    assert program_artifact["file"] == written.carrier_program_evidence.name
    assert program_artifact["contains_complete_sealed_program"] is True
    assert written.sample_manifest["atomic_publication"]["destination_no_clobber"]

    expected_det_bytes = np.packbits(
        record_batch.det,
        axis=1,
        bitorder="little",
    ).tobytes()
    expected_obs_bytes = np.packbits(
        record_batch.obs,
        axis=1,
        bitorder="little",
    ).tobytes()
    assert written.detection_events.read_bytes() == expected_det_bytes
    assert written.obs_flips_actual.read_bytes() == expected_obs_bytes
    np.testing.assert_array_equal(
        _unpack_file(
            written.detection_events,
            shots=record_batch.n_shots,
            width=record_batch.det.shape[1],
        ),
        record_batch.det,
    )
    np.testing.assert_array_equal(
        _unpack_file(
            written.obs_flips_actual,
            shots=record_batch.n_shots,
            width=record_batch.obs.shape[1],
        ),
        record_batch.obs,
    )


def test_no_measurement_mcwf_writer_fails_without_creating_artifacts(tmp_path: Path):
    out_dir = tmp_path / "no-measurement"
    options = {
        "local_dims": [2],
        "initial_levels": [1],
        "microstep_count": 4,
        "finite_step_order": "first_order",
        "trajectory_count": 8,
        "rng_seed": 19079,
        "mass_residual_budget": 0.1,
    }

    with pytest.raises(ValueError, match="measurement|Record"):
        write_axis1_mcwf_mps_record_samples(
            _no_measurement_schedule(),
            out_dir,
            device="cuda",
            execution_backend_options=options,
            max_record_array_payload_bytes=1_024,
        )

    assert not out_dir.exists() or not any(out_dir.rglob("*"))

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scope_static.physical.full_circuit_cudaq_teacher import (
    _CudaqSchedule,
    _build_full_circuit_oracle_mechanisms,
    _cudaq_target_looks_gpu,
    _mechanism_channels_by_location,
    _operation_sites_from_mechanisms,
    build_full_circuit_mechanism_definition_audit,
    generate_full_circuit_cudaq_teacher_dataset,
)
from scope_static.physical.channels import MechanismSpec


def _reset_cudaq_target_if_available() -> None:
    cudaq = pytest.importorskip("cudaq")
    if hasattr(cudaq, "reset_target"):
        cudaq.reset_target()


def test_full_circuit_cudaq_teacher_writes_literal_depth_artifact(tmp_path: Path) -> None:
    _reset_cudaq_target_if_available()

    result = generate_full_circuit_cudaq_teacher_dataset(
        {
            "num_qubits": 2,
            "circuit_depth": 3,
            "probe_set": "base",
            "mechanism_set": ["M8"],
            "balanced_min_instances_per_mechanism": 2,
            "shots": 8,
            "seed": 0,
            "cudaq_target": "",
            "full_circuit_cudaq_progress_logging": False,
        },
        output_dir=tmp_path / "teacher",
    )

    assert result["teacher_model"] == "full_circuit_cudaq"
    assert result["circuit_depth"] == 3
    assert result["configured_circuit_depth"] == 3
    assert result["effective_circuit_depth"] == 3
    assert result["circuit_depth_semantics"] == "literal_full_n_qubit_cudaq_schedule"
    assert result["rzz_implementation"] == "cx_rz_cx"
    assert result["rzz_gate_semantics"] == "logical_rzz_unitary_with_post_rzz_mechanism_channel"
    assert result["num_circuit_batches"] == 2
    assert result["mechanism_counts"] == {"M8": 2}
    observations = np.load(tmp_path / "teacher" / "observations.npz")
    assert observations["observations"].shape == (6, 8, 2)
    audit = json.loads((tmp_path / "teacher" / "sampling_audit.json").read_text())
    assert audit["teacher_model"] == "full_circuit_cudaq"
    assert audit["completed_probe_circuits"] == 6
    assert audit["cpu_fallback_allowed"] is False
    assert _cudaq_target_looks_gpu(audit["cudaq_target"], audit["cudaq_target_description"])
    assert audit["configured_circuit_depth"] == 3
    assert audit["effective_circuit_depth"] == 3
    assert audit["rzz_implementation"] == "cx_rz_cx"
    assert audit["noise_model_excluded_operations"] == ["cx", "rz"]
    assert audit["contract_note"] == "Samples literal n-qubit noisy circuits at configured gate depth."
    progress = json.loads((tmp_path / "teacher" / "sampling_progress.json").read_text())
    assert progress["completed"] is True
    assert progress["completed_probe_circuits"] == 6
    noise = json.loads((tmp_path / "teacher" / "noise_application_audit.json").read_text())
    assert noise["teacher_model"] == "full_circuit_cudaq"
    assert noise["rzz_implementation"] == "cx_rz_cx"
    assert noise["mechanism_application_convention"] == "post_gate_or_post_reset_channel_at_scheduled_location"
    definition = json.loads((tmp_path / "teacher" / "mechanism_definition_audit.json").read_text())
    assert definition["passed"] is True
    assert result["mechanism_definition_audit_passed"] is True
    cptp = json.loads((tmp_path / "teacher" / "cptp_guardrail_audit.json").read_text())
    assert cptp["passed"] is True
    assert result["cptp_guardrail_passed"] is True


def test_full_circuit_gpu_target_guard_rejects_cpu_target_description() -> None:
    assert _cudaq_target_looks_gpu("nvidia", "simulator=cusvsim_fp32")
    assert _cudaq_target_looks_gpu("tensornet", "cuTensorNet simulator backend")
    assert not _cudaq_target_looks_gpu("qpp-cpu", "CPU-only statevector simulator")


def test_full_circuit_cudaq_teacher_resumes_completed_probe_checkpoints(tmp_path: Path) -> None:
    _reset_cudaq_target_if_available()
    output = tmp_path / "teacher"
    config = {
        "num_qubits": 2,
        "circuit_depth": 2,
        "probe_set": "base",
        "mechanism_set": ["M8"],
        "balanced_min_instances_per_mechanism": 2,
        "shots": 16,
        "seed": 7,
        "cudaq_target": "",
        "full_circuit_cudaq_shot_batch_size": 4,
        "full_circuit_cudaq_progress_logging": False,
    }

    with pytest.raises(KeyboardInterrupt):
        generate_full_circuit_cudaq_teacher_dataset(
            {**config, "full_circuit_cudaq_interrupt_after_completed_probes": 2},
            output_dir=output,
        )

    partial_progress = json.loads((output / "sampling_progress.json").read_text())
    assert partial_progress["completed_probe_circuits_this_run"] == 2
    assert (output / "checkpoints" / "probe_000000.npz").exists()
    assert (output / "checkpoints" / "probe_000001.npz").exists()

    result = generate_full_circuit_cudaq_teacher_dataset(config, output_dir=output)

    assert result["teacher_model"] == "full_circuit_cudaq"
    audit = json.loads((output / "sampling_audit.json").read_text())
    assert audit["completed_probe_circuits"] == 6
    assert audit["skipped_resumed_probe_circuits"] >= 2
    assert audit["shot_batch_size"] == 4
    observations = np.load(output / "observations.npz")
    assert observations["observations"].shape == (6, 16, 2)


def test_full_circuit_weighted_mechanism_instance_counts_are_preserved() -> None:
    mechanisms, repetitions, sampling_contract = _build_full_circuit_oracle_mechanisms(
        {
            "num_qubits": 5,
            "mechanism_set": ["M0", "M8"],
            "balanced_min_instances_per_mechanism": 2,
            "mechanism_instance_counts": {"M0": 4, "M8": 1},
            "probe_set": "base",
        }
    )

    counts = {}
    for spec in mechanisms:
        counts[spec.mechanism_id] = counts.get(spec.mechanism_id, 0) + 1
    assert repetitions == 4
    assert sampling_contract == "weighted"
    assert counts == {"M0": 4, "M8": 1}


def test_m13_m14_operation_sites_and_definition_audit_are_explicit() -> None:
    mechanisms, repetitions, sampling_contract = _build_full_circuit_oracle_mechanisms(
        {
            "num_qubits": 10,
            "mechanism_set": ["M13", "M14"],
            "balanced_min_instances_per_mechanism": 6,
            "probe_set": "base",
        }
    )
    groups: dict[int, list[MechanismSpec]] = {}
    for spec in mechanisms:
        groups.setdefault(int(spec.circuit_id), []).append(spec)
    operation_sites_by_group = {
        circuit_id: _operation_sites_from_mechanisms(specs)
        for circuit_id, specs in groups.items()
    }

    audit = build_full_circuit_mechanism_definition_audit(
        mechanisms,
        operation_sites_by_group=operation_sites_by_group,
    )

    assert repetitions == 6
    assert sampling_contract == "balanced"
    assert audit["passed"] is True
    assert audit["m13_has_observed_drift_span"] is True
    assert audit["m14_operation_error_axes_distinct"] is True
    for record in audit["records"]:
        if record["oracle_label"] in {"M13", "M14"}:
            assert record["instruction"] == "rx"
            assert record["operation_axis"] == "rx"
            assert record["scheduled_operation_site_present"] is True
        if record["oracle_label"] == "M14":
            assert record["error_axis"] == "rz"


def test_decomposed_rzz_keeps_scheduled_rz_noise_inline() -> None:
    cudaq = pytest.importorskip("cudaq")
    spec = MechanismSpec(
        mechanism_id="M7",
        name="coherent_rz_overrotation",
        num_qubits=1,
        parameters={"epsilon": 0.01},
        instruction="rz",
        qubits=(0,),
    )

    inline, _noise_model, has_noise_model_channels = _mechanism_channels_by_location(
        cudaq,
        [spec],
        mode="hybrid",
        rzz_implementation="cx_rz_cx",
    )

    assert ("rz", (0,)) in inline
    assert has_noise_model_channels is False


def test_cx_rz_cx_rzz_matches_exp_pauli_statevector() -> None:
    cudaq = pytest.importorskip("cudaq")
    if not hasattr(cudaq, "get_state"):
        pytest.skip("CUDA-Q get_state is unavailable")
    if hasattr(cudaq, "reset_target"):
        cudaq.reset_target()

    def state_for(implementation: str) -> np.ndarray:
        kernel = cudaq.make_kernel()
        qubits = kernel.qalloc(2)
        schedule = _CudaqSchedule(kernel, qubits, {}, rzz_implementation=implementation)
        schedule.h(0)
        schedule.h(1)
        schedule.rzz(0.37, 0, 1)
        return np.asarray(cudaq.get_state(kernel), dtype=np.complex128)

    reference = state_for("exp_pauli")
    decomposed = state_for("cx_rz_cx")
    phase = np.vdot(reference, decomposed)
    if abs(phase) > 0.0:
        phase /= abs(phase)
    assert np.linalg.norm(reference * phase - decomposed) < 1e-6

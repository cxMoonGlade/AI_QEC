from __future__ import annotations

import json
from pathlib import Path
import sys
import types

import numpy as np
import pytest
import yaml

from scope_static.experiments.run_s2d_oracle_separability import run_s2d_oracle_separability
from scope_static.experiments.run_s2d_physical_teacher import run_s2d_physical_teacher
from scope_static.experiments.run_s2d_preflight import run_s2d_preflight
from scope_static.numerics import NUMERICAL_ZERO
from scope_static.physical.preflight import audit_aer_backend
from scope_static.physical.teacher import (
    _counts_to_bit_matrix,
    _sample_circuits,
    build_default_oracle_mechanisms,
    resolve_aer_simulator_settings,
)


def test_s2d_preflight_writes_backend_audit(tmp_path: Path) -> None:
    audit = run_s2d_preflight(output_dir=tmp_path / "S2D_PHYS0_preflight")

    assert audit["schema"] == "scope_static_s2d_backend_audit_v1"
    assert audit["backend_policy"]["priority"] == ["qiskit-aer-gpu", "qiskit-aer"]
    assert "qiskit-aer-gpu" in audit["packages"]
    assert "tiny_density_matrix_gpu_simulation" in audit
    if bool(audit["backend_usable"]):
        assert audit["tiny_density_matrix_gpu_simulation"]["passed"] is True
    assert (tmp_path / "S2D_PHYS0_preflight" / "backend_audit.json").exists()
    assert (tmp_path / "S2D_PHYS0_preflight" / "backend_audit.md").exists()


def test_default_oracle_mechanisms_include_required_labels() -> None:
    labels = [spec.mechanism_id for spec in build_default_oracle_mechanisms()]

    assert {"M0", "M1", "M2", "M3", "M4", "M13", "M14", "M15", "M16"} <= set(labels)


def test_aer_simulator_auto_uses_mps_tensor_network_for_phys15() -> None:
    small = resolve_aer_simulator_settings({"profile": "phys9_chain"})
    large = resolve_aer_simulator_settings({"profile": "phys15_chain"})
    larger = resolve_aer_simulator_settings({"profile": "phys20_chain"})

    assert small["method"] == "density_matrix"
    assert small["selection_reason"] == "auto_small_qubit_density_matrix"
    assert large["method"] == "matrix_product_state"
    assert large["device"] == "GPU"
    assert large["options"] == {"matrix_product_state_truncation_threshold": NUMERICAL_ZERO}
    assert large["selection_reason"] == "auto_large_qubit_tensor_network"
    assert larger["method"] == "matrix_product_state"
    assert larger["num_qubits"] == 20


def test_aer_simulator_allows_explicit_tensor_network_method() -> None:
    settings = resolve_aer_simulator_settings(
        {
            "profile": "phys15_chain",
            "aer_simulation_method": "tensor-network",
        }
    )

    assert settings["method"] == "tensor_network"
    assert settings["selection_reason"] == "explicit_aer_simulation_method"


def test_aer_simulator_options_do_not_duplicate_method_or_device() -> None:
    settings = resolve_aer_simulator_settings(
        {
            "profile": "phys15_chain",
            "aer_simulator_options": {
                "method": "tensor_network",
                "device": "GPU",
                "matrix_product_state_truncation_threshold": NUMERICAL_ZERO,
                "shot_branching_enable": True,
                "not_an_aer_option": 1,
            },
        }
    )

    assert settings["method"] == "tensor_network"
    assert settings["device"] == "GPU"
    assert settings["options"] == {"matrix_product_state_truncation_threshold": NUMERICAL_ZERO, "shot_branching_enable": True}


def test_counts_to_bit_matrix_materializes_grouped_counts_with_numpy_repeat() -> None:
    rows = _counts_to_bit_matrix({"00": 2, "11": 1, "0x2": 2}, shots=5, num_bits=2)

    assert rows.dtype == np.uint8
    assert rows.shape == (5, 2)
    assert rows.tolist() == [[0, 0], [0, 0], [0, 1], [0, 1], [1, 1]]


def test_sample_circuits_batches_aer_jobs_and_reports_wall_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeResult:
        def __init__(self, counts_by_circuit: list[dict[str, int]]) -> None:
            self._counts_by_circuit = counts_by_circuit

        def get_counts(self, index=None):
            if index is None:
                return self._counts_by_circuit[0]
            return self._counts_by_circuit[int(index)]

    class FakeJob:
        def __init__(self, counts_by_circuit: list[dict[str, int]]) -> None:
            self._counts_by_circuit = counts_by_circuit

        def result(self):
            return FakeResult(self._counts_by_circuit)

    class FakeAerSimulator:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def run(self, circuits, *, shots: int, seed_simulator: int):
            batch = list(circuits) if isinstance(circuits, list) else [circuits]
            calls.append({"batch_len": len(batch), "shots": shots, "seed": seed_simulator})
            counts = [{"0": shots // 2, "1": shots - shots // 2} for _ in batch]
            return FakeJob(counts)

    monkeypatch.setitem(sys.modules, "qiskit_aer", types.SimpleNamespace(AerSimulator=FakeAerSimulator))

    observations, warning_records, audit = _sample_circuits(
        ["c0", "c1", "c2", "c3", "c4"],
        {
            "num_qubits": 1,
            "shots": 7,
            "seed": 11,
            "backend": "qiskit_aer_gpu",
            "aer_sampling_mode": "batch",
            "aer_sampling_job_batch_size": 2,
        },
        noise_model=None,
    )

    assert observations.shape == (5, 7, 1)
    assert warning_records == []
    assert [call["batch_len"] for call in calls] == [2, 2, 1]
    assert [call["seed"] for call in calls] == [11, 12, 13]
    assert audit["schema"] == "scope_static_s2d_phys1_sampling_audit_v1"
    assert audit["mode"] == "batch"
    assert audit["num_jobs"] == 3
    assert audit["job_batch_size"] == 2
    assert audit["aer_options"]["max_parallel_experiments"] == 2
    assert audit["aer_sampling_option_defaults"] == {"max_parallel_experiments": 2}
    assert audit["total_requested_shots"] == 35
    assert audit["seed_policy"] == "one_seed_per_aer_job"
    assert audit["count_materialization"] == "grouped_counts_np_repeat"
    assert audit["metrics_are_wall_clock"] is True
    assert audit["sampling_wall_clock_seconds"] >= 0.0
    assert audit["materialization_wall_clock_seconds"] >= 0.0
    assert audit["total_wall_clock_seconds"] >= 0.0


def test_sample_circuits_keeps_per_circuit_mode_for_legacy_reproducibility(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeResult:
        def get_counts(self):
            return {"0": 2, "1": 2}

    class FakeJob:
        def result(self):
            return FakeResult()

    class FakeAerSimulator:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def run(self, circuits, *, shots: int, seed_simulator: int):
            calls.append({"is_list": isinstance(circuits, list), "shots": shots, "seed": seed_simulator})
            return FakeJob()

    monkeypatch.setitem(sys.modules, "qiskit_aer", types.SimpleNamespace(AerSimulator=FakeAerSimulator))

    observations, _, audit = _sample_circuits(
        ["c0", "c1", "c2"],
        {
            "num_qubits": 1,
            "shots": 4,
            "seed": 19,
            "backend": "qiskit_aer_gpu",
            "aer_sampling_mode": "per_circuit",
        },
        noise_model=None,
    )

    assert observations.shape == (3, 4, 1)
    assert [call["is_list"] for call in calls] == [False, False, False]
    assert [call["seed"] for call in calls] == [19, 20, 21]
    assert audit["mode"] == "per_circuit"
    assert audit["num_jobs"] == 3
    assert audit["job_batch_size"] == 1
    assert audit["seed_policy"] == "seed_plus_circuit_index"


def test_s2d_teacher_generation_writes_noise_application_audit_when_gpu_available(tmp_path: Path) -> None:
    audit = audit_aer_backend(backend="qiskit_aer_gpu", require_gpu=True, allow_cpu_aer_fallback=False)
    if not bool(audit["backend_usable"]):
        pytest.skip(f"qiskit-aer-gpu preflight is not usable here: {audit.get('errors')}")
    config_path = tmp_path / "s2d_phys.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "s2d_physical": {
                    "shots": 32,
                    "num_qubits": 5,
                    "include_m5": True,
                    "backend": "qiskit_aer_gpu",
                    "require_gpu": True,
                    "allow_cpu_aer_fallback": False,
                }
            }
        )
    )
    result = run_s2d_physical_teacher(
        config_path,
        output_dir=tmp_path / "S2D_PHYS1_teacher",
        preflight_dir=tmp_path / "S2D_PHYS0_preflight",
    )

    assert {"M0", "M1", "M2", "M3", "M4", "M13", "M14", "M15", "M16"} <= set(result["mechanism_counts"])
    noise_audit = json.loads((tmp_path / "S2D_PHYS1_teacher" / "noise_application_audit.json").read_text())
    assert noise_audit["schema"] == "scope_static_s2d_noise_application_audit_v1"
    assert noise_audit["uses_oracle_labels_for_training"] is False
    assert noise_audit["uses_oracle_labels_for_selection"] is False
    assert {record["oracle_label"] for record in noise_audit["records"]} >= {"M0", "M1", "M2", "M3", "M4", "M13", "M14", "M15", "M16"}
    assert all(record["qiskit_application_api"] == "add_readout_error" for record in noise_audit["records"] if record["oracle_label"] in {"M13", "M14", "M15", "M16"})
    assert all(record["qiskit_application_api"] == "add_quantum_error" for record in noise_audit["records"] if record["oracle_label"] == "M4")
    non_clifford = json.loads((tmp_path / "S2D_PHYS1_teacher" / "non_clifford_audit.json").read_text())
    assert non_clifford["schema"] == "scope_static_s2d_non_clifford_audit_v1"
    assert non_clifford["non_clifford_teacher"] is True
    assert any(record["gate"] == "rzz" and record["source"] == "oracle_noise" for record in non_clifford["non_clifford_sources"])
    assert any(record["gate"] == "rzz" and record["source"] == "ideal_probe_circuit" for record in non_clifford["non_clifford_sources"])
    sampling_audit = json.loads((tmp_path / "S2D_PHYS1_teacher" / "sampling_audit.json").read_text())
    assert sampling_audit["schema"] == "scope_static_s2d_phys1_sampling_audit_v1"
    assert sampling_audit["mode"] == "batch"
    assert sampling_audit["metrics_are_wall_clock"] is True
    observations = np.load(tmp_path / "S2D_PHYS1_teacher" / "observations.npz")
    assert observations["observations"].ndim == 3


def test_s2d_oracle_separability_writes_artifacts(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYS1_teacher"
    teacher.mkdir()
    records = []
    specs = build_default_oracle_mechanisms({"include_m5": True, "num_qubits": 5})
    for idx, spec in enumerate(specs):
        records.append({"location_id": idx, **spec.audit_dict(), "oracle_label": spec.mechanism_id})
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}))

    out = tmp_path / "S2D_PHYS2_oracle_separability"
    result = run_s2d_oracle_separability(teacher_dir=teacher, output_dir=out)

    assert result["stage"] == "S2D_PHYS2_oracle_separability"
    assert result["ari_nmi_used_for_selection"] is False
    assert result["separability_gate"] in {"identifying", "limited_but_usable", "probe_set_insufficient"}
    assert result["fingerprint_families"]["probe_response"]["source"] == "oracle_channel_probe_responses"
    assert result["fingerprint_families"]["rzz_type_features"]["feature_names"] == [
        "rzz_type1_commuting_fixed_fraction",
        "rzz_type2_two_entry_rotation_fraction",
        "rzz_type3_nonclifford_rotation_strength",
        "rzz_type4_hard_residual_leakage",
    ]
    assert (out / "fingerprints.npy").exists()
    assert (out / "ptm_fingerprints.npy").exists()
    assert (out / "probe_fingerprints.npy").exists()
    assert (out / "rzz_type_features.npy").exists()
    assert np.load(out / "fingerprints.npy").ndim == 2
    assert (out / "metrics.json").exists()
    assert (out / "confusion_matrix.json").exists()
    assert (out / "summary.md").exists()


def test_aer_gpu_execution_preflight_when_available() -> None:
    audit = audit_aer_backend(backend="qiskit_aer_gpu", require_gpu=True, allow_cpu_aer_fallback=False)
    if not bool(audit["backend_usable"]):
        pytest.skip(f"qiskit-aer-gpu preflight is not usable here: {audit.get('errors')}")
    assert audit["gpu_simulator_constructed"] is True
    assert audit["simulator_device"] == "GPU"

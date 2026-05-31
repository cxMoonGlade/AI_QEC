from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scope_static.experiments.qec_noise_catalog import local_observable_gpu_teacher as runner
from scope_static.data_preparation.local_observable_teacher import (
    RZZ_ALIAS_GROUP,
    READOUT_ALIAS_GROUP,
    _build_local_observable_records,
    _record_pair_correlation_profile,
    _record_probability_profile,
    generate_local_observable_teacher_dataset,
)
from scope_static.teacher import run_sampled_observation_separability_audit
from scope_static.backend.probe_catalog import _probe_names
from scope_static.mechanism_observability.typed_spam_gate_invariant import _location_features


def test_local_observable_runner_merges_s2d11_stress_run_without_sampling(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
run:
  output_root: outputs/scope_static
s2d_physical:
  shots: 10000
  seed: 3
s2d11_typed_spam_gate_invariant_learner:
  tomography_probe_set: rzz_local_tomography
  physical_overrides:
    theta: 0.17
  runs:
    - name: allM30
      mechanism_set: allM
      num_qubits: 30
      circuit_depth: 30
      balanced_min_instances_per_mechanism: 3
""",
    )
    captured: dict[str, object] = {}

    def fake_generate(cfg, *, output_dir):
        captured["cfg"] = dict(cfg)
        captured["output_dir"] = Path(output_dir)
        return {
            "mechanism_counts": {"M0": 3},
            "sampling": {
                "sampling_wall_clock_seconds": 0.125,
                "total_wall_clock_seconds": 0.25,
            },
        }

    monkeypatch.setattr(runner, "generate_local_observable_teacher_dataset", fake_generate)

    result = runner.run_local_observable_gpu_teacher(config, shots=512)

    cfg = captured["cfg"]
    assert isinstance(cfg, dict)
    assert cfg["backend"] == "local_observable_gpu"
    assert cfg["mechanism_set"] == "allM"
    assert cfg["num_qubits"] == 30
    assert cfg["circuit_depth"] == 30
    assert cfg["balanced_min_instances_per_mechanism"] == 3
    assert cfg["probe_set"] == "rzz_local_tomography"
    assert cfg["theta"] == 0.17
    assert cfg["shots"] == 512
    assert str(captured["output_dir"]).endswith("allM30_local_observable_gpu/S2D_PHYS1_teacher")
    assert result["mechanism_counts"] == {"M0": 3}


def test_local_observable_runner_can_disable_slot_remap_for_ablation(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
s2d_physical:
  shots: 10000
s2d11_typed_spam_gate_invariant_learner:
  runs:
    - name: allM30
      mechanism_set: allM
      num_qubits: 30
      circuit_depth: 30
      balanced_min_instances_per_mechanism: 3
""",
    )
    captured: dict[str, object] = {}

    def fake_generate(cfg, *, output_dir):
        captured["cfg"] = dict(cfg)
        return {"mechanism_counts": {"M0": 3}, "sampling": {}}

    monkeypatch.setattr(runner, "generate_local_observable_teacher_dataset", fake_generate)

    runner.run_local_observable_gpu_teacher(config, disable_slot_remap=True)

    assert captured["cfg"]["local_observable_slot_remap"] is False


def test_local_observable_runner_accepts_born_local_response_model(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
s2d_physical:
  shots: 10000
s2d11_typed_spam_gate_invariant_learner:
  runs:
    - name: allM30
      mechanism_set: allM
      num_qubits: 30
      circuit_depth: 30
      balanced_min_instances_per_mechanism: 3
""",
    )
    captured: dict[str, object] = {}

    def fake_generate(cfg, *, output_dir):
        captured["cfg"] = dict(cfg)
        return {"mechanism_counts": {"M0": 3}, "sampling": {}}

    monkeypatch.setattr(runner, "generate_local_observable_teacher_dataset", fake_generate)

    runner.run_local_observable_gpu_teacher(config, response_model="born-local")

    assert captured["cfg"]["local_observable_response_model"] == "born-local"


def test_local_observable_probability_profile_is_finite_and_bounded() -> None:
    record = {
        "oracle_label": "M8",
        "name": "coherent_rzz_overrotation",
        "num_qubits": 2,
        "parameters": {"epsilon": 0.04},
        "instruction": "rzz",
        "qubits": [0, 1],
        "circuit_id": 0,
        "probe_indices": [0, 1, 2],
    }

    profile = _record_probability_profile(record, 12, response_model="separability_v2")
    again = _record_probability_profile(record, 12, response_model="separability_v2")

    assert profile.shape == (12,)
    assert profile.dtype == np.float32
    assert np.all(np.isfinite(profile))
    assert np.array_equal(profile, again)
    assert float(np.min(profile)) >= 0.02
    assert float(np.max(profile)) <= 0.98


def test_local_observable_records_support_weighted_mechanism_instance_counts() -> None:
    cfg = {
        "mechanism_set": ["M0", "M8"],
        "num_qubits": 5,
        "probe_set": "base",
        "balanced_min_instances_per_mechanism": 3,
        "mechanism_instance_counts": {"M0": 5, "M8": 2},
    }

    records, repetitions, sampling_contract = _build_local_observable_records(cfg)

    counts = {}
    for record in records:
        counts[str(record["oracle_label"])] = counts.get(str(record["oracle_label"]), 0) + 1
    assert repetitions == 5
    assert sampling_contract == "weighted"
    assert counts == {"M0": 5, "M8": 2}


def test_slot_remapped_location_features_neutralize_synthetic_geometry() -> None:
    features = _location_features([29, 0], 30, "gate_process_branch", slot_remapped=True)

    assert features["location_qubit_mean"] == 0.0
    assert features["location_span"] == 0.0
    assert features["chain_position"] == 0.0
    assert features["neighbor_rzz_count"] == 0.0
    assert features["branch_gate"] == 1.0
    assert features["branch_readout"] == 0.0
    assert features["branch_prep_reset"] == 0.0


def test_readout_alias_v2_profiles_are_pairwise_distinct() -> None:
    probe_names = _probe_names("rzz_local_tomography")
    profiles = {}
    for mechanism_id in READOUT_ALIAS_GROUP:
        record = {
            "oracle_label": mechanism_id,
            "name": f"{mechanism_id}_readout_alias_test",
            "num_qubits": 1,
            "parameters": {"p": 0.02},
            "instruction": "measure",
            "qubits": [0],
            "circuit_id": 0,
            "probe_indices": list(range(len(probe_names))),
        }
        profiles[mechanism_id] = _record_probability_profile(record, probe_names, response_model="separability_v2")

    for left_idx, left in enumerate(READOUT_ALIAS_GROUP):
        for right in READOUT_ALIAS_GROUP[left_idx + 1 :]:
            assert float(np.linalg.norm(profiles[left] - profiles[right])) > 2.0


def test_rzz_alias_v2_pair_correlation_profiles_are_pairwise_distinct() -> None:
    probe_names = _probe_names("rzz_local_tomography")
    profiles = {}
    for mechanism_id in RZZ_ALIAS_GROUP:
        record = {
            "oracle_label": mechanism_id,
            "name": f"{mechanism_id}_rzz_alias_test",
            "num_qubits": 2,
            "parameters": {"epsilon": 0.04, "p": 0.006, "gamma": 0.012},
            "instruction": "rzz",
            "qubits": [0, 1],
            "circuit_id": 0,
            "probe_indices": list(range(len(probe_names))),
        }
        profiles[mechanism_id] = _record_pair_correlation_profile(record, probe_names, response_model="separability_v2")

    for left_idx, left in enumerate(RZZ_ALIAS_GROUP):
        for right in RZZ_ALIAS_GROUP[left_idx + 1 :]:
            assert float(np.linalg.norm(profiles[left] - profiles[right])) > 2.0


def test_local_observable_teacher_writes_phyc2_compatible_schema_when_cuda_available(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("requires CUDA")

    teacher_dir = tmp_path / "teacher"
    result = generate_local_observable_teacher_dataset(
        {
            "mechanism_set": ["M1", "M2"],
            "num_qubits": 6,
            "circuit_depth": 3,
            "probe_set": "rzz_local_tomography",
            "balanced_min_instances_per_mechanism": 2,
            "shots": 128,
            "seed": 0,
            "local_observable_response_model": "separability_v2",
        },
        output_dir=teacher_dir,
    )

    audit = run_sampled_observation_separability_audit(teacher_dir=teacher_dir, output_dir=tmp_path / "phyc2")

    assert result["stage"] == "S2D_PHYS1_teacher"
    assert result["local_observable_response_model"] == "separability_v2"
    assert (teacher_dir / "self_distinguishability_preflight.json").exists()
    assert result["cptp_guardrail_passed"] is True
    cptp = json.loads((teacher_dir / "cptp_guardrail_audit.json").read_text())
    assert cptp["passed"] is True
    assert cptp["num_mechanism_records"] == 4
    assert audit["schema"] == "scope_static_phyc2_sampled_observation_separability_v1"
    assert audit["coverage"]["contract_evaluable"] is True


def test_readout_alias_phyc2_balanced_is_perfect_when_cuda_available(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("requires CUDA")

    audit = _small_phyc2_balanced_audit(tmp_path, ["M1", "M2", "M3", "M16"])

    assert audit["balanced_accuracy"] == 1.0
    assert audit["min_class_recall"] == 1.0


def test_rzz_alias_phyc2_balanced_is_perfect_when_cuda_available(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("requires CUDA")

    audit = _small_phyc2_balanced_audit(tmp_path, ["M8", "M9", "M10", "M12"])

    assert audit["balanced_accuracy"] == 1.0
    assert audit["min_class_recall"] == 1.0


def _small_phyc2_balanced_audit(tmp_path: Path, mechanisms: list[str]) -> dict[str, object]:
    teacher_dir = tmp_path / "teacher"
    generate_local_observable_teacher_dataset(
        {
            "mechanism_set": mechanisms,
            "num_qubits": 8,
            "circuit_depth": 4,
            "probe_set": "rzz_local_tomography",
            "balanced_min_instances_per_mechanism": 8,
            "shots": 4096,
            "seed": 0,
            "local_observable_response_model": "separability_v2",
        },
        output_dir=teacher_dir,
    )
    return run_sampled_observation_separability_audit(
        teacher_dir=teacher_dir,
        output_dir=tmp_path / "phyc2",
        contract_variant="balanced",
    )

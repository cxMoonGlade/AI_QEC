from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from scope_static.primitives.preflight import audit_cudaq_backend
from scope_static.catalog_pipeline import (
    load_phys1_teacher_artifact,
    load_phys2_metrics,
    load_phys3_metrics,
    catalog_pipeline_paths,
    run_catalog_pipeline,
)
from scope_static.catalog_pipeline import pipeline as pipeline_mod


def test_catalog_pipeline_paths_and_artifact_loaders(tmp_path: Path) -> None:
    paths = catalog_pipeline_paths(tmp_path)
    paths.teacher_dir.mkdir()
    paths.separability_dir.mkdir()
    paths.local_inverse_dir.mkdir()
    (paths.teacher_dir / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": [{"oracle_label": "M0"}]}) + "\n")
    np.savez_compressed(
        paths.teacher_dir / "observations.npz",
        observations=np.zeros((2, 3, 4), dtype=np.uint8),
        probe_names=np.asarray(["z_basis", "x_measure"]),
        shots=np.asarray([3], dtype=np.int64),
    )
    (paths.separability_dir / "metrics.json").write_text(json.dumps({"ari": 1.0, "nmi": 1.0}) + "\n")
    (paths.local_inverse_dir / "metrics.json").write_text(json.dumps({"s2d3_result": "ok"}) + "\n")

    teacher = load_phys1_teacher_artifact(paths.teacher_dir)

    assert paths.preflight_dir.name == "S2D_PHYS0_preflight"
    assert teacher["num_locations"] == 1
    assert teacher["observations_shape"] == [2, 3, 4]
    assert load_phys2_metrics(paths.separability_dir)["ari"] == 1.0
    assert load_phys3_metrics(paths.local_inverse_dir)["s2d3_result"] == "ok"


def test_catalog_pipeline_runs_all_stages_when_teacher_self_passes(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    _patch_pipeline_adapters(monkeypatch, calls=calls, phys2_ari=1.0, phys2_nmi=1.0)

    result = run_catalog_pipeline({"shots": 8}, output_dir=tmp_path, bootstrap_replicates=2, random_baseline_trials=3)

    assert calls == ["PHYS1", "PHYS2", "PHYS3"]
    assert result["verdicts"]["teacher_self_verdict"] == "teacher_self_distinguishable"
    assert result["verdicts"]["overall_diagnosis"] == "strong_recovery"
    assert result["learner"]["ran"] is True
    assert (tmp_path / "catalog_pipeline.json").exists()
    assert (tmp_path / "catalog_pipeline.md").exists()


def test_catalog_pipeline_skips_learner_when_teacher_self_is_probe_limited(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    _patch_pipeline_adapters(monkeypatch, calls=calls, phys2_ari=0.2, phys2_nmi=0.3)

    result = run_catalog_pipeline({"shots": 8}, output_dir=tmp_path)

    assert calls == ["PHYS1", "PHYS2"]
    assert result["verdicts"]["teacher_self_verdict"] == "teacher_self_probe_limited"
    assert result["verdicts"]["overall_diagnosis"] == "probe_limited"
    assert result["learner"]["ran"] is False
    assert result["learner"]["skip_reason"] == "teacher_self_probe_limited"


def test_catalog_pipeline_always_mode_runs_learner_for_diagnostics(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    _patch_pipeline_adapters(monkeypatch, calls=calls, phys2_ari=0.2, phys2_nmi=0.3)

    result = run_catalog_pipeline({"shots": 8}, output_dir=tmp_path, run_local_inverse="always")

    assert calls == ["PHYS1", "PHYS2", "PHYS3"]
    assert result["learner"]["ran"] is True
    assert result["verdicts"]["overall_diagnosis"] == "probe_limited"


def test_catalog_pipeline_real_small_smoke_when_gpu_available(tmp_path: Path) -> None:
    if os.environ.get("AIQEC_RUN_CUDAQ_SMOKE") != "1":
        pytest.skip("set AIQEC_RUN_CUDAQ_SMOKE=1 to run CUDA-Q catalog pipeline smoke")
    audit = audit_cudaq_backend(backend="cudaq", require_gpu=True)
    if not bool(audit["backend_usable"]):
        pytest.skip(f"CUDA-Q preflight is not usable here: {audit.get('errors')}")
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("local sampled teacher requires torch CUDA")

    result = run_catalog_pipeline(
        {
            "profile": "phys5_chain",
            "mechanism_set": ["M1", "M2"],
            "shots": 16,
            "seed": 2,
            "backend": "cudaq",
            "require_gpu": True,
            "local_observable_response_model": "born_local",
            "balanced_min_instances_per_mechanism": 2,
        },
        output_dir=tmp_path,
        bootstrap_replicates=1,
        random_baseline_trials=1,
        run_local_inverse="always",
    )

    assert result["teacher"]["num_qubits"] == 5
    assert result["teacher_self"]["oracle_label_names"]
    assert result["learner"]["ran"] is True
    assert (tmp_path / "catalog_pipeline.json").exists()


def _patch_pipeline_adapters(monkeypatch, *, calls: list[str], phys2_ari: float, phys2_nmi: float) -> None:
    def fake_teacher(config, *, output_dir, preflight_dir):
        calls.append("PHYS1")
        Path(output_dir).mkdir(parents=True)
        Path(preflight_dir).mkdir(parents=True)
        return {
            "stage": "S2D_PHYS1_teacher",
            "output_dir": str(output_dir),
            "num_probes": 3,
            "num_qubits": 5,
            "shots": int(config.get("shots", 8)),
            "mechanism_counts": {"M0": 1},
            "cudaq_backend": {"target": "nvidia", "gpu_count": 1},
        }

    def fake_phys2(*, teacher_dir, output_dir, paper_informed):
        calls.append("PHYS2")
        Path(output_dir).mkdir(parents=True)
        return {
            "ari": phys2_ari,
            "nmi": phys2_nmi,
            "active_clusters": 2,
            "separability_gate": "identifying" if min(phys2_ari, phys2_nmi) >= 0.9 else "probe_set_insufficient",
            "oracle_label_names": ["M0", "M1"],
            "feature_shape": [2, 4],
            "num_locations": 2,
            "pairwise_mechanism_distance": {"M0/M1": 1.0},
        }

    def fake_phys3(*, teacher_dir, separability_dir, output_dir, config):
        calls.append("PHYS3")
        Path(output_dir).mkdir(parents=True)
        return {
            "s2d3_result": "catalog_validation_strong_recovery",
            "acceptance_label": "catalog_validation_strong_recovery",
            "num_clusters": 2,
            "main_result": {"ari": 0.9, "nmi": 0.9, "active_clusters": 2},
            "physical_local_inverse_probability_v2_result": {"ari": 0.9, "nmi": 0.9},
            "direct_S_alpha_result": {"ari": 0.1, "nmi": 0.2},
            "oracle_fingerprint_upper_bound": {"ari": 1.0, "nmi": 1.0},
            "bootstrap_nmi": {"min_vs_full": 0.9, "labels": [[0, 1]]},
            "prediction_metrics": {},
            "nll_difficulty_audit": {},
            "key_comparison": {},
            "comparisons": [],
        }

    monkeypatch.setattr(pipeline_mod, "_generate_teacher_dataset", fake_teacher)
    monkeypatch.setattr(pipeline_mod, "_run_oracle_separability_audit", fake_phys2)
    monkeypatch.setattr(pipeline_mod, "_run_mechanism_observability_recovery", fake_phys3)

import json

import pytest
import yaml

from scope_static.experiments.plan import ExperimentPlan
from scope_static.experiments.run_static import run_experiment


def test_smoke_experiment_writes_claim_boundary_metadata(tmp_path):
    config = {
        "run": {"name": "smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
        "circuit": {
            "family": "surface_code:rotated_memory_x",
            "distance": 3,
            "rounds": 1,
            "noise": {
                "after_clifford_depolarization": 0.001,
                "after_reset_flip_probability": 0.001,
                "before_measure_flip_probability": 0.001,
                "before_round_data_depolarization": 0.001,
            },
        },
        "graph": {"canonicalize_duplicate_masks": True, "residual_ranks": [0, 1]},
        "experiment": {
            "seeds": [0],
            "teacher_modes": ["exact_orbit"],
            "epsilon_breaks": [0.0],
            "shot_budgets": [64],
            "heldout_shots": 128,
            "threshold_epsilon": 0.1,
            "teacher_residual_rank": 1,
        },
        "training": {
            "models": ["dmle_qec", "soft_feature_orbit"],
            "model_options": {
                "dmle_qec": {"perturb_scale": 0.0},
                "soft_feature_orbit": {"beta_l2": 0.001},
            },
            "steps": 3,
            "lr": 0.05,
            "aggregate_unique": True,
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_experiment(config_path)
    assert result["dem_fault_logit_claim"] is True
    assert result["cptp_gksl_claim"] is False
    assert result["num_observation_bits_B"] > 0
    assert result["residual_ranks"] == [0, 1]
    assert result["teacher_residual_rank"] == 1
    assert result["num_model_fit_cache_hits"] >= 1
    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text())
    assert metrics["records"]
    assert metrics["records"][0]["baseline_family"] == "dmle_qec"
    assert metrics["records"][0]["baseline_source_repository"] == "https://github.com/cxMoonGlade/DMLE-QEC"
    assert metrics["records"][0]["train_observation_mode"] == "detectors"
    assert metrics["records"][0]["evidence_record_schema"] == "scope_static_v1"
    assert metrics["records"][0]["train_likelihood_adapter"] == "pytorch_detector_exact"
    assert metrics["records"][0]["train_likelihood_gpu_batch_available"] is False
    important = metrics["important_results"]
    assert important["schema"] == "scope_static_important_results_v1"
    assert important["run"]["num_records"] == len(metrics["records"])
    assert important["run"]["num_model_fits_executed"] == metrics["num_model_fits_executed"]
    assert important["run"]["num_model_fit_cache_hits"] == metrics["num_model_fit_cache_hits"]
    assert important["run"]["num_model_fit_requests"] == (
        metrics["num_model_fits_executed"] + metrics["num_model_fit_cache_hits"]
    )
    assert important["run"]["model_fit_cache_hit_rate"] > 0.0
    assert {"value": "pytorch_detector_exact", "count": 2} in important["run"]["train_likelihood_adapter_counts"]
    assert [row["residual_rank"] for row in important["compression_by_rank"]] == [0, 1]
    assert important["best_by_teacher_case_at_max_shots"]
    assert important["best_by_teacher_case_and_shots"]
    assert important["model_rank_summary"]
    assert important["threshold_summary"]["threshold_table"]
    assert metrics["config_stem"] == "config"
    assert metrics["output_dir_overridden"] is False
    assert {record["residual_rank"] for record in metrics["records"]} == {0, 1}
    assert {record["residual_rank"] for record in metrics["shots_to_threshold"]} == {0, 1}
    assert metrics["records"][0]["train_likelihood_objective"] == "global_exact"
    assert metrics["records"][0]["P_local"] >= metrics["records"][0]["P_hard"]
    assert "soft_compressed" in metrics["records"][0]
    soft_records = [record for record in metrics["records"] if record["model"] == "soft_feature_orbit"]
    assert soft_records
    assert all(record["train_regularization_weight"] == 0.001 for record in soft_records)
    assert metrics["records"][0]["train_final_nll"] <= metrics["records"][0]["train_initial_nll"]


def test_local_window_objective_records_window_and_compression_metadata(tmp_path):
    config = {
        "run": {"name": "window_smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
        "circuit": {
            "family": "surface_code:rotated_memory_x",
            "distance": 3,
            "rounds": 1,
            "noise": {
                "after_clifford_depolarization": 0.001,
                "after_reset_flip_probability": 0.001,
                "before_measure_flip_probability": 0.001,
                "before_round_data_depolarization": 0.001,
            },
        },
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 1},
        "windows": {
            "enabled": True,
            "builders": ["detector_geometry", "orbits"],
            "include_radius1": False,
            "max_window_bits": 3,
        },
        "experiment": {
            "seeds": [0],
            "teacher_cases": [{"mode": "exact_orbit", "epsilon_break": 0.0}],
            "shot_budgets": [64],
            "heldout_shots": 128,
            "threshold_epsilon": 0.1,
        },
        "training": {
            "models": ["hard_orbit"],
            "steps": 2,
            "lr": 0.05,
            "aggregate_unique": True,
            "likelihood_objective": "local_exact",
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_experiment(config_path)
    record = result["records"][0]
    assert record["train_likelihood_objective"] == "local_exact"
    assert record["num_train_windows"] > 0
    assert record["max_train_window_bits"] <= 3
    assert record["heldout_local_window_nll"] is not None
    assert record["delta_nll_oracle_source"] == "global_exact"
    assert record["P_local"] == 23
    assert record["P_hard"] == 9
    assert result["teacher_cases"] == [{"teacher_mode": "exact_orbit", "epsilon_break": 0.0}]
    assert result["window_audits"][0]["num_windows"] > 0
    assert result["window_audits"][0]["window_plan_enabled"] is True


def test_experiment_plan_rejects_known_mvp_output_mismatch(tmp_path):
    config = {
        "run": {"name": "bad", "output_dir": "outputs/scope_static/MVP03", "device": "cpu", "dtype": "float64"},
        "circuit": {"family": "surface_code:rotated_memory_x", "distance": 3, "rounds": 1, "noise": {}},
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
        "experiment": {"seeds": [0], "shot_budgets": [8]},
        "training": {"models": ["hard_orbit"], "steps": 1},
    }
    config_path = tmp_path / "d3_r1_MVP05_windows.yaml"
    config_path.write_text(yaml.safe_dump(config))

    with pytest.raises(ValueError, match="MVP05"):
        ExperimentPlan.from_path(config_path)

    override = ExperimentPlan.from_path(config_path, output_dir=tmp_path / "intentional")
    assert override.output_dir_overridden is True


def test_experiment_plan_cuda_request_requires_visible_cuda(monkeypatch, tmp_path):
    monkeypatch.setattr("torch.cuda.is_available", lambda: False)
    config = {
        "run": {"name": "cuda", "output_dir": str(tmp_path / "out"), "device": "cuda", "dtype": "float64"},
        "circuit": {"family": "surface_code:rotated_memory_x", "distance": 3, "rounds": 1, "noise": {}},
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
        "experiment": {"seeds": [0], "shot_budgets": [8]},
        "training": {"models": ["hard_orbit"], "steps": 1},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config))

    with pytest.raises(RuntimeError, match="requests CUDA"):
        ExperimentPlan.from_path(config_path)

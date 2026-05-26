import json

import pytest
import yaml

from scope_static.experiments.plan import ExperimentPlan
from scope_static.experiments.run_static_discovery import format_discovery_terminal_summary, run_discovery_experiment
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


def test_discovery_smoke_records_stage2a_schema_restarts_and_known_orbit_delta(tmp_path):
    config = {
        "run": {"name": "disc_smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
        "experiment": {
            "seeds": [0],
            "teacher_cases": [{"mode": "exact_orbit", "epsilon_break": 0.0}],
            "shot_budgets": [32],
            "heldout_shots": 64,
            "threshold_epsilon": 0.1,
        },
        "training": {
            "models": ["known_hard_orbit", "disc_hard"],
            "steps": 2,
            "lr": 0.05,
            "aggregate_unique": True,
            "discovery": {"prototype_counts": ["O"], "restarts": 2, "active_mass_threshold": 1.0},
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
        "evaluation": {"global_exact_max_bits": 20},
    }
    config_path = tmp_path / "disc_config.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_discovery_experiment(config_path)
    assert result["stage"] == "stage2A"
    assert len(result["discovery_restart_records"]) == 2
    assert sum(1 for row in result["discovery_restart_records"] if row["selected"]) == 1
    disc_record = next(record for record in result["records"] if record["model"] == "disc_hard")
    assert disc_record["evidence_record_schema"] == "scope_static_discovery_v1"
    assert disc_record["prototype_count_K"] == 9
    assert disc_record["P_discovery_assignment"] == 23 * 8
    assert disc_record["compressed_claim_allowed"] is False
    assert disc_record["known_orbit_oracle_model"] == "known_hard_orbit"
    assert disc_record["known_orbit_oracle_available"] is True
    assert disc_record["delta_nll_known_orbit"] is not None
    assert disc_record["tvd"] is not None
    assert "discovery_important_results" in result
    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text())
    assert metrics["records"][1]["discovery_num_restarts"] == 2
    terminal = format_discovery_terminal_summary(result)
    assert "Stage 2A Discovery Summary" in terminal
    assert "disc_hard" in terminal
    assert '"records"' not in terminal
    assert "metrics.json" in terminal


def test_discovery_scenario_config_combines_named_tasks(tmp_path):
    config = {
        "run": {"name": "stage2a", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
        "windows": {"enabled": True, "builders": ["detector_geometry"], "max_window_bits": 2, "max_windows": 3},
        "experiment": {"seeds": [0], "heldout_shots": 32, "threshold_epsilon": 0.1},
        "training": {
            "steps": 1,
            "lr": 0.05,
            "aggregate_unique": True,
            "likelihood_objective": "local_exact",
            "discovery": {"restarts": 1, "active_mass_threshold": 1.0},
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
        "evaluation": {"global_exact_max_bits": 20},
        "scenarios": [
            {
                "name": "matched_k_exact",
                "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
                "experiment": {
                    "teacher_cases": [{"mode": "exact_orbit", "epsilon_break": 0.0}],
                    "shot_budgets": [16],
                },
                "training": {"models": ["known_hard_orbit", "disc_hard"], "discovery": {"prototype_counts": ["O"]}},
            },
            {
                "name": "k_sweep_exact",
                "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
                "experiment": {
                    "teacher_cases": [{"mode": "exact_orbit", "epsilon_break": 0.0}],
                    "shot_budgets": [16],
                },
                "training": {"models": ["known_hard_orbit", "disc_hard"], "discovery": {"prototype_counts": [8, 9]}},
            },
        ],
    }
    config_path = tmp_path / "stage2a.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_discovery_experiment(config_path)
    assert result["scenario_config"] is True
    assert {record["scenario"] for record in result["records"]} == {"matched_k_exact", "k_sweep_exact"}
    assert (tmp_path / "out" / "matched_k_exact" / "metrics.json").exists()
    assert (tmp_path / "out" / "k_sweep_exact" / "metrics.json").exists()
    terminal = format_discovery_terminal_summary(result)
    assert "scenario" in terminal
    assert "matched_k_exact" in terminal
    assert "k_sweep_exact" in terminal


def test_experiment_plan_uses_internal_regularization_for_discovery(tmp_path):
    config = {
        "run": {"name": "regularization", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
        "circuit": {"family": "surface_code:rotated_memory_x", "distance": 3, "rounds": 1, "noise": {}},
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
        "experiment": {"seeds": [0], "shot_budgets": [8]},
        "training": {
            "models": ["disc_hard"],
            "steps": 1,
            "model_options": {
                "soft_feature_orbit": {"beta_l2": 0.001},
                "disc_hard": {"assignment_entropy_weight": 0.02},
                "disc_soft": {"assignment_entropy_weight": 0.02, "beta_l2": 0.001},
            },
        },
    }
    plan = ExperimentPlan.from_config(config, config_path=tmp_path / "regularization.yaml")

    assert plan.regularization_weight("soft_feature_orbit", {"beta_l2": 0.001}) == 0.001
    assert plan.regularization_weight("disc_hard", {"assignment_entropy_weight": 0.02}) == 1.0
    assert plan.regularization_weight("disc_soft", {"assignment_entropy_weight": 0.02, "beta_l2": 0.001}) == 1.0


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

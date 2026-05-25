import json

import yaml

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

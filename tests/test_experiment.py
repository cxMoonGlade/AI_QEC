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
    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text())
    assert metrics["records"]
    assert metrics["records"][0]["baseline_family"] == "dmle_qec"
    assert metrics["records"][0]["baseline_source_repository"] == "https://github.com/cxMoonGlade/DMLE-QEC"
    assert metrics["records"][0]["train_observation_mode"] == "detectors"
    assert {record["residual_rank"] for record in metrics["records"]} == {0, 1}
    assert {record["residual_rank"] for record in metrics["shots_to_threshold"]} == {0, 1}
    soft_records = [record for record in metrics["records"] if record["model"] == "soft_feature_orbit"]
    assert soft_records
    assert all(record["train_regularization_weight"] == 0.001 for record in soft_records)
    assert metrics["records"][0]["train_final_nll"] <= metrics["records"][0]["train_initial_nll"]

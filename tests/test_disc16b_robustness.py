from __future__ import annotations

from pathlib import Path

import yaml

from scope_static.experiments.run_static_disc16b_robustness import run_disc16b_robustness


NOISE = {
    "after_clifford_depolarization": 0.001,
    "after_reset_flip_probability": 0.001,
    "before_measure_flip_probability": 0.001,
    "before_round_data_depolarization": 0.001,
}


def test_disc16b_robustness_smoke_writes_schema(tmp_path: Path) -> None:
    config = {
        "run": {"name": "d3_r1_stage2c_disc16b_test", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
        "circuit": {"family": "surface_code:rotated_memory_x", "distance": 3, "rounds": 1, "noise": NOISE},
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
        "windows": {"enabled": False},
        "experiment": {
            "seeds": [0],
            "teacher_cases": [{"mode": "exact_orbit_separated", "epsilon_break": 0.0}],
            "shot_budgets": [64],
            "heldout_shots": 64,
        },
        "training": {
            "models": ["local"],
            "steps": 2,
            "lr": 0.05,
            "aggregate_unique": True,
            "likelihood_backend": "pytorch",
            "likelihood_objective": "global_exact",
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
        "evaluation": {"global_exact_max_bits": 20},
        "multi_env": {"teacher_seed": 0, "environment_design": "default", "contrast_strength": 1.0, "train_env_ids": [0, 1]},
        "disc16b": {
            "synthetic_seeds": [0, 1],
            "shot_budgets": [32, 64],
            "bootstrap_replicates": 2,
            "heldout_shots": 64,
            "local_inverse_steps": 2,
            "num_clusters": 3,
            "random_baseline_trials": 2,
            "train_env_ids": [0, 1],
            "regimes": [
                {"name": "default", "environment_design": "default", "contrast_strength": 1.0},
                {"name": "harder", "environment_design": "default", "contrast_strength": 0.75},
            ],
        },
    }
    path = tmp_path / "disc16b.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))

    result = run_disc16b_robustness(path)

    assert result["experiment"] == "DISC16b_local_inverse_recovery_robustness"
    assert result["predeclared_representation"] == "local_logit_probability"
    assert result["candidate_selection"] == "disabled_predeclared_representation"
    assert result["ari_nmi_used_for_selection"] is False
    assert result["altered_orbit_count_available"] is False
    assert len(result["robustness_grid"]) == 8
    assert result["aggregate_by_regime_budget"]
    assert "failure_cases" in result
    assert (tmp_path / "out" / "metrics.json").exists()
    assert (tmp_path / "out" / "robustness_grid.json").exists()
    assert (tmp_path / "out" / "failure_cases.json").exists()
    assert (tmp_path / "out" / "cluster_audit.json").exists()
    assert (tmp_path / "out" / "run_selection_audit.json").exists()
    assert (tmp_path / "out" / "disc16b_summary.md").exists()

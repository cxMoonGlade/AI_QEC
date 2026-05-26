import json

import yaml

from scope_static.experiments.run_static_inverse_logit_audit import run_inverse_logit_audit
from scope_static.multi_env import make_multi_env_teacher
from scope_static.stim_dem import build_surface_code_graph


def _graph():
    return build_surface_code_graph(
        distance=3,
        rounds=1,
        residual_rank=0,
        noise={
            "after_clifford_depolarization": 0.001,
            "after_reset_flip_probability": 0.001,
            "before_measure_flip_probability": 0.001,
            "before_round_data_depolarization": 0.001,
        },
    )


def test_disc13b_smoke_quantifies_local_oracle_gap(tmp_path):
    graph = _graph()
    teacher = make_multi_env_teacher(graph, seed=0)
    env_alpha_path = tmp_path / "env_alpha.json"
    env_alpha_path.write_text(
        json.dumps(
            {
                "local_full_per_fault_per_env": {
                    "train": {
                        str(env): [float(value) for value in teacher.logits_by_env[:, env].tolist()]
                        for env in range(4)
                    }
                }
            }
        )
    )
    config = {
        "run": {"name": "disc13b_smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
        "windows": {"enabled": False},
        "experiment": {
            "seeds": [0],
            "teacher_cases": [{"mode": "exact_orbit_separated", "epsilon_break": 0.0}],
            "shot_budgets": [32],
            "heldout_shots": 64,
            "threshold_epsilon": 0.1,
        },
        "training": {
            "models": ["local"],
            "steps": 1,
            "lr": 0.05,
            "aggregate_unique": True,
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
        "evaluation": {"global_exact_max_bits": 20},
        "multi_env": {"teacher_seed": 0, "environment_design": "default", "contrast_strength": 1.0},
        "disc13b": {"local_logit_metrics_path": str(env_alpha_path)},
    }
    config_path = tmp_path / "disc13b.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_inverse_logit_audit(config_path)

    assert result["stage"] == "stage2A.2"
    assert result["experiment"] == "DISC13b_inverse_logit_recovery_gap"
    assert result["uses_hidden_omega_for_training"] is False
    assert result["ari_nmi_used_for_selection"] is False
    assert result["ari_cluster_oracle_logit_vs_omega"] == 1.0
    assert result["corr_local_oracle"] > 0.9
    assert (tmp_path / "out" / "metrics.json").exists()
    assert (tmp_path / "out" / "disc13b_summary.md").exists()
    assert (tmp_path / "out" / "logit_clusters.json").exists()

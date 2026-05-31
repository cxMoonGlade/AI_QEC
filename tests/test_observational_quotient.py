import json

import torch
import yaml

from scope_static.experiments.static.observational_quotient import (
    build_disc13_fingerprints,
    run_observational_quotient_audit,
)
from scope_static.dem.multi_env import make_multi_env_teacher
from scope_static.dem.stim_dem import build_surface_code_graph


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


def test_disc13_fingerprints_are_finite_and_fault_shaped():
    graph = _graph()
    teacher = make_multi_env_teacher(graph, seed=0)
    fingerprints = build_disc13_fingerprints(graph, teacher.logits_by_env)
    assert {"oracle_logit", "oracle_logit_support", "observation_side", "combined"} <= set(fingerprints)
    for matrix in fingerprints.values():
        assert matrix.shape[0] == graph.M
        assert matrix.shape[1] > 0
        assert bool(torch.isfinite(matrix).all())


def test_disc13_smoke_writes_target_alignment_artifacts(tmp_path):
    graph = _graph()
    learned_path = tmp_path / "shared_assignment.json"
    learned_path.write_text(
        json.dumps(
            {
                "toy_learned": {
                    "hard_assignment_labels": [int(value) for value in graph.orbit_ids.tolist()],
                    "ari": 1.0,
                    "nmi": 1.0,
                }
            }
        )
    )
    config = {
        "run": {"name": "disc13_smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
        "disc13": {
            "primary_observational_quotient_family": "observation_side",
            "learned_partition_path": str(learned_path),
        },
    }
    config_path = tmp_path / "disc13.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_observational_quotient_audit(config_path)

    assert result["stage"] == "stage2A.2"
    assert result["experiment"] == "DISC13_observational_quotient_audit"
    assert result["uses_hidden_omega_for_training"] is False
    assert result["uses_hidden_omega_for_checkpoint_selection"] is False
    assert result["uses_hidden_omega_for_final_evaluation"] is True
    assert result["ari_nmi_used_for_selection"] is False
    assert result["target_alignment"]
    assert result["primary_observational_quotient_family"] == "observation_side"

    output = tmp_path / "out"
    for filename in ["metrics.json", "disc13_summary.md", "observational_quotient.json", "target_alignment.json"]:
        assert (output / filename).exists()
    assert (output / "fingerprints" / "observation_side.npy").exists()

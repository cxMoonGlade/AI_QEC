import json

import torch
import yaml

from scope_static.experiments.run_static_multi_env_discovery import run_multi_env_discovery
from scope_static.multi_env import (
    MultiEnvSharedAssignmentField,
    assignment_recovery_metrics,
    codebook_perturbations,
    make_multi_env_teacher,
)
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


def test_multi_env_teacher_keeps_omega_fixed_and_varies_alpha():
    graph = _graph()
    teacher = make_multi_env_teacher(graph, seed=0)
    assert teacher.alpha_by_env.shape == (5, graph.O)
    assert teacher.logits_by_env.shape == (graph.M, 5)
    assert torch.equal(teacher.omega, graph.orbit_ids)
    assert float((teacher.alpha_by_env[0] - teacher.alpha_by_env[1]).abs().sum()) > 0.0
    for env in range(5):
        assert torch.allclose(teacher.logits_by_env[:, env], teacher.alpha_by_env[env, graph.orbit_ids])


def test_codebook_teacher_contrast_strength_scales_alpha_variation():
    graph = _graph()
    weak = make_multi_env_teacher(graph, seed=0, contrast_strength=1.0, design="codebook")
    strong = make_multi_env_teacher(graph, seed=0, contrast_strength=4.0, design="codebook")
    assert codebook_perturbations(5, graph.O).shape == (5, graph.O)
    weak_span = float((weak.alpha_by_env - weak.alpha_by_env.mean(dim=0, keepdim=True)).norm())
    strong_span = float((strong.alpha_by_env - strong.alpha_by_env.mean(dim=0, keepdim=True)).norm())
    assert strong_span > weak_span


def test_shared_assignment_field_has_shared_S_and_env_specific_alpha():
    field = MultiEnvSharedAssignmentField(4, 3, 2, dtype=torch.float64, assignment_init_scale=0.0)
    S = field.assignment_probabilities()
    logits = field.realized_logits()
    assert S.shape == (4, 3)
    assert torch.allclose(S.sum(dim=1), torch.ones(4, dtype=torch.float64))
    assert logits.shape == (4, 2)
    metrics = assignment_recovery_metrics(S, torch.tensor([0, 1, 2, 0]), active_mass_threshold=0.1)
    assert metrics["ari"] is not None
    assert metrics["nmi"] is not None


def test_disc12_smoke_writes_required_audits_and_artifacts(tmp_path):
    config = {
        "run": {"name": "disc12_smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
            "models": ["local", "known_hard_orbit", "disc_hard"],
            "steps": 1,
            "lr": 0.05,
            "aggregate_unique": True,
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
        "evaluation": {"global_exact_max_bits": 20},
        "multi_env": {
            "train_env_ids": [0, 1],
            "heldout_env_ids": [2],
            "validation_shots": 32,
            "heldout_env_adaptation_shots": 32,
            "restarts": 1,
            "contrast_sweep": {
                "enabled": True,
                "environment_design": "codebook",
                "strengths": [1.0],
                "shot_budget": 32,
                "validation_shots": 32,
                "heldout_shots": 32,
                "heldout_env_adaptation_shots": 32,
                "restarts": 1,
            },
            "conditions": [
                {
                    "model": "single_env_local_logit_init",
                    "name": "single_env_local_logit_init",
                    "multi_env": False,
                    "initializer": "DISC10_local_logit",
                },
                {
                    "model": "multi_env_shared_S_DISC10_init",
                    "name": "multi_env_shared_S_DISC10_init",
                    "multi_env": True,
                    "initializer": "DISC10_local_logit",
                },
                {"model": "known_orbit_oracle_shared_S", "name": "known_orbit_oracle_shared_S", "oracle": True},
            ],
        },
    }
    config_path = tmp_path / "disc12.yaml"
    config_path.write_text(yaml.safe_dump(config))
    result = run_multi_env_discovery(config_path)

    assert result["stage"] == "stage2A.2"
    assert result["experiment"] == "DISC12_multi_env_shared_assignment"
    assert result["uses_hidden_omega_for_training"] is False
    assert result["uses_hidden_omega_for_checkpoint_selection"] is False
    assert result["uses_hidden_omega_for_final_evaluation"] is True
    assert result["ari_nmi_used_for_selection"] is False
    assert result["environment_contrast_audit"]["alpha_variation_norm"] > 0.0
    assert result["disc12_important_results"]["model_summary"]
    assert any(record["model"] == "multi_env_shared_S_DISC10_init" for record in result["records"])

    output = tmp_path / "out"
    for filename in [
        "metrics.json",
        "disc12_summary.md",
        "shared_assignment.json",
        "env_alpha.json",
        "run_selection_audit.json",
        "contrast_sweep.json",
    ]:
        assert (output / filename).exists()
    metrics = json.loads((output / "metrics.json").read_text())
    assert metrics["records"]
    assert metrics["restart_records"][0]["selection_rule"] == "validation_nll_plus_observable_health"
    assert metrics["restart_records"][0]["ari_nmi_used_for_selection"] is False
    assert metrics["disc12a_stage_label"] == "multi_env_predictive_only_weak_recovery_gain_observable_contrast_likely_insufficient"
    assert metrics["contrast_sweep"]["enabled"] is True
    assert metrics["contrast_sweep"]["rows"]

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import torch
import yaml

from scope_static.experiments.plan import ExperimentPlan
from scope_static.experiments.run_static_disc16_observability import _fit_local_inverse, _sample_env_observations
from scope_static.experiments.run_static_disc16_observability import run_disc16_observability
from scope_static.identifiability import deterministic_kmeans
from scope_static.local_mechanism import local_probability_features
from scope_static.multi_env import make_multi_env_teacher


NOISE = {
    "after_clifford_depolarization": 0.001,
    "after_reset_flip_probability": 0.001,
    "before_measure_flip_probability": 0.001,
    "before_round_data_depolarization": 0.001,
}


def test_disc16a_shot_budget_smoke_writes_schema(tmp_path: Path) -> None:
    config = {
        "run": {"name": "d3_r1_stage2d_disc16a_test", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
        "disc16a": {
            "shot_budgets": [32, 64],
            "bootstrap_replicates": 2,
            "heldout_shots": 64,
            "local_inverse_steps": 2,
            "num_clusters": 3,
            "random_baseline_trials": 2,
            "train_env_ids": [0, 1],
        },
    }
    path = tmp_path / "disc16a.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))

    result = run_disc16_observability(path)

    assert result["experiment"] == "DISC16a_shot_budget_sweep"
    assert result["predeclared_representation"] == "local_logit_probability"
    assert result["candidate_selection"] == "disabled_predeclared_representation"
    assert result["ari_nmi_used_for_selection"] is False
    assert len(result["shot_sweep"]) == 2
    assert "local_logit_probability_variance" in result["shot_sweep"][0]
    assert (tmp_path / "out" / "metrics.json").exists()
    assert (tmp_path / "out" / "shot_sweep.json").exists()
    assert (tmp_path / "out" / "cluster_audit.json").exists()
    assert (tmp_path / "out" / "run_selection_audit.json").exists()


def test_disc16a_local_inverse_path_ignores_orbit_ids_after_sampling(tmp_path: Path) -> None:
    config = {
        "run": {"name": "d3_r1_stage2d_disc16a_leakage_test", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
    }
    path = tmp_path / "disc16a_leakage.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    plan = ExperimentPlan.from_path(path)
    graph = plan.build_graph(plan.teacher_residual_rank)
    teacher = make_multi_env_teacher(graph, seed=0, dtype=plan.dtype, contrast_strength=1.0, design="default")
    train_env_ids = (0, 1)
    observations = _sample_env_observations(graph, teacher.logits_by_env, shots=64, seed_base=1234, env_ids=train_env_ids)

    altered_orbits = torch.arange(graph.M, dtype=torch.long) % graph.O
    altered_graph = replace(
        graph,
        orbit_ids=altered_orbits,
        orbit_sizes=torch.bincount(altered_orbits, minlength=graph.O).to(dtype=torch.long),
        feature_rank_by_orbit={},
    )

    original_fit = _fit_local_inverse(plan, graph, observations, train_env_ids=train_env_ids, steps=2, lr=0.05)
    altered_fit = _fit_local_inverse(plan, altered_graph, observations, train_env_ids=train_env_ids, steps=2, lr=0.05)
    original_features = local_probability_features(original_fit["local_logits"])
    altered_features = local_probability_features(altered_fit["local_logits"])
    original_clusters = deterministic_kmeans(original_features, graph.O)
    altered_clusters = deterministic_kmeans(altered_features, graph.O)

    assert torch.allclose(original_fit["local_logits"], altered_fit["local_logits"], atol=1e-12, rtol=0.0)
    assert torch.allclose(original_features, altered_features, atol=1e-12, rtol=0.0)
    assert torch.equal(original_clusters.labels, altered_clusters.labels)

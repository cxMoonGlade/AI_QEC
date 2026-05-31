from __future__ import annotations

import json
from pathlib import Path

import torch
import yaml

from scope_static.experiments.static.local_mechanism_discovery import run_local_mechanism_discovery
from scope_static.dem.local_mechanism import (
    graph_smooth_features,
    load_local_logit_matrix,
    local_probability_features,
    nmf_codes,
    pca_denoised_features,
    spectral_similarity_embedding,
    split_merge_audit,
)
from scope_static.dem.stim_dem import build_surface_code_graph


NOISE = {
    "after_clifford_depolarization": 0.001,
    "after_reset_flip_probability": 0.001,
    "before_measure_flip_probability": 0.001,
    "before_round_data_depolarization": 0.001,
}


def test_local_mechanism_transforms_are_finite_and_shaped() -> None:
    graph = build_surface_code_graph(
        family="surface_code:rotated_memory_x",
        distance=3,
        rounds=1,
        noise=NOISE,
        residual_rank=0,
        canonicalize_duplicate_masks=True,
    )
    features = torch.randn((graph.M, 4), dtype=torch.float64)
    smoothed = graph_smooth_features(graph, features, strength=0.5, steps=2)
    denoised = pca_denoised_features(features, rank=2)
    spectral = spectral_similarity_embedding(features, num_components=graph.O)
    codes = nmf_codes(features, rank=graph.O, seed=0, steps=5)
    for matrix in [smoothed, denoised, spectral, codes]:
        assert matrix.shape[0] == graph.M
        assert torch.isfinite(matrix).all()
    assert codes.shape[1] == min(graph.O, graph.M, features.shape[1])


def test_split_merge_audit_marks_exact_partition() -> None:
    labels = torch.tensor([0, 0, 1, 1, 2, 2])
    audit = split_merge_audit(labels, labels)
    assert audit["mean_splits_per_omega"] == 1.0
    assert audit["mean_merged_omega_per_cluster"] == 1.0
    assert audit["mean_cluster_purity"] == 1.0


def test_load_local_logit_matrix_from_env_alpha(tmp_path: Path) -> None:
    path = tmp_path / "env_alpha.json"
    path.write_text(
        json.dumps(
            {
                "local_full_per_fault_per_env": {
                    "train": {
                        "0": [-1.0, -2.0, -3.0],
                        "1": [-4.0, -5.0, -6.0],
                    }
                }
            }
        )
    )
    matrix = load_local_logit_matrix(path, 3)
    assert matrix.shape == (3, 2)
    assert matrix[0, 1].item() == -4.0


def test_load_local_logit_matrix_ignores_oracle_entries(tmp_path: Path) -> None:
    path = tmp_path / "env_alpha.json"
    local_values = {
        "0": [-1.0, -2.0, -3.0],
        "1": [-4.0, -5.0, -6.0],
    }
    oracle_values = {
        "0": [100.0, 101.0, 102.0],
        "1": [103.0, 104.0, 105.0],
    }
    path.write_text(
        json.dumps(
            {
                "known_orbit_oracle_shared_S": {"train": oracle_values},
                "local_full_per_fault_per_env": {"train": local_values},
            }
        )
    )

    matrix = load_local_logit_matrix(path, 3)

    assert matrix.tolist() == [[-1.0, -4.0], [-2.0, -5.0], [-3.0, -6.0]]
    assert 100.0 not in matrix


def test_local_probability_features_do_not_accept_orbit_labels() -> None:
    logits = torch.tensor([[-2.0, -3.0], [-4.0, -5.0], [-6.0, -7.0]], dtype=torch.float64)

    features = local_probability_features(logits)

    assert features.shape == (3, 4)
    assert torch.allclose(features[:, :2], logits)
    assert torch.allclose(features[:, 2:], torch.sigmoid(logits))


def test_disc15_runner_writes_artifacts(tmp_path: Path) -> None:
    config_path = tmp_path / "disc15.yaml"
    output_dir = tmp_path / "out"
    source_path = tmp_path / "env_alpha.json"
    config = {
        "run": {"name": "d3_r1_stage2c_disc15_test", "output_dir": str(output_dir), "device": "cpu", "dtype": "float64"},
        "circuit": {
            "family": "surface_code:rotated_memory_x",
            "distance": 3,
            "rounds": 1,
            "noise": NOISE,
        },
        "graph": {"canonicalize_duplicate_masks": True, "residual_rank": 0},
        "windows": {"enabled": False},
        "experiment": {
            "seeds": [0],
            "teacher_cases": [{"mode": "exact_orbit_separated", "epsilon_break": 0.0}],
            "shot_budgets": [128],
            "heldout_shots": 128,
        },
        "training": {
            "models": ["local"],
            "steps": 2,
            "lr": 0.05,
            "aggregate_unique": True,
            "likelihood_backend": "torch",
            "likelihood_objective": "global_exact",
            "exact_likelihood_trainable": True,
            "dem_fault_logit_claim": True,
            "cptp_gksl_claim": False,
        },
        "evaluation": {"global_exact_max_bits": 20},
        "disc15": {
            "local_logit_source": str(source_path),
            "local_logit_baseline": {"ari": 0.0, "nmi": 0.0},
            "pca_ranks": [1],
            "nmf_steps": 3,
            "nmf_seeds": [0],
            "random_baseline_trials": 2,
        },
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    graph = build_surface_code_graph(
        family="surface_code:rotated_memory_x",
        distance=3,
        rounds=1,
        noise=NOISE,
        residual_rank=0,
        canonicalize_duplicate_masks=True,
    )
    local = {}
    for env in range(graph.O):
        local[str(env)] = [2.0 if int(label) == env else -2.0 for label in graph.orbit_ids.tolist()]
    source_path.write_text(json.dumps({"local_full_per_fault_per_env": {"train": local}}))

    result = run_local_mechanism_discovery(config_path)

    assert result["stage"] == "stage2C"
    assert result["ari_nmi_used_for_selection"] is False
    assert result["uses_hidden_omega_for_training"] is False
    assert (output_dir / "metrics.json").exists()
    assert (output_dir / "disc15_summary.md").exists()
    assert (output_dir / "representations" / "local_logit_baseline.npy").exists()
    assert (output_dir / "clusters" / "local_logit_baseline_clusters.json").exists()

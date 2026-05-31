import dataclasses
import json

import numpy as np
import torch
import yaml

from scope_static.experiments.static.identifiability import run_identifiability_audit
from scope_static.experiments.static.stage2a0_summary import build_stage2a0_summary, write_stage2a0_summary
from scope_static.identifiability import (
    classify_passive_identifiability,
    deterministic_kmeans,
    local_logit_signature,
    moment_spectral_signature,
    random_partition_baseline,
    shuffled_omega_control,
    structural_signature,
)
from scope_static.dem.stim_dem import build_surface_code_graph


def _d3_graph():
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


def test_visible_signatures_do_not_change_when_orbit_ids_change():
    graph = _d3_graph()
    observations = torch.zeros((16, graph.B), dtype=torch.bool)
    permuted = dataclasses.replace(graph, orbit_ids=torch.flip(graph.orbit_ids, dims=[0]))

    assert torch.allclose(structural_signature(graph), structural_signature(permuted))
    assert torch.allclose(moment_spectral_signature(graph, observations), moment_spectral_signature(permuted, observations))


def test_signature_matrices_are_finite_and_shaped_by_faults():
    graph = _d3_graph()
    observations = torch.randint(0, 2, (32, graph.B), dtype=torch.bool)
    local = local_logit_signature(torch.linspace(-7.0, -4.0, graph.M))
    for signature in [
        structural_signature(graph),
        moment_spectral_signature(graph, observations, spectral_rank=2),
        local,
    ]:
        assert signature.shape[0] == graph.M
        assert signature.ndim == 2
        assert signature.shape[1] > 0
        assert bool(torch.isfinite(signature).all())


def test_deterministic_kmeans_is_stable_for_fixed_inputs():
    features = torch.tensor([[0.0], [0.1], [5.0], [5.1]], dtype=torch.float64)
    left = deterministic_kmeans(features, 2)
    right = deterministic_kmeans(features, 2)
    assert torch.equal(left.labels, right.labels)
    assert left.active_clusters == 2


def test_collapsed_clusters_are_not_classified_as_separating():
    result = classify_passive_identifiability(
        ari=1.0,
        nmi=1.0,
        active_clusters=1,
        num_clusters=9,
        random_ari=0.0,
        random_nmi=0.0,
    )
    assert result in {"weak", "failed"}


def test_null_controls_move_scores_toward_chance():
    hidden = torch.arange(40) // 10
    labels = hidden.clone()
    shuffled = shuffled_omega_control(labels, hidden, seed=3)
    assert shuffled["shuffled_omega_ari"] < 1.0
    random_labels = random_partition_baseline(hidden.numel(), 4, seed=5, num_trials=4)
    assert all(label.shape == hidden.shape for label in random_labels)


def test_stage2a0_summary_classifies_nll_only_success_as_not_enough(tmp_path):
    metrics = {
        "output_dir": str(tmp_path),
        "discovery_important_results": {"threshold_epsilon": 0.01},
        "records": [
            {
                "scenario": "matched_k_exact",
                "teacher_mode": "exact_orbit_separated",
                "epsilon_break": 0.0,
                "model": "disc_hard",
                "residual_rank": 0,
                "shots": 2048,
                "prototype_count_K": 9,
                "seed": seed,
                "ari": 0.2,
                "nmi": 0.6,
                "delta_nll_known_orbit": 0.002,
                "assignment_collapse": False,
                "assignment_entropy_normalized": 0.1,
                "num_active_prototypes": 9,
            }
            for seed in [0, 1, 2]
        ],
    }
    summary = build_stage2a0_summary(metrics)
    assert summary["stage2a0_result"] == "likelihood_match_without_partition_recovery"
    assert summary["success_requires"]["nll_only_success_sufficient"] is False

    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(metrics))
    written = write_stage2a0_summary(metrics_path)
    assert (tmp_path / "stage2a0_summary.json").exists()
    assert (tmp_path / "stage2a0_summary.md").exists()
    assert written["stage2a0_result"] == summary["stage2a0_result"]


def test_disc10_smoke_writes_compact_artifacts(tmp_path):
    config = {
        "run": {"name": "disc10_smoke", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
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
        "identifiability": {
            "K_mode": "known_K_synthetic_audit",
            "spectral_rank": 2,
            "random_baseline_trials": 4,
        },
    }
    config_path = tmp_path / "disc10.yaml"
    config_path.write_text(yaml.safe_dump(config))
    metrics = run_identifiability_audit(config_path)

    assert metrics["stage"] == "stage2A.0.5"
    assert metrics["K_mode"] == "known_K_synthetic_audit"
    assert metrics["disc10_audit"]["passive_identifiability_result"] in {"separates", "weak", "failed"}
    assert metrics["disc10_seed_candidate"]["selection_rule"] == "observable_only"
    assert metrics["records"][0]["ari_nmi_used_for_selection"] is False
    assert "random_gaussian_signature" in metrics["null_controls"]
    assert "mean_ari_gap_vs_random" in metrics["null_controls"]["random_gaussian_signature"]

    output = tmp_path / "out"
    assert (output / "disc10_metrics.json").exists()
    assert (output / "disc10_summary.md").exists()
    for family in ["structural", "local_logit", "moment_spectral", "combined"]:
        array = np.load(output / "signatures" / f"{family}.npy")
        assert array.ndim == 3
        assert (output / "clusters" / f"{family}_clusters.json").exists()

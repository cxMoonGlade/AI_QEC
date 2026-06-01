from __future__ import annotations

import json
from pathlib import Path

import yaml

from scope_static.experiments.static.disc15c_confirmatory import run_disc15c_confirmatory
from scope_static.dem.stim_dem import build_surface_code_graph


NOISE = {
    "after_clifford_depolarization": 0.001,
    "after_reset_flip_probability": 0.001,
    "before_measure_flip_probability": 0.001,
    "before_round_data_depolarization": 0.001,
}


def test_disc15c_confirmatory_disables_candidate_selection(tmp_path: Path) -> None:
    graph = build_surface_code_graph(
        family="surface_code:rotated_memory_x",
        distance=3,
        rounds=1,
        noise=NOISE,
        residual_rank=0,
        canonicalize_duplicate_masks=True,
    )
    source = tmp_path / "env_alpha.json"
    local = {}
    for env in range(graph.O):
        local[str(env)] = [2.0 if int(label) == env else -2.0 for label in graph.orbit_ids.tolist()]
    source.write_text(json.dumps({"per_fault_per_env_baseline": {"train": local}}))
    config = {
        "run": {"name": "d3_r1_stage2c_disc15c_test", "output_dir": str(tmp_path / "out"), "device": "cpu", "dtype": "float64"},
        "circuit": {"family": "surface_code:rotated_memory_x", "distance": 3, "rounds": 1, "noise": NOISE},
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
        "disc15c": {"local_logit_source": str(source), "num_clusters": graph.O, "random_baseline_trials": 2},
    }
    path = tmp_path / "disc15c.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))

    result = run_disc15c_confirmatory(path)

    assert result["predeclared_representation"] == "local_logit_probability"
    assert result["candidate_selection"] == "disabled_predeclared_representation"
    assert result["ari_nmi_used_for_selection"] is False
    assert result["uses_hidden_omega_for_training"] is False
    assert (tmp_path / "out" / "metrics.json").exists()
    assert (tmp_path / "out" / "local_logit_probability.npy").exists()

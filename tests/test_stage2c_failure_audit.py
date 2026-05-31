from __future__ import annotations

import json
from pathlib import Path

from scope_static.experiments.static.stage2c_failure_audit import run_stage2c_failure_audit


def test_stage2c_failure_audit_summarizes_near_miss_failures(tmp_path: Path) -> None:
    metrics = {
        "predeclared_representation": "local_logit_probability",
        "candidate_selection": "disabled_predeclared_representation",
        "ari_nmi_used_for_selection": False,
        "uses_hidden_omega_for_training": False,
        "uses_hidden_omega_for_initialization": False,
        "uses_hidden_omega_for_checkpoint_selection": False,
        "uses_hidden_omega_for_final_evaluation": True,
        "strong_threshold": {"ari": 0.8, "nmi": 0.8, "active_clusters_min": 2},
        "failure_cases": [
            {
                "regime": "default",
                "synthetic_seed": 0,
                "shots": 10000,
                "ari_min": 0.75,
                "nmi_min": 0.91,
                "active_clusters_min": 3,
                "reasons": ["ari_below_0.80"],
            }
        ],
        "robustness_grid": [
            _record("default", 0, 10000, 0.75, 0.91, False),
            _record("default", 0, 25000, 1.0, 1.0, True),
            _record("default", 1, 10000, 1.0, 1.0, True),
        ],
    }
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps(metrics))

    result = run_stage2c_failure_audit(path)

    assert result["experiment"] == "DISC16b_failure_case_audit"
    assert result["num_failures"] == 1
    assert result["num_strong_conditions"] == 2
    assert result["failure_audit_conclusion"] == "near_miss_ari_failures_no_cluster_collapse_mostly_low_shot_split_merge"
    assert result["failure_rows"][0]["resolved_by_any_higher_shot_budget"] is True
    assert (tmp_path / "failure_case_audit.json").exists()
    assert (tmp_path / "failure_case_audit.md").exists()


def _record(regime: str, seed: int, shots: int, ari: float, nmi: float, strong: bool) -> dict[str, object]:
    return {
        "regime": regime,
        "synthetic_seed": seed,
        "shots": shots,
        "ari_mean": ari,
        "ari_min": ari,
        "nmi_mean": nmi,
        "nmi_min": nmi,
        "active_clusters_min": 3,
        "bootstrap_label_pairwise_nmi": nmi,
        "local_logit_probability_variance": 0.01,
        "mean_cluster_purity_mean": 0.95,
        "mean_splits_per_omega_mean": 1.1,
        "heldout_local_inverse_nll_mean": 0.9,
        "strong_all_replicates": strong,
        "replicates": [
            {
                "replicate": 0,
                "ari": ari,
                "nmi": nmi,
                "active_clusters": 3,
                "mean_cluster_purity": 0.95,
                "mean_splits_per_omega": 1.1,
                "max_splits_per_omega": 2,
                "max_merged_omega_per_cluster": 2,
                "cluster_masses": [1, 1, 1],
            }
        ],
    }

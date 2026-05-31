from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.static.plan import ExperimentPlan
from scope_static.identifiability import deterministic_kmeans, evaluate_partition, random_baseline_summary, random_partition_baseline
from scope_static.dem.local_mechanism import load_local_logit_matrix, local_probability_features, split_merge_audit


DISC15C_AUDIT = {
    "stage": "stage2C",
    "experiment": "DISC15c_confirmatory_local_logit_probability",
    "uses_hidden_omega_for_training": False,
    "uses_hidden_omega_for_initialization": False,
    "uses_hidden_omega_for_checkpoint_selection": False,
    "uses_hidden_omega_for_final_evaluation": True,
    "ari_nmi_used_for_selection": False,
    "candidate_selection": "disabled_predeclared_representation",
    "predeclared_representation": "local_logit_probability",
}


def run_disc15c_confirmatory(config_path: str | Path, *, output_dir: str | Path | None = None) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("disc15c", {}))
    output = plan.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    source = Path(str(cfg.get("local_logit_source", "outputs/scope_static/STAGE2A2_DISC12_multi_env/env_alpha.json")))
    local_logits = load_local_logit_matrix(source, graph.M)
    representation = local_probability_features(local_logits)
    k = int(cfg.get("num_clusters", graph.O))
    clustering = deterministic_kmeans(representation, k)
    random_summary = random_baseline_summary(
        random_partition_baseline(graph.M, k, seed=int(cfg.get("random_baseline_seed", 0)), num_trials=int(cfg.get("random_baseline_trials", 32))),
        graph.orbit_ids,
    )
    recovery = evaluate_partition(clustering.labels, graph.orbit_ids, num_clusters=k, random_baseline=random_summary)
    baseline = _local_logit_baseline(local_logits, graph, k, random_summary)
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        **DISC15C_AUDIT,
        "schema": "scope_static_stage2c_disc15c_confirmatory_v1",
        "question": "Does the predeclared local_logit_probability representation recover synthetic omega without evaluator-based candidate selection?",
        "K_mode": "known_K_synthetic_audit",
        "local_logit_source": str(source),
        "representation_shape": [int(value) for value in representation.shape],
        "local_logit_shape": [int(value) for value in local_logits.shape],
        "declared_success": {
            "beats_local_logit_baseline": "ARI and NMI both improve over measured local-logit baseline",
            "strong": "ARI >= 0.80 and NMI >= 0.80",
            "near_strong": "NMI >= 0.80 and ARI in [0.75, 0.80)",
        },
        "local_logit_baseline": baseline,
        "ari": recovery["ari"],
        "nmi": recovery["nmi"],
        "active_clusters": recovery["active_clusters"],
        "cluster_masses": recovery["cluster_masses"],
        "dead_clusters": recovery["dead_clusters"],
        "passive_identifiability_result": recovery["passive_identifiability_result"],
        "random_partition_baseline": random_summary,
        "within_cluster_dispersion": clustering.within_cluster_dispersion,
        "silhouette_like": clustering.silhouette_like,
        "cluster_mass_entropy_normalized": clustering.cluster_mass_entropy_normalized,
        "observable_selection_score_reported_not_used": clustering.observable_selection_score,
        "beats_local_logit_baseline": bool(
            float(recovery["ari"]) > float(baseline["ari"]) and float(recovery["nmi"]) > float(baseline["nmi"])
        ),
        "disc15c_result": _disc15c_result(float(recovery["ari"]), float(recovery["nmi"]), baseline),
        "labels": [int(value) for value in clustering.labels.tolist()],
        "contingency_table": recovery["contingency_table"],
        **split_merge_audit(clustering.labels, graph.orbit_ids),
    }
    np.save(output / "local_logits.npy", local_logits.numpy())
    np.save(output / "local_logit_probability.npy", representation.numpy())
    (output / "clusters.json").write_text(
        json.dumps({"labels": result["labels"], "cluster_masses": result["cluster_masses"]}, indent=2, sort_keys=True) + "\n"
    )
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "disc15c_summary.md").write_text(format_disc15c_summary(result))
    print(format_disc15c_terminal_summary(result))
    return result


def _local_logit_baseline(local_logits: torch.Tensor, graph, k: int, random_summary: dict[str, float]) -> dict[str, object]:
    clustering = deterministic_kmeans(local_logits, k)
    recovery = evaluate_partition(clustering.labels, graph.orbit_ids, num_clusters=k, random_baseline=random_summary)
    return {
        "representation": "local_logit",
        "ari": recovery["ari"],
        "nmi": recovery["nmi"],
        "active_clusters": recovery["active_clusters"],
        "cluster_masses": recovery["cluster_masses"],
    }


def _disc15c_result(ari: float, nmi: float, baseline: dict[str, object]) -> str:
    if ari >= 0.80 and nmi >= 0.80:
        return "strong_confirmed"
    if nmi >= 0.80 and ari >= 0.75:
        return "near_strong_confirmed"
    if ari > float(baseline["ari"]) and nmi > float(baseline["nmi"]):
        return "beats_local_logit_baseline_but_not_near_strong"
    return "does_not_beat_local_logit_baseline"


def format_disc15c_summary(result: dict[str, object]) -> str:
    baseline = result["local_logit_baseline"]
    return "\n".join(
        [
            "# DISC15c Confirmatory Local-Logit Probability",
            "",
            f"- Result: `{result['disc15c_result']}`",
            f"- Candidate selection: `{result['candidate_selection']}`",
            f"- Predeclared representation: `{result['predeclared_representation']}`",
            f"- ARI/NMI used for selection: `{str(result['ari_nmi_used_for_selection']).lower()}`",
            "",
            "| representation | ARI | NMI | active |",
            "| --- | ---: | ---: | ---: |",
            f"| local_logit baseline | {_fmt(baseline['ari'])} | {_fmt(baseline['nmi'])} | {baseline['active_clusters']} |",
            f"| local_logit_probability | {_fmt(result['ari'])} | {_fmt(result['nmi'])} | {result['active_clusters']} |",
            "",
        ]
    )


def format_disc15c_terminal_summary(result: dict[str, object]) -> str:
    baseline = result["local_logit_baseline"]
    return "\n".join(
        [
            "Stage 2C DISC15c Confirmatory Local-Logit Probability",
            f"config: {result.get('config_path')}",
            f"output: {result.get('output_dir')}",
            f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
            f"result: {result['disc15c_result']}",
            f"baseline local_logit: ARI={_fmt(baseline['ari'])} NMI={_fmt(baseline['nmi'])}",
            f"predeclared local_logit_probability: ARI={_fmt(result['ari'])} NMI={_fmt(result['nmi'])}",
        ]
    )


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DISC15c confirmatory local_logit_probability recovery.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_disc15c_confirmatory(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

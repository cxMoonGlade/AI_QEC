from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.plan import ExperimentPlan
from scope_static.identifiability import (
    combined_signature,
    deterministic_kmeans,
    evaluate_partition,
    random_baseline_summary,
    random_partition_baseline,
    standardize_features,
    structural_signature,
)
from scope_static.local_mechanism import (
    graph_smooth_features,
    load_local_logit_matrix,
    local_probability_features,
    nmf_codes,
    overlapping_topk_codes,
    pca_denoised_features,
    pca_scores,
    spectral_similarity_embedding,
    split_merge_audit,
)
from scope_static.metrics import normalized_mutual_info
from scope_static.numerics import NUMERICAL_ZERO


DISC15_AUDIT = {
    "stage": "stage2C",
    "experiment": "DISC15_local_logit_to_mechanism_discovery",
    "uses_hidden_omega_for_training": False,
    "uses_hidden_omega_for_initialization": False,
    "uses_hidden_omega_for_checkpoint_selection": False,
    "uses_hidden_omega_for_final_evaluation": True,
    "ari_nmi_used_for_selection": False,
}


def run_local_mechanism_discovery(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("disc15", {}))
    output = plan.output_dir
    reps_dir = output / "representations"
    clusters_dir = output / "clusters"
    reps_dir.mkdir(parents=True, exist_ok=True)
    clusters_dir.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    local_source = Path(str(cfg.get("local_logit_source", "outputs/scope_static/STAGE2A2_DISC12_multi_env/env_alpha.json")))
    local_logits = load_local_logit_matrix(local_source, graph.M)
    np.save(reps_dir / "source_local_logits.npy", local_logits.numpy())

    k = int(cfg.get("num_clusters", graph.O))
    baseline_ref = dict(cfg.get("local_logit_baseline", {}))
    declared_baseline = {
        "ari": float(baseline_ref.get("ari", 0.5187)),
        "nmi": float(baseline_ref.get("nmi", 0.8287)),
    }
    random_summary = random_baseline_summary(
        random_partition_baseline(graph.M, k, seed=int(cfg.get("random_baseline_seed", 0)), num_trials=int(cfg.get("random_baseline_trials", 32))),
        graph.orbit_ids,
    )

    candidates = _build_candidates(graph, local_logits, cfg, k)
    records = []
    for name, features, method in candidates:
        features = torch.nan_to_num(
            torch.as_tensor(features, dtype=torch.float64, device="cpu"),
            nan=NUMERICAL_ZERO,
            posinf=NUMERICAL_ZERO,
            neginf=-NUMERICAL_ZERO,
        )
        np.save(reps_dir / f"{_safe_name(name)}.npy", features.numpy())
        record = _evaluate_candidate(
            name,
            method,
            features,
            graph,
            k,
            declared_baseline=declared_baseline,
            random_summary=random_summary,
        )
        records.append(record)
        (clusters_dir / f"{_safe_name(name)}_clusters.json").write_text(
            json.dumps(
                {
                    "labels": record["labels"],
                    "ari": record["ari"],
                    "nmi": record["nmi"],
                    "observable_selection_score": record["observable_selection_score"],
                    "cluster_masses": record["cluster_masses"],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    selected = max(records, key=lambda item: float(item["observable_selection_score"]))
    evaluator_best = max(records, key=lambda item: (float(item["ari"]) + float(item["nmi"]), float(item["ari"])))
    measured_baseline = next(record for record in records if record["candidate"] == "local_logit_baseline")
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        **DISC15_AUDIT,
        "schema": "scope_static_stage2c_disc15_local_logit_mechanism_v1",
        "question": "Can fitted local inverse representations be denoised, factorized, and clustered better than direct S/alpha learning?",
        "stage2a_closure": (
            "direct_shared_assignment_likelihood_learning_does_not_recover_hidden_omega_"
            "even_though_local_inverse_logits_contain_substantial_target_signal"
        ),
        "K_mode": "known_K_synthetic_audit",
        "local_logit_source": str(local_source),
        "declared_local_logit_baseline": declared_baseline,
        "measured_local_logit_baseline": _compact_candidate(measured_baseline),
        "random_partition_baseline": random_summary,
        "selection_rule": "observable_cluster_health_only",
        "selected_by_observable_candidate": _compact_candidate(selected),
        "evaluator_best_candidate": _compact_candidate(evaluator_best),
        "selected_beats_declared_local_logit_baseline": bool(selected["beats_declared_local_logit_baseline"]),
        "any_candidate_beats_declared_local_logit_baseline": bool(any(record["beats_declared_local_logit_baseline"] for record in records)),
        "stability_across_seeds": _stability_across_seeded_candidates(records),
        "disc15_result": _disc15_result(selected, evaluator_best, declared_baseline),
        "records": records,
    }
    _write_outputs(output, result)
    print(format_disc15_terminal_summary(result))
    return result


def _build_candidates(graph, local_logits: torch.Tensor, cfg: dict[str, object], k: int) -> list[tuple[str, torch.Tensor, str]]:
    candidates: list[tuple[str, torch.Tensor, str]] = [
        ("local_logit_baseline", local_logits, "deterministic_kmeans"),
        ("local_logit_probability", local_probability_features(local_logits), "deterministic_kmeans"),
    ]
    for env in range(local_logits.shape[1]):
        candidates.append((f"single_env_local_logit_env{env}", local_logits[:, env : env + 1], "deterministic_kmeans"))

    structural = structural_signature(graph)
    candidates.append(("structural_plus_local_logit", combined_signature(structural, local_logits), "deterministic_kmeans"))

    smooth_strength = float(cfg.get("graph_smoothing_strength", 0.55))
    smooth_steps = int(cfg.get("graph_smoothing_steps", 2))
    smoothed = graph_smooth_features(graph, local_logits, strength=smooth_strength, steps=smooth_steps)
    candidates.append((f"graph_smoothed_local_s{smooth_steps}", smoothed, "graph_smoothing_kmeans"))
    candidates.append(
        (
            f"structural_plus_graph_smoothed_local_s{smooth_steps}",
            combined_signature(structural, smoothed),
            "graph_smoothing_kmeans",
        )
    )

    pca_ranks = [int(rank) for rank in cfg.get("pca_ranks", [1, 2, 3, 4])]
    for rank in pca_ranks:
        candidates.append((f"pca_scores_rank{rank}", pca_scores(local_logits, rank), "pca_scores_kmeans"))
        candidates.append((f"pca_denoised_rank{rank}", pca_denoised_features(local_logits, rank), "pca_denoised_kmeans"))
        candidates.append(
            (
                f"graph_smoothed_pca_scores_rank{rank}",
                pca_scores(smoothed, rank),
                "graph_smoothed_pca_kmeans",
            )
        )

    candidates.append(("spectral_similarity_local", spectral_similarity_embedding(local_logits, k), "spectral_similarity_kmeans"))

    nmf_rank = int(cfg.get("nmf_rank", k))
    nmf_steps = int(cfg.get("nmf_steps", 200))
    for seed in [int(seed) for seed in cfg.get("nmf_seeds", [0, 1, 2])]:
        codes = nmf_codes(local_logits, nmf_rank, seed=seed, steps=nmf_steps)
        candidates.append((f"nmf_codes_rank{nmf_rank}_seed{seed}", codes, "nmf_code_kmeans"))
        candidates.append(
            (
                f"nmf_overlap_top2_rank{nmf_rank}_seed{seed}",
                overlapping_topk_codes(codes, topk=2),
                "overlapping_nmf_code_kmeans",
            )
        )
    return candidates


def _evaluate_candidate(
    name: str,
    method: str,
    features: torch.Tensor,
    graph,
    k: int,
    *,
    declared_baseline: dict[str, float],
    random_summary: dict[str, float],
) -> dict[str, object]:
    clustering = deterministic_kmeans(features, k)
    partition = evaluate_partition(
        clustering.labels,
        graph.orbit_ids,
        num_clusters=k,
        random_baseline=random_summary,
    )
    split_merge = split_merge_audit(clustering.labels, graph.orbit_ids)
    margin = _cluster_margin(features, clustering.labels, clustering.centers)
    ari = float(partition["ari"])
    nmi = float(partition["nmi"])
    return {
        "candidate": name,
        "method": method,
        "feature_shape": [int(features.shape[0]), int(features.shape[1])],
        "finite_features": bool(torch.isfinite(features).all().item()),
        "labels": [int(value) for value in clustering.labels.tolist()],
        "ari": ari,
        "nmi": nmi,
        "ari_nmi_used_for_selection": False,
        "active_clusters": int(clustering.active_clusters),
        "cluster_masses": clustering.cluster_masses,
        "cluster_mass_entropy_normalized": float(clustering.cluster_mass_entropy_normalized),
        "within_cluster_dispersion": float(clustering.within_cluster_dispersion),
        "silhouette_like": float(clustering.silhouette_like),
        "cluster_margin": float(margin),
        "observable_selection_score": float(clustering.observable_selection_score),
        "beats_declared_local_logit_baseline": bool(ari > declared_baseline["ari"] and nmi > declared_baseline["nmi"]),
        **{key: value for key, value in partition.items() if key not in {"ari", "nmi", "cluster_masses"}},
        **split_merge,
    }


def _cluster_margin(features: torch.Tensor, labels: torch.Tensor, centers: torch.Tensor) -> float:
    x = standardize_features(features)
    if x.numel() == 0 or centers.shape[0] <= 1:
        return 0.0
    distances = torch.cdist(x, centers, p=2)
    labels = labels.to(dtype=torch.long)
    own = distances[torch.arange(x.shape[0]), labels]
    masked = distances.clone()
    masked[torch.arange(x.shape[0]), labels] = float("inf")
    other = torch.min(masked, dim=1).values
    margin = other - own
    finite = torch.isfinite(margin)
    return float(margin[finite].mean().item()) if bool(finite.any()) else 0.0


def _compact_candidate(record: dict[str, object]) -> dict[str, object]:
    return {
        "candidate": record["candidate"],
        "method": record["method"],
        "ari": record["ari"],
        "nmi": record["nmi"],
        "active_clusters": record["active_clusters"],
        "observable_selection_score": record["observable_selection_score"],
        "cluster_margin": record["cluster_margin"],
        "beats_declared_local_logit_baseline": record["beats_declared_local_logit_baseline"],
    }


def _disc15_result(
    selected: dict[str, object],
    evaluator_best: dict[str, object],
    declared_baseline: dict[str, float],
) -> str:
    selected_ari = float(selected["ari"])
    selected_nmi = float(selected["nmi"])
    if selected_ari >= 0.80 and selected_nmi >= 0.80:
        return "strong_local_mechanism_recovery"
    if bool(selected["beats_declared_local_logit_baseline"]):
        return "observable_selected_beats_local_logit_baseline"
    if bool(evaluator_best["beats_declared_local_logit_baseline"]):
        return "evaluator_only_candidate_beats_baseline_no_observable_selection_claim"
    if selected_nmi >= declared_baseline["nmi"] or selected_ari >= declared_baseline["ari"]:
        return "partial_metric_gain_without_full_baseline_win"
    return "no_improvement_over_local_logit_baseline"


def _stability_across_seeded_candidates(records: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for record in records:
        name = str(record["candidate"])
        if "_seed" not in name:
            continue
        family = name.rsplit("_seed", 1)[0]
        grouped.setdefault(family, []).append(record)
    summary = {}
    for family, items in grouped.items():
        if len(items) < 2:
            continue
        values = []
        for left_idx, left in enumerate(items):
            for right in items[left_idx + 1 :]:
                values.append(normalized_mutual_info(left["labels"], right["labels"]))
        summary[family] = {
            "num_seeds": len(items),
            "mean_pairwise_nmi": float(sum(values) / len(values)) if values else 1.0,
            "min_pairwise_nmi": float(min(values)) if values else 1.0,
        }
    return summary


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "disc15_summary.md").write_text(format_disc15_summary_markdown(result))
    (output / "run_selection_audit.json").write_text(
        json.dumps(
            {
                "selection_rule": result["selection_rule"],
                "ari_nmi_used_for_selection": result["ari_nmi_used_for_selection"],
                "selected_by_observable_candidate": result["selected_by_observable_candidate"],
                "evaluator_best_candidate": result["evaluator_best_candidate"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def format_disc15_summary_markdown(result: dict[str, object]) -> str:
    selected = result["selected_by_observable_candidate"]
    best = result["evaluator_best_candidate"]
    baseline = result["measured_local_logit_baseline"]
    lines = [
        "# DISC15 Local-Logit-To-Mechanism Discovery",
        "",
        f"- Result: `{result['disc15_result']}`",
        f"- Source: `{result['local_logit_source']}`",
        f"- Selection rule: `{result['selection_rule']}`",
        f"- ARI/NMI used for selection: `{str(result['ari_nmi_used_for_selection']).lower()}`",
        "",
        "| candidate | role | ARI | NMI | active | score | beats baseline |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        _summary_row(baseline, "measured local-logit baseline"),
        _summary_row(selected, "observable-selected"),
        _summary_row(best, "evaluator-best"),
        "",
        "## Top Observable Candidates",
        "",
        "| candidate | ARI | NMI | active | score | margin |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    top = sorted(result["records"], key=lambda item: float(item["observable_selection_score"]), reverse=True)[:8]
    for record in top:
        lines.append(
            f"| {record['candidate']} | {_fmt(record['ari'])} | {_fmt(record['nmi'])} | "
            f"{record['active_clusters']} | {_fmt(record['observable_selection_score'])} | {_fmt(record['cluster_margin'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def _summary_row(record: dict[str, object], role: str) -> str:
    return (
        f"| {record['candidate']} | {role} | {_fmt(record['ari'])} | {_fmt(record['nmi'])} | "
        f"{record['active_clusters']} | {_fmt(record['observable_selection_score'])} | "
        f"{str(record['beats_declared_local_logit_baseline']).lower()} |"
    )


def format_disc15_terminal_summary(result: dict[str, object]) -> str:
    selected = result["selected_by_observable_candidate"]
    best = result["evaluator_best_candidate"]
    baseline = result["measured_local_logit_baseline"]
    return "\n".join(
        [
            "Stage 2C DISC15 Local-Logit-To-Mechanism Discovery",
            f"config: {result.get('config_path')}",
            f"output: {result.get('output_dir')}",
            f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
            f"result: {result['disc15_result']}",
            f"baseline: ARI={_fmt(baseline['ari'])} NMI={_fmt(baseline['nmi'])}",
            (
                "selected: "
                f"{selected['candidate']} ARI={_fmt(selected['ari'])} NMI={_fmt(selected['nmi'])} "
                f"score={_fmt(selected['observable_selection_score'])}"
            ),
            (
                "evaluator-best: "
                f"{best['candidate']} ARI={_fmt(best['ari'])} NMI={_fmt(best['nmi'])} "
                f"beats_baseline={str(best['beats_declared_local_logit_baseline']).lower()}"
            ),
        ]
    )


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage 2C DISC15 local-logit mechanism discovery.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_local_mechanism_discovery(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

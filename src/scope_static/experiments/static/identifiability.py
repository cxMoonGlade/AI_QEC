from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.static.plan import ExperimentPlan
from scope_static.dem.fields import LocalFaultLogitField
from scope_static.identifiability import (
    classify_passive_identifiability,
    combined_signature,
    deterministic_kmeans,
    evaluate_partition,
    local_logit_signature,
    moment_spectral_signature,
    random_baseline_summary,
    random_partition_baseline,
    shuffled_omega_control,
    structural_signature,
)
from scope_static.dem.stim_dem import sample_observations_from_logits
from scope_static.dem.teacher_logits import make_teacher_logits
from scope_static.dem.training import fit_field
from scope_static.dem.windows import WindowPlan


SIGNATURE_FAMILIES = ("structural", "local_logit", "moment_spectral", "combined")


def run_identifiability_audit(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("identifiability", {}))
    k_mode = str(cfg.get("K_mode", "known_K_synthetic_audit"))
    if k_mode != "known_K_synthetic_audit":
        raise ValueError("first DISC10 pass only supports K_mode='known_K_synthetic_audit'")

    output = plan.output_dir
    signatures_dir = output / "signatures"
    clusters_dir = output / "clusters"
    signatures_dir.mkdir(parents=True, exist_ok=True)
    clusters_dir.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    K = int(graph.O)
    if K <= 0:
        raise ValueError("known_K_synthetic_audit requires at least one hidden orbit")
    windows = WindowPlan.from_config(graph, plan.windows_cfg)
    spectral_rank = int(cfg.get("spectral_rank", 3))
    random_trials = int(cfg.get("random_baseline_trials", 32))
    local_steps = int(cfg.get("local_fit_steps", plan.training_cfg.get("steps", 100)))
    local_lr = float(cfg.get("local_fit_lr", plan.training_cfg.get("lr", 0.05)))

    records: list[dict[str, object]] = []
    null_records: list[dict[str, object]] = []
    signature_payloads: dict[str, list[np.ndarray]] = {family: [] for family in SIGNATURE_FAMILIES}
    cluster_payloads: dict[str, list[dict[str, object]]] = {family: [] for family in SIGNATURE_FAMILIES}

    for seed in plan.seeds:
        for teacher_case in plan.teacher_cases:
            teacher_logits = make_teacher_logits(
                graph,
                mode=teacher_case.mode,
                epsilon_break=teacher_case.epsilon_break,
                seed=int(seed),
                dtype=plan.dtype,
            )
            for shots in plan.shot_budgets:
                observations = sample_observations_from_logits(
                    graph,
                    teacher_logits,
                    shots=int(shots),
                    seed=int(seed) + int(shots),
                )
                local_logits = _fit_visible_local_logits(
                    plan,
                    graph,
                    observations,
                    windows=windows,
                    steps=local_steps,
                    lr=local_lr,
                )
                signatures = _build_signatures(
                    graph,
                    observations,
                    local_logits=local_logits,
                    spectral_rank=spectral_rank,
                )
                random_baseline = random_baseline_summary(
                    random_partition_baseline(graph.M, K, seed=_stable_seed(seed, shots, 991), num_trials=random_trials),
                    graph.orbit_ids,
                )
                context = {
                    "seed": int(seed),
                    "teacher_mode": teacher_case.mode,
                    "epsilon_break": float(teacher_case.epsilon_break),
                    "shots": int(shots),
                    "K": K,
                    "K_mode": k_mode,
                }

                for family in SIGNATURE_FAMILIES:
                    signature = signatures[family]
                    signature_payloads[family].append(signature.numpy())
                    result = deterministic_kmeans(signature, K)
                    eval_metrics = evaluate_partition(
                        result.labels,
                        graph.orbit_ids,
                        num_clusters=K,
                        random_baseline=random_baseline,
                    )
                    shuffle_control = shuffled_omega_control(
                        result.labels,
                        graph.orbit_ids,
                        seed=_stable_seed(seed, shots, 313),
                    )
                    record = {
                        "stage": "stage2A.0.5",
                        "experiment": "DISC10_moment_spectral_seed",
                        "signature_family": family,
                        "K_mode": k_mode,
                        "selection_rule": "observable_only",
                        "ari_nmi_used_for_selection": False,
                        "hidden_partition_available_to_learner": False,
                        "hidden_partition_used_by": "synthetic_teacher_and_evaluator_only",
                        "feature_leakage_guardrail": "signatures_do_not_use_orbit_ids_or_centered_phi",
                        "feature_dim": int(signature.shape[1]),
                        "finite_signature": bool(torch.isfinite(signature).all().item()),
                        "observable_selection_score": float(result.observable_selection_score),
                        "within_cluster_dispersion": float(result.within_cluster_dispersion),
                        "silhouette_like": float(result.silhouette_like),
                        "cluster_mass_entropy_normalized": float(result.cluster_mass_entropy_normalized),
                        "random_baseline": random_baseline,
                        **context,
                        **eval_metrics,
                        **shuffle_control,
                    }
                    records.append(record)
                    cluster_payloads[family].append(
                        {
                            "context": context,
                            "labels": [int(value) for value in result.labels.tolist()],
                            "cluster_masses": result.cluster_masses,
                            "active_clusters": int(result.active_clusters),
                            "observable_selection_score": float(result.observable_selection_score),
                            "within_cluster_dispersion": float(result.within_cluster_dispersion),
                            "silhouette_like": float(result.silhouette_like),
                        }
                    )

                random_signature = _random_gaussian_signature(
                    graph.M,
                    signatures["combined"].shape[1],
                    seed=_stable_seed(seed, shots, 707),
                )
                random_result = deterministic_kmeans(random_signature, K)
                random_eval = evaluate_partition(
                    random_result.labels,
                    graph.orbit_ids,
                    num_clusters=K,
                    random_baseline=random_baseline,
                )
                null_records.append(
                    {
                        "control": "random_gaussian_signature",
                        "selection_rule": "observable_only",
                        "ari_nmi_used_for_selection": False,
                        "feature_dim": int(random_signature.shape[1]),
                        "observable_selection_score": float(random_result.observable_selection_score),
                        "random_baseline": random_baseline,
                        **context,
                        **random_eval,
                    }
                )

    for family, arrays in signature_payloads.items():
        np.save(signatures_dir / f"{family}.npy", np.stack(arrays, axis=0))
        (clusters_dir / f"{family}_clusters.json").write_text(
            json.dumps({"family": family, "records": cluster_payloads[family]}, indent=2, sort_keys=True) + "\n"
        )

    family_summaries = _family_summaries(records)
    best_family = _select_best_visible_family(family_summaries)
    best_summary = family_summaries[best_family]
    passive_result = classify_passive_identifiability(
        ari=float(best_summary["mean_ari"]),
        nmi=float(best_summary["mean_nmi"]),
        active_clusters=int(round(float(best_summary["min_active_clusters"]))),
        num_clusters=K,
        random_ari=float(best_summary["mean_random_ari"]),
        random_nmi=float(best_summary["mean_random_nmi"]),
    )
    metrics = {
        "stage": "stage2A.0.5",
        "experiment": "DISC10_moment_spectral_seed",
        "schema": "scope_static_disc10_identifiability_v1",
        "config_path": str(plan.config_path),
        "output_dir": str(output),
        "K_mode": k_mode,
        "K": K,
        "num_faults_M": int(graph.M),
        "num_detectors": int(graph.num_detectors),
        "num_observables": int(graph.num_observables),
        "evaluator_only_rule": "ARI/NMI are computed only after clustering and never select signatures or hyperparameters.",
        "observable_selection_criteria": [
            "cluster_balance",
            "within_cluster_dispersion",
            "silhouette_like_score",
            "moment_signature_compactness",
            "determinism",
            "finite_value_checks",
        ],
        "disc10_audit": {
            "best_visible_signature_family": best_family,
            "ari": float(best_summary["mean_ari"]),
            "nmi": float(best_summary["mean_nmi"]),
            "active_clusters": float(best_summary["mean_active_clusters"]),
            "min_active_clusters": int(best_summary["min_active_clusters"]),
            "passive_identifiability_result": passive_result,
        },
        "disc10_seed_candidate": {
            "recommended_for_stage2a1_init": passive_result in {"separates", "weak"},
            "signature_family": best_family,
            "selection_rule": "observable_only",
        },
        "family_summaries": family_summaries,
        "records": records,
        "null_controls": {
            "random_gaussian_signature": _aggregate_records(null_records),
            "shuffled_omega_evaluator": _aggregate_shuffled_controls(records),
            "per_context": null_records,
        },
        "claim_boundary": (
            "A positive DISC10 means passive visible signatures contain enough information to separate "
            "the synthetic hidden quotient; it is not a physical-mechanism claim and does not prove "
            "the likelihood learner can recover omega(j)."
        ),
        "artifacts": {
            "metrics": str(output / "disc10_metrics.json"),
            "summary_md": str(output / "disc10_summary.md"),
            "signatures_dir": str(signatures_dir),
            "clusters_dir": str(clusters_dir),
        },
    }
    (output / "disc10_metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    (output / "disc10_summary.md").write_text(format_disc10_summary_markdown(metrics))
    print_disc10_summary(metrics)
    return metrics


def format_disc10_summary_markdown(metrics: dict[str, object]) -> str:
    audit = metrics["disc10_audit"]
    lines = [
        "# DISC10 Passive Identifiability Audit",
        "",
        f"- Result: `{audit['passive_identifiability_result']}`",
        f"- Best visible signature: `{audit['best_visible_signature_family']}`",
        f"- K mode: `{metrics['K_mode']}`",
        "",
        "ARI/NMI are evaluator-only diagnostics and are not used for signature selection.",
        "",
        "| family | score | ARI | NMI | active | result |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for family, summary in metrics["family_summaries"].items():
        lines.append(
            f"| {family} | {_fmt(summary['mean_observable_selection_score'])} | "
            f"{_fmt(summary['mean_ari'])} | {_fmt(summary['mean_nmi'])} | "
            f"{_fmt(summary['mean_active_clusters'])} | {summary['modal_result']} |"
        )
    lines.extend(["", "## Claim Boundary", "", str(metrics["claim_boundary"]), ""])
    return "\n".join(lines)


def print_disc10_summary(metrics: dict[str, object]) -> None:
    audit = metrics["disc10_audit"]
    print("Stage 2A.0.5 DISC10 Passive Identifiability Audit")
    print(f"config: {metrics['config_path']}")
    print(f"output: {metrics['output_dir']}")
    print(
        f"best: {audit['best_visible_signature_family']} | "
        f"result: {audit['passive_identifiability_result']} | "
        f"ARI={_fmt(audit['ari'])} NMI={_fmt(audit['nmi'])} active={_fmt(audit['active_clusters'])}"
    )
    print("")
    print("family           score    ARI     NMI     active  result")
    print("---------------  -------  ------  ------  ------  --------")
    for family, summary in metrics["family_summaries"].items():
        print(
            f"{family:<15}  {_fmt(summary['mean_observable_selection_score']):>7}  "
            f"{_fmt(summary['mean_ari']):>6}  {_fmt(summary['mean_nmi']):>6}  "
            f"{_fmt(summary['mean_active_clusters']):>6}  {summary['modal_result']}"
        )
    print("")
    print(f"metrics: {metrics['artifacts']['metrics']}")


def _fit_visible_local_logits(
    plan: ExperimentPlan,
    graph,
    observations: torch.Tensor,
    *,
    windows: WindowPlan,
    steps: int,
    lr: float,
) -> torch.Tensor:
    field = LocalFaultLogitField.from_graph(graph, dtype=plan.dtype)
    fit = fit_field(
        graph,
        field,
        observations,
        steps=int(steps),
        lr=float(lr),
        aggregate_unique=plan.aggregate_unique,
        device=plan.device,
        backend=plan.likelihood_backend,
        cuda_kernel_variant=str(plan.training_cfg.get("cuda_kernel_variant", "dp")),
        likelihood_objective=plan.likelihood_objective,
        windows=windows,
    )
    fitted = fit["field"]
    return fitted.realized_logits(graph).detach().cpu().to(dtype=torch.float64)


def _build_signatures(
    graph,
    observations: torch.Tensor,
    *,
    local_logits: torch.Tensor,
    spectral_rank: int,
) -> dict[str, torch.Tensor]:
    structural = structural_signature(graph)
    local = local_logit_signature(local_logits)
    moment = moment_spectral_signature(graph, observations, spectral_rank=spectral_rank)
    return {
        "structural": structural,
        "local_logit": local,
        "moment_spectral": moment,
        "combined": combined_signature(structural, local, moment),
    }


def _family_summaries(records: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    summaries: dict[str, dict[str, object]] = {}
    for family in SIGNATURE_FAMILIES:
        group = [record for record in records if record["signature_family"] == family]
        random_baselines = [record["random_baseline"] for record in group]
        modal_result = _modal([str(record["passive_identifiability_result"]) for record in group])
        summaries[family] = {
            "num_records": len(group),
            "mean_observable_selection_score": _mean(group, "observable_selection_score"),
            "mean_within_cluster_dispersion": _mean(group, "within_cluster_dispersion"),
            "mean_silhouette_like": _mean(group, "silhouette_like"),
            "mean_cluster_mass_entropy_normalized": _mean(group, "cluster_mass_entropy_normalized"),
            "mean_ari": _mean(group, "ari"),
            "mean_nmi": _mean(group, "nmi"),
            "mean_active_clusters": _mean(group, "active_clusters"),
            "min_active_clusters": min(int(record["active_clusters"]) for record in group) if group else 0,
            "mean_random_ari": _mean_dicts(random_baselines, "ari_mean"),
            "mean_random_nmi": _mean_dicts(random_baselines, "nmi_mean"),
            "modal_result": modal_result,
            "ari_nmi_used_for_selection": False,
            "selection_rule": "observable_only",
        }
    return summaries


def _select_best_visible_family(summaries: dict[str, dict[str, object]]) -> str:
    order = {family: idx for idx, family in enumerate(SIGNATURE_FAMILIES)}
    return max(
        summaries,
        key=lambda family: (
            float(summaries[family]["mean_observable_selection_score"]),
            -order[family],
        ),
    )


def _aggregate_records(records: list[dict[str, object]]) -> dict[str, object]:
    if not records:
        return {"num_records": 0}
    baseline_ari = _mean_dicts([record["random_baseline"] for record in records], "ari_mean")
    baseline_nmi = _mean_dicts([record["random_baseline"] for record in records], "nmi_mean")
    mean_ari = _mean(records, "ari")
    mean_nmi = _mean(records, "nmi")
    return {
        "num_records": len(records),
        "mean_ari": mean_ari,
        "mean_nmi": mean_nmi,
        "mean_random_baseline_ari": baseline_ari,
        "mean_random_baseline_nmi": baseline_nmi,
        "mean_ari_gap_vs_random": mean_ari - baseline_ari,
        "mean_nmi_gap_vs_random": mean_nmi - baseline_nmi,
        "mean_active_clusters": _mean(records, "active_clusters"),
        "modal_result": _modal([str(record["passive_identifiability_result"]) for record in records]),
    }


def _aggregate_shuffled_controls(records: list[dict[str, object]]) -> dict[str, object]:
    if not records:
        return {"num_records": 0}
    return {
        "num_records": len(records),
        "mean_shuffled_omega_ari": _mean(records, "shuffled_omega_ari"),
        "mean_shuffled_omega_nmi": _mean(records, "shuffled_omega_nmi"),
    }


def _random_gaussian_signature(num_faults: int, feature_dim: int, *, seed: int) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    return torch.randn((int(num_faults), int(feature_dim)), generator=generator, dtype=torch.float64)


def _stable_seed(seed: int, shots: int, salt: int) -> int:
    return int(seed) * 100_003 + int(shots) * 97 + int(salt)


def _mean(records: list[dict[str, object]], key: str) -> float:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return float(sum(values) / len(values)) if values else 0.0


def _mean_dicts(records: list[dict[str, object]], key: str) -> float:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return float(sum(values) / len(values)) if values else 0.0


def _modal(values: list[str]) -> str:
    if not values:
        return "failed"
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage 2A.0.5 DISC10 passive identifiability audit.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_identifiability_audit(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

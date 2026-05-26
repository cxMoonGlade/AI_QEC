from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

import torch
import yaml

from scope_static.experiments.plan import ExperimentPlan
from scope_static.experiments.run_static_disc16_observability import (
    _build_objectives,
    _fit_local_inverse,
    _heldout_nll,
    _pairwise_label_nmi,
    _probability_variance,
    _sample_env_observations,
)
from scope_static.identifiability import deterministic_kmeans, evaluate_partition, random_baseline_summary, random_partition_baseline
from scope_static.local_mechanism import local_probability_features, split_merge_audit
from scope_static.multi_env import make_multi_env_teacher


DISC16B_AUDIT = {
    "stage": "stage2C",
    "experiment": "DISC16b_local_inverse_recovery_robustness",
    "uses_hidden_omega_for_training": False,
    "uses_hidden_omega_for_initialization": False,
    "uses_hidden_omega_for_checkpoint_selection": False,
    "uses_hidden_omega_for_final_evaluation": True,
    "ari_nmi_used_for_selection": False,
    "candidate_selection": "disabled_predeclared_representation",
    "predeclared_representation": "local_logit_probability",
}


def run_disc16b_robustness(config_path: str | Path, *, output_dir: str | Path | None = None) -> dict[str, object]:
    plan = ExperimentPlan.from_path(config_path, output_dir=output_dir)
    cfg = dict(plan.config.get("disc16b", {}))
    multi_env_cfg = dict(plan.config.get("multi_env", {}))
    output = plan.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "config_snapshot.yaml").write_text(yaml.safe_dump(plan.config, sort_keys=False))

    graph = plan.build_graph(plan.teacher_residual_rank)
    train_env_ids = tuple(int(env) for env in cfg.get("train_env_ids", multi_env_cfg.get("train_env_ids", [0, 1, 2, 3])))
    synthetic_seeds = tuple(int(seed) for seed in cfg.get("synthetic_seeds", [0, 1, 2, 3, 4]))
    shot_budgets = tuple(int(shots) for shots in cfg.get("shot_budgets", [10_000, 25_000, 50_000]))
    regimes = tuple(_normalize_regime(item, multi_env_cfg) for item in cfg.get("regimes", _default_regimes()))
    bootstrap_replicates = int(cfg.get("bootstrap_replicates", 2))
    heldout_shots = int(cfg.get("heldout_shots", plan.heldout_shots))
    steps = int(cfg.get("local_inverse_steps", plan.training_cfg.get("steps", 200)))
    lr = float(cfg.get("lr", plan.training_cfg.get("lr", 0.05)))
    k = int(cfg.get("num_clusters", graph.O))
    random_summary = random_baseline_summary(
        random_partition_baseline(
            graph.M,
            k,
            seed=int(cfg.get("random_baseline_seed", 0)),
            num_trials=int(cfg.get("random_baseline_trials", 32)),
        ),
        graph.orbit_ids,
    )

    condition_records: list[dict[str, object]] = []
    cluster_audit: dict[str, object] = {}
    for regime_index, regime in enumerate(regimes):
        for synthetic_seed in synthetic_seeds:
            teacher = make_multi_env_teacher(
                graph,
                seed=int(synthetic_seed),
                dtype=plan.dtype,
                contrast_strength=float(regime["contrast_strength"]),
                design=str(regime["environment_design"]),
            )
            heldout_observations = _sample_env_observations(
                graph,
                teacher.logits_by_env,
                shots=heldout_shots,
                seed_base=_seed_base(cfg, "heldout_seed_base", 700_000, regime_index, synthetic_seed, 0),
                env_ids=train_env_ids,
            )
            heldout_objectives = _build_objectives(plan, graph, heldout_observations, train_env_ids)
            for shot_budget in shot_budgets:
                replicate_records = []
                probability_representations = []
                replicate_labels = []
                for replicate in range(bootstrap_replicates):
                    observations = _sample_env_observations(
                        graph,
                        teacher.logits_by_env,
                        shots=shot_budget,
                        seed_base=_seed_base(cfg, "sample_seed_base", 100_000, regime_index, synthetic_seed, replicate)
                        + int(shot_budget),
                        env_ids=train_env_ids,
                    )
                    fit = _fit_local_inverse(
                        plan,
                        graph,
                        observations,
                        train_env_ids=train_env_ids,
                        steps=steps,
                        lr=lr,
                    )
                    local_logits = fit["local_logits"]
                    representation = local_probability_features(local_logits)
                    clustering = deterministic_kmeans(representation, k)
                    recovery = evaluate_partition(clustering.labels, graph.orbit_ids, num_clusters=k, random_baseline=random_summary)
                    heldout_nll = _heldout_nll(heldout_objectives, local_logits, train_env_ids, device=plan.device)
                    record = {
                        "regime": regime["name"],
                        "synthetic_seed": int(synthetic_seed),
                        "shots": int(shot_budget),
                        "replicate": int(replicate),
                        "train_final_nll": fit["train_final_nll"],
                        "heldout_local_inverse_nll": heldout_nll,
                        "ari": recovery["ari"],
                        "nmi": recovery["nmi"],
                        "active_clusters": recovery["active_clusters"],
                        "cluster_masses": recovery["cluster_masses"],
                        "dead_clusters": recovery["dead_clusters"],
                        "within_cluster_dispersion": clustering.within_cluster_dispersion,
                        "silhouette_like": clustering.silhouette_like,
                        "cluster_mass_entropy_normalized": clustering.cluster_mass_entropy_normalized,
                        "observable_selection_score": clustering.observable_selection_score,
                        "labels": [int(value) for value in clustering.labels.tolist()],
                        **split_merge_audit(clustering.labels, graph.orbit_ids),
                    }
                    replicate_records.append(record)
                    probability_representations.append(representation)
                    replicate_labels.append(clustering.labels)

                summary = _condition_summary(
                    regime=regime,
                    synthetic_seed=int(synthetic_seed),
                    shots=int(shot_budget),
                    num_clusters=k,
                    records=replicate_records,
                    probability_representations=probability_representations,
                    labels=replicate_labels,
                )
                condition_records.append(summary)
                key = f"{regime['name']}/seed_{synthetic_seed}/shots_{shot_budget}"
                cluster_audit[key] = {
                    "primary_replicate": 0,
                    "labels": replicate_records[0]["labels"],
                    "cluster_masses": replicate_records[0]["cluster_masses"],
                    "replicates": [
                        {
                            "replicate": record["replicate"],
                            "ari": record["ari"],
                            "nmi": record["nmi"],
                            "active_clusters": record["active_clusters"],
                            "cluster_masses": record["cluster_masses"],
                            "mean_splits_per_omega": record["mean_splits_per_omega"],
                            "mean_cluster_purity": record["mean_cluster_purity"],
                        }
                        for record in replicate_records
                    ],
                }

    failure_cases = _failure_cases(condition_records, k)
    aggregate_by_regime_budget = _aggregate_by_regime_budget(condition_records)
    result_label = _disc16b_conclusion(condition_records)
    result = {
        **graph.audit_dict(
            exact_likelihood_trainable=bool(plan.training_cfg.get("exact_likelihood_trainable", False)),
            dem_fault_logit_claim=bool(plan.training_cfg.get("dem_fault_logit_claim", False)),
            cptp_gksl_claim=bool(plan.training_cfg.get("cptp_gksl_claim", False)),
        ),
        **plan.output_audit_dict(),
        **DISC16B_AUDIT,
        "schema": "scope_static_stage2c_disc16b_robustness_v1",
        "question": "Does strong local-inverse probability recovery hold beyond one controlled d3/r1 synthetic instance?",
        "K_mode": "known_K_synthetic_audit",
        "altered_orbit_count_available": False,
        "regime_axis": "synthetic_multi_env_teacher_contrast",
        "synthetic_seeds": [int(seed) for seed in synthetic_seeds],
        "shot_budgets": [int(value) for value in shot_budgets],
        "regimes": [dict(regime) for regime in regimes],
        "train_env_ids": [int(env) for env in train_env_ids],
        "bootstrap_replicates": int(bootstrap_replicates),
        "heldout_shots": int(heldout_shots),
        "local_inverse_steps": int(steps),
        "strong_threshold": {"ari": 0.80, "nmi": 0.80, "active_clusters_min": max(1, k - 1)},
        "random_partition_baseline": random_summary,
        "robustness_grid": condition_records,
        "aggregate_by_regime_budget": aggregate_by_regime_budget,
        "failure_cases": failure_cases,
        "cluster_audit": cluster_audit,
        "disc16b_result": result_label,
    }
    _write_outputs(output, result)
    print(format_disc16b_terminal_summary(result))
    return result


def _normalize_regime(raw: object, multi_env_cfg: dict[str, object]) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError("each DISC16b regime must be a mapping")
    return {
        "name": str(raw.get("name", "default")),
        "contrast_strength": float(raw.get("contrast_strength", multi_env_cfg.get("contrast_strength", 1.0))),
        "environment_design": str(raw.get("environment_design", multi_env_cfg.get("environment_design", "default"))),
    }


def _default_regimes() -> list[dict[str, object]]:
    return [
        {"name": "easy", "contrast_strength": 1.25, "environment_design": "default"},
        {"name": "default", "contrast_strength": 1.0, "environment_design": "default"},
        {"name": "harder", "contrast_strength": 0.75, "environment_design": "default"},
    ]


def _seed_base(
    cfg: dict[str, object],
    key: str,
    default: int,
    regime_index: int,
    synthetic_seed: int,
    replicate: int,
) -> int:
    return (
        int(cfg.get(key, default))
        + 10_000_000 * int(regime_index)
        + 100_000 * int(synthetic_seed)
        + 10_000 * int(replicate)
    )


def _condition_summary(
    *,
    regime: dict[str, object],
    synthetic_seed: int,
    shots: int,
    num_clusters: int,
    records: list[dict[str, object]],
    probability_representations: list[torch.Tensor],
    labels: list[torch.Tensor],
) -> dict[str, object]:
    ari_values = [float(record["ari"]) for record in records]
    nmi_values = [float(record["nmi"]) for record in records]
    active_values = [int(record["active_clusters"]) for record in records]
    active_min = min(active_values) if active_values else 0
    strong_replicates = [
        bool(record["ari"] >= 0.80 and record["nmi"] >= 0.80 and int(record["active_clusters"]) >= max(1, int(num_clusters) - 1))
        for record in records
    ]
    summary = {
        "regime": regime["name"],
        "contrast_strength": regime["contrast_strength"],
        "environment_design": regime["environment_design"],
        "synthetic_seed": int(synthetic_seed),
        "shots": int(shots),
        "replicates": records,
        "ari_mean": _mean(ari_values),
        "ari_std": _std(ari_values),
        "ari_min": float(min(ari_values)) if ari_values else 0.0,
        "nmi_mean": _mean(nmi_values),
        "nmi_std": _std(nmi_values),
        "nmi_min": float(min(nmi_values)) if nmi_values else 0.0,
        "active_clusters_mean": _mean(active_values),
        "active_clusters_min": int(active_min),
        "heldout_local_inverse_nll_mean": _mean(record["heldout_local_inverse_nll"] for record in records),
        "heldout_local_inverse_nll_std": _std(record["heldout_local_inverse_nll"] for record in records),
        "bootstrap_label_pairwise_nmi": _pairwise_label_nmi(labels),
        "local_logit_probability_variance": _probability_variance(probability_representations),
        "mean_cluster_purity_mean": _mean(record["mean_cluster_purity"] for record in records),
        "mean_splits_per_omega_mean": _mean(record["mean_splits_per_omega"] for record in records),
        "strong_replicates": strong_replicates,
        "strong_all_replicates": bool(strong_replicates and all(strong_replicates)),
    }
    summary["strong_by_mean"] = bool(
        summary["ari_mean"] >= 0.80 and summary["nmi_mean"] >= 0.80 and summary["active_clusters_min"] >= max(1, int(num_clusters) - 1)
    )
    return summary


def _failure_cases(records: list[dict[str, object]], num_clusters: int) -> list[dict[str, object]]:
    failures = []
    active_threshold = max(1, int(num_clusters) - 1)
    for record in records:
        reasons = []
        if float(record["ari_min"]) < 0.80:
            reasons.append("ari_below_0.80")
        if float(record["nmi_min"]) < 0.80:
            reasons.append("nmi_below_0.80")
        if int(record["active_clusters_min"]) < active_threshold:
            reasons.append("active_cluster_deficit")
        if reasons:
            failures.append(
                {
                    "regime": record["regime"],
                    "synthetic_seed": record["synthetic_seed"],
                    "shots": record["shots"],
                    "ari_min": record["ari_min"],
                    "nmi_min": record["nmi_min"],
                    "active_clusters_min": record["active_clusters_min"],
                    "reasons": reasons,
                }
            )
    return failures


def _aggregate_by_regime_budget(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int], list[dict[str, object]]] = {}
    for record in records:
        grouped.setdefault((str(record["regime"]), int(record["shots"])), []).append(record)
    summaries = []
    for (regime, shots), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        summaries.append(
            {
                "regime": regime,
                "shots": int(shots),
                "num_conditions": len(group),
                "ari_mean": _mean(record["ari_mean"] for record in group),
                "ari_std": _std(record["ari_mean"] for record in group),
                "ari_min": float(min(float(record["ari_min"]) for record in group)),
                "nmi_mean": _mean(record["nmi_mean"] for record in group),
                "nmi_std": _std(record["nmi_mean"] for record in group),
                "nmi_min": float(min(float(record["nmi_min"]) for record in group)),
                "active_clusters_min": int(min(int(record["active_clusters_min"]) for record in group)),
                "bootstrap_label_pairwise_nmi_mean": _mean(
                    record["bootstrap_label_pairwise_nmi"]
                    for record in group
                    if record.get("bootstrap_label_pairwise_nmi") is not None
                ),
                "local_logit_probability_variance_mean": _mean(record["local_logit_probability_variance"] for record in group),
                "heldout_local_inverse_nll_mean": _mean(record["heldout_local_inverse_nll_mean"] for record in group),
                "strong_conditions": int(sum(1 for record in group if bool(record["strong_all_replicates"]))),
            }
        )
    return summaries


def _disc16b_conclusion(records: list[dict[str, object]]) -> str:
    if not records:
        return "no_robustness_records"
    strong = [bool(record["strong_all_replicates"]) for record in records]
    strong_fraction = sum(1 for value in strong if value) / len(strong)
    ari_mean = _mean(record["ari_mean"] for record in records)
    nmi_mean = _mean(record["nmi_mean"] for record in records)
    if all(strong):
        return "confirmed_strong_recovery_robust"
    if strong_fraction >= 0.90 and ari_mean >= 0.80 and nmi_mean >= 0.80:
        return "confirmed_strong_recovery_nearly_all_runs"
    if ari_mean >= 0.80 and nmi_mean >= 0.90:
        return "robust_near_strong_some_hard_cases"
    return "fragile_recovery_not_robust_across_grid"


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "robustness_grid.json").write_text(json.dumps(result["robustness_grid"], indent=2, sort_keys=True) + "\n")
    (output / "failure_cases.json").write_text(json.dumps(result["failure_cases"], indent=2, sort_keys=True) + "\n")
    (output / "cluster_audit.json").write_text(json.dumps(result["cluster_audit"], indent=2, sort_keys=True) + "\n")
    (output / "run_selection_audit.json").write_text(
        json.dumps(
            {
                "candidate_selection": result["candidate_selection"],
                "predeclared_representation": result["predeclared_representation"],
                "ari_nmi_used_for_selection": result["ari_nmi_used_for_selection"],
                "uses_hidden_omega_for_training": result["uses_hidden_omega_for_training"],
                "uses_hidden_omega_for_checkpoint_selection": result["uses_hidden_omega_for_checkpoint_selection"],
                "uses_hidden_omega_for_final_evaluation": result["uses_hidden_omega_for_final_evaluation"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (output / "disc16b_summary.md").write_text(format_disc16b_summary(result))


def format_disc16b_summary(result: dict[str, object]) -> str:
    lines = [
        "# DISC16b Local-Inverse Recovery Robustness",
        "",
        f"- Result: `{result['disc16b_result']}`",
        f"- Predeclared representation: `{result['predeclared_representation']}`",
        f"- Candidate selection: `{result['candidate_selection']}`",
        f"- ARI/NMI used for selection: `{str(result['ari_nmi_used_for_selection']).lower()}`",
        f"- Regime axis: `{result['regime_axis']}`",
        "",
        "| regime | shots | seeds | ARI mean | ARI min | NMI mean | NMI min | active min | boot NMI | prob var | strong |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in result["aggregate_by_regime_budget"]:
        lines.append(
            f"| {record['regime']} | {record['shots']} | {record['num_conditions']} | "
            f"{_fmt(record['ari_mean'])} | {_fmt(record['ari_min'])} | "
            f"{_fmt(record['nmi_mean'])} | {_fmt(record['nmi_min'])} | "
            f"{record['active_clusters_min']} | {_fmt(record['bootstrap_label_pairwise_nmi_mean'])} | "
            f"{_fmt(record['local_logit_probability_variance_mean'])} | "
            f"{record['strong_conditions']}/{record['num_conditions']} |"
        )
    lines.extend(
        [
            "",
            f"Failure cases: {len(result['failure_cases'])}",
            "",
            "Interpretation labels:",
            "",
            "- `confirmed_strong_recovery_robust`: every grid condition clears ARI/NMI and active-cluster thresholds.",
            "- `confirmed_strong_recovery_nearly_all_runs`: at least 90% of grid conditions clear thresholds.",
            "- `robust_near_strong_some_hard_cases`: mean recovery is strong/near-strong, with some below-threshold cases.",
            "- `fragile_recovery_not_robust_across_grid`: strong recovery is not stable across the grid.",
            "",
        ]
    )
    return "\n".join(lines)


def format_disc16b_terminal_summary(result: dict[str, object]) -> str:
    lines = [
        "Stage 2C DISC16b Local-Inverse Robustness",
        f"config: {result.get('config_path')}",
        f"output: {result.get('output_dir')}",
        f"metrics: {Path(str(result.get('output_dir'))) / 'metrics.json'}",
        f"result: {result['disc16b_result']} | failures: {len(result['failure_cases'])}",
        "regime   shots  seeds  ARImean  ARImin  NMImean  NMImin  active  bootNMI  strong",
        "-------  -----  -----  -------  ------  -------  ------  ------  -------  ------",
    ]
    for record in result["aggregate_by_regime_budget"]:
        lines.append(
            f"{str(record['regime'])[:7]:<7}  {record['shots']:<5}  {record['num_conditions']:<5}  "
            f"{_fmt(record['ari_mean']):<7}  {_fmt(record['ari_min']):<6}  "
            f"{_fmt(record['nmi_mean']):<7}  {_fmt(record['nmi_min']):<6}  "
            f"{record['active_clusters_min']:<6}  {_fmt(record['bootstrap_label_pairwise_nmi_mean']):<7}  "
            f"{record['strong_conditions']}/{record['num_conditions']}"
        )
    return "\n".join(lines)


def _mean(values) -> float:
    numbers = [float(value) for value in values]
    return float(sum(numbers) / len(numbers)) if numbers else 0.0


def _std(values) -> float:
    numbers = [float(value) for value in values]
    if len(numbers) <= 1:
        return 0.0
    return float(statistics.stdev(numbers))


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) < 1e-4 and number != 0.0:
        return f"{number:.3e}"
    return f"{number:.4g}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DISC16b local-inverse recovery robustness grid.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_disc16b_robustness(args.config, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

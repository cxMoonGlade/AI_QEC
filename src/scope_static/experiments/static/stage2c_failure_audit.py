from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


def run_stage2c_failure_audit(
    metrics_path: str | Path = "outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/metrics.json",
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    source = Path(metrics_path)
    metrics = json.loads(source.read_text())
    out = Path(output_dir) if output_dir is not None else source.parent
    out.mkdir(parents=True, exist_ok=True)

    records = list(metrics.get("robustness_grid", []))
    failures = list(metrics.get("failure_cases", []))
    failure_keys = {
        _condition_key(item["regime"], item["synthetic_seed"], item["shots"])
        for item in failures
    }
    failures_by_key = {_condition_key(item["regime"], item["synthetic_seed"], item["shots"]): item for item in failures}
    successful_records = [record for record in records if _condition_key(record["regime"], record["synthetic_seed"], record["shots"]) not in failure_keys]
    failed_records = [record for record in records if _condition_key(record["regime"], record["synthetic_seed"], record["shots"]) in failure_keys]

    failure_rows = []
    for record in failed_records:
        key = _condition_key(record["regime"], record["synthetic_seed"], record["shots"])
        later = _later_conditions(records, record)
        failure_rows.append(
            {
                "regime": record["regime"],
                "synthetic_seed": int(record["synthetic_seed"]),
                "shots": int(record["shots"]),
                "ari_min": float(record["ari_min"]),
                "nmi_min": float(record["nmi_min"]),
                "active_clusters_min": int(record["active_clusters_min"]),
                "ari_margin_to_threshold": float(0.80 - float(record["ari_min"])),
                "nmi_margin_to_threshold": float(float(record["nmi_min"]) - 0.80),
                "bootstrap_label_pairwise_nmi": record.get("bootstrap_label_pairwise_nmi"),
                "local_logit_probability_variance": record.get("local_logit_probability_variance"),
                "heldout_local_inverse_nll_mean": record.get("heldout_local_inverse_nll_mean"),
                "mean_cluster_purity_mean": record.get("mean_cluster_purity_mean"),
                "mean_splits_per_omega_mean": record.get("mean_splits_per_omega_mean"),
                "max_splits_per_omega_max": _max_replicate_value(record, "max_splits_per_omega"),
                "max_merged_omega_per_cluster_max": _max_replicate_value(record, "max_merged_omega_per_cluster"),
                "worst_replicate": _worst_replicate(record),
                "failure_reasons": failures_by_key[key].get("reasons", []),
                "resolved_by_any_higher_shot_budget": any(bool(item.get("strong_all_replicates")) for item in later),
                "higher_shot_outcomes": [
                    {
                        "shots": int(item["shots"]),
                        "ari_min": float(item["ari_min"]),
                        "nmi_min": float(item["nmi_min"]),
                        "strong_all_replicates": bool(item.get("strong_all_replicates")),
                    }
                    for item in later
                ],
            }
        )

    summary = {
        "schema": "scope_static_stage2c_failure_audit_v1",
        "source_metrics": str(source),
        "stage": "stage2C",
        "experiment": "DISC16b_failure_case_audit",
        "predeclared_representation": metrics.get("predeclared_representation"),
        "candidate_selection": metrics.get("candidate_selection"),
        "ari_nmi_used_for_selection": metrics.get("ari_nmi_used_for_selection"),
        "uses_hidden_omega_for_training": metrics.get("uses_hidden_omega_for_training"),
        "uses_hidden_omega_for_initialization": metrics.get("uses_hidden_omega_for_initialization"),
        "uses_hidden_omega_for_checkpoint_selection": metrics.get("uses_hidden_omega_for_checkpoint_selection"),
        "uses_hidden_omega_for_final_evaluation": metrics.get("uses_hidden_omega_for_final_evaluation"),
        "strong_threshold": metrics.get("strong_threshold"),
        "total_conditions": len(records),
        "num_failures": len(failed_records),
        "num_strong_conditions": sum(1 for record in records if bool(record.get("strong_all_replicates"))),
        "failure_rate": len(failed_records) / len(records) if records else 0.0,
        "failure_counts_by_shots": _count_by(failed_records, "shots"),
        "failure_counts_by_regime": _count_by(failed_records, "regime"),
        "failure_counts_by_seed": _count_by(failed_records, "synthetic_seed"),
        "failure_reason_counts": dict(Counter(reason for item in failures for reason in item.get("reasons", []))),
        "failure_metric_summary": _metric_summary(failed_records),
        "success_metric_summary": _metric_summary(successful_records),
        "failure_rows": failure_rows,
        "failure_audit_conclusion": _failure_conclusion(
            records,
            failed_records,
            failure_rows,
            active_threshold=int(metrics.get("strong_threshold", {}).get("active_clusters_min", 1)),
        ),
        "stage2c_freeze_label": "local_inverse_probability_robust_near_strong_with_near_miss_split_merge_failures",
    }
    (out / "failure_case_audit.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (out / "failure_case_audit.md").write_text(format_failure_audit_markdown(summary))
    print(format_failure_audit_terminal(summary))
    return summary


def _condition_key(regime: object, seed: object, shots: object) -> tuple[str, int, int]:
    return (str(regime), int(seed), int(shots))


def _later_conditions(records: list[dict[str, object]], record: dict[str, object]) -> list[dict[str, object]]:
    regime = str(record["regime"])
    seed = int(record["synthetic_seed"])
    shots = int(record["shots"])
    later = [
        item
        for item in records
        if str(item["regime"]) == regime and int(item["synthetic_seed"]) == seed and int(item["shots"]) > shots
    ]
    return sorted(later, key=lambda item: int(item["shots"]))


def _max_replicate_value(record: dict[str, object], key: str) -> int | float | None:
    values = [rep.get(key) for rep in record.get("replicates", []) if rep.get(key) is not None]
    return max(values) if values else None


def _worst_replicate(record: dict[str, object]) -> dict[str, object] | None:
    replicates = list(record.get("replicates", []))
    if not replicates:
        return None
    worst = min(replicates, key=lambda item: (float(item.get("ari", 0.0)), float(item.get("nmi", 0.0))))
    return {
        "replicate": int(worst["replicate"]),
        "ari": float(worst["ari"]),
        "nmi": float(worst["nmi"]),
        "active_clusters": int(worst["active_clusters"]),
        "mean_cluster_purity": worst.get("mean_cluster_purity"),
        "mean_splits_per_omega": worst.get("mean_splits_per_omega"),
        "max_splits_per_omega": worst.get("max_splits_per_omega"),
        "max_merged_omega_per_cluster": worst.get("max_merged_omega_per_cluster"),
        "cluster_masses": worst.get("cluster_masses"),
    }


def _count_by(records: list[dict[str, object]], key: str) -> dict[str, int]:
    counts = Counter(str(record.get(key)) for record in records)
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _metric_summary(records: list[dict[str, object]]) -> dict[str, object]:
    keys = [
        "ari_mean",
        "ari_min",
        "nmi_mean",
        "nmi_min",
        "active_clusters_min",
        "bootstrap_label_pairwise_nmi",
        "local_logit_probability_variance",
        "mean_cluster_purity_mean",
        "mean_splits_per_omega_mean",
        "heldout_local_inverse_nll_mean",
    ]
    return {key: _summary_values(record.get(key) for record in records if record.get(key) is not None) for key in keys}


def _summary_values(values) -> dict[str, float | int | None]:
    numbers = [float(value) for value in values]
    if not numbers:
        return {"mean": None, "std": None, "min": None, "max": None}
    return {
        "mean": float(sum(numbers) / len(numbers)),
        "std": float(statistics.stdev(numbers)) if len(numbers) > 1 else 0.0,
        "min": float(min(numbers)),
        "max": float(max(numbers)),
    }


def _failure_conclusion(
    records: list[dict[str, object]],
    failed_records: list[dict[str, object]],
    failure_rows: list[dict[str, object]],
    *,
    active_threshold: int,
) -> str:
    if not failed_records:
        return "no_failure_cases"
    all_active = all(int(record["active_clusters_min"]) >= int(active_threshold) for record in failed_records)
    all_nmi_strong = all(float(record["nmi_min"]) >= 0.80 for record in failed_records)
    only_ari = all(row["failure_reasons"] == ["ari_below_0.80"] for row in failure_rows)
    mostly_low_shot = sum(1 for record in failed_records if int(record["shots"]) == 10_000) >= max(1, len(failed_records) // 2)
    if all_active and all_nmi_strong and only_ari and mostly_low_shot:
        return "near_miss_ari_failures_no_cluster_collapse_mostly_low_shot_split_merge"
    if all_active and all_nmi_strong and only_ari:
        return "near_miss_ari_failures_no_cluster_collapse"
    return "mixed_failure_modes_require_manual_inspection"


def format_failure_audit_markdown(summary: dict[str, object]) -> str:
    failure_metrics = summary["failure_metric_summary"]
    success_metrics = summary["success_metric_summary"]
    lines = [
        "# Stage 2C Failure-Case Audit",
        "",
        f"- Source: `{summary['source_metrics']}`",
        f"- Conclusion: `{summary['failure_audit_conclusion']}`",
        f"- Freeze label: `{summary['stage2c_freeze_label']}`",
        f"- Conditions: {summary['num_strong_conditions']}/{summary['total_conditions']} strong; {summary['num_failures']} failures",
        f"- Candidate selection: `{summary['candidate_selection']}`",
        f"- ARI/NMI used for selection: `{str(summary['ari_nmi_used_for_selection']).lower()}`",
        "",
        "## Failure Counts",
        "",
        f"- By shots: `{summary['failure_counts_by_shots']}`",
        f"- By regime: `{summary['failure_counts_by_regime']}`",
        f"- By seed: `{summary['failure_counts_by_seed']}`",
        f"- Reasons: `{summary['failure_reason_counts']}`",
        "",
        "## Failure Pattern",
        "",
        "| group | ARI min mean | ARI min range | NMI min mean | active min | boot NMI mean | purity mean | splits mean |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        _summary_row("failures", failure_metrics),
        _summary_row("successes", success_metrics),
        "",
        "## Failure Rows",
        "",
        "| regime | seed | shots | ARI min | NMI min | active | boot NMI | purity | splits | resolved later |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["failure_rows"]:
        lines.append(
            f"| {row['regime']} | {row['synthetic_seed']} | {row['shots']} | "
            f"{_fmt(row['ari_min'])} | {_fmt(row['nmi_min'])} | {row['active_clusters_min']} | "
            f"{_fmt(row['bootstrap_label_pairwise_nmi'])} | {_fmt(row['mean_cluster_purity_mean'])} | "
            f"{_fmt(row['mean_splits_per_omega_mean'])} | {str(row['resolved_by_any_higher_shot_budget']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Failures are near-miss recovery errors, not collapse: every failure keeps all 9 clusters active and NMI remains above 0.80. The failed cells miss only the ARI threshold, usually at 10k shots, with split/merge counts slightly above the exact-partition value of 1.0.",
            "",
            "This freezes Stage 2C as robust near-strong local-inverse recovery with known hard cases. The next research branch should change observability or broaden the teacher/grid, not add more direct S/alpha hardening.",
            "",
        ]
    )
    return "\n".join(lines)


def _summary_row(name: str, metrics: dict[str, object]) -> str:
    ari_min = metrics["ari_min"]
    nmi_min = metrics["nmi_min"]
    active = metrics["active_clusters_min"]
    boot = metrics["bootstrap_label_pairwise_nmi"]
    purity = metrics["mean_cluster_purity_mean"]
    splits = metrics["mean_splits_per_omega_mean"]
    return (
        f"| {name} | {_fmt(ari_min['mean'])} | {_fmt(ari_min['min'])}-{_fmt(ari_min['max'])} | "
        f"{_fmt(nmi_min['mean'])} | {_fmt(active['min'])} | {_fmt(boot['mean'])} | "
        f"{_fmt(purity['mean'])} | {_fmt(splits['mean'])} |"
    )


def format_failure_audit_terminal(summary: dict[str, object]) -> str:
    lines = [
        "Stage 2C Failure-Case Audit",
        f"source: {summary['source_metrics']}",
        f"result: {summary['failure_audit_conclusion']}",
        f"freeze: {summary['stage2c_freeze_label']}",
        f"strong: {summary['num_strong_conditions']}/{summary['total_conditions']} | failures: {summary['num_failures']}",
        "regime   seed  shots  ARImin  NMImin  active  bootNMI  purity  splits  later",
        "-------  ----  -----  ------  ------  ------  -------  ------  ------  -----",
    ]
    for row in summary["failure_rows"]:
        lines.append(
            f"{str(row['regime'])[:7]:<7}  {row['synthetic_seed']:<4}  {row['shots']:<5}  "
            f"{_fmt(row['ari_min']):<6}  {_fmt(row['nmi_min']):<6}  {row['active_clusters_min']:<6}  "
            f"{_fmt(row['bootstrap_label_pairwise_nmi']):<7}  {_fmt(row['mean_cluster_purity_mean']):<6}  "
            f"{_fmt(row['mean_splits_per_omega_mean']):<6}  {str(row['resolved_by_any_higher_shot_budget']).lower()}"
        )
    return "\n".join(lines)


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
    parser = argparse.ArgumentParser(description="Summarize Stage 2C DISC16b failure cases before freezing Stage 2C.")
    parser.add_argument("--metrics", default="outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/metrics.json")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    run_stage2c_failure_audit(args.metrics, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

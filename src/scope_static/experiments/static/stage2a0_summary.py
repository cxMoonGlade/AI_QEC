from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


def build_stage2a0_summary(metrics: dict[str, object]) -> dict[str, object]:
    records = [dict(record) for record in metrics.get("records", []) if isinstance(record, dict)]
    threshold_epsilon = _threshold_epsilon(metrics)
    discovery_records = [record for record in records if str(record.get("model", "")).startswith("disc_")]
    grouped = _summarize_discovery_groups(discovery_records, threshold_epsilon=threshold_epsilon)
    main = _select_main_matched_record(grouped)
    if main is None:
        result = "missing_matched_k_disc_hard"
        outcome_hint = "E_candidate_observation_model_contract_or_run_missing"
    else:
        result = _classify_stage2a0(main, threshold_epsilon=threshold_epsilon)
        outcome_hint = _publishable_outcome_hint(result)

    return {
        "stage": "stage2A.0",
        "summary_schema": "scope_static_stage2a0_summary_v1",
        "source_metrics": str(metrics.get("output_dir", "outputs/scope_static/STAGE2A_full")) + "/metrics.json",
        "stage2a_question": (
            "Can free learned DEM-fault assignments S[j,k] recover hidden omega(j) "
            "from DEM parity-map observations alone?"
        ),
        "success_requires": {
            "partition_recovery": "high ARI/NMI against hidden omega(j)",
            "predictive_quality": "heldout NLL close to matched known-orbit oracle",
            "nll_only_success_sufficient": False,
            "ari_nmi_only_success_sufficient": False,
        },
        "thresholds": {
            "high_ari": 0.80,
            "high_nmi": 0.80,
            "delta_nll_known_orbit_epsilon": threshold_epsilon,
        },
        "stage2a0_result": result,
        "publishable_outcome_hint": outcome_hint,
        "main_matched_k_disc_hard": main,
        "discovery_group_summaries": grouped,
        "claim_boundary": (
            "This summarizes synthetic Stage 2A.0 free-assignment recovery only; "
            "it is not a physical mechanism discovery claim."
        ),
    }


def write_stage2a0_summary(
    metrics_path: str | Path = "outputs/scope_static/STAGE2A_full/metrics.json",
    *,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    metrics_file = Path(metrics_path)
    metrics = json.loads(metrics_file.read_text())
    summary = build_stage2a0_summary(metrics)
    output = Path(output_dir) if output_dir is not None else metrics_file.parent
    output.mkdir(parents=True, exist_ok=True)
    summary["source_metrics"] = str(metrics_file)
    (output / "stage2a0_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output / "stage2a0_summary.md").write_text(format_stage2a0_summary_markdown(summary))
    return summary


def format_stage2a0_summary_markdown(summary: dict[str, object]) -> str:
    main = summary.get("main_matched_k_disc_hard")
    lines = [
        "# Stage 2A.0 Summary",
        "",
        f"- Result: `{summary.get('stage2a0_result')}`",
        f"- Outcome hint: `{summary.get('publishable_outcome_hint')}`",
        f"- Source metrics: `{summary.get('source_metrics')}`",
        "",
        "Success requires both high partition recovery and heldout NLL close to the matched known-orbit oracle.",
    ]
    if isinstance(main, dict):
        lines.extend(
            [
                "",
                "## Main Matched-K `disc_hard`",
                "",
                "| scenario | teacher | shots | K | mean ARI | mean NMI | mean dNLL known | collapses | result |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
                (
                    f"| {main.get('scenario')} | {main.get('teacher_mode')} | {main.get('shots')} | "
                    f"{main.get('prototype_count_K')} | {_fmt(main.get('mean_ari'))} | "
                    f"{_fmt(main.get('mean_nmi'))} | {_fmt(main.get('mean_delta_nll_known_orbit'))} | "
                    f"{main.get('num_selected_collapsed')} | {main.get('stage2a0_result')} |"
                ),
            ]
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            str(summary.get("claim_boundary")),
            "",
        ]
    )
    return "\n".join(lines)


def print_compact_summary(summary: dict[str, object]) -> None:
    print("Stage 2A.0 Summary")
    print(f"metrics: {summary.get('source_metrics')}")
    print(f"result: {summary.get('stage2a0_result')}")
    main = summary.get("main_matched_k_disc_hard")
    if isinstance(main, dict):
        print(
            "matched K disc_hard: "
            f"ARI={_fmt(main.get('mean_ari'))} "
            f"NMI={_fmt(main.get('mean_nmi'))} "
            f"dNLL_known={_fmt(main.get('mean_delta_nll_known_orbit'))} "
            f"collapses={main.get('num_selected_collapsed')}"
        )


def _summarize_discovery_groups(
    records: list[dict[str, object]],
    *,
    threshold_epsilon: float,
) -> list[dict[str, object]]:
    keys = [
        "scenario",
        "teacher_mode",
        "epsilon_break",
        "model",
        "residual_rank",
        "shots",
        "prototype_count_K",
    ]
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for record in records:
        key = tuple(record.get(name) for name in keys)
        grouped.setdefault(key, []).append(record)
    summaries: list[dict[str, object]] = []
    for key, group in grouped.items():
        values = dict(zip(keys, key))
        summary = dict(values)
        summary.update(
            {
                "num_records": len(group),
                "num_seeds": len({record.get("seed") for record in group}),
                "mean_ari": _mean_key(group, "ari"),
                "mean_nmi": _mean_key(group, "nmi"),
                "mean_delta_nll_known_orbit": _mean_key(group, "delta_nll_known_orbit"),
                "mean_assignment_entropy_normalized": _mean_key(group, "assignment_entropy_normalized"),
                "mean_num_active_prototypes": _mean_key(group, "num_active_prototypes"),
                "std_ari": _std_key(group, "ari"),
                "std_nmi": _std_key(group, "nmi"),
                "num_selected_collapsed": sum(1 for record in group if bool(record.get("assignment_collapse", False))),
            }
        )
        summary["passes_known_orbit_nll_threshold"] = (
            summary["mean_delta_nll_known_orbit"] is not None
            and float(summary["mean_delta_nll_known_orbit"]) <= float(threshold_epsilon)
        )
        summary["partition_recovery_high"] = (
            summary["mean_ari"] is not None
            and summary["mean_nmi"] is not None
            and float(summary["mean_ari"]) >= 0.80
            and float(summary["mean_nmi"]) >= 0.80
        )
        summary["stage2a0_result"] = _classify_stage2a0(summary, threshold_epsilon=threshold_epsilon)
        summaries.append(summary)
    return sorted(
        summaries,
        key=lambda item: (
            str(item.get("scenario")),
            str(item.get("model")),
            int(item.get("shots") or 0),
            int(item.get("prototype_count_K") or -1),
        ),
    )


def _select_main_matched_record(summaries: list[dict[str, object]]) -> dict[str, object] | None:
    candidates = [
        summary
        for summary in summaries
        if summary.get("model") == "disc_hard"
        and str(summary.get("scenario")) == "matched_k_exact"
        and summary.get("prototype_count_K") is not None
    ]
    if not candidates:
        candidates = [
            summary
            for summary in summaries
            if summary.get("model") == "disc_hard" and summary.get("prototype_count_K") is not None
        ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: int(item.get("shots") or 0))


def _classify_stage2a0(summary: dict[str, object], *, threshold_epsilon: float) -> str:
    recovery = bool(summary.get("partition_recovery_high", False))
    nll_close = bool(summary.get("passes_known_orbit_nll_threshold", False))
    collapsed = int(summary.get("num_selected_collapsed") or 0) > 0
    if collapsed:
        return "collapsed_or_inconclusive"
    if recovery and nll_close:
        return "success_partition_and_likelihood"
    if nll_close and not recovery:
        return "likelihood_match_without_partition_recovery"
    if recovery and not nll_close:
        return "partition_recovery_without_likelihood_match"
    delta = summary.get("mean_delta_nll_known_orbit")
    if delta is None:
        return "missing_known_orbit_comparison"
    if float(delta) <= 2.0 * float(threshold_epsilon):
        return "near_likelihood_match_but_recovery_failed"
    return "failed_partition_and_likelihood"


def _publishable_outcome_hint(result: str) -> str:
    if result == "success_partition_and_likelihood":
        return "A_2A0_free_assignment_recovers_synthetic_hidden_quotient"
    if result in {"likelihood_match_without_partition_recovery", "near_likelihood_match_but_recovery_failed"}:
        return "B_candidate_2A0_needs_recovery_biased_optimization"
    if result == "partition_recovery_without_likelihood_match":
        return "C_candidate_requires_identifiability_aware_likelihood_or_probes"
    return "E_candidate_current_observation_model_contract_insufficient_or_run_failed"


def _threshold_epsilon(metrics: dict[str, object]) -> float:
    important = metrics.get("discovery_important_results", {})
    if isinstance(important, dict) and important.get("threshold_epsilon") is not None:
        return float(important["threshold_epsilon"])
    for record in metrics.get("records", []):
        if isinstance(record, dict) and record.get("threshold_epsilon") is not None:
            return float(record["threshold_epsilon"])
    return 0.01


def _mean_key(records: Iterable[dict[str, object]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return float(mean(values)) if values else None


def _std_key(records: Iterable[dict[str, object]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return float(pstdev(values)) if len(values) > 1 else 0.0 if values else None


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize existing Stage 2A.0 discovery metrics.")
    parser.add_argument("--metrics", default="outputs/scope_static/STAGE2A_full/metrics.json")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    summary = write_stage2a0_summary(args.metrics, output_dir=args.output_dir)
    print_compact_summary(summary)
    output = Path(args.output_dir) if args.output_dir is not None else Path(args.metrics).parent
    print(f"summary: {output / 'stage2a0_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

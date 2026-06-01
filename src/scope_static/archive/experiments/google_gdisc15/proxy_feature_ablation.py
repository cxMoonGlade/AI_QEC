from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time
from typing import Iterable

import yaml

from . import gdisc15b_grid
from .gdisc15b_grid import PRIMARY_METRIC
from scope_static.archive.google_gdisc15.local_mechanism import PROXY_FEATURE_PROFILES


WINDOW_PROFILES = (
    "current_structured",
    "balanced_structured",
    "detector_local",
    "logical_tail",
    "mixed_claim",
)

DEFAULT_OUTPUT_DIR = Path("outputs/google_static/google_proxy_feature_ablation")
DEFAULT_CONFIG = Path("configs/archive/google_gdisc15/google_proxy_feature_ablation.yaml")
DEFAULT_CONTEXT_MANIFEST = Path("outputs/google_static/google_benchmark_suite_v1/B0/google_context_manifest.jsonl")
DEFAULT_DECODER_MANIFEST = Path("outputs/google_static/google_benchmark_suite_v1/B0/google_decoder_manifest.jsonl")


def main(argv: list[str] | None = None) -> dict[str, object]:
    start = time.perf_counter()
    args = _parse_args(argv)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    args.prepared_cache_dir = str(Path(args.prepared_cache_dir) if args.prepared_cache_dir else output / "prepared_cache")
    profiles = _csv(args.proxy_feature_profiles) or list(PROXY_FEATURE_PROFILES)
    window_profiles = _csv(args.window_profiles) or list(WINDOW_PROFILES)

    flat_records: list[dict[str, object]] = []
    run_refs: list[dict[str, object]] = []
    feature_audits: list[dict[str, object]] = []
    window_audits: list[dict[str, object]] = []
    for window_profile in window_profiles:
        profile_groups = [(profile, [profile]) for profile in profiles] if args.separate_profile_runs else [("all_proxy_profiles", profiles)]
        for profile_group, profile_names in profile_groups:
            feature_profile_csv = ",".join(profile_names)
            run_output = output / "runs" / f"{window_profile}__{profile_group}"
            grid_result = gdisc15b_grid.main(_grid_argv(args, run_output, window_profile, feature_profile_csv))
            tagged = [
                {
                    **record,
                    "window_profile": window_profile,
                    "proxy_feature_profile": _record_proxy_profile(record),
                    "ablation_profile_group": profile_group,
                    "ablation_run_output": str(run_output),
                }
                for record in grid_result.get("flat_records", [])
            ]
            flat_records.extend(tagged)
            completed = list(grid_result.get("grid", {}).get("completed_contexts", []))
            run_refs.append(
                {
                    "window_profile": window_profile,
                    "proxy_feature_profile": profile_group,
                    "proxy_feature_profiles": list(profile_names),
                    "output_dir": str(run_output),
                    "completed_contexts": len(completed),
                    "skipped_contexts": len(grid_result.get("grid", {}).get("skipped_contexts", [])),
                }
            )
            feature_audits.extend(_collect_feature_audits(completed, window_profile, profile_names))
            window_audits.extend(_collect_window_audits(completed, window_profile, profile_group))

    paired = _paired_structure_lift(flat_records)
    leaderboard = _leaderboard(paired)
    feature_audit = _feature_audit_summary(feature_audits, paired)
    window_audit = _window_audit_summary(window_audits)
    claim_summary = _claim_summary(leaderboard, feature_audit)

    _write_csv(output / "preprocessing_feature_ablation.csv", flat_records, _ablation_columns())
    _write_json(output / "preprocessing_feature_audit.json", feature_audit)
    _write_json(output / "window_profile_audit.json", window_audit)
    _write_csv(output / "paired_structure_lift.csv", paired, _paired_columns())
    (output / "proxy_feature_leaderboard.md").write_text(_leaderboard_markdown(leaderboard), encoding="utf-8")
    (output / "claim_summary.md").write_text(claim_summary, encoding="utf-8")

    result = {
        "run": {
            "name": "Google_proxy_feature_ablation",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "output_dir": str(output),
            "claim_boundary": (
                "Diagnostic Google benchmark only: reports visible proxy-feature and window-profile "
                "lift against local_full and dmle_qec. It does not claim true physical mechanism recovery."
            ),
            "primary_metric": PRIMARY_METRIC,
            "wall_seconds": time.perf_counter() - start,
            "run_refs": run_refs,
        },
        "leaderboard": leaderboard,
        "feature_audit": feature_audit,
        "window_audit": window_audit,
        "paired_structure_lift": paired,
    }
    _write_json(output / "metrics.json", result)
    print(f"Google proxy-feature ablation artifacts: {output}")
    return result


def _grid_argv(args: argparse.Namespace, output: Path, window_profile: str, feature_profiles: str) -> list[str]:
    argv = [
        "--dataset-root",
        args.dataset_root,
        "--dataset-name",
        args.dataset_name,
        "--dataset-family",
        args.dataset_family,
        "--samples",
        args.samples,
        "--patches",
        args.patches,
        "--bases",
        args.bases,
        "--rounds-labels",
        args.rounds_labels,
        "--heldout-split-types",
        "shot-heldout",
        "--max-contexts",
        str(args.max_contexts),
        "--context-workers",
        str(args.context_workers),
        "--torch-num-threads",
        str(args.torch_num_threads),
        "--dem-source",
        args.dem_source,
        "--reference-dem-sources",
        args.reference_dem_sources,
        "--orbit-mode",
        "fault_graph_heuristic",
        "--candidate-family",
        "proxy_profiles",
        "--proxy-feature-profiles",
        feature_profiles,
        "--train-shots",
        str(args.train_shots),
        "--heldout-shots",
        str(args.heldout_shots),
        "--steps",
        str(args.steps),
        "--subsample-count",
        str(args.subsample_count),
        "--subsample-shots",
        str(args.subsample_shots),
        "--subsample-steps",
        str(args.subsample_steps),
        "--max-windows",
        str(args.max_windows),
        "--max-window-bits",
        str(args.max_window_bits),
        "--detector-pair-window-budget",
        str(args.detector_pair_window_budget),
        "--logical-detector-pair-window-budget",
        str(args.logical_detector_pair_window_budget),
        "--window-plan-mode",
        "logical_aware",
        "--eval-window-plan-mode",
        window_profile,
        "--eval-max-window-bits",
        str(args.eval_max_window_bits),
        "--eval-max-windows",
        str(args.eval_max_windows),
        "--eval-radius",
        str(args.eval_radius),
        "--eval-template-window-budget",
        str(args.eval_template_window_budget),
        "--eval-orbit-window-budget",
        str(args.eval_orbit_window_budget),
        "--random-control-ranks",
        "",
        "--pca-ranks",
        "",
        "--nmf-steps",
        str(args.nmf_steps),
        "--kmeans-max-iter",
        str(args.kmeans_max_iter),
        "--dtype",
        args.dtype,
        "--likelihood-backend",
        args.likelihood_backend,
        "--cuda-kernel-variant",
        args.cuda_kernel_variant,
        "--spectral-memory-cap-mib",
        str(args.spectral_memory_cap_mib),
        "--prepared-cache-dir",
        args.prepared_cache_dir,
        "--native-gpu",
        "--output-dir",
        str(output),
    ]
    if args.context_manifest:
        argv.extend(["--context-manifest", args.context_manifest])
    if args.decoder_manifest:
        argv.extend(["--decoder-manifest", args.decoder_manifest])
    if args.disable_prepared_cache:
        argv.append("--disable-prepared-cache")
    if not args.include_reference_priors:
        argv.append("--skip-reference-priors")
    if not args.include_local_correlation_metrics:
        argv.append("--skip-local-correlation-metrics")
    return argv


def _record_proxy_profile(record: dict[str, object]) -> str:
    profile = str(record.get("proxy_feature_profile") or "")
    if profile:
        return profile
    model = str(record.get("model") or "")
    prefix = "GDISC15_proxy_"
    return model[len(prefix) :] if model.startswith(prefix) else ""


def _collect_feature_audits(
    completed_contexts: Iterable[dict[str, object]],
    window_profile: str,
    feature_profiles: Iterable[str],
) -> list[dict[str, object]]:
    rows = []
    requested_profiles = list(feature_profiles)
    for context in completed_contexts:
        metrics = _load_context_metrics(context)
        audit = metrics.get("preprocessing_feature_audit", {}) if isinstance(metrics, dict) else {}
        profiles = audit.get("profiles", {}) if isinstance(audit, dict) else {}
        if not isinstance(profiles, dict):
            profiles = {}
        names = requested_profiles or sorted(str(name) for name in profiles)
        for feature_profile in names:
            profile_audit = dict(profiles.get(feature_profile, {}))
            rows.append(
                {
                    "context_id": context.get("context_id"),
                    "window_profile": window_profile,
                    "proxy_feature_profile": feature_profile,
                    "metrics_path": _metrics_path(context),
                    "loaded": bool(profile_audit),
                    **profile_audit,
                }
            )
    return rows


def _collect_window_audits(
    completed_contexts: Iterable[dict[str, object]],
    window_profile: str,
    feature_profile: str,
) -> list[dict[str, object]]:
    rows = []
    for context in completed_contexts:
        metrics = _load_context_metrics(context)
        window = {}
        if isinstance(metrics, dict):
            window = metrics.get("window_audit", {}).get("eval_window_audit", {})
        rows.append(
            {
                "context_id": context.get("context_id"),
                "window_profile": window_profile,
                "proxy_feature_profile": feature_profile,
                "metrics_path": _metrics_path(context),
                "loaded": bool(window),
                "eval_window_audit": window,
            }
        )
    return rows


def _paired_structure_lift(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        key = (
            record.get("window_profile"),
            record.get("context_id"),
            record.get("dataset_name"),
            record.get("sample_id"),
            record.get("patch_id"),
            record.get("basis"),
            record.get("rounds_label"),
        )
        grouped[key].append(record)

    profile_rows = []
    by_window_context_profile: dict[tuple[object, object, object], dict[str, object]] = {}
    for key, rows in grouped.items():
        window_profile, context_id, dataset_name, sample_id, patch_id, basis, rounds_label = key
        local = _first_model(rows, "local_full")
        dmle = _first_model(rows, "dmle_qec")
        for row in rows:
            profile = row.get("proxy_feature_profile")
            if not str(row.get("model", "")).startswith("GDISC15_proxy_"):
                continue
            metric = _float(row.get(PRIMARY_METRIC))
            item = {
                "window_profile": window_profile,
                "proxy_feature_profile": profile,
                "context_id": context_id,
                "dataset_name": dataset_name,
                "sample_id": sample_id,
                "patch_id": patch_id,
                "basis": basis,
                "rounds_label": rounds_label,
                "model": row.get("model"),
                "primary_metric": PRIMARY_METRIC,
                "primary_metric_value": metric,
                "local_full_metric": _float(local.get(PRIMARY_METRIC)) if local else None,
                "dmle_qec_metric": _float(dmle.get(PRIMARY_METRIC)) if dmle else None,
                "delta_vs_local_full": _delta(metric, _float(local.get(PRIMARY_METRIC)) if local else None),
                "delta_vs_dmle_qec": _delta(metric, _float(dmle.get(PRIMARY_METRIC)) if dmle else None),
                "wins_vs_local_full": _wins(metric, _float(local.get(PRIMARY_METRIC)) if local else None),
                "wins_vs_dmle_qec": _wins(metric, _float(dmle.get(PRIMARY_METRIC)) if dmle else None),
                "feature_count": row.get("proxy_feature_count"),
                "feature_rank": row.get("proxy_feature_rank"),
                "constant_feature_count": row.get("proxy_constant_feature_count"),
                "missing_feature_count": row.get("proxy_missing_feature_count"),
            }
            by_window_context_profile[(window_profile, context_id, profile)] = item
            profile_rows.append(item)

    for row in profile_rows:
        baseline = by_window_context_profile.get((row["window_profile"], row["context_id"], "fg_only"))
        baseline_metric = _float(baseline.get("primary_metric_value")) if baseline else None
        row["fg_only_metric"] = baseline_metric
        row["delta_vs_fg_only"] = _delta(_float(row["primary_metric_value"]), baseline_metric)
        row["wins_vs_fg_only"] = _wins(_float(row["primary_metric_value"]), baseline_metric)
    return profile_rows


def _leaderboard(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["window_profile"]), str(row["proxy_feature_profile"]))].append(row)
    result = []
    for (window_profile, feature_profile), items in sorted(groups.items()):
        result.append(
            {
                "window_profile": window_profile,
                "proxy_feature_profile": feature_profile,
                "n": len(items),
                "primary_metric_mean": _mean(row.get("primary_metric_value") for row in items),
                "delta_vs_fg_only_mean": _mean(row.get("delta_vs_fg_only") for row in items),
                "delta_vs_local_full_mean": _mean(row.get("delta_vs_local_full") for row in items),
                "delta_vs_dmle_qec_mean": _mean(row.get("delta_vs_dmle_qec") for row in items),
                "wins_vs_fg_only": _sum_true(row.get("wins_vs_fg_only") for row in items),
                "wins_vs_local_full": _sum_true(row.get("wins_vs_local_full") for row in items),
                "wins_vs_dmle_qec": _sum_true(row.get("wins_vs_dmle_qec") for row in items),
                "feature_rank_mean": _mean(row.get("feature_rank") for row in items),
                "missing_feature_count_mean": _mean(row.get("missing_feature_count") for row in items),
            }
        )
    return result


def _feature_audit_summary(feature_audits: list[dict[str, object]], paired: list[dict[str, object]]) -> dict[str, object]:
    by_profile: dict[str, list[dict[str, object]]] = defaultdict(list)
    for audit in feature_audits:
        by_profile[str(audit.get("proxy_feature_profile"))].append(audit)
    summaries = []
    for profile, audits in sorted(by_profile.items()):
        summaries.append(
            {
                "proxy_feature_profile": profile,
                "contexts": len(audits),
                "feature_count_mean": _mean(audit.get("feature_count") for audit in audits),
                "nonzero_feature_count_mean": _mean(audit.get("nonzero_feature_count") for audit in audits),
                "constant_feature_count_mean": _mean(audit.get("constant_feature_count") for audit in audits),
                "feature_rank_mean": _mean(audit.get("feature_rank") for audit in audits),
                "missing_feature_count_mean": _mean(audit.get("missing_feature_count") for audit in audits),
                "forbidden_label_audit_passed": all(
                    bool(audit.get("forbidden_label_audit", {}).get("passed", False)) for audit in audits
                )
                if audits
                else False,
            }
        )
    return {
        "profiles": summaries,
        "contexts": feature_audits,
        "forbidden_label_audit_passed": all(
            bool(audit.get("forbidden_label_audit", {}).get("passed", False)) for audit in feature_audits
        )
        if feature_audits
        else False,
        "heldout_metric_correlation": _heldout_metric_correlations(paired),
    }


def _window_audit_summary(window_audits: list[dict[str, object]]) -> dict[str, object]:
    by_profile: dict[str, list[dict[str, object]]] = defaultdict(list)
    for audit in window_audits:
        by_profile[str(audit.get("window_profile"))].append(audit)
    summaries = []
    for profile, audits in sorted(by_profile.items()):
        evals = [audit.get("eval_window_audit", {}) for audit in audits if isinstance(audit.get("eval_window_audit"), dict)]
        summaries.append(
            {
                "window_profile": profile,
                "contexts": len(audits),
                "num_windows_mean": _mean(item.get("num_windows") for item in evals),
                "mean_window_bits_mean": _mean(item.get("mean_window_bits") for item in evals),
                "max_window_bits_mean": _mean(item.get("max_window_bits") for item in evals),
                "bit_coverage_mean": _mean(
                    item.get("detector_logical_bit_coverage", {}).get("fraction_bits_covered") for item in evals
                ),
                "logical_window_count_mean": _mean(item.get("num_windows_containing_logical") for item in evals),
                "family_counts_total": _sum_family_counts(evals),
            }
        )
    return {"profiles": summaries, "contexts": window_audits}


def _heldout_metric_correlations(rows: list[dict[str, object]]) -> dict[str, object]:
    fields = ["feature_count", "feature_rank", "constant_feature_count", "missing_feature_count"]
    result = {}
    for field in fields:
        x = [_float(row.get(field)) for row in rows]
        y = [_float(row.get("primary_metric_value")) for row in rows]
        pairs = [(a, b) for a, b in zip(x, y, strict=True) if a is not None and b is not None]
        result[field] = {
            "n": len(pairs),
            "pearson": _pearson([a for a, _ in pairs], [b for _, b in pairs]) if len(pairs) >= 2 else None,
            "evaluator_only": True,
            "used_for_selection": False,
        }
    return result


def _claim_summary(leaderboard: list[dict[str, object]], feature_audit: dict[str, object]) -> str:
    richer = [row for row in leaderboard if row["proxy_feature_profile"] != "fg_only"]
    improves_fg = [row for row in richer if _float(row.get("delta_vs_fg_only_mean")) is not None and float(row["delta_vs_fg_only_mean"]) < 0.0]
    beats_local = [row for row in richer if _float(row.get("delta_vs_local_full_mean")) is not None and float(row["delta_vs_local_full_mean"]) < 0.0]
    balanced = [
        row
        for row in richer
        if row["window_profile"] in {"balanced_structured", "detector_local"}
        and _float(row.get("delta_vs_fg_only_mean")) is not None
        and float(row["delta_vs_fg_only_mean"]) < 0.0
    ]
    lines = [
        "# Google Proxy-Feature Ablation Claim Summary",
        "",
        f"- Primary metric: `{PRIMARY_METRIC}`",
        f"- Forbidden-label audit passed: `{str(feature_audit.get('forbidden_label_audit_passed')).lower()}`",
        f"- Richer profiles improving over `fg_only`: `{len(improves_fg)}`",
        f"- Richer profiles beating `local_full`: `{len(beats_local)}`",
        f"- Richer profiles improving under balanced/detector windows: `{len(balanced)}`",
        "",
        "This is a diagnostic benchmark, not a final Google claim. A preprocessing bottleneck is supported only if the paired lift repeats across contexts and the forbidden-label audit passes.",
        "",
    ]
    if improves_fg and beats_local and balanced and feature_audit.get("forbidden_label_audit_passed"):
        lines.append("Status: preprocessing bottleneck is supported on this diagnostic slice.")
    else:
        lines.append("Status: preprocessing bottleneck is not confirmed by the available artifact set.")
    lines.append("")
    return "\n".join(lines)


def _leaderboard_markdown(rows: list[dict[str, object]]) -> str:
    ordered = sorted(rows, key=lambda row: (_none_high(row.get("primary_metric_mean")), str(row["window_profile"])))
    lines = [
        "# Proxy Feature Leaderboard",
        "",
        f"- Primary metric: `{PRIMARY_METRIC}`",
        "",
        "| window | feature profile | n | metric | delta fg_only | delta local | delta dmle | wins local | wins dmle | rank |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in ordered:
        lines.append(
            f"| {row['window_profile']} | {row['proxy_feature_profile']} | {row['n']} | "
            f"{_fmt(row.get('primary_metric_mean'))} | {_fmt(row.get('delta_vs_fg_only_mean'))} | "
            f"{_fmt(row.get('delta_vs_local_full_mean'))} | {_fmt(row.get('delta_vs_dmle_qec_mean'))} | "
            f"{row.get('wins_vs_local_full')} | {row.get('wins_vs_dmle_qec')} | {_fmt(row.get('feature_rank_mean'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def _load_context_metrics(context: dict[str, object]) -> dict[str, object]:
    path = Path(_metrics_path(context))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"load_error": str(exc)}


def _metrics_path(context: dict[str, object]) -> str:
    return str(Path(str(context.get("output_root"))) / "GDISC15_real_local_mechanism_discovery" / "metrics.json")


def _write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csvable(row.get(key)) for key in columns})


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ablation_columns() -> list[str]:
    return [
        "window_profile",
        "proxy_feature_profile",
        "context_id",
        "dataset_name",
        "sample_id",
        "patch_id",
        "basis",
        "rounds_label",
        "model",
        PRIMARY_METRIC,
        "heldout_local_window_excess_nll",
        "detector_rate_mae",
        "local_correlation_error",
        "logical_flip_rate_calibration",
        "parameter_count",
        "proxy_feature_device",
        "proxy_feature_count",
        "proxy_feature_rank",
        "proxy_constant_feature_count",
        "proxy_missing_feature_count",
    ]


def _paired_columns() -> list[str]:
    return [
        "window_profile",
        "proxy_feature_profile",
        "context_id",
        "dataset_name",
        "sample_id",
        "patch_id",
        "basis",
        "rounds_label",
        "model",
        "primary_metric",
        "primary_metric_value",
        "fg_only_metric",
        "local_full_metric",
        "dmle_qec_metric",
        "delta_vs_fg_only",
        "delta_vs_local_full",
        "delta_vs_dmle_qec",
        "wins_vs_fg_only",
        "wins_vs_local_full",
        "wins_vs_dmle_qec",
        "feature_count",
        "feature_rank",
        "constant_feature_count",
        "missing_feature_count",
    ]


def _first_model(rows: list[dict[str, object]], model: str) -> dict[str, object] | None:
    return next((row for row in rows if row.get("model") == model), None)


def _delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return float(value) - float(baseline)


def _wins(value: float | None, baseline: float | None) -> bool | None:
    if value is None or baseline is None:
        return None
    return float(value) < float(baseline)


def _mean(values: Iterable[object]) -> float | None:
    numbers = [_float(value) for value in values]
    clean = [value for value in numbers if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def _sum_true(values: Iterable[object]) -> int:
    return int(sum(1 for value in values if value is True))


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    if statistics.pstdev(left) == 0.0 or statistics.pstdev(right) == 0.0:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    cov = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True)) / len(left)
    return float(cov / (statistics.pstdev(left) * statistics.pstdev(right)))


def _sum_family_counts(items: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        families = item.get("window_family_counts", {})
        if not isinstance(families, dict):
            continue
        for key, value in families.items():
            counts[str(key)] = counts.get(str(key), 0) + int(value)
    return dict(sorted(counts.items()))


def _float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: object) -> str:
    number = _float(value)
    if number is None:
        return "-"
    return f"{number:.6g}"


def _none_high(value: object) -> float:
    number = _float(value)
    return number if number is not None else float("inf")


def _csv(value: str) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _csvable(value: object) -> object:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_jsonable(value), sort_keys=True)
    return value


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    defaults = _config_defaults(argv)
    default_config = str(DEFAULT_CONFIG) if DEFAULT_CONFIG.is_file() else ""

    def d(key: str, fallback):
        return defaults.get(key, fallback)

    parser = argparse.ArgumentParser(description="Run the Google proxy-feature preprocessing ablation.")
    parser.add_argument("--config", default=default_config)
    parser.add_argument("--dataset-root", default=d("dataset_root", "/home/cx/Document/google_72Q_surface_code_d3_d5_set1"))
    parser.add_argument("--context-manifest", default=d("context_manifest", str(DEFAULT_CONTEXT_MANIFEST) if DEFAULT_CONTEXT_MANIFEST.is_file() else ""))
    parser.add_argument("--decoder-manifest", default=d("decoder_manifest", str(DEFAULT_DECODER_MANIFEST) if DEFAULT_DECODER_MANIFEST.is_file() else ""))
    parser.add_argument("--dataset-name", default=d("dataset_name", "google_72Q_surface_code_d3_d5_set1"))
    parser.add_argument("--dataset-family", default=d("dataset_family", "surface"))
    parser.add_argument("--samples", default=d("samples", "sample_01,sample_02"))
    parser.add_argument("--patches", default=d("patches", "d3_at_q5_5,d3_at_q7_5,d3_at_q3_5,d5_at_q5_5,d3_at_q5_3,d3_at_q5_7"))
    parser.add_argument("--bases", default=d("bases", "X,Z"))
    parser.add_argument("--rounds-labels", default=d("rounds_labels", "r13"))
    parser.add_argument("--max-contexts", type=int, default=d("max_contexts", 24))
    parser.add_argument("--context-workers", type=int, default=d("context_workers", 4))
    parser.add_argument("--torch-num-threads", type=int, default=d("torch_num_threads", 6))
    parser.add_argument("--dem-source", default=d("dem_source", "decoder_si1000"))
    parser.add_argument("--reference-dem-sources", default=d("reference_dem_sources", "decoder_si1000,decoder_rl"))
    parser.add_argument("--proxy-feature-profiles", default=d("proxy_feature_profiles", ",".join(PROXY_FEATURE_PROFILES)))
    parser.add_argument("--window-profiles", default=d("window_profiles", ",".join(WINDOW_PROFILES)))
    parser.add_argument("--separate-profile-runs", action="store_true")
    parser.add_argument("--include-reference-priors", action="store_true")
    parser.add_argument("--include-local-correlation-metrics", action="store_true")
    parser.add_argument("--train-shots", type=int, default=d("train_shots", 4096))
    parser.add_argument("--heldout-shots", type=int, default=d("heldout_shots", 4096))
    parser.add_argument("--steps", type=int, default=d("steps", 40))
    parser.add_argument("--subsample-count", type=int, default=d("subsample_count", 2))
    parser.add_argument("--subsample-shots", type=int, default=d("subsample_shots", 2048))
    parser.add_argument("--subsample-steps", type=int, default=d("subsample_steps", 30))
    parser.add_argument("--max-windows", type=int, default=d("max_windows", 96))
    parser.add_argument("--max-window-bits", type=int, default=d("max_window_bits", 8))
    parser.add_argument("--detector-pair-window-budget", type=int, default=d("detector_pair_window_budget", 48))
    parser.add_argument("--logical-detector-pair-window-budget", type=int, default=d("logical_detector_pair_window_budget", 48))
    parser.add_argument("--eval-max-window-bits", type=int, default=d("eval_max_window_bits", 6))
    parser.add_argument("--eval-max-windows", type=int, default=d("eval_max_windows", 256))
    parser.add_argument("--eval-radius", type=float, default=d("eval_radius", 1.0))
    parser.add_argument("--eval-template-window-budget", type=int, default=d("eval_template_window_budget", 32))
    parser.add_argument("--eval-orbit-window-budget", type=int, default=d("eval_orbit_window_budget", 64))
    parser.add_argument("--random-control-ranks", default=d("random_control_ranks", ""))
    parser.add_argument("--nmf-steps", type=int, default=d("nmf_steps", 1))
    parser.add_argument("--kmeans-max-iter", type=int, default=d("kmeans_max_iter", 32))
    parser.add_argument("--dtype", choices=["float64", "float32"], default=d("dtype", "float64"))
    parser.add_argument("--likelihood-backend", choices=["auto", "pytorch", "cuda_extension"], default=d("likelihood_backend", "auto"))
    parser.add_argument("--cuda-kernel-variant", choices=["dp", "spectral_shadow", "spectral", "auto"], default=d("cuda_kernel_variant", "dp"))
    parser.add_argument("--spectral-memory-cap-mib", type=int, default=d("spectral_memory_cap_mib", 1024))
    parser.add_argument("--prepared-cache-dir", default=d("prepared_cache_dir", ""))
    parser.add_argument("--disable-prepared-cache", action="store_true")
    parser.add_argument("--output-dir", default=d("output_dir", str(DEFAULT_OUTPUT_DIR)))
    return parser.parse_args(argv)


def _config_defaults(argv: list[str] | None) -> dict[str, object]:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", default=str(DEFAULT_CONFIG) if DEFAULT_CONFIG.is_file() else "")
    known, _unknown = pre.parse_known_args(argv)
    if not known.config:
        return {}
    path = Path(known.config)
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    section = data.get("google_proxy_feature_ablation", data)
    return section if isinstance(section, dict) else {}


if __name__ == "__main__":
    main()

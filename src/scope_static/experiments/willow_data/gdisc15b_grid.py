from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import statistics
import time

import numpy as np
import torch

from scope_static.google.inventory import (
    DATASET_SURFACE_SET1,
    extract_dem_proxy_labels,
    google_context_id,
    load_context_manifest,
    load_decoder_manifest,
    normalize_decoder_pathway,
    select_context_rows,
)
from scope_static.google.set1 import find_google_set1_leaf, normalize_google_set1_root

from . import local_mechanism as run_google_local_mechanism
from .static import _fmt_float, _print_table


PRIMARY_METRIC = "heldout_local_window_excess_nll"
SUMMARY_METRICS = [
    "heldout_local_window_nll",
    "heldout_local_window_excess_nll",
    "detector_rate_mae",
    "local_correlation_error",
    "logical_flip_rate_calibration",
]


def main(argv: list[str] | None = None) -> dict[str, object]:
    start = time.perf_counter()
    args = _parse_args(argv)
    output = Path(args.output_dir)
    runs_dir = output / "runs"
    output.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    contexts = _context_specs(args)
    completed = []
    skipped = []
    flat_records = []
    for index, context in enumerate(contexts):
        if args.max_contexts is not None and len(completed) >= int(args.max_contexts):
            break
        if context.get("skip_reason"):
            skipped.append(context)
            continue
        split_type = context["heldout_split_type"]
        if split_type != "shot-heldout":
            skipped.append({**context, "skip_reason": "cross_context_transfer_split_not_implemented_in_gdisc15b_grid"})
            continue
        run_output = runs_dir / _context_id(context)
        try:
            result = run_google_local_mechanism.main(_local_mechanism_args(args, context, run_output))
        except Exception as exc:
            skipped.append({**context, "skip_reason": str(exc)})
            continue
        completed.append({**context, "output_root": str(run_output)})
        dem_proxy_labels = _context_dem_proxy_labels(args, context)
        flat_records.extend(_flatten_records(result, context, run_output, dem_proxy_labels=dem_proxy_labels))
        print(
            "[gdisc15b] "
            f"{len(completed)}/{len(contexts)} {context['sample_id']} {context['patch_id']} "
            f"{context['basis']} {context['rounds_label']} {split_type}"
        )

    summary = _model_summary(flat_records)
    result = {
        "run": {
            "name": "GDISC15b_google_grid_validation",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_root": str(normalize_google_set1_root(args.dataset_root)),
            "output_dir": str(output),
            "wall_seconds": time.perf_counter() - start,
            "claim_boundary": (
                "Google GDISC15b reports predictive utility, stability, paired improvements, "
                "and explicitly labelled proxy alignments only. It does not report true omega recovery."
            ),
        },
        "grid": {
            "context_manifest": args.context_manifest or None,
            "decoder_manifest": args.decoder_manifest or None,
            "dataset_name_filter": args.dataset_name,
            "dataset_family_filter": args.dataset_family or None,
            "distance_filter": args.distances or None,
            "rounds_filter": args.rounds or None,
            "decoder_pathway_filter": args.decoder_pathway or None,
            "samples": _csv(args.samples),
            "patches": _csv(args.patches),
            "bases": _csv(args.bases),
            "rounds_labels": _csv(args.rounds_labels),
            "heldout_split_types": _csv(args.heldout_split_types),
            "completed_contexts": completed,
            "skipped_contexts": skipped,
        },
        "required_baselines": {
            "local_full": True,
            "dmle_qec": True,
            "dmle_qec_upstream": bool(args.include_upstream_dmle),
            "global_shared_scalar": True,
            "si1000_prior_reference": True,
            "rl_optimized_prior_reference_where_available": True,
            "gdisc15_pca_scores_ranks": _csv(args.pca_ranks),
            "random_low_rank_control": _csv(args.random_control_ranks),
        },
        "uncertainty": {
            "kind": "paired_context_statistics",
            "mean_std": True,
            "paired_improvement_over_local_full": True,
            "wins_counted_against": "local_full",
            "primary_win_metric": PRIMARY_METRIC,
        },
        "flat_records": flat_records,
        "model_summary": summary,
    }
    _write_outputs(output, result)
    _print_summary(result)
    return result


def _context_specs(args: argparse.Namespace) -> list[dict[str, object]]:
    if args.context_manifest:
        return _context_specs_from_manifest(args)
    contexts = []
    root = args.dataset_root
    for split_type in _csv(args.heldout_split_types):
        for sample in _csv(args.samples):
            for patch in _csv(args.patches):
                for basis in _csv(args.bases):
                    for rounds in _csv(args.rounds_labels):
                        try:
                            find_google_set1_leaf(
                                root,
                                sample_id=sample,
                                patch_id=patch,
                                basis=basis,
                                rounds_label=rounds,
                            )
                        except Exception:
                            continue
                        contexts.append(
                            {
                                "context_id": google_context_id(
                                    dataset_name=DATASET_SURFACE_SET1,
                                    sample_id=sample,
                                    patch_id=patch,
                                    basis=basis,
                                    rounds_label=rounds,
                                ),
                                "dataset_name": DATASET_SURFACE_SET1,
                                "dataset_family": "surface",
                                "sample_id": sample,
                                "sample_index": _sample_index(sample),
                                "patch_id": patch,
                                "basis": basis,
                                "distance": _distance_from_patch(patch),
                                "rounds": _rounds_from_label(rounds),
                                "rounds_label": rounds,
                                "dem_source": args.dem_source,
                                "decoder_pathway": normalize_decoder_pathway(DATASET_SURFACE_SET1, args.dem_source),
                                "heldout_split_type": split_type,
                            }
                        )
    return contexts


def _context_specs_from_manifest(args: argparse.Namespace) -> list[dict[str, object]]:
    rows = load_context_manifest(args.context_manifest)
    dataset_name = _single_filter(args.dataset_name)
    dataset_family = _single_filter(args.dataset_family)
    selected = select_context_rows(
        rows,
        dataset_name=dataset_name,
        dataset_family=dataset_family,
    )
    selected = [
        row
        for row in selected
        if _matches_filter(row.get("sample_id"), args.samples)
        and _matches_filter(row.get("patch_id"), args.patches)
        and _matches_filter(row.get("basis"), args.bases)
        and _matches_filter(row.get("rounds_label"), args.rounds_labels)
        and _matches_int_filter(row.get("distance"), args.distances)
        and _matches_int_filter(row.get("rounds"), args.rounds)
    ]

    decoder_manifest = _decoder_manifest_rows(args)
    decoder_pathway = _single_filter(args.decoder_pathway)
    contexts: list[dict[str, object]] = []
    for split_type in _csv(args.heldout_split_types):
        for row in selected:
            context = {
                "context_id": row.get("context_id"),
                "dataset_name": row.get("dataset_name"),
                "dataset_family": row.get("dataset_family"),
                "sample_id": row.get("sample_id"),
                "sample_index": row.get("sample_index"),
                "patch_id": row.get("patch_id"),
                "basis": row.get("basis"),
                "distance": row.get("distance"),
                "rounds": row.get("rounds"),
                "rounds_label": row.get("rounds_label"),
                "shots": row.get("shots"),
                "dem_source": args.dem_source,
                "heldout_split_type": split_type,
            }
            if row.get("dataset_name") != DATASET_SURFACE_SET1:
                contexts.append({**context, "skip_reason": "dataset_not_supported_by_set1_runner"})
                continue
            if row.get("sample_id") is None or row.get("patch_id") is None:
                contexts.append({**context, "skip_reason": "set1_runner_requires_sample_and_patch"})
                continue
            if decoder_pathway:
                pathway = normalize_decoder_pathway(str(row.get("dataset_name")), decoder_pathway)
                decoder_row = decoder_manifest.get((str(row.get("context_id")), pathway))
                context["dem_source"] = pathway
                context["decoder_pathway"] = pathway
                if decoder_row is None:
                    contexts.append({**context, "skip_reason": "decoder_pathway_not_in_manifest"})
                    continue
                if not decoder_row.get("available_dem") or not decoder_row.get("available_predictions"):
                    contexts.append(
                        {
                            **context,
                            "skip_reason": "missing_decoder_outputs",
                            "available_dem": bool(decoder_row.get("available_dem")),
                            "available_predictions": bool(decoder_row.get("available_predictions")),
                        }
                    )
                    continue
                context["dem_proxy_labels"] = decoder_row.get("dem_proxy_labels")
            else:
                context["decoder_pathway"] = normalize_decoder_pathway(DATASET_SURFACE_SET1, args.dem_source)
            contexts.append(context)
    return contexts


def _local_mechanism_args(args: argparse.Namespace, context: dict[str, object], output_root: Path) -> list[str]:
    dem_source = str(context.get("dem_source") or args.dem_source)
    result = [
        "--dataset-root",
        str(args.dataset_root),
        "--sample-id",
        str(context["sample_id"]),
        "--patch-id",
        str(context["patch_id"]),
        "--basis",
        str(context["basis"]),
        "--rounds-label",
        str(context["rounds_label"]),
        "--dem-source",
        dem_source,
        "--reference-dem-sources",
        args.reference_dem_sources,
        "--orbit-mode",
        args.orbit_mode,
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
        args.window_plan_mode,
        "--pca-ranks",
        args.pca_ranks,
        "--random-control-ranks",
        args.random_control_ranks,
        "--random-control-seeds",
        args.random_control_seeds,
        "--nmf-steps",
        str(args.nmf_steps),
        "--kmeans-max-iter",
        str(args.kmeans_max_iter),
        "--upstream-dmle-repo",
        args.upstream_dmle_repo,
        "--upstream-dmle-epochs",
        str(args.upstream_dmle_epochs),
        "--upstream-dmle-lr",
        str(args.upstream_dmle_lr),
        "--upstream-dmle-batch-size",
        str(args.upstream_dmle_batch_size),
        "--upstream-dmle-minibatch",
        str(args.upstream_dmle_minibatch),
        "--upstream-dmle-path-search-max-time",
        str(args.upstream_dmle_path_search_max_time),
        "--seed",
        str(args.seed),
        "--dtype",
        args.dtype,
        "--likelihood-backend",
        args.likelihood_backend,
        "--cuda-kernel-variant",
        args.cuda_kernel_variant,
        "--spectral-memory-cap-mib",
        str(args.spectral_memory_cap_mib),
        "--output-root",
        str(output_root),
    ]
    if args.native_gpu:
        result.append("--native-gpu")
    if args.include_upstream_dmle:
        result.append("--include-upstream-dmle")
    if args.upstream_dmle_path_file:
        result.extend(["--upstream-dmle-path-file", args.upstream_dmle_path_file])
    if args.disable_prepared_cache:
        result.append("--disable-prepared-cache")
    if args.kmeans_check_convergence:
        result.append("--kmeans-check-convergence")
    return result


def _flatten_records(
    result: dict[str, object],
    context: dict[str, object],
    output_root: Path,
    *,
    dem_proxy_labels: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    records = list(result["GDISC15_real_local_mechanism_discovery"]["records"])
    local = next((record for record in records if record.get("model") == "local_full"), None)
    flat = []
    for record in records:
        row = {
            **context,
            "output_root": str(output_root),
            "decoder_pathway": context.get("decoder_pathway"),
            "dem_proxy_labels": dem_proxy_labels,
            "model": record.get("model"),
            "parameter_count": record.get("parameter_count"),
            "compression_ratio": record.get("compression_ratio"),
            "baseline_family": record.get("baseline_family"),
            "baseline_display_name": record.get("baseline_display_name"),
            "baseline_variant": record.get("baseline_variant"),
            "baseline_implementation": record.get("baseline_implementation"),
            "baseline_kind": record.get("baseline_kind"),
            "upstream_dmle_qec_direct_adapter": record.get("upstream_dmle_qec_direct_adapter"),
            "upstream_dmle_qec_component": record.get("upstream_dmle_qec_component"),
            "upstream_dmle_qec_complete_implementation": record.get("upstream_dmle_qec_complete_implementation"),
            "upstream_dmle_qec_compatibility_scope": record.get("upstream_dmle_qec_compatibility_scope"),
            "combined_excess_parameter_pareto_status": record.get("combined_excess_parameter_pareto_status"),
        }
        for metric in SUMMARY_METRICS:
            row[metric] = record.get(metric)
            baseline_value = local.get(metric) if local is not None else None
            row[f"{metric}_delta_vs_local_full"] = _delta(record.get(metric), baseline_value)
        row["wins_primary_vs_local_full"] = _wins(record.get(PRIMARY_METRIC), local.get(PRIMARY_METRIC) if local else None)
        flat.append(row)
    return flat


def _model_summary(records: list[dict[str, object]]) -> list[dict[str, object]]:
    by_model: dict[str, list[dict[str, object]]] = {}
    for record in records:
        by_model.setdefault(str(record["model"]), []).append(record)
    summary = []
    for model, rows in sorted(by_model.items()):
        item: dict[str, object] = {
            "model": model,
            "n": len(rows),
            "params_mean": _mean([row.get("parameter_count") for row in rows]),
            "params_std": _std([row.get("parameter_count") for row in rows]),
            "wins_primary_vs_local_full": int(sum(1 for row in rows if row.get("wins_primary_vs_local_full") is True)),
            "total_paired": int(sum(1 for row in rows if row.get("wins_primary_vs_local_full") is not None)),
        }
        for metric in SUMMARY_METRICS:
            values = [row.get(metric) for row in rows]
            deltas = [row.get(f"{metric}_delta_vs_local_full") for row in rows]
            item[f"{metric}_mean"] = _mean(values)
            item[f"{metric}_std"] = _std(values)
            item[f"{metric}_paired_delta_mean"] = _mean(deltas)
            item[f"{metric}_paired_delta_std"] = _std(deltas)
        summary.append(item)
    return summary


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n")
    (output / "flat_records.json").write_text(json.dumps(_jsonable(result["flat_records"]), indent=2, sort_keys=True) + "\n")
    (output / "run_manifest.json").write_text(json.dumps(_jsonable(result["grid"]), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(_summary_markdown(result))


def _summary_markdown(result: dict[str, object]) -> str:
    rows = sorted(
        result["model_summary"],
        key=lambda row: (
            _none_high(row.get(f"{PRIMARY_METRIC}_mean")),
            int(row.get("params_mean") or 10**9),
        ),
    )
    lines = [
        "# GDISC15b Google Grid Validation",
        "",
        f"- Completed contexts: `{len(result['grid']['completed_contexts'])}`",
        f"- Skipped contexts: `{len(result['grid']['skipped_contexts'])}`",
        f"- Primary win metric: `{PRIMARY_METRIC}`",
        f"- True omega recovery claim: `false`",
        "",
        "| model | params | heldout NLL | detector MAE | local corr err | logical calib | wins/total |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        wins = f"{row['wins_primary_vs_local_full']}/{row['total_paired']}"
        lines.append(
            f"| {row['model']} | {_mean_std(row.get('params_mean'), row.get('params_std'))} | "
            f"{_mean_std(row.get('heldout_local_window_nll_mean'), row.get('heldout_local_window_nll_std'))} | "
            f"{_mean_std(row.get('detector_rate_mae_mean'), row.get('detector_rate_mae_std'))} | "
            f"{_mean_std(row.get('local_correlation_error_mean'), row.get('local_correlation_error_std'))} | "
            f"{_mean_std(row.get('logical_flip_rate_calibration_mean'), row.get('logical_flip_rate_calibration_std'))} | "
            f"{wins} |"
        )
    lines.append("")
    return "\n".join(lines)


def _print_summary(result: dict[str, object]) -> None:
    output = Path(str(result["run"]["output_dir"]))
    print("GDISC15b Google grid validation complete")
    print(f"metrics: {output / 'metrics.json'}")
    print(f"summary: {output / 'summary.md'}")
    print(f"contexts: completed={len(result['grid']['completed_contexts'])} skipped={len(result['grid']['skipped_contexts'])}")
    rows = sorted(
        result["model_summary"],
        key=lambda row: (_none_high(row.get(f"{PRIMARY_METRIC}_mean")), int(row.get("params_mean") or 10**9)),
    )[:10]
    _print_table(
        ["model", "params", "heldout NLL", "det MAE", "corr err", "log calib", "wins/total"],
        [
            [
                row["model"],
                _fmt_float(row.get("params_mean"), precision=1),
                _mean_std(row.get("heldout_local_window_nll_mean"), row.get("heldout_local_window_nll_std")),
                _mean_std(row.get("detector_rate_mae_mean"), row.get("detector_rate_mae_std")),
                _mean_std(row.get("local_correlation_error_mean"), row.get("local_correlation_error_std")),
                _mean_std(row.get("logical_flip_rate_calibration_mean"), row.get("logical_flip_rate_calibration_std")),
                f"{row['wins_primary_vs_local_full']}/{row['total_paired']}",
            ]
            for row in rows
        ],
    )


def _context_dem_proxy_labels(args: argparse.Namespace, context: dict[str, object]) -> dict[str, object] | None:
    existing = context.get("dem_proxy_labels")
    if isinstance(existing, dict):
        return existing
    if context.get("dataset_name") not in {None, DATASET_SURFACE_SET1}:
        return None
    try:
        leaf = find_google_set1_leaf(
            args.dataset_root,
            sample_id=str(context["sample_id"]),
            patch_id=str(context["patch_id"]),
            basis=str(context["basis"]),
            rounds_label=str(context["rounds_label"]),
        )
        pathway = str(context.get("decoder_pathway") or args.dem_source)
        return extract_dem_proxy_labels(
            leaf.decoder_dem_path(pathway),
            dataset_name=DATASET_SURFACE_SET1,
            context_id=str(context.get("context_id")),
            pathway_name=normalize_decoder_pathway(DATASET_SURFACE_SET1, pathway),
        )
    except Exception as exc:
        return {
            "proxy_label_only": True,
            "available": False,
            "error": str(exc),
        }


def _context_id(context: dict[str, object]) -> str:
    if context.get("context_id"):
        return "__".join([str(context["heldout_split_type"]), str(context["context_id"])])
    return "__".join(str(context[key]) for key in ["heldout_split_type", "sample_id", "patch_id", "basis", "rounds_label"])


def _csv(value: str) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _single_filter(value: str) -> str | None:
    values = _csv(value)
    if len(values) != 1:
        return None
    text = values[0]
    return None if text.lower() in {"all", "*", "any"} else text


def _matches_filter(value: object, csv_value: str) -> bool:
    values = _csv(csv_value)
    if not values or any(item.lower() in {"all", "*", "any"} for item in values):
        return True
    return str(value) in set(values)


def _matches_int_filter(value: object, csv_value: str) -> bool:
    values = _csv(csv_value)
    if not values or any(item.lower() in {"all", "*", "any"} for item in values):
        return True
    try:
        number = int(value)
    except (TypeError, ValueError):
        return False
    return number in {int(item) for item in values}


def _decoder_manifest_rows(args: argparse.Namespace) -> dict[tuple[str, str], dict[str, object]]:
    if not args.decoder_pathway:
        return {}
    path = Path(args.decoder_manifest) if args.decoder_manifest else Path(args.context_manifest).with_name("google_decoder_manifest.jsonl")
    if not path.is_file():
        return {}
    rows = {}
    for row in load_decoder_manifest(path):
        rows[(str(row.get("context_id")), str(row.get("pathway_name")))] = row
    return rows


def _sample_index(sample_id: str | None) -> int | None:
    if sample_id is None:
        return None
    match = re.search(r"(\d+)$", str(sample_id))
    return int(match.group(1)) if match else None


def _rounds_from_label(rounds_label: str | None) -> int | None:
    if rounds_label is None:
        return None
    match = re.search(r"(\d+)$", str(rounds_label))
    return int(match.group(1)) if match else None


def _distance_from_patch(patch_id: str | None) -> int | None:
    if patch_id is None:
        return None
    match = re.match(r"d(\d+)_", str(patch_id))
    return int(match.group(1)) if match else None


def _delta(value: object, baseline: object) -> float | None:
    if value is None or baseline is None:
        return None
    return float(value) - float(baseline)


def _wins(value: object, baseline: object) -> bool | None:
    if value is None or baseline is None:
        return None
    return float(value) < float(baseline)


def _mean(values: list[object]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    return float(sum(numbers) / len(numbers)) if numbers else None


def _std(values: list[object]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return None
    if len(numbers) == 1:
        return 0.0
    return float(statistics.stdev(numbers))


def _mean_std(mean: object, std: object) -> str:
    if mean is None:
        return "-"
    if std is None:
        return _fmt_float(mean)
    return f"{_fmt_float(mean)} +- {_fmt_float(std)}"


def _none_high(value: object) -> float:
    return float(value) if value is not None else float("inf")


def _jsonable(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GDISC15b Google grid validation.")
    parser.add_argument("--dataset-root", default="/home/cx/Document/google_72Q_surface_code_d3_d5_set1")
    parser.add_argument("--context-manifest", default="")
    parser.add_argument("--decoder-manifest", default="")
    parser.add_argument("--dataset-name", default=DATASET_SURFACE_SET1)
    parser.add_argument("--dataset-family", default="")
    parser.add_argument("--samples", default="sample_00")
    parser.add_argument("--patches", default="d3_at_q5_5")
    parser.add_argument("--bases", default="X")
    parser.add_argument("--distances", default="")
    parser.add_argument("--rounds", default="")
    parser.add_argument("--rounds-labels", default="r13")
    parser.add_argument("--decoder-pathway", default="")
    parser.add_argument("--heldout-split-types", default="shot-heldout")
    parser.add_argument("--max-contexts", type=int, default=None)
    parser.add_argument("--dem-source", default="decoder_si1000")
    parser.add_argument("--reference-dem-sources", default="decoder_si1000,decoder_rl")
    parser.add_argument("--orbit-mode", default="fault_graph_heuristic")
    parser.add_argument("--train-shots", type=int, default=4096)
    parser.add_argument("--heldout-shots", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--subsample-count", type=int, default=2)
    parser.add_argument("--subsample-shots", type=int, default=2048)
    parser.add_argument("--subsample-steps", type=int, default=30)
    parser.add_argument("--max-windows", type=int, default=96)
    parser.add_argument("--max-window-bits", type=int, default=8)
    parser.add_argument("--detector-pair-window-budget", type=int, default=48)
    parser.add_argument("--logical-detector-pair-window-budget", type=int, default=48)
    parser.add_argument("--window-plan-mode", choices=["logical_aware", "detector_local"], default="logical_aware")
    parser.add_argument("--pca-ranks", default="1,2,3,5,8")
    parser.add_argument("--random-control-ranks", default="1,2,3,5,8")
    parser.add_argument("--random-control-seeds", default="0")
    parser.add_argument("--nmf-steps", type=int, default=120)
    parser.add_argument("--kmeans-max-iter", type=int, default=32)
    parser.add_argument("--kmeans-check-convergence", action="store_true")
    parser.add_argument("--include-upstream-dmle", action="store_true")
    parser.add_argument("--upstream-dmle-repo", default="/tmp/DMLE-QEC")
    parser.add_argument("--upstream-dmle-epochs", type=int, default=20)
    parser.add_argument("--upstream-dmle-lr", type=float, default=0.01)
    parser.add_argument("--upstream-dmle-batch-size", type=int, default=10000)
    parser.add_argument("--upstream-dmle-minibatch", type=int, default=1000)
    parser.add_argument("--upstream-dmle-path-file", default="")
    parser.add_argument("--upstream-dmle-path-search-max-time", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dtype", choices=["float64", "float32"], default="float64")
    parser.add_argument("--likelihood-backend", choices=["auto", "pytorch", "cuda_extension"], default="auto")
    parser.add_argument("--cuda-kernel-variant", choices=["dp", "spectral_shadow", "spectral", "auto"], default="dp")
    parser.add_argument("--spectral-memory-cap-mib", type=int, default=1024)
    parser.add_argument("--native-gpu", action="store_true")
    parser.add_argument("--disable-prepared-cache", action="store_true")
    parser.add_argument("--output-dir", default="outputs/google_static/GDISC15b_google_grid_validation")
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()

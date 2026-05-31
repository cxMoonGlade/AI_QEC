from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time
from typing import Any, Iterable

import numpy as np
import torch
import yaml

from scope_static.google.set1 import DATASET_NAME, normalize_google_set1_root

from . import gdisc15b_grid
from .gdisc15b_grid import PRIMARY_METRIC, SUMMARY_METRICS
from .static import _fmt_float, _print_table


DEFAULT_CONFIG = Path("configs/scope_static/google_xz_scorecard.yaml")
DEFAULT_OUTPUT_DIR = Path("outputs/google_static/google_xz_scorecard")

CLAIM_BOUNDARY = (
    "Google X/Z scorecard reports current-model predictive utility, compression, calibration, "
    "decoder-facing and DEM-proxy diagnostics only. Google datasets do not provide true per-shot "
    "physical-mechanism labels, true hidden fault partitions, or catalog M-ID labels."
)

BASELINE_MODELS = {"dmle_qec", "dmle_qec_upstream", "global_shared_scalar"}

GRID_DEFAULTS: dict[str, Any] = {
    "dataset_root": "/home/cx/Document/google_72Q_surface_code_d3_d5_set1",
    "context_manifest": "",
    "decoder_manifest": "",
    "dataset_name": DATASET_NAME,
    "dataset_family": "",
    "samples": "sample_00,sample_01,sample_02,sample_03,sample_04",
    "patches": "d3_at_q5_5,d3_at_q7_5,d3_at_q3_5,d5_at_q5_5,d3_at_q5_3,d3_at_q5_7",
    "bases": "X,Z",
    "distances": "",
    "rounds": "",
    "rounds_labels": "r13",
    "decoder_pathway": "",
    "heldout_split_types": "shot-heldout",
    "max_contexts": 12,
    "dem_source": "decoder_si1000",
    "reference_dem_sources": "decoder_si1000,decoder_rl",
    "orbit_mode": "fault_graph_heuristic",
    "train_shots": 4096,
    "heldout_shots": 1024,
    "steps": 40,
    "subsample_count": 2,
    "subsample_shots": 2048,
    "subsample_steps": 30,
    "max_windows": 96,
    "max_window_bits": 8,
    "detector_pair_window_budget": 48,
    "logical_detector_pair_window_budget": 48,
    "window_plan_mode": "logical_aware",
    "pca_ranks": "1,2,3,5,8",
    "random_control_ranks": "1,2,3,5,8",
    "random_control_seeds": "0",
    "nmf_steps": 120,
    "kmeans_max_iter": 32,
    "kmeans_check_convergence": False,
    "include_upstream_dmle": False,
    "upstream_dmle_repo": "/tmp/DMLE-QEC",
    "upstream_dmle_epochs": 20,
    "upstream_dmle_lr": 0.01,
    "upstream_dmle_batch_size": 10000,
    "upstream_dmle_minibatch": 1000,
    "upstream_dmle_path_file": "",
    "upstream_dmle_path_search_max_time": 0,
    "seed": 0,
    "dtype": "float64",
    "likelihood_backend": "auto",
    "cuda_kernel_variant": "dp",
    "spectral_memory_cap_mib": 1024,
    "disable_prepared_cache": False,
}

SCORECARD_DEFAULTS: dict[str, Any] = {
    "min_contexts": 4,
    "max_skipped_contexts": 0,
    "require_both_bases": True,
}

GRID_FLAGS = {
    "dataset_root": "--dataset-root",
    "context_manifest": "--context-manifest",
    "decoder_manifest": "--decoder-manifest",
    "dataset_name": "--dataset-name",
    "dataset_family": "--dataset-family",
    "samples": "--samples",
    "patches": "--patches",
    "bases": "--bases",
    "distances": "--distances",
    "rounds": "--rounds",
    "rounds_labels": "--rounds-labels",
    "decoder_pathway": "--decoder-pathway",
    "heldout_split_types": "--heldout-split-types",
    "max_contexts": "--max-contexts",
    "dem_source": "--dem-source",
    "reference_dem_sources": "--reference-dem-sources",
    "orbit_mode": "--orbit-mode",
    "train_shots": "--train-shots",
    "heldout_shots": "--heldout-shots",
    "steps": "--steps",
    "subsample_count": "--subsample-count",
    "subsample_shots": "--subsample-shots",
    "subsample_steps": "--subsample-steps",
    "max_windows": "--max-windows",
    "max_window_bits": "--max-window-bits",
    "detector_pair_window_budget": "--detector-pair-window-budget",
    "logical_detector_pair_window_budget": "--logical-detector-pair-window-budget",
    "window_plan_mode": "--window-plan-mode",
    "pca_ranks": "--pca-ranks",
    "random_control_ranks": "--random-control-ranks",
    "random_control_seeds": "--random-control-seeds",
    "nmf_steps": "--nmf-steps",
    "kmeans_max_iter": "--kmeans-max-iter",
    "upstream_dmle_repo": "--upstream-dmle-repo",
    "upstream_dmle_epochs": "--upstream-dmle-epochs",
    "upstream_dmle_lr": "--upstream-dmle-lr",
    "upstream_dmle_batch_size": "--upstream-dmle-batch-size",
    "upstream_dmle_minibatch": "--upstream-dmle-minibatch",
    "upstream_dmle_path_file": "--upstream-dmle-path-file",
    "upstream_dmle_path_search_max_time": "--upstream-dmle-path-search-max-time",
    "seed": "--seed",
    "dtype": "--dtype",
    "likelihood_backend": "--likelihood-backend",
    "cuda_kernel_variant": "--cuda-kernel-variant",
    "spectral_memory_cap_mib": "--spectral-memory-cap-mib",
}


def run_google_xz_scorecard_from_config(
    *,
    config_path: str | Path | None = DEFAULT_CONFIG,
    output_dir: str | Path | None = None,
    grid_overrides: dict[str, Any] | None = None,
    scorecard_overrides: dict[str, Any] | None = None,
) -> dict[str, object]:
    start = time.perf_counter()
    cfg = _load_config(config_path)
    grid_cfg = {**GRID_DEFAULTS, **_mapping(cfg.get("grid"))}
    scorecard_cfg = {**SCORECARD_DEFAULTS, **_mapping(cfg.get("scorecard"))}
    grid_cfg.update({key: value for key, value in (grid_overrides or {}).items() if value is not None})
    scorecard_cfg.update({key: value for key, value in (scorecard_overrides or {}).items() if value is not None})

    output = Path(output_dir if output_dir is not None else cfg.get("output_dir", DEFAULT_OUTPUT_DIR))
    grid_output = Path(str(grid_cfg.pop("output_dir", output / "GDISC15b_grid")))
    output.mkdir(parents=True, exist_ok=True)
    grid_output.mkdir(parents=True, exist_ok=True)

    grid_argv = _grid_argv(grid_cfg, grid_output)
    grid_result = gdisc15b_grid.main(grid_argv)
    context_scorecard = _context_scorecard(grid_result["flat_records"])
    basis_summary = _basis_summary(context_scorecard)
    label_manifest = _label_manifest(grid_result, grid_cfg)
    checks = _scorecard_checks(grid_result, scorecard_cfg)
    result = {
        "run": {
            "name": "Google_XZ_scorecard",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "claim_boundary": CLAIM_BOUNDARY,
            "output_dir": str(output),
            "grid_output_dir": str(grid_output),
            "grid_metrics_path": str(grid_output / "metrics.json"),
            "wall_seconds": time.perf_counter() - start,
        },
        "config": {
            "config_path": None if config_path is None else str(config_path),
            "grid": _jsonable({**grid_cfg, "output_dir": str(grid_output)}),
            "scorecard": _jsonable(scorecard_cfg),
            "grid_argv": grid_argv,
        },
        "scorecard": {
            "google_xz_scorecard_passed": all(bool(item["passed"]) for item in checks.values()),
            "primary_metric": PRIMARY_METRIC,
            "claim_boundary": CLAIM_BOUNDARY,
            "checks": checks,
            "basis_summary": basis_summary,
            "context_scorecard": context_scorecard,
            "model_summary": grid_result["model_summary"],
            "label_manifest": label_manifest,
        },
        "grid": {
            "completed_contexts": grid_result["grid"]["completed_contexts"],
            "skipped_contexts": grid_result["grid"]["skipped_contexts"],
        },
    }
    _write_outputs(output, result)
    _print_summary(result)
    return result


def _context_scorecard(flat_records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for record in flat_records:
        key = (
            record.get("dataset_name"),
            record.get("dataset_family"),
            record.get("context_id"),
            record.get("decoder_pathway"),
            record.get("heldout_split_type"),
            record.get("sample_id"),
            record.get("patch_id"),
            record.get("basis"),
            record.get("rounds_label"),
        )
        grouped.setdefault(key, []).append(record)

    rows = []
    for key, records in sorted(grouped.items()):
        local = next((record for record in records if record.get("model") == "local_full"), None)
        compressed = [
            record
            for record in records
            if str(record.get("model", "")).startswith("GDISC15_")
            and "random_low_rank" not in str(record.get("model", ""))
        ]
        random_controls = [record for record in records if "random_low_rank" in str(record.get("model", ""))]
        baselines = [
            record
            for record in records
            if str(record.get("model")) in BASELINE_MODELS or str(record.get("model", "")).endswith("_prior_reference")
        ]
        best_compressed = _best_record(compressed)
        best_baseline = _best_record(baselines)
        best_random = _best_record(random_controls)
        basis = str(key[7])
        context = {
            "dataset_name": key[0],
            "dataset_family": key[1],
            "context_id": key[2],
            "decoder_pathway": key[3],
            "heldout_split_type": key[4],
            "sample_id": key[5],
            "patch_id": key[6],
            "basis": basis,
            "rounds_label": key[8],
            "distance": record_distance(records, key[6]),
            "dem_proxy_labels": _first_non_null(record.get("dem_proxy_labels") for record in records),
            "local_full": _compact_record(local),
            "best_compressed": _compact_record(best_compressed),
            "best_baseline": _compact_record(best_baseline),
            "baseline_suite": [_compact_record(record) for record in sorted(baselines, key=lambda item: str(item.get("model")))],
            "best_random_control": _compact_record(best_random),
            "compressed_minus_local_excess_nll": _metric_delta(best_compressed, local, PRIMARY_METRIC),
            "compressed_minus_best_baseline_excess_nll": _metric_delta(best_compressed, best_baseline, PRIMARY_METRIC),
            "random_minus_compressed_excess_nll": _metric_delta(best_random, best_compressed, PRIMARY_METRIC),
            "compression_ratio_vs_local_full": _compression_ratio(local, best_compressed),
            "true_hidden_omega_available": False,
            "physical_mechanism_recovery_claim_allowed": False,
        }
        rows.append(context)
    return rows


def _basis_summary(context_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in context_rows:
        grouped.setdefault(str(row["basis"]), []).append(row)
    result = []
    for basis, rows in sorted(grouped.items()):
        model_counts = Counter(str(row["best_compressed"]["model"]) for row in rows if row.get("best_compressed"))
        baseline_counts = Counter(str(row["best_baseline"]["model"]) for row in rows if row.get("best_baseline"))
        result.append(
            {
                "basis": basis,
                "num_contexts": len(rows),
                "best_compressed_model_counts": dict(sorted(model_counts.items())),
                "best_baseline_model_counts": dict(sorted(baseline_counts.items())),
                "compressed_minus_local_excess_nll_mean": _mean(
                    [row.get("compressed_minus_local_excess_nll") for row in rows]
                ),
                "compressed_minus_best_baseline_excess_nll_mean": _mean(
                    [row.get("compressed_minus_best_baseline_excess_nll") for row in rows]
                ),
                "compressed_minus_local_excess_nll_std": _std(
                    [row.get("compressed_minus_local_excess_nll") for row in rows]
                ),
                "random_minus_compressed_excess_nll_mean": _mean(
                    [row.get("random_minus_compressed_excess_nll") for row in rows]
                ),
                "compression_ratio_vs_local_full_mean": _mean(
                    [row.get("compression_ratio_vs_local_full") for row in rows]
                ),
                "best_compressed_excess_nll_mean": _mean(
                    [_metric_from_compact(row.get("best_compressed"), PRIMARY_METRIC) for row in rows]
                ),
                "local_full_excess_nll_mean": _mean(
                    [_metric_from_compact(row.get("local_full"), PRIMARY_METRIC) for row in rows]
                ),
                "best_compressed_detector_mae_mean": _mean(
                    [_metric_from_compact(row.get("best_compressed"), "detector_rate_mae") for row in rows]
                ),
                "best_compressed_logical_calibration_mean": _mean(
                    [_metric_from_compact(row.get("best_compressed"), "logical_flip_rate_calibration") for row in rows]
                ),
            }
        )
    return result


def _label_manifest(grid_result: dict[str, object], grid_cfg: dict[str, Any]) -> dict[str, object]:
    contexts = []
    for context in grid_result["grid"]["completed_contexts"]:
        contexts.append(
            {
                "context_id": context.get("context_id"),
                "dataset": context.get("dataset_name", DATASET_NAME),
                "dataset_name": context.get("dataset_name", DATASET_NAME),
                "dataset_family": context.get("dataset_family", "surface"),
                "dataset_root": str(normalize_google_set1_root(str(grid_cfg["dataset_root"]))),
                "sample_id": context.get("sample_id"),
                "sample_index": context.get("sample_index"),
                "patch_id": context.get("patch_id"),
                "basis": context.get("basis"),
                "rounds_label": context.get("rounds_label"),
                "rounds": context.get("rounds"),
                "distance": context.get("distance", _distance_from_patch(context.get("patch_id"))),
                "decoder_pathway": context.get("decoder_pathway"),
                "heldout_split_type": context.get("heldout_split_type"),
                "output_root": context.get("output_root"),
                "context_labels": [
                    "dataset_name",
                    "dataset_family",
                    "sample_id",
                    "patch_id",
                    "basis",
                    "rounds_label",
                    "distance",
                    "qubit_coordinates",
                ],
                "strong_labels_available": ["obs_flips_actual", "decoder_failure"],
                "decoder_labels_available": ["decoder_family", "prior_family"],
                "dem_proxy_labels_available": [
                    "support_size",
                    "touches_logical",
                    "detector_degree",
                    "boundary_or_bulk_proxy",
                    "fault_graph_community",
                ],
            }
        )
    return {
        "schema": "google_label_manifest_preview_v1",
        "purpose": "Context-level labels for X/Z scorecard; full shot/decoder/DEM manifests are future inventory work.",
        "claim_boundary": CLAIM_BOUNDARY,
        "label_layers": {
            "strong_labels": ["obs_flips_actual", "obs_flips_actual_xor_obs_flips_predicted"],
            "context_labels": ["dataset", "sample", "patch", "basis", "rounds", "distance", "shots", "coordinates"],
            "decoder_labels": ["decoder_family", "prior_family"],
            "dem_proxy_labels": ["support_size", "touches_logical", "degree", "region", "fault_graph_community"],
            "forbidden_true_labels": [
                "true_per_shot_physical_error_mechanism",
                "true_hidden_fault_partition",
                "true_catalog_M_id",
            ],
        },
        "contexts": contexts,
    }


def _scorecard_checks(grid_result: dict[str, object], scorecard_cfg: dict[str, Any]) -> dict[str, dict[str, object]]:
    completed = list(grid_result["grid"]["completed_contexts"])
    skipped = list(grid_result["grid"]["skipped_contexts"])
    bases = sorted({str(context.get("basis")) for context in completed})
    execution = _execution_audit(completed)
    return {
        "contexts_completed": {
            "passed": len(completed) >= int(scorecard_cfg["min_contexts"]),
            "value": len(completed),
            "threshold": int(scorecard_cfg["min_contexts"]),
        },
        "contexts_skipped": {
            "passed": len(skipped) <= int(scorecard_cfg["max_skipped_contexts"]),
            "value": len(skipped),
            "threshold": int(scorecard_cfg["max_skipped_contexts"]),
        },
        "both_bases_present": {
            "passed": (not bool(scorecard_cfg["require_both_bases"])) or {"X", "Z"}.issubset(set(bases)),
            "value": bases,
            "required": bool(scorecard_cfg["require_both_bases"]),
        },
        "gpu_execution": {
            "passed": bool(execution["all_cuda_extension"]),
            "value": execution["all_cuda_extension"],
            "required": True,
            "contexts": execution["contexts"],
        },
        "true_hidden_omega_claim": {
            "passed": True,
            "value": False,
            "required": False,
        },
    }


def _execution_audit(completed_contexts: list[dict[str, object]]) -> dict[str, object]:
    contexts = []
    for context in completed_contexts:
        metrics_path = Path(str(context["output_root"])) / "GDISC15_real_local_mechanism_discovery" / "metrics.json"
        item: dict[str, object] = {"context_id": _context_id(context), "metrics_path": str(metrics_path), "loaded": False}
        try:
            metrics = json.loads(metrics_path.read_text())
            run = metrics.get("run", {})
            item.update(
                {
                    "loaded": True,
                    "device": run.get("device"),
                    "likelihood_backend": run.get("likelihood_backend"),
                    "cuda_kernel_variant": run.get("cuda_kernel_variant"),
                    "cuda_extension": run.get("device") == "cuda" and run.get("likelihood_backend") == "cuda_extension",
                }
            )
        except Exception as exc:
            item.update({"error": str(exc), "cuda_extension": False})
        contexts.append(item)
    return {"all_cuda_extension": all(bool(item.get("cuda_extension")) for item in contexts), "contexts": contexts}


def _grid_argv(grid_cfg: dict[str, Any], output_dir: Path) -> list[str]:
    argv: list[str] = []
    for key, flag in GRID_FLAGS.items():
        value = grid_cfg.get(key)
        if value is None:
            continue
        if key == "upstream_dmle_path_file" and not str(value).strip():
            continue
        argv.extend([flag, str(value)])
    argv.append("--native-gpu")
    if bool(grid_cfg.get("disable_prepared_cache")):
        argv.append("--disable-prepared-cache")
    if bool(grid_cfg.get("kmeans_check_convergence")):
        argv.append("--kmeans-check-convergence")
    if bool(grid_cfg.get("include_upstream_dmle")):
        argv.append("--include-upstream-dmle")
    argv.extend(["--output-dir", str(output_dir)])
    return argv


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    scorecard = result["scorecard"]
    (output / "metrics.json").write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n")
    (output / "scorecard.json").write_text(json.dumps(_jsonable(scorecard), indent=2, sort_keys=True) + "\n")
    (output / "context_scorecard.json").write_text(
        json.dumps(_jsonable(scorecard["context_scorecard"]), indent=2, sort_keys=True) + "\n"
    )
    (output / "label_manifest.json").write_text(
        json.dumps(_jsonable(scorecard["label_manifest"]), indent=2, sort_keys=True) + "\n"
    )
    (output / "run_manifest.json").write_text(json.dumps(_jsonable(result["config"]), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(_summary_markdown(result))


def _summary_markdown(result: dict[str, object]) -> str:
    scorecard = result["scorecard"]
    lines = [
        "# Google X/Z Scorecard",
        "",
        f"- Passed: `{str(scorecard['google_xz_scorecard_passed']).lower()}`",
        f"- Completed contexts: `{len(result['grid']['completed_contexts'])}`",
        f"- Skipped contexts: `{len(result['grid']['skipped_contexts'])}`",
        f"- Primary metric: `{scorecard['primary_metric']}`",
        f"- True hidden omega recovery claim: `false`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Basis Summary",
        "",
        "| basis | contexts | best compressed | best baseline | compressed-local ex NLL | compressed-baseline ex NLL | random-compressed ex NLL | compression | det MAE | log calib |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in scorecard["basis_summary"]:
        lines.append(
            f"| {row['basis']} | {row['num_contexts']} | {_model_counts(row['best_compressed_model_counts'])} | "
            f"{_model_counts(row['best_baseline_model_counts'])} | "
            f"{_fmt_float(row.get('compressed_minus_local_excess_nll_mean'))} | "
            f"{_fmt_float(row.get('compressed_minus_best_baseline_excess_nll_mean'))} | "
            f"{_fmt_float(row.get('random_minus_compressed_excess_nll_mean'))} | "
            f"{_fmt_float(row.get('compression_ratio_vs_local_full_mean'), precision=2)} | "
            f"{_fmt_float(row.get('best_compressed_detector_mae_mean'))} | "
            f"{_fmt_float(row.get('best_compressed_logical_calibration_mean'))} |"
        )
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| check | passed | value | threshold |",
            "| --- | ---: | --- | ---: |",
        ]
    )
    for name, item in scorecard["checks"].items():
        lines.append(
            f"| {name} | `{str(item.get('passed')).lower()}` | "
            f"`{item.get('value')}` | `{item.get('threshold', item.get('required', '-'))}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _print_summary(result: dict[str, object]) -> None:
    scorecard = result["scorecard"]
    output = Path(str(result["run"]["output_dir"]))
    print("Google X/Z scorecard complete")
    print(f"metrics: {output / 'metrics.json'}")
    print(f"summary: {output / 'summary.md'}")
    print(f"passed: {scorecard['google_xz_scorecard_passed']}")
    _print_table(
        ["basis", "contexts", "compressed-local", "compressed-baseline", "random-compressed", "compression"],
        [
            [
                row["basis"],
                str(row["num_contexts"]),
                _fmt_float(row.get("compressed_minus_local_excess_nll_mean")),
                _fmt_float(row.get("compressed_minus_best_baseline_excess_nll_mean")),
                _fmt_float(row.get("random_minus_compressed_excess_nll_mean")),
                _fmt_float(row.get("compression_ratio_vs_local_full_mean"), precision=2),
            ]
            for row in scorecard["basis_summary"]
        ],
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Google X/Z current-model scorecard.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dataset-root")
    parser.add_argument("--context-manifest")
    parser.add_argument("--decoder-manifest")
    parser.add_argument("--dataset-name")
    parser.add_argument("--dataset-family")
    parser.add_argument("--samples")
    parser.add_argument("--patches")
    parser.add_argument("--bases")
    parser.add_argument("--distances")
    parser.add_argument("--rounds")
    parser.add_argument("--rounds-labels")
    parser.add_argument("--decoder-pathway")
    parser.add_argument("--heldout-split-types")
    parser.add_argument("--max-contexts", type=int)
    parser.add_argument("--dem-source")
    parser.add_argument("--reference-dem-sources")
    parser.add_argument("--orbit-mode")
    parser.add_argument("--train-shots", type=int)
    parser.add_argument("--heldout-shots", type=int)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--subsample-count", type=int)
    parser.add_argument("--subsample-shots", type=int)
    parser.add_argument("--subsample-steps", type=int)
    parser.add_argument("--max-windows", type=int)
    parser.add_argument("--max-window-bits", type=int)
    parser.add_argument("--detector-pair-window-budget", type=int)
    parser.add_argument("--logical-detector-pair-window-budget", type=int)
    parser.add_argument("--window-plan-mode")
    parser.add_argument("--pca-ranks")
    parser.add_argument("--random-control-ranks")
    parser.add_argument("--random-control-seeds")
    parser.add_argument("--nmf-steps", type=int)
    parser.add_argument("--kmeans-max-iter", type=int)
    parser.add_argument("--kmeans-check-convergence", action="store_true", default=None)
    parser.add_argument("--include-upstream-dmle", action="store_true", default=None)
    parser.add_argument("--upstream-dmle-repo")
    parser.add_argument("--upstream-dmle-epochs", type=int)
    parser.add_argument("--upstream-dmle-lr", type=float)
    parser.add_argument("--upstream-dmle-batch-size", type=int)
    parser.add_argument("--upstream-dmle-minibatch", type=int)
    parser.add_argument("--upstream-dmle-path-file")
    parser.add_argument("--upstream-dmle-path-search-max-time", type=int)
    parser.add_argument("--dtype", choices=["float64", "float32"])
    parser.add_argument("--likelihood-backend", choices=["auto", "pytorch", "cuda_extension"])
    parser.add_argument("--cuda-kernel-variant", choices=["dp", "spectral_shadow", "spectral", "auto"])
    parser.add_argument("--spectral-memory-cap-mib", type=int)
    parser.add_argument("--disable-prepared-cache", action="store_true", default=None)
    parser.add_argument("--min-contexts", type=int)
    parser.add_argument("--max-skipped-contexts", type=int)
    parser.add_argument("--require-both-bases", action="store_true", default=None)
    parser.add_argument("--no-require-both-bases", action="store_false", dest="require_both_bases")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    grid_overrides = {
        key: getattr(args, key)
        for key in [
            "dataset_root",
            "context_manifest",
            "decoder_manifest",
            "dataset_name",
            "dataset_family",
            "samples",
            "patches",
            "bases",
            "distances",
            "rounds",
            "rounds_labels",
            "decoder_pathway",
            "heldout_split_types",
            "max_contexts",
            "dem_source",
            "reference_dem_sources",
            "orbit_mode",
            "train_shots",
            "heldout_shots",
            "steps",
            "subsample_count",
            "subsample_shots",
            "subsample_steps",
            "max_windows",
            "max_window_bits",
            "detector_pair_window_budget",
            "logical_detector_pair_window_budget",
            "window_plan_mode",
            "pca_ranks",
            "random_control_ranks",
            "random_control_seeds",
            "nmf_steps",
            "kmeans_max_iter",
            "kmeans_check_convergence",
            "include_upstream_dmle",
            "upstream_dmle_repo",
            "upstream_dmle_epochs",
            "upstream_dmle_lr",
            "upstream_dmle_batch_size",
            "upstream_dmle_minibatch",
            "upstream_dmle_path_file",
            "upstream_dmle_path_search_max_time",
            "dtype",
            "likelihood_backend",
            "cuda_kernel_variant",
            "spectral_memory_cap_mib",
            "disable_prepared_cache",
        ]
    }
    scorecard_overrides = {
        key: getattr(args, key)
        for key in [
            "min_contexts",
            "max_skipped_contexts",
            "require_both_bases",
        ]
    }
    return run_google_xz_scorecard_from_config(
        config_path=args.config,
        output_dir=args.output_dir,
        grid_overrides=grid_overrides,
        scorecard_overrides=scorecard_overrides,
    )


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    path = Path(config_path)
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Google X/Z scorecard config must be a mapping")
    section = data.get("google_xz_scorecard", data)
    if not isinstance(section, dict):
        raise ValueError("google_xz_scorecard config section must be a mapping")
    return dict(section)


def _mapping(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("config subsection must be a mapping")
    return dict(value)


def _context_id(context: dict[str, object]) -> str:
    if context.get("context_id"):
        return str(context["context_id"])
    keys = ["heldout_split_type", "sample_id", "patch_id", "basis", "rounds_label"]
    return "__".join(str(context.get(key)) for key in keys)


def _best_record(records: list[dict[str, object]]) -> dict[str, object] | None:
    if not records:
        return None
    return min(records, key=lambda record: (_none_high(record.get(PRIMARY_METRIC)), int(record.get("parameter_count") or 10**9)))


def _compact_record(record: dict[str, object] | None) -> dict[str, object] | None:
    if record is None:
        return None
    keys = [
        "model",
        "parameter_count",
        "compression_ratio",
        "baseline_family",
        "baseline_display_name",
        "baseline_variant",
        "baseline_implementation",
        "baseline_kind",
        "upstream_dmle_qec_direct_adapter",
        "upstream_dmle_qec_component",
        "upstream_dmle_qec_complete_implementation",
        "upstream_dmle_qec_compatibility_scope",
        "upstream_dmle_qec_missing_components",
        *SUMMARY_METRICS,
    ]
    return {key: record.get(key) for key in keys}


def _metric_delta(left: dict[str, object] | None, right: dict[str, object] | None, metric: str) -> float | None:
    if left is None or right is None or left.get(metric) is None or right.get(metric) is None:
        return None
    return float(left[metric]) - float(right[metric])


def _compression_ratio(local: dict[str, object] | None, compressed: dict[str, object] | None) -> float | None:
    if local is None or compressed is None:
        return None
    left = local.get("parameter_count")
    right = compressed.get("parameter_count")
    if left is None or right in (None, 0):
        return None
    return float(left) / float(right)


def _metric_from_compact(record: object, metric: str) -> float | None:
    if not isinstance(record, dict) or record.get(metric) is None:
        return None
    return float(record[metric])


def _distance_from_patch(patch_id: object) -> int | None:
    text = str(patch_id or "")
    if text.startswith("d3_"):
        return 3
    if text.startswith("d5_"):
        return 5
    if text.startswith("d7_"):
        return 7
    return None


def record_distance(records: list[dict[str, object]], patch_id: object) -> int | None:
    for record in records:
        if record.get("distance") is not None:
            return int(record["distance"])
    return _distance_from_patch(patch_id)


def _first_non_null(values: Iterable[object]) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


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


def _none_high(value: object) -> float:
    return float(value) if value is not None else float("inf")


def _model_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "-"
    return ", ".join(f"{model}:{count}" for model, count in sorted(counts.items()))


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


if __name__ == "__main__":
    main()

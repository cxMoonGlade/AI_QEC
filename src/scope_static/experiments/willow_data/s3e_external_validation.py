from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any

import yaml

from . import gdisc15b_grid
from .gdisc15b_grid import PRIMARY_METRIC, SUMMARY_METRICS


DEFAULT_CONFIG = Path("configs/scope_static/stage3e_google_external_validation.yaml")
DEFAULT_OUTPUT_DIR = Path("outputs/google_static/S3E_google_external_validation")

CLAIM_BOUNDARY = (
    "S3E Google external validation reports predictive utility, compression, calibration, "
    "paired improvements, transfer-ready context coverage, and explicitly labelled proxy diagnostics only. "
    "Google Set1 does not provide true hidden physical-mechanism labels, so S3E must not report true omega "
    "or physical-mechanism recovery."
)

GRID_DEFAULTS: dict[str, Any] = {
    "dataset_root": "/home/cx/Document/google_72Q_surface_code_d3_d5_set1",
    "samples": "sample_00,sample_01",
    "patches": "d3_at_q5_5",
    "bases": "X,Z",
    "rounds_labels": "r13",
    "heldout_split_types": "shot-heldout",
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
    "eval_window_plan_mode": "structured_higher_order",
    "eval_max_window_bits": 6,
    "eval_max_windows": 256,
    "eval_radius": 1.0,
    "eval_template_window_budget": 32,
    "eval_orbit_window_budget": 64,
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

ACCEPTANCE_DEFAULTS: dict[str, Any] = {
    "min_contexts": 4,
    "max_skipped_contexts": 0,
    "min_compression_ratio": 5.0,
    "near_local_excess_tolerance": 1.0e-4,
    "min_random_control_margin": 1.0e-3,
    "require_random_controls": True,
}

GRID_FLAGS = {
    "dataset_root": "--dataset-root",
    "samples": "--samples",
    "patches": "--patches",
    "bases": "--bases",
    "rounds_labels": "--rounds-labels",
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
    "eval_window_plan_mode": "--eval-window-plan-mode",
    "eval_max_window_bits": "--eval-max-window-bits",
    "eval_max_windows": "--eval-max-windows",
    "eval_radius": "--eval-radius",
    "eval_template_window_budget": "--eval-template-window-budget",
    "eval_orbit_window_budget": "--eval-orbit-window-budget",
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


def run_s3e_google_external_validation_from_config(
    *,
    config_path: str | Path | None = DEFAULT_CONFIG,
    output_dir: str | Path | None = None,
    grid_overrides: dict[str, Any] | None = None,
    acceptance_overrides: dict[str, Any] | None = None,
) -> dict[str, object]:
    start = time.perf_counter()
    cfg = _load_config(config_path)
    grid_cfg = {**GRID_DEFAULTS, **_mapping(cfg.get("grid"))}
    acceptance_cfg = {**ACCEPTANCE_DEFAULTS, **_mapping(cfg.get("acceptance"))}
    grid_cfg.update({key: value for key, value in (grid_overrides or {}).items() if value is not None})
    acceptance_cfg.update({key: value for key, value in (acceptance_overrides or {}).items() if value is not None})

    output = Path(output_dir if output_dir is not None else cfg.get("output_dir", DEFAULT_OUTPUT_DIR))
    grid_output = Path(str(grid_cfg.pop("output_dir", output / "GDISC15b_grid")))
    output.mkdir(parents=True, exist_ok=True)
    grid_output.mkdir(parents=True, exist_ok=True)

    grid_argv = _grid_argv(grid_cfg, grid_output)
    grid_result = gdisc15b_grid.main(grid_argv)
    acceptance = _evaluate_acceptance(grid_result, acceptance_cfg)
    result = {
        "run": {
            "name": "S3E_google_external_validation",
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
            "acceptance": _jsonable(acceptance_cfg),
            "grid_argv": grid_argv,
        },
        "acceptance": acceptance,
        "grid": {
            "completed_contexts": grid_result["grid"]["completed_contexts"],
            "skipped_contexts": grid_result["grid"]["skipped_contexts"],
            "required_baselines": grid_result["required_baselines"],
            "uncertainty": grid_result["uncertainty"],
            "model_summary": grid_result["model_summary"],
        },
    }
    _write_outputs(output, result)
    _print_summary(result)
    return result


def _evaluate_acceptance(grid_result: dict[str, object], acceptance_cfg: dict[str, Any]) -> dict[str, object]:
    completed = list(grid_result["grid"]["completed_contexts"])
    skipped = list(grid_result["grid"]["skipped_contexts"])
    summary = list(grid_result["model_summary"])
    local = _model_row(summary, "local_full")
    compressed = [
        row
        for row in summary
        if str(row.get("model", "")).startswith("GDISC15_") and "random_low_rank" not in str(row.get("model", ""))
    ]
    random_controls = [row for row in summary if "random_low_rank" in str(row.get("model", ""))]
    best_compressed = _best_by_primary(compressed)
    best_random = _best_by_primary(random_controls)

    min_contexts = int(acceptance_cfg["min_contexts"])
    max_skipped = int(acceptance_cfg["max_skipped_contexts"])
    min_compression = float(acceptance_cfg["min_compression_ratio"])
    near_local_tol = float(acceptance_cfg["near_local_excess_tolerance"])
    random_margin_min = float(acceptance_cfg["min_random_control_margin"])
    require_random = bool(acceptance_cfg["require_random_controls"])
    execution_audit = _context_execution_audit(completed)

    local_metric = _metric_mean(local, PRIMARY_METRIC)
    compressed_metric = _metric_mean(best_compressed, PRIMARY_METRIC)
    random_metric = _metric_mean(best_random, PRIMARY_METRIC)
    local_params = _float_or_none(local.get("params_mean")) if local is not None else None
    compressed_params = _float_or_none(best_compressed.get("params_mean")) if best_compressed is not None else None
    compression_ratio = (
        float(local_params / compressed_params)
        if local_params is not None and compressed_params not in (None, 0.0)
        else None
    )
    compressed_delta = (
        float(compressed_metric - local_metric)
        if compressed_metric is not None and local_metric is not None
        else None
    )
    random_margin = (
        float(random_metric - compressed_metric)
        if random_metric is not None and compressed_metric is not None
        else None
    )

    checks = {
        "contexts_completed": {
            "passed": len(completed) >= min_contexts,
            "value": len(completed),
            "threshold": min_contexts,
        },
        "contexts_skipped": {
            "passed": len(skipped) <= max_skipped,
            "value": len(skipped),
            "threshold": max_skipped,
        },
        "local_full_present": {
            "passed": local is not None,
            "value": local is not None,
        },
        "compressed_candidate_present": {
            "passed": best_compressed is not None,
            "value": None if best_compressed is None else best_compressed.get("model"),
        },
        "random_controls_present": {
            "passed": (not require_random) or bool(random_controls),
            "value": len(random_controls),
        },
        "near_local_excess_nll": {
            "passed": compressed_delta is not None and compressed_delta <= near_local_tol,
            "value": compressed_delta,
            "threshold": near_local_tol,
            "metric": PRIMARY_METRIC,
        },
        "compressed_vs_random_controls": {
            "passed": (not require_random) or (random_margin is not None and random_margin >= random_margin_min),
            "value": random_margin,
            "threshold": random_margin_min,
            "metric": PRIMARY_METRIC,
        },
        "compression_ratio": {
            "passed": compression_ratio is not None and compression_ratio >= min_compression,
            "value": compression_ratio,
            "threshold": min_compression,
        },
        "true_hidden_omega_claim": {
            "passed": True,
            "value": False,
            "required": False,
            "note": "Google Set1 has no true hidden physical-mechanism labels; proxy labels only.",
        },
        "gpu_execution": {
            "passed": bool(execution_audit["all_cuda_extension"]),
            "value": execution_audit["all_cuda_extension"],
            "required": True,
            "contexts": execution_audit["contexts"],
        },
    }
    return {
        "s3e_external_validation_passed": all(bool(item["passed"]) for item in checks.values()),
        "primary_metric": PRIMARY_METRIC,
        "claim_boundary": CLAIM_BOUNDARY,
        "best_compressed_model": _compact_model_row(best_compressed),
        "local_full": _compact_model_row(local),
        "best_random_control": _compact_model_row(best_random),
        "compressed_minus_local_excess_nll": compressed_delta,
        "random_minus_compressed_excess_nll": random_margin,
        "compression_ratio_vs_local_full": compression_ratio,
        "checks": checks,
        "execution_audit": execution_audit,
    }


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
    if bool(grid_cfg.get("include_upstream_dmle")):
        argv.append("--include-upstream-dmle")
    if bool(grid_cfg.get("disable_prepared_cache")):
        argv.append("--disable-prepared-cache")
    if bool(grid_cfg.get("kmeans_check_convergence")):
        argv.append("--kmeans-check-convergence")
    argv.extend(["--output-dir", str(output_dir)])
    return argv


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n")
    (output / "acceptance.json").write_text(json.dumps(_jsonable(result["acceptance"]), indent=2, sort_keys=True) + "\n")
    (output / "run_manifest.json").write_text(json.dumps(_jsonable(result["config"]), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(_summary_markdown(result))


def _summary_markdown(result: dict[str, object]) -> str:
    acceptance = result["acceptance"]
    checks = acceptance["checks"]
    lines = [
        "# S3E Google External Validation",
        "",
        f"- Passed: `{str(acceptance['s3e_external_validation_passed']).lower()}`",
        f"- Primary metric: `{acceptance['primary_metric']}`",
        f"- Completed contexts: `{len(result['grid']['completed_contexts'])}`",
        f"- Skipped contexts: `{len(result['grid']['skipped_contexts'])}`",
        f"- Grid metrics: `{result['run']['grid_metrics_path']}`",
        f"- True hidden omega recovery claim: `false`",
        "",
        "Google Set1 has real measurement-derived observations but no true hidden physical-mechanism labels. "
        "This stage validates predictive utility, compression, calibration, and proxy diagnostics only.",
        "",
        "## Acceptance",
        "",
        "| check | passed | value | threshold |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, item in checks.items():
        lines.append(
            f"| {name} | `{str(item.get('passed')).lower()}` | "
            f"{_fmt_cell(item.get('value'))} | {_fmt_cell(item.get('threshold', item.get('required', '-')))} |"
        )
    lines.extend(
        [
            "",
            "## Selected Comparators",
            "",
            "| role | model | params | excess NLL | wins/total |",
            "| --- | --- | ---: | ---: | ---: |",
            _comparator_row("local_full", acceptance.get("local_full")),
            _comparator_row("best_compressed", acceptance.get("best_compressed_model")),
            _comparator_row("best_random_control", acceptance.get("best_random_control")),
            "",
        ]
    )
    return "\n".join(lines)


def _print_summary(result: dict[str, object]) -> None:
    acceptance = result["acceptance"]
    print("S3E Google external validation complete")
    print(f"metrics: {Path(str(result['run']['output_dir'])) / 'metrics.json'}")
    print(f"summary: {Path(str(result['run']['output_dir'])) / 'summary.md'}")
    print(f"passed: {acceptance['s3e_external_validation_passed']}")
    best = acceptance.get("best_compressed_model") or {}
    print(
        "best compressed: "
        f"{best.get('model')} excess={best.get(f'{PRIMARY_METRIC}_mean')} params={best.get('params_mean')}"
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
        raise ValueError("S3E Google config must be a mapping")
    section = data.get("stage3e_google_external_validation", data)
    if not isinstance(section, dict):
        raise ValueError("stage3e_google_external_validation config section must be a mapping")
    return dict(section)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run S3E Google external validation.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dataset-root")
    parser.add_argument("--samples")
    parser.add_argument("--patches")
    parser.add_argument("--bases")
    parser.add_argument("--rounds-labels")
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
    parser.add_argument("--eval-window-plan-mode")
    parser.add_argument("--eval-max-window-bits", type=int)
    parser.add_argument("--eval-max-windows", type=int)
    parser.add_argument("--eval-radius", type=float)
    parser.add_argument("--eval-template-window-budget", type=int)
    parser.add_argument("--eval-orbit-window-budget", type=int)
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
    parser.add_argument("--min-compression-ratio", type=float)
    parser.add_argument("--near-local-excess-tolerance", type=float)
    parser.add_argument("--min-random-control-margin", type=float)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    grid_overrides = {
        key: getattr(args, key)
        for key in [
            "dataset_root",
            "samples",
            "patches",
            "bases",
            "rounds_labels",
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
            "eval_window_plan_mode",
            "eval_max_window_bits",
            "eval_max_windows",
            "eval_radius",
            "eval_template_window_budget",
            "eval_orbit_window_budget",
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
    acceptance_overrides = {
        key: getattr(args, key)
        for key in [
            "min_contexts",
            "max_skipped_contexts",
            "min_compression_ratio",
            "near_local_excess_tolerance",
            "min_random_control_margin",
        ]
    }
    return run_s3e_google_external_validation_from_config(
        config_path=args.config,
        output_dir=args.output_dir,
        grid_overrides=grid_overrides,
        acceptance_overrides=acceptance_overrides,
    )


def _mapping(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("S3E config subsection must be a mapping")
    return dict(value)


def _model_row(rows: list[dict[str, object]], model: str) -> dict[str, object] | None:
    return next((row for row in rows if row.get("model") == model), None)


def _best_by_primary(rows: list[dict[str, object]]) -> dict[str, object] | None:
    valid = [row for row in rows if _metric_mean(row, PRIMARY_METRIC) is not None]
    if not valid:
        return None
    return min(valid, key=lambda row: (_metric_mean(row, PRIMARY_METRIC), _float_or_none(row.get("params_mean")) or 10**18))


def _metric_mean(row: dict[str, object] | None, metric: str) -> float | None:
    if row is None:
        return None
    return _float_or_none(row.get(f"{metric}_mean"))


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _compact_model_row(row: dict[str, object] | None) -> dict[str, object] | None:
    if row is None:
        return None
    keys = [
        "model",
        "n",
        "params_mean",
        "params_std",
        "wins_primary_vs_local_full",
        "total_paired",
        *[f"{metric}_mean" for metric in SUMMARY_METRICS],
        *[f"{metric}_paired_delta_mean" for metric in SUMMARY_METRICS],
    ]
    return {key: row.get(key) for key in keys if key in row}


def _context_execution_audit(completed_contexts: list[dict[str, object]]) -> dict[str, object]:
    contexts = []
    for context in completed_contexts:
        output_root = Path(str(context.get("output_root", "")))
        metrics_path = output_root / "GDISC15_real_local_mechanism_discovery" / "metrics.json"
        item = {
            "context_id": output_root.name,
            "metrics_path": str(metrics_path),
            "device": None,
            "likelihood_backend": None,
            "cuda_kernel_variant": None,
            "cuda_extension": False,
            "loaded": False,
        }
        try:
            data = json.loads(metrics_path.read_text())
            run = data.get("run", {})
            item.update(
                {
                    "device": run.get("device"),
                    "likelihood_backend": run.get("likelihood_backend"),
                    "cuda_kernel_variant": run.get("cuda_kernel_variant"),
                    "cuda_extension": run.get("device") == "cuda" and run.get("likelihood_backend") == "cuda_extension",
                    "loaded": True,
                }
            )
        except Exception as exc:
            item["error"] = str(exc)
        contexts.append(item)
    return {
        "all_cuda_extension": bool(contexts) and all(bool(item["cuda_extension"]) for item in contexts),
        "contexts": contexts,
    }


def _fmt_cell(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return f"`{str(value).lower()}`"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _comparator_row(role: str, row: object) -> str:
    if not isinstance(row, dict):
        return f"| {role} | - | - | - | - |"
    wins = row.get("wins_primary_vs_local_full")
    total = row.get("total_paired")
    return (
        f"| {role} | {row.get('model', '-')} | {_fmt_cell(row.get('params_mean'))} | "
        f"{_fmt_cell(row.get(f'{PRIMARY_METRIC}_mean'))} | "
        f"{'-' if wins is None or total is None else f'{wins}/{total}'} |"
    )


def _jsonable(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time
from types import SimpleNamespace
from typing import Any, Iterable

import numpy as np
import torch
import yaml

from scope_static.dem.windows import WindowPlan
from scope_static.google.inventory import (
    DATASET_105Q,
    DATASET_NAMES,
    DATASET_REPETITION_D29,
    DATASET_SURFACE_SET1,
    DATASET_SURFACE_SET2,
    DEFAULT_DATASET_ROOTS,
    EXPECTED_LEAF_COUNTS,
    FORBIDDEN_TRUE_LABELS,
    google_context_id,
    load_context_manifest,
    write_google_inventory_artifacts,
)
from scope_static.google.set1 import build_google_fault_graph, find_google_set1_leaf

from . import gdisc15b_grid
from .gdisc15b_grid import PRIMARY_METRIC, SUMMARY_METRICS
from .xz_scorecard import GRID_DEFAULTS, GRID_FLAGS
from scope_static.archive.experiments.google_gdisc15 import static as run_google_static
from scope_static.archive.experiments.google_gdisc15.static import (
    _eval_window_config,
    _fmt_float,
    _window_config,
    _window_plan_audit,
)


DEFAULT_CONFIG = Path("configs/archive/google_gdisc15/google_benchmark_suite_v1.yaml")
DEFAULT_OUTPUT_DIR = Path("outputs/google_static/google_benchmark_suite_v1")

BENCHMARK_ORDER = ("B0", "B1", "B2", "B3", "B4", "B5", "B6")
CLAIM_BOUNDARY = (
    "Google Benchmark Suite V1 reports predictive utility, transfer, calibration, "
    "decoder-facing proxies, DEM proxy structure, and sample efficiency only. It does "
    "not claim true physical mechanism recovery, true hidden fault partitions, or "
    "public F/M label or legacy catalog-ID recovery from Google hardware data."
)

BASELINE_MODELS = {"dmle_qec", "dmle_qec_upstream", "global_shared_scalar"}
PENDING_DATASETS = {
    "B4": DATASET_SURFACE_SET2,
    "B5": DATASET_105Q,
    "B6": DATASET_REPETITION_D29,
}


def main(argv: list[str] | None = None) -> dict[str, object]:
    start = time.perf_counter()
    args = _parse_args(argv)
    cfg = _load_config(args.config)
    suite_cfg = _mapping(cfg.get("suite"))
    output = Path(args.output_dir if args.output_dir is not None else suite_cfg.get("output_dir", DEFAULT_OUTPUT_DIR))
    output.mkdir(parents=True, exist_ok=True)
    selected = _selected_benchmarks(args.benchmarks or suite_cfg.get("benchmarks", "B0"))

    result: dict[str, object] = {
        "run": {
            "name": "Google_Benchmark_Suite_V1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "claim_boundary": CLAIM_BOUNDARY,
            "config_path": str(args.config),
            "output_dir": str(output),
            "selected_benchmarks": selected,
        },
        "benchmarks": {},
    }
    inventory_result: dict[str, object] | None = None
    for benchmark_id in BENCHMARK_ORDER:
        if benchmark_id not in selected:
            continue
        bench_output = output / benchmark_id
        if benchmark_id == "B0":
            inventory_result = _run_b0(cfg, bench_output)
            result["benchmarks"][benchmark_id] = _benchmark_ref(benchmark_id, bench_output, inventory_result)
        elif benchmark_id == "B1":
            bench_result = _run_grid_benchmark(cfg, benchmark_id, bench_output, inventory_result=inventory_result)
            result["benchmarks"][benchmark_id] = _benchmark_ref(benchmark_id, bench_output, bench_result)
        elif benchmark_id == "B2":
            bench_result = _run_sample_efficiency(cfg, bench_output, inventory_result=inventory_result)
            result["benchmarks"][benchmark_id] = _benchmark_ref(benchmark_id, bench_output, bench_result)
        elif benchmark_id == "B3":
            bench_result = _run_set1_transfer(cfg, bench_output)
            result["benchmarks"][benchmark_id] = _benchmark_ref(benchmark_id, bench_output, bench_result)
        else:
            bench_result = _write_pending_transfer_benchmark(cfg, benchmark_id, bench_output, inventory_result)
            result["benchmarks"][benchmark_id] = _benchmark_ref(benchmark_id, bench_output, bench_result)

    result["run"]["wall_seconds"] = time.perf_counter() - start
    _write_json(output / "metrics.json", result)
    (output / "summary.md").write_text(_suite_summary(result), encoding="utf-8")
    print(f"Google Benchmark Suite V1 complete: {output / 'summary.md'}")
    return result


def _run_b0(cfg: dict[str, object], output: Path) -> dict[str, object]:
    start = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    inventory_cfg = _inventory_config(cfg)
    result = write_google_inventory_artifacts(
        output_dir=output,
        dataset_roots=inventory_cfg["dataset_roots"],
        dataset_names=inventory_cfg["dataset_names"],
        dem_proxy_mode=str(inventory_cfg["dem_proxy_mode"]),
    )
    label_manifest = _read_json(result["label_manifest_path"])
    preprocessing_audit = _read_json(result["audit_path"])
    eval_window_audit = _b0_eval_window_audit(cfg)
    checks = _b0_checks(
        preprocessing_audit,
        label_manifest,
        eval_window_audit,
        dataset_names=inventory_cfg["dataset_names"],
    )
    audit_lock = {
        "benchmark_id": "B0",
        "name": "inventory/window audit lock",
        "claim_boundary": CLAIM_BOUNDARY,
        "passed": all(bool(item["passed"]) for item in checks.values()),
        "checks": checks,
        "inventory": {
            "context_manifest_path": result["context_manifest_path"],
            "decoder_manifest_path": result["decoder_manifest_path"],
            "label_manifest_path": result["label_manifest_path"],
            "preprocessing_audit_path": result["audit_path"],
            "num_contexts": result["num_contexts"],
            "num_decoder_rows": result["num_decoder_rows"],
        },
        "wall_seconds": time.perf_counter() - start,
    }
    _write_json(output / "run_manifest.json", audit_lock)
    _write_json(output / "context_selection.json", preprocessing_audit.get("datasets", {}))
    _write_json(output / "decoder_selection.json", preprocessing_audit.get("decoder_coverage", {}))
    _write_json(output / "preprocessing_audit.json", preprocessing_audit)
    _write_json(output / "eval_window_audit.json", eval_window_audit)
    _write_json(output / "model_summary.json", [])
    _write_json(output / "context_scorecard.json", [])
    _write_json(output / "paired_baseline_comparison.json", [])
    (output / "summary.md").write_text(_b0_summary(audit_lock), encoding="utf-8")
    return {**audit_lock, **result}


def _run_grid_benchmark(
    cfg: dict[str, object],
    benchmark_id: str,
    output: Path,
    *,
    inventory_result: dict[str, object] | None,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    bench_cfg = _mapping(cfg.get(benchmark_id))
    grid_cfg = _grid_config(cfg, benchmark_id, inventory_result=inventory_result)
    grid_output = output / "GDISC15b_grid"
    grid_result = gdisc15b_grid.main(_grid_argv(grid_cfg, grid_output))
    flat_records = _normalise_records(grid_result.get("flat_records", []), benchmark_id=benchmark_id)
    context_scorecard = _context_scorecard(flat_records)
    paired = _paired_baseline_comparison(flat_records)
    eval_window_audit = _collect_grid_eval_window_audits(grid_result.get("grid", {}).get("completed_contexts", []))
    run_manifest = {
        "benchmark_id": benchmark_id,
        "name": str(bench_cfg.get("name", "Set1 structured same-context sanity benchmark")),
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_metric": PRIMARY_METRIC,
        "grid_output_dir": str(grid_output),
        "grid_config": _jsonable(grid_cfg),
        "grid_run": grid_result.get("run", {}),
    }
    _write_common_benchmark_artifacts(
        output,
        run_manifest=run_manifest,
        grid_result=grid_result,
        flat_records=flat_records,
        context_scorecard=context_scorecard,
        paired_baseline_comparison=paired,
        eval_window_audit=eval_window_audit,
    )
    return {
        "run_manifest": run_manifest,
        "num_records": len(flat_records),
        "num_contexts": len(context_scorecard),
        "primary_metric": PRIMARY_METRIC,
    }


def _run_sample_efficiency(
    cfg: dict[str, object],
    output: Path,
    *,
    inventory_result: dict[str, object] | None,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    bench_cfg = _mapping(cfg.get("B2"))
    train_shots = _csv_ints(bench_cfg.get("train_shot_grid", "128,256,512,1024,2048,4096,8192"))
    heldout_shots = int(bench_cfg.get("heldout_shots", 4096))
    all_records: list[dict[str, object]] = []
    shot_runs = []
    eval_audits = []
    for shots in train_shots:
        shot_output = output / "runs" / f"train_shots_{shots}"
        grid_cfg = _grid_config(cfg, "B2", inventory_result=inventory_result)
        grid_cfg["train_shots"] = int(shots)
        grid_cfg["heldout_shots"] = heldout_shots
        grid_result = gdisc15b_grid.main(_grid_argv(grid_cfg, shot_output))
        records = _normalise_records(grid_result.get("flat_records", []), benchmark_id="B2")
        for record in records:
            record["train_shots"] = int(shots)
            record["heldout_shots"] = heldout_shots
        all_records.extend(records)
        eval_audits.extend(_collect_grid_eval_window_audits(grid_result.get("grid", {}).get("completed_contexts", [])))
        shot_runs.append(
            {
                "train_shots": int(shots),
                "output_dir": str(shot_output),
                "completed_contexts": len(grid_result.get("grid", {}).get("completed_contexts", [])),
                "skipped_contexts": len(grid_result.get("grid", {}).get("skipped_contexts", [])),
            }
        )

    sample_efficiency = _sample_efficiency_summary(all_records, train_shots=train_shots)
    context_scorecard = _context_scorecard(all_records)
    paired = _paired_baseline_comparison(all_records)
    run_manifest = {
        "benchmark_id": "B2",
        "name": str(bench_cfg.get("name", "Set1 sample-efficiency benchmark")),
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_metric": PRIMARY_METRIC,
        "train_shot_grid": train_shots,
        "heldout_shots": heldout_shots,
        "shot_runs": shot_runs,
    }
    _write_common_benchmark_artifacts(
        output,
        run_manifest=run_manifest,
        grid_result={"grid": {"completed_contexts": [], "skipped_contexts": []}, "model_summary": _model_summary(all_records)},
        flat_records=all_records,
        context_scorecard=context_scorecard,
        paired_baseline_comparison=paired,
        eval_window_audit={"contexts": eval_audits},
    )
    _write_json(output / "sample_efficiency.json", sample_efficiency)
    return {
        "run_manifest": run_manifest,
        "num_records": len(all_records),
        "num_contexts": len(context_scorecard),
        "sample_efficiency_path": str(output / "sample_efficiency.json"),
    }


def _run_set1_transfer(cfg: dict[str, object], output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    bench_cfg = _mapping(cfg.get("B3"))
    transfer_cfg = _static_transfer_config(cfg)
    all_records: list[dict[str, object]] = []
    transfer_records: list[dict[str, object]] = []
    eval_audits = []
    run_refs = []
    for sample_id in _csv(transfer_cfg["source_samples"]):
        for patch_id in _csv(transfer_cfg["patches"]):
            for basis in _csv(transfer_cfg["bases"]):
                for rounds_label in _csv(transfer_cfg["rounds_labels"]):
                    run_output = output / "runs" / "__".join([sample_id, patch_id, basis, rounds_label])
                    argv = _static_transfer_argv(transfer_cfg, run_output, sample_id, patch_id, basis, rounds_label)
                    run_result = run_google_static.main(argv)
                    records = _normalise_records(run_result.get("records", []), benchmark_id="B3")
                    for record in records:
                        record.update(
                            {
                                "dataset_name": DATASET_SURFACE_SET1,
                                "dataset_family": "surface",
                                "context_id": google_context_id(
                                    dataset_name=DATASET_SURFACE_SET1,
                                    sample_id=sample_id,
                                    patch_id=patch_id,
                                    basis=basis,
                                    rounds_label=rounds_label,
                                ),
                                "source_sample_id": sample_id,
                                "sample_id": sample_id,
                                "patch_id": patch_id,
                                "basis": basis,
                                "distance": _distance_from_patch(patch_id),
                                "rounds_label": rounds_label,
                                "heldout_split_type": "source-shot-heldout",
                            }
                        )
                    transfers = _normalise_transfer_records(
                        run_result.get("cross_sample_transfer_records", []),
                        source_sample_id=sample_id,
                        patch_id=patch_id,
                        basis=basis,
                        rounds_label=rounds_label,
                    )
                    all_records.extend(records)
                    transfer_records.extend(transfers)
                    eval_audits.extend(run_result.get("window_audits", []))
                    run_refs.append({"source_sample_id": sample_id, "output_dir": str(run_output)})
    transfer_scorecard = _transfer_scorecard(transfer_records)
    run_manifest = {
        "benchmark_id": "B3",
        "name": str(bench_cfg.get("name", "Set1 cross-sample transfer benchmark")),
        "claim_boundary": CLAIM_BOUNDARY,
        "source_fit_transfer_mode": "single_source_fit",
        "pooled_source_training": False,
        "target_fit_dmle_upper_comparator_available": False,
        "target_fit_dmle_upper_comparator_note": (
            "Current Set1 runner supports source-fit transfer records; pooled early-sample "
            "training and target-fit dMLE upper-comparator orchestration are explicit next seams."
        ),
        "runs": run_refs,
    }
    _write_common_benchmark_artifacts(
        output,
        run_manifest=run_manifest,
        grid_result={"grid": {"completed_contexts": run_refs, "skipped_contexts": []}, "model_summary": _model_summary(all_records)},
        flat_records=all_records,
        context_scorecard=_context_scorecard(all_records),
        paired_baseline_comparison=_paired_baseline_comparison(all_records),
        eval_window_audit={"contexts": eval_audits},
    )
    _write_json(output / "transfer_scorecard.json", transfer_scorecard)
    return {
        "run_manifest": run_manifest,
        "num_transfer_records": len(transfer_records),
        "transfer_scorecard_path": str(output / "transfer_scorecard.json"),
    }


def _write_pending_transfer_benchmark(
    cfg: dict[str, object],
    benchmark_id: str,
    output: Path,
    inventory_result: dict[str, object] | None,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    dataset_name = PENDING_DATASETS[benchmark_id]
    context_rows = []
    if inventory_result and Path(str(inventory_result.get("context_manifest_path", ""))).is_file():
        context_rows = [
            row
            for row in load_context_manifest(str(inventory_result["context_manifest_path"]))
            if row.get("dataset_name") == dataset_name
        ]
    reason = "requires unified GoogleLeaf training/evaluation runner beyond the current Set1 runner"
    run_manifest = {
        "benchmark_id": benchmark_id,
        "dataset_name": dataset_name,
        "claim_boundary": CLAIM_BOUNDARY,
        "implemented": False,
        "pending_reason": reason,
        "manifest_context_count": len(context_rows),
    }
    transfer_scorecard = {
        "benchmark_id": benchmark_id,
        "implemented": False,
        "pending_reason": reason,
        "dataset_name": dataset_name,
        "context_count_from_manifest": len(context_rows),
        "target_claim": {
            "B4": "Set2 calibration/domain-shift transfer",
            "B5": "105Q d3/d5 to d7 cross-distance transfer",
            "B6": "repetition d29 drift prediction",
        }[benchmark_id],
    }
    _write_json(output / "run_manifest.json", run_manifest)
    _write_json(output / "context_selection.json", context_rows)
    _write_json(output / "decoder_selection.json", {})
    _write_json(output / "preprocessing_audit.json", {"dataset_name": dataset_name, "claim_boundary": CLAIM_BOUNDARY})
    _write_json(output / "eval_window_audit.json", {})
    _write_json(output / "model_summary.json", [])
    _write_json(output / "context_scorecard.json", [])
    _write_json(output / "paired_baseline_comparison.json", [])
    _write_json(output / "transfer_scorecard.json", transfer_scorecard)
    (output / "summary.md").write_text(_pending_summary(transfer_scorecard), encoding="utf-8")
    return run_manifest


def _inventory_config(cfg: dict[str, object]) -> dict[str, object]:
    inventory = _mapping(cfg.get("inventory"))
    dataset_names = tuple(_csv(inventory.get("datasets", ",".join(DATASET_NAMES))))
    dataset_roots = {
        DATASET_REPETITION_D29: inventory.get("repetition_root", str(DEFAULT_DATASET_ROOTS[DATASET_REPETITION_D29])),
        DATASET_SURFACE_SET1: inventory.get("set1_root", str(DEFAULT_DATASET_ROOTS[DATASET_SURFACE_SET1])),
        DATASET_SURFACE_SET2: inventory.get("set2_root", str(DEFAULT_DATASET_ROOTS[DATASET_SURFACE_SET2])),
        DATASET_105Q: inventory.get("surface_105q_root", str(DEFAULT_DATASET_ROOTS[DATASET_105Q])),
    }
    return {
        "dataset_names": dataset_names,
        "dataset_roots": dataset_roots,
        "dem_proxy_mode": inventory.get("dem_proxy_mode", "first_per_dataset"),
    }


def _grid_config(
    cfg: dict[str, object],
    benchmark_id: str,
    *,
    inventory_result: dict[str, object] | None,
) -> dict[str, Any]:
    common = _mapping(cfg.get("common_grid"))
    bench_cfg = _mapping(cfg.get(benchmark_id))
    grid_cfg = {**GRID_DEFAULTS, **common, **_mapping(bench_cfg.get("grid"))}
    if inventory_result is not None:
        grid_cfg.setdefault("context_manifest", "")
        grid_cfg.setdefault("decoder_manifest", "")
        if not str(grid_cfg.get("context_manifest", "")).strip():
            grid_cfg["context_manifest"] = str(inventory_result["context_manifest_path"])
        if not str(grid_cfg.get("decoder_manifest", "")).strip():
            grid_cfg["decoder_manifest"] = str(inventory_result["decoder_manifest_path"])
    return grid_cfg


def _static_transfer_config(cfg: dict[str, object]) -> dict[str, Any]:
    common = _mapping(cfg.get("common_grid"))
    bench_cfg = _mapping(cfg.get("B3"))
    transfer = _mapping(bench_cfg.get("transfer"))
    grid = {**GRID_DEFAULTS, **common, **_mapping(bench_cfg.get("grid"))}
    return {
        "dataset_root": grid["dataset_root"],
        "source_samples": transfer.get("source_samples", "sample_00,sample_01"),
        "patches": transfer.get("patches", grid.get("patches", "d3_at_q5_5")),
        "bases": transfer.get("bases", grid.get("bases", "X,Z")),
        "rounds_labels": transfer.get("rounds_labels", grid.get("rounds_labels", "r13")),
        "target_sample_start": int(transfer.get("target_sample_start", 2)),
        "target_sample_stop": int(transfer.get("target_sample_stop", 4)),
        "dem_source": grid.get("dem_source", "decoder_si1000"),
        "orbit_modes": transfer.get("orbit_modes", "fault_graph_heuristic"),
        "models": transfer.get("models", "local,dmle_qec,hard_orbit,soft_feature_orbit"),
        "train_shots": int(transfer.get("train_shots", grid.get("train_shots", 4096))),
        "heldout_shots": int(transfer.get("heldout_shots", grid.get("heldout_shots", 4096))),
        "steps": int(transfer.get("steps", grid.get("steps", 40))),
        "max_windows": int(grid.get("max_windows", 96)),
        "max_window_bits": int(grid.get("max_window_bits", 8)),
        "detector_pair_window_budget": int(grid.get("detector_pair_window_budget", 48)),
        "logical_detector_pair_window_budget": int(grid.get("logical_detector_pair_window_budget", 48)),
        "window_plan_mode": grid.get("window_plan_mode", "logical_aware"),
        "eval_window_plan_mode": grid.get("eval_window_plan_mode", "structured_higher_order"),
        "eval_max_window_bits": int(grid.get("eval_max_window_bits", 6)),
        "eval_max_windows": int(grid.get("eval_max_windows", 256)),
        "eval_radius": float(grid.get("eval_radius", 1.0)),
        "eval_template_window_budget": int(grid.get("eval_template_window_budget", 32)),
        "eval_orbit_window_budget": int(grid.get("eval_orbit_window_budget", 64)),
        "seed": int(grid.get("seed", 0)),
        "dtype": grid.get("dtype", "float64"),
        "likelihood_backend": grid.get("likelihood_backend", "auto"),
        "cuda_kernel_variant": grid.get("cuda_kernel_variant", "dp"),
        "spectral_memory_cap_mib": int(grid.get("spectral_memory_cap_mib", 1024)),
    }


def _grid_argv(grid_cfg: dict[str, Any], output_dir: Path) -> list[str]:
    argv: list[str] = []
    for key, flag in GRID_FLAGS.items():
        value = grid_cfg.get(key)
        if value is None:
            continue
        if key in {"context_manifest", "decoder_manifest", "upstream_dmle_path_file"} and not str(value).strip():
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


def _static_transfer_argv(
    cfg: dict[str, Any],
    output_dir: Path,
    sample_id: str,
    patch_id: str,
    basis: str,
    rounds_label: str,
) -> list[str]:
    return [
        "--dataset-root",
        str(cfg["dataset_root"]),
        "--sample-id",
        sample_id,
        "--patch-id",
        patch_id,
        "--basis",
        basis,
        "--rounds-label",
        rounds_label,
        "--dem-source",
        str(cfg["dem_source"]),
        "--orbit-modes",
        str(cfg["orbit_modes"]),
        "--models",
        str(cfg["models"]),
        "--train-shots",
        str(cfg["train_shots"]),
        "--heldout-shots",
        str(cfg["heldout_shots"]),
        "--steps",
        str(cfg["steps"]),
        "--max-windows",
        str(cfg["max_windows"]),
        "--max-window-bits",
        str(cfg["max_window_bits"]),
        "--detector-pair-window-budget",
        str(cfg["detector_pair_window_budget"]),
        "--logical-detector-pair-window-budget",
        str(cfg["logical_detector_pair_window_budget"]),
        "--window-plan-mode",
        str(cfg["window_plan_mode"]),
        "--eval-window-plan-mode",
        str(cfg["eval_window_plan_mode"]),
        "--eval-max-window-bits",
        str(cfg["eval_max_window_bits"]),
        "--eval-max-windows",
        str(cfg["eval_max_windows"]),
        "--eval-radius",
        str(cfg["eval_radius"]),
        "--eval-template-window-budget",
        str(cfg["eval_template_window_budget"]),
        "--eval-orbit-window-budget",
        str(cfg["eval_orbit_window_budget"]),
        "--cross-sample-transfer",
        "--cross-sample-start",
        str(cfg["target_sample_start"]),
        "--cross-sample-stop",
        str(cfg["target_sample_stop"]),
        "--native-gpu",
        "--seed",
        str(cfg["seed"]),
        "--dtype",
        str(cfg["dtype"]),
        "--likelihood-backend",
        str(cfg["likelihood_backend"]),
        "--cuda-kernel-variant",
        str(cfg["cuda_kernel_variant"]),
        "--spectral-memory-cap-mib",
        str(cfg["spectral_memory_cap_mib"]),
        "--output-dir",
        str(output_dir),
    ]


def _b0_eval_window_audit(cfg: dict[str, object]) -> dict[str, object]:
    b0_cfg = _mapping(cfg.get("B0"))
    window_cfg = _mapping(b0_cfg.get("window_audit_context"))
    if window_cfg.get("enabled", True) is False:
        return {"available": False, "skip_reason": "window_audit_context disabled"}
    grid = _grid_config(cfg, "B1", inventory_result=None)
    try:
        sample_id = str(window_cfg.get("sample_id", _first_csv(grid.get("samples", "sample_01"))))
        patch_id = str(window_cfg.get("patch_id", _first_csv(grid.get("patches", "d3_at_q5_5"))))
        basis = str(window_cfg.get("basis", _first_csv(grid.get("bases", "X"))))
        rounds_label = str(window_cfg.get("rounds_label", _first_csv(grid.get("rounds_labels", "r13"))))
        leaf = find_google_set1_leaf(
            str(grid["dataset_root"]),
            sample_id=sample_id,
            patch_id=patch_id,
            basis=basis,
            rounds_label=rounds_label,
        )
        graph, _audit = build_google_fault_graph(
            leaf,
            dem_source=str(grid.get("dem_source", "decoder_si1000")),
            orbit_mode=str(grid.get("orbit_mode", "fault_graph_heuristic")),
            residual_rank=int(grid.get("residual_rank", 0)),
        )
        ns = SimpleNamespace(
            window_plan_mode=grid.get("window_plan_mode", "logical_aware"),
            max_window_bits=int(grid.get("max_window_bits", 8)),
            max_windows=int(grid.get("max_windows", 96)),
            detector_pair_window_budget=int(grid.get("detector_pair_window_budget", 48)),
            logical_detector_pair_window_budget=int(grid.get("logical_detector_pair_window_budget", 48)),
            eval_window_plan_mode=grid.get("eval_window_plan_mode", "structured_higher_order"),
            eval_max_window_bits=int(grid.get("eval_max_window_bits", 6)),
            eval_max_windows=int(grid.get("eval_max_windows", 256)),
            eval_radius=float(grid.get("eval_radius", 1.0)),
            eval_template_window_budget=int(grid.get("eval_template_window_budget", 32)),
            eval_orbit_window_budget=int(grid.get("eval_orbit_window_budget", 64)),
        )
        train_config = _window_config(ns)
        eval_config = _eval_window_config(ns, train_config)
        train_windows = WindowPlan.from_config(graph, train_config)
        eval_windows = train_windows if train_config == eval_config else WindowPlan.from_config(graph, eval_config)
        return {
            "available": True,
            "representative_context": {
                "dataset_name": DATASET_SURFACE_SET1,
                "sample_id": sample_id,
                "patch_id": patch_id,
                "basis": basis,
                "rounds_label": rounds_label,
            },
            "train_window_audit": _window_plan_audit(graph, train_windows, preprocessing_mode=str(grid.get("orbit_mode")), role="train"),
            "eval_window_audit": _window_plan_audit(graph, eval_windows, preprocessing_mode=str(grid.get("orbit_mode")), role="eval"),
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _b0_checks(
    preprocessing_audit: dict[str, object],
    label_manifest: dict[str, object],
    eval_window_audit: dict[str, object],
    *,
    dataset_names: Iterable[str],
) -> dict[str, dict[str, object]]:
    datasets = preprocessing_audit.get("datasets", {})
    missing_roots = preprocessing_audit.get("missing_roots", {})
    inventory_matches = []
    for dataset_name in dataset_names:
        item = datasets.get(dataset_name, {}) if isinstance(datasets, dict) else {}
        inventory_matches.append(
            {
                "dataset_name": dataset_name,
                "expected": EXPECTED_LEAF_COUNTS.get(dataset_name),
                "observed": item.get("num_leaves"),
                "passed": bool(item.get("leaf_count_matches_observed_inventory")),
            }
        )
    label_layers = label_manifest.get("label_layers", {})
    forbidden_as_available = [
        label
        for group, values in label_layers.items()
        if group != "forbidden_true_labels"
        for label in (values if isinstance(values, list) else [])
        if label in FORBIDDEN_TRUE_LABELS
    ]
    eval_audit = eval_window_audit.get("eval_window_audit", {}) if isinstance(eval_window_audit, dict) else {}
    return {
        "expected_leaf_counts": {
            "passed": all(item["passed"] for item in inventory_matches) and not missing_roots,
            "value": inventory_matches,
            "missing_roots": missing_roots,
        },
        "forbidden_true_labels_absent": {
            "passed": not forbidden_as_available,
            "value": forbidden_as_available,
            "forbidden_true_labels": list(FORBIDDEN_TRUE_LABELS),
        },
        "gpu_only_path_configured": {
            "passed": True,
            "value": "--native-gpu is always passed by this suite for training/evaluation rungs",
        },
        "structured_eval_windows": {
            "passed": bool(eval_audit)
            and eval_audit.get("window_plan_mode") == "structured_higher_order"
            and int(eval_audit.get("max_window_bits", 0)) > 2,
            "value": {
                "available": bool(eval_window_audit.get("available")),
                "window_plan_mode": eval_audit.get("window_plan_mode"),
                "max_window_bits": eval_audit.get("max_window_bits"),
                "window_family_counts": eval_audit.get("window_family_counts"),
                "window_size_distribution": eval_audit.get("window_size_distribution"),
            },
        },
        "eval_metric_fields_declared": {
            "passed": True,
            "value": [
                "heldout_eval_window_nll",
                "heldout_eval_window_empirical_entropy",
                "heldout_eval_window_excess_nll",
            ],
        },
    }


def _normalise_records(records: Iterable[dict[str, object]], *, benchmark_id: str) -> list[dict[str, object]]:
    normalised = []
    for record in records:
        row = dict(record)
        row["benchmark_id"] = benchmark_id
        row["primary_metric"] = PRIMARY_METRIC
        row["primary_metric_value"] = row.get(PRIMARY_METRIC)
        row["dem_proxy_labels_available"] = row.get("dem_proxy_labels") not in (None, {}, "not available")
        if row.get("baseline_family") is None:
            row["baseline_family"] = _baseline_family(str(row.get("model", "")))
        if row.get("heldout_split_type") is None:
            row["heldout_split_type"] = "shot-heldout"
        normalised.append(row)
    return normalised


def _normalise_transfer_records(
    records: Iterable[dict[str, object]],
    *,
    source_sample_id: str,
    patch_id: str,
    basis: str,
    rounds_label: str,
) -> list[dict[str, object]]:
    result = []
    for record in records:
        row = dict(record)
        row.update(
            {
                "benchmark_id": "B3",
                "dataset_name": DATASET_SURFACE_SET1,
                "dataset_family": "surface",
                "context_id": google_context_id(
                    dataset_name=DATASET_SURFACE_SET1,
                    sample_id=str(row.get("sample_id")),
                    patch_id=patch_id,
                    basis=basis,
                    rounds_label=rounds_label,
                ),
                "source_sample_id": source_sample_id,
                "target_sample_id": row.get("sample_id"),
                "patch_id": patch_id,
                "basis": basis,
                "distance": _distance_from_patch(patch_id),
                "rounds_label": rounds_label,
                "heldout_split_type": "cross-sample-transfer",
                "primary_metric": PRIMARY_METRIC,
                "primary_metric_value": row.get(PRIMARY_METRIC),
                "baseline_family": _baseline_family(str(row.get("model", ""))),
            }
        )
        result.append(row)
    return result


def _context_scorecard(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for record in records:
        key = (
            record.get("dataset_name"),
            record.get("dataset_family"),
            record.get("context_id"),
            record.get("sample_id"),
            record.get("patch_id"),
            record.get("basis"),
            record.get("distance"),
            record.get("rounds_label"),
            record.get("decoder_pathway"),
            record.get("heldout_split_type"),
            record.get("train_shots"),
        )
        grouped.setdefault(key, []).append(record)
    rows = []
    for key, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
        best = _best_record(group)
        dmle = next((record for record in group if record.get("model") == "dmle_qec"), None)
        local = next((record for record in group if record.get("model") in {"local", "local_full"}), None)
        rows.append(
            {
                "dataset_name": key[0],
                "dataset_family": key[1],
                "context_id": key[2],
                "sample_id": key[3],
                "patch_id": key[4],
                "basis": key[5],
                "distance": key[6],
                "rounds_label": key[7],
                "decoder_pathway": key[8],
                "heldout_split_type": key[9],
                "train_shots": key[10],
                "primary_metric": PRIMARY_METRIC,
                "best_model": _compact_record(best),
                "dmle_qec": _compact_record(dmle),
                "local_full": _compact_record(local),
                "best_minus_dmle_qec": _metric_delta(best, dmle, PRIMARY_METRIC),
                "best_minus_local_full": _metric_delta(best, local, PRIMARY_METRIC),
                "physical_mechanism_recovery_claim_allowed": False,
            }
        )
    return rows


def _paired_baseline_comparison(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for record in records:
        key = (
            record.get("dataset_name"),
            record.get("context_id"),
            record.get("sample_id"),
            record.get("patch_id"),
            record.get("basis"),
            record.get("distance"),
            record.get("rounds_label"),
            record.get("decoder_pathway"),
            record.get("heldout_split_type"),
            record.get("train_shots"),
        )
        grouped.setdefault(key, []).append(record)
    rows = []
    for key, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
        local = next((record for record in group if record.get("model") in {"local", "local_full"}), None)
        dmle = next((record for record in group if record.get("model") == "dmle_qec"), None)
        for record in sorted(group, key=lambda item: str(item.get("model"))):
            rows.append(
                {
                    "dataset_name": key[0],
                    "context_id": key[1],
                    "sample_id": key[2],
                    "patch_id": key[3],
                    "basis": key[4],
                    "distance": key[5],
                    "rounds_label": key[6],
                    "decoder_pathway": key[7],
                    "heldout_split_type": key[8],
                    "train_shots": key[9],
                    "model": record.get("model"),
                    "baseline_family": record.get("baseline_family"),
                    "primary_metric": PRIMARY_METRIC,
                    "primary_metric_value": record.get(PRIMARY_METRIC),
                    "delta_vs_dmle_qec": _metric_delta(record, dmle, PRIMARY_METRIC),
                    "delta_vs_local_full": _metric_delta(record, local, PRIMARY_METRIC),
                    "detector_mae_delta_vs_dmle_qec": _metric_delta(record, dmle, "detector_rate_mae"),
                    "logical_calibration_delta_vs_dmle_qec": _metric_delta(record, dmle, "logical_flip_rate_calibration"),
                    "random_control": "random_low_rank" in str(record.get("model", "")),
                }
            )
    return rows


def _sample_efficiency_summary(records: list[dict[str, object]], *, train_shots: list[int]) -> dict[str, object]:
    rows = []
    by_model_shot: dict[tuple[str, int], list[dict[str, object]]] = {}
    for record in records:
        shot = record.get("train_shots")
        if shot is None:
            continue
        by_model_shot.setdefault((str(record.get("model")), int(shot)), []).append(record)
    for (model, shot), group in sorted(by_model_shot.items(), key=lambda item: (item[0][0], item[0][1])):
        rows.append(
            {
                "model": model,
                "train_shots": shot,
                "n": len(group),
                "heldout_eval_window_excess_nll_mean": _mean([row.get(PRIMARY_METRIC) for row in group]),
                "detector_rate_mae_mean": _mean([row.get("detector_rate_mae") for row in group]),
                "logical_flip_calibration_mean": _mean([row.get("logical_flip_rate_calibration") for row in group]),
                "local_correlation_error_mean": _mean([row.get("local_correlation_error") for row in group]),
            }
        )
    dmle_4096 = next(
        (
            row["heldout_eval_window_excess_nll_mean"]
            for row in rows
            if row["model"] == "dmle_qec" and row["train_shots"] == 4096
        ),
        None,
    )
    curves = []
    for model in sorted({row["model"] for row in rows}):
        model_rows = sorted([row for row in rows if row["model"] == model], key=lambda row: row["train_shots"])
        first_match = None
        if dmle_4096 is not None:
            for row in model_rows:
                value = row.get("heldout_eval_window_excess_nll_mean")
                if value is not None and float(value) <= float(dmle_4096):
                    first_match = row["train_shots"]
                    break
        curves.append(
            {
                "model": model,
                "shots_to_match_dmle_4096_quality": first_match,
                "area_under_learning_curve_log2_shots": _auc_log2(
                    [(row["train_shots"], row.get("heldout_eval_window_excess_nll_mean")) for row in model_rows]
                ),
            }
        )
    return {
        "primary_metric": PRIMARY_METRIC,
        "train_shot_grid": train_shots,
        "dmle_4096_reference": dmle_4096,
        "rows": rows,
        "curves": curves,
    }


def _transfer_scorecard(records: list[dict[str, object]]) -> dict[str, object]:
    by_model: dict[str, list[dict[str, object]]] = {}
    for record in records:
        by_model.setdefault(str(record.get("model")), []).append(record)
    return {
        "benchmark_id": "B3",
        "primary_metric": PRIMARY_METRIC,
        "source_fit_transfer_mode": "single_source_fit",
        "pooled_source_training": False,
        "target_fit_dmle_upper_comparator_available": False,
        "model_summary": [
            {
                "model": model,
                "n": len(rows),
                "transfer_evaluated": sum(1 for row in rows if bool(row.get("transfer_evaluated", True))),
                "heldout_eval_window_excess_nll_mean": _mean([row.get(PRIMARY_METRIC) for row in rows]),
                "detector_rate_mae_mean": _mean([row.get("detector_rate_mae") for row in rows]),
                "logical_flip_calibration_mean": _mean([row.get("logical_flip_rate_calibration") for row in rows]),
            }
            for model, rows in sorted(by_model.items())
        ],
        "records": records,
    }


def _collect_grid_eval_window_audits(completed_contexts: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    audits = []
    for context in completed_contexts:
        output_root = context.get("output_root")
        if not output_root:
            continue
        metrics_path = Path(str(output_root)) / "GDISC15_real_local_mechanism_discovery" / "metrics.json"
        try:
            metrics = _read_json(metrics_path)
        except Exception as exc:
            audits.append({"context_id": context.get("context_id"), "available": False, "error": str(exc)})
            continue
        audits.append(
            {
                "context_id": context.get("context_id"),
                "available": True,
                "window_audit": metrics.get("window_audit"),
                "eval_window_audit": _nested_get(metrics, ["window_audit", "eval_window_audit"]),
            }
        )
    return audits


def _write_common_benchmark_artifacts(
    output: Path,
    *,
    run_manifest: dict[str, object],
    grid_result: dict[str, object],
    flat_records: list[dict[str, object]],
    context_scorecard: list[dict[str, object]],
    paired_baseline_comparison: list[dict[str, object]],
    eval_window_audit: dict[str, object] | list[dict[str, object]],
) -> None:
    _write_json(output / "run_manifest.json", run_manifest)
    _write_json(output / "context_selection.json", grid_result.get("grid", {}))
    _write_json(output / "decoder_selection.json", _decoder_selection(flat_records))
    _write_json(output / "preprocessing_audit.json", _preprocessing_summary(flat_records))
    _write_json(output / "eval_window_audit.json", eval_window_audit)
    _write_json(output / "model_summary.json", grid_result.get("model_summary", _model_summary(flat_records)))
    _write_json(output / "context_scorecard.json", context_scorecard)
    _write_json(output / "paired_baseline_comparison.json", paired_baseline_comparison)
    (output / "summary.md").write_text(_benchmark_summary(run_manifest, context_scorecard), encoding="utf-8")


def _decoder_selection(records: list[dict[str, object]]) -> dict[str, object]:
    counts = Counter(str(record.get("decoder_pathway")) for record in records if record.get("decoder_pathway"))
    return {
        "decoder_pathway_counts": dict(sorted(counts.items())),
        "decoder_pathways": sorted(counts),
    }


def _preprocessing_summary(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "num_records": len(records),
        "dem_proxy_labels_available_records": sum(1 for record in records if record.get("dem_proxy_labels_available")),
        "forbidden_true_labels_absent": True,
        "forbidden_true_labels": list(FORBIDDEN_TRUE_LABELS),
    }


def _model_summary(records: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for record in records:
        grouped.setdefault(str(record.get("model")), []).append(record)
    result = []
    for model, rows in sorted(grouped.items()):
        item = {
            "model": model,
            "n": len(rows),
            "parameter_count_mean": _mean([row.get("parameter_count") for row in rows]),
            "heldout_eval_window_excess_nll_mean": _mean([row.get(PRIMARY_METRIC) for row in rows]),
            "detector_rate_mae_mean": _mean([row.get("detector_rate_mae") for row in rows]),
            "logical_flip_calibration_mean": _mean([row.get("logical_flip_rate_calibration") for row in rows]),
        }
        for metric in SUMMARY_METRICS:
            item[f"{metric}_mean"] = _mean([row.get(metric) for row in rows])
        result.append(item)
    return result


def _selected_benchmarks(value: object) -> list[str]:
    selected = [item.upper() for item in _csv(value)]
    if any(item in {"ALL", "*"} for item in selected):
        return list(BENCHMARK_ORDER)
    unknown = [item for item in selected if item not in BENCHMARK_ORDER]
    if unknown:
        raise ValueError(f"unknown benchmarks: {unknown}")
    return [item for item in BENCHMARK_ORDER if item in selected]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    path = Path(config_path)
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Google benchmark suite config must be a mapping")
    section = data.get("google_benchmark_suite_v1", data)
    if not isinstance(section, dict):
        raise ValueError("google_benchmark_suite_v1 config section must be a mapping")
    return dict(section)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Google Benchmark Suite V1.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--benchmarks",
        default=None,
        help="Comma-separated benchmark IDs to run. Use all for B0-B6. Config default is used when omitted.",
    )
    return parser.parse_args(argv)


def _benchmark_ref(benchmark_id: str, output: Path, result: dict[str, object]) -> dict[str, object]:
    return {
        "benchmark_id": benchmark_id,
        "output_dir": str(output),
        "summary_path": str(output / "summary.md"),
        "run_manifest_path": str(output / "run_manifest.json"),
        "result": _jsonable(result),
    }


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
        "baseline_family",
        "baseline_variant",
        "primary_metric",
        "primary_metric_value",
        "heldout_eval_window_nll",
        "heldout_eval_window_empirical_entropy",
        "heldout_eval_window_excess_nll",
        "heldout_local_window_nll",
        "heldout_local_window_excess_nll",
        "detector_rate_mae",
        "local_correlation_error",
        "logical_flip_rate_calibration",
    ]
    return {key: record.get(key) for key in keys}


def _metric_delta(left: dict[str, object] | None, right: dict[str, object] | None, metric: str) -> float | None:
    if left is None or right is None or left.get(metric) is None or right.get(metric) is None:
        return None
    return float(left[metric]) - float(right[metric])


def _baseline_family(model: str) -> str:
    if model in {"dmle_qec", "dmle_qec_upstream"}:
        return "dmle_qec"
    if model in BASELINE_MODELS or model.endswith("_prior_reference"):
        return "baseline"
    if "random_low_rank" in model:
        return "random_control"
    return "scope_structured"


def _auc_log2(points: list[tuple[int, object]]) -> float | None:
    clean = [(int(x), float(y)) for x, y in points if y is not None and int(x) > 0]
    if len(clean) < 2:
        return None
    clean.sort()
    area = 0.0
    for (x0, y0), (x1, y1) in zip(clean, clean[1:]):
        lx0 = np.log2(float(x0))
        lx1 = np.log2(float(x1))
        area += 0.5 * (y0 + y1) * (lx1 - lx0)
    return float(area)


def _b0_summary(audit_lock: dict[str, object]) -> str:
    lines = [
        "# B0 Audit Lock",
        "",
        f"- Passed: `{str(audit_lock['passed']).lower()}`",
        f"- Contexts: `{audit_lock['inventory']['num_contexts']}`",
        f"- Decoder rows: `{audit_lock['inventory']['num_decoder_rows']}`",
        "",
        "| check | passed | value |",
        "| --- | ---: | --- |",
    ]
    for name, item in audit_lock["checks"].items():
        lines.append(f"| {name} | `{str(item['passed']).lower()}` | `{_short_json(item.get('value'))}` |")
    lines.append("")
    return "\n".join(lines)


def _benchmark_summary(run_manifest: dict[str, object], context_scorecard: list[dict[str, object]]) -> str:
    lines = [
        f"# {run_manifest.get('benchmark_id')} Google Benchmark",
        "",
        f"- Primary metric: `{run_manifest.get('primary_metric', PRIMARY_METRIC)}`",
        f"- Context rows: `{len(context_scorecard)}`",
        f"- Physical mechanism recovery claim: `false`",
        "",
        CLAIM_BOUNDARY,
        "",
        "| context | best model | metric | delta vs dMLE |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in context_scorecard[:50]:
        best = row.get("best_model") if isinstance(row.get("best_model"), dict) else {}
        context = row.get("context_id") or "__".join(str(row.get(key)) for key in ["sample_id", "patch_id", "basis", "rounds_label"])
        lines.append(
            f"| {context} | {best.get('model')} | "
            f"{_fmt_float(best.get(PRIMARY_METRIC) or best.get('primary_metric_value'))} | "
            f"{_fmt_float(row.get('best_minus_dmle_qec'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def _pending_summary(scorecard: dict[str, object]) -> str:
    return "\n".join(
        [
            f"# {scorecard['benchmark_id']} Pending",
            "",
            f"- Dataset: `{scorecard['dataset_name']}`",
            f"- Reason: {scorecard['pending_reason']}",
            f"- Manifest contexts: `{scorecard['context_count_from_manifest']}`",
            "",
            CLAIM_BOUNDARY,
            "",
        ]
    )


def _suite_summary(result: dict[str, object]) -> str:
    lines = [
        "# Google Benchmark Suite V1",
        "",
        CLAIM_BOUNDARY,
        "",
        "| benchmark | output |",
        "| --- | --- |",
    ]
    for benchmark_id, item in result["benchmarks"].items():
        lines.append(f"| {benchmark_id} | `{item['summary_path']}` |")
    lines.append("")
    return "\n".join(lines)


def _mapping(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("config section must be a mapping")
    return dict(value)


def _csv(value: object) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _csv_ints(value: object) -> list[int]:
    return [int(item) for item in _csv(value)]


def _first_csv(value: object) -> str:
    values = _csv(value)
    if not values:
        raise ValueError("expected at least one CSV value")
    return values[0]


def _distance_from_patch(patch_id: object) -> int | None:
    text = str(patch_id or "")
    if text.startswith("d3_"):
        return 3
    if text.startswith("d5_"):
        return 5
    if text.startswith("d7_"):
        return 7
    return None


def _mean(values: Iterable[object]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    return float(sum(numbers) / len(numbers)) if numbers else None


def _std(values: Iterable[object]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return None
    if len(numbers) == 1:
        return 0.0
    return float(statistics.stdev(numbers))


def _none_high(value: object) -> float:
    return float(value) if value is not None else float("inf")


def _nested_get(value: dict[str, object], keys: list[str]) -> object | None:
    current: object = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _read_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _short_json(value: object, limit: int = 120) -> str:
    text = json.dumps(_jsonable(value), sort_keys=True)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


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

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import torch

from scope_static.discovery import discovery_parameter_audit, field_discovery_metrics, is_discovery_model
from scope_static.fault_graph import FaultGraph
from scope_static.fields import make_field
from scope_static.google_set1 import (
    CLAIM_BOUNDARY,
    build_google_fault_graph,
    build_google_schedule_context,
    find_google_set1_leaf,
    load_google_dem_data,
    load_google_observations,
    load_google_predicted_observables,
)
from scope_static.likelihood import (
    WindowBatchNLLCache,
    WindowNLLCache,
    build_window_batch_nll_cache,
    build_window_batch_nll_cache_from_observations,
    build_window_nll_caches,
    exact_dem_nll,
    local_window_exact_nll,
)
from scope_static.likelihoods.local_window_parity import ExactLocalWindowParityLikelihood
from scope_static.metrics import (
    augment_model_comparison_metrics,
    augment_transfer_comparison_metrics,
    compression_audit,
    compression_ratio,
    evaluate_real_data_model,
)
from scope_static.objectives import LikelihoodObjective, build_likelihood_objective
from scope_static.prepared_graph_store import (
    load_prepared_fault_graph_cache,
    prepared_fault_graph_cache_file,
    prepared_fault_graph_cache_key,
    save_prepared_fault_graph_cache,
)
from scope_static.training import fit_field
from scope_static.window_cache_store import (
    load_window_batch_cache,
    save_window_batch_cache,
    window_batch_cache_file,
    window_batch_cache_key,
)
from scope_static.windows import ObservationWindow, WindowPlan, detector_only_windows, window_coverage_audit_dict


PreparedEvalCache = tuple[list[WindowNLLCache], WindowBatchNLLCache | None]


def main(argv: list[str] | None = None) -> dict[str, object]:
    run_start = time.perf_counter()
    args = _parse_args(argv)
    _resolve_execution_mode(args)
    dataset_root = args.dataset_root or os.environ.get(
        "SCOPE_GOOGLE_SET1_ROOT",
        "/home/cx/Document/google_72Q_surface_code_d3_d5_set1",
    )
    leaf = find_google_set1_leaf(
        dataset_root,
        sample_id=args.sample_id,
        patch_id=args.patch_id,
        basis=args.basis,
        rounds_label=args.rounds_label,
    )
    observations = load_google_observations(leaf)
    split = _train_heldout_split(observations.shape[0], args.train_shots, args.heldout_shots)
    train_observations = observations[split["train_slice"]]
    heldout_observations = observations[split["heldout_slice"]]
    predicted = load_google_predicted_observables(leaf, args.dem_source)
    heldout_predicted = None if predicted is None else predicted[split["heldout_slice"]]
    schedule_context = build_google_schedule_context(
        leaf,
        dem_source=args.dem_source,
        observations=observations,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    args.prepared_cache_dir = str(Path(args.prepared_cache_dir) if args.prepared_cache_dir else output_dir / "prepared_cache")
    records: list[dict[str, object]] = []
    graph_audits: list[dict[str, object]] = []
    window_audits: list[dict[str, object]] = []
    transfer_records: list[dict[str, object]] = []
    transfer_cache: dict[tuple[str, str], dict[str, object]] = {}
    prepared_cache_events: list[dict[str, object]] = []
    dem_data_cache: dict[str, object] = {}
    dtype = torch.float64 if args.dtype == "float64" else torch.float32
    model_names = _csv(args.models)
    required_observation_modes = {"detectors" if model == "dmle_qec" else "full" for model in model_names}

    for orbit_mode in _csv(args.orbit_modes):
        prepare_start = time.perf_counter()
        graph, preprocessing_audit = _prepare_google_fault_graph(
            args,
            leaf,
            orbit_mode=orbit_mode,
            schedule_context=schedule_context,
            dem_data_cache=dem_data_cache,
            cache_events=prepared_cache_events,
        )
        windows = WindowPlan.from_config(graph, _window_config(args))
        train_objectives = _prepare_train_objectives(
            args,
            leaf,
            graph,
            train_observations,
            windows,
            orbit_mode=orbit_mode,
            split=split,
            observation_modes=required_observation_modes,
            cache_events=prepared_cache_events,
        )
        heldout_eval_cache = _prepare_eval_cache(
            args,
            leaf,
            graph,
            heldout_observations,
            windows,
            orbit_mode=orbit_mode,
            role="heldout_eval",
            slice_start=int(split["heldout_start"]),
            slice_end=int(split["heldout_end"]),
            cache_events=prepared_cache_events,
        )
        graph_audit = graph.audit_dict(
            exact_likelihood_trainable=False,
            dem_fault_logit_claim=True,
            cptp_gksl_claim=False,
        )
        graph_audit.update(preprocessing_audit)
        graph_audit.update(compression_audit(graph))
        graph_audits.append(graph_audit)

        window_audit = window_coverage_audit_dict(graph, list(windows.windows))
        window_audit.update(windows.audit_dict())
        window_audit["preprocessing_mode"] = orbit_mode
        window_audits.append(window_audit)
        _emit_progress_event(
            args,
            {
                "event": "prepared_preprocessing",
                "preprocessing_mode": orbit_mode,
                "num_windows": len(windows),
                "prepare_wall_seconds": time.perf_counter() - prepare_start,
            },
        )

        for model_name in model_names:
            prototype_counts = _google_prototype_counts(args, graph, model_name)
            for prototype_count in prototype_counts:
                model_options = _google_model_options(args, model_name, prototype_count)
                model_label = _google_model_label(model_name, prototype_count, prototype_counts)
                fit_start = time.perf_counter()
                _emit_progress_event(
                    args,
                    {
                        "event": "start_fit",
                        "preprocessing_mode": orbit_mode,
                        "model": model_label,
                        "device": args.device,
                        "likelihood_backend": args.likelihood_backend,
                        "cuda_kernel_variant": args.cuda_kernel_variant,
                    },
                )
                observation_mode = "detectors" if model_name == "dmle_qec" else "full"
                if is_discovery_model(model_name):
                    selected = _fit_google_discovery_restarts(
                        args,
                        graph,
                        model_name=model_name,
                        model_options=model_options,
                        train_observations=train_observations,
                        train_objective=train_objectives[observation_mode],
                        windows=windows,
                        dtype=dtype,
                        observation_mode=observation_mode,
                    )
                    fit = selected["fit"]
                    restart_outcomes = selected["restart_outcomes"]
                else:
                    seed = int(args.seed)
                    torch.manual_seed(seed)
                    field = make_field(model_name, graph, dtype=dtype, seed=seed, model_options=model_options)
                    fit = fit_field(
                        graph,
                        field,
                        train_observations,
                        steps=args.steps,
                        lr=args.lr,
                        aggregate_unique=True,
                        device=args.device,
                        backend=args.likelihood_backend,
                        cuda_kernel_variant=args.cuda_kernel_variant,
                        spectral_min_abs_factor=args.spectral_min_abs_factor,
                        spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
                        observation_mode=observation_mode,
                        likelihood_objective="local_exact",
                        windows=windows,
                        prepared_objective=train_objectives[observation_mode],
                    )
                    restart_outcomes = []
                fit_seconds = time.perf_counter() - fit_start
                trained_field = fit["field"]
                logits = trained_field.realized_logits(graph).detach()
                eval_start = time.perf_counter()
                metrics = evaluate_real_data_model(
                    graph,
                    logits,
                    heldout_observations,
                    aggregate_unique=True,
                    backend=args.likelihood_backend,
                    windows=list(windows.windows),
                    window_caches=heldout_eval_cache[0],
                    window_batch_cache=heldout_eval_cache[1],
                    predicted_observables=heldout_predicted,
                )
                if is_discovery_model(model_name):
                    metrics.update(
                        field_discovery_metrics(
                            trained_field,
                            None,
                            active_mass_threshold=float(args.discovery_active_mass_threshold),
                        )
                    )
                    metrics.update(
                        {
                            "stage": "stage2B_google_external_validation",
                            "google_true_hidden_partition_available": False,
                            "partition_recovery_claim_allowed": False,
                            "discovery_num_restarts": int(args.discovery_restarts),
                            "discovery_selected_restart_index": int(fit["selected_restart_index"]),
                            "discovery_restart_selection_metric": "train_final_nll",
                            "discovery_restart_outcomes": restart_outcomes,
                        }
                    )
                eval_seconds = time.perf_counter() - eval_start
                parameter_count = int(trained_field.parameter_count)
                record = _record(
                    args=args,
                    leaf=leaf,
                    graph=graph,
                    model_name=model_label,
                    orbit_mode=orbit_mode,
                    split=split,
                    fit=fit,
                    metrics=metrics,
                    preprocessing_audit=preprocessing_audit,
                    parameter_count=parameter_count,
                    fit_wall_seconds=fit_seconds,
                    eval_wall_seconds=eval_seconds,
                    base_model_name=model_name,
                    prototype_count=prototype_count,
                )
                if is_discovery_model(model_name) and prototype_count is not None:
                    record.update(
                        discovery_parameter_audit(
                            graph,
                            model_name=model_name,
                            prototype_count=int(prototype_count),
                            residual_rank=int(graph.residual_rank),
                        )
                    )
                records.append(record)
                _emit_progress_event(
                    args,
                    {
                        "event": "finish_fit",
                        "preprocessing_mode": orbit_mode,
                        "model": model_label,
                        "fit_wall_seconds": fit_seconds,
                        "eval_wall_seconds": eval_seconds,
                        "heldout_local_window_nll": metrics.get("heldout_local_window_nll"),
                        "heldout_local_window_excess_nll": metrics.get("heldout_local_window_excess_nll"),
                        "adapter": fit.get("likelihood_adapter"),
                    },
                )
                if args.cross_sample_transfer:
                    transfer_start = time.perf_counter()
                    transfer_records.extend(
                        _cross_sample_transfer(
                            args=args,
                            source_leaf=leaf,
                            source_graph=graph,
                            logits=logits,
                            windows=windows,
                            model_name=model_label,
                            orbit_mode=orbit_mode,
                            transfer_cache=transfer_cache,
                            cache_events=prepared_cache_events,
                            base_model_name=model_name,
                            prototype_count=prototype_count,
                        )
                    )
                    _emit_progress_event(
                        args,
                        {
                            "event": "finish_transfer",
                            "preprocessing_mode": orbit_mode,
                            "model": model_label,
                            "transfer_wall_seconds": time.perf_counter() - transfer_start,
                            "num_target_samples": int(args.cross_sample_stop) - int(args.cross_sample_start) + 1,
                        },
                    )
    augment_model_comparison_metrics(records, baseline_model="local")
    augment_transfer_comparison_metrics(transfer_records, baseline_model="local")

    result = {
        "run": {
            "name": "Google 72Q Set1 logical-aware static/discovery validation"
            if any(is_discovery_model(model) for model in model_names)
            else "S1.7 Google 72Q Set1 logical-aware window ablation",
            "stage2b_google_discovery_external_validation": any(is_discovery_model(model) for model in model_names),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_root": str(leaf.root),
            "default_leaf": {
                "sample_id": leaf.sample_id,
                "patch_id": leaf.patch_id,
                "basis": leaf.basis,
                "rounds_label": leaf.rounds_label,
            },
            "dem_source": args.dem_source,
            "device": args.device,
            "likelihood_backend": args.likelihood_backend,
            "cuda_kernel_variant": args.cuda_kernel_variant,
            "spectral_min_abs_factor": float(args.spectral_min_abs_factor),
            "spectral_memory_cap_bytes": _spectral_memory_cap_bytes(args),
            "window_plan_mode": args.window_plan_mode,
            "native_gpu": bool(args.native_gpu),
            "gpu_policy": args.gpu_policy,
            "prepared_cache": {
                "enabled": not bool(args.disable_prepared_cache),
                "dir": args.prepared_cache_dir,
            },
            "wall_seconds": time.perf_counter() - run_start,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        "train_heldout_split": _json_split(split),
        "schedule_context_audit": schedule_context.audit_dict(),
        "graph_audits": graph_audits,
        "window_audits": window_audits,
        "micro_window_global_validation": _micro_window_global_validation(args.likelihood_backend),
        "records": records,
        "cross_sample_transfer_records": transfer_records,
        "prepared_cache_events": prepared_cache_events,
    }
    result["decision"] = _decision_summary(records)
    metrics_path = output_dir / "google_static_metrics.json"
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(_jsonable(result), handle, indent=2, sort_keys=True)
        handle.write("\n")
    if args.progress_json:
        print(json.dumps({"metrics_path": str(metrics_path), "num_records": len(records)}, sort_keys=True))
    else:
        _print_final_summary(result, metrics_path)
    return result


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=None)
    parser.add_argument("--sample-id", default="sample_00")
    parser.add_argument("--patch-id", default="d3_at_q5_5")
    parser.add_argument("--basis", default="X")
    parser.add_argument("--rounds-label", default="r13")
    parser.add_argument("--dem-source", default="decoder_si1000")
    parser.add_argument("--orbit-modes", default="fault_graph_heuristic,schedule_geometric")
    parser.add_argument("--models", default="local,dmle_qec,hard_orbit,soft_feature_orbit")
    parser.add_argument("--train-shots", type=int, default=40000)
    parser.add_argument("--heldout-shots", type=int, default=10000)
    parser.add_argument("--max-window-bits", type=int, default=8)
    parser.add_argument("--max-windows", type=int, default=128)
    parser.add_argument(
        "--window-plan-mode",
        choices=["logical_aware", "detector_local"],
        default="logical_aware",
    )
    parser.add_argument("--detector-pair-window-budget", type=int, default=64)
    parser.add_argument("--logical-detector-pair-window-budget", type=int, default=64)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--residual-rank", type=int, default=2)
    parser.add_argument(
        "--discovery-prototype-counts",
        default="O",
        help="Comma-separated K values for disc_hard/disc_soft on Google data; use O for graph.O.",
    )
    parser.add_argument("--discovery-restarts", type=int, default=4)
    parser.add_argument("--discovery-active-mass-threshold", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", choices=["float64", "float32"], default="float64")
    parser.add_argument("--likelihood-backend", choices=["auto", "pytorch", "cuda_extension"], default="auto")
    parser.add_argument(
        "--cuda-kernel-variant",
        choices=["dp", "spectral_shadow", "spectral", "auto"],
        default="auto",
    )
    parser.add_argument("--spectral-min-abs-factor", type=float, default=1e-6)
    parser.add_argument("--spectral-memory-cap-mib", type=int, default=1024)
    parser.add_argument(
        "--native-gpu",
        action="store_true",
        help="Require CUDA and use the C++/CUDA local-window likelihood backend.",
    )
    parser.add_argument(
        "--allow-cpu-fallback",
        action="store_true",
        help="Explicitly allow CPU/PyTorch execution when CUDA is not visible.",
    )
    parser.add_argument("--output-dir", default="outputs/google_static/S1_7_logical_aware")
    parser.add_argument("--prepared-cache-dir", default=None)
    parser.add_argument("--disable-prepared-cache", action="store_true")
    parser.add_argument("--cross-sample-transfer", dest="cross_sample_transfer", action="store_true", default=False)
    parser.add_argument("--skip-cross-sample-transfer", dest="cross_sample_transfer", action="store_false")
    parser.add_argument("--cross-sample-start", type=int, default=1)
    parser.add_argument("--cross-sample-stop", type=int, default=20)
    parser.add_argument(
        "--progress-json",
        action="store_true",
        help="Emit per-stage JSON progress events instead of only a concise final summary.",
    )
    return parser.parse_args(argv)


def _emit_progress_event(args: argparse.Namespace, event: dict[str, object]) -> None:
    if bool(getattr(args, "progress_json", False)):
        print(json.dumps(event, sort_keys=True), flush=True)


def _print_final_summary(result: dict[str, object], metrics_path: Path) -> None:
    run = result.get("run", {})
    records = list(result.get("records", []))
    transfers = list(result.get("cross_sample_transfer_records", []))
    window_audits = list(result.get("window_audits", []))
    if run.get("stage2b_google_discovery_external_validation"):
        print("S2B Google static discovery validation complete")
    else:
        print("S1.7 Google static complete")
    print(f"metrics: {metrics_path}")
    print(
        "run: "
        f"device={run.get('device')} backend={run.get('likelihood_backend')} "
        f"kernel={run.get('cuda_kernel_variant')} window_plan={run.get('window_plan_mode')} "
        f"wall={_fmt_seconds(run.get('wall_seconds'))}"
    )
    if window_audits:
        print("")
        print("Window Coverage")
        for audit in window_audits:
            coverage = audit.get("detector_logical_bit_coverage", {})
            logical = audit.get("logical_bit_coverage", {})
            family_counts = audit.get("window_family_counts", audit.get("window_type_counts", {}))
            print(
                "  "
                f"{audit.get('preprocessing_mode')}: "
                f"windows={audit.get('num_windows')} max_bits={audit.get('max_window_bits')} "
                f"bits={coverage.get('num_bits_covered')}/{coverage.get('num_bits_total')} "
                f"logical_bits={logical.get('num_logical_bits_covered')}/{logical.get('num_logical_bits_total')} "
                f"logical_windows={audit.get('num_windows_containing_logical', 0)} "
                f"logical_support={audit.get('logical_fault_support_selected', 0)}/"
                f"{audit.get('logical_fault_support_unique', 0)} "
                f"families={_compact_counts(family_counts)}"
            )

    print("")
    print("Heldout Model Comparison")
    _print_table(
        [
            "preprocess",
            "model",
            "K",
            "params",
            "comp",
            "ex_mn",
            "d_mn",
            "d_bit/shot",
            "log_d_mn",
            "log_cal",
            "det_mae",
            "ent",
            "active",
            "pareto",
        ],
        [
            [
                record.get("preprocessing_mode"),
                record.get("model"),
                record.get("prototype_count_K"),
                record.get("parameter_count"),
                _fmt_float(record.get("compression_ratio"), precision=2),
                _fmt_float(record.get("excess_mnats_per_window")),
                _fmt_signed_float(record.get("excess_delta_mnats_vs_baseline")),
                _fmt_signed_float(record.get("pseudo_delta_bits_per_shot_vs_baseline")),
                _fmt_signed_float(record.get("logical_excess_delta_mnats_vs_baseline")),
                _fmt_float(record.get("logical_flip_rate_calibration")),
                _fmt_float(record.get("detector_rate_mae")),
                _fmt_float(record.get("assignment_entropy_normalized")),
                record.get("num_active_prototypes"),
                record.get("combined_excess_parameter_pareto_status"),
            ]
            for record in records
        ],
    )
    print(
        "  units: ex_mn=1000*excess nats/window; d_mn and d_bit/shot are deltas vs local baseline; "
        "pareto uses combined excess and parameter count; discovery ARI/NMI unavailable on Google real data."
    )

    if transfers:
        print("")
        print("Cross-Sample Transfer Means")
        transfer_rows = []
        for mode, model, rows in _group_transfer_records(transfers):
            transfer_rows.append(
                [
                    mode,
                    model,
                    len(rows),
                    _fmt_float(_mean_metric(rows, "cross_sample_excess_mnats_per_window")),
                    _fmt_signed_float(_mean_metric(rows, "cross_sample_excess_delta_mnats_vs_baseline")),
                    _fmt_signed_float(_mean_metric(rows, "cross_sample_pseudo_delta_bits_per_shot_vs_baseline")),
                    _fmt_signed_float(_mean_metric(rows, "cross_sample_logical_excess_delta_mnats_vs_baseline")),
                    _fmt_float(_mean_metric(rows, "cross_sample_logical_flip_calibration")),
                    _fmt_float(_mean_metric(rows, "cross_sample_detector_rate_MAE")),
                ]
            )
        _print_table(
            ["preprocess", "model", "n", "ex_mn", "d_mn", "d_bit/shot", "log_d_mn", "log_cal", "det_mae"],
            transfer_rows,
        )
        print("  units: transfer means use the same local-baseline deltas per target sample.")

    decision = result.get("decision", {})
    per_model = decision.get("per_model", []) if isinstance(decision, dict) else []
    if per_model:
        statuses = sorted({str(item.get("schedule_symmetry_status")) for item in per_model})
        useful = any(bool(item.get("schedule_geometric_useful")) for item in per_model)
        print("")
        print(
            "Decision: "
            f"schedule_geometric_useful={useful} "
            f"schedule_symmetry_status={','.join(statuses)}"
        )


def _print_table(headers: list[str], rows: list[list[object]]) -> None:
    if not rows:
        print("  (none)")
        return
    string_rows = [[_cell(value) for value in row] for row in rows]
    widths = [
        max(len(headers[col]), *(len(row[col]) for row in string_rows))
        for col in range(len(headers))
    ]
    header = "  " + "  ".join(headers[col].ljust(widths[col]) for col in range(len(headers)))
    print(header)
    print("  " + "  ".join("-" * width for width in widths))
    for row in string_rows:
        print("  " + "  ".join(row[col].ljust(widths[col]) for col in range(len(headers))))


def _group_transfer_records(records: list[dict[str, object]]) -> list[tuple[str, str, list[dict[str, object]]]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = {}
    for record in records:
        if not bool(record.get("transfer_evaluated", True)):
            continue
        key = (str(record.get("preprocessing_mode")), str(record.get("model")))
        groups.setdefault(key, []).append(record)
    return [(mode, model, groups[(mode, model)]) for mode, model in sorted(groups)]


def _mean_metric(records: list[dict[str, object]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return sum(values) / len(values) if values else None


def _fmt_float(value: object, *, precision: int = 4) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) >= 100:
        return f"{number:.2f}"
    if abs(number) >= 10:
        return f"{number:.3f}"
    return f"{number:.{precision}g}"


def _fmt_signed_float(value: object, *, precision: int = 4) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) < 10 ** (-(precision + 1)):
        return "0"
    return f"{number:+.{precision}g}"


def _fmt_seconds(value: object) -> str:
    if value is None:
        return "-"
    return f"{float(value):.2f}s"


def _compact_counts(counts: object) -> str:
    if not isinstance(counts, dict):
        return "{}"
    return ",".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _cell(value: object) -> str:
    if value is None:
        return "-"
    return str(value)


def _resolve_execution_mode(args: argparse.Namespace) -> None:
    if args.native_gpu:
        if not torch.cuda.is_available():
            raise RuntimeError("native GPU requested, but torch.cuda.is_available() is false")
        args.device = "cuda"
        args.likelihood_backend = "cuda_extension"
        args.gpu_policy = "native_gpu_required"
        return

    requested_device = str(args.device)
    if requested_device == "auto":
        if torch.cuda.is_available():
            args.device = "cuda"
            if args.likelihood_backend == "auto":
                args.likelihood_backend = "cuda_extension"
            args.gpu_policy = "gpu_first_auto_cuda"
            return
        if args.allow_cpu_fallback:
            args.device = "cpu"
            if args.likelihood_backend == "auto":
                args.likelihood_backend = "pytorch"
            args.gpu_policy = "cpu_fallback_explicit"
            return
        raise RuntimeError(
            "GPU-first Google run could not see CUDA. The target workstation is assumed to have at least "
            "an RTX 5090-class CUDA device; fix CUDA visibility or pass --allow-cpu-fallback for an explicit CPU run."
        )

    if requested_device == "cpu":
        if not args.allow_cpu_fallback:
            raise RuntimeError("GPU-first Google run requires --allow-cpu-fallback for explicit CPU execution")
        if args.likelihood_backend == "auto":
            args.likelihood_backend = "pytorch"
        args.gpu_policy = "cpu_fallback_explicit"
        return

    if requested_device.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError("run.device requests CUDA, but torch.cuda.is_available() is false")
        if args.likelihood_backend == "auto":
            args.likelihood_backend = "cuda_extension"
        args.gpu_policy = "cuda_device_explicit"
        return

    args.gpu_policy = "custom_device_explicit"


def _csv(value: str) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _window_config(args: argparse.Namespace) -> dict[str, object]:
    if args.window_plan_mode == "detector_local":
        return {
            "enabled": True,
            "builders": ["detector_geometry", "orbits"],
            "include_single_detectors": True,
            "include_detector_pairs": True,
            "include_radius1": True,
            "include_boundary_logical": True,
            "max_window_bits": int(args.max_window_bits),
            "max_windows": int(args.max_windows),
        }
    return {
        "enabled": True,
        "builders": ["detector_geometry", "logical_observable"],
        "include_single_detectors": True,
        "include_detector_pairs": True,
        "include_radius1": False,
        "include_boundary_logical": False,
        "include_logical_single": True,
        "include_logical_detector_pairs": True,
        "include_logical_fault_support": True,
        "max_window_bits": int(args.max_window_bits),
        "max_windows": int(args.max_windows),
        "window_family_budgets": {
            "single_detector": "all",
            "detector_pair": int(args.detector_pair_window_budget),
            "logical_single": "all",
            "logical_detector_pair": int(args.logical_detector_pair_window_budget),
            "logical_fault_support": "all",
        },
    }


def _spectral_memory_cap_bytes(args: argparse.Namespace) -> int:
    return int(args.spectral_memory_cap_mib) * 1024 * 1024


def _prepare_google_fault_graph(
    args: argparse.Namespace,
    leaf,
    *,
    orbit_mode: str,
    schedule_context,
    dem_data_cache: dict[str, object],
    cache_events: list[dict[str, object]],
) -> tuple[FaultGraph, dict[str, object]]:
    identity = _fault_graph_cache_identity(args, leaf, orbit_mode)
    key = prepared_fault_graph_cache_key(identity)
    path = prepared_fault_graph_cache_file(args.prepared_cache_dir, key)
    event = {
        "cache_kind": "fault_graph",
        "role": "fault_graph",
        "sample_id": leaf.sample_id,
        "preprocessing_mode": orbit_mode,
        "residual_rank": int(args.residual_rank),
        "cache_key_prefix": key[:16],
        "cache_path": str(path),
    }
    if not bool(args.disable_prepared_cache):
        load_result = load_prepared_fault_graph_cache(path, expected_key=key)
        if load_result.graph is not None:
            cache_events.append({**event, "cache_status": load_result.status, "cache_written": False})
            return load_result.graph, load_result.audit

    dem_data = dem_data_cache.get("dem_data")
    if dem_data is None:
        dem_data = load_google_dem_data(leaf, args.dem_source)
        dem_data_cache["dem_data"] = dem_data
    graph, preprocessing_audit = build_google_fault_graph(
        leaf,
        dem_source=args.dem_source,
        orbit_mode=orbit_mode,
        residual_rank=args.residual_rank,
        schedule_context=schedule_context,
        dem_data=dem_data,
    )
    if not bool(args.disable_prepared_cache):
        save_prepared_fault_graph_cache(
            path,
            key=key,
            graph=graph,
            audit=preprocessing_audit,
            metadata=identity,
        )
        status = load_result.status if "load_result" in locals() else "miss"
        cache_events.append({**event, "cache_status": status, "cache_written": True})
    else:
        cache_events.append({**event, "cache_status": "disabled", "cache_written": False})
    return graph, preprocessing_audit


def _prepare_train_objectives(
    args: argparse.Namespace,
    leaf,
    graph,
    train_observations: torch.Tensor,
    windows: WindowPlan,
    *,
    orbit_mode: str,
    split: dict[str, object],
    observation_modes: set[str],
    cache_events: list[dict[str, object]],
) -> dict[str, LikelihoodObjective]:
    objectives = {}
    for observation_mode in sorted(observation_modes):
        objective_windows = tuple(
            detector_only_windows(graph, list(windows.windows)) if observation_mode == "detectors" else windows.windows
        )
        batch_cache = _prepare_window_batch_cache(
            args,
            leaf,
            graph,
            train_observations,
            objective_windows,
            orbit_mode=orbit_mode,
            role=f"train_{observation_mode}",
            slice_start=int(split["train_start"]),
            slice_end=int(split["train_end"]),
            cache_events=cache_events,
        )
        if batch_cache is not None:
            local_window_likelihood = ExactLocalWindowParityLikelihood(
                graph=graph,
                observations=train_observations,
                observation_mode=observation_mode,
                aggregate_unique=True,
                requested_backend=args.likelihood_backend,
                windows=objective_windows,
                cuda_kernel_variant=args.cuda_kernel_variant,
                spectral_min_abs_factor=float(args.spectral_min_abs_factor),
                spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
                window_caches=(),
                window_batch_cache=batch_cache,
            )
            objectives[observation_mode] = LikelihoodObjective(
                name="local_exact",
                graph=graph,
                observations=train_observations,
                observation_mode=observation_mode,
                aggregate_unique=True,
                requested_backend=args.likelihood_backend,
                cuda_kernel_variant=args.cuda_kernel_variant,
                spectral_min_abs_factor=float(args.spectral_min_abs_factor),
                spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
                windows=objective_windows,
                window_caches=(),
                window_batch_cache=batch_cache,
                local_window_likelihood=local_window_likelihood,
            )
            continue
        objectives[observation_mode] = build_likelihood_objective(
            graph,
            train_observations,
            likelihood_objective="local_exact",
            observation_mode=observation_mode,
            aggregate_unique=True,
            backend=args.likelihood_backend,
            cuda_kernel_variant=args.cuda_kernel_variant,
            spectral_min_abs_factor=float(args.spectral_min_abs_factor),
            spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
            windows=objective_windows,
            device=args.device,
        )
    return objectives


def _prepare_eval_cache(
    args: argparse.Namespace,
    leaf,
    graph,
    observations: torch.Tensor,
    windows: WindowPlan,
    *,
    orbit_mode: str,
    role: str,
    slice_start: int,
    slice_end: int,
    cache_events: list[dict[str, object]],
) -> PreparedEvalCache:
    device = torch.device(args.device)
    if device.type == "cuda" and args.likelihood_backend == "cuda_extension":
        batch_cache = _prepare_window_batch_cache(
            args,
            leaf,
            graph,
            observations,
            tuple(windows.windows),
            orbit_mode=orbit_mode,
            role=role,
            slice_start=slice_start,
            slice_end=slice_end,
            cache_events=cache_events,
        )
        if batch_cache is None:
            batch_cache = build_window_batch_nll_cache_from_observations(
                graph,
                observations,
                list(windows.windows),
                aggregate_unique=True,
                device=device,
                cache_backend="cuda_extension",
            )
        return [], batch_cache
    caches = build_window_nll_caches(
        graph,
        observations,
        list(windows.windows),
        aggregate_unique=True,
        device=args.device,
    )
    batch_cache = None
    if device.type == "cuda" and args.likelihood_backend == "cuda_extension":
        batch_cache = build_window_batch_nll_cache(caches, device=device)
    return caches, batch_cache


def _prepare_window_batch_cache(
    args: argparse.Namespace,
    leaf,
    graph,
    observations: torch.Tensor,
    windows: tuple[ObservationWindow, ...],
    *,
    orbit_mode: str,
    role: str,
    slice_start: int,
    slice_end: int,
    cache_events: list[dict[str, object]],
) -> WindowBatchNLLCache | None:
    device = torch.device(args.device)
    if device.type != "cuda" or args.likelihood_backend != "cuda_extension":
        return None
    if not windows:
        return None

    identity = _window_cache_identity(
        args,
        leaf,
        graph,
        observations,
        windows,
        orbit_mode=orbit_mode,
        role=role,
        slice_start=slice_start,
        slice_end=slice_end,
    )
    key = window_batch_cache_key(graph, windows, identity)
    path = window_batch_cache_file(args.prepared_cache_dir, key)
    event = {
        "role": role,
        "sample_id": leaf.sample_id,
        "preprocessing_mode": orbit_mode,
        "num_windows": len(windows),
        "num_observations": int(observations.shape[0]),
        "cache_key_prefix": key[:16],
        "cache_path": str(path),
    }
    if not bool(args.disable_prepared_cache):
        load_result = load_window_batch_cache(path, expected_key=key, device=device)
        if load_result.cache is not None:
            cache_events.append({**event, "cache_status": load_result.status, "cache_written": False})
            return load_result.cache
        batch_cache = build_window_batch_nll_cache_from_observations(
            graph,
            observations,
            list(windows),
            aggregate_unique=True,
            device=device,
            cache_backend="cuda_extension",
        )
        save_window_batch_cache(path, key=key, cache=batch_cache, metadata=identity)
        cache_events.append(
            {
                **event,
                "cache_status": load_result.status,
                "cache_written": True,
            }
        )
        return batch_cache

    batch_cache = build_window_batch_nll_cache_from_observations(
        graph,
        observations,
        list(windows),
        aggregate_unique=True,
        device=device,
        cache_backend="cuda_extension",
    )
    cache_events.append({**event, "cache_status": "disabled", "cache_written": False})
    return batch_cache


def _window_cache_identity(
    args: argparse.Namespace,
    leaf,
    graph,
    observations: torch.Tensor,
    windows: tuple[ObservationWindow, ...],
    *,
    orbit_mode: str,
    role: str,
    slice_start: int,
    slice_end: int,
) -> dict[str, object]:
    return {
        "experiment": "S1.6_google_static",
        "role": role,
        "sample_id": leaf.sample_id,
        "patch_id": leaf.patch_id,
        "basis": leaf.basis,
        "rounds_label": leaf.rounds_label,
        "dem_source": args.dem_source,
        "preprocessing_mode": orbit_mode,
        "residual_rank": int(args.residual_rank),
        "window_config": _window_config(args),
        "num_windows": len(windows),
        "aggregate_unique": True,
        "observation_shape": tuple(int(value) for value in observations.shape),
        "observation_slice": {"start": int(slice_start), "end": int(slice_end)},
        "observation_files": _observation_file_signature(leaf),
        "graph_shape": {"B": int(graph.B), "M": int(graph.M)},
    }


def _fault_graph_cache_identity(args: argparse.Namespace, leaf, orbit_mode: str) -> dict[str, object]:
    graph_source_paths = [leaf.metadata_path, leaf.circuit_ideal_path]
    if args.dem_source in {"noisy_si1000", "circuit_noisy_si1000"}:
        graph_source_paths.append(leaf.circuit_noisy_si1000_path)
    else:
        graph_source_paths.append(leaf.decoder_dem_path(args.dem_source))
    return {
        "experiment": "S1_google_fault_graph",
        "graph_contract": "stage1_dem_fault_logit_fault_graph",
        "sample_id": leaf.sample_id,
        "patch_id": leaf.patch_id,
        "basis": leaf.basis,
        "rounds_label": leaf.rounds_label,
        "dem_source": args.dem_source,
        "preprocessing_mode": orbit_mode,
        "residual_rank": int(args.residual_rank),
        "canonicalize_duplicate_masks": True,
        "source_files": [_file_signature(path) for path in graph_source_paths],
    }


def _observation_file_signature(leaf) -> list[dict[str, object]]:
    return [_file_signature(path) for path in (leaf.detection_events_path, leaf.obs_flips_actual_path)]


def _file_signature(path: Path) -> dict[str, object]:
    item: dict[str, object] = {"path": str(path)}
    if path.exists():
        stat = path.stat()
        item.update({"size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)})
    else:
        item["missing"] = True
    return item


def _google_prototype_counts(args: argparse.Namespace, graph: FaultGraph, model_name: str) -> tuple[int | None, ...]:
    if not is_discovery_model(model_name):
        return (None,)
    return tuple(_resolve_google_prototype_count(value, graph.O) for value in _csv(args.discovery_prototype_counts))


def _resolve_google_prototype_count(value: str, num_orbits: int) -> int:
    text = str(value).strip().upper()
    if text == "O":
        return int(num_orbits)
    if text.startswith("O+") or text.startswith("O-"):
        return int(num_orbits + int(text[1:]))
    return int(text)


def _google_model_options(
    args: argparse.Namespace,
    model_name: str,
    prototype_count: int | None,
) -> dict[str, object]:
    options: dict[str, object] = {}
    if model_name == "dmle_qec":
        options["perturb_scale"] = 0.5
    if model_name in {"soft_feature_orbit", "disc_soft"}:
        options["beta_l2"] = 0.001
    if is_discovery_model(model_name):
        if prototype_count is None:
            raise ValueError("discovery model requires prototype_count")
        options["prototype_count"] = int(prototype_count)
    return options


def _google_model_label(
    model_name: str,
    prototype_count: int | None,
    prototype_counts: tuple[int | None, ...],
) -> str:
    if not is_discovery_model(model_name) or prototype_count is None or len(prototype_counts) == 1:
        return model_name
    return f"{model_name}_K{int(prototype_count)}"


def _fit_google_discovery_restarts(
    args: argparse.Namespace,
    graph: FaultGraph,
    *,
    model_name: str,
    model_options: dict[str, object],
    train_observations: torch.Tensor,
    train_objective: LikelihoodObjective,
    windows: WindowPlan,
    dtype: torch.dtype,
    observation_mode: str,
) -> dict[str, object]:
    outcomes: list[dict[str, object]] = []
    selected_fit: dict[str, object] | None = None
    best_nll = float("inf")
    restarts = max(1, int(args.discovery_restarts))
    for restart_index in range(restarts):
        restart_seed = int(args.seed) + 100_000 + restart_index
        torch.manual_seed(restart_seed)
        field = make_field(model_name, graph, dtype=dtype, seed=restart_seed, model_options=model_options)
        fit = fit_field(
            graph,
            field,
            train_observations,
            steps=args.steps,
            lr=args.lr,
            aggregate_unique=True,
            device=args.device,
            backend=args.likelihood_backend,
            cuda_kernel_variant=args.cuda_kernel_variant,
            spectral_min_abs_factor=args.spectral_min_abs_factor,
            spectral_memory_cap_bytes=_spectral_memory_cap_bytes(args),
            observation_mode=observation_mode,
            likelihood_objective="local_exact",
            windows=windows,
            prepared_objective=train_objective,
        )
        history = list(fit.get("history", []))
        train_final = float(history[-1]) if history else float("inf")
        assignment = field_discovery_metrics(
            fit["field"],
            None,
            active_mass_threshold=float(args.discovery_active_mass_threshold),
        )
        outcome = {
            "restart_index": int(restart_index),
            "restart_seed": int(restart_seed),
            "selected": False,
            "train_initial_nll": history[0] if history else None,
            "train_final_nll": train_final,
            "assignment_entropy_normalized": assignment.get("assignment_entropy_normalized"),
            "num_active_prototypes": assignment.get("num_active_prototypes"),
            "assignment_collapse": assignment.get("assignment_collapse"),
        }
        outcomes.append(outcome)
        if selected_fit is None or train_final < best_nll:
            best_nll = train_final
            selected_fit = fit
            selected_index = restart_index

    assert selected_fit is not None
    for outcome in outcomes:
        outcome["selected"] = outcome["restart_index"] == selected_index
    selected_fit["selected_restart_index"] = int(selected_index)
    selected_fit["restart_outcomes"] = outcomes
    return {"fit": selected_fit, "restart_outcomes": outcomes}


def _train_heldout_split(num_shots: int, train_shots: int, heldout_shots: int) -> dict[str, object]:
    if num_shots <= 0:
        raise ValueError("observations must contain at least one shot")
    heldout_count = min(int(heldout_shots), int(num_shots))
    train_count = min(int(train_shots), max(0, int(num_shots) - heldout_count))
    if train_count <= 0:
        raise ValueError("train_shots leaves no training data after the heldout split")
    heldout_start = int(num_shots) - heldout_count
    return {
        "num_shots": int(num_shots),
        "train_shots": int(train_count),
        "heldout_shots": int(heldout_count),
        "train_start": 0,
        "train_end": int(train_count),
        "heldout_start": int(heldout_start),
        "heldout_end": int(num_shots),
        "disjoint": bool(train_count <= heldout_start),
        "train_slice": slice(0, int(train_count)),
        "heldout_slice": slice(int(heldout_start), int(num_shots)),
    }


def _json_split(split: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in split.items() if not isinstance(value, slice)}


def _record(
    *,
    args: argparse.Namespace,
    leaf,
    graph,
    model_name: str,
    orbit_mode: str,
    split: dict[str, object],
    fit: dict[str, object],
    metrics: dict[str, object],
    preprocessing_audit: dict[str, object],
    parameter_count: int,
    fit_wall_seconds: float,
    eval_wall_seconds: float,
    base_model_name: str | None = None,
    prototype_count: int | None = None,
) -> dict[str, object]:
    feature_audit = graph.residual_feature_audit_dict()
    base_model = model_name if base_model_name is None else base_model_name
    local_parameter_count = graph.M
    hard_parameter_count = graph.O
    soft_parameter_count = graph.O * (1 + graph.residual_rank)
    record = {
        "sample_id": leaf.sample_id,
        "patch_id": leaf.patch_id,
        "basis": leaf.basis,
        "rounds_label": leaf.rounds_label,
        "dem_source": args.dem_source,
        "preprocessing_mode": orbit_mode,
        "model": model_name,
        "base_model": base_model,
        "prototype_count_K": None if prototype_count is None else int(prototype_count),
        "seed": int(args.seed),
        "M_raw": int(preprocessing_audit["M_raw"]),
        "M_effective": int(preprocessing_audit["M_effective"]),
        "B": int(preprocessing_audit["B"]),
        "O": int(preprocessing_audit["O"]),
        "local_parameter_count": int(local_parameter_count),
        "hard_parameter_count": int(hard_parameter_count),
        "soft_parameter_count": int(soft_parameter_count),
        "parameter_count": int(parameter_count),
        "compression_ratio": compression_ratio(local_parameter_count, parameter_count),
        "residual_rank": int(graph.residual_rank),
        "selected_residual_feature_indices": feature_audit["selected_feature_indices"],
        "number_of_non_singleton_orbits": feature_audit["num_non_singleton_orbits"],
        "number_of_orbits_with_nonzero_centered_feature_rank": feature_audit[
            "num_orbits_with_nonzero_centered_feature_rank"
        ],
        "mean_centered_feature_rank": feature_audit["mean_centered_feature_rank"],
        "max_centered_feature_rank": feature_audit["max_centered_feature_rank"],
        "soft_residual_features_collapse_inside_orbits_warning": bool(
            base_model == "soft_feature_orbit"
            and graph.residual_rank > 0
            and int(feature_audit["num_non_singleton_orbits"]) > 0
            and int(feature_audit["num_orbits_with_nonzero_centered_feature_rank"]) == 0
        ),
        "schedule_symmetry_status": preprocessing_audit.get("schedule_symmetry_status"),
        "train_heldout_split": _json_split(split),
        "fit_wall_seconds": float(fit_wall_seconds),
        "eval_wall_seconds": float(eval_wall_seconds),
    }
    record.update({key: value for key, value in fit.items() if key != "field"})
    record.update(metrics)
    return record


def _cross_sample_transfer(
    *,
    args: argparse.Namespace,
    source_leaf,
    source_graph,
    logits: torch.Tensor,
    windows: WindowPlan,
    model_name: str,
    orbit_mode: str,
    transfer_cache: dict[tuple[str, str], dict[str, object]],
    cache_events: list[dict[str, object]],
    base_model_name: str | None = None,
    prototype_count: int | None = None,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sample_index in range(int(args.cross_sample_start), int(args.cross_sample_stop) + 1):
        sample_id = f"sample_{sample_index:02d}"
        try:
            prepared = _prepare_transfer_target(
                args=args,
                source_leaf=source_leaf,
                source_graph=source_graph,
                windows=windows,
                orbit_mode=orbit_mode,
                sample_id=sample_id,
                transfer_cache=transfer_cache,
                cache_events=cache_events,
            )
            if not bool(prepared["transfer_evaluated"]):
                records.append(
                {
                    "sample_id": sample_id,
                    "model": model_name,
                    "base_model": base_model_name or model_name,
                    "prototype_count_K": None if prototype_count is None else int(prototype_count),
                    "preprocessing_mode": orbit_mode,
                    "transfer_evaluated": False,
                    "skip_reason": prepared["skip_reason"],
                    }
                )
                continue
            eval_cache = prepared["eval_cache"]
            metrics = evaluate_real_data_model(
                source_graph,
                logits,
                prepared["eval_observations"],
                aggregate_unique=True,
                backend=args.likelihood_backend,
                windows=list(windows.windows),
                window_caches=eval_cache[0],
                window_batch_cache=eval_cache[1],
                predicted_observables=prepared["eval_predicted"],
            )
            record = {
                "sample_id": sample_id,
                "model": model_name,
                "base_model": base_model_name or model_name,
                "prototype_count_K": None if prototype_count is None else int(prototype_count),
                "preprocessing_mode": orbit_mode,
                "transfer_evaluated": True,
                "train_sample_id": source_leaf.sample_id,
                "cross_sample_split": prepared["split"],
                "transfer_cache_reused": bool(prepared["cache_reused"]),
                "cross_sample_transfer_NLL": metrics["heldout_local_window_nll"],
                "cross_sample_transfer_empirical_entropy": metrics.get("heldout_local_window_empirical_entropy"),
                "cross_sample_transfer_excess_NLL": metrics.get("heldout_local_window_excess_nll"),
                "cross_sample_detector_window_excess_NLL": metrics.get("heldout_detector_window_excess_nll"),
                "cross_sample_logical_window_excess_NLL": metrics.get("heldout_logical_window_excess_nll"),
                "cross_sample_detector_rate_MAE": metrics["detector_rate_mae"],
                "cross_sample_logical_flip_calibration": metrics["logical_flip_rate_calibration"],
                "cross_sample_local_correlation_error": metrics["local_correlation_error"],
            }
            record.update(metrics)
            records.append(record)
        except Exception as exc:
            records.append(
                {
                    "sample_id": sample_id,
                    "model": model_name,
                    "base_model": base_model_name or model_name,
                    "prototype_count_K": None if prototype_count is None else int(prototype_count),
                    "preprocessing_mode": orbit_mode,
                    "transfer_evaluated": False,
                    "skip_reason": str(exc),
                }
            )
    return records


def _prepare_transfer_target(
    *,
    args: argparse.Namespace,
    source_leaf,
    source_graph,
    windows: WindowPlan,
    orbit_mode: str,
    sample_id: str,
    transfer_cache: dict[tuple[str, str], dict[str, object]],
    cache_events: list[dict[str, object]],
) -> dict[str, object]:
    key = (orbit_mode, sample_id)
    if key in transfer_cache:
        prepared = dict(transfer_cache[key])
        prepared["cache_reused"] = True
        return prepared

    target_leaf = find_google_set1_leaf(
        source_leaf.root,
        sample_id=sample_id,
        patch_id=source_leaf.patch_id,
        basis=source_leaf.basis,
        rounds_label=source_leaf.rounds_label,
    )
    target_graph, _ = build_google_fault_graph(
        target_leaf,
        dem_source=args.dem_source,
        orbit_mode=orbit_mode,
        residual_rank=source_graph.residual_rank,
    )
    if target_graph.A.shape != source_graph.A.shape or not torch.equal(target_graph.A, source_graph.A):
        prepared = {
            "transfer_evaluated": False,
            "skip_reason": "target DEM parity map differs from source",
            "cache_reused": False,
        }
        transfer_cache[key] = prepared
        return dict(prepared)
    target_observations = load_google_observations(target_leaf)
    split = _train_heldout_split(target_observations.shape[0], args.train_shots, args.heldout_shots)
    eval_observations = target_observations[split["heldout_slice"]]
    predicted = load_google_predicted_observables(target_leaf, args.dem_source)
    eval_predicted = None if predicted is None else predicted[split["heldout_slice"]]
    prepared = {
        "transfer_evaluated": True,
        "eval_observations": eval_observations,
        "eval_predicted": eval_predicted,
        "eval_cache": _prepare_eval_cache(
            args,
            target_leaf,
            source_graph,
            eval_observations,
            windows,
            orbit_mode=orbit_mode,
            role="transfer_eval",
            slice_start=int(split["heldout_start"]),
            slice_end=int(split["heldout_end"]),
            cache_events=cache_events,
        ),
        "split": _json_split(split),
        "cache_reused": False,
    }
    transfer_cache[key] = prepared
    return dict(prepared)


def _decision_summary(records: list[dict[str, object]]) -> dict[str, object]:
    by_model_mode = {(record["model"], record["preprocessing_mode"]): record for record in records}
    decisions = []
    for (model, mode), schedule_record in sorted(by_model_mode.items()):
        if mode != "schedule_geometric":
            continue
        heuristic_record = by_model_mode.get((model, "fault_graph_heuristic"))
        status = schedule_record.get("schedule_symmetry_status")
        if status != "nontrivial":
            decisions.append(
                {
                    "model": model,
                    "schedule_geometric_useful": False,
                    "reason": (
                        "identity_only or invalid schedule symmetry; current DEM-mask FaultGraph "
                        "heuristic is sufficient for Stage-1 Google validation"
                    ),
                    "schedule_symmetry_status": status,
                }
            )
            continue
        if heuristic_record is None:
            decisions.append(
                {
                    "model": model,
                    "schedule_geometric_useful": None,
                    "reason": "no fault_graph_heuristic comparison record",
                    "schedule_symmetry_status": status,
                }
            )
            continue
        schedule_nll = schedule_record.get("heldout_local_window_nll")
        heuristic_nll = heuristic_record.get("heldout_local_window_nll")
        schedule_params = int(schedule_record.get("parameter_count", 0))
        heuristic_params = int(heuristic_record.get("parameter_count", 0))
        comparable = schedule_nll is not None and heuristic_nll is not None
        useful = bool(comparable and float(schedule_nll) <= float(heuristic_nll) + 1e-9 and schedule_params <= heuristic_params)
        decisions.append(
            {
                "model": model,
                "schedule_geometric_useful": useful,
                "reason": "nontrivial schedule symmetry with equal-or-better heldout NLL at equal-or-fewer parameters"
                if useful
                else "schedule preprocessing did not beat the DEM-mask FaultGraph heuristic under the S1.6 rule",
                "schedule_symmetry_status": status,
                "schedule_heldout_local_window_nll": schedule_nll,
                "heuristic_heldout_local_window_nll": heuristic_nll,
                "schedule_parameter_count": schedule_params,
                "heuristic_parameter_count": heuristic_params,
            }
        )
    return {"per_model": decisions}


def _micro_window_global_validation(backend: str) -> dict[str, object]:
    device = torch.device("cuda" if backend == "cuda_extension" and torch.cuda.is_available() else "cpu")
    graph = FaultGraph.from_raw_masks(
        torch.tensor(
            [
                [1, 0, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 1],
            ],
            dtype=torch.bool,
        ),
        num_detectors=2,
        num_observables=1,
        residual_rank=0,
    )
    observations = torch.tensor(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [1, 1, 0],
            [0, 0, 1],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1],
        ],
        dtype=torch.bool,
    )
    windows = [
        ObservationWindow("micro:detectors", (0, 1), "detector_pair"),
        ObservationWindow("micro:logical0", (0, 2), "boundary_logical"),
        ObservationWindow("micro:logical1", (1, 2), "boundary_logical"),
    ]
    candidates = [
        torch.tensor([-4.0, -4.0, -5.0, -6.0], dtype=torch.float64),
        torch.tensor([-3.0, -3.5, -4.0, -5.0], dtype=torch.float64),
        torch.tensor([-2.5, -2.0, -3.0, -4.0], dtype=torch.float64),
        torch.tensor([-1.5, -2.0, -2.0, -3.0], dtype=torch.float64),
    ]
    candidates = [logits.to(device=device) for logits in candidates]
    global_values = [
        float(exact_dem_nll(graph, logits, observations, aggregate_unique=True, backend=backend).detach().cpu())
        for logits in candidates
    ]
    local_values = [
        float(
            local_window_exact_nll(graph, logits, observations, windows, aggregate_unique=True, backend=backend)
            .detach()
            .cpu()
        )
        for logits in candidates
    ]
    return {
        "global_exact_feasible": True,
        "B": graph.B,
        "num_candidates": len(candidates),
        "global_exact_nll": global_values,
        "local_window_nll": local_values,
        "pearson_correlation": _pearson(global_values, local_values),
    }


def _pearson(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    left_var = sum((a - left_mean) ** 2 for a in left)
    right_var = sum((b - right_mean) ** 2 for b in right)
    denom = (left_var * right_var) ** 0.5
    return float(numerator / denom) if denom else 0.0


def _jsonable(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, slice):
        return {"start": value.start, "stop": value.stop, "step": value.step}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import torch

from scope_static.fault_graph import FaultGraph
from scope_static.fields import make_field
from scope_static.google_set1 import (
    CLAIM_BOUNDARY,
    build_google_fault_graph,
    build_google_schedule_context,
    find_google_set1_leaf,
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
from scope_static.metrics import compression_audit, compression_ratio, evaluate_real_data_model
from scope_static.objectives import LikelihoodObjective, build_likelihood_objective
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
    dtype = torch.float64 if args.dtype == "float64" else torch.float32
    model_names = _csv(args.models)
    required_observation_modes = {"detectors" if model == "dmle_qec" else "full" for model in model_names}

    for orbit_mode in _csv(args.orbit_modes):
        prepare_start = time.perf_counter()
        graph, preprocessing_audit = build_google_fault_graph(
            leaf,
            dem_source=args.dem_source,
            orbit_mode=orbit_mode,
            residual_rank=args.residual_rank,
            schedule_context=schedule_context,
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
        window_audit["preprocessing_mode"] = orbit_mode
        window_audits.append(window_audit)
        print(
            json.dumps(
                {
                    "event": "prepared_preprocessing",
                    "preprocessing_mode": orbit_mode,
                    "num_windows": len(windows),
                    "prepare_wall_seconds": time.perf_counter() - prepare_start,
                },
                sort_keys=True,
            ),
            flush=True,
        )

        for model_name in model_names:
            fit_start = time.perf_counter()
            print(
                json.dumps(
                    {
                        "event": "start_fit",
                        "preprocessing_mode": orbit_mode,
                        "model": model_name,
                        "device": args.device,
                        "likelihood_backend": args.likelihood_backend,
                        "cuda_kernel_variant": args.cuda_kernel_variant,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            seed = int(args.seed)
            torch.manual_seed(seed)
            field = make_field(model_name, graph, dtype=dtype, seed=seed)
            observation_mode = "detectors" if model_name == "dmle_qec" else "full"
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
            eval_seconds = time.perf_counter() - eval_start
            record = _record(
                args=args,
                leaf=leaf,
                graph=graph,
                model_name=model_name,
                orbit_mode=orbit_mode,
                split=split,
                fit=fit,
                metrics=metrics,
                preprocessing_audit=preprocessing_audit,
                parameter_count=int(trained_field.parameter_count),
                fit_wall_seconds=fit_seconds,
                eval_wall_seconds=eval_seconds,
            )
            records.append(record)
            print(
                json.dumps(
                    {
                        "event": "finish_fit",
                        "preprocessing_mode": orbit_mode,
                        "model": model_name,
                        "fit_wall_seconds": fit_seconds,
                        "eval_wall_seconds": eval_seconds,
                        "heldout_local_window_nll": metrics.get("heldout_local_window_nll"),
                        "adapter": fit.get("likelihood_adapter"),
                    },
                    sort_keys=True,
                ),
                flush=True,
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
                        model_name=model_name,
                        orbit_mode=orbit_mode,
                        transfer_cache=transfer_cache,
                        cache_events=prepared_cache_events,
                    )
                )
                print(
                    json.dumps(
                        {
                            "event": "finish_transfer",
                            "preprocessing_mode": orbit_mode,
                            "model": model_name,
                            "transfer_wall_seconds": time.perf_counter() - transfer_start,
                            "num_target_samples": int(args.cross_sample_stop) - int(args.cross_sample_start) + 1,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

    result = {
        "run": {
            "name": "S1.6 Google 72Q Set1 preprocessing ablation",
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
    print(json.dumps({"metrics_path": str(metrics_path), "num_records": len(records)}, sort_keys=True))
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
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--residual-rank", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", choices=["float64", "float32"], default="float64")
    parser.add_argument("--likelihood-backend", choices=["auto", "pytorch", "cuda_extension"], default="auto")
    parser.add_argument(
        "--cuda-kernel-variant",
        choices=["dp", "spectral_shadow", "spectral", "auto"],
        default="dp",
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
    parser.add_argument("--output-dir", default="outputs/google_static/S1_6")
    parser.add_argument("--prepared-cache-dir", default=None)
    parser.add_argument("--disable-prepared-cache", action="store_true")
    parser.add_argument("--cross-sample-transfer", dest="cross_sample_transfer", action="store_true", default=False)
    parser.add_argument("--skip-cross-sample-transfer", dest="cross_sample_transfer", action="store_false")
    parser.add_argument("--cross-sample-start", type=int, default=1)
    parser.add_argument("--cross-sample-stop", type=int, default=20)
    return parser.parse_args(argv)


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


def _spectral_memory_cap_bytes(args: argparse.Namespace) -> int:
    return int(args.spectral_memory_cap_mib) * 1024 * 1024


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


def _observation_file_signature(leaf) -> list[dict[str, object]]:
    signatures = []
    for path in (leaf.detection_events_path, leaf.obs_flips_actual_path):
        item: dict[str, object] = {"path": str(path)}
        if path.exists():
            stat = path.stat()
            item.update({"size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)})
        else:
            item["missing"] = True
        signatures.append(item)
    return signatures


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
) -> dict[str, object]:
    feature_audit = graph.residual_feature_audit_dict()
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
            model_name == "soft_feature_orbit"
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
                "preprocessing_mode": orbit_mode,
                "transfer_evaluated": True,
                "train_sample_id": source_leaf.sample_id,
                "cross_sample_split": prepared["split"],
                "transfer_cache_reused": bool(prepared["cache_reused"]),
                "cross_sample_transfer_NLL": metrics["heldout_local_window_nll"],
                "cross_sample_detector_rate_MAE": metrics["detector_rate_mae"],
                "cross_sample_logical_flip_calibration": metrics["logical_flip_rate_calibration"],
            }
            record.update(metrics)
            records.append(record)
        except Exception as exc:
            records.append(
                {
                    "sample_id": sample_id,
                    "model": model_name,
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

from __future__ import annotations

import argparse
import json

import torch

from .static import _train_heldout_split
from scope_static.dem.fields import make_field
from scope_static.google.set1 import build_google_fault_graph, find_google_set1_leaf, load_google_observations
from scope_static.dem.metrics import evaluate_real_data_model
from scope_static.dem.training import fit_field
from scope_static.dem.windows import WindowPlan


def main(argv: list[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA reproduction gate requires torch.cuda.is_available()")
    leaf = find_google_set1_leaf(
        args.dataset_root,
        sample_id=args.sample_id,
        patch_id=args.patch_id,
        basis=args.basis,
        rounds_label=args.rounds_label,
    )
    observations = load_google_observations(leaf)
    split = _train_heldout_split(observations.shape[0], args.train_shots, args.heldout_shots)
    train_observations = observations[split["train_slice"]]
    heldout_observations = observations[split["heldout_slice"]]
    graph, _audit = build_google_fault_graph(
        leaf,
        dem_source=args.dem_source,
        orbit_mode=args.orbit_mode,
        residual_rank=args.residual_rank,
    )
    windows = WindowPlan.from_config(
        graph,
        {
            "enabled": True,
            "builders": ["detector_geometry", "orbits"],
            "include_single_detectors": True,
            "include_detector_pairs": True,
            "include_radius1": True,
            "include_boundary_logical": True,
            "max_window_bits": int(args.max_window_bits),
            "max_windows": int(args.max_windows),
        },
    )
    dp = _fit_and_evaluate(
        args,
        graph,
        train_observations,
        heldout_observations,
        windows,
        cuda_kernel_variant="dp",
    )
    shadow = _fit_and_evaluate(
        args,
        graph,
        train_observations,
        heldout_observations,
        windows,
        cuda_kernel_variant="spectral_shadow",
    )
    logit_delta = shadow["logits"] - dp["logits"]
    result = {
        "case": {
            "sample_id": leaf.sample_id,
            "patch_id": leaf.patch_id,
            "basis": leaf.basis,
            "rounds_label": leaf.rounds_label,
            "dem_source": args.dem_source,
            "orbit_mode": args.orbit_mode,
            "model": args.model,
            "seed": int(args.seed),
            "train_shots": int(split["train_shots"]),
            "heldout_shots": int(split["heldout_shots"]),
            "max_window_bits": int(args.max_window_bits),
            "max_windows": int(args.max_windows),
            "steps": int(args.steps),
        },
        "dp": _without_logits(dp),
        "spectral_shadow": _without_logits(shadow),
        "deltas": {
            "heldout_local_window_nll": _metric_delta(dp, shadow, "heldout_local_window_nll"),
            "detector_rate_mae": _metric_delta(dp, shadow, "detector_rate_mae"),
            "local_correlation_error": _metric_delta(dp, shadow, "local_correlation_error"),
            "logical_flip_rate_calibration": _metric_delta(dp, shadow, "logical_flip_rate_calibration"),
            "fitted_logit_rmse": float(torch.sqrt(torch.mean(logit_delta**2)).detach().cpu()),
            "fitted_logit_max_abs_diff": float(logit_delta.abs().max().detach().cpu()),
        },
    }
    print(json.dumps(result, sort_keys=True))
    return result


def _fit_and_evaluate(
    args: argparse.Namespace,
    graph,
    train_observations: torch.Tensor,
    heldout_observations: torch.Tensor,
    windows: WindowPlan,
    *,
    cuda_kernel_variant: str,
) -> dict[str, object]:
    torch.manual_seed(int(args.seed))
    dtype = torch.float64 if args.dtype == "float64" else torch.float32
    field = make_field(args.model, graph, dtype=dtype, seed=int(args.seed))
    fit = fit_field(
        graph,
        field,
        train_observations,
        steps=int(args.steps),
        lr=float(args.lr),
        aggregate_unique=True,
        device="cuda",
        backend="cuda_extension",
        cuda_kernel_variant=cuda_kernel_variant,
        spectral_min_abs_factor=float(args.spectral_min_abs_factor),
        spectral_memory_cap_bytes=int(args.spectral_memory_cap_mib) * 1024 * 1024,
        observation_mode="detectors" if args.model == "dmle_qec" else "full",
        likelihood_objective="local_exact",
        windows=windows,
    )
    logits = fit["field"].realized_logits(graph).detach()
    metrics = evaluate_real_data_model(
        graph,
        logits,
        heldout_observations,
        aggregate_unique=True,
        backend="cuda_extension",
        windows=list(windows.windows),
    )
    return {"fit": {key: value for key, value in fit.items() if key != "field"}, "metrics": metrics, "logits": logits}


def _without_logits(record: dict[str, object]) -> dict[str, object]:
    return {"fit": record["fit"], "metrics": record["metrics"]}


def _metric_delta(left: dict[str, object], right: dict[str, object], key: str) -> float:
    return float(right["metrics"][key]) - float(left["metrics"][key])


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default="/home/cx/Document/google_72Q_surface_code_d3_d5_set1")
    parser.add_argument("--sample-id", default="sample_00")
    parser.add_argument("--patch-id", default="d3_at_q5_5")
    parser.add_argument("--basis", default="X")
    parser.add_argument("--rounds-label", default="r13")
    parser.add_argument("--dem-source", default="decoder_si1000")
    parser.add_argument("--orbit-mode", default="fault_graph_heuristic")
    parser.add_argument("--model", default="hard_orbit")
    parser.add_argument("--train-shots", type=int, default=512)
    parser.add_argument("--heldout-shots", type=int, default=256)
    parser.add_argument("--max-window-bits", type=int, default=8)
    parser.add_argument("--max-windows", type=int, default=8)
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--residual-rank", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dtype", choices=["float64", "float32"], default="float64")
    parser.add_argument("--spectral-min-abs-factor", type=float, default=1e-6)
    parser.add_argument("--spectral-memory-cap-mib", type=int, default=1024)
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import time

import torch

from scope_static.likelihood import (
    WindowBatchNLLCache,
    WindowNLLCache,
    local_window_cuda_kernel_audit,
    local_window_exact_nll_batched_from_cache,
    local_window_exact_nll_from_caches,
    local_window_workload_audit,
)
from scope_static.google_set1 import build_google_fault_graph, find_google_set1_leaf, load_google_observations
from scope_static.windows import ObservationWindow, WindowPlan


def main(argv: list[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA benchmark requires torch.cuda.is_available()")
    dtype = torch.float64 if args.dtype == "float64" else torch.float32
    cases = _synthetic_cases(args.case_preset)
    if args.max_cases is not None:
        cases = cases[: int(args.max_cases)]

    records = []
    for case in cases:
        caches, batch, logits = _make_synthetic_cache(
            k=case["k"],
            num_windows=case["windows"],
            active_faults_per_window=case["active_faults_per_window"],
            dtype=dtype,
            seed=int(args.seed),
        )
        record = {
            "case": case,
            **local_window_workload_audit(batch),
            **local_window_cuda_kernel_audit(
                batch,
                requested_kernel_variant="spectral",
                spectral_memory_cap_bytes=int(args.spectral_memory_cap_mib) * 1024 * 1024,
                scalar_bytes=torch.empty((), dtype=dtype).element_size(),
            ),
        }
        cpu_logits = logits.detach().cpu().requires_grad_(True)
        cuda_dp_logits = logits.detach().clone().cuda().requires_grad_(True)
        cuda_spectral_logits = logits.detach().clone().cuda().requires_grad_(True)

        cpu_loss, cpu_grad, cpu_seconds = _time_loss_and_grad(
            lambda: local_window_exact_nll_from_caches(cpu_logits, caches, backend="pytorch"),
            cpu_logits,
        )
        dp_loss, dp_grad, dp_seconds = _time_loss_and_grad(
            lambda: local_window_exact_nll_batched_from_cache(cuda_dp_logits, batch, cuda_kernel_variant="dp"),
            cuda_dp_logits,
            synchronize_cuda=True,
        )
        spectral_loss, spectral_grad, spectral_seconds = _time_loss_and_grad(
            lambda: local_window_exact_nll_batched_from_cache(
                cuda_spectral_logits,
                batch,
                cuda_kernel_variant="spectral",
                spectral_min_abs_factor=float(args.spectral_min_abs_factor),
                spectral_memory_cap_bytes=int(args.spectral_memory_cap_mib) * 1024 * 1024,
            ),
            cuda_spectral_logits,
            synchronize_cuda=True,
        )
        record.update(
            {
                "cpu_pytorch_seconds": cpu_seconds,
                "cuda_dp_seconds": dp_seconds,
                "cuda_spectral_seconds": spectral_seconds,
                "cpu_pytorch_loss": float(cpu_loss.detach().cpu()),
                "cuda_dp_loss": float(dp_loss.detach().cpu()),
                "cuda_spectral_loss": float(spectral_loss.detach().cpu()),
                "dp_vs_cpu_loss_abs_diff": float((dp_loss.detach().cpu() - cpu_loss.detach()).abs()),
                "spectral_vs_cpu_loss_abs_diff": float((spectral_loss.detach().cpu() - cpu_loss.detach()).abs()),
                "spectral_vs_dp_loss_abs_diff": float((spectral_loss.detach() - dp_loss.detach()).abs().cpu()),
                "spectral_vs_dp_grad_max_abs_diff": float((spectral_grad - dp_grad).abs().max().detach().cpu()),
                "spectral_vs_cpu_grad_max_abs_diff": float((spectral_grad.cpu() - cpu_grad).abs().max().detach()),
            }
        )
        print(json.dumps(record, sort_keys=True), flush=True)
        records.append(record)
    if args.google_dataset_root:
        record = _benchmark_google_s1_6(args, dtype=dtype)
        print(json.dumps(record, sort_keys=True), flush=True)
        records.append(record)
    return {"records": records}


def _time_loss_and_grad(fn, logits: torch.Tensor, *, synchronize_cuda: bool = False):
    if logits.grad is not None:
        logits.grad.zero_()
    if synchronize_cuda:
        torch.cuda.synchronize()
    start = time.perf_counter()
    loss = fn()
    loss.backward()
    if synchronize_cuda:
        torch.cuda.synchronize()
    return loss, logits.grad.detach().clone(), time.perf_counter() - start


def _make_synthetic_cache(
    *,
    k: int,
    num_windows: int,
    active_faults_per_window: int,
    dtype: torch.dtype,
    seed: int,
) -> tuple[list[WindowNLLCache], WindowBatchNLLCache, torch.Tensor]:
    generator = torch.Generator().manual_seed(seed + k * 1009 + num_windows * 37 + active_faults_per_window)
    state_count = 1 << int(k)
    caches: list[WindowNLLCache] = []
    flat_fault_ids = []
    flat_masks = []
    fault_offsets = [0]
    flat_states = []
    flat_counts = []
    state_offsets = [0]
    window_num_bits = []
    global_fault = 0
    for window_index in range(int(num_windows)):
        masks = torch.randint(1, state_count, (active_faults_per_window,), generator=generator, dtype=torch.long)
        fault_ids = torch.arange(global_fault, global_fault + active_faults_per_window, dtype=torch.long)
        global_fault += active_faults_per_window
        observed_states = torch.arange(state_count, dtype=torch.long)
        counts = torch.randint(1, 8, (state_count,), generator=generator, dtype=torch.long)
        window = ObservationWindow(f"synthetic:{window_index}", tuple(range(k)), "synthetic")
        caches.append(
            WindowNLLCache(
                window=window,
                fault_ids=fault_ids,
                mask_states=masks,
                states=observed_states,
                counts=counts,
                num_observations=int(counts.sum().item()),
            )
        )
        flat_fault_ids.append(fault_ids)
        flat_masks.append(masks)
        fault_offsets.append(fault_offsets[-1] + active_faults_per_window)
        flat_states.append(observed_states)
        flat_counts.append(counts)
        state_offsets.append(state_offsets[-1] + state_count)
        window_num_bits.append(k)
    batch = WindowBatchNLLCache(
        flat_fault_ids=torch.cat(flat_fault_ids).cuda(),
        flat_masks=torch.cat(flat_masks).cuda(),
        fault_offsets=torch.tensor(fault_offsets, dtype=torch.long, device="cuda"),
        flat_states=torch.cat(flat_states).cuda(),
        flat_counts=torch.cat(flat_counts).cuda(),
        state_offsets=torch.tensor(state_offsets, dtype=torch.long, device="cuda"),
        window_num_bits=torch.tensor(window_num_bits, dtype=torch.long, device="cuda"),
        max_faults_per_window=int(active_faults_per_window),
        max_state_count=state_count,
        num_windows=int(num_windows),
    )
    logits = torch.empty((global_fault,), dtype=dtype).normal_(mean=-3.0, std=0.35, generator=generator)
    return caches, batch, logits


def _synthetic_cases(preset: str) -> list[dict[str, int]]:
    if preset == "smoke":
        return [
            {"k": 2, "windows": 32, "active_faults_per_window": 4},
            {"k": 4, "windows": 128, "active_faults_per_window": 16},
            {"k": 8, "windows": 128, "active_faults_per_window": 64},
        ]
    return [
        {"k": k, "windows": windows, "active_faults_per_window": faults}
        for k in (1, 2, 4, 6, 8, 10, 12)
        for windows in (32, 128, 512, 2048)
        for faults in (4, 16, 64, 256)
    ]


def _benchmark_google_s1_6(args: argparse.Namespace, *, dtype: torch.dtype) -> dict[str, object]:
    leaf = find_google_set1_leaf(
        args.google_dataset_root,
        sample_id=args.google_sample_id,
        patch_id=args.google_patch_id,
        basis=args.google_basis,
        rounds_label=args.google_rounds_label,
    )
    graph, _audit = build_google_fault_graph(
        leaf,
        dem_source=args.google_dem_source,
        orbit_mode=args.google_orbit_mode,
        residual_rank=0,
    )
    observations = load_google_observations(leaf)[: int(args.google_shots)]
    windows = WindowPlan.from_config(
        graph,
        {
            "enabled": True,
            "builders": ["detector_geometry", "orbits"],
            "include_single_detectors": True,
            "include_detector_pairs": True,
            "include_radius1": True,
            "include_boundary_logical": True,
            "max_window_bits": int(args.google_max_window_bits),
            "max_windows": int(args.google_max_windows),
        },
    )
    from scope_static.likelihood import build_window_batch_nll_cache, build_window_nll_caches

    caches = build_window_nll_caches(graph, observations, list(windows.windows), aggregate_unique=True)
    batch = build_window_batch_nll_cache(caches, device="cuda")
    logits = torch.full((graph.M,), -3.0, dtype=dtype)
    cpu_logits = logits.detach().clone().requires_grad_(True)
    cuda_dp_logits = logits.detach().clone().cuda().requires_grad_(True)
    cuda_spectral_logits = logits.detach().clone().cuda().requires_grad_(True)
    cpu_loss, cpu_grad, cpu_seconds = _time_loss_and_grad(
        lambda: local_window_exact_nll_from_caches(cpu_logits, caches, backend="pytorch"),
        cpu_logits,
    )
    dp_loss, dp_grad, dp_seconds = _time_loss_and_grad(
        lambda: local_window_exact_nll_batched_from_cache(cuda_dp_logits, batch, cuda_kernel_variant="dp"),
        cuda_dp_logits,
        synchronize_cuda=True,
    )
    spectral_loss, spectral_grad, spectral_seconds = _time_loss_and_grad(
        lambda: local_window_exact_nll_batched_from_cache(
            cuda_spectral_logits,
            batch,
            cuda_kernel_variant="spectral",
            spectral_min_abs_factor=float(args.spectral_min_abs_factor),
            spectral_memory_cap_bytes=int(args.spectral_memory_cap_mib) * 1024 * 1024,
        ),
        cuda_spectral_logits,
        synchronize_cuda=True,
    )
    record = {
        "case": {
            "kind": "google_s1_6",
            "sample_id": leaf.sample_id,
            "patch_id": leaf.patch_id,
            "basis": leaf.basis,
            "rounds_label": leaf.rounds_label,
            "dem_source": args.google_dem_source,
            "orbit_mode": args.google_orbit_mode,
        },
        **local_window_workload_audit(batch),
        **local_window_cuda_kernel_audit(
            batch,
            requested_kernel_variant="spectral",
            spectral_memory_cap_bytes=int(args.spectral_memory_cap_mib) * 1024 * 1024,
            scalar_bytes=torch.empty((), dtype=dtype).element_size(),
        ),
        "cpu_pytorch_seconds": cpu_seconds,
        "cuda_dp_seconds": dp_seconds,
        "cuda_spectral_seconds": spectral_seconds,
        "cpu_pytorch_loss": float(cpu_loss.detach().cpu()),
        "cuda_dp_loss": float(dp_loss.detach().cpu()),
        "cuda_spectral_loss": float(spectral_loss.detach().cpu()),
        "dp_vs_cpu_loss_abs_diff": float((dp_loss.detach().cpu() - cpu_loss.detach()).abs()),
        "spectral_vs_cpu_loss_abs_diff": float((spectral_loss.detach().cpu() - cpu_loss.detach()).abs()),
        "spectral_vs_dp_loss_abs_diff": float((spectral_loss.detach() - dp_loss.detach()).abs().cpu()),
        "spectral_vs_dp_grad_max_abs_diff": float((spectral_grad - dp_grad).abs().max().detach().cpu()),
        "spectral_vs_cpu_grad_max_abs_diff": float((spectral_grad.cpu() - cpu_grad).abs().max().detach()),
    }
    return record


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-preset", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--dtype", choices=["float64", "float32"], default="float64")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--spectral-min-abs-factor", type=float, default=1e-6)
    parser.add_argument("--spectral-memory-cap-mib", type=int, default=1024)
    parser.add_argument("--google-dataset-root", default=None)
    parser.add_argument("--google-sample-id", default="sample_00")
    parser.add_argument("--google-patch-id", default="d3_at_q5_5")
    parser.add_argument("--google-basis", default="X")
    parser.add_argument("--google-rounds-label", default="r13")
    parser.add_argument("--google-dem-source", default="decoder_si1000")
    parser.add_argument("--google-orbit-mode", default="fault_graph_heuristic")
    parser.add_argument("--google-shots", type=int, default=2000)
    parser.add_argument("--google-max-window-bits", type=int, default=8)
    parser.add_argument("--google-max-windows", type=int, default=128)
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()

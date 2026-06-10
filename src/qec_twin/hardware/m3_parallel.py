"""K-way process-parallel executor for the M3 window fits (pin P1h).

Scheduling ONLY, never math: each (basis, window, seed, split) task calls the
SAME ``hardware_nll.calibrate_window`` with the SAME registered hyperparameters
and seeds as the sequential ``m3_report.fit_windows`` loop; parallelism shards
the per-window-independent fits (registered: "per-window independent fits")
across worker processes to fill the GPU, which a single sequential launch-bound
LBFGS chain cannot. Finished records land in the canonical fit cache with the
identical key format, so ``m3_report`` / the M3 tests consume them as cached
fits.

Determinism (what makes P1h's "exactly" well-posed): workers AND the P1h
sequential re-check run under ``torch.use_deterministic_algorithms(True)`` +
``CUBLAS_WORKSPACE_CONFIG=:4096:8``, so the 256-bin ``scatter_add`` and cuBLAS
reductions use deterministic implementations and the parallel and
eager-sequential execution modes are bit-comparable. P1h verification
(``--verify M``): after the parallel run, M of the just-fitted tasks are
re-fitted sequentially in the parent process and every record field is
compared bit-exactly (law / q_eff / markov via array equality; scalars by
``==``). Any mismatch exits nonzero — the parallel cache is then NOT to be
used.

Execution mode (``--graph {auto,off,on}``, default ``auto``): forwarded
unchanged to ``calibrate_window`` for BOTH the worker fits and the P1h
sequential verify re-fits, so the two sides of the bit-exact comparison always
run the same mode. ``graph_mode`` is execution-only — a CUDA-graph replay of
the identical eager fit kernels (graph-vs-eager equality pins:
``tests/test_hardware_nll_graph_mode.py``); fits whose burn-in pre-check fails
fall back to eager per fit and are tagged in the log.

    QEC_TWIN_HW_DATA=<parent> python -m qec_twin.hardware.m3_parallel --workers 8
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import numpy as np

DEFAULT_WORKERS = 8
DEFAULT_CACHE = "outputs/m3_fit_cache.pt"
DEFAULT_HIST_DIR = "outputs"


def _enable_determinism() -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    torch.use_deterministic_algorithms(True)


def _fit_threads() -> int:
    """One thread count for workers AND the P1h sequential re-check: on CPU,
    thread count can change reduction order, so bit-exactness demands both
    execution modes use the identical setting."""
    return max(1, (os.cpu_count() or 8) // DEFAULT_WORKERS)


def _hist_path(hist_dir: str, basis: str, split: str) -> Path:
    return Path(hist_dir) / f"m3_hist_{basis}_{split}.npz"


def _fit_one(
    histogram: np.ndarray,
    basis: str,
    window: int,
    seed: int,
    split: str,
    *,
    device: str,
    steps: int,
    max_burn_in: int,
    fp_tol: float,
    graph_mode: str,
):
    """One registered fit; returns ``(FitRecord, execution tag)``. The tag
    ("graph" | "eager" | "eager-fallback") is log-only, never cached math."""
    from qec_twin.calibration import hardware_nll
    from qec_twin.hardware.m3_report import FitRecord

    result = hardware_nll.calibrate_window(
        histogram,
        steps=steps,
        seed=int(seed),
        device=device,
        max_burn_in=max_burn_in,
        fp_tol=fp_tol,
        graph_mode=graph_mode,
    )
    record = FitRecord(
        basis=basis,
        window=int(window),
        seed=int(seed),
        split=split,
        ce_per_block=float(result["ce_per_block"]),
        law=result["block_law"].cpu().numpy(),
        q_eff=result["q_eff"].cpu().numpy(),
        markov=result["markov_pairs"].cpu().numpy(),
        fp_residual=float(result["fp_residual"]),
        fp_rounds=int(result["fp_rounds"]),
    )
    if result["graph_used"]:
        tag = "graph"
    elif result["fallback"]:
        tag = f"eager-fallback ({result['fallback_reason']})"
    else:
        tag = "eager"
    return record, tag


def _atomic_save(obj, path: Path) -> None:
    import torch

    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def _run_tasks(
    rank: int,
    tasks: list,
    hist_dir: str,
    shard_path: str,
    device: str,
    steps: int,
    max_burn_in: int,
    fp_tol: float,
    graph_mode: str,
) -> None:
    """The shared fit loop body (used by both process and thread workers)."""
    from qec_twin.hardware.m3_report import _cache_key

    hist_files: dict = {}
    shard: dict = {}
    for basis, window, seed, split in tasks:
        key = (basis, split)
        if key not in hist_files:
            hist_files[key] = np.load(_hist_path(hist_dir, basis, split))
        data = hist_files[key]
        w_index = int(np.where(data["windows"] == int(window))[0][0])
        t0 = time.perf_counter()
        record, tag = _fit_one(
            data["counts"][w_index], basis, window, seed, split,
            device=device, steps=steps, max_burn_in=max_burn_in, fp_tol=fp_tol,
            graph_mode=graph_mode,
        )
        shard[_cache_key(basis, int(window), int(seed), split)] = record
        _atomic_save(shard, Path(shard_path))
        print(
            f"  [w{rank}] {basis}/w{window}/s{seed}/{split} [{tag}]: CE/block "
            f"{record.ce_per_block:.6f}, fp {record.fp_residual:.2e}@{record.fp_rounds}, "
            f"{time.perf_counter() - t0:.1f}s",
            flush=True,
        )


def _worker(
    rank: int,
    tasks: list,
    hist_dir: str,
    shard_path: str,
    device: str,
    steps: int,
    max_burn_in: int,
    fp_tol: float,
    graph_mode: str,
) -> None:
    """Process-mode worker: own CUDA context (spawn)."""
    _enable_determinism()
    import torch

    torch.set_num_threads(_fit_threads())
    _run_tasks(rank, tasks, hist_dir, shard_path, device, steps, max_burn_in, fp_tol, graph_mode)


def _thread_worker(
    rank: int,
    tasks: list,
    hist_dir: str,
    shard_path: str,
    device: str,
    steps: int,
    max_burn_in: int,
    fp_tol: float,
    graph_mode: str,
    errors: list,
) -> None:
    """Thread-mode worker: ONE shared CUDA context, a private stream per thread.

    Rationale (measured on WSL2, 2026-06-09): the eager closure is sync-bound —
    ~215 `matrix_exp` calls per closure each host-sync, so multiple CUDA
    CONTEXTS time-slice with a context switch per sync and aggregate throughput
    DROPS below sequential. Threads in one context have no context switches:
    while one thread blocks in a sync (GIL released in C++), the others issue
    kernels. Per-fit math is untouched — stream choice and thread interleaving
    cannot change a fit's own kernel sequence or inputs (scheduling only, P1h).
    """
    import torch

    try:
        stream = torch.cuda.Stream() if device == "cuda" else None
        if stream is not None:
            with torch.cuda.stream(stream):
                _run_tasks(rank, tasks, hist_dir, shard_path, device, steps,
                           max_burn_in, fp_tol, graph_mode)
            stream.synchronize()
        else:
            _run_tasks(rank, tasks, hist_dir, shard_path, device, steps,
                       max_burn_in, fp_tol, graph_mode)
    except Exception as exc:  # noqa: BLE001 — reported to the parent loop
        errors.append((rank, repr(exc)))


def _needed_tasks(bases, windows, seeds, splits) -> list:
    return [
        (basis, int(w), int(s), split)
        for basis in bases
        for split in splits
        for w in windows
        for s in seeds
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bases", nargs="+", default=["X", "Z"])
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--max-burn-in", type=int, default=320)
    parser.add_argument("--fp-tol", type=float, default=1e-9)
    parser.add_argument("--splits", nargs="+", default=["full"])
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--hist-dir", default=DEFAULT_HIST_DIR)
    parser.add_argument("--no-hot", action="store_true", help="exclude {15,19} control windows")
    parser.add_argument(
        "--graph", choices=["auto", "off", "on"], default="auto",
        help="calibrate_window execution mode (P1h): CUDA-graph replay (auto/on) or eager (off); "
             "workers and the sequential verify re-fits always use the SAME mode",
    )
    parser.add_argument(
        "--exec", dest="exec_mode", choices=["process", "thread"], default="process",
        help="worker isolation: separate CUDA contexts (process) or one shared context with "
             "a stream per thread (thread; the WSL2 sync-bound regime — see _thread_worker)",
    )
    parser.add_argument("--verify", type=int, default=2, help="P1h: sequential re-fits to compare")
    parser.add_argument("--max-tasks", type=int, default=0, help="smoke: cap the task list")
    args = parser.parse_args(argv)

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch
    import torch.multiprocessing as mp

    from qec_twin.hardware import b8_io, blocks, m1_report
    from qec_twin.hardware.dataset import RepCodeD29
    from qec_twin.hardware.m3_report import TRAIN_SAMPLE, _cache_key

    ds = RepCodeD29.from_env()
    windows = list(blocks.CLEAN_INTERIOR_WINDOWS)
    if not args.no_hot:
        windows += list(blocks.HOT_WINDOWS)

    cache_path = Path(args.cache)
    cache: dict = {}
    if cache_path.exists():
        cache = torch.load(cache_path, weights_only=False)

    tasks = [
        t for t in _needed_tasks(args.bases, windows, args.seeds, args.splits)
        if _cache_key(t[0], t[1], t[2], t[3]) not in cache
    ]
    if args.max_tasks:
        tasks = tasks[: args.max_tasks]
    print(f"tasks: {len(tasks)} to fit ({len(cache)} already cached)", flush=True)

    # Precompute histograms once per (basis, split): one streaming pass each.
    Path(args.hist_dir).mkdir(parents=True, exist_ok=True)
    for basis in args.bases:
        grid = m1_report.build_grid(ds, basis)
        paths = ds.paths(basis, TRAIN_SAMPLE)
        for split in args.splits:
            out = _hist_path(args.hist_dir, basis, split)
            if out.exists():
                continue
            shot_slice = None
            if split == "first_half":
                total = b8_io.num_shots_in_file(
                    paths.detection_events, grid.num_layers * grid.num_chains
                )
                shot_slice = (0, total // 2)
            t0 = time.perf_counter()
            counts = blocks.block_histograms(
                paths.detection_events, grid, windows, shot_slice=shot_slice
            )
            np.savez(out, windows=np.asarray(windows, dtype=np.int64), counts=counts)
            print(f"histograms {basis}/{split}: {time.perf_counter() - t0:.1f}s -> {out}", flush=True)

    if tasks:
        k = max(1, min(args.workers, len(tasks)))
        shards = [Path(args.hist_dir) / f"m3_fit_shard_{r}.pt" for r in range(k)]
        t0 = time.perf_counter()
        failed: list = []
        if args.exec_mode == "thread":
            import threading

            _enable_determinism()
            torch.set_num_threads(1)  # 1 intra-op thread per worker thread; matched by verify
            threads = []
            for r in range(k):
                t = threading.Thread(
                    target=_thread_worker,
                    args=(r, tasks[r::k], args.hist_dir, str(shards[r]), args.device,
                          args.steps, args.max_burn_in, args.fp_tol, args.graph, failed),
                )
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
        else:
            ctx = mp.get_context("spawn")
            procs = []
            for r in range(k):
                assigned = tasks[r::k]  # round-robin: balanced mix of windows/bases
                p = ctx.Process(
                    target=_worker,
                    args=(r, assigned, args.hist_dir, str(shards[r]), args.device,
                          args.steps, args.max_burn_in, args.fp_tol, args.graph),
                )
                p.start()
                procs.append(p)
            for r, p in enumerate(procs):
                p.join()
                if p.exitcode != 0:
                    failed.append((r, p.exitcode))
        wall = time.perf_counter() - t0
        # Merge shards (also on partial failure: keep finished fits).
        merged = 0
        for shard_file in shards:
            if shard_file.exists():
                shard = torch.load(shard_file, weights_only=False)
                cache.update(shard)
                merged += len(shard)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_save(cache, cache_path)
        for shard_file in shards:
            if shard_file.exists():
                shard_file.unlink()
        print(
            f"parallel run: {merged}/{len(tasks)} fits in {wall:.0f}s wall "
            f"({k} workers) -> {cache_path}",
            flush=True,
        )
        if failed:
            print(f"FAILED workers: {failed} — rerun to resume from cache", flush=True)
            return 1

    # ---- P1h: sequential re-fit of a subset, bit-exact record comparison ----
    if args.verify and tasks:
        _enable_determinism()
        torch.set_num_threads(_fit_threads())
        mismatches = []
        for basis, window, seed, split in tasks[: args.verify]:
            data = np.load(_hist_path(args.hist_dir, basis, split))
            w_index = int(np.where(data["windows"] == int(window))[0][0])
            t0 = time.perf_counter()
            seq, tag = _fit_one(
                data["counts"][w_index], basis, window, seed, split,
                device=args.device, steps=args.steps,
                max_burn_in=args.max_burn_in, fp_tol=args.fp_tol,
                graph_mode=args.graph,  # SAME mode as the workers (P1h contract)
            )
            par = cache[_cache_key(basis, int(window), int(seed), split)]
            exact = (
                np.array_equal(seq.law, par.law)
                and np.array_equal(seq.q_eff, par.q_eff)
                and np.array_equal(seq.markov, par.markov)
                and seq.ce_per_block == par.ce_per_block
                and seq.fp_residual == par.fp_residual
                and seq.fp_rounds == par.fp_rounds
            )
            law_gap = float(np.abs(seq.law - par.law).max())
            print(
                f"P1h {basis}/w{window}/s{seed} [{tag}]: bit-exact={exact} "
                f"(law max gap {law_gap:.2e}) seq {time.perf_counter() - t0:.1f}s",
                flush=True,
            )
            if not exact:
                mismatches.append((basis, window, seed, law_gap))
        if mismatches:
            print(f"P1h FAIL: {mismatches}", flush=True)
            return 2
        print("P1h PASS: parallel execution reproduces sequential records bit-exactly", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

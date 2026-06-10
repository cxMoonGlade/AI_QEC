"""R2-lite M3 detector-block extraction on packed events (the F_blk family).

Pre-registration: docs/metric_results.md "2026-06-09 -- R2-lite M3". Per window,
the family is the joint of the window's 4 fully-interior detectors on DISJOINT
2-layer blocks at starts ``t in {80, 82, ..., 998}`` (460 blocks, 3680
bits/shot/window; the transient cut = M1-P6 ~70 + guard). Streaming via
``b8_io.iter_b8_chunks`` (pij.py pattern); a corpus file is never materialized
unpacked.

Window convention (M2): window start ``s`` covers the 6 measure sites
``s..s+5``; its 4 fully-interior detectors are chains ``s+1..s+4``. The 19
clean interior windows are starts ``1..21`` minus the M2-adjudicated hot set
``{15, 19}``.

Bit convention (pinned; identical in forward/exact/steady_state.py, the
readout convolution, and hardware/baselines.py): interior site ``k`` (left to
right within the window), block layer ``l`` (0 = block start ``t``, 1 =
``t+1``), bit index ``2k + l`` -- ``pattern = sum_k (d[k,t] + 2*d[k,t+1]) * 4**k``.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np

from qec_twin.hardware.b8_io import iter_b8_chunks, num_shots_in_file
from qec_twin.hardware.stim_artifacts import DetectorGrid

T_START = 80
T_STOP = 998
STRIDE = 2
WINDOW_SITES = 6
NUM_INTERIOR_DETECTORS = 4
NUM_BLOCK_PATTERNS = 2 ** (2 * NUM_INTERIOR_DETECTORS)
HOT_WINDOWS = (15, 19)  # M2-adjudicated exclusion set (the located (18, 21) pair)
CLEAN_INTERIOR_WINDOWS = tuple(s for s in range(1, 22) if s not in HOT_WINDOWS)


def interior_chains(window_start: int) -> np.ndarray:
    """The window's 4 fully-interior detector chains ``s+1..s+4``."""
    s = int(window_start)
    return np.arange(s + 1, s + 1 + NUM_INTERIOR_DETECTORS)


def block_starts(t_start: int = T_START, t_stop: int = T_STOP, stride: int = STRIDE) -> np.ndarray:
    """The registered disjoint block starts ``{t_start, t_start+stride, ..., t_stop}``."""
    return np.arange(int(t_start), int(t_stop) + 1, int(stride))


def _chunk_block_patterns(
    packed: np.ndarray,
    grid: DetectorGrid,
    windows,
    t0: np.ndarray,
) -> np.ndarray:
    """``[shots, n_windows, n_blocks]`` uint8 patterns for one packed chunk."""
    bits_per_shot = grid.num_layers * grid.num_chains
    bits = np.unpackbits(packed, axis=1, count=bits_per_shot, bitorder="little")
    g = bits[:, grid.grid.ravel()].reshape(bits.shape[0], grid.num_layers, grid.num_chains)
    out = np.zeros((g.shape[0], len(windows), t0.size), dtype=np.uint8)
    for w, start in enumerate(windows):
        cols = interior_chains(start)
        d0 = g[:, t0][:, :, cols]  # [shots, n_blocks, 4]
        d1 = g[:, t0 + 1][:, :, cols]
        pat = np.zeros((g.shape[0], t0.size), dtype=np.uint8)
        for k in range(NUM_INTERIOR_DETECTORS):
            pat |= (d0[:, :, k] << (2 * k)) | (d1[:, :, k] << (2 * k + 1))
        out[:, w] = pat
    return out


def block_histograms_from_chunks(
    chunks: Iterable[tuple[int, np.ndarray]],
    grid: DetectorGrid,
    windows,
    *,
    t_start: int = T_START,
    t_stop: int = T_STOP,
    stride: int = STRIDE,
) -> np.ndarray:
    """``[n_windows, 256]`` int64 pattern counts from packed-event chunks.

    The SINGLE extractor for every arm (device data, naive stim MC) -- the M3
    pipeline-identity pin (P1d) holds by construction for anything routed here.
    """
    t0 = block_starts(t_start, t_stop, stride)
    hist = np.zeros((len(windows), NUM_BLOCK_PATTERNS), dtype=np.int64)
    for _, packed in chunks:
        patterns = _chunk_block_patterns(packed, grid, windows, t0)
        for w in range(len(windows)):
            hist[w] += np.bincount(
                patterns[:, w].ravel().astype(np.int64), minlength=NUM_BLOCK_PATTERNS
            )
    return hist


def block_histograms(
    events_path: Path | str,
    grid: DetectorGrid,
    windows,
    *,
    t_start: int = T_START,
    t_stop: int = T_STOP,
    stride: int = STRIDE,
    shot_slice=None,
    chunk_shots: int = 10_000,
) -> np.ndarray:
    """``[n_windows, 256]`` int64 block-pattern histograms of a ``.b8`` events file."""
    bits_per_shot = grid.num_layers * grid.num_chains
    chunks = iter_b8_chunks(events_path, bits_per_shot, chunk_shots=chunk_shots, shot_slice=shot_slice)
    return block_histograms_from_chunks(
        chunks, grid, windows, t_start=t_start, t_stop=t_stop, stride=stride
    )


def per_shot_block_nll_multi(
    events_path: Path | str,
    grid: DetectorGrid,
    windows,
    log_p: np.ndarray,
    *,
    t_start: int = T_START,
    t_stop: int = T_STOP,
    stride: int = STRIDE,
    shot_slice=None,
    chunk_shots: int = 10_000,
) -> np.ndarray:
    """Per-shot block NLL for several windows (and optionally several models).

    ``log_p`` is ``[n_windows, 256]`` (returns ``[shots, n_windows]``) or
    ``[n_models, n_windows, 256]`` (returns ``[shots, n_models, n_windows]``);
    the per-shot value is ``-sum_blocks log p(pattern)`` -- the registered
    composite marginal likelihood, in nats/shot/window. One streaming pass
    scores every model on identical patterns (the paired-bootstrap input).
    """
    log_p = np.asarray(log_p, dtype=np.float64)
    squeeze = log_p.ndim == 2
    if squeeze:
        log_p = log_p[None]
    if log_p.shape[1] != len(windows) or log_p.shape[2] != NUM_BLOCK_PATTERNS:
        raise ValueError(f"log_p shape {log_p.shape} does not match {len(windows)} windows")
    bits_per_shot = grid.num_layers * grid.num_chains
    total = num_shots_in_file(events_path, bits_per_shot)
    if shot_slice is not None:
        start, stop = (shot_slice.indices(total)[:2] if isinstance(shot_slice, slice)
                       else (int(shot_slice[0]), int(shot_slice[1])))
        total = stop - start
    t0 = block_starts(t_start, t_stop, stride)
    out = np.zeros((total, log_p.shape[0], len(windows)), dtype=np.float64)
    seen = 0
    for _, packed in iter_b8_chunks(
        events_path, bits_per_shot, chunk_shots=chunk_shots, shot_slice=shot_slice
    ):
        patterns = _chunk_block_patterns(packed, grid, windows, t0)  # [n, W, B]
        n = patterns.shape[0]
        for w in range(len(windows)):
            pat = patterns[:, w].astype(np.int64)
            for m in range(log_p.shape[0]):
                out[seen : seen + n, m, w] = -log_p[m, w][pat].sum(axis=1)
        seen += n
    if seen != total:
        raise ValueError(f"saw {seen} shots, expected {total}")
    return out[:, 0, :] if squeeze else out


def per_shot_block_nll(
    events_path: Path | str,
    grid: DetectorGrid,
    window: int,
    log_p: np.ndarray,
    *,
    t_start: int = T_START,
    t_stop: int = T_STOP,
    stride: int = STRIDE,
    shot_slice=None,
    chunk_shots: int = 10_000,
) -> np.ndarray:
    """``[shots]`` per-shot block NLL of one window under one model's ``log_p[256]``."""
    out = per_shot_block_nll_multi(
        events_path,
        grid,
        [int(window)],
        np.asarray(log_p, dtype=np.float64)[None, :],
        t_start=t_start,
        t_stop=t_stop,
        stride=stride,
        shot_slice=shot_slice,
        chunk_shots=chunk_shots,
    )
    return out[:, 0]

"""Detection-event fractions on packed events (METRICS.md hardware ledger).

Layer-resolved firing fractions, the layer-0 / bulk / final split, shot-level
bootstrap SEs/CIs (shots are the iid units; within-shot detector correlation
forbids naive binomial errors), and the bulk time profile with burst-outlier
flagging (outliers reported, excluded from the flatness statistic).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from qec_twin.hardware.b8_io import DEFAULT_CHUNK_SHOTS, iter_b8_chunks, num_shots_in_file
from qec_twin.hardware.stim_artifacts import DetectorGrid

M1_BOOTSTRAP_SEED = 20260609
BOOTSTRAP_REPLICATES = 1000


@dataclass(frozen=True)
class DetectionStats:
    num_shots: int
    num_layers: int
    num_chains: int
    per_layer_fraction: np.ndarray  # [L] mean firing fraction per detector layer
    per_detector_fraction: np.ndarray  # [L, C] grid-resolved firing fraction
    layer0_fraction: float
    bulk_fraction: float  # layers 1..L-2 inclusive (the 1000 bulk layers)
    final_fraction: float
    per_shot_layer0: np.ndarray  # [N] fired-detector counts (bootstrap units)
    per_shot_bulk: np.ndarray  # [N]
    per_shot_final: np.ndarray  # [N]


def detection_stats_from_chunks(
    chunks: Iterable[tuple[int, np.ndarray]],
    grid: DetectorGrid,
    *,
    num_shots: int,
) -> DetectionStats:
    layers, chains = grid.num_layers, grid.num_chains
    grid_flat = grid.grid.ravel()
    det_counts = np.zeros(layers * chains, dtype=np.int64)
    per_shot_layer0 = np.zeros(num_shots, dtype=np.int32)
    per_shot_bulk = np.zeros(num_shots, dtype=np.int32)
    per_shot_final = np.zeros(num_shots, dtype=np.int32)

    seen = 0
    for start, packed in chunks:
        bits = np.unpackbits(packed, axis=1, count=layers * chains, bitorder="little")
        g = bits[:, grid_flat].reshape(bits.shape[0], layers, chains)
        det_counts += g.reshape(g.shape[0], -1).sum(axis=0, dtype=np.int64)
        layer_counts = g.sum(axis=2, dtype=np.int32)
        stop = start + g.shape[0]
        per_shot_layer0[start:stop] = layer_counts[:, 0]
        per_shot_final[start:stop] = layer_counts[:, -1]
        per_shot_bulk[start:stop] = layer_counts[:, 1:-1].sum(axis=1, dtype=np.int32)
        seen += g.shape[0]
    if seen != num_shots:
        raise ValueError(f"saw {seen} shots, expected {num_shots}")

    per_detector = det_counts.reshape(layers, chains) / float(num_shots)
    per_layer = per_detector.mean(axis=1)
    bulk_denominator = float(num_shots) * chains * (layers - 2)
    return DetectionStats(
        num_shots=int(num_shots),
        num_layers=layers,
        num_chains=chains,
        per_layer_fraction=per_layer,
        per_detector_fraction=per_detector,
        layer0_fraction=float(per_shot_layer0.sum(dtype=np.int64)) / (float(num_shots) * chains),
        bulk_fraction=float(per_shot_bulk.sum(dtype=np.int64)) / bulk_denominator,
        final_fraction=float(per_shot_final.sum(dtype=np.int64)) / (float(num_shots) * chains),
        per_shot_layer0=per_shot_layer0,
        per_shot_bulk=per_shot_bulk,
        per_shot_final=per_shot_final,
    )


def detection_stats_from_file(
    events_path: Path | str,
    grid: DetectorGrid,
    *,
    chunk_shots: int = DEFAULT_CHUNK_SHOTS,
) -> DetectionStats:
    bits_per_shot = grid.num_layers * grid.num_chains
    num_shots = num_shots_in_file(events_path, bits_per_shot)
    chunks = iter_b8_chunks(events_path, bits_per_shot, chunk_shots=chunk_shots)
    return detection_stats_from_chunks(chunks, grid, num_shots=num_shots)


def detection_stats_from_sampler(
    circuit,
    grid: DetectorGrid,
    *,
    shots: int,
    seed: int,
    chunk_shots: int = DEFAULT_CHUNK_SHOTS,
) -> DetectionStats:
    """MC detection stats of a stim circuit (P8), streamed bit-packed."""

    sampler = circuit.compile_detector_sampler(seed=int(seed))

    def chunks():
        start = 0
        while start < shots:
            take = min(int(chunk_shots), shots - start)
            yield start, np.asarray(sampler.sample(take, bit_packed=True), dtype=np.uint8)
            start += take

    return detection_stats_from_chunks(chunks(), grid, num_shots=int(shots))


def bootstrap_mean_replicates(
    per_shot: np.ndarray,
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = M1_BOOTSTRAP_SEED,
) -> np.ndarray:
    """Shot-level bootstrap replicate means; per_shot is [N] or [N, k]."""

    x = np.asarray(per_shot, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    n = x.shape[0]
    rng = np.random.default_rng(int(seed))
    out = np.empty((int(replicates), x.shape[1]), dtype=np.float64)
    for b in range(int(replicates)):
        idx = rng.integers(0, n, size=n)
        out[b] = x[idx].mean(axis=0)
    return out


def bootstrap_se(replicate_means: np.ndarray) -> np.ndarray:
    return np.asarray(replicate_means, dtype=np.float64).std(axis=0, ddof=1)


def percentile_ci(replicate_means: np.ndarray, *, alpha: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    r = np.asarray(replicate_means, dtype=np.float64)
    lo = np.quantile(r, alpha / 2.0, axis=0)
    hi = np.quantile(r, 1.0 - alpha / 2.0, axis=0)
    return lo, hi


@dataclass(frozen=True)
class FlatnessReport:
    """Bulk time-profile flatness; burst outliers flagged via median ± sigma·(1.4826 MAD),
    reported and EXCLUDED from the flatness statistic (pre-registration P6)."""

    window: tuple[int, int]  # inclusive layer range entering the statistic
    mean_fraction: float
    rel_std: float  # std/mean over non-outlier window layers
    outlier_sigma: float
    outlier_layers: tuple[int, ...]
    outlier_fractions: tuple[float, ...]


def bulk_flatness(
    per_layer_fraction: np.ndarray,
    *,
    window: tuple[int, int] = (2, 999),
    outlier_sigma: float = 5.0,
) -> FlatnessReport:
    lo, hi = int(window[0]), int(window[1])
    values = np.asarray(per_layer_fraction, dtype=np.float64)[lo : hi + 1]
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if scale <= 0.0:
        outlier_mask = np.zeros(values.size, dtype=bool)
    else:
        outlier_mask = np.abs(values - median) > outlier_sigma * scale
    kept = values[~outlier_mask]
    mean = float(kept.mean())
    rel_std = float(kept.std(ddof=1) / mean) if mean > 0 else float("nan")
    outlier_layers = tuple(int(i) + lo for i in np.nonzero(outlier_mask)[0])
    return FlatnessReport(
        window=(lo, hi),
        mean_fraction=mean,
        rel_std=rel_std,
        outlier_sigma=float(outlier_sigma),
        outlier_layers=outlier_layers,
        outlier_fractions=tuple(float(v) for v in values[outlier_mask]),
    )

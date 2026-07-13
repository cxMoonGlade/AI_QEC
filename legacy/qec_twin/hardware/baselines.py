"""R2-lite M3 pinned baseline arms: the pij-DEM block model and the naive stim MC.

Pre-registration: docs/metric_results.md "2026-06-09 -- R2-lite M3" (Baselines,
PINNED). Both arms emit a 256-bin law over the SAME registered block family as
the twin (hardware/blocks.py bit convention), so the three arms are scored on
an identical object.

pij arm: train-split Spitz-EXACT entries (the ledgered Eq. 13 exact form,
hardware/pij.py) on layer-pooled moments over ``[80, 999]``; in-block edge set
``{dt=0: di<=3} U {dt=1: di<=2}`` over the block's 8 detector nodes (12 + 14 =
26 edges -- the dt=1 set carries the time-like di=0 and both diagonal
orientations); entries clamped to ``[0, 1/2)``; per-node mean-matching
half-edges (singles chosen so the folded model marginal reproduces the
measured pooled ``f`` EXACTLY -- out-of-block mass is absorbed there); exact
256-cell law as the XOR/Walsh-Hadamard product of the independent Bernoulli
edge folds.

naive arm: stim detector-sample MC of ``circuit_noisy_si1000.stim`` (1e5
shots, seed 20260609) routed through the IDENTICAL grid/window/block extractor
as the device data, Krichevsky-Trofimov smoothed ``(count + 1/2)/(N + 128)``
to the 256-bin law.

A1 budget-rescaled pij arm (``budget_rescale=True``; M3 ADDENDUM
PRE-REGISTRATION, docs/metric_results.md): BEFORE mean-matching, every
in-block edge mass is scaled by ONE per-window factor
``s_W = min(1, min_i s*_i)``, where ``s*_i`` is the unique root in (0, 1] of
``prod_{e ni i} (1 - 2 s p_e) = 1 - 2 f_i`` over the 8 block nodes (bisection
to ``NUMERICAL_ZERO``; ``s*_i = 1`` when even ``s = 1`` keeps the product
``>= 1 - 2 f_i``) -- the minimal uniform shrinkage making the registered
mean-matching half-edges feasible (>= 0) at every node, i.e. the
budget-consistent member of the SAME independent-edges family. Mean-matching
then proceeds exactly as the pinned arm (feasibility is asserted loudly).
``f_i`` is the same per-node pooled marginal the mean-matching uses. The
default (flag-off) path is byte-identical to the pinned M3 arm.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from qec_twin.hardware.b8_io import iter_b8_chunks
from qec_twin.hardware.blocks import (
    NUM_BLOCK_PATTERNS,
    NUM_INTERIOR_DETECTORS,
    STRIDE,
    T_START,
    T_STOP,
    block_histograms_from_chunks,
    interior_chains,
)
from qec_twin.hardware.pij import spitz_pij_exact
from qec_twin.hardware.stim_artifacts import DetectorGrid, load_circuit
from qec_twin.numerics import NUMERICAL_ZERO

NAIVE_MC_SHOTS = 100_000
NAIVE_MC_SEED = 20260609
LAYER_LO = 80
LAYER_HI = 999
KT_HALF_CELLS = NUM_BLOCK_PATTERNS / 2.0  # 128: KT adds 1/2 per cell

# Pooled pair classes needed by the in-block edge set (and the P10 deficit):
# (di, dt, orient) in pij.py's orientation convention.
POOLED_CLASSES = (
    (1, 0, 0),
    (2, 0, 0),
    (3, 0, 0),
    (0, 1, 0),
    (1, 1, 1),
    (1, 1, -1),
    (2, 1, 1),
    (2, 1, -1),
)


@dataclass(frozen=True)
class PooledBlockMoments:
    """Layer-pooled per-pair moment planes over the bulk block (train split)."""

    num_shots: int
    layer_lo: int
    layer_hi: int
    marg: np.ndarray  # [L_pool, C] mean firing per (layer, chain)
    joint: dict  # (di, dt, orient) -> [L_pool - dt, C - di] mean AND plane


def pooled_block_moments(
    events_path: Path | str,
    grid: DetectorGrid,
    *,
    layer_lo: int = LAYER_LO,
    layer_hi: int = LAYER_HI,
    shot_slice=None,
    chunk_shots: int = 10_000,
) -> PooledBlockMoments:
    """One streaming pass accumulating marginal + joint planes for all chains."""
    bits_per_shot = grid.num_layers * grid.num_chains
    lo, hi = int(layer_lo), int(layer_hi)
    l_pool = hi - lo + 1
    chains = grid.num_chains
    marg = np.zeros((l_pool, chains), dtype=np.int64)
    joint = {
        key: np.zeros((l_pool - key[1], chains - key[0]), dtype=np.int64)
        for key in POOLED_CLASSES
    }
    num_shots = 0
    for _, packed in iter_b8_chunks(
        events_path, bits_per_shot, chunk_shots=chunk_shots, shot_slice=shot_slice
    ):
        bits = np.unpackbits(packed, axis=1, count=bits_per_shot, bitorder="little")
        g = bits[:, grid.grid.ravel()].reshape(bits.shape[0], grid.num_layers, chains)
        x = g[:, lo : hi + 1]
        num_shots += x.shape[0]
        marg += x.sum(axis=0, dtype=np.int64)
        for di, dt, orient in POOLED_CLASSES:
            rows = l_pool - dt
            if orient >= 0:
                a = x[:, :rows, : chains - di] & x[:, dt:, di:]
            else:
                a = x[:, dt:, : chains - di] & x[:, :rows, di:]
            joint[(di, dt, orient)] += a.sum(axis=0, dtype=np.int64)
    n = float(num_shots)
    return PooledBlockMoments(
        num_shots=num_shots,
        layer_lo=lo,
        layer_hi=hi,
        marg=marg / n,
        joint={key: plane / n for key, plane in joint.items()},
    )


def pooled_pair_entry(
    moments: PooledBlockMoments, di: int, dt: int, orient: int, chain: int
) -> float:
    """Spitz-exact entry from the LAYER-POOLED moments of one (site-pair, class)."""
    rows = (moments.layer_hi - moments.layer_lo + 1) - dt
    c = int(chain)
    if orient >= 0:
        mi = moments.marg[:rows, c].mean()
        mj = moments.marg[dt:, c + di].mean()
    else:
        mi = moments.marg[dt:, c].mean()
        mj = moments.marg[:rows, c + di].mean()
    mij = moments.joint[(di, dt, orient)][:, c].mean()
    return float(spitz_pij_exact(np.float64(mi), np.float64(mj), np.float64(mij)))


def pooled_site_fraction(moments: PooledBlockMoments, chain: int) -> float:
    return float(moments.marg[:, int(chain)].mean())


def in_block_edges() -> tuple:
    """The PINNED in-block edge set over the 8 nodes ``(site k, layer l)``.

    Returns ``(node1, node2, (di, dt, orient), k_left)`` tuples; node bit
    index is ``2k + l`` (blocks.py convention).
    """
    edges = []
    for layer in (0, 1):
        for di in (1, 2, 3):
            for k in range(NUM_INTERIOR_DETECTORS - di):
                edges.append(((k, layer), (k + di, layer), (di, 0, 0), k))
    for k in range(NUM_INTERIOR_DETECTORS):
        edges.append(((k, 0), (k, 1), (0, 1, 0), k))
    for di in (1, 2):
        for k in range(NUM_INTERIOR_DETECTORS - di):
            edges.append(((k, 0), (k + di, 1), (di, 1, 1), k))
            edges.append(((k, 1), (k + di, 0), (di, 1, -1), k))
    return tuple(edges)


def _node_bit(node: tuple) -> int:
    k, layer = node
    return 2 * int(k) + int(layer)


_PARITY = np.zeros(NUM_BLOCK_PATTERNS, dtype=np.int64)
for _v in range(NUM_BLOCK_PATTERNS):
    _PARITY[_v] = bin(_v).count("1") & 1


def xor_fold_law(edge_p: dict, singles: np.ndarray) -> np.ndarray:
    """Exact 256-cell law of independent Bernoulli edge/single flips (WHT product).

    For character ``S``: ``E[chi_S] = prod_nodes (1-2s)^{S_b} *
    prod_edges (1-2p)^{S_b1 XOR S_b2}``; the law is the inverse WHT.
    """
    s_idx = np.arange(NUM_BLOCK_PATTERNS)
    coeff = np.ones(NUM_BLOCK_PATTERNS, dtype=np.float64)
    for b, s in enumerate(np.asarray(singles, dtype=np.float64)):
        coeff *= np.where((s_idx >> b) & 1, 1.0 - 2.0 * s, 1.0)
    for (n1, n2), p in edge_p.items():
        b1, b2 = _node_bit(n1), _node_bit(n2)
        coeff *= np.where(((s_idx >> b1) ^ (s_idx >> b2)) & 1, 1.0 - 2.0 * p, 1.0)
    z = np.arange(NUM_BLOCK_PATTERNS)
    signs = 1.0 - 2.0 * _PARITY[z[:, None] & s_idx[None, :]]
    law = signs @ coeff / float(NUM_BLOCK_PATTERNS)
    return np.clip(law, 0.0, None)


def _budget_shrink_factor(edge_p: dict, node_f: dict) -> tuple:
    """A1 shrink factor ``(s_W, binding node, ((node, s*_i), ...))``.

    ``s*_i`` is the unique root in (0, 1] of
    ``prod_{e ni i} (1 - 2 s p_e) = 1 - 2 f_i`` (strictly decreasing in ``s``
    wherever an incident ``p_e > 0``); a node where even ``s = 1`` keeps the
    product ``>= 1 - 2 f_i`` never binds, so ``s*_i = 1`` there. Bisection to
    interval width ``NUMERICAL_ZERO`` returns the FEASIBLE (lower) bracket
    end, and the product uses the identical float form ``1 - 2 (s p)`` and the
    identical edge iteration order as the mean-matching loop, so the returned
    ``s_W = min(1, min_i s*_i)`` satisfies every node inequality as evaluated.
    """

    def product_at(s: float, incident: list) -> float:
        prod = 1.0
        for p in incident:
            prod *= 1.0 - 2.0 * (s * p)
        return prod

    s_star: dict = {}
    for node, f_node in node_f.items():
        b = _node_bit(node)
        incident = [
            p for (n1, n2), p in edge_p.items() if _node_bit(n1) == b or _node_bit(n2) == b
        ]
        target = 1.0 - 2.0 * f_node
        if product_at(1.0, incident) >= target:
            s_star[node] = 1.0
            continue
        lo, hi = 0.0, 1.0  # invariant: product_at(lo) >= target > product_at(hi)
        while hi - lo > NUMERICAL_ZERO:
            mid = 0.5 * (lo + hi)
            if product_at(mid, incident) >= target:
                lo = mid
            else:
                hi = mid
        s_star[node] = lo
    s_w = min(1.0, min(s_star.values()))
    binding = min(s_star, key=s_star.get) if s_w < 1.0 else None
    return s_w, binding, tuple(s_star.items())


@dataclass(frozen=True)
class PijBlockModel:
    window: int
    edge_p: dict  # (node1, node2) -> clamped pooled Spitz entry (A1: scaled by s_w)
    singles: np.ndarray  # [8] mean-matching half-edges
    law: np.ndarray  # [256]
    drop_diagonal_edges: bool
    clipped_edges: tuple  # edges whose raw entry left [0, 1/2)
    clipped_singles: tuple  # nodes whose solved single left [0, 1/2)
    budget_rescale: bool = False  # the A1 arm (M3 addendum registration)
    s_w: float | None = None  # A1: uniform in-block shrink min(1, min_i s*_i)
    s_w_node: tuple | None = None  # A1: binding node (k, layer); None when s_w == 1
    s_star: tuple = ()  # A1: ((k, layer), s*_i) over the 8 block nodes


def pij_block_model(
    moments_or_events,
    grid: DetectorGrid,
    window: int,
    *,
    layer_lo: int = LAYER_LO,
    layer_hi: int = LAYER_HI,
    shot_slice=None,
    chunk_shots: int = 10_000,
    drop_diagonal_edges: bool = False,
    budget_rescale: bool = False,
) -> PijBlockModel:
    """The PINNED pij arm for one window (``drop_diagonal_edges`` = the P4
    attribution ablation: removes the ``dt=1, di>=1`` diagonal edges).

    ``budget_rescale`` = the A1 arm (M3 addendum registration, module
    docstring): all in-block edge masses are scaled by the per-window uniform
    ``s_W`` BEFORE the unchanged mean-matching, which is then feasible
    (>= 0) at every node by construction -- violations raise loudly.
    """
    if isinstance(moments_or_events, PooledBlockMoments):
        moments = moments_or_events
    else:
        moments = pooled_block_moments(
            moments_or_events,
            grid,
            layer_lo=layer_lo,
            layer_hi=layer_hi,
            shot_slice=shot_slice,
            chunk_shots=chunk_shots,
        )
    chains = interior_chains(window)
    edge_p: dict = {}
    clipped_edges = []
    for n1, n2, (di, dt, orient), k_left in in_block_edges():
        if drop_diagonal_edges and dt == 1 and di >= 1:
            continue
        raw = pooled_pair_entry(moments, di, dt, orient, int(chains[k_left]))
        clamped = float(np.clip(raw, 0.0, 0.5 - NUMERICAL_ZERO))
        if raw != clamped:
            clipped_edges.append((n1, n2, raw))
        edge_p[(n1, n2)] = clamped

    s_w = None
    s_w_node = None
    s_star: tuple = ()
    if budget_rescale:
        # f per node = the SAME pooled marginal the mean-matching below uses
        # (layer-pooled, so both layers of interior site k share one value).
        node_f = {
            (k, layer): pooled_site_fraction(moments, int(chains[k]))
            for k in range(NUM_INTERIOR_DETECTORS)
            for layer in (0, 1)
        }
        s_w, s_w_node, s_star = _budget_shrink_factor(edge_p, node_f)
        edge_p = {pair: s_w * p for pair, p in edge_p.items()}

    singles = np.zeros(2 * NUM_INTERIOR_DETECTORS, dtype=np.float64)
    clipped_singles = []
    for k in range(NUM_INTERIOR_DETECTORS):
        f_site = pooled_site_fraction(moments, int(chains[k]))
        for layer in (0, 1):
            b = 2 * k + layer
            prod = 1.0
            for (n1, n2), p in edge_p.items():
                if _node_bit(n1) == b or _node_bit(n2) == b:
                    prod *= 1.0 - 2.0 * p
            raw = 0.5 * (1.0 - (1.0 - 2.0 * f_site) / prod)
            if budget_rescale and raw < 0.0:
                raise AssertionError(
                    f"A1 budget rescale: infeasible half-edge {raw:.3e} at node "
                    f"{(k, layer)} of window {window} despite s_W = {s_w!r} -- "
                    "the registered shrink-factor construction is violated"
                )
            clamped = float(np.clip(raw, 0.0, 0.5 - NUMERICAL_ZERO))
            if raw != clamped:
                clipped_singles.append(((k, layer), raw))
            singles[b] = clamped

    return PijBlockModel(
        window=int(window),
        edge_p=edge_p,
        singles=singles,
        law=xor_fold_law(edge_p, singles),
        drop_diagonal_edges=bool(drop_diagonal_edges),
        clipped_edges=tuple(clipped_edges),
        clipped_singles=tuple(clipped_singles),
        budget_rescale=bool(budget_rescale),
        s_w=s_w,
        s_w_node=s_w_node,
        s_star=s_star,
    )


def kt_smooth(histogram: np.ndarray) -> np.ndarray:
    """Krichevsky-Trofimov ``(count + 1/2)/(N + 128)`` law from a 256-bin histogram."""
    hist = np.asarray(histogram, dtype=np.float64)
    return (hist + 0.5) / (hist.sum() + KT_HALF_CELLS)


def naive_block_histograms(
    circuit_noisy_path: Path | str,
    grid: DetectorGrid,
    windows,
    *,
    shots: int = NAIVE_MC_SHOTS,
    seed: int = NAIVE_MC_SEED,
    chunk_shots: int = 10_000,
    t_start: int = T_START,
    t_stop: int = T_STOP,
    stride: int = STRIDE,
) -> np.ndarray:
    """``[n_windows, 256]`` stim-MC histograms through the IDENTICAL extractor."""
    circuit = load_circuit(circuit_noisy_path)  # stim imported lazily inside
    sampler = circuit.compile_detector_sampler(seed=int(seed))

    def chunks():
        start = 0
        while start < int(shots):
            take = min(int(chunk_shots), int(shots) - start)
            yield start, np.asarray(sampler.sample(take, bit_packed=True), dtype=np.uint8)
            start += take

    return block_histograms_from_chunks(
        chunks(), grid, windows, t_start=t_start, t_stop=t_stop, stride=stride
    )


def naive_block_model(
    circuit_noisy_path: Path | str,
    grid: DetectorGrid,
    window: int,
    *,
    shots: int = NAIVE_MC_SHOTS,
    seed: int = NAIVE_MC_SEED,
    chunk_shots: int = 10_000,
    t_start: int = T_START,
    t_stop: int = T_STOP,
    stride: int = STRIDE,
) -> np.ndarray:
    """``[256]`` KT-smoothed naive-MC law for one window (the pinned naive arm)."""
    hist = naive_block_histograms(
        circuit_noisy_path,
        grid,
        [int(window)],
        shots=shots,
        seed=seed,
        chunk_shots=chunk_shots,
        t_start=t_start,
        t_stop=t_stop,
        stride=stride,
    )
    return kt_smooth(hist[0])

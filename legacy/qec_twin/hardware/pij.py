"""Spitz Eq. 13 EXACT two-point ``p_ij`` on packed detection events.

Pre-registered pair set (docs/metric_results.md 2026-06-09): ``|Δt|<=5`` same
chain index ∪ ``|Δi|<=5`` same layer ∪ the ``|Δi|<=2 x |Δt|<=2`` diagonal block
∪ 1e4 seeded random far pairs. Classes aggregate by
``(|Δi|, |Δt|, diagonal orientation, boundary flag)``.

Statistics: shots are the iid units. Class-mean SEs come from a shot-level
bootstrap (B=1000) of the first-order (delta-method) per-shot projection of the
class mean — within-shot cross-pair correlation is carried exactly; per-entry
SEs are analytic delta-method from the exact trinomial moment covariance.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from qec_twin.numerics import NUMERICAL_ZERO
from qec_twin.hardware.b8_io import iter_b8_chunks, num_shots_in_file
from qec_twin.hardware.stim_artifacts import DetectorGrid

M1_FAR_PAIR_SEED = 20260609
M1_PIJ_BOOTSTRAP_SEED = 20260609
NUM_FAR_PAIRS = 10_000
TIME_MAX_DT = 5
SPACE_MAX_DI = 5
BLOCK_MAX = 2
FAR_CLASS = "far"

PairClassKey = "tuple[int, int, int] | str"


def spitz_pij_exact(mean_i: np.ndarray, mean_j: np.ndarray, mean_joint: np.ndarray) -> np.ndarray:
    """Spitz et al. arXiv:1712.02360 **Eq. 13, EXACT form** (METRICS.md ledger):

        p_ij = 1/2 - sqrt(1/4 - cov(x_i, x_j) / (1 - 2<x_i XOR x_j>))

    with ``cov = <x_i x_j> - <x_i><x_j>`` and ``<x_i XOR x_j> = <x_i> + <x_j>
    - 2<x_i x_j>``. The common ``cov / ((1-2<x_i>)(1-2<x_j>))`` form is this
    expression's leading-order small-p approximation — not used here.

    Convention caveats (carried with every number): two-point only — the
    estimator is **structurally blind to hyperedges** (Takou–Brown
    arXiv:2504.20212); negative outputs are meaningful sampling noise around
    null pairs and are NOT floored.
    """

    mi = np.asarray(mean_i, dtype=np.float64)
    mj = np.asarray(mean_j, dtype=np.float64)
    mij = np.asarray(mean_joint, dtype=np.float64)
    cov = mij - mi * mj
    denom = 1.0 - 2.0 * (mi + mj - 2.0 * mij)
    radicand = 0.25 - cov / denom
    return 0.5 - np.sqrt(np.clip(radicand, 0.0, None))


def _pij_gradients(mi: np.ndarray, mj: np.ndarray, mij: np.ndarray):
    """d p_ij / d(<x_i>, <x_j>, <x_i x_j>) for the exact Eq. 13 form."""

    cov = mij - mi * mj
    denom = 1.0 - 2.0 * (mi + mj - 2.0 * mij)
    g = cov / denom
    root = np.sqrt(np.clip(0.25 - g, NUMERICAL_ZERO, None))
    d2 = denom * denom
    common = 1.0 / (2.0 * root)
    gi = common * (-mj * denom + 2.0 * cov) / d2
    gj = common * (-mi * denom + 2.0 * cov) / d2
    gij = common * (denom - 4.0 * cov) / d2
    return gi, gj, gij


def spitz_pij_delta_se(
    mean_i: np.ndarray, mean_j: np.ndarray, mean_joint: np.ndarray, num_shots: int
) -> np.ndarray:
    """Per-entry delta-method SE from the exact per-shot moment covariance."""

    mi = np.asarray(mean_i, dtype=np.float64)
    mj = np.asarray(mean_j, dtype=np.float64)
    mij = np.asarray(mean_joint, dtype=np.float64)
    gi, gj, gij = _pij_gradients(mi, mj, mij)
    var_i = mi * (1.0 - mi)
    var_j = mj * (1.0 - mj)
    var_ij = mij * (1.0 - mij)
    cov_i_j = mij - mi * mj
    cov_i_ij = mij * (1.0 - mi)
    cov_j_ij = mij * (1.0 - mj)
    variance = (
        gi * gi * var_i
        + gj * gj * var_j
        + gij * gij * var_ij
        + 2.0 * gi * gj * cov_i_j
        + 2.0 * gi * gij * cov_i_ij
        + 2.0 * gj * gij * cov_j_ij
    )
    return np.sqrt(np.clip(variance, 0.0, None) / float(num_shots))


def structured_class_keys() -> tuple:
    keys = [(0, dt, 0) for dt in range(1, TIME_MAX_DT + 1)]
    keys += [(di, 0, 0) for di in range(1, SPACE_MAX_DI + 1)]
    keys += [
        (di, dt, orient)
        for di in range(1, BLOCK_MAX + 1)
        for dt in range(1, BLOCK_MAX + 1)
        for orient in (1, -1)
    ]
    return tuple(keys)


def null_class_keys() -> tuple:
    """Pre-registered null classes: ``|Δi|>=2 or |Δt|>=2`` (plus the far set)."""

    keys = [k for k in structured_class_keys() if max(k[0], k[1]) >= 2]
    return tuple(keys) + (FAR_CLASS,)


def _class_slices(key, layers: int, chains: int):
    di, dt, orient = key
    if di == 0:
        return (slice(0, layers - dt), slice(0, chains)), (slice(dt, layers), slice(0, chains))
    if dt == 0:
        return (slice(0, layers), slice(0, chains - di)), (slice(0, layers), slice(di, chains))
    if orient > 0:
        return (slice(0, layers - dt), slice(0, chains - di)), (slice(dt, layers), slice(di, chains))
    return (slice(dt, layers), slice(0, chains - di)), (slice(0, layers - dt), slice(di, chains))


def _boundary_mask(key, layers: int, chains: int) -> np.ndarray:
    (s1, s2) = _class_slices(key, layers, chains)
    l1 = np.arange(layers)[s1[0]]
    l2 = np.arange(layers)[s2[0]]
    c1 = np.arange(chains)[s1[1]]
    c2 = np.arange(chains)[s2[1]]
    layer_edge = np.isin(l1, (0, layers - 1)) | np.isin(l2, (0, layers - 1))
    chain_edge = np.isin(c1, (0, chains - 1)) | np.isin(c2, (0, chains - 1))
    return layer_edge[:, None] | chain_edge[None, :]


def build_far_pairs(
    grid: DetectorGrid, *, num_pairs: int = NUM_FAR_PAIRS, seed: int = M1_FAR_PAIR_SEED
) -> np.ndarray:
    """Seeded random detector pairs OUTSIDE the structured near set, ``[F, 2]``."""

    rng = np.random.default_rng(int(seed))
    num_detectors = grid.det_to_layer.size
    chain = grid.det_to_chain
    layer = grid.det_to_layer
    chosen: set[tuple[int, int]] = set()
    pairs: list[tuple[int, int]] = []
    while len(pairs) < int(num_pairs):
        draw = rng.integers(0, num_detectors, size=(4 * int(num_pairs), 2))
        a, b = draw[:, 0], draw[:, 1]
        di = np.abs(chain[a] - chain[b])
        dt = np.abs(layer[a] - layer[b])
        near = (
            ((di == 0) & (dt <= TIME_MAX_DT))
            | ((dt == 0) & (di <= SPACE_MAX_DI))
            | ((di <= BLOCK_MAX) & (dt <= BLOCK_MAX))
        )
        for x, y in zip(a[~near], b[~near]):
            key = (int(min(x, y)), int(max(x, y)))
            if key not in chosen:
                chosen.add(key)
                pairs.append(key)
                if len(pairs) == int(num_pairs):
                    break
    return np.asarray(pairs, dtype=np.int64)


@dataclass
class PairCounts:
    """Pass-1 accumulators: per-detector counts + per-pair joint counts."""

    num_shots: int
    grid_counts: np.ndarray  # [L, C] int64
    and_counts: dict  # structured class key -> joint-count plane int64
    far_pairs: np.ndarray  # [F, 2] detector ids
    far_and: np.ndarray  # [F] int64


def accumulate_pair_counts(
    events_path: Path | str,
    grid: DetectorGrid,
    *,
    chunk_shots: int = 10_000,
    far_pairs: np.ndarray | None = None,
    progress=None,
) -> PairCounts:
    layers, chains = grid.num_layers, grid.num_chains
    bits_per_shot = layers * chains
    num_shots = num_shots_in_file(events_path, bits_per_shot)
    if far_pairs is None:
        far_pairs = build_far_pairs(grid)
    far_a, far_b = far_pairs[:, 0], far_pairs[:, 1]

    grid_flat = grid.grid.ravel()
    keys = structured_class_keys()
    slices = {k: _class_slices(k, layers, chains) for k in keys}
    grid_counts = np.zeros((layers, chains), dtype=np.int64)
    and_counts = {
        k: np.zeros(
            (len(np.arange(layers)[slices[k][0][0]]), len(np.arange(chains)[slices[k][0][1]])),
            dtype=np.int64,
        )
        for k in keys
    }
    far_and = np.zeros(far_pairs.shape[0], dtype=np.int64)

    for start, packed in iter_b8_chunks(events_path, bits_per_shot, chunk_shots=chunk_shots):
        bits = np.unpackbits(packed, axis=1, count=bits_per_shot, bitorder="little")
        g = bits[:, grid_flat].reshape(bits.shape[0], layers, chains)
        grid_counts += g.sum(axis=0, dtype=np.int64)
        for k in keys:
            (s1, s2) = slices[k]
            joint = g[:, s1[0], s1[1]] & g[:, s2[0], s2[1]]
            and_counts[k] += joint.sum(axis=0, dtype=np.int64)
        far_and += (bits[:, far_a] & bits[:, far_b]).sum(axis=0, dtype=np.int64)
        if progress is not None:
            progress(start + g.shape[0], num_shots)

    return PairCounts(
        num_shots=num_shots,
        grid_counts=grid_counts,
        and_counts=and_counts,
        far_pairs=far_pairs,
        far_and=far_and,
    )


def _class_moment_planes(counts: PairCounts, grid: DetectorGrid) -> dict:
    layers, chains = grid.num_layers, grid.num_chains
    n = float(counts.num_shots)
    m = counts.grid_counts / n
    moments: dict = {}
    for key, joint in counts.and_counts.items():
        (s1, s2) = _class_slices(key, layers, chains)
        moments[key] = (m[s1], m[s2], joint / n)
    m_det = np.empty(layers * chains, dtype=np.float64)
    m_det[grid.grid.ravel()] = m.ravel()
    far_a, far_b = counts.far_pairs[:, 0], counts.far_pairs[:, 1]
    moments[FAR_CLASS] = (m_det[far_a], m_det[far_b], counts.far_and / n)
    return moments


@dataclass(frozen=True)
class PairEntryStats:
    key: object
    num_pairs: int
    pij: np.ndarray  # flattened per-pair values
    se_delta: np.ndarray  # flattened per-pair delta-method SEs
    boundary: np.ndarray  # flattened boundary flags
    mean_pij: float
    mean_pij_bulk: float  # boundary pairs excluded
    mean_pij_boundary: float


def pair_entry_stats(counts: PairCounts, grid: DetectorGrid) -> dict:
    layers, chains = grid.num_layers, grid.num_chains
    moments = _class_moment_planes(counts, grid)
    entries: dict = {}
    for key, (mi, mj, mij) in moments.items():
        pij = spitz_pij_exact(mi, mj, mij).ravel()
        se = spitz_pij_delta_se(mi, mj, mij, counts.num_shots).ravel()
        if key == FAR_CLASS:
            far = counts.far_pairs
            boundary = (
                np.isin(grid.det_to_layer[far], (0, layers - 1)).any(axis=1)
                | np.isin(grid.det_to_chain[far], (0, chains - 1)).any(axis=1)
            )
        else:
            boundary = _boundary_mask(key, layers, chains).ravel()
        bulk = pij[~boundary]
        edge = pij[boundary]
        entries[key] = PairEntryStats(
            key=key,
            num_pairs=int(pij.size),
            pij=pij,
            se_delta=se,
            boundary=boundary,
            mean_pij=float(pij.mean()),
            mean_pij_bulk=float(bulk.mean()) if bulk.size else float("nan"),
            mean_pij_boundary=float(edge.mean()) if edge.size else float("nan"),
        )
    return entries


@dataclass(frozen=True)
class ClassMeanSE:
    key: object
    num_pairs: int
    mean_pij: float
    se_boot: float  # shot-level bootstrap (B replicates) of the linearized class mean
    se_linear: float  # closed-form SE of the same linearization (cross-check)
    replicates: int


def class_mean_bootstrap(
    events_path: Path | str,
    grid: DetectorGrid,
    counts: PairCounts,
    *,
    chunk_shots: int = 2000,
    replicates: int = 1000,
    seed: int = M1_PIJ_BOOTSTRAP_SEED,
    progress=None,
) -> dict:
    """Shot-level bootstrap SEs of every class mean via per-shot projections.

    The class mean is a smooth function of per-shot moment means; its
    first-order expansion turns each shot into a scalar contribution
    ``T_n = (1/|C|) Σ_p [gi_p x_n(i_p) + gj_p x_n(j_p) + gij_p x_n(i_p)x_n(j_p)]``
    which is bootstrapped exactly at shot level (B = ``replicates``).
    """

    layers, chains = grid.num_layers, grid.num_chains
    bits_per_shot = layers * chains
    num_shots = counts.num_shots
    moments = _class_moment_planes(counts, grid)
    keys = list(moments.keys())
    k_index = {k: i for i, k in enumerate(keys)}

    w_lin = np.zeros((layers, chains, len(keys)), dtype=np.float64)
    c_planes: dict = {}
    far_a, far_b = counts.far_pairs[:, 0], counts.far_pairs[:, 1]
    for key in keys:
        mi, mj, mij = moments[key]
        gi, gj, gij = _pij_gradients(mi, mj, mij)
        scale = 1.0 / float(mi.size)
        col = k_index[key]
        if key == FAR_CLASS:
            np.add.at(
                w_lin[:, :, col], (grid.det_to_layer[far_a], grid.det_to_chain[far_a]), gi * scale
            )
            np.add.at(
                w_lin[:, :, col], (grid.det_to_layer[far_b], grid.det_to_chain[far_b]), gj * scale
            )
            c_planes[key] = (gij * scale).astype(np.float32)
        else:
            (s1, s2) = _class_slices(key, layers, chains)
            w_lin[s1[0], s1[1], col] += gi * scale
            w_lin[s2[0], s2[1], col] += gj * scale
            c_planes[key] = (gij * scale).ravel().astype(np.float32)
    w_mat = w_lin.reshape(layers * chains, len(keys)).astype(np.float32)

    grid_flat = grid.grid.ravel()
    t_shot = np.zeros((num_shots, len(keys)), dtype=np.float64)
    for start, packed in iter_b8_chunks(events_path, bits_per_shot, chunk_shots=chunk_shots):
        bits = np.unpackbits(packed, axis=1, count=bits_per_shot, bitorder="little")
        n = bits.shape[0]
        g = bits[:, grid_flat].reshape(n, layers, chains)
        gf = g.reshape(n, -1).astype(np.float32)
        block = gf @ w_mat
        for key in keys:
            col = k_index[key]
            if key == FAR_CLASS:
                joint = (bits[:, far_a] & bits[:, far_b]).astype(np.float32)
            else:
                (s1, s2) = _class_slices(key, layers, chains)
                joint = (g[:, s1[0], s1[1]] & g[:, s2[0], s2[1]]).reshape(n, -1).astype(np.float32)
            block[:, col] += joint @ c_planes[key]
        t_shot[start : start + n] = block
        if progress is not None:
            progress(start + n, num_shots)

    rng = np.random.default_rng(int(seed))
    reps = np.empty((int(replicates), len(keys)), dtype=np.float64)
    for b in range(int(replicates)):
        idx = rng.integers(0, num_shots, size=num_shots)
        reps[b] = t_shot[idx].mean(axis=0)
    se_boot = reps.std(axis=0, ddof=1)
    se_linear = t_shot.std(axis=0, ddof=1) / np.sqrt(float(num_shots))

    entries = pair_entry_stats(counts, grid)
    return {
        key: ClassMeanSE(
            key=key,
            num_pairs=entries[key].num_pairs,
            mean_pij=entries[key].mean_pij,
            se_boot=float(se_boot[k_index[key]]),
            se_linear=float(se_linear[k_index[key]]),
            replicates=int(replicates),
        )
        for key in keys
    }


@dataclass(frozen=True)
class PijAnalysis:
    num_shots: int
    entries: dict  # class key -> PairEntryStats
    class_se: dict  # class key -> ClassMeanSE
    far_pairs: np.ndarray


def analyze_pij(
    events_path: Path | str,
    grid: DetectorGrid,
    *,
    chunk_shots: int = 10_000,
    projection_chunk_shots: int = 2000,
    replicates: int = 1000,
    seed: int = M1_PIJ_BOOTSTRAP_SEED,
    progress=None,
) -> PijAnalysis:
    counts = accumulate_pair_counts(events_path, grid, chunk_shots=chunk_shots, progress=progress)
    entries = pair_entry_stats(counts, grid)
    class_se = class_mean_bootstrap(
        events_path,
        grid,
        counts,
        chunk_shots=projection_chunk_shots,
        replicates=replicates,
        seed=seed,
        progress=progress,
    )
    return PijAnalysis(
        num_shots=counts.num_shots,
        entries=entries,
        class_se=class_se,
        far_pairs=counts.far_pairs,
    )

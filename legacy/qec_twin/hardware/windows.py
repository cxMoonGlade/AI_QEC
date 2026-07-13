"""R2-lite M2 — window-closure audit over the d=29 chain (ADR 0007; pre-registered
2026-06-09 in docs/metric_results.md).

Aggregates the ledgered Spitz-exact ``p_ij`` per-pair planes into per-separation
site-pair masses over the bulk-layer block, then scores every sliding 6-site
window: ``X1`` (naive closure = crossing/(within+crossing)) and ``X2`` (margin-2
leakage = trusted-interior↔exterior mass over all mass touching the interior).
Observations only — no decoding, no mechanism attribution (R2-lite claim scope).

STATUS WARNING (binding, 2026-06-10 user directive; METRICS.md rung-3 row):
``X1``/``X2`` are a HEURISTIC RISK-AUDIT GATE, not a theorem. There is NO
sufficiency result of the form "X2 <= threshold => bounded marginal-calibration
error" — the metric sees only the two-point sector and is blind to higher-order
cross-cut dependence. Permitted use: pre-registered go/no-go risk gating of
window selections (the M2 role). FORBIDDEN use: as a premise, definition,
derivation step, error bound, or conclusion anywhere downstream. Any future
result that needs a cross-cut residual BOUND must derive one independently.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from qec_twin.hardware.pij import (
    PairCounts,
    _class_moment_planes,
    spitz_pij_exact,
    structured_class_keys,
)
from qec_twin.hardware.stim_artifacts import DetectorGrid

BULK_LAYER_LO = 2
BULK_LAYER_HI = 999
WINDOW_SITES = 6
MARGIN = 2


def site_pair_masses(
    counts: PairCounts,
    grid: DetectorGrid,
    *,
    layer_lo: int = BULK_LAYER_LO,
    layer_hi: int = BULK_LAYER_HI,
) -> dict[int, np.ndarray]:
    """Per chain separation ``di``: summed bulk-block p_ij mass per left site.

    A class plane's row ``r`` corresponds to the pair layers ``(r, r+dt)`` and its
    column ``c`` to the site pair ``(c, c+di)``; a pair enters the bulk block iff
    both layers lie in ``[layer_lo, layer_hi]``.
    """
    moments = _class_moment_planes(counts, grid)
    masses: dict[int, np.ndarray] = {}
    for key in structured_class_keys():
        di, dt, _ = key
        mi, mj, mij = moments[key]
        pij = spitz_pij_exact(mi, mj, mij)
        rows = np.arange(pij.shape[0])
        keep = (rows >= layer_lo) & (rows + dt <= layer_hi)
        col_mass = pij[keep].sum(axis=0)
        if di not in masses:
            masses[di] = np.zeros(grid.num_chains, dtype=np.float64)
        masses[di][: col_mass.size] += col_mass
    return masses


@dataclass(frozen=True)
class WindowScore:
    start: int
    is_interior: bool
    within: float
    crossing: float
    x1: float
    interior_touch: float
    interior_leak: float
    x2: float


def _pairs_for_di(di: int, num_sites: int):
    return ((c, c + di) for c in range(num_sites - di)) if di else ((c, c) for c in range(num_sites))


def window_closure_audit(
    masses: dict[int, np.ndarray],
    num_sites: int,
    *,
    window_sites: int = WINDOW_SITES,
    margin: int = MARGIN,
) -> list[WindowScore]:
    scores = []
    for s in range(num_sites - window_sites + 1):
        w_lo, w_hi = s, s + window_sites - 1
        t_lo, t_hi = s + margin, s + window_sites - 1 - margin
        within = crossing = touch = leak = 0.0
        for di, col in masses.items():
            for (a, b) in _pairs_for_di(di, num_sites):
                m = float(col[a])
                in_a, in_b = w_lo <= a <= w_hi, w_lo <= b <= w_hi
                if in_a and in_b:
                    within += m
                elif in_a or in_b:
                    crossing += m
                t_a, t_b = t_lo <= a <= t_hi, t_lo <= b <= t_hi
                if t_a or t_b:
                    touch += m
                    if (t_a and not in_b) or (t_b and not in_a):
                        leak += m
        x1 = crossing / (within + crossing)
        x2 = leak / touch if touch else float("nan")
        scores.append(
            WindowScore(
                start=s,
                is_interior=(s > 0 and s + window_sites < num_sites),
                within=within,
                crossing=crossing,
                x1=x1,
                interior_touch=touch,
                interior_leak=leak,
                x2=x2,
            )
        )
    return scores

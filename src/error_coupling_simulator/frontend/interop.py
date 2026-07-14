from __future__ import annotations

"""P0 interop: correlated-Pauli DEM reduction of emitted ``{det,obs}`` records.

The DEM is the decoder-facing Stim-compatible SUMMARY of a record cube
(``docs/twin_validation/conjunction_tool_product_spec_2026-07-06.md``, Interface
(b)): per-detector marginals + the canonical Spitz Eq. 13 exact pairwise
``p_ij`` (the package-local :mod:`error_coupling_simulator.frontend.pij`
estimator) reduced to a matchable
``stim.DetectorErrorModel``:

- **pair edges** = detector pairs whose ``p_ij`` clears a DECLARED floor
  (absolute + sigma, class (c) selection rule);
- **boundary edges** = per-detector residuals from the exact odd-parity product
  identity ``1 - 2<x_i> = (1 - 2 p_bnd_i) * prod_j (1 - 2 p_ij)`` over the kept
  edges (exact given the two-point-edge model; the model itself is the declared
  reduction);
- **logical attachment** = a DECLARED geometry rule (the caller names the
  detectors whose boundary fault class flips the logical observable), class
  (c) — bounded against the exact record law at P1, not estimated here.

Convention caveats carried with the numbers: the reduction is two-point only
(structurally blind to hyperedges — the same caveat as ``spitz_pij_exact``),
and it summarizes whatever correlations the records carry into an
edge-factorized DEM; the faithful non-Pauli/coupled content stays in the
``{det,obs}`` cube itself. This module is record-facing reduction plumbing and
does not consume evaluator-only process truth.
"""

from typing import Any, Sequence

import numpy as np

from ..numerics import NUMERICAL_ZERO
from . import decoder as _decoder
from .pij import spitz_pij_delta_se, spitz_pij_exact

#: Declared class-(c) edge-selection floors (P0 defaults; carried in the
#: diagnostics of every reduction so no number travels without them).
DEFAULT_PAIR_FLOOR_ABS = 1e-5
DEFAULT_PAIR_FLOOR_SIGMA = 4.0

#: Probability half-open cap for emitted DEM error lines (an error(p>=0.5)
#: line is not a matchable edge weight).
_MAX_EDGE_P = 0.5 - 1e-9


def records_to_dem(
    det: np.ndarray,
    *,
    detector_names: Sequence[str],
    logical_boundary_detectors: Sequence[str] = (),
    logical_index: int = 0,
    pair_floor_abs: float = DEFAULT_PAIR_FLOOR_ABS,
    pair_floor_sigma: float = DEFAULT_PAIR_FLOOR_SIGMA,
    cluster_size: int = 1,
) -> tuple[Any, dict]:
    """Reduce a ``det`` record cube to a matchable ``stim.DetectorErrorModel``.

    Parameters
    ----------
    det:
        ``(N, D)`` 0/1 detection events (D = ``len(detector_names)`` columns in
        record-layout declaration order).
    detector_names:
        The layout names for the D columns (used for the logical-attachment
        rule and the diagnostics; the DEM itself is index-based).
    logical_boundary_detectors:
        DECLARED geometry rule (class (c)): the detector names whose BOUNDARY
        fault class flips logical ``L{logical_index}``. Empty means the DEM
        carries no logical attachment (e.g. an observable structurally
        disconnected from every check — declared, not hidden).
    pair_floor_abs / pair_floor_sigma:
        Class-(c) edge-selection floors: keep pair ``(i, j)`` iff
        ``p_ij > pair_floor_abs`` and ``p_ij > pair_floor_sigma * SE(p_ij)``.
    cluster_size:
        Declared shot-clustering of the input records (e.g. a process's
        ``shots_per_trajectory``). SE CONVENTION (carried with the numbers,
        METRICS discipline): ``spitz_pij_delta_se`` treats shots as iid units;
        for ``cluster_size > 1`` the reported SEs — and hence the sigma
        edge floor — are ANTI-CONSERVATIVE by the cluster design effect
        (trajectory common-mode covariance, historical ledger S-1/C-11). The
        deviation is declared in the diagnostics, not silently corrected;
        bounding it is the P1 faithfulness-table job.

    Returns
    -------
    (dem, diagnostics):
        ``dem`` is a ``stim.DetectorErrorModel``; ``diagnostics`` carries the
        full marginals / p_ij / SE matrices, the kept edges, the boundary
        residual accounting (including clamps), and the floors — so every DEM
        number is auditable against the records it came from.
    """

    import stim

    x = np.asarray(det)
    if x.ndim != 2:
        raise ValueError(f"det must be (N, D), got shape {x.shape}")
    n_shots, d = int(x.shape[0]), int(x.shape[1])
    if int(cluster_size) < 1:
        raise ValueError(f"cluster_size must be >= 1, got {cluster_size!r}")
    names = tuple(str(s) for s in detector_names)
    if len(names) != d:
        raise ValueError(
            f"detector_names has {len(names)} entries for a {d}-column det array"
        )
    if n_shots < 2:
        raise ValueError(f"need at least 2 shots to form moments, got {n_shots}")
    uniq = np.unique(x)
    if not np.all(np.isin(uniq, (0, 1))):
        raise ValueError(f"det must be 0/1 valued, found values {uniq[:8]!r}")
    unknown = set(str(s) for s in logical_boundary_detectors) - set(names)
    if unknown:
        raise ValueError(
            f"logical_boundary_detectors not in detector_names: {sorted(unknown)}"
        )

    xf = x.astype(np.float64)
    marginals = xf.mean(axis=0)
    joint = (xf.T @ xf) / float(n_shots)

    iu_i, iu_j = np.triu_indices(d, k=1)
    pij_flat = spitz_pij_exact(marginals[iu_i], marginals[iu_j], joint[iu_i, iu_j])
    se_flat = spitz_pij_delta_se(
        marginals[iu_i], marginals[iu_j], joint[iu_i, iu_j], n_shots
    )
    finite = np.isfinite(pij_flat) & np.isfinite(se_flat)
    kept_flat = (
        finite
        & (pij_flat > float(pair_floor_abs))
        & (pij_flat > float(pair_floor_sigma) * se_flat)
    )

    pij = np.zeros((d, d), dtype=np.float64)
    pij[iu_i, iu_j] = np.where(np.isfinite(pij_flat), pij_flat, 0.0)
    pij = pij + pij.T
    pij_se = np.zeros((d, d), dtype=np.float64)
    pij_se[iu_i, iu_j] = np.where(np.isfinite(se_flat), se_flat, 0.0)
    pij_se = pij_se + pij_se.T

    edges: list[dict] = []
    edge_factor = np.ones(d, dtype=np.float64)
    for a, b, p in zip(iu_i[kept_flat], iu_j[kept_flat], pij_flat[kept_flat]):
        p = float(min(p, _MAX_EDGE_P))
        edges.append({"i": int(a), "j": int(b), "p": p})
        edge_factor[a] *= 1.0 - 2.0 * p
        edge_factor[b] *= 1.0 - 2.0 * p

    boundaries: list[dict] = []
    clamped_boundaries: list[dict] = []
    l0_names = set(str(s) for s in logical_boundary_detectors)
    for i in range(d):
        if edge_factor[i] <= NUMERICAL_ZERO:
            # Kept edges already saturate this detector's marginal capacity;
            # a residual boundary is numerically unidentifiable here.
            clamped_boundaries.append(
                {"i": i, "reason": "edge_factor_nonpositive", "p_raw": None}
            )
            continue
        p_raw = 0.5 - 0.5 * (1.0 - 2.0 * float(marginals[i])) / float(edge_factor[i])
        if p_raw <= NUMERICAL_ZERO:
            if p_raw < -float(pair_floor_abs):
                # Pair edges over-account the marginal beyond noise: recorded,
                # never silently zeroed.
                clamped_boundaries.append(
                    {"i": i, "reason": "negative_residual", "p_raw": float(p_raw)}
                )
            continue
        p = float(min(p_raw, _MAX_EDGE_P))
        boundaries.append(
            {"i": i, "p": p, "logical": names[i] in l0_names, "p_raw": float(p_raw)}
        )

    lines: list[str] = []
    for edge in edges:
        lines.append(f"error({edge['p']:.12g}) D{edge['i']} D{edge['j']}")
    for bnd in boundaries:
        suffix = f" L{int(logical_index)}" if bnd["logical"] else ""
        lines.append(f"error({bnd['p']:.12g}) D{bnd['i']}{suffix}")
    for i in range(d):
        lines.append(f"detector D{i}")
    lines.append(f"logical_observable L{int(logical_index)}")
    dem = stim.DetectorErrorModel("\n".join(lines))

    diagnostics = {
        "num_shots": n_shots,
        "num_detectors": d,
        "detector_names": list(names),
        "marginals": marginals,
        "pij": pij,
        "pij_se": pij_se,
        "edges": edges,
        "boundaries": boundaries,
        "clamped_boundaries": clamped_boundaries,
        "logical_boundary_detectors": sorted(l0_names),
        "logical_index": int(logical_index),
        "floors": {
            "pair_floor_abs": float(pair_floor_abs),
            "pair_floor_sigma": float(pair_floor_sigma),
            "epistemic_class": "c",
        },
        "pij_se_convention": {
            "estimator": "spitz_pij_delta_se (shots as iid units)",
            "cluster_size": int(cluster_size),
            "anti_conservative_for_clusters": bool(int(cluster_size) > 1),
            "note": (
                "for cluster_size > 1 the SEs and the sigma edge floor are "
                "understated by the cluster design effect (trajectory "
                "common-mode, teacher S-1/C-11); declared, not corrected — "
                "bound at P1"
            ),
        },
        "reduction_caveat": (
            "two-point edge-factorized reduction (Spitz Eq. 13 exact pairs); "
            "structurally blind to hyperedges; logical attachment is a "
            "declared geometry rule, not estimated from records"
        ),
    }
    return dem, diagnostics


def decode_records(dem: Any, det: np.ndarray, *, logical_index: int = 0) -> np.ndarray:
    """MWPM-decode a ``det`` cube against a DEM; return predicted obs ``(N,)``.

    Thin adaptor through the package-local optional decoder port (baseline
    discipline: external PyMatching at its defaults and frozen provenance).
    ``logical_index`` selects the observable column and must match the index
    the DEM was built with — a mismatched index raises instead of silently
    returning the structurally-empty wrong column.
    """

    x = np.asarray(det)
    if x.ndim != 2:
        raise ValueError(f"det must be (N, D), got shape {x.shape}")
    if not np.all((x == 0) | (x == 1)):
        raise ValueError("det must contain only 0/1 values")
    li = int(logical_index)
    if li < 0:
        raise ValueError(f"logical_index must be >= 0, got {logical_index!r}")
    detector_error_model = _decoder._as_dem(dem)
    if int(detector_error_model.num_detectors) != int(x.shape[1]):
        raise ValueError(
            f"DEM declares {detector_error_model.num_detectors} detectors, det has "
            f"{x.shape[1]} columns"
        )
    n_obs = int(detector_error_model.num_observables)
    if li >= n_obs:
        raise ValueError(
            f"logical_index={li} out of range: the DEM carries {n_obs} "
            "observable column(s)"
        )
    predicted = _decoder.decode_dem(
        detector_error_model,
        x.astype(np.bool_, copy=False),
    )
    predicted = np.asarray(predicted, dtype=np.uint8)
    if predicted.ndim == 1:
        predicted = predicted[:, None]
    if predicted.shape[1] != n_obs:
        raise ValueError(
            f"decode_batch returned {predicted.shape[1]} columns, expected "
            f"{n_obs} fault ids"
        )
    return predicted[:, li]


def insert_op_after_tick(
    circuit: Any,
    tick_index: int,
    name: str,
    targets: Sequence[int],
    args: Sequence[float] = (),
) -> Any:
    """Return a copy of ``circuit`` with one op inserted after the given TICK.

    Deterministic fault-injection utility for the INDEPENDENT wiring check
    (stim as the reference implementation): inject a known fault at a known
    round boundary and assert the EXACT fired-detector pattern + observable
    the record layout predicts. Unlike the noiseless all-zero sample — which
    is vacuous for an all-Z fixture (every measurement is deterministically 0,
    so any xor/key bug still samples zero) — this check fails loudly on
    mis-mapped detector columns, wrong xor sets, or wrong observable keys.

    NOTE stim frame semantics: stim's detector sampler reports deviations from
    the noiseless-WITH-GATES reference, so a deterministic GATE (``X``) never
    fires a detector — inject a probability-1 ERROR instead, e.g.
    ``insert_op_after_tick(c, 1, "X_ERROR", (2,), (1.0,))``, which flips the
    error frame deterministically and registers as a detection event.

    ``tick_index = 0`` inserts before the first instruction (before round 0);
    ``tick_index = t >= 1`` inserts immediately after the t-th ``TICK`` (i.e.
    after round ``t-1``'s measurements, before round ``t``). The compiler
    emits one TICK per round, so valid values are ``0..rounds``.
    """

    import stim

    total_ticks = sum(1 for inst in circuit if getattr(inst, "name", "") == "TICK")
    t = int(tick_index)
    if not 0 <= t <= total_ticks:
        raise ValueError(
            f"tick_index {tick_index!r} outside [0, {total_ticks}] for this circuit"
        )
    out = stim.Circuit()
    if t == 0:
        out.append(str(name), [int(q) for q in targets], list(args))
    seen = 0
    for inst in circuit:
        out.append(inst)
        if getattr(inst, "name", "") == "TICK":
            seen += 1
            if seen == t:
                out.append(str(name), [int(q) for q in targets], list(args))
    return out


__all__ = [
    "DEFAULT_PAIR_FLOOR_ABS",
    "DEFAULT_PAIR_FLOOR_SIGMA",
    "decode_records",
    "insert_op_after_tick",
    "records_to_dem",
]

"""Stage-D batch ``interop`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.interop`` (3 LIVE public units, CPU-pure).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md). The module is the
frontend/evaluator-side ``{det,obs}`` -> matchable ``stim.DetectorErrorModel`` plumbing:
the exact Spitz Eq.13 pairwise ``p_ij`` + odd-parity boundary-residual product identity
reduction, a PyMatching MWPM adaptor, and a deterministic stim fault-injection utility.
CPU-PURE (stim + pymatching + qec_twin.hardware.pij; imports NEITHER torch NOR quimb)
=> FULL treatment (L0 100% stmt+branch, L1 property, L2 mutmut).

  UNIT                  L0 branch surface                          L1/KILLER value pin
  ----                  -----------------                          -------------------
  records_to_dem        6 ValueError guards; kept-edge loop body   edges/boundaries pinned
                        vs 0-edge; edge_factor<=0 clamp; p_raw<=0   to an INDEPENDENT from-
                        skip vs negative_residual clamp; boundary   scratch Spitz recompute
                        logical True/False ternary; p>_MAX_EDGE_P   + the EXACT odd-parity
                        + p_raw>_MAX_EDGE_P clamps; non-finite mask boundary identity
  decode_records        ndim/li<0/ndet/li>=n_obs guards; the        output contract + the
                        predicted.ndim==1 reshape arc + the         logical_index column is
                        shape!=n_obs guard via a monkeypatched      load-bearing (2-obs DEM,
                        pymatching backend seam                     col0 != col1)
  insert_op_after_tick  t out of [0,total]; t==0 vs t>=1; TICK      exact resulting circuit;
                        match vs non-match; seen==t both arcs       injected X_ERROR fires
                                                                    the EXACT detector, off-
                                                                    by-one changes it

THE PRIOR-BATCH LESSON (certify: 100% coverage at ~0.75 kill because it asserted
SHAPES/verdicts, not VALUES). Every load-bearing assert here PINS A VALUE against an
INDEPENDENT recompute (``_spitz_ref`` reimplements Spitz Eq.13 from scratch -- it does
NOT import the module's ``spitz_pij_exact``, so it is a genuine from-scratch oracle) or
asserts DISCRIMINATION (``assert_discriminates`` -- floor bracket, clamp, logical index).
A mutant that drops the ``1-2p`` factor, flips a triu index, changes a floor comparison,
mis-selects the observable column, or miscounts TICKs must FAIL an assert here.

DETERMINISTIC POPULATION CUBES (no sampling). Every records_to_dem case is an EXACT
integer-count population cube, so the moments are exact rationals and the Spitz outputs
are exact to 1e-12 -- no random seed, no tolerance slack. The planted 4-detector cube
recovers edge p=0.25 and boundaries p=0.125 EXACTLY (hand-derived + from-scratch pinned).

DEFENSIVE-ASSERT / SEAM (CODEBOOK). PyMatching's ``decode_batch`` always returns a 2-D
``(N, n_obs)`` array (measured: stim 1.16 / pymatching 2.4), so the ``predicted.ndim==1``
reshape arc and the ``shape[1]!=n_obs`` guard are unreachable through the real backend.
They are covered by tripping the guard via a monkeypatched ``pymatching.Matching``
backend seam -- the sanctioned "extract/trip the seam" route, paired with the legit-path
property (``test_L1_decode_output_contract`` proves the real 2-D path).
"""
from __future__ import annotations

import numpy as np
import pytest
import stim
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins
from error_coupling_simulator.frontend.interop import (
    DEFAULT_PAIR_FLOOR_ABS,
    DEFAULT_PAIR_FLOOR_SIGMA,
    _MAX_EDGE_P,
    decode_records,
    insert_op_after_tick,
    records_to_dem,
)
from error_coupling_simulator.frontend.stim_io import sample_detector_records
from error_coupling_simulator.noise_processes.coupled_cycle import CoupledCycleNoiseProcess

ROUNDS = 3


# --------------------------------------------------------------------------- #
# builders + the INDEPENDENT Spitz oracle (from-scratch; NOT the module's)     #
# --------------------------------------------------------------------------- #
def _cube(rows) -> np.ndarray:
    """Stack ``rows`` = [(pattern_tuple, count), ...] into an EXACT population cube.
    Moments are exact rationals (no sampling), so every downstream value pins to 1e-12."""
    return np.vstack([np.tile(np.array(p, np.uint8), (c, 1)) for p, c in rows])


def _spitz_ref(det: np.ndarray):
    """INDEPENDENT from-scratch Spitz et al. Eq.13 EXACT pairwise ``p_ij`` (NOT importing
    the module's ``spitz_pij_exact`` -- a genuine reimplementation, faithfulness Rule I):

        p_ij = 1/2 - sqrt( 1/4 - cov / (1 - 2<x_i XOR x_j>) ),
        cov = <x_i x_j> - <x_i><x_j>,  <x_i XOR x_j> = <x_i> + <x_j> - 2<x_i x_j>.

    Returns (marginals, P) with P symmetric, P[i,i]=0, non-finite entries left non-finite
    (the module's finite-mask drops those). Mirrors the module's radicand clip-to->=0."""
    X = np.asarray(det, dtype=np.float64)
    n, d = X.shape
    m = X.mean(axis=0)
    J = (X.T @ X) / float(n)
    P = np.zeros((d, d), dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        for i in range(d):
            for j in range(i + 1, d):
                cov = J[i, j] - m[i] * m[j]
                denom = 1.0 - 2.0 * (m[i] + m[j] - 2.0 * J[i, j])
                rad = 0.25 - cov / denom
                if rad >= 0.0:                       # finite, non-negative radicand
                    pij = 0.5 - np.sqrt(rad)
                elif np.isfinite(rad):               # finite negative -> module clips to 0
                    pij = 0.5
                else:                                # 0/0 or /0 -> non-finite (dropped)
                    pij = np.nan
                P[i, j] = P[j, i] = pij
    return m, P


def _spitz_se_ref(det: np.ndarray) -> np.ndarray:
    """INDEPENDENT from-scratch delta-method SE of the Spitz p_ij (reimplements the exact
    per-shot moment-covariance propagation; NOT importing the module's ``spitz_pij_delta_se``).
    Symmetric, 0 diagonal. Verified bit-identical to the module on the planted cube -- pinning
    ``diagnostics['pij_se']`` to it kills any SE-computation / where-fill mutation."""
    X = np.asarray(det, dtype=np.float64)
    n, d = X.shape
    m = X.mean(axis=0)
    J = (X.T @ X) / float(n)
    SE = np.zeros((d, d), dtype=np.float64)
    with np.errstate(all="ignore"):
        for i in range(d):
            for j in range(i + 1, d):
                mi, mj, mij = m[i], m[j], J[i, j]
                cov = mij - mi * mj
                denom = 1.0 - 2.0 * (mi + mj - 2.0 * mij)
                root = np.sqrt(np.clip(0.25 - cov / denom, 1e-12, None))
                d2 = denom * denom
                common = 1.0 / (2.0 * root)
                gi = common * (-mj * denom + 2.0 * cov) / d2
                gj = common * (-mi * denom + 2.0 * cov) / d2
                gij = common * (denom - 4.0 * cov) / d2
                variance = (gi * gi * mi * (1 - mi) + gj * gj * mj * (1 - mj)
                            + gij * gij * mij * (1 - mij)
                            + 2 * gi * gj * (mij - mi * mj)
                            + 2 * gi * gij * (mij * (1 - mi))
                            + 2 * gj * gij * (mij * (1 - mj)))
                SE[i, j] = SE[j, i] = np.sqrt(np.clip(variance, 0.0, None) / float(n))
    return SE


def _planted_cube() -> np.ndarray:
    """4 detectors, exact population of three INDEPENDENT fault classes:
      f01 ~ 0.25 flips D0,D1 (pair edge);  f2 ~ 0.125 flips D2 (+ logical);
      f0 ~ 0.125 flips D0 alone (boundary, no logical);  D3 planted silent.
    Independence is EXACT (full 2^3 population), so: p_ij(0,1)=0.25, boundary D0=0.125,
    boundary D2=0.125 -- all recovered EXACTLY (hand-derived, from-scratch pinned)."""
    p01, p2, p0, n = 0.25, 0.125, 0.125, 2560
    rows = []
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                cnt = int(round(n * (p01 if a else 1 - p01)
                                * (p2 if b else 1 - p2) * (p0 if c else 1 - p0)))
                rows.append(((a ^ c, a, b, 0), cnt))          # D0=f01^f0, D1=f01, D2=f2, D3=0
    return _cube(rows)


def _corr_half_cube() -> np.ndarray:
    """3 detectors PERFECTLY correlated at marginal 0.5 -> each pair's raw Spitz p_ij is
    EXACTLY 0.5 (> the _MAX_EDGE_P cap) and each detector touches 2 near-0.5 edges whose
    (1-2p) product underflows NUMERICAL_ZERO -> edge_factor_nonpositive on all three."""
    return _cube([((1, 1, 1), 2000), ((0, 0, 0), 2000)])


def _neg_resid_cube() -> np.ndarray:
    """2 detectors: joint P(D0,D1) = {(1,1):0.1,(0,1):0.3,(0,0):0.6,(1,0):0}. The kept
    edge p_ij ~ 0.1838 EXCEEDS m0=0.1, so the edge over-accounts D0's marginal and the
    residual p_raw ~ -0.132 < -pair_floor_abs -> the 'negative_residual' clamp arc."""
    return _cube([((1, 1), 1000), ((0, 1), 3000), ((0, 0), 6000)])


def _indep_half_cube() -> np.ndarray:
    """2 INDEPENDENT detectors at marginal 0.5: denom = 1-2*(0.5+0.5-2*0.25) = 0, so the
    Spitz p_ij is 0/0 = NON-FINITE (dropped by the finite mask -> 0 kept edges), and each
    detector's residual p_raw = 0.5 > _MAX_EDGE_P -> the boundary clamp arc."""
    return _cube([((0, 0), 500), ((0, 1), 500), ((1, 0), 500), ((1, 1), 500)])


def _zero_cube() -> np.ndarray:
    """The null control: all-silent 4-detector cube -> 0 edges AND 0 boundaries (every
    p_raw = 0 <= NUMERICAL_ZERO, not < -floor -> skipped), the empty-loop arcs."""
    return np.zeros((5000, 4), dtype=np.uint8)


def _two_obs_dem() -> "stim.DetectorErrorModel":
    """Hand-built 2-observable DEM where D_k's fault flips L_k ONLY, so decoded column 0
    (L0) and column 1 (L1) DIFFER -- makes ``logical_index`` load-bearing (a wrong index
    reads the wrong column, which a shape-only assert could never catch)."""
    return stim.DetectorErrorModel(
        "error(0.1) D0 L0\nerror(0.1) D1 L1\n"
        "detector D0\ndetector D1\nlogical_observable L0\nlogical_observable L1"
    )


def _parse_dem(dem) -> tuple:
    """Round-trip parse: read the emitted DEM back and split error(p) lines into edge
    (2 detector targets) vs boundary (1 detector target) probabilities. INDEPENDENT of
    the diagnostics -- reproduces the edge/boundary structure from the DEM text alone."""
    edge_p, bnd_p = [], []
    for line in str(dem).splitlines():
        line = line.strip()
        if not line.startswith("error("):
            continue
        p = float(line[line.index("(") + 1: line.index(")")])
        toks = line[line.index(")") + 1:].split()
        ndet = sum(1 for t in toks if t.startswith("D"))
        if ndet == 2:
            edge_p.append(p)
        elif ndet == 1:
            bnd_p.append(p)
    return edge_p, bnd_p


def _boundary_identity_maxviol(det: np.ndarray, diag: dict) -> float:
    """Max abs violation of the EXACT odd-parity boundary-residual identity, computed with
    INDEPENDENTLY recomputed marginals (mean of the cube):

        (1 - 2<x_i>) == (1 - 2 p_raw_i) * prod_over_kept_edges_touching_i (1 - 2 p_edge).

    THE load-bearing physics of the reduction; a mutant that drops a (1-2p) factor, uses
    (1+2p), or reads the wrong marginal breaks it well above 1e-12."""
    m = np.asarray(det, dtype=np.float64).mean(axis=0)
    viol = 0.0
    for b in diag["boundaries"]:
        i = b["i"]
        prod = 1.0
        for e in diag["edges"]:
            if e["i"] == i or e["j"] == i:
                prod *= 1.0 - 2.0 * e["p"]
        lhs = 1.0 - 2.0 * m[i]
        rhs = (1.0 - 2.0 * b["p_raw"]) * prod
        viol = max(viol, abs(lhs - rhs))
    return viol


# =========================================================================== #
# L0 -- records_to_dem: every statement + BOTH arcs of every guard             #
# =========================================================================== #
def test_L0_records_to_dem_planted_edge_and_boundary_arcs():
    """Kept-edge loop body + boundary loop body + the ``bnd['logical']`` ternary BOTH arcs
    (D2 True, D0 False) + the p_raw<=0 skip arc (D1, D3) + the edge_factor>0 (False) arc."""
    det = _planted_cube()
    dem, diag = records_to_dem(
        det, detector_names=("d0", "d1", "d2", "d3"), logical_boundary_detectors=("d2",)
    )
    assert {(e["i"], e["j"]) for e in diag["edges"]} == {(0, 1)}          # loop body ran
    logic = {b["i"]: b["logical"] for b in diag["boundaries"]}
    assert logic == {0: False, 2: True}                                  # ternary both arcs
    assert diag["clamped_boundaries"] == []                              # no clamp here
    assert dem.num_detectors == 4 and dem.num_observables == 1


def test_L0_records_to_dem_corr_half_edge_factor_nonpositive_clamp():
    """The p>_MAX_EDGE_P pair clamp + the edge_factor<=NUMERICAL_ZERO (True) arc +
    boundaries-loop 0-iteration arc (all three detectors saturate -> no boundary)."""
    det = _corr_half_cube()
    _, diag = records_to_dem(det, detector_names=("a", "b", "c"))
    assert {(e["i"], e["j"]) for e in diag["edges"]} == {(0, 1), (0, 2), (1, 2)}
    reasons = {c["i"]: c["reason"] for c in diag["clamped_boundaries"]}
    assert reasons == {0: "edge_factor_nonpositive",
                       1: "edge_factor_nonpositive",
                       2: "edge_factor_nonpositive"}
    # exact record schema (kills the 'p_raw' key rename in the edge_factor clamp dict)
    for c in diag["clamped_boundaries"]:
        assert set(c.keys()) == {"i", "reason", "p_raw"}
        assert c["p_raw"] is None
    assert diag["boundaries"] == []                                      # empty boundary loop


def test_L0_records_to_dem_negative_residual_clamp():
    """The p_raw<=NUMERICAL_ZERO (True) arc AND its p_raw<-pair_floor_abs (True) inner arc
    -> 'negative_residual'; plus a positive boundary on the other detector."""
    det = _neg_resid_cube()
    _, diag = records_to_dem(det, detector_names=("d0", "d1"))
    clamp = {c["i"]: c["reason"] for c in diag["clamped_boundaries"]}
    assert clamp == {0: "negative_residual"}
    assert {b["i"] for b in diag["boundaries"]} == {1}


def test_L0_records_to_dem_indep_half_nonfinite_and_boundary_clamp():
    """The non-finite finite-mask path (0/0 p_ij) -> 0 kept edges (empty edge loop) + the
    p_raw>_MAX_EDGE_P boundary clamp (residual 0.5 -> _MAX_EDGE_P)."""
    det = _indep_half_cube()
    _, diag = records_to_dem(det, detector_names=("d0", "d1"))
    assert diag["edges"] == []                                           # empty edge loop
    assert {b["i"]: b["p"] for b in diag["boundaries"]} == {0: _MAX_EDGE_P, 1: _MAX_EDGE_P}


def test_L0_records_to_dem_zero_null_control():
    """Both emit loops 0-iteration: no edges, no boundaries (all p_raw = 0, skipped)."""
    det = _zero_cube()
    dem, diag = records_to_dem(det, detector_names=("a", "b", "c", "d"))
    assert diag["edges"] == [] and diag["boundaries"] == []
    assert diag["clamped_boundaries"] == []
    assert dem.num_detectors == 4


def test_L0_records_to_dem_input_validation_all_guards():
    """BOTH arcs of every input guard: each raises; the valid path is exercised above."""
    good = np.zeros((10, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match=r"must be \(N, D\)"):            # ndim != 2
        records_to_dem(np.zeros(4, dtype=np.uint8), detector_names=("a",))
    with pytest.raises(ValueError, match="cluster_size"):                # cluster_size < 1
        records_to_dem(good, detector_names=("a", "b"), cluster_size=0)
    with pytest.raises(ValueError, match="detector_names"):              # len(names) != d
        records_to_dem(good, detector_names=("only_one",))
    with pytest.raises(ValueError, match="2 shots"):                     # n_shots < 2
        records_to_dem(np.zeros((1, 2), dtype=np.uint8), detector_names=("a", "b"))
    with pytest.raises(ValueError, match="0/1"):                         # non-0/1 values
        records_to_dem(np.full((10, 2), 3, dtype=np.uint8), detector_names=("a", "b"))
    with pytest.raises(ValueError, match="not in detector_names"):       # unknown logical
        records_to_dem(good, detector_names=("a", "b"), logical_boundary_detectors=("zz",))


# =========================================================================== #
# L0 -- decode_records: every guard + the reshape/shape arcs via a seam         #
# =========================================================================== #
def test_L0_decode_records_happy_and_logical_index():
    """Normal 2-D return path (predicted.ndim==1 FALSE arc) + logical_index column select.
    Independent oracle: for _two_obs_dem, D_k fault <-> L_k, so predicted L_k == det[:,k]."""
    det = np.array([[1, 0], [0, 1], [1, 1], [0, 0]], dtype=np.uint8)
    dem = _two_obs_dem()
    p0 = decode_records(dem, det, logical_index=0)
    p1 = decode_records(dem, det, logical_index=1)
    assert p0.shape == (4,) and p0.dtype == np.uint8
    assert np.array_equal(p0, det[:, 0])
    assert np.array_equal(p1, det[:, 1])


def test_L0_decode_records_guards():
    """BOTH arcs of ndim / li<0 / num_detectors / li>=n_obs guards."""
    det = _planted_cube()
    dem, _ = records_to_dem(
        det, detector_names=("d0", "d1", "d2", "d3"), logical_boundary_detectors=("d2",)
    )
    with pytest.raises(ValueError, match=r"must be \(N, D\)"):            # ndim != 2
        decode_records(dem, np.zeros(4, dtype=np.uint8))
    with pytest.raises(ValueError, match="logical_index must be >= 0"):  # li < 0
        decode_records(dem, det, logical_index=-1)
    with pytest.raises(ValueError, match="columns"):                     # num_detectors != cols
        decode_records(dem, np.zeros((3, 3), dtype=np.uint8))
    # li >= n_obs: use logical_index EXACTLY == n_obs so a '>=' -> '>' mutation slips past
    # the guard and raises IndexError (not ValueError) instead -> caught by the type; and pin
    # the EXACT message so a wrapped/upper-cased 'observable column(s)' string is caught too.
    dem2, det2 = _two_obs_dem(), np.array([[1, 0], [0, 1]], dtype=np.uint8)
    with pytest.raises(ValueError) as ei:
        decode_records(dem2, det2, logical_index=2)                      # li == n_obs == 2
    assert str(ei.value) == (
        "logical_index=2 out of range: the DEM carries 2 observable column(s)")


def test_L0_decode_records_reshape_arc_via_1d_backend(monkeypatch):
    """The ``predicted.ndim == 1`` TRUE (reshape) arc -- unreachable through real
    PyMatching (decode_batch always returns 2-D), so trip it via a backend seam that
    ravels the prediction to 1-D. The legit 2-D path is proved by the happy test above."""
    import pymatching

    det = _planted_cube()
    dem, _ = records_to_dem(
        det, detector_names=("d0", "d1", "d2", "d3"), logical_boundary_detectors=("d2",)
    )
    orig = pymatching.Matching.decode_batch

    def _ravel_backend(self, shots, *a, **k):
        return np.asarray(orig(self, shots, *a, **k)).ravel()            # force ndim == 1

    monkeypatch.setattr(pymatching.Matching, "decode_batch", _ravel_backend)
    out = decode_records(dem, det)                                       # 1-obs DEM -> (N,)
    assert out.shape == (det.shape[0],) and out.dtype == np.uint8


def test_L0_decode_records_shape_guard_via_bad_backend(monkeypatch):
    """The ``predicted.shape[1] != n_obs`` guard (TRUE/raise arc) -- a defensive guard the
    real backend never trips; trip it with a seam returning the wrong column count."""
    import pymatching

    det = _planted_cube()
    dem, _ = records_to_dem(
        det, detector_names=("d0", "d1", "d2", "d3"), logical_boundary_detectors=("d2",)
    )

    def _wide_backend(self, shots, *a, **k):
        return np.zeros((np.asarray(shots).shape[0], 2), dtype=np.uint8)  # 2 cols, DEM has 1

    monkeypatch.setattr(pymatching.Matching, "decode_batch", _wide_backend)
    with pytest.raises(ValueError, match="expected"):
        decode_records(dem, det)


# =========================================================================== #
# L0 -- insert_op_after_tick: t==0 / t>=1 / range guard / seen==t both arcs     #
# =========================================================================== #
def _tiny_circuit() -> "stim.Circuit":
    c = stim.Circuit()
    c.append("X", [0]); c.append("TICK")
    c.append("Y", [0]); c.append("TICK")
    c.append("Z", [0])
    return c                                                             # total_ticks = 2


def _expect(op_after):
    """Build the expected circuit with H inserted at position ``op_after`` (0=before all,
    1=after 1st TICK, 2=after 2nd TICK) -- the module's own construction order."""
    seq = [("X", "op"), ("TICK", None), ("Y", "op"), ("TICK", None), ("Z", "op")]
    out = stim.Circuit()
    if op_after == 0:
        out.append("H", [0])
    seen = 0
    for name, _ in seq:
        if name == "TICK":
            out.append("TICK")
            seen += 1
            if seen == op_after:
                out.append("H", [0])
        else:
            out.append(name, [0])
    return out


def test_L0_insert_op_after_tick_positions_exact():
    """t==0 (insert-before, TRUE arc) and t>=1 (FALSE arc) with seen==t hit BOTH arcs
    (matching tick True, other ticks False) -- pinned to the EXACT resulting circuit."""
    c = _tiny_circuit()
    assert insert_op_after_tick(c, 0, "H", (0,)) == _expect(0)           # t == 0
    assert insert_op_after_tick(c, 1, "H", (0,)) == _expect(1)           # after 1st TICK
    assert insert_op_after_tick(c, 2, "H", (0,)) == _expect(2)           # after 2nd (==total)


def test_L0_insert_op_after_tick_out_of_range():
    """The range guard raises for t<0 AND t>total (both TRUE-arc entries)."""
    c = _tiny_circuit()
    with pytest.raises(ValueError, match="outside"):
        insert_op_after_tick(c, -1, "H", (0,))
    with pytest.raises(ValueError, match="outside"):
        insert_op_after_tick(c, 3, "H", (0,))


# =========================================================================== #
# KILLER / VALUE PINS -- prove the asserts DISCRIMINATE (the anti-vacuity core) #
# =========================================================================== #
def test_PIN_planted_edges_boundaries_vs_independent_spitz():
    """Pin the kept edge + boundaries to an INDEPENDENT from-scratch Spitz recompute AND
    the exact planted constants, plus the EXACT odd-parity boundary identity. Kills any
    triu-index / 1-2p-factor / marginal-index mutation."""
    det = _planted_cube()
    m_ref, P_ref = _spitz_ref(det)
    dem, diag = records_to_dem(
        det, detector_names=("d0", "d1", "d2", "d3"), logical_boundary_detectors=("d2",)
    )
    edges = {(e["i"], e["j"]): e["p"] for e in diag["edges"]}
    assert set(edges) == {(0, 1)}                                        # no spurious edges
    assert_pins(edges[(0, 1)], P_ref[0, 1], atol=1e-12, label="edge p_ij(0,1) vs oracle")
    assert_pins(edges[(0, 1)], 0.25, atol=1e-12, label="edge p_ij(0,1) exact")

    bounds = {b["i"]: b for b in diag["boundaries"]}
    assert set(bounds) == {0, 2}
    assert_pins(bounds[0]["p"], 0.125, atol=1e-12, label="boundary D0")
    assert bounds[0]["logical"] is False
    assert_pins(bounds[2]["p"], 0.125, atol=1e-12, label="boundary D2")
    assert bounds[2]["logical"] is True

    assert _boundary_identity_maxviol(det, diag) <= 1e-12                # THE physics identity
    # the EXACT residual (0.125) is separated from the naive first-order value (m0 - p01 =
    # 0.0625) -> the exactness claim is falsifiable, not a coincidence.
    assert abs(bounds[0]["p"] - (m_ref[0] - edges[(0, 1)])) > 1e-2

    # pin the FULL pij matrix (not just the kept edge) to the independent recompute -- a mutant
    # that collapses the matrix (e.g. np.where(None, ...) -> all-zero) is caught here even
    # though it leaves the edge LIST (built from pij_flat) intact.
    P_mod = np.where(np.isfinite(P_ref), P_ref, 0.0)                     # module stores 0 for non-finite
    assert_pins(np.asarray(diag["pij"]), P_mod, atol=1e-12, label="pij matrix")
    assert diag["pij"][0, 1] != 0.0                                      # the load-bearing entry is nonzero


def test_PIN_max_edge_p_clamp_discriminates():
    """Raw Spitz p_ij is EXACTLY 0.5 (independent recompute) -> every emitted edge is
    clamped to _MAX_EDGE_P; the '< 0.5' property HOLDS for the clamped edges and FAILS for
    an unclamped-0.5 variant -> the min(p, _MAX_EDGE_P) clamp is load-bearing."""
    det = _corr_half_cube()
    _, P_ref = _spitz_ref(det)
    _, diag = records_to_dem(det, detector_names=("a", "b", "c"))
    for i, j in [(0, 1), (0, 2), (1, 2)]:
        assert_pins(P_ref[i, j], 0.5, atol=1e-12, label=f"raw p_ij({i},{j})")
    assert all(e["p"] == _MAX_EDGE_P for e in diag["edges"])

    def _all_below_half(edge_list):
        for e in edge_list:
            assert e["p"] < 0.5, f"edge p {e['p']} not < 0.5"

    assert_discriminates(_all_below_half, diag["edges"], [{"i": 0, "j": 1, "p": 0.5}],
                         label="_MAX_EDGE_P clamp")


def test_KILLER_floor_selection_discriminates():
    """An edge just under vs just over the floor must flip kept<->dropped -- for BOTH the
    absolute floor (p_ij=0.25: keep at 0.2, drop at 0.3) and the sigma floor (se>0: keep
    at sigma=4, drop at sigma=1e9). Kills a mutated floor comparison."""
    det = _planted_cube()
    names = ("d0", "d1", "d2", "d3")

    def _has_edge(diag):
        assert (0, 1) in {(e["i"], e["j"]) for e in diag["edges"]}, "edge (0,1) absent"

    _, keep_abs = records_to_dem(det, detector_names=names, pair_floor_abs=0.2)
    _, drop_abs = records_to_dem(det, detector_names=names, pair_floor_abs=0.3)
    assert_discriminates(_has_edge, keep_abs, drop_abs, label="pair_floor_abs")

    _, keep_sig = records_to_dem(det, detector_names=names, pair_floor_sigma=4.0)
    _, drop_sig = records_to_dem(det, detector_names=names, pair_floor_sigma=1e9)
    assert_discriminates(_has_edge, keep_sig, drop_sig, label="pair_floor_sigma")


def test_PIN_negative_residual_value_vs_independent_recompute():
    """Pin the 'negative_residual' clamp's p_raw to an INDEPENDENT recompute of the exact
    residual formula (from the from-scratch edge p_ij + recomputed marginal)."""
    det = _neg_resid_cube()
    m_ref, P_ref = _spitz_ref(det)
    _, diag = records_to_dem(det, detector_names=("d0", "d1"))
    assert {(e["i"], e["j"]) for e in diag["edges"]} == {(0, 1)}
    p_edge = diag["edges"][0]["p"]
    assert_pins(p_edge, P_ref[0, 1], atol=1e-12, label="neg-cube edge p_ij")

    edge_factor0 = 1.0 - 2.0 * p_edge                                    # one edge touches D0
    p_raw_ref = 0.5 - 0.5 * (1.0 - 2.0 * m_ref[0]) / edge_factor0
    assert p_raw_ref < -DEFAULT_PAIR_FLOOR_ABS                           # over-accounted
    clamp = {c["i"]: c for c in diag["clamped_boundaries"]}
    assert clamp[0]["reason"] == "negative_residual"
    assert_pins(clamp[0]["p_raw"], p_raw_ref, atol=1e-12, label="negative residual p_raw")
    assert 0 not in {b["i"] for b in diag["boundaries"]}                 # D0 NOT emitted


def test_PIN_indep_half_nonfinite_pij():
    """The independent marginal-0.5 pair: the from-scratch Spitz oracle is NON-FINITE (0/0),
    matching the module dropping it -> 0 kept edges, both residuals clamped to _MAX_EDGE_P."""
    det = _indep_half_cube()
    _, P_ref = _spitz_ref(det)
    _, diag = records_to_dem(det, detector_names=("d0", "d1"))
    assert not np.isfinite(P_ref[0, 1])
    assert diag["edges"] == []
    for b in diag["boundaries"]:
        assert_pins(b["p_raw"], 0.5, atol=1e-12, label=f"D{b['i']} p_raw")
        assert b["p"] == _MAX_EDGE_P and b["logical"] is False


def test_KILLER_decode_records_logical_index_selects_column():
    """The 2-observable DEM has col0 != col1, so decoding with the WRONG logical_index
    returns a DIFFERENT array -> shape alone cannot catch a mis-selected column, but this
    does: the 'equals column 0' property holds for li=0 and FAILS for li=1."""
    det = np.array([[1, 0], [0, 1]], dtype=np.uint8)                     # col0 != col1
    dem = _two_obs_dem()
    expected0 = det[:, 0]

    def _equals_col0(arr):
        assert np.array_equal(np.asarray(arr), expected0), "not column 0"

    assert_discriminates(_equals_col0,
                         decode_records(dem, det, logical_index=0),
                         decode_records(dem, det, logical_index=1),
                         label="logical_index column selection")


def test_KILLER_insert_op_after_tick_injection_off_by_one():
    """Independent wiring reference (stim sampler): a probability-1 X_ERROR on q2 injected
    after TICK t fires EXACTLY the round-t z12 detector. Off-by-one in the TICK count fires
    a DIFFERENT detector (round1 vs round2) -> the seen==t / TICK count is load-bearing.
    (A deterministic GATE never fires a detector -- the module's frame-semantics note.)"""
    teacher = CoupledCycleNoiseProcess(ROUNDS, fixture="d3_repz")
    circ, man = teacher.export_stim_circuit()
    names = man["detector_names"]

    def _fired(tick):
        c2 = insert_op_after_tick(circ, tick, "X_ERROR", (2,), (1.0,))
        det, _ = sample_detector_records(c2, shots=8, seed=3)
        return tuple(n for n, v in zip(names, det[0]) if v)

    assert _fired(1) == ("delta:z12:round1",)
    assert _fired(2) == ("delta:z12:round2",)
    assert _fired(ROUNDS) == ("final:z12",)

    def _is_round1(tick):
        assert _fired(tick) == ("delta:z12:round1",), "not the round-1 detector"

    assert_discriminates(_is_round1, 1, 2, label="insert-after-tick round index")


# =========================================================================== #
# L1 -- Hypothesis faithfulness properties (records_to_dem / decode_records)    #
# =========================================================================== #
@st.composite
def _rand_cube(draw):
    """A random 0/1 detection cube (2<=D<=5 columns, 2<=N<=30 shots)."""
    d = draw(st.integers(2, 5))
    n = draw(st.integers(2, 30))
    bits = draw(st.lists(st.integers(0, 1), min_size=n * d, max_size=n * d))
    return np.array(bits, dtype=np.uint8).reshape(n, d)


@settings(max_examples=300, deadline=None)
@given(_rand_cube())
def test_L1_pij_matrix_symmetry_and_upper_bound(cube):
    """diagnostics['pij'] is symmetric with zero diagonal, and every finite entry obeys
    the Spitz theorem p_ij = 1/2 - sqrt(nonneg) <= 1/2 (the raw estimate is stored, so
    negatives are ALLOWED -- the honest invariant is the upper bound + symmetry)."""
    names = tuple(f"d{i}" for i in range(cube.shape[1]))
    _, diag = records_to_dem(cube, detector_names=names)
    P = np.asarray(diag["pij"])
    assert np.allclose(P, P.T, atol=1e-12)
    assert np.allclose(np.diag(P), 0.0, atol=1e-12)
    fin = P[np.isfinite(P)]
    assert np.all(fin <= 0.5 + 1e-12)


@settings(max_examples=300, deadline=None)
@given(_rand_cube())
def test_L1_dem_error_probs_are_matchable_and_roundtrip(cube):
    """Every emitted error(p) is a matchable weight 0 <= p < 0.5 (the _MAX_EDGE_P cap), and
    re-reading the DEM reproduces the diagnostics' edge/boundary counts (round-trip)."""
    names = tuple(f"d{i}" for i in range(cube.shape[1]))
    dem, diag = records_to_dem(cube, detector_names=names)
    edge_p, bnd_p = _parse_dem(dem)
    for p in edge_p + bnd_p:
        assert 0.0 <= p < 0.5
    assert len(edge_p) == len(diag["edges"])
    assert len(bnd_p) == len(diag["boundaries"])


def test_L1_decode_output_contract():
    """decode_records returns (N,) uint8 in {0,1} (the real 2-D PyMatching path)."""
    det = _planted_cube()
    dem, _ = records_to_dem(
        det, detector_names=("d0", "d1", "d2", "d3"), logical_boundary_detectors=("d2",)
    )
    out = decode_records(dem, det)
    assert out.shape == (det.shape[0],)
    assert out.dtype == np.uint8
    assert set(np.unique(out)).issubset({0, 1})


# =========================================================================== #
# VALUE PINS on the DIAGNOSTICS payload (mutation: dict keys, string labels,   #
# floors, SE convention, SE matrix, boundary-comparison strictness)            #
# =========================================================================== #
_EXPECTED_DIAG_KEYS = {
    "num_shots", "num_detectors", "detector_names", "marginals", "pij", "pij_se",
    "edges", "boundaries", "clamped_boundaries", "logical_boundary_detectors",
    "logical_index", "floors", "pij_se_convention", "reduction_caveat",
}
_EXPECTED_NOTE = (
    "for cluster_size > 1 the SEs and the sigma edge floor are "
    "understated by the cluster design effect (trajectory "
    "common-mode, teacher S-1/C-11); declared, not corrected — "
    "bound at P1"
)
_EXPECTED_CAVEAT = (
    "two-point edge-factorized reduction (Spitz Eq. 13 exact pairs); "
    "structurally blind to hyperedges; logical attachment is a "
    "declared geometry rule, not estimated from records"
)


def test_PIN_diagnostics_structure_labels_and_floors():
    """Pin the EXACT diagnostics schema + label strings + floors dict + SE-convention block.
    Kills every dict-key rename, string-literal wrap/upper/lower, and the epistemic-class /
    estimator / note / caveat value mutations -- none of which any structural assert can catch."""
    det = _planted_cube()
    m_ref, _ = _spitz_ref(det)
    names = ("d0", "d1", "d2", "d3")
    dem, diag = records_to_dem(
        det, detector_names=names, logical_boundary_detectors=("d2",), logical_index=0
    )
    assert set(diag.keys()) == _EXPECTED_DIAG_KEYS
    assert diag["num_shots"] == det.shape[0]
    assert diag["num_detectors"] == 4
    assert diag["detector_names"] == ["d0", "d1", "d2", "d3"]
    assert diag["logical_boundary_detectors"] == ["d2"]
    assert diag["logical_index"] == 0
    assert_pins(np.asarray(diag["marginals"]), m_ref, atol=1e-12, label="marginals")

    # floors sub-dict EXACT (keys + the epistemic_class == "c" value)
    assert diag["floors"] == {
        "pair_floor_abs": DEFAULT_PAIR_FLOOR_ABS,
        "pair_floor_sigma": DEFAULT_PAIR_FLOOR_SIGMA,
        "epistemic_class": "c",
    }
    # SE-convention block: EXACT keys + estimator/note strings + default cluster_size == 1
    conv = diag["pij_se_convention"]
    assert set(conv.keys()) == {
        "estimator", "cluster_size", "anti_conservative_for_clusters", "note"}
    assert conv["estimator"] == "spitz_pij_delta_se (shots as iid units)"
    assert conv["cluster_size"] == 1                                     # DEFAULT (kills default=2)
    assert conv["anti_conservative_for_clusters"] is False              # bool(1 > 1) (kills >=1)
    assert conv["note"] == _EXPECTED_NOTE
    assert diag["reduction_caveat"] == _EXPECTED_CAVEAT


def test_PIN_cluster_size_convention_flags():
    """The anti-conservative flag is bool(cluster_size > 1): False at 1, True at 2 -- pinning
    BOTH kills the bool(None) / '>= 1' / '> 2' comparison mutations AND the cluster_size passthrough."""
    det = _planted_cube()
    names = ("d0", "d1", "d2", "d3")
    _, d2 = records_to_dem(det, detector_names=names, cluster_size=2)
    assert d2["pij_se_convention"]["cluster_size"] == 2
    assert d2["pij_se_convention"]["anti_conservative_for_clusters"] is True     # bool(2>1)
    _, d1 = records_to_dem(det, detector_names=names, cluster_size=1)
    assert d1["pij_se_convention"]["anti_conservative_for_clusters"] is False    # bool(1>1)


def test_PIN_pij_se_matrix_vs_independent_recompute():
    """Pin diagnostics['pij_se'] (symmetric, non-negative, zero diagonal) to the INDEPENDENT
    from-scratch delta-method SE. Kills the where-condition / where-fill / matrix-sign
    mutations that a shapes-only assert leaves alive."""
    det = _planted_cube()
    SE_ref = _spitz_se_ref(det)
    _, diag = records_to_dem(det, detector_names=("d0", "d1", "d2", "d3"))
    S = diag["pij_se"]
    assert isinstance(S, np.ndarray) and S.shape == (4, 4)              # kills pij_se = None
    assert np.allclose(S, S.T, atol=1e-12)                             # symmetric (kills - .T)
    assert np.all(S >= -1e-12)                                          # non-negative
    assert np.allclose(np.diag(S), 0.0, atol=1e-12)
    assert_pins(S, SE_ref, atol=1e-9, label="pij_se matrix")           # kills the value/fill muts
    assert S[0, 1] > 1e-4                                               # the load-bearing entry is nonzero
    # non-finite SE (independent-0.5 pair) is filled with 0.0, NOT nan/1.0
    _, dgi = records_to_dem(_indep_half_cube(), detector_names=("d0", "d1"))
    Si = np.asarray(dgi["pij_se"])
    assert np.all(np.isfinite(Si)) and np.allclose(Si, 0.0, atol=1e-12)


def test_KILLER_floor_comparisons_are_strict_at_the_boundary():
    """The kept-edge floors use STRICT '>' -- an edge exactly AT the floor must be DROPPED (a
    '>' -> '>=' mutation would keep it). Exercised at exact equality for BOTH the absolute
    floor (floor == p_ij == 0.25) and the sigma floor (sigma*se == p_ij, by construction)."""
    det = _planted_cube()
    names = ("d0", "d1", "d2", "d3")

    def _kept(diag):
        return {(e["i"], e["j"]) for e in diag["edges"]}

    # absolute floor exactly at p_ij(0,1) = 0.25 -> strict '>' drops it
    _, d_abs = records_to_dem(det, detector_names=names, pair_floor_abs=0.25)
    assert (0, 1) not in _kept(d_abs)
    # sigma floor exactly at p_ij: sigma := p_ij / se so that sigma*se == p_ij (float-exact
    # here); strict '>' drops, '>=' keeps -> the '>' is load-bearing
    _, d0 = records_to_dem(det, detector_names=names)
    sigma = d0["pij"][0, 1] / d0["pij_se"][0, 1]
    _, d_sig = records_to_dem(det, detector_names=names, pair_floor_abs=0.0, pair_floor_sigma=sigma)
    assert (0, 1) not in _kept(d_sig)
    # sanity: a hair below either floor DOES keep it (the drop is the floor, not a dead edge)
    _, d_lo = records_to_dem(det, detector_names=names, pair_floor_abs=0.25 - 1e-6)
    assert (0, 1) in _kept(d_lo)


def test_KILLER_negative_residual_boundary_is_strict():
    """The negative-residual clamp uses STRICT '<' against -pair_floor_abs: a residual exactly
    at -pair_floor_abs is NOT recorded (a '<' -> '<=' mutation would record it)."""
    neg = _neg_resid_cube()
    _, d0 = records_to_dem(neg, detector_names=("d0", "d1"))
    p_raw = d0["clamped_boundaries"][0]["p_raw"]                        # the negative residual
    assert p_raw < 0
    # set pair_floor_abs so that -pair_floor_abs == p_raw EXACTLY (float negation is exact)
    _, d1 = records_to_dem(neg, detector_names=("d0", "d1"), pair_floor_abs=-p_raw)
    assert all(c["reason"] != "negative_residual" for c in d1["clamped_boundaries"])
    assert 0 not in {c["i"] for c in d1["clamped_boundaries"]}          # D0 silently skipped, not clamped


def test_KILLER_insert_op_carries_args_exact_circuit():
    """The op's probability args are load-bearing: insert an X_ERROR(0.125) at t==0 AND t>=1
    and pin the EXACT resulting circuit. A mutant dropping list(args) -> None makes stim raise
    on X_ERROR (which REQUIRES its probability), killing both append sites."""
    c = _tiny_circuit()
    got0 = insert_op_after_tick(c, 0, "X_ERROR", (0,), (0.125,))
    got1 = insert_op_after_tick(c, 1, "X_ERROR", (0,), (0.125,))
    assert "X_ERROR(0.125) 0" in str(got0)
    assert "X_ERROR(0.125) 0" in str(got1)
    exp0 = stim.Circuit()
    exp0.append("X_ERROR", [0], [0.125])
    exp0.append("X", [0]); exp0.append("TICK")
    exp0.append("Y", [0]); exp0.append("TICK")
    exp0.append("Z", [0])
    assert got0 == exp0
    exp1 = stim.Circuit()
    exp1.append("X", [0]); exp1.append("TICK")
    exp1.append("X_ERROR", [0], [0.125])
    exp1.append("Y", [0]); exp1.append("TICK")
    exp1.append("Z", [0])
    assert got1 == exp1

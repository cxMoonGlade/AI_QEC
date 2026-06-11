"""R2-lite M4 -- dem_compose build tests (S2 projection, S4 arms + structure
freeze, S5 twin->DEM composition, S6 P1c/P1f/P1h machinery, S12 stitched hybrid).

PRE-REGISTRATION: docs/metric_results.md "M4 PRE-REGISTRATION (decoder-prior
utility; recorded 2026-06-10 BEFORE build/run)"; reviewer blueprint
docs/.reports/m4_panel/R_reviewer_verdict.md. BUILD-ONLY scope: these are
scoped unit tests of the composition machinery -- no decoding, no pilot, ZERO
new twin fits (the frozen M3 cache is a read-only input). Hardware-gated tests
skip without QEC_TWIN_HW_DATA and touch ONLY sample_00 (samples 01-99 are
held-out-protected). The streaming pij-arm acceptance smoke is additionally
gated behind QEC_TWIN_M4_HEAVY=1 (minutes of sample_00 streaming).

Toy coverage (hand-built DEMs/grids, no dataset needed):
  - skeleton parse: graphlike-COMPONENT asserts (hyperedge components are
    rejected; ``^``-decomposed instructions are ACCEPTED with their component
    structure preserved -- the true I-3 precondition, FIX ROUND 2026-06-10);
  - decomposed machinery: byte-faithful round-trip, component-wise S2
    projection, conservative arm passthrough (identical across all arms),
    mean-matching site products including decomposed incidence;
  - P1c: parse -> serialize round-trip identity; restriction at the full chain
    = identity; clamp-hit accounting (G9);
  - detector coordinates (B-17, FIX ROUND 2 2026-06-10): source annotations
    captured/re-emitted byte-faithfully (P1c extended), projection
    passthrough, ``with_grid_coordinates`` canonical (chain, layer) swap that
    satisfies B2's A3c ``space_edge_geometry`` contract (toy + hardware);
  - S2 projection: one-detector-outside -> weight-1 at the survivor with the
    SAME p; sub-observable L0 carried by exactly the left-cut crossers;
  - S2 instruments: maximal disjoint partitions (registered counts) + advance
    hot-region flags;
  - S5: median-over-owners assignment (data interior positions {1,2,3} local,
    measure interior detectors), unowned-fill identity (twin == pij on every
    unowned cell BY CONSTRUCTION), the f_hat = r*R guard;
  - A2 pij arm: mean-matching exactness (composed site marginal == measured
    detection fraction at weight-1 sites), bulk pooling vs layer resolution;
  - A3b Spitz-of-the-twin: exact-recovery identities (R == 1 => time edge ==
    q_eff, space edge == r_hat for any R; bunching strictly inflates time/diag
    when R > 1), twin-implied mean-matching, pij fallback identity;
  - G6: extended_skeleton (mirror class, claim-flagged) + support census;
  - P1h acceptance identity; S12 stitched hybrid; G2 freeze manifest.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest
import stim

from qec_twin.hardware import dem_compose as dc
from qec_twin.hardware.b8_io import pack_bits
from qec_twin.hardware.dataset import resolve_rep29_root
from qec_twin.hardware.pij import accumulate_pair_counts
from qec_twin.hardware.stim_artifacts import DetectorGrid

TOY_LAYERS = 8
TOY_CHAINS = 10
TOY_WINDOWS = (1, 2, 3)  # toy clean-window stand-ins; data owned 3..7, measure owned 2..7
P_W1, P_SPACE, P_TIME, P_DIAG = 0.04, 0.02, 0.01, 0.004
TOY_SEED = dc.M4_SEED  # 20260610, ratified R3 for all new M4 randomness


# ---------------------------------------------------------------- toy fixtures


def toy_grid(layers: int = TOY_LAYERS, chains: int = TOY_CHAINS) -> DetectorGrid:
    return DetectorGrid(
        det_to_layer=np.repeat(np.arange(layers, dtype=np.int32), chains),
        det_to_chain=np.tile(np.arange(chains, dtype=np.int32), layers),
        grid=np.arange(layers * chains, dtype=np.int64).reshape(layers, chains),
        num_layers=layers,
        num_chains=chains,
        chain_order_source="synthetic",
    )


def toy_dem_text(
    layers: int = TOY_LAYERS,
    chains: int = TOY_CHAINS,
    *,
    extra_w1_chains: tuple = (),
    second_w1_at_chain0: bool = False,
) -> str:
    """Hand-built graphlike DEM on the complete toy grid: weight-1 boundary
    columns (chain 0 carries L0), space (di=1), time (dt=1), one diagonal
    orientation (+1) -- the SI1000 support shape."""

    c_max = chains - 1
    lines = []
    for l in range(layers):
        lines.append(f"error({P_W1}) D{l * chains} L0")
        if second_w1_at_chain0:
            lines.append(f"error(0.05) D{l * chains}")
        lines.append(f"error({P_W1}) D{l * chains + c_max}")
        for c in extra_w1_chains:
            lines.append(f"error(0.03) D{l * chains + c}")
    for l in range(layers):
        for c in range(chains - 1):
            lines.append(f"error({P_SPACE}) D{l * chains + c} D{l * chains + c + 1}")
    for l in range(layers - 1):
        for c in range(chains):
            lines.append(f"error({P_TIME}) D{l * chains + c} D{(l + 1) * chains + c}")
    for l in range(layers - 1):
        for c in range(chains - 1):
            lines.append(f"error({P_DIAG}) D{l * chains + c} D{(l + 1) * chains + c + 1}")
    return "\n".join(lines)


def toy_skeleton(**kwargs):
    grid = toy_grid()
    dem = stim.DetectorErrorModel(toy_dem_text(**kwargs))
    return dc.load_skeleton(dem, source="toy"), grid, dem


class _Rec:
    """Duck-typed stand-in for the frozen m3_report.FitRecord (markov [5, 2] =
    per-window-local data qubit (p01, p10); q_eff [4] = interior detectors)."""

    def __init__(self, markov, q_eff, ce):
        self.markov = np.asarray(markov, dtype=np.float64)
        self.q_eff = np.asarray(q_eff, dtype=np.float64)
        self.ce_per_block = float(ce)


def master_records(windows=TOY_WINDOWS, *, bunched: bool) -> dict:
    """Per-window records sharing one MASTER parameter table (medians ==
    master values): data qubit g -> (p01, p10), measure chain c -> q."""

    def pair(g):
        if bunched:
            return 0.006 + 0.0004 * g, 0.020 + 0.0008 * g  # p01 != p10 => R > 1
        p = 0.010 + 0.0005 * g
        return p, p  # R == 1 exactly

    recs = {}
    for w in windows:
        markov = [pair(w + 1 + k) for k in range(5)]
        q_eff = [0.012 + 0.0004 * (w + 1 + k) for k in range(4)]
        recs[int(w)] = _Rec(markov, q_eff, 1.0)
    return recs


def het_records(windows=TOY_WINDOWS) -> dict:
    """Records that DIFFER across windows -- exercises the true median."""

    recs = {}
    for w in windows:
        base = 0.008 + 0.002 * w
        markov = [[base + 0.001 * k, base + 0.0005 + 0.001 * k] for k in range(5)]
        q_eff = [0.010 + 0.001 * w + 0.0002 * k for k in range(4)]
        recs[int(w)] = _Rec(markov, q_eff, 1.0)
    return recs


def _find(sites, *, key=None, col=None, row=None, arity=None):
    out = []
    for i, s in enumerate(sites):
        if key is not None and s.key != key:
            continue
        if col is not None and s.col != col:
            continue
        if row is not None and s.row != row:
            continue
        if arity is not None and s.arity != arity:
            continue
        out.append(i)
    return out


# ---------------------------------------------------------------- exact identities


def test_markov_identities_exact():
    rng = np.random.default_rng(TOY_SEED)
    eps = np.finfo(np.float64).eps
    for _ in range(50):
        p01, p10 = rng.uniform(1e-4, 0.2, size=2)
        r, R, f = dc.r_hat(p01, p10), dc.R_hat(p01, p10), dc.f_hat(p01, p10)
        assert abs(r * R - f) < 1e-15, "r * R == f = (p01+p10)/2 is exact (a)"
        assert abs(f - 0.5 * (p01 + p10)) < 1e-18
        assert r <= f + 1e-18, "AM-HM: the marginal never exceeds the conditional"
        cov1 = dc.markov_flip_cov(p01, p10, 1)
        assert abs(cov1 - (p01 * p10 - r * r)) < 1e-18
        # cov1 == r^2 (R - 1) is exact ALGEBRA, but the float comparison is
        # cancellation-limited (FIX ROUND 2026-06-10): r_hat/R_hat carry O(eps)
        # RELATIVE error from a few roundings, so fl(R) = R (1 + k*eps); the
        # subtraction R - 1 is itself EXACT for R in [1, 2] (Sterbenz lemma),
        # but it inherits that absolute error ~ k*eps*R, whose RELATIVE size
        # blows up as R -> 1 (p01 ~ p10) while cov1 = r^2 (R - 1) -> 0. The
        # product r^2 (R - 1) therefore carries absolute error ~ k*eps*r^2*R
        # REGARDLESS of how small R - 1 is; likewise cov1 = p01*p10 - r^2
        # (two nearly-equal terms at R ~ 1) carries ~ k*eps*p01*p10. The
        # correct exact-identity budget is ABSOLUTE in those magnitudes --
        # never relative to the cancelling difference itself:
        #   |cov1 - r^2 (R-1)| <= C * eps * (r^2 * R + p01 * p10),  C = op-count
        # (C = 32 is generous for the ~6 roundings involved; a genuine algebra
        # error would be O(cov1) ~ r^2 |R-1|, many orders above this floor at
        # any (p01, p10) where the check is informative).
        tol = 32.0 * eps * (r * r * R + p01 * p10)
        assert abs(cov1 - r * r * (R - 1.0)) < tol
        lam = 1.0 - p01 - p10
        assert abs(dc.markov_flip_cov(p01, p10, 3) - lam**2 * cov1) < 1e-18


def test_guard_rejects_conditional_assignment():
    p01, p10 = 0.01, 0.03
    r, f, R = dc.r_hat(p01, p10), dc.f_hat(p01, p10), dc.R_hat(p01, p10)
    dc.assert_marginal_not_conditional(r, r, f, R)  # the registered assignment passes
    with pytest.raises(AssertionError):
        dc.assert_marginal_not_conditional(f, r, f, R)  # f = r*R wired in -> guard trips
    with pytest.raises(AssertionError):
        dc.assert_marginal_not_conditional(f + 0.01, r, f, R)  # above f: always mis-wired
    with pytest.raises(AssertionError):
        dc.assert_marginal_not_conditional(0.5 * (r + f), r, f, R)  # not the r median


# ---------------------------------------------------------------- skeleton + P1c


def test_load_skeleton_graphlike_component_asserts():
    skel, _, _ = toy_skeleton()
    assert skel.num_errors == 2 * TOY_LAYERS + TOY_LAYERS * 9 + 7 * TOY_CHAINS + 7 * 9
    assert skel.arity_census() == {1: 2 * TOY_LAYERS, 2: 72 + 70 + 63}
    assert skel.num_decomposed == 0
    assert skel.component_census() == skel.arity_census()
    # the true I-3 precondition is graphlike COMPONENTS: a 3-detector component
    # is a hyperedge and is rejected; a ^-decomposed instruction is ACCEPTED
    # with its component structure preserved (FIX ROUND 2026-06-10)
    with pytest.raises(ValueError, match="graphlike"):
        dc.load_skeleton(stim.DetectorErrorModel("error(0.1) D0 D1 D2"))
    with pytest.raises(ValueError, match="graphlike"):
        dc.load_skeleton(stim.DetectorErrorModel("error(0.1) D0 D1 D2 ^ D3"))
    skel2 = dc.load_skeleton(stim.DetectorErrorModel("error(0.1) D0 D1 ^ D2 D3"))
    assert skel2.num_decomposed == 1
    assert skel2.comps[0] == (((0, 1), ()), ((2, 3), ()))
    assert skel2.dets[0] == (0, 1, 2, 3) and skel2.obs[0] == ()
    assert skel2.arity_census() == {4: 1} and skel2.component_census() == {2: 2}


def test_roundtrip_identity_p1c():
    skel, _, dem = toy_skeleton()
    emitted, clamp = dc.with_probabilities(skel, skel.p)
    assert clamp.total_hits == 0
    assert emitted == dem, "P1c: serialize(parse(dem)) == dem on an errors-only DEM"
    report = dc.roundtrip_report(dem)
    print(f"P1c toy round-trip: {report}")
    assert report["errors_equal"] and report["p_bitexact_unclamped"]
    assert report["num_detectors_preserved"]


def test_with_probabilities_clamp_accounting():
    skel, _, _ = toy_skeleton()
    column = skel.p.copy()
    column[0] = 0.0
    column[1] = 0.7
    emitted, clamp = dc.with_probabilities(skel, column)
    assert (clamp.low_hits, clamp.high_hits) == (1, 1), "G9 clamp-hit counts"
    back = dc.load_skeleton(emitted)
    assert back.p[0] == dc.CLAMP_LO and abs(back.p[1] - dc.CLAMP_HI) < 1e-15
    assert np.array_equal(back.p[2:], skel.p[2:])


def test_dem_sha256_p1f():
    skel, _, dem = toy_skeleton()
    h1 = dc.dem_sha256(dem)
    assert len(h1) == 64 and h1 == dc.dem_sha256(dem)
    other, _ = dc.with_probabilities(skel, np.full(skel.num_errors, 0.01))
    assert dc.dem_sha256(other) != h1


# ------------------------------------------- detector coordinates (B-17, FIX ROUND 2)


def toy_device_coords(layers: int = TOY_LAYERS, chains: int = TOY_CHAINS) -> dict:
    """Device-style (x, y, t) annotations deliberately NOT (chain, layer) --
    mimics the shipped SI1000 DEM (whose coords are device triplets, measured
    2026-06-10); detector 0 carries a non-integral x to pin float fidelity."""

    coords = {}
    for l in range(layers):
        for c in range(chains):
            d = l * chains + c
            x = 2 * c + 1 + (0.5 if d == 0 else 0)
            coords[d] = (float(x), float(7 - c), float(10 * l))
    return coords


def toy_skeleton_with_coords():
    grid = toy_grid()
    coords = toy_device_coords()
    coord_lines = "\n".join(
        "detector(" + ", ".join(dc._fmt_coord(v) for v in coords[d]) + f") D{d}"
        for d in sorted(coords)
    )
    dem = stim.DetectorErrorModel(toy_dem_text() + "\n" + coord_lines)
    return dc.load_skeleton(dem, source="toy"), grid, dem, coords


def test_coords_capture_emission_roundtrip():
    """B-17 (1): source coordinate annotations are CAPTURED, re-EMITTED
    faithfully, and survive the P1c parse -> serialize -> parse round-trip;
    annotation-free DEMs keep coords=None (legacy path untouched)."""

    skel, _, dem, coords = toy_skeleton_with_coords()
    assert skel.coords is not None and len(skel.coords) == TOY_LAYERS * TOY_CHAINS
    assert skel.coords[0] == (1.5, 7.0, 0.0), "non-integral value captured exactly"
    assert skel.coords[1] == (3.0, 6.0, 0.0)
    emitted, clamp = dc.with_probabilities(skel, skel.p)
    assert clamp.total_hits == 0
    assert emitted == dem, "errors AND coordinate annotations byte-faithful (P1c)"
    report = dc.roundtrip_report(dem)
    assert report["errors_equal"] and report["coords_equal"]
    assert report["num_detectors_preserved"]
    # legacy: an annotation-free DEM stays coords=None and still round-trips
    bare, _, bare_dem = toy_skeleton()
    assert bare.coords is None
    assert dc.roundtrip_report(bare_dem)["coords_equal"]
    # mixed: a bare detector declaration among annotated ones survives as ()
    mixed = stim.DetectorErrorModel("error(0.1) D0 D1\ndetector(4, 2) D0\ndetector D1")
    mskel = dc.load_skeleton(mixed)
    assert mskel.coords == ((4.0, 2.0), ())
    m_emitted, _ = dc.with_probabilities(mskel, mskel.p)
    assert dc.load_skeleton(m_emitted).coords == mskel.coords


# ---------------------------------------------------------------- S2 projection


def test_full_restriction_is_identity():
    skel, grid, _ = toy_skeleton()
    sub = dc.subchain_skeleton(skel, grid, 0, TOY_CHAINS)
    assert sub.dets == skel.dets and sub.obs == skel.obs
    assert np.array_equal(sub.p, skel.p)
    assert np.array_equal(sub.detector_ids, np.arange(TOY_LAYERS * TOY_CHAINS))


def test_subchain_projection_crossers_and_observable():
    skel, grid, _ = toy_skeleton()
    sub = dc.subchain_skeleton(skel, grid, 2, 7)  # data 2..7 -> chains 2..6
    assert np.array_equal(
        np.unique(grid.det_to_chain[sub.detector_ids]), np.arange(2, 7)
    )
    # census: 32 space-in + 8 left + 8 right crossers, 35 time, 28 diag-in + 14 diag crossers
    assert sub.num_errors == 32 + 16 + 35 + 28 + 14
    sites = dc.error_sites(sub, grid)
    w1 = [i for i, s in enumerate(sites) if s.arity == 1]
    assert len(w1) == 16 + 14, "every crosser became a weight-1 edge at its survivor"
    # the SAME p travels with the crosser (a)
    for i in w1:
        assert sub.p[i] in (P_SPACE, P_DIAG)
    # sub-observable: L0 on exactly the left-cut crossers (all at chain data_lo = 2)
    flagged = [i for i in range(sub.num_errors) if sub.obs[i]]
    assert flagged and all(sites[i].arity == 1 and sites[i].col == 2 for i in flagged)
    assert len(flagged) == 8 + 7  # space (1,2) per layer + diag (1,l)->(2,l+1)
    unflagged_w1_cols = {sites[i].col for i in w1 if not sub.obs[i]}
    assert unflagged_w1_cols == {6}, "right crossers carry no observable"
    # fully-inside errors carry no observable once the left edge moved
    assert all(not sub.obs[i] for i in range(sub.num_errors) if sites[i].arity == 2)


def test_subchain_emission_pins_detector_count():
    skel, grid, _ = toy_skeleton()
    sub = dc.subchain_skeleton(skel, grid, 2, 7)
    dem, _ = dc.with_probabilities(sub, sub.p)
    assert dem.num_detectors == len(sub.detector_ids) == 5 * TOY_LAYERS


def test_window_skeleton_is_the_d5_subchain():
    skel, grid, _ = toy_skeleton()
    win = dc.window_skeleton(skel, grid, 1)  # data 2..6, interior chains 2..5
    sub = dc.subchain_skeleton(skel, grid, 2, 6)
    assert win.dets == sub.dets and win.obs == sub.obs
    assert np.array_equal(np.unique(grid.det_to_chain[win.detector_ids]), np.arange(2, 6))


def test_subchain_coords_passthrough_and_grid_canonical():
    """B-17 (2): projection passes SOURCE annotations through unchanged for
    surviving detectors (identity at full restriction, P1c); the canonical
    ``with_grid_coordinates`` swap emits integral global (chain, layer) that
    satisfies B2's A3c geometry contract (``space_edge_geometry``)."""

    skel, grid, _, coords = toy_skeleton_with_coords()
    # full restriction: identity on coords too
    full = dc.subchain_skeleton(skel, grid, 0, TOY_CHAINS)
    assert full.coords == skel.coords
    # sub-chain: each survivor keeps its device annotation VERBATIM
    sub = dc.subchain_skeleton(skel, grid, 2, 7)  # data 2..7 -> chains 2..6
    assert sub.coords is not None and len(sub.coords) == 5 * TOY_LAYERS
    assert sub.coords == tuple(coords[int(d)] for d in sub.detector_ids)
    # canonical swap: global (chain, layer) ranks, structure untouched
    canon = dc.with_grid_coordinates(sub, grid)
    assert canon.dets == sub.dets and canon.obs == sub.obs and canon.comps == sub.comps
    assert np.array_equal(canon.p, sub.p)
    assert canon.coords == tuple(
        (float(grid.det_to_chain[int(d)]), float(grid.det_to_layer[int(d)]))
        for d in sub.detector_ids
    )
    dem_c, _ = dc.with_probabilities(canon, canon.p)
    assert dem_c.num_detectors == 5 * TOY_LAYERS
    # the A3c consumer contract engages (this is the B-17 acceptance):
    # bulk space pairs (2,3)..(5,6) x 8 layers = 32 entries; left-cut w1
    # survivors at chain 2 -> qkey (1,2) on layers 0..7 (space crossers at l,
    # diag crossers landing at l+1 share the same detector => same key);
    # right-cut survivors at chain 6 -> qkey (6,7), 8 layers: 32+8+8 = 48.
    # Qubit keys are GLOBAL (g-1, g) for data qubits g = 2..7 -- the B-16
    # adaptor convention aligning two_pass_table's data-qubit indexing.
    from qec_twin.hardware.m4_decode import space_edge_geometry

    geo = space_edge_geometry(dem_c)
    qkeys = {q for _, q, _ in geo.classify.values()}
    assert qkeys == {(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)}
    assert geo.num_space_edges == 48
    assert geo.num_unclassified_singles == 0
    # the DEVICE annotations must NOT be fed to the geometry contract: here
    # the non-integral x at detector 0 trips the contract loudly; NOTE the
    # contract canNOT catch integral device coords (it would silently mis-key
    # qubits -- the real-DEM x is integral but is not the chain rank), so the
    # canonical transform is MANDATORY for A3c emission, never optional.
    dem_dev, _ = dc.with_probabilities(skel, skel.p)
    with pytest.raises(ValueError, match="integral"):
        space_edge_geometry(dem_dev)


def test_decomposed_roundtrip_projection_and_arm_passthrough():
    """Decomposed-instruction machinery (FIX ROUND 2026-06-10; the shipped
    SI1000 exact DEM carries 2,002 ^-decomposed instructions, 2 components
    each, every component <= 2 detectors -- measured 2026-06-10, both bases):
    byte-faithful parse/emit, component-wise S2 projection, conservative arm
    passthrough (identical across all arms => zero contrast contribution),
    and mean-matching site products that include decomposed incidence."""

    grid = toy_grid()
    # two space-edge components in layer 3 (chains (2,3) + (5,6)), the left one
    # carrying L0; plus a w1-component + space-component instruction whose w1
    # component sits ON the chain-0 mean-matching site of layer 3
    extra = ("error(0.015) D32 D33 L0 ^ D35 D36\n"
             "error(0.011) D30 ^ D38 D39")
    dem = stim.DetectorErrorModel(toy_dem_text() + "\n" + extra)
    skel = dc.load_skeleton(dem, source="toy")
    n_base = 2 * TOY_LAYERS + 72 + 70 + 63
    assert skel.num_errors == n_base + 2 and skel.num_decomposed == 2
    assert skel.comps[-2] == (((32, 33), (0,)), ((35, 36), ()))
    assert skel.comps[-1] == (((30,), ()), ((38, 39), ()))
    assert skel.dets[-2] == (32, 33, 35, 36) and skel.obs[-2] == (0,)

    # byte-faithful emission: separators, component order, per-component L0
    emitted, clamp = dc.with_probabilities(skel, skel.p)
    assert clamp.total_hits == 0 and emitted == dem
    assert dc.roundtrip_report(dem)["errors_equal"]

    # instruction-level sentinel + per-component classification + census label
    sites = dc.error_sites(skel, grid)
    assert sites[-2].num_components == 2 and sites[-2].key is None
    csites = dc.component_sites(skel, grid)
    assert [cs.key for cs in csites[-2]] == [(1, 0, 0), (1, 0, 0)]
    assert csites[-1][0].arity == 1 and csites[-1][1].key == (1, 0, 0)
    census = dc.support_census({"toy": (skel, skel.p)}, grid=grid)["toy"]
    assert census["decomposed[space(di=1)+space(di=1)]"]["count"] == 1
    assert census["decomposed[space(di=1)+w1]"]["count"] == 1

    # component-wise S2 (registered rule, applied per component):
    # full restriction stays the bit-identity (P1c)
    full = dc.subchain_skeleton(skel, grid, 0, TOY_CHAINS)
    assert full.dets == skel.dets and full.obs == skel.obs and full.comps == skel.comps
    # one component entirely outside -> dropped; the survivor becomes the
    # plain graphlike edge it now is (single component, no left-cut L0)
    sub = dc.subchain_skeleton(skel, grid, 4, TOY_CHAINS)  # chains 4..9
    j = int(np.flatnonzero(sub.p == 0.015)[0])
    assert sub.comps[j] == (((35, 36), ()),) and sub.obs[j] == ()
    # one component loses one detector (weight-1 survivor + L0 at the left
    # cut), the other survives whole -- same probability slot throughout
    sub2 = dc.subchain_skeleton(skel, grid, 3, 8)  # chains 3..7
    j2 = sub2.dets.index((33, 35, 36))
    assert sub2.comps[j2] == (((33,), (0,)), ((35, 36), ())) and sub2.p[j2] == 0.015
    # all components gone => the instruction is dropped
    sub3 = dc.subchain_skeleton(skel, grid, 7, TOY_CHAINS)  # chains 7..9
    assert 0.015 not in sub3.p
    j3 = int(np.flatnonzero(sub3.p == 0.011)[0])
    assert sub3.dets[j3] == (38, 39) and sub3.obs[j3] == ()
    # dropping an observable-carrying component while the left edge is
    # unchanged would silently change the observable -> loud failure
    with pytest.raises(ValueError, match="observable-carrying component"):
        dc.subchain_skeleton(
            dc.load_skeleton(stim.DetectorErrorModel("error(0.1) D0 ^ D38 D39 L0")),
            grid, 0, 8,
        )

    # arms: conservative passthrough -- decomposed slots carry the shipped
    # value in A2 and copy the pij column in A3/A3b => identical everywhere
    counts = _toy_counts(grid, seed=TOY_SEED + 8)
    pij, report = dc.arm_pij(
        counts, grid, skel, layer_lo=0, layer_hi=TOY_LAYERS - 1, return_report=True
    )
    i_a, i_b = skel.num_errors - 2, skel.num_errors - 1
    assert report["decomposed_passthrough"] == 2
    assert pij[i_a] == 0.015 and pij[i_b] == 0.011
    # mean-matching stays EXACT at the chain-0 site that carries the
    # decomposed w1 component (its factor enters the site product)
    composed = dc.composed_site_marginals(skel, pij)
    local30 = int(np.searchsorted(skel.detector_ids, 30))
    pooled0 = float((counts.grid_counts[:, 0] / counts.num_shots).mean())
    assert abs(composed[local30] - pooled0) < 1e-12
    records = master_records(bunched=True)
    twin, table = dc.arm_twin_static(
        records, TOY_WINDOWS, grid, pij, skel=skel, layer_lo=0, layer_hi=TOY_LAYERS - 1
    )
    assert table["unowned_census"]["decomposed"] == 2
    assert twin[i_a] == pij[i_a] and twin[i_b] == pij[i_b]
    a3b, rep3 = dc.arm_spitz_of_twin(
        records, TOY_WINDOWS, grid, skel, pij_probs=pij,
        layer_lo=0, layer_hi=TOY_LAYERS - 1, return_report=True,
    )
    assert rep3["decomposed_fallback_groups"] == 2
    assert a3b[i_a] == pij[i_a] and a3b[i_b] == pij[i_b]


def test_disjoint_partitions_registered_counts_and_hot_flags():
    registered = {5: 5, 7: 4, 9: 3, 11: 2, 13: 2, 15: 1, 17: 1, 19: 1, 21: 1}
    for d_prime, count in registered.items():
        parts = dc.disjoint_partitions(d_prime)
        assert len(parts) == count, f"S2 registered partition count at d'={d_prime}"
        assert parts[0][0] == 0 and all(hi - lo + 1 == d_prime for lo, hi in parts)
        spans = [set(range(lo, hi + 1)) for lo, hi in parts]
        assert all(a.isdisjoint(b) for i, a in enumerate(spans) for b in spans[i + 1:])
    table5 = dc.partition_table(5)
    assert [row["hot"] for row in table5] == [False, False, False, True, True]
    table9 = dc.partition_table(9)
    assert [row["hot"] for row in table9] == [False, False, True]
    print(f"d'=5 partitions: {table5}")


# ---------------------------------------------------------------- frozen-fit selection


def test_select_frozen_records_lower_train_ce_rule():
    rec_a, rec_b = het_records()[1], het_records()[2]
    rec_a.ce_per_block, rec_b.ce_per_block = 2.0, 1.0
    raw = {"X/3/0/full": rec_a, "X/3/1/full": rec_b, "X/3/0/first_half": rec_a}
    selected, keys = dc.select_frozen_records(raw, [3], basis="X")
    assert selected[3] is rec_b and keys == ("X/3/1/full",)
    with pytest.raises(KeyError, match="ZERO new fits"):
        dc.select_frozen_records(raw, [4], basis="X")
    with pytest.raises(ValueError, match="basis"):
        dc.select_frozen_records(raw, [3])
    direct = {3: rec_a}
    passed, _ = dc.select_frozen_records(direct, [3])
    assert passed[3] is rec_a


# ---------------------------------------------------------------- S5 twin arm


def test_arm_naive_is_the_skeleton_column():
    skel, _, _ = toy_skeleton()
    naive = dc.arm_naive(skel)
    assert np.array_equal(naive, skel.p) and naive is not skel.p


def test_twin_median_ownership_values():
    skel, grid, _ = toy_skeleton()
    records = het_records()
    rng = np.random.default_rng(TOY_SEED)
    pij = rng.uniform(1e-4, 1e-2, size=skel.num_errors)
    probs, table = dc.arm_twin_static(
        records, TOY_WINDOWS, grid, pij, skel=skel, layer_lo=0, layer_hi=TOY_LAYERS - 1
    )
    sites = dc.error_sites(skel, grid)
    # data g=5: owners {1 (k=3), 2 (k=2), 3 (k=1)} -- median of three r_hat values
    expected_r5 = float(
        np.median(
            [dc.r_hat(*records[w].markov[5 - w - 1]) for w in TOY_WINDOWS]
        )
    )
    assert table["space"][5]["owners"] == (1, 2, 3)
    for i in _find(sites, key=(1, 0, 0), col=4):
        assert probs[i] == expected_r5
    # data g=3: single owner window 1 (k=1)
    assert table["space"][3]["owners"] == (1,)
    expected_r3 = dc.r_hat(*records[1].markov[1])
    for i in _find(sites, key=(1, 0, 0), col=2):
        assert probs[i] == expected_r3
    # measure chain 4: owners {1 (k=2), 2 (k=1), 3 (k=0)} -- median of three q_eff
    expected_q4 = float(np.median([records[w].q_eff[4 - w - 1] for w in TOY_WINDOWS]))
    assert table["time"][4]["owners"] == (1, 2, 3)
    for i in _find(sites, key=(0, 1, 0), col=4):
        assert probs[i] == expected_q4
    assert table["guard"]["passed"] and table["guard"]["space_groups_checked"] > 0


def test_twin_unowned_fill_identity_by_construction():
    skel, grid, _ = toy_skeleton()
    records = het_records()
    rng = np.random.default_rng(TOY_SEED + 1)
    pij = rng.uniform(1e-4, 1e-2, size=skel.num_errors)
    probs, table = dc.arm_twin_static(
        records, TOY_WINDOWS, grid, pij, skel=skel, layer_lo=2, layer_hi=5
    )
    assigned = table["assigned_mask"]
    assert np.array_equal(probs[~assigned], pij[~assigned]), "twin == pij on EVERY unowned cell"
    assert table["unowned_identical_to_pij"]
    sites = dc.error_sites(skel, grid)
    census = table["unowned_census"]
    assert census["weight1"] == 2 * TOY_LAYERS
    assert census["diagonal"] == 7 * 9
    # bulk window [2, 5]: space rows {0,1,6,7} and time rows {0,1,5,6,7} are out
    for i in _find(sites, key=(1, 0, 0), col=4, row=1):
        assert not assigned[i] and probs[i] == pij[i]
    for i in _find(sites, key=(0, 1, 0), col=4, row=5):  # layers (5, 6): 6 > 5
        assert not assigned[i] and probs[i] == pij[i]
    # chain ends: data {1, 2} and {8, 9, 10} own no window; measure {0, 1} / {8, 9}
    for col in (0, 1, 7, 8):  # data 1, 2, 8, 9
        for i in _find(sites, key=(1, 0, 0), col=col, row=3):
            assert not assigned[i]
    assert census["chain_end_or_gap_space"] > 0
    assert census["boundary_or_gap_measure"] > 0
    assert table["num_assigned"] + table["num_unowned"] == skel.num_errors
    # owned cells: data 3..7, measure 2..7 (toy windows {1,2,3})
    assert sorted(table["space"]) == [3, 4, 5, 6, 7]
    assert sorted(table["time"]) == [2, 3, 4, 5, 6, 7]


def test_two_pass_table_medians_and_R_formula():
    records = het_records()
    table = dc.two_pass_table(records, TOY_WINDOWS)
    assert sorted(table) == [3, 4, 5, 6, 7]
    expected_r5 = float(np.median([dc.r_hat(*records[w].markov[5 - w - 1]) for w in TOY_WINDOWS]))
    expected_R5 = float(np.median([dc.R_hat(*records[w].markov[5 - w - 1]) for w in TOY_WINDOWS]))
    assert table[5] == (expected_r5, expected_R5)
    assert abs(dc.R_hat(0.01, 0.04) - 1.5625) < 1e-15  # (0.05)^2 / (4 * 4e-4) exactly


# ---------------------------------------------------------------- P1h acceptance


def test_acceptance_identity_and_tolerance():
    dem = stim.DetectorErrorModel("error(0.1) D0 D1\nerror(0.2) D1 D3\nerror(0.05) D2")
    skel = dc.load_skeleton(dem)
    probs = skel.p
    marginals = dc.composed_site_marginals(skel, probs)
    expected = np.array([0.1, 0.5 * (1 - 0.8 * 0.6), 0.05, 0.2])
    assert np.allclose(marginals, expected, atol=1e-15)
    _, ok = dc.acceptance_check(skel, probs, expected)
    assert bool(ok) and ok.max_abs_dev < 1e-15 and ok.num_out == 0
    _, bad = dc.acceptance_check(skel, probs, expected + 0.006)
    assert not bool(bad) and bad.num_out == 4 and bad.tol == dc.ACCEPTANCE_TOL


# ---------------------------------------------------------------- A2 pij arm


def _toy_counts(grid, *, shots=4000, p=0.05, seed=TOY_SEED):
    rng = np.random.default_rng(seed)
    bits = (rng.random((shots, grid.num_layers * grid.num_chains)) < p).astype(np.uint8)
    packed = pack_bits(bits)
    handle, path = tempfile.mkstemp(suffix=".b8")
    os.close(handle)
    packed.tofile(path)
    try:
        counts = accumulate_pair_counts(
            path, grid, far_pairs=np.array([[0, grid.num_layers * grid.num_chains - 1]])
        )
    finally:
        os.unlink(path)
    return counts


def test_arm_pij_mean_matching_exactness():
    skel, grid, _ = toy_skeleton(second_w1_at_chain0=True)
    counts = _toy_counts(grid)
    probs, report = dc.arm_pij(
        counts, grid, skel, layer_lo=0, layer_hi=TOY_LAYERS - 1, return_report=True
    )
    print(f"A2 toy report: {report}")
    assert np.all(probs >= dc.CLAMP_LO) and np.all(probs <= dc.CLAMP_HI)
    # mean-matching EXACTNESS: composed marginal == measured f at every w1 site
    composed = dc.composed_site_marginals(skel, probs)
    measured = dc.detection_fraction_global(counts, grid)[skel.detector_ids]
    sites = dc.error_sites(skel, grid)
    w1_local = sorted(
        {int(np.searchsorted(skel.detector_ids, skel.dets[i][0]))
         for i in range(skel.num_errors) if sites[i].arity == 1}
    )
    # bulk pooling => composed at a bulk w1 site matches the POOLED chain fraction
    for li in w1_local:
        chain = int(grid.det_to_chain[skel.detector_ids[li]])
        pooled = float((counts.grid_counts[:, chain] / counts.num_shots).mean())
        assert abs(composed[li] - pooled) < 1e-12, "M3 mean-matching identity (exact)"
    # the two parallel slots at a chain-0 site carry EQUAL split probabilities
    chain0_w1 = [i for i in range(skel.num_errors)
                 if sites[i].arity == 1 and sites[i].col == 0 and sites[i].row == 3]
    assert len(chain0_w1) == 2 and probs[chain0_w1[0]] == probs[chain0_w1[1]]
    assert report["w1_sites"] == 2 * TOY_LAYERS  # chains {0, 9} x layers (2 slots share site)
    rerun = dc.arm_pij(counts, grid, skel, layer_lo=0, layer_hi=TOY_LAYERS - 1)
    np.testing.assert_array_equal(probs, rerun, err_msg="A2 writer must be deterministic")
    print(f"A2 toy: composed-vs-measured(site-resolved) max dev at w1 sites "
          f"{max(abs(composed[li] - measured[li]) for li in w1_local):.2e} (pooled f used)")


def test_arm_pij_bulk_pooled_vs_layer_resolved():
    from qec_twin.hardware.pij import _class_moment_planes, spitz_pij_exact

    skel, grid, _ = toy_skeleton()
    counts = _toy_counts(grid, seed=TOY_SEED + 2)
    lo, hi = 2, 5
    probs, report = dc.arm_pij(counts, grid, skel, layer_lo=lo, layer_hi=hi, return_report=True)
    sites = dc.error_sites(skel, grid)
    moments = _class_moment_planes(counts, grid)
    mi, mj, mij = moments[(1, 0, 0)]
    # bulk space edges (rows 2..5) share ONE pooled value per chain pair
    bulk_idx = [i for i in _find(sites, key=(1, 0, 0), col=3) if lo <= sites[i].row <= hi]
    pooled = float(spitz_pij_exact(
        np.float64(mi[lo : hi + 1, 3].mean()),
        np.float64(mj[lo : hi + 1, 3].mean()),
        np.float64(mij[lo : hi + 1, 3].mean()),
    ))
    expected_bulk = min(max(pooled, dc.CLAMP_LO), dc.CLAMP_HI)
    assert all(probs[i] == expected_bulk for i in bulk_idx)
    # outside the bulk window: the layer-resolved per-entry value (M1-P6 profile kept)
    outside = _find(sites, key=(1, 0, 0), col=3, row=0)
    expected_out = float(spitz_pij_exact(
        np.float64(mi[0, 3]), np.float64(mj[0, 3]), np.float64(mij[0, 3])
    ))
    expected_out = min(max(expected_out, dc.CLAMP_LO), dc.CLAMP_HI)
    assert all(probs[i] == expected_out for i in outside)
    assert report["bulk_pooled_groups"] > 0 and report["layer_resolved_groups"] > 0


# ---------------------------------------------------------------- A3b Spitz-of-the-twin


def test_spitz_of_twin_exact_recovery_identities():
    skel, grid, _ = toy_skeleton()
    records = master_records(bunched=False)  # R == 1 exactly
    rng = np.random.default_rng(TOY_SEED + 3)
    pij = rng.uniform(1e-4, 1e-2, size=skel.num_errors)
    twin, _ = dc.arm_twin_static(
        records, TOY_WINDOWS, grid, pij, skel=skel, layer_lo=0, layer_hi=TOY_LAYERS - 1
    )
    a3b, report = dc.arm_spitz_of_twin(
        records, TOY_WINDOWS, grid, skel, pij_probs=pij,
        layer_lo=0, layer_hi=TOY_LAYERS - 1, return_report=True,
    )
    print(f"A3b toy (R=1) report: {report}")
    sites = dc.error_sites(skel, grid)
    # R == 1: the twin-implied statistics invert EXACTLY back to q (time) and r (space)
    for i in _find(sites, key=(0, 1, 0), col=4):
        assert abs(a3b[i] - twin[i]) < 1e-9, "dt=1 time edge: Spitz-of-the-twin == q_eff"
    for i in _find(sites, key=(1, 0, 0), col=4):  # data 5: shared-flip exact recovery
        assert abs(a3b[i] - twin[i]) < 1e-9, "space edge: Spitz-of-the-twin == r_hat"
    # R == 1: diagonals carry zero twin-implied two-point mass -> clamp floor
    diag_owned = [i for i in _find(sites, key=(1, 1, 1), col=4)]
    assert diag_owned and all(a3b[i] == dc.CLAMP_LO for i in diag_owned)
    # uncovered cells copy pij IDENTICALLY (w1 chains 0/9; chain-end edges)
    for i in range(skel.num_errors):
        if sites[i].arity == 1:
            assert a3b[i] == pij[i]
    for i in _find(sites, key=(1, 0, 0), col=0):
        assert a3b[i] == pij[i]


def test_spitz_of_twin_bunching_inflates_time_and_diag():
    skel, grid, _ = toy_skeleton()
    records = master_records(bunched=True)  # R > 1
    rng = np.random.default_rng(TOY_SEED + 4)
    pij = rng.uniform(1e-4, 1e-2, size=skel.num_errors)
    twin, table = dc.arm_twin_static(
        records, TOY_WINDOWS, grid, pij, skel=skel, layer_lo=0, layer_hi=TOY_LAYERS - 1
    )
    a3b = dc.arm_spitz_of_twin(
        records, TOY_WINDOWS, grid, skel, pij_probs=pij,
        layer_lo=0, layer_hi=TOY_LAYERS - 1,
    )
    sites = dc.error_sites(skel, grid)
    i_time = _find(sites, key=(0, 1, 0), col=4)[0]
    i_space = _find(sites, key=(1, 0, 0), col=4)[0]
    i_diag = _find(sites, key=(1, 1, 1), col=4)[0]
    q_med = table["time"][4]["q_eff"]
    assert a3b[i_time] > q_med, "bunching shadow: dt=1 time edge strictly above q_eff"
    assert a3b[i_diag] > dc.CLAMP_LO, "bunching feeds the diagonal two-point shadow"
    assert abs(a3b[i_space] - twin[i_space]) < 1e-9, "space recovery stays exact at any R"
    print(f"A3b bunched toy: time {a3b[i_time]:.6f} vs q {q_med:.6f}; "
          f"diag {a3b[i_diag]:.2e}; space == r {a3b[i_space]:.6f}")


def test_spitz_of_twin_owned_weight1_mean_matching():
    """A3b twin-implied mean-matching at a covered weight-1 site -- the exact
    solve (FIX ROUND 2026-06-10, re-derived; this corrects build finding F2).

    The registered A3b boundary rule is mean-matching against the TWIN-IMPLIED
    site marginal: the single solves ``(1 - 2s) * Pi = 1 - 2 m_site`` with
    ``1 - 2 m_site = (1-2 r4)(1-2 r5)(1-2 q4)^2`` (the stationary site
    characteristic) and ``Pi`` the product of ``(1 - 2 p_e)`` over the OTHER
    incident assigned edges -- whatever is actually incident at that site on
    the given skeleton. At R == 1 the A3b inversion assigns space == r
    (exact), time(dt=1) == q (exact), diagonals == 0 -> clamp floor c. Hence:

    * INTERIOR layers ``1 <= l <= 6`` (two time edges + two diag floors
      incident): ``Pi = (1-2r4)(1-2r5)(1-2q4)^2 (1-2c)^2`` so
      ``(1-2m)/Pi = (1-2c)^{-2} > 1`` and ``raw = (1 - (1-2c)^{-2})/2
      ~= -2c < 0`` -- the twin-implied pair edges exactly consume the site
      budget and the solved single CLAMPS AT THE FLOOR (F2's saturation
      claim, valid exactly here).
    * TEMPORAL-BOUNDARY layers ``l in {0, 7}`` (ONE time edge, ONE diag):
      ``Pi = (1-2r4)(1-2r5)(1-2q4)(1-2c)`` so
      ``raw = (1 - (1-2q4)/(1-2c))/2 = (q4 - c)/(1 - 2c) ~= q4`` -- the
      single absorbs the MISSING time factor and lands near q4, NOT at the
      floor. F2's "the single clamps at the floor" over-generalized to these
      two layers; the implementation (solve against the actual incidence) is
      what the registration dictates, so the TEST expectation is corrected.

    On the real chain all weight-1 sites sit at unowned chains 0/27 (pij
    fallback) and the bulk window [80, 999] keeps temporal boundaries out of
    twin coverage, so both regimes are toy-only -- documented for the A3b
    results discussion."""

    skel, grid, _ = toy_skeleton(extra_w1_chains=(4,))
    records = master_records(bunched=False)  # R == 1: pair edges == {q, q, r4, r5} + floors
    rng = np.random.default_rng(TOY_SEED + 5)
    pij = rng.uniform(1e-4, 1e-2, size=skel.num_errors)
    a3b, report = dc.arm_spitz_of_twin(
        records, TOY_WINDOWS, grid, skel, pij_probs=pij,
        layer_lo=0, layer_hi=TOY_LAYERS - 1, return_report=True,
    )
    assert report["twin_w1_sites"] == TOY_LAYERS  # the owned chain-4 column
    sites = dc.error_sites(skel, grid)
    by_layer = {
        sites[i].row: i
        for i in range(skel.num_errors)
        if sites[i].arity == 1 and sites[i].col == 4
    }
    assert sorted(by_layer) == list(range(TOY_LAYERS))
    interior = [by_layer[l] for l in range(1, TOY_LAYERS - 1)]
    boundary = [by_layer[0], by_layer[TOY_LAYERS - 1]]
    assert all(a3b[i] == dc.CLAMP_LO for i in interior), (
        "interior budget saturation: the twin-implied single clamps at the floor"
    )
    q4 = 0.012 + 0.0004 * 4
    expected_boundary = (q4 - dc.CLAMP_LO) / (1.0 - 2.0 * dc.CLAMP_LO)
    for i in boundary:
        assert a3b[i] > 10 * dc.CLAMP_LO, "boundary single must NOT saturate"
        # the incident time edge carries the Spitz-inverted q (exact to ~1e-9)
        assert abs(a3b[i] - expected_boundary) < 1e-8, (
            "boundary single == (q4 - c)/(1 - 2c), the missing-time-factor solve"
        )
    composed = dc.composed_site_marginals(skel, a3b)
    p_master = 0.010 + 0.0005 * 4, 0.010 + 0.0005 * 5  # data 4, 5 (p01 == p10)
    char = (1 - 2 * p_master[0]) * (1 - 2 * p_master[1]) * (1 - 2 * q4) ** 2
    m_site = 0.5 * (1 - char)  # r_hat(p, p) == p analytically
    local = int(np.searchsorted(skel.detector_ids, grid.grid[3, 4]))
    assert abs(composed[local] - m_site) < 1e-5, (
        "composed == twin-implied marginal up to the floor resolution (~3e-6)"
    )
    print(f"A3b owned-w1: interior composed {composed[local]:.6e} vs twin-implied "
          f"{m_site:.6e} (floor-resolution gap {abs(composed[local] - m_site):.2e}); "
          f"boundary single {a3b[boundary[0]]:.6e} vs derived {expected_boundary:.6e}")
    with pytest.raises(ValueError, match="pij_probs"):
        dc.arm_spitz_of_twin(records, TOY_WINDOWS, grid, skel,
                             layer_lo=0, layer_hi=TOY_LAYERS - 1)


# ---------------------------------------------------------------- G6 extension + census


def test_extended_skeleton_mirror_is_claim_flagged_and_appended():
    skel, grid, _ = toy_skeleton()
    ext = dc.extended_skeleton(skel, grid)
    added = 7 * 9  # the absent (1,1,-1) mirror orientation over the toy grid
    assert ext.num_errors == skel.num_errors + added
    assert ext.dets[: skel.num_errors] == skel.dets, "original order is a prefix"
    assert ext.extended_mask is not None and int(ext.extended_mask.sum()) == added
    assert all(ext.obs[i] == () for i in range(skel.num_errors, ext.num_errors))
    assert "G6-ablation-secondary" in ext.source, "claim flag travels with the object"
    sites = dc.error_sites(ext, grid)
    assert all(sites[i].key == (1, 1, -1) for i in range(skel.num_errors, ext.num_errors))
    # the pij writer can fill the mirror class (the M1-measured device support)
    counts = _toy_counts(grid, seed=TOY_SEED + 6)
    probs = dc.arm_pij(counts, grid, ext, layer_lo=0, layer_hi=TOY_LAYERS - 1)
    assert np.isfinite(probs).all() and probs.min() >= dc.CLAMP_LO


def test_support_census_class_resolution():
    skel, grid, _ = toy_skeleton()
    ext = dc.extended_skeleton(skel, grid)
    census = dc.support_census(
        {"naive": (skel, skel.p), "ext": (ext, np.full(ext.num_errors, 0.01))}, grid=grid
    )
    naive = census["naive"]
    assert naive["w1"]["count"] == 2 * TOY_LAYERS
    assert naive["space(di=1)"]["count"] == 72
    assert naive["time(dt=1)"]["count"] == 70
    assert naive["diag(di=1,dt=1,orient=+1)"]["count"] == 63
    assert "diag(di=1,dt=1,orient=-1)" not in naive, "no primary carries the mirror class"
    assert census["ext"]["diag(di=1,dt=1,orient=-1)"]["extended"] == 63
    assert naive["space(di=1)"]["p_min"] == naive["space(di=1)"]["p_max"] == P_SPACE


# ---------------------------------------------------------------- S12 + G2


def test_stitched_hybrid_toy_disclosure():
    skel, grid, _ = toy_skeleton()
    counts = _toy_counts(grid, seed=TOY_SEED + 7)
    records = het_records()
    dem, audit = dc.stitched_hybrid(
        records, TOY_WINDOWS, grid, skel, counts=counts, layer_lo=0, layer_hi=TOY_LAYERS - 1
    )
    assert dem.num_detectors == TOY_LAYERS * TOY_CHAINS
    fill = audit["fill_disclosure"]
    assert fill["identical_on_unowned"], "S12 disclosure: pij fill is verbatim"
    assert fill["num_assigned"] + fill["num_unowned"] == skel.num_errors
    assert "NOT SI1000" in fill["rule"]
    assert audit["guard"]["passed"]
    assert audit["seam_rows"], "G6 seam audit rows attach to the stitched deliverable"
    hot = audit["hot_region_disclosure"]
    assert hot["hot_windows"] == (15, 19) and hot["hot_pair_chains"] == (18, 21)
    print(f"stitched toy seams: {audit['seam_rows'][:4]} ...")


def test_freeze_manifest_g2_fields_and_determinism():
    manifest = dc.freeze_manifest(cache_keys=("X/8/0/full", "X/3/1/full"))
    assert len(manifest["dem_compose_sha256"]) == 64
    assert manifest["cache_keys"] == ("X/3/1/full", "X/8/0/full")
    assert manifest["m4_seed"] == 20260610
    assert manifest["clamp"] == {"lo": dc.CLAMP_LO, "hi": dc.CLAMP_HI}
    assert manifest["bulk_layers"] == (80, 999)
    assert manifest["clean_windows"] == tuple(w for w in range(1, 22) if w not in (15, 19))
    assert manifest == dc.freeze_manifest(cache_keys=("X/3/1/full", "X/8/0/full"))


# ---------------------------------------------------------------- hardware-gated (sample_00 ONLY)

requires_hw = pytest.mark.skipif(
    resolve_rep29_root() is None, reason="R2-lite d29 dataset absent (set QEC_TWIN_HW_DATA)"
)
heavy = pytest.mark.skipif(
    os.environ.get("QEC_TWIN_M4_HEAVY") != "1",
    reason="streaming sample_00 pij pass is opt-in (QEC_TWIN_M4_HEAVY=1)",
)

I3_NUM_ERRORS = 86_115  # measured I-3 fact (a), recorded in the registration
# measured SI1000 exact-DEM decomposition structure (orchestrator measurement
# 2026-06-10, outputs/m4_b1_dem_structure.py, both bases identical):
M_NUM_DECOMPOSED = 2_002  # instructions carrying a ^ separator (exactly 2 components each)
M_COMPONENT_CENSUS = {1: 6_008, 2: 82_109}  # arity census over all 88,117 components
M_NUM_L0 = 2_003  # instructions carrying L0
EXPECTED_CLASSES = {"w1", "time(dt=1)", "space(di=1)", "diag(di=1,dt=1,orient=+1)",
                    "diag(di=1,dt=1,orient=-1)"}  # one orientation expected populated


def _hw():
    """sample_00 X-basis artifacts ONLY (held-out protection: samples 01-99 untouched)."""
    from qec_twin.hardware import m1_report
    from qec_twin.hardware.dataset import RepCodeD29
    from qec_twin.hardware.stim_artifacts import load_circuit

    ds = RepCodeD29.from_env()
    grid = m1_report.build_grid(ds, "X", sample=0)
    circuit = load_circuit(ds.paths("X", 0).circuit_noisy_si1000)
    dem = circuit.detector_error_model(decompose_errors=True, flatten_loops=True)
    return ds, grid, dem


@requires_hw
def test_hw_si1000_skeleton_facts():
    _, grid, dem = _hw()
    skel = dc.load_skeleton(dem)  # raises on any hyperedge COMPONENT (the true I-3 fact)
    assert skel.num_errors == I3_NUM_ERRORS, "I-3 measured fact (a): 86,115 errors"
    # measured decomposition structure (2026-06-10): 2,002 decomposed
    # instructions, exactly 2 components each, every component <= 2 detectors
    assert skel.num_decomposed == M_NUM_DECOMPOSED
    assert max(len(c) for c in skel.comps) == 2
    assert skel.component_census() == M_COMPONENT_CENSUS
    census = dc.support_census({"si1000": (skel, skel.p)}, grid=grid)["si1000"]
    print(f"SI1000 skeleton census: { {k: v['count'] for k, v in census.items()} }")
    base = {k for k in census if not k.startswith("decomposed[")}
    assert base <= EXPECTED_CLASSES, f"unexpected class in the skeleton: {base}"
    decomp = {k: census[k]["count"] for k in census if k.startswith("decomposed[")}
    assert sum(decomp.values()) == M_NUM_DECOMPOSED
    for label in decomp:
        inner = set(label[len("decomposed["):-1].split("+"))
        assert inner <= EXPECTED_CLASSES, f"unexpected component class in {label}"
    # the measured class breakdown of the 2,002 decompositions -- the build-
    # report deliverable for the conservative not-twin-owned reading (any
    # would-be-owned class here is the flagged registration ambiguity)
    print(f"decomposed class breakdown: {decomp}")
    n_l0 = sum(1 for o in skel.obs if o)
    print(f"L0-carrying errors: {n_l0}; arity census: {skel.arity_census()}; "
          f"component census: {skel.component_census()}; "
          f"p in [{skel.p.min():.3e}, {skel.p.max():.3e}]")
    assert n_l0 == M_NUM_L0


@requires_hw
def test_hw_full_restriction_identity_and_roundtrip():
    _, grid, dem = _hw()
    skel = dc.load_skeleton(dem)
    sub = dc.subchain_skeleton(skel, grid, 0, 28)
    assert sub.dets == skel.dets and sub.obs == skel.obs and np.array_equal(sub.p, skel.p)
    assert np.array_equal(sub.detector_ids, np.arange(skel.num_detectors_full))
    # B-17 (FIX ROUND 2): device coordinate annotations captured + identity at
    # full restriction + byte-faithful round-trip (the extended P1c pin)
    assert skel.coords is not None
    arity = {}
    for v in skel.coords:
        arity[len(v)] = arity.get(len(v), 0) + 1
    assert arity == {3: 28, 6: 28_000, 9: 28}, (
        "measured device-coord arity census (x, y, t)-triplets: init 1, bulk 2, final 3"
    )
    assert sub.coords == skel.coords, "full restriction is the identity on coords (P1c)"
    report = dc.roundtrip_report(dem)
    print(f"P1c hardware round-trip: {report}")
    assert report["errors_equal"] and report["p_bitexact_unclamped"]
    assert report["coords_equal"], "P1c extended: detector coordinates byte-faithful"
    # measured non-canonicality (why with_grid_coordinates exists): device x
    # takes 10 distinct values over 28 chains -- x alone cannot key the chain
    x_distinct = {v[0] for v in skel.coords}
    print(f"device coordinate[0] distinct values: {sorted(x_distinct)} "
          f"(num_chains {grid.num_chains})")
    assert len(x_distinct) == 10 and grid.num_chains == 28
    print(f"P1f skeleton-DEM sha256: {dc.dem_sha256(dem)[:16]}...")


@requires_hw
def test_hw_window_projection_structure():
    _, grid, dem = _hw()
    skel = dc.load_skeleton(dem)
    win = dc.window_skeleton(skel, grid, 16)  # data 17..21, interior chains 17..20
    assert len(win.detector_ids) == 4 * 1002
    sites = dc.error_sites(win, grid)
    csites = dc.component_sites(win, grid)
    flagged = [i for i in range(win.num_errors) if win.obs[i]]
    assert flagged, "the sub-observable cut produces L0 carriers"
    # component-wise L0 rule: every L0-carrying COMPONENT is the weight-1
    # left-cut survivor at chain 17 (a surviving decomposed instruction may
    # carry the flag on one component while another component lives inside)
    for i in flagged:
        for (comp_dets, comp_obs), cs in zip(win.comps[i], csites[i]):
            if comp_obs:
                assert cs.arity == 1 and cs.col == 17, (
                    "L0 sits exactly on the left-cut crossers (data qubit 17 mechanisms)"
                )
    n_flagged_single = sum(1 for i in flagged if len(win.comps[i]) == 1)
    print(f"window 16 projection: {win.num_errors} errors, {len(flagged)} L0 carriers "
          f"({n_flagged_single} single-component), "
          f"decomposed surviving {win.num_decomposed}, "
          f"w1 census {sum(1 for s in sites if s.arity == 1 and s.num_components == 1)}")
    # B-17 acceptance on the real window: device coords pass through; the
    # canonical (chain, layer) emission satisfies B2's A3c geometry contract
    # with GLOBAL qubit keys (g-1, g) for window-16 data qubits g = 17..21
    assert win.coords is not None and len(win.coords) == 4 * 1002
    canon = dc.with_grid_coordinates(win, grid)
    dem_w, _ = dc.with_probabilities(canon, win.p)
    from qec_twin.hardware.m4_decode import space_edge_geometry

    geo = space_edge_geometry(dem_w)
    qkeys = {q for _, q, _ in geo.classify.values()}
    assert qkeys <= {(16, 17), (17, 18), (18, 19), (19, 20), (20, 21)}, (
        "A3c qubit keys are the window's data qubits via (g-1, g)"
    )
    assert {(16, 17), (20, 21)} <= qkeys, "boundary data qubits carry space keys"
    assert geo.num_space_edges > 3 * 1000, "bulk space edges classified across layers"
    print(f"window 16 A3c geometry: {geo.num_space_edges} space-edge slots, "
          f"qubit keys {sorted(qkeys)}, "
          f"unclassified singles {geo.num_unclassified_singles}")


@requires_hw
def test_hw_twin_arm_from_frozen_cache_smoke():
    cache_path = os.environ.get("QEC_TWIN_M3_FIT_CACHE", "outputs/m3_fit_cache.pt")
    if not os.path.exists(cache_path):
        pytest.skip(f"frozen M3 fit cache absent: {cache_path}")
    _, grid, dem = _hw()
    skel = dc.load_skeleton(dem)
    cache = dc.load_frozen_cache(cache_path)  # READ-ONLY; zero new fits (S11)
    windows = tuple(w for w in range(1, 22) if w not in (15, 19))
    # build-smoke stand-in fill: the registered pij fill is the production path
    probs, table = dc.arm_twin_static(
        cache, windows, grid, skel.p, skel=skel, basis="X"
    )
    assert sorted(table["space"]) == list(range(3, 26)), "owned data positions 3..25"
    assert sorted(table["time"]) == list(range(2, 26)), "owned measure chains 2..25"
    assert table["unowned_identical_to_pij"] and table["guard"]["passed"]
    hot = table["hot_region_disclosure"]
    print(f"hot-region resolution: space-only-hot {hot['space_cells_unowned_only_because_hot_excluded']}, "
          f"time-only-hot {hot['time_cells_unowned_only_because_hot_excluded']} "
          f"(empty == the {{15,19}} region keeps clean owners; disclosed, see build report)")
    print(f"assigned {table['num_assigned']} / unowned {table['num_unowned']}; "
          f"census {table['unowned_census']}")
    print(f"cache keys used (first 4): {table['cache_keys'][:4]}")
    assert len(table["cache_keys"]) == len(windows)
    r_values = [c["r_hat"] for c in table["space"].values()]
    q_values = [c["q_eff"] for c in table["time"].values()]
    print(f"r_hat in [{min(r_values):.3e}, {max(r_values):.3e}]; "
          f"q_eff in [{min(q_values):.3e}, {max(q_values):.3e}]")


@requires_hw
def test_hw_two_pass_table_from_frozen_cache():
    cache_path = os.environ.get("QEC_TWIN_M3_FIT_CACHE", "outputs/m3_fit_cache.pt")
    if not os.path.exists(cache_path):
        pytest.skip(f"frozen M3 fit cache absent: {cache_path}")
    cache = dc.load_frozen_cache(cache_path)
    windows = tuple(w for w in range(1, 22) if w not in (15, 19))
    table = dc.two_pass_table(cache, windows, basis="X")
    assert sorted(table) == list(range(3, 26))
    R_values = [R for _, R in table.values()]
    print(f"A3c table: R_hat in [{min(R_values):.3f}, {max(R_values):.3f}] "
          f"(M3 measured located range [1.0, 17.7])")
    assert all(R >= 1.0 - 1e-12 for R in R_values), "R >= 1 by AM-GM (a)"


@requires_hw
@heavy
def test_hw_pij_arm_acceptance_smoke():
    """Opt-in: streams sample_00 once (minutes). Build-smoke ONLY -- the P1h
    pin verdict belongs to the registered freeze sequence, not this test."""

    import warnings

    ds, grid, dem = _hw()
    skel = dc.load_skeleton(dem)
    counts = accumulate_pair_counts(ds.paths("X", 0).detection_events, grid)
    probs, report = dc.arm_pij(counts, grid, skel, return_report=True)
    print(f"A2 hardware report: {report}")
    assert np.isfinite(probs).all()
    assert probs.min() >= dc.CLAMP_LO and probs.max() <= dc.CLAMP_HI
    marginals, result = dc.acceptance_check(
        skel, probs, dc.detection_fraction_global(counts, grid)
    )
    print(f"P1h smoke: max |composed - measured| {result.max_abs_dev:.4e}, "
          f"mean {result.mean_abs_dev:.4e}, out {result.num_out}/{result.num_sites} "
          f"at tol {result.tol}")
    if not result.passed:
        warnings.warn(
            f"P1h smoke outside +/-0.5% on {result.num_out} sites (registered pin is "
            "adjudicated at composition freeze, reported here)", stacklevel=1
        )

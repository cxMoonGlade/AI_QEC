"""Tests for ``error_coupling_simulator.certify`` — the certification seam.

Step 1: the interface (the value types + the ``Anchor`` / ``Control`` / ``ControlledNoiseProcess`` ports)
imports + constructs; the ``CertReport`` verdict / summary / assert_pass logic; the ports are
duck-typed ``runtime_checkable`` Protocols through the package-owned certification port.

Step 2: the core (route → controls-first → score → ledger) against an IN-MEMORY anchor with a known
law (the port IS the test surface — pure, no GPU). The genuine-check invariants are proven here:
a broken carrier FAILs; an inert control forces FAIL; an infeasible cell is UNANCHORED, never PASS;
exact anchors are preferred. The in-memory anchor + controlled process fixture live HERE (in
``tests/``) — they are structurally never production anchors.
"""

from dataclasses import replace

import numpy as np

from error_coupling_simulator.certify import (
    Anchor,
    AnchorValue,
    Capability,
    CertReport,
    Control,
    ControlledNoiseProcess,
    Exactness,
    Feasibility,
    LedgerRow,
    Regime,
    Statistic,
    Verdict,
)
from error_coupling_simulator.certify.core import certify_cells, compare, route

_DIST = (Statistic.FULL_JOINT, Statistic.SYNDROME_DIST)


# ======================================================================= #
# Step 1 — the interface                                                   #
# ======================================================================= #
def test_types_import_and_construct():
    reg = Regime(R=2, register="subregister", n_active=3, n_stab=8, sites=(0, 1, 2))
    feas = Feasibility(ok=False, reason="R>=2 full-9q OOM", mem_bytes_estimate=100 * 1024**3)
    cap = Capability(statistic=Statistic.FULL_JOINT, exactness=Exactness.EXACT, feasible=False,
                     reason=feas.reason, epistemic_class="a",
                     mem_bytes_estimate=feas.mem_bytes_estimate)
    row = LedgerRow(anchor="dm", statistic=Statistic.SYNDROME_DIST, value=4e-4,
                    band=(0.0, 2.1e-3), epistemic_class="a", verdict=Verdict.PASS)
    assert reg.R == 2 and reg.sites == (0, 1, 2)
    assert not cap.feasible and not feas.ok
    assert row.verdict is Verdict.PASS and row.epistemic_class == "a"


def test_report_summary_and_assert_pass():
    rows = (LedgerRow("dm", Statistic.SYNDROME_DIST, 4e-4, (0.0, 2e-3), "a", Verdict.PASS),)
    ok = CertReport(verdict=Verdict.PASS, rows=rows, controls=(), routing={}, truth={"theta": 0.15})
    assert "PASS" in ok.summary()
    ok.assert_pass()  # must NOT raise
    assert ok.row("dm", Statistic.SYNDROME_DIST) is rows[0]
    assert ok.row("dm", Statistic.FULL_JOINT) is None
    assert ok.truth == {"theta": 0.15}  # returned only to the certification caller

    bad = CertReport(verdict=Verdict.FAIL, rows=rows, controls=(), routing={}, truth={})
    raised = False
    try:
        bad.assert_pass()
    except AssertionError:
        raised = True
    assert raised, "assert_pass must raise on a FAIL verdict"


def test_ports_are_duck_typed_runtime_checkable_protocols():
    class _DuckAnchor:
        name = "duck"
        independence = "from-scratch closed form (test)"

        def answers(self):
            return frozenset({Statistic.SCALAR_FUNC})

        def capability(self, statistic, regime):
            return Capability(statistic, Exactness.EXACT, feasible=True)

        def answer(self, process, statistic, regime, *, N=None, generator=None):
            return None

    class _DuckControl:
        name = "shuffle"

        def guards(self, statistic):
            return True

        def expect(self):
            return "must_fail"

        def run(self, ctx, statistic, regime, *, N=None):
            return None

    class _DuckProcess:
        sched = object()
        truth = {"theta": 0.15}

        def emit(self, regime, *, m, N, seed):
            return None

        def channels(self):
            return None

    assert isinstance(_DuckAnchor(), Anchor)
    assert isinstance(_DuckControl(), Control)
    assert isinstance(_DuckProcess(), ControlledNoiseProcess)
    assert not isinstance(object(), Anchor)  # a non-conforming object is rejected (the port has teeth)


# ======================================================================= #
# Step 2 — test fixtures (TEST-ONLY: in tests/, never production anchors)   #
# ======================================================================= #
def _make_records(joint: dict, N: int) -> dict:
    """Deterministic (det, obs) realizing ``joint`` ({FULL_JOINT key -> prob}; key = det + (flip<<1)
    for a 1-stabilizer R=1 surface), so ``emitted_statistic`` recovers the dist exactly (no flake)."""
    keys = list(joint)
    counts = [int(round(joint[k] * N)) for k in keys]
    counts[0] += N - sum(counts)
    det = np.concatenate([np.full(c, k & 1, np.uint8) for k, c in zip(keys, counts)]).reshape(N, 1)
    obs = np.concatenate([np.full(c, (k >> 1) & 1, np.uint8) for k, c in zip(keys, counts)])
    return {"det": det, "obs": obs}


class ControlledProcessFixture:
    """A controlled process emitting a KNOWN law (test fixture)."""

    sched = object()
    truth = {"theta": 0.15, "gamma": 0.04}

    def __init__(self, joint: dict):
        self._joint = joint

    def emit(self, regime, *, m, N, seed):
        return _make_records(self._joint, N)

    def channels(self):
        return None


class InMemoryAnchor:
    """TEST FIXTURE — a hand-written known law that shares no code with any engine (the port IS the
    test surface). Lives in ``tests/`` so it is structurally never a production anchor."""

    name = "in_memory"
    independence = "hand-written known law (TEST fixture; shares no code with any engine)"

    def __init__(self, joint: dict, *, feasible: bool = True, exactness=Exactness.EXACT,
                 corruptible: bool = True):
        self._joint = joint
        self._feasible = feasible
        self._exactness = exactness
        self._corruptible = corruptible  # whether it can host the corrupt-stabilizer control

    def answers(self):
        return frozenset({Statistic.FULL_JOINT, Statistic.SYNDROME_DIST})

    def capability(self, statistic, regime):
        return Capability(statistic, self._exactness, feasible=self._feasible,
                          epistemic_class="a" if self._exactness is Exactness.EXACT else "b")

    def answer(self, process, statistic, regime, *, N=None, generator=None, corrupt=None):
        if statistic is Statistic.SYNDROME_DIST:
            val: dict = {}
            for k, p in self._joint.items():
                val[k & 1] = val.get(k & 1, 0.0) + p
        else:
            val = dict(self._joint)
        if corrupt and "stab" in corrupt and self._corruptible:
            # a corrupted ground truth: uniform over the realized keys (differs from the true law,
            # so the carrier — which matches the true law — must FAIL → the control fires).
            u = 1.0 / len(val)
            val = {k: u for k in val}
        cls = "a" if self._exactness is Exactness.EXACT else "b"
        band = 0.0 if self._exactness is Exactness.EXACT else 0.01
        return AnchorValue(statistic, regime, val, self._exactness, band, cls,
                           provenance={"anchor": self.name})


class _CorruptControl:
    """Corrupts the anchor and confirms the comparison now FAILs (the check has teeth)."""

    def guards(self, statistic):
        return statistic in _DIST

    def expect(self):
        return "must_fail"

    def run(self, ctx, statistic, regime, *, N=None):
        corrupt = self._corrupt(ctx.anchor_value)
        _, _, verdict, _ = compare(statistic, ctx.emitted, corrupt, N=ctx.N)
        fired = verdict is Verdict.FAIL  # the comparison CAUGHT the corruption
        return LedgerRow(ctx.anchor.name, statistic, 1.0 if fired else 0.0, None, "c",
                         Verdict.CONTROL, {"fired": fired, "name": self.name})


class ShuffleControl(_CorruptControl):
    name = "shuffle_label"

    def _corrupt(self, av: AnchorValue) -> AnchorValue:
        keys = sorted(av.value)
        vals = [av.value[k] for k in keys]
        rolled = {k: vals[(i + 1) % len(vals)] for i, k in enumerate(keys)}
        return replace(av, value=rolled)


class InertControl(_CorruptControl):
    """A deliberately broken control: its perturbation is the IDENTITY, so it can NEVER fire. The
    core must turn this into a FAIL (a check that can't fail is vacuous)."""

    name = "inert"

    def _corrupt(self, av: AnchorValue) -> AnchorValue:
        return av  # identity — the comparison can't fail -> the control never fires -> FAIL


_JOINT = {0: 0.4, 1: 0.1, 2: 0.05, 3: 0.45}
_REG = Regime(R=1, register="subregister", n_active=1, n_stab=1)


# ======================================================================= #
# Step 2 — the genuine-check invariants                                    #
# ======================================================================= #
def test_core_routes_scores_and_passes():
    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [ShuffleControl()], N=20000)
    assert rep.verdict is Verdict.PASS, rep.summary()
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS
    assert all(c.detail["fired"] for c in rep.controls)  # the control has teeth (it fired)


def test_broken_carrier_fails():
    broken = ControlledProcessFixture({0: 0.1, 1: 0.4, 2: 0.45, 3: 0.05})  # a DIFFERENT law
    rep = certify_cells(broken, [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [ShuffleControl()], N=20000)
    assert rep.verdict is Verdict.FAIL, rep.summary()  # the comparison has teeth


def test_inert_control_forces_fail():
    # the carrier MATCHES the anchor -> the positive row PASSES -> but an inert control forces FAIL.
    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [InertControl()], N=20000)
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS
    assert not any(c.detail["fired"] for c in rep.controls)
    assert rep.verdict is Verdict.FAIL, rep.summary()  # a vacuous check cannot pass


def test_infeasible_anchor_is_unanchored_not_pass():
    reg = Regime(R=2, register="full", n_active=9, n_stab=1)  # the OOM regime
    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, reg)],
                        [InMemoryAnchor(_JOINT, feasible=False)], [], N=20000)
    assert rep.row("in_memory", Statistic.FULL_JOINT) is None  # no anchor row
    assert rep.rows[0].anchor is None and rep.rows[0].verdict is Verdict.UNANCHORED
    assert rep.verdict is not Verdict.PASS  # an honest gap, never a silent pass
    assert "UNANCHORED" in next(iter(rep.routing.values()))


def test_exact_preferred_routing():
    chosen = route([InMemoryAnchor(_JOINT, exactness=Exactness.STATISTICAL),
                    InMemoryAnchor(_JOINT, exactness=Exactness.EXACT)],
                   Statistic.FULL_JOINT, _REG)
    assert chosen.capability(Statistic.FULL_JOINT, _REG).exactness is Exactness.EXACT


# ======================================================================= #
# Step 3a — the DM-oracle anchor's feasibility descriptor (PURE; no GPU)    #
# the OOM-as-data routing: a 32 GB card is mocked via card_bytes, so this    #
# exercises the do-not-OOM logic with zero allocation.                       #
# ======================================================================= #
def test_dm_anchor_capability_is_oom_safe():
    from error_coupling_simulator.certify.anchors import DMOracleAnchor

    dm = DMOracleAnchor(card_bytes=32 * 1024**3)  # mock a 32 GB card -> capability is pure, no GPU
    full9_R1 = Regime(R=1, register="full", n_active=9, n_stab=8)
    full9_R2 = Regime(R=2, register="full", n_active=9, n_stab=8)
    sub_R1 = Regime(R=1, register="subregister", n_active=3, n_stab=2)

    # DETECTOR_MARG @ R=1 full-9q on a 32 GB card @ safety 0.5: INFEASIBLE — the accounting was
    # CORRECTED 2026-07-06 (residual-②): the projection loop's live set is rho1 + working clone +
    # apply output (+ tiles), declared 4 copies ~ 24.8 GB > the 17.2 GB half-card budget. (The old
    # 2-copy "~12.4 GB feasible" claim was falsified by measurement: the pre-fix path peaked at
    # k=5.44 copies and would have OOMed the cell it declared feasible.)
    cap = dm.capability(Statistic.DETECTOR_MARG, full9_R1)
    assert not cap.feasible and cap.exactness is Exactness.EXACT and cap.epistemic_class == "a"
    assert 2.2e10 < cap.mem_bytes_estimate < 2.6e10  # 4 copies ~ 24.8 GB live
    assert "budget" in cap.reason
    # ... and FEASIBLE on a card whose half-budget covers the corrected live set (64 GB -> 32 GB).
    dm_big = DMOracleAnchor(card_bytes=64 * 1024**3)
    assert dm_big.capability(Statistic.DETECTOR_MARG, full9_R1).feasible
    # DETECTOR_MARG @ R>=2: NOT via projection (needs the moments path) -> infeasible, with a reason.
    cap2 = dm.capability(Statistic.DETECTOR_MARG, full9_R2)
    assert not cap2.feasible and "moments" in cap2.reason

    # FULL_JOINT @ R=1 full-9q: depth-8 enumeration ~50 GB > 16 GB budget -> INFEASIBLE (route to scale).
    cj = dm.capability(Statistic.FULL_JOINT, full9_R1)
    assert not cj.feasible and "GB" in cj.reason and cj.mem_bytes_estimate > 4e10
    # FULL_JOINT @ R=2 full-9q: ~100 GB -> INFEASIBLE.
    assert not dm.capability(Statistic.FULL_JOINT, full9_R2).feasible
    # FULL_JOINT on a small sub-register: feasible (tiny DM).
    assert dm.capability(Statistic.FULL_JOINT, sub_R1).feasible

    # documented independence (anti-circular) + answers the right statistics. WS1 wired the R>=2
    # MOMENTS (RR_CORR / SPATIAL_CORR) into the DM anchor, so they ARE now in answers().
    assert "DIFFERENT object" in dm.independence
    assert Statistic.DETECTOR_MARG in dm.answers()
    assert Statistic.RR_CORR in dm.answers() and Statistic.SPATIAL_CORR in dm.answers()


# ======================================================================= #
# Step 3b — WS1: the DM MOMENTS anchor (RR_CORR / SPATIAL_CORR) capability   #
# + emitted shapes + the shared reduction (PURE; no GPU — card mocked).      #
# ======================================================================= #
def test_dm_anchor_moments_capability_is_oom_safe():
    from error_coupling_simulator.certify.anchors import DMOracleAnchor

    dm = DMOracleAnchor(card_bytes=32 * 1024**3)  # mock a 32 GB card -> capability is pure, no GPU
    full9_R2 = Regime(R=2, register="full", n_active=9, n_stab=8)
    full9_R1 = Regime(R=1, register="full", n_active=9, n_stab=8)
    sub_R2 = Regime(R=2, register="subregister", n_active=4, n_stab=2, sites=(0, 2, 5, 7))

    # RR_CORR / SPATIAL_CORR @ full-9q R=2: INFEASIBLE — the moments path's peak live memory is the
    # depth-(n_stab*R) clone stack (~100 GB at full-9q R=2; pruning shrinks breadth, NOT the depth), so
    # it gates on depth*copy exactly like FULL_JOINT and routes the scale to the carrier-MCWF. The DM
    # moments GT therefore lives on a SMALL VALID sub-code (sub_R2), where depth*copy fits the budget.
    for stat in (Statistic.RR_CORR, Statistic.SPATIAL_CORR):
        cap = dm.capability(stat, full9_R2)
        assert not cap.feasible and "carrier-MCWF" in cap.reason  # route the scale to the carrier
        assert cap.mem_bytes_estimate is not None and cap.mem_bytes_estimate > 4e10  # declared depth bound
        # FEASIBLE on a small valid sub-code (the DM-for-anchor register).
        cap_sub = dm.capability(stat, sub_R2)
        assert cap_sub.feasible and cap_sub.exactness is Exactness.EXACT and cap_sub.epistemic_class == "a"
        # the moments need R>=2: at R=1 there is no round-to-round / realized second moment -> infeasible.
        cap1 = dm.capability(stat, full9_R1)
        assert not cap1.feasible and "R>=2" in cap1.reason

    # the feasibility branch HAS TEETH (not vacuously True): no GPU budget (card_bytes=0) -> infeasible,
    # and a card too small for the full-9q depth stack -> infeasible with a budget reason.
    dm0 = DMOracleAnchor(card_bytes=0)
    assert not dm0.capability(Statistic.RR_CORR, sub_R2).feasible
    tiny = DMOracleAnchor(card_bytes=1 * 1024**3)  # 1 GB card: the full-9q depth stack won't fit
    cap_tiny = tiny.capability(Statistic.SPATIAL_CORR, full9_R2)
    assert not cap_tiny.feasible and "budget" in cap_tiny.reason


def test_emitted_spatial_corr_shape_and_foil_zero():
    from error_coupling_simulator.certify.core import emitted_statistic

    rng = np.random.default_rng(1)
    n, R, n_stab = 4000, 3, 4
    # an INDEPENDENT-bit-flip foil: every (round, stab) detector iid -> RR_CORR and SPATIAL_CORR are
    # IDENTICALLY ~0 (they factorize across (round, stab)) -> the statistic's prevent-toy property.
    det = (rng.random((n, R, n_stab)) < 0.3).astype(np.uint8).reshape(n, R * n_stab)
    reg = Regime(R=R, n_stab=n_stab)
    sp = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.SPATIAL_CORR, reg)
    assert sp.shape == (R,)                      # per-round, length R (mirrors RR_CORR's R-1)
    assert float(np.max(np.abs(sp))) < 0.05      # the foil is correlation-free (teeth preserved)
    rr = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.RR_CORR, reg)
    assert rr.shape == (R - 1,)
    assert float(np.max(np.abs(rr))) < 0.05


def test_emitted_spatial_corr_detects_correlation_and_matches_from_scratch():
    from error_coupling_simulator.certify.core import emitted_statistic

    rng = np.random.default_rng(2)
    n, R, n_stab = 60000, 2, 2
    # build a CORRELATED same-round pair (stab 1 = stab 0 XOR a little noise) -> SPATIAL_CORR != 0
    # (the reduction must DISCRIMINATE — not collapse to a constant).
    s0 = (rng.random((n, R)) < 0.3).astype(np.uint8)
    noise = (rng.random((n, R)) < 0.1).astype(np.uint8)
    s1 = (s0 ^ noise).astype(np.uint8)
    det = np.stack([s0[:, 0], s1[:, 0], s0[:, 1], s1[:, 1]], axis=1)  # (n, R*n_stab) round-major
    reg = Regime(R=R, n_stab=n_stab)
    sp = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.SPATIAL_CORR, reg)
    assert sp.shape == (R,)
    assert float(sp[0]) > 0.1  # a genuine same-round correlation is detected (not collapsed)
    # from-scratch: round 0 off-diagonal mean of |corr| over the 2x2 = |corr(det0, det1)| (one pair).
    from_scratch = abs(np.corrcoef(det[:, 0].astype(float), det[:, 1].astype(float))[0, 1])
    assert abs(float(sp[0]) - from_scratch) < 1e-9


def test_shared_moment_reductions_match_emitted_and_dm_shapes():
    # the apples-to-apples GUARANTEE: the DM anchor reduces its (R-1,n_stab) rr_corr / (R,n_stab,n_stab)
    # spatial_corr through the SAME core helpers the emitted side uses, so the shapes/semantics cannot
    # drift. Here we exercise the helpers directly on a synthetic SIGNED matrix (the DM record_oracle
    # output shape) and confirm the reduced shape + the off-diagonal/abs semantics.
    from error_coupling_simulator.certify.core import reduce_rr_corr, reduce_spatial_corr

    R, n_stab = 3, 4
    rng = np.random.default_rng(3)
    rr2d = rng.uniform(-1, 1, size=(R - 1, n_stab))
    rr = reduce_rr_corr(rr2d)
    assert rr.shape == (R - 1,)
    assert np.allclose(rr, np.abs(rr2d).mean(axis=1))  # mean over j of |.|

    sp3d = rng.uniform(-1, 1, size=(R, n_stab, n_stab))
    for r in range(R):  # diagonal = the trivial self-correlation 1 (must be EXCLUDED by the reduction)
        np.fill_diagonal(sp3d[r], 1.0)
    sp = reduce_spatial_corr(sp3d)
    assert sp.shape == (R,)
    off = ~np.eye(n_stab, dtype=bool)
    assert np.allclose(sp, np.abs(sp3d)[:, off].mean(axis=1))  # off-diagonal mean of |.| (diag excluded)
    # the diagonal-1 must NOT leak into the value (else the reduction is a constant collapse, not teeth)
    assert float(np.max(sp)) < 1.0

    # R==1 edge: no round-to-round -> rr is [0.0]; spatial with n_stab<2 -> per-round 0 (no off-diag pair).
    assert np.array_equal(reduce_rr_corr(np.zeros((0, n_stab))), np.array([0.0]))
    assert np.array_equal(reduce_spatial_corr(np.zeros((2, 1, 1))), np.zeros(2))


def test_corrupt_stab_control_guards_the_moments():
    from error_coupling_simulator.certify.anchors import CorruptStabControl

    # WS1: the corrupt-stabilizer control must now GUARD the moments anchors (so an inert control on a
    # moments cell forces FAIL, per the core roll-up). Before WS1 it guarded only the geometry stats.
    ctrl = CorruptStabControl(stab=1)
    assert ctrl.guards(Statistic.RR_CORR) and ctrl.guards(Statistic.SPATIAL_CORR)
    assert ctrl.guards(Statistic.DETECTOR_MARG)  # the existing geometry guards still hold


# ======================================================================= #
# Step 4a — the corrupt-stabilizer control (teeth) + the stim anchor        #
# ======================================================================= #
def test_corrupt_stab_control_fires_on_corruptible_anchor():
    from error_coupling_simulator.certify.anchors import CorruptStabControl

    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT, corruptible=True)], [CorruptStabControl(stab=0)], N=20000)
    assert rep.verdict is Verdict.PASS, rep.summary()
    assert all(c.detail["fired"] for c in rep.controls)  # the corruption was caught (geometric teeth)


def test_corrupt_stab_control_inert_forces_fail():
    from error_coupling_simulator.certify.anchors import CorruptStabControl

    # an anchor that CANNOT host the corruption returns the same answer -> the control can't fire -> FAIL.
    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT, corruptible=False)], [CorruptStabControl(stab=0)], N=20000)
    assert not any(c.detail["fired"] for c in rep.controls)
    assert rep.verdict is Verdict.FAIL, rep.summary()  # a control that can't fail is vacuous -> FAIL


def test_stim_anchor_capability_and_emit_kind():
    from error_coupling_simulator.certify.anchors import StimCliffordAnchor

    st = StimCliffordAnchor(p_x=0.03)
    assert st.emit_kind() == "clifford_slice"  # certifies the process's Clifford SLICE (wiring), not the full mechanism
    for R in (1, 2, 3):
        cap = st.capability(Statistic.SYNDROME_DIST, Regime(R=R, n_stab=8))
        assert cap.feasible and cap.exactness is Exactness.STATISTICAL and cap.epistemic_class == "b"
    assert "SEPARATE Clifford simulator" in st.independence
    assert Statistic.SYNDROME_DIST in st.answers()
    # the feasibility branch HAS teeth (not vacuously True): a statistic stim does NOT answer
    # (round-to-round leakage correlation — Clifford-blind) is NOT feasible.
    assert Statistic.RR_CORR not in st.answers()
    assert not st.capability(Statistic.RR_CORR, Regime(R=2, n_stab=8)).feasible


def test_exact_anchor_with_nonzero_band_is_rejected():
    # the EXACT => band==0 contract (_assert_anchor_value) must have TEETH — an anchor declaring EXACT
    # yet returning a nonzero band is a violation and must RAISE, never silently pass. The review found
    # this invariant was never exercised by the suite (dormant); this exercises both legs.
    import pytest

    from error_coupling_simulator.certify.core import _assert_anchor_value

    class _NamedAnchor:
        name = "bad_exact"

    legal = AnchorValue(Statistic.DETECTOR_MARG, Regime(R=1, n_stab=8), np.array([0.1]),
                        Exactness.EXACT, 0.0, "a", {})
    _assert_anchor_value(legal, _NamedAnchor())  # EXACT with band==0 is fine (no raise)
    illegal = AnchorValue(Statistic.DETECTOR_MARG, Regime(R=1, n_stab=8), np.array([0.1]),
                          Exactness.EXACT, 0.5, "a", {})  # EXACT but band=0.5 — illegal
    with pytest.raises(ValueError):
        _assert_anchor_value(illegal, _NamedAnchor())


# ======================================================================= #
# Step 5 — the closed-form sidecar (RR_CORR machinery + the T-B prediction) #
# ======================================================================= #
def test_rr_corr_machinery_matches_from_scratch():
    from error_coupling_simulator.certify.core import emitted_statistic

    rng = np.random.default_rng(0)
    n = 50000
    d0 = (rng.random(n) < 0.3).astype(np.uint8)
    flip = (rng.random(n) < 0.2).astype(np.uint8)
    d1 = (d0 ^ flip).astype(np.uint8)                # round 1 correlated with round 0
    det = np.stack([d0, d1], axis=1)                 # (n, 2): R=2, n_stab=1
    emitted = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)},
                                Statistic.RR_CORR, Regime(R=2, n_stab=1))
    from_scratch = abs(np.corrcoef(d0.astype(float), d1.astype(float))[0, 1])
    assert abs(float(emitted[0]) - from_scratch) < 1e-9  # the rr_corr machinery is correct


def test_closed_form_anchor_predicts_transient_two_state_markov_rr_corr():
    # The record chain is PREPARED in |0>, so the measured two-state chain is TRANSIENT — the earlier
    # anchor predicted the STATIONARY limit (markov_flip_cov) and disagreed with the engine (5b). This
    # pins the corrected anchor with THREE non-circular checks + a positive control that the bug is now
    # caught. None of them assumes stationarity (the shared blind spot that made 5a circular).
    import itertools

    from error_coupling_simulator.certify.anchors import ClosedFormAnchor

    a, b = 0.08, 0.20
    R = 6
    cf = ClosedFormAnchor(p01=a, p10=b, exact_single_qubit=True)
    assert cf.emit_kind() == "nonunital_slice"
    assert cf.answers() == frozenset({Statistic.RR_CORR})
    assert cf.capability(Statistic.RR_CORR, Regime(R=R, n_stab=1)).exactness is Exactness.EXACT
    assert not cf.capability(Statistic.RR_CORR, Regime(R=1, n_stab=1)).feasible  # R=1: no round-to-round

    seq = cf._exact_rr_corr(R)  # the anchor's GROUND TRUTH (exact local triple-joint propagation)
    assert seq.shape == (R - 1,)

    # (i) INDEPENDENT from-scratch GT — a DIFFERENT method (full 2^R path enumeration, not the local
    #     triple-joint), s_{-1}=0. A coding bug in one would not be replicated in the other.
    T = np.array([[1 - a, a], [b, 1 - b]])
    paths = list(itertools.product((0, 1), repeat=R))
    probs = np.array([np.prod([T[(p[k - 1] if k else 0), p[k]] for k in range(R)]) for p in paths])
    assert abs(probs.sum() - 1.0) < 1e-12
    S = np.array(paths)
    s_prev = np.concatenate([np.zeros((len(paths), 1), int), S[:, :-1]], axis=1)  # s_{-1}=0
    D = (S ^ s_prev).astype(float)  # detectors d_r = s_{r-1} XOR s_r (d_0 = s_0)
    scratch = []
    for r in range(R - 1):
        x, y = D[:, r], D[:, r + 1]
        ex, ey, exy = (probs * x).sum(), (probs * y).sum(), (probs * x * y).sum()
        vx, vy = ex * (1 - ex), ey * (1 - ey)
        scratch.append(abs((exy - ex * ey) / np.sqrt(vx * vy)) if vx > 1e-12 and vy > 1e-12 else 0.0)
    assert np.max(np.abs(seq - np.array(scratch))) < 1e-12  # exact GT == independent full-path enumeration

    # (ii) the analytic flip-flip identity (E[d_r d_{r+1}] = p01 p10) matches the enumeration (r>=1).
    assert np.max(np.abs(cf.predict_sequence(R) - seq[1:])) < 1e-12

    # (iii) TRANSIENT, not stationary: the flip-flip correlation DECREASES toward — and stays above —
    #       the stationary value at finite R. POSITIVE CONTROL: the OLD stationary form is WRONG here,
    #       so the stationary-vs-transient bug would now fail loudly.
    flip = seq[1:]
    assert np.all(np.diff(flip) < 0)
    r_stat = 2 * a * b / (a + b)
    corr_stat = abs((a * b - r_stat * r_stat) / (r_stat * (1 - r_stat)))  # the OLD (stationary) value
    assert corr_stat < flip.min() - 0.01  # every transient entry exceeds the stationary limit by >0.01

    # d3 mode (default): an honest (b) prediction with a band — NOT inflated to exact.
    cf_d3 = ClosedFormAnchor(p01=a, p10=b)
    av = cf_d3.answer(None, Statistic.RR_CORR, Regime(R=R, n_stab=8))
    assert av.epistemic_class == "b" and av.exactness is Exactness.STATISTICAL and av.band > 0
    assert av.value.shape == (R - 1,) and "no simulator" in cf_d3.independence


# ======================================================================= #
# Step 6 — the neutral certification facade (orchestration: route + merge + roll) #
# ======================================================================= #
def test_certify_noise_process_facade_merges_and_rolls_up():
    from error_coupling_simulator.certify import certify_noise_process
    from error_coupling_simulator.certify.anchors import CorruptStabControl

    rep = certify_noise_process(ControlledProcessFixture(_JOINT), anchors=[InMemoryAnchor(_JOINT)],
                                cells=[(Statistic.FULL_JOINT, _REG)],
                                controls=[CorruptStabControl(stab=0)], N=20000)
    assert rep.verdict is Verdict.PASS, rep.summary()
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS
    assert all(c.detail["fired"] for c in rep.controls)
    assert rep.provenance["level"] == "standard" and rep.provenance["N"] == 20000

    raised = False  # an unknown level is rejected
    try:
        certify_noise_process(ControlledProcessFixture(_JOINT), level="bogus", anchors=[InMemoryAnchor(_JOINT)],
                              cells=[(Statistic.FULL_JOINT, _REG)])
    except ValueError:
        raised = True
    assert raised


# ======================================================================= #
# Anti-vacuity + feasibility-gate regressions (the R3 commit-gate review)  #
# A scored cell with no FIRED falsifier is FINDING, never a teeth-less     #
# PASS; a class-'a' STATISTICAL value and an n_stab=None feasibility gate  #
# are rejected; a degenerate shuffle is INAPPLICABLE, not a spurious FAIL. #
# ======================================================================= #
def test_empty_controls_does_not_pass():
    # the anti-vacuity invariant made STRUCTURAL: a matching, feasible, EXACT cell with NO control
    # (controls=[]) is NOT a PASS — it has no falsifier that could fail, so it is UNCERTIFIED ->
    # FINDING. (Before the fix, `any([]) == False` let this through as a teeth-less PASS — the bug.)
    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [], N=20000)
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS  # the data matches...
    assert rep.verdict is Verdict.FINDING, rep.summary()  # ...but with no falsifier it is uncertified


def test_nonguarding_control_does_not_pass():
    # a control that does NOT guard the cell's statistic attaches NO control row -> same as controls=[]
    # -> the cell is uncertified (FINDING), never a PASS. (Closes the all-non-guarding variant.)
    class _NonGuarding:
        name = "nonguarding"

        def guards(self, statistic):
            return False

        def expect(self):
            return "must_fail"

        def run(self, ctx, statistic, regime, *, N=None):  # never called (guards is False)
            raise AssertionError("a non-guarding control must not be run")

    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [_NonGuarding()], N=20000)
    assert rep.verdict is Verdict.FINDING, rep.summary()


def test_class_a_statistical_value_is_rejected():
    # the class<->exactness consistency leg of _assert_anchor_value: a class-'a' (exact-grade) value
    # that is actually STATISTICAL would be rolled up as an EXACT PASS (inflation) — it must RAISE.
    import pytest

    from error_coupling_simulator.certify.core import _assert_anchor_value

    class _NamedAnchor:
        name = "mislabeled"

    legal = AnchorValue(Statistic.DETECTOR_MARG, Regime(R=1, n_stab=8), np.array([0.1]),
                        Exactness.STATISTICAL, 0.01, "b", {})  # honestly class 'b' (no raise)
    _assert_anchor_value(legal, _NamedAnchor())
    illegal = AnchorValue(Statistic.DETECTOR_MARG, Regime(R=1, n_stab=8), np.array([0.1]),
                          Exactness.STATISTICAL, 0.01, "a", {})  # STATISTICAL mislabeled 'a' -> raise
    with pytest.raises(ValueError):
        _assert_anchor_value(illegal, _NamedAnchor())


def test_dm_anchor_nstab_none_is_infeasible():
    # the feasibility gate must REFUSE a regime with n_stab=None: it cannot bound the depth-(n_stab*R)
    # clone stack, and a None under-counts depth to R and would falsely pass the gate -> an OOM at
    # answer time. Pure capability arithmetic (mock card -> no GPU).
    from error_coupling_simulator.certify.anchors import DMOracleAnchor

    dm = DMOracleAnchor(card_bytes=32 * 1024**3)
    none_R1 = Regime(R=1, register="subregister", n_active=2, n_stab=None)
    none_R2 = Regime(R=2, register="subregister", n_active=2, n_stab=None)
    set_R1 = Regime(R=1, register="subregister", n_active=2, n_stab=1)  # same size, n_stab declared
    assert not dm.capability(Statistic.FULL_JOINT, none_R1).feasible
    assert not dm.capability(Statistic.RR_CORR, none_R2).feasible
    assert dm.capability(Statistic.FULL_JOINT, set_R1).feasible  # the size is fine; only None is refused


def test_shuffle_control_inapplicable_on_symmetric_value():
    # the real ShuffleControl on a FLAT/symmetric ground truth: np.roll is the identity, so the control
    # cannot perturb. It must mark itself INAPPLICABLE (not a FAILED falsifier -> no spurious FAIL); the
    # cell then has no working control -> FINDING (uncertified), never a PASS or a FAIL.
    from error_coupling_simulator.certify.anchors.controls import ShuffleControl as RealShuffleControl

    flat = {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25}
    rep = certify_cells(ControlledProcessFixture(flat), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(flat)], [RealShuffleControl()], N=20000)
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS  # data matches
    shuf = rep.controls[0]
    assert shuf.detail.get("applicable") is False  # the degenerate shuffle marked itself inapplicable
    assert rep.verdict is Verdict.FINDING, rep.summary()  # no spurious FAIL; uncertified for lack of teeth

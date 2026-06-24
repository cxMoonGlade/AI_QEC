"""Tests for ``qec_twin.audit.certify`` — the certification seam.

Step 1: the interface (the value types + the ``Anchor`` / ``Control`` / ``ControlledTeacher`` ports)
imports + constructs; the ``CertReport`` verdict / summary / assert_pass logic; the ports are
duck-typed ``runtime_checkable`` Protocols (the ``audit.floor_backend.PathJointEvaluator`` pattern).

Step 2: the core (route → controls-first → score → ledger) against an IN-MEMORY anchor with a known
law (the port IS the test surface — pure, no GPU). The genuine-check invariants are proven here:
a broken carrier FAILs; an inert control forces FAIL; an infeasible cell is UNANCHORED, never PASS;
exact anchors are preferred. The in-memory anchor + fake teacher live HERE (in ``tests/``) — they are
structurally never production anchors.
"""

from dataclasses import replace

import numpy as np

from qec_twin.audit.certify import (
    Anchor,
    AnchorValue,
    Capability,
    CertReport,
    Control,
    ControlledTeacher,
    Exactness,
    Feasibility,
    LedgerRow,
    Regime,
    Statistic,
    Verdict,
)
from qec_twin.audit.certify.core import certify_cells, compare, route

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
    assert ok.truth == {"theta": 0.15}  # the known truth is RETURNED (isolation: never to a learner)

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

        def answer(self, teacher, statistic, regime, *, N=None, generator=None):
            return None

    class _DuckControl:
        name = "shuffle"

        def guards(self, statistic):
            return True

        def expect(self):
            return "must_fail"

        def run(self, ctx, statistic, regime, *, N=None):
            return None

    class _DuckTeacher:
        sched = object()
        truth = {"theta": 0.15}

        def emit(self, regime, *, m, N, seed):
            return None

        def channels(self):
            return None

    assert isinstance(_DuckAnchor(), Anchor)
    assert isinstance(_DuckControl(), Control)
    assert isinstance(_DuckTeacher(), ControlledTeacher)
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


class FakeTeacher:
    """A controlled teacher emitting a KNOWN law (test fixture)."""

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

    def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
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
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [ShuffleControl()], N=20000)
    assert rep.verdict is Verdict.PASS, rep.summary()
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS
    assert all(c.detail["fired"] for c in rep.controls)  # the control has teeth (it fired)


def test_broken_carrier_fails():
    broken = FakeTeacher({0: 0.1, 1: 0.4, 2: 0.45, 3: 0.05})  # a DIFFERENT law
    rep = certify_cells(broken, [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [ShuffleControl()], N=20000)
    assert rep.verdict is Verdict.FAIL, rep.summary()  # the comparison has teeth


def test_inert_control_forces_fail():
    # the carrier MATCHES the anchor -> the positive row PASSES -> but an inert control forces FAIL.
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT)], [InertControl()], N=20000)
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS
    assert not any(c.detail["fired"] for c in rep.controls)
    assert rep.verdict is Verdict.FAIL, rep.summary()  # a vacuous check cannot pass


def test_infeasible_anchor_is_unanchored_not_pass():
    reg = Regime(R=2, register="full", n_active=9, n_stab=1)  # the OOM regime
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, reg)],
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
    from qec_twin.audit.certify.anchors import DMOracleAnchor

    dm = DMOracleAnchor(card_bytes=32 * 1024**3)  # mock a 32 GB card -> capability is pure, no GPU
    full9_R1 = Regime(R=1, register="full", n_active=9, n_stab=8)
    full9_R2 = Regime(R=2, register="full", n_active=9, n_stab=8)
    sub_R1 = Regime(R=1, register="subregister", n_active=3, n_stab=2)

    # DETECTOR_MARG @ R=1 full-9q: feasible (~12.4 GB single-stab projection) — the batch-1 GT path.
    cap = dm.capability(Statistic.DETECTOR_MARG, full9_R1)
    assert cap.feasible and cap.exactness is Exactness.EXACT and cap.epistemic_class == "a"
    assert 1.0e10 < cap.mem_bytes_estimate < 1.6e10  # ~12.4 GB live
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

    # documented independence (anti-circular) + answers the right statistics.
    assert "DIFFERENT object" in dm.independence
    assert Statistic.DETECTOR_MARG in dm.answers() and Statistic.RR_CORR not in dm.answers()


# ======================================================================= #
# Step 4a — the corrupt-stabilizer control (teeth) + the stim anchor        #
# ======================================================================= #
def test_corrupt_stab_control_fires_on_corruptible_anchor():
    from qec_twin.audit.certify.anchors import CorruptStabControl

    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT, corruptible=True)], [CorruptStabControl(stab=0)], N=20000)
    assert rep.verdict is Verdict.PASS, rep.summary()
    assert all(c.detail["fired"] for c in rep.controls)  # the corruption was caught (geometric teeth)


def test_corrupt_stab_control_inert_forces_fail():
    from qec_twin.audit.certify.anchors import CorruptStabControl

    # an anchor that CANNOT host the corruption returns the same answer -> the control can't fire -> FAIL.
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT, corruptible=False)], [CorruptStabControl(stab=0)], N=20000)
    assert not any(c.detail["fired"] for c in rep.controls)
    assert rep.verdict is Verdict.FAIL, rep.summary()  # a control that can't fail is vacuous -> FAIL


def test_stim_anchor_capability_and_emit_kind():
    from qec_twin.audit.certify.anchors import StimCliffordAnchor

    st = StimCliffordAnchor(p_x=0.03)
    assert st.emit_kind() == "clifford_slice"  # certifies the teacher's Clifford SLICE (wiring), not the full mechanism
    for R in (1, 2, 3):
        cap = st.capability(Statistic.SYNDROME_DIST, Regime(R=R, n_stab=8))
        assert cap.feasible and cap.exactness is Exactness.STATISTICAL and cap.epistemic_class == "b"
    assert "SEPARATE Clifford simulator" in st.independence
    assert Statistic.SYNDROME_DIST in st.answers()


# ======================================================================= #
# Step 5 — the closed-form sidecar (RR_CORR machinery + the T-B prediction) #
# ======================================================================= #
def test_rr_corr_machinery_matches_from_scratch():
    from qec_twin.audit.certify.core import emitted_statistic

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


def test_closed_form_anchor_predicts_two_state_markov_rr_corr():
    from qec_twin.audit.certify.anchors import ClosedFormAnchor

    a, b = 0.1, 0.2
    cf = ClosedFormAnchor(p01=a, p10=b, exact_single_qubit=True)
    assert cf.emit_kind() == "nonunital_slice"
    assert cf.answers() == frozenset({Statistic.RR_CORR})
    assert cf.capability(Statistic.RR_CORR, Regime(R=2, n_stab=1)).exactness is Exactness.EXACT
    assert not cf.capability(Statistic.RR_CORR, Regime(R=1, n_stab=1)).feasible  # R=1: no round-to-round

    # from-scratch two-state Markov detector flip-flip Pearson correlation (the independent identity):
    # E[d_r d_{r+1}] = p01 p10, E[d_r] = r = 2 p01 p10 /(p01+p10), Var = r(1-r).
    r = 2 * a * b / (a + b)
    corr_exact = abs((a * b - r * r) / (r * (1 - r)))
    assert abs(cf.predict() - corr_exact) < 1e-9  # the markov_flip_cov-based prediction == the closed form

    # d3 mode (default): an honest (b) prediction with a band — NOT inflated to exact.
    cf_d3 = ClosedFormAnchor(p01=a, p10=b)
    av = cf_d3.answer(None, Statistic.RR_CORR, Regime(R=2, n_stab=8))
    assert av.epistemic_class == "b" and av.exactness is Exactness.STATISTICAL and av.band > 0
    assert "no simulator" in cf_d3.independence


# ======================================================================= #
# Step 6 — the certify_teacher facade (orchestration: route + merge + roll) #
# ======================================================================= #
def test_certify_teacher_facade_merges_and_rolls_up():
    from qec_twin.audit.certify import certify_teacher
    from qec_twin.audit.certify.anchors import CorruptStabControl

    rep = certify_teacher(FakeTeacher(_JOINT), anchors=[InMemoryAnchor(_JOINT)],
                          cells=[(Statistic.FULL_JOINT, _REG)],
                          controls=[CorruptStabControl(stab=0)], N=20000)
    assert rep.verdict is Verdict.PASS, rep.summary()
    assert rep.row("in_memory", Statistic.FULL_JOINT).verdict is Verdict.PASS
    assert all(c.detail["fired"] for c in rep.controls)
    assert rep.provenance["level"] == "standard" and rep.provenance["N"] == 20000

    raised = False  # an unknown level is rejected
    try:
        certify_teacher(FakeTeacher(_JOINT), level="bogus", anchors=[InMemoryAnchor(_JOINT)],
                        cells=[(Statistic.FULL_JOINT, _REG)])
    except ValueError:
        raised = True
    assert raised

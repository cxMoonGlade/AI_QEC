"""Per-unit L0+L1+KILLER coverage of the four
independent-ground-truth anchor adapters + the negative controls under
``error_coupling_simulator.certify.anchors``:

  * ``closed_form.ClosedFormAnchor``   -- the analytic sidecar (transient two-state Markov RR_CORR),
  * ``controls.{CorruptStabControl, ShuffleControl}`` -- the first-class negative controls,
  * ``stim_clifford.StimCliffordAnchor`` -- the implementation-INDEPENDENT Clifford-slice wiring check,
  * ``dm_oracle.DMOracleAnchor``       -- the exact density-matrix route (capability is CPU-pure;
    ``answer`` is TRUE GPU and is out_of_scope=gpu_bound in the registry -- NOT tested here).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4; work-list
docs/SIMULATOR.md). Registry:
``tests/_support/certify_anchors_coverage_targets.json`` (17 registered public units; the 18th public
unit ``DMOracleAnchor.answer`` is out_of_scope gpu_bound). CPU-ONLY: the DM capability is exercised
with a MOCKED ``card_bytes`` (pure arithmetic, no CUDA); stim is a lazy CPU Clifford import; the
closed form is numpy-only. Nothing here touches a GPU.

Test discipline (feedback-devious-tests-killer-standard). Every load-bearing assert is DISCRIMINATING:
``assert_pins`` pins a VALUE against a from-scratch/closed-form INDEPENDENT recompute (never a >=0
bound), and ``assert_discriminates`` proves the property HOLDS for the real impl and FAILS for the
NAMED sabotage (drop the R<2 guard / replace p01*p10 with e_dr*e_dr1 / hardcode band / drop
``and need<=budget`` / return-feasible-for-RR_CORR / fired=True-always / return-True-always-guards /
drop the seam-XOR detector).

Honesty note (convergence). The stim anchor is STATISTICAL; the pins are at a FIXED seed (deterministic)
against an INDEPENDENT CLOSED-FORM syndrome distribution (the two-state parity algebra) -- an
implementation-independent reference, never the anchor's own sampler; the tolerance is the declared
6/sqrt(N) sampling band, not a physical convergence claim.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins

from error_coupling_simulator.certify.anchors.closed_form import ClosedFormAnchor
from error_coupling_simulator.certify.anchors.controls import (
    _GEOM,
    _shuffle_value,
    _value_close,
    CorruptStabControl,
    ShuffleControl,
)
from error_coupling_simulator.certify.anchors.dm_oracle import DMOracleAnchor
from error_coupling_simulator.certify.anchors.stim_clifford import (
    StimCliffordAnchor,
    _stim_slice_records,
)
from error_coupling_simulator.certify.core import MeasureCtx, certify_cells
from error_coupling_simulator.certify.types import (
    AnchorValue,
    Capability,
    Exactness,
    LedgerRow,
    Regime,
    Statistic,
    Verdict,
)


# =========================================================================== #
# TEST FIXTURES (TEST-ONLY: in tests/, never production anchors) -- the        #
# ControlledProcessFixture / InMemoryAnchor stub pattern reused from tests/test_certify.py  #
# so the "Mixed" control-run units run on CPU with NO GPU.                      #
# =========================================================================== #
_JOINT = {0: 0.4, 1: 0.1, 2: 0.05, 3: 0.45}
_FLAT = {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25}
_REG = Regime(R=1, register="subregister", n_active=1, n_stab=1)


def _make_records(joint: dict, N: int) -> dict:
    """Deterministic (det, obs) realizing ``joint`` (key = det + (flip<<1); 1-stab R=1 surface)."""
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
    """TEST FIXTURE -- a hand-written known law that shares no code with any engine (the port IS the
    test surface)."""

    name = "in_memory"
    independence = "hand-written known law (TEST fixture; shares no code with any engine)"

    def __init__(self, joint: dict, *, feasible: bool = True, exactness=Exactness.EXACT,
                 corruptible: bool = True):
        self._joint = joint
        self._feasible = feasible
        self._exactness = exactness
        self._corruptible = corruptible

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
            u = 1.0 / len(val)
            val = {k: u for k in val}
        cls = "a" if self._exactness is Exactness.EXACT else "b"
        band = 0.0 if self._exactness is Exactness.EXACT else 0.01
        return AnchorValue(statistic, regime, val, self._exactness, band, cls,
                           provenance={"anchor": self.name})


# =========================================================================== #
# Independent from-scratch references for the closed-form anchor               #
# (DIFFERENT computations than the module -- anti-circular).                   #
# =========================================================================== #
def _exact_rr_from_paths(p01: float, p10: float, R: int) -> np.ndarray:
    """|Corr(d_r, d_{r+1})| by FULL 2^R path enumeration (a DIFFERENT method than the module's local
    triple-joint), s_{-1}=0, d_r = s_{r-1} XOR s_r. The genuinely-independent ground truth."""
    T = np.array([[1 - p01, p01], [p10, 1 - p10]])
    paths = list(itertools.product((0, 1), repeat=R))
    probs = np.array([np.prod([T[(pth[k - 1] if k else 0), pth[k]] for k in range(R)]) for pth in paths])
    S = np.array(paths)
    s_prev = np.concatenate([np.zeros((len(paths), 1), int), S[:, :-1]], axis=1)
    D = (S ^ s_prev).astype(float)
    out = []
    for r in range(R - 1):
        x, y = D[:, r], D[:, r + 1]
        ex, ey, exy = (probs * x).sum(), (probs * y).sum(), (probs * x * y).sum()
        vx, vy = ex * (1 - ex), ey * (1 - ey)
        out.append(abs((exy - ex * ey) / np.sqrt(vx * vy)) if vx > 1e-12 and vy > 1e-12 else 0.0)
    return np.array(out, dtype=np.float64)


def _flip_flip_ref(p01: float, p10: float, R: int, a0=None) -> np.ndarray:
    """The analytic flip-flip identity E[d_r d_{r+1}] = p01 p10 (r = 1..R-2), recomputed from scratch."""
    a = np.empty(R)
    a[0] = p01 if a0 is None else a0
    q = 1.0 - p01 - p10
    for r in range(1, R):
        a[r] = p01 + a[r - 1] * q
    out = []
    for r in range(1, R - 1):
        e_dr = p01 + a[r - 1] * (p10 - p01)
        e_dr1 = p01 + a[r] * (p10 - p01)
        vr, vr1 = e_dr * (1 - e_dr), e_dr1 * (1 - e_dr1)
        out.append(abs((p01 * p10 - e_dr * e_dr1) / np.sqrt(vr * vr1)) if vr > 1e-12 and vr1 > 1e-12 else 0.0)
    return np.array(out, dtype=np.float64)


def _flip_flip_sabotaged(p01: float, p10: float, R: int, a0=None) -> np.ndarray:
    """KILLER sabotage: replace p01*p10 with e_dr*e_dr1 -> the flip-flip identity dies (all zeros)."""
    a = np.empty(R)
    a[0] = p01 if a0 is None else a0
    q = 1.0 - p01 - p10
    for r in range(1, R):
        a[r] = p01 + a[r - 1] * q
    out = []
    for r in range(1, R - 1):
        e_dr = p01 + a[r - 1] * (p10 - p01)
        e_dr1 = p01 + a[r] * (p10 - p01)
        vr, vr1 = e_dr * (1 - e_dr), e_dr1 * (1 - e_dr1)
        out.append(abs((e_dr * e_dr1 - e_dr * e_dr1) / np.sqrt(vr * vr1)) if vr > 1e-12 and vr1 > 1e-12 else 0.0)
    return np.array(out, dtype=np.float64)


# =========================================================================== #
# closed_form.ClosedFormAnchor -- 5 units                                      #
# =========================================================================== #
def test_closed_form_emit_kind_and_answers():
    # emit_kind + answers are constants: pin the exact values (a wrong constant is caught).
    cf = ClosedFormAnchor(p01=0.08, p10=0.20)
    assert cf.emit_kind() == "nonunital_slice"
    assert cf.answers() == frozenset({Statistic.RR_CORR})


def test_closed_form_capability_all_arcs():
    # cover BOTH the early-return guard (statistic-not-RR_CORR OR R<2) AND the R>=2 feasible leg,
    # AND both the EXACT/class-a and STATISTICAL/class-b legs of the exness/cls ternaries.
    cf_exact = ClosedFormAnchor(p01=0.08, p10=0.20, exact_single_qubit=True)
    cf_d3 = ClosedFormAnchor(p01=0.08, p10=0.20)

    # arc 1: statistic is not RR_CORR -> infeasible, class 'a'.
    c1 = cf_exact.capability(Statistic.FULL_JOINT, Regime(R=2, n_stab=1))
    assert not c1.feasible and c1.epistemic_class == "a" and c1.exactness is Exactness.EXACT
    # arc 2: RR_CORR but R<2 -> infeasible (the R<2 guard).
    c2 = cf_exact.capability(Statistic.RR_CORR, Regime(R=1, n_stab=1))
    assert not c2.feasible
    # arc 3: RR_CORR, R>=2, EXACT single-qubit -> feasible, EXACT, class 'a'.
    c3 = cf_exact.capability(Statistic.RR_CORR, Regime(R=3, n_stab=1))
    assert c3.feasible and c3.exactness is Exactness.EXACT and c3.epistemic_class == "a"
    # arc 4: RR_CORR, R>=2, d3 (the STATISTICAL/'b' leg).
    c4 = cf_d3.capability(Statistic.RR_CORR, Regime(R=3, n_stab=8))
    assert c4.feasible and c4.exactness is Exactness.STATISTICAL and c4.epistemic_class == "b"


def test_closed_form_capability_drop_R_guard_is_caught():
    # KILLER: an anchor that drops the "regime.R < 2" guard would declare RR_CORR feasible at R=1
    # (there is no round-to-round pair at R=1) -- the guard MUST make it infeasible.
    class _NoRGuardClosedForm(ClosedFormAnchor):
        def capability(self, statistic, regime):
            if statistic is not Statistic.RR_CORR:
                return Capability(statistic, Exactness.EXACT, False, "", "a", 0)
            exness = Exactness.EXACT if self._exact else Exactness.STATISTICAL
            cls = "a" if self._exact else "b"
            return Capability(statistic, exness, True, "", cls, 0)  # SABOTAGE: no R<2 guard

    def _r1_infeasible(anchor):
        assert not anchor.capability(Statistic.RR_CORR, Regime(R=1, n_stab=1)).feasible

    assert_discriminates(_r1_infeasible,
                         real=ClosedFormAnchor(p01=0.08, p10=0.20, exact_single_qubit=True),
                         wrong=_NoRGuardClosedForm(p01=0.08, p10=0.20, exact_single_qubit=True),
                         label="closed_form R<2 guard")


def test_closed_form_predict_sequence_flip_flip_theorem():
    # THEOREM E[d_r d_{r+1}] = p01 p10 (transient cancels). predict_sequence is pinned against
    # (i) the module's OWN _exact_rr_corr[1:] (the two internal computations must agree) AND
    # (ii) an INDEPENDENT from-scratch flip-flip recompute; every |corr| in [0,1].
    cf = ClosedFormAnchor(p01=0.08, p10=0.20, exact_single_qubit=True)
    R = 6
    seq = cf.predict_sequence(R)
    assert seq.shape == (R - 2,)
    assert np.all(seq >= 0.0) and np.all(seq <= 1.0)  # |corr| in [0,1]
    assert_pins(seq, cf._exact_rr_corr(R)[1:], atol=1e-12, label="predict_sequence vs _exact_rr_corr[1:]")
    assert_pins(seq, _flip_flip_ref(0.08, 0.20, R), atol=1e-12, label="predict_sequence vs from-scratch")

    # cover the zero-variance else-append: p01=p10=0 -> a_r=0 -> e_dr=0 -> var=0 -> append 0.0.
    zero_seq = ClosedFormAnchor(p01=0.0, p10=0.0, exact_single_qubit=True).predict_sequence(4)
    assert zero_seq.shape == (2,) and np.array_equal(zero_seq, np.zeros(2))


def test_closed_form_predict_sequence_killer():
    # KILLER (assert_discriminates): replacing p01*p10 with e_dr*e_dr1 zeroes the identity.
    R = 6
    ref = _flip_flip_ref(0.08, 0.20, R)

    def _matches_flip_flip(seq):
        assert_pins(seq, ref, atol=1e-12, label="flip-flip")

    assert_discriminates(_matches_flip_flip,
                         real=ClosedFormAnchor(p01=0.08, p10=0.20, exact_single_qubit=True).predict_sequence(R),
                         wrong=_flip_flip_sabotaged(0.08, 0.20, R),
                         label="predict_sequence p01*p10")


def test_closed_form_exact_rr_corr_independent_ground_truth():
    # the anchor's GROUND TRUTH (_exact_rr_corr, exercised via answer) pinned vs the FULLY INDEPENDENT
    # 2^R path enumeration -- a different method, so a coding bug in one is not replicated in the other.
    a, b, R = 0.08, 0.20, 6
    cf = ClosedFormAnchor(p01=a, p10=b, exact_single_qubit=True)
    assert_pins(cf._exact_rr_corr(R), _exact_rr_from_paths(a, b, R), atol=1e-12,
                label="_exact_rr_corr vs full-path enumeration")
    # zero-variance else-branch of _exact_rr_corr (degenerate absorbing member) -> all zeros.
    assert np.array_equal(ClosedFormAnchor(p01=0.0, p10=0.0, exact_single_qubit=True)._exact_rr_corr(4),
                          np.zeros(3))


def test_closed_form_answer_exact_and_statistical_legs():
    # cover BOTH answer legs: EXACT (band==0, class 'a') AND d3 STATISTICAL (band==band_d3>0, class 'b').
    a, b, R = 0.08, 0.20, 6
    reg = Regime(R=R, n_stab=8)

    av_exact = ClosedFormAnchor(p01=a, p10=b, exact_single_qubit=True).answer(None, Statistic.RR_CORR, reg)
    assert av_exact.exactness is Exactness.EXACT and av_exact.epistemic_class == "a"
    assert av_exact.band == 0.0                       # EXACT <=> band 0
    assert av_exact.value.shape == (R - 1,)
    assert np.all(av_exact.value >= 0.0) and np.all(av_exact.value <= 1.0)

    cf_d3 = ClosedFormAnchor(p01=a, p10=b, band_d3=0.02)  # d3 default
    av_d3 = cf_d3.answer(None, Statistic.RR_CORR, reg)
    assert av_d3.exactness is Exactness.STATISTICAL and av_d3.epistemic_class == "b"
    assert av_d3.band == pytest.approx(0.02) and av_d3.band > 0.0
    assert av_d3.value.shape == (R - 1,)


def test_closed_form_answer_band_tracks_exactness_killer():
    # KILLER: a hardcoded band (regardless of _exact) breaks the EXACT<=>band==0 contract. The
    # d3 anchor MUST carry a positive band; an exact anchor MUST carry band 0 -- so a hardcode of
    # EITHER value is caught. assert_discriminates proves the property distinguishes the two.
    a, b = 0.08, 0.20
    reg = Regime(R=6, n_stab=8)

    def _band_positive(anchor):
        assert anchor.answer(None, Statistic.RR_CORR, reg).band > 0.0

    assert_discriminates(_band_positive,
                         real=ClosedFormAnchor(p01=a, p10=b),                         # d3 -> band>0
                         wrong=ClosedFormAnchor(p01=a, p10=b, exact_single_qubit=True),  # exact -> band 0
                         label="answer band tracks exactness")


@settings(max_examples=40, deadline=None)
@given(p01=st.floats(0.01, 0.49), p10=st.floats(0.01, 0.49), R=st.integers(4, 8))
def test_closed_form_predict_sequence_property(p01, p10, R):
    # L1: the flip-flip theorem holds over thousands of (p01, p10, R) -- predict_sequence matches BOTH
    # the module's internal brute-force _exact_rr_corr[1:] AND the from-scratch flip-flip formula.
    cf = ClosedFormAnchor(p01=p01, p10=p10, exact_single_qubit=True)
    seq = cf.predict_sequence(R)
    assert_pins(seq, cf._exact_rr_corr(R)[1:], atol=1e-9, label="internal agreement")
    assert_pins(seq, _flip_flip_ref(p01, p10, R), atol=1e-9, label="flip-flip agreement")


# =========================================================================== #
# controls.CorruptStabControl -- 3 units (guards / expect / run)               #
# =========================================================================== #
def test_corrupt_stab_control_guards():
    ctrl = CorruptStabControl(stab=1)
    # guards <=> statistic in the geometry set.
    for s in _GEOM:
        assert ctrl.guards(s)
    assert not ctrl.guards(Statistic.SCALAR_FUNC)


def test_corrupt_stab_control_guards_killer():
    # KILLER: return True always -> a control that guards a non-geometry statistic.
    class _AlwaysGuardCorrupt(CorruptStabControl):
        def guards(self, statistic):
            return True  # SABOTAGE

    def _scalar_not_guarded(ctrl):
        assert not ctrl.guards(Statistic.SCALAR_FUNC)

    assert_discriminates(_scalar_not_guarded, real=CorruptStabControl(stab=1),
                         wrong=_AlwaysGuardCorrupt(stab=1), label="CorruptStabControl guards")


def test_corrupt_stab_control_expect():
    # NO caller in these modules -> direct assert of the constant.
    assert CorruptStabControl(stab=1).expect() == "must_fail"


def test_corrupt_stab_control_run_both_fired_arcs():
    # run drives ctx.corrupt_answer -> compare -> fired <=> verdict FAIL. Cover BOTH arcs of the
    # `1.0 if fired else 0.0` outcome via a corruptible anchor (fires) and a non-corruptible one
    # (cannot host the corruption -> same answer -> does not fire).
    rep_fire = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                             [InMemoryAnchor(_JOINT, corruptible=True)], [CorruptStabControl(stab=0)],
                             N=20000)
    assert rep_fire.controls[0].detail["fired"] is True
    assert rep_fire.controls[0].detail["applicable"] is True

    rep_inert = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                              [InMemoryAnchor(_JOINT, corruptible=False)], [CorruptStabControl(stab=0)],
                              N=20000)
    assert rep_inert.controls[0].detail["fired"] is False


def test_corrupt_stab_control_run_inert_forces_fail_killer():
    # KILLER (assert_discriminates): a run that sets fired=True ALWAYS no longer forces the verdict to
    # FAIL on an inert (non-corruptible) anchor -- a vacuous control that "can't fail" would PASS.
    class _AlwaysFiredCorruptControl(CorruptStabControl):
        def run(self, ctx, statistic, regime, *, N=None):
            return LedgerRow(ctx.anchor.name, statistic, 1.0, None, "c", Verdict.CONTROL,
                             {"fired": True, "applicable": True, "name": self.name, "stab": self._stab})

    def _inert_control_forces_fail(control):
        rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                            [InMemoryAnchor(_JOINT, corruptible=False)], [control], N=20000)
        assert rep.verdict is Verdict.FAIL

    assert_discriminates(_inert_control_forces_fail, real=CorruptStabControl(stab=0),
                         wrong=_AlwaysFiredCorruptControl(stab=0), label="CorruptStabControl.run teeth")


# =========================================================================== #
# controls.ShuffleControl -- 3 units (guards / expect / run)                   #
# =========================================================================== #
def test_shuffle_control_guards_always():
    ctrl = ShuffleControl()
    for s in (Statistic.FULL_JOINT, Statistic.SCALAR_FUNC, Statistic.RR_CORR):
        assert ctrl.guards(s)


def test_shuffle_control_guards_killer():
    # KILLER: ShuffleControl guards ANY statistic; a geometry-only guard drops SCALAR_FUNC.
    class _GeomOnlyShuffle(ShuffleControl):
        def guards(self, statistic):
            return statistic in _GEOM  # SABOTAGE: not always True

    def _scalar_guarded(ctrl):
        assert ctrl.guards(Statistic.SCALAR_FUNC)

    assert_discriminates(_scalar_guarded, real=ShuffleControl(), wrong=_GeomOnlyShuffle(),
                         label="ShuffleControl guards-always")


def test_shuffle_control_expect():
    assert ShuffleControl().expect() == "must_fail"


def _shuffle_ctx(value, emitted, statistic):
    """A MeasureCtx wrapping a hand-built anchor value + emitted statistic (no GPU, no process)."""
    class _Stub:
        name = "stub"
    av = AnchorValue(statistic, _REG, value, Exactness.EXACT, 0.0, "a", {})
    return MeasureCtx(_Stub(), statistic, _REG, 20000, emitted, av, process=None)


def test_shuffle_control_run_applicable_dict_fires():
    # applicable leg (non-symmetric dict): the roll perturbs -> compare FAILs -> fired True.
    ctrl = ShuffleControl()
    ctx = _shuffle_ctx(dict(_JOINT), dict(_JOINT), Statistic.FULL_JOINT)
    row = ctrl.run(ctx, Statistic.FULL_JOINT, _REG, N=20000)
    assert row.detail["applicable"] is True and row.detail["fired"] is True


def test_shuffle_control_run_inapplicable_flat():
    # inapplicable leg (flat/symmetric dict): np.roll of values is the identity -> INAPPLICABLE.
    ctrl = ShuffleControl()
    ctx = _shuffle_ctx(dict(_FLAT), dict(_FLAT), Statistic.FULL_JOINT)
    row = ctrl.run(ctx, Statistic.FULL_JOINT, _REG, N=20000)
    assert row.detail["applicable"] is False and row.detail["fired"] is False


def test_shuffle_control_run_ndarray_branch():
    # the ndarray branch of _shuffle_value / _value_close (an array statistic, non-symmetric).
    ctrl = ShuffleControl()
    arr = np.array([0.1, 0.5, 0.9])
    ctx = _shuffle_ctx(arr.copy(), arr.copy(), Statistic.DETECTOR_MARG)
    row = ctrl.run(ctx, Statistic.DETECTOR_MARG, _REG, N=20000)
    assert row.detail["applicable"] is True and row.detail["fired"] is True


def test_shuffle_control_run_killer():
    # KILLER: swapping two keys of a NON-symmetric distribution MUST be caught (applicable + fired);
    # an IDENTITY perturbation (the sabotage) would leave the control INAPPLICABLE -> no teeth.
    class _IdentityShuffleControl(ShuffleControl):
        def run(self, ctx, statistic, regime, *, N=None):
            shuffled = ctx.anchor_value  # SABOTAGE: identity, never perturbs
            if _value_close(shuffled.value, ctx.anchor_value.value):
                return LedgerRow(ctx.anchor.name, statistic, 0.0, None, "c", Verdict.CONTROL,
                                 {"fired": False, "applicable": False, "name": self.name})
            return LedgerRow(ctx.anchor.name, statistic, 1.0, None, "c", Verdict.CONTROL,
                             {"fired": True, "applicable": True, "name": self.name})

    def _fires_on_nonsymmetric(control):
        ctx = _shuffle_ctx(dict(_JOINT), dict(_JOINT), Statistic.FULL_JOINT)
        row = control.run(ctx, Statistic.FULL_JOINT, _REG, N=20000)
        assert row.detail["applicable"] and row.detail["fired"]

    assert_discriminates(_fires_on_nonsymmetric, real=ShuffleControl(),
                         wrong=_IdentityShuffleControl(), label="ShuffleControl.run teeth")


def test_shuffle_helpers_mixed_and_symmetric():
    # direct coverage of the private _shuffle_value / _value_close edge branches (exercised by run):
    # the mixed dict-vs-nondict False leg and the array symmetric True leg.
    assert _value_close({0: 0.5, 1: 0.5}, np.array([0.5, 0.5])) is False  # mixed types -> False
    sym = np.array([0.3, 0.3, 0.3])
    assert _value_close(np.roll(sym, 1), sym) is True                     # flat array -> identity roll
    rolled = _shuffle_value(AnchorValue(Statistic.DETECTOR_MARG, _REG, np.array([1.0, 2.0, 3.0]),
                                        Exactness.EXACT, 0.0, "a", {}))
    assert np.array_equal(np.asarray(rolled.value), np.array([3.0, 1.0, 2.0]))  # np.roll by 1


# =========================================================================== #
# stim_clifford.StimCliffordAnchor -- 4 units                                  #
# =========================================================================== #
class _Stab:
    def __init__(self, paulis):
        self.paulis = paulis


class _Sched:
    """A minimal duck-typed schedule: one ZZ stabilizer on two data qubits, logical Z0."""

    def __init__(self):
        self.n_data = 2
        self.stabilizers = [_Stab({0: "Z", 1: "Z"})]
        self.logical = {0: "Z"}


class _StimProcessFixture:
    def __init__(self):
        self.sched = _Sched()
        self.truth = {}


def _q(p):
    return 2.0 * p * (1.0 - p)


def _syndrome_with_seam_R2(p):
    """Closed-form P(det0, det1) for the ZZ two-state slice WITH the seam XOR: det0, det1 are the two
    INDEPENDENT per-round flip parities (key = det0 + 2*det1)."""
    q = _q(p)
    return {0: (1 - q) ** 2, 1: q * (1 - q), 2: (1 - q) * q, 3: q * q}


def _syndrome_without_seam_R2(p):
    """The SABOTAGE reference: detector1 = raw MPP (no XOR with round 0) -> det1 = det0 XOR (round-1
    parity), so det0 and det1 are CORRELATED -- a different joint (keys 1 and 3 swap mass)."""
    q = _q(p)
    return {0: (1 - q) ** 2, 1: q * q, 2: (1 - q) * q, 3: q * (1 - q)}


def _dense(d, keys=(0, 1, 2, 3)):
    return {k: float(d.get(k, 0.0)) for k in keys}


def test_stim_emit_kind_and_answers():
    st_anchor = StimCliffordAnchor(p_x=0.03)
    assert st_anchor.emit_kind() == "clifford_slice"
    assert st_anchor.answers() == frozenset(
        {Statistic.SYNDROME_DIST, Statistic.DETECTOR_MARG, Statistic.FULL_JOINT})


def test_stim_capability_both_arcs():
    st_anchor = StimCliffordAnchor(p_x=0.03)
    for s in (Statistic.SYNDROME_DIST, Statistic.DETECTOR_MARG, Statistic.FULL_JOINT):
        cap = st_anchor.capability(s, Regime(R=2, n_stab=8))
        assert cap.feasible and cap.exactness is Exactness.STATISTICAL and cap.epistemic_class == "b"
    # a statistic stim does NOT answer -> infeasible (the guard has teeth).
    cap_rr = st_anchor.capability(Statistic.RR_CORR, Regime(R=2, n_stab=8))
    assert not cap_rr.feasible and cap_rr.exactness is Exactness.STATISTICAL


def test_stim_capability_rr_corr_killer():
    # KILLER: return feasible for RR_CORR (a Clifford-blind round-to-round leakage correlation).
    class _RRFeasibleStim(StimCliffordAnchor):
        def capability(self, statistic, regime):
            return Capability(statistic, Exactness.STATISTICAL, True, "", "b", 0)  # SABOTAGE

    def _rr_infeasible(anchor):
        assert not anchor.capability(Statistic.RR_CORR, Regime(R=2, n_stab=8)).feasible

    assert Statistic.RR_CORR not in StimCliffordAnchor().answers()
    assert_discriminates(_rr_infeasible, real=StimCliffordAnchor(), wrong=_RRFeasibleStim(),
                         label="stim RR_CORR feasibility")


def test_stim_answer_syndrome_dist_pins_closed_form():
    # answer at R=2: the seam-folded SYNDROME_DIST is pinned against the INDEPENDENT closed-form
    # two-state parity distribution (NOT the anchor's own sampler); band == 6/sqrt(N); shape match.
    p, N = 0.1, 50000
    reg = Regime(R=2, n_stab=1, n_active=2)
    st_anchor = StimCliffordAnchor(p_x=p, seed=4242)
    av = st_anchor.answer(_StimProcessFixture(), Statistic.SYNDROME_DIST, reg, N=N)

    assert av.exactness is Exactness.STATISTICAL and av.epistemic_class == "b"
    assert av.band == pytest.approx(6.0 / math.sqrt(N))
    emp = _dense(av.value)
    assert_pins(emp, _dense(_syndrome_with_seam_R2(p)), atol=0.02,
                label="stim SYNDROME_DIST vs closed-form (with seam)")
    # emitted-shape match: R*n_stab = 2 folded detectors -> keys span {0,1,2,3}.
    assert set(av.value) <= {0, 1, 2, 3}


def test_stim_answer_seam_xor_killer():
    # KILLER: dropping the seam-XOR detector produces the CORRELATED (without-seam) joint -> the pin
    # catches it (keys 1 and 3 differ by >0.1). The anchor matches WITH-seam and NOT without-seam.
    p, N = 0.1, 50000
    reg = Regime(R=2, n_stab=1, n_active=2)
    av = StimCliffordAnchor(p_x=p, seed=4242).answer(_StimProcessFixture(), Statistic.SYNDROME_DIST, reg, N=N)
    emp = _dense(av.value)
    with_seam = _dense(_syndrome_with_seam_R2(p))
    without_seam = _dense(_syndrome_without_seam_R2(p))

    def _matches_with_seam(dist):
        assert_pins(dist, with_seam, atol=0.02, label="with-seam")

    assert_discriminates(_matches_with_seam, real=emp, wrong=without_seam,
                         label="stim seam-XOR detector")


def test_stim_answer_corrupt_and_marg_and_m1_paths():
    # exercise answer's corrupt ternary + the DETECTOR_MARG surface + the slice builder's m==1
    # logical-|1> prep branch, asserting the emitted shape/band (not an analytic pin). The transversal
    # X/Y DD echoes are intentionally absent from the Clifford slice (frame-invariant; see the anchor
    # module docstring) -> there is no echo branch to cover here.
    reg = Regime(R=2, n_stab=1, n_active=2)
    av_corrupt = StimCliffordAnchor(p_x=0.1).answer(_StimProcessFixture(), Statistic.SYNDROME_DIST, reg,
                                                    N=4000, corrupt={"stab": 0})
    assert av_corrupt.provenance["corrupt_stab"] == 0
    av_marg = StimCliffordAnchor(p_x=0.1).answer(_StimProcessFixture(), Statistic.DETECTOR_MARG, reg, N=4000)
    assert np.asarray(av_marg.value).shape == (reg.R * reg.n_stab + 1,)  # per-detector + flip rate
    # directly cover the private slice builder's m==1 logical-|1> prep branch.
    det, obs = _stim_slice_records(_Sched(), 0.1, reg, m=1, N=2000, seed=1, corrupt_stab=None)
    assert det.shape == (2000, reg.R * 1) and obs.shape == (2000,)


@pytest.mark.parametrize("p", [0.05, 0.1, 0.15])
def test_stim_answer_property_sweep(p):
    # L1 (crafted sweep for the engine unit): the seam-folded R=2 SYNDROME_DIST matches the
    # closed-form independent-round product distribution across a sweep of bit-flip rates.
    N = 60000
    reg = Regime(R=2, n_stab=1, n_active=2)
    av = StimCliffordAnchor(p_x=p, seed=4242).answer(_StimProcessFixture(), Statistic.SYNDROME_DIST, reg, N=N)
    assert_pins(_dense(av.value), _dense(_syndrome_with_seam_R2(p)), atol=0.02,
                label=f"stim sweep p={p}")


# =========================================================================== #
# dm_oracle.DMOracleAnchor -- 2 registered units (answers / capability)        #
# (answer is TRUE GPU -> out_of_scope gpu_bound; NOT tested here).             #
# capability is CPU-pure arithmetic with a MOCKED card_bytes: NO CUDA.         #
# =========================================================================== #
_CARD32 = 32 * 1024 ** 3


def test_dm_answers():
    dm = DMOracleAnchor(card_bytes=_CARD32)
    assert dm.answers() == frozenset(
        {Statistic.DETECTOR_MARG, Statistic.FULL_JOINT, Statistic.SYNDROME_DIST,
         Statistic.RR_CORR, Statistic.SPATIAL_CORR})


def test_dm_capability_detector_marg_arcs():
    dm = DMOracleAnchor(card_bytes=_CARD32)          # budget = 16 GB
    full9_R1 = Regime(R=1, register="full", n_active=9, n_stab=8)
    full9_R2 = Regime(R=2, register="full", n_active=9, n_stab=8)
    sub_R1 = Regime(R=1, register="subregister", n_active=3, n_stab=2)

    # R != 1 -> needs the moments path (not single-stab projection).
    c_r2 = dm.capability(Statistic.DETECTOR_MARG, full9_R2)
    assert not c_r2.feasible and "moments" in c_r2.reason and c_r2.mem_bytes_estimate is None
    # R == 1, feasible (small register, budget covers need).
    c_ok = dm.capability(Statistic.DETECTOR_MARG, sub_R1)
    assert c_ok.feasible and c_ok.reason == "" and c_ok.epistemic_class == "a"
    # R == 1, infeasible via need > budget (full-9q ~ 24.8 GB > 16 GB).
    c_oom = dm.capability(Statistic.DETECTOR_MARG, full9_R1)
    assert not c_oom.feasible and "budget" in c_oom.reason and c_oom.mem_bytes_estimate > 2.2e10
    # R == 1, infeasible via budget == 0 (no CUDA / card unknown).
    c_nob = DMOracleAnchor(card_bytes=0).capability(Statistic.DETECTOR_MARG, sub_R1)
    assert not c_nob.feasible and "no GPU budget known" in c_nob.reason


def test_dm_capability_moments_arcs():
    dm = DMOracleAnchor(card_bytes=_CARD32)
    for stat in (Statistic.RR_CORR, Statistic.SPATIAL_CORR):
        # R < 2 -> no round-to-round / realized second moment.
        c_r1 = dm.capability(stat, Regime(R=1, register="full", n_active=9, n_stab=8))
        assert not c_r1.feasible and "R>=2" in c_r1.reason
        # n_stab is None -> cannot bound the depth stack -> refused.
        c_none = dm.capability(stat, Regime(R=2, register="subregister", n_active=3, n_stab=None))
        assert not c_none.feasible and "n_stab unknown" in c_none.reason
        # feasible on a small valid sub-code.
        c_ok = dm.capability(stat, Regime(R=2, register="subregister", n_active=3, n_stab=2))
        assert c_ok.feasible and c_ok.epistemic_class == "a" and c_ok.reason == ""
        # infeasible full-9q (route the scale to the carrier-MCWF).
        c_big = dm.capability(stat, Regime(R=2, register="full", n_active=9, n_stab=8))
        assert not c_big.feasible and "carrier-MCWF" in c_big.reason and c_big.mem_bytes_estimate > 4e10
        # budget == 0 -> infeasible (no CUDA).
        c_nob = DMOracleAnchor(card_bytes=0).capability(stat, Regime(R=2, n_active=3, n_stab=2))
        assert not c_nob.feasible and "no GPU budget known" in c_nob.reason


def test_dm_capability_full_joint_arcs():
    dm = DMOracleAnchor(card_bytes=_CARD32)
    # statistic not answered -> "DM anchor does not answer this".
    c_no = dm.capability(Statistic.SCALAR_FUNC, Regime(R=1, n_active=3, n_stab=1))
    assert not c_no.feasible and "does not answer" in c_no.reason
    # n_stab None -> refused.
    c_none = dm.capability(Statistic.FULL_JOINT, Regime(R=1, n_active=3, n_stab=None))
    assert not c_none.feasible and "n_stab unknown" in c_none.reason
    # feasible small register.
    c_ok = dm.capability(Statistic.FULL_JOINT, Regime(R=1, n_active=3, n_stab=1))
    assert c_ok.feasible and c_ok.reason == ""
    # R>=2 record_oracle exposes moments only, even when a tiny register fits in memory.
    c_r2 = dm.capability(Statistic.FULL_JOINT, Regime(R=2, n_active=1, n_stab=1))
    assert not c_r2.feasible and "returns moments only" in c_r2.reason
    assert c_r2.mem_bytes_estimate is None
    # infeasible full-9q depth-8 enumeration (~50 GB > 16 GB).
    c_big = dm.capability(Statistic.FULL_JOINT, Regime(R=1, register="full", n_active=9, n_stab=8))
    assert not c_big.feasible and "budget" in c_big.reason and c_big.mem_bytes_estimate > 4e10
    # budget == 0 -> infeasible.
    c_nob = DMOracleAnchor(card_bytes=0).capability(Statistic.FULL_JOINT, Regime(R=1, n_active=3, n_stab=1))
    assert not c_nob.feasible and "no GPU budget known" in c_nob.reason


def test_dm_capability_need_le_budget_killer():
    # KILLER: dropping the "and need <= budget" clause would declare an OOM full-9q R=1 DETECTOR_MARG
    # cell FEASIBLE (need ~ 24.8 GB > 16 GB budget) -> an OOM at answer time.
    class _NoBudgetGuardDM(DMOracleAnchor):
        def capability(self, statistic, regime):
            if statistic is Statistic.DETECTOR_MARG and regime.R == 1:
                budget = int(self.safety * self.card_bytes) if self.card_bytes else 0
                need = 4 * self._dm_copy_bytes(regime.n_active)
                ok = budget > 0  # SABOTAGE: dropped "and need <= budget"
                return Capability(statistic, Exactness.EXACT, ok, "", "a", need)
            return super().capability(statistic, regime)

    full9_R1 = Regime(R=1, register="full", n_active=9, n_stab=8)

    def _oom_cell_infeasible(anchor):
        assert not anchor.capability(Statistic.DETECTOR_MARG, full9_R1).feasible

    assert_discriminates(_oom_cell_infeasible, real=DMOracleAnchor(card_bytes=_CARD32),
                         wrong=_NoBudgetGuardDM(card_bytes=_CARD32), label="DM need<=budget guard")


@settings(max_examples=60, deadline=None)
@given(n_active=st.integers(2, 8), n_stab=st.integers(1, 8), R=st.integers(1, 3),
       card_gb=st.sampled_from([0, 1, 8, 32, 96]), safety=st.floats(0.1, 0.9))
def test_dm_capability_feasibility_formula_property(n_active, n_stab, R, card_gb, safety):
    # L1: FULL_JOINT exists only at R=1. There its feasibility equals an INDEPENDENT recompute of
    # the OOM-as-data formula; at R>=2 record_oracle returns moments only, regardless of memory.
    card = card_gb * 1024 ** 3
    dm = DMOracleAnchor(card_bytes=card, safety=safety)
    cap = dm.capability(Statistic.FULL_JOINT, Regime(R=R, register="subregister",
                                                     n_active=n_active, n_stab=n_stab))
    copy = (3 ** n_active) ** 2 * 16
    budget = int(safety * card) if card else 0
    need = max(1, n_stab) * R * copy
    expected = R == 1 and budget > 0 and need <= budget
    assert cap.feasible == expected
    if R >= 2:
        assert "returns moments only" in cap.reason
        assert cap.mem_bytes_estimate is None
    elif cap.feasible:
        assert cap.mem_bytes_estimate == need  # the declared bound is the true copy-stack size


# =========================================================================== #
# L2 VALUE-PINNING pass -- every FIELD of every returned object pinned against  #
# an INDEPENDENT recompute, so a wrong constant / operator / index / None / a   #
# case-flipped reason string cannot survive (the mutation gate's teeth). The    #
# capability descriptors are pinned FULL-TUPLE + at the feasibility BOUNDARY.    #
# =========================================================================== #
def _cap_eq(cap, *, statistic, exactness, feasible, reason, cls, mem):
    """Pin EVERY field of a Capability against an independently-known value. ``is`` on the enum /
    bool fields (so a None-substitution mutant dies where ``not feasible`` would pass), exact ``==``
    on the reason string (so a case/XX/substring mutant dies) and the integer memory bound."""
    assert cap.statistic is statistic, f"statistic={cap.statistic!r}"
    assert cap.exactness is exactness, f"exactness={cap.exactness!r}"
    assert cap.feasible is feasible, f"feasible={cap.feasible!r} want {feasible!r}"
    assert cap.reason == reason, f"reason={cap.reason!r}\n  want {reason!r}"
    assert cap.epistemic_class == cls, f"class={cap.epistemic_class!r}"
    assert cap.mem_bytes_estimate == mem, f"mem={cap.mem_bytes_estimate!r} want {mem!r}"


def _copy_bytes(n: int) -> int:
    return (3 ** int(n)) ** 2 * 16  # a complex128 qutrit density matrix (INDEPENDENT recompute)


def _budget(card: int, safety: float) -> int:
    return int(safety * card) if card else 0


# --------------------------------------------------------------------------- #
# dm_oracle.DMOracleAnchor.capability -- full-tuple pins over EVERY branch      #
# --------------------------------------------------------------------------- #
def test_dm_capability_full_tuple_pins():
    S, EX = Statistic, Exactness.EXACT
    dm = DMOracleAnchor(card_bytes=_CARD32, safety=0.5, device="cpu")   # budget = 16 GB
    budget = _budget(_CARD32, 0.5)

    # (1) statistic NOT answered.
    _cap_eq(dm.capability(S.SCALAR_FUNC, Regime(R=1, n_active=3, n_stab=1)),
            statistic=S.SCALAR_FUNC, exactness=EX, feasible=False,
            reason="DM anchor does not answer this", cls="a", mem=None)

    # (2) DETECTOR_MARG, R != 1 -> moments-path reason (no mem bound).
    _cap_eq(dm.capability(S.DETECTOR_MARG, Regime(R=2, register="full", n_active=9, n_stab=8)),
            statistic=S.DETECTOR_MARG, exactness=EX, feasible=False,
            reason="R>=2 detector marginals need the moments path (RR_CORR), not single-stab projection",
            cls="a", mem=None)

    # (3) DETECTOR_MARG R=1 OOM (full-9q ~25GB > 16GB): the exact formatted reason + mem == 4*copy.
    need = 4 * _copy_bytes(9)
    _cap_eq(dm.capability(S.DETECTOR_MARG, Regime(R=1, register="full", n_active=9, n_stab=8)),
            statistic=S.DETECTOR_MARG, exactness=EX, feasible=False,
            reason=f"~{need/1e9:.0f}GB live > {budget/1e9:.0f}GB budget", cls="a", mem=need)

    # (4) DETECTOR_MARG R=1, budget == 0 (no CUDA) -> the no-budget reason; mem still == need.
    dm0 = DMOracleAnchor(card_bytes=0, device="cpu")
    need0 = 4 * _copy_bytes(3)
    _cap_eq(dm0.capability(S.DETECTOR_MARG, Regime(R=1, n_active=3, n_stab=2)),
            statistic=S.DETECTOR_MARG, exactness=EX, feasible=False,
            reason="no GPU budget known (card_bytes=0; the DM oracle needs CUDA)", cls="a", mem=need0)

    # (5) MOMENTS (RR_CORR / SPATIAL_CORR) R < 2.
    for stat in (S.RR_CORR, S.SPATIAL_CORR):
        _cap_eq(dm.capability(stat, Regime(R=1, register="full", n_active=9, n_stab=8)),
                statistic=stat, exactness=EX, feasible=False,
                reason="the moments (round-to-round / spatial detector correlation) need R>=2; at "
                       "R=1 there is no round-to-round or realized-distribution second moment",
                cls="a", mem=None)
        # (6) MOMENTS n_stab is None.
        _cap_eq(dm.capability(stat, Regime(R=2, register="subregister", n_active=3, n_stab=None)),
                statistic=stat, exactness=EX, feasible=False,
                reason="n_stab unknown for this regime — cannot bound the depth-(n_stab*R) clone "
                       "stack; refusing (a None n_stab under-counts depth to R and would falsely pass "
                       "the feasibility gate -> an OOM at answer time)", cls="a", mem=None)

    # (7) MOMENTS full-9q R=2 OOM (~99GB): depth-16 * 6.2GB > 16GB.
    depthM = max(1, 8) * 2
    needM = depthM * _copy_bytes(9)
    _cap_eq(dm.capability(S.RR_CORR, Regime(R=2, register="full", n_active=9, n_stab=8)),
            statistic=S.RR_CORR, exactness=EX, feasible=False,
            reason=f"depth-{depthM} x {_copy_bytes(9)/1e9:.1f}GB ~ {needM/1e9:.0f}GB > "
                   f"{budget/1e9:.0f}GB budget (route the scale to the carrier-MCWF; the DM moments "
                   f"GT lives on a small valid sub-code)", cls="a", mem=needM)
    # (8) MOMENTS budget == 0.
    _cap_eq(dm0.capability(S.RR_CORR, Regime(R=2, n_active=3, n_stab=2)),
            statistic=S.RR_CORR, exactness=EX, feasible=False,
            reason="no GPU budget known (card_bytes=0; the DM oracle needs CUDA)", cls="a",
            mem=max(1, 2) * 2 * _copy_bytes(3))

    # (9) FULL_JOINT / SYNDROME_DIST fail closed at R>=2 before any memory arithmetic.
    joint_unavailable = (
        "R>=2 QutritDM.record_oracle returns moments only; it cannot provide the full joint "
        "required by FULL_JOINT or SYNDROME_DIST"
    )
    for stat in (S.FULL_JOINT, S.SYNDROME_DIST):
        _cap_eq(dm.capability(stat, Regime(R=2, n_active=1, n_stab=1)),
                statistic=stat, exactness=EX, feasible=False, reason=joint_unavailable,
                cls="a", mem=None)

    # (10) FULL_JOINT / SYNDROME_DIST at R=1 with n_stab None.
    for stat in (S.FULL_JOINT, S.SYNDROME_DIST):
        _cap_eq(dm.capability(stat, Regime(R=1, n_active=3, n_stab=None)),
                statistic=stat, exactness=EX, feasible=False,
                reason="n_stab unknown for this regime — cannot bound the depth-(n_stab*R) "
                       "enumeration stack; refusing (a None n_stab under-counts depth and would "
                       "falsely pass the feasibility gate -> an OOM at answer time)", cls="a", mem=None)

    # (11) FULL_JOINT full-9q R=1 depth-8 OOM (~50GB).
    depthF = max(1, 8) * 1
    needF = depthF * _copy_bytes(9)
    _cap_eq(dm.capability(S.FULL_JOINT, Regime(R=1, register="full", n_active=9, n_stab=8)),
            statistic=S.FULL_JOINT, exactness=EX, feasible=False,
            reason=f"depth-{depthF} x {_copy_bytes(9)/1e9:.1f}GB ~ {needF/1e9:.0f}GB > "
                   f"{budget/1e9:.0f}GB budget (route the scale to the carrier-MCWF)",
            cls="a", mem=needF)
    # (12) FULL_JOINT budget == 0.
    _cap_eq(dm0.capability(S.FULL_JOINT, Regime(R=1, n_active=3, n_stab=1)),
            statistic=S.FULL_JOINT, exactness=EX, feasible=False,
            reason="no GPU budget known (card_bytes=0; the DM oracle needs CUDA)", cls="a",
            mem=max(1, 1) * 1 * _copy_bytes(3))


def test_dm_capability_feasibility_boundary():
    # The feasibility gate is `budget > 0 AND need <= budget`. Pin it at the EXACT boundary
    # (need == budget => feasible, mem == need) for EACH statistic x branch. This kills the
    # `need < budget` (off-by-one) mutant and the `max(2, n_stab)` depth mutant (n_stab=1 arm).
    S, EX = Statistic, Exactness.EXACT

    # DETECTOR_MARG R=1: need = 4*copy; safety=1.0, card=need => budget == need (feasible).
    needD = 4 * _copy_bytes(3)
    dmD = DMOracleAnchor(card_bytes=needD, safety=1.0, device="cpu")
    _cap_eq(dmD.capability(S.DETECTOR_MARG, Regime(R=1, n_active=3, n_stab=1)),
            statistic=S.DETECTOR_MARG, exactness=EX, feasible=True, reason="", cls="a", mem=needD)
    # one byte under budget -> infeasible (need == budget + 1) with the OOM reason.
    dmDm = DMOracleAnchor(card_bytes=needD - 1, safety=1.0, device="cpu")
    _cap_eq(dmDm.capability(S.DETECTOR_MARG, Regime(R=1, n_active=3, n_stab=1)),
            statistic=S.DETECTOR_MARG, exactness=EX, feasible=False,
            reason=f"~{needD/1e9:.0f}GB live > {(needD-1)/1e9:.0f}GB budget", cls="a", mem=needD)

    # MOMENTS n_stab=1 (exercises max(1,n_stab)): depth = max(1,1)*2 = 2, need = 2*copy.
    needM = max(1, 1) * 2 * _copy_bytes(3)
    dmM = DMOracleAnchor(card_bytes=needM, safety=1.0, device="cpu")
    _cap_eq(dmM.capability(S.RR_CORR, Regime(R=2, register="subregister", n_active=3, n_stab=1)),
            statistic=S.RR_CORR, exactness=EX, feasible=True, reason="", cls="a", mem=needM)

    # FULL_JOINT n_stab=1: depth = 1, need = copy.
    needF = max(1, 1) * 1 * _copy_bytes(3)
    dmF = DMOracleAnchor(card_bytes=needF, safety=1.0, device="cpu")
    _cap_eq(dmF.capability(S.FULL_JOINT, Regime(R=1, n_active=3, n_stab=1)),
            statistic=S.FULL_JOINT, exactness=EX, feasible=True, reason="", cls="a", mem=needF)


def test_dm_init_pins():
    # __init__ is not a canonical unit, but the CPU-reachable arcs are pinned: device wrapping and
    # the `int(card_bytes or 0)` (a `or 1` mutant makes card_bytes 0 -> 1). The torch.cuda
    # auto-detect branch stays GPU-only (untested here, per the registry).
    assert str(DMOracleAnchor(card_bytes=_CARD32, device="cpu").device) == "cpu"
    assert DMOracleAnchor(card_bytes=0, device="cpu").card_bytes == 0


# --------------------------------------------------------------------------- #
# closed_form.ClosedFormAnchor -- capability full-tuple + answer provenance     #
# --------------------------------------------------------------------------- #
def test_closed_capability_full_tuple_pins():
    S, EX = Statistic, Exactness.EXACT
    cf = ClosedFormAnchor(p01=0.08, p10=0.20, exact_single_qubit=True)
    cfd = ClosedFormAnchor(p01=0.08, p10=0.20)  # d3 -> STATISTICAL / class 'b'
    inf = "the closed form predicts RR_CORR at R>=2 only"

    # infeasible: not RR_CORR (mem is the literal 0, NOT None -> a trailing-arg mutant dies).
    _cap_eq(cf.capability(S.FULL_JOINT, Regime(R=2, n_stab=1)),
            statistic=S.FULL_JOINT, exactness=EX, feasible=False, reason=inf, cls="a", mem=0)
    # infeasible: RR_CORR but R < 2 (the guard).
    _cap_eq(cf.capability(S.RR_CORR, Regime(R=1, n_stab=1)),
            statistic=S.RR_CORR, exactness=EX, feasible=False, reason=inf, cls="a", mem=0)
    # feasible at the R == 2 BOUNDARY (kills the `R <= 2` / `R < 3` guard mutants).
    _cap_eq(cf.capability(S.RR_CORR, Regime(R=2, n_stab=1)),
            statistic=S.RR_CORR, exactness=EX, feasible=True, reason="", cls="a", mem=0)
    # feasible R >= 2, EXACT single-qubit / class 'a'.
    _cap_eq(cf.capability(S.RR_CORR, Regime(R=3, n_stab=1)),
            statistic=S.RR_CORR, exactness=EX, feasible=True, reason="", cls="a", mem=0)
    # feasible d3 -> STATISTICAL / class 'b' leg of the exness/cls ternaries.
    _cap_eq(cfd.capability(S.RR_CORR, Regime(R=3, n_stab=8)),
            statistic=S.RR_CORR, exactness=Exactness.STATISTICAL, feasible=True, reason="",
            cls="b", mem=0)


def test_closed_answer_field_and_provenance_pins():
    S = Statistic
    reg = Regime(R=6, n_stab=8)
    av = ClosedFormAnchor(p01=0.08, p10=0.20, exact_single_qubit=True).answer(None, S.RR_CORR, reg)
    assert av.statistic is S.RR_CORR
    assert av.regime is reg
    # the FULL provenance dict pinned (kills every key/value string mutant + the dropped-dict mutant).
    assert av.provenance == {"anchor": "closed_form_transient_markov", "p01": 0.08, "p10": 0.20, "a0": 0.08,
                             "exact_single_qubit": True, "transient": True}
    # the DEFAULT band_d3 (the __init__ default 0.02) -- a d3 anchor built without band_d3.
    assert ClosedFormAnchor(p01=0.08, p10=0.20).answer(None, S.RR_CORR, reg).band == pytest.approx(0.02)


def test_closed_exact_rr_extreme_variance_isolated_zero():
    # p01=1.0 makes d_0 DETERMINISTIC (var 0) while d_1 has variance -> the `var_r>1e-12 AND
    # var_r1>1e-12` guard MUST take the else-branch (append 0.0). An `or` mutant divides by ~0 and
    # returns nan/inf, breaking the pin vs the INDEPENDENT full 2^R path enumeration.
    a, b, R = 1.0, 0.3, 5
    cf = ClosedFormAnchor(p01=a, p10=b, exact_single_qubit=True)
    seq = cf._exact_rr_corr(R)
    assert seq[0] == 0.0  # d_0 deterministic under p01=1 -> zero-variance else-branch
    assert_pins(seq, _exact_rr_from_paths(a, b, R), atol=1e-12, label="_exact_rr_corr extreme p01=1")


# --------------------------------------------------------------------------- #
# stim_clifford.StimCliffordAnchor -- capability full-tuple + answer fields     #
# --------------------------------------------------------------------------- #
def test_stim_capability_full_tuple_pins():
    S, EXS = Statistic, Exactness.STATISTICAL
    st = StimCliffordAnchor(p_x=0.03)
    # not answered (mem default None, class 'b').
    _cap_eq(st.capability(S.RR_CORR, Regime(R=2, n_stab=8)),
            statistic=S.RR_CORR, exactness=EXS, feasible=False,
            reason="stim does not answer this", cls="b", mem=None)
    # answered -> feasible at any R, empty reason, mem the literal 0, class 'b'.
    for s in (S.SYNDROME_DIST, S.DETECTOR_MARG, S.FULL_JOINT):
        _cap_eq(st.capability(s, Regime(R=2, n_stab=8)),
                statistic=s, exactness=EXS, feasible=True, reason="", cls="b", mem=0)


def test_stim_answer_field_provenance_band_and_corrupt():
    S = Statistic
    p, N = 0.1, 60000
    reg = Regime(R=2, n_stab=1, n_active=2)
    st = StimCliffordAnchor(p_x=p, seed=4242)

    av = st.answer(_StimProcessFixture(), S.SYNDROME_DIST, reg, N=N)
    assert av.statistic is S.SYNDROME_DIST
    assert av.regime is reg
    assert av.provenance == {"anchor": "stim_clifford", "p_x": p, "corrupt_stab": None}
    # the DEFAULT-N band (N=200_000 in `int(N or 200_000)`) pins the 200_000 constant.
    assert st.answer(_StimProcessFixture(), S.SYNDROME_DIST, reg).band == pytest.approx(6.0 / math.sqrt(200_000))

    # DETECTOR_MARG at m=0 pinned against the closed form [q, q, flip]; then the CORRUPT answer
    # (stab0 Z<->X) is DISCRIMINATED: it drives the detectors deterministic (0) and the logical
    # anti-commuting (~0.5), a distribution the m=0 pin CANNOT satisfy -> the corrupt path fires.
    q = 2 * p * (1 - p)
    flip = (1 - (1 - 2 * p) ** reg.R) / 2
    dm = np.asarray(st.answer(_StimProcessFixture(), S.DETECTOR_MARG, reg, N=N).value)
    assert_pins(dm, np.array([q, q, flip]), atol=0.02, label="stim DETECTOR_MARG m0 vs closed form")
    dmc = np.asarray(st.answer(_StimProcessFixture(), S.DETECTOR_MARG, reg, N=N, corrupt={"stab": 0}).value)
    assert_pins(dmc, np.array([0.0, 0.0, 0.5]), atol=0.03, label="stim DETECTOR_MARG corrupt (XX)")


# --------------------------------------------------------------------------- #
# controls -- the FULL CONTROL ledger row pinned on every arc                   #
# --------------------------------------------------------------------------- #
def test_corrupt_run_full_row_pins():
    S = Statistic
    rep_fire = certify_cells(ControlledProcessFixture(_JOINT), [(S.FULL_JOINT, _REG)],
                             [InMemoryAnchor(_JOINT, corruptible=True)], [CorruptStabControl(stab=0)],
                             N=20000)
    row = rep_fire.controls[0]
    assert row.anchor == "in_memory"
    assert row.statistic is S.FULL_JOINT
    assert row.value == 1.0
    assert row.band is None
    assert row.epistemic_class == "c"
    assert row.verdict is Verdict.CONTROL
    assert row.detail == {"fired": True, "applicable": True, "name": "corrupt_stabilizer", "stab": 0}

    rep_inert = certify_cells(ControlledProcessFixture(_JOINT), [(S.FULL_JOINT, _REG)],
                              [InMemoryAnchor(_JOINT, corruptible=False)], [CorruptStabControl(stab=0)],
                              N=20000)
    r2 = rep_inert.controls[0]
    assert r2.value == 0.0                       # the else-arc of `1.0 if fired else 0.0`
    assert r2.detail["fired"] is False and r2.detail["applicable"] is True

    # DEFAULT stab (the __init__ default is 1) -> detail carries stab == 1 (a None / default mutant dies).
    rep_def = certify_cells(ControlledProcessFixture(_JOINT), [(S.FULL_JOINT, _REG)],
                            [InMemoryAnchor(_JOINT, corruptible=True)], [CorruptStabControl()], N=20000)
    assert rep_def.controls[0].detail["stab"] == 1


def test_shuffle_run_full_row_pins():
    S = Statistic
    ctrl = ShuffleControl()
    # applicable + fired.
    row = ctrl.run(_shuffle_ctx(dict(_JOINT), dict(_JOINT), S.FULL_JOINT), S.FULL_JOINT, _REG, N=20000)
    assert row.anchor == "stub"
    assert row.statistic is S.FULL_JOINT
    assert row.value == 1.0
    assert row.band is None
    assert row.epistemic_class == "c"
    assert row.verdict is Verdict.CONTROL
    assert row.detail == {"fired": True, "applicable": True, "name": "shuffle"}

    # inapplicable (flat/symmetric value) -> the early return row.
    rowf = ctrl.run(_shuffle_ctx(dict(_FLAT), dict(_FLAT), S.FULL_JOINT), S.FULL_JOINT, _REG, N=20000)
    assert rowf.anchor == "stub"
    assert rowf.statistic is S.FULL_JOINT
    assert rowf.value == 0.0
    assert rowf.epistemic_class == "c"
    assert rowf.verdict is Verdict.CONTROL
    assert rowf.detail == {"fired": False, "applicable": False, "name": "shuffle",
                           "reason": "shuffle is ~identity on this symmetric/flat value"}

    # applicable but NOT fired (emitted already == the rolled GT) -> the else-arc value 0.0. This is
    # the ONLY arc that distinguishes `1.0 if fired else 0.0` from `1.0 if fired else 1.0`.
    rolled = {0: 0.1, 1: 0.05, 2: 0.45, 3: 0.4}   # _shuffle_value(_JOINT): roll values by (i+1)%len
    rown = ctrl.run(_shuffle_ctx(dict(_JOINT), rolled, S.FULL_JOINT), S.FULL_JOINT, _REG, N=20000)
    assert rown.value == 0.0
    assert rown.detail == {"fired": False, "applicable": True, "name": "shuffle"}


def test_corrupt_init_stab_stored():
    # __init__ stores int(stab); a `self._stab = None` mutant is caught via the run detail.
    rep = certify_cells(ControlledProcessFixture(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [InMemoryAnchor(_JOINT, corruptible=True)], [CorruptStabControl(stab=0)], N=20000)
    assert rep.controls[0].detail["stab"] == 0


def test_value_close_default_boundary_and_setop_pins():
    # dict branch: the missing-key default is 0.0 (a None / 1.0 / dropped default all change the answer
    # or raise), the set combiner is UNION (& would drop the differing key), and the tolerance is
    # inclusive `<= tol` (a `< tol` mutant rejects an exactly-tol pair). All pinned independently.
    assert _value_close({0: 0.5}, {0: 0.5, 1: 0.9}) is False        # union sees k=1 (|0-0.9|>tol)
    assert _value_close({0: 0.5, 1: 0.9}, {0: 0.5}) is False        # symmetric (b missing key)
    assert _value_close({0: 0.5}, {0: 0.5, 1: 1.0}) is False        # a.get default MUST be 0.0, not 1.0
    assert _value_close({0: 0.5, 1: 1.0}, {0: 0.5}) is False        # b.get default MUST be 0.0, not 1.0
    assert _value_close({0: 0.0}, {0: 1e-12}) is True               # exactly tol apart -> inclusive close
    # array branch: the inclusive tolerance again (a `< tol` mutant rejects the exactly-tol pair).
    assert _value_close(np.array([0.0]), np.array([1e-12])) is True


def test_shuffle_value_dict_roll_direction():
    # the dict branch rolls values by (i+1)%len -> a NON-symmetric dict distinguishes +1 from -1/+2.
    av = AnchorValue(Statistic.FULL_JOINT, _REG, {0: 1.0, 1: 2.0, 2: 3.0}, Exactness.EXACT, 0.0, "a", {})
    assert _shuffle_value(av).value == {0: 2.0, 1: 3.0, 2: 1.0}

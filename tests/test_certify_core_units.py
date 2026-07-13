"""Stage-D batch D4 -- per-unit L0 + L1 + KILLER coverage of the ``certify`` engine trio
``error_coupling_simulator.certify.{core, facade, types}`` (25 CPU-coverable public units).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4; work-list
docs/twin_validation/l3_release_package_unit_inventory.md). The three modules are the certify
STATISTICAL BACKBONE + the value types + the ``certify_teacher`` facade. ``core``/``types`` are
torch-free; ``facade`` imports torch TRANSITIVELY (via ``.anchors`` -> ``dm_oracle``) but never
touches a GPU on the paths exercised here (``DMOracleAnchor(device="cuda")`` only builds a
``torch.device`` object and reads ``torch.cuda.is_available()`` -> False on a CPU box -> card
budget 0 -> the DM leg is infeasible-as-data, so ``answer`` -- the only GPU path -- is never
reached). So all 25 units are covered CPU-ONLY.

The three "Mixed" units that normally drive a GPU teacher/anchor (``certify_cells``,
``certify_teacher``, ``MeasureCtx.corrupt_answer`` -- and ``MeasureCtx.score``) are covered with the
same TEST-ONLY in-memory stub pattern the existing ``tests/test_certify.py`` uses (``FakeTeacher`` /
``InMemoryAnchor``): a hand-written known law that shares no code with any engine, so the port IS the
test surface, on CPU, with NO GPU.

BRANCH SURFACE (coverage.py --branch facts confirmed by probe before authoring):
  * single-line ternaries (``a if c else b`` on ONE source line) emit NO tracked branch arc -- so
    ``compare``'s six single-line ternaries, ``MeasureCtx.score``'s two, and ``emitted_statistic``'s
    ``... if R>1 else [0.0]`` are branch-0 surface; their faithfulness rests on the VALUE pin + the
    KILLER, not a branch count. ``compare``'s ONLY tracked branches are the two multi-line ``if``s
    (``in _DIST_STATS`` / ``is SCALAR_FUNC``);
  * generator/comprehension bodies emit NO tracked branch arc (the observables-batch fact) -- so the
    ``certify_cells`` ``n_fired`` genexp, the ``certify_teacher`` ``feasible``/``check_list`` list-
    comps + ``routing`` dict-comp, and ``route``'s ``cands`` listcomp are branch-0 surface;
  * real multi-line ``if``/``for`` DO create arcs -- so ``emitted_statistic``'s stat dispatch chain +
    the RR/SPATIAL ``for`` loops, ``reduce_*``'s guards, ``certify_cells``'s cell/control loops +
    ``anchor is None`` + ``ctrl.guards``, and ``certify_teacher``'s policy ``if``s are each exercised
    on BOTH arcs;
  * the 15 ``types`` Protocol/CertReport methods: the Protocol ``...``-stub bodies + the enum/
    dataclass shells are covered by IMPORT (coverage.py does not count a ``...``/docstring stub as a
    statement); only ``CertReport.row``/``summary``/``assert_pass`` carry real bodies + branches.

KILLER (feedback-devious-tests-killer-standard). Every load-bearing assert is DISCRIMINATING via the
faithfulness API: ``assert_pins`` pins the VALUE against an INDEPENDENT from-scratch recompute (numpy
``corrcoef`` for the correlations; a per-row Counter for the joint; ``0.5*sum|p-q|`` for TV), and
``assert_discriminates`` proves the named sabotage FAILS the property (drop the FULL_JOINT obs shift;
drop ``np.abs`` in reduce_rr_corr; include the diagonal in reduce_spatial_corr; drop the TV 0.5;
force PASS in compare; flip route's exactness key; return 0.0 in score; return the answer unchanged in
corrupt_answer; skip the control loop so an inert control cannot force FAIL; merge only the first
anchor's rows; drop the ``and r.statistic==`` in CertReport.row; widen assert_pass to accept FAIL).
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from _support import faithfulness as F
from error_coupling_simulator.certify.core import (
    MeasureCtx,
    _rollup,
    certify_cells,
    compare,
    emitted_statistic,
    reduce_rr_corr,
    reduce_spatial_corr,
    route,
    total_variation,
)
from error_coupling_simulator.certify.facade import certify_teacher
from error_coupling_simulator.certify.types import (
    Anchor,
    AnchorValue,
    Capability,
    CertReport,
    CliffordSliceable,
    Control,
    ControlledNoiseProcess,
    DMReplayable,
    Exactness,
    Feasibility,
    LedgerRow,
    Regime,
    Statistic,
    Verdict,
)

_REG = Regime(R=1, register="subregister", n_active=1, n_stab=1)
_JOINT = {0: 0.4, 1: 0.1, 2: 0.05, 3: 0.45}


def _rk(regime) -> tuple:
    """INDEPENDENT recompute of ``core._rkey`` (NOT the SUT helper): the routing-key coordinates."""
    return (regime.R, regime.register, regime.n_active, regime.arm, regime.b)


def _routekey(statistic, regime) -> tuple:
    """INDEPENDENT recompute of ``certify_cells``'s per-cell routing key ``(stat.value, _rkey)``."""
    return (statistic.value, _rk(regime))


# --------------------------------------------------------------------------- #
# TEST-ONLY fixtures (in tests/, structurally never production anchors)       #
# --------------------------------------------------------------------------- #
def _make_records(joint: dict, N: int) -> dict:
    """Deterministic (det, obs) realizing ``joint`` (key = det + (flip<<1) for a 1-stab R=1
    surface), so ``emitted_statistic`` recovers the dist exactly (no flake). Mirrors the fixture in
    tests/test_certify.py."""
    keys = list(joint)
    counts = [int(round(joint[k] * N)) for k in keys]
    counts[0] += N - sum(counts)
    det = np.concatenate([np.full(c, k & 1, np.uint8) for k, c in zip(keys, counts)]).reshape(N, 1)
    obs = np.concatenate([np.full(c, (k >> 1) & 1, np.uint8) for k, c in zip(keys, counts)])
    return {"det": det, "obs": obs}


class FakeTeacher:
    """A controlled teacher emitting a KNOWN law (test fixture). ``sched`` is a namespace so the
    facade's ``_regime`` can read ``n_data`` / ``stabilizers``; the core never touches it."""

    truth = {"theta": 0.15, "gamma": 0.04}

    def __init__(self, joint: dict, *, sched=None):
        self._joint = joint
        self.sched = sched if sched is not None else object()

    def emit(self, regime, *, m, N, seed):
        return _make_records(self._joint, N)

    def emit_clifford_slice(self, regime, *, p_x, m, N, seed):
        return _make_records(self._joint, N)

    def channels(self):
        return None


class MemAnchor:
    """TEST FIXTURE -- a hand-written known law that shares no code with any engine (the port IS the
    test surface). Answers FULL_JOINT / SYNDROME_DIST from the joint; hosts the ``{"stab": j}``
    corruption. Parametrized ``answers_set`` / ``emit_kind_val`` / ``feasible`` / ``exactness`` drive
    the routing + emit-leg cases."""

    independence = "hand-written known law (TEST fixture; shares no code with any engine)"

    def __init__(self, joint: dict, *, name: str = "mem", feasible: bool = True,
                 exactness=Exactness.EXACT, answers_set=None, emit_kind_val: str = "full",
                 mem: int = 0):
        self._joint = joint
        self.name = name
        self._feasible = feasible
        self._exactness = exactness
        self._answers = frozenset(answers_set or {Statistic.FULL_JOINT, Statistic.SYNDROME_DIST})
        self._emit_kind = emit_kind_val
        self._mem = mem
        self.p_x = 0.03

    def answers(self):
        return frozenset(self._answers)

    def emit_kind(self):
        return self._emit_kind

    def capability(self, statistic, regime):
        # the port contract: the core NEVER asks capability with a None statistic/regime -- so a
        # certify_cells / route mutant that drops one to None is caught here (mut route(None,...)).
        assert statistic is not None, "capability received statistic=None"
        assert regime is not None, "capability received regime=None"
        cls = "a" if self._exactness is Exactness.EXACT else "b"
        return Capability(statistic, self._exactness, feasible=self._feasible,
                          epistemic_class=cls, mem_bytes_estimate=self._mem)

    def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
        if statistic is Statistic.SYNDROME_DIST:
            val: dict = {}
            for k, p in self._joint.items():
                val[k & 1] = val.get(k & 1, 0.0) + p
        else:
            val = dict(self._joint)
        if corrupt and "stab" in corrupt:
            u = 1.0 / len(val)  # uniform corruption -> differs from the true law -> control fires
            val = {k: u for k in val}
        cls = "a" if self._exactness is Exactness.EXACT else "b"
        band = 0.0 if self._exactness is Exactness.EXACT else 0.01
        return AnchorValue(statistic, regime, val, self._exactness, band, cls,
                           provenance={"anchor": self.name})


class RRStub:
    """A minimal EXACT anchor answering RR_CORR (value ``[0.0]``) -- drives the ``RR_CORR R==1``
    emitted leg through ``certify_cells``."""

    name = "rr"
    independence = "test"
    p_x = 0.03

    def answers(self):
        return frozenset({Statistic.RR_CORR})

    def emit_kind(self):
        return "full"

    def capability(self, statistic, regime):
        return Capability(statistic, Exactness.EXACT, True, "", "a", 0)

    def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
        return AnchorValue(statistic, regime, np.array([0.0]), Exactness.EXACT, 0.0, "a",
                           {"anchor": self.name})


class ShuffleCtrl:
    """A generic teeth control: shuffle the GROUND-TRUTH dict value -> the emitted must FAIL to match
    -> the control FIRES (fired=True)."""

    name = "shuffle_label"

    def __init__(self, guard_stats=(Statistic.FULL_JOINT, Statistic.SYNDROME_DIST)):
        self._guards = tuple(guard_stats)

    def guards(self, statistic):
        return statistic in self._guards

    def expect(self):
        return "must_fail"

    def run(self, ctx, statistic, regime, *, N=None):
        av = ctx.anchor_value
        keys = sorted(av.value)
        vals = [av.value[k] for k in keys]
        rolled = {k: vals[(i + 1) % len(vals)] for i, k in enumerate(keys)}
        _, _, verdict, _ = compare(statistic, ctx.emitted, replace(av, value=rolled), N=ctx.N)
        fired = verdict is Verdict.FAIL
        return LedgerRow(ctx.anchor.name, statistic, 1.0 if fired else 0.0, None, "c",
                         Verdict.CONTROL, {"fired": fired, "applicable": True, "name": self.name})


class InertCtrl(ShuffleCtrl):
    """A deliberately broken control: it compares the emitted against the UNCHANGED ground truth
    (identity perturbation), so it can NEVER fire. The core must turn this into a FAIL."""

    name = "inert"

    def run(self, ctx, statistic, regime, *, N=None):
        _, _, verdict, _ = compare(statistic, ctx.emitted, ctx.anchor_value, N=ctx.N)
        fired = verdict is Verdict.FAIL  # False (the emitted matches) -> the control is inert
        return LedgerRow(ctx.anchor.name, statistic, 1.0 if fired else 0.0, None, "c",
                         Verdict.CONTROL, {"fired": fired, "applicable": True, "name": self.name})


class NonGuardingCtrl:
    """A control that guards NOTHING -> the ``ctrl.guards(statistic)`` False arc; it is never run."""

    name = "nonguarding"

    def guards(self, statistic):
        return False

    def expect(self):
        return "must_fail"

    def run(self, ctx, statistic, regime, *, N=None):
        raise AssertionError("a non-guarding control must not be run")


class RouteStub:
    """A capability-only anchor for the ``route`` unit (answer must never be called)."""

    independence = "test"

    def __init__(self, *, name, answers_set, feasible, exactness, mem=0):
        self.name = name
        self._answers = frozenset(answers_set)
        self._feasible = feasible
        self._exactness = exactness
        self._mem = mem

    def answers(self):
        return frozenset(self._answers)

    def capability(self, statistic, regime):
        # route must pass the REAL (statistic, regime) to every capability probe (filter AND sort key)
        # -- a mutant that swaps one to None is caught here.
        assert statistic is not None, "route passed statistic=None to capability"
        assert regime is not None, "route passed regime=None to capability"
        cls = "a" if self._exactness is Exactness.EXACT else "b"
        return Capability(statistic, self._exactness, self._feasible, "", cls, self._mem)

    def answer(self, *a, **k):  # pragma: no cover - route must never call answer
        raise AssertionError("route must not call answer")


class RecordingMemAnchor(MemAnchor):
    """A MemAnchor that RECORDS every ``capability`` / ``answer`` call so a test can pin the EXACT
    argument tuple the core forwarded (kills the drop-an-arg-to-None mutants: teacher/statistic/
    regime/N/corrupt on ``answer``; statistic/regime on ``capability``)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.answer_calls: list = []
        self.capability_calls: list = []

    def capability(self, statistic, regime):
        self.capability_calls.append((statistic, regime))
        return super().capability(statistic, regime)

    def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
        self.answer_calls.append((teacher, statistic, regime, N, corrupt))
        return super().answer(teacher, statistic, regime, N=N, corrupt=corrupt)


class RecordingTeacher(FakeTeacher):
    """A FakeTeacher that records the args of ``emit`` / ``emit_clifford_slice`` (kills the
    certify_cells mutants that drop regime/p_x/m/N/seed to None on the two emit legs)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.emit_args: list = []
        self.clifford_args: list = []

    def emit(self, regime, *, m, N, seed):
        self.emit_args.append((regime, m, N, seed))
        return super().emit(regime, m=m, N=N, seed=seed)

    def emit_clifford_slice(self, regime, *, p_x, m, N, seed):
        self.clifford_args.append((regime, p_x, m, N, seed))
        return super().emit_clifford_slice(regime, p_x=p_x, m=m, N=N, seed=seed)


class CountingTeacher2(FakeTeacher):
    """Counts ``emit`` calls (for the cache-key perf invariant across DISTINCT regimes)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.emit_calls = 0

    def emit(self, regime, *, m, N, seed):
        self.emit_calls += 1
        return super().emit(regime, m=m, N=N, seed=seed)


class ScoringCtrl:
    """A teeth control that exercises the FULL ``MeasureCtx`` surface a real corrupt-stab control
    uses: ``ctx.score()`` (reads ctx.statistic/emitted/anchor_value), ``ctx.corrupt_answer`` (reads
    ctx.anchor/teacher/statistic/regime/N), and ``ctx.N`` (a sqrt threshold). It also records its
    OWN run(...) params so a mutant that drops regime/N on ``ctrl.run(...)`` is caught."""

    name = "scoring"
    seen_run = None

    def guards(self, statistic):
        return statistic in (Statistic.FULL_JOINT, Statistic.SYNDROME_DIST)

    def expect(self):
        return "must_fail"

    def run(self, ctx, statistic, regime, *, N=None):
        ScoringCtrl.seen_run = (statistic, regime, N)
        base = ctx.score()                                  # ctx.statistic/emitted/anchor_value/N
        corrupted = ctx.corrupt_answer({"stab": 1})         # ctx.anchor/teacher/statistic/regime/N
        pert = ctx.score(anchor_value=corrupted)
        thr = 6.0 / np.sqrt(ctx.N)                          # reads ctx.N (kills ctx.N=None)
        fired = bool(pert > thr and pert > base)
        return LedgerRow(ctx.anchor.name, statistic, pert, None, "c", Verdict.CONTROL,
                         {"fired": fired, "applicable": True, "name": self.name})


class NoEmitKindAnchor:
    """An anchor WITHOUT an ``emit_kind`` method -> the core's ``hasattr(...) else "full"`` default is
    taken (kills the mutated default literal ``"XXfullXX"`` / ``"FULL"``, which would raise)."""

    name = "noek"
    independence = "test"
    p_x = 0.03

    def __init__(self, joint):
        self._joint = joint

    def answers(self):
        return frozenset({Statistic.FULL_JOINT})

    def capability(self, statistic, regime):
        assert statistic is not None and regime is not None
        return Capability(statistic, Exactness.EXACT, True, "", "a", 0)

    def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
        val = dict(self._joint)
        if corrupt and "stab" in corrupt:
            u = 1.0 / len(val)
            val = {k: u for k in val}
        return AnchorValue(statistic, regime, val, Exactness.EXACT, 0.0, "a", {"anchor": self.name})


class RegimeGatedAnchor(MemAnchor):
    """Feasible EVERYWHERE except the full-9q R>=2 OOM corner -> lets one cell be UNANCHORED while a
    later cell PASSES (kills the ``continue`` -> ``break`` mutant: the loop must keep going)."""

    def capability(self, statistic, regime):
        assert statistic is not None and regime is not None
        feas = not (regime.register == "full" and regime.n_active >= 9 and regime.R >= 2)
        return Capability(statistic, Exactness.EXACT, feasible=feas, epistemic_class="a",
                          mem_bytes_estimate=0)


class FixedCtrl:
    """A control returning a HAND-SET ``detail`` -- drives the _rollup / n_fired applicable/fired
    lookup edges (missing keys, inapplicable-but-fired, etc.) with a known control row."""

    def __init__(self, name, detail, guard=(Statistic.FULL_JOINT,)):
        self.name = name
        self._detail = detail
        self._guard = tuple(guard)

    def guards(self, statistic):
        return statistic in self._guard

    def expect(self):
        return "must_fail"

    def run(self, ctx, statistic, regime, *, N=None):
        return LedgerRow(ctx.anchor.name, statistic, 1.0, None, "c", Verdict.CONTROL, dict(self._detail))


class RegimeRecAnchor:
    """Records the ``Regime`` the facade's ``_regime`` (plan branch) constructed -> pins every field
    of that Regime (kills the _regime R/register/n_active/n_stab/arm/b mutants)."""

    name = "regrec"
    independence = "test"
    p_x = 0.03
    seen = None

    def answers(self):
        return frozenset({Statistic.DETECTOR_MARG})

    def emit_kind(self):
        return "full"

    def capability(self, statistic, regime):
        RegimeRecAnchor.seen = regime
        return Capability(statistic, Exactness.EXACT, True, "", "a", 0)

    def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
        return AnchorValue(statistic, regime, np.array([0.0, 0.0]), Exactness.EXACT, 0.0, "a",
                           {"anchor": self.name})


# =========================================================================== #
# core.emitted_statistic -- every statistic leg + the NotImplementedError guard #
# =========================================================================== #
def test_emitted_full_joint_pins_and_obs_shift_killer():
    det = np.array([[1], [1], [0]], np.uint8)
    obs = np.array([0, 1, 0], np.uint8)
    got = emitted_statistic({"det": det, "obs": obs}, Statistic.FULL_JOINT, _REG)

    # INDEPENDENT from-scratch: per-row (det, flip) key via a Counter (not the impl's matmul).
    cnt = Counter(int(det[i, 0]) + (int(obs[i]) << 1) for i in range(len(obs)))
    expected = {k: v / len(obs) for k, v in cnt.items()}     # {1: 1/3, 3: 1/3, 0: 1/3}
    F.assert_pins(got, expected, label="FULL_JOINT vs per-row Counter")
    assert set(got) == {0, 1, 3}                              # the obs shift kept det=1 keys SEPARATE

    # KILLER (drop the "<<bits" obs shift -> det=1 rows MERGE, dropping key 3).
    wrong_keys = Counter(int(det[i, 0]) for i in range(len(obs)))
    wrong = {k: v / len(obs) for k, v in wrong_keys.items()}  # {1: 2/3, 0: 1/3}

    def prop_fj(d):
        F.assert_pins(d, expected, label="FULL_JOINT must equal the with-shift dist")

    F.assert_discriminates(prop_fj, got, wrong, label="FULL_JOINT obs shift")


def test_emitted_syndrome_dist_pins_and_no_obs_shift():
    det = np.array([[1], [0], [1], [1]], np.uint8)
    obs = np.array([1, 1, 0, 1], np.uint8)   # nonzero obs -- SYNDROME must IGNORE it
    got = emitted_statistic({"det": det, "obs": obs}, Statistic.SYNDROME_DIST, _REG)

    cnt = Counter(int(d[0]) for d in det)     # from-scratch: det-only marginal
    expected = {k: v / len(det) for k, v in cnt.items()}     # {1: 3/4, 0: 1/4}
    F.assert_pins(got, expected, label="SYNDROME_DIST vs det-only Counter")

    # KILLER: a FULL_JOINT-style key (with the obs shift) would split det=1 by obs -> DIFFERENT keys.
    wrong = {k: v / len(det)
             for k, v in Counter(int(det[i, 0]) + (int(obs[i]) << 1) for i in range(len(det))).items()}

    def prop_sd(d):
        F.assert_pins(d, expected, label="SYNDROME_DIST must be the det-only marginal")

    F.assert_discriminates(prop_sd, got, wrong, label="SYNDROME_DIST ignores obs")


def test_emitted_detector_marg_pins():
    det = np.array([[1, 0], [1, 1], [0, 1], [1, 0]], np.uint8)
    obs = np.array([0, 1, 0, 1], np.uint8)
    reg2 = Regime(R=1, register="subregister", n_active=2, n_stab=2)
    got = emitted_statistic({"det": det, "obs": obs}, Statistic.DETECTOR_MARG, reg2)

    # INDEPENDENT: per-column on-rate by explicit summation + the flip rate appended.
    expected = np.array([np.sum(det[:, j]) / len(det) for j in range(det.shape[1])]
                        + [np.sum(obs) / len(obs)])           # [0.75, 0.5, 0.5]
    F.assert_pins(got, expected, label="DETECTOR_MARG vs explicit column on-rates")

    def prop_dm(v):
        F.assert_pins(v, expected, label="DETECTOR_MARG must be per-detector on-rate + flip rate")

    wrong = expected.copy()
    wrong[-1] = 0.0                                            # a sabotage that drops the flip rate
    F.assert_discriminates(prop_dm, got, wrong, label="DETECTOR_MARG includes the flip rate")


def test_emitted_rr_corr_r2_pins_via_corrcoef_and_r1_edge():
    rng = np.random.default_rng(7)
    n = 4000
    d0 = (rng.random(n) < 0.3).astype(np.uint8)
    d1 = (d0 ^ (rng.random(n) < 0.25)).astype(np.uint8)       # round 1 correlated with round 0
    det = np.stack([d0, d1], axis=1)                          # (n, 2): R=2, n_stab=1, round-major
    reg_rr = Regime(R=2, register="subregister", n_active=1, n_stab=1)
    got = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.RR_CORR, reg_rr)
    assert got.shape == (1,)                                  # length R-1

    from_scratch = np.array([abs(np.corrcoef(d0.astype(float), d1.astype(float))[0, 1])])
    F.assert_pins(got, from_scratch, atol=1e-9, label="RR_CORR R=2 vs numpy corrcoef")

    # R==1 else-arc: no round-to-round -> exactly [0.0] (mutation teeth for the ``if R>1`` ternary).
    det1 = np.array([[1], [0], [1]], np.uint8)
    got1 = emitted_statistic({"det": det1, "obs": np.zeros(3, np.uint8)}, Statistic.RR_CORR,
                             Regime(R=1, n_stab=1))
    F.assert_pins(got1, np.array([0.0]), label="RR_CORR R=1 edge")
    assert got1.shape == (1,)


def test_emitted_spatial_corr_pins_via_corrcoef():
    rng = np.random.default_rng(8)
    n = 5000
    s0 = (rng.random(n) < 0.3).astype(np.uint8)
    s1 = (s0 ^ (rng.random(n) < 0.1)).astype(np.uint8)        # same-round correlated pair
    det = np.stack([s0, s1], axis=1)                          # (n, 2): R=1, n_stab=2
    reg_sp = Regime(R=1, register="subregister", n_active=2, n_stab=2)
    got = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.SPATIAL_CORR, reg_sp)
    assert got.shape == (1,)                                  # per-round, length R

    # from-scratch: the single off-diagonal 2x2 pair -> |corr(s0, s1)|.
    from_scratch = np.array([abs(np.corrcoef(s0.astype(float), s1.astype(float))[0, 1])])
    F.assert_pins(got, from_scratch, atol=1e-9, label="SPATIAL_CORR vs numpy corrcoef")


def test_emitted_statistic_notimplemented_guard():
    reg2 = Regime(R=1, register="subregister", n_active=2, n_stab=2)
    with pytest.raises(NotImplementedError, match="arrives with its anchor adapter"):
        emitted_statistic({"det": np.zeros((3, 2), np.uint8), "obs": np.zeros(3, np.uint8)},
                          Statistic.FLOOR, reg2)


def test_emitted_full_joint_multicol_weights_killer():
    # 2-column det -> the little-endian weights [1, 2] MATTER (>> would give [1, 0], dropping col 1).
    det = np.array([[0, 0], [1, 0], [0, 1], [1, 1], [1, 1]], np.uint8)
    obs = np.array([0, 0, 0, 0, 1], np.uint8)
    reg2 = Regime(R=1, register="subregister", n_active=2, n_stab=2)
    got = emitted_statistic({"det": det, "obs": obs}, Statistic.FULL_JOINT, reg2)
    # INDEPENDENT: key = det[:,0]*1 + det[:,1]*2 + obs*4 (bits=2, obs shifted by 2).
    cnt = Counter(int(det[i, 0]) + (int(det[i, 1]) << 1) + (int(obs[i]) << 2) for i in range(len(obs)))
    expected = {k: v / len(obs) for k, v in cnt.items()}      # {0,1,2,3,7} each 0.2
    F.assert_pins(got, expected, label="FULL_JOINT 2-col little-endian weights")

    # KILLER (>> weights -> col 1 (weight 2) collapses -> a different, degenerate dist).
    wrong = {k: v / len(obs)
             for k, v in Counter(int(det[i, 0]) + (int(obs[i]) << 2) for i in range(len(obs))).items()}

    def prop_w(d):
        F.assert_pins(d, expected, label="FULL_JOINT must use the little-endian detector weights")

    F.assert_discriminates(prop_w, got, wrong, label="FULL_JOINT weights direction")


def test_emitted_syndrome_multicol_weights_killer():
    det = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], np.uint8)
    obs = np.array([1, 1, 1, 1], np.uint8)   # nonzero but SYNDROME ignores it
    reg2 = Regime(R=1, register="subregister", n_active=2, n_stab=2)
    got = emitted_statistic({"det": det, "obs": obs}, Statistic.SYNDROME_DIST, reg2)
    cnt = Counter(int(det[i, 0]) + (int(det[i, 1]) << 1) for i in range(len(det)))
    expected = {k: v / len(det) for k, v in cnt.items()}       # {0,1,2,3} each 0.25
    F.assert_pins(got, expected, label="SYNDROME_DIST 2-col little-endian weights")

    wrong = {k: v / len(det) for k, v in Counter(int(det[i, 0]) for i in range(len(det))).items()}

    def prop_w(d):
        F.assert_pins(d, expected, label="SYNDROME_DIST must use the little-endian detector weights")

    F.assert_discriminates(prop_w, got, wrong, label="SYNDROME_DIST weights direction")


def test_emitted_rr_corr_r1_nstab_none_fallback():
    # regime.n_stab=None -> the ``regime.n_stab or (det.shape[1] // max(R, 1))`` fallback fires.
    # width=2, R=1 -> fallback n_stab = 2 // max(1, 1) = 2 -> reshape (n, 1, 2); R==1 -> [0.0].
    n = 60
    det = np.stack([(np.arange(n) % 2).astype(np.uint8), (np.arange(n) % 3 == 0).astype(np.uint8)],
                   axis=1)
    got = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.RR_CORR,
                            Regime(R=1, n_stab=None))
    assert got.shape == (1,)
    F.assert_pins(got, np.array([0.0]), label="RR_CORR R=1 n_stab=None fallback -> [0.0]")


def test_emitted_spatial_corr_r1_nstab_none_fallback():
    # SPATIAL n_stab=None fallback: width=2, R=1 -> fallback n_stab=2 -> reshape (n,1,2) -> off-diag.
    rng = np.random.default_rng(11)
    n = 4000
    s0 = (rng.random(n) < 0.3).astype(np.uint8)
    s1 = (s0 ^ (rng.random(n) < 0.15)).astype(np.uint8)
    det = np.stack([s0, s1], axis=1)
    got = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.SPATIAL_CORR,
                            Regime(R=1, n_stab=None))
    assert got.shape == (1,)
    fs = np.array([abs(np.corrcoef(s0.astype(float), s1.astype(float))[0, 1])])
    F.assert_pins(got, fs, atol=1e-9, label="SPATIAL_CORR R=1 n_stab=None fallback vs corrcoef")


def test_emitted_rr_corr_r3_per_round_pins():
    # R=3 -> the per-round sequence has length 2, and the r+1 (not r-1) neighbour matters.
    rng = np.random.default_rng(3)
    n = 8000
    d0 = (rng.random(n) < 0.3).astype(np.uint8)
    d1 = (d0 ^ (rng.random(n) < 0.1)).astype(np.uint8)        # high corr(d0, d1)
    d2 = (d1 ^ (rng.random(n) < 0.4)).astype(np.uint8)        # lower corr(d1, d2)
    det = np.stack([d0, d1, d2], axis=1)                      # (n, 3): R=3, n_stab=1
    reg = Regime(R=3, register="subregister", n_active=1, n_stab=1)
    got = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.RR_CORR, reg)
    assert got.shape == (2,)                                  # length R-1; a (R-2)-row rr2d would raise
    c01 = abs(np.corrcoef(d0.astype(float), d1.astype(float))[0, 1])
    c12 = abs(np.corrcoef(d1.astype(float), d2.astype(float))[0, 1])
    F.assert_pins(got, np.array([c01, c12]), atol=1e-9, label="RR_CORR R=3 per-round (r, r+1)")

    # KILLER (r-1 instead of r+1 -> [|corr(d0,d2)|, |corr(d1,d0)|], a DIFFERENT sequence).
    wrong = np.array([abs(np.corrcoef(d0.astype(float), d2.astype(float))[0, 1]), c01])

    def prop_neighbour(v):
        F.assert_pins(v, np.array([c01, c12]), atol=1e-9, label="RR_CORR pairs round r with r+1")

    F.assert_discriminates(prop_neighbour, got, wrong, label="RR_CORR r+1 neighbour")


def test_emitted_rr_corr_zero_variance_column_is_zero():
    # a CONSTANT detector column has zero variance -> the shared _pearson_bits returns 0.0 (the
    # DM ``_conn_corr`` convention), so a foil round with a stuck detector reads correlation 0 (not
    # a divide-by-zero). Exercises the zero-variance arc of the moment machinery.
    n = 100
    det = np.stack([np.zeros(n, np.uint8), (np.arange(n) % 2).astype(np.uint8)], axis=1)  # col0 const
    got = emitted_statistic({"det": det, "obs": np.zeros(n, np.uint8)}, Statistic.RR_CORR,
                            Regime(R=2, n_stab=1))
    F.assert_pins(got, np.array([0.0]), label="zero-variance column -> correlation 0")


# =========================================================================== #
# core.reduce_rr_corr / reduce_spatial_corr -- the SHARED moment reductions    #
# =========================================================================== #
def test_reduce_rr_corr_pins_edges_and_abs_killer():
    rr2d = np.array([[0.5, -0.5], [0.2, 0.8]])                # (R-1, n_stab) = (2, 2), mixed signs
    got = reduce_rr_corr(rr2d)
    assert got.shape == (2,)                                  # length R-1
    F.assert_pins(got, np.abs(rr2d).mean(axis=1), label="reduce_rr_corr = mean_j |.|")  # [0.5, 0.5]

    # KILLER (drop np.abs -> signed cancellation): row 0 abs-mean 0.5 vs signed-mean 0.0.
    signed = np.asarray(rr2d).mean(axis=1)                    # [0.0, 0.5]

    def prop_abs(v):
        F.assert_pins(v, np.abs(rr2d).mean(axis=1), label="reduce_rr_corr must take |.|")

    F.assert_discriminates(prop_abs, got, signed, label="reduce_rr_corr abs")

    with pytest.raises(ValueError, match="expects a 2-D"):
        reduce_rr_corr(np.zeros(3))                           # ndim != 2 (1-D)
    with pytest.raises(ValueError, match="got shape"):
        reduce_rr_corr(np.zeros((2, 2, 2)))                   # ndim != 2 (3-D)
    edge = reduce_rr_corr(np.zeros((0, 4)))                   # shape[0]==0 (R==1) -> [0.0]
    assert edge.shape == (1,)                                 # NOT the (0,)-shaped mean over an empty axis
    F.assert_pins(edge, np.array([0.0]), label="reduce_rr_corr R==1 (shape[0]==0) -> [0.0]")


def test_reduce_spatial_corr_pins_edges_and_diagonal_killer():
    sp3d = np.array([[[1.0, 0.3, -0.2], [0.3, 1.0, 0.5], [-0.2, 0.5, 1.0]],
                     [[1.0, -0.4, 0.1], [-0.4, 1.0, -0.6], [0.1, -0.6, 1.0]]])   # (R, n, n), diag 1
    got = reduce_spatial_corr(sp3d)
    assert got.shape == (2,)                                  # length R
    off = ~np.eye(3, dtype=bool)
    expected = np.abs(sp3d)[:, off].mean(axis=1)              # off-diagonal mean of |.|
    F.assert_pins(got, expected, label="reduce_spatial_corr = off-diagonal mean |.|")
    assert float(np.max(got)) < 1.0                           # the diagonal (=1) is EXCLUDED

    # KILLER (include the diagonal -> the self-correlation 1 leaks in -> a different, larger mean).
    incl_diag = np.abs(sp3d).reshape(sp3d.shape[0], -1).mean(axis=1)

    def prop_offdiag(v):
        F.assert_pins(v, expected, label="reduce_spatial_corr must exclude the diagonal")

    F.assert_discriminates(prop_offdiag, got, incl_diag, label="reduce_spatial_corr off-diagonal")

    with pytest.raises(ValueError, match=r"expects \(R, n_stab, n_stab\)"):
        reduce_spatial_corr(np.zeros((2, 2)))                 # ndim != 3
    with pytest.raises(ValueError, match="got shape"):
        reduce_spatial_corr(np.zeros((2, 3, 4)))              # non-square
    small = reduce_spatial_corr(np.zeros((2, 1, 1)))          # n_stab<2 -> per-round 0, length R
    assert small.shape == (2,)                                # np.zeros(R), NOT a 0-d np.zeros(None)
    F.assert_pins(small, np.zeros(2), label="reduce_spatial_corr n_stab<2 -> per-round 0")


# =========================================================================== #
# core.total_variation                                                         #
# =========================================================================== #
def test_total_variation_pins_and_half_factor_killer():
    p = {0: 0.5, 1: 0.3, 2: 0.2}
    q = {0: 0.1, 1: 0.6, 3: 0.3}                              # disjoint keys 2 (only p) + 3 (only q)
    got = total_variation(p, q)
    expected = 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))   # 0.6
    F.assert_pins(got, expected, label="TV = 0.5 * sum|p-q|")
    assert 0.0 <= got <= 1.0

    # KILLER (drop the 0.5 factor).
    wrong = sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))            # 1.2

    def prop_tv(v):
        F.assert_pins(v, expected, label="TV must carry the 0.5 factor")

    F.assert_discriminates(prop_tv, got, wrong, label="TV half factor")


# =========================================================================== #
# core.compare -- the statistical backbone (dist / scalar / array + verdict)   #
# =========================================================================== #
def _av(value, statistic, exactness, band):
    cls = "a" if exactness is Exactness.EXACT else "b"
    return AnchorValue(statistic, _REG, value, exactness, band, cls, {})


def test_compare_dist_scalar_array_pins_and_verdicts():
    # -- distributional (FULL_JOINT / SYNDROME_DIST) path: TV, band, PASS/FAIL, null subtraction. -- #
    em = {0: 0.6, 1: 0.4}
    match = _av({0: 0.6, 1: 0.4}, Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    v, band, verdict, detail = compare(Statistic.FULL_JOINT, em, match, N=20000)
    F.assert_pins(v, 0.0, label="compare dist value (match) = TV 0")
    assert verdict is Verdict.PASS and band[0] == 0.0 and detail["null"] is None

    far = _av({0: 0.0, 1: 1.0}, Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    v2, band2, verdict2, _ = compare(Statistic.FULL_JOINT, em, far, N=20000)
    exp_tv = 0.5 * sum(abs(em.get(k, 0.0) - far.value.get(k, 0.0)) for k in set(em) | set(far.value))
    F.assert_pins(v2, exp_tv, label="compare dist value (mismatch) = TV")
    assert verdict2 is Verdict.FAIL and v2 > band2[1]         # over the band -> FAIL

    v3, _, _, detail3 = compare(Statistic.FULL_JOINT, em, match, N=20000, null=0.02)
    F.assert_pins(v3, -0.02, label="compare subtracts the null (0 - 0.02)")
    assert detail3["null"] == 0.02

    # -- scalar (SCALAR_FUNC) path: |Δ|, EXACT band 1e-9 vs STATISTICAL band. -- #
    vs, bs, verds, _ = compare(Statistic.SCALAR_FUNC, 1.0,
                               _av(1.0, Statistic.SCALAR_FUNC, Exactness.EXACT, 0.0), N=20000)
    F.assert_pins(vs, 0.0, label="compare scalar value = |Δ|")
    assert verds is Verdict.PASS and bs == (0.0, 1e-9)        # EXACT -> tight 1e-9 band
    vs2, bs2, verds2, _ = compare(Statistic.SCALAR_FUNC, 1.0,
                                  _av(2.0, Statistic.SCALAR_FUNC, Exactness.STATISTICAL, 0.01), N=20000)
    F.assert_pins(vs2, 1.0, label="compare scalar |1-2|")
    assert verds2 is Verdict.FAIL and bs2 == (0.0, 0.01)      # STATISTICAL -> the anchor band

    # -- array (DETECTOR_MARG / RR_CORR / SPATIAL_CORR) path: max|Δ|, e.size + N gates. -- #
    e_arr = np.array([0.1, 0.2])
    a_arr = _av(np.array([0.1, 0.2]), Statistic.DETECTOR_MARG, Exactness.EXACT, 0.0)
    va, ba, verda, _ = compare(Statistic.DETECTOR_MARG, e_arr, a_arr, N=20000)
    F.assert_pins(va, 0.0, label="compare array value (match) = max|Δ|")
    assert verda is Verdict.PASS
    va2, _, verda2, _ = compare(Statistic.DETECTOR_MARG, np.array([0.1, 0.9]), a_arr, N=20000)
    F.assert_pins(va2, 0.7, label="compare array value = max|Δ|")
    assert verda2 is Verdict.FAIL
    # empty emitted + N==0 + STATISTICAL band: value 0.0 (e.size False), hi = 0 + band.
    ve, be, verde, _ = compare(Statistic.DETECTOR_MARG, np.array([]),
                               _av(np.array([]), Statistic.DETECTOR_MARG, Exactness.STATISTICAL, 0.02),
                               N=0)
    F.assert_pins(ve, 0.0, label="compare array empty -> 0.0")
    assert be == (0.0, 0.02) and verde is Verdict.PASS


def test_compare_verdict_has_teeth_force_pass_killer():
    # a mismatched pair -> compare returns FAIL. Forcing PASS unconditionally is the sabotage.
    em = {0: 1.0}
    far = _av({1: 1.0}, Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    real = compare(Statistic.FULL_JOINT, em, far, N=20000)
    wrong = (real[0], real[1], Verdict.PASS, real[3])        # verdict forced to PASS

    def prop_fail(out):
        assert out[2] is Verdict.FAIL, f"a mismatched compare must FAIL, got {out[2]}"

    assert real[2] is Verdict.FAIL
    F.assert_discriminates(prop_fail, real, wrong, label="compare verdict teeth")


def _distband(realized, n, extra=0.0):
    """INDEPENDENT recompute of ``core._dist_band``'s upper edge (the closed form, not the helper)."""
    floor = 0.5 * math.sqrt(realized / n) if n else 0.0
    return max(6.0 / math.sqrt(n) if n else 0.0, 6.0 * floor) + extra


def test_compare_dist_band_pins_every_term():
    # (a) 6/sqrt-dominated (realized=2): band[1] == 6/sqrt(N) exactly -> pins the 6.0 numerator.
    em = {0: 0.6, 1: 0.4}
    av = _av({0: 0.6, 1: 0.4}, Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    _, band, _, _ = compare(Statistic.FULL_JOINT, em, av, N=20000)
    F.assert_pins(band, (0.0, _distband(2, 20000)), label="dist band 6/sqrt-dominated")

    # (b) floor-dominated (realized=8, small N): band[1] == 6 * 0.5*sqrt(realized/N) -> pins 0.5 & 6.
    keys = list(range(8))
    em2 = {k: 1.0 / 8 for k in keys}
    av2 = _av({k: 1.0 / 8 for k in keys}, Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    _, band2, _, _ = compare(Statistic.FULL_JOINT, em2, av2, N=100)
    assert 6.0 * (0.5 * math.sqrt(8 / 100)) > 6.0 / math.sqrt(100)      # the floor term truly dominates
    F.assert_pins(band2, (0.0, _distband(8, 100)), label="dist band floor-dominated")

    # (c) STATISTICAL anchor: the + anchor.band extra is ADDED (pins the `is STATISTICAL` and the +).
    av3 = _av({0: 0.6, 1: 0.4}, Statistic.FULL_JOINT, Exactness.STATISTICAL, 0.05)
    _, band3, _, _ = compare(Statistic.FULL_JOINT, em, av3, N=20000)
    F.assert_pins(band3, (0.0, _distband(2, 20000, extra=0.05)), label="dist band + STATISTICAL extra")

    # (d) N==0 with a STATISTICAL band: both MC terms vanish -> band[1] == extra (pins the `else 0.0`).
    av4 = _av({0: 1.0}, Statistic.FULL_JOINT, Exactness.STATISTICAL, 0.05)
    _, band4, _, _ = compare(Statistic.FULL_JOINT, {0: 1.0}, av4, N=0)
    F.assert_pins(band4, (0.0, 0.05), label="dist band N=0 -> extra only")


def test_compare_verdict_flips_exactly_at_band_edge():
    # -- distributional boundary: value == band[1] EXACTLY -> PASS, not FAIL. The null is derived from
    #    the SUT's OWN band[1] so value = tv - (-band[1]) = band[1] to the bit (no sqrt-ULP race). --
    em = {0: 0.6, 1: 0.4}
    av = _av({0: 0.6, 1: 0.4}, Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    _, band0, _, _ = compare(Statistic.FULL_JOINT, em, av, N=20000)   # tv=0, band0[1] = the MC floor
    v, band, verdict, detail = compare(Statistic.FULL_JOINT, em, av, N=20000, null=-band0[1])
    assert v == band[1]                                # value hits the edge exactly
    assert verdict is Verdict.PASS                     # value <= band[1] at equality -> PASS (mut < -> FAIL)
    assert detail["tv"] == 0.0 and detail["null"] == -band0[1]   # pins the detail keys "tv"/"null"

    # -- scalar boundary: |Δ| == hi (STATISTICAL band) EXACTLY -> PASS. --
    vs, bs, verds, _ = compare(Statistic.SCALAR_FUNC, 1.5,
                               _av(1.0, Statistic.SCALAR_FUNC, Exactness.STATISTICAL, 0.5), N=100)
    assert vs == 0.5 and bs == (0.0, 0.5) and verds is Verdict.PASS   # 0.5 <= 0.5 (mut < -> FAIL)

    # -- array boundary: max|Δ| == hi == 8/sqrt(N) EXACTLY -> PASS + pins the 8.0 numerator. --
    va, ba, verda, _ = compare(Statistic.DETECTOR_MARG, np.array([1.0]),
                               _av(np.array([0.0]), Statistic.DETECTOR_MARG, Exactness.EXACT, 0.0), N=64)
    assert va == 1.0 and ba == (0.0, 8.0 / math.sqrt(64)) and verda is Verdict.PASS
    assert ba[1] == 1.0                                # 8/sqrt(64)=1.0 (mut 9.0 -> 1.125 -> band assert dies)


# =========================================================================== #
# core.route -- feasible + exact-preferred + min-mem                           #
# =========================================================================== #
def test_route_exact_preferred_min_mem_and_infeasible_none():
    stat = Statistic.FULL_JOINT
    a_stat = RouteStub(name="stat", answers_set={stat}, feasible=True,
                       exactness=Exactness.STATISTICAL, mem=1)
    a_exact = RouteStub(name="exact", answers_set={stat}, feasible=True,
                        exactness=Exactness.EXACT, mem=999)
    chosen = route([a_stat, a_exact], stat, _REG)
    assert chosen is a_exact                                  # EXACT preferred even at larger mem

    # KILLER (flip the exactness sort key -> the STATISTICAL anchor would win).
    def prop_exact(anc):
        assert anc.capability(stat, _REG).exactness is Exactness.EXACT

    F.assert_discriminates(prop_exact, a_exact, a_stat, label="route prefers EXACT")

    # among EXACT feasible, the TIGHTEST memory bound wins.
    a_e_big = RouteStub(name="e_big", answers_set={stat}, feasible=True,
                        exactness=Exactness.EXACT, mem=100)
    a_e_small = RouteStub(name="e_small", answers_set={stat}, feasible=True,
                          exactness=Exactness.EXACT, mem=50)
    picked = route([a_e_big, a_e_small], stat, _REG)
    assert picked is a_e_small
    F.assert_pins(picked._mem, min(100, 50), label="route picks the min-mem EXACT anchor")

    # None when NO anchor is feasible (both filter arcs: non-answering + answering-infeasible).
    a_noans = RouteStub(name="noans", answers_set=set(), feasible=True, exactness=Exactness.EXACT)
    a_infeas = RouteStub(name="infeas", answers_set={stat}, feasible=False, exactness=Exactness.EXACT)
    assert route([a_noans, a_infeas], stat, _REG) is None


def test_route_mem_zero_tiebreak_default_killer():
    # the ``mem_bytes_estimate or 0`` default matters when an anchor reports mem==0: the mem=0 anchor
    # must WIN the min over mem=1. A mutated ``or 1`` maps 0->1, ties them, and (stable min) returns
    # the FIRST -> the mem=1 anchor -> a wrong route.
    stat = Statistic.FULL_JOINT
    a_one = RouteStub(name="one", answers_set={stat}, feasible=True, exactness=Exactness.EXACT, mem=1)
    a_zero = RouteStub(name="zero", answers_set={stat}, feasible=True, exactness=Exactness.EXACT, mem=0)
    assert route([a_one, a_zero], stat, _REG) is a_zero   # mem 0 < 1 (orig); ``or 1`` -> ties -> a_one


# =========================================================================== #
# core.MeasureCtx.score / .corrupt_answer                                      #
# =========================================================================== #
def _score_ctx():
    records = _make_records(_JOINT, 20000)
    emitted = emitted_statistic(records, Statistic.FULL_JOINT, _REG)
    av = _av(dict(_JOINT), Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    return MeasureCtx(MemAnchor(_JOINT), Statistic.FULL_JOINT, _REG, 20000, emitted, av,
                      teacher=FakeTeacher(_JOINT)), emitted, av


def test_measurectx_score_pins_and_zero_killer():
    ctx, emitted, av = _score_ctx()

    # default args -> uses self.emitted / self.anchor_value (both ternary None-arcs).
    s0 = ctx.score()
    assert s0 >= 0.0
    F.assert_pins(s0, 0.0, label="score(match) = TV 0")
    # score() == compare(...)[0], pinned to an INDEPENDENT TV recompute.
    F.assert_pins(s0, total_variation(emitted, av.value), label="score == compare()[0]")

    # explicit emitted -> the ternary else-arc; distance > 0 for a mismatched surface.
    other = {0: 1.0}
    s1 = ctx.score(emitted=other)
    exp = 0.5 * sum(abs(other.get(k, 0.0) - av.value.get(k, 0.0)) for k in set(other) | set(av.value))
    F.assert_pins(s1, exp, label="score(other) = TV(other, anchor)")
    # explicit anchor_value -> the other ternary else-arc.
    s2 = ctx.score(anchor_value=replace(av, value={0: 1.0}))
    exp2 = 0.5 * sum(abs(emitted.get(k, 0.0) - {0: 1.0}.get(k, 0.0)) for k in set(emitted) | {0})
    F.assert_pins(s2, exp2, label="score(anchor_value=...) uses the override")

    # KILLER (return 0.0): the mismatched score is nonzero.
    def prop_score(v):
        assert abs(v - exp) <= 1e-9, f"score must equal {exp}, got {v}"

    F.assert_discriminates(prop_score, s1, 0.0, label="score is not a constant 0")


def test_measurectx_init_stores_every_attr():
    anc = MemAnchor(_JOINT)
    av = _av(dict(_JOINT), Statistic.FULL_JOINT, Exactness.EXACT, 0.0)
    t = FakeTeacher(_JOINT)
    em = {0: 1.0}
    ctx = MeasureCtx(anc, Statistic.SYNDROME_DIST, _REG, 12345, em, av, teacher=t)
    # every constructor arg is stored VERBATIM (kills self.<attr> = None sabotages).
    assert ctx.anchor is anc
    assert ctx.statistic is Statistic.SYNDROME_DIST
    assert ctx.regime is _REG
    assert ctx.N == 12345
    assert ctx.emitted is em
    assert ctx.anchor_value is av
    assert ctx.teacher is t


def test_measurectx_corrupt_answer_forwards_args_and_reanswers_killer():
    stub = RecordingMemAnchor(_JOINT, name="mem")
    t = FakeTeacher(_JOINT)
    av = stub.answer(t, Statistic.FULL_JOINT, _REG)          # the uncorrupted ground truth
    ctx = MeasureCtx(stub, Statistic.FULL_JOINT, _REG, 20000, emitted=None, anchor_value=av,
                     teacher=t)
    corrupted = ctx.corrupt_answer({"stab": 1})
    assert isinstance(corrupted, AnchorValue) and corrupted.value != av.value

    # the re-answer forwards ctx.teacher/statistic/regime/N + the corruption VERBATIM (kills each
    # arg-dropped-to-None mutant on ``anchor.answer(...)``).
    assert stub.answer_calls[-1] == (t, Statistic.FULL_JOINT, _REG, 20000, {"stab": 1})

    # KILLER (return the answer unchanged -> the corrupt control could never fire).
    def prop_differs(a):
        assert a.value != av.value, "corrupt_answer must return a DIFFERENT ground truth"

    F.assert_discriminates(prop_differs, corrupted, av, label="corrupt_answer re-answers")


# =========================================================================== #
# core.certify_cells -- route -> controls-first -> score -> ledger             #
# =========================================================================== #
def test_certify_cells_full_path_passes_with_firing_control():
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [MemAnchor(_JOINT)], [ShuffleCtrl(), NonGuardingCtrl()], N=20000)
    row = rep.row("mem", Statistic.FULL_JOINT)
    assert row is not None and row.verdict is Verdict.PASS
    F.assert_pins(row.value, 0.0, label="the emitted matches the anchor -> TV 0")
    assert all(c.detail["fired"] for c in rep.controls)      # the guarding control FIRED
    assert row.detail["n_controls"] == 1 and row.detail["n_controls_fired"] == 1   # nonguarding skipped
    assert rep.verdict is Verdict.PASS, rep.summary()

    # the PASS row's band is the EMITTED MC floor (EXACT anchor, realized=4 keys) -- pinned exactly.
    assert row.band is not None
    F.assert_pins(row.band, (0.0, _distband(4, 20000)), label="PASS row band = emitted MC floor")

    # the routing entry names the anchor + its exactness under the (stat.value, _rkey) key.
    assert rep.routing[_routekey(Statistic.FULL_JOINT, _REG)] == "mem [exact]"

    # the report carries the evaluator-only truth + the run provenance VERBATIM.
    assert rep.truth == {"theta": 0.15, "gamma": 0.04}
    assert rep.provenance == {"N": 20000, "seed": 0, "m": 0}


def test_certify_cells_records_positive_and_control_answer_and_emit_args():
    teacher = RecordingTeacher(_JOINT)
    anchor = RecordingMemAnchor(_JOINT)
    ScoringCtrl.seen_run = None
    rep = certify_cells(teacher, [(Statistic.FULL_JOINT, _REG)], [anchor], [ScoringCtrl()],
                        N=20000, seed=7, m=3)
    assert rep.verdict is Verdict.PASS, rep.summary()

    # the POSITIVE answer forwards (teacher, statistic, regime, N, corrupt=None) verbatim ...
    assert anchor.answer_calls[0] == (teacher, Statistic.FULL_JOINT, _REG, 20000, None)
    # ... and the control's corrupt re-answer forwards the SAME cell coords + the corruption.
    assert anchor.answer_calls[-1] == (teacher, Statistic.FULL_JOINT, _REG, 20000, {"stab": 1})
    # the ``cap =`` probe used the real (statistic, regime) (kills capability(None, .)/(., None)).
    assert anchor.capability_calls[-1] == (Statistic.FULL_JOINT, _REG)
    # the full-mix emit leg forwarded (regime, m, N, seed) verbatim.
    assert teacher.emit_args[-1] == (_REG, 3, 20000, 7)
    # the control's run(...) received the real (statistic, regime, N) (kills run(., None, .)/(., ., None)).
    assert ScoringCtrl.seen_run == (Statistic.FULL_JOINT, _REG, 20000)
    # provenance reflects the non-default seed/m (kills the signature-default seed/m mutants).
    assert rep.provenance == {"N": 20000, "seed": 7, "m": 3}


def test_certify_cells_clifford_emit_forwards_args():
    teacher = RecordingTeacher(_JOINT)
    certify_cells(teacher, [(Statistic.FULL_JOINT, _REG)],
                  [MemAnchor(_JOINT, emit_kind_val="clifford_slice")], [ShuffleCtrl()],
                  N=20000, seed=5, m=2)
    # the Clifford-slice leg forwarded (regime, p_x, m, N, seed) verbatim (p_x from anchor.p_x).
    assert teacher.clifford_args[-1] == (_REG, 0.03, 2, 20000, 5)


def test_certify_cells_no_emit_kind_anchor_uses_full_default():
    # an anchor WITHOUT emit_kind -> the core defaults kind="full" -> teacher.emit -> PASS.
    # A mutated default literal ("XXfullXX"/"FULL") would take the raise-loud else -> error.
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [NoEmitKindAnchor(_JOINT)], [ShuffleCtrl()], N=20000)
    row = rep.row("noek", Statistic.FULL_JOINT)
    assert row is not None and row.verdict is Verdict.PASS


def test_certify_cells_caches_one_emit_per_DISTINCT_regime():
    # the cache key is (regime, kind, m): TWO DISTINCT regimes -> TWO emits (a key=None mutant would
    # collide them to ONE and silently reuse the wrong records).
    teacher = CountingTeacher2(_JOINT)
    reg2 = Regime(R=2, register="subregister", n_active=1, n_stab=1)
    certify_cells(teacher, [(Statistic.FULL_JOINT, _REG), (Statistic.FULL_JOINT, reg2)],
                  [MemAnchor(_JOINT)], [ShuffleCtrl()], N=20000)
    assert teacher.emit_calls == 2


def test_certify_cells_infeasible_is_unanchored_not_pass():
    oom = Regime(R=2, register="full", n_active=9, n_stab=1)
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, oom)],
                        [MemAnchor(_JOINT, feasible=False)], [], N=20000)
    assert rep.row("mem", Statistic.FULL_JOINT) is None      # no anchor row
    assert rep.verdict is not Verdict.PASS                   # an honest gap, never a silent pass

    # pin the WHOLE UNANCHORED row (anchor/statistic/value/band/class/verdict/detail) + the routing.
    r = rep.rows[0]
    assert r.anchor is None
    assert r.statistic is Statistic.FULL_JOINT
    assert math.isnan(r.value)                               # float("nan"); a None value would raise here
    assert r.band is None
    assert r.epistemic_class == "c"
    assert r.verdict is Verdict.UNANCHORED
    assert r.detail == {"reason": "no feasible anchor for this regime"}
    assert rep.routing[_routekey(Statistic.FULL_JOINT, oom)] == \
        "UNANCHORED (no feasible anchor — honest gap, not PASS)"


def test_certify_cells_unanchored_continues_to_next_cell():
    # an UNANCHORED cell must CONTINUE (not break) so a later feasible cell is still certified.
    oom = Regime(R=2, register="full", n_active=9, n_stab=1)
    rep = certify_cells(FakeTeacher(_JOINT),
                        [(Statistic.FULL_JOINT, oom), (Statistic.FULL_JOINT, _REG)],
                        [RegimeGatedAnchor(_JOINT)], [ShuffleCtrl()], N=20000)
    assert len(rep.rows) == 2                                # a ``break`` would drop the 2nd cell
    assert rep.rows[0].verdict is Verdict.UNANCHORED         # oom -> no feasible anchor
    assert rep.rows[1].verdict is Verdict.PASS               # _REG -> feasible + emitted matches


def test_certify_cells_inert_control_forces_fail_killer():
    cells = [(Statistic.FULL_JOINT, _REG)]
    real = certify_cells(FakeTeacher(_JOINT), cells, [MemAnchor(_JOINT)], [InertCtrl()], N=20000)
    wrong = certify_cells(FakeTeacher(_JOINT), cells, [MemAnchor(_JOINT)], [], N=20000)
    assert real.row("mem", Statistic.FULL_JOINT).verdict is Verdict.PASS   # the data matches...
    assert not any(c.detail["fired"] for c in real.controls)              # ...but the control is inert
    assert real.verdict is Verdict.FAIL and wrong.verdict is Verdict.FINDING

    # KILLER (skip the control loop -> no inert falsifier -> the report would NOT be forced to FAIL).
    def prop_fail(rep):
        assert rep.verdict is Verdict.FAIL, f"an inert control must force FAIL, got {rep.verdict}"

    F.assert_discriminates(prop_fail, real, wrong, label="inert control forces FAIL")


def test_certify_cells_clifford_slice_emit_leg():
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                        [MemAnchor(_JOINT, emit_kind_val="clifford_slice")], [ShuffleCtrl()], N=20000)
    row = rep.row("mem", Statistic.FULL_JOINT)               # the clifford-slice emit leg ran
    assert row is not None and row.verdict is Verdict.PASS


def test_certify_cells_unknown_emit_kind_raises():
    with pytest.raises(NotImplementedError, match="has no teacher emit path in"):
        certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)],
                      [MemAnchor(_JOINT, emit_kind_val="nonunital_slice")], [ShuffleCtrl()], N=20000)


def test_certify_cells_rr_corr_r1_cell():
    reg1 = Regime(R=1, register="subregister", n_active=1, n_stab=1)
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.RR_CORR, reg1)], [RRStub()], [], N=20000)
    row = rep.row("rr", Statistic.RR_CORR)
    assert row is not None and row.statistic is Statistic.RR_CORR and row.verdict is Verdict.PASS
    F.assert_pins(row.value, 0.0, label="RR_CORR R=1 emitted [0.0] matches the anchor")
    assert rep.verdict is Verdict.FINDING                    # no falsifier -> uncertified, never PASS


def test_certify_cells_caches_one_emit_per_regime():
    # the perf invariant: ONE teacher.emit per (regime, kind, m) feeds EVERY statistic at that regime.
    class CountingTeacher(FakeTeacher):
        emit_calls = 0

        def emit(self, regime, *, m, N, seed):
            self.emit_calls += 1
            return _make_records(self._joint, N)

    teacher = CountingTeacher(_JOINT)
    rep = certify_cells(teacher, [(Statistic.FULL_JOINT, _REG), (Statistic.SYNDROME_DIST, _REG)],
                        [MemAnchor(_JOINT)], [ShuffleCtrl()], N=20000)
    assert teacher.emit_calls == 1                           # cache hit: the 2nd cell reused the emit
    assert rep.verdict is Verdict.PASS, rep.summary()


def test_certify_cells_broken_carrier_fails():
    # a broken carrier (a DIFFERENT emitted law) FAILs against the true-law anchor -> the comparison
    # has teeth; the FAILing scored row drives the verdict to FAIL (distinct from the control-inert
    # FAIL path).
    broken = FakeTeacher({0: 0.1, 1: 0.4, 2: 0.45, 3: 0.05})
    rep = certify_cells(broken, [(Statistic.FULL_JOINT, _REG)], [MemAnchor(_JOINT)],
                        [ShuffleCtrl()], N=20000)
    assert rep.row("mem", Statistic.FULL_JOINT).verdict is Verdict.FAIL
    assert all(c.detail["fired"] for c in rep.controls)      # the control still fired (not the cause)
    assert rep.verdict is Verdict.FAIL, rep.summary()


def test_certify_cells_empty_cells_is_finding():
    rep = certify_cells(FakeTeacher(_JOINT), [], [MemAnchor(_JOINT)], [ShuffleCtrl()], N=20000)
    assert rep.rows == () and rep.verdict is Verdict.FINDING  # no cell -> nothing certified


def test_certify_cells_rejects_exact_anchor_with_nonzero_band():
    # the EXACT => band==0 ingest contract has teeth: an anchor declaring EXACT yet returning a
    # nonzero band is rejected loudly at answer time.
    class BadExactAnchor(MemAnchor):
        def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
            return AnchorValue(statistic, regime, dict(self._joint), Exactness.EXACT, 0.5, "a", {})

    with pytest.raises(ValueError, match="undeclared band"):
        certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)], [BadExactAnchor(_JOINT)],
                      [], N=20000)


def test_certify_cells_rejects_class_a_statistical_value():
    # class<->exactness consistency: a class-'a' (exact-grade) value that is actually STATISTICAL
    # would be rolled up as an EXACT PASS (inflation) -- it must be rejected on ingest.
    class BadClassAnchor(MemAnchor):
        def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
            return AnchorValue(statistic, regime, dict(self._joint), Exactness.STATISTICAL, 0.01,
                               "a", {})

    with pytest.raises(ValueError, match="mislabeled 'a'"):
        certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)], [BadClassAnchor(_JOINT)],
                      [], N=20000)


# =========================================================================== #
# core.certify_cells n_fired coverage + core._rollup verdict edges              #
# =========================================================================== #
def test_certify_cells_nfired_counts_only_applicable_and_fired():
    # a control that is INAPPLICABLE yet claims fired=True must NOT count toward the cell's falsifier
    # coverage: n_controls_fired needs (applicable AND fired). Miscounting it -> a teeth-less PASS.
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)], [MemAnchor(_JOINT)],
                        [FixedCtrl("inapp_fired", {"applicable": False, "fired": True})], N=20000)
    assert rep.row("mem", Statistic.FULL_JOINT).detail["n_controls_fired"] == 0
    assert rep.verdict is Verdict.FINDING           # no APPLICABLE firing control -> uncertified


def test_certify_cells_nfired_counts_missing_applicable_as_present():
    # a firing control with NO "applicable" key defaults to applicable -> it DOES count (the default
    # is True, not None/False), so the passing row is certified.
    rep = certify_cells(FakeTeacher(_JOINT), [(Statistic.FULL_JOINT, _REG)], [MemAnchor(_JOINT)],
                        [FixedCtrl("missapp_fired", {"fired": True})], N=20000)
    assert rep.row("mem", Statistic.FULL_JOINT).detail["n_controls_fired"] == 1
    assert rep.verdict is Verdict.PASS              # counted -> a real falsifier -> PASS


def _lr_ctrl(detail):
    return LedgerRow("a", Statistic.FULL_JOINT, 1.0, None, "c", Verdict.CONTROL, detail)


def _lr_pass(detail=None):
    return LedgerRow("a", Statistic.FULL_JOINT, 0.0, (0.0, 0.1), "a", Verdict.PASS,
                     {"n_controls_fired": 1} if detail is None else detail)


def test_rollup_control_fired_gate_edges():
    # an APPLICABLE control that did NOT fire (missing/false fired) forces FAIL ...
    assert _rollup([_lr_pass()], [_lr_ctrl({"applicable": True})]) is Verdict.FAIL         # no "fired"
    assert _rollup([_lr_pass()], [_lr_ctrl({"applicable": True, "fired": False})]) is Verdict.FAIL
    # ... an APPLICABLE control that fired does NOT force FAIL (the row's own coverage carries it).
    assert _rollup([_lr_pass()], [_lr_ctrl({"applicable": True, "fired": True})]) in (
        Verdict.PASS, Verdict.PASS_PROVISIONAL)
    # an INAPPLICABLE non-firing control is SKIPPED -> it must NOT force FAIL.
    assert _rollup([_lr_pass()], [_lr_ctrl({"applicable": False, "fired": False})]) in (
        Verdict.PASS, Verdict.PASS_PROVISIONAL)
    # a control MISSING "applicable" defaults to applicable -> a non-firing one DOES force FAIL.
    assert _rollup([_lr_pass()], [_lr_ctrl({"fired": False})]) is Verdict.FAIL


def test_rollup_pass_row_needs_a_fired_control_default_zero():
    # a PASS row whose detail LACKS n_controls_fired reads as 0 fired -> FINDING (uncertified). A
    # mutated default (1 -> wrongly PASS; None -> ``None < 1`` TypeError) is caught here.
    assert _rollup([_lr_pass(detail={})], []) is Verdict.FINDING
    # a PASS row that DOES record coverage (n_controls_fired>=1) rolls up to PASS when all rows exact.
    assert _rollup([_lr_pass()], []) is Verdict.PASS
    # a STATISTICAL (class 'b') passing row caps at PASS_PROVISIONAL (never PASS -- no inflation).
    stat_row = LedgerRow("a", Statistic.FULL_JOINT, 0.0, (0.0, 0.1), "b", Verdict.PASS,
                         {"n_controls_fired": 1})
    assert _rollup([stat_row], []) is Verdict.PASS_PROVISIONAL


# =========================================================================== #
# facade.certify_teacher -- route + merge + roll (stubbed anchors, CPU-only)   #
# =========================================================================== #
def test_certify_teacher_merges_two_anchors_and_passes():
    teacher = FakeTeacher(_JOINT)
    a_fj = MemAnchor(_JOINT, name="anchor_fj", answers_set={Statistic.FULL_JOINT})
    a_sd = MemAnchor(_JOINT, name="anchor_sd", answers_set={Statistic.SYNDROME_DIST})
    rep = certify_teacher(teacher, anchors=[a_fj, a_sd],
                          cells=[(Statistic.FULL_JOINT, _REG), (Statistic.SYNDROME_DIST, _REG)],
                          controls=[ShuffleCtrl()], N=20000, level="standard")
    assert rep.verdict in (Verdict.PASS, Verdict.PASS_PROVISIONAL), rep.summary()
    assert {r.anchor for r in rep.rows} == {"anchor_fj", "anchor_sd"}       # BOTH anchors merged
    assert rep.provenance["level"] == "standard" and rep.provenance["N"] == 20000
    assert all(c.detail["fired"] for c in rep.controls)

    # KILLER (merge only the first anchor's rows -> anchor_sd's row disappears).
    def prop_both(r):
        assert "anchor_sd" in {x.anchor for x in r.rows}, "the merge must keep BOTH anchors' rows"

    wrong = replace(rep, rows=tuple(x for x in rep.rows if x.anchor == "anchor_fj"))
    F.assert_discriminates(prop_both, rep, wrong, label="certify_teacher merges all anchors")


def test_certify_teacher_auto_builds_anchors_and_raises_when_infeasible():
    # anchors=None -> the auto-built DM + stim anchors (CPU: DM budget 0 -> infeasible; neither
    # answers FLOOR) -> every cell infeasible -> ValueError. Exercises the auto-build + default-
    # controls + the "not feasible: continue" + "not all_rows: raise" arcs, with NO GPU.
    teacher = FakeTeacher({0: 1.0})
    with pytest.raises(ValueError):
        certify_teacher(teacher, level="smoke", cells=[(Statistic.FLOOR, _REG)])   # dm_safety None -> {}
    with pytest.raises(ValueError):
        certify_teacher(teacher, level="smoke", cells=[(Statistic.FLOOR, _REG)],
                        dm_safety=0.78)                                             # -> the else arc


def test_certify_teacher_cells_none_uses_the_level_plan():
    # cells=None -> the ``_regime``-from-plan branch of the ternary (needs sched.n_data/stabilizers).
    teacher = FakeTeacher({0: 1.0}, sched=SimpleNamespace(n_data=1, stabilizers=[object()]))
    infeasible = MemAnchor({0: 1.0}, name="infeas", feasible=False,
                           answers_set={Statistic.DETECTOR_MARG})
    with pytest.raises(ValueError):
        certify_teacher(teacher, anchors=[infeasible], controls=[ShuffleCtrl()], level="smoke")


def test_certify_teacher_unknown_level_rejected():
    with pytest.raises(ValueError, match="unknown level"):
        certify_teacher(FakeTeacher({0: 1.0}), level="bogus", anchors=[MemAnchor({0: 1.0})],
                        cells=[(Statistic.FULL_JOINT, _REG)])


def test_regime_from_plan_pins_every_field():
    # cells=None -> the facade builds each cell's Regime from the teacher's schedule via ``_regime``.
    # Pin EVERY field of that Regime (R from the plan; register/arm/b constants; n_active/n_stab from
    # the schedule) so a mutated field literal is caught.
    teacher = FakeTeacher(_JOINT, sched=SimpleNamespace(n_data=5,
                                                        stabilizers=[object(), object(), object()]))
    RegimeRecAnchor.seen = None
    certify_teacher(teacher, anchors=[RegimeRecAnchor()], controls=[], level="smoke", cells=None)
    assert RegimeRecAnchor.seen == Regime(R=1, register="full", n_active=5, n_stab=3, arm="A", b=1.0)


# =========================================================================== #
# types -- value types (enums / frozen dataclasses) + the Protocol ports       #
# =========================================================================== #
def test_types_dataclasses_and_enums_round_trip():
    reg = Regime(R=2, register="subregister", n_active=3, n_stab=8, sites=(0, 1, 2))
    assert (reg.R, reg.register, reg.n_active, reg.n_stab, reg.arm, reg.b, reg.sites) == \
        (2, "subregister", 3, 8, "A", 1.0, (0, 1, 2))
    feas = Feasibility(ok=False, reason="R>=2 full-9q OOM", mem_bytes_estimate=100)
    assert (feas.ok, feas.reason, feas.mem_bytes_estimate) == (False, "R>=2 full-9q OOM", 100)
    cap = Capability(Statistic.FULL_JOINT, Exactness.EXACT, feasible=False, reason="r",
                     epistemic_class="a", mem_bytes_estimate=5)
    assert (cap.statistic, cap.exactness, cap.feasible, cap.epistemic_class, cap.mem_bytes_estimate) \
        == (Statistic.FULL_JOINT, Exactness.EXACT, False, "a", 5)
    av = AnchorValue(Statistic.SYNDROME_DIST, reg, {0: 1.0}, Exactness.STATISTICAL, 0.01, "b",
                     {"anchor": "x"})
    assert av.value == {0: 1.0} and av.band == 0.01 and av.exactness is Exactness.STATISTICAL
    assert av.provenance == {"anchor": "x"}
    row = LedgerRow("dm", Statistic.SYNDROME_DIST, 4e-4, (0.0, 2e-3), "a", Verdict.PASS, {"z": 1})
    assert (row.anchor, row.value, row.band, row.verdict, row.detail) == \
        ("dm", 4e-4, (0.0, 2e-3), Verdict.PASS, {"z": 1})

    # enums: member/value round-trip (both directions).
    assert Exactness.EXACT.value == "exact" and Exactness("statistical") is Exactness.STATISTICAL
    assert Statistic.FULL_JOINT.value == "full_joint" and Statistic("rr_corr") is Statistic.RR_CORR
    assert Verdict.PASS.value == "PASS" and Verdict.PASS_PROVISIONAL.value == "PASS*"
    assert Verdict("FAIL") is Verdict.FAIL and Verdict("UNANCHORED") is Verdict.UNANCHORED


def test_certreport_row_found_none_and_statistic_killer():
    r_syn = LedgerRow("dm", Statistic.SYNDROME_DIST, 1e-3, (0.0, 2e-3), "a", Verdict.PASS)
    r_full = LedgerRow("dm", Statistic.FULL_JOINT, 2e-3, (0.0, 3e-3), "a", Verdict.PASS)
    rep = CertReport(Verdict.PASS, (r_syn, r_full), (), {})
    assert rep.row("dm", Statistic.FULL_JOINT) is r_full     # found (skips r_syn on the statistic)
    assert rep.row("dm", Statistic.FLOOR) is None            # no match -> None
    assert rep.row("other", Statistic.SYNDROME_DIST) is None  # anchor mismatch -> None

    # KILLER (drop the "and r.statistic==" test -> an anchor-only match returns r_syn for a FULL query).
    def prop_full(r):
        assert r is not None and r.statistic is Statistic.FULL_JOINT

    F.assert_discriminates(prop_full, rep.row("dm", Statistic.FULL_JOINT), r_syn,
                           label="CertReport.row matches BOTH anchor and statistic")


def test_certreport_summary_shows_verdicts_and_both_band_arcs():
    r_fail = LedgerRow("dm", Statistic.SYNDROME_DIST, 0.5, (0.0, 1e-3), "a", Verdict.FAIL)   # band set
    r_gap = LedgerRow(None, Statistic.FULL_JOINT, float("nan"), None, "c", Verdict.UNANCHORED)  # None
    ctrl = LedgerRow("dm", Statistic.SYNDROME_DIST, 1.0, None, "c", Verdict.CONTROL, {"fired": True})
    s = CertReport(Verdict.FAIL, (r_fail, r_gap), (ctrl,), {}).summary()
    assert "=== certify: FAIL ===" in s                      # the headline verdict line
    assert "FAIL" in s and "UNANCHORED" in s and "CONTROL" in s
    assert "band=(" in s                                     # a band-set row prints its interval
    assert "-" in s                                          # the None-anchor row prints '-'


def test_certreport_assert_pass_accepts_pass_rejects_fail_killer():
    ok = CertReport(Verdict.PASS, (), (), {})
    prov = CertReport(Verdict.PASS_PROVISIONAL, (), (), {})
    ok.assert_pass()                                         # PASS -> no raise
    prov.assert_pass()                                       # PASS* -> no raise
    with pytest.raises(AssertionError):
        CertReport(Verdict.FAIL, (), (), {}).assert_pass()   # FAIL -> raise

    # KILLER (widen the accept set to include FAIL): assert_pass must REJECT a FAIL report.
    def prop_accepts(rep):
        rep.assert_pass()

    F.assert_discriminates(prop_accepts, ok, CertReport(Verdict.FAIL, (), (), {}),
                           label="assert_pass accepts PASS, rejects FAIL")


def test_ports_are_runtime_checkable_protocols_with_teeth():
    class DuckAnchor:
        name = "duck"
        independence = "from-scratch closed form (test)"

        def answers(self):
            return frozenset()

        def capability(self, statistic, regime):
            return None

        def answer(self, teacher, statistic, regime, *, N=None, generator=None, corrupt=None):
            return None

    class DuckControl:
        name = "shuffle"

        def guards(self, statistic):
            return True

        def expect(self):
            return "must_fail"

        def run(self, ctx, statistic, regime, *, N=None):
            return None

    class DuckTeacher:
        @property
        def sched(self):
            return None

        @property
        def truth(self):
            return {}

        def emit(self, regime, *, m, N, seed):
            return None

        def channels(self):
            return None

    class DuckDMReplay:
        def dm_round_callbacks(self, device):
            return (None, None)

    class DuckClifford:
        def emit_clifford_slice(self, regime, *, p_x, m, N, seed):
            return {}

    assert isinstance(DuckAnchor(), Anchor)
    assert isinstance(DuckControl(), Control)
    assert isinstance(DuckTeacher(), ControlledNoiseProcess)
    assert isinstance(DuckDMReplay(), DMReplayable)
    assert isinstance(DuckClifford(), CliffordSliceable)
    # duck-typing teeth: a bare object conforms to NONE of the ports.
    for proto in (Anchor, Control, ControlledNoiseProcess, DMReplayable, CliffordSliceable):
        assert not isinstance(object(), proto)

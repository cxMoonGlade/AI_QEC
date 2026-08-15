"""Per-unit L0+L1 coverage of
``error_coupling_simulator.quantum_bath.observables`` (7 CPU-pure units).

Current coverage contract: docs/SIMULATOR.md SS12.3/12.4. The module
is alphabet-agnostic multi-time record statistics over a 3-round outcome distribution --
pure math (numpy/math only, no torch), so it gets the FULL treatment: L0 (100% statement +
branch per unit) + L1 (Hypothesis faithfulness properties). L2 runs through the current
mutation harness.

The 7 units + their L0 partition and L1 invariant. NB on the
"branch surface": coverage.py --branch emits NO tracked branch arc for a generator/comprehension
body, so K_stat_joint / K_stat_binary / tv_distance / record_distance score branch 0/0 (nothing
to miss) -- their faithfulness rests on the L1 PROPERTY, not on a branch count.

  UNIT               L0 branch surface                       L1 faithfulness property
  ----               -----------------                       ------------------------
  K_stat_joint       none tracked (comprehension; 0/0)       >=0; ==0 when P_skip = exact
                                                             2-marginal (Kolmogorov consistency)
  project_axis       for-loop; out.get default vs existing   mass-preserving marginal
                     (KEY-COLLISION case exercises existing)  (sum + per-key-len invariant)
  K_stat_binary      none tracked (comprehension; 0/0)       >=0; ==0 on exact binary marginal
  M_mem_stat         ternary denom>1e-15 else 0.0            >=0; ==0 on a Markov-1 chain
                     (ZERO-MIDDLE-MARGINAL case)
  exact_cmi_bits     `if p>0` (P==0 KEY case) + live guard    I(s1;s3|s2) >= 0 (CMI theorem);
                     `if den>0 and num>0` (UNDERFLOW case)    ==0 on a Markov-1 chain
  tv_distance        none tracked (comprehension; 0/0)       in [0,1], symmetric on shared support
  record_distance    none tracked (comprehension; 0/0)       in [0,1], symmetric on shared support

SHARED-SUPPORT CONTRACT (tv_distance / record_distance). Both iterate ONLY ``Pa1``'s keys, so
they assume Pa1 and Pa2 share the SAME support (the docstring's "shared 64-key support"). The
L1 metric-axiom test therefore exercises them only on equal-support pairs (``joint3`` x
``joint3``, the same 64 keys) and asserts bounds + symmetry + ``rd <= 2*tv``; the unqualified
"==0 iff equal" over ARBITRARY dicts is NOT a theorem here (mismatched support silently misses
keys or raises KeyError) and is deliberately NOT claimed.

exact_cmi_bits `if den>0 and num>0` is a LIVE guard, not dead code (review finding 2). den =
P12*P23 and num = p*P2 use marginals recomputed from P_all, so for a WELL-SCALED term den,num>0;
but a valid non-negative normalized distribution with a TINY term (e.g.
{(0,0,0):1e-200,(1,1,1):1-1e-200}) UNDERFLOWS num=p*P2 to exactly 0.0, so the False arc IS
reachable -- the guard then correctly contributes 0.0 (not log2(0/0)=nan). That arc is covered
honestly by ``test_L0_exact_cmi_bits_underflow_reaches_guard_false_arc`` (no exemption).

Two-sided teeth (Side-A, KILLER). The load-bearing L1 asserts (CMI>=0, mass preservation,
K>=0, M_mem==0-on-markov) are each shown DISCRIMINATING: an inlined sabotaged variant VIOLATES
the property on a crafted input, so the property is not vacuous (feedback-devious-tests-killer-standard).
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from error_coupling_simulator.quantum_bath import observables as obs

ALPHA = obs.M_ALPHABET                      # [(0,0),(0,1),(1,0),(1,1)]
JOINT_KEYS = list(itertools.product(ALPHA, repeat=3))          # 64 joint (X,Z) keys
BIN_KEYS = list(itertools.product((0, 1), repeat=3))           # 8 binary keys


# --------------------------------------------------------------------------- #
# builders (shared, deterministic; NOT ad-hoc -- the batch's fixtures)        #
# --------------------------------------------------------------------------- #
def _normalize(d: dict) -> dict:
    s = sum(d.values())
    return {k: v / s for k, v in d.items()}


def _exact_2marg(P_all: dict, i: int, j: int) -> dict:
    """Exact 2-marginal of a 3-round joint onto positions (i, j)."""
    out: dict = {}
    for k, v in P_all.items():
        key = (k[i], k[j])
        out[key] = out.get(key, 0.0) + v
    return out


def _markov1_joint(P1, T):
    """P(s1,s2,s3) = P1[s1] * T[s1][s2] * T[s2][s3] over a symbol set -> CMI = M_mem = 0."""
    syms = list(P1)
    return {(a, b, c): P1[a] * T[a][b] * T[b][c]
            for a in syms for b in syms for c in syms}


# =========================================================================== #
# L0 -- per-unit statement + branch coverage (explicit, crafted inputs)       #
# =========================================================================== #
def test_L0_K_stat_joint_runs_and_is_zero_on_exact_marginal():
    P_all = _normalize({k: 1.0 + (i % 3) for i, k in enumerate(JOINT_KEYS)})
    P_skip = _exact_2marg(P_all, 0, 2)                 # exact (m1, m3) marginal
    assert obs.K_stat_joint(P_all, P_skip) == pytest.approx(0.0, abs=1e-12)
    # a NON-marginal skip gives a strictly positive, finite K (comprehension body runs)
    P_skip_bad = {k: 1.0 / len(P_skip) for k in P_skip}
    assert obs.K_stat_joint(P_all, P_skip_bad) > 0.0


def test_L0_project_axis_both_axes_and_key_collision():
    # two DISTINCT joint keys that collapse to the SAME projected key on axis 0 (X):
    #   ((0,0),(0,1),(0,0)) and ((0,1),(0,0),(0,1))  -> X-projection (0,0,0) for BOTH
    # so the second insert exercises out.get(nk, existing) (the accumulation arc);
    # a fresh key exercises out.get(nk, 0.0) (the default arc).
    P = {((0, 0), (0, 1), (0, 0)): 0.4,
         ((0, 1), (0, 0), (0, 1)): 0.35,
         ((1, 1), (1, 0), (1, 1)): 0.25}
    x = obs.project_axis(P, 0)
    z = obs.project_axis(P, 1)
    assert x[(0, 0, 0)] == pytest.approx(0.75)          # 0.4 + 0.35 collided
    assert x[(1, 1, 1)] == pytest.approx(0.25)
    assert z[(0, 1, 0)] == pytest.approx(0.4)
    assert sum(x.values()) == pytest.approx(1.0)        # mass preserved
    assert sum(z.values()) == pytest.approx(1.0)


def test_L0_K_stat_binary_runs_and_is_zero_on_exact_marginal():
    P_all = _normalize({k: 1.0 + (i % 4) for i, k in enumerate(BIN_KEYS)})
    P_skip = {}
    for (s1, s2, s3), v in P_all.items():
        P_skip[(s1, s3)] = P_skip.get((s1, s3), 0.0) + v
    assert obs.K_stat_binary(P_all, P_skip) == pytest.approx(0.0, abs=1e-12)


def test_L0_M_mem_stat_covers_both_ternary_arcs():
    # normal arc: a generic joint with a nonzero middle marginal (denom > 1e-15).
    P_all = _normalize({k: 1.0 + (i % 5) for i, k in enumerate(BIN_KEYS)})
    assert obs.M_mem_stat(P_all) >= 0.0
    # else arc (denom <= 1e-15): a joint whose middle outcome s2=1 has ZERO marginal,
    # supplied as an EXPLICIT p==0 key so the loop still visits it -> denom=0 -> else 0.0.
    P_zero_mid = {(0, 0, 0): 0.5, (1, 0, 1): 0.5, (0, 1, 0): 0.0}
    assert obs.M_mem_stat(P_zero_mid) >= 0.0             # the else branch does not blow up


def test_L0_exact_cmi_bits_covers_p_zero_and_body():
    # a joint with an EXPLICIT p==0 key (skip arc of `if p>0`) plus p>0 keys (body arc).
    base = _normalize({k: 1.0 + (i % 5) for i, k in enumerate(BIN_KEYS)})
    P_all = dict(base)
    a_key = BIN_KEYS[0]
    P_all = {k: (0.0 if k == a_key else v) for k, v in P_all.items()}
    P_all = _normalize({k: v for k, v in P_all.items()})   # renormalize the rest
    P_all[a_key] = 0.0                                      # keep the explicit zero key
    val = obs.exact_cmi_bits(P_all)
    assert val >= -1e-9                                     # CMI non-negative


def test_L0_exact_cmi_bits_underflow_reaches_guard_false_arc():
    # the `if den>0 and num>0` guard's False arc, reached by a VALID non-negative normalized
    # distribution whose tiny term underflows num=p*P2 to exactly 0.0 (review finding 2:
    # the arc is LIVE, not dead). The big term takes the True arc; result stays finite.
    P_all = {(0, 0, 0): 1e-200, (1, 1, 1): 1.0 - 1e-200}
    # precondition: the tiny term's num really does underflow to 0.0 (else this test is
    # vacuous -- it would not exercise the False arc).
    p_tiny = P_all[(0, 0, 0)]
    p2_mid0 = sum(v for k, v in P_all.items() if k[1] == 0)   # P2[(0,)]
    assert p_tiny > 0.0 and p_tiny * p2_mid0 == 0.0, "underflow precondition not met"
    val = obs.exact_cmi_bits(P_all)
    assert math.isfinite(val) and val >= -1e-9


def test_L0_tv_and_record_distance_run():
    Pa = _normalize({k: 1.0 + (i % 3) for i, k in enumerate(JOINT_KEYS)})
    Pb = _normalize({k: 1.0 + ((i + 1) % 3) for i, k in enumerate(JOINT_KEYS)})
    assert 0.0 <= obs.tv_distance(Pa, Pb) <= 1.0
    assert 0.0 <= obs.record_distance(Pa, Pb) <= 1.0
    assert obs.tv_distance(Pa, Pa) == pytest.approx(0.0)
    assert obs.record_distance(Pa, Pa) == pytest.approx(0.0)


# =========================================================================== #
# L1 -- Hypothesis faithfulness properties (thousands of generated inputs)     #
# =========================================================================== #
@st.composite
def joint3(draw, keys=JOINT_KEYS):
    """A valid 3-round joint distribution over `keys` (non-negative, sums to 1)."""
    raw = draw(st.lists(st.floats(min_value=0.0, max_value=1.0,
                                  allow_nan=False, allow_infinity=False),
                        min_size=len(keys), max_size=len(keys)))
    tot = sum(raw)
    assume_nonzero = tot > 1e-9
    if not assume_nonzero:                     # degenerate all-zero draw -> make uniform
        raw = [1.0] * len(keys)
        tot = float(len(keys))
    return {k: raw[i] / tot for i, k in enumerate(keys)}


@st.composite
def binary_transition(draw):
    """A binary Markov-1 (P1, T) with strictly-positive rows (so marginals never vanish)."""
    a = draw(st.floats(min_value=0.15, max_value=0.85))
    t00 = draw(st.floats(min_value=0.15, max_value=0.85))
    t10 = draw(st.floats(min_value=0.15, max_value=0.85))
    P1 = {0: a, 1: 1.0 - a}
    T = {0: {0: t00, 1: 1.0 - t00}, 1: {0: t10, 1: 1.0 - t10}}
    return P1, T


@settings(max_examples=200, deadline=None)
@given(joint3())
def test_L1_cmi_is_nonnegative(P_all):
    """The crown property: conditional mutual information I(s1;s3|s2) >= 0 (a theorem)."""
    assert obs.exact_cmi_bits(P_all) >= -1e-9


@settings(max_examples=200, deadline=None)
@given(joint3())
def test_L1_m_mem_is_nonnegative(P_all):
    assert obs.M_mem_stat(P_all) >= 0.0


@settings(max_examples=200, deadline=None)
@given(joint3())
def test_L1_k_joint_zero_on_exact_marginal_and_nonneg(P_all):
    assert obs.K_stat_joint(P_all, _exact_2marg(P_all, 0, 2)) == pytest.approx(0.0, abs=1e-9)
    # K is a sum of absolute values -> non-negative for any skip
    P_skip_any = {(a, c): 1.0 / (len(ALPHA) ** 2) for a in ALPHA for c in ALPHA}
    assert obs.K_stat_joint(P_all, P_skip_any) >= 0.0


@settings(max_examples=200, deadline=None)
@given(joint3(keys=BIN_KEYS))
def test_L1_k_binary_zero_on_exact_marginal_and_nonneg(P_all):
    skip = {}
    for (s1, s2, s3), v in P_all.items():
        skip[(s1, s3)] = skip.get((s1, s3), 0.0) + v
    assert obs.K_stat_binary(P_all, skip) == pytest.approx(0.0, abs=1e-9)   # exact marginal
    skip_any = {(s1, s3): 0.25 for s1 in (0, 1) for s3 in (0, 1)}
    assert obs.K_stat_binary(P_all, skip_any) >= 0.0                        # sum of |.| >= 0


@settings(max_examples=200, deadline=None)
@given(binary_transition())
def test_L1_cmi_and_mmem_vanish_on_markov1_chain(pt):
    P1, T = pt
    P_all = _markov1_joint(P1, T)                 # exact Markov-1 -> I(s1;s3|s2) = 0
    assert obs.exact_cmi_bits(P_all) == pytest.approx(0.0, abs=1e-9)
    assert obs.M_mem_stat(P_all) == pytest.approx(0.0, abs=1e-9)


@settings(max_examples=200, deadline=None)
@given(joint3())
def test_L1_project_axis_preserves_mass_and_key_length(P_all):
    for which in (0, 1):
        proj = obs.project_axis(P_all, which)
        assert sum(proj.values()) == pytest.approx(sum(P_all.values()), abs=1e-9)
        for k in proj:                             # projected keys keep the round count
            assert len(k) == 3


@settings(max_examples=200, deadline=None)
@given(joint3(), joint3())
def test_L1_tv_and_record_distance_metric_axioms(Pa, Pb):
    tv, rd = obs.tv_distance(Pa, Pb), obs.record_distance(Pa, Pb)
    assert 0.0 - 1e-12 <= tv <= 1.0 + 1e-12
    assert 0.0 - 1e-12 <= rd <= 1.0 + 1e-12
    assert obs.tv_distance(Pa, Pb) == pytest.approx(obs.tv_distance(Pb, Pa))   # symmetric
    assert obs.record_distance(Pa, Pb) == pytest.approx(obs.record_distance(Pb, Pa))
    assert rd <= 2.0 * tv + 1e-12                  # max|d| <= sum|d| = 2*TV


# =========================================================================== #
# KILLER (Side-A teeth) -- prove the load-bearing asserts DISCRIMINATE          #
# =========================================================================== #
def _buggy_cmi_inverted_ratio(P_all):
    """Sabotage: invert the log ratio (log2(den/num), not log2(num/den)) -- a single-token
    mutation that NEGATES the CMI, so it goes strictly negative whenever the true CMI > 0.
    (NB: the 'drop the P2 marginal factor' mutation does NOT break >=0 -- it adds
    -sum p log2(P2) >= 0, staying non-negative; the sign-inverting mutation is the honest
    teeth for the non-negativity property.)"""
    def marg(idxs):
        d: dict = {}
        for k, v in P_all.items():
            key = tuple(k[i] for i in idxs)
            d[key] = d.get(key, 0.0) + v
        return d
    P12, P23, P2 = marg([0, 1]), marg([1, 2]), marg([1])
    c = 0.0
    for (s1, s2, s3), p in P_all.items():
        if p > 0.0:
            num = p * P2[(s2,)]
            den = P12[(s1, s2)] * P23[(s2, s3)]
            if den > 0.0 and num > 0.0:
                c += p * math.log2(den / num)      # <-- inverted ratio (negates CMI)
    return float(c)


def test_KILLER_cmi_nonneg_would_fail_for_inverted_ratio_variant():
    # a strongly-correlated joint whose true CMI > 0; the sign-inverting mutant goes
    # strictly NEGATIVE while the real one stays >= 0 -- so test_L1_cmi_is_nonnegative has
    # TEETH (it is not vacuous). Given s2, (s1,s3) are correlated on both s2 branches.
    P_all = {(0, 0, 0): 0.45, (1, 1, 1): 0.45, (0, 1, 0): 0.05, (1, 0, 1): 0.05}
    real = obs.exact_cmi_bits(P_all)
    assert real > 1e-6                                        # real: strictly positive CMI
    assert _buggy_cmi_inverted_ratio(P_all) == pytest.approx(-real, abs=1e-9)  # mutant = -CMI
    assert _buggy_cmi_inverted_ratio(P_all) < -1e-6          # mutant: strictly negative


def test_KILLER_project_axis_mass_would_fail_for_overwrite_variant():
    # a buggy project that OVERWRITES instead of accumulating loses mass on a collision;
    # prove the mass-preservation assert would catch it.
    P = {((0, 0), (0, 1), (0, 0)): 0.4,
         ((0, 1), (0, 0), (0, 1)): 0.35,
         ((1, 1), (1, 0), (1, 1)): 0.25}
    real = obs.project_axis(P, 0)
    buggy = {}
    for key, v in P.items():
        buggy[tuple(m[0] for m in key)] = v                  # overwrite (no +=)
    assert sum(real.values()) == pytest.approx(1.0)          # real preserves mass
    assert sum(buggy.values()) < 1.0 - 1e-6                  # mutant drops the collided mass


def test_KILLER_k_stat_nonneg_would_fail_for_dropped_abs_variant():
    # An OVER-normalized skip (sums to 2, not 1) makes the SIGNED sum strictly negative:
    # sum_over_all(marg - skip) = sum(marg) - sum(skip) = 1 - 2 = -1 < 0. The real K (with
    # abs) stays >= 0, so a mutant that drops abs() would VIOLATE the K>=0 property. This is
    # the honest teeth for non-negativity (the earlier 'one bucket = 0.5' skip left signed
    # POSITIVE, so it did not exercise the sign).
    P_all = _normalize({k: 1.0 + (i % 3) for i, k in enumerate(JOINT_KEYS)})
    P_skip_over = {(a, c): 2.0 / (len(ALPHA) ** 2) for a in ALPHA for c in ALPHA}  # sums to 2
    real = obs.K_stat_joint(P_all, P_skip_over)
    signed = float(sum(sum(P_all[(m1, m2, m3)] for m2 in ALPHA) - P_skip_over[(m1, m3)]
                       for m1 in ALPHA for m3 in ALPHA))
    assert real >= 0.0                                        # real: abs() -> non-negative
    assert signed < -1e-9                                     # mutant (no abs): strictly < 0


def _buggy_mmem_no_divide(P_all):
    """Sabotage: forget the /P2 conditional (P12*P23 instead of P12*P23/P2). Breaks
    ==0-on-Markov-1: leaves sum_k p*(1 - P2[s2]) > 0 on a Markov chain."""
    def marg(idxs):
        d: dict = {}
        for k, v in P_all.items():
            key = tuple(k[i] for i in idxs)
            d[key] = d.get(key, 0.0) + v
        return d
    P12, P23 = marg([0, 1]), marg([1, 2])
    m = 0.0
    for (s1, s2, s3), p in P_all.items():
        m += abs(p - P12[(s1, s2)] * P23[(s2, s3)])           # <-- missing / P2[(s2,)]
    return float(m)


def test_KILLER_mmem_zero_on_markov1_would_fail_for_no_divide_variant():
    # M_mem_stat >= 0 is trivial (sum of abs); its DISCRIMINATING content is ==0 on a Markov-1
    # chain. Show that teeth: the no-divide mutant is strictly > 0 on a Markov chain where the
    # real statistic is 0.
    P1 = {0: 0.6, 1: 0.4}
    T = {0: {0: 0.7, 1: 0.3}, 1: {0: 0.4, 1: 0.6}}
    P_all = _markov1_joint(P1, T)
    assert obs.M_mem_stat(P_all) == pytest.approx(0.0, abs=1e-9)   # real: Markov -> 0
    assert _buggy_mmem_no_divide(P_all) > 1e-6                     # mutant: nonzero on Markov

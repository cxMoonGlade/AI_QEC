"""H1 (HARDEN): the coherent hidden-failure axis, built on H0's frozen mixed teacher.

Two claims, both pre-registered (derived before running):

  Claim 1 -- the alias LIFTS, witnessed by the scale-free EXPONENT. Along the
    per-location iso-Z-marginal coherence direction, profile-NLL ~ h^p: p=4 (a
    2nd-order Fisher null -> coherence aliased) at r=1 for the pure-coherent loc0,
    lifting to p=2 (resolved) at the first phase-sensitive rung. The exponent flip
    4->2 is the unit-free witness; kappa magnitude is REPORTED, never targeted.
    Per-location gradient: loc0 (pure RX) clean null; loc1 (RX-in-AmpDamp) the
    non-unital FINDING; loc2 (stochastic) the always-resolved anchor.

  Claim 2 -- one recovered E_hat, two functionals. The SAME low-r E_hat (calib_KL~0,
    the precondition that makes this the hidden-failure cell and not an ordinary bad
    fit) gives the RIGHT do(E->I) dLER but the WRONG exotic (phase-sensitive)
    prediction -- the converse decision-regret statement (null on one functional,
    projects onto the other). The low-r exotic error sits at the moment-matched
    (Pauli-twirl) SHADOW scale; it collapses when basis-rotated probes enter.

Result (run 2026-06-09).
  Claim 1: loc0 p=4.00@r1 -> 2.00@r2 (lifts at r=2, the repeated-storage rung); loc1
    p~2.0 at every r (no clean null -- non-unitality + both-bases resolve it early);
    loc2 p~2.1 (anchor). CONTROLS -> a sharper finding: loc0's r=1 null PERSISTS
    under IDENTITY neighbors (exp 4, KL ~ the mixed curve) -- it is the geometric /
    observation-map default -- and is resolved ONLY by a COHERENT backdrop
    (pure-coherent teacher, exp 2.01, KL ~100x larger). So it is a coherence-mediated
    OBSERVATION-MAP effect under a FACTORIZED teacher, NOT channel/generator coupling;
    H2 escalates to a non-factorized generator (the H1->H2 link is conceptual).
  Claim 2 at k=1: calib_kl=2.2e-9 (good fit), B_LER=2.6e-7 (do RIGHT),
    exotic_err=0.205 (pred WRONG); exotic/twirl-shadow=1.07 (shadows like the twirl);
    exotic collapses 24x by k=3.
  NUANCE kept honestly: the iso-marginal Fisher alias lifts at r=2 (accumulation) but
    the out-of-basis exotic prediction only collapses at r=3 (basis-rotation) -- two
    facets of the coherence, two rungs; and the exotic shadow penalty (~24x) is NOT
    the do-functional's ~942x (different functional, larger high-r floor).

Metrics: calib_KL = calibrate(...)["total_kl"]; do/exotic via audit.validity
predict_held_out_curve; profile-NLL via calibration.nll.joint_kl. See docs/METRICS.md.
"""

from __future__ import annotations

import math

import pytest

from qec_twin.audit.validity import predict_held_out_curve
from qec_twin.calibration.nll import joint_kl
from qec_twin.contexts.ladder import (
    calibration_contexts,
    held_out_eval_context,
    held_out_exotic_contexts,
    run_context,
)
from qec_twin.knobs.intervention import build_frozen_decoder
from qec_twin.mechanisms.teachers import (
    amplitude_damped_rotation_kraus,
    coherent_overrotation_field,
    coherent_overrotation_kraus,
    mixed_mechanism_field,
    pauli_twirl_field,
)
from qec_twin.forward.exact.circuit_sim import bit_flip

# H0's frozen mixed teacher -- H1 is its held-out-r continuation.
H0_SPECS = [("coherent", 0.03, 0.6), ("damped", 0.05, 0.5), ("pauli", 0.04)]
HS = (0.02, 0.01, 0.005)        # loc0 / loc2 steps
HS1 = (0.008, 0.004, 0.002)     # loc1: smaller (iso-marginal slope ~3.7 is steep -> keep gamma>=0)


def _total_kl_at(i, kraus_i, base, contexts, teacher_fwd) -> float:
    field = lambda t, j: (kraus_i if j == i else base[j])  # noqa: E731
    return sum(
        float(joint_kl(tf, run_context(c, channel_field=field)))
        for c, tf in zip(contexts, teacher_fwd)
    )


def _exponent(i, pert_plus, pert_minus, base, contexts, teacher_fwd, hs=HS) -> float:
    # central-difference profile NLL at each step; slope of log(KL) vs log(h).
    kls = [
        0.5 * (_total_kl_at(i, pert_plus(h), base, contexts, teacher_fwd)
               + _total_kl_at(i, pert_minus(h), base, contexts, teacher_fwd))
        for h in hs
    ]
    return math.log(kls[0] / kls[2]) / math.log(hs[0] / hs[2])


def _loc0_dirs(p, t):
    # iso-Z-marginal f = p + (1-2p) sin^2(t/2); dp = -c dt.
    c = ((1 - 2 * p) * 0.5 * math.sin(t)) / math.cos(t)
    return (lambda h: coherent_overrotation_kraus(p - c * h, t + h),
            lambda h: coherent_overrotation_kraus(p + c * h, t - h))


def _loc1_dirs(g, t):
    # iso-|0>-marginal f = (1-g) sin^2(t/2); dg = (1-g) cot(t/2) dt.
    s = (1 - g) * math.cos(t / 2) / math.sin(t / 2)
    return (lambda h: amplitude_damped_rotation_kraus(g + s * h, t + h),
            lambda h: amplitude_damped_rotation_kraus(g - s * h, t - h))


def _loc2_dirs(q):
    return (lambda h: bit_flip(q + h), lambda h: bit_flip(q - h))


@pytest.fixture(scope="module")
def exponents():
    teacher = mixed_mechanism_field(H0_SPECS)
    base = [teacher(0, i) for i in range(3)]
    out = {}
    for r in (1, 2, 3):
        ctx = calibration_contexts(r)
        tf = [run_context(c, channel_field=teacher) for c in ctx]
        p0 = _exponent(0, *_loc0_dirs(0.03, 0.6), base, ctx, tf)
        out[("loc0", r)] = p0
        if r == 1:  # loc1/loc2 only need the r=1 read (anchor + non-unital finding)
            out[("loc1", 1)] = _exponent(1, *_loc1_dirs(0.05, 0.5), base, ctx, tf, hs=HS1)
            out[("loc2", 1)] = _exponent(2, *_loc2_dirs(0.04), base, ctx, tf)
    return out


def test_h1_loc0_coherent_null_lifts_4_to_2(exponents):
    # Claim 1, primary: pure-coherent loc0 is a 2nd-order null at r=1 (p~4), lifting
    # to ordinary curvature (p~2) at r=2 -- the scale-free exponent-flip witness.
    assert exponents[("loc0", 1)] > 3.5
    assert exponents[("loc0", 2)] < 2.5
    assert exponents[("loc0", 3)] < 2.5


def test_h1_loc1_nonunital_has_no_clean_null(exponents):
    # Claim 1, the FINDING: the unital coherent null does NOT transfer to the
    # non-unital T1+coherent loc1 -- its analogous iso-marginal direction is already
    # ordinary-curved (p~2) at r=1 (non-unitality + both-bases resolve it early).
    assert exponents[("loc1", 1)] < 2.5


def test_h1_loc2_stochastic_anchor_is_always_resolved(exponents):
    # Claim 1, anchor: the stochastic location is resolved (p~2) at every r.
    assert 1.7 < exponents[("loc2", 1)] < 2.4


def test_h1_loc0_null_is_backdrop_dependent():
    # Isolation control -- the prediction REVERSED into a finding: a pure-coherent
    # teacher does NOT reproduce the mixed teacher's r=1 loc0 null. Same loc0
    # mechanism, but exp~2 (resolved; KL ~100x larger, well above the 1e-12 floor)
    # vs the mixed backdrop's exp~4. The coherent Fisher null is BACKDROP-DEPENDENT,
    # so cross-location terms matter for coherent identifiability -- this feeds H2.
    teacher = coherent_overrotation_field([0.03, 0.03, 0.03], [0.6, 0.6, 0.6])
    base = [teacher(0, i) for i in range(3)]
    ctx = calibration_contexts(1)
    tf = [run_context(c, channel_field=teacher) for c in ctx]
    exp_r1 = _exponent(0, *_loc0_dirs(0.03, 0.6), base, ctx, tf)
    assert 1.5 < exp_r1 < 2.5  # resolved at r=1 -- diverges from the mixed teacher's exp~4


def test_h1_loc0_null_is_geometric_not_channel_coupling():
    # Disambiguates the backdrop-dependence (same apparatus, identity neighbors):
    # with loc1/loc2 = IDENTITY, loc0's r=1 null PERSISTS (exp~4, KL ~ the mixed
    # curve). So the null is the geometric default of the 3-location observation map,
    # NOT generic neighbor channel-coupling -- the dissipative/stochastic neighbors
    # have ~zero effect on loc0's coherence. Only a coherent backdrop resolves it
    # (the test above). => H1's coupling is in the observation map under a FACTORIZED
    # teacher; H2's novelty is a non-factorized GENERATOR.
    p, t = 0.03, 0.6
    loc0 = coherent_overrotation_kraus(p, t)
    teacher = lambda tt, j: (loc0 if j == 0 else None)  # noqa: E731 -- loc1/loc2 = identity
    base = [teacher(0, j) for j in range(3)]
    ctx = calibration_contexts(1)
    tf = [run_context(c, channel_field=teacher) for c in ctx]
    exp_r1 = _exponent(0, *_loc0_dirs(p, t), base, ctx, tf)
    assert exp_r1 > 3.5  # null persists under identity neighbors -> geometric, not channel-coupling


@pytest.fixture(scope="module")
def two_functionals():
    teacher = mixed_mechanism_field(H0_SPECS)
    eval_ctx = held_out_eval_context()
    decoder = build_frozen_decoder(eval_ctx)
    curve = predict_held_out_curve(
        teacher, eval_context=eval_ctx, decoder=decoder,
        levels=(1, 2, 3), num_kraus=3, steps=300, seed=0,
    )["curve"]
    exotic = held_out_exotic_contexts()
    teacher_exotic = [run_context(c, channel_field=teacher) for c in exotic]
    twirl = pauli_twirl_field(teacher, 3)
    mm_exotic = max(
        float(joint_kl(te, run_context(c, channel_field=twirl)))
        for c, te in zip(exotic, teacher_exotic)
    )
    return {row["k"]: row for row in curve}, mm_exotic


def test_h1_precondition_good_fit_at_low_r(two_functionals):
    # Claim 2 precondition (guard against false collapse): calib_KL~0 at every level,
    # so a wrong exotic prediction is HIDDEN failure, not an ordinary bad fit.
    rows, _ = two_functionals
    for k in (1, 2, 3):
        assert rows[k]["calib_kl"] < 1e-6


def test_h1_one_ehat_two_functionals(two_functionals):
    # Claim 2 core: the SAME low-r E_hat gives the RIGHT do() but the WRONG exotic.
    rows, _ = two_functionals
    assert rows[1]["B_LER_max"] < 1e-4            # do(E->I) is right (phase-insensitive)
    assert rows[1]["exotic_obs_error_max"] > 0.05  # exotic prediction is wrong (shadowed)


def test_h1_low_r_twin_shadows_like_the_twirl(two_functionals):
    # Claim 2 shadow tie: the low-r exotic error sits at the moment-matched Pauli-twirl
    # scale -- the exact-NLL twin Pauli-shadows the coherence out of basis.
    rows, mm_exotic = two_functionals
    assert 0.5 < rows[1]["exotic_obs_error_max"] / mm_exotic < 2.0


def test_h1_exotic_collapses_with_basis_rotated_probes(two_functionals):
    # Claim 2 collapse: the exotic error falls sharply once basis-rotated (r=3) probes
    # enter, while do() stays right and calib_KL stays ~0 (functionals, not fit).
    rows, _ = two_functionals
    assert rows[1]["exotic_obs_error_max"] / rows[3]["exotic_obs_error_max"] > 10.0
    assert rows[3]["B_LER_max"] < 1e-4

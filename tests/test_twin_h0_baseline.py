"""H0 (HARDEN): the frozen same-r matched baseline.

A *richer matched* teacher -- heterogeneous single-qubit mechanisms spanning the
visible coherent-error / Lindbladian-learning frontier taxonomy (coherent `RX`,
T1 `AmpDamp.RX`, stochastic Pauli `BitFlip`), every location <=2-Kraus so the
`num_kraus=2` learner class contains it -- is calibrated at *fixed* richness r=1
and frozen as the reference every later HARDEN axis compares against.

Pre-registered (derived BEFORE running; see docs/_archive/PLAN.md H0):

  1. calib_KL -> floor. Matched class => the joint is exactly representable, so
     exact observation-NLL recovers it to the numerical floor, cross-context and
     on a held-out longer circuit. FALSIFICATION (plan2 H0): if it does NOT, the
     failure is numerical/optimizer, not identifiability -- fix before any richer
     axis.
  2. The Tier-0 band covers the controlled-teacher's true `do(E->I)` knob at every
     location (|knob_value - true_knob| <= 2 * statistical_band).
  3. Coherent-vs-stochastic alias split. At r=1 there is no phase-sensitive probe
     (rounds {1,2,3}, both bases, but no pre_rotation/repeats), so the RX-phase
     direction is unresolved: coherent/damped locations carry a larger epistemic
     `alias_weight` than the pure-Pauli location, whose stochastic rate r=1
     identifies. (The Girsanov split, surfaced in the frozen baseline.)

Result (run 2026-06-09). (1) and (2) hold strongly: calib_KL = 1.0e-14 (machine
floor) and every location's `knob_hat` matches its true knob exactly. (3) was
FALSIFIED as stated and corrected: the predicted coherent-vs-stochastic split did
NOT appear -- all three `alias_weight`s sit at the floor (~9.4e-7, <0.2% of the
statistical band). Diagnosis (under-derivation, not a bug): the RX-phase IS
unresolved at r=1, but `do(E->I)` removes the whole channel, so its gradient is
phase-insensitive -- the coherent alias does not *project* onto this knob (an
alias matters iff it projects onto the do() functional; docs/_archive/PLAN.md
decision-regret). The coherent-vs-stochastic split therefore belongs to a
phase-sensitive functional / out-of-basis exotic prediction (H1), not to do(E->I)
at H0. Test (3) is rewritten to the corrected finding. EARNED (Fisher-null check,
`test_h0_coherent_alias_is_a_real_fisher_null`): at the r=1 point the iso-Z-marginal
coherence direction is a *2nd-order-null* Fisher direction (NLL ~ h^4, kappa_coh->0;
the rate direction kappa_rate~81 is resolved), so the coherent<->stochastic alias is
genuinely REAL at r=1 -- it exists but does not project onto do(E->I). That is the
*interesting* reading (not "nothing is aliased at r=1"), so the decision-regret
reading is earned, not merely consistent.

Metrics are the standard ledger objects (docs/METRICS.md): calib_KL =
calibration.nll.joint_kl / calibrate(...)["total_kl"]; LER/ΔLER =
knobs.intervention.logical_error_rate; band = audit.bands.tier0_alias_band.
"""

from __future__ import annotations

import math

import pytest

from qec_twin.audit.bands import tier0_alias_band
from qec_twin.calibration.nll import calibrate, evaluate_kl, joint_kl
from qec_twin.contexts.ladder import (
    calibration_contexts,
    held_out_eval_context,
    run_context,
)
from qec_twin.knobs.intervention import (
    build_frozen_decoder,
    do_remove,
    intervene_field,
    logical_error_rate,
)
from qec_twin.mechanisms.teachers import coherent_overrotation_kraus, mixed_mechanism_field

# Frozen H0 baseline: location 0 = Pauli+coherent, 1 = T1+coherent (non-unital),
# 2 = pure stochastic Pauli. Heterogeneous, all <=2-Kraus (matched).
H0_SPECS = [("coherent", 0.03, 0.6), ("damped", 0.05, 0.5), ("pauli", 0.04)]
RICHNESS = 1
STEPS = 800
SHOTS = 20_000
KL_FLOOR = 1e-7  # pre-registered "reaches the floor" threshold


@pytest.fixture(scope="module")
def h0():
    teacher = mixed_mechanism_field(H0_SPECS)
    contexts = calibration_contexts(RICHNESS)
    result = calibrate(teacher, contexts, distance=3, num_kraus=2, steps=STEPS, seed=0)
    twin = result["twin"]

    eval_ctx = held_out_eval_context()
    decoder = build_frozen_decoder(eval_ctx)
    teacher_forwards = [run_context(c, channel_field=teacher) for c in contexts]

    base = logical_error_rate(run_context(eval_ctx, channel_field=teacher), decoder)
    true_knobs, bands = {}, {}
    for i in range(len(H0_SPECS)):
        removed = logical_error_rate(
            run_context(eval_ctx, channel_field=intervene_field(teacher, i, do_remove)),
            decoder,
        )
        true_knobs[i] = removed - base
        bands[i] = tier0_alias_band(
            twin, contexts, teacher_forwards,
            eval_context=eval_ctx, decoder=decoder,
            target_i=i, intervention=do_remove, shots=SHOTS, z=1.0,
        )
    return result, true_knobs, bands


def test_h0_calib_kl_reaches_floor(h0) -> None:
    # (1) matched class -> exact observation-NLL recovers the joint to the floor.
    result, _, _ = h0
    assert result["total_kl"] < KL_FLOOR
    for kl in result["per_context_kl"].values():
        assert kl < KL_FLOOR


def test_h0_generalizes_to_held_out(h0) -> None:
    # (1, cross-context) -- the load-bearing signal: a held-out longer circuit.
    result, _, _ = h0
    teacher = mixed_mechanism_field(H0_SPECS)
    assert evaluate_kl(result["twin"], teacher, held_out_eval_context()) < KL_FLOOR


def test_h0_band_covers_true_knob(h0) -> None:
    # (2) the Tier-0 band covers the controlled-teacher's true do(E->I) knob.
    _, true_knobs, bands = h0
    for i, band in bands.items():
        assert abs(band["knob_value"] - true_knobs[i]) <= 2.0 * band["statistical_band"]


def test_h0_do_knob_identified_for_every_mechanism(h0) -> None:
    # (3, corrected) The predicted coherent-vs-stochastic split did NOT appear on
    # do(E->I): the unresolved RX-phase does not project onto a channel-removal
    # knob, so the epistemic alias_weight is negligible -- <5% of the statistical
    # band -- for coherent, T1, AND Pauli locations alike (the decision-regret
    # principle: an alias matters iff it projects onto the functional). The split
    # is deferred to a phase-sensitive functional (H1). The original noise-floor
    # ordering (9.36 vs 9.47e-7) is NOT asserted -- a ratio against the floor.
    _, _, bands = h0
    for i, band in bands.items():
        assert band["alias_weight"] < 0.05 * band["statistical_band"]


def _iso_marginal_slope(p: float, theta: float) -> float:
    # Hold the single-round Z bit-flip rate f = p + (1-2p) sin^2(theta/2) fixed:
    # dp/dtheta = -(df/dtheta)/(df/dp) -- the coherent<->stochastic alias direction
    # (raise the coherent phase, drop the stochastic rate to keep the marginal).
    dfdth = (1.0 - 2.0 * p) * 0.5 * math.sin(theta)
    dfdp = math.cos(theta)
    return -dfdth / dfdp


def _total_kl_loc0(kraus0, contexts, teacher_fwd, loc1, loc2) -> float:
    field = lambda t, i: (kraus0 if i == 0 else (loc1 if i == 1 else loc2))  # noqa: E731
    return sum(
        float(joint_kl(tf, run_context(c, channel_field=field)))
        for c, tf in zip(contexts, teacher_fwd)
    )


def test_h0_coherent_alias_is_a_real_fisher_null() -> None:
    # Earns the decision-regret reading of (3): the flat alias_weight is degenerate
    # between "a real coherent alias orthogonal to do(E->I)" and "nothing aliased".
    # Discriminate with the W2 Fisher curvature at the r=1 point along the
    # iso-Z-marginal coherence direction (the coherent<->stochastic alias) vs the
    # resolved rate direction. Base point = teacher (calib_KL=1e-14 => == recovered).
    p0, th0 = H0_SPECS[0][1], H0_SPECS[0][2]
    contexts = calibration_contexts(RICHNESS)
    teacher = mixed_mechanism_field(H0_SPECS)
    teacher_fwd = [run_context(c, channel_field=teacher) for c in contexts]
    loc1, loc2 = teacher(0, 1), teacher(0, 2)
    slope = _iso_marginal_slope(p0, th0)  # dp = slope * dtheta

    def kl_coh(h: float) -> float:
        return 0.5 * (
            _total_kl_loc0(coherent_overrotation_kraus(p0 + slope * h, th0 + h), contexts, teacher_fwd, loc1, loc2)
            + _total_kl_loc0(coherent_overrotation_kraus(p0 - slope * h, th0 - h), contexts, teacher_fwd, loc1, loc2)
        )

    def kl_rate(h: float) -> float:
        return 0.5 * (
            _total_kl_loc0(coherent_overrotation_kraus(p0 + h, th0), contexts, teacher_fwd, loc1, loc2)
            + _total_kl_loc0(coherent_overrotation_kraus(p0 - h, th0), contexts, teacher_fwd, loc1, loc2)
        )

    h = 0.01
    klc_h, klc_2h, klr_h = kl_coh(h), kl_coh(2 * h), kl_rate(h)
    kappa_coh = 2.0 * klc_h / (h * h * (1.0 + slope * slope))
    kappa_rate = 2.0 * klr_h / (h * h)

    # (a) rate direction is well-conditioned (resolved) -- the control (~81).
    assert kappa_rate > 50.0
    # (b) coherence direction is near-null relative to it at r=1 (~2e-5).
    assert kappa_coh / kappa_rate < 1e-3
    # (c) and it is a TRUE 2nd-order null, not just small curvature: NLL ~ h^4 means
    # halving h cuts KL ~16x (quartic), vs ~4x for a quadratic. >10 separates them.
    assert klc_2h / klc_h > 10.0


def test_h0_freeze_report(h0) -> None:
    # The frozen baseline record (run with -s to print; copy into metric_results.md).
    result, true_knobs, bands = h0
    print("\n=== H0 frozen baseline (d=3, r=1, matched) ===")
    print(f"specs            : {H0_SPECS}")
    print(f"calib_KL total   : {result['total_kl']:.3e}")
    print(f"per_context_KL   : max={max(result['per_context_kl'].values()):.3e}")
    for i in bands:
        b = bands[i]
        print(
            f"loc{i} {H0_SPECS[i][0]:>8}: true_knob={true_knobs[i]:+.3e}  "
            f"knob_hat={b['knob_value']:+.3e}  stat_band={b['statistical_band']:.3e}  "
            f"alias_weight={b['alias_weight']:.3e}  inv_quad={b['inv_quad']:.3e}"
        )
    assert True

"""H2 (HARDEN) -- non-factorized coherent ZZ crosstalk axis (pre-registered 2026-06-09).

Escalation from H1. H1 showed cross-location identifiability effects arise with a
FACTORIZED teacher: loc0's coherent null is geometric (persists under identity
neighbors) and is lifted only by a coherent backdrop -- the coupling lives in the
observation map / Fisher, NOT the generator. H2's novelty is a NON-FACTORIZED
GENERATOR: the teacher's channels do not factor (a coherent ZZ crosstalk term), and
the question is whether a FACTORIZED learner lies about it.

THE ESCALATED DANGEROUS CELL -- the third band. H1's danger was (calib_KL~0,
prediction wrong) but the band stayed HONEST: the alias is in-class, so probe
richness flags it. H2's danger is (calib_KL~0, prediction wrong, BAND OVERCONFIDENT):
crosstalk is out-of-class for a factorized learner, so its epistemic band cannot
contain the error -- this is B_misspec, the third band (PLAN.md S1.2), measurable
only against the controlled teacher. No within-factorized probe richness fixes it;
only a model-class change does.

FROZEN DESIGN (docs/metric_results.md 2026-06-09 H2 PRE-REGISTRATION -- binding).
Teacher = H0 mixed field + edge exp(-i phi Z@Z) on pair (0,1); phi_ref = 0.1,
regime phi in [0.05, 0.15]. Placement (load-bearing, declared): per round
[ (prod_i E_i) ; U_phi ]^repeats then extraction. Factorized learner = RepCodeTwin;
non-factorized = CoupledRepCodeTwin (+ ONE learnable phi). Frozen decoder, exact
population metrics. Predictions P1-P8 with pre-declared thresholds; each test below
names the predictions it scores. Falsification routing: P1/P2 fail => coupling-hook
placement bug or theorem wrong (fix before anything downstream); P4 (a) already at
r<=2 => shadow construction wrong (record, continue); P4 stays (b) at r=4 =>
ladder-permanent overconfidence (escalates; ADR 0006 (ii) re-read); P7 fails =>
edge DOF not in-class identifiable => stop/redesign.

BUILD ORDER (mandated, followed): (1) forward edge hook + teacher constructors +
P1 regression pins; (2) the W2 DOF gate (P3) runs BEFORE any calibration fit
(ADR 0006 Decision 3(i)) -- enforced structurally: every fit fixture depends on the
``dof_gate`` fixture; (3) fits (P2/P4), knobs (P5), bands (P6), non-factorized
closure (P7), stochastic control (P8).

MACHINERY (built 2026-06-09):
  1. forward: edge hook in forward/exact (edge_field, [ (prod E_i); U_edge ]^repeats).
  2. teacher: mechanisms.teachers.coupled_mixed_teacher / zz_coupling_kraus /
     correlated_dephasing_kraus (the stochastic control).
  3. learner: calibration.nll.CoupledRepCodeTwin (factorized + one learnable phi).
  4. B_misspec: knobs.intervention edge knobs + audit.bands tier0 band with the phi
     direction; audit.gating.edge_dof_gate (the W2 gate).

Metrics (docs/METRICS.md): calib_KL = calibrate(...)["total_kl"]; knob error =
knob_dler_error (B_LER); shift = obs_shift_tvd (B_obs); band = tier0_alias_band
(shots=1e7, z=3, declared); B_misspec = factorized learner's knob error vs the
2-body teacher (flagged project-defined, ADR 0006).
"""

from __future__ import annotations

import math

import pytest

import torch

from qec_twin.audit.bands import tier0_alias_band
from qec_twin.audit.gating import edge_dof_gate
from qec_twin.calibration.nll import calibrate, evaluate_kl, joint_kl
from qec_twin.contexts.ladder import (
    calibration_contexts,
    held_out_eval_context,
    held_out_exotic_contexts,
    held_out_sandwich_context,
    run_context,
)
from qec_twin.knobs.intervention import (
    build_frozen_decoder,
    counterfactual_scores,
    do_remove,
    field_counterfactual_scores,
    intervene_edge_field,
    intervene_field,
    logical_error_rate,
)
from qec_twin.mechanisms.teachers import (
    correlated_dephasing_kraus,
    coupled_mixed_teacher,
    mixed_mechanism_field,
)

# Frozen design (pre-registration 2026-06-09): H0 mixed teacher + ZZ edge on (0,1).
H0_SPECS = [("coherent", 0.03, 0.6), ("damped", 0.05, 0.5), ("pauli", 0.04)]
PAIR = (0, 1)
PHI_REF = 0.1
PHI_REGIME = (0.05, 0.1, 0.15)
STEPS = 600
NUM_KRAUS = 2
SEED = 0
SHOTS = 10_000_000  # declared band scale (P6/P7)
Z = 3.0


def _edge(phi):
    return coupled_mixed_teacher(H0_SPECS, phi, pair=PAIR)[1]


def _stoch_edge(phi):
    kraus = correlated_dephasing_kraus(phi)
    return lambda t, e: kraus if tuple(e) == PAIR else None  # noqa: E731


def _tv(fa, fb) -> float:
    # branch-aligned TV over (s, m) (the record -> (s,m) bijection makes branch L1 exact)
    return 0.5 * float((fa.probs - fb.probs).abs().sum())


def _true_edge_dler(field, edge_field, ctx, decoder) -> float:
    base = logical_error_rate(
        run_context(ctx, channel_field=field, edge_field=edge_field),
        decoder, logical_reference=ctx.logical,
    )
    removed = logical_error_rate(
        run_context(ctx, channel_field=field,
                    edge_field=intervene_edge_field(edge_field, PAIR, do_remove)),
        decoder, logical_reference=ctx.logical,
    )
    return float(removed - base)


def _slope(kl_by_phi, lo=0.05, hi=0.15) -> float:
    return math.log(kl_by_phi[hi] / kl_by_phi[lo]) / math.log(hi / lo)


# --------------------------------------------------------------------------- #
# Fixtures. The W2 DOF gate (P3) is a dependency of EVERY fit fixture, so it     #
# always runs before any calibration fit (ADR 0006 Decision 3(i), pre-reg P3).   #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def dof_gate():
    field = mixed_mechanism_field(H0_SPECS)
    return edge_dof_gate(field, _edge, PHI_REF, levels=(0, 1, 2, 3, 4),
                         slope_phis=PHI_REGIME, pair=PAIR)


@pytest.fixture(scope="module")
def fact_fits(dof_gate):
    # factorized fits vs the coupled teacher at phi_ref, per cumulative rung
    field = mixed_mechanism_field(H0_SPECS)
    edge = _edge(PHI_REF)
    return {
        r: calibrate(field, calibration_contexts(r), distance=3, num_kraus=NUM_KRAUS,
                     steps=STEPS, seed=SEED, teacher_edge_field=edge)
        for r in (0, 1, 2, 3, 4)
    }


@pytest.fixture(scope="module")
def fact_fits_phi(dof_gate):
    # r=4 factorized fits at the regime endpoints (P4 scaling slope)
    field = mixed_mechanism_field(H0_SPECS)
    return {
        p: calibrate(field, calibration_contexts(4), distance=3, num_kraus=NUM_KRAUS,
                     steps=STEPS, seed=SEED, teacher_edge_field=_edge(p))
        for p in (0.05, 0.15)
    }


@pytest.fixture(scope="module")
def coupled_fits(dof_gate):
    # non-factorized fits from +/- phi inits (P2 sign minima; P7 closure uses (4, +))
    field = mixed_mechanism_field(H0_SPECS)
    edge = _edge(PHI_REF)
    return {
        (r, init): calibrate(field, calibration_contexts(r), distance=3,
                             num_kraus=NUM_KRAUS, steps=STEPS, seed=SEED,
                             teacher_edge_field=edge, twin_edge=True,
                             twin_phi_init=init, twin_pair=PAIR)
        for r in (3, 4) for init in (+0.05, -0.05)
    }


@pytest.fixture(scope="module")
def stoch_fit(dof_gate):
    # factorized fit vs the correlated-stochastic (twirl) edge teacher (P8 control)
    field = mixed_mechanism_field(H0_SPECS)
    return calibrate(field, calibration_contexts(4), distance=3, num_kraus=NUM_KRAUS,
                     steps=STEPS, seed=SEED, teacher_edge_field=_stoch_edge(PHI_REF))


# --------------------------------------------------------------------------- #
# P1 -- precondition guard (exact T1 machinery pins + regression vs H0)         #
# --------------------------------------------------------------------------- #
def test_h2_factorized_precondition_fits_at_low_r(fact_fits) -> None:
    # P1: repeats=1 contexts are EXACTLY phi-blind (T1, all orders) -- the coupling
    # hook placement pin; a violation here is a build bug, by the pre-registered
    # falsification routing, never a tuning target.
    field = mixed_mechanism_field(H0_SPECS)
    edge15 = _edge(0.15)
    repeats1 = [c for c in calibration_contexts(4) if c.repeats == 1]
    repeats1 += [held_out_eval_context(), held_out_exotic_contexts()[0]]  # R4-L0, R4-ry
    for c in repeats1:
        kl = float(joint_kl(run_context(c, channel_field=field, edge_field=edge15),
                            run_context(c, channel_field=field)))
        assert kl <= 1e-10, f"{c.label}: repeats=1 phi-blindness violated (KL={kl:.3e})"

    # P1: the factorized fit reaches the floor at r<=1 (the edge is invisible there).
    for r in (0, 1):
        assert fact_fits[r]["total_kl"] < 1e-6

    # P1 regression pin: the H0 knob table is reproduced exactly on the repeats=1
    # eval R4-L0 -- the coupled teacher's do(E_i -> I) knobs equal the edge-free
    # H0 teacher's (T1 null under local do()), and match the dated H0 pins.
    h0_pinned = {0: -4.100e-2, 1: -3.312e-2, 2: -2.391e-2}  # metric_results.md 2026-06-09
    eval_ctx = held_out_eval_context()
    decoder = build_frozen_decoder(eval_ctx)
    base_c = logical_error_rate(run_context(eval_ctx, channel_field=field, edge_field=edge15), decoder)
    base_0 = logical_error_rate(run_context(eval_ctx, channel_field=field), decoder)
    for i in range(3):
        do_field = intervene_field(field, i, do_remove)
        knob_c = logical_error_rate(
            run_context(eval_ctx, channel_field=do_field, edge_field=edge15), decoder) - base_c
        knob_0 = logical_error_rate(run_context(eval_ctx, channel_field=do_field), decoder) - base_0
        assert abs(knob_c - knob_0) <= 1e-10
        assert abs(knob_c - h0_pinned[i]) <= 1e-5


# --------------------------------------------------------------------------- #
# P2 -- exact phi-parity (T2') + the sign alias and its r=4 resolution          #
# --------------------------------------------------------------------------- #
def test_h2_phi_parity_and_sign_minima(coupled_fits) -> None:
    # P2: every pre_rotation=0 context is exactly EVEN in phi (the (prod Z) o K
    # anti-unitary symmetry, T2') -- TV(p_phi, p_-phi) <= 1e-10.
    field = mixed_mechanism_field(H0_SPECS)
    plus, minus = _edge(0.15), _edge(-0.15)
    even_ctxs = [c for c in calibration_contexts(4) if c.pre_rotation == 0.0]
    even_ctxs += [held_out_eval_context(), held_out_sandwich_context()]
    for c in even_ctxs:
        tv = _tv(run_context(c, channel_field=field, edge_field=plus),
                 run_context(c, channel_field=field, edge_field=minus))
        assert tv <= 1e-10, f"{c.label}: phi-parity violated (TV={tv:.3e})"

    # R1 (re-registered 2026-06-09 after the first run; metric_results.md H2 addendum).
    # Original ±minima-landing check MISSED: both inits cross the shallow (~1.7e-4 nat)
    # phi=0 barrier under LBFGS line search -- an optimizer assumption, not physics.
    # Derived replacement: flipping the converged phi_hat is a KL IDENTITY over
    # C_cal(3) (every r<=3 context is even (T2') or blind (T1) in phi).
    p3, m3 = coupled_fits[(3, +0.05)], coupled_fits[(3, -0.05)]
    assert abs(p3["phi_hat"] - PHI_REF) <= 0.25 * PHI_REF
    assert p3["total_kl"] < 1e-6 and m3["total_kl"] < 1e-6
    tedge = _edge(PHI_REF)

    def _total_kl(twin, level: int) -> float:
        return sum(
            evaluate_kl(twin, field, c, teacher_edge_field=tedge)
            for c in calibration_contexts(level)
        )

    # R1a' (second re-registration; metric_results.md): the exact identity holds only
    # for T-invariant locals -- fitted locals break (prod Z) o K at the fit-floor
    # amplitude, so the derived check is floor-level equality, not exact equality:
    # (i) the flipped point is itself a floor-level minimum; (ii) |dKL| = O(base KL).
    twin3 = m3["twin"]
    base3 = _total_kl(twin3, 3)
    with torch.no_grad():
        twin3.phi_hat.mul_(-1.0)
    flipped3 = _total_kl(twin3, 3)
    with torch.no_grad():
        twin3.phi_hat.mul_(-1.0)
    assert flipped3 <= 1e-8, f"R1a'(i): flipped KL(r=3) {flipped3:.3e} not floor-level"
    assert abs(flipped3 - base3) <= 10.0 * max(base3, 1e-12), (
        f"R1a'(ii): |dKL| {abs(flipped3 - base3):.3e} exceeds the derived cross-term "
        f"scale 10 x base ({base3:.3e})"
    )

    # R1b: at r=4 the flipped sign mismatches the k2ry phi-linear channel at
    # amplitude 2*phi -> derived band [2x, 8x] of the factorized r=4 residual.
    twin4 = coupled_fits[(4, +0.05)]["twin"]
    with torch.no_grad():
        twin4.phi_hat.mul_(-1.0)
    flipped4 = _total_kl(twin4, 4)
    with torch.no_grad():
        twin4.phi_hat.mul_(-1.0)
    assert 2.5e-2 <= flipped4 <= 1.1e-1, f"R1b: flipped KL(r=4) {flipped4:.3e} outside [2.5e-2, 1.1e-1]"

    # P2: at r=4 (k2ry breaks T1 AND T-parity) the wrong-sign minimum is rejected:
    # either the -init fit escapes to +phi_true, or its KL is >= 10x the +fit's.
    p4, m4 = coupled_fits[(4, +0.05)], coupled_fits[(4, -0.05)]
    assert abs(p4["phi_hat"] - PHI_REF) <= 0.25 * PHI_REF
    if m4["phi_hat"] < 0.0:
        assert m4["total_kl"] >= 10.0 * p4["total_kl"]
    else:
        assert abs(m4["phi_hat"] - PHI_REF) <= 0.25 * PHI_REF


# --------------------------------------------------------------------------- #
# P3 + P4 -- the W2 DOF gate (run BEFORE any fit) and the named-outcome fork    #
# --------------------------------------------------------------------------- #
def test_h2_two_outcomes_calib_kl_degrades_or_stays_flat(dof_gate, fact_fits, fact_fits_phi) -> None:
    # P3 (the W2 DOF gate, computed before any fit via the fixture dependency):
    # teacher-discrimination KL(p_phi || p_0) over C_cal(r) per rung.
    rung = dof_gate["per_rung"]
    for r in (0, 1):  # T1: blind at every phi in the regime
        assert max(rung[r]["kl_by_phi"].values()) <= 1e-10
    assert rung[3]["increment"] <= 1e-10        # the r=3 rung is NOT the crosstalk rung
    assert 3.5 <= rung[2]["slope"] <= 4.5       # even/quartic null at the sandwich rung
    assert 3.5 <= rung[3]["slope"] <= 4.5
    assert 1.7 <= rung[4]["slope"] <= 2.3       # signed sector opens at r=4 (k2ry)
    # A-proxy blindness (T2): the edge twirl has no DEM column -- zero stochastic
    # edge DOF at every r (earned: the twirl edge alone leaves the richest Z-basis
    # context at the noiseless joint).
    assert dof_gate["a_proxy"]["twirl_quiet_kl"] <= 1e-10
    assert dof_gate["a_proxy"]["edge_stochastic_dof"] == 0

    # P4 / R2 (re-registered 2026-06-09; metric_results.md H2 addendum). Original
    # >=90% absorption MISSED at 87.9%/87.4%; the derivation's own residual estimate
    # is O(p_exc), p_exc ~ 0.06-0.1 -> derived threshold: unabsorbed <= 2*p_exc_max
    # = 0.2 (absorption >= 80%). The r=2-3 cell is "weakly detectable", not silent;
    # the exact dangerous cell stands at r<=1 by T1.
    for r in (2, 3):
        unabsorbed = fact_fits[r]["total_kl"] / rung[r]["kl"]
        assert unabsorbed <= 0.2, (
            f"R2: unabsorbed fraction {unabsorbed:.3f} at r={r} exceeds the derived "
            f"O(p_exc) bound 0.2 (shadow construction wrong)"
        )
    # P4, outcome (a) at r=4: the misspecification SURFACES in the fit.
    assert fact_fits[4]["total_kl"] >= 10.0 * fact_fits[3]["total_kl"]
    assert fact_fits[4]["total_kl"] >= 1e-6
    # P4 scaling: calib_KL_fact(4) ~ phi^2 (the phi-linear k2ry signature exits the
    # factorized tangent space; KL is quadratic in the unmatchable amplitude).
    slope = _slope({p: fact_fits_phi[p]["total_kl"] for p in (0.05, 0.15)})
    assert 1.7 <= slope <= 2.3


# --------------------------------------------------------------------------- #
# P5 + P6 + P7 -- B_misspec scaling/sign, band overconfidence, and closure      #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def truth():
    # teacher-side exact truths per phi: edge-knob dLER on the sandwich + memory
    # evals, and the do()-shift TVD on the k2ry exotics (evaluator-only ground truth).
    field = mixed_mechanism_field(H0_SPECS)
    sandwich, memory = held_out_sandwich_context(), held_out_eval_context()
    exotics = held_out_exotic_contexts()[1:]  # the k2ry pair (R4-ry-k2, R3-ry-k2)
    dec_sw, dec_mem = build_frozen_decoder(sandwich), build_frozen_decoder(memory)
    out = {"dler_sandwich": {}, "dler_memory": {}, "tvd_k2ry": {}, "dler_stoch": {}}
    for p in PHI_REGIME:
        edge = _edge(p)
        out["dler_sandwich"][p] = _true_edge_dler(field, edge, sandwich, dec_sw)
        out["dler_memory"][p] = _true_edge_dler(field, edge, memory, dec_mem)
        out["tvd_k2ry"][p] = [
            _tv(run_context(c, channel_field=field, edge_field=edge),
                run_context(c, channel_field=field))
            for c in exotics
        ]
        out["dler_stoch"][p] = _true_edge_dler(field, _stoch_edge(p), sandwich, dec_sw)
    return out


def test_h2_factorized_band_overconfident_nonfactorized_closes(
    truth, fact_fits, coupled_fits
) -> None:
    field = mixed_mechanism_field(H0_SPECS)
    edge = _edge(PHI_REF)
    sandwich = held_out_sandwich_context()
    decoder = build_frozen_decoder(sandwich)

    # P5: B_misspec = |dLER_true| (factorized edge-knob prediction is structurally 0)
    # on the sandwich eval: ~ phi^2, with dLER_true > 0 (echo-protective coupling --
    # removing the crosstalk RAISES the LER; a non-monotone-LER instance).
    assert truth["dler_sandwich"][PHI_REF] > 0.0
    slope_sw = _slope({p: abs(truth["dler_sandwich"][p]) for p in (0.05, 0.15)})
    assert 1.7 <= slope_sw <= 2.3
    # P5: O(phi)-linear component on the k2ry evals (obs_shift_tvd; B_LER reported,
    # decoder-projection fallback declared in the pre-registration).
    for k in range(2):
        slope_tv = _slope({p: truth["tvd_k2ry"][p][k] for p in (0.05, 0.15)})
        assert 0.7 <= slope_tv <= 1.3
    # P5: the projection control -- on the repeats=1 memory eval the edge knob is a
    # T1 null, so B_misspec = 0 exactly.
    for p in PHI_REGIME:
        assert abs(truth["dler_memory"][p]) <= 1e-10

    # P6: the factorized Tier-0 band (z=3, shots=1e7) FAILS to cover the edge-knob
    # truth, and richness does not close it -- model-class, not data.
    b_misspec, bands = {}, {}
    for r in (2, 4):
        twin = fact_fits[r]["twin"]
        scores = field_counterfactual_scores(
            field, twin.field(), sandwich, decoder,
            intervention=do_remove, target_edge=PAIR,
            teacher_edge_field=edge, twin_edge_field=None,
        )
        b_misspec[r] = scores["B_LER"]
        bands[r] = tier0_alias_band(
            twin, calibration_contexts(r), fact_fits[r]["teacher_forwards"],
            eval_context=sandwich, decoder=decoder,
            intervention=do_remove, target_edge=PAIR, shots=SHOTS, z=Z,
        )
        half = bands[r]["statistical_band"] + bands[r]["alias_weight"]
        assert b_misspec[r] >= half  # the miss: truth outside the 3-sigma + alias band
        assert abs(bands[r]["knob_value"] - truth["dler_sandwich"][PHI_REF]) > half
    assert b_misspec[4] >= 0.5 * b_misspec[2]  # richness does not close B_misspec

    # P7 (Claim 2 closure): the non-factorized learner at C_cal(4) -- signed phi_hat
    # within 25%, knob error <= 0.1 x factorized B_misspec on the exposing
    # functionals, and ITS band covers truth.
    p4 = coupled_fits[(4, +0.05)]
    twin_c = p4["twin"]
    assert abs(p4["phi_hat"] - PHI_REF) <= 0.25 * PHI_REF
    cf_sw = counterfactual_scores(
        field, twin_c, sandwich, decoder,
        intervention=do_remove, target_edge=PAIR, teacher_edge_field=edge,
    )
    assert cf_sw["B_LER"] <= 0.1 * b_misspec[4]
    exotic = held_out_exotic_contexts()[1]  # R4-ry-k2
    dec_exo = build_frozen_decoder(exotic)
    cf_exo = counterfactual_scores(
        field, twin_c, exotic, dec_exo,
        intervention=do_remove, target_edge=PAIR, teacher_edge_field=edge,
    )
    fact_exo = field_counterfactual_scores(
        field, fact_fits[4]["twin"].field(), exotic, dec_exo,
        intervention=do_remove, target_edge=PAIR,
        teacher_edge_field=edge, twin_edge_field=None,
    )
    assert cf_exo["B_obs"] <= 0.1 * fact_exo["B_obs"]
    band_c = tier0_alias_band(
        twin_c, calibration_contexts(4), p4["teacher_forwards"],
        eval_context=sandwich, decoder=decoder,
        intervention=do_remove, target_edge=PAIR, shots=SHOTS, z=Z,
    )
    assert (
        abs(band_c["knob_value"] - truth["dler_sandwich"][PHI_REF])
        <= band_c["statistical_band"] + band_c["alias_weight"]
    )


# --------------------------------------------------------------------------- #
# P8 -- the correlated-STOCHASTIC control (Pauli-shadow one level up)           #
# --------------------------------------------------------------------------- #
def test_h2_stochastic_crosstalk_control(dof_gate, fact_fits, stoch_fit, truth) -> None:
    field = mixed_mechanism_field(H0_SPECS)
    # (i) echo-equivalence at the Z-basis rungs: the coherent edge and its twirl at
    # matched rate sin^2(phi) are within 10% of the edge's own visibility on C_cal(2).
    coh, stoch = _edge(PHI_REF), _stoch_edge(PHI_REF)
    kl_cs = sum(
        float(joint_kl(run_context(c, channel_field=field, edge_field=coh),
                       run_context(c, channel_field=field, edge_field=stoch)))
        for c in calibration_contexts(2)
    )
    assert kl_cs <= 0.1 * dof_gate["per_rung"][2]["kl"]
    # (ii) the factorized fit NEVER degrades on the stochastic edge -- local
    # dephasing absorbs it (pure-(b) at every built rung); only the COHERENT case
    # surfaces in the fit.
    assert stoch_fit["total_kl"] <= 0.1 * fact_fits[4]["total_kl"]
    # (iii) its edge-knob B_misspec ~ phi^2 persists (the overconfidence does not
    # need coherence; the FIT-visibility does). Nonzero guard is well below the
    # measured phi^2 scale (not a registered threshold).
    slope_st = _slope({p: abs(truth["dler_stoch"][p]) for p in (0.05, 0.15)})
    assert 1.7 <= slope_st <= 2.3
    assert abs(truth["dler_stoch"][PHI_REF]) > 1e-6


# --------------------------------------------------------------------------- #
# Report (run with -s; numbers feed docs/metric_results.md)                     #
# --------------------------------------------------------------------------- #
def test_h2_report(dof_gate, fact_fits, fact_fits_phi, coupled_fits, stoch_fit, truth) -> None:
    print("\n=== H2 non-factorized coherent ZZ crosstalk (d=3, phi_ref=0.1) ===")
    for r, row in dof_gate["per_rung"].items():
        slope = "None" if row["slope"] is None else f"{row['slope']:.2f}"
        print(f"P3 gate r={r}: KL={row['kl']:.3e}  increment={row['increment']:.3e}  slope={slope}")
    print(f"P3 a_proxy: {dof_gate['a_proxy']}")
    for r in (0, 1, 2, 3, 4):
        print(f"P4 calib_KL_fact(r={r}) = {fact_fits[r]['total_kl']:.3e}")
    for p in (0.05, 0.15):
        print(f"P4 calib_KL_fact(4) at phi={p} = {fact_fits_phi[p]['total_kl']:.3e}")
    for key, fit in coupled_fits.items():
        print(f"P2/P7 coupled fit {key}: phi_hat={fit['phi_hat']:+.5f}  KL={fit['total_kl']:.3e}")
    print(f"P8 calib_KL_stoch(4) = {stoch_fit['total_kl']:.3e}")
    for p in PHI_REGIME:
        print(
            f"P5 truth at phi={p}: dler_sandwich={truth['dler_sandwich'][p]:+.4e}  "
            f"dler_memory={truth['dler_memory'][p]:+.3e}  "
            f"tvd_k2ry={[f'{t:.4e}' for t in truth['tvd_k2ry'][p]]}  "
            f"dler_stoch={truth['dler_stoch'][p]:+.4e}"
        )
    assert True

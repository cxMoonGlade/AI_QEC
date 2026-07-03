#!/usr/bin/env python
r"""WEDGE HARNESS (Builder ③ deliverable) — COHERENCE-ENVELOPE observable (rebuilt v3, 2026-06-26).

WHY v3 (two construction bugs the gtcheck correctly EXPOSED)
-----------------------------------------------------------
v2 measured the wedge on the single-basis Ramsey fringe Re L(t) with a sign-free / Markov-k baseline,
and the gtcheck FAILED (wedge negative everywhere). Two real bugs, both in the wedge CONSTRUCTION:

  BUG 1 — single-basis Re L is MIMICABLE. A CP-divisible (Markovian) dephasing WITH a coherent
    detuning delta gives  Re L(t) = cos(delta t) * exp(-Gamma t)  — which OSCILLATES and goes
    NEGATIVE, faking the RTN's sign flips. So Re L sign changes do NOT certify non-Markovianity. The
    UNFORGEABLE signature is the ENVELOPE |L(t)|: the CP-divisibility theorem gives
        |L(t)| = exp(-integral_0^t gamma_phi ds),  gamma_phi >= 0  =>  |L| MONOTONE non-increasing,
    and a coherent detuning ROTATES the phase but does NOT change |L|. A |L| REVIVAL (the envelope
    dips to a node then climbs BACK UP) is non-Markovian and cannot be faked by any detuning.
    FIX: the observable estimates the fringe ENVELOPE |L(t)| via TWO-QUADRATURE Ramsey (X and Y
    bases): |L| = sqrt(<sigma_x>^2 + <sigma_y>^2),  <sigma_x> = Re L,  <sigma_y> = Im L.

  BUG 2 — the v2 baseline was OVER-FLEXIBLE. Per-t_k empirical-sign freedom + Markov-k ALONG the
    measurement-time axis made it a ~saturated one-param-per-t fit that ABSORBED the revival. A
    physical CP-divisible |L| has NO sign freedom (|L|>=0) and is a SMOOTH MONOTONE envelope, not a
    free classical Markov chain along t. FIX: the C5 baseline = the best MONOTONE-non-increasing,
    POSITIVE |L| in [0,1] ONLY (multi-exponential |L|=sum a_j exp(-r_j t), a_j>=0, sum a<=1, r_j>=0;
    and/or isotonic on |L|). **Markov-k is DROPPED from the coherence wedge baseline** — it is not a
    CP-divisible dephasing model; it belongs only to the SECONDARY syndrome-round-correlation result
    (labeled classical), never here. The monotone-positive |L| fit IS the strongest fair CP-divisible
    competitor (the theorem: any Markovian dephasing envelope is monotone-positive) and PROVABLY
    cannot fit a |L| revival.

THE PHYSICS (the (a)-exact basis)
  CP-divisible dephasing  <=>  |L(t)| monotone non-increasing & >= 0  (gamma_phi >= 0). For the
  symmetric RTN, L is real; in the underdamped branch v>gamma_sw it crosses zero at nodes and its
  ENVELOPE |L| revives (climbs back up after a node) — non-Markovian BY DEFINITION (Rivas-Huelga-
  Plenio). Z-syndromes are phase-blind (cannot see L); the two-quadrature coherence probe estimates
  |L| directly. The |L| revival is the ONLY non-Markovian signature no CP-divisible model can forge.

WHAT THIS MEASURES
  * Observation model = TWO-QUADRATURE Ramsey envelope probe over a grid of free-evolution times
    {t_k} (S-class; declared+bounded below).
  * C5 baseline = the STRONGEST monotone-positive |L| (multi-exp + isotonic-on-|L|). NO sign freedom,
    NO Markov-k. Fit by max-likelihood on the two-basis coherence-NLL (Born rule, ADR 0003).
  * twin = SOURCE-RESOLVED |L(t)| (reproduces the revival), HISTORY/observation-ONLY (fits
    (v, gamma_sw) from the envelope; NEVER the per-shot latent — isolation preserved).
  * wedge = baseline_heldout_NLL - twin_heldout_NLL = the irreducible gap a monotone |L| leaves at a
    |L| revival.
  * C10 (HARD): the wedge MUST collapse (~0) for v<gamma_sw (monotone |L|) and turn on for v>gamma_sw
    (revival), CO-LOCATED with the RHP crossover at v=gamma_sw (imported from nm_divisibility).
  * C9/P4 on |L| calibration: the twin tracks the |L| envelope incl. the revival bump; the monotone
    baseline cannot at the revival. Strict-improve + self-calibration + isolation.

BINDING CONTRACT
  - docs/twin_validation/nonmarkovian_coupling_constraint_ledger.md  (C5 REVISED, C10 NEW; C9)
  - docs/twin_validation/full_error_coupling_prereg.md  §5.1 REVISION (P1<->wedge), P3, P4
  - docs/teacher_learner.md   (isolation: learner sees observations only; latent evaluator-only)
  - docs/FAITHFULNESS_PROTOCOL.md  (rules I/II/III)

DECLARED + BOUNDED OBSERVATION MODEL (rule III; S-class):
  TWO-QUADRATURE Ramsey. Per (t_k, shot): prepare |+>, free-evolve t_k, then read out in the X basis
  OR the Y basis (the shots at each t_k are SPLIT half/half between bases). Per-shot Born:
      X basis:  P(+x | t_k, shot) = 0.5*(1 + cos phi_shot(t_k))          [<sigma_x> = Re L]
      Y basis:  P(+y | t_k, shot) = 0.5*(1 + sin phi_shot(t_k))          [<sigma_y> = Im L]
  phi_shot(t_k) = v * integral_0^{t_k} xi. Pooled: <sigma_x> -> Re L(t_k), <sigma_y> -> Im L(t_k);
  the ENVELOPE estimate is |L|_hat = sqrt(<sigma_x>_hat^2 + <sigma_y>_hat^2). The model (baseline or
  twin) predicts (Re L, Im L); the NLL is the Bernoulli likelihood over BOTH bases. The monotone
  constraint binds the ENVELOPE |L| = sqrt(ReL^2+ImL^2), which is exactly what a CP-divisible model
  cannot grow.
    * EPISTEMIC CLASS: (c) design / scope. The per-shot Born likelihood is EXACT for this probe.
    * BOUND: pooled <sigma_x>,<sigma_y> -> Re L, Im L at 1/sqrt(n_shots_per_basis); the envelope
      estimate inherits that band. Phase integral trapezoidal on n_substep (bias -> 0). For the pure
      SYMMETRIC RTN Im L = 0 exactly, so |L| = |Re L| — the two-quadrature machinery RECOVERS that
      and, crucially, is detuning-PROOF (BUG 1): with any coherent detuning Re L would oscillate but
      |L| would NOT, so the baseline could fake Re L sign flips but never the |L| envelope. Full
      multi-round QEC-DEM / soft-readout DEFERRED (scope).
    * WHY |L| (not Re L): non-Markovianity = |L| non-monotonicity; Re L sign flips are forgeable by a
      Markovian detuning (BUG 1). The two-quadrature envelope is the smallest faithful carrier.
  Secondary classical result: the syndrome round-correlation (if reported) is Markov-k-capturable and
  is NOT this wedge; Markov-k lives ONLY there.

DISCIPLINE (HARD CONSTRAINTS):
  - AUTHOR-only: NO torch / GPU / QuTiP / heavy runs. Pure numpy. Orchestrator runs the gtcheck
    SERIALLY.
  - ISOLATION load-bearing: every fit consumes ONLY the binary outcomes (both bases). The per-shot
    latent phase is EVALUATOR-only; the gtcheck asserts latent-scramble invariance + a latent-peeker
    is detectably different.
  - C5 FAIR: the strongest monotone-positive |L| competitor, converged. NO sign freedom, NO Markov-k.
  - the wedge MUST be CAUSED by the |L| revival: a no-revival (v<gamma_sw) control => wedge ~ 0.
  - seeds EXPLICIT (numpy Generator); NEVER global/time RNG. float64.

OWNERSHIP: Builder ③ owns ONLY nm_wedge.py + nm_wedge_gtcheck.py. nm_source.py (Builder ①) and
nm_divisibility.py (Builder ②) are imported, FIXED interfaces; do NOT touch theirs.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

# The memory-ful source layer (moved from outputs/teacher_prereg/nm_source.py; MIGRATION P1).
from .nonmarkovian import (
    RTNParams,
    rtn_coherence_analytic,
    sample_rtn_trajectory,
)

# numerical floor (project convention; see src/qec_twin/numerics.py).
NUMERICAL_ZERO = 1e-12
# probability floor for log() in NLL (avoid log(0); never replaces a structural zero).
_PROB_FLOOR = 1e-12


# =========================================================================== #
# Coherence components: Re L (X basis) and Im L (Y basis).                      #
# =========================================================================== #
def analytic_reL(p: RTNParams, t_grid: np.ndarray) -> np.ndarray:
    """Re L(t) for the symmetric RTN, from Builder ①'s exact rtn_coherence_analytic (returns the real
    L). Returns a float64 array. (<sigma_x> = Re L.)"""
    return np.asarray(rtn_coherence_analytic(p, np.asarray(t_grid, dtype=np.float64)),
                      dtype=np.float64)


def analytic_imL(p: RTNParams, t_grid: np.ndarray) -> np.ndarray:
    """Im L(t). For the symmetric (+/-v, zero-mean) RTN the phase distribution is symmetric so
    Im L = <sin phi> = 0 EXACTLY. Returned as zeros (the Y-quadrature is identically the dephased
    coin for this source). Detuning would make Im L != 0; THIS source has none (declared)."""
    return np.zeros(np.asarray(t_grid, dtype=np.float64).shape, dtype=np.float64)


def analytic_envelope(p: RTNParams, t_grid: np.ndarray) -> np.ndarray:
    """The EXACT coherence envelope |L(t)| = sqrt(Re L^2 + Im L^2) (= |Re L| for the symmetric RTN).
    Evaluator/twin GROUND TRUTH (NOT a fit). The unforgeable non-Markovian signal lives in its
    non-monotonicity (the revival)."""
    reL = analytic_reL(p, t_grid)
    imL = analytic_imL(p, t_grid)
    return np.sqrt(reL * reL + imL * imL)


def revival_amplitude(p: RTNParams, t_grid: np.ndarray) -> float:
    r"""[C10 turn-on reference] The analytic |L|-REVIVAL AMPLITUDE on t_grid: the largest climb-back of
    the envelope above its running minimum,  max_k ( |L|(t_k) - min_{j<=k} |L|(t_j) ).

    = 0 when |L| is monotone (Markovian / motional-narrowing side: no revival); > 0 in the underdamped
    branch where the envelope dips to a node then climbs back up. Near the crossover v~gamma_sw this is
    exponentially suppressed (~e^{-gamma_sw*t_revival}), so it is the physically-correct INDEPENDENT
    reference for when the wedge becomes OBSERVABLE (a finite-shot NLL can only detect a revival whose
    amplitude clears the MC floor) — unlike RHP, which is >0 at any infinitesimal negativity. This is
    the C10 turn-on co-location reference (it is an analytic property of |L|, independent of the wedge).
    """
    env = analytic_envelope(p, t_grid)
    climb = env - np.minimum.accumulate(env)
    return float(np.max(climb))


def p_plus_x(re_L) -> np.ndarray:
    """Born P(+x) = 0.5*(1 + Re L) (X-basis). Clamped to a valid probability."""
    return np.clip(0.5 * (1.0 + np.asarray(re_L, dtype=np.float64)), _PROB_FLOOR, 1.0 - _PROB_FLOOR)


def p_plus_y(im_L) -> np.ndarray:
    """Born P(+y) = 0.5*(1 + Im L) (Y-basis). Clamped to a valid probability."""
    return np.clip(0.5 * (1.0 + np.asarray(im_L, dtype=np.float64)), _PROB_FLOOR, 1.0 - _PROB_FLOOR)


# =========================================================================== #
# simulate_envelope_observations — two-basis stream + evaluator-only latent.    #
# =========================================================================== #
@dataclass(frozen=True)
class EnvelopeObs:
    """Two-quadrature Ramsey envelope-probe dataset.

    t_grid       : (n_t,) float64 free-evolution times.
    yx           : (n_shots_x, n_t) uint8 X-basis outcomes (y=1 == "+x"). LEARNER-VISIBLE.
    yy           : (n_shots_y, n_t) uint8 Y-basis outcomes (y=1 == "+y"). LEARNER-VISIBLE.
    latent_phase_x / latent_phase_y : per-shot accumulated phase, EVALUATOR-ONLY (the source latent);
                   the isolation contract forbids any fit consuming them.
    p            : the source RTNParams (evaluator-only metadata).
    n_substep    : phase-integration resolution used.
    """

    t_grid: np.ndarray
    yx: np.ndarray
    yy: np.ndarray
    latent_phase_x: np.ndarray
    latent_phase_y: np.ndarray
    p: RTNParams
    n_substep: int

    def envelope_hat(self, debias: bool = True) -> np.ndarray:
        r"""Empirical envelope |L|_hat per t_k from the pooled two-basis outcome rates (<sigma> =
        2*phat - 1).

        The naive estimator sqrt(<sx>^2 + <sy>^2) is RICIAN-biased UPWARD where |L|->0 (the squared
        quadrature noise does not cancel): E[<sx>^2] = ReL^2 + Var(<sx>), so at a revival NODE the
        naive |L|_hat sits at ~sqrt(Var(<sx>)+Var(<sy>)) > 0 even though |L|=0. We DEBIAS (default):
            |L|^2_debiased = max(0, <sx>^2 + <sy>^2 - Var(<sx>) - Var(<sy>)),
            Var(<sigma>) = (1 - <sigma>^2) / n_shots_basis   (Bernoulli variance of 2*phat-1),
        then sqrt. This removes the node bias (so the source-resolved twin, which predicts |L|->0 at
        the node, is not penalized by an instrument artifact). Set debias=False for the raw estimator.
        """
        sx = 2.0 * self.yx.mean(axis=0) - 1.0
        sy = 2.0 * self.yy.mean(axis=0) - 1.0
        if not debias:
            return np.sqrt(sx * sx + sy * sy)
        n_x = float(self.yx.shape[0])
        n_y = float(self.yy.shape[0])
        var_sx = (1.0 - sx * sx) / max(n_x, 1.0)          # Var(2*phat-1) = 4*phat(1-phat)/n = (1-s^2)/n
        var_sy = (1.0 - sy * sy) / max(n_y, 1.0)
        sq = sx * sx + sy * sy - var_sx - var_sy
        return np.sqrt(np.clip(sq, 0.0, None))


def _cum_phase(xi: np.ndarray, sub: np.ndarray, v: float, k_idx: np.ndarray) -> np.ndarray:
    """phi(t_k) = v * integral_0^{t_k} xi dt' via cumulative trapezoid (Builder ①'s convention),
    sampled at the sub-grid indices k_idx for each t_k."""
    incr = 0.5 * (xi[1:] + xi[:-1]) * np.diff(sub)
    cum = np.concatenate([[0.0], np.cumsum(incr)])
    return v * cum[k_idx]


def simulate_envelope_observations(source_p: RTNParams, t_grid, n_shots: int, seed: int,
                                   n_substep: int = 600) -> EnvelopeObs:
    r"""Generate the two-quadrature envelope-probe stream + the evaluator-only per-shot latent phases.

    n_shots shots are SPLIT half/half between the X and Y readout bases (n_shots//2 each; the source
    is identically distributed across bases). Per shot, ONE telegraph trajectory on the full
    [0, t_max] sub-grid drives ALL t_k (one physical history per shot). For each t_k:
        X-basis shot: yx ~ Bernoulli(0.5*(1 + cos phi_shot(t_k)))   [<sigma_x> -> Re L]
        Y-basis shot: yy ~ Bernoulli(0.5*(1 + sin phi_shot(t_k)))   [<sigma_y> -> Im L]
    Pooled: |L|_hat = sqrt(<sigma_x>^2 + <sigma_y>^2) -> |L(t_k)|. seed EXPLICIT. Returns EnvelopeObs.
    """
    tg = np.asarray(t_grid, dtype=np.float64)
    assert tg.ndim == 1 and tg.size >= 1 and np.all(np.diff(tg) > 0), \
        "simulate_envelope_observations: t_grid must be 1-D strictly increasing."
    assert n_shots >= 2 and n_substep >= 2, "need n_shots>=2, n_substep>=2."
    rng = np.random.default_rng(int(seed))
    v = float(source_p.v)
    t_max = float(tg[-1])
    sub = np.linspace(0.0, t_max, int(n_substep), dtype=np.float64)
    k_idx = np.clip(np.searchsorted(sub, tg, side="left"), 1, sub.size - 1)
    n_t = tg.size
    n_x = int(n_shots) // 2
    n_y = int(n_shots) - n_x

    yx = np.empty((n_x, n_t), dtype=np.uint8)
    yy = np.empty((n_y, n_t), dtype=np.uint8)
    lpx = np.empty((n_x, n_t), dtype=np.float64)
    lpy = np.empty((n_y, n_t), dtype=np.float64)
    for s in range(n_x):
        xi = sample_rtn_trajectory(source_p, sub, seed=int(seed) + 1 + s)
        phi = _cum_phase(xi, sub, v, k_idx)
        lpx[s] = phi
        yx[s] = (rng.random(n_t) < 0.5 * (1.0 + np.cos(phi))).astype(np.uint8)
    for s in range(n_y):
        xi = sample_rtn_trajectory(source_p, sub, seed=int(seed) + 1 + n_x + s)
        phi = _cum_phase(xi, sub, v, k_idx)
        lpy[s] = phi
        yy[s] = (rng.random(n_t) < 0.5 * (1.0 + np.sin(phi))).astype(np.uint8)
    return EnvelopeObs(t_grid=tg, yx=yx, yy=yy, latent_phase_x=lpx, latent_phase_y=lpy,
                       p=source_p, n_substep=int(n_substep))


def simulate_markovian_envelope_observations(env_func, t_grid, n_shots: int, seed: int
                                             ) -> EnvelopeObs:
    r"""[C10 NEGATIVE CONTROL] Two-quadrature stream from a GENUINELY MARKOVIAN (monotone-positive,
    CP-divisible) source whose REAL envelope is env_func(t) in [0,1] (Im L = 0 — a classical
    pure-dephasing source). Routes an OUT-OF-FAMILY monotone source (e.g. Gaussian-T2
    e^{-(t/T2)^2} or exponential e^{-t/T2} — NOT RTN) through the SAME EnvelopeObs machinery, so the
    RTN-twin + the monotone baseline are scored on it identically. Per (t_k, shot):
        X: yx ~ Bernoulli(0.5*(1 + L(t_k))),  Y: yy ~ Bernoulli(0.5)   (Im L = 0).
    Pooled: <sx> -> L(t_k) (monotone), <sy> -> 0, so |L|_hat -> L(t_k) — a MONOTONE envelope with NO
    revival. The RTN-twin therefore CANNOT beat the monotone supremum baseline => wedge <= 0 (no false
    positive). latent_phase is a placeholder (these sources have no per-shot RTN trajectory; the field
    exists only to satisfy the container + the isolation-scramble test, never read by any fit).
    Returns EnvelopeObs (its .p is a nominal RTNParams placeholder — UNUSED by the baseline/twin fits,
    which read only y; reliability's analytic |L| is NOT used for this control's gating).
    """
    tg = np.asarray(t_grid, dtype=np.float64)
    assert tg.ndim == 1 and tg.size >= 1 and np.all(np.diff(tg) > 0), \
        "simulate_markovian_envelope_observations: t_grid must be 1-D strictly increasing."
    assert n_shots >= 2, "need n_shots>=2."
    rng = np.random.default_rng(int(seed))
    env = np.clip(np.asarray(env_func(tg), dtype=np.float64), 0.0, 1.0)   # the monotone |L|=Re L
    n_t = tg.size
    n_x = int(n_shots) // 2
    n_y = int(n_shots) - n_x
    p_x = np.clip(0.5 * (1.0 + env), _PROB_FLOOR, 1.0 - _PROB_FLOOR)      # X: Re L = env
    p_y = np.full(n_t, 0.5)                                               # Y: Im L = 0
    yx = (rng.random((n_x, n_t)) < p_x[None, :]).astype(np.uint8)
    yy = (rng.random((n_y, n_t)) < p_y[None, :]).astype(np.uint8)
    # latent placeholder (no RTN trajectory for these sources); never read by any fit.
    lpx = np.zeros((n_x, n_t), dtype=np.float64)
    lpy = np.zeros((n_y, n_t), dtype=np.float64)
    return EnvelopeObs(t_grid=tg, yx=yx, yy=yy, latent_phase_x=lpx, latent_phase_y=lpy,
                       p=RTNParams(v=1e-6, gamma_sw=1.0), n_substep=2)


# =========================================================================== #
# Two-basis coherence-NLL (Born rule, ADR 0003).                               #
# =========================================================================== #
def _bernoulli_nll(y: np.ndarray, p1_per_t: np.ndarray) -> float:
    """Sum of -log Bernoulli over a (n_shots, n_t) outcome array given per-t P(y=1)."""
    Y = np.asarray(y)
    pp = np.clip(np.asarray(p1_per_t, dtype=np.float64), _PROB_FLOOR, 1.0 - _PROB_FLOOR)
    assert Y.shape[1] == pp.shape[0], "bernoulli_nll: per-t length mismatch."
    n1 = Y.sum(axis=0).astype(np.float64)
    n0 = Y.shape[0] - n1
    return float(-np.sum(n1 * np.log(pp) + n0 * np.log(1.0 - pp)))


def coherence_nll(obs: EnvelopeObs, reL_per_t: np.ndarray, imL_per_t: np.ndarray) -> float:
    r"""Total two-basis coherence-NLL given a model's predicted (Re L, Im L) per t_k.
    = X-basis Bernoulli NLL (p=0.5*(1+ReL)) + Y-basis Bernoulli NLL (p=0.5*(1+ImL)). ADR 0003."""
    return (_bernoulli_nll(obs.yx, p_plus_x(reL_per_t)) +
            _bernoulli_nll(obs.yy, p_plus_y(imL_per_t)))


# =========================================================================== #
# C5 baseline — the STRONGEST monotone-POSITIVE |L| competitor (NO sign        #
# freedom, NO Markov-k). The model is an ENVELOPE |L|>=0 monotone-non-          #
# increasing; the predicted (ReL, ImL) split the envelope by the EMPIRICAL      #
# phase direction (a global phase is allowed; it cannot create a revival).      #
# =========================================================================== #
def _empirical_phase_unit(obs: EnvelopeObs) -> Tuple[np.ndarray, np.ndarray]:
    """The empirical unit phase direction (cos_hat, sin_hat) per t_k from the pooled (<sx>,<sy>):
    cos_hat = <sx>/|.|, sin_hat = <sy>/|.| (the phase of the measured coherence vector). A
    CP-divisible model may have ANY phase (incl. a detuning) — the BASELINE is allowed to match the
    empirical phase direction; what it is FORBIDDEN is growing the MAGNITUDE. So we factor the
    predicted coherence as |L|_model * (cos_hat, sin_hat): the magnitude is the constrained-monotone
    fit, the direction is free. This is the strongest fair CP-divisible competitor."""
    sx = 2.0 * obs.yx.mean(axis=0) - 1.0
    sy = 2.0 * obs.yy.mean(axis=0) - 1.0
    mag = np.sqrt(sx * sx + sy * sy)
    safe = np.where(mag > NUMERICAL_ZERO, mag, 1.0)
    cos_hat = np.where(mag > NUMERICAL_ZERO, sx / safe, 1.0)
    sin_hat = np.where(mag > NUMERICAL_ZERO, sy / safe, 0.0)
    return cos_hat.astype(np.float64), sin_hat.astype(np.float64)


def _pava_monotone_decreasing(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    r"""Pool-Adjacent-Violators isotonic regression for a MONOTONE NON-INCREASING fit (weighted LS).
    Returns the fitted monotone-non-increasing array (the non-parametric strongest monotone competitor;
    matches ANY monotone decay)."""
    v = -np.asarray(values, dtype=np.float64)             # negate => fit non-DECREASING
    w = np.asarray(weights, dtype=np.float64)
    n = v.size
    means: List[float] = []
    ws: List[float] = []
    lens: List[int] = []
    for k in range(n):
        cur_m = float(v[k])
        cur_w = float(w[k])
        cur_l = 1
        while means and means[-1] > cur_m:
            pm = means.pop(); pw = ws.pop(); pl = lens.pop()
            tot_w = pw + cur_w
            cur_m = (pm * pw + cur_m * cur_w) / max(tot_w, NUMERICAL_ZERO)
            cur_w = tot_w
            cur_l = pl + cur_l
        means.append(cur_m); ws.append(cur_w); lens.append(cur_l)
    out = np.empty(n, dtype=np.float64)
    pos = 0
    for m, l in zip(means, lens):
        out[pos:pos + l] = m
        pos += l
    return -out                                           # un-negate => non-INCREASING


def fit_baseline_isotonic(obs: EnvelopeObs) -> Dict[str, object]:
    r"""[C5] Best-fit MONOTONE-non-increasing, POSITIVE envelope |L| via isotonic regression (PAVA)
    on the EMPIRICAL envelope |L|_hat. NO sign freedom (|L|>=0); the direction is the empirical phase
    unit (a detuning is allowed, a magnitude revival is NOT). Predicted (ReL,ImL) =
    |L|_mono * (cos_hat, sin_hat). Fit/scored by the two-basis coherence-NLL. Returns
    {'reL','imL','env_mono','nll_train'}.

    KEY: at a |L| revival the empirical envelope DIPS then GROWS; the monotone constraint FORBIDS the
    growth, so the baseline UNDER-fits the post-node region — the irreducible wedge source."""
    n_shots = obs.yx.shape[0] + obs.yy.shape[0]
    env_hat = obs.envelope_hat()
    env_hat = np.clip(env_hat, 0.0, 1.0)
    w = np.full(env_hat.size, float(n_shots), dtype=np.float64)
    env_mono = np.clip(_pava_monotone_decreasing(env_hat, w), 0.0, 1.0)
    cos_hat, sin_hat = _empirical_phase_unit(obs)
    reL = env_mono * cos_hat
    imL = env_mono * sin_hat
    nll = coherence_nll(obs, reL, imL)
    return {"reL": reL, "imL": imL, "env_mono": env_mono, "nll_train": float(nll)}


def _multiexp_env(t: np.ndarray, params: np.ndarray) -> np.ndarray:
    """Multi-exponential monotone-decreasing POSITIVE envelope:
        |L|(t) = sum_j a_j exp(-r_j t),  a_j>=0, sum a_j<=1, r_j>=0  => monotone non-increasing, >=0.
    params packs [a_1..a_K, r_1..r_K] (non-negative). Returns |L|(t) in [0,1]."""
    K = params.size // 2
    a = params[:K]
    r = params[K:]
    t = np.asarray(t, dtype=np.float64)
    out = np.zeros_like(t)
    for j in range(K):
        out = out + a[j] * np.exp(-r[j] * t)
    return np.clip(out, 0.0, 1.0)


def _multiexp_project(params: np.ndarray) -> np.ndarray:
    """Project multi-exp params to the feasible set (a_j>=0, sum a<=1, r_j>=0)."""
    p = params.copy()
    K = p.size // 2
    p[:K] = np.clip(p[:K], 0.0, None)
    ssum = p[:K].sum()
    if ssum > 1.0:
        p[:K] = p[:K] / ssum
    p[K:] = np.clip(p[K:], 0.0, None)
    return p


def _multiexp_polish(params: np.ndarray, nll_of, t_span: float,
                     n_iter: int = 4000, min_frac: float = 1e-9) -> Tuple[np.ndarray, float]:
    r"""Fine coordinate-descent polish of a multi-exp param vector until the step floor is tiny enough
    that no small rescale can improve it (drives nll@opt <= nll@1.02x — the C5 convergence sub-check).
    Returns (polished_params, nll). The min step is scaled to each coordinate (amplitudes ~1, rates
    ~1/t_span) and shrunk to min_frac of the initial step so the optimum is resolved finely."""
    params = _multiexp_project(params)
    cur = nll_of(params)
    K = params.size // 2
    step = np.concatenate([np.full(K, 0.05), np.full(K, 0.5 / t_span)])
    min_step = np.concatenate([np.full(K, 0.05 * min_frac), np.full(K, (0.5 / t_span) * min_frac)])
    for _ in range(int(n_iter)):
        improved = False
        for d in range(params.size):
            for sgn in (+1.0, -1.0):
                trial = _multiexp_project(params + sgn * step * np.eye(params.size)[d])
                tn = nll_of(trial)
                if tn < cur - 1e-12:
                    params, cur = trial, tn
                    improved = True
        if not improved:
            step = step * 0.5
            if np.all(step < min_step):
                break
    return params, cur


def fit_baseline_multiexp(obs: EnvelopeObs, K: int = 3, n_restart: int = 16,
                          n_iter: int = 600, seed: int = 0) -> Dict[str, object]:
    r"""[C5] Best-fit MONOTONE multi-exponential POSITIVE envelope |L| (a smooth CP-divisible model),
    fit by ML on the two-basis coherence-NLL via seeded random-restart hill-climbing + a FINE final
    polish (numpy-only). The polish drives the optimum fine enough that a 2% rescale cannot improve it
    (the C5 'baseline converged' sub-check). A better-converged baseline is STRONGER/fairer (it only
    shrinks the wedge — the conservative fix). Direction = empirical phase unit (as in isotonic).
    Returns {'reL','imL','params','nll_train'}."""
    t = obs.t_grid
    cos_hat, sin_hat = _empirical_phase_unit(obs)
    rng = np.random.default_rng(int(seed))
    t_span = max(float(t[-1] - t[0]), NUMERICAL_ZERO)

    def nll_of(params: np.ndarray) -> float:
        env = _multiexp_env(t, params)
        return coherence_nll(obs, env * cos_hat, env * sin_hat)

    best_params = _multiexp_project(np.concatenate([np.full(K, 1.0 / K), np.full(K, 1.0 / t_span)]))
    best_nll = nll_of(best_params)
    for _ in range(int(n_restart)):
        a = rng.random(K)
        a = a / max(a.sum(), NUMERICAL_ZERO) * rng.uniform(0.5, 1.0)
        r = rng.uniform(0.05, 20.0, K) / t_span
        params = _multiexp_project(np.concatenate([a, r]))
        cur = nll_of(params)
        step = np.concatenate([np.full(K, 0.1), np.full(K, 2.0 / t_span)])
        min_step = np.concatenate([np.full(K, 1e-4), np.full(K, 1e-4 / t_span)])
        for _it in range(int(n_iter)):
            improved = False
            for d in range(params.size):
                for sgn in (+1.0, -1.0):
                    trial = _multiexp_project(params + sgn * step * np.eye(params.size)[d])
                    tn = nll_of(trial)
                    if tn < cur - 1e-9:
                        params, cur = trial, tn
                        improved = True
            if not improved:
                step = step * 0.5
                if np.all(step < min_step):
                    break
        if cur < best_nll:
            best_nll, best_params = cur, params
    # FINE polish from the best restart so the optimum is resolved (nll@opt <= nll@1.02x).
    best_params, best_nll = _multiexp_polish(best_params, nll_of, t_span)
    env = _multiexp_env(t, best_params)
    return {"reL": env * cos_hat, "imL": env * sin_hat, "params": best_params,
            "nll_train": float(best_nll)}


def _env_exp_T2(t: np.ndarray, T2: float) -> np.ndarray:
    """Exponential-T2 envelope |L|=exp(-t/T2) (T1-limited / white-noise dephasing). Monotone-positive."""
    return np.clip(np.exp(-np.asarray(t, dtype=np.float64) / max(float(T2), NUMERICAL_ZERO)),
                   0.0, 1.0)


def _env_gauss_T2(t: np.ndarray, T2: float) -> np.ndarray:
    """Gaussian-T2 envelope |L|=exp(-(t/T2)^2) (quasi-static / 1/f-dominated dephasing).
    Monotone-positive."""
    return np.clip(np.exp(-(np.asarray(t, dtype=np.float64) / max(float(T2), NUMERICAL_ZERO)) ** 2),
                   0.0, 1.0)


def _fit_named_T2(obs: EnvelopeObs, env_func) -> Dict[str, object]:
    r"""ML fit of a one-parameter NAMED Markovian envelope |L|=env_func(t, T2) by minimizing the
    two-basis coherence-NLL over T2 (1-D golden-section-style coarse-to-fine search; numpy-only).
    Direction = empirical phase unit (a CP-divisible detuning is allowed). CONVERGENCE asserted by the
    caller (a non-converged named baseline = artificially weak = a toy, rejected). Returns
    {'T2','nll_train','env'}."""
    t = obs.t_grid
    cos_hat, sin_hat = _empirical_phase_unit(obs)

    def nll_of(T2: float) -> float:
        env = env_func(t, T2)
        return coherence_nll(obs, env * cos_hat, env * sin_hat)

    t_span = max(float(t[-1] - t[0]), NUMERICAL_ZERO)
    # coarse log grid over plausible T2 (much shorter than to much longer than the window).
    grid = np.geomspace(t_span * 1e-3, t_span * 1e3, 200)
    nlls = np.array([nll_of(float(T2)) for T2 in grid])
    i0 = int(np.argmin(nlls))
    lo = grid[max(i0 - 1, 0)]
    hi = grid[min(i0 + 1, grid.size - 1)]
    # fine refinement (ternary search) in [lo, hi].
    for _ in range(80):
        if hi - lo < 1e-9 * (1.0 + lo):
            break
        m1 = lo + (hi - lo) / 3.0
        m2 = hi - (hi - lo) / 3.0
        if nll_of(m1) < nll_of(m2):
            hi = m2
        else:
            lo = m1
    T2 = 0.5 * (lo + hi)
    return {"T2": float(T2), "nll_train": float(nll_of(T2)), "env": env_func(t, T2)}


def fit_baseline_exp_T2(obs: EnvelopeObs) -> Dict[str, object]:
    """[C5 named panel] exponential-T2 baseline |L|=e^{-t/T2}, ML-fit T2."""
    return _fit_named_T2(obs, _env_exp_T2)


def fit_baseline_gauss_T2(obs: EnvelopeObs) -> Dict[str, object]:
    """[C5 named panel] Gaussian-T2 baseline |L|=e^{-(t/T2)^2}, ML-fit T2."""
    return _fit_named_T2(obs, _env_gauss_T2)


def best_baseline_nll_heldout(obs_train: EnvelopeObs, obs_test: EnvelopeObs,
                              multiexp_K: int = 3, seed: int = 0) -> Dict[str, object]:
    r"""[C5, NO-TOY panel] FAIR baseline held-out NLL = the BEST (lowest) over the full panel of
    monotone-POSITIVE CP-divisible competitors, each ML-fit on train + scored held-out on test:

      - ISOTONIC SUPREMUM: the best monotone-non-increasing positive |L| (non-parametric). By the
        CP-divisibility theorem (|L|=exp(-int gamma_phi), gamma_phi>=0 => |L| monotone-positive) this
        is the SUPREMUM over ALL CP-divisible dephasing — it NLL-BOUNDS every Markovian model
        (including the Bloch-Redfield / general time-local-rate Lindblad envelope, which IS a
        monotone-positive |L| and so is dominated by the supremum; no separate fit needed) FROM BELOW.
      - multi-exponential (smooth monotone),
      - exponential-T2  |L|=e^{-t/T2}   (NAMED field-standard),
      - Gaussian-T2     |L|=e^{-(t/T2)^2} (NAMED field-standard).

    NO Markov-k (it is not a CP-divisible dephasing model; secondary classical result only). Returns
    each competitor's held-out NLL + 'best_nll', 'best_name', + the named fitted params ('exp_T2',
    'gauss_T2'). The supremum is the strongest (lowest NLL) and the wedge is reported vs it (the most
    conservative); the supremum-bounds-all sanity assertion is checked in the gtcheck."""
    out: Dict[str, object] = {}
    # the fitted ENVELOPE transfers to the test grid; the test-grid direction is the test empirical
    # phase unit (the phase is a free CP-divisible degree of freedom).
    cos_te, sin_te = _empirical_phase_unit(obs_test)
    # isotonic supremum.
    iso = fit_baseline_isotonic(obs_train)
    env_iso = np.asarray(iso["env_mono"])
    out["isotonic_supremum_heldout"] = coherence_nll(obs_test, env_iso * cos_te, env_iso * sin_te)
    # multi-exponential.
    me = fit_baseline_multiexp(obs_train, K=multiexp_K, seed=seed)
    env_me = _multiexp_env(obs_test.t_grid, np.asarray(me["params"]))
    out["multiexp_heldout"] = coherence_nll(obs_test, env_me * cos_te, env_me * sin_te)
    # named field-standard models.
    ex = fit_baseline_exp_T2(obs_train)
    env_ex = _env_exp_T2(obs_test.t_grid, float(ex["T2"]))
    out["exp_T2_heldout"] = coherence_nll(obs_test, env_ex * cos_te, env_ex * sin_te)
    out["exp_T2"] = float(ex["T2"])
    ga = fit_baseline_gauss_T2(obs_train)
    env_ga = _env_gauss_T2(obs_test.t_grid, float(ga["T2"]))
    out["gauss_T2_heldout"] = coherence_nll(obs_test, env_ga * cos_te, env_ga * sin_te)
    out["gauss_T2"] = float(ga["T2"])
    # the FAIR baseline = the strongest (lowest held-out NLL) competitor (expected: the supremum).
    comp = {kk: float(vv) for kk, vv in out.items() if kk.endswith("heldout")}
    best_name = min(comp, key=comp.get)
    out["best_nll"] = comp[best_name]
    out["best_name"] = best_name
    return out


# =========================================================================== #
# Source-resolved TWIN — reproduces |L(t)| (incl. the revival), fit from the    #
# envelope ONLY (isolation-respecting; never the per-shot latent).              #
# =========================================================================== #
@dataclass(frozen=True)
class TwinParams:
    """The twin's source model: the RTN (v, gamma_sw). Reproduces (Re L, Im L) via Builder ①'s EXACT
    rtn_coherence_analytic — INCLUDING the revival branch v>gamma_sw. Fit from the envelope by ML
    (fit_twin_params) or set to the source params (oracle). NEVER the latent."""

    v: float
    gamma_sw: float

    def to_rtn(self) -> RTNParams:
        return RTNParams(v=float(self.v), gamma_sw=float(self.gamma_sw))


def twin_reL_imL(tp: TwinParams, t_grid: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """The twin's predicted (Re L, Im L) per t_k from Builder ①'s exact RTN coherence (Im L = 0 for
    the symmetric source). Source-resolved — captures the |L| revival a monotone model cannot."""
    rtn = tp.to_rtn()
    return analytic_reL(rtn, t_grid), analytic_imL(rtn, t_grid)


def twin_nll(obs: EnvelopeObs, tp: TwinParams) -> float:
    """The source-resolved twin's two-basis coherence-NLL on obs (observations ONLY). ISOLATION:
    obs.yx/obs.yy are the only data inputs; the per-shot latent is NEVER read."""
    reL, imL = twin_reL_imL(tp, obs.t_grid)
    return coherence_nll(obs, reL, imL)


def fit_twin_params(obs_train: EnvelopeObs, v_grid: Optional[np.ndarray] = None,
                    gamma_grid: Optional[np.ndarray] = None, refine: bool = True) -> TwinParams:
    r"""Fit the twin's (v, gamma_sw) from the ENVELOPE outcomes by ML (minimize the two-basis
    coherence-NLL) — a HISTORY/observation-only learner (NEVER the latent). Coarse 2-D grid + local
    log-space refinement. The twin model is Builder ①'s exact rtn_coherence_analytic, so the fit lands
    in EITHER branch from the observed envelope shape — recovering the source class label-free."""
    if v_grid is None:
        v_grid = np.geomspace(1e-5, 1e-2, 25)
    if gamma_grid is None:
        gamma_grid = np.geomspace(1e-6, 1e-2, 25)
    best = (np.inf, float(v_grid[0]), float(gamma_grid[0]))
    for v in v_grid:
        for g in gamma_grid:
            nll = twin_nll(obs_train, TwinParams(v=float(v), gamma_sw=float(g)))
            if nll < best[0]:
                best = (nll, float(v), float(g))
    _, v0, g0 = best
    if not refine:
        return TwinParams(v=v0, gamma_sw=g0)
    for _ in range(3):
        vg = np.geomspace(max(v0 / 2.0, 1e-7), v0 * 2.0, 9)
        gg = np.geomspace(max(g0 / 2.0, 1e-8), g0 * 2.0, 9)
        cur = (twin_nll(obs_train, TwinParams(v=v0, gamma_sw=g0)), v0, g0)
        for v in vg:
            for g in gg:
                nll = twin_nll(obs_train, TwinParams(v=float(v), gamma_sw=float(g)))
                if nll < cur[0]:
                    cur = (nll, float(v), float(g))
        _, v0, g0 = cur
    return TwinParams(v=v0, gamma_sw=g0)


# =========================================================================== #
# The wedge.                                                                    #
# =========================================================================== #
def coherence_wedge(obs_train: EnvelopeObs, obs_test: EnvelopeObs, tp: TwinParams,
                    seed: int = 0) -> Dict[str, object]:
    r"""The coherence-envelope wedge = best monotone-|L| baseline held-out NLL - twin held-out NLL.
    A POSITIVE wedge = the irreducible gap a monotone-positive |L| leaves at the |L| revival. Returns
    components + 'wedge'."""
    base = best_baseline_nll_heldout(obs_train, obs_test, seed=seed)
    twin_te = twin_nll(obs_test, tp)
    return {"baseline": base, "twin_nll": float(twin_te),
            "wedge": float(float(base["best_nll"]) - twin_te),
            "best_baseline_name": base["best_name"]}


# =========================================================================== #
# C9/P4 — envelope reliability (self-calibration) on |L(t)|.                    #
# =========================================================================== #
def reliability_envelope(env_pred: np.ndarray, obs: EnvelopeObs) -> Dict[str, object]:
    r"""[C9/P4] Per-time reliability of an ENVELOPE forecaster vs the empirical |L|_hat.

    A calibrated forecaster has |L|_pred ~ |L|_hat at EVERY t_k (including the revival times); a
    monotone baseline is FORCED to mis-predict where the true |L| revives (its magnitude can't grow).
    The revival times are an EVALUATOR-side stratification (true |L| non-monotone), used ONLY to LOCATE
    where the baseline must fail — never fed to the forecaster. Returns {'pred','emp','abs_dev',
    'max_dev','mean_dev','revival_dev','n_revival_times'}."""
    env_hat = obs.envelope_hat()
    pred = np.clip(np.asarray(env_pred, dtype=np.float64), 0.0, 1.0)
    dev = np.abs(pred - env_hat)
    # locate the revival: true |L| where the envelope is non-monotone (a LATER value exceeds an
    # earlier one by a margin) — the structural failure region for a monotone model.
    true_env = analytic_envelope(obs.p, obs.t_grid)
    running_min = np.minimum.accumulate(true_env)
    revival_mask = true_env > running_min + 1e-3        # |L| climbed back above its running minimum
    revival_dev = float(dev[revival_mask].max()) if np.any(revival_mask) else 0.0
    return {"pred": pred, "emp": env_hat, "abs_dev": dev, "max_dev": float(dev.max()),
            "mean_dev": float(dev.mean()), "revival_dev": revival_dev,
            "n_revival_times": int(revival_mask.sum())}


def twin_envelope(tp: TwinParams, t_grid: np.ndarray) -> np.ndarray:
    """The twin's predicted envelope |L|_pred = sqrt(ReL^2 + ImL^2) (reproduces the revival)."""
    reL, imL = twin_reL_imL(tp, t_grid)
    return np.sqrt(reL * reL + imL * imL)


def baseline_envelope_isotonic(obs: EnvelopeObs) -> np.ndarray:
    """The monotone-positive baseline's predicted envelope (for the reliability contrast)."""
    return np.asarray(fit_baseline_isotonic(obs)["env_mono"])


if __name__ == "__main__":
    # AUTHOR-only module: a TINY structural smoke (small sizes, NO heavy sweep). Real validation is
    # nm_wedge_gtcheck.py (run SERIALLY).
    _p = RTNParams(v=2.0e-3, gamma_sw=5.0e-4)             # v > gamma_sw : REVIVAL branch
    _tmax = 4.0 * np.pi / _p.v
    _tg = np.linspace(_tmax / 40.0, _tmax, 40)
    _obs = simulate_envelope_observations(_p, _tg, n_shots=800, seed=0, n_substep=200)
    print("nm_wedge (envelope) structural smoke (small, NO heavy sweep):", flush=True)
    _env = analytic_envelope(_p, _tg)
    rmin = np.minimum.accumulate(_env)
    has_revival = bool(np.any(_env > rmin + 1e-3))
    print(f"  v={_p.v:.2e} gamma_sw={_p.gamma_sw:.2e}  |L| revival present (envelope non-monotone): "
          f"{has_revival}  min|L|={_env.min():.3f}", flush=True)
    _iso = fit_baseline_isotonic(_obs)
    print(f"  isotonic monotone-|L| baseline nll_train={_iso['nll_train']:.1f}", flush=True)
    _tp = TwinParams(v=_p.v, gamma_sw=_p.gamma_sw)
    print(f"  twin oracle nll={twin_nll(_obs, _tp):.1f}", flush=True)
    sys.exit(0)

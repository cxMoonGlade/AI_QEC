"""H2 (HARDEN) -- PRE-REGISTRATION (stubs skip-marked; machinery is the next build).

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

CENTRAL PREDICTION -- two named outcomes (derive which, do NOT pre-quote; it is
phi-and-probe dependent). Fit a factorized learner to a non-factorized teacher. At
low r it fits (calib_KL~0) and is confidently wrong. As crosstalk probes enter:
  (a) factorized calib_KL DEGRADES -- the misspecification surfaces in the fit, the
      fit catches it (benign); or
  (b) calib_KL STAYS ~0 but the do() band still misses -- irreducible overconfidence,
      the scary cell, fixable only by the non-factorized learner.

CLAIM 2 -- what resolves it. Non-factorized learner = factorized + ONE ZZ coupling
term (minimal escalation, so B_misspec is attributable to that single DOF). It closes
the gap once crosstalk probes enter; the factorized band stays open regardless. The
two curves' contrast IS the misspecification-gap plot.

PRECONDITION GUARD (the H2 analog of H1's). Confirm factorized calib_KL~0 at low r:
overconfidence requires the misspecification be INVISIBLE in the fit (Pauli-shadowing
again). If the factorized learner cannot even fit, that is DETECTABLE misspecification,
not overconfidence -- a different, less dangerous finding.

FALSIFICATION. Factorized band COVERS truth -> factorization is benign at this
crosstalk strength (honest; sweep phi up). Non-factorized learner CANNOT close the gap
with crosstalk probes -> the coupling isn't in-class identifiable -> stop/redesign.

FORK. Primary: coherent ZZ crosstalk exp(-i phi Z@Z) on the loc0-loc1 pair -- the
frontier-standard residual-ZZ mechanism; coherent (continues the thread, and moments
Pauli-shadow it -> the hard case); ties to the exact pair H1 flagged. Control:
correlated-stochastic crosstalk -- does overconfidence appear, or do the factorized
learner's pairwise moments absorb it? If only the coherent case breaks it, that is the
Pauli-shadow theme one level up. Stays on the exact backend (a coupling term, not more
qubits -- no backend swap; that is H5).

MACHINERY TO BUILD (un-skip each test as it lands):
  1. forward: a 2-qubit coherent ZZ coupling exp(-i phi Z@Z) on a data pair, per round
     (forward/exact -- apply_unitary already takes 2-qubit targets; needs a coupling
     hook alongside the per-location channel_field).
  2. teacher: non-factorized = per-location channels + the ZZ coupling (mechanisms/).
  3. learner: non-factorized = factorized RepCodeTwin + one learnable phi.
  4. B_misspec: the factorized learner's do() band vs the non-factorized truth.

Metrics (docs/METRICS.md): calib_KL = calibrate(...)["total_kl"]; do() band =
audit.bands.tier0_alias_band; B_misspec = band-vs-truth gap (the third band, S1.2).
"""

from __future__ import annotations

import pytest

_BLOCKED = "H2 pre-registration -- blocked on the non-factorized teacher/learner machinery (see docstring)"


@pytest.mark.skip(reason=_BLOCKED)
def test_h2_factorized_precondition_fits_at_low_r():
    # PRECONDITION: the factorized learner fits the non-factorized teacher at low r
    # (calib_KL ~ 0) -- the crosstalk is invisible in the fit (Pauli-shadowed), so a
    # wrong prediction is OVERCONFIDENCE, not detectable misspecification.
    #   assert factorized_calib_kl(r=1) < 1e-6
    ...


@pytest.mark.skip(reason=_BLOCKED)
def test_h2_two_outcomes_calib_kl_degrades_or_stays_flat():
    # CENTRAL PREDICTION (two named outcomes): as crosstalk probes enter, EITHER the
    # factorized calib_KL degrades (a: benign, fit catches it) OR it stays ~0 while the
    # do() band still misses (b: overconfidence). Pre-registered; measure which.
    #   record factorized_calib_kl(r) across crosstalk-probe richness; classify (a)/(b)
    ...


@pytest.mark.skip(reason=_BLOCKED)
def test_h2_factorized_band_overconfident_nonfactorized_closes():
    # CLAIM 2 + band-coverage pin: the factorized do() band fails to contain the truth
    # (B_misspec > band), and stays open regardless of crosstalk-probe richness; the
    # non-factorized learner (factorized + one phi) closes the gap once those probes
    # enter. The two band curves' contrast is the misspecification-gap plot.
    #   assert factorized_band_misses_truth (B_misspec > factorized_band)
    #   assert nonfactorized_closes_with_crosstalk_probes
    ...


@pytest.mark.skip(reason=_BLOCKED)
def test_h2_stochastic_crosstalk_control():
    # CONTROL (fork): correlated-STOCHASTIC crosstalk -- does overconfidence appear, or
    # do the factorized learner's pairwise moments absorb it? If only the COHERENT case
    # breaks the factorized band, that is the Pauli-shadow theme one level up.
    ...

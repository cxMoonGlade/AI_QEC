"""Decision-Regret Engine -- Go/No-Go gate (the in-distribution preview).

Decides whether to commit to plan2.md (the calibrated prioritization engine) or land
the bounded four-capability result. Reframed (this session) onto EXISTING machinery:
the decision band is coordinate-invariant, so no GKSL learner is needed -- the Kraus
learner already represents non-Pauli/non-Clifford, and `tier0_alias_band`'s
`g^T H^+ g` IS the linear Fisher-pushforward onto `do()->ΔLER` (plan2's phantom
`decision_pushforward`). The one genuinely new module is the EXACT
finite-displacement band for Claim B's slope test (the linear band overshoots).

Sources (representability ⊥ identifiability; §2 of the gate):
  loc0 coherent RX  -> Claim B (representable-partial, UNidentifiable at low r)
  loc1 pure AmpDamp -> Claim A (provably NOT Pauli-representable, identifiable)
  loc2 Pauli        -> anchor (both steelmen pass)

Functionals differ per source (where the alias projects): `do(E->I)` on |1_L> for the
dissipative source (it is invisible on |0_L>, the fixed point); a phase-sensitive
(repeated-storage) functional for the coherent source (`do` on |0_L> is phase-
insensitive -- the H0 result).

Results (run 2026-06-09): engine `calib_KL`~1e-15 (matched). Claim A -- on the pure-damp
source, engine miss 2e-9 vs the exact-moment Pauli twirl's 1.8e-2 (46% of the true ΔLER);
the non-unital gap projects. P0 -- twirl fooled on the dissipative source; the engine
POINT misses the coherent source's phase-sensitive ΔLER by 0.123 at r=1 (calib_KL at
floor) and recovers by r=2.

CLAIM B VERDICT (explored this session). The decision-regret band is REAL -- the identified
set spans the >0.1 regret (point and truth both at NLL_min, 0.123 apart in F) -- but it is
NOT cheaply computable: NO slack calibrates a LOCAL band (overconfident at the real alias
r=1, never covering; vacuous at r=2/3, slope 20-56x), because local ascent cannot traverse
the curved / gauge-redundant identified set between the MLE point and truth. Earning slope~1
needs GLOBAL continuation machinery (plan2's explicitly-deferred projected-ascent), not an
afternoon. So the gate's signal: BANK THE CLAIM-A FLOOR (non-Pauli-capable calibration beats
the field's Pauli/DEM standard -- real, and bigger than the bounded plan); do NOT build
plan2's superstructure on an un-computed band. The continuation band is the genuine next
investment IF plan2 is pursued -- and the gate just priced it for an afternoon.
"""

from __future__ import annotations

import pytest

from qec_twin.audit.bands import tier0_alias_band
from qec_twin.calibration.nll import calibrate
from qec_twin.contexts.ladder import (
    RepCodeContext,
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
from qec_twin.mechanisms.teachers import mixed_mechanism_field, pauli_twirl_field

SPECS = [("coherent", 0.03, 0.6), ("pure_damp", 0.08), ("pauli", 0.04)]
DAMP_SRC, COH_SRC = 1, 0


def _dler(field, eval_ctx, decoder, i):
    base = logical_error_rate(run_context(eval_ctx, channel_field=field), decoder, logical_reference=eval_ctx.logical)
    removed = logical_error_rate(
        run_context(eval_ctx, channel_field=intervene_field(field, i, do_remove)), decoder,
        logical_reference=eval_ctx.logical,
    )
    return float(removed - base)


@pytest.fixture(scope="module")
def gate():
    teacher = mixed_mechanism_field(SPECS)
    result = calibrate(teacher, calibration_contexts(1), distance=3, num_kraus=2, steps=600, seed=0)
    twin = result["twin"].field()
    twirl = pauli_twirl_field(teacher, 3)  # strongest Pauli steelman (exact teacher moments)

    eval_L1 = RepCodeContext(3, 4, 1, -1, "eval:R4-L1")          # dissipative is consequential here
    eval_ps = RepCodeContext(3, 4, 0, -1, "eval:R4-k3", repeats=3)  # phase-sensitive (coherent)
    dec_L1, dec_ps = build_frozen_decoder(eval_L1), build_frozen_decoder(eval_ps)

    per_source_L1 = {
        i: {
            "true": _dler(teacher, eval_L1, dec_L1, i),
            "engine": _dler(twin, eval_L1, dec_L1, i),
            "twirl": _dler(twirl, eval_L1, dec_L1, i),
        }
        for i in range(len(SPECS))
    }
    coh_ps = {
        "true": _dler(teacher, eval_ps, dec_ps, COH_SRC),
        "point": _dler(twin, eval_ps, dec_ps, COH_SRC),
    }
    return {"calib_kl": float(result["total_kl"]), "L1": per_source_L1, "coh_ps": coh_ps}


def test_gng_step0_pushforward_is_green():
    # Step 0 (reframed): the linear Fisher-pushforward onto do()->ΔLER EXISTS as
    # tier0_alias_band's g^T H^+ g -- not plan2's phantom decision_pushforward. Green.
    teacher = mixed_mechanism_field(SPECS)
    contexts = calibration_contexts(1)
    twin = calibrate(teacher, contexts, distance=3, num_kraus=2, steps=300, seed=0)["twin"]
    band = tier0_alias_band(
        twin, contexts, [run_context(c, channel_field=teacher) for c in contexts],
        eval_context=held_out_eval_context(), decoder=build_frozen_decoder(held_out_eval_context()),
        target_i=COH_SRC, intervention=do_remove, shots=20_000,
    )
    assert band["inv_quad"] >= 0.0 and band["statistical_band"] >= 0.0  # the pushforward is real


def test_gng_p0_steelman_a_fooled_on_nonpauli(gate):
    # P0 precondition (Claim A side): the Pauli steelman is confidently WRONG on the
    # non-unital source, while the engine is not -- a winnable game (else INCONCLUSIVE).
    s = gate["L1"][DAMP_SRC]
    assert abs(s["twirl"] - s["true"]) > 5e-3
    assert abs(s["engine"] - s["true"]) < 1e-6


def test_gng_p0_steelman_b_fooled_on_coherent(gate):
    # P0 precondition (Claim B side): the engine POINT misses the coherent source's
    # phase-sensitive ΔLER at low r, WHILE calib_KL is at the floor (hidden failure,
    # not a bad fit). Steelman B is fooled.
    assert gate["calib_kl"] < 1e-6
    assert abs(gate["coh_ps"]["point"] - gate["coh_ps"]["true"]) > 1e-2


def test_gng_claim_a_nonpauli_representation_projects(gate):
    # Claim A (the floor): on the pure-damping source the engine matches truth while no
    # Pauli model can (unital ⊉ non-unital is a theorem), and the gap PROJECTS onto the
    # decision (it is a large fraction of the true ΔLER, not a rounding effect).
    s = gate["L1"][DAMP_SRC]
    assert abs(s["engine"] - s["true"]) < 1e-6                      # engine represents it
    assert abs(s["twirl"] - s["true"]) > 5e-3                       # Pauli cannot
    assert abs(s["twirl"] - s["true"]) / abs(s["true"]) > 0.2       # ...and it projects (~46%)


def test_gng_claim_b_regret_is_real_but_band_is_the_open_bet(gate):
    # Claim B verdict. The engine POINT recovers the calibration joint (calib_KL~0) yet its
    # phase-sensitive do() ΔLER differs from truth by >0.1: the identified set SPANS the
    # regret (point and truth both at NLL_min), so a point is under-determined and a band is
    # necessary -- it must span >=0.1 to be honest. FINDING (explored this session, /tmp
    # scripts): no slack calibrates a LOCAL band -- overconfident at the real alias (r=1,
    # never covers) and vacuous at r=2/3 (slope 20-56x); local ascent cannot traverse the
    # curved/gauge-redundant identified set between point and truth. Earning slope~1 needs
    # GLOBAL continuation machinery (plan2's deferred projected-ascent), not an afternoon.
    # => Bank the Claim-A floor; do NOT build plan2's superstructure on an un-computed band.
    assert gate["calib_kl"] < 1e-6                                          # point in the identified set
    assert abs(gate["coh_ps"]["point"] - gate["coh_ps"]["true"]) > 0.1     # ...yet the regret is in it too

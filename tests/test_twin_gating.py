"""D5 (ADR 0008): identifiability gating.

D5a (DEM layer, genuinely first): the repetition code is anchor-degenerate (every
detector is shared, so no fault is mechanism-identifiable from structure alone)
and its first-moment learnable-rate subspace is rank-deficient (an explicit alias
quotient). D5b (channel layer, PARTIAL -- co-built with D2): ``girsanov_split``
exactly separates the Pauli "quadratic variation" from the coherent "drift", and
``has_coherent_drift`` is the *qualitative* necessary-condition gate; the
*quantitative* per-direction B_LER prediction is a stub until D2's high-r forwards
exist (forcing it now would give false confidence on the coherent slice).
"""

from __future__ import annotations

from qec_twin.audit.gating import (
    anchor_features,
    girsanov_split,
    has_coherent_drift,
    learnable_first_moment_dim,
    predict_exotic_drop_level,
    rep_code_parity_map,
)
from qec_twin.mechanisms.teachers import (
    coherent_overrotation_field,
    coherent_overrotation_kraus,
)
from qec_twin.forward.exact.circuit_sim import bit_flip

RATES = [0.02, 0.03, 0.02]
THETAS = [0.6, 0.7, 0.5]


# --- D5a: DEM layer (done) ------------------------------------------------- #
def test_rep_code_is_anchor_degenerate_with_aliased_learnable_dof() -> None:
    parity_map = rep_code_parity_map(3, 4)
    anchors = anchor_features(parity_map)
    learnable = learnable_first_moment_dim(parity_map)

    # Every detector is shared by >= 2 faults, so no fault has an anchor: the rep
    # code has zero structural mechanism-identifiability (must lean on context).
    assert anchors["num_identifiable"] == 0
    # And the first-moment learnable-rate subspace is strictly rank-deficient: an
    # explicit Pauli-layer alias quotient (the thing probe richness must shrink).
    assert learnable["first_moment_rank"] < learnable["num_faults"]
    assert learnable["aliased"] > 0


# --- D5b: channel layer (partial -- decomposition + qualitative gate) ------- #
def test_girsanov_split_separates_pauli_from_coherent() -> None:
    pauli = girsanov_split(bit_flip(0.05))
    assert pauli["coherent_offdiag"] < 1e-9
    assert pauli["drift"] < 1e-9
    assert pauli["second_order_identifiable"] is True

    coherent = girsanov_split(coherent_overrotation_kraus(0.02, 0.6))
    assert coherent["coherent_offdiag"] > 0.1
    assert coherent["second_order_identifiable"] is False


def test_coherent_drift_grows_with_rotation_angle() -> None:
    small = girsanov_split(coherent_overrotation_kraus(0.02, 0.3))["coherent_offdiag"]
    large = girsanov_split(coherent_overrotation_kraus(0.02, 0.9))["coherent_offdiag"]
    assert large > small > 0.0


def test_has_coherent_drift_is_a_qualitative_gate() -> None:
    # Coherent teacher carries drift a second-order/DEM twin must miss (necessary
    # condition for the moment-matched control to fail -- NOT the quantitative
    # prediction, which is D5b/D2).
    coherent_teacher = coherent_overrotation_field(RATES, THETAS)
    assert has_coherent_drift(coherent_teacher, 3) is True

    # Pure Pauli teacher: no drift -> moment-matching has no coherent blind spot.
    pauli_teacher = lambda t, i: bit_flip([0.04, 0.09, 0.06][i])  # noqa: E731
    assert has_coherent_drift(pauli_teacher, 3) is False


def test_d5b_predicts_exotic_drop_at_first_phase_sensitive_level() -> None:
    # D5b structural prediction (co-built with D2): the coherent teacher's exotic
    # error must drop at k=3, the first calibration level carrying a phase-
    # sensitive (pre_rotation) probe -- the pre-registered hypothesis the measured
    # D2 curve confirms (exotic KL ~0.57 for k<=2 -> ~6e-6 at k=3).
    coherent_teacher = coherent_overrotation_field(RATES, THETAS)
    assert predict_exotic_drop_level(coherent_teacher, 3)["predicted_drop_level"] == 3

    # A drift-free Pauli teacher needs no phase-sensitive probe -> predicted 0.
    pauli_teacher = lambda t, i: bit_flip([0.04, 0.09, 0.06][i])  # noqa: E731
    assert predict_exotic_drop_level(pauli_teacher, 3)["predicted_drop_level"] == 0

"""D2 (ADR 0008): calibrate-on-r<=k, predict the held-out coherent exotic.

The finance vanilla->exotic protocol on the toy. The headline: the twin fits its
calibration data at every richness (calib_kl ~ 0), the Z-basis do() knob is
already good by k=2, yet the held-out PHASE-SENSITIVE exotic stays Pauli-shadowed
until basis-rotated probes enter calibration -- and collapses exactly at the
level D5b pre-registered (k=3). This is the out-of-basis counterfactual error the
in-basis knob hides, made quantitative (observational adequacy != interventional
validity).
"""

from __future__ import annotations

from qec_twin.contexts.ladder import held_out_eval_context
from qec_twin.audit.gating import predict_exotic_drop_level
from qec_twin.knobs.intervention import build_frozen_decoder
from qec_twin.mechanisms.teachers import coherent_overrotation_field
from qec_twin.audit.validity import predict_held_out_curve

RATES = [0.02, 0.03, 0.02]
THETAS = [0.6, 0.7, 0.5]


def test_exotic_error_collapses_at_d5b_predicted_richness() -> None:
    teacher = coherent_overrotation_field(RATES, THETAS)
    eval_ctx = held_out_eval_context()
    decoder = build_frozen_decoder(eval_ctx)

    # D5b pre-registers the drop at the first phase-sensitive calibration level.
    predicted = predict_exotic_drop_level(teacher, 3)["predicted_drop_level"]
    assert predicted == 3

    # D2 measures the levels straddling the prediction.
    curve = predict_held_out_curve(
        teacher, eval_context=eval_ctx, decoder=decoder,
        levels=(2, predicted), num_kraus=3, steps=200, seed=0,
    )
    rows = {row["k"]: row for row in curve["curve"]}

    # Observational adequacy holds on both sides -- the calibration fit is ~perfect.
    assert rows[2]["calib_kl"] < 1e-6
    assert rows[predicted]["calib_kl"] < 1e-6

    # Below the predicted level the phase-sensitive exotic is Pauli-shadowed...
    assert rows[2]["exotic_obs_error_max"] > 0.1
    # ...and collapses once phase-sensitive probes enter calibration (the drop).
    assert rows[predicted]["exotic_obs_error_max"] < 1e-3
    assert rows[2]["exotic_obs_error_max"] > 100 * rows[predicted]["exotic_obs_error_max"]

    # The contrast that makes the point: at k=2 the in-basis Z knob is ALREADY
    # good, while the out-of-basis exotic observable is not -- the in-basis knob
    # hides the residual alias the exotic reveals.
    assert rows[2]["B_LER_max"] < 1e-4

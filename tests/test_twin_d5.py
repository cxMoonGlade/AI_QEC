"""Make-it-harder step 1: the B loop closes at distance 5.

Code-scaling d3->d5 (the parity backend keeps it tractable) does not break the
loop: a coherent 5-location teacher is calibrated label-free (observational
adequacy holds -- the GF(2) bijection is robust to distance), and its do() knob is
recovered against the controlled teacher under the now NON-TRIVIAL d5 MWPM decoder
(d5 corrects 2 errors). So the falsification boundary is not at distance -- it is
the richer-mechanism axis (step 2).
"""

from __future__ import annotations

from qec_twin.calibration.nll import calibrate
from qec_twin.contexts.ladder import RepCodeContext, run_context
from qec_twin.knobs.intervention import (
    build_frozen_decoder,
    do_remove,
    intervene_field,
    logical_error_rate,
)
from qec_twin.mechanisms.teachers import coherent_overrotation_field

RATES = [0.02, 0.03, 0.02, 0.03, 0.02]
THETAS = [0.6, 0.7, 0.5, 0.65, 0.55]
TARGET = 2


def test_b_loop_closes_at_distance_five() -> None:
    teacher = coherent_overrotation_field(RATES, THETAS)
    # d5 ladder at R1, R2 (R3 = 2**17 is exact but slow; R4 = 2**21 intractable).
    contexts = [
        RepCodeContext(5, 1, 0, 1, "d5R1L0"),
        RepCodeContext(5, 2, 0, 1, "d5R2L0"),
        RepCodeContext(5, 1, 1, 1, "d5R1L1"),
        RepCodeContext(5, 2, 1, 1, "d5R2L1"),
    ]
    eval_ctx = RepCodeContext(5, 2, 0, -1, "d5-eval-R2")

    result = calibrate(teacher, contexts, distance=5, num_kraus=2, steps=200, seed=0)
    # Observational adequacy at d5 -- the bijection / representability is robust.
    assert result["total_kl"] < 1e-5

    twin = result["twin"]
    decoder = build_frozen_decoder(eval_ctx)  # non-trivial d5 MWPM

    base_teacher = logical_error_rate(run_context(eval_ctx, channel_field=teacher), decoder)
    base_twin = logical_error_rate(run_context(eval_ctx, channel_field=twin.field()), decoder)
    do_teacher = logical_error_rate(
        run_context(eval_ctx, channel_field=intervene_field(teacher, TARGET, do_remove)), decoder
    )
    do_twin = logical_error_rate(
        run_context(eval_ctx, channel_field=intervene_field(twin.field(), TARGET, do_remove)), decoder
    )

    assert base_teacher > 0.005  # the knob has real signal
    assert abs(base_teacher - base_twin) < 1e-4  # base LER matches
    # The counterfactual knob closes at d5 with the non-trivial MWPM decoder.
    assert abs((do_teacher - base_teacher) - (do_twin - base_twin)) < 1e-3

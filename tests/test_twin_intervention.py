"""B4: channel-level do() knobs, frozen decoder, and counterfactual-validity scores.

On the identifiable regime (a per-location Pauli bit-flip teacher, Z-basis r=1
ladder) the calibrated twin's *predicted* counterfactual effect matches the
teacher's *true* effect: removing or weakening a location's channel changes the
held-out LER by the same amount for twin and teacher (small B_LER / B_obs), and
the knob ranks the locations physically (worst location -> largest LER drop). The
do() transforms are CPTP, and the frozen decoder gives zero LER with no noise.

(This is the positive, identifiable case that proves the loop. The coherent /
non-Clifford slice where the observational alias quotient makes B_* large unless
probe richness is high is the separate B5 study.)
"""

from __future__ import annotations

import pytest
import torch

from qec_twin.calibration.nll import calibrate
from qec_twin.contexts.ladder import (
    calibration_contexts,
    held_out_eval_context,
    run_context,
)
from qec_twin.knobs.intervention import (
    build_frozen_decoder,
    counterfactual_scores,
    do_remove,
    do_weaken,
    logical_error_rate,
)
from qec_twin.forward.exact.circuit_sim import bit_flip

RATES = [0.04, 0.09, 0.06]


def _teacher(t: int, i: int):
    return bit_flip(RATES[i])


@pytest.fixture(scope="module")
def calibrated():
    contexts = calibration_contexts(1)
    result = calibrate(_teacher, contexts, distance=3, num_kraus=2, steps=300, seed=0)
    eval_ctx = held_out_eval_context()
    decoder = build_frozen_decoder(eval_ctx)
    return result["twin"], eval_ctx, decoder


def test_do_transforms_are_cptp() -> None:
    kraus = bit_flip(0.09)
    identity = torch.eye(2, dtype=kraus.dtype)

    removed = do_remove(kraus)
    assert torch.allclose(removed, identity.unsqueeze(0))

    weakened = do_weaken(kraus, 0.3)
    completeness = torch.einsum("eij,eik->jk", weakened.conj(), weakened)
    assert torch.linalg.matrix_norm(completeness - identity).item() < 1e-12


def test_frozen_decoder_gives_zero_ler_without_noise(calibrated) -> None:
    _twin, eval_ctx, decoder = calibrated
    noiseless = run_context(eval_ctx, channel_field=lambda t, i: None)
    assert logical_error_rate(noiseless, decoder) == 0.0


def test_calibrated_twin_matches_teacher_base_ler(calibrated) -> None:
    twin, eval_ctx, decoder = calibrated
    base_teacher = logical_error_rate(run_context(eval_ctx, channel_field=_teacher), decoder)
    base_twin = logical_error_rate(run_context(eval_ctx, channel_field=twin.field()), decoder)
    assert base_teacher > 0.01  # the knob has real signal to get right
    assert abs(base_teacher - base_twin) < 1e-6


def test_tier0_remove_knob_matches_teacher_and_ranks_locations(calibrated) -> None:
    twin, eval_ctx, decoder = calibrated
    dler_teacher = []
    for i in range(3):
        scores = counterfactual_scores(
            _teacher, twin, eval_ctx, decoder, target_i=i, intervention=do_remove
        )
        assert scores["B_LER"] < 1e-6  # twin's knob == teacher's true knob
        assert scores["B_obs"] < 1e-6
        assert scores["dLER_teacher"] < 0  # removing noise reduces logical error
        dler_teacher.append(scores["dLER_teacher"])

    # The worst location (i=1, p=0.09) must give the largest LER reduction.
    assert dler_teacher[1] < dler_teacher[0]
    assert dler_teacher[1] < dler_teacher[2]


def test_tier1_weaken_matches_teacher_and_is_milder_than_removal(calibrated) -> None:
    twin, eval_ctx, decoder = calibrated
    weaken = counterfactual_scores(
        _teacher, twin, eval_ctx, decoder, target_i=1,
        intervention=lambda k: do_weaken(k, 0.5),
    )
    remove = counterfactual_scores(
        _teacher, twin, eval_ctx, decoder, target_i=1, intervention=do_remove
    )
    assert weaken["B_LER"] < 1e-6
    assert weaken["dLER_teacher"] < 0
    # Half-weakening reduces LER, but less than full removal.
    assert abs(weaken["dLER_teacher"]) < abs(remove["dLER_teacher"])

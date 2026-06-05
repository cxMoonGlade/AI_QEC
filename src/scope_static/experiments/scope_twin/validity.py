from __future__ import annotations

"""B5: counterfactual-validity-vs-probe-richness curve and negative controls.

The deliverable of the B feasibility step (ADR 0007): for each probe richness
``r``, calibrate the twin label-free on ``C_cal(r)`` and score how well its
*counterfactual* (``do()``) predictions match the controlled teacher's *true*
ones on a held-out eval circuit. The point the curve makes precise is the central
risk -- observational adequacy is not interventional validity: the twin can fit
the calibration joint at every ``r`` (``calib_kl`` ~ 0) yet give wrong knobs at
low ``r`` (large ``B_LER``) because the Z-basis ladder Pauli-shadows the coherent
mechanism; richer probes break the alias quotient and ``B_LER`` falls.

Negative controls:
  * shuffled-channel twin -- permute the calibrated per-location channels; must
    give wrong counterfactuals (a twin that fits aggregate stats but misassigns
    mechanisms to locations fails the knobs) universally;
  * moment-matched (Pauli-twirl) twin -- keep only the diagonal PTM; must
    underperform specifically on the coherent slice (the Pauli-shadowing control).
"""

import torch

from scope_static.experiments.scope_twin.calibration import RepCodeTwin, calibrate
from scope_static.experiments.scope_twin.contexts import (
    RepCodeContext,
    calibration_contexts,
    run_context,
)
from scope_static.experiments.scope_twin.intervention import (
    counterfactual_scores,
    do_remove,
    field_counterfactual_scores,
    logical_error_rate,
)
from scope_static.experiments.scope_twin.mechanisms import pauli_twirl_field


def calibrate_at_richness(
    teacher_field, richness: int, *, distance: int = 3, num_kraus: int = 3, steps: int = 300, seed: int = 0
) -> dict[str, object]:
    """Label-free calibration on the cumulative ladder ``C_cal(richness)``."""
    contexts = calibration_contexts(richness, distance=distance)
    return calibrate(
        teacher_field, contexts, distance=distance, num_kraus=num_kraus, steps=steps, seed=seed
    )


def _aggregate_scores(teacher_field, twin, eval_context, decoder, interventions):
    b_ler, b_obs = [], []
    for target_i, intervention in interventions:
        scores = counterfactual_scores(
            teacher_field, twin, eval_context, decoder,
            target_i=target_i, intervention=intervention,
        )
        b_ler.append(scores["B_LER"])
        b_obs.append(scores["B_obs"])
    return b_ler, b_obs


def validity_curve(
    teacher_field,
    *,
    eval_context: RepCodeContext,
    decoder,
    distance: int = 3,
    levels=(0, 1, 2, 3, 4),
    num_kraus: int = 3,
    steps: int = 300,
    seed: int = 0,
    interventions=None,
) -> dict[str, object]:
    """Compute ``B_LER(r)`` / ``B_obs(r)`` across probe-richness ``levels``.

    ``interventions`` is a list of ``(target_i, intervention_fn)``; the default is
    a Tier-0 ``do(E_i -> I)`` on every location. Each level reports the
    calibration KL (observational fit), the held-out base-LER error, and the
    max/mean counterfactual errors over the interventions.
    """
    if interventions is None:
        interventions = [(i, do_remove) for i in range(distance)]

    base_teacher_ler = logical_error_rate(
        run_context(eval_context, channel_field=teacher_field), decoder,
        logical_reference=eval_context.logical,
    )

    rows = []
    for richness in levels:
        result = calibrate_at_richness(
            teacher_field, richness, distance=distance, num_kraus=num_kraus, steps=steps, seed=seed
        )
        twin = result["twin"]
        base_twin_ler = logical_error_rate(
            run_context(eval_context, channel_field=twin.field()), decoder,
            logical_reference=eval_context.logical,
        )
        b_ler, b_obs = _aggregate_scores(teacher_field, twin, eval_context, decoder, interventions)
        rows.append(
            {
                "r": richness,
                "calib_kl": float(result["total_kl"]),
                "base_ler_error": abs(base_twin_ler - base_teacher_ler),
                "B_LER_max": max(b_ler),
                "B_LER_mean": sum(b_ler) / len(b_ler),
                "B_obs_max": max(b_obs),
                "twin": twin,
            }
        )

    return {"base_teacher_ler": base_teacher_ler, "curve": rows}


# --------------------------------------------------------------------------- #
# Negative controls                                                             #
# --------------------------------------------------------------------------- #
def shuffled_channel_field(twin: RepCodeTwin):
    """Cyclically permute the calibrated per-location channels (a saboteur twin).

    Reproduces the same aggregate channel multiset but misassigns each mechanism
    to the wrong location, so location-targeted knobs must be wrong.
    """
    channels = twin.channels
    permuted = channels[1:] + channels[:1]
    return lambda t, i: permuted[i].kraus()


def _max_b_ler(teacher_field, other_field, eval_context, decoder, interventions) -> float:
    return max(
        field_counterfactual_scores(
            teacher_field, other_field, eval_context, decoder,
            target_i=target_i, intervention=intervention,
        )["B_LER"]
        for target_i, intervention in interventions
    )


def negative_controls(
    teacher_field,
    twin: RepCodeTwin,
    *,
    eval_context: RepCodeContext,
    decoder,
    distance: int = 3,
    interventions=None,
) -> dict[str, float]:
    """Max ``B_LER`` of the two negative-control twins vs the calibrated twin.

    ``moment_matched`` is the teacher's Pauli twirl (the DEM-style stochastic
    shadow -- must fail on the coherent slice); ``shuffled`` permutes the twin's
    per-location channels (must fail location-targeted knobs). Both should be far
    larger than the exact-NLL twin's ``B_LER``.
    """
    if interventions is None:
        interventions = [(i, do_remove) for i in range(distance)]
    moment_matched = pauli_twirl_field(teacher_field, distance)
    shuffled = shuffled_channel_field(twin)
    return {
        "twin_B_LER": _max_b_ler(teacher_field, twin.field(), eval_context, decoder, interventions),
        "moment_matched_B_LER": _max_b_ler(teacher_field, moment_matched, eval_context, decoder, interventions),
        "shuffled_B_LER": _max_b_ler(teacher_field, shuffled, eval_context, decoder, interventions),
    }

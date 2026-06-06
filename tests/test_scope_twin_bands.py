"""D3 Tier 0 (ADR 0008): closed-form Laplace alias/uncertainty band.

The band ``(z/sqrt(N)) sqrt(g^T H^+ g)`` covers the controlled-teacher's true
knob, shrinks with probe richness (the alias quotient collapsing, as a closed
form), surfaces the D5a learnable-DOF deficiency as ``g``-weight in ``H``'s
near-null space, and couples to the finite-shot scale as ``1/sqrt(N)``.
"""

from __future__ import annotations

import math

import pytest

from scope_static.experiments.scope_twin.bands import tier0_alias_band
from scope_static.experiments.scope_twin.calibration import calibrate
from scope_static.experiments.scope_twin.contexts import (
    calibration_contexts,
    held_out_eval_context,
    run_context,
)
from scope_static.experiments.scope_twin.intervention import (
    build_frozen_decoder,
    do_remove,
    intervene_field,
    logical_error_rate,
)
from scope_static.experiments.scope_twin.mechanisms import coherent_overrotation_field

RATES = [0.02, 0.03, 0.02]
THETAS = [0.6, 0.7, 0.5]
TARGET = 1
SHOTS = 20_000


@pytest.fixture(scope="module")
def tier0():
    teacher = coherent_overrotation_field(RATES, THETAS)
    eval_ctx = held_out_eval_context()
    decoder = build_frozen_decoder(eval_ctx)

    base = logical_error_rate(run_context(eval_ctx, channel_field=teacher), decoder)
    removed = logical_error_rate(
        run_context(eval_ctx, channel_field=intervene_field(teacher, TARGET, do_remove)), decoder
    )
    true_knob = removed - base

    bands = {}
    for r in (0, 1):
        contexts = calibration_contexts(r)
        twin = calibrate(teacher, contexts, distance=3, num_kraus=2, steps=200, seed=0)["twin"]
        teacher_forwards = [run_context(c, channel_field=teacher) for c in contexts]
        bands[r] = tier0_alias_band(
            twin, contexts, teacher_forwards, eval_context=eval_ctx, decoder=decoder,
            target_i=TARGET, intervention=do_remove, shots=SHOTS, z=1.0,
        )
    return true_knob, bands


def test_band_covers_true_knob_at_both_richness(tier0) -> None:
    true_knob, bands = tier0
    for r in (0, 1):
        band = bands[r]
        assert abs(band["knob_value"] - true_knob) <= 2.0 * band["statistical_band"]


def test_band_and_alias_geometry_shrink_with_richness(tier0) -> None:
    _, bands = tier0
    assert bands[1]["statistical_band"] < bands[0]["statistical_band"] / 5
    assert bands[1]["inv_quad"] < bands[0]["inv_quad"] / 10  # g^T H^+ g, the alias geometry
    assert bands[1]["alias_weight"] < bands[0]["alias_weight"]


def test_band_is_the_closed_form_coupling(tier0) -> None:
    # statistical_band == (z/sqrt(N)) sqrt(g^T H^+ g) with z=1 -- the a<->b coupling
    # formula, so the finite-shot scale enters purely as 1/sqrt(N).
    _, bands = tier0
    band = bands[1]
    assert band["statistical_band"] == pytest.approx(math.sqrt(band["inv_quad"] / SHOTS), rel=1e-9)

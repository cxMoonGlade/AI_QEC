"""B2: the probe-richness ladder C_cal(r) and held-out eval.

Checks the ladder grows monotonically with distinct contexts, the eval context
is held out (disjoint from calibration), every context exact-forwards to a valid
joint distribution, the logical-prep / detector invariants hold per context
(noiseless |0_L> reads 0, |1_L> reads 1, neither detects), and the per-location
channel-field path B3 calibrates over is live and differentiable.
"""

from __future__ import annotations

import torch

from scope_static.experiments.scope_twin.contexts import (
    MAX_BUILT_RICHNESS,
    calibration_contexts,
    held_out_eval_context,
    run_context,
)
from scope_static.primitives.diff_circuit_sim import bit_flip


def test_calibration_ladder_grows_and_is_distinct() -> None:
    c0 = calibration_contexts(0)
    c1 = calibration_contexts(1)

    assert len(c0) == 1
    assert len(c1) == 6  # r=0 (1) + r=1 (5)

    # Monotone growth: every r=0 context survives into r=1.
    keys0 = {c.key for c in c0}
    keys1 = {c.key for c in c1}
    assert keys0 <= keys1

    # Distinct circuits, and the r=1 set spans rounds {1,2,3} x logical {0,1}.
    assert len(keys1) == len(c1)
    assert {c.rounds for c in c1} == {1, 2, 3}
    assert {c.logical for c in c1} == {0, 1}


def test_richness_beyond_built_is_guarded() -> None:
    try:
        calibration_contexts(MAX_BUILT_RICHNESS + 1)
    except NotImplementedError:
        return
    raise AssertionError("expected NotImplementedError beyond MAX_BUILT_RICHNESS")


def test_held_out_eval_is_disjoint_from_calibration() -> None:
    eval_ctx = held_out_eval_context()
    cal_keys = {c.key for c in calibration_contexts(MAX_BUILT_RICHNESS)}
    assert eval_ctx.key not in cal_keys


def test_every_context_exact_forwards_to_valid_distribution() -> None:
    contexts = calibration_contexts(1) + [held_out_eval_context()]
    channel = bit_flip(0.05)
    for ctx in contexts:
        result = run_context(ctx, data_channel=channel)
        assert abs(result.total_probability().item() - 1.0) < 1e-9
        assert (result.probs >= -1e-12).all()


def test_noiseless_logical_prep_and_detector_invariants() -> None:
    # With no noise, |0_L> reads observable 0 and |1_L> reads 1, and neither
    # produces detections -- the logical prep and basis-invariant syndrome wiring.
    for ctx in calibration_contexts(1):
        result = run_context(ctx)  # noiseless
        assert abs(result.total_probability().item() - 1.0) < 1e-9
        assert result.detector_marginals().abs().max().item() < 1e-12
        assert abs(result.observable_marginal().item() - float(ctx.logical)) < 1e-12


def test_per_location_channel_field_is_live_and_differentiable() -> None:
    # A per-location field: bit-flip only on data qubit 1, strength a leaf param.
    # Exercises the exact path B3 calibrates over (per-(t,i) channels) and that a
    # gradient flows from the joint distribution back to the mechanism parameter.
    p = torch.tensor(0.1, dtype=torch.float64, requires_grad=True)

    def field(t: int, i: int):
        if i == 1:
            return bit_flip(p)
        return None

    ctx = held_out_eval_context()
    result = run_context(ctx, channel_field=field)

    assert abs(result.total_probability().item() - 1.0) < 1e-9
    assert result.detector_marginals().sum().item() > 1e-6  # qubit-1 errors detected

    signal = result.detector_marginals().sum()
    signal.backward()
    assert torch.isfinite(p.grad)
    assert abs(p.grad.item()) > 1e-9

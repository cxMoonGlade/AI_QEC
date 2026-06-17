"""B5: counterfactual-validity-vs-richness curve and negative controls.

The scientific centerpiece of the B step: on a coherent over-rotation teacher
(RX(theta) + bit-flip), the exact-observation-NLL twin recovers the coherent
mechanism well enough that its do() knobs are trustworthy (small B_LER), while

  * a moment-matched (Pauli-twirl / DEM-style) twin Pauli-shadows the coherence
    and gives knobs that are orders of magnitude wrong (the central
    observational != interventional risk, realized), and
  * a shuffled-channel twin fits the AGGREGATE LER yet gets location-targeted
    knobs wrong (mechanisms misassigned to locations);

and richer probes reduce the residual counterfactual error (B_LER(r=0) >>
B_LER(r=1)) even though the observational fit (calib_kl) is ~0 at every level.
"""

from __future__ import annotations

import pytest
import torch

from scope_static.experiments.scope_twin.contexts import held_out_eval_context
from scope_static.experiments.scope_twin.intervention import build_frozen_decoder
from scope_static.experiments.scope_twin.mechanisms import (
    coherent_overrotation_field,
    coherent_overrotation_kraus,
    pauli_twirl_kraus,
)
from scope_static.experiments.scope_twin.validity import (
    calibrate_at_richness,
    negative_controls,
)
from scope_static.primitives.diff_cptp_channel import pauli_transfer_matrix

RATES = [0.02, 0.03, 0.02]
THETAS = [0.6, 0.7, 0.5]


def _off_diagonal(matrix: torch.Tensor) -> float:
    return (matrix - torch.diag(torch.diagonal(matrix))).abs().max().item()


@pytest.fixture(scope="module")
def b5_run():
    teacher = coherent_overrotation_field(RATES, THETAS)
    eval_ctx = held_out_eval_context()
    decoder = build_frozen_decoder(eval_ctx)

    result_r0 = calibrate_at_richness(teacher, 0, num_kraus=3, steps=200, seed=0)
    result_r1 = calibrate_at_richness(teacher, 1, num_kraus=3, steps=200, seed=0)

    controls_r0 = negative_controls(teacher, result_r0["twin"], eval_context=eval_ctx, decoder=decoder)
    controls = negative_controls(teacher, result_r1["twin"], eval_context=eval_ctx, decoder=decoder)

    return {
        "calib_kl_r0": result_r0["total_kl"],
        "calib_kl_r1": result_r1["total_kl"],
        "bler_r0": controls_r0["twin_B_LER"],
        "controls": controls,
    }


def test_pauli_twirl_discards_coherence() -> None:
    # The coherent channel has off-diagonal PTM (coherence); its twirl is a pure
    # Pauli channel (diagonal PTM) -- the moment-matched shadow.
    kraus = coherent_overrotation_kraus(0.02, 0.7)
    twirl = pauli_twirl_kraus(kraus)
    assert _off_diagonal(pauli_transfer_matrix(kraus)) > 1e-2
    assert _off_diagonal(pauli_transfer_matrix(twirl)) < 1e-9


def test_observational_fit_succeeds_at_every_richness(b5_run) -> None:
    # The twin reproduces the calibration joint at both levels (observational
    # adequacy is NOT the issue -- interventional validity is).
    assert b5_run["calib_kl_r0"] < 1e-6
    assert b5_run["calib_kl_r1"] < 1e-6


def test_richer_probes_reduce_counterfactual_error(b5_run) -> None:
    # B_LER falls sharply once multi-context exact-NLL data is available.
    assert b5_run["bler_r0"] > 10 * b5_run["controls"]["twin_B_LER"]


def test_exact_nll_beats_moment_matching_on_coherent_slice(b5_run) -> None:
    # The Pauli-shadowing control: moment matching gives knobs orders of magnitude
    # worse than the exact-NLL twin on the coherent mechanism.
    controls = b5_run["controls"]
    assert controls["moment_matched_B_LER"] > 1e-3  # the shadow really is wrong
    assert controls["twin_B_LER"] < controls["moment_matched_B_LER"] / 50


def test_exact_nll_beats_shuffled_location_assignment(b5_run) -> None:
    # The misassignment control: shuffling per-location channels wrecks the
    # location-targeted knob even though aggregate stats are preserved.
    controls = b5_run["controls"]
    assert controls["shuffled_B_LER"] > 1e-3
    assert controls["twin_B_LER"] < controls["shuffled_B_LER"] / 50

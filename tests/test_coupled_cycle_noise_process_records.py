"""Owner tests for emitted records from ``CoupledCycleNoiseProcess``.

These checks exercise the real GPU emitter and channel assembler.  The record
rate check uses only declared reset/readout probabilities and Bernoulli algebra;
it does not reuse the emitter's probability table.
"""

from __future__ import annotations

import math

import numpy as np
import torch

from conftest import requires_cuda
from error_coupling_simulator.certify import Regime
from error_coupling_simulator.noise_processes import CoupledCycleNoiseProcess
from error_coupling_simulator.source import default_source_coupling_config


def _regime() -> Regime:
    return Regime(R=2, n_stab=2)


def _assert_no_record_arrays(node) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            assert key not in {"det", "obs"}
            _assert_no_record_arrays(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            _assert_no_record_arrays(value)


@requires_cuda
def test_emit_returns_only_binary_record_payload():
    process = CoupledCycleNoiseProcess(2, shots_per_trajectory=8)
    shot_count = 32
    payload = process.emit(_regime(), m=0, N=shot_count, seed=101)

    assert set(payload) == {"det", "obs"}
    detector_bits = payload["det"]
    observable_bits = payload["obs"]
    assert isinstance(detector_bits, np.ndarray)
    assert isinstance(observable_bits, np.ndarray)
    assert detector_bits.dtype == np.uint8
    assert observable_bits.dtype == np.uint8
    assert detector_bits.shape == (shot_count, 4)
    assert observable_bits.shape == (shot_count,)
    assert set(np.unique(detector_bits)) <= {0, 1}
    assert set(np.unique(observable_bits)) <= {0, 1}

    truth = process.truth
    assert truth["last_emit"]["N"] == shot_count
    assert truth["last_emit"]["shots_per_trajectory"] == 8
    _assert_no_record_arrays(truth)


@requires_cuda
def test_emit_is_seed_reproducible_and_seed_sensitive():
    process = CoupledCycleNoiseProcess(2, shots_per_trajectory=256)
    first = process.emit(_regime(), m=0, N=256, seed=7)
    replay = process.emit(_regime(), m=0, N=256, seed=7)
    np.testing.assert_array_equal(first["det"], replay["det"])
    np.testing.assert_array_equal(first["obs"], replay["obs"])

    changed = process.emit(_regime(), m=0, N=256, seed=8)
    assert not (
        np.array_equal(first["det"], changed["det"])
        and np.array_equal(first["obs"], changed["obs"])
    )


@requires_cuda
def test_batched_emit_declares_clusters_and_preserves_off_source_marginals():
    batched = CoupledCycleNoiseProcess(
        2, shots_per_trajectory=64
    ).off_source()
    shot_count = 512
    batched_payload = batched.emit(
        _regime(), m=0, N=shot_count, seed=3
    )
    truth = batched.truth
    assert truth["shots_per_trajectory"] == 64
    assert truth["last_emit"]["shots_per_trajectory"] == 64
    assert truth["last_emit"]["n_trajectories"] == shot_count // 64

    unbatched = CoupledCycleNoiseProcess(2).off_source()
    unbatched_payload = unbatched.emit(
        _regime(), m=0, N=shot_count, seed=4
    )
    for column in range(batched_payload["det"].shape[1]):
        p_batched = float(batched_payload["det"][:, column].mean())
        p_unbatched = float(unbatched_payload["det"][:, column].mean())
        pooled = max((p_batched + p_unbatched) / 2.0, 1.0 / shot_count)
        standard_error = math.sqrt(
            2.0 * pooled * (1.0 - pooled) / shot_count
        )
        assert abs(p_batched - p_unbatched) <= 5.0 * standard_error + 1.0e-9


@requires_cuda
def test_reported_channels_are_cptp():
    rows = CoupledCycleNoiseProcess(2).channels()
    assert rows
    for row in rows:
        assert 0 <= row["round_index"] < 2
        kraus = row["kraus"]
        assert kraus.ndim == 3
        assert kraus.shape[-1] == kraus.shape[-2]
        dimension = kraus.shape[-1]
        identity = torch.eye(
            dimension, dtype=kraus.dtype, device=kraus.device
        )
        trace_preservation_residual = (
            torch.einsum("kij,kil->jl", kraus.conj(), kraus) - identity
        ).abs().max()
        assert float(trace_preservation_residual) <= 1.0e-10


@requires_cuda
def test_z_check_record_rates_match_closed_form():
    """The diagonal check chain is fixed by reset/readout Bernoulli algebra.

    With reset-flip probability ``p_reset`` and readout-flip probability
    ``p_readout``, one round reports one with

    ``p = p_reset + p_readout - 2 p_reset p_readout``.

    Independent round resets make the temporal detector rate ``2p(1-p)``;
    the terminal detector applies one more readout flip.  The logical
    observable is a direct final readout of a data site fixed in zero.
    """
    config = default_source_coupling_config()
    shot_count = 1 << 16
    process = CoupledCycleNoiseProcess(
        2, shots_per_trajectory=shot_count
    ).off_source()
    payload = process.emit(
        _regime(), m=0, N=shot_count, seed=11
    )

    p_reset = config.reset_flip_base_p
    p_readout = config.readout_flip_base_p
    one_round = p_reset + p_readout - 2.0 * p_reset * p_readout
    predictions = {
        "delta:z1:round1": 2.0 * one_round * (1.0 - one_round),
        "final:z1": (
            one_round * (1.0 - p_readout)
            + (1.0 - one_round) * p_readout
        ),
    }
    detector_names = process.truth["detector_names"]
    for name, predicted in predictions.items():
        measured = float(payload["det"][:, detector_names.index(name)].mean())
        standard_error = math.sqrt(
            predicted * (1.0 - predicted) / shot_count
        )
        assert abs(measured - predicted) <= 5.0 * standard_error + 1.0e-4

    observable_rate = float(payload["obs"].mean())
    observable_error = math.sqrt(
        p_readout * (1.0 - p_readout) / shot_count
    )
    assert abs(observable_rate - p_readout) <= 5.0 * observable_error + 1.0e-4

"""B1: exact multi-round repetition-code forward model.

Validates the trajectory-enumerated joint ``p(s, m)`` of
:mod:`scope_static.primitives.diff_rep_code`:

  * no noise  -> no detections, zero logical readout (the exact limit);
  * a deterministic data flip -> the exact syndrome its wiring must produce;
  * stochastic bit-flip noise -> detector / observable marginals matching a
    hand-built stim reference circuit (same qubits, CX order, noise placement,
    ``MR``/``M`` order, ``rec`` offsets) -- the pure-Pauli cross-check;
  * a coherent (non-Clifford) error and a generic non-Pauli CPTP channel ->
    a valid distribution with detections and a differentiable knob, on the same
    exact substrate stim cannot represent.
"""

from __future__ import annotations

import torch

from scope_static.primitives.diff_circuit_sim import bit_flip, rx
from scope_static.primitives.diff_cptp_channel import (
    StinespringChannel,
    pauli_transfer_matrix,
)
from scope_static.primitives.diff_rep_code import (
    rep_code_qubits,
    simulate_rep_code_memory,
)


# --------------------------------------------------------------------------- #
# stim reference (pure-Pauli slice) -- same wiring as the density-matrix sim   #
# --------------------------------------------------------------------------- #
def _build_stim_rep_code(distance: int, rounds: int, p_data: float):
    import stim

    d = int(distance)
    nchecks = d - 1
    data, anc, _ = rep_code_qubits(d)
    circuit = stim.Circuit()

    for t in range(int(rounds)):
        if p_data > 0:
            circuit.append("X_ERROR", data, p_data)
        for j in range(nchecks):
            circuit.append("CX", [data[j], anc[j]])
            circuit.append("CX", [data[j + 1], anc[j]])
        circuit.append("MR", anc)  # measure + reset, order anc[0..d-2]
        for j in range(nchecks):
            if t == 0:
                circuit.append("DETECTOR", [stim.target_rec(-nchecks + j)])
            else:
                circuit.append(
                    "DETECTOR",
                    [stim.target_rec(-nchecks + j), stim.target_rec(-2 * nchecks + j)],
                )

    circuit.append("M", data)  # order data[0..d-1]
    for j in range(nchecks):
        circuit.append(
            "DETECTOR",
            [
                stim.target_rec(-d + j),
                stim.target_rec(-d + j + 1),
                stim.target_rec(-d - nchecks + j),
            ],
        )
    circuit.append("OBSERVABLE_INCLUDE", [stim.target_rec(-d)], 0)
    return circuit


def _stim_marginals(circuit, *, shots: int, seed: int):
    sampler = circuit.compile_detector_sampler(seed=seed)
    sample = torch.as_tensor(
        sampler.sample(int(shots), append_observables=True), dtype=torch.float64
    )
    num_obs = circuit.num_observables
    det = sample[:, : sample.shape[1] - num_obs]
    obs = sample[:, sample.shape[1] - num_obs :]
    return det.mean(0), obs.mean(0)


# --------------------------------------------------------------------------- #
# Tests                                                                        #
# --------------------------------------------------------------------------- #
def test_noiseless_rep_code_has_no_detections_and_zero_logical() -> None:
    result = simulate_rep_code_memory(distance=3, rounds=2)

    assert abs(result.total_probability().item() - 1.0) < 1e-9
    # Exactly one trajectory carries all the weight: the all-zeros record.
    assert result.probs.max().item() > 1.0 - 1e-9
    assert torch.allclose(
        result.detector_marginals(),
        torch.zeros(result.num_detectors, dtype=torch.float64),
        atol=1e-12,
    )
    assert result.observable_marginal().item() < 1e-12
    assert abs(result.no_detection_probability().item() - 1.0) < 1e-12


def test_deterministic_data_flip_lights_expected_detectors() -> None:
    # X on the middle data qubit (data 1) is shared by both checks, so both
    # round-0 absolute detectors fire and nothing else; the observable (data 0)
    # is untouched.
    mid = simulate_rep_code_memory(distance=3, rounds=2, initial_flips=[1])
    assert abs(mid.total_probability().item() - 1.0) < 1e-9
    leaf = mid.probs.argmax()
    assert mid.probs[leaf].item() > 1.0 - 1e-9
    assert mid.detector_events[leaf].tolist() == [1, 1, 0, 0, 0, 0]
    assert mid.observable[leaf].item() == 0

    # X on the boundary data qubit (data 0) lights only its single check and
    # flips the logical observable -- pins the observable wiring.
    edge = simulate_rep_code_memory(distance=3, rounds=2, initial_flips=[0])
    leaf_e = edge.probs.argmax()
    assert edge.detector_events[leaf_e].tolist() == [1, 0, 0, 0, 0, 0]
    assert edge.observable[leaf_e].item() == 1


def test_pauli_bitflip_marginals_match_stim_reference() -> None:
    distance, rounds, p = 3, 3, 0.08
    result = simulate_rep_code_memory(distance, rounds, data_channel=bit_flip(p))

    assert abs(result.total_probability().item() - 1.0) < 1e-9

    circuit = _build_stim_rep_code(distance, rounds, p)
    stim_det, stim_obs = _stim_marginals(circuit, shots=200_000, seed=12345)

    assert result.num_detectors == stim_det.shape[0]
    assert torch.allclose(result.detector_marginals(), stim_det, atol=0.01)
    assert abs(result.observable_marginal().item() - stim_obs.item()) < 0.01


def test_coherent_error_gives_valid_joint_and_differentiable_knob() -> None:
    # A coherent RX(theta) storage error each round: non-Clifford, beyond any
    # stochastic Pauli model, evaluated exactly through the multi-round
    # mid-circuit-measurement enumeration.
    theta = torch.tensor(0.3, dtype=torch.float64, requires_grad=True)
    channel = rx(theta).unsqueeze(0)  # single-Kraus unitary channel
    result = simulate_rep_code_memory(distance=3, rounds=2, data_channel=channel)

    assert abs(result.total_probability().item() - 1.0) < 1e-9
    assert result.detector_marginals().sum().item() > 1e-6  # errors are detected

    # The knob: d P(detection) / d theta exists and is nonzero -- the gradient
    # that B4's priority-list / strength knobs ride on.
    signal = result.detector_marginals().sum()
    signal.backward()
    assert torch.isfinite(theta.grad)
    assert abs(theta.grad.item()) > 1e-9


def test_generic_non_pauli_channel_stays_a_valid_distribution() -> None:
    # A generic CPTP channel (random Stinespring) acts nontrivially on |0> and
    # is non-Pauli (off-diagonal PTM); the enumerated forward must remain an
    # exact probability distribution (CPTP closure through measurement).
    channel = StinespringChannel.random(dim=2, num_kraus=3, seed=7, scale=0.4)
    kraus = channel.kraus()

    ptm = pauli_transfer_matrix(kraus)
    off_diagonal = (ptm - torch.diag(torch.diagonal(ptm))).abs().max()
    assert off_diagonal.item() > 1e-3  # certifies non-Pauli action

    result = simulate_rep_code_memory(distance=3, rounds=2, data_channel=kraus.detach())
    assert abs(result.total_probability().item() - 1.0) < 1e-9
    assert (result.probs >= -1e-12).all()
    assert result.detector_marginals().sum().item() > 1e-6

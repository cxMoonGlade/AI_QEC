"""L2 minimal forward-model test: an exact, differentiable circuit -> detection
event probability, with a coherent (non-Clifford) error and a non-Pauli channel.

Demonstrates the pieces the digital twin's device forward model needs:
  * compose local non-Clifford gates + local CPTP channels on an n-qubit
    register exactly;
  * read out an exact detection-event probability;
  * differentiate it w.r.t. a mechanism parameter -- the gradient that powers
    the L4 priority-list / bottleneck knobs.
"""

from __future__ import annotations

import torch

from scope_static.primitives.diff_circuit_sim import (
    amplitude_damping,
    apply_channel_local,
    apply_unitary,
    cx,
    qubit_marginal_one,
    rx,
    zero_state,
)


def test_coherent_error_detection_matches_analytic_and_is_differentiable() -> None:
    # |00>; coherent RX(eps) error on data qubit 0; parity check CX onto ancilla
    # qubit 1; measure the ancilla. Analytic P(detect) = sin^2(eps/2).
    n = 2
    eps = torch.tensor(0.37, dtype=torch.float64, requires_grad=True)
    rho = zero_state(n)
    rho = apply_unitary(rho, rx(eps), [0], n)
    rho = apply_unitary(rho, cx(), [0, 1], n)
    p_detect = qubit_marginal_one(rho, 1, n)

    expected = torch.sin(eps / 2) ** 2
    assert abs(p_detect.detach().item() - expected.detach().item()) < 1e-10

    # Exact differentiable sensitivity: d/d eps sin^2(eps/2) = 0.5 sin(eps).
    p_detect.backward()
    assert abs(eps.grad.item() - 0.5 * torch.sin(eps).detach().item()) < 1e-7


def test_non_pauli_channel_changes_detection_and_is_differentiable() -> None:
    # Same circuit with amplitude damping (non-Pauli, non-unital) on the data
    # qubit before the parity check. Damping suppresses the excitation, so the
    # detection probability drops, and it is differentiable w.r.t. gamma.
    n = 2
    angle = torch.tensor(0.8, dtype=torch.float64)

    def detect(gamma_value: float, with_damping: bool):
        gamma = torch.tensor(gamma_value, dtype=torch.float64, requires_grad=True)
        rho = zero_state(n)
        rho = apply_unitary(rho, rx(angle), [0], n)
        if with_damping:
            rho = apply_channel_local(rho, amplitude_damping(gamma), [0], n)
        rho = apply_unitary(rho, cx(), [0, 1], n)
        trace = torch.trace(rho).real
        return qubit_marginal_one(rho, 1, n), gamma, trace

    p_no_damp, _, _ = detect(0.0, with_damping=False)
    p_damp, gamma, trace = detect(0.15, with_damping=True)

    # Trace preserved through the non-Pauli channel (CPTP).
    assert abs(trace.detach().item() - 1.0) < 1e-10
    # Amplitude damping reduces the detection probability.
    assert p_damp.detach().item() < p_no_damp.detach().item()
    # Differentiable sensitivity (a mini "knob"): d P(detect) / d gamma exists.
    p_damp.backward()
    assert torch.isfinite(gamma.grad)
    assert abs(float(gamma.grad)) > 1e-9

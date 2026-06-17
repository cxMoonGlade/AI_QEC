"""Kernel test: differentiable CPTP-by-construction recovery of a known
non-Pauli, non-Clifford channel.

Proves three things the learner-side CPTP upgrade needs:
  1. the Stinespring parameterization is trace-preserving by construction;
  2. it can represent a genuinely coherent (non-Pauli, non-Clifford) channel;
  3. that channel is recoverable to high precision by differentiable
     optimization on an informationally-complete input set.
"""

from __future__ import annotations

import numpy as np
import torch

from scope_static.primitives.channels import amplitude_damping_kraus, rx_unitary
from scope_static.primitives.diff_cptp_channel import (
    CDTYPE,
    StinespringChannel,
    apply_kraus,
    pauli_transfer_matrix,
    recover_channel,
    tp_residual,
)


def _target_channel() -> torch.Tensor:
    """Amplitude damping (gamma=0.12) composed after a coherent RX(0.3).

    RX(0.3) is non-Clifford (0.3 is not a multiple of pi/2); amplitude damping
    is non-unital and non-Pauli. The composition Kraus set is {A_e @ U}.
    """
    u = np.asarray(rx_unitary(0.3), dtype=np.complex128)
    damping = [np.asarray(a, dtype=np.complex128) for a in amplitude_damping_kraus(0.12)]
    composed = np.stack([a @ u for a in damping])
    return torch.from_numpy(composed).to(CDTYPE)


def test_random_stinespring_channel_is_trace_preserving() -> None:
    # CPTP-by-construction: any random generator yields a TP map.
    for seed in range(5):
        channel = StinespringChannel.random(dim=2, num_kraus=4, seed=seed)
        with torch.no_grad():
            assert float(tp_residual(channel.kraus())) < 1e-10


def test_target_is_cptp_and_non_pauli() -> None:
    target = _target_channel()
    # Composition is genuinely trace preserving (validates the Kraus assembly).
    assert float(tp_residual(target)) < 1e-10
    # A stochastic Pauli channel has a diagonal PTM; coherent RX leaves a
    # nonzero Y<->Z rotation block, certifying non-Pauli / non-Clifford action.
    ptm = pauli_transfer_matrix(target)
    off_diagonal = ptm - torch.diag(torch.diagonal(ptm))
    assert float(off_diagonal.abs().max()) > 0.1


def test_recovers_known_non_pauli_channel() -> None:
    torch.manual_seed(0)
    target = _target_channel()
    result = recover_channel(target, steps=300, seed=0)

    assert result["action_loss"] < 1e-8
    assert result["choi_distance"] < 1e-5
    assert result["tp_residual"] < 1e-10

    # The recovered channel reproduces the target action on a fresh input.
    rho = torch.tensor([[0.5, 0.5], [0.5, 0.5]], dtype=CDTYPE)  # |+><+|
    recovered_out = apply_kraus(rho, result["recovered_kraus"])
    target_out = apply_kraus(rho, target)
    assert float((recovered_out - target_out).abs().max()) < 1e-4

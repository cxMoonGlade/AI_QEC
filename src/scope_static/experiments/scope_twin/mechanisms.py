from __future__ import annotations

"""Teacher mechanisms and their Pauli twirls for the B5 study.

The B5 teacher is a coherent over-rotation plus a stochastic bit-flip per
location -- ``E_i = BitFlip(p_i) . RX(theta_i)`` -- the canonical control error
whose coherent part a Z-basis ladder Pauli-shadows. The Pauli twirl of a channel
(its diagonal Pauli-transfer matrix, rebuilt as a Pauli channel) is the
observationally-aliased stochastic counterpart used as a reference and as the
moment-matched negative control.
"""

import torch

from scope_static.primitives.diff_circuit_sim import bit_flip, rx
from scope_static.primitives.diff_cptp_channel import (
    pauli_transfer_matrix,
    single_qubit_paulis,
)


def coherent_overrotation_kraus(p: float, theta: float) -> torch.Tensor:
    """``BitFlip(p) . RX(theta)`` as a ``(2, 2, 2)`` Kraus stack.

    Kraus of the composition: ``{sqrt(1-p) RX, sqrt(p) X RX}``.
    """
    u = rx(torch.tensor(float(theta), dtype=torch.float64))
    flip = bit_flip(p)
    return torch.stack([flip[0] @ u, flip[1] @ u])


def coherent_overrotation_field(rates, thetas):
    """Per-location coherent-over-rotation teacher field ``(t, i) -> Kraus``."""
    kraus = [coherent_overrotation_kraus(rates[i], thetas[i]) for i in range(len(rates))]
    return lambda t, i: kraus[i]


def pauli_twirl_kraus(kraus: torch.Tensor) -> torch.Tensor:
    """The Pauli channel with the same diagonal PTM as ``kraus`` (its twirl).

    Coherence (off-diagonal PTM) is discarded, leaving the stochastic
    Pauli-shadow that a Z-basis ladder cannot distinguish from the original.
    """
    ptm = pauli_transfer_matrix(kraus)
    r_xx, r_yy, r_zz = float(ptm[1, 1]), float(ptm[2, 2]), float(ptm[3, 3])
    probs = [
        (1.0 + r_xx + r_yy + r_zz) / 4.0,
        (1.0 + r_xx - r_yy - r_zz) / 4.0,
        (1.0 - r_xx + r_yy - r_zz) / 4.0,
        (1.0 - r_xx - r_yy + r_zz) / 4.0,
    ]
    paulis = single_qubit_paulis()
    return torch.stack([(max(p, 0.0) ** 0.5) * paulis[k] for k, p in enumerate(probs)])


def pauli_twirl_field(field, n_locations: int):
    """Pauli-twirl every location of a teacher ``field`` (the aliased reference)."""
    twirled = [pauli_twirl_kraus(field(0, i)) for i in range(n_locations)]
    return lambda t, i: twirled[i]

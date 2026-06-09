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

from qec_twin.forward.exact.circuit_sim import amplitude_damping, bit_flip, rx
from qec_twin.forward.cptp_channel import (
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


def amplitude_damped_rotation_kraus(gamma: float, theta: float) -> torch.Tensor:
    """``AmplitudeDamp(gamma) . RX(theta)`` as a ``(2, 2, 2)`` Kraus stack.

    A coherent over-rotation followed by T1 relaxation -- the dominant
    superconducting-hardware pair (control error + amplitude damping). Non-unital,
    so a strictly richer *matched* mechanism than the Pauli-twirlable
    ``coherent_overrotation``; the ``RX`` populates ``|1>`` so the damping is
    visible already on the ``|0_L>`` ground state. Kraus of the composition:
    ``{A0 RX, A1 RX}`` (still 2 Kraus -> inside the ``num_kraus=2`` learner class).
    """
    u = rx(torch.tensor(float(theta), dtype=torch.float64))
    a = amplitude_damping(gamma)
    return torch.stack([a[0] @ u, a[1] @ u])


def mixed_mechanism_field(specs):
    """Heterogeneous per-location *matched* teacher -- the H0 richer baseline.

    ``specs[i]`` selects data-location ``i``'s mechanism; each is <=2-Kraus so the
    ``num_kraus=2`` learner class contains it (matched, no misspecification):

      ``("coherent", p, theta)``  -> ``BitFlip(p) . RX(theta)``      (Pauli + coherent)
      ``("damped", gamma, theta)`` -> ``AmpDamp(gamma) . RX(theta)``  (T1 + coherent, non-unital)
      ``("pure_damp", gamma)``    -> ``AmpDamp(gamma)``              (pure non-unital, NO Pauli twirl)
      ``("pauli", p)``            -> ``BitFlip(p)``                  (pure stochastic Pauli)

    ``pure_damp`` is the clean non-Pauli isolate (a unital/Pauli class provably cannot
    represent it); it is invisible on ``|0_L>`` (the AmpDamp fixed point) so its decision
    functional must use a ``|1_L>`` / superposition eval context.

    Spans the *visible* single-qubit mechanism taxonomy of the coherent-error /
    Lindbladian-learning frontier (coherent Hamiltonian + dissipative Kossakowski,
    the GKSL ``(h, a)`` split). Z-type mechanisms (phase flip / dephasing) are
    omitted: on this bit-flip rep code they are blind-sector and inconsequential.
    Returns the field callable ``(t, i) -> Kraus``.
    """
    kraus = []
    for spec in specs:
        kind = spec[0]
        if kind == "coherent":
            kraus.append(coherent_overrotation_kraus(spec[1], spec[2]))
        elif kind == "damped":
            kraus.append(amplitude_damped_rotation_kraus(spec[1], spec[2]))
        elif kind == "pure_damp":
            kraus.append(amplitude_damping(spec[1]))
        elif kind == "pauli":
            kraus.append(bit_flip(spec[1]))
        else:
            raise ValueError(f"unknown mechanism kind {kind!r} (coherent|damped|pure_damp|pauli)")
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

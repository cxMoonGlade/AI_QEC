from __future__ import annotations

"""Specified mechanism fields and their Pauli-twirled controls.

The primitives include coherent over-rotation plus stochastic bit flip,
amplitude damping, coherent ZZ coupling, and correlated dephasing. The Pauli
twirl of a channel is built from its diagonal Pauli-transfer matrix and serves
as a controlled stochastic reference. This module constructs channels and
fields; it does not fit them from records or choose between model classes.
"""

import torch

from ..carrier.exact.circuit_sim import amplitude_damping, bit_flip, rx
from ..carrier.cptp_channel import (
    CDTYPE,
    RDTYPE,
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
    """Per-location coherent-over-rotation field ``(t, i) -> Kraus``."""
    kraus = [coherent_overrotation_kraus(rates[i], thetas[i]) for i in range(len(rates))]
    return lambda t, i: kraus[i]


def amplitude_damped_rotation_kraus(gamma: float, theta: float) -> torch.Tensor:
    """``AmplitudeDamp(gamma) . RX(theta)`` as a ``(2, 2, 2)`` Kraus stack.

    A coherent over-rotation followed by T1 relaxation -- the dominant
    superconducting-hardware pair (control error + amplitude damping). Non-unital,
    so a strictly richer *matched* mechanism than the Pauli-twirlable
    ``coherent_overrotation``; the ``RX`` populates ``|1>`` so the damping is
    visible already on the ``|0_L>`` ground state. Kraus of the composition:
    ``{A0 RX, A1 RX}`` (a rank-2 channel).
    """
    u = rx(torch.tensor(float(theta), dtype=torch.float64))
    a = amplitude_damping(gamma)
    return torch.stack([a[0] @ u, a[1] @ u])


def mixed_mechanism_field(specs):
    """Heterogeneous per-location specified-mechanism field.

    ``specs[i]`` selects data-location ``i``'s mechanism; each has Kraus rank at
    most two:

      ``("coherent", p, theta)``  -> ``BitFlip(p) . RX(theta)``      (Pauli + coherent)
      ``("damped", gamma, theta)`` -> ``AmpDamp(gamma) . RX(theta)``  (T1 + coherent, non-unital)
      ``("pure_damp", gamma)``    -> ``AmpDamp(gamma)``              (pure non-unital, NO Pauli twirl)
      ``("pauli", p)``            -> ``BitFlip(p)``                  (pure stochastic Pauli)

    ``pure_damp`` is the clean non-Pauli isolate (a unital/Pauli class provably cannot
    represent it); it is invisible on ``|0_L>`` (the AmpDamp fixed point) so its decision
    functional must use a ``|1_L>`` / superposition eval context.

    The set spans coherent Hamiltonian and dissipative single-qubit examples.
    Z-type mechanisms are omitted because the original bit-flip repetition-code
    fixture used by this field is insensitive to them.
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


def zz_coupling_kraus(phi) -> torch.Tensor:
    """``exp(-i phi Z(x)Z)`` as a ``(1, 4, 4)`` Kraus stack.

    ``diag(e^{-i phi}, e^{i phi}, e^{i phi}, e^{-i phi})`` -- the frontier-standard
    residual-ZZ crosstalk unitary on a data pair. Accepts a float or a real leaf
    tensor so differentiable carrier/certification calculations remain possible.
    """
    p = torch.as_tensor(phi, dtype=RDTYPE)
    phase = torch.stack([-p, p, p, -p]).to(CDTYPE)
    return torch.diag_embed(torch.exp(1j * phase)).unsqueeze(0)


def correlated_dephasing_kraus(phi) -> torch.Tensor:
    """Correlated dephasing ``{cos(phi) I_4, sin(phi) Z(x)Z}`` -- a ``(2, 4, 4)`` stack.

    The exact two-qubit Pauli twirl of ``zz_coupling_kraus(phi)`` (rate
    ``sin^2(phi)``) -- a correlated stochastic crosstalk control.
    """
    p = torch.as_tensor(float(phi), dtype=RDTYPE)
    eye = torch.eye(4, dtype=CDTYPE)
    zz = torch.diag(torch.tensor([1.0, -1.0, -1.0, 1.0], dtype=CDTYPE))
    return torch.stack([torch.cos(p).to(CDTYPE) * eye, torch.sin(p).to(CDTYPE) * zz])


def coupled_mixed_teacher(specs, phi, pair=(0, 1)):
    """Mixed local field plus coherent ZZ crosstalk on ``pair``.

    Returns ``(field, edge_field)`` with ``field = mixed_mechanism_field(specs)``
    unchanged and ``edge_field`` the ``(t, (i, j)) -> Kraus | None`` callable
    yielding ``exp(-i phi Z(x)Z)`` on the declared pair. Both are evaluator-side
    process truth and must not enter emitted record payloads.
    """
    field = mixed_mechanism_field(specs)
    coupling = zz_coupling_kraus(phi)
    target = tuple(pair)
    edge_field = lambda t, e: coupling if tuple(e) == target else None  # noqa: E731
    return field, edge_field


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
    """Pauli-twirl every location of a mechanism ``field``."""
    twirled = [pauli_twirl_kraus(field(0, i)) for i in range(n_locations)]
    return lambda t, i: twirled[i]


# Neutral public spelling. The historical name remains the defining symbol because
# downstream registries pin its qualname; both names intentionally reference the same object.
coupled_mixed_noise_fields = coupled_mixed_teacher

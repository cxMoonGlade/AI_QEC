"""Simulator-owned channel and two-body noise-mechanism regression tests.

These tests exercise the declared Kraus/channel objects directly.  They do not
fit parameters, compare learner model classes, construct probe ladders, or make
uncertainty-band claims.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from error_coupling_simulator.carrier.channels import amplitude_damping_kraus, rx_unitary
from error_coupling_simulator.carrier.cptp_channel import (
    CDTYPE,
    StinespringChannel,
    apply_kraus,
    choi_matrix,
    pauli_transfer_matrix,
    tp_residual,
)
from error_coupling_simulator.mechanisms.teachers import (
    amplitude_damped_rotation_kraus,
    coherent_overrotation_field,
    coherent_overrotation_kraus,
    correlated_dephasing_kraus,
    coupled_mixed_noise_fields,
    mixed_mechanism_field,
    pauli_twirl_field,
    pauli_twirl_kraus,
    zz_coupling_kraus,
)


def _assert_tp(kraus: torch.Tensor, *, atol: float = 1e-10) -> None:
    assert float(tp_residual(kraus).detach()) <= atol


def _non_pauli_reference() -> torch.Tensor:
    """Amplitude damping after a non-Clifford RX rotation."""
    unitary = np.asarray(rx_unitary(0.3), dtype=np.complex128)
    damping = [np.asarray(k, dtype=np.complex128) for k in amplitude_damping_kraus(0.12)]
    return torch.from_numpy(np.stack([k @ unitary for k in damping])).to(CDTYPE)


def test_stinespring_channel_is_cptp_by_construction() -> None:
    for seed in range(5):
        channel = StinespringChannel.random(dim=2, num_kraus=4, seed=seed)
        _assert_tp(channel.kraus())


def test_non_pauli_reference_is_cptp_and_coherent() -> None:
    kraus = _non_pauli_reference()
    _assert_tp(kraus)
    ptm = pauli_transfer_matrix(kraus)
    off_diagonal = ptm - torch.diag(torch.diagonal(ptm))
    assert float(off_diagonal.abs().max()) > 0.1


def test_single_qubit_mechanism_factories_are_cptp_and_route_by_location() -> None:
    coherent = coherent_overrotation_kraus(0.03, 0.6)
    damped = amplitude_damped_rotation_kraus(0.05, 0.5)
    _assert_tp(coherent)
    _assert_tp(damped)

    field = coherent_overrotation_field([0.03, 0.04], [0.6, 0.7])
    assert torch.equal(field(0, 0), coherent_overrotation_kraus(0.03, 0.6))
    assert torch.equal(field(9, 1), coherent_overrotation_kraus(0.04, 0.7))


def test_mixed_mechanism_field_covers_declared_channel_families() -> None:
    specs = [
        ("coherent", 0.03, 0.6),
        ("damped", 0.05, 0.5),
        ("pure_damp", 0.04),
        ("pauli", 0.02),
    ]
    field = mixed_mechanism_field(specs)
    for index in range(len(specs)):
        _assert_tp(field(0, index))

    maximally_mixed = 0.5 * torch.eye(2, dtype=CDTYPE)
    damped_output = apply_kraus(maximally_mixed, field(0, 2))
    assert float((damped_output - maximally_mixed).abs().max()) > 1e-3

    with pytest.raises(ValueError, match="unknown mechanism kind"):
        mixed_mechanism_field([("not-a-mechanism", 0.1)])


def test_zz_coupling_is_the_declared_two_body_unitary_and_differentiable() -> None:
    phi = torch.tensor(0.2, dtype=torch.float64, requires_grad=True)
    kraus = zz_coupling_kraus(phi)
    expected = torch.diag(
        torch.exp(
            1j
            * torch.tensor([-0.2, 0.2, 0.2, -0.2], dtype=torch.float64).to(CDTYPE)
        )
    )
    assert kraus.shape == (1, 4, 4)
    assert torch.allclose(kraus[0], expected, atol=1e-12, rtol=0.0)
    _assert_tp(kraus)

    kraus[0, 0, 0].imag.backward()
    assert phi.grad is not None and torch.isfinite(phi.grad)
    assert abs(float(phi.grad)) > 1e-3


def test_correlated_dephasing_is_cptp_and_even_as_a_channel() -> None:
    plus = correlated_dephasing_kraus(0.2)
    minus = correlated_dephasing_kraus(-0.2)
    _assert_tp(plus)
    _assert_tp(minus)
    assert torch.allclose(choi_matrix(plus), choi_matrix(minus), atol=1e-12, rtol=0.0)


def test_two_body_edge_factory_routes_only_the_declared_pair() -> None:
    specs = [("pauli", 0.02), ("pure_damp", 0.03)]
    local_field, edge_field = coupled_mixed_noise_fields(specs, 0.1, pair=(0, 1))
    _assert_tp(local_field(0, 0))
    _assert_tp(local_field(0, 1))
    expected = zz_coupling_kraus(0.1)
    assert torch.equal(edge_field(0, (0, 1)), expected)
    assert edge_field(0, (1, 0)) is None
    assert edge_field(0, (1, 2)) is None


def test_pauli_twirl_preserves_ptm_diagonal_and_removes_coherent_blocks() -> None:
    original = coherent_overrotation_kraus(0.03, 0.6)
    twirled = pauli_twirl_kraus(original)
    _assert_tp(twirled)

    original_ptm = pauli_transfer_matrix(original)
    twirled_ptm = pauli_transfer_matrix(twirled)
    assert torch.allclose(
        torch.diagonal(twirled_ptm), torch.diagonal(original_ptm), atol=1e-12, rtol=0.0
    )
    twirled_off_diagonal = twirled_ptm - torch.diag(torch.diagonal(twirled_ptm))
    assert float(twirled_off_diagonal.abs().max()) <= 1e-12

    field = coherent_overrotation_field([0.03, 0.04], [0.6, 0.7])
    twirled_field = pauli_twirl_field(field, 2)
    assert torch.equal(twirled_field(0, 0), pauli_twirl_kraus(field(0, 0)))
    assert torch.equal(twirled_field(5, 1), pauli_twirl_kraus(field(0, 1)))

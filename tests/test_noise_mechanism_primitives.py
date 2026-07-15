"""CPTP-channel and measurement regression tests for current carrier utilities."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from error_coupling_simulator.carrier.cptp_channel import (
    CDTYPE,
    StinespringChannel,
    measurement_probabilities_z,
    pauli_transfer_matrix,
    tp_residual,
)


def _assert_tp(kraus: torch.Tensor, *, atol: float = 1e-10) -> None:
    assert float(tp_residual(kraus).detach()) <= atol


def _non_pauli_reference() -> torch.Tensor:
    """Hand-typed amplitude damping after a non-Clifford X rotation."""

    angle = 0.3
    gamma = 0.12
    cosine = np.cos(angle / 2.0)
    sine = np.sin(angle / 2.0)
    unitary = np.array(
        [[cosine, -1j * sine], [-1j * sine, cosine]],
        dtype=np.complex128,
    )
    damping = [
        np.array(
            [[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]],
            dtype=np.complex128,
        ),
        np.array(
            [[0.0, np.sqrt(gamma)], [0.0, 0.0]],
            dtype=np.complex128,
        ),
    ]
    return torch.from_numpy(np.stack([kraus @ unitary for kraus in damping])).to(CDTYPE)


def test_stinespring_channel_is_cptp_by_construction() -> None:
    for seed in range(5):
        channel = StinespringChannel.random(dim=2, num_kraus=4, seed=seed)
        _assert_tp(channel.kraus())


def test_non_pauli_reference_is_cptp_and_has_off_diagonal_pauli_structure() -> None:
    kraus = _non_pauli_reference()
    _assert_tp(kraus)
    ptm = pauli_transfer_matrix(kraus)
    off_diagonal = ptm - torch.diag(torch.diagonal(ptm))
    assert float(off_diagonal.abs().max()) > 0.1


def test_measurement_probabilities_z_preserves_exact_structural_zero() -> None:
    rho = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=CDTYPE)

    probabilities = measurement_probabilities_z(rho)

    assert torch.equal(probabilities, torch.tensor([1.0, 0.0], dtype=torch.float64))
    assert probabilities[1].item() == 0.0


@pytest.mark.parametrize("dtype", [torch.float64, CDTYPE], ids=["real", "complex"])
def test_measurement_probabilities_z_normalizes_valid_density_matrix(
    dtype: torch.dtype,
) -> None:
    rho = torch.tensor([[0.7, 0.1], [0.1, 0.3]], dtype=dtype)

    probabilities = measurement_probabilities_z(rho)

    assert torch.allclose(
        probabilities,
        torch.tensor([0.7, 0.3], dtype=torch.float64),
        atol=1e-15,
        rtol=0.0,
    )
    assert probabilities.sum().item() == pytest.approx(1.0, abs=1e-15)


@pytest.mark.parametrize(
    "rho",
    [
        torch.zeros((2, 2), dtype=CDTYPE),
        torch.diag(torch.tensor([1.1, -0.1], dtype=CDTYPE)),
        torch.tensor([[0.5, 0.2], [0.0, 0.5]], dtype=CDTYPE),
        torch.tensor([[1.0, 0.0], [0.0, float("nan")]], dtype=CDTYPE),
        torch.tensor([[1.0, 0.0], [0.0, float("inf")]], dtype=CDTYPE),
    ],
    ids=["zero-trace", "negative", "non-hermitian", "nan", "inf"],
)
def test_measurement_probabilities_z_rejects_out_of_domain_density_matrices(
    rho: torch.Tensor,
) -> None:
    with pytest.raises(ValueError):
        measurement_probabilities_z(rho)


def test_measurement_probabilities_z_rejects_non_square_input() -> None:
    with pytest.raises(ValueError, match="square"):
        measurement_probabilities_z(torch.ones((2, 3), dtype=CDTYPE))


def test_measurement_probabilities_z_only_clips_roundoff_negative_diagonal() -> None:
    rho = torch.diag(torch.tensor([1.0, -5.0e-13], dtype=CDTYPE))

    probabilities = measurement_probabilities_z(rho)

    assert torch.equal(probabilities, torch.tensor([1.0, 0.0], dtype=torch.float64))


def test_amplitude_damping_has_off_diagonal_ptm_in_fixed_pauli_basis() -> None:
    gamma = 0.3
    kraus = torch.stack(
        [
            torch.tensor(
                [[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]],
                dtype=CDTYPE,
            ),
            torch.tensor(
                [[0.0, np.sqrt(gamma)], [0.0, 0.0]],
                dtype=CDTYPE,
            ),
        ]
    )

    ptm = pauli_transfer_matrix(kraus)

    expected = torch.tensor(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.sqrt(1.0 - gamma), 0.0, 0.0],
            [0.0, 0.0, np.sqrt(1.0 - gamma), 0.0],
            [gamma, 0.0, 0.0, 1.0 - gamma],
        ],
        dtype=torch.float64,
    )
    assert torch.allclose(ptm, expected, atol=1e-12, rtol=0.0)
    assert ptm[3, 0].item() == pytest.approx(gamma, abs=1e-12)

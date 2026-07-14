from __future__ import annotations

import numpy as np
import pytest

from error_coupling_simulator.certify.channel_diagnostics import (
    pauli_basis,
    ptm_from_kraus,
    ptm_from_unitary,
)


def test_two_qubit_identity_has_identity_ptm() -> None:
    ptm = ptm_from_unitary(np.eye(4, dtype=np.complex128))
    np.testing.assert_allclose(ptm, np.eye(16), atol=1e-14)


def test_two_qubit_coherent_channel_is_not_diagonal() -> None:
    theta = 0.2
    xx = dict(pauli_basis(2))["XX"]
    unitary = np.cos(theta) * np.eye(4) - 1j * np.sin(theta) * xx
    ptm = ptm_from_unitary(unitary)
    off_diagonal = ptm - np.diag(np.diag(ptm))
    assert np.linalg.norm(off_diagonal) > 0.1


def test_kraus_stack_and_sequence_are_equivalent() -> None:
    identity = np.eye(2, dtype=np.complex128)
    np.testing.assert_array_equal(
        ptm_from_kraus(np.stack([identity])),
        ptm_from_kraus([identity]),
    )


@pytest.mark.parametrize(
    "kraus",
    [
        [np.eye(3, dtype=np.complex128)],
        [np.eye(2, dtype=np.complex128), np.eye(4, dtype=np.complex128)],
        [],
    ],
)
def test_invalid_kraus_spaces_fail_loud(kraus) -> None:
    with pytest.raises(ValueError):
        ptm_from_kraus(kraus)

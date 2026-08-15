"""Operator-level checks for the supported coherent Pauli generators.

The references below are hand-typed Pauli matrices.  They deliberately do not call
the carrier's generator builder, so a wrong axis, normalization, or leaked-level
embedding changes the comparison result.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
    _hamiltonian_group_gates,
    _hamiltonian_matrix_for_term,
)


X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)

COHERENT_GENERATOR_CASES = [
    ("COH_RX", X, 0.5, (0,), (2,)),
    ("COH_RY", Y, 0.5, (0,), (2,)),
    ("COH_RZ", Z, 0.5, (0,), (2,)),
    ("COH_XX", np.kron(X, X), 0.25, (0, 1), (2, 2)),
    ("COH_YY", np.kron(Y, Y), 0.25, (0, 1), (2, 2)),
    (
        "COH_XX_YY",
        np.kron(X, X) + np.kron(Y, Y),
        0.25,
        (0, 1),
        (2, 2),
    ),
    ("COH_ZX", np.kron(Z, X), 0.25, (0, 1), (2, 2)),
]


@pytest.mark.parametrize(
    ("family", "reference"),
    [
        ("COH_RX", 0.5 * X),
        ("COH_RY", 0.5 * Y),
        ("COH_RZ", 0.5 * Z),
    ],
    ids=["x-rotation", "y-rotation", "z-rotation"],
)
def test_single_qubit_rotation_generator_matches_hand_typed_pauli(
    family: str,
    reference: np.ndarray,
) -> None:
    coefficient = 0.37
    actual = _hamiltonian_matrix_for_term(
        {"operator_family": family, "coefficient": coefficient},
        support=(0,),
        local_dims=(3,),
        device="cpu",
    )
    expected = np.zeros((3, 3), dtype=np.complex128)
    expected[:2, :2] = coefficient * reference

    np.testing.assert_allclose(actual.numpy(), expected, rtol=0.0, atol=1.0e-15)
    assert torch.equal(actual[2], torch.zeros(3, dtype=torch.complex128))
    assert torch.equal(actual[:, 2], torch.zeros(3, dtype=torch.complex128))


@pytest.mark.parametrize(
    ("family", "reference"),
    [
        ("COH_XX", np.kron(X, X)),
        ("COH_YY", np.kron(Y, Y)),
        ("COH_XX_YY", np.kron(X, X) + np.kron(Y, Y)),
        ("COH_ZX", np.kron(Z, X)),
        ("COH_CROSSTALK_ZZ", np.kron(Z, Z)),
    ],
    ids=["xx", "yy", "xx-plus-yy", "zx", "zz-crosstalk"],
)
def test_two_qubit_coupling_generator_matches_hand_typed_pauli_tensor(
    family: str,
    reference: np.ndarray,
) -> None:
    coefficient = -0.23
    actual = _hamiltonian_matrix_for_term(
        {"operator_family": family, "coefficient": coefficient},
        support=(0, 1),
        local_dims=(3, 3),
        device="cpu",
    )
    expected = np.zeros((9, 9), dtype=np.complex128)
    for left_out in (0, 1):
        for right_out in (0, 1):
            row = left_out * 3 + right_out
            qrow = left_out * 2 + right_out
            for left_in in (0, 1):
                for right_in in (0, 1):
                    col = left_in * 3 + right_in
                    qcol = left_in * 2 + right_in
                    expected[row, col] = 0.25 * coefficient * reference[qrow, qcol]

    np.testing.assert_allclose(actual.numpy(), expected, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(actual.numpy(), actual.numpy().conj().T, rtol=0.0, atol=0.0)
    assert np.trace(actual.numpy()) == pytest.approx(0.0, abs=1.0e-15)


def test_wrong_pauli_axis_is_detected_by_the_hand_typed_reference() -> None:
    coefficient = 0.41
    rx = _hamiltonian_matrix_for_term(
        {"operator_family": "COH_RX", "coefficient": coefficient},
        support=(0,),
        local_dims=(2,),
        device="cpu",
    ).numpy()
    wrong_axis = 0.5 * coefficient * Z

    assert not np.allclose(rx, wrong_axis, rtol=0.0, atol=1.0e-15)


@pytest.mark.parametrize(
    ("family", "reference", "scale", "support", "local_dims"),
    COHERENT_GENERATOR_CASES,
    ids=[
        "x-rotation",
        "y-rotation",
        "z-rotation",
        "xx-coupling",
        "yy-coupling",
        "xx-plus-yy-coupling",
        "ordered-zx-coupling",
    ],
)
def test_generator_exponentiates_to_the_hand_typed_unitary_channel(
    family: str,
    reference: np.ndarray,
    scale: float,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
) -> None:
    coefficient = 0.31
    hamiltonian = _hamiltonian_matrix_for_term(
        {"operator_family": family, "coefficient": coefficient},
        support=support,
        local_dims=local_dims,
        device="cpu",
    )
    expected_hamiltonian = torch.as_tensor(
        coefficient * scale * reference,
        dtype=torch.complex128,
    )
    actual_unitary = torch.linalg.matrix_exp(-1j * hamiltonian)
    reference_unitary = torch.linalg.matrix_exp(-1j * expected_hamiltonian)

    torch.testing.assert_close(
        actual_unitary,
        reference_unitary,
        rtol=0.0,
        atol=1.0e-14,
    )
    identity = torch.eye(
        actual_unitary.shape[0],
        dtype=torch.complex128,
    )
    torch.testing.assert_close(
        actual_unitary.conj().T @ actual_unitary,
        identity,
        rtol=0.0,
        atol=1.0e-14,
    )

    dimension = actual_unitary.shape[0]
    measured_infidelity = 1.0 - (
        abs(torch.trace(actual_unitary)) ** 2 + dimension
    ).real / (dimension * (dimension + 1))
    reference_infidelity = 1.0 - (
        abs(torch.trace(reference_unitary)) ** 2 + dimension
    ).real / (dimension * (dimension + 1))
    assert float(measured_infidelity) == pytest.approx(
        float(reference_infidelity),
        abs=1.0e-14,
    )


def test_xx_plus_yy_coupling_requires_both_summands() -> None:
    coefficient = 0.29
    actual = _hamiltonian_matrix_for_term(
        {"operator_family": "COH_XX_YY", "coefficient": coefficient},
        support=(0, 1),
        local_dims=(2, 2),
        device="cpu",
    ).numpy()
    expected = 0.25 * coefficient * (
        np.kron(X, X) + np.kron(Y, Y)
    )
    missing_yy = 0.25 * coefficient * np.kron(X, X)

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1.0e-15)
    assert not np.allclose(actual, missing_yy, rtol=0.0, atol=1.0e-15)


def test_ordered_zx_coupling_is_not_symmetric_under_site_swap() -> None:
    coefficient = -0.19
    actual = _hamiltonian_matrix_for_term(
        {"operator_family": "COH_ZX", "coefficient": coefficient},
        support=(0, 1),
        local_dims=(2, 2),
        device="cpu",
    ).numpy()
    expected = 0.25 * coefficient * np.kron(Z, X)
    swapped = 0.25 * coefficient * np.kron(X, Z)

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1.0e-15)
    assert not np.allclose(actual, swapped, rtol=0.0, atol=1.0e-15)


@pytest.mark.parametrize(
    ("family", "reference", "scale", "support", "local_dims"),
    COHERENT_GENERATOR_CASES,
    ids=[
        "x-rotation",
        "y-rotation",
        "z-rotation",
        "xx-coupling",
        "yy-coupling",
        "xx-plus-yy-coupling",
        "ordered-zx-coupling",
    ],
)
def test_compiled_hamiltonian_gate_matches_hand_typed_unitary_channel(
    family: str,
    reference: np.ndarray,
    scale: float,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
) -> None:
    coefficient = 0.27
    duration_ns = 0.83
    term = {
        "kind": "hamiltonian",
        "operator_family": family,
        "coefficient": coefficient,
        "support": list(support),
    }
    compiled = _hamiltonian_group_gates(
        {"substep_id": "physical-operation-test", "terms": [term]},
        dt_ns=duration_ns,
        local_dims=local_dims,
        device="cpu",
    )
    assert len(compiled) == 1
    assert compiled[0]["support"] == support
    actual_unitary = compiled[0]["gate"]

    reference_hamiltonian = torch.as_tensor(
        coefficient * scale * reference,
        dtype=torch.complex128,
    )
    reference_unitary = torch.linalg.matrix_exp(
        -1j * duration_ns * reference_hamiltonian
    )
    torch.testing.assert_close(
        actual_unitary,
        reference_unitary,
        rtol=0.0,
        atol=1.0e-14,
    )

    actual_superoperator = torch.kron(
        actual_unitary.conj(), actual_unitary
    )
    reference_superoperator = torch.kron(
        reference_unitary.conj(), reference_unitary
    )
    torch.testing.assert_close(
        actual_superoperator,
        reference_superoperator,
        rtol=0.0,
        atol=2.0e-14,
    )

    wrong_sign = torch.linalg.matrix_exp(
        1j * duration_ns * reference_hamiltonian
    )
    wrong_normalization = torch.linalg.matrix_exp(
        -2j * duration_ns * reference_hamiltonian
    )
    assert not torch.allclose(actual_unitary, wrong_sign, rtol=0.0, atol=1.0e-12)
    assert not torch.allclose(
        actual_unitary,
        wrong_normalization,
        rtol=0.0,
        atol=1.0e-12,
    )


def test_xx_plus_yy_channel_has_its_distinct_entanglement_infidelity() -> None:
    epsilon = 0.36
    compiled = _hamiltonian_group_gates(
        {
            "substep_id": "exchange-coupling-test",
            "terms": [{
                "kind": "hamiltonian",
                "operator_family": "COH_XX_YY",
                "coefficient": epsilon,
                "support": [0, 1],
            }],
        },
        dt_ns=1.0,
        local_dims=(2, 2),
        device="cpu",
    )
    unitary = compiled[0]["gate"]
    entanglement_infidelity = 1.0 - float(
        (abs(torch.trace(unitary)) ** 2 / 16.0).real
    )
    expected = 1.0 - np.cos(epsilon / 4.0) ** 4

    assert entanglement_infidelity == pytest.approx(expected, abs=1.0e-14)
    pure_axis_formula = np.sin(epsilon / 4.0) ** 2
    assert abs(entanglement_infidelity - pure_axis_formula) > 1.0e-5

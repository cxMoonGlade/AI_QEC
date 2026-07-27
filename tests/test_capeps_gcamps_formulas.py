from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
import stim

from error_coupling_simulator.carrier.capeps import (
    CAPEPSState,
    DenseResidual,
    ResidualStateError,
    StimCliffordFrame,
    TableauGeneratorBasis,
    decompose_pauli_in_tableau,
    expand_local_unitary_to_paulis,
)
from error_coupling_simulator.numerics import NUMERICAL_ZERO


I2 = np.eye(2, dtype=np.complex128)
X = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y = np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
PAULIS = (I2, X, Y, Z)
CX = np.asarray(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=np.complex128,
)


class _ForcedExpectationResidual(DenseResidual):
    def __init__(self, value: float) -> None:
        self._forced_value = value
        super().__init__(
            np.asarray([1.0, 0.0], dtype=np.complex128),
            num_qubits=1,
        )

    def copy(self) -> "_ForcedExpectationResidual":
        return _ForcedExpectationResidual(self._forced_value)

    def expectation_pauli(self, pauli: stim.PauliString) -> complex:
        del pauli
        return complex(self._forced_value)


def _fidelity(left: np.ndarray, right: np.ndarray) -> float:
    numerator = abs(np.vdot(left, right)) ** 2
    denominator = float(np.vdot(left, left).real * np.vdot(right, right).real)
    return float(numerator / denominator)


def _apply_local(
    vector: np.ndarray,
    unitary: np.ndarray,
    targets: tuple[int, ...],
    num_qubits: int,
) -> np.ndarray:
    rest = tuple(index for index in range(num_qubits) if index not in targets)
    permutation = targets + rest
    inverse = tuple(np.argsort(permutation).tolist())
    tensor = vector.reshape((2,) * num_qubits)
    front = np.transpose(tensor, permutation).reshape(1 << len(targets), -1)
    evolved = unitary @ front
    return np.transpose(
        evolved.reshape((2,) * num_qubits),
        inverse,
    ).reshape(-1)


def test_eq5_phase_ledger_fixes_y_order_and_conjugation_direction() -> None:
    identity_y = decompose_pauli_in_tableau(
        stim.Tableau(1),
        stim.PauliString("+Y"),
    )
    assert identity_y.stabilizer_exponents == (1,)
    assert identity_y.destabilizer_exponents == (1,)
    assert identity_y.ordered_generator_product == "+iY"
    assert identity_y.coefficient_phase == -1.0j
    assert identity_y.pulled_back_pauli == "+Y"

    phase_x = decompose_pauli_in_tableau(
        stim.Circuit("S 0").to_tableau(),
        stim.PauliString("+X"),
    )
    assert phase_x.ordered_generator_product == "-iX"
    assert phase_x.coefficient_phase == 1.0j
    assert phase_x.pulled_back_pauli == "-Y"

    entangling = stim.Circuit("S 0\nCX 0 1").to_tableau()
    entangling_y = decompose_pauli_in_tableau(
        entangling,
        stim.PauliString("+Y_"),
    )
    assert entangling_y.stabilizer_exponents == (0, 0)
    assert entangling_y.destabilizer_exponents == (1, 1)
    assert entangling_y.pulled_back_pauli == "+XX"


def test_eq5_round_trips_all_one_qubit_cliffords_and_pauli_phases() -> None:
    for tableau in stim.Tableau.iter_all(1):
        for label in "_XYZ":
            for prefix in ("+", "-", "+i", "-i"):
                physical = stim.PauliString(prefix + label)
                decomposition = decompose_pauli_in_tableau(tableau, physical)
                rebuilt = (
                    stim.PauliString(decomposition.ordered_generator_product)
                    * decomposition.coefficient_phase
                )
                direct = physical.before(tableau, targets=[0])
                assert rebuilt == physical
                assert stim.PauliString(decomposition.pulled_back_pauli) == direct


def test_eq5_round_trips_all_unsigned_two_qubit_cliffords() -> None:
    for tableau in stim.Tableau.iter_all(2, unsigned=True):
        basis = TableauGeneratorBasis(tableau)
        for labels in itertools.product("_XYZ", repeat=2):
            physical = stim.PauliString("+" + "".join(labels))
            decomposition = basis.decompose(physical)
            rebuilt = (
                stim.PauliString(decomposition.ordered_generator_product)
                * decomposition.coefficient_phase
            )
            direct = physical.before(tableau, targets=[0, 1])
            assert rebuilt == physical
            assert stim.PauliString(decomposition.pulled_back_pauli) == direct


def test_local_unitary_pauli_expansion_reconstructs_without_zero_filter() -> None:
    t_gate = np.asarray(
        [[1.0, 0.0], [0.0, np.exp(1.0j * math.pi / 4.0)]],
        dtype=np.complex128,
    )
    terms = expand_local_unitary_to_paulis(
        t_gate,
        (1,),
        num_qubits=3,
    )

    assert len(terms) == 4
    reconstructed = np.zeros((2, 2), dtype=np.complex128)
    for coefficient, pauli in terms:
        reconstructed += coefficient * PAULIS[int(pauli[1])]
    assert np.allclose(reconstructed, t_gate, atol=1e-15, rtol=0.0)

    state = CAPEPSState.dense_zero(3)
    state.apply_clifford(stim.Circuit("H 0\nCX 0 2"))
    before = state.physical_state_vector()
    update = state.apply_local_unitary(t_gate, (1,))
    expected = _apply_local(before, t_gate, (1,), 3)

    assert len(update.physical_terms) == 4
    assert len(update.tableau_decompositions) == 4
    assert 1.0 - _fidelity(state.physical_state_vector(), expected) <= 1e-12


def test_local_unitary_guard_and_reverse_two_site_order() -> None:
    state = CAPEPSState.dense_zero(3)
    state.apply_clifford(stim.Circuit("H 2"))
    before = state.physical_state_vector()

    update = state.apply_local_unitary(CX, (2, 0))
    expected = _apply_local(before, CX, (2, 0), 3)
    assert len(update.physical_terms) == 16
    assert 1.0 - _fidelity(state.physical_state_vector(), expected) <= 1e-12

    three_site = np.eye(8, dtype=np.complex128)
    frozen = state.physical_state_vector()
    with pytest.raises(ValueError, match="64 terms"):
        state.apply_local_unitary(three_site, (0, 1, 2))
    assert np.array_equal(state.physical_state_vector(), frozen)
    opted_in = expand_local_unitary_to_paulis(
        three_site,
        (0, 1, 2),
        num_qubits=3,
        max_local_qubits=3,
    )
    assert len(opted_in) == 64

    opted_update = state.apply_local_unitary(
        three_site,
        (0, 1, 2),
        max_local_qubits=3,
    )
    assert len(opted_update.physical_terms) == 64
    assert np.array_equal(state.physical_state_vector(), frozen)


def test_dense_exact_clifford_refactor_preserves_physical_ray() -> None:
    vector = np.asarray(
        [0.3 + 0.1j, -0.2 + 0.4j, 0.1 - 0.5j, 0.6 + 0.2j],
        dtype=np.complex128,
    )
    vector /= np.linalg.norm(vector)
    state = CAPEPSState(
        StimCliffordFrame(2),
        DenseResidual(vector, num_qubits=2),
    )
    state.apply_clifford(stim.Circuit("S 0\nH 1\nCX 1 0"))
    before_physical = state.physical_state_vector()
    before_residual = state.residual.state_vector()
    before_frame = state.frame.as_stim_tableau()

    local = stim.Circuit("H 0\nCX 0 1\nS 1").to_tableau()
    result = state.refactor_residual_clifford(local, (0, 1))

    embedded = stim.Tableau(2)
    embedded.append(local, [0, 1])
    expected_frame = before_frame * embedded.inverse()
    expected_residual = _apply_local(
        before_residual,
        np.asarray(local.to_unitary_matrix(endian="big"), dtype=np.complex128),
        (0, 1),
        2,
    )
    assert state.frame.as_stim_tableau() == expected_frame
    assert 1.0 - _fidelity(
        state.residual.state_vector(),
        expected_residual,
    ) <= 1e-12
    assert 1.0 - _fidelity(
        state.physical_state_vector(),
        before_physical,
    ) <= 1e-12
    assert result.residual_update.strategy == "dense_exact_local_clifford"


def test_peps_exact_refactor_and_nonadjacent_failure_are_transactional() -> None:
    state = CAPEPSState.peps_zero((1, 2), contraction_optimize="greedy")
    state.apply_ry(0, 0.7)
    before = state.physical_state_vector()

    result = state.refactor_residual_clifford(
        stim.Circuit("CX 0 1").to_tableau(),
        (0, 1),
    )

    assert result.residual_update.strategy == "two_site_clifford_split_untruncated"
    assert 1.0 - _fidelity(state.physical_state_vector(), before) <= 1e-12

    vertical = CAPEPSState.peps_zero((2, 1), contraction_optimize="greedy")
    vertical.apply_ry(1, 0.23)
    vertical_before = vertical.physical_state_vector()
    vertical_result = vertical.refactor_residual_clifford(
        stim.Circuit("H 0\nCX 0 1").to_tableau(),
        (1, 0),
    )
    assert vertical_result.residual_update.strategy == (
        "two_site_clifford_split_untruncated"
    )
    assert 1.0 - _fidelity(
        vertical.physical_state_vector(),
        vertical_before,
    ) <= 1e-12

    separated = CAPEPSState.peps_zero((1, 3), contraction_optimize="greedy")
    separated.apply_ry(1, 0.31)
    before_state = separated.physical_state_vector()
    before_frame = separated.frame.as_stim_tableau()
    with pytest.raises(ValueError, match="adjacent"):
        separated.refactor_residual_clifford(
            stim.Circuit("CX 0 1").to_tableau(),
            (0, 2),
        )
    assert separated.frame.as_stim_tableau() == before_frame
    assert np.array_equal(separated.physical_state_vector(), before_state)


def test_pauli_expectation_clamps_roundoff_and_rejects_unphysical_value() -> None:
    rounded = CAPEPSState(
        StimCliffordFrame(1),
        _ForcedExpectationResidual(1.0 + 0.5 * NUMERICAL_ZERO),
    )
    assert rounded.expectation_pauli(stim.PauliString("Z")).value == 1.0

    invalid = CAPEPSState(
        StimCliffordFrame(1),
        _ForcedExpectationResidual(1.0 + 2.0 * NUMERICAL_ZERO),
    )
    with pytest.raises(ResidualStateError, match="outside"):
        invalid.expectation_pauli(stim.PauliString("Z"))


@pytest.mark.parametrize("backend", ["dense", "peps"])
def test_pauli_expectation_matches_born_branch_identity(backend: str) -> None:
    state = (
        CAPEPSState.dense_zero(2)
        if backend == "dense"
        else CAPEPSState.peps_zero((1, 2), contraction_optimize="greedy")
    )
    state.apply_clifford(stim.Circuit("H 0\nCX 0 1"))

    xx = state.expectation_pauli(stim.PauliString("XX"))
    zz = state.expectation_pauli(stim.PauliString("ZZ"))
    assert xx.value == pytest.approx(1.0, abs=1e-12)
    assert zz.value == pytest.approx(1.0, abs=1e-12)

    state.apply_ry(0, 0.37)
    observable = stim.PauliString("Z_")
    expectation = state.expectation_pauli(observable).value
    branch_zero, branch_one = state.fork_measurement(observable)
    assert branch_zero.conditional_probability == pytest.approx(
        0.5 * (1.0 + expectation),
        abs=1e-12,
    )
    assert branch_one.conditional_probability == pytest.approx(
        0.5 * (1.0 - expectation),
        abs=1e-12,
    )

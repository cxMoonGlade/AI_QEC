from __future__ import annotations

import math

import numpy as np
import pytest
import stim

from error_coupling_simulator.carrier.capeps import (
    CAPEPSState,
    DenseResidual,
    FrameBackendUnavailable,
    QuimbPepsResidual,
    SdimCliffordFrame,
    StimCliffordFrame,
    sdim_backend_status,
)
from error_coupling_simulator.carrier.capeps.frame import (
    _sdim_generator_to_stim_pauli,
)


I2 = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
X = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y = np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
S = np.asarray([[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128)
CX = np.asarray(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=np.complex128,
)


def _fidelity(left: np.ndarray, right: np.ndarray) -> float:
    numerator = abs(np.vdot(left, right)) ** 2
    denominator = float(np.vdot(left, left).real * np.vdot(right, right).real)
    return float(numerator / denominator)


def _ry(angle: float) -> np.ndarray:
    half = 0.5 * angle
    return np.asarray(
        [
            [math.cos(half), -math.sin(half)],
            [math.sin(half), math.cos(half)],
        ],
        dtype=np.complex128,
    )


def test_stim_frame_uses_left_composition_and_signed_pullback() -> None:
    frame = StimCliffordFrame(2)
    frame.apply_clifford(stim.Circuit("S 0"))
    frame.apply_clifford(stim.Circuit("CX 0 1"))

    physical_pauli = stim.PauliString("Y_")
    pulled = frame.pullback_pauli(physical_pauli)

    assert str(pulled) == "+XX"

    # Independent complex128 matrix reconstruction.  Qubit zero is the MSB.
    clifford = CX @ np.kron(S, I2)
    physical = np.kron(Y, I2)
    xx = np.kron(X, X)
    assert np.allclose(
        clifford.conj().T @ physical @ clifford,
        xx,
        atol=1e-12,
        rtol=0.0,
    )
    # The common direction error has the opposite sign for this fixture.
    assert np.allclose(
        clifford @ physical @ clifford.conj().T,
        -xx,
        atol=1e-12,
        rtol=0.0,
    )


def test_dense_coherent_ry_matches_independent_physical_reference_not_twirl() -> None:
    angle = 0.02
    state = CAPEPSState.dense_zero(2)
    state.apply_clifford(stim.Circuit("S 0\nCX 0 1"))

    residual_before = state.residual.state_vector()
    update = state.apply_ry(0, angle)
    candidate = state.physical_state_vector()

    initial = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
    clifford = CX @ np.kron(S, I2)
    reference = np.kron(_ry(angle), I2) @ clifford @ initial

    assert update.pulled_back_terms[1][1] == "+XX"
    assert update.residual_update.strategy == "dense_exact"
    assert 1.0 - _fidelity(candidate, reference) <= 1e-12
    assert np.array_equal(residual_before, initial)

    # A Pauli twirl would remove the coherent cross term and is a different
    # physical object even though it uses the same two Pauli bodies.
    base = clifford @ initial
    flipped = np.kron(Y, I2) @ base
    half = 0.5 * angle
    twirled = (
        math.cos(half) ** 2 * np.outer(base, base.conj())
        + math.sin(half) ** 2 * np.outer(flipped, flipped.conj())
    )
    coherent = np.outer(candidate, candidate.conj())
    assert np.linalg.norm(coherent - twirled) > 1e-4


def test_quimb_peps_executes_nonlocal_pulled_rotation_by_untruncated_direct_sum() -> None:
    angle = 0.02
    state = CAPEPSState.peps_zero((1, 2))
    residual = state.residual
    assert isinstance(residual, QuimbPepsResidual)
    assert residual.max_bond_dimension == 1

    before = residual.state_vector()
    state.apply_clifford(stim.Circuit("S 0\nCX 0 1"))
    # Clifford routing touches only the frame.
    assert np.array_equal(residual.state_vector(), before)

    update = state.apply_ry(0, angle)
    candidate = state.physical_state_vector()

    initial = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
    reference = np.kron(_ry(angle), I2) @ CX @ np.kron(S, I2) @ initial

    assert update.pulled_back_terms[1][1] == "+XX"
    assert update.residual_update.strategy == "global_direct_sum_untruncated"
    assert update.residual_update.max_bond_before == 1
    assert update.residual_update.max_bond_after == 2
    assert 1.0 - _fidelity(candidate, reference) <= 1e-12


def test_quimb_local_rotation_keeps_bond_and_copies_input_vectors() -> None:
    local = np.asarray([1.0, 0.0], dtype=np.complex128)
    residual = QuimbPepsResidual.product_state((1, 2), [local, local])
    state = CAPEPSState(StimCliffordFrame(2), residual)

    # Mutating caller-owned input after construction cannot change the PEPS.
    local[:] = np.asarray([0.0, 1.0], dtype=np.complex128)
    assert np.array_equal(
        residual.state_vector(),
        np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.complex128),
    )

    update = state.apply_ry(0, 0.02)

    assert update.residual_update.strategy == "one_site_untruncated_gate"
    assert update.residual_update.max_bond_before == 1
    assert update.residual_update.max_bond_after == 1
    assert 1.0 - _fidelity(
        state.physical_state_vector(),
        np.kron(_ry(0.02), I2)
        @ np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.complex128),
    ) <= 1e-12


def test_measurement_forks_share_parent_snapshot_and_z_reset_is_exact() -> None:
    vector = np.asarray(
        [math.sqrt(0.8), math.sqrt(0.2)],
        dtype=np.complex128,
    )
    external_frame = StimCliffordFrame(1)
    external_residual = DenseResidual(vector, num_qubits=1)
    parent = CAPEPSState(external_frame, external_residual)
    z = stim.PauliString("Z")

    # Constructor inputs and public accessors are snapshots, so callers cannot
    # bypass transactional updates or the measurement ledger through aliases.
    external_frame.apply_clifford(stim.Circuit("H 0"))
    external_residual.apply_pauli_sum(((1.0, stim.PauliString("X")),))
    frame_snapshot = parent.frame
    frame_snapshot.apply_clifford(stim.Circuit("H 0"))
    residual_snapshot = parent.residual
    residual_snapshot.apply_pauli_sum(((1.0, stim.PauliString("X")),))
    assert np.array_equal(parent.residual.state_vector(), vector)
    assert 1.0 - _fidelity(parent.physical_state_vector(), vector) <= 1e-12

    branch_zero, branch_one = parent.fork_measurement(z, reset_to_zero=True)

    assert parent.measurement_events == ()
    assert np.array_equal(parent.residual.state_vector(), vector)
    assert branch_zero.state is not None
    assert branch_one.state is not None
    assert branch_zero.conditional_probability == pytest.approx(0.8, abs=1e-15)
    assert branch_one.conditional_probability == pytest.approx(0.2, abs=1e-15)
    assert (
        branch_zero.conditional_probability + branch_one.conditional_probability
        == pytest.approx(1.0, abs=1e-15)
    )
    expected_reset = np.asarray([1.0, 0.0], dtype=np.complex128)
    assert 1.0 - _fidelity(
        branch_zero.state.physical_state_vector(),
        expected_reset,
    ) <= 1e-12
    assert 1.0 - _fidelity(
        branch_one.state.physical_state_vector(),
        expected_reset,
    ) <= 1e-12
    assert branch_one.state.measurement_events[0].reset_to_zero is True
    assert branch_one.state.branch_log_mass == pytest.approx(
        math.log(0.2),
        abs=1e-15,
    )


def test_quimb_measurement_pulls_nonlocal_pauli_and_resets_physical_qubit() -> None:
    parent = CAPEPSState.peps_zero((1, 2))
    parent.apply_clifford(stim.Circuit("H 0\nCX 0 1"))

    branch_zero, branch_one = parent.fork_measurement(
        stim.PauliString("_Z"),
        reset_to_zero=True,
    )

    assert parent.measurement_events == ()
    assert branch_zero.state is not None
    assert branch_one.state is not None
    assert branch_zero.conditional_probability == pytest.approx(0.5, abs=1e-15)
    assert branch_one.conditional_probability == pytest.approx(0.5, abs=1e-15)
    assert (
        branch_zero.state.measurement_events[0].pulled_back_pauli
        == "+XZ"
    )
    assert (
        branch_one.state.measurement_events[0].residual_update.strategy
        == "global_direct_sum_untruncated"
    )

    expected_zero = np.asarray(
        [1.0, 0.0, 0.0, 0.0],
        dtype=np.complex128,
    )
    # Outcome one first produces |11>; the physical X reset on qubit one
    # then produces |10> in the declared MSB-first convention.
    expected_one_after_reset = np.asarray(
        [0.0, 0.0, 1.0, 0.0],
        dtype=np.complex128,
    )
    assert 1.0 - _fidelity(
        branch_zero.state.physical_state_vector(),
        expected_zero,
    ) <= 1e-12
    assert 1.0 - _fidelity(
        branch_one.state.physical_state_vector(),
        expected_one_after_reset,
    ) <= 1e-12

    # A deterministic PEPS projector can contract to 1 + O(eps).  This is
    # upper-bound roundoff, not an invalid branch, and is clamped to one.
    deterministic = CAPEPSState.peps_zero(
        (1, 2),
        contraction_optimize="greedy",
    )
    deterministic.apply_clifford(stim.Circuit("H 0\nH 1"))
    deterministic.apply_pauli_rotation(stim.PauliString("+X_"), 0.1)
    event = deterministic.measure_pauli(stim.PauliString("+XX"), 0)
    assert event.conditional_probability == 1.0


def test_tiny_positive_measurement_branch_is_not_floored_to_zero() -> None:
    vector = np.asarray([1.0, 1e-14], dtype=np.complex128)
    state = CAPEPSState(
        StimCliffordFrame(1),
        DenseResidual(vector, num_qubits=1),
    )

    event = state.measure_pauli(stim.PauliString("Z"), 1)

    assert event.conditional_probability > 0.0
    assert event.conditional_probability == pytest.approx(1e-28, rel=1e-12)
    assert state.physical_state_vector()[1] == pytest.approx(1.0 + 0.0j)


def test_sdim_bridge_is_explicit_and_preserves_generator_sign() -> None:
    plus_y = _sdim_generator_to_stim_pauli(
        np.asarray([1], dtype=np.int64),
        np.asarray([1], dtype=np.int64),
        1,
    )
    minus_y = _sdim_generator_to_stim_pauli(
        np.asarray([1], dtype=np.int64),
        np.asarray([1], dtype=np.int64),
        3,
    )
    assert str(plus_y) == "+Y"
    assert str(minus_y) == "-Y"

    status = sdim_backend_status()
    if status.available:
        frame = SdimCliffordFrame(2)
        frame.apply_clifford(stim.Circuit("S 0\nCX 0 1"))
        assert str(frame.pullback_pauli(stim.PauliString("Y_"))) == "+XX"
    else:
        with pytest.raises(FrameBackendUnavailable):
            SdimCliffordFrame(2)

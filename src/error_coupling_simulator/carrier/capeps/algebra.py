from __future__ import annotations

"""Qubit algebra used by the Clifford-frame and residual-state layers."""

import itertools
import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
import stim

from ...numerics import NUMERICAL_ZERO


_CDTYPE = np.dtype(np.complex128)
_I = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=_CDTYPE)
_X = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=_CDTYPE)
_Y = np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=_CDTYPE)
_Z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=_CDTYPE)
_H = np.asarray([[1.0, 1.0], [1.0, -1.0]], dtype=_CDTYPE) / math.sqrt(2.0)
_S = np.asarray([[1.0, 0.0], [0.0, 1.0j]], dtype=_CDTYPE)
_CX = np.asarray(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=_CDTYPE,
)
for _matrix in (_I, _X, _Y, _Z, _H, _S, _CX):
    _matrix.setflags(write=False)

PAULI_MATRICES = (_I, _X, _Y, _Z)


@dataclass(frozen=True)
class TableauPauliDecomposition:
    """Exact qubit specialization of the paper's Eq. (5).

    Stabilizer exponents multiply ``C Z_i C^dagger`` first, followed by
    destabilizer exponents multiplying ``C X_i C^dagger``.  The explicit
    complex phase is required because Stim's Hermitian ``Y`` label already
    includes the factor in ``Y = i X Z``.
    """

    physical_pauli: str
    stabilizer_exponents: tuple[int, ...]
    destabilizer_exponents: tuple[int, ...]
    ordered_generator_product: str
    coefficient_phase: complex
    pulled_back_pauli: str


def require_targets(
    targets: Sequence[int],
    *,
    num_qubits: int,
    expected_count: int | None = None,
) -> tuple[int, ...]:
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        raise TypeError("targets must be a sequence of qubit indices")
    out: list[int] = []
    for target in targets:
        if isinstance(target, bool) or not isinstance(target, int):
            raise TypeError("targets must contain integers")
        if target < 0 or target >= num_qubits:
            raise ValueError("target is outside the state")
        out.append(target)
    if not out:
        raise ValueError("at least one target is required")
    if len(set(out)) != len(out):
        raise ValueError("targets must be distinct")
    if expected_count is not None and len(out) != expected_count:
        raise ValueError(
            f"expected {expected_count} targets, received {len(out)}"
        )
    return tuple(out)


def apply_unitary_to_axes(
    vector: np.ndarray,
    unitary: np.ndarray,
    targets: tuple[int, ...],
    num_qubits: int,
) -> np.ndarray:
    remaining = tuple(index for index in range(num_qubits) if index not in targets)
    permutation = targets + remaining
    inverse = tuple(np.argsort(permutation).tolist())
    tensor = vector.reshape((2,) * num_qubits)
    front = np.transpose(tensor, permutation).reshape(1 << len(targets), -1)
    evolved = unitary @ front
    tensor = evolved.reshape((2,) * num_qubits)
    return np.transpose(tensor, inverse).reshape(-1)


def apply_local_tableau_to_vector(
    vector: np.ndarray,
    tableau: stim.Tableau,
    targets: Sequence[int],
    *,
    num_qubits: int,
) -> np.ndarray:
    """Apply a local Clifford using complex128 H/S/CX synthesis."""

    if not isinstance(tableau, stim.Tableau):
        raise TypeError("tableau must be a stim.Tableau")
    checked = require_targets(
        targets,
        num_qubits=num_qubits,
        expected_count=len(tableau),
    )
    expected_shape = (1 << num_qubits,)
    if not isinstance(vector, np.ndarray) or vector.shape != expected_shape:
        raise ValueError(f"vector must have shape {expected_shape}")
    if vector.dtype != _CDTYPE:
        raise TypeError("vector dtype must be complex128")
    out = np.array(vector, copy=True)
    for instruction in tableau.to_circuit(method="elimination").flattened():
        if not isinstance(instruction, stim.CircuitInstruction):
            raise RuntimeError("tableau synthesis yielded a non-instruction")
        local = instruction.targets_copy()
        if any(not target.is_qubit_target for target in local):
            raise RuntimeError("tableau synthesis yielded a non-qubit target")
        mapped = tuple(checked[int(target.qubit_value)] for target in local)
        if instruction.name == "H":
            for target in mapped:
                out = apply_unitary_to_axes(out, _H, (target,), num_qubits)
        elif instruction.name == "S":
            for target in mapped:
                out = apply_unitary_to_axes(out, _S, (target,), num_qubits)
        elif instruction.name == "CX":
            if len(mapped) % 2:
                raise RuntimeError("synthesized CX instruction has odd target count")
            for offset in range(0, len(mapped), 2):
                out = apply_unitary_to_axes(
                    out,
                    _CX,
                    (mapped[offset], mapped[offset + 1]),
                    num_qubits,
                )
        else:
            raise RuntimeError(
                f"unexpected gate {instruction.name!r} in tableau synthesis"
            )
    return out


def tableau_unitary_complex128(tableau: stim.Tableau) -> np.ndarray:
    """Materialize a small Clifford without Stim's complex64 conversion."""

    if not isinstance(tableau, stim.Tableau):
        raise TypeError("tableau must be a stim.Tableau")
    num_qubits = len(tableau)
    dimension = 1 << num_qubits
    unitary = np.empty((dimension, dimension), dtype=_CDTYPE)
    for column in range(dimension):
        basis = np.zeros(dimension, dtype=_CDTYPE)
        basis[column] = 1.0
        unitary[:, column] = apply_local_tableau_to_vector(
            basis,
            tableau,
            tuple(range(num_qubits)),
            num_qubits=num_qubits,
        )
    return unitary


def apply_pauli_to_vector(
    vector: np.ndarray,
    pauli: stim.PauliString,
) -> np.ndarray:
    num_qubits = len(pauli)
    tensor = vector.reshape((2,) * num_qubits)
    for qubit in range(num_qubits):
        code = int(pauli[qubit])
        if code == 0:
            continue
        tensor = np.tensordot(
            PAULI_MATRICES[code],
            tensor,
            axes=([1], [qubit]),
        )
        tensor = np.moveaxis(tensor, 0, qubit)
    out = np.asarray(tensor.reshape(-1), dtype=_CDTYPE)
    out *= complex(pauli.sign)
    return out


def _invert_gf2(matrix: np.ndarray) -> np.ndarray:
    """Invert a square full-rank matrix over GF(2)."""

    left = np.asarray(matrix, dtype=np.uint8) % 2
    if left.ndim != 2 or left.shape[0] != left.shape[1]:
        raise ValueError("GF(2) coefficient matrix must be square")
    width = left.shape[0]
    augmented = np.concatenate(
        (left.copy(), np.eye(width, dtype=np.uint8)),
        axis=1,
    )
    for column in range(width):
        candidates = np.flatnonzero(augmented[column:, column])
        if candidates.size == 0:
            raise ValueError("tableau generator matrix is singular over GF(2)")
        pivot = column + int(candidates[0])
        if pivot != column:
            augmented[[column, pivot]] = augmented[[pivot, column]]
        for row in range(width):
            if row != column and augmented[row, column]:
                augmented[row] ^= augmented[column]
    if not np.array_equal(augmented[:, :width], np.eye(width, dtype=np.uint8)):
        raise ValueError("GF(2) elimination did not produce an identity block")
    return augmented[:, width:]


class TableauGeneratorBasis:
    """Reusable qubit generator basis for GCAMPS Eq. (5).

    One Gauss-Jordan inversion is shared by every Pauli term in the same
    coherent update instead of rebuilding and eliminating the tableau matrix
    for each of the ``4^k`` local-unitary coefficients.
    """

    def __init__(self, tableau: stim.Tableau) -> None:
        if not isinstance(tableau, stim.Tableau):
            raise TypeError("tableau must be a stim.Tableau")
        self._tableau = tableau.copy()
        self._num_qubits = len(tableau)
        if self._num_qubits == 0:
            raise ValueError("tableau must contain at least one qubit")
        self._stabilizers = tuple(
            tableau.z_output(index) for index in range(self._num_qubits)
        )
        self._destabilizers = tuple(
            tableau.x_output(index) for index in range(self._num_qubits)
        )
        columns: list[np.ndarray] = []
        for generator in self._stabilizers + self._destabilizers:
            x, z = generator.to_numpy()
            columns.append(np.concatenate((x, z)).astype(np.uint8))
        self._matrix = np.column_stack(columns)
        self._inverse = _invert_gf2(self._matrix)

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def generator_matrix(self) -> np.ndarray:
        out = np.array(self._matrix, copy=True)
        out.setflags(write=False)
        return out

    def decompose(
        self,
        pauli: stim.PauliString,
    ) -> TableauPauliDecomposition:
        if not isinstance(pauli, stim.PauliString):
            raise TypeError("pauli must be a stim.PauliString")
        if len(pauli) != self._num_qubits:
            raise ValueError("Pauli and tableau widths differ")

        pauli_x, pauli_z = pauli.to_numpy()
        rhs = np.concatenate((pauli_x, pauli_z)).astype(np.uint8)
        exponents = (self._inverse @ rhs) % 2
        stabilizer_exponents = tuple(
            int(value) for value in exponents[: self._num_qubits]
        )
        destabilizer_exponents = tuple(
            int(value) for value in exponents[self._num_qubits :]
        )

        ordered = stim.PauliString(self._num_qubits)
        for exponent, generator in zip(
            stabilizer_exponents,
            self._stabilizers,
            strict=True,
        ):
            if exponent:
                ordered *= generator
        for exponent, generator in zip(
            destabilizer_exponents,
            self._destabilizers,
            strict=True,
        ):
            if exponent:
                ordered *= generator
        ordered_x, ordered_z = ordered.to_numpy()
        if not np.array_equal(ordered_x, pauli_x) or not np.array_equal(
            ordered_z,
            pauli_z,
        ):
            raise ValueError("Eq. (5) generator exponents do not reconstruct P")
        phase = complex(pauli.sign) / complex(ordered.sign)
        if phase not in (1.0 + 0.0j, -1.0 + 0.0j, 1.0j, -1.0j):
            raise ValueError("Eq. (5) produced a non-Pauli coefficient phase")

        canonical = stim.PauliString(self._num_qubits)
        for index, exponent in enumerate(stabilizer_exponents):
            if exponent:
                factor = stim.PauliString(self._num_qubits)
                factor[index] = 3
                canonical *= factor
        for index, exponent in enumerate(destabilizer_exponents):
            if exponent:
                factor = stim.PauliString(self._num_qubits)
                factor[index] = 1
                canonical *= factor
        pulled = canonical * phase
        direct = pauli.before(
            self._tableau,
            targets=range(self._num_qubits),
        )
        if pulled != direct:
            raise ValueError(
                "Eq. (5) reconstruction disagrees with Stim signed pullback"
            )
        return TableauPauliDecomposition(
            physical_pauli=str(pauli),
            stabilizer_exponents=stabilizer_exponents,
            destabilizer_exponents=destabilizer_exponents,
            ordered_generator_product=str(ordered),
            coefficient_phase=phase,
            pulled_back_pauli=str(pulled),
        )


def decompose_pauli_in_tableau(
    tableau: stim.Tableau,
    pauli: stim.PauliString,
) -> TableauPauliDecomposition:
    """Decompose one Pauli using a freshly constructed Eq. (5) basis."""

    return TableauGeneratorBasis(tableau).decompose(pauli)


def expand_local_unitary_to_paulis(
    unitary: np.ndarray,
    targets: Sequence[int],
    *,
    num_qubits: int,
    max_local_qubits: int = 2,
) -> tuple[tuple[complex, stim.PauliString], ...]:
    """Expand a small qubit unitary in the orthogonal Pauli basis.

    Harper et al. specify a numerical linear solve but not its matrix layout.
    For the qubit Pauli basis, orthogonality gives the equivalent project
    identity ``c_P = Tr(P^dagger U) / 2^k``.  Every one of the ``4^k``
    coefficients is returned; no floating threshold is used to infer a
    structural zero.  The default two-qubit resource guard prevents an
    accidental exponential expansion; larger support requires explicit opt-in.
    """

    if not isinstance(unitary, np.ndarray):
        raise TypeError("unitary must be a numpy.ndarray")
    if unitary.dtype != _CDTYPE:
        raise TypeError("unitary dtype must be complex128")
    if (
        isinstance(max_local_qubits, bool)
        or not isinstance(max_local_qubits, int)
    ):
        raise TypeError("max_local_qubits must be an integer")
    if max_local_qubits <= 0:
        raise ValueError("max_local_qubits must be positive")
    checked = require_targets(targets, num_qubits=num_qubits)
    if len(checked) > max_local_qubits:
        raise ValueError(
            "local Pauli expansion would create "
            f"{4 ** len(checked)} terms; max_local_qubits="
            f"{max_local_qubits} requires explicit opt-in"
        )
    local_dimension = 1 << len(checked)
    if unitary.shape != (local_dimension, local_dimension):
        raise ValueError(
            f"unitary must have shape {(local_dimension, local_dimension)}"
        )
    if not np.isfinite(unitary).all():
        raise ValueError("unitary must contain only finite values")
    gram = unitary.conj().T @ unitary
    discrepancy = float(np.max(np.abs(gram - np.eye(local_dimension))))
    if discrepancy > NUMERICAL_ZERO:
        raise ValueError(
            f"matrix is not unitary within NUMERICAL_ZERO: {discrepancy}"
        )

    terms: list[tuple[complex, stim.PauliString]] = []
    for codes in itertools.product(range(4), repeat=len(checked)):
        local_pauli = np.asarray([[1.0 + 0.0j]], dtype=_CDTYPE)
        full_pauli = stim.PauliString(num_qubits)
        for target, code in zip(checked, codes, strict=True):
            local_pauli = np.kron(local_pauli, PAULI_MATRICES[code])
            full_pauli[target] = code
        coefficient = complex(np.vdot(local_pauli, unitary) / local_dimension)
        terms.append((coefficient, full_pauli))
    return tuple(terms)

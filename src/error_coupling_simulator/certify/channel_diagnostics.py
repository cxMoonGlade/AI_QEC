"""Implementation-independent Pauli-transfer diagnostics for qubit channels.

These helpers accept ordinary NumPy unitaries or Kraus operators and therefore
work for one or more qubits.  They are certification algebra: they inspect an
already specified channel and do not construct, fit, or calibrate one.
"""

from __future__ import annotations

from itertools import product
from typing import Sequence

import numpy as np


Array = np.ndarray


def pauli_basis(num_qubits: int) -> list[tuple[str, Array]]:
    """Return the ordered, unnormalised ``I/X/Y/Z`` tensor-product basis."""

    n = int(num_qubits)
    if n <= 0:
        raise ValueError("num_qubits must be positive")
    one = {
        "I": np.eye(2, dtype=np.complex128),
        "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        "Y": np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128),
        "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
    }
    basis: list[tuple[str, Array]] = []
    for labels in product(("I", "X", "Y", "Z"), repeat=n):
        operator = one[labels[0]]
        for label in labels[1:]:
            operator = np.kron(operator, one[label])
        basis.append(("".join(labels), operator))
    return basis


def ptm_from_unitary(unitary: Array) -> Array:
    """Return the PTM of a square qubit-space unitary matrix."""

    operator = np.asarray(unitary, dtype=np.complex128)
    if operator.ndim != 2 or operator.shape[0] != operator.shape[1]:
        raise ValueError("unitary must be square")
    return ptm_from_kraus((operator,))


def ptm_from_kraus(kraus: Sequence[Array] | Array) -> Array:
    r"""Return ``R_ab = Tr(P_a Phi(P_b)) / d`` for a qubit channel.

    The channel dimension must be a positive power of two and every Kraus
    operator must have the same square shape.  Kraus completeness is not
    imposed here: the same diagnostic is useful for trace-decreasing channel
    branches, while CPTP checks remain a separate certification assertion.
    """

    operators = _normalise_kraus(kraus)
    dim = operators[0].shape[0]
    basis = pauli_basis(_num_qubits_from_dim(dim))
    out = np.empty((len(basis), len(basis)), dtype=np.float64)
    for col, (_input_label, p_in) in enumerate(basis):
        evolved = sum(
            (operator @ p_in @ operator.conj().T for operator in operators),
            start=np.zeros_like(p_in, dtype=np.complex128),
        )
        for row, (_output_label, p_out) in enumerate(basis):
            out[row, col] = float(np.real(np.trace(p_out @ evolved) / dim))
    if not np.isfinite(out).all():
        raise ValueError("channel produced a non-finite Pauli-transfer matrix")
    return out


def _normalise_kraus(kraus: Sequence[Array] | Array) -> tuple[Array, ...]:
    if isinstance(kraus, np.ndarray) and kraus.ndim == 2:
        raw = (kraus,)
    else:
        raw = tuple(kraus)
    if not raw:
        raise ValueError("at least one Kraus operator is required")
    operators = tuple(np.asarray(operator, dtype=np.complex128) for operator in raw)
    first = operators[0]
    if first.ndim != 2 or first.shape[0] != first.shape[1]:
        raise ValueError("Kraus operators must be square")
    shape = first.shape
    if any(operator.shape != shape for operator in operators):
        raise ValueError("all Kraus operators must have the same square shape")
    if any(not np.isfinite(operator).all() for operator in operators):
        raise ValueError("Kraus operators must be finite")
    _num_qubits_from_dim(shape[0])
    return operators


def _num_qubits_from_dim(dim: int) -> int:
    value = int(dim)
    if value < 2 or value & (value - 1):
        raise ValueError("channel dimension must be a positive qubit-space power of two")
    return value.bit_length() - 1


__all__ = ["pauli_basis", "ptm_from_kraus", "ptm_from_unitary"]

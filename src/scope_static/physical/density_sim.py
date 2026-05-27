from __future__ import annotations

import numpy as np

from scope_static.numerics import NUMERICAL_ZERO


Array = np.ndarray


def apply_kraus(rho: Array, kraus: list[Array] | tuple[Array, ...]) -> Array:
    state = np.asarray(rho, dtype=np.complex128)
    if state.ndim != 2 or state.shape[0] != state.shape[1]:
        raise ValueError("rho must be a square density matrix")
    out = np.zeros_like(state)
    for op in kraus:
        k = np.asarray(op, dtype=np.complex128)
        if k.shape != state.shape:
            raise ValueError("Kraus operators must match rho shape")
        out = out + k @ state @ k.conj().T
    return _hermitianize(out)


def measurement_probabilities_z(rho: Array, num_qubits: int | None = None) -> Array:
    state = np.asarray(rho, dtype=np.complex128)
    if state.ndim != 2 or state.shape[0] != state.shape[1]:
        raise ValueError("rho must be a square density matrix")
    dim = state.shape[0]
    if num_qubits is not None and dim != 2 ** int(num_qubits):
        raise ValueError("rho dimension does not match num_qubits")
    probs = np.real(np.diag(state)).astype(np.float64)
    probs = np.clip(probs, NUMERICAL_ZERO, None)
    total = float(probs.sum())
    if total <= NUMERICAL_ZERO:
        raise ValueError("density matrix has zero measurement weight")
    return probs / total


def tensor_product_state_zero(num_qubits: int) -> Array:
    dim = 2 ** int(num_qubits)
    rho = np.zeros((dim, dim), dtype=np.complex128)
    rho[0, 0] = 1.0
    return rho


def _hermitianize(rho: Array) -> Array:
    return 0.5 * (rho + rho.conj().T)

from __future__ import annotations

from itertools import product
import math

import numpy as np

from scope_static.numerics import NUMERICAL_ZERO

from scope_static.backend.channels import MechanismSpec, mechanism_channel
from scope_static.backend.mechanism_catalog import RZZ_FAMILY_IDS


Array = np.ndarray


def pauli_basis(num_qubits: int) -> list[tuple[str, Array]]:
    if int(num_qubits) <= 0:
        raise ValueError("num_qubits must be positive")
    one = {
        "I": np.eye(2, dtype=np.complex128),
        "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        "Y": np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128),
        "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
    }
    basis = []
    for labels in product(("I", "X", "Y", "Z"), repeat=int(num_qubits)):
        mat = one[labels[0]]
        for label in labels[1:]:
            mat = np.kron(mat, one[label])
        basis.append(("".join(labels), mat))
    return basis


def ptm_from_unitary(unitary: Array) -> Array:
    u = np.asarray(unitary, dtype=np.complex128)
    if u.ndim != 2 or u.shape[0] != u.shape[1]:
        raise ValueError("unitary must be square")
    return ptm_from_kraus([u])


def ptm_from_kraus(kraus: list[Array] | tuple[Array, ...]) -> Array:
    if not kraus:
        raise ValueError("at least one Kraus operator is required")
    dim = np.asarray(kraus[0]).shape[0]
    num_qubits = _num_qubits_from_dim(dim)
    basis = pauli_basis(num_qubits)
    scale = 1.0 / dim
    out = np.zeros((len(basis), len(basis)), dtype=np.float64)
    for col, (_label_in, p_in) in enumerate(basis):
        evolved = np.zeros_like(p_in, dtype=np.complex128)
        for op in kraus:
            k = np.asarray(op, dtype=np.complex128)
            if k.shape != (dim, dim):
                raise ValueError("all Kraus operators must have the same square shape")
            evolved = evolved + k @ p_in @ k.conj().T
        for row, (_label_out, p_out) in enumerate(basis):
            out[row, col] = float(np.real(scale * np.trace(p_out @ evolved)))
    return _finite(out)


def channel_fingerprint(spec: MechanismSpec, *, paper_informed: bool = False) -> Array:
    channel = mechanism_channel(spec)
    kind = str(channel["kind"])
    if kind == "readout":
        features = _readout_fingerprint(np.asarray(channel["matrix"], dtype=np.float64))
    elif kind == "unitary":
        ptm = ptm_from_unitary(np.asarray(channel["unitary"], dtype=np.complex128))
        features = _ptm_fingerprint(ptm, num_qubits=int(spec.num_qubits))
    elif kind == "kraus":
        ptm = ptm_from_kraus(channel["kraus"])  # type: ignore[arg-type]
        features = _ptm_fingerprint(ptm, num_qubits=int(spec.num_qubits))
    else:
        raise ValueError(f"unknown channel kind {kind!r}")
    if paper_informed and spec.mechanism_id in RZZ_FAMILY_IDS and kind in {"unitary", "kraus"}:
        audit = rzz_ptm_block_audit(ptm)
        features = np.concatenate(
            [
                features,
                np.array(
                    [
                        float(audit["num_fixed_columns"]),
                        float(audit["num_two_entry_columns"]),
                        float(audit["max_column_support"]),
                    ],
                    dtype=np.float64,
                ),
            ]
        )
    elif paper_informed:
        features = np.concatenate([features, np.zeros(3, dtype=np.float64)])
    return _finite(features)


def probe_response_fingerprint(spec: MechanismSpec) -> Array:
    """Probe-specific local response summaries for oracle separability audits."""

    channel = mechanism_channel(spec)
    kind = str(channel["kind"])
    if kind == "readout":
        matrix = np.asarray(channel["matrix"], dtype=np.float64)
        rows = []
        for probs in _readout_probe_probabilities():
            reported = probs @ matrix
            rows.extend(_classical_response_stats(reported))
        return _fixed_length(rows, 32)

    if kind == "unitary":
        kraus = [np.asarray(channel["unitary"], dtype=np.complex128)]
    elif kind == "kraus":
        kraus = [np.asarray(item, dtype=np.complex128) for item in channel["kraus"]]  # type: ignore[index]
    else:
        raise ValueError(f"unknown channel kind {kind!r}")

    rows = []
    for rho in _probe_density_matrices(int(spec.num_qubits)):
        out = _apply_kraus(rho, kraus)
        rows.extend(_density_response_stats(out, int(spec.num_qubits)))
    return _fixed_length(rows, 32)


def rzz_type_feature_dict(ptm: Array) -> dict[str, float]:
    """Named RZZ Type 1/2/3/4-style PTM characterization features."""

    matrix = np.asarray(ptm, dtype=np.float64)
    audit = rzz_ptm_block_audit(matrix)
    num_columns = max(1, int(audit["num_columns"]))
    offdiag = matrix - np.diag(np.diag(matrix))
    support_over_two = [max(0, int(size) - 2) for size in audit["support_sizes"]]  # type: ignore[index]
    affine = matrix[1:, 0] if matrix.shape[0] > 1 else np.zeros(0, dtype=np.float64)
    first_row = matrix[0, 1:] if matrix.shape[0] > 1 else np.zeros(0, dtype=np.float64)
    return {
        "rzz_type1_commuting_fixed_fraction": float(int(audit["num_fixed_columns"]) / num_columns),
        "rzz_type2_two_entry_rotation_fraction": float(int(audit["num_two_entry_columns"]) / num_columns),
        "rzz_type3_nonclifford_rotation_strength": float(np.linalg.norm(offdiag) / max(1.0, np.sqrt(matrix.size))),
        "rzz_type4_hard_residual_leakage": float(sum(support_over_two) / num_columns + np.linalg.norm(affine) + np.linalg.norm(first_row)),
    }


def rzz_type_feature_vector(spec: MechanismSpec) -> Array:
    if spec.mechanism_id != "M1":
        return np.zeros(4, dtype=np.float64)
    channel = mechanism_channel(spec)
    if str(channel["kind"]) != "unitary":
        return np.zeros(4, dtype=np.float64)
    features = rzz_type_feature_dict(ptm_from_unitary(np.asarray(channel["unitary"], dtype=np.complex128)))
    return np.array([features[key] for key in _RZZ_TYPE_FEATURE_KEYS], dtype=np.float64)


def rzz_type_feature_names() -> list[str]:
    return list(_RZZ_TYPE_FEATURE_KEYS)


def rzz_ptm_block_audit(ptm: Array, *, atol: float = NUMERICAL_ZERO) -> dict[str, object]:
    matrix = np.asarray(ptm, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("ptm must be square")
    support_sizes = [int(np.count_nonzero(np.abs(matrix[:, col]) > float(atol))) for col in range(matrix.shape[1])]
    return {
        "num_columns": int(matrix.shape[1]),
        "num_fixed_columns": int(
            sum(size == 1 and abs(abs(matrix[col, col]) - 1.0) <= NUMERICAL_ZERO for col, size in enumerate(support_sizes))
        ),
        "num_two_entry_columns": int(sum(size == 2 for size in support_sizes)),
        "max_column_support": int(max(support_sizes) if support_sizes else 0),
        "support_sizes": support_sizes,
    }


def _ptm_fingerprint(ptm: Array, *, num_qubits: int) -> Array:
    matrix = np.asarray(ptm, dtype=np.float64)
    diag = np.diag(matrix)
    offdiag = matrix - np.diag(diag)
    affine_shift = matrix[1:, 0] if matrix.shape[0] > 1 else np.zeros(0, dtype=np.float64)
    first_row_error = matrix[0, 1:] if matrix.shape[0] > 1 else np.zeros(0, dtype=np.float64)
    singular = np.linalg.svd(matrix, compute_uv=False)
    return np.array(
        [
            float(num_qubits),
            float(matrix.shape[0]),
            float(np.trace(matrix)),
            float(np.mean(diag)),
            float(np.std(diag)),
            float(np.min(diag)),
            float(np.max(diag)),
            float(np.linalg.norm(offdiag)),
            float(np.linalg.norm(affine_shift)),
            float(np.linalg.norm(first_row_error)),
            float(np.linalg.norm(matrix.T @ matrix - np.eye(matrix.shape[1]))),
            float(np.mean(np.abs(matrix) > NUMERICAL_ZERO)),
            float(singular[0]) if singular.size else 0.0,
            float(singular[-1]) if singular.size else 0.0,
        ],
        dtype=np.float64,
    )


def _readout_fingerprint(matrix: Array) -> Array:
    row_sums = matrix.sum(axis=1)
    asymmetry = float(matrix[0, 1] - matrix[1, 0])
    base = np.array(
        [
            1.0,
            2.0,
            float(np.trace(matrix)),
            float(np.mean(np.diag(matrix))),
            float(np.std(np.diag(matrix))),
            float(np.min(np.diag(matrix))),
            float(np.max(np.diag(matrix))),
            float(np.linalg.norm(matrix - np.diag(np.diag(matrix)))),
            abs(asymmetry),
            float(np.linalg.norm(row_sums - 1.0)),
            float(np.linalg.norm(matrix.T @ matrix - np.eye(2))),
            float(np.mean(np.abs(matrix) > NUMERICAL_ZERO)),
            float(np.linalg.svd(matrix, compute_uv=False)[0]),
            float(np.linalg.svd(matrix, compute_uv=False)[-1]),
        ],
        dtype=np.float64,
    )
    return _finite(base)


_RZZ_TYPE_FEATURE_KEYS = (
    "rzz_type1_commuting_fixed_fraction",
    "rzz_type2_two_entry_rotation_fraction",
    "rzz_type3_nonclifford_rotation_strength",
    "rzz_type4_hard_residual_leakage",
)


def _probe_density_matrices(num_qubits: int) -> list[Array]:
    n = int(num_qubits)
    if n not in {1, 2}:
        raise ValueError("probe fingerprints currently support one- or two-qubit mechanisms")
    zero = np.array([1.0, 0.0], dtype=np.complex128)
    one = np.array([0.0, 1.0], dtype=np.complex128)
    plus = (zero + one) / np.sqrt(2.0)
    plus_i = (zero + 1j * one) / np.sqrt(2.0)
    if n == 1:
        states = [zero, one, plus, plus_i]
    else:
        states = [_kron_state([zero, zero]), _kron_state([one, one]), _kron_state([plus, plus]), _kron_state([plus_i, plus_i])]
    return [_pure_density(state) for state in states]


def _readout_probe_probabilities() -> list[Array]:
    return [
        np.array([1.0, 0.0], dtype=np.float64),
        np.array([0.0, 1.0], dtype=np.float64),
        np.array([0.5, 0.5], dtype=np.float64),
        np.array([0.5, 0.5], dtype=np.float64),
    ]


def _density_response_stats(rho: Array, num_qubits: int) -> list[float]:
    state = np.asarray(rho, dtype=np.complex128)
    purity = np.real(np.trace(state @ state))
    mean_x = _mean_single_pauli_expectation(state, int(num_qubits), "X")
    mean_y = _mean_single_pauli_expectation(state, int(num_qubits), "Y")
    mean_z = _mean_single_pauli_expectation(state, int(num_qubits), "Z")
    pair_xx = _pair_pauli_expectation(state, int(num_qubits), "X")
    pair_yy = _pair_pauli_expectation(state, int(num_qubits), "Y")
    pair_zz = _pair_pauli_expectation(state, int(num_qubits), "Z")
    return [
        float(np.real(np.trace(state))),
        float(np.real(purity)),
        mean_x,
        mean_y,
        mean_z,
        pair_xx,
        pair_yy,
        pair_zz,
    ]


def _classical_response_stats(probs: Array) -> list[float]:
    p = np.asarray(probs, dtype=np.float64)
    return [
        float(p.sum()),
        float(np.sum(p * p)),
        0.0,
        0.0,
        float(p[0] - p[1]),
        0.0,
        0.0,
        0.0,
    ]


def _apply_kraus(rho: Array, kraus: list[Array]) -> Array:
    out = np.zeros_like(rho, dtype=np.complex128)
    for op in kraus:
        out = out + op @ rho @ op.conj().T
    return 0.5 * (out + out.conj().T)


def _mean_single_pauli_expectation(rho: Array, num_qubits: int, label: str) -> float:
    values = []
    for q in range(int(num_qubits)):
        labels = ["I"] * int(num_qubits)
        labels[q] = label
        values.append(_expectation(rho, _pauli_operator(labels)))
    return float(sum(values) / len(values)) if values else 0.0


def _pair_pauli_expectation(rho: Array, num_qubits: int, label: str) -> float:
    if int(num_qubits) < 2:
        return 0.0
    labels = ["I"] * int(num_qubits)
    labels[0] = label
    labels[1] = label
    return _expectation(rho, _pauli_operator(labels))


def _expectation(rho: Array, operator: Array) -> float:
    return float(np.real(np.trace(np.asarray(operator, dtype=np.complex128) @ np.asarray(rho, dtype=np.complex128))))


def _pauli_operator(labels: list[str]) -> Array:
    one = {
        "I": np.eye(2, dtype=np.complex128),
        "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        "Y": np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128),
        "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
    }
    op = one[labels[0]]
    for label in labels[1:]:
        op = np.kron(op, one[label])
    return op


def _kron_state(states: list[Array]) -> Array:
    out = states[0]
    for state in states[1:]:
        out = np.kron(out, state)
    return out


def _pure_density(state: Array) -> Array:
    vector = np.asarray(state, dtype=np.complex128).reshape((-1, 1))
    return vector @ vector.conj().T


def _fixed_length(values: list[float], length: int) -> Array:
    out = np.zeros((int(length),), dtype=np.float64)
    clipped = np.asarray(values[: int(length)], dtype=np.float64)
    out[: clipped.shape[0]] = clipped
    return _finite(out)


def _num_qubits_from_dim(dim: int) -> int:
    n = math.log2(int(dim))
    if abs(n - round(n)) > NUMERICAL_ZERO:
        raise ValueError("channel dimension must be a power of two")
    return int(round(n))


def _finite(values: Array) -> Array:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)

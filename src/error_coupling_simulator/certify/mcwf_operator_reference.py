from __future__ import annotations

"""Certifier-local MCWF Hamiltonian and collapse operator references.

This module intentionally imports neither the MCWF execution implementation nor
its private family registries, embedding helpers, Stim lowering, or Torch matrix
logarithms.  The references are hand-typed NumPy matrices on the declared local
Hilbert spaces, so corrupting a production operator builder does not corrupt the
dense oracle in the same way.
"""

import math
from numbers import Real
from typing import Any

import numpy as np


_ONE_QUBIT_CONTROLS = frozenset(
    {
        "C_XYZ",
        "C_ZYX",
        "H",
        "H_XY",
        "H_XZ",
        "S",
        "S_DAG",
        "SQRT_X",
        "SQRT_X_DAG",
        "SQRT_Y",
        "SQRT_Y_DAG",
        "SQRT_Z",
        "SQRT_Z_DAG",
        "X",
        "Y",
        "Z",
    }
)
_TWO_QUBIT_CONTROLS = frozenset(
    {
        "CX",
        "CY",
        "CZ",
        "ISWAP",
        "ISWAP_DAG",
        "SQRT_XX",
        "SQRT_XX_DAG",
        "SQRT_YY",
        "SQRT_YY_DAG",
        "SQRT_ZZ",
        "SQRT_ZZ_DAG",
        "SWAP",
        "XCX",
        "XCY",
        "XCZ",
        "YCX",
        "YCY",
        "YCZ",
    }
)
_TWO_SITE_LEAKAGE_LEVELS = {
    "LEAK_EXCHANGE_11_02": ((1, 1), (0, 2)),
    "LEAK_MOBILITY_12_21": ((1, 2), (2, 1)),
    "LEAK_TRANSPORT_30_12": ((3, 0), (1, 2)),
    "LEAK_TRANSPORT_31_22": ((3, 1), (2, 2)),
}
_ONE_SITE_COHERENT = {
    "COH_RX": "X",
    "COH_RY": "Y",
    "COH_RZ": "Z",
}
_TWO_SITE_COHERENT = {
    "COH_XX": (("X", "X"),),
    "COH_YY": (("Y", "Y"),),
    "COH_ZX": (("Z", "X"),),
    "COH_XX_YY": (("X", "X"), ("Y", "Y")),
    "COH_CROSSTALK_ZZ": (("Z", "Z"),),
}
_ONE_SITE_COLLAPSE = frozenset(
    {"T1", "T1_UP", "T2", "RD", "LEAK_SEEP_21", "LEAK_HEAT_12"}
)


def _finite_coefficient(term: dict[str, Any]) -> float:
    raw = term.get("coefficient")
    if isinstance(raw, bool) or not isinstance(raw, Real):
        raise TypeError("MCWF operator coefficient must be a real number")
    coefficient = float(raw)
    if not math.isfinite(coefficient):
        raise ValueError("MCWF operator coefficient must be finite")
    return coefficient


def _normalized_support_and_dims(
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if any(type(q) is not int for q in support):
        raise TypeError("MCWF operator reference support entries must be exact integers")
    if any(type(d) is not int for d in local_dims):
        raise TypeError("MCWF operator reference local dimensions must be exact integers")
    normalized_support = tuple(support)
    normalized_dims = tuple(local_dims)
    if any(d < 2 for d in normalized_dims):
        raise ValueError("MCWF operator reference local dimensions must be >= 2")
    if len(set(normalized_support)) != len(normalized_support):
        raise ValueError("MCWF operator reference support must not repeat a site")
    if any(q < 0 or q >= len(normalized_dims) for q in normalized_support):
        raise ValueError("MCWF operator reference support is outside local_dims")
    return normalized_support, normalized_dims


def _require_arity(
    family: str,
    support: tuple[int, ...],
    arity: int,
) -> None:
    if len(support) != int(arity):
        raise ValueError(
            f"certifier-local {family} reference requires {arity}-site support, "
            f"got {support!r}"
        )


def _pauli(axis: str) -> np.ndarray:
    if axis == "I":
        return np.eye(2, dtype=np.complex128)
    if axis == "X":
        return np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    if axis == "Y":
        return np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
    if axis == "Z":
        return np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    raise ValueError(f"unsupported certifier-local Pauli axis {axis!r}")


def _pauli_tensor(left: str, right: str) -> np.ndarray:
    return np.kron(_pauli(left), _pauli(right))


def _embed_one_site_computational(
    operator: np.ndarray,
    *,
    local_dim: int,
) -> np.ndarray:
    dim = int(local_dim)
    if dim < 2:
        raise ValueError("one-site computational reference requires local_dim >= 2")
    out = np.zeros((dim, dim), dtype=np.complex128)
    out[:2, :2] = np.asarray(operator, dtype=np.complex128)
    return out


def _embed_two_site_computational(
    operator: np.ndarray,
    *,
    dims: tuple[int, int],
) -> np.ndarray:
    left_dim, right_dim = int(dims[0]), int(dims[1])
    if left_dim < 2 or right_dim < 2:
        raise ValueError("two-site computational reference requires local_dims >= 2")
    source = np.asarray(operator, dtype=np.complex128)
    if source.shape != (4, 4):
        raise ValueError("two-site computational reference must be 4x4")
    out = np.zeros(
        (left_dim * right_dim, left_dim * right_dim),
        dtype=np.complex128,
    )
    for left_in in (0, 1):
        for right_in in (0, 1):
            col = left_in * right_dim + right_in
            qcol = left_in * 2 + right_in
            for left_out in (0, 1):
                for right_out in (0, 1):
                    row = left_out * right_dim + right_out
                    qrow = left_out * 2 + right_out
                    out[row, col] = source[qrow, qcol]
    return out


def _one_qubit_control_generator(gate: str) -> np.ndarray:
    x = _pauli("X")
    y = _pauli("Y")
    z = _pauli("Z")
    if gate == "C_XYZ":
        return (x + y + z) / math.sqrt(3.0)
    if gate == "C_ZYX":
        return -(x + y + z) / math.sqrt(3.0)
    if gate in {"H", "H_XZ"}:
        return (x + z) / math.sqrt(2.0)
    if gate == "H_XY":
        return -(x + y) / math.sqrt(2.0)
    if gate in {"S", "SQRT_Z"}:
        return z
    if gate in {"S_DAG", "SQRT_Z_DAG"}:
        return -z
    if gate == "SQRT_X":
        return x
    if gate == "SQRT_X_DAG":
        return -x
    if gate == "SQRT_Y":
        return y
    if gate == "SQRT_Y_DAG":
        return -y
    if gate in {"X", "Y", "Z"}:
        return _pauli(gate)
    raise ValueError(f"unsupported certifier-local one-qubit control {gate!r}")


def _two_qubit_control_generator(gate: str) -> np.ndarray:
    ii = _pauli_tensor("I", "I")
    if gate == "CX":
        return 0.5 * (
            ii
            + _pauli_tensor("I", "X")
            + _pauli_tensor("Z", "I")
            - _pauli_tensor("Z", "X")
        )
    if gate == "CZ":
        return 0.25 * (
            ii
            - _pauli_tensor("I", "Z")
            - _pauli_tensor("Z", "I")
            + _pauli_tensor("Z", "Z")
        )
    if gate == "CY":
        return (math.pi / 4.0) * (
            _pauli_tensor("I", "Y")
            + _pauli_tensor("Z", "I")
            - _pauli_tensor("Z", "Y")
        )
    if gate in {"ISWAP", "ISWAP_DAG"}:
        sign = -1.0 if gate == "ISWAP" else 1.0
        return sign * (math.pi / 4.0) * (
            _pauli_tensor("X", "X") + _pauli_tensor("Y", "Y")
        )
    if gate.startswith("SQRT_"):
        dag = gate.endswith("_DAG")
        core = gate.removeprefix("SQRT_").removesuffix("_DAG")
        if core not in {"XX", "YY", "ZZ"}:
            raise ValueError(f"unsupported certifier-local two-qubit control {gate!r}")
        sign = -1.0 if dag else 1.0
        return sign * (math.pi / 4.0) * _pauli_tensor(core[0], core[1])
    if gate == "SWAP":
        return (math.pi / 4.0) * (
            _pauli_tensor("X", "X")
            + _pauli_tensor("Y", "Y")
            + _pauli_tensor("Z", "Z")
        )
    if len(gate) == 3 and gate[1] == "C" and gate[0] in {"X", "Y"}:
        control_axis = gate[0]
        target_axis = gate[2]
        if target_axis in {"X", "Y", "Z"}:
            return (math.pi / 4.0) * (
                _pauli_tensor("I", target_axis)
                + _pauli_tensor(control_axis, "I")
                - _pauli_tensor(control_axis, target_axis)
            )
    raise ValueError(f"unsupported certifier-local two-qubit control {gate!r}")


def reference_hamiltonian_matrix_for_term(
    term: dict[str, Any],
    *,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
) -> np.ndarray:
    """Return the independent hand-typed Hamiltonian for one sealed term."""

    if term.get("kind") != "hamiltonian":
        raise ValueError("Hamiltonian reference requires kind='hamiltonian'")
    support, local_dims = _normalized_support_and_dims(support, local_dims)
    raw_family = term.get("operator_family")
    if type(raw_family) is not str or not raw_family:
        raise TypeError("Hamiltonian reference family must be nonempty text")
    family = raw_family.upper()
    coefficient = _finite_coefficient(term)

    if family.startswith("CTRL_"):
        gate = family.removeprefix("CTRL_")
        if gate in _ONE_QUBIT_CONTROLS:
            _require_arity(family, support, 1)
            return coefficient * _embed_one_site_computational(
                _one_qubit_control_generator(gate),
                local_dim=local_dims[support[0]],
            )
        if gate in _TWO_QUBIT_CONTROLS:
            _require_arity(family, support, 2)
            return coefficient * _embed_two_site_computational(
                _two_qubit_control_generator(gate),
                dims=(local_dims[support[0]], local_dims[support[1]]),
            )
        raise ValueError(f"unsupported certifier-local control family {family!r}")

    if family in {"ZZ", "FSIM_PHASE"}:
        _require_arity(family, support, 2)
        d0, d1 = local_dims[support[0]], local_dims[support[1]]
        out = np.zeros((d0 * d1, d0 * d1), dtype=np.complex128)
        index = d1 + 1
        out[index, index] = coefficient
        return out

    if family == "LEAK_EXCHANGE_12":
        _require_arity(family, support, 1)
        dim = local_dims[support[0]]
        if dim < 3:
            raise ValueError("LEAK_EXCHANGE_12 reference requires local_dim >= 3")
        out = np.zeros((dim, dim), dtype=np.complex128)
        out[1, 2] = coefficient
        out[2, 1] = coefficient
        return out

    if family in _TWO_SITE_LEAKAGE_LEVELS:
        _require_arity(family, support, 2)
        d0, d1 = local_dims[support[0]], local_dims[support[1]]
        left, right = _TWO_SITE_LEAKAGE_LEVELS[family]
        for level0, level1 in (left, right):
            if level0 >= d0 or level1 >= d1:
                raise ValueError(
                    f"{family} reference levels are outside local_dims {(d0, d1)!r}"
                )
        left_index = left[0] * d1 + left[1]
        right_index = right[0] * d1 + right[1]
        out = np.zeros((d0 * d1, d0 * d1), dtype=np.complex128)
        out[left_index, right_index] = coefficient
        out[right_index, left_index] = coefficient
        return out

    if family in {
        "LEAK_COND_PHASE_LEFT2_RIGHTZ",
        "LEAK_COND_PHASE_LEFTZ_RIGHT2",
    }:
        _require_arity(family, support, 2)
        d0, d1 = local_dims[support[0]], local_dims[support[1]]
        out = np.zeros((d0 * d1, d0 * d1), dtype=np.complex128)
        if family == "LEAK_COND_PHASE_LEFT2_RIGHTZ":
            if d0 < 3:
                raise ValueError(f"{family} reference requires left local_dim >= 3")
            out[2 * d1, 2 * d1] = coefficient
            out[2 * d1 + 1, 2 * d1 + 1] = -coefficient
        else:
            if d1 < 3:
                raise ValueError(f"{family} reference requires right local_dim >= 3")
            out[2, 2] = coefficient
            out[d1 + 2, d1 + 2] = -coefficient
        return out

    if family in _ONE_SITE_COHERENT:
        _require_arity(family, support, 1)
        generator = 0.5 * coefficient * _pauli(_ONE_SITE_COHERENT[family])
        return _embed_one_site_computational(
            generator,
            local_dim=local_dims[support[0]],
        )

    if family in _TWO_SITE_COHERENT:
        _require_arity(family, support, 2)
        generator = np.zeros((4, 4), dtype=np.complex128)
        for left_axis, right_axis in _TWO_SITE_COHERENT[family]:
            generator = generator + _pauli_tensor(left_axis, right_axis)
        generator = (0.25 * coefficient) * generator
        return _embed_two_site_computational(
            generator,
            dims=(local_dims[support[0]], local_dims[support[1]]),
        )

    raise ValueError(f"unsupported certifier-local Hamiltonian family {family!r}")


def reference_collapse_operator_for_term(
    term: dict[str, Any],
    *,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
) -> np.ndarray:
    """Return the independent hand-typed collapse operator for one sealed term."""

    if term.get("kind") != "collapse":
        raise ValueError("collapse reference requires kind='collapse'")
    support, local_dims = _normalized_support_and_dims(support, local_dims)
    raw_family = term.get("operator_family")
    if type(raw_family) is not str or not raw_family:
        raise TypeError("collapse reference family must be nonempty text")
    family = raw_family.upper()
    coefficient = _finite_coefficient(term)

    one_site_transition = {
        "T1": (0, 1, 2),
        "T1_UP": (1, 0, 2),
        "T2": (1, 1, 2),
        "RD": (1, 1, 2),
        "LEAK_SEEP_21": (1, 2, 3),
        "LEAK_HEAT_12": (2, 1, 3),
    }.get(family)
    if one_site_transition is not None:
        _require_arity(family, support, 1)
        dim = local_dims[support[0]]
        row, column, minimum_dim = one_site_transition
        if dim < minimum_dim:
            raise ValueError(
                f"{family} reference requires local_dim >= {minimum_dim}"
            )
        out = np.zeros((dim, dim), dtype=np.complex128)
        out[row, column] = coefficient
        return out

    if family == "CORR_RELAX":
        _require_arity(family, support, 2)
        d0, d1 = local_dims[support[0]], local_dims[support[1]]
        lowering0 = np.zeros((d0, d0), dtype=np.complex128)
        lowering1 = np.zeros((d1, d1), dtype=np.complex128)
        lowering0[0, 1] = 1.0
        lowering1[0, 1] = 1.0
        return coefficient * (
            np.kron(lowering0, np.eye(d1, dtype=np.complex128))
            + np.kron(np.eye(d0, dtype=np.complex128), lowering1)
        )

    raise ValueError(f"unsupported certifier-local collapse family {family!r}")


def reference_structural_zero_mask_for_term(
    term: dict[str, Any],
    *,
    support: tuple[int, ...],
    local_dims: tuple[int, ...],
) -> np.ndarray:
    """Return matrix entries that the declared operator requires to be exact zero.

    Computational control and coherent generators may contain harmless eig/log
    round-off inside their computational block on the production side.  Their
    padding into leaked levels is nevertheless a structural zero.  Sparse
    leakage, phase, and collapse families are hand-constructed, so every zero in
    their reference matrix is structural.  A zero coefficient makes the entire
    operator structural zero for every family.
    """

    support, local_dims = _normalized_support_and_dims(support, local_dims)
    raw_family = term.get("operator_family")
    if type(raw_family) is not str or not raw_family:
        raise TypeError("MCWF structural-zero family must be nonempty text")
    family = raw_family.upper()
    coefficient = _finite_coefficient(term)
    kind = term.get("kind")
    if kind == "hamiltonian":
        reference = reference_hamiltonian_matrix_for_term(
            term,
            support=support,
            local_dims=local_dims,
        )
    elif kind == "collapse":
        reference = reference_collapse_operator_for_term(
            term,
            support=support,
            local_dims=local_dims,
        )
    else:
        raise ValueError("structural-zero reference requires Hamiltonian or collapse kind")

    if coefficient == 0.0:
        return np.ones(reference.shape, dtype=np.bool_)
    if kind != "hamiltonian" or not (
        family.startswith("CTRL_")
        or family in _ONE_SITE_COHERENT
        or family in _TWO_SITE_COHERENT
    ):
        return reference == 0.0

    if len(support) == 1:
        dim = local_dims[support[0]]
        computational = np.arange(dim) < 2
    elif len(support) == 2:
        d0, d1 = local_dims[support[0]], local_dims[support[1]]
        computational = np.asarray(
            [left < 2 and right < 2 for left in range(d0) for right in range(d1)],
            dtype=np.bool_,
        )
    else:
        raise ValueError(
            f"computational structural-zero reference requires one- or two-site support, "
            f"got {support!r}"
        )
    return ~(computational[:, None] & computational[None, :])


__all__ = [
    "reference_collapse_operator_for_term",
    "reference_hamiltonian_matrix_for_term",
    "reference_structural_zero_mask_for_term",
]

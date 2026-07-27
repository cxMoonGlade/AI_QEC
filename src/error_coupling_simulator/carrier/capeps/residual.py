from __future__ import annotations

"""Residual-state backends for the all-qubit CAPEPS prototype."""

import math
import numbers
from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

import numpy as np
import stim

from ...numerics import NUMERICAL_ZERO
from .algebra import (
    PAULI_MATRICES,
    apply_local_tableau_to_vector,
    apply_pauli_to_vector,
    require_targets,
    tableau_unitary_complex128,
)


CDTYPE = np.dtype(np.complex128)

class ResidualStateError(RuntimeError):
    """Raised when a residual update would create an invalid state."""


class ZeroProbabilityBranch(ResidualStateError):
    """Raised when a requested measurement outcome has exact zero probability."""

    def __init__(self, outcome: int, pauli: stim.PauliString) -> None:
        super().__init__(f"outcome {outcome} has exact zero probability for {pauli}")
        self.outcome = outcome
        self.pauli = str(pauli)
        self.probability = 0.0


@dataclass(frozen=True)
class ResidualUpdate:
    operation: str
    strategy: str
    term_count: int
    union_support_weight: int
    max_bond_before: int | None
    max_bond_after: int | None


PauliTerm = tuple[complex, stim.PauliString]


@runtime_checkable
class ResidualState(Protocol):
    @property
    def num_qubits(self) -> int: ...

    @property
    def backend_name(self) -> str: ...

    def copy(self) -> "ResidualState": ...

    def norm_squared(self) -> float: ...

    def apply_pauli_sum(self, terms: Sequence[PauliTerm]) -> ResidualUpdate: ...

    def apply_local_clifford(
        self,
        tableau: stim.Tableau,
        targets: Sequence[int],
    ) -> ResidualUpdate: ...

    def expectation_pauli(self, pauli: stim.PauliString) -> complex: ...

    def project_pauli(
        self,
        pauli: stim.PauliString,
        outcome: int,
    ) -> tuple[float, ResidualUpdate]: ...

    def state_vector(self, *, max_qubits: int = 12) -> np.ndarray: ...


def _require_num_qubits(num_qubits: int) -> int:
    if isinstance(num_qubits, bool) or not isinstance(num_qubits, int):
        raise TypeError("num_qubits must be an integer")
    if num_qubits <= 0:
        raise ValueError("num_qubits must be positive")
    return num_qubits


def _require_outcome(outcome: int) -> int:
    if isinstance(outcome, bool) or not isinstance(outcome, int):
        raise TypeError("measurement outcome must be integer 0 or 1")
    if outcome not in (0, 1):
        raise ValueError("measurement outcome must be 0 or 1")
    return outcome


def _copy_pauli(pauli: stim.PauliString, num_qubits: int) -> stim.PauliString:
    if not isinstance(pauli, stim.PauliString):
        raise TypeError("Pauli terms must use stim.PauliString")
    if len(pauli) != num_qubits:
        raise ValueError(
            f"Pauli width {len(pauli)} does not match residual width {num_qubits}"
        )
    return stim.PauliString(str(pauli))


def _require_coefficient(value: complex) -> complex:
    if isinstance(value, bool) or not isinstance(value, numbers.Complex):
        raise TypeError("Pauli coefficient must be a real or complex scalar")
    if not np.isfinite(value):
        raise ValueError("Pauli coefficient must be finite")
    return complex(value)


def _validated_terms(
    terms: Sequence[PauliTerm],
    num_qubits: int,
) -> tuple[PauliTerm, ...]:
    if not isinstance(terms, Sequence) or isinstance(terms, (str, bytes)):
        raise TypeError("terms must be a sequence of (coefficient, PauliString)")
    if not terms:
        raise ValueError("a coherent Pauli sum needs at least one term")
    out: list[PauliTerm] = []
    any_nonzero = False
    for item in terms:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError(
                "each Pauli term must be a (coefficient, PauliString) tuple"
            )
        coefficient = _require_coefficient(item[0])
        pauli = _copy_pauli(item[1], num_qubits)
        any_nonzero |= coefficient != 0.0
        out.append((coefficient, pauli))
    if not any_nonzero:
        raise ResidualStateError("the coherent Pauli sum is the zero operator")
    return tuple(out)


def _pauli_support(pauli: stim.PauliString) -> tuple[int, ...]:
    return tuple(index for index in range(len(pauli)) if int(pauli[index]) != 0)


def _union_support(terms: Sequence[PauliTerm]) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                qubit
                for coefficient, pauli in terms
                if coefficient != 0.0
                for qubit in _pauli_support(pauli)
            }
        )
    )


def _raw_norm_squared(vector: np.ndarray) -> float:
    raw = np.vdot(vector, vector)
    if not np.isfinite(raw):
        raise ResidualStateError("residual norm is non-finite")
    if raw.imag != 0.0:
        raise ResidualStateError("residual norm has a nonzero imaginary component")
    value = float(raw.real)
    if value < 0.0:
        raise ResidualStateError("residual norm is negative")
    return value


def _conditional_probability(
    after_norm: float,
    before_norm: float,
    *,
    backend: str,
) -> float:
    probability = after_norm / before_norm
    if not math.isfinite(probability) or probability <= 0.0:
        raise ResidualStateError(
            f"{backend} projection produced invalid probability {probability!r}"
        )
    if probability > 1.0:
        if probability - 1.0 > NUMERICAL_ZERO:
            raise ResidualStateError(
                f"{backend} projection produced invalid probability {probability!r}"
            )
        # Only absorb upper-bound contraction roundoff.  Do not floor small
        # positive branches: they can represent physically real amplitudes.
        return 1.0
    return probability


class DenseResidual:
    """Untruncated complex128 residual for small-register mechanics."""

    def __init__(self, vector: np.ndarray, *, num_qubits: int) -> None:
        self._num_qubits = _require_num_qubits(num_qubits)
        if not isinstance(vector, np.ndarray):
            raise TypeError("dense residual vector must be a numpy.ndarray")
        if vector.dtype != CDTYPE:
            raise TypeError(
                f"dense residual dtype must be complex128, got {vector.dtype}"
            )
        if vector.shape != (1 << self._num_qubits,):
            raise ValueError(
                f"dense residual shape must be {(1 << self._num_qubits,)}, "
                f"got {vector.shape}"
            )
        if not np.isfinite(vector).all():
            raise ValueError("dense residual vector must be finite")
        self._vector = np.array(vector, copy=True)
        if _raw_norm_squared(self._vector) == 0.0:
            raise ResidualStateError("dense residual must have positive norm")

    @classmethod
    def zero(cls, num_qubits: int) -> "DenseResidual":
        n = _require_num_qubits(num_qubits)
        vector = np.zeros(1 << n, dtype=CDTYPE)
        vector[0] = 1.0
        return cls(vector, num_qubits=n)

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def backend_name(self) -> str:
        return "numpy-dense-complex128"

    def copy(self) -> "DenseResidual":
        return DenseResidual(self._vector, num_qubits=self._num_qubits)

    def norm_squared(self) -> float:
        value = _raw_norm_squared(self._vector)
        if value == 0.0:
            raise ResidualStateError("dense residual has zero norm")
        return value

    def apply_pauli_sum(self, terms: Sequence[PauliTerm]) -> ResidualUpdate:
        checked = _validated_terms(terms, self._num_qubits)
        candidate = np.zeros_like(self._vector)
        for coefficient, pauli in checked:
            if coefficient == 0.0:
                continue
            candidate += coefficient * apply_pauli_to_vector(self._vector, pauli)
        if not np.isfinite(candidate).all():
            raise ResidualStateError("coherent dense update produced non-finite data")
        if _raw_norm_squared(candidate) == 0.0:
            raise ResidualStateError("coherent dense update produced the zero state")
        self._vector = candidate
        return ResidualUpdate(
            operation="coherent_pauli_sum",
            strategy="dense_exact",
            term_count=len(checked),
            union_support_weight=len(_union_support(checked)),
            max_bond_before=None,
            max_bond_after=None,
        )

    def apply_local_clifford(
        self,
        tableau: stim.Tableau,
        targets: Sequence[int],
    ) -> ResidualUpdate:
        if not isinstance(tableau, stim.Tableau):
            raise TypeError("tableau must be a stim.Tableau")
        checked = require_targets(
            targets,
            num_qubits=self._num_qubits,
            expected_count=len(tableau),
        )
        candidate = apply_local_tableau_to_vector(
            self._vector,
            tableau,
            checked,
            num_qubits=self._num_qubits,
        )
        if not np.isfinite(candidate).all():
            raise ResidualStateError("local Clifford produced non-finite data")
        if _raw_norm_squared(candidate) == 0.0:
            raise ResidualStateError("local Clifford produced the zero state")
        self._vector = candidate
        return ResidualUpdate(
            operation="clifford_refactor",
            strategy="dense_exact_local_clifford",
            term_count=1,
            union_support_weight=len(checked),
            max_bond_before=None,
            max_bond_after=None,
        )

    def expectation_pauli(self, pauli: stim.PauliString) -> complex:
        checked = _copy_pauli(pauli, self._num_qubits)
        acted = apply_pauli_to_vector(self._vector, checked)
        return complex(np.vdot(self._vector, acted) / self.norm_squared())

    def project_pauli(
        self,
        pauli: stim.PauliString,
        outcome: int,
    ) -> tuple[float, ResidualUpdate]:
        bit = _require_outcome(outcome)
        checked_pauli = _copy_pauli(pauli, self._num_qubits)
        before = self.norm_squared()
        acted = apply_pauli_to_vector(self._vector, checked_pauli)
        candidate = 0.5 * (self._vector + ((-1.0) ** bit) * acted)
        after = _raw_norm_squared(candidate)
        if after == 0.0:
            raise ZeroProbabilityBranch(bit, checked_pauli)
        probability = _conditional_probability(
            after,
            before,
            backend="dense",
        )
        candidate /= math.sqrt(after)
        self._vector = candidate
        return probability, ResidualUpdate(
            operation="pauli_projection",
            strategy="dense_exact",
            term_count=2,
            union_support_weight=len(_pauli_support(checked_pauli)),
            max_bond_before=None,
            max_bond_after=None,
        )

    def state_vector(self, *, max_qubits: int = 12) -> np.ndarray:
        if isinstance(max_qubits, bool) or not isinstance(max_qubits, int):
            raise TypeError("max_qubits must be an integer")
        if self._num_qubits > max_qubits:
            raise ResidualStateError(
                f"dense materialization guard {max_qubits} < {self._num_qubits}"
            )
        out = np.array(self._vector, copy=True)
        out.setflags(write=False)
        return out


class QuimbPepsResidual:
    """Finite OBC qubit PEPS with untruncated local or algebraic-sum updates.

    The qubit order is row-major and is also the dense tensor-axis order:
    qubit zero is the most-significant axis.
    """

    def __init__(
        self,
        peps,
        *,
        shape: tuple[int, int],
        contraction_optimize: str = "auto-hq",
        updates: Sequence[ResidualUpdate] = (),
    ) -> None:
        rows, columns = shape
        if (
            isinstance(rows, bool)
            or isinstance(columns, bool)
            or not isinstance(rows, int)
            or not isinstance(columns, int)
        ):
            raise TypeError("PEPS shape entries must be integers")
        if rows <= 0 or columns <= 0:
            raise ValueError("PEPS shape entries must be positive")
        self._shape = (rows, columns)
        self._sites = tuple(
            (row, column)
            for row in range(rows)
            for column in range(columns)
        )
        self._num_qubits = rows * columns
        self._peps = peps
        self._contraction_optimize = str(contraction_optimize)
        self._updates = list(updates)
        self._validate_structure()
        if self._norm_squared_for(self._peps) == 0.0:
            raise ResidualStateError("Quimb PEPS residual must have positive norm")

    @classmethod
    def product_state(
        cls,
        shape: tuple[int, int],
        local_vectors: Sequence[np.ndarray] | None = None,
        *,
        contraction_optimize: str = "auto-hq",
    ) -> "QuimbPepsResidual":
        import quimb.tensor as qtn

        rows, columns = shape
        if (
            isinstance(rows, bool)
            or isinstance(columns, bool)
            or not isinstance(rows, int)
            or not isinstance(columns, int)
        ):
            raise TypeError("PEPS shape entries must be integers")
        if rows <= 0 or columns <= 0:
            raise ValueError("PEPS shape entries must be positive")
        count = rows * columns
        if local_vectors is None:
            vectors = [
                np.asarray([1.0, 0.0], dtype=CDTYPE)
                for _ in range(count)
            ]
        else:
            if not isinstance(local_vectors, Sequence):
                raise TypeError("local_vectors must be a sequence")
            if len(local_vectors) != count:
                raise ValueError(
                    f"expected {count} local vectors, got {len(local_vectors)}"
                )
            vectors = []
            for index, vector in enumerate(local_vectors):
                if not isinstance(vector, np.ndarray):
                    raise TypeError(f"local vector {index} is not a numpy.ndarray")
                if vector.dtype != CDTYPE:
                    raise TypeError(
                        f"local vector {index} dtype must be complex128, "
                        f"got {vector.dtype}"
                    )
                if vector.shape != (2,):
                    raise ValueError(f"local vector {index} must have shape (2,)")
                if not np.isfinite(vector).all():
                    raise ValueError(f"local vector {index} must be finite")
                norm = _raw_norm_squared(vector)
                if abs(norm - 1.0) > NUMERICAL_ZERO:
                    raise ValueError(
                        f"local vector {index} is not normalized: norm^2={norm}"
                    )
                # Quimb product_state otherwise retains shared input arrays.
                vectors.append(np.array(vector, copy=True))
        sites = tuple(
            (row, column)
            for row in range(rows)
            for column in range(columns)
        )
        site_map = {
            site: vectors[index].copy()
            for index, site in enumerate(sites)
        }
        peps = qtn.PEPS.product_state(site_map, cyclic=False)
        return cls(
            peps,
            shape=shape,
            contraction_optimize=contraction_optimize,
        )

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def backend_name(self) -> str:
        return "quimb-peps-numpy-complex128-untruncated-algebra"

    @property
    def shape(self) -> tuple[int, int]:
        return self._shape

    @property
    def updates(self) -> tuple[ResidualUpdate, ...]:
        return tuple(self._updates)

    @property
    def max_bond_dimension(self) -> int:
        value = self._peps.max_bond()
        return 1 if value is None else int(value)

    def _validate_structure(self) -> None:
        if getattr(self._peps, "Lx", None) != self._shape[0]:
            raise ValueError("Quimb PEPS row count does not match shape")
        if getattr(self._peps, "Ly", None) != self._shape[1]:
            raise ValueError("Quimb PEPS column count does not match shape")
        for site in self._sites:
            physical = self._peps.site_ind(*site)
            if int(self._peps.ind_size(physical)) != 2:
                raise ValueError(f"PEPS site {site} does not have physical dimension 2")
            tensor = self._peps[site]
            data = np.asarray(tensor.data)
            if data.dtype != CDTYPE:
                raise TypeError(
                    f"PEPS site {site} dtype must be complex128, got {data.dtype}"
                )
            if not np.isfinite(data).all():
                raise ValueError(f"PEPS site {site} contains non-finite data")

    def _norm_squared_for(self, peps) -> float:
        raw = complex(
            peps.norm(
                squared=True,
                optimize=self._contraction_optimize,
            )
        )
        if not math.isfinite(raw.real) or not math.isfinite(raw.imag):
            raise ResidualStateError("Quimb PEPS norm is non-finite")
        scale = max(1.0, abs(raw.real))
        if abs(raw.imag) > NUMERICAL_ZERO * scale:
            raise ResidualStateError(
                f"Quimb PEPS norm has imaginary residual {raw.imag}"
            )
        if raw.real < 0.0:
            raise ResidualStateError("Quimb PEPS norm is negative")
        return float(raw.real)

    def copy(self) -> "QuimbPepsResidual":
        return QuimbPepsResidual(
            self._peps.copy(deep=True),
            shape=self._shape,
            contraction_optimize=self._contraction_optimize,
            updates=self._updates,
        )

    def norm_squared(self) -> float:
        value = self._norm_squared_for(self._peps)
        if value == 0.0:
            raise ResidualStateError("Quimb PEPS residual has zero norm")
        return value

    def _apply_pauli_body(self, peps, pauli: stim.PauliString) -> None:
        for qubit, site in enumerate(self._sites):
            code = int(pauli[qubit])
            if code:
                peps.gate_(
                    PAULI_MATRICES[code],
                    where=site,
                    contract=True,
                )
        sign = complex(pauli.sign)
        if sign != 1.0:
            peps.multiply_(sign)

    def _build_pauli_sum(
        self,
        checked: tuple[PauliTerm, ...],
    ):
        support = _union_support(checked)
        if len(support) <= 1:
            site_qubit = support[0] if support else 0
            operator = np.zeros((2, 2), dtype=CDTYPE)
            for coefficient, pauli in checked:
                if coefficient == 0.0:
                    continue
                code = int(pauli[site_qubit])
                operator += (
                    coefficient
                    * complex(pauli.sign)
                    * PAULI_MATRICES[code]
                )
            candidate = self._peps.copy(deep=True)
            candidate.gate_(
                operator,
                where=self._sites[site_qubit],
                contract=True,
            )
            return candidate, "one_site_untruncated_gate", support

        candidate = None
        for coefficient, pauli in checked:
            if coefficient == 0.0:
                continue
            term_peps = self._peps.copy(deep=True)
            self._apply_pauli_body(term_peps, pauli)
            if coefficient != 1.0:
                term_peps.multiply_(coefficient)
            if candidate is None:
                candidate = term_peps
            else:
                # Quimb's PEPS algebraic sum is a virtual direct product on
                # matching edges.  No SVD or cutoff is invoked.
                candidate.add_PEPS_(term_peps)
        if candidate is None:
            raise ResidualStateError("the coherent Pauli sum is the zero operator")
        return candidate, "global_direct_sum_untruncated", support

    def apply_pauli_sum(self, terms: Sequence[PauliTerm]) -> ResidualUpdate:
        checked = _validated_terms(terms, self._num_qubits)
        before_bond = self.max_bond_dimension
        candidate, strategy, support = self._build_pauli_sum(checked)
        if self._norm_squared_for(candidate) == 0.0:
            raise ResidualStateError("coherent PEPS update produced the zero state")
        self._peps = candidate
        update = ResidualUpdate(
            operation="coherent_pauli_sum",
            strategy=strategy,
            term_count=len(checked),
            union_support_weight=len(support),
            max_bond_before=before_bond,
            max_bond_after=self.max_bond_dimension,
        )
        self._updates.append(update)
        return update

    def apply_local_clifford(
        self,
        tableau: stim.Tableau,
        targets: Sequence[int],
    ) -> ResidualUpdate:
        if not isinstance(tableau, stim.Tableau):
            raise TypeError("tableau must be a stim.Tableau")
        checked = require_targets(
            targets,
            num_qubits=self._num_qubits,
            expected_count=len(tableau),
        )
        if len(checked) not in (1, 2):
            raise ValueError(
                "Quimb PEPS Clifford refactor supports one or two sites"
            )
        sites = tuple(self._sites[target] for target in checked)
        if len(sites) == 2:
            distance = abs(sites[0][0] - sites[1][0]) + abs(
                sites[0][1] - sites[1][1]
            )
            if distance != 1:
                raise ValueError(
                    "two-site PEPS Clifford refactor requires adjacent sites"
                )
        unitary = tableau_unitary_complex128(tableau)
        before_bond = self.max_bond_dimension
        candidate = self._peps.copy(deep=True)
        if len(sites) == 1:
            candidate.gate_(
                unitary,
                where=sites[0],
                contract=True,
            )
            strategy = "one_site_clifford_untruncated"
        else:
            candidate.gate_(
                unitary,
                where=sites,
                contract="split",
                cutoff=0.0,
                max_bond=None,
                method="svd",
                absorb="both",
            )
            strategy = "two_site_clifford_split_untruncated"
        if self._norm_squared_for(candidate) == 0.0:
            raise ResidualStateError("local Clifford produced the zero PEPS")
        for site in self._sites:
            data = np.asarray(candidate[site].data)
            if data.dtype != CDTYPE or not np.isfinite(data).all():
                raise ResidualStateError(
                    f"local Clifford produced invalid PEPS tensor at {site}"
                )
        self._peps = candidate
        update = ResidualUpdate(
            operation="clifford_refactor",
            strategy=strategy,
            term_count=1,
            union_support_weight=len(checked),
            max_bond_before=before_bond,
            max_bond_after=self.max_bond_dimension,
        )
        self._updates.append(update)
        return update

    def expectation_pauli(self, pauli: stim.PauliString) -> complex:
        checked = _copy_pauli(pauli, self._num_qubits)
        acted = self._peps.copy(deep=True)
        self._apply_pauli_body(acted, checked)
        # Quimb conjugates the argument of ``overlap``.  Therefore
        # acted.overlap(original) is <original|acted>.
        numerator = complex(
            acted.overlap(
                self._peps,
                optimize=self._contraction_optimize,
            )
        )
        if not math.isfinite(numerator.real) or not math.isfinite(
            numerator.imag
        ):
            raise ResidualStateError("Pauli expectation is non-finite")
        return numerator / self.norm_squared()

    def project_pauli(
        self,
        pauli: stim.PauliString,
        outcome: int,
    ) -> tuple[float, ResidualUpdate]:
        bit = _require_outcome(outcome)
        checked_pauli = _copy_pauli(pauli, self._num_qubits)
        before_norm = self.norm_squared()
        before_bond = self.max_bond_dimension
        identity = stim.PauliString(self._num_qubits)
        terms: tuple[PauliTerm, ...] = (
            (0.5, identity),
            (0.5 * ((-1.0) ** bit), checked_pauli),
        )
        candidate, strategy, support = self._build_pauli_sum(terms)
        after_norm = self._norm_squared_for(candidate)
        if after_norm == 0.0:
            raise ZeroProbabilityBranch(bit, checked_pauli)
        probability = _conditional_probability(
            after_norm,
            before_norm,
            backend="PEPS",
        )
        candidate.multiply_(1.0 / math.sqrt(after_norm))
        self._peps = candidate
        update = ResidualUpdate(
            operation="pauli_projection",
            strategy=strategy,
            term_count=2,
            union_support_weight=len(support),
            max_bond_before=before_bond,
            max_bond_after=self.max_bond_dimension,
        )
        self._updates.append(update)
        return probability, update

    def state_vector(self, *, max_qubits: int = 12) -> np.ndarray:
        if isinstance(max_qubits, bool) or not isinstance(max_qubits, int):
            raise TypeError("max_qubits must be an integer")
        if self._num_qubits > max_qubits:
            raise ResidualStateError(
                f"dense materialization guard {max_qubits} < {self._num_qubits}"
            )
        physical = tuple(self._peps.site_ind(*site) for site in self._sites)
        raw = self._peps.to_dense(
            physical,
            to_qarray=False,
            to_ket=False,
            optimize=self._contraction_optimize,
        )
        vector = np.asarray(raw).reshape(-1)
        if vector.dtype != CDTYPE:
            raise TypeError(
                f"materialized PEPS dtype must be complex128, got {vector.dtype}"
            )
        if not np.isfinite(vector).all():
            raise ResidualStateError("materialized PEPS vector is non-finite")
        out = np.array(vector, copy=True)
        out.setflags(write=False)
        return out

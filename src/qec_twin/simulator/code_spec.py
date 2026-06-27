from __future__ import annotations

"""Syndrome-code specifications for the simulator frontend.

`CodeSpec` is a frontend construction contract. It names data/ancilla qubits,
commuting stabilizer checks, final logical observables, and the number of
measurement rounds. It deliberately does not own sampling, noise, decoding, or
analog carrier evolution.
"""

from dataclasses import dataclass, field
import re
from typing import Iterable

from qec_twin.simulator.metadata_guard import validate_public_metadata
from qec_twin.simulator.operation import OperationSet, as_operation_set, default_memory_operations

_PAULI_BASES = {"X", "Y", "Z"}
_RECORD_TOKEN_RE = re.compile(r"[A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class CodeQubit:
    """Physical qubit declared by a syndrome-code spec."""

    index: int
    role: str
    coords: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "index", int(self.index))
        object.__setattr__(self, "role", str(self.role))
        object.__setattr__(self, "coords", tuple(float(c) for c in self.coords))
        if self.index < 0:
            raise ValueError(f"qubit index must be non-negative, got {self.index}")
        if self.role not in {"data", "ancilla"}:
            raise ValueError(f"qubit role must be 'data' or 'ancilla', got {self.role!r}")

    def to_manifest(self) -> dict:
        return {"index": self.index, "role": self.role, "coords": list(self.coords)}


@dataclass(frozen=True)
class PauliTerm:
    """One Pauli factor in a stabilizer or logical observable."""

    qubit: int
    basis: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "qubit", int(self.qubit))
        object.__setattr__(self, "basis", str(self.basis).upper())
        if self.qubit < 0:
            raise ValueError(f"PauliTerm qubit must be non-negative, got {self.qubit}")
        if self.basis not in _PAULI_BASES:
            raise ValueError(f"unsupported Pauli basis {self.basis!r}")

    def to_manifest(self) -> dict:
        return {"qubit": self.qubit, "basis": self.basis}


@dataclass(frozen=True)
class StabilizerCheck:
    """One commuting syndrome check measured by a declared ancilla."""

    name: str
    ancilla: int
    terms: tuple[PauliTerm, ...]
    coords: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "ancilla", int(self.ancilla))
        object.__setattr__(self, "terms", _as_terms(self.terms))
        object.__setattr__(self, "coords", tuple(float(c) for c in self.coords))
        _require_record_token("stabilizer check name", self.name)
        if self.ancilla < 0:
            raise ValueError(f"stabilizer ancilla must be non-negative, got {self.ancilla}")
        if not self.terms:
            raise ValueError(f"stabilizer check {self.name!r} must have at least one term")
        _require_unique_term_qubits(self.name, self.terms)

    def to_manifest(self) -> dict:
        return {
            "name": self.name,
            "ancilla": self.ancilla,
            "coords": list(self.coords),
            "terms": [t.to_manifest() for t in self.terms],
        }


@dataclass(frozen=True)
class LogicalObservableSpec:
    """Final logical observable measured as an XOR of final Pauli terms."""

    name: str
    terms: tuple[PauliTerm, ...]
    index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "terms", _as_terms(self.terms))
        object.__setattr__(self, "index", int(self.index))
        _require_record_token("logical observable name", self.name)
        if not self.terms:
            raise ValueError(f"logical observable {self.name!r} must have at least one term")
        if self.index < 0:
            raise ValueError(f"logical observable index must be non-negative, got {self.index}")
        _require_unique_term_qubits(self.name, self.terms)

    def to_manifest(self) -> dict:
        return {
            "name": self.name,
            "index": self.index,
            "terms": [t.to_manifest() for t in self.terms],
        }


@dataclass(frozen=True)
class CodeSpec:
    """Generic syndrome-code input to the frontend compiler."""

    name: str
    num_qubits: int
    data_qubits: tuple[CodeQubit, ...]
    ancilla_qubits: tuple[CodeQubit, ...]
    checks: tuple[StabilizerCheck, ...]
    logical_observables: tuple[LogicalObservableSpec, ...]
    rounds: int
    metadata: dict = field(default_factory=dict)
    operations: tuple = field(default_factory=default_memory_operations)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "num_qubits", int(self.num_qubits))
        object.__setattr__(self, "data_qubits", tuple(self.data_qubits))
        object.__setattr__(self, "ancilla_qubits", tuple(self.ancilla_qubits))
        object.__setattr__(self, "checks", tuple(self.checks))
        object.__setattr__(self, "logical_observables", tuple(self.logical_observables))
        object.__setattr__(self, "rounds", int(self.rounds))
        operation_set = as_operation_set(self.operations)
        object.__setattr__(self, "operations", operation_set.operations)
        object.__setattr__(
            self,
            "metadata",
            validate_public_metadata(self.metadata, label="CodeSpec.metadata"),
        )
        if not self.name:
            raise ValueError("CodeSpec name must be non-empty")
        if self.num_qubits <= 0:
            raise ValueError("num_qubits must be positive")
        if self.rounds < 2:
            raise ValueError("rounds must be at least 2 so detector deltas are defined")
        if not self.data_qubits:
            raise ValueError("CodeSpec must declare at least one data qubit")
        if not self.ancilla_qubits:
            raise ValueError("CodeSpec must declare at least one ancilla qubit")
        if not self.checks:
            raise ValueError("CodeSpec must declare at least one stabilizer check")
        if not self.logical_observables:
            raise ValueError("CodeSpec must declare at least one logical observable")
        self._validate_qubits()
        self._validate_checks_and_logicals()

    def to_manifest(self) -> dict:
        return {
            "name": self.name,
            "num_qubits": self.num_qubits,
            "rounds": self.rounds,
            "metadata": dict(self.metadata),
            "operations": self.operation_set.to_manifest(),
            "data_qubits": [q.to_manifest() for q in self.data_qubits],
            "ancilla_qubits": [q.to_manifest() for q in self.ancilla_qubits],
            "checks": [c.to_manifest() for c in self.checks],
            "logical_observables": [o.to_manifest() for o in self.logical_observables],
        }

    @property
    def data_indices(self) -> tuple[int, ...]:
        return tuple(q.index for q in self.data_qubits)

    @property
    def ancilla_indices(self) -> tuple[int, ...]:
        return tuple(q.index for q in self.ancilla_qubits)

    @property
    def operation_set(self) -> OperationSet:
        return OperationSet(tuple(self.operations))

    def _validate_qubits(self) -> None:
        qubits = self.data_qubits + self.ancilla_qubits
        seen: set[int] = set()
        for q in qubits:
            if q.index >= self.num_qubits:
                raise ValueError(f"qubit {q.index} outside [0, {self.num_qubits})")
            if q.index in seen:
                raise ValueError(f"duplicate qubit index {q.index}")
            seen.add(q.index)
        for q in self.data_qubits:
            if q.role != "data":
                raise ValueError(f"data_qubits entry {q.index} has role {q.role!r}")
        for q in self.ancilla_qubits:
            if q.role != "ancilla":
                raise ValueError(f"ancilla_qubits entry {q.index} has role {q.role!r}")

    def _validate_checks_and_logicals(self) -> None:
        data = set(self.data_indices)
        ancilla = set(self.ancilla_indices)
        check_names: set[str] = set()
        for check in self.checks:
            if check.name in check_names:
                raise ValueError(f"duplicate stabilizer check name {check.name!r}")
            check_names.add(check.name)
            if check.ancilla not in ancilla:
                raise ValueError(
                    f"check {check.name!r} ancilla {check.ancilla} is not an ancilla qubit"
                )
            for term in check.terms:
                if term.qubit not in data:
                    raise ValueError(
                        f"check {check.name!r} term {term.qubit} is not a data qubit"
                    )
        for a, b in _pairs(self.checks):
            if not commute(a.terms, b.terms):
                raise ValueError(f"stabilizer checks {a.name!r} and {b.name!r} do not commute")

        check_vectors = [_pauli_vector(check.terms, self.num_qubits) for check in self.checks]
        logical_names: set[str] = set()
        logical_indices: set[int] = set()
        for observable in self.logical_observables:
            if observable.name in logical_names:
                raise ValueError(f"duplicate logical observable name {observable.name!r}")
            logical_names.add(observable.name)
            if observable.index in logical_indices:
                raise ValueError(f"duplicate logical observable index {observable.index}")
            logical_indices.add(observable.index)
            for term in observable.terms:
                if term.qubit not in data:
                    raise ValueError(
                        f"logical {observable.name!r} term {term.qubit} is not a data qubit"
                    )
            for check in self.checks:
                if not commute(observable.terms, check.terms):
                    raise ValueError(
                        f"logical {observable.name!r} does not commute with check {check.name!r}"
                    )
            logical_vector = _pauli_vector(observable.terms, self.num_qubits)
            if _pauli_product_in_stabilizer_span(logical_vector, check_vectors):
                raise ValueError(
                    f"logical {observable.name!r} is in the stabilizer span; "
                    "use DetectorDef/stabilizer records for check products, not LogicalObservableSpec"
                )


def commute(a_terms: Iterable[PauliTerm], b_terms: Iterable[PauliTerm]) -> bool:
    """Return True iff the two Pauli products commute."""

    a = {t.qubit: t.basis for t in a_terms}
    b = {t.qubit: t.basis for t in b_terms}
    anti = 0
    for qubit in set(a) & set(b):
        if a[qubit] != b[qubit]:
            anti += 1
    return anti % 2 == 0


def _as_terms(terms: Iterable[PauliTerm]) -> tuple[PauliTerm, ...]:
    out = tuple(terms)
    if not all(isinstance(t, PauliTerm) for t in out):
        raise TypeError("terms must be PauliTerm instances")
    return out


def _require_unique_term_qubits(name: str, terms: tuple[PauliTerm, ...]) -> None:
    seen: set[int] = set()
    for term in terms:
        if term.qubit in seen:
            raise ValueError(f"{name!r} has duplicate term qubit {term.qubit}")
        seen.add(term.qubit)


def _require_record_token(label: str, value: str) -> None:
    if not value:
        raise ValueError(f"{label} must be non-empty")
    if not _RECORD_TOKEN_RE.fullmatch(value):
        raise ValueError(
            f"{label} {value!r} must match {_RECORD_TOKEN_RE.pattern!r}; "
            "avoid ':' and whitespace so generated record keys stay parseable"
        )


def _pairs(items):
    items = tuple(items)
    for i, left in enumerate(items):
        for right in items[i + 1:]:
            yield left, right


def _pauli_vector(terms: Iterable[PauliTerm], num_qubits: int) -> list[int]:
    x = [0] * int(num_qubits)
    z = [0] * int(num_qubits)
    for term in terms:
        if term.basis in {"X", "Y"}:
            x[term.qubit] ^= 1
        if term.basis in {"Z", "Y"}:
            z[term.qubit] ^= 1
    return x + z


def _pauli_product_in_stabilizer_span(vector: list[int], rows: list[list[int]]) -> bool:
    return _binary_row_rank(rows + [vector]) == _binary_row_rank(rows)


def _binary_row_rank(rows: list[list[int]]) -> int:
    reduced = [list(row) for row in rows if any(row)]
    if not reduced:
        return 0
    rank = 0
    width = len(reduced[0])
    for col in range(width):
        pivot = None
        for i in range(rank, len(reduced)):
            if reduced[i][col]:
                pivot = i
                break
        if pivot is None:
            continue
        reduced[rank], reduced[pivot] = reduced[pivot], reduced[rank]
        for i in range(len(reduced)):
            if i != rank and reduced[i][col]:
                reduced[i] = [a ^ b for a, b in zip(reduced[i], reduced[rank])]
        rank += 1
    return rank

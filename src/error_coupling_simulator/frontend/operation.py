from __future__ import annotations

"""Named frontend operations exposed by code-level circuit constructors.

Operations are a small construction vocabulary, not a noise or mechanism
model. They let a `CodeSpec` declare which frontend procedures it supports
before a schedule tries to compile it.
"""

from dataclasses import dataclass, field

from .metadata_guard import validate_public_metadata

_ALIASES = {
    "prepp": "prep_plus",
    "prepm": "prep_minus",
}

ALLOWED_OPERATION_NAMES = frozenset(
    {
        "prep0",
        "prep1",
        "prep_plus",
        "prep_minus",
        "stabilizer_round",
        "final_readout",
    }
)


@dataclass(frozen=True)
class OperationSpec:
    """One named code-construction operation supported by a `CodeSpec`."""

    name: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        name = canonical_operation_name(self.name)
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "metadata",
            validate_public_metadata(self.metadata, label=f"OperationSpec({name}).metadata"),
        )

    def to_manifest(self) -> dict:
        return {"name": self.name, "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class OperationSet:
    """Validated collection of frontend construction operations."""

    operations: tuple[OperationSpec, ...]

    def __post_init__(self) -> None:
        operations = tuple(self.operations)
        if not operations:
            raise ValueError("OperationSet must contain at least one operation")
        names = [operation.name for operation in operations]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"duplicate frontend operations {duplicates}")
        object.__setattr__(self, "operations", operations)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(operation.name for operation in self.operations)

    def require(self, required: tuple[str, ...] | list[str] | set[str], *, label: str) -> None:
        missing = sorted(set(canonical_operation_name(name) for name in required) - set(self.names))
        if missing:
            raise ValueError(
                f"{label} requires frontend operation(s) {missing}, "
                f"but CodeSpec declares {list(self.names)}"
            )

    def to_manifest(self) -> list[dict]:
        return [operation.to_manifest() for operation in self.operations]


def canonical_operation_name(name: str) -> str:
    out = str(name).strip().lower()
    out = _ALIASES.get(out, out)
    if out not in ALLOWED_OPERATION_NAMES:
        raise ValueError(
            f"unsupported frontend operation {name!r}; "
            f"allowed={sorted(ALLOWED_OPERATION_NAMES)}"
        )
    return out


def default_memory_operations() -> tuple[OperationSpec, ...]:
    """Operations required by the current repeated-memory schedule."""

    return (
        OperationSpec("prep0"),
        OperationSpec("stabilizer_round"),
        OperationSpec("final_readout"),
    )


def as_operation_set(operations) -> OperationSet:
    if isinstance(operations, OperationSet):
        return operations
    return OperationSet(
        tuple(operation if isinstance(operation, OperationSpec) else OperationSpec(operation) for operation in operations)
    )

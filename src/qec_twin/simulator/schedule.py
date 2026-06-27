from __future__ import annotations

"""Frontend schedule templates for compiling code specs into record circuits."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qec_twin.simulator.operation import canonical_operation_name

if TYPE_CHECKING:  # pragma: no cover
    from qec_twin.simulator.code_spec import CodeSpec


_REPEATED_MEMORY_REQUIRED_OPERATIONS = ("prep0", "stabilizer_round", "final_readout")
_REPEATED_MEMORY_DETECTOR_POLICY = "round_delta_and_final_closure"
_REPEATED_MEMORY_FINAL_READOUT_POLICY = "check_and_logical_compatible_basis"


@dataclass(frozen=True)
class ScheduleTemplate:
    """Named frontend schedule contract.

    The template validates code-level capabilities and declares record-layout
    policy. It does not define a physical noise model.
    """

    name: str
    required_operations: tuple[str, ...]
    detector_policy: str
    final_readout_policy: str

    def __post_init__(self) -> None:
        name = canonical_schedule_name(self.name)
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "required_operations",
            tuple(canonical_operation_name(op) for op in self.required_operations),
        )
        if not self.required_operations:
            raise ValueError("ScheduleTemplate requires at least one operation")
        if not self.detector_policy:
            raise ValueError("ScheduleTemplate detector_policy must be non-empty")
        if not self.final_readout_policy:
            raise ValueError("ScheduleTemplate final_readout_policy must be non-empty")
        if self.name == "repeated_memory_v1":
            expected = repeated_memory_schedule_manifest()
            actual = self.to_manifest()
            if actual != expected:
                raise ValueError(
                    "schedule_template 'repeated_memory_v1' has fixed compiler semantics; "
                    f"expected {expected}, got {actual}"
                )

    def validate_for(self, spec: "CodeSpec") -> None:
        spec.operation_set.require(
            self.required_operations,
            label=f"schedule_template {self.name!r}",
        )

    def to_manifest(self) -> dict:
        return {
            "name": self.name,
            "required_operations": list(self.required_operations),
            "detector_policy": self.detector_policy,
            "final_readout_policy": self.final_readout_policy,
        }


def repeated_memory_schedule() -> ScheduleTemplate:
    """Return the current repeated ancilla-syndrome memory schedule."""

    return ScheduleTemplate(
        name="repeated_memory_v1",
        required_operations=_REPEATED_MEMORY_REQUIRED_OPERATIONS,
        detector_policy=_REPEATED_MEMORY_DETECTOR_POLICY,
        final_readout_policy=_REPEATED_MEMORY_FINAL_READOUT_POLICY,
    )


def repeated_memory_schedule_manifest() -> dict:
    return {
        "name": "repeated_memory_v1",
        "required_operations": list(_REPEATED_MEMORY_REQUIRED_OPERATIONS),
        "detector_policy": _REPEATED_MEMORY_DETECTOR_POLICY,
        "final_readout_policy": _REPEATED_MEMORY_FINAL_READOUT_POLICY,
    }


def canonical_schedule_name(name: str) -> str:
    out = str(name).strip()
    if out != "repeated_memory_v1":
        raise ValueError(
            f"unsupported schedule_template {name!r}; supported=['repeated_memory_v1']"
        )
    return out


def resolve_schedule_template(schedule_template: str | ScheduleTemplate) -> ScheduleTemplate:
    if isinstance(schedule_template, ScheduleTemplate):
        return schedule_template
    name = canonical_schedule_name(schedule_template)
    if name == "repeated_memory_v1":
        return repeated_memory_schedule()
    raise AssertionError(f"unhandled schedule_template {schedule_template!r}")

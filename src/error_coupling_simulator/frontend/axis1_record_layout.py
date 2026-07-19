from __future__ import annotations

"""Immutable Axis-1 measurement-Record layout parsed from a sealed schedule.

The layout is a public-schedule fact, not an execution result.  Backends may
fill outcome bits, but they must not discover keys, targets, reset masks, or
XOR columns from a sampled trajectory.
"""

from dataclasses import dataclass
from typing import Any, Sequence

from .analog_schedule import SubstepSchedule, require_compiler_schedule_seal


AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA = (
    "error_coupling_simulator.frontend.axis1_schedule_record_layout.v1"
)


@dataclass(frozen=True, slots=True)
class Axis1MeasurementOperationLayout:
    substep_id: str
    operation_index: int
    source_step_index: int
    name: str
    keys: tuple[str, ...]
    targets: tuple[int, ...]
    basis: str
    reset_after_measurement: bool


@dataclass(frozen=True, slots=True)
class Axis1MeasurementBoundaryLayout:
    substep_id: str
    substep_index: int
    operations: tuple[Axis1MeasurementOperationLayout, ...]
    keys: tuple[str, ...]
    targets: tuple[int, ...]
    bases: tuple[str, ...]
    reset_after: tuple[bool, ...]
    global_slice: tuple[int, int]

    @property
    def width(self) -> int:
        return len(self.keys)


@dataclass(frozen=True, slots=True)
class Axis1XorLayout:
    ordinal: int
    name: str
    keys: tuple[str, ...]
    columns: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Axis1ScheduleRecordLayout:
    schema: str
    source_hash: str
    schedule_schema: str
    boundaries: tuple[Axis1MeasurementBoundaryLayout, ...]
    measurement_keys: tuple[str, ...]
    measurement_targets: tuple[int, ...]
    measurement_bases: tuple[str, ...]
    reset_after: tuple[bool, ...]
    detectors: tuple[Axis1XorLayout, ...]
    observables: tuple[Axis1XorLayout, ...]

    @property
    def measurement_width(self) -> int:
        return len(self.measurement_keys)

    def boundary_for_substep_id(self, substep_id: str) -> Axis1MeasurementBoundaryLayout:
        wanted = str(substep_id)
        for boundary in self.boundaries:
            if boundary.substep_id == wanted:
                return boundary
        raise ValueError(
            f"measurement substep {wanted!r} is absent from the sealed schedule Record layout"
        )


@dataclass(frozen=True, slots=True)
class Axis1ProjectedRecords:
    detector_names: tuple[str, ...]
    detector_records: tuple[tuple[int, ...], ...]
    observable_names: tuple[str, ...]
    observable_records: tuple[tuple[int, ...], ...]


def axis1_record_layout_from_schedule(
    schedule: SubstepSchedule,
) -> Axis1ScheduleRecordLayout:
    """Parse one immutable Record schema from a compiler-sealed schedule."""

    require_compiler_schedule_seal(schedule)
    boundaries: list[Axis1MeasurementBoundaryLayout] = []
    all_keys: list[str] = []
    all_targets: list[int] = []
    all_bases: list[str] = []
    all_reset_after: list[bool] = []

    for substep_index, substep in enumerate(schedule.substeps):
        if str(substep.kind) != "measurement":
            continue
        start = len(all_keys)
        operations: list[Axis1MeasurementOperationLayout] = []
        boundary_keys: list[str] = []
        boundary_targets: list[int] = []
        boundary_bases: list[str] = []
        boundary_reset_after: list[bool] = []
        for operation_index, operation in enumerate(substep.operations):
            keys = tuple(str(key) for key in operation.measurement_keys)
            targets = tuple(int(target) for target in operation.targets)
            if not keys:
                raise ValueError(
                    f"measurement operation in {substep.substep_id!r} has no Record keys"
                )
            if len(keys) != len(targets):
                raise ValueError(
                    "measurement operation keys must match targets: "
                    f"substep={substep.substep_id!r} keys={keys!r} targets={targets!r}"
                )
            if any(not key for key in keys):
                raise ValueError(
                    f"measurement operation in {substep.substep_id!r} has an empty Record key"
                )
            if any(target < 0 or target >= int(schedule.num_qubits) for target in targets):
                raise ValueError(
                    f"measurement target outside schedule qubits in {substep.substep_id!r}"
                )
            basis = str(operation.basis or "Z").upper()
            reset = bool(operation.reset_after_measurement)
            operations.append(
                Axis1MeasurementOperationLayout(
                    substep_id=str(substep.substep_id),
                    operation_index=int(operation_index),
                    source_step_index=int(operation.source_step_index),
                    name=str(operation.name),
                    keys=keys,
                    targets=targets,
                    basis=basis,
                    reset_after_measurement=reset,
                )
            )
            boundary_keys.extend(keys)
            boundary_targets.extend(targets)
            boundary_bases.extend([basis] * len(targets))
            boundary_reset_after.extend([reset] * len(targets))

        if not operations:
            raise ValueError(
                f"measurement substep {substep.substep_id!r} has no operations"
            )
        if tuple(substep.measurement_keys) != tuple(boundary_keys):
            raise ValueError(
                "measurement substep keys disagree with its operations: "
                f"substep={substep.substep_id!r} "
                f"substep_keys={tuple(substep.measurement_keys)!r} "
                f"operation_keys={tuple(boundary_keys)!r}"
            )
        if len(set(boundary_targets)) != len(boundary_targets):
            raise ValueError(
                f"measurement boundary {substep.substep_id!r} repeats a target"
            )
        stop = start + len(boundary_keys)
        boundaries.append(
            Axis1MeasurementBoundaryLayout(
                substep_id=str(substep.substep_id),
                substep_index=int(substep_index),
                operations=tuple(operations),
                keys=tuple(boundary_keys),
                targets=tuple(boundary_targets),
                bases=tuple(boundary_bases),
                reset_after=tuple(boundary_reset_after),
                global_slice=(start, stop),
            )
        )
        all_keys.extend(boundary_keys)
        all_targets.extend(boundary_targets)
        all_bases.extend(boundary_bases)
        all_reset_after.extend(boundary_reset_after)

    if len(set(all_keys)) != len(all_keys):
        duplicates = sorted({key for key in all_keys if all_keys.count(key) > 1})
        raise ValueError(f"measurement Record keys must be globally unique: {duplicates}")

    raw_ref = schedule.record_layout_ref
    if not isinstance(raw_ref, dict):
        raise TypeError("schedule record_layout_ref must be a dict")
    reference_keys = raw_ref.get("measurement_keys", ())
    if not isinstance(reference_keys, (list, tuple)):
        raise TypeError("schedule record_layout_ref measurement_keys must be a list or tuple")
    if tuple(str(key) for key in reference_keys) != tuple(all_keys):
        raise ValueError(
            "sealed schedule record_layout_ref keys disagree with measurement substeps"
        )
    key_to_column = {key: index for index, key in enumerate(all_keys)}
    detectors = _xor_layouts(
        raw_ref.get("detectors", ()),
        expected_names=raw_ref.get("detector_names", ()),
        key_to_column=key_to_column,
        label="detector",
    )
    observables = _xor_layouts(
        raw_ref.get("observables", ()),
        expected_names=raw_ref.get("observable_names", ()),
        key_to_column=key_to_column,
        label="observable",
    )
    return Axis1ScheduleRecordLayout(
        schema=AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
        source_hash=str(schedule.source_hash),
        schedule_schema=str(schedule.schema_version),
        boundaries=tuple(boundaries),
        measurement_keys=tuple(all_keys),
        measurement_targets=tuple(all_targets),
        measurement_bases=tuple(all_bases),
        reset_after=tuple(all_reset_after),
        detectors=detectors,
        observables=observables,
    )


def materialize_binary_records(width: int) -> tuple[tuple[int, ...], ...]:
    """Return the canonical LSB-first binary Record domain for ``width`` bits."""

    if isinstance(width, bool) or not isinstance(width, int):
        raise TypeError("Record width must be an integer")
    if width < 0:
        raise ValueError("Record width must be nonnegative")
    return tuple(
        tuple((index >> bit) & 1 for bit in range(width))
        for index in range(1 << width)
    )


def project_axis1_xor_records(
    layout: Axis1ScheduleRecordLayout,
    measurement_records: Sequence[Sequence[int]],
) -> Axis1ProjectedRecords:
    """Project fixed-width binary Records through precomputed XOR columns."""

    normalized: list[tuple[int, ...]] = []
    for row_index, row in enumerate(measurement_records):
        values = tuple(row)
        if len(values) != layout.measurement_width:
            raise ValueError(
                f"measurement record {row_index} width does not match immutable layout"
            )
        bits: list[int] = []
        for column, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
                raise ValueError(
                    f"measurement record {row_index} column {column} is not a binary int"
                )
            bits.append(int(value))
        normalized.append(tuple(bits))

    return Axis1ProjectedRecords(
        detector_names=tuple(definition.name for definition in layout.detectors),
        detector_records=_project_xors(normalized, layout.detectors),
        observable_names=tuple(definition.name for definition in layout.observables),
        observable_records=_project_xors(normalized, layout.observables),
    )


def _validate_axis1_projected_record_payload(
    layout: Axis1ScheduleRecordLayout,
    execution: dict[str, Any],
    *,
    context: str,
) -> None:
    """Bind serialized detector/observable projections to one frozen layout.

    This is deliberately private authentication machinery.  The execution
    adapter supplies only measurement outcomes; detector and logical rows are
    reconstructed from the compiler-sealed layout before a parent may publish
    the child as trusted Record evidence.
    """

    measurement_records = _require_exact_binary_record_matrix(
        execution.get("measurement_records"),
        field="measurement_records",
        context=context,
    )
    projected = project_axis1_xor_records(layout, measurement_records)
    projections = (
        (
            "detector",
            "detector_names",
            list(projected.detector_names),
            "detector_records",
            [list(row) for row in projected.detector_records],
            "detector_records_emitted",
        ),
        (
            "logical observable",
            "logical_observable_names",
            list(projected.observable_names),
            "logical_observable_records",
            [list(row) for row in projected.observable_records],
            "logical_observables_emitted",
        ),
    )
    for (
        label,
        names_field,
        expected_names,
        records_field,
        expected_records,
        emitted_field,
    ) in projections:
        names = _require_exact_text_list(
            execution.get(names_field),
            field=names_field,
            context=context,
        )
        if names != expected_names:
            raise ValueError(
                f"{context} {label} names do not match frozen Record layout"
            )
        records = _require_exact_binary_record_matrix(
            execution.get(records_field),
            field=records_field,
            context=context,
        )
        if records != expected_records:
            raise ValueError(
                f"{context} {label} records do not match frozen Record layout"
            )
        emitted = execution.get(emitted_field)
        if type(emitted) is not bool:
            raise TypeError(f"{context} {emitted_field} must be an exact bool")
        if emitted is not bool(expected_names):
            raise ValueError(
                f"{context} {emitted_field} does not match frozen Record layout"
            )


def _require_exact_text_list(
    value: Any,
    *,
    field: str,
    context: str,
) -> list[str]:
    if type(value) is not list:
        raise TypeError(f"{context} {field} must be an exact list")
    if any(type(item) is not str or not item for item in value):
        raise TypeError(
            f"{context} {field} entries must be nonempty exact strings"
        )
    return value


def _require_exact_binary_record_matrix(
    value: Any,
    *,
    field: str,
    context: str,
) -> list[list[int]]:
    if type(value) is not list:
        raise TypeError(f"{context} {field} must be an exact list")
    for row_index, row in enumerate(value):
        if type(row) is not list:
            raise TypeError(
                f"{context} {field}[{row_index}] must be an exact list"
            )
        for column, bit in enumerate(row):
            if type(bit) is not int or bit not in (0, 1):
                raise TypeError(
                    f"{context} {field}[{row_index}][{column}] must be an "
                    "exact binary int"
                )
    return value


def _xor_layouts(
    definitions: Any,
    *,
    expected_names: Any,
    key_to_column: dict[str, int],
    label: str,
) -> tuple[Axis1XorLayout, ...]:
    if not isinstance(definitions, (list, tuple)):
        raise TypeError(f"schedule {label} definitions must be a list or tuple")
    out: list[Axis1XorLayout] = []
    seen_names: set[str] = set()
    for ordinal, definition in enumerate(definitions):
        if not isinstance(definition, dict):
            raise TypeError(f"schedule {label} definition {ordinal} must be a dict")
        name = str(definition.get("name", ""))
        if not name:
            raise ValueError(f"schedule {label} definition {ordinal} has an empty name")
        if name in seen_names:
            raise ValueError(f"schedule {label} names must be unique: {name!r}")
        seen_names.add(name)
        raw_keys = definition.get("keys", ())
        if not isinstance(raw_keys, (list, tuple)):
            raise TypeError(f"schedule {label} {name!r} keys must be a list or tuple")
        keys = tuple(str(key) for key in raw_keys)
        if len(set(keys)) != len(keys):
            raise ValueError(f"schedule {label} {name!r} repeats a Record key")
        unknown = [key for key in keys if key not in key_to_column]
        if unknown:
            raise ValueError(
                f"schedule {label} {name!r} references unknown Record keys: {unknown}"
            )
        out.append(
            Axis1XorLayout(
                ordinal=int(ordinal),
                name=name,
                keys=keys,
                columns=tuple(key_to_column[key] for key in keys),
            )
        )
    if not isinstance(expected_names, (list, tuple)):
        raise TypeError(f"schedule {label}_names must be a list or tuple")
    if tuple(str(name) for name in expected_names) != tuple(item.name for item in out):
        raise ValueError(f"schedule {label}_names disagree with {label} definitions")
    return tuple(out)


def _project_xors(
    rows: Sequence[tuple[int, ...]],
    definitions: tuple[Axis1XorLayout, ...],
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(sum(row[column] for column in definition.columns) % 2 for definition in definitions)
        for row in rows
    )

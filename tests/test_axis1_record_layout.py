from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from error_coupling_simulator.frontend import (
    CircuitBuilder,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.frontend.axis1_record_layout import (
    AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA,
    _require_exact_binary_record_matrix,
    _require_exact_text_list,
    _validate_axis1_projected_record_payload,
    axis1_record_layout_from_schedule,
    materialize_binary_records,
    project_axis1_xor_records,
)
from error_coupling_simulator.frontend.analog_schedule import _seal_compiler_schedule


def _mixed_boundary_schedule():
    builder = CircuitBuilder(num_qubits=2)
    builder.measure(0, key="m0", reset=True)
    builder.measure(1, key="m1")
    builder.tick()
    builder.measure(1, key="m2")
    builder.detector("d_time", xor=("m1", "m2"))
    builder.observable("logical", xor=("m0", "m2"), index=0)
    return circuit_ir_to_substep_schedule(builder.build())


def test_axis1_record_layout_freezes_schedule_schema_and_xor_columns() -> None:
    schedule = _mixed_boundary_schedule()

    layout = axis1_record_layout_from_schedule(schedule)

    assert layout.schema == AXIS1_SCHEDULE_RECORD_LAYOUT_SCHEMA
    assert layout.measurement_keys == ("m0", "m1", "m2")
    assert layout.measurement_targets == (0, 1, 1)
    assert layout.measurement_bases == ("Z", "Z", "Z")
    assert layout.reset_after == (True, False, False)
    assert [boundary.keys for boundary in layout.boundaries] == [
        ("m0", "m1"),
        ("m2",),
    ]
    assert [boundary.global_slice for boundary in layout.boundaries] == [
        (0, 2),
        (2, 3),
    ]
    assert layout.detectors[0].columns == (1, 2)
    assert layout.observables[0].columns == (0, 2)
    assert layout.source_hash == schedule.source_hash
    assert layout.schedule_schema == schedule.schema_version
    assert [boundary.width for boundary in layout.boundaries] == [2, 1]
    assert [
        (
            boundary.substep_id,
            boundary.substep_index,
            [
                (
                    operation.substep_id,
                    operation.operation_index,
                    operation.source_step_index,
                    operation.name,
                    operation.keys,
                    operation.targets,
                    operation.basis,
                    operation.reset_after_measurement,
                )
                for operation in boundary.operations
            ],
        )
        for boundary in layout.boundaries
    ] == [
        (
            "s0000",
            0,
            [
                ("s0000", 0, 0, "MR", ("m0",), (0,), "Z", True),
                ("s0000", 1, 1, "M", ("m1",), (1,), "Z", False),
            ],
        ),
        (
            "s0002",
            2,
            [("s0002", 0, 3, "M", ("m2",), (1,), "Z", False)],
        ),
    ]
    assert [
        (item.ordinal, item.name, item.keys, item.columns)
        for item in (*layout.detectors, *layout.observables)
    ] == [
        (0, "d_time", ("m1", "m2"), (1, 2)),
        (0, "logical", ("m0", "m2"), (0, 2)),
    ]

    with pytest.raises(FrozenInstanceError):
        layout.source_hash = "mutated"  # type: ignore[misc]
    with pytest.raises(TypeError):
        layout.boundaries[0].keys[0] = "mutated"  # type: ignore[index]


def test_axis1_record_layout_projects_hand_written_temporal_xors() -> None:
    layout = axis1_record_layout_from_schedule(_mixed_boundary_schedule())
    records = materialize_binary_records(layout.measurement_width)

    projected = project_axis1_xor_records(layout, records)

    assert records == (
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 0),
        (1, 1, 0),
        (0, 0, 1),
        (1, 0, 1),
        (0, 1, 1),
        (1, 1, 1),
    )
    assert projected.detector_names == ("d_time",)
    assert projected.detector_records == (
        (0,),
        (0,),
        (1,),
        (1,),
        (1,),
        (1,),
        (0,),
        (0,),
    )
    assert projected.observable_names == ("logical",)
    assert projected.observable_records == (
        (0,),
        (1,),
        (0,),
        (1,),
        (1,),
        (0,),
        (1,),
        (0,),
    )


def test_axis1_record_layout_rejects_record_width_and_bit_corruption() -> None:
    layout = axis1_record_layout_from_schedule(_mixed_boundary_schedule())

    with pytest.raises(ValueError):
        project_axis1_xor_records(layout, ((0, 1),))
    with pytest.raises(ValueError):
        project_axis1_xor_records(layout, ((0, 1, True),))

    with pytest.raises(TypeError):
        materialize_binary_records(True)
    with pytest.raises(ValueError):
        materialize_binary_records(-1)
    with pytest.raises(ValueError):
        layout.boundary_for_substep_id("not-a-boundary")

    assert materialize_binary_records(0) == ((),)
    assert materialize_binary_records(2) == (
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
    )
    for corrupted_width in (False, 1.0, "1", None):
        with pytest.raises(TypeError):
            materialize_binary_records(corrupted_width)  # type: ignore[arg-type]


class _ListSubclass(list):
    pass


class _TextSubclass(str):
    pass


class _IntSubclass(int):
    pass


def test_axis1_record_payload_text_list_requires_exact_nonempty_strings() -> None:
    names = ["d0", "logical"]

    assert _require_exact_text_list(
        names,
        field="names",
        context="unit",
    ) is names

    corruptions = (
        None,
        "d0",
        ("d0",),
        _ListSubclass(["d0"]),
        [""],
        [1],
        [True],
        [_TextSubclass("d0")],
        ["d0", ""],
    )
    for corrupted in corruptions:
        with pytest.raises(TypeError):
            _require_exact_text_list(
                corrupted,
                field="names",
                context="unit",
            )


def test_axis1_record_payload_matrix_requires_exact_binary_int_lists() -> None:
    records = [[0, 1], [], [1, 0]]

    assert _require_exact_binary_record_matrix(
        records,
        field="records",
        context="unit",
    ) is records

    corruptions = (
        None,
        ((0, 1),),
        _ListSubclass([[0, 1]]),
        [(0, 1)],
        [_ListSubclass([0, 1])],
        [[True, 1]],
        [[0, False]],
        [[-1, 1]],
        [[0, 2]],
        [[0.0, 1]],
        [[0, "1"]],
        [[_IntSubclass(0), 1]],
        [[0, 1], [1, 2]],
        [[0, 1], [1, 0], [0, 2]],
    )
    for corrupted in corruptions:
        with pytest.raises(TypeError):
            _require_exact_binary_record_matrix(
                corrupted,
                field="records",
                context="unit",
            )


def _valid_projected_execution() -> tuple[object, dict[str, object]]:
    layout = axis1_record_layout_from_schedule(_mixed_boundary_schedule())
    execution: dict[str, object] = {
        "measurement_records": [[0, 0, 0], [1, 1, 0], [0, 1, 1]],
        "detector_names": ["d_time"],
        "detector_records": [[0], [1], [0]],
        "detector_records_emitted": True,
        "logical_observable_names": ["logical"],
        "logical_observable_records": [[0], [1], [1]],
        "logical_observables_emitted": True,
    }
    return layout, execution


def test_axis1_projected_payload_authenticates_without_mutating_valid_evidence() -> None:
    layout, execution = _valid_projected_execution()
    before = copy.deepcopy(execution)

    assert _validate_axis1_projected_record_payload(
        layout,
        execution,
        context="unit",
    ) is None
    assert execution == before


@pytest.mark.parametrize(
    ("field", "corrupted", "error_type"),
    [
        ("measurement_records", None, TypeError),
        ("measurement_records", ((0, 0, 0),), TypeError),
        ("measurement_records", [(0, 0, 0)], TypeError),
        ("measurement_records", [[0, 0, True]], TypeError),
        ("measurement_records", [[0, 0]], ValueError),
        ("detector_names", None, TypeError),
        ("detector_names", ("d_time",), TypeError),
        ("detector_names", [""], TypeError),
        ("detector_names", ["wrong"], ValueError),
        ("detector_records", None, TypeError),
        ("detector_records", [(0,), (1,), (0,)], TypeError),
        ("detector_records", [[False], [1], [0]], TypeError),
        ("detector_records", [[1], [1], [0]], ValueError),
        ("detector_records_emitted", 1, TypeError),
        ("detector_records_emitted", False, ValueError),
        ("logical_observable_names", None, TypeError),
        ("logical_observable_names", ("logical",), TypeError),
        ("logical_observable_names", [""], TypeError),
        ("logical_observable_names", ["wrong"], ValueError),
        ("logical_observable_records", None, TypeError),
        ("logical_observable_records", [(0,), (1,), (1,)], TypeError),
        ("logical_observable_records", [[0], [True], [1]], TypeError),
        ("logical_observable_records", [[1], [1], [1]], ValueError),
        ("logical_observables_emitted", 1, TypeError),
        ("logical_observables_emitted", False, ValueError),
    ],
)
def test_axis1_projected_payload_rejects_serialized_projection_corruption(
    field: str,
    corrupted: object,
    error_type: type[Exception],
) -> None:
    layout, execution = _valid_projected_execution()
    execution[field] = corrupted

    with pytest.raises(error_type):
        _validate_axis1_projected_record_payload(
            layout,
            execution,
            context="unit",
        )


def test_axis1_projected_payload_binds_false_emission_flags_for_empty_xor_layouts() -> None:
    schedule = circuit_ir_to_substep_schedule(
        CircuitBuilder(num_qubits=1).measure(0, key="m0").build()
    )
    layout = axis1_record_layout_from_schedule(schedule)
    execution = {
        "measurement_records": [[0], [1]],
        "detector_names": [],
        "detector_records": [[], []],
        "detector_records_emitted": False,
        "logical_observable_names": [],
        "logical_observable_records": [[], []],
        "logical_observables_emitted": False,
    }

    assert _validate_axis1_projected_record_payload(
        layout,
        execution,
        context="unit",
    ) is None
    for emitted_field in (
        "detector_records_emitted",
        "logical_observables_emitted",
    ):
        corrupted = dict(execution)
        corrupted[emitted_field] = True
        with pytest.raises(ValueError):
            _validate_axis1_projected_record_payload(
                layout,
                corrupted,
                context="unit",
            )


def _reseal_with_measurement(
    schedule,
    *,
    operations=None,
    measurement_keys=None,
    record_layout_ref=None,
):
    measurement_index = next(
        index
        for index, substep in enumerate(schedule.substeps)
        if substep.kind == "measurement"
    )
    original = schedule.substeps[measurement_index]
    changed = replace(
        original,
        operations=original.operations if operations is None else tuple(operations),
        measurement_keys=(
            original.measurement_keys
            if measurement_keys is None
            else tuple(measurement_keys)
        ),
    )
    substeps = list(schedule.substeps)
    substeps[measurement_index] = changed
    candidate = replace(schedule, substeps=tuple(substeps))
    if record_layout_ref is not None:
        object.__setattr__(candidate, "record_layout_ref", record_layout_ref)
    return _seal_compiler_schedule(candidate)


def test_axis1_record_layout_constructs_multiple_xors_in_declared_order() -> None:
    schedule = _mixed_boundary_schedule()
    record_layout_ref = {
        **schedule.record_layout_ref,
        "detectors": [
            {"name": "d_left", "keys": ["m0"]},
            {"name": "d_time", "keys": ["m1", "m2"]},
        ],
        "detector_names": ["d_left", "d_time"],
    }
    resealed = _reseal_with_measurement(
        schedule,
        record_layout_ref=record_layout_ref,
    )

    layout = axis1_record_layout_from_schedule(resealed)

    assert [
        (item.ordinal, item.name, item.keys, item.columns)
        for item in layout.detectors
    ] == [
        (0, "d_left", ("m0",), (0,)),
        (1, "d_time", ("m1", "m2"), (1, 2)),
    ]


@pytest.mark.parametrize(
    ("updates", "error_type"),
    [
        ({"detectors": "not-a-sequence", "detector_names": []}, TypeError),
        ({"detectors": [None], "detector_names": []}, TypeError),
        ({"detectors": [{}], "detector_names": ["None"]}, ValueError),
        ({"detectors": [{}], "detector_names": ["XXXX"]}, ValueError),
        (
            {"detectors": [{"name": "", "keys": []}], "detector_names": []},
            ValueError,
        ),
        (
            {
                "detectors": [
                    {"name": "same", "keys": ["m0"]},
                    {"name": "same", "keys": ["m1"]},
                ],
                "detector_names": ["same", "same"],
            },
            ValueError,
        ),
        (
            {
                "detectors": [{"name": "d", "keys": "m0"}],
                "detector_names": ["d"],
            },
            TypeError,
        ),
        (
            {
                "detectors": [{"name": "d", "keys": ["m0", "m0"]}],
                "detector_names": ["d"],
            },
            ValueError,
        ),
        (
            {
                "detectors": [{"name": "d", "keys": ["unknown"]}],
                "detector_names": ["d"],
            },
            ValueError,
        ),
        ({"detector_names": "d_time"}, TypeError),
        ({"detector_names": ["wrong"]}, ValueError),
    ],
)
def test_axis1_record_layout_rejects_xor_definition_corruption(
    updates: dict[str, object],
    error_type: type[Exception],
) -> None:
    schedule = _mixed_boundary_schedule()
    resealed = _reseal_with_measurement(
        schedule,
        record_layout_ref={**schedule.record_layout_ref, **updates},
    )

    with pytest.raises(error_type):
        axis1_record_layout_from_schedule(resealed)


@pytest.mark.parametrize(
    "mutation",
    [
        "no_keys",
        "key_target_width",
        "empty_key",
        "target_outside",
        "no_operations",
        "substep_key_mismatch",
        "repeated_target",
    ],
)
def test_axis1_record_layout_rejects_resealed_measurement_corruption(
    mutation: str,
) -> None:
    schedule = circuit_ir_to_substep_schedule(
        CircuitBuilder(num_qubits=1).measure(0, key="m0").build()
    )
    operation = next(
        substep.operations[0]
        for substep in schedule.substeps
        if substep.kind == "measurement"
    )
    if mutation == "no_keys":
        corrupted = _reseal_with_measurement(
            schedule,
            operations=(replace(operation, measurement_keys=()),),
            measurement_keys=(),
        )
    elif mutation == "key_target_width":
        corrupted = _reseal_with_measurement(
            schedule,
            operations=(replace(operation, measurement_keys=("m0", "m1")),),
            measurement_keys=("m0", "m1"),
        )
    elif mutation == "empty_key":
        corrupted = _reseal_with_measurement(
            schedule,
            operations=(replace(operation, measurement_keys=("",)),),
            measurement_keys=("",),
        )
    elif mutation == "target_outside":
        corrupted = _reseal_with_measurement(
            schedule,
            operations=(replace(operation, targets=(1,)),),
        )
    elif mutation == "no_operations":
        corrupted = _reseal_with_measurement(
            schedule,
            operations=(),
            measurement_keys=(),
        )
    elif mutation == "substep_key_mismatch":
        corrupted = _reseal_with_measurement(
            schedule,
            measurement_keys=("different",),
        )
    else:
        second = replace(
            operation,
            source_step_index=operation.source_step_index + 1,
            measurement_keys=("m1",),
        )
        corrupted = _reseal_with_measurement(
            schedule,
            operations=(operation, second),
            measurement_keys=("m0", "m1"),
        )

    with pytest.raises(ValueError):
        axis1_record_layout_from_schedule(corrupted)


def test_axis1_record_layout_rejects_resealed_global_and_reference_corruption() -> None:
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.tick()
    builder.measure(0, key="m1")
    schedule = circuit_ir_to_substep_schedule(builder.build())
    assert axis1_record_layout_from_schedule(schedule).measurement_keys == (
        "m0",
        "m1",
    )
    second_index = [
        index for index, substep in enumerate(schedule.substeps) if substep.kind == "measurement"
    ][1]
    second = schedule.substeps[second_index]
    duplicate_operation = replace(second.operations[0], measurement_keys=("m0",))
    substeps = list(schedule.substeps)
    substeps[second_index] = replace(
        second,
        operations=(duplicate_operation,),
        measurement_keys=("m0",),
    )
    duplicate = replace(schedule, substeps=tuple(substeps))
    object.__setattr__(
        duplicate,
        "record_layout_ref",
        {
            "measurement_keys": ["m0", "m0"],
            "detectors": [],
            "detector_names": [],
            "observables": [],
            "observable_names": [],
        },
    )
    _seal_compiler_schedule(duplicate)
    with pytest.raises(ValueError):
        axis1_record_layout_from_schedule(duplicate)

    not_a_mapping = replace(schedule)
    object.__setattr__(not_a_mapping, "record_layout_ref", [])
    _seal_compiler_schedule(not_a_mapping)
    with pytest.raises(TypeError):
        axis1_record_layout_from_schedule(not_a_mapping)

    wrong_key_type = replace(schedule)
    object.__setattr__(
        wrong_key_type,
        "record_layout_ref",
        {**schedule.record_layout_ref, "measurement_keys": "m0,m1"},
    )
    _seal_compiler_schedule(wrong_key_type)
    with pytest.raises(TypeError):
        axis1_record_layout_from_schedule(wrong_key_type)

    wrong_keys = replace(schedule)
    object.__setattr__(
        wrong_keys,
        "record_layout_ref",
        {**schedule.record_layout_ref, "measurement_keys": ["m0", "wrong"]},
    )
    _seal_compiler_schedule(wrong_keys)
    with pytest.raises(ValueError):
        axis1_record_layout_from_schedule(wrong_keys)


def test_axis1_layout_preserves_basis_and_accepts_canonical_empty_xor_defaults() -> None:
    x_schedule = circuit_ir_to_substep_schedule(
        CircuitBuilder(num_qubits=1)
        .measure(0, key="mx", basis="X")
        .build()
    )
    assert axis1_record_layout_from_schedule(x_schedule).measurement_bases == ("X",)

    default_schedule = circuit_ir_to_substep_schedule(
        CircuitBuilder(num_qubits=1).measure(0, key="mz").build()
    )
    default_operation = next(
        substep.operations[0]
        for substep in default_schedule.substeps
        if substep.kind == "measurement"
    )
    fallback_schedule = _reseal_with_measurement(
        default_schedule,
        operations=(replace(default_operation, basis=None),),
    )
    fallback_layout = axis1_record_layout_from_schedule(fallback_schedule)
    assert fallback_layout.measurement_bases == ("Z",)
    assert fallback_layout.boundaries[0].operations[0].basis == "Z"

    no_measurement = circuit_ir_to_substep_schedule(
        CircuitBuilder(num_qubits=1).build()
    )
    no_measurement = replace(no_measurement)
    object.__setattr__(no_measurement, "record_layout_ref", {})
    _seal_compiler_schedule(no_measurement)
    empty_layout = axis1_record_layout_from_schedule(no_measurement)
    assert empty_layout.measurement_keys == ()
    assert empty_layout.boundaries == ()

    stripped = circuit_ir_to_substep_schedule(
        CircuitBuilder(num_qubits=1).measure(0, key="m0").build()
    )
    stripped = replace(stripped)
    object.__setattr__(
        stripped,
        "record_layout_ref",
        {"measurement_keys": ["m0"]},
    )
    _seal_compiler_schedule(stripped)
    layout = axis1_record_layout_from_schedule(stripped)
    assert layout.detectors == ()
    assert layout.observables == ()

    schedule = _mixed_boundary_schedule()
    omitted_keys = _reseal_with_measurement(
        schedule,
        record_layout_ref={
            **schedule.record_layout_ref,
            "detectors": [{"name": "empty"}],
            "detector_names": ["empty"],
        },
    )
    empty_detector = axis1_record_layout_from_schedule(omitted_keys).detectors[0]
    assert empty_detector.keys == ()
    assert empty_detector.columns == ()

    with pytest.raises(ValueError):
        project_axis1_xor_records(
            axis1_record_layout_from_schedule(_mixed_boundary_schedule()),
            ((0, 1, 0.0),),
        )


@pytest.mark.mutation_trampoline_incompatible
@pytest.mark.parametrize(
    "relative_path",
    [
        "src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py",
        "src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py",
    ],
)
def test_mps_record_schema_is_not_registered_inside_trajectory_control_flow(
    relative_path: str,
) -> None:
    source = (Path(__file__).parents[1] / relative_path).read_text()

    assert "boundary_seen" not in source
    assert "measurement_keys.extend" not in source
    assert "measurement_targets.extend" not in source

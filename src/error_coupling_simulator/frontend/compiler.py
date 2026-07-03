from __future__ import annotations

"""Frontend compiler from generic syndrome-code specs to `CircuitIR`."""

from .circuit_ir import CircuitBuilder, CircuitIR
from .code_spec import CodeSpec, PauliTerm
from .axis1_context import AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY
from .metadata_guard import (
    AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY,
    AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY,
)
from .noise_spec import FrontendNoiseSpec
from .record_layout import (
    build_repeated_memory_record_layout,
    check_key,
    final_measurements,
)
from .schedule import ScheduleTemplate, resolve_schedule_template
from .stim_source import CircuitIRSource, CompiledCircuit


def compile_code_spec(
    spec: CodeSpec,
    *,
    schedule_template: str | ScheduleTemplate = "repeated_memory_v1",
) -> CircuitIR:
    """Compile a commuting stabilizer `CodeSpec` into keyed `CircuitIR`.

    The current schedule is deliberately simple and explicit: each check uses
    its declared ancilla, repeated rounds are measured in the same order, and
    detectors are round-to-round syndrome deltas plus final data-closure
    detectors. This schedule requires every data qubit used in final closure or
    logical readout to have one compatible measurement basis.
    """

    schedule = resolve_schedule_template(schedule_template)
    schedule.validate_for(spec)
    _require_supported_bases(spec)
    _require_final_measurement_compatibility(spec)
    layout = build_repeated_memory_record_layout(spec, schedule_name=schedule.name)

    builder = CircuitBuilder(
        spec.num_qubits,
        metadata={
            "compiler": "qec_twin.simulator.compiler.repeated_memory_v1",
            "schedule": schedule.to_manifest(),
            "record_layout": layout.to_manifest(),
            "code_spec": spec.to_manifest(),
            "qubit_coords": _qubit_coords(spec),
        },
    )
    if (
        AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY in spec.metadata
        or AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY in spec.metadata
    ):
        builder.declare_static_zz_couplings(
            spec.metadata.get(AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY, ()),
            zeta_rad_per_ns_by_edge=spec.metadata.get(
                AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY
            ),
        )
    if AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY in spec.metadata:
        builder.declare_axis1_local_lindblad_context(
            spec.metadata[AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY]
        )
    for round_index in range(spec.rounds):
        for check in spec.checks:
            _measure_check(builder, check, round_index=round_index)
        builder.tick()

    for detector in layout.detectors:
        if detector.kind == "round_delta":
            builder.detector(detector.name, xor=detector.keys, coords=detector.coords)

    for record in layout.final_data:
        builder.measure(record.qubit, key=record.key, basis=record.basis)
    for detector in layout.detectors:
        if detector.kind == "final_closure":
            builder.detector(detector.name, xor=detector.keys, coords=detector.coords)
    for observable in layout.observables:
        builder.observable(observable.name, xor=observable.keys, index=observable.index)
    return builder.build()


def compile_code_spec_to_compiled(
    spec: CodeSpec,
    *,
    noise: FrontendNoiseSpec | None = None,
    schedule_template: str | ScheduleTemplate = "repeated_memory_v1",
) -> CompiledCircuit:
    """Compile a `CodeSpec` all the way to the simulator's Stim-backed pair."""

    return CircuitIRSource(
        compile_code_spec(spec, schedule_template=schedule_template)
    ).compile(noise)


def _measure_check(builder: CircuitBuilder, check, *, round_index: int) -> None:
    builder.reset(check.ancilla)
    for term in check.terms:
        _rotate_data_to_z(builder, term)
        builder.cx((term.qubit, check.ancilla))
        _undo_data_rotation(builder, term)
    builder.measure(check.ancilla, key=check_key(round_index, check.name))


def _rotate_data_to_z(builder: CircuitBuilder, term: PauliTerm) -> None:
    if term.basis == "X":
        builder.h(term.qubit)
    elif term.basis == "Z":
        return
    else:  # pragma: no cover - guarded by _require_supported_bases
        raise NotImplementedError(f"unsupported check basis {term.basis!r}")


def _undo_data_rotation(builder: CircuitBuilder, term: PauliTerm) -> None:
    if term.basis == "X":
        builder.h(term.qubit)
    elif term.basis == "Z":
        return
    else:  # pragma: no cover - guarded by _require_supported_bases
        raise NotImplementedError(f"unsupported check basis {term.basis!r}")


def _require_supported_bases(spec: CodeSpec) -> None:
    unsupported = sorted(
        {
            term.basis
            for check in spec.checks
            for term in check.terms
            if term.basis not in {"X", "Z"}
        }
    )
    unsupported += sorted(
        {
            term.basis
            for logical in spec.logical_observables
            for term in logical.terms
            if term.basis not in {"X", "Z"}
        }
    )
    if unsupported:
        raise NotImplementedError(
            "compiler schedule currently supports X/Z Pauli products only; "
            f"unsupported={sorted(set(unsupported))}"
        )


def _require_final_measurement_compatibility(spec: CodeSpec) -> None:
    final_measurements(spec)


def _qubit_coords(spec: CodeSpec) -> dict[str, list[float]]:
    return {
        str(qubit.index): list(qubit.coords)
        for qubit in spec.data_qubits + spec.ancilla_qubits
        if qubit.coords
    }

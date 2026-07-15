from __future__ import annotations

import json

import pytest

from error_coupling_simulator.frontend import (
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    OperationSpec,
    PauliTerm,
    ScheduleTemplate,
    Simulator,
    StabilizerCheck,
    XZZXCodeSpec,
    build_repeated_memory_record_layout,
    compile_code_spec,
    repeated_memory_schedule,
)
from error_coupling_simulator.frontend.operation import canonical_operation_name
from error_coupling_simulator.frontend.record_layout import final_measurements
from error_coupling_simulator.frontend.stim_io import circuit_to_stim

def test_record_layout_matches_compiled_circuit_key_order():
    spec = XZZXCodeSpec(layout_size=3, rounds=3).to_code_spec()
    schedule = repeated_memory_schedule()
    layout = build_repeated_memory_record_layout(spec, schedule_name=schedule.name)
    circuit = compile_code_spec(spec, schedule_template=schedule)

    assert circuit.metadata["schedule"] == schedule.to_manifest()
    assert circuit.metadata["record_layout"] == layout.to_manifest()
    assert circuit.measurement_keys == layout.measurement_keys
    assert circuit.detector_names == layout.detector_names
    assert circuit.observable_names == layout.observable_names
    assert len(layout.round_measurements) == len(spec.checks) * spec.rounds
    assert len(layout.detectors) == len(spec.checks) * spec.rounds
    assert len(layout.final_data) == len(spec.data_qubits)
    assert layout.detectors[0].kind == "round_delta"
    assert layout.detectors[-1].kind == "final_closure"


def test_persisted_manifest_records_exact_layout_order(tmp_path):
    spec = _make_mixed_frontend_spec(rounds=2)
    circuit = compile_code_spec(spec)
    result = Simulator(circuit).run(shots=16, noise=None, out_dir=tmp_path / "mixed", seed=2)
    manifest = json.loads(result.paths.manifest.read_text())
    layout = circuit.metadata["record_layout"]

    assert manifest["record_schema"]["measurement_keys"] == [
        record["key"] for record in layout["round_measurements"]
    ] + [record["key"] for record in layout["final_data"]]
    assert manifest["record_schema"]["detector_names"] == [
        record["name"] for record in layout["detectors"]
    ]
    assert manifest["record_schema"]["observable_names"] == [
        record["name"] for record in layout["observables"]
    ]


def test_custom_record_order_has_golden_names():
    spec = _make_mixed_frontend_spec(rounds=3)
    circuit = compile_code_spec(spec)

    assert circuit.measurement_keys == (
        "round0:x0",
        "round0:z1",
        "round1:x0",
        "round1:z1",
        "round2:x0",
        "round2:z1",
        "final:q0:X",
        "final:q1:Z",
        "final:q2:Z",
    )
    assert circuit.detector_names == (
        "delta:x0:round1",
        "delta:z1:round1",
        "delta:x0:round2",
        "delta:z1:round2",
        "final:x0",
        "final:z1",
    )
    assert circuit.observable_names == ("logical_z2",)


def test_custom_repetition_codespec_compiles_through_same_frontend():
    spec = _make_repetition3_spec(rounds=2)
    circuit = compile_code_spec(spec)
    stim_circuit = circuit_to_stim(circuit)

    assert stim_circuit.num_qubits == 5
    assert stim_circuit.num_detectors == len(spec.checks) * spec.rounds
    assert stim_circuit.num_observables == 1
    assert circuit.metadata["code_spec"]["name"] == "rep3_custom_frontend"
    assert circuit.metadata["schedule"]["name"] == "repeated_memory_v1"
    assert circuit.metadata["record_layout"]["final_data"] == [
        {"key": "final:q0:Z", "qubit": 0, "basis": "Z"},
        {"key": "final:q1:Z", "qubit": 1, "basis": "Z"},
        {"key": "final:q2:Z", "qubit": 2, "basis": "Z"},
    ]


def test_schedule_fails_before_artifacts_when_required_operation_missing():
    good = _make_repetition3_spec(rounds=2)
    bad = CodeSpec(
        name=good.name,
        num_qubits=good.num_qubits,
        data_qubits=good.data_qubits,
        ancilla_qubits=good.ancilla_qubits,
        checks=good.checks,
        logical_observables=good.logical_observables,
        rounds=good.rounds,
        metadata=good.metadata,
        operations=(OperationSpec("prep0"), OperationSpec("final_readout")),
    )

    with pytest.raises(ValueError, match="requires frontend operation"):
        compile_code_spec(bad)


def test_schedule_template_cannot_lie_about_repeated_memory_policy():
    with pytest.raises(ValueError, match="fixed compiler semantics"):
        ScheduleTemplate(
            name="repeated_memory_v1",
            required_operations=("prep0", "stabilizer_round", "final_readout"),
            detector_policy="round_delta_only",
            final_readout_policy="check_and_logical_compatible_basis",
        )


def test_record_layout_rejects_conflicting_final_basis_directly():
    spec = CodeSpec(
        name="bad_final_layout",
        num_qubits=4,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data")),
        ancilla_qubits=(CodeQubit(2, "ancilla"), CodeQubit(3, "ancilla")),
        checks=(StabilizerCheck("z1", 2, (PauliTerm(1, "Z"),)),),
        logical_observables=(
            LogicalObservableSpec("logical_z", (PauliTerm(0, "Z"),), index=0),
            LogicalObservableSpec("logical_x", (PauliTerm(0, "X"),), index=1),
        ),
        rounds=2,
    )

    with pytest.raises(ValueError, match="incompatible bases"):
        final_measurements(spec)


def test_operation_aliases_are_frontend_only_names():
    assert canonical_operation_name("prepp") == "prep_plus"
    assert canonical_operation_name("prepm") == "prep_minus"
    with pytest.raises(ValueError, match="unsupported frontend operation"):
        OperationSpec("joint_lindbladian_noise")


def test_legacy_parity_schedule_name_is_rejected():
    spec = _make_repetition3_spec(rounds=2)
    with pytest.raises(ValueError, match="unsupported schedule_template"):
        compile_code_spec(spec, schedule_template="repeated_ancilla" + "_parity_v1")


def test_codespec_rejects_ambiguous_record_tokens_and_error_metadata():
    with pytest.raises(ValueError, match="record keys stay parseable"):
        StabilizerCheck("bad:name", 3, (PauliTerm(0, "Z"),))
    with pytest.raises(ValueError, match="evaluator truth"):
        CodeSpec(
            name="bad_frontend_metadata",
            num_qubits=3,
            data_qubits=(CodeQubit(0, "data"),),
            ancilla_qubits=(CodeQubit(1, "ancilla"), CodeQubit(2, "ancilla")),
            checks=(StabilizerCheck("z0", 1, (PauliTerm(0, "Z"),)),),
            logical_observables=(LogicalObservableSpec("logical0", (PauliTerm(0, "Z"),)),),
            rounds=2,
            metadata={"axis1_error_model": "belongs outside frontend metadata"},
        )
    for key in ("axis", "baseline", "error", "noise_model", "si1000"):
        with pytest.raises(ValueError, match="metadata cannot contain"):
            CodeSpec(
                name=f"bad_{key}",
                num_qubits=3,
                data_qubits=(CodeQubit(0, "data"),),
                ancilla_qubits=(CodeQubit(1, "ancilla"), CodeQubit(2, "ancilla")),
                checks=(StabilizerCheck("z0", 1, (PauliTerm(0, "Z"),)),),
                logical_observables=(LogicalObservableSpec("logical0", (PauliTerm(0, "Z"),)),),
                rounds=2,
                metadata={key: "not a frontend code fact"},
            )


def _make_repetition3_spec(*, rounds: int) -> CodeSpec:
    return CodeSpec(
        name="rep3_custom_frontend",
        num_qubits=5,
        data_qubits=(
            CodeQubit(0, "data", (0.0,)),
            CodeQubit(1, "data", (1.0,)),
            CodeQubit(2, "data", (2.0,)),
        ),
        ancilla_qubits=(
            CodeQubit(3, "ancilla", (0.5,)),
            CodeQubit(4, "ancilla", (1.5,)),
        ),
        checks=(
            StabilizerCheck("z01", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z")), (0.5,)),
            StabilizerCheck("z12", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z")), (1.5,)),
        ),
        logical_observables=(
            LogicalObservableSpec("logical_z0", (PauliTerm(0, "Z"),), index=0),
        ),
        rounds=rounds,
        metadata={"family": "custom_repetition", "encoded_distance_certified": False},
    )


def _make_mixed_frontend_spec(*, rounds: int) -> CodeSpec:
    return CodeSpec(
        name="mixed_custom_frontend",
        num_qubits=5,
        data_qubits=(
            CodeQubit(0, "data", (0.0,)),
            CodeQubit(1, "data", (1.0,)),
            CodeQubit(2, "data", (2.0,)),
        ),
        ancilla_qubits=(
            CodeQubit(3, "ancilla", (0.0, 0.5)),
            CodeQubit(4, "ancilla", (1.0, 0.5)),
        ),
        checks=(
            StabilizerCheck("x0", 3, (PauliTerm(0, "X"),), (0.0, 0.5)),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"),), (1.0, 0.5)),
        ),
        logical_observables=(
            LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),), index=0),
        ),
        rounds=rounds,
        metadata={"family": "custom_mixed_basis", "encoded_distance_certified": False},
    )

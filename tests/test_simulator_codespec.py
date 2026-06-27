from __future__ import annotations

import json

import numpy as np
import pytest

from qec_twin.hardware import b8_io
from qec_twin.simulator import (
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    Simulator,
    StabilizerCheck,
    XZZXCodeSpec,
    compile_code_spec,
    compile_code_spec_to_compiled,
)
from qec_twin.simulator.circuit_ir import CircuitIR, GateOp, Tick
from qec_twin.simulator.stim_io import sample_detector_records
from qec_twin.simulator.stim_io import circuit_to_stim


def _num_detectors(spec):
    return len(spec.checks) * spec.rounds


def test_xzzx_codespec_compiles_to_normal_circuit_ir_and_runs(tmp_path):
    pytest.importorskip("pymatching", reason="codespec simulator smoke uses PyMatching")

    spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
    circuit = compile_code_spec(spec)
    stim_circuit = circuit_to_stim(circuit)

    assert isinstance(circuit, CircuitIR)
    assert stim_circuit.num_qubits == 17
    assert stim_circuit.num_detectors == _num_detectors(spec)
    assert stim_circuit.num_observables == 1
    assert "QUBIT_COORDS(0, 0) 0" in str(stim_circuit)
    assert "QUBIT_COORDS(-0.5, 0.5) 13" in str(stim_circuit)
    assert "XZZX" not in type(Simulator(circuit).source).__name__.upper()

    result = Simulator(circuit).run(
        shots=128,
        noise=None,
        out_dir=tmp_path / "xzzx_run",
        seed=12,
    )
    manifest = json.loads(result.paths.manifest.read_text())

    assert manifest["source_type"] == "circuit_ir"
    assert manifest["record_schema"]["detector_bit_width"] == _num_detectors(spec)
    assert manifest["record_schema"]["observable_bit_width"] == 1
    assert manifest["record_schema"]["detector_names"][0].startswith("delta:")
    assert manifest["record_schema"]["detector_names"][-1].startswith("final:")
    assert manifest["record_schema"]["observable_names"] == ["observable_smoke_z1"]
    assert manifest["circuit_metadata"]["code_spec"]["name"] == "xzzx_3x3_checkerboard_compiler_smoke"
    assert manifest["circuit_metadata"]["code_spec"]["metadata"]["family"] == "xzzx"
    assert manifest["circuit_metadata"]["code_spec"]["metadata"]["encoded_distance_certified"] is False

    det = b8_io.unpack_bits(
        b8_io.read_b8(result.paths.detection_events, _num_detectors(spec)),
        _num_detectors(spec),
    )
    obs = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_actual, 1), 1)
    assert det.shape == (128, _num_detectors(spec))
    assert obs.shape == (128, 1)


def test_codespec_can_compile_directly_to_compiled_circuit_source(tmp_path):
    pytest.importorskip("pymatching", reason="codespec simulator smoke uses PyMatching")

    spec = XZZXCodeSpec(layout_size=3, rounds=3).to_code_spec()
    compiled = compile_code_spec_to_compiled(spec, noise=None)

    assert compiled.source_type == "circuit_ir"
    assert compiled.record_schema.num_detectors == _num_detectors(spec)
    assert compiled.record_schema.num_observables == 1

    result = Simulator(compiled).run(
        shots=64,
        noise=None,
        out_dir=tmp_path / "compiled_codespec",
        seed=21,
    )
    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["num_detectors"] == _num_detectors(spec)
    assert manifest["noise"] is None


def test_codespec_rejects_noncommuting_checks():
    data = (
        CodeQubit(0, "data"),
        CodeQubit(1, "data"),
    )
    ancilla = (
        CodeQubit(2, "ancilla"),
        CodeQubit(3, "ancilla"),
    )

    with pytest.raises(ValueError, match="do not commute"):
        CodeSpec(
            name="bad_noncommuting",
            num_qubits=4,
            data_qubits=data,
            ancilla_qubits=ancilla,
            checks=(
                StabilizerCheck("zx", 2, (PauliTerm(0, "Z"), PauliTerm(1, "X"))),
                StabilizerCheck("xx", 3, (PauliTerm(0, "X"), PauliTerm(1, "X"))),
            ),
            logical_observables=(
                LogicalObservableSpec("logical0", (PauliTerm(0, "Z"), PauliTerm(1, "X"))),
            ),
            rounds=2,
        )


def test_compiler_rejects_conflicting_final_logical_bases():
    spec = CodeSpec(
        name="conflicting_logicals",
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
        compile_code_spec(spec)


def test_codespec_rejects_logical_inside_stabilizer_span():
    with pytest.raises(ValueError, match="stabilizer span"):
        CodeSpec(
            name="bad_logical_is_check",
            num_qubits=3,
            data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data")),
            ancilla_qubits=(CodeQubit(2, "ancilla"),),
            checks=(StabilizerCheck("zz", 2, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),),
            logical_observables=(
                LogicalObservableSpec("not_logical", (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),
            ),
            rounds=2,
        )


def test_codespec_metadata_rejects_evaluator_truth_keys():
    with pytest.raises(ValueError, match="evaluator truth"):
        CodeSpec(
            name="leaky_metadata",
            num_qubits=3,
            data_qubits=(CodeQubit(0, "data"),),
            ancilla_qubits=(CodeQubit(1, "ancilla"), CodeQubit(2, "ancilla")),
            checks=(StabilizerCheck("z0", 1, (PauliTerm(0, "Z"),)),),
            logical_observables=(LogicalObservableSpec("logical0", (PauliTerm(0, "Z"),)),),
            rounds=2,
            metadata={"channel_truth": {"secret": True}},
        )


def test_xzzx_ideal_detectors_are_deterministic_under_zero_noise(tmp_path):
    pytest.importorskip("pymatching", reason="codespec simulator smoke uses PyMatching")

    spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
    result = Simulator(compile_code_spec(spec)).run(
        shots=96,
        noise=None,
        out_dir=tmp_path / "xzzx_ideal",
        seed=33,
    )
    det = b8_io.unpack_bits(
        b8_io.read_b8(result.paths.ideal_detection_events, _num_detectors(spec)),
        _num_detectors(spec),
    )
    assert not np.any(det)


@pytest.mark.parametrize("qubit", range(9))
@pytest.mark.parametrize("fault_basis", ("X", "Z"))
def test_compiled_checks_match_declared_pauli_fault_response(qubit, fault_basis):
    spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
    circuit = compile_code_spec(spec)
    faulted = _insert_after_first_round(circuit, GateOp(f"{fault_basis}_ERROR", (qubit,), (1.0,)))
    det, _ = sample_detector_records(circuit_to_stim(faulted), shots=8, seed=7)

    expected_delta = np.array(
        [
            any(term.qubit == qubit and term.basis != fault_basis for term in check.terms)
            for check in spec.checks
        ],
        dtype=np.bool_,
    )
    assert np.array_equal(det[0, :len(spec.checks)], expected_delta)
    assert not det[:, len(spec.checks):].any()
    assert np.all(det == det[0])


def _insert_after_first_round(circuit: CircuitIR, op: GateOp) -> CircuitIR:
    steps = []
    inserted = False
    for step in circuit.steps:
        steps.append(step)
        if not inserted and isinstance(step, Tick):
            steps.append(op)
            inserted = True
    assert inserted
    metadata = dict(circuit.metadata)
    metadata["noise_projection"] = {
        "type": "test_declared_pauli_fault",
        "instruction": op.name,
        "targets": list(op.targets),
        "args": list(op.args),
    }
    return CircuitIR(circuit.num_qubits, tuple(steps), metadata=metadata)

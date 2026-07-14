from __future__ import annotations

import json

from qec_twin.simulator import CircuitBuilder, Noise, Simulator, depolarizing_noise, targeted_noise
from qec_twin.simulator.noise import (
    Noise as NoiseModuleFacade,
    StimPauliNoiseSpec,
    apply_stim_pauli_noise,
)
from qec_twin.simulator.stim_io import circuit_to_stim


def _deterministic_two_qubit_detector_circuit():
    builder = CircuitBuilder(num_qubits=2, metadata={"code": "noise_module_public_api"})
    builder.tick()
    builder.cz((0, 1))
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"))
    builder.detector("d0", xor=("m0",), coords=(0.0,))
    builder.detector("d1", xor=("m1",), coords=(1.0,))
    builder.observable("logical0", xor=("m0",), index=0)
    return builder.build()


def test_noise_module_public_depolarizing_factory_roundtrips_manifest():
    noise = depolarizing_noise(after_1q=0.01, after_2q=0.02, before_measure_flip=0.03)

    assert isinstance(noise, StimPauliNoiseSpec)
    assert noise.to_manifest() == {
        "type": "stim_pauli",
        "after_1q_depolarization": 0.01,
        "after_2q_depolarization": 0.02,
        "before_measure_flip": 0.03,
    }
    assert Noise.depolarizing(after_2q=0.02).after_2q_depolarization == 0.02
    assert Noise.pauli(before_measure_flip=0.03).before_measure_flip == 0.03
    assert Noise.none() is None


def test_noise_module_public_targeted_builder_inserts_and_audits_placements():
    circuit = _deterministic_two_qubit_detector_circuit()
    noise = (
        targeted_noise()
        .after_gate_type("CZ", "DEPOLARIZE", 0.02, target_filter=(0, 1))
        .during_idle("DEPOLARIZE", 0.005, targets=(0, 1))
        .before_measurement("X_ERROR", 0.03)
        .build()
    )

    noisy = apply_stim_pauli_noise(circuit, noise)
    text = str(circuit_to_stim(noisy))

    assert "CZ 0 1\nDEPOLARIZE2(0.02) 0 1" in text
    assert "DEPOLARIZE1(0.005) 0 1\nTICK" in text
    assert "X_ERROR(0.03) 0 1\nM 0 1" in text
    assert noisy.metadata["noise_projection"]["matched_counts"] == [1, 1, 1]
    assert noisy.metadata["noise_projection"]["matched_events"][0][0]["matched_op"] == "CZ"


def test_noise_module_public_facade_runs_through_simulator_manifest(tmp_path):
    circuit = _deterministic_two_qubit_detector_circuit()
    noise = (
        NoiseModuleFacade.targeted()
        .after_gate_type("CZ", "DEPOLARIZE", 0.02, target_filter=(0, 1))
        .before_measurement("X_ERROR", 0.03)
        .build()
    )
    result = Simulator(circuit).run(
        shots=32,
        noise=noise,
        out_dir=tmp_path / "noise_module_public_facade",
        seed=20260627,
    )

    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["representability"] == "stim_pauli"
    assert manifest["noise"]["type"] == "targeted_stim_pauli"
    assert manifest["noise"]["matched_counts"] == [1, 1]
    assert manifest["record_schema"]["num_detectors"] == 2
    assert result.load_detection_events().shape == (32, 2)

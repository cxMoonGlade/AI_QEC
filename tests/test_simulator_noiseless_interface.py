from __future__ import annotations

import json

import numpy as np
import pytest

from qec_twin.simulator.noise_spec import StimPauliNoiseSpec, apply_stim_pauli_noise
from qec_twin.simulator import (
    CircuitBuilder,
    StimCircuitSource,
    Simulator,
    XZZXCodeSpec,
    compile_code_spec,
    simulate_noiseless,
)
from qec_twin.simulator.stim_io import circuit_to_stim


def test_run_noiseless_accepts_user_built_circuit_and_loads_records(tmp_path):
    pytest.importorskip("pymatching", reason="noiseless interface smoke uses PyMatching")

    builder = CircuitBuilder(num_qubits=1, metadata={"purpose": "noiseless_interface_test"})
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",), coords=(0.0,))
    builder.observable("logical0", xor=("m0",), index=0)
    circuit = builder.build()

    result = Simulator(circuit).run_noiseless(
        shots=32,
        out_dir=tmp_path / "manual_noiseless",
        seed=5,
        decoder="pymatching",
    )

    assert result.manifest["noise"] is None
    assert result.manifest["shots"] == 32
    assert result.manifest["circuit_metadata"]["purpose"] == "noiseless_interface_test"
    np.testing.assert_array_equal(result.load_detection_events(), np.zeros((32, 1), dtype=np.uint8))
    np.testing.assert_array_equal(result.load_observable_flips(), np.zeros((32, 1), dtype=np.uint8))
    np.testing.assert_array_equal(result.load_predicted_observable_flips(), np.zeros((32, 1), dtype=np.uint8))
    assert result.load_detection_events().dtype == np.bool_
    assert result.load_observable_flips().dtype == np.bool_
    np.testing.assert_array_equal(
        result.load_detection_events(ideal=True),
        result.load_detection_events(),
    )
    np.testing.assert_array_equal(
        result.load_observable_flips(ideal=True),
        result.load_observable_flips(),
    )


def test_simulate_noiseless_runs_compiled_xzzx_frontend(tmp_path):
    spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
    result = simulate_noiseless(
        compile_code_spec(spec),
        shots=24,
        out_dir=tmp_path / "xzzx_noiseless",
        seed=11,
    )

    assert result.manifest["noise"] is None
    assert result.manifest["circuit_metadata"]["code_spec"]["name"] == spec.name
    assert result.load_detection_events().shape == (24, len(spec.checks) * spec.rounds)
    assert result.load_observable_flips().shape == (24, 1)
    assert not result.load_detection_events().any()


def test_run_defaults_to_noiseless_when_noise_is_omitted(tmp_path):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    result = Simulator(builder.build()).run(
        shots=12,
        out_dir=tmp_path / "default_noiseless",
        seed=3,
    )
    manifest = json.loads(result.paths.manifest.read_text())

    assert manifest["noise"] is None
    assert manifest["decoder"] is None
    assert result.load_detection_events().shape == (12, 1)
    assert result.load_observable_flips().shape == (12, 0)
    assert result.load_predicted_observable_flips().shape == (12, 0)
    assert result.load_observable_flips().dtype == np.bool_


def test_run_noiseless_rejects_pre_noised_source(tmp_path):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    builder.observable("logical0", xor=("m0",), index=0)
    circuit = builder.build()
    noisy = apply_stim_pauli_noise(circuit, StimPauliNoiseSpec(before_measure_flip=0.25))
    source = StimCircuitSource(
        ideal_circuit=circuit_to_stim(circuit),
        noisy_circuit=circuit_to_stim(noisy),
        metadata={"origin": "pre_noised_source"},
    )

    with pytest.raises(ValueError, match="requires the source to compile to identical"):
        Simulator(source).run_noiseless(
            shots=16,
            out_dir=tmp_path / "should_not_write",
            seed=8,
        )

    result = Simulator(source).run(
        shots=16,
        noise=None,
        out_dir=tmp_path / "pre_noised_regular_run",
        seed=8,
    )
    assert result.manifest["noise"]["type"] == "pre_noised_stim_source"
    assert str(result.paths.circuit_ideal.read_text()) != str(result.paths.circuit_noisy_pauli.read_text())


def test_result_loaders_validate_manifest_file_and_sha(tmp_path):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    result = Simulator(builder.build()).run_noiseless(
        shots=8,
        out_dir=tmp_path / "loader_validation",
        seed=4,
    )

    broken_file = dict(result.manifest)
    broken_file["artifacts"] = dict(result.manifest["artifacts"])
    broken_file["artifacts"]["detection_events"] = dict(
        result.manifest["artifacts"]["detection_events"]
    )
    broken_file["artifacts"]["detection_events"]["file"] = "wrong.b8"
    broken = result.__class__(
        paths=result.paths,
        sample_summary_ideal=result.sample_summary_ideal,
        sample_summary_noisy=result.sample_summary_noisy,
        theory_prediction=result.theory_prediction,
        decoder_results=result.decoder_results,
        manifest=broken_file,
    )
    with pytest.raises(ValueError, match="points to"):
        broken.load_detection_events()

    broken_sha = dict(result.manifest)
    broken_sha["artifacts"] = dict(result.manifest["artifacts"])
    broken_sha["artifacts"]["detection_events"] = dict(
        result.manifest["artifacts"]["detection_events"]
    )
    broken_sha["artifacts"]["detection_events"]["sha256"] = "0" * 64
    broken = result.__class__(
        paths=result.paths,
        sample_summary_ideal=result.sample_summary_ideal,
        sample_summary_noisy=result.sample_summary_noisy,
        theory_prediction=result.theory_prediction,
        decoder_results=result.decoder_results,
        manifest=broken_sha,
    )
    with pytest.raises(ValueError, match="sha256 mismatch"):
        broken.load_detection_events()

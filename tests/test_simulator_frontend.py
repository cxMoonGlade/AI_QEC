from __future__ import annotations

import json

import numpy as np
import pytest

from error_coupling_simulator.frontend import b8_io
from error_coupling_simulator.frontend import decoder as m4_decode
from error_coupling_simulator.frontend.circuit_ir import CircuitBuilder, CircuitIR, DetectorDef, GateOp, MeasureOp
from error_coupling_simulator.frontend.noise_spec import (
    NoiseBuilder,
    StimNoiseRule,
    StimPauliNoiseSpec,
    TargetedStimNoiseSpec,
    apply_stim_pauli_noise,
)
from error_coupling_simulator.frontend.simulator import Simulator
from error_coupling_simulator.frontend.stim_source import CompiledCircuit, StimCircuitSource
from error_coupling_simulator.frontend.stim_io import circuit_to_stim, write_stim_circuit


def _single_detector_circuit():
    builder = CircuitBuilder(num_qubits=1, metadata={"code": "unit_test_repetition_leaf"})
    builder.measure(0, key="m0")
    builder.detector("d0", xor=["m0"], coords=(0.0, 0.0))
    builder.observable("logical0", xor=["m0"], index=0)
    return builder.build()


def _detector_only_circuit():
    builder = CircuitBuilder(num_qubits=1, metadata={"code": "unit_test_detector_only"})
    builder.measure(0, key="m0")
    builder.detector("d0", xor=["m0"], coords=(0.0,))
    return builder.build()


def _measurement_only_circuit():
    builder = CircuitBuilder(num_qubits=1, metadata={"code": "unit_test_measurement_only"})
    builder.measure(0, key="m0")
    return builder.build()


def _many_detector_circuit():
    builder = CircuitBuilder(num_qubits=10, metadata={"code": "unit_test_many_records"})
    builder.measure(tuple(range(10)), key=[f"m{i}" for i in range(10)])
    for i in range(10):
        builder.detector(f"d{i}", xor=[f"m{i}"], coords=(float(i),))
    builder.observable("logical0", xor=["m0"], index=0)
    builder.observable("logical1", xor=["m9"], index=1)
    return builder.build()


def test_circuit_ir_exports_keyed_detectors_and_observables_to_stim():
    circuit = _single_detector_circuit()
    stim_circuit = circuit_to_stim(circuit)

    assert stim_circuit.num_detectors == 1
    assert stim_circuit.num_observables == 1
    assert stim_circuit.num_measurements == 1
    text = str(stim_circuit)
    assert "DETECTOR(0, 0) rec[-1]" in text
    assert "OBSERVABLE_INCLUDE(0) rec[-1]" in text


def test_circuit_ir_touches_declared_idle_qubits_and_rejects_record_gateop():
    builder = CircuitBuilder(num_qubits=3)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=["m0"])
    assert circuit_to_stim(builder.build()).num_qubits == 3

    with pytest.raises(ValueError, match="record-affecting"):
        CircuitIR(num_qubits=1, steps=(GateOp("M", (0,)),))

    with pytest.raises(ValueError, match="outside"):
        CircuitIR(num_qubits=1, steps=(GateOp("H", (9,)),))


def test_pauli_noise_projection_preserves_record_schema():
    circuit = _single_detector_circuit()
    noisy = apply_stim_pauli_noise(circuit, StimPauliNoiseSpec(before_measure_flip=0.25))
    stim_circuit = circuit_to_stim(noisy)

    assert stim_circuit.num_detectors == 1
    assert stim_circuit.num_observables == 1
    assert "X_ERROR(0.25) 0" in str(stim_circuit)


def test_targeted_noise_builder_supports_gate_instance_type_all_idle_and_measurement():
    builder = CircuitBuilder(num_qubits=3, metadata={"code": "targeted_noise_smoke"})
    builder.h(0)
    builder.cz((0, 1))
    builder.tick()
    builder.x(2)
    builder.idle(1)
    builder.tick()
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    circuit = builder.build()
    noise = (
        NoiseBuilder()
        .after_gate(0, "X_ERROR", 0.01)
        .after_gate_type("CZ", "DEPOLARIZE", 0.02)
        .after_all_gates("Z_ERROR", 0.03)
        .during_idle("DEPOLARIZE", 0.04)
        .before_measurement("X_ERROR", 0.05)
        .build()
    )

    noisy = apply_stim_pauli_noise(circuit, noise)
    text = str(circuit_to_stim(noisy))

    assert "H 0\nX_ERROR(0.01) 0\nZ_ERROR(0.03) 0" in text
    assert "CZ 0 1\nDEPOLARIZE2(0.02) 0 1\nZ_ERROR(0.03) 0 1" in text
    assert "DEPOLARIZE1(0.04) 2\nTICK" in text
    assert "X 2\nZ_ERROR(0.03) 2\nI 1\nZ_ERROR(0.03) 1\nDEPOLARIZE1(0.04) 0 1\nTICK" in text
    assert "X_ERROR(0.05) 0 1 2\nM 0 1 2" in text
    assert noisy.metadata["noise_projection"]["matched_counts"] == [1, 1, 4, 2, 1]


def test_targeted_noise_builder_rejects_unmatched_required_rules():
    circuit = _single_detector_circuit()
    noise = NoiseBuilder().after_gate_type("CZ", "DEPOLARIZE", 0.02).build()

    with pytest.raises(ValueError, match="matched no circuit operation"):
        apply_stim_pauli_noise(circuit, noise)


def test_targeted_noise_manifest_records_rule_matches(tmp_path):
    noise = NoiseBuilder().before_measurement("X_ERROR", 0.25).build()
    result = Simulator(_single_detector_circuit()).run(
        shots=64,
        noise=noise,
        out_dir=tmp_path / "targeted_noise_manifest",
        seed=12,
    )

    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["noise"]["type"] == "targeted_stim_pauli"
    assert manifest["noise"]["rules"][0]["match_kind"] == "measurement_type"
    assert manifest["noise"]["matched_counts"] == [1]
    assert manifest["noise"]["matched_events"][0][0]["matched_op"] == "M"
    assert manifest["noise"]["matched_events"][0][0]["noise"] == "X_ERROR"
    assert "X_ERROR(0.25) 0" in result.paths.circuit_noisy_pauli.read_text()


def test_targeted_noise_target_filter_is_match_filter_not_insert_override():
    builder = CircuitBuilder(num_qubits=4)
    builder.cz((0, 1))
    builder.cz((2, 3))
    builder.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"))
    circuit = builder.build()
    noise = NoiseBuilder().after_gate_type("CZ", "DEPOLARIZE", 0.02, target_filter=(0, 1)).build()

    noisy = apply_stim_pauli_noise(circuit, noise)
    text = str(circuit_to_stim(noisy))

    assert "CZ 0 1\nDEPOLARIZE2(0.02) 0 1\nCZ 2 3" in text
    assert "DEPOLARIZE2(0.02) 2 3" not in text
    assert noisy.metadata["noise_projection"]["matched_counts"] == [1]
    assert noisy.metadata["noise_projection"]["matched_events"][0][0]["matched_targets"] == [0, 1]


def test_targeted_noise_rejects_unsupported_or_bad_arity_noise():
    builder = CircuitBuilder(num_qubits=2)
    builder.h(0)
    builder.cz((0, 1))
    circuit = builder.build()

    with pytest.raises(ValueError, match="currently supports"):
        NoiseBuilder().after_gate(0, "HERALDED_ERASE", 0.1).build()
    with pytest.raises(ValueError, match="exactly one probability"):
        apply_stim_pauli_noise(
            circuit,
            TargetedStimNoiseSpec(
                (
                    StimNoiseRule(
                        position="after",
                        match_kind="gate_index",
                        gate_index=0,
                        noise="X_ERROR",
                        args=(0.1, 0.2),
                    ),
                )
            ),
        )
    with pytest.raises(ValueError, match="DEPOLARIZE2 requires an even number"):
        apply_stim_pauli_noise(circuit, NoiseBuilder().after_gate(0, "DEPOLARIZE2", 0.1).build())
    with pytest.raises(ValueError, match="idle noise is per-qubit"):
        apply_stim_pauli_noise(circuit, NoiseBuilder().during_idle("DEPOLARIZE2", 0.1).build())


def test_noise_probability_validation_rejects_invalid_values():
    for bad in (-0.1, 1.0, float("inf"), float("nan")):
        with pytest.raises(ValueError, match=r"\[0, 1\)"):
            StimPauliNoiseSpec(before_measure_flip=bad)
        with pytest.raises(ValueError, match=r"\[0, 1\)"):
            NoiseBuilder().after_all_gates("X_ERROR", bad).build()


def test_source_embedded_noise_instruction_is_not_noiseless_circuitir():
    with pytest.raises(ValueError, match="source-embedded noise instruction"):
        CircuitIR(num_qubits=1, steps=(GateOp("X_ERROR", (0,), (0.25,)),))
    with pytest.raises(ValueError, match="source-embedded noise instruction"):
        CircuitIR(
            num_qubits=1,
            steps=(GateOp("X_ERROR", (0,), (0.25,)),),
            metadata={"noise_projection": {"type": "forged_public_metadata"}},
        )
    with pytest.raises(ValueError, match="source-embedded noise instruction"):
        CircuitIR(num_qubits=1, steps=(GateOp("CORRELATED_ERROR", (0,), (0.25,)),))


def test_optional_unmatched_targeted_rule_records_zero_matches():
    circuit = _single_detector_circuit()
    noise = NoiseBuilder().after_gate_type("CZ", "DEPOLARIZE", 0.02, require_match=False).build()
    noisy = apply_stim_pauli_noise(circuit, noise)

    assert noisy.metadata["noise_projection"]["matched_counts"] == [0]
    assert noisy.metadata["noise_projection"]["matched_events"] == [[]]


def test_idle_noise_tick_boundaries_and_touch_semantics_are_pinned():
    builder = CircuitBuilder(num_qubits=3)
    builder.tick()
    builder.reset(0)
    builder.measure(1, key="m1")
    builder.idle(2)
    builder.tick()
    builder.tick()
    circuit = builder.build()
    noise = NoiseBuilder().during_idle("DEPOLARIZE", 0.04, targets=(0, 1, 2)).build()

    noisy = apply_stim_pauli_noise(circuit, noise)
    text = str(circuit_to_stim(noisy))

    assert text.count("DEPOLARIZE1(0.04)") == 3
    assert "DEPOLARIZE1(0.04) 0 1 2\nTICK" in text
    assert "I 2\nDEPOLARIZE1(0.04) 2\nTICK" in text
    assert text.rstrip().endswith("DEPOLARIZE1(0.04) 0 1 2\nTICK")
    assert noisy.metadata["noise_projection"]["matched_counts"] == [3]


def test_simulator_run_writes_stim_dem_b8_and_decoder_artifacts(tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    circuit = _single_detector_circuit()
    result = Simulator(circuit).run(
        shots=256,
        noise=StimPauliNoiseSpec(before_measure_flip=0.25),
        out_dir=tmp_path / "sim_run",
        seed=123,
        decoder="pymatching",
    )

    for path in (
        result.paths.circuit_ideal,
        result.paths.circuit_noisy_pauli,
        result.paths.detector_error_model,
        result.paths.detection_events,
        result.paths.obs_flips_actual,
        result.paths.obs_flips_predicted,
        result.paths.ideal_detection_events,
        result.paths.ideal_obs_flips_actual,
        result.paths.sample_summary_ideal,
        result.paths.sample_summary_noisy,
        result.paths.theory_prediction,
        result.paths.decoder_results,
        result.paths.manifest,
    ):
        assert path.exists(), path

    det = b8_io.unpack_bits(b8_io.read_b8(result.paths.detection_events, 1), 1)
    obs = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_actual, 1), 1)
    pred = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_predicted, 1), 1)
    ideal_det = b8_io.unpack_bits(b8_io.read_b8(result.paths.ideal_detection_events, 1), 1)
    ideal_obs = b8_io.unpack_bits(b8_io.read_b8(result.paths.ideal_obs_flips_actual, 1), 1)

    assert det.shape == (256, 1)
    assert obs.shape == (256, 1)
    assert pred.shape == (256, 1)
    assert np.array_equal(det, obs)
    assert np.array_equal(pred, obs)
    assert not ideal_det.any()
    assert not ideal_obs.any()

    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["schema"] == "qec_twin.simulator_frontend.v1"
    assert manifest["representability"] == "stim_pauli"
    assert manifest["num_detectors"] == 1
    assert manifest["num_observables"] == 1
    assert manifest["noise"]["before_measure_flip"] == 0.25
    assert manifest["record_schema"]["detector_bit_width"] == 1
    assert manifest["record_schema"]["observable_bit_width"] == 1
    assert manifest["artifacts"]["sample_summary_ideal"]["file"] == "sample_summary_ideal.json"
    assert manifest["artifacts"]["sample_summary_noisy"]["file"] == "sample_summary_noisy.json"
    assert manifest["artifacts"]["theory_prediction"]["file"] == "theory_prediction.json"
    assert manifest["artifacts"]["obs_flips_predicted"]["file"] == "obs_flips_predicted.b8"
    assert manifest["artifacts"]["detector_error_model"]["decompose_errors"] is True
    assert manifest["artifacts"]["detection_events"]["bits_per_shot"] == 1
    assert manifest["artifacts"]["obs_flips_actual"]["bits_per_shot"] == 1
    assert manifest["artifacts"]["obs_flips_predicted"]["bits_per_shot"] == 1
    assert manifest["decoder_provenance"]["pinned_version"] == m4_decode.PYMATCHING_PIN

    ideal_summary = json.loads(result.paths.sample_summary_ideal.read_text())
    noisy_summary = json.loads(result.paths.sample_summary_noisy.read_text())
    theory = json.loads(result.paths.theory_prediction.read_text())
    assert ideal_summary["estimator"] == "finite_shot_sample"
    assert noisy_summary["estimator"] == "finite_shot_sample"
    assert theory == {
        "available": False,
        "reason": (
            "stim detector sampling frontend currently reports finite-shot summaries; "
            "exact/analytic theory predictions require a backend-declared method"
        ),
    }

    decoder = json.loads(result.paths.decoder_results.read_text())
    assert decoder["num_observables"] == 1
    assert decoder["any_observable_ler"] == 0.0
    assert "error" in result.paths.detector_error_model.read_text()

    roundtrip_pred = m4_decode.decode_dem(result.paths.detector_error_model, det)
    assert np.array_equal(roundtrip_pred, pred)

    packed_det = b8_io.read_b8(result.paths.detection_events, 1)
    with pytest.raises(ValueError, match="ambiguous"):
        m4_decode.decode_dem(result.paths.detector_error_model, packed_det)


def test_decoder_predictions_are_not_copied_from_actual_observables(monkeypatch, tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    def fake_decode_dem(dem, dets):
        return np.ones((np.asarray(dets).shape[0], 1), dtype=np.uint8)

    monkeypatch.setattr(
        "error_coupling_simulator.frontend.simulator.m4_decode.decode_dem",
        fake_decode_dem,
    )
    result = Simulator(_single_detector_circuit()).run(
        shots=32,
        noise=None,
        out_dir=tmp_path / "sentinel_decoder",
        seed=123,
        decoder="pymatching",
    )

    obs = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_actual, 1), 1)
    pred = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_predicted, 1), 1)
    assert not obs.any()
    assert pred.all()
    decoder = json.loads(result.paths.decoder_results.read_text())
    assert decoder["any_observable_ler"] == 1.0


def test_zero_observable_b8_artifacts_are_omitted_with_schema(tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    result = Simulator(_detector_only_circuit()).run(
        shots=32,
        noise=StimPauliNoiseSpec(before_measure_flip=0.25),
        out_dir=tmp_path / "zero_obs",
        seed=4,
        decoder="pymatching",
    )

    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["num_observables"] == 0
    assert manifest["record_schema"]["observable_bit_width"] == 0
    assert manifest["artifacts"]["obs_flips_actual"]["file"] is None
    assert manifest["artifacts"]["ideal_obs_flips_actual"]["file"] is None
    assert manifest["artifacts"]["obs_flips_predicted"]["file"] is None
    assert not result.paths.obs_flips_actual.exists()
    assert not result.paths.ideal_obs_flips_actual.exists()
    assert not result.paths.obs_flips_predicted.exists()
    det = b8_io.unpack_bits(b8_io.read_b8(result.paths.detection_events, 1), 1)
    assert det.shape == (32, 1)


def test_zero_detector_and_zero_observable_b8_artifacts_are_omitted(tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    result = Simulator(_measurement_only_circuit()).run(
        shots=16,
        noise=None,
        out_dir=tmp_path / "zero_det_zero_obs",
        seed=3,
        decoder="pymatching",
    )

    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["num_detectors"] == 0
    assert manifest["num_observables"] == 0
    for key in (
        "detection_events",
        "obs_flips_actual",
        "obs_flips_predicted",
        "ideal_detection_events",
        "ideal_obs_flips_actual",
    ):
        assert manifest["artifacts"][key]["file"] is None
        assert manifest["artifacts"][key]["bits_per_shot"] == 0
    assert not result.paths.detection_events.exists()
    assert not result.paths.obs_flips_actual.exists()
    assert result.decoder_results["num_observables"] == 0


def test_multibyte_b8_schema_and_decoder_roundtrip(tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    result = Simulator(_many_detector_circuit()).run(
        shots=64,
        noise=StimPauliNoiseSpec(before_measure_flip=0.25),
        out_dir=tmp_path / "many_records",
        seed=9,
        decoder="pymatching",
    )
    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["num_detectors"] == 10
    assert manifest["num_observables"] == 2
    assert manifest["artifacts"]["detection_events"]["bits_per_shot"] == 10
    assert manifest["artifacts"]["detection_events"]["packed_bytes_per_shot"] == 2
    assert manifest["artifacts"]["obs_flips_actual"]["bits_per_shot"] == 2
    assert manifest["artifacts"]["obs_flips_actual"]["packed_bytes_per_shot"] == 1

    det = b8_io.unpack_bits(b8_io.read_b8(result.paths.detection_events, 10), 10)
    obs = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_actual, 2), 2)
    pred = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_predicted, 2), 2)
    assert det.shape == (64, 10)
    assert obs.shape == (64, 2)
    assert pred.shape == (64, 2)
    assert np.array_equal(m4_decode.decode_dem(result.paths.detector_error_model, det), pred)


def test_stim_circuit_source_uses_same_artifact_path(tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    circuit = _single_detector_circuit()
    noisy_ir = apply_stim_pauli_noise(circuit, StimPauliNoiseSpec(before_measure_flip=0.25))
    source = StimCircuitSource(
        ideal_circuit=circuit_to_stim(circuit),
        noisy_circuit=circuit_to_stim(noisy_ir),
        metadata={"origin": "stim_native_test"},
    )

    result = Simulator(source).run(
        shots=128,
        noise=None,
        out_dir=tmp_path / "stim_source_run",
        seed=321,
        decoder="pymatching",
    )

    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["source_type"] == "stim_circuit"
    assert manifest["circuit_metadata"] == {"origin": "stim_native_test"}
    assert manifest["representability"] == "stim_pauli"
    assert manifest["noise"]["type"] == "pre_noised_stim_source"
    assert manifest["noise"]["placement"] == "external"

    det = b8_io.unpack_bits(b8_io.read_b8(result.paths.detection_events, 1), 1)
    obs = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_actual, 1), 1)
    pred = b8_io.unpack_bits(b8_io.read_b8(result.paths.obs_flips_predicted, 1), 1)
    assert np.array_equal(det, obs)
    assert np.array_equal(pred, obs)


def test_stim_circuit_source_from_file_records_hashes(tmp_path):
    circuit = _single_detector_circuit()
    ideal_path = tmp_path / "ideal.stim"
    noisy_path = tmp_path / "noisy.stim"
    write_stim_circuit(circuit_to_stim(circuit), ideal_path)
    write_stim_circuit(
        circuit_to_stim(apply_stim_pauli_noise(circuit, StimPauliNoiseSpec(before_measure_flip=0.25))),
        noisy_path,
    )

    source = StimCircuitSource.from_file(
        ideal_path, noisy_path=noisy_path, metadata={"origin": "file_roundtrip"}
    )
    result = Simulator(source).run(
        shots=32,
        noise=None,
        out_dir=tmp_path / "from_file",
        seed=5,
    )
    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["source_type"] == "stim_circuit"
    assert manifest["circuit_metadata"]["origin"] == "file_roundtrip"
    assert manifest["circuit_metadata"]["ideal_path"] == str(ideal_path)
    assert len(manifest["circuit_metadata"]["ideal_sha256"]) == 64
    assert manifest["circuit_metadata"]["noisy_path"] == str(noisy_path)
    assert len(manifest["circuit_metadata"]["noisy_sha256"]) == 64
    assert manifest["noise"]["type"] == "pre_noised_stim_source"


def test_same_seed_produces_identical_stable_artifacts(tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    circuit = _many_detector_circuit()
    kwargs = dict(
        shots=64,
        noise=StimPauliNoiseSpec(before_measure_flip=0.25),
        seed=99,
        decoder="pymatching",
    )
    a = Simulator(circuit).run(out_dir=tmp_path / "run_a", **kwargs)
    b = Simulator(circuit).run(out_dir=tmp_path / "run_b", **kwargs)

    for path_a, path_b in (
        (a.paths.circuit_ideal, b.paths.circuit_ideal),
        (a.paths.circuit_noisy_pauli, b.paths.circuit_noisy_pauli),
        (a.paths.detector_error_model, b.paths.detector_error_model),
        (a.paths.detection_events, b.paths.detection_events),
        (a.paths.obs_flips_actual, b.paths.obs_flips_actual),
        (a.paths.obs_flips_predicted, b.paths.obs_flips_predicted),
        (a.paths.sample_summary_ideal, b.paths.sample_summary_ideal),
        (a.paths.sample_summary_noisy, b.paths.sample_summary_noisy),
        (a.paths.theory_prediction, b.paths.theory_prediction),
        (a.paths.decoder_results, b.paths.decoder_results),
    ):
        assert path_a.read_bytes() == path_b.read_bytes()

    c = Simulator(circuit).run(
        shots=64,
        noise=StimPauliNoiseSpec(before_measure_flip=0.25),
        out_dir=tmp_path / "run_c",
        seed=100,
        decoder="pymatching",
    )
    assert a.paths.detection_events.read_bytes() != c.paths.detection_events.read_bytes()


def test_compiled_circuit_can_enter_simulator_directly(tmp_path):
    circuit = _single_detector_circuit()
    source = StimCircuitSource(
        ideal_circuit=circuit_to_stim(circuit),
        noisy_circuit=circuit_to_stim(
            apply_stim_pauli_noise(circuit, StimPauliNoiseSpec(before_measure_flip=0.25))
        ),
        metadata={"origin": "compiled_test"},
    )

    result = Simulator(source.compile()).run(
        shots=64,
        noise=None,
        out_dir=tmp_path / "compiled_run",
        seed=123,
    )

    manifest = json.loads(result.paths.manifest.read_text())
    assert manifest["source_type"] == "stim_circuit"
    assert manifest["circuit_metadata"] == {"origin": "compiled_test"}


def test_compiled_circuit_rejects_schema_mismatch_and_truth_laundering():
    circuit = _single_detector_circuit()
    ideal = circuit_to_stim(circuit)
    noisy_without_observable = circuit_to_stim(_detector_only_circuit())

    with pytest.raises(ValueError, match="identical record schema"):
        CompiledCircuit(
            ideal_circuit=ideal,
            noisy_circuit=noisy_without_observable,
            metadata={},
            source_type="bad_schema",
        )

    with pytest.raises(ValueError, match="unsupported frontend representability"):
        CompiledCircuit(
            ideal_circuit=ideal,
            noisy_circuit=ideal,
            metadata={},
            source_type="launder",
            representability="analog_joint_l_window",
        )

    with pytest.raises(ValueError, match="evaluator_only"):
        CompiledCircuit(
            ideal_circuit=ideal,
            noisy_circuit=ideal,
            metadata={},
            source_type="bad_sidecar",
            evaluator_sidecars=({"name": "truth", "path": "truth.json", "visibility": "learner"},),
        )

    with pytest.raises(ValueError, match="evaluator truth"):
        CompiledCircuit(
            ideal_circuit=ideal,
            noisy_circuit=ideal,
            metadata={"kraus_stack": "secret.npz"},
            source_type="bad_metadata",
        )

    with pytest.raises(ValueError, match="evaluator truth"):
        CompiledCircuit(
            ideal_circuit=ideal,
            noisy_circuit=ideal,
            metadata={},
            source_type="bad_noise_manifest",
            noise_manifest={"channel_truth": "secret.npz"},
        )

    with pytest.raises(ValueError, match="evaluator truth"):
        CircuitIR(
            num_qubits=1,
            steps=(MeasureOp("M", (0,), ("m0",)),),
            metadata={"channel_truth": {"do_not_publish": True}},
        )


def test_raw_stim_source_rejects_ambiguous_noise_placement(tmp_path):
    source = StimCircuitSource(ideal_circuit=circuit_to_stim(_single_detector_circuit()))

    with pytest.raises(NotImplementedError, match="location-aware compiler"):
        Simulator(source).run(
            shots=8,
            noise=StimPauliNoiseSpec(before_measure_flip=0.25),
            out_dir=tmp_path / "should_stop_before_sampling",
            seed=0,
        )


def test_noise_spec_normalizes_numeric_inputs():
    noise = StimPauliNoiseSpec(before_measure_flip="0.25")
    assert isinstance(noise.before_measure_flip, float)
    assert noise.before_measure_flip == 0.25


def test_run_clears_stale_optional_b8(tmp_path):
    pytest.importorskip("pymatching", reason="simulator frontend decode smoke uses PyMatching")

    out_dir = tmp_path / "stale"
    first = Simulator(_single_detector_circuit()).run(
        shots=16,
        noise=StimPauliNoiseSpec(before_measure_flip=0.25),
        out_dir=out_dir,
        seed=1,
        decoder="pymatching",
    )
    assert first.paths.obs_flips_predicted.exists()

    second = Simulator(_detector_only_circuit()).run(
        shots=16,
        noise=StimPauliNoiseSpec(before_measure_flip=0.25),
        out_dir=out_dir,
        seed=1,
        decoder="pymatching",
    )
    manifest = json.loads(second.paths.manifest.read_text())
    assert manifest["artifacts"]["obs_flips_predicted"]["file"] is None
    assert not second.paths.obs_flips_predicted.exists()

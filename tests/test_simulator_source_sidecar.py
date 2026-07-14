from __future__ import annotations

import json

import numpy as np
import pytest

from qec_twin.mechanisms import RTNSource
from qec_twin.simulator import (
    CircuitBuilder,
    Simulator,
    SourceTimelineBinding,
    XZZXCodeSpec,
    compile_code_spec,
)
from qec_twin.simulator.artifacts import file_sha256
from qec_twin.simulator.source_sidecar import load_source_timeline_from_manifest


def test_simulator_run_writes_replayable_axis2_source_sidecar(tmp_path):
    spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
    circuit = compile_code_spec(spec)
    timeline = RTNSource(amplitude_radns=2.0e-4, gamma_per_cycle=0.1).sample(seed=7, n_cycles=2)

    result = Simulator(circuit).run(
        shots=32,
        out_dir=tmp_path / "xzzx_with_source",
        source_timeline=timeline,
        seed=9,
    )
    manifest = json.loads(result.paths.manifest.read_text())

    assert manifest["source_binding"]["cycle_binding"] == "qec_round"
    assert manifest["source_binding"]["execution_status"]["applied_to_stim_records"] is False
    assert manifest["source_binding"]["execution_status"]["stim_dem_modified"] is False
    assert "source_timeline" not in manifest["source_binding"]
    assert manifest["artifacts"]["source_timeline"]["visibility"] == "evaluator_only"
    assert manifest["artifacts"]["source_timeline_binding"]["file"] == "source_timeline_binding.json"
    assert manifest["evaluator_sidecars"][0]["name"] == "axis2_source_timeline"
    assert manifest["evaluator_sidecars"][0]["applied_to_records"] is False
    binding_manifest = json.loads((result.paths.out_dir / "source_timeline_binding.json").read_text())
    assert "source_timeline" in binding_manifest

    loaded = result.load_source_timeline()
    np.testing.assert_array_equal(loaded.payload_series("z_radns"), timeline.payload_series("z_radns"))
    np.testing.assert_array_equal(loaded.latent_series("rtn_state"), timeline.latent_series("rtn_state"))


def test_qec_round_source_binding_rejects_mismatched_cycle_count(tmp_path):
    spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
    circuit = compile_code_spec(spec)
    out_dir = tmp_path / "bad_source_cycles"
    valid = RTNSource().sample(seed=2, n_cycles=2)
    Simulator(circuit).run(shots=8, out_dir=out_dir, source_timeline=valid, seed=4)
    assert (out_dir / "manifest.json").exists()

    timeline = RTNSource().sample(seed=3, n_cycles=3)

    with pytest.raises(ValueError, match="does not match CodeSpec rounds"):
        Simulator(circuit).run(
            shots=8,
            out_dir=out_dir,
            source_timeline=timeline,
            source_binding=SourceTimelineBinding(cycle_binding="qec_round"),
            seed=4,
        )
    assert not (out_dir / "manifest.json").exists()
    assert not (out_dir / "source_timeline.npz").exists()


def test_hand_built_circuit_defaults_source_binding_to_external_cycle(tmp_path):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    timeline = RTNSource().sample(seed=5, n_cycles=4)

    result = Simulator(builder.build()).run(
        shots=8,
        out_dir=tmp_path / "manual_with_source",
        source_timeline=timeline,
        seed=6,
    )

    assert result.manifest["source_binding"]["cycle_binding"] == "external_cycle"
    assert result.manifest["source_binding"]["inferred_context"]["code_rounds"] is None


def test_run_noiseless_accepts_source_sidecar(tmp_path):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    timeline = RTNSource().sample(seed=10, n_cycles=1)

    result = Simulator(builder.build()).run_noiseless(
        shots=4,
        out_dir=tmp_path / "noiseless_with_source",
        source_timeline=timeline,
        seed=11,
    )

    assert result.manifest["noise"] is None
    assert result.manifest["source_binding"]["cycle_binding"] == "external_cycle"
    np.testing.assert_array_equal(result.load_source_timeline().payload_series("z_radns"), timeline.payload_series("z_radns"))


def test_source_binding_rejects_unimplemented_semantics():
    with pytest.raises(NotImplementedError, match="continuous_acquisition"):
        SourceTimelineBinding(shot_binding="continuous_acquisition")
    with pytest.raises(NotImplementedError, match="schedule_windows"):
        SourceTimelineBinding(schedule_windows=({"name": "idle"},))
    with pytest.raises(ValueError, match="payload_keys"):
        SourceTimelineBinding(payload_keys="z_radns")


def test_source_sidecar_loader_rejects_path_and_hash_tampering(tmp_path):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    timeline = RTNSource().sample(seed=12, n_cycles=1)
    result = Simulator(builder.build()).run(
        shots=4,
        out_dir=tmp_path / "tamper",
        source_timeline=timeline,
        seed=13,
    )

    escaped = dict(result.manifest)
    escaped["artifacts"] = dict(result.manifest["artifacts"])
    escaped["artifacts"]["source_timeline"] = dict(result.manifest["artifacts"]["source_timeline"])
    escaped["artifacts"]["source_timeline"]["file"] = "../source_timeline.npz"
    with pytest.raises(ValueError, match="relative basename"):
        load_source_timeline_from_manifest(result.paths.out_dir, escaped)

    missing_sha = dict(result.manifest)
    missing_sha["artifacts"] = dict(result.manifest["artifacts"])
    missing_sha["artifacts"]["source_timeline"] = dict(result.manifest["artifacts"]["source_timeline"])
    missing_sha["artifacts"]["source_timeline"].pop("sha256")
    with pytest.raises(ValueError, match="sha256"):
        load_source_timeline_from_manifest(result.paths.out_dir, missing_sha)

    binding_path = result.paths.out_dir / "source_timeline_binding.json"
    binding_path.write_text(binding_path.read_text() + "\n")
    with pytest.raises(ValueError, match="source_timeline_binding sha256 mismatch"):
        result.load_source_timeline()


def test_source_timeline_sidecar_does_not_change_stim_dem_or_b8_outputs(tmp_path):
    spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
    circuit = compile_code_spec(spec)
    timeline = RTNSource().sample(seed=14, n_cycles=2)
    plain = Simulator(circuit).run(shots=16, out_dir=tmp_path / "plain", seed=15)
    sourced = Simulator(circuit).run(
        shots=16,
        out_dir=tmp_path / "sourced",
        source_timeline=timeline,
        seed=15,
    )

    for attr in (
        "circuit_ideal",
        "circuit_noisy_pauli",
        "detector_error_model",
        "detection_events",
        "obs_flips_actual",
        "ideal_detection_events",
        "ideal_obs_flips_actual",
    ):
        assert file_sha256(getattr(sourced.paths, attr)) == file_sha256(getattr(plain.paths, attr))
    for result in (plain, sourced):
        assert result.manifest["artifacts"]["obs_flips_predicted"]["omitted_reason"] == (
            "decoder_not_requested"
        )
        assert not result.paths.obs_flips_predicted.exists()


def test_simulator_rejects_non_integral_shots(tmp_path):
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    with pytest.raises(ValueError, match="positive integer"):
        Simulator(builder.build()).run(shots=3.9, out_dir=tmp_path / "bad_shots")
    assert not (tmp_path / "bad_shots" / "manifest.json").exists()


def test_source_sidecar_files_are_cleared_when_rerunning_without_source(tmp_path):
    out_dir = tmp_path / "rerun"
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    circuit = builder.build()
    timeline = RTNSource().sample(seed=8, n_cycles=1)

    Simulator(circuit).run(shots=4, out_dir=out_dir, source_timeline=timeline, seed=1)
    assert (out_dir / "source_timeline.npz").exists()
    assert (out_dir / "source_timeline_binding.json").exists()

    result = Simulator(circuit).run(shots=4, out_dir=out_dir, seed=2)
    assert not (out_dir / "source_timeline.npz").exists()
    assert not (out_dir / "source_timeline_binding.json").exists()
    assert "source_timeline" not in result.manifest["artifacts"]
    assert result.manifest["source_binding"] is None

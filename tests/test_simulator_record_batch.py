from __future__ import annotations

import numpy as np
import pytest
import stim

from error_coupling_simulator.carrier import RecordBatch
from error_coupling_simulator.frontend.circuit_ir import CircuitBuilder
from error_coupling_simulator.frontend.simulator import Simulator
from error_coupling_simulator.frontend.stim_source import StimCircuitSource


def test_default_stim_run_emits_record_without_optional_decoder(
    monkeypatch,
    tmp_path,
) -> None:
    from error_coupling_simulator.frontend import simulator as simulator_module

    def forbidden_decode(*_args, **_kwargs):
        raise AssertionError("decoder must not run for the record-first default")

    monkeypatch.setattr(simulator_module.m4_decode, "decode_dem", forbidden_decode)

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    builder.observable("logical0", xor=("m0",), index=0)

    result = Simulator(builder.build()).run_noiseless(
        shots=8,
        out_dir=tmp_path / "record_batch",
        seed=5,
    )
    record = result.load_record_batch()

    assert isinstance(record, RecordBatch)
    np.testing.assert_array_equal(record.det, result.load_detection_events())
    np.testing.assert_array_equal(record.obs, result.load_observable_flips())
    assert record.provenance["backend"] == "stim"
    assert record.provenance["record_semantics"] == "temporal_detector_events"
    assert result.manifest["decoder"] is None
    assert result.manifest["decoder_provenance"] is None
    assert result.decoder_results is None
    assert result.sample_summary_noisy["decoder"] is None
    assert result.manifest["artifacts"]["obs_flips_predicted"] == {
        "file": None,
        "bits_per_shot": 1,
        "packed_bytes_per_shot": 1,
        "omitted_reason": "decoder_not_requested",
    }
    assert result.manifest["artifacts"]["decoder_results"] == {
        "file": None,
        "omitted_reason": "decoder_not_requested",
    }
    assert not result.paths.obs_flips_predicted.exists()
    assert not result.paths.decoder_results.exists()
    with pytest.raises(ValueError, match="decoder_not_requested"):
        result.load_predicted_observable_flips()


def test_decoder_off_rerun_clears_stale_optional_decoder_artifacts(tmp_path) -> None:
    out_dir = tmp_path / "stale_decoder"
    out_dir.mkdir()
    (out_dir / "obs_flips_predicted.b8").write_bytes(b"\xff")
    (out_dir / "decoder_results.json").write_text("{}\n")

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    builder.observable("logical0", xor=("m0",), index=0)

    result = Simulator(builder.build()).run_noiseless(
        shots=4,
        out_dir=out_dir,
        seed=1,
    )

    assert result.manifest["decoder"] is None
    assert not result.paths.obs_flips_predicted.exists()
    assert not result.paths.decoder_results.exists()


@pytest.mark.parametrize(
    "decoder",
    ["unknown", [], {}, np.array(["pymatching"], dtype=object)],
    ids=("unknown_name", "list", "dict", "array"),
)
def test_frontend_rejects_unknown_decoder_before_writing(tmp_path, decoder) -> None:
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    out_dir = tmp_path / "unknown_decoder"

    with pytest.raises(ValueError, match="None or 'pymatching'"):
        Simulator(builder.build()).run(
            shots=4,
            out_dir=out_dir,
            decoder=decoder,
        )

    assert not out_dir.exists()


def test_record_only_run_preserves_nongraphlike_hyperedge_dem(tmp_path) -> None:
    ideal = stim.Circuit(
        "R 0 1 2\n"
        "M 0 1 2\n"
        "DETECTOR rec[-3]\n"
        "DETECTOR rec[-2]\n"
        "DETECTOR rec[-1]\n"
    )
    noisy = stim.Circuit(
        "R 0 1 2\n"
        "E(0.1) X0 X1 X2\n"
        "M 0 1 2\n"
        "DETECTOR rec[-3]\n"
        "DETECTOR rec[-2]\n"
        "DETECTOR rec[-1]\n"
    )

    result = Simulator(StimCircuitSource(ideal, noisy)).run(
        shots=16,
        out_dir=tmp_path / "nongraphlike_record",
        seed=11,
    )

    assert result.load_record_batch().det.shape == (16, 3)
    assert "D0 D1 D2" in result.paths.detector_error_model.read_text()
    assert result.manifest["artifacts"]["detector_error_model"]["decompose_errors"] is False

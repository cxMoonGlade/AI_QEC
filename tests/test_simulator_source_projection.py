from __future__ import annotations

import json
import math

import mpmath
import numpy as np
import pytest

from error_coupling_simulator.source import RTNSource, SourceTimeline
from error_coupling_simulator.frontend import (
    CircuitBuilder,
    Simulator,
    SourceTimelineBinding,
    SourceStimPauliProjectionSpec,
    SourceStimPauliRule,
    XZZXCodeSpec,
    compile_code_spec,
)
from error_coupling_simulator.frontend.artifacts import file_sha256


def _two_measurement_circuit():
    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=("m0",))
    builder.tick()
    builder.measure(0, key="m1")
    builder.detector("d1", xor=("m0", "m1"))
    return builder.build()


def test_source_pauli_projection_changes_records_and_writes_source_sidecar(tmp_path):
    circuit = _two_measurement_circuit()
    timeline = SourceTimeline(
        name="measurement_flip_probability",
        n_cycles=2,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([0.45, 0.0], dtype=np.float64)},
        latent={"state": np.asarray([1, 0], dtype=np.int8)},
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M",
                noise="X_ERROR",
                payload_key="p",
                map_kind="payload_probability",
            ),
        ),
    )

    plain = Simulator(circuit).run(shots=512, out_dir=tmp_path / "plain", seed=17)
    sourced = Simulator(circuit).run(shots=512, out_dir=tmp_path / "sourced", noise=noise, seed=17)

    assert sourced.manifest["noise"]["type"] == "stim_pauli_source_projection"
    assert sourced.manifest["noise"]["representability"] == "reduced_pauli_projection_not_analog_truth"
    assert sourced.manifest["noise"]["matched_counts"] == [2]
    assert sourced.manifest["noise"]["source"]["cycle_binding"] == "circuit_tick"
    assert sourced.manifest["source_binding"]["cycle_binding"] == "circuit_tick"
    assert sourced.manifest["source_binding"]["execution_status"]["applied_to_stim_records"] is True
    assert sourced.manifest["source_binding"]["execution_status"]["stim_dem_modified"] is True
    assert sourced.manifest["evaluator_sidecars"][0]["name"] == "axis2_source_timeline"
    assert sourced.manifest["evaluator_sidecars"][0]["applied_to_records"] is True
    assert "matched_events" not in sourced.manifest["noise"]
    assert "source_timeline" not in sourced.manifest["noise"]
    assert "payload_key" not in json.dumps(sourced.manifest["noise"])
    binding_manifest = json.loads((sourced.paths.out_dir / "source_timeline_binding.json").read_text())
    audit = binding_manifest["projection_audit"]
    assert audit["visibility"] == "evaluator_only"
    assert audit["matched_events"][0][0]["source_cycle_binding"] == "circuit_tick"
    assert audit["matched_events"][0][0]["projected_probability"] == pytest.approx(0.45)
    assert audit["matched_events"][0][0]["payload_key"] == "p"
    assert "X_ERROR(0.45)" in sourced.paths.circuit_noisy_pauli.read_text()
    assert file_sha256(sourced.paths.detector_error_model) != file_sha256(plain.paths.detector_error_model)
    assert file_sha256(sourced.paths.detection_events) != file_sha256(plain.paths.detection_events)
    np.testing.assert_array_equal(sourced.load_source_timeline().payload_series("p"), timeline.payload_series("p"))


def test_source_projection_auto_sidecar_rejects_mismatched_run_timeline(tmp_path):
    circuit = _two_measurement_circuit()
    out_dir = tmp_path / "mismatch"
    noise_timeline = RTNSource(amplitude_radns=1.0e-4, gamma_per_cycle=0.0).sample(seed=1, n_cycles=2)
    other_timeline = RTNSource(amplitude_radns=2.0e-4, gamma_per_cycle=0.0).sample(seed=1, n_cycles=2)
    noise = SourceStimPauliProjectionSpec(
        timeline=noise_timeline,
        rules=(
            SourceStimPauliRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M",
                noise="X_ERROR",
                payload_key="z_radns",
                base_p=0.05,
                sensitivity=0.1,
                z_scale=1.0e-4,
            ),
        ),
    )
    Simulator(circuit).run(shots=8, out_dir=out_dir, seed=2)
    assert (out_dir / "manifest.json").exists()

    with pytest.raises(ValueError, match="do not match"):
        Simulator(circuit).run(
            shots=8,
            out_dir=out_dir,
            noise=noise,
            source_timeline=other_timeline,
            seed=2,
        )
    assert not (out_dir / "manifest.json").exists()


def test_source_projection_logit_rule_executes_in_registered_acceptance(tmp_path):
    circuit = _two_measurement_circuit()
    timeline = SourceTimeline(
        name="finite_logit_projection",
        n_cycles=2,
        cycle_time_ns=1_000.0,
        payload={"z_radns": np.asarray([1.0e-4, -1.0e-4], dtype=np.float64)},
    )
    rule = SourceStimPauliRule(
        position="before",
        match_kind="measurement_type",
        measure_name="M",
        noise="X_ERROR",
        payload_key="z_radns",
        base_p=0.05,
        sensitivity=0.1,
        z_scale=1.0e-4,
    )
    result = Simulator(circuit).run(
        shots=32,
        out_dir=tmp_path / "logit_projection",
        noise=SourceStimPauliProjectionSpec(timeline=timeline, rules=(rule,)),
        seed=23,
    )

    expected = []
    base_logit = math.log(0.05) - math.log1p(-0.05)
    for shift in (0.1, -0.1):
        y = base_logit + shift
        if y < 0.0:
            exp_y = math.exp(y)
            expected.append(exp_y / (1.0 + exp_y))
        else:
            exp_neg_y = math.exp(-y)
            expected.append(1.0 - exp_neg_y / (1.0 + exp_neg_y))

    binding = json.loads((result.paths.out_dir / "source_timeline_binding.json").read_text())
    events = binding["projection_audit"]["matched_events"][0]
    assert [event["projected_probability"] for event in events] == pytest.approx(expected)
    noisy_text = result.paths.circuit_noisy_pauli.read_text()
    assert noisy_text.count("X_ERROR(") == 2


def test_source_projection_logit_large_opposite_terms_match_exact_float_oracle():
    """The frontend map must not round a cancellation-sensitive logit to 0.5."""

    base_p = float.fromhex("0x0.0000000000001p-1022")
    shift = float.fromhex("0x1.74385446d71c3p+9")
    timeline = SourceTimeline(
        name="cancellation_sensitive_logit",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"z": np.asarray([1.0], dtype=np.float64)},
    )
    rule = SourceStimPauliRule(
        position="before",
        match_kind="measurement_type",
        measure_name="M",
        noise="X_ERROR",
        payload_key="z",
        base_p=base_p,
        sensitivity=shift,
        z_scale=1.0,
    )
    with mpmath.workdps(200):
        p_num, p_den = base_p.as_integer_ratio()
        s_num, s_den = shift.as_integer_ratio()
        p_exact = mpmath.mpf(p_num) / p_den
        shift_exact = mpmath.mpf(s_num) / s_den
        oracle = float(
            1
            / (
                1
                + mpmath.exp(
                    -(mpmath.log(p_exact / (1 - p_exact)) + shift_exact)
                )
            )
        )
    got = rule.probability_for(timeline, cycle_index=0, targets=(0,))
    assert abs(got - oracle) <= math.ulp(oracle)


def test_source_projection_logit_uses_exact_float_domain_at_cancellation_boundary():
    """The frontend must neither reject an exact inside point nor accept an exact outside point."""

    min_open = float.fromhex("0x0.0000000000001p-1022")
    max_open = float.fromhex("0x1.fffffffffffffp-1")
    cancelling_shift = float.fromhex("0x1.8696a3c1fe543p+9")
    timeline = SourceTimeline(
        name="endpoint_cancellation",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"z": np.asarray([1.0], dtype=np.float64)},
    )

    def probability(base_p: float, shift: float) -> float:
        rule = SourceStimPauliRule(
            position="before",
            match_kind="measurement_type",
            measure_name="M",
            noise="X_ERROR",
            payload_key="z",
            base_p=base_p,
            sensitivity=shift,
            z_scale=1.0,
        )
        return rule.probability_for(timeline, cycle_index=0, targets=(0,))

    assert probability(min_open, cancelling_shift) == max_open
    assert probability(max_open, -cancelling_shift) == min_open
    outside_shift = math.nextafter(cancelling_shift, math.inf)
    with pytest.raises(ValueError, match="outside the representable float64 open interval"):
        probability(min_open, outside_shift)
    with pytest.raises(ValueError, match="outside the representable float64 open interval"):
        probability(max_open, -outside_shift)


def test_source_projection_recovers_representable_shift_from_overflowing_ratio():
    """Finite factors whose naive division overflows may still define a finite shift."""

    min_subnormal = math.nextafter(0.0, 1.0)
    timeline = SourceTimeline(
        name="recoverable_product_ratio",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"z": np.asarray([1.0], dtype=np.float64)},
    )
    rule = SourceStimPauliRule(
        position="before",
        match_kind="measurement_type",
        measure_name="M",
        noise="X_ERROR",
        payload_key="z",
        base_p=0.2,
        sensitivity=min_subnormal,
        z_scale=min_subnormal,
    )
    expected = 1.0 / (1.0 + math.exp(-(math.log(0.2 / 0.8) + 1.0)))
    got = rule.probability_for(timeline, cycle_index=0, targets=(0,))
    assert abs(got - expected) <= math.ulp(expected)


def test_source_projection_rejects_short_timeline_by_default(tmp_path):
    circuit = _two_measurement_circuit()
    timeline = SourceTimeline(
        name="one_cycle_probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([0.2], dtype=np.float64)},
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M",
                noise="X_ERROR",
                payload_key="p",
                map_kind="payload_probability",
                require_match=True,
            ),
        ),
    )

    with pytest.raises(ValueError, match="not fully covered"):
        Simulator(circuit).run(shots=32, out_dir=tmp_path / "short_source", noise=noise, seed=3)
    assert not (tmp_path / "short_source" / "manifest.json").exists()


def test_source_projection_can_optionally_skip_out_of_timeline_matches(tmp_path):
    circuit = _two_measurement_circuit()
    timeline = SourceTimeline(
        name="one_cycle_probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([0.2], dtype=np.float64)},
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M",
                noise="X_ERROR",
                payload_key="p",
                map_kind="payload_probability",
                require_match=False,
            ),
        ),
    )

    result = Simulator(circuit).run(shots=32, out_dir=tmp_path / "optional_short_source", noise=noise, seed=3)

    assert result.manifest["noise"]["matched_counts"] == [1]
    assert result.manifest["noise"]["skipped_outside_timeline"] == [1]
    assert result.paths.circuit_noisy_pauli.read_text().count("X_ERROR") == 1


def test_source_projection_splits_site_payloads_for_bundled_measurements(tmp_path):
    builder = CircuitBuilder(num_qubits=2)
    builder.measure((0, 1), key=("m0", "m1"))
    builder.detector("d0", xor=("m0",))
    builder.detector("d1", xor=("m1",))
    circuit = builder.build()
    timeline = SourceTimeline(
        name="site_probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([[0.2, 0.4]], dtype=np.float64)},
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M",
                noise="X_ERROR",
                payload_key="p",
                map_kind="payload_probability",
            ),
        ),
    )

    result = Simulator(circuit).run(shots=64, out_dir=tmp_path / "site_split", noise=noise, seed=5)
    text = result.paths.circuit_noisy_pauli.read_text()
    assert "X_ERROR(0.2) 0" in text
    assert "X_ERROR(0.4) 1" in text
    binding_manifest = json.loads((result.paths.out_dir / "source_timeline_binding.json").read_text())
    events = binding_manifest["projection_audit"]["matched_events"][0]
    assert [event["noise_targets"] for event in events] == [[0], [1]]
    assert [event["site_reduction"] for event in events] == [
        "per_target_from_site_payload",
        "per_target_from_site_payload",
    ]


def test_source_projection_after_gate_and_idle_branches_are_pinned(tmp_path):
    builder = CircuitBuilder(num_qubits=2)
    builder.x(0)
    builder.tick()
    builder.measure((0, 1), key=("m0", "m1"))
    builder.detector("d0", xor=("m0",))
    builder.detector("d1", xor=("m1",))
    circuit = builder.build()
    timeline = SourceTimeline(
        name="gate_idle_probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={
            "p_gate": np.asarray([0.1], dtype=np.float64),
            "p_idle": np.asarray([0.3], dtype=np.float64),
        },
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="after",
                match_kind="gate_type",
                gate_name="X",
                noise="X_ERROR",
                payload_key="p_gate",
                map_kind="payload_probability",
            ),
            SourceStimPauliRule(
                position="during",
                match_kind="idle",
                noise="X_ERROR",
                payload_key="p_idle",
                map_kind="payload_probability",
                target_filter=(1,),
            ),
        ),
    )

    result = Simulator(circuit).run(shots=64, out_dir=tmp_path / "after_idle", noise=noise, seed=6)
    text = result.paths.circuit_noisy_pauli.read_text()
    assert "X 0\nX_ERROR(0.1) 0" in text
    assert "X_ERROR(0.3) 1\nTICK" in text
    assert result.manifest["noise"]["matched_counts"] == [1, 1]


def test_source_projection_splits_site_payloads_for_depolarize2_pairs(tmp_path):
    builder = CircuitBuilder(num_qubits=4)
    builder.cx((0, 1, 2, 3))
    builder.measure((0, 1, 2, 3), key=("m0", "m1", "m2", "m3"))
    for i in range(4):
        builder.detector(f"d{i}", xor=(f"m{i}",))
    circuit = builder.build()
    timeline = SourceTimeline(
        name="site_probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([[0.1, 0.3, 0.2, 0.6]], dtype=np.float64)},
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="after",
                match_kind="gate_type",
                gate_name="CX",
                noise="DEPOLARIZE2",
                payload_key="p",
                map_kind="payload_probability",
            ),
        ),
    )

    result = Simulator(circuit).run(shots=64, out_dir=tmp_path / "depolarize2_pair_split", noise=noise, seed=7)
    text = result.paths.circuit_noisy_pauli.read_text()
    assert "DEPOLARIZE2(0.2) 0 1" in text
    assert "DEPOLARIZE2(0.4) 2 3" in text
    assert result.manifest["noise"]["matched_counts"] == [2]
    binding_manifest = json.loads((result.paths.out_dir / "source_timeline_binding.json").read_text())
    events = binding_manifest["projection_audit"]["matched_events"][0]
    assert [event["site_reduction"] for event in events] == [
        "per_pair_mean_from_site_payload",
        "per_pair_mean_from_site_payload",
    ]


def test_source_projection_codespec_final_readout_requires_tick_coverage(tmp_path):
    circuit = compile_code_spec(XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec())
    timeline = SourceTimeline(
        name="rounds_without_final_readout_tick",
        n_cycles=2,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([0.1, 0.1], dtype=np.float64)},
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M",
                noise="X_ERROR",
                payload_key="p",
                map_kind="payload_probability",
            ),
        ),
    )

    with pytest.raises(ValueError, match="not fully covered"):
        Simulator(circuit).run(shots=8, out_dir=tmp_path / "codespec_short_tick", noise=noise, seed=8)


def test_source_projection_rejects_bad_payload_probability():
    timeline = SourceTimeline(
        name="bad_probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([1.0], dtype=np.float64)},
    )
    rule = SourceStimPauliRule(
        position="before",
        match_kind="measurement_type",
        measure_name="M",
        noise="X_ERROR",
        payload_key="p",
        map_kind="payload_probability",
    )
    with pytest.raises(ValueError, match="must be in"):
        rule.probability_for(timeline, cycle_index=0, targets=(0,))


def test_source_projection_bad_payload_run_clears_stale_artifacts(tmp_path):
    circuit = _two_measurement_circuit()
    out_dir = tmp_path / "bad_payload_run"
    Simulator(circuit).run(shots=8, out_dir=out_dir, seed=9)
    assert (out_dir / "manifest.json").exists()

    timeline = SourceTimeline(
        name="bad_probability",
        n_cycles=2,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([1.0, 0.0], dtype=np.float64)},
    )
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(
            SourceStimPauliRule(
                position="before",
                match_kind="measurement_type",
                measure_name="M",
                noise="X_ERROR",
                payload_key="p",
                map_kind="payload_probability",
            ),
        ),
    )

    with pytest.raises(ValueError, match="must be in"):
        Simulator(circuit).run(shots=8, out_dir=out_dir, noise=noise, seed=9)
    assert not (out_dir / "manifest.json").exists()


def test_source_projection_rejects_non_tick_binding_and_bad_config():
    timeline = SourceTimeline(
        name="probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={"p": np.asarray([0.2], dtype=np.float64)},
    )
    rule = SourceStimPauliRule(
        position="before",
        match_kind="measurement_type",
        measure_name="M",
        noise="X_ERROR",
        payload_key="p",
        map_kind="payload_probability",
    )
    with pytest.raises(NotImplementedError, match="circuit_tick"):
        SourceStimPauliProjectionSpec(
            timeline=timeline,
            rules=(rule,),
            source_binding=SourceTimelineBinding(cycle_binding="qec_round"),
        )
    with pytest.raises(ValueError, match="sensitivity"):
        SourceStimPauliRule(
            position="before",
            match_kind="measurement_type",
            measure_name="M",
            noise="X_ERROR",
            payload_key="p",
            sensitivity=math.inf,
        )
    with pytest.raises(ValueError, match="target_filter"):
        SourceStimPauliRule(
            position="before",
            match_kind="measurement_type",
            measure_name="M",
            noise="X_ERROR",
            payload_key="p",
            target_filter=(0.9,),
        )
    with pytest.raises(ValueError, match="gate_index"):
        SourceStimPauliRule(
            position="after",
            match_kind="gate_index",
            gate_index=0.9,
            noise="X_ERROR",
            payload_key="p",
        )


def test_source_projection_binding_payload_keys_must_cover_rules():
    timeline = SourceTimeline(
        name="probability",
        n_cycles=1,
        cycle_time_ns=1_000.0,
        payload={
            "p": np.asarray([0.2], dtype=np.float64),
            "z_radns": np.asarray([1.0e-4], dtype=np.float64),
        },
    )
    rule = SourceStimPauliRule(
        position="before",
        match_kind="measurement_type",
        measure_name="M",
        noise="X_ERROR",
        payload_key="p",
        map_kind="payload_probability",
    )
    with pytest.raises(ValueError, match="omit"):
        SourceStimPauliProjectionSpec(
            timeline=timeline,
            rules=(rule,),
            source_binding=SourceTimelineBinding(cycle_binding="circuit_tick", payload_keys=("z_radns",)),
        )

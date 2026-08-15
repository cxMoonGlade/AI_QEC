"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.stim_source`` (6 CPU-pure public units: the frozen
``CompiledCircuit.__post_init__`` record validator, the ``CircuitSource`` Protocol
``compile`` stub, and the three source-adapter ``compile`` surfaces
``CircuitIRSource.compile`` / ``CompiledCircuitSource.compile`` / ``StimCircuitSource.compile``
plus ``StimCircuitSource.from_file``; the private ``_sha256_file`` helper is not a public unit
but is mutated + exercised through ``from_file``; the module imports NEITHER torch NOR quimb, so
out_of_scope is empty).

Current coverage contract: docs/SIMULATOR.md SS12.3/12.4.
``frontend/stim_source.py`` keeps the ORIGIN of a compiled Stim circuit explicit: keyed
``CircuitIR``, an already-compiled pair, and imported/on-disk Stim circuits all feed the same
``CompiledCircuit`` artifact path.

L2 DISCIPLINE (100% coverage != discrimination). The ``CompiledCircuit`` record reconcile is
killed operand-by-operand (four one-field record_schema mismatches, each with its EXACT
reconstructed message); require_stim_circuit is tripped for BOTH label routes; the metadata /
noise_manifest / source_projection_audit guards are pinned with their EXACT labelled messages via
``assert_raises_exact``; the ``StimCircuitSource.from_file`` sha256 is pinned against an
INDEPENDENT ``hashlib`` recompute of the file bytes; and every source-adapter ``compile`` branch
(noise None / trivial / non-trivial; noisy present / absent) is exercised, with the pre-noised
stub manifest and the source-projection isolation contract pinned exactly.
"""
from __future__ import annotations

import dataclasses
import hashlib

import numpy as np
import pytest
import stim
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_raises_exact

from error_coupling_simulator.frontend.circuit_ir import CircuitBuilder, CircuitIR
from error_coupling_simulator.frontend.noise_spec import (
    NoiseBuilder,
    SourceStimPauliProjectionSpec,
    SourceStimPauliRule,
    StimPauliNoiseSpec,
    apply_stim_pauli_noise,
)
from error_coupling_simulator.frontend.record_schema import RecordSchema
from error_coupling_simulator.frontend.stim_io import circuit_to_stim, write_stim_circuit
from error_coupling_simulator.frontend.stim_source import (
    CircuitIRSource,
    CircuitSource,
    CompiledCircuit,
    CompiledCircuitSource,
    StimCircuitSource,
)
from error_coupling_simulator.source.process import SourceTimeline


# --------------------------------------------------------------------------- #
# INDEPENDENT input builders.                                                  #
# --------------------------------------------------------------------------- #
def _base_ir(metadata=None) -> CircuitIR:
    """A 1-qubit CircuitIR with one Z-measurement, one detector, one observable
    (counts: num_qubits=1, num_measurements=1, num_detectors=1, num_observables=1). The M is a
    Z-basis measurement so StimPauliNoiseSpec(before_measure_flip=..) inserts X_ERROR before it."""
    b = CircuitBuilder(num_qubits=1,
                       metadata=({"code": "cc_base"} if metadata is None else metadata))
    b.measure(0, key="m0")
    b.detector("d0", xor=("m0",), coords=(0.0,))
    b.observable("L0", xor=("m0",), index=0)
    return b.build()


def _ideal() -> stim.Circuit:
    return circuit_to_stim(_base_ir())


def _valid_compiled() -> CompiledCircuit:
    return CircuitIRSource(_base_ir()).compile()


# =========================================================================== #
# CompiledCircuit.__post_init__                                                 #
# =========================================================================== #
def test_L0_compiled_circuit_valid_defaults_and_copies():
    ideal = _ideal()
    meta_in = {"code": "public_ok"}
    cc = CompiledCircuit(
        ideal_circuit=ideal, noisy_circuit=ideal, metadata=meta_in, source_type="circuit_ir")
    # backend / representability default + normalize to the only allowed values.
    assert cc.backend == "stim"
    assert cc.representability == "stim_pauli"
    # record_schema defaults to the actual from_stim schema (record_schema None arm + the
    # record_schema setattr -> not None). INDEPENDENT recompute.
    ref = RecordSchema.from_stim(ideal)
    assert cc.record_schema is not None
    assert (cc.record_schema.num_qubits, cc.record_schema.num_measurements,
            cc.record_schema.num_detectors, cc.record_schema.num_observables) == (
        ref.num_qubits, ref.num_measurements, ref.num_detectors, ref.num_observables)
    # metadata is the validated COPY (is-not the input) -- kills the 'metadata' setattr-key wrap.
    assert cc.metadata == {"code": "public_ok"}
    assert cc.metadata is not meta_in
    # noise_manifest default None arm (the ternary else); source_projection_audit default None arm.
    assert cc.noise_manifest is None
    assert cc.source_projection_audit is None


def test_L0_compiled_circuit_truthy_record_schema_arm():
    # a MATCHING explicit record_schema exercises the `record_schema or actual` TRUTHY arm (no
    # raise) -- the 4-way count `if` is False.
    ideal = _ideal()
    good_schema = RecordSchema.from_stim(ideal)
    cc = CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                         source_type="t", record_schema=good_schema)
    assert cc.record_schema.num_qubits == good_schema.num_qubits


def test_L0_compiled_circuit_record_schema_mismatch_each_field_exact():
    # FOUR one-field mismatches: each bumps EXACTLY one count so exactly one `!=` operand of the
    # 4-way `or` fires -> kills every `!=`->`==` and the `or`->`and` variants (a mutant flips the
    # valid single-field mismatch into no-raise). The EXACT reconstructed message kills the
    # f-string-prefix wrap a substring match would leave surviving.
    ideal = _ideal()
    actual = RecordSchema.from_stim(ideal)
    for field in ("num_qubits", "num_measurements", "num_detectors", "num_observables"):
        wrong = dataclasses.replace(actual, **{field: getattr(actual, field) + 1})
        expected = ("record_schema counts do not match compiled Stim circuits; "
                    f"record_schema={wrong.to_manifest()} actual={actual.to_manifest()}")
        assert_raises_exact(
            ValueError, expected,
            lambda w=wrong: CompiledCircuit(
                ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                source_type="mismatch", record_schema=w),
            label=f"record_schema mismatch {field}")


def test_L0_compiled_circuit_requires_stim_circuit_both_labels_exact():
    ideal = _ideal()
    # a non-stim IDEAL circuit -> require_stim_circuit trips with the 'ideal_circuit' label.
    assert_raises_exact(
        TypeError, "ideal_circuit must be stim.Circuit, got <class 'str'>",
        lambda: CompiledCircuit(ideal_circuit="not a circuit", noisy_circuit=ideal,
                                metadata={}, source_type="bad_ideal"),
        label="require_stim_circuit ideal label")
    # a valid ideal but non-stim NOISY -> the 'noisy_circuit' label (ideal is checked first).
    assert_raises_exact(
        TypeError, "noisy_circuit must be stim.Circuit, got <class 'str'>",
        lambda: CompiledCircuit(ideal_circuit=ideal, noisy_circuit="nope",
                                metadata={}, source_type="bad_noisy"),
        label="require_stim_circuit noisy label")


def test_L0_compiled_circuit_rejects_bad_representability():
    # the require_frontend_representability guard (part of the truth-laundering contract).
    ideal = _ideal()
    with pytest.raises(ValueError, match="unsupported frontend representability"):
        CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                        source_type="launder", representability="analog_joint_l_window")


def test_L0_compiled_circuit_rejects_mismatched_ideal_noisy_schema():
    # require_matching_schemas: an ideal with an observable vs a noisy without one differ in schema.
    ideal = _ideal()
    detector_only = CircuitBuilder(num_qubits=1)
    detector_only.measure(0, key="m0")
    detector_only.detector("d0", xor=("m0",))
    noisy_no_obs = circuit_to_stim(detector_only.build())
    with pytest.raises(ValueError, match="identical record schema"):
        CompiledCircuit(ideal_circuit=ideal, noisy_circuit=noisy_no_obs, metadata={},
                        source_type="schema_mismatch")


def test_L0_compiled_circuit_rejects_reserved_metadata_key_exact():
    # validate_public_metadata on metadata, EXACT message carries the 'CompiledCircuit.metadata'
    # label (kills the label wrap + proves the guard is load-bearing at construction).
    ideal = _ideal()
    assert_raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator truth; "
        "reserved key CompiledCircuit.metadata.kraus_stack matches 'kraus'. "
        "Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal,
                                metadata={"kraus_stack": "secret.npz"}, source_type="launder"),
        label="metadata reserved-key guard")


def test_L0_compiled_circuit_noise_manifest_validated_copied_and_reserved_exact():
    ideal = _ideal()
    # a VALID non-None noise_manifest is validated + stored as a COPY (is-not the input) -- kills
    # the 'noise_manifest' setattr-key wrap AND exercises the ternary is-not-None arm.
    nm_in = {"origin": "manual"}
    cc = CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                         source_type="t", noise_manifest=nm_in)
    assert cc.noise_manifest == {"origin": "manual"}
    assert cc.noise_manifest is not nm_in
    # a reserved key in noise_manifest is rejected with the 'CompiledCircuit.noise_manifest' label.
    assert_raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator truth; "
        "reserved key CompiledCircuit.noise_manifest.channel_truth matches 'channel_truth'. "
        "Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                                source_type="launder", noise_manifest={"channel_truth": "x.npz"}),
        label="noise_manifest reserved-key guard")


def test_L0_compiled_circuit_source_type_str_coerced():
    # source_type is str()-coerced -> pinning the coerced value kills the 'source_type' setattr-key
    # wrap (under it self.source_type would keep the raw int).
    ideal = _ideal()
    cc = CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={}, source_type=123)
    assert cc.source_type == "123"
    assert isinstance(cc.source_type, str)


def test_L0_compiled_circuit_evaluator_sidecars_validated_to_tuple():
    ideal = _ideal()
    # a LIST of valid sidecars is stored as a validated TUPLE (kills the 'evaluator_sidecars'
    # setattr-key wrap -- under it self.evaluator_sidecars stays the input LIST).
    sidecars_in = [{"name": "truth", "path": "truth.json", "visibility": "evaluator_only"}]
    cc = CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                         source_type="t", evaluator_sidecars=sidecars_in)
    assert isinstance(cc.evaluator_sidecars, tuple)
    assert cc.evaluator_sidecars[0]["name"] == "truth"
    # a non-evaluator-only sidecar is rejected (the guard is load-bearing).
    with pytest.raises(ValueError, match="evaluator_only"):
        CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={}, source_type="t",
                        evaluator_sidecars=({"name": "t", "path": "t.json",
                                             "visibility": "public"},))


def test_L0_compiled_circuit_source_projection_audit_valid_copied():
    ideal = _ideal()
    audit_in = {"visibility": "evaluator_only", "source_timeline": {"name": "x"}}
    cc = CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                         source_type="t", source_projection_audit=audit_in)
    # stored as a COPY (dict(...)) -- kills the `is not None`->`is None` mutant (which would skip
    # the copy or dict(None)->TypeError on the default) and the dict() copy drop.
    assert cc.source_projection_audit == audit_in
    assert cc.source_projection_audit is not audit_in
    assert cc.source_projection_audit["visibility"] == "evaluator_only"


def test_L0_compiled_circuit_source_projection_audit_bad_visibility_exact():
    ideal = _ideal()
    # a wrong visibility raises the EXACT message (kills the `!=`->`==`, the 'visibility' key wrap,
    # and the 'evaluator_only' value wrap -- a wrap makes .get(...) != ... True even for a valid
    # audit, so the valid-audit test above ALSO discriminates those two literals).
    assert_raises_exact(
        ValueError, "source_projection_audit must be visibility='evaluator_only'",
        lambda: CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={},
                                source_type="t",
                                source_projection_audit={"visibility": "public"}),
        label="source_projection_audit visibility guard")


# =========================================================================== #
# CircuitSource (typing.Protocol stub -- covered by import)                     #
# =========================================================================== #
def test_L0_circuit_source_protocol_is_runtime_checkable():
    # the Protocol's `compile` def line is covered by IMPORT; the concrete adapters structurally
    # satisfy the runtime_checkable Protocol (they each expose `compile`).
    assert isinstance(CircuitIRSource(_base_ir()), CircuitSource)
    assert isinstance(StimCircuitSource(_ideal()), CircuitSource)
    assert isinstance(CompiledCircuitSource(_valid_compiled()), CircuitSource)


# =========================================================================== #
# CircuitIRSource.compile                                                       #
# =========================================================================== #
def test_L0_circuit_ir_source_compile_no_noise():
    ir = _base_ir({"code": "irc"})
    cc = CircuitIRSource(ir).compile()          # noise=None -> the `if noise is not None` False arc
    assert cc.source_type == "circuit_ir"
    assert cc.noise_manifest is None
    assert cc.source_projection_audit is None
    # metadata is the clean original dict as a COPY.
    assert cc.metadata == {"code": "irc"}
    assert cc.metadata is not ir.metadata
    # record_schema counts round-trip the emitted noisy stim circuit (INDEPENDENT recompute).
    assert (cc.record_schema.num_qubits, cc.record_schema.num_measurements,
            cc.record_schema.num_detectors, cc.record_schema.num_observables) == (
        int(cc.noisy_circuit.num_qubits), int(cc.noisy_circuit.num_measurements),
        int(cc.noisy_circuit.num_detectors), int(cc.noisy_circuit.num_observables))
    # the IR record-schema carries the keyed names (from_circuit_ir).
    assert cc.record_schema.measurement_keys == ("m0",)
    assert cc.record_schema.detector_names == ("d0",)
    assert cc.record_schema.observable_names == ("L0",)


def test_L0_circuit_ir_source_compile_targeted_noise_manifest_key():
    # a NON-TRIVIAL TargetedStimNoiseSpec: apply_stim_pauli_noise stores a noise_projection manifest
    # that carries 'matched_counts' the noise's own to_manifest() lacks. So threading the STORED
    # manifest (the `.get('noise_projection', ...)` primary) is load-bearing: a 'noise_projection'
    # key wrap falls back to the bare manifest -> no matched_counts -> killed.
    ir = _base_ir()
    noise = NoiseBuilder().before_measurement("X_ERROR", 0.25).build()
    cc = CircuitIRSource(ir).compile(noise)
    assert cc.noise_manifest is not None
    assert cc.noise_manifest["type"] == "targeted_stim_pauli"
    assert cc.noise_manifest["matched_counts"] == [1]
    assert "matched_counts" not in noise.to_manifest()      # the fallback would drop it

    def prop(nm):
        assert nm.get("matched_counts") == [1]

    assert_discriminates(prop, cc.noise_manifest, noise.to_manifest(),
                         label="CircuitIRSource stored noise_projection manifest")


def test_L0_circuit_ir_source_compile_trivial_noise_uses_manifest_fallback():
    # a TRIVIAL StimPauliNoiseSpec: apply returns the circuit UNCHANGED (no noise_projection
    # metadata), so the `.get('noise_projection', noise.to_manifest())` DEFAULT fallback arm fires.
    ir = _base_ir()
    noise = StimPauliNoiseSpec()                # is_trivial -> no metadata inserted
    cc = CircuitIRSource(ir).compile(noise)
    assert cc.noise_manifest == {
        "type": "stim_pauli",
        "after_1q_depolarization": 0.0,
        "after_2q_depolarization": 0.0,
        "before_measure_flip": 0.0,
    }


def test_L0_circuit_ir_source_compile_source_projection_isolation():
    # the ISOLATION CONTRACT through the compile path: public metadata stays the CLEAN
    # original circuit's dict while the evaluator-only source-projection audit rides the SEPARATE
    # visibility-gated field.
    ir = _base_ir({"code": "src_proj"})
    timeline = SourceTimeline(
        name="p_timeline", n_cycles=1, cycle_time_ns=1_000.0,
        payload={"p": np.asarray([0.2], dtype=np.float64)})
    noise = SourceStimPauliProjectionSpec(
        timeline=timeline,
        rules=(SourceStimPauliRule(position="before", match_kind="measurement_type",
                                   measure_name="M", noise="X_ERROR",
                                   payload_key="p", map_kind="payload_probability"),))
    cc = CircuitIRSource(ir).compile(noise)
    # public-artifact metadata: clean, no source truth.
    assert cc.metadata == {"code": "src_proj"}
    assert "source_timeline" not in cc.metadata
    # evaluator-only audit: present, visibility-gated, carries the source truth.
    assert cc.source_projection_audit is not None
    assert cc.source_projection_audit["visibility"] == "evaluator_only"
    assert "source_timeline" in cc.source_projection_audit
    # public noise manifest: reduced projection + match counts.
    assert cc.noise_manifest["type"] == "stim_pauli_source_projection"
    assert cc.noise_manifest["matched_counts"] == [1]


# =========================================================================== #
# CompiledCircuitSource.compile                                                 #
# =========================================================================== #
def test_L0_compiled_circuit_source_identity_and_trivial_noise():
    compiled = _valid_compiled()
    src = CompiledCircuitSource(compiled)
    # noise=None -> the `and` first operand False -> returns BY IDENTITY.
    assert src.compile() is compiled
    # a TRIVIAL noise -> first operand True, second (not is_trivial) False -> returns.
    assert src.compile(StimPauliNoiseSpec()) is compiled


def test_L0_compiled_circuit_source_rejects_new_noise_exact():
    src = CompiledCircuitSource(_valid_compiled())
    # a NON-TRIVIAL noise -> `noise is not None and not noise.is_trivial` True -> raise EXACT.
    assert_raises_exact(
        ValueError, "cannot apply new noise to an already compiled circuit pair",
        lambda: src.compile(StimPauliNoiseSpec(before_measure_flip=0.25)),
        label="CompiledCircuitSource new-noise guard")


# =========================================================================== #
# StimCircuitSource.from_file                                                   #
# =========================================================================== #
def test_L0_stim_circuit_source_from_file_ideal_only(tmp_path):
    ideal_stim = _ideal()
    ideal_path = tmp_path / "ideal.stim"
    write_stim_circuit(ideal_stim, ideal_path)
    src = StimCircuitSource.from_file(ideal_path)      # metadata=None -> `metadata or {}` -> {}
    # the meta dict is EXACT (kills every key wrap) with the sha256 pinned against an INDEPENDENT
    # hashlib recompute of the file bytes (kills the _sha256_file 'rb'/arithmetic mutants).
    indep_sha = hashlib.sha256(ideal_path.read_bytes()).hexdigest()
    assert src.metadata == {
        "ideal_path": str(ideal_path),
        "ideal_sha256": indep_sha,
        "noisy_is_ideal": True,                        # the `noisy_path is None` else arc
    }
    assert src.noisy_circuit is None
    assert src.ideal_circuit == ideal_stim


def test_L0_stim_circuit_source_from_file_with_noisy_and_metadata(tmp_path):
    ideal_stim = _ideal()
    noisy_stim = circuit_to_stim(
        apply_stim_pauli_noise(_base_ir(), StimPauliNoiseSpec(before_measure_flip=0.25)))
    ideal_path = tmp_path / "ideal.stim"
    noisy_path = tmp_path / "noisy.stim"
    write_stim_circuit(ideal_stim, ideal_path)
    write_stim_circuit(noisy_stim, noisy_path)
    # a truthy metadata dict whose keys survive (the `metadata or {}` truthy arm) + noisy path.
    src = StimCircuitSource.from_file(
        ideal_path, noisy_path=noisy_path, metadata={"origin": "roundtrip"})
    assert src.metadata == {
        "origin": "roundtrip",
        "ideal_path": str(ideal_path),
        "ideal_sha256": hashlib.sha256(ideal_path.read_bytes()).hexdigest(),
        "noisy_path": str(noisy_path),
        "noisy_sha256": hashlib.sha256(noisy_path.read_bytes()).hexdigest(),
    }
    assert src.noisy_circuit == noisy_stim
    assert src.ideal_circuit == ideal_stim
    # the two sha256 hashes differ because the two files differ (a swapped/dropped hash would tie).
    assert src.metadata["ideal_sha256"] != src.metadata["noisy_sha256"]


# =========================================================================== #
# StimCircuitSource.compile                                                     #
# =========================================================================== #
def test_L0_stim_circuit_source_compile_ideal_only_no_noise():
    ideal = _ideal()
    src = StimCircuitSource(ideal)              # no noisy circuit, metadata None
    cc = src.compile()                          # noise=None
    assert cc.source_type == "stim_circuit"
    # noisy_circuit is None -> the ternary else reuses ideal as noisy.
    assert cc.noisy_circuit is ideal
    # noisy None -> the `if self.noisy_circuit is not None and ...` first operand False -> skip.
    assert cc.noise_manifest is None
    # metadata None -> dict(None or {}) == {}.
    assert cc.metadata == {}


def test_L0_stim_circuit_source_compile_prenoised_stub_manifest():
    ideal = _ideal()
    noisy = _ideal()                            # equal schema, distinct pair role
    src = StimCircuitSource(ideal, noisy_circuit=noisy, metadata={"origin": "native"})
    cc = src.compile()                          # noise=None, noisy present -> both `and` operands
    # the pre-noised stub manifest is pinned EXACT (kills each literal wrap).
    assert cc.noise_manifest == {
        "type": "pre_noised_stim_source",
        "source_type": "stim_circuit",
        "placement": "external",
    }
    assert cc.noisy_circuit is noisy            # the ternary if-arc
    assert cc.metadata == {"origin": "native"}
    assert cc.source_type == "stim_circuit"

    def prop(nm):
        assert nm == {
            "type": "pre_noised_stim_source",
            "source_type": "stim_circuit",
            "placement": "external",
        }

    wrong = {"type": "pre_noised_stim_source", "source_type": "stim_circuit",
             "placement": "internal"}
    assert_discriminates(prop, cc.noise_manifest, wrong, label="pre-noised stub manifest")


def test_L0_stim_circuit_source_compile_trivial_noise_routes_noise_manifest():
    ideal = _ideal()
    noisy = _ideal()
    src = StimCircuitSource(ideal, noisy_circuit=noisy)
    # a TRIVIAL noise -> noise_manifest = noise.to_manifest() (ternary if-arc); then the
    # `noisy is not None and noise_manifest is None` SECOND operand is False (noise_manifest set)
    # -> the pre-noised stub is NOT applied.
    cc = src.compile(StimPauliNoiseSpec())
    assert cc.noise_manifest == {
        "type": "stim_pauli",
        "after_1q_depolarization": 0.0,
        "after_2q_depolarization": 0.0,
        "before_measure_flip": 0.0,
    }


def test_L0_stim_circuit_source_compile_rejects_nontrivial_noise_exact():
    src = StimCircuitSource(_ideal())
    assert_raises_exact(
        NotImplementedError,
        "non-trivial StimPauliNoiseSpec placement on raw Stim sources requires "
        "the location-aware compiler slice; pass a pre-noised Stim circuit as noisy_circuit",
        lambda: src.compile(StimPauliNoiseSpec(before_measure_flip=0.25)),
        label="StimCircuitSource non-trivial noise guard")


# =========================================================================== #
# L1 PROPERTIES (Hypothesis)                                                    #
# =========================================================================== #
@settings(max_examples=100, deadline=None)
@given(nq=st.integers(1, 4),
       p=st.floats(min_value=0.0, max_value=0.3, allow_nan=False, allow_infinity=False))
def test_L1_circuit_ir_source_compile_schema_consistent(nq, p):
    b = CircuitBuilder(num_qubits=nq, metadata={"code": f"l1_{nq}"})
    keys = tuple(f"m{i}" for i in range(nq))
    b.measure(tuple(range(nq)), key=keys)
    for i, key in enumerate(keys):
        b.detector(f"d{i}", xor=(key,))
    ir = b.build()
    cc = CircuitIRSource(ir).compile(StimPauliNoiseSpec(before_measure_flip=p))
    assert cc.source_type == "circuit_ir"
    # metadata is a clean copy of the ORIGINAL circuit.
    assert cc.metadata == {"code": f"l1_{nq}"}
    assert cc.metadata is not ir.metadata
    # record_schema counts match stim's OWN properties on the emitted noisy circuit (INDEPENDENT),
    # and the ideal/noisy pair share their record schema.
    assert (cc.record_schema.num_qubits, cc.record_schema.num_measurements,
            cc.record_schema.num_detectors, cc.record_schema.num_observables) == (
        int(cc.noisy_circuit.num_qubits), int(cc.noisy_circuit.num_measurements),
        int(cc.noisy_circuit.num_detectors), int(cc.noisy_circuit.num_observables))
    assert int(cc.ideal_circuit.num_measurements) == int(cc.noisy_circuit.num_measurements)
    assert int(cc.ideal_circuit.num_detectors) == int(cc.noisy_circuit.num_detectors)


@settings(max_examples=60, deadline=None)
@given(nq=st.integers(1, 4))
def test_L1_compiled_circuit_record_schema_defaults_to_actual(nq):
    b = CircuitBuilder(num_qubits=nq)
    keys = tuple(f"m{i}" for i in range(nq))
    b.measure(tuple(range(nq)), key=keys)
    for i, key in enumerate(keys):
        b.detector(f"d{i}", xor=(key,))
    ideal = circuit_to_stim(b.build())
    cc = CompiledCircuit(ideal_circuit=ideal, noisy_circuit=ideal, metadata={}, source_type="t")
    # the None record_schema arm defaults to from_stim(actual) -- INDEPENDENT recompute.
    ref = RecordSchema.from_stim(ideal)
    assert (cc.record_schema.num_qubits, cc.record_schema.num_measurements,
            cc.record_schema.num_detectors, cc.record_schema.num_observables) == (
        ref.num_qubits, ref.num_measurements, ref.num_detectors, ref.num_observables)


@settings(max_examples=40, deadline=None)
@given(present=st.booleans(), trivial=st.booleans())
def test_L1_stim_circuit_source_compile_branch_matrix(present, trivial):
    ideal = _ideal()
    noisy = _ideal() if present else None
    src = StimCircuitSource(ideal, noisy_circuit=noisy)
    noise = StimPauliNoiseSpec() if trivial else None      # both are None-or-trivial (no raise)
    cc = src.compile(noise)
    assert cc.source_type == "stim_circuit"
    # noisy selection: present -> the noisy circuit; absent -> ideal reused.
    assert cc.noisy_circuit is (noisy if present else ideal)
    if trivial:
        # a trivial noise routes the noise's own manifest (never the pre-noised stub).
        assert cc.noise_manifest["type"] == "stim_pauli"
    elif present:
        # noise None + noisy present -> the pre-noised stub.
        assert cc.noise_manifest == {
            "type": "pre_noised_stim_source",
            "source_type": "stim_circuit",
            "placement": "external",
        }
    else:
        # noise None + no noisy -> no manifest.
        assert cc.noise_manifest is None

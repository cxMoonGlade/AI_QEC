"""Stage-D batch ``noise_spec`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.noise_spec`` (25 CPU-pure public units: 20 methods/funcs
+ 5 frozen-dataclass ``__post_init__`` dunders; no torch, no quimb, so out_of_scope is empty).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md D14).
``frontend/noise_spec.py`` owns the Stim-representable Pauli noise-spec layer: the plain
depolarizing ``StimPauliNoiseSpec``, the location-aware ``TargetedStimNoiseSpec`` built by the
``NoiseBuilder`` fluent API, and the evaluator-only ``SourceStimPauliProjectionSpec`` (a reduced
Pauli projection of a ``SourceTimeline``). ``apply_stim_pauli_noise`` inserts the noise ops into
a ``CircuitIR`` at the right positions.

L2 DISCIPLINE (100% coverage != discrimination). The workhorse is EXACT-STRUCTURE pinning: the
transformed circuit's (name, targets, args) step tuples and the ``noise_projection`` metadata are
pinned against an INDEPENDENT from-scratch expectation (NOT the module's own manifest).
``probability_for`` is pinned against a from-scratch recompute of the logit sigmoid and of the
payload-probability identity map -- NEVER the module's own call. Every validation RAISE asserts
its EXACT message via ``str(excinfo.value)==...`` (KeyError via ``.args[0]``) so mutmut's
string-literal wrap/roundtrip mutants die (a substring ``match=`` lets them survive).

ISOLATION CONTRACT (load-bearing): the learner-visible public manifests must NOT leak the
evaluator-only source-conditioning fields that the evaluator manifest carries; pinned both ways
with an ``assert_discriminates`` leak variant.

Module-level set-element string mutants (the 1q/2q unitary sets, the Z-measurement set, the
noise-instruction aliases) are killed by PARAMETRIZED coverage of every element. The private
routing helpers (``_apply_*``/``_append_*``/``_rule_matches_*``/``_resolve_*``/``_validate_*``/
``_strict_*``) are exercised + pinned through the public apply/builder paths plus direct
value-pins (mutmut is coverage-guided).
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins

import error_coupling_simulator.frontend.noise_spec as nspec
from error_coupling_simulator.frontend.noise_spec import (
    NoiseBuilder,
    SourceStimPauliProjectionSpec,
    SourceStimPauliRule,
    StimNoiseRule,
    StimPauliNoiseSpec,
    TargetedStimNoiseSpec,
    apply_stim_pauli_noise,
)
from error_coupling_simulator.frontend.circuit_ir import (
    CircuitBuilder,
    CircuitIR,
    DetectorDef,
    GateOp,
    MeasureOp,
    ObservableDef,
    Tick,
)
from error_coupling_simulator.source.process import SourceTimeline

_TL_SCHEMA = "qec_twin.mechanisms.SourceTimeline.v1"
_EXEC_STATUS = {
    "applied_to_stim_records": True,
    "stim_dem_modified": True,
    "backend_lowering": "stim_pauli_reduced_source_projection",
    "reason": (
        "A reduced Pauli projection of the source timeline was inserted into "
        "the noisy Stim circuit. Exact source payloads remain evaluator-only "
        "sidecar truth; this is not analog joint-Lindbladian/source truth."
    ),
}
_AUDIT_KEY = "_source_projection_evaluator_audit"


# --------------------------------------------------------------------------- #
# helpers: exact-message raise + INDEPENDENT step/expectation reconstruction    #
# --------------------------------------------------------------------------- #
def _raises_exact(exc, msg, fn):
    """pytest.raises pinning the EXACT ``str(exc)`` (kills mutmut string-literal wrap/case
    mutants that a substring ``match=`` lets survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _raises_arg(exc, msg, fn):
    """Like ``_raises_exact`` but compares ``exc.args[0]`` -- for KeyError, whose ``str``
    wraps the message in quotes."""
    with pytest.raises(exc) as ei:
        fn()
    assert ei.value.args[0] == msg, f"arg mismatch\n got: {ei.value.args[0]!r}\n exp: {msg!r}"


def _steps(circuit):
    """A comparable, from-scratch view of a CircuitIR's ordered steps."""
    out = []
    for s in circuit.steps:
        if isinstance(s, Tick):
            out.append(("T",))
        elif isinstance(s, MeasureOp):
            out.append(("M", s.name, tuple(s.targets)))
        elif isinstance(s, GateOp):
            out.append(("G", s.name, tuple(s.targets), tuple(s.args)))
        elif isinstance(s, DetectorDef):
            out.append(("D", s.name))
        elif isinstance(s, ObservableDef):
            out.append(("O", s.name))
    return out


def _indep_logit_prob(value, base_p, z_scale, sensitivity):
    """From-scratch recompute of the SourceStimPauliRule logit sigmoid map."""
    x = float(value) / float(z_scale)
    logit = math.log(float(base_p) / (1.0 - float(base_p)))
    y = max(-60.0, min(60.0, logit + float(sensitivity) * x))
    return 1.0 / (1.0 + math.exp(-y))


def _one_gate_circuit(name, targets, num_qubits):
    """A CircuitIR with a single non-noise gate (bypasses CircuitBuilder helpers)."""
    return CircuitIR(num_qubits=num_qubits, steps=(GateOp(name, targets, ()),), metadata={})


def _sp_expected_steps(circuit, spec):
    """INDEPENDENT reconstruction of the StimPauliNoiseSpec inline projection -- mirrors the
    documented contract, NOT the module's own loop."""
    one_q = {"H", "I", "X", "Y", "Z", "S", "S_DAG", "SQRT_X", "SQRT_X_DAG", "SQRT_Y",
             "SQRT_Y_DAG", "SQRT_Z", "SQRT_Z_DAG"}
    two_q = {"CX", "CY", "CZ", "ISWAP", "ISWAP_DAG", "SQRT_XX", "SQRT_XX_DAG", "SQRT_YY",
             "SQRT_YY_DAG", "SQRT_ZZ", "SQRT_ZZ_DAG", "SWAP", "XCX", "XCY", "XCZ", "YCX",
             "YCY", "YCZ"}
    z_meas = {"M", "MR", "MZ", "MRZ"}
    out = []
    for s in circuit.steps:
        if isinstance(s, MeasureOp) and spec.before_measure_flip > 0.0:
            assert s.name in z_meas
            out.append(("G", "X_ERROR", tuple(s.targets), (float(spec.before_measure_flip),)))
            out.append(("M", s.name, tuple(s.targets)))
            continue
        if isinstance(s, Tick):
            out.append(("T",))
        elif isinstance(s, MeasureOp):
            out.append(("M", s.name, tuple(s.targets)))
        elif isinstance(s, GateOp):
            out.append(("G", s.name, tuple(s.targets), tuple(s.args)))
        elif isinstance(s, DetectorDef):
            out.append(("D", s.name))
        elif isinstance(s, ObservableDef):
            out.append(("O", s.name))
        if isinstance(s, GateOp):
            if s.name in one_q and spec.after_1q_depolarization > 0.0:
                out.append(("G", "DEPOLARIZE1", tuple(s.targets),
                            (float(spec.after_1q_depolarization),)))
            elif s.name in two_q and spec.after_2q_depolarization > 0.0:
                out.append(("G", "DEPOLARIZE2", tuple(s.targets),
                            (float(spec.after_2q_depolarization),)))
    return out


def _hcz_circuit():
    b = CircuitBuilder(num_qubits=3)
    b.h(0)
    b.cz((0, 1))
    b.tick()
    b.measure((0, 1, 2), key=("m0", "m1", "m2"))
    b.detector("d0", xor=("m0",))
    return b.build()


# =========================================================================== #
# apply_stim_pauli_noise -- routing + StimPauliNoiseSpec inline path            #
# =========================================================================== #
def test_L0_apply_none_and_trivial_return_circuit_unchanged():
    circ = _hcz_circuit()
    assert apply_stim_pauli_noise(circ, None) is circ           # None -> identity
    assert apply_stim_pauli_noise(circ, StimPauliNoiseSpec()) is circ  # trivial -> identity


def test_L0_apply_stim_pauli_full_projection_pins_steps_and_manifest():
    circ = _hcz_circuit()
    spec = StimPauliNoiseSpec(after_1q_depolarization=0.01, after_2q_depolarization=0.02,
                              before_measure_flip=0.03)
    noisy = apply_stim_pauli_noise(circ, spec)
    assert _steps(noisy) == _sp_expected_steps(circ, spec)
    assert noisy.metadata["noise_projection"] == {
        "type": "stim_pauli",
        "after_1q_depolarization": 0.01,
        "after_2q_depolarization": 0.02,
        "before_measure_flip": 0.03,
    }
    assert noisy is not circ                                     # a NEW circuit


def test_L0_apply_stim_pauli_isolated_arcs():
    circ = _hcz_circuit()
    # 1q ONLY (after_2q==0, flip==0): DEPOLARIZE1 after H; NO DEPOLARIZE2 after CZ; NO flip
    s1 = StimPauliNoiseSpec(after_1q_depolarization=0.05)
    assert _steps(apply_stim_pauli_noise(circ, s1)) == _sp_expected_steps(circ, s1)
    assert not any(st[0] == "G" and st[1] in ("DEPOLARIZE2", "X_ERROR")
                   for st in _steps(apply_stim_pauli_noise(circ, s1)))
    # 2q ONLY: DEPOLARIZE2 after CZ; NO DEPOLARIZE1 after H (kills `>0.0`->`>=0.0` on 1q line)
    s2 = StimPauliNoiseSpec(after_2q_depolarization=0.05)
    got2 = _steps(apply_stim_pauli_noise(circ, s2))
    assert got2 == _sp_expected_steps(circ, s2)
    assert not any(st[0] == "G" and st[1] == "DEPOLARIZE1" for st in got2)
    # flip ONLY: X_ERROR before M; NO depolarize (kills `>0.0`->`>=0.0` on 2q/flip lines)
    s3 = StimPauliNoiseSpec(before_measure_flip=0.07)
    got3 = _steps(apply_stim_pauli_noise(circ, s3))
    assert got3 == _sp_expected_steps(circ, s3)
    assert not any(st[0] == "G" and st[1].startswith("DEPOLARIZE") for st in got3)


def test_L0_apply_stim_pauli_non_z_measurement_flip_raises():
    circ = CircuitIR(num_qubits=1, steps=(MeasureOp("MX", (0,), ("m0",)),), metadata={})
    _raises_exact(
        NotImplementedError,
        "before_measure_flip currently supports Z-basis measurements only, got MX",
        lambda: apply_stim_pauli_noise(circ, StimPauliNoiseSpec(before_measure_flip=0.03)),
    )


@pytest.mark.parametrize("gate", sorted(nspec._ONE_QUBIT_UNITARIES))
def test_L0_every_one_qubit_unitary_gets_depolarize1(gate):
    circ = _one_gate_circuit(gate, (0,), 1)
    noisy = apply_stim_pauli_noise(circ, StimPauliNoiseSpec(after_1q_depolarization=0.02))
    assert _steps(noisy) == [("G", gate, (0,), ()), ("G", "DEPOLARIZE1", (0,), (0.02,))]


@pytest.mark.parametrize("gate", sorted(nspec._TWO_QUBIT_UNITARIES))
def test_L0_every_two_qubit_unitary_gets_depolarize2(gate):
    circ = _one_gate_circuit(gate, (0, 1), 2)
    noisy = apply_stim_pauli_noise(circ, StimPauliNoiseSpec(after_2q_depolarization=0.03))
    assert _steps(noisy) == [("G", gate, (0, 1), ()), ("G", "DEPOLARIZE2", (0, 1), (0.03,))]


@pytest.mark.parametrize("mname", sorted(nspec._Z_MEASUREMENTS))
def test_L0_every_z_measurement_gets_flip(mname):
    circ = CircuitIR(num_qubits=1, steps=(MeasureOp(mname, (0,), ("m0",)),), metadata={})
    noisy = apply_stim_pauli_noise(circ, StimPauliNoiseSpec(before_measure_flip=0.04))
    assert _steps(noisy) == [("G", "X_ERROR", (0,), (0.04,)), ("M", mname, (0,))]


def test_L0_apply_stim_pauli_non_unitary_gate_untouched():
    # a reset R is neither 1q-unitary nor 2q-unitary -> no noise inserted after it
    circ = _one_gate_circuit("R", (0,), 1)
    noisy = apply_stim_pauli_noise(circ, StimPauliNoiseSpec(after_1q_depolarization=0.02,
                                                            after_2q_depolarization=0.02))
    assert _steps(noisy) == [("G", "R", (0,), ())]


# =========================================================================== #
# StimPauliNoiseSpec -- __post_init__ + is_trivial + to_manifest                #
# =========================================================================== #
def test_L0_stim_pauli_post_init_validates_and_coerces():
    sp = StimPauliNoiseSpec(after_1q_depolarization=0, after_2q_depolarization=0.5,
                            before_measure_flip=0.25)
    # int 0 coerced to float 0.0 (kills the _validate_probability float() drop on a live field)
    assert isinstance(sp.after_1q_depolarization, float) and sp.after_1q_depolarization == 0.0
    assert sp.after_2q_depolarization == 0.5 and sp.before_measure_flip == 0.25
    # each of the three fields is validated -> trip each with an exact message
    _raises_exact(ValueError, "after_1q_depolarization must be in [0, 1), got 1.0",
                  lambda: StimPauliNoiseSpec(after_1q_depolarization=1.0))
    _raises_exact(ValueError, "after_2q_depolarization must be in [0, 1), got -0.1",
                  lambda: StimPauliNoiseSpec(after_2q_depolarization=-0.1))
    _raises_exact(ValueError, "before_measure_flip must be in [0, 1), got inf",
                  lambda: StimPauliNoiseSpec(before_measure_flip=float("inf")))


def test_L0_stim_pauli_is_trivial_both_arcs():
    assert StimPauliNoiseSpec().is_trivial is True
    assert StimPauliNoiseSpec(after_1q_depolarization=0.01).is_trivial is False
    assert StimPauliNoiseSpec(after_2q_depolarization=0.01).is_trivial is False
    assert StimPauliNoiseSpec(before_measure_flip=0.01).is_trivial is False


def test_KILLER_stim_pauli_is_trivial_discriminates():
    def prop(sp):
        assert sp.is_trivial is (sp.after_1q_depolarization == 0.0
                                 and sp.after_2q_depolarization == 0.0
                                 and sp.before_measure_flip == 0.0)
    # `wrong` -- a subclass whose is_trivial ignores the flip field (would pass a vacuous check)
    real = StimPauliNoiseSpec(before_measure_flip=0.02)
    assert real.is_trivial is False
    # sabotage: an object reporting is_trivial True despite a nonzero flip
    class _Leaky:
        after_1q_depolarization = 0.0
        after_2q_depolarization = 0.0
        before_measure_flip = 0.02
        is_trivial = True
    assert_discriminates(prop, real, _Leaky(), label="is_trivial")


def test_L0_stim_pauli_to_manifest_exact():
    m = StimPauliNoiseSpec(after_1q_depolarization=0.011, after_2q_depolarization=0.022,
                           before_measure_flip=0.033).to_manifest()
    assert m == {"type": "stim_pauli", "after_1q_depolarization": 0.011,
                 "after_2q_depolarization": 0.022, "before_measure_flip": 0.033}


# =========================================================================== #
# StimNoiseRule -- __post_init__ (every raise + normalization) + to_manifest    #
# =========================================================================== #
def test_L0_stim_noise_rule_normalizes_all_fields():
    r = StimNoiseRule(position="AFTER", match_kind="GATE_TYPE", noise="x_error",
                      args=(0.02,), gate_name="cz", target_filter=[0, 1], require_match=False)
    assert r.position == "after" and r.match_kind == "gate_type" and r.noise == "X_ERROR"
    assert r.gate_name == "CZ" and r.target_filter == (0, 1) and r.require_match is False
    assert r.args == (0.02,)
    # measure_name uppercased on a measurement rule
    rm = StimNoiseRule(position="before", match_kind="measurement_type", noise="X_ERROR",
                       args=(0.01,), measure_name="mrz")
    assert rm.measure_name == "MRZ"
    # gate_index accepts a numpy integer (kills the np.integer removal in the strict-int guard)
    ri = StimNoiseRule(position="after", match_kind="gate_index", noise="X_ERROR",
                       args=(0.01,), gate_index=np.int64(3))
    assert ri.gate_index == 3 and isinstance(ri.gate_index, int)


def test_L0_stim_noise_rule_post_init_every_raise():
    def rule(**kw):
        base = dict(position="after", match_kind="all_gates", noise="X_ERROR", args=(0.01,))
        base.update(kw)
        return lambda: StimNoiseRule(**base)
    _raises_exact(ValueError, "noise rule position must be 'after', 'before', or 'during', got 'sideways'",
                  rule(position="sideways"))
    _raises_exact(ValueError, "unsupported noise rule match_kind 'bogus'",
                  rule(match_kind="bogus"))
    _raises_exact(ValueError, "before rules currently support measurement_type only",
                  rule(position="before", match_kind="all_gates"))
    _raises_exact(ValueError, "measurement_type rules must use position='before'",
                  rule(position="after", match_kind="measurement_type", measure_name="M"))
    _raises_exact(ValueError, "during rules currently support idle only",
                  rule(position="during", match_kind="all_gates"))
    _raises_exact(ValueError, "idle rules must use position='during'",
                  rule(position="after", match_kind="idle"))
    _raises_exact(ValueError, "gate_index rules require a non-negative integer gate_index",
                  rule(match_kind="gate_index", gate_index=None))
    _raises_exact(ValueError, "gate_index rules require a non-negative integer gate_index, got 0.9",
                  rule(match_kind="gate_index", gate_index=0.9))
    _raises_exact(ValueError, "gate_index rules require a non-negative integer gate_index, got -1",
                  rule(match_kind="gate_index", gate_index=-1))
    _raises_exact(ValueError, "gate_index rules require a non-negative integer gate_index, got True",
                  rule(match_kind="gate_index", gate_index=True))
    _raises_exact(ValueError, "gate_type rules require gate_name",
                  rule(match_kind="gate_type", gate_name=None))
    _raises_exact(ValueError, "measurement_type rules require measure_name",
                  rule(position="before", match_kind="measurement_type", measure_name=None))
    _raises_exact(
        ValueError,
        "targeted frontend noise currently supports X_ERROR/Y_ERROR/Z_ERROR, "
        "DEPOLARIZE/DEPOLARIZING, DEPOLARIZE1, and DEPOLARIZE2 only; got 'FOO'",
        rule(noise="FOO"))
    _raises_exact(ValueError, "idle noise is per-qubit in this frontend slice; use DEPOLARIZE/DEPOLARIZE1",
                  rule(position="during", match_kind="idle", noise="DEPOLARIZE2"))
    _raises_exact(ValueError, "X_ERROR rules require exactly one probability argument, got 2",
                  rule(args=(0.01, 0.02)))
    _raises_exact(ValueError, "X_ERROR rules require exactly one probability argument, got 0",
                  rule(args=()))
    _raises_exact(ValueError, "noise probability must be in [0, 1), got 1.5",
                  rule(args=(1.5,)))


@pytest.mark.parametrize("noise", sorted(nspec._NOISE_INSTRUCTIONS | nspec._AUTO_DEPOLARIZE_ALIASES))
def test_L0_stim_noise_rule_accepts_every_supported_noise(noise):
    # each supported noise name/alias survives __post_init__ (kills the set-element mutations)
    r = StimNoiseRule(position="after", match_kind="all_gates", noise=noise.lower(), args=(0.01,))
    assert r.noise == noise


def test_L0_stim_noise_rule_to_manifest_exact():
    r = StimNoiseRule(position="after", match_kind="gate_index", noise="Y_ERROR", args=(0.02,),
                      gate_index=4, target_filter=(2, 3), require_match=False)
    assert r.to_manifest() == {
        "position": "after", "match_kind": "gate_index", "noise": "Y_ERROR", "args": [0.02],
        "gate_index": 4, "gate_name": None, "measure_name": None, "target_filter": [2, 3],
        "require_match": False}
    # target_filter None routes to None (not [])
    r2 = StimNoiseRule(position="after", match_kind="all_gates", noise="Z_ERROR", args=(0.01,))
    assert r2.to_manifest()["target_filter"] is None


# =========================================================================== #
# TargetedStimNoiseSpec -- __post_init__ + is_trivial + to_manifest             #
# =========================================================================== #
def test_L0_targeted_spec_post_init_coerces_rules_to_tuple():
    r = StimNoiseRule(position="after", match_kind="all_gates", noise="X_ERROR", args=(0.01,))
    spec = TargetedStimNoiseSpec([r])                 # a LIST becomes a tuple
    assert isinstance(spec.rules, tuple) and spec.rules == (r,)
    assert spec.schema == "qec_twin.simulator.TargetedStimNoiseSpec.v1"


def test_L0_targeted_spec_is_trivial_both_arcs():
    assert TargetedStimNoiseSpec(()).is_trivial is True
    r = StimNoiseRule(position="after", match_kind="all_gates", noise="X_ERROR", args=(0.01,))
    assert TargetedStimNoiseSpec((r,)).is_trivial is False


def test_L0_targeted_spec_to_manifest_exact():
    r = StimNoiseRule(position="after", match_kind="all_gates", noise="X_ERROR", args=(0.01,))
    spec = TargetedStimNoiseSpec((r,), schema="custom.schema.v2")
    assert spec.to_manifest() == {"type": "targeted_stim_pauli", "schema": "custom.schema.v2",
                                  "rules": [r.to_manifest()]}


# =========================================================================== #
# NoiseBuilder -- each fluent method + build                                    #
# =========================================================================== #
def test_L0_noise_builder_after_gate():
    nb = NoiseBuilder()
    assert nb.after_gate(2, "X_ERROR", 0.01, target_filter=(0, 1), require_match=False) is nb
    (r,) = nb.build().rules
    assert r.to_manifest() == {
        "position": "after", "match_kind": "gate_index", "noise": "X_ERROR", "args": [0.01],
        "gate_index": 2, "gate_name": None, "measure_name": None, "target_filter": [0, 1],
        "require_match": False}


def test_L0_noise_builder_after_gate_type():
    nb = NoiseBuilder()
    assert nb.after_gate_type("cz", "Y_ERROR", 0.02, target_filter=5) is nb
    (r,) = nb.build().rules
    assert r.to_manifest() == {
        "position": "after", "match_kind": "gate_type", "noise": "Y_ERROR", "args": [0.02],
        "gate_index": None, "gate_name": "CZ", "measure_name": None, "target_filter": [5],
        "require_match": True}


def test_L0_noise_builder_after_all_gates():
    nb = NoiseBuilder()
    assert nb.after_all_gates("Z_ERROR", 0.03) is nb
    (r,) = nb.build().rules
    assert r.to_manifest() == {
        "position": "after", "match_kind": "all_gates", "noise": "Z_ERROR", "args": [0.03],
        "gate_index": None, "gate_name": None, "measure_name": None, "target_filter": None,
        "require_match": True}


def test_L0_noise_builder_before_measurement_bases():
    for basis, name in [("Z", "M"), ("X", "MX"), ("Y", "MY")]:
        nb = NoiseBuilder()
        assert nb.before_measurement("X_ERROR", 0.04, basis=basis) is nb
        (r,) = nb.build().rules
        assert r.position == "before" and r.match_kind == "measurement_type"
        assert r.measure_name == name and r.args == (0.04,)
    # invalid basis raises with the exact (uppercased) message
    _raises_exact(ValueError, "measurement basis must be X, Y, or Z, got 'W'",
                  lambda: NoiseBuilder().before_measurement("X_ERROR", 0.04, basis="w"))


def test_L0_noise_builder_before_measurement_type():
    nb = NoiseBuilder()
    assert nb.before_measurement_type("mrx", "X_ERROR", 0.05, target_filter=[7]) is nb
    (r,) = nb.build().rules
    assert r.to_manifest() == {
        "position": "before", "match_kind": "measurement_type", "noise": "X_ERROR",
        "args": [0.05], "gate_index": None, "gate_name": None, "measure_name": "MRX",
        "target_filter": [7], "require_match": True}


def test_L0_noise_builder_during_idle():
    nb = NoiseBuilder()
    assert nb.during_idle("DEPOLARIZE1", 0.006, targets=(1, 2)) is nb
    (r,) = nb.build().rules
    assert r.to_manifest() == {
        "position": "during", "match_kind": "idle", "noise": "DEPOLARIZE1", "args": [0.006],
        "gate_index": None, "gate_name": None, "measure_name": None, "target_filter": [1, 2],
        "require_match": True}
    # during_idle with DEPOLARIZE2 raises inside the rule construction
    _raises_exact(ValueError, "idle noise is per-qubit in this frontend slice; use DEPOLARIZE/DEPOLARIZE1",
                  lambda: NoiseBuilder().during_idle("DEPOLARIZE2", 0.006))


def test_L0_noise_builder_build_accumulates_in_order():
    spec = (NoiseBuilder()
            .after_gate(0, "X_ERROR", 0.01)
            .after_all_gates("Z_ERROR", 0.02)
            .build())
    assert isinstance(spec, TargetedStimNoiseSpec)
    assert [r.match_kind for r in spec.rules] == ["gate_index", "all_gates"]
    # a fresh builder starts empty (kills a shared-state mutation)
    assert NoiseBuilder().build().rules == ()


# =========================================================================== #
# apply_stim_pauli_noise -- TargetedStimNoiseSpec path (+ private routing)      #
# =========================================================================== #
def test_L0_apply_targeted_full_placement_pins_steps_and_events():
    circ = _hcz_circuit()
    spec = (NoiseBuilder()
            .after_gate(0, "DEPOLARIZE1", 0.01)
            .after_gate_type("CZ", "DEPOLARIZE", 0.02)
            .after_all_gates("Z_ERROR", 0.005)
            .before_measurement("X_ERROR", 0.03)
            .during_idle("DEPOLARIZE1", 0.004)
            .build())
    noisy = apply_stim_pauli_noise(circ, spec)
    assert _steps(noisy) == [
        ("G", "H", (0,), ()),
        ("G", "DEPOLARIZE1", (0,), (0.01,)),
        ("G", "Z_ERROR", (0,), (0.005,)),
        ("G", "CZ", (0, 1), ()),
        ("G", "DEPOLARIZE2", (0, 1), (0.02,)),
        ("G", "Z_ERROR", (0, 1), (0.005,)),
        ("G", "DEPOLARIZE1", (2,), (0.004,)),
        ("T",),
        ("G", "X_ERROR", (0, 1, 2), (0.03,)),
        ("M", "M", (0, 1, 2)),
        ("D", "d0"),
    ]
    mp = noisy.metadata["noise_projection"]
    assert mp["type"] == "targeted_stim_pauli"
    assert mp["matched_counts"] == [1, 1, 2, 1, 1]
    # idle match-event dict pinned field-by-field (kills every _append_idle_noise routing mutant)
    idle_ev = mp["matched_events"][4][0]
    assert idle_ev == {"position": "during", "match_kind": "idle", "tick_index": 0,
                       "active_touched": [0, 1], "idle_targets": [2], "noise": "DEPOLARIZE1",
                       "noise_targets": [2]}
    # gate match-event dict pinned (kills _match_event routing mutants)
    assert mp["matched_events"][0][0] == {
        "position": "after", "match_kind": "gate_index", "matched_op": "H",
        "matched_targets": [0], "noise": "DEPOLARIZE1", "noise_targets": [0], "tick_index": 0,
        "gate_index": 0}
    # measurement event carries NO gate_index key (kills the `if gate_index is not None` arc)
    assert "gate_index" not in mp["matched_events"][3][0]


def test_L0_apply_targeted_auto_depolarize_resolution():
    # DEPOLARIZE alias resolves by arity: after 1q->DEPOLARIZE1, after 2q->DEPOLARIZE2, after reset->1
    for gate, targets, nq, resolved in [("H", (0,), 1, "DEPOLARIZE1"),
                                        ("CZ", (0, 1), 2, "DEPOLARIZE2"),
                                        ("R", (0,), 1, "DEPOLARIZE1")]:
        circ = _one_gate_circuit(gate, targets, nq)
        spec = NoiseBuilder().after_gate_type(gate, "DEPOLARIZE", 0.02).build()
        noisy = apply_stim_pauli_noise(circ, spec)
        assert _steps(noisy)[1] == ("G", resolved, targets, (0.02,))


def test_L0_apply_targeted_auto_depolarize_unresolvable_gate_raises():
    # a 3-target CCX has arity None -> auto-DEPOLARIZE cannot resolve
    circ = _one_gate_circuit("CCX", (0, 1, 2), 3)
    spec = NoiseBuilder().after_gate_type("CCX", "DEPOLARIZE", 0.02).build()
    _raises_exact(ValueError, "cannot auto-resolve DEPOLARIZE for gate 'CCX'",
                  lambda: apply_stim_pauli_noise(circ, spec))


def test_L0_apply_targeted_auto_depolarize_before_measurement_raises():
    circ = CircuitIR(num_qubits=1, steps=(MeasureOp("M", (0,), ("m0",)),), metadata={})
    spec = NoiseBuilder().before_measurement("DEPOLARIZE", 0.02).build()
    _raises_exact(ValueError,
                  "automatic DEPOLARIZE noise is only defined after gates, not before measurements",
                  lambda: apply_stim_pauli_noise(circ, spec))


def test_L0_apply_targeted_depolarize2_on_one_qubit_gate_raises():
    circ = _one_gate_circuit("H", (0,), 1)
    spec = NoiseBuilder().after_gate_type("H", "DEPOLARIZE2", 0.02).build()
    _raises_exact(ValueError, "DEPOLARIZE2 requires an even number of targets, got (0,)",
                  lambda: apply_stim_pauli_noise(circ, spec))


def test_L0_apply_targeted_idle_alias_and_explicit_and_I_gate():
    # idle DEPOLARIZE alias -> DEPOLARIZE1 (kills _resolve_idle_noise_name alias branch);
    # an explicit I gate does NOT mark the qubit touched, so it stays an idle candidate.
    circ = CircuitIR(num_qubits=2, steps=(GateOp("I", (0,), ()), Tick(),
                                          MeasureOp("M", (0, 1), ("m0", "m1"))), metadata={})
    spec = NoiseBuilder().during_idle("DEPOLARIZE", 0.007).build()
    noisy = apply_stim_pauli_noise(circ, spec)
    # both qubits idle (I did not touch q0) -> DEPOLARIZE1 on (0, 1)
    assert ("G", "DEPOLARIZE1", (0, 1), (0.007,)) in _steps(noisy)


def test_L0_apply_targeted_target_filter_and_measure_alias_matching():
    # target_filter selects exactly one CZ pair; a measure_name='M' rule matches an MZ instruction
    b = CircuitBuilder(num_qubits=4)
    b.cz((0, 1))
    b.cz((2, 3))
    circ = CircuitIR(num_qubits=4, steps=(*b.build().steps, MeasureOp("MZ", (0,), ("m0",))),
                     metadata={})
    spec = (NoiseBuilder()
            .after_gate_type("CZ", "Z_ERROR", 0.01, target_filter=(2, 3))
            .before_measurement("X_ERROR", 0.02, basis="Z")
            .build())
    noisy = apply_stim_pauli_noise(circ, spec)
    steps = _steps(noisy)
    # Z_ERROR only after the (2,3) CZ, not the (0,1) CZ
    assert ("G", "Z_ERROR", (2, 3), (0.01,)) in steps
    assert ("G", "Z_ERROR", (0, 1), (0.01,)) not in steps
    # X_ERROR before the MZ (measure_name 'M' alias-matches MZ)
    assert ("G", "X_ERROR", (0,), (0.02,)) in steps


def test_L0_apply_targeted_require_match_raise_and_optional_skip():
    circ = _one_gate_circuit("H", (0,), 1)          # only ONE gate (index 0)
    # a gate_index=5 rule matches nothing -> require_match raises with the exact label
    strict = NoiseBuilder().after_gate(5, "X_ERROR", 0.01).build()
    _raises_exact(ValueError,
                  "targeted noise rule(s) matched no circuit operation: ['rule[0] gate_index:5']",
                  lambda: apply_stim_pauli_noise(circ, strict))
    # require_match=False -> no raise, matched_counts records the zero
    lax = NoiseBuilder().after_gate(5, "X_ERROR", 0.01, require_match=False).build()
    noisy = apply_stim_pauli_noise(circ, lax)
    assert noisy.metadata["noise_projection"]["matched_counts"] == [0]


def test_L0_apply_targeted_rule_label_uses_gate_name_then_idle():
    # the missing-rule label falls back gate_index -> gate_name -> measure_name -> 'idle'
    circ = _one_gate_circuit("H", (0,), 1)
    spec = NoiseBuilder().after_gate_type("ZZZ", "X_ERROR", 0.01).build()
    _raises_exact(ValueError,
                  "targeted noise rule(s) matched no circuit operation: ['rule[0] gate_type:ZZZ']",
                  lambda: apply_stim_pauli_noise(circ, spec))


# =========================================================================== #
# SourceStimPauliRule -- __post_init__ + probability_for + manifests            #
# =========================================================================== #
def _source_rule(**kw):
    base = dict(position="before", match_kind="measurement_type", measure_name="M",
                noise="X_ERROR", payload_key="z", base_p=1e-3, sensitivity=1.0, z_scale=1e-4)
    base.update(kw)
    return SourceStimPauliRule(**base)


def test_L0_source_rule_post_init_normalizes_and_validates():
    r = SourceStimPauliRule(position="AFTER", match_kind="GATE_TYPE", gate_name="cz",
                            noise="x_error", payload_key="zk", base_p=2e-3, sensitivity=1.5,
                            z_scale=1e-4, target_filter=[0, 1])
    assert r.position == "after" and r.match_kind == "gate_type" and r.noise == "X_ERROR"
    assert r.gate_name == "CZ" and r.target_filter == (0, 1) and r.payload_key == "zk"
    assert r.base_p == 2e-3 and r.sensitivity == 1.5 and r.z_scale == 1e-4
    # every dedicated guard tripped
    _raises_exact(ValueError, "map_kind must be 'logit' or 'payload_probability'",
                  lambda: _source_rule(map_kind="nope"))
    _raises_exact(ValueError, "logit source projection requires base_p > 0",
                  lambda: _source_rule(map_kind="logit", base_p=0.0))
    _raises_exact(ValueError, "sensitivity must be finite, got inf",
                  lambda: _source_rule(sensitivity=float("inf")))
    _raises_exact(ValueError, "z_scale must be finite and > 0, got 0.0",
                  lambda: _source_rule(z_scale=0.0))
    _raises_exact(ValueError, "z_scale must be finite and > 0, got inf",
                  lambda: _source_rule(z_scale=float("inf")))
    _raises_exact(ValueError, "base_p must be in [0, 1), got 1.0",
                  lambda: _source_rule(base_p=1.0))
    _raises_exact(ValueError, "target_filter must contain integer targets, not a string",
                  lambda: _source_rule(target_filter="01"))
    _raises_exact(ValueError, "target_filter must contain integer targets, got 0.9",
                  lambda: _source_rule(target_filter=(0.9,)))
    # base_p==0 is fine for payload_probability (the logit>0 guard is map-gated)
    assert _source_rule(map_kind="payload_probability", base_p=0.0).base_p == 0.0


def test_L0_source_rule_probability_for_logit_and_payload():
    tl = SourceTimeline(name="tl", n_cycles=3, cycle_time_ns=1000.0,
                        payload={"z": np.asarray([1e-4, 2e-4, -1e-4])})
    r = _source_rule(base_p=1e-3, sensitivity=1.0, z_scale=1e-4)
    for c in range(3):
        got = r.probability_for(tl, cycle_index=c, targets=(0,))
        assert_pins(got, _indep_logit_prob(tl.payload_series("z")[c], 1e-3, 1e-4, 1.0),
                    rtol=1e-12, atol=0.0, label=f"logit@{c}")
    # payload_probability returns the (validated) payload value directly
    tlp = SourceTimeline(name="p", n_cycles=1, cycle_time_ns=1000.0,
                         payload={"z": np.asarray([0.42])})
    rp = _source_rule(map_kind="payload_probability")
    assert rp.probability_for(tlp, cycle_index=0, targets=(0,)) == 0.42
    # payload out of [0,1) raises with the payload-keyed name
    tlbad = SourceTimeline(name="b", n_cycles=1, cycle_time_ns=1000.0,
                           payload={"z": np.asarray([1.0])})
    _raises_exact(ValueError, "z[0] must be in [0, 1), got 1.0",
                  lambda: rp.probability_for(tlbad, cycle_index=0, targets=(0,)))
    # cycle_index guard: both operands of the `or`
    _raises_exact(IndexError, "cycle_index=-1 outside source timeline length 3",
                  lambda: r.probability_for(tl, cycle_index=-1, targets=(0,)))
    _raises_exact(IndexError, "cycle_index=3 outside source timeline length 3",
                  lambda: r.probability_for(tl, cycle_index=3, targets=(0,)))


def test_KILLER_source_rule_probability_for_logit_discriminates():
    tl = SourceTimeline(name="tl", n_cycles=1, cycle_time_ns=1000.0,
                        payload={"z": np.asarray([3e-4])})
    r = _source_rule(base_p=5e-3, sensitivity=2.0, z_scale=1e-4)

    def prop(p):
        assert_pins(p, _indep_logit_prob(3e-4, 5e-3, 1e-4, 2.0), rtol=1e-12, atol=0.0, label="p")
    # wrong: sensitivity with the OPPOSITE sign (a coefficient sabotage)
    wrong = _indep_logit_prob(3e-4, 5e-3, 1e-4, -2.0)
    assert_discriminates(prop, r.probability_for(tl, cycle_index=0, targets=(0,)), wrong,
                         label="probability_for")


@settings(max_examples=150, deadline=None)
@given(v=st.floats(-5e-4, 5e-4, allow_nan=False, allow_infinity=False),
       base=st.floats(1e-4, 0.2, allow_nan=False), sens=st.floats(-3.0, 3.0, allow_nan=False))
def test_L1_source_rule_logit_matches_independent(v, base, sens):
    tl = SourceTimeline(name="tl", n_cycles=1, cycle_time_ns=1000.0,
                        payload={"z": np.asarray([v])})
    r = _source_rule(base_p=base, sensitivity=sens, z_scale=1e-4)
    got = r.probability_for(tl, cycle_index=0, targets=(0,))
    assert 0.0 <= got < 1.0
    assert_pins(got, _indep_logit_prob(v, base, 1e-4, sens), rtol=1e-9, atol=1e-15, label="logit")


def test_L0_source_rule_to_public_manifest_exact_no_leak():
    r = _source_rule(base_p=2e-3, sensitivity=1.5, z_scale=1e-4)
    assert r.to_public_manifest() == {
        "position": "before", "match_kind": "measurement_type", "noise": "X_ERROR",
        "gate_index": None, "gate_name": None, "measure_name": "M", "target_filter": None,
        "require_match": True, "probability_source": "evaluator_only_source_projection_binding"}


def test_L0_source_rule_to_manifest_exact_full():
    r = _source_rule(base_p=2e-3, sensitivity=1.5, z_scale=1e-4, payload_key="zk")
    assert r.to_manifest() == {
        "position": "before", "match_kind": "measurement_type", "noise": "X_ERROR",
        "payload_key": "zk", "map_kind": "logit", "base_p": 2e-3, "sensitivity": 1.5,
        "z_scale": 1e-4, "gate_index": None, "gate_name": None, "measure_name": "M",
        "target_filter": None, "require_match": True}


def test_KILLER_source_rule_public_manifest_hides_conditioning_fields():
    r = _source_rule(base_p=2e-3, sensitivity=1.5, z_scale=1e-4, payload_key="zk")
    leak_tokens = ("payload_key", "map_kind", "base_p", "sensitivity", "z_scale")

    def no_leak(m):
        blob = json.dumps(m)
        for tok in leak_tokens:
            assert tok not in blob, f"leaked {tok}"
    # the FULL manifest carries every conditioning field; the public one carries none
    assert_discriminates(no_leak, r.to_public_manifest(), r.to_manifest(),
                         label="public manifest isolation")
    assert set(r.to_manifest()) - set(r.to_public_manifest()) == {
        "payload_key", "map_kind", "base_p", "sensitivity", "z_scale"}


# =========================================================================== #
# SourceStimPauliProjectionSpec -- __post_init__ + is_trivial + source_timeline #
# + to_manifest + to_evaluator_manifest                                         #
# =========================================================================== #
def _proj_timeline(**kw):
    base = dict(name="src_tl", n_cycles=3, cycle_time_ns=500.0,
                payload={"zk": np.asarray([1e-4, 2e-4, 3e-4])}, coupling_mode="shared")
    base.update(kw)
    return SourceTimeline(**base)


def test_L0_source_proj_post_init_all_arcs():
    tl = _proj_timeline()
    rule = _source_rule(payload_key="zk")
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(rule,))     # default binding
    assert spec.source_binding is not None and spec.source_binding.cycle_binding == "circuit_tick"
    assert isinstance(spec.rules, tuple)
    # empty rules
    _raises_exact(ValueError, "SourceStimPauliProjectionSpec requires at least one rule",
                  lambda: SourceStimPauliProjectionSpec(timeline=tl, rules=()))
    # rule payload key missing from timeline
    _raises_arg(KeyError, "source projection payload key(s) missing from timeline: ['nope']",
                lambda: SourceStimPauliProjectionSpec(timeline=tl, rules=(_source_rule(payload_key="nope"),)))


def test_L0_source_proj_post_init_binding_arcs():
    from error_coupling_simulator.frontend.source_sidecar import SourceTimelineBinding
    tl = _proj_timeline()
    rule = _source_rule(payload_key="zk")
    # a non-tick binding raises NotImplementedError
    _raises_exact(
        NotImplementedError,
        "SourceStimPauliProjectionSpec currently executes source cycles as CircuitIR TICK "
        "indices; use source_binding=SourceTimelineBinding(cycle_binding='circuit_tick')",
        lambda: SourceStimPauliProjectionSpec(
            timeline=tl, rules=(rule,),
            source_binding=SourceTimelineBinding(cycle_binding="qec_round")))
    # a tick binding whose payload_keys OMIT a rule key raises
    tl2 = _proj_timeline(payload={"zk": np.asarray([1e-4, 2e-4, 3e-4]),
                                  "other": np.asarray([0.0, 0.0, 0.0])})
    _raises_exact(
        ValueError,
        "source projection binding payload_keys omit rule payload key(s): ['zk']",
        lambda: SourceStimPauliProjectionSpec(
            timeline=tl2, rules=(rule,),
            source_binding=SourceTimelineBinding(cycle_binding="circuit_tick",
                                                 payload_keys=("other",))))
    # an EMPTY payload_keys binding skips the omit check (the `if binding.payload_keys` False arc)
    spec = SourceStimPauliProjectionSpec(
        timeline=tl, rules=(rule,),
        source_binding=SourceTimelineBinding(cycle_binding="circuit_tick", payload_keys=()))
    assert spec.source_binding.payload_keys == ()
    # a covering payload_keys binding passes (True arc, omitted empty)
    spec2 = SourceStimPauliProjectionSpec(
        timeline=tl, rules=(rule,),
        source_binding=SourceTimelineBinding(cycle_binding="circuit_tick", payload_keys=("zk",)))
    assert spec2.source_binding.payload_keys == ("zk",)


def test_L0_source_proj_is_trivial_and_source_timeline():
    tl = _proj_timeline()
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(_source_rule(payload_key="zk"),))
    assert spec.is_trivial is False        # a source projection is NEVER trivial
    assert spec.source_timeline is tl      # returns the exact timeline object


def test_L0_source_proj_to_manifest_exact_and_no_leak():
    tl = _proj_timeline()
    rule = _source_rule(payload_key="zk", base_p=2e-3, sensitivity=1.5, z_scale=1e-4)
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(rule,))
    assert spec.to_manifest() == {
        "type": "stim_pauli_source_projection",
        "schema": "qec_twin.simulator.SourceStimPauliProjectionSpec.v1",
        "visibility": "reduced_public_summary",
        "representability": "reduced_pauli_projection_not_analog_truth",
        "source": {"sidecar_required": True, "cycle_binding": "circuit_tick",
                   "n_cycles": 3, "cycle_time_ns": 500.0},
        "rules": [rule.to_public_manifest()],
        "boundary": ("Executable frontend projection into Stim Pauli noise. This is not "
                     "joint-Lindbladian, coherent, leakage, or full analog source truth."),
    }
    # isolation: the public projection manifest leaks NONE of the conditioning fields
    blob = json.dumps(spec.to_manifest())
    for tok in ("payload_key", "map_kind", "base_p", "sensitivity", "z_scale", "coupling_mode"):
        assert tok not in blob, f"public manifest leaked {tok}"


def test_L0_source_proj_to_evaluator_manifest_exact_carries_conditioning():
    tl = _proj_timeline()
    rule = _source_rule(payload_key="zk", base_p=2e-3, sensitivity=1.5, z_scale=1e-4)
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(rule,))
    assert spec.to_evaluator_manifest() == {
        "type": "stim_pauli_source_projection",
        "schema": "qec_twin.simulator.SourceStimPauliProjectionSpec.v1",
        "visibility": "evaluator_only",
        "representability": "reduced_pauli_projection_not_analog_truth",
        "source_cycle_map": "CircuitIR TICK index; cycle 0 is before the first TICK",
        "source_timeline": {"name": "src_tl", "schema": _TL_SCHEMA, "n_cycles": 3,
                            "cycle_time_ns": 500.0, "coupling_mode": "shared"},
        "rules": [rule.to_manifest()],
        "execution_status": _EXEC_STATUS,
    }
    # the evaluator manifest DOES carry the conditioning fields the public one hides
    blob = json.dumps(spec.to_evaluator_manifest())
    for tok in ("payload_key", "base_p", "sensitivity", "z_scale", "coupling_mode"):
        assert tok in blob, f"evaluator manifest missing {tok}"


def test_KILLER_source_proj_public_vs_evaluator_discriminates():
    tl = _proj_timeline()
    spec = SourceStimPauliProjectionSpec(
        timeline=tl, rules=(_source_rule(payload_key="zk"),))

    def no_conditioning_leak(m):
        assert "payload_key" not in json.dumps(m)
    # public manifest hides payload_key; evaluator manifest exposes it -> discriminated
    assert_discriminates(no_conditioning_leak, spec.to_manifest(), spec.to_evaluator_manifest(),
                         label="projection isolation")


# =========================================================================== #
# apply_stim_pauli_noise -- SourceStimPauliProjectionSpec path (private routing) #
# =========================================================================== #
def _source_circuit():
    b = CircuitBuilder(num_qubits=2)
    b.x(0)
    b.tick()
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0",))
    b.detector("d1", xor=("m1",))
    return b.build()


def test_L0_apply_source_projection_pins_steps_manifest_and_audit():
    circ = _source_circuit()
    tl = SourceTimeline(name="tl", n_cycles=2, cycle_time_ns=1000.0,
                        payload={"p_gate": np.asarray([0.1, 0.2]),
                                 "p_meas": np.asarray([0.3, 0.4]),
                                 "p_idle": np.asarray([0.05, 0.06])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_type", gate_name="X",
                            noise="X_ERROR", payload_key="p_gate", map_kind="payload_probability"),
        SourceStimPauliRule(position="during", match_kind="idle", noise="X_ERROR",
                            payload_key="p_idle", map_kind="payload_probability", target_filter=(1,)),
        SourceStimPauliRule(position="before", match_kind="measurement_type", measure_name="M",
                            noise="X_ERROR", payload_key="p_meas", map_kind="payload_probability")))
    noisy = apply_stim_pauli_noise(circ, spec)
    # gate noise uses cycle 0 (0.1); idle uses cycle 0 (0.05) on q1; measure uses cycle 1 (0.4)
    assert _steps(noisy) == [
        ("G", "X", (0,), ()),
        ("G", "X_ERROR", (0,), (0.1,)),
        ("G", "X_ERROR", (1,), (0.05,)),
        ("T",),
        ("G", "X_ERROR", (0, 1), (0.4,)),
        ("M", "M", (0, 1)),
        ("D", "d0"),
        ("D", "d1"),
    ]
    mp = noisy.metadata["noise_projection"]
    assert mp["type"] == "stim_pauli_source_projection"
    assert mp["visibility"] == "reduced_public_summary"       # public summary in the circuit meta
    assert mp["matched_counts"] == [1, 1, 1]
    assert mp["skipped_outside_timeline"] == [0, 0, 0]
    assert mp["matched_event_counts"] == [1, 1, 1]
    assert "payload_key" not in json.dumps(mp)                # no conditioning leak in circuit meta
    # the evaluator audit lives under the private key and carries the full events
    assert _AUDIT_KEY in noisy.metadata
    audit = noisy.metadata[_AUDIT_KEY]
    assert audit["visibility"] == "evaluator_only"
    assert audit["matched_counts"] == [1, 1, 1]
    # gate match-event dict pinned field-by-field (kills _source_match_event routing mutants)
    assert audit["matched_events"][0][0] == {
        "position": "after", "match_kind": "gate_type", "noise": "X_ERROR", "noise_targets": [0],
        "tick_index": 0, "source_cycle": 0, "source_cycle_binding": "circuit_tick",
        "projected_probability": 0.1, "payload_key": "p_gate",
        "site_reduction": "global_cycle_payload", "matched_op": "X", "matched_targets": [0],
        "gate_index": 0}
    # idle event has matched_op IDLE + no gate_index
    idle_ev = audit["matched_events"][1][0]
    assert idle_ev["matched_op"] == "IDLE" and idle_ev["matched_targets"] == [1]
    assert "gate_index" not in idle_ev
    # measurement event has no gate_index but a source_cycle of 1
    meas_ev = audit["matched_events"][2][0]
    assert meas_ev["source_cycle"] == 1 and "gate_index" not in meas_ev


def test_L0_apply_source_projection_2d_per_target_split():
    # a 2-D site payload splits an X_ERROR measurement into per-target probabilities
    b = CircuitBuilder(num_qubits=2)
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0",))
    b.detector("d1", xor=("m1",))
    circ = b.build()
    tl = SourceTimeline(name="site", n_cycles=1, cycle_time_ns=1000.0,
                        payload={"p": np.asarray([[0.2, 0.4]])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="before", match_kind="measurement_type", measure_name="M",
                            noise="X_ERROR", payload_key="p", map_kind="payload_probability"),))
    noisy = apply_stim_pauli_noise(circ, spec)
    steps = _steps(noisy)
    assert ("G", "X_ERROR", (0,), (0.2,)) in steps
    assert ("G", "X_ERROR", (1,), (0.4,)) in steps
    # the single rule matched TWICE (one per site) -> kills the `matched[i] += 1` -> `= 1` mutant
    assert noisy.metadata["noise_projection"]["matched_counts"] == [2]
    events = noisy.metadata[_AUDIT_KEY]["matched_events"][0]
    assert [e["site_reduction"] for e in events] == ["per_target_from_site_payload"] * 2


def test_L0_apply_source_projection_2d_depolarize2_pair_split():
    # a 2-D site payload splits a DEPOLARIZE2 after CX into per-pair MEANs
    b = CircuitBuilder(num_qubits=4)
    b.cx((0, 1, 2, 3))
    circ = b.build()
    tl = SourceTimeline(name="site", n_cycles=1, cycle_time_ns=1000.0,
                        payload={"p": np.asarray([[0.1, 0.3, 0.2, 0.6]])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_type", gate_name="CX",
                            noise="DEPOLARIZE2", payload_key="p", map_kind="payload_probability"),))
    noisy = apply_stim_pauli_noise(circ, spec)
    steps = _steps(noisy)
    # mean(0.1,0.3)=0.2 on (0,1); mean(0.2,0.6)=0.4 on (2,3)
    assert ("G", "DEPOLARIZE2", (0, 1), (0.2,)) in steps
    assert ("G", "DEPOLARIZE2", (2, 3), (0.4,)) in steps
    events = noisy.metadata[_AUDIT_KEY]["matched_events"][0]
    assert [e["site_reduction"] for e in events] == ["per_pair_mean_from_site_payload"] * 2


def _two_measurement_circuit():
    # a measurement at tick 0 (in-window) and one at tick 1 (out of a 1-cycle timeline)
    b = CircuitBuilder(num_qubits=1)
    b.measure(0, key="m0")
    b.detector("d0", xor=("m0",))
    b.tick()
    b.measure(0, key="m1")
    b.detector("d1", xor=("m1",))
    return b.build()


def test_L0_apply_source_projection_require_match_and_skip():
    # in-window match at tick 0, skipped at tick 1 -> ONLY the skipped>0 missing branch fires
    circ = _two_measurement_circuit()
    tl_short = SourceTimeline(name="s", n_cycles=1, cycle_time_ns=1000.0,
                              payload={"p": np.asarray([0.2])})
    strict = SourceStimPauliProjectionSpec(timeline=tl_short, rules=(
        SourceStimPauliRule(position="before", match_kind="measurement_type", measure_name="M",
                            noise="X_ERROR", payload_key="p", map_kind="payload_probability"),))
    _raises_exact(
        ValueError,
        "source projection rule(s) were not fully covered by the source timeline: "
        "['source_rule[0] measurement_type:M']",
        lambda: apply_stim_pauli_noise(circ, strict))
    # require_match=False -> skip, recorded in skipped_outside_timeline (matched 1 in-window, skipped 1)
    lax = SourceStimPauliProjectionSpec(timeline=tl_short, rules=(
        SourceStimPauliRule(position="before", match_kind="measurement_type", measure_name="M",
                            noise="X_ERROR", payload_key="p", map_kind="payload_probability",
                            require_match=False),))
    noisy = apply_stim_pauli_noise(circ, lax)
    mp = noisy.metadata["noise_projection"]
    assert mp["matched_counts"] == [1] and mp["skipped_outside_timeline"] == [1]
    # exactly one X_ERROR inserted (at the in-window tick-0 measurement, prob 0.2)
    assert _steps(noisy).count(("G", "X_ERROR", (0,), (0.2,))) == 1


def test_L0_apply_source_projection_no_match_require_raises():
    # a gate_type rule matching no gate (count 0, not skipped) -> require_match missing raise
    circ = _source_circuit()
    tl = SourceTimeline(name="t", n_cycles=2, cycle_time_ns=1000.0,
                        payload={"p": np.asarray([0.1, 0.1])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_type", gate_name="ZZZ",
                            noise="X_ERROR", payload_key="p", map_kind="payload_probability"),))
    _raises_exact(
        ValueError,
        "source projection rule(s) were not fully covered by the source timeline: "
        "['source_rule[0] gate_type:ZZZ']",
        lambda: apply_stim_pauli_noise(circ, spec))


def test_L0_apply_source_projection_logit_probability_pinned():
    # the logit map end-to-end: X gate at cycle 0 -> projected sigmoid probability on the step
    b = CircuitBuilder(num_qubits=1)
    b.x(0)
    circ = b.build()
    tl = SourceTimeline(name="z", n_cycles=1, cycle_time_ns=1000.0,
                        payload={"z": np.asarray([2e-4])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_type", gate_name="X",
                            noise="X_ERROR", payload_key="z", base_p=1e-3, sensitivity=2.0,
                            z_scale=1e-4),))
    noisy = apply_stim_pauli_noise(circ, spec)
    # find the inserted X_ERROR and pin its probability against the independent logit recompute
    xerr = [s for s in noisy.steps if isinstance(s, GateOp) and s.name == "X_ERROR"]
    assert len(xerr) == 1
    assert_pins(xerr[0].args[0], _indep_logit_prob(2e-4, 1e-3, 1e-4, 2.0), rtol=1e-12, atol=0.0,
                label="projected p")


# =========================================================================== #
# PRIVATE HELPERS -- direct value-pins (mutation teeth on covered helper lines)  #
# =========================================================================== #
def test_private_optional_targets_all_forms():
    assert nspec._optional_targets(None) is None
    assert nspec._optional_targets(3) == (3,)
    assert nspec._optional_targets((1, 2)) == (1, 2)
    assert nspec._optional_targets([4, 5]) == (4, 5)


def test_private_strict_optional_targets_forms_and_guards():
    assert nspec._strict_optional_targets("tf", None) is None
    assert nspec._strict_optional_targets("tf", 3) == (3,)
    assert nspec._strict_optional_targets("tf", np.int64(2)) == (2,)
    assert nspec._strict_optional_targets("tf", [0, 1]) == (0, 1)
    _raises_exact(ValueError, "tf must contain integer targets, not a string",
                  lambda: nspec._strict_optional_targets("tf", "01"))
    _raises_exact(ValueError, "tf must contain integer targets, got 0.5",
                  lambda: nspec._strict_optional_targets("tf", [0.5]))
    # a bool is rejected even though it is an int subclass
    _raises_exact(ValueError, "tf must contain integer targets, got True",
                  lambda: nspec._strict_optional_targets("tf", [True]))
    _raises_exact(ValueError, "tf must contain integer targets, not a string",
                  lambda: nspec._strict_optional_targets("tf", b"01"))


def test_private_strict_nonnegative_int_guards():
    assert nspec._strict_nonnegative_int("gi", 0) == 0
    assert nspec._strict_nonnegative_int("gi", np.int64(5)) == 5
    _raises_exact(ValueError, "gi rules require a non-negative integer gi",
                  lambda: nspec._strict_nonnegative_int("gi", None))
    _raises_exact(ValueError, "gi rules require a non-negative integer gi, got 1.5",
                  lambda: nspec._strict_nonnegative_int("gi", 1.5))
    _raises_exact(ValueError, "gi rules require a non-negative integer gi, got True",
                  lambda: nspec._strict_nonnegative_int("gi", True))
    _raises_exact(ValueError, "gi rules require a non-negative integer gi, got -2",
                  lambda: nspec._strict_nonnegative_int("gi", -2))


def test_private_validate_probability_boundaries():
    assert nspec._validate_probability("p", 0) == 0.0
    assert nspec._validate_probability("p", 0.999) == 0.999
    _raises_exact(ValueError, "p must be in [0, 1), got 1.0",
                  lambda: nspec._validate_probability("p", 1.0))
    _raises_exact(ValueError, "p must be in [0, 1), got -0.001",
                  lambda: nspec._validate_probability("p", -0.001))
    _raises_exact(ValueError, "p must be in [0, 1), got nan",
                  lambda: nspec._validate_probability("p", float("nan")))


def test_private_payload_value_for_targets_1d_2d_and_guards():
    p1 = np.asarray([0.1, 0.2, 0.3])
    assert nspec._payload_value_for_targets(p1, cycle_index=1, targets=(0,)) == 0.2
    p2 = np.asarray([[0.1, 0.2, 0.4], [0.5, 0.6, 0.7]])
    # 2-D with targets: mean over selected sites
    assert nspec._payload_value_for_targets(p2, cycle_index=0, targets=(0, 2)) == pytest.approx(0.25)
    # 2-D without targets: mean over the whole cycle row
    assert nspec._payload_value_for_targets(p2, cycle_index=1, targets=()) == pytest.approx(0.6)
    # out-of-range site raises
    _raises_exact(ValueError, "source payload has 3 sites but matched targets were (5,)",
                  lambda: nspec._payload_value_for_targets(p2, cycle_index=0, targets=(5,)))
    # neither 1-D nor 2-D raises
    p3 = np.zeros((2, 2, 2))
    _raises_exact(ValueError, "source payload must be 1-D or 2-D, got shape (2, 2, 2)",
                  lambda: nspec._payload_value_for_targets(p3, cycle_index=0, targets=(0,)))


def test_private_gate_arity_all_branches():
    assert nspec._gate_arity(GateOp("H", (0,), ())) == 1
    assert nspec._gate_arity(GateOp("R", (0,), ())) == 1
    assert nspec._gate_arity(GateOp("RX", (0,), ())) == 1
    assert nspec._gate_arity(GateOp("CZ", (0, 1), ())) == 2
    assert nspec._gate_arity(GateOp("CCX", (0, 1, 2), ())) is None


def test_private_resolve_noise_name_and_idle_name():
    # explicit noise passes through
    assert nspec._resolve_noise_name("X_ERROR", GateOp("H", (0,), ())) == "X_ERROR"
    # DEPOLARIZE alias resolves by arity
    assert nspec._resolve_noise_name("DEPOLARIZE", GateOp("H", (0,), ())) == "DEPOLARIZE1"
    assert nspec._resolve_noise_name("DEPOLARIZING", GateOp("CZ", (0, 1), ())) == "DEPOLARIZE2"
    # idle name resolution
    assert nspec._resolve_idle_noise_name("DEPOLARIZE") == "DEPOLARIZE1"
    assert nspec._resolve_idle_noise_name("X_ERROR") == "X_ERROR"
    _raises_exact(ValueError, "idle noise is per-qubit in this frontend slice; use DEPOLARIZE/DEPOLARIZE1",
                  lambda: nspec._resolve_idle_noise_name("DEPOLARIZE2"))


def test_private_validate_noise_targets_branches():
    assert nspec._validate_noise_targets("X_ERROR", (0,)) is None
    assert nspec._validate_noise_targets("DEPOLARIZE1", (0, 1)) is None
    assert nspec._validate_noise_targets("DEPOLARIZE2", (0, 1)) is None
    _raises_exact(ValueError, "X_ERROR requires at least one target",
                  lambda: nspec._validate_noise_targets("X_ERROR", ()))
    _raises_exact(ValueError, "DEPOLARIZE2 requires an even number of targets, got (0, 1, 2)",
                  lambda: nspec._validate_noise_targets("DEPOLARIZE2", (0, 1, 2)))
    _raises_exact(ValueError, "unsupported frontend noise instruction 'CORRELATED_ERROR'",
                  lambda: nspec._validate_noise_targets("CORRELATED_ERROR", (0,)))


def test_private_source_projection_execution_status_exact():
    assert nspec._source_projection_execution_status() == _EXEC_STATUS
    assert nspec.SOURCE_PROJECTION_AUDIT_METADATA_KEY == "_source_projection_evaluator_audit"


# =========================================================================== #
# ADDED mutation teeth: builder default-args, matching truth tables, multi-tick #
# counters, source routing edge cases, defensive branches                       #
# =========================================================================== #
@pytest.mark.parametrize("make", [
    lambda nb, **kw: nb.after_gate(0, "X_ERROR", 0.01, **kw),
    lambda nb, **kw: nb.after_gate_type("H", "X_ERROR", 0.01, **kw),
    lambda nb, **kw: nb.after_all_gates("X_ERROR", 0.01, **kw),
    lambda nb, **kw: nb.before_measurement("X_ERROR", 0.01, **kw),
    lambda nb, **kw: nb.before_measurement_type("M", "X_ERROR", 0.01, **kw),
])
def test_L0_noise_builder_require_match_and_target_filter_default_args(make):
    # default require_match -> the bool True (identity kills require_match=None / =bool(None) /
    # the `require_match: bool = True` -> False default mutation)
    assert make(NoiseBuilder()).build().rules[0].require_match is True
    # explicit False -> False (kills the `require_match=bool(require_match)` line-removed mutant,
    # whose StimNoiseRule default would be True)
    assert make(NoiseBuilder(), require_match=False).build().rules[0].require_match is False
    # a non-None target_filter routes through _optional_targets (kills target_filter=None / arg->None)
    assert make(NoiseBuilder(), target_filter=(1, 2)).build().rules[0].target_filter == (1, 2)


def test_L0_noise_builder_during_idle_default_args():
    assert NoiseBuilder().during_idle("X_ERROR", 0.01).build().rules[0].require_match is True
    r = NoiseBuilder().during_idle("X_ERROR", 0.01, require_match=False).build().rules[0]
    assert r.require_match is False
    assert NoiseBuilder().during_idle("X_ERROR", 0.01, targets=(1, 2)).build().rules[0].target_filter == (1, 2)


def _mrule(measure_name, target_filter=None):
    return StimNoiseRule(position="before", match_kind="measurement_type",
                         measure_name=measure_name, noise="X_ERROR", args=(0.01,),
                         target_filter=target_filter)


def _meas(name, targets=(0,)):
    return MeasureOp(name, targets, tuple(f"k{i}" for i in range(len(targets))))


def test_private_rule_matches_measurement_truth_table():
    m = nspec._rule_matches_measurement
    # not a measurement rule -> False (kills the `match_kind != 'measurement_type'` guard)
    grule = StimNoiseRule(position="after", match_kind="all_gates", noise="X_ERROR", args=(0.01,))
    assert m(grule, _meas("M")) is False
    # exact-name match (kills `step.name == measure_name` -> `!=`)
    assert m(_mrule("MRZ"), _meas("MRZ")) is True
    # 'M' alias set: MZ/MR/MRZ match (kills element wrap/case + the `and`->`or`), MX does not
    assert m(_mrule("M"), _meas("MZ")) is True
    assert m(_mrule("M"), _meas("MR")) is True
    assert m(_mrule("M"), _meas("MRZ")) is True
    assert m(_mrule("M"), _meas("MX")) is False
    # 'MX' alias set: MX/MRX match, MY does not (kills the MX-branch and->or / ==-> != / in->not in)
    assert m(_mrule("MX"), _meas("MX")) is True
    assert m(_mrule("MX"), _meas("MRX")) is True
    assert m(_mrule("MX"), _meas("MY")) is False
    # 'MY' alias set: MY/MRY match, MX does not
    assert m(_mrule("MY"), _meas("MY")) is True
    assert m(_mrule("MY"), _meas("MRY")) is True
    assert m(_mrule("MY"), _meas("MX")) is False
    # a measure_name matching nothing -> the final `return False`
    assert m(_mrule("MPP"), _meas("M")) is False
    # target_filter mismatch -> False (kills `tuple(step.targets)`->`tuple(None)` + `!=`->`==`);
    # a matching filter proceeds to the name check
    assert m(_mrule("M", target_filter=(1,)), _meas("M", (0,))) is False
    assert m(_mrule("M", target_filter=(0,)), _meas("M", (0,))) is True


def test_L0_apply_targeted_multitick_gate_index_and_tick_index():
    b = CircuitBuilder(num_qubits=2)
    b.h(0)
    b.x(1)
    b.tick()
    b.cz((0, 1))
    b.tick()
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0",))
    b.detector("d1", xor=("m1",))
    circ = b.build()
    spec = NoiseBuilder().after_all_gates("Z_ERROR", 0.01).before_measurement("X_ERROR", 0.02).build()
    noisy = apply_stim_pauli_noise(circ, spec)
    mp = noisy.metadata["noise_projection"]
    # all_gates matched all 3 gates, measurement once (kills `matched[i] += 1` -> `= 1`)
    assert mp["matched_counts"] == [3, 1]
    # gate_index counts 0,1,2 across gates; tick_index 0,0,1 (kills gate_index/tick_index +=1 mutants)
    events = [(e["matched_op"], e["gate_index"], e["tick_index"]) for e in mp["matched_events"][0]]
    assert events == [("H", 0, 0), ("X", 1, 0), ("CZ", 2, 1)]
    # the measurement lands at tick_index 2 (kills tick_index = 1 / -= 1 / += 2 on the final tick)
    assert mp["matched_events"][1][0]["tick_index"] == 2


def test_L0_apply_targeted_measurement_rule_matches_twice():
    b = CircuitBuilder(num_qubits=1)
    b.measure(0, key="m0")
    b.detector("d0", xor=("m0",))
    b.measure(0, key="m1")
    b.detector("d1", xor=("m1",))
    circ = b.build()
    noisy = apply_stim_pauli_noise(circ, NoiseBuilder().before_measurement("X_ERROR", 0.03).build())
    # the measurement rule matched BOTH measurements -> kills the measurement `matched[i] += 1` -> `= 1`
    assert noisy.metadata["noise_projection"]["matched_counts"] == [2]


def test_L0_apply_targeted_measurement_rule_mismatch_no_insert():
    # an MX rule on a Z 'M' measurement must NOT insert -> kills the
    # `position == 'before' and _rule_matches_measurement(...)` -> `or`
    b = CircuitBuilder(num_qubits=1)
    b.measure(0, key="m0")
    b.detector("d0", xor=("m0",))
    circ = b.build()
    spec = NoiseBuilder().before_measurement("X_ERROR", 0.03, basis="X", require_match=False).build()
    noisy = apply_stim_pauli_noise(circ, spec)
    assert noisy.metadata["noise_projection"]["matched_counts"] == [0]
    assert all(not (isinstance(s, GateOp) and s.name == "X_ERROR") for s in noisy.steps)


def test_L0_apply_targeted_idle_with_target_filter_and_break_guard():
    b = CircuitBuilder(num_qubits=3)
    b.x(0)
    b.x(1)
    b.tick()
    b.measure((0, 1, 2), key=("a", "b", "c"))
    b.detector("d", xor=("a",))
    circ = b.build()
    # an idle rule WITH an explicit target_filter reaches set(rule.target_filter) (kills set(None))
    n1 = apply_stim_pauli_noise(circ, NoiseBuilder().during_idle("X_ERROR", 0.02, targets=(2,)).build())
    assert ("G", "X_ERROR", (2,), (0.02,)) in _steps(n1)
    # two idle rules: the FIRST has an empty idle set (target 0 already touched); the SECOND (target
    # 2) must still fire -> kills the `continue` -> `break` mutant that would abort the rule loop
    spec = (NoiseBuilder()
            .during_idle("X_ERROR", 0.01, targets=(0,), require_match=False)
            .during_idle("Y_ERROR", 0.02, targets=(2,))
            .build())
    n2 = apply_stim_pauli_noise(circ, spec)
    assert n2.metadata["noise_projection"]["matched_counts"] == [0, 1]
    assert ("G", "Y_ERROR", (2,), (0.02,)) in _steps(n2)


def test_L0_apply_source_multitick_gate_index_and_measurement_cycle():
    b = CircuitBuilder(num_qubits=2)
    b.x(0)
    b.h(1)
    b.tick()
    b.cx((0, 1))
    b.tick()
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0",))
    b.detector("d1", xor=("m1",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=3, cycle_time_ns=1000.0,
                        payload={"p": np.asarray([0.1, 0.2, 0.3])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_index", gate_index=2, noise="X_ERROR",
                            payload_key="p", map_kind="payload_probability"),
        SourceStimPauliRule(position="before", match_kind="measurement_type", measure_name="M",
                            noise="X_ERROR", payload_key="p", map_kind="payload_probability")))
    noisy = apply_stim_pauli_noise(circ, spec)
    # gate_index rule fires on the CX (gate 2, tick 1 -> cycle 1 -> 0.2); measurement rule fires at
    # tick 2 -> cycle 2 -> 0.3. This pins the gate_index counter, the tick_index counter, the
    # gate_index passed into matching, and the _source_rule_as_stim_rule gate_index route.
    assert _steps(noisy) == [
        ("G", "X", (0,), ()), ("G", "H", (1,), ()), ("T",),
        ("G", "CX", (0, 1), ()), ("G", "X_ERROR", (0, 1), (0.2,)), ("T",),
        ("G", "X_ERROR", (0, 1), (0.3,)), ("M", "M", (0, 1)), ("D", "d0"), ("D", "d1"),
    ]
    assert noisy.metadata["noise_projection"]["matched_counts"] == [1, 1]


def test_L0_apply_source_idle_no_target_filter_and_I_gate():
    b = CircuitBuilder(num_qubits=2)
    b.x(0)
    b.idle(1)               # an explicit I gate: does NOT mark q1 as touched
    b.tick()
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0",))
    b.detector("d1", xor=("m1",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=2, cycle_time_ns=1000.0,
                        payload={"p": np.asarray([0.05, 0.06])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="during", match_kind="idle", noise="X_ERROR", payload_key="p",
                            map_kind="payload_probability"),))       # NO target_filter -> range(num_qubits)
    noisy = apply_stim_pauli_noise(circ, spec)
    # q0 touched by X, q1 only by an I (which does NOT touch) -> only q1 idle at tick 0 -> X_ERROR(0.05)
    # kills num_qubits->None, set(range(...)) mutants, and `step.name != 'I'` -> `== 'I'` / wrap / case
    assert ("G", "X_ERROR", (1,), (0.05,)) in _steps(noisy)
    assert ("G", "X_ERROR", (0,), (0.05,)) not in _steps(noisy)


def test_L0_apply_source_gate_target_filter_selects_one_pair():
    b = CircuitBuilder(num_qubits=4)
    b.cz((0, 1))
    b.cz((2, 3))
    b.measure((0, 1, 2, 3), key=("a", "b", "c", "d"))
    for i, k in enumerate("abcd"):
        b.detector(f"det{i}", xor=(k,))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.2])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_type", gate_name="CZ", noise="Z_ERROR",
                            payload_key="p", map_kind="payload_probability", target_filter=(2, 3)),))
    noisy = apply_stim_pauli_noise(circ, spec)
    steps = _steps(noisy)
    # the target_filter selects ONLY the (2,3) CZ (kills the _source_rule_as_stim_rule target_filter drop)
    assert ("G", "Z_ERROR", (2, 3), (0.2,)) in steps
    assert ("G", "Z_ERROR", (0, 1), (0.2,)) not in steps
    assert noisy.metadata["noise_projection"]["matched_counts"] == [1]


def test_L0_apply_source_depolarize_alias_uses_matched_step_arity():
    b = CircuitBuilder(num_qubits=2)
    b.cx((0, 1))
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0",))
    b.detector("d1", xor=("m1",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.15])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_type", gate_name="CX", noise="DEPOLARIZE",
                            payload_key="p", map_kind="payload_probability"),))
    noisy = apply_stim_pauli_noise(circ, spec)
    # DEPOLARIZE alias resolves via the matched CX step's arity -> DEPOLARIZE2 (kills the
    # `_resolve_noise_name(probe.noise, matched_step)` -> `..., None` mutant, which AttributeErrors)
    assert ("G", "DEPOLARIZE2", (0, 1), (0.15,)) in _steps(noisy)


def test_L0_apply_source_multi_skip_records_counts_and_audit():
    b = CircuitBuilder(num_qubits=1)
    b.measure(0, key="m0")
    b.detector("d0", xor=("m0",))
    b.tick()
    b.measure(0, key="m1")
    b.detector("d1", xor=("m1",))
    b.tick()
    b.measure(0, key="m2")
    b.detector("d2", xor=("m2",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.2])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="before", match_kind="measurement_type", measure_name="M",
                            noise="X_ERROR", payload_key="p", map_kind="payload_probability",
                            require_match=False),))
    noisy = apply_stim_pauli_noise(circ, spec)
    mp = noisy.metadata["noise_projection"]
    # tick 0 matched (cycle 0), ticks 1 & 2 skipped -> matched 1, skipped 2 (kills `skipped[i] += 1`->`= 1`)
    assert mp["matched_counts"] == [1] and mp["skipped_outside_timeline"] == [2]
    audit = noisy.metadata[_AUDIT_KEY]
    # kills `audit['skipped_outside_timeline'] = skipped` -> `= None` and the key wrap/case mutations
    assert "skipped_outside_timeline" in audit and audit["skipped_outside_timeline"] == [2]


def test_L0_apply_source_idle_skip_out_of_timeline():
    # an idle candidate at tick 0 (matched) AND tick 1 (skipped, out of a 1-cycle timeline)
    b = CircuitBuilder(num_qubits=2)
    b.x(0)
    b.tick()
    b.tick()
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0",))
    b.detector("d1", xor=("m1",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.05])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="during", match_kind="idle", noise="X_ERROR", payload_key="p",
                            map_kind="payload_probability", target_filter=(1,), require_match=False),))
    noisy = apply_stim_pauli_noise(circ, spec)
    mp = noisy.metadata["noise_projection"]
    # kills the idle-branch `skipped_outside_timeline` arg -> None (would TypeError on skip)
    assert mp["matched_counts"] == [1] and mp["skipped_outside_timeline"] == [1]


def test_L0_apply_source_idle_rule_matched_no_timeline_raises_with_idle_label():
    # a source idle rule that never matches (no tick) -> require_match missing raise, 'idle' label
    circ = _one_gate_circuit("H", (0,), 1)      # no TICK -> the idle rule never fires
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.2])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="during", match_kind="idle", noise="X_ERROR", payload_key="p",
                            map_kind="payload_probability"),))
    _raises_exact(
        ValueError,
        "source projection rule(s) were not fully covered by the source timeline: "
        "['source_rule[0] idle:idle']",
        lambda: apply_stim_pauli_noise(circ, spec))


def test_L0_apply_targeted_idle_rule_matched_nothing_raises_with_idle_label():
    # a targeted idle rule that never matches (no tick) -> require_match raise, 'idle' label
    circ = _one_gate_circuit("H", (0,), 1)
    spec = NoiseBuilder().during_idle("X_ERROR", 0.02).build()
    _raises_exact(ValueError,
                  "targeted noise rule(s) matched no circuit operation: ['rule[0] idle:idle']",
                  lambda: apply_stim_pauli_noise(circ, spec))


def test_L0_apply_source_measurement_rule_mismatch_no_insert():
    # an MX source rule on a Z 'M' measurement must NOT insert -> kills the source
    # `position == 'before' and _source_rule_matches_measurement(...)` -> `or`
    b = CircuitBuilder(num_qubits=1)
    b.measure(0, key="m0")
    b.detector("d0", xor=("m0",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.2])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="before", match_kind="measurement_type", measure_name="MX",
                            noise="X_ERROR", payload_key="p", map_kind="payload_probability",
                            require_match=False),))
    noisy = apply_stim_pauli_noise(circ, spec)
    assert noisy.metadata["noise_projection"]["matched_counts"] == [0]
    assert all(not (isinstance(s, GateOp) and s.name == "X_ERROR") for s in noisy.steps)


def test_L0_apply_source_gate_skip_out_of_timeline():
    # a gate after two ticks (tick_index 2) with a 1-cycle timeline is skipped via the GATE branch
    # -> kills the gate-branch `skipped_outside_timeline` arg -> None (which would TypeError on skip)
    b = CircuitBuilder(num_qubits=1)
    b.tick()
    b.tick()
    b.x(0)
    b.measure(0, key="m0")
    b.detector("d0", xor=("m0",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.2])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="after", match_kind="gate_type", gate_name="X", noise="X_ERROR",
                            payload_key="p", map_kind="payload_probability", require_match=False),))
    noisy = apply_stim_pauli_noise(circ, spec)
    mp = noisy.metadata["noise_projection"]
    assert mp["matched_counts"] == [0] and mp["skipped_outside_timeline"] == [1]


def test_L0_apply_source_idle_break_guard():
    # two source idle rules: the FIRST has an empty idle set (target 0 touched); the SECOND (target 2)
    # must still fire -> kills the source-idle `continue` -> `break` mutant
    b = CircuitBuilder(num_qubits=3)
    b.x(0)
    b.x(1)
    b.tick()
    b.measure((0, 1, 2), key=("a", "b", "c"))
    b.detector("d", xor=("a",))
    circ = b.build()
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.05])})
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(
        SourceStimPauliRule(position="during", match_kind="idle", noise="X_ERROR", payload_key="p",
                            map_kind="payload_probability", target_filter=(0,), require_match=False),
        SourceStimPauliRule(position="during", match_kind="idle", noise="Y_ERROR", payload_key="p",
                            map_kind="payload_probability", target_filter=(2,))))
    noisy = apply_stim_pauli_noise(circ, spec)
    assert noisy.metadata["noise_projection"]["matched_counts"] == [0, 1]
    assert ("G", "Y_ERROR", (2,), (0.05,)) in _steps(noisy)


def test_L0_apply_targeted_idle_matched_across_two_ticks():
    # a targeted idle rule fires at BOTH ticks (q1 idle each time) -> matched count 2
    # -> kills the idle `matched[i] += 1` -> `= 1` mutant
    b = CircuitBuilder(num_qubits=2)
    b.x(0)
    b.tick()
    b.x(0)
    b.tick()
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d", xor=("m0",))
    circ = b.build()
    noisy = apply_stim_pauli_noise(circ, NoiseBuilder().during_idle("X_ERROR", 0.01, targets=(1,)).build())
    assert noisy.metadata["noise_projection"]["matched_counts"] == [2]


def test_private_rule_matches_gate_non_gate_kind_returns_false():
    # a measurement_type rule fed to the gate matcher -> the final `return False` (kills -> `return True`)
    mrule = _mrule("M")
    assert nspec._rule_matches_gate(mrule, GateOp("H", (0,), ()), 0) is False
    # an all_gates rule matches any gate; a gate_index rule matches only its index
    grule = StimNoiseRule(position="after", match_kind="all_gates", noise="X_ERROR", args=(0.01,))
    assert nspec._rule_matches_gate(grule, GateOp("H", (0,), ()), 3) is True
    girule = StimNoiseRule(position="after", match_kind="gate_index", noise="X_ERROR", args=(0.01,),
                           gate_index=2)
    assert nspec._rule_matches_gate(girule, GateOp("H", (0,), ()), 2) is True
    assert nspec._rule_matches_gate(girule, GateOp("H", (0,), ()), 3) is False


def test_private_gate_arity_reset_variants():
    # RY / RZ resets also have arity 1 (kills the reset-set element wrap/case mutations)
    assert nspec._gate_arity(GateOp("RY", (0,), ())) == 1
    assert nspec._gate_arity(GateOp("RZ", (0,), ())) == 1


def test_private_validate_noise_targets_single_qubit_set_members():
    # Y_ERROR / Z_ERROR are in the single-target fast-path set (kills the Y_ERROR element wrap/case)
    assert nspec._validate_noise_targets("Y_ERROR", (0,)) is None
    assert nspec._validate_noise_targets("Z_ERROR", (0,)) is None


def test_private_source_noise_target_groups_empty_targets_branch():
    # 2-D payload + empty targets -> the 'empty_target_error' guard (kills its string wrap/case)
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0,
                        payload={"p": np.asarray([[0.2, 0.3]])})
    rule = _source_rule(map_kind="payload_probability", payload_key="p")
    assert nspec._source_noise_target_groups(tl, rule, name="X_ERROR", targets=()) == (
        ((), "empty_target_error"),)


def test_private_payload_value_for_targets_boundary_site_raises():
    # a target EXACTLY equal to the site count trips the `>=` bound (kills `>= arr.shape[1]` -> `>`)
    p2 = np.asarray([[0.1, 0.2, 0.3]])
    _raises_exact(ValueError, "source payload has 3 sites but matched targets were (3,)",
                  lambda: nspec._payload_value_for_targets(p2, cycle_index=0, targets=(3,)))


def test_private_append_source_noise_matched_step_none_raises():
    # the defensive matched_step-None guard on a NON-idle rule (# pragma: no cover in prod)
    tl = SourceTimeline(name="t", n_cycles=1, cycle_time_ns=1000.0, payload={"p": np.asarray([0.2])})
    rule = _source_rule(map_kind="payload_probability", payload_key="p")
    spec = SourceStimPauliProjectionSpec(timeline=tl, rules=(rule,))
    _raises_exact(ValueError, "matched_step is required for non-idle source projection",
                  lambda: nspec._append_source_noise_if_in_timeline(
                      [], spec, rule, 0, (0,), [0], [0], [[]],
                      matched_step=None, gate_index=None, tick_index=0))

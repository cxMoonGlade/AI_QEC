"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.analog_schedule`` (17 CPU-pure public units: the
five frozen Axis-1 schedule dataclasses' ``__post_init__`` + ``to_manifest``,
``DurationPolicy.bracket_for``, the ``default_duration_policy`` table, the three
compilers ``compile_code_spec_to_substep_schedule`` / ``circuit_ir_to_substep_schedule``
/ ``stim_circuit_to_substep_schedule``, and the process-lifetime seal pair
``has_valid_compiler_schedule_seal`` / ``require_compiler_schedule_seal``; no torch, no
quimb, so out_of_scope is empty).

Current coverage contract: docs/SIMULATOR.md SS12.3/12.4.
``frontend/analog_schedule.py`` is the compiler/schedule seam: it records which public
circuit operations occupy the same substep, the duration bracket attached to that
substep, the record-boundary provenance, and a process-owned HMAC seal that later Axis-1
bridge code requires. It deliberately holds no Hamiltonians / channels / Kraus / source
truth.

L2 DISCIPLINE (100% coverage != discrimination). THE LOAD-BEARING PART is that a compiled
``SubstepSchedule`` is pinned against an INDEPENDENT recompute of the schedule structure
(the ordered substep kinds, per-substep operations, active/idle qubits, duration bracket,
mechanism slots, participants, window support, record layout) -- NOT read back from the
module -- and every dataclass ``to_manifest`` is pinned to its EXACT dict. The
``default_duration_policy`` is pinned to its exact six-bracket table reconstructed by hand.
Every coercion is made observable by feeding NON-canonical typed inputs and pinning the
coerced value+type (kills the ``object.__setattr__(self, "<field>", ...)`` attribute-name
string mutants). Every validation raise is tripped through EVERY route reaching it with
the EXACT message via ``str(excinfo.value)==...``.

The seal is a process-lifetime HMAC over the schedule manifest; ``require_...`` is tripped
through the genuine UNSEALED route (a schedule built by hand, not via a compiler) AND a
TAMPERED route (a wrong non-empty signature drives the ``hmac.compare_digest`` arc). The
``or``->default fallbacks (``source_hash or _stable_hash``, ``duration_policy or
default_duration_policy()``) are each exercised both ways with the explicit value pinned as
used. The ``_find_axis2_source_metadata_path`` arm of ``_reject_projected_or_noisy_circuit``
is DEAD-DEFENSIVE (probed): ``CircuitIR.__post_init__``'s ``validate_public_metadata``
rejects every axis-2 source key at the data boundary. The isolation-contract fix makes the
``_source_projection_evaluator_audit`` transport FAIL-CLOSED -- the audit key is rejected at
EVERY position on public-artifact objects (both the TOP-LEVEL guard-bypass and a key hidden
under a NESTED audit subtree), skipped only under the internal ``_allow_noise_steps`` opt-in
(see ``test_L0_validate_public_metadata_audit_transport_fail_closed`` and
``test_L0_circuit_ir_toplevel_audit_transport_gated_by_allow_noise_steps``) -- so no route
reaches the extractor with a constructed circuit. The compiler backstops
(top-level audit + ``_find_axis2`` recursion) are pinned by a DIRECT probe on unvalidated
stub metadata (``test_L0_find_axis2_source_metadata_path_direct``).
"""
from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins

from error_coupling_simulator.frontend.analog_schedule import (
    DEFAULT_DURATION_POLICY_ID,
    ANALOG_SCHEDULE_REPRESENTABILITY,
    SCHEDULE_SCHEMA_VERSION,
    COMPILER_SCHEDULE_SEAL_SCHEMA,
    AnalogSubstepIR,
    DurationBracket,
    DurationPolicy,
    SubstepOperation,
    SubstepSchedule,
    circuit_ir_to_substep_schedule,
    compile_code_spec_to_substep_schedule,
    default_duration_policy,
    has_valid_compiler_schedule_seal,
    require_compiler_schedule_seal,
    stim_circuit_to_substep_schedule,
    _operation_from_step,
    _step_manifest,
    _stim_circuit_to_circuit_ir,
    _find_axis2_source_metadata_path,
    _reject_projected_or_noisy_circuit,
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
from error_coupling_simulator.frontend.metadata_guard import (
    AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY,
    AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY,
    validate_public_metadata,
)
from error_coupling_simulator.frontend.code_spec import (
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
)
from error_coupling_simulator.frontend.axis1_context import (
    Axis1LocalLindbladContextSpec,
)


# --------------------------------------------------------------------------- #
# helpers                                                                       #
# --------------------------------------------------------------------------- #
def _raises_exact(exc, msg, fn):
    """pytest.raises pinning the EXACT ``str(exc)`` (kills mutmut string-literal wrap/case
    mutants a substring ``match=`` would let survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _ir_substep(**over):
    """A minimal VALID AnalogSubstepIR for SubstepSchedule fixtures; override any field."""
    base = dict(
        substep_id="s0000", round_index=None, tick_index=0, order_index=0, kind="idle",
        operations=(), active_qubits=(), idle_qubits=(0, 1), participants=((0,), (1,)),
        dt_ns_nominal=None, dt_ns_bracket=(0.0, 300.0),
        dt_source="error_coupling_simulator.frontend.duration_policy.v1",
        mechanism_slots=("idle",), measurement_keys=(), window_support=(0, 1),
    )
    base.update(over)
    return AnalogSubstepIR(**base)


def _direct_schedule(**over):
    """A hand-built (UNSEALED) SubstepSchedule -- never routed through a compiler."""
    base = dict(
        source_kind="circuit_ir", source_hash="h", schedule_template=None,
        num_qubits=3, substeps=(_ir_substep(),), duration_policy=default_duration_policy(),
    )
    base.update(over)
    return SubstepSchedule(**base)


def _rich_circuit() -> CircuitIR:
    """A curated 3-qubit circuit exercising ALL six substep kinds in order:
    one_qubit_gate (H0) -> two_qubit_gate (CX 1,2) -> barrier (TICK) -> reset (R2) ->
    idle (I 0,1 @50ns) -> measurement (MR0)."""
    b = CircuitBuilder(num_qubits=3)
    b.h(0)
    b.cx((1, 2))
    b.tick()
    b.reset(2)
    b.idle((0, 1), duration_ns=50.0)
    b.measure((0,), key="m0", reset=True)
    return b.build()


def _mixed_spec(rounds: int = 2) -> CodeSpec:
    """A d=3-ish mixed X/Z memory spec so the compiler emits H (one_qubit_gate) + CX
    (two_qubit_gate) + reset + measurement + barrier substeps."""
    return CodeSpec(
        name="axis1_mixed",
        num_qubits=5,
        data_qubits=(CodeQubit(0, "data", (0.0,)), CodeQubit(1, "data", (1.0,)),
                     CodeQubit(2, "data", (2.0,))),
        ancilla_qubits=(CodeQubit(3, "ancilla", (0.0, 0.5)),
                        CodeQubit(4, "ancilla", (1.0, 0.5))),
        checks=(
            StabilizerCheck("x0", 3, (PauliTerm(0, "X"),), (0.0, 0.5)),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"),), (1.0, 0.5)),
        ),
        logical_observables=(
            LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),), index=0),
        ),
        rounds=rounds,
    )


# --------------------------------------------------------------------------- #
# INDEPENDENT source-hash recompute (from-scratch reimplementation of the      #
# documented manifest+hash contract -- NOT a call into the module's private    #
# helpers). A mutant in _circuit_ir_manifest/_step_manifest/_stable_hash/       #
# _jsonable/the stim payload changes the module's opaque source_hash while this #
# independent digest stays correct -> mismatch -> killed.                       #
# --------------------------------------------------------------------------- #
def _indep_jsonable(value):
    if isinstance(value, dict):
        return {str(k): _indep_jsonable(v)
                for k, v in sorted(value.items(), key=lambda it: str(it[0]))}
    if isinstance(value, (list, tuple)):
        return [_indep_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _indep_hash(value) -> str:
    payload = json.dumps(_indep_jsonable(value), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _indep_step_manifest(step) -> dict:
    if isinstance(step, GateOp):
        return {"kind": "gate", "name": step.name, "targets": list(step.targets),
                "args": list(step.args)}
    if isinstance(step, Tick):
        return {"kind": "tick"}
    if isinstance(step, MeasureOp):
        return {"kind": "measurement", "name": step.name, "targets": list(step.targets),
                "keys": list(step.keys), "args": list(step.args)}
    if isinstance(step, DetectorDef):
        return {"kind": "detector", "name": step.name, "keys": list(step.keys),
                "coords": list(step.coords)}
    if isinstance(step, ObservableDef):
        return {"kind": "observable", "name": step.name, "keys": list(step.keys),
                "index": step.index}
    raise TypeError(step)


def _indep_circuit_ir_source_hash(circuit: CircuitIR) -> str:
    return _indep_hash({
        "schema": "error_coupling_simulator.frontend.circuit_ir_schedule_hash.v1",
        "num_qubits": circuit.num_qubits,
        "metadata": _indep_jsonable(circuit.metadata),
        "steps": [_indep_step_manifest(s) for s in circuit.steps],
    })


def _indep_stim_source_hash(circuit_str, *, edges=(), calibrations=None,
                            context_manifest=None) -> str:
    payload = {
        "schema": "error_coupling_simulator.frontend.stim_circuit_schedule_hash.v1",
        "stim_circuit": circuit_str,
        "static_zz_couplings": [list(e) for e in edges],
        "static_zz_calibrations": calibrations or [],
    }
    if context_manifest is not None:
        payload["axis1_local_lindblad_context"] = context_manifest
    return _indep_hash(payload)


# =========================================================================== #
# DurationBracket.__post_init__ + to_manifest                                  #
# =========================================================================== #
def test_L0_duration_bracket_valid_and_coercion():
    # non-canonical typed inputs -> pin the coerced value+TYPE (kills setattr string mutants).
    b = DurationBracket(kind=123, low_ns=20, high_ns=30, nominal_ns=25, source=456,
                        epistemic_class="a")
    assert b.kind == "123" and type(b.kind) is str
    assert b.low_ns == 20.0 and type(b.low_ns) is float
    assert b.high_ns == 30.0 and type(b.high_ns) is float
    assert b.nominal_ns == 25.0 and type(b.nominal_ns) is float
    assert b.source == "456" and type(b.source) is str
    assert b.epistemic_class == "a"
    # nominal None arc (the `None if ... is None` branch)
    assert DurationBracket("idle", 0.0, 300.0, None).nominal_ns is None
    # defaults live: source -> policy id, epistemic -> 'c' (kills the "c" default mutant,
    # since a mutated default would fail the {'a','b','c'} membership guard).
    d = DurationBracket("k", 1.0, 2.0, None)
    assert d.source == DEFAULT_DURATION_POLICY_ID and d.epistemic_class == "c"
    # low==0.0 valid (kills `< 0.0` -> `<= 0.0`); high==low valid (kills `high < low` -> `<=`)
    assert DurationBracket("barrier", 0.0, 0.0, None).high_ns == 0.0
    # nominal exactly at a bracket endpoint is valid (kills `<=` boundary mutants)
    assert DurationBracket("k", 20.0, 30.0, 20.0).nominal_ns == 20.0
    assert DurationBracket("k", 20.0, 30.0, 30.0).nominal_ns == 30.0


def test_L0_duration_bracket_guards():
    # low<0 with high>=low: the `or` FIRST operand fires alone (kills or->and).
    _raises_exact(ValueError, "invalid duration bracket for 'k': [-1.0, 5.0]",
                  lambda: DurationBracket("k", -1.0, 5.0, None))
    # high<low: the `or` SECOND operand fires alone.
    _raises_exact(ValueError, "invalid duration bracket for 'k': [5.0, 3.0]",
                  lambda: DurationBracket("k", 5.0, 3.0, None))
    # nominal outside the bracket
    _raises_exact(ValueError, "duration nominal 35.0 outside bracket [20.0, 30.0] for 'k'",
                  lambda: DurationBracket("k", 20.0, 30.0, 35.0))
    _raises_exact(ValueError, "duration nominal 15.0 outside bracket [20.0, 30.0] for 'k'",
                  lambda: DurationBracket("k", 20.0, 30.0, 15.0))
    # bad epistemic_class
    _raises_exact(ValueError, "invalid epistemic_class 'd'",
                  lambda: DurationBracket("k", 0.0, 1.0, None, epistemic_class="d"))


def test_L0_duration_bracket_to_manifest_exact_dict():
    b = DurationBracket("one_qubit_gate", 20.0, 30.0, 25.0)
    expected = {"kind": "one_qubit_gate", "low_ns": 20.0, "high_ns": 30.0,
                "nominal_ns": 25.0,
                "source": "error_coupling_simulator.frontend.duration_policy.v1",
                "epistemic_class": "c"}
    got = b.to_manifest()
    assert got == expected
    # None-nominal shows through as None (not dropped)
    assert DurationBracket("idle", 0.0, 300.0, None).to_manifest()["nominal_ns"] is None

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, dict(expected, nominal_ns=26.0),
                         label="DurationBracket.to_manifest")


# =========================================================================== #
# DurationPolicy.__post_init__ / bracket_for / to_manifest                     #
# =========================================================================== #
def test_L0_duration_policy_valid_and_coercion():
    p = DurationPolicy(table_id=9, brackets=[DurationBracket("a", 0.0, 1.0, None)])
    assert p.table_id == "9" and type(p.table_id) is str
    assert isinstance(p.brackets, tuple) and len(p.brackets) == 1


def test_L0_duration_policy_guards():
    _raises_exact(ValueError, "DurationPolicy requires at least one bracket",
                  lambda: DurationPolicy("t", ()))
    _raises_exact(ValueError, "duplicate duration bracket kind(s): ['idle', 'idle']",
                  lambda: DurationPolicy("t", (DurationBracket("idle", 0.0, 1.0, None),
                                               DurationBracket("idle", 0.0, 2.0, None))))


def test_L0_duration_policy_bracket_for():
    pol = default_duration_policy()
    # a MID-table kind so the loop runs past non-matching brackets (the no-match arc).
    reset = pol.bracket_for("reset")
    assert reset.to_manifest() == {"kind": "reset", "low_ns": 100.0, "high_ns": 500.0,
                                   "nominal_ns": None,
                                   "source": "error_coupling_simulator.frontend.duration_policy.v1",
                                   "epistemic_class": "c"}
    one = pol.bracket_for("one_qubit_gate")
    assert one.nominal_ns == 25.0

    def prop(b):
        assert b.kind == "reset"

    assert_discriminates(prop, reset, one, label="bracket_for(reset)")
    _raises_exact(
        ValueError,
        "duration policy 'error_coupling_simulator.frontend.duration_policy.v1' "
        "has no bracket for 'nope'",
                  lambda: pol.bracket_for("nope"))


def test_L0_duration_policy_to_manifest_exact_dict():
    p = DurationPolicy("mini", (DurationBracket("idle", 0.0, 5.0, None),
                                DurationBracket("reset", 1.0, 2.0, 1.5)))
    expected = {
        "table_id": "mini",
        "brackets": [
            {"kind": "idle", "low_ns": 0.0, "high_ns": 5.0, "nominal_ns": None,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
            {"kind": "reset", "low_ns": 1.0, "high_ns": 2.0, "nominal_ns": 1.5,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
        ],
    }
    got = p.to_manifest()
    assert got == expected

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, {**expected, "table_id": "other"},
                         label="DurationPolicy.to_manifest")


# =========================================================================== #
# SubstepOperation.__post_init__ + to_manifest                                 #
# =========================================================================== #
def test_L0_substep_operation_valid_and_coercion():
    op = SubstepOperation(name="mr", targets=(0.0, 1.0), source_step_index=3.0,
                          args=(1, 2), basis="z", measurement_keys=("m0",),
                          reset_after_measurement=1)
    assert op.name == "MR"                                   # .upper()
    assert op.targets == (0, 1) and all(type(t) is int for t in op.targets)
    assert op.source_step_index == 3 and type(op.source_step_index) is int
    assert op.args == (1.0, 2.0) and all(type(a) is float for a in op.args)
    assert op.basis == "Z"                                   # .upper()
    assert op.measurement_keys == ("m0",)
    assert op.reset_after_measurement is True                # bool(1)
    # basis None arc
    assert SubstepOperation("h", (0,), 0).basis is None


def test_L0_substep_operation_negative_target_raise():
    # MIXED (0, -1): any(t<0) True but all(t<0) False -> kills any->all.
    _raises_exact(ValueError, "operation 'X' has negative target(s): (0, -1)",
                  lambda: SubstepOperation("x", (0, -1), 0))


def test_L0_substep_operation_to_manifest_exact_dict():
    full = SubstepOperation("mr", (0,), 5, args=(), basis="z",
                            measurement_keys=("m0",), reset_after_measurement=True)
    expected_full = {"name": "MR", "targets": [0], "source_step_index": 5, "args": [],
                     "basis": "Z", "measurement_keys": ["m0"],
                     "reset_after_measurement": True}
    got = full.to_manifest()
    assert got == expected_full
    # minimal op: basis/measurement_keys/reset keys are ABSENT (the falsy arcs).
    minimal = SubstepOperation("h", (0,), 0)
    assert minimal.to_manifest() == {"name": "H", "targets": [0],
                                     "source_step_index": 0, "args": []}

    def prop(m):
        assert m == expected_full

    assert_discriminates(prop, got, dict(expected_full, basis="X"),
                         label="SubstepOperation.to_manifest")


# =========================================================================== #
# AnalogSubstepIR.__post_init__ + to_manifest                                  #
# =========================================================================== #
def test_L0_analog_substep_valid_and_coercion():
    ir = AnalogSubstepIR(
        substep_id=7, round_index=2.0, tick_index=1.0, order_index=0.0, kind=5,
        operations=(), active_qubits=(1, 0, 0), idle_qubits=(2,), participants=((0.0,),),
        dt_ns_nominal=5, dt_ns_bracket=(0, 10), dt_source=9, mechanism_slots=(1,),
        measurement_keys=(1,), window_support=(2, 1), generated_by_compiler=0,
        epistemic_class="b")
    assert ir.substep_id == "7" and type(ir.substep_id) is str
    assert ir.round_index == 2 and type(ir.round_index) is int
    assert ir.tick_index == 1 and type(ir.tick_index) is int
    assert ir.order_index == 0 and type(ir.order_index) is int
    assert ir.kind == "5" and type(ir.kind) is str
    assert ir.active_qubits == (0, 1)                        # _sorted_unique
    assert ir.idle_qubits == (2,)
    assert ir.participants == ((0,),)
    assert ir.dt_ns_nominal == 5.0 and type(ir.dt_ns_nominal) is float
    assert ir.dt_ns_bracket == (0.0, 10.0) and all(type(x) is float for x in ir.dt_ns_bracket)
    assert ir.dt_source == "9"
    assert ir.mechanism_slots == ("1",)
    assert ir.measurement_keys == ("1",)
    assert ir.window_support == (1, 2)
    assert ir.generated_by_compiler is False                # bool(0)
    assert ir.epistemic_class == "b"
    # round_index None arc + nominal None arc
    z = _ir_substep(round_index=None, dt_ns_nominal=None)
    assert z.round_index is None and z.dt_ns_nominal is None


def test_L0_analog_substep_guards():
    # tick<0 (first `or` operand) / order<0 (second operand)
    _raises_exact(ValueError, "tick_index/order_index must be non-negative",
                  lambda: _ir_substep(tick_index=-1, order_index=0))
    _raises_exact(ValueError, "tick_index/order_index must be non-negative",
                  lambda: _ir_substep(tick_index=0, order_index=-1))
    # nominal <= 0 when present
    _raises_exact(ValueError, "dt_ns_nominal must be positive when present",
                  lambda: _ir_substep(dt_ns_nominal=0.0))
    _raises_exact(ValueError, "dt_ns_nominal must be positive when present",
                  lambda: _ir_substep(dt_ns_nominal=-2.0))
    # dt_bracket[0]<0 (first `or` operand) / [1]<[0] (second operand)
    _raises_exact(ValueError, "invalid dt_ns_bracket (-1.0, 5.0)",
                  lambda: _ir_substep(dt_ns_bracket=(-1.0, 5.0)))
    _raises_exact(ValueError, "invalid dt_ns_bracket (5.0, 3.0)",
                  lambda: _ir_substep(dt_ns_bracket=(5.0, 3.0)))
    # bad epistemic_class
    _raises_exact(ValueError, "invalid epistemic_class 'z'",
                  lambda: _ir_substep(epistemic_class="z"))


def test_L0_analog_substep_to_manifest_exact_dict():
    ir = AnalogSubstepIR(
        substep_id="s0007", round_index=2, tick_index=1, order_index=3,
        kind="one_qubit_gate", operations=(SubstepOperation("h", (0,), 5),),
        active_qubits=(0,), idle_qubits=(1,), participants=((0,),),
        dt_ns_nominal=25.0, dt_ns_bracket=(20.0, 30.0),
        dt_source="error_coupling_simulator.frontend.duration_policy.v1",
        mechanism_slots=("drive", "idle", "spectator"), measurement_keys=(),
        window_support=(0, 1), generated_by_compiler=True, epistemic_class="b")
    expected = {
        "substep_id": "s0007", "round_index": 2, "tick_index": 1, "order_index": 3,
        "kind": "one_qubit_gate",
        "operations": [{"name": "H", "targets": [0], "source_step_index": 5, "args": []}],
        "active_qubits": [0], "idle_qubits": [1], "participants": [[0]],
        "dt_ns_nominal": 25.0, "dt_ns_bracket": [20.0, 30.0],
        "dt_source": "error_coupling_simulator.frontend.duration_policy.v1",
        "mechanism_slots": ["drive", "idle", "spectator"], "measurement_keys": [],
        "window_support": [0, 1], "generated_by_compiler": True, "epistemic_class": "b",
    }
    got = ir.to_manifest()
    assert got == expected

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, dict(expected, order_index=4),
                         label="AnalogSubstepIR.to_manifest")


# =========================================================================== #
# SubstepSchedule.__post_init__ + to_manifest                                  #
# =========================================================================== #
def test_L0_substep_schedule_direct_and_coercion():
    ctx = {"include_thermal_excitation": True, "gamma_up_per_ns": 2.0e-4}
    s = SubstepSchedule(
        source_kind="circuit_ir", source_hash="abc", schedule_template="tmpl",
        num_qubits=3, substeps=(_ir_substep(),), duration_policy=default_duration_policy(),
        qubit_roles={0: "data", 1: "ancilla"}, qubit_coords={0: (0.0, 1.0)},
        static_zz_couplings=((1, 0),),
        static_zz_calibrations={(0, 1): {"zeta_rad_per_ns": 0.25}},
        axis1_local_lindblad_context=ctx,
    )
    assert s.source_kind == "circuit_ir" and s.source_hash == "abc"
    assert s.schedule_template == "tmpl"                     # str arc
    assert s.num_qubits == 3 and type(s.num_qubits) is int
    assert s.schema_version == SCHEDULE_SCHEMA_VERSION
    assert s.qubit_roles == {0: "data", 1: "ancilla"}
    assert s.qubit_coords == {0: (0.0, 1.0)}
    # static_zz edge canonicalized (1,0) -> (0,1); calibration carries default epistemic 'c'.
    assert s.static_zz_couplings == ((0, 1),)
    assert s.static_zz_calibrations == {(0, 1): {"zeta_rad_per_ns": 0.25, "epistemic_class": "c"}}
    # NON-trivial context -> the `else context.to_manifest()` arc (dict is non-empty).
    assert s.axis1_local_lindblad_context["include_thermal_excitation"] is True
    # UNSEALED (built by hand, not via a compiler).
    assert has_valid_compiler_schedule_seal(s) is False
    # template None arc + trivial-context arc
    t = _direct_schedule(schedule_template=None)
    assert t.schedule_template is None and t.axis1_local_lindblad_context == {}


def test_L0_substep_schedule_guards():
    retired_schema = "_".join(("qec", "twin")) + ".simulator.SubstepSchedule.v1"
    with pytest.raises(ValueError, match="unsupported substep-schedule schema"):
        _direct_schedule(substeps=(), schema_version=retired_schema)
    _raises_exact(ValueError, "num_qubits must be positive",
                  lambda: _direct_schedule(num_qubits=0, substeps=()))
    _raises_exact(ValueError, "source_hash must be non-empty",
                  lambda: _direct_schedule(source_hash="", substeps=()))
    _raises_exact(
        ValueError, "SubstepSchedule representability must be 'analog_schedule_metadata_only'",
        lambda: _direct_schedule(substeps=(), representability="bad"))
    # per-substep order_index must equal its position (a substep with order_index=3 at pos 0)
    _raises_exact(
        ValueError, "substep 'sX' has order_index 3, expected 0",
        lambda: _direct_schedule(substeps=(_ir_substep(substep_id="sX", order_index=3),)))
    # window qubit outside [0, num_qubits): q=5 with num_qubits=2 (q>=nq operand of the `or`)
    _raises_exact(
        ValueError, "substep 'sW' window qubit 5 outside [0, 2)",
        lambda: _direct_schedule(
            num_qubits=2, substeps=(_ir_substep(substep_id="sW", window_support=(5,)),)))


def test_L0_substep_schedule_to_manifest_sealed_vs_unsealed():
    # SEALED via the compiler: seal_present True, generated_substeps True, no context key.
    sealed = circuit_ir_to_substep_schedule(_rich_circuit())
    m = sealed.to_manifest()
    assert m["schema_version"] == SCHEDULE_SCHEMA_VERSION
    assert m["source_kind"] == "circuit_ir"
    assert m["representability"] == ANALOG_SCHEDULE_REPRESENTABILITY
    assert m["visibility"] == "public_schedule_metadata_no_mechanism_truth"
    assert m["compiler_provenance"] == {
        "seal_schema": COMPILER_SCHEDULE_SEAL_SCHEMA,
        "seal_present": True, "seal_public": False, "generated_substeps": True}
    assert "seal_digest" not in m["compiler_provenance"]
    assert "axis1_local_lindblad_context" not in m                 # trivial -> key absent
    assert len(m["substeps"]) == len(sealed.substeps)

    # UNSEALED, NON-trivial context: seal_present False, generated_substeps False (the
    # hand substep has generated_by_compiler=False), context key PRESENT (the truthy arc).
    ctx = {"include_thermal_excitation": True, "gamma_up_per_ns": 2.0e-4}
    unsealed = _direct_schedule(axis1_local_lindblad_context=ctx)
    mu = unsealed.to_manifest()
    assert mu["compiler_provenance"] == {
        "seal_schema": COMPILER_SCHEDULE_SEAL_SCHEMA,
        "seal_present": False, "seal_public": False, "generated_substeps": False}
    assert mu["axis1_local_lindblad_context"]["include_thermal_excitation"] is True

    def prop(mm):
        assert mm["compiler_provenance"]["seal_present"] is True

    assert_discriminates(prop, m, mu, label="compiler_provenance.seal_present")


# =========================================================================== #
# default_duration_policy -- independent table reconstruction                   #
# =========================================================================== #
def test_L0_default_duration_policy_exact_table():
    expected = {
        "table_id": "error_coupling_simulator.frontend.duration_policy.v1",
        "brackets": [
            {"kind": "one_qubit_gate", "low_ns": 20.0, "high_ns": 30.0, "nominal_ns": 25.0,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
            {"kind": "two_qubit_gate", "low_ns": 25.0, "high_ns": 45.0, "nominal_ns": 30.0,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
            {"kind": "idle", "low_ns": 0.0, "high_ns": 300.0, "nominal_ns": None,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
            {"kind": "measurement", "low_ns": 100.0, "high_ns": 1000.0, "nominal_ns": None,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
            {"kind": "reset", "low_ns": 100.0, "high_ns": 500.0, "nominal_ns": None,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
            {"kind": "barrier", "low_ns": 0.0, "high_ns": 0.0, "nominal_ns": None,
             "source": "error_coupling_simulator.frontend.duration_policy.v1",
             "epistemic_class": "c"},
        ],
    }
    got = default_duration_policy().to_manifest()
    assert got == expected

    def prop(m):
        assert m == expected

    # A single wrong bracket value must fail.
    wrong = {"table_id": "error_coupling_simulator.frontend.duration_policy.v1",
             "brackets": [dict(expected["brackets"][0], nominal_ns=99.0)]
             + expected["brackets"][1:]}
    assert_discriminates(prop, got, wrong, label="default_duration_policy")


# =========================================================================== #
# compile_code_spec_to_substep_schedule                                        #
# =========================================================================== #
def test_L0_compile_code_spec_schedule():
    sched = compile_code_spec_to_substep_schedule(_mixed_spec(rounds=2))
    assert sched.source_kind == "code_spec_compiler"
    assert sched.schedule_template == "repeated_memory_v1"
    assert len(sched.source_hash) == 64                       # sha256 hexdigest
    assert has_valid_compiler_schedule_seal(sched) is True
    require_compiler_schedule_seal(sched)                      # does not raise
    assert all(ss.generated_by_compiler for ss in sched.substeps)
    # roles come from the code_spec metadata (data vs ancilla partition)
    assert sched.qubit_roles[0] == "data" and sched.qubit_roles[3] == "ancilla"
    # X + Z checks -> the full kind set is present
    kinds = {ss.kind for ss in sched.substeps}
    assert kinds >= {"reset", "one_qubit_gate", "two_qubit_gate", "measurement", "barrier"}
    # first measured check is x0 -> record key round0:x0
    assert sched.record_layout_ref["measurement_keys"][0] == "round0:x0"

    def prop(k):
        assert k == "code_spec_compiler"

    assert_discriminates(prop, sched.source_kind, "circuit_ir", label="compile source_kind")


# =========================================================================== #
# circuit_ir_to_substep_schedule -- the workhorse extractor                     #
# =========================================================================== #
def _independent_schedule_recompute():
    """The ordered (kind, op-names, active, idle, dt_nominal, dt_bracket, dt_source,
    slots, participants, window) tuple I derive BY HAND from _rich_circuit() -- NOT read
    from the module. num_qubits=3; H0/CX12/TICK/R2/I(0,1)@50/MR0."""
    return [
        ("one_qubit_gate", ["H"], (0,), (1, 2), 25.0, (20.0, 30.0),
         "error_coupling_simulator.frontend.duration_policy.v1",
         ("drive", "idle", "spectator"), ((0,),), (0, 1, 2)),
        ("two_qubit_gate", ["CX"], (1, 2), (0,), 30.0, (25.0, 45.0),
         "error_coupling_simulator.frontend.duration_policy.v1",
         ("two_qubit_drive", "zz_spectator", "idle"), ((1, 2),), (0, 1, 2)),
        ("barrier", [], (), (), None, (0.0, 0.0),
         "error_coupling_simulator.frontend.duration_policy.v1", (), (), ()),
        ("reset", ["R"], (2,), (), None, (100.0, 500.0),
         "error_coupling_simulator.frontend.duration_policy.v1",
         ("reset_boundary",), ((2,),), (2,)),
        ("idle", ["I"], (), (0, 1), 50.0, (50.0, 50.0), "explicit_circuit_idle_duration",
         ("idle",), ((0,), (1,)), (0, 1)),
        ("measurement", ["MR"], (0,), (), None, (100.0, 1000.0),
         "error_coupling_simulator.frontend.duration_policy.v1",
         ("readout_boundary", "reset_boundary"), ((0,),), (0,)),
    ]


def test_L0_circuit_ir_schedule_structure_independent_pin():
    sched = circuit_ir_to_substep_schedule(_rich_circuit())
    assert sched.source_kind == "circuit_ir"
    assert sched.num_qubits == 3
    assert sched.schedule_template is None
    assert len(sched.source_hash) == 64
    assert has_valid_compiler_schedule_seal(sched) is True
    ref = _independent_schedule_recompute()
    assert len(sched.substeps) == len(ref)
    for i, (ss, exp) in enumerate(zip(sched.substeps, ref)):
        (kind, opnames, active, idle, nom, bracket, src, slots, part, win) = exp
        assert ss.order_index == i
        assert ss.substep_id == f"s{i:04d}"
        assert ss.kind == kind, f"substep {i} kind"
        assert [o.name for o in ss.operations] == opnames
        assert ss.active_qubits == active
        assert ss.idle_qubits == idle
        assert ss.dt_ns_nominal == nom
        assert ss.dt_ns_bracket == bracket
        assert ss.dt_source == src
        assert ss.mechanism_slots == slots
        assert ss.participants == part
        assert ss.window_support == win
    # tick_index structure: 0 before the barrier, 1 after (one TICK in the circuit)
    assert [ss.tick_index for ss in sched.substeps] == [0, 0, 0, 1, 1, 1]
    # the MR measurement op carries basis Z, its record key, and the reset-after flag
    # (pins _operation_from_step's measurement branch: basis lookup + keys + MR reset flag).
    meas_op = sched.substeps[5].operations[0]
    assert meas_op.name == "MR"
    assert meas_op.basis == "Z"
    assert meas_op.measurement_keys == ("m0",)
    assert meas_op.reset_after_measurement is True
    assert sched.substeps[5].measurement_keys == ("m0",)

    def prop(kinds):
        assert kinds == [e[0] for e in ref]

    assert_discriminates(prop, [ss.kind for ss in sched.substeps],
                         [e[0] for e in ref][::-1], label="ordered substep kinds")


def test_L0_circuit_ir_reserved_source_kind_raise():
    # public route WITHOUT the authority sentinel -> reserved-source_kind guard fires.
    _raises_exact(
        ValueError,
        "source_kind='stim_circuit' is reserved for compiler/importer wrappers; "
        "public CircuitIR extraction must use source_kind='circuit_ir'",
        lambda: circuit_ir_to_substep_schedule(CircuitBuilder(2).h(0).build(),
                                               source_kind="stim_circuit"))


def test_L0_circuit_ir_explicit_hash_and_policy_pinned_as_used():
    # `source_hash or ...` and `duration_policy or ...` -- the EXPLICIT values are used
    # (kills the or->default-fallback mutant).
    custom = DurationPolicy("custom_v9", (
        DurationBracket("one_qubit_gate", 11.0, 12.0, 11.5),
        DurationBracket("idle", 0.0, 5.0, None),
        DurationBracket("barrier", 0.0, 0.0, None),
    ))
    s = circuit_ir_to_substep_schedule(CircuitBuilder(2).h(0).build(),
                                       source_hash="deadbeefhash", duration_policy=custom)
    assert s.source_hash == "deadbeefhash"
    assert s.duration_policy.table_id == "custom_v9"
    # The custom one_qubit bracket flows into the substep, not the default 25.0.
    assert s.substeps[0].dt_ns_nominal == 11.5
    assert s.substeps[0].dt_ns_bracket == (11.0, 12.0)


def test_L0_circuit_ir_reject_projected_or_noisy():
    # dict projection -> the `.get("type")` arc; message carries the extracted type.
    _raises_exact(
        ValueError,
        "Axis-1 SubstepSchedule requires an unprojected frontend circuit; "
        "noise_projection='stim_pauli' is a Stim/Pauli/source projection, "
        "not analog joint-L schedule metadata",
        lambda: circuit_ir_to_substep_schedule(CircuitIR(
            num_qubits=2, steps=(GateOp("H", (0,)),),
            metadata={"noise_projection": {"type": "stim_pauli"}})))
    # non-dict projection -> the `else projection` arc (same message; projection IS the value).
    _raises_exact(
        ValueError,
        "Axis-1 SubstepSchedule requires an unprojected frontend circuit; "
        "noise_projection='stim_pauli' is a Stim/Pauli/source projection, "
        "not analog joint-L schedule metadata",
        lambda: circuit_ir_to_substep_schedule(CircuitIR(
            num_qubits=2, steps=(GateOp("H", (0,)),),
            metadata={"noise_projection": "stim_pauli"})))
    # source-projection evaluator audit: the DATA BOUNDARY now rejects a TOP-LEVEL audit key at
    # CONSTRUCTION (it is an internal transport, not public metadata), so this input never
    # reaches the compiler's own top-level audit backstop (analog_schedule.py:1065). That
    # backstop is pinned directly on unvalidated metadata in
    # test_L0_find_axis2_source_metadata_path_direct.
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot carry the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata._source_projection_evaluator_audit is an internal source-"
        "projection transport (permitted only on the transient noisy CircuitIR), not "
        "public-artifact metadata. Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: CircuitIR(
            num_qubits=2, steps=(GateOp("H", (0,)),),
            metadata={"_source_projection_evaluator_audit": {"x": 1}}))


def test_L0_circuit_ir_axis2_source_key_is_rejected_by_earlier_guard():
    """DEAD-DEFENSIVE PROBE (not assumed): the _find_axis2_source_metadata_path arm of
    _reject_projected_or_noisy_circuit is unreachable because CircuitIR.__post_init__'s
    validate_public_metadata already rejects an axis-2 'source_*' key at construction.
    Proven here: building the circuit raises BEFORE any schedule extraction can run."""
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator truth; reserved key "
        "CircuitIR.metadata.source_process matches 'source_process'. "
        "Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: CircuitIR(num_qubits=2, steps=(GateOp("H", (0,)),),
                          metadata={"source_process": {"x": 1}}))


def test_L0_circuit_ir_extraction_raises():
    def ir(*steps, nq=3):
        return CircuitIR(num_qubits=nq, steps=steps)

    _raises_exact(ValueError, "unsupported operation 'FOO' for Axis-1 SubstepSchedule extraction",
                  lambda: circuit_ir_to_substep_schedule(ir(GateOp("FOO", (0,)))))
    _raises_exact(ValueError, "CZ requires an even-length target pair list",
                  lambda: circuit_ir_to_substep_schedule(ir(GateOp("CZ", (0,)))))
    _raises_exact(ValueError, "CZ has invalid pair participant (0, 0)",
                  lambda: circuit_ir_to_substep_schedule(ir(GateOp("CZ", (0, 0)))))
    _raises_exact(ValueError, "CZ has overlapping pair participant(s): ((0, 1), (1, 2))",
                  lambda: circuit_ir_to_substep_schedule(ir(GateOp("CZ", (0, 1, 1, 2)))))
    _raises_exact(ValueError, "unsupported measurement instruction 'MPP'",
                  lambda: circuit_ir_to_substep_schedule(ir(MeasureOp("MPP", (0,), ("m0",)))))
    _raises_exact(ValueError, "idle operation expects at most one duration_ns argument, got (1.0, 2.0)",
                  lambda: circuit_ir_to_substep_schedule(ir(GateOp("I", (0,), (1.0, 2.0)))))
    _raises_exact(ValueError, "idle duration_ns must be positive, got -5.0",
                  lambda: circuit_ir_to_substep_schedule(ir(GateOp("I", (0,), (-5.0,)))))
    # two idle ops on disjoint qubits group together -> inconsistent durations raise.
    _raises_exact(ValueError, "grouped idle operations have inconsistent durations [50.0, 60.0]",
                  lambda: circuit_ir_to_substep_schedule(
                      ir(GateOp("I", (0,), (50.0,)), GateOp("I", (1,), (60.0,)))))


def test_L0_circuit_ir_measurement_no_reset_slot():
    # a plain M (reset=False) -> mechanism_slots is JUST readout_boundary (the else arc of
    # _mechanism_slots_for's reset-after check; the MR path is covered by _rich_circuit).
    b = CircuitBuilder(num_qubits=1).measure((0,), key="m0")
    sched = circuit_ir_to_substep_schedule(b.build())
    meas = sched.substeps[-1]
    assert meas.kind == "measurement"
    assert meas.operations[0].name == "M"
    assert meas.operations[0].reset_after_measurement is False
    assert meas.mechanism_slots == ("readout_boundary",)


def test_L0_circuit_ir_explicit_measurement_duration():
    # measurement with an explicit duration_ns arg -> _explicit_duration_ns measurement arc.
    b = CircuitBuilder(num_qubits=1).measure((0,), key="m0", duration_ns=250.0)
    sched = circuit_ir_to_substep_schedule(b.build())
    meas = sched.substeps[-1]
    assert meas.dt_ns_nominal == 250.0
    assert meas.dt_ns_bracket == (250.0, 250.0)
    assert meas.dt_source == "explicit_circuit_measurement_duration"


# =========================================================================== #
# stim_circuit_to_substep_schedule -- the read-only Stim importer               #
# =========================================================================== #
def _stim_hcm():
    import stim
    return stim.Circuit("H 0\nCZ 0 1\nM 0")


def test_L0_stim_plain_schedule():
    import stim
    circuit = stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(1, 0) 1
        H 0
        TICK
        CZ 0 1
        MR 0
        DETECTOR rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
        """
    )
    sched = stim_circuit_to_substep_schedule(circuit)
    assert sched.source_kind == "stim_circuit"
    assert sched.num_qubits == 2
    assert sched.qubit_coords == {0: (0.0, 0.0), 1: (1.0, 0.0)}
    assert sched.static_zz_couplings == ()
    assert sched.axis1_local_lindblad_context == {}
    assert sched.record_layout_ref["measurement_keys"] == ["m0"]
    assert sched.record_layout_ref["detector_names"] == ["d0"]
    assert sched.record_layout_ref["observable_names"] == ["logical0"]
    assert [ss.kind for ss in sched.substeps] == [
        "one_qubit_gate", "barrier", "two_qubit_gate", "measurement"]
    assert has_valid_compiler_schedule_seal(sched) is True

    def prop(names):
        assert names == ["m0"]

    assert_discriminates(prop, sched.record_layout_ref["measurement_keys"], ["m9"],
                         label="stim record measurement_keys")


def test_L0_stim_static_and_calibration_and_context():
    # CASE A: static edges + calibrations + non-trivial context (every truthy arc).
    sched = stim_circuit_to_substep_schedule(
        _stim_hcm(),
        static_zz_couplings=((0, 1),),
        static_zz_calibrations=[{"edge": [0, 1], "zeta_rad_per_ns": 1.2e-3,
                                 "epistemic_class": "b"}],
        axis1_local_lindblad_context=Axis1LocalLindbladContextSpec(gamma_phi_per_ns=1e-3),
    )
    assert sched.static_zz_couplings == ((0, 1),)
    assert sched.static_zz_calibrations == {(0, 1): {"zeta_rad_per_ns": 1.2e-3,
                                                     "epistemic_class": "b"}}
    assert bool(sched.axis1_local_lindblad_context) is True
    assert sched.to_manifest()["static_zz_calibrations"] == [
        {"edge": [0, 1], "zeta_rad_per_ns": 1.2e-3, "epistemic_class": "b"}]
    # changing the calibration changes the source hash (calibration is inside the hash)
    other = stim_circuit_to_substep_schedule(
        _stim_hcm(), static_zz_couplings=((0, 1),),
        static_zz_calibrations=[{"edge": [0, 1], "zeta_rad_per_ns": 2.4e-3,
                                 "epistemic_class": "b"}])
    assert other.source_hash != sched.source_hash


def test_L0_stim_static_only_no_calibration_no_context():
    # CASE B: static edges present, NO calibration, NO context (the static-block falsy arcs).
    sched = stim_circuit_to_substep_schedule(_stim_hcm(), static_zz_couplings=((0, 1),))
    assert sched.static_zz_couplings == ((0, 1),)
    assert sched.static_zz_calibrations == {}
    assert sched.axis1_local_lindblad_context == {}
    # a static sidecar changes the hash vs the plain import
    assert sched.source_hash != stim_circuit_to_substep_schedule(_stim_hcm()).source_hash


def test_L0_stim_context_only():
    # CASE C: NO static edges, non-trivial context (the `elif not is_trivial` arc).
    sched = stim_circuit_to_substep_schedule(
        _stim_hcm(),
        axis1_local_lindblad_context=Axis1LocalLindbladContextSpec(gamma_phi_per_ns=1e-3))
    assert sched.static_zz_couplings == ()
    assert bool(sched.axis1_local_lindblad_context) is True
    assert sched.source_hash != stim_circuit_to_substep_schedule(_stim_hcm()).source_hash


def test_L0_stim_explicit_source_hash_pinned():
    sched = stim_circuit_to_substep_schedule(_stim_hcm(), source_hash="myfixedhash")
    assert sched.source_hash == "myfixedhash"


def test_L0_stim_importer_raises():
    import stim
    _raises_exact(ValueError, "Stim SHIFT_COORDS is not supported by the Axis-1 schedule importer",
                  lambda: stim_circuit_to_substep_schedule(stim.Circuit("SHIFT_COORDS(0, 0, 1)")))
    _raises_exact(
        ValueError,
        "source-embedded Stim noise instruction 'X_ERROR' is not analog joint-L schedule metadata",
        lambda: stim_circuit_to_substep_schedule(stim.Circuit("X_ERROR(0.1) 0")))
    # CXSWAP has qubit targets but is not in any supported set -> the FINAL unsupported raise.
    _raises_exact(
        ValueError, "unsupported Stim instruction 'CXSWAP' for Axis-1 SubstepSchedule extraction",
        lambda: stim_circuit_to_substep_schedule(stim.Circuit("CXSWAP 0 1")))
    # a Pauli-product measurement target is not a qubit target
    _raises_exact(ValueError, "MPP target stim.target_x(0) is not a qubit target",
                  lambda: stim_circuit_to_substep_schedule(stim.Circuit("MPP X0*X1")))
    _raises_exact(ValueError, "QUBIT_COORDS must target exactly one qubit",
                  lambda: stim_circuit_to_substep_schedule(stim.Circuit("QUBIT_COORDS(0, 0) 0 1")))


# =========================================================================== #
# has_valid_compiler_schedule_seal / require_compiler_schedule_seal            #
# =========================================================================== #
def test_L0_has_valid_seal_sealed_unsealed_tampered():
    sealed = circuit_ir_to_substep_schedule(CircuitBuilder(2).h(0).build())
    assert has_valid_compiler_schedule_seal(sealed) is True
    # UNSEALED: hand-built schedule -> _compiler_signature is None -> the early-return arc.
    assert has_valid_compiler_schedule_seal(_direct_schedule()) is False
    # TAMPERED: a WRONG non-empty signature -> skips the early return, drives compare_digest
    # to False (the isinstance(str) and-non-empty branch + the hmac comparison arc).
    object.__setattr__(sealed, "_compiler_signature", "deadbeef")
    assert has_valid_compiler_schedule_seal(sealed) is False
    # EMPTY signature -> the `not signature` operand of the early return.
    object.__setattr__(sealed, "_compiler_signature", "")
    assert has_valid_compiler_schedule_seal(sealed) is False


def test_L0_require_seal_pass_and_raise():
    sealed = circuit_ir_to_substep_schedule(CircuitBuilder(2).h(0).build())
    require_compiler_schedule_seal(sealed)                    # sealed -> no raise
    _raises_exact(
        ValueError,
        "Axis-1 frontend gates require a compiler-owned schedule seal; "
        "build schedules via circuit_ir_to_substep_schedule(...) or "
        "compile_code_spec_to_substep_schedule(...)",
        lambda: require_compiler_schedule_seal(_direct_schedule()))


def test_L0_seal_survives_manifest_roundtrip_but_not_field_edit():
    """The seal is over the schedule manifest MINUS compiler_provenance; a hand clone that
    changes a load-bearing field (num_qubits) must NOT validate under the process seal."""
    sealed = circuit_ir_to_substep_schedule(CircuitBuilder(3).h(0).build())
    assert has_valid_compiler_schedule_seal(sealed) is True
    # copy the signature onto a schedule with a DIFFERENT num_qubits -> signature mismatch.
    forged = _direct_schedule(num_qubits=7, source_kind=sealed.source_kind,
                              source_hash=sealed.source_hash)
    object.__setattr__(forged, "_compiler_signature",
                       getattr(sealed, "_compiler_signature"))
    assert has_valid_compiler_schedule_seal(forged) is False


# =========================================================================== #
# L1 properties (Hypothesis)                                                    #
# =========================================================================== #
_KIND = st.sampled_from(["one_qubit_gate", "two_qubit_gate", "idle", "measurement",
                         "reset", "barrier"])
_CLASS = st.sampled_from(["a", "b", "c"])


@settings(max_examples=150, deadline=None)
@given(low=st.floats(0.0, 100.0), width=st.floats(0.0, 100.0), frac=st.floats(0.0, 1.0),
       has_nominal=st.booleans(), kind=_KIND, ec=_CLASS)
def test_L1_duration_bracket_manifest_roundtrip(low, width, frac, has_nominal, kind, ec):
    high = low + width
    nominal = (low + frac * width) if has_nominal else None
    b = DurationBracket(kind, low, high, nominal, epistemic_class=ec)
    m = b.to_manifest()
    assert m == {"kind": kind, "low_ns": low, "high_ns": high, "nominal_ns": nominal,
                 "source": DEFAULT_DURATION_POLICY_ID, "epistemic_class": ec}
    # the invariant the guard enforces holds for every accepted bracket
    assert m["low_ns"] >= 0.0 and m["high_ns"] >= m["low_ns"]
    if nominal is not None:
        assert m["low_ns"] <= nominal <= m["high_ns"]


@settings(max_examples=150, deadline=None)
@given(name=st.text(alphabet="abcdxyz", min_size=1, max_size=4),
       targets=st.lists(st.integers(0, 9), min_size=0, max_size=4),
       ssi=st.integers(0, 20), reset=st.booleans())
def test_L1_substep_operation_manifest_roundtrip(name, targets, ssi, reset):
    op = SubstepOperation(name, tuple(targets), ssi, reset_after_measurement=reset)
    m = op.to_manifest()
    assert m["name"] == name.upper()
    assert m["targets"] == [int(t) for t in targets]
    assert m["source_step_index"] == ssi
    assert ("reset_after_measurement" in m) is reset


@settings(max_examples=60, deadline=None)
@given(n_gate=st.integers(1, 4))
def test_L1_circuit_ir_schedule_invariants(n_gate):
    b = CircuitBuilder(num_qubits=4)
    for q in range(n_gate):
        b.h(q % 4)
    b.tick()
    b.measure((0,), key="m0")
    sched = circuit_ir_to_substep_schedule(b.build())
    # order_index == position; window support within [0, num_qubits); sealed.
    for i, ss in enumerate(sched.substeps):
        assert ss.order_index == i
        for q in ss.window_support:
            assert 0 <= q < sched.num_qubits
    assert has_valid_compiler_schedule_seal(sched) is True
    require_compiler_schedule_seal(sched)


# =========================================================================== #
# L2 REINFORCEMENT -- kill the private manifest/hash/extractor helpers through   #
# the public compilers (mutmut is coverage-guided; these pins give the opaque    #
# source_hash + exposed metadata + extractor edge cases TEETH).                 #
# =========================================================================== #
def _comprehensive_circuit() -> CircuitIR:
    """A circuit exercising EVERY CircuitStep kind (gate/tick/measure/detector/observable)
    AND rich metadata (static-ZZ couplings + calibration + Markovian context), so pinning
    its source_hash + record_layout + exposed metadata exercises _circuit_ir_manifest /
    _step_manifest / _stable_hash / _jsonable / _record_layout_ref / _static_zz_* /
    _axis1_local_lindblad_context_metadata all at once."""
    b = CircuitBuilder(num_qubits=3)
    b.declare_static_zz_couplings(((0, 1),), zeta_rad_per_ns_by_edge={(0, 1): 0.5})
    b.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(gamma_phi_per_ns=1e-3))
    b.h(0)
    b.cx((1, 2))
    b.tick()
    b.measure((0,), key="m0")
    b.measure((1,), key="m1")
    b.detector("d0", xor=("m0", "m1"), coords=(1.0, 2.0))
    b.observable("logical0", xor=("m0",), index=0)
    return b.build()


def test_L0_circuit_ir_source_hash_and_metadata_independent_pin():
    circuit = _comprehensive_circuit()
    sched = circuit_ir_to_substep_schedule(circuit)
    # source_hash pinned to the INDEPENDENT manifest recompute (kills _circuit_ir_manifest,
    # _step_manifest, _stable_hash, _jsonable, and the `_circuit_ir_manifest(circuit)` /
    # `_stable_hash(source_manifest)` data-flow mutants).
    assert sched.source_hash == _indep_circuit_ir_source_hash(circuit)
    # changing the circuit changes the hash (stable_hash actually depends on content)
    assert sched.source_hash != circuit_ir_to_substep_schedule(
        CircuitBuilder(2).h(0).build()).source_hash
    # FULL record_layout_ref (kills _record_layout_ref field/branch mutants).
    assert sched.record_layout_ref == {
        "measurement_keys": ["m0", "m1"],
        "detector_names": ["d0"],
        "observable_names": ["logical0"],
        "detectors": [{"name": "d0", "keys": ["m0", "m1"], "coords": [1.0, 2.0]}],
        "observables": [{"name": "logical0", "keys": ["m0"], "index": 0}],
    }
    # exposed static-ZZ + calibration + context (kills _static_zz_*/_axis1_context extractors)
    assert sched.static_zz_couplings == ((0, 1),)
    assert sched.static_zz_calibrations == {(0, 1): {"zeta_rad_per_ns": 0.5,
                                                     "epistemic_class": "c"}}
    assert sched.axis1_local_lindblad_context["gamma_phi_per_ns"] == 1e-3

    def prop(h):
        assert h == _indep_circuit_ir_source_hash(circuit)

    assert_discriminates(prop, sched.source_hash, "0" * 64, label="circuit_ir source_hash")


def test_L0_circuit_ir_jsonable_nonstandard_metadata_value():
    # a complex-number metadata VALUE forces _jsonable's `return str(value)` else-arc; its
    # str() is deterministic so the source_hash is still independently pinnable.
    circuit = CircuitIR(num_qubits=2, steps=(GateOp("H", (0,)),),
                        metadata={"note": complex(1, 2)})
    sched = circuit_ir_to_substep_schedule(circuit)
    assert sched.source_hash == _indep_circuit_ir_source_hash(circuit)


def test_L0_circuit_ir_undeclared_calibration_uses_declared_edges():
    # kills the `declared_edges=static_zz_couplings` -> `declared_edges=None` mutant: a
    # calibration for an edge NOT among the declared couplings must raise (with None the
    # cross-check is skipped and no raise fires).
    circuit = CircuitIR(
        num_qubits=3, steps=(GateOp("H", (0,)),),
        metadata={AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY: [[0, 1]],
                  AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY: [
                      {"edge": [1, 2], "zeta_rad_per_ns": 0.5, "epistemic_class": "c"}]})
    _raises_exact(
        ValueError,
        "CircuitIR.metadata.axis1_static_zz_calibrations[0] edge (1, 2) is not declared "
        "in axis1_static_zz_couplings",
        lambda: circuit_ir_to_substep_schedule(circuit))


def test_L0_compile_qubit_metadata_and_custom_policy_pinned():
    # FULL qubit roles + coords from the code_spec metadata (kills _qubit_metadata mutants).
    custom = DurationPolicy("compiler_cust", (
        DurationBracket("one_qubit_gate", 13.0, 14.0, 13.5),
        DurationBracket("two_qubit_gate", 15.0, 16.0, 15.5),
        DurationBracket("idle", 0.0, 5.0, None),
        DurationBracket("measurement", 100.0, 200.0, None),
        DurationBracket("reset", 100.0, 200.0, None),
        DurationBracket("barrier", 0.0, 0.0, None),
    ))
    sched = compile_code_spec_to_substep_schedule(_mixed_spec(rounds=2),
                                                  duration_policy=custom)
    assert sched.qubit_roles == {0: "data", 1: "data", 2: "data",
                                 3: "ancilla", 4: "ancilla"}
    assert sched.qubit_coords == {0: (0.0,), 1: (1.0,), 2: (2.0,),
                                  3: (0.0, 0.5), 4: (1.0, 0.5)}
    # the EXPLICIT duration_policy is used (kills the compile `duration_policy=None` mutant).
    assert sched.duration_policy.table_id == "compiler_cust"
    one = [ss for ss in sched.substeps if ss.kind == "one_qubit_gate"][0]
    assert one.dt_ns_nominal == 13.5


def test_L0_circuit_ir_custom_policy_epistemic_and_barrier_nominal():
    # custom brackets: one_qubit epistemic 'a', barrier nominal 2.0 + epistemic 'b'. Kills
    # _make_substep's `epistemic_class=epistemic_class` drop and _make_barrier_substep's
    # `dt_ns_nominal=bracket.nominal_ns` / `epistemic_class=bracket.epistemic_class` drops.
    custom = DurationPolicy("cust", (
        DurationBracket("one_qubit_gate", 11.0, 12.0, 11.5, epistemic_class="a"),
        DurationBracket("barrier", 0.0, 5.0, 2.0, epistemic_class="b"),
    ))
    sched = circuit_ir_to_substep_schedule(CircuitBuilder(2).h(0).tick().build(),
                                           duration_policy=custom)
    gate = sched.substeps[0]
    barrier = sched.substeps[1]
    assert gate.kind == "one_qubit_gate" and gate.epistemic_class == "a"
    assert barrier.kind == "barrier"
    assert barrier.dt_ns_nominal == 2.0                       # bracket.nominal_ns, not None
    assert barrier.epistemic_class == "b"                     # bracket.epistemic_class, not 'c'


def test_L0_circuit_ir_three_ticks_tick_index_increments():
    # THREE ticks with a gate after each: tick_index must INCREMENT (kills `tick_index += 1`
    # -> `tick_index = 1`, which would pin every post-first-tick substep at 1).
    b = CircuitBuilder(num_qubits=1).h(0).tick().x(0).tick().y(0).tick()
    sched = circuit_ir_to_substep_schedule(b.build())
    assert [ss.tick_index for ss in sched.substeps] == [0, 0, 1, 1, 2, 2]


def test_L0_circuit_ir_detector_between_measurements_continues():
    # a DetectorDef BETWEEN two measurements must FLUSH-and-CONTINUE (kills the `continue`
    # -> `break` mutant, which would drop every step after the first detector).
    b = CircuitBuilder(num_qubits=2)
    b.measure((0,), key="m0")
    b.detector("d0", xor=("m0",))
    b.measure((1,), key="m1")
    sched = circuit_ir_to_substep_schedule(b.build())
    meas = [ss for ss in sched.substeps if ss.kind == "measurement"]
    assert len(meas) == 2
    assert [ss.measurement_keys for ss in meas] == [("m0",), ("m1",)]


def test_L0_circuit_ir_idle_duration_boundaries():
    # grouped idle: a no-arg idle FOLLOWED by an idle with a duration -> the no-arg op must
    # be SKIPPED (`continue`), not `break`, so the explicit 50ns is still collected.
    grouped = CircuitIR(num_qubits=2,
                        steps=(GateOp("I", (0,)), GateOp("I", (1,), (50.0,))))
    idle = [ss for ss in circuit_ir_to_substep_schedule(grouped).substeps
            if ss.kind == "idle"][0]
    assert idle.dt_ns_nominal == 50.0
    assert idle.dt_source == "explicit_circuit_idle_duration"
    # duration == 0.0 is REJECTED (kills `<= 0.0` -> `< 0.0`).
    _raises_exact(ValueError, "idle duration_ns must be positive, got 0.0",
                  lambda: circuit_ir_to_substep_schedule(
                      CircuitIR(num_qubits=1, steps=(GateOp("I", (0,), (0.0,)),))))
    # duration 0.5 is ACCEPTED (kills `<= 0.0` -> `<= 1.0`, which would reject 0.5).
    half = circuit_ir_to_substep_schedule(
        CircuitIR(num_qubits=1, steps=(GateOp("I", (0,), (0.5,)),)))
    assert half.substeps[0].dt_ns_nominal == 0.5


def test_L0_stim_full_structure_and_hash_independent_pin():
    import stim
    circuit = stim.Circuit(
        "QUBIT_COORDS(0, 0) 0\nQUBIT_COORDS(1, 1) 1\nH 0\nCZ 0 1\nM 0 1\n"
        "DETECTOR rec[-2]\nOBSERVABLE_INCLUDE(0) rec[-1]")
    sched = stim_circuit_to_substep_schedule(circuit)
    # qubit coords + substep structure (kills _stim_circuit_to_circuit_ir mutants)
    assert sched.qubit_coords == {0: (0.0, 0.0), 1: (1.0, 1.0)}
    assert [ss.kind for ss in sched.substeps] == [
        "one_qubit_gate", "two_qubit_gate", "measurement"]
    assert [[o.name for o in ss.operations] for ss in sched.substeps] == [
        ["H"], ["CZ"], ["M"]]
    meas_op = sched.substeps[2].operations[0]
    assert meas_op.basis == "Z" and meas_op.measurement_keys == ("m0", "m1")
    # record layout: m-keys, detector referencing rec[-2]=m0, observable referencing rec[-1]=m1
    assert sched.record_layout_ref == {
        "measurement_keys": ["m0", "m1"],
        "detector_names": ["d0"],
        "observable_names": ["logical0"],
        "detectors": [{"name": "d0", "keys": ["m0"], "coords": []}],
        "observables": [{"name": "logical0", "keys": ["m1"], "index": 0}],
    }
    # source_hash pinned to the INDEPENDENT stim payload recompute (kills the payload keys /
    # schema / str(stim_circuit) mutants in stim_circuit_to_substep_schedule).
    assert sched.source_hash == _indep_stim_source_hash(str(circuit))


def test_L0_stim_source_hash_static_and_calibration_independent_pin():
    # static-only payload + static+calibration payload, each pinned to the independent
    # recompute (kills the static_zz_couplings / static_zz_calibrations payload-branch mutants).
    circuit = _stim_hcm()
    static_only = stim_circuit_to_substep_schedule(circuit, static_zz_couplings=((0, 1),))
    assert static_only.source_hash == _indep_stim_source_hash(str(circuit), edges=((0, 1),))
    calib = [{"edge": [0, 1], "zeta_rad_per_ns": 1.2e-3, "epistemic_class": "b"}]
    with_calib = stim_circuit_to_substep_schedule(
        circuit, static_zz_couplings=((0, 1),), static_zz_calibrations=calib)
    assert with_calib.source_hash == _indep_stim_source_hash(
        str(circuit), edges=((0, 1),), calibrations=calib)


def test_L0_stim_detector_record_target_out_of_range():
    # a DETECTOR referencing rec[-2] with only ONE prior measurement points before the
    # record start (index = 1 + (-2) = -1 < 0) -> the out-of-range raise (kills the
    # `index < 0 or ...` -> `and` mutant and the message-None mutant).
    import stim
    _raises_exact(
        ValueError,
        "DETECTOR record target stim.target_rec(-2) points outside previous measurements",
        lambda: stim_circuit_to_substep_schedule(stim.Circuit("M 0\nDETECTOR rec[-2]")))


def test_L0_stim_non_circuit_input_typeerror():
    # a non-stim object has no .num_qubits -> the importer's TypeError (kills the message
    # mutants on `expects a stim.Circuit`).
    _raises_exact(TypeError, "stim_circuit_to_substep_schedule expects a stim.Circuit",
                  lambda: stim_circuit_to_substep_schedule(object()))


def test_L0_stim_detector_coords_naming_observable_index_and_trailing_gate():
    # THREE detectors (with the first carrying coords) + an OBSERVABLE_INCLUDE(2) + a gate
    # AFTER the observable. Kills: the DetectorDef coords-drop, the detector_count increment
    # mutants (naming d0/d1/d2), the ObservableDef index-drop, the observable `continue`->
    # `break` (which would drop the trailing gate), and the GateOp targets-drop.
    import stim
    circuit = stim.Circuit(
        "QUBIT_COORDS(0, 0) 0\nM 0 0 0 0\n"
        "DETECTOR(5, 6) rec[-1]\nDETECTOR rec[-2]\nDETECTOR rec[-3]\n"
        "OBSERVABLE_INCLUDE(2) rec[-4]\nH 0")
    sched = stim_circuit_to_substep_schedule(circuit)
    rl = sched.record_layout_ref
    assert rl["detector_names"] == ["d0", "d1", "d2"]
    assert rl["detectors"] == [
        {"name": "d0", "keys": ["m3"], "coords": [5.0, 6.0]},
        {"name": "d1", "keys": ["m2"], "coords": []},
        {"name": "d2", "keys": ["m1"], "coords": []}]
    assert rl["observables"] == [{"name": "logical2", "keys": ["m0"], "index": 2}]
    # the trailing H produced a one_qubit_gate substep on qubit 0 (continue not break;
    # GateOp keeps its qubit target).
    assert [ss.kind for ss in sched.substeps] == ["measurement", "one_qubit_gate"]
    assert sched.substeps[1].operations[0].name == "H"
    assert sched.substeps[1].operations[0].targets == (0,)


def test_L0_stim_static_sidecar_out_of_bounds():
    # an out-of-bounds static-ZZ sidecar edge exercises the num_qubits bounds check (kills the
    # `num_qubits=circuit.num_qubits` -> `None` mutant) and pins the label (kills label mutants).
    import stim
    _raises_exact(
        ValueError,
        "stim_circuit_to_substep_schedule.static_zz_couplings[0] endpoint 5 outside [0, 1)",
        lambda: stim_circuit_to_substep_schedule(stim.Circuit("H 0\nM 0"),
                                                 static_zz_couplings=((0, 5),)))


def test_L0_stim_calibration_out_of_bounds_and_undeclared():
    import stim
    circ3 = stim.Circuit("H 0\nCZ 0 1\nCZ 1 2\nM 0")
    # out-of-bounds calibration edge -> the calibration num_qubits bounds check.
    _raises_exact(
        ValueError,
        "stim_circuit_to_substep_schedule.static_zz_calibrations[0].edge[0] endpoint 5 "
        "outside [0, 3)",
        lambda: stim_circuit_to_substep_schedule(
            circ3, static_zz_couplings=((0, 1),),
            static_zz_calibrations=[{"edge": [1, 5], "zeta_rad_per_ns": 0.5,
                                     "epistemic_class": "c"}]))
    # in-bounds but UNDECLARED calibration edge -> the declared_edges cross-check (kills the
    # `declared_edges=static_edges` -> `None` mutant).
    _raises_exact(
        ValueError,
        "stim_circuit_to_substep_schedule.static_zz_calibrations[0] edge (1, 2) is not "
        "declared in axis1_static_zz_couplings",
        lambda: stim_circuit_to_substep_schedule(
            circ3, static_zz_couplings=((0, 1),),
            static_zz_calibrations=[{"edge": [1, 2], "zeta_rad_per_ns": 0.5,
                                     "epistemic_class": "c"}]))


def test_L0_stim_context_source_hash_independent_and_differs():
    # the context payload branch: pin the context-case source_hash to the INDEPENDENT payload
    # (context manifest from the public spec.to_manifest, NOT the analog_schedule payload
    # builder) -> kills the payload-key + value-None mutants; and two DIFFERENT contexts must
    # yield DIFFERENT hashes (kills the value->None mutant that would collapse them).
    circuit = _stim_hcm()
    spec_a = Axis1LocalLindbladContextSpec(gamma_phi_per_ns=1e-3)
    spec_b = Axis1LocalLindbladContextSpec(gamma_phi_per_ns=2e-3)
    sched_a = stim_circuit_to_substep_schedule(circuit, axis1_local_lindblad_context=spec_a)
    sched_b = stim_circuit_to_substep_schedule(circuit, axis1_local_lindblad_context=spec_b)
    assert sched_a.source_hash == _indep_stim_source_hash(
        str(circuit), context_manifest=spec_a.to_manifest())
    assert sched_a.source_hash != sched_b.source_hash


def test_L0_stim_custom_duration_policy_used():
    # the explicit duration_policy flows through to the extractor (kills the final call's
    # `duration_policy=duration_policy` -> `None` mutant).
    custom = DurationPolicy("stimcust", (
        DurationBracket("one_qubit_gate", 7.0, 8.0, 7.5),
        DurationBracket("two_qubit_gate", 9.0, 10.0, 9.5),
        DurationBracket("measurement", 1.0, 2.0, None),
    ))
    sched = stim_circuit_to_substep_schedule(_stim_hcm(), duration_policy=custom)
    assert sched.duration_policy.table_id == "stimcust"
    assert sched.substeps[0].dt_ns_nominal == 7.5


def test_L0_circuit_ir_static_metadata_out_of_bounds():
    # an out-of-bounds static-ZZ coupling in CircuitIR.metadata exercises the num_qubits
    # bounds check (kills _static_zz_couplings_metadata `num_qubits=circuit.num_qubits`->None).
    _raises_exact(
        ValueError,
        "CircuitIR.metadata.axis1_static_zz_couplings[0] endpoint 5 outside [0, 3)",
        lambda: circuit_ir_to_substep_schedule(CircuitIR(
            num_qubits=3, steps=(GateOp("H", (0,)),),
            metadata={AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY: [[0, 5]]})))
    # out-of-bounds calibration edge -> the calibration num_qubits bounds check.
    _raises_exact(
        ValueError,
        "CircuitIR.metadata.axis1_static_zz_calibrations[0].edge[0] endpoint 5 "
        "outside [0, 3)",
        lambda: circuit_ir_to_substep_schedule(CircuitIR(
            num_qubits=3, steps=(GateOp("H", (0,)),),
            metadata={AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY: [[0, 1]],
                      AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY: [
                          {"edge": [1, 5], "zeta_rad_per_ns": 0.5, "epistemic_class": "c"}]})))


def test_L0_compile_record_layout_ref_hash_and_schedule_name():
    # the compile path attaches a "record_layout" metadata dict, so _record_layout_ref's
    # `if isinstance(record_layout, dict):` branch runs -> it adds record_layout_hash +
    # schedule_name. Pin BOTH (kills the record_layout=None / hash-None / schedule_name-drop
    # mutants); record_layout_hash pinned to the INDEPENDENT recompute of the layout manifest.
    from error_coupling_simulator.frontend.compiler import compile_code_spec
    spec = _mixed_spec(rounds=2)
    sched = compile_code_spec_to_substep_schedule(spec)
    rl = sched.record_layout_ref
    assert rl["schedule_name"] == "repeated_memory_v1"
    layout_metadata = compile_code_spec(spec).metadata["record_layout"]
    assert rl["record_layout_hash"] == _indep_hash(layout_metadata)


def test_L0_compile_coordless_qubits_metadata():
    # a spec with NO qubit coords: the qubit_coords metadata block does not overwrite, so the
    # code_spec block's `coords[q] = tuple(...)` value (an empty tuple) is the FINAL value --
    # kills the `coords[q] = None` mutant.
    spec = CodeSpec(
        name="nocoord", num_qubits=5,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data"), CodeQubit(2, "data")),
        ancilla_qubits=(CodeQubit(3, "ancilla"), CodeQubit(4, "ancilla")),
        checks=(StabilizerCheck("x0", 3, (PauliTerm(0, "X"),)),
                StabilizerCheck("z1", 4, (PauliTerm(1, "Z"),))),
        logical_observables=(LogicalObservableSpec("lz", (PauliTerm(2, "Z"),), index=0),),
        rounds=2)
    sched = compile_code_spec_to_substep_schedule(spec)
    assert sched.qubit_coords == {0: (), 1: (), 2: (), 3: (), 4: ()}
    assert sched.qubit_roles == {0: "data", 1: "data", 2: "data",
                                 3: "ancilla", 4: "ancilla"}


# =========================================================================== #
# L2 REINFORCEMENT (round 2) -- the PUBLIC entry points circuit_ir_to_* and     #
# stim_circuit_to_* accept ARBITRARY CircuitIR / stim.Circuit input. An         #
# adversarial-mutation review found that an Axis-2 source key NESTED under a      #
# ``_source_projection_evaluator_audit`` subtree slipped the DATA BOUNDARY        #
# (``validate_public_metadata`` skipped the audit subtree at EVERY depth) and     #
# survived into the stored public-artifact metadata -- caught only later by the   #
# schedule compiler, which a non-compiler consumer (simulator run manifest)       #
# bypasses. A follow-up review found the TOP-LEVEL sibling: any top-level audit   #
# key smuggled wrapped Axis-2 truth into the run manifest the same way. The       #
# isolation-contract fix is FAIL-CLOSED: the audit key is rejected at EVERY       #
# position on public-artifact objects and skipped only under the internal opt-in  #
# (the transient noisy CircuitIR, gated by _allow_noise_steps). Both routes are   #
# now closed at CONSTRUCTION (see                                                 #
# ``test_L0_validate_public_metadata_audit_transport_fail_closed`` and            #
# ``test_L0_circuit_ir_toplevel_audit_transport_gated_by_allow_noise_steps``), so #
# the schedule compiler's audit/``_find_axis2`` guards are again defense-in-depth #
# -- pinned by a DIRECT probe rather than through an (unreachable) compile path.  #
# =========================================================================== #
def test_L0_reject_nested_axis2_source_leak():
    """ISOLATION-CONTRACT guard, boundary-scope fix. A ``_source_projection_evaluator_audit``
    key NESTED under another key is NOT the declared (top-level-only) transport, so the DATA
    BOUNDARY (``CircuitIR.__post_init__`` -> ``validate_public_metadata``) now rejects it at
    CONSTRUCTION -- BEFORE ``circuit_ir_to_substep_schedule`` runs -- closing the leak that
    previously reached the stored metadata. Both a dict-nested and a list-nested audit
    placement are rejected at the audit key itself; the EXACT boundary message + found path is
    pinned so the depth-scope / path-format mutants die. (The compiler backstop for a
    TOP-LEVEL audit key is pinned separately in ``test_L0_circuit_ir_reject_projected_or_noisy``.)"""
    # dict-nested audit key -> rejected at the boundary during CircuitIR construction.
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot nest the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata.foo._source_projection_evaluator_audit is permitted only at "
        "the top level of the transient noisy CircuitIR. Use evaluator_sidecars with "
        "visibility='evaluator_only'.",
        lambda: CircuitIR(
            num_qubits=1, steps=(),
            metadata={"foo": {"_source_projection_evaluator_audit":
                              {"source-process": "LEAK"}}}))
    # list-nested audit key (value is a list) -> also rejected at the audit key itself.
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot nest the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata.wrap._source_projection_evaluator_audit is permitted only at "
        "the top level of the transient noisy CircuitIR. Use evaluator_sidecars with "
        "visibility='evaluator_only'.",
        lambda: CircuitIR(
            num_qubits=1, steps=(),
            metadata={"wrap": {"_source_projection_evaluator_audit":
                               [{"ok": 1}, {"source timeline": [0.0, 1.0]}]}}))
    # CLEAN control: a nested non-axis-2 subtree constructs + compiles with NO raise (kills
    # the reject-inversion mutant that would over-reject a benign nested dict).
    ok = circuit_ir_to_substep_schedule(CircuitIR(
        num_qubits=1, steps=(), metadata={"schedule": {"name": "x"}}))
    assert ok.source_kind == "circuit_ir"


def test_L0_circuit_ir_toplevel_audit_transport_gated_by_allow_noise_steps():
    """ISOLATION-CONTRACT, FAIL-CLOSED wiring. ``CircuitIR.__post_init__`` passes
    ``allow_evaluator_audit_transport=bool(_allow_noise_steps)`` to the boundary guard, so ONLY
    the internal transient noisy circuit may carry the top-level audit transport. A public/user
    circuit (default ``_allow_noise_steps=False``) REJECTS a top-level audit key at construction
    -- closing the guard-bypass that would otherwise smuggle wrapped Axis-2 truth into the run
    manifest (simulator.py `circuit_metadata`). Pins the circuit_ir.py -> metadata_guard wiring."""
    # public/user circuit: top-level audit REJECTED at construction.
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot carry the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata._source_projection_evaluator_audit is an internal source-"
        "projection transport (permitted only on the transient noisy CircuitIR), not "
        "public-artifact metadata. Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: CircuitIR(num_qubits=1, steps=(GateOp("H", (0,)),),
                          metadata={"_source_projection_evaluator_audit": {"source_process": "x"}}))
    # internal transient noisy circuit (_allow_noise_steps=True): transport carried verbatim.
    ir = CircuitIR(num_qubits=1, steps=(GateOp("H", (0,)),),
                   metadata={"_source_projection_evaluator_audit": {"source_process": "x"}},
                   _allow_noise_steps=True)
    assert ir.metadata["_source_projection_evaluator_audit"] == {"source_process": "x"}
    # ...but even the internal circuit must not NEST the transport (top-level only).
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot nest the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata.foo._source_projection_evaluator_audit is permitted only at "
        "the top level of the transient noisy CircuitIR. Use evaluator_sidecars with "
        "visibility='evaluator_only'.",
        lambda: CircuitIR(num_qubits=1, steps=(GateOp("H", (0,)),),
                          metadata={"foo": {"_source_projection_evaluator_audit":
                                            {"source_process": "x"}}},
                          _allow_noise_steps=True))


def test_L0_validate_public_metadata_audit_transport_fail_closed():
    """ISOLATION-CONTRACT data boundary (the fix). The declared
    ``_source_projection_evaluator_audit`` transport is FAIL-CLOSED: ``validate_public_metadata``
    rejects it at EVERY position by DEFAULT (public-artifact objects) and skips it ONLY at the
    TOP LEVEL under the internal opt-in ``allow_evaluator_audit_transport=True`` (the transient
    noisy CircuitIR, gated by _allow_noise_steps). This closes the top-level guard-bypass where a
    top-level audit key would smuggle any wrapped Axis-2 key into the stored public-artifact
    metadata (copied into CompiledCircuit.metadata, serialized into the run manifest, outside the
    schedule compiler's reject guard). Exercises the boundary DIRECTLY, not via the compile path."""
    # --- DEFAULT (public-artifact) rejects the audit key at EVERY position --------------------
    # top level -> the internal-transport rejection.
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot carry the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata._source_projection_evaluator_audit is an internal source-"
        "projection transport (permitted only on the transient noisy CircuitIR), not "
        "public-artifact metadata. Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: validate_public_metadata(
            {"_source_projection_evaluator_audit": {"source_process": "LEAK"}},
            label="CircuitIR.metadata"))
    # nested (dict) shielding a reserved key -> the nested rejection.
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot nest the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata.foo._source_projection_evaluator_audit is permitted only at "
        "the top level of the transient noisy CircuitIR. Use evaluator_sidecars with "
        "visibility='evaluator_only'.",
        lambda: validate_public_metadata(
            {"foo": {"_source_projection_evaluator_audit": {"source_process": "LEAK"}}},
            label="CircuitIR.metadata"))
    # nested audit with a CLEAN subtree is still rejected (misplaced transport, not content).
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot nest the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata.wrap._source_projection_evaluator_audit is permitted only at "
        "the top level of the transient noisy CircuitIR. Use evaluator_sidecars with "
        "visibility='evaluator_only'.",
        lambda: validate_public_metadata(
            {"wrap": {"_source_projection_evaluator_audit": {"harmless": 1}}},
            label="CircuitIR.metadata"))
    # a bare top-level reserved key is still rejected (control; unchanged reserved-key path).
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator truth; reserved key "
        "CircuitIR.metadata.source_process matches 'source_process'. "
        "Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: validate_public_metadata({"source_process": {"x": 1}},
                                         label="CircuitIR.metadata"))
    # --- INTERNAL opt-in: the TOP-LEVEL transport survives, even carrying source_* truth -------
    payload = {"_source_projection_evaluator_audit":
               {"source_process": "audit", "source_timeline": [0.0]}}
    assert validate_public_metadata(
        dict(payload), label="CircuitIR.metadata",
        allow_evaluator_audit_transport=True) == payload
    # ...but the opt-in is TOP-LEVEL ONLY: a nested audit key is rejected even under the flag.
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot nest the evaluator-only audit transport; reserved "
        "key CircuitIR.metadata.foo._source_projection_evaluator_audit is permitted only at "
        "the top level of the transient noisy CircuitIR. Use evaluator_sidecars with "
        "visibility='evaluator_only'.",
        lambda: validate_public_metadata(
            {"foo": {"_source_projection_evaluator_audit": {"source_process": "LEAK"}}},
            label="CircuitIR.metadata", allow_evaluator_audit_transport=True))


def test_L0_find_axis2_source_metadata_path_direct():
    """DEFENSE-IN-DEPTH PROBE. Since the boundary fix rejects a nested audit key at
    construction, no constructed ``CircuitIR`` can carry an audit-shielded Axis-2 key into
    ``_reject_projected_or_noisy_circuit``, so ``_find_axis2_source_metadata_path`` is
    unreachable via the public compile path. It stays as a load-bearing backstop, so its
    recursion arms are pinned here by DIRECT calls on raw dicts/lists: the dict-recursion arm
    with a dashed key (``.replace("-","_")``), the list-recursion arm with a spaced key at a
    specific index (``.replace(" ","_")``), the first-match short-circuit under a non-default
    path label, and the None-return on clean trees. ``_reject_projected_or_noisy_circuit``
    still raises when handed such a (hand-built, unvalidated) dict via ``circuit.metadata``."""
    # dict-recursion arm, dashed axis-2 key, exact found-path.
    assert _find_axis2_source_metadata_path(
        {"foo": {"bar": {"source-process": "LEAK"}}}
    ) == "CircuitIR.metadata.foo.bar.source-process"
    # list-recursion arm, spaced axis-2 key at list index 1, exact found-path.
    assert _find_axis2_source_metadata_path(
        {"wrap": [{"ok": 1}, {"source timeline": [0.0, 1.0]}]}
    ) == "CircuitIR.metadata.wrap[1].source timeline"
    # first-match short-circuit + non-default path label.
    assert _find_axis2_source_metadata_path({"source_binding": 1}, path="X") == "X.source_binding"
    # CLEAN: nested non-axis-2 dict / list return None (no fabricated leak).
    assert _find_axis2_source_metadata_path({"schedule": {"name": "x"}}) is None
    assert _find_axis2_source_metadata_path([{"ok": 1}, {"deep": {"clean": 2}}]) is None
    # Backstops still fire if unvalidated metadata ever reaches the compiler guard: hand stub
    # circuits (bypassing CircuitIR.__post_init__ validation) with an audit key. (1) A TOP-LEVEL
    # audit key trips the compiler's own audit check (analog_schedule.py:1065). (2) A NESTED
    # audit subtree hiding an Axis-2 key misses the top-level check and is caught by the
    # recursion; the EXACT compiler message + integrated found-path are pinned.
    _raises_exact(
        ValueError,
        "Source projection evaluator audit cannot be used as Axis-1 schedule metadata",
        lambda: _reject_projected_or_noisy_circuit(SimpleNamespace(
            metadata={"_source_projection_evaluator_audit": {"x": 1}})))
    _raises_exact(
        ValueError,
        "Axis-1 SubstepSchedule metadata cannot contain Axis-2 source truth; found "
        "CircuitIR.metadata.foo._source_projection_evaluator_audit.source-process",
        lambda: _reject_projected_or_noisy_circuit(SimpleNamespace(
            metadata={"foo": {"_source_projection_evaluator_audit":
                              {"source-process": "LEAK"}}})))


def _codespec_schedule(cs_meta, *, num_qubits=6):
    return circuit_ir_to_substep_schedule(
        CircuitIR(num_qubits=num_qubits, steps=(), metadata={"code_spec": cs_meta}))


def test_L0_qubit_metadata_from_raw_code_spec_metadata():
    # the PUBLIC entry accepts a raw "code_spec" metadata block (validate does not reserve
    # code_spec/data_qubits/role/coords). With NO top-level "qubit_coords" block the
    # code_spec-block coords are the FINAL value. Entry 0/2 carry NO role -> the loop DEFAULT
    # is materialized ("data"/"ancilla"); entry 1 carries a NON-default role -> observed
    # verbatim. Kills the role-default/-key mutants and the coords-extraction mutants.
    sched = _codespec_schedule({
        "data_qubits": [{"index": 0, "coords": [1.0, 2.0]},
                        {"index": 1, "role": "custom_role"}],
        "ancilla_qubits": [{"index": 2, "coords": [5.0, 6.0]}]}, num_qubits=3)
    assert sched.qubit_roles == {0: "data", 1: "custom_role", 2: "ancilla"}
    # entry 1 has no coords -> () (kills coords[q]=None + the get-default mutants); entries
    # with coords keep them (NOT overwritten, since no qubit_coords metadata block).
    assert sched.qubit_coords == {0: (1.0, 2.0), 1: (), 2: (5.0, 6.0)}

    def prop(roles):
        assert roles == {0: "data", 1: "custom_role", 2: "ancilla"}

    assert_discriminates(prop, sched.qubit_roles, {0: "data", 1: "data", 2: "ancilla"},
                         label="qubit_metadata roles")


def test_L0_qubit_metadata_code_spec_edge_cases():
    # (a) missing "ancilla_qubits" key -> the `code_spec.get(key, ())` default is LIVE (kills
    # the `get(key, None)`/no-default mutant that would iterate None -> TypeError).
    assert _codespec_schedule(
        {"data_qubits": [{"index": 0, "coords": [1.0, 2.0]}]},
        num_qubits=3).qubit_roles == {0: "data"}
    # (b) a str "data_qubits" trips the Sequence/str guard and must CONTINUE to ancilla (kills
    # the guard `continue`->`break`, which would drop the ancilla roles).
    assert _codespec_schedule(
        {"data_qubits": "bad", "ancilla_qubits": [{"index": 0, "coords": [1.0, 2.0]}]},
        num_qubits=3).qubit_roles == {0: "ancilla"}
    # (c) an entry without "index" must be SKIPPED (continue), and processing must CONTINUE to
    # the next entry (kills the entry-guard `or`->`and` KeyError and the `continue`->`break`).
    assert _codespec_schedule(
        {"data_qubits": [{"noindex": 1}, {"index": 5, "coords": [1.0, 2.0]}]},
        num_qubits=6).qubit_roles == {5: "data"}
    # (d) a non-Sequence, non-str "data_qubits" (an int) trips the OUTER Sequence guard and must
    # CONTINUE to ancilla. Kills the outer-guard `or`->`and` mutant: under `and`, `not
    # isinstance(5, Sequence)` is True but `isinstance(5, (str, bytes))` is False, so it does NOT
    # continue and falls into `for entry in 5` -> TypeError. (A str value, case (b), cannot catch
    # this -- str is iterable, so both `or` and `and` yield the same empty result.)
    assert _codespec_schedule(
        {"data_qubits": 5, "ancilla_qubits": [{"index": 0, "coords": [1.0, 2.0]}]},
        num_qubits=3).qubit_roles == {0: "ancilla"}


def test_L0_stim_observable_non_record_target_raise():
    # an OBSERVABLE_INCLUDE whose target is a Pauli (not a measurement record) trips the
    # `is_measurement_record_target` guard raise (kills the message-None mutant #14).
    import stim
    _raises_exact(
        ValueError,
        "OBSERVABLE_INCLUDE target stim.target_x(0) is not a measurement record target",
        lambda: stim_circuit_to_substep_schedule(stim.Circuit("M 0\nOBSERVABLE_INCLUDE(0) X0")))


def test_L0_stim_observable_record_out_of_range():
    # an OBSERVABLE_INCLUDE referencing rec[-1] with NO prior measurement points outside the
    # record (index -1) -> the out-of-range raise via the OBSERVABLE route (kills the
    # `instruction=None` mutant that would drop 'OBSERVABLE_INCLUDE' from the message).
    import stim
    circuit = stim.Circuit()
    circuit.append("OBSERVABLE_INCLUDE", [stim.target_rec(-1)], 0)
    _raises_exact(
        ValueError,
        "OBSERVABLE_INCLUDE record target stim.target_rec(-1) points outside previous "
        "measurements",
        lambda: stim_circuit_to_substep_schedule(circuit))


def test_L0_stim_importer_preserves_imported_from_and_coords():
    # direct-call the importer: the reconstructed CircuitIR carries imported_from + coords
    # (kills the "imported_from" key/value string mutants #142-145).
    import stim
    circuit = stim.Circuit()
    circuit.append("QUBIT_COORDS", [0], [0.0, 0.0])
    circuit.append("H", [0])
    circuit.append("M", [0])
    ir = _stim_circuit_to_circuit_ir(circuit)
    assert ir.metadata["imported_from"] == "stim_circuit"
    assert ir.metadata["qubit_coords"] == {"0": [0.0, 0.0]}


def test_L0_operation_from_step_and_step_manifest_defensive_typeerrors():
    # these defensive raises are unreachable through the public compiler (record-only steps
    # are flushed before extraction; CircuitIR only holds known step types), so trip them by
    # a DIRECT call -- the EXACT message (with the step type) kills the msg-None and
    # type(None) mutants (#46/#47 and #55/#56).
    with pytest.raises(TypeError, match=r"record-only step.*DetectorDef.*should not reach"):
        _operation_from_step(DetectorDef("d0", ()), 0)
    with pytest.raises(TypeError, match=r"unknown CircuitIR step.*object"):
        _step_manifest(object())


def test_L0_has_valid_seal_non_str_signature_and_non_schedule():
    # a NON-STRING (int) tampered signature: the guard `not isinstance(sig, str) or not sig`
    # returns False WITHOUT reaching compare_digest; the `or`->`and` mutant falls through to
    # hmac.compare_digest(int, hex) -> TypeError, so pinning False kills it.
    sealed = circuit_ir_to_substep_schedule(CircuitBuilder(2).h(0).build())
    object.__setattr__(sealed, "_compiler_signature", 12345)
    assert has_valid_compiler_schedule_seal(sealed) is False
    # an object WITHOUT the attribute exercises the getattr DEFAULT (kills the no-default
    # mutant, which would raise AttributeError instead of returning False).
    assert has_valid_compiler_schedule_seal(object()) is False


def test_L0_circuit_ir_nonascii_metadata_hash_ensure_ascii():
    # a NON-ASCII metadata value makes ensure_ascii load-bearing: the independent hash uses
    # ensure_ascii=True, so an ensure_ascii=False mutant in _stable_hash yields a different
    # digest -> mismatch -> killed.
    circuit = CircuitIR(num_qubits=2, steps=(GateOp("H", (0,)),),
                        metadata={"note": "café-π"})
    sched = circuit_ir_to_substep_schedule(circuit)
    assert sched.source_hash == _indep_circuit_ir_source_hash(circuit)

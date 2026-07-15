"""Stage-D batch ``circuit_ir`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.circuit_ir`` (23 CPU-pure public units: 5 frozen-dataclass
``__post_init__`` dunders + 3 ``CircuitIR`` record-schema properties + 15 ``CircuitBuilder``
fluent methods; no torch, no quimb, so out_of_scope is empty).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4;
work-list docs/SIMULATOR.md D15).
``frontend/circuit_ir.py`` owns the user-facing, Stim-compatible circuit IR: the frozen
dataclasses (``GateOp``/``Tick``/``MeasureOp``/``DetectorDef``/``ObservableDef``) whose
``__post_init__`` normalizes names/targets/keys/args/coords/index, the validating ``CircuitIR``
container (+ ``measurement_keys``/``detector_names``/``observable_names``), and the
``CircuitBuilder`` fluent API that assembles them.

L2 DISCIPLINE (100% coverage != discrimination). The workhorse is EXACT-STRUCTURE pinning: a
from-scratch ``_view()`` reconstruction of each step tuple pins the built ``CircuitIR`` ordered
steps against an INDEPENDENT expectation (NOT the module's own accessors). The record-schema
properties are pinned vs an INDEPENDENT extraction from the constructed steps (a comprehension
over the step tuples the test built, NEVER the module's property), with an ``assert_discriminates``
dropped/wrong-name variant. Every validation RAISE asserts its EXACT message via
``str(excinfo.value)==...`` so mutmut's string-literal wrap/case mutants die.

SET-ELEMENT string mutants (the module-level ``_RECORD_AFFECTING_GATE_NAMES`` /
``_SOURCE_NOISE_GATE_NAMES`` sets) are killed by PARAMETRIZED coverage of EVERY element -- each
name is fed as a ``GateOp`` inside a ``CircuitIR`` and must raise its dedicated ``ValueError``.
The private helpers (``_as_targets``/``_as_args``/``_validate_targets``/``_require_known_keys``)
are exercised + pinned through the public builder/``CircuitIR`` paths (mutmut is coverage-guided:
both ``_validate_targets`` arcs and both ``_require_known_keys`` arcs are tripped, and every
``_as_targets``/``_as_args`` branch + coercion is fed a value that makes it load-bearing).
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates

import error_coupling_simulator.frontend.circuit_ir as cir
from error_coupling_simulator.frontend.circuit_ir import (
    CircuitBuilder,
    CircuitIR,
    DetectorDef,
    GateOp,
    MeasureOp,
    ObservableDef,
    Tick,
)
from error_coupling_simulator.frontend.axis1_context import Axis1LocalLindbladContextSpec


# --------------------------------------------------------------------------- #
# helpers: exact-message raise + INDEPENDENT step reconstruction               #
# --------------------------------------------------------------------------- #
def _raises_exact(exc, msg, fn):
    """pytest.raises pinning the EXACT ``str(exc)`` (kills mutmut string-literal wrap/case
    mutants that a substring ``match=`` lets survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _view(step):
    """A comparable, from-scratch view of one CircuitIR step (NOT built from the module's
    own accessors)."""
    if isinstance(step, Tick):
        return ("T",)
    if isinstance(step, GateOp):
        return ("G", step.name, tuple(step.targets), tuple(step.args))
    if isinstance(step, MeasureOp):
        return ("M", step.name, tuple(step.targets), tuple(step.keys), tuple(step.args))
    if isinstance(step, DetectorDef):
        return ("D", step.name, tuple(step.keys), tuple(step.coords))
    if isinstance(step, ObservableDef):
        return ("O", step.name, tuple(step.keys), step.index)
    raise AssertionError(f"unexpected step {step!r}")


def _views(ir):
    return [_view(s) for s in ir.steps]


# =========================================================================== #
# GateOp.__post_init__                                                          #
# =========================================================================== #
def test_L0_gateop_post_init_normalizes():
    op = GateOp("h", ["3", "4"], ["0.5"])
    assert op.name == "H"                                    # name uppercased
    assert op.targets == (3, 4) and all(type(t) is int for t in op.targets)   # int() coercion
    assert op.args == (0.5,) and all(type(a) is float for a in op.args)       # float() coercion
    assert GateOp("X", (0,)).args == ()                      # default args


def test_KILLER_gateop_name_uppercased():
    def prop(op):
        assert op.name == "CZ"
    class _Wrong:                                            # a raw (un-normalized) name
        name = "cz"
    assert_discriminates(prop, GateOp("cz", (0, 1)), _Wrong(), label="GateOp.name upper")


# =========================================================================== #
# MeasureOp.__post_init__                                                       #
# =========================================================================== #
def test_L0_measureop_post_init_normalizes():
    op = MeasureOp("mx", ["0"], [5], ["0.1"])
    assert op.name == "MX"                                   # name uppercased
    assert op.targets == (0,) and type(op.targets[0]) is int
    assert op.keys == ("5",) and type(op.keys[0]) is str     # keys str() coercion
    assert op.args == (0.1,) and type(op.args[0]) is float
    assert MeasureOp("M", (0,), ("m",)).args == ()           # default args


# =========================================================================== #
# DetectorDef.__post_init__                                                     #
# =========================================================================== #
def test_L0_detectordef_post_init_normalizes():
    d = DetectorDef(5, [6], ["1.5"])
    assert d.name == "5" and type(d.name) is str             # name str() (NOT uppercased)
    assert d.keys == ("6",) and type(d.keys[0]) is str
    assert d.coords == (1.5,) and type(d.coords[0]) is float
    assert DetectorDef("dX", ("m",)).name == "dX"            # case preserved (str, not .upper())
    assert DetectorDef("d", ("m",)).coords == ()             # default coords


# =========================================================================== #
# ObservableDef.__post_init__                                                   #
# =========================================================================== #
def test_L0_observabledef_post_init_normalizes():
    o = ObservableDef(7, [8], "2")
    assert o.name == "7" and type(o.name) is str
    assert o.keys == ("8",) and type(o.keys[0]) is str
    assert o.index == 2 and type(o.index) is int             # index int() coercion
    assert ObservableDef("L", ("m",)).index == 0             # default index


# =========================================================================== #
# CircuitIR.__post_init__ -- normalization + every validation guard             #
# =========================================================================== #
def test_L0_circuit_ir_normalizes_fields():
    ir = CircuitIR(num_qubits=2.0, steps=[GateOp("H", (0,))], metadata={"foo": 1})
    assert type(ir.num_qubits) is int and ir.num_qubits == 2  # num_qubits int() coercion
    assert isinstance(ir.steps, tuple) and len(ir.steps) == 1  # steps tuple() coercion
    assert ir.metadata == {"foo": 1}
    src = {"foo": 1}
    ir2 = CircuitIR(num_qubits=1, steps=(), metadata=src)
    assert ir2.metadata == src and ir2.metadata is not src     # metadata copied, not aliased


def test_L0_circuit_ir_num_qubits_positive_guard():
    _raises_exact(ValueError, "num_qubits must be positive",
                  lambda: CircuitIR(num_qubits=0, steps=(), metadata={}))
    _raises_exact(ValueError, "num_qubits must be positive",
                  lambda: CircuitIR(num_qubits=-2, steps=(), metadata={}))


@pytest.mark.parametrize("name", sorted(cir._RECORD_AFFECTING_GATE_NAMES))
def test_L0_circuit_ir_record_affecting_gate_raises(name):
    # every record-affecting name individually trips the raise (kills set-element mutants)
    _raises_exact(
        ValueError,
        f"record-affecting instruction {name!r} must use "
        "MeasureOp/DetectorDef/ObservableDef, not GateOp",
        lambda: CircuitIR(num_qubits=1, steps=(GateOp(name, (0,)),), metadata={}),
    )


@pytest.mark.parametrize("name", sorted(cir._SOURCE_NOISE_GATE_NAMES))
def test_L0_circuit_ir_source_noise_gate_raises(name):
    # every source-noise name individually trips the raise (kills set-element mutants)
    _raises_exact(
        ValueError,
        f"source-embedded noise instruction {name!r} is not allowed in CircuitIR; "
        "use NoiseBuilder/StimPauliNoiseSpec or pass an explicit pre-noised Stim source",
        lambda: CircuitIR(num_qubits=1, steps=(GateOp(name, (0,)),), metadata={}),
    )
    # the allow route accepts the same op (exercises bool(_allow_noise_steps) + the `not allow` False arc)
    ir = CircuitIR(num_qubits=1, steps=(GateOp(name, (0,)),), metadata={}, _allow_noise_steps=1)
    assert ir.steps[0].name == name


def test_L0_circuit_ir_validate_targets_both_arcs():
    _raises_exact(ValueError, "target 5 outside [0, 1)",
                  lambda: CircuitIR(num_qubits=1, steps=(GateOp("H", (5,)),), metadata={}))
    _raises_exact(ValueError, "target -1 outside [0, 1)",
                  lambda: CircuitIR(num_qubits=1, steps=(GateOp("H", (-1,)),), metadata={}))
    # boundary: t == num_qubits must raise (kills the `t >= nq` -> `t > nq` mutant)
    _raises_exact(ValueError, "target 2 outside [0, 2)",
                  lambda: CircuitIR(num_qubits=2, steps=(GateOp("H", (2,)),), metadata={}))


def test_L0_circuit_ir_measure_key_guards():
    _raises_exact(
        ValueError, "measurement keys ('m0',) do not match (0, 1)",
        lambda: CircuitIR(num_qubits=2, steps=(MeasureOp("M", (0, 1), ("m0",)),), metadata={}))
    _raises_exact(
        ValueError, "duplicate measurement key 'm0'",
        lambda: CircuitIR(num_qubits=2, steps=(MeasureOp("M", (0, 1), ("m0", "m0")),), metadata={}))


def test_L0_circuit_ir_detector_guards():
    dup = (MeasureOp("M", (0,), ("m0",)), DetectorDef("d0", ("m0",)), DetectorDef("d0", ("m0",)))
    _raises_exact(ValueError, "duplicate detector name 'd0'",
                  lambda: CircuitIR(num_qubits=1, steps=dup, metadata={}))
    unk = (MeasureOp("M", (0,), ("m0",)), DetectorDef("d0", ("zz",)))
    _raises_exact(ValueError, "unknown measurement key(s): ['zz']",
                  lambda: CircuitIR(num_qubits=1, steps=unk, metadata={}))


def test_L0_circuit_ir_observable_guards():
    neg = (MeasureOp("M", (0,), ("m0",)), ObservableDef("o", ("m0",), -1))
    _raises_exact(ValueError, "observable index must be non-negative, got -1",
                  lambda: CircuitIR(num_qubits=1, steps=neg, metadata={}))
    dupidx = (MeasureOp("M", (0,), ("m0",)), ObservableDef("o0", ("m0",), 0),
              ObservableDef("o1", ("m0",), 0))
    _raises_exact(ValueError, "duplicate observable index 0",
                  lambda: CircuitIR(num_qubits=1, steps=dupidx, metadata={}))
    unk = (MeasureOp("M", (0,), ("m0",)), ObservableDef("o", ("zz",), 0))
    _raises_exact(ValueError, "unknown measurement key(s): ['zz']",
                  lambda: CircuitIR(num_qubits=1, steps=unk, metadata={}))


def test_L0_circuit_ir_unknown_step_and_tick():
    _raises_exact(TypeError, "unknown circuit step <class 'int'>",
                  lambda: CircuitIR(num_qubits=1, steps=(42,), metadata={}))
    # a Tick is accepted -- the `elif not isinstance(step, Tick)` False arc
    ir = CircuitIR(num_qubits=1, steps=(Tick(),), metadata={})
    assert _views(ir) == [("T",)]


def test_L0_circuit_ir_metadata_reserved_key_raises_with_label():
    # the reserved-key guard message carries the CircuitIR.metadata label -> pin it exactly
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator truth; "
        "reserved key CircuitIR.metadata.ground_truth matches 'ground_truth'. "
        "Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: CircuitIR(num_qubits=1, steps=(), metadata={"ground_truth": 1}))


# =========================================================================== #
# CircuitIR.measurement_keys / detector_names / observable_names                #
# =========================================================================== #
def _multi_ir():
    """A CircuitIR whose steps mix gates/ticks with two measures, two detectors, two
    observables -- so the property isinstance-filters are load-bearing."""
    steps = (
        GateOp("H", (0,)),
        Tick(),
        MeasureOp("M", (0, 1), ("a", "b")),
        MeasureOp("MX", (2,), ("c",)),
        DetectorDef("d0", ("a",)),
        DetectorDef("d1", ("b", "c")),
        ObservableDef("L0", ("a",), 0),
        ObservableDef("L1", ("c",), 1),
    )
    return CircuitIR(num_qubits=3, steps=steps, metadata={}), steps


def test_L0_measurement_keys_independent_pin():
    ir, steps = _multi_ir()
    expected = tuple(k for s in steps if isinstance(s, MeasureOp) for k in s.keys)
    assert expected == ("a", "b", "c")
    assert ir.measurement_keys == expected
    def prop(mk):
        assert mk == expected
    assert_discriminates(prop, ir.measurement_keys, ("a", "b"), label="measurement_keys")


def test_L0_detector_names_independent_pin():
    ir, steps = _multi_ir()
    expected = tuple(s.name for s in steps if isinstance(s, DetectorDef))
    assert expected == ("d0", "d1")
    assert ir.detector_names == expected
    def prop(dn):
        assert dn == expected
    assert_discriminates(prop, ir.detector_names, ("d0",), label="detector_names")


def test_L0_observable_names_independent_pin():
    ir, steps = _multi_ir()
    expected = tuple(s.name for s in steps if isinstance(s, ObservableDef))
    assert expected == ("L0", "L1")
    assert ir.observable_names == expected
    def prop(on):
        assert on == expected
    assert_discriminates(prop, ir.observable_names, ("L0", "WRONG"), label="observable_names")


# =========================================================================== #
# CircuitBuilder -- fluent chain (each method's effect present in the built IR)  #
# =========================================================================== #
def _full_builder():
    b = CircuitBuilder(num_qubits=4, metadata={"note": "demo"})
    (b.h(0).x(1).y(2).reset(3)
      .cz([0, 1]).cx([2, 3])
      .idle(0)
      .idle(1, duration_ns=25.0)
      .tick()
      .measure([0, 1, 2, 3], key=["m0", "m1", "m2", "m3"])
      .detector("d0", xor=["m0", "m1"], coords=[1.0, 2.0])
      .observable("L0", xor=["m2", "m3"], index=0))
    return b


_FULL_EXPECTED = [
    ("G", "H", (0,), ()),
    ("G", "X", (1,), ()),
    ("G", "Y", (2,), ()),
    ("G", "R", (3,), ()),
    ("G", "CZ", (0, 1), ()),
    ("G", "CX", (2, 3), ()),
    ("G", "I", (0,), ()),
    ("G", "I", (1,), (25.0,)),
    ("T",),
    ("M", "M", (0, 1, 2, 3), ("m0", "m1", "m2", "m3"), ()),
    ("D", "d0", ("m0", "m1"), (1.0, 2.0)),
    ("O", "L0", ("m2", "m3"), 0),
]


def test_L0_fluent_chain_full_circuit_pins_ordered_steps():
    ir = _full_builder().build()
    assert _views(ir) == _FULL_EXPECTED
    assert ir.num_qubits == 4
    assert ir.metadata == {"note": "demo"}
    # each builder method's effect present + ordered; a single wrong op fails the pin
    def prop(views):
        assert views == _FULL_EXPECTED
    wrong = list(_FULL_EXPECTED)
    wrong[0] = ("G", "X", (0,), ())              # H mutated to X
    assert_discriminates(prop, _views(ir), wrong, label="fluent chain ordered steps")


# =========================================================================== #
# CircuitBuilder.gate (+ _as_targets / _as_args private helpers)                #
# =========================================================================== #
def test_L0_builder_gate_target_and_arg_coercion():
    b = CircuitBuilder(3)
    b.gate("rz", 0, args=None)                    # int target -> _as_targets int arc; args None arc
    b.gate("rz", [0, 1], args=0.5)                # sequence target arc; scalar args arc
    b.gate("rz", ["2"], args=["0.25", "0.75"])    # string-int target arc; sequence args arc
    ir = b.build()
    assert _views(ir) == [
        ("G", "RZ", (0,), ()),
        ("G", "RZ", (0, 1), (0.5,)),
        ("G", "RZ", (2,), (0.25, 0.75)),
    ]
    assert b.gate("rz", 0) is b                    # returns self


# =========================================================================== #
# CircuitBuilder.tick / h / x / y / reset / idle                                #
# =========================================================================== #
def test_L0_builder_tick():
    b = CircuitBuilder(1)
    assert b.tick() is b
    assert _views(b.build()) == [("T",)]


def test_L0_builder_single_qubit_gate_names():
    b = CircuitBuilder(3)
    assert b.h(0) is b
    assert b.x(1) is b
    assert b.y(2) is b
    assert b.reset(0) is b
    assert _views(b.build()) == [
        ("G", "H", (0,), ()), ("G", "X", (1,), ()),
        ("G", "Y", (2,), ()), ("G", "R", (0,), ()),
    ]


def test_L0_builder_idle_no_duration_and_with_duration():
    b = CircuitBuilder(2)
    assert b.idle(0) is b                          # duration None -> args ()
    b.idle(1, duration_ns=25)                       # duration -> float() coercion -> args (25.0,)
    assert _views(b.build()) == [("G", "I", (0,), ()), ("G", "I", (1,), (25.0,))]


# =========================================================================== #
# CircuitBuilder.cz / cx                                                         #
# =========================================================================== #
def test_L0_builder_cz_cx_even_and_odd():
    b = CircuitBuilder(4)
    assert b.cz([0, 1]) is b
    assert b.cx([2, 3]) is b
    assert _views(b.build()) == [("G", "CZ", (0, 1), ()), ("G", "CX", (2, 3), ())]
    _raises_exact(ValueError, "CZ targets must be an even-length pair list",
                  lambda: CircuitBuilder(3).cz([0, 1, 2]))
    _raises_exact(ValueError, "CZ targets must be an even-length pair list",
                  lambda: CircuitBuilder(1).cz([0]))
    _raises_exact(ValueError, "CX targets must be an even-length pair list",
                  lambda: CircuitBuilder(3).cx([0, 1, 2]))
    _raises_exact(ValueError, "CX targets must be an even-length pair list",
                  lambda: CircuitBuilder(1).cx([0]))


# =========================================================================== #
# CircuitBuilder.measure                                                         #
# =========================================================================== #
@pytest.mark.parametrize("basis,reset,name", [
    ("Z", False, "M"), ("Z", True, "MR"),
    ("X", False, "MX"), ("X", True, "MRX"),
    ("Y", False, "MY"), ("Y", True, "MRY"),
    ("z", False, "M"),                              # lowercase basis normalized to Z
])
def test_L0_builder_measure_basis_reset_names(basis, reset, name):
    b = CircuitBuilder(1)
    assert b.measure(0, key="m", basis=basis, reset=reset) is b
    assert _view(b.build().steps[0]) == ("M", name, (0,), ("m",), ())


def test_L0_builder_measure_duration_and_sequence_keys():
    b = CircuitBuilder(2)
    b.measure([0, 1], key=["m0", "m1"], duration_ns=30)   # sequence keys + duration float() coercion
    assert _view(b.build().steps[0]) == ("M", "M", (0, 1), ("m0", "m1"), (30.0,))


def test_L0_builder_measure_raises():
    _raises_exact(ValueError, "measurement keys ('m0',) do not match targets (0, 1)",
                  lambda: CircuitBuilder(2).measure([0, 1], key="m0"))
    b = CircuitBuilder(2)
    b.measure(0, key="m")
    _raises_exact(ValueError, "duplicate measurement key 'm'",
                  lambda: b.measure(1, key="m"))
    _raises_exact(ValueError, "unsupported measurement basis 'W'",
                  lambda: CircuitBuilder(1).measure(0, key="m", basis="w"))
    _raises_exact(ValueError, "target 2 outside [0, 1)",
                  lambda: CircuitBuilder(1).measure(2, key="m"))


# =========================================================================== #
# CircuitBuilder.detector / observable (+ _require_known_keys)                   #
# =========================================================================== #
def test_L0_builder_detector_known_coords_and_name_str():
    b = CircuitBuilder(2)
    b.measure([0, 1], key=["a", "b"])
    assert b.detector(7, xor=["a", "b"], coords=["1.5", "2.5"]) is b
    assert _view(b.build().steps[-1]) == ("D", "7", ("a", "b"), (1.5, 2.5))


def test_L0_builder_detector_unknown_key_raises():
    b = CircuitBuilder(1)
    b.measure(0, key="a")
    _raises_exact(ValueError, "unknown measurement key(s): ['zz']",
                  lambda: b.detector("d", xor=["zz"]))


def test_L0_builder_observable_known_index_and_name_str():
    b = CircuitBuilder(1)
    b.measure(0, key="a")
    assert b.observable(9, xor=["a"], index="3") is b    # name str(), index int() coercion
    assert _view(b.build().steps[-1]) == ("O", "9", ("a",), 3)


def test_L0_builder_observable_unknown_key_raises():
    b = CircuitBuilder(1)
    b.measure(0, key="a")
    _raises_exact(ValueError, "unknown measurement key(s): ['zz']",
                  lambda: b.observable("L", xor=["zz"]))


def test_L0_builder_observable_default_index_is_zero():
    # exercise the DEFAULT index arg (the D13 reachable-default lesson): omitting index -> 0
    b = CircuitBuilder(1)
    b.measure(0, key="a")
    b.observable("L", xor=["a"])                    # no index -> default 0
    assert _view(b.build().steps[-1]) == ("O", "L", ("a",), 0)


# =========================================================================== #
# CircuitBuilder.declare_static_zz_couplings                                     #
# =========================================================================== #
def test_L0_declare_static_zz_couplings_with_calibrations():
    b = CircuitBuilder(4)
    assert b.declare_static_zz_couplings(
        [[1, 0], [2, 3]], zeta_rad_per_ns_by_edge={(0, 1): 0.5}) is b
    ir = b.build()
    assert ir.metadata["axis1_static_zz_couplings"] == [[0, 1], [2, 3]]   # normalized + sorted
    assert ir.metadata["axis1_static_zz_calibrations"] == [
        {"edge": [0, 1], "zeta_rad_per_ns": 0.5, "epistemic_class": "c"}]


def test_L0_declare_static_zz_couplings_without_calibrations_pops():
    b = CircuitBuilder(4)
    b.declare_static_zz_couplings([[0, 1]])              # no zeta -> else-branch pop (key absent)
    ir = b.build()
    assert ir.metadata["axis1_static_zz_couplings"] == [[0, 1]]
    assert "axis1_static_zz_calibrations" not in ir.metadata


def test_L0_declare_static_zz_couplings_pop_removes_prior_calibrations():
    b = CircuitBuilder(4)
    b.declare_static_zz_couplings([[0, 1]], zeta_rad_per_ns_by_edge={(0, 1): 0.5})
    assert "axis1_static_zz_calibrations" in b._metadata   # present after the calibrated call
    b.declare_static_zz_couplings([[0, 1]])                # second (uncalibrated) call clears it
    assert "axis1_static_zz_calibrations" not in b._metadata  # the pop actually removed it


def test_L0_declare_static_zz_couplings_coupling_route_pins_num_qubits_and_label():
    # an out-of-range EDGE routes through the FIRST normalize with num_qubits=self.num_qubits and
    # label="CircuitBuilder.declare_static_zz_couplings"; the EXACT message pins both call args
    # (kills num_qubits=None -> no raise, and every label mutant -> different message).
    _raises_exact(
        ValueError,
        "CircuitBuilder.declare_static_zz_couplings[0] endpoint 5 outside [0, 2)",
        lambda: CircuitBuilder(2).declare_static_zz_couplings([[0, 5]]))


def test_L0_declare_static_zz_couplings_calibration_route_pins_declared_and_label():
    # an in-range but UNDECLARED calibration edge routes through the SECOND normalize with
    # declared_edges=normalized and label=...zeta_rad_per_ns_by_edge; the EXACT message pins both
    # (kills declared_edges=None -> no raise, and every calibration-label mutant).
    _raises_exact(
        ValueError,
        "CircuitBuilder.declare_static_zz_couplings.zeta_rad_per_ns_by_edge[0] edge (2, 3) "
        "is not declared in axis1_static_zz_couplings",
        lambda: CircuitBuilder(4).declare_static_zz_couplings(
            [[0, 1]], zeta_rad_per_ns_by_edge={(2, 3): 0.5}))


def test_L0_declare_static_zz_couplings_calibration_range_pins_num_qubits():
    # an out-of-range + undeclared calibration edge: the range check (which needs
    # num_qubits=self.num_qubits) must fire BEFORE the declared check -> a range message, NOT a
    # not-declared message (kills the calibration-normalize num_qubits=None mutants).
    _raises_exact(
        ValueError,
        "CircuitBuilder.declare_static_zz_couplings.zeta_rad_per_ns_by_edge[0].edge[0] "
        "endpoint 5 outside [0, 2)",
        lambda: CircuitBuilder(2).declare_static_zz_couplings(
            [[0, 1]], zeta_rad_per_ns_by_edge={(0, 5): 0.5}))


# =========================================================================== #
# CircuitBuilder.declare_axis1_local_lindblad_context                            #
# =========================================================================== #
def test_L0_declare_axis1_context_nontrivial_sets_manifest():
    b = CircuitBuilder(2)
    spec = Axis1LocalLindbladContextSpec(gamma_1_per_ns=1e-3)
    assert b.declare_axis1_local_lindblad_context(spec) is b
    ir = b.build()
    assert ir.metadata["axis1_local_lindblad_context"] == spec.to_manifest()
    assert ir.metadata["axis1_local_lindblad_context"]["gamma_1_per_ns"] == 1e-3


def test_L0_declare_axis1_context_trivial_pops():
    b = CircuitBuilder(2)
    b.declare_axis1_local_lindblad_context(Axis1LocalLindbladContextSpec())  # trivial -> pop (absent)
    ir = b.build()
    assert "axis1_local_lindblad_context" not in ir.metadata


def test_L0_declare_axis1_context_pop_removes_prior():
    b = CircuitBuilder(2)
    b.declare_axis1_local_lindblad_context(Axis1LocalLindbladContextSpec(gamma_1_per_ns=1e-3))
    assert "axis1_local_lindblad_context" in b._metadata
    b.declare_axis1_local_lindblad_context(Axis1LocalLindbladContextSpec())  # trivial -> pop removes
    assert "axis1_local_lindblad_context" not in b._metadata


# =========================================================================== #
# CircuitBuilder.__init__ guard + build                                         #
# =========================================================================== #
def test_L0_builder_num_qubits_positive_guard_and_int_coercion():
    _raises_exact(ValueError, "num_qubits must be positive", lambda: CircuitBuilder(0))
    _raises_exact(ValueError, "num_qubits must be positive", lambda: CircuitBuilder(-3))
    assert CircuitBuilder(3.5).num_qubits == 3            # int() coercion in __init__


def test_L0_build_copies_steps_and_metadata():
    b = CircuitBuilder(2, metadata={"foo": 1})
    b.h(0).tick()
    ir = b.build()
    assert isinstance(ir, CircuitIR)
    assert ir.num_qubits == 2
    assert _views(ir) == [("G", "H", (0,), ()), ("T",)]
    assert ir.metadata == {"foo": 1}
    # build SNAPSHOTS: further builder mutation does NOT leak into the built IR
    b.x(1)
    assert _views(ir) == [("G", "H", (0,), ()), ("T",)]   # tuple(self._steps) copied
    b._metadata["bar"] = 2
    assert "bar" not in ir.metadata                        # dict(self._metadata) copied


# =========================================================================== #
# L1 property (Hypothesis) -- normalization + record-schema invariants          #
# =========================================================================== #
@settings(max_examples=100, deadline=None)
@given(name=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122),
                    min_size=1, max_size=5),
       nt=st.integers(0, 4))
def test_L1_gateop_name_always_uppercase(name, nt):
    op = GateOp(name, tuple(range(nt)))
    assert op.name == name.upper()
    assert op.targets == tuple(range(nt))
    assert all(type(t) is int for t in op.targets)


@settings(max_examples=75, deadline=None)
@given(keys=st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=5, unique=True))
def test_L1_measurement_keys_matches_independent_extraction(keys):
    n = len(keys)
    b = CircuitBuilder(n)
    b.measure(list(range(n)), key=list(keys))
    ir = b.build()
    # the property returns exactly the (ordered) keys the builder recorded
    assert ir.measurement_keys == tuple(keys)

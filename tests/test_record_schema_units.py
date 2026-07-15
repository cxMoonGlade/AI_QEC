"""Stage-D batch ``record_schema`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.record_schema`` (10 CPU-pure public units: the two
``RecordSchema`` classmethods ``from_stim``/``from_circuit_ir``, the two width properties
``detector_bit_width``/``observable_bit_width``, ``RecordSchema.to_manifest``, and the five
module-level guards ``require_frontend_representability``/``require_stim_circuit``/
``require_matching_schemas``/``validate_evaluator_sidecars``/``b8_manifest_entry``; no
torch, no quimb -- ``stim`` is a lazy import inside ``require_stim_circuit`` -- so
out_of_scope is empty).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4;
work-list docs/SIMULATOR.md D20).
``frontend/record_schema.py`` owns the detector/observable RECORD-SCHEMA + manifest guards
carried alongside each compiled Stim circuit: ``RecordSchema`` (a frozen carrier built
either from a stim.Circuit's counts or from a CircuitIR blended with a stim circuit) and
the frontend representability / stim-type / matching-schema / evaluator-only-sidecar /
b8-manifest guards.

L2 DISCIPLINE (100% coverage != discrimination). Every schema field is pinned to its EXACT
value vs an INDEPENDENT extraction: the counts are read straight off the ``stim.Circuit``
(``.num_qubits``/``.num_measurements``/``.num_detectors``/``.num_observables``), the names
off the ``CircuitIR``'s own ``measurement_keys``/``detector_names``/``observable_names`` --
NEVER RecordSchema's own accessors. ``from_circuit_ir`` is fed a stim circuit whose counts
(m=3,d=2,o=1) DIFFER from the IR's name-lists (mkeys=['m0'], det=[], obs=[]) so the blend
is load-bearing. Every RAISING guard is tripped through EVERY route reaching it with the
EXACT message via ``assert_raises_exact`` (kills the string wrap/case/None message mutants a
substring ``match=`` leaves surviving), AND its happy path is pinned. The
``validate_evaluator_sidecars`` second guard ``"name" not in item or "path" not in item`` is
tripped via BOTH operands (missing-name-only and missing-path-only), which is what kills the
``or``->``and`` mutant. ``b8_manifest_entry``'s ``(bits+7)//8`` arithmetic is pinned by an L1
property vs ``math.ceil(bits/8)`` over many bits.
"""
from __future__ import annotations

import math

import pytest
import stim
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins, assert_raises_exact
from _support.fixtures import canonical_circuit_ir, canonical_stim_circuit

from error_coupling_simulator.frontend.record_schema import (
    RecordSchema,
    b8_manifest_entry,
    require_frontend_representability,
    require_matching_schemas,
    require_stim_circuit,
    validate_evaluator_sidecars,
)


# --------------------------------------------------------------------------- #
# INDEPENDENT builders: hand stim circuits with KNOWN counts (read straight    #
# off the stim.Circuit, NOT via RecordSchema).                                 #
# --------------------------------------------------------------------------- #
def _rec(i):
    return stim.target_rec(i)


def _blend_stim_circuit() -> stim.Circuit:
    """A 3-qubit stim circuit with DISTINCT counts m=3, d=2, o=1 (all different from each
    other and from the IR's name-lists), so from_circuit_ir's stim-counts vs IR-names blend
    is load-bearing."""
    c = stim.Circuit()
    for q in range(3):
        c.append("QUBIT_COORDS", [q], [float(q)])
    c.append("H", [0])
    c.append("M", [0, 1, 2])           # 3 measurements
    c.append("DETECTOR", [_rec(-1)])   # 2 detectors
    c.append("DETECTOR", [_rec(-2)])
    c.append("OBSERVABLE_INCLUDE", [_rec(-3)], 0)  # 1 observable
    return c


def _five_qubit_stim_circuit() -> stim.Circuit:
    """A stim circuit whose num_qubits (5) differs from the canonical IR's (3) -> trips the
    from_circuit_ir mismatch raise."""
    c = stim.Circuit()
    c.append("H", [4])
    return c


def _stim_counts(circuit):
    """INDEPENDENT count extraction straight off a stim.Circuit (not via RecordSchema)."""
    return (int(circuit.num_qubits), int(circuit.num_measurements),
            int(circuit.num_detectors), int(circuit.num_observables))


# =========================================================================== #
# RecordSchema.from_stim                                                        #
# =========================================================================== #
def test_L0_from_stim_pins_counts_vs_independent_stim_extraction():
    c = canonical_stim_circuit()
    nq, nm, nd, no = _stim_counts(c)   # INDEPENDENT: read off the stim.Circuit
    assert (nq, nm, nd, no) == (2, 2, 1, 0)
    s = RecordSchema.from_stim(c)
    # every count field pinned to the independent extraction
    assert (s.num_qubits, s.num_measurements, s.num_detectors, s.num_observables) == (
        nq, nm, nd, no)
    # from_stim leaves the NAME tuples empty (counts-only construction)
    assert s.measurement_keys == () and s.detector_names == () and s.observable_names == ()

    def prop(schema):
        assert (schema.num_qubits, schema.num_measurements, schema.num_detectors,
                schema.num_observables) == (nq, nm, nd, no)

    wrong = RecordSchema(num_qubits=nq, num_measurements=nm, num_detectors=nd + 1,
                         num_observables=no)  # a single wrong count must fail the pin
    assert_discriminates(prop, s, wrong, label="RecordSchema.from_stim counts")


# =========================================================================== #
# RecordSchema.from_circuit_ir                                                  #
# =========================================================================== #
def test_L0_from_circuit_ir_blends_stim_counts_with_ir_names():
    ir = canonical_circuit_ir()
    sc = _blend_stim_circuit()
    nq, nm, nd, no = _stim_counts(sc)            # counts from the stim circuit
    assert (nq, nm, nd, no) == (3, 3, 2, 1)
    assert int(ir.num_qubits) == nq              # match route: no raise
    s = RecordSchema.from_circuit_ir(ir, sc)

    # counts come from the STIM circuit ...
    assert (s.num_qubits, s.num_measurements, s.num_detectors, s.num_observables) == (
        nq, nm, nd, no)
    # ... and the NAME tuples come from the CircuitIR (INDEPENDENT: ir's own accessors),
    # which DIFFER from the stim counts (mkeys has 1 entry but num_measurements=3, etc.),
    # so the blend source is discriminated.
    assert s.measurement_keys == tuple(ir.measurement_keys) == ("m0",)
    assert s.detector_names == tuple(ir.detector_names) == ()
    assert s.observable_names == tuple(ir.observable_names) == ()

    # exact manifest pin (independent literal)
    assert s.to_manifest() == {
        "num_qubits": 3, "num_measurements": 3, "num_detectors": 2, "num_observables": 1,
        "detector_bit_width": 2, "observable_bit_width": 1,
        "measurement_keys": ["m0"], "detector_names": [], "observable_names": []}

    def prop(schema):
        assert schema.measurement_keys == ("m0",) and schema.num_detectors == 2

    wrong = RecordSchema(num_qubits=3, num_measurements=3, num_detectors=2,
                         num_observables=1, measurement_keys=("WRONG",))
    assert_discriminates(prop, s, wrong, label="from_circuit_ir blend")


def test_L0_from_circuit_ir_num_qubits_mismatch_raises_exact():
    ir = canonical_circuit_ir()                  # declares 3 qubits
    sc5 = _five_qubit_stim_circuit()             # uses 5 qubits
    assert int(sc5.num_qubits) == 5 and int(ir.num_qubits) == 3
    assert_raises_exact(
        ValueError,
        "Stim circuit uses 5 qubits, but CircuitIR declares 3",
        lambda: RecordSchema.from_circuit_ir(ir, sc5),
        label="from_circuit_ir qubit mismatch")


# =========================================================================== #
# RecordSchema.detector_bit_width / observable_bit_width                        #
# =========================================================================== #
def _hand_schema() -> RecordSchema:
    """A hand schema with DISTINCT field values (num_detectors=3 != num_observables=2) so
    the two width properties are individually discriminated, and non-empty name tuples so
    to_manifest's list() coercions are load-bearing."""
    return RecordSchema(
        num_qubits=5, num_measurements=4, num_detectors=3, num_observables=2,
        measurement_keys=("m0", "m1"), detector_names=("d0",),
        observable_names=("L0", "L1", "L2"))


def test_L0_detector_bit_width_pins_num_detectors():
    s = _hand_schema()
    assert s.detector_bit_width == s.num_detectors == 3

    def prop(schema):
        assert schema.detector_bit_width == 3

    # a schema whose num_detectors differs must fail -> proves the property tracks num_detectors
    wrong = RecordSchema(num_qubits=5, num_measurements=4, num_detectors=2, num_observables=2)
    assert_discriminates(prop, s, wrong, label="detector_bit_width")


def test_L0_observable_bit_width_pins_num_observables():
    s = _hand_schema()
    assert s.observable_bit_width == s.num_observables == 2
    # distinct from detector_bit_width(3): proves the two properties do not alias
    assert s.observable_bit_width != s.detector_bit_width

    def prop(schema):
        assert schema.observable_bit_width == 2

    wrong = RecordSchema(num_qubits=5, num_measurements=4, num_detectors=3, num_observables=1)
    assert_discriminates(prop, s, wrong, label="observable_bit_width")


# =========================================================================== #
# RecordSchema.to_manifest                                                      #
# =========================================================================== #
def test_L0_to_manifest_exact_dict():
    s = _hand_schema()
    expected = {
        "num_qubits": 5, "num_measurements": 4, "num_detectors": 3, "num_observables": 2,
        "detector_bit_width": 3, "observable_bit_width": 2,
        "measurement_keys": ["m0", "m1"], "detector_names": ["d0"],
        "observable_names": ["L0", "L1", "L2"]}
    got = s.to_manifest()
    assert got == expected
    # keys/detector/observable names coerced to LISTS (pins the list(...) coercions)
    assert type(got["measurement_keys"]) is list
    assert type(got["detector_names"]) is list
    assert type(got["observable_names"]) is list

    def prop(m):
        assert m == expected

    wrong = dict(expected, num_detectors=99)  # a single field drift must fail
    assert_discriminates(prop, got, wrong, label="RecordSchema.to_manifest")


# =========================================================================== #
# require_frontend_representability                                             #
# =========================================================================== #
def test_L0_require_frontend_representability_happy_returns_none():
    # both guards pass -> None (no raise); pins the all-valid arc of both ifs
    assert require_frontend_representability(backend="stim", representability="stim_pauli") is None


def test_L0_require_frontend_representability_bad_backend_raises_exact():
    # backend guard trips first (representability is valid, proving guard-1 fires on its own)
    assert_raises_exact(
        ValueError,
        "unsupported simulator backend 'mps'; allowed=['stim']",
        lambda: require_frontend_representability(backend="mps", representability="stim_pauli"),
        label="representability backend guard")


def test_L0_require_frontend_representability_bad_representability_raises_exact():
    # representability guard is ONLY reachable with a VALID backend -- trip it exactly that
    # way (never masked by the backend guard).
    assert_raises_exact(
        ValueError,
        "unsupported frontend representability 'foo'; allowed=['stim_pauli']",
        lambda: require_frontend_representability(backend="stim", representability="foo"),
        label="representability class guard")


# =========================================================================== #
# require_stim_circuit                                                          #
# =========================================================================== #
def test_L0_require_stim_circuit_returns_identity_on_stim():
    c = canonical_stim_circuit()
    out = require_stim_circuit(c, label="ideal")
    assert out is c   # identity return (happy path)


def test_L0_require_stim_circuit_rejects_non_stim_exact():
    # a str is not a stim.Circuit -> TypeError with the exact type-repr in the message
    assert_raises_exact(
        TypeError,
        "ideal must be stim.Circuit, got <class 'str'>",
        lambda: require_stim_circuit("not a circuit", label="ideal"),
        label="require_stim_circuit type guard")
    # a different (non-str, non-Sequence) value also trips it with its own type repr
    assert_raises_exact(
        TypeError,
        "noisy must be stim.Circuit, got <class 'int'>",
        lambda: require_stim_circuit(7, label="noisy"),
        label="require_stim_circuit type guard int")


# =========================================================================== #
# require_matching_schemas                                                      #
# =========================================================================== #
def test_L0_require_matching_schemas_identical_returns_noisy():
    ideal = canonical_stim_circuit()
    noisy = canonical_stim_circuit()             # identical schema
    out = require_matching_schemas(ideal, noisy)
    # returns a schema equal to from_stim(noisy) (INDEPENDENT recompute)
    assert out == RecordSchema.from_stim(noisy)
    assert (out.num_qubits, out.num_measurements, out.num_detectors, out.num_observables) == (
        2, 2, 1, 0)


def test_L0_require_matching_schemas_mismatch_raises_exact():
    ideal = canonical_stim_circuit()             # num_qubits=2
    noisy = canonical_stim_circuit()
    noisy.append("QUBIT_COORDS", [2], [2.0, 0.0])  # num_qubits=3 -> schemas differ
    # INDEPENDENT hand-built manifests (the message interpolates each schema's to_manifest);
    # they differ ONLY in num_qubits (2 vs 3).
    _base = {
        "num_measurements": 2, "num_detectors": 1, "num_observables": 0,
        "detector_bit_width": 1, "observable_bit_width": 0,
        "measurement_keys": [], "detector_names": [], "observable_names": []}
    manifest_ideal = {"num_qubits": 2, **_base}
    manifest_noisy = {"num_qubits": 3, **_base}
    expected = ("ideal/noisy Stim circuits must have identical record schema; "
                f"ideal={manifest_ideal} noisy={manifest_noisy}")
    assert_raises_exact(ValueError, expected,
                        lambda: require_matching_schemas(ideal, noisy),
                        label="require_matching_schemas mismatch")


# =========================================================================== #
# validate_evaluator_sidecars (ISOLATION-CONTRACT: evaluator-only gate)         #
# =========================================================================== #
def test_L0_validate_evaluator_sidecars_valid_returns_copies():
    raw = {"visibility": "evaluator_only", "name": "truth_A", "path": "/x/a.json", "extra": 1}
    out = validate_evaluator_sidecars((raw,))
    assert out == (raw,)
    assert isinstance(out, tuple) and len(out) == 1
    # dict(raw) makes a COPY -- the validated item is not the same object as the input
    assert out[0] is not raw
    # two valid sidecars -> both pass through in order
    raw2 = {"visibility": "evaluator_only", "name": "truth_B", "path": "/x/b.json"}
    assert validate_evaluator_sidecars((raw, raw2)) == (raw, raw2)


def test_L0_validate_evaluator_sidecars_bad_visibility_raises_exact():
    # explicit non-'evaluator_only' visibility -> first guard fires (exact message with item repr)
    assert_raises_exact(
        ValueError,
        "truth sidecars must be marked visibility='evaluator_only'; "
        "got {'visibility': 'public', 'name': 'n', 'path': 'p'}",
        lambda: validate_evaluator_sidecars(({"visibility": "public", "name": "n", "path": "p"},)),
        label="sidecar visibility guard")
    # a MISSING visibility key (a non-str default route: .get returns None) also trips it
    assert_raises_exact(
        ValueError,
        "truth sidecars must be marked visibility='evaluator_only'; "
        "got {'name': 'n', 'path': 'p'}",
        lambda: validate_evaluator_sidecars(({"name": "n", "path": "p"},)),
        label="sidecar visibility missing-key")


def test_L0_validate_evaluator_sidecars_missing_name_raises_exact():
    # valid visibility, HAS path, MISSING name -> trips the FIRST operand of the `or` guard.
    assert_raises_exact(
        ValueError,
        "truth sidecar needs name and path: {'visibility': 'evaluator_only', 'path': 'p'}",
        lambda: validate_evaluator_sidecars(({"visibility": "evaluator_only", "path": "p"},)),
        label="sidecar missing-name guard")


def test_L0_validate_evaluator_sidecars_missing_path_raises_exact():
    # valid visibility, HAS name, MISSING path -> trips the SECOND operand of the `or` guard.
    # (missing-name + missing-path together kill the `or`->`and` mutant: each trips the raise
    # in the original but NOT under `and`.)
    assert_raises_exact(
        ValueError,
        "truth sidecar needs name and path: {'visibility': 'evaluator_only', 'name': 'n'}",
        lambda: validate_evaluator_sidecars(({"visibility": "evaluator_only", "name": "n"},)),
        label="sidecar missing-path guard")


# =========================================================================== #
# b8_manifest_entry                                                             #
# =========================================================================== #
def test_L0_b8_manifest_entry_negative_raises_exact():
    assert_raises_exact(
        ValueError,
        "bits_per_shot must be non-negative, got -3",
        lambda: b8_manifest_entry("f.b8", bits_per_shot=-3),
        label="b8 negative guard")


def test_L0_b8_manifest_entry_zero_bit_width_omits():
    assert b8_manifest_entry("f.b8", bits_per_shot=0) == {
        "file": None, "bits_per_shot": 0, "packed_bytes_per_shot": 0,
        "omitted_reason": "zero_bit_width"}


def test_L0_b8_manifest_entry_normal_dict_exact():
    # bits=10 -> packed=(10+7)//8=2 ; distinguishes //8 from //9 (17//9=1) and float // (17/8=2.125)
    assert b8_manifest_entry("f.b8", bits_per_shot=10) == {
        "file": "f.b8", "bits_per_shot": 10, "packed_bytes_per_shot": 2}
    # bits=8 -> packed=15//8=1 ; distinguishes 7->8 (16//8=2) and +7->-7 (1//8=0)
    assert b8_manifest_entry("f.b8", bits_per_shot=8) == {
        "file": "f.b8", "bits_per_shot": 8, "packed_bytes_per_shot": 1}
    # bits=1 -> packed=8//8=1 ; +7->-7 gives -6//8=-1
    assert b8_manifest_entry("data.b8", bits_per_shot=1) == {
        "file": "data.b8", "bits_per_shot": 1, "packed_bytes_per_shot": 1}
    # int() coercion on a float bits_per_shot: bits becomes 10 (int), packed=2
    got = b8_manifest_entry("f.b8", bits_per_shot=10.0)
    assert got == {"file": "f.b8", "bits_per_shot": 10, "packed_bytes_per_shot": 2}
    assert type(got["bits_per_shot"]) is int

    def prop(d):
        assert d["packed_bytes_per_shot"] == 2

    wrong = {"file": "f.b8", "bits_per_shot": 10, "packed_bytes_per_shot": 3}
    assert_discriminates(prop, b8_manifest_entry("f.b8", bits_per_shot=10), wrong,
                         label="b8 packed_bytes")


# =========================================================================== #
# L1 property (Hypothesis)                                                       #
# =========================================================================== #
@settings(max_examples=200, deadline=None)
@given(bits=st.integers(min_value=1, max_value=4096))
def test_L1_b8_packed_bytes_matches_ceil_div8(bits):
    entry = b8_manifest_entry("f.b8", bits_per_shot=bits)
    # INDEPENDENT recompute: ceil(bits/8) (NOT the module's (bits+7)//8 expression)
    assert entry["packed_bytes_per_shot"] == math.ceil(bits / 8)
    assert entry["file"] == "f.b8"
    assert entry["bits_per_shot"] == bits
    assert "omitted_reason" not in entry


@settings(max_examples=100, deadline=None)
@given(nq=st.integers(0, 30), nm=st.integers(0, 30), nd=st.integers(0, 30),
       no=st.integers(0, 30))
def test_L1_record_schema_widths_and_manifest_shape(nq, nm, nd, no):
    s = RecordSchema(num_qubits=nq, num_measurements=nm, num_detectors=nd, num_observables=no)
    # widths ARE the corresponding counts (INDEPENDENT recompute)
    assert s.detector_bit_width == nd
    assert s.observable_bit_width == no
    m = s.to_manifest()
    assert m["detector_bit_width"] == nd and m["observable_bit_width"] == no
    assert set(m) == {
        "num_qubits", "num_measurements", "num_detectors", "num_observables",
        "detector_bit_width", "observable_bit_width",
        "measurement_keys", "detector_names", "observable_names"}


@settings(max_examples=100, deadline=None)
@given(names=st.lists(st.text(min_size=1, max_size=4), min_size=0, max_size=5))
def test_L1_validate_evaluator_sidecars_passes_valid_and_copies(names):
    sidecars = tuple(
        {"visibility": "evaluator_only", "name": n, "path": f"/p/{n}"} for n in names)
    out = validate_evaluator_sidecars(sidecars)
    assert out == sidecars
    # each validated item is a distinct copy of its input
    for original, validated in zip(sidecars, out):
        assert validated == original and validated is not original

"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.code_spec`` (17 CPU-pure public units: the five
frozen syndrome-code dataclasses' ``__post_init__`` + ``to_manifest``,
``Axis1StaticZZDeviceSpec.to_metadata``, ``CodeSpec.to_manifest`` + the three
properties ``data_indices``/``ancilla_indices``/``operation_set``, and the Pauli-algebra
function ``commute``; no torch, no quimb, so out_of_scope is empty).

Current coverage contract: docs/SIMULATOR.md SS12.3/12.4.
``frontend/code_spec.py`` owns the syndrome-code construction contract the frontend
compiler consumes: ``CodeQubit``/``PauliTerm``/``StabilizerCheck``/
``LogicalObservableSpec``/``Axis1StaticZZDeviceSpec`` (each with a load-bearing
``__post_init__`` that coerces + validates), the ``CodeSpec`` container, and ``commute``.

L2 DISCIPLINE (100% coverage != discrimination). THE LOAD-BEARING PART is the
``commute`` Pauli-algebra: it is pinned against an INDEPENDENT symplectic recompute
(X=(1,0), Y=(1,1), Z=(0,1); two Pauli products commute iff the symplectic inner product
over shared support is EVEN -- NOT the module's own count-differing-bases expression)
over a FULL enumerated truth table PLUS a Hypothesis property, with an
``assert_discriminates`` variant that flips ONE factor's basis so the parity flips.
``data_indices``/``ancilla_indices``/``operation_set`` are pinned vs an INDEPENDENT
partition computed from the constructed inputs (NOT the module's property). Every
``to_manifest``/``to_metadata`` is pinned to its EXACT dict, and every validation raise
is tripped through EVERY route reaching it with the EXACT message via
``str(excinfo.value)==...``.

``PauliTerm.__post_init__`` upper-cases ``basis`` (source:
``object.__setattr__(self, "basis", str(self.basis).upper())``), so a lowercase-basis
CASE literal a callee normalizes is EQUIVALENT while a WRAP mutant is killable -- the
tests feed lowercase input and pin the upper-cased result to make ``.upper()``
load-bearing. Numeric/coords coercions (``int``/``float``/``str``) are made observable by
feeding non-canonical typed inputs and pinning the coerced TYPE (kills the
``object.__setattr__(self, "<field>", ...)`` attribute-name string mutants).

The private helpers (``_as_terms``/``_require_unique_term_qubits``/
``_require_record_token``/``_pairs``/``_pauli_vector``/
``_pauli_product_in_stabilizer_span``/``_binary_row_rank`` + ``CodeSpec._validate_*``)
are not scored units but ARE exercised + mutation-covered through the public construction
paths: ``_pauli_vector`` runs X/Y/Z terms through BOTH set-membership arcs (a rich valid
spec routes an X logical, a Y logical, and Z checks), and the GF(2) stabilizer-span check
is exercised BOTH ways -- a valid spec whose logicals are NOT in span AND two in-span
specs (a single-check logical and a PRODUCT-OF-TWO-CHECKS logical Z0Z2 = z0 XOR z1 that
forces the multi-row XOR elimination).
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins

from error_coupling_simulator.frontend.code_spec import (
    Axis1StaticZZDeviceSpec,
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
    commute,
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


def _P(q, b):
    return PauliTerm(q, b)


# INDEPENDENT symplectic commute reference. X=(x,z)=(1,0); Y=(1,1); Z=(0,1). Two Pauli
# products commute iff sum over shared support of (x_a z_b + z_a x_b) is EVEN. This is the
# STANDARD symplectic-form definition, computed here from scratch -- NOT the module's
# "count qubits where the basis differs" expression.
_XZ = {"X": (1, 0), "Y": (1, 1), "Z": (0, 1)}


def _symplectic_commute(a_terms, b_terms) -> bool:
    a = {t.qubit: t.basis for t in a_terms}
    b = {t.qubit: t.basis for t in b_terms}
    s = 0
    for q in set(a) & set(b):
        xa, za = _XZ[a[q]]
        xb, zb = _XZ[b[q]]
        s += xa * zb + za * xb
    return s % 2 == 0


# --------------------------------------------------------------------------- #
# CodeSpec fixtures                                                             #
# --------------------------------------------------------------------------- #
def _valid_rep_spec(rounds: int = 3) -> CodeSpec:
    """A clean d=3 Z-memory repetition code (all-Z checks/logical) for the manifest +
    property pins. checks z0=Z0Z1 (anc3), z1=Z1Z2 (anc4); logical LZ=Z0."""
    return CodeSpec(
        name="rep3z",
        num_qubits=5,
        data_qubits=(CodeQubit(0, "data", (0.0,)), CodeQubit(1, "data", (1.0,)),
                     CodeQubit(2, "data", (2.0,))),
        ancilla_qubits=(CodeQubit(3, "ancilla"), CodeQubit(4, "ancilla")),
        checks=(
            StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z")), (0.5,)),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z")), (1.5,)),
        ),
        logical_observables=(LogicalObservableSpec("LZ", (PauliTerm(0, "Z"),), index=0),),
        rounds=rounds,
    )


def _rich_valid_spec() -> CodeSpec:
    """A VALID spec that routes X, Y AND Z terms through ``_pauli_vector`` so both
    set-membership arcs ({'X','Y'} and {'Z','Y'}) are load-bearing: Z checks z0=Z0Z1,
    z1=Z1Z2 plus three logicals LZ=Z0 (Z), LX=X3 (X), LY=Y4 (Y), each commuting with the
    checks and NOT in the (Z-only) stabilizer span."""
    return CodeSpec(
        name="rich",
        num_qubits=7,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data"), CodeQubit(2, "data"),
                     CodeQubit(3, "data"), CodeQubit(4, "data")),
        ancilla_qubits=(CodeQubit(5, "ancilla"), CodeQubit(6, "ancilla")),
        checks=(
            StabilizerCheck("z0", 5, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),
            StabilizerCheck("z1", 6, (PauliTerm(1, "Z"), PauliTerm(2, "Z"))),
        ),
        logical_observables=(
            LogicalObservableSpec("LZ", (PauliTerm(0, "Z"),), index=0),
            LogicalObservableSpec("LX", (PauliTerm(3, "X"),), index=1),
            LogicalObservableSpec("LY", (PauliTerm(4, "Y"),), index=2),
        ),
        rounds=2,
    )


def _rep_spec_with(**overrides) -> CodeSpec:
    """Build a valid rep-code spec, overriding one field, so a single guard is tripped
    while the earlier guards pass (RAISING-GUARD ROUTE coverage)."""
    base = dict(
        name="c",
        num_qubits=5,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data"), CodeQubit(2, "data")),
        ancilla_qubits=(CodeQubit(3, "ancilla"), CodeQubit(4, "ancilla")),
        checks=(
            StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z"))),
        ),
        logical_observables=(LogicalObservableSpec("LZ", (PauliTerm(0, "Z"),), index=0),),
        rounds=2,
    )
    base.update(overrides)
    return CodeSpec(**base)


# =========================================================================== #
# commute -- the Pauli-algebra parity function (THE LOAD-BEARING UNIT)          #
# =========================================================================== #
# (a_terms, b_terms, expected) truth table -- single/multi/disjoint/empty/Y, and every
# expected value re-derived by the INDEPENDENT symplectic reference below.
_COMMUTE_CASES = [
    ((_P(0, "X"),), (_P(0, "Z"),), False),                       # single anti
    ((_P(0, "X"),), (_P(0, "X"),), True),                        # single same
    ((_P(0, "X"),), (_P(0, "Y"),), False),                       # X vs Y differ -> anti
    ((_P(0, "Y"),), (_P(0, "Z"),), False),                       # Y vs Z differ -> anti
    ((_P(0, "X"), _P(1, "X")), (_P(0, "Z"), _P(1, "Z")), True),  # two anti -> even
    ((_P(0, "X"),), (_P(0, "Z"), _P(1, "Z")), False),            # one anti (shared q0)
    ((_P(0, "X"),), (_P(0, "X"), _P(1, "Z")), True),             # zero anti on shared q0
    ((_P(0, "X"),), (_P(1, "Z"),), True),                        # disjoint support
    ((), (), True),                                              # both empty
    ((_P(0, "X"), _P(1, "X"), _P(2, "X")), (_P(0, "Z"), _P(1, "Z")), True),   # two anti
    ((_P(0, "X"), _P(1, "X"), _P(2, "X")), (_P(0, "Z"),), False),             # one anti
    ((_P(0, "Y"), _P(1, "Y")), (_P(0, "Y"), _P(1, "Y")), True),  # Y self -> commute
    ((_P(0, "Y"), _P(1, "Y")), (_P(0, "X"), _P(1, "Z")), True),  # both differ -> even
    ((_P(0, "Z"), _P(1, "Z")), (_P(1, "Z"), _P(2, "Z")), True),  # rep-code checks
]


def test_L0_commute_full_truth_table_vs_symplectic():
    module = {}
    reference = {}
    for i, (a, b, exp) in enumerate(_COMMUTE_CASES):
        got = commute(a, b)
        ref = _symplectic_commute(a, b)
        assert ref == exp, f"case {i}: bad hand-labelled expectation"     # sanity on the table
        module[i] = got
        reference[i] = ref
    # pin the WHOLE truth table (module output) to the INDEPENDENT symplectic recompute.
    assert_pins(module, reference, label="commute vs symplectic")
    # explicit per-case equality too (crisp failure locus under mutation)
    for i, (a, b, exp) in enumerate(_COMMUTE_CASES):
        assert commute(a, b) is exp, f"case {i}: commute {commute(a, b)} != {exp}"


def test_L0_commute_discriminates_single_factor_flip():
    """KILLER: flipping ONE factor's basis flips the parity, so the verdict flips. A mutant
    that changes the anticommute rule / the parity test cannot pass BOTH."""
    x0x1 = (_P(0, "X"), _P(1, "X"))

    def prop(pair):
        assert commute(pair[0], pair[1]) is True

    real = (x0x1, (_P(0, "Z"), _P(1, "Z")))   # 2 anti -> even -> commute True
    wrong = (x0x1, (_P(0, "Z"), _P(1, "X")))  # 1 anti (q1 X==X same) -> odd -> False
    assert_discriminates(prop, real, wrong, label="commute parity")


@settings(max_examples=200, deadline=None)
@given(
    a=st.lists(st.tuples(st.integers(0, 5), st.sampled_from(["X", "Y", "Z"])),
               min_size=0, max_size=6, unique_by=lambda t: t[0]),
    b=st.lists(st.tuples(st.integers(0, 5), st.sampled_from(["X", "Y", "Z"])),
               min_size=0, max_size=6, unique_by=lambda t: t[0]),
)
def test_L1_commute_matches_symplectic_reference(a, b):
    at = tuple(_P(q, base) for q, base in a)
    bt = tuple(_P(q, base) for q, base in b)
    assert commute(at, bt) == _symplectic_commute(at, bt)


# =========================================================================== #
# CodeQubit.__post_init__ + to_manifest                                        #
# =========================================================================== #
def test_L0_code_qubit_valid_and_coercion():
    # non-empty coords (generator body runs) + INT coords -> FLOAT coercion is observable.
    q = CodeQubit(index=2.0, role="data", coords=(1, 2))
    assert q.index == 2 and type(q.index) is int          # int() coercion of a float index
    assert q.coords == (1.0, 2.0)
    assert all(type(c) is float for c in q.coords)         # float() coercion of int coords
    assert q.role == "data"
    # empty coords (generator body does NOT run) -- the empty-coords arc
    q0 = CodeQubit(3, "ancilla")
    assert q0.coords == ()


def test_L0_code_qubit_guards():
    _raises_exact(ValueError, "qubit index must be non-negative, got -1",
                  lambda: CodeQubit(-1, "data"))
    _raises_exact(ValueError, "qubit role must be 'data' or 'ancilla', got 'bogus'",
                  lambda: CodeQubit(0, "bogus"))


def test_L0_code_qubit_to_manifest_exact_dict():
    q = CodeQubit(0, "data", (0.5, 1.5))
    expected = {"index": 0, "role": "data", "coords": [0.5, 1.5]}
    got = q.to_manifest()
    assert got == expected
    assert type(got["coords"]) is list                     # coords coerced to a list
    # default coords=() -> []
    assert CodeQubit(4, "ancilla").to_manifest() == {"index": 4, "role": "ancilla", "coords": []}

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, dict(expected, role="ancilla"),
                         label="CodeQubit.to_manifest")


# =========================================================================== #
# PauliTerm.__post_init__ + to_manifest                                        #
# =========================================================================== #
def test_L0_pauli_term_valid_upper_and_coercion():
    # lowercase basis -> .upper() makes it 'X' (basis CASE normalization is load-bearing:
    # if .upper() / the 'basis' setattr is dropped, 'x' is NOT in _PAULI_BASES -> raises).
    t = PauliTerm(qubit=2.0, basis="x")
    assert t.basis == "X"
    assert t.qubit == 2 and type(t.qubit) is int            # int() coercion of a float qubit
    # every accepted basis (kills a _PAULI_BASES set-element drop)
    assert PauliTerm(0, "x").basis == "X"
    assert PauliTerm(0, "y").basis == "Y"
    assert PauliTerm(0, "z").basis == "Z"


def test_L0_pauli_term_guards():
    _raises_exact(ValueError, "PauliTerm qubit must be non-negative, got -1",
                  lambda: PauliTerm(-1, "X"))
    _raises_exact(ValueError, "unsupported Pauli basis 'W'",
                  lambda: PauliTerm(0, "W"))


def test_L0_pauli_term_to_manifest_exact_dict():
    t = PauliTerm(3, "Y")
    expected = {"qubit": 3, "basis": "Y"}
    got = t.to_manifest()
    assert got == expected

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, dict(expected, basis="X"), label="PauliTerm.to_manifest")


# =========================================================================== #
# StabilizerCheck.__post_init__ + to_manifest                                  #
# =========================================================================== #
def test_L0_stabilizer_check_valid_and_coercion():
    # int name -> str() coercion observable; int coords -> float() coercion; non-empty coords.
    c = StabilizerCheck(name=0, ancilla=2.0, terms=(PauliTerm(0, "Z"), PauliTerm(1, "Z")),
                        coords=(1, 2))
    assert c.name == "0" and type(c.name) is str
    assert c.ancilla == 2 and type(c.ancilla) is int
    assert c.coords == (1.0, 2.0) and all(type(x) is float for x in c.coords)
    # default empty coords arc
    assert StabilizerCheck("z", 3, (PauliTerm(0, "Z"),)).coords == ()


def test_L0_stabilizer_check_guards():
    _raises_exact(ValueError, "stabilizer check name must be non-empty",
                  lambda: StabilizerCheck("", 3, (PauliTerm(0, "Z"),)))
    _raises_exact(
        ValueError,
        "stabilizer check name 'z:0' must match '[A-Za-z0-9_.-]+'; avoid ':' and whitespace "
        "so generated record keys stay parseable",
        lambda: StabilizerCheck("z:0", 3, (PauliTerm(0, "Z"),)))
    _raises_exact(ValueError, "stabilizer ancilla must be non-negative, got -1",
                  lambda: StabilizerCheck("z0", -1, (PauliTerm(0, "Z"),)))
    _raises_exact(ValueError, "stabilizer check 'z0' must have at least one term",
                  lambda: StabilizerCheck("z0", 3, ()))
    _raises_exact(ValueError, "'z0' has duplicate term qubit 0",
                  lambda: StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), PauliTerm(0, "X"))))
    # MIXED terms (one PauliTerm + one non-PauliTerm) -> _as_terms all()-guard TypeError
    # (mixed input kills an all()->any() mutant that a wholly-invalid input would let pass).
    _raises_exact(TypeError, "terms must be PauliTerm instances",
                  lambda: StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), object())))


def test_L0_stabilizer_check_to_manifest_exact_dict():
    c = StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z")), (0.5, 1.0))
    expected = {
        "name": "z0", "ancilla": 3, "coords": [0.5, 1.0],
        "terms": [{"qubit": 0, "basis": "Z"}, {"qubit": 1, "basis": "Z"}]}
    got = c.to_manifest()
    assert got == expected
    assert type(got["coords"]) is list and type(got["terms"]) is list
    # empty-coords arc -> []
    assert StabilizerCheck("z1", 4, (PauliTerm(2, "X"),)).to_manifest() == {
        "name": "z1", "ancilla": 4, "coords": [], "terms": [{"qubit": 2, "basis": "X"}]}

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, dict(expected, ancilla=4),
                         label="StabilizerCheck.to_manifest")


# =========================================================================== #
# LogicalObservableSpec.__post_init__ + to_manifest                            #
# =========================================================================== #
def test_L0_logical_observable_valid_and_coercion():
    o = LogicalObservableSpec(name=7, terms=(PauliTerm(0, "Z"),), index=2.0)
    assert o.name == "7" and type(o.name) is str
    assert o.index == 2 and type(o.index) is int
    # default index=0
    assert LogicalObservableSpec("L", (PauliTerm(0, "Z"),)).index == 0


def test_L0_logical_observable_guards():
    _raises_exact(ValueError, "logical observable name must be non-empty",
                  lambda: LogicalObservableSpec("", (PauliTerm(0, "Z"),)))
    _raises_exact(
        ValueError,
        "logical observable name 'L X' must match '[A-Za-z0-9_.-]+'; avoid ':' and whitespace "
        "so generated record keys stay parseable",
        lambda: LogicalObservableSpec("L X", (PauliTerm(0, "Z"),)))
    _raises_exact(ValueError, "logical observable 'L' must have at least one term",
                  lambda: LogicalObservableSpec("L", ()))
    _raises_exact(ValueError, "logical observable index must be non-negative, got -1",
                  lambda: LogicalObservableSpec("L", (PauliTerm(0, "Z"),), index=-1))
    _raises_exact(ValueError, "'L' has duplicate term qubit 0",
                  lambda: LogicalObservableSpec("L", (PauliTerm(0, "Z"), PauliTerm(0, "X"))))
    _raises_exact(TypeError, "terms must be PauliTerm instances",
                  lambda: LogicalObservableSpec("L", (PauliTerm(0, "Z"), object())))


def test_L0_logical_observable_to_manifest_exact_dict():
    o = LogicalObservableSpec("LZ", (PauliTerm(0, "Z"), PauliTerm(1, "Z")), index=1)
    expected = {
        "name": "LZ", "index": 1,
        "terms": [{"qubit": 0, "basis": "Z"}, {"qubit": 1, "basis": "Z"}]}
    got = o.to_manifest()
    assert got == expected
    assert type(got["terms"]) is list

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, dict(expected, index=0),
                         label="LogicalObservableSpec.to_manifest")


# =========================================================================== #
# Axis1StaticZZDeviceSpec.__post_init__ / to_metadata / to_manifest            #
# =========================================================================== #
def test_L0_axis1_empty_default():
    a = Axis1StaticZZDeviceSpec(edges=())
    assert a.edges == () and a.num_qubits is None and a.zeta_rad_per_ns_by_edge == {}
    # to_metadata: empty calibrations -> the calibrations key is ABSENT (the falsy arc)
    assert a.to_metadata() == {"axis1_static_zz_couplings": []}
    assert a.to_manifest() == {
        "metadata_key": "axis1_static_zz_couplings", "edges": [], "calibrations": [],
        "num_qubits": None,
        "visibility": "public_schedule_metadata_no_mechanism_truth",
        "representability": "axis1_static_zz_device_edges_and_public_calibrations_not_operator_truth"}


def test_L0_axis1_with_edges_and_calibrations():
    # num_qubits is not None (the else arc of the ternary); edges normalized+sorted+ordered.
    a = Axis1StaticZZDeviceSpec(edges=((1, 0), (2, 3)), num_qubits=4,
                                zeta_rad_per_ns_by_edge={(0, 1): 0.25})
    assert a.edges == ((0, 1), (2, 3))            # (1,0) canonicalized to (0,1) + sorted
    assert a.num_qubits == 4
    assert a.zeta_rad_per_ns_by_edge == {(0, 1): {"zeta_rad_per_ns": 0.25, "epistemic_class": "c"}}
    # to_metadata: calibrations present -> the calibrations key IS added (the truthy arc)
    assert a.to_metadata() == {
        "axis1_static_zz_couplings": [[0, 1], [2, 3]],
        "axis1_static_zz_calibrations": [
            {"edge": [0, 1], "zeta_rad_per_ns": 0.25, "epistemic_class": "c"}]}
    expected_manifest = {
        "metadata_key": "axis1_static_zz_couplings",
        "edges": [[0, 1], [2, 3]],
        "calibrations": [{"edge": [0, 1], "zeta_rad_per_ns": 0.25, "epistemic_class": "c"}],
        "num_qubits": 4,
        "visibility": "public_schedule_metadata_no_mechanism_truth",
        "representability": "axis1_static_zz_device_edges_and_public_calibrations_not_operator_truth"}
    got = a.to_manifest()
    assert got == expected_manifest

    def prop(m):
        assert m == expected_manifest

    assert_discriminates(prop, got, dict(expected_manifest, num_qubits=5),
                         label="Axis1StaticZZDeviceSpec.to_manifest")


def test_L0_axis1_label_string_raises_exact():
    # The edges/calibrations LABEL string literals live in code_spec.py (passed to the
    # metadata_guard normalizers); trip each raise so a label WRAP mutant changes the message.
    _raises_exact(ValueError,
                  "Axis1StaticZZDeviceSpec.edges must be a sequence of two-qubit edges",
                  lambda: Axis1StaticZZDeviceSpec(edges="x"))
    _raises_exact(
        ValueError,
        "Axis1StaticZZDeviceSpec.zeta_rad_per_ns_by_edge[0] edge (1, 2) is not declared in "
        "axis1_static_zz_couplings",
        lambda: Axis1StaticZZDeviceSpec(edges=((0, 1),), num_qubits=3,
                                        zeta_rad_per_ns_by_edge={(1, 2): 0.5}))


# =========================================================================== #
# CodeSpec.__post_init__ (valid path + the seven top-level guards)             #
# =========================================================================== #
def test_L0_code_spec_valid_constructs():
    # exercises the full pass path (all seven guards pass + both _validate_* calls run) on
    # BOTH the clean rep spec and the rich X/Y/Z spec.
    s = _valid_rep_spec()
    assert s.name == "rep3z" and s.num_qubits == 5 and s.rounds == 3
    assert _rich_valid_spec().name == "rich"


def test_L0_code_spec_top_level_guards():
    _raises_exact(ValueError, "CodeSpec name must be non-empty",
                  lambda: _rep_spec_with(name=""))
    _raises_exact(ValueError, "num_qubits must be positive",
                  lambda: _rep_spec_with(num_qubits=0))
    _raises_exact(ValueError, "rounds must be at least 2 so detector deltas are defined",
                  lambda: _rep_spec_with(rounds=1))
    _raises_exact(ValueError, "CodeSpec must declare at least one data qubit",
                  lambda: _rep_spec_with(data_qubits=()))
    _raises_exact(ValueError, "CodeSpec must declare at least one ancilla qubit",
                  lambda: _rep_spec_with(ancilla_qubits=()))
    _raises_exact(ValueError, "CodeSpec must declare at least one stabilizer check",
                  lambda: _rep_spec_with(checks=()))
    _raises_exact(ValueError, "CodeSpec must declare at least one logical observable",
                  lambda: _rep_spec_with(logical_observables=()))


def test_L0_code_spec_name_num_rounds_coercion():
    # int name -> str(); float num_qubits/rounds -> int() (setattr-string + coercion mutants).
    s = _rep_spec_with(name=9, num_qubits=5.0, rounds=2.0)
    assert s.name == "9" and type(s.name) is str
    assert s.num_qubits == 5 and type(s.num_qubits) is int
    assert s.rounds == 2 and type(s.rounds) is int


def test_L0_code_spec_metadata_reserved_key_raises_exact():
    _raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator truth; reserved key "
        "CodeSpec.metadata.channel_truth matches 'channel_truth'. "
        "Use evaluator_sidecars with visibility='evaluator_only'.",
        lambda: _rep_spec_with(metadata={"channel_truth": {"x": 1}}))


# =========================================================================== #
# CodeSpec._validate_qubits routes (via __post_init__)                         #
# =========================================================================== #
def test_L0_code_spec_validate_qubits_routes():
    # out-of-range: boundary index == num_qubits trips `>=` (a `>` mutant would let q3
    # through and raise for q4 with a DIFFERENT message -> exact-message pin kills it).
    _raises_exact(
        ValueError, "qubit 3 outside [0, 3)",
        lambda: _rep_spec_with(
            num_qubits=3,
            data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data"), CodeQubit(2, "data")),
            ancilla_qubits=(CodeQubit(3, "ancilla"), CodeQubit(4, "ancilla"))))
    # duplicate index (an `in`->`not in` mutant would raise at the FIRST qubit -> "index 0")
    _raises_exact(
        ValueError, "duplicate qubit index 1",
        lambda: _rep_spec_with(
            data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data"), CodeQubit(1, "data"))))
    # role mismatch in data_qubits / ancilla_qubits
    _raises_exact(
        ValueError, "data_qubits entry 0 has role 'ancilla'",
        lambda: _rep_spec_with(
            data_qubits=(CodeQubit(0, "ancilla"), CodeQubit(1, "data"), CodeQubit(2, "data"))))
    _raises_exact(
        ValueError, "ancilla_qubits entry 3 has role 'data'",
        lambda: _rep_spec_with(
            ancilla_qubits=(CodeQubit(3, "data"), CodeQubit(4, "ancilla"))))


# =========================================================================== #
# CodeSpec._validate_checks_and_logicals routes (via __post_init__)            #
# =========================================================================== #
def test_L0_code_spec_check_routes():
    _raises_exact(
        ValueError, "duplicate stabilizer check name 'z0'",
        lambda: _rep_spec_with(checks=(
            StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),
            StabilizerCheck("z0", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z"))))))
    _raises_exact(
        ValueError, "check 'z0' ancilla 0 is not an ancilla qubit",
        lambda: _rep_spec_with(checks=(
            StabilizerCheck("z0", 0, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z"))))))
    _raises_exact(
        ValueError, "check 'z0' term 3 is not a data qubit",
        lambda: _rep_spec_with(checks=(
            StabilizerCheck("z0", 3, (PauliTerm(3, "Z"), PauliTerm(1, "Z"))),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z"))))))
    # genuinely NON-COMMUTING checks (zx=Z0X1, xx=X0X1 anticommute) -> the pairwise-commute
    # raise (exercises _pairs + commute inside the check loop).
    _raises_exact(
        ValueError, "stabilizer checks 'zx' and 'xx' do not commute",
        lambda: CodeSpec(
            name="bad", num_qubits=4,
            data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data")),
            ancilla_qubits=(CodeQubit(2, "ancilla"), CodeQubit(3, "ancilla")),
            checks=(StabilizerCheck("zx", 2, (PauliTerm(0, "Z"), PauliTerm(1, "X"))),
                    StabilizerCheck("xx", 3, (PauliTerm(0, "X"), PauliTerm(1, "X")))),
            logical_observables=(LogicalObservableSpec("l0", (PauliTerm(0, "Z"), PauliTerm(1, "X"))),),
            rounds=2))


def test_L0_code_spec_logical_routes():
    _raises_exact(
        ValueError, "duplicate logical observable name 'LZ'",
        lambda: _rep_spec_with(logical_observables=(
            LogicalObservableSpec("LZ", (PauliTerm(0, "Z"),), index=0),
            LogicalObservableSpec("LZ", (PauliTerm(2, "Z"),), index=1))))
    _raises_exact(
        ValueError, "duplicate logical observable index 0",
        lambda: _rep_spec_with(logical_observables=(
            LogicalObservableSpec("LZ", (PauliTerm(0, "Z"),), index=0),
            LogicalObservableSpec("LZ2", (PauliTerm(2, "Z"),), index=0))))
    _raises_exact(
        ValueError, "logical 'LZ' term 3 is not a data qubit",
        lambda: _rep_spec_with(logical_observables=(
            LogicalObservableSpec("LZ", (PauliTerm(3, "Z"),), index=0),)))
    # logical that does NOT commute with a check (LX=X0 vs z0=Z0Z1 -> anti on q0)
    _raises_exact(
        ValueError, "logical 'LX' does not commute with check 'z0'",
        lambda: _rep_spec_with(logical_observables=(
            LogicalObservableSpec("LX", (PauliTerm(0, "X"),), index=0),)))


def test_L0_code_spec_stabilizer_span_routes():
    span_msg = ("logical 'Lin' is in the stabilizer span; use DetectorDef/stabilizer records "
                "for check products, not LogicalObservableSpec")
    # single-check logical: Lin = Z0Z1 == check z0 (rank(rows)==rank(rows+[vec]))
    _raises_exact(
        ValueError, span_msg,
        lambda: _rep_spec_with(logical_observables=(
            LogicalObservableSpec("Lin", (PauliTerm(0, "Z"), PauliTerm(1, "Z")), index=0),)))
    # PRODUCT of BOTH checks: Lin = Z0Z2 = z0 XOR z1 (forces multi-row GF(2) elimination to
    # detect the dependency -- kills row-reduction / XOR mutants in _binary_row_rank).
    _raises_exact(
        ValueError, span_msg,
        lambda: _rep_spec_with(logical_observables=(
            LogicalObservableSpec("Lin", (PauliTerm(0, "Z"), PauliTerm(2, "Z")), index=0),)))


def test_L0_pauli_vector_Y_basis_span_discrimination():
    """Y contributes to BOTH the X-part and the Z-part of the symplectic vector. Two VALID
    specs whose Y-logical would fall INTO the stabilizer span if EITHER Y-contribution were
    dropped from ``_pauli_vector``: a Z-check spec (drop Y's X-bit -> Y==Z==the check -> in
    span) and an X-check spec (drop Y's Z-bit -> Y==X==the check -> in span). Constructing
    BOTH must SUCCEED in the real code; a set-element mutant that stops Y matching {'X','Y'}
    OR {'Z','Y'} makes exactly one of them raise 'in the stabilizer span' -> killed."""
    # Z-check + Y0Y1: real Y0Y1 (x=[1,1], z=[1,1]) is NOT in span{Z0Z1 (z-only)}.
    s_z = CodeSpec(
        name="yz", num_qubits=3,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data")),
        ancilla_qubits=(CodeQubit(2, "ancilla"),),
        checks=(StabilizerCheck("cz", 2, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),),
        logical_observables=(
            LogicalObservableSpec("L", (PauliTerm(0, "Y"), PauliTerm(1, "Y")), index=0),),
        rounds=2)
    assert s_z.logical_observables[0].name == "L"
    # X-check + Y0Y1: real Y0Y1 is NOT in span{X0X1 (x-only)}.
    s_x = CodeSpec(
        name="yx", num_qubits=3,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data")),
        ancilla_qubits=(CodeQubit(2, "ancilla"),),
        checks=(StabilizerCheck("cx", 2, (PauliTerm(0, "X"), PauliTerm(1, "X"))),),
        logical_observables=(
            LogicalObservableSpec("L", (PauliTerm(0, "Y"), PauliTerm(1, "Y")), index=0),),
        rounds=2)
    assert s_x.logical_observables[0].name == "L"


def test_L0_code_spec_pairs_ordering_noncommute():
    """A 3-check spec where checks[0],checks[1] anticommute but checks[0] COMMUTES with
    checks[2]: ``_pairs`` MUST yield (checks[0], checks[1]) FIRST so the reported pair is
    'ca' and 'cb'. An ``items[i - 1:]`` mutant instead reaches (checks[1], checks[0]) and
    reports 'cb' and 'ca' -> the exact-message pin kills it."""
    _raises_exact(
        ValueError, "stabilizer checks 'ca' and 'cb' do not commute",
        lambda: CodeSpec(
            name="pairs", num_qubits=5,
            data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data")),
            ancilla_qubits=(CodeQubit(2, "ancilla"), CodeQubit(3, "ancilla"),
                            CodeQubit(4, "ancilla")),
            checks=(StabilizerCheck("ca", 2, (PauliTerm(0, "Z"), PauliTerm(1, "X"))),
                    StabilizerCheck("cb", 3, (PauliTerm(0, "X"), PauliTerm(1, "X"))),
                    StabilizerCheck("cc", 4, (PauliTerm(1, "X"),))),
            logical_observables=(LogicalObservableSpec("L", (PauliTerm(0, "X"),), index=0),),
            rounds=2))


# =========================================================================== #
# CodeSpec.to_manifest + properties                                            #
# =========================================================================== #
def test_L0_code_spec_to_manifest_exact_dict():
    got = _valid_rep_spec().to_manifest()
    expected = {
        "name": "rep3z", "num_qubits": 5, "rounds": 3, "metadata": {},
        "operations": [
            {"name": "prep0", "metadata": {}},
            {"name": "stabilizer_round", "metadata": {}},
            {"name": "final_readout", "metadata": {}}],
        "data_qubits": [
            {"index": 0, "role": "data", "coords": [0.0]},
            {"index": 1, "role": "data", "coords": [1.0]},
            {"index": 2, "role": "data", "coords": [2.0]}],
        "ancilla_qubits": [
            {"index": 3, "role": "ancilla", "coords": []},
            {"index": 4, "role": "ancilla", "coords": []}],
        "checks": [
            {"name": "z0", "ancilla": 3, "coords": [0.5],
             "terms": [{"qubit": 0, "basis": "Z"}, {"qubit": 1, "basis": "Z"}]},
            {"name": "z1", "ancilla": 4, "coords": [1.5],
             "terms": [{"qubit": 1, "basis": "Z"}, {"qubit": 2, "basis": "Z"}]}],
        "logical_observables": [
            {"name": "LZ", "index": 0, "terms": [{"qubit": 0, "basis": "Z"}]}],
    }
    assert got == expected

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, {**expected, "rounds": 2}, label="CodeSpec.to_manifest")


def test_L0_code_spec_data_indices_independent_pin():
    s = _valid_rep_spec()
    # INDEPENDENT partition: the data indices I constructed are exactly (0, 1, 2).
    assert s.data_indices == (0, 1, 2)

    def prop(di):
        assert di == (0, 1, 2)

    # a wrong split (an ancilla index leaking in) must fail
    assert_discriminates(prop, s.data_indices, (0, 1, 2, 3), label="data_indices")


def test_L0_code_spec_ancilla_indices_independent_pin():
    s = _valid_rep_spec()
    assert s.ancilla_indices == (3, 4)

    def prop(ai):
        assert ai == (3, 4)

    assert_discriminates(prop, s.ancilla_indices, (0, 3, 4), label="ancilla_indices")


def test_L0_code_spec_operation_set_independent_pin():
    s = _valid_rep_spec()
    # default_memory_operations -> exactly these three, in order.
    assert s.operation_set.names == ("prep0", "stabilizer_round", "final_readout")

    def prop(names):
        assert names == ("prep0", "stabilizer_round", "final_readout")

    assert_discriminates(prop, s.operation_set.names,
                         ("prep0", "final_readout"), label="operation_set.names")


# =========================================================================== #
# L1 property (Hypothesis) -- manifest round-trip + partition invariants        #
# =========================================================================== #
_NAME = st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122),
                min_size=1, max_size=4)
_BASIS = st.sampled_from(["X", "Y", "Z"])


@settings(max_examples=100, deadline=None)
@given(q=st.integers(0, 30), basis=_BASIS)
def test_L1_pauli_term_manifest_roundtrip(q, basis):
    t = PauliTerm(q, basis)
    assert t.to_manifest() == {"qubit": q, "basis": basis}


@settings(max_examples=100, deadline=None)
@given(idx=st.integers(0, 30), role=st.sampled_from(["data", "ancilla"]),
       coords=st.lists(st.floats(-5, 5, allow_nan=False), min_size=0, max_size=3))
def test_L1_code_qubit_manifest_roundtrip(idx, role, coords):
    q = CodeQubit(idx, role, tuple(coords))
    assert q.to_manifest() == {"index": idx, "role": role, "coords": list(coords)}
    assert q.index == idx and q.role == role


@settings(max_examples=50, deadline=None)
@given(n_data=st.integers(2, 4), n_anc=st.integers(1, 3))
def test_L1_code_spec_indices_partition(n_data, n_anc):
    data = tuple(CodeQubit(i, "data") for i in range(n_data))
    anc = tuple(CodeQubit(n_data + i, "ancilla") for i in range(n_anc))
    # check z0=Z0Z1 (needs n_data>=2); logical LZ=Z0 commutes with it and is NOT in span.
    spec = CodeSpec(
        name="p", num_qubits=n_data + n_anc,
        data_qubits=data, ancilla_qubits=anc,
        checks=(StabilizerCheck("z0", n_data, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),),
        logical_observables=(LogicalObservableSpec("L", (PauliTerm(0, "Z"),), index=0),),
        rounds=2)
    assert spec.data_indices == tuple(range(n_data))
    assert spec.ancilla_indices == tuple(range(n_data, n_data + n_anc))
    # the two index sets partition the declared qubits (disjoint + complete)
    assert set(spec.data_indices).isdisjoint(spec.ancilla_indices)
    assert set(spec.data_indices) | set(spec.ancilla_indices) == set(range(n_data + n_anc))

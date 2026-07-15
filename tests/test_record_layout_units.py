"""Stage-D batch ``record_layout`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.record_layout`` (14 CPU-pure public units: 4
frozen-record-dataclass ``to_manifest`` methods + 3 ``RecordLayout`` record-schema
properties + ``RecordLayout.to_manifest`` + the ``build_repeated_memory_record_layout``
assembler + ``final_measurements`` + 4 record-KEY/NAME formatting functions; no torch,
no quimb, so out_of_scope is empty).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4;
work-list docs/SIMULATOR.md D16).
``frontend/record_layout.py`` owns the structured record layout the frontend compiles a
``CodeSpec`` into BEFORE Stim conversion: the four frozen record dataclasses
(``RoundMeasurementRecord``/``DetectorLayoutRecord``/``FinalDataRecord``/
``ObservableLayoutRecord``) each with a ``to_manifest``, the ``RecordLayout`` container
(+ ``detector_names``/``measurement_keys``/``observable_names``/``to_manifest``), the
``build_repeated_memory_record_layout`` assembler, ``final_measurements`` (the
qubit->final-readout-basis map), and the record-key/name formatting functions
``check_key``/``delta_detector_name``/``final_detector_name``/``final_key``.

L2 DISCIPLINE (100% coverage != discrimination). THE LOAD-BEARING PART is EXACT-STRING
pinning of the record KEYS/NAMES: each formatting function is pinned against an
INDEPENDENT f-string recompute (reconstructed from the source FORMAT, not the module's own
expression) with an ``assert_discriminates`` wrong-format variant (swapped fields / missing
separator / wrong prefix). ``build_repeated_memory_record_layout`` is pinned by a
from-scratch ``_view()`` reconstruction of every record on a rich d=3 rounds=3 rep-code
fixture (round count, per-round delta naming, round-1 delta key wiring, final-closure
keys/coords, sorted final-readout map). ``final_measurements`` is pinned on the same
fixture (qubit->basis map incl. the same-basis merge branch) and its incompatible-basis
raise is tripped through BOTH routes (final-check-closure AND final-logical-observable)
with the EXACT message via ``str(excinfo.value)==...``. The record properties are pinned
vs an INDEPENDENT extraction from the constructed records (NEVER the module's property).
Every ``to_manifest`` is pinned to its EXACT dict.

The private ``_add_final_measurement`` helper (not a scored unit) is exercised +
mutation-covered through ``final_measurements``: the first-insert (existing is None),
same-basis merge (existing == basis), and conflict (existing != basis) arcs are all
tripped, and the conflict raise is reached through EVERY input route reaching it.
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates

from error_coupling_simulator.frontend.record_layout import (
    DetectorLayoutRecord,
    FinalDataRecord,
    ObservableLayoutRecord,
    RecordLayout,
    RoundMeasurementRecord,
    build_repeated_memory_record_layout,
    check_key,
    delta_detector_name,
    final_detector_name,
    final_key,
    final_measurements,
)
from error_coupling_simulator.frontend.code_spec import (
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
)


# --------------------------------------------------------------------------- #
# helpers: exact-message raise + INDEPENDENT record reconstruction (NOT the    #
# module's own accessors -- a from-scratch tuple view of each record).         #
# --------------------------------------------------------------------------- #
def _raises_exact(exc, msg, fn):
    """pytest.raises pinning the EXACT ``str(exc)`` (kills mutmut string-literal wrap/case
    mutants that a substring ``match=`` lets survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _rm_view(r):
    return (r.key, r.round_index, r.check_name, r.ancilla)


def _det_view(d):
    return (d.name, d.index, d.kind, tuple(d.keys), tuple(d.coords))


def _fd_view(f):
    return (f.key, f.qubit, f.basis)


def _obs_view(o):
    return (o.name, o.index, tuple(o.keys))


# --------------------------------------------------------------------------- #
# CodeSpec fixtures (validated at runtime -- see the D16 scratch de-risk).      #
# --------------------------------------------------------------------------- #
def _rep_spec(rounds: int = 3) -> CodeSpec:
    """A valid d=3 Z-memory repetition-code spec: two Z-checks (z0=Z0Z1 anc 3, z1=Z1Z2
    anc 4), logical LZ=Z0, per-check coords so the coords concatenation is load-bearing.
    All final-readout bases are Z (no conflict); the logical's Z0 shares q0 with z0's Z0
    so final_measurements exercises the same-basis MERGE branch."""
    return CodeSpec(
        name="rep3z",
        num_qubits=5,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data"), CodeQubit(2, "data")),
        ancilla_qubits=(CodeQubit(3, "ancilla"), CodeQubit(4, "ancilla")),
        checks=(
            StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z")), (0.5,)),
            StabilizerCheck("z1", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z")), (1.5,)),
        ),
        logical_observables=(LogicalObservableSpec("LZ", (PauliTerm(0, "Z"),), index=0),),
        rounds=rounds,
    )


def _check_conflict_spec() -> CodeSpec:
    """Valid spec whose TWO checks (xA=X0X1, zB=Z0Z1) commute (2 anti) yet request
    incompatible final bases on q0 -> final_measurements raises in the CHECK-terms loop."""
    return CodeSpec(
        name="xz_conflict",
        num_qubits=5,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data"), CodeQubit(2, "data")),
        ancilla_qubits=(CodeQubit(3, "ancilla"), CodeQubit(4, "ancilla")),
        checks=(
            StabilizerCheck("xA", 3, (PauliTerm(0, "X"), PauliTerm(1, "X"))),
            StabilizerCheck("zB", 4, (PauliTerm(0, "Z"), PauliTerm(1, "Z"))),
        ),
        logical_observables=(LogicalObservableSpec("L", (PauliTerm(2, "X"),), index=0),),
        rounds=2,
    )


def _logical_conflict_spec() -> CodeSpec:
    """Valid spec whose check xA=X0X1 and logical L=Z0Z1 commute (2 anti) yet request
    incompatible final bases on q0 -> final_measurements raises in the LOGICAL-terms loop."""
    return CodeSpec(
        name="xl_conflict",
        num_qubits=3,
        data_qubits=(CodeQubit(0, "data"), CodeQubit(1, "data")),
        ancilla_qubits=(CodeQubit(2, "ancilla"),),
        checks=(StabilizerCheck("xA", 2, (PauliTerm(0, "X"), PauliTerm(1, "X"))),),
        logical_observables=(
            LogicalObservableSpec("L", (PauliTerm(0, "Z"), PauliTerm(1, "Z")), index=0),
        ),
        rounds=2,
    )


# =========================================================================== #
# RoundMeasurementRecord.to_manifest                                           #
# =========================================================================== #
def test_L0_round_measurement_record_to_manifest():
    r = RoundMeasurementRecord(key="round0:z0", round_index=0, check_name="z0", ancilla=3)
    expected = {"key": "round0:z0", "round_index": 0, "check_name": "z0", "ancilla": 3}
    assert r.to_manifest() == expected

    def prop(m):
        assert m == expected

    wrong = dict(expected, ancilla=4)  # a single wrong field must fail the pin
    assert_discriminates(prop, r.to_manifest(), wrong, label="RoundMeasurementRecord.to_manifest")


# =========================================================================== #
# DetectorLayoutRecord.to_manifest                                             #
# =========================================================================== #
def test_L0_detector_layout_record_to_manifest():
    d = DetectorLayoutRecord(
        name="delta:z0:round1", index=2, kind="round_delta",
        keys=("round0:z0", "round1:z0"), coords=(0.5, 1.0))
    expected = {
        "name": "delta:z0:round1", "index": 2, "kind": "round_delta",
        "keys": ["round0:z0", "round1:z0"], "coords": [0.5, 1.0]}
    got = d.to_manifest()
    assert got == expected
    # keys/coords are coerced to LISTS (not tuples) -- pins the list(...) coercions
    assert type(got["keys"]) is list and type(got["coords"]) is list
    # default coords=() -> [] (the empty-coords arc)
    d0 = DetectorLayoutRecord(name="final:z0", index=4, kind="final_closure", keys=("round2:z0",))
    assert d0.to_manifest() == {
        "name": "final:z0", "index": 4, "kind": "final_closure",
        "keys": ["round2:z0"], "coords": []}

    def prop(m):
        assert m == expected

    wrong = dict(expected, kind="final_closure")  # wrong kind must fail
    assert_discriminates(prop, got, wrong, label="DetectorLayoutRecord.to_manifest")


# =========================================================================== #
# FinalDataRecord.to_manifest                                                  #
# =========================================================================== #
def test_L0_final_data_record_to_manifest():
    f = FinalDataRecord(key="final:q0:Z", qubit=0, basis="Z")
    expected = {"key": "final:q0:Z", "qubit": 0, "basis": "Z"}
    assert f.to_manifest() == expected

    def prop(m):
        assert m == expected

    wrong = dict(expected, basis="X")
    assert_discriminates(prop, f.to_manifest(), wrong, label="FinalDataRecord.to_manifest")


# =========================================================================== #
# ObservableLayoutRecord.to_manifest                                           #
# =========================================================================== #
def test_L0_observable_layout_record_to_manifest():
    o = ObservableLayoutRecord(name="LZ", index=0, keys=("final:q0:Z", "final:q1:Z"))
    expected = {"name": "LZ", "index": 0, "keys": ["final:q0:Z", "final:q1:Z"]}
    got = o.to_manifest()
    assert got == expected
    assert type(got["keys"]) is list  # keys coerced to a list

    def prop(m):
        assert m == expected

    wrong = dict(expected, keys=["final:q0:Z"])  # dropped key must fail
    assert_discriminates(prop, got, wrong, label="ObservableLayoutRecord.to_manifest")


# =========================================================================== #
# RecordLayout container: build a hand layout, pin properties + to_manifest    #
# =========================================================================== #
def _hand_layout() -> RecordLayout:
    """A RecordLayout built DIRECTLY (not via the assembler) with two of each record type
    and DISTINCT keys, so measurement_keys' round+final concatenation is load-bearing."""
    return RecordLayout(
        schedule_name="demo_sched",
        round_measurements=(
            RoundMeasurementRecord("round0:z0", 0, "z0", 3),
            RoundMeasurementRecord("round1:z0", 1, "z0", 3),
        ),
        detectors=(
            DetectorLayoutRecord("delta:z0:round1", 0, "round_delta",
                                 ("round0:z0", "round1:z0"), (0.5, 1.0)),
            DetectorLayoutRecord("final:z0", 1, "final_closure",
                                 ("round1:z0", "final:q0:Z"), (0.5, 2.0)),
        ),
        final_data=(
            FinalDataRecord("final:q0:Z", 0, "Z"),
            FinalDataRecord("final:q1:Z", 1, "Z"),
        ),
        observables=(
            ObservableLayoutRecord("LZ", 0, ("final:q0:Z",)),
            ObservableLayoutRecord("LX", 1, ("final:q1:Z",)),
        ),
    )


def test_L0_record_layout_detector_names_independent_pin():
    lay = _hand_layout()
    expected = tuple(d.name for d in lay.detectors)  # INDEPENDENT extraction
    assert expected == ("delta:z0:round1", "final:z0")
    assert lay.detector_names == expected

    def prop(dn):
        assert dn == expected

    assert_discriminates(prop, lay.detector_names, ("delta:z0:round1",), label="detector_names")


def test_L0_record_layout_measurement_keys_independent_pin():
    lay = _hand_layout()
    # INDEPENDENT extraction: round_measurement keys FOLLOWED BY final_data keys.
    expected = tuple(r.key for r in lay.round_measurements) + tuple(
        f.key for f in lay.final_data)
    assert expected == ("round0:z0", "round1:z0", "final:q0:Z", "final:q1:Z")
    assert lay.measurement_keys == expected

    def prop(mk):
        assert mk == expected

    # dropping a FINAL_DATA key must fail -> proves the concatenation's 2nd operand bites
    assert_discriminates(prop, lay.measurement_keys,
                         ("round0:z0", "round1:z0", "final:q0:Z"), label="measurement_keys")
    # a round-only extraction (missing the final_data half) must ALSO fail the pin
    assert lay.measurement_keys != tuple(r.key for r in lay.round_measurements)


def test_L0_record_layout_observable_names_independent_pin():
    lay = _hand_layout()
    expected = tuple(o.name for o in lay.observables)
    assert expected == ("LZ", "LX")
    assert lay.observable_names == expected

    def prop(on):
        assert on == expected

    assert_discriminates(prop, lay.observable_names, ("LZ", "WRONG"), label="observable_names")


def test_L0_record_layout_to_manifest_exact_dict():
    lay = _hand_layout()
    expected = {
        "schedule_name": "demo_sched",
        "round_measurements": [
            {"key": "round0:z0", "round_index": 0, "check_name": "z0", "ancilla": 3},
            {"key": "round1:z0", "round_index": 1, "check_name": "z0", "ancilla": 3},
        ],
        "detectors": [
            {"name": "delta:z0:round1", "index": 0, "kind": "round_delta",
             "keys": ["round0:z0", "round1:z0"], "coords": [0.5, 1.0]},
            {"name": "final:z0", "index": 1, "kind": "final_closure",
             "keys": ["round1:z0", "final:q0:Z"], "coords": [0.5, 2.0]},
        ],
        "final_data": [
            {"key": "final:q0:Z", "qubit": 0, "basis": "Z"},
            {"key": "final:q1:Z", "qubit": 1, "basis": "Z"},
        ],
        "observables": [
            {"name": "LZ", "index": 0, "keys": ["final:q0:Z"]},
            {"name": "LX", "index": 1, "keys": ["final:q1:Z"]},
        ],
    }
    got = lay.to_manifest()
    assert got == expected

    def prop(m):
        assert m == expected

    wrong = {**expected, "schedule_name": "OTHER"}  # a single field drift must fail
    assert_discriminates(prop, got, wrong, label="RecordLayout.to_manifest")


# =========================================================================== #
# build_repeated_memory_record_layout -- exact-structure pin (rich fixture)     #
# =========================================================================== #
# INDEPENDENT hand reconstruction of the d=3 rounds=3 rep-code layout (literal strings;
# NOT built from the module's own check_key/delta_detector_name/... expressions).
_RM_EXPECTED = [
    ("round0:z0", 0, "z0", 3), ("round0:z1", 0, "z1", 4),
    ("round1:z0", 1, "z0", 3), ("round1:z1", 1, "z1", 4),
    ("round2:z0", 2, "z0", 3), ("round2:z1", 2, "z1", 4),
]
_DET_EXPECTED = [
    ("delta:z0:round1", 0, "round_delta", ("round0:z0", "round1:z0"), (0.5, 1.0)),
    ("delta:z1:round1", 1, "round_delta", ("round0:z1", "round1:z1"), (1.5, 1.0)),
    ("delta:z0:round2", 2, "round_delta", ("round1:z0", "round2:z0"), (0.5, 2.0)),
    ("delta:z1:round2", 3, "round_delta", ("round1:z1", "round2:z1"), (1.5, 2.0)),
    ("final:z0", 4, "final_closure", ("round2:z0", "final:q0:Z", "final:q1:Z"), (0.5, 3.0)),
    ("final:z1", 5, "final_closure", ("round2:z1", "final:q1:Z", "final:q2:Z"), (1.5, 3.0)),
]
_FD_EXPECTED = [
    ("final:q0:Z", 0, "Z"), ("final:q1:Z", 1, "Z"), ("final:q2:Z", 2, "Z"),
]
_OBS_EXPECTED = [("LZ", 0, ("final:q0:Z",))]


def test_L0_build_repeated_memory_record_layout_pins_full_structure():
    lay = build_repeated_memory_record_layout(_rep_spec(rounds=3), schedule_name="sched")
    assert lay.schedule_name == "sched"
    assert [_rm_view(r) for r in lay.round_measurements] == _RM_EXPECTED
    assert [_det_view(d) for d in lay.detectors] == _DET_EXPECTED
    assert [_fd_view(f) for f in lay.final_data] == _FD_EXPECTED
    assert [_obs_view(o) for o in lay.observables] == _OBS_EXPECTED

    # KILLER: a single wrong detector row (round-1 delta key mis-wired) must fail the pin.
    def prop(views):
        assert views == _DET_EXPECTED

    wrong = list(_DET_EXPECTED)
    wrong[0] = ("delta:z0:round1", 0, "round_delta", ("round1:z0", "round1:z0"), (0.5, 1.0))
    assert_discriminates(prop, [_det_view(d) for d in lay.detectors], wrong,
                         label="build_repeated detectors")


def test_L0_build_repeated_rounds2_has_single_delta_round():
    """rounds=2 -> the delta loop range(1, rounds) runs for r=1 ONLY (kills a
    range(0, rounds) / range(2, rounds) mutant that would add/drop a delta round)."""
    lay = build_repeated_memory_record_layout(_rep_spec(rounds=2), schedule_name="s2")
    # round_measurements: rounds 0,1 x checks z0,z1
    assert [_rm_view(r) for r in lay.round_measurements] == [
        ("round0:z0", 0, "z0", 3), ("round0:z1", 0, "z1", 4),
        ("round1:z0", 1, "z0", 3), ("round1:z1", 1, "z1", 4)]
    # delta detectors only for r=1, then the two final-closure detectors
    assert [_det_view(d) for d in lay.detectors] == [
        ("delta:z0:round1", 0, "round_delta", ("round0:z0", "round1:z0"), (0.5, 1.0)),
        ("delta:z1:round1", 1, "round_delta", ("round0:z1", "round1:z1"), (1.5, 1.0)),
        ("final:z0", 2, "final_closure", ("round1:z0", "final:q0:Z", "final:q1:Z"), (0.5, 2.0)),
        ("final:z1", 3, "final_closure", ("round1:z1", "final:q1:Z", "final:q2:Z"), (1.5, 2.0))]


# =========================================================================== #
# final_measurements -- qubit->basis map + both incompatible-basis raise routes #
# =========================================================================== #
def test_L0_final_measurements_qubit_basis_map():
    # all-Z rep code: every data qubit reads out in Z; the logical's Z0 shares q0 with
    # check z0's Z0 so the same-basis MERGE branch (existing == basis) is exercised.
    got = final_measurements(_rep_spec(rounds=3))
    expected = {0: "Z", 1: "Z", 2: "Z"}
    assert got == expected

    def prop(m):
        assert m == expected

    assert_discriminates(prop, got, {0: "Z", 1: "X", 2: "Z"}, label="final_measurements map")


def test_L0_final_measurements_check_route_conflict_raises():
    # existing X (from check xA) != Z (from check zB) -> raise in the CHECK-terms loop;
    # the message carries the check-route context f-string (pins it exactly).
    _raises_exact(
        ValueError,
        "final check closure 'zB' requests incompatible bases for final readout "
        "on qubit 0: X vs Z",
        lambda: final_measurements(_check_conflict_spec()))


def test_L0_final_measurements_logical_route_conflict_raises():
    # existing X (from check xA) != Z (from logical L) -> raise in the LOGICAL-terms loop;
    # the message carries the logical-route context f-string (pins it exactly).
    _raises_exact(
        ValueError,
        "final logical observable 'L' requests incompatible bases for final readout "
        "on qubit 0: X vs Z",
        lambda: final_measurements(_logical_conflict_spec()))


# =========================================================================== #
# record-KEY/NAME formatting functions -- exact-string pins vs INDEPENDENT      #
# f-string recomputes (reconstructed from the source FORMAT, not copied).       #
# =========================================================================== #
def test_L0_check_key_exact_format():
    # source format: f"round{int(round_index)}:{check_name}"
    assert check_key(2, "z0") == "round2:z0"
    assert check_key(2, "z0") == f"round{2}:z0"                 # independent recompute
    assert check_key(2.0, "z0") == "round2:z0"                 # int() coercion (no ".0")
    assert check_key(0, "x1") == "round0:x1"

    def prop(k):
        assert k == "round2:z0"

    # wrong format: swapped order (name:round) must fail -> separator/field-order teeth
    assert_discriminates(prop, check_key(2, "z0"), "z0:round2", label="check_key format")
    # missing the ':' separator must also fail
    assert check_key(2, "z0") != f"round{2}z0"


def test_L0_delta_detector_name_exact_format():
    # source format: f"delta:{check_name}:round{int(round_index)}"  (args: name, round!)
    assert delta_detector_name("z0", 1) == "delta:z0:round1"
    assert delta_detector_name("z0", 1) == f"delta:z0:round{1}"   # independent recompute
    assert delta_detector_name("z1", 2.0) == "delta:z1:round2"   # int() coercion

    def prop(n):
        assert n == "delta:z0:round1"

    # swapped fields (round before name) must fail
    assert_discriminates(prop, delta_detector_name("z0", 1), "delta:round1:z0",
                         label="delta_detector_name format")
    # wrong prefix must fail
    assert delta_detector_name("z0", 1) != "final:z0:round1"


def test_L0_final_detector_name_exact_format():
    # source format: f"final:{check_name}"
    assert final_detector_name("z0") == "final:z0"
    assert final_detector_name("z0") == f"final:{'z0'}"          # independent recompute
    assert final_detector_name("x1") == "final:x1"

    def prop(n):
        assert n == "final:z0"

    # wrong prefix (delta:) must fail
    assert_discriminates(prop, final_detector_name("z0"), "delta:z0",
                         label="final_detector_name format")
    # missing separator must fail
    assert final_detector_name("z0") != "finalz0"


def test_L0_final_key_exact_format():
    # source format: f"final:q{int(qubit)}:{basis}"
    assert final_key(0, "Z") == "final:q0:Z"
    assert final_key(0, "Z") == f"final:q{0}:Z"                  # independent recompute
    assert final_key(2.0, "X") == "final:q2:X"                  # int() coercion
    assert final_key(1, "Y") == "final:q1:Y"

    def prop(k):
        assert k == "final:q0:Z"

    # swapped basis/qubit order must fail
    assert_discriminates(prop, final_key(0, "Z"), "final:qZ:0", label="final_key format")
    # dropping the 'q' prefix must fail
    assert final_key(0, "Z") != "final:0:Z"


# =========================================================================== #
# L1 property (Hypothesis) -- format invariants + record-schema extraction      #
# =========================================================================== #
_NAME = st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122),
                min_size=1, max_size=5)
_BASIS = st.sampled_from(["X", "Y", "Z"])


@settings(max_examples=100, deadline=None)
@given(r=st.integers(0, 20), name=_NAME)
def test_L1_check_key_matches_independent_recompute(r, name):
    assert check_key(r, name) == f"round{r}:{name}"


@settings(max_examples=100, deadline=None)
@given(r=st.integers(0, 20), name=_NAME)
def test_L1_delta_detector_name_matches_independent_recompute(r, name):
    assert delta_detector_name(name, r) == f"delta:{name}:round{r}"


@settings(max_examples=100, deadline=None)
@given(q=st.integers(0, 20), basis=_BASIS)
def test_L1_final_key_matches_independent_recompute(q, basis):
    assert final_key(q, basis) == f"final:q{q}:{basis}"


@settings(max_examples=75, deadline=None)
@given(keys=st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=4, unique=True),
       fkeys=st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=4, unique=True))
def test_L1_measurement_keys_is_round_then_final_concatenation(keys, fkeys):
    lay = RecordLayout(
        schedule_name="h",
        round_measurements=tuple(
            RoundMeasurementRecord(k, i, "c", 0) for i, k in enumerate(keys)),
        detectors=(),
        final_data=tuple(FinalDataRecord(k, i, "Z") for i, k in enumerate(fkeys)),
        observables=(),
    )
    assert lay.measurement_keys == tuple(keys) + tuple(fkeys)

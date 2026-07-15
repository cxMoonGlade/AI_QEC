"""Stage-D batch ``operation`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.operation`` (9 CPU-pure public units: the two frozen
dataclasses ``OperationSpec`` (``__post_init__`` name-canonicalization + metadata validation,
``to_manifest``) and ``OperationSet`` (``__post_init__`` empty/duplicate guards, the ``names``
property, ``require``, ``to_manifest``), plus the three module functions
``canonical_operation_name`` / ``default_memory_operations`` / ``as_operation_set``; the module
imports NEITHER torch NOR quimb -- ``dataclasses`` + a sibling ``metadata_guard.
validate_public_metadata`` -- so out_of_scope is empty).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4;
work-list docs/SIMULATOR.md D24).
``frontend/operation.py`` owns the PUBLIC construction vocabulary a ``CodeSpec`` declares before
a schedule compiles it. It is NOT a noise/mechanism model, NOT evaluator truth, NOT a serialized
channel payload -- just a named-operation + validated-metadata carrier and the name
canonicalization/default helpers.

L2 DISCIPLINE (100% coverage != discrimination). The alias map, the ALLOWED name set (and its
sorted form in the raise message), the schema of every manifest dict, and every guard message are
HARDCODED here (deliberately NOT imported from src): a mutmut mutation of a module constant/literal
must make the module's output stop matching THIS hardcoded literal -> the pin fails -> the mutant is
killed. Every raising guard is tripped through EVERY public route reaching it with the EXACT message
via ``assert_raises_exact`` (kills the string-wrap/case/None-message mutants a substring ``match=``
leaves surviving). The D19 ``.lower()`` note: mutmut wraps a literal as ``XX<s>XX`` (NOT a
case-swap), and ``XXprep0XX`` survives ``.lower()`` yet FAILS the ALLOWED-membership guard -> raise
-> killed; the already-canonical caller literals are therefore fully discriminated (no masked
fraction).
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_raises_exact

from error_coupling_simulator.frontend.operation import (
    OperationSet,
    OperationSpec,
    as_operation_set,
    canonical_operation_name,
    default_memory_operations,
)

# --------------------------------------------------------------------------- #
# INDEPENDENT hardcoded literals (deliberately NOT imported from the module):  #
# a mutmut mutation of the module's alias/ALLOWED constant must make the        #
# module's output stop matching THESE literals -> the pin fails -> mutant dead. #
# --------------------------------------------------------------------------- #
_ALLOWED = ("prep0", "prep1", "prep_plus", "prep_minus", "stabilizer_round", "final_readout")
# sorted(ALLOWED_OPERATION_NAMES) as it appears in the unsupported-name raise message
# ('0'<'1'<'_' and 'f'<'p'<'s'):
_ALLOWED_SORTED = ["final_readout", "prep0", "prep1", "prep_minus", "prep_plus", "stabilizer_round"]
_ALIASES = {"prepp": "prep_plus", "prepm": "prep_minus"}


def _unsupported_msg(original: str) -> str:
    """INDEPENDENT reconstruction of the canonical_operation_name raise message; carries the
    ORIGINAL (pre-normalization) name repr + the hardcoded sorted ALLOWED set."""
    return f"unsupported frontend operation {original!r}; allowed={_ALLOWED_SORTED}"


# =========================================================================== #
# canonical_operation_name                                                      #
# =========================================================================== #
@pytest.mark.parametrize("name", _ALLOWED)
def test_L0_canonical_allowed_names_round_trip(name):
    # every ALLOWED name maps to itself (kills each frozenset-member wrap: a wrapped member
    # makes THIS name fail the membership guard -> raise -> this assert errors -> killed).
    assert canonical_operation_name(name) == name


def test_L0_canonical_aliases_pin():
    # the two alias entries map to their canonical targets (kills the alias key AND value wraps:
    # a wrapped value is not in ALLOWED -> raise; a wrapped key misses the .get -> raise).
    assert canonical_operation_name("prepp") == "prep_plus"
    assert canonical_operation_name("prepm") == "prep_minus"

    def prop(result):
        assert result == "prep_plus"

    # teeth: the property distinguishes the aliased result from the un-aliased raw string.
    assert_discriminates(prop, canonical_operation_name("prepp"), "prepp", label="alias maps")


def test_L0_canonical_strip_and_lower_load_bearing():
    # .strip() + .lower() are BOTH load-bearing: without either, the padded/upper form is NOT in
    # ALLOWED and would raise. Also an aliased upper+padded input exercises both then the alias.
    assert canonical_operation_name("  PREP0  ") == "prep0"
    assert canonical_operation_name("PREP_Plus") == "prep_plus"
    assert canonical_operation_name("  PREPP ") == "prep_plus"
    assert canonical_operation_name("Stabilizer_Round") == "stabilizer_round"


def test_L0_canonical_unsupported_raises_exact():
    # `not in` guard fires on an unsupported name; message carries the ORIGINAL repr + sorted set.
    assert_raises_exact(
        ValueError, _unsupported_msg("bogus"),
        lambda: canonical_operation_name("bogus"),
        label="canonical unsupported")
    # a MIXED-CASE invalid pins that the message uses the ORIGINAL name (`name!r`), NOT the
    # lowered `out` -- the repr shows 'PREP9', not 'prep9'.
    assert_raises_exact(
        ValueError, _unsupported_msg("PREP9"),
        lambda: canonical_operation_name("PREP9"),
        label="canonical unsupported mixed-case")
    # an EMPTY string is also unsupported (the `not in` guard, valid vs invalid both exercised).
    assert_raises_exact(
        ValueError, _unsupported_msg(""),
        lambda: canonical_operation_name(""),
        label="canonical unsupported empty")


def test_L0_canonical_membership_guard_both_directions():
    # `not in` guard exercised BOTH ways: a valid name returns without raising, an invalid one
    # raises (kills `not in`->`in`). Teeth via a value-property: a valid canonical output is in
    # ALLOWED, an out-of-set string is not.
    assert canonical_operation_name("prep0") == "prep0"
    with pytest.raises(ValueError):
        canonical_operation_name("not_a_real_op")

    def prop(name_out):
        assert name_out in _ALLOWED

    assert_discriminates(prop, canonical_operation_name("prep0"), "not_a_real_op",
                         label="canonical membership guard")


# =========================================================================== #
# OperationSpec.__post_init__  --  canonicalize name + validate metadata         #
# =========================================================================== #
def test_L0_operation_spec_post_init_canonicalizes_name():
    # an UPPER/padded name is coerced to the canonical lower form (kills the 'name' setattr-key
    # wrap: under the mutant self.name would keep the RAW 'PREP0' input).
    s = OperationSpec("  PREP0  ")
    assert s.name == "prep0"
    # an alias name is canonicalized at construction too.
    assert OperationSpec("prepp").name == "prep_plus"

    def prop(spec):
        assert spec.name == "prep0"

    assert_discriminates(prop, OperationSpec("PREP0"), OperationSpec("prep1"),
                         label="OperationSpec canonicalizes name")


def test_L0_operation_spec_post_init_validates_and_copies_metadata():
    raw = {"note": "hi", "count": 3}
    s = OperationSpec("prep0", raw)
    # the stored metadata equals the input BUT is a distinct COPY (validate_public_metadata does
    # dict(metadata)) -- kills the 'metadata' setattr-key wrap (under which self.metadata would
    # remain the SAME input object).
    assert s.metadata == raw
    assert s.metadata is not raw
    # default metadata is an empty dict.
    assert OperationSpec("prep0").metadata == {}


def test_L0_operation_spec_post_init_rejects_reserved_metadata_key_exact():
    # a reserved evaluator/error-model metadata key is rejected by validate_public_metadata with
    # the EXACT message carrying the OperationSpec(<name>).metadata label (kills the label
    # f-string wrap + proves validate_public_metadata is load-bearing at construction).
    assert_raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator/error-model semantics; "
        "reserved key OperationSpec(prep0).metadata.error matches exact key 'error'. "
        "Put runnable noise in NoiseSpec and evaluator truth in evaluator_sidecars.",
        lambda: OperationSpec("prep0", {"error": 1}),
        label="OperationSpec reserved-metadata guard")
    # the label interpolates the CANONICAL name (prep0), even for an upper/alias input.
    assert_raises_exact(
        ValueError,
        "public-artifact metadata cannot contain evaluator/error-model semantics; "
        "reserved key OperationSpec(prep_plus).metadata.error matches exact key 'error'. "
        "Put runnable noise in NoiseSpec and evaluator truth in evaluator_sidecars.",
        lambda: OperationSpec("PREPP", {"error": 1}),
        label="OperationSpec reserved-metadata guard canonical label")


def test_L0_operation_spec_post_init_bad_name_raises_exact():
    # an unsupported name at construction propagates the canonical guard's exact message.
    assert_raises_exact(
        ValueError, _unsupported_msg("nope"),
        lambda: OperationSpec("nope"),
        label="OperationSpec bad name")


# =========================================================================== #
# OperationSpec.to_manifest                                                      #
# =========================================================================== #
def test_L0_operation_spec_to_manifest_exact_dict():
    s = OperationSpec("prep_plus", {"note": "x"})
    got = s.to_manifest()
    expected = {"name": "prep_plus", "metadata": {"note": "x"}}
    assert got == expected
    # the manifest metadata is a COPY (dict(self.metadata)), not the spec's own object.
    assert got["metadata"] is not s.metadata

    def prop(m):
        assert m == expected

    wrong = {"name": "prep_plus", "metadata": {"note": "DRIFT"}}  # a single field drift
    assert_discriminates(prop, got, wrong, label="OperationSpec.to_manifest exact")


# =========================================================================== #
# OperationSet.__post_init__  --  empty + duplicate guards + tuple coercion       #
# =========================================================================== #
def test_L0_operation_set_empty_raises_exact():
    # empty operations -> the first guard raises with its EXACT message (both () and [] routes).
    assert_raises_exact(
        ValueError, "OperationSet must contain at least one operation",
        lambda: OperationSet(()),
        label="OperationSet empty tuple")
    assert_raises_exact(
        ValueError, "OperationSet must contain at least one operation",
        lambda: OperationSet([]),
        label="OperationSet empty list")


def test_L0_operation_set_unique_constructs_and_coerces_to_tuple():
    # a UNIQUE multi-op set constructs (no raise) -- kills the duplicate-count `>`->`>=` and
    # `1`->`0` mutants (every unique name would falsely count as a duplicate under those).
    ops = [OperationSpec("prep0"), OperationSpec("prep1"), OperationSpec("final_readout")]
    os_ = OperationSet(ops)               # LIST input
    # stored as a TUPLE (kills the 'operations' setattr-key wrap + proves tuple() coercion:
    # under the wrap self.operations would remain the input LIST).
    assert type(os_.operations) is tuple
    assert os_.operations == tuple(ops)


def test_L0_operation_set_duplicate_raises_exact():
    # a single duplicate name -> exact message with the sorted single-element list.
    assert_raises_exact(
        ValueError, "duplicate frontend operations ['prep0']",
        lambda: OperationSet((OperationSpec("prep0"), OperationSpec("prep0"))),
        label="OperationSet duplicate single")
    # TWO distinct duplicated names, supplied in REVERSED order, still report SORTED (kills a
    # dropped sorted()) and `1`->`2` (each name appears exactly twice -> count 2 > 1).
    assert_raises_exact(
        ValueError, "duplicate frontend operations ['prep0', 'prep1']",
        lambda: OperationSet((OperationSpec("prep1"), OperationSpec("prep0"),
                              OperationSpec("prep1"), OperationSpec("prep0"))),
        label="OperationSet duplicate two sorted")


# =========================================================================== #
# OperationSet.names                                                            #
# =========================================================================== #
def _canonical_set() -> OperationSet:
    return OperationSet((OperationSpec("prep0"), OperationSpec("prep1"),
                         OperationSpec("final_readout")))


def test_L0_operation_set_names_exact_tuple():
    os_ = _canonical_set()
    got = os_.names
    expected = ("prep0", "prep1", "final_readout")
    assert got == expected
    assert type(got) is tuple

    def prop(names):
        assert names == expected

    wrong = OperationSet((OperationSpec("prep0"), OperationSpec("prep1"),
                          OperationSpec("stabilizer_round"))).names
    assert_discriminates(prop, got, wrong, label="OperationSet.names exact")


# =========================================================================== #
# OperationSet.require                                                          #
# =========================================================================== #
def test_L0_operation_set_require_all_present_returns_none():
    os_ = _canonical_set()
    # all present -> None (no raise). tuple / alias / upper-case routes all pass through the
    # canonicalization then the membership check.
    assert os_.require(("prep0", "final_readout"), label="schedule") is None
    assert os_.require(("PREP0",), label="schedule") is None          # canonical -> prep0
    # a required op given as an ALIAS whose canonical target is present passes.
    os2 = OperationSet((OperationSpec("prep_plus"),))
    assert os2.require(("prepp",), label="schedule") is None


def test_L0_operation_set_require_missing_raises_exact_every_route():
    os_ = OperationSet((OperationSpec("prep0"), OperationSpec("prep1")))
    msg = ("schedule requires frontend operation(s) ['final_readout'], "
           "but CodeSpec declares ['prep0', 'prep1']")
    # TUPLE route
    assert_raises_exact(ValueError, msg,
                        lambda: os_.require(("final_readout",), label="schedule"),
                        label="require missing tuple")
    # LIST route
    assert_raises_exact(ValueError, msg,
                        lambda: os_.require(["final_readout"], label="schedule"),
                        label="require missing list")
    # SET route
    assert_raises_exact(ValueError, msg,
                        lambda: os_.require({"final_readout"}, label="schedule"),
                        label="require missing set")
    # ALIAS route: the missing name is reported in its CANONICAL form (prep_plus), not 'prepp'
    # -> proves canonical_operation_name is applied to each required name.
    assert_raises_exact(
        ValueError,
        "schedule requires frontend operation(s) ['prep_plus'], "
        "but CodeSpec declares ['prep0', 'prep1']",
        lambda: os_.require(("prepp",), label="schedule"),
        label="require missing alias canonicalized")


def test_L0_operation_set_require_label_interpolated():
    # the label is interpolated verbatim into the message (kills a label-drop / f-string wrap).
    os_ = OperationSet((OperationSpec("prep0"),))
    assert_raises_exact(
        ValueError,
        "CUSTOM_LABEL requires frontend operation(s) ['prep1'], "
        "but CodeSpec declares ['prep0']",
        lambda: os_.require(("prep1",), label="CUSTOM_LABEL"),
        label="require label interpolation")


# =========================================================================== #
# OperationSet.to_manifest                                                      #
# =========================================================================== #
def test_L0_operation_set_to_manifest_exact_list():
    os_ = OperationSet((OperationSpec("prep0", {"note": "a"}),
                        OperationSpec("final_readout")))
    got = os_.to_manifest()
    expected = [
        {"name": "prep0", "metadata": {"note": "a"}},
        {"name": "final_readout", "metadata": {}},
    ]
    assert got == expected

    def prop(m):
        assert m == expected

    wrong = [
        {"name": "prep0", "metadata": {"note": "a"}},
        {"name": "prep1", "metadata": {}},     # a member drift
    ]
    assert_discriminates(prop, got, wrong, label="OperationSet.to_manifest exact")


# =========================================================================== #
# default_memory_operations                                                     #
# =========================================================================== #
def test_L0_default_memory_operations_exact():
    ops = default_memory_operations()
    # the EXACT ordered (prep0, stabilizer_round, final_readout) tuple; a wrap of any of the
    # three literals would raise at construction (XX<s>XX fails the ALLOWED guard) -> killed.
    assert tuple(o.name for o in ops) == ("prep0", "stabilizer_round", "final_readout")
    assert all(isinstance(o, OperationSpec) for o in ops)
    assert all(o.metadata == {} for o in ops)

    def prop(names):
        assert names == ("prep0", "stabilizer_round", "final_readout")

    assert_discriminates(prop, tuple(o.name for o in ops),
                         ("prep0", "stabilizer_round", "prep1"),
                         label="default_memory_operations exact")


# =========================================================================== #
# as_operation_set                                                              #
# =========================================================================== #
def test_L0_as_operation_set_identity_on_operation_set():
    os_ = _canonical_set()
    # an OperationSet is returned BY IDENTITY (the isinstance-True branch).
    assert as_operation_set(os_) is os_


def test_L0_as_operation_set_wraps_names_and_keeps_specs():
    # a list of NAME strings -> each wrapped via OperationSpec (isinstance-False element arc).
    out = as_operation_set(["prep0", "prep1"])
    assert isinstance(out, OperationSet)
    assert out.names == ("prep0", "prep1")
    # a MIXED [spec, name]: the spec object is kept BY IDENTITY (ternary-if arc), the name is
    # wrapped (ternary-else arc). Kills the ternary always-else (which would re-wrap the spec:
    # OperationSpec(OperationSpec(...)) -> str(spec) not an ALLOWED name -> raise).
    spec = OperationSpec("prep0", {"k": "v"})
    out2 = as_operation_set([spec, "prep1"])
    assert out2.operations[0] is spec
    assert out2.names == ("prep0", "prep1")

    def prop(o):
        assert o.names == ("prep0", "prep1")

    assert_discriminates(prop, out, as_operation_set(["prep0", "final_readout"]),
                         label="as_operation_set wraps names")


# =========================================================================== #
# L1 PROPERTY (Hypothesis)                                                       #
# =========================================================================== #
_CASE = st.sampled_from(
    ["prep0", "PREP0", "  prep0 ", "prep1", "PREP1", "prep_plus", "PREP_PLUS",
     "prep_minus", "stabilizer_round", "STABILIZER_ROUND", "final_readout", "prepp",
     "PREPP", "prepm", " prepm "])


def _independent_canon(name: str) -> str:
    """INDEPENDENT reimplementation of the canonicalization spec (independent constants)."""
    out = str(name).strip().lower()
    out = _ALIASES.get(out, out)
    assert out in _ALLOWED
    return out


@settings(max_examples=200, deadline=None)
@given(name=_CASE)
def test_L1_canonical_matches_independent_and_is_idempotent(name):
    got = canonical_operation_name(name)
    # matches the independent recompute ...
    assert got == _independent_canon(name)
    # ... lands in ALLOWED ...
    assert got in _ALLOWED
    # ... and is idempotent (a canonical name maps to itself).
    assert canonical_operation_name(got) == got


@settings(max_examples=200, deadline=None)
@given(names=st.lists(st.sampled_from(list(_ALLOWED)), min_size=1, max_size=6, unique=True))
def test_L1_operation_set_names_manifest_require_consistent(names):
    os_ = OperationSet(tuple(OperationSpec(n) for n in names))
    # names is exactly the constructed order (INDEPENDENT recompute).
    assert os_.names == tuple(names)
    # to_manifest mirrors names one-for-one.
    assert [d["name"] for d in os_.to_manifest()] == list(names)
    assert all(d["metadata"] == {} for d in os_.to_manifest())
    # require(subset) never raises; require(name not present) raises.
    assert os_.require(tuple(names), label="L") is None
    missing = next((n for n in _ALLOWED if n not in names), None)
    if missing is not None:
        with pytest.raises(ValueError):
            os_.require((missing,), label="L")


@settings(max_examples=100, deadline=None)
@given(names=st.lists(st.sampled_from(list(_ALLOWED)), min_size=2, max_size=6))
def test_L1_operation_set_rejects_duplicates(names):
    # INDEPENDENT recompute: a set constructs iff the names are all distinct.
    specs = tuple(OperationSpec(n) for n in names)
    if len(set(names)) == len(names):
        assert OperationSet(specs).names == tuple(names)
    else:
        with pytest.raises(ValueError, match="duplicate frontend operations"):
            OperationSet(specs)


@settings(max_examples=100, deadline=None)
@given(names=st.lists(st.sampled_from(list(_ALLOWED)), min_size=1, max_size=5, unique=True))
def test_L1_as_operation_set_roundtrips(names):
    built = as_operation_set(list(names))
    # building from names == building explicit specs.
    assert built.names == tuple(names)
    # an OperationSet passes through by identity.
    assert as_operation_set(built) is built

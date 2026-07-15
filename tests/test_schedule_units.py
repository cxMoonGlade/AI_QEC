"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.schedule`` (7 CPU-pure public units: the frozen
dataclass ``ScheduleTemplate`` (``__post_init__`` name + operation canonicalization plus the
non-empty and manifest-consistency guards, ``validate_for``, ``to_manifest``), and the four
module functions ``repeated_memory_schedule`` / ``repeated_memory_schedule_manifest`` /
``canonical_schedule_name`` / ``resolve_schedule_template``; the module imports NEITHER torch
NOR quimb -- ``dataclasses`` + the sibling ``operation.canonical_operation_name`` -- so
out_of_scope is empty).

Current coverage contract: docs/SIMULATOR.md SS12.3/12.4.
``frontend/schedule.py`` is the PUBLIC named-schedule contract a compiler resolves BEFORE it
lowers a ``CodeSpec`` into a record circuit. It is NOT a noise/mechanism model and declares no
physical dynamics: a ``ScheduleTemplate`` names its required frontend operations + declares the
record-layout policy, and the module ships exactly ONE template (``repeated_memory_v1``).

L2 DISCIPLINE (100% coverage != discrimination). The schedule name, the three fixed policy
strings, the required-operation tuple, and every manifest-dict schema/guard message are
HARDCODED here (deliberately NOT imported from src): a mutmut mutation of a module
constant/literal must make the module's output stop matching THIS hardcoded literal -> the pin
fails -> the mutant is killed. Every raising guard is tripped through a real construction/call
route with the EXACT message via ``assert_raises_exact`` (kills the ``XX<s>XX``-wrap / UPPERCASE
case-swap / ``None`` message mutants a substring ``match=`` leaves surviving).

CASE-SWAP note (different from the ``operation`` registry outcome). mutmut 3.6.0
emits BOTH an ``XX<s>XX`` wrap AND an UPPERCASE case-swap per string literal. UNLIKE
``canonical_operation_name`` (which does ``.strip().lower()`` so an already-canonical caller
literal's case-swap is byte-identical after ``.lower()`` -> a genuine equivalent),
``canonical_schedule_name`` does ONLY ``.strip()`` (NO ``.lower()``). So an UPPERCASE case-swap of
the ``"repeated_memory_v1"`` name literal is NOT re-lowered: it makes the name mismatch the
membership guard (``"REPEATED_MEMORY_V1" != "repeated_memory_v1"`` -> raise) and is KILLABLE.
Likewise ``ScheduleTemplate.__post_init__`` cross-checks its own ``to_manifest()`` against
``repeated_memory_schedule_manifest()``: because the required-operation constant is consumed BOTH
canonicalized (through the template) AND raw (through the manifest), a case-swap of that constant
breaks the self-check -> the constructor raises -> killed. There is therefore NO canonicalization
mask here; the only genuine equivalents are the two f-string mutants on the structurally
UNREACHABLE ``AssertionError`` fall-through of ``resolve_schedule_template`` (dead because
``canonical_schedule_name`` already rejects every non-``repeated_memory_v1`` name).

REACHABILITY (PROBE, never ASSERT). ``ScheduleTemplate.__post_init__`` line ``if self.name ==
"repeated_memory_v1"`` is ALWAYS True (the name was just canonicalized, and
``canonical_schedule_name`` returns only that string or raises) -> its False arc is dead; likewise
``resolve_schedule_template``'s ``if name == "repeated_memory_v1"`` is always True so the trailing
``raise AssertionError`` never executes. Both are registered COVERAGE exemptions (branch / raise),
each named as a defensive/forward-compat guard; NEITHER is a mutation gap (the mutants that flip
those comparisons DO execute -- they divert the always-True path into the fall-through, changing an
observable result -- and are killed by the manifest-mismatch / resolve tests below).
"""
from __future__ import annotations

import dataclasses

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_raises_exact
from _support.fixtures import canonical_rep_code_spec

from error_coupling_simulator.frontend.operation import OperationSpec
from error_coupling_simulator.frontend.schedule import (
    ScheduleTemplate,
    canonical_schedule_name,
    repeated_memory_schedule,
    repeated_memory_schedule_manifest,
    resolve_schedule_template,
)

# --------------------------------------------------------------------------- #
# INDEPENDENT hardcoded literals (deliberately NOT imported from the module):  #
# a mutmut mutation of the module's name/policy/required constants must make    #
# the module's output stop matching THESE literals -> the pin fails -> dead.    #
# --------------------------------------------------------------------------- #
_RM_NAME = "repeated_memory_v1"
_RM_REQUIRED = ("prep0", "stabilizer_round", "final_readout")
_RM_DETECTOR = "round_delta_and_final_closure"
_RM_FINAL = "check_and_logical_compatible_basis"
_RM_MANIFEST = {
    "name": _RM_NAME,
    "required_operations": list(_RM_REQUIRED),
    "detector_policy": _RM_DETECTOR,
    "final_readout_policy": _RM_FINAL,
}
# a template whose required_operations != the fixed set fails __post_init__'s self-check; the
# expected/got dicts are rebuilt from INDEPENDENT literals (same key order as the module).
_MISMATCH_ACTUAL = {
    "name": _RM_NAME,
    "required_operations": ["prep0"],
    "detector_policy": _RM_DETECTOR,
    "final_readout_policy": _RM_FINAL,
}
_MISMATCH_MSG = (
    f"schedule_template 'repeated_memory_v1' has fixed compiler semantics; "
    f"expected {_RM_MANIFEST}, got {_MISMATCH_ACTUAL}"
)


def _valid_template() -> ScheduleTemplate:
    """A hand-built VALID template (equal in content to ``repeated_memory_schedule()`` but
    constructed here, so tests do not lean on the module's own builder)."""
    return ScheduleTemplate(_RM_NAME, _RM_REQUIRED, _RM_DETECTOR, _RM_FINAL)


# =========================================================================== #
# canonical_schedule_name                                                       #
# =========================================================================== #
def test_L0_canonical_schedule_name_valid_and_strips():
    # the ONE supported name round-trips; surrounding whitespace is stripped (kills a dropped
    # .strip(): a padded input would then mismatch the membership guard and raise).
    assert canonical_schedule_name("repeated_memory_v1") == "repeated_memory_v1"
    assert canonical_schedule_name("  repeated_memory_v1  ") == "repeated_memory_v1"
    assert canonical_schedule_name("\trepeated_memory_v1\n") == "repeated_memory_v1"


def test_L0_canonical_schedule_name_unsupported_raises_exact():
    # the `!=` guard fires on any other name; the message carries the ORIGINAL name repr + the
    # hardcoded supported list (kills the f-string wrap/case + `supported=[...]` literal mutants).
    assert_raises_exact(
        ValueError,
        "unsupported schedule_template 'bogus'; supported=['repeated_memory_v1']",
        lambda: canonical_schedule_name("bogus"),
        label="canonical_schedule_name unsupported")
    # an EMPTY string is also unsupported (valid vs invalid both exercised -> kills `!=`->`==`).
    assert_raises_exact(
        ValueError,
        "unsupported schedule_template ''; supported=['repeated_memory_v1']",
        lambda: canonical_schedule_name(""),
        label="canonical_schedule_name empty")
    # a PADDED invalid pins that the message uses the ORIGINAL `name!r` (with the spaces), NOT
    # the stripped `out` -- the repr shows '  repeated_memory_v2  ', not 'repeated_memory_v2'.
    assert_raises_exact(
        ValueError,
        "unsupported schedule_template '  repeated_memory_v2  '; supported=['repeated_memory_v1']",
        lambda: canonical_schedule_name("  repeated_memory_v2  "),
        label="canonical_schedule_name original-repr")


def test_L0_canonical_schedule_name_membership_both_directions():
    # `!=` guard exercised BOTH ways: a valid name returns without raising, an invalid one raises.
    assert canonical_schedule_name("repeated_memory_v1") == "repeated_memory_v1"
    with pytest.raises(ValueError):
        canonical_schedule_name("repeated_memory_v2")

    def prop(out):
        assert out == "repeated_memory_v1"

    assert_discriminates(prop, canonical_schedule_name("  repeated_memory_v1 "),
                         "repeated_memory_v2", label="canonical_schedule_name maps")


# =========================================================================== #
# ScheduleTemplate.__post_init__  --  canonicalize + guards + manifest self-check #
# =========================================================================== #
def test_L0_schedule_template_canonicalizes_name_and_operations():
    # a PADDED name + non-canonical (UPPER/mixed) operation inputs both get canonicalized. A
    # successful construction pins name (kills strip + the 'name' setattr-key wrap: under the wrap
    # self.name keeps the padded input and the assert fails) AND the canonical required_operations
    # tuple (kills the 'required_operations' setattr-key wrap: under it the RAW upper names survive
    # -> the manifest self-check mismatches -> the constructor raises -> the test errors).
    t = ScheduleTemplate("  repeated_memory_v1  ",
                         ("PREP0", "Stabilizer_Round", "final_readout"),
                         _RM_DETECTOR, _RM_FINAL)
    assert t.name == "repeated_memory_v1"
    assert t.required_operations == ("prep0", "stabilizer_round", "final_readout")
    assert t.detector_policy == _RM_DETECTOR
    assert t.final_readout_policy == _RM_FINAL


def test_L0_schedule_template_empty_required_raises_exact():
    # empty required_operations -> the first guard raises its EXACT message (kills the message
    # wrap/case AND the `not` operator: without `not`, an empty tuple falls through to the manifest
    # check which raises a DIFFERENT message -> assert_raises_exact still fails -> killed).
    assert_raises_exact(
        ValueError, "ScheduleTemplate requires at least one operation",
        lambda: ScheduleTemplate(_RM_NAME, (), _RM_DETECTOR, _RM_FINAL),
        label="ScheduleTemplate empty required")


def test_L0_schedule_template_empty_detector_raises_exact():
    # a non-empty required list but empty detector_policy -> the detector guard raises (reached
    # only AFTER the required guard passes -> both routes exercised).
    assert_raises_exact(
        ValueError, "ScheduleTemplate detector_policy must be non-empty",
        lambda: ScheduleTemplate(_RM_NAME, ("prep0",), "", _RM_FINAL),
        label="ScheduleTemplate empty detector")


def test_L0_schedule_template_empty_final_raises_exact():
    assert_raises_exact(
        ValueError, "ScheduleTemplate final_readout_policy must be non-empty",
        lambda: ScheduleTemplate(_RM_NAME, ("prep0",), _RM_DETECTOR, ""),
        label="ScheduleTemplate empty final")


def test_L0_schedule_template_manifest_mismatch_raises_exact():
    # name canonicalizes to 'repeated_memory_v1' (always) so the manifest self-consistency guard
    # runs; a template whose required_operations != the fixed set fails it with the EXACT
    # expected/got message (kills the message f-string mutants + the `!=` comparison flip).
    assert_raises_exact(
        ValueError, _MISMATCH_MSG,
        lambda: ScheduleTemplate(_RM_NAME, ("prep0",), _RM_DETECTOR, _RM_FINAL),
        label="ScheduleTemplate manifest mismatch")


# =========================================================================== #
# ScheduleTemplate.to_manifest                                                  #
# =========================================================================== #
def test_L0_schedule_template_to_manifest_exact():
    t = _valid_template()
    got = t.to_manifest()
    assert got == _RM_MANIFEST

    def prop(m):
        assert m == _RM_MANIFEST

    wrong = dict(_RM_MANIFEST)
    wrong["detector_policy"] = "DRIFT"
    assert_discriminates(prop, got, wrong, label="ScheduleTemplate.to_manifest exact")


# =========================================================================== #
# ScheduleTemplate.validate_for                                                 #
# =========================================================================== #
def test_L0_validate_for_all_present_returns_none():
    # a CodeSpec whose operation_set contains the required ops -> require passes -> None.
    spec = canonical_rep_code_spec()
    assert _valid_template().validate_for(spec) is None


def test_L0_validate_for_missing_op_raises_exact():
    # a CodeSpec MISSING an operation -> require raises, and validate_for's label f-string
    # ("schedule_template <name!r>") is interpolated verbatim (kills the label wrap/case-swap).
    spec = dataclasses.replace(
        canonical_rep_code_spec(),
        operations=(OperationSpec("prep0"), OperationSpec("stabilizer_round")))
    assert_raises_exact(
        ValueError,
        "schedule_template 'repeated_memory_v1' requires frontend operation(s) "
        "['final_readout'], but CodeSpec declares ['prep0', 'stabilizer_round']",
        lambda: _valid_template().validate_for(spec),
        label="validate_for missing op")


# =========================================================================== #
# repeated_memory_schedule                                                       #
# =========================================================================== #
def test_L0_repeated_memory_schedule_fields_exact():
    # the module builder returns the fixed template. A wrap of any constant literal makes the
    # constructor raise (name/op fail their guards; a required-op case-swap breaks the manifest
    # self-check); a detector/final case-swap survives construction but is caught by these pins.
    sch = repeated_memory_schedule()
    assert sch.name == "repeated_memory_v1"
    assert sch.required_operations == ("prep0", "stabilizer_round", "final_readout")
    assert sch.detector_policy == "round_delta_and_final_closure"
    assert sch.final_readout_policy == "check_and_logical_compatible_basis"


# =========================================================================== #
# repeated_memory_schedule_manifest                                              #
# =========================================================================== #
def test_L0_repeated_memory_schedule_manifest_exact():
    got = repeated_memory_schedule_manifest()
    assert got == _RM_MANIFEST

    def prop(m):
        assert m == _RM_MANIFEST

    wrong = dict(_RM_MANIFEST)
    wrong["required_operations"] = ["prep0", "stabilizer_round", "prep1"]  # a member drift
    assert_discriminates(prop, got, wrong, label="repeated_memory_schedule_manifest exact")


def test_L0_repeated_memory_roundtrip():
    # the schedule's manifest == the standalone manifest builder == the independent literal.
    assert repeated_memory_schedule().to_manifest() == repeated_memory_schedule_manifest()
    assert repeated_memory_schedule().to_manifest() == _RM_MANIFEST


# =========================================================================== #
# resolve_schedule_template                                                     #
# =========================================================================== #
def test_L0_resolve_identity_on_template():
    # a ScheduleTemplate is returned BY IDENTITY (the isinstance-True branch).
    t = _valid_template()
    assert resolve_schedule_template(t) is t


def test_L0_resolve_from_name():
    # a string name (isinstance-False) is canonicalized then mapped to the builder's template
    # (kills the `name == "repeated_memory_v1"` flip/wrap: under it the always-True branch is
    # skipped and the fall-through AssertionError fires instead of returning a template).
    r = resolve_schedule_template("repeated_memory_v1")
    assert isinstance(r, ScheduleTemplate)
    assert r.to_manifest() == _RM_MANIFEST
    # padded string route -> canonical_schedule_name's .strip() is load-bearing.
    r2 = resolve_schedule_template("  repeated_memory_v1  ")
    assert r2.to_manifest() == _RM_MANIFEST


def test_L0_resolve_unsupported_raises_valueerror():
    # an unsupported name raises ValueError FROM canonical_schedule_name (NOT the AssertionError
    # fall-through, which is structurally unreachable) with the exact unsupported message.
    assert_raises_exact(
        ValueError,
        "unsupported schedule_template 'nope'; supported=['repeated_memory_v1']",
        lambda: resolve_schedule_template("nope"),
        label="resolve unsupported")


# =========================================================================== #
# L1 PROPERTY (Hypothesis)                                                       #
# =========================================================================== #
_WS = st.text(alphabet=" \t\n\r", max_size=4)


@settings(max_examples=200, deadline=None)
@given(pad_l=_WS, pad_r=_WS)
def test_L1_canonical_schedule_name_strips_to_fixed(pad_l, pad_r):
    name = pad_l + "repeated_memory_v1" + pad_r
    got = canonical_schedule_name(name)
    assert got == "repeated_memory_v1"
    # idempotent: the canonical output maps to itself.
    assert canonical_schedule_name(got) == got


@settings(max_examples=200, deadline=None)
@given(bad=st.text(min_size=0, max_size=30).filter(lambda s: s.strip() != "repeated_memory_v1"))
def test_L1_canonical_schedule_name_rejects_non_canonical(bad):
    with pytest.raises(ValueError):
        canonical_schedule_name(bad)


@settings(max_examples=100, deadline=None)
@given(pad_l=_WS, pad_r=_WS)
def test_L1_resolve_from_name_matches_manifest(pad_l, pad_r):
    sch = resolve_schedule_template(pad_l + "repeated_memory_v1" + pad_r)
    # every whitespace variant resolves to a template with the fixed manifest ...
    assert sch.to_manifest() == _RM_MANIFEST
    # ... and a ScheduleTemplate passes through by identity.
    assert resolve_schedule_template(sch) is sch

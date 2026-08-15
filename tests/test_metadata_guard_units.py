"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.metadata_guard`` (4 CPU-pure public units: the
public-artifact ISOLATION-CONTRACT validator ``validate_public_metadata`` and the three
axis1 static-ZZ normalizers ``normalize_axis1_static_zz_couplings`` /
``normalize_axis1_static_zz_calibrations`` / ``axis1_static_zz_calibrations_to_manifest``;
no torch, no quimb -- ``collections.abc`` + ``math`` + plain dict/f-string -- so out_of_scope
is empty).

Current coverage contract: docs/SIMULATOR.md SS12.3/12.4.
``frontend/metadata_guard.py`` owns the downstream-visible public-metadata boundary of the
isolation contract: ``validate_public_metadata`` copies a metadata dict and recurses
(``_validate_keys``) rejecting evaluator/error-model reserved keys FAIL-CLOSED, and the
axis1 static-ZZ helpers normalize public device/schedule couplings + per-edge calibrations.

CURRENT FAIL-CLOSED BEHAVIOR. ``_validate_keys`` recurses fail-closed: a NESTED
``_source_projection_evaluator_audit`` key (inside a sub-dict OR a list element) is REJECTED
while the DECLARED TOP-LEVEL audit transport is allowed ONLY under
``allow_evaluator_audit_transport=True``.

L2 DISCIPLINE (100% coverage != discrimination). Reserved-key rejection is the load-bearing
isolation-contract behavior, so EVERY reserved key (all 8 exact + all 31 parts) is tripped
one-per-call with the EXACT message via ``assert_raises_exact``, keyed off INDEPENDENT
HARDCODED lists (NOT imported from src): a mutated src constant no longer matches the
hardcoded key -> no raise -> the exact-message pin fails -> mutant killed. Key normalization
(``.lower()``/``.replace('-','_')``/``.replace(' ','_')``) is killed by upper-case / hyphen /
space variants of a reserved key that must still normalize to a match. The audit transport is
pinned BOTH ways (allowed under opt-in, rejected fail-closed by default) at the top level AND
nested (the KILLER). Every normalizer output is pinned vs an INDEPENDENT recompute and every
validation guard is tripped through EVERY route reaching it (bad-edge via BOTH ``or`` operands,
boundary ``<=``/``>=`` cases, non-str non-Sequence ``int`` probes) with the exact message.
"""
from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_raises_exact

from error_coupling_simulator.frontend.metadata_guard import (
    _validate_keys,
    axis1_static_zz_calibrations_to_manifest,
    normalize_axis1_static_zz_calibrations,
    normalize_axis1_static_zz_couplings,
    validate_public_metadata,
)

# --------------------------------------------------------------------------- #
# INDEPENDENT reserved-key lists (HARDCODED -- deliberately NOT imported from   #
# the module: a mutmut string mutation of a src constant must make src STOP     #
# matching the hardcoded key -> no raise -> the exact-message pin fails ->       #
# mutant killed. Importing the src constant would move WITH the mutation and     #
# leave it surviving).                                                           #
# --------------------------------------------------------------------------- #
_EXACT_KEYS = (
    "axis", "axis1", "axis2", "baseline", "cudaqx", "error", "noise_model", "si1000",
)
_PART_KEYS = (
    "analog_truth", "axis1_error", "axis2_error", "baseline_noise", "cudaqx_noise",
    "cudaqx_error", "channel_truth", "dem_error_model", "error_ids", "error_model",
    "exact_channel", "evaluator_truth", "ground_truth", "hidden_state",
    "joint_lindbladian_truth", "kraus", "leakage_trace", "mechanism_truth", "oracle",
    "process_matrix", "ptm", "si1000_noise", "si1000_error", "source_binding",
    "source_fanout", "source_payload", "source_process", "source_trace",
    "source_timeline", "source_trajectory", "teach" + "er_id",
)
_AUDIT_KEY = "_source_projection_evaluator_audit"
_COUPLINGS_LABEL = "axis1_static_zz_couplings"
_CALIBRATIONS_LABEL = "axis1_static_zz_calibrations"


# --------------------------------------------------------------------------- #
# INDEPENDENT message templates (reconstructed from the contract text, NOT     #
# read off the module -- an exact-string pin that a message-content mutant      #
# (XX-wrap / case / None) fails).                                               #
# --------------------------------------------------------------------------- #
def _exact_key_msg(path: str, key: str, normalized: str) -> str:
    return ("public-artifact metadata cannot contain evaluator/error-model semantics; "
            f"reserved key {path}.{key} matches exact key {normalized!r}. "
            "Put runnable noise in NoiseSpec and evaluator truth in evaluator_sidecars.")


def _part_key_msg(path: str, key: str, reserved: str) -> str:
    return ("public-artifact metadata cannot contain evaluator truth; "
            f"reserved key {path}.{key} matches {reserved!r}. "
            "Use evaluator_sidecars with visibility='evaluator_only'.")


def _audit_root_msg(path: str, key: str) -> str:
    return ("public-artifact metadata cannot carry the evaluator-only audit transport; "
            f"reserved key {path}.{key} is an internal source-projection transport "
            "(permitted only on the transient noisy CircuitIR), not public-artifact "
            "metadata. Use evaluator_sidecars with visibility='evaluator_only'.")


def _audit_nested_msg(path: str, key: str) -> str:
    return ("public-artifact metadata cannot nest the evaluator-only audit transport; "
            f"reserved key {path}.{key} is permitted only at the top level of the transient "
            "noisy CircuitIR. Use evaluator_sidecars with visibility='evaluator_only'.")


def _accepts(md, **kw):
    """A KILLER-pattern property (AssertionError on rejection) for assert_discriminates:
    validate_public_metadata must ACCEPT ``md`` (return a dict, raise no ValueError)."""
    def prop(_md):
        try:
            out = validate_public_metadata(_md, **kw)
        except ValueError as exc:  # a reject -> the property fails (has teeth)
            raise AssertionError(f"unexpectedly rejected: {exc}")
        assert isinstance(out, dict)
    return prop


# =========================================================================== #
# validate_public_metadata  --  clean / copy / None                            #
# =========================================================================== #
def test_L0_validate_none_and_empty_return_empty_copy():
    # metadata=None -> `dict(None or {})` == {} ; kills the `metadata or {}` -> `and` mutant
    # (None and {} == None -> dict(None) raises TypeError; the original returns {}).
    assert validate_public_metadata(None) == {}
    assert validate_public_metadata({}) == {}
    out = validate_public_metadata(None)
    assert isinstance(out, dict) and out == {}


def test_L0_validate_clean_returns_distinct_copy_all_recursion_arms():
    # clean dict exercises the dict arm (nested dict), the list/tuple arm (nested list), and
    # the scalar arm (int/str values recurse to the no-op), and runs the reserved-part loop to
    # COMPLETION on every key (no match) -- covers the loop-exit arc.
    md = {"alpha": 1, "beta": {"gamma": 2}, "delta": [1, 2, {"epsilon": 3}], "note": "hi"}
    out = validate_public_metadata(md)
    assert out == md                       # returned value equals the input ...
    assert out is not md                   # ... but is a DISTINCT (shallow) copy
    # discriminate: the acceptance property holds for the clean dict and FAILS for one that
    # inserts a reserved key (proves the property is not vacuous).
    assert_discriminates(_accepts(md), md, dict(md, kraus={"K": 1}),
                         label="validate accepts clean, rejects reserved")


def test_L1_validate_tuple_value_and_custom_label():
    # a TUPLE value also recurses via the (list, tuple) arm; a custom label threads into the
    # path (kills a mutant that ignores the passed label).
    assert validate_public_metadata({"edges": (0, 1, 2)}, label="md") == {"edges": (0, 1, 2)}
    assert_raises_exact(
        ValueError, _exact_key_msg("md", "axis1", "axis1"),
        lambda: validate_public_metadata({"axis1": 1}, label="md"),
        label="custom-label exact reject")


# =========================================================================== #
# validate_public_metadata  --  every reserved key rejected (exact message)     #
# =========================================================================== #
@pytest.mark.parametrize("key", _EXACT_KEYS)
def test_L0_validate_rejects_every_exact_reserved_key(key):
    # each of the 8 exact keys -> the exact-key ValueError with the exact message (default
    # label 'metadata'). Independent hardcoded key -> a mutated src exact-key tuple element
    # stops matching -> no raise -> this pin fails -> mutant killed.
    assert_raises_exact(
        ValueError, _exact_key_msg("metadata", key, key),
        lambda: validate_public_metadata({key: 1}),
        label=f"exact reserved key {key!r}")


@pytest.mark.parametrize("key", _PART_KEYS)
def test_L0_validate_rejects_every_reserved_part_key(key):
    # each of the 31 reserved parts as a metadata key (key == part -> the part matches itself
    # first) -> the reserved-part ValueError with the exact message.
    assert_raises_exact(
        ValueError, _part_key_msg("metadata", key, key),
        lambda: validate_public_metadata({key: 1}),
        label=f"reserved part key {key!r}")


def test_L0_validate_key_normalization_upper_hyphen_space():
    # `.lower()`: an UPPER-CASE exact key must still normalize+match (kills a removed .lower()).
    assert_raises_exact(
        ValueError, _exact_key_msg("metadata", "AXIS", "axis"),
        lambda: validate_public_metadata({"AXIS": 1}),
        label="upper-case exact key normalization")
    # `.replace('-','_')`: a HYPHEN reserved-part key must still normalize+match.
    assert_raises_exact(
        ValueError, _part_key_msg("metadata", "ground-truth", "ground_truth"),
        lambda: validate_public_metadata({"ground-truth": 1}),
        label="hyphen reserved-part normalization")
    # `.replace(' ','_')`: a SPACE reserved-exact key must still normalize+match.
    assert_raises_exact(
        ValueError, _exact_key_msg("metadata", "noise model", "noise_model"),
        lambda: validate_public_metadata({"noise model": 1}),
        label="space exact-key normalization")


def test_L0_validate_reserved_part_via_substring_key():
    # a key that CONTAINS a reserved part as a substring (not equal) -> matches that part.
    # 'my_ground_truth_blob' -> normalized contains 'ground_truth' -> part match.
    key = "my_ground_truth_blob"
    assert_raises_exact(
        ValueError, _part_key_msg("metadata", key, "ground_truth"),
        lambda: validate_public_metadata({key: 1}),
        label="substring reserved-part key")


# =========================================================================== #
# validate_public_metadata  --  the audit transport (top-level + nested KILLER) #
# =========================================================================== #
def test_L0_validate_audit_transport_allowed_only_under_optin_at_root():
    # TOP-LEVEL audit key + opt-in -> ALLOWED: the subtree is skipped (its inner axis-2 key is
    # NOT recursed), the copy is returned UNCHANGED. Pins the is_root & allow_audit `continue`.
    md = {_AUDIT_KEY: {"axis2_error": {"p": 0.1}}, "note": "clean"}
    out = validate_public_metadata(md, allow_evaluator_audit_transport=True)
    assert out == md and out is not md
    # SAME input WITHOUT the opt-in (default fail-closed) -> REJECTED with the exact 'cannot
    # carry' message. Kills allow-default=True and the `is_root and allow` -> `or` mutant.
    assert_raises_exact(
        ValueError, _audit_root_msg("metadata", _AUDIT_KEY),
        lambda: validate_public_metadata(md),
        label="top-level audit rejected without opt-in")


def test_L0_validate_nested_audit_key_in_subdict_rejected_KILLER():
    # A NESTED audit key inside a SUB-DICT is rejected fail-closed at
    # is_root=False (line 283, 'cannot nest'), reached AT the audit boundary -- the exact
    # message references metadata.foo._source... proving it fired there (not on the inner key).
    wrong = {"foo": {_AUDIT_KEY: {"axis2_error": {"p": 0.1}}}}
    assert_raises_exact(
        ValueError, _audit_nested_msg("metadata.foo", _AUDIT_KEY),
        lambda: validate_public_metadata(wrong),
        label="nested-in-subdict audit rejected")
    # discriminate against a clean-nested control of the SAME shape without the audit key.
    clean = {"foo": {"benign": {"p": 0.1}}}
    assert_discriminates(_accepts(clean), clean, wrong, label="nested-subdict audit discriminates")


def test_L0_validate_nested_audit_key_in_list_element_rejected_KILLER():
    # ... and inside a LIST element (exercises the (list, tuple) recursion arm reaching the
    # nested dict at is_root=False). Path metadata.foo[0]._source... .
    wrong = {"foo": [{_AUDIT_KEY: {"ground_truth": 1}}]}
    assert_raises_exact(
        ValueError, _audit_nested_msg("metadata.foo[0]", _AUDIT_KEY),
        lambda: validate_public_metadata(wrong),
        label="nested-in-list audit rejected")
    clean = {"foo": [{"benign": 1}]}
    assert_discriminates(_accepts(clean), clean, wrong, label="nested-list audit discriminates")


def test_L0_validate_nested_audit_not_rescued_by_optin():
    # allow_evaluator_audit_transport applies ONLY at the root: a NESTED audit key is still
    # rejected even WITH the opt-in (line 303 recursion passes is_root=False and does NOT
    # thread allow through) -- kills the `is_root=False`->`True` mutant on the recursion call.
    wrong = {"foo": {_AUDIT_KEY: {}}}
    assert_raises_exact(
        ValueError, _audit_nested_msg("metadata.foo", _AUDIT_KEY),
        lambda: validate_public_metadata(wrong, allow_evaluator_audit_transport=True),
        label="nested audit not rescued by opt-in")


def test_L0_validate_top_level_audit_with_optin_but_nested_reserved_is_smuggled_then_blocked():
    # Faithfulness illustration of the closed bypass: with opt-in, a TOP-LEVEL audit subtree is
    # skipped (its inner reserved key is NOT validated -- the DECLARED transport). WITHOUT
    # opt-in the SAME top-level audit key is rejected outright.
    md = {_AUDIT_KEY: {"kraus": [[1, 0], [0, 1]]}}
    # opt-in: returned unchanged (subtree skipped, inner 'kraus' not raised on)
    assert validate_public_metadata(md, allow_evaluator_audit_transport=True) == md
    # default: the top-level audit key itself is rejected before the subtree is reached
    assert_raises_exact(
        ValueError, _audit_root_msg("metadata", _AUDIT_KEY),
        lambda: validate_public_metadata(md),
        label="top-level audit default-reject")


# =========================================================================== #
# normalize_axis1_static_zz_couplings                                           #
# =========================================================================== #
def _canon_edges(edges):
    """INDEPENDENT recompute: canonicalize each edge (sorted endpoints), dedupe, sort."""
    return tuple(sorted({tuple(sorted((int(a), int(b)))) for a, b in edges}))


def test_L0_couplings_empty_inputs_return_empty():
    assert normalize_axis1_static_zz_couplings(None) == ()
    assert normalize_axis1_static_zz_couplings(()) == ()
    # an empty LIST is not caught by the `in (None, ())` early return: it runs the full path
    # (loop over nothing -> dedup check -> tuple(sorted([]))) and still returns ().
    assert normalize_axis1_static_zz_couplings([]) == ()


def test_L0_couplings_canonicalizes_sorts_dedup_pins():
    # swap (a>b) canonicalized, and the whole list sorted -- pinned vs an INDEPENDENT recompute.
    got = normalize_axis1_static_zz_couplings([(3, 2), (0, 1)])
    assert got == _canon_edges([(3, 2), (0, 1)]) == ((0, 1), (2, 3))
    assert normalize_axis1_static_zz_couplings([(1, 0)]) == ((0, 1),)   # pure swap
    # an endpoint == 0 is VALID (kills `q < 0` -> `q <= 0`); distinct endpoints valid (kills
    # `a == b` -> `a != b`); a valid 2-tuple must NOT raise (kills `len != 2` -> `== 2`).
    assert normalize_axis1_static_zz_couplings([(0, 4), (2, 1)]) == ((0, 4), (1, 2))

    def prop(edges):
        assert normalize_axis1_static_zz_couplings(edges) == ((0, 1), (2, 3))

    assert_discriminates(prop, [(3, 2), (0, 1)], [(3, 2), (0, 2)], label="couplings canonical/sort")


def test_L0_couplings_num_qubits_range_and_positive_guards():
    # in-range with num_qubits set: no raise (also exercises the nq-not-None `and` false arm).
    assert normalize_axis1_static_zz_couplings([(0, 2)], num_qubits=3) == ((0, 2),)
    # endpoint == nq (boundary) is OUT of range -> raise (kills `>=` -> `>`).
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL}[0] endpoint 3 outside [0, 3)",
        lambda: normalize_axis1_static_zz_couplings([(0, 3)], num_qubits=3),
        label="couplings endpoint out of range")
    # num_qubits == 0 (boundary) is non-positive -> raise (kills `<= 0` -> `< 0`).
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL} num_qubits must be positive, got 0",
        lambda: normalize_axis1_static_zz_couplings([(0, 1)], num_qubits=0),
        label="couplings num_qubits==0")
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL} num_qubits must be positive, got -2",
        lambda: normalize_axis1_static_zz_couplings([(0, 1)], num_qubits=-2),
        label="couplings num_qubits negative")


def test_L0_couplings_bad_container_and_edge_guards():
    # top-level container: a NON-Sequence int (first `or` operand) AND a str (second operand).
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL} must be a sequence of two-qubit edges",
        lambda: normalize_axis1_static_zz_couplings(5),
        label="couplings non-sequence int")
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL} must be a sequence of two-qubit edges",
        lambda: normalize_axis1_static_zz_couplings("01"),
        label="couplings str container")
    # per-edge: a NON-Sequence int edge (first operand) AND a str edge (second operand).
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL}[0] must be a two-qubit edge",
        lambda: normalize_axis1_static_zz_couplings([5]),
        label="couplings non-sequence edge int")
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL}[1] must be a two-qubit edge",
        lambda: normalize_axis1_static_zz_couplings([(0, 1), "xy"]),
        label="couplings str edge")
    # wrong arity, duplicate endpoint, negative endpoint, duplicate edge.
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL}[0] must contain exactly two qubit indices",
        lambda: normalize_axis1_static_zz_couplings([(0, 1, 2)]),
        label="couplings arity!=2")
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL}[0] has duplicate endpoint 2",
        lambda: normalize_axis1_static_zz_couplings([(2, 2)]),
        label="couplings duplicate endpoint")
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL}[0] endpoint -1 must be non-negative",
        lambda: normalize_axis1_static_zz_couplings([(-1, 0)]),
        label="couplings negative endpoint")
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL} must not contain duplicate edges",
        lambda: normalize_axis1_static_zz_couplings([(0, 1), (1, 0)]),
        label="couplings duplicate edge")


# =========================================================================== #
# normalize_axis1_static_zz_calibrations                                        #
# =========================================================================== #
def test_L0_calibrations_empty_inputs_return_empty():
    assert normalize_axis1_static_zz_calibrations(None) == {}
    assert normalize_axis1_static_zz_calibrations(()) == {}
    assert normalize_axis1_static_zz_calibrations({}) == {}


def test_L0_calibrations_mapping_scalar_and_dict_values_pins():
    # Mapping arm (ternary True): scalar value -> zeta from the value, epistemic default 'c';
    # dict value -> zeta + explicit class; keys canonicalized + sorted; INT zeta coerced to
    # float. Pinned vs an INDEPENDENT literal.
    out = normalize_axis1_static_zz_calibrations(
        {(1, 0): 1, (2, 3): {"zeta_rad_per_ns": 0.25, "epistemic_class": "b"}})
    assert list(out.items()) == [
        ((0, 1), {"zeta_rad_per_ns": 1.0, "epistemic_class": "c"}),
        ((2, 3), {"zeta_rad_per_ns": 0.25, "epistemic_class": "b"})]
    # the scalar-value zeta is a FLOAT (kills a removed float() coercion)
    assert type(out[(0, 1)]["zeta_rad_per_ns"]) is float

    def prop(cal):
        got = normalize_axis1_static_zz_calibrations(cal)
        assert got[(0, 1)]["epistemic_class"] == "c"

    assert_discriminates(
        prop, {(0, 1): 1}, {(0, 1): {"zeta_rad_per_ns": 1, "epistemic_class": "b"}},
        label="calibrations default epistemic_class 'c'")


def test_L0_calibrations_sequence_records_edge_and_qubits_fallback():
    # Sequence arm (ternary False): a record with 'edge', and a record whose edge comes from
    # the 'qubits' fallback (record.get('edge', record.get('qubits'))).
    out = normalize_axis1_static_zz_calibrations([
        {"edge": (0, 1), "zeta_rad_per_ns": 0.5},
        {"qubits": (3, 2), "zeta_rad_per_ns": 0.25, "epistemic_class": "b"}])
    assert list(out.items()) == [
        ((0, 1), {"zeta_rad_per_ns": 0.5, "epistemic_class": "c"}),
        ((2, 3), {"zeta_rad_per_ns": 0.25, "epistemic_class": "b"})]


def test_L0_calibrations_string_mapping_keys_parse():
    # mapping keys parsed from strings: hyphen and comma separators.
    out = normalize_axis1_static_zz_calibrations({"1-0": 0.5, "2,3": 0.25})
    assert list(out.items()) == [
        ((0, 1), {"zeta_rad_per_ns": 0.5, "epistemic_class": "c"}),
        ((2, 3), {"zeta_rad_per_ns": 0.25, "epistemic_class": "c"})]


def test_L0_calibrations_declared_edges_gate():
    # declared_edges provided (line 147 True): an edge IN the declared set passes ...
    assert normalize_axis1_static_zz_calibrations(
        {(0, 1): 0.5}, declared_edges=[(0, 1)]) == {
            (0, 1): {"zeta_rad_per_ns": 0.5, "epistemic_class": "c"}}
    # ... an UNDECLARED edge is rejected with the exact message.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0] edge {(2, 3)!r} is not declared in {_COUPLINGS_LABEL}",
        lambda: normalize_axis1_static_zz_calibrations({(2, 3): 0.5}, declared_edges=[(0, 1)]),
        label="calibrations undeclared edge")


def test_L0_calibrations_zeta_and_class_guards():
    # duplicate edge calibration (two string keys collapsing to the same canonical edge).
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL} must not contain duplicate edge calibration {(0, 1)!r}",
        lambda: normalize_axis1_static_zz_calibrations([
            {"edge": (0, 1), "zeta_rad_per_ns": 0.1},
            {"edge": (1, 0), "zeta_rad_per_ns": 0.2}]),
        label="calibrations duplicate edge")
    # zeta == 0.0 is VALID (boundary; kills `zeta < 0.0` -> `<= 0.0`).
    assert normalize_axis1_static_zz_calibrations({(0, 1): 0.0}) == {
        (0, 1): {"zeta_rad_per_ns": 0.0, "epistemic_class": "c"}}
    # non-finite zeta (first `or` operand: inf) AND negative zeta (second operand) both raise.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0].zeta_rad_per_ns must be finite and non-negative",
        lambda: normalize_axis1_static_zz_calibrations({(0, 1): float("inf")}),
        label="calibrations non-finite zeta")
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0].zeta_rad_per_ns must be finite and non-negative",
        lambda: normalize_axis1_static_zz_calibrations({(0, 1): -0.5}),
        label="calibrations negative zeta")
    # bad epistemic_class -> raise; 'b' and 'c' accepted.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0].epistemic_class must be 'b' or 'c'",
        lambda: normalize_axis1_static_zz_calibrations(
            {(0, 1): {"zeta_rad_per_ns": 0.1, "epistemic_class": "x"}}),
        label="calibrations bad epistemic_class")


def test_L0_calibrations_bad_container_and_record_guards():
    # not a Mapping and not a Sequence (int) -> the from_sequence container guard (first `or`
    # operand); a str -> the second operand.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL} must be a sequence of calibration records",
        lambda: normalize_axis1_static_zz_calibrations(5),
        label="calibrations non-sequence int")
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL} must be a sequence of calibration records",
        lambda: normalize_axis1_static_zz_calibrations("abc"),
        label="calibrations str container")
    # a sequence element that is not a Mapping -> record guard.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0] must be a calibration record",
        lambda: normalize_axis1_static_zz_calibrations([5]),
        label="calibrations non-mapping record")
    # a record with neither 'edge' nor 'qubits' -> missing-edge guard.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0] must contain 'edge'",
        lambda: normalize_axis1_static_zz_calibrations([{"zeta_rad_per_ns": 0.1}]),
        label="calibrations record missing edge")
    # a record missing 'zeta_rad_per_ns' -> missing-zeta guard.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0] must contain 'zeta_rad_per_ns'",
        lambda: normalize_axis1_static_zz_calibrations([{"edge": (0, 1)}]),
        label="calibrations record missing zeta")


def test_L0_calibrations_mapping_key_parse_guards():
    # str mapping key with the wrong number of parts (first `or` operand: 1 part) AND an empty
    # part (second operand: '0,' -> ['0','']).
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL} mapping key {'0'!r} must encode two qubits",
        lambda: normalize_axis1_static_zz_calibrations({"0": 0.1}),
        label="calibrations str key one part")
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL} mapping key {'0,'!r} must encode two qubits",
        lambda: normalize_axis1_static_zz_calibrations({"0,": 0.1}),
        label="calibrations str key empty part")
    # a sequence mapping key of the wrong length (len != 2).
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL} mapping key {(0, 1, 2)!r} must contain two qubits",
        lambda: normalize_axis1_static_zz_calibrations({(0, 1, 2): 0.1}),
        label="calibrations seq key len!=2")
    # a mapping key that is NEITHER a str NOR a Sequence (int) -> the final parse raise (kills
    # the `isinstance Sequence and not str/bytes` `and` -> `or`, which would try len(int)).
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL} mapping key {5!r} must encode two qubits",
        lambda: normalize_axis1_static_zz_calibrations({5: 0.1}),
        label="calibrations int mapping key")


# =========================================================================== #
# axis1_static_zz_calibrations_to_manifest                                      #
# =========================================================================== #
def test_L0_to_manifest_exact_records():
    # exact manifest list (edges canonicalized+sorted, scalar-value edge defaults class 'c').
    got = axis1_static_zz_calibrations_to_manifest(
        {(1, 0): {"zeta_rad_per_ns": 0.5, "epistemic_class": "b"}, (2, 3): 0.25})
    assert got == [
        {"edge": [0, 1], "zeta_rad_per_ns": 0.5, "epistemic_class": "b"},
        {"edge": [2, 3], "zeta_rad_per_ns": 0.25, "epistemic_class": "c"}]
    # the edge is a JSON-safe LIST, not a tuple.
    assert type(got[0]["edge"]) is list

    def prop(cal):
        assert axis1_static_zz_calibrations_to_manifest(cal)[0]["epistemic_class"] == "b"

    assert_discriminates(
        prop,
        {(0, 1): {"zeta_rad_per_ns": 0.5, "epistemic_class": "b"}},
        {(0, 1): {"zeta_rad_per_ns": 0.5, "epistemic_class": "c"}},
        label="to_manifest epistemic_class")


def test_L0_to_manifest_none_and_empty():
    # `calibrations or {}`: None and {} both -> []. A NON-EMPTY dict is what kills the
    # `or` -> `and` mutant (None-alone is equivalent since normalize(None)==normalize({})==[]).
    assert axis1_static_zz_calibrations_to_manifest(None) == []
    assert axis1_static_zz_calibrations_to_manifest({}) == []
    assert axis1_static_zz_calibrations_to_manifest({(0, 1): 0.5}) == [
        {"edge": [0, 1], "zeta_rad_per_ns": 0.5, "epistemic_class": "c"}]


# =========================================================================== #
# L2 mutation-hardening: num_qubits/label THREADING + private seams             #
# (each kills a specific surviving mutant identified via mutants/ diffs)         #
# =========================================================================== #
def test_L2_couplings_num_qubits_one_is_positive_boundary():
    # num_qubits==1 is POSITIVE (the `nq <= 0` guard must NOT fire): the raise instead comes
    # from the endpoint-range check. Kills the `nq <= 0` -> `nq <= 1` mutant (which would raise
    # the 'must be positive, got 1' message here instead of the out-of-range message).
    assert_raises_exact(
        ValueError, f"{_COUPLINGS_LABEL}[0] endpoint 1 outside [0, 1)",
        lambda: normalize_axis1_static_zz_couplings([(0, 1)], num_qubits=1),
        label="couplings num_qubits==1 boundary")


def test_L2_calibrations_num_qubits_threads_into_edge_range_check():
    # num_qubits is threaded (nq = int(num_qubits)) into the per-edge range check with the
    # '<label>[i].edge' label. An out-of-range edge raises that EXACT message. Kills the
    # nq=None / int(None) / edge-normalize num_qubits=None-or-removed / edge-normalize
    # label=None-or-removed mutants (each would either not raise, raise TypeError, or raise a
    # DIFFERENT label/message).
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}[0].edge[0] endpoint 5 outside [0, 3)",
        lambda: normalize_axis1_static_zz_calibrations({(0, 5): 0.1}, num_qubits=3),
        label="calibrations num_qubits threaded into edge range")
    # a valid IN-RANGE edge with num_qubits set must return normally (kills int(None), which
    # would raise TypeError even on the happy path).
    assert normalize_axis1_static_zz_calibrations({(0, 2): 0.1}, num_qubits=3) == {
        (0, 2): {"zeta_rad_per_ns": 0.1, "epistemic_class": "c"}}


def test_L2_calibrations_declared_edges_range_checked_with_label():
    # the declared_edges normalize is called with num_qubits=nq and the
    # '<label>.declared_edges' label: an out-of-range declared edge raises that EXACT message
    # BEFORE the undeclared-edge check. Kills the declared num_qubits=None-or-removed (-> the
    # 'not declared' message instead) and declared label=None-or-removed (-> a different label)
    # mutants.
    assert_raises_exact(
        ValueError, f"{_CALIBRATIONS_LABEL}.declared_edges[0] endpoint 4 outside [0, 3)",
        lambda: normalize_axis1_static_zz_calibrations(
            {(0, 1): 0.1}, num_qubits=3, declared_edges=[(0, 4)]),
        label="calibrations declared_edges range-checked")


def test_L2_calibrations_string_key_internal_space_is_stripped():
    # `.replace(' ', '')` strips an INTERNAL space inside a multi-digit token so '1 0,2' parses
    # as edge (10, 2) -> canonical (2, 10). Kills the replace(' ','') string mutants
    # (replace('XX XX','') no-op and replace(' ','XXXX')), each of which leaves/inserts junk so
    # int(...) raises instead of returning this exact edge. (int() strips BOUNDARY whitespace,
    # so only an internal space discriminates.)
    assert normalize_axis1_static_zz_calibrations({"1 0,2": 0.5}) == {
        (2, 10): {"zeta_rad_per_ns": 0.5, "epistemic_class": "c"}}


def test_L2_validate_keys_default_allow_audit_transport_is_false():
    # _validate_keys' default allow_audit_transport is False (fail-closed): a ROOT audit key
    # with the default (no opt-in) is REJECTED. Probed on the private seam directly at
    # is_root=True (the only route where the default is OBSERVED -- the recursion sites pass
    # is_root=False, where allow is never read). Kills the `= False` -> `= True` default mutant.
    assert_raises_exact(
        ValueError, _audit_root_msg("m", _AUDIT_KEY),
        lambda: _validate_keys({_AUDIT_KEY: {}}, path="m", is_root=True),
        label="private _validate_keys default allow=False")


def test_L2_validate_audit_continue_keeps_scanning_siblings():
    # the allowed ROOT audit key uses `continue` (skip THIS key, keep scanning) not `break`
    # (stop): a reserved SIBLING key AFTER the audit key is still rejected. Kills the
    # `continue` -> `break` mutant (which would stop the loop and let 'kraus' through).
    assert_raises_exact(
        ValueError, _part_key_msg("metadata", "kraus", "kraus"),
        lambda: validate_public_metadata(
            {_AUDIT_KEY: {"x": 1}, "kraus": 1}, allow_evaluator_audit_transport=True),
        label="audit continue keeps scanning siblings")


# =========================================================================== #
# L1 PROPERTY (Hypothesis)                                                       #
# =========================================================================== #
@settings(max_examples=200, deadline=None)
@given(pairs=st.lists(
    st.tuples(st.integers(0, 9), st.integers(0, 9)).filter(lambda e: e[0] != e[1]),
    min_size=0, max_size=8))
def test_L1_couplings_output_is_sorted_canonical_deduped(pairs):
    # feed a canonically-UNIQUE set of edges (some possibly swapped) so the duplicate-edge
    # guard does not fire; the output must equal the INDEPENDENT sorted-canonical set.
    canon = {tuple(sorted(e)) for e in pairs}
    # rebuild a feed list with an arbitrary (possibly reversed) orientation per canonical edge
    feed = [((b, a) if (a + b) % 2 else (a, b)) for (a, b) in canon]
    out = normalize_axis1_static_zz_couplings(feed)
    assert out == tuple(sorted(canon))
    # every emitted edge is ordered a<b, endpoints non-negative, and the tuple is sorted.
    assert all(a < b and a >= 0 for a, b in out)
    assert list(out) == sorted(out)


@settings(max_examples=150, deadline=None)
@given(
    edges=st.lists(st.integers(0, 9), min_size=0, max_size=6, unique=True),
    zeta=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False))
def test_L1_calibrations_roundtrip_through_manifest(edges, zeta):
    # build distinct canonical edges (i, i+10) style to guarantee uniqueness, calibrate each,
    # normalize, and round-trip through to_manifest.
    cal = {(i, i + 10): zeta for i in edges}
    norm = normalize_axis1_static_zz_calibrations(cal)
    manifest = axis1_static_zz_calibrations_to_manifest(cal)
    # manifest edges are sorted and match the normalized keys; zetas are the (float) input.
    assert [tuple(r["edge"]) for r in manifest] == sorted((i, i + 10) for i in edges)
    for r in manifest:
        assert r["zeta_rad_per_ns"] == float(zeta)
        assert r["epistemic_class"] == "c"
    assert len(norm) == len(edges)


@settings(max_examples=100, deadline=None)
@given(keys=st.lists(st.sampled_from(["a", "bb", "ccc", "layout", "coords", "notes"]),
                     min_size=0, max_size=6, unique=True))
def test_L1_validate_clean_keys_return_equal_copy(keys):
    md = {k: i for i, k in enumerate(keys)}
    out = validate_public_metadata(md)
    assert out == md
    assert out is not md or md == {}   # a distinct object (an empty dict may compare equal-ident)


@settings(max_examples=100, deadline=None)
@given(key=st.sampled_from(_PART_KEYS))
def test_L1_validate_every_part_key_rejected(key):
    # property form of the per-part reject: no clean-looking wrapper lets a reserved part pass.
    with pytest.raises(ValueError):
        validate_public_metadata({key: {"nested": 1}})

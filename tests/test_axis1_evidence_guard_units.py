"""Stage-D batch ``axis1_evidence_guard`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.axis1_evidence_guard`` (3 LIVE public units, CPU-pure).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md). The module is the
OUTPUT-side claim-scan + verdict de-overload (finish-plan step6_a): the OUTPUT mirror of the
isolation contract that keeps the simulator from EMITTING an Axis-1 ``*_evidence`` /
``*_certification`` manifest that overclaims (asserts an exact-channel / PTM / Kraus /
teacher-ID / source-timeline / DEM / production result it did not produce) or labels a
non-executed contract surface as a passing run. CPU-PURE (string / dict structure inspection;
imports collections.abc + typing, NEITHER torch NOR quimb) => FULL treatment (L0 100%
stmt+branch, L1 property, L2 mutmut >= 0.90).

  UNIT                              L0 branch surface                        L1/KILLER value pin
  ----                              -----------------                        -------------------
  manifest_is_executed              top-level *_executed True/False;         pinned to an INDEPENDENT
                                    honest-claim loop True/False; nested     from-scratch executed
                                    executed bool/non-bool; qualifier        predicate over Hypothesis
                                    or-chain True/False; final return        manifests + exact arcs
  validate_axis1_evidence_manifest  non-Mapping TypeError; walk continue     forbidden-True rejected
                                    vs non-bool raise vs True-overclaim      (every family, message
                                    vs False; present-and-False compound;    pins the returned family)
                                    verdict W-J compound; return copy        + verdict<=>execution +
                                                                             constant value-pins
  axis1_contract_verdict            not-valid; backend-or-oracle;            exact verdict string for
                                    contract_only fallthrough                all 8 (valid,be,oe) combos

THE PRIOR-BATCH LESSON (certify: 100% coverage at ~0.75 kill because it asserted
VERDICTS/SHAPES, not VALUES). Here every load-bearing guard is proved with
``assert_discriminates`` (HOLDS for the real object, FAILS for a named sabotage), and the
load-bearing POLICY CONSTANTS (FORBIDDEN_CLAIM_FAMILIES, HONEST_EXECUTION_CLAIMS,
_EVIDENCE_SCHEMA_TOKENS, VERDICT_*) are value-pinned against an INDEPENDENT hard-coded expected
copy so a wrong / dropped / reworded family string is caught -- not a boolean/shape assert. Each
family, honest claim, and schema token also carries a BEHAVIORAL parametrized case, and
``manifest_is_executed`` is pinned to an INDEPENDENT re-implementation of the executed predicate.

The module's PRIVATE helpers (_normalize_key, _forbidden_family_for, _walk,
_iter_nested_mappings, _is_evidence_or_certification_schema) are not public units; they are
exercised + mutation-covered via the public units (dash/space/upper key variants; nested-list
overclaim sub_path; the nested-oracle qualifier keys).
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates
from error_coupling_simulator.frontend.axis1_evidence_guard import (
    FORBIDDEN_CLAIM_FAMILIES,
    HONEST_EXECUTION_CLAIMS,
    VERDICT_CONTRACT_ONLY,
    VERDICT_FAIL,
    VERDICT_PASS,
    _EVIDENCE_SCHEMA_TOKENS,
    axis1_contract_verdict,
    manifest_is_executed,
    validate_axis1_evidence_manifest,
)


# --------------------------------------------------------------------------- #
# INDEPENDENT hard-coded expected copies of the policy constants (from the      #
# module source, re-typed by hand -- NOT read back from the module). Pinning     #
# the module's constants to these kills every family/honest/token/verdict        #
# string mutation, incl. the ones behaviorally subsumed by another family.       #
# --------------------------------------------------------------------------- #
_EXPECTED_FORBIDDEN = (
    "exact_channel",
    "exact_joint_lindblad",
    "exact_continuous_time",
    "dense_channel_payload",
    "dense_channel_evidence",
    "overlapping_window_joint_generator",
    "process_matrix",
    "ptm",
    "kraus",
    "teacher_id",
    "axis2_source_timeline",
    "axis2_source_projection",
    "source_timeline",
    "source_process",
    "dem_decoder_semantics",
    "dem_artifact",
    "decoder_integration",
    "production_scalable_backend",
    "scalable_backend_completed",
    "axis1_full_completion",
)
_EXPECTED_HONEST = frozenset(
    {
        "claims_mcwf_mps_backend_execution",
        "claims_qt_mps_backend_execution",
        "claims_qt_mps_restricted_product_channel_execution",
        "claims_qutip_cuquantum_execution",
        "claims_state_execution",
        "claims_record_execution",
        "claims_record_emission",
        "claims_dense_qutrit_oracle_certification",
        "claims_dense_two_site_leakage_oracle_certification",
        "claims_independent_two_site_leakage_oracle_certification",
    }
)
_EXPECTED_TOKENS = ("evidence", "certification", "execution", "contract")


# --------------------------------------------------------------------------- #
# Builders (faithful minimal replicas of the two emitted manifest shapes).     #
# --------------------------------------------------------------------------- #
def _evidence_manifest(**over) -> dict:
    """A minimal EXECUTED ``*_evidence`` manifest that PASSES validate: an evidence-schema,
    verdict 'pass', an ``*_executed:True`` flag, and the honest present-and-False block."""
    m = {
        "schema": "qec_twin.simulator.axis1_substep_channel_evidence.v1",
        "verdict": "pass",
        "passed": True,
        "channel_payload_executed": True,          # -> manifest_is_executed True -> W-J ok
        "claims_dense_channel_payload": False,
        "claims_dense_channel_evidence": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_axis2_source_timeline": False,
        "claims_dem_decoder_semantics": False,
        "claims_production_scalable_backend": False,
    }
    m.update(over)
    return m


def _contract_only(**over) -> dict:
    """A NON-evidence-schema surface (so W-E.2 present-and-False never fires) carrying
    verdict 'pass'. With no execution evidence it is a contract-only overload (W-J)."""
    m = {
        "schema": "qec_twin.simulator.axis1_state_record_probe.v1",   # no evidence token
        "verdict": "pass",
        "passed": True,
    }
    m.update(over)
    return m


def _accepts(manifest, **kw):
    """A property callable: the guard MUST ACCEPT ``manifest`` (validate does not raise).
    Converts the guard's ``ValueError`` into ``AssertionError`` so it composes with
    ``assert_discriminates`` (which reads an AssertionError as 'property violated')."""
    try:
        validate_axis1_evidence_manifest(manifest, label="lbl", **kw)
    except ValueError as e:
        raise AssertionError(f"guard REJECTED a manifest it should ACCEPT: {e}")


# =========================================================================== #
# VALUE-PINS on the policy constants (kills every family/honest/token/verdict    #
# string mutation -- a boolean/shape assert never could)                        #
# =========================================================================== #
def test_PIN_policy_constants_exact():
    """Pin the load-bearing policy constants to an INDEPENDENT hard-coded copy. A dropped /
    reworded / reordered family or honest-claim or schema-token string is a real overclaim-
    discipline defect and is caught here (not by any structural assert)."""
    assert FORBIDDEN_CLAIM_FAMILIES == _EXPECTED_FORBIDDEN          # order + spelling
    assert HONEST_EXECUTION_CLAIMS == _EXPECTED_HONEST
    assert _EVIDENCE_SCHEMA_TOKENS == _EXPECTED_TOKENS
    assert VERDICT_PASS == "pass"
    assert VERDICT_CONTRACT_ONLY == "contract_only"
    assert VERDICT_FAIL == "fail"


def test_PIN_honest_allowlist_disjoint_from_forbidden_families():
    """A genuine invariant of the two sets: NO honest 'what was done' claim contains a
    forbidden-family substring, so the allowlist bypass is real (an honest True is exempt),
    not an accidental overlap that would let a forbidden family through under an honest name."""
    for honest in HONEST_EXECUTION_CLAIMS:
        offenders = [fam for fam in FORBIDDEN_CLAIM_FAMILIES if fam in honest]
        assert offenders == [], f"honest claim {honest!r} contains forbidden family {offenders}"


# =========================================================================== #
# manifest_is_executed -- every statement + BOTH arcs of every guard            #
# =========================================================================== #
def test_L0_manifest_is_executed_all_arcs():
    """Every branch of manifest_is_executed, pinned to the EXACT boolean value:
      * top-level ``*_executed`` truthy -> True (early return);
      * ``*_executed:False`` -> not counted; honest-loop body with a NON-honest claim
        (219 False) then a nested oracle block (executed:True + qualifier) -> True;
      * an honest claim True anywhere -> True;
      * a nested executed:1 (non-bool) + a nested executed:True WITHOUT a qualifier -> False;
      * nothing executed -> False."""
    assert manifest_is_executed({"backend_executed": True}) is True          # 215 True -> 216
    m = {
        "backend_executed": False,                                            # 215 False
        "claims_neutral_flag": True,                                          # 219 False (not honest)
        "oracle": {"executed": True, "backend_contract": "x"},               # 224 True, 228 True -> 229
    }
    assert manifest_is_executed(m) is True
    assert manifest_is_executed({"claims_record_emission": True}) is True     # 219 True -> 220
    # 224 False (executed:1 non-bool) then 228 False (executed True, no qualifier) -> 230
    assert manifest_is_executed(
        {"claims_neutral_flag": False, "oracle": {"executed": 1, "other": "x"}}
    ) is False
    assert manifest_is_executed({"oracle": {"executed": True, "other": "x"}}) is False
    assert manifest_is_executed({"schema": "x"}) is False                     # 230 nothing executed


@pytest.mark.parametrize(
    "flag",
    ["mcwf_mps_backend_executed", "qt_mps_backend_executed", "backend_executed",
     "dense_probe_executed"],
)
def test_L1_executed_via_top_level_flag(flag):
    """A top-level ``*_executed:True`` is executed (and the manifest validates at verdict
    'pass'); flipping it to False makes it a contract-only overload -> W-J raise. Kills the
    ``endswith('_executed')`` and ``bool(item) is True`` mutations (the executed key must be
    recognized, and a False must NOT count)."""
    good = _contract_only(**{flag: True})
    assert manifest_is_executed(good) is True
    _accepts(good)                                                           # verdict pass ok
    bad = _contract_only(**{flag: False})
    assert manifest_is_executed(bad) is False
    with pytest.raises(ValueError, match="contract_only|reserved for EXECUTED"):
        validate_axis1_evidence_manifest(bad, label="lbl")


@pytest.mark.parametrize("honest", sorted(_EXPECTED_HONEST))
def test_L1_executed_via_honest_claim(honest):
    """Each honest ``claims_*_execution`` / oracle-certification flag True (and nothing else)
    is EXECUTED and must validate at verdict 'pass'. Kills each honest-string mutation in the
    frozenset (a mutated spelling is no longer detected -> not executed -> W-J raise on the
    accepted manifest) and the honest early-return in _forbidden_family_for (an honest True is
    NOT rejected as an overclaim)."""
    m = _contract_only(**{honest: True})
    assert manifest_is_executed(m) is True
    _accepts(m)


@pytest.mark.parametrize(
    "qualifier", ["backend_contract", "evidence_schema", "evidence_content_hash"]
)
def test_L1_executed_via_nested_oracle_qualifier(qualifier):
    """A nested certification block ``executed:True`` counts as executed ONLY with a
    backend_contract / evidence_schema / evidence_content_hash qualifier. Each qualifier is the
    SOLE qualifier here, so a mutation to that key string drops the detection -> W-J raise on
    the accepted manifest -> killed."""
    m = _contract_only(dense_oracle_certification={"executed": True, qualifier: "x"})
    assert manifest_is_executed(m) is True
    _accepts(m)


def test_L0_nested_oracle_false_and_nonbool_and_unqualified_not_executed():
    """The nested-oracle NEGATIVE arcs (all must NOT count as executed):
      * ``executed:False`` (strict bool, but False -> the ``and`` is False; kills ``and``->``or``);
      * ``executed:1`` (int, isinstance(_, bool) False);
      * ``executed:True`` with NO qualifier (the or-chain is False)."""
    for block in (
        {"executed": False, "backend_contract": "x"},                        # and->or discriminator
        {"executed": 1, "backend_contract": "x"},                            # isinstance False
        {"executed": True, "unrelated": "x"},                                # 228 or-chain False
    ):
        m = _contract_only(dense_oracle_certification=block)
        assert manifest_is_executed(m) is False
        with pytest.raises(ValueError, match="contract_only|reserved for EXECUTED"):
            validate_axis1_evidence_manifest(m, label="lbl")


def test_L1_executed_via_nested_oracle_in_a_list():
    """A certification block nested INSIDE A LIST must still be found (the
    _iter_nested_mappings Sequence-recursion). Kills a mutant that recurses into ``None``
    instead of the list item -- which would miss the block and wrongly reject verdict 'pass'."""
    m = _contract_only(rows=[{"note": "s0"}, {"executed": True, "backend_contract": "x"}])
    assert manifest_is_executed(m) is True
    validate_axis1_evidence_manifest(m, label="lbl")                         # accepted
    # discrimination: the SAME block NOT in a list-then-flattened structure still counts, but a
    # bare list of non-oracle dicts does NOT -> stays contract-only -> rejected.
    bare = _contract_only(rows=[{"note": "s0"}, {"note": "s1"}])
    assert manifest_is_executed(bare) is False
    with pytest.raises(ValueError, match="contract_only|reserved for EXECUTED"):
        validate_axis1_evidence_manifest(bare, label="lbl")


# ---- L1 property: manifest_is_executed == an INDEPENDENT re-implementation ---- #
def _indep_is_executed(manifest) -> bool:
    """INDEPENDENT from-scratch re-implementation of the module's executed predicate (does
    NOT import the module's helpers). Mirrors EXACTLY: top-level & honest use the truthy
    ``bool(v) is True``; the nested-oracle path uses the STRICT ``isinstance(bool) and is True``
    with a certification qualifier; a test-local copy of the honest allowlist."""
    def _norm(k):
        return str(k).lower().replace("-", "_").replace(" ", "_")

    for k, v in manifest.items():
        if _norm(k).endswith("_executed") and bool(v) is True:
            return True

    def _walk(v):
        if isinstance(v, dict):
            for k, item in v.items():
                nk = _norm(k)
                if nk.startswith("claims_") and nk in _EXPECTED_HONEST and bool(item) is True:
                    return True
                if _walk(item):
                    return True
        elif isinstance(v, (list, tuple)):
            return any(_walk(item) for item in v)
        return False

    if _walk(manifest):
        return True

    def _iter(v):
        if isinstance(v, dict):
            yield v
            for item in v.values():
                yield from _iter(item)
        elif isinstance(v, (list, tuple)):
            for item in v:
                yield from _iter(item)

    for sub in _iter(manifest):
        ex = sub.get("executed")
        if isinstance(ex, bool) and ex is True and (
            "backend_contract" in sub or "evidence_schema" in sub
            or "evidence_content_hash" in sub
        ):
            return True
    return False


@st.composite
def _random_manifest(draw):
    """A random manifest touching every executed-predicate path with booleans (kept simple so
    the independent oracle matches EXACTLY)."""
    m: dict = {"schema": "x"}
    if draw(st.booleans()):
        m[draw(st.sampled_from(
            ["mcwf_mps_backend_executed", "qt_mps_backend_executed", "backend_executed"]))] = \
            draw(st.booleans())
    if draw(st.booleans()):
        m[draw(st.sampled_from(sorted(_EXPECTED_HONEST)))] = draw(st.booleans())
    if draw(st.booleans()):
        m["claims_something_else"] = draw(st.booleans())                     # neutral claim
    if draw(st.booleans()):
        block = {"executed": draw(st.sampled_from([True, False]))}
        if draw(st.booleans()):
            block[draw(st.sampled_from(
                ["backend_contract", "evidence_schema", "evidence_content_hash", "unrelated"]))] = "x"
        m["nested"] = block
    if draw(st.booleans()):
        m["passed"] = draw(st.booleans())                                    # truthy non-executed
    return m


@settings(max_examples=400, deadline=None)
@given(_random_manifest())
def test_L1_manifest_is_executed_matches_independent(manifest):
    """The executed predicate matches an INDEPENDENT recompute over many structures -- kills
    logic mutations (a flipped ``is True``, a dropped path, an ``and``->``or``) that a single
    hand case leaves alive."""
    assert manifest_is_executed(manifest) == _indep_is_executed(manifest)


# =========================================================================== #
# validate -- structural guards (TypeError / non-bool) + return-copy            #
# =========================================================================== #
def test_L0_non_mapping_raises_typeerror():
    """(guard) a non-Mapping is a TypeError naming the offending type. Kills the
    ``not isinstance(manifest, Mapping)`` guard (dropping ``not`` would reject a valid dict)."""
    with pytest.raises(TypeError, match="must be a mapping, got list"):
        validate_axis1_evidence_manifest(["not", "a", "mapping"], label="lbl")
    # the guard ACCEPTS a real mapping (the both-arcs proof)
    _accepts(_evidence_manifest())


def test_L0_forbidden_claim_must_be_bool():
    """A forbidden-family claim carrying a NON-bool value is rejected ('must be a bool') --
    claim flags are structural booleans. The real (bool False) is accepted; a string is not."""
    real = _evidence_manifest()
    wrong = _evidence_manifest(claims_dense_channel_evidence="false")        # string, not bool
    with pytest.raises(ValueError, match="must be a bool, got str"):
        validate_axis1_evidence_manifest(wrong, label="lbl")
    assert_discriminates(_accepts, real, wrong, label="forbidden claim must be bool")


def test_L1_returns_shallow_copy_preserving_honest_flags():
    """validate returns a shallow COPY (``dict(manifest)``) and NEVER mutates the honest flags.
    Kills a ``return dict(manifest)`` -> ``return manifest`` mutation (identity) and any
    accidental flip of an honest True."""
    m = _evidence_manifest(claims_dense_qutrit_oracle_certification=True)     # honest True allowed
    returned = validate_axis1_evidence_manifest(m, label="lbl")
    assert returned is not m                                                  # a COPY
    assert returned == m                                                      # same content
    assert returned["claims_dense_qutrit_oracle_certification"] is True       # honest True kept
    assert m["claims_dense_qutrit_oracle_certification"] is True              # source untouched


def test_L0_honest_and_neutral_claims_skip_forbidden_check():
    """The ``family is None: continue`` arc: a honest claim True and a neutral claims_ key True
    are both NOT forbidden -> no raise (while the base's forbidden-False keys exercise the
    ``is True`` False / saw_forbidden_false arc)."""
    m = _evidence_manifest(claims_record_emission=True, claims_neutral_flag=True)
    _accepts(m)


# =========================================================================== #
# validate W-E.1 -- a forbidden claims_* True is REJECTED (every family)         #
# =========================================================================== #
# Each exemplar is caught by its intended family AS THE FIRST match in FORBIDDEN order, so the
# raised message's ``forbidden family {family!r}`` names exactly this family -- pinning it kills
# each family-string mutation (incl. axis2_source_timeline, which would otherwise fall through
# to 'source_timeline').
_FAMILY_EXEMPLARS = [
    ("claims_exact_channel_recovered", "exact_channel"),
    ("claims_exact_joint_lindblad_generator", "exact_joint_lindblad"),
    ("claims_exact_continuous_time_mcwf", "exact_continuous_time"),
    ("claims_dense_channel_payload_emitted", "dense_channel_payload"),
    ("claims_dense_channel_evidence_written", "dense_channel_evidence"),
    ("claims_overlapping_window_joint_generator", "overlapping_window_joint_generator"),
    ("claims_process_matrix_emitted", "process_matrix"),
    ("claims_ptm_export", "ptm"),
    ("claims_kraus_payload", "kraus"),
    ("claims_teacher_id_recovered", "teacher_id"),
    ("claims_axis2_source_timeline", "axis2_source_timeline"),
    ("claims_axis2_source_projection", "axis2_source_projection"),
    ("claims_source_timeline_leak", "source_timeline"),
    ("claims_source_process_state", "source_process"),
    ("claims_dem_decoder_semantics", "dem_decoder_semantics"),
    ("claims_dem_artifact_written", "dem_artifact"),
    ("claims_decoder_integration_done", "decoder_integration"),
    ("claims_production_scalable_backend_done", "production_scalable_backend"),
    ("claims_scalable_backend_completed", "scalable_backend_completed"),
    ("claims_axis1_full_completion", "axis1_full_completion"),
]


def test_meta_family_exemplars_cover_every_family():
    """Every forbidden family has an exemplar (so the parametrization is complete)."""
    assert {fam for _, fam in _FAMILY_EXEMPLARS} == set(FORBIDDEN_CLAIM_FAMILIES)


@pytest.mark.parametrize("injected_key,family", _FAMILY_EXEMPLARS)
def test_L1_forbidden_family_true_is_rejected(injected_key, family):
    """A True on each forbidden family is an OVERCLAIM the guard REJECTS; the message names the
    exact first-match family (``forbidden family {family!r}``). Holds for the clean object,
    fails for the injected one (assert_discriminates)."""
    clean = _evidence_manifest()
    dirty = _evidence_manifest(**{injected_key: True})
    with pytest.raises(ValueError) as ei:
        validate_axis1_evidence_manifest(dirty, label="lbl")
    msg = str(ei.value)
    assert "OVERCLAIM" in msg
    assert f"forbidden family {family!r}" in msg                             # kills the family string
    assert_discriminates(_accepts, clean, dirty, label=f"forbidden {family} True rejected")


def test_L1_KILLER_forbidden_true_never_escapes_headline():
    """Headline W-E.1: an honest-False flag flipped True must NOT escape the guard."""
    clean = _evidence_manifest()
    dirty = _evidence_manifest(claims_dense_channel_evidence=True)
    assert_discriminates(_accepts, clean, dirty, label="no forbidden claims_* True escapes")


def test_L0_forbidden_true_nested_in_list_is_caught():
    """A forbidden True buried in a nested list/dict (rows[0]) is caught -- exercises the
    _walk Sequence branch; the sub_path ``rows[0]`` is pinned (kills the enumerate ``[i]``
    index / bracket mutation)."""
    m = _evidence_manifest()
    m["rows"] = [{"substep": "s0", "claims_kraus_payload": True}]
    with pytest.raises(ValueError) as ei:
        validate_axis1_evidence_manifest(m, label="lbl")
    msg = str(ei.value)
    assert "OVERCLAIM" in msg
    assert "rows[0]" in msg


def test_L1_default_label_in_message():
    """With NO label the default ``axis1_evidence_manifest`` names the manifest in the raise --
    kills the default-label string mutation."""
    m = _evidence_manifest(claims_kraus_payload=True)
    with pytest.raises(ValueError, match="axis1_evidence_manifest: OVERCLAIM"):
        validate_axis1_evidence_manifest(m)                                  # default label


@pytest.mark.parametrize(
    "variant",
    [
        "claims-dense-channel-evidence",     # dashes  -> _normalize_key .replace("-","_")
        "claims dense channel evidence",     # spaces  -> _normalize_key .replace(" ","_")
        "CLAIMS_DENSE_CHANNEL_EVIDENCE",     # upper   -> _normalize_key .lower()
        "Claims_Dense_Channel_Evidence",     # mixed
    ],
)
def test_L1_normalize_key_variants_are_caught(variant):
    """Non-normalized forbidden keys (dashes / spaces / caps) still normalize to a forbidden
    family and are rejected -- kills the _normalize_key replace/lower mutations (a mutated
    normalization would leave the key not-``claims_``-prefixed -> not scanned -> not caught)."""
    m = _evidence_manifest()
    m[variant] = True
    with pytest.raises(ValueError, match="OVERCLAIM"):
        validate_axis1_evidence_manifest(m, label="lbl")


# ---- L1 property: validate raises iff a forbidden family key is True ---- #
_CLAIM_KEY_POOL = [
    "claims_exact_channel_recovered", "claims_kraus_payload", "claims_dem_artifact_written",
    "claims_source_process_state", "claims_axis2_source_timeline",           # forbidden
    "claims_mcwf_mps_backend_execution", "claims_record_emission",           # honest
    "claims_dense_qutrit_oracle_certification",                              # honest
    "claims_neutral_flag", "claims_logical_gate_semantics",                  # neutral
    "backend_executed", "passed",                                           # non-claims noise
]


def _indep_family(raw_key):
    """INDEPENDENT copy of _forbidden_family_for (honest bypass first, then substring), using
    the hard-coded expected constants; None for non-claims keys (which _walk never yields)."""
    n = str(raw_key).lower().replace("-", "_").replace(" ", "_")
    if not n.startswith("claims_"):
        return None
    if n in _EXPECTED_HONEST:
        return None
    for fam in _EXPECTED_FORBIDDEN:
        if fam in n:
            return fam
    return None


@st.composite
def _random_claims_manifest(draw):
    keys = draw(st.lists(st.sampled_from(_CLAIM_KEY_POOL), min_size=0, max_size=6, unique=True))
    m = {"schema": "plain_probe", "verdict": "contract_only"}               # non-evidence, non-pass
    for k in keys:
        m[k] = draw(st.booleans())
    return m


@settings(max_examples=400, deadline=None)
@given(_random_claims_manifest())
def test_L1_validate_raises_iff_forbidden_true(manifest):
    """With require_present=False (isolate W-E.1) and a non-'pass' verdict (isolate W-J),
    validate raises iff some key mapping to a forbidden family is True -- pinned to the
    INDEPENDENT family map. Kills the forbidden-scan logic (the substring loop, the honest
    bypass, the ``is True`` check) over many inputs."""
    should_raise = any(_indep_family(k) is not None and v is True for k, v in manifest.items())
    if should_raise:
        with pytest.raises(ValueError, match="OVERCLAIM"):
            validate_axis1_evidence_manifest(manifest, label="lbl", require_present=False)
    else:
        validate_axis1_evidence_manifest(manifest, label="lbl", require_present=False)


# =========================================================================== #
# validate W-E.2 -- present-and-False discipline on evidence/certification       #
# =========================================================================== #
def _prose_only(**over) -> dict:
    """An evidence-schema manifest with NO ``claims_*`` keys (prose-only discipline)."""
    m = {
        "schema": "qec_twin.simulator.axis1_substep_channel_evidence.v1",
        "verdict": "contract_only",                                          # not 'pass' -> no W-J
        "passed": True,
    }
    m.update(over)
    return m


def test_L1_present_and_false_required_on_evidence_schema():
    """A prose-only evidence manifest (no ``claims_*=False``) is REJECTED; adding ONE
    forbidden-False satisfies the discipline and it PASSES. assert_discriminates + relying on
    the DEFAULT require_present (kills the require_present default->False mutation)."""
    prose = _prose_only()
    with pytest.raises(ValueError, match="present-and-False"):
        validate_axis1_evidence_manifest(prose, label="lbl")                # default require_present
    ok = _prose_only(claims_dense_channel_evidence=False)
    assert_discriminates(_accepts, ok, prose, label="present-and-False discipline")


def test_L0_require_present_false_skips_the_discipline():
    """The ``require_present`` False arc: with require_present=False a prose-only evidence
    manifest is accepted (the compound's first conjunct is False)."""
    validate_axis1_evidence_manifest(_prose_only(), label="lbl", require_present=False)


@pytest.mark.parametrize("token", _EXPECTED_TOKENS)
def test_L1_schema_token_triggers_present_and_false(token):
    """Each of the four schema tokens (evidence / certification / execution / contract) marks a
    manifest as needing present-and-False; a prose-only manifest with ONLY that token raises.
    Kills each token string in _EVIDENCE_SCHEMA_TOKENS (a mutated token no longer matches ->
    is_evidence_schema False -> no raise)."""
    m = {"schema": f"qec_twin.simulator.axis1_{token}_probe.v1",
         "verdict": "contract_only", "passed": True}
    with pytest.raises(ValueError, match="present-and-False"):
        validate_axis1_evidence_manifest(m, label="lbl")


def test_L0_non_evidence_schema_not_required_present():
    """A NON-evidence schema (freeze) is NOT forced to carry claims_* keys (is_evidence_schema
    False arc) -- and the uppercase form still normalizes via ``.lower()`` on the token match."""
    freeze = {"schema": "qec_twin.simulator.axis1_substep_channel_freeze.v1",
              "verdict": "contract_only", "passed": True}
    _accepts(freeze)                                                         # no raise
    # uppercase evidence token still triggers the discipline (kills a dropped .lower())
    upper = {"schema": "QEC_TWIN.AXIS1_EVIDENCE.V1", "verdict": "contract_only", "passed": True}
    with pytest.raises(ValueError, match="present-and-False"):
        validate_axis1_evidence_manifest(upper, label="lbl")


def test_L0_present_and_false_not_forced_when_forbidden_false_present():
    """The W-E.2 compound's ``not saw_forbidden_false`` False arc: an evidence schema that DOES
    carry a forbidden-False is accepted even at require_present=True."""
    _accepts(_prose_only(claims_production_scalable_backend=False))


# =========================================================================== #
# validate W-J -- verdict 'pass' reserved for EXECUTED evidence                  #
# =========================================================================== #
def test_L1_KILLER_verdict_pass_iff_execution():
    """Headline W-J: the guard ACCEPTS an executed pass-manifest and REJECTS a non-executed one
    (verdict <=> execution). assert_discriminates proves the check bites."""
    executed = _contract_only(mcwf_mps_backend_executed=True)
    contract_only = _contract_only()                                        # nothing executed
    assert manifest_is_executed(executed) is True
    assert manifest_is_executed(contract_only) is False
    assert_discriminates(_accepts, executed, contract_only,
                         label="verdict:pass reserved for executed")


def test_L1_verdict_pass_requires_execution_core():
    """A plain contract-only surface (verdict 'pass', ``passed:True``, NOTHING executed) is a
    W-J overload -> raise. This also kills the 215 ``and``->``or`` mutation (``passed:True`` would
    be wrongly read as executed under ``or``)."""
    m = _contract_only()
    assert manifest_is_executed(m) is False
    with pytest.raises(ValueError, match="contract_only|reserved for EXECUTED"):
        validate_axis1_evidence_manifest(m, label="lbl")


def test_L0_verdict_non_pass_skips_wj():
    """The W-J compound's ``verdict == VERDICT_PASS`` False arc: a non-'pass' verdict on a
    non-executed surface is accepted (the de-overloaded verdict IS the fix)."""
    validate_axis1_evidence_manifest(
        _contract_only(verdict="contract_only"), label="lbl")
    validate_axis1_evidence_manifest(
        _contract_only(verdict="fail"), label="lbl")


def test_L1_executed_pass_via_dense_oracle_keeps_pass():
    """A contract surface that executed a dense oracle (nested executed:True + qualifier)
    legitimately keeps verdict 'pass' (the ``not manifest_is_executed`` False arc)."""
    m = _contract_only(dense_oracle_certification={
        "executed": True,
        "backend_contract": "dense_jointL_probe",
        "evidence_schema": "qec_twin.simulator.axis1_carrier_mcwf_mps_execution.v1",
        "evidence_content_hash": "abc123",
    })
    assert manifest_is_executed(m) is True
    validate_axis1_evidence_manifest(m, label="lbl")


# =========================================================================== #
# EXACT raise-message pins -- the message text IS the contract (it tells the      #
# writer WHY it was rejected + what to do). Pinning the FULL message (with a       #
# known label / sub_path) kills every mutmut string mutation of the raise text     #
# (XX-wrap, upper, lower) AND the ``_walk(manifest, label)`` sub_path mutation      #
# (label -> None). These are the ~34 surviving message/sub_path mutants.           #
# =========================================================================== #
def test_PIN_overclaim_message_exact():
    m = _evidence_manifest(claims_kraus_payload=True)                        # last -> raises here
    with pytest.raises(ValueError) as ei:
        validate_axis1_evidence_manifest(m, label="LBL")
    assert str(ei.value) == (
        "LBL: OVERCLAIM — LBL.claims_kraus_payload is True (forbidden family 'kraus'). "
        "An Axis-1 evidence/certification manifest cannot assert an exact-channel / "
        "PTM / Kraus / teacher-ID / source-timeline / DEM / production result it did "
        "not produce. Set this claim False, or move the real evaluator truth into an "
        "evaluator_sidecar (isolation contract)."
    )


def test_PIN_must_be_bool_message_exact():
    m = _evidence_manifest(claims_dense_channel_evidence="oops")             # non-bool forbidden
    with pytest.raises(ValueError) as ei:
        validate_axis1_evidence_manifest(m, label="LBL")
    assert str(ei.value) == (
        "LBL: forbidden claim key LBL.claims_dense_channel_evidence "
        "(family 'dense_channel_evidence') must be a bool, got str='oops'. Claim flags are "
        "structural booleans, not free values."
    )


def test_PIN_present_and_false_message_exact():
    m = {"schema": "qec_twin.simulator.axis1_substep_channel_evidence.v1",
         "verdict": "contract_only", "passed": True}
    with pytest.raises(ValueError) as ei:
        validate_axis1_evidence_manifest(m, label="LBL")
    assert str(ei.value) == (
        "LBL: evidence/certification manifest "
        "(schema='qec_twin.simulator.axis1_substep_channel_evidence.v1') carries NO "
        "explicit claims_*=False from the forbidden families. Prose policy strings are "
        "not enforceable; the manifest must declare the forbidden claims present-and-False "
        "(e.g. claims_dense_channel_evidence=False, claims_exact_joint_lindblad_generator="
        "False, claims_axis2_source_timeline=False, claims_dem_decoder_semantics=False, "
        "claims_production_scalable_backend=False)."
    )


def test_PIN_wj_message_exact():
    m = _contract_only()                                                    # verdict pass, none exec
    with pytest.raises(ValueError) as ei:
        validate_axis1_evidence_manifest(m, label="LBL")
    assert str(ei.value) == (
        "LBL: verdict:'pass' is reserved for EXECUTED evidence. This manifest has "
        "no execution evidence (no *_executed:True flag and no dense_oracle_certification."
        "executed:True), so it is a contract-only surface and must use "
        "verdict:'contract_only' (W-J de-overload), with passed reflecting the "
        "contract check rather than an executed run."
    )


def test_PIN_typeerror_message_exact():
    with pytest.raises(TypeError) as ei:
        validate_axis1_evidence_manifest(("not", "a", "mapping"), label="LBL")
    assert str(ei.value) == "LBL must be a mapping, got tuple"


# =========================================================================== #
# axis1_contract_verdict -- exact verdict string over the full (valid,be,oe) grid#
# =========================================================================== #
@pytest.mark.parametrize(
    "contract_valid,backend_executed,oracle_executed,expected",
    [
        (True, False, False, "contract_only"),
        (True, True, False, "pass"),
        (True, False, True, "pass"),
        (True, True, True, "pass"),
        (False, False, False, "fail"),
        (False, True, False, "fail"),
        (False, False, True, "fail"),
        (False, True, True, "fail"),
    ],
)
def test_L0_L1_contract_verdict_matrix(contract_valid, backend_executed, oracle_executed,
                                       expected):
    """Pin the EXACT verdict string for all 8 (valid, backend, oracle) combos. Kills the
    VERDICT_FAIL/PASS/CONTRACT_ONLY string mutations, the ``not contract_valid`` guard, and the
    ``backend_executed or oracle_executed`` (or->and) mutation."""
    assert axis1_contract_verdict(
        contract_valid=contract_valid,
        backend_executed=backend_executed,
        oracle_executed=oracle_executed,
    ) == expected


def test_L0_contract_verdict_defaults():
    """The default ``backend_executed=False, oracle_executed=False`` -> a valid surface is
    'contract_only' (kills a default->True mutation); an invalid surface is 'fail'."""
    assert axis1_contract_verdict(contract_valid=True) == "contract_only"
    assert axis1_contract_verdict(contract_valid=False) == "fail"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

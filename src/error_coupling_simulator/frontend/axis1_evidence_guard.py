"""candidate.py — finish-plan Step 6 (step6_a): OUTPUT-side claim-scan + verdict de-overload.

Findings addressed
------------------
W-E  The claim guard ``metadata_guard.validate_public_metadata`` runs on INPUT objects
     only (CircuitIR / CodeSpec); NO output-side scan asserts the forbidden ``claims_*``
     booleans are present-and-False on emitted ``*_evidence`` / ``*_certification``
     manifests before ``write_json``. The canonical evidence writers
     (``axis1_substep_channel_evidence_manifest`` in axis1_channel_evidence.py and the
     bridge manifest in axis1_bridge.py) carry NO ``claims_*`` keys at all — their
     claim-discipline is prose-only (``channel_payload_policy`` / ``bridge_scope`` strings),
     so an overclaim could not be caught structurally.

W-J  ``verdict:"pass"`` is overloaded. ``axis1_mcwf_mps_contract.py:72`` emits
     ``verdict:"pass", passed:True, backend_executed:False`` for a CONTRACT-ONLY
     (non-executed) surface — indistinguishable from an executed pass.

Two reusable OUTPUT-side validators (distinct from the INPUT guard
``metadata_guard.validate_public_metadata``) live here:

1. ``validate_axis1_evidence_manifest(manifest)`` — the W-E + W-J output guard:
   (a) every forbidden claim FAMILY (dense-channel payload/evidence, exact-* channel,
       joint-Lindblad generator, teacher-id / PTM / Kraus / process-matrix,
       Axis-2 source-timeline, DEM/decoder, production / scalable-completed) is PRESENT
       and ``False`` somewhere on the manifest, and NO forbidden ``claims_*`` key
       anywhere in the tree is ``True``;
   (b) ``verdict:"pass"`` is reserved for EXECUTED evidence; a manifest with no
       execution evidence (no ``*_executed:True`` flag and no
       ``dense_oracle_certification.executed:True``) must use
       ``verdict:"contract_only"``, NOT ``"pass"``.

2. ``axis1_contract_verdict(...)`` — the tiny de-overloading helper a contract writer
   uses instead of a hardcoded ``"pass"`` literal.

This is the OUTPUT mirror of the isolation contract (CLAUDE.md): the input guard keeps
evaluator truth OUT of public artifact metadata; this output guard keeps the simulator
from EMITTING a manifest that overclaims (asserts an exact channel / PTM / Kraus /
teacher-ID / source-timeline / DEM / production result it did not produce) or that
labels a non-executed contract surface as a passing run. Claim-discipline +
faithfulness-protocol Rule III (declare + BOUND every simplification; an unbounded
overclaim = STOP) are enforced as a structural pre-write gate.

The validator NEVER mutates the honest claim flags. ``claims_*_execution:True`` and
``claims_dense_qutrit_oracle_certification:True`` are positive assertions of WHAT WAS
DONE; they are an allowlist that bypasses the "no forbidden True" check.

CPU-ONLY — string / dict structure inspection only; no CUDA, no torch, no project
compute. Author-only; Claude integrates the thin pre-write call into the writers.

Epistemic classes
-----------------
  (a) exact     — the forbidden-key membership + verdict gate are exact structural
                  predicates (zero-tolerance: a forbidden True / a missing required-False
                  / a mislabeled verdict is a hard raise, never a band).
  (c) policy    — the FORBIDDEN_CLAIM_FAMILIES set and the HONEST_EXECUTION_CLAIMS
                  allowlist are claim-discipline design constants (go/no-go gating only).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

# --------------------------------------------------------------------------- #
# Provenance of the forbidden-claim families (epistemic class c — policy set).
#
# Each family is a substring matched against the normalized claim-key name (lower,
# "-"/" " -> "_"), mirroring metadata_guard._RESERVED_METADATA_KEY_PARTS so the OUTPUT
# guard and the INPUT guard share one vocabulary. A family fires on ANY claims_* key
# whose normalized name contains the substring.
#
# Provenance (where the forbidden concept already appears as a claims_*=False flag, i.e.
# what the writers ALREADY promise NOT to claim — this guard makes that promise
# present-and-enforced rather than optional prose):
#   exact_channel / process_matrix / ptm / kraus / teacher_id / source_timeline
#       <- metadata_guard._RESERVED_METADATA_KEY_PARTS (the INPUT evaluator-truth list)
#   dense_channel_payload      <- axis1_qutrit_leakage_certification.py:271, mcwf_mps_contract carrier summary
#   dense_channel_evidence     <- axis1_mcwf_mps_execution.py:141, axis1_carrier_execution.py:144, qt_mps:*
#   exact_joint_lindblad_generator <- axis1_mcwf_mps_execution.py:140, axis1_carrier_execution.py:349
#   exact_continuous_time_mcwf <- axis1_qutrit_leakage_certification.py:272
#   axis2_source_timeline      <- axis1_mcwf_mps_contract.py:122, axis1_mcwf_mps_execution.py:143
#   axis2_source_projection    <- axis1_record_evidence.py:168, axis1_state_evidence.py:356
#   dem_decoder_semantics      <- axis1_mcwf_mps_contract.py (book guard), axis1_carrier_execution.py:145
#   dem_artifact               <- axis1_record_evidence.py:334
#   production_scalable_backend / scalable_backend_completed
#       <- axis1_mcwf_mps_contract.py:119, axis1_carrier_execution.py:147/347/348
#   overlapping_window_joint_generator <- axis1_record_evidence.py:698, axis1_state_evidence.py:355
# --------------------------------------------------------------------------- #
FORBIDDEN_CLAIM_FAMILIES: tuple[str, ...] = (
    # exact / dense channel payload + closed-form generator overclaims
    "exact_channel",
    "exact_joint_lindblad",
    "exact_continuous_time",
    "dense_channel_payload",
    "dense_channel_evidence",
    "overlapping_window_joint_generator",
    # evaluator-truth handles (the INPUT-guard vocabulary, mirrored OUT)
    "process_matrix",
    "ptm",
    "kraus",
    "teacher_id",
    # source-timeline / Axis-2 leakage from a same-substep (Axis-1) manifest
    "axis2_source_timeline",
    "axis2_source_projection",
    "source_timeline",
    "source_process",
    # DEM / decoder semantics from a forward-channel manifest
    "dem_decoder_semantics",
    "dem_artifact",
    "decoder_integration",
    # production / fully-scalable-backend completion overclaims
    "production_scalable_backend",
    "scalable_backend_completed",
    "axis1_full_completion",
)

# --------------------------------------------------------------------------- #
# Honest "what was DONE" positive claims (epistemic class c — allowlist).
#
# These legitimately carry value True on an EXECUTED manifest. They are exempt from the
# "no forbidden claims_* is True" rule. They are matched as EXACT normalized names (not
# substrings) so a True here can never shadow a forbidden family.
#
# Provenance:
#   claims_mcwf_mps_backend_execution  True <- axis1_mcwf_mps_execution.py:256 (executed run)
#   claims_qt_mps_backend_execution    True <- axis1_qt_mps_execution.py:149/406/... (executed run)
#   claims_qutip_cuquantum_execution   True <- axis1_carrier_execution.py:563 (executed probe)
#   claims_dense_qutrit_oracle_certification True <- axis1_qutrit_leakage_certification.py:270
#   claims_dense_two_site_leakage_oracle_certification / claims_independent_two_site_..._certification
#                                      True <- axis1_qutrit_leakage_certification.py:507/508
#   claims_state_execution / claims_record_execution / claims_record_emission
#                                      True when the corresponding artifact really emitted.
# --------------------------------------------------------------------------- #
HONEST_EXECUTION_CLAIMS: frozenset[str] = frozenset(
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

# Verdict reserved for an executed evidence/certification surface.
VERDICT_PASS = "pass"
# Verdict a non-executed contract-only surface MUST use instead of "pass" (W-J fix).
VERDICT_CONTRACT_ONLY = "contract_only"
VERDICT_FAIL = "fail"

# A manifest is treated as carrying the present-and-False discipline when its top-level
# "schema" string contains one of these tokens. (The contract surfaces in this token set
# must declare verdict via VERDICT_CONTRACT_ONLY when they did not execute.)
_EVIDENCE_SCHEMA_TOKENS: tuple[str, ...] = (
    "evidence",
    "certification",
    "execution",
    "contract",
)


def _normalize_key(raw_key: Any) -> str:
    return str(raw_key).lower().replace("-", "_").replace(" ", "_")


def _forbidden_family_for(normalized_key: str) -> str | None:
    """Return the forbidden family substring this claim key matches, else None.

    An exact-name member of HONEST_EXECUTION_CLAIMS is never forbidden — a True there is
    an honest "what was done" assertion, not an overclaim.
    """

    if normalized_key in HONEST_EXECUTION_CLAIMS:
        return None
    for family in FORBIDDEN_CLAIM_FAMILIES:
        if family in normalized_key:
            return family
    return None


def _walk(value: Any, path: str):
    """Yield (path, key, normalized_key, claim_value) for every claims_* key in the tree."""

    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = _normalize_key(key)
            sub_path = f"{path}.{key}"
            if normalized.startswith("claims_"):
                yield sub_path, key, normalized, item
            yield from _walk(item, sub_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for i, item in enumerate(value):
            yield from _walk(item, f"{path}[{i}]")


def manifest_is_executed(manifest: Mapping[str, Any]) -> bool:
    """Return True iff the manifest carries evidence that SOMETHING executed.

    Executed means any of:
      * a top-level ``*_executed`` boolean is True (e.g. ``mcwf_mps_backend_executed``,
        ``qt_mps_backend_executed``, ``backend_executed``, ``dense_probe_executed``);
      * an honest ``claims_*_execution`` / oracle-certification flag is True anywhere;
      * a ``dense_oracle_certification.executed`` (or nested ``*.executed``) is True.

    A contract-only surface (axis1_mcwf_mps_contract: backend_executed False, no oracle
    executed) returns False — and therefore may NOT use verdict:"pass".
    """

    for raw_key, item in manifest.items():
        key = _normalize_key(raw_key)
        if key.endswith("_executed") and bool(item) is True:
            return True
    # Honest execution claims True anywhere in the tree.
    for _path, _key, normalized, claim_value in _walk(manifest, "manifest"):
        if normalized in HONEST_EXECUTION_CLAIMS and bool(claim_value) is True:
            return True
    # A dense-oracle certification (or any nested object) that actually executed.
    for sub in _iter_nested_mappings(manifest):
        executed = sub.get("executed")
        if isinstance(executed, bool) and executed is True:
            # Only count nested executed:True that belongs to a certification/oracle block,
            # i.e. a block also declaring a backend_contract / evidence_schema (the dense
            # oracle path) — not a bare flag.
            if "backend_contract" in sub or "evidence_schema" in sub or "evidence_content_hash" in sub:
                return True
    return False


def _iter_nested_mappings(value: Any):
    if isinstance(value, Mapping):
        yield value
        for item in value.values():
            yield from _iter_nested_mappings(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            yield from _iter_nested_mappings(item)


def _is_evidence_or_certification_schema(schema: Any) -> bool:
    s = str(schema).lower()
    return any(token in s for token in _EVIDENCE_SCHEMA_TOKENS)


def validate_axis1_evidence_manifest(
    manifest: Mapping[str, Any],
    *,
    label: str = "axis1_evidence_manifest",
    require_present: bool = True,
) -> dict:
    """Validate an Axis-1 ``*_evidence`` / ``*_certification`` manifest before write_json.

    Raises ``ValueError`` if:
      (W-E.1) any forbidden ``claims_*`` family key anywhere in the tree is True
              (an exact-channel / PTM / Kraus / teacher-ID / source-timeline / DEM /
              production overclaim);
      (W-E.2) ``require_present`` and the top-level schema is an evidence/certification
              schema yet the manifest does not carry at least one explicit
              ``claims_*=False`` from the forbidden families (the present-and-False
              discipline — prose-only policy strings are no longer sufficient);
      (W-J)   ``verdict == "pass"`` on a manifest that did not execute anything
              (a contract-only surface must use verdict:"contract_only").

    Returns the manifest unchanged (a shallow copy) on success. NEVER mutates the honest
    claim flags. This is a pre-write gate, not a transform.
    """

    if not isinstance(manifest, Mapping):
        raise TypeError(f"{label} must be a mapping, got {type(manifest).__name__}")

    schema = manifest.get("schema")
    is_evidence_schema = _is_evidence_or_certification_schema(schema)

    # ---- (W-E.1) no forbidden claims_* is True anywhere in the tree. ----------- #
    saw_forbidden_false = False
    for sub_path, key, normalized, claim_value in _walk(manifest, label):
        family = _forbidden_family_for(normalized)
        if family is None:
            continue
        if not isinstance(claim_value, bool):
            raise ValueError(
                f"{label}: forbidden claim key {sub_path} (family {family!r}) must be a "
                f"bool, got {type(claim_value).__name__}={claim_value!r}. Claim flags are "
                "structural booleans, not free values."
            )
        if claim_value is True:
            raise ValueError(
                f"{label}: OVERCLAIM — {sub_path} is True (forbidden family {family!r}). "
                "An Axis-1 evidence/certification manifest cannot assert an exact-channel / "
                "PTM / Kraus / teacher-ID / source-timeline / DEM / production result it did "
                "not produce. Set this claim False, or move the real evaluator truth into an "
                "evaluator_sidecar (isolation contract)."
            )
        saw_forbidden_false = True

    # ---- (W-E.2) present-and-False discipline on evidence/certification schemas. - #
    if require_present and is_evidence_schema and not saw_forbidden_false:
        raise ValueError(
            f"{label}: evidence/certification manifest (schema={schema!r}) carries NO "
            "explicit claims_*=False from the forbidden families. Prose policy strings are "
            "not enforceable; the manifest must declare the forbidden claims present-and-False "
            "(e.g. claims_dense_channel_evidence=False, claims_exact_joint_lindblad_generator="
            "False, claims_axis2_source_timeline=False, claims_dem_decoder_semantics=False, "
            "claims_production_scalable_backend=False)."
        )

    # ---- (W-J) verdict de-overloading. ---------------------------------------- #
    verdict = manifest.get("verdict")
    if verdict == VERDICT_PASS and not manifest_is_executed(manifest):
        raise ValueError(
            f"{label}: verdict:'pass' is reserved for EXECUTED evidence. This manifest has "
            "no execution evidence (no *_executed:True flag and no dense_oracle_certification."
            "executed:True), so it is a contract-only surface and must use "
            f"verdict:'{VERDICT_CONTRACT_ONLY}' (W-J de-overload), with passed reflecting the "
            "contract check rather than an executed run."
        )

    return dict(manifest)


def axis1_contract_verdict(
    *,
    contract_valid: bool,
    backend_executed: bool = False,
    oracle_executed: bool = False,
) -> str:
    """Return the de-overloaded verdict for a contract surface (W-J helper).

    * Anything executed (backend OR dense oracle) and valid -> "pass".
    * A non-executed but valid contract surface           -> "contract_only".
    * An invalid / blocked contract surface               -> "fail".

    A contract writer calls this instead of hardcoding ``"pass"``: e.g.
    ``axis1_mcwf_mps_contract`` (backend_executed=False, oracle_executed=False) gets
    ``"contract_only"``; ``axis1_qt_mps_contract`` on a dense-oracle-executed schedule
    (oracle_executed=True) keeps ``"pass"``.
    """

    if not contract_valid:
        return VERDICT_FAIL
    if backend_executed or oracle_executed:
        return VERDICT_PASS
    return VERDICT_CONTRACT_ONLY


# --------------------------------------------------------------------------- #
# INTEGRATION SKETCH (how the thin pre-write call wires in — Claude integrates;
# this candidate does NOT edit src/). Shown for the four canonical write_json sites.
#
#   from error_coupling_simulator.frontend.axis1_evidence_guard import validate_axis1_evidence_manifest
#
#   # axis1_channel_evidence.write_axis1_substep_channel_evidence (line ~285):
#   manifest = axis1_substep_channel_evidence_manifest(schedule, device=device)
#   validate_axis1_evidence_manifest(manifest, label="axis1_substep_channel_evidence")
#   write_json(path, manifest)
#
#   # axis1_state_evidence.write_axis1_state_evolution_evidence (line ~145):
#   manifest = axis1_state_evolution_evidence_manifest(schedule, device=device)
#   validate_axis1_evidence_manifest(manifest, label="axis1_state_evolution_evidence")
#   write_json(path, manifest)
#
#   # axis1_record_evidence.write_* (line ~260) and axis1_bridge.write_* (line ~274):
#   validate_axis1_evidence_manifest(manifest, label="axis1_measurement_record_evidence")
#   write_json(path, manifest)
#
# Because channel_evidence + bridge manifests today carry NO claims_* keys, the
# integration step ALSO adds the honest present-and-False block to each (the W-E content
# fix) — claims_dense_channel_payload/_evidence, claims_exact_joint_lindblad_generator,
# claims_axis2_source_timeline, claims_dem_decoder_semantics, claims_production_scalable_backend
# = False — turning the existing prose policy strings into enforced structure WITHOUT
# changing any honest flag.
#
#   # axis1_mcwf_mps_contract.axis1_mcwf_mps_state_record_contract_manifest (line 72) — W-J:
#   "verdict": axis1_contract_verdict(contract_valid=True, backend_executed=False),
#   #  -> "contract_only"  (was the hardcoded "pass")
# --------------------------------------------------------------------------- #

__all__ = [
    "FORBIDDEN_CLAIM_FAMILIES",
    "HONEST_EXECUTION_CLAIMS",
    "VERDICT_PASS",
    "VERDICT_CONTRACT_ONLY",
    "VERDICT_FAIL",
    "validate_axis1_evidence_manifest",
    "axis1_contract_verdict",
    "manifest_is_executed",
]

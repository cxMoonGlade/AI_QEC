"""red_test.py — finish-plan Step 6 (step6_a): OUTPUT claim-scan + verdict de-overload.

CPU-ONLY. No CUDA, no torch, no project compute. The real manifest builders
(axis1_*_evidence_manifest, axis1_mcwf_mps_state_record_contract_manifest) all call
``_require_cuda_device`` and so cannot run CPU-only here; the fixtures below replicate
the EXACT emitted key structure (cited to source file:line) so the failure is shown on
the structure the unguarded write_json path emits today, and the fix is shown to pass.

Each test has two halves:
  * ``*_current_unguarded`` — proves the CURRENT path (write_json with no output guard)
    accepts an overclaiming / verdict-overloaded manifest (RED: the bug is live).
  * ``*_guarded`` — proves ``validate_axis1_evidence_manifest`` / ``axis1_contract_verdict``
    catches it (GREEN: the fix works).

Run:
  conda run -n aiqec python -m pytest -q \
    outputs/axis1_review/fixes/step6/step6_a/red_test.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# The integrated output-manifest claim guard (pure string/dict structure; no GPU/torch).
from qec_twin.simulator.axis1_evidence_guard import (
    axis1_contract_verdict,
    manifest_is_executed,
    validate_axis1_evidence_manifest,
)


# --------------------------------------------------------------------------- #
# The CURRENT (unguarded) output path. This is exactly what every writer does today:
# build the manifest dict and hand it to artifacts.write_json with NO output-side scan.
# --------------------------------------------------------------------------- #
def _unguarded_write_json(path: Path, manifest: dict) -> dict:
    """Mirror artifacts.write_json (json.dumps + sort_keys) with NO claim guard.

    Returns the round-tripped manifest. This is the CURRENT path — it never inspects
    claims_* keys nor the verdict overload, so an overclaim / overload is persisted.
    """

    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return json.loads(path.read_text())


# --------------------------------------------------------------------------- #
# Fixtures: faithful replicas of the emitted manifest structures.
# --------------------------------------------------------------------------- #
def _channel_evidence_manifest_current() -> dict:
    """Replica of axis1_substep_channel_evidence_manifest (axis1_channel_evidence.py:225).

    IMPORTANT: the real manifest carries NO claims_* keys — discipline is prose-only
    (channel_payload_policy + bridge_scope strings). This is the W-E gap verbatim.
    """

    return {
        "schema": "qec_twin.simulator.axis1_substep_channel_evidence.v1",
        "verdict": "pass",
        "source_kind": "compiler",
        "source_hash": "deadbeef",
        "representability": "axis1_substep_channel_carrier_evidence",
        "channel_payload_policy": (
            "Kraus, Choi, and superoperator arrays are computed on GPU as carrier "
            "evidence but are not serialized into this artifact"
        ),
        "bridge_scope": (
            "joint channel carrier evidence only; no analog record emission, no Axis-2 "
            "source timeline, no leakage/qutrit integration"
        ),
        "passed": True,
        "rows": [{"passed": True, "substep_id": "s0"}],
        # NOTE: no claims_* keys at all -> the present-and-False discipline is absent.
    }


def _state_evidence_manifest_with_false_claims() -> dict:
    """Replica of the state-evidence nested claim block (axis1_state_evidence.py:352-356),
    promoted to the top level as the W-E content fix expects, all honestly False."""

    return {
        "schema": "qec_twin.simulator.axis1_state_evolution_evidence.v1",
        "verdict": "pass",
        "source_kind": "compiler",
        "passed": True,
        "state_execution": {"executed": True, "backend_contract": "dense_jointL_probe"},
        "claims_logical_gate_semantics": False,
        "claims_record_emission": False,
        "claims_dense_channel_evidence": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_axis2_source_timeline": False,
        "claims_dem_decoder_semantics": False,
        "claims_production_scalable_backend": False,
    }


def _mcwf_mps_contract_manifest_current() -> dict:
    """Replica of axis1_mcwf_mps_state_record_contract_manifest (axis1_mcwf_mps_contract.py:62-139).

    The W-J overload verbatim: verdict:"pass", passed:True, backend_executed:False, no
    dense_oracle_certification -> nothing executed, yet labeled "pass".
    """

    return {
        "schema": "qec_twin.simulator.axis1_mcwf_mps_state_record_contract.v1",
        "representability": "axis1_mcwf_mps_state_record_contract_no_backend_execution",
        "contract_valid": True,
        "verdict": "pass",  # <-- axis1_mcwf_mps_contract.py:72
        "passed": True,
        "backend_executed": False,  # <-- axis1_mcwf_mps_contract.py:74
        "mcwf_mps_backend_executed": False,  # <-- axis1_mcwf_mps_contract.py:75
        "implementation_status": "contract_only_backend_not_implemented",
        "claims_qt_mps_restricted_product_channel_execution": False,
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
    }


def _qt_mps_contract_manifest_dense_executed() -> dict:
    """Replica of the qt_mps contract DENSE-ORACLE-EXECUTED path (axis1_qt_mps_contract.py:108-130).

    This one DID execute a dense oracle (dense_oracle_certification.executed=True), so its
    verdict:"pass" is HONEST and must be left alone by the validator.
    """

    return {
        "schema": "qec_twin.simulator.axis1_qt_mps_state_record_contract.v1",
        "representability": "axis1_qt_mps_state_record_contract_no_backend_execution",
        "verdict": "pass",
        "passed": True,
        "qt_mps_backend_executed": False,
        "dense_oracle_certification": {
            "executed": True,
            "backend_contract": "dense_jointL_probe",
            "evidence_schema": "qec_twin.simulator.axis1_carrier_mcwf_mps_execution.v1",
            "evidence_content_hash": "abc123",
            "comparison_outcome_is_metric": False,
        },
        "claims_qt_mps_backend_execution": False,
        "claims_production_scalable_backend": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
    }


def _mcwf_mps_execution_manifest_executed() -> dict:
    """Replica of axis1_mcwf_mps_state_record_execution_manifest executed pass
    (axis1_mcwf_mps_execution.py:120-256): an HONEST claims_mcwf_mps_backend_execution=True."""

    return {
        "schema": "qec_twin.simulator.axis1_carrier_mcwf_mps_execution.v1",
        "verdict": "pass",
        "passed": True,
        "mcwf_mps_backend_executed": True,  # axis1_mcwf_mps_execution.py:255
        "claims_mcwf_mps_backend_execution": True,  # honest "what was done": :256
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
    }


# =========================================================================== #
# W-E.1  — an injected overclaim (claims_*=True on a forbidden family) is caught.
# =========================================================================== #
@pytest.mark.parametrize(
    "injected_key",
    [
        "claims_exact_joint_lindblad_generator",  # exact closed-form generator overclaim
        "claims_dense_channel_evidence",  # dense channel payload overclaim
        "claims_dense_channel_payload",  # dense channel payload overclaim
        "claims_axis2_source_timeline",  # Axis-2 source-timeline leak
        "claims_dem_decoder_semantics",  # DEM/decoder semantics overclaim
        "claims_production_scalable_backend",  # production-backend completion overclaim
        "claims_teacher_id_recovered",  # evaluator-truth (teacher id) overclaim
        "claims_process_matrix_emitted",  # PTM / process-matrix overclaim
        "claims_kraus_payload_serialized",  # Kraus payload overclaim
    ],
)
def test_we_injected_overclaim_current_path_accepts_then_guard_raises(tmp_path, injected_key):
    manifest = _state_evidence_manifest_with_false_claims()
    manifest[injected_key] = True  # the overclaim

    # CURRENT path: write_json persists the overclaim with no complaint (RED).
    out = _unguarded_write_json(tmp_path / "evidence.json", manifest)
    assert out[injected_key] is True  # the bug is live: an overclaim reaches disk

    # GUARDED path: the output validator rejects it (GREEN).
    with pytest.raises(ValueError, match="OVERCLAIM"):
        validate_axis1_evidence_manifest(manifest, label="axis1_state_evolution_evidence")


def test_we_injected_overclaim_nested_in_rows_is_caught():
    """A forbidden True buried in a nested list/dict (e.g. rows[]) is still caught."""

    manifest = _channel_evidence_manifest_current()
    manifest["claims_dense_channel_evidence"] = False  # satisfy present-and-False
    manifest["rows"][0]["claims_exact_joint_lindblad_generator"] = True  # nested overclaim
    with pytest.raises(ValueError, match="OVERCLAIM"):
        validate_axis1_evidence_manifest(manifest, label="axis1_substep_channel_evidence")


# =========================================================================== #
# W-E.2  — present-and-False discipline: an evidence manifest missing every
#          forbidden claims_*=False (prose-only) is rejected.
# =========================================================================== #
def test_we_channel_evidence_prose_only_current_path_accepts_then_guard_raises(tmp_path):
    manifest = _channel_evidence_manifest_current()  # NO claims_* keys (real today)

    # CURRENT path: prose-only manifest is written with no enforcement (RED).
    out = _unguarded_write_json(tmp_path / "channel_evidence.json", manifest)
    assert not any(k.startswith("claims_") for k in out)  # the gap is live

    # GUARDED path: missing present-and-False discipline is rejected (GREEN).
    with pytest.raises(ValueError, match="present-and-False|NO\\s+explicit claims_"):
        validate_axis1_evidence_manifest(manifest, label="axis1_substep_channel_evidence")


def test_we_channel_evidence_with_false_block_passes():
    """The W-E content fix: add the honest present-and-False block -> validator passes,
    and the honest flags are untouched (no mutation)."""

    manifest = _channel_evidence_manifest_current()
    for k in (
        "claims_dense_channel_payload",
        "claims_dense_channel_evidence",
        "claims_exact_joint_lindblad_generator",
        "claims_axis2_source_timeline",
        "claims_dem_decoder_semantics",
        "claims_production_scalable_backend",
    ):
        manifest[k] = False
    # state_execution-style evidence: this one is a verdict:"pass" but it executed rows.
    manifest["rows"][0]["claims_dense_channel_evidence"] = False
    # mark it executed so verdict:"pass" is allowed (it is real channel evidence).
    manifest["channel_payload_executed"] = True

    returned = validate_axis1_evidence_manifest(manifest, label="axis1_substep_channel_evidence")
    # honest flags unchanged
    assert returned["claims_dense_channel_evidence"] is False
    assert returned["channel_payload_executed"] is True


def test_we_present_check_optional_for_non_evidence_schema():
    """A non-evidence schema (e.g. a freeze guard) is not forced to carry claims_* keys."""

    freeze = {
        "schema": "qec_twin.simulator.axis1_substep_channel_freeze.v1",
        "verdict": "pass",
        "passed": True,
        "evidence_sha256": "f" * 64,
        "channel_evidence_executed": True,  # executed -> verdict:"pass" allowed
    }
    # No raise: freeze schema is not in the evidence/certification present-and-False set...
    # but it IS in the token set ("contract"/"execution" not matched; "freeze" not a token),
    # so require_present does not fire.
    validate_axis1_evidence_manifest(freeze, label="axis1_substep_channel_freeze")


# =========================================================================== #
# W-J  — verdict:"pass" reserved for executed evidence; contract-only must not use it.
# =========================================================================== #
def test_wj_contract_only_current_path_emits_pass_then_guard_raises(tmp_path):
    manifest = _mcwf_mps_contract_manifest_current()

    # CURRENT path: the contract-only manifest is written with verdict:"pass" (RED).
    out = _unguarded_write_json(tmp_path / "contract.json", manifest)
    assert out["verdict"] == "pass"
    assert out["backend_executed"] is False
    assert manifest_is_executed(manifest) is False  # nothing executed

    # GUARDED path: a non-executed surface labeled "pass" is rejected (GREEN).
    with pytest.raises(ValueError, match="contract_only|reserved for EXECUTED"):
        validate_axis1_evidence_manifest(manifest, label="axis1_mcwf_mps_state_record_contract")


def test_wj_contract_only_with_deoverloaded_verdict_passes():
    """The W-J fix: use axis1_contract_verdict -> 'contract_only' -> validator passes."""

    manifest = _mcwf_mps_contract_manifest_current()
    manifest["verdict"] = axis1_contract_verdict(
        contract_valid=True, backend_executed=False, oracle_executed=False
    )
    assert manifest["verdict"] == "contract_only"  # de-overloaded
    returned = validate_axis1_evidence_manifest(
        manifest, label="axis1_mcwf_mps_state_record_contract"
    )
    assert returned["verdict"] == "contract_only"


def test_wj_dense_oracle_executed_contract_keeps_pass():
    """The qt_mps contract that executed a dense oracle legitimately keeps verdict:'pass'."""

    manifest = _qt_mps_contract_manifest_dense_executed()
    assert manifest_is_executed(manifest) is True  # dense oracle executed
    returned = validate_axis1_evidence_manifest(
        manifest, label="axis1_qt_mps_state_record_contract"
    )
    assert returned["verdict"] == "pass"  # untouched


def test_wj_executed_mcwf_run_keeps_pass():
    """An honestly-executed MCWF/MPS run (claims_mcwf_mps_backend_execution=True) keeps 'pass'."""

    manifest = _mcwf_mps_execution_manifest_executed()
    assert manifest_is_executed(manifest) is True
    returned = validate_axis1_evidence_manifest(
        manifest, label="axis1_carrier_mcwf_mps_execution"
    )
    assert returned["verdict"] == "pass"
    # the honest True flag is preserved
    assert returned["claims_mcwf_mps_backend_execution"] is True


# =========================================================================== #
# axis1_contract_verdict unit behaviour.
# =========================================================================== #
def test_contract_verdict_helper_matrix():
    assert axis1_contract_verdict(contract_valid=True, backend_executed=False) == "contract_only"
    assert axis1_contract_verdict(contract_valid=True, backend_executed=True) == "pass"
    assert axis1_contract_verdict(contract_valid=True, oracle_executed=True) == "pass"
    assert axis1_contract_verdict(contract_valid=False, backend_executed=True) == "fail"


# =========================================================================== #
# A forbidden claim that is non-bool is rejected (claim flags are structural booleans).
# =========================================================================== #
def test_forbidden_claim_must_be_bool():
    manifest = _state_evidence_manifest_with_false_claims()
    manifest["claims_dense_channel_evidence"] = "false"  # string, not bool
    with pytest.raises(ValueError, match="must be a bool"):
        validate_axis1_evidence_manifest(manifest, label="axis1_state_evolution_evidence")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

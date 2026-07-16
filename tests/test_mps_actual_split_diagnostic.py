from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "mps_actual_split_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("mps_actual_split_diagnostic", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
DIAGNOSTIC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAGNOSTIC)


def _fixture(manifest: dict, fixture_id: str) -> dict:
    return next(
        fixture for fixture in manifest["fixtures"] if fixture["fixture_id"] == fixture_id
    )


def _dense_target(fixture: dict) -> np.ndarray:
    initial = DIAGNOSTIC._complex_array_from_payload(
        fixture["initial_dense_state"], field="initial"
    )
    operator = DIAGNOSTIC._complex_array_from_payload(
        fixture["two_site_operator"], field="operator"
    )
    return DIAGNOSTIC.apply_two_site_dense(
        initial,
        operator,
        support=tuple(fixture["support"]),
        num_sites=fixture["num_sites"],
    )


def _neutral_result(fixtures: dict, fixture: dict, *, accepted: bool = True) -> dict:
    initial = DIAGNOSTIC._complex_array_from_payload(
        fixture["initial_dense_state"], field="initial"
    )
    result = {
        "schema": DIAGNOSTIC.RESULT_SCHEMA,
        "fixture_manifest_sha256": fixtures["content_hash_sha256"],
        "producer": {
            "library": "isolated-example-mps",
            "library_version": "test",
            "array_backend": "independent",
            "device": "cpu",
            "dtype": "complex128",
            "python": "test",
        },
        "selected_fixture_ids": [fixture["fixture_id"]],
        "case_count": 1,
        "cases": [
            {
                "fixture_id": fixture["fixture_id"],
                "fixture_sha256": DIAGNOSTIC.sha256_bytes(
                    DIAGNOSTIC.canonical_json_bytes(fixture)
                ),
                "num_sites": fixture["num_sites"],
                "support": fixture["support"],
                "max_bond": fixture["max_bond"],
                "operation_semantics": fixture["operation_semantics"],
                "route_relation": fixture["route_relation"],
                "candidate_output": {
                    "normalized_state": DIAGNOSTIC._complex_array_payload(initial)
                },
            }
        ],
        "diagnostic_acceptance": {"passed": bool(accepted)},
        "claim_boundary": DIAGNOSTIC.CLAIM_BOUNDARY,
    }
    result["content_hash_sha256"] = DIAGNOSTIC._canonical_hash(
        result, hash_field="content_hash_sha256"
    )
    return result


def _split_record(*, discarded_fraction: float, discarded_raw: float) -> dict:
    return {
        "requested_cutoff_mode": "rsum2",
        "actual_discarded_weight_raw": discarded_raw,
        "actual_discarded_weight_fraction_of_pre_split": discarded_fraction,
    }


def test_default_fixture_manifest_freezes_requested_4_to_6_qubit_surface() -> None:
    manifest = DIAGNOSTIC.build_default_fixture_manifest()

    assert manifest["schema"] == DIAGNOSTIC.FIXTURE_SCHEMA
    assert manifest["dtype"] == "complex128"
    assert manifest["fixture_count"] == 6
    assert {fixture["num_sites"] for fixture in manifest["fixtures"]} == {4, 5, 6}
    assert {fixture["max_bond"] for fixture in manifest["fixtures"]} == {1, 8}
    assert any(
        fixture["operation_semantics"] == "adjacent_two_site_unitary_gate"
        for fixture in manifest["fixtures"]
    )
    assert any(
        fixture["operation_semantics"] == "nonadjacent_two_site_unitary_gate"
        for fixture in manifest["fixtures"]
    )
    assert any(
        fixture["operation_semantics"]
        == "hypothetical_capped_corr_relax_jump_candidate_c_equals_smI_plus_Ism"
        for fixture in manifest["fixtures"]
    )
    assert {fixture["cutoff_mode"] for fixture in manifest["fixtures"]} == {"rsum2"}
    assert all(
        fixture["route_relation"]
        == "HYPOTHETICAL_COUNTERFACTUAL_CURRENT_MCWF_BYPASSES_CAP"
        for fixture in manifest["fixtures"]
        if "corr_relax" in fixture["operation_semantics"]
    )
    assert manifest["neutral_exchange_contract"]["runtime_co_loading"] is False
    assert manifest["claim_boundary"]["production_error_bound"] is False
    assert manifest["claim_boundary"]["record_faithfulness"] is False
    assert manifest["content_hash_sha256"] == DIAGNOSTIC._canonical_hash(
        manifest, hash_field="content_hash_sha256"
    )


def test_corr_relax_production_bypass_witness_is_source_bound() -> None:
    witness = DIAGNOSTIC.mcwf_corr_relax_bypass_witness()
    source = Path(__file__).parents[1] / witness["source_path"]

    assert witness["status"] == "OBSERVED_CURRENT_PRODUCTION_BYPASS"
    assert witness["operator_family"] == "CORR_RELAX"
    assert witness["current_max_bond_forwarding"] is None
    assert witness["capped_fixture_relation"] == "HYPOTHETICAL_COUNTERFACTUAL_ONLY"
    assert len(witness["call_sites"]) == 2
    assert all(site["contract"] == "auto-mps" for site in witness["call_sites"])
    assert all(site["max_bond"] is None for site in witness["call_sites"])
    assert witness["source_sha256"] == DIAGNOSTIC._sha256_file(source)
    assert Path("tests/harness/proc.py") in DIAGNOSTIC.REPO_BINDINGS
    assert Path("tests/harness/gpu_pool.py") in DIAGNOSTIC.REPO_BINDINGS


def test_static_provenance_hashes_every_runtime_binding_without_execution() -> None:
    provenance = DIAGNOSTIC.execution_provenance(require_committed_script=False)
    expected = {path.as_posix() for path in DIAGNOSTIC.REPO_BINDINGS}

    assert expected == set(provenance["binding_file_sha256"])
    assert expected == set(provenance["binding_files_tracked"])
    assert all(
        len(value) == 64 for value in provenance["binding_file_sha256"].values()
    )


@pytest.mark.parametrize(
    ("fixture_id", "fidelity", "discarded_fraction", "discarded_raw"),
    [
        ("adjacent_cnot_4q_cap1", 0.5, 0.5, 0.5),
        ("adjacent_cnot_4q_exact_cap", 1.0, 0.0, 0.0),
    ],
)
def test_runtime_acceptance_requires_expected_cap_fidelity_and_discard(
    fixture_id: str,
    fidelity: float,
    discarded_fraction: float,
    discarded_raw: float,
) -> None:
    fixture = _fixture(DIAGNOSTIC.build_default_fixture_manifest(), fixture_id)
    acceptance = DIAGNOSTIC._case_runtime_acceptance(
        fixture,
        metrics={"normalized_state_fidelity": fidelity},
        split_records=[
            _split_record(
                discarded_fraction=discarded_fraction,
                discarded_raw=discarded_raw,
            )
        ],
        tensor_runtime_ok=True,
    )

    assert acceptance["passed"] is True
    assert acceptance["verdict"] == "PASS"
    assert all(acceptance["checks"].values())


def test_runtime_acceptance_fails_closed_on_empty_or_wrong_split_evidence() -> None:
    fixture = _fixture(
        DIAGNOSTIC.build_default_fixture_manifest(), "adjacent_cnot_4q_cap1"
    )
    empty = DIAGNOSTIC._case_runtime_acceptance(
        fixture,
        metrics={"normalized_state_fidelity": 0.5},
        split_records=[],
        tensor_runtime_ok=True,
    )
    wrong = DIAGNOSTIC._case_runtime_acceptance(
        fixture,
        metrics={"normalized_state_fidelity": 1.0},
        split_records=[
            _split_record(discarded_fraction=0.0, discarded_raw=0.0)
        ],
        tensor_runtime_ok=True,
    )

    assert empty["passed"] is False
    assert empty["checks"]["nonzero_split_ledger"] is False
    assert empty["checks"]["expected_split_count"] is False
    assert wrong["passed"] is False
    assert wrong["checks"]["expected_normalized_state_fidelity"] is False
    assert wrong["checks"]["expected_worst_discarded_weight_fraction"] is False
    assert wrong["checks"]["positive_discard_requirement"] is False


def test_fresh_process_acceptance_requires_matching_gpu_lease_and_cleanup() -> None:
    result = {
        "producer": {"device": "cuda"},
        "runtime_identity": {
            "requested_device": "cuda",
            "process_id": 1234,
            "ECS_GPU_SLOT": "2",
            "CUDA_VISIBLE_DEVICES": "2",
        },
        "fresh_process_execution": {
            "command": ["python", "diagnostic.py", "--worker"],
            "returncode": 0,
            "timed_out": False,
            "process_group_cleanup_verified": True,
            "process_group_id": 1234,
            "gpu_lease_slot": 2,
        },
    }

    assert DIAGNOSTIC._fresh_process_execution_verified(result) is True
    result["fresh_process_execution"]["gpu_lease_slot"] = 1
    assert DIAGNOSTIC._fresh_process_execution_verified(result) is False
    result["fresh_process_execution"]["gpu_lease_slot"] = 2
    result["fresh_process_execution"]["process_group_cleanup_verified"] = False
    assert DIAGNOSTIC._fresh_process_execution_verified(result) is False


def test_independent_dense_application_builds_adjacent_bell_target() -> None:
    fixture = _fixture(
        DIAGNOSTIC.build_default_fixture_manifest(), "adjacent_cnot_4q_cap1"
    )
    target, raw_norm = DIAGNOSTIC._normalized(_dense_target(fixture))
    expected = np.zeros(16, dtype=np.complex128)
    expected[0] = 1.0 / np.sqrt(2.0)
    expected[6] = 1.0 / np.sqrt(2.0)

    assert raw_norm == pytest.approx(1.0, abs=1.0e-14)
    np.testing.assert_allclose(target, expected, rtol=0.0, atol=1.0e-14)


def test_independent_dense_application_preserves_nonadjacent_site_order() -> None:
    fixture = _fixture(
        DIAGNOSTIC.build_default_fixture_manifest(), "nonadjacent_cnot_5q_cap1"
    )
    target, _ = DIAGNOSTIC._normalized(_dense_target(fixture))
    expected = np.zeros(32, dtype=np.complex128)
    expected[0] = 1.0 / np.sqrt(2.0)
    expected[17] = 1.0 / np.sqrt(2.0)

    np.testing.assert_allclose(target, expected, rtol=0.0, atol=1.0e-14)
    schmidt = DIAGNOSTIC._schmidt_records(target, num_sites=5, max_bond=1)
    assert [record["pre_truncation_rank"] for record in schmidt] == [2, 2, 2, 2]
    assert [
        record["discarded_weight_fraction_at_cap"] for record in schmidt
    ] == pytest.approx(
        [0.5, 0.5, 0.5, 0.5], abs=1.0e-14
    )


def test_corr_relax_candidate_creates_normalized_bell_jump() -> None:
    fixture = _fixture(
        DIAGNOSTIC.build_default_fixture_manifest(), "corr_relax_bell_jump_6q_cap1"
    )
    target, raw_norm = DIAGNOSTIC._normalized(_dense_target(fixture))
    expected = np.zeros(64, dtype=np.complex128)
    expected[4] = 1.0 / np.sqrt(2.0)
    expected[8] = 1.0 / np.sqrt(2.0)

    assert raw_norm == pytest.approx(np.sqrt(2.0), abs=1.0e-14)
    np.testing.assert_allclose(target, expected, rtol=0.0, atol=1.0e-14)


def test_corr_relax_sign_corruption_is_discriminated() -> None:
    fixture = _fixture(
        DIAGNOSTIC.build_default_fixture_manifest(), "corr_relax_bell_jump_6q_cap1"
    )
    reference = _dense_target(fixture)
    sigma_minus = np.asarray([[0, 1], [0, 0]], dtype=np.complex128)
    identity = np.eye(2, dtype=np.complex128)
    corrupted = DIAGNOSTIC.apply_two_site_dense(
        DIAGNOSTIC._complex_array_from_payload(
            fixture["initial_dense_state"], field="initial"
        ),
        np.kron(sigma_minus, identity) - np.kron(identity, sigma_minus),
        support=tuple(fixture["support"]),
        num_sites=fixture["num_sites"],
    )

    metrics = DIAGNOSTIC._state_metrics(reference, corrupted)
    assert metrics["normalized_state_fidelity"] == pytest.approx(0.0, abs=1.0e-15)
    assert metrics["pure_state_trace_distance"] == pytest.approx(1.0, abs=1.0e-15)


def test_fixture_validator_rejects_self_consistent_hash_over_wrong_dense_state() -> None:
    manifest = DIAGNOSTIC.build_default_fixture_manifest()
    corrupted = copy.deepcopy(manifest)
    corrupted["fixtures"][0]["initial_dense_state"]["real"][0] = 0.5
    corrupted["content_hash_sha256"] = DIAGNOSTIC._canonical_hash(
        corrupted, hash_field="content_hash_sha256"
    )

    with pytest.raises(ValueError, match="does not match product factors"):
        DIAGNOSTIC.validate_fixture_manifest(corrupted)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("cutoff_mode", "rel", "rsum2"),
        (
            "route_relation",
            "DIRECT_QUBIT_AUTO_MPS_CAP_DIAGNOSTIC",
            "labelled hypothetical",
        ),
    ],
)
def test_fixture_validator_rejects_self_hashed_contract_drift(
    field: str, value: str, message: str
) -> None:
    manifest = DIAGNOSTIC.build_default_fixture_manifest()
    corrupted = copy.deepcopy(manifest)
    fixture = _fixture(corrupted, "corr_relax_bell_jump_6q_cap1")
    fixture[field] = value
    corrupted["content_hash_sha256"] = DIAGNOSTIC._canonical_hash(
        corrupted, hash_field="content_hash_sha256"
    )

    with pytest.raises(ValueError, match=message):
        DIAGNOSTIC.validate_fixture_manifest(corrupted)


def test_fixture_loader_rejects_content_hash_tampering(tmp_path: Path) -> None:
    manifest = DIAGNOSTIC.build_default_fixture_manifest()
    path = tmp_path / "fixtures.json"
    DIAGNOSTIC.write_json_atomic(path, manifest)
    loaded = DIAGNOSTIC.load_fixture_manifest(path)
    assert loaded == manifest

    tampered = copy.deepcopy(manifest)
    tampered["unrecognized_tamper"] = True
    path.write_text(DIAGNOSTIC.json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="content hash mismatch"):
        DIAGNOSTIC.load_fixture_manifest(path)


def test_neutral_result_validator_accepts_non_quimb_fresh_process_payload() -> None:
    fixtures = DIAGNOSTIC.build_default_fixture_manifest()
    fixture = fixtures["fixtures"][0]
    result = _neutral_result(fixtures, fixture)

    DIAGNOSTIC.validate_result_manifest(result, fixture_manifest=fixtures)
    joined = DIAGNOSTIC.join_result_to_fixtures(fixtures, result)
    assert joined == [(fixture, result["cases"][0])]


def test_strict_result_join_rejects_self_hashed_case_metadata_drift() -> None:
    fixtures = DIAGNOSTIC.build_default_fixture_manifest()
    fixture = fixtures["fixtures"][0]
    result = _neutral_result(fixtures, fixture)
    result["cases"][0]["support"] = [0, 3]
    result["content_hash_sha256"] = DIAGNOSTIC._canonical_hash(
        result, hash_field="content_hash_sha256"
    )

    with pytest.raises(ValueError, match="does not join to its fixture"):
        DIAGNOSTIC.validate_result_manifest(result, fixture_manifest=fixtures)


def test_strict_result_join_rejects_unknown_selected_fixture() -> None:
    fixtures = DIAGNOSTIC.build_default_fixture_manifest()
    fixture = fixtures["fixtures"][0]
    result = _neutral_result(fixtures, fixture)
    result["selected_fixture_ids"] = ["unknown_fixture"]
    result["cases"][0]["fixture_id"] = "unknown_fixture"
    result["content_hash_sha256"] = DIAGNOSTIC._canonical_hash(
        result, hash_field="content_hash_sha256"
    )

    with pytest.raises(ValueError, match="unknown fixture ids"):
        DIAGNOSTIC.validate_result_manifest(result, fixture_manifest=fixtures)


def test_cross_library_join_rejects_unaccepted_result() -> None:
    fixtures = DIAGNOSTIC.build_default_fixture_manifest()
    fixture = fixtures["fixtures"][0]
    result = _neutral_result(fixtures, fixture, accepted=False)

    DIAGNOSTIC.validate_result_manifest(result, fixture_manifest=fixtures)
    with pytest.raises(ValueError, match="not accepted for a cross-library claim"):
        DIAGNOSTIC.join_result_to_fixtures(fixtures, result)


def test_split_path_role_labels_do_not_claim_an_unexpected_runtime_path() -> None:
    expected = [{"sequence_index": index} for index in range(7)]
    DIAGNOSTIC._label_split_roles(expected, support=(0, 4))
    assert [record["inferred_path_role"] for record in expected] == [
        "forward_swap_split",
        "forward_swap_split",
        "forward_swap_split",
        "two_site_operator_split",
        "reverse_swap_split",
        "reverse_swap_split",
        "reverse_swap_split",
    ]

    unexpected = [{"sequence_index": index} for index in range(6)]
    DIAGNOSTIC._label_split_roles(unexpected, support=(0, 4))
    assert {record["inferred_path_role"] for record in unexpected} == {
        "unclassified_runtime_path"
    }


def test_atomic_writer_publishes_exact_hash_without_temporary_file(tmp_path: Path) -> None:
    manifest = DIAGNOSTIC.build_default_fixture_manifest()
    destination = tmp_path / "nested" / "fixtures.json"
    byte_hash = DIAGNOSTIC.write_json_atomic(destination, manifest)

    assert byte_hash == DIAGNOSTIC.hashlib.sha256(destination.read_bytes()).hexdigest()
    assert not list(destination.parent.glob(f".{destination.name}.*"))

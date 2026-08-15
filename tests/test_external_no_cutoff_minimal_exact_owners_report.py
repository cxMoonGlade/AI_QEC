"""Fail-closed integration contract for the three minimal exact owners."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest


EXPECTED_STATUS = "VALID_MINIMAL_EXACT_OWNER_QUALIFICATION_CODE_BLOCKED"


def test_report_qualifies_only_the_three_micro_owners() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.report import (
        ACTIVE_PREREG_SHA256,
        build_report,
        validate_report,
    )

    report = build_report()
    validate_report(report, verify_current_sources=True)

    assert report["report_status"] == EXPECTED_STATUS
    assert report["scope"] == "MICRO_QUALIFICATION_ONLY"
    assert report["pair_micro_owner"] == "QUALIFIED"
    assert report["dynamic_add_micro_owner"] == "QUALIFIED"
    assert report["retained_boundary_tn_micro_owner"] == "QUALIFIED"
    assert report["solver_permission"] == "CODE_BLOCKED"
    assert report["preregistration"]["sha256"] == (
        ACTIVE_PREREG_SHA256
    )
    assert report["owner_results"]["pair"]["result"]["support_history"] == [2, 8, 2]
    assert report["owner_results"]["dynamic_add"]["result"][
        "n_exact_pair_add_nodes_history_micro"
    ] == [7, 20, 11]
    assert report["owner_results"]["retained_boundary_tn"]["result"]["unweighted"][
        "exact_value"
    ] == 3
    assert report["owner_results"]["retained_boundary_tn"]["result"]["weighted"][
        "exact_value"
    ] == 6
    assert report["target_pair_owner"] == "UNAVAILABLE/NO_TARGET_QEC_PAIR_LOWERING"
    assert report["target_dynamic_add_owner"] == (
        "UNAVAILABLE/NO_TARGET_QEC_DYNAMIC_ADD_LOWERING"
    )
    assert report["target_retained_boundary_tn_owner"] == (
        "UNAVAILABLE/NO_TARGET_QEC_TN_LOWERING"
    )
    assert report["target_d3_d5_metrics"] == "UNAVAILABLE"
    assert report["delta_tv_cert"] == "UNAVAILABLE/UNANCHORED_FULL_RECORD"
    assert report["route_disposition"] == (
        "NO_ROUTE_KILLED_OR_PROMOTED_BY_MICROFIXTURE"
    )
    assert all(
        control["status"] == "FIRED"
        for control in report["corruption_controls"].values()
    )


def test_report_binds_every_relevant_source_and_test_byte() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.report import (
        REPO,
        build_report,
    )

    report = build_report()
    manifests = report["provenance"]
    required_sources = {
        "scripts/external_baselines/no_cutoff_minimal_exact_owners/model.py",
        "scripts/external_baselines/no_cutoff_minimal_exact_owners/pair.py",
        "scripts/external_baselines/no_cutoff_minimal_exact_owners/add.py",
        "scripts/external_baselines/no_cutoff_minimal_exact_owners/tn.py",
        (
            "scripts/external_baselines/no_cutoff_minimal_exact_owners/"
            "independent_sympy_oracle.py"
        ),
        (
            "scripts/external_baselines/no_cutoff_minimal_exact_owners/"
            "independent_tn_oracle.py"
        ),
        "scripts/external_baselines/no_cutoff_minimal_exact_owners/report.py",
    }
    assert required_sources <= set(manifests["source_sha256"])
    assert {
        "tests/test_external_no_cutoff_minimal_exact_pair_owner.py",
        "tests/test_external_no_cutoff_dynamic_add_micro_owner.py",
        "tests/test_external_no_cutoff_retained_boundary_tn_micro_owner.py",
        "tests/test_external_no_cutoff_minimal_exact_owners_report.py",
    } <= set(manifests["test_sha256"])
    for relative, digest in {
        **manifests["source_sha256"],
        **manifests["test_sha256"],
    }.items():
        assert digest == hashlib.sha256((REPO / relative).read_bytes()).hexdigest()


def test_report_is_compact_canonical_exclusive_and_strictly_reloadable(
    tmp_path: Path,
) -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        canonical_json_bytes,
        sha256_json,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.report import (
        REPORT_INTEGRATION_TEST_FILE,
        build_publication_receipt,
        canonical_report_bytes,
        publish_report,
        read_strict_publication_receipt,
        read_strict_report,
    )

    destination = tmp_path / "report.json"
    written = publish_report(destination)
    raw = destination.read_bytes()
    assert raw == canonical_report_bytes(written)
    assert not raw.endswith(b"\n")
    assert read_strict_report(destination) == written
    with pytest.raises(FileExistsError):
        publish_report(destination)

    destination.write_bytes(json.dumps(written, indent=2, sort_keys=True).encode())
    with pytest.raises(ValueError, match="canonical"):
        read_strict_report(destination)

    destination.write_bytes(canonical_report_bytes(written))
    runtime = written["provenance"]["runtime_identity"]
    execution_body = {
        "command": ["python", "-m", "pytest", "-q", REPORT_INTEGRATION_TEST_FILE],
        "input_identity_sha256": sha256_json(
            {
                "report_test_sha256": written["provenance"]["test_sha256"][
                    REPORT_INTEGRATION_TEST_FILE
                ],
                "source_sha256": written["provenance"]["source_sha256"],
                "python_executable": runtime["python_executable"],
                "pytest_version": runtime["pytest_version"],
            }
        ),
        "passed_count": 7,
        "return_code": 0,
        "status": "PASS",
        "test_file": REPORT_INTEGRATION_TEST_FILE,
    }
    execution = {
        **execution_body,
        "receipt_sha256": sha256_json(execution_body),
    }
    publication = build_publication_receipt(
        report_path=destination,
        report=written,
        report_test_execution=execution,
    )
    receipt_path = tmp_path / "publication_receipt.json"
    receipt_path.write_bytes(canonical_json_bytes(publication))
    assert read_strict_publication_receipt(
        receipt_path, report_path=destination
    ) == publication


def test_strict_reload_rejects_duplicates_floats_and_noncanonical_rationals(
    tmp_path: Path,
) -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.report import (
        canonical_report_bytes,
        publish_report,
        read_strict_report,
    )

    destination = tmp_path / "report.json"
    report = publish_report(destination)
    raw = canonical_report_bytes(report)

    destination.write_bytes(raw[:-1] + b',"scope":"MICRO_QUALIFICATION_ONLY"}')
    with pytest.raises(ValueError, match="duplicate"):
        read_strict_report(destination)

    integer_token = f'"passed_count":{report["provenance"]["qualification_test_execution"]["passed_count"]}'.encode()
    destination.write_bytes(raw.replace(integer_token, integer_token + b".0", 1))
    with pytest.raises(ValueError, match="floating"):
        read_strict_report(destination)

    for rational in ([0, 2], [1, -2], [2, 4]):
        corrupted = deepcopy(report)
        corrupted["independent_oracle_receipts"]["sympy_pair_add"]["receipt"][
            "interference_evidence"
        ]["tail"][0] = rational
        destination.write_bytes(canonical_report_bytes(corrupted))
        with pytest.raises(ValueError, match="denominator|reduced|noncanonical"):
            read_strict_report(destination)


def test_report_fails_closed_when_an_owner_prediction_drifts(monkeypatch) -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners import report

    real = report.run_pair_owner

    def corrupt(program):
        result = real(program)
        result["support_history"] = [2, 7, 2]
        return result

    monkeypatch.setattr(report, "run_pair_owner", corrupt)
    with pytest.raises(ValueError, match="pair owner"):
        report.build_report()


def test_reload_rejects_rehashed_control_outcome_and_add_terminal_forgery() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        sha256_json,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.report import (
        _fixture_identities,
        build_report,
        validate_report,
    )

    report = build_report()

    forged_control = deepcopy(report)
    control = forged_control["corruption_controls"]["tn_remove_edge_d0_d1"]
    control["expected"] = {"weighted_exact_value": 999}
    control["observed"] = {"weighted_exact_value": 999}
    control["receipt_sha256"] = sha256_json(
        {key: value for key, value in control.items() if key != "receipt_sha256"}
    )
    forged_control["content_sha256"] = sha256_json(
        {
            key: value
            for key, value in forged_control.items()
            if key != "content_sha256"
        }
    )
    with pytest.raises(ValueError, match="corruption-control expected ledger"):
        validate_report(forged_control, verify_current_sources=True)

    forged_add = deepcopy(report)
    add_wrapper = forged_add["owner_results"]["dynamic_add"]
    add_result = add_wrapper["result"]
    final_checkpoint = add_result["checkpoints"][-1]
    tiny_terminal = next(
        node
        for node in final_checkpoint["node_table"]
        if node["kind"] == "terminal"
        and node["value"] != [[0, 1], [0, 1], [0, 1], [0, 1]]
    )
    tiny_terminal["value"] = [[7, 1], [0, 1], [0, 1], [0, 1]]
    final_checkpoint["node_table_sha256"] = sha256_json(
        final_checkpoint["node_table"]
    )
    add_wrapper["hash_inventory"]["checkpoint_node_table_sha256"][-1] = (
        final_checkpoint["node_table_sha256"]
    )
    add_wrapper["result_sha256"] = sha256_json(add_result)
    owners = forged_add["owner_results"]
    forged_add["fixture_identities"] = _fixture_identities(
        owners["pair"]["result"],
        owners["dynamic_add"]["result"],
        owners["retained_boundary_tn"]["result"],
    )
    forged_add["content_sha256"] = sha256_json(
        {
            key: value
            for key, value in forged_add.items()
            if key != "content_sha256"
        }
    )
    with pytest.raises(ValueError, match="independent ADD table"):
        validate_report(forged_add, verify_current_sources=True)


def test_reload_rejects_rehashed_nested_hash_evidence_and_version_forgery() -> None:
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.model import (
        sha256_json,
    )
    from scripts.external_baselines.no_cutoff_minimal_exact_owners.report import (
        _fixture_identities,
        build_report,
        validate_report,
    )

    def rehash_content(value):
        value["content_sha256"] = sha256_json(
            {key: item for key, item in value.items() if key != "content_sha256"}
        )

    report = build_report()

    forged_pair = deepcopy(report)
    pair_wrapper = forged_pair["owner_results"]["pair"]
    pair_wrapper["result"]["checkpoints"][0]["map_sha256"] = "0" * 64
    pair_wrapper["hash_inventory"]["checkpoint_map_sha256"][0] = "0" * 64
    pair_wrapper["result_sha256"] = sha256_json(pair_wrapper["result"])
    owners = forged_pair["owner_results"]
    forged_pair["fixture_identities"] = _fixture_identities(
        owners["pair"]["result"],
        owners["dynamic_add"]["result"],
        owners["retained_boundary_tn"]["result"],
    )
    rehash_content(forged_pair)
    with pytest.raises(ValueError, match="pair owner embedded result"):
        validate_report(forged_pair, verify_current_sources=True)

    forged_oracle = deepcopy(report)
    oracle_wrapper = forged_oracle["independent_oracle_receipts"]["sympy_pair_add"]
    oracle = oracle_wrapper["receipt"]
    oracle["checkpoint_literal_maps"][0]["nonzero_witnesses_sha256"] = "0" * 64
    oracle["oracle_payload_sha256"] = sha256_json(
        {key: item for key, item in oracle.items() if key != "oracle_payload_sha256"}
    )
    oracle_wrapper["receipt_sha256"] = sha256_json(oracle)
    rehash_content(forged_oracle)
    with pytest.raises(ValueError, match="SymPy receipt"):
        validate_report(forged_oracle, verify_current_sources=True)

    forged_evidence = deepcopy(report)
    control = forged_evidence["corruption_controls"]["pair_float_rejected"]
    control["evidence"]["qualification_test_receipt_sha256"] = "0" * 64
    control["receipt_sha256"] = sha256_json(
        {key: item for key, item in control.items() if key != "receipt_sha256"}
    )
    rehash_content(forged_evidence)
    with pytest.raises(ValueError, match="corruption-control expected ledger"):
        validate_report(forged_evidence, verify_current_sources=True)

    forged_version = deepcopy(report)
    oracle_wrapper = forged_version["independent_oracle_receipts"]["sympy_pair_add"]
    oracle = oracle_wrapper["receipt"]
    oracle["sympy_version"] = "0.0.0"
    oracle["oracle_payload_sha256"] = sha256_json(
        {key: item for key, item in oracle.items() if key != "oracle_payload_sha256"}
    )
    oracle_wrapper["receipt_sha256"] = sha256_json(oracle)
    rehash_content(forged_version)
    with pytest.raises(ValueError, match="SymPy receipt|SymPy version"):
        validate_report(forged_version, verify_current_sources=True)

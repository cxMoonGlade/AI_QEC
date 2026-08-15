"""Fail-closed report and publication contracts for target lowerings."""

from __future__ import annotations


def _synthetic_structural_test_run() -> dict[str, object]:
    """Build a schema-valid receipt for unit tests, never for publication."""

    from scripts.external_baselines.no_cutoff_target_lowering.model import (
        sha256_json,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        collect_qualification_nodeids,
        qualification_test_command,
    )

    nodeids = collect_qualification_nodeids()
    body: dict[str, object] = {
        "command": qualification_test_command(),
        "nodeids": nodeids,
        "passed": len(nodeids),
        "failed": 0,
    }
    return {**body, "receipt_sha256": sha256_json(body)}


def test_program_bundle_contains_exactly_32_strict_canonical_artifacts() -> None:
    import json

    from scripts.external_baselines.no_cutoff_target_lowering.model import (
        canonical_json_bytes,
    )
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        build_program_artifacts,
        validate_program_artifacts,
    )

    programs = build_program_artifacts()
    validate_program_artifacts(programs)
    expected = {
        f"programs/d{distance}_r{rounds}/{name}.json"
        for distance in (3, 5)
        for rounds in (1, 3, 5, 7)
        for name in ("neutral", "pair", "add_relations", "tn")
    }
    assert set(programs) == expected
    for relative, raw in programs.items():
        assert type(raw) is bytes
        assert raw == canonical_json_bytes(json.loads(raw))
        assert not raw.endswith(b"\n"), relative


def test_historical_firewall_rehashes_prior_bytes_and_recorded_manifests() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        verify_historical_firewall,
    )

    firewall = verify_historical_firewall()
    assert firewall == {
        "structure_report": (
            "88e6175dc3b7d1474c155f06cf1857484a96a8d3f6754a5e91b4c66a5292918b"
        ),
        "minimal_report": (
            "fb645bb886c4b35c8efd2977956c50df9afca88c9c9be58716307d9dc6baf777"
        ),
        "minimal_receipt": (
            "ce6a332e16f2839d50839ee86ad54a269d3bc192ee65ba0795e7a83ecaae29b8"
        ),
        "source_test_manifests_match": True,
    }


def test_all_40_target_cell_oracle_receipts_bind_complete_rows() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        build_cell_oracle_receipts,
        build_program_artifacts,
    )

    receipts = build_cell_oracle_receipts(build_program_artifacts())
    expected_ids = {
        f"{prefix}:d{distance}:r{rounds}"
        for prefix in ("source", "pair", "rref", "add", "tn")
        for distance in (3, 5)
        for rounds in (1, 3, 5, 7)
    }
    assert {receipt["oracle_id"] for receipt in receipts} == expected_ids
    assert len(receipts) == 40
    for receipt in receipts:
        assert receipt["receipt_sha256"]
        assert all(assertion["status"] == "PASS" for assertion in receipt["assertions"])
        assert all(assertion["row_count"] > 0 for assertion in receipt["assertions"])
        assert all(
            assertion["expected_sha256"] == assertion["observed_sha256"]
            for assertion in receipt["assertions"]
        )


def test_pair_coset_and_tn_witness_receipts_bind_complete_catalogs() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        build_non_add_witness_oracle_receipts,
    )

    receipts = build_non_add_witness_oracle_receipts()
    assert {receipt["oracle_id"] for receipt in receipts} == {
        "pair-witness:P1",
        "pair-witness:P2",
        "coset-witness:C1",
        "coset-witness:C2",
        "coset-witness:C3",
        "coset-witness:C4",
        "tn-witness:T1",
        "tn-witness:T2",
        "tn-witness:T3",
        "tn-witness:T4",
    }
    assert all(
        assertion["status"] == "PASS" and assertion["row_count"] > 0
        for receipt in receipts
        for assertion in receipt["assertions"]
    )
    pair_counts = {
        receipt["oracle_id"]: receipt["assertions"][0]["row_count"]
        for receipt in receipts
        if receipt["oracle_id"].startswith("pair-witness:")
    }
    assert pair_counts == {"pair-witness:P1": 256, "pair-witness:P2": 1024}


def test_qualification_report_qualifies_static_objects_and_keeps_solver_blocked() -> None:
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        REPORT_STATUS,
        _assemble_qualification_report_from_receipt,
        build_program_artifacts,
        validate_qualification_report,
    )

    programs = build_program_artifacts()
    test_run = _synthetic_structural_test_run()
    report = _assemble_qualification_report_from_receipt(
        programs, test_run=test_run
    )
    validate_qualification_report(report, programs=programs)

    assert report["report_status"] == REPORT_STATUS
    assert report["scope"] == "STATIC_TARGET_LOWERING_ONLY"
    assert report["solver_permission"] == "CODE_BLOCKED"
    assert report["route_disposition"] == "NONE/STATIC_LOWERING_ONLY"
    assert len(report["artifact_manifest"]) == 32
    assert len(report["cells"]) == 8
    assert len(report["independent_oracle_receipts"]) == 56
    assert len(report["corruption_controls"]) == 33
    add_counts = {
        receipt["oracle_id"].removeprefix("add-truth:"): receipt["assertions"][
            0
        ]["row_count"]
        for receipt in report["independent_oracle_receipts"]
        if receipt["oracle_id"].startswith("add-truth:")
    }
    assert add_counts == {
        "P1": 32_768,
        "P2": 4_194_304,
        "T1": 98_304,
        "T2": 163_840,
        "T3": 114_688,
        "T4": 44_040_192,
    }
    assert all(
        value["headline_eligible"] is False
        and value["status"].startswith("UNAVAILABLE/")
        for value in report["metrics"].values()
    )


def test_publication_rejects_structural_receipt_without_observed_capability(
    tmp_path,
) -> None:
    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        _publish_validated_bundle,
    )

    with pytest.raises(TypeError, match="run_qualification_tests"):
        _publish_validated_bundle(
            tmp_path / "bundle",
            programs={},
            report={},
            observed_test_run=_synthetic_structural_test_run(),  # type: ignore[arg-type]
        )


def test_test_run_receipt_rejects_unexecuted_command_and_nodeid_drift() -> None:
    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        _validate_test_run_receipt,
    )

    valid = _synthetic_structural_test_run()
    for mutation in ("command", "missing_node", "extra_node"):
        body = {key: value for key, value in valid.items() if key != "receipt_sha256"}
        body["nodeids"] = list(body["nodeids"])
        if mutation == "command":
            body["command"] = ["never-executed"]
        elif mutation == "missing_node":
            body["nodeids"] = body["nodeids"][:-1]
            body["passed"] = len(body["nodeids"])
        else:
            body["nodeids"].append("tests/not_in_prereg.py::test_fabricated")
            body["nodeids"].sort()
            body["passed"] = len(body["nodeids"])
        receipt = {**body, "receipt_sha256": sha256_json(body)}
        with pytest.raises(ValueError, match="command drift|node-id set drift"):
            _validate_test_run_receipt(receipt)


def test_production_report_assembly_rejects_structural_receipt_without_capability() -> None:
    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        assemble_qualification_report,
    )

    with pytest.raises(TypeError, match="run_qualification_tests"):
        assemble_qualification_report(  # type: ignore[arg-type]
            {}, observed_test_run=_synthetic_structural_test_run()
        )


def test_publication_validator_rejects_self_consistent_arbitrary_files(tmp_path) -> None:
    import hashlib

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.model import sha256_json
    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        ACTIVE_PREREG_SHA256,
        PUBLICATION_RECEIPT_SCHEMA,
        validate_publication_receipt,
    )

    output_dir = tmp_path / "forged"
    manifest: dict[str, str] = {}
    for distance in (3, 5):
        for rounds in (1, 3, 5, 7):
            for name in ("neutral", "pair", "add_relations", "tn"):
                relative = f"programs/d{distance}_r{rounds}/{name}.json"
                path = output_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"not-json")
                manifest[relative] = hashlib.sha256(b"not-json").hexdigest()
    report_raw = b"{}"
    (output_dir / "qualification_report.json").write_bytes(report_raw)
    manifest["qualification_report.json"] = hashlib.sha256(report_raw).hexdigest()
    body: dict[str, object] = {
        "_schema": PUBLICATION_RECEIPT_SCHEMA,
        "preregistration_sha256": ACTIVE_PREREG_SHA256,
        "report_path": "qualification_report.json",
        "report_sha256": manifest["qualification_report.json"],
        "artifact_manifest": manifest,
        "artifact_manifest_sha256": sha256_json(manifest),
    }
    receipt = {**body, "content_sha256": sha256_json(body)}
    (output_dir / "publication_receipt.json").write_bytes(
        __import__(
            "scripts.external_baselines.no_cutoff_target_lowering.model",
            fromlist=["canonical_json_bytes"],
        ).canonical_json_bytes(receipt)
    )
    with pytest.raises(ValueError, match="strict|JSON|program|schema"):
        validate_publication_receipt(receipt, output_dir=output_dir, report={})


def test_source_drift_is_rejected_before_cached_programs_can_be_reused(
    monkeypatch,
) -> None:
    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering import report

    report.build_program_artifacts()
    original = report._secure_file_sha256

    def changed(path):
        observed = original(path)
        if path.name == "independent_pair_oracle.py":
            return "0" * 64
        return observed

    monkeypatch.setattr(report, "_secure_file_sha256", changed)
    with pytest.raises(ValueError, match="changed after module import"):
        report.build_program_artifacts()


def test_publication_rejects_symlink_root_and_intermediate_parent(tmp_path) -> None:
    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        _open_directory_no_symlinks,
        _open_relative_parent,
    )

    outside = tmp_path / "outside"
    outside.mkdir()
    root_link = tmp_path / "root-link"
    root_link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        _open_directory_no_symlinks(root_link)

    target = tmp_path / "target"
    target.mkdir()
    (target / "programs").symlink_to(outside, target_is_directory=True)
    descriptor = _open_directory_no_symlinks(target)
    try:
        with pytest.raises(ValueError, match="symlink"):
            _open_relative_parent(
                descriptor, "programs/d3_r1/neutral.json", create=True
            )
    finally:
        __import__("os").close(descriptor)
    assert list(outside.iterdir()) == []


def test_atomic_directory_commit_refuses_existing_destination(tmp_path) -> None:
    import os

    import pytest

    from scripts.external_baselines.no_cutoff_target_lowering.report import (
        _open_directory_no_symlinks,
        _renameat2_noreplace,
    )

    (tmp_path / "stage").mkdir()
    (tmp_path / "destination").mkdir()
    descriptor = _open_directory_no_symlinks(tmp_path)
    try:
        with pytest.raises(FileExistsError, match="refuses to overwrite"):
            _renameat2_noreplace(descriptor, "stage", "destination")
    finally:
        os.close(descriptor)

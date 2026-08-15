"""Contracts for the frozen n=8, active-rank-3 GCAPEPS differential."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO / "scripts" / "external_baselines"
EMITTER_PATH = SCRIPT_DIR / "emit_gcapeps_n8_r3_fixture.py"
ANCHOR_PATH = SCRIPT_DIR / "gcapeps_n8_r3_dense_anchor.py"
COMPARATOR_PATH = SCRIPT_DIR / "compare_gcapeps_n8_r3_differential.py"
PLAIN_PATH = SCRIPT_DIR / "plain_quimb_n8_r3_worker.py"
GC_WORKER_PATH = SCRIPT_DIR / "gcapeps_n8_r3_worker.py"
CONTROLS_PATH = SCRIPT_DIR / "run_gcapeps_n8_r3_controls.py"
RUNNER_PATH = SCRIPT_DIR / "run_gcapeps_n8_r3_differential.py"


def _load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_fixture_identity_gate_streams_and_route_are_pinned() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture")
    fixture = emitter.build_fixture()

    assert emitter.EXPECTED_FIXTURE_SHA256 == (
        "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
    )
    assert emitter.validate_fixture(fixture) == emitter.EXPECTED_FIXTURE_SHA256
    assert emitter.canonical_sha256(fixture) == emitter.EXPECTED_FIXTURE_SHA256
    assert fixture["schema"] == emitter.FIXTURE_SCHEMA
    assert fixture["n_qubits"] == 8
    assert fixture["active_rank"] == 3
    assert fixture["site_order"] == [
        [0, 0],
        [0, 1],
        [0, 2],
        [0, 3],
        [1, 0],
        [1, 1],
        [1, 2],
        [1, 3],
    ]
    assert fixture["preparation"]["gate_stream_sha256"] == (
        "e42a195ba2736164700fcf86c1f5949f5a49d39c1932cfd9ee6b8cf6efab3538"
    )
    assert fixture["clifford"]["gate_stream_sha256"] == (
        "aeb75e08b6ac4a592d31199c2eafe9ed0c968465e50d05fa45b7d139a397e50c"
    )
    assert fixture["routing"] == {
        "dependence_set": [0, 3, 4, 7],
        "conservative_support": list(range(8)),
        "root": 0,
        "vertices": [0, 1, 2, 3, 4, 7],
        "edges": [[0, 1], [0, 4], [1, 2], [2, 3], [3, 7]],
    }


def test_numpy_anchor_independently_matches_its_two_state_action_forms() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_anchor")
    anchor = _load_script(ANCHOR_PATH, "gcapeps_n8_r3_dense_anchor")
    fixture = emitter.build_fixture()

    computation = anchor.compute_anchor(fixture)

    assert computation["schema"] == anchor.ANCHOR_COMPUTATION_SCHEMA
    assert computation["fixture_sha256"] == emitter.canonical_sha256(fixture)
    for name in (
        "closed_form_preparation",
        "gate_replay_preparation",
        "residual_state",
        "physical_preparation_after_clifford",
        "physical_from_residual_lift",
        "physical_from_signed_terms",
    ):
        vector = computation["vectors"][name]
        assert vector.shape == (256,)
        assert vector.dtype == np.dtype("complex128")
        assert np.all(np.isfinite(vector))

    closed = computation["vectors"]["closed_form_preparation"]
    replayed = computation["vectors"]["gate_replay_preparation"]
    assert np.count_nonzero(closed) == 4
    assert np.max(np.abs(closed - replayed)) <= 2.0e-15
    assert np.linalg.norm(closed) == 1.0

    lifted = computation["vectors"]["physical_from_residual_lift"]
    physical = computation["vectors"]["physical_from_signed_terms"]
    assert np.max(np.abs(lifted - physical)) <= 2.0e-15
    assert abs(np.linalg.norm(physical) - 1.0) <= 2.0e-15
    assert computation["imports_forbidden_simulator_module"] is False
    assert computation["enters_efficiency_timing_or_rss"] is False


def test_complete_vector_comparator_accepts_identical_c128_vectors() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_compare")
    anchor = _load_script(ANCHOR_PATH, "gcapeps_n8_r3_anchor_compare")
    comparator = _load_script(
        COMPARATOR_PATH,
        "compare_gcapeps_n8_r3_differential",
    )
    fixture = emitter.build_fixture()
    vector = anchor.compute_anchor(fixture)["vectors"]["residual_state"]

    comparison = comparator.compare_complete_vectors(
        vector,
        vector.copy(),
        bands=fixture["metric_bands"],
    )

    assert comparison["verdict"] == "AGREE"
    assert comparison["d_inf"] == 0.0
    assert comparison["d_2"] == 0.0
    assert comparison["d_rel"] == 0.0
    assert comparison["d_norm"] == 0.0
    assert comparison["fidelity"] == 1.0
    assert comparison["infidelity"] == 0.0


def test_plain_quimb_product_operator_adapter_names_and_transposes_raw_axes() -> None:
    plain = _load_script(PLAIN_PATH, "plain_quimb_n8_r3_worker_orientation")
    desired_output_input = np.asarray(
        [[1.0 + 0.0j, 2.0j], [3.0 + 0.0j, 4.0 + 0.0j]],
        dtype=np.complex128,
    )

    raw_bra_ket = plain.quimb_product_operator_raw_bra_ket(
        desired_output_input
    )

    assert raw_bra_ket.dtype == np.dtype("complex128")
    assert raw_bra_ket.flags.c_contiguous
    assert np.array_equal(raw_bra_ket, desired_output_input.T)
    assert np.array_equal(raw_bra_ket.T, desired_output_input)


def test_numpy_anchor_has_static_and_fresh_process_import_independence() -> None:
    source = ANCHOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ANCHOR_PATH))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(
        {"quimb", "stim", "sdim", "gcapeps", "emit_gcapeps_n8_r3_fixture"}
    )

    program = "\n".join(
        (
            "import importlib.util, json, pathlib, sys",
            f"path = pathlib.Path({str(ANCHOR_PATH)!r})",
            "spec = importlib.util.spec_from_file_location('dense_anchor_runtime', path)",
            "module = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(module)",
            "forbidden = sorted(name for name in sys.modules if "
            "name.split('.', 1)[0] in {'quimb', 'stim', 'sdim'} or "
            "'.gcapeps' in name)",
            "print(json.dumps(forbidden))",
        )
    )
    process = subprocess.run(
        [sys.executable, "-I", "-c", program],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(process.stdout) == []


def test_complete_vector_comparator_catches_phase_scale_element_and_axis_changes() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_corrupt")
    anchor = _load_script(ANCHOR_PATH, "gcapeps_n8_r3_anchor_corrupt")
    comparator = _load_script(COMPARATOR_PATH, "gcapeps_n8_r3_compare_corrupt")
    fixture = emitter.build_fixture()
    vector = anchor.compute_anchor(fixture)["vectors"]["physical_from_signed_terms"]

    phase = np.ascontiguousarray(1.0j * vector)
    phase_result = comparator.compare_complete_vectors(
        vector,
        phase,
        bands=fixture["metric_bands"],
    )
    assert phase_result["verdict"] == "MISMATCH"
    assert phase_result["infidelity"] <= 1.0e-12
    assert phase_result["d_rel"] > 1.0

    scaled = np.ascontiguousarray((1.0 + 1.0e-6) * vector)
    scale_result = comparator.compare_complete_vectors(
        vector,
        scaled,
        bands=fixture["metric_bands"],
    )
    assert scale_result["verdict"] == "MISMATCH"
    assert scale_result["infidelity"] <= 1.0e-12
    assert scale_result["d_norm"] > 1.0e-8

    element = vector.copy()
    element[0] += np.complex128(1.0e-6)
    assert comparator.compare_complete_vectors(
        vector,
        element,
        bands=fixture["metric_bands"],
    )["verdict"] == "MISMATCH"

    swapped = np.ascontiguousarray(
        vector.reshape((2,) * 8).transpose(7, 1, 2, 3, 4, 5, 6, 0).reshape(256)
    )
    assert comparator.compare_complete_vectors(
        vector,
        swapped,
        bands=fixture["metric_bands"],
    )["verdict"] == "MISMATCH"


def test_shared_candidate_corruption_can_pass_pair_but_fails_anchor() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_shared")
    anchor = _load_script(ANCHOR_PATH, "gcapeps_n8_r3_anchor_shared")
    comparator = _load_script(COMPARATOR_PATH, "gcapeps_n8_r3_compare_shared")
    fixture = emitter.build_fixture()
    reference = anchor.compute_anchor(fixture)["vectors"]["physical_from_signed_terms"]
    shared = reference.copy()
    shared[0] += np.complex128(1.0e-6)

    pair = comparator.compare_complete_vectors(
        shared,
        shared.copy(),
        bands=fixture["metric_bands"],
    )
    against_anchor = comparator.compare_complete_vectors(
        reference,
        shared,
        bands=fixture["metric_bands"],
    )

    assert pair["verdict"] == "AGREE"
    assert against_anchor["verdict"] == "MISMATCH"


def test_complete_vector_comparator_rejects_invalid_arrays_before_metrics() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_invalid")
    anchor = _load_script(ANCHOR_PATH, "gcapeps_n8_r3_anchor_invalid")
    comparator = _load_script(COMPARATOR_PATH, "gcapeps_n8_r3_compare_invalid")
    fixture = emitter.build_fixture()
    vector = anchor.compute_anchor(fixture)["vectors"]["residual_state"]

    invalid = [
        vector.astype(np.complex64),
        vector[:-1],
        np.full(256, np.complex128(np.nan + 0.0j)),
        np.zeros(256, dtype=np.complex128),
    ]
    for corrupted in invalid:
        with pytest.raises(ValueError):
            comparator.compare_complete_vectors(
                vector,
                corrupted,
                bands=fixture["metric_bands"],
            )


def test_fixture_semantic_validator_rejects_frozen_field_corruptions() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_mutations")
    fixture = emitter.build_fixture()
    corruptions = []

    wrong_site = copy.deepcopy(fixture)
    wrong_site["site_map"][7]["coordinate"] = [0, 0]
    corruptions.append(wrong_site)

    wrong_gate = copy.deepcopy(fixture)
    wrong_gate["clifford"]["gates"][5]["token"] = "S"
    corruptions.append(wrong_gate)

    wrong_phase = copy.deepcopy(fixture)
    wrong_phase["physical_terms"][0]["word_phase"] = 1
    corruptions.append(wrong_phase)

    wrong_route = copy.deepcopy(fixture)
    wrong_route["routing"]["vertices"] = [0, 3, 4, 7]
    corruptions.append(wrong_route)

    wrong_limit = copy.deepcopy(fixture)
    wrong_limit["gcapeps_resource_limits"]["max_total_operator_elements"] = 177
    corruptions.append(wrong_limit)

    for corrupted in corruptions:
        with pytest.raises(ValueError, match="semantic mismatch"):
            emitter.validate_fixture(corrupted)


def test_fixture_cli_writes_exact_canonical_bytes_and_refuses_replace(tmp_path: Path) -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_cli")
    output = tmp_path / "fixture.json"

    first = subprocess.run(
        [sys.executable, str(EMITTER_PATH), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert first.returncode == 0, first.stderr
    fixture = emitter.build_fixture()
    assert output.read_bytes() == emitter.canonical_json_bytes(fixture)
    assert emitter.validate_fixture(json.loads(output.read_bytes())) == (
        emitter.EXPECTED_FIXTURE_SHA256
    )

    second = subprocess.run(
        [sys.executable, str(EMITTER_PATH), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert second.returncode != 0
    assert output.read_bytes() == emitter.canonical_json_bytes(fixture)


def test_anchor_cli_seals_private_vectors_without_timing_or_replace(tmp_path: Path) -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_anchor_cli")
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_bytes(emitter.canonical_json_bytes(emitter.build_fixture()))
    output_directory = tmp_path / "anchor-output"
    output_directory.mkdir()

    process = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ANCHOR_PATH),
            "--fixture",
            str(fixture_path),
            "--output-directory",
            str(output_directory),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert process.returncode == 0, process.stderr
    expected_names = {
        "anchor_report.json",
        "closed_form_preparation.npy",
        "gate_replay_preparation.npy",
        "residual_state.npy",
        "physical_preparation_after_clifford.npy",
        "physical_from_residual_lift.npy",
        "physical_from_signed_terms.npy",
    }
    assert {path.name for path in output_directory.iterdir()} == expected_names
    report = json.loads((output_directory / "anchor_report.json").read_bytes())
    assert report["schema"].endswith("gcapeps_n8_r3_dense_anchor_worker.v1")
    assert report["fixture"]["sha256"] == emitter.EXPECTED_FIXTURE_SHA256
    assert report["anchor_self_verdict"] == "PASS"
    assert report["all_checks_passed"] is True
    assert report["scope"]["enters_efficiency_timing_or_rss"] is False
    assert report["runtime_provenance"]["forbidden_loaded_modules"] == []
    assert "timing" not in report
    for name, row in report["vectors"].items():
        vector = np.load(output_directory / row["relative_path"], allow_pickle=False)
        assert vector.shape == (256,)
        assert vector.dtype == np.dtype("complex128")
        assert row["sha256"] == hashlib.sha256(
            np.ascontiguousarray(vector, dtype="<c16").tobytes()
        ).hexdigest()
        assert name in row["relative_path"]

    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output_directory.iterdir()
    }
    repeated = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ANCHOR_PATH),
            "--fixture",
            str(fixture_path),
            "--output-directory",
            str(output_directory),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert repeated.returncode != 0
    assert before == {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output_directory.iterdir()
    }


def test_aggregate_grading_keeps_candidates_symmetric_and_sdim_non_numeric() -> None:
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_fixture_grade")
    anchor = _load_script(ANCHOR_PATH, "gcapeps_n8_r3_anchor_grade")
    comparator = _load_script(COMPARATOR_PATH, "gcapeps_n8_r3_compare_grade")
    fixture = emitter.build_fixture()
    vectors = anchor.compute_anchor(fixture)["vectors"]

    grading = comparator.grade_candidate_state_action(
        plain_preparation=vectors["gate_replay_preparation"],
        gcapeps_preparation=vectors["closed_form_preparation"],
        plain_after_clifford=vectors["physical_preparation_after_clifford"],
        gcapeps_after_clifford=vectors["physical_preparation_after_clifford"].copy(),
        plain_final=vectors["physical_from_signed_terms"],
        gcapeps_final=vectors["physical_from_residual_lift"],
        gcapeps_residual=vectors["residual_state"].copy(),
        anchor_vectors=vectors,
        bands=fixture["metric_bands"],
    )
    assert grading["differential_verdict"] == "AGREE"
    assert grading["anchor_verdict"] == "PASS"
    assert grading["candidate_role"] == "equal_status"

    passing = comparator.terminal_semantics(
        differential_verdict=grading["differential_verdict"],
        anchor_verdict=grading["anchor_verdict"],
        sdim_frame_verdict="PASS",
        exact_structure_and_fairness_passed=True,
        controls_passed=True,
        provenance_passed=True,
        publication_preflight_passed=True,
    )
    assert passing == {
        "differential_verdict": "AGREE",
        "anchor_verdict": "PASS",
        "sdim_frame_verdict": "PASS",
        "state_action_qualification_status": (
            "BOUNDED_EXACT_SMALL_STATE_ACTION_ANCHORED"
        ),
        "efficiency_interpretation": (
            "ELIGIBLE_ONLY_IF_DIFFERENTIAL_ANCHOR_AND_SDIM_AGREEMENT"
        ),
    }

    sdim_failed = comparator.terminal_semantics(
        differential_verdict=grading["differential_verdict"],
        anchor_verdict=grading["anchor_verdict"],
        sdim_frame_verdict="FAIL",
        exact_structure_and_fairness_passed=True,
        controls_passed=True,
        provenance_passed=True,
        publication_preflight_passed=True,
    )
    assert sdim_failed["differential_verdict"] == "AGREE"
    assert sdim_failed["anchor_verdict"] == "PASS"
    assert sdim_failed["state_action_qualification_status"] == "INELIGIBLE"
    assert sdim_failed["efficiency_interpretation"] == "INELIGIBLE"

    unfair = comparator.terminal_semantics(
        differential_verdict=grading["differential_verdict"],
        anchor_verdict=grading["anchor_verdict"],
        sdim_frame_verdict="PASS",
        exact_structure_and_fairness_passed=False,
        controls_passed=True,
        provenance_passed=True,
        publication_preflight_passed=True,
    )
    assert unfair["state_action_qualification_status"] == "INELIGIBLE"
    assert unfair["efficiency_interpretation"] == "INELIGIBLE"


def test_fresh_worker_schedule_and_efficiency_summary_are_frozen() -> None:
    runner = _load_script(RUNNER_PATH, "run_gcapeps_n8_r3_differential_schedule")

    assert runner.warmup_launch_order() == ("plain", "gcapeps")
    assert runner.measured_launch_order() == (
        "plain",
        "gcapeps",
        "gcapeps",
        "plain",
        "plain",
        "gcapeps",
        "gcapeps",
        "plain",
        "plain",
        "gcapeps",
        "gcapeps",
        "plain",
    )
    assert runner.WORKER_RESOURCE_ENVELOPE == {
        "MemoryMax": 8 * 1024**3,
        "MemorySwapMax": 0,
        "RuntimeMaxSec": 300,
        "TasksMax": 32,
    }

    summary = runner.summarize_efficiency_samples(
        plain_update_ns=[10, 12, 11, 13, 9, 10],
        gcapeps_update_ns=[5, 6, 5, 7, 4, 5],
        plain_peak_rss_bytes=[100, 101, 99, 102, 98, 100],
        gcapeps_peak_rss_bytes=[50, 52, 49, 51, 48, 50],
        interpretation_eligible=True,
    )
    assert summary["sample_count_per_lane"] == 6
    assert summary["plain_update_ns"]["median"] == 10.5
    assert summary["plain_update_ns"]["mad"] == 1.0
    assert summary["update_ratio_plain_over_gcapeps"] == 2.1
    assert summary["rss_ratio_plain_over_gcapeps"] == 2.0
    assert summary["directional_hypothesis_plain_slower"] is True

    ineligible = runner.summarize_efficiency_samples(
        plain_update_ns=[10, 12, 11, 13, 9, 10],
        gcapeps_update_ns=[5, 6, 5, 7, 4, 5],
        plain_peak_rss_bytes=[100, 101, 99, 102, 98, 100],
        gcapeps_peak_rss_bytes=[50, 52, 49, 51, 48, 50],
        interpretation_eligible=False,
    )
    assert ineligible["update_ratio_plain_over_gcapeps"] is None
    assert ineligible["rss_ratio_plain_over_gcapeps"] is None
    assert ineligible["directional_hypothesis_plain_slower"] is None

    with pytest.raises(ValueError):
        runner.summarize_efficiency_samples(
            plain_update_ns=[10, 12, 11, 13, 9, 0],
            gcapeps_update_ns=[5, 6, 5, 7, 4, 5],
            plain_peak_rss_bytes=[100] * 6,
            gcapeps_peak_rss_bytes=[50] * 6,
            interpretation_eligible=True,
        )


def test_bundle_publication_is_directory_atomic_noreplace_and_not_self_attesting(
    tmp_path: Path,
) -> None:
    runner = _load_script(RUNNER_PATH, "run_gcapeps_n8_r3_publish")
    destination = tmp_path / "gcapeps-result"

    with runner.preflight_publication(destination) as preflight:
        confirmation = runner.publish_bundle_noreplace(
            preflight,
            artifacts={"raw/sample.bin": b"sample-bytes"},
            manifest_payload={"schema": runner.RESULT_SCHEMA, "verdict": "TEST_ONLY"},
        )

    assert confirmation["rename_noreplace_success"] is True
    assert confirmation["parent_directory_fsync_success"] is True
    assert confirmation["published_destination_identity_recheck_success"] is True
    assert destination.is_dir()
    assert (destination / "raw" / "sample.bin").read_bytes() == b"sample-bytes"
    manifest = json.loads((destination / "manifest.json").read_bytes())
    assert manifest["schema"] == runner.RESULT_SCHEMA
    assert manifest["publication_status"] == "prepared_for_atomic_publication"
    assert manifest["claims_offline_durability_confirmation"] is False
    assert manifest["target_filesystem_collision_probe_passed"] is True
    assert manifest["target_filesystem_noreplace_success_probe_passed"] is True
    assert manifest["artifact_file_fsync_success_attested_in_bundle"] is False
    assert manifest["staging_directory_fsync_success_attested_in_bundle"] is False
    assert manifest["final_staged_set_revalidation_success_attested_in_bundle"] is False
    assert manifest["rename_noreplace_success_attested_in_bundle"] is False
    assert manifest["parent_directory_fsync_success_attested_in_bundle"] is False
    assert (
        manifest["published_destination_identity_recheck_success_attested_in_bundle"]
        is False
    )
    assert manifest["successful_supervisor_return_is_only_publication_confirmation"] is True
    artifact = manifest["artifacts"]["raw/sample.bin"]
    assert artifact["sha256"] == hashlib.sha256(b"sample-bytes").hexdigest()
    assert artifact["size_bytes"] == len(b"sample-bytes")

    with pytest.raises(FileExistsError):
        runner.preflight_publication(destination)
    assert (destination / "raw" / "sample.bin").read_bytes() == b"sample-bytes"
    assert not any(path.name.startswith(".gcapeps-stage-") for path in tmp_path.iterdir())


def test_publication_detects_destination_race_and_preserves_existing_entry(
    tmp_path: Path,
) -> None:
    runner = _load_script(RUNNER_PATH, "run_gcapeps_n8_r3_publish_race")
    destination = tmp_path / "raced-result"
    with runner.preflight_publication(destination) as preflight:
        destination.mkdir()
        marker = destination / "owner.txt"
        marker.write_text("external-owner", encoding="utf-8")
        with pytest.raises(FileExistsError):
            runner.publish_bundle_noreplace(
                preflight,
                artifacts={"sample.bin": b"ours"},
                manifest_payload={"schema": runner.RESULT_SCHEMA},
            )
    assert marker.read_text(encoding="utf-8") == "external-owner"
    assert not any(path.name.startswith(".gcapeps-stage-") for path in tmp_path.iterdir())


def test_publication_detects_parent_path_identity_swap_before_staging(
    tmp_path: Path,
) -> None:
    runner = _load_script(RUNNER_PATH, "run_gcapeps_n8_r3_publish_parent_swap")
    parent = tmp_path / "parent"
    parent.mkdir()
    destination = parent / "result"
    preflight = runner.preflight_publication(destination)
    displaced = tmp_path / "displaced-parent"
    parent.rename(displaced)
    parent.mkdir()
    try:
        with pytest.raises(RuntimeError, match="parent path identity"):
            runner.publish_bundle_noreplace(
                preflight,
                artifacts={"sample.bin": b"ours"},
                manifest_payload={"schema": runner.RESULT_SCHEMA},
            )
    finally:
        preflight.close()
    assert not destination.exists()
    assert not (displaced / "result").exists()
    assert not any(
        path.name.startswith(".gcapeps-stage-") for path in displaced.iterdir()
    )



def test_controls_bundle_uses_gate_and_rejects_self_authorization(
    tmp_path: Path,
) -> None:
    runner = _load_script(RUNNER_PATH, "run_gcapeps_n8_r3_controls_bundle")
    emitter = _load_script(EMITTER_PATH, "emit_gcapeps_n8_r3_controls_bundle")
    sources = {
        "fixture_emitter": runner._sha256_file(EMITTER_PATH),
        "numpy_anchor": runner._sha256_file(ANCHOR_PATH),
        "complete_vector_comparator": runner._sha256_file(COMPARATOR_PATH),
        "plain_quimb_worker": runner._sha256_file(PLAIN_PATH),
        "gcapeps_worker": runner._sha256_file(GC_WORKER_PATH),
        "sdim_worker": runner._sha256_file(SCRIPT_DIR / "gcapeps_n8_r3_sdim_worker.py"),
        "controls_runner": runner._sha256_file(CONTROLS_PATH),
    }
    fixture_bytes = emitter.canonical_json_bytes(emitter.build_fixture())

    def publish_controls(name: str, *, self_authorized: bool) -> Path:
        external = {
            key: {"status": "PASS", "passed": True}
            for key in (
                "one_site_quimb_orientation",
                "gc_construction_pytests",
                "sdim_normal_and_first_sign_flip",
            )
        }
        report = {
            "schema": runner.CONTROLS_SCHEMA,
            "report_role": "supervisor_private_controls_only",
            "source_sha256": sources,
            "external_evidence": external,
            "external_evidence_all_supplied_and_passed": True,
            "controls_passed": True,
            "controls_gate_passed_for_later_preflights": True,
            "target_execution_authorized_by_this_report_alone": self_authorized,
            "execution_scope": {
                "clean_plain_n8_candidate_executed": False,
                "clean_gcapeps_n8_candidate_executed": False,
                "anchor_enters_timing_or_rss": False,
                "sdim_enters_timing_or_rss": False,
            },
        }
        report["content_sha256"] = hashlib.sha256(
            runner._canonical_json_bytes(report)
        ).hexdigest()
        destination = tmp_path / name
        with runner.preflight_publication(destination) as preflight:
            runner.publish_bundle_noreplace(
                preflight,
                artifacts={
                    "fixture.json": fixture_bytes,
                    "controls.json": runner._canonical_json_bytes(report),
                    "orientation.json": b"{}",
                    "gc-construction.json": b"{}",
                    "sdim-normal.json": b"{}",
                    "sdim-flip.json": b"{}",
                },
                manifest_payload={
                    "schema": runner.CONTROLS_SCHEMA,
                    "status": "PASS",
                    "controls_passed": True,
                    "clean_n8_plain_candidate_executed": False,
                    "clean_n8_gcapeps_candidate_executed": False,
                    "fixture_sha256": runner.EXPECTED_FIXTURE_SHA256,
                    "parent_commit": "0" * 40,
                    "fork_commit": runner.EXPECTED_FORK_COMMIT,
                },
            )
        return destination

    accepted = runner.validate_controls_bundle(
        publish_controls("accepted-controls", self_authorized=False)
    )
    assert accepted["passed"] is True
    assert accepted["controls"][
        "controls_gate_passed_for_later_preflights"
    ] is True
    assert accepted["controls"][
        "target_execution_authorized_by_this_report_alone"
    ] is False

    rejected = publish_controls("self-authorized-controls", self_authorized=True)
    with pytest.raises(ValueError, match="controls report did not pass"):
        runner.validate_controls_bundle(rejected)


def test_worker_environment_and_systemd_command_are_fail_closed(tmp_path: Path) -> None:
    runner = _load_script(RUNNER_PATH, "run_gcapeps_n8_r3_worker_env")
    private = tmp_path / "private-runtime"
    private.mkdir()
    environment = runner.build_worker_environment(
        {
            "PATH": "/usr/bin",
            "HOME": "/not-private",
            "PYTHONPATH": "/leak",
            "CONDA_PREFIX": "/leak-conda",
            "CONDA_SHLVL": "2",
            "_CE_CONDA": "1",
            "VIRTUAL_ENV": "/leak-venv",
            "CUDA_HOME": "/cuda",
            "LD_LIBRARY_PATH": "/libs",
            "OMP_NUM_THREADS": "99",
        },
        private_root=private,
    )
    for forbidden in (
        "PYTHONPATH",
        "CONDA_PREFIX",
        "CONDA_SHLVL",
        "_CE_CONDA",
        "VIRTUAL_ENV",
        "CUDA_HOME",
        "LD_LIBRARY_PATH",
    ):
        assert forbidden not in environment
    assert environment["HOME"] == str(private.resolve())
    assert environment["CUDA_VISIBLE_DEVICES"] == ""
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["PYTHONHASHSEED"] == "0"
    assert environment["TZ"] == "UTC"
    assert environment["NUMBA_CACHE_DIR"] == str(
        (private / "numba-cache").resolve()
    )
    assert (private / "numba-cache").is_dir()
    assert (private / "numba-cache").stat().st_mode & 0o777 == 0o700
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        assert environment[name] == "1"

    command = runner.build_systemd_worker_command(
        unit_name="gcapeps-test-0123456789abcdef",
        cpu_id=3,
        worker_command=["/bin/true", "--example"],
    )
    assert command[:5] == [
        "systemd-run",
        "--user",
        "--wait",
        "--pipe",
        "--service-type=exec",
    ]
    joined = "\n".join(command)
    for property_text in (
        "MemoryAccounting=yes",
        "MemoryMax=8589934592",
        "MemorySwapMax=0",
        "RuntimeMaxSec=300",
        "TasksMax=32",
        "CPUAffinity=3",
    ):
        assert property_text in joined
    assert command[-2:] == ["/bin/true", "--example"]

    with pytest.raises(ValueError):
        runner.build_systemd_worker_command(
            unit_name="bad/unit",
            cpu_id=3,
            worker_command=["/bin/true"],
        )



def test_gc_construction_pytest_is_isolated_and_cannot_write_bytecode() -> None:
    controls = _load_script(
        CONTROLS_PATH,
        "run_gcapeps_n8_r3_controls_pytest_command",
    )
    command = controls.build_gc_construction_pytest_command(
        python_executable=Path(sys.executable),
        fork_checkout=REPO,
    )

    assert command[:7] == [
        str(Path(sys.executable)),
        "-I",
        "-B",
        "-m",
        "pytest",
        "-q",
        "--tb=short",
    ]
    assert command[7:9] == ["-p", "no:cacheprovider"]
    assert tuple(command[-4:]) == controls.GC_CONSTRUCTION_TEST_IDS


def test_gc_coherent_event_term_binding_rejects_coefficient_and_sign_drift() -> None:
    gc_worker = _load_script(
        GC_WORKER_PATH,
        "gcapeps_n8_r3_worker_term_binding",
    )
    physical_terms = (
        "-0.8j*-IXYIZIYZ",
        "-0.48j*+YXYXXIYZ",
        "-0.36j*+YXYXYZYI",
    )
    pulled_back_terms = (
        "-0.8j*+XXYIZZXZ",
        "-0.48j*+YXYZIZXZ",
        "-0.36j*+ZXYZZZXI",
    )

    accepted = gc_worker.validate_coherent_event_term_binding(
        physical_terms,
        pulled_back_terms,
    )

    assert accepted == {
        "physical_terms": list(physical_terms),
        "pulled_back_terms": list(pulled_back_terms),
        "coefficients_and_signed_words_exactly_bound": True,
    }

    coefficient_corruption = list(physical_terms)
    coefficient_corruption[1] = "-0.481j*+YXYXXIYZ"
    with pytest.raises(RuntimeError, match="physical terms drifted"):
        gc_worker.validate_coherent_event_term_binding(
            coefficient_corruption,
            pulled_back_terms,
        )

    first_sign_corruption = list(pulled_back_terms)
    first_sign_corruption[0] = "-0.8j*-XXYIZZXZ"
    with pytest.raises(RuntimeError, match="pulled terms drifted"):
        gc_worker.validate_coherent_event_term_binding(
            physical_terms,
            first_sign_corruption,
        )


def test_fixture_derived_gc_term_binding_control_passes_without_target() -> None:
    emitter = _load_script(
        EMITTER_PATH,
        "emit_gcapeps_n8_r3_fixture_term_binding_control",
    )
    gc_worker = _load_script(
        GC_WORKER_PATH,
        "gcapeps_n8_r3_worker_term_binding_control",
    )
    controls = _load_script(
        CONTROLS_PATH,
        "run_gcapeps_n8_r3_controls_term_binding",
    )

    result = controls.run_gc_coherent_term_binding_control(
        emitter.build_fixture(),
        gc_worker=gc_worker,
    )

    assert result["passed"] is True
    assert result["corruption_rejected"] is True
    assert result["clean_n8_candidate_executed"] is False
    assert result["accepted_binding"][
        "coefficients_and_signed_words_exactly_bound"
    ] is True
    assert result["fixture_derived_physical_terms"][0] == "-0.8j*-IXYIZIYZ"
    assert result["fixture_derived_pulled_terms"][0] == "-0.8j*+XXYIZZXZ"
    assert result["corrupted_first_pulled_term"] == "-0.8j*-XXYIZZXZ"


def test_plain_process_envelope_matches_gc_policy_and_fails_on_each_gap(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    plain = _load_script(
        PLAIN_PATH,
        "plain_quimb_n8_r3_worker_process_envelope",
    )
    gc_worker = _load_script(
        GC_WORKER_PATH,
        "gcapeps_n8_r3_worker_process_envelope",
    )
    assert plain.THREAD_ENVIRONMENT == gc_worker.THREAD_ENVIRONMENT

    def install_valid_envelope(patch: pytest.MonkeyPatch) -> None:
        patch.delenv("PYTHONPATH", raising=False)
        numba_cache = tmp_path / "numba-cache"
        numba_cache.mkdir(mode=0o700, exist_ok=True)
        patch.setenv("NUMBA_CACHE_DIR", str(numba_cache))
        for name in plain.THREAD_ENVIRONMENT:
            patch.setenv(name, "1")
        for name, value in {
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "CUDA_VISIBLE_DEVICES": "",
        }.items():
            patch.setenv(name, value)
        patch.setattr(plain.sys, "platform", "linux")
        patch.setattr(plain.sys, "version_info", (3, 13, 0, "final", 0))
        patch.setattr(plain.sys, "flags", SimpleNamespace(no_user_site=1))
        patch.setattr(plain.sys, "dont_write_bytecode", True)
        patch.setattr(plain.os, "sched_getaffinity", lambda _pid: {17})

    with monkeypatch.context() as patch:
        install_valid_envelope(patch)
        plain_report = plain.verify_process_envelope()
        gc_report = gc_worker.verify_process_envelope()

        assert plain_report["cpu_affinity"] == [17]
        assert plain_report["thread_environment"] == gc_report[
            "thread_environment"
        ]
        assert plain_report["process_environment"] == gc_report[
            "process_environment"
        ]
        assert plain_report["python_no_user_site"] is True
        assert plain_report["python_dont_write_bytecode"] is True
        assert plain_report["pythonpath_absent"] is True
        assert plain_report["numba_cache_directory"] == gc_report[
            "numba_cache_directory"
        ]

    corruptions = (
        (
            "python_3_13",
            lambda patch: patch.setattr(
                plain.sys,
                "version_info",
                (3, 12, 0, "final", 0),
            ),
        ),
        (
            "single_thread",
            lambda patch: patch.setenv("OMP_NUM_THREADS", "2"),
        ),
        (
            "cpu_only",
            lambda patch: patch.setenv("CUDA_VISIBLE_DEVICES", "0"),
        ),
        (
            "single_cpu",
            lambda patch: patch.setattr(
                plain.os,
                "sched_getaffinity",
                lambda _pid: {17, 18},
            ),
        ),
        (
            "no_user_site_flag",
            lambda patch: patch.setattr(
                plain.sys,
                "flags",
                SimpleNamespace(no_user_site=0),
            ),
        ),
        (
            "no_user_site_environment",
            lambda patch: patch.delenv("PYTHONNOUSERSITE"),
        ),
        (
            "no_bytecode_flag",
            lambda patch: patch.setattr(
                plain.sys,
                "dont_write_bytecode",
                False,
            ),
        ),
        (
            "no_bytecode_environment",
            lambda patch: patch.delenv("PYTHONDONTWRITEBYTECODE"),
        ),
        (
            "pythonpath_absent",
            lambda patch: patch.setenv("PYTHONPATH", "/forbidden"),
        ),
        (
            "numba_cache_externalized",
            lambda patch: patch.delenv("NUMBA_CACHE_DIR"),
        ),
    )
    for label, corrupt in corruptions:
        with monkeypatch.context() as patch:
            install_valid_envelope(patch)
            corrupt(patch)
            for worker in (plain, gc_worker):
                with pytest.raises(RuntimeError) as caught:
                    worker.verify_process_envelope()
                assert str(caught.value), label


def test_both_lanes_use_shared_float_rank_cutoff_for_quimb_preparation() -> None:
    plain = _load_script(
        PLAIN_PATH,
        "plain_quimb_n8_r3_worker_preparation_resource_ledger",
    )
    gc_worker = _load_script(
        GC_WORKER_PATH,
        "gcapeps_n8_r3_worker_preparation_resource_ledger",
    )

    # The shared floating cutoff removes numerical null SVD directions. It is
    # not a physical-probability floor and complete c128 vectors remain graded.
    assert plain.PEPS_GATE_SVD_CUTOFF == gc_worker.PEPS_GATE_SVD_CUTOFF == 1e-12
    assert plain.EXPECTED_PREPARATION_BONDS == (2, 2, 2, 2, 2, 2, 1, 2, 1, 1)
    assert plain.EXPECTED_PREPARATION_SITE_ELEMENTS == (4, 16, 8, 4, 4, 16, 8, 4)

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPT = (
    Path(__file__).parents[1]
    / "scripts"
    / "benchmarks"
    / "run_restricted_mps_benchmark.py"
)
SPEC = importlib.util.spec_from_file_location("run_restricted_mps_benchmark", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


def test_atomic_report_is_strict_canonical_json_with_content_hash(
    tmp_path: Path,
    monkeypatch,
) -> None:
    report = {
        "schema": BENCHMARK.REPORT_SCHEMA,
        "mode": "smoke",
        "passed": True,
    }
    report["content_hash_sha256"] = BENCHMARK.canonical_payload_hash(
        report,
        hash_field="content_hash_sha256",
    )

    first = tmp_path / "first" / "report.json"
    second = tmp_path / "second" / "report.json"
    fsynced: list[Path] = []
    real_fsync = BENCHMARK._fsync_directory

    def observe_fsync(path: Path) -> None:
        fsynced.append(Path(path))
        real_fsync(path)

    monkeypatch.setattr(BENCHMARK, "_fsync_directory", observe_fsync)
    first_hash = BENCHMARK.atomic_write_json(first, report)
    second_hash = BENCHMARK.atomic_write_json(second, report)

    assert first.read_bytes() == second.read_bytes()
    assert first_hash == second_hash
    assert json.loads(first.read_text(encoding="utf-8")) == report
    assert list(first.parent.glob("*.tmp")) == []
    assert fsynced == [first.parent, second.parent]


def test_formal_pre_vs_final_block_binds_baseline_bytes_and_canonical_ratios() -> None:
    repo = SCRIPT.parents[2]
    baseline_path = repo / BENCHMARK.DEFAULT_BASELINE_REPORT
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    comparison = BENCHMARK.build_pre_vs_final_comparison(
        baseline_path=baseline_path,
        final_performance_summary=baseline["performance_summary"],
        mode="full",
    )

    assert comparison["valid"] is True
    assert comparison["baseline_git_commit"] == (
        "fa5b0d622b48ccd0cbd34a81b132e11d892d28d2"
    )
    assert comparison["performance_is_verdict_driving"] is False
    assert all(
        row["semantic_payload_hash_match"] is True
        and all(
            metric["final_over_pre"] == pytest.approx(1.0)
            for metric in row["metrics"].values()
        )
        for row in comparison["workloads"]
    )
    assert comparison["content_hash_sha256"] == (
        BENCHMARK.canonical_payload_hash(
            comparison,
            hash_field="content_hash_sha256",
        )
    )


def test_timing_summary_reports_median_and_median_absolute_deviation() -> None:
    summary = BENCHMARK.summarize_samples([1.0, 2.0, 8.0], unit="seconds")

    assert summary == {
        "unit": "seconds",
        "sample_count": 3,
        "samples": [1.0, 2.0, 8.0],
        "median": 2.0,
        "median_absolute_deviation": 1.0,
        "minimum": 1.0,
        "maximum": 8.0,
    }

    with pytest.raises(ValueError, match="nonempty"):
        BENCHMARK.summarize_samples([], unit="seconds")
    with pytest.raises(ValueError, match="finite"):
        BENCHMARK.summarize_samples([float("nan")], unit="seconds")


def test_workload_catalog_is_representative_bounded_and_mode_explicit() -> None:
    smoke = BENCHMARK.workload_catalog("smoke")
    full = BENCHMARK.workload_catalog("full")

    expected_ids = [
        "qt_exact",
        "qt_sampled",
        "qt_capped",
        "mcwf_mixed",
        "mcwf_capped",
    ]
    assert [row["workload_id"] for row in smoke] == expected_ids
    assert [row["workload_id"] for row in full] == expected_ids
    assert all(row["warmup_count"] == 1 for row in smoke)
    assert all(row["repetition_count"] == 3 for row in smoke)
    assert all(row["warmup_count"] == 2 for row in full)
    assert all(row["repetition_count"] == 9 for row in full)

    smoke_by_id = {row["workload_id"]: row for row in smoke}
    full_by_id = {row["workload_id"]: row for row in full}
    assert smoke_by_id["qt_exact"]["execution_config"]["trajectory_count"] is None
    assert smoke_by_id["qt_sampled"]["execution_config"]["trajectory_count"] == 32
    assert full_by_id["qt_sampled"]["execution_config"]["trajectory_count"] == 256
    assert smoke_by_id["qt_capped"]["execution_config"]["max_bond"] == 1
    assert smoke_by_id["mcwf_mixed"]["execution_config"]["local_dims"] == [
        2,
        3,
        4,
        2,
        3,
        4,
    ]
    assert smoke_by_id["mcwf_mixed"]["execution_config"]["max_bond"] is None
    assert smoke_by_id["mcwf_capped"]["execution_config"]["max_bond"] == 1
    assert {
        workload_id: row["expected_public_outcome"]
        for workload_id, row in smoke_by_id.items()
    } == {
        "qt_exact": {
            "passed": True,
            "verdict": "pass",
            "certification_status": "accepted",
            "blocked_reason": None,
            "accepted_for_restricted_execution": True,
        },
        "qt_sampled": {
            "passed": True,
            "verdict": "pass",
            "certification_status": "accepted",
            "blocked_reason": None,
            "accepted_for_restricted_execution": True,
        },
        "qt_capped": {
            "passed": False,
            "verdict": "fail",
            "certification_status": "rejected",
            "blocked_reason": "dense_record_certification_failed",
            "accepted_for_restricted_execution": False,
        },
        "mcwf_mixed": {
            "passed": False,
            "verdict": "fail",
            "certification_status": "unavailable",
            "blocked_reason": (
                "dense_jointL_certification:"
                "skipped_overcap_dense_fallback_forbidden"
            ),
            "accepted_for_restricted_execution": False,
        },
        "mcwf_capped": {
            "passed": True,
            "verdict": "pass",
            "certification_status": "accepted",
            "blocked_reason": None,
            "accepted_for_restricted_execution": True,
        },
    }
    assert {
        row["workload_id"]: row["expected_public_outcome"] for row in full
    } == {
        workload_id: row["expected_public_outcome"]
        for workload_id, row in smoke_by_id.items()
    }

    for row in smoke + full:
        assert row["device"] == "cuda"
        assert row["claim_role"] == "engineering_performance_only"
        assert row["fresh_process_policy"] == "one_exec_worker_per_workload"
        assert "dtype" not in row["execution_config"]
        assert "cutoff" not in row["execution_config"]

    with pytest.raises(ValueError, match="mode"):
        BENCHMARK.workload_catalog("quick")


def _fake_completed_manifest(*, capped: bool) -> dict:
    execution = {
        "trajectory_sampling": {
            "mode": "exact_branch_enumeration",
            "trajectory_count": None,
            "rng_seed": None,
        },
        "measurement_records": [[0, 0], [0, 1], [1, 0], [1, 1]],
        "record_probabilities": [0.5, 0.0, 0.0, 0.5],
        "total_probability": 1.0,
        "total_probability_residual": 0.0,
        "max_observed_bond": 1 if capped else 2,
        "mps_truncation_ledger": {
            "explicit_truncation_requested": capped,
            "actual_split_count": 1 if capped else 0,
            "n_truncating_ops": 1 if capped else 0,
            "discarded_weight_sum": 0.5 if capped else 0.0,
            "worst_cut_discarded_weight": 0.5 if capped else 0.0,
        },
    }
    manifest = {
        "schema": (
            "error_coupling_simulator.frontend.qt_mps_restricted_execution.v6"
        ),
        "source_hash": "a" * 64,
        "execution_status": "completed",
        "passed": False,
        "verdict": "fail",
        "certification_status": "rejected",
        "blocked_reason": "dense_record_certification_failed",
        "restricted_acceptance_policy": {
            "certification_status": "rejected",
            "accepted_for_restricted_execution": False,
            "blocked_reason": "dense_record_certification_failed",
        },
        "qt_mps_backend_executed": True,
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "mps_execution": execution,
    }
    manifest["content_hash"] = BENCHMARK.canonical_payload_hash(
        manifest,
        hash_field="content_hash",
    )
    return manifest


def test_semantic_digest_checks_manifest_hash_probability_law_and_real_cap() -> None:
    workload = {
        row["workload_id"]: row for row in BENCHMARK.workload_catalog("smoke")
    }["qt_capped"]
    manifest = _fake_completed_manifest(capped=True)

    analysis = BENCHMARK.analyze_semantic_manifest(manifest, workload)

    assert analysis["passed"] is True
    assert analysis["violations"] == []
    assert analysis["manifest_content_hash_verified"] is True
    assert len(analysis["semantic_payload_sha256"]) == 64
    assert analysis["summary"]["record_probability_total"] == pytest.approx(1.0)
    assert analysis["summary"]["actual_split_count"] == 1
    assert analysis["summary"]["explicit_truncation_requested"] is True
    assert analysis["summary"]["public_outcome_matches_catalog"] is True

    false_green = dict(manifest)
    false_green["passed"] = True
    false_green["verdict"] = "pass"
    false_green["certification_status"] = "accepted"
    false_green["blocked_reason"] = None
    false_green["restricted_acceptance_policy"] = {
        "certification_status": "accepted",
        "accepted_for_restricted_execution": True,
        "blocked_reason": None,
    }
    false_green["content_hash"] = BENCHMARK.canonical_payload_hash(
        false_green,
        hash_field="content_hash",
    )
    rejected = BENCHMARK.analyze_semantic_manifest(false_green, workload)
    assert rejected["passed"] is False
    assert rejected["summary"]["public_outcome_matches_catalog"] is False
    assert {
        "public_passed_mismatch",
        "public_verdict_mismatch",
        "public_certification_status_mismatch",
        "public_blocked_reason_mismatch",
        "restricted_policy_acceptance_mismatch",
    }.issubset(rejected["violations"])

    corrupt = dict(manifest)
    corrupt["claims_production_scalable_backend"] = True
    corrupt["content_hash"] = BENCHMARK.canonical_payload_hash(
        corrupt,
        hash_field="content_hash",
    )
    rejected = BENCHMARK.analyze_semantic_manifest(corrupt, workload)
    assert rejected["passed"] is False
    assert "production_scalable_claim_must_be_false" in rejected["violations"]

    uncapped_execution = dict(manifest["mps_execution"])
    uncapped_execution["mps_truncation_ledger"] = {
        "explicit_truncation_requested": True,
        "actual_split_count": 0,
        "n_truncating_ops": 0,
        "discarded_weight_sum": 0.0,
        "worst_cut_discarded_weight": 0.0,
    }
    no_split = {**manifest, "mps_execution": uncapped_execution}
    no_split["content_hash"] = BENCHMARK.canonical_payload_hash(
        no_split,
        hash_field="content_hash",
    )
    rejected = BENCHMARK.analyze_semantic_manifest(no_split, workload)
    assert rejected["passed"] is False
    assert "capped_workload_did_not_execute_actual_split" in rejected["violations"]


def test_measurement_loop_separates_warmups_and_records_resource_samples() -> None:
    workload = {
        row["workload_id"]: row for row in BENCHMARK.workload_catalog("smoke")
    }["qt_capped"]
    invocation_count = 0
    synchronization_count = 0
    reset_count = 0
    clock_values = iter([0.0, 1.0, 2.0, 4.0, 5.0, 8.0])
    cuda_values = iter(
        [
            {"peak_allocated_bytes": 1000, "peak_reserved_bytes": 2000},
            {"peak_allocated_bytes": 1100, "peak_reserved_bytes": 2200},
            {"peak_allocated_bytes": 1200, "peak_reserved_bytes": 2400},
        ]
    )
    rss_values = iter([10_000, 11_000, 12_000])

    def invoke() -> dict:
        nonlocal invocation_count
        invocation_count += 1
        return _fake_completed_manifest(capped=True)

    def synchronize() -> None:
        nonlocal synchronization_count
        synchronization_count += 1

    def reset_cuda_peaks() -> None:
        nonlocal reset_count
        reset_count += 1

    measured = BENCHMARK.measure_workload(
        workload,
        invoke=invoke,
        synchronize=synchronize,
        reset_cuda_peaks=reset_cuda_peaks,
        read_cuda_peaks=lambda: next(cuda_values),
        read_process_max_rss_bytes=lambda: next(rss_values),
        clock=lambda: next(clock_values),
    )

    assert invocation_count == 4
    assert reset_count == 3
    assert synchronization_count == 7
    assert measured["warmup_count"] == 1
    assert measured["repetition_count"] == 3
    assert measured["wall_time"]["samples"] == [1.0, 2.0, 3.0]
    assert measured["wall_time"]["median"] == 2.0
    assert measured["wall_time"]["median_absolute_deviation"] == 1.0
    assert measured["cuda_peak_allocated"]["available"] is True
    assert measured["cuda_peak_allocated"]["median"] == 1100.0
    assert measured["cuda_peak_reserved"]["median"] == 2200.0
    assert measured["process_max_rss_after_run"]["median"] == 11_000.0
    assert measured["semantic_consistency"]["unique_payload_hash_count"] == 1
    assert measured["semantic_consistency"]["all_repetitions_passed"] is True
    assert measured["passed"] is True


def test_worker_request_is_exact_catalog_input_and_rejects_tampering() -> None:
    workload = {
        row["workload_id"]: row for row in BENCHMARK.workload_catalog("smoke")
    }["qt_sampled"]
    request = BENCHMARK.build_worker_request(workload)

    assert request["schema"] == BENCHMARK.WORKER_REQUEST_SCHEMA
    assert BENCHMARK.validate_worker_request(request) == workload

    tampered = json.loads(json.dumps(request))
    tampered["workload"]["execution_config"]["trajectory_count"] = 31
    with pytest.raises(ValueError, match="catalog"):
        BENCHMARK.validate_worker_request(tampered)

    wrong_schema = dict(request)
    wrong_schema["schema"] = "old.v0"
    with pytest.raises(ValueError, match="schema"):
        BENCHMARK.validate_worker_request(wrong_schema)


def test_schedule_fixtures_are_public_compiler_inputs_with_frozen_hashes() -> None:
    workloads = {
        row["workload_id"]: row for row in BENCHMARK.workload_catalog("smoke")
    }
    two_site = BENCHMARK.build_schedule_for_workload(workloads["qt_exact"])
    capped = BENCHMARK.build_schedule_for_workload(workloads["mcwf_capped"])
    mixed = BENCHMARK.build_schedule_for_workload(workloads["mcwf_mixed"])

    two_site_manifest = two_site.to_manifest()
    capped_manifest = capped.to_manifest()
    mixed_manifest = mixed.to_manifest()
    assert two_site_manifest == capped_manifest
    assert len(two_site_manifest["source_hash"]) == 64
    assert two_site_manifest["num_qubits"] == 2
    assert two_site_manifest["record_layout_ref"]["measurement_keys"] == [
        "m0",
        "m1",
    ]
    assert len(mixed_manifest["source_hash"]) == 64
    assert mixed_manifest["num_qubits"] == 6
    assert mixed_manifest["record_layout_ref"]["measurement_keys"] == [
        "m0",
        "m1",
        "m2",
        "m3",
        "m4",
        "m5",
    ]
    assert mixed_manifest["static_zz_couplings"] == [[0, 5]]


@pytest.mark.parametrize(
    ("workload_id", "module_name", "entrypoint_name"),
    [
        (
            "qt_exact",
            "error_coupling_simulator.frontend.axis1_qt_mps_execution",
            "axis1_qt_mps_restricted_execution_manifest",
        ),
        (
            "mcwf_mixed",
            "error_coupling_simulator.frontend.axis1_mcwf_mps_execution",
            "axis1_mcwf_mps_state_record_execution_manifest",
        ),
    ],
)
def test_public_invocation_dispatches_exact_catalog_configuration(
    monkeypatch: pytest.MonkeyPatch,
    workload_id: str,
    module_name: str,
    entrypoint_name: str,
) -> None:
    module = __import__(module_name, fromlist=[entrypoint_name])
    workload = {
        row["workload_id"]: row for row in BENCHMARK.workload_catalog("smoke")
    }[workload_id]
    schedule = object()
    observed: dict = {}

    def fake_entrypoint(received_schedule: object, **config: object) -> dict:
        observed["schedule"] = received_schedule
        observed["config"] = config
        return {"fixture": workload_id}

    monkeypatch.setattr(module, entrypoint_name, fake_entrypoint)

    result = BENCHMARK.invoke_public_workload(workload, schedule)

    assert result == {"fixture": workload_id}
    assert observed["schedule"] is schedule
    assert observed["config"] == workload["execution_config"]


def _fake_worker_result(workload: dict, *, pid: int, passed: bool = True) -> dict:
    result = {
        "schema": BENCHMARK.WORKER_RESULT_SCHEMA,
        "workload_id": workload["workload_id"],
        "mode": workload["mode"],
        "worker_process": {
            "pid": pid,
            "parent_pid": 77,
            "started_at_utc": f"2026-07-17T00:00:0{pid % 10}+00:00",
            "fresh_exec_worker": True,
        },
        "exact_input": {
            "workload": workload,
            "schedule_manifest": {"source_hash": "a" * 64},
            "schedule_manifest_sha256": "b" * 64,
        },
        "wall_time": BENCHMARK.summarize_samples(
            [1.0, 1.1, 0.9],
            unit="seconds",
        ),
        "cuda_peak_allocated": {
            "available": True,
            **BENCHMARK.summarize_samples([100, 110, 90], unit="bytes"),
        },
        "cuda_peak_reserved": {
            "available": True,
            **BENCHMARK.summarize_samples([200, 220, 180], unit="bytes"),
        },
        "process_max_rss_after_run": BENCHMARK.summarize_samples(
            [1000, 1100, 1200],
            unit="bytes",
        ),
        "semantic_consistency": {
            "unique_payload_hash_count": 1,
            "all_repetitions_passed": passed,
            "stable_across_repetitions": passed,
        },
        "passed": passed,
    }
    result["content_hash_sha256"] = BENCHMARK.canonical_payload_hash(
        result,
        hash_field="content_hash_sha256",
    )
    return result


def test_report_requires_all_catalog_workers_and_keeps_claim_boundary() -> None:
    workloads = BENCHMARK.workload_catalog("smoke")
    results = [
        _fake_worker_result(workload, pid=100 + index)
        for index, workload in enumerate(workloads)
    ]

    report = BENCHMARK.build_benchmark_report(
        mode="smoke",
        worker_results=results,
        provenance={"git_commit": "deadbeef", "worktree_dirty": True},
        generated_at_utc="2026-07-17T00:01:00+00:00",
        parent_runtime_seconds=12.5,
    )

    assert report["schema"] == BENCHMARK.REPORT_SCHEMA
    assert report["passed"] is True
    assert report["fresh_process_topology"]["worker_count"] == 5
    assert report["fresh_process_topology"]["one_worker_per_workload"] is True
    assert [row["workload_id"] for row in report["workloads"]] == [
        row["workload_id"] for row in workloads
    ]
    assert report["claim_boundary"] == {
        "engineering_performance_instrument": True,
        "production_error_bound": False,
        "record_faithfulness": False,
        "scientific_carrier_claim": False,
        "external_baseline_oracle": False,
    }
    assert report["content_hash_sha256"] == BENCHMARK.canonical_payload_hash(
        report,
        hash_field="content_hash_sha256",
    )

    results[-1] = _fake_worker_result(workloads[-1], pid=199, passed=False)
    failed = BENCHMARK.build_benchmark_report(
        mode="smoke",
        worker_results=results,
        provenance={},
        generated_at_utc="2026-07-17T00:01:00+00:00",
        parent_runtime_seconds=12.5,
    )
    assert failed["passed"] is False


def test_fresh_worker_command_uses_current_python_without_shell_or_pythonpath() -> None:
    command = BENCHMARK.fresh_worker_command(
        request_path=Path("/tmp/request.json"),
        output_path=Path("/tmp/result.json"),
    )

    assert command == [
        sys.executable,
        str(SCRIPT.resolve()),
        "--worker-request",
        "/tmp/request.json",
        "--worker-output",
        "/tmp/result.json",
    ]
    assert "PYTHONPATH" not in " ".join(command)
    assert "-c" not in command


def test_finalized_worker_result_binds_exact_schedule_config_and_provenance() -> None:
    workload = {
        row["workload_id"]: row for row in BENCHMARK.workload_catalog("smoke")
    }["qt_exact"]
    measurement = {
        "schema": BENCHMARK.WORKER_RESULT_SCHEMA,
        "workload_id": "qt_exact",
        "backend": "qt_mps_state_record",
        "mode": "smoke",
        "worker_pid": 123,
        "wall_time": BENCHMARK.summarize_samples([1.0], unit="seconds"),
        "cuda_peak_allocated": {
            "available": True,
            **BENCHMARK.summarize_samples([100], unit="bytes"),
        },
        "cuda_peak_reserved": {
            "available": True,
            **BENCHMARK.summarize_samples([200], unit="bytes"),
        },
        "process_max_rss_after_run": BENCHMARK.summarize_samples(
            [1000],
            unit="bytes",
        ),
        "semantic_consistency": {
            "unique_payload_hashes": ["c" * 64],
            "unique_payload_hash_count": 1,
        },
        "passed": True,
    }
    schedule_manifest = {"source_hash": "a" * 64, "num_qubits": 2}

    result = BENCHMARK.finalize_worker_result(
        workload=workload,
        schedule_manifest=schedule_manifest,
        measurement=measurement,
        runtime_provenance={"torch_version": "fixture"},
        process_started_at_utc="2026-07-17T00:00:00+00:00",
        parent_pid=77,
    )

    assert "worker_pid" not in result
    assert result["worker_process"] == {
        "pid": 123,
        "parent_pid": 77,
        "started_at_utc": "2026-07-17T00:00:00+00:00",
        "fresh_exec_worker": True,
    }
    assert result["exact_input"]["workload"] == workload
    assert result["exact_input"]["schedule_manifest"] == schedule_manifest
    assert result["exact_input"]["schedule_manifest_sha256"] == (
        BENCHMARK.canonical_payload_hash(schedule_manifest)
    )
    assert result["content_hash_sha256"] == BENCHMARK.canonical_payload_hash(
        result,
        hash_field="content_hash_sha256",
    )


def test_parent_provenance_hashes_every_restricted_mps_production_owner() -> None:
    hashes = BENCHMARK._contract_file_hashes(SCRIPT.parents[2])
    required = {
        "src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py",
        "src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py",
        "src/error_coupling_simulator/frontend/axis1_carrier_program.py",
        "src/error_coupling_simulator/frontend/axis1_record_layout.py",
        "src/error_coupling_simulator/frontend/axis1_ideal_controls.py",
        "src/error_coupling_simulator/frontend/axis1_selection.py",
        "src/error_coupling_simulator/frontend/axis1_channel_evidence.py",
        "src/error_coupling_simulator/frontend/axis1_state_evidence.py",
        "src/error_coupling_simulator/frontend/analog_schedule.py",
        "src/error_coupling_simulator/numerics.py",
        "src/error_coupling_simulator/certify/axis1_mps.py",
        "src/error_coupling_simulator/carrier/mps/capped_two_site.py",
        "src/error_coupling_simulator/carrier/mps/controls.py",
        "src/error_coupling_simulator/carrier/mps/probability.py",
        "src/error_coupling_simulator/carrier/mps/state.py",
        "src/error_coupling_simulator/carrier/mps/truncation.py",
        "src/error_coupling_simulator/carrier/mps/uncapped_nonlocal.py",
    }

    assert required.issubset(hashes)
    assert all(len(hashes[path]) == 64 for path in required)


def test_benchmark_parent_and_worker_provenance_bind_lock_and_gpu_identity() -> None:
    repo = SCRIPT.parents[2]
    parent = BENCHMARK.parent_provenance(
        repo,
        argv=["benchmark", "--mode", "smoke"],
        require_clean=False,
    )
    assert parent["status_scope"] == (
        "whole_worktree_including_untracked_not_ignored"
    )
    assert parent["environment_lock_provenance"][
        "selected_runtime_lock_conformance_passed"
    ] is True

    import torch

    worker = BENCHMARK._worker_runtime_provenance(torch, repo_root=repo)
    assert worker["numpy_version"]
    assert worker["quimb_version"] == "1.14.0"
    assert worker["torch_version"]
    assert worker["cuda_device_uuid"].startswith("GPU-")
    assert worker["nvidia_driver_version"]
    assert worker["loaded_cuda_runtime_version_status"] == "not_attested"

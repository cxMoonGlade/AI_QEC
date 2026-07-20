#!/usr/bin/env python3
"""Benchmark the restricted QT/MPS and MCWF/MPS verification routes.

This is an engineering performance instrument.  It does not establish a
production error bound, Record faithfulness, or a scientific carrier claim.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence


REPORT_SCHEMA = (
    "error_coupling_simulator.benchmarks.restricted_mps_performance.v1"
)
WORKER_REQUEST_SCHEMA = (
    "error_coupling_simulator.benchmarks.restricted_mps_worker_request.v1"
)
WORKER_RESULT_SCHEMA = (
    "error_coupling_simulator.benchmarks.restricted_mps_worker_result.v1"
)
DEFAULT_BASELINE_REPORT = Path(
    "outputs/simulator_validation/benchmarks/restricted_mps/final_fa5b0d6.json"
)
WORKLOAD_IDS = (
    "qt_exact",
    "qt_sampled",
    "qt_capped",
    "mcwf_mixed",
    "mcwf_capped",
)
_EXPECTED_PUBLIC_OUTCOME_BY_WORKLOAD = {
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


def workload_catalog(mode: str) -> list[dict[str, Any]]:
    """Return the frozen representative workload/configuration catalog."""

    if mode not in {"smoke", "full"}:
        raise ValueError("mode must be 'smoke' or 'full'")
    warmups = 1 if mode == "smoke" else 2
    repetitions = 3 if mode == "smoke" else 9
    qt_sampled_trajectories = 32 if mode == "smoke" else 256
    mcwf_mixed_trajectories = 4 if mode == "smoke" else 32
    mcwf_capped_trajectories = 8 if mode == "smoke" else 64

    common = {
        "mode": mode,
        "device": "cuda",
        "warmup_count": warmups,
        "repetition_count": repetitions,
        "fresh_process_policy": "one_exec_worker_per_workload",
        "claim_role": "engineering_performance_only",
    }
    qt_common = {
        "device": "cuda",
        "max_branches": 64,
        "max_record_materialization_outcomes": 64,
        "microstep_count": 1,
        "finite_step_order": "first_order",
        "dense_oracle_certification": True,
    }
    mcwf_common = {
        "device": "cuda",
        "microstep_count": 1,
        "finite_step_order": "first_order",
        "leaked_readout_b": 1.0,
        "mass_residual_budget": 0.1,
    }
    return [
        {
            **common,
            "workload_id": "qt_exact",
            "expected_public_outcome": dict(
                _EXPECTED_PUBLIC_OUTCOME_BY_WORKLOAD["qt_exact"]
            ),
            "backend": "qt_mps_state_record",
            "schedule_fixture": "two_qubit_entangling_z_record_v1",
            "execution_config": {
                **qt_common,
                "max_bond": None,
                "trajectory_count": None,
                "rng_seed": None,
                "worst_cut_discarded_weight_gate": None,
                "total_discarded_weight_gate": None,
            },
        },
        {
            **common,
            "workload_id": "qt_sampled",
            "expected_public_outcome": dict(
                _EXPECTED_PUBLIC_OUTCOME_BY_WORKLOAD["qt_sampled"]
            ),
            "backend": "qt_mps_state_record",
            "schedule_fixture": "two_qubit_entangling_z_record_v1",
            "execution_config": {
                **qt_common,
                "max_bond": None,
                "trajectory_count": qt_sampled_trajectories,
                "rng_seed": 1701,
                "worst_cut_discarded_weight_gate": None,
                "total_discarded_weight_gate": None,
            },
        },
        {
            **common,
            "workload_id": "qt_capped",
            "expected_public_outcome": dict(
                _EXPECTED_PUBLIC_OUTCOME_BY_WORKLOAD["qt_capped"]
            ),
            "backend": "qt_mps_state_record",
            "schedule_fixture": "two_qubit_entangling_z_record_v1",
            "execution_config": {
                **qt_common,
                "max_bond": 1,
                "trajectory_count": None,
                "rng_seed": None,
                "worst_cut_discarded_weight_gate": 1.0,
                "total_discarded_weight_gate": 1.0,
            },
        },
        {
            **common,
            "workload_id": "mcwf_mixed",
            "expected_public_outcome": dict(
                _EXPECTED_PUBLIC_OUTCOME_BY_WORKLOAD["mcwf_mixed"]
            ),
            "backend": "mcwf_mps_state_record",
            "schedule_fixture": "six_site_mixed_dim_static_zz_record_v1",
            "execution_config": {
                **mcwf_common,
                "local_dims": [2, 3, 4, 2, 3, 4],
                "initial_levels": [0, 0, 0, 0, 0, 0],
                "max_bond": None,
                "trajectory_count": mcwf_mixed_trajectories,
                "rng_seed": 1801,
                "worst_cut_discarded_weight_gate": None,
                "total_discarded_weight_gate": None,
            },
        },
        {
            **common,
            "workload_id": "mcwf_capped",
            "expected_public_outcome": dict(
                _EXPECTED_PUBLIC_OUTCOME_BY_WORKLOAD["mcwf_capped"]
            ),
            "backend": "mcwf_mps_state_record",
            "schedule_fixture": "two_qubit_entangling_z_record_v1",
            "execution_config": {
                **mcwf_common,
                "local_dims": [2, 2],
                "initial_levels": [0, 0],
                "max_bond": 1,
                "trajectory_count": mcwf_capped_trajectories,
                "rng_seed": 1901,
                "worst_cut_discarded_weight_gate": 1.0,
                "total_discarded_weight_gate": 1.0,
            },
        },
    ]


def build_worker_request(workload: Mapping[str, Any]) -> dict[str, Any]:
    """Freeze one catalog row into a strict neutral worker request."""

    copied = json.loads(
        json.dumps(workload, allow_nan=False, sort_keys=True)
    )
    request = {"schema": WORKER_REQUEST_SCHEMA, "workload": copied}
    validate_worker_request(request)
    return request


def validate_worker_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Require a worker request to match one current catalog row exactly."""

    if request.get("schema") != WORKER_REQUEST_SCHEMA:
        raise ValueError("worker request schema is not current")
    if set(request) != {"schema", "workload"}:
        raise ValueError("worker request must contain only schema and workload")
    workload = request.get("workload")
    if not isinstance(workload, Mapping):
        raise TypeError("worker request workload must be a mapping")
    mode = workload.get("mode")
    if not isinstance(mode, str):
        raise TypeError("worker request workload mode must be a string")
    workload_id = workload.get("workload_id")
    matching = [
        row for row in workload_catalog(mode) if row["workload_id"] == workload_id
    ]
    if len(matching) != 1 or dict(workload) != matching[0]:
        raise ValueError("worker request workload must match the frozen catalog")
    return matching[0]


def build_schedule_for_workload(workload: Mapping[str, Any]) -> Any:
    """Build one compiler-sealed schedule through the public frontend API."""

    from error_coupling_simulator.frontend import (
        Axis1LocalLindbladContextSpec,
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )

    fixture = workload.get("schedule_fixture")
    if fixture == "two_qubit_entangling_z_record_v1":
        builder = CircuitBuilder(num_qubits=2)
        builder.declare_axis1_local_lindblad_context(
            Axis1LocalLindbladContextSpec(
                gamma_phi_per_ns=0.0,
                gamma_1_per_ns=0.0,
                gamma_readout_phi_per_ns=0.0,
            )
        )
        builder.h((0, 1))
        builder.tick()
        builder.cz((0, 1))
        builder.tick()
        builder.measure(
            (0, 1),
            key=("m0", "m1"),
            duration_ns=1.0e-6,
        )
        return circuit_ir_to_substep_schedule(builder.build())
    if fixture == "six_site_mixed_dim_static_zz_record_v1":
        builder = CircuitBuilder(num_qubits=6)
        builder.declare_static_zz_couplings(((0, 5),))
        builder.declare_axis1_local_lindblad_context(
            Axis1LocalLindbladContextSpec(
                zeta_rad_per_ns=1.0e-3,
                gamma_phi_per_ns=0.0,
                gamma_1_per_ns=0.0,
                gamma_readout_phi_per_ns=0.0,
            )
        )
        builder.h((0, 5))
        builder.tick()
        builder.idle(tuple(range(6)), duration_ns=5.0)
        builder.tick()
        builder.measure(
            tuple(range(6)),
            key=tuple(f"m{index}" for index in range(6)),
            duration_ns=1.0e-6,
        )
        return circuit_ir_to_substep_schedule(builder.build())
    raise ValueError(f"unknown benchmark schedule fixture {fixture!r}")


def invoke_public_workload(
    workload: Mapping[str, Any],
    schedule: Any,
) -> Mapping[str, Any]:
    """Invoke the current public direct executor with the exact catalog config."""

    config = workload.get("execution_config")
    if not isinstance(config, Mapping):
        raise TypeError("workload execution_config must be a mapping")
    backend = workload.get("backend")
    if backend == "qt_mps_state_record":
        from error_coupling_simulator.frontend import axis1_qt_mps_execution

        return axis1_qt_mps_execution.axis1_qt_mps_restricted_execution_manifest(
            schedule,
            **dict(config),
        )
    if backend == "mcwf_mps_state_record":
        from error_coupling_simulator.frontend import axis1_mcwf_mps_execution

        return (
            axis1_mcwf_mps_execution
            .axis1_mcwf_mps_state_record_execution_manifest(
                schedule,
                **dict(config),
            )
        )
    raise ValueError(f"unknown restricted MPS benchmark backend {backend!r}")


def fresh_worker_command(
    *,
    request_path: Path,
    output_path: Path,
) -> list[str]:
    """Return the argv for one shell-free fresh Python worker exec."""

    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker-request",
        str(Path(request_path)),
        "--worker-output",
        str(Path(output_path)),
    ]


def _validated_worker_result(
    result: Mapping[str, Any],
    *,
    workload: Mapping[str, Any],
) -> dict[str, Any]:
    if result.get("schema") != WORKER_RESULT_SCHEMA:
        raise ValueError("worker result schema is not current")
    if result.get("workload_id") != workload["workload_id"]:
        raise ValueError("worker result workload_id does not match catalog")
    if result.get("mode") != workload["mode"]:
        raise ValueError("worker result mode does not match catalog")
    exact_input = result.get("exact_input")
    if (
        not isinstance(exact_input, Mapping)
        or exact_input.get("workload") != workload
    ):
        raise ValueError("worker result exact input does not match catalog")
    expected_hash = canonical_payload_hash(
        result,
        hash_field="content_hash_sha256",
    )
    if result.get("content_hash_sha256") != expected_hash:
        raise ValueError("worker result content hash mismatch")
    process = result.get("worker_process")
    if (
        not isinstance(process, Mapping)
        or process.get("fresh_exec_worker") is not True
    ):
        raise ValueError("worker result lacks fresh exec process evidence")
    return dict(result)


def build_pre_vs_final_comparison(
    *,
    baseline_path: Path,
    final_performance_summary: Sequence[Mapping[str, Any]],
    mode: str,
) -> dict[str, Any]:
    """Bind one historical benchmark artifact to the current measured summary."""

    resolved = Path(baseline_path).resolve()
    baseline = _read_json_object(resolved)
    if (
        baseline.get("schema") != REPORT_SCHEMA
        or baseline.get("mode") != mode
        or baseline.get("passed") is not True
        or baseline.get("content_hash_sha256")
        != canonical_payload_hash(baseline, hash_field="content_hash_sha256")
    ):
        raise ValueError("benchmark baseline report is not a valid same-mode pass")
    baseline_rows = baseline.get("performance_summary")
    if not isinstance(baseline_rows, list):
        raise ValueError("benchmark baseline performance summary is unavailable")
    before = {row.get("workload_id"): row for row in baseline_rows}
    after = {row.get("workload_id"): row for row in final_performance_summary}
    if (
        sorted(before) != sorted(WORKLOAD_IDS)
        or sorted(after) != sorted(WORKLOAD_IDS)
    ):
        raise ValueError("benchmark pre/final workload identities drifted")

    metrics = (
        "wall_time_median_seconds",
        "cuda_peak_allocated_median_bytes",
        "cuda_peak_reserved_median_bytes",
        "process_max_rss_median_bytes",
    )
    comparisons: list[dict[str, Any]] = []
    for workload_id in WORKLOAD_IDS:
        pre = before[workload_id]
        final = after[workload_id]
        metric_rows: dict[str, Any] = {}
        for metric in metrics:
            pre_value = float(pre[metric])
            final_value = float(final[metric])
            if (
                not math.isfinite(pre_value)
                or not math.isfinite(final_value)
                or pre_value < 0.0
                or final_value < 0.0
            ):
                raise ValueError("benchmark pre/final metric is invalid")
            metric_rows[metric] = {
                "pre": pre_value,
                "final": final_value,
                "final_over_pre": (
                    None if pre_value == 0.0 else final_value / pre_value
                ),
                "final_minus_pre": final_value - pre_value,
            }
        comparisons.append(
            {
                "workload_id": workload_id,
                "metrics": metric_rows,
                "pre_semantic_payload_sha256": pre[
                    "semantic_payload_sha256"
                ],
                "final_semantic_payload_sha256": final[
                    "semantic_payload_sha256"
                ],
                "semantic_payload_hash_match": (
                    pre["semantic_payload_sha256"]
                    == final["semantic_payload_sha256"]
                ),
                "pre_passed": pre.get("passed") is True,
                "final_passed": final.get("passed") is True,
            }
        )
    baseline_provenance = baseline.get("provenance")
    baseline_commit = (
        baseline_provenance.get("git_commit")
        if isinstance(baseline_provenance, Mapping)
        else None
    )
    block: dict[str, Any] = {
        "schema": (
            "error_coupling_simulator.benchmarks."
            "restricted_mps_pre_vs_final.v1"
        ),
        "baseline_path": str(resolved.relative_to(Path(__file__).resolve().parents[2])),
        "baseline_file_sha256": _sha256_file(resolved),
        "baseline_content_hash_sha256": baseline["content_hash_sha256"],
        "baseline_git_commit": baseline_commit,
        "mode": mode,
        "workloads": comparisons,
        "performance_is_verdict_driving": False,
        "semantic_payload_hash_match_is_diagnostic_across_source_checkpoints": True,
        "valid": bool(all(row["pre_passed"] and row["final_passed"] for row in comparisons)),
    }
    block["content_hash_sha256"] = canonical_payload_hash(
        block,
        hash_field="content_hash_sha256",
    )
    return block


def build_benchmark_report(
    *,
    mode: str,
    worker_results: Sequence[Mapping[str, Any]],
    provenance: Mapping[str, Any],
    generated_at_utc: str,
    parent_runtime_seconds: float,
    pre_vs_final_comparison: Mapping[str, Any] | None = None,
    require_pre_vs_final: bool = False,
) -> dict[str, Any]:
    """Assemble the complete five-workload, claim-bounded benchmark report."""

    catalog = workload_catalog(mode)
    by_id: dict[str, Mapping[str, Any]] = {}
    for result in worker_results:
        workload_id = result.get("workload_id")
        if not isinstance(workload_id, str) or workload_id in by_id:
            raise ValueError("worker results must have unique string workload_id values")
        by_id[workload_id] = result
    expected_ids = [workload["workload_id"] for workload in catalog]
    if sorted(by_id) != sorted(expected_ids):
        raise ValueError("worker results must cover the complete workload catalog")
    ordered_results = [
        _validated_worker_result(by_id[workload["workload_id"]], workload=workload)
        for workload in catalog
    ]
    runtime = float(parent_runtime_seconds)
    if not math.isfinite(runtime) or runtime < 0.0:
        raise ValueError("parent runtime must be finite and nonnegative")
    process_evidence = [
        result["worker_process"] for result in ordered_results
    ]
    topology_passed = all(
        process.get("fresh_exec_worker") is True
        for process in process_evidence
    )
    all_workloads_passed = all(
        result.get("passed") is True for result in ordered_results
    )
    performance_summary = [
        {
            "workload_id": result["workload_id"],
            "wall_time_median_seconds": result["wall_time"]["median"],
            "wall_time_mad_seconds": result["wall_time"][
                "median_absolute_deviation"
            ],
            "cuda_peak_allocated_median_bytes": result[
                "cuda_peak_allocated"
            ]["median"],
            "cuda_peak_reserved_median_bytes": result[
                "cuda_peak_reserved"
            ]["median"],
            "process_max_rss_median_bytes": result[
                "process_max_rss_after_run"
            ]["median"],
            "semantic_payload_sha256": result["semantic_consistency"].get(
                "unique_payload_hashes",
                [],
            ),
            "passed": result["passed"],
        }
        for result in ordered_results
    ]
    if require_pre_vs_final and pre_vs_final_comparison is None:
        raise ValueError("formal pre-vs-final benchmark comparison is required")
    comparison = (
        {
            "status": "not_requested",
            "performance_is_verdict_driving": False,
        }
        if pre_vs_final_comparison is None
        else dict(pre_vs_final_comparison)
    )
    comparison_passed = bool(
        not require_pre_vs_final or comparison.get("valid") is True
    )
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "generated_at_utc": str(generated_at_utc),
        "mode": mode,
        "parent_runtime_seconds": runtime,
        "workload_catalog_ids": expected_ids,
        "fresh_process_topology": {
            "policy": "one_shell_free_python_exec_worker_per_workload",
            "parent_imports_torch_or_cuda": False,
            "worker_count": len(ordered_results),
            "one_worker_per_workload": topology_passed,
            "worker_processes": process_evidence,
            "pythonpath_modified_by_harness": False,
        },
        "performance_summary": performance_summary,
        "pre_vs_final_comparison": comparison,
        "workloads": ordered_results,
        "all_workloads_passed": all_workloads_passed,
        "claim_boundary": {
            "engineering_performance_instrument": True,
            "production_error_bound": False,
            "record_faithfulness": False,
            "scientific_carrier_claim": False,
            "external_baseline_oracle": False,
        },
        "provenance": dict(provenance),
        "passed": bool(
            topology_passed and all_workloads_passed and comparison_passed
        ),
    }
    report["content_hash_sha256"] = canonical_payload_hash(
        report,
        hash_field="content_hash_sha256",
    )
    return report


def canonical_payload_hash(
    payload: Mapping[str, Any],
    *,
    hash_field: str | None = None,
) -> str:
    """Hash one strict canonical JSON object, optionally excluding one field."""

    value = dict(payload)
    if hash_field is not None:
        value.pop(hash_field, None)
    encoded = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Atomically write deterministic strict JSON and return its byte hash."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(encoded).hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def summarize_samples(values: Sequence[float | int], *, unit: str) -> dict[str, Any]:
    """Return raw samples plus robust median/MAD summary."""

    samples = [float(value) for value in values]
    if not samples:
        raise ValueError("samples must be nonempty")
    if any(not math.isfinite(value) for value in samples):
        raise ValueError("samples must be finite")
    median = float(statistics.median(samples))
    mad = float(statistics.median(abs(value - median) for value in samples))
    return {
        "unit": str(unit),
        "sample_count": len(samples),
        "samples": samples,
        "median": median,
        "median_absolute_deviation": mad,
        "minimum": min(samples),
        "maximum": max(samples),
    }


def analyze_semantic_manifest(
    manifest: Mapping[str, Any],
    workload: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one measured public manifest and return its semantic digest."""

    workload_id = str(workload.get("workload_id"))
    backend = str(workload.get("backend"))
    config = workload.get("execution_config")
    if not isinstance(config, Mapping):
        raise TypeError("workload execution_config must be a mapping")
    execution = manifest.get("mps_execution")
    violations: list[str] = []
    if not isinstance(execution, Mapping):
        execution = {}
        violations.append("mps_execution_missing")

    expected_hash = canonical_payload_hash(manifest, hash_field="content_hash")
    observed_hash = manifest.get("content_hash")
    content_hash_verified = (
        isinstance(observed_hash, str)
        and len(observed_hash) == 64
        and observed_hash == expected_hash
    )
    if not content_hash_verified:
        violations.append("manifest_content_hash_mismatch")
    if manifest.get("execution_status") != "completed":
        violations.append("execution_status_not_completed")
    expected_public_outcome = workload.get("expected_public_outcome")
    if (
        not isinstance(expected_public_outcome, Mapping)
        or set(expected_public_outcome)
        != {
            "passed",
            "verdict",
            "certification_status",
            "blocked_reason",
            "accepted_for_restricted_execution",
        }
    ):
        raise ValueError("workload expected_public_outcome is malformed")
    public_outcome_checks = {
        "public_passed_mismatch": (
            manifest.get("passed") == expected_public_outcome["passed"]
        ),
        "public_verdict_mismatch": (
            manifest.get("verdict") == expected_public_outcome["verdict"]
        ),
        "public_certification_status_mismatch": (
            manifest.get("certification_status")
            == expected_public_outcome["certification_status"]
        ),
        "public_blocked_reason_mismatch": (
            manifest.get("blocked_reason")
            == expected_public_outcome["blocked_reason"]
        ),
    }
    for violation, matched in public_outcome_checks.items():
        if not matched:
            violations.append(violation)
    restricted_policy = manifest.get("restricted_acceptance_policy")
    if not isinstance(restricted_policy, Mapping):
        restricted_policy = {}
        violations.append("restricted_policy_missing")
    restricted_policy_checks = {
        "restricted_policy_certification_status_mismatch": (
            restricted_policy.get("certification_status")
            == expected_public_outcome["certification_status"]
        ),
        "restricted_policy_acceptance_mismatch": (
            restricted_policy.get("accepted_for_restricted_execution")
            == expected_public_outcome["accepted_for_restricted_execution"]
        ),
        "restricted_policy_blocked_reason_mismatch": (
            restricted_policy.get("blocked_reason")
            == expected_public_outcome["blocked_reason"]
        ),
    }
    for violation, matched in restricted_policy_checks.items():
        if not matched:
            violations.append(violation)
    executed_field = (
        "qt_mps_backend_executed"
        if backend == "qt_mps_state_record"
        else "mcwf_mps_backend_executed"
    )
    if manifest.get(executed_field) is not True:
        violations.append("restricted_mps_backend_not_executed")
    if manifest.get("claims_production_scalable_backend") is not False:
        violations.append("production_scalable_claim_must_be_false")
    if manifest.get("claims_exact_joint_lindblad_generator") is not False:
        violations.append("exact_joint_generator_claim_must_be_false")
    if manifest.get("claims_dense_channel_evidence") is not False:
        violations.append("dense_channel_evidence_claim_must_be_false")

    records = execution.get("measurement_records")
    probabilities = execution.get("record_probabilities")
    probability_total: float | None = None
    if (
        not isinstance(records, Sequence)
        or isinstance(records, (str, bytes, bytearray))
        or not isinstance(probabilities, Sequence)
        or isinstance(probabilities, (str, bytes, bytearray))
        or not records
        or len(records) != len(probabilities)
    ):
        violations.append("record_probability_payload_invalid")
    else:
        normalized_probabilities: list[float] = []
        for value in probabilities:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                violations.append("record_probability_payload_invalid")
                break
            normalized = float(value)
            if not math.isfinite(normalized) or normalized < 0.0:
                violations.append("record_probability_payload_invalid")
                break
            normalized_probabilities.append(normalized)
        else:
            probability_total = float(math.fsum(normalized_probabilities))
            if abs(probability_total - 1.0) > 1.0e-8:
                violations.append("record_probability_total_not_one")

    sampling = execution.get("trajectory_sampling")
    if not isinstance(sampling, Mapping):
        sampling = {}
        violations.append("trajectory_sampling_missing")
    expected_trajectory_count = config.get("trajectory_count")
    if sampling.get("trajectory_count") != expected_trajectory_count:
        violations.append("trajectory_count_mismatch")
    expected_seed = config.get("rng_seed")
    if sampling.get("rng_seed") != expected_seed:
        violations.append("rng_seed_mismatch")
    expected_mode = {
        "qt_exact": "exact_branch_enumeration",
        "qt_sampled": "sampled_product_channel_trajectories",
        "qt_capped": "exact_branch_enumeration",
        "mcwf_mixed": "sampled_fixed_microstep_mcwf_trajectories",
        "mcwf_capped": "sampled_fixed_microstep_mcwf_trajectories",
    }.get(workload_id)
    if sampling.get("mode") != expected_mode:
        violations.append("trajectory_sampling_mode_mismatch")

    counts = execution.get("record_counts")
    if expected_trajectory_count is not None:
        if (
            not isinstance(counts, Sequence)
            or isinstance(counts, (str, bytes, bytearray))
            or any(
                isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
                for count in counts
            )
            or sum(counts) != expected_trajectory_count
        ):
            violations.append("sampled_record_counts_invalid")

    ledger = execution.get("mps_truncation_ledger")
    if not isinstance(ledger, Mapping):
        ledger = {}
        violations.append("mps_truncation_ledger_missing")
    explicit_truncation = ledger.get("explicit_truncation_requested")
    actual_split_count = ledger.get("actual_split_count")
    capped = config.get("max_bond") is not None
    if capped:
        if explicit_truncation is not True:
            violations.append("capped_workload_missing_explicit_truncation")
        if (
            isinstance(actual_split_count, bool)
            or not isinstance(actual_split_count, int)
            or actual_split_count <= 0
        ):
            violations.append("capped_workload_did_not_execute_actual_split")
    elif explicit_truncation is not False:
        violations.append("uncapped_workload_reported_explicit_truncation")

    if workload_id == "mcwf_mixed":
        local_space = manifest.get("local_hilbert_space")
        observed_dims = (
            local_space.get("local_dims")
            if isinstance(local_space, Mapping)
            else None
        )
        if observed_dims != config.get("local_dims"):
            violations.append("mixed_local_dims_mismatch")

    semantic_payload = {
        "workload_id": workload_id,
        "backend": backend,
        "manifest_schema": manifest.get("schema"),
        "source_hash": manifest.get("source_hash"),
        "execution_status": manifest.get("execution_status"),
        "backend_executed": manifest.get(executed_field),
        "claims_production_scalable_backend": manifest.get(
            "claims_production_scalable_backend"
        ),
        "claims_exact_joint_lindblad_generator": manifest.get(
            "claims_exact_joint_lindblad_generator"
        ),
        "claims_dense_channel_evidence": manifest.get(
            "claims_dense_channel_evidence"
        ),
        "mps_execution": execution,
    }
    public_outcome_matches_catalog = all(public_outcome_checks.values()) and all(
        restricted_policy_checks.values()
    )
    return {
        "semantic_payload_sha256": canonical_payload_hash(semantic_payload),
        "manifest_content_hash": observed_hash,
        "manifest_content_hash_verified": content_hash_verified,
        "summary": {
            "public_outcome_matches_catalog": public_outcome_matches_catalog,
            "public_passed": manifest.get("passed"),
            "public_verdict": manifest.get("verdict"),
            "public_certification_status": manifest.get("certification_status"),
            "public_blocked_reason": manifest.get("blocked_reason"),
            "expected_public_outcome": dict(expected_public_outcome),
            "record_count": len(records) if isinstance(records, Sequence) else None,
            "record_probability_total": probability_total,
            "trajectory_sampling_mode": sampling.get("mode"),
            "trajectory_count": sampling.get("trajectory_count"),
            "rng_seed": sampling.get("rng_seed"),
            "max_observed_bond": ledger.get("max_observed_bond"),
            "explicit_truncation_requested": explicit_truncation,
            "actual_split_count": actual_split_count,
            "n_truncating_ops": ledger.get("n_truncating_ops"),
            "discarded_weight_sum": ledger.get("discarded_weight_sum"),
            "worst_cut_discarded_weight": ledger.get(
                "worst_cut_discarded_weight"
            ),
        },
        "violations": sorted(set(violations)),
        "passed": not violations,
    }


def _summarize_optional_samples(
    values: Sequence[int | float | None],
    *,
    unit: str,
) -> dict[str, Any]:
    present = [value for value in values if value is not None]
    if not present:
        return {
            "available": False,
            "unit": unit,
            "sample_count": 0,
            "samples": [],
            "median": None,
            "median_absolute_deviation": None,
            "minimum": None,
            "maximum": None,
        }
    summary = summarize_samples(present, unit=unit)
    return {"available": len(present) == len(values), **summary}


def measure_workload(
    workload: Mapping[str, Any],
    *,
    invoke: Callable[[], Mapping[str, Any]],
    synchronize: Callable[[], None],
    reset_cuda_peaks: Callable[[], None],
    read_cuda_peaks: Callable[[], Mapping[str, int] | None],
    read_process_max_rss_bytes: Callable[[], int],
    clock: Callable[[], float],
) -> dict[str, Any]:
    """Warm and measure one already-built workload in one worker process."""

    warmup_count = int(workload["warmup_count"])
    repetition_count = int(workload["repetition_count"])
    if warmup_count < 0 or repetition_count <= 0:
        raise ValueError("warmup_count must be nonnegative and repetitions positive")

    warmup_analyses: list[dict[str, Any]] = []
    for _ in range(warmup_count):
        manifest = invoke()
        synchronize()
        warmup_analyses.append(analyze_semantic_manifest(manifest, workload))

    samples: list[dict[str, Any]] = []
    for repetition_index in range(repetition_count):
        synchronize()
        reset_cuda_peaks()
        started = float(clock())
        manifest = invoke()
        synchronize()
        elapsed = float(clock()) - started
        if not math.isfinite(elapsed) or elapsed < 0.0:
            raise ValueError("measured wall time must be finite and nonnegative")
        cuda_peaks = read_cuda_peaks()
        rss_bytes = read_process_max_rss_bytes()
        if isinstance(rss_bytes, bool) or not isinstance(rss_bytes, int):
            raise TypeError("process max RSS must be an integer byte count")
        if rss_bytes < 0:
            raise ValueError("process max RSS must be nonnegative")
        semantic = analyze_semantic_manifest(manifest, workload)
        allocated: int | None = None
        reserved: int | None = None
        if cuda_peaks is not None:
            allocated = int(cuda_peaks["peak_allocated_bytes"])
            reserved = int(cuda_peaks["peak_reserved_bytes"])
            if allocated < 0 or reserved < 0:
                raise ValueError("CUDA peak byte counts must be nonnegative")
        samples.append(
            {
                "repetition_index": repetition_index,
                "wall_seconds": elapsed,
                "cuda_peak_allocated_bytes": allocated,
                "cuda_peak_reserved_bytes": reserved,
                "process_max_rss_bytes_after_run": rss_bytes,
                "semantic": semantic,
            }
        )

    semantic_hashes = [
        str(sample["semantic"]["semantic_payload_sha256"])
        for sample in samples
    ]
    unique_hashes = sorted(set(semantic_hashes))
    all_measured_semantics_passed = all(
        bool(sample["semantic"]["passed"]) for sample in samples
    )
    all_warmup_semantics_passed = all(
        bool(analysis["passed"]) for analysis in warmup_analyses
    )
    semantic_consistency = {
        "hash_kind": "canonical_selected_semantic_payload_sha256",
        "payload_hashes": semantic_hashes,
        "unique_payload_hashes": unique_hashes,
        "unique_payload_hash_count": len(unique_hashes),
        "all_warmups_passed": all_warmup_semantics_passed,
        "all_repetitions_passed": all_measured_semantics_passed,
        "stable_across_repetitions": len(unique_hashes) == 1,
    }
    passed = bool(
        all_warmup_semantics_passed
        and all_measured_semantics_passed
        and semantic_consistency["stable_across_repetitions"]
    )
    return {
        "schema": WORKER_RESULT_SCHEMA,
        "workload_id": workload["workload_id"],
        "backend": workload["backend"],
        "mode": workload["mode"],
        "worker_pid": os.getpid(),
        "warmup_count": warmup_count,
        "repetition_count": repetition_count,
        "timing_scope": (
            "public_execution_manifest_call_plus_required_cuda_synchronization"
        ),
        "warmup_semantic_analyses": warmup_analyses,
        "samples": samples,
        "wall_time": summarize_samples(
            [sample["wall_seconds"] for sample in samples],
            unit="seconds",
        ),
        "cuda_peak_allocated": _summarize_optional_samples(
            [sample["cuda_peak_allocated_bytes"] for sample in samples],
            unit="bytes",
        ),
        "cuda_peak_reserved": _summarize_optional_samples(
            [sample["cuda_peak_reserved_bytes"] for sample in samples],
            unit="bytes",
        ),
        "process_max_rss_after_run": summarize_samples(
            [sample["process_max_rss_bytes_after_run"] for sample in samples],
            unit="bytes",
        ),
        "resource_measurement_notes": {
            "cuda_peak_allocated": (
                "torch.cuda peak allocated bytes after resetting peak statistics "
                "immediately before each timed invocation"
            ),
            "cuda_peak_reserved": (
                "torch.cuda peak reserved bytes after resetting peak statistics "
                "immediately before each timed invocation"
            ),
            "process_max_rss_after_run": (
                "process high-water RSS after each invocation; cumulative within "
                "the fresh workload worker, not an invocation-local delta"
            ),
        },
        "semantic_consistency": semantic_consistency,
        "passed": passed,
    }


def finalize_worker_result(
    *,
    workload: Mapping[str, Any],
    schedule_manifest: Mapping[str, Any],
    measurement: Mapping[str, Any],
    runtime_provenance: Mapping[str, Any],
    process_started_at_utc: str,
    parent_pid: int,
) -> dict[str, Any]:
    """Bind one measured worker result to exact input and runtime provenance."""

    result = dict(measurement)
    pid = result.pop("worker_pid", None)
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ValueError("measurement worker_pid must be a positive integer")
    if (
        isinstance(parent_pid, bool)
        or not isinstance(parent_pid, int)
        or parent_pid <= 0
    ):
        raise ValueError("parent_pid must be a positive integer")
    frozen_workload = json.loads(
        json.dumps(workload, allow_nan=False, sort_keys=True)
    )
    frozen_schedule = json.loads(
        json.dumps(schedule_manifest, allow_nan=False, sort_keys=True)
    )
    result.update(
        {
            "worker_process": {
                "pid": pid,
                "parent_pid": parent_pid,
                "started_at_utc": str(process_started_at_utc),
                "fresh_exec_worker": True,
            },
            "exact_input": {
                "workload": frozen_workload,
                "schedule_manifest": frozen_schedule,
                "schedule_manifest_sha256": canonical_payload_hash(
                    frozen_schedule
                ),
            },
            "runtime_provenance": dict(runtime_provenance),
        }
    )
    result["content_hash_sha256"] = canonical_payload_hash(
        result,
        hash_field="content_hash_sha256",
    )
    return result


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"nonfinite JSON constant {value!r} is forbidden")

    payload = json.loads(
        Path(path).read_text(encoding="utf-8"),
        parse_constant=reject_constant,
    )
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return payload


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _git_output(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _contract_file_hashes(repo_root: Path) -> dict[str, str]:
    relative_paths = [
        "docs/SIMULATOR.md",
        "src/error_coupling_simulator/carrier/mps/README.md",
        "src/error_coupling_simulator/frontend/README.md",
        "src/error_coupling_simulator/frontend/__init__.py",
        "src/error_coupling_simulator/frontend/axis1_carrier_execution.py",
        "src/error_coupling_simulator/frontend/axis1_carrier_program.py",
        "src/error_coupling_simulator/frontend/axis1_channel_evidence.py",
        "src/error_coupling_simulator/frontend/axis1_ideal_controls.py",
        "src/error_coupling_simulator/frontend/axis1_record_layout.py",
        "src/error_coupling_simulator/frontend/axis1_selection.py",
        "src/error_coupling_simulator/frontend/axis1_state_evidence.py",
        "src/error_coupling_simulator/frontend/analog_schedule.py",
        "src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py",
        "src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py",
        "src/error_coupling_simulator/certify/axis1_mps.py",
        "src/error_coupling_simulator/numerics.py",
        "scripts/benchmarks/run_restricted_mps_benchmark.py",
    ]
    carrier_source_root = repo_root / "src/error_coupling_simulator/carrier/mps"
    relative_paths.extend(
        str(path.relative_to(repo_root))
        for path in sorted(carrier_source_root.glob("*.py"))
    )
    return {
        relative: _sha256_file(repo_root / relative)
        for relative in dict.fromkeys(relative_paths)
    }


def _selected_runtime_lock_provenance(repo_root: Path) -> dict[str, Any]:
    core_lock = repo_root / "core-environment-cu130.lock"
    uv_lock = repo_root / "uv.lock"
    pinned: dict[str, str] = {}
    for raw_line in core_lock.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, version = line.split("==", 1)
        pinned[name.lower()] = version
    observed = {
        name: _distribution_version(name)
        for name in ("numpy", "quimb", "torch")
    }
    selected = {
        name: {
            "locked": pinned.get(name),
            "observed": version,
            "matches": pinned.get(name) == version,
        }
        for name, version in observed.items()
    }
    passed = all(record["matches"] for record in selected.values())
    if not passed:
        raise RuntimeError("benchmark selected runtime drifted from core lock")
    return {
        "lock_sha256": {
            "core-environment-cu130.lock": _sha256_file(core_lock),
            "uv.lock": _sha256_file(uv_lock),
        },
        "selected_distributions": selected,
        "selected_runtime_lock_conformance_checked": True,
        "selected_runtime_lock_conformance_passed": True,
        "claims_full_environment_lock_conformance": False,
        "claims_reproducible_environment": False,
        "limitation": (
            "selected NumPy/Quimb/Torch direct pins are checked; full transitive "
            "environment reconstruction is not performed by this benchmark"
        ),
    }


def parent_provenance(
    repo_root: Path,
    *,
    argv: Sequence[str],
    require_clean: bool = False,
) -> dict[str, Any]:
    """Collect stdlib-only parent provenance without importing Torch/CUDA."""

    status = _git_output(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if require_clean and status:
        raise RuntimeError("restricted MPS benchmark requires a clean Git worktree")
    return {
        "repo_root": str(repo_root.resolve()),
        "git_commit": _git_output(repo_root, "rev-parse", "HEAD"),
        "worktree_dirty": bool(status),
        "whole_worktree_clean_including_untracked": not bool(status),
        "status_scope": "whole_worktree_including_untracked_not_ignored",
        "worktree_status_sha256": hashlib.sha256(
            status.encode("utf-8")
        ).hexdigest(),
        "contract_file_sha256": _contract_file_hashes(repo_root),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "argv": list(argv),
        "installed_distribution_versions_without_import": {
            "error-coupling-simulator": _distribution_version(
                "error-coupling-simulator"
            ),
            "numpy": _distribution_version("numpy"),
            "torch": _distribution_version("torch"),
            "quimb": _distribution_version("quimb"),
        },
        "environment_lock_provenance": _selected_runtime_lock_provenance(
            repo_root
        ),
        "declared_environment_controls": {
            name: os.environ.get(name)
            for name in (
                "ECS_DISABLE_NATIVE_KERNELS",
                "ECS_FORCE_UNFACTORIZED_AXIS1",
                "ECS_D3_DATA_ROOT",
                "ECS_D3_MASK",
            )
        },
        "parent_imports_torch_or_cuda": False,
        "pythonpath_modified_by_harness": False,
        "inherited_pythonpath_present": "PYTHONPATH" in os.environ,
    }


def _worker_runtime_provenance(torch: Any, *, repo_root: Path) -> dict[str, Any]:
    import numpy
    import quimb

    device_index = int(torch.cuda.current_device())
    properties = torch.cuda.get_device_properties(device_index)
    driver_process = subprocess.run(
        [
            "nvidia-smi",
            f"--id={device_index}",
            "--query-gpu=driver_version",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30.0,
    )
    driver_version = driver_process.stdout.strip()
    if not driver_version:
        raise RuntimeError("benchmark NVIDIA driver identity is unavailable")
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "torch_version": str(torch.__version__),
        "numpy_version": str(numpy.__version__),
        "torch_cuda_build_version": (
            None if torch.version.cuda is None else str(torch.version.cuda)
        ),
        "quimb_version": str(quimb.__version__),
        "error_coupling_simulator_distribution_version": _distribution_version(
            "error-coupling-simulator"
        ),
        "cuda_available_in_worker": bool(torch.cuda.is_available()),
        "cuda_device_index": device_index,
        "cuda_device_name": str(properties.name),
        "cuda_device_uuid": f"GPU-{properties.uuid}",
        "cuda_device_capability": list(torch.cuda.get_device_capability(device_index)),
        "cuda_device_total_memory_bytes": int(properties.total_memory),
        "nvidia_driver_version": driver_version,
        "loaded_cuda_runtime_version_status": "not_attested",
        "route_array_dtype": "torch.complex128",
        "contract_file_sha256": _contract_file_hashes(repo_root),
        "declared_environment_controls": {
            name: os.environ.get(name)
            for name in (
                "ECS_DISABLE_NATIVE_KERNELS",
                "ECS_FORCE_UNFACTORIZED_AXIS1",
                "ECS_D3_DATA_ROOT",
                "ECS_D3_MASK",
            )
        },
        "pythonpath_modified_by_harness": False,
        "inherited_pythonpath_present": "PYTHONPATH" in os.environ,
    }


def _process_max_rss_bytes() -> int:
    import resource

    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return raw if sys.platform == "darwin" else raw * 1024


def execute_worker_request(
    request: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Execute one validated catalog workload in this fresh worker process."""

    process_started_at_utc = _utc_now()
    parent_pid = os.getppid()
    workload = validate_worker_request(request)
    schedule = build_schedule_for_workload(workload)
    schedule_manifest = schedule.to_manifest()

    import torch

    if not torch.cuda.is_available():
        raise RuntimeError(
            "restricted MPS benchmark requires CUDA in each fresh worker"
        )
    device = str(workload["device"])

    def synchronize() -> None:
        torch.cuda.synchronize(device)

    def reset_cuda_peaks() -> None:
        torch.cuda.reset_peak_memory_stats(device)

    def read_cuda_peaks() -> dict[str, int]:
        return {
            "peak_allocated_bytes": int(
                torch.cuda.max_memory_allocated(device)
            ),
            "peak_reserved_bytes": int(
                torch.cuda.max_memory_reserved(device)
            ),
        }

    measurement = measure_workload(
        workload,
        invoke=lambda: invoke_public_workload(workload, schedule),
        synchronize=synchronize,
        reset_cuda_peaks=reset_cuda_peaks,
        read_cuda_peaks=read_cuda_peaks,
        read_process_max_rss_bytes=_process_max_rss_bytes,
        clock=time.perf_counter,
    )
    return finalize_worker_result(
        workload=workload,
        schedule_manifest=schedule_manifest,
        measurement=measurement,
        runtime_provenance=_worker_runtime_provenance(
            torch,
            repo_root=repo_root,
        ),
        process_started_at_utc=process_started_at_utc,
        parent_pid=parent_pid,
    )


def run_fresh_worker(
    workload: Mapping[str, Any],
    *,
    repo_root: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Run one workload in a shell-free exec child and validate its artifact."""

    timeout = float(timeout_seconds)
    if not math.isfinite(timeout) or timeout <= 0.0:
        raise ValueError("timeout_seconds must be finite and positive")
    request = build_worker_request(workload)
    with tempfile.TemporaryDirectory(
        prefix=f"restricted-mps-{workload['workload_id']}-"
    ) as temporary:
        temporary_root = Path(temporary)
        request_path = temporary_root / "request.json"
        result_path = temporary_root / "result.json"
        atomic_write_json(request_path, request)
        command = fresh_worker_command(
            request_path=request_path,
            output_path=result_path,
        )
        try:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"benchmark worker {workload['workload_id']} timed out "
                f"after {timeout} seconds"
            ) from exc
        if completed.returncode != 0:
            raise RuntimeError(
                f"benchmark worker {workload['workload_id']} failed with "
                f"returncode {completed.returncode}; "
                f"stdout={completed.stdout[-4000:]!r}; "
                f"stderr={completed.stderr[-4000:]!r}"
            )
        if not result_path.is_file():
            raise RuntimeError(
                f"benchmark worker {workload['workload_id']} emitted no result"
            )
        result = _read_json_object(result_path)
    return _validated_worker_result(result, workload=workload)


def run_benchmark(
    *,
    mode: str,
    output: Path,
    timeout_seconds: float,
    argv: Sequence[str],
    baseline_report: Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Run the complete catalog and atomically write its aggregate report."""

    repo_root = Path(__file__).resolve().parents[2]
    provenance = parent_provenance(
        repo_root,
        argv=argv,
        require_clean=True,
    )
    started = time.perf_counter()
    results = [
        run_fresh_worker(
            workload,
            repo_root=repo_root,
            timeout_seconds=timeout_seconds,
        )
        for workload in workload_catalog(mode)
    ]
    runtime = time.perf_counter() - started
    final_provenance = parent_provenance(
        repo_root,
        argv=argv,
        require_clean=True,
    )
    if final_provenance != provenance:
        raise RuntimeError("benchmark source/environment provenance drifted during run")
    provenance["post_run_revalidation"] = {
        "identical_to_pre_run": True,
        "canonical_sha256": canonical_payload_hash(final_provenance),
    }
    preliminary = build_benchmark_report(
        mode=mode,
        worker_results=results,
        provenance=provenance,
        generated_at_utc=_utc_now(),
        parent_runtime_seconds=runtime,
    )
    comparison = None
    if baseline_report is not None:
        comparison = build_pre_vs_final_comparison(
            baseline_path=baseline_report,
            final_performance_summary=preliminary["performance_summary"],
            mode=mode,
        )
    report = build_benchmark_report(
        mode=mode,
        worker_results=results,
        provenance=provenance,
        generated_at_utc=preliminary["generated_at_utc"],
        parent_runtime_seconds=runtime,
        pre_vs_final_comparison=comparison,
        require_pre_vs_final=baseline_report is not None,
    )
    exact_byte_sha256 = atomic_write_json(Path(output), report)
    return report, exact_byte_sha256


def _positive_finite(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0.0:
        raise argparse.ArgumentTypeError("value must be finite and positive")
    return parsed


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "outputs/simulator_validation/benchmarks/"
            "restricted_mps/report.json"
        ),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=_positive_finite,
        default=900.0,
        help="per-workload fresh-worker timeout",
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=None,
        help="same-mode hash-valid pre checkpoint for formal pre-vs-final ratios",
    )
    parser.add_argument("--worker-request", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    if (args.worker_request is None) != (args.worker_output is None):
        raise ValueError("--worker-request and --worker-output must be paired")
    if args.worker_request is not None:
        request = _read_json_object(args.worker_request)
        result = execute_worker_request(request, repo_root=repo_root)
        exact_byte_sha256 = atomic_write_json(args.worker_output, result)
        print(
            f"restricted MPS benchmark worker {result['workload_id']}: "
            f"{'PASS' if result['passed'] else 'FAIL'} "
            f"exact_byte_sha256={exact_byte_sha256}"
        )
        return 0 if result["passed"] else 1

    effective_argv = list(sys.argv if argv is None else [str(__file__), *argv])
    report, exact_byte_sha256 = run_benchmark(
        mode=args.mode,
        output=args.output,
        timeout_seconds=args.timeout_seconds,
        argv=effective_argv,
        baseline_report=args.baseline_report,
    )
    print(
        "restricted MPS benchmark: "
        f"{'PASS' if report['passed'] else 'FAIL'}"
    )
    print(
        f"wrote {args.output.resolve()} "
        f"exact_byte_sha256={exact_byte_sha256}"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

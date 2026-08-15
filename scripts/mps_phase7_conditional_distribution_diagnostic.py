#!/usr/bin/env python3
"""Bounded Phase-7 QT/MPS conditional-distribution diagnostic.

This diagnostic compares the restricted QT/MPS exact branch table with seeded
sampled trajectories on one small, hand-checkable schedule.  It is an
implementation diagnostic only: it is neither a production error bound nor a
Record-faithfulness certificate, and the exact and sampled branches are not
independent scientific oracles.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from numbers import Real
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence


REPORT_SCHEMA = (
    "error_coupling_simulator.diagnostics."
    "mps_phase7_conditional_distribution_report.v1"
)
DEFAULT_OUTPUT = Path(
    "outputs/simulator_validation/diagnostics/"
    "mps_phase7_conditional_distribution/report.json"
)
DEFAULT_TRAJECTORY_COUNT = 2048
DEFAULT_SEEDS = (7, 19, 73)
REPO_BINDINGS = (
    Path("scripts/mps_phase7_conditional_distribution_diagnostic.py"),
    Path("src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py"),
    Path("src/error_coupling_simulator/frontend/axis1_record_layout.py"),
    Path("src/error_coupling_simulator/frontend/analog_schedule.py"),
    Path("pyproject.toml"),
    Path("core-environment-cu130.lock"),
    Path("uv.lock"),
)
EXPECTED_QT_EXECUTION_SCHEMA = (
    "error_coupling_simulator.frontend.qt_mps_restricted_execution.v6"
)
RECORD_SUPPORT_ALIGNMENT_POLICY = "union_of_record_values_missing_probability_zero"
_PROBABILITY_MASS_TOLERANCE = 1.0e-8
CONFIDENCE_LEVEL = 0.999
ALPHA = 0.001
STRICT_TV_GATE = 0.2
GROSS_TV_GATE_CEILING = 0.45
EXACT_HAND_DISTRIBUTION_TV_GATE = 1.0e-12
EXPECTED_EXACT_SUPPORT_POLICY = "full_binary_record_support"
EXPECTED_SAMPLED_SUPPORT_POLICY = "observed_empirical_outcomes_only"
HAND_EXPECTED_RECORD_DISTRIBUTION = {
    (0, 0, 0, 0): 0.5,
    (1, 1, 1, 1): 0.5,
}
CLAIM_BOUNDARY = {
    "status": "BOUNDED_IMPLEMENTATION_DIAGNOSTIC_ONLY",
    "production_error_bound": False,
    "record_faithfulness": False,
    "independent_scientific_oracle": False,
    "trajectory_bit_identity_required": False,
    "exact_joint_lindblad_generator_claim": False,
    "notes": (
        "The exact branch table and sampled trajectories are two modes of the "
        "same restricted QT/MPS implementation. This bounded fixture checks "
        "distributional consistency only and does not certify a production "
        "Record law or provide a multi-operation error bound."
    ),
}


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_payload_hash(payload: Mapping[str, Any], *, hash_field: str) -> str:
    unhashed = {key: value for key, value in payload.items() if key != hash_field}
    return hashlib.sha256(canonical_json_bytes(unhashed)).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically replace one JSON artifact in its destination directory."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_output(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def execution_provenance(*, schedule_source_hash: str) -> dict[str, Any]:
    """Bind one run to the current script, v6 owner, locks, and CUDA runtime."""

    script_path = Path(__file__).resolve()
    repo_root = Path(_git_output(script_path.parent, "rev-parse", "--show-toplevel"))
    missing = [
        path.as_posix() for path in REPO_BINDINGS if not (repo_root / path).is_file()
    ]
    if missing:
        raise RuntimeError(f"missing diagnostic binding files: {missing}")
    binding_status = _git_output(
        repo_root,
        "status",
        "--short",
        "--untracked-files=all",
        "--",
        *(path.as_posix() for path in REPO_BINDINGS),
    )

    import torch

    cuda_device = torch.cuda.current_device()
    return {
        "git_commit": _git_output(repo_root, "rev-parse", "HEAD"),
        "binding_files_git_status": binding_status.splitlines(),
        "binding_file_sha256": {
            path.as_posix(): _sha256_file(repo_root / path) for path in REPO_BINDINGS
        },
        "schedule_source_hash": str(schedule_source_hash),
        "qt_execution_schema": EXPECTED_QT_EXECUTION_SCHEMA,
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "quimb", "torch")
        },
        "cuda": {
            "torch_cuda_available": bool(torch.cuda.is_available()),
            "torch_cuda_version": torch.version.cuda,
            "device_index_in_process": int(cuda_device),
            "device_name": torch.cuda.get_device_name(cuda_device),
            "ECS_GPU_SLOT": os.environ.get("ECS_GPU_SLOT"),
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
        },
        "command": list(sys.argv),
    }


def build_hand_checkable_schedule() -> tuple[Any, dict[str, Any]]:
    """Build a Bell pair followed by two correlated two-target Z boundaries."""

    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )
    from error_coupling_simulator.frontend.axis1_record_layout import (
        axis1_record_layout_from_schedule,
    )

    local_context = {
        "gamma_phi_per_ns": 0.0,
        "gamma_1_per_ns": 0.0,
        "gamma_readout_phi_per_ns": 0.0,
        "zeta_rad_per_ns": 0.0,
        "epistemic_class": "c",
    }
    builder = CircuitBuilder(
        num_qubits=2,
        metadata={
            "fixture": "mps_phase7_bell_repeated_z_records",
            "encoded_distance_certified": False,
        },
    )
    builder.declare_axis1_local_lindblad_context(local_context)
    builder.h(0)
    builder.tick()
    builder.cx((0, 1))
    builder.tick()
    builder.measure(
        (0, 1),
        key=("round0_q0", "round0_q1"),
        duration_ns=1.0e-6,
    )
    builder.tick()
    builder.measure(
        (0, 1),
        key=("round1_q0", "round1_q1"),
        duration_ns=1.0e-6,
    )
    schedule = circuit_ir_to_substep_schedule(builder.build())
    layout = axis1_record_layout_from_schedule(schedule)
    fixture = {
        "schema": (
            "error_coupling_simulator.diagnostics."
            "mps_phase7_conditional_distribution_fixture.v1"
        ),
        "fixture_id": "bell_pair_two_correlated_z_measurement_boundaries",
        "source_hash": schedule.source_hash,
        "source_kind": schedule.source_kind,
        "schedule_schema": schedule.schema_version,
        "num_qubits": 2,
        "operation_sequence": [
            "H(0)",
            "CX(0,1)",
            "MZ(0,1)->(round0_q0,round0_q1)",
            "MZ(0,1)->(round1_q0,round1_q1)",
        ],
        "local_lindblad_context": local_context,
        "zero_rate_context_role": (
            "isolate conditional Record sampling and keep exact branch count bounded"
        ),
        "measurement_boundary_count": len(layout.boundaries),
        "measurement_width": layout.measurement_width,
        "measurement_boundaries": [
            {
                "substep_id": boundary.substep_id,
                "keys": list(boundary.keys),
                "targets": list(boundary.targets),
                "bases": list(boundary.bases),
                "reset_after": list(boundary.reset_after),
                "global_slice": list(boundary.global_slice),
            }
            for boundary in layout.boundaries
        ],
        "correlation_structure": (
            "within-boundary Bell correlation and across-boundary repeat correlation"
        ),
        "expected_positive_distribution": _distribution_rows(
            HAND_EXPECTED_RECORD_DISTRIBUTION
        ),
        "exact_branch_role": (
            "bounded same-implementation exact branch table, not an independent oracle"
        ),
    }
    return schedule, fixture


def record_probability_map(
    records: Sequence[Sequence[int]],
    probabilities: Sequence[float],
    *,
    name: str,
) -> dict[tuple[int, ...], float]:
    """Validate and normalize one finite Record distribution."""

    if len(records) != len(probabilities) or not records:
        raise ValueError(f"{name} records/probabilities must be nonempty and aligned")
    out: dict[tuple[int, ...], float] = {}
    width: int | None = None
    for index, (record, probability) in enumerate(zip(records, probabilities, strict=True)):
        normalized = tuple(record)
        if width is None:
            width = len(normalized)
        elif len(normalized) != width:
            raise ValueError(f"{name} Record widths must match")
        if any(isinstance(bit, bool) or bit not in (0, 1) for bit in normalized):
            raise ValueError(f"{name} record {index} must contain integer binary values")
        if normalized in out:
            raise ValueError(f"{name} contains duplicate Record {normalized!r}")
        if isinstance(probability, bool) or not isinstance(probability, Real):
            raise TypeError(f"{name} probability {index} must be a real number")
        value = float(probability)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} probability {index} must be finite and nonnegative")
        out[normalized] = value
    total = math.fsum(out.values())
    if not math.isfinite(total) or abs(total - 1.0) > _PROBABILITY_MASS_TOLERANCE:
        raise ValueError(f"{name} probabilities must sum to one")
    return {record: probability / total for record, probability in out.items()}


def total_variation_distance(
    left: Mapping[tuple[int, ...], float],
    right: Mapping[tuple[int, ...], float],
) -> tuple[float, tuple[tuple[int, ...], ...]]:
    """Return standard ``TV = 1/2 L1`` after union-support alignment."""

    union = tuple(sorted(set(left) | set(right)))
    value = 0.5 * math.fsum(
        abs(float(left.get(record, 0.0)) - float(right.get(record, 0.0)))
        for record in union
    )
    return float(value), union


def frozen_sampling_gate(
    *,
    trajectory_count: int,
    union_record_support_size: int,
) -> dict[str, Any]:
    """Return the frozen per-bin Hoeffding-to-TV diagnostic gate."""

    if isinstance(trajectory_count, bool) or not isinstance(trajectory_count, int):
        raise TypeError("trajectory_count must be an integer, not bool")
    if trajectory_count <= 0:
        raise ValueError("trajectory_count must be positive")
    if (
        isinstance(union_record_support_size, bool)
        or not isinstance(union_record_support_size, int)
    ):
        raise TypeError("union_record_support_size must be an integer, not bool")
    if union_record_support_size <= 0:
        raise ValueError("union_record_support_size must be positive")
    per_bin = math.sqrt(
        math.log(2.0 / ALPHA) / (2.0 * float(trajectory_count))
    )
    tv_halfwidth = (
        float(union_record_support_size) / 2.0 * per_bin
    )
    gross_gate = min(
        STRICT_TV_GATE + tv_halfwidth,
        GROSS_TV_GATE_CEILING,
    )
    return {
        "confidence_level": CONFIDENCE_LEVEL,
        "alpha": ALPHA,
        "per_bin_hoeffding_halfwidth": float(per_bin),
        "per_bin_hoeffding_formula": "sqrt(log(2 / alpha) / (2 * N))",
        "tv_halfwidth": float(tv_halfwidth),
        "tv_halfwidth_formula": "K / 2 * per_bin_hoeffding_halfwidth",
        "strict_tv_gate": STRICT_TV_GATE,
        "confidence_adjusted_gross_gate": float(gross_gate),
        "gross_gate_formula": "min(0.2 + tv_halfwidth, 0.45)",
        "gross_gate_ceiling": GROSS_TV_GATE_CEILING,
        "confidence_interpretation": (
            "per-bin Hoeffding padding propagated to TV by the triangle "
            "inequality; not an exact global TV confidence interval"
        ),
    }


def deliberate_corruption_falsifier(
    exact: Mapping[tuple[int, ...], float],
) -> dict[str, Any]:
    """Move every positive mass bin by flipping its final Record bit."""

    if not exact:
        raise ValueError("exact distribution must be nonempty")
    corrupted: dict[tuple[int, ...], float] = {}
    for record, probability in exact.items():
        if not record:
            raise ValueError("corruption falsifier requires nonempty Records")
        value = float(probability)
        if value <= 0.0:
            continue
        changed = record[:-1] + (1 - record[-1],)
        corrupted[changed] = corrupted.get(changed, 0.0) + value
    tv, union = total_variation_distance(exact, corrupted)
    rejected = tv > GROSS_TV_GATE_CEILING
    passed = tv >= 0.5 and rejected
    return {
        "corruption": "flip_final_bit_of_every_positive_record",
        "corrupted_distribution": [
            {"record": list(record), "probability": float(corrupted[record])}
            for record in sorted(corrupted)
        ],
        "record_support_alignment_policy": RECORD_SUPPORT_ALIGNMENT_POLICY,
        "union_record_support": [list(record) for record in union],
        "metric": "total_variation_distance",
        "metric_convention": "TV = 1/2 * sum_r |p_exact(r) - p_corrupt(r)|",
        "total_variation_distance": float(tv),
        "required_minimum_total_variation": 0.5,
        "rejection_gate": GROSS_TV_GATE_CEILING,
        "rejected_by_gross_gate_ceiling": bool(rejected),
        "passed": bool(passed),
        "falsifier_role": "deliberate_analysis_corruption_not_production_input",
    }


def compare_record_distributions(
    exact: Mapping[tuple[int, ...], float],
    sampled: Mapping[tuple[int, ...], float],
    *,
    trajectory_count: int,
    rng_seed: int,
) -> dict[str, Any]:
    """Compare one sampled Record law with the bounded exact branch table."""

    tv, union = total_variation_distance(exact, sampled)
    gate = frozen_sampling_gate(
        trajectory_count=trajectory_count,
        union_record_support_size=len(union),
    )
    return {
        "rng_seed": int(rng_seed),
        "trajectory_count": int(trajectory_count),
        "record_support_alignment_policy": RECORD_SUPPORT_ALIGNMENT_POLICY,
        "union_record_support": [list(record) for record in union],
        "union_record_support_size": len(union),
        "exact_emitted_record_count": len(exact),
        "sampled_emitted_record_count": len(sampled),
        "metric": "total_variation_distance",
        "metric_convention": "TV = 1/2 * sum_r |p_exact(r) - p_sampled(r)|",
        "total_variation_distance": tv,
        **gate,
        "strict_passed": bool(tv <= STRICT_TV_GATE),
        "confidence_adjusted_passed": bool(
            tv <= gate["confidence_adjusted_gross_gate"]
        ),
        "acceptance_basis": "confidence_adjusted_gross_gate",
    }


def _distribution_rows(
    distribution: Mapping[tuple[int, ...], float],
    *,
    positive_only: bool = False,
) -> list[dict[str, Any]]:
    return [
        {"record": list(record), "probability": float(distribution[record])}
        for record in sorted(distribution)
        if not positive_only or float(distribution[record]) > 0.0
    ]


def analyze_distribution_payloads(
    exact_execution: Mapping[str, Any],
    sampled_executions: Sequence[Mapping[str, Any]],
    *,
    trajectory_count: int,
) -> dict[str, Any]:
    """Analyze exact and multi-seed sampled v6 execution payloads."""

    exact_sampling = exact_execution.get("trajectory_sampling")
    if not isinstance(exact_sampling, Mapping):
        raise ValueError("exact execution has no trajectory_sampling object")
    if exact_sampling.get("mode") != "exact_branch_enumeration":
        raise ValueError("exact execution must use exact_branch_enumeration")
    if exact_sampling.get("trajectory_count") is not None:
        raise ValueError("exact execution trajectory_count must be None")
    if exact_sampling.get("record_support_policy") != EXPECTED_EXACT_SUPPORT_POLICY:
        raise ValueError("exact execution must emit full binary Record support")
    exact = record_probability_map(
        exact_execution.get("measurement_records", ()),
        exact_execution.get("record_probabilities", ()),
        name="exact execution",
    )
    exact_widths = {len(record) for record in exact}
    if exact_widths != {4}:
        raise ValueError("diagnostic exact execution must emit four-bit Records")
    if len(exact) != 16:
        raise ValueError("diagnostic exact execution must emit all 16 Records")

    if len(sampled_executions) < 2:
        raise ValueError("diagnostic requires at least two explicit-seed sampled runs")
    comparisons: list[dict[str, Any]] = []
    observed_seeds: set[int] = set()
    for run_index, sampled_execution in enumerate(sampled_executions):
        sampling = sampled_execution.get("trajectory_sampling")
        if not isinstance(sampling, Mapping):
            raise ValueError(f"sampled execution {run_index} has no trajectory_sampling object")
        if sampling.get("mode") != "sampled_product_channel_trajectories":
            raise ValueError(f"sampled execution {run_index} has the wrong mode")
        if sampling.get("trajectory_count") != trajectory_count:
            raise ValueError(f"sampled execution {run_index} trajectory_count mismatch")
        if sampling.get("rng_seed_was_explicit") is not True:
            raise ValueError(f"sampled execution {run_index} must use an explicit seed")
        if sampling.get("record_support_policy") != EXPECTED_SAMPLED_SUPPORT_POLICY:
            raise ValueError(f"sampled execution {run_index} must emit observed support")
        seed = sampling.get("rng_seed")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError(f"sampled execution {run_index} has an invalid seed")
        if seed in observed_seeds:
            raise ValueError("sampled executions must use distinct explicit seeds")
        observed_seeds.add(seed)
        sampled_records = sampled_execution.get("measurement_records", ())
        sampled_probabilities = sampled_execution.get("record_probabilities", ())
        sampled = record_probability_map(
            sampled_records,
            sampled_probabilities,
            name=f"sampled execution {run_index}",
        )
        if {len(record) for record in sampled} != {4}:
            raise ValueError(f"sampled execution {run_index} Record width mismatch")
        counts = sampled_execution.get("record_counts")
        if (
            not isinstance(counts, Sequence)
            or isinstance(counts, (str, bytes))
            or len(counts) != len(sampled_records)
            or len(counts) != len(sampled_probabilities)
            or any(
                isinstance(count, bool)
                or not isinstance(count, int)
                or count <= 0
                for count in counts
            )
            or sum(counts) != trajectory_count
        ):
            raise ValueError(f"sampled execution {run_index} has invalid record_counts")
        for bin_index, (count, probability) in enumerate(
            zip(counts, sampled_probabilities, strict=True)
        ):
            expected_probability = float(count) / float(trajectory_count)
            if abs(float(probability) - expected_probability) > _PROBABILITY_MASS_TOLERANCE:
                raise ValueError(
                    f"sampled execution {run_index} probability {bin_index} must "
                    "equal count / trajectory_count"
                )
        comparison = compare_record_distributions(
            exact,
            sampled,
            trajectory_count=trajectory_count,
            rng_seed=seed,
        )
        comparison["sampled_distribution"] = _distribution_rows(sampled)
        comparisons.append(comparison)

    hand_tv, hand_union = total_variation_distance(
        exact,
        HAND_EXPECTED_RECORD_DISTRIBUTION,
    )
    exact_hand_check = {
        "expected_state_and_record_law": (
            "Bell state (|00> + |11>) / sqrt(2), measured twice without "
            "reset, gives 0000 and 1111 with probability 1/2 each"
        ),
        "expected_distribution": _distribution_rows(
            HAND_EXPECTED_RECORD_DISTRIBUTION
        ),
        "record_support_alignment_policy": RECORD_SUPPORT_ALIGNMENT_POLICY,
        "union_record_support_size": len(hand_union),
        "metric": "total_variation_distance",
        "metric_convention": "TV = 1/2 * sum_r |p_exact(r) - p_hand(r)|",
        "total_variation_distance": float(hand_tv),
        "gate": EXACT_HAND_DISTRIBUTION_TV_GATE,
        "passed": bool(hand_tv <= EXACT_HAND_DISTRIBUTION_TV_GATE),
    }
    corruption = deliberate_corruption_falsifier(exact)
    all_strict = all(row["strict_passed"] for row in comparisons)
    all_adjusted = all(row["confidence_adjusted_passed"] for row in comparisons)
    passed = bool(exact_hand_check["passed"] and all_adjusted and corruption["passed"])
    return {
        "schema": (
            "error_coupling_simulator.diagnostics."
            "mps_phase7_conditional_distribution_analysis.v1"
        ),
        "comparison_object": "restricted_qt_mps_Record_distributions",
        "exact_positive_distribution": _distribution_rows(exact, positive_only=True),
        "exact_emitted_record_count": len(exact),
        "sampled_run_count": len(comparisons),
        "trajectory_count_per_seed": int(trajectory_count),
        "exact_hand_distribution_check": exact_hand_check,
        "seed_comparisons": comparisons,
        "all_seed_strict_passed": bool(all_strict),
        "all_seed_confidence_adjusted_passed": bool(all_adjusted),
        "strict_result_role": "reported_without_sampling_allowance_not_acceptance_basis",
        "confidence_adjusted_result_role": "frozen_diagnostic_acceptance_basis",
        "acceptance_basis": (
            "every_seed_tv_at_or_below_confidence_adjusted_gross_gate"
        ),
        "deliberate_corruption_falsifier": corruption,
        "passed": passed,
    }


def _execution_manifest_summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if manifest.get("schema") != EXPECTED_QT_EXECUTION_SCHEMA:
        raise ValueError("diagnostic requires the QT/MPS restricted execution v6 schema")
    if manifest.get("execution_status") != "completed":
        raise ValueError("diagnostic branch execution did not complete")
    if manifest.get("qt_mps_backend_executed") is not True:
        raise ValueError("diagnostic branch did not execute the QT/MPS backend")
    for field in (
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_production_scalable_backend",
    ):
        if manifest.get(field) is not False:
            raise ValueError(f"diagnostic branch must report {field}=False")
    execution = manifest.get("mps_execution")
    if not isinstance(execution, Mapping):
        raise ValueError("diagnostic branch has no mps_execution payload")
    sampling = execution.get("trajectory_sampling")
    if not isinstance(sampling, Mapping):
        raise ValueError("diagnostic branch has no trajectory_sampling payload")
    return {
        "schema": manifest["schema"],
        "content_hash": manifest.get("content_hash"),
        "source_hash": manifest.get("source_hash"),
        "execution_status": manifest["execution_status"],
        "top_level_verdict": manifest.get("verdict"),
        "top_level_passed": manifest.get("passed"),
        "top_level_blocked_reason": manifest.get("blocked_reason"),
        "qt_mps_backend_executed": True,
        "trajectory_mode": sampling.get("mode"),
        "trajectory_count": sampling.get("trajectory_count"),
        "rng_seed": sampling.get("rng_seed"),
        "rng_seed_was_explicit": sampling.get("rng_seed_was_explicit"),
        "record_support_policy": sampling.get("record_support_policy"),
        "emitted_record_count": len(execution.get("measurement_records", ())),
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_production_scalable_backend": False,
    }


def build_report(
    *,
    fixture: Mapping[str, Any],
    exact_manifest: Mapping[str, Any],
    sampled_manifests: Sequence[Mapping[str, Any]],
    analysis: Mapping[str, Any],
    provenance: Mapping[str, Any],
    generated_at_utc: str,
    runtime_seconds: float,
) -> dict[str, Any]:
    """Build and hash the claim-bounded diagnostic artifact."""

    exact_summary = _execution_manifest_summary(exact_manifest)
    sampled_summaries = [
        _execution_manifest_summary(manifest) for manifest in sampled_manifests
    ]
    source_hash = fixture.get("source_hash")
    if exact_summary["source_hash"] != source_hash or any(
        summary["source_hash"] != source_hash for summary in sampled_summaries
    ):
        raise ValueError("fixture and branch source hashes must match")
    passed = analysis.get("passed") is True
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "generated_at_utc": str(generated_at_utc),
        "runtime_seconds": float(runtime_seconds),
        "fixture": dict(fixture),
        "execution_provenance": dict(provenance),
        "exact_branch": exact_summary,
        "sampled_branches": sampled_summaries,
        "analysis": dict(analysis),
        "diagnostic_acceptance": {
            "verdict": "PASS" if passed else "FAIL",
            "passed": passed,
            "acceptance_basis": analysis.get("acceptance_basis"),
            "all_seed_strict_passed": analysis.get("all_seed_strict_passed"),
            "all_seed_confidence_adjusted_passed": analysis.get(
                "all_seed_confidence_adjusted_passed"
            ),
            "strict_result_is_informational": True,
            "corruption_falsifier_passed": (
                analysis.get("deliberate_corruption_falsifier", {}).get("passed")
                is True
            ),
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }
    report["content_hash_sha256"] = canonical_payload_hash(
        report,
        hash_field="content_hash_sha256",
    )
    return report


def _normalize_run_inputs(
    *,
    trajectory_count: int,
    seeds: Sequence[int],
) -> tuple[int, tuple[int, ...]]:
    if isinstance(trajectory_count, bool) or not isinstance(trajectory_count, int):
        raise TypeError("trajectory_count must be an integer, not bool")
    if trajectory_count <= 0:
        raise ValueError("trajectory_count must be positive")
    normalized_seeds: list[int] = []
    for seed in seeds:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError("seeds must contain integers, not bool")
        if seed < 0:
            raise ValueError("seeds must be nonnegative")
        normalized_seeds.append(seed)
    if len(normalized_seeds) < 2:
        raise ValueError("at least two explicit seeds are required")
    if len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("explicit seeds must be distinct")
    return trajectory_count, tuple(normalized_seeds)


def run_diagnostic(
    *,
    trajectory_count: int = DEFAULT_TRAJECTORY_COUNT,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    output: Path | None = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    """Run exact and explicit-seed sampled branches and optionally write JSON."""

    ntraj, normalized_seeds = _normalize_run_inputs(
        trajectory_count=trajectory_count,
        seeds=seeds,
    )
    started = time.perf_counter()
    schedule, fixture = build_hand_checkable_schedule()

    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA,
        axis1_qt_mps_restricted_execution_manifest,
    )

    if AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA != EXPECTED_QT_EXECUTION_SCHEMA:
        raise RuntimeError(
            "diagnostic is bound to QT/MPS restricted execution schema v6; "
            f"runtime reports {AXIS1_QT_MPS_RESTRICTED_EXECUTION_SCHEMA!r}"
        )
    common = {
        "device": "cuda",
        "max_bond": None,
        "max_branches": 64,
        "max_record_materialization_outcomes": 16,
        "microstep_count": 1,
        "finite_step_order": "first_order",
        "dense_oracle_certification": False,
    }
    exact_manifest = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        **common,
    )
    sampled_manifests = [
        axis1_qt_mps_restricted_execution_manifest(
            schedule,
            **common,
            trajectory_count=ntraj,
            rng_seed=seed,
        )
        for seed in normalized_seeds
    ]
    exact_execution = exact_manifest.get("mps_execution")
    if not isinstance(exact_execution, Mapping):
        raise RuntimeError("exact QT/MPS branch produced no execution payload")
    sampled_executions: list[Mapping[str, Any]] = []
    for index, manifest in enumerate(sampled_manifests):
        execution = manifest.get("mps_execution")
        if not isinstance(execution, Mapping):
            raise RuntimeError(f"sampled QT/MPS branch {index} produced no payload")
        sampled_executions.append(execution)
    analysis = analyze_distribution_payloads(
        exact_execution,
        sampled_executions,
        trajectory_count=ntraj,
    )
    provenance = execution_provenance(
        schedule_source_hash=schedule.source_hash,
    )
    report = build_report(
        fixture=fixture,
        exact_manifest=exact_manifest,
        sampled_manifests=sampled_manifests,
        analysis=analysis,
        provenance=provenance,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        runtime_seconds=time.perf_counter() - started,
    )
    if output is not None:
        atomic_write_json(Path(output), report)
    return report


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trajectory-count",
        type=int,
        default=DEFAULT_TRAJECTORY_COUNT,
        help="Sampled trajectories per explicit seed (default: %(default)s).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=list(DEFAULT_SEEDS),
        help="Two or more distinct nonnegative explicit seeds.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Atomic JSON report path (default: %(default)s).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run_diagnostic(
        trajectory_count=args.trajectory_count,
        seeds=tuple(args.seeds),
        output=args.output,
    )
    summary = {
        "output": str(args.output),
        "verdict": report["diagnostic_acceptance"]["verdict"],
        "content_hash_sha256": report["content_hash_sha256"],
        "runtime_seconds": report["runtime_seconds"],
        "seed_tv": [
            {
                "rng_seed": row["rng_seed"],
                "total_variation_distance": row["total_variation_distance"],
                "strict_passed": row["strict_passed"],
                "confidence_adjusted_gross_gate": row[
                    "confidence_adjusted_gross_gate"
                ],
                "confidence_adjusted_passed": row[
                    "confidence_adjusted_passed"
                ],
            }
            for row in report["analysis"]["seed_comparisons"]
        ],
        "corruption_falsifier_tv": report["analysis"][
            "deliberate_corruption_falsifier"
        ]["total_variation_distance"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["diagnostic_acceptance"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

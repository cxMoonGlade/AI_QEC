#!/usr/bin/env python3
"""Supervise the committed GCAPEPS native 1/4-thread T3 regression.

The runner launches fresh worker processes for the frozen operation-100
finite-memory prefix.  Its verdict is limited to deterministic execution of
the selected finite-cap algorithm.  Candidate-versus-dense state accuracy,
generic PEPS faithfulness, QEC Records, and speed claims are outside scope.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "native_thread_regression.v1"
)
THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
CHECKPOINT_OPERATIONS = (99, 100)
INPUT_ID = 2
NATIVE_STRATEGY = "native_simple_update"
LEGACY_STRATEGY = "exact_tree_then_native_compress"
_NO_SHADOW_CAUSE = "not_observed_without_shadow"
_REPOSITORY = Path(__file__).resolve().parents[2]
_WORKER = Path(__file__).resolve().with_name(
    "gcapeps_native_thread_worker.py"
)
_FIXTURE_OWNER = Path(__file__).resolve().with_name(
    "emit_gcapeps_finite_memory_fixture.py"
)
_DEFAULT_FORK_PYTHON = (
    _REPOSITORY
    / "external/forks/quimb-gcapeps/.pixi/envs/testpymid/bin/python"
)
_MAX_CHILD_STDOUT_BYTES = 64 * 1024 * 1024
_BANDS = {
    "relative_state_distance_max": 1.0e-9,
    "relative_norm_distance_max": 1.0e-10,
    "one_minus_fidelity_max": 1.0e-10,
    "fidelity_roundoff_correction_max": 1.0e-12,
}

EXPECTED_SPLIT_POLICY = {
    "max_bond": 32,
    "cutoff": 0.0,
    "cutoff_mode": "rel",
    "method": "svd",
    "renorm": False,
    "absorb": None,
    "smudge": 1.0e-12,
    "smudge_mode": "add",
    "power": 1.0,
}


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _projection_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path.resolve(strict=True))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _parse_json(raw: bytes, *, name: str) -> Mapping[str, Any]:
    if not isinstance(raw, bytes) or not raw:
        raise ValueError(f"{name} is empty")
    if len(raw) > _MAX_CHILD_STDOUT_BYTES:
        raise ValueError(f"{name} exceeds the byte cap")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON token {token}")
            ),
        )
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name} is not UTF-8") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} root must be an object")
    return value


def build_frozen_fixture() -> Mapping[str, Any]:
    owner = _load_path("_gcapeps_native_t3_fixture", _FIXTURE_OWNER)
    fixture = owner.build_fixture(
        run_partition="CALIBRATION",
        width=7,
        rounds=4,
        axis_family=3,
        p_event_numerator=3,
        seed=2,
        gamma_index=2,
        run_blpensemble=False,
    )
    owner.validate_fixture(fixture)
    if fixture["case_id"] != "calibration-g2-s2-w7-r4-a3-p3of4":
        raise ValueError("frozen T3 case id drifted")
    return fixture


def child_environment(
    parent: Mapping[str, str],
    *,
    thread_count: int,
) -> dict[str, str]:
    """Build the exact fresh-child thread envelope."""

    if isinstance(thread_count, bool) or thread_count not in (1, 4):
        raise ValueError("thread_count must be exactly 1 or 4")
    environment = dict(parent)
    environment.pop("PYTHONPATH", None)
    value = str(thread_count)
    for name in THREAD_VARIABLES:
        environment[name] = value
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _run_child(
    *,
    fixture_bytes: bytes,
    fork_python: Path,
    thread_count: int,
    strategy: str,
    shadow_evidence: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    command = [
        str(fork_python),
        str(_WORKER),
        "--thread-count",
        str(thread_count),
        "--strategy",
        strategy,
    ]
    if shadow_evidence:
        command.append("--shadow-evidence")
    environment = child_environment(
        os.environ,
        thread_count=thread_count,
    )
    wall_start = time.perf_counter_ns()
    completed = subprocess.run(
        command,
        cwd=_REPOSITORY,
        env=environment,
        input=fixture_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )
    elapsed = time.perf_counter_ns() - wall_start
    if completed.returncode != 0:
        raise RuntimeError(
            f"worker failed with code {completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    if completed.stderr:
        raise RuntimeError(
            "worker emitted unexpected stderr: "
            + completed.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    core = dict(_parse_json(completed.stdout, name="worker stdout"))
    core["supervisor_process_receipt"] = {
        "thread_count": thread_count,
        "strategy": strategy,
        "shadow_evidence": shadow_evidence,
        "returncode": completed.returncode,
        "parent_observed_wall_duration_ns": elapsed,
        "stdout_nbytes": len(completed.stdout),
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_nbytes": 0,
    }
    return core


def decode_raw_vector(payload: Mapping[str, Any], *, n_qubits: int):
    """Decode one exact c128 ndarray-v1 payload without coordinate changes."""

    import numpy as np

    expected_keys = {
        "encoding",
        "dtype",
        "shape",
        "order",
        "nbytes",
        "data_sha256",
        "data_base64",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected_keys:
        raise ValueError("vector payload has the wrong exact key set")
    if (
        payload["encoding"] != "ndarray-v1"
        or payload["dtype"] != "<c16"
        or payload["shape"] != [1 << n_qubits]
        or payload["order"] != "C"
        or payload["nbytes"] != (1 << n_qubits) * 16
    ):
        raise ValueError("vector encoding identity drifted")
    try:
        raw = base64.b64decode(payload["data_base64"], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("vector base64 is invalid") from exc
    if (
        len(raw) != payload["nbytes"]
        or hashlib.sha256(raw).hexdigest() != payload["data_sha256"]
    ):
        raise ValueError("vector byte identity failed")
    vector = np.frombuffer(raw, dtype=np.dtype("<c16")).copy()
    if (
        vector.shape != (1 << n_qubits,)
        or vector.dtype != np.dtype(np.complex128)
        or not vector.flags.c_contiguous
        or not np.isfinite(vector.real).all()
        or not np.isfinite(vector.imag).all()
    ):
        raise ValueError("decoded vector violates the raw c128 contract")
    return vector


def raw_complete_vector_metrics(reference, candidate) -> dict[str, Any]:
    """Compute the preregistered raw metrics with no phase or norm fitting."""

    import numpy as np

    if (
        not isinstance(reference, np.ndarray)
        or not isinstance(candidate, np.ndarray)
        or reference.dtype != np.dtype(np.complex128)
        or candidate.dtype != np.dtype(np.complex128)
        or reference.ndim != 1
        or candidate.shape != reference.shape
        or reference.size == 0
        or not np.isfinite(reference).all()
        or not np.isfinite(candidate).all()
    ):
        raise ValueError("raw metric inputs must be same-shape finite c128 vectors")
    reference_mass = np.vdot(reference, reference)
    candidate_mass = np.vdot(candidate, candidate)
    overlap = np.vdot(reference, candidate)
    scalar_values = (
        reference_mass.real,
        reference_mass.imag,
        candidate_mass.real,
        candidate_mass.imag,
        overlap.real,
        overlap.imag,
    )
    if not all(math.isfinite(float(value)) for value in scalar_values):
        raise ValueError("raw inner products are non-finite")
    if reference_mass.real <= 0.0 or candidate_mass.real <= 0.0:
        raise ValueError("raw vector mass must be strictly positive")
    if (
        abs(float(reference_mass.imag)) > 1.0e-12
        or abs(float(candidate_mass.imag)) > 1.0e-12
    ):
        raise ValueError("raw norm-squared has an imaginary residual")
    fidelity_denominator = float(
        reference_mass.real * candidate_mass.real
    )
    if not math.isfinite(fidelity_denominator) or fidelity_denominator <= 0.0:
        raise ValueError("fidelity denominator is invalid")
    fidelity_raw = float(abs(overlap) ** 2 / fidelity_denominator)
    if not math.isfinite(fidelity_raw) or fidelity_raw < 0.0:
        raise ValueError("raw fidelity is invalid")
    correction = max(0.0, fidelity_raw - 1.0)
    if correction > _BANDS["fidelity_roundoff_correction_max"]:
        raise ValueError("fidelity exceeds one beyond clipping allowance")
    fidelity = min(1.0, fidelity_raw)
    difference = candidate - reference
    d2 = float(np.linalg.norm(difference))
    dinf = float(np.max(np.abs(difference), initial=0.0))
    reference_norm = math.sqrt(float(reference_mass.real))
    candidate_norm = math.sqrt(float(candidate_mass.real))
    norm_sum = reference_norm + candidate_norm
    if not math.isfinite(norm_sum) or norm_sum <= 0.0:
        raise ValueError("raw norm sum is invalid")
    d_rel = 2.0 * d2 / norm_sum
    d_norm = 2.0 * abs(reference_norm - candidate_norm) / norm_sum
    metrics = {
        "dinf_raw": dinf,
        "d2_raw": d2,
        "relative_state_distance": d_rel,
        "relative_norm_distance": d_norm,
        "reference_raw_norm": reference_norm,
        "candidate_raw_norm": candidate_norm,
        "reference_raw_norm_squared": float(reference_mass.real),
        "candidate_raw_norm_squared": float(candidate_mass.real),
        "overlap_real": float(overlap.real),
        "overlap_imag": float(overlap.imag),
        "fidelity_denominator": fidelity_denominator,
        "fidelity_raw": fidelity_raw,
        "fidelity_roundoff_correction": correction,
        "fidelity": fidelity,
        "one_minus_fidelity": 1.0 - fidelity,
        "phase_fit": False,
        "normalization_before_comparison": False,
        "dtype_cast": False,
        "coordinate_permutation": False,
    }
    numeric = [
        value
        for value in metrics.values()
        if isinstance(value, float)
    ]
    if not all(math.isfinite(value) for value in numeric):
        raise ValueError("raw metric computation produced a non-finite value")
    gates = {
        "relative_state_distance": (
            d_rel <= _BANDS["relative_state_distance_max"]
        ),
        "relative_norm_distance": (
            d_norm <= _BANDS["relative_norm_distance_max"]
        ),
        "one_minus_fidelity": (
            1.0 - fidelity <= _BANDS["one_minus_fidelity_max"]
        ),
        "fidelity_roundoff_correction": (
            correction
            <= _BANDS["fidelity_roundoff_correction_max"]
        ),
    }
    return {
        "metrics": metrics,
        "bands": dict(_BANDS),
        "gates": gates,
        "passed": all(gates.values()),
    }


def _checkpoint_vector(child: Mapping[str, Any], operation_index: int):
    row = child["checkpoints"][str(operation_index)]
    vector = decode_raw_vector(row["vector"], n_qubits=14)
    raw_sha = hashlib.sha256(vector.tobytes(order="C")).hexdigest()
    if (
        row["operation_index"] != operation_index
        or row["pre_metric"]["raw_vector_sha256"] != raw_sha
        or row["vector"]["data_sha256"] != raw_sha
    ):
        raise ValueError("checkpoint vector hashes do not join")
    return vector


def _metadata_projection(
    child: Mapping[str, Any],
    operation_index: int,
) -> dict[str, Any]:
    row = child["checkpoint_metadata"][str(operation_index)]
    required = (
        "operation_index",
        "round_index",
        "physical_request",
        "physical_pauli",
        "signed_pulled_word",
        "pullback",
        "strategy",
        "update_strategy",
        "routing_root",
        "routing_vertices",
        "routing_tree_edges",
        "configured_max_bond",
        "configured_cutoff",
    )
    if any(key not in row for key in required):
        raise ValueError("checkpoint metadata is incomplete")
    projection = {key: row[key] for key in required}
    if child["strategy"] == NATIVE_STRATEGY:
        for key in (
            "plan_digest_sha256",
            "canonical_gate_transcript",
            "candidate_kept_dimensions",
        ):
            if key not in row:
                raise ValueError("native checkpoint metadata is incomplete")
            projection[key] = row[key]
    return projection


def _validate_child_identity(
    child: Mapping[str, Any],
    *,
    fixture: Mapping[str, Any],
    thread_count: int,
    strategy: str,
    shadow_evidence: bool,
) -> None:
    if child.get("schema") != (
        "error_coupling_simulator.external.gcapeps_finite_memory."
        "native_thread_worker.v1"
    ):
        raise ValueError("worker schema drifted")
    identity = child["fixture_identity"]
    if (
        child["formal_claim_eligible"] is not False
        or child["faithfulness_claim"] is not False
        or child["performance_claim"] is not False
        or child["strategy"] != strategy
        or child["shadow_evidence_enabled"] is not shadow_evidence
        or identity["fixture_projection_sha256"]
        != fixture["result_projection_sha256"]
        or identity["input_id"] != INPUT_ID
        or identity["stop_after_operation"] != 100
        or identity["checkpoint_operations"] != [99, 100]
        or child["operation_count"] != 101
    ):
        raise ValueError("worker identity disagrees with the T3 request")
    environment = child["environment"]
    if (
        environment["requested_thread_count"] != thread_count
        or environment["CUDA_VISIBLE_DEVICES"] != ""
        or environment["PYTHONHASHSEED"] != "0"
        or environment["PYTHONPATH_present"] is not False
        or environment[
            "validated_before_numpy_quimb_stim_import"
        ] is not True
        or any(
            environment["thread_variables"][name] != str(thread_count)
            for name in THREAD_VARIABLES
        )
    ):
        raise ValueError("worker environment receipt is invalid")
    if child.get("split_policy") != EXPECTED_SPLIT_POLICY:
        raise ValueError("worker split policy drifted")
    if not shadow_evidence and (
        child["shadow_builder_call_count"] != 0
        or child["shadow_span_count"] != 0
        or child["shadow_evidence_bytes"] != 0
    ):
        raise ValueError("no-shadow worker performed shadow work")
    for operation_index in CHECKPOINT_OPERATIONS:
        _checkpoint_vector(child, operation_index)
        _metadata_projection(child, operation_index)


def _pair_comparison(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    name: str,
) -> dict[str, Any]:
    checkpoints = {}
    for operation_index in CHECKPOINT_OPERATIONS:
        left_vector = _checkpoint_vector(left, operation_index)
        right_vector = _checkpoint_vector(right, operation_index)
        metrics = raw_complete_vector_metrics(left_vector, right_vector)
        left_metadata = _metadata_projection(left, operation_index)
        right_metadata = _metadata_projection(right, operation_index)
        metadata_equal = (
            _canonical_json_bytes(left_metadata)
            == _canonical_json_bytes(right_metadata)
        )
        checkpoints[str(operation_index)] = {
            "operation_index": operation_index,
            "raw_metrics": metrics,
            "exact_metadata_equal": metadata_equal,
            "left_metadata_projection_sha256": _projection_sha256(
                left_metadata
            ),
            "right_metadata_projection_sha256": _projection_sha256(
                right_metadata
            ),
            "passed": metrics["passed"] and metadata_equal,
        }
    return {
        "name": name,
        "phase_fit": False,
        "checkpoints": checkpoints,
        "passed": all(row["passed"] for row in checkpoints.values()),
    }


def select_nondegeneracy_witness(
    evidence_child: Mapping[str, Any],
) -> dict[str, Any] | None:
    for operation in evidence_child["operation_records"]:
        ledger = operation.get("native_execution_ledger")
        if not isinstance(ledger, Mapping):
            continue
        for split_index, split in enumerate(ledger["split_records"]):
            full_dimension = split["full_bond_dimension"]
            kept_dimension = split["candidate_kept_bond_dimension"]
            fraction = split["discarded_fraction"]
            if (
                isinstance(full_dimension, int)
                and not isinstance(full_dimension, bool)
                and full_dimension > 32
                and kept_dimension == 32
                and split["cause"] == "max_bond"
                and isinstance(fraction, (int, float))
                and not isinstance(fraction, bool)
                and math.isfinite(float(fraction))
                and float(fraction) > 1.0e-12
            ):
                return {
                    "operation_index": operation["operation_index"],
                    "round_index": operation["round_index"],
                    "split_index": split_index,
                    "native_step_index": split["step_index"],
                    "edge": split["edge"],
                    "full_bond_dimension": full_dimension,
                    "kept_bond_dimension": kept_dimension,
                    "cause": split["cause"],
                    "discarded_fraction": float(fraction),
                }
    return None


def _timing_inventory(child: Mapping[str, Any]) -> dict[str, Any]:
    timing = child["timing"]
    if (
        timing["schema"]
        != (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "layered_timing.v1"
        )
        or timing["wall_clock"] != "time.perf_counter_ns"
        or timing["cpu_clock"] != "time.process_time_ns"
    ):
        raise ValueError("worker timing identity drifted")
    required_scopes = {
        "child_total",
        "initialization",
        "physical_operation",
        "named_algorithm_substep",
        "checkpoint_contraction",
        "serialization",
        "publication_accounting",
    }
    scopes = {row["scope"] for row in timing["spans"]}
    if not required_scopes.issubset(scopes):
        raise ValueError("worker timing lacks required scopes")
    totals = {}
    for row in timing["spans"]:
        key = f"{row['scope']}::{row['kind']}"
        aggregate = totals.setdefault(
            key,
            {
                "span_count": 0,
                "wall_duration_ns": 0,
                "cpu_duration_ns": 0,
            },
        )
        aggregate["span_count"] += 1
        aggregate["wall_duration_ns"] += row["wall_duration_ns"]
        aggregate["cpu_duration_ns"] += row["cpu_duration_ns"]
    return {
        "clock_identity": {
            "wall_clock": timing["wall_clock"],
            "cpu_clock": timing["cpu_clock"],
        },
        "raw_spans": timing["spans"],
        "aggregated_by_scope_and_kind": totals,
        "supervisor_process_receipt": child[
            "supervisor_process_receipt"
        ],
    }


def build_report(
    *,
    fixture: Mapping[str, Any],
    native_thread1: Mapping[str, Any],
    native_thread4: Mapping[str, Any],
    native_evidence_thread1: Mapping[str, Any],
    legacy_children: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    _validate_child_identity(
        native_thread1,
        fixture=fixture,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
    )
    _validate_child_identity(
        native_thread4,
        fixture=fixture,
        thread_count=4,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
    )
    _validate_child_identity(
        native_evidence_thread1,
        fixture=fixture,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=True,
    )
    thread_comparison = _pair_comparison(
        native_thread1,
        native_thread4,
        name="native_one_thread_vs_four_threads",
    )
    shadow_comparison = _pair_comparison(
        native_thread1,
        native_evidence_thread1,
        name="native_no_shadow_vs_evidence_shadow",
    )
    witness = select_nondegeneracy_witness(native_evidence_thread1)
    timing = {
        "native_threads1_no_shadow": _timing_inventory(native_thread1),
        "native_threads4_no_shadow": _timing_inventory(native_thread4),
        "native_threads1_evidence": _timing_inventory(
            native_evidence_thread1
        ),
    }
    legacy_report = None
    legacy_required_red = True
    if legacy_children:
        if len(legacy_children) != 2:
            raise ValueError("legacy diagnostic requires one and four threads")
        for thread_count, child in zip((1, 4), legacy_children):
            _validate_child_identity(
                child,
                fixture=fixture,
                thread_count=thread_count,
                strategy=LEGACY_STRATEGY,
                shadow_evidence=False,
            )
        legacy_comparison = _pair_comparison(
            legacy_children[0],
            legacy_children[1],
            name="legacy_diagnostic_one_thread_vs_four_threads",
        )
        legacy_report = {
            "lane": "gcapeps_exact_tree_compress_diagnostic_only",
            "formal_claim_eligible": False,
            "comparison": legacy_comparison,
            "violates_at_least_one_native_band_at_operation_100": (
                not legacy_comparison["checkpoints"]["100"]["passed"]
            ),
            "timing": {
                "threads1": _timing_inventory(legacy_children[0]),
                "threads4": _timing_inventory(legacy_children[1]),
            },
        }
        legacy_required_red = legacy_report[
            "violates_at_least_one_native_band_at_operation_100"
        ]
    passed = bool(
        thread_comparison["passed"]
        and shadow_comparison["passed"]
        and witness is not None
        and legacy_required_red
    )
    report = {
        "schema": SCHEMA,
        "formal_claim_eligible": False,
        "faithfulness_claim": False,
        "performance_claim": False,
        "selected_strategy": NATIVE_STRATEGY,
        "split_policy": dict(EXPECTED_SPLIT_POLICY),
        "fixture_identity": {
            "case_id": fixture["case_id"],
            "fixture_projection_sha256": fixture[
                "result_projection_sha256"
            ],
            "parameters": fixture["parameters"],
            "input_id": INPUT_ID,
            "checkpoint_operations": list(CHECKPOINT_OPERATIONS),
        },
        "thread_invariance": thread_comparison,
        "shadow_isolation": shadow_comparison,
        "nondegeneracy_witness": witness,
        "nondegeneracy_passed": witness is not None,
        "timing": timing,
        "raw_children": {
            "native_threads1_no_shadow": native_thread1,
            "native_threads4_no_shadow": native_thread4,
            "native_threads1_evidence": native_evidence_thread1,
        },
        "legacy_diagnostic": legacy_report,
        "dense_pairing": {
            "status": "not_run_by_this_regression",
            "role": "report_only_development_reference",
            "acceptance_band": None,
        },
        "passed": passed,
        "verdict": (
            "PASS_ENGINEERING_NATIVE_THREAD_REGRESSION"
            if passed
            else "FAIL_ENGINEERING_NATIVE_THREAD_REGRESSION"
        ),
        "claim_boundary": (
            "deterministic execution of one bounded finite-cap native "
            "algorithm prefix only; no whole-state faithfulness, generic "
            "PEPS, QEC Record, or speed conclusion"
        ),
        "source_identity": {
            "runner_source_sha256": _source_sha256(
                Path(__file__).resolve(strict=True)
            ),
            "worker_source_sha256": _source_sha256(_WORKER),
            "fixture_owner_source_sha256": _source_sha256(_FIXTURE_OWNER),
        },
        "result_projection_sha256": "",
    }
    report["result_projection_sha256"] = _projection_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "result_projection_sha256"
        }
    )
    return report


def run_regression(
    *,
    fork_python: Path,
    timeout_seconds: float,
    include_legacy_diagnostic: bool,
) -> dict[str, Any]:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0.0:
        raise ValueError("timeout_seconds must be finite and positive")
    fork_python = fork_python.resolve(strict=True)
    if not fork_python.is_file() or not os.access(fork_python, os.X_OK):
        raise ValueError("fork Python is not an executable file")
    fixture = build_frozen_fixture()
    fixture_bytes = _canonical_json_bytes(fixture)
    native_thread1 = _run_child(
        fixture_bytes=fixture_bytes,
        fork_python=fork_python,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
        timeout_seconds=timeout_seconds,
    )
    native_thread4 = _run_child(
        fixture_bytes=fixture_bytes,
        fork_python=fork_python,
        thread_count=4,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=False,
        timeout_seconds=timeout_seconds,
    )
    native_evidence = _run_child(
        fixture_bytes=fixture_bytes,
        fork_python=fork_python,
        thread_count=1,
        strategy=NATIVE_STRATEGY,
        shadow_evidence=True,
        timeout_seconds=timeout_seconds,
    )
    legacy = []
    if include_legacy_diagnostic:
        for thread_count in (1, 4):
            legacy.append(
                _run_child(
                    fixture_bytes=fixture_bytes,
                    fork_python=fork_python,
                    thread_count=thread_count,
                    strategy=LEGACY_STRATEGY,
                    shadow_evidence=False,
                    timeout_seconds=timeout_seconds,
                )
            )
    return build_report(
        fixture=fixture,
        native_thread1=native_thread1,
        native_thread4=native_thread4,
        native_evidence_thread1=native_evidence,
        legacy_children=legacy,
    )


def _publish_fresh(path: Path, payload: bytes) -> None:
    target = path.resolve(strict=False)
    parent = target.parent.resolve(strict=True)
    if target.exists():
        raise FileExistsError(f"output already exists: {target}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fork-python-executable",
        type=Path,
        default=_DEFAULT_FORK_PYTHON,
    )
    parser.add_argument("--timeout-seconds", type=float, default=3600.0)
    parser.add_argument(
        "--include-legacy-diagnostic",
        action="store_true",
        help="also run the explicitly ineligible legacy one/four-thread lane",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run_regression(
        fork_python=args.fork_python_executable,
        timeout_seconds=args.timeout_seconds,
        include_legacy_diagnostic=args.include_legacy_diagnostic,
    )
    encoded = _canonical_json_bytes(report) + b"\n"
    if args.output is None:
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    else:
        _publish_fresh(args.output, encoded)
        summary = {
            "schema": report["schema"],
            "verdict": report["verdict"],
            "passed": report["passed"],
            "formal_claim_eligible": False,
            "output": str(args.output.resolve(strict=True)),
            "output_sha256": hashlib.sha256(encoded).hexdigest(),
        }
        sys.stdout.buffer.write(_canonical_json_bytes(summary) + b"\n")
        sys.stdout.buffer.flush()
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

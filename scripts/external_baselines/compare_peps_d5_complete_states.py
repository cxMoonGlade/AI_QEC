#!/usr/bin/env python3
"""Compare complete complex128 states for the frozen PEPS d3/d5 fixture.

This is the sole verdict-driving fidelity owner for the external PEPS
benchmark.  It rejects local retained-weight, discarded-tail, and contraction
residual proxies: both inputs must be complete, identically ordered state
vectors whose bytes and producing summaries pass provenance checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import tempfile
import time
from typing import Any, Mapping

import numpy as np


RESULT_SCHEMA = (
    "error_coupling_simulator.external.peps_complete_state_fidelity.v1"
)
REFERENCE_SCHEMA = (
    "error_coupling_simulator.external.peps_d5_dense_reference.v1"
)
ALLOWED_CANDIDATE_SCHEMAS = {
    "error_coupling_simulator.external.quimb_peps_d5_state.v1",
    "error_coupling_simulator.external.pepsy_peps_d5_state.v1",
}
REPO = Path(__file__).resolve().parents[2]
COMMITTED_INPUTS = (
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md"
    ),
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md"
    ),
    "scripts/external_baselines/compare_peps_d5_complete_states.py",
    "tests/test_external_peps_d5_pure_state_fidelity.py",
)
REFERENCE_COMMITTED_INPUTS = (
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md"
    ),
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md"
    ),
    "scripts/external_baselines/emit_peps_d5_pure_state_fixture.py",
    "scripts/external_baselines/peps_d5_dense_reference.py",
    "tests/test_external_peps_d5_pure_state_fidelity.py",
)
SCHEMA_PROVENANCE_POLICIES = {
    REFERENCE_SCHEMA: {
        "worker": (
            "scripts/external_baselines/peps_d5_dense_reference.py"
        ),
        "committed_inputs": REFERENCE_COMMITTED_INPUTS,
    },
    "error_coupling_simulator.external.quimb_peps_d5_state.v1": {
        "worker": (
            "scripts/external_baselines/quimb_peps_d5_fidelity_worker.py"
        ),
        "committed_inputs": (
            "baseline-environment-quimb-peps-linux-64.lock.json",
            "docs/METRICS.md",
            (
                "docs/simulator_validation/"
                "PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md"
            ),
            (
                "docs/simulator_validation/"
                "PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md"
            ),
            "scripts/external_baselines/emit_peps_d5_pure_state_fixture.py",
            (
                "scripts/external_baselines/"
                "build_quimb_peps_d5_environment_lock.py"
            ),
            (
                "scripts/external_baselines/"
                "quimb_peps_d5_fidelity_worker.py"
            ),
            "tests/test_external_peps_d5_pure_state_fidelity.py",
        ),
        "environment_lock": (
            "baseline-environment-quimb-peps-linux-64.lock.json"
        ),
        "environment_lock_schema": (
            "error_coupling_simulator.environment_lock.quimb_peps_d5.v1"
        ),
        "environment_name": "ecs-baseline-quimb-peps",
        "source_key": "quimb_source_clone",
        "installed_key": "installed_quimb",
        "source_commit": (
            "3c89529fe0a3487133a3928201691161e110abdf"
        ),
    },
    "error_coupling_simulator.external.pepsy_peps_d5_state.v1": {
        "worker": (
            "scripts/external_baselines/pepsy_peps_d5_state_worker.py"
        ),
        "committed_inputs": (
            "baseline-environment-pepsy-linux-64.lock.json",
            "docs/METRICS.md",
            (
                "docs/simulator_validation/"
                "PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md"
            ),
            (
                "docs/simulator_validation/"
                "PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md"
            ),
            (
                "scripts/external_baselines/"
                "build_pepsy_baseline_environment.py"
            ),
            "scripts/external_baselines/emit_peps_d5_pure_state_fixture.py",
            "scripts/external_baselines/pepsy_peps_d5_state_worker.py",
            "tests/test_external_peps_d5_pure_state_fidelity.py",
        ),
        "environment_lock": (
            "baseline-environment-pepsy-linux-64.lock.json"
        ),
        "environment_lock_schema": (
            "error_coupling_simulator.environment_lock.pepsy_peps_d5.v1"
        ),
        "environment_name": "ecs-baseline-pepsy",
        "source_key": "pepsy_source_clone",
        "installed_key": "installed_pepsy",
        "source_commit": (
            "27cb956ec88a739daece90407833bd3c3f8e1d8f"
        ),
    },
}
FIXTURE_POLICIES = {
    3: {
        "canonical_sha256": (
            "d53a3cd27e53f3fcf5fbe8c0d91232d1f81e2f8d914d78bea6914ec3988c4125"
        ),
        "operation_count": 88,
    },
    5: {
        "canonical_sha256": (
            "c73b932ff8c213d6dce956cddb9bee0c9bfa2b465bde3bc6a3ece5789aed1324"
        ),
        "operation_count": 272,
    },
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to replace existing output: {path}")
    encoded = (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _verify_committed_inputs() -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    hashes: dict[str, str] = {}
    for relative in COMMITTED_INPUTS:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if tracked.returncode != 0:
            raise RuntimeError(f"claim-bearing input is untracked: {relative}")
        changed = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", relative],
            cwd=REPO,
        )
        if changed.returncode != 0:
            raise RuntimeError(
                f"claim-bearing input differs from HEAD: {relative}"
            )
        hashes[relative] = _file_sha256(REPO / relative)
    return {"git_head": head, "sha256": hashes}


def _load_summary(path: Path, *, allowed_schemas: set[str]) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"summary is not an object: {path}")
    if payload.get("schema") not in allowed_schemas:
        raise ValueError(f"unsupported summary schema: {payload.get('schema')!r}")
    if payload.get("status") != "completed":
        raise ValueError("state summary is not completed")
    return payload


def _resolve_complete_state(
    summary: Mapping[str, Any],
) -> tuple[Path, np.ndarray]:
    state_metadata = summary.get("state")
    if not isinstance(state_metadata, dict):
        raise ValueError("summary has no state metadata")
    if state_metadata.get("dtype") != "complex128":
        raise ValueError("complete state metadata must declare complex128")
    if (
        state_metadata.get("source_kind")
        != "complete_complex128_state_vector"
    ):
        raise ValueError(
            "state source_kind must be complete_complex128_state_vector"
        )
    state_path = Path(state_metadata.get("path", ""))
    if not state_path.is_absolute() or not state_path.is_file():
        raise ValueError("complete state path must be an existing absolute file")
    if _file_sha256(state_path) != state_metadata.get("file_sha256"):
        raise ValueError("complete state file hash mismatch")
    state = np.load(state_path, mmap_mode="r", allow_pickle=False)
    if state.dtype != np.complex128 or state.ndim != 1:
        raise ValueError("complete state must be a one-dimensional complex128 array")
    if list(state.shape) != state_metadata.get("shape"):
        raise ValueError("complete state shape differs from summary")
    return state_path, state


def _expected_amplitude_convention(distance: int) -> dict[str, Any]:
    site_count = distance * distance
    return {
        "storage": "one_dimensional_c_order_complex128",
        "qubit_axis_order": list(range(site_count)),
        "q0_axis": 0,
        "q0_bit_significance": "most_significant",
        "flat_index": "sum_q bit(q)*2**(site_count-1-q)",
        "local_basis": ["|0>", "|1>"],
        "two_qubit_basis": ["|00>", "|01>", "|10>", "|11>"],
        "target_to_kronecker_factor": (
            "targets[0] is the left Kronecker factor and the more "
            "significant local basis bit"
        ),
        "matrix_indices": "row_is_output_column_is_input",
        "chronological_update": (
            "operations execute in ascending index; psi <- U_operation*psi; "
            "final_state=U_last*...*U_1*U_0*initial_state"
        ),
    }


def _validate_fixture_binding(
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> None:
    reference_fixture = reference.get("fixture")
    candidate_fixture = candidate.get("fixture")
    if (
        not isinstance(reference_fixture, dict)
        or not isinstance(candidate_fixture, dict)
    ):
        raise ValueError("summaries must carry fixture identities")
    distance = reference_fixture.get("distance_label")
    if distance not in FIXTURE_POLICIES:
        raise ValueError("fixture distance is not registered")
    policy = FIXTURE_POLICIES[distance]
    expected_claim_boundary = (
        f"controlled {distance}x{distance} pure-state unitary benchmark only; "
        "no ancilla, measurement, reset, Kraus, leakage, Record, LER, "
        "calibration, or scaling claim"
    )
    exact_fixture_fields = {
        "schema": (
            "error_coupling_simulator.external."
            "peps_d5_pure_state_fixture.v1"
        ),
        "distance_label": distance,
        "operation_count": policy["operation_count"],
        "canonical_sha256": policy["canonical_sha256"],
    }
    for summary_name, fixture in (
        ("reference", reference_fixture),
        ("candidate", candidate_fixture),
    ):
        for field, expected in exact_fixture_fields.items():
            if fixture.get(field) != expected:
                raise ValueError(
                    f"{summary_name} fixture violates pinned {field}"
                )
    if candidate_fixture.get("distance_label") != distance:
        raise ValueError("candidate fixture distance mismatch")
    if (
        reference.get("claim_boundary") != expected_claim_boundary
        or candidate.get("claim_boundary") != expected_claim_boundary
    ):
        raise ValueError("summary claim boundary violates fixture policy")
    expected_convention = _expected_amplitude_convention(distance)
    for summary_name, summary in (
        ("reference", reference),
        ("candidate", candidate),
    ):
        state_metadata = summary.get("state")
        if not isinstance(state_metadata, dict):
            raise ValueError(f"{summary_name} summary has no complete state")
        if state_metadata.get("amplitude_convention") != expected_convention:
            raise ValueError(
                f"{summary_name} amplitude convention violates fixture policy"
            )
        if state_metadata.get("shape") != [1 << (distance * distance)]:
            raise ValueError(
                f"{summary_name} state shape violates fixture policy"
            )


def _validate_worker_provenance(
    summary: Mapping[str, Any],
) -> None:
    schema = summary["schema"]
    policy = SCHEMA_PROVENANCE_POLICIES[schema]
    provenance = summary.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("state summary has no worker provenance")
    current_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if provenance.get("git_head") != current_head:
        raise ValueError("state summary Git commit is not the frozen HEAD")
    expected_worker = (REPO / policy["worker"]).resolve()
    worker_path = Path(provenance.get("worker_path", ""))
    if worker_path.resolve() != expected_worker or not expected_worker.is_file():
        raise ValueError("state summary producer is not the schema-owned worker")
    if _file_sha256(worker_path) != provenance.get("worker_sha256"):
        raise ValueError("state summary worker hash mismatch")
    committed_hashes = provenance.get("committed_input_sha256")
    required_inputs = set(policy["committed_inputs"])
    if (
        not isinstance(committed_hashes, dict)
        or set(committed_hashes) != required_inputs
    ):
        raise ValueError("state summary committed-input ledger is incomplete")
    for relative in sorted(required_inputs):
        expected_hash = committed_hashes[relative]
        if (
            not isinstance(expected_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None
        ):
            raise ValueError("invalid committed-input hash row")
        path = REPO / relative
        if not path.is_file() or _file_sha256(path) != expected_hash:
            raise ValueError(f"committed-input hash mismatch: {relative}")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        changed = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", relative],
            cwd=REPO,
        )
        if tracked.returncode != 0 or changed.returncode != 0:
            raise ValueError(f"committed-input is not frozen: {relative}")

    if "environment_lock" not in policy:
        return
    environment_lock = summary.get("environment_lock")
    if not isinstance(environment_lock, dict):
        raise ValueError("candidate summary has no environment lock")
    expected_lock_path = (REPO / policy["environment_lock"]).resolve()
    lock_path = Path(environment_lock.get("path", ""))
    if (
        lock_path.resolve() != expected_lock_path
        or not expected_lock_path.is_file()
    ):
        raise ValueError("candidate environment-lock path is not schema-owned")
    if _file_sha256(lock_path) != environment_lock.get("file_sha256"):
        raise ValueError("candidate environment-lock hash mismatch")
    lock_payload = json.loads(lock_path.read_text(encoding="utf-8"))
    if (
        lock_payload.get("schema") != policy["environment_lock_schema"]
        or lock_payload.get("environment_name") != policy["environment_name"]
        or lock_payload.get("upstream", {}).get("commit")
        != policy["source_commit"]
    ):
        raise ValueError("candidate environment lock violates schema policy")
    if (
        environment_lock.get("schema") != policy["environment_lock_schema"]
        or environment_lock.get("environment_name")
        != policy["environment_name"]
    ):
        raise ValueError("candidate summary environment-lock identity mismatch")
    source = summary.get(policy["source_key"])
    installed = summary.get(policy["installed_key"])
    if not isinstance(source, dict) or not isinstance(installed, dict):
        raise ValueError("candidate source/runtime provenance is incomplete")
    commit = source.get("commit")
    if commit != policy["source_commit"]:
        raise ValueError("candidate source commit violates schema policy")
    pristine = source.get(
        "clean_including_ignored",
        source.get("pristine_including_ignored_paths"),
    )
    if pristine is not True:
        raise ValueError("candidate source clone was not pristine")
    installed_commit = (
        installed.get("direct_url", {})
        .get("vcs_info", {})
        .get("commit_id")
    )
    if installed_commit != policy["source_commit"]:
        raise ValueError("candidate installed commit violates schema policy")


def _validate_execution_diagnostics(
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> None:
    reference_diagnostics = reference.get("diagnostics")
    candidate_diagnostics = candidate.get("diagnostics")
    if not isinstance(reference_diagnostics, dict):
        raise ValueError("reference summary has no numerical diagnostics")
    if not isinstance(candidate_diagnostics, dict):
        raise ValueError("candidate summary has no numerical diagnostics")
    requested_max_bond = candidate_diagnostics.get("requested_max_bond")
    if (
        isinstance(requested_max_bond, bool)
        or not isinstance(requested_max_bond, int)
        or not 1 <= requested_max_bond <= 16
    ):
        raise ValueError(
            f"candidate requested bond is outside [1,16]: "
            f"{requested_max_bond!r}"
        )
    bounded_rows = (
        (
            "reference gate unitarity",
            reference_diagnostics.get("max_gate_unitarity_residual"),
        ),
        (
            "reference gate semantics",
            reference_diagnostics.get("max_gate_semantic_residual"),
        ),
        (
            "reference norm",
            reference_diagnostics.get("norm_residual"),
        ),
        (
            "candidate gate unitarity",
            candidate_diagnostics.get("max_gate_unitarity_residual"),
        ),
        (
            "candidate gate semantics",
            candidate_diagnostics.get("max_gate_semantic_residual"),
        ),
    )
    for label, value in bounded_rows:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not np.isfinite(value)
            or value < 0.0
            or value > 1e-12
        ):
            raise ValueError(f"{label} diagnostic failed: {value!r}")


def normalized_fidelity_chunked(
    left: np.ndarray,
    right: np.ndarray,
    *,
    chunk_amplitudes: int = 1 << 20,
) -> dict[str, Any]:
    if (
        left.shape != right.shape
        or left.ndim != 1
        or left.dtype != np.complex128
        or right.dtype != np.complex128
    ):
        raise ValueError(
            "fidelity inputs must be equal one-dimensional complex128 arrays"
        )
    if (
        isinstance(chunk_amplitudes, bool)
        or not isinstance(chunk_amplitudes, int)
        or chunk_amplitudes < 1
    ):
        raise ValueError("chunk_amplitudes must be a positive integer")
    overlap = 0.0 + 0.0j
    left_norm = 0.0
    right_norm = 0.0
    for start in range(0, left.size, chunk_amplitudes):
        stop = min(left.size, start + chunk_amplitudes)
        left_chunk = np.asarray(left[start:stop])
        right_chunk = np.asarray(right[start:stop])
        if (
            not np.isfinite(left_chunk).all()
            or not np.isfinite(right_chunk).all()
        ):
            raise ValueError("complete state contains a non-finite amplitude")
        overlap += np.vdot(left_chunk, right_chunk)
        left_norm += float(np.vdot(left_chunk, left_chunk).real)
        right_norm += float(np.vdot(right_chunk, right_chunk).real)
    if (
        not np.isfinite(left_norm)
        or not np.isfinite(right_norm)
        or left_norm <= 0.0
        or right_norm <= 0.0
    ):
        raise ValueError("complete states must have finite positive norms")
    fidelity = float(abs(overlap) ** 2 / (left_norm * right_norm))
    if not np.isfinite(fidelity) or not -1e-10 <= fidelity <= 1.0 + 1e-10:
        raise ValueError(f"invalid normalized fidelity: {fidelity!r}")
    fidelity = min(1.0, max(0.0, fidelity))
    return {
        "normalized_squared_overlap": fidelity,
        "infidelity": 1.0 - fidelity,
        "overlap_real": float(overlap.real),
        "overlap_imag": float(overlap.imag),
        "reference_norm_squared": left_norm,
        "candidate_norm_squared": right_norm,
        "chunk_amplitudes": chunk_amplitudes,
    }


def _classify(fidelity: float) -> str:
    if fidelity >= 0.99:
        return "useful"
    if fidelity >= 0.95:
        return "marginal"
    return "low"


def compare_summaries(
    reference_summary_path: Path,
    candidate_summary_path: Path,
    *,
    chunk_amplitudes: int,
) -> dict[str, Any]:
    reference = _load_summary(
        reference_summary_path,
        allowed_schemas={REFERENCE_SCHEMA},
    )
    candidate = _load_summary(
        candidate_summary_path,
        allowed_schemas=ALLOWED_CANDIDATE_SCHEMAS,
    )
    _validate_fixture_binding(reference, candidate)
    _validate_worker_provenance(reference)
    _validate_worker_provenance(candidate)
    _validate_execution_diagnostics(reference, candidate)
    reference_fixture = reference["fixture"]
    candidate_fixture = candidate["fixture"]
    identity_fields = (
        "schema",
        "distance_label",
        "operation_count",
        "canonical_sha256",
    )
    for field in identity_fields:
        if reference_fixture.get(field) != candidate_fixture.get(field):
            raise ValueError(f"fixture identity mismatch at {field}")
    reference_state_metadata = reference.get("state", {})
    candidate_state_metadata = candidate.get("state", {})
    if reference_state_metadata.get(
        "amplitude_convention"
    ) != candidate_state_metadata.get("amplitude_convention"):
        raise ValueError("complete states use different amplitude conventions")
    reference_state_path, reference_state = _resolve_complete_state(reference)
    candidate_state_path, candidate_state = _resolve_complete_state(candidate)
    started = time.perf_counter()
    metric = normalized_fidelity_chunked(
        reference_state,
        candidate_state,
        chunk_amplitudes=chunk_amplitudes,
    )
    elapsed = time.perf_counter() - started
    metric.update(
        {
            "name": "normalized_complete_pure_state_fidelity",
            "formula": (
                "|<psi_reference|psi_candidate>|^2/"
                "(<psi_reference|psi_reference>*"
                "<psi_candidate|psi_candidate>)"
            ),
            "source": "Evenbly 2018, Section V, Equation (12), PDF page 6",
            "value_kind": "exact_complete_vector_complex128_numerical",
            "classification": _classify(
                metric["normalized_squared_overlap"]
            ),
        }
    )
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "verdict_scope": "per_point_nonterminal_metric_only",
        "claim_boundary": reference["claim_boundary"],
        "fixture": {
            field: reference_fixture[field] for field in identity_fields
        },
        "reference": {
            "summary_path": str(reference_summary_path.resolve()),
            "summary_file_sha256": _file_sha256(reference_summary_path),
            "state_path": str(reference_state_path.resolve()),
            "state_file_sha256": reference["state"]["file_sha256"],
            "summary_schema": reference["schema"],
        },
        "candidate": {
            "summary_path": str(candidate_summary_path.resolve()),
            "summary_file_sha256": _file_sha256(candidate_summary_path),
            "state_path": str(candidate_state_path.resolve()),
            "state_file_sha256": candidate["state"]["file_sha256"],
            "summary_schema": candidate["schema"],
            "diagnostics": candidate.get("diagnostics"),
        },
        "metric": metric,
        "bands": {
            "useful_minimum": 0.99,
            "marginal_minimum": 0.95,
            "self_infidelity_maximum": 1e-12,
        },
        "runtime": {
            "elapsed_seconds": elapsed,
            "python_peak_rss_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-summary", type=Path, required=True)
    parser.add_argument("--candidate-summary", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument(
        "--chunk-amplitudes",
        type=int,
        default=1 << 20,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    committed_inputs = _verify_committed_inputs()
    result = compare_summaries(
        args.reference_summary,
        args.candidate_summary,
        chunk_amplitudes=args.chunk_amplitudes,
    )
    result["provenance"] = {
        "git_head": committed_inputs["git_head"],
        "committed_input_sha256": committed_inputs["sha256"],
        "worker_path": str(Path(__file__).resolve()),
        "worker_sha256": _file_sha256(Path(__file__).resolve()),
    }
    _atomic_write_json(args.output_json, result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

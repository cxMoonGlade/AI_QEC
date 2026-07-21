#!/usr/bin/env python3
"""Compare public GPU MCWF X/Z Records with isolated CPU QuTiP MCWF."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping

import torch

from error_coupling_simulator.frontend import (
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    Axis1LocalLindbladContextSpec,
    CircuitBuilder,
    axis1_carrier_execution_manifest,
    axis1_mcwf_mps_state_record_execution_manifest,
    circuit_ir_to_substep_schedule,
)
from error_coupling_simulator.numerics import NUMERICAL_ZERO

import qutip_mcwf_xz_protocol as protocol


SCHEMA = "ai_qec.external_baseline.qutip_project_mcwf_xz_comparison.v3"
WORKER_SCHEMA = (
    "error_coupling_simulator.external_baseline.qutip_mcwf_xz_record.v3"
)
WORKER_ENVELOPE_SCHEMA = "ai_qec.external_baseline.qutip_mcwf_xz_worker_envelope.v1"
EXPECTED_PROJECT_ENVIRONMENT = "ecs"
EXPECTED_QUTIP_COMMIT = "f343ee3ca273a4ea19f6bebbd6f563354ea309ed"
EXPECTED_QUTIP_VERSION = "5.4.0.dev0+f343ee3"
EXPECTED_QUTIP_TREE = "f09c4126447d8d77b66f2da39dca759a606346dd"
REPO = Path(__file__).resolve().parents[2]
QUTIP_WORKER = Path(__file__).with_name("qutip_mcwf_xz_worker.py")
QUTIP_BASELINE_REPO = REPO / "external" / "baselines" / "qutip"
# Authoritative per-platform QuTiP baseline locks. Each entry is
# (repository-relative lock filename, expected lock "platform" field). The
# conformance gate compares the FULL ordered conda explicit sha256 URL list, so
# an execution machine without a registered lock fails closed here.
QUTIP_BASELINE_LOCKS_BY_MACHINE = {
    "x86_64": ("baseline-environment-qutip-linux-64.lock.json", "linux-64"),
    "aarch64": ("baseline-environment-qutip-linux-aarch64.lock.json", "linux-aarch64"),
}


def _qutip_baseline_lock_for_machine() -> tuple[Path, str]:
    machine = platform.machine()
    try:
        name, lock_platform = QUTIP_BASELINE_LOCKS_BY_MACHINE[machine]
    except KeyError:
        raise RuntimeError(
            "no authoritative QuTiP baseline lock is registered for machine "
            f"{machine!r}; registered machines: "
            f"{sorted(QUTIP_BASELINE_LOCKS_BY_MACHINE)}"
        ) from None
    return REPO / name, lock_platform


QUTIP_BASELINE_LOCK, QUTIP_BASELINE_LOCK_PLATFORM = _qutip_baseline_lock_for_machine()
PROJECT_EVIDENCE_SOURCE_PATHS = (
    "baseline-environment-qutip-linux-64.lock.json",
    "baseline-environment-qutip-linux-aarch64.lock.json",
    "scripts/external_baselines/mcwf_xz_dense_worker.py",
    "scripts/external_baselines/qutip_mcwf_xz_protocol.py",
    "scripts/external_baselines/qutip_mcwf_xz_worker.py",
    "scripts/external_baselines/run_mcwf_xz_fixture_family_comparison.py",
    "scripts/external_baselines/run_qutip_mcwf_xz_comparison.py",
    "scripts/external_baselines/fixtures/mcwf_xz_comparison_registry.json",
    "scripts/external_baselines/fixtures/qutip_mcwf_xz_two_qubit_pure_dephasing.json",
    "scripts/external_baselines/fixtures/qutip_mcwf_xz_two_qubit_t1.json",
    "scripts/external_baselines/fixtures/qutip_mcwf_xz_two_qubit_thermal.json",
    "tests/test_axis1_mcwf_convergence.py",
    "tests/test_external_mcwf_xz_fixture_family.py",
    "tests/test_external_qutip_mcwf_xz_comparison.py",
)
PROJECT_ENVIRONMENT_LOCK_PATHS = (
    "core-environment-cu130.lock",
    "uv.lock",
)
SELECTED_QUTIP_SOURCES = (
    "qutip/__init__.py",
    "qutip/solver/mcsolve.py",
    "qutip/solver/multitrajresult.py",
)
SANITIZED_INHERITED_ENVIRONMENT_KEYS = (
    "CONDA_DEFAULT_ENV",
    "CONDA_EXE",
    "CONDA_PREFIX",
    "CONDA_PROMPT_MODIFIER",
    "CONDA_PYTHON_EXE",
    "CONDA_SHLVL",
    "CUDA_HOME",
    "LD_LIBRARY_PATH",
    "VIRTUAL_ENV",
    "_CE_CONDA",
    "_CE_M",
)
EXPECTED_QUTIP_SOLVER_OPTIONS = {
    "map": "serial",
    "progress_bar": False,
    "store_final_state": True,
    "keep_runs_results": True,
    "improved_sampling": False,
    "method": "vern7",
    "atol": 1.0e-10,
    "rtol": 1.0e-8,
    "nsteps": 10_000,
    "mc_corr_eps": 1.0e-12,
    "norm_steps": 50,
    "norm_t_tol": 1.0e-8,
    "norm_tol": 1.0e-8,
    "norm_min_step": 0.01,
}

_WORKER_TOP_LEVEL_FIELDS = {
    "all_checks_passed",
    "analytic_reference",
    "atomic_publication",
    "claim_boundary",
    "content_hash",
    "fixture",
    "numerical_provenance",
    "record",
    "reset_checks",
    "runtime_provenance",
    "schema",
    "solver",
    "statistical_limitations",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_at(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git(*arguments: str) -> str:
    return _git_at(REPO, *arguments)


def _project_source_provenance() -> dict[str, Any]:
    commit = _git("rev-parse", "HEAD")
    if len(commit) not in (40, 64) or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise RuntimeError("project comparator requires a full hexadecimal Git commit")
    tracked = set(
        _git(
            "ls-files",
            "--error-unmatch",
            "--",
            *PROJECT_EVIDENCE_SOURCE_PATHS,
        ).splitlines()
    )
    if tracked != set(PROJECT_EVIDENCE_SOURCE_PATHS):
        raise RuntimeError("project evidence source inventory is not fully tracked")
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError(
            "project evidence requires a clean Git worktree including untracked files"
        )
    identities = {
        relative: {
            "path": relative,
            "sha256": _sha256_file(REPO / relative),
        }
        for relative in PROJECT_EVIDENCE_SOURCE_PATHS
    }
    return {
        "repo_commit": commit,
        "git_object_format": "sha1" if len(commit) == 40 else "sha256",
        "status_scope": "whole_worktree_including_untracked_not_ignored",
        "git_status_porcelain": "",
        "whole_worktree_clean_including_untracked": True,
        "selected_sources_clean_at_repo_commit": True,
        "selected_sources": identities,
    }


def _qutip_baseline_lock_provenance() -> dict[str, Any]:
    if not QUTIP_BASELINE_LOCK.is_file():
        raise RuntimeError("authoritative QuTiP baseline lock is missing")
    lock = _strict_json_loads(QUTIP_BASELINE_LOCK.read_bytes())
    if set(lock) != {
        "conda_explicit_sha256_urls",
        "environment_name",
        "platform",
        "python_version",
        "qutip_vcs",
        "recreation_sequence",
        "schema",
    } or lock.get("schema") != (
        "error_coupling_simulator.environment_lock.qutip_baseline.v1"
    ):
        raise RuntimeError("authoritative QuTiP baseline lock schema drifted")
    if lock.get("environment_name") != "ecs-baseline-qutip":
        raise RuntimeError("authoritative QuTiP baseline environment name drifted")
    expected_urls = lock.get("conda_explicit_sha256_urls")
    if not isinstance(expected_urls, list) or not expected_urls:
        raise RuntimeError("authoritative QuTiP conda package lock is empty")
    if len(set(expected_urls)) != len(expected_urls) or any(
        not isinstance(value, str)
        or not value.startswith("https://")
        or len(value.rsplit("#", 1)) != 2
        or len(value.rsplit("#", 1)[1]) != 64
        or any(character not in "0123456789abcdef" for character in value.rsplit("#", 1)[1])
        for value in expected_urls
    ):
        raise RuntimeError("authoritative QuTiP conda package lock is malformed")

    conda = shutil.which("conda")
    if conda is None:
        raise RuntimeError("conda is required for QuTiP baseline lock conformance")
    completed = subprocess.run(
        [conda, "list", "-n", "ecs-baseline-qutip", "--explicit", "--sha256"],
        cwd=REPO,
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        check=True,
        capture_output=True,
        text=True,
        timeout=120.0,
    )
    observed_urls = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip().startswith("https://")
    ]
    if observed_urls != expected_urls:
        raise RuntimeError("ecs-baseline-qutip conda packages drifted from lock")

    baseline_python = _resolve_named_conda_python(
        conda,
        environment_name="ecs-baseline-qutip",
    )
    identity_process = subprocess.run(
        [
            str(baseline_python),
            "-c",
            (
                "import importlib.metadata as m,json,platform;"
                "d=m.distribution('qutip');"
                "print(json.dumps({'python_version':platform.python_version(),"
                "'qutip_version':d.version,'direct_url':json.loads("
                "d.read_text('direct_url.json'))},sort_keys=True))"
            ),
        ],
        cwd=REPO,
        env=_worker_launch_environment(
            os.environ,
            baseline_python=baseline_python,
        ),
        check=True,
        capture_output=True,
        text=True,
        timeout=120.0,
    )
    installed = _strict_json_loads(identity_process.stdout.encode("utf-8"))
    qutip_vcs = lock.get("qutip_vcs")
    if not isinstance(qutip_vcs, Mapping) or set(qutip_vcs) != {
        "commit",
        "installed_distribution_version",
        "source_relative_to_repository",
        "tree",
    }:
        raise RuntimeError("authoritative QuTiP VCS lock is malformed")
    direct_url = installed.get("direct_url")
    vcs_info = direct_url.get("vcs_info") if isinstance(direct_url, Mapping) else None
    observed_commit = _git_at(QUTIP_BASELINE_REPO, "rev-parse", "HEAD")
    observed_tree = _git_at(QUTIP_BASELINE_REPO, "rev-parse", "HEAD^{tree}")
    if (
        lock.get("platform") != QUTIP_BASELINE_LOCK_PLATFORM
        or installed.get("python_version") != lock.get("python_version")
        or qutip_vcs.get("source_relative_to_repository")
        != "external/baselines/qutip"
        or qutip_vcs.get("commit") != EXPECTED_QUTIP_COMMIT
        or qutip_vcs.get("tree") != EXPECTED_QUTIP_TREE
        or qutip_vcs.get("installed_distribution_version")
        != EXPECTED_QUTIP_VERSION
        or installed.get("qutip_version") != EXPECTED_QUTIP_VERSION
        or not isinstance(direct_url, Mapping)
        or direct_url.get("url") != QUTIP_BASELINE_REPO.resolve().as_uri()
        or not isinstance(vcs_info, Mapping)
        or vcs_info.get("vcs") != "git"
        or vcs_info.get("commit_id") != EXPECTED_QUTIP_COMMIT
        or vcs_info.get("requested_revision") != EXPECTED_QUTIP_COMMIT
        or observed_commit != EXPECTED_QUTIP_COMMIT
        or observed_tree != EXPECTED_QUTIP_TREE
        or _git_at(
            QUTIP_BASELINE_REPO,
            "status",
            "--porcelain",
            "--untracked-files=all",
        )
        != ""
    ):
        raise RuntimeError("ecs-baseline-qutip VCS/install identity drifted from lock")
    return {
        "path": str(QUTIP_BASELINE_LOCK.relative_to(REPO)),
        "sha256": _sha256_file(QUTIP_BASELINE_LOCK),
        "schema": lock["schema"],
        "environment_name": lock["environment_name"],
        "conda_explicit_package_count": len(expected_urls),
        "conda_executable": str(Path(conda).resolve()),
        "conda_executable_sha256": _sha256_file(Path(conda).resolve()),
        "python_executable": str(baseline_python),
        "python_version": installed["python_version"],
        "qutip_commit": observed_commit,
        "qutip_tree": observed_tree,
        "qutip_version": installed["qutip_version"],
        "authoritative_lock_conformance_checked": True,
        "claims_reproducible_environment": True,
    }


def _environment_lock_provenance() -> dict[str, Any]:
    lock_hashes: dict[str, str] = {}
    for relative in PROJECT_ENVIRONMENT_LOCK_PATHS:
        path = REPO / relative
        if not path.is_file():
            raise RuntimeError(f"required project environment lock is missing: {relative}")
        lock_hashes[relative] = _sha256_file(path)
    baseline = _qutip_baseline_lock_provenance()
    return {
        "project_environment_locks": lock_hashes,
        "core_lock_scope": "project_ecs_only_not_qutip_baseline",
        "uv_lock_scope": "project_ecs_only_not_qutip_baseline",
        "baseline_environment": "ecs-baseline-qutip",
        "baseline_environment_lock": baseline,
        "authoritative_lock_conformance_checked": True,
        "claims_qutip_baseline_lock_conformance": True,
        "claims_reproducible_environment": True,
        "limitation": None,
    }


def _project_runtime_provenance() -> dict[str, Any]:
    if "PYTHONPATH" in os.environ:
        raise RuntimeError("project comparator refuses caller-provided PYTHONPATH")
    prefix = Path(sys.prefix).resolve()
    executable = Path(sys.executable).resolve()
    if prefix.name != EXPECTED_PROJECT_ENVIRONMENT or not executable.is_relative_to(prefix):
        raise RuntimeError(
            f"project comparator must run inside {EXPECTED_PROJECT_ENVIRONMENT!r}"
        )
    source_provenance = _project_source_provenance()
    environment_locks = _environment_lock_provenance()
    if not torch.cuda.is_available():
        raise RuntimeError("project MCWF comparator requires an in-process CUDA device")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible in (None, ""):
        raise RuntimeError("project MCWF comparator requires one pinned visible GPU")
    return {
        "environment": EXPECTED_PROJECT_ENVIRONMENT,
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "python_prefix": str(prefix),
        "python_executable": str(executable),
        "cuda_visible_devices": visible,
        "cuda_device_count": int(torch.cuda.device_count()),
        "cuda_device_name": torch.cuda.get_device_name(0),
        "repo_commit": source_provenance["repo_commit"],
        "adapter_path": str(Path(__file__).resolve().relative_to(REPO)),
        "adapter_sha256": _sha256_file(Path(__file__).resolve()),
        "fixture_protocol_sha256": _sha256_file(
            Path(__file__).with_name("qutip_mcwf_xz_protocol.py")
        ),
        "qutip_worker_sha256": _sha256_file(QUTIP_WORKER),
        "source_provenance": source_provenance,
        "environment_lock_provenance": environment_locks,
        "pythonpath_env": None,
    }


def _schedule_from_fixture(fixture: dict[str, Any]):
    builder = CircuitBuilder(num_qubits=int(fixture["num_qubits"]))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=float(fixture["gamma_phi_per_ns"]),
            gamma_1_per_ns=float(fixture["gamma_1_per_ns"]),
            include_thermal_excitation=(
                float(fixture["gamma_up_per_ns"]) > 0.0
            ),
            gamma_up_per_ns=float(fixture["gamma_up_per_ns"]),
            gamma_readout_phi_per_ns=0.0,
        )
    )
    duration = float(fixture["evolution_duration_ns"])
    builder.idle((0, 1), duration_ns=duration)
    builder.tick()
    builder.measure(0, key="mx_before", basis="X", reset=True)
    builder.measure(1, key="mz_before", basis="Z", reset=True)
    builder.tick()
    builder.idle((0, 1), duration_ns=duration)
    builder.tick()
    builder.measure(0, key="mx_after", basis="X", reset=False)
    builder.measure(1, key="mz_after", basis="Z", reset=False)
    return circuit_ir_to_substep_schedule(builder.build())


def _strict_binary_histogram(
    rows: Any,
    counts: Any,
    probabilities: Any,
    *,
    trajectory_count: int,
    label: str,
) -> dict[str, Any]:
    if not (
        type(rows) is list
        and type(counts) is list
        and type(probabilities) is list
        and rows
        and len(rows) == len(counts) == len(probabilities)
    ):
        raise RuntimeError(f"{label} histogram shape drifted")
    if any(
        type(row) is not list
        or len(row) != 4
        or any(type(value) is not int or value not in (0, 1) for value in row)
        for row in rows
    ):
        raise RuntimeError(f"{label} bit domain drifted")
    normalized_rows = [tuple(row) for row in rows]
    if normalized_rows != sorted(set(normalized_rows)):
        raise RuntimeError(f"{label} support drifted")
    if any(type(value) is not int or value <= 0 for value in counts):
        raise RuntimeError(f"{label} counts drifted")
    if sum(counts) != trajectory_count:
        raise RuntimeError(f"{label} counts drifted")
    if any(
        type(value) not in (int, float)
        or not math.isfinite(float(value))
        or float(value) < 0.0
        for value in probabilities
    ):
        raise RuntimeError(f"{label} probabilities drifted")
    for count, probability in zip(counts, probabilities, strict=True):
        if abs(float(probability) - count / trajectory_count) > NUMERICAL_ZERO:
            raise RuntimeError(f"{label} probability/count identity drifted")
    return {
        "records": [list(row) for row in normalized_rows],
        "counts": list(counts),
        "probabilities": [float(value) for value in probabilities],
    }


def _validate_record_payload(
    payload: dict[str, Any], fixture: dict[str, Any], *, label_prefix: str
) -> dict[str, Any]:
    for field in (
        "measurement_keys",
        "measurement_targets",
        "measurement_bases",
        "reset_after",
    ):
        if not _json_type_exact_equal(payload.get(field), fixture[field]):
            raise RuntimeError(f"{label_prefix} {field} drifted from neutral fixture")
    records = payload.get("measurement_records")
    counts = payload.get("record_counts")
    probabilities = payload.get("record_probabilities")
    trajectory_count = int(fixture["trajectory_count"])
    return _strict_binary_histogram(
        records,
        counts,
        probabilities,
        trajectory_count=trajectory_count,
        label=f"{label_prefix} Record",
    )


def _validate_label_payload(
    payload: dict[str, Any], fixture: dict[str, Any]
) -> dict[str, Any]:
    records = payload.get("level_records")
    counts = payload.get("level_record_counts")
    probabilities = payload.get("level_record_probabilities")
    trajectory_count = int(fixture["trajectory_count"])
    return _strict_binary_histogram(
        records,
        counts,
        probabilities,
        trajectory_count=trajectory_count,
        label="direct MCWF label",
    )


def _law(histogram: dict[str, Any]) -> dict[tuple[int, ...], float]:
    return {
        tuple(row): float(probability)
        for row, probability in zip(
            histogram["records"], histogram["probabilities"], strict=True
        )
    }


def _qutip_histogram(report: dict[str, Any], kind: str) -> dict[str, Any]:
    record = report["record"]
    return {
        "records": record[f"{kind}_records"],
        "counts": record[f"{kind}_counts"],
        "probabilities": record[f"{kind}_probabilities"],
    }


def _require_exact_keys(
    payload: Any,
    expected: set[str] | frozenset[str],
    *,
    label: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    observed = set(payload)
    if observed != set(expected):
        missing = sorted(set(expected) - observed)
        additional = sorted(observed - set(expected))
        raise RuntimeError(
            f"{label} fields drifted: missing={missing!r}, additional={additional!r}"
        )
    return payload


def _strict_json_loads(payload: bytes) -> dict[str, Any]:
    def reject_constant(value: str) -> Any:
        raise RuntimeError(f"isolated QuTiP worker emitted non-finite JSON {value}")

    def finite_float(value: str) -> float:
        decoded = float(value)
        if not math.isfinite(decoded):
            raise RuntimeError(
                f"isolated QuTiP worker emitted non-finite JSON {value}"
            )
        return decoded

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        decoded: dict[str, Any] = {}
        for key, value in pairs:
            if key in decoded:
                raise RuntimeError(
                    f"isolated QuTiP worker emitted duplicate JSON key {key!r}"
                )
            decoded[key] = value
        return decoded

    try:
        decoded = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
    except UnicodeDecodeError as exc:
        raise RuntimeError("isolated QuTiP worker emitted non-UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise RuntimeError("isolated QuTiP worker report must be a JSON object")
    return decoded


def _json_type_exact_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(
            _json_type_exact_equal(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            _json_type_exact_equal(left_value, right_value)
            for left_value, right_value in zip(left, right, strict=True)
        )
    return bool(left == right)


def _validate_worker_histogram(
    record: dict[str, Any],
    *,
    kind: str,
    trajectory_count: int,
) -> dict[str, Any]:
    rows = record[f"{kind}_records"]
    counts = record[f"{kind}_counts"]
    probabilities = record[f"{kind}_probabilities"]
    return _strict_binary_histogram(
        rows,
        counts,
        probabilities,
        trajectory_count=trajectory_count,
        label=f"isolated QuTiP {kind}",
    )


def _validate_isolated_qutip_report(
    report: dict[str, Any],
    *,
    fixture: dict[str, Any],
    fixture_path: Path,
) -> None:
    _require_exact_keys(report, _WORKER_TOP_LEVEL_FIELDS, label="worker report")
    if report["schema"] != WORKER_SCHEMA:
        raise RuntimeError("isolated QuTiP worker schema drifted")
    if report["all_checks_passed"] is not True:
        raise RuntimeError("isolated QuTiP worker did not pass its own gates")
    if report["content_hash"] != protocol.canonical_content_hash(report):
        raise RuntimeError("isolated QuTiP worker content hash mismatch")
    if report["claim_boundary"] != fixture["claim_boundary"]:
        raise RuntimeError("isolated QuTiP claim boundary drifted")

    fixture_record = _require_exact_keys(
        report["fixture"],
        {
            "collapse_terms",
            "comparison_registry_sha256",
            "evolution_segments_ns",
            "id",
            "initial_levels",
            "path",
            "schema",
            "sha256",
        },
        label="worker fixture",
    )
    fixture_expectations = {
        "collapse_terms": fixture["collapse_terms"],
        "comparison_registry_sha256": protocol.EXPECTED_REGISTRY_SHA256,
        "evolution_segments_ns": fixture["evolution_segments_ns"],
        "id": fixture["fixture_id"],
        "initial_levels": fixture["initial_levels"],
        "path": str(fixture_path.resolve()),
        "schema": fixture["schema"],
        "sha256": protocol.fixture_sha256(fixture_path),
    }
    if not _json_type_exact_equal(fixture_record, fixture_expectations):
        raise RuntimeError("isolated QuTiP fixture binding drifted")

    runtime = _require_exact_keys(
        report["runtime_provenance"],
        {
            "baseline_repo",
            "cache_isolation",
            "clone_pristine",
            "cuda_visible_devices",
            "environment",
            "expected_commit",
            "installed_distribution",
            "numpy_version",
            "observed_commit",
            "observed_tree",
            "project_modules_imported",
            "project_package_find_spec",
            "protocol_sha256",
            "python_executable",
            "python_implementation",
            "python_prefix",
            "python_version",
            "pythonpath_env",
            "qutip_module_file",
            "qutip_version",
            "resolved_sys_path",
            "sanitized_parent_environment",
            "scipy_version",
            "worker_sha256",
        },
        label="worker runtime provenance",
    )
    current_qutip_commit = _git_at(QUTIP_BASELINE_REPO, "rev-parse", "HEAD")
    current_qutip_tree = _git_at(
        QUTIP_BASELINE_REPO, "rev-parse", "HEAD^{tree}"
    )
    current_qutip_dirty = _git_at(
        QUTIP_BASELINE_REPO,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    python_prefix = Path(str(runtime["python_prefix"])).resolve()
    python_executable = Path(str(runtime["python_executable"])).resolve()
    qutip_module_file = Path(str(runtime["qutip_module_file"])).resolve()
    if (
        runtime["environment"] != "ecs-baseline-qutip"
        or runtime["cuda_visible_devices"] != ""
        or runtime["clone_pristine"] is not True
        or runtime["baseline_repo"] != "external/baselines/qutip"
        or runtime["expected_commit"] != EXPECTED_QUTIP_COMMIT
        or runtime["observed_commit"] != EXPECTED_QUTIP_COMMIT
        or current_qutip_commit != EXPECTED_QUTIP_COMMIT
        or runtime["observed_tree"] != current_qutip_tree
        or current_qutip_dirty != ""
        or runtime["qutip_version"] != EXPECTED_QUTIP_VERSION
        or python_prefix.name != "ecs-baseline-qutip"
        or not python_executable.is_relative_to(python_prefix)
        or not qutip_module_file.is_relative_to(python_prefix)
        or runtime["project_modules_imported"] != []
        or runtime["project_package_find_spec"] is not None
        or runtime["pythonpath_env"] is not None
    ):
        raise RuntimeError("isolated QuTiP runtime isolation drifted")
    cache_isolation = _require_exact_keys(
        runtime["cache_isolation"],
        {
            "all_cache_roots_exist_and_are_nonsymlink_directories",
            "common_private_root",
            "common_private_root_mode_octal",
            "home",
            "matplotlib_config",
            "private_root_owner_only",
            "xdg_cache_home",
        },
        label="worker cache isolation",
    )
    private_root = Path(str(cache_isolation["common_private_root"]))
    if (
        cache_isolation["all_cache_roots_exist_and_are_nonsymlink_directories"]
        is not True
        or cache_isolation["private_root_owner_only"] is not True
        or cache_isolation["common_private_root_mode_octal"] != "700"
        or Path(str(cache_isolation["home"])).parent != private_root
        or Path(str(cache_isolation["xdg_cache_home"])).parent != private_root
        or Path(str(cache_isolation["matplotlib_config"])).parent != private_root
        or Path(str(cache_isolation["home"])).name != "home"
        or Path(str(cache_isolation["xdg_cache_home"])).name != "xdg-cache"
        or Path(str(cache_isolation["matplotlib_config"])).name != "mpl-config"
    ):
        raise RuntimeError("isolated QuTiP cache isolation drifted")
    sanitized = _require_exact_keys(
        runtime["sanitized_parent_environment"],
        set(SANITIZED_INHERITED_ENVIRONMENT_KEYS),
        label="worker sanitized parent environment",
    )
    if any(value is not None for value in sanitized.values()):
        raise RuntimeError("isolated QuTiP inherited environment was not sanitized")
    if runtime["worker_sha256"] != _sha256_file(QUTIP_WORKER):
        raise RuntimeError("isolated QuTiP worker source hash mismatch")
    if runtime["protocol_sha256"] != _sha256_file(
        Path(__file__).with_name("qutip_mcwf_xz_protocol.py")
    ):
        raise RuntimeError("isolated QuTiP protocol source hash mismatch")
    installed = _require_exact_keys(
        runtime["installed_distribution"],
        {
            "content_identity",
            "direct_url",
            "name",
            "selected_clone_sha256",
            "selected_installed_sha256",
            "selected_sources_match_clone",
            "version",
        },
        label="worker installed distribution",
    )
    if (
        installed["selected_sources_match_clone"] is not True
        or installed["name"].lower() != "qutip"
        or installed["version"] != EXPECTED_QUTIP_VERSION
    ):
        raise RuntimeError("isolated QuTiP selected source identity drifted")
    direct_url = _require_exact_keys(
        installed["direct_url"],
        {"url", "vcs_info"},
        label="worker installed distribution direct URL",
    )
    vcs_info = _require_exact_keys(
        direct_url["vcs_info"],
        {"commit_id", "requested_revision", "vcs"},
        label="worker installed distribution VCS info",
    )
    expected_baseline_url = QUTIP_BASELINE_REPO.resolve().as_uri()
    if (
        direct_url["url"] != expected_baseline_url
        or vcs_info["vcs"] != "git"
        or vcs_info["commit_id"] != runtime["observed_commit"]
        or vcs_info["requested_revision"] != runtime["observed_commit"]
    ):
        raise RuntimeError("isolated QuTiP installed direct URL drifted")
    expected_selected_sources = set(SELECTED_QUTIP_SOURCES)
    installed_hashes = _require_exact_keys(
        installed["selected_installed_sha256"],
        expected_selected_sources,
        label="worker selected installed sources",
    )
    clone_hashes = _require_exact_keys(
        installed["selected_clone_sha256"],
        expected_selected_sources,
        label="worker selected clone sources",
    )
    expected_clone_hashes = {
        relative: _sha256_file(QUTIP_BASELINE_REPO / relative)
        for relative in SELECTED_QUTIP_SOURCES
    }
    if installed_hashes != clone_hashes or clone_hashes != expected_clone_hashes:
        raise RuntimeError("isolated QuTiP selected source hashes diverged")
    identity = _require_exact_keys(
        installed["content_identity"],
        {"file_count", "sha256"},
        label="worker installed distribution content identity",
    )
    if (
        isinstance(identity["file_count"], bool)
        or not isinstance(identity["file_count"], int)
        or identity["file_count"] <= 0
        or not isinstance(identity["sha256"], str)
        or len(identity["sha256"]) != 64
    ):
        raise RuntimeError("isolated QuTiP installed distribution identity drifted")

    numerical = _require_exact_keys(
        report["numerical_provenance"],
        {
            "environment_lock_status",
            "observed_final_state_dtypes",
            "observed_probability_array_dtype",
            "precision_purpose",
            "probability_dtype",
            "repository_environment_lock",
            "state_dtype",
        },
        label="worker numerical provenance",
    )
    if (
        numerical["state_dtype"] != "complex128"
        or numerical["observed_final_state_dtypes"] != ["complex128"]
        or numerical["probability_dtype"] != "float64"
        or numerical["observed_probability_array_dtype"] != "float64"
        or numerical["repository_environment_lock"] is not None
        or numerical["environment_lock_status"]
        != "not_available_runtime_identity_recorded"
        or numerical["precision_purpose"]
        != "independent continuous-time MCWF trajectory and X/Z Record-law differential"
    ):
        raise RuntimeError("isolated QuTiP numerical provenance drifted")

    trajectory_count = int(fixture["trajectory_count"])
    solver = _require_exact_keys(
        report["solver"],
        {
            "collapse_operator_count",
            "device",
            "first_interval_jump_count",
            "integrator_options",
            "name",
            "retained_final_state_count_per_interval",
            "second_interval_jump_count",
            "total_jump_count",
            "trajectory_count",
            "unravelling",
        },
        label="worker solver",
    )
    _require_exact_keys(
        solver["integrator_options"],
        set(EXPECTED_QUTIP_SOLVER_OPTIONS),
        label="worker solver options",
    )
    solver_count_fields = (
        "collapse_operator_count",
        "first_interval_jump_count",
        "retained_final_state_count_per_interval",
        "second_interval_jump_count",
        "total_jump_count",
        "trajectory_count",
    )
    if any(
        isinstance(solver[field], bool) or not isinstance(solver[field], int)
        for field in solver_count_fields
    ):
        raise RuntimeError("isolated QuTiP solver count types drifted")
    if (
        solver["name"] != "qutip.mcsolve"
        or solver["unravelling"]
        != "continuous_time_monte_carlo_wave_function"
        or solver["device"] != "cpu"
        or solver["trajectory_count"] != trajectory_count
        or solver["retained_final_state_count_per_interval"] != trajectory_count
        or solver["collapse_operator_count"] != len(fixture["collapse_terms"])
        or solver["first_interval_jump_count"] < 0
        or solver["second_interval_jump_count"] < 0
        or not _json_type_exact_equal(
            solver["integrator_options"], EXPECTED_QUTIP_SOLVER_OPTIONS
        )
        or solver["total_jump_count"]
        != solver["first_interval_jump_count"] + solver["second_interval_jump_count"]
        or solver["total_jump_count"] <= 0
    ):
        raise RuntimeError("isolated QuTiP solver record drifted")

    record = _require_exact_keys(
        report["record"],
        {
            "binary_counts",
            "binary_probabilities",
            "binary_records",
            "label_counts",
            "label_probabilities",
            "label_records",
            "measurement_bases",
            "measurement_keys",
            "measurement_targets",
            "qubit_label_to_binary_mapping",
            "reset_after",
        },
        label="worker record",
    )
    for field in (
        "measurement_bases",
        "measurement_keys",
        "measurement_targets",
        "reset_after",
    ):
        if not _json_type_exact_equal(record[field], fixture[field]):
            raise RuntimeError(f"isolated QuTiP Record {field} drifted")
    labels = _validate_worker_histogram(
        record, kind="label", trajectory_count=trajectory_count
    )
    binary = _validate_worker_histogram(
        record, kind="binary", trajectory_count=trajectory_count
    )
    if labels != binary or record["qubit_label_to_binary_mapping"] != (
        "identity_0_to_0_1_to_1"
    ):
        raise RuntimeError("isolated QuTiP label/binary identity drifted")

    reset = _require_exact_keys(
        report["reset_checks"],
        {
            "X_reset_state",
            "Z_reset_state",
            "max_post_reset_state_l2",
            "numerical_zero",
            "passed",
        },
        label="worker reset checks",
    )
    reset_residual = float(reset["max_post_reset_state_l2"])
    if (
        reset["X_reset_state"] != "|+>"
        or reset["Z_reset_state"] != "|0>"
        or reset["numerical_zero"] != fixture["numerical_zero"]
        or reset["passed"] is not True
        or not math.isfinite(reset_residual)
        or reset_residual < 0.0
        or reset_residual > float(fixture["numerical_zero"])
    ):
        raise RuntimeError("isolated QuTiP reset evidence drifted")

    analytic = _require_exact_keys(
        report["analytic_reference"],
        {
            "bonferroni_component_alpha",
            "derivation",
            "joint_tv",
            "nonverdict_directed_marginal_tv",
            "registered_statistic",
            "registry_entry_count",
        },
        label="worker analytic reference",
    )
    expected_statistic = {
        "two_qubit_t1_ordered_xz_reset": "f1.qutip_dense_joint",
        "two_qubit_pure_dephasing_ordered_xz_reset": "f2.qutip_dense_joint",
        "two_qubit_thermal_ordered_xz_reset": "f3.qutip_dense_joint",
    }[fixture["fixture_id"]]
    if analytic["derivation"] != (
        "closed-form local Lindblad population/coherence evolution composed "
        "with the ordered selective measurement and reset maps"
    ) or analytic["registered_statistic"] != expected_statistic:
        raise RuntimeError("isolated QuTiP analytic comparison family drifted")
    if analytic["registry_entry_count"] != 15:
        raise RuntimeError("isolated QuTiP registry cardinality drifted")
    expected_worker_alpha = float(fixture["comparison_family_alpha"]) / 15.0
    if not math.isclose(
        float(analytic["bonferroni_component_alpha"]),
        expected_worker_alpha,
        rel_tol=0.0,
        abs_tol=NUMERICAL_ZERO,
    ):
        raise RuntimeError("isolated QuTiP worker Bonferroni alpha drifted")
    analytic_law = protocol.analytic_binary_distribution(fixture)
    observed_binary_law = _law(binary)
    comparison = _require_exact_keys(
        analytic["joint_tv"],
        {
            "alpha",
            "alphabet_size",
            "gate_rule",
            "passed",
            "sample_count",
            "schema",
            "total_variation",
            "tv_radius",
        },
        label="worker joint_tv",
    )
    recomputed_tv = protocol.total_variation(observed_binary_law, analytic_law)
    recomputed_radius = protocol.multinomial_tv_radius(
        sample_count=trajectory_count,
        alphabet_size=16,
        alpha=expected_worker_alpha,
    )
    if (
        comparison["schema"]
        != (
            "error_coupling_simulator.external_baseline."
            "one_sample_multinomial_tv.v1"
        )
        or comparison["sample_count"] != trajectory_count
        or comparison["alphabet_size"] != 16
        or not math.isclose(
            float(comparison["alpha"]),
            expected_worker_alpha,
            rel_tol=0.0,
            abs_tol=NUMERICAL_ZERO,
        )
        or not math.isclose(
            float(comparison["total_variation"]),
            recomputed_tv,
            rel_tol=0.0,
            abs_tol=NUMERICAL_ZERO,
        )
        or not math.isclose(
            float(comparison["tv_radius"]),
            recomputed_radius,
            rel_tol=0.0,
            abs_tol=NUMERICAL_ZERO,
        )
        or comparison["gate_rule"] != "observed_total_variation <= tv_radius"
        or comparison["passed"] is not bool(recomputed_tv <= recomputed_radius)
        or comparison["passed"] is not True
    ):
        raise RuntimeError("isolated QuTiP joint evidence drifted")
    marginal_diagnostics = _require_exact_keys(
        analytic["nonverdict_directed_marginal_tv"],
        set(protocol.EXPECTED_DIRECTED_MARGINALS[fixture["fixture_id"]]),
        label="worker nonverdict directed marginals",
    )
    for key, observed_tv in marginal_diagnostics.items():
        column = fixture["measurement_keys"].index(key)
        recomputed = protocol.total_variation(
            protocol.binary_column_marginal(observed_binary_law, column=column),
            protocol.binary_column_marginal(analytic_law, column=column),
        )
        if not math.isclose(
            float(observed_tv), recomputed, rel_tol=0.0, abs_tol=NUMERICAL_ZERO
        ):
            raise RuntimeError("isolated QuTiP marginal diagnostic drifted")

    limitations = _require_exact_keys(
        report["statistical_limitations"],
        {"finite_ntraj", "not_established", "rare_outcome_resolution_floor", "scope"},
        label="worker statistical limitations",
    )
    expected_not_established = [
        "trajectory-by-trajectory coupling to the project RNG",
        "qutrit or leakage label semantics",
        "complete multi-round QEC Record faithfulness",
        "scalability or production readiness",
    ]
    if (
        limitations["finite_ntraj"] != trajectory_count
        or not math.isclose(
            float(limitations["rare_outcome_resolution_floor"]),
            1.0 / trajectory_count,
            rel_tol=0.0,
            abs_tol=NUMERICAL_ZERO,
        )
        or limitations["scope"] != fixture["fixture_id"]
        or limitations["not_established"] != expected_not_established
    ):
        raise RuntimeError("isolated QuTiP statistical limitations drifted")
    atomic = _require_exact_keys(
        report["atomic_publication"],
        {
            "artifact_presence_means_current_invocation_completed",
            "file_fsync_before_replace",
            "durability_failure_removes_destination",
            "parent_directory_fsync_after_replace",
            "protocol",
            "stale_output_invalidated_before_compute",
        },
        label="worker atomic publication",
    )
    if not _json_type_exact_equal(atomic, {
        "artifact_presence_means_current_invocation_completed": True,
        "file_fsync_before_replace": True,
        "durability_failure_removes_destination": True,
        "parent_directory_fsync_after_replace": True,
        "protocol": (
            "unlink_previous_fsync_parent_then_mkstemp_file_fsync_"
            "replace_parent_fsync"
        ),
        "stale_output_invalidated_before_compute": True,
    }):
        raise RuntimeError("isolated QuTiP atomic publication contract drifted")


def _worker_transport_envelope(
    worker_report: dict[str, Any],
    *,
    stdout: str,
    stderr: str,
    returncode: int,
    raw_json_bytes: bytes | None = None,
) -> dict[str, Any]:
    if int(returncode) != 0:
        raise RuntimeError("cannot envelope a failed isolated QuTiP worker")
    if worker_report.get("content_hash") != protocol.canonical_content_hash(
        worker_report
    ):
        raise RuntimeError("cannot envelope a worker report with an invalid hash")
    immutable_report = copy.deepcopy(worker_report)
    if raw_json_bytes is None:
        raw_json_bytes = json.dumps(
            immutable_report,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    if not _json_type_exact_equal(
        _strict_json_loads(raw_json_bytes), immutable_report
    ):
        raise RuntimeError(
            "isolated QuTiP worker raw JSON does not match the embedded report"
        )
    envelope = {
        "schema": WORKER_ENVELOPE_SCHEMA,
        "worker_report": immutable_report,
        "worker_report_content_hash": immutable_report["content_hash"],
        "worker_report_raw_json_sha256": hashlib.sha256(raw_json_bytes).hexdigest(),
        "worker_report_raw_json_size_bytes": len(raw_json_bytes),
        "fresh_process": {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": int(returncode),
        },
    }
    envelope["content_hash"] = protocol.canonical_content_hash(envelope)
    return envelope


def _validate_worker_transport_envelope(
    envelope: dict[str, Any],
    *,
    raw_json_bytes: bytes,
) -> None:
    _require_exact_keys(
        envelope,
        {
            "content_hash",
            "fresh_process",
            "schema",
            "worker_report",
            "worker_report_content_hash",
            "worker_report_raw_json_sha256",
            "worker_report_raw_json_size_bytes",
        },
        label="worker transport envelope",
    )
    process = _require_exact_keys(
        envelope["fresh_process"],
        {"returncode", "stderr", "stdout"},
        label="worker fresh process",
    )
    worker_report = envelope["worker_report"]
    decoded_raw_report = _strict_json_loads(raw_json_bytes)
    if (
        envelope["schema"] != WORKER_ENVELOPE_SCHEMA
        or process["returncode"] != 0
        or envelope["worker_report_content_hash"] != worker_report["content_hash"]
        or worker_report["content_hash"]
        != protocol.canonical_content_hash(worker_report)
        or not _json_type_exact_equal(decoded_raw_report, worker_report)
        or envelope["worker_report_raw_json_sha256"]
        != hashlib.sha256(raw_json_bytes).hexdigest()
        or envelope["worker_report_raw_json_size_bytes"] != len(raw_json_bytes)
        or envelope["content_hash"] != protocol.canonical_content_hash(envelope)
    ):
        raise RuntimeError("isolated QuTiP worker transport envelope drifted")


def _worker_launch_environment(
    parent: dict[str, str],
    *,
    baseline_python: Path,
    cache_root: Path | None = None,
) -> dict[str, str]:
    environment = dict(parent)
    environment.pop("PYTHONPATH", None)
    for key in tuple(environment):
        if (
            key.startswith("CONDA_")
            or key.startswith("_CE_")
            or key in {"CUDA_HOME", "LD_LIBRARY_PATH", "VIRTUAL_ENV"}
        ):
            environment.pop(key, None)
    environment.update(
        {
            "PYTHONNOUSERSITE": "1",
            "CUDA_VISIBLE_DEVICES": "",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "PATH": f"{baseline_python.parent}:{os.defpath}",
        }
    )
    if cache_root is not None:
        resolved_cache_root = Path(cache_root).resolve()
        resolved_cache_root.mkdir(parents=True, exist_ok=False, mode=0o700)
        private_paths = {
            "HOME": resolved_cache_root / "home",
            "XDG_CACHE_HOME": resolved_cache_root / "xdg-cache",
            "MPLCONFIGDIR": resolved_cache_root / "mpl-config",
        }
        for path in private_paths.values():
            path.mkdir(exist_ok=False, mode=0o700)
        environment.update(
            {name: str(path) for name, path in private_paths.items()}
        )
    return environment


def _run_isolated_qutip(fixture_path: Path) -> dict[str, Any]:
    fixture = protocol.load_fixture(fixture_path)
    conda = shutil.which("conda")
    if conda is None:
        raise RuntimeError("conda executable is required for isolated QuTiP")
    baseline_python = _resolve_named_conda_python(
        conda,
        environment_name="ecs-baseline-qutip",
    )
    with tempfile.TemporaryDirectory(prefix="qutip_mcwf_xz_") as temporary:
        temporary_root = Path(temporary)
        environment = _worker_launch_environment(
            os.environ,
            baseline_python=baseline_python,
            cache_root=temporary_root / "private-runtime",
        )
        output = temporary_root / "qutip_mcwf_xz.json"
        process = subprocess.Popen(
            [
                str(baseline_python),
                str(QUTIP_WORKER),
                "--fixture",
                str(fixture_path.resolve()),
                "--output",
                str(output),
            ],
            cwd=REPO,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = _communicate_isolated_process(
            process,
            timeout_s=300.0,
        )
        if not output.is_file():
            raise RuntimeError("isolated QuTiP worker published no artifact")
        raw_json_bytes = output.read_bytes()
        report = _strict_json_loads(raw_json_bytes)
    _validate_isolated_qutip_report(
        report,
        fixture=fixture,
        fixture_path=fixture_path,
    )
    envelope = _worker_transport_envelope(
        report,
        stdout=stdout,
        stderr=stderr,
        returncode=int(process.returncode),
        raw_json_bytes=raw_json_bytes,
    )
    _validate_worker_transport_envelope(envelope, raw_json_bytes=raw_json_bytes)
    return envelope


def _resolve_named_conda_python(
    conda: str,
    *,
    environment_name: str,
) -> Path:
    """Resolve one named environment without importing it into this process."""

    completed = subprocess.run(
        [conda, "env", "list", "--json"],
        cwd=REPO,
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        capture_output=True,
        text=True,
        timeout=120.0,
        check=True,
    )
    payload = json.loads(completed.stdout)
    raw_prefixes = payload.get("envs")
    if not isinstance(raw_prefixes, list):
        raise RuntimeError("conda env list returned an invalid environment list")
    matches = [
        Path(raw).resolve(strict=True)
        for raw in raw_prefixes
        if isinstance(raw, str) and Path(raw).name == environment_name
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one Conda environment named {environment_name!r}"
        )
    executable = (matches[0] / "bin" / "python").resolve(strict=True)
    if not executable.is_relative_to(matches[0]) or not executable.is_file():
        raise RuntimeError("isolated QuTiP Python escaped its Conda prefix")
    return executable


def _communicate_isolated_process(
    process: subprocess.Popen[str],
    *,
    timeout_s: float,
) -> tuple[str, str]:
    """Collect the direct worker inside the supervisor-owned process group."""

    try:
        stdout, stderr = process.communicate(timeout=float(timeout_s))
    except subprocess.TimeoutExpired as exc:
        _terminate_worker_process(process)
        process.communicate()
        raise RuntimeError(
            f"isolated QuTiP worker timed out after {float(timeout_s):g} s"
        ) from exc
    if process.returncode != 0:
        _terminate_worker_process(process)
        raise RuntimeError(
            "isolated QuTiP worker failed:\n"
            f"stdout:\n{stdout}\nstderr:\n{stderr}"
        )
    return stdout, stderr


def _terminate_worker_process(process: subprocess.Popen[str]) -> None:
    """Reap the direct worker; it remains in the supervisor-owned process group."""

    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=1.0)
        return
    except subprocess.TimeoutExpired:
        process.kill()
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("isolated QuTiP worker cleanup failed") from exc


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(str(Path(path).resolve()), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _prepare_output_path(path: Path) -> None:
    destination = path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.unlink()
    except FileNotFoundError:
        pass
    _fsync_directory(destination.parent)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    destination = path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    published = False
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        published = True
        _fsync_directory(destination.parent)
    except BaseException:
        if published:
            try:
                destination.unlink()
            except FileNotFoundError:
                pass
            try:
                _fsync_directory(destination.parent)
            except OSError:
                pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def build_report(fixture_path: Path) -> dict[str, Any]:
    fixture = protocol.load_fixture(fixture_path)
    if float(fixture["numerical_zero"]) != NUMERICAL_ZERO:
        raise RuntimeError("neutral fixture numerical_zero drifted from project constant")
    deterministic_convergence = protocol.finite_step_convergence_evidence(fixture)
    if deterministic_convergence.get("all_checks_passed") is not True:
        raise RuntimeError("finite-step convergence or corruption evidence failed")
    project_runtime = _project_runtime_provenance()
    schedule = _schedule_from_fixture(fixture)
    execution_options = {
        "device": "cuda",
        "local_dims": fixture["local_dims"],
        "initial_levels": fixture["initial_levels"],
        "microstep_count": int(fixture["microstep_count"]),
        "trajectory_count": int(fixture["trajectory_count"]),
        "rng_seed": int(fixture["project_rng_seed"]),
    }
    direct_manifest = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        **execution_options,
    )
    if direct_manifest.get("verdict") != "pass":
        raise RuntimeError(
            f"public direct MCWF fixture failed: {direct_manifest.get('preflight')}"
        )
    direct_execution = direct_manifest["mps_execution"]
    direct_record = _validate_record_payload(
        direct_execution, fixture, label_prefix="direct MCWF"
    )
    direct_labels = _validate_label_payload(
        direct_execution["evaluator_only_diagnostics"], fixture
    )

    carrier_manifest = axis1_carrier_execution_manifest(
        schedule,
        device="cuda",
        execution_backend_contract=(
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        execution_backend_options={
            "local_dims": fixture["local_dims"],
            "initial_levels": fixture["initial_levels"],
            "microstep_count": int(fixture["microstep_count"]),
            "trajectory_count": int(fixture["trajectory_count"]),
            "rng_seed": int(fixture["project_rng_seed"]),
        },
    )
    if carrier_manifest.get("passed") is not True:
        raise RuntimeError("public Carrier MCWF fixture failed")
    carrier_record = _validate_record_payload(
        carrier_manifest["record_execution"],
        fixture,
        label_prefix="Carrier MCWF",
    )
    direct_carrier_exact = direct_record == carrier_record
    if not direct_carrier_exact:
        raise RuntimeError("public direct and Carrier MCWF Records diverged")

    qutip_envelope = _run_isolated_qutip(fixture_path)
    qutip_report = qutip_envelope["worker_report"]
    qutip_labels = _qutip_histogram(qutip_report, "label")
    qutip_binary = _qutip_histogram(qutip_report, "binary")
    comparison_alpha = float(fixture["comparison_alpha"]) / 6.0
    ntraj = int(fixture["trajectory_count"])
    qutip_label_law = _law(qutip_labels)
    qutip_binary_law = _law(qutip_binary)
    direct_label_law = _law(direct_labels)
    direct_binary_law = _law(direct_record)
    carrier_binary_law = _law(carrier_record)
    direct_finite_step_gate = protocol.finite_step_public_sample_evidence(
        fixture,
        direct_binary_law,
    )
    carrier_finite_step_gate = protocol.finite_step_public_sample_evidence(
        fixture,
        carrier_binary_law,
    )
    public_finite_step_passed = bool(
        direct_carrier_exact
        and direct_finite_step_gate["passed"]
        and carrier_finite_step_gate["passed"]
    )
    finite_step_convergence: dict[str, Any] = {
        "schema": (
            "ai_qec.external_baseline.qutip_project_mcwf_xz_finite_step_evidence.v1"
        ),
        "deterministic_recurrence": deterministic_convergence,
        "public_m40_sample_gate": {
            "direct": direct_finite_step_gate,
            "carrier": carrier_finite_step_gate,
            "direct_carrier_exact_record_match": direct_carrier_exact,
            "all_checks_passed": public_finite_step_passed,
        },
        "all_checks_passed": bool(
            deterministic_convergence["all_checks_passed"]
            and public_finite_step_passed
        ),
    }
    finite_step_convergence["content_hash"] = protocol.canonical_content_hash(
        finite_step_convergence
    )
    x_after_column = fixture["measurement_keys"].index("mx_after")
    if fixture["measurement_bases"][x_after_column] != "X":
        raise RuntimeError("directed X-after comparison is not bound to an X column")
    comparisons = {
        "qutip_vs_direct_labels": protocol.two_sample_tv_comparison(
            qutip_label_law,
            direct_label_law,
            left_sample_count=ntraj,
            right_sample_count=ntraj,
            alphabet_size=16,
            alpha=comparison_alpha,
        ),
        "qutip_vs_direct_binary": protocol.two_sample_tv_comparison(
            qutip_binary_law,
            direct_binary_law,
            left_sample_count=ntraj,
            right_sample_count=ntraj,
            alphabet_size=16,
            alpha=comparison_alpha,
        ),
        "qutip_vs_carrier_binary": protocol.two_sample_tv_comparison(
            qutip_binary_law,
            carrier_binary_law,
            left_sample_count=ntraj,
            right_sample_count=ntraj,
            alphabet_size=16,
            alpha=comparison_alpha,
        ),
        "qutip_vs_direct_labels_x_after": protocol.two_sample_tv_comparison(
            protocol.binary_column_marginal(
                qutip_label_law, column=x_after_column
            ),
            protocol.binary_column_marginal(
                direct_label_law, column=x_after_column
            ),
            left_sample_count=ntraj,
            right_sample_count=ntraj,
            alphabet_size=2,
            alpha=comparison_alpha,
        ),
        "qutip_vs_direct_binary_x_after": protocol.two_sample_tv_comparison(
            protocol.binary_column_marginal(
                qutip_binary_law, column=x_after_column
            ),
            protocol.binary_column_marginal(
                direct_binary_law, column=x_after_column
            ),
            left_sample_count=ntraj,
            right_sample_count=ntraj,
            alphabet_size=2,
            alpha=comparison_alpha,
        ),
        "qutip_vs_carrier_binary_x_after": protocol.two_sample_tv_comparison(
            protocol.binary_column_marginal(
                qutip_binary_law, column=x_after_column
            ),
            protocol.binary_column_marginal(
                carrier_binary_law, column=x_after_column
            ),
            left_sample_count=ntraj,
            right_sample_count=ntraj,
            alphabet_size=2,
            alpha=comparison_alpha,
        ),
    }
    corrupted_qutip_binary = protocol.flip_binary_column(
        qutip_binary_law, column=3
    )
    corruption_comparison = protocol.two_sample_tv_comparison(
        corrupted_qutip_binary,
        carrier_binary_law,
        left_sample_count=ntraj,
        right_sample_count=ntraj,
        alphabet_size=16,
        alpha=comparison_alpha,
    )
    corruption_detected = bool(
        not corruption_comparison["passed"]
        and corruption_comparison["total_variation"]
        > corruption_comparison["simultaneous_tv_radius"]
    )
    analytic_x_after = protocol.binary_column_marginal(
        protocol.analytic_binary_distribution(fixture), column=x_after_column
    )
    population_rate_mutation = protocol.population_rate_x_coherence_mutation(
        fixture
    )
    coherence_corruption_comparison = protocol.two_sample_tv_comparison(
        analytic_x_after,
        population_rate_mutation,
        left_sample_count=ntraj,
        right_sample_count=ntraj,
        alphabet_size=2,
        alpha=comparison_alpha,
    )
    coherence_corruption_detected = bool(
        not coherence_corruption_comparison["passed"]
        and coherence_corruption_comparison["total_variation"]
        > coherence_corruption_comparison["simultaneous_tv_radius"]
    )
    z_after_structural_zero = all(
        row[3] == 0
        for histogram in (qutip_labels, qutip_binary, direct_labels, direct_record, carrier_record)
        for row in histogram["records"]
    )
    expected_semantics = (
        "measurement_bases and reset_after are schedule-ordered one-per-Record-column; "
        "X measurement rotates into Z, projects, then rotates back unless reset prepares |+>"
    )
    project_semantics_match = bool(
        direct_execution.get("measurement_basis_semantics") == expected_semantics
        and carrier_manifest["record_execution"].get("measurement_basis_semantics")
        == expected_semantics
    )
    all_checks_passed = bool(
        qutip_report["all_checks_passed"]
        and direct_carrier_exact
        and z_after_structural_zero
        and project_semantics_match
        and all(comparison["passed"] for comparison in comparisons.values())
        and corruption_detected
        and coherence_corruption_detected
        and finite_step_convergence["all_checks_passed"]
    )
    if _project_source_provenance() != project_runtime["source_provenance"]:
        raise RuntimeError("project evidence sources changed during comparator run")
    if (
        _environment_lock_provenance()
        != project_runtime["environment_lock_provenance"]
    ):
        raise RuntimeError("project environment locks changed during comparator run")
    report = {
        "schema": SCHEMA,
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "id": fixture["fixture_id"],
            "path": str(Path(fixture_path).resolve()),
            "sha256": protocol.fixture_sha256(fixture_path),
            "trajectory_count": ntraj,
            "comparison_alpha": fixture["comparison_alpha"],
            "per_comparison_bonferroni_alpha": comparison_alpha,
            "simultaneous_comparison_count": 6,
        },
        "project_runtime_provenance": project_runtime,
        "numerical_provenance": {
            "project_array_backend": direct_execution["array_backend"],
            "carrier_array_backend": carrier_manifest["state_execution"][
                "array_backend"
            ],
            "probability_representation": (
                "python_float_from_integer_trajectory_count_ratio"
            ),
            "precision_purpose": (
                "public GPU MCWF versus isolated CPU QuTiP X/Z finite-sample differential"
            ),
            "repository_qutip_environment_lock": None,
            "environment_lock_status": "not_available_runtime_identity_recorded",
        },
        "ordered_measurement_contract": {
            "measurement_keys": fixture["measurement_keys"],
            "measurement_targets": fixture["measurement_targets"],
            "measurement_bases": fixture["measurement_bases"],
            "reset_after": fixture["reset_after"],
            "X_reset_state": "|+>",
            "Z_reset_state": "|0>",
            "project_public_semantics_match": project_semantics_match,
            "post_Z_reset_final_bit_is_structural_zero": z_after_structural_zero,
            "directed_x_after_column": x_after_column,
            "directed_x_after_key": fixture["measurement_keys"][x_after_column],
        },
        "project": {
            "direct": {
                "schema": direct_manifest["schema"],
                "content_hash": direct_manifest["content_hash"],
                "passed": True,
                "labels": direct_labels,
                "binary_record": direct_record,
            },
            "carrier": {
                "schema": carrier_manifest["schema"],
                "content_hash": carrier_manifest["content_hash"],
                "passed": True,
                "binary_record": carrier_record,
            },
            "direct_carrier_exact_record_match": direct_carrier_exact,
        },
        "isolated_qutip": qutip_envelope,
        "finite_step_convergence": finite_step_convergence,
        "comparisons": comparisons,
        "corruption_negative_control": {
            "mutation": "flip every mz_after binary bit from 0 to 1",
            "comparison": corruption_comparison,
            "detected": corruption_detected,
            "forces_overall_fail": corruption_detected,
        },
        "x_coherence_mutation_negative_control": {
            "mutation": "replace X coherence survival sqrt(s) with population survival s",
            "comparison": coherence_corruption_comparison,
            "detected": coherence_corruption_detected,
            "forces_overall_fail": coherence_corruption_detected,
        },
        "statistical_limitations": {
            "finite_ntraj": ntraj,
            "rare_outcome_resolution_floor": 1.0 / ntraj,
            "gate": (
                "Bonferroni over three joint Record and three directed X-after "
                "marginal comparisons; correlated duplicate qubit views reuse samples "
                "but retain the conservative six-way alpha allocation"
            ),
            "not_established": qutip_report["statistical_limitations"]["not_established"],
        },
        "atomic_publication": {
            "protocol": (
                "unlink_previous_fsync_parent_then_mkstemp_file_fsync_"
                "replace_parent_fsync"
            ),
            "stale_output_invalidated_before_compute": True,
            "file_fsync_before_replace": True,
            "durability_failure_removes_destination": True,
            "parent_directory_fsync_after_replace": True,
            "artifact_presence_means_current_invocation_completed": True,
        },
        "canonical_report_identity": {
            "hash_algorithm": "sha256",
            "canonicalization": (
                "json_sort_keys_compact_separators_utf8_allow_nan_false"
            ),
            "excluded_top_level_field": "content_hash",
            "content_hash_locator": "#/content_hash",
        },
        "all_checks_passed": all_checks_passed,
    }
    report["content_hash"] = protocol.canonical_content_hash(report)
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    _prepare_output_path(args.output)
    report = build_report(args.fixture)
    _atomic_write_json(args.output, report)
    print(
        "QuTiP vs public GPU MCWF X/Z: "
        f"{'PASS' if report['all_checks_passed'] else 'FAIL'}"
    )
    for name, comparison in report["comparisons"].items():
        print(
            f"{name}: TV={comparison['total_variation']:.6g} "
            f"radius={comparison['simultaneous_tv_radius']:.6g}"
        )
    print(f"wrote {args.output.resolve()}")
    return 0 if report["all_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

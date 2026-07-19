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
from typing import Any

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


SCHEMA = "ai_qec.external_baseline.qutip_project_mcwf_xz_comparison.v2"
WORKER_SCHEMA = "ai_qec.external_baseline.qutip_mcwf_xz_record.v2"
WORKER_ENVELOPE_SCHEMA = "ai_qec.external_baseline.qutip_mcwf_xz_worker_envelope.v1"
EXPECTED_PROJECT_ENVIRONMENT = "ecs"
EXPECTED_QUTIP_COMMIT = "f343ee3ca273a4ea19f6bebbd6f563354ea309ed"
EXPECTED_QUTIP_VERSION = "5.4.0.dev0+f343ee3"
REPO = Path(__file__).resolve().parents[2]
QUTIP_WORKER = Path(__file__).with_name("qutip_mcwf_xz_worker.py")
QUTIP_BASELINE_REPO = REPO / "external" / "baselines" / "qutip"
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


def _project_runtime_provenance() -> dict[str, Any]:
    if "PYTHONPATH" in os.environ:
        raise RuntimeError("project comparator refuses caller-provided PYTHONPATH")
    prefix = Path(sys.prefix).resolve()
    executable = Path(sys.executable).resolve()
    if prefix.name != EXPECTED_PROJECT_ENVIRONMENT or not executable.is_relative_to(prefix):
        raise RuntimeError(
            f"project comparator must run inside {EXPECTED_PROJECT_ENVIRONMENT!r}"
        )
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
        "repo_commit": _git("rev-parse", "HEAD"),
        "adapter_path": str(Path(__file__).resolve().relative_to(REPO)),
        "adapter_sha256": _sha256_file(Path(__file__).resolve()),
        "fixture_protocol_sha256": _sha256_file(
            Path(__file__).with_name("qutip_mcwf_xz_protocol.py")
        ),
        "qutip_worker_sha256": _sha256_file(QUTIP_WORKER),
        "pythonpath_env": None,
    }


def _schedule_from_fixture(fixture: dict[str, Any]):
    builder = CircuitBuilder(num_qubits=int(fixture["num_qubits"]))
    builder.declare_axis1_local_lindblad_context(
        Axis1LocalLindbladContextSpec(
            gamma_phi_per_ns=float(fixture["gamma_phi_per_ns"]),
            gamma_1_per_ns=float(fixture["gamma_1_per_ns"]),
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
            "evolution_duration_ns",
            "gamma_1_per_ns",
            "id",
            "initial_levels",
            "path",
            "schema",
            "sha256",
            "target_survival_probability",
        },
        label="worker fixture",
    )
    fixture_expectations = {
        "evolution_duration_ns": fixture["evolution_duration_ns"],
        "gamma_1_per_ns": fixture["gamma_1_per_ns"],
        "id": fixture["fixture_id"],
        "initial_levels": fixture["initial_levels"],
        "path": str(fixture_path.resolve()),
        "schema": fixture["schema"],
        "sha256": protocol.fixture_sha256(fixture_path),
        "target_survival_probability": fixture["target_survival_probability"],
    }
    if not _json_type_exact_equal(fixture_record, fixture_expectations):
        raise RuntimeError("isolated QuTiP fixture binding drifted")

    runtime = _require_exact_keys(
        report["runtime_provenance"],
        {
            "baseline_repo",
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
        or solver["collapse_operator_count"] != 2
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
            "binary_tv",
            "bonferroni_component_alpha",
            "derivation",
            "label_tv",
            "simultaneous_components",
            "x_after_binary_marginal_tv",
            "x_after_column",
            "x_after_key",
        },
        label="worker analytic reference",
    )
    if (
        analytic["derivation"]
        != (
            "p(X_before=0)=1/2; p(Z_before=1)=exp(-gamma*t); "
            "after X/Z reset, p(X_after=0)=(1+sqrt(exp(-gamma*t)))/2 "
            "and p(Z_after=0)=1"
        )
        or analytic["simultaneous_components"]
        != [
        "labels",
        "binary_record",
        "x_after_binary_marginal",
        ]
    ):
        raise RuntimeError("isolated QuTiP analytic comparison family drifted")
    expected_worker_alpha = float(fixture["comparison_alpha"]) / 3.0
    if not math.isclose(
        float(analytic["bonferroni_component_alpha"]),
        expected_worker_alpha,
        rel_tol=0.0,
        abs_tol=NUMERICAL_ZERO,
    ):
        raise RuntimeError("isolated QuTiP worker Bonferroni alpha drifted")
    x_after_column = fixture["measurement_keys"].index("mx_after")
    if (
        analytic["x_after_column"] != x_after_column
        or analytic["x_after_key"] != "mx_after"
    ):
        raise RuntimeError("isolated QuTiP X-after binding drifted")
    analytic_law = protocol.analytic_binary_distribution(fixture)
    observed_label_law = _law(labels)
    observed_binary_law = _law(binary)
    observed_x_after_law = protocol.binary_column_marginal(
        observed_binary_law, column=x_after_column
    )
    expected_x_after_law = protocol.binary_column_marginal(
        analytic_law, column=x_after_column
    )
    for label, expected_alphabet_size, observed_law, expected_law in (
        ("label_tv", 16, observed_label_law, analytic_law),
        ("binary_tv", 16, observed_binary_law, analytic_law),
        (
            "x_after_binary_marginal_tv",
            2,
            observed_x_after_law,
            expected_x_after_law,
        ),
    ):
        comparison = _require_exact_keys(
            analytic[label],
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
            label=f"worker {label}",
        )
        recomputed_tv = protocol.total_variation(observed_law, expected_law)
        recomputed_radius = protocol.multinomial_tv_radius(
            sample_count=trajectory_count,
            alphabet_size=expected_alphabet_size,
            alpha=expected_worker_alpha,
        )
        recomputed_passed = bool(recomputed_tv <= recomputed_radius)
        if (
            comparison["schema"]
            != "ai_qec.external_baseline.one_sample_multinomial_tv.v1"
            or comparison["sample_count"] != trajectory_count
            or comparison["alphabet_size"] != expected_alphabet_size
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
            or comparison["passed"] is not recomputed_passed
            or recomputed_passed is not True
        ):
            raise RuntimeError(f"isolated QuTiP {label} evidence drifted")

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
        or limitations["scope"]
        != "one fixed two-qubit two-boundary T1 fixture"
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
    environment = _worker_launch_environment(
        os.environ,
        baseline_python=baseline_python,
    )
    with tempfile.TemporaryDirectory(prefix="qutip_mcwf_xz_") as temporary:
        output = Path(temporary) / "qutip_mcwf_xz.json"
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
    )
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

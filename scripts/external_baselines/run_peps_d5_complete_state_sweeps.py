#!/usr/bin/env python3
"""Run the frozen d5 complete-state fidelity sweeps under hard resource gates.

This is the terminal aggregate owner.  Per-point workers and the comparator
remain nonterminal: this runner fixes D=(1,2,4,8,16), supervises fresh
processes, enforces the 1800 second / 64 GiB host / 28 GiB device envelope,
and classifies only complete complex128 state comparisons.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
import time
from typing import Any, Mapping

import numpy as np


RESULT_SCHEMA = (
    "error_coupling_simulator.external.peps_d5_complete_state_sweeps.v1"
)
REPO = Path(__file__).resolve().parents[2]
CONDA = Path("/home/cx/miniforge3/bin/conda")
BONDS = (1, 2, 4, 8, 16)
POINT_TIMEOUT_SECONDS = 1800
HOST_LIMIT_BYTES = 64 * 1024**3
DEVICE_LIMIT_BYTES = 28 * 1024**3
COMMITTED_INPUTS = (
    "baseline-environment-pepsy-linux-64.lock.json",
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
    "scripts/external_baselines/compare_peps_d5_complete_states.py",
    "scripts/external_baselines/build_pepsy_baseline_environment.py",
    "scripts/external_baselines/build_quimb_peps_d5_environment_lock.py",
    "scripts/external_baselines/emit_peps_d5_pure_state_fixture.py",
    "scripts/external_baselines/peps_d5_dense_reference.py",
    "scripts/external_baselines/peps_d5_physical_corruption_control.py",
    "scripts/external_baselines/pepsy_peps_d5_state_worker.py",
    "scripts/external_baselines/quimb_peps_d5_fidelity_worker.py",
    "scripts/external_baselines/run_peps_d5_complete_state_sweeps.py",
    "tests/test_external_peps_d5_pure_state_fidelity.py",
)
CANDIDATES = {
    "quimb": {
        "environment": "ecs-baseline-quimb-peps",
        "worker": (
            "scripts/external_baselines/quimb_peps_d5_fidelity_worker.py"
        ),
        "extra_arguments": ["--optimize", "auto-hq-serial"],
    },
    "pepsy": {
        "environment": "ecs-baseline-pepsy",
        "worker": "scripts/external_baselines/pepsy_peps_d5_state_worker.py",
        "extra_arguments": [
            "--contraction-optimize",
            "auto-hq-serial",
            "--max-dense-bytes",
            str(2 * 1024**3),
            "--max-contraction-intermediate-bytes",
            str(DEVICE_LIMIT_BYTES),
            "--max-host-rss-bytes",
            str(HOST_LIMIT_BYTES),
            "--max-device-allocation-bytes",
            str(DEVICE_LIMIT_BYTES),
        ],
    },
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_content_sha256(payload: Mapping[str, Any]) -> str:
    canonical = copy.deepcopy(dict(payload))
    publication = canonical.get("publication")
    if publication is not None:
        if not isinstance(publication, dict):
            raise ValueError("publication metadata must be an object")
        publication.pop("content_sha256", None)
    encoded = json.dumps(
        canonical,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _published_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    published = copy.deepcopy(dict(payload))
    if "publication" in published:
        raise ValueError("payload already contains publication metadata")
    published["publication"] = {
        "status": "atomically_published",
        "protocol": (
            "temporary_file_fsync_then_os_replace_then_"
            "parent_directory_fsync"
        ),
        "content_sha256_scope": (
            "canonical_utf8_json_sort_keys_compact_"
            "excluding_publication.content_sha256"
        ),
        "terminal_bundle_hashes_child_artifacts": True,
    }
    published["publication"]["content_sha256"] = (
        _canonical_content_sha256(published)
    )
    return published


def _verify_publication(payload: Mapping[str, Any]) -> None:
    publication = payload.get("publication")
    if not isinstance(publication, dict):
        raise ValueError("result has no publication metadata")
    observed = publication.get("content_sha256")
    if (
        not isinstance(observed, str)
        or observed != _canonical_content_sha256(payload)
    ):
        raise ValueError("result canonical content hash mismatch")
    if (
        publication.get("status") != "atomically_published"
        or publication.get("protocol")
        != (
            "temporary_file_fsync_then_os_replace_then_"
            "parent_directory_fsync"
        )
    ):
        raise ValueError("result atomic publication contract mismatch")


def _atomic_json(
    path: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if path.exists():
        raise FileExistsError(f"refusing to replace existing output: {path}")
    published = _published_payload(payload)
    encoded = (
        json.dumps(published, allow_nan=False, indent=2, sort_keys=True) + "\n"
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
    return published


def _verify_frozen_inputs() -> dict[str, Any]:
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
        changed = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", relative],
            cwd=REPO,
        )
        if tracked.returncode != 0 or changed.returncode != 0:
            raise RuntimeError(f"sweep input is not frozen at HEAD: {relative}")
        hashes[relative] = _file_sha256(REPO / relative)
    return {"git_head": head, "committed_input_sha256": hashes}


def _require_frozen_inputs_unchanged(
    expected: Mapping[str, Any],
    *,
    stage: str,
) -> None:
    observed = _verify_frozen_inputs()
    if observed != expected:
        raise RuntimeError(
            f"frozen sweep inputs changed during {stage}; "
            "refusing a mixed-HEAD result"
        )


def _require_comparator_head(
    comparison: Mapping[str, Any],
    *,
    expected_git_head: str,
    label: str,
) -> None:
    observed = comparison.get("provenance", {}).get("git_head")
    if observed != expected_git_head:
        raise RuntimeError(
            f"{label} comparator Git HEAD {observed!r} differs from "
            f"the frozen sweep HEAD {expected_git_head!r}"
        )


def _child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if (
            name == "PYTHONPATH"
            or name == "VIRTUAL_ENV"
            or name.startswith("CONDA_")
            or name.startswith("_CE_")
        ):
            environment.pop(name, None)
    environment.update(
        {
            "CUDA_VISIBLE_DEVICES": "0",
            "ECS_GPU_SLOT": "0",
            "PYTHONNOUSERSITE": "1",
        }
    )
    return environment


def _run_fresh_process(
    *,
    label: str,
    command: list[str],
    timeout_seconds: int,
    log_path: Path,
) -> dict[str, Any]:
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=REPO,
        env=_child_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
    elapsed = time.perf_counter() - started
    log_path.write_text(output, encoding="utf-8")
    with log_path.open("rb") as stream:
        os.fsync(stream.fileno())
    return {
        "label": label,
        "command": command,
        "timeout_seconds": timeout_seconds,
        "elapsed_seconds": elapsed,
        "timed_out": timed_out,
        "returncode": process.returncode,
        "log_path": str(log_path.resolve()),
        "log_sha256": _file_sha256(log_path),
    }


def _conda_python(environment: str, script: str, *arguments: str) -> list[str]:
    return [
        str(CONDA),
        "run",
        "--no-capture-output",
        "-n",
        environment,
        "python",
        str(REPO / script),
        *arguments,
    ]


def _candidate_resource_usage(
    candidate: str,
    summary: Mapping[str, Any],
) -> tuple[int, int]:
    def exact_nonnegative_integer(value: Any, *, label: str) -> int:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise RuntimeError(
                f"{label} must be a nonnegative JSON integer"
            )
        return value

    if candidate == "quimb":
        host_bytes = exact_nonnegative_integer(
            summary["provenance"]["python_peak_rss_kib"],
            label="Quimb peak host RSS KiB",
        ) * 1024
        device_bytes = exact_nonnegative_integer(
            summary["diagnostics"]["peak_device_allocated_bytes"],
            label="Quimb peak device allocation",
        )
    else:
        host_bytes = exact_nonnegative_integer(
            summary["resource_usage"]["python_peak_rss_bytes"],
            label="Pepsy peak host RSS bytes",
        )
        device_bytes = exact_nonnegative_integer(
            summary["resource_usage"]["peak_device_allocated_bytes"],
            label="Pepsy peak device allocation",
        )
        plan = summary["resource_plan"]
        if (
            exact_nonnegative_integer(
                plan["max_host_rss_bytes"],
                label="Pepsy host RSS limit",
            )
            != HOST_LIMIT_BYTES
            or exact_nonnegative_integer(
                plan["max_device_allocation_bytes"],
                label="Pepsy device allocation limit",
            )
            != DEVICE_LIMIT_BYTES
        ):
            raise RuntimeError("Pepsy resource plan differs from frozen limits")
    return host_bytes, device_bytes


def _summarize_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [
        row for row in rows if row["status"] == "completed"
    ]
    invalid_rows = [
        row for row in rows if row["status"] == "invalid"
    ]
    by_bond = {row["bond"]: row for row in completed}
    fidelities = [
        row["fidelity"] for row in completed
    ]
    useful = [row for row in completed if row["fidelity"] >= 0.99]

    monotonic_evaluable = len(completed) == len(BONDS)
    monotonic_passed = None
    if monotonic_evaluable:
        monotonic_passed = all(
            by_bond[right]["fidelity"] + 1e-8
            >= by_bond[left]["fidelity"]
            for left, right in zip(BONDS, BONDS[1:])
        )
    nondegenerate_evaluable = 1 in by_bond and 16 in by_bond
    separation = None
    nondegenerate_passed = None
    if nondegenerate_evaluable:
        separation = by_bond[16]["fidelity"] - by_bond[1]["fidelity"]
        nondegenerate_passed = separation > 1e-4
    if invalid_rows:
        usefulness_verdict = "invalid"
    elif len(completed) != len(BONDS):
        usefulness_verdict = "inconclusive_partial"
    elif nondegenerate_passed is not True:
        usefulness_verdict = "invalid_nondegenerate_control"
    elif not useful:
        usefulness_verdict = "fail"
    else:
        usefulness_verdict = "pass"
    d16_rank_audited = (
        16 in by_bond
        and by_bond[16].get("no_rank_discarded") is True
    )
    return {
        "requested_bonds": list(BONDS),
        "completed_bonds": sorted(by_bond),
        "invalid_bonds": sorted(row["bond"] for row in invalid_rows),
        "best_fidelity": max(fidelities) if fidelities else None,
        "best_bond": (
            max(completed, key=lambda row: row["fidelity"])["bond"]
            if completed
            else None
        ),
        "usefulness_verdict": usefulness_verdict,
        "monotonic_prediction": {
            "evaluable": monotonic_evaluable,
            "passed": monotonic_passed,
            "tolerance": 1e-8,
        },
        "bond_knob_nondegeneracy": {
            "evaluable": nondegenerate_evaluable,
            "d16_minus_d1": separation,
            "passed": nondegenerate_passed,
            "required_minimum": 1e-4,
        },
        "d16_exact_representation_prediction": {
            "evaluable": d16_rank_audited,
            "reason_if_not_evaluable": (
                None
                if d16_rank_audited
                else "candidate_has_no_authenticated_no_rank_discarded_ledger"
            ),
            "passed": (
                by_bond[16]["fidelity"] >= 1.0 - 1e-10
                if d16_rank_audited
                else None
            ),
        },
    }


def _require_requested_bond(
    summary: dict[str, Any],
    *,
    expected: int,
    label: str,
) -> None:
    value = summary.get("diagnostics", {}).get("requested_max_bond")
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value != expected
    ):
        raise RuntimeError(
            f"{label} requested_max_bond {value!r} != {expected}"
        )


def _validated_fidelity(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label} fidelity must be a finite real number")
    fidelity = float(value)
    if (
        not np.isfinite(fidelity)
        or fidelity < -1e-10
        or fidelity > 1.0 + 1e-10
    ):
        raise RuntimeError(f"{label} emitted invalid fidelity: {fidelity!r}")
    return fidelity


def _run_d3_integration_controls(
    *,
    output_directory: Path,
    candidates: list[str],
    process_rows: list[dict[str, Any]],
    expected_git_head: str,
) -> dict[str, Any]:
    fixture_path = output_directory / "fixture_d3.json"
    reference_state = output_directory / "reference_d3.npy"
    reference_summary = output_directory / "reference_d3.json"
    emit = _run_fresh_process(
        label="emit_d3_fixture",
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/"
            "emit_peps_d5_pure_state_fixture.py",
            "--distance",
            "3",
            "--output-json",
            str(fixture_path),
        ),
        timeout_seconds=60,
        log_path=output_directory / "emit_d3.log",
    )
    process_rows.append(emit)
    if emit["returncode"] != 0 or emit["timed_out"]:
        raise RuntimeError(f"d3 fixture emission failed: {emit}")
    reference = _run_fresh_process(
        label="dense_reference_d3",
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/peps_d5_dense_reference.py",
            "--fixture",
            str(fixture_path),
            "--output-state",
            str(reference_state),
            "--output-summary",
            str(reference_summary),
            "--device",
            "cuda",
            "--require-numpy-crosscheck",
        ),
        timeout_seconds=POINT_TIMEOUT_SECONDS,
        log_path=output_directory / "reference_d3.log",
    )
    process_rows.append(reference)
    if reference["returncode"] != 0 or reference["timed_out"]:
        raise RuntimeError(f"d3 dense reference failed: {reference}")

    rows: dict[str, Any] = {}
    for candidate in candidates:
        config = CANDIDATES[candidate]
        prefix = f"{candidate}_d3_D16"
        state_path = output_directory / f"{prefix}.npy"
        summary_path = output_directory / f"{prefix}.json"
        comparison_path = output_directory / f"{prefix}_fidelity.json"
        worker = _run_fresh_process(
            label=prefix,
            command=_conda_python(
                config["environment"],
                config["worker"],
                "--fixture",
                str(fixture_path),
                "--max-bond",
                "16",
                "--output-state",
                str(state_path),
                "--output-summary",
                str(summary_path),
                "--device",
                "cuda",
                *config["extra_arguments"],
            ),
            timeout_seconds=POINT_TIMEOUT_SECONDS,
            log_path=output_directory / f"{prefix}.log",
        )
        process_rows.append(worker)
        if worker["returncode"] != 0 or worker["timed_out"]:
            raise RuntimeError(f"{candidate} d3 integration failed: {worker}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("status") != "completed":
            raise RuntimeError(
                f"{candidate} d3 integration unavailable: "
                f"{summary.get('reason')}"
            )
        _require_requested_bond(
            summary,
            expected=16,
            label=f"{candidate} d3 integration",
        )
        host_bytes, device_bytes = _candidate_resource_usage(
            candidate,
            summary,
        )
        if (
            host_bytes > HOST_LIMIT_BYTES
            or device_bytes > DEVICE_LIMIT_BYTES
        ):
            raise RuntimeError(f"{candidate} d3 integration exceeded resources")
        compare_process = _run_fresh_process(
            label=f"{prefix}_compare",
            command=_conda_python(
                "ecs",
                "scripts/external_baselines/"
                "compare_peps_d5_complete_states.py",
                "--reference-summary",
                str(reference_summary),
                "--candidate-summary",
                str(summary_path),
                "--output-json",
                str(comparison_path),
            ),
            timeout_seconds=300,
            log_path=output_directory / f"{prefix}_compare.log",
        )
        process_rows.append(compare_process)
        if (
            compare_process["returncode"] != 0
            or compare_process["timed_out"]
        ):
            raise RuntimeError(
                f"{candidate} d3 comparison failed: {compare_process}"
            )
        comparison = json.loads(
            comparison_path.read_text(encoding="utf-8")
        )
        _require_comparator_head(
            comparison,
            expected_git_head=expected_git_head,
            label=f"{candidate} d3 integration",
        )
        fidelity = _validated_fidelity(
            comparison["metric"]["normalized_squared_overlap"],
            label=f"{candidate} d3 integration",
        )
        if fidelity < 1.0 - 1e-10:
            raise RuntimeError(
                f"{candidate} d3 D16 fidelity control failed: {fidelity}"
            )
        rows[candidate] = {
            "bond": 16,
            "fidelity": fidelity,
            "required_minimum": 1.0 - 1e-10,
            "candidate_summary_sha256": _file_sha256(summary_path),
            "comparison_sha256": _file_sha256(comparison_path),
            "host_peak_bytes": host_bytes,
            "device_peak_bytes": device_bytes,
            "passed": True,
        }
    return {
        "status": "passed",
        "reference_summary_sha256": _file_sha256(reference_summary),
        "candidate_controls": rows,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument(
        "--candidates",
        nargs="+",
        choices=tuple(CANDIDATES),
        default=list(CANDIDATES),
    )
    parser.add_argument(
        "--controls-only",
        action="store_true",
        help="Run the d3 integration gate and stop before any d5 evolution.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if len(args.candidates) != len(set(args.candidates)):
        raise ValueError("candidate names must be unique")
    if args.output_directory.exists():
        raise FileExistsError(
            f"output directory already exists: {args.output_directory}"
        )
    provenance = _verify_frozen_inputs()
    args.output_directory.mkdir(parents=True)
    fixture_path = args.output_directory / "fixture_d5.json"
    reference_state = args.output_directory / "reference_d5.npy"
    reference_summary = args.output_directory / "reference_d5.json"
    corruption_control_path = (
        args.output_directory / "physical_corruption_control.json"
    )
    process_rows: list[dict[str, Any]] = []

    lock_path = Path("/tmp/ecs_gpu.0.lock")
    with lock_path.open("a+b") as gpu_lock:
        fcntl.flock(gpu_lock.fileno(), fcntl.LOCK_EX)
        d3_controls = _run_d3_integration_controls(
            output_directory=args.output_directory,
            candidates=list(CANDIDATES),
            process_rows=process_rows,
            expected_git_head=provenance["git_head"],
        )
        _require_frozen_inputs_unchanged(
            provenance,
            stage="post-d3 integration control gate",
        )
        if args.controls_only:
            control_result = {
                "schema": (
                    "error_coupling_simulator.external."
                    "peps_d3_integration_controls.v1"
                ),
                "status": "passed",
                "d3_integration_controls": d3_controls,
                "resource_gate": {
                    "point_timeout_seconds": POINT_TIMEOUT_SECONDS,
                    "host_peak_limit_bytes": HOST_LIMIT_BYTES,
                    "device_peak_limit_bytes": DEVICE_LIMIT_BYTES,
                    "gpu_lock": str(lock_path),
                },
                "processes": process_rows,
                "provenance": {
                    **provenance,
                    "runner_path": str(Path(__file__).resolve()),
                    "runner_sha256": _file_sha256(Path(__file__).resolve()),
                },
            }
            destination = (
                args.output_directory / "d3_control_result.json"
            )
            _require_frozen_inputs_unchanged(
                provenance,
                stage="controls-only publication",
            )
            control_result = _atomic_json(destination, control_result)
            print(json.dumps(control_result, sort_keys=True), flush=True)
            return 0
        emit = _run_fresh_process(
            label="emit_fixture",
            command=_conda_python(
                "ecs",
                "scripts/external_baselines/"
                "emit_peps_d5_pure_state_fixture.py",
                "--distance",
                "5",
                "--output-json",
                str(fixture_path),
            ),
            timeout_seconds=60,
            log_path=args.output_directory / "emit.log",
        )
        process_rows.append(emit)
        if emit["returncode"] != 0 or emit["timed_out"]:
            raise RuntimeError(f"d5 fixture emission failed: {emit}")

        reference = _run_fresh_process(
            label="dense_reference",
            command=_conda_python(
                "ecs",
                "scripts/external_baselines/peps_d5_dense_reference.py",
                "--fixture",
                str(fixture_path),
                "--output-state",
                str(reference_state),
                "--output-summary",
                str(reference_summary),
                "--device",
                "cuda",
            ),
            timeout_seconds=POINT_TIMEOUT_SECONDS,
            log_path=args.output_directory / "reference.log",
        )
        process_rows.append(reference)
        if reference["returncode"] != 0 or reference["timed_out"]:
            raise RuntimeError(f"d5 dense reference failed: {reference}")

        corruption_control = _run_fresh_process(
            label="physical_corruption_control",
            command=_conda_python(
                "ecs",
                "scripts/external_baselines/"
                "peps_d5_physical_corruption_control.py",
                "--fixture",
                str(fixture_path),
                "--reference-state",
                str(reference_state),
                "--reference-summary",
                str(reference_summary),
                "--output-json",
                str(corruption_control_path),
                "--device",
                "cuda",
            ),
            timeout_seconds=POINT_TIMEOUT_SECONDS,
            log_path=args.output_directory / "physical_corruption.log",
        )
        process_rows.append(corruption_control)
        if (
            corruption_control["returncode"] != 0
            or corruption_control["timed_out"]
        ):
            raise RuntimeError(
                f"d5 physical corruption control failed: "
                f"{corruption_control}"
            )

        candidate_results: dict[str, Any] = {}
        for candidate in args.candidates:
            config = CANDIDATES[candidate]
            rows: list[dict[str, Any]] = []
            for bond in BONDS:
                _require_frozen_inputs_unchanged(
                    provenance,
                    stage=f"{candidate} d5 D{bond} preflight",
                )
                prefix = f"{candidate}_d5_D{bond}"
                state_path = args.output_directory / f"{prefix}.npy"
                summary_path = args.output_directory / f"{prefix}.json"
                comparison_path = (
                    args.output_directory / f"{prefix}_fidelity.json"
                )
                worker_command = _conda_python(
                    config["environment"],
                    config["worker"],
                    "--fixture",
                    str(fixture_path),
                    "--max-bond",
                    str(bond),
                    "--output-state",
                    str(state_path),
                    "--output-summary",
                    str(summary_path),
                    "--device",
                    "cuda",
                    *config["extra_arguments"],
                )
                worker = _run_fresh_process(
                    label=prefix,
                    command=worker_command,
                    timeout_seconds=POINT_TIMEOUT_SECONDS,
                    log_path=args.output_directory / f"{prefix}.log",
                )
                process_rows.append(worker)
                if worker["timed_out"]:
                    rows.append(
                        {
                            "bond": bond,
                            "status": "UNAVAILABLE",
                            "reason": "wall_timeout",
                            "process": worker,
                        }
                    )
                    continue
                if worker["returncode"] != 0:
                    rows.append(
                        {
                            "bond": bond,
                            "status": "invalid",
                            "reason": "worker_failure",
                            "process": worker,
                        }
                    )
                    continue
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                if summary.get("status") == "UNAVAILABLE":
                    rows.append(
                        {
                            "bond": bond,
                            "status": "UNAVAILABLE",
                            "reason": summary.get("reason"),
                            "process": worker,
                            "summary_sha256": _file_sha256(summary_path),
                        }
                    )
                    continue
                if summary.get("status") != "completed":
                    rows.append(
                        {
                            "bond": bond,
                            "status": "invalid",
                            "reason": "worker_status_not_completed",
                            "process": worker,
                            "summary_sha256": _file_sha256(summary_path),
                        }
                    )
                    continue
                try:
                    _require_requested_bond(
                        summary,
                        expected=bond,
                        label=f"{candidate} d5 D{bond}",
                    )
                except RuntimeError as error:
                    rows.append(
                        {
                            "bond": bond,
                            "status": "invalid",
                            "reason": "requested_bond_mismatch",
                            "detail": str(error),
                            "process": worker,
                            "summary_sha256": _file_sha256(summary_path),
                        }
                    )
                    continue
                host_bytes, device_bytes = _candidate_resource_usage(
                    candidate,
                    summary,
                )
                if (
                    host_bytes > HOST_LIMIT_BYTES
                    or device_bytes > DEVICE_LIMIT_BYTES
                ):
                    rows.append(
                        {
                            "bond": bond,
                            "status": "UNAVAILABLE",
                            "reason": "measured_resource_limit_exceeded",
                            "host_peak_bytes": host_bytes,
                            "device_peak_bytes": device_bytes,
                            "process": worker,
                        }
                    )
                    continue
                remaining_seconds = int(
                    POINT_TIMEOUT_SECONDS - worker["elapsed_seconds"]
                )
                if remaining_seconds < 1:
                    rows.append(
                        {
                            "bond": bond,
                            "status": "UNAVAILABLE",
                            "reason": "point_wall_timeout_before_comparison",
                            "process": worker,
                        }
                    )
                    continue
                comparison = _run_fresh_process(
                    label=f"{prefix}_compare",
                    command=_conda_python(
                        "ecs",
                        "scripts/external_baselines/"
                        "compare_peps_d5_complete_states.py",
                        "--reference-summary",
                        str(reference_summary),
                        "--candidate-summary",
                        str(summary_path),
                        "--output-json",
                        str(comparison_path),
                    ),
                    timeout_seconds=remaining_seconds,
                    log_path=(
                        args.output_directory / f"{prefix}_compare.log"
                    ),
                )
                process_rows.append(comparison)
                if comparison["returncode"] != 0 or comparison["timed_out"]:
                    rows.append(
                        {
                            "bond": bond,
                            "status": "invalid",
                            "reason": "comparison_failure",
                            "process": comparison,
                        }
                    )
                    continue
                comparison_payload = json.loads(
                    comparison_path.read_text(encoding="utf-8")
                )
                _require_comparator_head(
                    comparison_payload,
                    expected_git_head=provenance["git_head"],
                    label=f"{candidate} d5 D{bond}",
                )
                fidelity = _validated_fidelity(
                    comparison_payload["metric"][
                        "normalized_squared_overlap"
                    ],
                    label=f"{candidate} d5 D{bond}",
                )
                rows.append(
                    {
                        "bond": bond,
                        "status": "completed",
                        "fidelity": fidelity,
                        "classification": comparison_payload["metric"][
                            "classification"
                        ],
                        "host_peak_bytes": host_bytes,
                        "device_peak_bytes": device_bytes,
                        "point_wall_seconds": (
                            worker["elapsed_seconds"]
                            + comparison["elapsed_seconds"]
                        ),
                        "no_rank_discarded": summary["diagnostics"].get(
                            "no_rank_discarded"
                        ),
                        "candidate_summary_sha256": _file_sha256(
                            summary_path
                        ),
                        "comparison_sha256": _file_sha256(comparison_path),
                    }
                )
            candidate_results[candidate] = {
                "points": rows,
                "aggregate": _summarize_candidate(rows),
            }

    _require_frozen_inputs_unchanged(
        provenance,
        stage="terminal sweep publication",
    )
    result = {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "claim_boundary": (
            "controlled 5x5 pure-state unitary benchmark only; no ancilla, "
            "measurement, reset, Kraus, leakage, Record, LER, calibration, "
            "or scaling claim"
        ),
        "resource_gate": {
            "point_timeout_seconds": POINT_TIMEOUT_SECONDS,
            "host_peak_limit_bytes": HOST_LIMIT_BYTES,
            "device_peak_limit_bytes": DEVICE_LIMIT_BYTES,
            "gpu_lock": str(lock_path),
        },
        "d3_integration_controls": d3_controls,
        "candidates": candidate_results,
        "physical_corruption_control": {
            "path": str(corruption_control_path.resolve()),
            "file_sha256": _file_sha256(corruption_control_path),
            "payload": json.loads(
                corruption_control_path.read_text(encoding="utf-8")
            ),
        },
        "processes": process_rows,
        "provenance": {
            **provenance,
            "runner_path": str(Path(__file__).resolve()),
            "runner_sha256": _file_sha256(Path(__file__).resolve()),
            "python_peak_rss_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }
    destination = args.output_directory / "sweep_result.json"
    result = _atomic_json(destination, result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

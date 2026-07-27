#!/usr/bin/env python3
"""Run the frozen two-round XZZX exact-reference/Quimb-PEPS experiment.

This is the terminal aggregate owner.  It keeps native runtimes in fresh
processes, enforces the preregistered resource envelope and execution order,
and refuses to start d5 unless every d2/d3 gate passes conjunctively.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import tempfile
import time
from typing import Any, Mapping, Sequence


RESULT_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.experiment.v1"
)
REPO = Path(__file__).resolve().parents[2]
CONDA = Path("/home/cx/miniforge3/bin/conda")
POINT_TIMEOUT_SECONDS = 1800
HOST_LIMIT_BYTES = 64 * 1024**3
DEVICE_LIMIT_BYTES = 28 * 1024**3
GPU_LOCK = Path("/tmp/ecs_gpu.0.lock")
REVIEW_MARKDOWN = (
    "docs/simulator_validation/"
    "PEPS_XZZX_ARTIFACT_ONLY_REVIEW_2026-07-27.md"
)
REVIEW_JSON = (
    "docs/simulator_validation/"
    "PEPS_XZZX_ARTIFACT_ONLY_REVIEW_2026-07-27.json"
)
FROZEN_PREREG_COMMIT = "dc7f6a6a4bbc2ae3e8ba8dea6f00343ef9a9fc67"
FROZEN_PREREG_SHA256 = (
    "76889bb6f9287ec7b5278257a81c71aacdbf697eb8a051003b1fbd90c05d4c36"
)
FROZEN_PREREG_PATH = (
    "docs/simulator_validation/"
    "PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_V2_2026-07-27.md"
)
D3_BONDS = (1, 2, 4, 8)
D5_BONDS = (1, 2, 4)
D5_RADII = (0, 1, 2, 3)
D3_BRANCHES = ("primary", "alternate")
EXPECTED_HASHES = {
    2: {
        "fixture": (
            "dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5"
        ),
        "stim": (
            "18492ad9bc8b286d1cf9f97f45546fac40552a10d83be9ef61fa892a941cb671"
        ),
        "spec": (
            "02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca"
        ),
    },
    3: {
        "fixture": (
            "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
        ),
        "stim": (
            "7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0"
        ),
        "spec": (
            "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9"
        ),
    },
    5: {
        "fixture": (
            "659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495"
        ),
        "stim": (
            "be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008"
        ),
        "spec": (
            "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4"
        ),
    },
}
COMMITTED_INPUTS = (
    "baseline-environment-quimb-peps-linux-64.lock.json",
    "core-environment-cu130.lock",
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_XZZX_PRETARGET_IMPLEMENTATION_AUDIT_2026-07-27.md"
    ),
    FROZEN_PREREG_PATH,
    (
        REVIEW_MARKDOWN
    ),
    REVIEW_JSON,
    "scripts/external_baselines/compare_xzzx_record_peps.py",
    "scripts/external_baselines/emit_xzzx_record_peps_fixture.py",
    "scripts/external_baselines/xzzx_record_dense_reference.py",
    "scripts/external_baselines/xzzx_record_exact_data_reference.py",
    "scripts/external_baselines/xzzx_record_quimb_candidate.py",
    "scripts/external_baselines/run_xzzx_record_peps_experiment.py",
    "tests/test_external_xzzx_record_fixture.py",
    "tests/test_external_xzzx_record_dense_reference.py",
    "tests/test_external_xzzx_record_exact_data_reference.py",
    "tests/test_external_xzzx_record_metrics.py",
    "tests/test_external_xzzx_record_quimb_candidate.py",
    "tests/test_external_xzzx_record_runner.py",
)
REVIEWED_IMPLEMENTATION_PATHS = tuple(
    relative
    for relative in COMMITTED_INPUTS
    if relative.startswith("scripts/") or relative.startswith("tests/")
)


def execution_plan() -> dict[str, Any]:
    """Return the frozen point grid in its only admissible order."""

    return {
        "rounds": 2,
        "d2": {
            "distance": 2,
            "bond_dimensions": [8],
            "rdm_radii": ["complete"],
            "raw_support_size": 1024,
            "record_support_size": 64,
        },
        "d3": {
            "distance": 3,
            "branches": list(D3_BRANCHES),
            "bond_dimensions": list(D3_BONDS),
            "rdm_radii": ["complete"],
            "points": [
                {"branch": branch, "bond": bond, "radius": "complete"}
                for branch in D3_BRANCHES
                for bond in D3_BONDS
            ],
        },
        "d5": {
            "distance": 5,
            "branches": ["primary"],
            "bond_dimensions": list(D5_BONDS),
            "rdm_radii": list(D5_RADII),
            "points": [
                {"branch": "primary", "bond": bond, "radius": radius}
                for bond in D5_BONDS
                for radius in D5_RADII
            ],
        },
    }


def child_environment() -> dict[str, str]:
    """Return a runtime-neutral child environment with one visible GPU."""

    environment = dict(os.environ)
    exact_removals = {
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONUSERBASE",
        "VIRTUAL_ENV",
        "LD_LIBRARY_PATH",
        "LD_PRELOAD",
        "LIBRARY_PATH",
        "CPATH",
        "C_INCLUDE_PATH",
        "CPLUS_INCLUDE_PATH",
        "CMAKE_PREFIX_PATH",
        "PKG_CONFIG_PATH",
        "CUDA_HOME",
        "CUDA_PATH",
        "CUDACXX",
        "CUPY_ACCELERATORS",
        "TORCH_CUDA_ARCH_LIST",
    }
    for name in tuple(environment):
        if (
            name in exact_removals
            or name.startswith("CONDA_")
            or name.startswith("_CE_")
            or name.startswith("ECS_")
        ):
            environment.pop(name, None)
    environment.update(
        {
            "CUDA_VISIBLE_DEVICES": "0",
            "CUDA_DEVICE_ORDER": "PCI_BUS_ID",
            "ECS_GPU_SLOT": "0",
            "ECS_XZZX_REQUIRE_CUDA_CONTROLS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHONNOUSERSITE": "1",
        }
    )
    return environment


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key in {path}: {key}")
            value[key] = item
        return value

    def reject_nonfinite(value: str) -> None:
        raise ValueError(f"non-finite JSON number in {path}: {value}")

    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_nonfinite,
    )
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    if not path.parent.is_dir():
        raise ValueError(f"output parent does not exist: {path.parent}")
    if os.path.lexists(path):
        raise FileExistsError(f"refusing to replace existing output: {path}")
    encoded = (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise FileExistsError(
                f"refusing to replace existing output: {path}"
            ) from error
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _atomic_bytes(path: Path, payload: bytes) -> None:
    if not path.parent.is_dir():
        raise ValueError(f"output parent does not exist: {path.parent}")
    if os.path.lexists(path):
        raise FileExistsError(f"refusing to replace existing output: {path}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise FileExistsError(
                f"refusing to replace existing output: {path}"
            ) from error
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _git_text(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def verify_frozen_inputs() -> dict[str, Any]:
    """Require every claim-bearing byte to be tracked and equal to HEAD."""

    head = _git_text("rev-parse", "HEAD")
    if _git_text("rev-parse", "--is-shallow-repository") != "false":
        raise RuntimeError("formal experiment requires a non-shallow repository")
    identities: dict[str, Any] = {}
    for relative in COMMITTED_INPUTS:
        path = REPO / relative
        if not path.is_file():
            raise RuntimeError(f"committed input is absent: {relative}")
        if (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", "--", relative],
                cwd=REPO,
                capture_output=True,
                text=True,
            ).returncode
            != 0
            or subprocess.run(
                ["git", "diff", "--quiet", "HEAD", "--", relative],
                cwd=REPO,
            ).returncode
            != 0
        ):
            raise RuntimeError(f"experiment input is not frozen at HEAD: {relative}")
        identities[relative] = {
            "blob": _git_text("rev-parse", f"HEAD:{relative}"),
            "sha256": _file_sha256(path),
        }
    return {
        "git_head": head,
        "repository_is_shallow": False,
        "committed_inputs": identities,
    }


def verify_artifact_only_review(
    frozen_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Authenticate the un-led review against the exact implementation bytes."""

    prereg_path = REPO / FROZEN_PREREG_PATH
    frozen_prereg_bytes = subprocess.run(
        [
            "git",
            "show",
            f"{FROZEN_PREREG_COMMIT}:{FROZEN_PREREG_PATH}",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout
    if (
        _file_sha256(prereg_path) != FROZEN_PREREG_SHA256
        or hashlib.sha256(frozen_prereg_bytes).hexdigest()
        != FROZEN_PREREG_SHA256
        or prereg_path.read_bytes() != frozen_prereg_bytes
    ):
        raise RuntimeError("current preregistration differs from frozen commit")
    review = _json_object(REPO / REVIEW_JSON)
    required_fields = {
        "schema",
        "status",
        "reviewer_mode",
        "reviewed_implementation_commit",
        "frozen_preregistration_commit",
        "frozen_preregistration_sha256",
        "review_markdown_sha256",
        "reviewed_inputs",
        "target_outputs_inspected",
        "implementation_modified",
    }
    if (
        set(review) != required_fields
        or review.get("schema")
        != (
            "error_coupling_simulator.external_xzzx_record_peps."
            "artifact_only_review.v1"
        )
        or review.get("status") != "pass"
        or review.get("reviewer_mode") != "new_unled_read_only"
        or review.get("target_outputs_inspected") is not False
        or review.get("implementation_modified") is not False
        or review.get("frozen_preregistration_commit")
        != FROZEN_PREREG_COMMIT
        or review.get("frozen_preregistration_sha256")
        != FROZEN_PREREG_SHA256
        or review.get("review_markdown_sha256")
        != _file_sha256(REPO / REVIEW_MARKDOWN)
    ):
        raise RuntimeError("artifact-only review identity or verdict is invalid")
    reviewed_commit = review.get("reviewed_implementation_commit")
    if (
        not isinstance(reviewed_commit, str)
        or len(reviewed_commit) != 40
        or any(character not in "0123456789abcdef" for character in reviewed_commit)
    ):
        raise RuntimeError("artifact review commit is not a full Git commit")
    if (
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                reviewed_commit,
                str(frozen_inputs["git_head"]),
            ],
            cwd=REPO,
        ).returncode
        != 0
    ):
        raise RuntimeError("reviewed implementation is not an ancestor of HEAD")
    reviewed_inputs = review.get("reviewed_inputs")
    if not isinstance(reviewed_inputs, Mapping) or set(
        reviewed_inputs
    ) != set(REVIEWED_IMPLEMENTATION_PATHS):
        raise RuntimeError("artifact review did not cover the exact input set")
    for relative in REVIEWED_IMPLEMENTATION_PATHS:
        row = reviewed_inputs.get(relative)
        current = frozen_inputs["committed_inputs"][relative]
        if (
            not isinstance(row, Mapping)
            or set(row) != {"git_blob", "sha256"}
            or row.get("git_blob") != current["blob"]
            or row.get("sha256") != current["sha256"]
            or _git_text("rev-parse", f"{reviewed_commit}:{relative}")
            != current["blob"]
        ):
            raise RuntimeError(
                f"artifact review does not bind current bytes: {relative}"
            )
    return dict(review)


def run_fresh_process(
    *,
    label: str,
    command: Sequence[str],
    log_path: Path,
    timeout_seconds: int = POINT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run one shell-free child in a new process group under the host cap."""

    if timeout_seconds <= 0 or timeout_seconds > POINT_TIMEOUT_SECONDS:
        raise ValueError("fresh-process timeout is outside the frozen cap")
    resource_path = log_path.with_name(f"{log_path.name}.resource")
    if os.path.lexists(resource_path):
        raise FileExistsError(
            f"refusing to replace process resource log: {resource_path}"
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{resource_path.name}.",
        suffix=".tmp",
        dir=resource_path.parent,
    )
    os.close(descriptor)
    temporary_resource = Path(temporary_name)
    try:
        timed_command = [
            "/usr/bin/time",
            "--format=%M",
            "--output",
            str(temporary_resource),
            "--",
            *command,
        ]
        started = time.perf_counter()
        process = subprocess.Popen(
            timed_command,
            cwd=REPO,
            env=child_environment(),
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
        _atomic_bytes(log_path, output.encode("utf-8"))
        resource_payload = temporary_resource.read_bytes()
        _atomic_bytes(resource_path, resource_payload)
    finally:
        temporary_resource.unlink(missing_ok=True)
    peak_host_rss_bytes: int | None = None
    if resource_path.is_file():
        resource_text = resource_path.read_text(encoding="utf-8").strip()
        try:
            peak_host_rss_bytes = int(resource_text) * 1024
        except ValueError as error:
            if not timed_out and process.returncode == 0:
                raise RuntimeError(
                    f"invalid GNU time RSS evidence for "
                    f"{label}: {resource_text!r}"
                ) from error
    host_limit_passed = (
        peak_host_rss_bytes is not None
        and peak_host_rss_bytes <= HOST_LIMIT_BYTES
    )
    return {
        "label": label,
        "command": list(command),
        "timeout_seconds": timeout_seconds,
        "elapsed_seconds": elapsed,
        "timed_out": timed_out,
        "returncode": process.returncode,
        "log_path": str(log_path.resolve()),
        "log_sha256": _file_sha256(log_path),
        "resource_log_path": (
            str(resource_path.resolve()) if resource_path.is_file() else None
        ),
        "resource_log_sha256": (
            _file_sha256(resource_path) if resource_path.is_file() else None
        ),
        "peak_host_rss_bytes": peak_host_rss_bytes,
        "host_limit_passed": host_limit_passed,
        "fresh_process_group": True,
        "host_rss_limit_bytes": HOST_LIMIT_BYTES,
        "host_rss_measured_by": "gnu_time_maximum_resident_set",
    }


def _conda_python(environment: str, script: str, *arguments: str) -> list[str]:
    return [
        str(CONDA),
        "run",
        "--no-capture-output",
        "-n",
        environment,
        "python",
        "-s",
        str(REPO / script),
        *arguments,
    ]


def validate_resource_usage(summary: Mapping[str, Any]) -> dict[str, int]:
    usage = summary.get("resource_usage")
    if not isinstance(usage, Mapping):
        raise RuntimeError("worker summary lacks resource usage")

    def integer(name: str) -> int:
        value = usage.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise RuntimeError(f"{name} must be a nonnegative integer")
        return value

    host = integer("python_peak_rss_bytes")
    device = integer("peak_device_allocated_bytes")
    if host > HOST_LIMIT_BYTES:
        raise RuntimeError("worker exceeded frozen host memory limit")
    if device > DEVICE_LIMIT_BYTES:
        raise RuntimeError("worker exceeded frozen device memory limit")
    return {
        "python_peak_rss_bytes": host,
        "peak_device_allocated_bytes": device,
    }


def validate_exact_resource_usage(
    summary: Mapping[str, Any],
) -> dict[str, float | int]:
    usage = summary.get("resource_usage")
    if not isinstance(usage, Mapping):
        raise RuntimeError("exact summary lacks resource usage")
    wall = usage.get("wall_seconds")
    host_kib = usage.get("peak_host_rss_kib")
    device = usage.get("peak_device_allocation_bytes")
    if (
        isinstance(wall, bool)
        or not isinstance(wall, (int, float))
        or not math.isfinite(wall)
        or wall < 0.0
        or wall > POINT_TIMEOUT_SECONDS
    ):
        raise RuntimeError("exact worker wall evidence is invalid")
    for name, value in (
        ("peak host RSS", host_kib),
        ("peak device allocation", device),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError(f"exact worker {name} must be an integer")
    assert isinstance(host_kib, int)
    assert isinstance(device, int)
    host = host_kib * 1024
    if host > HOST_LIMIT_BYTES:
        raise RuntimeError("exact worker exceeded frozen host memory limit")
    if device > DEVICE_LIMIT_BYTES:
        raise RuntimeError("exact worker exceeded frozen device memory limit")
    return {
        "wall_seconds": float(wall),
        "python_peak_rss_bytes": host,
        "peak_device_allocated_bytes": device,
    }


def evaluate_d3_gate(
    *,
    control_processes_passed: bool,
    d2_comparison: Mapping[str, Any],
    exact_dense_comparisons: Mapping[str, Mapping[str, Any]],
    d3_points: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Apply the conjunctive preregistered gate that alone authorizes d5."""

    if set(exact_dense_comparisons) != set(D3_BRANCHES):
        raise ValueError("d3 exact/dense comparison set is incomplete")
    expected = {
        (branch, bond)
        for branch in D3_BRANCHES
        for bond in D3_BONDS
    }
    indexed: dict[tuple[str, int], Mapping[str, Any]] = {}
    for row in d3_points:
        key = (
            row.get("branch_role", row.get("branch_id")),
            row.get("bond_dimension"),
        )
        if key in indexed:
            raise ValueError("duplicate d3 point")
        indexed[key] = row
    if set(indexed) != expected:
        raise ValueError("d3 point grid is incomplete")

    branch_results: dict[str, Any] = {}
    for branch in D3_BRANCHES:
        ordered = [indexed[(branch, bond)] for bond in D3_BONDS]
        fidelities: list[float] = []
        available = True
        for row in ordered:
            value = row.get("fidelity")
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0.0 <= float(value) <= 1.0
            ):
                available = False
                continue
            fidelities.append(float(value))
        monotonic = (
            all(
                right + 1e-8 >= left
                for left, right in zip(fidelities, fidelities[1:])
            )
            if available
            else None
        )
        movement = (
            abs(fidelities[-1] - fidelities[0])
            if available
            else None
        )
        d8_useful = (
            available
            and ordered[-1].get("verdict")
            == "useful_conditioned_trajectory"
        )
        branch_results[branch] = {
            "fidelities_by_bond": {
                str(bond): row.get("fidelity")
                for bond, row in zip(D3_BONDS, ordered, strict=True)
            },
            "all_points_available": available,
            "monotonic_non_decreasing": monotonic,
            "monotonic_tolerance": 1e-8,
            "bond_knob_movement": movement,
            "bond_knob_required_minimum": 1e-4,
            "d8_useful": d8_useful,
            "passes": (
                available
                and movement is not None
                and movement > 1e-4
                and d8_useful
            ),
        }
    passes = (
        control_processes_passed
        and d2_comparison.get("passes") is True
        and all(
            exact_dense_comparisons[branch].get("passes") is True
            for branch in D3_BRANCHES
        )
        and all(branch_results[branch]["passes"] for branch in D3_BRANCHES)
    )
    return {
        "controls_passed": control_processes_passed,
        "d2_complete_law_gate_passed": d2_comparison.get("passes") is True,
        "exact_dense_gates": {
            branch: exact_dense_comparisons[branch].get("passes") is True
            for branch in D3_BRANCHES
        },
        **branch_results,
        "passes": passes,
    }


def summarize_d5(points: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = {
        (bond, radius)
        for bond in D5_BONDS
        for radius in D5_RADII
    }
    indexed: dict[tuple[int, int], Mapping[str, Any]] = {}
    for row in points:
        if row.get("branch_role", row.get("branch_id")) != "primary":
            raise ValueError("d5 contains a non-primary branch")
        key = (row.get("bond_dimension"), row.get("rdm_radius"))
        if key in indexed:
            raise ValueError("duplicate d5 point")
        indexed[key] = row
    complete = set(indexed) == expected
    terminal = indexed.get((4, 3))
    if not complete or terminal is None:
        verdict = "unavailable"
    elif terminal.get("verdict") == "useful_conditioned_trajectory":
        verdict = "pass"
    else:
        verdict = terminal.get("verdict", "unavailable")
    return {
        "all_registered_points_present": complete,
        "registered_point_count": len(expected),
        "completed_point_count": sum(
            row.get("verdict") != "unavailable"
            for row in indexed.values()
        ),
        "terminal_point": dict(terminal) if terminal is not None else None,
        "verdict": verdict,
    }


def _require_success(row: Mapping[str, Any]) -> None:
    if (
        row.get("timed_out") is True
        or row.get("returncode") != 0
        or row.get("host_limit_passed") is not True
    ):
        raise RuntimeError(
            f"fresh process failed: {row.get('label')}; "
            f"timed_out={row.get('timed_out')}, "
            f"returncode={row.get('returncode')}, "
            f"log={row.get('log_path')}"
        )


def _run_required(
    *,
    label: str,
    command: Sequence[str],
    output_directory: Path,
    processes: list[dict[str, Any]],
    timeout_seconds: int = POINT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    row = run_fresh_process(
        label=label,
        command=command,
        log_path=output_directory / f"{label}.log",
        timeout_seconds=timeout_seconds,
    )
    processes.append(row)
    _require_success(row)
    return row


def _conda_pytest(environment: str, *paths: str) -> list[str]:
    return [
        str(CONDA),
        "run",
        "--no-capture-output",
        "-n",
        environment,
        "python",
        "-s",
        "-m",
        "pytest",
        "-q",
        *paths,
    ]


def run_unit_and_corruption_controls(
    *,
    output_directory: Path,
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run all preregistered implementation/corruption tests before targets."""

    core_paths = (
        "tests/test_external_xzzx_record_fixture.py",
        "tests/test_external_xzzx_record_dense_reference.py",
        "tests/test_external_xzzx_record_exact_data_reference.py",
        "tests/test_external_xzzx_record_metrics.py",
        "tests/test_external_xzzx_record_runner.py",
    )
    core = _run_required(
        label="controls_core",
        command=_conda_pytest("ecs", *core_paths),
        output_directory=output_directory,
        processes=processes,
    )
    quimb = _run_required(
        label="controls_quimb",
        command=_conda_pytest(
            "ecs-baseline-quimb-peps",
            "tests/test_external_xzzx_record_quimb_candidate.py",
        ),
        output_directory=output_directory,
        processes=processes,
    )
    return {
        "status": "passed",
        "core_test_files": list(core_paths),
        "quimb_test_file": (
            "tests/test_external_xzzx_record_quimb_candidate.py"
        ),
        "process_log_sha256": {
            "core": core["log_sha256"],
            "quimb": quimb["log_sha256"],
        },
    }


def materialize_fixture(
    *,
    distance: int,
    output_directory: Path,
    processes: list[dict[str, Any]],
) -> dict[str, Path]:
    if distance not in EXPECTED_HASHES:
        raise ValueError("fixture distance is not registered")
    fixture = output_directory / f"d{distance}_fixture.json"
    stim = output_directory / f"d{distance}_circuit.stim"
    spec = output_directory / f"d{distance}_spec.json"
    _run_required(
        label=f"emit_d{distance}",
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/emit_xzzx_record_peps_fixture.py",
            "--distance",
            str(distance),
            "--rounds",
            "2",
            "--output-json",
            str(fixture),
            "--output-stim",
            str(stim),
            "--output-spec",
            str(spec),
        ),
        output_directory=output_directory,
        processes=processes,
        timeout_seconds=60,
    )
    observed = {
        "fixture": _file_sha256(fixture),
        "stim": _file_sha256(stim),
        "spec": _file_sha256(spec),
    }
    if observed != EXPECTED_HASHES[distance]:
        raise RuntimeError(
            f"materialized d{distance} bytes differ from freeze: {observed}"
        )
    return {"fixture": fixture, "stim": stim, "spec": spec}


def write_neutral_branch(
    *,
    reference_summary_path: Path,
    destination: Path,
) -> dict[str, Any]:
    """Publish the exact reference's seven-field neutral branch separately."""

    summary = _json_object(reference_summary_path)
    branch = summary.get("branch")
    authority = summary.get("branch_authority")
    expected_fields = {
        "schema",
        "fixture_sha256",
        "run_spec_sha256",
        "distance",
        "rounds",
        "branch_id",
        "outcomes",
    }
    if (
        not isinstance(branch, Mapping)
        or set(branch) != expected_fields
        or not isinstance(authority, Mapping)
        or authority.get("branch_sha256")
        != hashlib.sha256(
            (
                json.dumps(
                    branch,
                    allow_nan=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
        ).hexdigest()
    ):
        raise RuntimeError("exact summary lacks an authenticated neutral branch")
    _atomic_json(destination, branch)
    if _file_sha256(destination) != authority["branch_sha256"]:
        raise RuntimeError("published neutral branch hash mismatch")
    return dict(branch)


def compare_summaries(
    *,
    mode: str,
    reference_summary: Path,
    candidate_summary: Path,
    output_path: Path,
    label: str,
    output_directory: Path,
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    _run_required(
        label=label,
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/compare_xzzx_record_peps.py",
            "--mode",
            mode,
            "--reference-summary",
            str(reference_summary),
            "--candidate-summary",
            str(candidate_summary),
            "--output",
            str(output_path),
        ),
        output_directory=output_directory,
        processes=processes,
        timeout_seconds=300,
    )
    return _json_object(output_path)


def run_exact_reference(
    *,
    distance: int,
    mode: str,
    fixture: Path,
    run_spec: Path,
    output_directory: Path,
    processes: list[dict[str, Any]],
    parent_summary: Path | None = None,
) -> dict[str, Any]:
    if mode not in {"primary", "alternate"}:
        raise ValueError("exact reference mode is not registered")
    if (mode == "alternate") != (parent_summary is not None):
        raise ValueError("exact alternate requires exactly one primary parent")
    prefix = f"d{distance}_exact_{mode}"
    summary_path = output_directory / f"{prefix}.json"
    state_path = output_directory / f"{prefix}.npy"
    arguments = [
        "--fixture",
        str(fixture),
        "--run-spec",
        str(run_spec),
        "--mode",
        mode,
    ]
    if parent_summary is not None:
        arguments.extend(["--parent-summary", str(parent_summary)])
    arguments.extend(
        [
            "--output-summary",
            str(summary_path),
            "--output-state",
            str(state_path),
        ]
    )
    process = run_fresh_process(
        label=prefix,
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/xzzx_record_exact_data_reference.py",
            *arguments,
        ),
        log_path=output_directory / f"{prefix}.log",
        timeout_seconds=POINT_TIMEOUT_SECONDS,
    )
    processes.append(process)
    if (
        process["timed_out"]
        or process["returncode"] != 0
        or process["host_limit_passed"] is not True
        or not summary_path.is_file()
        or not state_path.is_file()
    ):
        return {
            "status": "unavailable",
            "distance": distance,
            "branch_role": mode,
            "reason": (
                "wall_timeout"
                if process["timed_out"]
                else (
                    "host_memory_limit"
                    if process["host_limit_passed"] is not True
                    else "exact_process_or_artifact_failure"
                )
            ),
            "process": process,
            "summary_path": None,
            "state_path": None,
            "branch_path": None,
        }
    summary = _json_object(summary_path)
    if summary.get("status") != "completed":
        return {
            "status": "unavailable",
            "distance": distance,
            "branch_role": mode,
            "reason": f"exact_status={summary.get('status')}",
            "process": process,
            "summary_path": str(summary_path),
            "state_path": str(state_path),
            "branch_path": None,
        }
    try:
        resources = validate_exact_resource_usage(summary)
    except RuntimeError as error:
        return {
            "status": "unavailable",
            "distance": distance,
            "branch_role": mode,
            "reason": f"exact_resource_gate:{error}",
            "process": process,
            "summary_path": str(summary_path),
            "state_path": str(state_path),
            "branch_path": None,
        }
    branch_path = output_directory / f"{prefix}_branch.json"
    branch = write_neutral_branch(
        reference_summary_path=summary_path,
        destination=branch_path,
    )
    authority = summary.get("branch_authority")
    if (
        not isinstance(authority, Mapping)
        or authority.get("role") != mode
    ):
        raise RuntimeError("exact branch role differs from requested mode")
    return {
        "status": "completed",
        "distance": distance,
        "branch_role": mode,
        "branch_id": branch["branch_id"],
        "summary_path": str(summary_path.resolve()),
        "summary_sha256": _file_sha256(summary_path),
        "state_path": str(state_path.resolve()),
        "state_sha256": _file_sha256(state_path),
        "branch_path": str(branch_path.resolve()),
        "branch_sha256": _file_sha256(branch_path),
        "resource_usage": resources,
        "process": process,
    }


def run_dense_d3(
    *,
    mode: str,
    fixture: Path,
    run_spec: Path,
    exact_primary_summary: Path,
    output_directory: Path,
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    if mode not in {"primary", "alternate"}:
        raise ValueError("dense d3 mode is not registered")
    prefix = f"d3_dense_{mode}"
    summary_path = output_directory / f"{prefix}.json"
    state_path = output_directory / f"{prefix}.npy"
    process = run_fresh_process(
        label=prefix,
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/xzzx_record_dense_reference.py",
            "--fixture",
            str(fixture),
            "--spec",
            str(run_spec),
            "--mode",
            mode,
            "--reference-summary",
            str(exact_primary_summary),
            "--output-json",
            str(summary_path),
            "--output-state",
            str(state_path),
        ),
        log_path=output_directory / f"{prefix}.log",
        timeout_seconds=POINT_TIMEOUT_SECONDS,
    )
    processes.append(process)
    if (
        process["timed_out"]
        or process["returncode"] != 0
        or process["host_limit_passed"] is not True
        or not summary_path.is_file()
        or not state_path.is_file()
    ):
        return {
            "status": "unavailable",
            "branch_role": mode,
            "reason": "dense_process_or_artifact_failure",
            "process": process,
            "summary_path": None,
            "state_path": None,
        }
    summary = _json_object(summary_path)
    if summary.get("status") != "completed":
        raise RuntimeError("dense d3 summary is not completed")
    return {
        "status": "completed",
        "branch_role": mode,
        "branch_id": summary["branch"]["branch_id"],
        "summary_path": str(summary_path.resolve()),
        "summary_sha256": _file_sha256(summary_path),
        "state_path": str(state_path.resolve()),
        "state_sha256": _file_sha256(state_path),
        "process": process,
    }


def run_d2_complete_law_gate(
    *,
    fixture: Path,
    run_spec: Path,
    output_directory: Path,
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    dense_summary = output_directory / "d2_dense_laws.json"
    _run_required(
        label="d2_dense_laws",
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/xzzx_record_dense_reference.py",
            "--fixture",
            str(fixture),
            "--spec",
            str(run_spec),
            "--mode",
            "tracer",
            "--output-json",
            str(dense_summary),
        ),
        output_directory=output_directory,
        processes=processes,
    )
    candidate_summary = output_directory / "d2_quimb_laws.json"
    candidate_process = run_fresh_process(
        label="d2_quimb_laws",
        command=_conda_python(
            "ecs-baseline-quimb-peps",
            "scripts/external_baselines/xzzx_record_quimb_candidate.py",
            "--fixture",
            str(fixture),
            "--run-spec",
            str(run_spec),
            "--enumerate-d2",
            "--D",
            "8",
            "--rdm-radius",
            "complete",
            "--output-summary",
            str(candidate_summary),
            "--device",
            "cuda",
            "--optimize",
            "auto-hq-serial",
        ),
        log_path=output_directory / "d2_quimb_laws.log",
        timeout_seconds=POINT_TIMEOUT_SECONDS,
    )
    processes.append(candidate_process)
    if (
        candidate_process["timed_out"]
        or candidate_process["returncode"] != 0
        or candidate_process["host_limit_passed"] is not True
        or not candidate_summary.is_file()
    ):
        return {
            "status": "unavailable",
            "passes": False,
            "reason": "d2_candidate_process_or_artifact_failure",
            "process": candidate_process,
            "dense_summary_sha256": _file_sha256(dense_summary),
        }
    candidate = _json_object(candidate_summary)
    try:
        resources = validate_resource_usage(candidate)
    except RuntimeError as error:
        return {
            "status": "unavailable",
            "passes": False,
            "reason": f"d2_resource_gate:{error}",
            "process": candidate_process,
            "dense_summary_sha256": _file_sha256(dense_summary),
            "candidate_summary_sha256": _file_sha256(candidate_summary),
        }
    comparison_path = output_directory / "d2_law_comparison.json"
    comparison = compare_summaries(
        mode="d2-tracer",
        reference_summary=dense_summary,
        candidate_summary=candidate_summary,
        output_path=comparison_path,
        label="d2_law_compare",
        output_directory=output_directory,
        processes=processes,
    )
    return {
        **comparison,
        "dense_summary_sha256": _file_sha256(dense_summary),
        "candidate_summary_sha256": _file_sha256(candidate_summary),
        "comparison_sha256": _file_sha256(comparison_path),
        "candidate_resource_usage": resources,
        "candidate_process": candidate_process,
    }


def _candidate_point(
    *,
    distance: int,
    branch_role: str,
    bond: int,
    radius: str | int,
    fixture: Path,
    run_spec: Path,
    branch: Path,
    exact_summary: Path,
    output_directory: Path,
    processes: list[dict[str, Any]],
) -> dict[str, Any]:
    prefix = f"d{distance}_{branch_role}_D{bond}_r{radius}"
    summary_path = output_directory / f"{prefix}_quimb.json"
    state_path = output_directory / f"{prefix}_quimb.npy"
    process = run_fresh_process(
        label=prefix,
        command=_conda_python(
            "ecs-baseline-quimb-peps",
            "scripts/external_baselines/xzzx_record_quimb_candidate.py",
            "--fixture",
            str(fixture),
            "--run-spec",
            str(run_spec),
            "--branch",
            str(branch),
            "--exact-reference-summary",
            str(exact_summary),
            "--D",
            str(bond),
            "--rdm-radius",
            str(radius),
            "--output-summary",
            str(summary_path),
            "--output-state",
            str(state_path),
            "--device",
            "cuda",
            "--optimize",
            "auto-hq-serial",
        ),
        log_path=output_directory / f"{prefix}.log",
        timeout_seconds=POINT_TIMEOUT_SECONDS,
    )
    processes.append(process)
    if (
        process["timed_out"]
        or process["returncode"] != 0
        or process["host_limit_passed"] is not True
        or not summary_path.is_file()
        or not state_path.is_file()
    ):
        return {
            "branch_role": branch_role,
            "bond_dimension": bond,
            "rdm_radius": radius,
            "fidelity": None,
            "verdict": "unavailable",
            "unavailable_reason": (
                "wall_timeout"
                if process["timed_out"]
                else (
                    "host_memory_limit"
                    if process["host_limit_passed"] is not True
                    else "candidate_process_or_artifact_failure"
                )
            ),
            "process": process,
        }
    summary = _json_object(summary_path)
    if summary.get("status") != "completed":
        return {
            "branch_role": branch_role,
            "bond_dimension": bond,
            "rdm_radius": radius,
            "fidelity": None,
            "verdict": "unavailable",
            "unavailable_reason": f"candidate_status={summary.get('status')}",
            "candidate_summary_sha256": _file_sha256(summary_path),
            "process": process,
        }
    try:
        resources = validate_resource_usage(summary)
    except RuntimeError as error:
        return {
            "branch_role": branch_role,
            "bond_dimension": bond,
            "rdm_radius": radius,
            "fidelity": None,
            "verdict": "unavailable",
            "unavailable_reason": f"resource_gate:{error}",
            "candidate_summary_sha256": _file_sha256(summary_path),
            "process": process,
        }
    remaining_seconds = int(
        math.floor(POINT_TIMEOUT_SECONDS - float(process["elapsed_seconds"]))
    )
    if remaining_seconds <= 0:
        return {
            "branch_role": branch_role,
            "bond_dimension": bond,
            "rdm_radius": radius,
            "fidelity": None,
            "verdict": "unavailable",
            "unavailable_reason": "point_wall_timeout_before_comparison",
            "candidate_summary_sha256": _file_sha256(summary_path),
            "resource_usage": resources,
            "process": process,
        }
    comparison_path = output_directory / f"{prefix}_comparison.json"
    comparison_process = run_fresh_process(
        label=f"{prefix}_compare",
        command=_conda_python(
            "ecs",
            "scripts/external_baselines/compare_xzzx_record_peps.py",
            "--mode",
            "selected",
            "--reference-summary",
            str(exact_summary),
            "--candidate-summary",
            str(summary_path),
            "--output",
            str(comparison_path),
        ),
        log_path=output_directory / f"{prefix}_compare.log",
        timeout_seconds=min(300, remaining_seconds),
    )
    processes.append(comparison_process)
    if (
        comparison_process["timed_out"]
        or comparison_process["returncode"] != 0
        or comparison_process["host_limit_passed"] is not True
        or not comparison_path.is_file()
    ):
        return {
            "branch_role": branch_role,
            "bond_dimension": bond,
            "rdm_radius": radius,
            "fidelity": None,
            "verdict": "unavailable",
            "unavailable_reason": "comparison_process_failure",
            "candidate_summary_sha256": _file_sha256(summary_path),
            "resource_usage": resources,
            "process": process,
            "comparison_process": comparison_process,
        }
    comparison = _json_object(comparison_path)
    if (
        comparison.get("branch_role") != branch_role
        or comparison.get("distance") != distance
        or comparison.get("bond_dimension") != bond
        or comparison.get("rdm_radius") != radius
    ):
        raise RuntimeError("comparison point identity differs from request")
    return {
        **comparison,
        "candidate_summary_sha256": _file_sha256(summary_path),
        "candidate_state_sha256": _file_sha256(state_path),
        "comparison_sha256": _file_sha256(comparison_path),
        "resource_usage": resources,
        "process": process,
        "comparison_process": comparison_process,
    }


def _artifact_manifest(
    output_directory: Path,
    *,
    exclude: Sequence[Path] = (),
) -> dict[str, Any]:
    excluded = {path.resolve() for path in exclude}
    files: dict[str, Any] = {}
    for path in sorted(output_directory.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"artifact bundle contains a symlink: {path}")
        metadata_before = path.lstat()
        if stat.S_ISDIR(metadata_before.st_mode):
            continue
        if (
            not stat.S_ISREG(metadata_before.st_mode)
            or path.resolve() in excluded
        ):
            raise RuntimeError(
                f"artifact bundle contains a non-regular entry: {path}"
            )
        relative = str(path.relative_to(output_directory))
        digest = _file_sha256(path)
        metadata_after = path.lstat()
        if (
            metadata_before.st_dev,
            metadata_before.st_ino,
            metadata_before.st_size,
            metadata_before.st_mtime_ns,
        ) != (
            metadata_after.st_dev,
            metadata_after.st_ino,
            metadata_after.st_size,
            metadata_after.st_mtime_ns,
        ):
            raise RuntimeError(f"artifact changed while hashing: {path}")
        files[relative] = {
            "bytes": metadata_after.st_size,
            "sha256": digest,
        }
    return {"file_count": len(files), "files": files}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    return parser.parse_args(argv)


def _publish_terminal_result(
    *,
    output_directory: Path,
    result: Mapping[str, Any],
    expected_frozen_inputs: Mapping[str, Any] | None = None,
) -> Path:
    destination = output_directory / "result.json"
    payload = copy.deepcopy(dict(result))
    manifest = _artifact_manifest(
        output_directory,
        exclude=(destination,),
    )
    if manifest != _artifact_manifest(
        output_directory,
        exclude=(destination,),
    ):
        raise RuntimeError("artifact bundle changed before publication")
    if (
        expected_frozen_inputs is not None
        and verify_frozen_inputs() != expected_frozen_inputs
    ):
        raise RuntimeError("frozen inputs changed at publication boundary")
    payload["artifact_manifest"] = manifest
    _atomic_json(destination, payload)
    print(json.dumps(payload, allow_nan=False, sort_keys=True), flush=True)
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        parent = args.output_directory.parent.resolve(strict=True)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"output parent does not exist: {args.output_directory.parent}"
        ) from error
    output_directory = parent / args.output_directory.name
    if os.path.lexists(output_directory):
        raise FileExistsError(
            f"output directory already exists: {output_directory}"
        )
    frozen = verify_frozen_inputs()
    review = verify_artifact_only_review(frozen)
    output_directory.mkdir()
    processes: list[dict[str, Any]] = []
    base_result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "status": "running",
        "claim_boundary": (
            "bounded all-qubit XZZX d2 complete law and selected d3/d5 "
            "two-round trajectories with coherent RY(0.02); no leakage, "
            "Kraus, decoded-LER, d5 full-law, or scalability claim"
        ),
        "execution_plan": execution_plan(),
        "resource_gate": {
            "point_wall_seconds": POINT_TIMEOUT_SECONDS,
            "host_rss_bytes": HOST_LIMIT_BYTES,
            "device_allocation_bytes": DEVICE_LIMIT_BYTES,
            "gpu_lock": str(GPU_LOCK),
            "child_environment": {
                key: child_environment()[key]
                for key in (
                    "CUDA_VISIBLE_DEVICES",
                    "CUDA_DEVICE_ORDER",
                    "ECS_GPU_SLOT",
                    "ECS_XZZX_REQUIRE_CUDA_CONTROLS",
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "PYTHONNOUSERSITE",
                )
            },
            "inherited_loader_and_conda_overrides_removed": True,
        },
        "provenance": {
            **frozen,
            "artifact_only_review": review,
            "runner_path": str(Path(__file__).resolve()),
            "runner_sha256": _file_sha256(Path(__file__).resolve()),
        },
        "processes": processes,
    }

    try:
        with GPU_LOCK.open("a+b") as gpu_lock:
            fcntl.flock(gpu_lock.fileno(), fcntl.LOCK_EX)
            controls = run_unit_and_corruption_controls(
                output_directory=output_directory,
                processes=processes,
            )
            if verify_frozen_inputs() != frozen:
                raise RuntimeError("frozen inputs changed during controls")

            fixtures = {
                distance: materialize_fixture(
                    distance=distance,
                    output_directory=output_directory,
                    processes=processes,
                )
                for distance in (2, 3, 5)
            }
            fixture_evidence = {
                str(distance): {
                    name: {
                        "path": str(path.resolve()),
                        "sha256": _file_sha256(path),
                    }
                    for name, path in paths.items()
                }
                for distance, paths in fixtures.items()
            }

            d2 = run_d2_complete_law_gate(
                fixture=fixtures[2]["fixture"],
                run_spec=fixtures[2]["spec"],
                output_directory=output_directory,
                processes=processes,
            )

            exact_references: dict[str, dict[str, Any]] = {}
            dense_references: dict[str, dict[str, Any]] = {}
            exact_dense: dict[str, dict[str, Any]] = {
                role: {
                    "status": "unavailable",
                    "passes": False,
                    "reason": "not_run",
                }
                for role in D3_BRANCHES
            }
            primary = run_exact_reference(
                distance=3,
                mode="primary",
                fixture=fixtures[3]["fixture"],
                run_spec=fixtures[3]["spec"],
                output_directory=output_directory,
                processes=processes,
            )
            exact_references["primary"] = primary
            if primary["status"] == "completed":
                primary_summary = Path(primary["summary_path"])
                dense_primary = run_dense_d3(
                    mode="primary",
                    fixture=fixtures[3]["fixture"],
                    run_spec=fixtures[3]["spec"],
                    exact_primary_summary=primary_summary,
                    output_directory=output_directory,
                    processes=processes,
                )
                dense_references["primary"] = dense_primary
                if dense_primary["status"] == "completed":
                    comparison_path = (
                        output_directory
                        / "d3_primary_exact_dense_comparison.json"
                    )
                    exact_dense["primary"] = compare_summaries(
                        mode="d3-exact-dense",
                        reference_summary=primary_summary,
                        candidate_summary=Path(
                            dense_primary["summary_path"]
                        ),
                        output_path=comparison_path,
                        label="d3_primary_exact_dense_compare",
                        output_directory=output_directory,
                        processes=processes,
                    )
                    exact_dense["primary"]["comparison_sha256"] = (
                        _file_sha256(comparison_path)
                    )

                alternate = run_exact_reference(
                    distance=3,
                    mode="alternate",
                    fixture=fixtures[3]["fixture"],
                    run_spec=fixtures[3]["spec"],
                    parent_summary=primary_summary,
                    output_directory=output_directory,
                    processes=processes,
                )
                exact_references["alternate"] = alternate
                dense_alternate = run_dense_d3(
                    mode="alternate",
                    fixture=fixtures[3]["fixture"],
                    run_spec=fixtures[3]["spec"],
                    exact_primary_summary=primary_summary,
                    output_directory=output_directory,
                    processes=processes,
                )
                dense_references["alternate"] = dense_alternate
                if (
                    alternate["status"] == "completed"
                    and dense_alternate["status"] == "completed"
                ):
                    comparison_path = (
                        output_directory
                        / "d3_alternate_exact_dense_comparison.json"
                    )
                    exact_dense["alternate"] = compare_summaries(
                        mode="d3-exact-dense",
                        reference_summary=Path(
                            alternate["summary_path"]
                        ),
                        candidate_summary=Path(
                            dense_alternate["summary_path"]
                        ),
                        output_path=comparison_path,
                        label="d3_alternate_exact_dense_compare",
                        output_directory=output_directory,
                        processes=processes,
                    )
                    exact_dense["alternate"]["comparison_sha256"] = (
                        _file_sha256(comparison_path)
                    )
            else:
                exact_references["alternate"] = {
                    "status": "unavailable",
                    "branch_role": "alternate",
                    "reason": "primary_exact_reference_unavailable",
                }

            d3_points: list[dict[str, Any]] = []
            pre_d3_candidate_gate = (
                d2.get("passes") is True
                and all(
                    exact_dense[role].get("passes") is True
                    for role in D3_BRANCHES
                )
            )
            for role in D3_BRANCHES:
                reference = exact_references[role]
                if (
                    not pre_d3_candidate_gate
                    or reference.get("status") != "completed"
                ):
                    d3_points.extend(
                        {
                            "distance": 3,
                            "branch_role": role,
                            "bond_dimension": bond,
                            "rdm_radius": "complete",
                            "fidelity": None,
                            "verdict": "unavailable",
                            "unavailable_reason": (
                                "pre_d3_candidate_gate_failed"
                                if not pre_d3_candidate_gate
                                else "exact_reference_unavailable"
                            ),
                        }
                        for bond in D3_BONDS
                    )
                    continue
                for bond in D3_BONDS:
                    d3_points.append(
                        _candidate_point(
                            distance=3,
                            branch_role=role,
                            bond=bond,
                            radius="complete",
                            fixture=fixtures[3]["fixture"],
                            run_spec=fixtures[3]["spec"],
                            branch=Path(reference["branch_path"]),
                            exact_summary=Path(reference["summary_path"]),
                            output_directory=output_directory,
                            processes=processes,
                        )
                    )

            d3_gate = evaluate_d3_gate(
                control_processes_passed=controls["status"] == "passed",
                d2_comparison=d2,
                exact_dense_comparisons=exact_dense,
                d3_points=d3_points,
            )
            if verify_frozen_inputs() != frozen:
                raise RuntimeError("frozen inputs changed before d5 gate")

            result = {
                **base_result,
                "status": "completed",
                "controls": controls,
                "fixtures": fixture_evidence,
                "d2_complete_law": d2,
                "d3_exact_references": exact_references,
                "d3_dense_references": dense_references,
                "d3_exact_dense_comparisons": exact_dense,
                "d3_points": d3_points,
                "d3_authorization_gate": d3_gate,
                "d5_authorized": d3_gate["passes"],
            }
            if not d3_gate["passes"]:
                result["d5_reference"] = {
                    "status": "not_run",
                    "reason": "d3_authorization_gate_failed",
                }
                result["d5_points"] = []
                result["d5_summary"] = {
                    "all_registered_points_present": False,
                    "registered_point_count": 12,
                    "completed_point_count": 0,
                    "terminal_point": None,
                    "verdict": "unavailable",
                }
                result["terminal_verdict"] = "d5_blocked_by_pretarget_gate"
                if verify_frozen_inputs() != frozen:
                    raise RuntimeError(
                        "frozen inputs changed before terminal publication"
                    )
                _publish_terminal_result(
                    output_directory=output_directory,
                    result=result,
                    expected_frozen_inputs=frozen,
                )
                return 0

            d5_reference = run_exact_reference(
                distance=5,
                mode="primary",
                fixture=fixtures[5]["fixture"],
                run_spec=fixtures[5]["spec"],
                output_directory=output_directory,
                processes=processes,
            )
            d5_points: list[dict[str, Any]] = []
            if d5_reference["status"] == "completed":
                for bond in D5_BONDS:
                    for radius in D5_RADII:
                        d5_points.append(
                            _candidate_point(
                                distance=5,
                                branch_role="primary",
                                bond=bond,
                                radius=radius,
                                fixture=fixtures[5]["fixture"],
                                run_spec=fixtures[5]["spec"],
                                branch=Path(d5_reference["branch_path"]),
                                exact_summary=Path(
                                    d5_reference["summary_path"]
                                ),
                                output_directory=output_directory,
                                processes=processes,
                            )
                        )
            d5_summary = summarize_d5(d5_points)
            result.update(
                {
                    "d5_reference": d5_reference,
                    "d5_points": d5_points,
                    "d5_summary": d5_summary,
                    "terminal_verdict": d5_summary["verdict"],
                }
            )
            if verify_frozen_inputs() != frozen:
                raise RuntimeError(
                    "frozen inputs changed before terminal publication"
                )
            _publish_terminal_result(
                output_directory=output_directory,
                result=result,
                expected_frozen_inputs=frozen,
            )
            return 0
    except Exception as error:
        failure = {
            **base_result,
            "status": "invalid",
            "terminal_verdict": "operational_failure",
            "failure": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }
        destination = output_directory / "result.json"
        if not os.path.lexists(destination):
            _publish_terminal_result(
                output_directory=output_directory,
                result=failure,
                expected_frozen_inputs=frozen,
            )
        raise


if __name__ == "__main__":
    raise SystemExit(main())

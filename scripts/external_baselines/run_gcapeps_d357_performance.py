#!/usr/bin/env python3
"""Supervise the frozen GCAPEPS d=3/5/7 performance-only sweep.

The supervisor has two explicit modes. ``controls-only`` emits and validates
all neutral fixtures, runs the three untimed SDIM signed-pullback checks, and
runs one fresh d=3 process per candidate as an excluded control.
``target`` consumes a sealed controls bundle and attempts the preregistered
fresh-process population. Candidate failures are retained as censored rows;
they never silently remove a requested distance or create a finite ratio.

This module reuses the already reviewed n=8 supervisor's fresh-clone,
locked-Pixi, systemd-cgroup, and atomic-directory publication mechanics. It
does not import either candidate implementation into the supervisor process.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping, Sequence
import uuid


CONTROLS_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_d357_depth_complexity_probability_controls_only.v2"
)
RESULT_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_d357_depth_complexity_probability_performance.v2"
)
PLAIN_WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_d357_plain_quimb_worker.v2"
)
GCAPEPS_WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_d357_gcapeps_worker.v2"
)
SDIM_WORKER_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_d357_sdim_accumulated_pullback_control.v2"
)
DISTANCES = (3, 5, 7)
LANES = ("plain", "gcapeps")
WARMUP_ORDER = ("plain", "gcapeps")
MEASURED_ORDER = (
    "plain",
    "gcapeps",
    "gcapeps",
    "plain",
    "plain",
    "gcapeps",
)
GRID_ROLE_SPECS = (
    ("baseline", 1, 1, 1e-3),
    ("depth-2", 2, 1, 1e-3),
    ("depth-d", "distance", 1, 1e-3),
    ("complexity-2", 1, 2, 1e-3),
    ("complexity-4", 1, 4, 1e-3),
    ("low-probability", 1, 1, 1e-4),
    ("high-probability", 1, 1, 1e-2),
    ("stress-corner", "distance", 4, 1e-2),
)
EXPECTED_FIXTURE_SHA256 = {
    3: "1b039174dc8b657efcb398cf0b9cfc29556e14e088a7a898b2824880407c420d",
    5: "ebafd1ef5f7f86cf55bb792dcf191c3c96fa8c8b02f6836cde7fba960385eac3",
    7: "727ec6d223a32a5d855df952a88abaa122ce0f20ce4c014af6a921396ea73f9a",
}
EXPECTED_FORK_COMMIT = "6fbbf74cd36686ed30a4d8865697ce46e47056c1"
EXPECTED_FORK_TREE = "ffdfdf421fbe4d9674c2c88029710042fd18ae14"
WORKER_RESOURCE_ENVELOPE = {
    "MemoryMax": 8 * 1024**3,
    "MemorySwapMax": 0,
    "RuntimeMaxSec": 300,
    "TasksMax": 32,
}

_SCRIPT_PATH = Path(__file__).resolve()
_REPO_ROOT = _SCRIPT_PATH.parents[2]
_SCRIPT_DIR = _SCRIPT_PATH.parent
_FOUNDATION_PATH = _SCRIPT_DIR / "run_gcapeps_n8_r3_differential.py"
_EMITTER_PATH = (
    _SCRIPT_DIR / "emit_gcapeps_d357_unitary_prefix_fixture.py"
)
_PLAIN_WORKER_PATH = _SCRIPT_DIR / "plain_quimb_d357_worker.py"
_GC_WORKER_PATH = _SCRIPT_DIR / "gcapeps_d357_worker.py"
_SDIM_WORKER_PATH = _SCRIPT_DIR / "gcapeps_d357_sdim_worker.py"
_TEST_PATH = _REPO_ROOT / "tests/test_external_gcapeps_d357_runner.py"
_FIXTURE_TEST_PATH = _REPO_ROOT / "tests/test_external_gcapeps_d357_fixture.py"
_WORKERS_TEST_PATH = _REPO_ROOT / "tests/test_external_gcapeps_d357_workers.py"
_SDIM_TEST_PATH = _REPO_ROOT / "tests/test_external_gcapeps_d357_sdim_worker.py"
_CLOSURE_PATH = (
    _REPO_ROOT
    / "docs/simulator_validation/"
    "GCAPEPS_D357_UNITARY_PREFIX_PERFORMANCE_LITERATURE_CLOSURE_2026-07-29.md"
)
_PREREG_PATH = (
    _REPO_ROOT
    / "docs/simulator_validation/"
    "GCAPEPS_D357_UNITARY_PREFIX_PERFORMANCE_PREREG_2026-07-29.md"
)
_GRID_CLOSURE_PATH = (
    _REPO_ROOT
    / "docs/simulator_validation/"
    "GCAPEPS_D357_DEPTH_COMPLEXITY_PROBABILITY_LITERATURE_CLOSURE_2026-07-29.md"
)
_GRID_PREREG_PATH = (
    _REPO_ROOT
    / "docs/simulator_validation/"
    "GCAPEPS_D357_DEPTH_COMPLEXITY_PROBABILITY_PREREG_2026-07-29.md"
)
DEFAULT_FORK_SOURCE = _REPO_ROOT / "external/forks/quimb-gcapeps"
DEFAULT_PIXI_EXECUTABLE = Path(
    "/home/cx/miniforge3/pkgs/pixi-0.72.2-ha759004_0/bin/pixi"
)
DEFAULT_SDIM_PYTHON = Path(
    "/home/cx/miniforge3/envs/gcapeps-sdim/bin/python3.12"
)
CLAIM_BEARING_PATHS = (
    _EMITTER_PATH,
    _PLAIN_WORKER_PATH,
    _GC_WORKER_PATH,
    _SDIM_WORKER_PATH,
    _SCRIPT_PATH,
    _TEST_PATH,
    _FIXTURE_TEST_PATH,
    _WORKERS_TEST_PATH,
    _SDIM_TEST_PATH,
    _CLOSURE_PATH,
    _PREREG_PATH,
    _GRID_CLOSURE_PATH,
    _GRID_PREREG_PATH,
    _FOUNDATION_PATH,
)

_FOUNDATION: Any | None = None


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.resolve(strict=True).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _reject_duplicate_pairs(
    pairs: Sequence[tuple[str, Any]],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate JSON key: {key!r}")
        output[key] = value
    return output


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def load_strict_json(path: Path, *, canonical: bool = False) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    raw = resolved.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid strict JSON artifact: {resolved}") from exc
    if not isinstance(value, dict):
        raise ValueError("JSON artifact must contain one object")
    if canonical and raw != canonical_json_bytes(value):
        raise ValueError(f"JSON artifact is not canonical: {resolved}")
    return value


def _load_script(path: Path, module_name: str) -> Any:
    source = path.resolve(strict=True)
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_foundation() -> Any:
    """Load the reviewed generic process/publication foundation once."""

    global _FOUNDATION
    if _FOUNDATION is None:
        _FOUNDATION = _load_script(
            _FOUNDATION_PATH,
            f"_gcapeps_d357_foundation_{uuid.uuid4().hex}",
        )
    expected = WORKER_RESOURCE_ENVELOPE
    if _FOUNDATION.WORKER_RESOURCE_ENVELOPE != expected:
        raise RuntimeError("shared worker resource envelope drifted")
    if (
        _FOUNDATION.EXPECTED_FORK_COMMIT != EXPECTED_FORK_COMMIT
        or _FOUNDATION.EXPECTED_FORK_TREE != EXPECTED_FORK_TREE
    ):
        raise RuntimeError("shared frozen-fork identity drifted")
    return _FOUNDATION


def _git_value(root: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    value = process.stdout.strip()
    if not value or "\n" in value:
        raise RuntimeError("Git identity command did not return one scalar")
    return value


def claim_bearing_source_hashes() -> dict[str, str]:
    return {
        path.resolve(strict=True).relative_to(_REPO_ROOT).as_posix():
        _sha256_file(path)
        for path in CLAIM_BEARING_PATHS
    }


def verify_committed_parent_checkout(
    repo_root: Path = _REPO_ROOT,
) -> dict[str, Any]:
    """Require every d357 owner/helper to be tracked at one clean HEAD."""

    lexical = repo_root.absolute()
    root = lexical.resolve(strict=True)
    if lexical != root or not root.is_dir():
        raise RuntimeError("parent checkout must be one nonsymlink directory")
    top = Path(_git_value(root, "rev-parse", "--show-toplevel")).resolve(
        strict=True
    )
    if top != root:
        raise RuntimeError("parent checkout is not its Git top level")
    status = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if status:
        raise RuntimeError("parent checkout must be clean before controls/target")
    relative = [
        path.resolve(strict=True).relative_to(root).as_posix()
        for path in CLAIM_BEARING_PATHS
    ]
    subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", *relative],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "root": str(root),
        "commit": _git_value(root, "rev-parse", "HEAD^{commit}"),
        "tree": _git_value(root, "rev-parse", "HEAD^{tree}"),
        "clean_including_untracked": True,
        "claim_bearing_source_sha256": claim_bearing_source_hashes(),
    }


def warmup_launch_order() -> tuple[str, ...]:
    return WARMUP_ORDER


def measured_launch_order() -> tuple[str, ...]:
    return MEASURED_ORDER


def frozen_grid_cells() -> list[dict[str, Any]]:
    """Return the 24 preregistered cells in exact execution order."""

    cells: list[dict[str, Any]] = []
    for distance in DISTANCES:
        for role, layer_spec, noise_complexity, probability in GRID_ROLE_SPECS:
            round_layers = (
                distance if layer_spec == "distance" else int(layer_spec)
            )
            p_twirl = float(probability)
            theta = float(2.0 * math.asin(math.sqrt(p_twirl)))
            cells.append(
                {
                    "distance": distance,
                    "cell_id": f"d{distance}-{role}",
                    "role": role,
                    "round_layers": round_layers,
                    "noise_complexity": noise_complexity,
                    "p_twirl": p_twirl,
                    "p_twirl_float64_hex": p_twirl.hex(),
                    "theta_radians": theta,
                    "theta_float64_hex": theta.hex(),
                    "expected_rotation_count": (
                        round_layers * noise_complexity
                    ),
                }
            )
    return cells


def frozen_grid_cell(distance: int, cell_id: str) -> dict[str, Any]:
    matches = [
        cell
        for cell in frozen_grid_cells()
        if cell["distance"] == distance and cell["cell_id"] == cell_id
    ]
    if len(matches) != 1:
        raise ValueError("cell is outside the frozen 24-cell grid")
    return matches[0]


def target_launch_plan() -> list[dict[str, Any]]:
    """Return all 192 preregistered fresh-process launches in order."""

    plan: list[dict[str, Any]] = []
    for cell in frozen_grid_cells():
        for lane in WARMUP_ORDER:
            plan.append(
                {
                    "distance": cell["distance"],
                    "cell_id": cell["cell_id"],
                    "lane": lane,
                    "sample_kind": "warmup",
                    "sample_index": 0,
                }
            )
        next_index = {"plain": 0, "gcapeps": 0}
        for lane in MEASURED_ORDER:
            sample_index = next_index[lane]
            next_index[lane] += 1
            plan.append(
                {
                    "distance": cell["distance"],
                    "cell_id": cell["cell_id"],
                    "lane": lane,
                    "sample_kind": "measured",
                    "sample_index": sample_index,
                }
            )
    return plan


def _positive_samples(
    values: Sequence[int],
    *,
    expected_count: int,
    label: str,
) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{label} must be a sequence")
    samples = tuple(values)
    if len(samples) != expected_count:
        raise ValueError(
            f"{label} must contain exactly {expected_count} samples"
        )
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
        for value in samples
    ):
        raise ValueError(f"{label} samples must be positive integers")
    return samples


def median_and_mad(
    values: Sequence[int],
    *,
    expected_count: int = 3,
    label: str = "samples",
) -> dict[str, Any]:
    samples = _positive_samples(
        values,
        expected_count=expected_count,
        label=label,
    )
    median = float(statistics.median(samples))
    deviations = [abs(float(value) - median) for value in samples]
    mad = float(statistics.median(deviations))
    if not math.isfinite(median) or not math.isfinite(mad):
        raise ValueError(f"{label} summary is nonfinite")
    return {"raw": list(samples), "median": median, "mad": mad}


def _metric_pair(
    plain: Sequence[int],
    gcapeps: Sequence[int],
    *,
    eligible: bool,
    label: str,
) -> dict[str, Any]:
    plain_summary = median_and_mad(
        plain, expected_count=3, label=f"plain {label}"
    )
    gc_summary = median_and_mad(
        gcapeps, expected_count=3, label=f"GCAPEPS {label}"
    )
    denominator = gc_summary["median"]
    ratio = (
        plain_summary["median"] / denominator
        if eligible and denominator > 0.0
        else None
    )
    return {
        "plain": plain_summary,
        "gcapeps": gc_summary,
        "ratio_plain_over_gcapeps": ratio,
        "ratio_eligible": eligible,
    }


METRIC_FIELDS = (
    "update_ns",
    "peak_rss_bytes",
    "cgroup_memory_peak_bytes",
    "maximum_bond_dimension",
    "total_tensor_elements",
    "logical_tensor_bytes",
)


def summarize_cell(
    *,
    distance: int,
    cell_id: str,
    runs: Sequence[Mapping[str, Any]],
    controls_passed: bool,
) -> dict[str, Any]:
    """Summarize one frozen cell without imputing censored samples."""

    cell = frozen_grid_cell(distance, cell_id)
    if not isinstance(controls_passed, bool):
        raise TypeError("controls_passed must be boolean")
    selected = [
        row
        for row in runs
        if row.get("distance") == distance and row.get("cell_id") == cell_id
    ]
    expected_specs = [
        row
        for row in target_launch_plan()
        if row["distance"] == distance and row["cell_id"] == cell_id
    ]
    identity_keys = (
        "distance",
        "cell_id",
        "lane",
        "sample_kind",
        "sample_index",
    )
    observed_specs = [
        {key: row.get(key) for key in identity_keys}
        for row in selected
    ]
    if observed_specs != expected_specs:
        raise ValueError(f"{cell_id} launch population/order drifted")

    lane_status: dict[str, Any] = {}
    successful_measured: dict[str, list[Mapping[str, Any]]] = {}
    for lane in LANES:
        lane_rows = [row for row in selected if row["lane"] == lane]
        warmup = [
            row for row in lane_rows if row["sample_kind"] == "warmup"
        ]
        measured = [
            row for row in lane_rows if row["sample_kind"] == "measured"
        ]
        successful = [
            row for row in measured if row.get("status") == "completed"
        ]
        successful_measured[lane] = successful
        completed = bool(
            len(warmup) == 1
            and warmup[0].get("status") == "completed"
            and len(successful) == 3
            and len(measured) == 3
        )
        lane_status[lane] = {
            "status": "completed" if completed else "censored",
            "warmup_completed": bool(
                len(warmup) == 1
                and warmup[0].get("status") == "completed"
            ),
            "measured_completed": len(successful),
            "measured_requested": 3,
            "censored_rows": [
                {
                    "sample_kind": row["sample_kind"],
                    "sample_index": row["sample_index"],
                    "censor_reason": row.get("censor_reason"),
                }
                for row in lane_rows
                if row.get("status") != "completed"
            ],
        }

    eligible = bool(
        controls_passed
        and all(lane_status[lane]["status"] == "completed" for lane in LANES)
    )
    metrics: dict[str, Any] | None = None
    if eligible:
        metrics = {}
        for field in METRIC_FIELDS:
            metrics[field] = _metric_pair(
                [
                    int(row["validated"][field])
                    for row in successful_measured["plain"]
                ],
                [
                    int(row["validated"][field])
                    for row in successful_measured["gcapeps"]
                ],
                eligible=True,
                label=field,
            )
    return {
        **cell,
        "fixture_sha256": EXPECTED_FIXTURE_SHA256[distance],
        "lane_status": lane_status,
        "joint_ratio_eligible": eligible,
        "metrics": metrics,
        "raw_launch_rows": [compact_run_row(row) for row in selected],
        "no_interaction_or_asymptotic_fit_performed": True,
    }


def compact_run_row(run: Mapping[str, Any]) -> dict[str, Any]:
    output = {
        key: run.get(key)
        for key in (
            "distance",
            "cell_id",
            "lane",
            "sample_kind",
            "sample_index",
            "status",
            "censor_reason",
        )
    }
    if run.get("status") == "completed":
        output["validated"] = {
            field: run["validated"][field] for field in METRIC_FIELDS
        }
        output["validated_progress"] = {
            key: run["validated"][key]
            for key in (
                "persistent_state_instances",
                "prefix_batches_completed",
                "completed_layers",
                "completed_rotations",
                "attempted_rotations",
            )
        }
    elif run.get("structured_censor") is not None:
        output["structured_censor"] = run["structured_censor"]
    process = run.get("process")
    if not isinstance(process, Mapping):
        process = {}
    output["process_returncode"] = process.get("returncode")
    output["process_elapsed_ns"] = process.get(
        "launch_and_process_elapsed_ns"
    )
    output["worker_output_sha256"] = run.get("output_sha256")
    return output


def execute_target_population(
    launch: Callable[..., Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Attempt every planned row, retaining per-row exceptions as censoring."""

    rows: list[dict[str, Any]] = []
    for spec in target_launch_plan():
        try:
            observed = dict(launch(**spec))
            row = {**spec, **observed}
            if row.get("status") not in {"completed", "censored"}:
                raise ValueError("launcher returned an unsupported status")
        except Exception as exc:
            row = {
                **spec,
                "status": "censored",
                "censor_reason": (
                    f"launcher_exception:{type(exc).__name__}:{exc}"
                ),
                "process": None,
            }
        rows.append(row)
    return rows


def emitter_command(
    *,
    python_executable: Path,
    distance: int,
    output_json: Path,
    output_stim: Path,
) -> list[str]:
    if distance not in DISTANCES:
        raise ValueError("fixture distance is outside the frozen sweep")
    return [
        str(python_executable),
        "-I",
        "-B",
        str(_EMITTER_PATH),
        "--distance",
        str(distance),
        "--output-json",
        str(output_json),
        "--output-stim",
        str(output_stim),
    ]


def candidate_worker_command(
    *,
    lane: str,
    python_executable: Path,
    fixture_path: Path,
    cell_id: str,
    fork_checkout: Path,
    output_json: Path,
) -> list[str]:
    if lane not in LANES:
        raise ValueError("candidate lane must be plain or gcapeps")
    if not any(cell["cell_id"] == cell_id for cell in frozen_grid_cells()):
        raise ValueError("candidate cell is outside the frozen grid")
    script = _PLAIN_WORKER_PATH if lane == "plain" else _GC_WORKER_PATH
    return [
        str(python_executable),
        "-s",
        "-B",
        str(script),
        "--fixture",
        str(fixture_path),
        "--cell-id",
        cell_id,
        "--fork-checkout",
        str(fork_checkout),
        "--output",
        str(output_json),
    ]


def sdim_worker_command(
    *,
    sdim_python: Path,
    fixture_path: Path,
    output_json: Path,
) -> list[str]:
    return [
        str(sdim_python),
        "-I",
        "-B",
        str(_SDIM_WORKER_PATH),
        "--fixture",
        str(fixture_path),
        "--output",
        str(output_json),
    ]


def _classify_censor(process: Mapping[str, Any]) -> str:
    text = (
        str(process.get("stdout", ""))
        + "\n"
        + str(process.get("stderr", ""))
    ).lower()
    if "oom" in text or "memorymax" in text or "out of memory" in text:
        return "memory_limit_or_oom"
    if "timeout" in text or "runtimemax" in text or "timed out" in text:
        return "wall_time_limit"
    if "resource guard" in text or "resource_guard" in text:
        return "exact_construction_resource_guard"
    return f"worker_nonzero_exit_{process.get('returncode')}"


def _private_subdirectory(
    foundation: Any,
    parent: Path,
    name: str,
) -> Path:
    return foundation._private_subdirectory(parent, name)


def _worker_environment(
    foundation: Any,
    *,
    python_executable: Path,
    private_root: Path,
) -> dict[str, str]:
    prefix = python_executable.resolve(strict=True).parent.parent
    return foundation._worker_environment_for_prefix(prefix, private_root)


def _run_systemd_worker(
    *,
    foundation: Any,
    unit_prefix: str,
    worker_command: Sequence[str],
    environment: Mapping[str, str],
    cpu_id: int,
    working_directory: Path,
) -> dict[str, Any]:
    unit_name = f"{unit_prefix}-{uuid.uuid4().hex[:12]}"
    command = foundation.build_systemd_worker_command(
        unit_name=unit_name,
        cpu_id=cpu_id,
        worker_command=worker_command,
        worker_environment=environment,
        working_directory=working_directory,
    )
    try:
        process = foundation._run_captured(
            command,
            cwd=working_directory,
            environment=environment,
            timeout_seconds=WORKER_RESOURCE_ENVELOPE["RuntimeMaxSec"] + 30,
            require_success=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr
        process = {
            "command": command,
            "cwd": str(working_directory.resolve(strict=True)),
            "returncode": -1,
            "launch_and_process_elapsed_ns": (
                WORKER_RESOURCE_ENVELOPE["RuntimeMaxSec"] + 30
            ) * 1_000_000_000,
            "stdout": stdout or "",
            "stderr": (stderr or "") + "\nsupervisor subprocess timeout",
            "stdout_sha256": hashlib.sha256((stdout or "").encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(
                ((stderr or "") + "\nsupervisor subprocess timeout").encode()
            ).hexdigest(),
        }
    process["unit_name"] = unit_name
    return process


def _require_positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _forbidden_numeric_payload_keys(value: Any) -> list[str]:
    """Find data-bearing truth surfaces, while allowing explicit false flags."""

    forbidden: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in {
                "state_vector",
                "statevector",
                "amplitudes",
                "norm_value",
                "fidelity_value",
                "born_probability",
                "record_batch",
            }:
                forbidden.append(str(key))
            forbidden.extend(_forbidden_numeric_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            forbidden.extend(_forbidden_numeric_payload_keys(item))
    return forbidden


def validate_candidate_report(
    report: Mapping[str, Any],
    *,
    lane: str,
    cell_id: str,
    fixture: Mapping[str, Any],
    fixture_sha256: str,
    cpu_id: int,
    fork_checkout: Path,
) -> dict[str, int]:
    """Validate one successful candidate report and extract only metrics."""

    if lane not in LANES:
        raise ValueError("candidate lane drifted")
    expected_schema = (
        PLAIN_WORKER_SCHEMA if lane == "plain" else GCAPEPS_WORKER_SCHEMA
    )
    expected_lane = (
        "plain_quimb_persistent_physical_layers_plus_local_ry"
        if lane == "plain"
        else "gcapeps_persistent_live_frame_plus_rank2_tree_residual"
    )
    if (
        report.get("schema") != expected_schema
        or report.get("status") != "completed"
        or report.get("lane") != expected_lane
    ):
        raise ValueError(f"{lane} worker headline identity drifted")
    frozen_cell = frozen_grid_cell(int(fixture["distance"]), cell_id)
    fixture_cells = fixture.get("grid_cells")
    matching_cells = (
        [row for row in fixture_cells if row.get("cell_id") == cell_id]
        if isinstance(fixture_cells, list)
        else []
    )
    if len(matching_cells) != 1:
        raise ValueError(f"{lane} fixture cell binding drifted")
    fixture_cell = matching_cells[0]
    frozen_to_fixture = {
        "role": frozen_cell["role"],
        "round_layers": frozen_cell["round_layers"],
        "noise_complexity": frozen_cell["noise_complexity"],
        "p_twirl": frozen_cell["p_twirl"],
        "p_twirl_float64_hex": frozen_cell["p_twirl_float64_hex"],
        "theta_radians": frozen_cell["theta_radians"],
        "theta_float64_hex": frozen_cell["theta_float64_hex"],
        "prefix_application_count": frozen_cell["round_layers"],
        "rotation_count": frozen_cell["expected_rotation_count"],
    }
    if any(fixture_cell.get(key) != value for key, value in frozen_to_fixture.items()):
        raise ValueError(f"{lane} frozen grid cell parameters drifted")
    locations = fixture.get("error_locations")
    expected_targets = (
        [row.get("target") for row in locations[: frozen_cell["noise_complexity"]]]
        if isinstance(locations, list)
        else []
    )
    if fixture_cell.get("selected_targets") != expected_targets:
        raise ValueError(f"{lane} frozen error-site order drifted")
    fixture_row = report.get("fixture")
    if (
        not isinstance(fixture_row, Mapping)
        or fixture_row.get("canonical_sha256") != fixture_sha256
        or fixture_row.get("distance") != fixture["distance"]
        or fixture_row.get("n_qubits") != fixture["n_qubits"]
        or fixture_row.get("dtype") != "complex128"
        or fixture_row.get("prefix_stream_sha256")
        != fixture["prefix"]["gate_stream_sha256"]
    ):
        raise ValueError(f"{lane} worker fixture binding drifted")
    expected_report_binding = {
        "schema": fixture["schema"],
        "fixture_id": fixture["fixture_id"],
        "prefix_gate_count": fixture["prefix"]["gate_count"],
        "graph_edge_count": fixture["graph"]["edge_count"],
        "graph_edge_stream_sha256": fixture["graph"]["edge_stream_sha256"],
        "grid_cells_sha256": fixture["grid_cells_sha256"],
        "cell_id": cell_id,
        "role": fixture_cell["role"],
        "round_layers": fixture_cell["round_layers"],
        "noise_complexity": fixture_cell["noise_complexity"],
        "p_twirl": fixture_cell["p_twirl"],
        "p_twirl_float64_hex": fixture_cell["p_twirl_float64_hex"],
        "theta_radians": fixture_cell["theta_radians"],
        "theta_float64_hex": fixture_cell["theta_float64_hex"],
        "selected_targets": fixture_cell["selected_targets"],
        "expected_rotation_count": fixture_cell["rotation_count"],
    }
    if any(
        fixture_row.get(key) != value
        for key, value in expected_report_binding.items()
    ):
        raise ValueError(f"{lane} worker cell identity drifted")
    if lane == "gcapeps" and fixture_row.get(
        "accumulated_frame_schedule_sha256"
    ) != fixture["accumulated_frame_schedule"]["schedule_sha256"]:
        raise ValueError("GCAPEPS accumulated-frame binding drifted")
    if report.get("numerical_settings") != {
        "dtype": "complex128",
        **fixture["peps_settings"],
    }:
        raise ValueError(f"{lane} worker numerical settings drifted")

    rotation = report.get("rotation")
    expected_rotation = {
        "physical_pauli": "Y",
        "selected_targets": fixture_cell["selected_targets"],
        "theta_radians": fixture_cell["theta_radians"],
        "theta_float64_hex": fixture_cell["theta_float64_hex"],
        "p_twirl": fixture_cell["p_twirl"],
        "active_rank_per_rotation": 2,
    }
    if (
        not isinstance(rotation, Mapping)
        or any(rotation.get(key) != value for key, value in expected_rotation.items())
    ):
        raise ValueError(f"{lane} physical rotation identity drifted")
    progress = report.get("progress")
    expected_progress = {
        "persistent_state_instances": 1,
        "prefix_batches_completed": fixture_cell["round_layers"],
        "completed_layers": fixture_cell["round_layers"],
        "completed_rotations": fixture_cell["rotation_count"],
        "attempted_rotations": fixture_cell["rotation_count"],
        "expected_layers": fixture_cell["round_layers"],
        "expected_rotations": fixture_cell["rotation_count"],
    }
    if (
        not isinstance(progress, Mapping)
        or any(progress.get(key) != value for key, value in expected_progress.items())
    ):
        raise ValueError(f"{lane} persistent-state progress drifted")

    timing = report.get("timing_ns")
    if not isinstance(timing, Mapping):
        raise ValueError(f"{lane} worker timing ledger is unavailable")
    if lane == "plain":
        parts = ("physical_prefix_apply_ns", "physical_local_ry_apply_ns")
    else:
        parts = ("tableau_prefix_apply_ns", "certified_tree_rotation_apply_ns")
    component_values = [
        _require_positive_int(timing.get(name), label=f"{lane} {name}")
        for name in parts
    ]
    update_ns = _require_positive_int(
        timing.get("update_ns"),
        label=f"{lane} update_ns",
    )
    if update_ns != sum(component_values):
        raise ValueError(f"{lane} update timing formula drifted")
    _require_positive_int(
        timing.get("worker_total_ns"),
        label=f"{lane} worker_total_ns",
    )
    operation_rows = timing.get("operation_rows")
    expected_operations = fixture_cell["operation_ledger"]
    if (
        not isinstance(operation_rows, list)
        or len(operation_rows) != len(expected_operations)
        or any(
            row.get("operation_index") != index
            or row.get("layer") != expected_operations[index]["layer"]
            or row.get("kind") != expected_operations[index]["kind"]
            or row.get("target") != expected_operations[index].get("target")
            or (
                lane == "gcapeps"
                and row.get("location_rank")
                != expected_operations[index].get("location_rank")
            )
            or row.get("status") != "completed"
            for index, row in enumerate(operation_rows)
        )
    ):
        raise ValueError(f"{lane} operation timing ledger drifted")

    usage = report.get("resource_usage")
    cgroup = usage.get("cgroup_memory_peak") if isinstance(usage, Mapping) else None
    peak_rss = _require_positive_int(
        usage.get("peak_rss_bytes") if isinstance(usage, Mapping) else None,
        label=f"{lane} peak RSS",
    )
    if not isinstance(cgroup, Mapping) or cgroup.get("status") != "available":
        raise ValueError(f"{lane} cgroup MemoryPeak is unavailable")
    cgroup_peak = _require_positive_int(
        cgroup.get("bytes"),
        label=f"{lane} cgroup MemoryPeak",
    )

    envelope = report.get("process_envelope")
    if (
        not isinstance(envelope, Mapping)
        or envelope.get("cpu_affinity") != [cpu_id]
        or envelope.get("python_no_user_site") is not True
        or envelope.get("python_dont_write_bytecode") is not True
        or envelope.get("pythonpath_absent") is not True
    ):
        raise ValueError(f"{lane} process envelope drifted")
    fork = report.get("fork")
    expected_checkout = str(fork_checkout.resolve(strict=True))
    if (
        not isinstance(fork, Mapping)
        or fork.get("path") != expected_checkout
        or fork.get("commit") != EXPECTED_FORK_COMMIT
        or fork.get("tree") != EXPECTED_FORK_TREE
        or fork.get("clean_including_ignored") is not True
    ):
        raise ValueError(f"{lane} fork binding drifted")

    semantics = report.get("candidate_semantics")
    if (
        not isinstance(semantics, Mapping)
        or semantics.get("is_truth") is not False
        or semantics.get("complete_state_contraction_performed") is not False
        or semantics.get("norm_computed") is not False
        or semantics.get("fidelity_computed") is not False
        or semantics.get("measurement_reset_or_record_computed") is not False
        or semantics.get("round_layers_are_complete_qec_rounds") is not False
        or semantics.get("p_twirl_is_sampled_frequency") is not False
    ):
        raise ValueError(f"{lane} candidate scope widened")
    forbidden = _forbidden_numeric_payload_keys(report)
    if forbidden:
        raise ValueError(
            f"{lane} emitted forbidden truth payload keys: {sorted(forbidden)}"
        )

    if lane == "gcapeps":
        construction = report.get("construction")
        if (
            report.get("censor") is not None
            or not isinstance(construction, Mapping)
            or construction.get("successful_update_count")
            != fixture_cell["rotation_count"]
            or construction.get("partial_ledger_complete_through_last_success")
            is not True
            or construction.get("multi_resource_limits")
            != {
                key: value
                for key, value in fixture["gcapeps_multi_resource_limits"].items()
                if key != "expected_refactor_factor_product"
            }
            or construction.get("expected_refactor_factor_product") != 1
        ):
            raise ValueError("GCAPEPS completed construction ledger drifted")

    representation = report.get("representation")
    snapshot = (
        representation.get("final")
        if isinstance(representation, Mapping)
        else None
    )
    if not isinstance(snapshot, Mapping):
        raise ValueError(f"{lane} final representation snapshot is unavailable")
    maximum_bond = _require_positive_int(
        snapshot.get("maximum_bond_dimension"),
        label=f"{lane} maximum bond",
    )
    tensor_elements = _require_positive_int(
        snapshot.get("total_tensor_elements"),
        label=f"{lane} tensor elements",
    )
    logical_bytes = _require_positive_int(
        snapshot.get("logical_tensor_bytes"),
        label=f"{lane} logical tensor bytes",
    )
    if (
        snapshot.get("tensor_count") != fixture["n_qubits"]
        or logical_bytes != tensor_elements * 16
        or snapshot.get("dtype") != "complex128"
    ):
        raise ValueError(f"{lane} representation resource identity drifted")
    return {
        "update_ns": update_ns,
        "peak_rss_bytes": peak_rss,
        "cgroup_memory_peak_bytes": cgroup_peak,
        "maximum_bond_dimension": maximum_bond,
        "total_tensor_elements": tensor_elements,
        "logical_tensor_bytes": logical_bytes,
        "persistent_state_instances": 1,
        "prefix_batches_completed": fixture_cell["round_layers"],
        "completed_layers": fixture_cell["round_layers"],
        "completed_rotations": fixture_cell["rotation_count"],
        "attempted_rotations": fixture_cell["rotation_count"],
    }


def validate_candidate_censor_report(
    report: Mapping[str, Any],
    *,
    lane: str,
    cell_id: str,
    fixture: Mapping[str, Any],
    fixture_sha256: str,
    cpu_id: int,
    fork_checkout: Path,
) -> dict[str, Any]:
    """Validate an exit-zero GC resource-guard censor as evidence."""

    if lane != "gcapeps":
        raise ValueError("only GCAPEPS may emit a structured resource censor")
    if (
        report.get("schema") != GCAPEPS_WORKER_SCHEMA
        or report.get("status") != "resource_guard_censored"
        or report.get("lane")
        != "gcapeps_persistent_live_frame_plus_rank2_tree_residual"
    ):
        raise ValueError("GCAPEPS structured-censor headline drifted")
    frozen_cell = frozen_grid_cell(int(fixture["distance"]), cell_id)
    fixture_cells = fixture.get("grid_cells")
    matches = (
        [row for row in fixture_cells if row.get("cell_id") == cell_id]
        if isinstance(fixture_cells, list)
        else []
    )
    if len(matches) != 1:
        raise ValueError("GCAPEPS structured-censor fixture cell drifted")
    cell = matches[0]
    expected_cell = {
        "role": frozen_cell["role"],
        "round_layers": frozen_cell["round_layers"],
        "noise_complexity": frozen_cell["noise_complexity"],
        "p_twirl": frozen_cell["p_twirl"],
        "p_twirl_float64_hex": frozen_cell["p_twirl_float64_hex"],
        "theta_radians": frozen_cell["theta_radians"],
        "theta_float64_hex": frozen_cell["theta_float64_hex"],
        "rotation_count": frozen_cell["expected_rotation_count"],
    }
    if any(cell.get(key) != value for key, value in expected_cell.items()):
        raise ValueError("GCAPEPS structured-censor frozen cell drifted")
    locations = fixture.get("error_locations")
    targets = (
        [row.get("target") for row in locations[: cell["noise_complexity"]]]
        if isinstance(locations, list)
        else []
    )
    if cell.get("selected_targets") != targets:
        raise ValueError("GCAPEPS structured-censor target order drifted")

    fixture_row = report.get("fixture")
    expected_binding = {
        "canonical_sha256": fixture_sha256,
        "distance": fixture["distance"],
        "n_qubits": fixture["n_qubits"],
        "dtype": "complex128",
        "prefix_stream_sha256": fixture["prefix"]["gate_stream_sha256"],
        "grid_cells_sha256": fixture["grid_cells_sha256"],
        "accumulated_frame_schedule_sha256": fixture[
            "accumulated_frame_schedule"
        ]["schedule_sha256"],
        "cell_id": cell_id,
        "role": cell["role"],
        "round_layers": cell["round_layers"],
        "noise_complexity": cell["noise_complexity"],
        "p_twirl": cell["p_twirl"],
        "p_twirl_float64_hex": cell["p_twirl_float64_hex"],
        "theta_radians": cell["theta_radians"],
        "theta_float64_hex": cell["theta_float64_hex"],
        "selected_targets": cell["selected_targets"],
        "expected_rotation_count": cell["rotation_count"],
    }
    if (
        not isinstance(fixture_row, Mapping)
        or any(fixture_row.get(key) != value for key, value in expected_binding.items())
        or report.get("numerical_settings")
        != {"dtype": "complex128", **fixture["peps_settings"]}
    ):
        raise ValueError("GCAPEPS structured-censor binding/settings drifted")

    censor = report.get("censor")
    required_text = ("error_type", "stage", "metric", "message")
    if (
        not isinstance(censor, Mapping)
        or censor.get("classification") != "RESOURCE_GUARD_CENSORED"
        or any(not isinstance(censor.get(key), str) or not censor.get(key) for key in required_text)
        or censor.get("failed_routing_event_not_committed") is not True
        or censor.get("carrier_update_contract") != "candidate_then_commit"
    ):
        raise ValueError("GCAPEPS structured censor payload drifted")
    failed_index = _require_nonnegative_int(
        censor.get("failed_operation_index"),
        label="failed operation index",
    )
    failed_layer = _require_positive_int(
        censor.get("failed_layer"),
        label="failed layer",
    )
    failed_rank = _require_positive_int(
        censor.get("failed_location_rank"),
        label="failed location rank",
    )
    failed_target = _require_nonnegative_int(
        censor.get("failed_target"),
        label="failed target",
    )
    predicted = _require_positive_int(censor.get("predicted"), label="predicted")
    limit = _require_positive_int(censor.get("limit"), label="limit")
    operations = cell.get("operation_ledger")
    if (
        predicted <= limit
        or not isinstance(operations, list)
        or failed_index >= len(operations)
        or operations[failed_index].get("kind") != "physical_ry"
        or operations[failed_index].get("layer") != failed_layer
        or operations[failed_index].get("location_rank") != failed_rank
        or operations[failed_index].get("target") != failed_target
    ):
        raise ValueError("GCAPEPS structured censor failed-operation binding drifted")

    progress = report.get("progress")
    if not isinstance(progress, Mapping):
        raise ValueError("GCAPEPS structured-censor progress is unavailable")
    completed_rotations = _require_nonnegative_int(
        progress.get("completed_rotations"),
        label="completed rotations",
    )
    attempted_rotations = _require_positive_int(
        progress.get("attempted_rotations"),
        label="attempted rotations",
    )
    if (
        progress.get("persistent_state_instances") != 1
        or progress.get("expected_layers") != cell["round_layers"]
        or progress.get("expected_rotations") != cell["rotation_count"]
        or progress.get("prefix_batches_completed") != failed_layer
        or progress.get("completed_layers") != failed_layer - 1
        or attempted_rotations != completed_rotations + 1
        or attempted_rotations > cell["rotation_count"]
        or failed_index != failed_layer + completed_rotations
    ):
        raise ValueError("GCAPEPS structured-censor progress drifted")

    timing = report.get("timing_ns")
    if not isinstance(timing, Mapping):
        raise ValueError("GCAPEPS structured-censor timing is unavailable")
    prefix_ns = _require_positive_int(
        timing.get("tableau_prefix_apply_ns"), label="censor prefix timing"
    )
    rotation_ns = _require_positive_int(
        timing.get("certified_tree_rotation_apply_ns"),
        label="censor rotation timing",
    )
    update_ns = _require_positive_int(
        timing.get("update_ns"), label="censor update timing"
    )
    _require_positive_int(timing.get("worker_total_ns"), label="censor worker total")
    timing_rows = timing.get("operation_rows")
    if (
        update_ns != prefix_ns + rotation_ns
        or not isinstance(timing_rows, list)
        or not timing_rows
        or timing_rows[-1].get("operation_index") != failed_index
        or timing_rows[-1].get("layer") != failed_layer
        or timing_rows[-1].get("kind") != "physical_ry"
        or timing_rows[-1].get("target") != failed_target
        or timing_rows[-1].get("location_rank") != failed_rank
        or timing_rows[-1].get("status") != "resource_guard_censored"
    ):
        raise ValueError("GCAPEPS structured-censor timing ledger drifted")

    representation = report.get("representation")
    partial = (
        representation.get("final_or_partial")
        if isinstance(representation, Mapping)
        else None
    )
    if (
        not isinstance(partial, Mapping)
        or representation.get("final") is not None
        or partial.get("tensor_count") != fixture["n_qubits"]
        or partial.get("dtype") != "complex128"
    ):
        raise ValueError("GCAPEPS structured-censor partial representation drifted")
    partial_maximum_bond = _require_positive_int(
        partial.get("maximum_bond_dimension"), label="partial maximum bond"
    )
    partial_tensor_elements = _require_positive_int(
        partial.get("total_tensor_elements"), label="partial tensor elements"
    )
    partial_logical_bytes = _require_positive_int(
        partial.get("logical_tensor_bytes"), label="partial logical bytes"
    )
    if partial_logical_bytes != partial_tensor_elements * 16:
        raise ValueError("GCAPEPS structured-censor logical bytes drifted")
    construction = report.get("construction")
    if (
        not isinstance(construction, Mapping)
        or construction.get("successful_update_count") != completed_rotations
        or construction.get("partial_ledger_complete_through_last_success") is not True
        or construction.get("multi_resource_limits")
        != {
            key: value
            for key, value in fixture["gcapeps_multi_resource_limits"].items()
            if key != "expected_refactor_factor_product"
        }
        or construction.get("expected_refactor_factor_product") != 1
    ):
        raise ValueError("GCAPEPS structured-censor construction ledger drifted")

    usage = report.get("resource_usage")
    cgroup = usage.get("cgroup_memory_peak") if isinstance(usage, Mapping) else None
    peak_rss = _require_positive_int(
        usage.get("peak_rss_bytes") if isinstance(usage, Mapping) else None,
        label="censor peak RSS",
    )
    if not isinstance(cgroup, Mapping) or cgroup.get("status") != "available":
        raise ValueError("GCAPEPS structured-censor cgroup peak unavailable")
    cgroup_peak = _require_positive_int(
        cgroup.get("bytes"), label="censor cgroup MemoryPeak"
    )

    envelope = report.get("process_envelope")
    fork = report.get("fork")
    semantics = report.get("candidate_semantics")
    expected_checkout = str(fork_checkout.resolve(strict=True))
    if (
        not isinstance(envelope, Mapping)
        or envelope.get("cpu_affinity") != [cpu_id]
        or envelope.get("python_no_user_site") is not True
        or envelope.get("python_dont_write_bytecode") is not True
        or envelope.get("pythonpath_absent") is not True
        or not isinstance(fork, Mapping)
        or fork.get("path") != expected_checkout
        or fork.get("commit") != EXPECTED_FORK_COMMIT
        or fork.get("tree") != EXPECTED_FORK_TREE
        or fork.get("clean_including_ignored") is not True
        or not isinstance(semantics, Mapping)
        or semantics.get("is_truth") is not False
        or semantics.get("complete_state_contraction_performed") is not False
        or semantics.get("norm_computed") is not False
        or semantics.get("fidelity_computed") is not False
        or semantics.get("measurement_reset_or_record_computed") is not False
        or semantics.get("round_layers_are_complete_qec_rounds") is not False
        or semantics.get("p_twirl_is_sampled_frequency") is not False
        or _forbidden_numeric_payload_keys(report)
    ):
        raise ValueError("GCAPEPS structured-censor runtime/scope drifted")
    return {
        "classification": "RESOURCE_GUARD_CENSORED",
        "censor": dict(censor),
        "progress": {
            key: progress[key]
            for key in (
                "persistent_state_instances",
                "prefix_batches_completed",
                "completed_layers",
                "completed_rotations",
                "attempted_rotations",
                "expected_layers",
                "expected_rotations",
            )
        },
        "update_ns_including_failed_attempt": update_ns,
        "peak_rss_bytes": peak_rss,
        "cgroup_memory_peak_bytes": cgroup_peak,
        "partial_maximum_bond_dimension": partial_maximum_bond,
        "partial_total_tensor_elements": partial_tensor_elements,
        "partial_logical_tensor_bytes": partial_logical_bytes,
    }


def _require_nonnegative_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def launch_candidate_worker(
    *,
    foundation: Any,
    lane: str,
    distance: int,
    cell_id: str,
    sample_kind: str,
    sample_index: int,
    fixture_path: Path,
    fixture: Mapping[str, Any],
    fork_checkout: Path,
    python_executable: Path,
    cpu_id: int,
    runtime_parent: Path,
) -> dict[str, Any]:
    """Launch one fresh process; retain nonzero exits as censored evidence."""

    if distance not in DISTANCES or fixture.get("distance") != distance:
        raise ValueError("candidate fixture distance drifted")
    cell = frozen_grid_cell(distance, cell_id)
    fixture_cells = fixture.get("grid_cells")
    if (
        not isinstance(fixture_cells, list)
        or len([row for row in fixture_cells if row.get("cell_id") == cell_id]) != 1
    ):
        raise ValueError("candidate fixture cell binding drifted")
    if sample_kind not in {"control", "warmup", "measured"}:
        raise ValueError("candidate sample kind drifted")
    token = (
        f"{cell_id}-{sample_kind}-{sample_index:02d}-{lane}-"
        f"{uuid.uuid4().hex}"
    )
    private_root = _private_subdirectory(foundation, runtime_parent, token)
    output_root = _private_subdirectory(foundation, private_root, "output")
    output_json = output_root / f"{lane}.json"
    environment = _worker_environment(
        foundation,
        python_executable=python_executable,
        private_root=private_root,
    )
    command = candidate_worker_command(
        lane=lane,
        python_executable=python_executable.resolve(strict=True),
        fixture_path=fixture_path.resolve(strict=True),
        cell_id=cell_id,
        fork_checkout=fork_checkout.resolve(strict=True),
        output_json=output_json,
    )
    process = _run_systemd_worker(
        foundation=foundation,
        unit_prefix=f"gcapeps-d{distance}-{sample_kind}-{lane}",
        worker_command=command,
        environment=environment,
        cpu_id=cpu_id,
        working_directory=fork_checkout,
    )
    base = {
        "distance": distance,
        "cell_id": cell_id,
        "cell": cell,
        "lane": lane,
        "sample_kind": sample_kind,
        "sample_index": sample_index,
        "private_root": str(private_root),
        "output_json": str(output_json),
        "process": process,
    }
    if process["returncode"] != 0:
        return {
            **base,
            "status": "censored",
            "censor_reason": _classify_censor(process),
            "output_sha256": None,
        }
    if not output_json.is_file() or output_json.is_symlink():
        return {
            **base,
            "status": "censored",
            "censor_reason": "worker_returned_without_regular_output",
            "output_sha256": None,
        }
    try:
        report = load_strict_json(output_json)
        if report.get("status") == "resource_guard_censored":
            structured_censor = validate_candidate_censor_report(
                report,
                lane=lane,
                cell_id=cell_id,
                fixture=fixture,
                fixture_sha256=EXPECTED_FIXTURE_SHA256[distance],
                cpu_id=cpu_id,
                fork_checkout=fork_checkout,
            )
            return {
                **base,
                "status": "censored",
                "censor_reason": "exact_construction_resource_guard",
                "structured_censor": structured_censor,
                "output_sha256": _sha256_file(output_json),
            }
        validated = validate_candidate_report(
            report,
            lane=lane,
            cell_id=cell_id,
            fixture=fixture,
            fixture_sha256=EXPECTED_FIXTURE_SHA256[distance],
            cpu_id=cpu_id,
            fork_checkout=fork_checkout,
        )
    except Exception as exc:
        return {
            **base,
            "status": "censored",
            "censor_reason": (
                f"worker_output_validation:{type(exc).__name__}:{exc}"
            ),
            "output_sha256": _sha256_file(output_json),
        }
    return {
        **base,
        "status": "completed",
        "censor_reason": None,
        "output_sha256": _sha256_file(output_json),
        "validated": validated,
    }


def emit_fixture_family(
    *,
    foundation: Any,
    python_executable: Path,
    runtime_parent: Path,
) -> dict[int, dict[str, Any]]:
    """Run the owning fixture CLI and independently revalidate all three rows."""

    emitter = _load_script(
        _EMITTER_PATH,
        f"_gcapeps_d357_emitter_{uuid.uuid4().hex}",
    )
    rows: dict[int, dict[str, Any]] = {}
    for distance in DISTANCES:
        private_root = _private_subdirectory(
            foundation,
            runtime_parent,
            f"fixture-d{distance}",
        )
        output_json = private_root / "fixture.json"
        output_stim = private_root / "fixture.stim"
        environment = _worker_environment(
            foundation,
            python_executable=python_executable,
            private_root=private_root,
        )
        process = foundation._run_captured(
            emitter_command(
                python_executable=python_executable.resolve(strict=True),
                distance=distance,
                output_json=output_json,
                output_stim=output_stim,
            ),
            cwd=_REPO_ROOT,
            environment=environment,
            timeout_seconds=120,
        )
        payload = load_strict_json(output_json, canonical=False)
        if output_json.read_bytes() != emitter.canonical_json_bytes(payload):
            raise RuntimeError(
                f"d={distance} fixture bytes violate the emitter-owned encoding"
            )
        digest = emitter.validate_fixture(payload)
        if (
            digest != EXPECTED_FIXTURE_SHA256[distance]
            or hashlib.sha256(output_json.read_bytes()).hexdigest() != digest
            or payload.get("distance") != distance
            or payload.get("n_qubits") != 2 * distance * distance - 1
        ):
            raise RuntimeError(f"d={distance} emitted fixture identity drifted")
        stim_digest = hashlib.sha256(output_stim.read_bytes()).hexdigest()
        if stim_digest != payload["stim_source"]["transformed_sha256"]:
            raise RuntimeError(f"d={distance} transformed Stim bytes drifted")
        rows[distance] = {
            "distance": distance,
            "fixture": payload,
            "fixture_json": str(output_json.resolve(strict=True)),
            "fixture_stim": str(output_stim.resolve(strict=True)),
            "fixture_sha256": digest,
            "stim_sha256": stim_digest,
            "process": process,
        }
    return rows


def launch_sdim_control(
    *,
    foundation: Any,
    distance: int,
    fixture_path: Path,
    sdim_python: Path,
    cpu_id: int,
    runtime_parent: Path,
) -> dict[str, Any]:
    if distance not in DISTANCES:
        raise ValueError("SDIM distance is outside the frozen sweep")
    private_root = _private_subdirectory(
        foundation,
        runtime_parent,
        f"sdim-d{distance}-{uuid.uuid4().hex}",
    )
    output_json = private_root / "sdim.json"
    environment = _worker_environment(
        foundation,
        python_executable=sdim_python,
        private_root=private_root,
    )
    process = _run_systemd_worker(
        foundation=foundation,
        unit_prefix=f"gcapeps-d{distance}-sdim-control",
        worker_command=sdim_worker_command(
            sdim_python=sdim_python.resolve(strict=True),
            fixture_path=fixture_path.resolve(strict=True),
            output_json=output_json,
        ),
        environment=environment,
        cpu_id=cpu_id,
        working_directory=_REPO_ROOT,
    )
    if process["returncode"] != 0 or not output_json.is_file():
        raise RuntimeError(
            f"d={distance} SDIM control failed: {process.get('stderr', '')}"
        )
    report = load_strict_json(output_json, canonical=True)
    worker = _load_script(
        _SDIM_WORKER_PATH,
        f"_gcapeps_d357_sdim_validator_{uuid.uuid4().hex}",
    )
    worker.validate_report(report)
    fixture_identity = report["fixture_identity"]
    if (
        report.get("schema") != SDIM_WORKER_SCHEMA
        or report.get("sdim_control_verdict") != "PASS"
        or fixture_identity.get("distance") != distance
        or fixture_identity.get("file_sha256")
        != EXPECTED_FIXTURE_SHA256[distance]
        or report["scope"].get("enters_performance_ratio") is not False
        or report["scope"].get("ground_truth") is not False
    ):
        raise ValueError(f"d={distance} SDIM report binding drifted")
    return {
        "distance": distance,
        "status": "PASS",
        "output_json": str(output_json.resolve(strict=True)),
        "output_sha256": _sha256_file(output_json),
        "process": process,
        "enters_performance_ratio": False,
    }


def build_controls_report(
    *,
    fixtures: Mapping[int, Mapping[str, Any]],
    sdim_runs: Mapping[int, Mapping[str, Any]],
    candidate_controls: Mapping[str, Mapping[str, Any]],
    parent_identity: Mapping[str, Any],
    fork_identity: Mapping[str, Any],
    environment_identity: Mapping[str, Any],
    systemd_identity: Mapping[str, Any],
) -> dict[str, Any]:
    if set(fixtures) != set(DISTANCES) or set(sdim_runs) != set(DISTANCES):
        raise ValueError("controls must cover exactly d=3,5,7")
    if set(candidate_controls) != set(LANES):
        raise ValueError("controls must cover both candidate lanes")
    for distance in DISTANCES:
        fixture = fixtures[distance]
        sdim = sdim_runs[distance]
        if (
            fixture.get("fixture_sha256")
            != EXPECTED_FIXTURE_SHA256[distance]
            or sdim.get("status") != "PASS"
            or sdim.get("enters_performance_ratio") is not False
        ):
            raise ValueError(f"d={distance} prerequisite control did not pass")
    for lane in LANES:
        row = candidate_controls[lane]
        if (
            row.get("status") != "completed"
            or row.get("distance") != 3
            or row.get("lane") != lane
            or row.get("cell_id") != "d3-baseline"
            or row.get("sample_kind") != "control"
        ):
            raise ValueError(f"d=3 {lane} candidate control did not pass")

    report: dict[str, Any] = {
        "schema": CONTROLS_SCHEMA,
        "report_role": "supervisor_private_controls_only",
        "status": "PASS",
        "controls_passed": True,
        "controls_gate_passed_for_later_target_preflight": True,
        "target_execution_authorized_by_this_report_alone": False,
        "fixture_family": {
            f"d{distance}": {
                "fixture_sha256": fixtures[distance]["fixture_sha256"],
                "stim_sha256": fixtures[distance]["stim_sha256"],
                "n_qubits": fixtures[distance]["fixture"]["n_qubits"],
            }
            for distance in DISTANCES
        },
        "sdim_controls": {
            f"d{distance}": {
                "status": "PASS",
                "output_sha256": sdim_runs[distance]["output_sha256"],
                "enters_performance_ratio": False,
            }
            for distance in DISTANCES
        },
        "candidate_d3_controls": {
            lane: {
                "status": "PASS",
                "output_sha256": candidate_controls[lane]["output_sha256"],
                "timing_values_retained_but_excluded": True,
                "enters_performance_ratio": False,
                "is_truth": False,
            }
            for lane in LANES
        },
        "execution_scope": {
            "target_worker_count": 0,
            "target_distance_count": 0,
            "candidate_control_distance": 3,
            "candidate_control_count": 2,
            "sdim_control_count": 3,
            "vector_norm_fidelity_or_record_computed": False,
        },
        "resource_envelope": dict(WORKER_RESOURCE_ENVELOPE),
        "parent": dict(parent_identity),
        "fork": dict(fork_identity),
        "environment": dict(environment_identity),
        "systemd": dict(systemd_identity),
        "source_sha256": claim_bearing_source_hashes(),
        "claim_boundary": (
            "controls only; no target sample, state faithfulness, Record law, "
            "scaling law, or general speed claim"
        ),
    }
    report["content_sha256"] = _canonical_sha256(report)
    validate_controls_report(report)
    return report


def validate_controls_report(report: Mapping[str, Any]) -> None:
    body = dict(report)
    content_hash = body.pop("content_sha256", None)
    if content_hash != _canonical_sha256(body):
        raise ValueError("controls report content hash drifted")
    if (
        report.get("schema") != CONTROLS_SCHEMA
        or report.get("report_role") != "supervisor_private_controls_only"
        or report.get("status") != "PASS"
        or report.get("controls_passed") is not True
        or report.get("controls_gate_passed_for_later_target_preflight") is not True
        or report.get("target_execution_authorized_by_this_report_alone") is not False
        or report.get("resource_envelope") != WORKER_RESOURCE_ENVELOPE
        or report.get("execution_scope", {}).get("target_worker_count") != 0
        or report.get("execution_scope", {}).get("target_distance_count") != 0
    ):
        raise ValueError("controls report headline/scope drifted")
    if set(report.get("fixture_family", {})) != {"d3", "d5", "d7"}:
        raise ValueError("controls fixture family drifted")
    if set(report.get("sdim_controls", {})) != {"d3", "d5", "d7"}:
        raise ValueError("controls SDIM family drifted")
    if set(report.get("candidate_d3_controls", {})) != set(LANES):
        raise ValueError("controls candidate family drifted")


def _artifact_bytes(path_value: str) -> bytes:
    path = Path(path_value).resolve(strict=True)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("private artifact is not a regular file")
    return path.read_bytes()


def controls_artifacts(
    *,
    controls: Mapping[str, Any],
    fixtures: Mapping[int, Mapping[str, Any]],
    sdim_runs: Mapping[int, Mapping[str, Any]],
    candidate_controls: Mapping[str, Mapping[str, Any]],
) -> dict[str, bytes]:
    artifacts = {"controls.json": canonical_json_bytes(controls)}
    for distance in DISTANCES:
        fixture = fixtures[distance]
        sdim = sdim_runs[distance]
        artifacts[f"fixtures/d{distance}.json"] = _artifact_bytes(
            fixture["fixture_json"]
        )
        artifacts[f"fixtures/d{distance}.stim"] = _artifact_bytes(
            fixture["fixture_stim"]
        )
        artifacts[f"logs/fixture-d{distance}.json"] = canonical_json_bytes(
            fixture["process"]
        )
        artifacts[f"controls/sdim-d{distance}.json"] = _artifact_bytes(
            sdim["output_json"]
        )
        artifacts[f"logs/sdim-d{distance}.json"] = canonical_json_bytes(
            sdim["process"]
        )
    for lane in LANES:
        row = candidate_controls[lane]
        artifacts[f"controls/d3-{lane}.json"] = _artifact_bytes(
            row["output_json"]
        )
        artifacts[f"logs/d3-{lane}.json"] = canonical_json_bytes(
            row["process"]
        )
    artifacts["provenance/parent.json"] = canonical_json_bytes(
        controls["parent"]
    )
    artifacts["provenance/fresh-fork.json"] = canonical_json_bytes(
        controls["fork"]
    )
    artifacts["provenance/main-environment.json"] = canonical_json_bytes(
        controls["environment"]
    )
    artifacts["provenance/systemd-cgroup.json"] = canonical_json_bytes(
        controls["systemd"]
    )
    return artifacts


def validate_controls_bundle(root: Path) -> dict[str, Any]:
    foundation = load_foundation()
    manifest, artifacts = foundation.load_published_bundle(root)
    required = {"controls.json"}
    for distance in DISTANCES:
        required.update(
            {
                f"fixtures/d{distance}.json",
                f"fixtures/d{distance}.stim",
                f"controls/sdim-d{distance}.json",
                f"logs/fixture-d{distance}.json",
                f"logs/sdim-d{distance}.json",
            }
        )
    for lane in LANES:
        required.update(
            {
                f"controls/d3-{lane}.json",
                f"logs/d3-{lane}.json",
            }
        )
    if not required.issubset(artifacts):
        raise ValueError("controls bundle is missing required raw evidence")
    controls = json.loads(
        artifacts["controls.json"],
        object_pairs_hook=_reject_duplicate_pairs,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(controls, dict):
        raise ValueError("controls artifact must contain one object")
    if artifacts["controls.json"] != canonical_json_bytes(controls):
        raise ValueError("controls artifact is not canonical JSON")
    validate_controls_report(controls)
    if controls.get("source_sha256") != claim_bearing_source_hashes():
        raise ValueError("controls source binding differs from current HEAD")
    emitter = _load_script(
        _EMITTER_PATH,
        f"_gcapeps_d357_bundle_fixture_{uuid.uuid4().hex}",
    )
    for distance in DISTANCES:
        raw = artifacts[f"fixtures/d{distance}.json"]
        fixture = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
        if (
            not isinstance(fixture, dict)
            or emitter.canonical_json_bytes(fixture) != raw
            or emitter.validate_fixture(fixture)
            != EXPECTED_FIXTURE_SHA256[distance]
            or hashlib.sha256(raw).hexdigest()
            != EXPECTED_FIXTURE_SHA256[distance]
            or hashlib.sha256(
                artifacts[f"fixtures/d{distance}.stim"]
            ).hexdigest()
            != fixture["stim_source"]["transformed_sha256"]
        ):
            raise ValueError(f"controls d={distance} fixture binding drifted")
        sdim_raw = artifacts[f"controls/sdim-d{distance}.json"]
        sdim = json.loads(
            sdim_raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
        sdim_worker = _load_script(
            _SDIM_WORKER_PATH,
            f"_gcapeps_d357_bundle_sdim_{distance}_{uuid.uuid4().hex}",
        )
        sdim_worker.validate_report(sdim)
        if (
            sdim.get("sdim_control_verdict") != "PASS"
            or sdim["fixture_identity"].get("file_sha256")
            != EXPECTED_FIXTURE_SHA256[distance]
        ):
            raise ValueError(f"controls d={distance} SDIM binding drifted")
    if (
        manifest.get("schema") != CONTROLS_SCHEMA
        or manifest.get("status") != "PASS"
        or manifest.get("controls_passed") is not True
        or manifest.get("target_execution_authorized_by_this_report_alone")
        is not False
        or manifest.get("parent_commit") != controls["parent"]["commit"]
        or manifest.get("fork_commit") != EXPECTED_FORK_COMMIT
        or manifest.get("fixture_sha256") != {
            f"d{distance}": EXPECTED_FIXTURE_SHA256[distance]
            for distance in DISTANCES
        }
    ):
        raise ValueError("controls manifest binding drifted")
    for lane in LANES:
        raw = artifacts[f"controls/d3-{lane}.json"]
        if hashlib.sha256(raw).hexdigest() != controls[
            "candidate_d3_controls"
        ][lane]["output_sha256"]:
            raise ValueError(f"controls d3 {lane} output hash drifted")
        report = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
        expected_schema = (
            PLAIN_WORKER_SCHEMA if lane == "plain" else GCAPEPS_WORKER_SCHEMA
        )
        if (
            report.get("schema") != expected_schema
            or report.get("status") != "completed"
            or report.get("candidate_semantics", {}).get("is_truth") is not False
            or report.get("candidate_semantics", {}).get("norm_computed") is not False
            or report.get("candidate_semantics", {}).get("fidelity_computed") is not False
        ):
            raise ValueError(f"controls d3 {lane} report drifted")
    return {
        "root": str(root.resolve(strict=True)),
        "manifest": manifest,
        "controls": controls,
        "artifacts": artifacts,
        "passed": True,
    }


def run_controls_only(
    *,
    destination: Path,
    fork_source: Path = DEFAULT_FORK_SOURCE,
    pixi_executable: Path = DEFAULT_PIXI_EXECUTABLE,
    sdim_python: Path = DEFAULT_SDIM_PYTHON,
) -> dict[str, Any]:
    """Execute and atomically publish controls without a target sample."""

    parent = verify_committed_parent_checkout()
    foundation = load_foundation()
    with foundation.preflight_publication(destination) as publication:
        with tempfile.TemporaryDirectory(prefix="gcapeps-d357-controls-") as temporary:
            runtime_root = Path(temporary).resolve(strict=True)
            os.chmod(runtime_root, 0o700)
            checkout = runtime_root / "fork"
            materialized = foundation.materialize_fresh_fork(
                fork_source,
                checkout,
            )
            environment_root = _private_subdirectory(
                foundation,
                runtime_root,
                "main-environment",
            )
            main_environment = foundation.provision_locked_main_environment(
                pixi_executable=pixi_executable,
                fork_checkout=checkout,
                private_root=environment_root,
            )
            capability_root = _private_subdirectory(
                foundation,
                runtime_root,
                "capability",
            )
            capability = foundation.preflight_systemd_resource_envelope(
                private_root=capability_root
            )
            cpu_id = int(capability["selected_lowest_cpu"])
            fixture_root = _private_subdirectory(
                foundation,
                runtime_root,
                "fixtures",
            )
            fixtures = emit_fixture_family(
                foundation=foundation,
                python_executable=Path(main_environment["python_executable"]),
                runtime_parent=fixture_root,
            )
            control_root = _private_subdirectory(
                foundation,
                runtime_root,
                "control-workers",
            )
            sdim_runs = {
                distance: launch_sdim_control(
                    foundation=foundation,
                    distance=distance,
                    fixture_path=Path(fixtures[distance]["fixture_json"]),
                    sdim_python=sdim_python,
                    cpu_id=cpu_id,
                    runtime_parent=control_root,
                )
                for distance in DISTANCES
            }
            candidate_controls = {
                lane: launch_candidate_worker(
                    foundation=foundation,
                    lane=lane,
                    distance=3,
                    cell_id="d3-baseline",
                    sample_kind="control",
                    sample_index=0,
                    fixture_path=Path(fixtures[3]["fixture_json"]),
                    fixture=fixtures[3]["fixture"],
                    fork_checkout=checkout,
                    python_executable=Path(main_environment["python_executable"]),
                    cpu_id=cpu_id,
                    runtime_parent=control_root,
                )
                for lane in LANES
            }
            if any(
                candidate_controls[lane].get("status") != "completed"
                for lane in LANES
            ):
                raise RuntimeError("d3 candidate control did not complete")
            fork_after = foundation.verify_frozen_fork_checkout(checkout)
            if fork_after != materialized:
                raise RuntimeError("fresh fork changed during controls")
            parent_after = verify_committed_parent_checkout()
            if parent_after != parent:
                raise RuntimeError("parent or claim-bearing source changed during controls")
            controls = build_controls_report(
                fixtures=fixtures,
                sdim_runs=sdim_runs,
                candidate_controls=candidate_controls,
                parent_identity=parent,
                fork_identity=fork_after,
                environment_identity=main_environment,
                systemd_identity=capability,
            )
            artifacts = controls_artifacts(
                controls=controls,
                fixtures=fixtures,
                sdim_runs=sdim_runs,
                candidate_controls=candidate_controls,
            )
            confirmation = foundation.publish_bundle_noreplace(
                publication,
                artifacts=artifacts,
                manifest_payload={
                    "schema": CONTROLS_SCHEMA,
                    "status": "PASS",
                    "controls_passed": True,
                    "target_execution_authorized_by_this_report_alone": False,
                    "target_worker_count": 0,
                    "parent_commit": parent["commit"],
                    "fork_commit": EXPECTED_FORK_COMMIT,
                    "fixture_sha256": {
                        f"d{distance}": EXPECTED_FIXTURE_SHA256[distance]
                        for distance in DISTANCES
                    },
                },
            )
    return {
        "status": "PASS",
        "destination": str(destination.absolute()),
        "target_worker_count": 0,
        "publication": confirmation,
    }


def _write_target_fixtures(
    *,
    foundation: Any,
    runtime_root: Path,
    controls: Mapping[str, Any],
) -> tuple[dict[int, dict[str, Any]], dict[int, Path]]:
    emitter = _load_script(
        _EMITTER_PATH,
        f"_gcapeps_d357_target_fixture_{uuid.uuid4().hex}",
    )
    fixture_root = _private_subdirectory(
        foundation,
        runtime_root,
        "target-fixtures",
    )
    fixtures: dict[int, dict[str, Any]] = {}
    paths: dict[int, Path] = {}
    artifacts = controls["artifacts"]
    for distance in DISTANCES:
        raw = artifacts[f"fixtures/d{distance}.json"]
        fixture = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
        if emitter.validate_fixture(fixture) != EXPECTED_FIXTURE_SHA256[distance]:
            raise RuntimeError(f"target d={distance} fixture drifted")
        path = fixture_root / f"d{distance}.json"
        foundation._write_exclusive_file(path, raw)
        fixtures[distance] = fixture
        paths[distance] = path.resolve(strict=True)
    return fixtures, paths


def _target_artifacts(
    *,
    result: Mapping[str, Any],
    controls: Mapping[str, Any],
    runs: Sequence[Mapping[str, Any]],
    main_environment: Mapping[str, Any],
) -> dict[str, bytes]:
    artifacts: dict[str, bytes] = {
        "result.json": canonical_json_bytes(result),
        "controls/source-manifest.json": canonical_json_bytes(
            controls["manifest"]
        ),
        "provenance/main-environment-full.json": canonical_json_bytes(
            main_environment
        ),
    }
    for name, payload in controls["artifacts"].items():
        artifacts[f"controls/{name}"] = payload
    for launch_index, row in enumerate(runs):
        prefix = (
            f"workers/{launch_index:03d}-{row['cell_id']}-"
            f"{row['sample_kind']}-{row['sample_index']:02d}-{row['lane']}"
        )
        artifacts[f"{prefix}/launch.json"] = canonical_json_bytes(
            row.get("process")
        )
        output = row.get("output_json")
        if output is not None and Path(output).is_file():
            artifacts[f"{prefix}/worker.json"] = Path(output).read_bytes()
    return artifacts


def build_target_result(
    *,
    runs: Sequence[Mapping[str, Any]],
    controls: Mapping[str, Any],
    parent_identity: Mapping[str, Any],
    fork_identity: Mapping[str, Any],
    environment_identity: Mapping[str, Any],
    systemd_identity: Mapping[str, Any],
) -> dict[str, Any]:
    if len(runs) != 192:
        raise ValueError("target must retain exactly 192 requested launches")
    cells = [
        summarize_cell(
            distance=int(cell["distance"]),
            cell_id=str(cell["cell_id"]),
            runs=runs,
            controls_passed=bool(controls["passed"]),
        )
        for cell in frozen_grid_cells()
    ]
    any_censored = any(row.get("status") != "completed" for row in runs)
    finite_ratio_cells = [
        row["cell_id"] for row in cells if row["joint_ratio_eligible"]
    ]
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "status": "completed_with_censoring" if any_censored else "completed",
        "question": (
            "bounded_equal_status_d357_depth_complexity_probability_"
            "performance_surface"
        ),
        "candidate_role": "equal_status",
        "ordinary_quimb_is_truth": False,
        "gcapeps_is_truth": False,
        "state_faithfulness_estimand": False,
        "measurement_reset_or_record_estimand": False,
        "grid_cells": cells,
        "execution": {
            "requested_distances": list(DISTANCES),
            "attempted_distances": list(DISTANCES),
            "requested_cell_count": 24,
            "attempted_cell_count": 24,
            "all_cells_attempted_independently": True,
            "warmup_count_per_lane_per_cell": 1,
            "measured_count_per_lane_per_cell": 3,
            "launch_count": 192,
            "launch_order": target_launch_plan(),
            "resource_envelope": dict(WORKER_RESOURCE_ENVELOPE),
        },
        "controls": {
            "bundle": controls["root"],
            "manifest_content_hash": controls["manifest"]["content_hash"],
            "passed_before_target": True,
        },
        "parent": dict(parent_identity),
        "fork": dict(fork_identity),
        "environment": dict(environment_identity),
        "systemd": dict(systemd_identity),
        "source_sha256": claim_bearing_source_hashes(),
        "terminal": {
            "any_censored": any_censored,
            "finite_ratio_cells": finite_ratio_cells,
            "finite_ratio_cell_count": len(finite_ratio_cells),
            "interaction_fit_performed": False,
            "asymptotic_fit_performed": False,
            "generic_speedup_claim": False,
            "peps_contraction_efficiency_claim": False,
            "record_faithfulness_claim": False,
        },
        "claim_boundary": (
            "persistent unitary H/CX shells plus coherent physical RY updates; "
            "current frozen machine, fork, settings, grid, and process envelope; "
            "no truth lane, physical QEC rounds, interaction fit, or scaling law"
        ),
    }
    result["content_sha256"] = _canonical_sha256(result)
    return result


def run_target(
    *,
    destination: Path,
    controls_bundle: Path,
    fork_source: Path = DEFAULT_FORK_SOURCE,
    pixi_executable: Path = DEFAULT_PIXI_EXECUTABLE,
) -> dict[str, Any]:
    """Run the target population only after a sealed matching controls bundle."""

    controls = validate_controls_bundle(controls_bundle)
    parent = verify_committed_parent_checkout()
    if controls["manifest"].get("parent_commit") != parent["commit"]:
        raise ValueError("controls parent commit differs from target parent")
    foundation = load_foundation()
    with foundation.preflight_publication(destination) as publication:
        with tempfile.TemporaryDirectory(prefix="gcapeps-d357-target-") as temporary:
            runtime_root = Path(temporary).resolve(strict=True)
            os.chmod(runtime_root, 0o700)
            checkout = runtime_root / "fork"
            materialized = foundation.materialize_fresh_fork(
                fork_source,
                checkout,
            )
            environment_root = _private_subdirectory(
                foundation,
                runtime_root,
                "main-environment",
            )
            main_environment = foundation.provision_locked_main_environment(
                pixi_executable=pixi_executable,
                fork_checkout=checkout,
                private_root=environment_root,
            )
            capability_root = _private_subdirectory(
                foundation,
                runtime_root,
                "capability",
            )
            capability = foundation.preflight_systemd_resource_envelope(
                private_root=capability_root
            )
            cpu_id = int(capability["selected_lowest_cpu"])
            fixtures, fixture_paths = _write_target_fixtures(
                foundation=foundation,
                runtime_root=runtime_root,
                controls=controls,
            )
            worker_root = _private_subdirectory(
                foundation,
                runtime_root,
                "target-workers",
            )
            python_executable = Path(main_environment["python_executable"])

            def launch(**spec: Any) -> Mapping[str, Any]:
                distance = int(spec["distance"])
                return launch_candidate_worker(
                    foundation=foundation,
                    fixture_path=fixture_paths[distance],
                    fixture=fixtures[distance],
                    fork_checkout=checkout,
                    python_executable=python_executable,
                    cpu_id=cpu_id,
                    runtime_parent=worker_root,
                    **spec,
                )

            runs = execute_target_population(launch)
            fork_after = foundation.verify_frozen_fork_checkout(checkout)
            if fork_after != materialized:
                raise RuntimeError("fresh fork changed during target execution")
            parent_after = verify_committed_parent_checkout()
            if parent_after != parent:
                raise RuntimeError("parent or claim-bearing source changed during target")
            result = build_target_result(
                runs=runs,
                controls=controls,
                parent_identity=parent,
                fork_identity=fork_after,
                environment_identity=foundation._compact_provenance(
                    main_environment
                ),
                systemd_identity=foundation._compact_provenance(capability),
            )
            artifacts = _target_artifacts(
                result=result,
                controls=controls,
                runs=runs,
                main_environment=main_environment,
            )
            confirmation = foundation.publish_bundle_noreplace(
                publication,
                artifacts=artifacts,
                manifest_payload={
                    "schema": RESULT_SCHEMA,
                    "status": result["status"],
                    "candidate_role": "equal_status",
                    "ordinary_quimb_is_truth": False,
                    "gcapeps_is_truth": False,
                    "requested_distances": list(DISTANCES),
                    "requested_cell_count": 24,
                    "all_cells_attempted": True,
                    "any_censored": result["terminal"]["any_censored"],
                    "finite_ratio_cells": result["terminal"][
                        "finite_ratio_cells"
                    ],
                    "parent_commit": parent["commit"],
                    "fork_commit": EXPECTED_FORK_COMMIT,
                    "fixture_sha256": {
                        f"d{distance}": EXPECTED_FIXTURE_SHA256[distance]
                        for distance in DISTANCES
                    },
                },
            )
    return {
        "status": result["status"],
        "destination": str(destination.absolute()),
        "terminal": result["terminal"],
        "publication": confirmation,
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    controls = subparsers.add_parser("controls-only")
    controls.add_argument("--destination", type=Path, required=True)
    controls.add_argument(
        "--fork-source",
        type=Path,
        default=DEFAULT_FORK_SOURCE,
    )
    controls.add_argument(
        "--pixi-executable",
        type=Path,
        default=DEFAULT_PIXI_EXECUTABLE,
    )
    controls.add_argument(
        "--sdim-python",
        type=Path,
        default=DEFAULT_SDIM_PYTHON,
    )
    target = subparsers.add_parser("target")
    target.add_argument("--destination", type=Path, required=True)
    target.add_argument("--controls-bundle", type=Path, required=True)
    target.add_argument(
        "--fork-source",
        type=Path,
        default=DEFAULT_FORK_SOURCE,
    )
    target.add_argument(
        "--pixi-executable",
        type=Path,
        default=DEFAULT_PIXI_EXECUTABLE,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "controls-only":
        result = run_controls_only(
            destination=args.destination,
            fork_source=args.fork_source,
            pixi_executable=args.pixi_executable,
            sdim_python=args.sdim_python,
        )
    else:
        result = run_target(
            destination=args.destination,
            controls_bundle=args.controls_bundle,
            fork_source=args.fork_source,
            pixi_executable=args.pixi_executable,
        )
    print(
        json.dumps(
            result,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

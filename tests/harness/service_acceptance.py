"""Run the declared simulator-service acceptance surface safely.

Every acceptance file runs in a fresh exec process so unrelated native runtimes
never share an allocator or lifetime.  The immutable catalog plan has three
resource lanes:

* ``cpu_light`` -- bounded subprocess concurrency;
* ``cpu_exclusive`` -- serial host execution for memory/BLAS-heavy tests;
* ``gpu_serial`` -- serial execution while holding one cross-process GPU lease.

The supervisor itself imports no Torch/CUDA runtime.  CUDA-Q remains routed to
the retained ``aiqec`` environment through a per-file catalog override.

Usage:
    python tests/harness/service_acceptance.py
    python tests/harness/service_acceptance.py --list
"""

from __future__ import annotations

import argparse
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import MappingProxyType
from typing import Callable, Mapping
import uuid


TESTS_ROOT = Path(__file__).resolve().parents[1]
REPO = TESTS_ROOT.parent
sys.path.insert(0, str(TESTS_ROOT))

from harness import gpu_pool, proc  # noqa: E402


CATALOG_PATH = REPO / "docs" / "service_status.json"
CONFIG_PATH = TESTS_ROOT / "harness_config.json"
DEFAULT_LOG_ROOT = REPO / "outputs" / "simulator_validation" / "logs" / "service_acceptance"
LANE_ORDER = ("cpu_light", "cpu_exclusive", "gpu_serial")
_CHECKPOINT_SCHEMA = "error_coupling_simulator.service_acceptance_checkpoint.v1"
_SUMMARY_SCHEMA = "error_coupling_simulator.service_acceptance_run.v3"
_CHECKPOINT_NAME = "service_acceptance_checkpoint.json"
_LOCK_NAME = ".service_acceptance.lock"
_CHECKPOINTABLE_PYTEST_RETURN_CODES = frozenset({0, 1, 5})
_SNAPSHOT_DIRECTORY_INPUTS = (
    "src",
    "tests",
    "scripts",
    "tools",
    "docs",
    "configs",
    "external/baselines/qiskit-aer",
    "external/baselines/yastn",
    "external/baselines/qutip",
    "external/baselines/ITensorMPS.jl",
)
_SNAPSHOT_GIT_REPOSITORY_INPUTS = (
    "external/baselines/qiskit-aer",
    "external/baselines/yastn",
    "external/baselines/qutip",
    "external/baselines/ITensorMPS.jl",
)
_RUNTIME_CONTENT_PACKAGE_TREES = MappingProxyType(
    {
        "ecs-baseline-qutip": ("numpy", "scipy", "qutip"),
    }
)
_SNAPSHOT_FILE_INPUTS = (
    "AGENTS.md",
    "CLAUDE.md",
    "CONTEXT.md",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "pytest.ini",
    "environment-ecs.yml",
    "core-environment-cu130.lock",
    "environment.yml",
    "environment.yaml",
    "requirements.txt",
    "requirements.lock.txt",
    "MANIFEST.in",
    "uv.lock",
    "poetry.lock",
    "pixi.lock",
)
_SNAPSHOT_EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
    }
)
_ALLOWED_PROCESS_ENVIRONMENT = frozenset(
    {
        "ECS_RUN_AER_MPS_COMPARISON",
        "ECS_RUN_ITENSOR_MPS_COMPARISON",
        "ECS_RUN_MCWF_XZ_FIXTURE_FAMILY_COMPARISON",
        "ECS_RUN_QUTIP_MCWF_XZ_COMPARISON",
        "ECS_RUN_YASTN_MPS_COMPARISON",
        "PYTORCH_ALLOC_CONF",
    }
)
_PROTECTED_GPU_ENVIRONMENT = frozenset({"CUDA_VISIBLE_DEVICES", "ECS_GPU_SLOT"})
_MAX_CPU_LIGHT_JOBS = 4
_CPU_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


@dataclass(frozen=True, slots=True)
class AcceptanceTask:
    """One immutable fresh-process admission unit."""

    lane: str
    environment: str
    test_file: str
    process_environment: tuple[tuple[str, str], ...] = ()
    nested_environments: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TaskResult:
    """Completed process result; only the main supervisor aggregates these."""

    task: AcceptanceTask
    returncode: int
    timed_out: bool
    group_cleanup_verified: bool
    log_path: Path
    elapsed_s: float
    error: str | None = None

    @property
    def ok(self) -> bool:
        return (
            self.error is None
            and self.group_cleanup_verified is True
            and type(self.timed_out) is bool
            and not self.timed_out
            and type(self.returncode) is int
            and self.returncode == 0
        )


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def acceptance_plan(catalog: dict) -> tuple[AcceptanceTask, ...]:
    """Return one lane/environment row per unique declared acceptance file."""

    execution = catalog["acceptance_execution"]
    if execution["isolation"] != "one_test_file_per_process":
        raise ValueError("service acceptance requires one_test_file_per_process")
    default_environment = str(execution["default_conda_environment"])
    environment_overrides = {
        str(path): str(environment)
        for path, environment in execution["environment_overrides"].items()
    }
    raw_process_environment = execution["process_environment_overrides"]
    if not isinstance(raw_process_environment, Mapping):
        raise ValueError("process_environment_overrides must be a mapping")
    process_environment_by_file: dict[str, tuple[tuple[str, str], ...]] = {}
    for raw_path, raw_environment in raw_process_environment.items():
        path = str(raw_path)
        if not isinstance(raw_environment, Mapping):
            raise ValueError(
                f"process environment for {path!r} must be a key/value mapping"
            )
        entries: list[tuple[str, str]] = []
        for raw_name, raw_value in raw_environment.items():
            if not isinstance(raw_name, str) or not raw_name or "=" in raw_name or "\0" in raw_name:
                raise ValueError(f"invalid process-environment name for {path!r}: {raw_name!r}")
            if raw_name in _PROTECTED_GPU_ENVIRONMENT:
                raise ValueError(
                    f"process environment may not override GPU routing variable {raw_name!r}"
                )
            if raw_name not in _ALLOWED_PROCESS_ENVIRONMENT:
                raise ValueError(f"unsupported process-environment variable: {raw_name!r}")
            if not isinstance(raw_value, str) or "\0" in raw_value:
                raise ValueError(
                    f"process-environment value for {raw_name!r} must be a NUL-free string"
                )
            entries.append((raw_name, raw_value))
        process_environment_by_file[path] = tuple(sorted(entries))
    raw_nested_environments = execution["nested_environment_overrides"]
    if not isinstance(raw_nested_environments, Mapping):
        raise ValueError("nested_environment_overrides must be a mapping")
    nested_environments_by_file: dict[str, tuple[str, ...]] = {}
    for raw_path, raw_environments in raw_nested_environments.items():
        path = str(raw_path)
        if (
            isinstance(raw_environments, (str, bytes))
            or not isinstance(raw_environments, (list, tuple))
        ):
            raise ValueError(
                f"nested environments for {path!r} must be a list of names"
            )
        names: list[str] = []
        for raw_name in raw_environments:
            if (
                not isinstance(raw_name, str)
                or not raw_name
                or "\0" in raw_name
                or "/" in raw_name
            ):
                raise ValueError(
                    f"invalid nested environment name for {path!r}: {raw_name!r}"
                )
            names.append(raw_name)
        if len(names) != len(set(names)):
            raise ValueError(f"nested environments for {path!r} contain duplicates")
        nested_environments_by_file[path] = tuple(sorted(names))
    default_lane = str(execution["default_lane"])
    lane_by_file: dict[str, str] = {}
    for lane, paths in execution["lane_overrides"].items():
        if lane not in LANE_ORDER:
            raise ValueError(f"unknown service-acceptance lane: {lane!r}")
        for path in paths:
            path = str(path)
            if path in lane_by_file:
                raise ValueError(f"acceptance file appears in multiple lanes: {path}")
            lane_by_file[path] = str(lane)
    files = sorted({
        str(path)
        for service in catalog["services"]
        for path in service["acceptance"]
    })
    acceptance_files = set(files)
    unknown_lanes = sorted(set(lane_by_file) - acceptance_files)
    if unknown_lanes:
        raise ValueError(f"lane overrides reference non-acceptance files: {unknown_lanes}")
    unknown_environments = sorted(set(environment_overrides) - acceptance_files)
    if unknown_environments:
        raise ValueError(
            "environment overrides reference non-acceptance files: "
            f"{unknown_environments}"
        )
    unknown_process_environments = sorted(
        set(process_environment_by_file) - acceptance_files
    )
    if unknown_process_environments:
        raise ValueError(
            "process-environment overrides reference non-acceptance files: "
            f"{unknown_process_environments}"
        )
    unknown_nested_environments = sorted(
        set(nested_environments_by_file) - acceptance_files
    )
    if unknown_nested_environments:
        raise ValueError(
            "nested-environment overrides reference non-acceptance files: "
            f"{unknown_nested_environments}"
        )
    return tuple(
        AcceptanceTask(
            lane=lane_by_file.get(path, default_lane),
            environment=environment_overrides.get(path, default_environment),
            test_file=path,
            process_environment=process_environment_by_file.get(path, ()),
            nested_environments=nested_environments_by_file.get(path, ()),
        )
        for path in files
    )


def _task_child_environment(
    task: AcceptanceTask,
    base_environment: Mapping[str, str],
) -> dict[str, str]:
    """Build one private fresh-exec environment without mutating the supervisor."""

    child = dict(base_environment)
    overrides = dict(task.process_environment)
    protected = sorted(set(overrides) & _PROTECTED_GPU_ENVIRONMENT)
    if protected:
        raise ValueError(f"task may not override GPU routing variables: {protected}")
    unsupported = sorted(set(overrides) - _ALLOWED_PROCESS_ENVIRONMENT)
    if unsupported:
        raise ValueError(f"task has unsupported process-environment variables: {unsupported}")
    if "PYTORCH_ALLOC_CONF" in overrides:
        # Do not let PyTorch's backwards-compatible alias compete with the
        # catalog's current, explicitly recorded allocator contract.
        child.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    child.pop("PYTHONPATH", None)
    child["PYTHONNOUSERSITE"] = "1"
    child.update(overrides)
    return child


def _cpu_child_environment(base_environment: Mapping[str, str]) -> dict[str, str]:
    """Return a CUDA-hidden, non-oversubscribing environment for CPU lanes."""

    child = dict(base_environment)
    child["CUDA_VISIBLE_DEVICES"] = ""
    child.pop("ECS_GPU_SLOT", None)
    for name in _CPU_THREAD_ENVIRONMENT:
        child[name] = "1"
    return child


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["service_acceptance"]


def _timeout_per_file(config: Mapping[str, object]) -> float:
    configured = float(config["timeout_per_file_s"])
    return float(os.environ.get("ECS_ACCEPTANCE_TIMEOUT", configured))


def _available_memory_bytes() -> int | None:
    """Read Linux's admission-oriented MemAvailable without importing psutil."""

    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def _cpu_light_jobs(config: Mapping[str, object]) -> tuple[int, int | None]:
    """Bound admissions by CPU count and a conservative host-memory token cap."""

    declared_ceiling = int(config["cpu_light_jobs"])
    requested = int(os.environ.get("ECS_ACCEPTANCE_CPU_JOBS", declared_ceiling))
    if declared_ceiling < 1 or requested < 1:
        raise ValueError("service_acceptance.cpu_light_jobs must be >= 1")
    cpu_cap = max(1, os.cpu_count() or 1)
    available = _available_memory_bytes()
    memory_cap: int | None = None
    if available is not None:
        gib = 1024 ** 3
        reserve = float(config["host_memory_reserve_gib"]) * gib
        per_job = float(config["cpu_light_memory_gib_per_job"]) * gib
        if per_job <= 0:
            raise ValueError("cpu_light_memory_gib_per_job must be > 0")
        memory_cap = max(1, math.floor(max(0.0, available - reserve) / per_job))
    return (
        min(
            requested,
            declared_ceiling,
            _MAX_CPU_LIGHT_JOBS,
            cpu_cap,
            memory_cap or requested,
        ),
        memory_cap,
    )


def _tail(path: Path, *, lines: int = 40) -> str:
    if not path.is_file():
        return "(log missing)"
    return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _new_run_log_dir(log_root: Path) -> Path:
    """Allocate a collision-free directory even for concurrent harness runs."""

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_id = f"run-{stamp}-p{os.getpid()}-{uuid.uuid4().hex[:8]}"
    run_dir = log_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _environment_metadata_identity(
    prefix: Path,
    *,
    package_trees: tuple[str, ...] = (),
) -> dict[str, object]:
    """Hash package records and import hooks without importing the environment."""

    resolved_prefix = prefix.resolve(strict=True)
    conda_meta = resolved_prefix / "conda-meta"
    if not conda_meta.is_dir():
        raise RuntimeError(f"Conda environment lacks conda-meta: {resolved_prefix}")

    entries: dict[str, Path] = {}

    def add(path: Path) -> None:
        relative = path.relative_to(resolved_prefix).as_posix()
        entries[relative] = path

    for path in conda_meta.rglob("*"):
        if path.is_symlink() or path.is_file():
            add(path)
    for site_packages in resolved_prefix.glob("lib/python*/site-packages"):
        if not site_packages.is_dir():
            continue
        for entry in site_packages.iterdir():
            if entry.is_symlink() or entry.is_file():
                add(entry)
            elif entry.is_dir() and entry.name.endswith((".dist-info", ".egg-info")):
                for path in entry.rglob("*"):
                    if path.is_symlink() or path.is_file():
                        add(path)
        for package_name in package_trees:
            package_root = site_packages / package_name
            if not package_root.is_dir():
                raise RuntimeError(
                    f"selected installed package tree is missing: {package_root}"
                )
            for path in package_root.rglob("*"):
                if path.suffix == ".pyc":
                    continue
                if path.is_symlink() or path.is_file():
                    add(path)
    if not entries:
        raise RuntimeError(f"Conda environment has no metadata files: {resolved_prefix}")

    digest = hashlib.sha256()
    total_bytes = 0
    for relative, path in sorted(entries.items()):
        encoded_path = relative.encode("utf-8")
        if path.is_symlink():
            kind = b"L"
            payload = os.readlink(path).encode("utf-8")
        elif path.is_file():
            kind = b"F"
            payload = path.read_bytes()
        else:
            raise RuntimeError(f"environment metadata entry changed type: {path}")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(kind)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
        total_bytes += len(payload)
    return {
        "prefix": str(resolved_prefix),
        "metadata_sha256": digest.hexdigest(),
        "metadata_file_count": len(entries),
        "metadata_bytes": total_bytes,
        "content_package_trees": sorted(package_trees),
    }


def _environment_prefixes_from_payload(
    payload: object,
    environment_names: tuple[str, ...],
) -> dict[str, Path]:
    """Resolve each named environment uniquely from ``conda env list`` JSON."""

    if not isinstance(payload, dict) or not isinstance(payload.get("envs"), list):
        raise RuntimeError("conda env list returned an invalid JSON document")
    prefixes: set[Path] = set()
    for raw_prefix in payload["envs"]:
        if not isinstance(raw_prefix, str) or not raw_prefix:
            raise RuntimeError("conda env list returned an invalid environment prefix")
        prefixes.add(Path(raw_prefix).resolve(strict=True))
    resolved: dict[str, Path] = {}
    for name in environment_names:
        matches = sorted(path for path in prefixes if path.name == name)
        if not matches:
            raise RuntimeError(f"missing named Conda environment: {name}")
        if len(matches) != 1:
            raise RuntimeError(f"ambiguous named Conda environment: {name}")
        resolved[name] = matches[0]
    return resolved


def _required_runtime_environments(
    plan: tuple[AcceptanceTask, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {task.environment for task in plan}
            | {
                environment
                for task in plan
                for environment in task.nested_environments
            }
        )
    )


def _runtime_environment_identity(
    conda: str,
    plan: tuple[AcceptanceTask, ...],
) -> dict[str, object]:
    """Bind the Conda executable and metadata of every direct/nested runtime."""

    conda_path = Path(conda).resolve(strict=True)
    child_env = _cpu_child_environment(os.environ)
    child_env.pop("PYTHONPATH", None)
    child_env["PYTHONNOUSERSITE"] = "1"
    completed = subprocess.run(
        [str(conda_path), "env", "list", "--json"],
        cwd=REPO,
        env=child_env,
        text=True,
        capture_output=True,
        timeout=120.0,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            "conda env list failed while fingerprinting acceptance runtimes: "
            f"returncode={completed.returncode}, detail={detail[-1000:]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("conda env list returned malformed JSON") from exc
    names = _required_runtime_environments(plan)
    prefixes = _environment_prefixes_from_payload(payload, names)
    return {
        "conda_executable": {
            "path": str(conda_path),
            "sha256": _sha256_file(conda_path),
        },
        "environments": {
            name: _environment_metadata_identity(
                prefixes[name],
                package_trees=_RUNTIME_CONTENT_PACKAGE_TREES.get(name, ()),
            )
            for name in names
        },
    }


def _acceptance_input_snapshot() -> str:
    """Hash the path-bound repository inputs consumed by service acceptance."""

    root = REPO.resolve()
    files: set[Path] = set()
    candidates = [REPO / path for path in _SNAPSHOT_DIRECTORY_INPUTS]
    candidates.extend(REPO / path for path in _SNAPSHOT_FILE_INPUTS)
    for candidate in candidates:
        if not candidate.exists():
            continue
        paths = candidate.rglob("*") if candidate.is_dir() else (candidate,)
        for path in paths:
            try:
                relative_unresolved = path.relative_to(REPO)
            except ValueError as exc:
                raise ValueError(f"acceptance snapshot input escapes repository: {path}") from exc
            if (
                set(relative_unresolved.parts) & _SNAPSHOT_EXCLUDED_PARTS
                or path.suffix == ".pyc"
                or not path.is_file()
            ):
                continue
            resolved = path.resolve(strict=True)
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise ValueError(
                    f"acceptance snapshot input escapes repository: {path}"
                ) from exc
            files.add(resolved)
    if not files:
        raise ValueError("service-acceptance snapshot has no files")

    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    for relative_text in _SNAPSHOT_GIT_REPOSITORY_INPUTS:
        repository = (REPO / relative_text).resolve()
        if not repository.exists():
            continue
        try:
            repository.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                f"acceptance git snapshot input escapes repository: {repository}"
            ) from exc
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "rev-parse",
                "HEAD",
                "HEAD^{tree}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        revisions = completed.stdout.splitlines()
        if len(revisions) != 2 or any(len(value) != 40 for value in revisions):
            raise RuntimeError(
                f"invalid external baseline git identity: {relative_text}"
            )
        identity = json.dumps(
            {
                "path": relative_text,
                "head": revisions[0],
                "tree": revisions[1],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(len(identity).to_bytes(8, "big"))
        digest.update(identity)
    return digest.hexdigest()


def _canonical_sha256(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _task_document(task: AcceptanceTask) -> dict[str, object]:
    return {
        "lane": task.lane,
        "environment": task.environment,
        "test_file": task.test_file,
        "process_environment": [list(item) for item in task.process_environment],
        "nested_environments": list(task.nested_environments),
    }


def _task_log_name(task: AcceptanceTask) -> str:
    identity = _canonical_sha256(_task_document(task))[:12]
    return f"{task.lane}_{Path(task.test_file).stem}_{identity}.log"


def _execution_order(
    plan: tuple[AcceptanceTask, ...],
) -> tuple[AcceptanceTask, ...]:
    ordered = tuple(
        task
        for lane in LANE_ORDER
        for task in plan
        if task.lane == lane
    )
    if len(ordered) != len(plan):
        unknown = sorted({task.lane for task in plan} - set(LANE_ORDER))
        raise ValueError(f"execution plan contains unknown lanes: {unknown}")
    test_files = [task.test_file for task in plan]
    if len(test_files) != len(set(test_files)):
        raise ValueError("execution plan contains duplicate acceptance files")
    return ordered


def _plan_identity(execution_order: tuple[AcceptanceTask, ...]) -> str:
    return _canonical_sha256(
        {
            "lane_order": list(LANE_ORDER),
            "tasks": [_task_document(task) for task in execution_order],
        }
    )


def _execution_policy(
    *,
    stop_on_failure: bool,
    timeout: float,
    cpu_jobs: int,
    runtime_environment_identity: Mapping[str, object],
) -> dict[str, object]:
    return {
        "stop_on_failure": stop_on_failure,
        "timeout_per_file_s": timeout,
        "cpu_light_jobs": cpu_jobs,
        "python_import_isolation": {
            "pythonpath": "removed",
            "python_no_user_site": "1",
        },
        "runtime_environment_identity": dict(runtime_environment_identity),
        "bound_parent_environment": _bound_parent_environment(),
    }


def _bound_parent_environment(
    environ: Mapping[str, str] | None = None,
) -> dict[str, str | None]:
    """Read the closed parent-environment contract through auditable literals."""

    source = dict(os.environ if environ is None else environ)
    return {
        "ECS_DISABLE_NATIVE_KERNELS": source.get("ECS_DISABLE_NATIVE_KERNELS"),
        "ECS_FORCE_UNFACTORIZED_AXIS1": source.get(
            "ECS_FORCE_UNFACTORIZED_AXIS1"
        ),
        "ECS_D3_DATA_ROOT": source.get("ECS_D3_DATA_ROOT"),
        "ECS_D3_MASK": source.get("ECS_D3_MASK"),
        "OMP_NUM_THREADS": source.get("OMP_NUM_THREADS"),
        "MKL_NUM_THREADS": source.get("MKL_NUM_THREADS"),
        "OPENBLAS_NUM_THREADS": source.get("OPENBLAS_NUM_THREADS"),
        "NUMEXPR_NUM_THREADS": source.get("NUMEXPR_NUM_THREADS"),
    }


def _write_json_atomic(destination: Path, payload: dict) -> None:
    """Publish JSON through a same-directory replace and clean failed temps."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def _checkpoint_row(
    result: TaskResult,
    *,
    sequence_index: int,
    expected_task: AcceptanceTask,
    run_dir: Path,
) -> dict[str, object] | None:
    """Return an authenticated terminal row, or close the resumable prefix."""

    elapsed = result.elapsed_s
    if (
        result.task != expected_task
        or type(result.returncode) is not int
        or result.returncode not in _CHECKPOINTABLE_PYTEST_RETURN_CODES
        or type(result.timed_out) is not bool
        or result.timed_out
        or result.group_cleanup_verified is not True
        or result.error is not None
        or isinstance(elapsed, bool)
        or not isinstance(elapsed, (int, float))
        or not math.isfinite(float(elapsed))
        or float(elapsed) < 0.0
    ):
        return None
    try:
        log_path = result.log_path.resolve(strict=True)
        run_root = run_dir.resolve(strict=True)
    except OSError:
        return None
    if (
        not log_path.is_file()
        or log_path.parent != run_root
        or log_path.name != _task_log_name(expected_task)
    ):
        return None
    return {
        "sequence_index": sequence_index,
        **_task_document(expected_task),
        "returncode": result.returncode,
        "timed_out": result.timed_out,
        "group_cleanup_verified": result.group_cleanup_verified,
        "elapsed_s": float(elapsed),
        "error": result.error,
        "log": log_path.name,
        "log_sha256": _sha256_file(log_path),
    }


def _validated_checkpoint_row(
    raw: object,
    *,
    sequence_index: int,
    expected_task: AcceptanceTask,
    run_dir: Path,
) -> TaskResult:
    fields = {
        "sequence_index",
        "lane",
        "environment",
        "test_file",
        "process_environment",
        "nested_environments",
        "returncode",
        "timed_out",
        "group_cleanup_verified",
        "elapsed_s",
        "error",
        "log",
        "log_sha256",
    }
    if not isinstance(raw, dict) or set(raw) != fields:
        raise ValueError("service-acceptance checkpoint row fields mismatch")
    if type(raw["sequence_index"]) is not int or raw["sequence_index"] != sequence_index:
        raise ValueError("service-acceptance checkpoint prefix is not contiguous")
    expected_identity = _task_document(expected_task)
    if any(raw[field] != value for field, value in expected_identity.items()):
        raise ValueError("service-acceptance checkpoint task identity mismatch")
    if (
        type(raw["returncode"]) is not int
        or raw["returncode"] not in _CHECKPOINTABLE_PYTEST_RETURN_CODES
    ):
        raise ValueError("service-acceptance checkpoint return code is not terminal")
    if type(raw["timed_out"]) is not bool or raw["timed_out"]:
        raise ValueError("service-acceptance checkpoint contains a timed-out row")
    if raw["group_cleanup_verified"] is not True:
        raise ValueError("service-acceptance checkpoint cleanup was not verified")
    if raw["error"] is not None:
        raise ValueError("service-acceptance checkpoint contains an execution error")
    elapsed = raw["elapsed_s"]
    if (
        isinstance(elapsed, bool)
        or not isinstance(elapsed, (int, float))
        or not math.isfinite(float(elapsed))
        or float(elapsed) < 0.0
    ):
        raise ValueError("service-acceptance checkpoint elapsed time is invalid")
    log_name = raw["log"]
    if (
        not isinstance(log_name, str)
        or not log_name
        or Path(log_name).name != log_name
        or log_name in {".", ".."}
    ):
        raise ValueError("service-acceptance checkpoint log path is invalid")
    if log_name != _task_log_name(expected_task):
        raise ValueError("service-acceptance checkpoint log identity mismatch")
    log_hash = raw["log_sha256"]
    if (
        not isinstance(log_hash, str)
        or len(log_hash) != 64
        or any(character not in "0123456789abcdef" for character in log_hash)
    ):
        raise ValueError("service-acceptance checkpoint log digest is invalid")
    log_path = (run_dir / log_name).resolve(strict=True)
    if log_path.parent != run_dir.resolve(strict=True) or not log_path.is_file():
        raise ValueError("service-acceptance checkpoint log escaped the run directory")
    if _sha256_file(log_path) != log_hash:
        raise ValueError("service-acceptance checkpoint log digest mismatch")
    return TaskResult(
        task=expected_task,
        returncode=raw["returncode"],
        timed_out=raw["timed_out"],
        group_cleanup_verified=raw["group_cleanup_verified"],
        log_path=log_path,
        elapsed_s=float(elapsed),
        error=raw["error"],
    )


def _write_checkpoint(
    checkpoint_path: Path,
    *,
    run_dir: Path,
    input_snapshot_sha256: str,
    plan_identity_sha256: str,
    execution_order: tuple[AcceptanceTask, ...],
    execution_policy: Mapping[str, object],
    completed_prefix: list[dict[str, object]],
) -> None:
    _write_json_atomic(
        checkpoint_path,
        {
            "schema": _CHECKPOINT_SCHEMA,
            "run_directory": run_dir.name,
            "input_snapshot_sha256": input_snapshot_sha256,
            "plan_identity_sha256": plan_identity_sha256,
            "task_count": len(execution_order),
            "lane_order": list(LANE_ORDER),
            "execution_policy": dict(execution_policy),
            "completed_prefix": completed_prefix,
        },
    )


def _validated_terminal_summary_status(
    summary_path: Path,
    *,
    run_dir: Path,
    input_snapshot_sha256: str,
    plan_identity_sha256: str,
    execution_order: tuple[AcceptanceTask, ...],
    execution_policy: Mapping[str, object],
    checkpoint_results: list[TaskResult],
) -> str:
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("service-acceptance prior summary is malformed") from exc
    fields = {
        "schema",
        "status",
        "cpu_light_jobs",
        "input_snapshot_sha256",
        "verified_snapshot_sha256",
        "plan_identity_sha256",
        "execution_policy",
        "resumed_prefix_count",
        "planned",
        "results",
    }
    if not isinstance(summary, dict) or set(summary) != fields:
        raise ValueError("terminal service-acceptance summary fields mismatch")
    status = summary["status"]
    if summary["schema"] != _SUMMARY_SCHEMA or status not in {"PASS", "FAIL"}:
        raise ValueError("terminal service-acceptance summary schema/status mismatch")
    if (
        summary["input_snapshot_sha256"] != input_snapshot_sha256
        or summary["verified_snapshot_sha256"] != input_snapshot_sha256
        or summary["plan_identity_sha256"] != plan_identity_sha256
    ):
        raise RuntimeError("terminal service-acceptance summary provenance mismatch")
    raw_policy = summary["execution_policy"]
    if (
        not isinstance(raw_policy, dict)
        or set(raw_policy) != set(execution_policy)
        or any(
            type(raw_policy[key]) is not type(value) or raw_policy[key] != value
            for key, value in execution_policy.items()
        )
        or type(summary["cpu_light_jobs"]) is not int
        or summary["cpu_light_jobs"] != execution_policy["cpu_light_jobs"]
    ):
        raise RuntimeError("terminal service-acceptance summary policy mismatch")
    if summary["planned"] != [_task_document(task) for task in execution_order]:
        raise RuntimeError("terminal service-acceptance summary plan mismatch")
    resumed_count = summary["resumed_prefix_count"]
    if (
        type(resumed_count) is not int
        or resumed_count < 0
        or resumed_count > len(execution_order)
    ):
        raise ValueError("terminal service-acceptance resume count is invalid")
    raw_results = summary["results"]
    if not isinstance(raw_results, list):
        raise ValueError("terminal service-acceptance results are invalid")
    expected_by_file = {task.test_file: task for task in execution_order}
    seen: set[str] = set()
    normalized: list[TaskResult] = []
    result_fields = {
        "lane",
        "environment",
        "test_file",
        "process_environment",
        "nested_environments",
        "returncode",
        "timed_out",
        "group_cleanup_verified",
        "elapsed_s",
        "error",
        "log",
        "log_sha256",
    }
    for raw in raw_results:
        if not isinstance(raw, dict) or set(raw) != result_fields:
            raise ValueError("terminal service-acceptance result fields mismatch")
        test_file = raw["test_file"]
        if not isinstance(test_file, str) or test_file in seen:
            raise ValueError("terminal service-acceptance results are duplicated")
        try:
            expected_task = expected_by_file[test_file]
        except KeyError as exc:
            raise ValueError("terminal service-acceptance result is outside plan") from exc
        seen.add(test_file)
        expected_identity = _task_document(expected_task)
        if any(raw[field] != value for field, value in expected_identity.items()):
            raise ValueError("terminal service-acceptance result identity mismatch")
        if (
            type(raw["returncode"]) is not int
            or type(raw["timed_out"]) is not bool
            or type(raw["group_cleanup_verified"]) is not bool
            or raw["error"] is not None and not isinstance(raw["error"], str)
        ):
            raise ValueError("terminal service-acceptance result types are invalid")
        elapsed = raw["elapsed_s"]
        if (
            isinstance(elapsed, bool)
            or not isinstance(elapsed, (int, float))
            or not math.isfinite(float(elapsed))
            or float(elapsed) < 0.0
        ):
            raise ValueError("terminal service-acceptance elapsed time is invalid")
        if raw["log"] != _task_log_name(expected_task):
            raise ValueError("terminal service-acceptance log identity mismatch")
        log_path = run_dir / raw["log"]
        log_hash = raw["log_sha256"]
        if log_hash is None:
            if log_path.exists() or status == "PASS":
                raise ValueError("terminal service-acceptance log evidence is missing")
        elif (
            not isinstance(log_hash, str)
            or len(log_hash) != 64
            or not log_path.is_file()
            or _sha256_file(log_path) != log_hash
        ):
            raise ValueError("terminal service-acceptance log digest mismatch")
        normalized.append(
            TaskResult(
                task=expected_task,
                returncode=raw["returncode"],
                timed_out=raw["timed_out"],
                group_cleanup_verified=raw["group_cleanup_verified"],
                log_path=log_path,
                elapsed_s=float(elapsed),
                error=raw["error"],
            )
        )
    if status == "PASS":
        if (
            len(normalized) != len(execution_order)
            or len(checkpoint_results) != len(execution_order)
            or not all(result.ok for result in normalized)
            or not all(result.ok for result in checkpoint_results)
        ):
            raise ValueError("terminal PASS lacks a complete authenticated result set")
    elif not (
        len(normalized) == len(execution_order)
        or execution_policy["stop_on_failure"]
        and any(not result.ok for result in normalized)
        or any(
            result.task.lane == "gpu_serial"
            and _must_halt_gpu_admission(result)
            for result in normalized
        )
    ):
        raise ValueError("terminal FAIL does not satisfy its execution policy")
    return status


def _load_checkpoint(
    checkpoint_path: Path,
    *,
    log_root: Path,
    input_snapshot_sha256: str,
    plan_identity_sha256: str,
    execution_order: tuple[AcceptanceTask, ...],
    execution_policy: Mapping[str, object],
) -> tuple[Path, list[dict[str, object]], list[TaskResult], str | None] | None:
    if not checkpoint_path.is_file():
        return None
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("service-acceptance checkpoint is unreadable") from exc
    fields = {
        "schema",
        "run_directory",
        "input_snapshot_sha256",
        "plan_identity_sha256",
        "task_count",
        "lane_order",
        "execution_policy",
        "completed_prefix",
    }
    if not isinstance(checkpoint, dict) or set(checkpoint) != fields:
        raise ValueError("service-acceptance checkpoint fields mismatch")
    if checkpoint["schema"] != _CHECKPOINT_SCHEMA:
        raise ValueError("unsupported service-acceptance checkpoint schema")
    if checkpoint["input_snapshot_sha256"] != input_snapshot_sha256:
        raise RuntimeError("service-acceptance checkpoint input snapshot mismatch")
    if checkpoint["plan_identity_sha256"] != plan_identity_sha256:
        raise RuntimeError("service-acceptance checkpoint semantic plan mismatch")
    if (
        type(checkpoint["task_count"]) is not int
        or checkpoint["task_count"] != len(execution_order)
        or checkpoint["lane_order"] != list(LANE_ORDER)
    ):
        raise RuntimeError("service-acceptance checkpoint execution topology mismatch")
    raw_policy = checkpoint["execution_policy"]
    if (
        not isinstance(raw_policy, dict)
        or set(raw_policy) != set(execution_policy)
        or any(
            type(raw_policy[key]) is not type(value) or raw_policy[key] != value
            for key, value in execution_policy.items()
        )
    ):
        raise RuntimeError("service-acceptance checkpoint execution policy mismatch")
    run_name = checkpoint["run_directory"]
    if (
        not isinstance(run_name, str)
        or not run_name
        or Path(run_name).name != run_name
        or run_name in {".", ".."}
    ):
        raise ValueError("service-acceptance checkpoint run directory is invalid")
    run_dir = (log_root / run_name).resolve(strict=True)
    if run_dir.parent != log_root.resolve(strict=True) or not run_dir.is_dir():
        raise ValueError("service-acceptance checkpoint run directory escaped log root")
    summary_path = run_dir / "summary.json"
    raw_prefix = checkpoint["completed_prefix"]
    if not isinstance(raw_prefix, list) or len(raw_prefix) > len(execution_order):
        raise ValueError("service-acceptance checkpoint prefix is invalid")
    normalized: list[dict[str, object]] = []
    results: list[TaskResult] = []
    for index, raw_row in enumerate(raw_prefix, start=1):
        result = _validated_checkpoint_row(
            raw_row,
            sequence_index=index,
            expected_task=execution_order[index - 1],
            run_dir=run_dir,
        )
        normalized.append(dict(raw_row))
        results.append(result)
    terminal_status: str | None = None
    if summary_path.is_file():
        try:
            prior_status = json.loads(summary_path.read_text(encoding="utf-8"))["status"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError("service-acceptance prior summary is malformed") from exc
        if prior_status != "INTERRUPTED":
            terminal_status = _validated_terminal_summary_status(
                summary_path,
                run_dir=run_dir,
                input_snapshot_sha256=input_snapshot_sha256,
                plan_identity_sha256=plan_identity_sha256,
                execution_order=execution_order,
                execution_policy=execution_policy,
                checkpoint_results=results,
            )
    return run_dir, normalized, results, terminal_status


def _run_one(
    task: AcceptanceTask,
    *,
    index: int,
    conda: str,
    timeout: float,
    log_dir: Path,
    child_env: Mapping[str, str],
) -> TaskResult:
    del index
    log_path = log_dir / _task_log_name(task)
    started = time.monotonic()
    try:
        result = proc.run(
            [
                conda,
                "run",
                "-n",
                task.environment,
                "python",
                "-m",
                "pytest",
                "-q",
                task.test_file,
            ],
            cwd=str(REPO),
            env=_task_child_environment(task, child_env),
            timeout=timeout,
            log_path=str(log_path),
        )
        return TaskResult(
            task=task,
            returncode=result.returncode,
            timed_out=result.timed_out,
            group_cleanup_verified=getattr(result, "group_cleanup_verified", False),
            log_path=log_path,
            elapsed_s=time.monotonic() - started,
        )
    except Exception as exc:
        return TaskResult(
            task=task,
            returncode=-1,
            timed_out=False,
            group_cleanup_verified=False,
            log_path=log_path,
            elapsed_s=time.monotonic() - started,
            error=f"{type(exc).__name__}: {exc}",
        )


def _report_result(result: TaskResult, *, completed: int, total: int) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(
        f"[{completed:02d}/{total:02d}] {status} {result.task.lane} "
        f"{result.task.environment}: {result.task.test_file} ({result.elapsed_s:.2f}s)",
        flush=True,
    )
    if not result.ok:
        print(_tail(result.log_path), flush=True)


def _run_serial(
    tasks: tuple[AcceptanceTask, ...],
    *,
    indices: Mapping[str, int],
    conda: str,
    timeout: float,
    log_dir: Path,
    child_env: Mapping[str, str],
    completed_offset: int,
    total: int,
    stop_on_failure: bool,
    on_result: Callable[[TaskResult], None] | None = None,
) -> list[TaskResult]:
    results: list[TaskResult] = []
    for task in tasks:
        result = _run_one(
            task,
            index=indices[task.test_file],
            conda=conda,
            timeout=timeout,
            log_dir=log_dir,
            child_env=child_env,
        )
        results.append(result)
        if on_result is not None:
            on_result(result)
        _report_result(result, completed=completed_offset + len(results), total=total)
        if (stop_on_failure and not result.ok) or (
            task.lane == "gpu_serial" and _must_halt_gpu_admission(result)
        ):
            break
    return results


def _must_halt_gpu_admission(result: TaskResult) -> bool:
    """Fail closed after native-fatal or unverifiably cleaned GPU work."""

    return (
        type(result.returncode) is not int
        or result.returncode not in _CHECKPOINTABLE_PYTEST_RETURN_CODES
        or type(result.timed_out) is not bool
        or result.timed_out
        or result.group_cleanup_verified is not True
    )


def _run_cpu_light_parallel(
    tasks: tuple[AcceptanceTask, ...],
    *,
    jobs: int,
    indices: Mapping[str, int],
    conda: str,
    timeout: float,
    log_dir: Path,
    child_env: Mapping[str, str],
    total: int,
    on_result: Callable[[TaskResult], None] | None = None,
) -> list[TaskResult]:
    """Launch subprocesses concurrently; aggregate results on this single owner."""

    results: list[TaskResult] = []
    with ThreadPoolExecutor(max_workers=jobs, thread_name_prefix="ecs-accept") as executor:
        futures: dict[Future[TaskResult], AcceptanceTask] = {
            executor.submit(
                _run_one,
                task,
                index=indices[task.test_file],
                conda=conda,
                timeout=timeout,
                log_dir=log_dir,
                child_env=child_env,
            ): task
            for task in tasks
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if on_result is not None:
                on_result(result)
            _report_result(result, completed=len(results), total=total)
    return results


def _write_summary(
    run_dir: Path,
    *,
    plan: tuple[AcceptanceTask, ...],
    results: list[TaskResult],
    status: str,
    cpu_jobs: int,
    input_snapshot_sha256: str,
    verified_snapshot_sha256: str,
    plan_identity_sha256: str,
    execution_policy: Mapping[str, object],
    resumed_prefix_count: int,
) -> None:
    """Single-writer, atomic publication prevents partial/racing summaries."""

    payload = {
        "schema": _SUMMARY_SCHEMA,
        "status": status,
        "cpu_light_jobs": cpu_jobs,
        "input_snapshot_sha256": input_snapshot_sha256,
        "verified_snapshot_sha256": verified_snapshot_sha256,
        "plan_identity_sha256": plan_identity_sha256,
        "execution_policy": dict(execution_policy),
        "resumed_prefix_count": resumed_prefix_count,
        "planned": [asdict(task) for task in plan],
        "results": [
            {
                **asdict(result.task),
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "group_cleanup_verified": result.group_cleanup_verified,
                "elapsed_s": result.elapsed_s,
                "error": result.error,
                "log": result.log_path.name,
                "log_sha256": (
                    _sha256_file(result.log_path)
                    if result.log_path.is_file()
                    else None
                ),
            }
            for result in sorted(results, key=lambda row: row.task.test_file)
        ],
    }
    _write_json_atomic(run_dir / "summary.json", payload)


def _run_plan_locked(
    plan: tuple[AcceptanceTask, ...],
    *,
    log_root: Path,
    stop_on_failure: bool,
) -> bool:
    conda = shutil.which("conda")
    if conda is None:
        raise RuntimeError("conda is required to enforce the catalog environment boundary")
    config = MappingProxyType(_config())
    timeout = _timeout_per_file(config)
    cpu_jobs, memory_cap = _cpu_light_jobs(config)
    if stop_on_failure:
        cpu_jobs = 1
    ordered_plan = _execution_order(plan)
    plan_identity_sha256 = _plan_identity(ordered_plan)
    runtime_environment_identity = _runtime_environment_identity(conda, ordered_plan)
    policy = MappingProxyType(
        _execution_policy(
            stop_on_failure=stop_on_failure,
            timeout=timeout,
            cpu_jobs=cpu_jobs,
            runtime_environment_identity=runtime_environment_identity,
        )
    )
    input_snapshot_sha256 = _acceptance_input_snapshot()
    checkpoint_path = log_root / _CHECKPOINT_NAME
    loaded = _load_checkpoint(
        checkpoint_path,
        log_root=log_root,
        input_snapshot_sha256=input_snapshot_sha256,
        plan_identity_sha256=plan_identity_sha256,
        execution_order=ordered_plan,
        execution_policy=policy,
    )
    if loaded is None:
        run_dir = _new_run_log_dir(log_root)
        completed_prefix: list[dict[str, object]] = []
        resumed_results: list[TaskResult] = []
        terminal_status = None
        _write_checkpoint(
            checkpoint_path,
            run_dir=run_dir,
            input_snapshot_sha256=input_snapshot_sha256,
            plan_identity_sha256=plan_identity_sha256,
            execution_order=ordered_plan,
            execution_policy=policy,
            completed_prefix=completed_prefix,
        )
    else:
        run_dir, completed_prefix, resumed_results, terminal_status = loaded
    if terminal_status is not None:
        checkpoint_path.unlink()
        checkpoint_path.with_name(f".{checkpoint_path.name}.tmp").unlink(
            missing_ok=True
        )
        print(
            "SERVICE ACCEPTANCE: recovered published terminal "
            f"{terminal_status} ({_display_path(run_dir)})",
            flush=True,
        )
        return terminal_status == "PASS"
    resumed_prefix_count = len(resumed_results)
    immutable_env = MappingProxyType(dict(os.environ))
    cpu_env = MappingProxyType(_cpu_child_environment(immutable_env))
    indices = MappingProxyType({task.test_file: i for i, task in enumerate(plan, start=1)})
    execution_indices = MappingProxyType(
        {task.test_file: index for index, task in enumerate(ordered_plan)}
    )
    pending_plan = ordered_plan[resumed_prefix_count:]
    lanes = {
        lane: tuple(task for task in pending_plan if task.lane == lane)
        for lane in LANE_ORDER
    }

    print(
        f"SERVICE ACCEPTANCE: {len(plan)} fresh processes; "
        f"resume_prefix={resumed_prefix_count}, "
        f"remaining_cpu_light={len(lanes['cpu_light'])}@{cpu_jobs}, "
        f"remaining_cpu_exclusive={len(lanes['cpu_exclusive'])}, "
        f"remaining_gpu_serial={len(lanes['gpu_serial'])}; "
        f"memory_cap={memory_cap or 'unavailable'}, timeout={timeout:g}s/file; "
        f"logs={_display_path(run_dir)}",
        flush=True,
    )

    result_by_index: dict[int, TaskResult] = {
        index: result for index, result in enumerate(resumed_results)
    }

    def record_result(result: TaskResult) -> None:
        try:
            index = execution_indices[result.task.test_file]
        except KeyError as exc:
            raise ValueError(
                f"acceptance result is outside the execution plan: {result.task.test_file}"
            ) from exc
        existing = result_by_index.get(index)
        if existing is not None:
            if existing != result:
                raise ValueError(
                    f"conflicting duplicate acceptance result: {result.task.test_file}"
                )
            return
        result_by_index[index] = result
        while len(completed_prefix) < len(ordered_plan):
            next_index = len(completed_prefix)
            next_result = result_by_index.get(next_index)
            if next_result is None:
                break
            row = _checkpoint_row(
                next_result,
                sequence_index=next_index + 1,
                expected_task=ordered_plan[next_index],
                run_dir=run_dir,
            )
            if row is None:
                break
            completed_prefix.append(row)
            _write_checkpoint(
                checkpoint_path,
                run_dir=run_dir,
                input_snapshot_sha256=input_snapshot_sha256,
                plan_identity_sha256=plan_identity_sha256,
                execution_order=ordered_plan,
                execution_policy=policy,
                completed_prefix=completed_prefix,
            )

    def record_phase(phase: list[TaskResult]) -> None:
        # Real runners call record_result immediately.  This second pass keeps
        # test doubles and future runner implementations on the same contract.
        for result in phase:
            record_result(result)

    def assert_provenance_unchanged(context: str) -> None:
        current = _acceptance_input_snapshot()
        if current != input_snapshot_sha256:
            raise RuntimeError(
                "service-acceptance input snapshot drifted "
                f"{context}: {input_snapshot_sha256} -> {current}"
            )
        current_runtime = _runtime_environment_identity(conda, ordered_plan)
        if current_runtime != runtime_environment_identity:
            raise RuntimeError(
                "service-acceptance runtime environment drifted "
                f"{context}"
            )

    execution_error: BaseException | None = None
    try:
        resumed_failure = stop_on_failure and any(
            not result.ok for result in resumed_results
        )
        if stop_on_failure and not resumed_failure:
            for lane in LANE_ORDER:
                tasks = lanes[lane]
                if not tasks:
                    continue
                assert_provenance_unchanged(f"before {lane}")
                if lane == "gpu_serial":
                    with gpu_pool.acquire_gpu_slot() as slot:
                        print(f"GPU LEASE: slot {slot.slot}", flush=True)
                        child_env = MappingProxyType(slot.child_env(immutable_env))
                        phase = _run_serial(
                            tasks,
                            indices=indices,
                            conda=conda,
                            timeout=timeout,
                            log_dir=run_dir,
                            child_env=child_env,
                            completed_offset=len(result_by_index),
                            total=len(plan),
                            stop_on_failure=True,
                            on_result=record_result,
                        )
                else:
                    phase = _run_serial(
                        tasks,
                        indices=indices,
                        conda=conda,
                        timeout=timeout,
                        log_dir=run_dir,
                        child_env=cpu_env,
                        completed_offset=len(result_by_index),
                        total=len(plan),
                        stop_on_failure=True,
                        on_result=record_result,
                    )
                record_phase(phase)
                assert_provenance_unchanged(f"after {lane}")
                if any(not result.ok for result in phase):
                    break
        elif not stop_on_failure:
            if lanes["cpu_light"]:
                assert_provenance_unchanged("before cpu_light")
                phase = _run_cpu_light_parallel(
                    lanes["cpu_light"],
                    jobs=cpu_jobs,
                    indices=indices,
                    conda=conda,
                    timeout=timeout,
                    log_dir=run_dir,
                    child_env=cpu_env,
                    total=len(plan),
                    on_result=record_result,
                )
                record_phase(phase)
                assert_provenance_unchanged("after cpu_light")
            if lanes["cpu_exclusive"]:
                assert_provenance_unchanged("before cpu_exclusive")
                phase = _run_serial(
                    lanes["cpu_exclusive"],
                    indices=indices,
                    conda=conda,
                    timeout=timeout,
                    log_dir=run_dir,
                    child_env=cpu_env,
                    completed_offset=len(result_by_index),
                    total=len(plan),
                    stop_on_failure=False,
                    on_result=record_result,
                )
                record_phase(phase)
                assert_provenance_unchanged("after cpu_exclusive")
            if lanes["gpu_serial"]:
                # The lease covers only the contiguous GPU phase.  Each file still
                # execs in a fresh process, resetting its CUDA/native allocator.
                assert_provenance_unchanged("before gpu_serial")
                with gpu_pool.acquire_gpu_slot() as slot:
                    print(f"GPU LEASE: slot {slot.slot}", flush=True)
                    gpu_env = MappingProxyType(slot.child_env(immutable_env))
                    phase = _run_serial(
                        lanes["gpu_serial"],
                        indices=indices,
                        conda=conda,
                        timeout=timeout,
                        log_dir=run_dir,
                        child_env=gpu_env,
                        completed_offset=len(result_by_index),
                        total=len(plan),
                        stop_on_failure=False,
                        on_result=record_result,
                    )
                record_phase(phase)
                assert_provenance_unchanged("after gpu_serial")
    except BaseException as exc:
        execution_error = exc

    verified_snapshot_sha256 = _acceptance_input_snapshot()
    if verified_snapshot_sha256 != input_snapshot_sha256 and execution_error is None:
        execution_error = RuntimeError(
            "service-acceptance input snapshot drifted before summary publication: "
            f"{input_snapshot_sha256} -> {verified_snapshot_sha256}"
        )
    verified_runtime_identity = _runtime_environment_identity(conda, ordered_plan)
    if verified_runtime_identity != runtime_environment_identity and execution_error is None:
        execution_error = RuntimeError(
            "service-acceptance runtime environment drifted before summary publication"
        )
    try:
        for index, row in enumerate(completed_prefix, start=1):
            _validated_checkpoint_row(
                row,
                sequence_index=index,
                expected_task=ordered_plan[index - 1],
                run_dir=run_dir,
            )
    except BaseException as exc:
        if execution_error is None:
            execution_error = exc
    results = [result_by_index[index] for index in sorted(result_by_index)]
    gpu_safety_halt = any(
        result.task.lane == "gpu_serial" and _must_halt_gpu_admission(result)
        for result in results
    )
    terminal_by_policy = (
        len(results) == len(plan)
        or stop_on_failure and any(not result.ok for result in results)
        or gpu_safety_halt
    )
    authenticated_complete = len(completed_prefix) == len(plan)
    status = (
        "INTERRUPTED"
        if execution_error is not None or not terminal_by_policy
        else "PASS"
        if (
            len(results) == len(plan)
            and authenticated_complete
            and all(result.ok for result in results)
        )
        else "FAIL"
    )
    _write_summary(
        run_dir,
        plan=ordered_plan,
        results=results,
        status=status,
        cpu_jobs=cpu_jobs,
        input_snapshot_sha256=input_snapshot_sha256,
        verified_snapshot_sha256=verified_snapshot_sha256,
        plan_identity_sha256=plan_identity_sha256,
        execution_policy=policy,
        resumed_prefix_count=resumed_prefix_count,
    )
    if status != "INTERRUPTED":
        checkpoint_path.unlink(missing_ok=True)
        checkpoint_path.with_name(f".{checkpoint_path.name}.tmp").unlink(missing_ok=True)
    if execution_error is not None:
        raise execution_error

    failures = [result for result in results if not result.ok]
    if status != "PASS":
        print("SERVICE ACCEPTANCE: FAIL", flush=True)
        for result in failures:
            print(
                f"- {result.task.test_file}: returncode={result.returncode}, "
                f"timed_out={result.timed_out}, "
                f"group_cleanup_verified={result.group_cleanup_verified}, "
                f"error={result.error}, "
                f"log={_display_path(result.log_path)}",
                flush=True,
            )
        if not authenticated_complete:
            print(
                "- aggregate authentication incomplete: "
                f"prefix={len(completed_prefix)}/{len(plan)}",
                flush=True,
            )
        return False
    print(f"SERVICE ACCEPTANCE: PASS ({_display_path(run_dir)})", flush=True)
    return True


def run_plan(
    plan: tuple[AcceptanceTask, ...],
    *,
    log_root: Path,
    stop_on_failure: bool,
) -> bool:
    """Run or resume one exact plan under a single cross-process writer lock."""

    log_root.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(str(log_root / _LOCK_NAME), os.O_CREAT | os.O_WRONLY, 0o644)
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    try:
        return _run_plan_locked(
            plan,
            log_root=log_root,
            stop_on_failure=stop_on_failure,
        )
    finally:
        os.close(lock_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="print the immutable plan only")
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="disable CPU concurrency and stop admission after the first failing file",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_ROOT,
        help="log root; each invocation creates a unique run subdirectory",
    )
    args = parser.parse_args(argv)

    plan = acceptance_plan(load_catalog())
    if args.list:
        for task in plan:
            print(f"{task.lane}\t{task.environment}\t{task.test_file}")
        return 0
    return 0 if run_plan(
        plan,
        log_root=args.log_dir,
        stop_on_failure=args.stop_on_failure,
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())

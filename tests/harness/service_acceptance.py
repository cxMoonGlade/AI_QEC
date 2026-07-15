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
import json
import math
import os
from pathlib import Path
import signal
import shutil
import sys
import time
from types import MappingProxyType
from typing import Mapping
import uuid


TESTS_ROOT = Path(__file__).resolve().parents[1]
REPO = TESTS_ROOT.parent
sys.path.insert(0, str(TESTS_ROOT))

from harness import gpu_pool, proc  # noqa: E402


CATALOG_PATH = REPO / "docs" / "service_status.json"
CONFIG_PATH = TESTS_ROOT / "harness_config.json"
DEFAULT_LOG_ROOT = REPO / "outputs" / "simulator_validation" / "logs" / "service_acceptance"
LANE_ORDER = ("cpu_light", "cpu_exclusive", "gpu_serial")
_ALLOWED_PROCESS_ENVIRONMENT = frozenset({"PYTORCH_ALLOC_CONF"})
_PROTECTED_GPU_ENVIRONMENT = frozenset({"CUDA_VISIBLE_DEVICES", "ECS_GPU_SLOT"})


@dataclass(frozen=True, slots=True)
class AcceptanceTask:
    """One immutable fresh-process admission unit."""

    lane: str
    environment: str
    test_file: str
    process_environment: tuple[tuple[str, str], ...] = ()


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
            and self.group_cleanup_verified
            and not self.timed_out
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
    return tuple(
        AcceptanceTask(
            lane=lane_by_file.get(path, default_lane),
            environment=environment_overrides.get(path, default_environment),
            test_file=path,
            process_environment=process_environment_by_file.get(path, ()),
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
    child.update(overrides)
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

    configured = int(os.environ.get("ECS_ACCEPTANCE_CPU_JOBS", int(config["cpu_light_jobs"])))
    if configured < 1:
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
    return min(configured, cpu_cap, memory_cap or configured), memory_cap


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


def _run_one(
    task: AcceptanceTask,
    *,
    index: int,
    conda: str,
    timeout: float,
    log_dir: Path,
    child_env: Mapping[str, str],
) -> TaskResult:
    log_path = log_dir / f"{index:03d}_{task.lane}_{Path(task.test_file).stem}.log"
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
        _report_result(result, completed=completed_offset + len(results), total=total)
        if (stop_on_failure and not result.ok) or (
            task.lane == "gpu_serial" and _must_halt_gpu_admission(result)
        ):
            break
    return results


def _must_halt_gpu_admission(result: TaskResult) -> bool:
    """Fail closed after native-fatal or unverifiably cleaned GPU work."""

    native_fatal_codes = {
        128 + signal.SIGABRT,
        128 + signal.SIGSEGV,
        -signal.SIGABRT,
        -signal.SIGSEGV,
    }
    return (
        result.timed_out
        or not result.group_cleanup_verified
        or result.returncode in native_fatal_codes
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
            _report_result(result, completed=len(results), total=total)
    return results


def _write_summary(
    run_dir: Path,
    *,
    plan: tuple[AcceptanceTask, ...],
    results: list[TaskResult],
    status: str,
    cpu_jobs: int,
) -> None:
    """Single-writer, atomic publication prevents partial/racing summaries."""

    payload = {
        "schema": "error_coupling_simulator.service_acceptance_run.v2",
        "status": status,
        "cpu_light_jobs": cpu_jobs,
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
            }
            for result in sorted(results, key=lambda row: row.task.test_file)
        ],
    }
    temporary = run_dir / ".summary.json.tmp"
    destination = run_dir / "summary.json"
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def run_plan(
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
    run_dir = _new_run_log_dir(log_root)
    immutable_env = MappingProxyType(dict(os.environ))
    indices = MappingProxyType({task.test_file: i for i, task in enumerate(plan, start=1)})
    lanes = {
        lane: tuple(task for task in plan if task.lane == lane)
        for lane in LANE_ORDER
    }
    if sum(len(tasks) for tasks in lanes.values()) != len(plan):
        unknown = sorted({task.lane for task in plan} - set(LANE_ORDER))
        raise ValueError(f"execution plan contains unknown lanes: {unknown}")

    print(
        f"SERVICE ACCEPTANCE: {len(plan)} fresh processes; "
        f"cpu_light={len(lanes['cpu_light'])}@{cpu_jobs}, "
        f"cpu_exclusive={len(lanes['cpu_exclusive'])}, "
        f"gpu_serial={len(lanes['gpu_serial'])}; "
        f"memory_cap={memory_cap or 'unavailable'}, timeout={timeout:g}s/file; "
        f"logs={_display_path(run_dir)}",
        flush=True,
    )

    results: list[TaskResult] = []
    interrupted = True
    try:
        if stop_on_failure:
            for lane in LANE_ORDER:
                tasks = lanes[lane]
                if not tasks:
                    continue
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
                            completed_offset=len(results),
                            total=len(plan),
                            stop_on_failure=True,
                        )
                else:
                    phase = _run_serial(
                        tasks,
                        indices=indices,
                        conda=conda,
                        timeout=timeout,
                        log_dir=run_dir,
                        child_env=immutable_env,
                        completed_offset=len(results),
                        total=len(plan),
                        stop_on_failure=True,
                    )
                results.extend(phase)
                if any(not result.ok for result in phase):
                    break
        else:
            results.extend(
                _run_cpu_light_parallel(
                    lanes["cpu_light"],
                    jobs=cpu_jobs,
                    indices=indices,
                    conda=conda,
                    timeout=timeout,
                    log_dir=run_dir,
                    child_env=immutable_env,
                    total=len(plan),
                )
            )
            results.extend(
                _run_serial(
                    lanes["cpu_exclusive"],
                    indices=indices,
                    conda=conda,
                    timeout=timeout,
                    log_dir=run_dir,
                    child_env=immutable_env,
                    completed_offset=len(results),
                    total=len(plan),
                    stop_on_failure=False,
                )
            )
            if lanes["gpu_serial"]:
                # The lease covers only the contiguous GPU phase.  Each file still
                # execs in a fresh process, resetting its CUDA/native allocator.
                with gpu_pool.acquire_gpu_slot() as slot:
                    print(f"GPU LEASE: slot {slot.slot}", flush=True)
                    gpu_env = MappingProxyType(slot.child_env(immutable_env))
                    results.extend(
                        _run_serial(
                            lanes["gpu_serial"],
                            indices=indices,
                            conda=conda,
                            timeout=timeout,
                            log_dir=run_dir,
                            child_env=gpu_env,
                            completed_offset=len(results),
                            total=len(plan),
                            stop_on_failure=False,
                        )
                    )
        interrupted = False
    finally:
        status = (
            "INTERRUPTED"
            if interrupted
            else "PASS"
            if len(results) == len(plan) and all(result.ok for result in results)
            else "FAIL"
        )
        _write_summary(
            run_dir,
            plan=plan,
            results=results,
            status=status,
            cpu_jobs=cpu_jobs,
        )

    failures = [result for result in results if not result.ok]
    if failures or len(results) != len(plan):
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
        return False
    print(f"SERVICE ACCEPTANCE: PASS ({_display_path(run_dir)})", flush=True)
    return True


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

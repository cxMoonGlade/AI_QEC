"""Execution-topology regressions for the catalog acceptance supervisor."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import signal
from types import MappingProxyType, SimpleNamespace

import pytest

from harness import service_acceptance as acceptance


@pytest.fixture(autouse=True)
def _stable_runtime_environment_identity(monkeypatch) -> None:
    monkeypatch.setattr(
        acceptance,
        "_runtime_environment_identity",
        lambda _conda, _plan: {"test_runtime": "stable"},
        raising=False,
    )


def _ok(task: acceptance.AcceptanceTask, log_dir: Path) -> acceptance.TaskResult:
    log_path = log_dir / acceptance._task_log_name(task)
    log_path.write_text("pytest completed\n", encoding="utf-8")
    return acceptance.TaskResult(
        task=task,
        returncode=0,
        timed_out=False,
        group_cleanup_verified=True,
        log_path=log_path,
        elapsed_s=0.01,
    )


def test_supervisor_source_does_not_import_a_native_compute_runtime() -> None:
    source = Path(acceptance.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert imported_roots.isdisjoint({"torch", "cupy", "qutip", "cudaq"})


def test_cpu_admission_is_bounded_by_available_memory(monkeypatch) -> None:
    config = {
        "cpu_light_jobs": 8,
        "host_memory_reserve_gib": 4,
        "cpu_light_memory_gib_per_job": 2,
    }
    monkeypatch.delenv("ECS_ACCEPTANCE_CPU_JOBS", raising=False)
    monkeypatch.setattr(acceptance.os, "cpu_count", lambda: 16)
    monkeypatch.setattr(
        acceptance,
        "_available_memory_bytes",
        lambda: 12 * 1024 ** 3,
    )

    jobs, memory_cap = acceptance._cpu_light_jobs(config)

    assert memory_cap == 4
    assert jobs == 4


def test_cpu_admission_never_exceeds_four_worker_ceiling(monkeypatch) -> None:
    config = {
        "cpu_light_jobs": 12,
        "host_memory_reserve_gib": 0,
        "cpu_light_memory_gib_per_job": 1,
    }
    monkeypatch.setenv("ECS_ACCEPTANCE_CPU_JOBS", "12")
    monkeypatch.setattr(acceptance.os, "cpu_count", lambda: 32)
    monkeypatch.setattr(
        acceptance,
        "_available_memory_bytes",
        lambda: 32 * 1024 ** 3,
    )

    jobs, memory_cap = acceptance._cpu_light_jobs(config)

    assert memory_cap == 32
    assert jobs == 4


def test_each_invocation_allocates_a_unique_log_directory(tmp_path: Path) -> None:
    first = acceptance._new_run_log_dir(tmp_path)
    second = acceptance._new_run_log_dir(tmp_path)

    assert first != second
    assert first.is_dir()
    assert second.is_dir()


def test_environment_metadata_identity_binds_conda_pip_and_import_hooks(
    tmp_path: Path,
) -> None:
    prefix = tmp_path / "envs" / "ecs"
    conda_meta = prefix / "conda-meta"
    dist_info = prefix / "lib" / "python3.12" / "site-packages" / "demo.dist-info"
    conda_meta.mkdir(parents=True)
    dist_info.mkdir(parents=True)
    (conda_meta / "history").write_text("create specs: demo\n", encoding="utf-8")
    (conda_meta / "demo-1.0-0.json").write_text(
        '{"name":"demo","version":"1.0"}\n',
        encoding="utf-8",
    )
    (dist_info / "METADATA").write_text(
        "Name: demo\nVersion: 1.0\n",
        encoding="utf-8",
    )
    import_hook = dist_info.parent / "editable-demo.pth"
    import_hook.write_text("/workspace/demo\n", encoding="utf-8")

    first = acceptance._environment_metadata_identity(prefix)
    second = acceptance._environment_metadata_identity(prefix)
    import_hook.write_text("/different/source\n", encoding="utf-8")
    changed = acceptance._environment_metadata_identity(prefix)

    assert first == second
    assert first["prefix"] == str(prefix.resolve())
    assert first["metadata_file_count"] == 4
    assert first["metadata_sha256"] != changed["metadata_sha256"]


def test_environment_prefix_resolution_fails_closed_on_missing_or_ambiguous_name(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first" / "envs" / "ecs"
    second = tmp_path / "second" / "envs" / "ecs"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="missing named Conda environment"):
        acceptance._environment_prefixes_from_payload(
            {"envs": [str(first)]},
            ("aiqec",),
        )
    with pytest.raises(RuntimeError, match="ambiguous named Conda environment"):
        acceptance._environment_prefixes_from_payload(
            {"envs": [str(first), str(second)]},
            ("ecs",),
        )


def test_acceptance_snapshot_binds_the_authoritative_core_environment_lock(
    monkeypatch,
    tmp_path: Path,
) -> None:
    assert "core-environment-cu130.lock" in acceptance._SNAPSHOT_FILE_INPUTS
    lock = tmp_path / "core-environment-cu130.lock"
    lock.write_text("version-one\n", encoding="utf-8")
    monkeypatch.setattr(acceptance, "REPO", tmp_path)
    monkeypatch.setattr(acceptance, "_SNAPSHOT_DIRECTORY_INPUTS", ())
    monkeypatch.setattr(
        acceptance,
        "_SNAPSHOT_FILE_INPUTS",
        ("core-environment-cu130.lock",),
    )

    before = acceptance._acceptance_input_snapshot()
    lock.write_text("version-two\n", encoding="utf-8")

    assert acceptance._acceptance_input_snapshot() != before


def test_gpu_lease_wraps_only_gpu_lane(monkeypatch, tmp_path: Path) -> None:
    plan = (
        acceptance.AcceptanceTask("cpu_light", "ecs", "tests/light.py"),
        acceptance.AcceptanceTask("cpu_exclusive", "ecs", "tests/heavy.py"),
        acceptance.AcceptanceTask("gpu_serial", "aiqec", "tests/gpu.py"),
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    events: list[tuple[str, str | None]] = []
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "parent-visible")
    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 2,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def fake_parallel(tasks, **kwargs):
        events.append(("cpu_light", kwargs["child_env"]["CUDA_VISIBLE_DEVICES"]))
        return [_ok(task, run_dir) for task in tasks]

    def fake_serial(tasks, **kwargs):
        if not tasks:
            return []
        lane = tasks[0].lane
        events.append((lane, kwargs["child_env"]["CUDA_VISIBLE_DEVICES"]))
        return [_ok(task, run_dir) for task in tasks]

    class Slot:
        slot = 7

        def __enter__(self):
            events.append(("acquire", None))
            return self

        def __exit__(self, *_args):
            events.append(("release", None))

        def child_env(self, base_env):
            child = dict(base_env)
            child["CUDA_VISIBLE_DEVICES"] = "7"
            child["ECS_GPU_SLOT"] = "7"
            return child

    monkeypatch.setattr(acceptance, "_run_cpu_light_parallel", fake_parallel)
    monkeypatch.setattr(acceptance, "_run_serial", fake_serial)
    monkeypatch.setattr(acceptance.gpu_pool, "acquire_gpu_slot", Slot)

    assert acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)
    assert events == [
        ("cpu_light", ""),
        ("cpu_exclusive", ""),
        ("acquire", None),
        ("gpu_serial", "7"),
        ("release", None),
    ]
    assert acceptance.os.environ["CUDA_VISIBLE_DEVICES"] == "parent-visible"


def _minimal_catalog(*test_files: str) -> dict:
    return {
        "acceptance_execution": {
            "isolation": "one_test_file_per_process",
            "default_conda_environment": "ecs",
            "environment_overrides": {},
            "process_environment_overrides": {},
            "nested_environment_overrides": {},
            "default_lane": "cpu_light",
            "lane_overrides": {},
        },
        "services": [{"acceptance": list(test_files)}],
    }


def test_acceptance_plan_freezes_per_file_process_environment() -> None:
    catalog = _minimal_catalog("tests/plain.py", "tests/pepo.py")
    configured = {"PYTORCH_ALLOC_CONF": "expandable_segments:True"}
    catalog["acceptance_execution"]["process_environment_overrides"] = {
        "tests/pepo.py": configured,
    }

    plan = acceptance.acceptance_plan(catalog)
    configured["PYTORCH_ALLOC_CONF"] = "mutated-after-plan"

    assert plan == (
        acceptance.AcceptanceTask("cpu_light", "ecs", "tests/pepo.py", (
            ("PYTORCH_ALLOC_CONF", "expandable_segments:True"),
        )),
        acceptance.AcceptanceTask("cpu_light", "ecs", "tests/plain.py"),
    )


def test_acceptance_plan_freezes_nested_environment_dependencies() -> None:
    catalog = _minimal_catalog("tests/external.py", "tests/plain.py")
    configured = ["ecs-baseline-yastn", "ecs-baseline-aer"]
    catalog["acceptance_execution"]["nested_environment_overrides"] = {
        "tests/external.py": configured,
    }

    plan = acceptance.acceptance_plan(catalog)
    configured.append("mutated-after-plan")

    assert plan == (
        acceptance.AcceptanceTask(
            "cpu_light",
            "ecs",
            "tests/external.py",
            nested_environments=("ecs-baseline-aer", "ecs-baseline-yastn"),
        ),
        acceptance.AcceptanceTask("cpu_light", "ecs", "tests/plain.py"),
    )


def test_current_catalog_binds_every_direct_and_nested_runtime_environment() -> None:
    plan = acceptance.acceptance_plan(acceptance.load_catalog())

    assert acceptance._required_runtime_environments(plan) == (
        "aiqec",
        "ecs",
        "ecs-baseline-aer",
        "ecs-baseline-yastn",
    )


def test_current_catalog_routes_cuda_transitive_mps_gate_to_gpu_serial() -> None:
    plan = acceptance.acceptance_plan(acceptance.load_catalog())
    by_file = {task.test_file: task for task in plan}

    assert by_file["tests/test_mps_qt_transitive_semantics.py"].lane == "gpu_serial"


def test_acceptance_plan_rejects_non_acceptance_process_environment_path() -> None:
    catalog = _minimal_catalog("tests/current.py")
    catalog["acceptance_execution"]["process_environment_overrides"] = {
        "tests/stale.py": {"PYTORCH_ALLOC_CONF": "expandable_segments:True"},
    }

    with pytest.raises(ValueError, match="non-acceptance files"):
        acceptance.acceptance_plan(catalog)


@pytest.mark.parametrize(
    "name",
    ["ECS_RUN_AER_MPS_COMPARISON", "ECS_RUN_YASTN_MPS_COMPARISON"],
)
def test_acceptance_plan_allows_external_mps_baseline_run_flags(
    name: str,
) -> None:
    catalog = _minimal_catalog("tests/external_mps.py")
    catalog["acceptance_execution"]["process_environment_overrides"] = {
        "tests/external_mps.py": {name: "1"},
    }

    assert acceptance.acceptance_plan(catalog) == (
        acceptance.AcceptanceTask(
            "cpu_light",
            "ecs",
            "tests/external_mps.py",
            ((name, "1"),),
        ),
    )


@pytest.mark.parametrize(
    "name",
    ["CUDA_VISIBLE_DEVICES", "ECS_GPU_SLOT", "UNDECLARED_RUNTIME_SWITCH"],
)
def test_acceptance_plan_rejects_unsafe_process_environment(name: str) -> None:
    catalog = _minimal_catalog("tests/current.py")
    catalog["acceptance_execution"]["process_environment_overrides"] = {
        "tests/current.py": {name: "unsafe"},
    }

    with pytest.raises(ValueError, match="GPU routing|unsupported"):
        acceptance.acceptance_plan(catalog)


def test_run_one_uses_a_private_task_environment(monkeypatch, tmp_path: Path) -> None:
    task = acceptance.AcceptanceTask(
        "gpu_serial",
        "ecs",
        "tests/pepo.py",
        (("PYTORCH_ALLOC_CONF", "expandable_segments:True"),),
    )
    base = MappingProxyType({
        "CUDA_VISIBLE_DEVICES": "7",
        "ECS_GPU_SLOT": "7",
        "PYTORCH_CUDA_ALLOC_CONF": "legacy-parent-value",
        "PYTHONPATH": "/unbound/injection",
        "PYTHONNOUSERSITE": "0",
        "PARENT_ONLY": "unchanged",
    })
    captured: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs["env"]
        return SimpleNamespace(
            returncode=0,
            timed_out=False,
            group_cleanup_verified=True,
        )

    monkeypatch.setattr(acceptance.proc, "run", fake_run)

    result = acceptance._run_one(
        task,
        index=1,
        conda="/conda",
        timeout=1.0,
        log_dir=tmp_path,
        child_env=base,
    )

    assert result.ok
    assert captured["env"] == {
        "CUDA_VISIBLE_DEVICES": "7",
        "ECS_GPU_SLOT": "7",
        "PYTORCH_ALLOC_CONF": "expandable_segments:True",
        "PYTHONNOUSERSITE": "1",
        "PARENT_ONLY": "unchanged",
    }
    assert dict(base)["PYTORCH_CUDA_ALLOC_CONF"] == "legacy-parent-value"
    assert task.process_environment == ((
        "PYTORCH_ALLOC_CONF",
        "expandable_segments:True",
    ),)


def test_run_one_fails_closed_when_cleanup_evidence_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    task = acceptance.AcceptanceTask("gpu_serial", "ecs", "tests/gpu.py")
    monkeypatch.setattr(
        acceptance.proc,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, timed_out=False),
    )

    result = acceptance._run_one(
        task,
        index=1,
        conda="/conda",
        timeout=1.0,
        log_dir=tmp_path,
        child_env={},
    )

    assert not result.ok
    assert result.group_cleanup_verified is False


@pytest.mark.parametrize(
    ("returncode", "timed_out", "cleanup_verified"),
    [
        (128 + signal.SIGABRT, False, True),
        (128 + signal.SIGSEGV, False, True),
        (-signal.SIGABRT, False, True),
        (-signal.SIGSEGV, False, True),
        (128 + signal.SIGKILL, False, True),
        (-signal.SIGTERM, False, True),
        (2, False, True),
        (0, True, True),
        (0, False, False),
    ],
)
def test_gpu_native_failure_stops_further_admission(
    monkeypatch,
    tmp_path: Path,
    returncode: int,
    timed_out: bool,
    cleanup_verified: bool,
) -> None:
    tasks = tuple(
        acceptance.AcceptanceTask("gpu_serial", "ecs", f"tests/gpu_{index}.py")
        for index in range(2)
    )
    called: list[str] = []

    def fake_run_one(task, **_kwargs):
        called.append(task.test_file)
        return acceptance.TaskResult(
            task=task,
            returncode=returncode,
            timed_out=timed_out,
            group_cleanup_verified=cleanup_verified,
            log_path=tmp_path / "gpu.log",
            elapsed_s=0.01,
        )

    monkeypatch.setattr(acceptance, "_run_one", fake_run_one)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    results = acceptance._run_serial(
        tasks,
        indices={task.test_file: index for index, task in enumerate(tasks)},
        conda="/conda",
        timeout=1.0,
        log_dir=tmp_path,
        child_env={},
        completed_offset=0,
        total=2,
        stop_on_failure=False,
    )

    assert len(results) == 1
    assert called == ["tests/gpu_0.py"]


def test_ordinary_gpu_test_failure_continues_unless_stop_requested(
    monkeypatch,
    tmp_path: Path,
) -> None:
    tasks = tuple(
        acceptance.AcceptanceTask("gpu_serial", "ecs", f"tests/gpu_{index}.py")
        for index in range(2)
    )

    def fake_run_one(task, **_kwargs):
        return acceptance.TaskResult(
            task=task,
            returncode=1,
            timed_out=False,
            group_cleanup_verified=True,
            log_path=tmp_path / "gpu.log",
            elapsed_s=0.01,
        )

    monkeypatch.setattr(acceptance, "_run_one", fake_run_one)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)
    kwargs = dict(
        indices={task.test_file: index for index, task in enumerate(tasks)},
        conda="/conda",
        timeout=1.0,
        log_dir=tmp_path,
        child_env={},
        completed_offset=0,
        total=2,
    )

    assert len(acceptance._run_serial(tasks, stop_on_failure=False, **kwargs)) == 2
    assert len(acceptance._run_serial(tasks, stop_on_failure=True, **kwargs)) == 1


def test_run_plan_stop_on_failure_publishes_first_failure_without_more_admission(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask("cpu_exclusive", "ecs", f"tests/stop_{name}.py")
        for name in ("a", "b")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    calls: list[str] = []

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def fail_first(task, **kwargs):
        calls.append(task.test_file)
        result = _ok(task, kwargs["log_dir"])
        return acceptance.TaskResult(
            task=result.task,
            returncode=1,
            timed_out=False,
            group_cleanup_verified=True,
            log_path=result.log_path,
            elapsed_s=result.elapsed_s,
        )

    monkeypatch.setattr(acceptance, "_run_one", fail_first)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    assert not acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=True)

    assert calls == [plan[0].test_file]
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "FAIL"
    assert summary["cpu_light_jobs"] == 1
    assert [row["test_file"] for row in summary["results"]] == [plan[0].test_file]
    assert not (tmp_path / "service_acceptance_checkpoint.json").exists()


def test_run_plan_fatal_gpu_exit_publishes_terminal_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask("gpu_serial", "ecs", f"tests/fatal_{name}.py")
        for name in ("a", "b")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    calls: list[str] = []

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    class Slot:
        slot = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def child_env(self, base_env):
            return dict(base_env, CUDA_VISIBLE_DEVICES="0", ECS_GPU_SLOT="0")

    def fatal_first(task, **kwargs):
        calls.append(task.test_file)
        result = _ok(task, kwargs["log_dir"])
        return acceptance.TaskResult(
            task=result.task,
            returncode=128 + signal.SIGKILL,
            timed_out=False,
            group_cleanup_verified=True,
            log_path=result.log_path,
            elapsed_s=result.elapsed_s,
        )

    monkeypatch.setattr(acceptance.gpu_pool, "acquire_gpu_slot", Slot)
    monkeypatch.setattr(acceptance, "_run_one", fatal_first)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    assert not acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert calls == [plan[0].test_file]
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "FAIL"
    assert not (tmp_path / "service_acceptance_checkpoint.json").exists()


def test_resume_crosses_from_completed_cpu_prefix_to_one_gpu_lease(
    monkeypatch,
    tmp_path: Path,
) -> None:
    cpu = acceptance.AcceptanceTask("cpu_exclusive", "ecs", "tests/cpu_done.py")
    gpu = acceptance.AcceptanceTask("gpu_serial", "ecs", "tests/gpu_pending.py")
    plan = (cpu, gpu)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    task_calls: list[str] = []
    lease_calls = 0

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    def run_one(task, **kwargs):
        task_calls.append(task.test_file)
        return _ok(task, kwargs["log_dir"])

    class Slot:
        slot = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def child_env(self, base_env):
            return dict(base_env, CUDA_VISIBLE_DEVICES="0", ECS_GPU_SLOT="0")

    def acquire():
        nonlocal lease_calls
        lease_calls += 1
        if lease_calls == 1:
            raise RuntimeError("simulated pre-lease interruption")
        return Slot()

    monkeypatch.setattr(acceptance, "_run_one", run_one)
    monkeypatch.setattr(acceptance.gpu_pool, "acquire_gpu_slot", acquire)

    with pytest.raises(RuntimeError, match="pre-lease interruption"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    checkpoint = json.loads(
        (tmp_path / "service_acceptance_checkpoint.json").read_text(encoding="utf-8")
    )
    assert [row["test_file"] for row in checkpoint["completed_prefix"]] == [
        cpu.test_file
    ]
    assert task_calls == [cpu.test_file]

    assert acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert lease_calls == 2
    assert task_calls == [cpu.test_file, gpu.test_file]
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))[
        "status"
    ] == "PASS"
    assert not (tmp_path / "service_acceptance_checkpoint.json").exists()


@pytest.mark.parametrize(
    "malform",
    [
        pytest.param(
            lambda result, _run_dir: acceptance.TaskResult(
                task=result.task,
                returncode=0.0,
                timed_out=False,
                group_cleanup_verified=True,
                log_path=result.log_path,
                elapsed_s=result.elapsed_s,
            ),
            id="float-returncode",
        ),
        pytest.param(
            lambda result, _run_dir: acceptance.TaskResult(
                task=result.task,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=1,
                log_path=result.log_path,
                elapsed_s=result.elapsed_s,
            ),
            id="integer-cleanup-flag",
        ),
        pytest.param(
            lambda result, run_dir: acceptance.TaskResult(
                task=result.task,
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
                log_path=run_dir / "missing.log",
                elapsed_s=result.elapsed_s,
            ),
            id="missing-log",
        ),
        pytest.param(
            lambda result, _run_dir: acceptance.TaskResult(
                task=acceptance.AcceptanceTask(
                    result.task.lane,
                    "wrong-environment",
                    result.task.test_file,
                ),
                returncode=0,
                timed_out=False,
                group_cleanup_verified=True,
                log_path=result.log_path,
                elapsed_s=result.elapsed_s,
            ),
            id="wrong-task-identity",
        ),
    ],
)
def test_unauthenticated_task_result_can_never_publish_pass(
    monkeypatch,
    tmp_path: Path,
    malform,
) -> None:
    task = acceptance.AcceptanceTask(
        "cpu_exclusive",
        "ecs",
        "tests/strict_result.py",
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)
    monkeypatch.setattr(
        acceptance,
        "_run_one",
        lambda current, **kwargs: malform(_ok(current, kwargs["log_dir"]), run_dir),
    )
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    assert not acceptance.run_plan((task,), log_root=tmp_path, stop_on_failure=False)

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "FAIL"


def test_interruption_resumes_only_after_authenticated_terminal_prefix(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask(
            "cpu_exclusive",
            "ecs",
            f"tests/serial_{name}.py",
        )
        for name in ("a", "b", "c")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    checkpoint = tmp_path / "service_acceptance_checkpoint.json"
    calls: list[str] = []
    phase = 1

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def fake_run_one(task, **kwargs):
        nonlocal phase
        calls.append(task.test_file)
        if phase == 1 and task is plan[2]:
            raise RuntimeError("simulated supervisor interruption")
        result = _ok(task, kwargs["log_dir"])
        if task is plan[1]:
            return acceptance.TaskResult(
                task=result.task,
                returncode=1,
                timed_out=False,
                group_cleanup_verified=True,
                log_path=result.log_path,
                elapsed_s=result.elapsed_s,
            )
        return result

    monkeypatch.setattr(acceptance, "_run_one", fake_run_one)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="supervisor interruption"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [row["test_file"] for row in checkpoint_doc["completed_prefix"]] == [
        plan[0].test_file,
        plan[1].test_file,
    ]
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))[
        "status"
    ] == "INTERRUPTED"

    phase = 2
    calls.clear()
    assert not acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert calls == [plan[2].test_file]
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "FAIL"
    assert [row["test_file"] for row in summary["results"]] == sorted(
        task.test_file for task in plan
    )
    assert not checkpoint.exists()


def test_unauthenticated_result_closes_prefix_and_resume_restarts_at_gap(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask(
            "cpu_exclusive",
            "ecs",
            f"tests/gap_{name}.py",
        )
        for name in ("a", "b", "c", "d")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    checkpoint = tmp_path / "service_acceptance_checkpoint.json"
    calls: list[str] = []
    phase = 1

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def fake_run_one(task, **kwargs):
        calls.append(task.test_file)
        if phase == 1 and task is plan[3]:
            raise RuntimeError("simulated supervisor interruption")
        result = _ok(task, kwargs["log_dir"])
        if phase == 1 and task is plan[1]:
            return acceptance.TaskResult(
                task=result.task,
                returncode=0,
                timed_out=True,
                group_cleanup_verified=True,
                log_path=result.log_path,
                elapsed_s=result.elapsed_s,
            )
        return result

    monkeypatch.setattr(acceptance, "_run_one", fake_run_one)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="supervisor interruption"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [row["test_file"] for row in checkpoint_doc["completed_prefix"]] == [
        plan[0].test_file
    ]

    phase = 2
    calls.clear()
    assert acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert calls == [task.test_file for task in plan[1:]]
    assert not checkpoint.exists()


def test_parallel_out_of_order_completion_never_jumps_a_prefix_gap(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask("cpu_light", "ecs", f"tests/parallel_{name}.py")
        for name in ("a", "b", "c")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    checkpoint = tmp_path / "service_acceptance_checkpoint.json"
    admitted: list[str] = []
    phase = 1

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def fake_parallel(tasks, **kwargs):
        admitted.extend(task.test_file for task in tasks)
        by_file = {task.test_file: task for task in tasks}
        if phase == 1:
            completion_order = (plan[2], plan[0])
        else:
            completion_order = (by_file[plan[2].test_file], by_file[plan[1].test_file])
        results = [_ok(task, kwargs["log_dir"]) for task in completion_order]
        for result in results:
            kwargs["on_result"](result)
        if phase == 1:
            raise RuntimeError("simulated supervisor interruption")
        return results

    monkeypatch.setattr(acceptance, "_run_cpu_light_parallel", fake_parallel)

    with pytest.raises(RuntimeError, match="supervisor interruption"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    checkpoint_doc = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [row["test_file"] for row in checkpoint_doc["completed_prefix"]] == [
        plan[0].test_file
    ]

    phase = 2
    admitted.clear()
    assert acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert admitted == [plan[1].test_file, plan[2].test_file]
    assert not checkpoint.exists()


def test_resume_rejects_tampered_log_before_new_task_admission(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask("cpu_exclusive", "ecs", f"tests/tamper_{name}.py")
        for name in ("a", "b")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def interrupt_after_first(task, **kwargs):
        if task is plan[1]:
            raise RuntimeError("simulated supervisor interruption")
        return _ok(task, kwargs["log_dir"])

    monkeypatch.setattr(acceptance, "_run_one", interrupt_after_first)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)
    with pytest.raises(RuntimeError, match="supervisor interruption"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    checkpoint = json.loads(
        (tmp_path / "service_acceptance_checkpoint.json").read_text(encoding="utf-8")
    )
    authenticated_log = run_dir / checkpoint["completed_prefix"][0]["log"]
    authenticated_log.write_text("tampered after checkpoint\n", encoding="utf-8")
    monkeypatch.setattr(
        acceptance,
        "_run_one",
        lambda *_args, **_kwargs: pytest.fail("resume admitted a task before validation"),
    )

    with pytest.raises(ValueError, match="log digest mismatch"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)


@pytest.mark.parametrize(
    ("drift", "message"),
    [
        ("snapshot", "input snapshot mismatch"),
        ("plan", "semantic plan mismatch"),
        ("policy", "execution policy mismatch"),
        ("runtime", "execution policy mismatch"),
    ],
)
def test_resume_rejects_snapshot_plan_or_policy_drift_before_admission(
    monkeypatch,
    tmp_path: Path,
    drift: str,
    message: str,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask("cpu_exclusive", "ecs", f"tests/drift_{name}.py")
        for name in ("a", "b")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    config = {
        "timeout_per_file_s": 1,
        "cpu_light_jobs": 4,
        "host_memory_reserve_gib": 0,
        "cpu_light_memory_gib_per_job": 1,
    }
    snapshot = "a" * 64
    runtime_identity = {"revision": "a"}

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(acceptance, "_config", lambda: dict(config))
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: snapshot)
    monkeypatch.setattr(
        acceptance,
        "_runtime_environment_identity",
        lambda _conda, _plan: dict(runtime_identity),
    )

    def interrupt_after_first(task, **kwargs):
        if task is plan[1]:
            raise RuntimeError("simulated supervisor interruption")
        return _ok(task, kwargs["log_dir"])

    monkeypatch.setattr(acceptance, "_run_one", interrupt_after_first)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)
    with pytest.raises(RuntimeError, match="supervisor interruption"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    checkpoint_path = tmp_path / "service_acceptance_checkpoint.json"
    checkpoint_before = checkpoint_path.read_bytes()
    resume_plan = plan
    if drift == "snapshot":
        snapshot = "b" * 64
    elif drift == "plan":
        resume_plan = (
            acceptance.AcceptanceTask(
                plan[0].lane,
                "different-environment",
                plan[0].test_file,
            ),
            plan[1],
        )
    elif drift == "policy":
        config["timeout_per_file_s"] = 2
    else:
        runtime_identity["revision"] = "b"
    monkeypatch.setattr(
        acceptance,
        "_run_one",
        lambda *_args, **_kwargs: pytest.fail("drifted resume admitted a task"),
    )

    with pytest.raises(RuntimeError, match=message):
        acceptance.run_plan(resume_plan, log_root=tmp_path, stop_on_failure=False)

    assert checkpoint_path.read_bytes() == checkpoint_before


def test_runtime_environment_drift_during_lane_retains_interrupted_checkpoint(
    monkeypatch,
    tmp_path: Path,
) -> None:
    task = acceptance.AcceptanceTask(
        "cpu_exclusive",
        "ecs",
        "tests/runtime_drift.py",
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    identity_calls = 0

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def runtime_identity(_conda, _plan):
        nonlocal identity_calls
        identity_calls += 1
        return {"revision": "a" if identity_calls <= 2 else "b"}

    monkeypatch.setattr(acceptance, "_runtime_environment_identity", runtime_identity)
    monkeypatch.setattr(
        acceptance,
        "_run_one",
        lambda current, **kwargs: _ok(current, kwargs["log_dir"]),
    )
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="runtime environment drifted after"):
        acceptance.run_plan((task,), log_root=tmp_path, stop_on_failure=False)

    assert identity_calls == 4
    assert (tmp_path / "service_acceptance_checkpoint.json").is_file()
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))[
        "status"
    ] == "INTERRUPTED"


def test_summary_publish_failure_retains_checkpoint_until_retry_succeeds(
    monkeypatch,
    tmp_path: Path,
) -> None:
    task = acceptance.AcceptanceTask(
        "cpu_exclusive",
        "ecs",
        "tests/publish.py",
    )
    plan = (task,)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    checkpoint = tmp_path / "service_acceptance_checkpoint.json"
    calls: list[str] = []

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def fake_run_one(current, **kwargs):
        calls.append(current.test_file)
        return _ok(current, kwargs["log_dir"])

    monkeypatch.setattr(acceptance, "_run_one", fake_run_one)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)
    real_write_summary = acceptance._write_summary
    publication_attempts = 0

    def flaky_write_summary(*args, **kwargs):
        nonlocal publication_attempts
        assert checkpoint.is_file()
        publication_attempts += 1
        if publication_attempts == 1:
            raise OSError("simulated summary publication failure")
        return real_write_summary(*args, **kwargs)

    monkeypatch.setattr(acceptance, "_write_summary", flaky_write_summary)

    with pytest.raises(OSError, match="publication failure"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert calls == [task.test_file]
    assert checkpoint.is_file()
    assert not (run_dir / "summary.json").exists()

    calls.clear()
    assert acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert calls == []
    assert publication_attempts == 2
    assert (run_dir / "summary.json").is_file()
    assert not checkpoint.exists()
    assert not (tmp_path / ".service_acceptance_checkpoint.json.tmp").exists()
    assert not (run_dir / ".summary.json.tmp").exists()


def test_terminal_summary_reconciles_lingering_checkpoint_after_retirement_crash(
    monkeypatch,
    tmp_path: Path,
) -> None:
    task = acceptance.AcceptanceTask(
        "cpu_exclusive",
        "ecs",
        "tests/terminal_reconcile.py",
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    checkpoint = tmp_path / "service_acceptance_checkpoint.json"
    calls: list[str] = []

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def fake_run_one(current, **kwargs):
        calls.append(current.test_file)
        return _ok(current, kwargs["log_dir"])

    monkeypatch.setattr(acceptance, "_run_one", fake_run_one)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)
    real_unlink = Path.unlink
    injected = False

    def crash_on_checkpoint_retirement(path, *args, **kwargs):
        nonlocal injected
        if path == checkpoint and (run_dir / "summary.json").is_file() and not injected:
            injected = True
            raise OSError("simulated crash after summary publication")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", crash_on_checkpoint_retirement)
    with pytest.raises(OSError, match="after summary publication"):
        acceptance.run_plan((task,), log_root=tmp_path, stop_on_failure=False)

    assert calls == [task.test_file]
    assert checkpoint.is_file()
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))[
        "status"
    ] == "PASS"

    calls.clear()
    monkeypatch.setattr(Path, "unlink", real_unlink)
    assert acceptance.run_plan((task,), log_root=tmp_path, stop_on_failure=False)

    assert calls == []
    assert not checkpoint.exists()


def test_partial_fatal_gpu_summary_reconciles_lingering_checkpoint(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask("gpu_serial", "ecs", f"tests/fatal_{name}.py")
        for name in ("a", "b")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    checkpoint = tmp_path / "service_acceptance_checkpoint.json"
    calls: list[str] = []
    lease_calls = 0

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    class Slot:
        slot = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def child_env(self, base_env):
            return dict(base_env, CUDA_VISIBLE_DEVICES="0", ECS_GPU_SLOT="0")

    def acquire():
        nonlocal lease_calls
        lease_calls += 1
        return Slot()

    def fatal_first(current, **kwargs):
        calls.append(current.test_file)
        result = _ok(current, kwargs["log_dir"])
        return acceptance.TaskResult(
            task=current,
            returncode=128 + signal.SIGKILL,
            timed_out=False,
            group_cleanup_verified=True,
            log_path=result.log_path,
            elapsed_s=result.elapsed_s,
        )

    monkeypatch.setattr(acceptance.gpu_pool, "acquire_gpu_slot", acquire)
    monkeypatch.setattr(acceptance, "_run_one", fatal_first)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)
    real_unlink = Path.unlink
    injected = False

    def crash_on_checkpoint_retirement(path, *args, **kwargs):
        nonlocal injected
        if path == checkpoint and (run_dir / "summary.json").is_file() and not injected:
            injected = True
            raise OSError("simulated fatal-summary retirement crash")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", crash_on_checkpoint_retirement)
    with pytest.raises(OSError, match="fatal-summary retirement crash"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert calls == [plan[0].test_file]
    assert lease_calls == 1
    assert checkpoint.is_file()
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))[
        "status"
    ] == "FAIL"

    calls.clear()
    monkeypatch.setattr(Path, "unlink", real_unlink)
    assert not acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    assert calls == []
    assert lease_calls == 1
    assert not checkpoint.exists()


def test_terminal_publication_reauthenticates_checkpointed_logs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    task = acceptance.AcceptanceTask(
        "cpu_exclusive",
        "ecs",
        "tests/reauthenticate.py",
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    checkpoint = tmp_path / "service_acceptance_checkpoint.json"
    snapshot_calls = 0

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)

    def snapshot_and_tamper_after_lane() -> str:
        nonlocal snapshot_calls
        snapshot_calls += 1
        if snapshot_calls == 3:
            (run_dir / acceptance._task_log_name(task)).write_text(
                "tampered before publication\n",
                encoding="utf-8",
            )
        return "a" * 64

    monkeypatch.setattr(
        acceptance,
        "_acceptance_input_snapshot",
        snapshot_and_tamper_after_lane,
    )
    monkeypatch.setattr(
        acceptance,
        "_run_one",
        lambda current, **kwargs: _ok(current, kwargs["log_dir"]),
    )
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)

    with pytest.raises(ValueError, match="log digest mismatch"):
        acceptance.run_plan((task,), log_root=tmp_path, stop_on_failure=False)

    assert checkpoint.is_file()
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))[
        "status"
    ] == "INTERRUPTED"


@pytest.mark.parametrize(
    "corrupt",
    [
        pytest.param(
            lambda doc: doc.update(schema="unsupported"),
            id="schema",
        ),
        pytest.param(
            lambda doc: doc.update(unexpected="field"),
            id="top-level-fields",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(sequence_index=2),
            id="noncontiguous-index",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(test_file="tests/other.py"),
            id="task-identity",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(returncode=True),
            id="bool-returncode",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(
                returncode=128 + signal.SIGSEGV
            ),
            id="native-fatal-returncode",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(timed_out=True),
            id="timeout",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(
                group_cleanup_verified=False
            ),
            id="cleanup-missing",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(error="worker error"),
            id="execution-error",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(elapsed_s=float("nan")),
            id="nonfinite-elapsed",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(log="../escape.log"),
            id="log-path-escape",
        ),
        pytest.param(
            lambda doc: doc["completed_prefix"][0].update(log_sha256="0" * 63),
            id="log-digest-shape",
        ),
    ],
)
def test_resume_rejects_corrupt_checkpoint_before_admission(
    monkeypatch,
    tmp_path: Path,
    corrupt,
) -> None:
    plan = tuple(
        acceptance.AcceptanceTask("cpu_exclusive", "ecs", f"tests/corrupt_{name}.py")
        for name in ("a", "b")
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    monkeypatch.setattr(acceptance.shutil, "which", lambda _name: "/conda")
    monkeypatch.setattr(
        acceptance,
        "_config",
        lambda: {
            "timeout_per_file_s": 1,
            "cpu_light_jobs": 4,
            "host_memory_reserve_gib": 0,
            "cpu_light_memory_gib_per_job": 1,
        },
    )
    monkeypatch.setattr(acceptance, "_available_memory_bytes", lambda: 8 * 1024 ** 3)
    monkeypatch.setattr(acceptance, "_new_run_log_dir", lambda _root: run_dir)
    monkeypatch.setattr(acceptance, "_acceptance_input_snapshot", lambda: "a" * 64)

    def interrupt_after_first(task, **kwargs):
        if task is plan[1]:
            raise RuntimeError("simulated supervisor interruption")
        return _ok(task, kwargs["log_dir"])

    monkeypatch.setattr(acceptance, "_run_one", interrupt_after_first)
    monkeypatch.setattr(acceptance, "_report_result", lambda *_args, **_kwargs: None)
    with pytest.raises(RuntimeError, match="supervisor interruption"):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

    checkpoint_path = tmp_path / "service_acceptance_checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    corrupt(checkpoint)
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    monkeypatch.setattr(
        acceptance,
        "_run_one",
        lambda *_args, **_kwargs: pytest.fail("corrupt resume admitted a task"),
    )

    with pytest.raises(ValueError):
        acceptance.run_plan(plan, log_root=tmp_path, stop_on_failure=False)

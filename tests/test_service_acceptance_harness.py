"""Execution-topology regressions for the catalog acceptance supervisor."""

from __future__ import annotations

import ast
from pathlib import Path

from harness import service_acceptance as acceptance


def _ok(task: acceptance.AcceptanceTask, log_dir: Path) -> acceptance.TaskResult:
    return acceptance.TaskResult(
        task=task,
        returncode=0,
        timed_out=False,
        log_path=log_dir / f"{Path(task.test_file).stem}.log",
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


def test_each_invocation_allocates_a_unique_log_directory(tmp_path: Path) -> None:
    first = acceptance._new_run_log_dir(tmp_path)
    second = acceptance._new_run_log_dir(tmp_path)

    assert first != second
    assert first.is_dir()
    assert second.is_dir()


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
        ("cpu_light", "parent-visible"),
        ("cpu_exclusive", "parent-visible"),
        ("acquire", None),
        ("gpu_serial", "7"),
        ("release", None),
    ]
    assert acceptance.os.environ["CUDA_VISIBLE_DEVICES"] == "parent-visible"


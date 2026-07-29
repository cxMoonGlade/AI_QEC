from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import signal
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_systemd_snapshot.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("gcapeps_fm_snapshot", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _cgroup(tmp_path):
    root = tmp_path / "cgroup"
    root.mkdir(parents=True)
    for name, value in {
        "memory.current": 100,
        "memory.peak": 200,
        "memory.swap.current": 0,
        "pids.current": 1,
        "pids.peak": 2,
    }.items():
        (root / name).write_text(f"{value}\n", encoding="ascii")
    (root / "memory.events").write_text(
        "low 0\nhigh 0\nmax 1\noom 0\noom_kill 0\noom_group_kill 0\n",
        encoding="ascii",
    )
    (root / "pids.events").write_text("max 0\n", encoding="ascii")
    (root / "cpu.stat").write_text(
        "usage_usec 123\nuser_usec 100\nsystem_usec 23\n",
        encoding="ascii",
    )
    return root


def test_build_snapshot_reads_live_cgroup_and_hashes_projection(tmp_path):
    module = _load_module()
    payload = module.build_snapshot(
        launch_id="abc-123",
        service_result="resources",
        exit_code="exited",
        exit_status="1",
        invocation_id="f" * 32,
        cgroup=_cgroup(tmp_path),
    )
    assert payload["schema"] == module.SNAPSHOT_SCHEMA
    assert payload["live_cgroup"]["memory_peak"] == 200
    assert payload["live_cgroup"]["memory_events"]["max"] == 1
    assert payload["live_cgroup"]["cpu_stat"]["usage_usec"] == 123
    assert payload["result_projection_sha256"] == module._projection(payload)


def test_publish_is_noreplace_fsync_shape_and_stops_after_bytes(tmp_path):
    module = _load_module()
    launch_id = "launch"
    runtime = tmp_path / f"gcapeps-fm-{launch_id}"
    runtime.mkdir()
    payload = module.build_snapshot(
        launch_id=launch_id,
        service_result="timeout",
        exit_code="killed",
        exit_status="15",
        invocation_id="a" * 32,
        cgroup=_cgroup(tmp_path),
    )
    calls = []
    module.publish_snapshot_and_stop(
        payload,
        runtime_directory=runtime,
        stop_process=lambda pid, sig: calls.append((pid, sig)),
    )
    snapshot = runtime / module.SNAPSHOT_FILENAME
    assert json.loads(snapshot.read_bytes()) == payload
    assert snapshot.stat().st_mode & 0o777 == 0o644
    assert calls and calls[0][1] == signal.SIGSTOP
    with pytest.raises(FileExistsError):
        module.publish_snapshot_and_stop(
            payload,
            runtime_directory=runtime,
            stop_process=lambda pid, sig: None,
        )


def test_success_exec_stop_post_is_a_noop(monkeypatch):
    module = _load_module()
    monkeypatch.setenv("SERVICE_RESULT", "success")
    assert module._main(["--launch-id", "success"]) == 0


def test_counter_and_launch_id_parsers_fail_closed(tmp_path):
    module = _load_module()
    cgroup = _cgroup(tmp_path)
    (cgroup / "memory.current").write_text("max\n", encoding="ascii")
    with pytest.raises(ValueError, match="unsigned"):
        module.read_live_cgroup(cgroup)
    with pytest.raises(ValueError, match="launch_id"):
        module.build_snapshot(
            launch_id="../escape",
            service_result="failed",
            exit_code="exited",
            exit_status="1",
            invocation_id="id",
            cgroup=_cgroup(tmp_path / "second"),
        )

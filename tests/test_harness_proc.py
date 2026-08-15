from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import pytest

from harness import proc


def _force_reap(child: subprocess.Popen[bytes]) -> None:
    """Best-effort cleanup for a failing regression assertion."""

    if child.returncode is None:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            pass


def test_run_owns_child_before_registration_can_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Once Popen returns, even a registration failure must not leak its child."""

    real_popen = proc.subprocess.Popen
    children: list[subprocess.Popen[bytes]] = []

    def capturing_popen(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    def fail_registration(_pgid: int) -> None:
        raise RuntimeError("injected registration failure")

    monkeypatch.setattr(proc.subprocess, "Popen", capturing_popen)
    monkeypatch.setattr(proc, "_register", fail_registration)

    try:
        with pytest.raises(RuntimeError, match="injected registration failure"):
            proc.run(["bash", "-c", "sleep 60"])

        assert len(children) == 1
        child = children[0]
        assert child.returncode is not None
        assert not proc.group_alive(child.pid)
    finally:
        for child in children:
            _force_reap(child)


def test_run_reaps_leader_when_wait_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An arbitrary wait failure still terminates the group and reaps its leader."""

    real_popen = proc.subprocess.Popen
    children: list[subprocess.Popen[bytes]] = []

    def popen_with_one_failing_wait(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        real_wait = child.wait
        wait_calls = 0

        def failing_wait(*wait_args, **wait_kwargs):
            nonlocal wait_calls
            wait_calls += 1
            if wait_calls == 1:
                raise RuntimeError("injected wait failure")
            return real_wait(*wait_args, **wait_kwargs)

        child.wait = failing_wait  # type: ignore[method-assign]
        children.append(child)
        return child

    monkeypatch.setattr(proc.subprocess, "Popen", popen_with_one_failing_wait)

    try:
        with pytest.raises(RuntimeError, match="injected wait failure"):
            proc.run(["bash", "-c", "sleep 60"])

        assert len(children) == 1
        child = children[0]
        assert child.returncode is not None
        assert not proc.group_alive(child.pid)
    finally:
        for child in children:
            _force_reap(child)


def test_run_reports_verified_group_cleanup() -> None:
    ran = proc.run([sys.executable, "-c", "pass"])

    assert ran.group_cleanup_verified is True
    assert ran.ok
    assert ran.pgid not in proc._LIVE_GROUPS


def test_run_cancellation_event_terminates_and_reaps_group() -> None:
    cancellation = threading.Event()
    trigger = threading.Timer(0.2, cancellation.set)
    started = time.monotonic()
    trigger.start()
    try:
        ran = proc.run(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            cancellation_event=cancellation,
        )
    finally:
        trigger.cancel()

    assert time.monotonic() - started < 5.0
    assert ran.timed_out is False
    assert ran.group_cleanup_verified is True
    assert ran.returncode != 0
    assert ran.pgid not in proc._LIVE_GROUPS


def test_four_concurrent_groups_share_cancellation_and_leave_no_orphans() -> None:
    cancellation = threading.Event()
    start = threading.Barrier(4)
    result_lock = threading.Lock()
    results: list[proc.Ran] = []
    errors: list[BaseException] = []

    def worker(index: int) -> None:
        try:
            start.wait(timeout=2.0)
            code = (
                "import sys; sys.exit(1)"
                if index == 4
                else "import time; time.sleep(60)"
            )
            ran = proc.run(
                [sys.executable, "-c", code],
                cancellation_event=cancellation,
            )
            if index == 4:
                cancellation.set()
            with result_lock:
                results.append(ran)
        except BaseException as exc:
            cancellation.set()
            with result_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(index,), daemon=True)
        for index in range(1, 5)
    ]
    started = time.monotonic()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5.0)

    assert time.monotonic() - started < 5.0
    assert all(not thread.is_alive() for thread in threads)
    assert errors == []
    assert len(results) == 4
    assert all(ran.group_cleanup_verified for ran in results)
    assert all(not proc.group_alive(ran.pgid) for ran in results)
    assert all(ran.pgid not in proc._LIVE_GROUPS for ran in results)


def test_terminate_group_keeps_unverified_survivor_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pgid = 987654321
    clock = iter(range(0, 100, 3))
    proc._register(pgid)
    monkeypatch.setattr(proc, "group_alive", lambda _pgid: True)
    monkeypatch.setattr(proc.os, "killpg", lambda *_args: None)
    monkeypatch.setattr(proc.time, "monotonic", lambda: float(next(clock)))
    monkeypatch.setattr(proc.time, "sleep", lambda _seconds: None)
    try:
        assert proc.terminate_group(pgid, grace=0.0) is False
        assert pgid in proc._LIVE_GROUPS
    finally:
        proc._unregister(pgid)


def test_signal_handler_only_records_inside_spawn_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The asynchronous callback neither takes the registry lock nor cleans groups."""

    handler = getattr(proc, "_signal_handler", None)
    assert handler is not None, "signal handling must have a directly testable callback"

    class LockMustNotBeTouched:
        def __enter__(self):
            raise AssertionError("signal callback entered _LOCK")

        def __exit__(self, *_args):
            return False

    def cleanup_must_not_run(*_args, **_kwargs):
        raise AssertionError("signal callback ran process cleanup")

    old_pending = proc._PENDING_SIGNAL
    old_depth = proc._MAIN_CRITICAL_DEPTH
    monkeypatch.setattr(proc, "_LOCK", LockMustNotBeTouched())
    monkeypatch.setattr(proc, "_cleanup_all", cleanup_must_not_run)
    try:
        proc._PENDING_SIGNAL = None
        proc._MAIN_CRITICAL_DEPTH = 1
        handler(signal.SIGTERM, None)
        assert proc._PENDING_SIGNAL == signal.SIGTERM
    finally:
        proc._PENDING_SIGNAL = old_pending
        proc._MAIN_CRITICAL_DEPTH = old_depth


def test_signal_in_spawn_register_window_is_deferred_until_owned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A signal after OS spawn cannot interrupt before registration and owner-finally."""

    signal_exit = getattr(proc, "_SignalExit", None)
    handler = getattr(proc, "_signal_handler", None)
    assert signal_exit is not None and handler is not None

    real_popen = proc.subprocess.Popen
    children: list[subprocess.Popen[bytes]] = []
    old_pending = proc._PENDING_SIGNAL
    old_depth = proc._MAIN_CRITICAL_DEPTH

    def popen_then_signal(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        # This models signal delivery after Popen created the OS child but before
        # ``run`` can execute its next bytecode and register the process group.
        handler(signal.SIGTERM, None)
        return child

    monkeypatch.setattr(proc.subprocess, "Popen", popen_then_signal)
    try:
        proc._PENDING_SIGNAL = None
        proc._MAIN_CRITICAL_DEPTH = 0
        with pytest.raises(signal_exit) as raised:
            proc.run(["bash", "-c", "sleep 60"])

        assert raised.value.signum == signal.SIGTERM
        assert len(children) == 1
        child = children[0]
        assert child.returncode is not None
        assert not proc.group_alive(child.pid)
    finally:
        proc._PENDING_SIGNAL = old_pending
        proc._MAIN_CRITICAL_DEPTH = old_depth
        for child in children:
            _force_reap(child)


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_real_signal_keeps_conventional_exit_and_leaves_no_child(
    tmp_path: Path,
    signum: signal.Signals,
) -> None:
    ready = tmp_path / f"child-{signum.value}.pid"
    repo = Path(__file__).resolve().parents[1]
    child_code = (
        "from pathlib import Path; import os, time; "
        f"Path({str(ready)!r}).write_text(str(os.getpid())); time.sleep(60)"
    )
    harness_code = (
        "import sys; "
        f"sys.path.insert(0, {str(repo / 'tests')!r}); "
        "from harness import proc; "
        f"proc.run([{sys.executable!r}, '-c', {child_code!r}])"
    )
    harness = subprocess.Popen([sys.executable, "-c", harness_code], cwd=repo)
    child_pid: int | None = None
    try:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if ready.is_file():
                child_pid = int(ready.read_text(encoding="utf-8"))
                break
            if harness.poll() is not None:
                pytest.fail(f"harness exited before child was ready: {harness.returncode}")
            time.sleep(0.02)
        assert child_pid is not None

        harness.send_signal(signum)
        assert harness.wait(timeout=8.0) == -signum.value

        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        if harness.poll() is None:
            harness.kill()
            harness.wait(timeout=3.0)
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

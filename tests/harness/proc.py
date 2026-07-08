"""Process-group-aware subprocess launcher -- THE fix for the orphan-process problem.

Root cause of the orphans (2026-07-07): mutmut spawned a pool of worker processes; when the bash
wrapper was killed, the workers were NOT in a process group tied to a single kill, so they
orphaned and kept running. Compounded by `pkill -f` matching (and killing) the killer's own shell.

Fix, done properly in Python:
  * every child is started in its OWN session / process group (`start_new_session=True`), so the
    child AND all its descendants (mutmut's workers) share one process-group id (pgid);
  * the whole group is killed ATOMICALLY with `os.killpg(pgid, ...)`, SIGTERM -> grace -> SIGKILL;
  * a launched group is REGISTERED and cleaned up on harness exit / SIGINT / SIGTERM, so even if
    the harness itself is interrupted it does not leave orphans;
  * commands are LISTS (no shell) -> no quoting/pre-expansion traps.

This module is the substrate the gate/mutation/gpu_pool runners build on.
"""
from __future__ import annotations

import atexit
import os
import signal
import subprocess
import sys
import threading
import time
from typing import Optional, Sequence

# pgids of groups we launched that may still be alive -- cleaned up on exit so we never orphan.
_LIVE_GROUPS: "set[int]" = set()
_LOCK = threading.Lock()


def _register(pgid: int) -> None:
    with _LOCK:
        _LIVE_GROUPS.add(pgid)


def _unregister(pgid: int) -> None:
    with _LOCK:
        _LIVE_GROUPS.discard(pgid)


def group_alive(pgid: int) -> bool:
    """True if ANY process in the group is still alive (signal 0 probes without killing)."""
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but not ours to signal (shouldn't happen for our own children)


def terminate_group(pgid: int, grace: float = 3.0) -> None:
    """Kill the WHOLE process group: SIGTERM, wait up to ``grace``, then an UNCONDITIONAL SIGKILL
    belt (a group member can outlive the SIGTERM of its parent while being reparented; relying on
    'the group looked dead' skips the SIGKILL and leaves that stray). SIGKILL is uncatchable, so
    after it + a short reap wait the group is guaranteed gone. Idempotent."""
    if not group_alive(pgid):
        _unregister(pgid)
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        _unregister(pgid)
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and group_alive(pgid):
        time.sleep(0.05)
    # UNCONDITIONAL SIGKILL belt (even if the group looked dead a moment ago) -> no stray survives.
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    reap = time.monotonic() + 2.0
    while time.monotonic() < reap and group_alive(pgid):
        time.sleep(0.05)
    _unregister(pgid)


class Ran:
    """Result of a run: returncode, timed_out flag, pgid (for post-hoc kill if detached)."""
    def __init__(self, returncode: int, timed_out: bool, pgid: int):
        self.returncode = returncode
        self.timed_out = timed_out
        self.pgid = pgid

    @property
    def ok(self) -> bool:
        return (not self.timed_out) and self.returncode == 0


def run(cmd: Sequence[str], *, cwd: Optional[str] = None, env: Optional[dict] = None,
        timeout: Optional[float] = None, log_path: Optional[str] = None,
        append: bool = False) -> Ran:
    """Run ``cmd`` (a LIST -- no shell, no quoting traps) in its own process group. Combined
    stdout+stderr go to ``log_path`` (or are inherited if None). On ``timeout`` the WHOLE group is
    killed (no runaway, no orphans). The group is ALWAYS torn down on return, so a child that
    spawned a worker pool cannot leave strays."""
    if isinstance(cmd, str):
        raise TypeError("cmd must be a list of args (no shell) -- pass ['a','b'], not 'a b'")
    out = open(log_path, "ab" if append else "wb") if log_path else None
    try:
        proc = subprocess.Popen(list(cmd), cwd=cwd, env=env, start_new_session=True,
                                stdout=out, stderr=subprocess.STDOUT if out else None)
    except Exception:
        if out:
            out.close()
        raise
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        pgid = proc.pid
    _register(pgid)
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        terminate_group(pgid)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    except KeyboardInterrupt:
        terminate_group(pgid)
        raise
    finally:
        # belt: reap any group member that outlived the leader (mutmut worker strays) -> no orphan.
        terminate_group(pgid, grace=2.0)
        if out:
            out.close()
    rc = proc.returncode if proc.returncode is not None else -signal.SIGKILL
    return Ran(rc, timed_out, pgid)


def _cleanup_all(*_a) -> None:
    with _LOCK:
        groups = list(_LIVE_GROUPS)
    for pgid in groups:
        terminate_group(pgid, grace=1.0)


atexit.register(_cleanup_all)


def _install_signal_cleanup() -> None:
    """On SIGINT/SIGTERM to the HARNESS itself, tear down all launched groups before exiting --
    so interrupting the harness never orphans its children."""
    def _handler(signum, _frame):
        _cleanup_all()
        # restore default and re-raise so the exit status is conventional.
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)
    for _sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(_sig, _handler)
        except (ValueError, OSError):
            pass  # not in main thread / unsupported -> atexit still covers normal exits


_install_signal_cleanup()

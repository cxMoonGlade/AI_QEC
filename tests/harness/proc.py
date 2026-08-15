"""Process-group-aware subprocess launcher -- the orphan-process safety seam.

Root cause of the orphans (2026-07-07): mutmut spawned a pool of worker processes; when the bash
wrapper was killed, the workers were NOT in a process group tied to a single kill, so they
orphaned and kept running. Compounded by `pkill -f` matching (and killing) the killer's own shell.

Fix, done properly in Python:
  * every child is started in its OWN session / process group (`start_new_session=True`), so the
    child AND all its descendants (mutmut's workers) share one process-group id (pgid);
  * the whole group is killed ATOMICALLY with `os.killpg(pgid, ...)`, SIGTERM -> grace -> SIGKILL;
  * once ``Popen`` succeeds, the caller owns the child immediately: registration, waiting, log
    handling, and every exceptional exit are enclosed by one owner ``finally``;
  * SIGINT/SIGTERM callbacks only record an interrupt.  Cleanup happens during ordinary stack
    unwinding, never re-entrantly inside the asynchronous callback;
  * the main-thread spawn/register window defers delivery until the new group is registered, then
    conventional signal termination is restored after cleanup;
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

# Signal callbacks run on the Python main thread between arbitrary bytecodes.  A plain integer is
# deliberately used as the event: ``threading.Event.set`` would itself acquire a lock in the
# callback.  The first signal wins; subsequent signals cannot re-enter an in-progress cleanup.
_PENDING_SIGNAL: int | None = None
_MAIN_CRITICAL_DEPTH = 0
_WAIT_POLL_SECONDS = 0.10

# Keep unpatched methods for owner cleanup.  Tests (and instrumentation) may wrap an instance's
# ``wait`` to inject a failure; reaping must not depend on that wrapper succeeding a second time.
_POPEN_WAIT = subprocess.Popen.wait
_POPEN_POLL = subprocess.Popen.poll


class _SignalExit(BaseException):
    """Internal stack-unwind token for a real SIGINT/SIGTERM."""

    def __init__(self, signum: int):
        super().__init__(signum)
        self.signum = int(signum)


def _begin_main_critical() -> bool:
    """Defer first-signal delivery across an ownership transition in the main thread."""

    global _MAIN_CRITICAL_DEPTH
    if threading.current_thread() is not threading.main_thread():
        return False
    _MAIN_CRITICAL_DEPTH += 1
    return True


def _raise_pending_signal() -> None:
    if _PENDING_SIGNAL is not None:
        raise _SignalExit(_PENDING_SIGNAL)


def _end_main_critical(entered: bool, *, deliver: bool) -> None:
    global _MAIN_CRITICAL_DEPTH
    if not entered:
        return
    if _MAIN_CRITICAL_DEPTH <= 0:
        raise RuntimeError("unbalanced main-thread signal-critical section")
    _MAIN_CRITICAL_DEPTH -= 1
    if deliver and _MAIN_CRITICAL_DEPTH == 0:
        _raise_pending_signal()


def _signal_handler(signum, _frame) -> None:
    """Record one signal and request normal stack unwinding.

    There is intentionally no lock acquisition, registry traversal, process signalling, waiting,
    or file I/O here.  During the main-thread Popen/register or cleanup window, delivery is deferred
    until ownership is stable.  A repeated signal only observes the already-pending event, which
    prevents re-entrant exceptions from interrupting cleanup.
    """

    global _PENDING_SIGNAL
    if _PENDING_SIGNAL is not None:
        return
    _PENDING_SIGNAL = int(signum)
    if _MAIN_CRITICAL_DEPTH > 0:
        return
    raise _SignalExit(signum)


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


def _verify_gone_and_unregister(pgid: int) -> bool:
    """Forget an owned group only after the OS confirms that it is gone."""

    if group_alive(pgid):
        return False
    _unregister(pgid)
    return True


def terminate_group(pgid: int, grace: float = 3.0) -> bool:
    """Kill the WHOLE process group: SIGTERM, wait up to ``grace``, then an UNCONDITIONAL SIGKILL
    belt (a group member can outlive the SIGTERM of its parent while being reparented; relying on
    'the group looked dead' skips the SIGKILL and leaves that stray). SIGKILL is uncatchable, so
    after it + a short reap wait the group is guaranteed gone. Idempotent."""
    if not group_alive(pgid):
        return _verify_gone_and_unregister(pgid)
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return _verify_gone_and_unregister(pgid)
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
    return _verify_gone_and_unregister(pgid)


def _send_group_signal(pgid: int, signum: int) -> bool:
    """Best-effort signal of an owned process group; False means it is already gone."""

    try:
        os.killpg(pgid, signum)
        return True
    except ProcessLookupError:
        return False


def _terminate_and_reap(proc: subprocess.Popen, pgid: int, *, grace: float = 2.0) -> bool:
    """Terminate an owned group and synchronously reap its Popen leader.

    ``terminate_group`` cannot reap because its public input is only a pgid.  ``run`` has stronger
    ownership information, so all of its exits use this helper.  Polling the leader while waiting
    also prevents a leader zombie from making ``killpg(..., 0)`` look alive for the whole grace
    period.
    """

    try:
        _POPEN_POLL(proc)
        if group_alive(pgid):
            _send_group_signal(pgid, signal.SIGTERM)

        deadline = time.monotonic() + max(0.0, grace)
        while time.monotonic() < deadline:
            _POPEN_POLL(proc)
            if not group_alive(pgid):
                break
            time.sleep(0.02)

        if group_alive(pgid):
            _send_group_signal(pgid, signal.SIGKILL)

        # SIGKILL makes a blocking reap bounded by kernel scheduling.  Use a short timed wait first
        # so a pathological platform still gets one final group kill before the definitive reap.
        if proc.returncode is None:
            try:
                _POPEN_WAIT(proc, timeout=2.0)
            except subprocess.TimeoutExpired:
                _send_group_signal(pgid, signal.SIGKILL)
                _POPEN_WAIT(proc)

        reap_deadline = time.monotonic() + 2.0
        while time.monotonic() < reap_deadline and group_alive(pgid):
            time.sleep(0.02)
    finally:
        cleanup_verified = _verify_gone_and_unregister(pgid)
    return cleanup_verified


class Ran:
    """Result of a run, including fail-closed process-group cleanup evidence."""

    def __init__(
        self,
        returncode: int,
        timed_out: bool,
        pgid: int,
        group_cleanup_verified: bool,
    ):
        self.returncode = returncode
        self.timed_out = timed_out
        self.pgid = pgid
        self.group_cleanup_verified = group_cleanup_verified

    @property
    def ok(self) -> bool:
        return (
            self.group_cleanup_verified
            and not self.timed_out
            and self.returncode == 0
        )


def run(cmd: Sequence[str], *, cwd: Optional[str] = None, env: Optional[dict] = None,
        timeout: Optional[float] = None, log_path: Optional[str] = None,
        append: bool = False,
        cancellation_event: Optional[threading.Event] = None) -> Ran:
    """Run ``cmd`` (a LIST -- no shell, no quoting traps) in its own process group. Combined
    stdout+stderr go to ``log_path`` (or are inherited if None). On ``timeout`` the WHOLE group is
    killed (no runaway, no orphans). The group is ALWAYS torn down on return, so a child that
    spawned a worker pool cannot leave strays."""
    if isinstance(cmd, str):
        raise TypeError("cmd must be a list of args (no shell) -- pass ['a','b'], not 'a b'")
    out = None
    child: subprocess.Popen | None = None
    pgid: int | None = None
    timed_out = False
    group_cleanup_verified = False
    try:
        out = open(log_path, "ab" if append else "wb") if log_path else None

        # ``start_new_session=True`` guarantees pgid == child.pid.  Keeping signal delivery
        # deferred through Popen's return bytecode and registration closes the otherwise-unowned
        # spawn/register window without making the child inherit a blocked POSIX signal mask.
        critical = _begin_main_critical()
        try:
            child = subprocess.Popen(
                list(cmd),
                cwd=cwd,
                env=env,
                start_new_session=True,
                stdout=out,
                stderr=subprocess.STDOUT if out else None,
            )
            pgid = child.pid
            _register(pgid)
        finally:
            _end_main_critical(critical, deliver=True)

        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            # Worker threads do not receive Python signal callbacks, but they observe the same
            # pending event and tear down their owned group while the main thread unwinds.
            _raise_pending_signal()
            if cancellation_event is not None and cancellation_event.is_set():
                break
            wait_for = _WAIT_POLL_SECONDS
            if deadline is not None:
                remaining = deadline - time.monotonic()
                wait_for = max(0.0, min(wait_for, remaining))
            try:
                child.wait(timeout=wait_for)
                break
            except subprocess.TimeoutExpired:
                if deadline is not None and time.monotonic() >= deadline:
                    timed_out = True
                    break
    finally:
        # One owner-finally covers registration failures, wait failures, timeout, KeyboardInterrupt,
        # SystemExit, and the internal signal unwind.  Signal delivery is deferred while cleanup
        # owns the registry/log transition so cleanup itself cannot be interrupted re-entrantly.
        critical = _begin_main_critical()
        try:
            try:
                if child is not None:
                    group_cleanup_verified = _terminate_and_reap(
                        child,
                        pgid if pgid is not None else child.pid,
                    )
            finally:
                if out is not None:
                    out.close()
        finally:
            _end_main_critical(critical, deliver=True)

    assert child is not None and pgid is not None
    rc = child.returncode if child.returncode is not None else -signal.SIGKILL
    return Ran(rc, timed_out, pgid, group_cleanup_verified)


def _cleanup_all(*_a) -> None:
    with _LOCK:
        groups = list(_LIVE_GROUPS)
    for pgid in groups:
        terminate_group(pgid, grace=1.0)


atexit.register(_cleanup_all)


_PREVIOUS_EXCEPTHOOK = sys.excepthook


def _signal_excepthook(exc_type, exc_value, traceback) -> None:
    """Finish ordinary cleanup, then restore genuine OS-signal exit semantics."""

    if not isinstance(exc_value, _SignalExit):
        _PREVIOUS_EXCEPTHOOK(exc_type, exc_value, traceback)
        return
    try:
        _cleanup_all()
    finally:
        signal.signal(exc_value.signum, signal.SIG_DFL)
        os.kill(os.getpid(), exc_value.signum)


def _install_signal_cleanup() -> None:
    """Install record-only callbacks; cleanup is performed by owner-finally/excepthook."""

    for _sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(_sig, _signal_handler)
        except (ValueError, OSError):
            pass  # not in main thread / unsupported -> atexit still covers normal exits
    sys.excepthook = _signal_excepthook


_install_signal_cleanup()

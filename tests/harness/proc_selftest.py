"""Self-test for tests/harness/proc.py -- PROVES the orphan-process fix. Spawns a process tree
(a leader with 3 grandchildren in one process group), then kills the group and asserts ZERO
survivors. Also proves timeout kills the whole group and normal completion leaves no stray."""
from __future__ import annotations

import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # put tools/ on path
from harness import proc  # noqa: E402


def _group_pids(pgid: int):
    r = subprocess.run(["pgrep", "-g", str(pgid)], capture_output=True, text=True)
    return sorted(int(x) for x in r.stdout.split())


def _pid_alive(pid: int) -> bool:
    """Alive = the pid exists AND is not a ZOMBIE (defunct = already dead, awaiting reap by its
    parent/init -- NOT a running orphan). Reading /proc state distinguishes the two."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            state = f.read().split(") ", 1)[1][0]  # state char right after "(comm)"
        return state != "Z"
    except (FileNotFoundError, ProcessLookupError, IndexError):
        return False


def test_terminate_group_kills_whole_tree() -> bool:
    # a leader (bash) that spawns 3 grandchildren, all sharing one process group.
    p = subprocess.Popen(["bash", "-c", "sleep 60 & sleep 60 & sleep 60 & wait"],
                         start_new_session=True)
    pgid = os.getpgid(p.pid)
    time.sleep(0.5)
    before = _group_pids(pgid)          # the SPECIFIC member pids (leader + 3 sleeps)
    proc.terminate_group(pgid)
    try:
        p.wait(timeout=3)               # reap the leader so it is not a lingering defunct entry
    except subprocess.TimeoutExpired:
        pass
    time.sleep(0.5)
    # check the ORIGINAL pids are dead (robust vs pgid REUSE -- on a busy box another process
    # can grab the freed pgid, which `pgrep -g` would wrongly report as a survivor).
    survivors = [pid for pid in before if _pid_alive(pid)]
    ok = len(before) >= 4 and survivors == []
    print(f"[A] tree kill: {len(before)} procs in group before, {len(survivors)} of the ORIGINAL "
          f"pids alive after -> {'PASS (no orphans)' if ok else f'FAIL (survivors={survivors})'}")
    for pid in survivors:  # diagnose a real survivor
        d = subprocess.run(["ps", "-o", "pid,ppid,pgid,stat,cmd", "-p", str(pid)],
                           capture_output=True, text=True)
        print("    survivor: " + d.stdout.strip().replace("\n", " | "))
        proc.terminate_group(os.getpgid(pid) if _pid_alive(pid) else pgid)  # clean it up
    return ok


def test_run_timeout_kills_group() -> bool:
    ran = proc.run(["bash", "-c", "sleep 60 & sleep 60 & wait"], timeout=1.0)
    time.sleep(0.3)
    alive = proc.group_alive(ran.pgid)
    ok = ran.timed_out and not alive
    print(f"[B] timeout kill: timed_out={ran.timed_out}, group_alive_after={alive} -> "
          f"{'PASS' if ok else 'FAIL'}")
    return ok


def test_run_normal_no_stray() -> bool:
    ran = proc.run(["bash", "-c", "echo hi >/dev/null"])
    time.sleep(0.2)
    ok = ran.ok and not proc.group_alive(ran.pgid)
    print(f"[C] normal completion: ok={ran.ok}, group_alive_after={proc.group_alive(ran.pgid)} -> "
          f"{'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    results = [test_terminate_group_kills_whole_tree(),
               test_run_timeout_kills_group(),
               test_run_normal_no_stray()]
    ok = all(results)
    print(f"PROC-SELFTEST: {'PASS' if ok else 'FAIL'} ({sum(results)}/3)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Decide the gpu_03 worker count from its own measured rate, and act on it.

The restricted-MPS gpu_03 shard has a same-shard, same-test-selection baseline
at ``jobs=4``: 1.84 wall-seconds per mutant over a 300-mutant prefix.  This
supervisor waits for the current ``jobs=16`` run of that shard to accumulate a
comparable prefix, measures its rate, and then either leaves the chain alone or
reverts the remaining x86 shards to the known-good worker count and restarts
them.

It is an operational supervisor, not mutation evidence.  Kill rates do not
depend on the worker count (the per-mutant timeout scales with the same
concurrency and a real timeout or resource exhaustion aborts the shard), so
this only ever changes throughput.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[1]
LOGDIR = REPO / "outputs" / "simulator_validation" / "logs"
SUITE = REPO / "tests" / "_support" / "restricted_mps_mutation_suite.json"
TEST_FILE = REPO / "tests" / "harness" / "test_mutation.py"
TAG = "restricted_mps_mutation_gpu_03_carrier_execution"
CHECKPOINT = LOGDIR / f"{TAG}_mutation_checkpoint.json"
JOBS4_BASELINE_S = 1.84  # same shard, same selection, 300-mutant prefix
X86_SHARDS = ("gpu_03_carrier_execution", "gpu_05_certification")
CHAIN_LOG = LOGDIR / "mutation_x86_autotuned_20260725.log"
JOURNAL = LOGDIR / "mutation_shard_autotune.log"


def say(message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}"
    print(line, flush=True)
    with JOURNAL.open("a", buffering=1) as stream:
        stream.write(line + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def completed_count() -> int | None:
    try:
        doc = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    rows = doc.get("completed_prefix")
    return len(rows) if isinstance(rows, list) else None


def plan_total() -> int | None:
    try:
        doc = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = doc.get("plan_mutant_count")
    return value if isinstance(value, int) else None


def wave_phase_start() -> float | None:
    logs = sorted(LOGDIR.glob(f"{TAG}_worker_*.log"))
    if not logs:
        return None
    births = []
    for path in logs[:64]:
        try:
            births.append(path.stat().st_ctime)
        except OSError:
            continue
    return min(births) if births else None


def chain_alive() -> bool:
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes().decode("utf-8", "replace")
        except OSError:
            continue
        if "harness/mutation.py" in cmdline.replace("\x00", " "):
            return True
    return False


def stop_chain() -> None:
    say("stopping the running chain")
    for pattern in ("harness/mutation.py", "mutation_x86_j16"):
        subprocess.run(["pkill", "-f", pattern], check=False)
    time.sleep(4)
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            environ = (entry / "environ").read_bytes().decode("utf-8", "replace")
        except OSError:
            continue
        if "MUTANT_UNDER_TEST=" in environ:
            try:
                os.kill(int(entry.name), signal.SIGKILL)
            except OSError:
                pass
    time.sleep(3)
    say(f"chain alive after stop: {chain_alive()}")


def set_jobs(value: int) -> None:
    """Point the remaining x86 shards at a different worker count."""
    lines = SUITE.read_text(encoding="utf-8").splitlines(keepends=True)
    current = None
    touched = []
    for index, line in enumerate(lines):
        if '"name":' in line:
            current = line.split('"')[3]
        match = re.search(r'"jobs": (\d+)', line)
        if match and current and any(stem in current for stem in X86_SHARDS):
            lines[index] = line[: match.start()] + f'"jobs": {value}' + line[match.end():]
            touched.append(current)
    SUITE.write_text("".join(lines), encoding="utf-8")
    say(f"suite jobs -> {value} for {touched}")

    for stem in X86_SHARDS:
        path = REPO / "tests" / "_support" / f"restricted_mps_mutation_{stem}.json"
        text = path.read_text(encoding="utf-8")
        new = re.sub(r'"jobs": \d+,', f'"jobs": {value},', text, count=1)
        path.write_text(new, encoding="utf-8")
        say(f"{path.name} jobs -> {value}")

    # keep the topology self-test honest about the new declaration
    test_text = TEST_FILE.read_text(encoding="utf-8")
    updated = test_text.replace(
        '        ("gpu_serial", 16),\n        ("gpu_serial", 16),\n        ("gpu_serial", 16),\n',
        f'        ("gpu_serial", 16),\n        ("gpu_serial", {value}),\n'
        f'        ("gpu_serial", {value}),\n',
    )
    if updated != test_text:
        TEST_FILE.write_text(updated, encoding="utf-8")
        say("topology self-test expectation updated")


def clear_checkpoints() -> None:
    for stem in X86_SHARDS:
        for path in LOGDIR.glob(f"restricted_mps_mutation_{stem}*_mutation_checkpoint.json"):
            path.unlink(missing_ok=True)
            say(f"removed stale checkpoint {path.name}")


def relaunch() -> None:
    script = (
        f'cd {REPO} && : > "{CHAIN_LOG}" && '
        'for reg in gpu_03_carrier_execution gpu_05_certification; do '
        f'echo "=== BATCH START $reg $(date -u "+%F %T")Z ===" >> "{CHAIN_LOG}"; '
        "conda run --no-capture-output -n ecs python tests/harness/mutation.py "
        f'"tests/_support/restricted_mps_mutation_$reg.json" >> "{CHAIN_LOG}" 2>&1; rc=$?; '
        f'echo "=== BATCH END $reg rc=$rc $(date -u "+%F %T")Z ===" >> "{CHAIN_LOG}"; '
        f'[ $rc -ne 0 ] && {{ echo "=== CHAIN ABORTED at $reg ===" >> "{CHAIN_LOG}"; break; }}; '
        f'done; echo "=== CHAIN DONE $(date -u "+%F %T")Z ===" >> "{CHAIN_LOG}"'
    )
    subprocess.Popen(["bash", "-c", script], start_new_session=True)
    say(f"relaunched gpu_03 -> gpu_05; log {CHAIN_LOG}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, default=160, help="mutants before deciding")
    parser.add_argument("--max-wait-hours", type=float, default=8.0)
    parser.add_argument("--fallback-jobs", type=int, default=4)
    args = parser.parse_args()
    if not 40 <= args.sample <= 5000:
        parser.error("--sample must be in [40, 5000]")
    if not 1 <= args.fallback_jobs <= 16:
        parser.error("--fallback-jobs must be in [1, 16]")
    return args


def main() -> int:
    args = parse_args()
    LOGDIR.mkdir(parents=True, exist_ok=True)
    say(f"autotune armed: sample={args.sample} baseline={JOBS4_BASELINE_S}s/mutant")

    deadline = time.monotonic() + args.max_wait_hours * 3600.0
    while time.monotonic() < deadline:
        done = completed_count()
        if done is not None and done >= args.sample:
            break
        if done is None and not chain_alive():
            say("no chain running and no gpu_03 checkpoint; nothing to tune")
            return 1
        time.sleep(20)
    else:
        say("gpu_03 never reached the decision sample within the wait window")
        return 1

    done = completed_count() or 0
    total = plan_total() or 0
    start = wave_phase_start()
    if start is None:
        say("worker logs missing; cannot measure")
        return 1
    elapsed = time.time() - start
    rate = elapsed / done
    say(
        f"measured gpu_03 at jobs=16: {done}/{total} in {elapsed / 60:.1f} min "
        f"-> {rate:.2f} wall-s/mutant (baseline {JOBS4_BASELINE_S:.2f})"
    )

    if rate < JOBS4_BASELINE_S:
        say(
            f"VERDICT keep jobs=16 ({JOBS4_BASELINE_S / rate:.2f}x faster); "
            f"projected shard {total * rate / 3600:.2f} h. No action."
        )
        return 0

    say(
        f"VERDICT jobs=16 is {rate / JOBS4_BASELINE_S:.2f}x SLOWER than jobs=4; "
        f"reverting the remaining x86 shards to jobs={args.fallback_jobs}"
    )
    stop_chain()
    set_jobs(args.fallback_jobs)
    clear_checkpoints()
    relaunch()
    say("autotune complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

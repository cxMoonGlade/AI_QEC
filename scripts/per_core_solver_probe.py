#!/usr/bin/env python3
"""Pin the captured pinv replay to one CPU core at a time and record each outcome.

The defect this screens for is a single degraded core: on the replaced Core Ultra
9 285K, logical cpu6 (core 40, a favored boost core) miscomputed only at its own
boost bin.  Generic all-core stress passes that fault because the all-core clock
never reaches the bad bin, and the workload only lands on the bad core when the
scheduler puts it there.  Pinning removes both escapes.

Evidence is written per core, fsynced before the core starts and after it ends,
so an ungraceful host disappearance attributes to exactly one core after reboot:
the last ``core_started`` row without a matching ``core_finished`` names it.

This is a hardware screening diagnostic.  It is not simulator acceptance, not
scientific evidence, and not a certificate of CPU health -- a clean sweep bounds
the fault, it does not prove its absence.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
REPLAY = REPO / "scripts" / "run_pinv_170_test.py"
OUTPUT_PARENT = REPO / "outputs" / "simulator_validation" / "per_core_solver_probe"
SCHEMA = "error_coupling_simulator.runtime.per_core_solver_probe.v1"


def timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="microseconds")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def append_jsonl(path: Path, value: Any) -> None:
    """Append one durable row; the reset-attribution guarantee depends on the fsync."""

    with path.open("ab", buffering=0) as stream:
        stream.write(canonical_bytes(value) + b"\n")
        os.fsync(stream.fileno())


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(canonical_bytes(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def boot_id() -> str:
    path = Path("/proc/sys/kernel/random/boot_id")
    return path.read_text(encoding="ascii").strip() if path.is_file() else "unavailable"


def core_topology() -> list[dict[str, Any]]:
    """Logical CPUs with their core id and maximum boost, hottest first.

    Frequency class matters: the previous fault appeared only at a favored core's
    own boost bin, so the fast cores are screened before the slow ones.
    """

    rows: list[dict[str, Any]] = []
    for entry in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*")):
        name = entry.name
        if not re.fullmatch(r"cpu\d+", name):
            continue
        index = int(name[3:])
        try:
            maximum = int((entry / "cpufreq" / "cpuinfo_max_freq").read_text()) // 1000
        except OSError:
            maximum = 0
        try:
            core_id = int((entry / "topology" / "core_id").read_text())
        except OSError:
            core_id = -1
        rows.append({"cpu": index, "core_id": core_id, "max_mhz": maximum})
    if not rows:
        raise SystemExit("could not read CPU topology")
    fastest = max(row["max_mhz"] for row in rows)
    for row in rows:
        # A heterogeneous package mixes performance and efficiency cores; the
        # class is recorded so a failure can be read against the core's own bin.
        row["class"] = "performance" if row["max_mhz"] >= fastest - 400 else "efficiency"
    rows.sort(key=lambda row: (-row["max_mhz"], row["cpu"]))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, default=40,
        help="pinv calls per core; 170 is the full replay (much slower, more thorough)",
    )
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--cores", help="comma-separated logical CPUs; default is every core, fastest first"
    )
    parser.add_argument(
        "--parallel-class", action="store_true",
        help=(
            "run every core of one frequency class concurrently, then the next class. "
            "Much faster, but a hard reset then names a CLASS rather than a core; "
            "re-run the implicated class serially to isolate."
        ),
    )
    parser.add_argument(
        "--resume-from", type=Path,
        help="an existing run directory to continue; cores already finished are skipped",
    )
    parser.add_argument(
        "--acknowledge-reset-risk", action="store_true",
        help="required for CUDA: this workload has hard-reset this host before",
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 170:
        parser.error("--limit must be in [1, 170]")
    if args.device == "cuda" and not args.acknowledge_reset_risk:
        parser.error("CUDA execution requires --acknowledge-reset-risk")
    return args


def main() -> int:
    args = parse_args()
    if not REPLAY.is_file():
        raise SystemExit(f"replay reproducer missing: {REPLAY}")

    topology = core_topology()
    if args.cores:
        wanted = {int(value) for value in args.cores.split(",") if value.strip()}
        topology = [row for row in topology if row["cpu"] in wanted]
        if not topology:
            raise SystemExit("no requested core matched the topology")

    if args.resume_from:
        run_root = args.resume_from.resolve(strict=True)
    else:
        OUTPUT_PARENT.mkdir(mode=0o700, parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        run_root = OUTPUT_PARENT / f"per_core_{args.device}_{stamp}"
        run_root.mkdir(mode=0o700, exist_ok=False)
        fsync_directory(run_root.parent)
    events = run_root / "events.jsonl"

    finished: set[int] = set()
    if events.is_file():
        for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("kind") == "core_finished":
                finished.add(int(row["cpu"]))
        if finished:
            print(f"resuming; {len(finished)} cores already finished", flush=True)

    common = {
        "schema": SCHEMA,
        "boot_id": boot_id(),
        "hostname": platform.node(),
        "kernel": platform.release(),
        "device": args.device,
        "calls_per_core": args.limit,
        "evidence_class": "hardware_screening_not_acceptance_or_health_certificate",
    }
    atomic_json(
        run_root / "preflight.json",
        {**common, "started_at": timestamp(), "topology": topology,
         "cpu_model": next((line.split(":", 1)[1].strip()
                            for line in Path("/proc/cpuinfo").read_text().splitlines()
                            if line.startswith("model name")), "unknown")},
    )
    print(f"run_root={run_root}", flush=True)
    print(f"cores={len(topology)} calls_per_core={args.limit} device={args.device}", flush=True)

    def launch(row: dict[str, Any]):
        cpu = row["cpu"]
        log_path = run_root / f"cpu{cpu:02d}.log"
        append_jsonl(events, {**common, "kind": "core_started", "timestamp": timestamp(), **row})
        sink = log_path.open("wb", buffering=0)
        child = subprocess.Popen(
            ["taskset", "-c", str(cpu),
             "conda", "run", "--no-capture-output", "-n", "ecs",
             "python", str(REPLAY), "--device", args.device,
             "--limit", str(args.limit), "--acknowledge-reset-risk"],
            cwd=str(REPO), stdout=sink, stderr=subprocess.STDOUT, start_new_session=True,
        )
        return child, sink, log_path, time.monotonic()

    def harvest(row, child, sink, log_path, started) -> dict[str, Any]:
        returncode = child.wait()
        os.fsync(sink.fileno())
        sink.close()
        elapsed = time.monotonic() - started
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-400:]
        status = "passed" if returncode == 0 else "failed"
        record = {
            **common, "kind": "core_finished", "timestamp": timestamp(), **row,
            "status": status, "returncode": returncode,
            "elapsed_s": round(elapsed, 2), "log": log_path.name, "log_tail": tail[-300:],
        }
        append_jsonl(events, record)
        print(
            f"  cpu{row['cpu']:02d} ({row['class'][:4]}, {row['max_mhz']}MHz) "
            f"{status.upper():6s} rc={returncode} {elapsed:6.1f}s",
            flush=True,
        )
        return record

    pending = [row for row in topology if row["cpu"] not in finished]
    results: list[dict[str, Any]] = []
    if args.parallel_class:
        # Fastest class first: the previous fault lived on a favored boost core.
        for klass in sorted({row["class"] for row in pending},
                            key=lambda k: 0 if k == "performance" else 1):
            group = [row for row in pending if row["class"] == klass]
            if not group:
                continue
            print(f"class={klass} concurrent={len(group)} "
                  f"cpus={[row['cpu'] for row in group]}", flush=True)
            live = [(row, *launch(row)) for row in group]
            results.extend(harvest(*entry) for entry in live)
    else:
        for row in pending:
            results.append(harvest(row, *launch(row)))

    failures = [row for row in results if row["status"] != "passed"]
    summary = {
        **common, "kind": "summary", "finished_at": timestamp(),
        "cores_run": len(results), "cores_failed": len(failures),
        "failed_cpus": [row["cpu"] for row in failures], "results": results,
        "no_hard_reset_during_run": True,
        "parallel_class": bool(args.parallel_class),
        "per_core_attribution": (
            "class" if args.parallel_class else "core"
        ),
        "claim_boundary": (
            "per-core screening of one solver workload; a clean sweep bounds the "
            "fault, it does not prove the processor is healthy"
        ),
    }
    atomic_json(run_root / "summary.json", summary)
    print(f"\nsummary={run_root / 'summary.json'}", flush=True)
    print(f"cores run={len(results)} failed={len(failures)}", flush=True)
    if failures:
        for row in failures:
            print(f"  FAILED cpu{row['cpu']} (core_id {row['core_id']}, "
                  f"{row['max_mhz']}MHz {row['class']})", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

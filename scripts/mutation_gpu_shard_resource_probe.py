#!/usr/bin/env python3
"""Sample host/device resource use during a GPU mutation shard's worker phase.

Read-only observer for an already-running ``tests/harness/mutation.py`` GPU
shard.  It waits for the per-mutant worker phase (stage 8) to appear, samples
device and host telemetry while it runs, and writes a peak/percentile summary
that can inform the worker-count decision for later shards.

This is a runtime resource diagnostic.  It is not mutation evidence, not a
kill-rate claim, and it never reads or writes the live ``mutants/`` tree, the
shard checkpoint, or any harness-owned artifact.
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
LOG_ROOT = REPO / "outputs" / "simulator_validation" / "logs"
OUTPUT_PARENT = REPO / "outputs" / "simulator_validation" / "mutation_resource_probes"
RESULT_SCHEMA = "error_coupling_simulator.runtime.mutation_shard_resource_probe.v1"

SMI_FIELDS = (
    "memory.used",
    "memory.total",
    "utilization.gpu",
    "utilization.memory",
    "power.draw",
    "temperature.gpu",
    "clocks.sm",
)


def timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="microseconds")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def append_jsonl(path: Path, value: Any) -> None:
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


def smi_sample() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        f"--query-gpu={','.join(SMI_FIELDS)}",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        return {"error": f"{type(error).__name__}: {error}"}
    if completed.returncode != 0:
        return {"error": completed.stderr.strip()[:200]}
    row = completed.stdout.strip().splitlines()[0].split(",")
    sample: dict[str, Any] = {}
    for name, raw in zip(SMI_FIELDS, row):
        text = raw.strip()
        try:
            sample[name] = float(text)
        except ValueError:
            sample[name] = text
    return sample


def compute_apps() -> list[dict[str, Any]]:
    command = [
        "nvidia-smi",
        "--query-compute-apps=pid,used_memory",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    apps: list[dict[str, Any]] = []
    for line in completed.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            continue
        try:
            apps.append({"pid": int(parts[0]), "used_mib": float(parts[1])})
        except ValueError:
            continue
    return apps


def read_proc_text(pid: int, name: str) -> str:
    try:
        return (Path("/proc") / str(pid) / name).read_bytes().decode(
            "utf-8", errors="replace"
        )
    except OSError:
        return ""


def worker_pids(tag: str) -> list[int]:
    """PIDs whose environment carries MUTANT_UNDER_TEST (stage-8 workers)."""
    found: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        environ = read_proc_text(pid, "environ")
        if "MUTANT_UNDER_TEST=" in environ:
            found.append(pid)
    return sorted(found)


def shard_driver_alive(registry_stem: str) -> bool:
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        cmdline = read_proc_text(int(entry.name), "cmdline").replace("\x00", " ")
        if "tests/harness/mutation.py" in cmdline and registry_stem in cmdline:
            return True
    return False


def worker_log_count(tag: str) -> int:
    if not LOG_ROOT.is_dir():
        return 0
    return len(list(LOG_ROOT.glob(f"{tag}_worker_*.log")))


def host_memory() -> dict[str, int]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            key, _, rest = line.partition(":")
            if key in ("MemTotal", "MemAvailable"):
                values[key] = int(rest.strip().split()[0])
    except OSError:
        pass
    return values


def load_average() -> list[float]:
    try:
        return [float(v) for v in os.getloadavg()]
    except OSError:
        return []


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


def summarize(name: str, values: list[float]) -> dict[str, Any]:
    if not values:
        return {"metric": name, "samples": 0}
    return {
        "metric": name,
        "samples": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "p95": percentile(values, 0.95),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        default="restricted_mps_mutation_gpu_03_carrier_execution",
        help="shard tag; used for worker-log discovery and output naming",
    )
    parser.add_argument("--interval", type=float, default=15.0, help="sample seconds")
    parser.add_argument(
        "--max-wait-hours",
        type=float,
        default=6.0,
        help="give up if the worker phase never starts within this window",
    )
    parser.add_argument(
        "--max-run-hours",
        type=float,
        default=24.0,
        help="hard stop for the sampling phase",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,120}", args.tag):
        parser.error("tag is not a safe identifier")
    if not 1.0 <= args.interval <= 300.0:
        parser.error("--interval must be in [1, 300] seconds")
    return args


def main() -> int:
    args = parse_args()
    registry_stem = args.tag.replace("restricted_mps_mutation_", "")

    if not shard_driver_alive(args.tag) and not shard_driver_alive(registry_stem):
        print(
            f"precondition failed: no running mutation.py for {args.tag}",
            file=sys.stderr,
            flush=True,
        )
        return 2

    run_id = f"resprobe_{args.tag}_{datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')}"
    OUTPUT_PARENT.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_root = OUTPUT_PARENT / run_id
    run_root.mkdir(mode=0o700, exist_ok=False)
    samples_path = run_root / "samples.jsonl"

    common = {
        "schema": RESULT_SCHEMA,
        "run_id": run_id,
        "tag": args.tag,
        "hostname": platform.node(),
        "interval_s": args.interval,
        "evidence_class": "runtime_resource_diagnostic_not_mutation_evidence",
    }
    atomic_json(
        run_root / "preflight.json",
        {
            **common,
            "started_at": timestamp(),
            "kernel": platform.release(),
            "device": smi_sample(),
            "host_memory_kib": host_memory(),
            "note": (
                "observer only; never reads mutants/, the shard checkpoint, or "
                "harness-owned artifacts"
            ),
        },
    )
    print(f"run_root={run_root}", flush=True)
    print(f"waiting for worker phase of {args.tag}", flush=True)

    deadline = time.monotonic() + args.max_wait_hours * 3600.0
    started = False
    while time.monotonic() < deadline:
        if worker_pids(args.tag) or worker_log_count(args.tag) > 0:
            started = True
            break
        if not shard_driver_alive(args.tag) and not shard_driver_alive(registry_stem):
            print("shard driver exited before the worker phase began", flush=True)
            atomic_json(
                run_root / "result.json",
                {**common, "status": "driver_exited_before_worker_phase",
                 "finished_at": timestamp()},
            )
            return 1
        time.sleep(min(args.interval, 30.0))

    if not started:
        atomic_json(
            run_root / "result.json",
            {**common, "status": "worker_phase_not_observed", "finished_at": timestamp()},
        )
        print("worker phase never appeared within the wait window", flush=True)
        return 1

    print(f"worker phase detected at {timestamp()}; sampling", flush=True)
    series: dict[str, list[float]] = {
        "gpu_memory_used_mib": [],
        "gpu_utilization_pct": [],
        "gpu_power_w": [],
        "gpu_temperature_c": [],
        "worker_count": [],
        "cuda_process_count": [],
        "cuda_total_mib": [],
        "host_available_gib": [],
        "load1": [],
    }
    sequence = 0
    idle_rounds = 0
    run_deadline = time.monotonic() + args.max_run_hours * 3600.0

    while time.monotonic() < run_deadline:
        sequence += 1
        device = smi_sample()
        apps = compute_apps()
        workers = worker_pids(args.tag)
        memory = host_memory()
        loads = load_average()

        cuda_total = sum(app["used_mib"] for app in apps)
        available_gib = memory.get("MemAvailable", 0) / (1024.0 * 1024.0)

        for key, value in (
            ("gpu_memory_used_mib", device.get("memory.used")),
            ("gpu_utilization_pct", device.get("utilization.gpu")),
            ("gpu_power_w", device.get("power.draw")),
            ("gpu_temperature_c", device.get("temperature.gpu")),
            ("worker_count", float(len(workers))),
            ("cuda_process_count", float(len(apps))),
            ("cuda_total_mib", cuda_total),
            ("host_available_gib", available_gib),
            ("load1", loads[0] if loads else None),
        ):
            if isinstance(value, (int, float)):
                series[key].append(float(value))

        append_jsonl(
            samples_path,
            {
                **common,
                "kind": "sample",
                "sequence": sequence,
                "timestamp": timestamp(),
                "device": device,
                "cuda_processes": apps,
                "cuda_total_mib": cuda_total,
                "worker_pids": workers,
                "worker_log_files": worker_log_count(args.tag),
                "host_memory_kib": memory,
                "loadavg": loads,
            },
        )

        if sequence % 20 == 0:
            print(
                f"[{sequence:05d}] workers={len(workers)} "
                f"gpu_mem={device.get('memory.used')}MiB "
                f"util={device.get('utilization.gpu')}% "
                f"load1={loads[0] if loads else '?'}",
                flush=True,
            )

        driver_alive = shard_driver_alive(args.tag) or shard_driver_alive(registry_stem)
        if not workers and not driver_alive:
            idle_rounds += 1
            if idle_rounds >= 3:
                break
        else:
            idle_rounds = 0
        time.sleep(args.interval)

    summary = {
        **common,
        "status": "completed",
        "finished_at": timestamp(),
        "sample_count": sequence,
        "metrics": [summarize(name, values) for name, values in series.items()],
        "worker_log_files_final": worker_log_count(args.tag),
        "claim_boundary": (
            "host/device resource observation of one mutation shard worker phase; "
            "not mutation evidence and not a kill-rate or capacity guarantee"
        ),
    }
    atomic_json(run_root / "summary.json", summary)
    print(f"summary={run_root / 'summary.json'}", flush=True)
    for metric in summary["metrics"]:
        if metric.get("samples"):
            print(
                f"  {metric['metric']}: max={metric['max']:.1f} "
                f"p95={metric['p95']:.1f} median={metric['median']:.1f}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

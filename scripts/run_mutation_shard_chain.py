#!/usr/bin/env python3
"""Run an ordered list of mutation shards, distinguishing a failed gate from a crash.

``tests/harness/mutation.py`` exits 1 both when a shard completes below the
kill-rate bar and when it aborts, so a naive ``rc != 0`` chain stops on a
perfectly good scientific result.  A completed shard always publishes its
``MUTATION tag=... PASS|FAIL`` summary line; an aborted one does not.  This
runner keys on that line: a below-bar shard is recorded and the chain
continues, while a crash stops the chain with the evidence intact.

This is an operational runner.  It performs no scoring of its own and changes
no shard input.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
LOGDIR = REPO / "outputs" / "simulator_validation" / "logs"
SUMMARY_RE = re.compile(
    r"^MUTATION tag=(?P<tag>\S+) total=(?P<total>\d+) killed=(?P<killed>\d+) "
    r"survived=(?P<survived>\d+).*?raw_kill_rate=(?P<raw>[0-9.]+).*?"
    r"(?P<verdict>PASS|FAIL)\s*$"
)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def emit(stream, message: str) -> None:
    line = f"{timestamp()} {message}"
    print(line, flush=True)
    stream.write(line + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def shard_summary(log_path: Path) -> dict | None:
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in reversed(text.splitlines()):
        match = SUMMARY_RE.match(line.strip())
        if match:
            data = match.groupdict()
            return {
                "tag": data["tag"],
                "total": int(data["total"]),
                "killed": int(data["killed"]),
                "survived": int(data["survived"]),
                "raw_kill_rate": float(data["raw"]),
                "verdict": data["verdict"],
            }
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shards", nargs="+", help="registry stems, e.g. gpu_03_carrier_execution")
    parser.add_argument("--env", default="ecs")
    parser.add_argument("--log", type=Path, default=LOGDIR / "mutation_shard_chain.log")
    args = parser.parse_args()
    for stem in args.shards:
        if not re.fullmatch(r"[a-z0-9_]{3,80}", stem):
            parser.error(f"unsafe shard stem: {stem!r}")
        registry = REPO / "tests" / "_support" / f"restricted_mps_mutation_{stem}.json"
        if not registry.is_file():
            parser.error(f"registry not found: {registry}")
    return args


def main() -> int:
    args = parse_args()
    LOGDIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    crashed: str | None = None

    with args.log.open("a", buffering=1) as journal:
        emit(journal, f"chain start: {' -> '.join(args.shards)}")
        for stem in args.shards:
            registry = f"tests/_support/restricted_mps_mutation_{stem}.json"
            # the PASS/FAIL summary is written to the runner's stdout, not to the
            # shard's own log, so capture it per shard and keep it as evidence
            capture = LOGDIR / f"restricted_mps_mutation_{stem}_chain_stdout.log"
            emit(journal, f"BATCH START {stem} (stdout -> {capture.name})")
            with capture.open("wb", buffering=0) as sink:
                completed = subprocess.run(
                    [
                        "conda", "run", "--no-capture-output", "-n", args.env,
                        "python", "tests/harness/mutation.py", registry,
                    ],
                    cwd=REPO,
                    stdout=sink,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                os.fsync(sink.fileno())
            summary = shard_summary(capture)
            if summary is None:
                crashed = stem
                emit(
                    journal,
                    f"BATCH ABORTED {stem} rc={completed.returncode} "
                    "(no MUTATION summary line published -- this is a crash, not a failed gate)",
                )
                break
            summary["returncode"] = completed.returncode
            results.append(summary)
            emit(
                journal,
                f"BATCH END {stem} rc={completed.returncode} verdict={summary['verdict']} "
                f"total={summary['total']} killed={summary['killed']} "
                f"survived={summary['survived']} kill_rate={summary['raw_kill_rate']:.4f} "
                "(below-bar is a result, chain continues)",
            )

        emit(journal, "chain done")
        for row in results:
            emit(
                journal,
                f"  {row['tag']}: {row['verdict']} kill_rate={row['raw_kill_rate']:.4f} "
                f"survivors={row['survived']}",
            )
        if crashed:
            emit(journal, f"  chain stopped early at {crashed}")

    print(json.dumps({"results": results, "crashed": crashed}, indent=2), flush=True)
    return 2 if crashed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Aggregate mutation-shard survivors into a ranked coverage-gap map.

Reads the published ``*_mutation_survivors.json`` batch documents, combines
their not-killed sets, and reports where the surviving mutants concentrate --
by module, by function, and by how much of the reviewed semantic-disposition
table actually applies.

This is a reporting instrument over already-published batch evidence.  It
computes no kill rate of its own, classifies nothing, and never decides whether
a survivor is equivalent or reachable; that judgement belongs to the semantic
disposition review.
"""

from __future__ import annotations

import argparse
import collections
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
LOGDIR = REPO / "outputs" / "simulator_validation" / "logs"
OUTPUT_PARENT = REPO / "outputs" / "simulator_validation" / "mutation_gap_maps"
RESULT_SCHEMA = "error_coupling_simulator.harness.mutation_survivor_gap_map.v1"
# error_coupling_simulator.pkg.mod.x_<function>__mutmut_<n>
MUTANT_RE = re.compile(r"^(?P<module>.+?)\.x_(?P<function>.+?)__mutmut_(?P<index>\d+)$")


def timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(canonical_bytes(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def split_mutant(name: str) -> tuple[str, str]:
    match = MUTANT_RE.match(name)
    if not match:
        return name.rsplit(".", 1)[0] if "." in name else "?", "<unparsed>"
    return match.group("module"), match.group("function")


def load_batch(path: Path) -> dict[str, Any] | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"skip {path.name}: {type(error).__name__}", file=sys.stderr, flush=True)
        return None
    if not isinstance(doc, dict) or "semantic" not in doc:
        print(f"skip {path.name}: not a batch-run document", file=sys.stderr, flush=True)
        return None
    semantic = doc["semantic"]
    critical = semantic.get("critical") or {}
    not_killed = critical.get("not_killed") or []
    disposition = doc.get("disposition_authentication") or {}
    return {
        "tag": doc.get("tag"),
        "path": str(path.relative_to(REPO)),
        "jobs": doc.get("jobs"),
        "total": doc.get("total"),
        "killed": doc.get("killed"),
        "survived": doc.get("survived"),
        "raw_kill_rate": doc.get("kill_rate"),
        "semantic_total": semantic.get("total"),
        "semantic_killed": semantic.get("killed"),
        "semantic_kill_rate": semantic.get("kill_rate"),
        "bar": semantic.get("bar", doc.get("bar")),
        "pass": semantic.get("pass", doc.get("pass")),
        "excluded_counts": semantic.get("excluded_counts") or {},
        "dispositions_reviewed": disposition.get("reviewed_count"),
        "dispositions_applied": disposition.get("applied_reviewed_count"),
        "dispositions_out_of_scope": disposition.get("out_of_scope_reviewed_count"),
        "scope_complete": disposition.get("scope_complete"),
        "not_killed": not_killed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--glob",
        default="restricted_mps_mutation_*_mutation_survivors.json",
        help="batch documents to combine, relative to the log directory",
    )
    parser.add_argument("--top", type=int, default=25, help="functions to rank")
    parser.add_argument("--out", type=Path, help="write the JSON map here")
    args = parser.parse_args()
    if not 1 <= args.top <= 500:
        parser.error("--top must be in [1, 500]")
    return args


def main() -> int:
    args = parse_args()
    paths = sorted(LOGDIR.glob(args.glob))
    if not paths:
        print(f"no batch documents match {args.glob} under {LOGDIR}", file=sys.stderr, flush=True)
        return 2

    batches = [row for row in (load_batch(path) for path in paths) if row is not None]
    if not batches:
        print("no usable batch documents", file=sys.stderr, flush=True)
        return 2

    by_function: collections.Counter[tuple[str, str]] = collections.Counter()
    by_module: collections.Counter[str] = collections.Counter()
    by_status: collections.Counter[str] = collections.Counter()
    per_batch_survivors: dict[str, int] = {}

    for batch in batches:
        rows = batch.pop("not_killed")
        per_batch_survivors[batch["tag"]] = len(rows)
        for row in rows:
            name = row.get("mutant", "")
            by_status[row.get("status", "?")] += 1
            module, function = split_mutant(name)
            by_function[(module, function)] += 1
            by_module[module] += 1

    combined_survivors = sum(per_batch_survivors.values())
    ranked = [
        {
            "module": module.rsplit(".", 1)[-1],
            "qualified_module": module,
            "function": function,
            "survivors": count,
            "share": round(count / combined_survivors, 4) if combined_survivors else 0.0,
        }
        for (module, function), count in by_function.most_common(args.top)
    ]

    report = {
        "schema": RESULT_SCHEMA,
        "generated_at": timestamp(),
        "batches": batches,
        "combined": {
            "batch_count": len(batches),
            "mutants": sum(b["total"] or 0 for b in batches),
            "killed": sum(b["killed"] or 0 for b in batches),
            "survivors": combined_survivors,
            "survivors_by_status": dict(by_status),
            "distinct_functions": len(by_function),
            "distinct_modules": len(by_module),
            "dispositions_applied_total": sum(b["dispositions_applied"] or 0 for b in batches),
        },
        "ranked_functions": ranked,
        "modules": [
            {"qualified_module": module, "survivors": count}
            for module, count in by_module.most_common()
        ],
        "claim_boundary": (
            "reporting instrument over published batch evidence; it neither scores "
            "nor classifies survivors and is not a coverage or equivalence claim"
        ),
    }

    destination = args.out or (
        OUTPUT_PARENT / f"gap_map_{datetime.now().astimezone():%Y%m%dT%H%M%S%z}.json"
    )
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    atomic_json(destination, report)

    print(f"batches: {len(batches)}", flush=True)
    for batch in batches:
        print(
            f"  {batch['tag']}: jobs={batch['jobs']} total={batch['total']} "
            f"killed={batch['killed']} survived={per_batch_survivors[batch['tag']]} "
            f"raw={batch['raw_kill_rate']} semantic={batch['semantic_kill_rate']} "
            f"pass={batch['pass']} dispositions_applied={batch['dispositions_applied']}",
            flush=True,
        )
    combined = report["combined"]
    print(
        f"combined: {combined['mutants']} mutants, {combined['killed']} killed, "
        f"{combined['survivors']} survivors across {combined['distinct_functions']} functions",
        flush=True,
    )
    print(f"survivor statuses: {combined['survivors_by_status']}", flush=True)
    print(f"reviewed dispositions applied anywhere: {combined['dispositions_applied_total']}", flush=True)
    print(f"\ntop {len(ranked)} gap clusters:", flush=True)
    for row in ranked:
        print(
            f"  {row['survivors']:5d}  {row['share'] * 100:5.1f}%  "
            f"{row['module']}::{row['function']}",
            flush=True,
        )
    print(f"\nmap written to {destination}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

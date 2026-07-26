#!/usr/bin/env python3
"""Check that docs/READING_ORDER.md still points at things that exist and are current.

The reading order is curated, so most of it cannot be machine-derived. Three kinds
of rot can be, and those are the ones that make it misleading rather than merely
incomplete:

1. it names a path that no longer exists;
2. it names a handoff or dated validation record that a newer one has superseded;
3. its reconciliation commit is far behind HEAD.

Exit 1 on the first two. The third is a warning: falling behind is expected, and
the file says so; being wrong is not.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "READING_ORDER.md"
VALIDATION = REPO / "docs" / "simulator_validation"

# Backtick-quoted repository paths: a slash plus a plausible extension or a trailing slash.
PATH_RE = re.compile(r"`([A-Za-z0-9_./-]+/[A-Za-z0-9_.-]+)`")
STAMP_RE = re.compile(r"Reconciled\s+(\d{4}-\d{2}-\d{2})\s+against\s+`([0-9a-f]{7,40})`")


def emit(line: str = "") -> None:
    print(line, flush=True)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=False
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--behind-warn",
        type=int,
        default=15,
        help="warn when the reconciliation commit is this many commits behind HEAD",
    )
    args = parser.parse_args()

    if not DOC.is_file():
        raise SystemExit(f"precondition failed: missing {DOC}")
    text = DOC.read_text(encoding="utf-8")
    emit(f"reading order   {DOC.relative_to(REPO)}  ({len(text.splitlines())} lines)")

    failures: list[str] = []

    # 1. every referenced path resolves
    referenced = sorted({m.group(1) for m in PATH_RE.finditer(text)})
    missing = [ref for ref in referenced if not (REPO / ref).exists()]
    emit(f"referenced paths {len(referenced)}, missing {len(missing)}")
    for ref in missing:
        emit(f"    MISSING  {ref}")
        failures.append(f"missing path: {ref}")

    # 2. no newer dated validation record than the newest one it names
    named = {
        Path(ref).name
        for ref in referenced
        if ref.startswith("docs/simulator_validation/")
    }
    dated = sorted(
        path.name
        for path in VALIDATION.glob("*.md")
        if re.search(r"\d{4}-\d{2}-\d{2}", path.name)
    )
    if dated:
        newest = max(dated, key=lambda name: re.search(r"\d{4}-\d{2}-\d{2}", name).group(0))
        emit(f"newest dated validation record  {newest}")
        if newest not in named:
            emit(f"    NOT NAMED  {newest}")
            failures.append(
                f"newest dated validation record is not in the reading order: {newest}"
            )

    # 3. reconciliation stamp versus HEAD
    stamp = STAMP_RE.search(text)
    if stamp is None:
        failures.append("no 'Reconciled <date> against `<commit>`' stamp")
        emit("    NO STAMP")
    else:
        date, commit = stamp.group(1), stamp.group(2)
        head = git("rev-parse", "--short", "HEAD")
        behind = git("rev-list", "--count", f"{commit}..HEAD")
        emit(f"reconciled      {date} at {commit}; HEAD {head}; {behind or '?'} commits since")
        if behind.isdigit() and int(behind) >= args.behind_warn:
            emit(f"    WARN  {behind} commits since reconciliation (>= {args.behind_warn})")

    emit()
    if failures:
        emit("DRIFT")
        for item in failures:
            emit(f"  - {item}")
        return 1
    emit("OK — every referenced path resolves and the newest dated record is named")
    return 0


if __name__ == "__main__":
    sys.exit(main())

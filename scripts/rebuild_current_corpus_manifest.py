#!/usr/bin/env python3
"""Rebuild docs/papers/CURRENT_CORPUS.toml from the notes that pass the audit.

The manifest is what ``literature_rag.py query`` and ``literature_kg.py`` read.
A note that passes ``audit`` but is absent from the manifest is invisible to both
-- valid work that answers no query. That is the failure this script closes: it
regenerates the manifest as exactly the audited-valid set, so the corpus a reader
retrieves from and the corpus that survives validation are the same object.

It admits nothing new. A note that fails the audit stays out; this only stops
already-valid notes from being orphaned.

Preconditions
-------------
* ``tools/literature_rag.py audit`` runs clean.
* The manifest exists and parses at the current schema.

Run with ``--check`` to report drift without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tomllib

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "docs" / "papers" / "CURRENT_CORPUS.toml"

sys.path.insert(0, str(REPO / "tools"))


def emit(line: str = "") -> None:
    print(line, flush=True)


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render(manifest: dict, entries: list[dict], corpus_sha: str, facts: int) -> str:
    lines = [
        f'schema = "{toml_escape(str(manifest["schema"]))}"',
        f'status = "{toml_escape(str(manifest["status"]))}"',
        f'corpus_sha256 = "{corpus_sha}"',
        f"note_count = {len(entries)}",
        f"paper_fact_count = {facts}",
        "",
    ]
    for entry in entries:
        lines.append("[[notes]]")
        for key in (
            "path",
            "note_sha256",
            "source_id",
            "source_version",
            "source_sha256",
        ):
            lines.append(f'{key} = "{toml_escape(str(entry[key]))}"')
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report orphaned or stale entries without writing the manifest",
    )
    args = parser.parse_args()

    if not MANIFEST.is_file():
        raise SystemExit(f"precondition failed: missing manifest {MANIFEST}")

    from literature_schema import (  # noqa: PLC0415 - path set above
        audit_corpus,
        corpus_identity_sha256,
    )

    manifest = tomllib.loads(MANIFEST.read_bytes().decode("utf-8"))
    before = [dict(note) for note in manifest.get("notes", [])]
    before_paths = {str(note["path"]) for note in before}

    report = audit_corpus(REPO / "docs" / "papers" / "reading_notes", REPO)
    validated = sorted(
        (dict(item) for item in report["validated"]),
        key=lambda item: str(item["path"]),
    )
    valid_paths = {str(item["path"]) for item in validated}

    orphaned = sorted(valid_paths - before_paths)
    stale = sorted(before_paths - valid_paths)

    emit(f"manifest        {MANIFEST.relative_to(REPO)}")
    emit(f"candidates      {report['excluded_count'] + len(validated)}")
    emit(f"audit-valid     {len(validated)}")
    emit(f"in manifest     {len(before)}")
    emit()
    emit(f"orphaned (valid, not retrievable)  {len(orphaned)}")
    for path in orphaned:
        emit(f"    + {path}")
    emit(f"stale (in manifest, not valid)     {len(stale)}")
    for path in stale:
        emit(f"    - {path}")
    emit()

    facts = sum(int(item["paper_fact_count"]) for item in validated)
    identities = [
        {key: item[key] for key in
         ("path", "note_sha256", "source_id", "source_version", "source_sha256")}
        for item in validated
    ]
    corpus_sha = corpus_identity_sha256(identities)

    if args.check:
        drifted = bool(orphaned or stale)
        emit("DRIFT" if drifted else "OK — manifest equals the audited-valid set")
        return 1 if drifted else 0

    if not orphaned and not stale:
        emit("no change: manifest already equals the audited-valid set")
        return 0

    MANIFEST.write_text(render(manifest, validated, corpus_sha, facts), encoding="utf-8")
    emit(f"wrote {len(validated)} notes, {facts} paper_facts, corpus_sha256 {corpus_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

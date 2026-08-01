#!/usr/bin/env python3
"""Rebuild docs/papers/CURRENT_CORPUS.toml from the notes that pass the audit.

The manifest is what ``literature_rag.py query`` and ``literature_kg.py`` read.
A note that passes ``audit`` but is absent from the manifest is invisible to both
-- valid work that answers no query. That is the failure this script closes: it
regenerates the manifest as exactly the audited-valid set, so the corpus a reader
retrieves from and the corpus that survives validation are the same object.

It admits nothing new. A note that fails the audit stays out; this only stops
already-valid notes from being orphaned, and already-admitted notes from being
recorded at a stale identity.

Drift is compared on the whole note identity -- ``path``, ``note_sha256``,
``source_id``, ``source_version``, ``source_sha256`` -- and on the manifest header
it implies, not on the path set alone. An admitted note amended in place keeps its
path and changes its ``note_sha256``, so a path-set comparison reports OK while
``literature_rag.py query`` and ``literature_kg.py stats`` fail closed with an
identity mismatch against the manifest they read.

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

# The fields that bind one manifest row to one note on disk. This is the same tuple
# ``literature_schema.note_identity`` returns and ``load_current_corpus`` enforces.
IDENTITY_KEYS = ("path", "note_sha256", "source_id", "source_version", "source_sha256")

sys.path.insert(0, str(REPO / "tools"))


def emit(line: str = "") -> None:
    print(line, flush=True)


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def identity(entry: dict) -> dict[str, str]:
    """Return *entry* reduced to its identity fields, as strings.

    A manifest row missing a field reads as empty rather than raising: the file is
    untrusted input here, and an incomplete row must surface as drift the write path
    repairs, not as a traceback.
    """

    return {key: str(entry.get(key, "")) for key in IDENTITY_KEYS}


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
        for key in IDENTITY_KEYS:
            lines.append(f'{key} = "{toml_escape(str(entry[key]))}"')
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report orphaned, stale, or amended entries without writing the manifest",
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
    before_by_path = {row["path"]: row for row in (identity(note) for note in before)}

    report = audit_corpus(REPO / "docs" / "papers" / "reading_notes", REPO)
    validated = sorted(
        (dict(item) for item in report["validated"]),
        key=lambda item: str(item["path"]),
    )
    identities = [identity(item) for item in validated]
    valid_by_path = {row["path"]: row for row in identities}

    facts = sum(int(item["paper_fact_count"]) for item in validated)
    corpus_sha = corpus_identity_sha256(identities)

    orphaned = sorted(valid_by_path.keys() - before_by_path.keys())
    stale = sorted(before_by_path.keys() - valid_by_path.keys())
    amended = sorted(
        path
        for path in before_by_path.keys() & valid_by_path.keys()
        if before_by_path[path] != valid_by_path[path]
    )
    # A repeated path collapses in the mapping above, so it can never show up as an
    # identity difference; count it directly or a duplicated row is never repaired.
    duplicated = len(before) - len(before_by_path)
    header = {
        "corpus_sha256": (str(manifest.get("corpus_sha256", "")), corpus_sha),
        "note_count": (manifest.get("note_count"), len(validated)),
        "paper_fact_count": (manifest.get("paper_fact_count"), facts),
    }
    header_drift = sorted(key for key, (recorded, actual) in header.items() if recorded != actual)

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
    emit(f"amended (admitted, recorded stale) {len(amended)}")
    for path in amended:
        changed = ", ".join(
            key for key in IDENTITY_KEYS if before_by_path[path][key] != valid_by_path[path][key]
        )
        emit(f"    ~ {path}  [{changed}]")
    emit(f"duplicate manifest rows            {duplicated}")
    emit(f"stale header fields                {len(header_drift)}")
    for key in header_drift:
        recorded, actual = header[key]
        emit(f"    ! {key}  recorded {recorded!r}, actual {actual!r}")
    emit()

    drifted = bool(orphaned or stale or amended or duplicated or header_drift)

    if args.check:
        emit("DRIFT" if drifted else "OK — manifest equals the audited-valid set")
        return 1 if drifted else 0

    if not drifted:
        emit("no change: manifest already equals the audited-valid set")
        return 0

    MANIFEST.write_text(render(manifest, validated, corpus_sha, facts), encoding="utf-8")
    emit(f"wrote {len(validated)} notes, {facts} paper_facts, corpus_sha256 {corpus_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

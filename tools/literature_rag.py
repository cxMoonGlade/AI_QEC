"""Paper-fact-only local retrieval over the explicit current corpus manifest."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.literature_schema import (  # noqa: E402
    RAG_SCHEMA,
    LiteratureNote,
    LiteratureSchemaError,
    audit_corpus,
    corpus_identity_sha256,
    corpus_sha256,
    load_current_corpus,
    note_identity,
    paper_fact_count,
    write_json_atomic,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTES_DIR = REPO_ROOT / "docs" / "papers" / "reading_notes"
DEFAULT_MANIFEST = REPO_ROOT / "docs" / "papers" / "CURRENT_CORPUS.toml"
DEFAULT_INDEX = REPO_ROOT / "outputs" / "literature" / "rag_index.json"
_TOKEN_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
_SCIENCE_SYMBOLS = frozenset({"c", "g", "k", "m", "r", "t"})
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "with",
    }
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSPECIFIED_LOCATOR_RE = re.compile(r"\b(?:unknown|n/?a|none|tbd|somewhere)\b", re.IGNORECASE)
_FACT_BODY_RE = re.compile(
    r"\AFact ID:\s*([a-z][a-z0-9_.-]*)\s*\n"
    r"Source locator:\s*(\S.*)\s*\n"
    r"PDF page:\s*([1-9]\d*)\s*\n"
    r"Claim:\s*(\S.*?)(?:\n\n|\Z)",
    re.DOTALL,
)
_INDEX_KEYS = frozenset(
    {
        "schema",
        "corpus_status",
        "corpus_sha256",
        "note_count",
        "paper_fact_count",
        "chunk_count",
        "epistemic_classes",
        "notes",
        "chunks",
    }
)
_IDENTITY_KEYS = frozenset(
    {"path", "note_sha256", "source_id", "source_version", "source_sha256"}
)
_CHUNK_KEYS = frozenset(
    {
        "id",
        "epistemic_class",
        "note_path",
        "note_sha256",
        "source_id",
        "source_version",
        "source_uri",
        "source_artifact",
        "source_sha256",
        "fact_id",
        "section_sha256",
        "chunk_sha256",
        "title",
        "section",
        "source_locator",
        "pdf_page",
        "claim",
        "text",
        "term_frequencies",
    }
)


def tokenize(text: str) -> tuple[str, ...]:
    """Normalize lexical search tokens, retaining controlled scientific symbols.

    Hyphenated terms are indexed both as compounds and components, so
    ``non-Markovian`` and ``non Markovian`` share tokens.
    """

    tokens: list[str] = []
    for match in _TOKEN_RE.finditer(text):
        compound = match.group(0).casefold()
        candidates = (compound, *re.split(r"[-']", compound))
        for token in candidates:
            if not token or token in _STOPWORDS:
                continue
            if len(token) > 1 or token in _SCIENCE_SYMBOLS:
                tokens.append(token)
    return tuple(tokens)


def _chunk_search_text(chunk: dict[str, Any]) -> str:
    return f"{chunk['title']}\n{chunk['section']}\n{chunk['text']}"


def _chunk_sha256(title: str, section: str, text: str) -> str:
    return hashlib.sha256(f"{title}\n{section}\n{text}".encode("utf-8")).hexdigest()


def _chunk_id(
    note_sha256: str,
    fact_id: str,
    source_locator: str,
    pdf_page: int,
    section_sha256: str,
    chunk_sha256: str,
) -> str:
    return hashlib.sha256(
        "\0".join(
            (
                note_sha256,
                fact_id,
                source_locator,
                str(pdf_page),
                section_sha256,
                chunk_sha256,
            )
        ).encode("utf-8")
    ).hexdigest()[:24]


def build_index(notes: Sequence[LiteratureNote]) -> dict[str, Any]:
    """Build a deterministic, one-fact-per-chunk index."""

    chunks: list[dict[str, Any]] = []
    for note in sorted(notes, key=lambda item: item.relative_path):
        for section in note.sections:
            if section.epistemic_class != "paper_fact":
                continue
            text = section.body
            section_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            chunk_sha256 = _chunk_sha256(note.title, section.title, text)
            chunk: dict[str, Any] = {
                "id": _chunk_id(
                    note.note_sha256,
                    section.fact_id,
                    section.source_locator,
                    section.pdf_page,
                    section_sha256,
                    chunk_sha256,
                ),
                "epistemic_class": "paper_fact",
                "note_path": note.relative_path,
                "note_sha256": note.note_sha256,
                "source_id": note.source_id,
                "source_version": note.source_version,
                "source_uri": note.source_uri,
                "source_artifact": note.source_artifact,
                "source_sha256": note.source_sha256,
                "fact_id": section.fact_id,
                "section_sha256": section_sha256,
                "chunk_sha256": chunk_sha256,
                "title": note.title,
                "section": section.title,
                "source_locator": section.source_locator,
                "pdf_page": section.pdf_page,
                "claim": section.claim,
                "text": text,
            }
            chunk["term_frequencies"] = dict(sorted(Counter(tokenize(_chunk_search_text(chunk))).items()))
            chunks.append(chunk)
    identities = [note_identity(note) for note in sorted(notes, key=lambda item: item.relative_path)]
    status = "active" if identities else "bootstrap_empty"
    return {
        "schema": RAG_SCHEMA,
        "corpus_status": status,
        "corpus_sha256": corpus_sha256(notes),
        "note_count": len(identities),
        "paper_fact_count": paper_fact_count(notes),
        "chunk_count": len(chunks),
        "epistemic_classes": ["paper_fact"],
        "notes": identities,
        "chunks": chunks,
    }


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], context: str) -> None:
    if set(value) != expected:
        raise ValueError(
            f"{context} fields differ: missing={sorted(expected - set(value))}, "
            f"extra={sorted(set(value) - expected)}"
        )


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and _HASH_RE.fullmatch(value) is not None


def validate_index(
    index: dict[str, Any], *, live_notes: Sequence[LiteratureNote] | None = None
) -> None:
    """Reject mixed, malformed, internally inconsistent, or stale indexes."""

    if not isinstance(index, dict):
        raise ValueError("RAG index must be an object")
    _require_exact_keys(index, _INDEX_KEYS, "RAG index")
    if index["schema"] != RAG_SCHEMA:
        raise ValueError(f"unsupported RAG schema {index['schema']!r}")
    if index["corpus_status"] not in {"active", "bootstrap_empty"}:
        raise ValueError("RAG index has invalid corpus_status")
    if index["epistemic_classes"] != ["paper_fact"]:
        raise ValueError("RAG index must declare paper_fact as its only epistemic class")
    identities = index["notes"]
    chunks = index["chunks"]
    if not isinstance(identities, list) or not isinstance(chunks, list):
        raise ValueError("RAG notes and chunks must be lists")
    seen_paths: set[str] = set()
    seen_sources: set[str] = set()
    identity_by_path: dict[str, dict[str, Any]] = {}
    for identity in identities:
        if not isinstance(identity, dict):
            raise ValueError("RAG note identity must be an object")
        _require_exact_keys(identity, _IDENTITY_KEYS, "RAG note identity")
        if not all(isinstance(identity[key], str) and identity[key] for key in _IDENTITY_KEYS):
            raise ValueError("RAG note identity fields must be non-empty strings")
        if not _valid_hash(identity["note_sha256"]) or not _valid_hash(identity["source_sha256"]):
            raise ValueError("RAG note identity has an invalid hash")
        if identity["path"] in seen_paths or identity["source_id"] in seen_sources:
            raise ValueError("RAG note paths and source IDs must be unique")
        seen_paths.add(identity["path"])
        seen_sources.add(identity["source_id"])
        identity_by_path[identity["path"]] = identity
    if index["note_count"] != len(identities):
        raise ValueError("RAG note_count mismatch")
    if index["chunk_count"] != len(chunks) or index["paper_fact_count"] != len(chunks):
        raise ValueError("RAG fact/chunk count mismatch")
    if index["corpus_sha256"] != corpus_identity_sha256(identities):
        raise ValueError("RAG corpus_sha256 mismatch")
    if index["corpus_status"] == "active" and not identities:
        raise ValueError("active RAG corpus cannot be empty")
    if index["corpus_status"] == "bootstrap_empty" and (identities or chunks):
        raise ValueError("bootstrap-empty RAG artifact cannot contain notes or chunks")

    seen_ids: set[str] = set()
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError("RAG chunk must be an object")
        _require_exact_keys(chunk, _CHUNK_KEYS, "RAG chunk")
        if chunk["epistemic_class"] != "paper_fact":
            raise ValueError("RAG index contains a non-paper_fact chunk")
        identity = identity_by_path.get(chunk["note_path"])
        if identity is None:
            raise ValueError("RAG chunk references an undeclared note")
        for key in ("note_sha256", "source_id", "source_version", "source_sha256"):
            identity_key = "path" if key == "note_path" else key
            if chunk[key] != identity[identity_key]:
                raise ValueError(f"RAG chunk {key} disagrees with note identity")
        for key in ("note_sha256", "source_sha256", "section_sha256", "chunk_sha256"):
            if not _valid_hash(chunk[key]):
                raise ValueError(f"RAG chunk has an invalid {key}")
        for key in (
            "id",
            "source_uri",
            "source_artifact",
            "fact_id",
            "title",
            "section",
            "source_locator",
            "claim",
            "text",
        ):
            if not isinstance(chunk[key], str) or not chunk[key].strip():
                raise ValueError(f"RAG chunk lacks {key}")
        if _UNSPECIFIED_LOCATOR_RE.search(chunk["source_locator"]):
            raise ValueError("RAG chunk has an inexact source locator")
        if not isinstance(chunk["pdf_page"], int) or isinstance(chunk["pdf_page"], bool) or chunk["pdf_page"] <= 0:
            raise ValueError("RAG chunk has an invalid PDF page")
        fact_header = _FACT_BODY_RE.match(chunk["text"])
        if fact_header is None:
            raise ValueError("RAG chunk text lacks its structured fact header")
        fact_id, locator, page, claim = fact_header.groups()
        if (
            chunk["fact_id"] != fact_id.strip()
            or chunk["source_locator"] != locator.strip()
            or chunk["pdf_page"] != int(page)
            or chunk["claim"] != " ".join(claim.split())
        ):
            raise ValueError("RAG chunk provenance disagrees with its fact text")
        section_sha = hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
        if chunk["section_sha256"] != section_sha:
            raise ValueError("RAG section_sha256 mismatch")
        chunk_sha = _chunk_sha256(chunk["title"], chunk["section"], chunk["text"])
        if chunk["chunk_sha256"] != chunk_sha:
            raise ValueError("RAG chunk_sha256 mismatch")
        if chunk["id"] != _chunk_id(
            chunk["note_sha256"],
            chunk["fact_id"],
            chunk["source_locator"],
            chunk["pdf_page"],
            section_sha,
            chunk_sha,
        ):
            raise ValueError("RAG chunk ID mismatch")
        if chunk["id"] in seen_ids:
            raise ValueError("duplicate RAG chunk ID")
        seen_ids.add(chunk["id"])
        expected_terms = dict(sorted(Counter(tokenize(_chunk_search_text(chunk))).items()))
        if chunk["term_frequencies"] != expected_terms:
            raise ValueError("RAG term frequencies mismatch")
    if live_notes is not None and index != build_index(live_notes):
        raise ValueError("RAG artifact does not match the live current corpus")


def query_index(index: dict[str, Any], query: str, *, top_k: int = 12) -> list[dict[str, Any]]:
    """Return deterministic TF-IDF hits from a validated active index."""

    validate_index(index)
    if index["corpus_status"] != "active":
        raise ValueError("current literature corpus is bootstrap-empty, so it cannot be queried")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    query_terms = Counter(tokenize(query))
    if not query_terms:
        return []
    chunks = index["chunks"]
    document_count = len(chunks)
    document_frequency: Counter[str] = Counter()
    for chunk in chunks:
        document_frequency.update(chunk["term_frequencies"].keys())

    scored: list[tuple[float, dict[str, Any]]] = []
    for chunk in chunks:
        frequencies = chunk["term_frequencies"]
        score = 0.0
        for term, query_count in query_terms.items():
            frequency = int(frequencies.get(term, 0))
            if frequency == 0:
                continue
            inverse = math.log((document_count + 1) / (document_frequency[term] + 1)) + 1.0
            score += query_count * (1.0 + math.log(frequency)) * inverse
        if score > 0.0:
            hit = {key: value for key, value in chunk.items() if key != "term_frequencies"}
            hit["score"] = score
            scored.append((score, hit))
    scored.sort(key=lambda item: (-item[0], item[1]["source_id"], item[1]["fact_id"]))
    return [hit for _, hit in scored[:top_k]]


def _resolve(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="classify candidate notes")
    audit.add_argument("--notes-dir", type=Path, default=Path("docs/papers/reading_notes"))
    audit.add_argument("--schema-only", action="store_true")
    audit.add_argument("--strict", action="store_true")
    audit.add_argument("--output", type=Path)

    build = subparsers.add_parser("build", help="write an artifact-verified fact index")
    build.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    build.add_argument("--output", type=Path, default=DEFAULT_INDEX)
    build.add_argument("--allow-empty", action="store_true", help="write the explicit reset artifact")

    query = subparsers.add_parser("query", help="query the live artifact-verified corpus")
    query.add_argument("query")
    query.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    query.add_argument("--top-k", type=int, default=12)
    query.add_argument("--json", action="store_true")

    validate = subparsers.add_parser("validate", help="validate an index against the live corpus")
    validate.add_argument("artifact", type=Path, nargs="?", default=DEFAULT_INDEX)
    validate.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    validate.add_argument("--allow-empty", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        args.repo_root = args.repo_root.resolve()
        if args.command == "audit":
            notes_dir = _resolve(args.notes_dir, args.repo_root)
            payload = audit_corpus(notes_dir, args.repo_root, schema_only=args.schema_only)
            if args.output is not None:
                output = _resolve(args.output, args.repo_root)
                write_json_atomic(output, payload)
                print(
                    f"wrote corpus audit to {output}: {payload['validated_count']} validated, "
                    f"{payload['excluded_count']} excluded ({payload['verification_mode']})"
                )
            else:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 1 if args.strict and payload["excluded_count"] else 0

        manifest = _resolve(args.manifest, args.repo_root)
        allow_empty = bool(getattr(args, "allow_empty", False))
        notes = load_current_corpus(manifest, args.repo_root, allow_empty=allow_empty)
        live_index = build_index(notes)
        if args.command == "build":
            output = _resolve(args.output, args.repo_root)
            validate_index(live_index, live_notes=notes)
            write_json_atomic(output, live_index)
            print(
                f"wrote {live_index['chunk_count']} paper_fact chunks from "
                f"{live_index['note_count']} current notes to {output}"
            )
            return 0
        if args.command == "validate":
            artifact = _resolve(args.artifact, args.repo_root)
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            validate_index(payload, live_notes=notes)
            print(f"validated RAG artifact against live corpus: {artifact}")
            return 0
        hits = query_index(live_index, args.query, top_k=args.top_k)
        if args.json:
            print(json.dumps(hits, ensure_ascii=False, indent=2, sort_keys=True))
        elif not hits:
            print("No current paper_fact records matched.")
        else:
            for number, hit in enumerate(hits, start=1):
                print(f"[{number}] {hit['title']} — {hit['section']} (score={hit['score']:.3f})")
                print(f"    note: {hit['note_path']}")
                print(f"    source: {hit['source_id']} {hit['source_version']} — {hit['source_uri']}")
                print(f"    locator: {hit['source_locator']}; PDF page {hit['pdf_page']}")
                print(f"    {' '.join(hit['claim'].split())[:500]}")
        return 0
    except (LiteratureSchemaError, ValueError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

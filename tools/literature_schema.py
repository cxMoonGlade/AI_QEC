"""Fail-closed provenance contracts shared by the local literature tools.

The active corpus is an explicit manifest.  Files merely present in the
candidate directory are never admitted implicitly, and every admitted note is
reopened together with its source PDF and separate review packet.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import tomllib
from typing import Any, Iterable
from urllib.parse import urlparse


NOTE_SCHEMA = "error_coupling_simulator.literature.note.v1"
CORPUS_MANIFEST_SCHEMA = "error_coupling_simulator.literature.corpus_manifest.v1"
RAG_SCHEMA = "error_coupling_simulator.literature.rag_index.v1"
KG_SCHEMA = "error_coupling_simulator.literature.knowledge_graph.v1"
CORPUS_AUDIT_SCHEMA = "error_coupling_simulator.literature.corpus_audit.v1"

SECTION_CLASSES = frozenset({"paper_fact", "literature_gap"})
OBJECT_TYPES = frozenset(
    {"concept", "limitation", "method", "model", "observable", "theorem"}
)
RELATION_TYPES = frozenset(
    {"contradicts", "defines", "derives", "limits", "measures", "supports", "uses"}
)
PUBLICATION_STATUSES = frozenset({"accepted", "preprint", "published", "technical_report"})

_NOTE_KEYS = frozenset(
    {
        "schema",
        "source_id",
        "source_version",
        "source_uri",
        "source_artifact",
        "source_sha256",
        "title",
        "publication_status",
        "read_status",
        "evidence_status",
        "review_scope",
        "operation_replay_status",
        "audit_packet",
        "audit_packet_sha256",
        "admission_status",
        "admission_reviewer",
        "admission_date",
        "visually_checked_pages",
        "relations",
    }
)
_RELATION_KEYS = frozenset(
    {"predicate", "object_id", "object_type", "object_label", "fact_id"}
)
_MANIFEST_KEYS = frozenset(
    {"schema", "status", "corpus_sha256", "note_count", "paper_fact_count", "notes"}
)
_MANIFEST_NOTE_KEYS = frozenset(
    {"path", "note_sha256", "source_id", "source_version", "source_sha256"}
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OBJECT_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
_ARXIV_ID_RE = re.compile(
    r"^arxiv:(\d{4}\.\d{4,5}|[a-z]+(?:-[a-z]+)*/\d{7})$"
)
_ARXIV_VERSION_RE = re.compile(r"^v[1-9]\d*$")
_DOI_ID_RE = re.compile(r"^doi:(10\.\d{4,9}/\S+)$", re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SECTION_RE = re.compile(
    r"^##\s+(.+?)\s+\[(paper_fact|literature_gap)\]\s*$", re.MULTILINE
)
_ANY_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_H1_RE = re.compile(r"^#\s+\S.*$", re.MULTILINE)
_FACT_HEADER_RE = re.compile(
    r"\AFact ID:\s*([a-z][a-z0-9_.-]*)\s*\n"
    r"Source locator:\s*(\S.*)\s*\n"
    r"PDF page:\s*([1-9]\d*)\s*\n"
    r"Claim:\s*(\S.*?)(?:\n\n|\Z)",
    re.DOTALL,
)
_GAP_SCOPE_RE = re.compile(r"(?:\A|\n)Gap scope:\s*source_local\s*(?:\n|\Z)")
_LOCATOR_ANCHOR_RE = re.compile(
    r"\b(?:Eq(?:uation)?s?|Thm|Theorem|Proposition|Lemma|Corollary|"
    r"Fig(?:ure)?s?|Table|Appendix|App|Sec(?:tion)?s?|Algorithm|Alg|"
    r"page|pages|p|paragraph|lines?)\.?\s*[A-Za-z0-9(]",
    re.IGNORECASE,
)
_UNSPECIFIED_RE = re.compile(r"\b(?:unknown|n/?a|none|tbd|somewhere)\b", re.IGNORECASE)
_OBSOLETE_NAMESPACE_PARTS = ("qec", "twin")
_OBSOLETE_ROLE_WORDS = ("".join(("teach", "er")), "".join(("learn", "er")))
_OBSOLETE_API_WORDS = (
    "Mechanism" + "Spec",
    "mechanism_" + "channel",
    "CoupledCycle" + _OBSOLETE_ROLE_WORDS[0].title(),
    "QutritLeakage" + _OBSOLETE_ROLE_WORDS[0].title(),
    "certify_" + _OBSOLETE_ROLE_WORDS[0],
    "Shot" + "Set",
)
_INTERNAL_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "obsolete product namespace",
        re.compile(
            rf"\b{_OBSOLETE_NAMESPACE_PARTS[0]}[_ -]?{_OBSOLETE_NAMESPACE_PARTS[1]}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "current project namespace in source-only prose",
        re.compile(r"\berror_coupling_simulator\b", re.IGNORECASE),
    ),
    ("retired mechanism ID", re.compile(r"(?<![A-Za-z0-9])M(?:[0-9]|[12]\d|3[0-4])(?![A-Za-z0-9])")),
    (
        "obsolete environment namespace",
        re.compile(rf"\b{'_'.join(('QEC', 'TWIN'))}_[A-Z0-9_]*\b"),
    ),
    (
        "obsolete role vocabulary",
        re.compile(
            rf"\b(?:{'|'.join(re.escape(item) for item in _OBSOLETE_ROLE_WORDS)})\b",
            re.IGNORECASE,
        ),
    ),
    ("retired path", re.compile(r"\b(?:retired|legacy)/", re.IGNORECASE)),
    ("retired ADR", re.compile(r"\b(?:docs/adr/)?000[2-7]\b", re.IGNORECASE)),
    ("project inference tag", re.compile(r"\[(?:ours|twin)\]|ours-inference", re.IGNORECASE)),
    (
        "project application prose",
        re.compile(
            r"\b(?:our simulator|our project|project (?:mapping|application|decision|inference)|"
            r"implementation decision|relevance to (?:the )?(?:simulator|project))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "obsolete API vocabulary",
        re.compile(
            rf"\b(?:{'|'.join(re.escape(item) for item in _OBSOLETE_API_WORDS)})\b",
            re.IGNORECASE,
        ),
    ),
)


class LiteratureSchemaError(ValueError):
    """A note, manifest, or generated literature artifact violates the contract."""


@dataclass(frozen=True)
class NoteSection:
    """One source-located evidence record from a note."""

    title: str
    epistemic_class: str
    fact_id: str
    source_locator: str
    pdf_page: int
    claim: str
    body: str
    line: int


@dataclass(frozen=True)
class NoteRelation:
    """A paper-fact-to-concept relationship resolved through a fact ID."""

    predicate: str
    object_id: str
    object_type: str
    object_label: str
    fact_id: str
    section: str
    source_locator: str
    pdf_page: int
    claim: str


@dataclass(frozen=True)
class LiteratureNote:
    """Validated full-text reading note."""

    path: Path
    relative_path: str
    note_sha256: str
    source_id: str
    source_version: str
    source_uri: str
    source_artifact: str
    source_sha256: str
    title: str
    publication_status: str
    read_status: str
    evidence_status: str
    audit_packet: str
    audit_packet_sha256: str
    admission_reviewer: str
    admission_date: str
    visually_checked_pages: tuple[int, ...]
    sections: tuple[NoteSection, ...]
    relations: tuple[NoteRelation, ...]


def sha256_file(path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of *path*."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _required_string(metadata: dict[str, Any], key: str, path: Path) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LiteratureSchemaError(f"{path}: metadata {key!r} must be a non-empty string")
    return value.strip()


def _reject_unknown_keys(
    mapping: dict[str, Any], allowed: frozenset[str], path: Path, context: str
) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise LiteratureSchemaError(f"{path}: unknown {context} keys: {', '.join(unknown)}")


def _parse_front_matter(text: str, path: Path) -> tuple[dict[str, Any], str, int]:
    if not text.startswith("+++\n"):
        raise LiteratureSchemaError(f"{path}: missing current TOML front matter")
    end = text.find("\n+++\n", 4)
    if end < 0:
        raise LiteratureSchemaError(f"{path}: unterminated TOML front matter")
    raw = text[4:end]
    try:
        metadata = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        raise LiteratureSchemaError(f"{path}: invalid TOML front matter: {exc}") from exc
    return metadata, text[end + 5 :], raw.count("\n") + 3


def _internal_marker(value: str) -> str | None:
    for label, pattern in _INTERNAL_MARKERS:
        if pattern.search(value):
            return label
    return None


def _require_source_only(value: str, path: Path, context: str) -> None:
    marker = _internal_marker(value)
    if marker is not None:
        raise LiteratureSchemaError(f"{path}: {context} contains {marker}")


def _valid_locator(locator: str) -> bool:
    return not _UNSPECIFIED_RE.search(locator) and _LOCATOR_ANCHOR_RE.search(locator) is not None


def _parse_sections(
    body: str,
    path: Path,
    body_line_offset: int,
    visually_checked_pages: frozenset[int],
) -> tuple[NoteSection, ...]:
    matches = list(_SECTION_RE.finditer(body))
    all_h2 = list(_ANY_H2_RE.finditer(body))
    classified_starts = {match.start() for match in matches}
    unclassified = [match.group(1) for match in all_h2 if match.start() not in classified_starts]
    if unclassified:
        raise LiteratureSchemaError(
            f"{path}: every level-two section needs [paper_fact] or [literature_gap]: "
            + ", ".join(repr(item) for item in unclassified)
        )
    if not matches:
        raise LiteratureSchemaError(f"{path}: no classified level-two sections")

    preamble = body[: matches[0].start()]
    preamble_lines = [line for line in preamble.splitlines() if line.strip()]
    if len(preamble_lines) != 1 or not preamble_lines[0].startswith("# "):
        raise LiteratureSchemaError(
            f"{path}: note body must start with exactly one H1 and no unclassified prose"
        )
    if len(_H1_RE.findall(body)) != 1:
        raise LiteratureSchemaError(f"{path}: note body must contain exactly one H1")
    _require_source_only(body, path, "note body")

    sections: list[NoteSection] = []
    seen_titles: set[str] = set()
    seen_fact_ids: set[str] = set()
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        epistemic_class = match.group(2)
        if title in seen_titles:
            raise LiteratureSchemaError(f"{path}: duplicate section title {title!r}")
        seen_titles.add(title)
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        section_body = body[match.end() : stop].strip()
        header = _FACT_HEADER_RE.match(section_body)
        if header is None:
            raise LiteratureSchemaError(
                f"{path}: section {title!r} must begin with Fact ID, Source locator, "
                "PDF page, and Claim"
            )
        fact_id, locator, page_text, claim = (item.strip() for item in header.groups())
        if fact_id in seen_fact_ids:
            raise LiteratureSchemaError(f"{path}: duplicate Fact ID {fact_id!r}")
        seen_fact_ids.add(fact_id)
        if not _valid_locator(locator):
            raise LiteratureSchemaError(f"{path}: section {title!r} has an inexact source locator")
        page = int(page_text)
        if page not in visually_checked_pages:
            raise LiteratureSchemaError(
                f"{path}: section {title!r} PDF page {page} was not visually checked"
            )
        if epistemic_class == "literature_gap" and _GAP_SCOPE_RE.search(section_body) is None:
            raise LiteratureSchemaError(
                f"{path}: literature_gap section {title!r} must declare Gap scope: source_local"
            )
        line = body_line_offset + body.count("\n", 0, match.start()) + 1
        sections.append(
            NoteSection(
                title=title,
                epistemic_class=epistemic_class,
                fact_id=fact_id,
                source_locator=locator,
                pdf_page=page,
                claim=_normalized_space(claim),
                body=section_body,
                line=line,
            )
        )

    if not any(section.epistemic_class == "paper_fact" for section in sections):
        raise LiteratureSchemaError(f"{path}: note contains no paper_fact section")
    return tuple(sections)


def _normalized_space(value: str) -> str:
    return " ".join(value.split())


def _parse_relations(
    raw_relations: Any,
    sections: tuple[NoteSection, ...],
    path: Path,
) -> tuple[NoteRelation, ...]:
    if raw_relations is None:
        return ()
    if not isinstance(raw_relations, list):
        raise LiteratureSchemaError(f"{path}: [[relations]] must be an array of tables")
    section_by_fact_id = {section.fact_id: section for section in sections}
    parsed: list[NoteRelation] = []
    seen: set[tuple[str, str, str]] = set()
    for index, raw in enumerate(raw_relations):
        if not isinstance(raw, dict):
            raise LiteratureSchemaError(f"{path}: relations[{index}] must be a table")
        _reject_unknown_keys(raw, _RELATION_KEYS, path, f"relations[{index}]")
        predicate = _required_string(raw, "predicate", path)
        object_id = _required_string(raw, "object_id", path)
        object_type = _required_string(raw, "object_type", path)
        object_label = _required_string(raw, "object_label", path)
        fact_id = _required_string(raw, "fact_id", path)
        for field, value in (
            ("object_id", object_id),
            ("object_label", object_label),
            ("fact_id", fact_id),
        ):
            _require_source_only(value, path, f"relations[{index}] {field}")
        if predicate not in RELATION_TYPES:
            raise LiteratureSchemaError(
                f"{path}: relations[{index}] predicate {predicate!r} is unsupported"
            )
        if object_type not in OBJECT_TYPES:
            raise LiteratureSchemaError(
                f"{path}: relations[{index}] object_type {object_type!r} is unsupported"
            )
        if not _OBJECT_ID_RE.fullmatch(object_id):
            raise LiteratureSchemaError(
                f"{path}: relations[{index}] object_id {object_id!r} is invalid"
            )
        section = section_by_fact_id.get(fact_id)
        if section is None:
            raise LiteratureSchemaError(
                f"{path}: relations[{index}] names missing Fact ID {fact_id!r}"
            )
        if section.epistemic_class != "paper_fact":
            raise LiteratureSchemaError(
                f"{path}: relations[{index}] must point to a paper_fact"
            )
        if _normalized_space(object_label).casefold() not in section.claim.casefold():
            raise LiteratureSchemaError(
                f"{path}: relations[{index}] object_label must occur in the fact claim"
            )
        identity = (predicate, object_type, object_id)
        if identity in seen:
            raise LiteratureSchemaError(f"{path}: duplicate relation {identity!r}")
        seen.add(identity)
        parsed.append(
            NoteRelation(
                predicate=predicate,
                object_id=object_id,
                object_type=object_type,
                object_label=object_label,
                fact_id=fact_id,
                section=section.title,
                source_locator=section.source_locator,
                pdf_page=section.pdf_page,
                claim=section.claim,
            )
        )
    return tuple(parsed)


def _repo_relative_file(
    value: str,
    path: Path,
    repo_root: Path,
    field: str,
    *,
    suffix: str | None = None,
) -> tuple[str, Path]:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise LiteratureSchemaError(f"{path}: {field} must be repository-relative")
    if suffix is not None and relative.suffix.casefold() != suffix:
        raise LiteratureSchemaError(f"{path}: {field} must name a {suffix} file")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise LiteratureSchemaError(f"{path}: {field} escapes repository root") from exc
    return relative.as_posix(), resolved


def _verify_hashed_file(
    owner: Path,
    artifact_path: Path,
    artifact_label: str,
    expected_sha256: str,
) -> None:
    if not artifact_path.is_file():
        raise LiteratureSchemaError(f"{owner}: {artifact_label} is missing: {artifact_path}")
    actual = sha256_file(artifact_path)
    if actual != expected_sha256:
        raise LiteratureSchemaError(
            f"{owner}: {artifact_label} SHA-256 mismatch: expected {expected_sha256}, got {actual}"
        )


def _validate_source_identity(
    source_id: str, source_version: str, source_uri: str, path: Path
) -> None:
    parsed = urlparse(source_uri)
    if parsed.scheme != "https" or not parsed.netloc:
        raise LiteratureSchemaError(f"{path}: source_uri must be an absolute HTTPS URI")
    arxiv = _ARXIV_ID_RE.fullmatch(source_id)
    doi = _DOI_ID_RE.fullmatch(source_id)
    if arxiv is not None:
        if _ARXIV_VERSION_RE.fullmatch(source_version) is None:
            raise LiteratureSchemaError(f"{path}: arXiv source_version must be vN")
        expected = f"https://arxiv.org/abs/{arxiv.group(1)}{source_version}"
        if source_uri != expected:
            raise LiteratureSchemaError(
                f"{path}: arXiv source_uri must pin the declared version: {expected}"
            )
    elif doi is not None:
        if source_version != "version-of-record":
            raise LiteratureSchemaError(
                f"{path}: DOI source_version must be 'version-of-record'"
            )
        expected = f"https://doi.org/{doi.group(1)}"
        if source_uri.casefold() != expected.casefold():
            raise LiteratureSchemaError(f"{path}: DOI source_uri must be {expected}")
    else:
        raise LiteratureSchemaError(f"{path}: source_id must be an arxiv: or doi: identifier")


def parse_note(path: Path, repo_root: Path, *, verify_artifact: bool = True) -> LiteratureNote:
    """Parse one current-schema note; trusted callers must keep verification enabled."""

    path = path.resolve()
    repo_root = repo_root.resolve()
    try:
        relative_path = path.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise LiteratureSchemaError(f"{path}: note is outside repository root") from exc
    try:
        raw_bytes = path.read_bytes()
        text = raw_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise LiteratureSchemaError(f"{path}: cannot read UTF-8 note: {exc}") from exc

    metadata, body, body_line_offset = _parse_front_matter(text, path)
    _reject_unknown_keys(metadata, _NOTE_KEYS, path, "note metadata")
    schema = _required_string(metadata, "schema", path)
    if schema != NOTE_SCHEMA:
        raise LiteratureSchemaError(f"{path}: unsupported note schema {schema!r}")

    source_id = _required_string(metadata, "source_id", path)
    source_version = _required_string(metadata, "source_version", path)
    source_uri = _required_string(metadata, "source_uri", path)
    source_artifact_raw = _required_string(metadata, "source_artifact", path)
    source_sha256 = _required_string(metadata, "source_sha256", path)
    title = _required_string(metadata, "title", path)
    publication_status = _required_string(metadata, "publication_status", path)
    read_status = _required_string(metadata, "read_status", path)
    evidence_status = _required_string(metadata, "evidence_status", path)
    review_scope = _required_string(metadata, "review_scope", path)
    operation_replay_status = _required_string(metadata, "operation_replay_status", path)
    audit_packet_raw = _required_string(metadata, "audit_packet", path)
    audit_packet_sha256 = _required_string(metadata, "audit_packet_sha256", path)
    admission_status = _required_string(metadata, "admission_status", path)
    admission_reviewer = _required_string(metadata, "admission_reviewer", path)
    admission_date = _required_string(metadata, "admission_date", path)

    for key, value in (
        ("source_sha256", source_sha256),
        ("audit_packet_sha256", audit_packet_sha256),
    ):
        if _SHA256_RE.fullmatch(value) is None:
            raise LiteratureSchemaError(f"{path}: {key} must be 64 lowercase hex characters")
    _validate_source_identity(source_id, source_version, source_uri, path)
    if publication_status not in PUBLICATION_STATUSES:
        raise LiteratureSchemaError(f"{path}: unsupported publication_status {publication_status!r}")
    if read_status != "complete" or review_scope != "full_text":
        raise LiteratureSchemaError(f"{path}: admission requires a complete full-text review")
    if evidence_status != "persisted" or operation_replay_status != "complete":
        raise LiteratureSchemaError(f"{path}: admission requires persisted evidence and operation replay")
    if admission_status != "source_only_reviewed":
        raise LiteratureSchemaError(f"{path}: admission_status must be 'source_only_reviewed'")
    if _DATE_RE.fullmatch(admission_date) is None:
        raise LiteratureSchemaError(f"{path}: admission_date must be YYYY-MM-DD")

    checked_raw = metadata.get("visually_checked_pages")
    if (
        not isinstance(checked_raw, list)
        or not checked_raw
        or any(not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in checked_raw)
    ):
        raise LiteratureSchemaError(f"{path}: visually_checked_pages must be positive integers")
    if len(set(checked_raw)) != len(checked_raw):
        raise LiteratureSchemaError(f"{path}: visually_checked_pages contains duplicates")
    checked_pages = tuple(checked_raw)

    source_artifact, artifact_path = _repo_relative_file(
        source_artifact_raw, path, repo_root, "source_artifact", suffix=".pdf"
    )
    audit_packet, audit_path = _repo_relative_file(
        audit_packet_raw, path, repo_root, "audit_packet", suffix=".md"
    )
    if not audit_packet.startswith("docs/simulator_validation/"):
        raise LiteratureSchemaError(
            f"{path}: audit_packet must be under docs/simulator_validation"
        )
    if audit_path == path:
        raise LiteratureSchemaError(f"{path}: audit_packet must be separate from the reading note")
    if verify_artifact:
        _verify_hashed_file(path, artifact_path, "source artifact", source_sha256)
        with artifact_path.open("rb") as handle:
            signature = handle.read(5)
        if signature != b"%PDF-":
            raise LiteratureSchemaError(f"{path}: source_artifact is not a PDF byte stream")
        _verify_hashed_file(path, audit_path, "audit packet", audit_packet_sha256)

    sections = _parse_sections(body, path, body_line_offset, frozenset(checked_pages))
    relations = _parse_relations(metadata.get("relations"), sections, path)
    return LiteratureNote(
        path=path,
        relative_path=relative_path,
        note_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        source_id=source_id,
        source_version=source_version,
        source_uri=source_uri,
        source_artifact=source_artifact,
        source_sha256=source_sha256,
        title=title,
        publication_status=publication_status,
        read_status=read_status,
        evidence_status=evidence_status,
        audit_packet=audit_packet,
        audit_packet_sha256=audit_packet_sha256,
        admission_reviewer=admission_reviewer,
        admission_date=admission_date,
        visually_checked_pages=checked_pages,
        sections=sections,
        relations=relations,
    )


def note_candidates(notes_dir: Path) -> tuple[Path, ...]:
    """Return candidate Markdown files, excluding the routing README."""

    if not notes_dir.is_dir():
        raise LiteratureSchemaError(f"candidate notes directory is missing: {notes_dir}")
    return tuple(
        path for path in sorted(notes_dir.glob("*.md")) if path.name.casefold() != "readme.md"
    )


def audit_corpus(
    notes_dir: Path,
    repo_root: Path,
    *,
    schema_only: bool = False,
) -> dict[str, Any]:
    """Classify candidates; schema-only mode is diagnostic and never means admitted."""

    validated: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for path in note_candidates(notes_dir):
        try:
            note = parse_note(path, repo_root, verify_artifact=not schema_only)
        except LiteratureSchemaError as exc:
            try:
                relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                relative = str(path)
            reason = str(exc).replace(str(repo_root.resolve()) + "/", "")
            excluded.append({"path": relative, "reason": reason})
            continue
        validated.append(note_identity(note) | {"paper_fact_count": paper_fact_count((note,))})
    return {
        "schema": CORPUS_AUDIT_SCHEMA,
        "verification_mode": "schema_only" if schema_only else "artifact_verified",
        "notes_dir": notes_dir.resolve().relative_to(repo_root.resolve()).as_posix(),
        "candidate_count": len(validated) + len(excluded),
        "validated_count": len(validated),
        "excluded_count": len(excluded),
        "validated": validated,
        "excluded": excluded,
    }


def note_identity(note: LiteratureNote) -> dict[str, Any]:
    """Return the fields that bind a generated artifact to one admitted note."""

    return {
        "path": note.relative_path,
        "note_sha256": note.note_sha256,
        "source_id": note.source_id,
        "source_version": note.source_version,
        "source_sha256": note.source_sha256,
    }


def paper_fact_count(notes: Iterable[LiteratureNote]) -> int:
    """Count independently located paper facts in *notes*."""

    return sum(
        section.epistemic_class == "paper_fact" for note in notes for section in note.sections
    )


def corpus_sha256(notes: Iterable[LiteratureNote]) -> str:
    """Hash the ordered manifest identity of a validated corpus."""

    return corpus_identity_sha256(note_identity(note) for note in notes)


def corpus_identity_sha256(identities: Iterable[dict[str, Any]]) -> str:
    """Hash canonical note identities without reopening files."""

    digest = hashlib.sha256()
    for identity in sorted(identities, key=lambda item: str(item["path"])):
        for key in ("path", "note_sha256", "source_id", "source_version", "source_sha256"):
            digest.update(str(identity[key]).encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def load_current_corpus(
    manifest_path: Path,
    repo_root: Path,
    *,
    allow_empty: bool = False,
) -> tuple[LiteratureNote, ...]:
    """Load exactly the artifact-verified notes named by the current manifest."""

    manifest_path = manifest_path.resolve()
    repo_root = repo_root.resolve()
    if not manifest_path.is_file():
        raise LiteratureSchemaError(f"current corpus manifest is missing: {manifest_path}")
    try:
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise LiteratureSchemaError(f"{manifest_path}: invalid corpus manifest: {exc}") from exc
    _reject_unknown_keys(data, _MANIFEST_KEYS, manifest_path, "manifest")
    if _required_string(data, "schema", manifest_path) != CORPUS_MANIFEST_SCHEMA:
        raise LiteratureSchemaError(f"{manifest_path}: unsupported corpus manifest schema")
    status = _required_string(data, "status", manifest_path)
    if status not in {"active", "bootstrap_empty"}:
        raise LiteratureSchemaError(f"{manifest_path}: status must be active or bootstrap_empty")
    expected_corpus_sha = _required_string(data, "corpus_sha256", manifest_path)
    if _SHA256_RE.fullmatch(expected_corpus_sha) is None:
        raise LiteratureSchemaError(f"{manifest_path}: corpus_sha256 must be lowercase SHA-256")
    expected_note_count = data.get("note_count")
    expected_fact_count = data.get("paper_fact_count")
    if (
        not isinstance(expected_note_count, int)
        or isinstance(expected_note_count, bool)
        or expected_note_count < 0
        or not isinstance(expected_fact_count, int)
        or isinstance(expected_fact_count, bool)
        or expected_fact_count < 0
    ):
        raise LiteratureSchemaError(f"{manifest_path}: manifest counts must be non-negative integers")
    raw_notes = data.get("notes")
    if not isinstance(raw_notes, list):
        raise LiteratureSchemaError(f"{manifest_path}: notes must be an array of tables")
    if status == "bootstrap_empty" and raw_notes:
        raise LiteratureSchemaError(f"{manifest_path}: bootstrap_empty manifest cannot name notes")
    if status == "active" and not raw_notes:
        raise LiteratureSchemaError(f"{manifest_path}: active manifest must name at least one note")
    if status == "bootstrap_empty" and not allow_empty:
        raise LiteratureSchemaError(
            "current literature corpus is bootstrap-empty; this is a safe reset state, not a query gate"
        )

    notes: list[LiteratureNote] = []
    source_ids: set[str] = set()
    for index, raw in enumerate(raw_notes):
        if not isinstance(raw, dict):
            raise LiteratureSchemaError(f"{manifest_path}: notes[{index}] must be a table")
        _reject_unknown_keys(raw, _MANIFEST_NOTE_KEYS, manifest_path, f"notes[{index}]")
        note_rel = _required_string(raw, "path", manifest_path)
        if not note_rel.startswith("docs/papers/reading_notes/"):
            raise LiteratureSchemaError(
                f"{manifest_path}: notes[{index}] path must be under docs/papers/reading_notes"
            )
        _, note_path = _repo_relative_file(note_rel, manifest_path, repo_root, "note path", suffix=".md")
        note = parse_note(note_path, repo_root, verify_artifact=True)
        expected = {
            "path": note_rel,
            "note_sha256": _required_string(raw, "note_sha256", manifest_path),
            "source_id": _required_string(raw, "source_id", manifest_path),
            "source_version": _required_string(raw, "source_version", manifest_path),
            "source_sha256": _required_string(raw, "source_sha256", manifest_path),
        }
        for key in ("note_sha256", "source_sha256"):
            if _SHA256_RE.fullmatch(expected[key]) is None:
                raise LiteratureSchemaError(f"{manifest_path}: notes[{index}] {key} is invalid")
        actual = note_identity(note)
        if actual != expected:
            raise LiteratureSchemaError(
                f"{manifest_path}: notes[{index}] identity mismatch: expected {expected!r}, got {actual!r}"
            )
        if note.source_id in source_ids:
            raise LiteratureSchemaError(f"{manifest_path}: duplicate source_id {note.source_id!r}")
        source_ids.add(note.source_id)
        notes.append(note)

    if expected_note_count != len(notes):
        raise LiteratureSchemaError(f"{manifest_path}: note_count does not match manifest entries")
    actual_fact_count = paper_fact_count(notes)
    if expected_fact_count != actual_fact_count:
        raise LiteratureSchemaError(f"{manifest_path}: paper_fact_count does not match admitted notes")
    actual_corpus_sha = corpus_sha256(notes)
    if expected_corpus_sha != actual_corpus_sha:
        raise LiteratureSchemaError(f"{manifest_path}: corpus_sha256 does not match admitted notes")
    return tuple(notes)


def write_json_atomic(path: Path, payload: Any) -> None:
    """Write a generated JSON artifact atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_text_atomic(path: Path, text: str) -> None:
    """Write a generated UTF-8 text artifact atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

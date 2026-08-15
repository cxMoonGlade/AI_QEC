"""Fail-closed contracts for the current literature corpus and generated evidence."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

from tools.literature_kg import (
    build_graph,
    graph_stats,
    main as kg_main,
    query_graph,
    render_concept_index,
    validate_graph,
)
from tools.literature_rag import (
    build_index,
    main as rag_main,
    query_index,
    validate_index,
)
from tools.literature_schema import (
    CORPUS_MANIFEST_SCHEMA,
    KG_SCHEMA,
    LiteratureSchemaError,
    audit_corpus,
    corpus_identity_sha256,
    corpus_sha256,
    load_current_corpus,
    note_identity,
    paper_fact_count,
    parse_note,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

# scripts/ is not a package, so the rebuild script is loaded by path. Executing it puts
# tools/ on sys.path, which is what its own bare ``literature_schema`` import needs.
_REBUILD_SPEC = importlib.util.spec_from_file_location(
    "rebuild_current_corpus_manifest",
    REPO_ROOT / "scripts" / "rebuild_current_corpus_manifest.py",
)
rebuild_manifest = importlib.util.module_from_spec(_REBUILD_SPEC)
_REBUILD_SPEC.loader.exec_module(rebuild_manifest)


def _write_current_note(
    root: Path,
    *,
    include_gap: bool = True,
    relative_path: str = "docs/papers/reading_notes/source_model.md",
) -> Path:
    artifact = root / "docs" / "papers" / "source.pdf"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"%PDF-1.7\ncontrolled full-text fixture\n%%EOF\n")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    audit_packet = root / "docs" / "simulator_validation" / "source_model.md"
    audit_packet.parent.mkdir(parents=True, exist_ok=True)
    audit_packet.write_text(
        "# Controlled source audit packet\n\nFull-text operation replay completed.\n",
        encoding="utf-8",
    )
    audit_digest = hashlib.sha256(audit_packet.read_bytes()).hexdigest()
    note = root / relative_path
    note.parent.mkdir(parents=True, exist_ok=True)
    gap = (
        """
## Unsupported scale [literature_gap]

Fact ID: gap.unsupported-scale
Source locator: Sec. IV, limitations
PDF page: 7
Claim: The source does not report a device-independent magnitude for this regime.

Gap scope: source_local
"""
        if include_gap
        else ""
    )
    note.write_text(
        f'''+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2401.00001"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2401.00001v2"
source_artifact = "docs/papers/source.pdf"
source_sha256 = "{digest}"
title = "Controlled source model"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/source_model.md"
audit_packet_sha256 = "{audit_digest}"
admission_status = "source_only_reviewed"
admission_reviewer = "controlled-fixture-reviewer"
admission_date = "2026-07-15"
visually_checked_pages = [3, 7]

[[relations]]
predicate = "defines"
object_id = "controlled-source-model"
object_type = "model"
object_label = "Controlled source model"
fact_id = "fact.controlled-source-model"
+++
# Full-text review — Controlled source model

## Model [paper_fact]

Fact ID: fact.controlled-source-model
Source locator: Sec. II, Eq. (3)
PDF page: 3
Claim: The Controlled source model evolves a binary latent state with a declared switching rate.
{gap}''',
        encoding="utf-8",
    )
    return note


def _write_manifest_identities(
    root: Path,
    identities: tuple[dict[str, object], ...],
    *,
    fact_count: int,
) -> Path:
    manifest = root / "docs" / "papers" / "CURRENT_CORPUS.toml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    status = "active" if identities else "bootstrap_empty"
    lines = [
        f'schema = "{CORPUS_MANIFEST_SCHEMA}"',
        f'status = "{status}"',
        f'corpus_sha256 = "{corpus_identity_sha256(identities)}"',
        f"note_count = {len(identities)}",
        f"paper_fact_count = {fact_count}",
        "",
    ]
    if not identities:
        lines.extend(("notes = []", ""))
    for identity in identities:
        lines.extend(
            (
                "[[notes]]",
                f'path = "{identity["path"]}"',
                f'note_sha256 = "{identity["note_sha256"]}"',
                f'source_id = "{identity["source_id"]}"',
                f'source_version = "{identity["source_version"]}"',
                f'source_sha256 = "{identity["source_sha256"]}"',
                "",
            )
        )
    manifest.write_text("\n".join(lines), encoding="utf-8")
    return manifest


def _write_manifest(root: Path, notes: tuple[Path, ...] = ()) -> Path:
    parsed_notes = tuple(parse_note(note, root) for note in notes)
    identities = tuple(note_identity(note) for note in parsed_notes)
    assert corpus_identity_sha256(identities) == corpus_sha256(parsed_notes)
    return _write_manifest_identities(
        root,
        identities,
        fact_count=paper_fact_count(parsed_notes),
    )


def _load_fixture_corpus(root: Path):
    note = _write_current_note(root)
    manifest = _write_manifest(root, (note,))
    return manifest, load_current_corpus(manifest, root)


def _replace_toml_value(path: Path, key: str, replacement: str) -> None:
    prefix = f"{key} = "
    lines = path.read_text(encoding="utf-8").splitlines()
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    assert len(matches) == 1
    lines[matches[0]] = f"{prefix}{replacement}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _amend_note_in_place(note_path: Path) -> None:
    """Append one paper_fact to an admitted note: same path, new content and hash."""

    note_path.write_text(
        note_path.read_text(encoding="utf-8")
        + """
## Second observable [paper_fact]

Fact ID: fact.controlled-second-observable
Source locator: Sec. III, Eq. (7)
PDF page: 7
Claim: The Controlled source model reports a second observable at a declared rate.
""",
        encoding="utf-8",
    )


def _run_rebuild(root: Path, monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    monkeypatch.setattr(rebuild_manifest, "REPO", root)
    monkeypatch.setattr(
        rebuild_manifest, "MANIFEST", root / "docs" / "papers" / "CURRENT_CORPUS.toml"
    )
    monkeypatch.setattr(sys, "argv", ["rebuild_current_corpus_manifest.py", *argv])
    return rebuild_manifest.main()


def _assert_cli_error(
    result: int,
    capsys: pytest.CaptureFixture[str],
    *,
    contains: str,
) -> None:
    assert result == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: ")
    assert captured.err.endswith("\n")
    assert len(captured.err.splitlines()) == 1
    assert contains in captured.err


def test_manifest_loads_an_explicit_current_note_and_fact_relation(tmp_path: Path) -> None:
    manifest, notes = _load_fixture_corpus(tmp_path)

    assert manifest.is_file()
    assert len(notes) == 1
    assert notes[0].source_id == "arxiv:2401.00001"
    fact = notes[0].sections[0]
    assert fact.fact_id == "fact.controlled-source-model"
    assert fact.source_locator == "Sec. II, Eq. (3)"
    assert fact.pdf_page == 3
    assert fact.claim.startswith("The Controlled source model evolves")
    assert notes[0].relations[0].fact_id == fact.fact_id


@pytest.mark.parametrize(
    ("old", "new", "message"),
    (
        ('review_scope = "full_text"', 'review_scope = "abstract_only"', "full-text"),
        (
            'operation_replay_status = "complete"',
            'operation_replay_status = "pending"',
            "operation replay",
        ),
        (
            'admission_status = "source_only_reviewed"',
            'admission_status = "pending"',
            "admission_status",
        ),
        (
            "visually_checked_pages = [3, 7]",
            'visually_checked_pages = ["3", "7"]',
            "positive integers",
        ),
    ),
)
def test_note_admission_metadata_fails_closed(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    note_path = _write_current_note(tmp_path)
    note_path.write_text(
        note_path.read_text(encoding="utf-8").replace(old, new, 1),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match=message):
        parse_note(note_path, tmp_path)


def test_note_requires_a_tracked_separate_hash_verified_audit_packet(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path)
    audit_packet = tmp_path / "docs" / "simulator_validation" / "source_model.md"
    audit_packet.unlink()
    with pytest.raises(LiteratureSchemaError, match="audit packet.*missing"):
        parse_note(note_path, tmp_path)

    note_path = _write_current_note(tmp_path)
    audit_packet.write_text("forged review packet\n", encoding="utf-8")
    with pytest.raises(LiteratureSchemaError, match="audit packet SHA-256 mismatch"):
        parse_note(note_path, tmp_path)

    note_path = _write_current_note(tmp_path)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace(
            'audit_packet = "docs/simulator_validation/source_model.md"',
            'audit_packet = "docs/papers/reading_notes/source_model.md"',
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(LiteratureSchemaError, match="docs/simulator_validation"):
        parse_note(note_path, tmp_path)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("Fact ID: fact.controlled-source-model\n", "Fact ID"),
        ("Source locator: Sec. II, Eq. (3)\n", "Source locator"),
        ("PDF page: 3\n", "PDF page"),
        (
            "Claim: The Controlled source model evolves a binary latent state with a declared switching rate.\n",
            "Claim",
        ),
    ],
)
def test_every_current_h2_requires_one_complete_fact(
    tmp_path: Path, line: str, message: str
) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    note_path.write_text(
        note_path.read_text(encoding="utf-8").replace(line, "", 1),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match=message):
        parse_note(note_path, tmp_path)


def test_current_h2_rejects_duplicate_fact_ids(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace(
            "Fact ID: fact.controlled-source-model",
            "Fact ID: fact.controlled-source-model\nFact ID: fact.second",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match="Fact ID"):
        parse_note(note_path, tmp_path)


def test_relation_must_reference_an_existing_paper_fact(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace(
            'fact_id = "fact.controlled-source-model"',
            'fact_id = "fact.missing"',
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match="fact.missing"):
        parse_note(note_path, tmp_path)


def test_relation_rejects_legacy_claim_locator_and_section_fields(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace(
            'fact_id = "fact.controlled-source-model"',
            '''fact_id = "fact.controlled-source-model"
section = "Model"
source_locator = "Sec. II, Eq. (3)"
claim = "The Controlled source model evolves a binary latent state with a declared switching rate."''',
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match="unsupported.*relation|relation.*keys"):
        parse_note(note_path, tmp_path)


def test_locator_must_be_exact_and_match_a_visually_checked_pdf_page(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace("Source locator: Sec. II, Eq. (3)", "Source locator: unknown", 1),
        encoding="utf-8",
    )
    with pytest.raises(LiteratureSchemaError, match="locator"):
        parse_note(note_path, tmp_path)

    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(text.replace("PDF page: 3", "PDF page: 99", 1), encoding="utf-8")
    with pytest.raises(LiteratureSchemaError, match="visually checked|visually_checked_pages"):
        parse_note(note_path, tmp_path)


def test_literature_gap_must_be_explicitly_source_local(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path)
    note_path.write_text(
        note_path.read_text(encoding="utf-8").replace(
            "\nGap scope: source_local\n", "\n", 1
        ),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match="Gap scope: source_local"):
        parse_note(note_path, tmp_path)


@pytest.mark.parametrize(
    "pollution",
    (
        "[ours] The model is useful.",
        "Relevance to "
        + "_".join(("qec", "twin"))
        + ": this maps to "
        + "".join(("teach", "er"))
        + " M"
        + "12.",
        "This is our simulator's project inference.",
    ),
)
def test_project_inference_cannot_enter_a_current_fact(
    tmp_path: Path, pollution: str
) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace(
            "Claim: The Controlled source model evolves a binary latent state with a declared switching rate.",
            f"Claim: {pollution}",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match="project|retired|inference"):
        parse_note(note_path, tmp_path)


def test_unclassified_preamble_and_unknown_metadata_fail_closed(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace(
            "# Full-text review — Controlled source model\n",
            "# Full-text review — Controlled source model\n\nProject decision outside evidence.\n",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(LiteratureSchemaError, match="unclassified prose"):
        parse_note(note_path, tmp_path)

    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(
        text.replace(
            'admission_date = "2026-07-15"',
            'admission_date = "2026-07-15"\nproject_application = "hidden"',
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(LiteratureSchemaError, match="unknown note metadata keys"):
        parse_note(note_path, tmp_path)


def test_source_identity_pdf_signature_and_lowercase_hash_are_verified(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    note_path.write_text(text.replace("2401.00001v2", "2401.00001v3", 1), encoding="utf-8")
    with pytest.raises(LiteratureSchemaError, match="pin the declared version"):
        parse_note(note_path, tmp_path)

    note_path = _write_current_note(tmp_path, include_gap=False)
    text = note_path.read_text(encoding="utf-8")
    digest = hashlib.sha256((tmp_path / "docs" / "papers" / "source.pdf").read_bytes()).hexdigest()
    note_path.write_text(text.replace(digest, digest.upper(), 1), encoding="utf-8")
    with pytest.raises(LiteratureSchemaError, match="lowercase"):
        parse_note(note_path, tmp_path)

    note_path = _write_current_note(tmp_path, include_gap=False)
    artifact = tmp_path / "docs" / "papers" / "source.pdf"
    artifact.write_bytes(b"not a PDF despite the suffix")
    forged_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    text = note_path.read_text(encoding="utf-8")
    original_digest = next(
        line.split('"')[1]
        for line in text.splitlines()
        if line.startswith("source_sha256 = ")
    )
    note_path.write_text(text.replace(original_digest, forged_digest, 1), encoding="utf-8")
    with pytest.raises(LiteratureSchemaError, match="not a PDF"):
        parse_note(note_path, tmp_path)


def test_source_identity_accepts_a_pinned_legacy_arxiv_category_id(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    _replace_toml_value(note_path, "source_id", '"arxiv:quant-ph/0408190"')
    _replace_toml_value(
        note_path,
        "source_uri",
        '"https://arxiv.org/abs/quant-ph/0408190v2"',
    )

    note = parse_note(note_path, tmp_path)

    assert note.source_id == "arxiv:quant-ph/0408190"
    assert note.source_version == "v2"


@pytest.mark.parametrize(
    ("source_id", "source_uri", "message"),
    (
        (
            "arxiv:quant-ph/0408190",
            "https://arxiv.org/abs/quant-ph/0408190",
            "pin the declared version",
        ),
        (
            "arxiv:quant-ph/0408190v2",
            "https://arxiv.org/abs/quant-ph/0408190v2",
            "arxiv: or doi:",
        ),
        (
            "arxiv:Quant-ph/0408190",
            "https://arxiv.org/abs/Quant-ph/0408190v2",
            "arxiv: or doi:",
        ),
        (
            "arxiv:quant_ph/0408190",
            "https://arxiv.org/abs/quant_ph/0408190v2",
            "arxiv: or doi:",
        ),
    ),
)
def test_source_identity_rejects_unpinned_or_malformed_legacy_arxiv_ids(
    tmp_path: Path,
    source_id: str,
    source_uri: str,
    message: str,
) -> None:
    note_path = _write_current_note(tmp_path, include_gap=False)
    _replace_toml_value(note_path, "source_id", f'"{source_id}"')
    _replace_toml_value(note_path, "source_uri", f'"{source_uri}"')

    with pytest.raises(LiteratureSchemaError, match=message):
        parse_note(note_path, tmp_path)


def test_candidate_audit_rejects_a_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(LiteratureSchemaError, match="directory is missing"):
        audit_corpus(tmp_path / "missing", tmp_path, schema_only=True)


def test_missing_manifest_and_missing_manifest_note_fail_closed(tmp_path: Path) -> None:
    missing_manifest = tmp_path / "docs" / "papers" / "CURRENT_CORPUS.toml"
    with pytest.raises(LiteratureSchemaError, match="manifest.*missing|missing.*manifest"):
        load_current_corpus(missing_manifest, tmp_path)

    missing_note = tmp_path / "docs" / "papers" / "reading_notes" / "missing.md"
    manifest = _write_manifest_identities(
        tmp_path,
        (
            {
                "path": missing_note.relative_to(tmp_path).as_posix(),
                "note_sha256": "0" * 64,
                "source_id": "arxiv:2401.00001",
                "source_version": "v2",
                "source_sha256": "1" * 64,
            },
        ),
        fact_count=1,
    )
    with pytest.raises(LiteratureSchemaError, match="missing.md"):
        load_current_corpus(manifest, tmp_path)


def test_manifest_note_losing_schema_marker_is_not_silently_skipped(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    note_path.write_text(
        note_path.read_text(encoding="utf-8").replace("+++\n", "---\n", 1),
        encoding="utf-8",
    )

    with pytest.raises(LiteratureSchemaError, match="front matter|schema"):
        load_current_corpus(manifest, tmp_path)


@pytest.mark.parametrize(
    ("key", "replacement", "message"),
    (
        ("note_count", "2", "note_count"),
        ("paper_fact_count", "2", "paper_fact_count"),
        ("corpus_sha256", f'"{"0" * 64}"', "corpus_sha256"),
        ("note_sha256", f'"{"0" * 64}"', "identity mismatch"),
        ("source_id", '"arxiv:2401.00002"', "identity mismatch"),
        ("source_version", '"v3"', "identity mismatch"),
        ("source_sha256", f'"{"0" * 64}"', "identity mismatch"),
    ),
)
def test_manifest_counts_hashes_and_note_identity_are_recomputed(
    tmp_path: Path, key: str, replacement: str, message: str
) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    _replace_toml_value(manifest, key, replacement)

    with pytest.raises(LiteratureSchemaError, match=message):
        load_current_corpus(manifest, tmp_path)


def test_unmanifested_candidates_are_never_implicitly_admitted(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    unmanifested = tmp_path / "docs" / "papers" / "reading_notes" / "old_project.md"
    unmanifested.write_text("legacy unvalidated project prose\n", encoding="utf-8")

    notes = load_current_corpus(manifest, tmp_path)

    assert tuple(note.relative_path for note in notes) == (
        "docs/papers/reading_notes/source_model.md",
    )


def test_empty_current_corpus_requires_explicit_bootstrap_authority(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    with pytest.raises(LiteratureSchemaError, match="empty"):
        load_current_corpus(manifest, tmp_path)
    assert load_current_corpus(manifest, tmp_path, allow_empty=True) == ()


def test_current_corpus_always_verifies_source_artifact_and_hash(tmp_path: Path) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    artifact = tmp_path / "docs" / "papers" / "source.pdf"
    artifact.unlink()
    with pytest.raises(LiteratureSchemaError, match="source artifact.*missing"):
        load_current_corpus(manifest, tmp_path)

    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    artifact.write_bytes(b"%PDF-1.7\ncorrupted\n%%EOF\n")
    with pytest.raises(LiteratureSchemaError, match="SHA-256 mismatch"):
        load_current_corpus(manifest, tmp_path)


def test_rebuild_sees_an_amended_note_that_a_path_set_comparison_cannot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    _amend_note_in_place(note_path)
    recorded = manifest.read_bytes()

    # The state the rebuild script exists to repair: the retrieval surfaces fail closed
    # here, so --check reporting OK is what makes the manifest unrepairable.
    with pytest.raises(LiteratureSchemaError, match="identity mismatch"):
        load_current_corpus(manifest, tmp_path)

    assert _run_rebuild(tmp_path, monkeypatch, "--check") == 1
    report = capsys.readouterr().out
    assert "DRIFT" in report
    assert "orphaned (valid, not retrievable)  0" in report
    assert "stale (in manifest, not valid)     0" in report
    assert "amended (admitted, recorded stale) 1" in report
    assert "~ docs/papers/reading_notes/source_model.md  [note_sha256]" in report
    assert manifest.read_bytes() == recorded

    assert _run_rebuild(tmp_path, monkeypatch) == 0
    assert "wrote 1 notes, 2 paper_facts" in capsys.readouterr().out

    # load_current_corpus recomputes every identity, both counts, and corpus_sha256,
    # so loading is the assertion that the rewritten manifest is internally exact.
    notes = load_current_corpus(manifest, tmp_path)
    assert tuple(note.relative_path for note in notes) == (
        "docs/papers/reading_notes/source_model.md",
    )
    assert paper_fact_count(notes) == 2
    assert _run_rebuild(tmp_path, monkeypatch, "--check") == 0


def test_rebuild_leaves_an_in_sync_manifest_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    recorded = manifest.read_bytes()

    assert _run_rebuild(tmp_path, monkeypatch, "--check") == 0
    assert "OK — manifest equals the audited-valid set" in capsys.readouterr().out

    assert _run_rebuild(tmp_path, monkeypatch) == 0
    assert "no change" in capsys.readouterr().out
    assert manifest.read_bytes() == recorded


def test_rebuild_catches_a_stale_manifest_header_with_every_note_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    _replace_toml_value(manifest, "corpus_sha256", f'"{"0" * 64}"')

    assert _run_rebuild(tmp_path, monkeypatch, "--check") == 1
    report = capsys.readouterr().out
    assert "stale header fields                1" in report
    assert "! corpus_sha256" in report

    assert _run_rebuild(tmp_path, monkeypatch) == 0
    assert load_current_corpus(manifest, tmp_path)[0].relative_path == (
        "docs/papers/reading_notes/source_model.md"
    )


def test_rebuild_refreshes_identities_without_admitting_an_audit_failing_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    note_path = _write_current_note(tmp_path)
    manifest = _write_manifest(tmp_path, (note_path,))
    _amend_note_in_place(note_path)
    unadmittable = tmp_path / "docs" / "papers" / "reading_notes" / "old_project.md"
    unadmittable.write_text("legacy unvalidated project prose\n", encoding="utf-8")

    assert _run_rebuild(tmp_path, monkeypatch) == 0

    notes = load_current_corpus(manifest, tmp_path)
    assert tuple(note.relative_path for note in notes) == (
        "docs/papers/reading_notes/source_model.md",
    )


def test_retrieval_contains_only_single_source_located_paper_facts(tmp_path: Path) -> None:
    _, notes = _load_fixture_corpus(tmp_path)
    index = build_index(notes)
    validate_index(index, live_notes=notes)

    assert index["note_count"] == 1
    assert index["chunk_count"] == 1
    assert index["epistemic_classes"] == ["paper_fact"]
    assert "device-independent magnitude" not in index["chunks"][0]["text"]
    hits = query_index(index, "binary latent switching", top_k=3)
    assert len(hits) == 1
    assert hits[0]["fact_id"] == "fact.controlled-source-model"
    assert hits[0]["source_locator"] == "Sec. II, Eq. (3)"
    assert hits[0]["pdf_page"] == 3
    assert len(hits[0]["section_sha256"]) == 64
    assert len(hits[0]["chunk_sha256"]) == 64


@pytest.mark.parametrize(
    "corruption",
    (
        "text",
        "claim",
        "locator",
        "pdf_page",
        "note_count",
        "paper_fact_count",
        "chunk_count",
        "corpus_sha256",
        "term_frequencies",
        "hash",
        "id",
    ),
)
def test_rag_validator_rejects_self_inconsistent_artifact(
    tmp_path: Path, corruption: str
) -> None:
    _, notes = _load_fixture_corpus(tmp_path)
    index = build_index(notes)
    chunk = index["chunks"][0]
    if corruption == "text":
        chunk["text"] = "Forged project inference."
    elif corruption == "claim":
        chunk["claim"] = "A different source claim."
    elif corruption == "locator":
        chunk["source_locator"] = "Sec. III, Eq. (9)"
    elif corruption == "pdf_page":
        chunk["pdf_page"] = 9
    elif corruption == "note_count":
        index["note_count"] += 1
    elif corruption == "paper_fact_count":
        index["paper_fact_count"] += 1
    elif corruption == "chunk_count":
        index["chunk_count"] += 1
    elif corruption == "corpus_sha256":
        index["corpus_sha256"] = "0" * 64
    elif corruption == "term_frequencies":
        chunk["term_frequencies"] = {"forged": 1000}
    elif corruption == "hash":
        chunk["chunk_sha256"] = "0" * 64
    elif corruption == "id":
        chunk["id"] = "forged"

    with pytest.raises(ValueError):
        validate_index(index)


def test_rag_validator_rejects_stale_but_internally_valid_corpus(tmp_path: Path) -> None:
    manifest, notes = _load_fixture_corpus(tmp_path)
    index = build_index(notes)
    note_path = tmp_path / "docs" / "papers" / "reading_notes" / "source_model.md"
    note_path.write_text(
        note_path.read_text(encoding="utf-8").replace(
            "binary latent state", "binary declared state"
        ),
        encoding="utf-8",
    )
    manifest = _write_manifest(tmp_path, (note_path,))
    live_notes = load_current_corpus(manifest, tmp_path)

    with pytest.raises(ValueError, match="corpus|stale|live"):
        validate_index(index, live_notes=live_notes)


def test_knowledge_graph_has_fact_locators_and_zero_dangling_edges(tmp_path: Path) -> None:
    _, notes = _load_fixture_corpus(tmp_path)
    graph = build_graph(notes)
    validate_graph(graph, live_notes=notes)

    assert graph["schema"] == KG_SCHEMA
    assert graph_stats(graph)["dangling_edges"] == 0
    edge = graph["edges"][0]
    assert edge["fact_id"] == "fact.controlled-source-model"
    assert edge["source_locator"] == "Sec. II, Eq. (3)"
    assert edge["pdf_page"] == 3
    assert len(edge["section_sha256"]) == 64
    results = query_graph(graph, "neighbors", "controlled-source-model")
    assert len(results) == 1
    assert results[0]["claim"].startswith("The Controlled source model evolves")


@pytest.mark.parametrize(
    "corruption",
    (
        "claim",
        "relation",
        "locator",
        "hash",
        "claim_hash",
        "section_hash",
        "note_count",
        "paper_fact_count",
        "corpus_sha256",
        "stats",
        "edge_id",
    ),
)
def test_kg_validator_rejects_self_inconsistent_artifact(
    tmp_path: Path, corruption: str
) -> None:
    _, notes = _load_fixture_corpus(tmp_path)
    graph = build_graph(notes)
    edge = graph["edges"][0]
    if corruption == "claim":
        edge["claim"] = "Forged claim."
    elif corruption == "relation":
        edge["relation"] = "invented_relation"
    elif corruption == "locator":
        edge["source_locator"] = "unknown"
    elif corruption == "hash":
        edge["source_sha256"] = "bad"
    elif corruption == "claim_hash":
        edge["claim_sha256"] = "0" * 64
    elif corruption == "section_hash":
        edge["section_sha256"] = "0" * 64
    elif corruption == "note_count":
        graph["note_count"] += 1
    elif corruption == "paper_fact_count":
        graph["paper_fact_count"] += 1
    elif corruption == "corpus_sha256":
        graph["corpus_sha256"] = "0" * 64
    elif corruption == "stats":
        graph["stats"]["edges"] += 1
    elif corruption == "edge_id":
        edge["id"] = "forged"

    with pytest.raises(ValueError):
        validate_graph(graph)


def test_knowledge_graph_rejects_a_dangling_edge(tmp_path: Path) -> None:
    _, notes = _load_fixture_corpus(tmp_path)
    graph = build_graph(notes)
    graph["edges"][0]["target"] = "model:missing"
    with pytest.raises(ValueError, match="dangling"):
        validate_graph(graph)


def test_kg_validator_rejects_stale_but_internally_valid_corpus(tmp_path: Path) -> None:
    manifest, notes = _load_fixture_corpus(tmp_path)
    graph = build_graph(notes)
    note_path = tmp_path / "docs" / "papers" / "reading_notes" / "source_model.md"
    note_path.write_text(
        note_path.read_text(encoding="utf-8").replace(
            "binary latent state", "binary declared state"
        ),
        encoding="utf-8",
    )
    manifest = _write_manifest(tmp_path, (note_path,))
    live_notes = load_current_corpus(manifest, tmp_path)

    with pytest.raises(ValueError, match="corpus|stale|live"):
        validate_graph(graph, live_notes=live_notes)


def test_trusted_cli_has_no_no_verify_artifacts_escape_hatch(tmp_path: Path) -> None:
    _load_fixture_corpus(tmp_path)

    with pytest.raises(SystemExit):
        rag_main(
            [
                "--repo-root",
                str(tmp_path),
                "--no-verify-artifacts",
                "query",
                "binary",
            ]
        )
    with pytest.raises(SystemExit):
        kg_main(
            [
                "--repo-root",
                str(tmp_path),
                "--no-verify-artifacts",
                "stats",
            ]
        )


def test_trusted_build_and_query_cannot_ignore_a_missing_pdf(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _load_fixture_corpus(tmp_path)
    (tmp_path / "docs" / "papers" / "source.pdf").unlink()

    _assert_cli_error(
        rag_main(["--repo-root", str(tmp_path), "query", "binary"]),
        capsys,
        contains="source artifact is missing",
    )
    _assert_cli_error(
        rag_main(
            [
                "--repo-root",
                str(tmp_path),
                "build",
                "--output",
                str(tmp_path / "rag.json"),
            ]
        ),
        capsys,
        contains="source artifact is missing",
    )
    _assert_cli_error(
        kg_main(["--repo-root", str(tmp_path), "stats"]),
        capsys,
        contains="source artifact is missing",
    )


def test_allow_empty_is_limited_to_reset_build_and_render(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_manifest(tmp_path)

    _assert_cli_error(
        rag_main(
            [
                "--repo-root",
                str(tmp_path),
                "build",
                "--output",
                str(tmp_path / "rag.json"),
            ]
        ),
        capsys,
        contains="bootstrap-empty",
    )
    assert (
        rag_main(
            [
                "--repo-root",
                str(tmp_path),
                "build",
                "--allow-empty",
                "--output",
                str(tmp_path / "rag.json"),
            ]
        )
        == 0
    )
    capsys.readouterr()
    with pytest.raises(SystemExit):
        rag_main(
            [
                "--repo-root",
                str(tmp_path),
                "query",
                "anything",
                "--allow-empty",
            ]
        )
    capsys.readouterr()

    assert (
        kg_main(
            [
                "--repo-root",
                str(tmp_path),
                "render-index",
                "--allow-empty",
                "--output",
                str(tmp_path / "CONCEPT_INDEX.md"),
            ]
        )
        == 0
    )
    capsys.readouterr()
    with pytest.raises(SystemExit):
        kg_main(["--repo-root", str(tmp_path), "stats", "--allow-empty"])


def test_repository_concept_index_matches_the_explicit_current_corpus() -> None:
    manifest = REPO_ROOT / "docs" / "papers" / "CURRENT_CORPUS.toml"
    notes = load_current_corpus(manifest, REPO_ROOT, allow_empty=True)
    graph = build_graph(notes)
    validate_graph(graph, live_notes=notes)
    expected = render_concept_index(graph)
    actual = (REPO_ROOT / "docs" / "papers" / "CONCEPT_INDEX.md").read_text(
        encoding="utf-8"
    )
    assert actual == expected

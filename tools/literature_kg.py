"""Source-located knowledge graph over the explicit current corpus manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sys
from typing import Any, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.literature_schema import (  # noqa: E402
    KG_SCHEMA,
    OBJECT_TYPES,
    RELATION_TYPES,
    LiteratureNote,
    LiteratureSchemaError,
    corpus_identity_sha256,
    corpus_sha256,
    load_current_corpus,
    note_identity,
    paper_fact_count,
    write_json_atomic,
    write_text_atomic,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "docs" / "papers" / "CURRENT_CORPUS.toml"
DEFAULT_GRAPH = REPO_ROOT / "outputs" / "literature" / "knowledge_graph.json"
DEFAULT_CONCEPT_INDEX = REPO_ROOT / "docs" / "papers" / "CONCEPT_INDEX.md"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSPECIFIED_LOCATOR_RE = re.compile(r"\b(?:unknown|n/?a|none|tbd|somewhere)\b", re.IGNORECASE)
_GRAPH_KEYS = frozenset(
    {
        "schema",
        "corpus_status",
        "corpus_sha256",
        "note_count",
        "paper_fact_count",
        "notes",
        "nodes",
        "edges",
        "stats",
    }
)
_IDENTITY_KEYS = frozenset(
    {
        "path",
        "note_sha256",
        "source_id",
        "source_version",
        "source_sha256",
        "paper_fact_count",
    }
)
_SOURCE_NODE_KEYS = frozenset(
    {
        "id",
        "type",
        "label",
        "note_path",
        "note_sha256",
        "source_id",
        "source_version",
        "source_uri",
        "source_artifact",
        "source_sha256",
    }
)
_CONCEPT_NODE_KEYS = frozenset({"id", "type", "label"})
_EDGE_KEYS = frozenset(
    {
        "id",
        "source",
        "target",
        "relation",
        "fact_id",
        "claim",
        "claim_sha256",
        "note_path",
        "section",
        "source_locator",
        "pdf_page",
        "source_sha256",
        "note_sha256",
        "section_sha256",
    }
)


def _edge_id(edge: dict[str, Any]) -> str:
    fields = (
        edge["source"],
        edge["relation"],
        edge["target"],
        edge["note_path"],
        edge["fact_id"],
        edge["section"],
        edge["source_locator"],
        str(edge["pdf_page"]),
        edge["claim_sha256"],
        edge["section_sha256"],
    )
    return hashlib.sha256("\0".join(fields).encode("utf-8")).hexdigest()[:24]


def build_graph(notes: Sequence[LiteratureNote]) -> dict[str, Any]:
    """Build a graph solely from explicit, source-located paper-fact relations."""

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    object_definitions: dict[str, tuple[str, str]] = {}
    for note in sorted(notes, key=lambda item: item.relative_path):
        source_node = f"source:{note.source_id}"
        nodes[source_node] = {
            "id": source_node,
            "type": "source",
            "label": note.title,
            "note_path": note.relative_path,
            "note_sha256": note.note_sha256,
            "source_id": note.source_id,
            "source_version": note.source_version,
            "source_uri": note.source_uri,
            "source_artifact": note.source_artifact,
            "source_sha256": note.source_sha256,
        }
        for relation in note.relations:
            section = next(item for item in note.sections if item.fact_id == relation.fact_id)
            section_sha256 = hashlib.sha256(section.body.encode("utf-8")).hexdigest()
            claim_sha256 = hashlib.sha256(relation.claim.encode("utf-8")).hexdigest()
            target_node = f"{relation.object_type}:{relation.object_id}"
            definition = (relation.object_type, relation.object_label)
            previous = object_definitions.get(target_node)
            if previous is not None and previous != definition:
                raise ValueError(
                    f"conflicting definitions for {target_node}: {previous!r} vs {definition!r}"
                )
            object_definitions[target_node] = definition
            nodes[target_node] = {
                "id": target_node,
                "type": relation.object_type,
                "label": relation.object_label,
            }
            edge: dict[str, Any] = {
                "source": source_node,
                "target": target_node,
                "relation": relation.predicate,
                "fact_id": relation.fact_id,
                "claim": relation.claim,
                "claim_sha256": claim_sha256,
                "note_path": note.relative_path,
                "section": relation.section,
                "source_locator": relation.source_locator,
                "pdf_page": relation.pdf_page,
                "source_sha256": note.source_sha256,
                "note_sha256": note.note_sha256,
                "section_sha256": section_sha256,
            }
            edge["id"] = _edge_id(edge)
            edges.append(edge)
    identities = [
        note_identity(note)
        | {
            "paper_fact_count": sum(
                section.epistemic_class == "paper_fact" for section in note.sections
            )
        }
        for note in sorted(notes, key=lambda item: item.relative_path)
    ]
    graph: dict[str, Any] = {
        "schema": KG_SCHEMA,
        "corpus_status": "active" if identities else "bootstrap_empty",
        "corpus_sha256": corpus_sha256(notes),
        "note_count": len(identities),
        "paper_fact_count": paper_fact_count(notes),
        "notes": identities,
        "nodes": [nodes[node_id] for node_id in sorted(nodes)],
        "edges": sorted(edges, key=lambda edge: edge["id"]),
    }
    graph["stats"] = graph_stats(graph)
    validate_graph(graph)
    return graph


def graph_stats(graph: dict[str, Any]) -> dict[str, int]:
    """Compute graph counts and dangling-edge count."""

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}
    dangling = sum(
        not isinstance(edge, dict)
        or edge.get("source") not in node_ids
        or edge.get("target") not in node_ids
        for edge in edges
    )
    return {
        "nodes": len(nodes),
        "sources": sum(isinstance(node, dict) and node.get("type") == "source" for node in nodes),
        "concept_nodes": sum(
            isinstance(node, dict) and node.get("type") != "source" for node in nodes
        ),
        "edges": len(edges),
        "dangling_edges": dangling,
    }


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], context: str) -> None:
    if set(value) != expected:
        raise ValueError(
            f"{context} fields differ: missing={sorted(expected - set(value))}, "
            f"extra={sorted(set(value) - expected)}"
        )


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and _HASH_RE.fullmatch(value) is not None


def validate_graph(
    graph: dict[str, Any], *, live_notes: Sequence[LiteratureNote] | None = None
) -> None:
    """Reject malformed, dangling, unsourced, self-inconsistent, or stale graphs."""

    if not isinstance(graph, dict):
        raise ValueError("knowledge graph must be an object")
    _require_exact_keys(graph, _GRAPH_KEYS, "knowledge graph")
    if graph["schema"] != KG_SCHEMA:
        raise ValueError(f"unsupported knowledge-graph schema {graph['schema']!r}")
    if graph["corpus_status"] not in {"active", "bootstrap_empty"}:
        raise ValueError("knowledge graph has invalid corpus_status")
    identities = graph["notes"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    if not isinstance(identities, list) or not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("knowledge graph notes, nodes, and edges must be lists")

    identity_by_path: dict[str, dict[str, Any]] = {}
    source_ids: set[str] = set()
    for identity in identities:
        if not isinstance(identity, dict):
            raise ValueError("knowledge-graph note identity must be an object")
        _require_exact_keys(identity, _IDENTITY_KEYS, "knowledge-graph note identity")
        string_keys = _IDENTITY_KEYS - {"paper_fact_count"}
        if not all(isinstance(identity[key], str) and identity[key] for key in string_keys):
            raise ValueError("knowledge-graph note identity fields must be non-empty strings")
        if (
            not isinstance(identity["paper_fact_count"], int)
            or isinstance(identity["paper_fact_count"], bool)
            or identity["paper_fact_count"] <= 0
        ):
            raise ValueError("knowledge-graph note identity has an invalid paper_fact_count")
        if not _valid_hash(identity["note_sha256"]) or not _valid_hash(identity["source_sha256"]):
            raise ValueError("knowledge-graph note identity has an invalid hash")
        if identity["path"] in identity_by_path or identity["source_id"] in source_ids:
            raise ValueError("knowledge-graph note paths and source IDs must be unique")
        identity_by_path[identity["path"]] = identity
        source_ids.add(identity["source_id"])
    if graph["note_count"] != len(identities):
        raise ValueError("knowledge-graph note_count mismatch")
    if graph["corpus_sha256"] != corpus_identity_sha256(identities):
        raise ValueError("knowledge-graph corpus_sha256 mismatch")
    if graph["corpus_status"] == "active" and not identities:
        raise ValueError("active knowledge-graph corpus cannot be empty")
    if graph["corpus_status"] == "bootstrap_empty" and (identities or nodes or edges):
        raise ValueError("bootstrap-empty graph cannot contain notes, nodes, or edges")

    node_by_id: dict[str, dict[str, Any]] = {}
    source_paths: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("knowledge-graph node must be an object")
        node_type = node.get("type")
        if node_type == "source":
            _require_exact_keys(node, _SOURCE_NODE_KEYS, "source node")
            if node["id"] != f"source:{node['source_id']}":
                raise ValueError("source node ID mismatch")
            identity = identity_by_path.get(node["note_path"])
            if identity is None:
                raise ValueError("source node references an undeclared note")
            for key in ("note_sha256", "source_id", "source_version", "source_sha256"):
                if node[key] != identity[key]:
                    raise ValueError(f"source node {key} disagrees with note identity")
            source_paths.add(node["note_path"])
        else:
            _require_exact_keys(node, _CONCEPT_NODE_KEYS, "concept node")
            if node_type not in OBJECT_TYPES:
                raise ValueError(f"unsupported concept node type {node_type!r}")
            if node["id"] != f"{node_type}:{node['id'].split(':', 1)[-1]}":
                raise ValueError("concept node ID/type mismatch")
        for key in ("id", "type", "label"):
            if not isinstance(node[key], str) or not node[key].strip():
                raise ValueError(f"knowledge-graph node lacks {key}")
        if node["id"] in node_by_id:
            raise ValueError(f"duplicate knowledge-graph node ID {node['id']!r}")
        node_by_id[node["id"]] = node
    if source_paths != set(identity_by_path):
        raise ValueError("knowledge graph must contain exactly one source node per admitted note")

    edge_ids: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("knowledge-graph edge must be an object")
        _require_exact_keys(edge, _EDGE_KEYS, "knowledge-graph edge")
        if edge["source"] not in node_by_id or edge["target"] not in node_by_id:
            raise ValueError(f"dangling knowledge-graph edge {edge!r}")
        if node_by_id[edge["source"]]["type"] != "source":
            raise ValueError("knowledge-graph edge source must be a source node")
        if node_by_id[edge["target"]]["type"] == "source":
            raise ValueError("knowledge-graph edge target must be a concept node")
        if edge["relation"] not in RELATION_TYPES:
            raise ValueError(f"unsupported knowledge-graph relation {edge['relation']!r}")
        for key in (
            "id",
            "source",
            "target",
            "relation",
            "fact_id",
            "claim",
            "note_path",
            "section",
            "source_locator",
        ):
            if not isinstance(edge[key], str) or not edge[key].strip():
                raise ValueError(f"knowledge-graph edge lacks {key}")
        for key in ("claim_sha256", "source_sha256", "note_sha256", "section_sha256"):
            if not _valid_hash(edge[key]):
                raise ValueError(f"knowledge-graph edge has an invalid {key}")
        if hashlib.sha256(edge["claim"].encode("utf-8")).hexdigest() != edge["claim_sha256"]:
            raise ValueError("knowledge-graph claim_sha256 mismatch")
        if _UNSPECIFIED_LOCATOR_RE.search(edge["source_locator"]):
            raise ValueError("knowledge-graph edge has an inexact source locator")
        if not isinstance(edge["pdf_page"], int) or isinstance(edge["pdf_page"], bool) or edge["pdf_page"] <= 0:
            raise ValueError("knowledge-graph edge has an invalid PDF page")
        source_node = node_by_id[edge["source"]]
        for edge_key, node_key in (
            ("note_path", "note_path"),
            ("note_sha256", "note_sha256"),
            ("source_sha256", "source_sha256"),
        ):
            if edge[edge_key] != source_node[node_key]:
                raise ValueError(f"knowledge-graph edge {edge_key} disagrees with source node")
        if edge["id"] != _edge_id(edge):
            raise ValueError("knowledge-graph edge ID mismatch")
        if edge["id"] in edge_ids:
            raise ValueError(f"duplicate knowledge-graph edge ID {edge['id']!r}")
        edge_ids.add(edge["id"])
    if graph["paper_fact_count"] != sum(
        identity["paper_fact_count"] for identity in identities
    ):
        raise ValueError("knowledge-graph paper_fact_count mismatch")
    if graph["paper_fact_count"] < len(edges):
        raise ValueError("knowledge-graph edges exceed admitted paper facts")
    if graph["stats"] != graph_stats(graph):
        raise ValueError("knowledge-graph stats mismatch")
    if graph["stats"]["dangling_edges"] != 0:
        raise ValueError("knowledge graph contains dangling edges")
    if live_notes is not None and graph != build_graph(live_notes):
        raise ValueError("knowledge-graph artifact does not match the live current corpus")


def query_graph(graph: dict[str, Any], mode: str, query: str = "") -> list[dict[str, Any]]:
    """Query nodes or source-located neighbors in an active graph."""

    validate_graph(graph)
    if graph["corpus_status"] != "active":
        raise ValueError("current literature corpus is bootstrap-empty, so it cannot be queried")
    lowered = query.casefold()
    nodes = {node["id"]: node for node in graph["nodes"]}
    if mode == "paper":
        return [
            node
            for node in nodes.values()
            if node["type"] == "source"
            and (lowered in node["label"].casefold() or lowered in node["source_id"].casefold())
        ]
    if mode == "concept":
        return [
            node
            for node in nodes.values()
            if node["type"] != "source"
            and (lowered in node["label"].casefold() or lowered in node["id"].casefold())
        ]
    if mode == "neighbors":
        matched_ids = {
            node_id
            for node_id, node in nodes.items()
            if lowered in node_id.casefold() or lowered in node["label"].casefold()
        }
        return [
            {
                **edge,
                "source_label": nodes[edge["source"]]["label"],
                "target_label": nodes[edge["target"]]["label"],
            }
            for edge in graph["edges"]
            if edge["source"] in matched_ids or edge["target"] in matched_ids
        ]
    raise ValueError(f"unsupported query mode {mode!r}")


def render_concept_index(
    graph: dict[str, Any],
    *,
    output_path: Path = DEFAULT_CONCEPT_INDEX,
    repo_root: Path = REPO_ROOT,
) -> str:
    """Render a portable current, source-located concept index."""

    validate_graph(graph)
    nodes = {node["id"]: node for node in graph["nodes"]}
    stats = graph_stats(graph)
    lines = [
        "# Current literature concept index",
        "",
        "Generated from the explicit current corpus manifest. Only source-reviewed `paper_fact`",
        "relationships appear here. This is routing metadata; the cited PDF and locator remain",
        "the evidence.",
        "",
        f"- corpus status: {graph['corpus_status']}",
        f"- sources: {stats['sources']}",
        f"- concept nodes: {stats['concept_nodes']}",
        f"- source-located relationships: {stats['edges']}",
        f"- dangling relationships: {stats['dangling_edges']}",
        "",
    ]
    concept_nodes = sorted(
        (node for node in graph["nodes"] if node["type"] != "source"),
        key=lambda node: (node["type"], node["label"].casefold()),
    )
    if not concept_nodes:
        lines.extend(
            [
                "No concept is currently admitted. The bootstrap-empty reset state is intentionally",
                "not a completed literature gate.",
                "",
            ]
        )
        return "\n".join(lines)
    try:
        output_parent_rel = output_path.resolve().parent.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        output_parent_rel = "."
    for node in concept_nodes:
        lines.extend([f"## {node['label']} ({node['type']})", ""])
        relevant = [edge for edge in graph["edges"] if edge["target"] == node["id"]]
        for edge in relevant:
            source = nodes[edge["source"]]
            relative_note = posixpath.relpath(edge["note_path"], start=output_parent_rel)
            lines.append(
                f"- **{edge['relation']}** — {source['label']} — "
                f"`{edge['source_locator']}`, PDF p. {edge['pdf_page']} — {edge['claim']} "
                f"([{edge['note_path']}]({relative_note}))"
            )
        lines.append("")
    return "\n".join(lines)


def _resolve(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="write the artifact-verified current graph")
    build.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    build.add_argument("--output", type=Path, default=DEFAULT_GRAPH)
    build.add_argument("--allow-empty", action="store_true")

    stats = subparsers.add_parser("stats", help="print active graph statistics")
    stats.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    for mode in ("concept", "paper", "neighbors"):
        query = subparsers.add_parser(mode, help=f"query {mode} entries")
        query.add_argument("query")
        query.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    render = subparsers.add_parser("render-index", help="write the current concept index")
    render.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    render.add_argument("--output", type=Path, default=DEFAULT_CONCEPT_INDEX)
    render.add_argument("--allow-empty", action="store_true")
    validate = subparsers.add_parser("validate", help="validate a graph against the live corpus")
    validate.add_argument("artifact", type=Path, nargs="?", default=DEFAULT_GRAPH)
    validate.add_argument("--manifest", type=Path, default=Path("docs/papers/CURRENT_CORPUS.toml"))
    validate.add_argument("--allow-empty", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        args.repo_root = args.repo_root.resolve()
        manifest = _resolve(args.manifest, args.repo_root)
        allow_empty = bool(getattr(args, "allow_empty", False))
        notes = load_current_corpus(manifest, args.repo_root, allow_empty=allow_empty)
        graph = build_graph(notes)
        if args.command == "build":
            output = _resolve(args.output, args.repo_root)
            validate_graph(graph, live_notes=notes)
            write_json_atomic(output, graph)
            print(f"wrote {graph['stats']['edges']} source-located edges to {output}")
            return 0
        if args.command == "stats":
            print(json.dumps(graph["stats"], indent=2, sort_keys=True))
            return 0
        if args.command == "render-index":
            output = _resolve(args.output, args.repo_root)
            write_text_atomic(
                output,
                render_concept_index(graph, output_path=output, repo_root=args.repo_root),
            )
            print(f"wrote concept index to {output}")
            return 0
        if args.command == "validate":
            artifact = _resolve(args.artifact, args.repo_root)
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            validate_graph(payload, live_notes=notes)
            print(f"validated knowledge graph against live corpus: {artifact}")
            return 0
        results = query_graph(graph, args.command, args.query)
        if not results:
            print("No current source-located graph records matched.")
            return 0
        print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (LiteratureSchemaError, ValueError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

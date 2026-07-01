"""Hybrid vector-keyword store for QEC reading notes.

Build:  python -m qec_twin.rag.store --build
Query:  python -m qec_twin.rag.store --query "how does ZZ coupling affect surface code threshold?"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import chromadb
import numpy as np
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ── paths ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NOTES_DIR = REPO_ROOT / "docs" / "papers" / "reading_notes"
CONCEPT_INDEX = REPO_ROOT / "docs" / "papers" / "CONCEPT_INDEX.md"
CHROMA_DIR = REPO_ROOT / ".chroma_notes"
COLLECTION_NAME = "reading_notes_v2"

# ── embedding model ──────────────────────────────────────────────────────
_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dim, fast, good for scientific text
_EMBEDDER: Optional[SentenceTransformer] = None


def _get_embedder() -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer(_MODEL_NAME)
    return _EMBEDDER


# ── concept index parsing ────────────────────────────────────────────────


def _parse_concept_index() -> dict[str, dict[str, list[str]]]:
    """Parse CONCEPT_INDEX.md → {concept: {role: [filenames]}} and {filename: status}.

    Returns a tuple of (concept_map, status_map).
    """
    if not CONCEPT_INDEX.exists():
        return {}, {}

    text = CONCEPT_INDEX.read_text(encoding="utf-8")
    concept_map: dict[str, dict[str, list[str]]] = {}
    status_map: dict[str, str] = {}

    current_concept: Optional[str] = None

    for line in text.split("\n"):
        # Track concept sections
        if line.startswith("## ") and not line.startswith("## Statistics"):
            current_concept = line[3:].strip()
            if current_concept not in concept_map:
                concept_map[current_concept] = {"primary": [], "mentions": [], "context": []}
            continue

        if line.startswith("## Statistics"):
            current_concept = None
            continue

        # Parse entry lines:  - `filename` — symbol role — summary
        if current_concept and line.startswith("- `"):
            m = re.match(
                r"- `([^`]+)` — ([★⚠✗§]) (primary|mentions|context) — (.+)$", line
            )
            if m:
                fname_raw = m.group(1)
                symbol = m.group(2)
                role = m.group(3)
                # Normalize filename: strip .md suffix
                fname = fname_raw.replace(".md", "")
                concept_map[current_concept][role].append(fname)
                # Track status
                if fname not in status_map:
                    status_map[fname] = {
                        "★": "trusted",
                        "⚠": "needs-audit",
                        "✗": "untrusted",
                        "§": "synthesis",
                    }.get(symbol, "unknown")

    return concept_map, status_map


# ── chunking ─────────────────────────────────────────────────────────────


def _chunk_note(filepath: Path) -> list[dict]:
    """Split a markdown note into chunks by ## headings. Returns list of dicts."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    fname = filepath.stem

    # Split on ## headings
    sections = re.split(r"\n(?=## )", text)

    chunks = []
    for sec in sections:
        # Extract section title
        title_match = re.match(r"^## (.+)$", sec, re.MULTILINE)
        section_title = title_match.group(1).strip() if title_match else "(preamble)"

        # Skip empty sections
        body = sec.strip()
        if len(body) < 50:
            continue

        # Truncate very long sections to ~2000 chars (model context window friendly)
        if len(body) > 3000:
            # Try to break at paragraph boundary
            break_point = body[:3000].rfind("\n\n")
            if break_point > 1000:
                body = body[:break_point]

        chunks.append(
            {
                "filename": fname,
                "section": section_title,
                "text": body,
                "char_count": len(body),
            }
        )

    return chunks


# ── store ────────────────────────────────────────────────────────────────


class NoteStore:
    """Hybrid vector-keyword index over reading notes."""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False)
        )
        self.embedder = _get_embedder()
        self.concept_map, self.status_map = _parse_concept_index()

    @property
    def collection(self):
        return self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ── build ────────────────────────────────────────────────────────

    def build(self, force: bool = False) -> int:
        """Build the index from scratch. Returns number of chunks indexed."""
        if force:
            try:
                self.client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass

        coll = self.collection
        existing = coll.count()
        if existing > 0 and not force:
            print(f"Index already has {existing} chunks. Use --force to rebuild.")
            return existing

        # Delete and recreate
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        coll = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        # Collect all chunks
        all_chunks = []
        note_files = sorted(NOTES_DIR.glob("*.md"))
        print(f"Scanning {len(note_files)} reading notes...")

        for fp in note_files:
            fname = fp.stem
            chunks = _chunk_note(fp)
            status = self.status_map.get(fname, "unknown")
            for c in chunks:
                c["status"] = status
            all_chunks.extend(chunks)

        print(f"Total chunks: {len(all_chunks)}")

        # Batch embed and insert
        batch_size = 32
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i : i + batch_size]
            texts = [c["text"] for c in batch]
            embeddings = self.embedder.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            ).tolist()

            ids = [f"chunk_{j}" for j in range(i, i + len(batch))]
            metadatas = [
                {
                    "filename": c["filename"],
                    "section": c["section"][:200],
                    "status": c["status"],
                    "char_count": c["char_count"],
                }
                for c in batch
            ]

            coll.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            if (i + batch_size) % 64 == 0 or i + batch_size >= len(all_chunks):
                print(f"  indexed {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

        # Persist concept index as JSON for keyword retrieval
        concept_json = CHROMA_DIR / "concept_index.json"
        concept_json.write_text(
            json.dumps(self.concept_map, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"Done. {len(all_chunks)} chunks indexed in {CHROMA_DIR}")
        return len(all_chunks)

    # ── query ────────────────────────────────────────────────────────

    def query(
        self,
        q: str,
        top_k: int = 10,
        status_filter: Optional[str] = None,
        concept_filter: Optional[str] = None,
    ) -> list[dict]:
        """Hybrid retrieval: dense (embeddings) + sparse (concept keywords).

        Args:
            q: natural language query
            top_k: number of results
            status_filter: if set, only return chunks with this status
            concept_filter: if set, boost chunks matching this concept name
        """
        coll = self.collection
        if coll.count() == 0:
            print("Index is empty. Run --build first.")
            return []

        # Dense retrieval
        q_embedding = self.embedder.encode(
            [q], normalize_embeddings=True
        ).tolist()

        where_filter = None
        if status_filter:
            where_filter = {"status": status_filter}

        n_results = top_k * 2 if concept_filter else top_k
        results = coll.query(
            query_embeddings=q_embedding,
            n_results=min(n_results, coll.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Flatten
        hits = []
        if results["ids"] and results["ids"][0]:
            for j in range(len(results["ids"][0])):
                hits.append(
                    {
                        "chunk_id": results["ids"][0][j],
                        "text": results["documents"][0][j],
                        "filename": results["metadatas"][0][j]["filename"],
                        "section": results["metadatas"][0][j]["section"],
                        "status": results["metadatas"][0][j].get("status", "unknown"),
                        "distance": results["distances"][0][j],
                    }
                )

        # Keyword boost: if concept_filter given, boost chunks whose filenames
        # appear in that concept's primary/mentions lists
        if concept_filter and concept_filter in self.concept_map:
            primary_files = self.concept_map[concept_filter].get("primary", [])
            mentions_files = self.concept_map[concept_filter].get("mentions", [])
            boosted = set(primary_files + mentions_files)

            # Re-rank: move boosted hits up
            boosted_hits = [h for h in hits if h["filename"] in boosted]
            other_hits = [h for h in hits if h["filename"] not in boosted]
            hits = boosted_hits + other_hits

        return hits[:top_k]

    # ── format ───────────────────────────────────────────────────────

    def format_results(self, hits: list[dict]) -> str:
        """Format retrieval results with epistemic-status-aware citations."""
        if not hits:
            return "No results found."

        status_icon = {"trusted": "★", "needs-audit": "⚠", "untrusted": "✗", "synthesis": "§", "unknown": "?"}

        lines = []
        for i, h in enumerate(hits):
            icon = status_icon.get(h["status"], "?")
            lines.append(f"### [{i+1}] `{h['filename']}` {icon}  (dist={h['distance']:.3f})")
            lines.append(f"**Section:** {h['section']}")
            lines.append("")
            # Show first ~500 chars
            excerpt = h["text"][:600].replace("\n", " ")
            lines.append(excerpt + ("..." if len(h["text"]) > 600 else ""))
            lines.append("")

        return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────


def build_index(force: bool = False) -> NoteStore:
    """Build the index. Returns the store for subsequent queries."""
    store = NoteStore()
    store.build(force=force)
    return store


def query(q: str, top_k: int = 10, concept: Optional[str] = None) -> str:
    """Query the index. Returns formatted results."""
    store = NoteStore()
    if store.collection.count() == 0:
        return "Index is empty. Run with --build first."

    hits = store.query(q, top_k=top_k, concept_filter=concept)
    return store.format_results(hits)


# ── main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="QEC Reading Notes RAG")
    ap.add_argument("--build", action="store_true", help="Build (or rebuild) the index")
    ap.add_argument("--force", action="store_true", help="Force rebuild even if index exists")
    ap.add_argument("--query", type=str, default=None, help="Query string")
    ap.add_argument("--top-k", type=int, default=10, help="Number of results")
    ap.add_argument("--concept", type=str, default=None, help="Boost results for this concept")
    ap.add_argument("--interactive", "-i", action="store_true", help="Interactive query mode")
    args = ap.parse_args()

    store = NoteStore()

    if args.build or args.force:
        store.build(force=args.force)

    if args.query:
        hits = store.query(args.query, top_k=args.top_k, concept_filter=args.concept)
        print(store.format_results(hits))

    elif args.interactive:
        if store.collection.count() == 0:
            print("Index is empty. Building now...")
            store.build(force=True)

        print(f"\nQEC Reading Notes RAG  ({store.collection.count()} chunks, {len(store.concept_map)} concepts)")
        print("Type 'exit' to quit. Use 'concept:NAME' to filter by concept.\n")

        while True:
            try:
                q = input("Query> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nDone.")
                break

            if not q:
                continue
            if q.lower() in ("exit", "quit", "q"):
                break

            # Parse concept filter: "concept:ZZ coupling rest of query"
            concept_filter = None
            if q.startswith("concept:"):
                parts = q.split(" ", 1)
                concept_filter = parts[0].replace("concept:", "")
                q = parts[1] if len(parts) > 1 else ""

            hits = store.query(q, top_k=args.top_k, concept_filter=concept_filter)
            print(store.format_results(hits))
            print("─" * 60)

    elif not args.build and not args.force:
        ap.print_help()

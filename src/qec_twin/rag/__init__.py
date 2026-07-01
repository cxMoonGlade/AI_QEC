"""RAG (Retrieval-Augmented Generation) over QEC reading notes.

Builds a hybrid vector-keyword index from docs/papers/reading_notes/*.md,
with epistemic-status-aware retrieval and CONCEPT_INDEX.md integration.

Usage:
    python -m qec_twin.rag.build   # one-time index build
    python -m qec_twin.rag.query   # interactive query loop
"""

from qec_twin.rag.store import NoteStore, build_index, query

__all__ = ["NoteStore", "build_index", "query"]

# Literature sources and evidence records

This directory separates source objects from evidence records.

- PDF, text, HTML, rendered pages, and acquisition provenance are local source caches. They are
  preserved but are not evidence by directory presence.
- `reading_notes/` is the candidate-record directory. It still contains excluded legacy notes
  during the reset; directory presence never means admission.
- `CURRENT_CORPUS.toml` is the explicit current-corpus manifest. Only a schema-valid,
  source-only-reviewed note listed there may enter current RAG/KG publication.
- `CONCEPT_INDEX.md` is generated from explicit source-located relationships in admitted notes.
  It is a discovery surface, never a substitute for the paper.
- Simulator application, extrapolation, and design choices belong in a claim or audit packet under
  `docs/simulator_validation/`; the literature indexer never scans those packets.

The default retrieval path is fail-closed:

```bash
conda run -n ecs python tools/literature_rag.py audit --schema-only
conda run -n ecs python tools/literature_rag.py query "<mechanism or observable>" --top-k 12
conda run -n ecs python tools/literature_kg.py stats
conda run -n ecs python tools/literature_kg.py concept "<concept>"
```

An audit reports `validated_count` / `validated` and states whether it ran in
`artifact_verified` or `schema_only` mode. Schema-only inspection is useful for corpus diagnosis,
but it is not an admission or scientific-completion gate.

The tools build only from notes explicitly enumerated by `CURRENT_CORPUS.toml`. They do not open
unlisted legacy notes, project syntheses, `.chroma_notes/`, or `outputs/knowledge_graph/`. Legacy
notes and syntheses remain discovery-only quarantine material and may not be copied into a new
record. A retrieval hit is routing information: reopen the named source object and verify the exact
locator before using the claim.

The current manifest is intentionally empty while clean-room reading is bootstrapped. Empty RAG,
KG, and concept-index outputs prove safe isolation only; they do not prove literature coverage,
source closure, or Phase-5 completion.

To add an evidence record, acquire a versioned source, record its SHA-256, read the full text,
visually inspect every load-bearing formula page, complete an operation replay, and write a note
using the contract in [`reading_notes/README.md`](reading_notes/README.md). A note that lacks any
required field remains excluded by normal validation. Structural validation can prove that fields,
hashes, and evidence-record boundaries are present; it cannot prove that a human reconstruction is
semantically faithful to the paper. Source-only review is therefore required before adding the note
to `CURRENT_CORPUS.toml`.

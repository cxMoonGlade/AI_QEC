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

The current manifest is active and deliberately small. It contains only records that completed the
current source-only schema and review gate. The many other notes in `reading_notes/` remain excluded
legacy or candidate material. A non-empty RAG, KG, or concept index proves publication integrity for
the admitted records only; it does not prove literature coverage or closure for a new claim.

To add an evidence record, acquire a versioned source, record its SHA-256, read the full text,
visually inspect every load-bearing formula page, complete an operation replay, and write a note
using the contract in [`reading_notes/README.md`](reading_notes/README.md). A note that lacks any
required field remains excluded by normal validation. Structural validation can prove that fields,
hashes, and evidence-record boundaries are present; it cannot prove that a human reconstruction is
semantically faithful to the paper. Source-only review is therefore required before adding the note
to `CURRENT_CORPUS.toml`.

## Rehydrate the current source cache

The PDFs are intentionally ignored by git. The active corpus can be rehydrated with these pinned
source URLs:

```bash
curl -L --fail https://arxiv.org/pdf/1804.09796v2 -o docs/papers/1804.09796v2.pdf
curl -L --fail https://arxiv.org/pdf/2501.17913v2 -o docs/papers/2501.17913v2.pdf
curl -L --fail https://arxiv.org/pdf/1901.05824v3 -o docs/papers/1901.05824v3.pdf
curl -L --fail https://arxiv.org/pdf/1405.3259v2 -o docs/papers/1405.3259v2.pdf
curl -L --fail https://arxiv.org/pdf/1801.05390v2 -o docs/papers/1801.05390v2.pdf
curl -L --fail https://arxiv.org/pdf/2107.06635v1 -o docs/papers/2107.06635v1.pdf
curl -L --fail https://scipost.org/SciPostPhysLectNotes.86/pdf \
  -o docs/papers/naumann_ipeps_variational_lecture_notes_2024.pdf
curl -L --fail https://scipost.org/SciPostPhysCodeb.52/pdf \
  -o docs/papers/rams_yastn_scipost_codebases_52.pdf
curl -L --fail https://harvest.aps.org/v2/journals/articles/10.1103/PhysRevA.97.032306/fulltext \
  -o docs/papers/wood_gambetta_leakage_characterization_pra_97_032306.pdf
```

Then run the artifact-verified builders; SHA mismatches fail closed:

```bash
conda run -n ecs python tools/literature_rag.py build
conda run -n ecs python tools/literature_kg.py build
conda run -n ecs python tools/literature_kg.py render-index
conda run -n ecs python -m pytest -q tests/test_literature_tools.py
```

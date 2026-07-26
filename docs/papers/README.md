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

The current manifest is active and deliberately curated. It includes the load-bearing MPS/PEPS
carrier-precision set, the Wood--Gambetta leakage baseline, and the four source-only records in the
leakage-frame closure packet. The many other notes in `reading_notes/` remain excluded legacy or
non-load-bearing material. A non-empty RAG, KG, or concept index proves publication integrity for
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
curl -L --fail https://arxiv.org/pdf/2607.01323v1 \
  -o docs/papers/froehlich_tensor_jump_method_2607.01323.pdf
curl -L --fail https://arxiv.org/pdf/2501.17913v2 -o docs/papers/2501.17913v2.pdf
curl -L --fail https://arxiv.org/pdf/1901.05824v3 -o docs/papers/1901.05824v3.pdf
curl -L --fail https://arxiv.org/pdf/1405.3259v2 -o docs/papers/1405.3259v2.pdf
curl -L --fail https://arxiv.org/pdf/1801.05390v2 -o docs/papers/1801.05390v2.pdf
curl -L --fail https://arxiv.org/pdf/2012.12233v1 -o docs/papers/2012.12233v1.pdf
curl -L --fail https://arxiv.org/pdf/1412.5746v2 \
  -o docs/papers/werner_positive_tensor_network_open_systems_1412.5746.pdf
mkdir -p outputs/papers/pepo_survey
curl -L --fail https://arxiv.org/pdf/2012.03095v2 \
  -o outputs/papers/pepo_survey/2012.03095.pdf
curl -L --fail https://arxiv.org/pdf/2507.11424v2 \
  -o outputs/papers/pepo_survey/2507.11424.pdf
curl -L --fail \
  https://harvest.aps.org/v2/journals/articles/10.1103/PhysRevLett.98.140506/fulltext \
  -o docs/papers/schuch_wolf_verstraete_cirac_prl_98_140506.pdf
curl -L --fail https://harvest.aps.org/v2/journals/articles/10.1103/PhysRevA.97.032306/fulltext \
  -o docs/papers/wood_gambetta_leakage_characterization_pra_97_032306.pdf
curl -L --fail https://arxiv.org/pdf/1306.0925v2 -o docs/papers/1306.0925v2.pdf
curl -L --fail https://arxiv.org/pdf/1905.12731v1 -o docs/papers/1905.12731v1.pdf
curl -L --fail https://arxiv.org/pdf/2002.07119v1 -o docs/papers/2002.07119v1.pdf
curl -L --fail https://arxiv.org/pdf/2607.17204v1 -o docs/papers/2607.17204v1.pdf
```

Then run the artifact-verified builders; SHA mismatches fail closed:

```bash
conda run -n ecs python tools/literature_rag.py build
conda run -n ecs python tools/literature_kg.py build
conda run -n ecs python tools/literature_kg.py render-index
conda run -n ecs python -m pytest -q tests/test_literature_tools.py
```

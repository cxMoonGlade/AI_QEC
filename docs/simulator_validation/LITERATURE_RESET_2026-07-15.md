# Literature reset audit — Phase 5A

Status: Phase 5A isolation/bootstrap complete; evidence admission and the overall literature reset
remain in progress.

This ledger records the current corpus cut, retrieval contracts, and dry-run dispositions. It is
an operational audit, not scientific authority. Source papers and exact source locators remain the
evidence.

## Safety preflight

- Repository: `/home/cx/AI_QEC/AI_QEC`, branch `Dev-F`.
- The tracked worktree was clean before Phase 5A edits.
- No PDF, text extraction, HTML source, provenance JSON, or rendered formula page was deleted.
- Existing vector and graph caches were read only for diagnosis. The current tools never open them.
- No simulator formula, numerical value, tolerance, or physical evolution operation changed. The
  quantum-bath diagnostic's public result contract did change: its overstrong result key was hard
  cut to `inequality_violated` with no alias, and `False` is now explicitly inconclusive. The source
  citation was corrected to Bäcker et al., *Phys. Rev. Lett.* **132**, 060402 (2024),
  arXiv:2310.01205; theorem applicability remains pending a source-hypothesis audit.

## Live corpus inventory

| surface | exact inventory | disposition |
|---|---:|---|
| `docs/papers/` | 331 files: 253 Markdown, 59 PDF, 16 text, 2 HTML, 1 TOML manifest | source objects preserved; manifest added |
| `docs/papers/reading_notes/` | 248 tracked Markdown: 247 content notes plus routing README | every content note excluded from current retrieval |
| top-level `docs/papers/2412.16092_NOTES.md` | 1 tracked content note | denied; no current source/test/authority consumer |
| content-note artifacts in total | 248 | 0 current-schema notes |
| `docs/papers/CURRENT_CORPUS.toml` | explicit current-corpus manifest with 0 notes | bootstrap-safe empty state; not a completion gate |
| `.chroma_notes/` | 127 files, 123 MiB | quarantined derived cache; Phase 6 purge candidate |
| `outputs/knowledge_graph/` | 6 files, 5.2 MiB | quarantined derived tools/graphs; Phase 6 purge candidate |

There are 248 content-note artifacts because the 247 files under `reading_notes/` and the one
top-level note are distinct. The machine-generated corpus audit lists all 247 directory members;
the top-level note is the single additional dry-run member:

- `outputs/literature/phase5a_corpus_audit.json`
- SHA-256 `70d7ac25bafaeb2579a693409c47e6b05c03e6cd1fefb13b01866431a3380dff`
- additional member: `docs/papers/2412.16092_NOTES.md`

## Why no existing note is admitted

No content note contains the required `paper_fact` / `literature_gap` section contract. Direct
file-level inspection found:

| marker | files |
|---|---:|
| `[paper]` | 191 |
| `[ours]` | 168 |
| retired runtime namespace | 92 |
| retired numbered mechanism tokens | 44 |
| retired role-vocabulary lexical quarantine hits | 93 |
| retired ADR 0002–0007 references | 16 |

The conservative union of `[ours]` and lexical internal-product quarantine markers covers 241/248
files. This is a fail-safe isolation count, not a claim that all 241 files contain a contextually
confirmed retired-product assertion: in particular, the counted role words can be paper-local terms.
One further file is an untagged project overview, and the remaining six also contain untyped project
analysis. Even the single note with paper tags but none of those direct markers contains an untyped
implementation-adoption section. Clean-room reconstruction is therefore safer than extracting
apparently clean paragraphs from mixed files.

Bare paper-local `F2`, `F0/Fn`, or algorithm-stage notation was not classified as product pollution.
Those symbols can be legitimate source notation and must be interpreted in context.

## Diagnosed cache failures

The quarantined vector cache contains 2,399 chunks from 246 filenames. Its default query did not
apply an epistemic-status filter. Of 1,373 chunks labeled `trusted` by the file-level index, 251
contain `[ours]`, 87 contain the retired namespace, 133 contain retired role vocabulary, and 138
contain numbered mechanism tokens. The cache has no artifact schema, source hash, note hash, model
hash, or corpus manifest. Twenty-four of twenty-five HNSW directories are orphaned rebuild residue.

The quarantined full graph contains 356 nodes and 30,770 relationships. All 30,770 relationships
lack an exact source locator, and 1,656 are dangling. Most edges are keyword/topic co-membership,
not paper-stated scientific relationships. It has no schema or freshness contract.

These caches are discovery residue only. They are neither migrated nor used as an input to the
current tools.

## Current fail-closed contracts

The tracked developer tools are:

- `tools/literature_schema.py` — strict note/provenance parser and atomic artifact writer;
- `tools/literature_rag.py` — deterministic live lexical retrieval over `paper_fact` only;
- `tools/literature_kg.py` — explicit source-to-concept graph with exact locators and zero dangling
  endpoints.

An admitted note must provide the current schema, source ID/version/URI, repository-relative source
artifact, source SHA-256, complete/persisted status, `review_scope = "full_text"`, completed
operation replay, a hashed audit packet, visually checked pages, and source-only reviewer/date
metadata. Every H2 is exactly one evidence record whose first four body fields are `Fact ID`, exact
`Source locator`, `PDF page`, and `Claim`; a `literature_gap` additionally declares
`Gap scope: source_local`. A current-schema note with a corrupted field fails the build; it is not
silently skipped. Markdown without the schema is excluded and cannot fall through to a heuristic
parser.

`docs/papers/CURRENT_CORPUS.toml` is the explicit publication boundary. A structurally valid note is
still excluded until that manifest lists it after source-only review. Corpus audits use
`validated_count` / `validated` and state `verification_mode = "artifact_verified"` or
`"schema_only"`; schema-only results are diagnostic and cannot admit evidence.

RAG chunks carry source, note, section, and chunk hashes plus exact locators. Only `paper_fact`
sections are indexed. `literature_gap` remains visible in its source note but is not returned as a
claim. Project application belongs in a separate claim/audit packet and is never indexed.

KG relationships must be explicitly declared by an admitted note and point by `fact_id` to one
`paper_fact` evidence record. They do not duplicate locator or claim text. Automatic same-topic
relationships are not scientific edges. A relation label must name a source concept present in the
referenced claim, never a project-defined target. Any dangling endpoint blocks publication.

These are structural and provenance controls. They block known mixed-corpus routes, but no parser
can prove that an unmarked natural-language reconstruction is semantically faithful to a paper.
Independent source-only review remains a required admission gate.

## Current generated state

The strict cut intentionally starts empty:

| artifact | current state | SHA-256 |
|---|---|---|
| `outputs/literature/rag_index.json` | 0 notes, 0 `paper_fact` chunks | `edf692578deffcfe81e21764625e9ac12b999d8d5532370a557a14a5ab0328bd` |
| `outputs/literature/knowledge_graph.json` | 0 nodes, 0 edges, 0 dangling | `a3beb9448f21786f956a85a07ddea53de733e271ca87b521934805afdc87b1c9` |
| `docs/papers/CONCEPT_INDEX.md` | 0 admitted concepts | `ef32b78169846dd7ca5f06e1a7f2538f20fea84d3a8aa10e7b3da73b6746b58f` |
| `docs/papers/CURRENT_CORPUS.toml` | 0 explicitly admitted notes | `3085b73cbdddecccfa90d9942d77dc8d1932e5586dd04200d80ddc03db2e445a` |

Empty is the correct safe state before clean-room rereading. It proves isolation, not successful
non-empty publication, evidence coverage, Phase-5 scientific closure, or formula-audit readiness.

## Dry-run dispositions

No item in this section was deleted in Phase 5A.

1. **Withdraw from the active corpus:** all 248 content-note artifacts. The exact 247-file directory
   manifest plus the one top-level note are named above. Git history is the only note archive.
2. **Rebuild only when load-bearing:** create a fresh current-schema note from the versioned full
   text, rendered formula pages, and recorded hash. Do not mechanically salvage tagged paragraphs.
3. **Preserve source objects:** all original PDFs, text extractions, HTML, provenance JSON, and
   formula-page renderings. Generated reading packages may be purged only after their canonical
   source objects and hashes are reconciled in the Phase-6 manifest.
4. **Purge derived retrieval products in Phase 6:** `.chroma_notes/`,
   `outputs/knowledge_graph/`, mutation snapshots of the removed RAG package, stale environment
   freezes, and retired product workflow/skill outputs. The tracked neutral tools replace their
   function; no compatibility reader is retained.

Explicit project-only note candidates include the top-level 2412.16092 note, the coherent-noise
survey, the Bayes-TN overview, the memory-witness synthesis preregistration, two numbered operator
grounding notes, and the direction-B overview. Eight duplicate-source families were also found;
each source may earn at most one clean full-text note after rereading.

## Next gated batch

The first scientific batch is limited to the highest-risk current attribution boundary:

1. Wood and Gambetta, arXiv:1704.03081 — separate the paper's leakage diagnostics from the
   project's qutrit GKSL construction.
2. Miao et al., arXiv:2211.04728 — establish exactly which effective coupling, population-transfer,
   and scale statements are source facts.
3. Varbanov et al., arXiv:2002.07119 — establish the Appendix-H/B multi-level transport model and
   its pulse/device scope.

Each paper requires version/hash verification, full-text traversal, visual formula checks, a
source-only note, and a separate operation-replay/application packet. The batch must close before
any source comment or public physical name is strengthened. Retained PEPO/PEPS literature is a
separate later batch; its current positive full-record claim is already withheld, and the visible
PEPS/FET failure is unchanged.

## Phase-5A gates

- literature tool corruption/fail-closed tests: `64 passed`;
- current scope boundary: `8 passed`;
- combined literature + scope batch: `72 passed`;
- quantum-memory-witness public-contract gates: `12 passed` in the focused unit suite plus
  `14 passed` in the package-owner suite;
- current source scan for repository retirement/compatibility paths: zero matches;
- current RAG query: no current `paper_fact` result and no cache write;
- current KG: zero dangling relationships;
- same-named `.agents` / `.claude` literature skills and templates: byte-identical after the
  command/schema reset.
- full repository collection: `2,204 tests collected`;

Phase 5A establishes isolation, an explicit empty manifest, and execution contracts. Its empty
bootstrap is not a scientific-completion gate. Phase 5 remains open until the required load-bearing
notes pass independent source-only review, enter `CURRENT_CORPUS.toml`, and make the graph/retrieval
gates pass on non-empty evidence.

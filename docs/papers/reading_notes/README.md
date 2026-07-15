# Candidate full-text literature records

This directory is a candidate surface, not the current corpus. Only files satisfying
`error_coupling_simulator.literature.note.v1`, completing source-only review, and appearing in
`../CURRENT_CORPUS.toml` enter local retrieval. All other Markdown is excluded without a fallback
parser.

Each note must provide TOML front matter with:

- versioned source identity and URI;
- repository-relative source artifact and exact SHA-256;
- title and publication status;
- `read_status = "complete"` and `evidence_status = "persisted"`;
- `review_scope = "full_text"` and `operation_replay_status = "complete"`;
- a repository-relative `audit_packet` plus its exact `audit_packet_sha256`;
- `admission_status = "source_only_reviewed"`, an `admission_reviewer`, and an
  `admission_date`;
- a non-empty list of visually checked PDF pages as positive integers;
- optional explicit relationships, each tied to one admitted evidence record by `fact_id`.

Every level-two section must represent exactly one evidence record and is typed as either
`paper_fact` or `literature_gap`. Its first four body lines are, in order, `Fact ID`,
`Source locator`, `PDF page`, and `Claim`. A `literature_gap` record has the additional fifth line
`Gap scope: source_local`:

```markdown
## Model definition [paper_fact]
Fact ID: model-equation-3
Source locator: Sec. II, Eq. (3)
PDF page: 4
Claim: The declared model evolves a binary latent state at rate gamma.

<source-faithful reconstruction>

## Unsupported magnitude [literature_gap]
Fact ID: gap-device-independent-magnitude
Source locator: Sec. VI, limitations
PDF page: 19
Claim: This source does not establish a device-independent magnitude for the stated regime.
Gap scope: source_local

<what this source does not establish>
```

Do not bundle several independently locatable claims into one H2. `paper_fact` contains only the
single declared source claim and its source-checked reconstruction.
`literature_gap` records a source-local absence or limitation. Cross-source search exhaustion can
only be declared by a completed closure packet. Project application, code mapping, extrapolation,
and design decisions are not note content; put them in a separate claim or audit packet.

Relationships repeat neither locator nor claim text. They identify the source evidence record:

```toml
[[relations]]
predicate = "defines"
object_id = "binary-latent-source-model"
object_type = "model"
object_label = "Binary latent source model"
fact_id = "model-equation-3"
```

The `object_label` must name a source concept present in that evidence record's `Claim`; it must
not introduce a project-defined target or interpretation.

Validation and retrieval:

```bash
conda run -n ecs python tools/literature_rag.py audit --schema-only
conda run -n ecs python tools/literature_rag.py build
conda run -n ecs python tools/literature_kg.py build
conda run -n ecs python tools/literature_kg.py render-index
```

The build and query surfaces intentionally fail while the manifest remains `bootstrap_empty`.
`--allow-empty` is restricted to regenerating declared reset artifacts; it never converts an empty
corpus into an evidence or completion gate.

The RAG index contains only `paper_fact` sections. Every chunk carries source, note, section, and
chunk hashes plus exact locators. The knowledge graph accepts only explicit relationships with the
same provenance and refuses publication when any endpoint is dangling.

The manifest begins empty. Empty publication proves that legacy material cannot leak into current
retrieval; it is a bootstrap safety condition, not evidence coverage or literature closure.
Schema checks enforce structure and known corruption barriers. They cannot determine whether a
plausible sentence accurately represents the source, so an independent source-only reviewer must
compare every claim and locator with the versioned artifact before manifest admission.

# Independent source admission rereview — Qian et al., arXiv:2405.09217v2

Date: 2026-07-27

Reviewer ID:
`independent_qian_2405_source_rereview_2026_07_27`

Verdict: **PASS for source-only admission**

This verdict authorizes only admission of the bounded source facts and
source-local gaps in the reviewed evidence pair. It does not authorize a
CAPEPS, PEPS, QEC-instrument, Record-correctness, or efficiency claim.

## Independence and review procedure

I read the complete `deep-read-paper` skill and reading-note template before
reviewing the evidence pair. I then:

1. verified the pinned source object and provenance;
2. read the complete six-page `2405.09217v2` paper before opening the note or
   audit;
3. rendered and visually inspected PDF pages 1--6, including Eqs. (1)--(6),
   Figs. 1--4, the 720-candidate sentence, the benchmark reference qualifiers,
   the runtime sentence, the PEPS sentence, and notes [52] and [54];
4. opened the revised source-only note and audit only after the source review;
5. checked every evidence-record claim, locator, PDF page, gap boundary,
   assigned closure row, and operation-replay row against the PDF.

I did not use
`QIAN_2405_09217_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md`, any project
summary, or a previous reviewer judgment as evidence for this verdict.
Extracted text was used only for traversal and full-text search; formula and
figure judgments came from the rendered PDF.

## Reviewed object identity

| object | path | SHA-256 / result |
|---|---|---|
| pinned source | `docs/papers/2405.09217v2.pdf` | `13e1369ff2817d5dc20c595716b2f89a505c239d245603ef89811b51e672e2b7` |
| source-only note | `docs/papers/reading_notes/qian_clifford_augmented_dmrg_2405.09217v2_source_review.md` | `4431d0bd898185e3ca1afd59e13e46334f0b36dda240cfdcea88bb99978b0a6c` |
| audit packet | `docs/simulator_validation/QIAN_2405_09217_SOURCE_ONLY_AUDIT_2026-07-27.md` | `052b502f41c34737536f345ec099a4850f746e6e5953200e2ec6028ff30a9625` |
| note-declared source hash | note front matter | exact match |
| note-declared audit hash | note front matter | exact match |
| PDF structure | independent byte and parser checks | `%PDF-1.5`, six pages, terminal `%%EOF` |
| visual coverage | independent rendering | pages 1, 2, 3, 4, 5, and 6 |

The provenance record identifies `arxiv_id = "2405.09217v2"`,
`version_status = "pinned-v2"`, and the same source SHA-256.

## Load-bearing ambiguity checks

### Quantitative local objective

PDF page 2 says that the two-qubit Clifford is applied before SVD to minimize
truncation loss. PDF page 3 says this is equivalent, in the paper's wording,
to minimizing the discarded singular values. The source does not state an
aggregation of those values, a squared discarded weight, a norm, a retained
rank convention, a Rényi-2 objective, or a purity objective.

The note preserves exactly this boundary in
`qian-local-truncation-criterion`,
`qian-gap-objective-scalarization`, and `qian-gap-renyi-two`. The audit also
marks the qualitative source criterion `closed`, exact scalarization
`missing`, and a Qian-attributed Rényi-2 objective
`contradicted_as_citation_claim`.

Result: **PASS**. No quantitative objective has been invented.

### The reported number 720

PDF page 3 reports “a total of 720 two-qubit Clifford circuits,” followed by
the parenthetical “excluding phase redundancy, as they do not affect singular
values.” The paper does not define the equivalence relation, enumerate the
representatives, or prove quotient completeness.

The note consistently calls 720 the paper-reported candidate count and
separately records the missing quotient definition and completeness proof.
The audit applies the same limitation in its closure row, replay assumption,
project application, and kill condition.

Result: **PASS**. The evidence pair does not promote 720 into a
group-theoretically complete quotient.

### Benchmark and resource qualifiers

| source statement | required qualifier | evidence-pair treatment | result |
|---|---|---|---|
| Fig. 2 energy errors | shown \(4\times4\) through \(10\times10\), OBC, \(J_2=0\), with QMC references | preserved in `qian-energy-benchmark-j2-zero` | PASS |
| Fig. 4 energy errors | shown \(8\times8\), OBC/CBC, \(J_2=0,0.5\), with a \(D=10000\) MPS reference energy | preserved in `qian-energy-benchmark-extended` | PASS |
| Fig. 3 entropy | center-bond entropy in the residual MPS part for the shown workloads | preserved in `qian-residual-entropy-threshold` | PASS |
| runtime ratio about 1.2 | reported \(10\times10\) OBC Heisenberg calculation; ratio said to approach one with increasing \(D\) | preserved as one workload-specific observation | PASS |
| PEPS | one future-direction sentence about extending the Fig. 1(b) framework | explicitly not treated as an implementation, benchmark, proof, or complexity result | PASS |

The audit expressly rejects arbitrary-model, asymptotic, PEPS, XZZX,
branching, and Record-efficiency transfers.

## Claim-by-claim source-note verification

| Fact ID | independent PDF check | locator/page check | verdict |
|---|---|---|---|
| `qian-source-identity` | title, authors, six-page v2 object, and title-page date are correct | p. 1 title/date/footer | PASS |
| `qian-selection-scope` | Clifford-augmented MPS/DMRG and spin-model ground-state workload scope is correct | p. 1 abstract | PASS |
| `qian-mps-notation` | rank-three \(M_i^{\sigma_i}\), physical \(d\), auxiliary \(D\) are stated | p. 2, Eq. (1) | PASS |
| `qian-camps-ansatz` | \(\lvert\mathrm{CAMPS}\rangle=C\lvert\mathrm{MPS}\rangle\) is the source definition | p. 2, Eq. (2), Fig. 1(a) | PASS |
| `qian-pauli-hamiltonian` | \(H=\sum_i a_iP_i\) with \(N\)-site Pauli strings is stated | p. 2, Eq. (3) | PASS |
| `qian-effective-hamiltonian` | two-site \(H_{\mathrm{eff}}\) and \(H_{\mathrm{eff}}\lvert\phi\rangle=E_g\lvert\phi\rangle\) are stated | p. 2, Eq. (4) and following text | PASS |
| `qian-clifford-before-svd` | the local Clifford precedes SVD and truncation | p. 2, Fig. 1(b) and final paragraph | PASS |
| `qian-reported-candidate-count` | the paper reports 720 after what it calls phase redundancy | p. 3, local-search paragraph | PASS |
| `qian-local-truncation-criterion` | truncation loss/discarded-singular-value wording is exact and remains qualitative | p. 3, local-search paragraph | PASS |
| `qian-hamiltonian-update` | \(H'=CHC^\dagger\) and Pauli-to-Pauli conjugation are stated | p. 3, Eq. (5) and following text | PASS |
| `qian-energy-benchmark-j2-zero` | the bounded OBC, \(J_2=0\), QMC-referenced comparison is accurate | p. 3, Fig. 2 and text | PASS |
| `qian-energy-benchmark-extended` | the bounded \(8\times8\), OBC/CBC, \(J_2=0,0.5\), \(D=10000\)-MPS-reference comparison is accurate | p. 4, Fig. 4 and preceding text | PASS |
| `qian-residual-entropy-threshold` | the below-threshold similarity and above-threshold CAMPS saturation are source-reported | pp. 3--4, Fig. 3 discussion and caption | PASS |
| `qian-runtime-observation` | the workload-specific ratio about 1.2 and trend toward one are exact | p. 4, Discussion | PASS |
| `qian-peps-future-direction` | the source makes only the stated extension suggestion | p. 4, Discussion | PASS |
| `qian-local-minimum-warning` | local trapping is explicitly warned | p. 4, Discussion | PASS |
| `qian-small-bond-local-minimum` | the empirical small-\(D\) warning and recommendation are in note [54] | p. 6, Ref. [54] | PASS |
| `qian-gap-objective-scalarization` | no exact scalarization, norm, discarded-weight formula, or retained-rank convention is supplied | full text, anchored at p. 3 | PASS |
| `qian-gap-clifford-quotient` | no equivalence relation, representative enumeration, or completeness proof is supplied | p. 3, 720 paragraph | PASS |
| `qian-gap-renyi-two` | no Rényi-2 or purity search objective is stated or derived | full text, anchored at p. 3 | PASS |
| `qian-gap-instrument` | no selective measurement, Born branching, reset, trajectory, syndrome Record, or Record-law result appears | full-text scope, anchored at p. 5 conclusion | PASS |
| `qian-gap-peps-result` | no PEPS construction, contraction, correctness, benchmark, or efficiency result is supplied | p. 4, PEPS sentence | PASS |

All 22 evidence records have unique Fact IDs, allowed epistemic classes,
source locators, in-range PDF pages, one bounded claim, and the required
first-field order. Each of the five `literature_gap` records includes
`Gap scope: source_local`. The note defines no relation records, so there is
no relation-to-fact or object-label mismatch to resolve.

## Audit-packet verification

The ten assigned closure rows agree with the source and the note:

- CAMPS ansatz, qualitative local criterion, reported 720-candidate procedure,
  Hamiltonian conjugation, selected benchmark observations, runtime
  observation, and local-minimum warning are closed only at the stated source
  scope;
- exact objective scalarization, a defined Clifford quotient, a PEPS
  mechanism/result, and a measurement--reset--Record bridge remain missing;
- a Qian-attributed Rényi-2 objective is rejected as a citation claim.

The six operation-replay rows follow the source order:
two-site effective solve, reported candidate evaluation, qualitative candidate
selection, SVD truncation, Hamiltonian conjugation, and continuation of the
DMRG sweep. The audit exposes the missing scalarization and quotient
assumption instead of silently filling either one. Its project-application
section and kill conditions do not leak into the source-only note.

Result: **PASS**.

## Schema and hash verdict

- The source hash in the note matches the reviewed PDF.
- The audit hash in the note matches the reviewed audit packet.
- The title, arXiv identifier, pinned version URI, publication status, page
  coverage, and artifact paths are internally consistent.
- The note body follows
  `error_coupling_simulator.literature.note.v1`.
- Before this rereview, the project validator excludes the note for exactly
  one expected reason:
  `admission_status must be 'source_only_reviewed'`.
- The current pending metadata correctly prevents accidental admission before
  this review; it is not a scientific or structural failure.

## Admission authorization

**Authorization granted.** The main agent may now:

1. update the audit packet to identify this rereview as the independent
   admission basis and change its pending evidence-status wording to the
   admitted source-only state;
2. recompute the audit packet SHA-256;
3. update the note metadata to:
   - `admission_status = "source_only_reviewed"`;
   - `admission_reviewer = "independent_qian_2405_source_rereview_2026_07_27"`;
   - `admission_date = "2026-07-27"`;
   - the recomputed `audit_packet_sha256`;
4. run the artifact-verified literature audit;
5. rebuild `docs/papers/CURRENT_CORPUS.toml` so the valid note is included,
   then rerun the corpus/RAG/KG integrity checks.

This authorization is valid only if the 22 reviewed claims and their locators
remain unchanged. Any semantic edit requires another independent source
review. Manifest inclusion must occur only after the updated note passes the
artifact-verified validator.

## Final bounded verdict

- `read_status: complete`
- `evidence_status: persisted`
- source-only evidence pair: `PASS`
- admission authorization: `GRANTED`
- CAPEPS/PEPS/QEC/Record extrapolation authorization: `NOT GRANTED`

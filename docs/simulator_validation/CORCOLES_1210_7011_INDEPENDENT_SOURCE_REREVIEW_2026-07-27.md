# Independent source-only admission rereview — Córcoles et al., arXiv:1210.7011v2

Date: 2026-07-27

Verdict: **PASS**

Reviewer ID: `corcoles_independent_source_rereview_2026_07_27`

This is a fresh admission review of:

- `docs/papers/reading_notes/corcoles_two_qubit_clifford_decomposition_1210.7011v2_source_review.md`;
- `docs/simulator_validation/CORCOLES_1210_7011_SOURCE_ONLY_AUDIT_2026-07-27.md`.

The earlier review report was not consulted or used. The reviewer first read
the complete `deep-read-paper` workflow and reading-note template, traversed
all nine pages of the pinned PDF, visually inspected all nine rendered pages,
and then compared every note claim, locator, primary PDF page, audit closure
row, and operation-replay row against the source.

## Fixed review objects

| object | review result |
|---|---|
| source PDF | Valid PDF 1.5 byte stream with 9 pages, `%PDF-` header, `%%EOF` trailer |
| source SHA-256 | `d0d52308fa0e23e7a8a10eab0291c3d02a9b28cb94893375d36693a602b1543f` |
| acquisition provenance | Pinned `arXiv:1210.7011v2`; provenance records 9 pages and the same PDF hash |
| reviewed audit SHA-256 | `7a6999b86451cdd333923ed834558da53a3f089d4f5400b1d7552f58d0b3b417` |
| note-declared source hash | Exact match |
| note-declared audit hash | Exact match |

The visually observed title-page line `Dated: November 27, 2024` conflicts
with the equally visible arXiv footer `arXiv:1210.7011v2 [quant-ph] 2 Nov
2012`. The note and audit preserve this anomaly rather than silently choosing
the 2024 line. The APS version-of-record page independently confirms
*Physical Review A* **87**, 030301(R), published 19 March 2013, so
`publication_status = "published"` is supported.

## Source-only note: claim-by-claim check

| Fact ID | exact source check | result |
|---|---|---|
| `corcoles-source-identity` | PDF p. 1 title, authors, visible v2 footer, and the APS publication record | PASS; the incompatible 2024 title-page date is explicitly retained as an anomaly |
| `corcoles-selection-scope` | Abstract and introduction on PDF p. 1; decomposition supplement on PDF p. 8 | PASS; the source is correctly bounded to two-qubit RB and Clifford compilation |
| `corcoles-local-groups` | Supplement, PDF p. 8 | PASS; \(\mathcal C_1\) has 24 elements and \(\mathcal S_1=\{I,R_S,R_S^2\}\) has three axis-cycling elements |
| `corcoles-four-class-decomposition` | Main text, PDF p. 1; four displayed supplement circuits, PDF p. 8 | PASS; the paper says four distinct classes with local, CNOT-like, iSWAP-like, and SWAP cores |
| `corcoles-class-counts` | Main text, PDF p. 1; supplement, PDF p. 8 | PASS; \(576,5184,5184,576\) and total \(11520\) are exact |
| `corcoles-entangling-counts` | Main text, PDF p. 1; supplement, PDF pp. 8–9 | PASS; the source assigns CNOT costs \(0,1,2,3\) and calls the decomposition optimal in CNOT count |
| `corcoles-average-cnot` | Main text, PDF p. 1; supplement, PDF p. 8 | PASS; the source reports 1.5 CNOTs per two-qubit Clifford, and the audit arithmetic reproduces it |
| `corcoles-gap-fixed-input` | Full decomposition section, PDF pp. 8–9 | PASS; no fixed-input objective or theorem discarding pre-core local gates appears |
| `corcoles-gap-tensor-objective` | Complete PDF scope, pp. 1–9 | PASS; no tensor-network truncation, purity, Rényi, bond, or fidelity objective appears |
| `corcoles-gap-capeps-instrument` | Complete PDF scope, pp. 1–9 | PASS; no PEPS/CAPEPS residual or measurement–reset–Record instrument appears |

The note uses the source's own phrase “four distinct classes” and the
displayed circuit decompositions. It does **not** promote them to a formal
left, right, or double quotient, and it does not claim that four candidates
suffice for a fixed-input disentangler search. That distinction is
scientifically necessary and is now stated correctly.

## Audit and operation-replay check

All six assigned closure rows have locators that resolve to the stated source
content. The four enumeration replay rows reproduce the displayed
\(\mathcal C_1\), entangling-core, and restricted \(\mathcal S_1\) factors.
The sum

\[
576+5184+5184+576=11520
\]

and the weighted CNOT average

\[
\frac{0(576)+1(5184)+2(5184)+3(576)}{11520}=1.5
\]

are correct. No hidden transformation is required beyond the source's
explicit statements that the four classes are distinct/exhaustive and that
the displayed combinations have the reported multiplicities.

The audit correctly confines fixed-input quotient language, CAPEPS mapping,
and comparisons with Chang or Masot-Llima/Garcia-Saez to project application,
competing evidence, or missing rows. Those statements are not copied into a
`paper_fact`. In particular, Córcoles et al. may support decomposition
background and a quotient-convention warning; this source alone cannot
validate the project's one-sided 20-representative search or any CAPEPS
efficiency claim.

## Source-only, schema, and hash gate

- Every level-two note section is exactly one `paper_fact` or
  `literature_gap`.
- Each record begins with `Fact ID`, `Source locator`, `PDF page`, and
  `Claim` in the required order; each gap also declares
  `Gap scope: source_local`.
- The note contains no project path, implementation instruction, or CAPEPS
  conclusion presented as a paper fact.
- The declared visual pages `[1, 8, 9]` cover every record's primary
  `PDF page`; the rereviewer additionally inspected pages 2–7.
- Source and audit artifacts exist and match their declared hashes.
- The current schema audit excludes the note only because its intentional
  pre-admission value is `admission_status = "draft_pending_review"`.
- A read-only, in-memory substitution of the reviewer-authorized admission
  fields passed full `parse_note(..., verify_artifact=True)` validation with
  all 10 evidence records and both artifact hashes verified.

## Admission authorization and exact boundary

The main agent is explicitly authorized to perform the following
post-review bookkeeping:

1. synchronize the audit's pending-review status to record this PASS, without
   changing any scientific claim, locator, replay row, or project boundary;
2. recompute the audit SHA-256 and update the note's
   `audit_packet_sha256` if that status-only audit edit is made;
3. set the note to
   `admission_status = "source_only_reviewed"`,
   `admission_reviewer = "corcoles_independent_source_rereview_2026_07_27"`,
   and `admission_date = "2026-07-27"`;
4. run artifact-verified schema validation;
5. add the validated note to `docs/papers/CURRENT_CORPUS.toml` and rebuild
   the RAG/KG artifacts.

This PASS is bound to the source-only scientific content and locators reviewed
above. Any change to a claim, locator, PDF page, source artifact, operation
replay, quotient interpretation, or project application requires another
independent review. Admission of this note does not admit the separate
Chang/Masot claims, prove a fixed-input quotient theorem, close the wider
CAPEPS literature packet, authorize experiment code, or establish CAPEPS
correctness or efficiency.

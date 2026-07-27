# Independent source-only admission review — Hostens, Dehaene, and De Moor, arXiv:quant-ph/0408190v2

Date: 2026-07-27

Reviewer ID: `hostens_independent_source_review_2026_07_27`

Verdict: **PASS for source-only admission**

This verdict is limited to the source facts, source-local gaps, locators, and
claim boundaries in the reviewed note/audit pair. It does not authorize a
qutrit local-equivalence enumeration, a 90-class result, leakage semantics,
measurement/reset/Record semantics, a PEPS/CAPEPS construction, or a QEC
performance claim.

No reading note, audit packet, source artifact, or corpus manifest was changed
by this review.

## Reviewed immutable snapshots

| object | verified identity |
|---|---|
| source PDF | `docs/papers/quant-ph_0408190v2.pdf` |
| source PDF SHA-256 | `b48cf81d89050ccf9372d5be713c098088fd3a0d371e9be2a9901d09ef07c831` |
| source PDF structure | `%PDF-1.4`, 236,797 bytes, unencrypted, 11 pages, terminal `%%EOF` |
| source-only note | `docs/papers/reading_notes/hostens_stabilizer_clifford_arbitrary_dimension_quant_ph_0408190v2_source_review.md` |
| source-only note SHA-256 | `15f2df0f858830ccb5774a688576185f0e06b3b5c1c2702752f5c0e77f5dc396` |
| audit packet | `docs/simulator_validation/HOSTENS_QUANT_PH_0408190V2_SOURCE_ONLY_AUDIT_2026-07-27.md` |
| audit packet SHA-256 | `eef73c9d3a7ec101ae1c0e5d13c8b522c36ba0d5974e07a5b0a0965e3f743c0b` |
| note-declared source hash | exact match |
| note-declared audit hash | exact match |
| compatibility-owner hash | `tools/literature_schema.py`: `6ab50f261fb64e11319831cc796bad341c4c73638144ad58cdae33d080eb23e3` |
| focused-test-owner hash | `tests/test_literature_tools.py`: `476bf38f53a942e18aba2a2d383fe545bdd3102020d6c1ecc4a10224cf3a4b30` |

The two compatibility hashes still equal the values recorded in the audit.

## Independent review procedure

I read the complete 11-page PDF in source order before reaching an admission
decision. A temporary `pdftotext -layout` extraction was used only for
traversal and full-text search. All 11 pages were independently rendered and
visually inspected. The load-bearing pages were:

- PDF p. 1: title, authors, printed date, visible arXiv version footer, scope,
  and graph-state limitation;
- PDF pp. 2--3: Eqs. (1)--(10), the Pauli and Clifford representations,
  phase domains, composition, inverse, and symplectic/phase conditions;
- PDF pp. 4--6: elementary Clifford operations, ring-safe decomposition,
  complexity statements, stabilizer definition, Eqs. (11)--(15), and the
  minimal-column anomaly;
- PDF pp. 7--9: Theorem 1, Eqs. (16)--(19), Appendices A--B, and the opening
  of Appendix C through Eq. (C5);
- PDF p. 10: Eqs. (C6)--(C8);
- PDF p. 11: the completion of reference note [18].

Every candidate `paper_fact`, `literature_gap`, relation, assigned closure
row, notation-ledger entry, replay row, anomaly, and project boundary was then
compared with the rendered source. Extracted text, the existing note, and the
existing audit were not treated as formula evidence.

## Source identity, date, and version

**PASS.**

The first rendered page visibly contains both:

- `(Dated: October 23, 2018)` in the title block; and
- `arXiv:quant-ph/0408190v2 22 Feb 2005` in the arXiv footer.

The PDF metadata also gives a 2018 creation/modification date. The note and
audit correctly identify the evidence object by its visible pinned v2 footer
and preserve the incompatible 2018 title-page date as an unexplained artifact
anomaly. They do not silently promote the 2018 line into the arXiv version
date. `publication_status = "preprint"` is appropriate for this reviewed
artifact.

The temporary local-PDF provenance helper conservatively reports
`version_status = "unknown-local-artifact-version"` because it was given a
local path, not an arXiv retrieval specification. That generic sidecar does
not override the version identifier visibly printed in the hashed PDF.

## The three semantic-sanity atomicity questions

The template forbids bundling independently locatable claims. The current
note resolves all three questioned clusters at the source's natural equation
boundaries.

| questioned cluster | current records | independent judgment |
|---|---|---|
| odd-\(d\) Clifford formulas | `hostens0408190-odd-clifford-conjugation` anchors Eq. (C2) and its immediately following admissibility paragraph; `hostens0408190-odd-clifford-composition` anchors Eq. (C3); `hostens0408190-odd-clifford-inverse` anchors Eq. (C4) | **PASS.** Composition and inversion are no longer bundled with conjugation. The \(C,g\) domains and “no further restriction on \(g\)” qualifier in the C2 record are the representation assumptions/constraint for that one conjugation formula, not a second independently located operation. |
| odd-\(d\) stabilizer formulas | `hostens0408190-odd-stabilizer-phase` anchors Eq. (C5); `hostens0408190-odd-stabilizer-generator-change` anchors Eq. (C6); `hostens0408190-odd-stabilizer-clifford-update` anchors Eq. (C7); the basis expansion is separately recorded at Eq. (C8) | **PASS.** The phase constraint, coordinate change, Clifford action, and basis expansion are distinct records. |
| minimal stabilizer generators | `hostens0408190-minimal-generator-reduction` anchors the Smith-normal reduction paragraph; `hostens0408190-minimal-generator-independence` anchors Eq. (14); `hostens0408190-minimal-generator-phase` anchors Eq. (15); generator-count wording and the \(d=4\) example are also separate facts | **PASS.** Construction, independence, and the per-column phase condition are no longer one bundled claim. |

There is no atomicity blocker in these three current groups.

## Formula, symbol, and locator fidelity

**PASS.**

The following load-bearing symbol checks agree with the rendered equations:

| object | independent source check | candidate treatment |
|---|---|---|
| Pauli labels and phases | \(a=[v;w]\in\mathbb Z_d^{2n}\); general phases are \(\zeta^\delta\) with \(\delta\in\mathbb Z_{2d}\); Eq. (4) uses \(2a^TUb\) | exact |
| commutation form | \(P=U-U^T\pmod d\) and Eq. (5) uses \(\omega^{a^TPb}\) | exact |
| general Clifford data | \(C\in\mathbb Z_d^{2n\times2n}\), \(h\in\mathbb Z_{2d}^{2n}\); Eqs. (7)--(9) retain modulo-\(2d\) phase arithmetic | exact |
| Clifford conditions | \(C^TPC=P\pmod d\), \(C^{-1}=-PC^TP\pmod d\), and Eq. (10) is \((d-1)\operatorname{Vdiag}(C^TUC)+h=0\pmod2\) | exact |
| stabilizer data | \(S\in\mathbb Z_d^{2n\times m}\), \(f\in\mathbb Z_{2d}^m\), and \(S^TPS=0\pmod d\) | exact |
| generator changes | Eq. (12) is a right action \(S'=SR\) with \(R\in\mathbb Z_d^{m\times m}\) invertible; Eq. (13) is \(S'=CS\) under Clifford conjugation | exact |
| odd-\(d\) Clifford phase | Appendix C defines \(g=h/2\in\mathbb Z_d^{2n}\); symplecticity remains required and there is no additional restriction on \(g\) | exact |
| odd-\(d\) stabilizer phase | Appendix C uses \(\omega^{b_k}XZ(S_k)\) with \(b=f/2\in\mathbb Z_d^m\), followed by Eqs. (C5)--(C7) | the equation-scoped facts and replay do not confuse \(b\) with general-case \(f\), and introduce no wrong domain |
| quadratic expansion | Theorem 1 uses \(\zeta^{t^TMt+p^Tt}\); Appendix C replaces it by \(\omega^{t^TMt+p^Tt}\) with the odd-\(d\) definitions | exact |

The audit notation ledger is a compact ledger rather than an enumeration of
every temporary proof symbol. Its stated domains are source-faithful. In
particular, it does not treat odd composite \(d\) as a field merely because
\(2^{-1}\) exists.

All 51 `paper_fact` locators resolve to the claimed title block, paragraph,
equation, theorem, or appendix. All 16 `literature_gap` records have a
source-local boundary and an in-range visually checked anchor page.

## Complexity and printed anomalies

**PASS.**

The candidate preserves, rather than repairs or hides, every load-bearing
printed anomaly independently observed:

| anomaly | rendered source result | candidate result |
|---|---|---|
| date mismatch | title block says October 23, 2018; footer says v2, 22 Feb 2005 | preserved |
| qubit/qudit wording | PDF pp. 2--3 say “one and two-qubit” in arbitrary-\(d\) decomposition passages; Sec. IV and the Conclusion use qudit wording | preserved without silent correction |
| decomposition complexity | end of Sec. IV prints \(O(n^2\log d)\) elementary operations; the Conclusion prints \(O(n^2)\) one- and two-qudit operations | both facts are separate, and the unreconciled mismatch is a source-local gap |
| zero-column count | after starting with \(m'\) columns and obtaining minimal \(m\), PDF p. 6 prints the rightmost \(m-m'\) columns as zero | preserved as printed; the likely \(m'-m\) repair remains audit inference only |
| prime-factor wording | PDF p. 6 prints “only single prime factors” and “multiple prime factors” without definitions | preserved verbatim and not silently modernized |
| Appendix-B index | the paragraph after Eq. (B1) defines \(j\)-indexed quantities but says “for every \(k=1,\ldots,m\)” | preserved |
| intermediate/final uniqueness | \(x^{*\prime}\in\mathbb Z_d^n\) is “most likely not unique,” while the reduced \(x^*\in G_{\bar q}\) is asserted unique | correctly treated as different objects, not a contradiction |

The audit's statement that the two complexity expressions agree only after an
additional fixed-\(d\) reading is clearly an audit inference, not attributed
to the paper.

## Composite-\(d\), qutrit, 90-class, and project boundaries

**PASS.**

The source explicitly works over the ring \(\mathbb Z_d\), requires a row
scaling factor to satisfy \(\gcd(r,d)=1\), uses Euclid's algorithm when no
individual column entry is a unit, and uses Smith normal form over a principal
ideal ring. The note and audit preserve all of these composite-\(d\)
qualifications.

The arbitrary-\(d\) formalism includes \(d=3\) only as a specialization of the
same complete \(d\)-level qudit space. The complete PDF does not:

- split that space into computational and leakage sectors;
- define leakage, seepage, return, or leakage measurement;
- state a qutrit-specific local-equivalence quotient;
- state or derive a 90-class enumeration;
- enumerate one- or double-sided local-equivalence representatives.

The source-only note records the 90-class item only as a
`literature_gap` with `Gap scope: source_local`. The audit similarly marks the
assigned qutrit-enumeration row `missing`. Neither artifact promotes arbitrary
\(d\) algebra into leakage support or a 90-class result.

The additional missing rows for selective measurement, Born probabilities,
reset, raw histories, emitted Records, physical noise, MPS/PEPS/CAPEPS, QEC
thresholds, decoders, and matched resources are also faithful to the complete
source scope. The only full-text occurrence of the word “Measurement” is in a
reference title; it does not supply any of those mechanisms.

## Relations, source-only separation, and replay

**PASS.**

The note contains 67 evidence records: 51 `paper_fact` and 16
`literature_gap` records, all with unique Fact IDs. Its 12 relations:

- use supported predicates and object types;
- resolve to existing `paper_fact` records, never to a gap;
- use object labels that occur in the referenced Claim;
- introduce no project-defined target.

The source-only note contains only `paper_fact` and `literature_gap` H2
records. Project mappings, possible implementation uses, disconfirmation
conditions, and extrapolation limits are confined to the separate audit.

The operation replay correctly follows:

1. Pauli multiplication and commutation;
2. general Clifford conjugation, composition, and inversion;
3. ring-safe elementary decomposition and phase correction;
4. stabilizer generator-coordinate and Clifford updates;
5. Smith-normal canonicalization and the quadratic standard-basis expansion;
6. the odd-\(d\) phase simplifications.

No replay row fills measurement, reset, leakage, Record, tensor-network, or
qutrit-enumeration gaps from project plausibility.

## Schema and pending-admission gate

The strict current parser rejects the reviewed draft for exactly its intended
pre-review metadata gate:

`admission_status must be 'source_only_reviewed'`.

An independent read-only body check, bypassing only that pending metadata
gate, parsed all 67 evidence records and all 12 relations, verified unique
Fact IDs, validated the legacy arXiv identifier/version/URI tuple, and found
no structural or relation error. Source and audit hashes match the declared
values.

The pending metadata is not a semantic blocker; it correctly prevents
premature admission.

## Admission authorization

**Authorization granted.** The main agent may perform post-review bookkeeping
without changing the reviewed scientific content:

1. update the audit's pending-review status to identify this report as the
   independent admission basis;
2. recompute the audit SHA-256 and update the note's
   `audit_packet_sha256`;
3. set the note metadata to:
   - `admission_status = "source_only_reviewed"`;
   - `admission_reviewer = "hostens_independent_source_review_2026_07_27"`;
   - `admission_date = "2026-07-27"`;
4. run artifact-verified note/corpus validation;
5. consider manifest admission only after those checks pass.

This authorization is bound to the reviewed source facts, gaps, locators,
pages, relations, replay rows, anomaly handling, and project boundaries.
Changing any of those scientific fields requires a fresh independent source
review. This PASS does not itself edit or admit the note.

## Blockers and final bounded verdict

Admission blockers: **none**.

- `read_status: complete`
- `evidence_status: persisted`
- full-text and visual source review: `complete`
- source identity/date/version handling: `PASS`
- formula and symbol fidelity: `PASS`
- three questioned atomicity groups: `PASS`
- complexity/anomaly handling: `PASS`
- qutrit/90-class boundary: `PASS`
- relation integrity: `PASS`
- operation replay: `PASS`
- source-only separation: `PASS`
- source-only admission authorization: `GRANTED`
- qutrit/leakage/measurement/Record/PEPS/CAPEPS/QEC extrapolation: `NOT GRANTED`

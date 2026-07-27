# Independent source-only admission review — Córcoles et al., arXiv:1210.7011v2

Date: 2026-07-27

Reviewer: `codex-independent-review-corcoles-2026-07-27`

Decision: **FAIL — revision and a fresh independent review are required before
admission.**

This is an admission decision on the current note/audit pair, not a rejection
of the paper's four-class decomposition facts. Those core facts replay
successfully. The current artifacts fail because the source-only note is not
schema-conformant, contains a project-inference section, and the audit
mis-transcribes one source formula.

No change to `CURRENT_CORPUS.toml` is authorized by this review.

## Objects reviewed

- PDF:
  `docs/papers/1210.7011v2.pdf`
- PDF SHA-256:
  `d0d52308fa0e23e7a8a10eab0291c3d02a9b28cb94893375d36693a602b1543f`
- PDF signature/page count:
  `%PDF-`, 9 pages
- Candidate source-only note:
  `docs/papers/reading_notes/corcoles_two_qubit_clifford_decomposition_1210.7011v2_source_review.md`
- Candidate note SHA-256 at review:
  `95970963868c86f0b54e3d6d6e2e6fb7d081bb0d11986bab158b65f4ebfe6ba6`
- Candidate audit:
  `docs/simulator_validation/CORCOLES_1210_7011_SOURCE_ONLY_AUDIT_2026-07-27.md`
- Candidate audit SHA-256 at review:
  `1b6d1d96e7953362b3fa83679664597ce6c7320269cde4f7f7c263ca52541fcf`
- Pinned arXiv v2 TeX source inspected in a temporary directory:
  `https://arxiv.org/src/1210.7011v2`
- Retrieved TeX-source archive SHA-256:
  `1f483ce4ca3388a90f06e9d0086ccafcb7c9419b47702223834616a7829ae773`

I traversed all nine PDF pages. PDF pages 1, 8, and 9 were rendered and
visually inspected. Page 1 was checked for the title date, arXiv footer,
four-class counts, total group size, and average CNOT count. Pages 8 and 9 were
checked for the displayed circuit order, local factors, class counts, CNOT
costs, and device-specific replacements. The extracted text and pinned TeX
source were used only to resolve navigation and exact source typography.

## Semantic findings

| item | independent source finding | current artifact judgment |
|---|---|---|
| four classes | PDF pp. 1 and 8 state four distinct decomposition classes: local, CNOT-like, iSWAP-like, and SWAP | substantively correct |
| formal quotient | The source uses no left-, right-, coset-, or double-quotient definition; p. 8 displays pre-\(\mathcal C_1\), an entangling core, and restricted post-\(\mathcal S_1\) factors for the middle classes | the note/audit correctly refuse to call this a formal double quotient |
| class counts | PDF p. 8 gives \(24^2\), \(24^2 3^2\), \(24^2 3^2\), and \(24^2\), hence \(576\), \(5{,}184\), \(5{,}184\), and \(576\) | correct |
| total size | The four counts sum to \(11{,}520\), also stated on PDF p. 1 | correct |
| CNOT costs | PDF pp. 1 and 8 assign 0, 1, 2, and 3 CNOTs to the four classes | correct |
| uniform average | \((0\cdot576+1\cdot5184+2\cdot5184+3\cdot576)/11520=1.5\) | operation replay correct |
| fixed-input objective | The paper never studies \(f(U\lvert\psi\rangle)\), never proves invariance to pre-local gates, and never equates its four classes with a one-sided 20-representative search | the audit's `missing` judgment is correct |
| CAPEPS/Record | The paper is a randomized-benchmarking and gate-compilation paper and contains no PEPS residual or measurement–reset–Record instrument | source-local gaps are correct |

### Quotient conclusion

The source supports a four-class **hardware compilation/decomposition** of the
full two-qubit Clifford group. It does not itself provide a formal
\(\mathcal C_1\backslash\mathcal C_2/\mathcal C_1\) theorem, and its displayed
forms are not arbitrary local factors on both sides: the CNOT-like and
iSWAP-like diagrams show pre-\(\mathcal C_1\) factors and post-\(\mathcal S_1\)
factors. Therefore:

- “Córcoles gives four decomposition classes” is supported;
- “Córcoles proves the project's formal double quotient has four elements” is
  unsupported;
- “Córcoles reduces a fixed-input disentangler search to four candidates” is
  unsupported.

The candidate audit preserves this distinction. The candidate note also says
the quotient equivalence is an inference, but it puts that inference in the
wrong artifact.

## Source-date anomaly

The anomaly handling is substantively correct:

- the visible title page says `Dated: November 27, 2024`;
- the same PDF page has the arXiv footer
  `arXiv:1210.7011v2 [quant-ph] 2 Nov 2012`;
- the official arXiv version history identifies v1 as 25 October 2012 and v2
  as 2 November 2012;
- the APS record identifies *Physical Review A* 87, 030301(R), published
  19 March 2013 and received 24 October 2012.

The 2024 title-page line must remain an unexplained artifact anomaly and must
not replace the arXiv version date or publication date. The revised audit
should add the exact official arXiv-version and APS-DOI URLs rather than the
generic phrase “published-record metadata.”

## Admission blockers

### 1. Project inference is present in the source-only note

The note contains:

`## Local-equivalence relevance [project_inference]`

The source-only schema permits only `[paper_fact]` and `[literature_gap]`.
This section also contains the project bridge from displayed local factors to
the project's quotient use. It belongs only in the separate audit packet,
where substantially the same distinction is already recorded.

Required repair: delete this H2 from the source-only note. Preserve any useful
project application solely in the audit.

### 2. Relation metadata is not schema-conformant

The note uses unsupported relation predicates `quantifies` and unsupported
object types `classification`, `cardinality`, and `resource`. The allowed
predicates are:

`contradicts`, `defines`, `derives`, `limits`, `measures`, `supports`, `uses`.

The allowed object types are:

`concept`, `limitation`, `method`, `model`, `observable`, `theorem`.

In addition:

- the `corcoles-gap-fixed-input` relation points to a `literature_gap`, while
  relations may point only to `paper_fact`;
- several `object_label` values are not literal substrings of their referenced
  one-sentence Claim, as required by the parser.

Required repair: rebuild the relations with allowed enums, point only to
`paper_fact` Fact IDs, and make each `object_label` occur verbatim in its
referenced Claim. Removing nonessential relations is preferable to inventing
ontology.

### 3. `PDF page` fields use lists and ranges

The current note uses values such as `1, 8`, `8–9`, and `1–9`. The current
schema requires exactly one positive integer per evidence record, and that
page must occur in `visually_checked_pages`.

Required repair: use PDF p. 8 as the single anchor for the decomposition,
counts, and CNOT facts. For full-text source-local gaps, retain the full
review boundary in `Source locator` but choose one visually checked anchor
page in `PDF page`.

### 4. The audit mis-transcribes the \(S\) definition

The audit notation ledger states

\[
S=\exp[-i(X+Y+Z)\pi/\sqrt 3].
\]

PDF p. 8 and the pinned TeX source instead print

```tex
S=\exp[-i (X+Y+Z)\pi/\sqrt{3}3]
```

The source typography is itself ambiguous, while the following sentence says
that the rotation cycles the Bloch axes. The audit's \(\pi/\sqrt3\)
normalization is not what is printed and is not justified by the source.

Required repair: either omit this non-load-bearing formula from the audit
notation ledger, or preserve the exact printed expression and explicitly mark
its typography as ambiguous. Do not silently normalize it. The source's
explicit action \(x\!-\!y\!-\!z\mapsto y\!-\!z\!-\!x\) may be recorded
separately as the unambiguous paper fact.

### 5. Hash and review state must be regenerated after repair

Once the audit changes, its SHA-256 in the note will be stale. Once the note
changes, this review no longer applies to that new byte sequence.

Required sequence:

1. repair the audit and source-only note;
2. recompute and update `audit_packet_sha256`;
3. run the literature-note schema validator on the repaired candidate;
4. perform a fresh independent claim/locator/page comparison;
5. only after a PASS set `admission_status="source_only_reviewed"` with that
   reviewer's identity and then consider manifest admission.

## Separation verdict

| category | verdict |
|---|---|
| paper facts | four-class decomposition, counts, CNOT costs, and average are faithful |
| project inference | substantively cautious in the audit, but one inference H2 improperly remains in the source-only note |
| source-local gaps | fixed-input quotient, tensor-network objective, and CAPEPS/Record absences are properly presented as source-local, not field-wide |
| date provenance | correct conclusion, but exact official metadata URLs should be added |
| operation replay | passes for the counts and 1.5-CNOT average |
| formula fidelity | fails for the audit's \(S\) normalization |

## Final admission verdict

- `read_status`: `complete`
- independent full-text traversal: `complete`
- core source-fact fidelity: `pass`
- operation replay: `pass`
- source-only separation: `fail`
- schema readiness: `fail`
- formula fidelity: `fail`
- admission decision: **FAIL**

The source can support the bounded claim “Córcoles et al. give four
two-qubit-Clifford decomposition classes with the stated cardinalities and
1.5 average CNOT cost.” It cannot support a formal project quotient or
fixed-input candidate reduction. The current evidence pair must not be
admitted until all blockers above are repaired and independently re-reviewed.

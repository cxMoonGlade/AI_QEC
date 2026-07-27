# Independent source-only admission review — Masot-Llima et al., arXiv:2602.15942v2

Date: 2026-07-27

Reviewer: `codex:/root/review_masot_source`

## Decision

**PASS_FOR_FAITHFUL_SOURCE_ONLY_ADMISSION**

This PASS applies only to the fidelity and source-only separation of the
reviewed reading note and its bound audit packet. It is not a PASS for
Theorem III.1, Appendix B, the printed double-sided 20-class explanation, a
CAPEPS/PEPS limitation, or any project no-go.

The current repository state remains intentionally **not admitted**. The note
still declares `admission_status = "draft_pending_review"` and names a pending
reviewer, and it is absent from `docs/papers/CURRENT_CORPUS.toml`. Those files
were not changed in this review.

| object | independent decision |
|---|---|
| source-only note fidelity | **PASS** |
| separation of source statements from mathematical/project judgment | **PASS** |
| source-only audit packet | **PASS** |
| Theorem III.1 as printed | **FAIL_AS_PRINTED** |
| Appendix B as a valid proof | **FAIL_MULTIPLE_INDEPENDENT_FATAL_ERRORS** |
| 20 classes under the printed double-sided relation | **FAIL** |
| narrower existential no-go | **OPEN_REQUIRES_NEW_STATEMENT_AND_PROOF** |
| PEPS mechanism or result | **MISSING_FROM_THIS_SOURCE** |
| measurement/reset/Record instrument or result | **MISSING_FROM_THIS_SOURCE** |
| project-level CAPEPS/PEPS no-go | **NOT_ESTABLISHED** |

## Review order and inspection record

The primary source was isolated from downstream interpretation. I first read
the complete 17-page PDF, then visually rendered all 17 pages. I inspected at
higher resolution:

- PDF p. 3, including both sides of
  \(V=(L_1\otimes L_2)U(R_1\otimes R_2)\) and the continued sentence reporting
  20 gates;
- PDF pp. 6--7, including every printed quantifier in Theorem III.1 and its
  prose interpretation;
- PDF pp. 13--17, including Eqs. (B1)--(B32), with separate crops for the
  equation-bearing regions.

Only after that source pass did I read, in order:

1. `docs/papers/reading_notes/masot_limits_clifford_disentangling_2602.15942v2_source_review.md`;
2. `docs/simulator_validation/MASOT_2602_15942V2_SOURCE_ONLY_AUDIT_2026-07-27.md`;
3. `docs/simulator_validation/MASOT_2602_15942V2_INDEPENDENT_MATH_REVIEW_2026-07-27.md`.

No older CAPEPS synthesis was consulted to form this verdict. After the
Masot verdict was fixed, I checked the independently cited Córcoles comparator
at its exact source page solely to verify the four-class/count statement in
the mathematical audit.

## Artifact identity and hash bindings

| artifact | SHA-256 | result |
|---|---|---|
| `docs/papers/2602.15942v2.pdf` | `ec572bd96d4a937667c2c6fb9c1996da92ff359072050c2fe47b501ed80aa83e` | matches note, source audit, and math review |
| reviewed source-only note | `e9f2cae32896c6769aee8d3dd039b5a3b388456b74891c8a50d758e76f3add00` | exact draft bytes reviewed |
| source-only audit | `5fe15996ca2ec419cd0101ef49df604572a039089bbedd830dd119f82ce74a3e` | matches note front matter |
| independent mathematical review | `fc4527cc6ba9c052194c8eebbca93c9f8725e437af1c0afb7c3694c5bdcf108c` | matches source-audit binding |
| `docs/papers/1210.7011v2.pdf` comparator | `d0d52308fa0e23e7a8a10eab0291c3d02a9b28cb94893375d36693a602b1543f` | matches math-review binding |

The Masot artifact begins with `%PDF-1.7`, ends with a valid `%%EOF` trailer,
contains 3,723,294 bytes, and reports 17 letter-sized pages. Its embedded
title and authors match the note. The title page says 24 February 2026 while
the visible arXiv v2 footer says 22 February 2026; the note correctly records
that discrepancy without resolving it by inference.

## Record-by-record source audit

The note contains 22 classified records: 18 `paper_fact` records and four
`literature_gap` records. Every Fact ID is unique, every record begins with
the required four fields in the required order, every gap adds
`Gap scope: source_local`, and every cited PDF page is included in the note's
`visually_checked_pages`.

| Fact ID | exact source check | admission judgment |
|---|---|---|
| `masot-source-identity` | Title page and arXiv footer, PDF p. 1, show the four named authors, v2 identifier, and a 17-page preprint. | **PASS** |
| `masot-source-date-anomaly` | PDF p. 1 visibly contains the 24 February title date and 22 February v2 footer date. | **PASS** |
| `masot-selection-scope` | Abstract and the end of Sec. I study exact/heuristic Clifford disentangling, with reported work focused on one-dimensional CAMPS/MPS and non-Clifford accumulation. | **PASS** |
| `masot-ctn-definition` | Definition 1 and Eq. (1), PDF p. 2, give \(\lvert\psi\rangle=C\lvert\psi_T\rangle\) and joint \(C,T\) updating. | **PASS** |
| `masot-cooling-gauge` | Sec. II.B, PDF p. 2, inserts \(I=U_CU_C^\dagger\), applies \(U_C\) to the TN, and absorbs the inverse into the Clifford frame. | **PASS** |
| `masot-heuristic-cooling` | Definition 2, Eq. (2), and Fig. 2, PDF p. 3, describe local candidate evaluation during sweeps up to depth \(d\). | **PASS** |
| `masot-double-sided-relation` | PDF p. 3 prints local Clifford factors on both the left and right of \(U\). | **PASS_AS_PRINTED_STATEMENT** |
| `masot-twenty-statement` | The immediately continued sentence on PDF p. 3 reports 20 gates. | **PASS_AS_PRINTED_STATEMENT** |
| `masot-gap-representative-derivation` | The paragraph neither enumerates the 20 gates nor derives 20 from the printed double-sided relation. | **PASS_SOURCE_LOCAL_GAP** |
| `masot-exact-cooling-construction` | Appendix A and Fig. 11, PDF p. 13, leave a local rotation on an affected separable stabilizer factor and move a controlled-Pauli cascade into the Clifford component. | **PASS_AS_SUFFICIENT_CONSTRUCTION_ONLY** |
| `masot-theorem-statement` | Theorem III.1, PDF p. 6, prints the arbitrary-\(\theta\), arbitrary-\(\lvert\Psi\rangle\), “\(U\) is Clifford iff” statement captured by the note. | **PASS_AS_SOURCE_STATEMENT_ONLY** |
| `masot-printed-unitary-decomposition` | Eq. (B1), PDF p. 13, asserts the two-block form for any unitary. | **PASS_AS_PRINTED_STATEMENT; MATHEMATICALLY FALSE** |
| `masot-printed-orthonormalization` | Eq. (B5), PDF p. 14, visibly has the plus sign, missing modulus, and squared overlap described by the note. | **PASS_AS_PRINTED_STATEMENT; MATHEMATICALLY FALSE** |
| `masot-printed-operator-conclusion` | Eqs. (B17)--(B18), PDF p. 15, contain the displayed all-\(\lvert\Psi\rangle\) inference described by the note. | **PASS_AS_PRINTED_STATEMENT; DERIVATION FAILS** |
| `masot-printed-purity-conclusion` | Eqs. (B27)--(B32) and the final paragraph, PDF p. 17, make the stated endpoint-to-stabilizer inference. | **PASS_AS_PRINTED_STATEMENT; DERIVATION FAILS** |
| `masot-special-state-caveat` | The paragraph after Eq. (B10), PDF p. 15, expressly leaves state-dependent gadgets and another separable stabilizer site outside the proof. | **PASS** |
| `masot-gap-independent-theorem-proof` | The source supplies no alternate proof independent of the Appendix B chain through Eqs. (B1) and (B5). | **PASS_SOURCE_LOCAL_GAP** |
| `masot-two-three-local-observation` | Fig. 4 and its discussion, PDF p. 5, report no improvement for the tested \(N=12\), \(m=100\) three-local workload over the two-local workload. | **PASS_FOR_REPORTED_WORKLOAD_ONLY** |
| `masot-depth-observation` | Fig. 5 and its discussion, PDF p. 5, report no clear advantage for the tested additional sweep depths. | **PASS_FOR_REPORTED_WORKLOAD_ONLY** |
| `masot-nonclifford-accumulation` | Fig. 7 and its discussion across PDF pp. 7--8 report delayed entanglement accumulation/saturation for smaller rotations. | **PASS_FOR_REPORTED_WORKLOAD_ONLY** |
| `masot-gap-peps` | Sec. V, PDF p. 9, places higher-dimensional tensor networks in future work; the source has no PEPS construction, contraction, benchmark, theorem, or resource comparison. | **PASS_SOURCE_LOCAL_GAP** |
| `masot-gap-measurement-reset` | Full-source inspection finds no selective measurement/reset map, Born branch accounting, conditional trajectory, syndrome Record, or Record-law metric. | **PASS_SOURCE_LOCAL_GAP** |

The note consistently uses “the source states,” “the source prints,” or
source-local absence wording around disputed material. It does not promote
the theorem or the 20-class explanation into mathematical truth.

## Theorem and Appendix B adjudication

The independent mathematical review is correct and is properly kept outside
the source-only note.

### Literal theorem counterexample

For \(P=X_1X_2\), target
\(\lvert\phi_2\rangle=\lvert0\rangle\), and
\(D=\operatorname{CNOT}_{2\rightarrow1}\),

\[
D e^{-i\theta X_1X_2}
\lvert\Psi\rangle\lvert0\rangle
=
\lvert\Psi\rangle
\left(\cos\theta\lvert0\rangle-i\sin\theta\lvert1\rangle\right)
\]

for every \(\theta\) and \(\lvert\Psi\rangle\). Post-composing with a
non-Clifford local \(T_1\) preserves the product cut, so
\(U=(T_1\otimes I_2)D\) qualifies under the literal hypothesis but is not
Clifford even though the target input is stabilizer. This refutes the
printed characterization of every qualifying \(U\).

Under Appendix B's pointwise-angle reading, the unexcluded Clifford angle
\(\theta=\pi/4\) gives a second contradiction:
\(U=e^{+i(\pi/4)P}\) is Clifford and exactly cancels the input rotation for
every target state, including non-stabilizer targets. The endpoint
\(\theta=0,\ U=I\) does the same. These examples do not decide a different
claim in which one \(U\) must be fixed for all \(\theta\); the paper does not
state and prove that different quantifier order consistently.

### Independent fatal proof defects

1. Eq. (B1) is false for a general bipartite unitary. For example,
   \(\operatorname{CNOT}_{1\rightarrow2}\lvert+0\rangle\) is a Bell state,
   whereas Eq. (B1) would force a fixed product output on the target for the
   whole \(\mathcal H_B\otimes\lvert\phi_n\rangle\) input subspace.
2. Eq. (B5) is not Gram--Schmidt. The nonsingular denominator is
   \(\sqrt{1-\lvert\langle\Omega_1|\Omega_2\rangle\rvert^2}\), not the
   printed square root with a plus sign and an unmodulated squared overlap.
3. Purity requires unit-modulus collinearity, not overlap restricted to
   \(\pm1\). Eqs. (B7)--(B8) also lose a \(P_B\) factor, and Eq. (B18) does
   not solve Eq. (B17) as printed.
4. The general chain omits the \(\beta\delta=0\) branches. Its displayed
   projector in Eq. (B25) has a wrong diagonal denominator and missing
   terms; Eq. (B26) has an independent denominator-sign defect.
5. The endpoint argument divides by
   \(\lvert\beta\rvert^2\lvert\gamma\rvert^2\) where the required endpoint
   can make that product zero. Equal computational-basis magnitudes
   \(x=\pi/4\) do not by themselves characterize a one-qubit stabilizer
   state.

These defects are independent. Correcting a sign or normalization cannot
promote Appendix B into a proof. The source-only audit therefore correctly
uses `FAIL_AS_PRINTED` and leaves a narrower existential theorem open.

## Double-sided relation versus the count 20

The visually checked PDF p. 3 defines a double-sided local relation but then
reports 20 representatives. With
\(\mathcal K=\mathcal C_1\otimes\mathcal C_1\),

\[
\lvert\mathcal C_2\rvert/\lvert\mathcal K\rvert
=11520/24^2=20
\]

is a one-sided coset index. It is not the cardinality of
\(\mathcal K\backslash\mathcal C_2/\mathcal K\).

The independently checked Córcoles supplement page gives four
local/core/local types with counts \(576\), \(5184\), \(5184\), and \(576\),
which sum to \(11520\). For a fixed-input objective, post-action local
Cliffords preserve entanglement, whereas pre-action locals can change the
input and its score. Thus a 20-candidate optimizer may be repairable as an
independently validated one-sided output-local transversal, but the source's
printed double-sided explanation does not establish it.

The note handles this correctly by recording the relation and count as two
separate printed facts and adding a source-local missing-derivation gap. The
audit, not the source-only note, records the contradiction.

## PEPS and measurement-instrument boundary

A full-text source search found “projected entangled pair states” only in
bibliography titles. The main text reports MPS/CAMPS workloads and names
higher-dimensional tensor networks as future work. It supplies no PEPS
algorithm or result.

The source contains no result for selective measurement, Born branch mass,
reset, conditional trajectories, syndrome/detector Records, or a Record-law
metric. Consequently neither the paper's heuristic observations nor its
failed theorem can establish CAPEPS/PEPS residual spreading, finite-bond
faithfulness, runtime, memory, or complete-Record behavior.

## Schema and corpus boundary

The note's metadata, source identity, artifact hash, audit hash, classified
record shape, exact-page coverage, and source-only prose are suitable for the
current `error_coupling_simulator.literature.note.v1` schema after an
authorized admission transition.

The schema intentionally permits one positive integer in each `PDF page`
field; a multi-page span belongs in `Source locator`. Accordingly,
`masot-gap-independent-theorem-proof` validly uses PDF p. 14 as the B5 anchor
while its source locator explicitly spans Appendix B, Eqs. (B1)--(B32). This
is not a hidden page mismatch.

The current fail-closed parser correctly rejects the exact reviewed draft
before record ingestion with:

`admission_status must be 'source_only_reviewed'`

That rejection is expected, not a semantic defect in this review candidate.
The exact note is absent from `CURRENT_CORPUS.toml`; no RAG/KG claim can
therefore consume it. The repository-wide manifest check also reported one
unrelated already-valid orphan note,
`kim_qutrit_camps_haldane_2607.03939v1_source_review.md`, and no stale
manifest entries. That pre-existing drift is outside this Masot decision.

Because this task forbids changes to the note, audit, and manifest, this
report does not perform the mechanical admission. A later authorized
admission must:

1. change only the admission metadata needed to identify the completed
   independent source reviewer;
2. preserve the reviewed source claims, gaps, audit binding, and all
   `FAIL_AS_PRINTED` boundaries;
3. recompute and bind the resulting note hash in the manifest;
4. rebuild generated discovery artifacts and rerun the corpus audit.

Any change to a claim, locator, epistemic class, gap scope, source hash, audit
hash, theorem status, or exclusion boundary requires a fresh semantic review;
it is not covered by this PASS.

## Final gate

- `read_status: complete`
- `evidence_status: persisted`
- `source-only admission decision: PASS`
- `current manifest admission performed: no`
- `Theorem III.1 mathematical status: FAIL_AS_PRINTED`
- `Appendix B proof status: FAIL_MULTIPLE_INDEPENDENT_FATAL_ERRORS`
- `printed double-sided 20-class bridge: contradicted`
- `narrow existential theorem: open`
- `PEPS result: source-local missing`
- `measurement--reset--Record result: source-local missing`
- `project no-go: not established`

This source may be admitted only as a faithful record of what it says,
including what it says incorrectly and what it does not address.

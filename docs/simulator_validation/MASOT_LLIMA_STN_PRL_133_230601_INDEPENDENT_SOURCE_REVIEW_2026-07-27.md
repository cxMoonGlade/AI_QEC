# Independent source-only admission review — Masot-Llima and Garcia-Saez, PRL 133, 230601

Date: 2026-07-27

Reviewer: `codex-independent-source-review-stn-vor-2026-07-27`

Verdict: **FAIL — correction and fresh independent re-review required**

The draft is close to an admissible source-only record, and its three named
source anomalies are real. It cannot pass yet because it omits a separate
load-bearing domain defect in Supplemental Lemma 3, overstates one
version-of-record addition as “implemented,” and gives an incomplete locator
for the basis-update part of the two-term-unitary claim.

This review does not modify the reading note, audit packet, source artifacts,
or `docs/papers/CURRENT_CORPUS.toml`.

## Reviewed immutable snapshots

| object | pages | SHA-256 |
|---|---:|---|
| `docs/papers/PhysRevLett.133.230601_version_of_record.pdf` | 6 | `7630570f2d8281ac29a99075082c7e992f8f68aa9d05bd13cf190c473f08946c` |
| `docs/papers/PhysRevLett.133.230601_supplement_version_of_record.pdf` | 11 | `5d9dcbd7746b79c38678a72fb42f6b4a529ea4678de2b873b0ee85fbc276b2d1` |
| `docs/papers/reading_notes/masot_llima_stabilizer_tensor_networks_prl_133_230601_source_review.md` | — | `f701f7bc25907e3d7492fe5c5172c7512cd09c86149ac29e5db267ee874d27d3` |
| `docs/simulator_validation/MASOT_LLIMA_STABILIZER_TENSOR_NETWORKS_PRL_133_230601_SOURCE_ONLY_AUDIT_2026-07-27.md` | — | `4d0fbb3bec3b356865b00f21c698a96fe1ac8a8d0deb8c7aa901f5cb4546c56b` |

The note's `source_sha256` and `audit_packet_sha256` match these objects. The
audit's article and supplement hashes also match. The article is a publisher
PDF whose embedded metadata names the title, DOI, and American Physical
Society; the supplement has the matching title, authors, affiliations, and
November 18, 2024 date. Article Ref. [38] identifies the APS supplemental
member. The supplement is therefore bound through

`note -> hashed audit packet -> hashed official supplement`.

The generic extraction sidecars identify the inputs as local PDFs and do not
attest a retrieval timestamp. They were not used as scientific evidence.

## Isolation and full-text check

The six-page published article and eleven-page official supplement were read
in full before the candidate note or audit was opened. The article's
load-bearing formula pages 1--4 and the supplement's formula pages 1--10 were
rendered from the hashed local PDFs and visually inspected. Text extraction
was used only for traversal. The stored supplement extraction does contain
one NUL byte, as the audit reports.

The quarantined legacy note and prior project syntheses were not opened or
used. Only after the published objects and candidate artifacts had been read
was the pinned primary arXiv v2 artifact consulted for the narrow version
comparison below.

## Version-of-record choice

Using the DOI version of record as authority is correct. The pinned
`arXiv:2403.08724v2` source contains the two-term Lemma 2 treatment and ends
its worked supplement by saying that implementation of unitaries with
arbitrary decomposition is future work. The published supplement adds Eqs.
(17)--(19), which state a formal product-of-rotations extension, and adds the
cluster, toric-code, and maximally nonlocal locality examples.

That difference supports “published formal multi-term extension” or
“published implementability statement.” It does not support the audit's
unqualified phrase “adds an implemented multi-term-unitary statement,”
because Supplemental PDF page 10 still says that implementation of unitaries
of arbitrary decomposition is left for future work. The audit otherwise
correctly labels this row `closed_as_source_statement`, not as a verified
software implementation.

## Schema and manifest boundary

The current parser rejects the note for exactly the expected front-matter
gate:

```text
admission_status must be 'source_only_reviewed'
```

An in-memory diagnostic that changed only
`admission_status = "draft_pending_review"` to
`admission_status = "source_only_reviewed"` passed every remaining current
schema, source-only-marker, locator-page, source-hash, and audit-hash check:
21 evidence records comprising 14 `paper_fact` and 7 `literature_gap`
records.

That diagnostic is structural only. It cannot override the semantic defect
below. The note is absent from `CURRENT_CORPUS.toml`, as a pending draft must
be. No admission or manifest mutation occurred.

## Blocking source discrepancy — Supplemental Lemma 3

Supplemental Lemma 3, PDF page 4, defines \(k\) as the position of the first
one in \(\hat n\) and states the coefficient operation

\[
P_k\widetilde R_{X_{I_x}Y_{I_y}Z_{I_z}},
\qquad P_k=\lvert0\rangle\langle0\rvert_k .
\]

The lemma is stated for an observable
\(O=\alpha\delta_{\hat n}\sigma_{\hat m}\) without the hypothesis
\(\hat n\ne0\). When \(\hat n=0\), no such \(k\) exists and the projector
\(P_k\) is undefined.

The proof recognizes the \(\hat n=0\) case in Eq. (27), where the correct
coefficient update is directly proportional to
\((I\pm\alpha Z_{\hat m})\lvert\nu\rangle\) and the stabilizer basis is not
updated. It then tries to rejoin the two cases by “defining”
\(\hat i_k\equiv0\) when \(\hat n=0\). That convention does not define a
physical coefficient qubit or \(P_k\), and it is incompatible with the later
Eq. (34) step

\[
\hat i_k=0\iff(\hat i+\hat n)_k=1,
\]

because for \(\hat n=0\) the two indexed bits are equal.

The draft records the other Eq. (34) defect correctly: an intermediate line
puts the already-global \(\langle\psi|O|\psi\rangle\) inside a remaining
summation without the coefficient factors needed for that equality. It does
not record the missing-\(k\) domain defect or the invalid rejoining of
\(\hat n=0\).

The final physical projector norm
\(\sqrt{(1\pm\langle O\rangle)/2}\) remains correct directly from
\((I\pm O)/2\) for a Hermitian Pauli observable. What is not established as
written is one uniform \(P_k\widetilde R\) coefficient operation, with the
stated normalization proof, for both \(\hat n\ne0\) and \(\hat n=0\).

Admission therefore requires the measurement records and replay to separate:

1. \(\hat n\ne0\): the source's \(k\), \(P_k\), basis update, and
   coefficient transformation;
2. \(\hat n=0\): the no-basis-update Eq. (27) diagonal projection;
3. the physical Born norm, supported independently by the projector
   identity, from the flawed uniform proof.

## Evidence-record-by-record review

| Fact ID | independent source check | status |
|---|---|---|
| `stn-vor-source-identity` | Article title block, publication history, DOI, matching supplement title block, and audit hash chain support the identity. The fact locator should also name the supplement title page or article Ref. [38], because article page 1 alone does not establish the companion object. | `supported; locator completion required` |
| `stn-vor-coefficient-representation` | Article Fig. 1(b) and Eq. (2) represent amplitudes in \(\mathcal B(S,D)\) by \(\lvert\nu\rangle\), stored as a TN. | `pass` |
| `stn-vor-basis-completeness` | Supplemental Lemma 1 proves normalization, orthogonality, and \(2^n\)-element completeness for the destabilizer-generated basis. | `pass` |
| `stn-vor-clifford-update` | Article page 2 states that the coefficients are unchanged; Eq. (4) on page 3 writes \(G\lvert\nu\rangle=\lvert\nu\rangle\). The body correctly notes the page break. | `pass` |
| `stn-vor-two-term-nonclifford` | The rotation is supported by article Eqs. (5)--(6). The additional “basis update plus rotation” wording is established by Supplemental Lemma 2 and Eqs. (7)--(16), not by the note's article-only locator. | `supported; exact locator incomplete` |
| `stn-vor-multiterm-extension` | Published supplement Eqs. (17)--(19) state a formal sequence-of-rotations extension. Supplemental page 10 preserves arbitrary-decomposition implementation as future work. | `pass only as source statement` |
| `stn-vor-observable-expectation` | Article Eq. (7), reproduced in supplement Eqs. (20)--(21), gives \(\alpha\langle\nu|X_{\hat n}Z_{\hat m}|\nu\rangle\). | `pass` |
| `stn-vor-selective-born-outcome` | The source gives \(p_\pm\), outcome selection, and separate coefficient/basis update formulas. The one-projector summary must be qualified by the \(\hat n=0\) case above. | `correction required` |
| `stn-vor-measurement-branch-norm` | The physical projector norm is correct, but Supplemental Lemma 3 does not prove one uniform \(P_k\widetilde R\) rule for \(\hat n=0\). | `qualification and paired gap required` |
| `stn-vor-measurement-bond-risk` | Article page 3 explicitly says non-Clifford gates and measurements can introduce coefficient correlations that increase \(\chi\). | `pass` |
| `stn-vor-mps-backend` | The concrete coefficient backend is a one-dimensional MPS. | `pass` |
| `stn-vor-t-product-example` | Eqs. (11)--(12) give the bond-one coefficient-MPS example with maximal pseudo-stabilizer rank. | `pass` |
| `stn-vor-operator-schmidt-bound` | Eq. (42) has at most \(k\chi\) product terms, which supports a Schmidt-rank upper bound. The record correctly rejects the stronger “already a Schmidt decomposition” prose. | `pass` |
| `stn-vor-routing-bounds` | Supplemental Fig. 1 and page 9 give \(4\chi\) for the two-CNOT crossing pattern and \(16\chi\) with SWAP routing, with higher-connectivity TNs reducing that bound at greater contraction cost. | `pass` |
| `stn-vor-gap-basis-index` | Article Eq. (2) visibly prints the inclusive upper limit \(2^n\), inconsistent with a \(2^n\)-element basis and supplemental indexing through \(2^n-1\). | `pass` |
| `stn-vor-gap-measurement-proof` | The named global-expectation summation error in Eq. (34) is real, but this gap is incomplete because it omits the undefined-\(k\) and invalid-\(\hat n=0\)-rejoining defect. | `incomplete; blocking` |
| `stn-vor-gap-schmidt-wording` | Operator-basis orthogonality does not imply mutual orthogonality of all \(A_j\lvert\psi_A^i\rangle\), \(B_j\lvert\psi_B^i\rangle\) pairs. The \(k\chi\) rank bound nevertheless survives. | `pass` |
| `stn-vor-gap-reset-record` | Neither object specifies reset, ordered branch histories or prefix masses, repeated-round detector Records, observable folds, or a complete Record-law metric. | `pass` |
| `stn-vor-gap-peps-qec` | The supplement discusses a toric-code stabilizer-basis example and mentions QEC, but it implements neither syndrome extraction nor a QEC benchmark; no PEPS coefficient backend is constructed. | `pass with this precise “no result/implementation” wording` |
| `stn-vor-gap-matched-efficiency` | The source gives analytic per-operation rank bounds and a single-gate coefficient-entanglement study, not a matched-accuracy runtime or peak-memory comparison. | `pass` |
| `stn-vor-gap-qudit` | The presented rules are binary \(n\)-qubit tableau/Pauli rules; no qutrit, leakage, or general-qudit backend is supplied. | `pass` |

## Audit-packet row review

| assigned row | review |
|---|---|
| stabilizer-basis coefficient representation | faithful |
| Clifford update | faithful |
| two-term non-Clifford update | faithful in the audit because it cites Supplemental Lemma 2; the note locator must be brought into agreement |
| multi-term unitary statement | faithful only as a formal source statement; replace the version-choice word “implemented” and retain the page-10 future-work limit |
| selective projective measurement | incomplete until the \(\hat n=0\) branch and Lemma 3 domain defect are explicit |
| coefficient-bond behavior under measurement | faithful; the source permits increase and gives no monotone-shrink result |
| concrete tensor-network backend | faithful for MPS; PEPS remains missing |
| operator-Schmidt bond bound | faithful as a rank bound; the stronger Schmidt-decomposition prose is correctly rejected |
| reset and complete Record law | faithful source-local absence |
| QEC/PEPS efficiency result | faithful when read as absence of an implementation or matched empirical result, not absence of QEC mentions |

The notation ledger is source-faithful. The operation replay is faithful for
the representation, Clifford update, non-Clifford update, and rank bound. Its
measurement replay must be split by \(\hat n=0\) versus \(\hat n\ne0\) before
it can be complete.

The audit's legacy-disconfirmation section was not used to grade admission,
because this review intentionally did not open the quarantined legacy note.
The current candidate stands or falls against the published source alone.

## Correctly retained anomalies and absences

The draft correctly preserves all of the following:

- article Eq. (2)'s inclusive \(2^n\) indexing inconsistency;
- Eq. (34)'s malformed intermediate global-expectation summation;
- Eq. (42)'s unjustified “valid Schmidt decomposition” wording while
  retaining the \(k\chi\) product-count rank bound;
- the source's explicit warning that measurement can increase coefficient
  bond dimension;
- absence of reset and a complete multi-round Record law;
- absence of a PEPS coefficient implementation and syndrome/QEC benchmark;
- absence of qutrit/leakage rules;
- absence of a matched-accuracy runtime, memory, and accuracy comparison.

The source does make theoretical efficiency and per-operation bond-growth
claims. The admissible absence is therefore “no matched empirical efficiency
result,” not “no efficiency discussion or result of any kind.” Likewise, the
source mentions QEC and gives a toric-code locality example; the admissible
absence is “no QEC implementation or benchmark,” not “no QEC content.”

## Exact admission boundary after correction

This source may support only:

1. a tableau-defined stabilizer basis with a coefficient state represented
   concretely as an MPS;
2. exact Clifford conjugation of that basis with unchanged coefficients;
3. the source's two-term pulled-back Pauli-axis rotation and its published
   formal multi-term factorization statement;
4. a selective Pauli-measurement primitive, with \(\hat n\ne0\) and
   \(\hat n=0\) handled separately and with the Born norm justified by the
   projector identity rather than the flawed uniform proof;
5. the qualitative possibility that measurement increases coefficient
   correlations and bond dimension;
6. the product-count Schmidt-rank bound \(k\chi\) and the source's
   operation-local \(4\chi/16\chi\) routing bounds.

It may not support:

- reset or a measurement--reset instrument;
- ordered branch-history or prefix masses;
- a repeated-round detector/observable Record law or Record metric;
- monotone bond reduction under measurement;
- PEPS residual mechanics, truncation, or faithfulness;
- a syndrome-extraction or QEC benchmark;
- qutrit, leakage, or general-qudit operation rules;
- empirical runtime, peak-memory, matched-accuracy, or production-efficiency
  advantage;
- the claim that Eq. (42)'s displayed vectors are already Schmidt
  orthogonal.

## Required promotion sequence

Before another independent admission attempt:

1. add the missing Lemma 3 \(\hat n=0\) gap and qualify the measurement facts
   and operation replay;
2. replace “implemented multi-term-unitary statement” with an exact formal
   source-statement description and cite the page-10 future-work limit;
3. add Supplemental Lemma 2 to the two-term basis-update locator and complete
   the supplement locator in the source-identity record;
4. recompute the audit hash stored in the note after any audit edit;
5. run a fresh independent semantic review;
6. only after a PASS, set the admission reviewer/status, recompute the note
   hash, validate the artifact, and add that exact identity to
   `CURRENT_CORPUS.toml`.

Until all six steps occur:

- `read_status: complete`
- `evidence_status: persisted_pending_correction`
- `independent_source_review: fail`
- `current_corpus_admission: no`


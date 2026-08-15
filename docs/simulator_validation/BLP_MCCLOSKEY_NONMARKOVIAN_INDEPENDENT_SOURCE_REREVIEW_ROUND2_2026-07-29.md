# BLP / McCloskey–Paternostro non-Markovianity — independent source-only rereview, Round 2

Date: 2026-07-29
Review basis: the two fixed PDFs, the repaired source notes, and their named audit packets only
Verdict: **REQUIRED REPAIRS**

This is a fresh source-only rereview. The fixed PDFs were reopened, extracted into a new temporary
directory, read in full, and freshly rendered for direct inspection. Candidate-note and audit prose
was not accepted as source evidence. No candidate note, candidate audit, PDF, or corpus manifest was
edited by this review.

## 1. Exact reviewed identities

| object | SHA-256 | independent check |
|---|---|---|
| `docs/papers/0908.0238v2.pdf` | `9e05b98a5b6a902be4fa8d4d2662b7e9b7592d150ddef6bf74a8d6e9f9bf4553` | valid PDF 1.4, 4 pages, `%PDF-` head, `%%EOF` tail |
| repaired BLP note | `e4b2adcefe14e970491c1706fafd96d81b4514a987803b4dd50605a61ee7e16c` | source hash and audit hash resolve |
| repaired BLP audit | `4151228066fc7e6e195c43debc3435dce7484b8169ab46352adfd356a2fa6b19` | exactly equals note `audit_packet_sha256` |
| `docs/papers/1402.4639v3.pdf` | `eee6e79e1f217b1c041ae524867c2785c773a9eb9050020927d1b485a0a846cc` | valid PDF 1.5, 7 pages, `%PDF-` head, `%%EOF` tail |
| repaired McCloskey–Paternostro note | `f436e54e0140a43e6cf7b66f325134a79c6478687b061f99c58c3ba6c0d64ad8` | source hash and audit hash resolve |
| repaired McCloskey–Paternostro audit | `5749cca16cb9d09cc5b3660cb65d17cdb61abf79ea82dc2b4c51c03b81307d9a` | exactly equals note `audit_packet_sha256` |

The BLP artifact visibly carries both `arXiv:0908.0238v2 [quant-ph] 5 Jan 2010`
and `Dated: October 26, 2018`. The McCloskey–Paternostro artifact visibly
carries both `arXiv:1402.4639v3 [quant-ph] 26 May 2014` and
`Dated: November 27, 2021`. The repaired source records now preserve these
pairs without inventing an explanation and classify the fixed arXiv objects
as preprints. The unsupported self-publication locators and journal-status
claims from Round 1 are gone.

Freshly inspected pages were BLP 1–4 and McCloskey–Paternostro 1–6. Page 7 of
the latter contains only the remaining references and was traversed in the
full-text read; it carries no load-bearing equation or figure used by the
candidate note.

## 2. Round-1 repair disposition

| prior required repair | Round-2 disposition |
|---|---|
| remove or separately source journal-publication assertions; preserve both visible date lines | **PASS** |
| split BLP trace-distance interpretation, exact-evaluation/lower-bound records, and five bundled gaps | **PARTIAL** — the requested splits landed, but two BLP records still combine independently paged evidence and declare only page 2 |
| normalize the BLP information-backflow relation | **STRUCTURAL PASS, SEMANTIC REPAIR STILL NEEDED** — the endpoint resolves, but \(\sigma\) itself is not a “positive rate” by definition |
| mark the BLP discrete increment replay as an audit derivation | **PASS** |
| record both independent defects in McCloskey Eq. (8) | **PASS** |
| replace “earlier revivals,” split retention findings, and inspect page 5 | **PASS for those requested changes**; a new \(\gamma\)-scope overstatement remains |
| split stochastic rule/finding and keep the unknown distribution outside source closure | **PASS** |
| split the four McCloskey tensor-network/resource gaps | **PASS** |
| preserve distinct \(\gamma\) and \(\delta\) | **PASS in the collision rows and algebra**; one replay row still renames the source's \(\widehat E\) operation as \(U\) |
| add the exact phase-bearing partial-SWAP replay and consuming-API sign | **PASS algebraically** |
| recompute audit hashes before rereview | **PASS** |

## 3. BLP source fidelity

The following repaired records are source-faithful and atomic at their stated
scope:

- `blp-source-identity`
- `blp-selection-scope`
- `blp-trace-distance`
- `blp-trace-distance-distinguishability`
- `blp-cpt-contraction`
- `blp-divisible-monotonicity`
- `blp-finite-spin-bath`
- `blp-fixed-pair-lower-bound`
- all five now-separated source-local tensor-network/resource gaps

All three relation endpoints resolve in the note. The fixed-pair relation and
trace-distance relation use source concepts present in their target Claims.

Three BLP repairs remain.

### 3.1 \(\sigma\) is a rate of change, not a positive rate by definition

BLP Eq. (10), PDF page 2, defines

\[
\sigma(t,\rho_{1,2}(0))
=\frac{d}{dt}D(\rho_1(t),\rho_2(t)).
\]

The surrounding text explicitly discusses both \(\sigma\leq0\) and
\(\sigma>0\). The repaired Claim currently says that the source “defines the
positive trace-distance rate \(\sigma=\cdots\).” That wording changes the
domain of the defined object. It should instead say that the source defines
the **trace-distance rate** \(\sigma\), and calls the process non-Markovian
when that rate is positive for some pair and time. The relation should use an
object such as:

```toml
object_id = "blp-trace-distance-rate"
object_label = "trace-distance rate"
```

This is a source-semantic repair, not merely terminology.

### 3.2 `blp-integrated-measure` still crosses pages inside one record

The record currently names `Eqs. (11)–(12)`, declares `PDF page: 2`, and
claims both the positive-rate integral and its endpoint sum. Eq. (11) is on
PDF page 2; Eq. (12) and the endpoint-sum explanation are on PDF page 3.
Because these are independently located reusable facts, one page-2 record
does not give an exact page for the page-3 assertion.

Required repair:

1. retain one atomic Eq. (11), PDF-page-2 record for the optimized positive
   integral; and
2. add a distinct Eq. (12), PDF-page-3 record for the sum over positive-rate
   interval endpoints.

### 3.3 `blp-optimization-limit` still crosses pages and duplicates the maximum

This record declares `PDF page: 2`, but its Claim combines:

- maximization over every initial pair from Eqs. (11)–(12), pages 2–3; and
- the complete-reduced-dynamics requirement from the conclusion, page 4.

The maximum is already represented by the integrated-measure record. Narrow
`blp-optimization-limit` to the conclusion's complete-reduced-dynamics
requirement with `PDF page: 4`, or split the two statements into exact,
single-page records. If the existing fixed-pair relation is retargeted during
that cleanup, its Fact ID must continue to resolve to a paper fact whose Claim
contains its object label.

The BLP audit's operation replay now correctly labels positive successive
increments as a discrete audit derivation rather than as a formula printed in
BLP. Its source/evaluation distinction is faithful.

## 4. McCloskey Eq. (8): both defects are now closed honestly

Fresh visual inspection of PDF page 3 again confirms the literal display

\[
\mathcal N=\max\sum_n\left[
D(\rho^S_{1,n},\rho^S_{2,n})
-D(\rho^S_{2,n-1},\rho^S_{2,n-1})
\right].
\]

The repaired note and audit now preserve two separate defects:

1. \(D(\rho^S_{2,n-1},\rho^S_{2,n-1})=0\), so the second term is not the
   distance between the two previous trajectories; and
2. Eq. (8) has an unrestricted \(\sum_n\), although Eq. (7) integrates only
   where \(\partial_tD>0\).

Repairing only the arguments would telescope and would not sum positive
growth. The audit's

\[
\mathcal N_{\rm pair}^{(R)}
=\sum_{n=1}^{R}\max\!\left[
0,\,
D(\rho^S_{1,n},\rho^S_{2,n})
-D(\rho^S_{1,n-1},\rho^S_{2,n-1})
\right]
\]

is correctly labeled a fixed-pair, cross-source project derivation from BLP,
not a silent McCloskey correction and not the optimized \(\mathcal N\).

**Eq. (8) Round-2 result: PASS.**

## 5. Partial-SWAP replay

For the source's system–ancilla operation,

\[
\widehat U_{S,j}(\gamma)
=\cos\gamma\,I+i\sin\gamma\,\mathrm{SWAP}
=e^{i\gamma\mathrm{SWAP}},
\]

and

\[
\mathrm{SWAP}=\frac{I+XX+YY+ZZ}{2}.
\]

The three nonidentity Pauli products commute, so the repaired audit's exact
phase-bearing identity is correct:

\[
\widehat U_{S,j}(\gamma)
=e^{+i\gamma/2}
e^{i\gamma XX/2}
e^{i\gamma YY/2}
e^{i\gamma ZZ/2}.
\]

For \(R_{PP}(\theta)=e^{-i\theta PP/2}\), the three API angles are
\(\theta=-\gamma\). Replacing \(\gamma\) by \(\delta\) gives the same algebra
for the adjacent-ancilla operation. A fresh independent complex128 replay at
\(\gamma=0.37\) found:

```text
SWAP Pauli-identity residual       0
XX/YY/ZZ commutator residuals      0, 0, 0
phase-bearing matrix residual      1.2412670766236366e-16
```

This agrees with the audit's rounded \(1.25\times10^{-16}\).

One symbol repair remains. McCloskey Eq. (3) names the adjacent-ancilla
unitary \(\widehat E_{j,j+1}(\delta)\), not
\(U_{j,j+1}(\delta)\). The final operation-replay row calls its input the
“source ancilla–ancilla partial SWAP \(U_{j,j+1}(\delta)\).” Replace that
symbol with the source's \(\widehat E_{j,j+1}(\delta)\). The transformation,
global-phase sign, and negative consuming-API angle are otherwise correct.

**Partial-SWAP algebra result: PASS; source-symbol replay result: REPAIR.**

## 6. McCloskey interaction-strength scope

`mp-retention-threshold` correctly replaces the unsupported “earlier
revivals” statement with the source-supported lower threshold in \(\delta\).
The exact evidence is Fig. 4 and its surrounding page-5 discussion. Its
locator should therefore be narrowed from `Figs. 3–4` to `Fig. 4`, and the
Claim should call \(\delta\) the intra-environment or adjacent-ancilla
interaction strength, avoiding the ambiguous “ancilla-interaction strength.”

`mp-interaction-strength-dependence` overstates the displayed parameter
study. Figs. 3–4 vary \(\delta\) while fixing
\(\gamma=0.05\); they do not establish a two-parameter dependence on both
\(\gamma\) and \(\delta\). The complete-text occurrence check found:

- Eq. (1) defines \(\gamma\);
- Eqs. (3)–(4) distinguish \(\delta\) from \(\gamma\);
- Figs. 2–5 keep \(\gamma=0.05\); and
- Figs. 3–4 vary \(\delta\).

Required repair: limit the Claim to dependence on \(\delta\) at the displayed
\(\gamma=0.05\), with exact Fig. 3/Fig. 4 parameter regimes, unless another
exact source locator is supplied for a \(\gamma\) sweep. The abstract's
phrase “all coupling strengths” does not turn the fixed-\(\gamma\) figures
into a resolved two-parameter result.

The other McCloskey paper facts, the two Eq. (8) gaps, and the four separate
tensor-network/resource gaps are source-faithful at their declared scope.
Both retained relations resolve to paper facts and use source concepts in
their Claims.

## 7. Stochastic-threshold boundary

PDF page 6 says only that a random variable is drawn, a collision occurs when
the draw is below a threshold in \([0,1]\), and the displayed
\(\delta=\pi/2\) case changes oscillation period without changing amplitude
when collision occurrence is reduced. It does not specify the draw's
distribution.

The repaired artifacts now separate:

- the source-stated draw-and-threshold rule;
- the displayed full-swap period/amplitude finding;
- the source-local missing distribution; and
- a uniform draw and Bernoulli mask as a project choice.

No source statement is used to identify the numerical threshold with a
Bernoulli event probability.

**Stochastic-threshold boundary result: PASS.**

## 8. Real artifact-verifying parser shadow

The production parser sources used were:

| parser object | SHA-256 |
|---|---|
| `tools/literature_schema.py` | `6ab50f261fb64e11319831cc796bad341c4c73638144ad58cdae33d080eb23e3` |
| `tools/literature_rag.py` | `47092f7cd0f62965e7451d5f5c318fa66f4a7e03687cb86af8cd9eb50a49d00d` |

Runtime: Python 3.12.13 in the `ecs` environment.

Direct artifact-verifying `parse_note` calls on the exact on-disk candidates
both stopped at the intended pre-admission gate:

```text
BLP         EXPECTED_FAIL admission_status must be 'source_only_reviewed'
McCloskey   EXPECTED_FAIL admission_status must be 'source_only_reviewed'
```

An isolated root was then created under
`/tmp/blp-mccloskey-round2-shadow.8WDsyV`. Exact copies of both PDFs and both
audit packets were placed at their declared repository-relative paths.
Only these two front-matter fields were changed in each temporary note:

```toml
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-rereview-blp-mccloskey-round2-2026-07-29"
```

No Claim, locator, page, relation, source hash, or audit hash was changed. The
real production command

```text
conda run -n ecs python tools/literature_rag.py \
  --repo-root /tmp/blp-mccloskey-round2-shadow.8WDsyV \
  audit --notes-dir docs/papers/reading_notes --strict
```

returned `verification_mode="artifact_verified"`,
`validated_count=2`, and `excluded_count=0`. Exact parser results were:

| shadow note | evidence records | paper facts | gaps | relations | checked pages | diagnostic SHA-256 |
|---|---:|---:|---:|---:|---|---|
| BLP | 16 | 11 | 5 | 3 | 1, 2, 3, 4 | `ab1471aef67862d66de14c7df6452a8d8cd2a90c0175c84130bd9b4380f67bad` |
| McCloskey–Paternostro | 21 | 14 | 7 | 2 | 1, 2, 3, 4, 5, 6 | `3bd7e7cadcdac7ce789a0812b045e556a63da9e2cf934eda5f742b7b03098162` |

Those are diagnostic shadow hashes only and must not enter
`CURRENT_CORPUS.toml`.

The current manifest SHA-256 is
`3a9445ccffdc2fbc21f4f2b3ce3e13f021d072a060d41ea87f12b1afcb29cd29`.
Neither candidate path nor source ID occurs in it. The read-only manifest
check reported 288 candidates, 44 audit-valid notes, 44 manifest entries,
zero orphaned notes, and zero stale entries. Exclusion of these pending notes
is therefore correct.

The shadow proves current structural shape, source/audit hash resolution,
checked-page membership, Fact-ID uniqueness, and relation endpoint validity.
It does not establish semantic atomicity, exact cross-page locators, or
source-faithful parameter scope; the blockers in Sections 3, 5, and 6 are
outside what the parser checks.

## 9. Actionable required repairs

1. In `blp-positive-rate-witness`, define \(\sigma\) as the trace-distance
   rate and reserve “positive” for the condition \(\sigma>0\); normalize its
   relation object ID/label accordingly.
2. Split `blp-integrated-measure` into an Eq. (11), page-2 integral record and
   an Eq. (12), page-3 endpoint-sum record.
3. Narrow `blp-optimization-limit` to the complete-reduced-dynamics
   requirement on page 4, or split its page-2/3 maximum and page-4 conclusion
   into separate records.
4. Narrow `mp-retention-threshold` to Fig. 4, page 5, and call \(\delta\) the
   intra-environment or adjacent-ancilla interaction strength.
5. Restrict `mp-interaction-strength-dependence` to the displayed
   \(\delta\) dependence at fixed \(\gamma=0.05\), unless an exact source
   locator for a \(\gamma\) sweep is supplied.
6. In the adjacent-ancilla partial-SWAP replay, replace the non-source symbol
   \(U_{j,j+1}(\delta)\) with the source's
   \(\widehat E_{j,j+1}(\delta)\).
7. Recompute any changed audit hash in its owning note, then rerun the real
   artifact-verifying parser shadow and a semantic source-only rereview
   before changing either admission status.

## 10. Source-local completion table

| assigned row | exact source location | paper says | paper does not say | status |
|---|---|---|---|---|
| BLP trace-distance metric and witness | BLP Eqs. (1), (2), (5), (9)–(10), PDF pp. 1–2 | trace distance contracts for the source's divisible construction; \(\sigma>0\) for some pair/time is the witness | \(\sigma\) is not positive by definition | source row closed; note terminology requires repair |
| BLP optimized measure | BLP Eqs. (11)–(12), PDF pp. 2–3; conclusion p. 4 | optimized positive growth defines \(\mathcal N\); exact evaluation needs complete reduced dynamics | it does not print the audit's sampled discrete formula | source row closed; note atomicity/pages require repair |
| BLP finite-spin example | BLP Eq. (14), PDF p. 4 | suitable pairs show periodic trace-distance exchange | no tensor-network monotonicity follows | closed |
| McCloskey coherent primitives | McCloskey Eqs. (1)–(5), PDF p. 2 | distinct \(\gamma\) and \(\delta\) partial SWAPs define the collisions | it does not print the Pauli decomposition | source row closed; project algebra passes; one replay symbol requires repair |
| McCloskey Eq. (8) | McCloskey Eqs. (7)–(8), PDF p. 3 | Eq. (7) selects positive growth | Eq. (8) has both a self-distance and no positive selector | contradicted/missing as printed; repaired note passes |
| correlation-retention threshold | McCloskey Fig. 4 and Sec. II.A, PDF p. 5 | Strategy 2 reaches nonzero optimized \(\mathcal N\) at a lower \(\delta\) in the displayed fixed-\(\gamma\) study | the displayed figures do not sweep both \(\gamma\) and \(\delta\) | threshold closed; two note locators/scope statements require repair |
| stochastic occurrence | McCloskey Sec. II.B and Fig. 6, PDF p. 6 | draw-and-threshold rule and the displayed full-swap period/amplitude result | no draw distribution identifies threshold with Bernoulli probability | source rule closed; Bernoulli bridge missing source-locally |

- independent `read_status`: `complete` for both fixed PDFs
- candidate `evidence_status`: `persisted`
- parser-shadow status: `PASS_ALL_REMAINING_STRUCTURAL_AND_ARTIFACT_CHECKS`
- semantic admission verdict at the reviewed hashes: **REQUIRED REPAIRS**


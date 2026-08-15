# Harper et al. arXiv:2605.29514v1 — independent source rereview

Date: 2026-07-27  
Reviewer: `/root/rereview_harper2605`  
Decision: **FAIL — not admissible to the source-only corpus**

This is an admission decision about the candidate evidence packet, not a rejection
of the paper as useful adjacent evidence. The paper does support a narrow claim
that GCAMPS was used with a Clifford frame and an MPS residual to simulate
coherent crosstalk in repeated rotated-surface-code syndrome extraction. It does
not support a PEPS/CAPEPS implementation, a complete measurement Record law, or
a matched efficiency or scaling claim.

## 1. Review protocol and independence

The exact pinned artifact
`docs/papers/2605.29514v1.pdf` was read from first page through bibliography
before the candidate reading note or audit packet was opened. All eight rendered
PDF pages were visually inspected. In particular, the title/version block,
Table I, Eqs. (1)–(9), the syndrome-extraction and ZZ-decomposition circuits,
and Figs. 1–6 were checked in the rendered source rather than inferred from
text extraction.

Only after that source judgment was fixed were these candidate artifacts read:

- `docs/papers/reading_notes/harper_hybrid_surface_code_2605.29514v1_source_review.md`
- `docs/simulator_validation/HARPER_2605_29514_SOURCE_ONLY_AUDIT_2026-07-27.md`

No legacy Harper note or CAPEPS-specific narrative was used to form the source
judgment. The binding repository contract was treated only as the boundary on
what an admission may later authorize.

## 2. Artifact, hash, and admission-state checks

| artifact or check | observed state | disposition |
|---|---|---|
| pinned PDF | PDF 1.7, 545,689 bytes, unencrypted, 8 pages; title and four authors match the title page | pass |
| pinned PDF SHA-256 | `c13096aa841acf2b2161f18140c56dd9d3549b268969f79328ff0865583a35dd` | matches the note and audit |
| candidate note SHA-256 | `5db78b54d05a06e43f3e199857cc46af092ab1432a0cbc634e4d57cbba553095` | measured, but no manifest entry binds it |
| candidate audit SHA-256 | `9ec02ddd80c7d5ad4d6321805179f3a072b724729287e57487fac3b7ae2a0376` | matches `audit_packet_sha256` in the note |
| current manifest SHA-256 at review time | `a13b89d80a9b3ce1a99f7d642ed43670d3c0d5ce91b9a048e776c8cb3b12f42c` | informational; the manifest is concurrently modified and was not edited here |
| note status | `admission_status = "draft_pending_review"`; reviewer is `pending_fresh_independent_source_only_review` | blocking |
| audit status | `DRAFT_PENDING_FRESH_INDEPENDENT_REVIEW`; independent reviewer `pending` | blocking |
| direct note validation | fails at `admission_status must be 'source_only_reviewed'` | blocking |
| current-corpus membership | no entry for arXiv:2605.29514v1 | correctly excluded |
| corpus drift check | 277 candidates, 37 audit-valid, 37 manifested, 0 orphaned, 0 stale | current manifest correctly equals the already-valid set |

At the start of this rereview there was no durable independent-review report for
the earlier claimed admission; the candidate audit itself acknowledges that
absence and withdrew the prior status. This file supplies a durable rereview,
but its decision is FAIL, so it cannot be used to replace the placeholders with
a passing reviewer or to admit the note.

The note has 20 `paper_fact` records and 7 `literature_gap` records. Their
required field order is present, Fact IDs are unique, and all nine relation
references name existing `paper_fact` IDs. Those manual shape checks do not
override the validator failure or the semantic findings below.

## 3. Independent source-only reconstruction

### 3.1 Scientific object

The source studies rotated-surface-code memory experiments with distances
\(d=3,5,7,9\). Syndrome extraction is repeated for \(d\) rounds. Figure 1
shows face ancillas prepared in \(|0\rangle\), ordered CNOT check circuits, and
ancilla measurement. The baseline model assigns error-rate multiples to
single-qubit gates, two-qubit gates, reset, and measurement. A gate-based,
nearest-neighbour coherent \(ZZ\) channel is placed after entangling operations.

The paper retains coherent forward dynamics but uses a PyMatching decoder whose
error model is generated from the Pauli-twirled approximation. Its observable is
the average of syndrome-associated logical-rotation distances in Eq. (1), not a
published detector/observable Record distribution.

### 3.2 GCAMPS and QEC positioning

Section IV explicitly says that the reported simulations use the GCAMPS library.
The state is represented as

\[
|\psi\rangle=C|\mathrm{MPS}\rangle,
\]

with the ideal Clifford QEC circuit accumulated in \(C\) and the non-Clifford
perturbation carried by the MPS. Clifford gates update \(C\); Pauli terms from a
non-Clifford operation are pulled through \(C\) and applied to the MPS. The
paper warns that a physically local Pauli word can thereby become high weight
on the residual tensor network.

This is GCAMPS/Clifford-frame/MPS evidence. The conclusion lists PEPS and tree
tensor networks only as possible future layouts. The paper never presents a
\(C|\mathrm{PEPS}\rangle\) algorithm, CAPEPS implementation, PEPS result, or
PEPS correctness or resource certificate.

### 3.3 Reported findings and their scope

For Fig. 4 the paper reports \(10^5\) samples per point. It says that adding
crosstalk moves the threshold from about \(1\%\) to \(0.8\%\), while retaining
coherence raises sub-threshold logical error further without a statistically
significant additional threshold shift. The latter detailed statement limits
the broader wording in the abstract.

The fixed-sign and uniformly random-sign coherent models have the same Pauli
twirl. The source reports different fixed-sign versus random-sign
sub-threshold behaviour, and the Fig. 5 caption specifically says that the
random-sign logical-error curve is identical to the Pauli-twirled
approximation. That latter null/near-null result must be retained alongside the
claim that a twirl can be insufficient.

The paper caps all post-truncation-study simulations at
\(\chi_{\max}=32\). Its downward-bias and lower-bound statements are empirical
interpretations of this workload, not state-fidelity, complete-instrument, or
Record-distance theorems.

## 4. Formula, circuit, and figure audit

| source object | rendered-source finding | candidate treatment | admission consequence |
|---|---|---|---|
| Eq. (1) | \(P_L=N^{-1}\sum_i|\sin(\theta_i/2)|\) is printed as the logical-error observable over sampled syndromes | formula is transcribed faithfully | the paper does not explain how a sampled syndrome and correction are converted into the logical angle \(\theta_i\); the replay omits this bridge |
| Eq. (2) | the printed one-qubit depolarizing sum is followed by an index statement that includes \(I\); read literally, its trace is \(1+p_1/3\), not 1 | not recorded at all | blocking omitted formula ambiguity; an intended \(i\in\{X,Y,Z\}\) repair is plausible but cannot be silently supplied |
| Eq. (3) | the two-qubit formula is normalized if the displayed pair exclusion \((i,j)\ne(I,I)\) is applied | omitted as a formula fact | not independently blocking, but the baseline mechanism is incompletely reconstructed |
| Fig. 1 | ancilla preparation, four CNOTs, measurement, and dashed post-CNOT crosstalk locations are visible; no outcome-resolved reset map is shown | high-level circuit and reset/measurement gap are mostly faithful | no Record or reset-instrument promotion |
| Eq. (4) plus ZZ circuit | Eq. (4) prints \(e^{+i\theta ZZ}\), while the circuit prints CNOT–\(R_Z(\theta/2)\)–CNOT and defines no \(R_Z\) convention | captured correctly as an ambiguity | closed as a source-local gap, not as an executable formula |
| Eq. (5), Table I, Secs. III.B/V.A | the source prints \(\theta=J_{ZZ}t_g\), \(\theta=10^{-3}\), \(100\,\mathrm{kHz}\times100\,\mathrm{ns}\), and \(150\,\mathrm{kHz}\times150\,\mathrm{ns}\); the products are \(10^{-2}\) and \(0.0225\) under the printed units | captured correctly | closed as an inconsistency, not one calibrated parameter set |
| Eq. (6) | \((1-\sin^2\theta)\rho+\sin^2\theta\,ZZ\rho ZZ\) is the printed twirl of the displayed Eq. (4) channel | captured correctly | pass at the printed-channel level |
| Eq. (7) | \(|\psi\rangle=C|\mathrm{MPS}\rangle\) is printed | captured correctly | pass |
| non-Clifford displayed derivation | prose names \(T\), equations use \(U\), and a generic Pauli expansion is shown without explicit coefficients | note paraphrases the pull-through but does not preserve either notation defect | blocking omission for operation fidelity |
| Fig. 2 | only the studied central cut is plotted; the caption labels squared Schmidt values, while the y-axis says “Schmidt Value” | note correctly avoids an all-cut theorem | pass with source ambiguity retained here |
| Eq. (8) | the Schmidt sum ends at \(\chi-1\); the following bound uses uppercase \(N\), already used in Eq. (1) for sample count, while Fig. 2 uses lowercase \(n\) for qubit count | \(\chi-1\) is captured; the \(N/n\) ambiguity is omitted | additional missing notation gap |
| Figs. 2–3 | the plots support source-reported convergence for the studied distances/central cut and a \(d=9\) bond-cap scan; they do not prove a global truncation bound | candidate scopes the bias claim to the workload | pass |
| Eq. (9), Figs. 5–6 | random sign is sampled from \(\{\theta,-\theta\}\); same twirl, different fixed/random coherent curves; Fig. 5 says random sign matches the PTA | the same-twirl difference is captured, but the explicit random-sign/PTA agreement is omitted | material contrary/null result should be added |
| threshold plots | no error bars or threshold-fit/uncertainty procedure is printed in the plots or text inspected | candidate repeats the source's statistical-significance statement without promoting it to independent proof | admissible only as “the source reports”; no independently certified threshold |

## 5. Record-by-record audit of the candidate note

`PASS` below means the one stated claim is faithful; it does not cure packet-wide
omissions. `QUALIFY` means the claim is directionally faithful but its evidence
record or locator needs repair before admission.

| Fact ID | exact source check | disposition |
|---|---|---|
| `harper2605-source-identity` | title/version/author block, p. 1 | PASS |
| `harper2605-repeated-syndrome-extraction` | Sec. II text, p. 2; circuit details in Fig. 1, p. 3 | PASS for the claim; the explanatory Fig. 1 details lie on a different page from the recorded page |
| `harper2605-logical-error-observable` | Sec. II, Eq. (1), p. 2 | PASS; missing computation bridge is a packet-level gap |
| `harper2605-error-rate-table` | Table I, p. 2 | PASS for the rate multiples; baseline Eqs. (2)–(3) remain unrecorded |
| `harper2605-coherent-zz-channel` | Sec. III.B, Eqs. (4)–(5), circuit and Fig. 1 caption, p. 3 | PASS because the separate circuit gap preserves the conflict |
| `harper2605-pauli-twirl` | Sec. III.C, Eq. (6), p. 3 | PASS |
| `harper2605-pauli-decoder` | Sec. III.D, p. 3 | PASS |
| `harper2605-hybrid-state` | Sec. IV.A, Eq. (7), p. 4 | PASS |
| `harper2605-clifford-update` | Sec. IV.A displayed equations, p. 4 | PASS |
| `harper2605-nonclifford-pullthrough` | Sec. IV.A displayed derivation, p. 4 | QUALIFY; omitted coefficients and the \(T/U\) switch are not preserved |
| `harper2605-local-to-high-weight` | Sec. IV.A paragraph after the derivation, p. 4 | PASS |
| `harper2605-projective-measurement` | Sec. IV.A measurement paragraph, p. 4 | PASS only at the source's high level |
| `harper2605-qec-frame-interpretation` | Sec. IV.A “specific context” paragraph, p. 4 | PASS |
| `harper2605-no-clifford-optimization` | Sec. IV.A final paragraph, p. 4 | PASS and correctly workload-scoped |
| `harper2605-mps-truncation` | Sec. IV.B, Eq. (8), p. 5 | PASS for the prose rule; incomplete anomaly ledger |
| `harper2605-truncation-bias` | Sec. IV.B discussion of Figs. 2–3, p. 5 | PASS as a source-reported workload interpretation |
| `harper2605-bond-cap` | Sec. IV.B final sentence, p. 5 | PASS |
| `harper2605-coherent-twirled-result` | Sec. V.A prose, p. 5; Fig. 4, p. 6 | QUALIFY; `PDF page: 6` does not locate the \(10^5\)-sample and threshold prose on p. 5 |
| `harper2605-same-twirl-distributions` | Eq. (9) and discussion, p. 5; Figs. 5–6, p. 6 | QUALIFY; the record bundles pages 5–6 and omits the Fig. 5 random-sign/PTA agreement |
| `harper2605-peps-future-work` | conclusion continuation, p. 7 | PASS |
| `harper2605-gap-zz-circuit-convention` | Eq. (4) and circuit, p. 3 | PASS |
| `harper2605-gap-theta-parameters` | Table I, p. 2; Eq. (5), p. 3; Sec. V.A, p. 5 | QUALIFY; true gap, but the single recorded `PDF page: 3` does not cover all compared values |
| `harper2605-gap-schmidt-index` | Eq. (8), p. 5 | PASS |
| `harper2605-gap-outcome-instrument` | Table I, p. 2; measurement prose, p. 4 | QUALIFY; true gap, but it combines independently located reset and measurement claims |
| `harper2605-gap-complete-record` | repeated-round description, p. 2; method/results, pp. 4–6 | QUALIFY; true source-local absence, but `PDF page: 4` is not a complete locator |
| `harper2605-gap-matched-resources` | Sec. IV, pp. 4–5; conclusion, pp. 6–7 | QUALIFY; true absence, but the record bundles several independently locatable comparisons |
| `harper2605-gap-threshold-wording` | abstract, p. 1; Sec. V.A, p. 5 | QUALIFY; correct contradiction/qualification, but `PDF page: 5` alone cannot locate both statements |

Because the schema permits one integer `PDF page` per evidence record and the
template forbids bundling independently locatable claims, the multi-page rows
must be split into atomic records rather than repaired with an unsupported page
range.

## 6. Missing load-bearing records and replay blockers

The following omissions prevent `operation_replay_status = "complete"` from
being accepted semantically:

1. **Baseline Eq. (2) ambiguity.** The note records Table I but not the printed
   single-qubit depolarizing channel or its identity-index/normalization
   ambiguity.
2. **Non-Clifford expansion notation.** The source switches from \(T\) in prose
   to \(U\) in the derivation and omits explicit Pauli coefficients. The note
   currently smooths over both.
3. **Eq. (8) size notation.** The unexplained \(\chi-1\) limit is recorded, but
   the bound's uppercase \(N\) conflicts with the earlier sample-count symbol
   and with Fig. 2's lowercase qubit-count \(n\).
4. **Mechanism-to-observable bridge.** The paper defines \(P_L\) once the
   syndrome-associated logical angles \(\theta_i\) are available, but does not
   specify how the coherent simulated state, syndrome, Pauli-model decoder
   correction, and resulting logical channel are converted into each
   \(\theta_i\). The candidate replay jumps over this transformation.
5. **GCAMPS identification and reproducibility scope.** The source explicitly
   names GCAMPS, but the candidate note never does. It also supplies no
   version/commit, source-code locator, or executable provenance for the library
   used in this experiment.
6. **Contrary/null result.** The Fig. 5 caption's random-sign/PTA agreement is
   absent, leaving the packet more uniformly anti-twirl than the source.

### Operation replay

| input | source transformation | output | source location | replay status |
|---|---|---|---|---|
| rotated surface-code checks | prepare ancilla, ordered CNOT extraction, measure; repeat for \(d\) rounds | sampled syndromes | Sec. II and Fig. 1, pp. 2–3 | closed only at circuit-description level |
| baseline operation | apply printed one- or two-qubit depolarizing channel plus reset/measurement error rates | noisy QEC operation | Eqs. (2)–(3), Table I, p. 2 | missing/ambiguous for Eq. (2) and reset/measurement maps |
| entangling-gate location | apply coherent \(ZZ\) channel | coherent perturbed state | Eqs. (4)–(5), p. 3 | equation closed; printed circuit equivalence missing |
| coherent \(ZZ\) channel | remove coherent cross terms | stochastic \(ZZ\) twirl | Eq. (6), p. 3 | closed for displayed Eq. (4) |
| QEC state | split into Clifford frame and MPS residual | \(C|\mathrm{MPS}\rangle\) | Eq. (7), p. 4 | closed |
| non-Clifford operation | Pauli expansion, pull through \(C\), act on residual | updated MPS | Sec. IV.A derivation, p. 4 | incomplete because coefficients/conventions are unstated |
| projective measurement | pull a Pauli sum through \(C\) and act on residual | paper says residual error collapses to tableau Pauli | Sec. IV.A, p. 4 | high-level only; branch masses/states/reset absent |
| sampled syndrome | PyMatching with PTA-derived error model | inferred correction | Sec. III.D, p. 3 | role closed; exact correction-to-logical-channel map absent |
| coherent state plus correction | unstated transformation | logical angle \(\theta_i\) | between Sec. III.D and Eq. (1) | **missing** |
| logical angles | average \(|\sin(\theta_i/2)|\) | \(P_L\) | Eq. (1), p. 2 | closed conditional on the missing angles |
| MPS across a cut | discard small Schmidt terms at a cap | truncated residual | Eq. (8), Figs. 2–3, pp. 4–5 | qualitative rule closed; indexing and global-error control missing |

## 7. Measurement, reset, Record, and efficiency boundary

- The source shows ancilla preparation and measurement and assigns
  \(p_R=2p\) and \(p_M=5p\).
- It describes projective measurement only as a pulled-through Pauli sum.
- It does not define outcome-resolved Born masses, normalized conditional
  branches, prefix masses, a reset channel or post-reset state invariant, final
  data readout, or a complete joint raw-outcome law.
- It calls the repeated ancilla outcomes an error syndrome. It does not define
  temporal detector folding, logical-observable XOR rows, a canonical Record
  schema, a detector/observable pushforward, or Record total variation.
- Its logical-error observable and truncation convergence cannot be promoted
  into complete Record-faithfulness evidence.
- Its qualitative statement that Clifford-optimization cost outweighed MPS
  bond benefit is workload-specific. No matched-accuracy runtime, peak memory,
  throughput, or scaling comparison is reported for GCAMPS versus full MPS,
  PEPS, CAPEPS, dense execution, or a Pauli tableau route.

## 8. Admission decision and required repair

The packet fails both halves of the requested gate:

1. **Semantic failure:** most atomic claims are faithful, but the packet omits
   Eq. (2)'s normalization/index ambiguity, the non-Clifford coefficient and
   \(T/U\) anomalies, the Eq. (8) \(N/n\) ambiguity, the missing
   correction-to-logical-angle bridge, the explicit GCAMPS identity/provenance
   limit, and the random-sign/PTA null result. Several records also bundle
   independently locatable statements while declaring only one PDF page.
2. **Schema/admission failure:** the validator rejects
   `draft_pending_review`; the reviewer remains a placeholder; the audit is
   draft; and the note is correctly absent from `CURRENT_CORPUS.toml`.

Before another independent admission review:

1. add atomic `paper_fact`/`literature_gap` records for the missing formula,
   notation, GCAMPS, logical-angle-bridge, and contrary-result rows;
2. split the multi-page bundled records so every claim has one exact,
   visually checked PDF page;
3. repair the operation replay without inventing the missing transformations;
4. update the separate audit and then its hash in the note;
5. obtain a new independent semantic review before setting
   `source_only_reviewed` and a real reviewer identity;
6. only after a passing direct validator may the note be added to the manifest
   and the corpus identities rebuilt.

Review read status: `complete`  
Review evidence status: `persisted`  
Candidate source-only admission status: `FAIL`

This decision does not authorize any PEPS/CAPEPS execution, Record-law claim,
state- or Record-faithfulness claim, truncation guarantee, efficiency or
scaling comparison, calibration claim, or production conclusion.

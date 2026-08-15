# Bravyi, Gosset, and Liu arXiv:2112.08499v2 — independent source-only review

Date: 2026-07-27

Reviewer role: fresh independent source-only admission reviewer

Decision: **FAIL — DO NOT ADMIT**

`read_status: complete`

`review_status: blocked_pending_source_note_and_audit_repairs`

This review is source-only. It does not modify the source note, its audit
packet, or `docs/papers/CURRENT_CORPUS.toml`.

## 1. Exact reviewed inputs

| input | exact SHA-256 |
|---|---|
| `docs/papers/2112.08499v2.pdf` | `4743d2f0ed7de44f0da83ca875fb69dd15378cecfb54ef368da93d81580c68c6` |
| `docs/papers/reading_notes/bravyi_gosset_liu_measurement_without_marginals_2112.08499v2_source_review.md` | `403bdbdb691b965e09263360fc436c66883eb3010a7aea6b0c11027cab38e8b0` |
| `docs/simulator_validation/BRAVYI_GOSSET_LIU_2112_08499V2_SOURCE_ONLY_AUDIT_2026-07-27.md` | `b909593a3c3f24d7ecefcfc5ea2f1c2aa572ee354517afcd007c1e3da0c38049` |

The PDF begins with `%PDF-1.5`, ends with a resolved `startxref` and
`%%EOF`, is unencrypted, and contains exactly 17 letter-size pages. The source
note's `source_sha256` and `audit_packet_sha256` match the reviewed PDF and
audit packet exactly.

The three inputs were unchanged when the review concluded. The note and audit
were already untracked worktree files; this review did not alter them.

## 2. Full-source traversal and visual verification

All 17 PDF pages were read in order. Every page was rendered at 150 dpi and
visually inspected; text extraction was used only for traversal and searching.

| PDF page | content checked | visual status |
|---:|---|---|
| 1 | source identity, abstract, Born sampling target, Eq. (1) | PASS |
| 2 | Algorithms 1--2, Eq. (2), exact prefix-distribution proof, call count, adaptive pointer | PASS |
| 3 | Table I, depth-cost heuristic, CoTenGra qualification, stabilizer rank, MBQC claim | PASS |
| 4 | Lemma 1 and Eq. (3), L1 definition, ground-state assumptions and Eqs. (4)--(6) | PASS |
| 5 | Metropolis--Hastings chain and Eqs. (7)--(14) | PASS |
| 6 | references and adaptive-circuit footnote 28 | PASS |
| 7 | robustness proof setup and Eqs. (15)--(17) | PASS |
| 8 | robustness induction and Eqs. (18)--(25), including the Eq. (22) anomaly | PASS |
| 9 | Eqs. (26)--(30), sum-over-Cliffords cost, numerical-method setup | PASS |
| 10 | Table II, rehearse methodology, all-zero-string assumption, Eq. (31), MBQC setup | PASS |
| 11 | Eq. (33), Algorithm 3, Problems 1--2, runtime statements | PASS |
| 12 | connectivity qualification, Theorems 1--2, hardness reduction start | PASS |
| 13 | crossing construction, Definition 1, Lemmas 2--3, Eqs. (37)--(43) | PASS |
| 14 | reduction identity and 2-factor gadget, Eqs. (44)--(51) | PASS |
| 15 | gadget figures and crossing-gadget Eqs. (52)--(55) | PASS |
| 16 | stoquastic sensitivity proof and magic-ratio definition/Lemma 4 | PASS |
| 17 | amplitude-ratio access and the final `s <= m` argument | PASS |

## 3. Admission checklist

| check | source result | note/audit treatment | status |
|---|---|---|---|
| Exact Born prefix invariant | Algorithm 2 defines `P_t`; induction gives `Q_t=P_t`, hence the final exact Born law. The local denominator is the `A`-marginal shared by `P_{t-1}` and `P_t`. | `bgl2112-prefix-invariant` and audit §§2--3 reproduce the invariant accurately. | **PASS** |
| Gate-local normalization and call count | Line 5 normalizes over at most `2^k` locally differing strings; it does not evaluate the growing Algorithm-1 marginal. At most `m 2^k` prefix probabilities are evaluated. | Accurately bounded in `bgl2112-call-count` and audit §3. | **PASS** |
| Adaptive measured-qubit constraint | Footnote 28 requires every subsequent gate to act trivially on a measured qubit; later gates may be classically controlled by earlier outcomes. | `bgl2112-adaptive-circuits` and audit §§3, 8 preserve the constraint and do not claim reset. | **PASS** |
| L1 versus total variation | Eq. (3) explicitly defines `||Q-P_m||_1` as a sum of absolute differences. Standard TV is one half of that quantity. Page 8 uses the phrase “total variation distance” while manipulating the L1 norm, but the displayed formulas retain the factor of two in Eq. (20). | `bgl2112-distance-convention` and audit §§4, 9 preserve the standard factor `1/2`. | **PASS WITH SOURCE-NOMENCLATURE CAUTION** |
| Robustness proof fidelity | The intended proof gives `||Q-P_m||_1 <= 16 sum_{t=1}^{m-1} epsilon_t`. | The bound and hypotheses are correct, but neither companion records the printed Eq. (22) defect described in §4 below. | **FAIL — BLOCKER B1** |
| CoTenGra estimates, not executed contractions | Pages 3 and 10 say CoTenGra optimized and estimated contraction costs; contractions were not performed. One optimizer run took about three days on 60 CPU cores. | Both companions correctly say estimates-not-executed. | **PASS** |
| CoTenGra workload qualification | Page 10 says the gate-by-gate rehearse calculation always assumes the sampled string is `0^n`; tables are optimizer FLOP estimates under the displayed slicing settings and random-circuit architecture. | The fixed-`0^n` rehearse assumption is absent from both companions, so their workload description is incomplete. | **FAIL — BLOCKER B2** |
| Surface-code scope | Eqs. (31)--(34) and Algorithm 3 concern MBQC with a planar-graph surface-code resource state, adaptive one-qubit basis choices, and amplitude/overlap evaluation. | Correctly identified as MBQC, not syndrome extraction or a QEC memory experiment. | **PASS** |
| Surface-code marginal hardness | Theorem 2 proves worst-case `#P`-hardness of unrestricted Problem 2 by reduction from exact perfect-matching counting. The obstruction is tied to an enforced adaptive order; regular non-adaptive measurement may be reordered when `G` is connected. | `bgl2112-marginal-hardness`, `bgl2112-order-qualification`, and audit §6 preserve both the theorem and qualification. | **PASS** |
| Conditional post-measurement state absence | The algorithm samples a classical output law and does not represent or certify outcome-conditioned quantum states. | Typed as source-local `bgl2112-gap-conditional-state`. | **PASS** |
| Reset/re-preparation absence | Footnote 28 leaves measured qubits untouched and defines no reset transaction. | Typed separately as `bgl2112-gap-reset`. | **PASS** |
| QEC raw history and Record absence | The source defines neither repeated syndrome rounds nor detector/observable Record folding. | Typed as source-local gaps and kept out of positive source claims. | **PASS, SUBJECT TO ATOMICITY REPAIR** |
| CAPEPS/full-PEPS absence | No CAPEPS representation, matched full-PEPS arm, channel/Record comparison, finite-bond certificate, conditional fidelity, or measured peak-memory benchmark appears. | These are correctly negative, source-local rows rather than positive paper facts. | **PASS, SUBJECT TO ATOMICITY REPAIR** |
| Fact atomicity | The source contains independently locatable results that should remain separate evidence records. | Several note records bundle distinct claims or gaps; details are in §5. | **FAIL — BLOCKER B3** |
| Locator fidelity | Positive claims resolve to the cited algorithms, equations, tables, theorem, or supplemental section. Gap locators are bounded to the relevant construction or full-source scope. | No positive claim was found with a false page, equation, algorithm, table, or theorem locator. | **PASS** |
| Relation integrity | All eight relations point to existing `paper_fact` IDs; predicates are defensible and every `object_label` occurs in its fact claim. No relation points to a project-only gap. | Relation endpoints and labels are source concepts. | **PASS** |
| Source/project separation | Positive source facts remain source statements. Project application and kill conditions are in audit §10. Project-specific missing targets appear as typed `literature_gap` records. | Separation is materially correct; the extra reset/channel sentence inside the adaptive `paper_fact` must be moved or removed as part of atomicity repair. | **PASS WITH REQUIRED REPAIR** |
| Artifact-verifying preflight | PDF and audit hashes match the note. Repository audit excludes this note only at the first admission gate because `admission_status` is still `draft_pending_review`. | Safe pre-admission state; it is not in `CURRENT_CORPUS.toml`. | **PASS** |
| Printed anomalies | One load-bearing equation typo and several editorial typos are visible. | None is disclosed in the note or audit. | **FAIL — BLOCKER B1 for Eq. (22); editorial items non-blocking** |

## 4. Printed anomalies

### 4.1 Load-bearing anomaly

Supplemental PDF page 8, Eq. (22), first norm:

```text
||P_t-R_t||_1 <= 4 || U_t|psi_t> -
                       U_t|phi_{t-1}>/||phi_{t-1}|| ||
```

Immediately above, the paper states
`|psi_t> = U_t|psi_{t-1}>`. The following equality in Eq. (22) also replaces
the first term by `|psi_t>`. Therefore the first displayed term must be
`U_t|psi_{t-1}>` (or directly `|psi_t>`), not `U_t|psi_t>`.

This is a repairable printed typo: with the intended term, unitarity plus
Eqs. (16) and (20) yields the stated `8 epsilon_{t-1}` bound and the induction
continues. It does not by itself contradict Lemma 1. It is nevertheless
load-bearing and must be recorded explicitly before the proof is admitted as
source-faithful evidence.

### 4.2 Non-blocking editorial anomalies

- PDF page 9 prints “`Q_moutput`” without a space.
- PDF page 13 prints “vice verse” for “vice versa.”
- PDF page 14 prints “updaing” for “updating.”
- PDF page 15 prints “undefined for for odd-weight strings.”

These do not alter any reviewed scientific claim. The page-8 use of “total
variation distance” beside an L1 contraction is a terminology caution, not an
algebraic failure; Eqs. (3) and (20) make the paper's displayed norm explicit.

## 5. Fact-atomicity failures

The note's H2 shape and first four fields are syntactically regular, but strict
semantic atomicity fails in at least these records:

1. `bgl2112-special-gates` combines the CNOT deterministic update/call-count
   specialization with the separate diagonal-gate skip rule.
2. `bgl2112-surface-resource` combines the definition of the uniform cycle
   state with a separate `O(n)` direct-measurement sampling result.
3. `bgl2112-magic-ratio` combines Lemma 4's local amplitude-ratio property
   with the later, separately proved sensitivity bound `s <= m`.
4. `bgl2112-gap-qec-record` combines repeated syndrome rounds, raw history,
   prefix branch masses, detector/observable folds, and decoder records.
5. `bgl2112-gap-record-metrics` combines conditional fidelity, Record TV, raw
   history equality, and reset correctness.
6. The prose after `bgl2112-adaptive-circuits` adds a reset/channel absence to
   a positive `paper_fact`, duplicating separately typed gap records.

Each independently checkable claim or assigned absence needs its own Fact ID,
claim, and exact locator. Assumption sets that function as one theorem
hypothesis set, such as `bgl2112-ground-state-conditions`, are not rejected
merely for listing all jointly required assumptions.

## 6. Required repairs and blockers

Admission is blocked until all three items are repaired and independently
rechecked:

- **B1 — printed-proof anomaly:** disclose Supplemental p.8 Eq. (22)'s
  `U_t|psi_t>` typo, state the intended term, and distinguish “repairable
  printed anomaly” from a source-proved corrected equation.
- **B2 — numerical-method qualification:** add the p.10 fixed-`0^n` rehearse
  assumption to the CoTenGra fact and audit reconstruction while retaining
  estimates-not-executed language.
- **B3 — semantic atomicity:** split the records listed in §5 and remove the
  duplicated gap prose from the adaptive positive fact.

Any repair to the audit changes its SHA-256, so the note's
`audit_packet_sha256` must be recomputed. Any repair to the note changes its
own SHA-256. Admission metadata and the corpus manifest must remain untouched
until a fresh post-repair artifact-verifying review passes.

## 7. Final verdict

The central scientific reconstruction is mostly accurate:

- exact prefix probabilities imply `Q_t=P_t` and the exact final Born law;
- adaptivity is allowed only while measured qubits remain untouched;
- Eq. (3) is an L1 bound, with standard TV equal to half;
- the CoTenGra tables are optimizer estimates, not executed contractions;
- the surface-code result is MBQC resource-state sampling, not QEC syndrome
  extraction; and
- conditional state, reset, QEC Record, CAPEPS, and matched full-PEPS claims
  are absent from this source.

The omitted load-bearing Eq. (22) anomaly, omitted fixed-`0^n` numerical
qualification, and non-atomic evidence records prevent source-only admission.

**Overall: FAIL. Blockers: B1, B2, B3. Do not add this note to
`docs/papers/CURRENT_CORPUS.toml`.**

# Independent cross-review — Transformer-QEC, arXiv:2311.16082v1

## Decision

**REVISE -- locator-only.** The audit's scientific reconstruction and all requested evidence
boundaries pass independent full-text review. Target-distance models receive ten epochs of labelled
target-data fine-tuning and are not frozen transfers; the artifact reports numerical results at four
distances rather than the six claimed in the abstract and introduction; Table 1 contains an explicit
distance-7, `p=0.05` MWPM counterexample; Figure 8 prints both `0.038` and `0.0038`; and the source
reports neither evaluation-population size nor uncertainty. The evaluated phenomenological noise
model has no temporal-memory law.

The fixed PDF, audit binding, source-note schema and all six relations pass. Three source-note
`PDF page` fields nevertheless fail the exact-locator gate. `wang-selection-scope` uses page 1 even
though its simulated fine-tuning evaluation clause is established in Secs. 4.1--4.2 on page 5.
`wang-transfer-protocol` and `wang-gap-frozen-transfer` use page 4 even though the load-bearing ten
epochs and learning rate `5e-4` are printed only in Sec. 4.1 on page 5. Their textual `Source
locator` fields name the correct later sections, so no scientific wording change is required; the
primary PDF page anchors should be corrected or the cross-page claims split.

No audit, source-note or manifest file was modified in this cross-review.

## Fixed-object verification

- The official record is arXiv:2311.16082v1, *Transformer-QEC: Quantum Error Correction Code
  Decoding with Transferable Transformers*, by Hanrui Wang and seven coauthors, submitted
  27 November 2023. The official comments list acceptance to the ICCAD 2023 FAST ML for Science
  Workshop and the submission history contains only v1.
- A fresh temporary retrieval from `https://arxiv.org/pdf/2311.16082v1` is byte-identical to the
  fixed local artifact: PDF 1.5, seven pages, 2,276,718 bytes, SHA-256
  `cc4a5fce3676648a1cfd8cc378ac4bf0a8b994294cef02acff18422696f30aa1`.
- Independent reading covered all seven pages, Figs. 1--8, Tables 1--3, the full methodology and
  evaluation, and references. Every rendered page was inspected. Table 1, Figs. 7--8 and
  Tables 2--3 were checked visually rather than inferred from extracted text.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/WANG_TRANSFORMER_QEC_2311_16082_AUDIT_2026-08-05.md`,
  SHA-256 `81e30793d9aba3a8dd5c96cc8d7299d9f15fbe47a49da84903b2f6cf720ede4b`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/wang_transformer_qec_2311.16082v1_source_review.md`,
  SHA-256 `11947682c6e9fc1d8ed4d571309c7fa8375a55848a7bcd94e0ef1fa34048cf44`.
- The note's declared source and audit hashes match the reviewed files. Artifact-verifying
  `parse_note` succeeds with 26 evidence records (20 `paper_fact`, six `literature_gap`) and six
  relations. The full draft-directory corpus audit validates the note with 20 paper facts.
- The note is absent from `docs/papers/CURRENT_CORPUS.toml`. No admission action was taken.

## Independent scientific reconstruction

### Generator and QEC-facing representation

The evaluated task is simulated repeated rotated-surface-code memory. For distance `D`, the
benchmark uses `D` syndrome-extraction rounds plus a final data measurement. The phenomenological
model assigns the same scalar `p` to syndrome-measurement flips and data-qubit depolarising errors,
with X, Y and Z equiprobable, and Stim supplies the circuit simulation. Ten scalar values of `p`
are declared. The paper gives no persistent physical or latent carrier, transition law,
history-conditioned probability, drift process or mixed mechanism. Multiple rounds in the input
therefore do not by themselves make this a temporal-memory-law study.

The neural representation is a six-channel `(D+1)`-scale spatiotemporal grid containing X- and
Z-check locations, two syndrome channels, and initial/final temporal-boundary flags. After learned
embedding and three-dimensional sinusoidal positional encoding, tokens pass through a Transformer
encoder. Data-qubit positional queries feed a Transformer decoder that predicts local physical
errors, while a pooled head predicts global parity. A confidence threshold above 0.95 selects local
positive predictions.

The reported logical result is a hybrid computation. Predicted local errors clear part of the
syndrome; residual syndrome is decoded with a global decoder implemented as MWPM, and its parity is
XORed with the Transformer's parity. Transformer-QEC is therefore not a stand-alone neural decoder
comparison against an otherwise external MWPM arm.

### What the source calls transfer

The source distance-5 model is trained from scratch for 100 epochs on one million samples generated
at `p=0.01`. At each other reported distance, the distance-5 checkpoint is used only as an
initialisation. Positional encoding is adjusted and the model is trained for ten epochs on the new
distance's labelled dataset at learning rate `5e-4`. This is within-family target-distance
fine-tuning. It is neither frozen inference nor zero-shot transfer.

The comparison also does not isolate the value of pretrained initialisation. The MLP has a different
architecture and is separately trained for 100 epochs, with training `p=0.01` at distances 3 and 5
but `p=0.025` at distances 7 and 9. No target-distance Transformer trained from scratch under an
accuracy- and compute-matched protocol is printed. The abstract's greater-than-tenfold cost language
is supported only by the disclosed 100-versus-10 epoch counts; wall time, GPU-hours, energy,
convergence and inference latency are absent.

## Requested boundary checks

| requested issue | independent finding | disposition |
|---|---|---|
| Frozen transfer | Every target-distance model is fine-tuned for ten epochs on target-distance data after positional-encoding adjustment. | **missing; fine-tuning is not frozen transfer** |
| Demonstrated distance reach | The abstract and Introduction name `{3,5,7,9,11,13}`. Sec. 4.1, Table 1 and Fig. 8 contain results only for `{3,5,7,9}`. | **four demonstrated distances, not six** |
| Blanket superiority | At distance 7 and `p=0.05`, Table 1 gives Transformer-QEC `0.20590` and lower MWPM `0.20178`. | **printed counterexample; “all benchmarks” is false** |
| Threshold | Figure 8 and its caption say about `0.038`; adjacent prose says `0.0038`. The plotted crossing is visually near `0.038`. | **unresolved factor-of-ten source inconsistency** |
| Population/uncertainty | Training data total one million for the source recipe, but evaluation-set size, splits, seeds, record reuse, paired outcomes, intervals and uncertainty estimator are absent. | **population-level/statistical closure missing** |
| Wrong-memory robustness | The ten settings are scalar values of `p` inside one memoryless phenomenological family. No history law or continuing carrier is varied. | **R1 missing; not a memory-law evaluation** |
| Temporal-history benefit | The Transformer consumes ordered multiround data, but there is no otherwise-matched history/window/temporal-attention ablation. | **memory-specific decoder benefit missing** |
| Deployment cost | Only epoch counts and one A6000 training-device name are reported. | **measured training and inference cost missing** |

All of these dispositions agree with the audit and draft note.

## Exact numerical and reporting checks

- Table 1 reports four distances and only `p=0.05` and `p=0.01` in the table. The method declares
  ten scalar rates; Table 2 and Figure 8 expose additional points, but no distance-11 or distance-13
  result occurs anywhere in the seven-page artifact.
- The seven non-counterexample Transformer-QEC/MWPM pairs are transcribed correctly in the audit.
  Several differences are extremely small, including `0.17232` versus `0.17279` and `0.23144`
  versus `0.23161`. Without sample totals or uncertainty, the decimal precision does not establish
  statistical separation.
- Table 2 correctly supports “better or equal in nine of ten” for the mixed-loss point estimates.
  At `p=0.0075`, local-plus-global loss is worse: `0.00103` versus `0.00097`.
- Figure 7 repeats `D5 p0.02` for two bar groups, so one condition is not uniquely labelled. Its
  rounded class-1 averages are about 0.93 and 0.50; “43% higher” is a 43-percentage-point difference,
  not an unambiguously defined relative gain.
- The model-size paragraph's statement that the larger model “performs poorly on testing” conflicts
  with the immediately preceding statement and Table 3. The audit correctly excludes it from a
  generalisation claim.

## Operation-replay check

| input | transformation | source-critical assumption | output | status |
|---|---|---|---|---|
| Distance-`D` repeated surface-code task | Simulate `D` rounds plus final measurement under equal scalar measurement/data error rate `p` | The printed phenomenological model represents the evaluation task | Synthetic syndrome and labels | **complete for declared model; no memory carrier** |
| Six-channel cubic grid | Embed, add 3-D positional encoding and flatten | Variable token length permits the architecture to accept multiple distances | Encoder tokens | **complete** |
| Encoder tokens and data-position queries | Transformer self-/cross-attention plus local/global training heads | Simulated labels train useful local errors and parity | Local errors and Transformer parity | **complete as architecture** |
| Predicted errors and residual syndrome | Clear predicted contribution, apply residual MWPM and XOR parities | Matching supplies syndrome-consistent global completion | Logical decision | **complete; hybrid pipeline** |
| Distance-5 checkpoint and target-distance data | Adjust positional encoding and update parameters for ten epochs at `5e-4` | Labelled target data are allowed | Distance-specific model | **complete as fine-tuning; no frozen branch** |
| Four decoder packages on declared tasks | Report marginal logical-error estimates | Evaluation population and uncertainty are unstated | Table 1 | **printed values fixed; statistical replay incomplete** |
| Four distance curves | Identify crossing | No finite-size or uncertainty procedure supplied | Threshold | **internally inconsistent: `0.038`/`0.0038`** |

## Source-note locator and relation audit

| record | semantic result | locator result | disposition |
|---|---|---|---|
| `wang-source-identity` | Correct; official record confirms comments and v1-only history. | Title page plus official record resolve. | **pass** |
| `wang-selection-scope` | Correct. | Page 1 contains the broad abstract claim, but not the simulated target-distance fine-tuning protocol used in the Claim; Secs. 4.1--4.2 on p. 5 do. | **revise primary PDF page or split claim** |
| `wang-phenomenological-model` | Correct and properly excludes a temporal carrier. | Sec. 4.1, p. 5 is exact. | **pass** |
| `wang-repeated-record` and `wang-record-representation` | Correct. | Sec. 3 on p. 4 establishes the representation; Sec. 4.1 on p. 5 fixes rounds equal to distance. | **pass; locator text is adequate** |
| `wang-transformer-computation`, `wang-mixed-loss`, `wang-hybrid-interface` | Correct. | Sec. 3 and Fig. 6 locate the architecture; Sec. 4.2 locates the reported ablation/hybrid interpretation. | **pass** |
| `wang-source-training` | Correct. | Training settings on p. 5 are exact. | **pass** |
| `wang-transfer-protocol` | Correct and load-bearing. | The p. 4 method states fine-tuning and positional adjustment, but ten epochs and `5e-4` in the Claim occur only on p. 5. | **revise `PDF page` from 4 to 5, or split** |
| `wang-baselines`, `wang-error-grid` | Correct. | Sec. 4.1, p. 5 is exact. | **pass** |
| `wang-reported-distances` | Correctly preserves the six-versus-four conflict. | Abstract/Introduction plus Sec. 4.1, Table 1 and Fig. 8 resolve. | **pass** |
| `wang-table-one-results`, `wang-mwpm-counterexample` | Exact values and qualifications are correct. | Table 1 on p. 5 is exact. | **pass** |
| `wang-threshold-inconsistency`, `wang-figure-seven-label` | Correct. | Figs. 7--8 and prose on p. 6 are exact. | **pass** |
| `wang-training-cost`, `wang-statistical-boundary`, `wang-artifact-boundary` | Correct. | Their page/record spans are adequate. | **pass** |
| `wang-gap-frozen-transfer` | Correct. | The exact ten-epoch condition is on p. 5, not the present page-4 anchor. | **revise `PDF page` to 5** |
| remaining five `wang-gap-*` records | Correctly limit independent transfer, wrong-model robustness, temporal generator/access and deployment cost. | The source-wide page/section anchors are adequate. | **pass** |

All six relations use allowed predicates/types, resolve to existing `paper_fact` records, and use an
object label that occurs in the referenced Claim and names the intended source concept. Relation
semantics therefore pass; no relation edit is required.

## Required revisions before pass

1. Anchor `wang-selection-scope` on the evaluation page that establishes simulation and
   target-distance fine-tuning, or split the abstract scope from the evaluated protocol.
2. Change the primary `PDF page` for `wang-transfer-protocol` and `wang-gap-frozen-transfer` from 4
   to 5, where ten epochs and learning rate `5e-4` are printed. Retain p. 4 in the textual locator for
   the architectural rationale and positional-encoding adjustment.
3. Rerun artifact-verifying `parse_note`, the draft-directory audit, SHA-256 recording and
   whitespace checks. No audit scientific revision is required.

## Disposition

- `read_status`: complete
- official/local fixed-object identity: pass
- audit scientific fidelity: pass
- fine-tuning versus frozen transfer: pass
- four-versus-six distance boundary: pass
- MWPM counterexample and threshold conflict: pass
- population/uncertainty and non-memory-law boundaries: pass
- source-note semantic claims: pass
- source-note exact locator gate: revise three primary page anchors
- relations: pass
- artifact/hash integrity: pass
- current machine schema: pass, but it does not test semantic page sufficiency
- manifest action: none

After the locator correction, this source can support only a bounded within-code-family
pretrained-initialisation-plus-fine-tuning example on synthetic memoryless records. It cannot support
frozen cross-distance transfer, cross-device or cross-code transfer, wrong-memory-model robustness,
memory-specific decoder benefit, statistically resolved superiority, or measured deployment cost.

## Final locator verification

**PASS.** The three locator-only blockers are closed without changing the scientific claims, audit
or fixed source. No audit, source-note or manifest file was modified during this verification.

- `wang-selection-scope` now gives the full explicit span `Abstract, p. 1; Sec. 1 contribution list,
  p. 2; Secs. 3--4, pp. 4--5` and uses p. 5 as its primary PDF anchor.
- `wang-transfer-protocol` retains the p. 4 method section in its textual locator and now uses p. 5,
  where ten target-data epochs and learning rate `5e-4` are printed, as its primary anchor.
- `wang-gap-frozen-transfer` likewise uses p. 5 as the primary anchor for the explicit ten-epoch
  condition.

Final artifact bindings:

- fixed official PDF:
  `cc4a5fce3676648a1cfd8cc378ac4bf0a8b994294cef02acff18422696f30aa1`;
- unchanged audit:
  `81e30793d9aba3a8dd5c96cc8d7299d9f15fbe47a49da84903b2f6cf720ede4b`;
- locator-corrected source note:
  `b4adca858e9c4a0d892f820ee404add0edc7e785784cc684ba23967eb3b88ee5`.

Artifact-verifying `parse_note` succeeds with 26 evidence records (20 `paper_fact`, six
`literature_gap`) and six relations. The note declares the actual PDF and audit hashes, the full
draft-directory audit lists it as validated, and the whitespace check is clean.

Final disposition:

- scientific fidelity: **pass**;
- fine-tuning/frozen-transfer and non-memory-law boundaries: **pass**;
- four-versus-six, MWPM-counterexample and threshold-conflict preservation: **pass**;
- population/uncertainty qualifications: **pass**;
- locators and relations: **pass**;
- artifact/schema/hash integrity: **pass**;
- manifest action: none.

## Final locator-revision verification

### Final decision

**PASS for pre-admission review.** This decision supersedes the initial locator-only `REVISE`
decision. All three requested page-anchor repairs are present, artifact and audit bindings pass, and
the source note passes both direct artifact-verifying parsing and the draft-directory audits. No
scientific Claim, relation meaning or evidence boundary changed with the locator repair.

### Artifact and hash verification

- The fixed local PDF remains byte-identical to a fresh stream from the official arXiv v1 endpoint:
  seven pages, 2,276,718 bytes, PDF 1.5, SHA-256
  `cc4a5fce3676648a1cfd8cc378ac4bf0a8b994294cef02acff18422696f30aa1`.
- The audit is unchanged at SHA-256
  `81e30793d9aba3a8dd5c96cc8d7299d9f15fbe47a49da84903b2f6cf720ede4b`.
- The locator-revised note has SHA-256
  `b4adca858e9c4a0d892f820ee404add0edc7e785784cc684ba23967eb3b88ee5`,
  replacing the initially reviewed note hash
  `11947682c6e9fc1d8ed4d571309c7fa8375a55848a7bcd94e0ef1fa34048cf44`.
- The revised note declares the exact current PDF and audit hashes. Its admission metadata,
  seven-page visual record and six relations remain internally consistent.

### Three-locator closure

| prior blocker | revised record | independent verification | result |
|---|---|---|---|
| Selection scope used p. 1 as the primary page although its simulated fine-tuning evaluation clause is established later | `Source locator: Abstract, p. 1; Sec. 1 contribution list, p. 2; Secs. 3--4, pp. 4--5`; `PDF page: 5` | Page 5 fixes the simulated rotated-surface-code benchmark and target-distance training protocol; pp. 1--2 provide the broad scope and p. 4 supplies the architecture/fine-tuning rationale. | **closed** |
| Transfer protocol used p. 4 although the exact epoch count and learning rate occur on p. 5 | `Sec. 3, “Transfer learning”; Sec. 4.1, “Transfer learning settings”`; `PDF page: 5` | Page 4 states new-distance fine-tuning and positional-encoding adjustment. Page 5 explicitly prints ten epochs and learning rate `0.0005`. | **closed** |
| Frozen-transfer gap used p. 4 although its decisive ten-epoch countercondition occurs on p. 5 | Same cross-section locator; `PDF page: 5` | Page 5 directly supports that every reported target-distance branch updates parameters for ten epochs. | **closed** |

### Schema and corpus diagnostics

Artifact-verifying `parse_note` succeeds and resolves:

- 26 evidence records: 20 `paper_fact` and six `literature_gap` records;
- six relations, all tied to valid `paper_fact` records with allowed predicates/types and exact
  Claim labels;
- the fixed source and audit artifacts at their declared hashes.

Both draft-directory commands validate the Transformer-QEC note with 20 paper facts:

- `literature_rag.py audit --schema-only`;
- `literature_rag.py audit` with artifact verification.

The note remains absent from `docs/papers/CURRENT_CORPUS.toml`; no admission or manifest mutation
was performed in this verification. Whitespace checks are clean.

### Scientific-boundary non-regression

The locator changes do not alter the approved scientific reconstruction:

- target distances receive labelled-data fine-tuning for ten epochs; this is not frozen or zero-shot
  cross-distance transfer;
- numerical demonstrations stop at distances 3, 5, 7 and 9 despite the six-distance abstract claim;
- Table 1 retains the distance-7, `p=0.05` MWPM counterexample;
- the `0.038` versus `0.0038` threshold conflict remains unresolved;
- evaluation population size, uncertainty, paired outcomes and measured deployment cost remain
  absent;
- the phenomenological generator remains memoryless, with no wrong temporal-memory law or
  otherwise-matched history-access ablation.

Final disposition: **PASS; locator repair complete and ready for the parent-controlled admission
step.** No audit, note or manifest file was changed by this verification.

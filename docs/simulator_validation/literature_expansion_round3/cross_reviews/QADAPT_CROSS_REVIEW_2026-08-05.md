# Independent cross-review — QAdapt, arXiv:2607.28422v1

## Decision

**REVISE.** The audit and draft note are substantially faithful on the method, numerical values,
latency boundary and the absence of a temporal-memory generator. They should not yet pass as the
coverage record for transfer or population-level evidence, because three phrases promote
source-reported point estimates beyond what the full protocol establishes:

1. the paper establishes **no target-domain fine-tuning, parameter update or target-domain
   calibration during the reported Willow evaluation**, but it does not establish a target-unseen
   model-selection protocol, identify the source hardware for T0, or bind an exact checkpoint to
   either Willow distance;
2. the 110 configurations are the complete cells of the authors' constructed static-Pauli design
   grid, not a sampled population, and the paper does not state that the 400,000/100,000 Willow
   cohorts are the complete public release or document exclusions and paired record reuse;
3. Ising-fast and QAdapt share the input representation and PyMatching backend, but they are not a
   matched decoder treatment: architecture, parameter count, task exposure and apparently training
   budget differ, while the evaluation checkpoint and baseline epoch/data budget are not printed.

The audit's conclusions that D1, D2 and wrong-memory R1 remain missing are correct. The revision is
needed to narrow the adjacent T1 claim and replace “population-wide”/“complete Willow shot sets”
with source-supported language.

## Fixed-object verification

- Independently streamed official source: `https://arxiv.org/pdf/2607.28422v1`.
- Official record: arXiv:2607.28422v1, *QAdapt: A Noise-Adaptive Neural Pre-Decoding Framework for
  Quantum Error Correction*, Ran Miao, Rui Luo, Xiaohan Shan and Xiaoming Sun, submitted 30 July
  2026. Only v1 was listed at review time.
- Official and local PDF match exactly: PDF 1.7, 11 pages, 1,019,924 bytes, SHA-256
  `2c8f6fec9a1dd0a76f041d76cdd4b76be74ee466a7cbb9719f15637f13144c7c`.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/QADAPT_2607_28422_AUDIT_2026-08-05.md`,
  SHA-256 `10ee1874bef7badea3368bfb921284a37cd895ab99e7f3ac2b9d8e3530207742`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/qadapt_2607.28422v1_source_review.md`,
  SHA-256 `4cacf877abecb4bbb01b5a138d055d30e3021b0f7715363a7a230ba1cb386557`.
- The audit hash printed in the draft metadata matches the reviewed audit.
- The draft is intentionally excluded by the current corpus audit because it declares
  `evidence_status = "unpersisted"` and `admission_status = "draft_not_admitted"`. No manifest
  admission should occur before the semantic revisions below.
- Independent full-text reading and visual inspection covered all 11 pages, including Eqs. (1)–(10),
  Figs. 1–6, Tables 1–6, Secs. 5.2–5.5 and 6.2–6.4, Sec. 7.4, Data Availability and Appendices A–D.

## Independent scientific reconstruction

### Generator and adaptation protocol

T0 is a 25-parameter circuit-level Pauli generator. The printed preparation, measurement, idle and
nonidentity CNOT-channel probabilities are fixed and applied per circuit occurrence. T1–T4 are
predefined offline tasks obtained by multiplying selected measurement, CNOT, idle or Z-bias
parameters by 1.5. HTNet is trained sequentially for 20 epochs per stage, with diagonal Fisher states
from 65,536 samples and an EWC penalty of 100.

Nothing in this chain is an online observation of hardware drift or a continuing physical/latent
memory state. At deployment, the model is fixed. Online Fisher updates and drift detection are
future work. The OOD grid likewise changes static probabilities inside the same Pauli
parameterization; it does not introduce a wrong temporal kernel, lifetime or carrier law.

### Decoder interface and comparator

HTNet consumes a four-channel multiround detector tensor, predicts local corrections, maps them
through the detector–correction incidence relation, and passes the residual syndrome to PyMatching.
Ising-fast uses the same detector representation and PyMatching backend. Those are useful controlled
dimensions.

The comparison nevertheless changes the learned front end and training exposure. QAdapt/HTNet has
650,374 parameters and the printed T0–T4 continual schedule; Ising-fast has 912,772 parameters and is
described only as trained under T0. The source does not print the baseline epoch count, sample count,
or an equal-compute protocol. It also does not compare Q-EWC with unregularized sequential training,
replay or joint mixed-noise training. The results therefore belong to two complete packages, not to
an isolated adaptation, temporal-branch or memory-access treatment.

### Synthetic grid

The authors construct 11 simultaneous-axis combinations, apply five fixed multipliers and evaluate
two distances: `11 × 5 × 2 = 110` design cells. They report that the QAdapt point estimate is lower in
all 110 cells and give averages across the 55 cells at each distance. This is complete coverage of the
declared **design grid**. It is not a random sample from a defined population of devices, temporal
regimes or noise models, and the 110 cells are not interchangeable independent population units.
Per-cell shot counts, synthetic train/validation/test splits, evaluation round count, random seeds and
uncertainty are absent.

### Willow protocol

Section 5.4 explicitly states that the ten-round Willow evaluation uses 400,000 distance-5 and
100,000 distance-7 shots without fine-tuning, parameter updates or target-domain calibration. That
supports a narrow, source-reported **no-target-update evaluation** on external hardware records.

It does not establish strict target blindness before evaluation:

- Willow densities are inspected and used as an external workload reference in Sec. 3.2 and Fig. 1;
- the source hardware from which the “device-mapped” T0 parameters were derived is not identified;
- the paper does not state that Willow records were excluded from architecture, hyperparameter,
  threshold or checkpoint selection;
- neither the exact checkpoint nor the mapping of checkpoints to d=5 and d=7 is supplied;
- the paper does not state that the reported cohorts exhaust the public release or describe any
  filtering, exclusions or record-level pairing.

These absences do not contradict the authors' “without target-domain fine-tuning” statement. They do
prevent the audit from upgrading it to an independently auditable target-unseen frozen-transfer
protocol.

## Point-by-point cross-check

| issue | independent source finding | audit/note treatment | result |
|---|---|---|---|
| Official artifact | The official v1 PDF is 11 pages and byte-identical to the fixed local artifact. | Identity, page count and PDF hash are correct. | **pass** |
| T0 generator | Appendix A defines 25 fixed per-occurrence circuit-level Pauli probabilities. No within-run carrier state, lifetime or transition law appears. | Both documents classify T0 as a static Pauli environment rather than temporal memory. | **pass** |
| Offline/online boundary | T0–T4 training and Q-EWC are offline; inference applies a fixed HTNet and PyMatching. Online Fisher updates/drift detection are prospective. | Reconstructed correctly. | **pass** |
| HTNet operation | Separate spatial, temporal and joint branches, adaptive fusion, axis–channel gating and raw-evidence skip lead to four local-correction channels. | Equations, architecture and nine-round receptive field are reported correctly. | **pass** |
| Q-EWC schedule | The text says 20 epochs per task, 100 cumulative epochs, lambda 100 and Fisher estimates from 65,536 samples after T0–T3. | Values are correct. The audit should not call the resulting evaluation checkpoint fixed/identified, because result-to-checkpoint mapping is not printed. | **revise wording** |
| Ising-fast comparator | Same T0 environment, detector representation and PyMatching backend; different network and parameter count. Only QAdapt receives the printed T0–T4 schedule. Baseline epochs/data budget are unstated. | Main confounding is recognized, but the missing baseline training budget and result-checkpoint mapping should be added. | **revise** |
| 110-point grid construction | Six two-axis, four three-axis and one four-axis combination, five multipliers and two distances yield exactly 110 cells. | Counts and values are correct. | **pass** |
| Meaning of 110/110 | The point estimate favors QAdapt in every constructed cell; no per-cell shot counts, intervals, seeds or paired records are supplied. | The note correctly says point estimates, but the audit's “population-wide coverage” promotes a fixed design grid to a population claim. | **revise** |
| “Retained” multipliers | The PDF repeatedly calls the five multipliers retained but does not define a larger candidate set or retention rule. | The audit flags this anomaly correctly. | **pass** |
| Synthetic round count | The OOD performance protocol does not print the number of QEC rounds. The nine-round value is an HTNet receptive field, not necessarily the evaluated circuit length. | The audit/gap record correctly marks evaluation round count absent. | **pass** |
| High-load subset | Seventy-four grid cells satisfy a threshold imported from a distinct d=3, Z-basis, nine-round anonymized hardware density measurement. The authors explicitly deny distributional equivalence/end-to-end hardware decoding. | Correctly bounded. | **pass** |
| Willow no-update statement | Sec. 5.4 explicitly says no fine-tuning, parameter updates or target-domain calibration for the reported ten-round evaluation. | Correct as a source statement. | **pass** |
| Willow target exposure | T0 provenance, target-data exclusion from model selection, exact checkpoints and checkpoint-to-distance mapping are absent. Willow summary statistics are inspected in the paper. | Checkpoint-to-distance is flagged, but “zero-shot target-domain transfer” remains too strong without a target-exposure boundary. | **revise** |
| Willow shot cohorts | The source states 400,000 d=5 and 100,000 d=7 shots. It does not say “all available shots,” specify exclusions, or print shot-paired decoder outcomes. | Numeric counts are correct; “complete Willow shot sets” is unsupported. | **revise** |
| Willow LER values | Table 4 prints 0.09963 versus 0.09386 at d=5 and 0.08412 versus 0.08201 at d=7. | Values and relative reductions are transcribed correctly. | **pass** |
| LER uncertainty | Sec. 7.4 says LER confidence intervals are absent and requests binomial intervals, seed variation and paired-shot analysis. Marginal rates alone do not determine paired-decoder uncertainty. | The absence is recognized and must remain load-bearing, especially for the small d=7 gap. | **pass, strengthen consequence** |
| Latency | Only residual-syndrome PyMatching time is measured; inference, transfer and residual construction are excluded, and platform/repetition details are absent. | Correctly limited to backend workload. | **pass** |
| EWC attribution | No unregularized continual, replay or joint mixed-noise comparator is provided. | Correctly rejected as a causal EWC result. | **pass** |
| Wrong-memory robustness | All training and OOD environments use static per-occurrence Pauli probabilities. No carrier lifetime, hidden transition or temporal-model misspecification is varied. | Correctly classifies R1 as missing for wrong-memory law and adjacent only for static-parameter OOD. | **pass** |
| Memory-conditioned decoder benefit | Multiround input and temporal convolutions are present, but there is no otherwise-identical history/temporal-branch/memory-state ablation. | D1/M1 boundaries are correct. | **pass** |
| Framework fit | Generator, detector-record interface, offline adaptation, learned pre-decoder, residual interface, PyMatching backend and demonstrated reach can be separated without adding a category. | F1 conclusion is correct if training/adaptation remains explicit. | **pass** |

## Uncertainty diagnostic

This calculation is a cross-review diagnostic, not a result reported by the paper. Treating the two
marginal LERs as if they were independent binomial proportions gives:

| Willow setting | absolute LER difference | approximate independent-binomial z | interpretation |
|---|---:|---:|---|
| d=5, 400,000 shots | 0.00577 | 8.73 | large relative to independent marginal sampling error, but still lacks the actual paired discordance table |
| d=7, 100,000 shots | 0.00211 | 1.71 | not clearly separated under this crude approximation; paired outcomes are necessary for a defensible comparison |

The actual models were presumably evaluated on a common cohort, so their errors are correlated and
the independent-binomial calculation is not the correct test. Depending on the number and direction
of discordant shots, paired uncertainty could be smaller or larger. The key audit conclusion is that
Table 4's marginal rates cannot recover that information. The missing paired analysis is therefore a
substantive evidence boundary, not merely a reporting preference.

## Operation-replay check

| input | transformation | source-critical assumption | output | status |
|---|---|---|---|---|
| Repeated surface-code circuit plus T0 probabilities | Stim samples fixed per-occurrence Pauli faults and constructs detector tensors | Static circuit-level Pauli model is an adequate generator for training | Synthetic multiround detector records | complete; no temporal carrier |
| T0–T4 predefined tasks | Sequential HTNet training with Fisher-diagonal EWC | Preserving Fisher-important weights improves multi-task behavior | A trained QAdapt model after the described schedule | method complete; exact evaluated checkpoint and selection rule missing |
| Detector tensor | HTNet spatial/temporal/joint feature extraction and local-correction head | Local receptive field can remove useful structures without harmful overcorrection | Local correction logits | complete as architecture |
| Local corrections | Apply incidence map and XOR with detector record | The correction/interface map matches the backend graph | Residual syndrome | complete |
| Residual syndrome | PyMatching global decode | Same backend can compare package outputs | Logical decision | complete; learned front ends remain unmatched |
| 11 axis combinations × five multipliers × two distances | Evaluate QAdapt and Ising-fast | The constructed grid is representative of desired static-parameter shifts | 110 point-estimate comparisons | complete for design cells; not a population or uncertainty result |
| Willow cohort | Apply reported models without target-domain update/calibration | The evaluated checkpoint was fixed and selected independently enough for the desired transfer claim | Two marginal LERs and backend timing values per distance | numerical result printed; target-exposure, checkpoint, cohort-selection and pairing provenance missing |

## Required revisions before pass

### Audit packet

1. In D2 and the source-local verdict, replace “population-wide coverage is present” with
   “complete coverage of the authors' fixed 110-cell design grid is present; population sampling,
   per-cell shot counts and uncertainty are absent.”
2. Replace “complete Willow shot sets” with “the reported Willow cohorts of 400,000 and 100,000
   shots.” Do not imply that the full public release was used or that no records were excluded.
3. In T1, replace “qualified zero-shot target-domain transfer” with “source-reported no-target-update
   evaluation on one external hardware dataset.” State that strict target-unseen transfer is not
   auditable because T0 hardware provenance, target exposure during selection and exact checkpoint
   identities are missing.
4. In the operation replay, replace “fixed deployable QAdapt pre-decoder after 100 cumulative
   epochs” with wording that separates the described final training schedule from the unidentified
   checkpoint used in each reported result.
5. Add the absent Ising-fast epoch/sample budget to the matched-comparator boundary.
6. Preserve the existing R1/M1 conclusion: the OOD result is static-Pauli parameter coverage, not
   wrong-memory-law robustness or online drift adaptation.

### Draft source note

1. Keep the source fact that Sec. 5.4 reports no target-domain fine-tuning, update or calibration, but
   add a source-local gap for unreported target exposure/model-selection independence, T0 hardware
   provenance and cohort filtering.
2. Extend the comparator limitation to include unstated baseline epochs/data budget and unidentified
   result checkpoints.
3. State explicitly that 110/110 refers to the complete constructed grid, not a sampled population.
4. Split the current “explicitly reports” limitation wording: confidence intervals and the EWC
   comparator are explicitly stated as absent; seed variation and paired-shot analysis are listed as
   required follow-up reporting.
5. Retain all current numerical point estimates and the wrong-history-model gap; those are faithful.

## Disposition

- `read_status`: complete
- official-object verification: pass
- cross-review result: **revise**
- audit semantic fidelity: revise on population and target-transfer wording
- source-note semantic fidelity: revise on target-exposure and comparator provenance boundaries
- static-Pauli versus wrong-memory-law classification: pass
- manifest action: none taken

After these revisions, the strongest defensible use is: QAdapt reports a complete fixed-grid
comparison over static Pauli parameter shifts and a no-target-update evaluation on one external
Willow record cohort, with the QAdapt package outperforming an unmatched neural pre-decoder in the
reported point estimates. It does not establish memory-conditioned decoder benefit, wrong-memory
robustness, online adaptation, population-level uncertainty, strict target-unseen transfer,
cross-device/cross-code transfer or end-to-end latency.

## Revision verification

### Verification decision

**REVISE — semantic revisions pass; schema readiness does not yet pass.** The revised audit and
source note close every scientific wording change requested above. Their source and audit hashes are
internally consistent. The source note still has one inexact locator and four relation labels that
would fail the current note schema after its intentional draft-status gate is lifted.

No audit, source-note or manifest file was changed during this verification.

### Hash and artifact verification

- Reviewed audit changed from SHA-256
  `10ee1874bef7badea3368bfb921284a37cd895ab99e7f3ac2b9d8e3530207742` to
  `99bec4adbd88848246a4dee164e82d459c55f2e206fd1ee5315f139ef6027fdc`.
- Reviewed source note changed from SHA-256
  `4cacf877abecb4bbb01b5a138d055d30e3021b0f7715363a7a230ba1cb386557` to
  `74f40d94068b659482537fa191d0f9db8c323da791a625cefa9c82c3a9dddb52`.
- The note's declared audit hash is the new
  `99bec4adbd88848246a4dee164e82d459c55f2e206fd1ee5315f139ef6027fdc`, exactly matching the
  revised audit.
- The note's declared source hash remains
  `2c8f6fec9a1dd0a76f041d76cdd4b76be74ee466a7cbb9719f15637f13144c7c`, exactly matching the
  fixed official PDF.

### Required-revision closure

| requested revision | revised location | verification |
|---|---|---|
| Replace population-wide language with complete coverage of a fixed design grid | Audit D2, grid replay row, Project application and verdict; note Synthetic OOD grid | **closed** |
| Replace “complete Willow shot sets” with reported cohorts and preserve filtering/pairing uncertainty | Audit D2, Willow replay, Project application and unresolved fields; note Willow protocol and target-exposure gap | **closed** |
| Narrow zero-shot/frozen transfer to source-reported no-target-update external-data evaluation | Audit T1, Transfer application, kill conditions and verdict; note Willow protocol/result, cross-setting gap and target-exposure gap | **closed** |
| Separate described 100-epoch schedule from unidentified evaluated checkpoints | Audit Q-EWC replay row and Willow replay; note comparator and checkpoint gaps | **closed** |
| Add missing Ising-fast epoch/sample budget and unequal exposure | Audit D2 and comparator replay; note Comparator configuration | **closed** |
| Preserve static-Pauli OOD versus wrong-memory-law distinction | Audit R1/M1 and verdict; note temporal-generator and wrong-history-model gaps | **closed** |
| Add target-exposure/model-selection/T0-provenance/cohort boundary | Note Willow protocol and new `qadapt-gap-target-exposure`; audit T1 and Transfer application | **closed** |
| Split explicit limitations from requested follow-up reporting | Note Stated evidence limitations | **closed** |
| Retain numerical point estimates and latency boundary | Audit replay; note Results and latency sections | **closed** |

The revised text no longer claims a sampled population, complete public Willow cohort, strict
target-unseen transfer, common cross-distance checkpoint, matched training budget, wrong-memory-law
robustness or end-to-end latency.

### Schema verification

The ordinary `literature_rag.py audit --schema-only` currently excludes the note at the intended
admission gate because its metadata still says `evidence_status = "unpersisted"` and
`admission_status = "draft_not_admitted"`. A read-only body/relation parse beyond that gate found the
following additional issues:

1. `Data availability` uses `Source locator: Data Availability`, which has no accepted page,
   section, figure, table, equation, algorithm or paragraph anchor. A locator such as
   `PDF p. 9, Data Availability section` is required.
2. Relation `qadapt-htnet` uses object label `heterogeneous spatiotemporal network`, which does not
   occur verbatim in the claim for `qadapt-spatiotemporal-branches`. `HTNet` does.
3. Relation `qadapt-q-ewc` uses object label `Q-EWC sequential adaptation`, which does not occur
   verbatim in the claim for `qadapt-ewc-schedule`. `Q-EWC` does.
4. Relation `qadapt-willow-zero-shot-result` uses object label
   `Willow no-target-update logical-error result`, which does not occur verbatim in the claim for
   `qadapt-willow-result`. `On Willow` does, or the claim must name the longer label explicitly.
5. Relation `qadapt-backend-latency-boundary` uses object label
   `residual-backend latency boundary`, which does not occur verbatim in the claim for
   `qadapt-latency-boundary`. `PyMatching on the residual syndrome` does.

With those five fields hypothetically corrected in memory, all 38 evidence sections—27
`paper_fact`, 11 `literature_gap`—and all five relations pass the body/relation parser. The remaining
metadata promotion to persisted, independently reviewed evidence should occur only after these
schema corrections and is outside this verification's authorization.

### Final revision-verification disposition

- scientific revision closure: **pass**
- source/audit hash binding: **pass**
- fixed-PDF hash binding: **pass**
- ordinary current-state corpus audit: expected draft exclusion
- post-promotion schema readiness: **revise**
- overall revision-verification result: **REVISE**

## Final schema re-verification

### Final decision

**PASS for pre-admission review.** All five schema blockers identified in the preceding verification
are closed, all scientific revisions remain intact, and the source/audit artifact bindings validate.
The note remains deliberately marked `unpersisted` and `draft_not_admitted`, so the ordinary corpus
command continues to exclude it at the admission-status gate. That is now the only reason it is not
listed as a validated/admitted note.

No source note, audit or manifest file was modified during this final verification.

### Final hashes

- fixed official PDF:
  `2c8f6fec9a1dd0a76f041d76cdd4b76be74ee466a7cbb9719f15637f13144c7c`
- revised audit, unchanged since semantic revision:
  `99bec4adbd88848246a4dee164e82d459c55f2e206fd1ee5315f139ef6027fdc`
- schema-corrected source note:
  `17adfbe2a0637be672b1f1b4c1245dcd32e2cc1c38bb450263a55c88d4457575`
- the note declares the same PDF and audit hashes as the actual files: **pass**

### Five-blocker closure

| prior blocker | final source-note value | result |
|---|---|---|
| Data Availability locator lacked an accepted anchor | `PDF p. 9, Data Availability section` | **closed** |
| `qadapt-htnet` label absent from fact claim | `HTNet` | **closed** |
| `qadapt-q-ewc` label absent from fact claim | `Q-EWC` | **closed** |
| Willow-result relation label absent from fact claim | `On Willow` | **closed** |
| latency-boundary relation label absent from fact claim | `PyMatching on the residual syndrome` | **closed** |

A read-only execution of the schema's metadata, identity, repository-path, PDF-signature,
source-hash, audit-hash, section and relation checks now passes with:

- 38 classified evidence sections;
- 27 `paper_fact` records;
- 11 `literature_gap` records;
- 5 valid relations;
- all 11 declared visual-check pages valid.

The standard schema-only and artifact-verified corpus commands both stop earlier at the intentional
`unpersisted`/`draft_not_admitted` gate. After authorized metadata promotion, no remaining
body/relation/artifact blocker was found in this verification.

### Scientific regression check

- The 110 settings remain described as a complete fixed design grid, not a sampled population.
- Willow remains a source-reported no-target-update evaluation, not strict target-unseen transfer.
- Target exposure, T0 hardware provenance, cohort filtering and checkpoint mapping remain explicit
  gaps.
- Ising-fast's missing epoch/sample budget and the unequal package/training comparison remain
  visible.
- Static-Pauli parameter OOD remains separated from wrong-memory-law robustness.
- LER uncertainty, paired-shot evidence and end-to-end latency remain absent rather than promoted.

### Final disposition

- substantive revision closure: **pass**
- schema-blocker closure: **pass**
- source/audit hash binding: **pass**
- artifact verification: **pass**
- scientific regression check: **pass**
- manifest action: none taken
- final pre-admission cross-review result: **PASS**

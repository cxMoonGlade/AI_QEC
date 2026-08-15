# Independent cross-review — Yan et al., arXiv:2605.12046v1

## Decision

**REVISE.** The audit reaches the correct coverage judgments: Yan et al. provide a bounded
target-calibrated simulation-to-matched-hardware application and fixed-checkpoint generalization to
lower scalar rates within two separately trained generator families. The source does not close
memory-conditioned decoder benefit, population-level matched evidence, wrong-memory-model
robustness, or frozen cross-device/cross-code/cross-distance transfer.

The audit and draft note should not yet be admitted for four reasons:

1. Table 1 is described as one 5,000-shot test partition, but several printed two-decimal LER values
   cannot be binary-error fractions of a single 5,000-shot cohort. The paper does not explain the
   averaging, repeated split or other aggregation that produced them, and gives no hardware
   uncertainty or paired-decision record.
2. The hardware comparison uses an outcome-selected distance-three center and only one selected
   distance-three and one distance-five setting. Its lower calibrated-TCN point estimates must not
   be promoted to a population or statistically established hardware benefit.
3. The HLS latency is internally inconsistent: main p. 9 reports 271 clock cycles, while Appendix
   Table 16 on p. 27 reports 267; both are labelled 0.77 microseconds. The note records only 271 and
   anchors the fact to p. 8, which contains analytical estimates rather than the HLS result.
4. The source note has pre-admission schema blockers: four undeclared visual-anchor pages, four
   relation labels absent from their linked claims, and one relation that points to a
   `literature_gap` instead of a `paper_fact`.

No source note, audit or manifest file was modified.

## Fixed-object verification

- Independently downloaded official source: `https://arxiv.org/pdf/2605.12046v1`.
- Official record: arXiv:2605.12046v1, *Rethink the Role of Neural Decoders in Quantum Error
  Correction*, Ge Yan, Shanchuan Li and Yuxuan Du, submitted 12 May 2026. The arXiv record lists
  only v1 and comments “Accepted to ICML 2026; 33 Pages, 9 figures.”
- Official and local PDFs match: PDF 1.7, 33 pages, 1,333,810 bytes, SHA-256
  `6b06b88907705b4b9ce674751cf198a188ff1a0a4446fd12b754121116f58c8c`.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/YAN_NEURAL_DECODER_TRANSFER_2605_12046_AUDIT_2026-08-05.md`,
  SHA-256 `6f4545e7bac53ec4c2bd51249340808a583ac708f76f4361d07cc4b534cb96a6`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/yan_neural_decoder_transfer_2605.12046v1_source_review.md`,
  SHA-256 `de671d917e2367b70f1e8649641b50a59a935861c853f0aac157bf15823378e5`.
- The note declares the exact source and audit hashes above.
- Independent full-text reading covered all 33 pages, including Appendices A--E and Tables 1--20.
  The source identity, ordered-record equations, TCN architecture, hardware comparison and dataset
  protocol, HLS results, and cross-rate experiments were visually checked on rendered PDF pages 1,
  3, 4, 6--9, 23, 27 and 32--33.

## Publication-status check

`publication_status = "preprint"` is correct for the fixed evidentiary object. The source identity is
the version-pinned arXiv v1 artifact, not a separately acquired PMLR version of record. Conference
acceptance is accurately retained as a source fact in the note and audit; it does not change the
schema identity of this artifact. The value `preprint` is accepted by the current literature schema.

## Independent scientific reconstruction

### Representation, decoder interface and computation

The evaluated TCN receives a fixed `r = d` window of ordered detector events from a repeated
rotated-surface-code Z-memory task. Each round is embedded on a spatial grid and processed by a 2D
convolutional encoder; the resulting sequence is passed through one-dimensional convolution blocks
and a classifier that predicts the cumulative logical flip. It is a fixed-window discriminative
decoder, not a continuing latent-state or carrier-transition model.

The comparison also includes MLP, 3D-CNN, Transformer and neural-BP/GNN packages, but the hardware
result uses the small TCN. Standard and correlated MWPM, uniform-prior TCN and calibrated-prior TCN
are complete decoder packages with different representations, training exposure and computation.
They are not otherwise-matched treatments that differ only in history access. MWPM itself consumes
a spacetime detector graph; the source contains no history-truncation or record-order control.

The paper's language about crosstalk, leakage, non-Pauli effects and latent patterns is
interpretive. The reported hardware evaluation does not observe a microscopic state, identify a
carrier or isolate one mechanism. Device-calibrated synthetic pretraining can encode an effective
hardware-aligned distribution without establishing why that distribution differs from a uniform
depolarizing generator.

### Target-calibrated simulation to matched hardware

For each selected Sycamore setting, the source generates five million synthetic training examples
from the target dataset's supplied device-calibrated `circuit_noisy.stim`. The resulting TCN is
called zero-shot when it is applied to experimental records without using the 45,000 experimental
shots allocated for optional fine-tuning. “Zero-shot” therefore means no experimental-shot
fine-tuning; it does not mean calibration-blind, target-unseen or device-independent deployment.

The hardware tasks are Z-memory at `(d,r) = (3,3)` and `(5,5)`. For distance three, the authors
select center `(7,5)` because it has the lowest baseline logical error rate among four available
centers. That target-informed selection prevents population-wide interpretation and may condition
the displayed result on baseline performance. No independent device, code family, unselected
distance-three population or different distance is evaluated with the same model.

Table 1 reports the following LER point estimates:

| distance | standard MWPM | correlated MWPM | calibrated TCN zero-shot | calibrated TCN fine-tuned |
|---:|---:|---:|---:|---:|
| 3 | 8.01% | 7.38% | 6.81% | 6.70% |
| 5 | 14.38% | 12.52% | 11.59% | 11.47% |

Uniform-depolarizing pretraining gives much worse zero-shot points, 34.42% and 47.89%, and remains
worse than the calibrated arm after fine-tuning. The comparison supports the narrower statement
that alignment of the synthetic training generator is important under these selected conditions.
It does not isolate a benefit from temporal-memory information.

### Hardware sample and uncertainty boundary

Appendix D.1 states that each selected configuration contains 50,000 experimental shots, split into
45,000 for optional fine-tuning and 5,000 for testing. Table 1 does not provide confidence intervals,
standard errors, run counts, split seeds, paired-decoder disagreements or a statistical test. The
paper also does not state whether every displayed decoder uses one identical 5,000-record cohort or
whether values are averaged over splits or model runs.

The printed values reveal that some aggregation is missing from the protocol description. With
exactly 5,000 binary trials, a percentage must change in increments of 0.02. Yet, for example,
8.01%, 6.81%, 9.27%, 47.89%, 11.59% and 11.47% correspond to half-integer error counts when multiplied
by 5,000. This does not invalidate the point estimates, but it falsifies a literal reconstruction as
one unaveraged 5,000-shot binary count. The audit should say **the paper declares a 5,000-shot test
allocation**, not that Table 1 is replayed on one known common partition.

Because the calibrated-TCN advantages over correlated MWPM are reported only as 0.57 and 0.93
percentage-point differences without uncertainty or paired predictions, the cross-review cannot
determine their statistical precision. Downstream prose may report lower point estimates under the
selected protocol; it should not adopt the source's unqualified “significantly outperforms” wording.

### Within-family scalar-rate generalization

Appendix E.4 trains separate TCNs under two generators:

- uniform depolarizing noise at `p = 0.005`;
- SI1000 at `p_base = 0.004`, with fixed operation-class multipliers.

Each checkpoint is tested only at lower scalar rates within its own generator family, at distances 5
and 7. Test sizes increase from 200,000 at rate 0.003 to five million at rate 0.001, and Tables 19--20
report mean plus or minus standard deviation over three runs. Optional same-family fine-tuning changes
the displayed absolute LER by less than 0.02 percentage points.

This is useful fixed-checkpoint downward rate-shift evidence. It does not apply a uniform-trained
checkpoint to SI1000 or the reverse. Neither generator defines a persistent carrier, temporal
transition kernel or memory-state calibration, and the experiment does not impose a stale lifetime,
wrong history law, mixed mechanism or cross-family misspecification. It is therefore not
wrong-memory-model robustness, despite the broader title used for Appendix E.4.

### HLS and deployment boundary

Most FPGA values in the main comparison are analytical estimates obtained from MAC counts, assumed
INT4 processing-element cost, 50% LUT derating and an overhead factor. The paper additionally
synthesizes a pruned, W4A4, distance-nine large TCN on a VP1902 target. This is a standalone decoder
module result, not an end-to-end quantum control-stack or hardware-record deployment.

The source has an unresolved numerical inconsistency:

- main p. 9 reports 271 cycles at 350 MHz, or 0.77 microseconds;
- Appendix D.4, Table 16, p. 27 reports component counts `193 + 28 + 46 = 267` cycles and labels the
  total 0.77 microseconds.

The stated time is compatible with the rounded 267-cycle value at 350 MHz, whereas 271 cycles also
rounds to 0.77 microseconds. The source does not reconcile the cycle totals. The note and audit must
preserve the discrepancy rather than select 271 as a uniquely verified value.

## Assigned-row cross-check

| row | independent source finding | audit/note treatment | result |
|---|---|---|---|
| D1 — hardware memory-conditioned benefit | TCN consumes an ordered `r=d` record and has lower selected calibrated-prior point estimates, but no control limits history, randomizes order or removes a continuing state. | Missing disposition is correct. | **pass** |
| D2 — population matched comparison | The paper states a 5,000-shot test allocation for each of two selected configurations; d=3 is outcome-selected, Table 1 has no uncertainty, exact cohort reuse is unstated, and several values require unreported aggregation. Decoder packages are not one-factor matched. | Core bounded/not-matched conclusion is correct; “one 5,000-shot partition” and benefit wording require revision. | **revise** |
| R1 — wrong memory model | Two fixed checkpoints generalize downward in scalar rate within their own separately trained generator families, with three-run mean and s.d. No model-family crossing or temporal-law perturbation occurs. | Correctly classified as within-family rate shift, not wrong-memory robustness. | **pass** |
| T1 — frozen transfer | Device-calibrated synthetic pretraining is applied without experimental-shot fine-tuning to matched target records. Models are target-calibrated and distance-specific; no cross-device, code-family or cross-distance deployment is shown. | Bounded simulation-to-matched-hardware wording and missing cross-domain T1 disposition are correct. | **pass** |
| F1 — frame residual | Generator/calibration exposure, per-distance architecture, fine-tuning protocol, record window and output must remain separate dimensions. | Correct; source belongs in Section 5 rather than a Section 3 memory-representation row. | **pass** |

## Operation-replay boundary

The conceptual chains can be reconstructed:

| input | transformation | assumption/resource | output | status |
|---|---|---|---|---|
| Device-calibrated Stim circuit | Generate five million synthetic target-aligned samples and train a distance-specific TCN | Supplied circuit is an adequate effective proxy for the selected hardware condition | Fixed zero-shot TCN | complete as a declared chain |
| Selected Sycamore records | Allocate 45,000 shots to optional fine-tuning and 5,000 to testing | Split construction, seed, exact common-record reuse and Table-1 aggregation are unstated | Hardware LER point estimates | **not exactly replayable** |
| Uniform or SI1000 generator at one rate | Infinite-online training of one TCN per distance/family | Same generator form remains valid at lower rates | Fixed checkpoint | complete |
| Lower rates in the same family | Evaluate zero-shot and after optional lightweight fine-tuning | Downward scalar shift only | Tables 19--20 mean and s.d. | complete at printed protocol level |
| Compressed distance-nine TCN | HLS synthesis and incremental buffered inference | VP1902 at 350 MHz; standalone decoder module | 0.77-microsecond result | **cycle count internally inconsistent: 271 versus 267** |

No source-code release, fixed Table-1 split/checkpoint identity or per-shot prediction artifact is
specified in the manuscript. `operation_replay_status = "complete"` can therefore mean that the
declared scientific transformation is reconstructed; it must not be read as exact numerical replay
of the hardware point estimates.

## Source-note schema review

The draft has 16 evidence records: 14 `paper_fact`, two `literature_gap`, and four declared
relations. It is intentionally marked `unpersisted` and `draft_not_admitted`, so the ordinary parser
stops at the expected admission gate. A read-only prospective parse found these later blockers:

1. Facts anchored to pages 1, 3, 4 and 8 are not represented in
   `visually_checked_pages = [6, 7, 23, 32, 33]`. The HLS fact should instead be anchored to and
   visually register main p. 9 and Appendix Table 16 on p. 27.
2. All four relation labels fail the requirement that the exact label occur in the linked claim:
   `temporal convolutional surface-code decoder`,
   `device-calibrated simulation-to-hardware zero-shot result`,
   `within-generator cross-rate fixed-checkpoint result`, and
   `absence of an explicit temporal-memory law or access ablation`.
3. The final relation points to `yan-gap-memory-law`, a `literature_gap`; schema relations may point
   only to `paper_fact` records. It should be removed rather than converting a source-local absence
   into a positive fact.

With the visual pages added, the first three labels replaced by exact phrases already present in
their fact claims, the invalid gap relation removed, and only the intentional admission metadata
promoted in memory, artifact-verifying parsing succeeds with 16 records and three relations. This
mechanical result does not close the scientific Table-1 or HLS revisions above.

## Required revisions

### Audit

1. Replace “one 5,000-shot test partition” with “a stated 5,000-shot test allocation per selected
   configuration.” Add that exact cohort reuse/aggregation is unspecified and some printed values
   are incompatible with a single unaveraged 5,000-trial binary count.
2. Restrict the hardware conclusion to lower **point estimates** under one selected d=3 center and
   one d=5 configuration; retain the absence of uncertainty and paired decisions.
3. Record the main-text 271-cycle versus Appendix Table-16 267-cycle HLS discrepancy; retain 0.77
   microseconds as the common rounded time and the non-integrated-control-stack boundary.
4. Clarify that operation replay closes the declared transformation chain, not exact Table-1
   split/aggregation or point-estimate reproduction.

### Draft source note

1. Preserve the stated 45,000/5,000 allocation, but add a source-local numerical-provenance boundary
   for unstated Table-1 aggregation, common-record reuse, uncertainty and split/checkpoint identity.
2. Revise `yan-fpga-boundary` to report both 271 and 267, anchor main p. 9 and Appendix D.4 Table 16
   p. 27, and register the visually checked pages.
3. Add all other fact-anchor pages to `visually_checked_pages`.
4. Replace the first three relation labels with exact claim phrases and remove the relation to the
   `literature_gap`.
5. Keep `publication_status = "preprint"`, the target-calibration qualifier, the within-family
   scalar-rate boundary and the missing cross-device/code/distance result.

## Disposition

- `read_status`: complete
- `evidence_status`: unpersisted
- official-object verification: pass
- publication-status classification: pass
- audit row dispositions: pass
- audit semantic/provenance fidelity: revise on hardware aggregation and HLS inconsistency
- source-note semantic fidelity: revise on the same two issues
- source-note admission schema: revise
- artifact/hash integrity: pass
- manifest action: none taken

After revision, the strongest defensible use is: Yan et al. report lower calibrated-TCN hardware LER
point estimates on two selected Sycamore settings after target-calibrated synthetic pretraining, and
fixed TCN checkpoints retain performance under lower scalar rates within their respective synthetic
generator families. The paper does not establish a population-level or statistically quantified
hardware advantage, memory-conditioned benefit, wrong-memory-model robustness, or frozen
cross-device, cross-code or cross-distance transfer.

## Final revision verification

**Final decision: PASS for pre-admission review.** All scientific, numerical-provenance and schema
revisions requested above are closed. The note remains intentionally `unpersisted` and
`draft_not_admitted`; that status gate is now the only reason the standard directory audit excludes
it.

### Revision closure

| prior issue | verified revision | result |
|---|---|---|
| One known 5,000-shot hardware partition was overstated | Audit and note now distinguish the source's stated 5,000-shot allocation from unstated cohort reuse, split/checkpoint identity and aggregation. | **closed** |
| Half-integer count incompatibility was absent | Both records state that several two-decimal Table-1 percentages cannot arise from one unaveraged 5,000-trial binary count. | **closed** |
| Hardware benefit lacked uncertainty boundary | Results are consistently called selected point estimates; absence of hardware uncertainty, paired decisions and a test is explicit. | **closed** |
| Selected d=3 setting was underqualified | Center `(7,5)` remains explicitly identified as the lowest-baseline choice among four centers, precluding population promotion. | **closed** |
| HLS cycle count was reported only as 271 | Audit and note preserve main-text 271 versus Appendix-Table-16 267, both labelled 0.77 microseconds, with no source reconciliation. | **closed** |
| HLS locator missed the result pages | The note points to main p. 9 and Appendix D.4 Table 16 p. 27 and declares both as visually checked. | **closed** |
| Four relation labels failed claim containment | Three retained labels now use exact claim phrases: `temporal convolutional decoder`, `device-calibrated synthetic pretraining`, and `fixed TCN checkpoints`. | **closed** |
| A relation pointed to a `literature_gap` | The invalid temporal-memory-gap relation was removed; the gap remains properly typed as source-local absence. | **closed** |
| Fact-anchor pages were absent from visual metadata | The note now lists all independently checked pages: 1, 3, 4, 6--9, 23, 27 and 32--33. | **closed** |
| Publication status required confirmation | `publication_status = "preprint"` remains correct for the fixed arXiv v1 object while ICML acceptance is retained as a source fact. | **closed** |

### Final artifact and schema checks

- fixed official/local PDF SHA-256:
  `6b06b88907705b4b9ce674751cf198a188ff1a0a4446fd12b754121116f58c8c`;
- revised audit SHA-256:
  `fd903ac9fb2fed3806e2b95784cd32c498a613850146001e9d668859f32bc633`;
- revised source-note SHA-256:
  `f7e1ef1e364a2823378c1ea845c1eecebe2ebefaa18f298f0848d728d6b9c694`;
- the note declares the exact PDF and audit hashes above: **pass**;
- `git diff --check` for audit, note and cross-review: **pass**.

A read-only prospective `parse_note(..., verify_artifact=True)` run, changing only the intentional
draft admission values in memory, succeeds with:

- 17 classified evidence records;
- 14 `paper_fact` records;
- three `literature_gap` records;
- three valid relations;
- 11 declared visual-check pages;
- `publication_status = "preprint"`;
- source-PDF and audit-packet hash verification enabled.

The standard schema-only directory audit stops earlier at the expected
`unpersisted`/`draft_not_admitted` gate. No source note, audit or manifest file was changed during
this final verification.

Final disposition:

- official-object and artifact integrity: **pass**;
- source-note semantic fidelity: **pass**;
- audit semantic fidelity: **pass**;
- D1/D2/R1/T1/F1 boundaries: **pass**;
- numerical-provenance qualifications: **pass**;
- pre-admission schema readiness: **pass**;
- manifest action: none taken.

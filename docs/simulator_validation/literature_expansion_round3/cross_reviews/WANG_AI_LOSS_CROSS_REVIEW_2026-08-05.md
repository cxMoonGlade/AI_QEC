# Independent cross-review — Wang et al., arXiv:2604.14269v2

## Decision

**REVISE.** The audit and draft source note preserve the important scientific boundaries. The
source contains a synthetic, episode-persistent data-loss process whose repeated local flicker is
diagnostically useful; it does not contain quantum-hardware records, a matched history-access
ablation, reported population size or uncertainty, wrong-model robustness, frozen transfer, or a
closed-loop reinitialization benefit. Its strongest defensible use is therefore a bounded Sections
4--5 example, not an upgrade of any of those stronger evidence rows.

Two source-level reconstruction gaps nevertheless prevent a pass in the present form. First, the
paper declares how loss persists and qualitatively explains the resulting flicker, but does not
specify how stochastic removal, shortened checks, overlapping multiple losses, and their detector
records are implemented in Stim. Second, the printed STGNN logical-output specification is
internally inconsistent: the main text calls the training label a binary scalar, the Supplemental
logical head and Algorithm 1 use one `L` or one `L in R^2`, while Eq. (S7) sums over `d` outputs
`L_k` and labels `y_k`; Figure 3 then averages `d` equivalent logical observables. The audit's
claims of a complete generator replay and complete printed STGNN forward map are consequently too
strong unless they are explicitly bounded to conceptual semantics and the unresolved mappings are
recorded.

The source note also needs three locator expansions and one semantically meaningful relation label.
The current machine schema passes because the generic label `data qubit` occurs in the claim, but it
does not name the persistent-loss model identified by the relation.

No audit, source-note or manifest file was modified in this cross-review.

## Fixed-object verification

- The fixed object is arXiv:2604.14269v2, *AI-Enabled Decoding of Qubit Loss for Quantum
  Error-Correcting Codes*, by Yuqing Wang and six coauthors. The PDF carries an arXiv version line
  of 25 May 2026 and an internal date of 26 May 2026.
- A fresh temporary retrieval from `https://arxiv.org/pdf/2604.14269v2` is byte-identical to the
  fixed local artifact: PDF 1.7, 12 pages, 763,440 bytes, SHA-256
  `098dc3506421d58a23a8a2cee15161d3de08a41228299470279319d9149c84dc`.
- The 12-page object contains seven pages of article and references followed by five pages of
  embedded Supplemental Material. The independent reading covered all pages, Figs. 1--5 and S1,
  Tables I--II, Eqs. (S1)--(S23), and Algorithms 1--2. All 12 rendered pages were inspected;
  load-bearing equations, figures and tables were checked visually.
- Audit reviewed:
  `docs/simulator_validation/literature_expansion_round3/WANG_AI_LOSS_DECODER_2604_14269_AUDIT_2026-08-05.md`,
  SHA-256 `643bb53216afe5a5f789b3e7b46857b03c4377e820db3cd4aa19d5ba0ca81f97`.
- Draft note reviewed:
  `docs/simulator_validation/literature_expansion_round3/drafts/wang_ai_loss_decoder_2604.14269v2_source_review.md`,
  SHA-256 `814c132dbd43fa24ee6aee845d3dcfc1955e8eb25f45928e5d66e1de0f83e34f`.
- The note's declared PDF and audit hashes exactly match the reviewed files. Artifact-verifying
  `parse_note` succeeds with 29 evidence records (21 `paper_fact`, eight `literature_gap`) and eight
  relations. The full draft-directory audit also validates this note with 21 paper facts.
- The note is not present in `docs/papers/CURRENT_CORPUS.toml`. No manifest action was taken.

## Independent scientific reconstruction

### Persistent carrier and flicker

The declared task is a rotated distance-5 surface-code memory circuit with `T` repeated QEC rounds
and a final destructive data readout. The Supplemental noise model fixes idle depolarizing,
post-CNOT depolarizing, measurement-bit-flip and per-round loss probabilities at 0.01. A lost data
qubit remains absent through the end of the simulated episode, whereas an ancilla loss is cleared by
the next round's refresh. The data-loss state is therefore absorbing only within the declared
episode; no reinitialization is executed in the reported task.

The paper's mechanism is removal of the data-qubit degree of freedom. Neighboring shortened X- and
Z-type checks that formerly commuted can then become effectively noncommuting, yielding stochastic
outcomes while the qubit is absent. Figure 1 shows persistent local flicker, and the Supplemental
delayed-erasure construction identifies in-round and cross-round correlated flip patterns for a
single lost data qubit. This supports a source-bounded statement about persistent simulated loss and
multicycle temporal structure. It is neither a device observation nor a formal test of quantum
non-Markovianity.

The source does not close an executable generator replay. It says that Stim generates the training
records and that a lost data qubit no longer participates in later gates, but supplies no circuit
transformation, sampler algorithm or code for stochastic removal. The single-loss rules on p. 12
are presented for an approximate delayed-erasure graph; that graph explicitly neglects interactions
among multiple lost data qubits and therefore cannot silently serve as the unspecified multi-loss
training generator.

### QEC interface and decoder computation

The learned interface contains ordered stabilizer measurements and consecutive-round XOR detector
events over `T+1` inputs. STGNN consumes the complete episode simultaneously, performs non-causal
temporal extraction with Conv1D and attention, combines this with local Tanner-graph messages and
global spatial attention, and returns logical and loss-head outputs. The modified AlphaQubit-style
model instead updates recurrent ancilla states round by round and additionally receives engineered
recent-window flicker counts. Standard MWPM and delayed-erasure MWPM are different complete decoder
packages; the latter receives exact final spatial loss locations but averages over unknown loss
times and neglects multiple-loss interactions.

This is not a matched information-access comparison. Architecture, parameter count, engineered
features, side information, graph approximation and time-to-decision all vary. The full-window
STGNN is about 8M parameters; the modified recurrent comparator is about 12.7M parameters. The
source also omits training-set size, splits, optimizer, schedule, seeds and checkpoint provenance.

The STGNN logical head cannot be reconstructed exactly from the printed specification. Main p. 3
describes a binary scalar logical label. Supplemental p. 9 describes a final logical state `L` and
Algorithm 1 ensures one `L in R^2`, whereas Eq. (S7) uses `L_k` and `y_k` for `k=1,...,d`.
Figure 3's metric averages predictions for `d` equivalent logical lines. The modified
AlphaQubit-style output is explicitly distance-many in Eqs. (S20)--(S23), so that section does not
resolve the STGNN ambiguity.

### Reported outputs

Figure 3 gives one distance-5 synthetic comparison over `T=3` to 10. The two learned curves nearly
coincide and lie above the two MWPM curves, but there are no test-sample counts, error bars,
confidence intervals, seed repetitions or statistical tests. Logical operators intersecting a lost
data qubit are removed before accuracy is averaged, so this is a survivor-conditioned metric rather
than unconditional logical preservation.

At threshold 0.5 after ten rounds, the reported STGNN loss recall and precision are 0.654 and 0.845;
the modified AlphaQubit-style values are 0.652 and 0.856. Figure 5 conditions misses on the loss
occurrence round: first-round losses have miss rate below 10%, while final-round losses exceed 85%.
This is consistent with a longer persistent signature supplying more observations, but loss time,
persistence duration and opportunity all change together. It is not a frozen-decoder history
removal, shuffle or truncation ablation.

The latency figures compare approximately 0.410 ms per recurrent update and 4.10 ms accumulated over
ten updates with one 0.595 ms delayed full-window STGNN pass. Platform, batch size, precision,
warm-up, repetitions and dispersion are absent, and the source itself calls the benchmark
preliminary. These values cannot establish equal-decision-time or platform-independent speedup.

## Assigned-row findings

| row | independent finding | disposition |
|---|---|---|
| L1 -- persistent-loss history is diagnostically usable | Persistent simulated data loss produces repeated local flicker; overall loss diagnostics and occurrence-round-conditioned miss rates are reported. No matched history-access treatment is present. | **closed only as synthetic capability and conditional association** |
| D1 -- hardware memory-conditioned decoder benefit | All QEC records and labels are generated in simulation. Atom-array operation, reinitialization and continuous loading are motivations, not evaluated operations. | **missing** |
| D2 -- population-level matched memory-decoder comparison | Figure 3 is one distance-5, fixed-noise comparison of unmatched decoder packages. Test-population size, uncertainty and record pairing are unreported. | **missing** |
| R1 -- robustness under a wrong memory model | One printed persistent-loss/Pauli/measurement model is evaluated. No frozen decoder is exposed to a wrong loss rate, lifetime, persistence law, mixed mechanism, stale calibration or held-out noise family. | **missing** |
| T1 -- frozen-model transfer | One code family and distance are reported; the source does not identify a frozen checkpoint evaluated across distance, code, device or loss mechanism. Generalization and qLDPC decoding are future work. | **missing** |
| C1 -- calibration and computational cost | Parameter totals and preliminary latency point estimates are reported, but training cost and an equal operational latency protocol are absent. | **partial and preliminary** |
| F1 -- framework residual | The source fits representation--interface--computation if the episode-persistent generator state is kept separate from learned hidden representations and decoder-facing graph abstractions. | **no fifth category required** |

These dispositions agree with the audit's central D1/D2/R1/T1 judgment.

## Sections 4--5 relevance

For Section 4, the paper can serve as one canonical mechanism-to-consequence example: an
episode-persistent loss state changes later check behavior, imprints an ordered multicycle flicker
pattern, complicates syndrome inference, and makes diagnostic performance depend on how much of the
post-loss record is available. The example must remain explicitly synthetic and must not be called
strict non-Markovianity. Its suggested reinitialization policy is an unresolved downstream action,
not a demonstrated QEC benefit.

For Section 5, the same source illustrates why observation, attribution, logical effect, decoder
benefit and transfer must remain separate. The simulated cause is known by construction; the source
does not infer a microscopic cause from hardware data. Figure 3 reports decoder-package point
estimates under loss, but does not isolate either the logical effect of persistence or the benefit of
history access. Survivor conditioning further narrows the logical claim. No hardware, population
uncertainty, wrong-model or transfer evidence upgrades the corresponding maturity judgments.

The paper is therefore better used as a bounded Section 4 mechanism example followed by a Section 5
evidence qualification. It should not be promoted to a concrete Section 3 physical-to-QEC approach
bundle: the learned networks are interface-first discriminative computations, not the physical
representation that carries the dependence.

## Source-note claim and locator audit

| fact or gap | semantic finding | locator/relation finding | result |
|---|---|---|---|
| `wang-source-identity` | Correct. | Title/version and embedded supplement were independently verified. | **pass** |
| `wang-selection-scope` | Correct. | The claim is anchored on pp. 1--2, but the body statement that evaluation is simulated needs p. 3. | **revise locator** |
| `wang-persistent-loss-model` | Correct; persistence is bounded to the episode. | Main p. 3 and Supplemental p. 12 are exact. | **pass** |
| `wang-loss-flicker-mechanism` | Correct as the source's mechanism. | Main pp. 1--2 and Fig. 1 are exact. | **pass** |
| `wang-qec-record` | Correct. | The body attributes the explicit no-loss-flag/no-side-channel statement to modified AlphaQubit, but that statement is on p. 10, not pp. 2 and 8. | **revise locator to include p. 10** |
| `wang-stgnn-full-window` | Correct. | Main p. 2 and Supplemental p. 8 are exact. | **pass** |
| `wang-stgnn-architecture` | The printed modules and parameter total are correct. | pp. 3 and 8--9 are exact, but the unresolved logical-output dimensionality should be recorded separately. | **pass with anomaly** |
| `wang-supervised-objectives` | Correct as printed. | pp. 3 and 9 are exact; Eq. (S7)'s `d`-output form conflicts with the scalar/Algorithm-1 wording. | **revise accompanying boundary** |
| `wang-alphaqubit-style-decoder` | Correct. | pp. 9--12, Fig. S1, Eqs. (S8)--(S23) and Algorithm 2 are exact. | **pass** |
| `wang-alphaqubit-flicker-features` | Correct. | Supplemental p. 10 is exact. | **pass** |
| `wang-alphaqubit-model-size` | Correct. | Table II on p. 12 is exact. | **pass** |
| `wang-logical-accuracy-metric` | Correct and load-bearing. | Main p. 4 and Supplemental p. 12 are exact. | **pass** |
| `wang-decoder-comparators` | Comparator identities are correct; the mismatch boundary is correct. | Page 4 establishes the arms and final-loss side information, but the engineered-feature and decision-schedule statements require pp. 8--12. | **revise locator** |
| `wang-delayed-erasure-approximation` | Correct. | Supplemental p. 12 is exact. | **pass** |
| `wang-logical-accuracy-result` | Correctly reports the plotted ordering without promoting it to a history ablation. | Fig. 3 on p. 4 is exact; population and uncertainty absence is also separately typed as a gap. | **pass** |
| `wang-loss-identification-result` | Exact values are correct. | Main p. 4 is exact. | **pass** |
| `wang-threshold-result` | Correct; hardware policy remains prospective. | Main pp. 4--5 and Fig. 4 are exact. | **pass** |
| `wang-history-length-diagnostic` | Correct and properly limited to a conditional association. | Main p. 5 and Fig. 5 are exact. | **pass** |
| `wang-inference-latency` | Exact point estimates and limitations are correct. | Main p. 5 is exact. | **pass** |
| `wang-reinitialization-status` | Correctly labels intervention claims as prospective. | Main pp. 4--6 are exact. | **pass** |
| `wang-generalization-status` | Future-work claim and one-setting boundary are correct. | Page 6 locates future work; the body statement about one distance and one rate tuple also requires pp. 4 and 12. | **revise locator** |
| eight `wang-gap-*` records | Hardware, matched history, population/uncertainty, wrong-model, transfer, unconditional metric, closed-loop and reproducibility absences are all source-locally correct. | Their page spans are adequate. The reproducibility gap should additionally name the unspecified loss-generation mapping and inconsistent STGNN logical-output specification. | **pass; strengthen reproducibility gap** |

### Relation review

Seven relations name a source concept present in the referenced claim and have the correct endpoint.
The first relation is mechanically valid but semantically under-specified:

```text
object_id = "wang-persistent-loss-generator"
object_type = "model"
object_label = "data qubit"
```

`data qubit` is an entity, not the persistent-loss model named by the object ID. Replace it with an
exact claim phrase that identifies persistence, or revise the claim to contain a concise label such
as `episode-persistent data-qubit loss model` and use that exact phrase. This is a semantic relation
failure that the current occurrence-only schema cannot detect.

## Operation-replay check

| input | transformation | source-critical assumption | output | status |
|---|---|---|---|---|
| Distance-5 circuit and printed rates | Sample Pauli, measurement and loss events through `T` rounds and final readout | Data loss persists; ancilla loss resets | Synthetic measurements, detectors and labels | **semantic model closed; executable Stim loss transformation and multi-loss behavior missing** |
| One data loss | Remove later participation and measure shortened checks | The printed measurement order produces the stated stochastic check relations | Persistent local detector flicker | **closed as the source's mechanism; not independently numerically replayable** |
| Complete ordered episode | STGNN embedding, local graph messages, temporal mixer and spatial attention | Full-window non-causal access is allowed | Loss logits plus logical output | **architecture mostly closed; exact STGNN logical-output dimension/label bridge contradicted internally** |
| Sequential record plus flicker counts | Recurrent AlphaQubit-style update and convolutional readout | Engineered recent-window counts are available | Per-round loss and distance-many logical logits | **closed as printed architecture** |
| Synthetic labels | Weighted two-task cross-entropy | Validation chooses task weights | Trained learned decoders | **partial; data volume, split, optimizer, epochs, seeds and checkpoints missing** |
| Final loss locations and detector graph | Average single-loss edges over possible times and neglect multi-loss interactions | Approximate graph is an adequate baseline | Delayed-erasure MWPM decision | **closed as an explicitly approximate baseline** |
| Decoder outputs | Remove loss-intersecting logical lines and average remaining predictions | Survivor-conditioned preservation is the target metric | Figure 3 curves | **closed for the printed metric; population and uncertainty missing** |
| Final loss logits and occurrence times | Threshold and group false negatives | Longer persistence provides more observations | Figures 4--5 diagnostics | **closed for point estimates and association; no causal history ablation** |

## Required revisions before pass

### Audit packet

1. Replace `complete for the declared generator` with a bounded semantic reconstruction and record
   that the executable Stim loss transformation, overlapping multi-loss behavior, dataset generation
   protocol and code are absent.
2. Change the STGNN operation-replay row from `complete for the printed forward map` to partial, or
   explicitly bound completeness to the printed feature modules while recording the unresolved
   scalar-versus-`d` logical output and label mapping across main p. 3, Supplemental p. 9,
   Eq. (S7), Algorithm 1 and Figure 3.
3. Add that output-shape inconsistency to `Source-local anomalies and reporting boundaries` and
   reconcile it with the source note's `operation_replay_status = "complete"` before admission.
4. Preserve the present D1/D2/R1/T1, survivor-conditioning, non-causal-decision, reinitialization and
   latency kill conditions; they are correct.

### Draft source note

1. Add p. 3 to `wang-selection-scope`, p. 10 to `wang-qec-record`, pp. 8--12 to
   `wang-decoder-comparators`, and pp. 4 and 12 to the experimental-scope body of
   `wang-generalization-status`.
2. Extend `wang-gap-reproducibility` to include the unspecified executable loss-generation mapping
   and the inconsistent STGNN logical-output/label specification.
3. Replace relation label `data qubit` with an exact, source-faithful phrase that identifies the
   episode-persistent loss model rather than only the affected entity.
4. Keep the existing source-local gaps for hardware, matched history, population/uncertainty,
   wrong-model robustness, transfer, unconditional logical performance and closed-loop
   intervention. They are faithful.

## Disposition

- `read_status`: complete
- official-object and local-object identity: pass
- persistent-loss/flicker scientific reconstruction: pass at the declared semantic level; numerical
  generator replay incomplete
- Sections 4--5 evidence disposition: pass
- hardware, matched-history, population/uncertainty, wrong-model and transfer boundaries: pass
- source-note semantic fidelity: revise one replay boundary, three locators and one relation label
- audit semantic fidelity: revise two operation-replay claims and add the STGNN output anomaly
- source/audit hash integrity: pass
- current machine schema: pass, but it does not detect the generic relation label or semantic replay
  overstatement
- manifest action: none

After these revisions, the source is suitable as a selective overview example of a persistent
simulated loss state imprinting diagnostically useful multicycle QEC records. It cannot support a
quantum-hardware observation, microscopic attribution from data, a matched memory-aware decoder
benefit, a population-level or uncertainty-qualified comparison, wrong-memory-model robustness,
frozen cross-distance/device/code transfer, unconditional logical preservation, or demonstrated
reinitialization benefit.

## Revision verification

### Final decision

**PASS for prospective admission review.** Every scientific, locator and relation revision required
above is closed. The fixed PDF is unchanged, the revised audit hash is bound exactly by the revised
source note, artifact-verifying parsing succeeds, and the directory audit validates the note. No
manifest action was taken.

`operation_replay_status = "complete"` is accepted here only in the bounded sense that the replay
audit itself is complete: it follows every supported source transformation and explicitly types the
two unresolved transformations as source-local gaps. It must not be read as a claim that executable
multi-loss generation or the exact STGNN logical-head/label map can be numerically replayed. The
audit now labels the former a semantic-only chain and the latter partial, and downstream use does not
depend on promoting either missing transformation.

### Final hashes and schema result

- fixed arXiv v2 PDF:
  `098dc3506421d58a23a8a2cee15161d3de08a41228299470279319d9149c84dc`;
- revised audit:
  `77af581c269b4e80e9523271d54f4a229f40e58db14b5f6e316fdd48290b4270`;
- revised source note:
  `ccd1e0eab500c7fc5ae0645418e80f2f4593b60dc48eb4e16e9ce6baeb06c967`.

The note declares the same PDF and audit hashes as the actual files. Direct
`parse_note(..., verify_artifact=True)` succeeds with 31 evidence records: 21 `paper_fact`, ten
`literature_gap`, and eight relations. The full draft-directory audit lists the Wang AI-loss note as
artifact-verified with 21 paper facts. Whitespace checks for the revised audit and note are clean.

### Required-revision closure

| prior blocker | revised evidence | result |
|---|---|---|
| Generator replay was called complete without an executable loss mapping | The audit now says `complete only as a semantic model chain` and names the absent Stim loss/removal transformation, overlapping multi-loss generation, data protocol and code. | **closed** |
| STGNN forward map was called complete despite incompatible output shapes | The audit now marks it partial and records the binary scalar, one `L in R^2`, `d`-output Eq. (S7), and `d`-line Fig. 3 conflict. | **closed** |
| Missing source-local records for those replay failures | New `wang-gap-loss-generator` and `wang-gap-stgnn-logical-output` records preserve both absences with exact page spans. | **closed** |
| `wang-selection-scope` did not locate simulated evaluation | Locator now includes Training Process on p. 3. | **closed** |
| `wang-qec-record` omitted the no-side-channel page | Locator now includes Supplemental p. 10. | **closed** |
| `wang-decoder-comparators` did not locate feature/schedule differences | Locator now includes Supplemental pp. 8--12. | **closed** |
| `wang-generalization-status` did not locate the one-setting boundary | Locator now includes Fig. 3 on p. 4 and the error model on p. 12 as well as the p. 6 future-work statement. | **closed** |
| Persistent-loss relation label named only `data qubit` | Claim and relation now use the exact phrase `episode-persistent data-qubit loss model`. | **closed** |
| Revised audit binding | Source-note `audit_packet_sha256` exactly equals the revised audit SHA-256. | **closed** |

### Final disposition

- scientific revision closure: **pass**;
- source-note semantic fidelity: **pass with explicit source-local replay gaps**;
- audit semantic fidelity: **pass**;
- locator and relation fidelity: **pass**;
- PDF/audit/note hash integrity: **pass**;
- artifact-verifying parser and directory schema audit: **pass**;
- manifest action: none.

The final admissible use remains unchanged: a synthetic, episode-persistent loss mechanism that
imprints diagnostically usable multicycle syndrome structure, bounded by an unmatched decoder
comparison, survivor-conditioned logical metric, absent population uncertainty, and no hardware,
wrong-model, transfer or closed-loop intervention demonstration.

# Claim audit — Wang et al. on AI decoding of persistent qubit loss

## Fixed source and reading scope

- Fixed artifact: `outputs/overview/literature/coverage_validation/wang_loss/2604.14269v2.pdf`
- Identity: arXiv:2604.14269v2, *AI-Enabled Decoding of Qubit Loss for Quantum
  Error-Correcting Codes*, Yuqing Wang, Xiaotian Nie, Jiale Dai, Zhongyi Ni, Tao Zhang, Hui Zhai
  and Linghui Chen. The arXiv version line is 25 May 2026 and the PDF is dated 26 May 2026.
- Publication status: preprint. No journal DOI is identified in the fixed source.
- Artifact verification: PDF 1.7, 12 artifact pages, 763,440 bytes, SHA-256
  `098dc3506421d58a23a8a2cee15161d3de08a41228299470279319d9149c84dc`.
- Reading scope: all 12 artifact pages, including Figs. 1–5, references, the embedded five-page
  Supplemental Material, Fig. S1, Tables I–II, Eqs. (S1)–(S23) and Algorithms 1–2.
- Visual verification: rendered artifact pages 1–12 were inspected. Load-bearing checks covered the
  persistent-loss mechanism and input record on pp. 1–3; the metric and decoder comparison in Fig. 3
  on p. 4; diagnostic and latency results in Figs. 4–5 on p. 5; the full-window non-causal STGNN
  statement and architecture on pp. 8–9; the recurrent AlphaQubit-style inputs and flicker-count
  features on pp. 10–11; and the noise model, survivor-conditioned metric and delayed-erasure graph
  approximation on p. 12.
- External supplementary material: none was found on the fixed arXiv record. The Supplemental
  Material is embedded on artifact pp. 8–12.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| L1 — persistent-loss history is diagnostically usable | Mechanism and Fig. 1, PDF pp. 1–2; Figs. 4–5, pp. 4–5 | In the declared simulator, data-qubit loss persists across rounds and creates repeated local stabilizer flicker. After a ten-round window, first-round losses have a reported miss rate below 10%, while final-round losses have a miss rate above 85%; overall STGNN recall and precision at threshold 0.5 are 0.654 and 0.845. | No matched removal, shuffling or truncation of history is performed within one frozen architecture. Loss time also changes persistence duration and signal opportunity, so Fig. 5 does not isolate a history-access treatment. | closed as synthetic capability evidence, not as a causal history ablation or device observation |
| D1 — hardware memory-conditioned decoder benefit | Training Process, p. 3; Results and Conclusion, pp. 4–6; Supplemental error model, p. 12 | Stim-generated surface-code records are decoded by STGNN, modified AlphaQubit, standard MWPM and delayed-erasure MWPM. Reinitialization and atom-array use are presented as motivations and future operational possibilities. | No hardware syndrome record, hardware loss label, on-device comparison, feedback loop or measured reinitialization benefit is reported. | missing |
| D2 — population-level matched memory-decoder comparison | Fig. 3 and surrounding text, p. 4; architecture descriptions, pp. 2–3 and 8–11 | For one synthetic distance-5 setting, the two AI decoders have nearly coincident survivor-conditioned logical-accuracy curves and outperform the two MWPM baselines over `T=3` to `10`. | The arms do not hold architecture, parameter count, features, information access or decision timing fixed. No no-history/window/order/state ablation, sample count, population definition, uncertainty interval or statistical test is supplied. | missing; an unmatched single-setting synthetic comparison only |
| R1 — robustness under a wrong memory model | Supplemental error model, p. 12; Conclusion, p. 6 | The study evaluates one fixed mixture of persistent data loss, round-reset ancilla loss, Pauli noise and measurement noise at the printed rates. | No loss-rate shift, wrong persistence lifetime, nonpersistent alternative, mixed unmodelled mechanism, stale calibration, held-out noise family or frozen-decoder mismatch test is reported. “Robust” is not tied to such an evaluation. | missing |
| T1 — frozen-model transfer | Fig. 3, p. 4; Tables I–II, pp. 9 and 12; Conclusion, p. 6 | Both learned decoders are instantiated for a rotated surface-code memory task at distance 5. Generalization-capable foundation models and qLDPC decoding are future directions. | No frozen model is evaluated across code distance, code family, device, calibrated operating regime or independent loss mechanism. | missing |
| C1 — calibration and computational cost | Inference Time, p. 5; Tables I–II, pp. 9 and 12 | The source reports about 0.410 ms per recurrent AlphaQubit-style update, 4.10 ms cumulatively over ten rounds, and 0.595 ms for one STGNN pass over the complete ten-round window. The models contain about 12.7M and 8M parameters, respectively. | Hardware platform, batch size, numerical precision, warm-up, repetition count, dispersion, training cost and end-to-end feedback latency are not reported. The compared architectures expose different latency-to-decision semantics, and neither is optimized. | partial and preliminary; not an equal operational-cost comparison |
| F1 — representation–interface–computation framework residual | Mechanism, pp. 1–3; Supplemental architectures and error model, pp. 8–12 | A persistent, absorbing data-loss state generates a multicycle ordered measurement/detector record; learned decoders map that record to logical and loss outputs, while MWPM consumes detector-graph abstractions. | The paper does not require a fifth scientific category, but it does require the comparison to distinguish the generator's physical loss state from the learned decoder's implicit hidden representation. | no framework residual; retain two representation levels explicitly |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| A rotated distance-5 surface-code memory circuit | Apply `T` QEC rounds, a final destructive readout and the printed circuit-level noise model | Idle and CNOT depolarizing error probabilities, measurement-bit flips and per-round loss probabilities are fixed at the printed values; data loss persists to the end while ancilla loss resets each round | Conceptually declared synthetic measurements, detector events, logical labels and spatiotemporal loss labels | Training Process, PDF p. 3; Supplemental error model, p. 12 | complete only as a semantic model chain; executable Stim loss/removal transformation, overlapping multi-loss record generation, data volume, splits, seeds and code are not specified |
| Loss of a data qubit | Remove its degree of freedom from later gate operations; continue measuring neighboring shortened checks | The formerly commuting neighboring X- and Z-type checks become effectively noncommuting and yield stochastic outcomes while the qubit remains absent | A persistent, spatially localized detector-flicker signature across rounds | Mechanism and Fig. 1, pp. 1–2 | complete as the source's simulated mechanism; it is not a hardware observation or a formal test of quantum non-Markovianity |
| `T+1` rounds of measurements, detectors and node/task metadata | Embed the complete ordered record as one spatiotemporal tensor; alternate local Tanner-graph messages, gated Conv1D/MHA temporal mixing and topology-biased global spatial attention | The full episode may be available before a decision and non-causal feature extraction across the window is operationally admissible | Loss logits plus a logical output whose dimensionality is internally inconsistent | Architecture, pp. 2–3; Supplemental pp. 8–9, Eqs. (S1)–(S7), Algorithm 1 and Table I | partial: feature modules are printed, but main-text scalar labeling, Algorithm 1's one `L in R^2`, Eq. (S7)'s `d` outputs and Fig. 3's `d` logical lines do not define one replayable logical-head/label map |
| Round-sequential measurements and detectors | Add learned metadata and recent-window flicker counts, update recurrent ancilla states through SyndromeTransformer blocks and map them to data-qubit features | Recent detection-event counts for windows such as 2, 3 and 4 rounds are informative engineered features | Modified AlphaQubit logical-line logits and per-round loss logits | Supplemental pp. 9–12, Eqs. (S8)–(S23), Fig. S1, Algorithm 2 and Table II | complete for the printed forward map; this is a modified, not stock, AlphaQubit comparator |
| Logical and loss labels | Optimize a weighted sum of two-class cross-entropies, with task weights tuned on validation data | Supervised synthetic labels capture the target generator and validation tuning selects adequate task weights | An approximately 8M-parameter STGNN and 12.7M-parameter AlphaQubit-style model | Training Process, p. 3; Supplemental Eq. (S7), p. 9, Tables I–II, pp. 9 and 12 | partial: model objectives are printed, but training-set size, split, optimizer, learning rate, epochs, seeds and run-to-run variation are not |
| Standard detector graph and final-round exact spatial loss locations | Construct delayed-erasure MWPM edges for loss-induced in-round and cross-round flips; average over possible loss times and neglect interactions among multiple lost data qubits | Exact final spatial locations are available, but loss times may be delayed or unknown and the single-loss graph can approximate multiple-loss records | A privileged but approximate delayed-erasure MWPM baseline | Fig. 3 comparison, p. 4; Supplemental decoding-graph construction, p. 12 | complete for the stated approximation; it is not an exact loss-aware optimum |
| Decoder outputs for `T=3` to `10` | Exclude any logical line whose support contains a lost data qubit, then average prediction success over the remaining loss-free lines | Performance within the surviving code space is the desired logical metric | Fig. 3 survivor-conditioned logical-accuracy curves at distance 5 | Logical Accuracy and Fig. 3, p. 4; Supplemental Metrics, p. 12 | complete for the defined metric; it is not the unconditional logical survival probability of the full encoded task |
| Final-round loss probabilities after ten rounds | Threshold the loss head at 0.5 and compute recall and precision; sweep the threshold for Fig. 4 | A binary per-qubit decision summarizes diagnostic utility and may later guide a hardware policy | STGNN recall 0.654 and precision 0.845; modified AlphaQubit recall 0.652 and precision 0.856; threshold-dependent precision/recall/F1 curves | Qubit Loss and Fig. 4, pp. 4–5 | complete for the reported point estimates; sample counts and uncertainty are absent |
| Loss-event ground-truth round | Group final false negatives by loss time and compute miss rate for each occurrence round | Earlier persistent losses offer a longer observation window for repeated flicker | Fig. 5: below-10% miss rate for first-round losses and above-85% miss rate for final-round losses | Fig. 5 and surrounding text, p. 5 | complete as a conditional diagnostic; not a matched manipulation of decoder history |
| One ten-round input window | Time recurrent per-round updates and one full-window parallel pass | Cumulative recurrent update time and delayed full-window inference are meaningfully comparable despite distinct decision schedules | Reported 4.10 ms cumulative modified-AlphaQubit time and 0.595 ms STGNN full-window time | Inference Time, p. 5 | partial: platform and benchmark protocol are absent, and neither model is optimized |

## Project application

### What the source changes

The paper adds a direct synthetic example in which a persistent loss state leaves a multicycle QEC
record that learned decoders can use for joint loss identification and logical prediction. Fig. 5 is
particularly useful for a bounded claim: under this generator, diagnostic success depends strongly
on how long the loss signature has been observable. That supports the overview's account of how a
continuing carrier can make an ordered record informative.

It does **not** upgrade the field-level decoder-benefit judgment. The logical comparison changes the
entire decoder family rather than changing only memory access. Standard MWPM, an approximate
delayed-erasure graph, a modified recurrent AlphaQubit and a full-window STGNN differ in
architecture, engineered features, parameter count, physical side information and decision timing.
The study therefore cannot assign the Fig. 3 gap specifically to temporal-history access.

### Observation, attribution, QEC effect, intervention and transfer

- **Temporal structure:** the source generates persistent loss and its repeated detector flicker in
  simulation. This is not observation on a physical processor.
- **Physical attribution:** the simulator supplies exact loss labels, so the study tests recovery of a
  known simulated cause. It does not infer a microscopic cause from ambiguous hardware data.
- **QEC performance effect:** Fig. 3 evaluates decoders in a lossy memory task, but the paper does not
  include an otherwise-matched no-loss or no-persistence arm that isolates the effect of the temporal
  mechanism itself. Its logical metric also conditions away logical lines intersected by loss.
- **Memory-aware benefit:** learned decoders outperform the printed MWPM baselines within the one
  synthetic setting, but no matched history ablation shows that history access, rather than model
  class, features, training or approximation quality, causes the benefit.
- **Intervention benefit:** reinitialization policies and possible benefits from treating false
  positives as lossy qubits are discussed, not simulated or implemented.
- **Transfer:** no code-, distance-, device- or model-shift evaluation is reported.

### Representation–interface–computation mapping

- **Memory-bearing representation:** an absorbing data-qubit loss state sampled per qubit and round;
  once lost, a data qubit remains absent through the end of the episode. Ancilla loss is instead
  reset each round.
- **QEC-facing interface:** ordered stabilizer measurements and detector differences over `T+1`
  rounds, plus code/task/node metadata. The AlphaQubit-style comparator also receives engineered
  recent-window flicker counts; the delayed-erasure MWPM receives exact final spatial loss locations.
- **Computation:** a discriminative full-window STGNN, a modified recurrent AlphaQubit-style neural
  decoder, standard MWPM and an approximate delayed-erasure MWPM graph.
- **Returned objects:** survivor-conditioned logical predictions and per-data-qubit loss logits;
  precision, recall, F1 and conditional miss rate summarize the latter.
- **Demonstrated reach:** Stim-generated rotated surface-code memory records at distance 5, up to ten
  QEC rounds, under one fixed set of noise and loss rates.

The paper fits the four-way comparison frame if the matrix keeps **generator representation**
separate from **decoder-internal representation**. Its learned hidden states are not themselves the
physical carrier of temporal dependence. This is an interface-first discriminative approach and is
better used as a bounded Section 4/5 example than promoted to a replacement for a concrete Section
3 physical-to-QEC approach bundle.

### Robustness, transfer and cost interpretation

- Only one printed noise/loss parameter tuple, one code distance and one code family are evaluated.
  The paper's “robust” and “scalable” language is not supported by a wrong-model, distance-scaling or
  held-out transfer study.
- Modified AlphaQubit is not a frozen external baseline: it receives a new loss head, additional
  data-grid mixing and explicit flicker-count features, and it is trained on the same simulated task.
- The delayed-erasure comparator has exact final spatial loss positions but averages over unknown
  loss times and neglects multiple-loss interactions. Outperforming it does not establish superiority
  to exact loss-aware decoding.
- The STGNN latency number is a delayed full-window decision, whereas AlphaQubit can update online.
  Without the execution platform and benchmark protocol, the reported times are preliminary
  implementation measurements rather than portable cost estimates.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- Nayak et al. provide an explicit latent-field-to-DEM decoder route with a more direct conditioned
  versus unconditioned model contrast, but their proposed-method results are event-selected and lack
  a population average and uncertainty.
- Remm et al. provide hardware syndrome-correlation and signature-inversion evidence, but their
  correlated-MWPM update does not yield a statistically significant decoder improvement and does not
  target persistent loss.
- AlphaQubit provides held-out device-run decoding in its own source, but Wang et al.'s modified
  AlphaQubit is retrained, feature-augmented and evaluated only on the new synthetic loss generator.
- Hockings et al. show a population-level matched comparison for static Pauli-prior calibration, not
  temporal-memory-conditioned decoding.

Wang et al. are therefore useful evidence that a persistent carrier can imprint diagnostically usable
ordered-record structure in a declared simulator. They do not close the stronger hardware, matched
benefit, wrong-model robustness or transfer rows.

### Kill conditions

- Kill a hardware-result claim: all reported QEC records and labels are generated in simulation.
- Kill a direct observation claim: loss-induced flicker is imposed by the model, not measured on an
  atom-array or other quantum processor.
- Kill a strict non-Markovianity claim: the source describes persistent loss and temporal
  correlation; it does not apply a formal quantum non-Markovianity criterion.
- Kill a matched history-benefit claim: no frozen decoder is evaluated with history removed,
  shuffled, shortened or otherwise selectively withheld.
- Kill a claim that Fig. 3 compares only information access: architecture, features, parameter count,
  side information, graph approximation and decision schedule also vary.
- Kill a population-level or statistically quantified benefit claim: no test-population size,
  uncertainty interval, random-seed variation or statistical test is reported.
- Kill an unconditional logical-preservation claim: logical lines containing a lost qubit are
  excluded from the accuracy calculation.
- Kill an exact delayed-erasure-optimum claim: the MWPM graph averages over possible loss times and
  neglects interactions among multiple lost data qubits.
- Kill a closed-loop reinitialization-benefit claim: reinitialization is not part of the evaluated
  task, and the suggested benefit of replacing false-positive qubits is prospective.
- Kill a “more than 90% overall recall after ten rounds” claim: overall STGNN recall is 65.4%; above
  90% applies to losses occurring in the first round and observed through the remaining window.
- Kill a real-time per-round STGNN claim: the STGNN uses non-causal feature extraction over the
  complete window before producing the compared decision.
- Kill a robustness or transfer claim: one distance-5 synthetic setting is used, with no wrong-model
  or frozen held-out evaluation.
- Kill a platform-independent speedup claim: timing hardware, batch size, precision, repetitions and
  uncertainty are unreported, and the models have different latency semantics.

## Source-local anomalies and reporting boundaries

- The abstract's “more than 90% of loss locations” statement is narrower in Fig. 5: it applies to
  losses occurring in the first round and receiving the longest observation window. The overall
  ten-round STGNN recall reported in the main text is 0.654.
- The source calls the assessment “statistically robust,” but Fig. 3 has no error bars and the paper
  reports no sample counts, train/validation/test split sizes, confidence intervals, repeated seeds or
  statistical tests.
- “Robust and scalable” is an architectural characterization in the abstract, not an evaluated
  robustness or scaling result: all reported accuracy data are for distance 5 and one noise setting.
- The logical-accuracy definition is explicitly survivor-conditioned. It may be useful for recovery
  within remaining support, but it cannot be substituted for an unconditional logical-failure metric.
- The false-positive discussion argues that reinitializing high-error qubits may reduce entropy and
  improve long-term stability. No such control policy or downstream QEC result is evaluated.
- The two latency numbers compare cumulative recurrent updates with a single delayed full-window
  pass. The paper itself notes the different operational paradigms; it does not report an equal
  time-to-decision benchmark.
- The Supplemental Material refers twice to `Algorithm ??` even though Algorithms 1 and 2 are
  present. This is a document cross-reference defect, not missing algorithm content.
- The source states that Stim generates the data and describes episode-persistent loss semantically,
  but it does not specify an executable loss/removal circuit transformation or the record generation
  for overlapping multiple losses. The single-loss delayed-erasure graph explicitly neglects
  multi-loss interactions and cannot substitute for the missing generator specification.
- The printed STGNN logical-output definition is inconsistent: main p. 3 describes a binary scalar,
  Supplemental p. 9 and Algorithm 1 give one logical output or `L in R^2`, Eq. (S7) sums over `d`
  outputs `L_k`, and Fig. 3 averages `d` logical lines. The feature modules are reconstructible, but
  the exact STGNN logical-head/label bridge is not.
- No code/data availability statement, repository, training-data volume or complete optimization
  protocol was found in the fixed artifact.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted as a fixed artifact, audit and candidate source-only note; corpus
  admission remains pending independent review
- L1: closed only for synthetic capability and history-length association under a persistent-loss
  generator; causal history access is not isolated
- D1: missing
- D2: missing; unmatched single-setting synthetic comparison only
- R1: missing
- T1: missing
- C1: partial and preliminary
- F1: no residual, provided generator state and learned hidden representation remain distinct
- overview effect: retain as a bounded persistent-loss example for Sections 4–5; do not use it to
  upgrade hardware benefit, population-level matched benefit, wrong-model robustness or transfer

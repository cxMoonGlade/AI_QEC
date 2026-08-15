+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2604.14269"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2604.14269v2"
source_artifact = "outputs/overview/literature/coverage_validation/wang_loss/2604.14269v2.pdf"
source_sha256 = "098dc3506421d58a23a8a2cee15161d3de08a41228299470279319d9149c84dc"
title = "AI-Enabled Decoding of Qubit Loss for Quantum Error-Correcting Codes"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/WANG_AI_LOSS_DECODER_2604_14269_AUDIT_2026-08-05.md"
audit_packet_sha256 = "77af581c269b4e80e9523271d54f4a229f40e58db14b5f6e316fdd48290b4270"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_qadapt"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

[[relations]]
predicate = "defines"
object_id = "wang-persistent-loss-generator"
object_type = "model"
object_label = "episode-persistent data-qubit loss model"
fact_id = "wang-persistent-loss-model"

[[relations]]
predicate = "uses"
object_id = "wang-stgnn-decoder"
object_type = "method"
object_label = "STGNN"
fact_id = "wang-stgnn-architecture"

[[relations]]
predicate = "uses"
object_id = "wang-modified-alphaqubit"
object_type = "method"
object_label = "modified AlphaQubit-style comparator"
fact_id = "wang-alphaqubit-style-decoder"

[[relations]]
predicate = "uses"
object_id = "wang-delayed-erasure-mwpm"
object_type = "method"
object_label = "delayed-erasure MWPM graph"
fact_id = "wang-delayed-erasure-approximation"

[[relations]]
predicate = "supports"
object_id = "wang-loss-history-diagnostic"
object_type = "observable"
object_label = "miss rate"
fact_id = "wang-history-length-diagnostic"

[[relations]]
predicate = "supports"
object_id = "wang-synthetic-decoder-comparison"
object_type = "observable"
object_label = "logical-accuracy curves"
fact_id = "wang-logical-accuracy-result"

[[relations]]
predicate = "limits"
object_id = "wang-survivor-conditioned-metric"
object_type = "limitation"
object_label = "excluding every logical operator"
fact_id = "wang-logical-accuracy-metric"

[[relations]]
predicate = "limits"
object_id = "wang-full-window-decision"
object_type = "limitation"
object_label = "non-causal feature extraction across the full decoding window"
fact_id = "wang-stgnn-full-window"
+++
# Full-text review — Wang et al., "AI-Enabled Decoding of Qubit Loss for Quantum Error-Correcting Codes"

## Source identity [paper_fact]
Fact ID: wang-source-identity
Source locator: PDF p. 1, title page and arXiv version line
PDF page: 1
Claim: The fixed source is the 12-artifact-page arXiv:2604.14269v2 preprint by Yuqing Wang and six coauthors, with an arXiv version line of 25 May 2026 and a PDF date of 26 May 2026.

The artifact contains seven pages of article and references followed by five pages of embedded
Supplemental Material. The source identifies no journal DOI or separate supplementary file.

## Selection scope [paper_fact]
Fact ID: wang-selection-scope
Source locator: PDF pp. 1–3, Abstract, final Introduction paragraph and Training Process
PDF page: 2
Claim: The source develops a dual-head neural decoder that predicts logical outcomes and data-qubit loss coordinates directly from multiround rotated-surface-code syndrome records.

The evaluated data are generated in simulation. Reinitialization and atom-array operation motivate
the study but are not part of the reported decoder task.

## Persistent loss model [paper_fact]
Fact ID: wang-persistent-loss-model
Source locator: PDF pp. 3 and 12, Training Process and Supplemental Circuit-Level Noise Model sections
PDF page: 12
Claim: The episode-persistent data-qubit loss model assigns every data qubit a loss probability of 0.01 per round and keeps it absent through the end of the distance-5 simulated episode once lost, whereas lost ancillas are reset each round.

The supplement also prints idle depolarizing probability 0.01 per round, correlated CNOT
depolarizing probability 0.01 after each CNOT and measurement-bit-flip probability 0.01.

## Loss-induced flicker mechanism [paper_fact]
Fact ID: wang-loss-flicker-mechanism
Source locator: PDF pp. 1–2, Introduction mechanism and Fig. 1 caption
PDF page: 2
Claim: The source attributes persistent local stabilizer flicker to removal of the lost data-qubit degree of freedom, which can leave formerly commuting neighboring X- and Z-type checks effectively noncommuting.

The affected outcomes then collapse stochastically while the qubit remains absent. The source calls
the resulting multiround syndrome structure temporally correlated but does not test a formal quantum
non-Markovianity criterion.

## Ordered QEC record [paper_fact]
Fact ID: wang-qec-record
Source locator: PDF pp. 2, 8 and 10, Architecture of the AI Decoder and Supplemental Input and Embedding Stage sections
PDF page: 8
Claim: The learned decoders receive ordered stabilizer measurements and detector differences over `T+1` rounds together with node, check, memory-task and position metadata.

The detector is the XOR difference between consecutive measurements. The modified AlphaQubit-style
decoder explicitly states that no loss flags, leakage probabilities or other side-channel information
are provided as neural inputs.

## Full-window STGNN input [paper_fact]
Fact ID: wang-stgnn-full-window
Source locator: PDF pp. 2 and 8, Architecture of the AI Decoder and Supplemental STGNN opening paragraphs
PDF page: 8
Claim: The STGNN processes the complete `T+1`-round episode simultaneously and permits non-causal feature extraction across the full decoding window rather than issuing the compared result from a round-by-round recurrent state.

This makes its time-to-decision different from that of a decoder capable of incremental recurrent
updates.

## STGNN architecture [paper_fact]
Fact ID: wang-stgnn-architecture
Source locator: PDF pp. 3 and 8–9, Fig. 2, Supplemental Eqs. (S1)–(S7), Algorithm 1 and Table I
PDF page: 9
Claim: The STGNN interleaves local Tanner-graph message passing, a gated temporal mixer combining Conv1D and multi-head attention, and topology-biased global spatial attention before applying separate logical and loss heads.

Table I gives distance 5, hidden dimension 256, six interleaved blocks, eight temporal-attention heads
and approximately eight million parameters.

The printed logical-output dimensionality is not internally consistent: main p. 3 describes a
binary scalar label; Supplemental p. 9 and Algorithm 1 give one logical output or `L in R^2`; Eq.
(S7) sums over `d` outputs `L_k`; and Fig. 3 averages `d` logical lines.

## Supervised objectives [paper_fact]
Fact ID: wang-supervised-objectives
Source locator: PDF pp. 3 and 9, Training Process and Supplemental Loss Function, Eq. (S7)
PDF page: 9
Claim: Training uses synthetic syndrome histories labelled by the final logical value and spatiotemporal loss coordinates and minimizes a validation-tuned weighted sum of two-class cross-entropies for the two tasks.

The source does not print the selected weights or the number and split of training, validation and
test samples.

## Modified AlphaQubit-style decoder [paper_fact]
Fact ID: wang-alphaqubit-style-decoder
Source locator: PDF pp. 9–12, Supplemental AlphaQubit-style decoder, Fig. S1, Eqs. (S8)–(S23) and Algorithm 2
PDF page: 11
Claim: The modified AlphaQubit-style comparator processes syndrome rounds sequentially, maintains recurrent hidden states on ancillas and uses a convolutional readout to produce per-data-qubit loss logits and final logical-line logits.

Relative to the cited original design, this implementation adds a loss head and additional data-grid
convolutional mixing before the task heads.

## Engineered flicker-count features [paper_fact]
Fact ID: wang-alphaqubit-flicker-features
Source locator: PDF p. 10, Supplemental Inputs, Flicker-count features paragraph
PDF page: 10
Claim: The modified AlphaQubit-style input is augmented with categorical counts of recent detection events in short windows such as 2, 3 and 4 rounds to distinguish sustained flicker from an isolated flip.

This engineered temporal input is not shared with the STGNN or MWPM arms as an otherwise-matched
feature treatment.

## AlphaQubit-style model size [paper_fact]
Fact ID: wang-alphaqubit-model-size
Source locator: PDF p. 12, Supplemental Table II
PDF page: 12
Claim: The modified AlphaQubit-style decoder uses hidden dimension 256, 16 attention heads, three SyndromeTransformer blocks and approximately 12.7 million parameters at distance 5.

It therefore differs from the approximately eight-million-parameter STGNN in both architecture and
model size.

## Logical-accuracy metric [paper_fact]
Fact ID: wang-logical-accuracy-metric
Source locator: PDF pp. 4 and 12, Logical Accuracy and Supplemental Metrics sections
PDF page: 12
Claim: Logical accuracy is averaged over `d` equivalent logical lines after excluding every logical operator whose support contains a data qubit lost during the QEC episode.

The metric describes prediction within the surviving code support and is not the unconditional
logical survival probability of the full encoded task.

## Decoder comparators [paper_fact]
Fact ID: wang-decoder-comparators
Source locator: PDF pp. 4 and 8–12, Logical Accuracy comparator paragraph and Supplemental decoder specifications
PDF page: 4
Claim: Figure 3 compares the STGNN with standard MWPM, a delayed-erasure MWPM supplied exact final spatial loss locations and a modified AlphaQubit-style neural decoder.

The four arms differ in algorithm, inputs, engineered features, parameterization and operational
decision schedule; the paper does not include a within-architecture history-access ablation.

## Delayed-erasure approximation [paper_fact]
Fact ID: wang-delayed-erasure-approximation
Source locator: PDF p. 12, Supplemental Decoding Graph Construction of Loss Events section
PDF page: 12
Claim: The delayed-erasure MWPM graph averages over all possible loss times and neglects interactions among multiple lost data qubits while incorporating the supplied final spatial loss positions.

It is consequently a privileged-information baseline but not an exact optimum for the simulated
multiple-loss process.

## Logical-accuracy result [paper_fact]
Fact ID: wang-logical-accuracy-result
Source locator: PDF p. 4, Fig. 3 and surrounding paragraphs
PDF page: 4
Claim: In the one reported distance-5 synthetic setting over `T=3` to `10`, STGNN and modified AlphaQubit have nearly coincident survivor-conditioned logical-accuracy curves above delayed-erasure MWPM and standard MWPM.

Figure 3 has no error bars, and the source does not report the number of test samples, repeated seeds,
uncertainty intervals or statistical tests. The comparison does not isolate history access.

## Overall loss-identification result [paper_fact]
Fact ID: wang-loss-identification-result
Source locator: PDF p. 4, Qubit Loss first two paragraphs
PDF page: 4
Claim: At threshold 0.5 after ten QEC rounds, STGNN has reported loss-identification recall 0.654 and precision 0.845, while modified AlphaQubit has recall 0.652 and precision 0.856.

The two MWPM methods are excluded from this diagnostic comparison because they do not return loss
classifications.

## Threshold trade-off [paper_fact]
Fact ID: wang-threshold-result
Source locator: PDF pp. 4–5, Qubit Loss threshold paragraph and Fig. 4
PDF page: 5
Claim: The STGNN loss-head sweep shows decreasing recall and increasing precision as the decision threshold rises, with the plotted F1 score reported to peak near threshold 0.45.

Hardware-specific threshold policies are discussed prospectively; none is evaluated in a feedback
experiment.

## History-length diagnostic [paper_fact]
Fact ID: wang-history-length-diagnostic
Source locator: PDF p. 5, Fig. 5 and surrounding paragraphs
PDF page: 5
Claim: After a ten-round episode, losses occurring in the first round have a reported miss rate below 10%, whereas losses occurring in the final round have a miss rate above 85% for both learned decoders.

Earlier losses persist longer and provide more syndrome opportunities. This conditional association
shows diagnostic use of accumulated simulated record structure but is not a matched history-removal
experiment.

## Inference-latency result [paper_fact]
Fact ID: wang-inference-latency
Source locator: PDF p. 5, Inference Time paragraphs
PDF page: 5
Claim: The source reports approximately 0.410 ms per modified-AlphaQubit recurrent update and 4.10 ms cumulatively over ten rounds, compared with 0.595 ms for one STGNN pass over the complete ten-round window.

The hardware platform, batch size, numerical precision, warm-up, repetitions and timing uncertainty
are not reported. The source labels the benchmark preliminary and states that neither model was
extensively optimized.

## Reinitialization status [paper_fact]
Fact ID: wang-reinitialization-status
Source locator: PDF pp. 4–6, Qubit Loss and Conclusion paragraphs
PDF page: 6
Claim: The paper presents qubit reinitialization and continuous atom loading as downstream motivations rather than operations executed in the evaluated simulation.

Its suggestion that replacing high-error false positives could reduce local entropy and benefit
long-term QEC stability is not accompanied by a control-policy or logical-performance result.

## Generalization status [paper_fact]
Fact ID: wang-generalization-status
Source locator: PDF pp. 4, 6 and 12, Fig. 3, Conclusion final paragraph and Supplemental Circuit-Level Noise Model
PDF page: 6
Claim: A foundation model with generalization ability and decoding of non-local qLDPC codes are listed as future efforts.

The reported experiments contain one distance, one code family and one printed noise/loss parameter
setting.

## Matched-history boundary [literature_gap]
Fact ID: wang-gap-matched-history
Source locator: PDF pp. 2–4 and 9–12, architecture and comparator sections, Figs. 3 and S1
PDF page: 11
Claim: The source does not evaluate one frozen decoder with record history selectively removed, truncated, shuffled or replaced by an otherwise-matched state summary.
Gap scope: source_local

The reported decoder arms differ simultaneously in architecture, features, information access,
parameter count, graph approximation and decision timing.

## Hardware-evidence boundary [literature_gap]
Fact ID: wang-gap-hardware
Source locator: PDF pp. 3, 6 and 12, Training Process, Conclusion and Supplemental Circuit-Level Noise Model sections
PDF page: 12
Claim: The source does not evaluate its decoder or loss classifier on quantum-device records and does not execute hardware feedback or reinitialization.
Gap scope: source_local

All reported QEC examples use the declared synthetic surface-code generator.

## Population and uncertainty boundary [literature_gap]
Fact ID: wang-gap-population-uncertainty
Source locator: PDF pp. 4–5, Logical Accuracy section and Figs. 3–5
PDF page: 5
Claim: The source does not report test-population size, sample counts, random-seed repetitions, uncertainty intervals or statistical tests for its accuracy, diagnostic or latency results.
Gap scope: source_local

The phrase “statistically robust assessment” is not accompanied by those quantities in the fixed
artifact.

## Wrong-model robustness boundary [literature_gap]
Fact ID: wang-gap-wrong-model
Source locator: PDF pp. 6 and 12, Conclusion and Supplemental Circuit-Level Noise Model sections
PDF page: 12
Claim: The source does not test a frozen decoder under an incorrect loss rate, persistence law, mixed mechanism, stale calibration or held-out noise family.
Gap scope: source_local

The word “robust” in the abstract is not attached to a model-mismatch evaluation.

## Frozen-transfer boundary [literature_gap]
Fact ID: wang-gap-transfer
Source locator: PDF pp. 4, 6, 9 and 12, Fig. 3, Tables I–II and Conclusion
PDF page: 12
Claim: The source does not evaluate one frozen learned model across a new code distance, code family, physical device or calibrated operating regime.
Gap scope: source_local

Generalization-capable models and qLDPC decoding remain prospective.

## Unconditional logical-performance boundary [literature_gap]
Fact ID: wang-gap-unconditional-logical
Source locator: PDF pp. 4 and 12, Logical Accuracy and Supplemental Metrics sections
PDF page: 12
Claim: The source does not report an unconditional full-task logical-failure metric that retains logical operators intersected by lost data qubits.
Gap scope: source_local

Figure 3 uses the declared survivor-conditioned logical-accuracy definition.

## Closed-loop intervention boundary [literature_gap]
Fact ID: wang-gap-closed-loop
Source locator: PDF pp. 4–6, Qubit Loss and Conclusion paragraphs
PDF page: 6
Claim: The source does not demonstrate that using predicted loss locations for reinitialization or control improves subsequent multicycle or logical performance.
Gap scope: source_local

Threshold selection, continuous loading and replacement of false-positive qubits are discussed only
as operational possibilities.

## Reproducibility boundary [literature_gap]
Fact ID: wang-gap-reproducibility
Source locator: PDF pp. 3 and 8–12, Training Process and Supplemental Network Structure and Training Details sections
PDF page: 12
Claim: The fixed artifact supplies no code repository, data volume, train/validation/test split, optimizer, learning rate, epoch count, random seeds or complete latency-benchmark protocol.
Gap scope: source_local

Architectures and loss functions are described, but the missing training and benchmark details
prevent independent numerical replay from the paper alone.

## Executable loss-generator boundary [literature_gap]
Fact ID: wang-gap-loss-generator
Source locator: PDF pp. 3 and 12, Training Process and Supplemental Circuit-Level Noise Model
PDF page: 12
Claim: The source does not specify an executable Stim loss/removal circuit transformation, sampler or overlapping multi-loss record-generation rule for the synthetic training and evaluation data.
Gap scope: source_local

The delayed-erasure baseline supplies an approximate single-loss graph and explicitly neglects
interactions among multiple lost data qubits; it does not close the generator specification.

## STGNN logical-output boundary [literature_gap]
Fact ID: wang-gap-stgnn-logical-output
Source locator: PDF pp. 3, 4 and 9, Training Process, Fig. 3, Eq. (S7) and Algorithm 1
PDF page: 9
Claim: The fixed source does not provide one internally consistent STGNN logical-output and label map because it alternates among a binary scalar, one two-class output and `d` logical-line outputs.
Gap scope: source_local

The printed feature modules can be reconstructed conceptually, but the exact logical-head/label
bridge cannot be replayed from the manuscript alone.

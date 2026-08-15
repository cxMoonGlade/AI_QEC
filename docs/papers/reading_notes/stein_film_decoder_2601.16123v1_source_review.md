+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2601.16123"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2601.16123v1"
source_artifact = "outputs/overview/literature/coverage_validation/stein_download/PDFs/Calibration-Conditioned_FiLM_Decoders_for_Low-Latency_Decoding_of_Quantum_Error_Correction_Evaluated_on_IBM_Repetition-Code_Experiments.pdf"
source_sha256 = "f09848cdf8ed099ebf213750bdbf397a92659f04c4e8c6e5177454821b3de50e"
title = "Calibration-Conditioned FiLM Decoders for Low-Latency Decoding of Quantum Error Correction Evaluated on IBM Repetition-Code Experiments"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/STEIN_FILM_DECODER_2601_16123_AUDIT_2026-08-05.md"
audit_packet_sha256 = "aa939b421cbfdc8dd3f18615ba4ecac16c1b56885f38a2269d1cea6779d07783"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_hockings"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

[[relations]]
predicate = "defines"
object_id = "stein-calibration-graph"
object_type = "model"
object_label = "target contiguous heavy-hex qubit chain"
fact_id = "stein-calibration-graph"

[[relations]]
predicate = "uses"
object_id = "stein-film-decoder"
object_type = "method"
object_label = "three-layer graph convolutional network"
fact_id = "stein-film-computation"

[[relations]]
predicate = "supports"
object_id = "stein-later-snapshot-transfer"
object_type = "observable"
object_label = "one-week-later Kingston experiments"
fact_id = "stein-unseen-transfer-result"

[[relations]]
predicate = "defines"
object_id = "stein-matched-cnn"
object_type = "method"
object_label = "unconditioned CNN comparator"
fact_id = "stein-matched-cnn-comparator"

[[relations]]
predicate = "limits"
object_id = "stein-calibration-conditioned-transfer-scope"
object_type = "limitation"
object_label = "fresh target calibration"
fact_id = "stein-transfer-boundary"
+++
# Full-text review — Stein et al., "Calibration-Conditioned FiLM Decoders for Low-Latency Decoding of Quantum Error Correction Evaluated on IBM Repetition-Code Experiments"

## Source identity [paper_fact]
Fact ID: stein-source-identity
Source locator: Title page, arXiv margin stamp and official version metadata
PDF page: 1
Claim: The fixed source is the 18-page arXiv:2601.16123v1 preprint by Samuel Stein and eight coauthors, submitted on 22 January 2026.

The artifact contains the main text, Appendix A, eight tables, seven figures and references. The
official arXiv version history contained only v1 at the time of review.

## Selection scope [paper_fact]
Fact ID: stein-selection-scope
Source locator: Abstract; Secs. I and IV
PDF page: 2
Claim: The source evaluates a calibration-conditioned neural decoder on multiround one-dimensional repetition-code experiments executed on IBM Fez, Kingston and Pittsburgh processors and on independently selected Kingston chains measured one week later.

The decoder receives both ordered detection events and a target hardware calibration graph.

## Repetition-code task [paper_fact]
Fact ID: stein-repetition-task
Source locator: Sec. II.A; Figs. 2–3
PDF page: 3
Claim: The experiments prepare X- or Z-basis repetition-code states, perform repeated parity checks with ancilla measurement and reset, and finish with data-qubit measurements and majority-vote logical readout.

The reported distances are 3, 5, 7, 9 and 11, with odd round counts from one through the distance.

## Detection-event representation [paper_fact]
Fact ID: stein-detector-representation
Source locator: Sec. II.A; Eq. (2)
PDF page: 3
Claim: The QEC record supplied to the neural decoder is an ordered binary tensor whose entry at round `t` and stabilizer `i` is the XOR of consecutive stabilizer outcomes, using a zero initial reference.

The tensor has shape `r x (d-1)` before the neural batch and channel dimensions.

## Calibration-graph representation [paper_fact]
Fact ID: stein-calibration-graph
Source locator: Sec. II.B; Sec. III.A; Fig. 1
PDF page: 4
Claim: A target contiguous heavy-hex qubit chain is represented as a graph with node and edge features drawn from the corresponding calibration snapshot, including normalized T1, T2, readout error and one- and two-qubit gate errors.

This graph is side information about the measured target hardware state rather than an inferred
trajectory or a history-dependent transition model.

## FiLM computation [paper_fact]
Fact ID: stein-film-computation
Source locator: Algorithm 1; Eqs. (4)–(7); Sec. III.A
PDF page: 5
Claim: A three-layer graph convolutional network and global mean pooling produce a hardware embedding, an MLP maps that embedding to feature-wise affine modulation values, and three FiLM-conditioned two-dimensional convolution blocks map the detection tensor to per-data-qubit flip probabilities.

The printed pooled hardware embedding has dimension 256.

## Decoder output interface [paper_fact]
Fact ID: stein-output-interface
Source locator: Secs. II.A and III.B; Eq. (8)
PDF page: 6
Claim: The neural output is a vector of per-data-qubit flip probabilities trained with binary cross-entropy against prepared-bit XOR measured-bit targets; thresholded predictions update the Pauli frame before majority-vote logical readout.

Logical error rate after that frame update is the hardware performance metric.

## Model granularity [paper_fact]
Fact ID: stein-model-granularity
Source locator: Secs. I, II.C, III.B and IV.A
PDF page: 6
Claim: The source trains a separate FiLM decoder and matched CNN for every logical basis and every distance-round pair.

Its references to a single trained model apply within one fixed basis and `(d,r)` setting, not across
distances, round counts or bases.

## Training and validation protocol [paper_fact]
Fact ID: stein-training-protocol
Source locator: Sec. III.B; Sec. IV.A; Table II
PDF page: 6
Claim: For each basis and distance-round setting, shots from Fez, Kingston and Pittsburgh are pooled and split 70:30 for training and validation; models use Adam with learning rate 0.005, cosine scheduling, 100 epochs and validation-accuracy checkpoint selection.

The paper does not identify whether the 70:30 split is grouped by shot, contiguous chain or
calibration snapshot. The same validation partition selects checkpoints by validation accuracy
before the paper reports its validation LER, so it is not an independent post-selection test.

## Matched CNN comparator [paper_fact]
Fact ID: stein-matched-cnn-comparator
Source locator: Sec. II.C; Sec. III.B
PDF page: 5
Claim: The unconditioned CNN comparator preserves the convolutional backbone, detector input, loss, optimizer, data split and decision threshold while removing the calibration graph encoder and FiLM generator.

This comparison isolates calibration conditioning at the neural-package level; it does not add or
remove access to the multiround detector record.

## Calibration-informed MWPM comparator [paper_fact]
Fact ID: stein-mwpm-comparator
Source locator: Sec. II.C
PDF page: 4
Claim: The modified MWPM comparator constructs a distinct circuit-level detector graph and target-calibrated Pauli edge weights for every device, basis, distance, round count and calibration snapshot.

It is therefore also supplied with target calibration information, but through a Pauli-twirled
matching abstraction rather than the learned FiLM mapping.

## Experimental reach [paper_fact]
Fact ID: stein-experimental-reach
Source locator: Secs. I and IV.A, p. 6
PDF page: 6
Claim: The hardware corpus contains 2,760,704 shots collected over 400 contiguous-chain calibration snapshots on IBM Fez, Kingston and Pittsburgh for X- and Z-basis repetition codes at distances 3 through 11 and odd round counts up to the distance.

The source does not evaluate a surface code, a different code family or a logical gate experiment.

## Unseen-chain transfer protocol [paper_fact]
Fact ID: stein-unseen-transfer-protocol
Source locator: Sec. IV.C
PDF page: 9
Claim: The trained parameters are applied without retraining or fine-tuning to independently selected Kingston chains and new calibration snapshots acquired one week later, while each new target calibration graph is supplied to the fixed GCN and FiLM mapping.

Kingston is already present in the pooled training-device set. The protocol therefore tests new
chains and a later operating snapshot on a seen device, not leave-one-device-out transfer.

## Validation-set decoder result [paper_fact]
Fact ID: stein-validation-result
Source locator: Sec. IV.B; Figs. 4–5; Tables III–IV
PDF page: 8
Claim: The validation tables show configuration-dependent decoder ordering: the calibration-conditioned FiLM decoder has its strongest relative gains at larger distance and round count, while several shallow and intermediate X- and Z-basis settings have lower reported LER for MWPM, the unconditioned CNN comparator or both.

The exact split-grouping boundary stated in the training protocol applies to these validation
comparisons.

## Unseen-chain transfer result [paper_fact]
Fact ID: stein-unseen-transfer-result
Source locator: Sec. IV.C; Figs. 6–7; Tables V–VI
PDF page: 9
Claim: The one-week-later Kingston experiments show configuration-dependent ordering rather than table-wide FiLM superiority; the FiLM decoder retains its learned parameters and is strictly lower than both comparators in 14 of the 40 printed X- and Z-basis rows.

For Z-basis distance 11 and 11 rounds, the tabulated LERs are 0.00879 for FiLM, 0.0652 for MWPM
and 0.0733 for CNN, giving factors of 7.41 and 8.33 relative to the two comparators.

## Unseen X-basis result [paper_fact]
Fact ID: stein-unseen-x-result
Source locator: Table VI
PDF page: 16
Claim: For X-basis distance 11 and 11 rounds in the later Kingston experiment, the tabulated LERs are 0.0540 for FiLM, 0.118 for MWPM and 0.113 for CNN.

Those values support factors of 2.19 relative to MWPM and 2.09 relative to CNN.

## Uncertainty reporting [paper_fact]
Fact ID: stein-uncertainty
Source locator: Sec. IV.A; Figs. 4–7
PDF page: 7
Claim: The evaluation plots 95% confidence bands and the main text describes binomial 95% confidence intervals for the empirical logical error rates.

The unseen Fig. 6 caption instead describes 95% confidence intervals across calibration snapshots,
and the source does not give the aggregation formula, per-configuration shot counts or numerical
interval endpoints.

## Folded and dynamic conditioning modes [paper_fact]
Fact ID: stein-conditioning-modes
Source locator: Secs. III.C and IV.D; Table I
PDF page: 10
Claim: In dynamic mode the target calibration graph is processed for every inference, whereas folded mode processes calibration when it changes and algebraically folds the resulting FiLM modulation into effective convolution weights for subsequent records.

Thus folded inference fixes the learned mapping but updates target-conditioned effective CNN
weights when a new calibration snapshot is provided.

## Inference-latency result [paper_fact]
Fact ID: stein-latency-result
Source locator: Sec. IV.D; Table I
PDF page: 10
Claim: On an Nvidia RTX 5000 at batch size one, 2,000 timed iterations after 500 warmups give approximately 81–98 microseconds per shot for the CNN and folded FiLM modes and approximately 1.38–1.43 milliseconds for dynamic FiLM.

The benchmark is a GPU forward pass rather than end-to-end integration with a QEC control stack,
and the calibration-update and folding time is not reported separately.

## Claimed transfer boundary [paper_fact]
Fact ID: stein-transfer-boundary
Source locator: Secs. IV.C, V and VI
PDF page: 12
Claim: The source presents its later Kingston evaluation as zero-shot transfer without retraining or fine-tuning, but that transfer keeps the device identity within the training pool, supplies fresh target calibration and uses a model trained specifically for the target basis and distance-round pair.

No cross-code, cross-distance, cross-round or calibration-blind transfer follows from this protocol.

## Abstract gain inconsistency [paper_fact]
Fact ID: stein-abstract-gain-inconsistency
Source locator: Abstract, p. 2; Tables III and V, pp. 14–15
PDF page: 15
Claim: The abstract attributes an improvement up to 11.1 times over MWPM to unseen experiments, while the exact 11.11-times row is in the validation-set Z-basis Table III rather than the one-week-later Table V.

For the later Kingston Z-basis table, distance 11 and 11 rounds gives 7.41 times and the largest
tabulated MWPM ratio is approximately 9.09 at distance 11 and 9 rounds.

## X-basis ratio inconsistency [paper_fact]
Fact ID: stein-x-ratio-inconsistency
Source locator: Sec. IV.C, p. 9; Table VI, p. 16
PDF page: 16
Claim: Sec. IV.C reports both 2.09 and 2.19 times as the unseen X-basis distance-11, round-11 gain over MWPM, while Table VI supports 2.19 times over MWPM and 2.09 times over the matched CNN.

The table values, rather than the ambiguous prose, determine the comparator-specific ratios.

## Explicit temporal-memory-law boundary [literature_gap]
Fact ID: stein-gap-memory-law
Source locator: Secs. I–III and Eqs. (2)–(7), full model specification
PDF page: 6
Claim: The source does not specify or estimate a continuing physical carrier, hidden-state transition, temporal kernel, memory time or formal quantum non-Markovianity.
Gap scope: source_local

The target calibration snapshot supplies slowly varying side information, while the ordered detector
record supplies multiround observations.

## Memory-access ablation boundary [literature_gap]
Fact ID: stein-gap-memory-access
Source locator: Sec. II.C and full comparator specification
PDF page: 5
Claim: The source does not compare otherwise identical decoders with and without access to detector history or to a declared memory state.
Gap scope: source_local

Both neural decoders consume the same ordered multiround detection tensor; their controlled
difference is calibration conditioning.

## Wrong-model robustness boundary [literature_gap]
Fact ID: stein-gap-wrong-model
Source locator: Secs. IV.C and V, full transfer evaluation
PDF page: 12
Claim: The source does not test stale, missing, biased or deliberately misspecified calibration metadata and does not perturb an explicit memory law.
Gap scope: source_local

The later-snapshot transfer evaluation provides the current target calibration rather than a wrong
conditioning model.

## Unseen-device transfer boundary [literature_gap]
Fact ID: stein-gap-unseen-device
Source locator: Secs. III.B and IV.C
PDF page: 9
Claim: The source does not hold out an entire device during training or evaluate the frozen learned mapping on a processor absent from the training-device pool.
Gap scope: source_local

Fez, Kingston and Pittsburgh all contribute training shots, and the later independent experiment is
performed on Kingston.

## Cross-configuration transfer boundary [literature_gap]
Fact ID: stein-gap-cross-configuration
Source locator: Secs. I, III.B and IV.A, pp. 2, 4 and 6
PDF page: 6
Claim: The source does not evaluate one identical checkpoint across bases, distances, round counts or QEC code families.
Gap scope: source_local

Separate models are trained for each basis and `(d,r)` setting.

## Calibration-blind transfer boundary [literature_gap]
Fact ID: stein-gap-calibration-blind
Source locator: Secs. III.A, III.C and IV.C
PDF page: 9
Claim: The source does not demonstrate transfer with all target-dependent inputs and effective parameters frozen.
Gap scope: source_local

New target calibration features are processed to generate FiLM values and, in folded mode, new
effective convolution weights.

## Validation split boundary [literature_gap]
Fact ID: stein-gap-validation-split
Source locator: Sec. III.B; Sec. IV.A; Table II
PDF page: 13
Claim: The source does not state whether its pooled 70:30 train-validation division prevents shots from the same chain or calibration snapshot from appearing on both sides, and the validation partition is reused for checkpoint selection before its LER is reported.
Gap scope: source_local

The later one-week transfer experiment does explicitly use independently selected chains.

## Exact uncertainty boundary [literature_gap]
Fact ID: stein-gap-uncertainty
Source locator: Sec. IV.A; Figs. 4–7; Tables III–VI
PDF page: 16
Claim: The source does not report per-configuration shot counts, numerical confidence-interval endpoints or an unambiguous interval aggregation rule.
Gap scope: source_local

Confidence bands are nevertheless plotted, so the results are not point-estimate-only evidence.

## Data-locator boundary [literature_gap]
Fact ID: stein-gap-data-locator
Source locator: Abstract and full fixed-PDF availability boundary
PDF page: 18
Claim: The source states that experimental data and raw IBM archives are provided but gives no repository identifier, URL or data-availability section in the fixed PDF.
Gap scope: source_local

The reported records cannot be resolved from this artifact alone.

## Integrated-latency boundary [literature_gap]
Fact ID: stein-gap-integrated-latency
Source locator: Secs. III.C and IV.D; Table I
PDF page: 10
Claim: The source does not measure end-to-end latency in a hardware control stack or separately report the cost of processing and folding a changed calibration snapshot.
Gap scope: source_local

The printed latency experiment measures neural GPU forward-pass modes at batch size one.

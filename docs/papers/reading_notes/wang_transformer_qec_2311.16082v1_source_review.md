+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2311.16082"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2311.16082v1"
source_artifact = "outputs/overview/literature/coverage_validation/sources/2311.16082v1.pdf"
source_sha256 = "cc4a5fce3676648a1cfd8cc378ac4bf0a8b994294cef02acff18422696f30aa1"
title = "Transformer-QEC: Quantum Error Correction Code Decoding with Transferable Transformers"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/WANG_TRANSFORMER_QEC_2311_16082_AUDIT_2026-08-05.md"
audit_packet_sha256 = "81e30793d9aba3a8dd5c96cc8d7299d9f15fbe47a49da84903b2f6cf720ede4b"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_qadapt"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7]

[[relations]]
predicate = "defines"
object_id = "wang-six-channel-record"
object_type = "model"
object_label = "six-channel multiround syndrome grid"
fact_id = "wang-record-representation"

[[relations]]
predicate = "uses"
object_id = "wang-transformer-decoder"
object_type = "method"
object_label = "Transformer encoder and decoder"
fact_id = "wang-transformer-computation"

[[relations]]
predicate = "uses"
object_id = "wang-residual-mwpm"
object_type = "method"
object_label = "residual MWPM stage"
fact_id = "wang-hybrid-interface"

[[relations]]
predicate = "uses"
object_id = "wang-target-distance-finetuning"
object_type = "method"
object_label = "target-distance fine-tuning"
fact_id = "wang-transfer-protocol"

[[relations]]
predicate = "supports"
object_id = "wang-table-one-logical-rates"
object_type = "observable"
object_label = "logical-error point estimates"
fact_id = "wang-table-one-results"

[[relations]]
predicate = "limits"
object_id = "wang-frozen-transfer-boundary"
object_type = "limitation"
object_label = "target-distance fine-tuning"
fact_id = "wang-transfer-protocol"
+++
# Full-text review — Wang et al., “Transformer-QEC: Quantum Error Correction Code Decoding with Transferable Transformers”

## Source identity [paper_fact]
Fact ID: wang-source-identity
Source locator: Title page; arXiv margin stamp; official arXiv version history and comments
PDF page: 1
Claim: The fixed source is the seven-page arXiv:2311.16082v1 preprint by Hanrui Wang and seven coauthors, submitted on 27 November 2023 and listed by arXiv as accepted to the ICCAD 2023 FAST ML for Science Workshop.

The official arXiv version history contained only v1 at the time of review. A fresh download from
the official v1 PDF endpoint matched the fixed artifact's SHA-256 hash.

## Selection scope [paper_fact]
Fact ID: wang-selection-scope
Source locator: Abstract, p. 1; Sec. 1 contribution list, p. 2; Secs. 3--4, pp. 4--5
PDF page: 5
Claim: The source develops a Transformer-based pre-decoder for simulated repeated rotated-surface-code memory data and evaluates target-distance fine-tuning within that code family.

The learned stage predicts physical errors and parity; an auxiliary matching decoder processes the
remaining syndrome before the final logical decision.

## Phenomenological error model [paper_fact]
Fact ID: wang-phenomenological-model
Source locator: Sec. 4.1, “Benchmarks”
PDF page: 5
Claim: The simulation assigns syndrome-measurement error probability `p` and data-qubit depolarising-error probability `p`, with X, Y and Z components equally likely, and generates the circuits and stabiliser samples with Stim.

The source sets the two printed error probabilities equal. It does not specify a continuing carrier,
latent transition state or history-conditioned probability.

## Repeated-QEC record [paper_fact]
Fact ID: wang-repeated-record
Source locator: Sec. 3, “Transformer model”; Figs. 3 and 6
PDF page: 4
Claim: For code distance `D`, the source uses `D` repeated syndrome-extraction rounds plus a final measurement layer, so the decoder input contains an ordered round dimension.

The number of rounds therefore changes with code distance in the reported benchmark.

## Record representation [paper_fact]
Fact ID: wang-record-representation
Source locator: Sec. 3, “Transformer model”; Fig. 6
PDF page: 4
Claim: The six-channel multiround syndrome grid encodes X-check locations, Z-check locations, two syndrome channels and binary flags for the initial and terminal temporal boundaries on a `(D+1)`-scale cubic lattice.

The features are embedded, augmented by three-dimensional sinusoidal positional encoding and
flattened into a one-dimensional token sequence.

## Transformer computation [paper_fact]
Fact ID: wang-transformer-computation
Source locator: Sec. 3, “Transformer model”; Fig. 6
PDF page: 4
Claim: The Transformer encoder and decoder apply self-attention over syndrome tokens and cross-attention from data-qubit positional queries to predict local physical errors.

The main model has six layers, embedding dimension 256, eight attention heads, feed-forward width
512 and approximately 7.9 million parameters.

## Mixed loss and threshold [paper_fact]
Fact ID: wang-mixed-loss
Source locator: Sec. 3, “Mixed loss”; Sec. 4.2, Table 2
PDF page: 4
Claim: Training combines weighted binary cross-entropy for local physical-error labels with binary cross-entropy for a globally pooled parity label, and post-sigmoid confidence greater than `0.95` triggers a positive local-error prediction.

At distance 5, Table 2 reports that adding global loss improves or matches nine of ten logical-error
point estimates but is worse at `p=0.0075`, where `0.00103` exceeds `0.00097`.

## Hybrid QEC interface [paper_fact]
Fact ID: wang-hybrid-interface
Source locator: Sec. 3, “Overall workflow”; Sec. 4.2, “Main results”
PDF page: 4
Claim: Transformer-QEC uses a residual MWPM stage to clear syndrome left after the learned physical-error prediction and XORs the matching decoder's parity with the Transformer's predicted parity.

The source itself attributes the closeness to the MWPM baseline partly to this embedded MWPM
component. The printed Transformer-QEC logical rates therefore describe a hybrid pipeline.

## Source-model training [paper_fact]
Fact ID: wang-source-training
Source locator: Sec. 4.1, “Training settings” and “Transfer learning settings”
PDF page: 5
Claim: The distance-5 source model is trained from scratch for 100 epochs on one million samples generated at `p=0.01`, using Adam on one NVIDIA A6000 GPU.

The source gives the optimiser, learning-rate schedule and weight decay but not a train/validation/test
split, seed list, stopping rule or evaluation sample count.

## Transfer protocol [paper_fact]
Fact ID: wang-transfer-protocol
Source locator: Sec. 3, “Transfer learning”; Sec. 4.1, “Transfer learning settings”
PDF page: 5
Claim: Target-distance fine-tuning starts from the distance-5 checkpoint, adjusts positional encoding for the new distance and performs 10 training epochs on the new distance's dataset at learning rate `5e-4`.

The source states that all other training settings remain identical to scratch training. This is
pretrained initialisation followed by parameter updates, not frozen inference.

## Baseline configuration [paper_fact]
Fact ID: wang-baselines
Source locator: Sec. 4.1, “Baselines” and “Training settings”
PDF page: 5
Claim: The reported baselines are Union Find, MWPM and a two-hidden-layer MLP trained separately for each distance for 100 epochs.

The MLP training data use `p=0.01` at distances 3 and 5 and `p=0.025` at distances 7 and 9. The
source does not report a target-distance Transformer trained from scratch as a matched comparator
for the transferred Transformer.

## Error-rate grid [paper_fact]
Fact ID: wang-error-grid
Source locator: Sec. 4.1, “Benchmarks”
PDF page: 5
Claim: The ten reported error configurations are the scalar values `0.05`, `0.04`, `0.03`, `0.025`, `0.02`, `0.015`, `0.01`, `0.0075`, `0.005` and `0.0025` within the same phenomenological model.

They vary error strength, not the form of a temporal process or the identity of a physical device.

## Reported distance reach [paper_fact]
Fact ID: wang-reported-distances
Source locator: Abstract and Sec. 1; Sec. 4.1; Table 1; Fig. 8
PDF page: 5
Claim: The abstract and introduction state evaluation at distances 3, 5, 7, 9, 11 and 13, whereas the evaluation method, Table 1 and Figure 8 report only distances 3, 5, 7 and 9.

No distance-11 or distance-13 numerical result appears elsewhere in the seven-page artifact.

## Table-1 logical results [paper_fact]
Fact ID: wang-table-one-results
Source locator: Sec. 4.2, “Main results”; Table 1
PDF page: 5
Claim: Table 1 supplies logical-error point estimates for UF, MWPM, MLP and Transformer-QEC at distances 3, 5, 7 and 9 for physical error rates `0.05` and `0.01`.

The smallest Transformer-QEC/MWPM differences include `0.17232` versus `0.17279` at distance 5
and `p=0.05`, and `1e-5` versus `2e-5` at distance 9 and `p=0.01`; the source gives no
sample count or uncertainty for those estimates.

## Printed MWPM counterexample [paper_fact]
Fact ID: wang-mwpm-counterexample
Source locator: Sec. 4.2, “Main results”; Table 1
PDF page: 5
Claim: At distance 7 and `p=0.05`, Table 1 reports Transformer-QEC logical error `0.20590` and the lower MWPM value `0.20178`, contrary to the surrounding statement that Transformer-QEC is lower for all benchmarks.

This is a source-internal numerical counterexample to the blanket superiority statement.

## Threshold reporting inconsistency [paper_fact]
Fact ID: wang-threshold-inconsistency
Source locator: Fig. 8, caption and “Evaluation of the threshold” paragraph
PDF page: 6
Claim: Figure 8 and its caption print a Transformer-QEC threshold near `0.038`, while the adjacent prose gives `0.0038` for the curve intersection.

The plotted crossing is visually near `0.038`; no finite-size scaling or uncertainty analysis is
reported.

## Figure-7 label boundary [paper_fact]
Fact ID: wang-figure-seven-label
Source locator: Fig. 7
PDF page: 6
Claim: Figure 7 prints `D5 p0.02` under two different bar groups, so one evaluated condition in the plotted physical-error accuracy comparison is not uniquely identified.

The source files or data needed to resolve the duplicate label are not linked in the paper.

## Epoch-count cost proxy [paper_fact]
Fact ID: wang-training-cost
Source locator: Abstract; Sec. 1; Sec. 4.1, training paragraphs
PDF page: 5
Claim: The disclosed quantitative basis for the claimed greater-than-tenfold training-cost saving is a reduction from 100 source-training epochs to 10 target-distance fine-tuning epochs.

No wall-clock duration, GPU-hours, energy, convergence criterion or accuracy-matched target-distance
scratch Transformer is reported.

## Statistical reporting boundary [paper_fact]
Fact ID: wang-statistical-boundary
Source locator: Sec. 4 and Tables 1--3, full evaluation scope
PDF page: 5
Claim: The evaluation reports point estimates without test-set sizes, confidence intervals, error bars, repeated seeds, paired decoder outcomes or a stated uncertainty estimator.

The training sample count does not establish the unreported evaluation sample count.

## Artifact boundary [paper_fact]
Fact ID: wang-artifact-boundary
Source locator: Full seven-page artifact; official arXiv record
PDF page: 7
Claim: The source provides no code or data availability statement, repository link, model checkpoint, generated evaluation records or separate Supplementary Information.

The official arXiv record supplies the PDF and TeX source but no author-declared implementation or
data artifact.

## No frozen transfer [literature_gap]
Fact ID: wang-gap-frozen-transfer
Source locator: Sec. 3, “Transfer learning”; Sec. 4.1, “Transfer learning settings”
PDF page: 5
Claim: The source does not evaluate frozen target-distance inference because every target-distance model is fine-tuned for 10 epochs after positional-encoding adjustment.
Gap scope: source_local

The abstract's phrase “without retraining” is incompatible with the explicit evaluation protocol.

## No independent-domain transfer [literature_gap]
Fact ID: wang-gap-independent-transfer
Source locator: Secs. 3--4, complete transfer and evaluation scope
PDF page: 5
Claim: The source does not transfer a fixed model across a quantum device, code family, decoder backend or independently calibrated noise distribution.
Gap scope: source_local

All reported target models remain within rotated surface codes generated by the same phenomenological
model and receive target-distance training.

## No wrong-model robustness test [literature_gap]
Fact ID: wang-gap-wrong-model
Source locator: Sec. 4.1, “Benchmarks”; complete evaluation scope
PDF page: 5
Claim: The source does not freeze a decoder and evaluate it under an incorrect carrier lifetime, history law, drift process, calibration or mixed temporal mechanism.
Gap scope: source_local

Changing the scalar physical error rate within the printed phenomenological family is the only
reported noise variation.

## No temporal-memory generator [literature_gap]
Fact ID: wang-gap-temporal-generator
Source locator: Sec. 4.1, complete phenomenological-model specification
PDF page: 5
Claim: The source does not specify a continuing physical or latent carrier, a state-transition model or a history-conditioned noise probability.
Gap scope: source_local

The decoder consumes several rounds, but the source does not identify the noise generator itself as
temporally dependent.

## No temporal-access ablation [literature_gap]
Fact ID: wang-gap-temporal-access
Source locator: Secs. 3--4, complete architecture and comparison scope
PDF page: 4
Claim: The source does not compare otherwise matched decoders with and without access to earlier rounds, a temporal-attention path or a declared memory-bearing state.
Gap scope: source_local

The MLP and algorithmic baselines change model class and input constraints rather than isolating
history access.

## No measured deployment cost [literature_gap]
Fact ID: wang-gap-deployment-cost
Source locator: Sec. 4.1 and full evaluation scope
PDF page: 5
Claim: The source does not measure neural inference latency, end-to-end decoder latency, throughput, memory use, hardware resources, wall-clock training time or energy.
Gap scope: source_local

One A6000 GPU is named as the training device, but no timing or utilisation measurement is given.

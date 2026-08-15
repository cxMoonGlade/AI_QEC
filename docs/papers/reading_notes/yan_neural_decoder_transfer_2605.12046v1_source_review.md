+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2605.12046"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2605.12046v1"
source_artifact = "outputs/overview/literature/coverage_validation/rethink_neural_decoders/2605.12046v1.pdf"
source_sha256 = "6b06b88907705b4b9ce674751cf198a188ff1a0a4446fd12b754121116f58c8c"
title = "Rethink the Role of Neural Decoders in Quantum Error Correction"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/YAN_NEURAL_DECODER_TRANSFER_2605_12046_AUDIT_2026-08-05.md"
audit_packet_sha256 = "fd903ac9fb2fed3806e2b95784cd32c498a613850146001e9d668859f32bc633"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_ziad"
admission_date = "2026-08-05"
visually_checked_pages = [1, 3, 4, 6, 7, 8, 9, 23, 27, 32, 33]

[[relations]]
predicate = "uses"
object_id = "yan-tcn-decoder"
object_type = "method"
object_label = "temporal convolutional decoder"
fact_id = "yan-tcn-computation"

[[relations]]
predicate = "supports"
object_id = "yan-calibrated-zero-shot-hardware"
object_type = "observable"
object_label = "device-calibrated synthetic pretraining"
fact_id = "yan-hardware-result"

[[relations]]
predicate = "supports"
object_id = "yan-cross-rate-result"
object_type = "observable"
object_label = "fixed TCN checkpoints"
fact_id = "yan-cross-rate-result"
+++
# Full-text review — Yan et al., “Rethink the Role of Neural Decoders in Quantum Error Correction”

## Source identity [paper_fact]
Fact ID: yan-source-identity
Source locator: Title page and arXiv version stamp
PDF page: 1
Claim: The fixed source is the 33-page arXiv:2605.12046v1 manuscript by Ge Yan, Shanchuan Li and Yuxuan Du, dated 12 May 2026 and marked as accepted to ICML 2026.

The artifact includes the complete appendices, tables and references.

## Study scope [paper_fact]
Fact ID: yan-study-scope
Source locator: Abstract; Sec. 1
PDF page: 1
Claim: The source compares five redesigned neural-decoder paradigms, training-data scale and compression choices for repeated rotated-surface-code Z-memory decoding and evaluates selected zero-shot and fine-tuned comparisons on released Sycamore records.

Its primary question is accuracy–latency co-design, not temporal-memory attribution.

## Ordered-record input [paper_fact]
Fact ID: yan-record-input
Source locator: Sec. 2, “Rotated surface code and memory experiment”
PDF page: 3
Claim: The decoder input is a dense spatiotemporal syndrome volume over repeated measurement rounds and the output is a predicted cumulative logical update for a Z-memory experiment.

## TCN computation [paper_fact]
Fact ID: yan-tcn-computation
Source locator: Sec. 3.1; Appendix C.1
PDF page: 4
Claim: The temporal convolutional decoder maps detectors to a spatial tensor, applies spatial encoding followed by one-dimensional temporal convolution blocks, and outputs a logical classification.

The source also compares MLP, 3D-CNN, Transformer and GNN implementations.

## Synthetic benchmark protocol [paper_fact]
Fact ID: yan-synthetic-protocol
Source locator: Appendix D.1, “Synthetic datasets”
PDF page: 23
Claim: Synthetic benchmarks use Stim rotated-surface-code Z-memory circuits at distances 3, 5, 7 and 9 with rounds equal to distance, separate fixed test sets of 50,000 samples and three random initializations.

Training sizes reach 5 million samples for distances 3 and 5 and 25 million for distances 7 and 9.

## Sycamore selection [paper_fact]
Fact ID: yan-sycamore-selection
Source locator: Appendix D.1, “Sycamore datasets”
PDF page: 23
Claim: The hardware evaluation uses released Sycamore Z-memory records at distance 3 with three rounds and distance 5 with five rounds, selecting distance-3 center `(7,5)` because it has the lowest baseline logical error rate among four available centers.

This selection limits population-wide interpretation.

## Hardware pretraining protocol [paper_fact]
Fact ID: yan-hardware-pretraining
Source locator: Appendix D.1, “Sycamore datasets”
PDF page: 23
Claim: For each selected hardware setting, the source generates 5 million synthetic pretraining samples from the device-calibrated Stim circuit supplied with the released dataset.

Target-device calibration is therefore available before zero-shot hardware evaluation.

## Hardware split [paper_fact]
Fact ID: yan-hardware-split
Source locator: Appendix D.1, “Sycamore datasets”
PDF page: 23
Claim: Each selected hardware configuration contains 50,000 experimental shots, divided into 45,000 shots for optional fine-tuning and 5,000 shots for testing.

The source does not state the split seed, exact checkpoint identity, whether all displayed decoders
reuse one common 5,000-shot cohort, or whether the Table 1 values aggregate splits or model runs.

## Hardware result [paper_fact]
Fact ID: yan-hardware-result
Source locator: Table 1
PDF page: 6
Claim: With device-calibrated synthetic pretraining and no experimental-shot fine-tuning, the reported TCN logical-error point estimates are 6.81 percent at distance 3 and 11.59 percent at distance 5, compared with correlated-MWPM point estimates of 7.38 percent and 12.52 percent.

The corresponding fine-tuned TCN values are 6.70 and 11.47 percent. Uniform-depolarizing
pretraining has higher reported point estimates than both matching baselines before fine-tuning.

## Hardware aggregation boundary [literature_gap]
Fact ID: yan-gap-hardware-aggregation
Source locator: Table 1, p. 6; Appendix D.1, p. 23
PDF page: 6
Claim: The declared 5,000-shot test allocation does not numerically determine the Table 1 point estimates because exact cohort reuse and aggregation are unstated, several printed percentages are incompatible with one unaveraged 5,000-trial binary count, and no hardware uncertainty or paired-decision record is supplied.
Gap scope: source_local

The hardware values can be reported as selected point estimates, but their sampling precision and
pairwise significance cannot be reconstructed from the paper.

## Hardware comparator boundary [paper_fact]
Fact ID: yan-hardware-comparator-boundary
Source locator: Table 1; Appendix D.1, “Baseline decoder”
PDF page: 23
Claim: Standard MWPM, correlated MWPM, zero-shot TCN and fine-tuned TCN differ in representation, training exposure and computation, so Table 1 is not a one-factor memory-access ablation.

## Cross-rate protocol [paper_fact]
Fact ID: yan-cross-rate-protocol
Source locator: Appendix E.4
PDF page: 32
Claim: Separate TCN checkpoints are trained to convergence at one scalar rate under uniform depolarizing and SI1000 generators and are then applied without retraining to lower rates within the same generator family at distances 5 and 7.

Test populations increase from 200,000 at rate 0.003 to 5 million at rate 0.001, and results are
reported as mean plus or minus standard deviation over three runs.

## Cross-rate result [paper_fact]
Fact ID: yan-cross-rate-result
Source locator: Tables 19–20; Appendix E.4 conclusion
PDF page: 32
Claim: The fixed TCN checkpoints have lower reported LER than MWPM at every tested lower rate in their respective generator families, while optional fine-tuning changes absolute LER by less than 0.02 percentage points across the reported configurations.

The values converge toward zero at the lowest rates, so rounded ties occur.

## Cross-model robustness boundary [literature_gap]
Fact ID: yan-gap-wrong-model
Source locator: Complete Appendix E.4 design
PDF page: 32
Claim: The source does not apply a checkpoint trained under uniform depolarizing noise to SI1000 or vice versa and does not perturb a temporal-memory transition law, carrier lifetime or mixed mechanism.
Gap scope: source_local

The result is within-family scalar-rate generalization, not wrong-memory-model robustness.

## Temporal-memory boundary [literature_gap]
Fact ID: yan-gap-memory-law
Source locator: Secs. 2–4 and comparator specification
PDF page: 6
Claim: Although the neural decoders consume ordered multiround records, the source does not identify a continuing physical or latent memory state or compare full-history access with a history-limited control.
Gap scope: source_local

Hardware improvement therefore cannot be attributed specifically to temporal-memory information.

## Transfer boundary [paper_fact]
Fact ID: yan-transfer-boundary
Source locator: Table 1; Appendix D.1; Appendix E.4
PDF page: 23
Claim: The demonstrated zero-shot applications use target-specific calibration or remain within one synthetic generator family and fixed code distance; no frozen cross-device, cross-code or cross-distance result is reported.

## FPGA boundary [paper_fact]
Fact ID: yan-fpga-boundary
Source locator: Sec. 4.3, p. 9; Appendix D.4, Table 16, p. 27
PDF page: 9
Claim: Most FPGA latency results are analytical resource estimates, while the reported HLS synthesis of a compressed distance-9 TCN kernel on a VP1902 target is listed as 271 cycles in the main text and 267 cycles in Appendix Table 16, with both locations reporting 0.77 microseconds.

The source does not reconcile the cycle-count discrepancy. This is not an integrated
quantum-control-stack timing test on the hardware-record experiment.

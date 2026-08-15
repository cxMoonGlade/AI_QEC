+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2310.05900"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2310.05900v1"
source_artifact = "outputs/overview/literature/final_expansion/sources/2310.05900.pdf"
source_sha256 = "6c38f70abfa12a3f622420fc0dc9ca18cc2086e9b0fc35014b3f6bcab298591c"
title = "Learning to Decode the Surface Code with a Recurrent, Transformer-Based Neural Network"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round2/ALPHAQUBIT_RECURRENT_DECODER_2310_05900_AUDIT_2026-08-05.md"
audit_packet_sha256 = "255a0483ac2f75fbc6252c85b74e0a506889cbc2812fa9838c1f5c3b4ccbcf22"
admission_status = "source_only_reviewed"
admission_reviewer = "/root"
admission_date = "2026-08-05"
visually_checked_pages = [1, 4, 5, 6, 7, 8, 9, 10, 13, 15, 34, 36, 38, 39, 40, 42, 49, 56, 61, 62, 64, 66, 68]

[[relations]]
predicate = "uses"
object_id = "alphaq-recurrent-decoder-state"
object_type = "model"
object_label = "fixed-size vector state"
fact_id = "alphaq-recurrent-state"

[[relations]]
predicate = "uses"
object_id = "alphaq-syndrome-transformer"
object_type = "method"
object_label = "multi-head self-attention"
fact_id = "alphaq-computational-architecture"

[[relations]]
predicate = "measures"
object_id = "alphaq-logical-error-per-round"
object_type = "observable"
object_label = "logical error per round"
fact_id = "alphaq-ler-definition"

[[relations]]
predicate = "limits"
object_id = "alphaq-memory-benefit-boundary"
object_type = "limitation"
object_label = "none of the listed controls removes the recurrent state"
fact_id = "alphaq-ablation-scope"
+++
# Full-text review — Bausch et al., recurrent syndrome-transformer decoder

## Source identity [paper_fact]
Fact ID: alphaq-source-identity
Source locator: Title page and arXiv page stamp
PDF page: 1
Claim: The fixed source is the 68-page arXiv:2310.05900v1 manuscript by Johannes Bausch and coauthors, posted 9 October 2023, entitled *Learning to Decode the Surface Code with a Recurrent, Transformer-Based Neural Network*.

The artifact contains the main text, Materials and Methods, Supplementary Text, figures, tables and
references. This note describes that fixed preprint rather than importing claims from its later
journal version.

## Selection scope [paper_fact]
Fact ID: alphaq-selection-scope
Source locator: Abstract; Secs. 2.1–2.5
PDF page: 1
Claim: The source develops a recurrent neural decoder for rotated-surface-code memory experiments and evaluates it on Sycamore experimental records and on simulated SI1000 and Pauli+ records with analog-readout and leakage variants.

Its principal outputs are logical-error predictions, fitted logical error per round, calibrated
prediction probabilities and compute-time measurements. It is a decoder study, not a direct
characterization of a physical memory process.

## Recurrent decoder state [paper_fact]
Fact ID: alphaq-recurrent-state
Source locator: Sec. 2.1 and Fig. 1b; Appendix A.4
PDF page: 4
Claim: The decoder reuses a fixed computation block each syndrome cycle and maintains a fixed-size vector state for every stabilizer that represents information from stabilizers observed up to the current cycle.

The current-cycle stabilizer representation is added to the corresponding prior state before three
syndrome-transformer layers update the state. A readout network may be applied after a variable
number of cycles. This establishes algorithmic access to a multiround record, not a physical or
formal definition of memory in the noise.

## QEC-facing input variables [paper_fact]
Fact ID: alphaq-input-variables
Source locator: Sec. 2.1; Appendix A.4.1
PDF page: 4
Claim: The basic QEC-facing inputs are stabilizer measurements and their temporal differences, called detection events, and simulated variants may add probabilistic measurement, probabilistic event, leakage-probability and leakage-difference channels.

For binary inputs, measurements and events contain the same information up to the initial frame.
The authors report that providing both improves training and performance relative to either input
alone, but this does not add an independently observed physical-memory variable.

## Computational architecture [paper_fact]
Fact ID: alphaq-computational-architecture
Source locator: Sec. 2.1 and Fig. 1c–f; Appendices A.4.1–A.4.4
PDF page: 5
Claim: Each recurrent update combines learned stabilizer embeddings with multi-head self-attention, a learned geometry-dependent attention bias, current/previous-cycle event-product features and dilated two-dimensional convolutions, followed by a spatial readout network that returns a logical-error probability.

Dense attention communicates between all stabilizer pairs, while the convolutions supply spatial
structure. The attention bias's explicit time-space indicator features use the current and preceding
event frames; longer history can only be carried through the learned recurrent state.

## Experimental repeated-QEC task [paper_fact]
Fact ID: alphaq-experimental-task
Source locator: Sec. 2.2; Appendix A.1.3
PDF page: 7
Claim: The experimental evaluation uses public Sycamore X- and Z-basis surface-code memory experiments at distance 3 in four chip regions and distance 5 in one region, with 50,000 shots for every total cycle count in `{1,3,...,25}`.

Each record contains repeated stabilizer syndromes and terminal data-qubit measurements from which
the final in-basis stabilizers and logical readout are computed.

## Experimental training and held-out split [paper_fact]
Fact ID: alphaq-experimental-split
Source locator: Sec. 2.2; Appendices A.1.3 and A.6.1
PDF page: 7
Claim: For each two-fold cross-validation direction, the model is pretrained on `2 x 10^9` samples from a detector error model fitted to one experimental half, fine-tuned on 19,880 records from that half, selected on another 5,120 records from the same half and finally evaluated on the opposite 25,000-record half.

The detector error models represent independent stochastic hyperedges fitted to experimental event
distributions. The final test half is not used for neural-network training or early stopping.

## Experimental decoder result [paper_fact]
Fact ID: alphaq-experimental-result
Source locator: Sec. 2.2 and Fig. 2
PDF page: 7
Claim: Averaged as declared across bases, cross-validation directions and distance-3 chip regions, the fine-tuned ensemble of 20 networks has reported LER `2.901 +/- 0.023%` at distance 3 and `2.748 +/- 0.015%` at distance 5, compared with `3.028 +/- 0.023%` and `2.915 +/- 0.016%` for the tensor-network decoder.

Figure 2 also reports higher LER values for MWPM-BP, MWPM-Corr and PyMatching on the same
experimental dataset. Fine-tuning and ensembling are both material to the best neural result; the
pretrained single-model condition is not the best bar.

## Logical-error-per-round definition [paper_fact]
Fact ID: alphaq-ler-definition
Source locator: Appendix A.2, Eqs. (2)–(5)
PDF page: 40
Claim: For variable-duration experiments, the source defines logical error per round by the ansatz `F(n) = (1 - 2 epsilon)^n` and obtains `epsilon` from a linear fit of log fidelity against cycle count, excluding the one-cycle point because of a stated boundary effect.

The displayed Sycamore fits use cycles 3 through 25 and have `R^2 >= 0.98`. A fixed-25-cycle
simulation instead obtains the per-round quantity by inverting the same fidelity ansatz.

## Experimental uncertainty aggregation [paper_fact]
Fact ID: alphaq-experimental-uncertainty
Source locator: Appendix A.3
PDF page: 42
Claim: Experimental fidelity points are bootstrapped and their errors are propagated in quadrature, while the spread among the constituent bases, folds and chip regions is deliberately excluded from the aggregated uncertainty estimate.

The reported plus/minus values therefore characterize the source's declared fidelity-resampling and
fit procedure; they do not include dataset-to-dataset hardware heterogeneity.

## Synthetic analog-readout transform [paper_fact]
Fact ID: alphaq-soft-readout-transform
Source locator: Appendix A.1.6 and Fig. S4
PDF page: 34
Claim: The simulated analog channel maps a noiseless measurement state to a one-dimensional I/Q-like sample and then, using known point-spread functions and priors, computes `post1 = P(|1> | not leaked)` and `post2 = P(leaked)` as network inputs.

The point-spread functions are parameterized by signal-to-noise ratio and normalized measurement
time. The model includes `|1> -> |0>` and `|2> -> |1>` decay tails but omits the second-order
`|2> -> |1> -> |0>` process.

## Soft-event construction [paper_fact]
Fact ID: alphaq-soft-event-construction
Source locator: Appendix A.1.7, Eq. (1)
PDF page: 36
Claim: Posterior stabilizer-measurement probabilities are converted into probabilistic detection events by the Bernoulli probability that consecutive measurements differ, providing a soft analogue of the binary XOR event.

At exact one-half measurement probability the recurrence used to invert soft events is singular.
The source reports better network results from direct measurement inputs than event-only inputs even
though the corresponding binary descriptions are information-equivalent under the stated initial
frame.

## Terminal-input label safeguard [paper_fact]
Fact ID: alphaq-label-safeguard
Source locator: Appendix A.1.8
PDF page: 38
Claim: The source thresholds terminal data-qubit and leakage values before deriving final-round stabilizer inputs because floating-point terminal values otherwise let the network infer the logical label from an overcomplete map.

The safeguard is applied in both hard- and soft-input conditions. Posterior probabilities for final
data-qubit measurements are also withheld from soft MWPM-Corr.

## Pauli+ representation and leakage removal [paper_fact]
Fact ID: alphaq-pauli-plus-model
Source locator: Appendix A.1.9
PDF page: 39
Claim: Pauli+ uses a Pauli-frame representation augmented by stochastic leakage states, Pauli-twirled qubit-subspace channels and Pauli-twirled crosstalk correlations on groups of as many as four qubits.

Leakage is introduced through CZ dephasing, heating and the crosstalk unitary. It is removed by
multilevel reset after measurement, data-qubit leakage-removal operations every syndrome cycle and
passive decay. The simulated noise strengths are described as a medium-term superconducting-device
profile rather than measurements from the Sycamore evaluation.

## Simulated soft-input comparison [paper_fact]
Fact ID: alphaq-soft-input-result
Source locator: Sec. 2.3.1 and Fig. 3a
PDF page: 9
Claim: In SI1000 simulations augmented with the synthetic I/Q channel, separately trained soft-input versions of both the recurrent neural decoder and MWPM-Corr have lower reported LER than their respective hard-input versions over the displayed readout-noise settings.

The same circuit-noise and I/Q parameter settings are used within each plotted hard/soft contrast.
This is evidence for use of additional per-shot readout information, not for benefit from longer
temporal history.

## Simulated leakage-input comparison [paper_fact]
Fact ID: alphaq-leakage-input-result
Source locator: Sec. 2.3.2 and Fig. 3b–c
PDF page: 10
Claim: In 25-cycle Pauli+ simulations at SNR 10, normalized measurement time 0.01 and 0.1% stabilizer-readout leakage, adding a binary leakage channel slightly improves the neural decoder over its hard/no-leakage-input condition, and supplying probabilistic readout and leakage inputs improves it further.

At distance 7, increasing simulated leakage from zero to 0.1% raises the soft-plus-leakage neural
LER by about 30%, compared with a roughly 60–80% penalty for leakage-unaware MWPM-Corr in the
source's relative comparison. The paper leaves comparison with a leakage-aware matching decoder to
future work.

## Simulated distance reach and training convergence [paper_fact]
Fact ID: alphaq-scaling-result
Source locator: Sec. 2.3.2 and Fig. 3b; Appendices A.6.3 and A.6.6
PDF page: 10
Claim: Pauli+ models are trained and evaluated at distances 3, 5, 7, 9 and 11; most neural points use `2 x 10^9` seen samples, whereas the highlighted distance-11 result is continued to `10^10` samples because training there had not converged at two billion.

The reported distance-11 LER after extended training is `5.37 +/- 0.01 x 10^-6`, compared with
`6.74 +/- 0.02 x 10^-6` for soft MWPM-Corr. The corresponding distance-3-to-11 suppression factors
are `4.28 +/- 0.02` and `4.33 +/- 0.04`; the source emphasizes that neural performance depends on
training duration.

## Same-model round-horizon extrapolation [paper_fact]
Fact ID: alphaq-round-horizon
Source locator: Fig. 4; Appendix B.2 and Fig. S14
PDF page: 13
Claim: Distance-specific recurrent decoders trained on Pauli+ examples of at most 25 cycles are applied without changing the architecture to the same Pauli+ setting at as many as 100,000 cycles, with LER shown only while the corresponding fidelity exceeds 0.1.

Both training and test use SNR 10, normalized measurement time 0.01 and 0.1% leakage. The plotted
records are generated from the same simulated experiments stopped after different cycle counts.
This is round-horizon extrapolation within one model family, not cross-device or cross-noise transfer.

## Constant recurrent resource with elapsed rounds [paper_fact]
Fact ID: alphaq-time-state-cost
Source locator: Appendix B.2
PDF page: 61
Claim: Once initialized, the recurrent decoder uses the same amount of state memory and computation for a late round as for an early round, whereas the PyMatching implementation used by the source receives the entire accumulated graph.

The paper does not compare against a streaming matching implementation and leaves that comparison to
future work.

## Architecture and input ablations [paper_fact]
Fact ID: alphaq-ablation-scope
Source locator: Appendix B.4 and Fig. S15
PDF page: 62
Claim: Five-seed ablations replace the syndrome-transformer core with a six-layer LSTM or remove or simplify convolution, attention-bias, input-stack, readout, pooling, auxiliary-loss, dimension, layer, measurement-input and event-input components; none of the listed controls removes the recurrent state.

The LSTM replacement remains recurrent, and none of the listed controls removes the recurrent state,
limits the accessible temporal window or randomizes cycle order. Other hyperparameters are not
retuned, and the authors note that compensating changes could recover some lost performance.

## Pretraining-model mismatch diagnostic [paper_fact]
Fact ID: alphaq-pretraining-mismatch
Source locator: Appendix B.5 and Fig. S17
PDF page: 66
Claim: On Sycamore evaluation data, pretraining on a detector error model fitted to the experiment outperforms pretraining on event-density-matched SD6 or SI1000, while fine-tuning each pretrained model on experimental records narrows the performance gap.

The matched DEM pretraining uses two billion examples, whereas SD6 and SI1000 pretraining is stopped
after 500 million and uses five seeds rather than 20. This comparison diagnoses pretraining-model
sensitivity and adaptation; it is not fixed-decoder transfer to an independent device.

## Compute-time benchmark [paper_fact]
Fact ID: alphaq-throughput
Source locator: Sec. 2.5.2; Appendix A.8 and Fig. S9
PDF page: 15
Claim: The source measures batch-1 computation time per QEC cycle for its unoptimized neural decoder on TPU hardware and for PyMatching on an Intel Xeon Platinum 8173M CPU, excluding the latency from the terminal input to the final answer.

The neural implementation is reported to remain about one to two orders of magnitude from the cited
one-microsecond superconducting target through the shown distances. Timing extends through distance
25, but the hatched region above distance 11 contains neural models that were neither trained nor
shown to decode accurately. The comparison also uses different processor classes.

## Training-data scaling [paper_fact]
Fact ID: alphaq-training-resources
Source locator: Sec. 2.5.3; Appendix B.6 and Fig. S18
PDF page: 15
Claim: The number of simulated examples required for the neural decoder first to reach parity with matching increases by roughly two orders of magnitude between distance 3 and distance 11 in the reported Pauli+ training curves.

The source extrapolates that distance-25 parity with MWPM-Corr might require `10^13–10^14`
pretraining examples. Figure S18 uses five seeds and reports their standard deviation for the first
parity-crossing sample count.

## Calibrated output and postselection [paper_fact]
Fact ID: alphaq-postselection
Source locator: Sec. 2.4 and Fig. 5
PDF page: 13
Claim: On one billion 25-cycle Pauli+ samples, the ensembled network output is used as a confidence score, and rejecting the least-confident 0.2% of distance-11 records reduces the postselected error rate by about tenfold, while rejecting 10% reduces it by about 250-fold.

Calibration curves use bootstrap error bars, and postselection bins use standard errors of their
values. This is a conditional-selection result on simulated records, not improved unconditional QEC
performance or a physical memory-control intervention.

## Temporal-memory observation boundary [literature_gap]
Fact ID: alphaq-gap-observation
Source locator: Secs. 2.1–2.5; Appendices A–B
PDF page: 4
Claim: The source does not report a temporal-correlation statistic, inferred memory timescale or formal non-Markovianity test for the Sycamore records.
Gap scope: source_local

Processing a multiround syndrome sequence with a recurrent state is not itself an observation that
the underlying physical noise has memory.

## Physical-attribution boundary [literature_gap]
Fact ID: alphaq-gap-attribution
Source locator: Secs. 2.2–2.3; Appendix A.1.9
PDF page: 7
Claim: The source does not identify a microscopic carrier responsible for temporal structure in the experimental records or causally attribute the experimental neural-decoder advantage to leakage, crosstalk, analog readout or another physical mechanism.
Gap scope: source_local

The explicit soft-readout and leakage-input contrasts are synthetic; the experimental result uses the
available Sycamore syndrome-record inputs and combines several modeling and training choices.

## Matched history-benefit boundary [literature_gap]
Fact ID: alphaq-gap-history-benefit
Source locator: Sec. 2.1; Appendix B.4
PDF page: 4
Claim: The source does not compare otherwise-matched decoders with and without recurrent history access, with different fixed history windows, with shuffled cycle order or with and without an explicit inferred memory state.
Gap scope: source_local

The LSTM ablation substitutes one recurrent core for another. The decoder-family, input-modality and
architecture comparisons therefore cannot establish that memory awareness causes the reported
performance gain.

## Transferability boundary [literature_gap]
Fact ID: alphaq-gap-transfer
Source locator: Fig. 4; Appendices B.2 and B.5
PDF page: 13
Claim: The source does not deploy one fixed trained decoder across an independent device, code family, code distance or distinct calibrated physical-noise regime without adaptation.
Gap scope: source_local

The 25-to-100,000-cycle result remains within the same distance-specific Pauli+ setting, and the
pretraining-noise comparison relies on experimental fine-tuning to narrow mismatch.

## Real-time boundary [literature_gap]
Fact ID: alphaq-gap-realtime
Source locator: Sec. 2.5.2; Appendix A.8
PDF page: 15
Claim: The source does not demonstrate real-time decoding integrated with a quantum processor or report end-to-end feedback latency.
Gap scope: source_local

Its timing isolates compute time per cycle, excludes final-answer latency and benchmarks different
decoder families on different processor classes.

# Claim audit — Bausch et al. recurrent syndrome-transformer decoder

## Fixed source and reading scope

- Fixed artifact: `outputs/overview/literature/final_expansion/sources/2310.05900.pdf`
- Identity: arXiv:2310.05900v1, *Learning to Decode the Surface Code with a Recurrent,
  Transformer-Based Neural Network*, Johannes Bausch and coauthors, posted 9 October 2023.
- Artifact verification: PDF 1.5, 68 pages, 2,005,758 bytes, SHA-256
  `6c38f70abfa12a3f622420fc0dc9ca18cc2086e9b0fc35014b3f6bcab298591c`.
- Reading scope: all 68 pages, including the main text, Materials and Methods, Supplementary Text,
  figures, tables and references. The older local AlphaQubit note and downstream manuscript material
  were treated as discovery residue, not evidence or reusable prose.
- Review status: source review by `/root/expand_decoder_benefit`, 2026-08-05; draft and audit only,
  with no corpus-admission decision.
- Visual verification: artifact pages 1, 4–10, 13, 15, 34, 36, 38–40, 42, 49, 56, 61–62,
  64, 66 and 68 were
  rendered from the fixed PDF. The checks covered source identity, recurrent state and input paths,
  the experimental comparison, simulated soft/leakage contrasts, long-round evaluation, LER
  definition, statistics, held-out split, compute-time benchmark, architecture/input ablations and
  training-sample scaling.

## Claim-separation audit

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| H1 — access to a multiround record | Main Sec. 2.1 and Fig. 1, PDF pp. 4–6; Appendix A.4, pp. 42–47 | A fixed recurrent block updates a per-stabilizer decoder state each cycle from current stabilizer inputs; the state represents information from preceding cycles and can be read out after a variable number of rounds. | The architecture alone does not show that the physical noise is non-Markovian, that long-range history is used, or that long-history access causes its accuracy advantage. | closed for decoder representation and information access only |
| O1 — observation of temporal memory in hardware | Main Sec. 2.2, pp. 7–8; Appendices A.1.3 and A.6.1, pp. 29 and 48–49 | The decoder is evaluated on multicycle Sycamore surface-code records extending to 25 rounds. | The source does not estimate a temporal-correlation statistic, identify a memory timescale or test a formal non-Markovianity criterion in those records. | missing |
| A1 — physical attribution | Main Secs. 2.2–2.3, pp. 7–12; Appendix A.1.9, pp. 38–39 | Leakage, crosstalk and analog readout are explicitly represented in the Pauli+ and I/Q simulations; the experimental decoder is trained and tested on Sycamore data. | The soft-I/Q and explicit leakage-input comparisons are simulated, not measurements of the microscopic cause of the experimental records. No candidate memory carrier is intervened upon in the hardware comparison. | missing |
| E1 — decoder performance on experimental repeated-QEC data | Main Sec. 2.2 and Fig. 2, pp. 7–8; Appendices A.1.3, A.3 and A.6.1, pp. 29, 42 and 48–49 | On held-out folds of the Sycamore distance-3 and distance-5 memory-experiment dataset, the reported fine-tuned ensemble LER is lower than the reported TN, MWPM-BP, MWPM-Corr and PyMatching values. | The comparison does not isolate recurrence, history length, soft readout or leakage access; fine-tuning and a 20-model ensemble are material parts of the best result. | closed for source-local decoder performance, not for a memory mechanism |
| I1 — benefit from soft readout and leakage side information | Main Sec. 2.3 and Fig. 3, pp. 9–12; Appendices A.1.6–A.1.9, pp. 33–39; B.3, p. 62 | In fixed simulated noise families, separately trained ML models improve when given probabilistic readout and leakage inputs; soft MWPM-Corr also improves relative to hard MWPM-Corr. Within the ML family, hard/no-leakage, hard/leakage and soft/leakage inputs are compared. | These contrasts do not isolate access to long temporal history. The I/Q channel is a synthetic per-measurement readout model, the Pauli+ leakage is actively removed each cycle, and a leakage-aware matching comparator is left to future work. | closed narrowly for simulated input-information benefit |
| B1 — benefit from memory-aware decoding | Main Secs. 2.1–2.3, pp. 4–12; Appendix B.4 and Fig. S15, pp. 62–65 | The decoder is recurrent, and architecture/input ablations replace the core with another recurrent LSTM or alter components and input encodings. | There is no otherwise-matched comparison that removes the recurrent state, truncates the accessible history, randomizes temporal order or supplies/withholds an explicit inferred memory state. The reported decoder advantages therefore cannot be assigned to memory awareness. | missing |
| T1 — transfer to longer round horizons | Main Fig. 4, p. 13; Appendix B.2 and Fig. S14, pp. 61–62 | Fixed distance-specific recurrent models trained on Pauli+ experiments of at most 25 cycles are applied to the same Pauli+ setting for as many as 100,000 cycles, with LER plotted only while fidelity exceeds 0.1. Per-round decoder time and state size do not grow with elapsed round count. | Training and testing share the same simulated noise model, distance, input construction and experiment family; the trajectories are generated as the same simulated experiments stopped at different times. This is not transfer across device, code, decoder, physical mechanism or independently calibrated noise. | closed only for same-model round-horizon extrapolation |
| R1 — robustness to model mismatch | Appendix B.5 and Fig. S17, pp. 66–67 | Pretraining on an experimental-fitted DEM performs better on Sycamore data than pretraining on SD6 or SI1000, while fine-tuning each pretrained model on experimental data narrows the differences. | A fixed decoder is not deployed without adaptation across independent devices or operating regimes, and the comparison does not establish a quantitative robustness range for temporal-memory misspecification. | missing for transfer-style robustness; source supplies a mismatch-sensitivity diagnostic |
| U1 — uncertainty and held-out evaluation | Main Fig. 2, pp. 7–8; Appendices A.2–A.3 and A.6.1, pp. 40–42 and 48–49 | The experimental folds separate ML training/early stopping from the final 25,000-shot test half. LER is fitted from log fidelity, and source-reported uncertainties are derived from bootstrapped fidelity points and Gaussian propagation. | For aggregated experimental results, the error estimate deliberately excludes spread across bases, folds and chip regions. The reported plus/minus values are therefore not evidence of robustness to dataset heterogeneity. | closed for declared evaluation and uncertainty procedure, with the stated exclusion |
| C1 — throughput and resource reach | Main Secs. 2.5.2–2.5.3, pp. 15–16; Appendices A.8 and B.6, pp. 55–57 and 67–68 | Batch-1 TPU compute time per cycle is benchmarked separately from PyMatching CPU time; the unoptimized ML implementation is stated to remain about one to two orders of magnitude from a 1-microsecond target. Training data to reach matching parity grows by roughly 100-fold from distance 3 to 11, and distance-25 parity is extrapolated to require `10^13–10^14` examples. | The timing excludes final-answer latency, distances above 11 are untrained, hardware differs between decoder families and no real-time hardware deployment is demonstrated. | closed for measured compute-time and training-resource limitations |

## Operation replay

| input | transformation | assumption or control | output | exact source location | replay status |
|---|---|---|---|---|---|
| One cycle of stabilizer measurements and/or detection events, optionally with soft and leakage channels | Embed each stabilizer, add it to its prior per-stabilizer decoder state and update that state with three syndrome-transformer layers; after the terminal stabilizers, apply the readout network | The same recurrent block is reused each cycle and the state dimension is fixed; learned attention, convolutions and several input features are combined | A probability for the logical-error label after a variable-length record | Main Sec. 2.1 and Fig. 1, pp. 4–6; Appendix A.4, pp. 42–47 | complete |
| Sycamore distance-3 and distance-5 X/Z memory records at `n in {1,3,...,25}` | Split each 50,000-shot dataset into even/odd folds; pretrain on `2 x 10^9` DEM samples fitted to one fold; fine-tune on 19,880 experimental records and select on 5,120; evaluate on the opposite 25,000-record fold; reverse folds for cross-validation | The DEM accompanying each fold was fitted to that fold; the opposite fold is not used for ML training or early stopping | Held-out experimental LER for each decoder condition | Main Sec. 2.2, p. 7; Appendices A.1.3 and A.6.1, pp. 29 and 48–49 | complete |
| Fidelity at experiment lengths 3 through 25 | Fit `log F(n) = log F_0 + n log(1 - 2 epsilon)`, excluding the one-cycle point | The fit uses a constant-LER ansatz; all displayed experimental fits have `R^2 >= 0.98`, and departures of the intercept are used as a fit diagnostic | Logical error per round `epsilon` and source-reported fit uncertainty | Appendix A.2 and Fig. S5, pp. 40–41 | complete |
| Experimental results across bases, folds and chip regions | Bootstrap individual fidelity points and propagate their errors in quadrature when aggregating | Spread among the 16 distance-3 or 4 distance-5 constituent datasets is deliberately discarded | Error bars for the aggregated experimental LER | Appendix A.3, p. 42 | complete |
| Synthetic measured state and one-dimensional analog readout `z` | Sample state-conditioned I/Q-like distributions and convert `z` with priors into `post1 = P(|1> | not leaked)` and `post2 = P(leaked)`; also form soft temporal-difference inputs | The |2> decay model is simplified; second-order `|2> -> |1> -> |0>` decay is omitted; priors and point-spread functions are known to the input transform | Probabilistic measurement, event, leakage and leakage-event inputs | Appendices A.1.6–A.1.7, pp. 33–38 | complete |
| Final data-qubit measurements in a memory experiment | Threshold final-round data-qubit and leakage values before deriving terminal stabilizers | Soft terminal values otherwise let the network reconstruct the logical label from an overcomplete floating-point map | Terminal inputs that withhold the label-level information identified by the authors | Appendix A.1.8, p. 38 | complete |
| Pauli+ surface-code simulation at distances 3, 5, 7, 9 and 11 | Pauli-frame propagation with stochastic leakage states, Pauli-twirled gate channels and Pauli-twirled crosstalk correlations on as many as four qubits; add synthetic I/Q noise in post-processing | Leakage is removed by multilevel reset after measurement, data-qubit leakage removal every syndrome cycle and passive decay; the model is a forecasted superconducting profile rather than a hardware measurement | Twenty-five-cycle simulated records with controllable leakage and readout input modalities | Appendix A.1.9, pp. 38–39; Appendix A.6.3, p. 50 | complete |
| Hard/soft and leakage/no-leakage input variants | Train separate models under the same declared Pauli+ family and compare LER with PyMatching and hard/soft MWPM-Corr | ML results use five-seed ensembles; most use `2 x 10^9` seen samples, while the highlighted distance-11 result uses `10^10`; leakage-aware matching is not tested | Input-modality and decoder-family performance contrasts through distance 11 | Main Sec. 2.3 and Fig. 3, pp. 9–12; Appendix A.7, p. 55; Appendix B.3, p. 62 | complete |
| A fixed Pauli+ decoder trained on examples of at most 25 cycles | Recurrently process simulations stopped at increasing cycle counts through 100,000 | Training and test use the same distance-specific Pauli+ setting; LER is shown only where fidelity is greater than 0.1 | Same-model round-horizon curves for ML, MWPM-Corr and PyMatching | Main Fig. 4, p. 13; Appendix B.2 and Fig. S14, pp. 61–62 | complete |
| Architecture and input variants | Retrain five seeds after replacing the transformer core with six LSTMs or removing/simplifying named modules and input types | Hyperparameters other than the ablated component are not retuned; the authors state that some lost performance might be recovered by compensation | Fig. S15/S16 ablation results | Appendix B.4 and Figs. S15–S16, pp. 62–65 | complete |
| Batch-1 decoder inference on present hardware | Measure computation time per round for ML on TPU and PyMatching on an Intel Xeon Platinum 8173M CPU, then fit code-distance scaling | Latency after the terminal input is excluded; ML instances beyond distance 11 are untrained | Fig. S9 compute-time comparison and 95% fit interval | Appendix A.8 and Fig. S9, pp. 55–57 | complete |

## Evidence interpretation for the overview

This source is a concrete decoder approach for Section 3 because its four relevant layers can be
separated without inventing a unified pipeline:

- **Memory-bearing representation:** a learned, fixed-size recurrent decoder state updated once per
  syndrome cycle. This is memory in the algorithmic representation, not evidence that the device
  dynamics satisfy a strict non-Markovianity definition.
- **QEC-facing variables:** stabilizer measurements and detection events, optionally augmented by
  posterior readout and leakage probabilities; the returned quantity is a logical-error probability.
- **Computation:** recurrent transformer layers, learned attention biases, spatial convolutions and a
  terminal readout network, trained by supervised learning.
- **Demonstrated reach:** held-out Sycamore distance-3/5 decoding; Pauli+ and I/Q simulation through
  distance 11; same-model round-horizon application through 100,000 cycles; compute timing through
  distance 25 although models above distance 11 are untrained.

For Section 5, the strongest defensible result is experimental decoder performance on held-out
repeated-QEC records. The source does not close an observation claim about temporal correlation, an
attribution claim about a physical memory carrier, or a causal claim that recurrent history access
produces the decoder gain. Simulated soft/leakage input benefits and narrow round-horizon
extrapolation should be reported separately from the experimental result.

## Competing explanations and kill conditions

### Competing explanations for decoder performance

- The experimental best result combines recurrent architecture, transformer/convolutional spatial
  processing, both measurements and events, DEM pretraining, experimental fine-tuning and an
  ensemble of 20 models. No reported comparison isolates long-history access from those factors.
- The Pauli+ gains can reflect spatial crosstalk structure, richer per-shot readout information,
  explicit leakage indicators, network capacity or training, rather than multicycle memory.
- In Fig. S15, replacing the syndrome transformer with an LSTM preserves recurrence, while the
  remaining ablations alter architecture or input encoding. None is a no-history control.
- Soft MWPM-Corr also benefits from soft inputs, showing that probabilistic readout information is
  not uniquely tied to the recurrent network.

### Kill conditions

- Kill any statement that AlphaQubit observes or identifies temporal memory in Sycamore hardware;
  it decodes multiround records but does not report a temporal-memory diagnostic.
- Kill any statement that its experimental advantage is caused by soft readout or leakage inputs;
  those explicit input comparisons are performed in simulation.
- Kill any statement that recurrence or long-history access is responsible for the decoder gain;
  the source has no matched no-history or history-window ablation.
- Kill any statement that long-round generalization demonstrates device, noise-model, code or
  mechanism transfer; training and testing remain within the same distance-specific Pauli+ setting.
- Kill any statement that the Pauli+ result establishes persistent leakage across QEC cycles;
  the simulated protocol removes leakage every syndrome cycle, in addition to measurement reset and
  passive decay.
- Kill any claim of real-time operation. The measured quantity excludes latency, uses an unoptimized
  batch-1 TPU implementation and remains roughly one to two orders of magnitude from the cited
  superconducting target.
- Kill any claim that the uncertainty bars capture hardware heterogeneity; the source explicitly
  excludes spread among bases, folds and chip regions from the aggregated experimental estimate.
- Kill any claim of broad transferability beyond the tested device dataset and matched simulation
  families.
- Kill any equation of a recurrent computational state, temporal correlation, leakage, drift or
  strict quantum non-Markovianity.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted
- H1: closed only for recurrent access to a multiround syndrome record
- O1: missing; no temporal-memory observation or timescale is reported
- A1: missing; no microscopic memory carrier is identified in the experimental data
- E1: closed for held-out experimental decoder performance under the declared training procedure
- I1: closed narrowly for simulated soft-readout/leakage-input benefits
- B1: missing; there is no matched history-access comparison
- T1: closed narrowly for same-Pauli+ round-horizon extrapolation, not broad transferability
- R1: missing for fixed-decoder robustness across independently changed regimes
- U1: closed for the declared split and uncertainty calculation, with cross-dataset spread excluded
- C1: closed for measured compute-time and training-resource limitations; real-time deployment is
  absent
- downstream status: audit and source-note draft only; no admission decision was made

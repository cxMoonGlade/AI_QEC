# Claim audit — Stein et al. on calibration-conditioned transfer in IBM repetition-code decoding

## Fixed source and reading scope

- Fixed artifact: `outputs/overview/literature/coverage_validation/stein_download/PDFs/Calibration-Conditioned_FiLM_Decoders_for_Low-Latency_Decoding_of_Quantum_Error_Correction_Evaluated_on_IBM_Repetition-Code_Experiments.pdf`
- Identity: arXiv:2601.16123v1, *Calibration-Conditioned FiLM Decoders for Low-Latency
  Decoding of Quantum Error Correction Evaluated on IBM Repetition-Code Experiments*, Samuel
  Stein and eight coauthors, submitted 22 January 2026.
- Lawful acquisition: official arXiv PDF via the open-access URL
  `https://arxiv.org/pdf/2601.16123v1`, with Supporting Information disabled for this download.
- Artifact verification: PDF 1.7, 18 pages, 696,762 bytes, SHA-256
  `f09848cdf8ed099ebf213750bdbf397a92659f04c4e8c6e5177454821b3de50e`.
- Version verification: the title-page margin states `arXiv:2601.16123v1 [quant-ph] 22 Jan 2026`;
  the official arXiv version page listed only v1 at review time.
- Reading scope: all 18 pages, including the main text, Appendix A, all eight tables, all seven
  figures and references.
- Visual checks: pages 1–18 were rendered and traversed. Equations (1)–(8), Algorithm 1, Figs. 1
  and 4–7, the latency comparison in Table I, the split/model specification in Table II, the LER
  values in Tables III–VI and the FiLM-mode tables were checked against the text.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| T1 — frozen-model transfer | Secs. I, III.B, IV.A/C and VI; Tables V–VI, PDF pp. 2, 6, 9, 12, 15–16 | For each fixed basis and `(d,r)`, learned parameters trained on pooled Fez, Kingston and Pittsburgh shots are evaluated without retraining or fine-tuning on independently selected Kingston chains with calibration snapshots acquired one week later; the new target calibration graph is supplied to the fixed GCN/FiLM mapping. | Kingston is already represented in the training pool; there is no leave-one-device-out test. A separate model is trained for every basis and `(d,r)`, so there is no cross-distance, cross-round or cross-code transfer. The effective CNN weights are recalculated from each target calibration rather than held calibration-blind. | closed only for fixed-learned-parameter, target-calibration-conditioned transfer across unseen chains and a later operating snapshot on a seen device; cross-device/cross-code transfer remains missing |
| F1 — representation/interface/computation frame | Secs. II.C–III and Fig. 1, pp. 3–6 | The source separates the ordered detector history, target calibration graph, per-qubit correction interface, GCN/FiLM/CNN computation and repetition-code hardware reach. | The phrase “without retraining” does not reveal that target calibration still changes FiLM parameters and folded effective CNN weights, or that training is separate per basis and `(d,r)`. | no ontology failure, but a visible calibration/training/adaptation-protocol dimension is required for transfer comparisons |
| D1 — hardware memory-conditioned decoder benefit | Secs. II.A, II.C, III.B and IV.C; Eq. (2); Tables V–VI, pp. 3–6, 9, 15–16 | Both neural arms read the same multiround detection-event history, and FiLM+CNN is compared with an otherwise architecturally identical CNN on hardware LER; the added information is the current calibration graph. | The contrast does not add or remove access to record history, a continuing carrier or a declared memory state. Calibration drift is not modeled as a transition law, and no microscopic temporal cause is identified. | missing for memory-conditioned benefit; closed for hardware calibration-conditioning benefit under a matched neural comparator |
| D2 — population-level matched decoder comparison | Secs. II.C, III.B and IV.A/C; Figs. 6–7 and Tables V–VI, pp. 4–10, 15–16 | FiLM+CNN and CNN use the same backbone, loss, optimizer, split and threshold and differ by the calibration encoder/FiLM path; the source reports a broad configuration grid with 95% bands, and selected deeper configurations show lower FiLM LER. | The target chain/snapshot population, selection and exclusion rules, per-cell shot counts, pairing and inferential aggregation are not defined. FiLM ordering is configuration-dependent rather than uniformly better, and the 30% validation partition is used for checkpoint selection before its LER is reported. | strong configuration-wide matched hardware calibration-conditioning evidence; not closed as a population-level claim and does not isolate temporal-memory access |
| R1 — robustness to a wrong memory model | Full method/evaluation scope; Secs. IV.C and V, pp. 6–12 | Fixed learned parameters are applied to later, recalibrated hardware snapshots and unseen chains using their current calibration features. | No memory kernel, carrier dynamics or hidden-state transition is specified or deliberately misspecified; there is no missing/biased/stale-calibration ablation. | missing for wrong-memory-model robustness; qualified for calibration-shift adaptation with fresh target metadata |
| M1 — temporal-memory specificity | Secs. I–III; Eqs. (2)–(7), pp. 1–6 | The CNN consumes the full ordered detection history, while calibration snapshots represent slow spatial and temporal hardware variation over hours or days. | The paper does not estimate a calibration trajectory, transition kernel, memory time, quantum non-Markovianity or a causal physical mechanism for multicycle dependence. Statements about non-Markovian or parasitic correlated errors are interpretations, not measured model variables. | missing as a temporal-memory-law study; relevant as drift-conditioned multiround decoding |
| U1 — metric and uncertainty | Sec. IV.A; Figs. 4–7; Tables III–VI, pp. 7–9, 14–16 | The hardware metric is logical error rate after a predicted per-qubit frame update and majority vote; the figures display 95% confidence bands, and the corpus totals 2,760,704 shots over 400 chain/calibration snapshots. | Shot counts and interval endpoints are not tabulated per `(device,basis,d,r,snapshot)`, and the source describes the intervals both as binomial 95% CIs and as CIs across calibration snapshots without defining the aggregation formula. | qualified uncertainty support; sufficient to avoid a point-estimate-only label, insufficient for exact reanalysis from the paper alone |
| L1 — latency and update cost | Secs. III.C and IV.D; Table I, pp. 6, 10 | On an Nvidia RTX 5000 at batch size one, 2,000 iterations after 500 warmups give approximately 81–98 microseconds per shot for folded FiLM/CNN and approximately 1.38–1.43 milliseconds for dynamic FiLM, with means and standard deviations reported. | The experiment is an offline GPU forward-pass benchmark, not an integrated control-stack or end-to-end QEC timing test; target-calibration encoding/folding update time is not separately measured. | closed for relative per-shot neural inference overhead, not real-time deployment latency |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Distance-`d` repetition-code experiment | Prepare an X- or Z-basis logical state, measure and reset `d-1` ancillas for `r` repeated rounds in one IBM dynamic circuit, then measure data qubits | The repetition code protects one Pauli basis and is used as a native heavy-hex testbed rather than as a surface-code implementation | Ancilla measurement sequence and terminal data readout | Sec. II.A; Figs. 2–3, PDF pp. 3, 7 | complete |
| Consecutive stabilizer outcomes `s_(t,i)` | Form `chi_(t,i)=s_(t,i) XOR s_(t-1,i)` with zero initial reference | The printed detector convention localizes changes from data and measurement faults | Ordered `r x (d-1)` detection-event tensor | Sec. II.A; Eq. (2), p. 3 | complete for the declared convention |
| Target contiguous qubit chain and calibration snapshot | Build a heavy-hex subgraph whose node/edge fields include normalized `T1`, `T2`, readout, one-qubit and two-qubit gate errors | Current calibration statistics are informative side information for the current hardware state | Calibration graph `G=(V,E)` | Secs. II.B and III.A; Fig. 1, pp. 3–5 | complete |
| Calibration graph | Apply a three-layer GCN and global mean pooling, then a two-layer MLP | A 256-dimensional pooled embedding can support chain-location-independent conditioning | Layer-wise FiLM scales and shifts | Algorithm 1; Eqs. (4)–(5), p. 5 | complete |
| Detection tensor and FiLM values | Apply three FiLM-modulated `3x3` convolution blocks and a dense per-qubit output head | Calibration-dependent channel modulation changes how a common convolutional feature library is used | Per-data-qubit flip probabilities | Algorithm 1; Eqs. (6)–(7), pp. 5–6 | complete |
| Per-qubit predictions | Threshold at 0.5, XOR into the tracked Pauli frame, combine with final data readouts and majority vote | Per-qubit BCE targets equal prepared bit string XOR measured data string | Corrected logical bit and LER | Secs. II.A and III.B; Eq. (8), pp. 3, 6 | complete |
| Fez, Kingston and Pittsburgh shot corpus | For each basis and each `(d,r)`, pool shots across devices, split 70:30, optimize BCE with Adam for 100 epochs and checkpoint on validation accuracy | The grouping unit is not specified, and the validation partition is used for model selection before its LER is reported | One trained FiLM model and one matched CNN model per basis and `(d,r)` | Secs. I and III.B; Sec. IV.A; Table II, pp. 2, 6, 13 | complete; validation is not an independent post-selection test and there is no cross-configuration model sharing |
| Same pooled train/validation split | Remove the hardware encoder and FiLM generator while preserving CNN backbone, loss, optimizer and threshold | This isolates calibration conditioning at the neural-package level | Unconditioned CNN comparator | Sec. II.C, pp. 4–5; Sec. III.B, p. 6 | complete |
| Target circuit and calibration | Build a separate circuit-level Pauli detector graph and weights for each device, basis, `(d,r)` and calibration snapshot using target `T1`, `T2`, gate and readout fields | Pauli-twirled calibration-derived channels are an adequate matching model | Modified calibration-informed MWPM comparator | Sec. II.C, p. 4 | complete within the declared reduction |
| Held-out 30% validation shots | Apply all three decoders at each basis and `(d,r)` | Validation shots were excluded from gradient training, but they selected checkpoints and snapshot/chain grouping is unstated | Configuration-dependent validation LER curves and Tables III–IV | Secs. IV.A–B; Figs. 4–5, pp. 7–9; Tables III–IV, pp. 14–15 | complete for printed aggregates; not an independent post-selection test |
| Independently selected Kingston chains and calibration snapshots acquired one week later | Feed each target calibration graph through the fixed GCN/FiLM mapping, fold the resulting modulation into the CNN and decode target records without retraining/fine-tuning | Kingston is a seen training device, while the physical chains and calibration snapshots are new; target calibration is available | Unseen-chain/later-snapshot LER curves and Tables V–VI | Sec. IV.C; Figs. 6–7, pp. 8–9; Tables V–VI, pp. 15–16 | complete; within-device, target-conditioned transfer only |
| Unseen Kingston `d=11,r=11` Z-basis records | Compare FiLM+CNN, target-calibrated MWPM and matched unconditioned CNN | All arms use the same target records; neural arms differ by calibration conditioning | LER `8.79e-3`, `6.52e-2` and `7.33e-2`, respectively | Table V, p. 15 | complete; FiLM gains 7.41x over MWPM and 8.33x over CNN |
| Unseen Kingston `d=11,r=11` X-basis records | Repeat the three-arm comparison | Same boundaries as the Z-basis comparison | LER `5.40e-2`, `1.18e-1` and `1.13e-1`, respectively | Table VI, p. 16 | complete; FiLM gains 2.19x over MWPM and 2.09x over CNN |
| Calibration values and trained FiLM mapping | Either recompute GCN/MLP per shot or precompute FiLM values and fold them into convolution weights | Calibration changes much more slowly than syndrome decoding; folded values remain valid until the next update | Dynamic or folded inference path | Secs. III.C and IV.D, pp. 6, 10 | complete |
| Batch-one forward passes on Nvidia RTX 5000 | Run 500 warmups then time 2,000 iterations | GPU kernel-launch overhead dominates the tested small networks | Mean and standard deviation per mode and `(d,d)` | Sec. IV.D and Table I, p. 10 | complete for this platform; not an integrated QEC latency test |

## Project application

This source changes the coverage judgment, but only after the word “transfer” is qualified precisely.

- **T1 change:** the corpus can no longer say that no frozen learned decoder has been tested under a
  later hardware operating snapshot without retraining. Stein et al. keep the learned GCN/FiLM/CNN
  parameters fixed and evaluate new Kingston chains one week later. The target calibration is still
  supplied and changes the FiLM values and folded effective CNN weights. The safe label is therefore
  **fixed-learned-parameter, target-calibration-conditioned within-device transfer**.
- **T1 remaining gaps:** this is not leave-one-device-out transfer because Fez, Kingston and
  Pittsburgh all contribute to the training pool and the later test uses Kingston. It is not
  cross-distance or cross-round transfer because each basis and `(d,r)` has its own model, and it is
  not cross-code transfer because only the 1D repetition code is tested.
- **Matched configuration-wide evidence:** FiLM+CNN versus CNN is a substantially cleaner hardware
  comparison than QAdapt versus Ising-fast: backbone, split, loss, optimizer and threshold are common,
  and a broad printed target grid is reported with uncertainty bands. The target chain/snapshot
  population and selection rule are not defined, and the ordering crosses with configuration. What
  the neural comparison isolates is calibration conditioning, not access to temporal history,
  because both arms see the same detection tensor.
- **Memory boundary:** the target metadata describe nonstationary drift snapshots, not a learned
  carrier transition law. A week-separated calibration test does not by itself establish a temporal
  memory mechanism, strict non-Markovianity or causal attribution of record correlations.
- **F1 consequence:** representation–interface–computation–reach remains a sound scientific frame,
  but it is not sufficient for transfer claims unless the comparison also states (i) how training is
  partitioned, (ii) what target-domain side information is supplied, (iii) whether learned parameters,
  calibration-conditioned effective parameters or both are frozen, and (iv) the granularity at which
  a separate model is trained. Add **calibration/training/adaptation protocol** as an explicit
  cross-cutting comparison column, not as a new memory-mechanism family.
- **Section placement:** this is a Section 5 decoder/transfer example and a boundary case for drift.
  It should not become one of the Section 3 memory-representation rows because it does not specify a
  generative temporal-memory model.

## Competing evidence and kill conditions

### Adjacent evidence

- QAdapt reports zero-shot application of a simulation-trained pre-decoder to Willow without target
  fine-tuning but changes architecture and training exposure relative to its baseline and omits LER
  uncertainty.
- Nayak et al. explicitly estimate a continuing latent quasiparticle field, but their proposed-decoder
  benefit is synthetic and event-selected rather than a population hardware comparison.
- Hockings et al. directly study decoder sensitivity to calibration/model mismatch, but a static
  calibration mismatch remains distinct from an incorrect temporal-memory law.

### Kill conditions

- Kill “unseen-device transfer.” Kingston contributes to the pooled training corpus and is the only
  device named for the one-week-later test.
- Kill “cross-code,” “cross-distance” or “one universal decoder.” A separate model is trained for
  each basis and `(d,r)`; the surface code is future work.
- Kill “calibration-free frozen transfer.” The target calibration graph is required to generate new
  FiLM values, which are folded into effective CNN weights.
- Kill a memory-conditioned-benefit claim. FiLM+CNN and CNN receive the same multiround record; the
  added information is static target calibration metadata.
- Kill causal microscopic attribution. The paper does not measure a memory carrier or discriminate
  drift, leakage, coherent accumulation and other sources of record structure.
- Kill strict non-Markovianity. “Non-Markovian errors” appears as an interpretation of deep-circuit
  behavior, not as a tested formal property or source variable.
- Kill universal decoder superiority. FiLM is worse than one or both baselines in several shallow
  `(d,r)` settings; the advantage appears mainly after the reported crossover.
- Kill sub-microsecond or control-stack latency. Folded inference measures roughly 81–98 microseconds
  per shot on a desktop-class GPU; FPGA/ASIC reductions are prospective.
- Kill an end-to-end adaptation-cost claim. The time required to encode a new calibration graph,
  produce FiLM values and fold them at each update is not reported separately.
- Kill exact uncertainty reconstruction. Confidence bands are plotted, but per-configuration shot
  counts, interval endpoints and a single unambiguous aggregation formula are absent.

## Source-local anomalies and reporting boundaries

- The abstract says the decoder achieves up to `11.1x` relative to MWPM “on these unseen
  experiments.” The exact `11.11x` value comes from the validation-set Z-basis `d=11,r=11` row in
  Table III. In the one-week-later Kingston Table V, the same configuration gives `7.41x`; the largest
  tabulated MWPM gain there is about `9.09x` at `d=11,r=9`.
- Sec. IV.C first says the unseen X-basis `d=11,r=11` gain over MWPM is `2.09x`, then the following
  bullet says `2.19x`. Table VI supports `2.19x` over MWPM (`0.118/0.054`) and `2.09x` over CNN
  (`0.113/0.054`).
- Sec. IV.C calls `7.41x` the unseen Z-basis gain “up to” `d=11,r=11`, but Table V contains the larger
  approximately `9.09x` MWPM gain at `d=11,r=9`.
- “A single trained model” in the abstract/conclusion means one model within a fixed basis and
  `(d,r)` setting; Secs. I, II.C, III.B and IV.A explicitly require separate models across these
  configurations.
- The main evaluation text calls the plotted uncertainty “binomial 95% confidence intervals,” while
  the unseen Fig. 6 caption calls the bands “95% CIs across calibration snapshots.” The source does
  not state whether these are two descriptions of one estimator or different interval constructions.
- The 70:30 validation split is pooled across devices, but the full text does not state whether the
  split unit is a shot, chain or calibration snapshot. The separate one-week test does explicitly use
  independently selected chains.
- The 30% partition is used to select checkpoints by validation accuracy before its LER is reported;
  it is excluded from gradient training but is not an independent post-selection test.
- FiLM superiority is configuration-dependent. Tables III–VI contain shallow and intermediate
  settings in which MWPM, CNN or both have lower LER; the strongest FiLM gains occur in selected
  deeper settings rather than every printed row.
- The paper says it provides the experimental dataset and raw IBM archives, but the fixed PDF gives
  no repository identifier, URL or data-availability section from which those artifacts can be
  resolved.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: unpersisted pending independent source-only review and corpus admission
- T1: closed only for within-seen-device, unseen-chain/later-snapshot transfer with fixed learned
  parameters and fresh target calibration conditioning
- F1: frame retained, but calibration/training/adaptation protocol must become an explicit comparison
  dimension
- D1: missing for hardware memory-conditioned benefit; hardware calibration-conditioning benefit is
  supported by a matched CNN comparator
- D2: strong configuration-wide matched calibration-conditioning evidence, but not a closed
  population-level claim
- R1: missing for wrong-memory-model robustness
- M1: temporal-memory law and causal attribution missing
- U1: qualified uncertainty support
- L1: closed only for relative GPU inference overhead, not integrated QEC latency

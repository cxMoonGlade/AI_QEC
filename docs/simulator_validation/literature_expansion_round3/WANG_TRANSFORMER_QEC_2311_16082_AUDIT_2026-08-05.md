# Claim audit — Wang et al. on cross-distance Transformer-QEC transfer

## Fixed source and reading scope

- Fixed source: Hanrui Wang et al., *Transformer-QEC: Quantum Error Correction Code Decoding
  with Transferable Transformers*, arXiv:2311.16082v1, submitted 27 November 2023 and listed by
  arXiv as accepted to the ICCAD 2023 FAST ML for Science Workshop.
- Official-current PDF: 7 pages, 2,276,718 bytes, SHA-256
  `cc4a5fce3676648a1cfd8cc378ac4bf0a8b994294cef02acff18422696f30aa1`. A fresh hash of
  `https://arxiv.org/pdf/2311.16082v1` matched the local artifact on 5 August 2026. The arXiv
  version history contains only v1 and supplies no separate Supplementary Information file.
- Reading scope: all seven pages, including all eight figures, three tables, equations, methods,
  evaluation text and references. All pages were rendered and visually checked. The transfer
  protocol, Table 1, Figs. 7--8 and Tables 2--3 were checked against the rendered pages rather than
  accepted from the abstract.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| T1 — frozen-model transfer | Abstract p. 1; Sec. 3, “Transfer learning,” p. 4; Sec. 4.1, “Transfer learning settings,” p. 5 | A distance-5 model is trained from scratch. For every other evaluated distance, its weights initialise a model whose positional encoding is adjusted and which is then trained on the new distance's dataset for 10 epochs. | No target distance is evaluated by frozen inference. No device, code family or independently calibrated noise setting is crossed without target-domain training or adjustment. | **missing; this is target-distance fine-tuning/pretrained initialisation, not frozen transfer** |
| D2 — population-level matched decoder comparison | Sec. 4.1 and Table 1, p. 5 | Logical-error point estimates are reported for Transformer-QEC, UF, MWPM and independently trained MLP baselines on the same declared rotated-surface-code/noise conditions at distances 3, 5, 7 and 9. | The test-set size, train/validation/test split, random seeds, record reuse across decoders, paired outcomes and uncertainty are not reported. The Transformer result is a hybrid Transformer-plus-MWPM pipeline, and MLP training rates differ by distance. | **missing under the frozen D2 requirements** |
| R1 — wrong-memory-model robustness | Sec. 4.1, “Benchmarks,” p. 5; full evaluation scope | Ten scalar physical-error rates are sampled inside one phenomenological generator with equal measurement and data-qubit error probabilities. | No continuing carrier, latent transition law or other temporal-memory model is varied; no frozen decoder is tested under a wrong history law, drift, calibration shift or mixed mechanism. | **missing** |
| C1 — temporal-memory specificity | Sec. 3 and Fig. 6, pp. 4--5 | The network receives an ordered multiround syndrome tensor and self-attention can couple positions across the round dimension. | The printed noise generator is not history-dependent, and there is no matched ablation of temporal history access, window length or a declared memory-bearing state. | **does not change the temporal-memory evidence judgment** |
| X1 — cost and latency | Abstract p. 1; Sec. 4.1, “Training settings” and “Transfer learning settings,” p. 5 | Source training uses 100 epochs on one A6000 GPU; target-distance fine-tuning uses 10 epochs, and the abstract reports a greater-than-tenfold training-cost saving. | No wall-clock time, GPU-hours, energy, convergence criterion, accuracy-matched scratch Transformer, inference latency, throughput or memory use is reported. | **epoch-count proxy only; measured cost and latency remain missing** |
| S1 — demonstrated transfer reach | Introduction p. 2; Sec. 4.1 and Table 1, p. 5; Fig. 8, p. 6 | The reported numerical reach is one rotated-surface-code family under one phenomenological generator, with target-distance fine-tuning and results at distances 3, 5, 7 and 9 across scalar values of `p`. | The stated six-distance set `{3,5,7,9,11,13}` is not represented in the evaluation method, Table 1 or Fig. 8; no result for 11 or 13 is printed. | **qualified closure only for within-family fine-tuning at four reported distances** |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Repeated rotated-surface-code memory circuit of distance `D` | Run `D` syndrome rounds and add a final measurement layer | Each syndrome measurement flips with probability `p`; each data qubit receives depolarising error with probability `p`, with X, Y and Z equiprobable; the two rates are equal | Synthetic syndrome history and physical-error/parity labels | Sec. 3, Fig. 6, p. 4; Sec. 4.1, p. 5 | complete for the declared phenomenological generator |
| Syndrome history | Place X-check locations, Z-check locations, two syndrome channels and initial/final temporal-boundary flags on a `(D+1)^3` grid; add 3-D sinusoidal positional encoding and flatten to tokens | Variable token length permits the same architecture to accept different distances after positional-encoding adjustment | Transformer encoder representation | Sec. 3 and Fig. 6, pp. 4--5 | complete |
| Encoder representation and data-qubit position queries | Apply Transformer decoder self-/cross-attention, feed-forward layers and a sigmoid threshold greater than 0.95 | Local physical-error labels are learnable from the simulated generator; mixed training loss adds a pooled global-parity label | Predicted data-qubit errors and Transformer global parity | Sec. 3, p. 4 | complete |
| Predicted errors and observed syndrome | Clear the predicted syndrome contribution, decode any residual syndrome with a global decoder such as MWPM and XOR its global parity with the Transformer parity | The residual global decoder supplies a valid syndrome-consistent completion | Final logical decision | Sec. 3, “Overall workflow,” p. 4; Sec. 4.2, p. 5 | complete; reported Transformer-QEC performance is hybrid with MWPM |
| One million samples at `p=0.01` | Train the 7.9-million-parameter distance-5 Transformer for 100 epochs using Adam on one A6000 GPU | The source does not print the data split, test population, random seeds or stopping rule | Source checkpoint for transfer | Sec. 4.1, “Training settings,” p. 5 | model recipe mostly specified; population split unreplayable |
| Distance-5 checkpoint and a new distance's dataset | Adjust positional encoding and fine-tune for 10 epochs at learning rate `0.0005`; all other settings are stated to remain identical | Target-distance labelled data and parameter updates are allowed | Distance-specific fine-tuned model | Sec. 3, p. 4; Sec. 4.1, p. 5 | complete as fine-tuning; no frozen-inference branch exists |
| Four decoder families and declared test condition | Evaluate UF, MWPM, MLP and hybrid Transformer-QEC and report logical-error point estimates | Test-set size, common-record pairing and uncertainty estimator are unstated | Table 1 logical-error rates | Sec. 4.2 and Table 1, p. 5 | comparison values fixed; sampling/statistical replay incomplete |
| Logical-error curves for distances 3, 5, 7 and 9 | Locate their crossing in physical-error rate | No finite-size scaling or uncertainty method is supplied | Claimed Transformer-QEC threshold | Fig. 8 and surrounding prose, p. 6 | numerical report internally inconsistent: figure/caption `0.038`, prose `0.0038` |

## Exact comparison findings

- Table 1 reports only distances 3, 5, 7 and 9, at `p=0.05` and `p=0.01`. The evaluation method
  names the same four distances. Figure 8 likewise shows four curves. The abstract and introduction
  instead state that six distances, including 11 and 13, were evaluated; no corresponding result is
  printed.
- Table 1 does not support “lower logical error rate for all benchmarks.” At distance 7 and
  `p=0.05`, Transformer-QEC is `0.20590`, whereas MWPM is lower at `0.20178`. The claim of
  consistent superiority therefore fails even on the source's own reported point estimates.
- The other Table-1 Transformer-QEC/MWPM pairs are `0.13005/0.14063` and `0.00784/0.00800`
  at distance 3; `0.17232/0.17279` and `0.00254/0.00268` at distance 5;
  `0.00059/0.00064` at distance 7 and `p=0.01`; and `0.23144/0.23161` and
  `0.00001/0.00002` at distance 9. Without shot totals or intervals, the very small differences
  and five-decimal estimates cannot be assigned statistical strength.
- The ten “error configurations” are the scalar rates
  `{0.05,0.04,0.03,0.025,0.02,0.015,0.01,0.0075,0.005,0.0025}` inside the same
  phenomenological generator. They are not ten mechanisms, temporal laws or device distributions.
- The MLP baseline is trained at `p=0.01` for distances 3 and 5 but at `p=0.025` for distances 7
  and 9. It is trained separately for 100 epochs at each distance. The source does not supply an
  accuracy-matched Transformer trained from scratch at each target distance, so Table 1 does not
  isolate the value of the pretrained initialisation from architecture and training differences.
- Table 2's mixed-loss ablation is distance 5 only. It improves or matches nine of ten printed
  point estimates, but at `p=0.0075` the local-plus-global result (`0.00103`) is worse than local
  loss alone (`0.00097`).
- Figure 8 and its caption print a threshold of about `0.038`; the adjacent prose prints
  `0.0038`, a factor-of-ten discrepancy. The plotted curves visually intersect near `0.038`.
- Figure 7 duplicates the label `D5 p0.02`, leaving one plotted condition unidentified. Its
  “43% higher” class-1 statement corresponds to rounded averages `0.93` versus `0.50`, which is
  a 43-percentage-point difference rather than an unambiguously defined relative improvement.

## Project application

Transformer-QEC is useful primarily as a terminology and transfer-boundary case:

- **Representation:** a learned token representation of a finite multiround detector record. It is
  not a representation of a continuing physical or latent noise carrier.
- **QEC-facing interface:** syndrome history in, local physical-error predictions plus a global
  parity out; a residual MWPM stage completes the logical decision.
- **Computation:** supervised Transformer training followed by target-distance fine-tuning and
  hybrid neural/MWPM inference.
- **Demonstrated reach:** simulated repeated rotated-surface-code memory tasks under one
  phenomenological generator, with four reported distances and no uncertainty.
- **What is established:** a distance-5 checkpoint can initialise target-distance models that are
  fine-tuned for 10 rather than 100 epochs while retaining competitive reported point estimates.
- **What is not established:** frozen inference across distance, transfer across device or code
  family, robustness to a wrong temporal-memory model, a temporal-memory-specific decoder benefit,
  or measured training/inference cost.

The paper therefore does not change the frozen T1 or R1 judgments. It narrows the language needed
for any transfer discussion: accepting variable input length is an architectural property;
pretrained initialisation plus target-data fine-tuning is an adaptation result; neither is evidence
of frozen transfer.

## Competing evidence and kill conditions

### Adjacent evidence in the reviewed corpus

- QAdapt explicitly distinguishes an offline training sequence from frozen online inference and
  reports a no-target-fine-tuning Willow evaluation. Its task, comparator and uncertainty limits
  must still be assessed separately; it cannot retroactively turn Transformer-QEC fine-tuning into
  frozen transfer.
- Hockings et al. compare true, average and finite-shot-estimated decoder priors on common simulated
  surface-code populations. That is a calibration/prior comparison, not cross-distance or
  cross-device transfer of a frozen learned decoder.
- Ziad et al. execute a leakage-conditioned decoder in FPGA logic across distances, but the
  trigger-to-edge map is mechanism-specific and no frozen cross-device or cross-code transfer is
  evaluated.

### Kill conditions

- Kill “without retraining” or “zero-shot”: target-distance labelled data and 10 epochs of parameter
  updates are explicitly required.
- Kill “frozen cross-distance transfer”: positional encoding is adjusted and the network is
  fine-tuned at each target distance.
- Kill “six demonstrated distances”: the reported evaluation contains only 3, 5, 7 and 9.
- Kill “consistently outperforms MWPM”: distance 7 at `p=0.05` is a printed counterexample.
- Kill “ten noise environments”: the ten settings are ten scalar values of `p` in one model family.
- Kill “memory-aware” or “robust to temporal shift”: multiround input alone does not instantiate a
  history-dependent noise law, and no temporal-access or wrong-model ablation is reported.
- Kill “10x measured training-cost reduction”: the disclosed comparison is 100 versus 10 epochs;
  no time, energy or accuracy-matched scratch run is reported.
- Kill “fast decoder” or hardware-readiness: neither neural inference latency nor end-to-end
  decoding latency/resource use is measured.
- Kill statistically resolved superiority: the source reports no test shots, confidence intervals,
  seed variation or paired outcomes.

## Source-local anomalies and qualifications

- The abstract's “without retraining” conflicts with the Methods statement that the pretrained
  model is fine-tuned on each new distance's dataset.
- The abstract and introduction claim six evaluated distances, while the evaluation method,
  Table 1 and Fig. 8 provide only four.
- The all-benchmarks superiority statement conflicts with the distance-7, `p=0.05` Table-1 values.
- The threshold is printed as both `0.038` and `0.0038` on the same page.
- Figure 7 contains a duplicated condition label.
- The model-size paragraph says the larger model is not overfitted yet “performs poorly on testing,”
  even though Table 3 and the preceding sentence show it outperforming the smaller model. The
  sentence is internally inconsistent and should not be used as evidence about generalisation.
- The paper gives no code/data availability statement, checkpoint, source repository, evaluation
  sample count, split, seeds or uncertainty analysis.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted audit; source-only note remains outside admitted manifests
- T1: missing; explicit target-distance fine-tuning, not frozen transfer
- D2: missing under common-record/population/uncertainty requirements
- R1: missing
- C1: not a temporal-memory-law evaluation
- X1: epoch-count proxy only
- S1: qualified within-family fine-tuning at four reported distances

# Claim audit — Yan et al. on neural-decoder hardware transfer and rate-shift robustness

## Fixed source

- Source: Ge Yan, Shanchuan Li and Yuxuan Du, *Rethink the Role of Neural Decoders in Quantum
  Error Correction*, arXiv:2605.12046v1, 12 May 2026; manuscript states acceptance at ICML 2026.
- Artifact:
  `outputs/overview/literature/coverage_validation/rethink_neural_decoders/2605.12046v1.pdf`
- Artifact SHA-256:
  `6b06b88907705b4b9ce674751cf198a188ff1a0a4446fd12b754121116f58c8c`
- Reading scope: all 33 pages, including appendices and all tables. Pages 6, 7, 23, 32 and 33
  were rendered and visually checked because they contain the hardware comparison, data split and
  cross-rate tests.

## Coverage rows

| row | source-local result | source-local boundary | status |
|---|---|---|---|
| **D1 — hardware memory-conditioned benefit** | A TCN processes the full detector history and is evaluated on released Sycamore repeated-surface-code records (Table 1; pp. 6–7) | No comparator removes or limits record history; the added contrast is device-calibrated synthetic pretraining, not access to a declared continuing memory state | **missing for D1** |
| **D2 — population matched comparison** | For each chosen hardware configuration, zero-shot TCN, fine-tuned TCN, standard MWPM and correlated MWPM point estimates are reported, and Appendix D.1 states a 5,000-shot test allocation (Table 1; Appendix D.1, p. 23) | Exact cohort reuse and aggregation are unstated; several two-decimal values are incompatible with one unaveraged 5,000-trial binary count. No hardware uncertainty or paired decisions are given; the d=3 location is selected as the lowest-baseline one of four; neural and MWPM packages differ in representation, computation and training | **useful bounded hardware point comparison, not a population-level or matched memory-access result** |
| **R1 — wrong memory model** | Fixed TCN checkpoints trained at one scalar rate are tested at lower rates under uniform depolarizing and SI1000 generators, with 200,000–5,000,000 test samples and mean ± s.d. over three runs (Appendix E.4; Tables 19–20, pp. 32–33) | Each checkpoint remains within the same generator family on which it was trained. The experiment does not cross from one noise model to the other, perturb a temporal transition law, or test stale/incorrect memory state | **positive for within-family scalar-rate shift; missing for wrong-memory-law robustness** |
| **T1 — frozen transfer** | A TCN pretrained on 5 million samples from the Sycamore dataset's device-calibrated Stim circuit is applied without experimental-shot fine-tuning to the corresponding hardware test records (Table 1; Appendix D.1) | Target-device calibration is used before training; only one selected d=3 location and one d=5 configuration are used; no independent device, code family, distance transfer or calibration-blind application is tested | **bounded simulation-to-matched-hardware zero-shot application; cross-device/cross-code T1 remains missing** |
| **F1 — frame residual** | The source separates ordered detector input, decoder output, neural computation and QEC reach | Transfer meaning additionally depends on the training generator, target-calibration exposure, per-distance model and fine-tuning/test split | **frame retained only with an explicit training/calibration/adaptation-protocol dimension** |

## Hardware comparison replay

- Task: released Google Sycamore Z-memory data at `(d,r)=(3,3)` and `(5,5)` (Appendix D.1,
  p. 23).
- Selection: for distance 3, center `(7,5)` is selected because it has the lowest baseline LER among
  four available centers (Appendix D.1, p. 23).
- Pretraining: 5,000,000 samples are generated from the device-calibrated `circuit_noisy.stim`
  supplied with the dataset (Appendix D.1, p. 23).
- Experimental split: 50,000 shots per selected configuration, of which 45,000 are assigned to
  optional fine-tuning and 5,000 to testing (Appendix D.1, p. 23). The paper does not state the
  split seed, exact checkpoint identity, whether all displayed decoders reuse one common cohort or
  whether the Table 1 values aggregate splits or runs.
- Distance 3 LER (%): standard MWPM 8.01, correlated MWPM 7.38, uniform-prior TCN zero-shot
  34.42, uniform-prior fine-tuned 9.27, calibrated-prior zero-shot 6.81, calibrated-prior fine-tuned
  6.70 (Table 1, p. 6).
- Distance 5 LER (%): 14.38, 12.52, 47.89, 20.06, 11.59 and 11.47 in the same column order
  (Table 1, p. 6).

Several printed percentages, including 8.01, 6.81, 11.59 and 11.47, correspond to half-integer
error counts if treated as one unaveraged 5,000-trial binary sample. The declared allocation and
point estimates are source facts, but their aggregation is not numerically replayable from the
paper. No confidence interval, paired-decision record or test is supplied, so downstream prose may
state only that the calibrated-TCN point estimates are lower under these selected conditions.

This is evidence that target-calibrated synthetic pretraining can transfer to matched experimental
records without using the target test labels. It is not evidence that temporal-memory access caused
the benefit: every neural arm receives the same ordered history, and device-specific calibration has
already entered the training generator.

## Cross-rate replay

- Separate TCNs are trained under uniform depolarizing noise at `p=0.005` and SI1000 at base
  `p=0.004`; each is tested only at lower rates in its own family (Appendix E.4, p. 32).
- Distances 5 and 7 are tested. Evaluation sizes increase from 200,000 at `p=0.003` to 5,000,000
  at `p=0.001`; results are mean ± s.d. across three runs (p. 32).
- Fine-tuning changes reported absolute LER by less than 0.02 percentage points across these
  configurations (p. 33).

The result demonstrates a fixed-checkpoint **rate-range** inside two separately trained model
families. Calling it “noise model robustness” must not be read as transfer between uniform and
SI1000 generators, let alone as misspecification of a memory model.

## Non-promotions

- Do not attribute hardware correlations to leakage, crosstalk or another microscopic mechanism;
  those terms appear as interpretations, not measured latent variables.
- Do not infer a population-wide Sycamore result: one d=3 center is selected and hardware
  uncertainty is absent.
- Do not infer a matched decoder test: the neural and matching decoders differ in model class,
  training exposure and computation.
- Do not infer FPGA deployment of the full hardware-tested system. Most resource numbers are
  analytical estimates; the reported HLS validation is a compressed d=9 TCN kernel, not an
  integrated QEC control-stack test. Main p. 9 reports 271 cycles, whereas Appendix Table 16 on
  p. 27 totals 267 cycles; both are labelled 0.77 microseconds, and the source does not reconcile
  the discrepancy.
- Do not infer cross-device, cross-code or cross-distance frozen transfer.

## Coverage consequence

Yan et al. add a second bounded simulation-to-hardware zero-shot example and a cleaner synthetic
test of fixed-checkpoint performance across lower scalar rates. Together with QAdapt and Stein,
this makes a blanket “no transfer” statement untenable. The defensible statement is narrower:

> Fixed-parameter or zero-shot application has been demonstrated under selected within-family
> rate shifts and simulation-to-matched-hardware settings, often with target calibration or fresh
> metadata. Frozen cross-device, cross-code and memory-model transfer remains missing.

The source belongs in Section 5's transfer/robustness boundary, not among the six Section 3
memory-representation rows.

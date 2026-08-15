# Claim audit — Remm et al. on syndrome-correlation-informed decoding

## Fixed source and reading scope

- Fixed artifact: `outputs/papers/2502.17722.pdf`
- Identity: arXiv:2502.17722v1, *Experimentally Informed Decoding of Stabilizer Codes Based on
  Syndrome Correlations*, Ants Remm and coauthors, manuscript dated 26 February 2025.
- Artifact verification: PDF 1.6, 23 pages, 7,616,887 bytes, SHA-256
  `e2c6f6261c134e510f00d9083cf87a6e98f1e79b414fdb7b6b259a64ba6054e2`.
- Reading scope: all 23 pages, including the main text, Appendices A–I and references. Older local
  discovery material was not used as evidence or prose.
- Independent admission reviewer: `/root/expand_decoder_benefit`, 2026-08-05.
- Visual verification: artifact pages 1, 2, 4–11 and 13–19 were rendered from the fixed PDF. The
  checks covered the source identity, no-reset syndrome convention, post-selection statement,
  signature identifiability and independence assumptions, Eqs. (9)–(10), Figs. 3, 5 and 8–10,
  Eqs. (C1)–(C3), Eq. (E3), Fig. 12, Table III and Eqs. (I1)–(I4).

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| O1 — observation of nontrivial multicycle temporal structure | Main Secs. IV–V, Figs. 3 and 5, PDF pp. 6–10 | In post-selected 16-cycle distance-3 surface-code data, the average same-auxiliary covariance remains positive at the plotted separations through `Delta-m = 11` and is fitted for `Delta-m > 2` by a tail proportional to `0.89^Delta-m`; the selected single-auxiliary C signatures occupy nine consecutive syndrome-cycle positions, hence have maximum separation `Delta-m = 8`. | The measured tail is not shown to be a non-leakage memory effect or a witness of strict quantum non-Markovianity. | closed for observation of temporal record structure only |
| A1 — physical attribution | Main Sec. V and Fig. 5, PDF pp. 8–10; Appendix I, pp. 18–19 | Final-readout leakage rejection and inclusion of C signatures change extracted `T-prime` probabilities in a manner the authors find consistent with undetected data-qubit leakage; the paper also retains changing bit-flip rates and quasiparticle-related processes and gives an analytic nonstationarity confounder. | It does not uniquely identify the microscopic cause of the long tail or intervene on one candidate carrier while holding the repeated-QEC task fixed. | missing |
| B1 — benefit from a correlation-aware decoder | Main Sec. III, PDF p. 6; Appendix C and Figs. 8–10, pp. 11–16 | A correlated-MWPM iteration conditions one syndrome graph on the inferred complementary Pauli-Y-compatible error and produces fitted per-cycle errors of `3.873 +/- 0.203%` standard versus `3.869 +/- 0.201%` modified at `gamma = 0.09`. | The source explicitly states that the difference is not statistically significant; the update targets cross-type Pauli-Y correlations rather than access to the long C-class tail, and weights, `gamma` selection and fidelity use the same dataset. | missing |
| R1 — robustness to mismatch and finite calibration data | Main Sec. VI, PDF p. 10; Appendix C, pp. 13–16; Appendix I, pp. 18–19 | Diagnostic simulations and analysis show that finite-sample fluctuations can erase or reverse the modified decoder's relative improvement, heterogeneous static gate rates alter the useful interpolation strength, and pooled acquisition-time rate changes can create spurious inferred correlations. | It does not perform a held-out robustness sweep over temporal-memory model misspecification or establish a calibrated robustness range. | missing |
| T1 — transfer | Main Secs. IV–VI and Appendices C–I, PDF pp. 6–20 | The inference and decoder procedures are evaluated on one 17-qubit distance-3 experiment and on illustrative surface-17 simulations constructed for diagnostic comparisons. | There is no deployment of a fixed inferred model or decoder on a held-out device, code family, distance or independently calibrated operating regime. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Four logical preparations on a 17-qubit distance-3 surface-code device | Acquire 16 stabilizer cycles and final readout; for the default analysis reject runs with any non-computational readout or failed ground-state initialization | After rejection, about 54,000 runs remain per prepared state from 500,000 acquisitions; Fig. 5 separately recomputes selected quantities with and without final data-qubit leakage rejection | Experimental syndrome-element records for in-situ calibration, conditional on the declared selection except in the explicit no-postselection contrast | Main Sec. IV, PDF p. 6; Fig. 5b–c and Sec. V, pp. 9–10 | complete |
| Binary syndrome elements across space and cycle | Compute pair covariance and average over runs and bulk cycle index | First and last cycle are omitted because their construction differs from bulk syndrome elements | A space-time covariance matrix resolving integer and half-cycle separations | Eq. (9), Fig. 3a and Sec. IV, pp. 6–7 | complete |
| Measured syndrome correlations of arbitrary order | Apply the closed-form inversion in Eq. (10), recursively renormalizing a signature by probabilities assigned to its strict supersets | Distinct generative error-process indicators `F` are assumed independent even when their signature sets overlap; measured syndrome elements are not assumed independent; physical errors with an identical signature are observationally aggregated | Per-cycle probabilities for the selected error-signature processes | Main Secs. III–IV, Eq. (10), pp. 5 and 7–8; Appendix E, Eqs. (E1)–(E3), pp. 17–18 | complete |
| The 124 syndrome elements from each 16-cycle run | Retain 116 circuit-Pauli signatures and 4,360 C signatures; the first C family contains subsets on one auxiliary over nine consecutive syndrome-cycle positions (`Delta-m_max = 8`), and the second contains subsets around one data qubit separated by at most two cycles | Exhaustive enumeration of `2^124` signatures is infeasible; the catalogue is selected and omitted high-weight signatures can bias inferred lower-weight probabilities | Error-class totals and diagnostics for the selected signature catalogue | Main Sec. IV and Fig. 3b–c, pp. 7–8; Appendix F and Table III, pp. 18–19 | complete |
| Same-auxiliary syndrome elements at separation `Delta-m` | Calculate covariance, average over the eight auxiliary qubits and fit the tail for separations greater than two | The displayed error bars are one standard deviation across auxiliary qubits; a positive tail can arise from persistent errors or acquisition-time nonstationarity | Average covariance tail fitted as proportional to `0.89^Delta-m` through the plotted separations to `Delta-m = 11` | Main Fig. 5a and Sec. V, PDF p. 9 | complete |
| Data with and without final-readout leakage rejection | Recalculate selected `T-prime` probabilities with and without the high-correlation signature class | Final-readout rejection misses leakage that seeps back before readout; other varying-rate mechanisms remain possible | Evidence consistent with undetected data-qubit leakage but not unique microscopic attribution | Main Fig. 5b–c and Sec. V, pp. 9–10 | complete |
| Inferred signature probabilities | Convert pair-signature probabilities to MWPM edge weights and decode X- and Z-type syndromes separately | Time-translation invariance is approximated in the bulk; matching represents only signatures of weight at most two per graph | Standard correlation-calibrated MWPM | Main Sec. III, Eqs. (3)–(8), pp. 4–6 | complete |
| Standard MWPM output on one syndrome type | Reweight the complementary graph using leading-order conditional probabilities for Pauli-Y-compatible signatures, interpolate old and new probabilities with `gamma`, and decode once more | Higher-order terms are omitted; statistical uncertainty increases in the conditional estimate | Correlated MWPM comparison with standard MWPM | Appendix C, Eqs. (C1)–(C3), pp. 11–15 | complete |
| Experimental decoder comparison | Choose `gamma = 0.09` at the highest logical fidelity and use the same data for inferred weights and plotted fidelity | The interpolation controls statistical noise in the update but is not selected or evaluated on independent held-out data | Fitted error per cycle `epsilon_std = 3.873 +/- 0.203%` versus `epsilon_mod = 3.869 +/- 0.201%`; the raw difference is 0.004 percentage points and the source states it is not statistically significant | Main Sec. III, p. 6; Appendix C and Fig. 8, PDF p. 13 | complete |
| Homogeneous and heterogeneous depolarizing simulations | Vary update strength, sample size and heterogeneity scale | These simulations are diagnostic and are not intended to reproduce the full experimental noise | Larger samples tolerate stronger updates; heterogeneity and finite statistics alter or reverse relative improvement | Figs. 9–10 and Appendix C.3–C.4, pp. 14–16 | complete |
| Two syndrome elements generated by independent flips whose common rate changes across acquisition time | Compare a stationary rate `p` with two equally weighted acquisition blocks at rates 0 and `2p`, then apply Eq. (10) to the pooled moments | Samples from distinct rate regimes are pooled as if generated by one stationary model | A nonzero apparent pair-error probability is inferred despite independence within each block; for rates `(1-epsilon)p` and `(1+epsilon)p`, the small-change term is proportional to `epsilon^2 p^2` | Appendix I, Eqs. (I1)–(I4), PDF p. 19 | complete |

## Project application

This source strengthens the overview primarily as a boundary-setting experiment. It supplies a
concrete record-level observation and a QEC-facing inference method while keeping several claims
separate.

- **Observation:** the post-selected experiment resolves spatial, half-cycle and multicycle syndrome
  covariance, including a fitted same-auxiliary tail through the displayed separation
  `Delta-m = 11`; this is distinct from the selected C-signature catalogue's maximum separation
  `Delta-m = 8`.
- **Attribution:** the leakage-rejection contrast makes residual leakage plausible, but the authors
  retain changing rates and quasiparticle-related processes as alternatives. The source therefore
  supports qualified attribution, not a unique microscopic cause.
- **QEC abstraction:** the output is an error-signature probability model used to set matching
  weights. It is not a microscopic open-system model and does not identify a unique physical event
  for every signature.
- **Decoder benefit:** the experimentally tested correlation-aware update concerns joint X/Z
  information associated with Pauli-Y errors. Its small improvement is not statistically
  significant and cannot close a claim about benefit from long-time memory access.
- **Calibration and robustness:** exhaustive high-weight inference is exponentially costly, finite
  samples enlarge conditional-weight uncertainty, acquisition-time nonstationarity can generate
  spurious correlations and using the same data for weights, interpolation choice and fidelity
  leaves no held-out validation in this source.
- **Concept boundary:** multicycle syndrome covariance is temporal structure; it is not automatically
  strict quantum non-Markovianity, nor is the possible leakage mechanism uniquely established.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- Miao et al., arXiv:2211.04728v1, prepares leakage and applies targeted leakage removal. That
  intervention provides stronger leakage-specific causal evidence than the post-selection and
  signature-consistency arguments in this source.
- AlphaQubit, arXiv:2310.05900, reports a learned recurrent decoder on experimental and simulated
  surface-code data. It may support decoder performance at greater scale but does not retroactively
  make the Remm correlated-MWPM difference statistically significant.
- A stationary circuit-level Pauli simulation reproduces broad error-class totals here but omits
  leakage and readout-misclassification errors. Agreement at that aggregation level is not a unique
  mechanism validation.

### Kill conditions

- Kill any claim that the long covariance tail is uniquely caused by leakage; the source explicitly
  presents varying rates and quasiparticle-related processes as alternatives.
- Kill any claim that all detected temporal structure is nonstationary drift; drift is demonstrated
  as a confounder by an analytic example, not identified as the cause of the device data.
- Kill any claim of a demonstrated memory-aware decoding gain; the tested update targets cross-type
  Pauli-Y information, and the experimental difference is not statistically significant.
- Kill any claim that calibration is model-free: the inversion depends on a selected family of
  independent error signatures, and omitted high-weight signatures bias inferred probabilities.
- Kill any claim that the error model is exhaustive: only a tractable subset of the exponentially
  large signature space is included.
- Kill any claim of transferability: no held-out device, code family or independent deployment is
  tested.
- Kill any statement equating multicycle covariance, leakage, drift or strict quantum
  non-Markovianity.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted
- O1: closed for observation of multicycle syndrome structure only
- A1: missing; leakage is plausible but not uniquely identified
- B1: missing; the experimental correlated-decoder difference is not statistically significant and
  does not isolate access to the long-time tail
- R1: missing; the source supplies finite-sample, heterogeneity and nonstationarity failure-mode
  evidence but no held-out temporal-memory-model robustness result
- T1: missing
- downstream status: independent source-only review passed; manifest admission remains a separate
  corpus-management action

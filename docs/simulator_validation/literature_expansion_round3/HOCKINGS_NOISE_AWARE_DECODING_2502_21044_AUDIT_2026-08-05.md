# Claim audit — Hockings, Doherty and Harper on noise-aware decoder calibration

## Fixed source and reading scope

- Fixed artifact: `outputs/overview/literature/coverage_validation/hockings/2502.21044v2.pdf`
- Identity: arXiv:2502.21044v2, *Improving error suppression with noise-aware decoding*,
  Evan T. Hockings, Andrew C. Doherty and Robin Harper, revised 1 April 2025.
- Publication status: preprint. The arXiv record lists v1 on 28 February 2025 and v2 on 1 April
  2025; no journal DOI is identified in the fixed source.
- Artifact verification: PDF 1.5, 10 artifact pages, 483,968 bytes, SHA-256
  `9477f3e1a195c59e92681ce7e026dc859323790fbeb62b66de63169915af3b46`.
- Reading scope: all 10 artifact pages, including both figures, Table I, Eqs. (1)–(2), references
  and Appendix A with Eqs. (A1)–(A5). The arXiv comment “5 pages + 2 page appendix” excludes
  the intervening reference pages from that short description; the downloaded artifact has five
  main-text pages, three continuation/reference pages and two appendix pages.
- Visual verification: rendered artifact pages 1–10 were inspected. Load-bearing checks covered
  the Pauli-channel and ACES regression equations on pp. 1–2, the population design and fitted
  quantities on p. 3, Fig. 2 and Table I on p. 4, the cost and future-work boundary on pp. 4–5,
  and the covariance/projection approximations in Appendix A on pp. 9–10.
- External supplementary material: none is linked by the fixed arXiv record. Appendix A is embedded
  in the main PDF.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| D1 — hardware memory-conditioned decoder benefit | Numerical results and Conclusions, PDF pp. 3–5 | Circuit-level simulations compare correlated-MWPM priors derived from a true static Pauli model, finite-shot ACES estimates and tuned depolarising noise. | No quantum-device memory experiment is run; no comparator differs specifically in access to a persistent carrier or additional record history. Hardware implementation is named as a next step. | missing |
| D2 — population-level matched memory-decoder comparison | Numerical results and Fig. 2, pp. 3–4; Table I, p. 4 | A defined synthetic distribution is averaged over 1,500 to 50 noise instances at distances 3 to 13, using one MWPM backend and four decoder priors; Fig. 2 reports one-standard-deviation error bars. Table I gives a shot-paired confusion matrix for one distance-25 instance. | The varied information is static gate-level calibration, not a temporal-memory representation or history-access ablation. Exact record reuse is explicit in Table I but is not separately documented for every population-fit point. | missing for the frozen memory-specific row; adjacent static-calibration analogue closed |
| R1 — robustness under a wrong memory model | Numerical results, pp. 3–4; Appendix A, pp. 9–10 | Finite-shot ACES priors at `10^6` and `10^7` calibration shots are compared with exact priors and a coarse tuned-depolarising prior inside one log-normal Pauli model family; large-scale estimation uses weighted rather than generalised least squares and gatewise projection. | No wrong temporal law, mixed mechanism, non-Pauli residual, drift during collection, stale calibration, held-out device shift or memory-carrier misspecification is tested. The Appendix-A reductions receive no formal error bound. | missing; finite-data/static-prior diagnostics only |
| T1 — frozen-model transfer | Numerical results, pp. 3–4 | The same overall ACES-plus-MWPM procedure is instantiated for XZZX surface-code distances 3–25, and the ACES design is initially optimised from tuned-depolarising parameters for a distance-3 circuit. | Each synthetic noise instance is characterised anew, only one code family is used, distance 25 is one fixed-seed instance, and there is no frozen decoder prior evaluated across an independent code, device or operating regime. | missing |
| C1 — calibration and computational cost | Numerical results, p. 3; Conclusions, pp. 4–5; Appendix A, p. 10 | On a 2021 M1 Max laptop, ACES processing for a distance-25 syndrome-extraction circuit takes under four seconds; `10^6` hardware shots are projected from another experiment's gate timings to take about two seconds with an appropriate stack. Weighted least squares and per-gate simplex projection are used at large scale. | The two-second acquisition is not measured in this study; end-to-end hardware integration, decoder latency, recalibration cadence, drift tracking and a quantified loss from the large-scale reductions are not reported. | closed for bounded simulation cost and a labelled acquisition projection |
| M1 — temporal-memory specificity | Pauli model and decoder prior, pp. 1–3; Conclusions, p. 5 | Each synthetic instance assigns time-independent gate-context Pauli probabilities, and ACES estimates a static circuit-level decoder prior. The phrase “memory experiment” denotes preservation of a logical observable over repeated rounds. | No source-defined persistent physical or latent state, time-varying transition law, history-conditioned prior, memory-length parameter or temporal-model ablation appears. Online updates for drift are only proposed future work. | contradicted: this is generic static noise-aware decoding, not a temporal-memory study |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| A Pauli-frame-randomised Clifford syndrome-extraction circuit | Associate each gate in its layer context with a Pauli channel `E(rho)=sum_a p_a P_a rho P_a` | Pauli frame randomisation justifies representing the simulated noise by Pauli channels | Gate-context Pauli probabilities | Introducing ACES and Eq. (1), PDF pp. 1–2 | complete for the declared model; no non-Pauli residual is evaluated |
| Rearranged Clifford circuits and measured Pauli observables | Decompose each circuit eigenvalue into gate eigenvalues and take logarithms | The design matrix has full rank and the circuit eigenvalues can be estimated | Linear system `log Lambda_mu=sum_nu A_mu,nu log lambda_nu` | Eq. (2) and surrounding text, p. 2 | complete |
| Estimated gate eigenvalues | Apply the inverse Walsh–Hadamard relation and project probability estimates into the simplex using covariance-weighted Mahalanobis distance | The covariance estimate is adequate and the retained coordinates omit identity components to obtain full rank | Physical gate-level Pauli probability estimates | Main text, p. 2; Appendix A, Eqs. (A4)–(A5), p. 9 | complete within the printed estimator |
| A synthetic noise instance | Draw each gate's Pauli error probabilities independently from the declared log-normal distribution; fix average operation-class rates and distribution widths | A static heterogeneous Pauli model resembles the cited below-threshold hardware parameter regime | One time-independent circuit-level noise model per instance | Numerical results, p. 3 | complete; resemblance is parameter-level, not device validation |
| True, finite-shot ACES and tuned-depolarising Pauli models | Convert each into the detector-error probabilities used as the prior of the same correlated PyMatching decoder | Stabiliser simulation of the Pauli circuit supplies the decoder prior; the tuned-depolarising comparator retains accurate average component rates | Four MWPM decoding configurations differing in prior calibration | Quantum codes and decoders, pp. 2–3; Numerical results, p. 3 | complete |
| Distance 3, 5, 7, 9, 11 and 13 X/Z memory tasks | Fit logical error per round over `r in {3,5,9,17,33}` from `10^5` shots and average across the printed numbers of log-normal instances | Exponential below-threshold distance scaling is an adequate fit | Error-suppression factors `1.7360±0.0025` (true), `1.6967±0.0025` (depolarising), `1.7347±0.0025` (ACES `10^6`) and `1.7358±0.0025` (ACES `10^7`) | Numerical results, p. 3 | complete; the source does not label the printed `±` values as confidence intervals |
| Population fits under the four priors | Divide logical error per round by the tuned-depolarising fit and plot versus distance | The random-instance distribution and within-instance covariance support the comparison | Fig. 2 population trend with one-standard-deviation error bars | Fig. 2 and caption, p. 4 | complete for static noise-aware decoding |
| One fixed-seed distance-25 log-normal instance | Decode the same `10^7` shots, split evenly between X and Z memories, under all four priors | A single large-distance instance can illustrate the population extrapolation | Shot-paired success/failure confusion matrix | Table I, p. 4 | complete; one instance is not a population |
| One distance-25 instance over several round counts | Fit per-round logical error from `10^6` shots in each X and Z memory task | The same exponential-in-round fit applies | `2.39±0.05`, `3.13±0.06`, `2.42±0.05` and `2.40±0.05`, all times `10^-5`, for true, depolarising, ACES `10^6` and ACES `10^7` priors | Numerical results, p. 4 | complete for the fixed instance |
| Small-distance population fit | Extrapolate the fitted distance trend to distances 61 and 63 | The fitted scaling and asserted self-averaging continue far beyond the simulated population | Predicted distance-63 logical rates and a predicted 496-qubit reduction at distance 61 | Numerical results, p. 4 | complete as an extrapolation, not a simulated result |
| Distance-25 ACES processing | Replace generalised least squares by weighted least squares using only the diagonal of `Omega'`; project each gate separately | Neglected simultaneous-eigenvalue covariance and blockwise projection have only a minor performance impact | Scalable ACES calibration computation | Appendix A, p. 10 | complete as implemented; no quantified error or global bound is supplied |

## Project application

### What the source changes

The paper provides a strong **adjacent control case**, not a temporal-memory decoder result. It shows
that a population-level comparison of decoder priors can be performed under a declared synthetic
distribution while holding the code task and decoding algorithm fixed, reporting dispersion and a
large-instance shot-paired confusion matrix. It therefore demonstrates that population-level
matched evaluation is technically possible for static heterogeneous Pauli calibration.

That does not close D1 or D2 for the overview's memory-specific question. The varied object is a
static decoder prior. There is no memory-bearing carrier, latent transition state, extra history
window or time-conditioned decoder information. Repeated rounds make the task a quantum-memory
experiment, but they do not make the physical-noise model temporally non-Markovian.

### Representation–interface–computation mapping

- **Representation:** stationary, gate- and layer-context Pauli channels whose probabilities are
  independently drawn once per synthetic instance from a log-normal distribution.
- **QEC-facing interface:** circuit-level Pauli probabilities are converted by stabiliser simulation
  into a decoder prior over detector-flip mechanisms for repeated XZZX surface-code memories.
- **Computation:** ACES circuit-eigenvalue estimation, linear regression, Walsh–Hadamard conversion,
  covariance-aware simplex projection, Stim sampling and correlated PyMatching decoding.
- **Demonstrated reach:** population simulations for one rotated-surface-code family at distances
  3–13; a single distance-25 instance; distances 61 and 63 are extrapolations.

The source fits the four-way comparison frame cleanly, but the representation has no temporal-memory
object. It should therefore remain outside the six core Section 3 memory approaches or appear only
as a boundary example separating generic noise-aware calibration from memory-conditioned inference.

### Robustness and transfer interpretation

- ACES `10^6` versus `10^7` tests finite calibration data within the correct Pauli model family.
- Tuned depolarising noise tests loss of static gate-level heterogeneity while retaining accurate
  average operation-class rates.
- Neither contrast changes the temporal law, carrier dynamics or physical mechanism.
- Applying the procedure at several distances is within-family scaling, not frozen transfer: target
  priors are re-estimated, no independent device or code family is held out, and distance 25 uses one
  selected fixed-seed instance for reproducibility.

### Cost interpretation

The under-four-second laptop processing result is measured in the authors' ACES simulation workflow.
The about-two-second hardware acquisition is a projection from timings in a cited experiment and
requires an appropriate control stack. The paper does not measure real-device collection, repeated
recalibration under drift, decoder latency or end-to-end operational cost. Appendix A also replaces
the full large-scale covariance calculation and global simplex projection by cheaper approximations
without a formal performance-loss bound.

## Competing evidence and kill conditions

### Competing or adjacent evidence

- Nayak et al. provide a genuinely time-conditioned latent-field decoder contrast, but only for
  impact-selected synthetic events and without a proposed-method population average or uncertainty.
- Remm et al. analyse hardware syndrome correlations, but their tested correlated-MWPM update targets
  cross-type Pauli information and yields no statistically significant decoder improvement.
- AlphaQubit demonstrates held-out hardware decoding with recurrent architecture but does not isolate
  access to record history from architecture, training and input differences.

Hockings is methodologically stronger than these sources on population averaging for its own static
calibration question, but it does not supply their missing memory-specific ablation.

### Kill conditions

- Kill a hardware-benefit claim: all QEC and ACES data in this paper are simulated; the hardware
  experiment is future work.
- Kill a temporal-memory claim: the noise parameters are static within each instance and no
  memory-bearing state or time-conditioned prior is defined.
- Kill a history-access claim: all arms use the same repeated-QEC record interface and differ in
  decoder-prior calibration.
- Kill a wrong-memory-model robustness claim: finite-shot ACES and tuned depolarising priors remain
  within or adjacent to the same stationary Pauli representation.
- Kill a frozen-transfer claim: only one surface-code family is used and calibration is repeated for
  the target instances.
- Kill a statement that distances 61 or 63 were simulated: both are extrapolated from lower-distance
  fits.
- Kill an unqualified “optimal decoding” claim: the true-noise arm gives exact model priors to the
  same correlated MWPM backend; it is not a comparison with globally optimal maximum-likelihood
  decoding.
- Kill an actual two-second hardware-calibration claim: collection time is projected from another
  experiment's timing parameters.
- Kill an equal end-to-end cost claim: prior calibration changes no advertised MWPM algorithm, but
  decoder runtime and total calibration-plus-decoding latency are not benchmarked across arms.
- Kill a certified approximation claim: the weighted-least-squares and gatewise-projection reductions
  are described as practical and having minor impact, without a quantitative bound.

## Source-local anomalies and reporting boundaries

- Fig. 2's error bars are explicitly one standard deviation. The separate `±0.0025` values attached
  to all four fitted suppression factors are not explicitly labelled as confidence intervals in the
  source and should not be promoted to that meaning.
- The distance-25 result is one fixed-seed noise instance. Agreement with the small-distance
  population fit is attributed by the authors to self-averaging, but no independent held-out device
  or model family tests that interpretation.
- The tuned-depolarising comparator is not uninformed: its component rates equal the accurate average
  rates of the log-normal distribution. This makes the comparison stricter but also limits what kind
  of model misspecification it probes.
- At large scale, weighted least squares discards off-diagonal elements of `Omega'`, and the
  probability-simplex projection is performed gate by gate because a global projection becomes
  intractable. The source reports only a minor performance impact and supplies no numerical bound or
  dedicated ablation in this letter.
- “Memory experiment” is the standard logical-storage task label. It must not be quoted as evidence
  that the noise model itself has temporal memory.

## Source-local verdict

- `read_status`: complete
- `evidence_status`: persisted as a fixed artifact, audit and candidate source-only note; corpus
  admission remains pending independent review
- D1: missing
- D2: missing for temporal-memory-conditioned decoding; strong adjacent population-level static
  calibration comparison
- R1: missing beyond finite-data and coarse-static-prior diagnostics
- T1: missing
- C1: closed for bounded simulated processing cost and a clearly labelled acquisition projection
- M1: contradicted — the study is not temporal-memory-specific
- framework result: no residual; the source is naturally represented by separating a stationary
  Pauli representation, decoder-prior interface, ACES/Stim/PyMatching computation and simulated
  surface-code reach


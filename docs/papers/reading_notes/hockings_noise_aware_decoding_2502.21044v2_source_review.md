+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2502.21044"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2502.21044v2"
source_artifact = "outputs/overview/literature/coverage_validation/hockings/2502.21044v2.pdf"
source_sha256 = "9477f3e1a195c59e92681ce7e026dc859323790fbeb62b66de63169915af3b46"
title = "Improving error suppression with noise-aware decoding"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/HOCKINGS_NOISE_AWARE_DECODING_2502_21044_AUDIT_2026-08-05.md"
audit_packet_sha256 = "cbad77c756b43dfa0635c7dc8cbb591c1bdabb1e73c61605f4e98d2509de1b6f"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_ziad"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

[[relations]]
predicate = "defines"
object_id = "hockings-log-normal-pauli-noise"
object_type = "model"
object_label = "log-normal Pauli noise"
fact_id = "hockings-lognormal-pauli-model"

[[relations]]
predicate = "uses"
object_id = "hockings-aces-calibration"
object_type = "method"
object_label = "averaged circuit eigenvalue sampling"
fact_id = "hockings-aces-regression"

[[relations]]
predicate = "uses"
object_id = "hockings-correlated-mwpm-prior"
object_type = "method"
object_label = "correlated MWPM decoder priors"
fact_id = "hockings-qec-interface"

[[relations]]
predicate = "supports"
object_id = "hockings-population-prior-comparison"
object_type = "observable"
object_label = "error-suppression factors"
fact_id = "hockings-population-result"

[[relations]]
predicate = "supports"
object_id = "hockings-finite-shot-aces-priors"
object_type = "observable"
object_label = "finite-shot ACES decoder priors"
fact_id = "hockings-finite-shot-calibration"

[[relations]]
predicate = "limits"
object_id = "hockings-large-scale-aces-reduction"
object_type = "limitation"
object_label = "weighted least squares"
fact_id = "hockings-large-scale-approximation"
+++
# Full-text review — Hockings, Doherty and Harper, "Improving error suppression with noise-aware decoding"

## Source identity [paper_fact]
Fact ID: hockings-source-identity
Source locator: Title page; arXiv version record
PDF page: 1
Claim: The fixed source is the 10-artifact-page arXiv:2502.21044v2 preprint by Evan T. Hockings, Andrew C. Doherty and Robin Harper, revised 1 April 2025.

The artifact contains five pages of main text, three continuation/reference pages and a two-page
embedded Appendix A. The fixed arXiv record supplies no journal-publication DOI or separate
supplementary file.

## Selection scope [paper_fact]
Fact ID: hockings-selection-scope
Source locator: Abstract; Introduction, final three paragraphs
PDF page: 1
Claim: The source uses circuit-level numerical simulations to test whether ACES estimates of Pauli gate noise can calibrate correlated-matching decoder priors for repeated surface-code memory experiments.

The reported comparison is among priors derived from the true simulated noise model, finite-shot
ACES estimates and tuned depolarising noise.

## Pauli-channel representation [paper_fact]
Fact ID: hockings-pauli-channel
Source locator: Introducing ACES; Eq. (1)
PDF page: 1
Claim: The source represents each gate's noise in its layer context by a Pauli channel whose probabilities weight a mixture of Pauli conjugations.

The stated motivation is that Pauli frame randomisation tailors arbitrary noise channels into Pauli
channels. The source does not simulate a residual non-Pauli component.

## ACES regression [paper_fact]
Fact ID: hockings-aces-regression
Source locator: Introducing ACES; Eq. (2)
PDF page: 2
Claim: Averaged circuit eigenvalue sampling decomposes measured circuit eigenvalues into products of gate eigenvalues and obtains the latter through a full-rank logarithmic linear-regression system.

An inverse Walsh–Hadamard transformation relates gate eigenvalues to gate Pauli error probabilities.
The experiment design is optimised to improve sample efficiency.

## Decoder-prior interface [paper_fact]
Fact ID: hockings-qec-interface
Source locator: Quantum codes and decoders, final three paragraphs
PDF page: 2
Claim: Stabiliser simulation converts a circuit-level Pauli model into correlated MWPM decoder priors that assign probabilities to detector-flip combinations caused by circuit error mechanisms.

The repeated memory experiment uses parities of stabiliser outcomes across consecutive syndrome-
extraction rounds as detectors. PyMatching performs the correlated matching in the numerical study.

## Log-normal Pauli model [paper_fact]
Fact ID: hockings-lognormal-pauli-model
Source locator: Numerical results, second paragraph
PDF page: 3
Claim: Each simulated log-normal Pauli noise instance draws the Pauli error probabilities of each gate independently from a log-normal distribution with fixed operation-class means and distribution widths.

The average single-qubit, two-qubit, measurement/measurement-idle and reset error rates are `0.05%`,
`0.4%`, `0.8%` and `0.2%`. The underlying normal-distribution standard deviations are `1/2` for
single- and two-qubit gates and `1/4` for measurement and reset. A seed of zero is fixed when only
one random instance is drawn.

## Tuned-depolarising comparator [paper_fact]
Fact ID: hockings-depolarising-comparator
Source locator: Numerical results, second paragraph
PDF page: 3
Claim: The tuned-depolarising comparator sets each operation class to the corresponding average error rate of the log-normal Pauli distribution.

The ACES experimental design is optimised according to these tuned-depolarising parameters for a
distance-3 syndrome-extraction circuit. The comparator is therefore informed by accurate average
rates rather than being an uncalibrated uniform prior.

## Population design [paper_fact]
Fact ID: hockings-population-design
Source locator: Numerical results, paragraph beginning "First, we examine"
PDF page: 3
Claim: The population study fits per-round logical decay over `r={3,5,9,17,33}` from `10^5` shots in both X and Z memories and averages over 1,500, 300, 100, 80, 60 and 50 noise instances at distances 3, 5, 7, 9, 11 and 13, respectively.

Every instance is decoded with the true-model, tuned-depolarising, ACES-`10^6` and ACES-`10^7`
priors using the same correlated-MWPM decoder type.

## Population decoder-prior result [paper_fact]
Fact ID: hockings-population-result
Source locator: Numerical results, population-fit paragraph
PDF page: 3
Claim: Exponential fits in code distance give error-suppression factors `1.7360±0.0025`, `1.6967±0.0025`, `1.7347±0.0025` and `1.7358±0.0025` for true-model, tuned-depolarising, ACES-`10^6` and ACES-`10^7` decoder priors, respectively.

The paper concludes that finite-shot ACES estimates reproduce nearly all of the true-prior advantage
over the tuned-depolarising prior within this synthetic distribution. It does not identify the
printed `±` quantities as confidence intervals.

## Figure-2 uncertainty and scaling [paper_fact]
Fact ID: hockings-figure-two
Source locator: Fig. 2 and caption
PDF page: 4
Claim: Figure 2 normalises logical error per round to the tuned-depolarising fit, displays one-standard-deviation error bars and reports a relative performance separation that grows with code distance for the tested population fits.

The figure combines X and Z memories and the declared random noise instances. Its population is the
synthetic log-normal Pauli ensemble rather than measured device runs.

## Finite-shot calibration [paper_fact]
Fact ID: hockings-finite-shot-calibration
Source locator: Numerical results and Fig. 2
PDF page: 4
Claim: Finite-shot ACES decoder priors calibrated from `10^6` and `10^7` simulated shots are separately evaluated and both closely track the exact-prior MWPM result within the declared log-normal Pauli model.

This varies finite calibration data while retaining the same assumed stationary Pauli model family.

## Distance-25 shot-paired comparison [paper_fact]
Fact ID: hockings-distance25-paired
Source locator: Numerical results, distance-25 paragraph; Table I
PDF page: 4
Claim: Table I decodes the same `10^7` distance-25 shots, divided evenly between X and Z memories, under all four priors and reports a shot-paired success/failure confusion matrix for one random noise instance.

The diagonal failure counts are 5,507 for the true prior, 5,539 for ACES-`10^7`, 5,631 for
ACES-`10^6` and 7,198 for tuned depolarising noise. The true-prior decoder succeeds on 3,005 shots
where the depolarising-prior decoder fails, while the reverse occurs on 1,314 shots.

## Distance-25 logical-rate result [paper_fact]
Fact ID: hockings-distance25-rate
Source locator: Numerical results, paragraph continuing below Fig. 2
PDF page: 4
Claim: For the same distance-25 noise instance, fits from `10^6` shots give per-round logical error estimates `(2.39±0.05)e-5`, `(3.13±0.06)e-5`, `(2.42±0.05)e-5` and `(2.40±0.05)e-5` for true, depolarising, ACES-`10^6` and ACES-`10^7` priors.

The authors describe agreement of the resulting ratios with the small-distance population fits as a
self-averaging effect. This calculation uses one fixed-seed distance-25 instance.

## Extrapolated large-distance result [paper_fact]
Fact ID: hockings-large-distance-extrapolation
Source locator: Numerical results, final two paragraphs
PDF page: 4
Claim: The distance-61 and distance-63 logical-rate and qubit-overhead numbers are predictions obtained by extending the lower-distance fitted trend rather than direct simulations at those distances.

The source predicts roughly a factor-two logical-rate reduction at distance 63 and a reduction of
496 physical qubits by using ACES-`10^6` at distance 61 instead of tuned depolarising decoding at
distance 63 for the stated target rate.

## Calibration-time accounting [paper_fact]
Fact ID: hockings-calibration-cost
Source locator: Conclusions, first two paragraphs
PDF page: 5
Claim: ACES processing for a simulated distance-25 syndrome-extraction circuit takes under four seconds on the stated laptop, while collection of `10^6` hardware shots is projected from cited operation timings to take about two seconds with an appropriate control stack.

Only the laptop processing time is measured in this study. The hardware collection time is an
estimate based on another experiment's gate, measurement and reset durations.

## Relative-precision modification [paper_fact]
Fact ID: hockings-relative-precision
Source locator: Appendix A; Eqs. (A1)–(A3)
PDF page: 9
Claim: The modified ACES design estimates products of gate eigenvalues over Clifford-gate Pauli orbits to relative precision by using repeated circuits whose depth scales inversely with noise strength.

The optimisation balances ordinary and relative-precision figures of merit through their product,
and the paper contrasts orbit-product relative precision with additive precision for individual
within-orbit gate eigenvalues.

## Covariance-aware projection [paper_fact]
Fact ID: hockings-covariance-projection
Source locator: Appendix A; Eqs. (A4)–(A5)
PDF page: 9
Claim: The source projects gate-probability estimates into the probability simplex using a Mahalanobis metric built from a transformed inverse gate-eigenvalue covariance matrix.

Identity eigenvalues and identity probabilities are omitted from the estimator vectors so their
covariance matrices remain full rank, requiring corresponding conjugations of the transform
matrices.

## Large-scale ACES approximation [paper_fact]
Fact ID: hockings-large-scale-approximation
Source locator: Appendix A, final two paragraphs
PDF page: 10
Claim: At distance 25, the implementation replaces generalised least squares by weighted least squares using only the diagonal of the circuit log-eigenvalue covariance and replaces global simplex projection by separate per-gate projections.

The source says the gatewise projection has only a minor performance impact and that the diagonal
covariance suffices in practice. It gives no quantitative approximation bound in this letter.

## Hardware and drift status [paper_fact]
Fact ID: hockings-hardware-future-work
Source locator: Conclusions, paragraphs beginning "A natural next step" and "An important advantage"
PDF page: 5
Claim: The source identifies implementation on a quantum-device memory experiment as future work and suggests that separately cited online syndrome methods could later update ACES-calibrated priors to account for device drift.

No hardware decoder comparison or online drift update is performed in the reported study.

## Temporal-memory boundary [literature_gap]
Fact ID: hockings-gap-temporal-memory
Source locator: Introducing ACES, Eqs. (1)–(2); Numerical results, paragraph beginning "We test our methods"; Conclusions, final two paragraphs
PDF page: 5
Claim: The source does not define a persistent physical or latent carrier, time-indexed noise parameters, a memory-length variable, a history-conditioned decoder prior or a matched history-access ablation.
Gap scope: source_local

The repeated “memory experiment” is a logical-storage task. The only discussion of device drift is
a prospective suggestion to combine ACES with separately cited online methods.

## Hardware-benefit boundary [literature_gap]
Fact ID: hockings-gap-hardware-benefit
Source locator: Conclusions, paragraph beginning "A natural next step"
PDF page: 5
Claim: The source does not evaluate noise-aware decoding on quantum-device syndrome records.
Gap scope: source_local

All ACES data, QEC records and decoder results reported by the source are generated in numerical
simulation.

## Wrong-model robustness boundary [literature_gap]
Fact ID: hockings-gap-memory-mismatch
Source locator: Numerical results; Appendix A; Conclusions
PDF page: 10
Claim: The source does not test a decoder frozen under an incorrect temporal-memory law, mixed mechanisms, stale calibration, non-Pauli residual noise or held-out device distribution shift.
Gap scope: source_local

Finite-shot ACES and tuned depolarising priors probe calibration precision and loss of static
gate-level detail inside the declared Pauli setting.

## Frozen-transfer boundary [literature_gap]
Fact ID: hockings-gap-transfer
Source locator: Numerical results, paragraphs beginning "First, we examine" and "Next, we test"; Conclusions, paragraph beginning "A natural next step"
PDF page: 5
Claim: The source does not evaluate one frozen decoder prior or calibrated model without re-estimation across an independent code family, physical device or held-out operating regime.
Gap scope: source_local

The demonstrated distance range remains within one XZZX surface-code family, and distance 25 uses a
single fixed-seed synthetic noise instance.

## End-to-end cost boundary [literature_gap]
Fact ID: hockings-gap-end-to-end-cost
Source locator: Conclusions; Appendix A, final two paragraphs
PDF page: 10
Claim: The source does not report measured quantum-device calibration time, recalibration cadence, decoder-runtime comparisons or a quantitative error bound for its large-scale covariance and projection reductions.
Gap scope: source_local

The reported under-four-second value covers laptop-based classical ACES processing for the simulated
distance-25 circuit, and the about-two-second collection value is projected.

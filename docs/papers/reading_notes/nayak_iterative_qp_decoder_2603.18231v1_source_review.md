+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2603.18231"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2603.18231v1"
source_artifact = "outputs/overview/literature/final_expansion/sources/2603.18231.pdf"
source_sha256 = "faf25f0c0c253199a5f45c4e5f511dcc2ec97ffad3761769780f1f118e264945"
title = "Iterative Decoding of Stabilizer Codes under Radiation-Induced Correlated Noise"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round2/NAYAK_ITERATIVE_QP_DECODER_2603_18231_AUDIT_2026-08-05.md"
audit_packet_sha256 = "3e4624b21280b1cfcc59c5363c61a5089f73b6ce0c6291367f9986ec3274b15e"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/expand_observation_attribution"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

[[relations]]
predicate = "defines"
object_id = "nayak-latent-qp-field"
object_type = "model"
object_label = "latent quasiparticle-density field"
fact_id = "nayak-latent-field"

[[relations]]
predicate = "derives"
object_id = "nayak-qec-priors"
object_type = "model"
object_label = "field-conditioned Pauli probabilities"
fact_id = "nayak-circuit-noise-model"

[[relations]]
predicate = "uses"
object_id = "nayak-iterative-decoder"
object_type = "method"
object_label = "BP+OSD with latent-field estimation"
fact_id = "nayak-decoder-configurations"

[[relations]]
predicate = "supports"
object_id = "nayak-selected-event-benefit"
object_type = "observable"
object_label = "selected-event logical-error reduction"
fact_id = "nayak-matched-contrast"

[[relations]]
predicate = "limits"
object_id = "nayak-event-selection-boundary"
object_type = "limitation"
object_label = "full-horizon event-selection rule"
fact_id = "nayak-event-selection"
+++
# Full-text review — Nayak et al., "Iterative Decoding of Stabilizer Codes under Radiation-Induced Correlated Noise"

## Source identity [paper_fact]
Fact ID: nayak-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The fixed source is the 14-page arXiv:2603.18231v1 preprint by Anuj K. Nayak and coauthors, dated 18 March 2026.

The artifact contains the main text, Appendices A–F and references.

## Selection scope [paper_fact]
Fact ID: nayak-selection-scope
Source locator: Abstract; Main Sec. I
PDF page: 1
Claim: The source develops and simulates joint syndrome decoding and latent quasiparticle-density estimation for repeated stabilizer-code memories under radiation-induced correlated noise.

The two demonstrations use a nominal distance-7 rotated surface code and a
`[[72,12,6]]` bivariate-bicycle qLDPC code.

## Latent QP representation [paper_fact]
Fact ID: nayak-latent-field
Source locator: Main Secs. II.A and III.A; Eq. (1)
PDF page: 2
Claim: A latent quasiparticle-density field carries the model's spatial and temporal dependence through graph-based diffusion, trapping and stochastic process fluctuations.

The implemented state transition is linear: it omits the quadratic recombination term from the
preceding physical equation and absorbs sparse QP injection into process noise. The field is sampled
once per microsecond and treated as quasi-static within a QEC cycle.

## Field-conditioned circuit noise [paper_fact]
Fact ID: nayak-circuit-noise-model
Source locator: Main Sec. III.B; Eq. (2)
PDF page: 3
Claim: The source derives field-conditioned Pauli probabilities from local `T1` and `T2` relations and treats circuit faults as conditionally independent but non-identically distributed when the instantaneous field is known.

QP-induced radiation error is the only physical noise in the simulation, and the faults are
Pauli-twirled. Correlation therefore enters through uncertainty about the shared classical field.

## Detector-error-model interface [paper_fact]
Fact ID: nayak-dem-interface
Source locator: Main Sec. III.C; Appendix A
PDF page: 3
Claim: Circuit Pauli faults with the same detector signature are grouped into detector-error-model mechanisms whose sparse supports extend over at most two adjacent QEC cycles.

The probability of a mechanism is approximated by summing its constituent single-fault
probabilities, under the assumption that simultaneous constituent faults are negligible.

## Generative dependency chain [paper_fact]
Fact ID: nayak-generative-chain
Source locator: Main Sec. III.D; Fig. 2
PDF page: 4
Claim: The graphical model connects physical parameters to the latent QP trajectory, circuit Pauli faults, detector-error mechanisms and the observed detector record.

The decoder observes detector events. The G4CMP QP field supplies simulation truth and the priors of
the genie configuration.

## Variational approximation boundary [paper_fact]
Fact ID: nayak-variational-boundary
Source locator: Main Sec. IV; Appendix B
PDF page: 4
Claim: The variational formulation retains approximation residuals from degeneracy, a mean-field error-mechanism prior and the Bethe posterior used by belief propagation.

The proposed alternating updates optimize the tractable terms rather than the exact joint posterior.

## Gradient-based field inference [paper_fact]
Fact ID: nayak-algorithm-one
Source locator: Main Sec. V.A; Algorithm 1
PDF page: 6
Claim: Algorithm 1 alternates field-conditioned belief propagation with gradient ascent on the log-QP trajectory and runs either over the full record or in sliding windows that commit leading decoded cycles.

The full-horizon form is offline. The principal bounded-window configuration uses a 20-cycle window,
a 10-cycle stride and repeated BP–gradient outer iterations.

## EKF field inference [paper_fact]
Fact ID: nayak-algorithm-two
Source locator: Main Sec. V.B; Algorithm 2
PDF page: 7
Claim: Algorithm 2 converts BP mechanism marginals into approximate per-qubit QP pseudo-measurements and updates a log-space field with an extended Kalman filter.

Its principal online configuration uses a two-cycle window and one-cycle stride. The recursion assumes
log-normal state dynamics, Gaussian pseudo-measurement noise and first-order propagation of a dense
field covariance.

## Shared decoder backend and configurations [paper_fact]
Fact ID: nayak-decoder-configurations
Source locator: Main Sec. VI.A
PDF page: 7
Claim: The five principal configurations use BP+OSD with latent-field estimation, genie field knowledge or a fixed uniform prior, while sharing 20 sum-product BP iterations and OSD order 10.

The configurations are full-horizon genie, full-horizon gradient inference, 20-cycle sliding gradient
inference, two-cycle online EKF and two-cycle fixed-uniform decoding.

## Simulation generator and QEC reach [paper_fact]
Fact ID: nayak-simulation-reach
Source locator: Main Sec. VI.A; Figs. 3–4
PDF page: 7
Claim: G4CMP trajectories on a 40 mm by 40 mm chip drive Stim simulations of a nominal distance-7 rotated surface code and a `[[72,12,6]]` BB-qLDPC code with 921-nanosecond stabilizer cycles.

The QP field is discretized on a 32 by 32 grid at one-microsecond resolution. The two code layouts
have different spatial geometries and receive separately selected model parameters.

## Surface-code count inconsistency [paper_fact]
Fact ID: nayak-surface-count-anomaly
Source locator: Main Secs. II.B and VI.A; Fig. 3
PDF page: 7
Claim: The source's surface-code size reporting is internally inconsistent because it calls `n=2d^2-1=97` the number of data qubits and adds 48 ancillas, while Fig. 3 depicts 97 total code-qubit markers.

The figure contains 49 white data-qubit markers and 48 stabilizer-measurement markers. The nominal
distance and code family are therefore less ambiguous than the printed physical-qubit count.

## Detailed parameter-selection procedure [paper_fact]
Fact ID: nayak-parameter-selection
Source locator: Appendix E; Table II
PDF page: 12
Claim: Appendix E tunes diffusion, trapping and process-noise parameters separately for each code using full-horizon Algorithm 1 on ten G4CMP events and reuses each code's selected parameters for the other algorithm choices.

The objective is average maximum log-space field MSE. The sentence describing the tuning set says it
“does not include both sample 53 and 58,” which does not unambiguously identify the ten indices.

## Parameter-selection wording discrepancy [paper_fact]
Fact ID: nayak-parameter-wording-anomaly
Source locator: Main Sec. VI.A; Appendix E
PDF page: 12
Claim: The main text says hyperparameters are selected “per algorithm and code,” whereas Appendix E says full-horizon Algorithm 1 is tuned per code and its parameters are reused across algorithm choices.

The detailed Appendix-E procedure is the more specific account, but the two descriptions are not
worded consistently.

## Event-selection rule [paper_fact]
Fact ID: nayak-event-selection
Source locator: Appendix F.1; Figs. 7–8
PDF page: 12
Claim: A full-horizon event-selection rule at `T_w=T=50 microseconds` chooses surface-code event 58 and BB-qLDPC event 53 as the largest uniform-to-genie PLE ratios among 64 simulated muon events.

The reported maximum ratios are 3.424 and 4.763, respectively. This selection uses the fixed-uniform
and genie configurations, not the proposed field estimators.

## All-event genie and uniform comparison [paper_fact]
Fact ID: nayak-all-event-prior-gap
Source locator: Appendix F.1; Figs. 7–8
PDF page: 12
Claim: Across 64 events, the surface-code mean PLE is `0.04202` with genie priors and `0.05342` with uniform priors, while the BB-qLDPC means are `0.02180` and `0.05815`.

The source also reports the mean of individual uniform-to-genie ratios as 1.167 for the surface code
and 2.181 for the BB-qLDPC code. These are not ratios of the corresponding means.

## Selected surface-code result [paper_fact]
Fact ID: nayak-surface-selected-result
Source locator: Main Sec. VI.B.2; Fig. 6
PDF page: 8
Claim: For selected surface-code event 58 at 100 microseconds, plotted PLE values are 0.09 for genie priors, 0.12 for offline gradient inference, 0.19 for sliding gradient inference, 0.23 for online EKF and 0.28 for the fixed uniform prior.

The source describes this event-specific comparison as demonstrative rather than as an average over
the 64-event set.

## Selected BB-qLDPC result [paper_fact]
Fact ID: nayak-bb-selected-result
Source locator: Main Sec. VI.B.2; Fig. 6
PDF page: 8
Claim: For selected BB-qLDPC event 53 at 100 microseconds, Fig. 6 gives PLE values of 0.12 for genie priors, 0.18 for offline gradient inference, 0.26 for sliding gradient inference, 0.52 for online EKF and 0.76 for the fixed uniform prior.

The source cautions that the absolute values and the ordering of algorithms can vary with the event
and code geometry.

## Narrow online-versus-uniform contrast [paper_fact]
Fact ID: nayak-matched-contrast
Source locator: Main Secs. VI.A–B; Fig. 6
PDF page: 8
Claim: The selected-event logical-error reduction from 0.28 to 0.23 for the surface code and from 0.76 to 0.52 for the BB-qLDPC code compares online EKF with a fixed uniform prior at common event, code, `T_w=2`, `t_s=1`, BP-20 and OSD-10 settings.

Only the EKF arm performs field inference, so this is a matched information/intervention contrast but
not an equal-computation comparison.

## Estimation-error interpretation [paper_fact]
Fact ID: nayak-mse-ple-boundary
Source locator: Main Sec. VI.B.2
PDF page: 8
Claim: The paper reports aligned MSE and PLE rankings for its principal configurations but explicitly states that it has not established a formal monotone relationship between field-estimation MSE and PLE.

The stated empirical alignment is limited to the tested configurations and two code instances.

## Computational trade-off [paper_fact]
Fact ID: nayak-computational-tradeoff
Source locator: Main Sec. VI.C; Table I
PDF page: 8
Claim: The paper assigns Algorithm 1 cost `O(K n T_w (I_BP+M))` and memory `O(n T_w)`, versus Algorithm 2 cost `O(n T_w I_BP+T_w n^3)` and memory `O(n^2)`.

These are asymptotic per-window cost and memory expressions; the source does not present a measured
wall-clock or end-to-end hardware latency benchmark.

## Additional-window result [paper_fact]
Fact ID: nayak-additional-window-result
Source locator: Appendix F.4; Fig. 13
PDF page: 13
Claim: On the selected events, a three-cycle EKF gives PLE 0.15 for the surface code and 0.28 for the BB-qLDPC code, versus 0.19 and 0.26 for the 20-cycle sliding gradient method despite the EKF's worse field-estimation accuracy.

The source attributes the surface-code advantage to prompt inflation of burst-onset priors and notes
that logical loss can be more sensitive to missed burst detections than to later false alarms.

## Short-window false alarms [paper_fact]
Fact ID: nayak-short-window-false-alarms
Source locator: Appendix F.2
PDF page: 13
Claim: The two-cycle EKF produces isolated high-density false alarms in the reconstructed field, while extending its window to three cycles suppresses those artifacts but does not remove burst-peak underestimation.

The paper associates the two-cycle artifacts with limited syndrome context and amplification by the
log-normal approximation.

## Figure-7 caption anomaly [paper_fact]
Fact ID: nayak-figure-seven-anomaly
Source locator: Appendix Fig. 7 caption
PDF page: 13
Claim: Figure 7's caption calls the Fig. 3 layout a `[[72,12,6]]` surface code even though the surrounding text and Fig. 3 identify it as the nominal distance-7 surface-code case.

Figure 8 contains the corresponding BB-qLDPC event-selection plot.

## Figure-13 reporting anomalies [paper_fact]
Fact ID: nayak-figure-thirteen-anomalies
Source locator: Appendix Fig. 13 and caption
PDF page: 14
Claim: Figure 13 is captioned “using Alg. 1” although its legend includes genie, uniform and both proposed algorithms, and its BB two-cycle uniform bar is 0.73 whereas Fig. 6 reports 0.76 for that named configuration.

The source does not reconcile either discrepancy. Figure 13 also introduces a full-horizon uniform
configuration that is not one of the five principal Fig. 6 arms.

## Proposed-algorithm population boundary [literature_gap]
Fact ID: nayak-gap-all-event-algorithms
Source locator: Appendix F.1 all-event analysis
PDF page: 12
Claim: The source does not report all-event mean PLE for Algorithm 1 or Algorithm 2 across the 64-event set.
Gap scope: source_local

Only the genie and fixed-uniform configurations receive 64-event aggregate values; headline results
for the proposed algorithms use the selected events.

## PLE uncertainty boundary [literature_gap]
Fact ID: nayak-gap-ple-uncertainty
Source locator: Main Sec. VI.B.2; Fig. 6
PDF page: 8
Claim: The source does not state a PLE shot count, confidence interval, seed variation or uncertainty bar for its selected-event decoder comparisons.
Gap scope: source_local

The displayed numbers therefore do not support a source-local precision or significance statement.

## Experimental-observation boundary [literature_gap]
Fact ID: nayak-gap-hardware-observation
Source locator: Main Secs. VI–VII
PDF page: 9
Claim: The source does not analyse a hardware syndrome record, a measured QP field or a synchronized external-particle record.
Gap scope: source_local

G4CMP-generated fields are simulation inputs, so the radiation/QP mechanism is assumed by the
generator rather than experimentally discriminated in this work.

## Model-robustness boundary [literature_gap]
Fact ID: nayak-gap-model-robustness
Source locator: Main Sec. VII
PDF page: 9
Claim: The source does not test mixed background noise, an incorrect field-evolution law, an incorrect QP-to-Pauli map or experimental calibration mismatch.
Gap scope: source_local

The fixed-uniform prior tests one prior-information mismatch within the same QP/Pauli generator, not
robustness to a different generative mechanism.

## Transfer boundary [literature_gap]
Fact ID: nayak-gap-transfer
Source locator: Appendix E; Appendix F.1
PDF page: 12
Claim: The source does not test a frozen estimator on a held-out code, device or physical noise mechanism.
Gap scope: source_local

Parameters are selected separately per code, and the two headline code results use different chosen
events.

## Strict non-Markovianity boundary [literature_gap]
Fact ID: nayak-gap-strict-nonmarkovianity
Source locator: Main Secs. III.A–B
PDF page: 3
Claim: The source does not establish strict quantum non-Markovianity or retention of a quantum environment across QEC cycles.
Gap scope: source_local

Its temporal dependence is represented by a classical Markov QP field, conditional on which the
Pauli faults are independent.

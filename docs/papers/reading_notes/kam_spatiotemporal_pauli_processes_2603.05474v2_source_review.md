+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2603.05474"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2603.05474v2"
source_artifact = "docs/papers/2603.05474v2.pdf"
source_sha256 = "3929443fb4587fefdd675dd611e05c9ce41ec4d8d0aea774bc8efb8bb0407c80"
title = "Spatiotemporal Pauli processes: Quantum combs for modelling correlated noise in quantum error correction"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion/KAM_SPP_PROCESS_COMB_2603_05474_AUDIT_2026-08-05.md"
audit_packet_sha256 = "d3adc19340551a71a0115039a39ee5b0fa4c10b2a436a1e6d308ac9bfa2093bf"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-spp-2026-08-05"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 35, 36, 37, 38, 39, 40, 48, 49, 50, 51, 52, 53, 54]

[[relations]]
predicate = "defines"
object_id = "kam-spp-process-tensor"
object_type = "model"
object_label = "spatiotemporal Pauli process"
fact_id = "spp-twirl-theorem"

[[relations]]
predicate = "defines"
object_id = "kam-spp-pauli-trajectories"
object_type = "observable"
object_label = "joint probability distribution over Pauli trajectories"
fact_id = "spp-twirl-theorem"

[[relations]]
predicate = "uses"
object_id = "kam-spp-sampled-stabilizer-method"
object_type = "method"
object_label = "Monte Carlo sampling, Stim propagation, and correlation-blind MWPM"
fact_id = "spp-qec-computation"

[[relations]]
predicate = "defines"
object_id = "kam-spp-storm-hmm"
object_type = "model"
object_label = "two-state calm/storm hidden Markov model"
fact_id = "spp-storm-model"

[[relations]]
predicate = "derives"
object_id = "kam-spp-qca-pca-mapping"
object_type = "model"
object_label = "probabilistic-cellular-automaton hidden Markov model"
fact_id = "spp-qca-pca-mapping"

[[relations]]
predicate = "supports"
object_id = "kam-spp-fixed-marginal-logical-effect"
object_type = "observable"
object_label = "increasing temporal correlation length at fixed single-round marginals"
fact_id = "spp-storm-qec-result"
+++
# Full-text review — Kam et al., "Spatiotemporal Pauli processes"

## Source identity [paper_fact]
Fact ID: spp-source-identity
Source locator: Title page and arXiv version stamp
PDF page: 1
Claim: The fixed source is arXiv:2603.05474v2, dated 6 March 2026, by John F. Kam, Angus Southwell, Spiro Gicev, Muhammad Usman, and Kavan Modi.

The artifact is a 54-page preprint. No publisher version is claimed for this fixed source.

## Selection scope [paper_fact]
Fact ID: spp-selection-scope
Source locator: Abstract, paragraph 1
PDF page: 1
Claim: The source develops a multi-time Pauli-process representation and tests two constructed correlated-noise models in repeated rotated-surface-code memory or stability simulations.

The two demonstrations are a temporally correlated calm/storm process and a spatially interacting
quantum-cellular-automaton bath. The study does not fit either process to new hardware data.

## Process-tensor representation [paper_fact]
Fact ID: spp-process-tensor
Source locator: Sec. 2.4, Eqs. (8)–(12)
PDF page: 9
Claim: A process tensor maps an ordered sequence of interventions to a conditional output state and thereby represents the multi-time input–output statistics of an open system.

Its Choi representation is contracted with the Choi operators of the interventions. The object must
satisfy causal trace constraints; it is not merely an uncontrolled time series.

## Formal distinctions among temporal processes [paper_fact]
Fact ID: spp-formal-distinctions
Source locator: Sec. 2.4, Eqs. (12)–(16)
PDF page: 10
Claim: The source distinguishes process separability from Markov factorisation: a process-separable comb can retain classical temporal dependence, whereas the Markov form factorises into independent single-step channels.

In the paper's process-tensor definitions, a fully Markovian process has neither quantum nor
classical temporal correlations; process separability removes only quantum temporal entanglement
and does not imply factorisation of trajectory statistics.

## Stinespring tensor-network carrier [paper_fact]
Fact ID: spp-stinespring-mpo
Source locator: Sec. 3.1, Eqs. (24)–(28)
PDF page: 13
Claim: Re-indexing finite-dimensional system–environment Stinespring dynamics gives a temporal matrix-product-operator representation whose internal bond is carried by the environment Liouville space and is bounded by d_E squared.

The bond represents the memory retained between time steps. This is a representation statement, not
an efficient-QEC benchmark by itself.

## Higher-dimensional tensor-network trade-off [paper_fact]
Fact ID: spp-higher-dimensional-tradeoff
Source locator: Sec. 3.2, Eqs. (29)–(30) and following discussion
PDF page: 14
Claim: Spatial factorisation promotes the temporal MPO to a spatiotemporal tensor network, but the source states that two-dimensional networks are generally not both exactly and efficiently contractible.

Spatial SVD truncation determines spatial bond dimensions, while temporal bonds remain bounded by
the environment size. Approximate contraction cost depends on correlations across the chosen
contraction direction.

## Multi-time Pauli-twirl theorem [paper_fact]
Fact ID: spp-twirl-theorem
Source locator: Sec. 4.1, Theorem 4.3 and Eqs. (32)–(36); proof in Appendix B
PDF page: 16
Claim: Applying the multi-time Pauli twirl to a process tensor produces a spatiotemporal Pauli process that is process-separable and has a joint probability distribution over Pauli trajectories.

The operation removes genuinely quantum temporal correlations from the effective process while
allowing arbitrary classical temporal correlations. Appendix B proves process separability by
diagonalising the twirled comb in a product Bell basis.

## Operational interpretation of twirling [paper_fact]
Fact ID: spp-operational-twirl
Source locator: Sec. 4.1, paragraph following Eq. (37)
PDF page: 17
Claim: The multi-time twirl is an operational effective description under Pauli-frame randomisation or related randomisation protocols, not a claim that the microscopic system–environment dynamics have literally become process-separable.

For QEC, the resulting object can be interpreted as an effective correlated circuit-level Pauli-noise
process under the assumed protocol.

## Local SPP tensor-network construction [paper_fact]
Fact ID: spp-local-tn-construction
Source locator: Sec. 4.2, Eqs. (38)–(48), Lemma 4.7, and Corollary 4.8
PDF page: 19
Claim: Fixed local Pauli-tensor contractions on the physical legs yield an SPP MPS or PEPS while leaving the virtual environment bonds unchanged, and the temporal bond dimension is no greater than the corresponding process-tensor bond.

For a finite environment the displayed temporal bound is d_E squared. The bond needed by a
particular SPP can be smaller after the projection.

## Transfer-operator diagnostics [paper_fact]
Fact ID: spp-transfer-diagnostics
Source locator: Secs. 5.1–5.2, Eqs. (53)–(65)
PDF page: 25
Claim: For a time-homogeneous ergodic SPP MPS, transfer and emission operators express multi-time correlations, and under the stated diagonalizability assumptions the subleading transfer eigenvalue controls asymptotic exponential correlation decay.

The source notes that non-normal transfer operators can require more than eigenvalues alone and that
complex or degenerate leading eigenvalues change the simple relaxation interpretation.

## Conditional HMM equivalence [paper_fact]
Fact ID: spp-hmm-condition
Source locator: Sec. 5.4, Eqs. (69)–(75)
PDF page: 28
Claim: A time-homogeneous SPP MPS of bond dimension D is isomorphic to an edge-emitting hidden Markov model with D hidden states when a nonnegative row-stochastic representation of that bond dimension exists.

The source presents this condition as sufficient rather than necessary and does not solve the minimal
HMM-realisation problem for a general SPP.

## Fixed-marginal storm model [paper_fact]
Fact ID: spp-storm-model
Source locator: Sec. 6.2, Eqs. (76)–(81)
PDF page: 30
Claim: The paper defines a two-state calm/storm hidden Markov model whose spectral gap and correlation length can be varied while keeping its stationary one-round Pauli-error marginal fixed.

The hidden state evolves with injection probability a and relaxation probability b. Equation (81)
writes the stationary one-round marginal as the stationary-state-weighted mixture of calm and storm
emissions. The paper states that Eqs. (79) and (81) are solved for a and b to tune correlation length
while holding that marginal fixed, under 0 ≤ a,b ≤ 1 and a+b<1.

## QEC-facing variables and computation [paper_fact]
Fact ID: spp-qec-computation
Source locator: Secs. 6.1 and 6.3, Fig. 8 and simulation protocol
PDF page: 31
Claim: The demonstrated QEC calculation samples one SPP Pauli string at the start of each round, composes it with independent 0.1-percent circuit-level noise, propagates the circuit with Stim, and decodes using Monte Carlo sampling, Stim propagation, and correlation-blind MWPM.

The decoder is built from a detector-error model with the same single-round marginal and does not use
the temporal correlations. The logical outputs are memory error per round or stability-experiment
logical failure.

## Demonstrated repeated-QEC reach [paper_fact]
Fact ID: spp-demonstrated-reach
Source locator: Secs. 6.3–6.4, Figs. 9–10
PDF page: 32
Claim: The storm benchmarks cover rotated-surface-code memory distances 5, 7, ..., 19 for 3d rounds and stability experiments of diameter 4 for 5, 10, ..., 35 rounds, with reported probabilities estimated from 10 million Monte Carlo shots.

This reach belongs to sampled Pauli trajectories in stabilizer circuits; it is not an exact contraction
of an arbitrary microscopic two-dimensional process tensor at those scales.

## Fixed-marginal logical result [paper_fact]
Fact ID: spp-storm-qec-result
Source locator: Sec. 6.4, Figs. 9–10
PDF page: 33
Claim: In the tested storm process, increasing temporal correlation length at fixed single-round marginals worsens logical memory and stability performance under the fixed correlation-blind decoder.

Within the simulated memory range the fitted distance dependence remains approximately exponential
but weakens as the correlation length grows. The comparison does not separate intrinsic code
sensitivity from the penalty due to decoder mismatch.

## Microscopic QCA construction [paper_fact]
Fact ID: spp-qca-construction
Source locator: Sec. 7.1, Eqs. (82)–(92)
PDF page: 35
Claim: The microscopic example uses local system and environment qubits, stochastic bath injection and relaxation, bipartite controlled-rotation QCA steps, and a controlled system–environment unitary satisfying a Hilbert–Schmidt orthogonality condition.

It is a constructed local and causal model. Its parameters are not inferred from a physical device in
this study.

## QCA-to-PCA mapping [paper_fact]
Fact ID: spp-qca-pca-mapping
Source locator: Secs. 7.1–7.2 and Appendix C, Eqs. (C3)–(C36)
PDF page: 54
Claim: Under the declared system twirl, the constructed QCA maps exactly to a probabilistic-cellular-automaton hidden Markov model with bath-state flips of probability sin squared of k theta and conditional Pauli emissions.

The derivation uses twirl-induced computational-basis dephasing of the environment and bipartite
half-step updates. The exactness is conditional on the model and interaction assumptions, not a
general reduction of arbitrary quantum baths to classical automata.

## Finite-size bath diagnostics [paper_fact]
Fact ID: spp-qca-bath-diagnostics
Source locator: Sec. 7.3, Eqs. (94)–(95) and Fig. 11
PDF page: 38
Claim: For lattice sizes corresponding to distances 9, 11, 13, and 15, the simulated QCA-derived bath shows a sharp finite-size crossover near theta approximately 0.39 pi, with peaks in scaled variance and fitted density-correlation time.

The bath statistics use 1 million cycles, discard a 200-thousand-cycle burn-in, and average over ten
independent trajectories. The paper calls the regime pseudo-critical; its correlation time is obtained
from a single-exponential fit and reaches approximately 140 cycles for distance 9 in the plotted data.

## QCA logical-performance result [paper_fact]
Fact ID: spp-qca-qec-result
Source locator: Sec. 7.4 and Fig. 12
PDF page: 39
Claim: In the tested QCA-derived process, rotated-surface-code memory performance degrades sharply in the finite-size pseudo-critical window and the plotted distance trend reverses above theta approximately 0.39 pi under marginalised MWPM.

The benchmark uses distances 5 through 17 for 3d rounds, 0.1-percent baseline circuit-level noise,
numerically estimated single-round marginals, and an all-zero bath initialisation for each shot. It does
not demonstrate a thermodynamic critical point or a correlation-aware decoding recovery. Because it
uses correlation-blind marginalised MWPM, it does not isolate intrinsic code sensitivity from decoder
mismatch.

## No hardware observation or device attribution [literature_gap]
Fact ID: spp-gap-observation-attribution
Source locator: Complete study design and Sec. 8
PDF page: 40
Claim: The source does not collect new hardware records, fit the storm or QCA process to a device, or identify a microscopic cause for temporal structure in a measured repeated-QEC record.
Gap scope: source_local

Experimental burst mechanisms are cited for qualitative context; they do not validate the constructed
models as explanations of those devices.

## No demonstrated memory-aware intervention benefit [literature_gap]
Fact ID: spp-gap-intervention-benefit
Source locator: Sec. 7.4 and Sec. 8 discussion of future directions
PDF page: 40
Claim: The source does not benchmark a correlation-aware decoder, reset intervention, schedule change, or memory-aware control against a matched baseline.
Gap scope: source_local

The demonstrated MWPM decoder uses marginalised error rates. Correlation-aware decoding,
reweighting, model learning, and mitigation are proposed extensions.

## No transfer demonstration [literature_gap]
Fact ID: spp-gap-transfer
Source locator: Complete numerical study and Sec. 8
PDF page: 40
Claim: The source does not demonstrate transfer of a learned model, quantitative logical effect, or intervention benefit across a calibrated device, distinct code family, or distinct decoder family.
Gap scope: source_local

The two constructed models broaden the paper's internal examples but do not constitute external
transfer validation.

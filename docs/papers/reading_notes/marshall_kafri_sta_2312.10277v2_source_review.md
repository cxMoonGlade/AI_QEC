+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2312.10277"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2312.10277v2"
source_artifact = "outputs/papers/coherent_leakage_longrange_closure/2312.10277v2.pdf"
source_sha256 = "82ddaa228d8b13e0f55a5fb1c1d18e688698698ffd102823fb0f4e47d10a6ada"
title = "Incoherent Approximation of Leakage in Quantum Error Correction"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round2/MARSHALL_KAFRI_STA_2312_10277_AUDIT_2026-08-05.md"
audit_packet_sha256 = "f4f7503b901de07947e13495b2a2a1fffe068fc61dd6c506a586ed208c58298e"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-round2"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23]

[[relations]]
predicate = "defines"
object_id = "marshall-subspace-twirling-approximation"
object_type = "model"
object_label = "Subspace Twirling Approximation"
fact_id = "marshall-sta-definition"

[[relations]]
predicate = "uses"
object_id = "marshall-kraus-trajectories"
object_type = "method"
object_label = "pure-state Kraus trajectories"
fact_id = "marshall-trajectory-method"

[[relations]]
predicate = "measures"
object_id = "marshall-repeated-qec-output"
object_type = "observable"
object_label = "logical memory outcomes"
fact_id = "marshall-qec-interface"

[[relations]]
predicate = "supports"
object_id = "marshall-coherent-leakage-stress-model"
object_type = "model"
object_label = "coherent CZ-leakage model"
fact_id = "marshall-coherent-stress-result"
+++
# Full-text review — Marshall and Kafri, "Incoherent Approximation of Leakage in Quantum Error Correction"

## Source identity [paper_fact]
Fact ID: marshall-source-identity
Source locator: Title page, visible arXiv version stamp and pinned acquisition provenance
PDF page: 1
Claim: The fixed source is the 23-page arXiv:2312.10277v2 artifact by Jeffrey Marshall and Dvir Kafri, dated 5 March 2025 and published as *Physical Review Applied* 23, 054025 (2025), DOI `10.1103/PhysRevApplied.23.054025`.

The complete artifact includes the main text, Appendices A--G and references.

## Selection scope [paper_fact]
Fact ID: marshall-selection-scope
Source locator: Abstract; Secs. II--III; Discussion
PDF page: 1
Claim: The source develops an incoherent approximation for leakage channels and tests it against exact qutrit trajectory simulations of repeated repetition-code and rotated-surface-code memories.

The tests compare full-qutrit trajectories, the Subspace Twirling Approximation and, in one stress
case, an effective thermal leakage model fitted to exact leakage-population data.

## Markovian noise scope [paper_fact]
Fact ID: marshall-markovian-scope
Source locator: Sec. II.A, opening paragraph
PDF page: 2
Claim: Although the channel and trajectory presentation is general, the simulations in this source are explicitly restricted to Markovian noise models.

Leakage occupation may persist across repeated-QEC rounds in these models, but the paper does not
simulate a retained non-Markovian environment.

## Pure-state trajectory method [paper_fact]
Fact ID: marshall-trajectory-method
Source locator: Sec. II.A
PDF page: 2
Claim: The simulator uses pure-state Kraus trajectories, sampling a Kraus operator at each noisy operation according to its state-dependent Born probability and propagating a pure state to produce sampled channel events and measurement outcomes.

This replaces full density-matrix propagation by sampling and therefore introduces statistical
uncertainty while retaining the declared qutrit channel dynamics within each trajectory. For Hilbert
dimension `N`, the source contrasts naive density-matrix memory `O(N^2)` and time `O(N^3)` with
`O(N)` memory and time for a single trajectory when the initial state is pure and the sampled Kraus
operators have bounded locality.

## Dynamic circuit reordering [paper_fact]
Fact ID: marshall-dynamic-state-method
Source locator: Sec. II.B; Appendix B and Fig. 6
PDF page: 3
Claim: A dependency graph is used to reorder commuting circuit operations so that measured qubits can be destroyed and reset qubits created only when needed, reducing the peak surface-code state from `2d^2-1` qutrit locations to `d^2+1` active quantum systems.

The reordering preserves the graph's partial order and reduces memory cost, but the remaining state
vector still scales exponentially in the number of active systems.

## Subspace-twirling definition [paper_fact]
Fact ID: marshall-sta-definition
Source locator: Sec. II.C--D, Eqs. (8)--(14); Appendix A
PDF page: 5
Claim: The Subspace Twirling Approximation averages a channel over independent relative phases between chosen computational and leakage subspaces, removing inter-subspace coherence while preserving within-subspace amplitudes and explicit transitions between sectors.

The resulting strictly incoherent operation is implemented with a quantum state and a classical
subspace register. The source distinguishes this channel twirl from appending a complete dephasing
map after an otherwise unchanged channel and shows that it preserves process fidelity to the identity
under the definition in Eq. (14).

## Measurement-induced coherence decay [paper_fact]
Fact ID: marshall-coherence-decay
Source locator: Sec. III.A, Eqs. (15)--(17) and Fig. 1
PDF page: 7
Claim: In a simplified repeated-stabilizer calculation, computational--leakage cross-sector coherences decay with factors `cos(phi/2)^m` or `sin(phi/2)^m` after `m` measurements for a generic leakage-conditioned phase `phi`.

The derivation assumes no CZ-generated leakage, no measure-qubit leakage and no leakage on the other
data qubits. It supports phase- and schedule-dependent suppression, not instantaneous or universal
loss of coherence.

## QEC-facing interface [paper_fact]
Fact ID: marshall-qec-interface
Source locator: Sec. III.B; Appendix C; Appendices D--F
PDF page: 19
Claim: The repeated-QEC simulations return per-qubit leakage populations, marginal detector-event fractions and logical memory outcomes decoded with minimum-weight perfect matching.

A qutrit readout outcome `2` is randomized to binary `0` or `1`, and the decoder uses weights from a
fixed marginal depolarizing detector-error model rather than exploiting a temporal leakage record.

## Thermal exact-versus-STA result [paper_fact]
Fact ID: marshall-thermal-result
Source locator: Sec. III.B.1 prose, p. 9; Fig. 2, p. 10; Appendix E, Fig. 10, p. 20
PDF page: 9
Claim: For a distance-3 surface-code thermal heating model run for 50 rounds with at least one million samples, the leakage-added logical-error rate is `0.275 +/- 0.012%` under exact qutrit trajectories and `0.266 +/- 0.009%` under STA.

The model uses Markovian Lindblad heating, relaxation and dephasing, and the reported added rate is
defined by subtracting a leakage-free baseline.

## Coherent stress-test result [paper_fact]
Fact ID: marshall-coherent-stress-result
Source locator: Sec. III.B.2 prose, p. 9; Figs. 3--4 and discussion, pp. 10--11
PDF page: 10
Claim: Under a deliberately strong coherent CZ-leakage model, exact qutrit, naive STA and leakage-population-fitted thermal STA simulations give leakage-added logical-error rates of `0.384 +/- 0.015%`, `0.404 +/- 0.014%` and `0.365 +/- 0.010%`, respectively.

Across the displayed logical curves, the source reports mean error of 11.0% for naive STA and 2.9%
for the fitted thermal surrogate. This is a bounded stress test, not evidence that the fitted
surrogate is generally faithful.

## Source uncertainty anomaly [paper_fact]
Fact ID: marshall-source-anomaly
Source locator: Sec. III.B.2 prose, p. 9; Fig. 3 caption and discussion, p. 10
PDF page: 9
Claim: The prose prints the exact coherent-model uncertainty as `0.0015%`, whereas the visually checked Fig. 3 caption and later discussion give `0.015%`; this review uses the repeated figure-caption value and records the extra zero as a source-local inconsistency.

No scientific conclusion here depends on choosing the smaller printed uncertainty.

## Mixed-model repetition-code reach [paper_fact]
Fact ID: marshall-repetition-reach
Source locator: Appendix F.1 prose, pp. 20--21; Figs. 15--16, p. 22
PDF page: 20
Claim: For a mixed coherent-and-thermal leakage model, exact qutrit and STA trajectories are compared on repetition-code memories at distances 3, 5, 7 and 9 with at least 200,000 samples per point.

The displayed logical-rate trends do not show increasing approximation error with distance in this
tested family; at distance 9 the added detector-event fraction is 1.18% exact and 1.13% under STA.
This is an empirical comparison over specified parameters rather than a scaling theorem.

## Mixed-model surface-code comparison [paper_fact]
Fact ID: marshall-surface-d3-result
Source locator: Appendix F.2 prose, p. 21; Figs. 17--18, p. 22
PDF page: 21
Claim: In the distance-3 surface-code mixed model, fitted logical-error rates are 0.0248 without leakage, 0.0283 for exact qutrit dynamics and 0.0284 under STA, with intermediate-round exact-versus-STA differences reaching roughly 4% relative in the displayed curves.

The fixed marginal decoder and randomized handling of outcome `2` remain common limitations of this
comparison.

## Approximate distance-5 surface-code reach [paper_fact]
Fact ID: marshall-surface-d5-reach
Source locator: Fig. 5 and Discussion
PDF page: 11
Claim: The largest two-dimensional example is a distance-5 rotated surface-code memory through 25 rounds using STA only, with 49 physical qutrit locations represented by at most 26 active quantum systems and 5,000 samples.

Because there is no full-qutrit distance-5 comparator, this result demonstrates computational reach
of the approximation rather than its accuracy at that scale.

## Reported computational cost [paper_fact]
Fact ID: marshall-computational-cost
Source locator: Discussion, paragraph reporting distance-5 run time, p. 11
PDF page: 11
Claim: On one 2.7-GHz Intel Xeon Cascade Lake core, the distance-5 STA simulation takes approximately 2.5 minutes per sample per round.

The reported cost makes the reachable scale interpretable and rules out presenting the method as a
generally efficient large-code solver.

## Logical-rate fit boundary [paper_fact]
Fact ID: marshall-logical-fit-boundary
Source locator: Appendix D, Eqs. (D1)--(D2) and Fig. 9
PDF page: 19
Claim: Logical fidelity versus round count is fitted with `F_L(k)=A(1-2 epsilon_L)^k`, where the prefactor `A` is introduced because leakage transients are not represented by the single-rate decay model.

The extracted logical-error rate is therefore a summary of the simulated curves rather than a full
description of their transient temporal structure.

## No uniform approximation bound [literature_gap]
Fact ID: marshall-gap-uniform-bound
Source locator: Complete analytic and numerical scope, especially Sec. III and Figs. 2--5 and 10--18
PDF page: 12
Claim: The source does not establish a uniform STA error bound across leakage channels, round counts, code distances or code families.
Gap scope: source_local

Its support consists of an analytic coherence-decay argument under stated simplifying assumptions
and empirical exact-versus-STA comparisons at specified parameter points.

## No hardware observation or physical attribution [literature_gap]
Fact ID: marshall-gap-hardware-attribution
Source locator: Secs. II--III and Discussion, p. 12
PDF page: 12
Claim: The source reports simulations only; it does not collect hardware records, calibrate the tested leakage models to a device data set, or identify a microscopic cause from measured temporal structure.
Gap scope: source_local

Experimental parameter values motivate parts of the model, but they do not constitute device-level
observation or attribution in this study.

## No demonstrated memory-aware intervention benefit [literature_gap]
Fact ID: marshall-gap-memory-aware-benefit
Source locator: Appendix C decoder specification and complete comparison scope
PDF page: 19
Claim: The source does not compare a memory-aware decoder, leakage-conditioned decoder, reset policy, schedule intervention or memory-aware control against a matched baseline.
Gap scope: source_local

The decoder uses a fixed marginal depolarizing detector-error model, and qutrit readout outcome `2`
is randomized to a binary value before decoding.

## No external transfer demonstration [literature_gap]
Fact ID: marshall-gap-transfer
Source locator: Sec. III and Discussion, p. 12
PDF page: 12
Claim: The source does not demonstrate transfer of an STA calibration, fitted thermal surrogate, approximation error or logical-performance conclusion to a held-out device, code family or decoder family.
Gap scope: source_local

Applying the framework to repetition and rotated-surface-code simulations broadens the internal test
set but is not an external transfer test.

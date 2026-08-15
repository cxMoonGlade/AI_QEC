+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1801.05390"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1801.05390v2"
source_artifact = "docs/papers/1801.05390v2.pdf"
source_sha256 = "a5578205d15a7c44a11e0508e400109393c555be243d8478c20f668f75997f40"
title = "Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/EVENBLY_1801_05390_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "f2d08e18788f554677250709cbf74b8da4df34b76cc753bee08e2a8868c66be1"
admission_status = "source_only_reviewed"
admission_reviewer = "peps_carrier_source_round2_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 10, 11]

[[relations]]
predicate = "defines"
object_id = "bond-environment"
object_type = "concept"
object_label = "bond environment"
fact_id = "evenbly-bond-environment"

[[relations]]
predicate = "defines"
object_id = "full-environment-truncation"
object_type = "method"
object_label = "full-environment truncation"
fact_id = "evenbly-fet-objective"
+++
# Full-text review — Evenbly, “Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops”

## Source identity [paper_fact]
Fact ID: evenbly-source-identity
Source locator: Title page and version line
PDF page: 1
Claim: Glen Evenbly authored this May 2018 v2 article on gauge fixing and truncation in tensor networks with closed loops, published as Physical Review B 98, 085155.

The artifact contains the main construction, numerical examples, and four appendices.

## Bond environment [paper_fact]
Fact ID: evenbly-bond-environment
Source locator: Sec. II, Eq. (1) and Fig. 1
PDF page: 2
Claim: The bond environment `Upsilon` is obtained by contracting the state norm network while leaving a selected bond and its conjugate open, and contracting it with the two bond matrices recovers the state norm.

It is invariant under gauge choices on other internal indices and under joint external unitaries; for a bridge bond it factorizes into left and right parts.

## Weighted trace gauge definition [paper_fact]
Fact ID: evenbly-wtg-definition
Source locator: Sec. III, weighted-trace-gauge box and Eq. (2)
PDF page: 3
Claim: A bond is in weighted trace gauge when its left and right boundary matrices are proportional to identity and its bond matrix is positive diagonal with entries in descending order.

For bridge bonds the construction reduces to the Schmidt gauge and its coefficients equal the Schmidt coefficients.

## Weighted trace gauge construction [paper_fact]
Fact ID: evenbly-wtg-construction
Source locator: Sec. III, Eqs. (3)--(8) and Fig. 3
PDF page: 4
Claim: The WTG construction obtains dominant left and right transfer eigenoperators, factors their positive spectra, and singular-value decomposes the transformed bond matrix to determine the bond gauges.

Existence requires strictly positive support of the dominant eigenoperators, while degeneracy in the transfer problem or bond spectrum leaves the stated gauge ambiguities.

## Cyclic coefficients are not state invariants [paper_fact]
Fact ID: evenbly-cyclic-coefficients-limit
Source locator: Sec. IV, Eqs. (9)--(10) and Fig. 4
PDF page: 5
Claim: Two cyclic tensor networks can represent the same quantum state while having different WTG coefficients because one representation can contain physically redundant internal correlations around the loop.

The example separates correlations among external degrees of freedom from representation-internal loop correlations.

## Cycle entropy [paper_fact]
Fact ID: evenbly-cycle-entropy
Source locator: Sec. IV, Eq. (11)
PDF page: 5
Claim: Cycle entropy is the entropy of the normalized absolute transfer-operator eigenvalue spectrum and vanishes exactly when the selected bond can be realized as a bridge after a suitable external unitary cycle reduction.

When it vanishes, WTG coefficients coincide with Schmidt coefficients of that bridge realization; a sufficiently small value is proposed as a near-optimal-truncation diagnostic.

## Full-environment truncation objective [paper_fact]
Fact ID: evenbly-fet-objective
Source locator: Sec. V, Eq. (12) and Fig. 5
PDF page: 6
Claim: Full-environment truncation replaces a selected bond by a lower-rank factorization and chooses its factors to maximize normalized whole-network pure-state fidelity.

The fidelity depends only on the selected bond matrix and its complete bond environment once that environment has been contracted.

## FET alternating solve [paper_fact]
Fact ID: evenbly-fet-alternating-solve
Source locator: Appendix C, Eq. (C1) and Fig. 11
PDF page: 11
Claim: Holding one isometry fixed turns the FET fidelity into a generalized-eigenvalue problem with analytic solution `R=P B^{-1}`, after which an SVD updates the bond factors and the opposite side is optimized in turn.

The two one-sided steps are repeated until the factors converge sufficiently.

## FET benchmark and convergence qualification [paper_fact]
Fact ID: evenbly-fet-benchmark
Source locator: Sec. V, Table I and paragraph below the table
PDF page: 7
Claim: In three critical-Ising partition-function networks, FET produced smaller fidelity error than a cut-cycle Schmidt truncation and required fewer than twenty iterations in the reported trials.

The author says the observed initialization-independent convergence suggests a global minimum rather than presenting a general proof of one.

## Cut-cycle truncation limitation [paper_fact]
Fact ID: evenbly-cut-cycle-limit
Source locator: Appendix B, discussion surrounding Fig. 9
PDF page: 10
Claim: Turning a cyclic bond into a bridge by cutting other bonds is gauge- and cut-dependent and can preserve redundant internal correlations, so it is not generally an optimal truncation.

The FET comparison is motivated by removing those internal correlations through the full environment.

## Stochastic trajectory law not treated [literature_gap]
Fact ID: evenbly-gap-stochastic-law
Source locator: Full-text scope; Secs. II--VI and Appendices A--D
PDF page: 7
Claim: This source does not define stochastic trajectory branches or physical probabilities carried by unnormalized branch norms.
Gap scope: source_local

Its states and fidelities are deterministic tensor-network objects.

## Multi-time record bridge not treated [literature_gap]
Fact ID: evenbly-gap-record-bridge
Source locator: Full-text scope and Sec. VI discussion
PDF page: 7
Claim: This source does not establish a bound from local FET infidelity or cycle entropy to a joint multi-time measurement-record distribution.
Gap scope: source_local

The applications discussed are tensor optimization and coarse-graining rather than selective measurements and temporal records.

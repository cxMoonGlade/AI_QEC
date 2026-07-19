+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2309.15642"
source_version = "v3"
source_uri = "https://arxiv.org/abs/2309.15642v3"
source_artifact = "outputs/papers/2309.15642v3.pdf"
source_sha256 = "aafacaf117d5a3a536760900800f473ef2c806f0c4485838e24db44712bc7fc6"
title = "Efficient tensor network simulation of IBM's largest quantum processors"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/PATRA_2309_15642_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "12edb2c645922165aaefdc2c8e12913c9dcf97b5425699df86e292318bd394c2"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_peps_record_round3_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 5, 6, 7]
+++
# Source review — Patra et al.

## Kicked-Ising pure-state circuit [paper_fact]

Fact ID: fact.kicked-ising-pure-state-circuit
Source locator: Sec. II, Eqs. (1)--(3)
PDF page: 1
Claim: The simulated object is a spin-half pure state obtained by repeatedly applying a first-order-Trotter kicked-Ising unitary to the all-zero product state.

The lattice edges follow the IBM heavy-hex connectivity, the two-qubit terms are `ZZ` rotations, and the single-qubit terms are transverse `X` rotations.

## Graph-PEPS approximation [paper_fact]

Fact ID: fact.graph-peps-approximation
Source locator: Sec. III, Method
PDF page: 2
Claim: The finite and infinite heavy-hex simulations use graph-based PEPS with simple-update tensor truncation and a mean-field approximation for expectation-value environments.

The state bond dimension `chi` is also the truncation cap, and belief-propagation regauging after each Trotter step is tested as an optional variant.

## Five-step exact comparison [paper_fact]

Fact ID: fact.five-step-exact-comparison
Source locator: Sec. IV.A and Fig. 2
PDF page: 3
Claim: At five Trotter steps on 127 sites, the paper compares average magnetization and two higher-weight expectation values against an available light-cone exact result.

The reported magnetization error for bond dimension 32 is near machine precision, while the higher-weight observables require larger bonds in parts of the parameter range.

## Twenty-step bond sweep [paper_fact]

Fact ID: fact.twenty-step-bond-sweep
Source locator: Sec. IV.A and Fig. 3
PDF page: 3
Claim: At twenty Trotter steps, the single-site expectation value is swept over bond dimensions 64 through 512 and compared with an infinite-bond extrapolation from another tensor-network method because no exact reference is available.

The finite-entanglement plot tends toward saturation for the displayed `theta_h = 0.7` point but does not show clear saturation for `theta_h = 1.0` over the computed bonds.

## Long-depth self-convergence [paper_fact]

Fact ID: fact.long-depth-self-convergence
Source locator: Sec. IV.C and Figs. 5--7
PDF page: 5
Claim: For 37 to 39 Trotter steps, local and average magnetizations are compared across attainable bond dimensions for 127, 433, and 1121 sites.

The displayed relative errors use the largest computed bond at each size as the denominator rather than an independent exact state or observable.

## Critical-region nonmonotonicity [paper_fact]

Fact ID: fact.critical-region-nonmonotonicity
Source locator: Appendix A, Results near critical point
PDF page: 6
Claim: In the interval near the reported critical point, a lower-bond simple-update result can be closer to the exact higher-weight observable than results at larger bonds.

The authors attribute the nonmonotonic behaviour to long correlations that are poorly represented by the simple-update and local-environment approximations.

## Clifford high-weight rewrite [paper_fact]

Fact ID: fact.clifford-high-weight-rewrite
Source locator: Appendix B, Eqs. (B1)--(B4)
PDF page: 6
Claim: The Weight-10 and Weight-17 observables are evaluated by using the special Clifford circuit at `theta_h = pi/2` to rewrite them as single-site `Z` expectation values after additional forward and inverse unitary layers.

This avoids directly contracting the intricate loop environment of the high-weight operator.

## Heavy-hex local tree structure [paper_fact]

Fact ID: fact.heavy-hex-local-tree-structure
Source locator: Appendix C and Fig. 8
PDF page: 7
Claim: The paper contrasts the local environment of heavy-hex and square lattices: square-lattice neighbourhoods contain loops beyond one step, while the displayed heavy-hex neighbourhood first contains loops beyond five steps.

The authors use this local tree-like structure together with short correlations away from criticality to explain the success of simple update and local measurements in their benchmark.

## Deep-circuit independent reference [literature_gap]

Fact ID: gap.deep-circuit-independent-reference
Source locator: Sec. IV.A and Fig. 3(b)--(c)
PDF page: 3
Claim: The twenty-step non-Clifford results do not have an independent exact reference over the full parameter range.
Gap scope: source_local

They are assessed through bond sweeps and comparison with an extrapolation from another tensor-network calculation.

## Outcome-distribution accuracy [literature_gap]

Fact ID: gap.outcome-distribution-accuracy
Source locator: Sec. IV.A--C and Figs. 2--7
PDF page: 5
Claim: The paper does not bound a terminal bitstring distribution or a sequence of conditional measurement outcomes under finite bond dimension.
Gap scope: source_local

Its reported accuracy surfaces are selected expectation values for deterministic unitary evolution.

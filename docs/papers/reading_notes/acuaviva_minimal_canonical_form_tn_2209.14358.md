+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2209.14358"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2209.14358v1"
source_artifact = "outputs/papers/peps_foundation/2209.14358.pdf"
source_sha256 = "85cdfe99c2934496a7f9d12d50dbff040f0da6401d05b74d142678ef75f7c90c"
title = "The minimal canonical form of a tensor network"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/ACUAVIVA_2209_14358_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "29bf149422cd1d2272b45b3f171256703efa4eb68c52cd4da8c39b46e2be3b6f"
admission_status = "source_only_reviewed"
admission_reviewer = "peps_carrier_source_round3_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 20, 21, 22, 23, 29, 30, 31, 32, 34, 35, 36, 42, 44]

[[relations]]
predicate = "defines"
object_id = "minimal-canonical-form"
object_type = "concept"
object_label = "minimal canonical form"
fact_id = "acuaviva-minimal-canonical-definition"

[[relations]]
predicate = "supports"
object_id = "orbit-closure-state-invariance"
object_type = "theorem"
object_label = "orbit closure"
fact_id = "acuaviva-orbit-closure-invariance"
+++
# Full-text review — Acuaviva et al., “The minimal canonical form of a tensor network”

## Source identity [paper_fact]
Fact ID: acuaviva-source-identity
Source locator: Title page, arXiv version line, and abstract
PDF page: 1
Claim: Arturo Acuaviva, Visu Makam, Harold Nieuwboer, David Pérez-García, Friedrich Sittner, Michael Walter, and Freek Witteveen authored this arXiv v1 preprint dated 28 September 2022.

The source presents a geometric-invariant-theory construction for MPS and PEPS, together with canonical-form theorems, a fundamental theorem, and approximation algorithms.

## Uniform-PEPS gauge action [paper_fact]
Fact ID: acuaviva-uniform-peps-gauge-action
Source locator: Sec. 4.1, Definition 4.3
PDF page: 20
Claim: The uniform-PEPS gauge action applies `g_k` and `g_k^{-T}` to the two virtual legs in each direction `k` while acting as the identity on the physical leg.

For `G=GL(D_1)×...×GL(D_m)`, the action is simultaneous conjugation of each matrix tuple by the Kronecker product of the direction gauges.

## Orbit-closure state invariance [paper_fact]
Fact ID: acuaviva-orbit-closure-invariance
Source locator: Sec. 4.1, Lemma 4.4 and Definition 4.5
PDF page: 21
Claim: Every tensor in the orbit closure of a uniform PEPS tensor gives exactly the same state on every finite arbitrary contraction graph.

The equality follows for gauge transforms and extends to their limits by continuity; the paper consequently defines gauge equivalence by intersection of two gauge-orbit closures.

## Minimal canonical form definition [paper_fact]
Fact ID: acuaviva-minimal-canonical-definition
Source locator: Sec. 4.2, Definition 4.6 and Theorem 4.7
PDF page: 21
Claim: A minimal canonical form is a minimum-Frobenius-norm tensor in the gauge-orbit closure, and all such minima are unique up to the product unitary gauge group.

Two tensors have unitary-related minimal canonical forms exactly when their gauge-orbit closures intersect.

## Virtual-marginal characterization [paper_fact]
Fact ID: acuaviva-virtual-marginal-characterization
Source locator: Sec. 4.2, Eq. (4.4), Theorem 4.8, and Eq. (4.5)
PDF page: 22
Claim: A uniform PEPS tensor is in minimal canonical form exactly when each pair of opposite virtual marginals satisfies `rho_(k,1)=rho_(k,2)^T`.

The condition is obtained by differentiating the local tensor Frobenius norm along every Hermitian gauge direction and applying the Kempf--Ness criticality criterion.

## Fundamental theorem scope [paper_fact]
Fact ID: acuaviva-fundamental-theorem-scope
Source locator: Sec. 4.3, Theorem 4.11
PDF page: 23
Claim: Two uniform PEPS tensors have intersecting gauge-orbit closures exactly when they generate the same state on every arbitrary contraction graph.

The finite decision bound requires arbitrary direction-matched contraction graphs, not only periodic rectangular grids, and scales exponentially in the bond dimension for more than one spatial direction.

## Non-closed orbit necessity [paper_fact]
Fact ID: acuaviva-nonclosed-symmetry-necessity
Source locator: Sec. 4.5, Proposition 4.18
PDF page: 29
Claim: If a closed-orbit tensor lies in another tensor's orbit closure but not in that tensor's orbit, then the closed-orbit tensor has a nontrivial multiplicative one-parameter gauge symmetry.

The proposition is a necessary-condition statement obtained from the Hilbert--Mumford criterion; it is not stated as a converse for arbitrary tensors.

## Normal tensors have closed orbits [paper_fact]
Fact ID: acuaviva-normal-closed-orbit
Source locator: Sec. 4.5, Proposition 4.20
PDF page: 30
Claim: If a PEPS gauge-orbit closure contains a normal tensor, then the orbit is already closed and contains its minimal canonical representative without taking a non-orbit limit.

The proof blocks the normal tensor to an injective one and uses its inverse to bound both the gauge sequence and its inverses.

## Toric-code example [paper_fact]
Fact ID: acuaviva-toric-code-example
Source locator: Sec. 4.5, Example 4.21
PDF page: 31
Claim: The displayed toric-code PEPS tensor is in minimal canonical form, has maximally mixed virtual marginals, and has no nontrivial one-parameter gauge symmetry.

The example therefore does not require passage from another tensor's orbit to this representative solely through a non-orbit limit.

## Explicit closure-only example [paper_fact]
Fact ID: acuaviva-explicit-closure-example
Source locator: Sec. 4.5, Example 4.23
PDF page: 32
Claim: The paper constructs a PEPS tensor `S` whose gauge transform approaches a minimal-canonical tensor `T` as `z` tends to zero even though `S` and `T` are not in the same gauge orbit.

The rank of one displayed matrix component distinguishes the two orbits, while a continuous virtual symmetry of `T` generates the limiting path.

## First-order gauge algorithm [paper_fact]
Fact ID: acuaviva-first-order-algorithm
Source locator: Sec. 5.1, Algorithm 1 and Eqs. (5.4)--(5.6)
PDF page: 34
Claim: Algorithm 1 repeatedly applies exponential gauge updates proportional to the normalized opposite-marginal mismatch until the squared balance residual reaches the requested tolerance.

Every iterate stays inside the gauge orbit; the objective is the log of the local tensor Frobenius norm on the nonpositively curved gauge-coset geometry.

## First-order convergence guarantee [paper_fact]
Fact ID: acuaviva-first-order-convergence
Source locator: Sec. 5.1, Theorem 5.1
PDF page: 35
Claim: When the minimum-norm representative is nonzero, the first-order algorithm reaches marginal-balance error `epsilon` within `O(m epsilon^{-2} log(||T||_2/||T_min||_2))` iterations.

This guarantee concerns a gauge representative and a normalized local marginal residual, not a bond-rank reduction.

## Dimension dependence [paper_fact]
Fact ID: acuaviva-dimension-dependence
Source locator: Sec. 5.2, Definition 5.4 and paragraph below it
PDF page: 36
Claim: The constant `gamma` linking canonical approximation errors is inverse-polynomial in bond dimension for one spatial direction but exponentially small for two or more directions.

Consequently, polynomial dependence on `gamma^{-1}` can be exponential in higher-dimensional bond dimensions.

## Second-order approximation guarantee [paper_fact]
Fact ID: acuaviva-second-order-approximation
Source locator: Sec. 5.3, Theorem 5.15 and Corollary 5.16
PDF page: 42
Claim: For a non-null rational finite-bit tensor, a box-constrained Newton method returns a gauge representative within prescribed relative local Frobenius distance of a minimal canonical form in time polynomial in `gamma^{-1}` and `log(1/delta)`.

The theorem assumes the minimum-norm representative is nonzero and measures approximation in the finite-dimensional tensor space.

## Proposed PEPS bond truncation [paper_fact]
Fact ID: acuaviva-proposed-peps-truncation
Source locator: Sec. 6, item 1 under Conclusion and outlook
PDF page: 44
Claim: The paper proposes computing a minimal canonical form and then retaining the virtual-marginal eigenvectors with the `D'` largest eigenvalues as a PEPS bond-truncation scheme.

The authors explicitly present numerical evaluation and theoretical truncation properties as follow-up questions.

## PEPS truncation guarantee absent [literature_gap]
Fact ID: acuaviva-gap-truncation-guarantee
Source locator: Sec. 6, item 1 under Conclusion and outlook
PDF page: 44
Claim: This source does not prove that its proposed canonicalize-then-truncate PEPS scheme is optimal or that it obeys a global many-body state-error bound.
Gap scope: source_local

The rigorous approximation theorems concern approach to a minimum-norm gauge representative before any bond directions are removed.

## Measurement-law guarantee absent [literature_gap]
Fact ID: acuaviva-gap-measurement-law
Source locator: Full-text scope and Sec. 6 application list
PDF page: 44
Claim: This source does not derive a bound from local tensor Frobenius error or virtual-marginal balance to a multi-time measurement-outcome probability law.
Gap scope: source_local

Its exact state-equality statements apply to gauge-orbit closures on fixed finite contraction graphs, while its finite-error algorithms report tensor-space canonicalization errors.

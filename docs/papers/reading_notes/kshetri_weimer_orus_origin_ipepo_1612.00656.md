+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1612.00656"
source_version = "v4"
source_uri = "https://arxiv.org/abs/1612.00656v4"
source_artifact = "outputs/papers/pepo_survey/1612.00656.pdf"
source_sha256 = "5ed4469fceceb276cbb9a1769ec31a63a83e6e43720e60cf1eebcb8eeb66d538"
title = "A simple tensor network algorithm for two-dimensional steady states"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/KSHETRIMAYUM_1612_00656_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "b65e2e62664009ef3e712f7423c93c6b03805ee8897ce80f2cee0d10fc57aadf"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-xhigh-source-review-2026-07-17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5, 8, 9, 10, 11, 12]

[[relations]]
predicate = "defines"
object_id = "ipepo-density-operator-representation"
object_type = "method"
object_label = "iPEPO density-operator representation"
fact_id = "fact.ipepo-representation"

[[relations]]
predicate = "defines"
object_id = "simple-update-bond-truncation"
object_type = "method"
object_label = "simple-update bond truncation"
fact_id = "fact.simple-update-truncation"

[[relations]]
predicate = "supports"
object_id = "strong-dissipation-steady-state-hypothesis"
object_type = "concept"
object_label = "strong-dissipation steady-state hypothesis"
fact_id = "fact.strong-dissipation-hypothesis"

[[relations]]
predicate = "contradicts"
object_id = "monotone-bond-dimension-convergence"
object_type = "limitation"
object_label = "monotone bond-dimension convergence"
fact_id = "fact.nonmonotone-bond-results"
+++
# Full-text review — Kshetrimayum, Weimer, and Orús, “A simple tensor network algorithm for two-dimensional steady states”

## Source identity [paper_fact]
Fact ID: fact.source-identity
Source locator: Title page and arXiv version stamp, page 1
PDF page: 1
Claim: The source is the arXiv:1612.00656v4 version dated 5 September 2017 of Kshetrimayum, Weimer, and Orús's method for approximating infinite two-dimensional dissipative-lattice steady states.

The title page presents the method as a tensor-network approximation for steady states in the
thermodynamic limit. The abstract identifies dissipative Ising and spin-one-half XYZ models as its
two numerical applications and states that the method is motivated by strong dissipation limiting
the growth of quantum entanglement.

## Vectorized steady-state objective [paper_fact]
Fact ID: fact.vectorized-steady-objective
Source locator: Eqs. (1)-(2) and paragraph continuing on page 2, pages 1-2
PDF page: 1
Claim: The method vectorizes a time-independent GKSL master equation and identifies a steady state with a zero-eigenvalue vector of the vectorized Liouvillian.

Equation (1) contains a Hamiltonian commutator and Lindblad dissipators. Equation (2) gives the
matrix acting on the vectorized density operator. For time-independent `L_#`, the source writes
`|rho(T)>_#=exp(T L_#)|rho(0)>_#` and defines the long-time steady state by
`L_#|rho_s>_#=0`. The subsequent construction assumes that the Liouvillian decomposes into local
nearest-neighbor terms.

## iPEPO density-operator representation [paper_fact]
Fact ID: fact.ipepo-representation
Source locator: Figure 1 and “Computing 2D steady states,” page 2
PDF page: 2
Claim: The iPEPO density-operator representation uses a PEPO of bond dimension D for rho and, after fusing the bra and ket indices, an iPEPS-shaped vector with physical dimension d squared.

Figure 1 shows the PEPO, its vectorization, and the tensor-network contraction associated with the
trace. Supplementary Note 1 specifies a two-site unit cell with tensors `A` and `B` and four positive
diagonal bond-weight matrices. The paper states that the PEPO construction does not by itself
guarantee positivity of the reduced density matrix.

## Imaginary-time and real-time parallel [paper_fact]
Fact ID: fact.time-evolution-parallel
Source locator: Table I and surrounding text, page 2
PDF page: 2
Claim: Table I pairs imaginary-time evolution toward a Hamiltonian ground state with real-time vectorized-Liouvillian evolution toward a steady state.

The table compares a sum of local Hamiltonian terms with a sum of local Liouvillian terms,
`exp(-tau H)` with `exp(T L_#)`, and their respective fixed objectives. The paper uses this formal
parallel to apply iPEPS time-evolution machinery to the vectorized density operator; it does not
state that the two problems have identical conditioning or convergence guarantees.

## Strong-dissipation steady-state hypothesis [paper_fact]
Fact ID: fact.strong-dissipation-hypothesis
Source locator: “Computing 2D steady states” and Discussion, pages 2 and 5
PDF page: 2
Claim: The strong-dissipation steady-state hypothesis is that a sufficiently strong dissipative fixed-point attractor reaches a steady state before operator entanglement becomes too large for the chosen tensor-network representation.

The source calls this the intuition behind the method and later says the approach relies on this
hypothesis. For weak dissipation it suggests starting in the strong-dissipation regime and lowering
the strength adiabatically. It does not provide a sufficient-dissipation theorem, a gap condition, or
a certified finite bond dimension.

## Simple-update bond truncation [paper_fact]
Fact ID: fact.simple-update-truncation
Source locator: Supplementary Eq. (3) and Supplementary Figure 2, pages 8-9
PDF page: 9
Claim: The simple-update bond truncation applies a first-order Trotter two-body gate, performs an SVD on the updated local tensor, and retains the D largest singular values on the acted-on bond.

Supplementary Eq. (3) splits the vectorized propagator into products of two-body gates. Supplementary
Figure 2 shows the gate contraction, SVD, truncation, new bond spectrum, and reconstructed site
tensors. The accompanying text says the update is locally optimal in one dimension but only
approximate in two dimensions because it omits the environment of the truncated bond. It reports
good behavior for gapped phases with small correlation length rather than a general error bound.

## CTM observable contraction [paper_fact]
Fact ID: fact.ctm-observables
Source locator: Supplementary Note 3 and Supplementary Figures 3-4, pages 8-10
PDF page: 9
Claim: Local observables are computed by approximating the infinite iPEPO trace environment with four corner transfer matrices and four half-row or half-column transfer tensors.

The construction first absorbs square roots of the local bond weights, traces the external physical
indices, and approximates the remaining infinite network by CTM tensors. Directional moves are
iterated to convergence with an environment bond dimension `chi`. This contraction is used after
the simple-update evolution and does not change the environment approximation used by that bond
truncation.

## Steady-state and negativity diagnostics [paper_fact]
Fact ID: fact.diagnostic-boundary
Source locator: Paragraph defining Delta and epsilon_n, page 3
PDF page: 3
Claim: Delta and epsilon_n are numerical diagnostics, and the source explicitly warns that neither diagnostic characterizes the distance to the steady state.

The paper defines `Delta=<rho_s|L_#|rho_s>` and expects it to be zero for an exact steady state. It
defines `epsilon_n` as the sum of negative eigenvalues of an `n`-site reduced density matrix, which
would vanish for a positive reduced state. The text says both can benchmark a calculation but do not
characterize distance to the steady state. It also notes that a fully positive tensor-network
algorithm is possible at a cost in accuracy and efficiency, but does not use such a representation.

## Nonmonotone bond-dimension results [paper_fact]
Fact ID: fact.nonmonotone-bond-results
Source locator: Figure 2 and Ising-model discussion, pages 4-5
PDF page: 4
Claim: The reported Ising calculations contradict monotone bond-dimension convergence because the source observes non-monotonic behavior with D near the transition and says the effect remains to be understood.

The transition curves tend toward the correlated variational result as `D` increases, but the text
explicitly reports non-monotonic convergence in the transition region. It also reports disappearance
of the finite-`D` bistable region above `D=2` and disappearance of an antiferromagnetic region for
`D=6,...,9` in the tested window. The paper says the latter does not rule out antiferromagnetic
behavior at other parameters.

## Operator-entanglement diagnostic [paper_fact]
Fact ID: fact.operator-entanglement
Source locator: Supplementary Eqs. (4)-(9), pages 9-11
PDF page: 10
Claim: The operator-entanglement entropy is the entanglement entropy of the vectorized density operator, not the entanglement of the mixed state, and it is bounded by 4 L log base 2 of D for an L-by-L block.

Supplementary Note 4 defines the reduced operator `sigma_#` by tracing the vectorized pure state.
It describes a full CTM calculation and a simpler mean-field approximation that replaces the block
environment by surrounding bond weights. The source says this latter approximation works well in
gapped phases and is the one used in the main text.

## Model-specific benchmark scope [paper_fact]
Fact ID: fact.benchmark-scope
Source locator: Figures 2-4 and Discussion, pages 4-5
PDF page: 5
Claim: The numerical evidence is limited to the stated dissipative Ising and XYZ models and does not constitute an exact general benchmark of the iPEPO algorithm.

For the Ising model, the paper compares with product and correlated variational approximations and
reports a first-order transition near `h_x/gamma=6` in its chosen parameters. For the XYZ model it
reports no re-entrance in the chosen coupling scan. The discussion describes both as benchmarks of
the method; no closed-form exact two-dimensional steady state or general finite-`D` error bound is
provided.

## Positivity preservation [literature_gap]
Fact ID: gap.positivity-preservation
Source locator: “Computing 2D steady states,” page 2; Supplementary Note 1, page 8
PDF page: 8
Claim: The source does not establish that finite-D simple-update evolution preserves positivity of the represented density operator.
Gap scope: source_local

The source explicitly says a PEPO need not be positive and that negative eigenvalues must be kept
under control. It monitors negative eigenvalues only in finite reduced density matrices. It supplies
neither a positive parametrization for the used ansatz nor a theorem that all finite-region or global
density operators remain positive after SVD truncation.

## Finite-bond convergence certificate [literature_gap]
Fact ID: gap.finite-bond-certificate
Source locator: Ising-model results and Discussion, pages 4-5
PDF page: 5
Claim: The source does not provide a monotone convergence theorem, a generally sufficient finite D, or a certified distance from its truncated iPEPO to the exact steady state.
Gap scope: source_local

The source reports convergence behavior for selected observables and diagnostics, including a
non-monotonic dependence on `D` near a transition. Its own warning about `Delta` and `epsilon_n`
prevents those quantities from filling this gap.

## Sequential outcome-distribution accuracy [literature_gap]
Fact ID: gap.sequential-outcome-accuracy
Source locator: Complete method and results scope, pages 1-12
PDF page: 5
Claim: The source does not establish an accuracy bound for a sequential measurement-outcome distribution produced from the truncated iPEPO.
Gap scope: source_local

The method evolves a deterministic density operator toward an infinite-lattice steady state and
extracts local reduced observables. It contains no measurement instrument, outcome-conditioned
state update, reset, adaptive operation, sampled joint sequence, or comparison between exact and
truncated outcome distributions.

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2012.03095"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2012.03095v2"
source_artifact = "outputs/papers/pepo_survey/2012.03095.pdf"
source_sha256 = "d750982bd052408459beb0a6b1ce2655dcac236273bbd6e65ec660e79cedd25b"
title = "On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/KILDA_2012_03095_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "80b6e2c02deebd8166651ecb2e83d5ffe0bc09b4ca5dd0b01afbd8bf1a8f52a5"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-xhigh-source-review-2026-07-17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 3, 4, 6, 7, 8, 10, 11, 15]

[[relations]]
predicate = "defines"
object_id = "ipepo-density-operator-evolution"
object_type = "method"
object_label = "iPEPO density-operator evolution"
fact_id = "fact.ipepo-vectorization"

[[relations]]
predicate = "defines"
object_id = "bond-spectrum-stationarity-diagnostic"
object_type = "observable"
object_label = "bond-spectrum stationarity diagnostic"
fact_id = "fact.stationarity-diagnostic"

[[relations]]
predicate = "contradicts"
object_id = "monotone-bond-dimension-convergence"
object_type = "limitation"
object_label = "monotone bond-dimension convergence"
fact_id = "fact.nonmonotone-bond-stability"
+++
# Full-text review — Kilda et al., “On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices”

## Source identity [paper_fact]
Fact ID: fact.source-identity
Source locator: Title page and arXiv version stamp, page 1
PDF page: 1
Claim: The source is the 8 February 2021 arXiv v2 submission by Kilda, Biella, Schiró, Fazio, and Keeling on the stability of the iPEPO ansatz for driven-dissipative two-dimensional lattices.

The PDF title page labels the object as a SciPost Physics submission, dates the manuscript 10
February 2021, and carries the arXiv:2012.03095v2 stamp dated 8 February 2021. The abstract states
that the study tests when the earlier iPEPO approach reaches a steady state and when apparently
converged calculations become unstable as bond dimension increases.

## Dissipative XYZ model [paper_fact]
Fact ID: fact.xyz-liouvillian
Source locator: Section 2, Eqs. (1)-(2), page 3
PDF page: 3
Claim: The tested model is an infinite-square-lattice dissipative spin-one-half XYZ master equation with nearest-neighbor XYZ couplings and local lowering-operator dissipation.

Equation (1) evolves the density operator with a Hamiltonian commutator and a sum of local
amplitude-damping dissipators at rate `kappa`. Equation (2) defines the nearest-neighbor Hamiltonian
with couplings `J_x`, `J_y`, and `J_z`. The numerical study fixes `J_x=0.5` and `J_z=1` in units
where `kappa=1` while scanning `J_y` unless a dissipation sweep is explicitly stated.

## iPEPO vectorization [paper_fact]
Fact ID: fact.ipepo-vectorization
Source locator: Appendix A.2, first three paragraphs, page 15
PDF page: 15
Claim: The iPEPO density-operator evolution vectorizes a PEPO into a PEPS-shaped state and replaces imaginary-time Hamiltonian gates by real-time two-body Liouvillian gates.

The bra and ket physical indices at each lattice site are fused to form a vectorized object
`|rho>`. For every bond direction `alpha` in `{U,R,D,L}`, the iPEPS imaginary-time gate is replaced
by `exp(-delta t L_alpha)`. Observables are evaluated as `Tr[O rho]`, and the normalization condition
is `Tr[rho]=1`, so local physical indices are traced rather than paired in a wavefunction inner
product.

## Simple-update operation [paper_fact]
Fact ID: fact.simple-update-operation
Source locator: Appendix A.1.1, numbered steps 1-6, pages 10-11
PDF page: 11
Claim: The simple update applies a two-body propagator to a locally gauged tensor pair, performs an SVD on the updated bond, and retains the largest D singular values.

The operation absorbs the three external diagonal bond spectra into the two site tensors, factors the
sites into rank-three subtensors, applies the directional two-body propagator, and decomposes the
result by SVD. It truncates the updated bond to the `D` largest singular values, reconstructs the
rank-five site tensors, and divides out the external spectra to restore the Vidal-form representation.

## Local-environment truncation limitation [paper_fact]
Fact ID: fact.local-truncation-limitation
Source locator: Appendix A.1.1, final two paragraphs, page 11
PDF page: 11
Claim: The simple-update truncation is suboptimal because it omits the full unit-cell environment, and the paper states that PEPS has no known MPS-like canonical form that removes this problem.

The source contrasts the `O(D^3 d^6)` local update with full update, which constructs a full
environment at higher cost. It says simple update is generally adequate for large gaps and short
correlation lengths but that its local truncation becomes problematic near critical points with long
correlation lengths.

## Bond-spectrum stationarity diagnostic [paper_fact]
Fact ID: fact.stationarity-diagnostic
Source locator: Section 2, Eq. (3) and Figure 2, page 4
PDF page: 4
Claim: The bond-spectrum stationarity diagnostic epsilon_Lambda is the maximum consecutive-step singular-value change divided by the timestep and the current maximum singular value.

For a directional diagonal spectrum `Lambda_n`, Eq. (3) defines
`epsilon_Lambda=max|Lambda_n-Lambda_(n-1)|/(delta t max|Lambda_n|)`. Figure 2 illustrates a
decaying history at `J_y=1.5` and persistent noisy oscillations at `J_y=1.2` for timesteps
`10^-1`, `10^-2`, and `10^-3`. Appendix A.2 specifies that the numerical stop rule must hold
separately for every one of the four directional spectra.

## Protocol-robust nonconvergence [paper_fact]
Fact ID: fact.protocol-robust-nonconvergence
Source locator: Section 2.1, Figures 2-5 and summary paragraph, pages 4-6
PDF page: 6
Claim: In the tested J_y=1.2 regime, persistent spectrum oscillations survive smaller timesteps, several initial states, and adiabatic sweeps in J_y or kappa.

The timestep comparison covers `10^-1`, `10^-2`, and `10^-3`. Four explicitly plotted initial
conditions remain nonconvergent. A sweep from `J_y=1.4` stops finding a steady state between
`J_y=1.33` and `1.32`, while a dissipation sweep at `J_y=1.2` finds a steady state for
`kappa>=5.2` but again becomes oscillatory below that value in the stated units and protocols.

## Nonmonotone bond-dimension stability [paper_fact]
Fact ID: fact.nonmonotone-bond-stability
Source locator: Section 2.2, Figure 6 and accompanying text, pages 6-8
PDF page: 7
Claim: The reported simulations contradict monotone bond-dimension convergence because increasing D can destroy a previously stationary simple-update iPEPO history.

At `J_y=1.5`, the histories converge for `D=3,4` but not for `D=5,6`. At `J_y=1.2`, the
`D=12` histories converge for timesteps `10^-2` and `10^-3`, whereas `D=14,15` again show
noisy oscillations. The paper interprets this as evidence that small-`D` stationary states can be
spurious rather than as a monotone accuracy sequence.

## CTM independence of the reported instability [paper_fact]
Fact ID: fact.ctm-independence
Source locator: Section 2, paragraphs following Figure 1, page 4
PDF page: 4
Claim: The stability histories reported in the paper arise in the simple-update evolution before CTM contraction and therefore do not depend on the CTM environment dimension.

CTM is needed to extract observables from the evolved infinite network, but the paper's stability
test monitors the directional singular-value spectra during SU evolution itself. It therefore states
that the remaining stability results do not depend on CTM contraction. The same source later notes
that evaluating observables at `D=15` would require more than 128 GB for its CTM calculation.

## Unknown sufficient bond dimension [paper_fact]
Fact ID: fact.unknown-sufficient-bond
Source locator: Section 3, first conclusion paragraph, page 8
PDF page: 8
Claim: The study is unable to determine a typical bond dimension sufficient for faithfully representing a prototypical driven-dissipative lattice steady state.

The authors state a belief that a suitable `D` exists when spatial correlations decay exponentially,
but explicitly distinguish that belief from what their study concludes. They advise substantial
caution when extending two-dimensional simple-update iPEPS machinery to Liouvillian evolution and
discuss full-environment or global variational alternatives rather than certifying a finite `D`.

## Positivity preservation [literature_gap]
Fact ID: gap.positivity-preservation
Source locator: Appendix A.2, representation, propagation, and normalization description, page 15
PDF page: 15
Claim: The source does not establish that finite-D simple-update iPEPO evolution preserves Hermiticity or positive semidefiniteness of the represented density operator.
Gap scope: source_local

The appendix specifies vectorization, Liouvillian propagation, trace normalization, local observables,
and the bond-spectrum stop rule. It does not provide a positivity-preserving parametrization, a
negative-eigenvalue or negativity test, or a theorem that the SVD-truncated PEPO remains a physical
density operator.

## Outcome-distribution accuracy [literature_gap]
Fact ID: gap.outcome-distribution-accuracy
Source locator: Sections 2-3 and Appendix A, complete evaluated-output scope, pages 3-16
PDF page: 8
Claim: The source does not establish an accuracy bound for a sequential measurement-outcome distribution produced from the truncated iPEPO.
Gap scope: source_local

The evaluated quantities are singular-spectrum stationarity and local observables of an infinite-lattice
steady state. The source contains no measurement sampler, conditional outcome update, reset process,
joint sequence probability, or distance between exact and truncated outcome distributions.

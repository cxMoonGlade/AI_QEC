+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "doi:10.21468/SciPostPhysLectNotes.86"
source_version = "version-of-record"
source_uri = "https://doi.org/10.21468/SciPostPhysLectNotes.86"
source_artifact = "docs/papers/naumann_ipeps_variational_lecture_notes_2024.pdf"
source_sha256 = "9e34cadaa235c94efc03cf1b9bf795764b55a3c7a42e0168ee3949b283c66c45"
title = "An introduction to infinite projected entangled-pair state methods for variational ground state simulations using automatic differentiation"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/NAUMANN_VARIPEPS_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "f56ec8091c10ff2bac5473f7b85116a9f250c6248d7561a5f1328492803d3aac"
admission_status = "source_only_reviewed"
admission_reviewer = "peps_carrier_source_round2_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 5, 9, 10, 11, 12, 16, 19, 33]

[[relations]]
predicate = "defines"
object_id = "ctmrg-projector-truncation"
object_type = "method"
object_label = "CTMRG projector truncation"
fact_id = "naumann-ctmrg-projectors"
+++
# Full-text review — Naumann et al., “An introduction to infinite projected entangled-pair state methods for variational ground state simulations using automatic differentiation”

## Source identity [paper_fact]
Fact ID: naumann-source-identity
Source locator: Title page and publication metadata
PDF page: 1
Claim: Jan Naumann, Erik Lennart Weerda, Matteo Rizzi, Jens Eisert, and Philipp Schmoll authored this 2024 SciPost Physics Lecture Notes article on variational iPEPS with automatic differentiation.

The version of record is SciPost Physics Lecture Notes 86 and accompanies the variPEPS software library.

## Variational iPEPS target [paper_fact]
Fact ID: naumann-variational-target
Source locator: Sec. 2, Eqs. (1)--(2)
PDF page: 5
Claim: The method searches a periodically repeated iPEPS unit cell for a minimum of the local-Hamiltonian energy density by differentiating through an approximate CTMRG contraction.

The iPEPS state bond dimension and the environment refinement dimension are independent numerical controls.

## Finite-environment variational qualification [paper_fact]
Fact ID: naumann-finite-environment-qualification
Source locator: Sec. 2, final paragraph before Sec. 2.1
PDF page: 5
Claim: A strict variational upper-bound interpretation would require the CTMRG environment dimension `chi_E` to approach infinity, while practical calculations increase it until observables converge.

Finite-environment convergence is therefore an empirical numerical condition in the presented workflow.

## CTMRG projector environment [paper_fact]
Fact ID: naumann-ctmrg-projectors
Source locator: Sec. 2.2.2, Figs. 7--8 and Eqs. (4)--(6)
PDF page: 10
Claim: CTMRG projector truncation singular-value decomposes an approximate lattice-environment matrix `M=rho_B rho_T` and retains the leading `chi_E` singular subspace.

The environment matrix includes the current CTM tensors and the local iPEPS patch for the absorption direction.

## CTMRG projector pseudoinverse [paper_fact]
Fact ID: naumann-ctmrg-pseudoinverse
Source locator: Sec. 2.2.2, Eqs. (7)--(9) and Fig. 9
PDF page: 10
Claim: The top and bottom projectors use an inverse square root of the retained singular spectrum with a pseudoinverse tolerance, and without truncation their product assembles the identity on the enlarged bond.

The source gives a typical inverse-square-root threshold of `10^-6`, corresponding to `10^-12` on singular values, for numerical stability.

## Full and half projectors [paper_fact]
Fact ID: naumann-full-half-projectors
Source locator: Sec. 2.2.2, discussion after Fig. 9 and Fig. 10
PDF page: 11
Claim: Full projectors use the complete displayed lattice environment, while computationally cheaper half projectors contract a smaller environment and retain correlations from only one half of the network.

The source says half projectors are sufficient in many applications rather than proving equivalence in general.

## Element-wise fixed-point requirement [paper_fact]
Fact ID: naumann-elementwise-fixed-point
Source locator: Sec. 2.2.3, Eq. (10)
PDF page: 12
Claim: Automatic differentiation through CTMRG requires element-wise convergence of the environment tensors because convergence of corner singular values alone can hide sign or phase fluctuations from SVD gauge freedom.

The proposed phase convention fixes the largest entry of each left singular vector to the positive real axis, with an ordering rule for quasi-degeneracies.

## Fixed-point gradient [paper_fact]
Fact ID: naumann-fixed-point-gradient
Source locator: Sec. 2.5, Eqs. (16)--(17)
PDF page: 16
Claim: At a true CTMRG fixed point, the energy gradient can be evaluated from one converged iteration and a fixed-point derivative series instead of storing every preceding CTMRG iteration.

The infinite derivative series is truncated only after the resulting gradient converges to the requested numerical accuracy.

## Environment truncation heuristic [paper_fact]
Fact ID: naumann-environment-truncation-heuristic
Source locator: Sec. 2.8.2, first paragraph
PDF page: 19
Claim: The norm of discarded normalized environment singular values is used as a heuristic for deciding whether `chi_E` is too small, with `epsilon_T>10^-5` given as an example warning threshold.

The source warns that an undersized environment can let automatic differentiation exploit CTMRG inaccuracies and produce artificially low energies.

## Stochastic trajectories not treated [literature_gap]
Fact ID: naumann-gap-stochastic-trajectories
Source locator: Full-text scope; Secs. 2--5 and Appendices A--D
PDF page: 33
Claim: This source does not define stochastic pure-state trajectories, selective measurement branches, or physical outcome masses.
Gap scope: source_local

Its optimization target is a deterministic thermodynamic-limit ground-state energy.

## Multi-time record bridge not treated [literature_gap]
Fact ID: naumann-gap-record-bridge
Source locator: Full-text scope and Sec. 5 conclusion
PDF page: 33
Claim: This source does not establish a bound from a discarded environment singular spectrum or CTMRG fixed point to a joint multi-time measurement-record distribution.
Gap scope: source_local

Its reported outputs are ground-state energies, gradients, contraction environments, and many-body benchmark observables.

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2501.17913"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2501.17913v2"
source_artifact = "docs/papers/2501.17913v2.pdf"
source_sha256 = "9c2b2f2584da0270ef740c5e9ef0b5bc5d2f0fa88326bd0b8b7f04d634dcd2b5"
title = "Large-scale stochastic simulation of open quantum systems"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/SANDER_2501_17913_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "53f29861d1c1a24e8de095f654e9f56e7888442ec5f8588c1fc67ffe1156563d"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_source_rebuild_xhigh_2026_07_17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 3, 4, 5, 7, 8, 10, 11, 12, 25]

[[relations]]
predicate = "defines"
object_id = "mcwf-norm-deficit-jump-probability"
object_type = "observable"
object_label = "MCWF norm-deficit jump probability"
fact_id = "sander-mcwf-jump-probability"

[[relations]]
predicate = "defines"
object_id = "tensor-jump-method"
object_type = "method"
object_label = "tensor jump method"
fact_id = "sander-tjm-composition"

[[relations]]
predicate = "limits"
object_id = "single-site-jump-factorization"
object_type = "limitation"
object_label = "single-site jump-operator factorization"
fact_id = "sander-single-site-factorization"

[[relations]]
predicate = "supports"
object_id = "full-bond-tjm-convergence"
object_type = "theorem"
object_label = "full-bond TJM convergence theorem"
fact_id = "sander-full-bond-theorem"

[[relations]]
predicate = "defines"
object_id = "dynamic-tdvp-projection-error"
object_type = "observable"
object_label = "dynamic-TDVP projection error"
fact_id = "sander-projection-error"
+++
# Full-text review — Sander et al., “Large-scale stochastic simulation of open quantum systems”

## Source identity [paper_fact]
Fact ID: sander-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The source is Sander et al.'s arXiv:2501.17913v2 preprint “Large-scale stochastic simulation of open quantum systems,” dated 8 September 2025 on the title page and posted as v2 on 22 July 2025.

The title page lists Aaron Sander and eight coauthors. This record is pinned to the 25-page v2 arXiv
artifact and does not infer a journal publication state absent from that artifact.

## Scientific scope [paper_fact]
Fact ID: sander-selection-scope
Source locator: Abstract and Sec. I
PDF page: 1
Claim: The source introduces the tensor jump method for stochastic matrix-product-state simulation of Markovian Lindblad dynamics using MCWF, dynamic TDVP, and a sampling MPS.

The stated goal is scalable trajectory simulation with reduced time-step sensitivity. The method is
benchmarked on dissipative spin-chain observables and extended numerically to systems as large as one
thousand spins.

## Lindblad model [paper_fact]
Fact ID: sander-lindblad-model
Source locator: Sec. II.A, Eq. (1)
PDF page: 3
Claim: The modeled open-system dynamics is a Markovian Lindblad equation with Hamiltonian `H_0`, jump operators `L_m`, and nonnegative coupling factors `gamma_m`.

The source permits Hermitian or non-Hermitian jump operators in the general equation and describes them
as instantaneous relaxation, dephasing, excitation, or related noise processes.

## MCWF jump probability [paper_fact]
Fact ID: sander-mcwf-jump-probability
Source locator: Sec. II.B, Eqs. (2)–(11)
PDF page: 3
Claim: The MCWF norm-deficit jump probability is `delta p = 1 - ||Psi^(i)(t+delta t)||^2`, with channel contributions `delta p_m = delta t gamma_m <Psi|L_m^dagger L_m|Psi>` normalized only after a jump is selected.

A uniform draw chooses jump versus no jump. The no-jump candidate is normalized for continuation; on a
jump, the selected operator acts on the pre-time-evolved state in this first-order MCWF construction and
the resulting state is normalized.

## MCWF ensemble bridge [paper_fact]
Fact ID: sander-mcwf-ensemble
Source locator: Sec. II.B, Eqs. (12)–(13) and Appendix A, Eq. (A6)
PDF page: 4
Claim: The source recovers the Lindblad density operator from the ensemble average of normalized MCWF pure-state projectors in the small-time-step and large-trajectory limits.

For finitely many trajectories, Eq. (13) defines the empirical density estimator. Appendix A derives the
master-equation generator by averaging the jump and no-jump updates to first order in the time step.

## Tensor jump method composition [paper_fact]
Fact ID: sander-tjm-composition
Source locator: Sec. III.A, Eqs. (14)–(20) and Fig. 1
PDF page: 5
Claim: The tensor jump method composes dynamic TDVP, dissipative contraction, and stochastic jumping through a sampling MPS whose reordered evolution permits physical-state retrieval at requested time steps.

The sampling state `Phi` alternates the declared operators, while a final half-step construction retrieves
the trajectory state `Psi`. Density operators or linear observables are then averaged over independent
trajectories.

## Strang split [paper_fact]
Fact ID: sander-strang-split
Source locator: Sec. III.B, Eqs. (21)–(28)
PDF page: 5
Claim: The tensor jump method uses a Strang split between `H_0` and the dissipative effective-Hamiltonian term, giving a local splitting remainder of order `delta t^3` in Eq. (23).

Neighboring dissipative half steps are combined because the dissipative Hamiltonian commutes with
itself. The sampling-MPS ordering is introduced to retain this split while exposing states at intermediate
simulation times.

## Dynamic TDVP cap rule [paper_fact]
Fact ID: sander-dynamic-tdvp-cap
Source locator: Sec. III.C, Eqs. (29)–(37)
PDF page: 7
Claim: Dynamic TDVP uses two-site updates while a local bond has room to grow and switches to one-site updates when the local bond reaches `chi_max`, thereby replacing further truncation with finite-manifold projection error.

The two-site update merges adjacent tensors, evolves them, and applies an SVD before continuing the
sweep. The one-site branch keeps the trajectory inside its current fixed-bond manifold.

## Single-site dissipative factorization [paper_fact]
Fact ID: sander-single-site-factorization
Source locator: Sec. III.D, Eqs. (38)–(40)
PDF page: 7
Claim: The paper's exact dissipative contraction is a single-site jump-operator factorization whose local factors commute, do not increase MPS bond dimension, and are contracted sitewise.

The source explicitly restricts this construction to jump operators whose only nonidentity factor acts on
one site. Equation (40) then rewrites the global dissipative exponential as a tensor product of local
matrices `D_l`.

## TJM jump trigger [paper_fact]
Fact ID: sander-tjm-jump-trigger
Source locator: Sec. III.E, Eqs. (41)–(42)
PDF page: 8
Claim: The TJM jump trigger computes `delta p = 1 - ||Phi^(i)(t+delta t)||^2` from the post-TDVP, post-dissipative MPS and compares it with a uniform random draw.

Unlike the first-order MCWF derivation, the source does not approximate the exponential to obtain this
norm loss. If no jump occurs, it normalizes the dissipated MPS before continuing.

## TJM jump-channel probability [paper_fact]
Fact ID: sander-tjm-channel-probability
Source locator: Sec. III.E, Eqs. (43)–(45)
PDF page: 8
Claim: Conditional on a TJM jump, channel `m` is sampled with probability proportional to `delta t gamma_m <Phi^(i)|L_m^dagger L_m|Phi^(i)>`, evaluated by a mixed-canonical sweep over the local jump operators.

The selected local operator is contracted into its site tensor and the MPS is normalized by successive
SVDs. The source emphasizes that this post-evolution jump application differs from the earlier MCWF
algorithm.

## Full-bond convergence theorem [paper_fact]
Fact ID: sander-full-bond-theorem
Source locator: Sec. IV.B, Theorem 2 and Eqs. (52)–(56); Appendix B, Theorem 7 and Eqs. (B18)–(B22)
PDF page: 10
Claim: The full-bond TJM convergence theorem gives an unbiased fixed-time density estimator with matrix-norm standard deviation bounded by `c/sqrt(N)` when every trajectory MPS has full bond dimension.

The proof uses independent, identically distributed normalized trajectory projectors, Frobenius variance,
and equivalence of finite-dimensional matrix norms. The theorem's full-bond condition is stated in both
the main text and Appendix B.

## TJM error inventory [paper_fact]
Fact ID: sander-error-inventory
Source locator: Sec. IV.C, numbered list
PDF page: 10
Claim: The paper's TJM error inventory separates Strang-splitting time-step error, dynamic-TDVP time-step error, and dynamic-TDVP projection error.

The source states that the dissipative contraction and jump application are exact for its declared
single-site construction. The zero-error statements therefore inherit that support assumption.

## Dynamic-TDVP projection error [paper_fact]
Fact ID: sander-projection-error
Source locator: Sec. IV.C, Eqs. (57)–(58)
PDF page: 11
Claim: The dynamic-TDVP projection error is the 2-norm of the component of `H_0|Phi>` outside the chosen MPS tangent space, and the one-site projector minimizes this local residual inside that space.

The source notes that the error depends on Hamiltonian structure and bond dimensions. For nearest-neighbor
Hamiltonians, it states that two-site TDVP has zero projection error before any subsequent capped-manifold
effects.

## Finite-bond benchmark [paper_fact]
Fact ID: sander-finite-bond-benchmark
Source locator: Sec. V.B and Fig. 4(b)
PDF page: 12
Claim: In the declared ten-site TFIM benchmark, increasing trajectory count has the larger overall effect on the shown correlator error, while finite bond dimension still controls errors at particular sites and times.

The compared values are `chi` in `{2,4,8}` and trajectory counts in `{100,1000,10000}` at time step
`delta t=0.1`. The source presents this as empirical behavior for the benchmark, not as a finite-bond
convergence theorem.

## Finite-bond theorem gap [literature_gap]
Fact ID: sander-gap-finite-bond-theorem
Source locator: Theorem 2 on PDF p. 10 contrasted with Secs. III.C and IV.C on PDF pp. 6–11
PDF page: 11
Claim: The source does not extend its unbiasedness and `1/sqrt(N)` convergence theorem from full-bond trajectories to trajectories constrained by a finite `chi_max`.
Gap scope: source_local

Finite bond dimension enters the practical method through dynamic one-site projection and is evaluated in
benchmarks. The source defines its projection error but supplies no theorem converting that residual into
the density-estimator or trajectory-law guarantees of Theorem 2.

## Connected jump-support gap [literature_gap]
Fact ID: sander-gap-connected-jump-support
Source locator: Sec. III.D, explicit support assumption before Eqs. (38)–(40), and Appendix C
PDF page: 25
Claim: This source does not establish the exact dissipative factorization or jump-application cost for connected multi-site jump operators.
Gap scope: source_local

Both the factorization derivation and the complexity count specify single-site jump operators. The general
Lindblad equation permits broader operators, but the TJM implementation developed here does not derive
its sitewise contraction for those broader supports.

## Measurement-record law gap [literature_gap]
Fact ID: sander-gap-measurement-record-law
Source locator: Full-text scope established by the abstract, Secs. III–VII, and appendices
PDF page: 25
Claim: This source does not define a repeated binary measurement-record distribution or connect finite-bond TJM errors to such a distribution or to a logical-error statistic.
Gap scope: source_local

The reported outputs are density estimates and physical expectation values at selected times. The paper
does not define a measurement schedule, temporal event folding, logical-observable bits, or a distributional
distance for complete multi-round records.

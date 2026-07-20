+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2607.01323"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2607.01323v1"
source_artifact = "docs/papers/froehlich_tensor_jump_method_2607.01323.pdf"
source_sha256 = "cf1c6c23a33ac7c73b43c5891cee3a5c77c3ba3d36e8e818afe8f9647d65c13a"
title = "Noisy quantum circuit simulation with the tensor jump method"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/FROEHLICH_2607_01323_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "a8475b89816248bf96296927ff68885280c7e1e49a699fbf79b269ca7418e83b"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_record_round2_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [3, 4, 5, 7, 9, 13, 14]
+++
# Source review — Fröhlich et al.

## Tensor-jump norm loss [paper_fact]

Fact ID: fact.tjm-norm-loss
Source locator: Sec. II.B, Eqs. (2)--(7)
PDF page: 3
Claim: One tensor-jump step obtains the total jump probability from the squared-norm loss of an unnormalized non-Hermitian update.

The no-jump state is normalized after the branch decision, while a jump channel is selected from its contribution to the total hazard and the jumped state is then normalized.

## Pauli-unitary hazard simplification [paper_fact]

Fact ID: fact.pauli-unitary-hazard
Source locator: Sec. II.C, Eqs. (8)--(13)
PDF page: 4
Claim: Sparse Pauli-Lindblad jumps have state-independent channel weights because each Pauli string satisfies `P_m^dagger P_m = I`.

For this jump family the dissipative contraction is a global scalar, and the normalized jump-channel distribution can be precomputed from the rates.

## Gate-local circuit window [paper_fact]

Fact ID: fact.gate-local-window
Source locator: Sec. III and Algorithm 1
PDF page: 5
Claim: The circuit tensor-jump algorithm applies a local variational gate update followed by dissipation and jump sampling restricted to jump operators whose support intersects the gate support.

The displayed algorithm permits at most one jump per two-qubit gate and states that a multi-jump generalization is outside the article's scope.

## Circuit tensor-jump error classes [paper_fact]

Fact ID: fact.ctjm-error-classes
Source locator: Sec. III.B, Eqs. (15)--(16)
PDF page: 5
Claim: The article separates Monte Carlo sampling error from splitting, time-integration, finite-manifold projection, and singular-value truncation errors.

It identifies the finite-manifold projection residual as the component whose accumulated impact is not generally estimable outside special cases.

## Projector generator equivalence [paper_fact]

Fact ID: fact.projector-generator-equivalence
Source locator: Sec. IV.B, Eqs. (23)--(35) and Theorem 1
PDF page: 7
Claim: The two projector collapse operators proportional to `I + P` and `I - P` reproduce the same Pauli-Lindblad generator as the corresponding unitary Pauli jump.

Under the theorem's no-Hamiltonian anticommuting-window assumptions, the selected observable has a Bernoulli single-trajectory law with a closed-form variance.

## Long-range bond-two operator [paper_fact]

Fact ID: fact.long-range-bond-two
Source locator: Sec. IV.C, long-range noise MPO construction
PDF page: 9
Claim: A two-endpoint Pauli-string collapse operator of the form `a I + b P` has an exact matrix-product-operator representation of bond dimension two independent of endpoint separation.

The construction applies to the projector and analog Pauli unravelings considered in the article.

## Generic accumulated projection effect [literature_gap]

Fact ID: gap.accumulated-projection-effect
Source locator: Sec. III.B, paragraph after Eq. (16)
PDF page: 5
Claim: The article does not supply a general estimator for the accumulated observable impact of finite-manifold projection error.
Gap scope: source_local

The text identifies strictly nearest-neighbor two-site variational evolution as a special zero-residual case and leaves the general accumulated effect unresolved.

## Sequential outcome-law accuracy [literature_gap]

Fact ID: gap.sequential-outcome-law
Source locator: Sec. V, Figs. 1--3 and benchmark discussion
PDF page: 14
Claim: The numerical studies do not establish an error bound for a joint sequence of adaptive measurement outcomes under finite bond dimension.
Gap scope: source_local

The benchmarks compare selected expectation values, trajectory variances, and average bond dimensions under a fixed hard bond cap.

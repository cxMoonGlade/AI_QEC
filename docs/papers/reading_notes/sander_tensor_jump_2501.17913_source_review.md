+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2501.17913"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2501.17913v2"
source_artifact = "docs/papers/2501.17913v2.pdf"
source_sha256 = "9c2b2f2584da0270ef740c5e9ef0b5bc5d2f0fa88326bd0b8b7f04d634dcd2b5"
title = "Large-scale stochastic simulation of open quantum systems"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/TENSOR_NETWORK_CARRIER_LITERATURE_AUDIT_2026-07-16.md"
audit_packet_sha256 = "450fbb9ce7e296661ed111b5bcc7f3acdb249716f44d8301017823e566b2f48c"
admission_status = "source_only_reviewed"
admission_reviewer = "tn_carrier_source_round1_dual_review"
admission_date = "2026-07-16"
visually_checked_pages = [3, 8, 10, 11]
+++
# Source review — Sander et al.

## Monte Carlo wave-function branches [paper_fact]

Fact ID: fact.mcwf-branches
Source locator: Sec. II, Eqs. (6)--(11)
PDF page: 3
Claim: The Monte Carlo wave-function construction represents Lindblad evolution by stochastic pure-state branches consisting of non-Hermitian evolution and quantum jumps.

The density operator is recovered as an ensemble average of the pure-state projectors.

## Norm-based jump sampling [paper_fact]

Fact ID: fact.norm-jump-sampling
Source locator: Sec. III.D, Eqs. (42)--(45)
PDF page: 8
Claim: The tensor jump method uses the post-contraction squared norm to obtain the total jump probability and samples a local jump channel from normalized channel weights.

The jump state is normalized after the selected jump operator has been applied.

## Full-bond convergence assumption [paper_fact]

Fact ID: fact.full-bond-theorem
Source locator: Sec. IV.B, Theorem 2
PDF page: 10
Claim: The displayed convergence theorem for the stochastic density estimate assumes that the propagated matrix-product state has full bond dimension.

The theorem concerns convergence of the fixed-time density estimate as time step and trajectory sampling are refined.

## Finite-bond projection error [paper_fact]

Fact ID: fact.finite-bond-projection
Source locator: Sec. IV.C, Eqs. (57)--(58)
PDF page: 11
Claim: Restricting the matrix-product-state bond dimension introduces a projection error in addition to the splitting, time-discretization, and sampling errors.

The article defines this error through the difference between the propagated state and its projection onto the chosen matrix-product-state manifold.

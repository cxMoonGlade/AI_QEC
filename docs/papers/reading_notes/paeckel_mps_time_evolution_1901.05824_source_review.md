+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1901.05824"
source_version = "v3"
source_uri = "https://arxiv.org/abs/1901.05824v3"
source_artifact = "docs/papers/1901.05824v3.pdf"
source_sha256 = "1ce466ed9ec3091ee1a8548cf42a84551584cd5d6f13b0d32a418fcdc981fbb9"
title = "Time-evolution methods for matrix-product states"
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
visually_checked_pages = [8, 9, 18, 19, 49, 50]
+++
# Source review — Paeckel et al.

## Canonical matrix-product-state cut [paper_fact]

Fact ID: fact.canonical-cut
Source locator: Secs. 2.4--2.6, Eqs. (13)--(16)
PDF page: 8
Claim: A matrix-product state in mixed canonical form exposes a bond matrix whose singular values give the Schmidt coefficients for that chain cut.

The tensors to either side define orthonormal bases for the corresponding bipartition.

## Direct singular-value truncation error [paper_fact]

Fact ID: fact.direct-svd-error
Source locator: Sec. 2.6.1, Eqs. (17)--(18)
PDF page: 9
Claim: Direct rank truncation at a canonical matrix-product-state cut has Hilbert-space error equal to the square root of the sum of squared discarded singular values.

The same section notes that locally optimal sequential cut truncations need not provide the globally optimal compressed matrix-product state.

## TEBD error separation [paper_fact]

Fact ID: fact.tebd-errors
Source locator: Sec. 4.1.1, discussion after the TEBD update algorithm
PDF page: 19
Claim: Time-evolving block decimation has a time-step approximation error and a separate truncation error controlled by the retained bond dimension or discarded weight.

Convergence therefore requires independent refinement of the time step and truncation control.

## TDVP error separation [paper_fact]

Fact ID: fact.tdvp-errors
Source locator: Sec. 6.2.2, error discussion
PDF page: 50
Claim: Time-dependent variational-principle evolution can contain projection, time-step, local-solver, and singular-value-decomposition errors whose relative importance depends on the chosen variant.

Increasing the number of integration steps can increase the number of projection or truncation operations even while reducing the integrator time step.

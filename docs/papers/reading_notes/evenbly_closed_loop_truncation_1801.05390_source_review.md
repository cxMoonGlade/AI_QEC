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
audit_packet = "docs/simulator_validation/TENSOR_NETWORK_CARRIER_LITERATURE_AUDIT_2026-07-16.md"
audit_packet_sha256 = "450fbb9ce7e296661ed111b5bcc7f3acdb249716f44d8301017823e566b2f48c"
admission_status = "source_only_reviewed"
admission_reviewer = "tn_carrier_source_round1_dual_review"
admission_date = "2026-07-16"
visually_checked_pages = [2, 3, 5, 6, 11]
+++
# Source review — Evenbly

## Bond environment [paper_fact]

Fact ID: fact.bond-environment
Source locator: Sec. II, Eq. (1) and Fig. 1
PDF page: 2
Claim: The bond environment is obtained by contracting the norm network while leaving the selected internal bond and its conjugate open.

For a bridge bond this environment factorizes, while a bond inside a closed loop is generally nonseparable.

## Cyclic weighted-trace-gauge spectrum [paper_fact]

Fact ID: fact.cyclic-wtg-spectrum
Source locator: Sec. IV, Eqs. (9)--(11) and Fig. 4
PDF page: 5
Claim: Two cyclic tensor networks can represent the same physical state while having different weighted-trace-gauge coefficients because closed loops can carry representation-internal correlations.

The cycle entropy vanishes precisely when the selected index can be realized as a bridge after an appropriate unitary cycle reduction.

## Full-environment truncation objective [paper_fact]

Fact ID: fact.fet-objective
Source locator: Sec. V, Eq. (12) and Fig. 5
PDF page: 6
Claim: Full-environment truncation replaces a selected bond by lower-rank factors chosen to maximize the normalized overlap between the original and truncated whole-network pure states.

The optimization depends on the complete bond environment rather than only on the local bond matrix.

## Alternating FET solve [paper_fact]

Fact ID: fact.fet-alternating-solve
Source locator: Appendix C, Eq. (C1) and Fig. 11
PDF page: 11
Claim: The full-environment truncation algorithm alternates two generalized-eigenvalue subproblems and iterates them until the tensors converge sufficiently.

The reported numerical examples converged in fewer than twenty iterations, but the appendix does not state a general global-convergence theorem.

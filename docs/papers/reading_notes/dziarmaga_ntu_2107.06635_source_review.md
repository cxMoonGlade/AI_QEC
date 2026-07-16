+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2107.06635"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2107.06635v1"
source_artifact = "docs/papers/2107.06635v1.pdf"
source_sha256 = "219ef54a195b5d43903fe3c6546f4f2195868c6291ff95b5b6c4b428ab0d906f"
title = "Time evolution of an infinite projected entangled pair state: Neighborhood tensor update"
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
visually_checked_pages = [3, 5, 9]
+++
# Source review — Dziarmaga

## Neighborhood tensor update environment [paper_fact]

Fact ID: fact.ntu-environment
Source locator: Sec. II, Figs. 3--4
PDF page: 3
Claim: Neighborhood tensor update chooses the truncation of an evolved infinite projected entangled-pair-state bond using a finite nearest-neighbor cluster surrounding the updated tensors.

The chosen cluster is larger than the environments used by the singular-value and simple updates and smaller than the infinite environment used by full-update variants.

## Exact cluster metric [paper_fact]

Fact ID: fact.ntu-cluster-metric
Source locator: Sec. II, Eqs. (2)--(5)
PDF page: 5
Claim: The neighborhood tensor update minimizes a quadratic error whose finite-cluster metric can be contracted exactly and is Hermitian nonnegative to machine precision.

Alternating pseudo-inverse updates minimize the quadratic form for the two reduced tensors.

## Environment hierarchy [paper_fact]

Fact ID: fact.update-environment-hierarchy
Source locator: Sec. VI, conclusion
PDF page: 9
Claim: The article orders SVDU, SU, NTU, and FTU or FU by increasing tensor-environment size and reports a tradeoff between computational cost, stability, and convergence with state bond dimension.

The numerical comparisons show that a larger update environment can improve convergence while requiring more work per update.

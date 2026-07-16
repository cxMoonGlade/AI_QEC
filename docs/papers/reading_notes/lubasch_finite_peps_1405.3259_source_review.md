+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1405.3259"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1405.3259v2"
source_artifact = "docs/papers/1405.3259v2.pdf"
source_sha256 = "5d7e010293770b0c97ac9c0b88075710ceda3a68988da7933dd2130621d8269a"
title = "Unifying projected entangled pair state contractions"
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
visually_checked_pages = [2, 3, 5, 7, 9]
+++
# Source review — Lubasch, Cirac, and Bañuls

## Finite open-boundary PEPS [paper_fact]

Fact ID: fact.finite-open-peps
Source locator: Sec. II, Fig. 1 and Eq. (1)
PDF page: 2
Claim: The article studies a finite square-lattice projected entangled-pair state with open boundaries, one physical index per site, and virtual bond dimension D.

Its alternating update minimizes the Hilbert-space norm distance between a target evolved state and a candidate projected entangled-pair state.

## Boundary-MPO environment approximation [paper_fact]

Fact ID: fact.boundary-mpo-environment
Source locator: Sec. III.A, Fig. 2
PDF page: 3
Claim: Row-by-row projected entangled-pair-state contraction replaces the growing boundary by a boundary matrix-product operator with an independently chosen bond dimension.

The environment approximation accuracy is controlled by this boundary bond dimension as well as by the selected cluster size.

## Exact-environment positivity [paper_fact]

Fact ID: fact.exact-environment-positivity
Source locator: Sec. III.A.2, positivity discussion
PDF page: 5
Claim: The exact norm environment is Hermitian positive semidefinite, whereas a general approximate contraction need not preserve positivity.

The article discusses Hermitian positive approximations as a numerical stabilization of the update equations.

## PEPS canonical-form limitation [paper_fact]

Fact ID: fact.peps-canonical-limitation
Source locator: Sec. III.B.2, gauge-fixing discussion
PDF page: 7
Claim: An open-boundary matrix-product state can be locally gauged so that its norm matrix is the identity, while a projected entangled-pair state generally has no gauge transformation that guarantees the same condition.

Gauge fixing can improve conditioning without producing the one-dimensional canonical form.

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1804.09796"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1804.09796v2"
source_artifact = "docs/papers/1804.09796v2.pdf"
source_sha256 = "62e6b0ceb9fbce3da5f938968a728873b50953d87e1506f43e1358828714919f"
title = "One-dimensional many-body entangled open quantum systems with tensor network methods"
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
visually_checked_pages = [3, 10, 11, 12]
+++
# Source review — Jaschke, Montangero, and Carr

## Open-system tensor-network representations [paper_fact]

Fact ID: fact.open-system-representations
Source locator: Sec. II, Eqs. (1)--(6)
PDF page: 3
Claim: The article distinguishes quantum trajectories represented by stochastic pure states, matrix-product density operators represented in Liouville space, and locally purified tensor networks represented by a purification.

The three approaches target the same Lindblad master equation through different tensor-network objects and have different local and bond dimensions.

## Effective non-Hermitian evolution [paper_fact]

Fact ID: fact.effective-hamiltonian
Source locator: Sec. III.B, Eqs. (24)--(25)
PDF page: 10
Claim: A quantum trajectory evolves under an effective non-Hermitian Hamiltonian between jumps, and loss of squared norm is used to determine whether a jump occurs.

The non-Hermitian component contains one half of the sum of the jump-rate operators.

## Jump-channel probability [paper_fact]

Fact ID: fact.jump-channel-probability
Source locator: Sec. III.B, paragraph after Eq. (25)
PDF page: 11
Claim: When a jump occurs, jump channel nu is selected with weight given by the expectation value of the corresponding jump-rate operator in the pre-jump state.

The selected jump operator is applied before the state is normalized for continued propagation.

## Trajectory ensemble observables [paper_fact]

Fact ID: fact.trajectory-observables
Source locator: Sec. III.B, Eqs. (26)--(27)
PDF page: 12
Claim: Linear observables of the density operator are obtained by averaging their pure-state values over trajectories, while nonlinear quantities need not equal the corresponding pure-trajectory average.

The article gives purity as an example of a nonlinear quantity requiring additional care.

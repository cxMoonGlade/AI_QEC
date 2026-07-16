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
audit_packet = "docs/simulator_validation/TENSOR_NETWORK_CARRIER_LITERATURE_AUDIT_2026-07-16.md"
audit_packet_sha256 = "450fbb9ce7e296661ed111b5bcc7f3acdb249716f44d8301017823e566b2f48c"
admission_status = "source_only_reviewed"
admission_reviewer = "tn_carrier_source_round1_dual_review"
admission_date = "2026-07-16"
visually_checked_pages = [3, 5, 6, 10, 11, 19, 33]
+++
# Source review — Naumann et al.

## Variational iPEPS target [paper_fact]

Fact ID: fact.variational-ipeps-target
Source locator: Sec. 2, Eqs. (1)--(3)
PDF page: 5
Claim: The variational infinite projected entangled-pair-state method searches for a periodically repeated unit-cell state that minimizes the energy density of a local Hamiltonian in the thermodynamic limit.

Automatic differentiation supplies gradients with respect to the unit-cell tensor coefficients.

## CTMRG environment projectors [paper_fact]

Fact ID: fact.ctmrg-projectors
Source locator: Sec. 2.2.2, Eqs. (4)--(9)
PDF page: 10
Claim: Corner-transfer-matrix renormalization constructs projectors by singular-value decomposing an approximate lattice-environment matrix and retaining a chosen environment bond dimension.

The retained dimension controls the approximation of the infinite-lattice environment rather than the state tensor bond itself.

## CTMRG fixed-point requirement [paper_fact]

Fact ID: fact.ctmrg-fixed-point
Source locator: Sec. 2.2.3, convergence discussion
PDF page: 11
Claim: Stable differentiation through corner-transfer-matrix renormalization requires a genuine fixed point and consistent singular-vector phase or gauge handling, not only convergence of a corner singular spectrum.

The chapter recommends checking tensors element by element when assessing the fixed point.

## Environment truncation heuristic [paper_fact]

Fact ID: fact.environment-truncation-heuristic
Source locator: Sec. 2.8.2, stability discussion
PDF page: 19
Claim: The norm of discarded normalized environment singular values is used as a heuristic for choosing the environment bond dimension, and an undersized environment can yield artificially low variational energies.

The chapter gives an example threshold for this ground-state optimization workflow and warns that automatic differentiation can exploit contraction inaccuracies.

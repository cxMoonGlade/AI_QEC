+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "doi:10.21468/SciPostPhysCodeb.52"
source_version = "version-of-record"
source_uri = "https://doi.org/10.21468/SciPostPhysCodeb.52"
source_artifact = "docs/papers/rams_yastn_scipost_codebases_52.pdf"
source_sha256 = "44a7a77c86ec8f1f1298c12a6984717a6e5ed17ce66da2f9fa071270813a6c73"
title = "YASTN: Yet another symmetric tensor networks; A Python library for Abelian symmetric tensor network calculations"
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
visually_checked_pages = [2, 4, 8, 9, 14]
+++
# Source review — Rams et al.

## Layered YASTN architecture [paper_fact]

Fact ID: fact.yastn-architecture
Source locator: Sec. 2, Fig. 2
PDF page: 4
Claim: YASTN separates dense numerical backends and Abelian-symmetry structure from a symmetric-tensor layer and higher-level matrix-product-state and projected-entangled-pair-state algorithms.

The architecture permits multiple execution backends while retaining the same block-sparse tensor abstraction.

## Finite MPS algorithms [paper_fact]

Fact ID: fact.yastn-mps-scope
Source locator: Sec. 2.3, first paragraph
PDF page: 8
Claim: The YASTN matrix-product-state module implements finite-size algorithms including ground-state DMRG, time evolution by TDVP, and overlap maximization against matrix-product-state or matrix-product-operator targets.

The same module also supplies boundary matrix-product-state contractions for selected projected-entangled-pair-state methods.

## Finite and infinite fPEPS algorithms [paper_fact]

Fact ID: fact.yastn-fpeps-scope
Source locator: Sec. 2.3, second paragraph
PDF page: 8
Claim: The YASTN fPEPS module covers finite square-lattice states and periodic unit-cell states in the thermodynamic limit with neighborhood, cluster, and full-update time-evolution methods.

The article lists imaginary-time purification, thermal-state sampling, and real-time pure-state quenches among its applications.

## CTM environment approximation [paper_fact]

Fact ID: fact.yastn-ctm-environment
Source locator: Sec. 3, Fig. 3 and accompanying text
PDF page: 9
Claim: The corner-transfer-matrix algorithm approximates an infinite projected entangled-pair-state environment by corner and transfer tensors with an independently selected environment bond dimension.

Singular-value decompositions provide low-rank projectors during the environment iteration.

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
audit_packet = "docs/simulator_validation/RAMS_YASTN_CODEBASE_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "a9735d9fa6e6f9a21dd503e2c53679890147f413e24239938d6457634969e10d"
admission_status = "source_only_reviewed"
admission_reviewer = "peps_carrier_source_round2_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 4, 5, 6, 8, 9, 13, 14]

[[relations]]
predicate = "defines"
object_id = "yastn-layered-architecture"
object_type = "method"
object_label = "YASTN layered architecture"
fact_id = "rams-yastn-architecture"
+++
# Full-text review — Rams et al., “YASTN: Yet another symmetric tensor networks; A Python library for Abelian symmetric tensor network calculations”

## Source identity [paper_fact]
Fact ID: rams-source-identity
Source locator: Title page and publication bundle metadata
PDF page: 1
Claim: Marek M. Rams, Gabriela Wójtowicz, Aritra Sinha, and Juraj Hasik authored this 2025 SciPost Physics Codebases article describing YASTN and its bundled codebase release 1.2.

The article is SciPost Physics Codebases 52 and identifies the package and release as a citation bundle.

## YASTN layered architecture [paper_fact]
Fact ID: rams-yastn-architecture
Source locator: Sec. 2 and Fig. 2
PDF page: 4
Claim: The YASTN layered architecture separates Abelian symmetry structure from dense numerical backends in `yastn.Tensor` and builds higher-level MPS and fPEPS modules above that symmetric-tensor layer.

Backends supply storage and dense operations, while the symmetry layer determines permitted blocks and their tensor-algebra transformations.

## Abelian charge selection [paper_fact]
Fact ID: rams-abelian-charge-selection
Source locator: Sec. 2.1, Eqs. (6) and (10)
PDF page: 5
Claim: Nonzero tensor elements and blocks obey a signed Abelian charge-conservation rule fixed by the leg charge sectors and the total tensor charge.

Ordering bases by charge yields the block-sparse representation used by the library.

## Lazy block storage [paper_fact]
Fact ID: rams-lazy-block-storage
Source locator: Sec. 2.1, final paragraph
PDF page: 6
Claim: YASTN allocates storage only for allowed blocks that have been assigned nonzero data and serializes those blocks in a one-dimensional array owned by the dense backend.

Allowed but unassigned blocks are not stored.

## Finite-MPS algorithm scope [paper_fact]
Fact ID: rams-mps-algorithm-scope
Source locator: Sec. 2.3, first paragraph
PDF page: 8
Claim: The YASTN MPS module supports finite-size DMRG, TDVP time evolution, and overlap maximization against MPS, sums of MPS, or MPO-MPS targets.

The same module also supplies boundary-MPS contractions for selected finite-PEPS calculations.

## Finite and infinite fPEPS scope [paper_fact]
Fact ID: rams-fpeps-algorithm-scope
Source locator: Sec. 2.3, second paragraph
PDF page: 8
Claim: The fPEPS module supports finite square-lattice states and periodic infinite states with neighborhood, larger-cluster, and full-update time-evolution schemes.

The listed uses include imaginary-time purification, thermal-state sampling, and real-time pure-state quenches.

## CTM environment approximation [paper_fact]
Fact ID: rams-ctm-environment
Source locator: Sec. 3 and Fig. 3
PDF page: 9
Claim: The CTM calculation approximates an infinite iPEPS environment by finite corner and transfer tensors and uses an SVD of enlarged corners to construct environment projectors controlled by bond dimension `chi`.

The source distinguishes these environment objects from the iPEPS state bond dimension `D`.

## Thermal Hubbard purification example [paper_fact]
Fact ID: rams-thermal-hubbard-example
Source locator: Sec. 3.3, Eq. (17) and first two paragraphs
PDF page: 13
Claim: The finite-temperature Hubbard example evolves an infinite-temperature physical-ancilla purification to inverse temperature `beta=2` with NTU before evaluating observables by CTM.

The implementation uses fermionic swap signs and compares `Z2`, `U(1)`, and `U(1)×U(1)` symmetry structures.

## Symmetry benchmark scale [paper_fact]
Fact ID: rams-symmetry-benchmark
Source locator: Sec. 3.3, Fig. 6 and accompanying discussion
PDF page: 14
Claim: In the reported thermal Hubbard CTM benchmark, `U(1)×U(1)` block sparsity reduced memory relative to an equivalent nonsymmetric tensor and enabled calculations through state bond dimension `D=36`.

The source reports a roughly thirty-fold memory gain for the displayed setup and notes that fusion of more than ten thousand blocks can itself become a bottleneck.

## Project-specific execution semantics not treated [literature_gap]
Fact ID: rams-gap-project-execution-semantics
Source locator: Full-text scope; Secs. 2--4
PDF page: 14
Claim: This source does not establish the exact behavior of a separately implemented MPS or PEPS adapter merely because the library lists a method with the same name.
Gap scope: source_local

The article documents YASTN's architecture, capabilities, and benchmarks.

## Multi-time record law not treated [literature_gap]
Fact ID: rams-gap-record-law
Source locator: Full-text scope and Sec. 4 conclusion
PDF page: 14
Claim: This source does not define a temporal detector/observable record or a bound from its tensor-network approximations to a joint measurement-record distribution.
Gap scope: source_local

No branch-mass reconciliation, detector folding, logical-observable distribution, or record-distance metric appears in the article.

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1906.04085"
source_version = "v1"
source_uri = "https://arxiv.org/abs/1906.04085v1"
source_artifact = "outputs/papers/pepo_survey/1906.04085.pdf"
source_sha256 = "baa3c51fb6452c2a750b20ca9cada92f47cf3f24f700071de0faece318227567"
title = "Loop update for infinite projected entangled-pair states in two spatial dimensions"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/ZHENG_YANG_1906_04085_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "0e791408184a43db69a0082001b07b66073b445573484a7989b7fb5ebf1cd89e"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_peps_record_round3_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5]
+++
# Source review — Zheng and Yang

## Alternating plaquette loops [paper_fact]

Fact ID: fact.alternating-plaquette-loops
Source locator: Sec. II, Eq. (1) and Fig. 1
PDF page: 2
Claim: The loop-update ansatz is a periodically repeated two-by-two iPEPS unit cell partitioned into two interleaved four-site plaquettes whose tensors appear in different cyclic orders.

The Hamiltonian is decomposed into the two plaquette families, and the algorithm alternates their imaginary-time updates.

## Plaquette MPO update [paper_fact]

Fact ID: fact.plaquette-mpo-update
Source locator: Sec. II, Eqs. (2)--(3) and Fig. 2(a)--(c)
PDF page: 2
Claim: Applying the four-site plaquette MPO enlarges each loop bond from `D` to `D chi_mpo`, while the external simple-update weights enter the evolved site tensors as squared diagonal factors.

The resulting four-site cyclic tensor cluster is interpreted as a periodic-boundary matrix product state with combined local legs.

## Loop truncation alternatives [paper_fact]

Fact ID: fact.loop-truncation-alternatives
Source locator: Sec. II, four-option truncation paragraph
PDF page: 2
Claim: The article compares variational MPS truncation, successive-SVD quasi-canonicalization, non-unitary MPS canonicalization, and Full Environment Truncation for reducing the enlarged plaquette loop.

The implemented sequence uses the lower-cost canonicalization as a pre-optimization and then applies FET as the rank-reducing truncation.

## Cyclic normalized-fidelity optimization [paper_fact]

Fact ID: fact.cyclic-normalized-fidelity
Source locator: Sec. II and Fig. 2(c)--(f)
PDF page: 3
Claim: For each loop bond, two isometries and a retained diagonal bond matrix are initialized by SVD and variationally updated to maximize the normalized overlap between the enlarged and truncated loop states.

The isometries reduce the bond dimension back to `D`, after which the tensor order is switched and the same operation is performed on the other plaquette family.

## Full-loop environment [paper_fact]

Fact ID: fact.full-loop-environment
Source locator: Sec. II, paragraph after Fig. 2
PDF page: 3
Claim: The full-loop-update variant replaces the local diagonal-weight environment by a boundary-MPS or corner-transfer-matrix environment for the plaquette.

The stated leading environment cost is `O(D^6 chi^3)` with the double-layer environment dimension `chi` greater than `D^2`.

## Heisenberg benchmark [paper_fact]

Fact ID: fact.heisenberg-loop-benchmark
Source locator: Sec. III, Eq. (4) and Fig. 3
PDF page: 3
Claim: For the square-lattice antiferromagnetic Heisenberg model at bond dimension six, the reported loop-update energy is closer to the cited quantum-Monte-Carlo energy than the simple-update energy.

The displayed cycle entropy is also lower under loop update than simple update at the compared bond dimensions.

## Transverse-Ising benchmark [paper_fact]

Fact ID: fact.transverse-ising-loop-benchmark
Source locator: Sec. III, Eq. (5) and Fig. 4
PDF page: 4
Claim: For the square-lattice transverse-field Ising model, loop update partially improves magnetization near criticality relative to simple update, and the full-loop variants estimate critical fields and exponents close to the cited quantum-Monte-Carlo values.

The paper reports similar full-loop results with boundary-MPS and CTM environments at the tested small state bonds.

## Demonstrated evolution scope [paper_fact]

Fact ID: fact.demonstrated-evolution-scope
Source locator: Sec. IV, Summary
PDF page: 4
Claim: The demonstrated loop and full-loop algorithms optimize pure-state iPEPS ground states through imaginary-time evolution on a square lattice.

Real-time evolution, three-dimensional tensor renormalization, and finite-temperature calculations are listed as future generalizations.

## Full-environment accuracy [literature_gap]

Fact ID: gap.full-environment-accuracy
Source locator: Sec. II, paragraph after Fig. 2
PDF page: 3
Claim: The article does not provide a rigorous bound for the error introduced by the finite boundary-MPS or CTM environment used in full loop update.
Gap scope: source_local

The environment methods and their bond dimension are described as approximate numerical contractions.

## Sequential outcome law [literature_gap]

Fact ID: gap.sequential-outcome-law
Source locator: Sec. III--IV and Figs. 3--4
PDF page: 4
Claim: The benchmarks do not establish an accuracy bound for branch probabilities or a joint sequence of conditional measurement outcomes.
Gap scope: source_local

They compare ground-state energies, magnetization, critical parameters, and cycle entropy under deterministic imaginary-time optimization.

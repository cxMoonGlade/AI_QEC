+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2602.15942"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2602.15942v2"
source_artifact = "docs/papers/2602.15942v2.pdf"
source_sha256 = "ec572bd96d4a937667c2c6fb9c1996da92ff359072050c2fe47b501ed80aa83e"
title = "Limits of Clifford Disentangling in Tensor Network States"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/MASOT_2602_15942V2_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "49cc95ccf98d83dd16bb342cca20c28861a7783753162fbc62e942033ad51986"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_masot_2602_source_review_2026_07_27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 5, 6, 7, 9, 13, 14, 15, 17]
+++
# Full-text review — Masot-Llima et al., “Limits of Clifford Disentangling in Tensor Network States”

## Source identity [paper_fact]
Fact ID: masot-source-identity
Source locator: Title page and arXiv footer
PDF page: 1
Claim: The artifact is the 17-page arXiv:2602.15942v2 preprint by Masot-Llima, Sierant, Stornati, and Garcia-Saez.

## Source date anomaly [paper_fact]
Fact ID: masot-source-date-anomaly
Source locator: Title page date and arXiv footer
PDF page: 1
Claim: The title page is dated 24 February 2026 while the visible arXiv v2 footer is dated 22 February 2026.

## Selection scope [paper_fact]
Fact ID: masot-selection-scope
Source locator: Abstract and Sec. I, final paragraph
PDF page: 1
Claim: The source studies exact and heuristic Clifford disentangling in one-dimensional Clifford tensor-network simulations and the effect of accumulating non-Clifford rotations.

## CTN definition [paper_fact]
Fact ID: masot-ctn-definition
Source locator: Sec. II.A, Definition 1 and Eq. (1)
PDF page: 2
Claim: The source defines a Clifford tensor network by jointly updating a Clifford transformation \(C\) and tensor network \(T\), with \(\lvert\psi\rangle=C\lvert\psi_T\rangle\).

## Cooling gauge update [paper_fact]
Fact ID: masot-cooling-gauge
Source locator: Sec. II.B, first two paragraphs
PDF page: 2
Claim: The source inserts \(I=U_CU_C^\dagger\), applies \(U_C\) to the tensor network, and absorbs \(U_C^\dagger\) into the Clifford component while preserving the physical state.

## Heuristic cooling procedure [paper_fact]
Fact ID: masot-heuristic-cooling
Source locator: Sec. II.B, Definition 2, Eq. (2), and Fig. 2
PDF page: 3
Claim: The source's \(k\)-local heuristic sweeps over contiguous site groups, evaluates Clifford candidates with an entropy objective, and retains an improving candidate up to sweep depth \(d\).

## Printed local-equivalence relation [paper_fact]
Fact ID: masot-double-sided-relation
Source locator: Sec. II.B, local-equivalence paragraph
PDF page: 3
Claim: The source defines \(U\sim V\) by \(V=(L_1\otimes L_2)U(R_1\otimes R_2)\), with \(L_i\) and \(R_i\) single-qubit Clifford gates.

## Printed twenty-representative statement [paper_fact]
Fact ID: masot-twenty-statement
Source locator: Sec. II.B, final sentence of the local-equivalence paragraph
PDF page: 3
Claim: Immediately after the printed local-equivalence relation, the source states that one representative from each entangling class reduces the 11,520 two-qubit Clifford gates to 20 gates.

## Missing representative derivation [literature_gap]
Fact ID: masot-gap-representative-derivation
Source locator: Sec. II.B, local-equivalence paragraph
PDF page: 3
Claim: The source does not enumerate the reported 20 gates or derive their count from the printed local-equivalence relation.
Gap scope: source_local

## Exact-cooling sufficient construction [paper_fact]
Fact ID: masot-exact-cooling-construction
Source locator: Appendix A, restated exact-cooling definition and Fig. 11
PDF page: 13
Claim: The source describes exact cooling for an affected separable stabilizer site by leaving a local rotation on that site and absorbing a controlled-Pauli cascade into the Clifford component.

## Universal no-go theorem statement [paper_fact]
Fact ID: masot-theorem-statement
Source locator: Sec. III.C, Theorem III.1
PDF page: 6
Claim: The source states that a unitary which leaves the last qubit separable for arbitrary angle and remainder state is Clifford if and only if the fixed last-qubit input is a stabilizer state.

## Printed arbitrary-unitary decomposition [paper_fact]
Fact ID: masot-printed-unitary-decomposition
Source locator: Appendix B, Eq. (B1)
PDF page: 13
Claim: The source begins its proof by asserting that any unitary has a two-block decomposition over \(\lvert\phi_n\rangle\), \(\lvert\bar\phi_n\rangle\), \(\lvert\omega\rangle\), and \(\lvert\bar\omega\rangle\).

## Printed orthonormalization step [paper_fact]
Fact ID: masot-printed-orthonormalization
Source locator: Appendix B, Eq. (B5)
PDF page: 14
Claim: The source divides \(\lvert\Omega_2\rangle-\langle\Omega_1\vert\Omega_2\rangle\lvert\Omega_1\rangle\) by \(\sqrt{1+\langle\Omega_1\vert\Omega_2\rangle^2}\) and calls the resulting pair orthonormal.

## Printed operator conclusion [paper_fact]
Fact ID: masot-printed-operator-conclusion
Source locator: Appendix B, Eqs. (B17) and (B18)
PDF page: 15
Claim: The source uses its all-\(\lvert\Psi\rangle\) condition to infer the displayed Eq. (B18) expression for \(U_2\).

## Printed purity conclusion [paper_fact]
Fact ID: masot-printed-purity-conclusion
Source locator: Appendix B, Eqs. (B27)--(B32) and final paragraph
PDF page: 17
Claim: The source uses the displayed single-qubit purity bounds and their stated equality cases to conclude the necessity direction of Theorem III.1.

## Special-state caveat [paper_fact]
Fact ID: masot-special-state-caveat
Source locator: Appendix B, paragraph following Eq. (B10)
PDF page: 15
Claim: The source says its proof does not rule out a gadget depending on a particular remainder state \(\lvert\Psi\rangle\) or a special case using another separable stabilizer site.

## Missing independent theorem proof [literature_gap]
Fact ID: masot-gap-independent-theorem-proof
Source locator: Appendix B, Eqs. (B1)--(B32)
PDF page: 14
Claim: The source provides no proof of Theorem III.1 independent of the Appendix B chain that uses Eqs. (B1) and (B5).
Gap scope: source_local

## Two-local versus three-local observation [paper_fact]
Fact ID: masot-two-three-local-observation
Source locator: Sec. III.A, Fig. 4 and accompanying paragraph
PDF page: 5
Claim: For the reported \(N=12\) random Clifford-plus-\(T\) MPS ensemble, the source observes no improvement from its three-local update over the two-local heuristic.

## Sweep-depth observation [paper_fact]
Fact ID: masot-depth-observation
Source locator: Sec. III.A, Fig. 5 and accompanying paragraph
PDF page: 5
Claim: For the reported random-circuit experiment, the source observes no clear advantage from increasing the tested number of two-local cooling sweeps.

## Non-Clifford accumulation observation [paper_fact]
Fact ID: masot-nonclifford-accumulation
Source locator: Sec. IV, Fig. 7 and accompanying discussion
PDF page: 7
Claim: On the reported random Clifford-plus-rotation MPS workloads, the source observes residual entanglement accumulation whose onset is delayed for smaller rotation angles.

## No PEPS result [literature_gap]
Fact ID: masot-gap-peps
Source locator: Sec. V, future-work paragraph
PDF page: 9
Claim: This source does not provide a PEPS construction, contraction rule, benchmark, correctness theorem, or resource comparison.
Gap scope: source_local

## No measurement--reset instrument [literature_gap]
Fact ID: masot-gap-measurement-reset
Source locator: Sec. V and complete source scope
PDF page: 9
Claim: This source does not define selective measurement, Born branch mass, reset, conditional trajectories, syndrome Records, or a Record-law metric.
Gap scope: source_local

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:quant-ph/0406196"
source_version = "v5"
source_uri = "https://arxiv.org/abs/quant-ph/0406196v5"
source_artifact = "docs/papers/quant-ph_0406196v5.pdf"
source_sha256 = "ef9e472536b380b60c365ca6a03b92680a43d725cfe5f8189a8325fc16bc11ef"
title = "Improved Simulation of Stabilizer Circuits"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/AARONSON_GOTTESMAN_0406196V5_STABILIZER_ANCHOR_AUDIT_2026-08-01.md"
audit_packet_sha256 = "404cdd98c4f55c08f9bd056a55025b119bbf911536b72f88141ec563c61b9964"
admission_status = "source_only_reviewed"
admission_reviewer = "independent-source-only-admission-review-wf_8b4fc2de-2026-08-01"
admission_date = "2026-08-01"
visually_checked_pages = [1, 2, 3, 4, 5, 8]

[[relations]]
predicate = "defines"
object_id = "stabilizer-tableau"
object_type = "method"
object_label = "tableau"
fact_id = "ag-tableau-representation"

[[relations]]
predicate = "derives"
object_id = "tableau-gate-updates"
object_type = "method"
object_label = "O(n) per gate"
fact_id = "ag-gate-updates"

[[relations]]
predicate = "derives"
object_id = "tableau-measurement"
object_type = "method"
object_label = "O(n^2)"
fact_id = "ag-measurement"

[[relations]]
predicate = "supports"
object_id = "gottesman-knill-simulability"
object_type = "theorem"
object_label = "simulated efficiently on a classical computer"
fact_id = "ag-gottesman-knill"

[[relations]]
predicate = "derives"
object_id = "stabilizer-inner-product-magnitude"
object_type = "observable"
object_label = "inner product between two stabilizer states"
fact_id = "ag-inner-product"

+++
# Full-text review — Aaronson and Gottesman, "Improved Simulation of Stabilizer Circuits"

## Source identity [paper_fact]
Fact ID: ag-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The reviewed fixed source is the fifteen-page preprint arXiv:quant-ph/0406196v5 by Aaronson and Gottesman, carrying the arXiv date line 18 Jun 2008.

The artifact is the arXiv v5 PDF. This record binds to the arXiv artifact only and
makes no statement about any journal version.

## Selection scope [paper_fact]
Fact ID: ag-selection-scope
Source locator: Abstract and Sec. I (Sec. I spans PDF pages 1-2)
PDF page: 1
Claim: The source improves the Gottesman-Knill classical simulation of stabilizer circuits, removing Gaussian elimination from measurement simulation and adding algorithms for the inner product between stabilizer states and a canonical circuit form.

## Gottesman-Knill simulability [paper_fact]
Fact ID: ag-gottesman-knill
Source locator: Abstract (PDF page 1), Sec. I (PDF pages 1-2), and Theorem 1
PDF page: 3
Claim: A stabilizer circuit — CNOT, Hadamard, phase, and 1-qubit measurement gates — can be simulated efficiently on a classical computer, and Theorem 1 characterizes the states reachable from |0...0> by such circuits as exactly those stabilized by 2^n Pauli operators and uniquely determined by their Pauli stabilizer group.

## Tableau representation [paper_fact]
Fact ID: ag-tableau-representation
Source locator: Sec. III, tableau display and surrounding text
PDF page: 4
Claim: The simulation state is a tableau of binary variables x_ij, z_ij for i in {1..2n}, j in {1..n} plus phase bits r_i, whose rows 1..n are destabilizer generators and rows n+1..2n are stabilizer generators, requiring 2n(2n+1) bits.

Notation ledger: the inline encoding sentence on PDF page 4 prints "00 means I, 01
means X, 11 means Y, and 10 means Z", while the Sec. V proof on PDF page 8 prints
"I = 00, X = 10, Y = 11, Z = 01"; as literal (x, z) pairs these disagree. The
operative semantics is fixed by the |00> example tableau on PDF page 4 (stabilizer
rows +ZI and +IZ have zero x-bits) and the Hadamard rule swapping x and z: the x-bit
carries the X component, the z-bit the Z component. This record preserves the
discrepancy without resolving which sentence is in error.

## Clifford-gate updates [paper_fact]
Fact ID: ag-gate-updates
Source locator: Sec. III, gate procedures
PDF page: 4
Claim: CNOT(a->b) sets r_i ^= x_ia z_ib (x_ib ^ z_ia ^ 1), x_ib ^= x_ia, z_ia ^= z_ib; Hadamard(a) sets r_i ^= x_ia z_ia and swaps x_ia with z_ia; Phase(a) sets r_i ^= x_ia z_ia then z_ia ^= x_ia — each over all 2n rows, hence O(n) per gate.

## rowsum phase bookkeeping [paper_fact]
Fact ID: ag-rowsum
Source locator: Sec. III, rowsum subroutine
PDF page: 4
Claim: rowsum(h, i) sets generator h to i + h with the phase bit determined by 2r_h + 2r_i + sum_j g(x_ij, z_ij, x_hj, z_hj) modulo 4, which the source states is never congruent to 1 or 3.

## Measurement simulation [paper_fact]
Fact ID: ag-measurement
Source locator: Sec. III, measurement procedure (PDF page 4) and Proposition 3 (PDF page 5)
PDF page: 4
Claim: Measuring qubit a takes O(n^2): if some stabilizer row has x_pa = 1 the outcome is random and the tableau is updated by rowsum calls and row replacement, and otherwise the outcome is determinate and obtained by rowsum-ing into a scratch row the stabilizer partners of destabilizer rows with x_ia = 1, with correctness resting on the four invariants of Proposition 3.

## Stabilizer inner product [paper_fact]
Fact ID: ag-inner-product
Source locator: End of Sec. III
PDF page: 5
Claim: The inner product between two stabilizer states is 0 if their stabilizers contain the same Pauli operator with opposite signs and otherwise equals 2^(-s/2), where s is the minimum over generating sets of the number of differing generators, computable by transforming one state to |0...0> via the Theorem 8 canonical form and Gaussian-eliminating the other tableau, in order n^3 steps.

The printed example: <XX, ZZ> and <ZI, IZ> have inner product 1/sqrt(2), since
<ZI, IZ> = <ZI, ZZ>.

## Inner-product phase scope [literature_gap]
Fact ID: ag-inner-product-phase-scope
Source locator: End of Sec. III
PDF page: 5
Claim: The printed inner-product passage assigns the nonnegative value 2^(-s/2) and does not discuss the complex phase of the overlap between the two stabilizer states.
Gap scope: source_local

## No distance measure [literature_gap]
Fact ID: ag-no-trace-distance
Source locator: Complete source scope, PDF pages 1-15 (Secs. I-IX)
PDF page: 1
Claim: The source nowhere defines a trace distance or any distance between stabilizer states, and states no identity connecting the inner product to a distance.
Gap scope: source_local

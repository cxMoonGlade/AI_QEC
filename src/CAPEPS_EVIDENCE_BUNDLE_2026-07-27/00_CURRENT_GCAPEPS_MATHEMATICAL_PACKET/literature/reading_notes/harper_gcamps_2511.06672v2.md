+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2511.06672"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2511.06672v2"
source_artifact = "docs/papers/2511.06672v2.pdf"
source_sha256 = "880c44e25e9c1fd589a75ca5e824e58a2436c0c35a7ee7dddebbb61d439a0c42"
title = "GCAMPS: A Scalable Classical Simulator for Qudit Systems"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md"
audit_packet_sha256 = "0851e0c193d47df5ac789c6fa398a4bd9357bc04611f148aa59d77928a6a6cea"
admission_status = "source_only_reviewed"
admission_reviewer = "gcamps_independent_source_formula_review_2026_07_27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8]

[[relations]]
predicate = "defines"
object_id = "gcamps-hybrid-state"
object_type = "model"
object_label = "leading Clifford"
fact_id = "gcamps-hybrid-invariant"

[[relations]]
predicate = "defines"
object_id = "gcamps-tableau-generator-decomposition"
object_type = "method"
object_label = "stabilizer and destabilizer exponents"
fact_id = "gcamps-equation-5"

[[relations]]
predicate = "uses"
object_id = "generalized-pauli-basis"
object_type = "method"
object_label = "operator basis"
fact_id = "gcamps-generalized-pauli"

[[relations]]
predicate = "uses"
object_id = "non-clifford-pauli-expansion"
object_type = "method"
object_label = "sum of generalized Pauli words"
fact_id = "gcamps-nonclifford-expansion"

[[relations]]
predicate = "defines"
object_id = "gcamps-clifford-disentangling-update"
object_type = "method"
object_label = "heuristic Clifford"
fact_id = "gcamps-disentangler-update"

[[relations]]
predicate = "measures"
object_id = "gcamps-scaled-bond-dimension"
object_type = "observable"
object_label = "scaled bond dimension"
fact_id = "gcamps-scaled-bond"

[[relations]]
predicate = "limits"
object_id = "general-disentangler-search"
object_type = "limitation"
object_label = "more efficient search"
fact_id = "gcamps-disentangler-scaling-limit"
+++
# Full-text review — Harper et al., “GCAMPS: A Scalable Classical Simulator for Qudit Systems”

## Source identity [paper_fact]
Fact ID: gcamps-source-identity
Source locator: Title page, publication block, and arXiv version line
PDF page: 1
Claim: The reviewed source is arXiv:2511.06672v2, titled “GCAMPS: A Scalable Classical Simulator for Qudit Systems,” published in the SCA/HPCAsia 2026 proceedings.

The title page names Ben Harper, Azar C. Nakhl, Thomas Quella, Martin Sevior,
and Muhammad Usman. The v2 artifact is dated 27 January 2026 and gives
DOI 10.1145/3773656.3773689.

## Qubit and qudit state-vector definitions [paper_fact]
Fact ID: gcamps-state-vector-definitions
Source locator: Sec. 2.1, Eqs. (1)–(2)
PDF page: 2
Claim: The source defines a qubit state by two normalized complex amplitudes and a qudit state by a sum of amplitudes over \(d\) orthogonal basis states.

Equation (1) writes
\(\lvert\psi\rangle=\alpha\lvert0\rangle+\beta\lvert1\rangle\) with
\(\lvert\alpha\rvert^2+\lvert\beta\rvert^2=1\). Equation (2) writes
\(\lvert\psi_d\rangle=\sum_{j=0}^{d-1}c_j\lvert j\rangle\).

## Direct state-vector storage cost [paper_fact]
Fact ID: gcamps-state-vector-storage
Source locator: Sec. 2.1, paragraph following Eq. (2)
PDF page: 2
Claim: The source assigns \(O(d^n)\) entries to an \(n\)-qudit state vector and \(O(d^{2n})\) entries to a general unitary.

## Qubit Pauli convention [paper_fact]
Fact ID: gcamps-qubit-pauli
Source locator: Sec. 2.2, Eq. (3)
PDF page: 2
Claim: The source defines the qubit Pauli matrices \(X\) and \(Z\) and fixes the convention \(Y=iXZ\).

## Stabilizer tableau representation [paper_fact]
Fact ID: gcamps-qubit-tableau
Source locator: Sec. 2.2, Eq. (4) and the paragraphs immediately before and after it
PDF page: 3
Claim: The source represents an \(n\)-qubit stabilizer state with \(n\) stabilizer and \(n\) destabilizer generators plus a phase column, producing a \(2n\times(2n+1)\) tableau with \(O(n^2)\) storage.

Equation (4) illustrates the construction for \(\lvert00\rangle\) with
generators \(ZI,IZ,XI,IX\). The text says the combined stabilizer and
destabilizer generators form a complete Pauli basis.

## Clifford tableau update direction [paper_fact]
Fact ID: gcamps-clifford-forward-update
Source locator: Sec. 2.2, displayed derivation beginning \(U\lvert\phi\rangle=US\lvert\phi\rangle\)
PDF page: 3
Claim: The source updates a stabilizer generator under a Clifford \(U\) by forward conjugation \(S'=USU^\dagger\).

The displayed derivation inserts \(U^\dagger U\) and concludes that
\(S'\) stabilizes \(U\lvert\phi\rangle\). The update direction is therefore
forward conjugation, not inverse conjugation.

## Generalized Pauli algebra [paper_fact]
Fact ID: gcamps-generalized-pauli
Source locator: Sec. 2.3, displayed definitions of \(\omega\), \(X\), and \(Z\)
PDF page: 3
Claim: The source defines generalized Pauli shift and clock operators satisfying \(XZ=\omega^{-1}ZX\), where \(\omega=\exp(2\pi i/d)\), and uses \(X^xZ^z\) terms as an operator basis.

The shift acts as \(X\lvert j\rangle=\lvert j+1\bmod d\rangle\), while the
clock acts as \(Z\lvert j\rangle=\omega^j\lvert j\rangle\).

## Odd- and even-dimension phase convention [paper_fact]
Fact ID: gcamps-qudit-phase-convention
Source locator: Sec. 2.3, paragraph following the generalized Pauli definitions
PDF page: 3
Claim: The source uses \(Y=XZ\) for odd \(d\), but introduces \(\tau=\omega^{1/2}\) and \(Y=\tau XZ\) for even \(d\) so that generalized Pauli operators have order \(d\).

## Even-dimension phase-column ambiguity [literature_gap]
Fact ID: gcamps-gap-even-phase-column
Source locator: Sec. 2.3, consecutive paragraphs on \(\tau\) and the generalized tableau phase column
PDF page: 3
Claim: The source does not reconcile the even-\(d\) \(\tau=\omega^{1/2}\) phase with its subsequent statement that the tableau phase column stores only \(\omega^k\) for \(k\in\mathbb Z_d\).
Gap scope: source_local

The source gives no phase-exponent range or lifting rule that contains both phase sets.

## Generalized Clifford gates and conjugation rules [paper_fact]
Fact ID: gcamps-generalized-cliffords
Source locator: Sec. 2.3 and Table 1
PDF page: 3
Claim: The source defines \(H_d\), parity-dependent \(S_d\), and \(\mathrm{SUM}_d\), and gives their forward conjugation rules on generalized Pauli generators.

The Fourier gate maps \(X\) to \(Z\) and \(Z\) to \(X^{-1}\). The phase gate
maps \(X\) to the chosen \(Y\) and leaves \(Z\) fixed. The SUM gate maps
\(X\otimes I\) to \(X\otimes X\) and
\(I\otimes Z\) to \(Z^{-1}\otimes Z\), with the other two single-generator
images shown in Table 1.

## Stabilizer-generator decomposition [paper_fact]
Fact ID: gcamps-generator-product
Source locator: Sec. 2.3.1, displayed equations immediately preceding Eq. (5)
PDF page: 4
Claim: The source expresses a physical Pauli \(P=\prod_iX_i^{x_i}Z_i^{z_i}\) as \(P=c\prod_jS_j^{s_j}D_j^{d_j}\) in the stabilizer and destabilizer generator basis.

The coefficient \(c\) carries the phase that is not recovered by the
phase-free exponent-vector linear system.

## Tableau linear system [paper_fact]
Fact ID: gcamps-equation-5
Source locator: Sec. 2.3.1, Eq. (5) and following paragraph
PDF page: 4
Claim: Equation (5) solves for stabilizer and destabilizer exponents from a \(2n\times2n\) tableau matrix with its phase column removed, after which explicit generator multiplication recovers the overall phase.

The source writes the system as
\(P=M[\mathbf s;\mathbf d]\) and says Gaussian elimination is performed over
\(\mathbb Z_d\). It then instructs the reader to multiply the selected tableau
rows explicitly because noncommuting Pauli multiplication contributes phase.

## Equation-5 orientation ambiguity [literature_gap]
Fact ID: gcamps-gap-equation-5-orientation
Source locator: Sec. 2.3.1, Eq. (5) and its defining prose
PDF page: 4
Claim: The source does not resolve whether the generator array in Eq. (5) is used with generators as rows or columns, because the prose calls them rows while the displayed column-vector equation has the opposite conventional orientation.
Gap scope: source_local

The source gives no worked example or vector-layout declaration selecting one orientation.

## Composite-dimension elimination limitation [literature_gap]
Fact ID: gcamps-gap-composite-elimination
Source locator: Sec. 2.3.1, paragraph following Eq. (5)
PDF page: 4
Claim: The source does not provide a congruence solver for composite \(d\), although it describes \(\mathbb Z_d\) as a field and calls for field Gaussian elimination.
Gap scope: source_local

\(\mathbb Z_d\) is a field only when \(d\) is prime. The reported experiments
use \(d=2\) and \(d=3\), so this gap does not affect those two benchmark
dimensions.

## Non-Clifford gate examples [paper_fact]
Fact ID: gcamps-nonclifford-examples
Source locator: Sec. 2.3.2, displayed \(T_2\) and \(T_3\) matrices and following \(R_Z\) paragraph
PDF page: 4
Claim: The source gives explicit diagonal \(T\) gates for \(d=2\) and \(d=3\), while stating that its implementation uses a parameterized \(R_Z\) with \(T=e^{i\pi/8}R_Z(\pi/4)\).

The qutrit \(T_3\) is presented explicitly through its three diagonal phases.

## Matrix-product-state representation [paper_fact]
Fact ID: gcamps-equation-6
Source locator: Sec. 2.4, Eq. (6) and immediately following paragraph
PDF page: 4
Claim: Equation (6) represents an \(N\)-site \(d\)-level state as a product of site-indexed matrices whose virtual dimensions \(\chi_i\) encode the bipartite bond structure.

The source assigns site matrices virtual dimensions \(\chi_{i-1}\times\chi_i\)
and calls \(\chi\) the bond dimension.

## MPS SVD bond reduction [paper_fact]
Fact ID: gcamps-mps-svd-reduction
Source locator: Sec. 2.4, paragraph on SVD reduction
PDF page: 4
Claim: The source states that an MPS bond can be reduced approximately by an SVD that retains only a fixed number of singular values.

## Local and multi-site operator bond growth [paper_fact]
Fact ID: gcamps-mps-operator-bond-growth
Source locator: Sec. 2.4, paragraph beginning “Evolving an MPS”
PDF page: 4
Claim: The source states that a one-site operator does not increase MPS bond dimensions, whereas a multi-site operator may increase relevant bonds by a factor of \(d\), with adjacent support preferred.

## Truncation-error specification gap [literature_gap]
Fact ID: gcamps-gap-truncation-error
Source locator: Sec. 2.4, paragraph on SVD truncation
PDF page: 4
Claim: The source does not define a truncation cutoff, discarded-weight observable, normalization rule, or accumulated state or observable error bound for its SVD reductions.
Gap scope: source_local

The source describes retaining a fixed number of singular values but does not
turn that choice into a quantitative fidelity certificate.

## GCAMPS hybrid invariant [paper_fact]
Fact ID: gcamps-hybrid-invariant
Source locator: Sec. 3, opening paragraphs and Fig. 3
PDF page: 5
Claim: GCAMPS represents a state as \(\lvert\psi\rangle=C\lvert\mathrm{MPS}\rangle\), with the leading Clifford stored in a stabilizer tableau and the residual state stored as an MPS.

The source says a physical Clifford gate updates \(C\) directly without
changing the MPS.

## Non-Clifford Pauli expansion and commutation [paper_fact]
Fact ID: gcamps-nonclifford-expansion
Source locator: Sec. 3, paragraph beginning “To perform non-Clifford operations”
PDF page: 5
Claim: The source numerically expands a small-support non-Clifford unitary as a sum of generalized Pauli words, commutes each word through \(C\), and applies the resulting operator to the MPS.

The source warns that an originally local operator can become nonlocal after
commutation and can increase MPS bond dimensions.

## Pauli-expansion solver gap [literature_gap]
Fact ID: gcamps-gap-pauli-coefficients
Source locator: Sec. 3, paragraph specifying a numerical linear system for \(U\)
PDF page: 5
Claim: The source does not give the coefficient-matrix layout, basis ordering, zero policy, numerical tolerance, support guard, or reconstruction acceptance rule for its non-Clifford Pauli expansion.
Gap scope: source_local

The text establishes that a numerical linear system is used for a gate acting
on a small number of sites, but does not provide an executable solver
specification.

## Clifford disentangling update [paper_fact]
Fact ID: gcamps-disentangler-update
Source locator: Sec. 3, paragraph beginning “Having performed a non-Clifford operation”
PDF page: 5
Claim: The source applies a heuristic Clifford \(Q\) to the residual MPS to reduce entanglement and preserves the represented state by updating the leading Clifford to \(\widetilde C=CQ^\dagger\).

The two updates are paired: the residual becomes
\(Q\lvert\mathrm{MPS}\rangle\), while the leading Clifford acquires
\(Q^\dagger\) on its right.

## Unique two-qudit entangler counts [paper_fact]
Fact ID: gcamps-unique-entanglers
Source locator: Secs. 3 and 3.1
PDF page: 5
Claim: The source reports 20 uniquely entangling two-qubit Cliffords for \(d=2\) and 90 uniquely entangling two-qutrit Cliffords for \(d=3\).

## Two-qudit entangler canonicalization procedure [paper_fact]
Fact ID: gcamps-entangler-canonicalization
Source locator: Sec. 3.1, first paragraph
PDF page: 5
Claim: The source generates every two-qudit Clifford tableau, applies single-qudit gates to obtain canonical forms, and removes duplicate entanglement structures.

## Disentangler-search specification gap [literature_gap]
Fact ID: gcamps-gap-disentangler-objective
Source locator: Secs. 3 and 3.1, complete disentangler discussion
PDF page: 5
Claim: The source does not provide the 20 or 90 gate lists, a canonical key, a mathematical entanglement objective, a threshold, a tie-break rule, a layer schedule, or a stopping rule for the disentangler optimizer.
Gap scope: source_local

The reported counts and high-level generation procedure do not by themselves
define a reproducible optimizer.

## Disentangler scaling limitation [paper_fact]
Fact ID: gcamps-disentangler-scaling-limit
Source locator: Sec. 3.1, final paragraph
PDF page: 6
Claim: The source says the set of generalized Clifford tableaus grows exponentially with \(d\), places \(d>3\) beyond the scope of the work, and leaves more efficient search for future work.

This limitation is attached to the exhaustive local-disentangler procedure,
not to state-vector dimension alone.

## Pauli-observable evaluation [paper_fact]
Fact ID: gcamps-pauli-observable
Source locator: Sec. 3, observable paragraph
PDF page: 5
Claim: For \(d=2\), the source evaluates a physical Pauli observable by commuting it through \(C\) and contracting the resulting Pauli string against the residual MPS.

## Generalized-Pauli Hermitian observable [paper_fact]
Fact ID: gcamps-qudit-hermitian-observable
Source locator: Sec. 3, observable paragraph
PDF page: 5
Claim: For \(d\ne2\), the source defines \(O_\sigma=(\sigma+\sigma^\dagger)/2\) because generalized Pauli words need not be Hermitian, and states that evaluating it can increase an MPS bond dimension by at most a factor of \(d\).

## Benchmark circuit definition [paper_fact]
Fact ID: gcamps-benchmark-circuit
Source locator: Sec. 4 and Fig. 4
PDF page: 6
Claim: The reported benchmark uses layers consisting of a random Clifford followed by one \(T\) gate on the first qudit, with layer count \(t\) equal to the non-Clifford \(T\)-gate count.

The source compares qubit and qutrit GCAMPS against conventional MPS on this
workload.

## Scaled bond-dimension observable [paper_fact]
Fact ID: gcamps-scaled-bond
Source locator: Sec. 4 and Fig. 5
PDF page: 7
Claim: The source plots scaled circuit depth \(t/N\) against scaled bond dimension \(2\log_d(\chi)/N\).

## Scaled bond-dimension benchmark finding [paper_fact]
Fact ID: gcamps-scaled-bond-finding
Source locator: Sec. 4 and Fig. 5
PDF page: 7
Claim: The source reports a low-depth near-constant-bond regime followed by growth around \(t\) of order \(N\) for the benchmarked GCAMPS circuits, while the conventional MPS curves approach maximal bond dimension after comparatively few layers.

## Runtime benchmark [paper_fact]
Fact ID: gcamps-runtime-benchmark
Source locator: Sec. 4.1.1 and Fig. 6
PDF page: 8
Claim: The source reports GCAMPS and MPS runtime comparisons at fixed \(N=12\) and at fixed depth \(t=0.5N\), with a larger low-depth relative improvement for qutrit GCAMPS than for qubit GCAMPS on the selected workload.

## Pauli-decomposition matrix sizes [paper_fact]
Fact ID: gcamps-runtime-matrix-sizes
Source locator: Sec. 4.1.1, paragraph discussing the qubit-to-qutrit runtime transition
PDF page: 6
Claim: The source reports maximum decomposition-matrix sizes of \(128\times128\) for qubits and \(2187\times2187\) for qutrits, and associates the transition with exponential growth in bond dimensions and decomposition size.

## Memory extrapolation [paper_fact]
Fact ID: gcamps-memory-model
Source locator: Sec. 4.1.2, paragraph beginning “In Figure 7”
PDF page: 6
Claim: The source extrapolates MPS tensor memory from \(\chi_l\chi_rd\) complex values per site tensor, using two 64-bit floating-point values per complex number.

## Pre-optimization memory assumption [paper_fact]
Fact ID: gcamps-memory-peak-assumption
Source locator: Sec. 4.1.2 and Fig. 7
PDF page: 8
Claim: For GCAMPS, the source extrapolates a pre-optimization worst case in which a non-Clifford operation increases every bond by a factor of \(d\); the plotted memory is derived from bond dimensions rather than whole-process resident memory.

## Total-memory-accounting gap [literature_gap]
Fact ID: gcamps-gap-total-memory
Source locator: Secs. 2.2 and 4.1.2, together with Fig. 7
PDF page: 8
Claim: The source does not include tableau storage, temporary decompositions, SVD workspace, object overhead, or contraction workspace in the memory curves inferred from MPS bond dimensions.
Gap scope: source_local

The source separately assigns \(O(N^2)\) storage to a tableau, so a
constant-bond residual-MPS payload does not alone establish that complete
GCAMPS memory is linear in \(N\).

## Benchmark-ensemble specification gap [literature_gap]
Fact ID: gcamps-gap-benchmark-ensemble
Source locator: Sec. 4 and Figs. 4–7
PDF page: 6
Claim: The source does not provide the random-Clifford distribution, random seeds, complete sample counts, or error bars needed to reconstruct the benchmark ensemble.
Gap scope: source_local

## Benchmark-environment specification gap [literature_gap]
Fact ID: gcamps-gap-benchmark-environment
Source locator: Sec. 4.1.1 execution note and full-text methods boundary
PDF page: 6
Claim: The source does not provide an executable implementation, dependency versions, or a complete machine specification needed for bit-for-bit benchmark reproduction.
Gap scope: source_local

## Measurement and reset gap [literature_gap]
Fact ID: gcamps-gap-measurement-reset
Source locator: Sec. 3 workflow and full-text algorithmic scope in Secs. 3–5
PDF page: 5
Claim: The source does not define selective measurement, reset, branch probabilities, stochastic trajectories, noise channels, or a multi-time measurement-record law for GCAMPS.
Gap scope: source_local

The developed workflow applies Clifford and non-Clifford gates, performs
residual optimization, and evaluates observables. It does not specify a
measurement-reset instrument.

## PEPS-generalization gap [literature_gap]
Fact ID: gcamps-gap-peps
Source locator: Sec. 2.4, Eq. (6), and full-text tensor-network scope in Secs. 2.4–5
PDF page: 4
Claim: The source does not derive a PEPS replacement for the residual MPS or prove a PEPS contraction, bond, runtime, memory, or fidelity bound for such a replacement.
Gap scope: source_local

All tensor-network formulas, optimization discussion, and reported benchmarks use an MPS residual.

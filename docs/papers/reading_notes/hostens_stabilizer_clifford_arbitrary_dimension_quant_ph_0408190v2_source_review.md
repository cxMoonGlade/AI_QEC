+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:quant-ph/0408190"
source_version = "v2"
source_uri = "https://arxiv.org/abs/quant-ph/0408190v2"
source_artifact = "docs/papers/quant-ph_0408190v2.pdf"
source_sha256 = "b48cf81d89050ccf9372d5be713c098088fd3a0d371e9be2a9901d09ef07c831"
title = "Stabilizer states and Clifford operations for systems of arbitrary dimensions, and modular arithmetic"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/HOSTENS_QUANT_PH_0408190V2_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "80eac75b50ff59b4008dd0f288ab5080b84e704bb8ad45996c480bf9a1df8a74"
admission_status = "source_only_reviewed"
admission_reviewer = "hostens_independent_source_review_2026_07_27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

[[relations]]
predicate = "defines"
object_id = "generalized-shift-phase-operators"
object_type = "concept"
object_label = "generalized shift and phase operators"
fact_id = "hostens0408190-shift-phase"

[[relations]]
predicate = "defines"
object_id = "generalized-pauli-group"
object_type = "concept"
object_label = "Pauli group"
fact_id = "hostens0408190-pauli-group"

[[relations]]
predicate = "derives"
object_id = "pauli-commutation-relation"
object_type = "method"
object_label = "commutation relation"
fact_id = "hostens0408190-commutation"

[[relations]]
predicate = "defines"
object_id = "arbitrary-d-clifford-operation"
object_type = "concept"
object_label = "Clifford operation"
fact_id = "hostens0408190-clifford-normalizer"

[[relations]]
predicate = "defines"
object_id = "clifford-c-h-representation"
object_type = "model"
object_label = "Clifford representation"
fact_id = "hostens0408190-clifford-representation"

[[relations]]
predicate = "defines"
object_id = "symplectic-clifford-condition"
object_type = "concept"
object_label = "symplectic condition"
fact_id = "hostens0408190-symplectic-condition"

[[relations]]
predicate = "derives"
object_id = "clifford-decomposition"
object_type = "method"
object_label = "Clifford decomposition"
fact_id = "hostens0408190-decomposition"

[[relations]]
predicate = "defines"
object_id = "arbitrary-d-stabilizer-state"
object_type = "concept"
object_label = "stabilizer state"
fact_id = "hostens0408190-stabilizer-definition"

[[relations]]
predicate = "defines"
object_id = "stabilizer-generator-matrix-change"
object_type = "method"
object_label = "stabilizer generator matrix change"
fact_id = "hostens0408190-generator-change"

[[relations]]
predicate = "derives"
object_id = "clifford-action-on-stabilizers"
object_type = "method"
object_label = "Clifford action on stabilizers"
fact_id = "hostens0408190-stabilizer-clifford-update"

[[relations]]
predicate = "derives"
object_id = "stabilizer-standard-basis-expansion"
object_type = "theorem"
object_label = "standard-basis expansion"
fact_id = "hostens0408190-basis-expansion"

[[relations]]
predicate = "defines"
object_id = "odd-d-pauli-representation"
object_type = "concept"
object_label = "odd-d Pauli representation"
fact_id = "hostens0408190-odd-pauli"
+++
# Full-text review — Hostens, Dehaene, and De Moor, “Stabilizer states and Clifford operations for systems of arbitrary dimensions, and modular arithmetic”

## Source identity [paper_fact]
Fact ID: hostens0408190-source-identity
Source locator: PDF p. 1, title block, author block, and arXiv footer
PDF page: 1
Claim: The reviewed artifact identifies Erik Hostens, Jeroen Dehaene, and Bart De Moor as authors and carries the visible footer `arXiv:quant-ph/0408190v2 22 Feb 2005`.

## Printed title-page date [paper_fact]
Fact ID: hostens0408190-title-date
Source locator: PDF p. 1, title block, date line
PDF page: 1
Claim: The title page prints the date October 23, 2018.

## Declared mathematical scope [paper_fact]
Fact ID: hostens0408190-declared-scope
Source locator: PDF p. 1, abstract
PDF page: 1
Claim: The source describes generalized Pauli groups, Clifford groups, and stabilizer states for arbitrary one-qudit dimension using matrices over \(\mathbb Z_d\), together with Clifford decomposition and standard-basis stabilizer expansions.

## Declared coding nonfocus [paper_fact]
Fact ID: hostens0408190-coding-nonfocus
Source locator: PDF p. 1, Introduction, third substantive paragraph
PDF page: 1
Claim: The authors state that their motivation is not primarily the study of stabilizer codes and their error-correcting capacities, but mathematically interesting states and operations that may play a role in quantum algorithms.

## Generalized shift and phase operators [paper_fact]
Fact ID: hostens0408190-shift-phase
Source locator: PDF p. 2, Sec. II.A, Eq. (1)
PDF page: 2
Claim: The generalized shift and phase operators satisfy \(X^{(d)}\lvert j\rangle=\lvert j+1\rangle\) and \(Z^{(d)}\lvert j\rangle=\omega^j\lvert j\rangle\) for \(j\in\mathbb Z_d\), with ket addition modulo \(d\).

## Pauli exponent-vector representation [paper_fact]
Fact ID: hostens0408190-pauli-vector
Source locator: PDF p. 2, Sec. II.A, Eqs. (2)--(3)
PDF page: 2
Claim: For \(a=[v;w]\in\mathbb Z_d^{2n}\), the source writes \(XZ(a)=X^{v_1}Z^{w_1}\otimes\cdots\otimes X^{v_n}Z^{w_n}\) and gives \(XZ(a)\lvert x\rangle=\omega^{w^Tx}\lvert x+v\rangle\).

## Generalized Pauli group [paper_fact]
Fact ID: hostens0408190-pauli-group
Source locator: PDF p. 2, Sec. II.A, paragraph before Eq. (4)
PDF page: 2
Claim: The Pauli group contains the \(d^{2n}\) operators \(XZ(a)\) multiplied by phases \(\zeta^\delta\), where \(\zeta\) is a square root of \(\omega\) and \(\delta\in\mathbb Z_{2d}\).

## Pauli multiplication law [paper_fact]
Fact ID: hostens0408190-pauli-multiplication
Source locator: PDF p. 2, Sec. II.A, Eq. (4)
PDF page: 2
Claim: Pauli multiplication is \(\zeta^\delta XZ(a)\zeta^\epsilon XZ(b)=\zeta^{\delta+\epsilon+2a^TUb}XZ(a+b)\), with exponent labels added modulo \(d\) and phase exponents modulo \(2d\).

## Pauli commutation relation [paper_fact]
Fact ID: hostens0408190-commutation
Source locator: PDF p. 2, Sec. II.A, Eqs. (5)--(6)
PDF page: 2
Claim: The commutation relation is \(XZ(a)XZ(b)=\omega^{a^TPb}XZ(b)XZ(a)\), where \(P=U-U^T\pmod d\).

## Even-d Pauli order [paper_fact]
Fact ID: hostens0408190-even-order
Source locator: PDF p. 2, Sec. II.A, paragraph after Eq. (6)
PDF page: 2
Claim: The order of \(XZ(a)\) divides \(d\), except that for even \(d\) and odd \(a^TUa\) it is \(2d\); the source says the \(\zeta^\delta\) phase rather than an \(\omega^\delta\) phase is necessary only when \(d\) is even.

## Clifford normalizer definition [paper_fact]
Fact ID: hostens0408190-clifford-normalizer
Source locator: PDF p. 2, Sec. II.B, opening paragraphs
PDF page: 2
Claim: A Clifford operation is a unitary operation \(Q\) satisfying \(Q\mathcal P_nQ^\dagger=\mathcal P_n\), and its conjugation action on the Pauli group determines it up to a global phase.

## Clifford C-h representation [paper_fact]
Fact ID: hostens0408190-clifford-representation
Source locator: PDF p. 2, Sec. II.B, paragraphs before and after Eq. (7)
PDF page: 2
Claim: The Clifford representation consists of a matrix \(C\in\mathbb Z_d^{2n\times2n}\) whose columns are the output labels of the standard Pauli generators and a phase vector \(h\in\mathbb Z_{2d}^{2n}\), and it completely specifies the operation up to global phase.

## Clifford conjugation update [paper_fact]
Fact ID: hostens0408190-clifford-update
Source locator: PDF p. 2, Sec. II.B, Eq. (7)
PDF page: 2
Claim: Under Clifford conjugation, the Pauli label updates as \(b=Ca\pmod d\), while the output phase is the modulo-\(2d\) polynomial in \(\delta,h,C,U\), and \(a\) printed in Eq. (7).

## Clifford composition [paper_fact]
Fact ID: hostens0408190-clifford-composition
Source locator: PDF p. 3, Sec. II.B, Eq. (8)
PDF page: 3
Claim: For \(Q''=Q'Q\), Eq. (8) gives \(C''=C'C\pmod d\) and the corresponding phase-vector composition formula modulo \(2d\).

## Clifford inverse [paper_fact]
Fact ID: hostens0408190-clifford-inverse
Source locator: PDF p. 3, Sec. II.B, Eq. (9)
PDF page: 3
Claim: Eq. (9) represents \(Q^\dagger\) by \(C'=C^{-1}\pmod d\) and a printed phase-vector inverse formula modulo \(2d\).

## Symplectic Clifford condition [paper_fact]
Fact ID: hostens0408190-symplectic-condition
Source locator: PDF p. 3, Sec. II.C, derivation before Eq. (10)
PDF page: 3
Claim: The symplectic condition for a Clifford label matrix is \(C^TPC=P\pmod d\), and it implies \(C^{-1}=-PC^TP\pmod d\).

## Clifford phase condition and sufficiency [paper_fact]
Fact ID: hostens0408190-clifford-phase-condition
Source locator: PDF p. 3, Sec. II.C, Eq. (10) and following sentence
PDF page: 3
Claim: The phase vector must satisfy \((d-1)\operatorname{Vdiag}(C^TUC)+h=0\pmod2\), and the source states that every symplectic \(C\) with an \(h\) satisfying this condition defines a Clifford operation.

## Pauli Clifford subclass [paper_fact]
Fact ID: hostens0408190-pauli-clifford
Source locator: PDF p. 3, Sec. III, first bullet
PDF page: 3
Claim: A Pauli operation \(XZ(a)\), viewed as a Clifford operation up to global phase, is represented by \(C=I\pmod d\) and \(h=-2Pa\pmod{2d}\).

## Configuration-space Clifford operations [paper_fact]
Fact ID: hostens0408190-configuration-transform
Source locator: PDF pp. 3--4, Sec. III, third bullet
PDF page: 3
Claim: Every invertible configuration-space map \(\lvert x\rangle\mapsto\lvert Tx\rangle\) is represented by \(C=\operatorname{diag}(T,T^{-T})\pmod d\) and \(h=0\pmod{2d}\); the listed special cases include qudit permutations and the two-qudit SUM gate.

## Discrete Fourier Clifford [paper_fact]
Fact ID: hostens0408190-fourier
Source locator: PDF p. 4, Sec. III, discrete-Fourier bullet
PDF page: 4
Claim: The one-qudit discrete Fourier transform is represented by \(C=\begin{bmatrix}0&-1\\1&0\end{bmatrix}\pmod d\) and \(h=0\pmod{2d}\).

## Qudit phase Clifford [paper_fact]
Fact ID: hostens0408190-phase-gate
Source locator: PDF p. 4, Sec. III, final bullet
PDF page: 4
Claim: The one-qudit map \(\lvert x\rangle\mapsto\zeta^{x(x+d)}\lvert x\rangle\) is represented by \(C=\begin{bmatrix}1&0\\1&1\end{bmatrix}\pmod d\) and \(h=[d+1;0]\pmod{2d}\).

## Clifford phase correction [paper_fact]
Fact ID: hostens0408190-phase-correction
Source locator: PDF p. 4, Sec. IV, opening paragraph
PDF page: 4
Claim: Once one admissible \((C,h)\) is realized, any other admissible \((C,h')\) with the same \(C\) can be realized by composing with a Pauli correction, because \(h'-h\) is even.

## Elementary row operations [paper_fact]
Fact ID: hostens0408190-row-operations
Source locator: PDF pp. 4--5, Sec. IV, elementary-operation paragraphs
PDF page: 4
Claim: The source realizes row swaps, unit row scalings, row additions, Fourier swaps between symplectic blocks, and phase-gate row additions as embedded one- or two-qudit Clifford operations.

## Composite-d unit condition [paper_fact]
Fact ID: hostens0408190-unit-condition
Source locator: PDF p. 4, Sec. IV, paragraph continuing on PDF p. 5
PDF page: 4
Claim: A row multiplier \(r\in\mathbb Z_d\) is invertible exactly when \(\gcd(r,d)=1\), and the companion row is multiplied by \(r^{-1}\).

## Composite-d Euclidean reduction [paper_fact]
Fact ID: hostens0408190-euclidean-reduction
Source locator: PDF p. 5, Sec. IV, paragraphs beginning with a noninvertible upper-left entry
PDF page: 5
Claim: A symplectic column can have no individually invertible entry; the source uses Euclid's algorithm on pairs of entries to form their gcd until the column gcd, which is invertible, is obtained.

## Clifford decomposition [paper_fact]
Fact ID: hostens0408190-decomposition
Source locator: PDF pp. 4--6, Sec. IV, constructive reduction of C to I
PDF page: 5
Claim: The Clifford decomposition reduces an arbitrary admissible symplectic matrix to identity with embedded operations acting on at most two qudits, then reverses those operations and applies the phase correction.

## Detailed decomposition complexity [paper_fact]
Fact ID: hostens0408190-detailed-complexity
Source locator: PDF p. 6, Sec. IV, final paragraph
PDF page: 6
Claim: After accounting for Euclid's algorithm, Sec. IV prints a decomposition count of \(O(n^2\log d)\) elementary operations.

## Stabilizer-state definition [paper_fact]
Fact ID: hostens0408190-stabilizer-definition
Source locator: PDF p. 6, Sec. V.A, opening definition paragraph
PDF page: 6
Claim: A stabilizer state is the simultaneous eigenvector with eigenvalue one of a subgroup of \(d^n\) commuting Pauli elements that contains no scalar multiple of identity other than identity itself.

## Stabilizer matrix representation [paper_fact]
Fact ID: hostens0408190-stabilizer-matrix
Source locator: PDF p. 6, Sec. V.A, opening definition paragraph
PDF page: 6
Claim: A generating set is represented by columns \(S_k\in\mathbb Z_d^{2n}\) of \(S\in\mathbb Z_d^{2n\times m}\) and phases \(f_k\in\mathbb Z_{2d}\), and generator commutation is \(S^TPS=0\pmod d\).

## Composite-d generator count [paper_fact]
Fact ID: hostens0408190-composite-generator-count
Source locator: PDF p. 6, Sec. V.A, paragraph before Eq. (11)
PDF page: 6
Claim: The source states that the minimal generator count can exceed \(n\), printing \(m=n\) when \(d\) has “only single prime factors” and \(n\le m\le2n\) when \(d\) has “multiple prime factors.”

## Four-level two-generator example [paper_fact]
Fact ID: hostens0408190-d4-example
Source locator: PDF p. 6, Sec. V.A, paragraph before Eq. (11)
PDF page: 6
Claim: For \(d=4,n=1\), the state \((\lvert0\rangle+\lvert2\rangle)/\sqrt2\) has stabilizer \(\{I,X^2,Z^2,X^2Z^2\}\) and minimal generator count \(m=2\).

## Stabilizer scalar-identity condition [paper_fact]
Fact ID: hostens0408190-stabilizer-phase-condition
Source locator: PDF p. 6, Sec. V.A, Eq. (11)
PDF page: 6
Claim: Eq. (11) gives the phase-vector congruence required whenever \(Sr=0\pmod d\), enforcing the exclusion of nonidentity scalar multiples of identity from the stabilizer.

## Stabilizer generator matrix change [paper_fact]
Fact ID: hostens0408190-generator-change
Source locator: PDF p. 6, Sec. V.A, Eq. (12)
PDF page: 6
Claim: An invertible right action \(S'=SR\pmod d\), together with the phase update printed in Eq. (12), is called a stabilizer generator matrix change.

## Clifford action on stabilizers [paper_fact]
Fact ID: hostens0408190-stabilizer-clifford-update
Source locator: PDF p. 6, Sec. V.A, Eq. (13)
PDF page: 6
Claim: The Clifford action on stabilizers sends \(S\) to \(S'=CS\pmod d\) and sends \(f\) to the modulo-\(2d\) phase vector printed in Eq. (13).

## Minimal-generator reduction [paper_fact]
Fact ID: hostens0408190-minimal-generator-reduction
Source locator: PDF p. 6, Sec. V.A, paragraph after Eq. (13)
PDF page: 6
Claim: The source computes a Smith normal form of an arbitrary stabilizer generator matrix and omits the resulting zero columns to form a generator matrix with a minimal number of columns.

## Minimal-generator independence [paper_fact]
Fact ID: hostens0408190-minimal-generator-independence
Source locator: PDF p. 6, Sec. V.A, Eq. (14)
PDF page: 6
Claim: Eq. (14) states that if \(\sum_k r_kS_k=0\pmod d\) for a minimal generator matrix, then each \(r_kS_k=0\pmod d\).

## Minimal-generator phase condition [paper_fact]
Fact ID: hostens0408190-minimal-generator-phase
Source locator: PDF p. 6, Sec. V.A, Eq. (15)
PDF page: 6
Claim: Eq. (15) requires \((r_k-1)r_kS_k^TUS_k+r_kf_k=0\pmod{2d}\) for each \(r_k\in\mathbb Z_d\) satisfying \(r_kS_k=0\pmod d\).

## Stabilizer canonical form [paper_fact]
Fact ID: hostens0408190-canonical-form
Source locator: PDF p. 7, Theorem 1(i), Eq. (16)
PDF page: 7
Claim: A configuration-space transform and generator change put an arbitrary stabilizer description into the block form \(S'=[Q;B]\pmod d\), where \(Q\) is pseudo-diagonal in Smith normal form and \(Q^TB\) is symmetric modulo \(d\).

## Stabilizer standard-basis expansion [paper_fact]
Fact ID: hostens0408190-basis-expansion
Source locator: PDF p. 7, Theorem 1(ii), Eqs. (17)--(18)
PDF page: 7
Claim: The standard-basis expansion is, up to normalization, a sum over \(t\in\mathbb Z_d^n\) of basis states \(\lvert T(\bar Qt+x^*)\rangle\) weighted by the quadratic phase \(\zeta^{t^TMt+p^Tt}\), with \(x^*\) defined by \(B^Tx=y\pmod q\).

## Unique affine offset [paper_fact]
Fact ID: hostens0408190-unique-offset
Source locator: PDF pp. 8--9, Appendix B, Eq. (B1) through final solution paragraph
PDF page: 8
Claim: Appendix B proves that Eq. (18) has a unique solution \(x^*\) in \(G_{\bar q}=\mathbb Z_{q_1}\times\cdots\times\mathbb Z_{q_n}\) and gives a Smith-normal procedure for finding it.

## Smith normal form over the modular ring [paper_fact]
Fact ID: hostens0408190-smith-form
Source locator: PDF p. 8, Appendix A, opening paragraph
PDF page: 8
Claim: Appendix A defines Smith normal form over the principal ideal ring \(\mathbb Z_d\) using invertible left and right transformations and diagonal entries ordered by divisibility.

## Non-field graph-state limitation [paper_fact]
Fact ID: hostens0408190-graph-state-limitation
Source locator: PDF p. 1, Introduction, graph-state discussion
PDF page: 1
Claim: When the one-qudit configuration space is not a field, the source says that not all stabilizer states are graph-state equivalent unless an additional condition is imposed.

## Odd-d Pauli representation [paper_fact]
Fact ID: hostens0408190-odd-pauli
Source locator: PDF p. 9, Appendix C, opening paragraphs and Eq. (C1)
PDF page: 9
Claim: Because \(2^{-1}=(d+1)/2\) exists modulo odd \(d\), the odd-d Pauli representation uses phases \(\omega^\delta\) with \(\delta\in\mathbb Z_d\), and Eq. (C1) gives its multiplication law.

## Odd-d Clifford conjugation [paper_fact]
Fact ID: hostens0408190-odd-clifford-conjugation
Source locator: PDF p. 9, Appendix C, Eq. (C2) and following paragraph
PDF page: 9
Claim: For odd \(d\), a Clifford is represented by symplectic \(C\) and \(g=h/2\in\mathbb Z_d^{2n}\), Eq. (C2) gives the Pauli conjugation update modulo \(d\), and the source says there is no further restriction on \(g\).

## Odd-d Clifford composition [paper_fact]
Fact ID: hostens0408190-odd-clifford-composition
Source locator: PDF p. 9, Appendix C, Eq. (C3)
PDF page: 9
Claim: For odd \(d\), Eq. (C3) gives the composition update \(C''=C'C\pmod d\) and its phase-vector update \(g''\pmod d\).

## Odd-d Clifford inverse [paper_fact]
Fact ID: hostens0408190-odd-clifford-inverse
Source locator: PDF p. 9, Appendix C, Eq. (C4)
PDF page: 9
Claim: For odd \(d\), Eq. (C4) represents the inverse Clifford by \(C'=C^{-1}=-PC^TP\pmod d\) and the printed inverse phase vector \(g'\pmod d\).

## Odd-d stabilizer phase condition [paper_fact]
Fact ID: hostens0408190-odd-stabilizer-phase
Source locator: PDF p. 9, Appendix C, Eq. (C5)
PDF page: 9
Claim: Eq. (C5) gives the modulo-\(d\) phase condition on every \(r\in\mathbb Z_d^m\) satisfying \(Sr=0\pmod d\) for an odd-\(d\) stabilizer.

## Odd-d stabilizer generator change [paper_fact]
Fact ID: hostens0408190-odd-stabilizer-generator-change
Source locator: PDF p. 10, Appendix C, Eq. (C6)
PDF page: 10
Claim: Eq. (C6) gives the modulo-\(d\) generator and phase updates under an invertible stabilizer generator change for odd \(d\).

## Odd-d Clifford stabilizer update [paper_fact]
Fact ID: hostens0408190-odd-stabilizer-clifford-update
Source locator: PDF p. 10, Appendix C, Eq. (C7)
PDF page: 10
Claim: Eq. (C7) sends an odd-\(d\) stabilizer generator matrix to \(S'=CS\pmod d\) and gives the corresponding phase-vector update \(b'\pmod d\).

## Odd-d standard-basis expansion [paper_fact]
Fact ID: hostens0408190-odd-basis-expansion
Source locator: PDF p. 10, Appendix C, Eq. (C8)
PDF page: 10
Claim: Eq. (C8) expresses an odd-\(d\) stabilizer state as a standard-basis sum weighted by the modulo-\(d\) quadratic phase \(\omega^{t^TMt+p^Tt}\).

## Printed conclusion complexity [paper_fact]
Fact ID: hostens0408190-conclusion-complexity
Source locator: PDF p. 8, Sec. VI, Conclusion
PDF page: 8
Claim: The Conclusion prints that an \(n\)-qudit Clifford operation can be decomposed in \(O(n^2)\) one- and two-qudit operations.

## Artifact date discrepancy [literature_gap]
Fact ID: hostens0408190-gap-date-discrepancy
Source locator: PDF p. 1, title date and arXiv footer
PDF page: 1
Claim: The source does not reconcile its printed October 23, 2018 title-page date with the visible `arXiv:quant-ph/0408190v2 22 Feb 2005` footer.
Gap scope: source_local

## Qubit-versus-qudit terminology [literature_gap]
Fact ID: hostens0408190-gap-qubit-wording
Source locator: PDF pp. 2--3, Introduction final paragraph and Sec. III opening
PDF page: 2
Claim: The source does not explain why these two arbitrary-dimensional decomposition passages say “one and two-qubit Clifford operations” while Sec. IV and the Conclusion describe one- and two-qudit operations.
Gap scope: source_local

## Decomposition-complexity discrepancy [literature_gap]
Fact ID: hostens0408190-gap-complexity
Source locator: PDF p. 6, Sec. IV final paragraph, and PDF p. 8, Conclusion
PDF page: 6
Claim: The source does not reconcile the \(O(n^2\log d)\) count printed at the end of Sec. IV with the \(O(n^2)\) count printed in the Conclusion.
Gap scope: source_local

## Minimal-column count anomaly [literature_gap]
Fact ID: hostens0408190-gap-column-count
Source locator: PDF p. 6, Sec. V.A, paragraph after Eq. (13)
PDF page: 6
Claim: After beginning with \(m'\) generators and obtaining a minimal count \(m\), the source prints that the rightmost \(m-m'\) columns are zero and does not resolve the resulting negative-count expression when \(m\le m'\).
Gap scope: source_local

## Prime-factor terminology precision [literature_gap]
Fact ID: hostens0408190-gap-prime-wording
Source locator: PDF p. 6, Sec. V.A, paragraph before Eq. (11)
PDF page: 6
Claim: The source does not define the phrases “only single prime factors” and “multiple prime factors” used for its stabilizer-generator count cases.
Gap scope: source_local

## Appendix-B index mismatch [literature_gap]
Fact ID: hostens0408190-gap-appendix-index
Source locator: PDF p. 8, Appendix B, paragraph after Eq. (B1)
PDF page: 8
Claim: The paragraph formulates the condition with quantities indexed by \(j\) but ends with “for every \(k=1,\ldots,m\),” without explaining the index change.
Gap scope: source_local

## No stabilizer measurement update [literature_gap]
Fact ID: hostens0408190-gap-measurement-update
Source locator: PDF p. 8, Sec. VI, Conclusion and documented full-text scope
PDF page: 8
Claim: This source does not give a stabilizer update rule for selective or nonselective measurement.
Gap scope: source_local

## No Born branch probabilities [literature_gap]
Fact ID: hostens0408190-gap-born-probabilities
Source locator: PDF p. 8, Sec. VI, Conclusion and documented full-text scope
PDF page: 8
Claim: This source does not define measurement outcomes, Born branch masses, or normalized conditional post-measurement states.
Gap scope: source_local

## No reset map [literature_gap]
Fact ID: hostens0408190-gap-reset
Source locator: PDF p. 8, Sec. VI, Conclusion and documented full-text scope
PDF page: 8
Claim: This source does not define a reset operation, reset-conditioned state update, or reset error model.
Gap scope: source_local

## No trajectory histories [literature_gap]
Fact ID: hostens0408190-gap-histories
Source locator: PDF p. 8, Sec. VI, Conclusion and documented full-text scope
PDF page: 8
Claim: This source does not define repeated-cycle outcome histories or a probability law on raw histories.
Gap scope: source_local

## No emitted Record [literature_gap]
Fact ID: hostens0408190-gap-record
Source locator: PDF p. 8, Sec. VI, Conclusion and documented full-text scope
PDF page: 8
Claim: This source does not define an emitted classical Record, a detector fold, conditional fidelity, or Record total variation.
Gap scope: source_local

## No leakage mechanism [literature_gap]
Fact ID: hostens0408190-gap-leakage
Source locator: PDF p. 2, Sec. II.A, Eq. (1), and PDF p. 8, Conclusion
PDF page: 2
Claim: Although the source treats arbitrary \(d\), it does not partition the \(d\)-level Hilbert space into computational and leakage sectors or define leakage, seepage, return, or leakage measurement.
Gap scope: source_local

## No physical noise channel [literature_gap]
Fact ID: hostens0408190-gap-noise-channel
Source locator: PDF p. 1, Introduction, motivation paragraph, and PDF p. 8, Conclusion
PDF page: 1
Claim: This source does not define a stochastic or open-system physical noise channel for the qudits.
Gap scope: source_local

## No PEPS or CAPEPS construction [literature_gap]
Fact ID: hostens0408190-gap-peps
Source locator: PDF p. 8, Sec. VI, Conclusion and documented full-text scope
PDF page: 8
Claim: This source does not provide an MPS, PEPS, Clifford-augmented PEPS, CAPEPS construction, tensor-network contraction rule, or tensor-network benchmark.
Gap scope: source_local

## No error-correction resource result [literature_gap]
Fact ID: hostens0408190-gap-resources
Source locator: PDF p. 1, Introduction, motivation paragraph
PDF page: 1
Claim: This source does not report a code threshold, decoder result, syndrome-circuit benchmark, detector model, circuit-noise study, or matched time and memory comparison for quantum error correction.
Gap scope: source_local

## No qutrit ninety-class quotient [literature_gap]
Fact ID: hostens0408190-gap-qutrit-quotient
Source locator: PDF p. 3, Sec. III opening, and documented full-text scope
PDF page: 3
Claim: This source does not derive a qutrit-specific 90-class entanglement quotient, classify double-sided local equivalence, or enumerate executable representatives for such classes.
Gap scope: source_local

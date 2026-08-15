+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1606.06301"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1606.06301v2"
source_artifact = "docs/papers/1606.06301v2.pdf"
source_sha256 = "bc240a9b78a84e886360d4d0a621a0b06b12fef93e4e399c6b9aa1f66d1e43c3"
title = "Approximating local observables on projected entangled pair states"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/SCHWARZ_1606_06301V2_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "c026c1be8bbdcb101531a624c0e84d56400c229d5c4ca70166314d858adbb609"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_schwarz_1606_source_rereview_2026_07_27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7]

[[relations]]
predicate = "supports"
object_id = "schwarz-conditional-local-observable-approximation"
object_type = "theorem"
object_label = "conditional local-observable approximation"
fact_id = "schwarz1606-theorem-error-object"

[[relations]]
predicate = "uses"
object_id = "schwarz-injectivity-after-constant-blocking"
object_type = "model"
object_label = "injectivity after constant blocking"
fact_id = "schwarz1606-injectivity"

[[relations]]
predicate = "uses"
object_id = "schwarz-uniform-prefix-parent-gap"
object_type = "model"
object_label = "uniformly gapped parent Hamiltonian"
fact_id = "schwarz1606-uniform-prefix-gap"

[[relations]]
predicate = "derives"
object_id = "schwarz-exact-finite-patch-contraction"
object_type = "method"
object_label = "exact finite-patch contraction"
fact_id = "schwarz1606-exact-patch-contraction"

[[relations]]
predicate = "limits"
object_id = "schwarz-standard-ltqo"
object_type = "limitation"
object_label = "standard local topological quantum order"
fact_id = "schwarz1606-ltqo-variant-only"

[[relations]]
predicate = "supports"
object_id = "schwarz-conditional-line-transfer-gap"
object_type = "theorem"
object_label = "conditional line-transfer-operator gap"
fact_id = "schwarz1606-transfer-gap"
+++
# Full-text review — Schwarz, Buerschaper, and Eisert, arXiv:1606.06301v2

## Source identity [paper_fact]
Fact ID: schwarz1606-source-identity
Source locator: PDF page 1, title, author block, and arXiv version line
PDF page: 1
Claim: The reviewed source is the seven-page arXiv:1606.06301v2 preprint by M. Schwarz, O. Buerschaper, and J. Eisert titled “Approximating local observables on projected entangled pair states.”

The version line is dated 29 August 2016. The source contains a four-page main
text, references, and a three-page appendix with the detailed proof, hardness
discussion, quantum-computer discussion, and transfer-operator argument.

## Selection scope [paper_fact]
Fact ID: schwarz1606-selection-scope
Source locator: PDF page 1, Abstract and final two paragraphs of the Introduction
PDF page: 1
Claim: The source studies approximation of local PEPS expectation values for a restricted class associated with uniformly gapped parent Hamiltonians rather than efficient contraction of arbitrary PEPS.

The introduction retains the worst-case #P-completeness of general
two-dimensional PEPS contraction as the problem boundary.

## Weak PEPS conjecture [paper_fact]
Fact ID: schwarz1606-weak-peps-conjecture
Source locator: PDF page 2, Conjecture 1
PDF page: 2
Claim: Conjecture 1 proposes that each constant-support observable of a unique gapped ground state can be approximated within additive error \(\epsilon\) by a PEPS of bond dimension polynomial in \(N\) and \(\epsilon^{-1}\).

The conjecture is stated per local observable. The nearby global trace-norm and
relative-entropy statements are part of the preceding one-dimensional MPS
discussion, not the printed higher-dimensional conjecture.

## Strong PEPS conjecture [paper_fact]
Fact ID: schwarz1606-strong-peps-conjecture
Source locator: PDF page 2, Conjecture 2
PDF page: 2
Claim: Conjecture 2 additionally asks the approximating PEPS to be injective and its parent Hamiltonian to have a constant spectral gap while retaining the local-observable approximation.

This is a conjectured existence statement, not the proved contraction theorem.

## Theorem input class [paper_fact]
Fact ID: schwarz1606-theorem-input-class
Source locator: PDF page 2, Theorem 1 opening sentence
PDF page: 2
Claim: Theorem 1 assumes an unnormalised injective PEPS on a constant-dimensional lattice of \(N\) finite-dimensional spins with bond dimension \(D\), uniformly gapped parent Hamiltonian, and local tensor collection \(\{A_i\}\).

The phrase “uniformly gapped” is defined later on PDF page 3 as a condition on
an entire prefix family of parent Hamiltonians.

## Theorem condition number [paper_fact]
Fact ID: schwarz1606-condition-number
Source locator: PDF page 2, Theorem 1 definition of \(\kappa_*\)
PDF page: 2
Claim: Theorem 1 defines \(\kappa_* = \max_i\kappa(A_i)\) as the upper bound on the local-tensor condition numbers entering its radius and error estimates.

The source does not state that this quantity is gauge- or
representation-independent.

## Theorem observable support [paper_fact]
Fact ID: schwarz1606-observable-support
Source locator: PDF page 3, Theorem 1 continuation and following paragraph
PDF page: 3
Claim: The theorem restricts \(O_X\) to fewer than a constant number \(k\) of sites but allows \(X\) to be disconnected, including fixed-order correlation observables.

## Theorem error object [paper_fact]
Fact ID: schwarz1606-theorem-error-object
Source locator: PDF page 2, Theorem 1 displayed inequality
PDF page: 2
Claim: The conditional local-observable approximation controls the additive absolute error in one normalized scalar expectation \(\langle\omega|O_X|\omega\rangle/\langle\omega|\omega\rangle\).

The displayed guarantee is not a norm bound between global states.

## Theorem patch radius [paper_fact]
Fact ID: schwarz1606-patch-radius
Source locator: PDF page 2, Theorem 1 Eq. (1)
PDF page: 2
Claim: Equation (1) chooses \(\ell\in O((2\ln\kappa_*+\ln\epsilon^{-1}+\ln\|O_X\|)/\Delta_*)\) as a sufficient patch radius.

The formula retains explicit dependence on the parent-gap lower bound,
condition number, target error, and observable norm.

## PEPS local-map representation [paper_fact]
Fact ID: schwarz1606-peps-map-representation
Source locator: PDF page 3, Preliminaries Eq. (2) and preceding definition of \(A_v\)
PDF page: 3
Claim: Equation (2) represents the PEPS as local virtual-to-physical maps applied to maximally entangled virtual pairs, \(|\psi\rangle=\bigotimes_{v\in V}A_v\bigotimes_{e\in E}|\phi_e\rangle\).

## Injectivity after constant blocking [paper_fact]
Fact ID: schwarz1606-injectivity
Source locator: PDF page 3, Preliminaries paragraph following Eq. (2)
PDF page: 3
Claim: The source defines injectivity after constant blocking by requiring every resulting local PEPS map \(A_v\) to have a Moore–Penrose left inverse satisfying \(A_v^{-1}A_v=I\).

The proof assumes the PEPS has already been blocked so that individual local
maps are left-invertible.

## Uniformly gapped prefix parent Hamiltonians [paper_fact]
Fact ID: schwarz1606-uniform-prefix-gap
Source locator: PDF page 3, Preliminaries final paragraph before “Proof sketch of Theorem 1”
PDF page: 3
Claim: A uniformly gapped parent Hamiltonian is defined by requiring every prefix/sub-PEPS parent Hamiltonian \(H_t\) to satisfy \(\Delta_t\geq\Delta_*\) for all \(0\leq t\leq N\).

This is stronger than requiring only the terminal parent Hamiltonian
\(H_N=H_*\) to be gapped.

## Prefix-state sequence [paper_fact]
Fact ID: schwarz1606-prefix-sequence
Source locator: PDF page 5, Appendix Eq. (8) and following paragraph
PDF page: 5
Claim: The proof orders the tensors into normalized prefix states \(|\omega_i\rangle=A_i\cdots A_1|\phi\rangle^{\otimes n}/\|A_i\cdots A_1|\phi\rangle^{\otimes n}\|\), with the last \(N_b=O(\ell^{d-1})\) tensors forming a boundary around \(X\).

The boundary is placed at graph-theoretical distance \(\ell\).

## Prefix exponential-clustering step [paper_fact]
Fact ID: schwarz1606-prefix-clustering
Source locator: PDF page 5, Appendix Eq. (9) and preceding paragraph
PDF page: 5
Claim: The source applies exponential clustering separately to every prefix Hamiltonian \(H_i\), using the common gap lower bound \(\Delta_*\), to bound the connected correlation of \(O_X\) with a boundary operator \(O_i\).

The displayed upper bound is
\(e^{-O(\ell\Delta_*)}\|O_X\|\|O_i\|\).

## One-tensor inverse removal [paper_fact]
Fact ID: schwarz1606-one-tensor-removal
Source locator: PDF page 6, Appendix Eqs. (10)–(13)
PDF page: 6
Claim: Choosing \(O_i=(A_i^{-1})^\dagger A_i^{-1}\) and normalizing the inverse-mapped state bounds one boundary-removal step by \(e^{-O(\ell\Delta_*)}\|O_X\|\kappa(A_i)^2\).

The condition number enters squared after the source divides by the inverse-map
expectation.

## Accumulated boundary error [paper_fact]
Fact ID: schwarz1606-boundary-error
Source locator: PDF page 6, Appendix Eq. (14)
PDF page: 6
Claim: Summing the boundary-removal steps gives the additive scalar bound \(\ell^{d-1}e^{-O(\ell\Delta_*)}\kappa_*^2\|O_X\|\) between the final PEPS expectation and the boundary-removed expectation.

## Radius selected from the accumulated error [paper_fact]
Fact ID: schwarz1606-radius-from-error
Source locator: PDF page 6, Appendix Eq. (15) and following paragraph
PDF page: 6
Claim: Equation (15) repeats the logarithmic radius choice and states that \(\ell=O(\log N)\) suffices when dimension and gap are constant and \(\kappa_*\), \(\epsilon^{-1}\), and \(\|O_X\|\) scale polynomially in \(N\).

## Patch–remainder factorization [paper_fact]
Fact ID: schwarz1606-patch-factorization
Source locator: PDF page 6, Appendix Eqs. (16)–(17)
PDF page: 6
Claim: After the boundary tensors are removed, the normalized state factorizes exactly as \(|\omega_*\rangle=|\omega_R\rangle\otimes|\omega_P\rangle\).

## Patch-only normalized expectation [paper_fact]
Fact ID: schwarz1606-patch-expectation
Source locator: PDF page 6, Appendix Eq. (18) and following paragraph
PDF page: 6
Claim: Because \(O_X\) acts only on the patch and the remainder has unit norm, Eq. (18) reduces the target to a normalized patch expectation without computing the global PEPS norm.

## Exact finite-patch contraction [paper_fact]
Fact ID: schwarz1606-exact-patch-contraction
Source locator: PDF page 6, Appendix paragraph following Eq. (18)
PDF page: 6
Claim: The source obtains its classical estimate by exact finite-patch contraction with printed cost \((Dd)^{O(\ell^d)}\).

This is exact summation over the sufficient patch, not an approximate boundary
environment or finite-bond compression algorithm.

## Reported classical scaling [paper_fact]
Fact ID: schwarz1606-classical-scaling
Source locator: PDF page 3, Theorem 1 continuation paragraph
PDF page: 3
Claim: The source reports quasi-polynomial deterministic time in the controlled polynomial-parameter regime and separately reports polynomial system-size scaling for the one-dimensional MPS case.

The printed complexity uses one symbol \(d\) for two different dimensions;
that ambiguity is retained below.

## Quantum patch preparation [paper_fact]
Fact ID: schwarz1606-quantum-patch-preparation
Source locator: PDF page 7, Appendix “Discussion of the computation of expectation values on a quantum computer”
PDF page: 7
Claim: Invoking the external method of Ref. 32, the source states that a patch of \(O(\ell^d)\) spins can be prepared within trace-distance error \(\epsilon\) in time \(O(\ell^d\operatorname{polylog}(\ell/\epsilon))\) and polylogarithmic depth.

The preparation algorithm is cited rather than re-proved in this paper.

## Quantum sampling count [paper_fact]
Fact ID: schwarz1606-quantum-sampling
Source locator: PDF page 7, Appendix quantum-computer discussion Chernoff sentence
PDF page: 7
Claim: The source states that \(O(1/\epsilon^2)\) independent preparations and measurements suffice to estimate \(\langle O_X\rangle\) to additive error \(\epsilon\) with constant error probability.

The missing observable-range dependence is retained as a source-local gap
below.

## Reported quantum cost [paper_fact]
Fact ID: schwarz1606-quantum-cost
Source locator: PDF page 7, final sentence of the quantum-computer discussion and Theorem 1 on page 2
PDF page: 7
Claim: The source reports total quantum time \(\widetilde O(\ell^d/\epsilon^2)\) and depth \(O(\operatorname{polylog}(\ell/\epsilon))\) for estimating the one local expectation.

## Standard LTQO is not established [paper_fact]
Fact ID: schwarz1606-ltqo-variant-only
Source locator: PDF page 4, paragraph “Injective PEPS with uniformly gapped parent Hamiltonians satisfy a variant of local topological quantum order”
PDF page: 4
Claim: The source explicitly says its proof does not establish standard local topological quantum order because it adds boundary terms to enforce a unique ground state, and instead claims only a unique-ground-state variant.

## Transfer-operator assumptions [paper_fact]
Fact ID: schwarz1606-transfer-assumptions
Source locator: PDF page 7, Appendix opening paragraph of “Implications for the gap of the transfer operator”
PDF page: 7
Claim: The transfer-operator argument assumes Conjecture 2, all assumptions of Theorem 1, translational invariance, and a one-dimensional line obtained after contracting the rest of the cubic lattice.

## Induced line transfer operator [paper_fact]
Fact ID: schwarz1606-line-transfer-operator
Source locator: PDF page 7, Appendix Eqs. (19)–(21)
PDF page: 7
Claim: Equations (19)–(21) define the site transfer operator, the induced one-dimensional line transfer operator, and the two-point correlation computed from it.

## Conditional line-transfer-operator gap [paper_fact]
Fact ID: schwarz1606-transfer-gap
Source locator: PDF page 7, Appendix Eqs. (22)–(24)
PDF page: 7
Claim: Under the extra transfer-section assumptions and the printed exponential-correlation bound, the source derives the conditional line-transfer-operator gap inequality \(\lambda_2/\lambda_1\leq e^{-c_2\delta}\).

The undefined \(\delta\), injectivity-direction wording, and spectral-expansion
assumption are preserved as separate gaps below.

## Hardness boundary [paper_fact]
Fact ID: schwarz1606-hardness-boundary
Source locator: PDF page 6, Appendix “Hardness of tensor network contraction”
PDF page: 6
Claim: The source distinguishes its restricted theorem from general PEPS hardness by excluding the projective hard construction through injectivity and a constant uniform parent-Hamiltonian gap.

The argument cites the general contraction hardness result of Ref. 27.

## Overloaded dimension symbol [literature_gap]
Fact ID: schwarz1606-gap-overloaded-d
Source locator: PDF page 3, Theorem 1 continuation and Preliminaries
PDF page: 3
Claim: The source uses \(d\) for both lattice dimension and physical spin dimension, leaving the two roles conflated in \((Dd)^{O(\ell^d)}\).
Gap scope: source_local

## Hidden constants in the exponential bound [literature_gap]
Fact ID: schwarz1606-gap-hidden-clustering-constants
Source locator: PDF page 6, Eqs. (9)–(14), with main-text Eqs. (3)–(5) on pages 3–4
PDF page: 6
Claim: The source does not expose the positive decay constants or prefactors hidden by \(e^{-O(\ell\Delta_*)}\), so the asymptotic clustering expression is not a directly executable numerical error certificate.
Gap scope: source_local

## Uncontrolled injective-approximation sentence [literature_gap]
Fact ID: schwarz1606-gap-noninjective-closeness
Source locator: PDF page 3, Preliminaries injectivity paragraph
PDF page: 3
Claim: The sentence that any non-injective PEPS is \(\epsilon\)-close to an injective one supplies no norm, construction, prefix-gap bound, or condition-number bound that would extend Theorem 1.
Gap scope: source_local

## Constant-time wording omits bond dimension [literature_gap]
Fact ID: schwarz1606-gap-constant-time-d
Source locator: PDF page 3, paragraph continuing Theorem 1
PDF page: 3
Claim: The printed constant-deterministic-time summary fixes \(d\), \(\Delta_*\), \(\kappa_*\), and \(\epsilon\) but does not also state the bounded-\(D\) condition required by the theorem's displayed runtime.
Gap scope: source_local

## Main-text equation cross-references [literature_gap]
Fact ID: schwarz1606-gap-equation-crossrefs
Source locator: PDF page 4, main-text patch-factorization discussion following Eq. (7)
PDF page: 4
Claim: The main text refers to Eqs. (17) and (18) beside displayed formulas numbered (6) and (7), while those numbers appear only when the formulas are repeated in the appendix.
Gap scope: source_local

## Quantum patch-size inconsistency [literature_gap]
Fact ID: schwarz1606-gap-quantum-patch-size
Source locator: PDF page 7, final sentence of the quantum-computer discussion
PDF page: 7
Claim: After obtaining \(\ell=O(\log N)\), the source prints \(\ell^d=O(\log N)\) for the patch spin count without stating an additional restriction or altered radius choice.
Gap scope: source_local

## Quantum sampling observable scale [literature_gap]
Fact ID: schwarz1606-gap-quantum-observable-norm
Source locator: PDF page 7, quantum-computer discussion Chernoff sentence
PDF page: 7
Claim: The source states an \(O(1/\epsilon^2)\) sample count without a range, variance, or \(\|O_X\|^2\) factor despite allowing a general-norm observable in Theorem 1.
Gap scope: source_local

## Reversed transfer-injectivity wording [literature_gap]
Fact ID: schwarz1606-gap-transfer-injectivity-direction
Source locator: PDF page 7, opening and penultimate paragraphs of the transfer-operator discussion
PDF page: 7
Claim: The transfer section first says MPS injectivity is inherited by the PEPS but later uses MPS injectivity as inherited from PEPS injectivity, without reconciling the directions.
Gap scope: source_local

## Undefined transfer decay symbol [literature_gap]
Fact ID: schwarz1606-gap-transfer-delta
Source locator: PDF page 7, Eqs. (22) and (24)
PDF page: 7
Claim: The transfer-operator section does not define \(\delta\), leaving the quantitative relation between the printed decay exponent and the parent-Hamiltonian gap incomplete.
Gap scope: source_local

## Transfer spectral expansion assumption [literature_gap]
Fact ID: schwarz1606-gap-transfer-diagonalizability
Source locator: PDF page 7, Eq. (23) and preceding sentence
PDF page: 7
Claim: The source uses a simple left/right eigenvector expansion of the transfer operator without treating non-diagonalizable operators or Jordan blocks.
Gap scope: source_local

## Generic non-injective PEPS [literature_gap]
Fact ID: schwarz1606-gap-generic-noninjective
Source locator: PDF page 4, Conclusion final paragraph, with exclusions on pages 2–3
PDF page: 4
Claim: The source does not establish its contraction theorem for generic non-injective or G-injective PEPS and leaves the G-injective extension as future work.
Gap scope: source_local

## Intrinsic topological PEPS [literature_gap]
Fact ID: schwarz1606-gap-topological-peps
Source locator: PDF page 2, paragraph after Conjecture 2
PDF page: 2
Claim: The source states that its conjectures do not capture non-unique ground states or intrinsic topological order and supplies no topological-sector contraction theorem.
Gap scope: source_local

## Global state fidelity [literature_gap]
Fact ID: schwarz1606-gap-global-fidelity
Source locator: PDF page 2, Conjecture 1 discussion and Theorem 1
PDF page: 2
Claim: The source does not establish a global trace-distance or fidelity guarantee for higher-dimensional PEPS, controlling only local expectation values in its conjecture and theorem.
Gap scope: source_local

## Outcome-resolved measurement branches [literature_gap]
Fact ID: schwarz1606-gap-measurement-branches
Source locator: PDF page 7, quantum-computer discussion through end of complete full text
PDF page: 7
Claim: The source does not define outcome-resolved Born branch masses, conditional post-measurement states, or branch-completeness conservation.
Gap scope: source_local

Its quantum discussion uses independent preparations and measurements only to
estimate one expectation value.

## Reset instrument [literature_gap]
Fact ID: schwarz1606-gap-reset-instrument
Source locator: PDF page 7, end of complete full text following Eq. (24)
PDF page: 7
Claim: The source does not define a reset operation, post-reset state invariant, or measurement–reset transaction.
Gap scope: source_local

## Multi-time measurement Record [literature_gap]
Fact ID: schwarz1606-gap-record-law
Source locator: PDF page 7, end of complete full text following Eq. (24)
PDF page: 7
Claim: The source does not define a raw multi-round outcome law, temporal detector fold, logical-observable bits, or a distance between complete measurement Records.
Gap scope: source_local

## Finite-bond numerical PEPS truncation [literature_gap]
Fact ID: schwarz1606-gap-finite-bond-truncation
Source locator: PDF page 6, exact-patch contraction paragraph following Eq. (18), with Conclusion on page 4
PDF page: 6
Claim: The source does not provide a finite-bond environment truncation rule or an error bound for approximate numerical PEPS contraction, because its sufficient finite patch is contracted exactly.
Gap scope: source_local

## Clifford-augmented PEPS efficiency [literature_gap]
Fact ID: schwarz1606-gap-capeps-efficiency
Source locator: PDF page 7, end of complete full text following Eq. (24)
PDF page: 7
Claim: The source does not define a Clifford-augmented PEPS method or compare its accuracy, runtime, bond dimensions, or memory with full PEPS.
Gap scope: source_local

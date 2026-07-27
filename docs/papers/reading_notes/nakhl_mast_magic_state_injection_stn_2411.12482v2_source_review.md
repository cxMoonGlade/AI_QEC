+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2411.12482"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2411.12482v2"
source_artifact = "docs/papers/2411.12482v2.pdf"
source_sha256 = "86de97a1ac18ac9c98272e5180e222115c0590d5cd0759a1eb7fd829ab81eaee"
title = "Stabilizer Tensor Networks with Magic State Injection"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/NAKHL_HARPER_MAST_2411_12482V2_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "5db0b9d8eec2ce4d08d05effb6f9085f2f3d1a480f6142b6bedfb346a8a05deb"
admission_status = "draft_pending_review"
admission_reviewer = "pending_independent_source_only_review"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]

[[relations]]
predicate = "uses"
object_id = "mast-stabilizer-basis-coefficient-mps"
object_type = "model"
object_label = "coefficient MPS"
fact_id = "mast2411-stn-representation"

[[relations]]
predicate = "uses"
object_id = "mast-magic-state-injection"
object_type = "method"
object_label = "magic-state injection"
fact_id = "mast2411-injection-deferral"

[[relations]]
predicate = "supports"
object_id = "mast-random-t-doped-clifford-regime"
object_type = "method"
object_label = "polynomial MAST cost"
fact_id = "mast2411-random-complexity"

[[relations]]
predicate = "limits"
object_id = "mast-general-probability-sampling"
object_type = "limitation"
object_label = "sampling from the probability distribution"
fact_id = "mast2411-sampling-boundary"

[[relations]]
predicate = "limits"
object_id = "mast-projection-order-independence"
object_type = "limitation"
object_label = "projection order"
fact_id = "mast2411-path-dependence"

[[relations]]
predicate = "uses"
object_id = "mast-hidden-bit-shift-benchmark"
object_type = "method"
object_label = "Hidden Bit Shift circuit"
fact_id = "mast2411-hidden-bit-shift"

[[relations]]
predicate = "limits"
object_id = "mast-camps-equivalence"
object_type = "limitation"
object_label = "CAMPS protocol"
fact_id = "mast2411-camps-distinction"
+++
# Full-text review — Nakhl et al., “Stabilizer Tensor Networks with Magic State Injection”

## Source identity [paper_fact]
Fact ID: mast2411-source-identity
Source locator: PDF page 1, title block, author block, visible date, and arXiv margin stamp
PDF page: 1
Claim: The reviewed source is the twelve-page arXiv:2411.12482v2 preprint “Stabilizer Tensor Networks with Magic State Injection” by Nakhl and six coauthors, with a visible April 16, 2025 title-page date.

The margin stamp identifies arXiv v2 and is dated 15 April 2025. This source
artifact is a preprint; a journal artifact is not included in this review.

## Source selection scope [paper_fact]
Fact ID: mast2411-selection-scope
Source locator: PDF page 1, Abstract and Introduction
PDF page: 1
Claim: The source augments Stabilizer Tensor Networks with magic-state injection and benchmarks the resulting MAST method on random \(T\)-doped Clifford circuits and Hidden Bit Shift circuits.

The source's cost observable is primarily the maximum bond dimension of the
coefficient MPS, with runtime also reported for part of the Hidden Bit Shift
study.

## Stabilizer-basis coefficient representation [paper_fact]
Fact ID: mast2411-stn-representation
Source locator: PDF page 1, Eq. (1); PDF page 7, Eqs. (B1)--(B2) and surrounding Appendix B opening
PDF page: 1
Claim: The intended STN representation writes \(\lvert\psi\rangle=\sum_i\nu_iD_{\hat i}\lvert\phi\rangle\), with \(\lvert\phi\rangle\) stored as a stabilizer tableau and the coefficients \(\nu_i\) stored as a coefficient MPS over binary basis labels.

The source says the basis operators are defined with respect to the
destabilizer tableau. A conflicting literal description in Eq. (B2) is
recorded separately below.

## Clifford basis update [paper_fact]
Fact ID: mast2411-clifford-update
Source locator: PDF page 7, Appendix B.1, displayed conjugation derivation following Eq. (B2)
PDF page: 7
Claim: A Clifford operation conjugates the stabilizer-basis tableau while leaving the coefficient MPS unchanged.

The source presents this as the cheap update in the hybrid representation.

## Pauli/tableau decomposition of a non-Clifford operation [paper_fact]
Fact ID: mast2411-nonclifford-decomposition
Source locator: PDF pages 7--8, Appendix B.2, Eqs. (B3)--(B6)
PDF page: 7
Claim: The source decomposes a non-Clifford operator as \(U=\sum_i c_iD_{\hat d_i}S_{\hat s_i}\) and maps its action to phase-weighted shifts of the coefficient labels.

The binary destabilizer and stabilizer row labels are obtained by testing
Pauli anticommutation with tableau rows and retaining the associated phase.

## Two-term coefficient-MPS rotation [paper_fact]
Fact ID: mast2411-two-term-rotation
Source locator: PDF page 8, Appendix B.2, Eqs. (B7)--(B9)
PDF page: 8
Claim: For a two-term decomposition, the source factors one Pauli term as a tableau-compatible operation and rewrites the remaining action as a multi-qubit controlled rotation on the coefficient MPS.

The source says decompositions with more than two terms may be treated
recursively, but does not further analyze general multi-qubit non-Clifford
operators because its chosen gate constructions use Cliffords and arbitrary
\(Z\) rotations with two-term decompositions.

## Pauli expectation value [paper_fact]
Fact ID: mast2411-pauli-expectation
Source locator: PDF page 8, Appendix B.3
PDF page: 8
Claim: For a Pauli observable \(O=\alpha D_{\hat a}S_{\hat b}\), the source maps the expectation calculation to coefficient-MPS Pauli operations and states that local expectations are polynomial-time when the MPS is canonical.

This statement concerns expectation values, not complete output-distribution
sampling.

## Intended selective projection [paper_fact]
Fact ID: mast2411-selective-projection
Source locator: PDF page 8, Appendix B.4, projector sentence and Eqs. (B10)--(B11)
PDF page: 8
Claim: Appendix B.4 states that a selected Pauli-measurement outcome applies \((I+pO)/2\), then applies a coefficient-MPS projector-like operation, performs the standard stabilizer-tableau measurement update, and renormalizes the MPS.

The source calls this projection computationally complex because the
coefficient operation resembles the controlled rotation used for
non-Clifford gates. Printed defects in the coefficient formula are retained
as source-local gaps below.

## Magic-state-injection deferral [paper_fact]
Fact ID: mast2411-injection-deferral
Source locator: PDF page 2, Fig. 1 and “Magic State Injected Stabilizer Tensor Networks” section
PDF page: 2
Claim: MAST replaces a non-Clifford gate by magic-state injection, simulates magic-state preparation and the resulting Clifford circuit, predetermines the injection measurement outcome, and delays the actual projection until the end of the circuit.

Figure 1 shows the \(T\)-gate gadget with a measured magic ancilla and an
outcome-dependent Clifford \(S\) correction.

## Random-circuit ensemble and complexity claim [paper_fact]
Fact ID: mast2411-random-complexity
Source locator: PDF pages 1--2, Abstract and Results A opening through the Appendix C synopsis
PDF page: 2
Claim: For the defined ensemble of uniformly random \(N\)-qubit Clifford layers followed by one \(T\) gate per layer, the source claims polynomial MAST cost on average when the number \(t\) of \(T\) gates satisfies \(t\lesssim N\).

The argument associates cost with the final magic-register projections and
the location of the first tableau row that anticommutes with the projected
observable. It is an ensemble-conditioned statement rather than a
worst-case claim for arbitrary circuits.

## Three reported bond-growth regions [paper_fact]
Fact ID: mast2411-three-regions
Source locator: PDF page 3, Fig. 2 and caption
PDF page: 3
Claim: Figure 2 reports maximum coefficient-MPS bond dimension averaged over 1000 random instances, with MAST average bond bounded by three for \(t\lesssim N\), exponential growth for \(N\lesssim t\lesssim1.5N\), and maximal \(\chi=2^{N/2}\) beyond the transition.

The plotted axes are scaled by the number of data qubits and exclude MAST
ancillas. The caption says the \(N=200\) simulations stop at \(N+10\) layers
because of exponential bond growth.

## Output-sampling boundary [paper_fact]
Fact ID: mast2411-sampling-boundary
Source locator: PDF page 3, Results A, paragraphs following Fig. 2
PDF page: 3
Claim: The source states that MAST permits efficient local expectation values in the reported regime but does not admit efficient general sampling from the probability distribution, giving an \(O(\exp(w))\) dependence on the number \(w\) of sampled bits when \(t<N\).

It further says that sampling need not increase the bond dimension for a
low-entanglement final state such as the Hidden Bit Shift output, but does
not generalize that observation to arbitrary outputs.

## Projection-order and decomposition dependence [paper_fact]
Fact ID: mast2411-path-dependence
Source locator: PDF page 4, final random-circuit paragraphs and Conclusion and Outlook
PDF page: 4
Claim: The source states that MAST does not universally find the minimum simulation cost, that the cost can depend on projection order, and that expensive-gate decompositions can materially change resource use.

For the particular \(U^\dagger U\) random-circuit test, pairwise projection
from the middle of the ancilla register outward keeps the reported MPS bond
at most two because the induced CNOT cascades cancel in pairs.

## Hidden Bit Shift benchmark [paper_fact]
Fact ID: mast2411-hidden-bit-shift
Source locator: PDF page 4, Fig. 3 and Results B
PDF page: 4
Claim: The source reports MAST simulations of the Hidden Bit Shift circuit up to 4000 qubits and 320 \(T\) gates and observes lower MAST bond dimension when the qubit count is increased at fixed non-Clifford resource count.

Figure 3 uses a four-\(T\) CCZ decomposition with ancillas and reports maximum
coefficient-MPS bond rather than state fidelity or output-distribution error.

## CCZ-decomposition benchmark [paper_fact]
Fact ID: mast2411-ccz-decomposition-benchmark
Source locator: PDF pages 10--12, Appendices D--E and Figs. 6--8
PDF page: 12
Claim: The source compares a four-\(T\), two-ancilla Toffoli/CCZ decomposition with a seven-\(T\), no-extra-ancilla decomposition and reports that MAST runtime is nearly decomposition-indifferent while STN runtime changes substantially.

Figure 8(a) is for \(N=40\); the caption says the simulations ran on dual
2.45 GHz AMD EPYC processors and that each point averages 10,000 shots.

## Distinction from CAMPS [paper_fact]
Fact ID: mast2411-camps-distinction
Source locator: PDF page 4, Conclusion and Outlook, paragraph beginning “Recently, a similar observation”
PDF page: 4
Claim: The source describes the cited CAMPS protocol as a different stabilizer--tensor-network amalgamation and states that the CAMPS-based method requires an optimization subroutine whereas MAST does not.

The source uses the name CAMPS in this comparison and does not use the term
GCAMPS.

## Reported implementation pointer [paper_fact]
Fact ID: mast2411-code-pointer
Source locator: PDF pages 5--6, Data Availability and Ref. [54]
PDF page: 5
Claim: The source points to a GitHub repository named “Magic State Injection Augmented Stabilizer Tensor Networks” as the implementation used for its numerical simulations.

The paper does not pin a commit in the reference; this source-only review did
not inspect or authenticate the repository.

## Binary basis-index convention is unresolved [literature_gap]
Fact ID: mast2411-gap-basis-index
Source locator: PDF page 7, Eqs. (A2) and (B1), together with the binary-label definition preceding Eq. (A2)
PDF page: 7
Claim: The source does not reconcile its \(i=1,\ldots,2^N\) summation convention with the statement that \(i\) is the decimal value of an \(N\)-bit string, which ordinarily includes zero and ends at \(2^N-1\).
Gap scope: source_local

This prevents the printed bounds from serving as a literal binary-label
enumeration without an unstated relabeling.

## Destabilizer basis generator is mislabeled [literature_gap]
Fact ID: mast2411-gap-b2-generator
Source locator: PDF page 7, Eq. (B2) and its following sentence, compared with Eq. (1) and the Appendix A destabilizer paragraph
PDF page: 7
Claim: Equation (B2) calls \(\phi_j\) a row of the stabilizer tableau even though the surrounding representation requires \(D_{\hat i}\) to be generated from destabilizer rows, so the printed definition is not self-consistent.
Gap scope: source_local

Products of stabilizers acting on the stabilized state cannot supply the
distinct coefficient basis that the same appendix claims to span the Hilbert
space.

## Projection coefficient and label operation are undefined [literature_gap]
Fact ID: mast2411-gap-b10
Source locator: PDF page 8, Eq. (B10)
PDF page: 8
Claim: Equation (B10) replaces the state amplitudes \(\nu_i\) by \(c_i\) and uses the unintroduced coefficient label \(D_{\hat i\cdot\hat b}\), so its displayed coefficient update cannot be replayed literally from the preceding definitions.
Gap scope: source_local

The physical projector \((I+pO)/2\) remains stated, but the printed
coefficient expansion is not an implementation-complete rule.

## Projection helper label is undefined [literature_gap]
Fact ID: mast2411-gap-b11
Source locator: PDF page 8, Eq. (B11) and following definition of \(k\)
PDF page: 8
Claim: Equation (B11) contains \(D_{\hat n}\) without defining \(\hat n\), while the prose defines only the row index \(k\), so the coefficient-MPS projector is not fully specified as printed.
Gap scope: source_local

The source additionally says to renormalize the MPS but does not retain the
pre-normalization norm as an outcome probability or branch mass.

## Appendix-C projection prefactor is inconsistent [literature_gap]
Fact ID: mast2411-gap-c1-c2-prefactor
Source locator: PDF page 9, Eqs. (C1)--(C2)
PDF page: 9
Claim: Equation (C1) identifies the operation with \(\lvert0\rangle\langle0\rvert_k\mathcal R\), but Eq. (C2) replaces that projector by a term carrying \(1/(4\sqrt2)\), which is inconsistent with \(\lvert0\rangle\langle0\rvert=(I+Z)/2\) and the preceding definition of \(\mathcal R\).
Gap scope: source_local

The subsequent scalar cancellation therefore cannot be used as a literal
normalization proof.

## Finite-size tableau probability uses inconsistent dimensions [literature_gap]
Fact ID: mast2411-gap-c3-dimension
Source locator: PDF page 10, Appendix C.2 and Eq. (C3)
PDF page: 10
Claim: The finite-\(n\) probability argument begins from \(\mathrm{Sp}(2n,\mathbb F_2)\), then counts vectors in \(\mathbb F_2^n\) and later writes \(\mathrm{Sp}(n;\mathbb F_2)\), so the printed formula \(2^{n-1}/(2^n-1)\) has no consistent stated dimension convention.
Gap scope: source_local

The source's asymptotic use of a probability approaching one half does not
resolve the exact finite-size notation.

## Figure 8 caption misidentifies the second decomposition [literature_gap]
Fact ID: mast2411-gap-figure8-caption
Source locator: PDF page 12, Fig. 8 caption, compared with the legend, Appendix E, and Fig. 7
PDF page: 12
Claim: The Fig. 8 caption calls the no-extra-ancilla case a four-\(T\) decomposition even though the plot legend and surrounding appendix identify it as the seven-\(T\) decomposition.
Gap scope: source_local

The reported comparison is interpreted from the plot legend and Appendix E,
not from that caption phrase.

## No reset or complete outcome-history law [literature_gap]
Fact ID: mast2411-gap-reset-record
Source locator: PDF page 2, MAST injection section; PDF page 8, Appendix B.4; documented full-text boundary
PDF page: 8
Claim: This source does not specify reset, ordered raw measurement histories, Born branch or prefix masses, repeated-round detector Records, logical-observable folds, or a complete classical outcome law.
Gap scope: source_local

Its measurement content is a selected projective primitive and a deferred
magic-injection projection, not a measurement--reset instrument.

## No PEPS residual [literature_gap]
Fact ID: mast2411-gap-peps
Source locator: PDF pages 1--4 and 7--10, complete method and results scope
PDF page: 1
Claim: This source does not define or execute a PEPS coefficient state, a \(C\lvert\mathrm{PEPS}\rangle\) residual, a two-dimensional local update, or a PEPS environment and truncation rule.
Gap scope: source_local

The concrete tensor network throughout the source is an MPS.

## No syndrome-circuit correctness benchmark [literature_gap]
Fact ID: mast2411-gap-qec-correctness
Source locator: PDF pages 2--4, complete benchmark scope
PDF page: 4
Claim: This source does not simulate syndrome extraction, XZZX checks, repeated quantum-error-correction rounds, or conditional-state and Record correctness against an independent dense reference.
Gap scope: source_local

Magic-state injection is motivated as a fault-tolerant computation tool, but
the reported circuits are random \(T\)-doped Clifford and Hidden Bit Shift
benchmarks.

## No matched full-tensor-network efficiency comparison [literature_gap]
Fact ID: mast2411-gap-matched-efficiency
Source locator: PDF pages 3--4 and 12, Figs. 2--3 and 8
PDF page: 3
Claim: This source does not report a matched-accuracy comparison of conditional fidelity, outcome-law distance, maximum bond, runtime, and peak memory against full MPS or PEPS and a Pauli-twirled tableau method on the same circuit.
Gap scope: source_local

Its reported comparisons are MAST versus STN on the paper's benchmark
families and do not include a full physical-state tensor-network baseline.

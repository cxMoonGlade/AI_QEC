+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2603.14670"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2603.14670v2"
source_artifact = "docs/papers/2603.14670.pdf"
source_sha256 = "a9cf8cf1278258eff34f3ee1518384856f0f6f313764a1d55840078106433e47"
title = "Computing logical error thresholds with the Pauli Frame Sparse Representation"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "not_attempted"
admission_status = "source_only_reviewed"
admission_reviewer = "assigned-source-review-pfsr-2026-08-02"
admission_date = "2026-08-02"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

[[relations]]
predicate = "defines"
object_id = "pauli-frame-sparse-representation"
object_type = "method"
object_label = "PFSR"
fact_id = "pfsr-represented-object"

[[relations]]
predicate = "uses"
object_id = "stabilizer-eigenbasis-orthonormality"
object_type = "property"
object_label = "orthonormal label basis"
fact_id = "pfsr-orthonormality"

[[relations]]
predicate = "derives"
object_id = "pfsr-projective-measurement"
object_type = "method"
object_label = "label deletion / frame change"
fact_id = "pfsr-measurement"

[[relations]]
predicate = "defines"
object_id = "amplitude-magnitude-truncation"
object_type = "method"
object_label = "|alpha_s| >= epsilon"
fact_id = "pfsr-truncation-by-magnitude"
+++

# Full-text review — Tuloup and Ayral, "Computing logical error thresholds with the Pauli Frame Sparse Representation"

All equation numbers below were read off rendered PDF pages, not off the extracted
`.txt`. Extraction hazard recorded: `docs/papers/2603.14670.txt` is of type `data`
(plain `grep` returns nothing; `grep -a` is required), and even with `-a` the phrase
"stabilizer rank" returns zero hits because the extractor broke it across a line
("stabilizer\nrank", txt line 69) while the phrase is plainly printed on PDF page 1.
Phrase-level greps on this artifact are unsafe.

## Source identity [paper_fact]
Fact ID: pfsr-source-identity
Source locator: Title block and arXiv stamp in the left margin, which prints
"arXiv:2603.14670v2 [quant-ph] 9 Apr 2026"
PDF page: 1
Claim: The reviewed fixed source is the 24-page preprint arXiv:2603.14670v2 by Thomas
Tuloup (Eviden Quantum Lab) and Thomas Ayral (CPHT, CNRS, Ecole Polytechnique),
dated 9 Apr 2026. Pages 1-19 are main text (Secs. I-VII); Appendix A spans pages 19-20
and Appendix B spans pages 20-21; the bibliography begins mid-page on page 21 and runs
to page 24. Pages 1-21 were rendered and read visually; pages 22-24 are bibliography
only and were checked from the extracted text.

The retrieval provenance recorded `source_version_date = null` with status
"verify-from-primary-source". This record pins the date from the rendered page-1
arXiv stamp.

## Represented object [paper_fact]
Fact ID: pfsr-represented-object
Source locator: Sec. II A Eqs. (1)-(3), Sec. II B Eqs. (4)-(5), Sec. II C 1 Eq. (6),
Sec. II D Eqs. (10)-(11), Sec. III A Eqs. (13), (15)
PDF pages: 2, 3, 4
Claim: The represented object is a sparse superposition over the common eigenbasis of
a running set of n mutually commuting independent Paulis. As printed:
Eq. (1) `S = {S_0, S_1, ..., S_{n-1}} subset P_n`, called the *stabilizer frame*;
Eq. (2) `s = (s_0, s_1, ..., s_{n-1}) in {0,1}^n`;
Eq. (3) `S_i |s> = (-1)^{s_i} |s>`;
Eq. (4) `|Psi> = sum_{s in I} alpha_s |s>` with `I subset {0,1}^n`;
Eq. (6) `|s> = P_s |0>`;
Eq. (10) `PFSR(|Psi>) = (S, {(s, alpha_s, P_s)}_{s in I})`;
Eq. (11) `|Psi> = sum_{s in I} alpha_s P_s |0>`.

## Reference state is a general stabilizer state, not specifically a code state [paper_fact]
Fact ID: pfsr-reference-state
Source locator: Sec. II B Eq. (5), Sec. III A Eqs. (13) and (15), Sec. IV A
PDF pages: 2, 4, 10
Claim: The reference `|0>` (bold in the source) is defined in Eq. (13) as "the
reference stabilizer eigenstate (+1 eigenstate of all stabilizers S_i)". It is
*initialized* to the computational product state — Eq. (5) prints
`|Psi_0> = |0>^{tensor n}, S_0 = {Z_0, Z_1, ..., Z_{n-1}}, I_0 = {0}, alpha_0 = 1` —
and is thereafter Clifford-transported, Eq. (15) `|0>' = C|0>`, with the frame updated
by Eq. (16) `S' = {C S_i C^dagger}`. So the reference is a *general stabilizer state*
carried by the frame, not a fixed `|0^n>` and not by definition a code state.

Refinement: in the surface-code application the frame *becomes* the code's. Sec. IV A
(PDF page 10) prints that the logical qubit "is initialized either in the logical
`|0>_L` state, corresponding to the +1 eigenstate of all Z-type stabilizers and of the
logical operator Z_L, or in the logical `|+>_L` state". The design intent is stated on
PDF page 1 — the representation "is tailored to quantum error correction: this
representation is the most economical for states that are supposed to be preserved by
the error correction process, namely the states that are stabilized by the code" — and
again in the Sec. II opening paragraph (PDF page 2) on the code space. So: general
stabilizer reference by construction, code-state reference in the QEC application,
explicitly motivated.

## Orthonormality of the label basis is stated and used [paper_fact]
Fact ID: pfsr-orthonormality
Source locator: Sec. II A text below Eq. (1); Sec. III B 1 text below Eq. (17);
Sec. III C text under "Computing expectation values"
PDF pages: 2, 4, 6
Claim: The source states that the frame defines a complete labelled eigenbasis and
then explicitly invokes its orthonormality. PDF page 2 prints: "S is a compact way to
define a common eigenbasis `{|s>}_{s in {0,1}^n}` — called the stabilizer eigenbasis —
on which we shall decompose our state." PDF page 4 repeats "a stabilizer frame
`S = {S_0, ..., S_{n-1}}` defining the common eigenbasis `{|s>}_{s in {0,1}^n}` with
`S_i |s> = (-1)^{s_i} |s>`". PDF page 6 prints: "Then we can simply take the scalar
product `<Psi|Psi'>` taking advantage of the orthonormality of the basis, and computing
the relative phases as described in Sec. II C 2."

This is a labelled orthonormal basis of size 2^n indexed by `s in {0,1}^n`, with
`|s> = P_s|0>` — i.e. the Pauli orbit of the stabilizer reference, one label per Pauli
coset mod S. It is *not* a stabilizer-rank decomposition, and the source draws that
contrast itself on PDF page 1: "Expansions in T gates using stabilizer rank [16, 17]
are exponential in the number of T gates, and limited to non-Clifford gates that are
diagonal in the computational basis."

The source does not print the coset-counting statement (`4^n / 2^n = 2^n`) as such;
it states the equivalent structural facts (Eqs. (2), (3), (6) and "common eigenbasis").

## Phase ambiguity and Pauli histories [paper_fact]
Fact ID: pfsr-pauli-histories
Source locator: Sec. II C 1 (above Eq. (6)); Sec. II C 2 Eqs. (7)-(9)
PDF pages: 2, 3
Claim: The source records that "a stabilizer basis element `|s>` is only defined up to
a phase", which is why each populated label carries a *Pauli history* `P_s` with
`|s> = P_s|0>` (Eq. (6)). Relative phases between two histories with the same label are
resolved by Eqs. (7)-(9): Eq. (7) `e^{i phi_12} = <s|_1 |s>_2 = <0| (P_s^{(1)})^dagger
P_s^{(2)} |0>`, Eq. (8) `(P_s^{(1)})^dagger P_s^{(2)} = gamma prod_{i in A} S_i`, and
Eq. (9) `e^{i phi_12} = gamma`.

## Projective measurement: label deletion in the commuting case [paper_fact]
Fact ID: pfsr-measurement
Source locator: Sec. III C 1, Eqs. (32)-(35); Sec. III C 2, Eqs. (36)-(39)
PDF pages: 6, 7
Claim: Equation numbers verified as printed. Eq. (32) `P = gamma prod_{i in A} S_i`;
Eq. (33) defines the indicator `chi_pm(s) = 1 if P(P_s|0>) = pm(P_s|0>), 0 otherwise`;
Eq. (34) `Pi_pm |Psi> = sum_{s in I} alpha_s chi_pm(s) P_s |0>`; Eq. (35) gives
`p_pm = sum_{s in I} |alpha_s|^2 chi_pm(s)` and
`|Psi_pm> = (1/sqrt(p_pm)) sum_{s in I} alpha_s chi_pm(s) P_s |0>`.

The sentence immediately after Eq. (35), quoted verbatim from PDF page 6, right
column: "In practice, this means that the projection is applied by simply deleting the
labels **s** for which chi_pm(**s**) = 0, and renormalizing the projected state by
multiplying all coefficients by a factor 1/sqrt(p_pm)". The claimed phrase is
substantively accurate; the full printed sentence includes the renormalization clause.

## Measurement does not require the observable to be in the frame, and never grows support [paper_fact]
Fact ID: pfsr-measurement-scope
Source locator: Sec. III C, case split at "1. If P commutes with all stabilizer
generators" / "2. If P anticommutes with at least one stabilizer generator";
Sec. III C 2 Eqs. (36)-(39); Fig. 1(e) and its caption
PDF pages: 6, 7, 9
Claim: The label-deletion rule (Eqs. (32)-(35)) is *only* the commuting branch. The
source explicitly handles the anticommuting branch: PDF page 7 prints "simply applying
the projector Pi_pm as an operator would increase the number of populated basis
eigenstates, which we wish to avoid. Therefore, we apply Pi_pm by changing the
stabilizer frame, keeping the same number of populated basis eigenstates." The frame
update is Eq. (36) and the Pauli-history update is Eq. (37), with the required Clifford
U constructed in Appendix A. Therefore the source does **not** require the measured
observable to lie in the reference's stabilizer group.

In both branches measurement never increases the sparse-vector size. The Fig. 1
caption (PDF page 9) prints that in the commuting case projection "will on average
divide the size of the sparse vector by two", and in the anticommuting case "The size
of the sparse vector will usually stay the same, up to merging of some Pauli
histories." Measurement is *support-non-increasing*, but it is not computationally
free in the anticommuting branch: it requires a Gaussian elimination on the symplectic
representation (Appendix A, Eqs. (A1)-(A3), PDF page 19).

## DECISIVE: coherent noise is a SINGLE-QUBIT Z rotation only [paper_fact]
Fact ID: pfsr-coherent-noise-single-qubit
Source locator: Sec. III D 3 "Coherent noise", Eq. (43); Fig. 6 caption; Fig. 11
caption; Appendix B 2 Eq. (B2)
PDF pages: 9, 13, 16, 21
Claim: Eq. (43) is verified as printed on PDF page 9 and reads
`E(rho) = e^{-i (theta/2) Z} rho e^{i (theta/2) Z}`,
introduced by the sentence "In this work, the coherent noise we will study is a
rotation along the Z-axis of a small angle theta". This is a **one-qubit** generator.
Fig. 6 (PDF page 13) is captioned "for coherent noise R_Z(theta)"; Fig. 11 (PDF page
16) is captioned "against unitary coherent noise R_Z(theta) at the circuit level".
Appendix B 2 decomposes the same channel as Eq. (B2) `E = q_I I + q_Z Z + q_S S`, again
single-qubit.

The source studies **no two-qubit coherent generator**. Searches over the extracted
text (with `grep -a`) return: "crosstalk" 0, "cross-talk" 0, "RZZ" 0, "coupling" 0.
Every one of the 20 "ZZ" hits is either a Bell-state stabilizer generator
(`S = {XX, ZZ}` in the running worked example) or the extractor gluing the channel
coefficient `q_Z` to the channel `Z` in Eqs. (B1)/(B2). The three "two-qubit" hits are
two-qubit *gates* (CNOTs) and a gate-count table row, not two-qubit noise generators.
Sec. IV C (PDF page 13) prints that at the circuit level "single- and two-qubit gates
undergo local error channels" — i.e. the noise following a CNOT is still a local
channel, and correlated data errors enter only as propagated ('hook') faults, which the
source then suppresses by "the standard CNOT orderings that prevent hook errors from
reducing the effective code distance".

## DECISIVE: truncation is by AMPLITUDE MAGNITUDE, not by perturbative order [paper_fact]
Fact ID: pfsr-truncation-by-magnitude
Source locator: Sec. IV C 2, whose printed heading is "2. Truncation of small-amplitude
terms"; Eqs. (49)-(50)
PDF pages: 14, 15
Claim: Equation numbers verified as printed on PDF page 15.
Eq. (49) `I_{>= epsilon} = {s in I : |alpha_s| >= epsilon}`;
Eq. (50) `|Psi'> = sum_{s in I_{>= epsilon}} (alpha_s / sqrt(nu)) P_s |0>` with
`nu = sum_{s in I_{>= epsilon}} |alpha_s|^2`.
The introducing sentence prints: "we remove from the sparse vector any basis component
whose amplitude absolute value falls below a fixed threshold epsilon > 0 and
renormalize the retained state." The source adds: "This truncation process is similar
in spirit to what is done in Pauli propagation methods [51, 52]."

The truncation is therefore by **amplitude magnitude against a fixed numerical
cutoff**. It is not by bond dimension (the source has no tensor network and no bond
dimension) and it is not by perturbative order. `grep -a` over the extracted text
returns 0 hits for "perturbat" and 0 for "leading order"; the single "leading-order"
hit is in the Conclusion (PDF page 19), where it describes what PTA discards
("the PFSR retains the leading-order coherent contributions that are suppressed by
Pauli-twirled approximations"), not a graded representation.

The nearest thing to an order statement is the PTA comparison on PDF page 12: a
coherent Z rotation "has a trace-infidelity that scales as 1 - F approx theta^2, but
its action on off-diagaonal density-matrix elements is linear in theta. In contrast,
the PTA replaces the coherent rotation by a probabilistic Z-flip with probability
p_z = theta^2/4 + O(theta^4), whose effect on the state is therefore quadratic in theta
at all orders." (The misspelling "off-diagaonal" is as printed.) This is an argument
about why PTA fails; the source never organizes `I` by theta-order and never truncates
by order.

## Approximation-error control is empirical convergence testing only [paper_fact]
Fact ID: pfsr-error-control
Source locator: Sec. IV C 2 following Eq. (50); Fig. 9 and Fig. 10 with captions;
Sec. IV C 3
PDF pages: 15
Claim: There is no a-priori bound and no accumulated discarded-weight budget. The
printed procedure is: "We choose epsilon by empirical convergence testing.
Specifically, for distance d = 5 we computed logical error vs physical error curves for
a range of truncation cutoffs epsilon. As shown in Fig. 9 the resulting logical-error
curves closely overlap for a wide window of 0 < epsilon < 10^{-4}, indicating that the
truncation has negligible effect on the extracted threshold in that regime." The
production runs use `epsilon = 10^{-4}`.

The retained weight `nu` of Eq. (50) is computed, but only as a renormalization factor;
the source does not report, accumulate, or bound `1 - nu` as an error estimate. The
source does record where the control fails: "For d = 9, the onset of deviation between
PFSR curves and expected scaling behavior suggests that the truncation threshold begins
to limit accuracy."

## DECISIVE: no distinguishability quantity is computed anywhere [literature_gap]
Fact ID: pfsr-no-distinguishability
Source locator: Complete source scope, PDF pages 1-21 (Secs. I-VII, Appendices A-B)
PDF page: 1
Claim: The source computes **logical error rate** and **threshold**, and no
distinguishability or state-discrimination quantity. Counts from `grep -a` over the
extracted text, each context checked:
- "trace distance" 0; "density operator" 0; "partial trace" 0; "mixed state" 0;
  "subsystem" 0; "diamond" 0.
- "density matrix" 2, both the boilerplate "acts on the density matrix as" introducing
  the depolarizing channel Eq. (40) and the amplitude-damping channel Eq. (41)
  (PDF page 8). A third, hyphenated occurrence "off-diagaonal density-matrix elements"
  is on PDF page 12 in the PTA argument.
- "reduced" 2, being "a reduced basis" (PDF page 2, meaning the frame-adapted basis)
  and "is reduced by several orders of magnitude" (PDF page 17, about estimator
  variance). Neither is a reduced density matrix.
- "fidelity" 3: "the same average fidelity as the exact amplitude-damping channel"
  (PDF page 12), "trace-infidelity that scales as 1 - F approx theta^2" (PDF page 12),
  and "measurements have finite fidelity" (PDF page 13, hardware description).

The whole simulation is state-vector / trajectory based: Sec. III D (PDF page 8) prints
"our simulation is based on a sparse representation of the state vector and not the
density matrix", with noise applied stochastically by Monte-Carlo sampling over Kraus
draws. There is no mixed state to take a distance between.
Gap scope: source_local

## No non-Markovianity content [literature_gap]
Fact ID: pfsr-no-non-markovianity
Source locator: Complete source scope, PDF pages 1-21
PDF page: 1
Claim: `grep -a` returns 0 hits for "Markov", "non-Markov", "backflow", and "divisib".
The source makes no statement about divisibility, information backflow, or any
non-Markovianity witness.
Gap scope: source_local

## Benchmark systems and sizes [paper_fact]
Fact ID: pfsr-benchmarks
Source locator: Abstract; Sec. IV A Eqs. (44)-(45); Figs. 4, 5, 6, 8, 9, 10, 11;
Sec. V and Table I; Figs. 12-13
PDF pages: 1, 10, 12, 13, 14, 15, 16, 18
Claim: The benchmark code is the `[[L^2, 1, L]]` rotated surface code (Sec. IV A, Eq.
(44) for the face stabilizers, Eq. (45) for the string logicals). Sizes as printed:
- Phenomenological level, amplitude damping: d = 3, 5, 7, 9, 11 (Fig. 5), thresholds
  `gamma_exact approx gamma_PTA approx 0.072`.
- Phenomenological level, coherent R_Z: d = 3, 5, 7, 9, 11 (Fig. 6), thresholds
  `t_exact approx 0.024` vs `t_PTA approx 0.028`.
- Circuit level, depolarizing (schedule validation against Stim): d = 3, 5, 7, 9
  (Fig. 8), `t_parallel approx 0.0053` vs `t_layered approx 0.0050`.
- **Circuit level, coherent R_Z: d = 3, 5, 7, 9** (Sec. IV C 3 prints "for distances
  d = 3, 5, 7, and 9"; Fig. 11), `t_PFSR approx 0.0009` vs `t_PTA approx 0.0034` —
  the "factor of about 4" overestimate of the abstract.
- Fig. 4 separately reports maximum PFSR size out to distance ~25 for phenomenological
  amplitude damping at gamma = 0.15, scaling as `O(2^{d^2/2})` empirically versus the
  `O(2^d)` bound argued on PDF page 11.
- Sec. V: magic-state cultivation (Gidney's protocol) at d = 3 and d = 5, with
  importance sampling over fault number, Eqs. (51)-(55).

Verdict on the claim "rotated surface code, d = 3,5,7,9, circuit-level coherent
noise": **verified as printed**, with the noise being single-qubit R_Z(theta).

## Tractability rests on scheduling, not on order structure [paper_fact]
Fact ID: pfsr-layered-schedule
Source locator: Sec. IV B 1 "Layered approach to noise application" and Fig. 3;
Sec. IV C 1 "Layered approach at the circuit level" and Fig. 7
PDF pages: 11, 13, 14
Claim: The support-growth control is a *scheduling* device: noise is applied to small
local clusters and each stabilizer is measured as soon as all its qubits have been
"noisified", so that projection compresses the vector before branching spreads. At the
phenomenological level the source states this "introduces no approximation" because
"the order of noise and stabilizer measurements is irrelevant to the overall channel".
At the circuit level the schedule is serial ancilla-by-ancilla and *is* a deviation
from the optimal parallel schedule, validated only empirically against Stim on the
depolarizing model (threshold difference `3 x 10^{-4}`, Fig. 8).

## What the source does not do [literature_gap]
Fact ID: pfsr-boundary
Source locator: Complete source scope, PDF pages 1-21
PDF page: 1
Claim: Reading the full source, it does not: (a) study any two-qubit coherent
generator, crosstalk, or correlated coherent noise; (b) organize the amplitude vector
by perturbative order in the rotation angle, or truncate by order; (c) compute any
trace distance, fidelity between two evolved states, reduced density matrix, or any
other distinguishability functional; (d) discuss non-Markovianity, divisibility, or
information backflow; (e) provide any a-priori or a-posteriori approximation-error
bound, or accumulate discarded weight.
Gap scope: source_local

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2605.29514"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2605.29514v1"
source_artifact = "docs/papers/2605.29514v1.pdf"
source_sha256 = "c13096aa841acf2b2161f18140c56dd9d3549b268969f79328ff0865583a35dd"
title = "Non-Clifford Crosstalk Noise in Surface Codes Using Hybrid Stabilizer-Tensor Network Methods"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/HARPER_2605_29514_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "e8731498a5efc2e8288826cebf4c85e7357fc569d2ba9256bfc8610048adc48d"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_harper_2605_source_rereview_round2_2026_07_27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7]

[[relations]]
predicate = "uses"
object_id = "harper-rotated-surface-code-syndrome-extraction"
object_type = "method"
object_label = "rotated-surface-code syndrome extraction"
fact_id = "harper2605-repeated-syndrome-extraction"

[[relations]]
predicate = "defines"
object_id = "harper-gate-based-coherent-zz-crosstalk"
object_type = "model"
object_label = "coherent ZZ crosstalk channel"
fact_id = "harper2605-coherent-zz-channel"

[[relations]]
predicate = "defines"
object_id = "harper-zz-pauli-twirl"
object_type = "model"
object_label = "Pauli-twirled crosstalk channel"
fact_id = "harper2605-pauli-twirl"

[[relations]]
predicate = "uses"
object_id = "harper-hybrid-clifford-mps-state"
object_type = "model"
object_label = "Clifford–MPS hybrid state"
fact_id = "harper2605-hybrid-state"

[[relations]]
predicate = "uses"
object_id = "harper-projective-measurement-pullthrough"
object_type = "method"
object_label = "projective-measurement Pauli sum"
fact_id = "harper2605-projective-measurement"

[[relations]]
predicate = "limits"
object_id = "harper-clifford-optimizer-cost"
object_type = "limitation"
object_label = "Clifford-optimization cost"
fact_id = "harper2605-no-clifford-optimization"

[[relations]]
predicate = "limits"
object_id = "harper-mps-truncation-bias"
object_type = "limitation"
object_label = "downward logical-error bias"
fact_id = "harper2605-truncation-bias"

[[relations]]
predicate = "measures"
object_id = "harper-coherent-versus-twirled-crosstalk"
object_type = "observable"
object_label = "sub-threshold logical error"
fact_id = "harper2605-coherent-twirled-result"

[[relations]]
predicate = "limits"
object_id = "harper-peps-future-layout"
object_type = "limitation"
object_label = "PEPS layout"
fact_id = "harper2605-peps-future-work"
+++
# Full-text review — Harper et al., arXiv:2605.29514v1

## Source identity [paper_fact]
Fact ID: harper2605-source-identity
Source locator: Title page, arXiv version line, and author block
PDF page: 1
Claim: The reviewed source is the eight-page arXiv:2605.29514v1 preprint by Ben Harper, Azar C. Nakhl, Martin Sevior, and Muhammad Usman on coherent crosstalk in surface-code syndrome extraction.

The version stamp is 28 May 2026. The paper contains six figures and describes
a forward classical simulation rather than an inference or calibration method.

## Abstract threshold wording [paper_fact]
Fact ID: harper2605-abstract-threshold-wording
Source locator: PDF page 1, Abstract, final sentences
PDF page: 1
Claim: The abstract states without the later Sec. V qualification that including coherent crosstalk reduces the surface-code threshold and substantially increases sub-threshold logical error relative to a Pauli-twirled approximation.

## Repeated syndrome extraction [paper_fact]
Fact ID: harper2605-repeated-syndrome-extraction
Source locator: Sec. II, first paragraph
PDF page: 2
Claim: The source simulates rotated-surface-code syndrome extraction repeated for \(d\) rounds, using face ancillas to measure local \(X\)- and \(Z\)-type checks.

## Syndrome-extraction circuit [paper_fact]
Fact ID: harper2605-syndrome-circuit
Source locator: Fig. 1 and caption
PDF page: 3
Claim: Figure 1 shows data qubits on square-lattice vertices, face ancillas prepared in \(\lvert0\rangle\), ordered CNOT extraction circuits for weight-four bulk checks, weight-two boundary checks, and ancilla measurement, with dashed post-CNOT crosstalk locations.

## Logical-error observable [paper_fact]
Fact ID: harper2605-logical-error-observable
Source locator: Sec. II, Eq. (1) and following paragraph
PDF page: 2
Claim: The source defines its coherent-noise logical-error observable as the sample average \(P_L=N^{-1}\sum_i|\sin(\theta_i/2)|\) over syndrome-conditioned logical rotation angles.

The paper identifies this quantity with an average diamond-norm distance from
the identity and says that it reduces to the standard logical-error rate when
each logical rotation angle is either zero or \(\pi\).

## Baseline gate, reset, and measurement error rates [paper_fact]
Fact ID: harper2605-error-rate-table
Source locator: Table I and Sec. III.A
PDF page: 2
Claim: The reported noise model sets single-qubit gate, two-qubit gate, reset, and measurement error rates to \(0.1p\), \(p\), \(2p\), and \(5p\), respectively, while fixing crosstalk angle \(\theta=10^{-3}\).

The paper varies \(p\) to locate a threshold. Table I is a parameter table; it
does not define an outcome-resolved reset instrument.

## Printed one-qubit depolarizing channel [paper_fact]
Fact ID: harper2605-one-qubit-depolarizing
Source locator: Sec. III.A, Eq. (2) and the sentence defining the Pauli-index set
PDF page: 2
Claim: Equation (2) prints \(\epsilon_1(\rho)=(1-p_1)\rho+(p_1/3)\sum_i\sigma_i\rho\sigma_i\), followed by a sentence that places \(i\) in \(\{I,X,Y,Z\}\).

## Printed two-qubit depolarizing channel [paper_fact]
Fact ID: harper2605-two-qubit-depolarizing
Source locator: Sec. III.A, Eq. (3) and the sentence defining the Pauli-index set
PDF page: 2
Claim: Equation (3) prints \(\epsilon_2(\rho)=(1-p_2)\rho+(p_2/15)\sum_{i,j}(\sigma_i\otimes\sigma_j)\rho(\sigma_i\otimes\sigma_j)\), with \((i,j)=(I,I)\) explicitly excluded.

## Coherent ZZ channel [paper_fact]
Fact ID: harper2605-coherent-zz-channel
Source locator: Sec. III.B, Eqs. (4)–(5), implementation circuit, and Fig. 1 caption
PDF page: 3
Claim: The source models gate-based nearest-neighbour noise as a coherent ZZ crosstalk channel \(e^{i\theta Z_1Z_2}\rho e^{-i\theta Z_1Z_2}\) applied after entangling gates, with \(\theta=J_{ZZ}t_g\).

The source separately prints a CNOT--\(R_Z(\theta/2)\)--CNOT circuit without
defining its \(R_Z\) convention. Under the common convention
\(R_Z(\varphi)=e^{-i\varphi Z/2}\), the circuit gives
\(e^{-i\theta Z_1Z_2/4}\), rather than the printed Eq. (4) unitary. The exact
relationship is preserved as a source-local gap below.

## Pauli-twirled crosstalk channel [paper_fact]
Fact ID: harper2605-pauli-twirl
Source locator: Sec. III.C, Eq. (6) and following paragraph
PDF page: 3
Claim: The source defines the Pauli-twirled crosstalk channel as \((1-\sin^2\theta)\rho+\sin^2\theta(Z\otimes Z)\rho(Z\otimes Z)\).

The paper describes Pauli twirling as projection of the channel's
Pauli-transfer matrix onto its diagonal and notes that it discards phase
information used by coherent interference across further evolution.

## Pauli-model decoder [paper_fact]
Fact ID: harper2605-pauli-decoder
Source locator: Sec. III.D
PDF page: 3
Claim: The source decodes every simulated arm with PyMatching using an error model generated from the Pauli-twirled approximation.

The forward coherent dynamics and the decoder model therefore have different
roles: coherence is retained in simulation, while the matching decoder uses a
Pauli error model.

## GCAMPS implementation identity [paper_fact]
Fact ID: harper2605-gcamps-identity
Source locator: Sec. IV opening paragraph
PDF page: 3
Claim: The source explicitly states that the reported coherent-noise surface-code simulations use the recently developed GCAMPS hybrid stabilizer--tensor-network simulation library.

## Clifford–MPS hybrid state [paper_fact]
Fact ID: harper2605-hybrid-state
Source locator: Sec. IV.A, Eq. (7)
PDF page: 4
Claim: The source represents an arbitrary simulated state as a Clifford–MPS hybrid state \(|\psi\rangle=C|\mathrm{MPS}\rangle\).

The tensor-network component is described as typically an MPS. The paper does
not instantiate a PEPS residual.

## Physical-qubit symbol in Fig. 2 [paper_fact]
Fact ID: harper2605-figure-qubit-symbol
Source locator: Fig. 2 caption
PDF page: 4
Claim: The Fig. 2 caption uses lowercase \(n\) for the number of physical qubits when locating the plotted central MPS cut.

## Physical Clifford update [paper_fact]
Fact ID: harper2605-clifford-update
Source locator: Sec. IV.A, displayed equations immediately following Eq. (7)
PDF page: 4
Claim: A physical Clifford gate \(G\) updates the leading Clifford as \(GC\) while leaving the MPS residual unchanged.

The displayed operation is \(G|\psi\rangle=GC|\mathrm{MPS}\rangle
=C'|\mathrm{MPS}\rangle\).

## Non-Clifford Pauli pull-through [paper_fact]
Fact ID: harper2605-nonclifford-pullthrough
Source locator: Sec. IV.A, non-Clifford displayed derivation
PDF page: 4
Claim: The source formally writes a non-Clifford operation as an unweighted displayed sum of Pauli terms, commutes those terms through \(C\), and applies the pulled-through Pauli sum to the MPS.

The prose calls the operation \(T\), while the displayed derivation uses \(U\).
No Pauli-expansion coefficients or stochastic branch rule are supplied, and
the derivation ends with \(C|\mathrm{MPS}'\rangle\).

## Local-to-high-weight transformation [paper_fact]
Fact ID: harper2605-local-to-high-weight
Source locator: Sec. IV.A, paragraph following the non-Clifford derivation
PDF page: 4
Claim: The source states that a physically local Pauli word can become a higher-weight nonlocal operation on the tensor network after transformation through \(C\).

The resulting weight depends on the entanglement represented by the leading
Clifford.

## Projective measurement pull-through [paper_fact]
Fact ID: harper2605-projective-measurement
Source locator: Sec. IV.A, projective-measurement paragraph
PDF page: 4
Claim: The source implements projective measurement by commuting a projective-measurement Pauli sum through \(C\) and applying it directly to the tensor network.

It further states that the non-Clifford error represented by the MPS collapses
to a Pauli error in the Clifford tableau when a measurement is made.

## Ideal-frame interpretation [paper_fact]
Fact ID: harper2605-qec-frame-interpretation
Source locator: Sec. IV.A, paragraph beginning “In the specific context”
PDF page: 4
Claim: In the source's QEC interpretation, \(C\) represents the ideal Clifford error-correction circuit and the MPS represents the non-Clifford perturbation of that ideal state.

Non-Clifford errors update the MPS and do not update the ideal Clifford
operator.

## Clifford optimization omitted [paper_fact]
Fact ID: harper2605-no-clifford-optimization
Source locator: Sec. IV.A, final paragraph
PDF page: 4
Claim: The source omits magic-state injection and Clifford optimization, stating that Clifford-optimization cost outweighed its MPS bond-dimension benefit for the reported circuits.

The magic-state route was also rejected because the large number of
non-Clifford gates would require many magic ancillas.

## MPS truncation rule [paper_fact]
Fact ID: harper2605-mps-truncation
Source locator: Sec. IV.B, Eq. (8) and following paragraph
PDF page: 5
Claim: The source limits MPS bond dimension \(\chi\) to \(\chi_{\max}\) and describes discarding the smallest-singular-value Schmidt terms across a cut.

Equation (8) prints a sum from 1 to \(\chi-1\), while the prose calls \(\chi\)
the bond dimension. Its cap uses uppercase \(N\), while Fig. 2 uses lowercase
\(n\) for physical-qubit count; the source does not reconcile the symbols.
The paper evaluates the central cut and compares logical-error results over
several bond caps.

## Downward logical-error bias [paper_fact]
Fact ID: harper2605-truncation-bias
Source locator: Sec. IV.B, paragraphs discussing Figs. 2–3
PDF page: 5
Claim: The source reports that aggressive MPS truncation creates a downward logical-error bias because the dominant residual component is the no-crosstalk state.

It consequently characterizes its logical-error results as lower bounds. The
argument is tied to the source's residual decomposition and logical observable,
not stated as a general state- or Record-distance theorem.

## Frozen MPS bond cap [paper_fact]
Fact ID: harper2605-bond-cap
Source locator: Sec. IV.B, final sentence
PDF page: 5
Claim: All result figures after the truncation study use maximum MPS bond dimension \(\chi_{\max}=32\).

The paper does not report a matched-accuracy full-MPS or PEPS resource arm.

## Results coupling parameters [paper_fact]
Fact ID: harper2605-results-coupling-parameters
Source locator: Sec. V.A, opening paragraph
PDF page: 5
Claim: The reported results section says that its simulations use \(J_{ZZ}=150\,\mathrm{kHz}\) and \(t_g=150\,\mathrm{ns}\).

## Coherent and Pauli-twirled result [paper_fact]
Fact ID: harper2605-coherent-twirled-result
Source locator: Sec. V.A, paragraphs preceding Fig. 4
PDF page: 5
Claim: For the reported workload, the source says that crosstalk lowers the threshold from about \(1\%\) to \(0.8\%\), while coherence further increases sub-threshold logical error without a statistically significant additional threshold shift.

Each data point is described as an average from \(10^5\) samples. This
detailed statement is narrower than the abstract's unqualified threshold
wording.

## Same-twirl distribution comparison [paper_fact]
Fact ID: harper2605-same-twirl-distributions
Source locator: Sec. V.B, Eq. (9) and associated discussion
PDF page: 5
Claim: The source defines a uniformly random-sign coherent model with \(\theta_i\in\{\theta,-\theta\}\), states that it has the same Pauli twirl as the fixed-sign model, and reports different fixed-sign and random-sign sub-threshold behaviour.

The paper attributes the difference to constructive versus destructive
interference.

## Random-sign and Pauli-twirl null result [paper_fact]
Fact ID: harper2605-random-sign-pta-agreement
Source locator: Fig. 5 caption
PDF page: 6
Claim: The Fig. 5 caption states that the logical-error rates of the random-sign coherent model are identical to those of the Pauli-twirling approximation despite the coherence of that model.

## Distance-nine model comparison [paper_fact]
Fact ID: harper2605-distance-nine-comparison
Source locator: Fig. 6 and caption
PDF page: 6
Claim: For the displayed distance-nine comparison, the source reports that fixed-sign coherent crosstalk raises logical error over the Pauli baseline while the random-direction coherent model reduces it relative to the fixed-sign coherent model.

## PEPS layout is future work [paper_fact]
Fact ID: harper2605-peps-future-work
Source locator: Conclusion, paragraph on further optimization and tensor-network layouts
PDF page: 7
Claim: The source lists a PEPS layout and tree tensor networks as possible future alternatives to its MPS residual.

No PEPS algorithm, benchmark, correctness certificate, or resource value is
reported.

## Ambiguous printed ZZ circuit [literature_gap]
Fact ID: harper2605-gap-zz-circuit-convention
Source locator: Sec. III.B, Eq. (4), implementation circuit, and surrounding text
PDF page: 3
Claim: The source does not define an \(R_Z\) convention that makes its printed CNOT--\(R_Z(\theta/2)\)--CNOT circuit reconstruct the displayed \(e^{+i\theta Z_1Z_2}\) unitary.
Gap scope: source_local

The paper does not explain the sign or scale relationship between the two
printed objects. With \(R_Z(\varphi)=e^{-i\varphi Z/2}\), the circuit gives
\(e^{-i\theta Z_1Z_2/4}\) rather than Eq. (4).

## Coupling-product mismatch [literature_gap]
Fact ID: harper2605-gap-coupling-product
Source locator: Sec. III.B, Eq. (5) and following hardware example
PDF page: 3
Claim: On the same page, the source defines \(\theta=J_{ZZ}t_g\), gives \(J_{ZZ}\) around \(100\,\mathrm{kHz}\) and \(t_g\) around \(100\,\mathrm{ns}\), and calls the resulting angle order \(10^{-3}\), although the printed product is \(10^{-2}\).
Gap scope: source_local

The separate Table I and results-section values are retained as atomic facts;
their cross-page inconsistency is recorded in the audit packet rather than
bundled into this single-page evidence record.

## One-qubit depolarizing normalization ambiguity [literature_gap]
Fact ID: harper2605-gap-one-qubit-depolarizing
Source locator: Sec. III.A, Eq. (2) and the sentence defining the Pauli-index set
PDF page: 2
Claim: Read literally with the printed index set including \(I\), Eq. (2) has trace \(1+p_1/3\); the source does not state that the identity should be excluded or otherwise repair the normalization.
Gap scope: source_local

## Missing logical-angle construction [literature_gap]
Fact ID: harper2605-gap-logical-angle-bridge
Source locator: Sec. II, Eq. (1) and its defining paragraph
PDF page: 2
Claim: The source defines \(P_L\) once syndrome-associated logical angles \(\theta_i\) are available but does not specify on this page how a sampled syndrome, decoder correction, and coherent logical channel are converted into each \(\theta_i\).
Gap scope: source_local

## Missing GCAMPS executable provenance [literature_gap]
Fact ID: harper2605-gap-gcamps-provenance
Source locator: Sec. IV opening paragraph naming GCAMPS
PDF page: 3
Claim: The source names the GCAMPS library but does not supply a version, commit, archived executable artifact, or source-code locator for the implementation used in the reported experiment.
Gap scope: source_local

## Incomplete non-Clifford expansion [literature_gap]
Fact ID: harper2605-gap-nonclifford-expansion
Source locator: Sec. IV.A, non-Clifford paragraph and displayed derivation
PDF page: 4
Claim: The source switches from \(T\) in prose to \(U\) in the displayed derivation and does not print the coefficients or normalization of its generic Pauli expansion.
Gap scope: source_local

## Unexplained Schmidt index [literature_gap]
Fact ID: harper2605-gap-schmidt-index
Source locator: Sec. IV.B, Eq. (8) and following paragraph
PDF page: 5
Claim: The source does not explain why Eq. (8) ends its Schmidt sum at \(\chi-1\) while the prose calls \(\chi\) the bond dimension.
Gap scope: source_local

The source's prose still supports a maximum-bond truncation rule, but not an
inferred correction of the printed summation limit.

## Ambiguous system-size symbol in truncation bound [literature_gap]
Fact ID: harper2605-gap-truncation-size-symbol
Source locator: Sec. IV.B, paragraph following Eq. (8)
PDF page: 5
Claim: The source writes \(\chi_{\max}\le 2^{N/2}\) without defining uppercase \(N\) in the truncation subsection or explaining its relation to the physical-qubit symbol used in the preceding figure.
Gap scope: source_local

## Missing reset transaction [literature_gap]
Fact ID: harper2605-gap-reset-transaction
Source locator: Table I and Sec. III.A
PDF page: 2
Claim: The source supplies a reset error-rate parameter but does not define an outcome-resolved reset channel, a fixed post-reset state, or a reset-state correctness invariant.
Gap scope: source_local

## Missing outcome-resolved measurement instrument [literature_gap]
Fact ID: harper2605-gap-measurement-instrument
Source locator: Sec. IV.A, projective-measurement paragraph
PDF page: 4
Claim: The source's projective-measurement pull-through does not specify outcome-resolved Kraus operators, Born branch masses, normalized conditional states, prefix masses, or a branch-completeness check.
Gap scope: source_local

## Missing complete Record law [literature_gap]
Fact ID: harper2605-gap-complete-record
Source locator: Sec. II, repeated-round syndrome paragraph
PDF page: 2
Claim: The source calls the repeated ancilla outcomes an error syndrome but does not define absolute raw-measurement columns, temporal detector folds, logical-observable XOR rows, or a canonical raw-to-Record map.
Gap scope: source_local

## Missing matched MPS resource comparison [literature_gap]
Fact ID: harper2605-gap-matched-mps-resources
Source locator: Sec. IV.A, final paragraph
PDF page: 4
Claim: The source gives a qualitative workload-specific reason for omitting Clifford optimization but does not report matched-accuracy runtime, peak memory, or throughput against a full-MPS or tableau-only route.
Gap scope: source_local

## Missing PEPS resource comparison [literature_gap]
Fact ID: harper2605-gap-peps-resources
Source locator: Conclusion, paragraph naming PEPS and tree tensor networks
PDF page: 7
Claim: The source names PEPS only as possible future work and reports no PEPS implementation, matched-accuracy runtime, peak memory, bond dimension, or comparison against the MPS route.
Gap scope: source_local

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
audit_packet_sha256 = "46b44a86c61df3304c600a8a8d01e650b53987a1e043c19b8553ad28fadcb727"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_harper_2605_source_only_review_2026_07_27"
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

## Repeated syndrome extraction [paper_fact]
Fact ID: harper2605-repeated-syndrome-extraction
Source locator: Sec. II, first paragraph; Fig. 1 and caption
PDF page: 2
Claim: The source simulates rotated-surface-code syndrome extraction repeated for \(d\) rounds, using face ancillas to measure local \(X\)- and \(Z\)-type checks.

Figure 1 shows data qubits on square-lattice vertices, ancillas on faces,
weight-four bulk checks, weight-two boundary checks, and separate \(X\)- and
\(Z\)-check circuits with ancillas prepared in \(|0\rangle\).

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

## Clifford–MPS hybrid state [paper_fact]
Fact ID: harper2605-hybrid-state
Source locator: Sec. IV.A, Eq. (7)
PDF page: 4
Claim: The source represents an arbitrary simulated state as a Clifford–MPS hybrid state \(|\psi\rangle=C|\mathrm{MPS}\rangle\).

The tensor-network component is described as typically an MPS. The paper does
not instantiate a PEPS residual.

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
Claim: The source expands a non-Clifford operation into Pauli terms, commutes those terms through \(C\), and applies the pulled-through Pauli sum to the MPS.

The printed derivation ends with \(C|\mathrm{MPS}'\rangle\) and supplies no
stochastic branch rule.

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
the bond dimension; the source does not explain that off-by-one convention.
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

## Coherent and Pauli-twirled result [paper_fact]
Fact ID: harper2605-coherent-twirled-result
Source locator: Sec. V.A and Fig. 4
PDF page: 6
Claim: For the reported workload, crosstalk lowers the threshold from about \(1\%\) to \(0.8\%\), while coherence further increases sub-threshold logical error without a statistically significant additional threshold shift.

Each Fig. 4 data point is described as an average from \(10^5\) samples. This
detailed statement is narrower than the abstract's unqualified threshold
wording.

## Same-twirl distribution comparison [paper_fact]
Fact ID: harper2605-same-twirl-distributions
Source locator: Sec. V.B, Eq. (9), Figs. 5–6, and associated discussion
PDF page: 6
Claim: Fixed-sign and uniformly random-sign coherent crosstalk models have the same Pauli twirl but different reported sub-threshold logical-error behaviour.

Equation (9) chooses \(\theta_i\) uniformly from \(\{\theta,-\theta\}\).
The paper attributes the difference to constructive versus destructive
interference.

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

## Inconsistent theta parameterization [literature_gap]
Fact ID: harper2605-gap-theta-parameters
Source locator: Table I; Sec. III.B, Eq. (5); Sec. V.A
PDF page: 3
Claim: The source does not reconcile its printed \(\theta=10^{-3}\), \(\theta=J_{ZZ}t_g\), and numerical \(J_{ZZ}t_g\) examples.
Gap scope: source_local

The printed examples evaluate to \(10^{-2}\) for
\(100\,\mathrm{kHz}\times100\,\mathrm{ns}\) and \(0.0225\) for
\(150\,\mathrm{kHz}\times150\,\mathrm{ns}\), not \(10^{-3}\).

## Unexplained Schmidt index [literature_gap]
Fact ID: harper2605-gap-schmidt-index
Source locator: Sec. IV.B, Eq. (8) and following paragraph
PDF page: 5
Claim: The source does not explain why Eq. (8) ends its Schmidt sum at \(\chi-1\) while the prose calls \(\chi\) the bond dimension.
Gap scope: source_local

The source's prose still supports a maximum-bond truncation rule, but not an
inferred correction of the printed summation limit.

## Missing outcome-resolved instrument [literature_gap]
Fact ID: harper2605-gap-outcome-instrument
Source locator: Sec. IV.A measurement description; Table I
PDF page: 4
Claim: The source does not specify outcome-resolved Born branch masses, normalized conditional states, or a fixed-state reset transaction for its measurement and reset model.
Gap scope: source_local

Table I supplies reset and measurement error rates, while Sec. IV.A supplies a
high-level projective-measurement pull-through. Neither location prints the
selective instrument required to reconstruct branch states and masses.

## Missing complete Record law [literature_gap]
Fact ID: harper2605-gap-complete-record
Source locator: Sec. II repeated-round description; Secs. IV–V
PDF page: 4
Claim: The source does not define or certify a complete raw-measurement law or a detector/observable Record pushforward.
Gap scope: source_local

The paper samples syndromes for a logical-error observable. It does not publish
absolute raw columns, detector or observable XOR rows, terminal branch
enumeration, Record total variation, or a complete classical–quantum
instrument.

## Missing matched resource comparison [literature_gap]
Fact ID: harper2605-gap-matched-resources
Source locator: Sec. IV and Conclusion
PDF page: 7
Claim: The source does not report a matched-accuracy runtime or peak-memory comparison among full tensor-network, hybrid MPS, hybrid PEPS, and Pauli-twirled routes.
Gap scope: source_local

Its optimizer-cost statement is qualitative and workload-specific. PEPS is
future work, not a measured comparator.

## Threshold wording qualification [literature_gap]
Fact ID: harper2605-gap-threshold-wording
Source locator: Abstract; Sec. V.A
PDF page: 5
Claim: The source's abstract attributes a lower threshold to coherence, whereas Sec. V.A says coherence has no statistically significant additional threshold effect beyond crosstalk.
Gap scope: source_local

Any source-faithful summary must retain the detailed Sec. V qualification.

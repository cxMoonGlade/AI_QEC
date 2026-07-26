+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2002.07119"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2002.07119v1"
source_artifact = "docs/papers/2002.07119v1.pdf"
source_sha256 = "e5e3f4756bcedac10a4016aaac957af41a7a560501033a7f43a993a7b22abbe9"
title = "Leakage detection for a transmon-based surface code"
publication_status = "preprint"
read_status = "incomplete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "incomplete"
admission_status = "pending_visual_verification_and_independent_review"
admission_reviewer = ""
admission_date = ""
visually_checked_pages = []
+++
# Full-text review — Varbanov, Battistel, Tarasinski, Ostroukh, O'Brien, DiCarlo, Terhal, "Leakage detection for a transmon-based surface code"

> **This note is deliberately NOT admissible and will fail `literature_rag.py audit`.** The schema
> requires `read_status = "complete"`, `operation_replay_status = "complete"` and
> `admission_status = "source_only_reviewed"`. Two gate conditions are unmet and neither can be
> satisfied by asserting them: (1) no PDF renderer is installed in this environment, so no equation,
> figure, or table was visually verified — every record below rests on extracted text; (2) no
> independent source-only reviewer has compared these claims against the source. The content is
> recorded so it is reusable and auditable; the front matter refuses the attestation.

## Source identity [paper_fact]
Fact ID: source-identity
Source locator: title page, author and affiliation block, date line
PDF page: 1
Claim: arXiv:2002.07119v1, dated 18 February 2020, by B. M. Varbanov, F. Battistel, B. M. Tarasinski, V. P. Ostroukh, T. E. O'Brien, L. DiCarlo and B. M. Terhal (QuTech/TU Delft, Kavli, Instituut-Lorentz Leiden, Google Research, Forschungszentrum Jülich), 21 pages including appendices.

## Selection scope [paper_fact]
Fact ID: selection-scope
Source locator: abstract
PDF page: 1
Claim: The source develops a leakage-detection scheme via hidden Markov models for transmon implementations of the distance-3 surface code, using density-matrix simulations, and reports restoring the logical error rate below the memory break-even point by post-selection.

## Load-bearing notation — leakage probability per two-qubit gate [paper_fact]
Fact ID: notation-l1
Source locator: Sec. I.A "Leakage error model"
PDF page: 2
Claim: `L1` denotes the leakage probability per CZ gate, with leakage modelled as an exchange between the two-qubit states |11> and |02> with amplitude sqrt(4*L1), and is set to 0.125% unless otherwise stated.

## Load-bearing notation — leakage conditional phases [paper_fact]
Fact ID: notation-leakage-conditional-phase
Source locator: Sec. I.A, definitions following the CZ rotation model
PDF page: 2
Claim: When one partner of a CZ is leaked the other acquires a leakage conditional phase, defined as `phi_stat^L := phi_02 - phi_12` when the flux qubit is leaked and `phi_flux^L := phi_20 - phi_21` when the static qubit is leaked; these are randomized per qubit pair across runs but held fixed across CZ gates within a run.

## Load-bearing notation — leakage population and defect probability [paper_fact]
Fact ID: notation-leakage-population
Source locator: Sec. I.C "Projection and signatures of leakage"
PDF page: 4
Claim: `p_DM^L(Q) = P(Q in L) = <2|rho_Q|2>` is the reduced-density-matrix probability that qubit Q occupies the leakage subspace at the end of a QEC cycle after ancilla measurement, and `p_d` is the probability of observing a defect `d = 1` on a neighbouring stabilizer.

## Model or mechanism — single-qubit gates act as identity on a leaked state [paper_fact]
Fact ID: mechanism-leaked-inert-single-qubit-gate
Source locator: Sec. I.A "Leakage error model", opening paragraph
PDF page: 2
Claim: The source states as an explicit modelling assumption, verbatim, "We assume that single-qubit gates act on a leaked state as the identity", alongside the assumptions that single-qubit gates induce no leakage and that measurement-induced leakage is negligible.

## Model or mechanism — three-level inclusion is selective [paper_fact]
Fact ID: mechanism-selective-qutrit
Source locator: Sec. I.B "Effect of leakage on the code performance"
PDF page: 3
Claim: Only the high- and mid-frequency qubits are treated as three-level systems in the density-matrix simulation while the low-frequency qubits remain two-level, because under the stated model with no leakage mobility only those are leakage-prone.

## Model or mechanism — defect definition under an unreset ancilla [paper_fact]
Fact ID: mechanism-defect-two-cycle
Source locator: Sec. I.B, paragraph defining syndrome and defect bits
PDF page: 3
Claim: Because ancilla qubits are not reset between QEC cycles, the syndrome is `m[n] XOR m[n-1]` and the surface-code defect is `d[n] = m[n] XOR m[n-2]`, with a measurement outcome `m[n] = 2` declared as `m[n] = 1`.

## Model or mechanism — leaked ancilla readout convention [paper_fact]
Fact ID: mechanism-leaked-readout-as-one
Source locator: decoding discussion preceding the leakage-detection section
PDF page: 12
Claim: For decoding the source assumes the |2> state is measured as a |1>, and states that this is the convention "as in most current experiments"; discrimination of |2> in readout is treated separately as a leakage-detection resource.

## Observable and bridge — data-qubit leakage reduces stabilizer weight and randomizes the check [paper_fact]
Fact ID: observable-bridge-weight3-anticommuting
Source locator: Sec. I.C, paragraph accompanying Fig. 3c-e
PDF page: 4
Claim: During data-qubit leakage the defect probability on neighbouring stabilizers rises to approximately 0.5, which the source explains by the leaked data qubit reducing the stabilizer checks it participates in to effective weight-3 anti-commuting checks, with the sharp projection of leakage attributed to measurement back-action whose outcomes are nearly randomized while the qubit is leaked.

## Observable and bridge — ancilla leakage disables the check and rotates neighbours [paper_fact]
Fact ID: observable-bridge-ancilla-signature
Source locator: Sec. I.C, paragraph accompanying Fig. 3f-h
PDF page: 4-5
Claim: During ancilla-qubit leakage the defect probability on neighbouring stabilizers rises abruptly in the cycle after leakage, which the source attributes to Z rotations acquired by neighbouring data qubits through interaction with the leaked ancilla, while the corresponding stabilizer measurement detects no errors at all and is effectively disabled.

## Findings and scale — leakage dwell times [paper_fact]
Fact ID: finding-dwell-time
Source locator: Sec. I.C, text accompanying Fig. 3a-d and Fig. 3g, referring to Table I parameters
PDF page: 4-5
Claim: A leaked data qubit remains leaked for approximately 9 QEC cycles on average and a leaked ancilla qubit for approximately 11 QEC cycles, with data-qubit leakage rising over roughly 3 QEC cycles to a maximum probability near 0.8.

## Findings and scale — effective distance reduction [paper_fact]
Fact ID: finding-distance-reduction
Source locator: Sec. I.C, paragraph following the weight-3 discussion
PDF page: 5
Claim: The weight-3 checks produced by data-qubit leakage can be interpreted as gauge operators whose pairwise product yields weight-6 stabilizer checks usable for decoding, effectively reducing the code distance from 3 to 2.

## Findings and scale — post-selection cost [paper_fact]
Fact ID: finding-postselection-cost
Source locator: abstract
PDF page: 1
Claim: The logical error rate is restored below the memory break-even point by post-selecting out leakage, at the cost of discarding about 47% of the data.

## Limitations and contrary results — declared model simplifications [paper_fact]
Fact ID: limitation-model-simplifications
Source locator: Sec. I.A, assumptions paragraph and the paragraph setting the exchange phase to zero
PDF page: 2-3
Claim: The source declares that single-qubit gates are assumed to induce no leakage and to act as identity on a leaked state, that measurement-induced leakage is neglected, that the leakage exchange phase and the |11><02| off-diagonal elements are set to zero for computational efficiency, and that leakage mobility and further leakage to |3> are treated only in an appendix.

## Limitations and contrary results — decoder weights are leakage-free [paper_fact]
Fact ID: limitation-decoder-trained-without-leakage
Source locator: Sec. I.B, description of the MWPM decoder
PDF page: 3-4
Claim: The minimum-weight perfect-matching decoder used to benchmark performance has weights trained on simulated data without leakage, so its reported logical error rate under leakage measures a leakage-unaware decoder.

## Source-local unsupported rows [literature_gap]
Fact ID: gap-transversal-echo-layer
Source locator: full-text keyword traversal of the extracted text; the two occurrences of "echo" appear in the flux-noise discussion of the Net-Zero pulse
PDF page: 13
Claim: This source does not apply, model, or discuss a transversal dynamical-decoupling layer on data qubits inside the QEC cycle; its only use of "echo" refers to the built-in echo effect of Net-Zero flux pulses on low-frequency flux noise, and "dynamical decoupling", "refocus" and "transversal" do not occur.
Gap scope: source_local

## Source-local unsupported rows [literature_gap]
Fact ID: gap-deterministic-frame-on-logical
Source locator: full-text keyword traversal; the single occurrence of "Pauli frame" is in the decoding discussion
PDF page: 12
Claim: This source does not treat the action of any deterministic inserted single-qubit layer on the logical operator or on stabilizer support parity; its one reference to a Pauli frame describes the MWPM decoder tracking decoder-inferred corrections to estimate the final logical state, not a circuit-level frame carried by intended gates.
Gap scope: source_local

## Source-local unsupported rows [literature_gap]
Fact ID: gap-support-parity-mechanism
Source locator: Sec. I.C, the mechanism paragraphs for both data-qubit and ancilla-qubit leakage
PDF page: 4-5
Claim: The source explains elevated defect probability by weight reduction and anti-commutation of the affected check and by phase rotation from a leaked ancilla, and does not state, derive, or test any mechanism in which the parity of the number of leaked support sites of a check determines a deterministic defect outcome.
Gap scope: source_local

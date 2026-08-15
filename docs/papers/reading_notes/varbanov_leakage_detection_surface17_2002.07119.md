+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2002.07119"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2002.07119v1"
source_artifact = "docs/papers/2002.07119v1.pdf"
source_sha256 = "e5e3f4756bcedac10a4016aaac957af41a7a560501033a7f43a993a7b22abbe9"
title = "Leakage detection for a transmon-based surface code"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/LEAKAGE_FRAME_LITERATURE_CLOSURE_2026-07-26.md"
audit_packet_sha256 = "c8ee8d0157fc5f1bc9c9cb0e208518a3579e103611d8fcaf114d4d450c04982b"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_varbanov_source_review"
admission_date = "2026-07-26"
visually_checked_pages = [1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

[[relations]]
predicate = "defines"
object_id = "varbanov.surface-code-defect"
object_type = "observable"
object_label = "surface-code defect"
fact_id = "varbanov.defect"

[[relations]]
predicate = "defines"
object_id = "varbanov.leakage-conditional-phase"
object_type = "model"
object_label = "leakage conditional phases"
fact_id = "varbanov.phases"

[[relations]]
predicate = "defines"
object_id = "varbanov.effective-weight-three-checks"
object_type = "model"
object_label = "effective weight-three parity checks"
fact_id = "varbanov.projector-regime"

[[relations]]
predicate = "defines"
object_id = "varbanov.weight-six-supercheck"
object_type = "observable"
object_label = "weight-six supercheck"
fact_id = "varbanov.supercheck"

[[relations]]
predicate = "defines"
object_id = "varbanov.leakage-hmm"
object_type = "method"
object_label = "two-hidden-state leakage model"
fact_id = "varbanov.hmm"

[[relations]]
predicate = "uses"
object_id = "varbanov.ancilla-pi-scheme"
object_type = "method"
object_label = "alternating ancilla pi-pulse scheme"
fact_id = "varbanov.ancilla-pi"

+++
# Full-text review -- Varbanov et al., "Leakage detection for a transmon-based surface code"

## Source identity [paper_fact]
Fact ID: varbanov.source
Source locator: PDF artifact metadata and p. 1 title and author block
PDF page: 1
Claim: The persisted source is the twenty-one-page arXiv:2002.07119v1 preprint by Boris M. Varbanov and coauthors, submitted on February 17, 2020.

Locators in this note refer only to the v1 artifact.

## Scientific scope [paper_fact]
Fact ID: varbanov.scope
Source locator: Abstract, PDF p. 1
PDF page: 1
Claim: The source simulates a qutrit-bearing distance-three Surface-17 circuit and infers the time and location of leakage with local hidden Markov models driven by neighboring defects, with ancilla analog readout additionally used for ancilla-qubit models.

It evaluates mitigation by post-selecting runs classified as leaked.

## Leaked-state gate convention [paper_fact]
Fact ID: varbanov.single-gate
Source locator: Sec. I.A, opening paragraph
PDF page: 2
Claim: The source assumes that single-qubit gates induce no leakage and act as the identity on a leaked state.

Measurement-induced leakage is also neglected in the stated error model.

## Leakage conditional phases [paper_fact]
Fact ID: varbanov.phases
Source locator: Sec. I.A, definitions following the CZ model
PDF page: 2
Claim: The leakage conditional phases are the phase differences imposed on the computational partner when either the fluxed or static CZ partner is leaked.

In the baseline simulation these phases are randomized per qubit pair between runs and held fixed within each run.

## Selective qutrit model [paper_fact]
Fact ID: varbanov.selective-qutrit
Source locator: Sec. I.B, Surface-17 simulation description
PDF page: 3
Claim: High- and middle-frequency transmons are modeled as qutrits while low-frequency data qubits remain two-level because the baseline model excludes leakage mobility.

Ancilla measurements are projective in the three-level basis.

## Surface-code defect [paper_fact]
Fact ID: varbanov.defect
Source locator: Sec. I.B, paragraph defining syndrome and defect bits
PDF page: 3
Claim: With ancillas left unreset, the surface-code defect is defined as d at cycle n equals m at n XOR m at n-minus-two, and a measured level two is declared as bit one.

The intermediate syndrome uses outcomes one cycle apart.

## Leakage projection [paper_fact]
Fact ID: varbanov.projection
Source locator: Sec. I.C, Fig. 3a-b and accompanying text
PDF page: 4
Claim: Repeated stabilizer measurement sharply projects simulated data-qubit leakage probabilities toward the computational or leakage sector.

This observation motivates the later use of a classical two-state hidden model.

## Data-leakage defect signature [paper_fact]
Fact ID: varbanov.data-signature
Source locator: Sec. I.C, Fig. 3c-e and accompanying text
PDF page: 4
Claim: Data-qubit leakage raises the neighboring stabilizer defect probability to approximately one half and is attributed to effective weight-reduced checks that anticommute.

The more detailed phase and supercheck qualifications are derived in Appendix D.

## Ancilla-leakage defect signature [paper_fact]
Fact ID: varbanov.ancilla-signature
Source locator: Sec. I.C, Fig. 3f-h and accompanying text
PDF page: 5
Claim: A leaked ancilla effectively disables its own check while leakage-conditional phase rotations on neighboring data qubits raise nearby defect rates.

## Effective distance reduction [paper_fact]
Fact ID: varbanov.distance
Source locator: Sec. I.C, paragraph following the effective-check explanation
PDF page: 5
Claim: One leaked data qubit reduces the effective code distance of Surface-17 from three to two.

The source attributes the reduction to replacing affected stabilizers with gauge checks and superchecks.

## Schedule-specific exchange-phase null [paper_fact]
Fact ID: varbanov.exchange-phase-null
Source locator: Appendix B, Eqs. (B7)-(B9)
PDF page: 14
Claim: In the simulated schedule, changing the leakage-exchange phase does not materially change the leakage dynamics or logical error rate.

The source attributes the null to an intervening ancilla measurement between repeated CZ interactions on the same pair and does not state it as a general channel identity.

## Schedule-specific coherent-leakage null [paper_fact]
Fact ID: varbanov.coherent-null
Source locator: Appendix B, final paragraph
PDF page: 14
Claim: Setting the computational-leakage coherences of the density matrix to zero leaves the leakage projections and signatures unchanged and, at least for a logical state prepared in the Z basis, does not affect the logical error rate.

The source presents this as a result for its simulated schedule, not a general coherence theorem.

## Qutrit CZ decomposition [paper_fact]
Fact ID: varbanov.cz-decomposition
Source locator: Appendix D, Eqs. (D1)-(D2)
PDF page: 15
Claim: In the limit of zero CZ leakage probability `L1`, zero leakage mobility `Lm`, and no decoherence, the ancilla-controlled qutrit CZ is decomposed into extended data operators whose leaked-level entries are minus one for the extended identity and minus `exp(-i phi_stat^L)` for the extended Z.

On the computational block those operators reduce to the ordinary identity and Pauli Z.

## Parity-check measurement operators [paper_fact]
Fact ID: varbanov.measurement-operators
Source locator: Appendix D, Eqs. (D3)-(D5)
PDF page: 16
Claim: The Z- and X-type parity-check outcomes are represented by two branch operators formed from extended identity and Pauli products, with the extended X derived under a Hadamard that acts trivially on leakage.

The leaked-level entry of the extended X carries the same leakage conditional phase as the extended Z.

## Leakage-induced anti-commutation [paper_fact]
Fact ID: varbanov.anticommutation
Source locator: Appendix D, Eqs. (D6)-(D12)
PDF page: 16
Claim: With one high-frequency data site leaked, the neighboring extended X- and Z-type checks anticommute independently of the leakage conditional phase.

The derivation requires the single-qubit gate on the leaked sector to commute with the leaked-sector CZ action.

Operation replay: Eq. (D11) prints a zero anticommutator for the four-overlap checks, whereas direct Pauli algebra gives a zero commutator. In Eq. (D12), direct multiplication gives the common prefactor exp(-2 i phi), not the printed exp(-i phi). The intended one-leaked-site anticommutation conclusion survives because it multiplies the zero anticommutator of the effective three-qubit X and Z checks.

## Projector phase regime [paper_fact]
Fact ID: varbanov.projector-regime
Source locator: Appendix D, Eq. (D13) and following paragraph
PDF page: 16
Claim: At leakage conditional phase zero or pi, the branch operators become projectors onto effective weight-three parity checks and their anti-commutation fully randomizes individual ancilla outcomes.

In this analytic regime the source assigns one-half defect probability to each neighboring stabilizer.

Operation replay: direct substitution into Eq. (D3) retains a branch-global minus sign omitted from Eq. (D13); it changes neither normalized post-measurement states nor probabilities. At phase pi, the plus and minus branch labels interchange.

## Weight-six supercheck [paper_fact]
Fact ID: varbanov.supercheck
Source locator: Appendix D, paragraph following Eq. (D13) and Fig. 10a
PDF page: 16
Claim: At leakage conditional phase zero or pi, the product of two same-type weight-three gauge outcomes defines a weight-six supercheck parity when both same-type gauges are measured before either opposite-type gauge.

The analyzed schedule satisfies that ordering condition.

## Generic-phase individual defects [paper_fact]
Fact ID: varbanov.generic-individual
Source locator: Appendix D, general-phase paragraph spanning PDF pp. 16-17
PDF page: 17
Claim: For leakage conditional phases other than zero or pi, individual branch operators are not projectors and outcomes are not analytically fully randomized, yet the simulations still give individual neighboring defect probabilities near one half for fixed or randomized phases.

The source explains that the two-cycle defect fold can turn moderate cycle-varying outcome imbalance into an approximately one-half defect probability.

## Generic-phase supercheck defects [paper_fact]
Fact ID: varbanov.generic-supercheck
Source locator: Appendix D, Fig. 10b-c and final paragraph
PDF page: 17
Claim: Outside the zero-or-pi projector regimes, leakage conditional phases perturb the two gauge measurements independently, giving a higher weight-six supercheck defect probability that can reach approximately one half.

Figure 10b-c plots the supercheck statistic rather than the individual neighboring-check statistic.

## Two-hidden-state leakage model [paper_fact]
Fact ID: varbanov.hmm
Source locator: Appendix E, Eqs. (E1)-(E6)
PDF page: 17
Claim: The two-hidden-state leakage model uses computational and leaked states, a transition matrix parameterized by leakage and seepage per cycle, state-dependent defect emissions, and a Bayesian posterior update.

The state posterior is an inferred probability, not a directly measured leakage label.

## Data-model emission approximation [paper_fact]
Fact ID: varbanov.hmm-emission
Source locator: Appendix E, paragraph following Eq. (E6)
PDF page: 17
Claim: The data-qubit hidden model uses leaked-state defect-emission probabilities near one half regardless of leakage conditional phase.

Those emission probabilities are extracted from density-matrix simulations using a leakage-probability threshold.

## Conditional-independence approximation [paper_fact]
Fact ID: varbanov.hmm-independence
Source locator: Appendix F, opening paragraph
PDF page: 18
Claim: Each local hidden model assumes that the neighboring defect observables are conditionally independent given the hidden leakage state.

## Alternating ancilla pi-pulse scheme [paper_fact]
Fact ID: varbanov.ancilla-pi
Source locator: Appendix G, opening paragraph spanning PDF pp. 18-19
PDF page: 19
Claim: The alternating ancilla pi-pulse scheme applies a pi pulse to each ancilla every other cycle and compensates it in post-processing so that a leaked ancilla, assumed unaffected by the pulse, would create a defect every cycle.

The pulse can be integrated with the single-qubit gates already present at the start of a cycle.

## Ancilla pi-scheme evaluation limit [paper_fact]
Fact ID: varbanov.ancilla-pi-limit
Source locator: Appendix G, paragraphs spanning PDF pp. 18-19
PDF page: 19
Claim: The alternating ancilla scheme is not physically simulated; it is evaluated by flipping outcomes only during density-matrix-identified ancilla-leakage periods.

The source reports improved ancilla-model optimality but worse data-model crosstalk and omits the added amplitude-damping cost of the physical pulses.

## Leakage mobility result [paper_fact]
Fact ID: varbanov.mobility
Source locator: Appendix I, opening paragraphs
PDF page: 20
Claim: In the simulated low-leakage regime, the included leakage-mobility probabilities have negligible effect on logical performance and hidden-model optimality.

The source calls mobility a second-order effect under its stated gate-leakage probability and limited qutrit allocation.

## Transversal data echo absent [literature_gap]
Fact ID: varbanov.gap-data-echo
Source locator: Full-text circuit scope; Net-Zero built-in flux echo in Appendix B on p. 13, Appendix D gate construction on pp. 15-17, and Appendix G ancilla-only proposal on pp. 18-19
PDF page: 18
Claim: The source does not apply or analyze a transversal data-qubit echo layer; its added deterministic pi-pulse proposal acts on ancillas every other cycle.
Gap scope: source_local

The Net-Zero pulse's built-in flux echo is a two-qubit-gate implementation detail, not a data-wide inserted layer.

## Logical-observable frame absent [literature_gap]
Fact ID: varbanov.gap-logical-frame
Source locator: Appendix A MWPM Pauli-frame tracking on p. 12 and Appendix G post-processing proposal on pp. 18-19
PDF page: 12
Claim: The source does not define a logical-observable frame conditioned on a data-qubit leakage and return trajectory.
Gap scope: source_local

Its Pauli-frame reference concerns decoder-inferred corrections, while the ancilla proposal applies a predetermined outcome relabeling.

## Exact instrument from public defects absent [literature_gap]
Fact ID: varbanov.gap-identifiability
Source locator: Appendix E hidden-state emissions and Appendix F error budget
PDF page: 18
Claim: The source does not prove that the hidden leakage trajectory or an exact trajectory-dependent correction is identifiable from the public defect sequence.
Gap scope: source_local

It reports an approximate local estimator with crosstalk and regular-error limitations.

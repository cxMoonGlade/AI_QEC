+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1306.0925"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1306.0925v2"
source_artifact = "docs/papers/1306.0925v2.pdf"
source_sha256 = "d2b630d8cee32a4e1ab5302fda3e4f7cee15849577565dff9eb63a10dd10f076"
title = "Understanding the effects of leakage in superconducting quantum error detection circuits"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/LEAKAGE_FRAME_LITERATURE_CLOSURE_2026-07-26.md"
audit_packet_sha256 = "c8ee8d0157fc5f1bc9c9cb0e208518a3579e103611d8fcaf114d4d450c04982b"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_ghosh_source_review"
admission_date = "2026-07-26"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8]

[[relations]]
predicate = "defines"
object_id = "ghosh.ancilla-assisted-sigma-z-measurement"
object_type = "method"
object_label = "ancilla-assisted measurement of a single sigma-z operator"
fact_id = "ghosh.scope"

[[relations]]
predicate = "defines"
object_id = "ghosh.leakage-phase-theta"
object_type = "model"
object_label = "leakage phase theta"
fact_id = "ghosh.theta"

[[relations]]
predicate = "defines"
object_id = "ghosh.ancilla-paralysis"
object_type = "observable"
object_label = "ancilla paralysis"
fact_id = "ghosh.paralysis"

[[relations]]
predicate = "defines"
object_id = "ghosh.paralysis-spacing"
object_type = "observable"
object_label = "spacing metric W"
fact_id = "ghosh.spacing"

+++
# Full-text review -- Ghosh, Fowler, Martinis, and Geller, "Understanding the effects of leakage in superconducting quantum error detection circuits"

## Source identity [paper_fact]
Fact ID: ghosh.source
Source locator: PDF artifact metadata and p. 1 title, author, rendered date, and arXiv footer
PDF page: 1
Claim: Joydip Ghosh, Austin G. Fowler, John M. Martinis, and Michael R. Geller authored the persisted eight-page arXiv:1306.0925v2 artifact.

The footer identifies v2 dated December 11, 2013, while the rendered title date and PDF creation metadata both say September 2, 2018; this provenance anomaly does not change the version pin.

## Scientific scope [paper_fact]
Fact ID: ghosh.scope
Source locator: Abstract and Sec. I, PDF p. 1
PDF page: 1
Claim: The source studies repeated ancilla-assisted measurement of a single sigma-z operator for one data qutrit and analyzes leakage signatures in the ancilla readout sequence.

It combines a two-qutrit simulation with an analytic reduction of the leaked-data dynamics.

## Measurement circuit [paper_fact]
Fact ID: ghosh.circuit
Source locator: Sec. I, Fig. 1 and its caption
PDF page: 2
Claim: Each measurement cycle resets the ancilla to zero, applies an ancilla Hadamard, a CZ, a second ancilla Hadamard, and ancilla readout, while the data qutrit is never measured or reset.

The cycle is repeated indefinitely in the analyzed protocol.

## Hadamard leakage embedding [paper_fact]
Fact ID: ghosh.hadamard
Source locator: Sec. I, Eq. (2)
PDF page: 2
Claim: The source embeds the Hadamard as the two-level Hadamard direct-summed with a unit entry on the third level.

This is a declared qutrit gate convention.

## Ideal qutrit CZ extension [paper_fact]
Fact ID: ghosh.cz-extension
Source locator: Sec. II.A, Eq. (6) and following paragraph
PDF page: 3
Claim: The ideal qutrit CZ generator assigns phase pi to |11> and |20>, while the other four noncomputational basis states |02>, |12>, |21>, and |22> receive protocol-dependent dynamical phases xi1 through xi4.

The source explicitly states that extending an ideal CZ to qutrits depends on the model and gate protocol.

## Leakage phase [paper_fact]
Fact ID: ghosh.theta
Source locator: Sec. II.A, Eqs. (7)-(8)
PDF page: 3
Claim: The leakage phase theta is defined as xi2 minus xi1 and is the dynamical phase difference that determines whether the ancilla becomes paralyzed during a data-leakage event.

The phase can be varied by changing the CZ gate time in the stated adiabatic model.

## Measurement-induced leakage map [paper_fact]
Fact ID: ghosh.measurement-map
Source locator: Sec. III.B, special case in Eq. (13) and Eqs. (15)-(18)
PDF page: 5
Claim: Under the special-case parameters of Eq. (13), the ancilla-zero measurement map sends an initially occupied data state |1> to |2> in the limit chi1 equals zero and chi2 approaches zero.

The simulations identify this nonlinear measurement back-action as the dominant mechanism producing near-unit data leakage in the model.

## Leaked-data subspace [paper_fact]
Fact ID: ghosh.leaked-subspace
Source locator: Sec. III.B, Eqs. (19)-(20)
PDF page: 5
Claim: While the data qutrit remains in |2>, the joint dynamics are restricted to the span of |02> and |12>, where the CZ acts diagonally with phases xi1 and xi2.

The two joint states differ only by the ancilla computational state.

## Ancilla rotation during leakage [paper_fact]
Fact ID: ghosh.ancilla-rotation
Source locator: Sec. III.B, Eqs. (20)-(22) and probability sentence on PDF pp. 5-6
PDF page: 6
Claim: The source identifies the leaked-data CZ phase difference as an ancilla z rotation by theta and states that the surrounding Hadamards convert it to an ancilla x rotation.

The unambiguous measurement prediction is that the probability of ancilla outcome zero equals cosine-squared theta-over-two.

## Equiprobable leakage signature [paper_fact]
Fact ID: ghosh.random-regime
Source locator: Sec. III.B, Eq. (23), following sentence, and Fig. 4
PDF page: 6
Claim: When theta modulo pi equals pi over two, the analytic model gives equiprobable ancilla outcomes zero and one during the leaked-data interval.

The source describes this regime as a leakage event that is simple to detect.

## Ancilla paralysis [paper_fact]
Fact ID: ghosh.paralysis
Source locator: Sec. III.B, Eq. (24), following paragraph, and Fig. 4
PDF page: 6
Claim: The source labels theta modulo pi equal to zero as ancilla paralysis and describes it as a deterministic all-zero readout with no indication of the leaked data state.

Figure 4 shows simulated traces with no leakage signature at theta equal to zero and random oscillations at larger theta.

## Paralysis spacing [paper_fact]
Fact ID: ghosh.spacing
Source locator: Sec. III.B, Eq. (25)
PDF page: 6
Claim: The spacing metric W is the average number of cycles between consecutive ancilla-one outcomes and equals cosecant-squared theta-over-two without decoherence.

## Critical paralysis phase [paper_fact]
Fact ID: ghosh.critical-phase
Source locator: Sec. III.B, Eqs. (26)-(27) and Fig. 4 caption
PDF page: 6
Claim: For T1 equal to 40 microseconds and a 45-nanosecond cycle, the source estimates a decoherence-background spacing W-star of 1778 cycles, compares it with the simulated background value 2381, and obtains a critical phase theta-star of 0.04.

The source labels theta modulo pi below this model-dependent threshold as susceptible to undetectable leakage.

## Time-correlated measurement errors [paper_fact]
Fact ID: ghosh.time-correlation
Source locator: Sec. IV, opening paragraph
PDF page: 7
Claim: The source concludes that a leaked data qutrit can randomize or paralyze the measurement qutrit and that long-lived leakage events thereby create long strings of time-correlated measurement errors.

This conclusion is drawn for the repeated one-data-one-ancilla circuit studied in the source.

## No modeled leakage propagation [paper_fact]
Fact ID: ghosh.no-propagation
Source locator: Sec. IV, opening paragraph
PDF page: 7
Claim: In the source's two-qutrit entangling model, leakage is observed not to propagate from one qutrit to its neighbor.

## Surface-code extrapolation [paper_fact]
Fact ID: ghosh.surface-extrapolation
Source locator: Sec. IV, paragraph beginning with the relevance to topological error correction
PDF page: 7
Claim: The source extrapolates its single-data measurement mechanism to surface- and toric-code stabilizer circuits because they use similar repeated ancilla-assisted measurements.

## Multi-check record absent [literature_gap]
Fact ID: ghosh.gap-surface-record
Source locator: Abstract and Sec. I protocol definition on PDF pp. 1-2; qualitative extrapolation in Sec. IV on p. 7
PDF page: 7
Claim: The source's single sigma-z measurement circuit does not construct joint neighboring-check products or a surface-code detector record.
Gap scope: source_local

Its measured object is one ancilla outcome sequence.

## Hidden-state estimator absent [literature_gap]
Fact ID: ghosh.gap-hmm
Source locator: Full-text review; stated analysis scope in Secs. I and IV
PDF page: 7
Claim: The source does not construct a hidden-state estimator or infer a leakage posterior from the ancilla sequence.
Gap scope: source_local

## Logical frame absent [literature_gap]
Fact ID: ghosh.gap-logical-frame
Source locator: Full-text review; stated analysis scope in Secs. I and IV
PDF page: 7
Claim: The source does not define a logical observable or a trajectory-conditioned logical frame.
Gap scope: source_local

## Data echo absent [literature_gap]
Fact ID: ghosh.gap-data-echo
Source locator: Sec. I, Fig. 1 circuit
PDF page: 2
Claim: The source does not apply a data-qubit echo pulse in the repeated measurement circuit.
Gap scope: source_local

The only single-qutrit gates shown in each cycle are the two ancilla Hadamards.

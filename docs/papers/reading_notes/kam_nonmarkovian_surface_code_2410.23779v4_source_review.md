+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2410.23779"
source_version = "v4"
source_uri = "https://arxiv.org/abs/2410.23779v4"
source_artifact = "outputs/papers/2410.23779.pdf"
source_sha256 = "9f7bfb374110dc76df3a60a0af3e16f64347ad80de999a2fce687d88936866bf"
title = "Detrimental non-Markovian errors for surface code memory"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion/KAM_NONMARKOVIAN_SURFACE_CODE_2410_23779_AUDIT_2026-08-05.md"
audit_packet_sha256 = "83e20e4bfa34301e9ed6e25753a8dcc3155073fbab7ea49e2f15a11c1924d2a1"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-kam-2026-08-05"
admission_date = "2026-08-05"
visually_checked_pages = [1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20]

[[relations]]
predicate = "defines"
object_id = "kam-pairwise-and-streaky-event-models"
object_type = "model"
object_label = "pairwise and streaky event models"
fact_id = "kam-temporal-event-models"

[[relations]]
predicate = "defines"
object_id = "kam-matched-one-location-marginals"
object_type = "method"
object_label = "matched one-location marginals"
fact_id = "kam-matched-marginals"

[[relations]]
predicate = "uses"
object_id = "kam-error-mask-stim-monte-carlo"
object_type = "method"
object_label = "custom error-mask Monte Carlo with Stim FlipSimulator"
fact_id = "kam-computational-strategy"

[[relations]]
predicate = "supports"
object_id = "kam-structure-dependent-logical-scaling"
object_type = "observable"
object_label = "structure-dependent logical-error scaling"
fact_id = "kam-class-dependent-result"

[[relations]]
predicate = "limits"
object_id = "kam-pairwise-autocorrelation-severity"
object_type = "limitation"
object_label = "pairwise detector autocorrelation"
fact_id = "kam-autocorrelation-limitation"
+++
# Full-text review — Kam et al., "Detrimental non-Markovian errors for surface code memory"

## Source identity [paper_fact]
Fact ID: kam-source-identity
Source locator: Title page and arXiv identifier/date in page margin
PDF page: 1
Claim: The fixed source is arXiv:2410.23779v4, whose page-margin version stamp is dated 18 July 2025, by John F. Kam, Spiro Gicev, Kavan Modi, Angus Southwell, and Muhammad Usman.

The artifact is the 20-page v4 preprint; the manuscript title page gives a manuscript date of
21 July 2025. This record does not substitute publisher pagination or metadata for the fixed arXiv
artifact.

## Selection scope [paper_fact]
Fact ID: kam-selection-scope
Source locator: Abstract and Sec. I
PDF page: 1
Claim: The source asks how selected two-time and multi-time temporal error structures change rotated-surface-code memory performance when compared with temporally independent circuit-level noise having the same one-location marginal error rates.

The work is a numerical model comparison. It does not estimate a device noise process or test a
microscopic open-system mechanism.

## Detector and decoder interface [paper_fact]
Fact ID: kam-detector-interface
Source locator: Sec. II.B, Eq. (2) and following detector-error-model discussion
PDF page: 3
Claim: The QEC-facing variables are detectors D_(s,t) = M_(s,t-1) XOR M_(s,t), their space-time detection events, a detector error model, and the final logical-memory outcome supplied to minimum-weight perfect matching.

The source distinguishes spacelike data-qubit errors, timelike syndrome-qubit errors, and
spacetimelike circuit errors by their detector endpoints. A stringlike error is a chain that triggers
no more than two endpoints or terminates at boundaries.

## Temporal event representation [paper_fact]
Fact ID: kam-temporal-event-models
Source locator: Sec. III.A, Fig. 3 caption and model definitions
PDF page: 6
Claim: The paper defines pairwise and streaky event models in which same-location errors occur at two selected rounds or throughout a selected interval, with event probability decaying polynomially or exponentially with separation or streak length.

For Class 0 locations the conditional error is depolarizing on a data qubit; Class 1 uses syndrome
bit flips; Class 2 uses two-qubit depolarizing errors after entangling gates. Correlations are confined
within an error class. These are prescribed circuit-level event processes rather than derived bath
dynamics.

## Matched-marginal construction [paper_fact]
Fact ID: kam-matched-marginals
Source locator: Sec. III.A (PDF pages 5–7) and Appendix A, Eqs. (A1)–(A10)
PDF page: 17
Claim: The correlated and independent contrasts have matched one-location marginals obtained by rewriting each channel as an idempotent maximal-mixing event and multiplying the probabilities that no event covering a space-time location occurs.

The conversion factors are channel-specific: 2 for the bit-flip channel, 4/3 for the single-qubit
depolarizing channel, and 16/15 for the two-qubit depolarizing channel. Because middle rounds can be
covered by more intervals, both sides of the contrast may be time-inhomogeneous; the construction
matches that inhomogeneity one location and time at a time.

## Computational strategy [paper_fact]
Fact ID: kam-computational-strategy
Source locator: Sec. III.B, Eqs. (3)–(4)
PDF page: 7
Claim: Predictions are computed by custom error-mask Monte Carlo with Stim FlipSimulator, mapping sampled correlated events through an endpoint-or-interval incidence matrix into dynamic Pauli injections and decoding both contrast arms with the same marginalized-independent PyMatching model.

The event matrix records which proposed pair or interval events occur. The transformation matrix
marks either the two endpoints or every time in the interval; error-class-specific composition then
produces the mask supplied to the Clifford simulator. The decoder is intentionally blind to the
correlation structure.

## Demonstrated QEC reach [paper_fact]
Fact ID: kam-demonstrated-reach
Source locator: Sec. III.B–C and Fig. 3 caption
PDF page: 7
Claim: The demonstrated calculation is a rotated-surface-code memory experiment lasting 2d syndrome rounds and simulated through code distance 15; the main logical-error simulation series use 10 million trials and report 95% confidence intervals on logical error per round.

The two-round-block duration is a practical choice, not a claim about arbitrarily long computation.
Distances needed for a logical error rate of 10^-12 per round are obtained from fits and therefore are
projections beyond the simulated distances.

## Pairwise control result [paper_fact]
Fact ID: kam-pairwise-result
Source locator: Sec. III.C, Fig. 3 and Table I
PDF page: 7
Claim: For the tested quadratically decaying circuit-level pairwise model at q = 10^-3, correlated and matched-independent logical-error curves are both fitted exponentially and both project to teraquop distance 27.

This is a null contrast within one declared family: it prevents the paper's detrimental result from
being generalized to all long-range temporal correlations.

## Multi-time streak result [paper_fact]
Fact ID: kam-streaky-result
Source locator: Sec. III.C, Figs. 3–4 and Table I
PDF page: 8
Claim: For the tested quadratically decaying circuit-level streak model, the logical error at distance 15 is about 58 times the matched-independent value, the fitted suppression is slower than exponential, and the paper gives no realistic teraquop-distance projection.

The plotted crossings near 0.3–0.4% are explicitly called apparent thresholds. The source does not
establish a conventional asymptotic threshold for the streak model.

## Error-class dependence [paper_fact]
Fact ID: kam-class-dependent-result
Source locator: Sec. IV.A, Fig. 5 and Table I
PDF page: 9
Claim: The class-isolated simulations show structure-dependent logical-error scaling: Class 0 pairwise and streaky cases retain favorable suppression, whereas quadratically decaying Class 1 and Class 2 streak cases do not yield realistic teraquop projections under the fixed decoder.

At distance 15, the paper reports the Class 1 streak logical error as 97 times its matched-independent
counterpart. The authors interpret the Class 1/2 sensitivity through timelike strings involving
syndrome qubits, while noting that a purely timelike string need not flip the logical observable in a
memory experiment without its interaction with spatial or spacetime errors.

## Pairwise statistic limitation [paper_fact]
Fact ID: kam-autocorrelation-limitation
Source locator: Sec. IV.C, Eq. (5), Figs. 7–8 and associated discussion
PDF page: 11
Claim: Across the tested models, pairwise detector autocorrelation persists over several round separations but its magnitude does not track logical severity or distinguish continuous streaks from disjoint localized errors.

The demonstrated insufficiency concerns the selected Pearson detector-correlation summary in these
models. It is not a theorem excluding every possible two-time observable.

## Finite-distance scaling caveat [paper_fact]
Fact ID: kam-finite-distance-caveat
Source locator: Appendix B and Fig. B1
PDF page: 19
Claim: At q = 0.002 and q = 0.003 the tested streak model has examples of non-monotonic logical error versus distance while its matched-independent comparison remains monotonic, but the source leaves persistence of this behavior across q unresolved.

The appendix states that the finite-distance power-law fit need not persist at larger code distances.

## No demonstrated memory-aware benefit [literature_gap]
Fact ID: kam-gap-decoder-benefit
Source locator: Sec. III.B (fixed decoder) and Sec. V.B (potential mitigation), PDF pages 7 and 13
PDF page: 7
Claim: The source does not implement or compare a memory-aware decoder, reset policy, or control intervention and therefore establishes no intervention benefit.
Gap scope: source_local

Tailored edge weights, drift-aware updates, code deformation, and walking circuits are discussed as
possibilities, not results of this study.

## No hardware observation or microscopic attribution [literature_gap]
Fact ID: kam-gap-observation-attribution
Source locator: Complete study design in Secs. I–V and experimental comparison in Sec. V.A, PDF pages 1–14
PDF page: 13
Claim: The source does not itself observe temporal structure on hardware or identify a microscopic cause for its prescribed event models.
Gap scope: source_local

Its comparison to a reported superconducting-QEC event pattern is contextual. It does not fit the
pairwise or streak process to those records and cannot transfer the simulated mechanism label to the
device event.

## No transfer demonstration [literature_gap]
Fact ID: kam-gap-transfer
Source locator: Sec. II.A scope statement, Sec. III simulation design, and Sec. V.C conclusion, PDF pages 2, 7, and 14
PDF page: 14
Claim: The source does not demonstrate transfer of its quantitative findings beyond the tested rotated surface-code memory circuits, prescribed noise families, finite round counts, and correlation-blind MWPM decoder.
Gap scope: source_local

The statement that the analysis should extend to other surface-code variations is not accompanied by
an additional code-family or decoder comparison in this artifact.

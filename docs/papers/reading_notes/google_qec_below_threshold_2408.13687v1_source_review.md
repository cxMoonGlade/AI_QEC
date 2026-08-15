+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2408.13687"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2408.13687v1"
source_artifact = "outputs/papers/2408.13687.pdf"
source_sha256 = "9ba05a64dfec13f5d733e0e22484e8f22db2482dc2a5a0d63e6f0766c9c3d368"
title = "Quantum error correction below the surface code threshold"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion/GOOGLE_QEC_BELOW_THRESHOLD_2408_13687_AUDIT_2026-08-05.md"
audit_packet_sha256 = "1c7bc0a8ce1978c28e1655380dc7c248ac2d86e7d5ce318c8903ed372609dc46"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-google-2026-08-05"
admission_date = "2026-08-05"
visually_checked_pages = [1, 4, 5, 6, 18, 20, 21, 23, 27]

[[relations]]
predicate = "defines"
object_id = "google-logical-error-per-cycle"
object_type = "observable"
object_label = "logical error per cycle"
fact_id = "google-logical-rate-conversion"

[[relations]]
predicate = "measures"
object_id = "google-persistent-detector-event-patterns"
object_type = "observable"
object_label = "temporally persistent detector-event patterns"
fact_id = "google-rare-event-patterns"

[[relations]]
predicate = "supports"
object_id = "google-high-distance-repetition-code-failures"
object_type = "observable"
object_label = "high-distance repetition-code logical failures"
fact_id = "google-logical-failure-association"

[[relations]]
predicate = "limits"
object_id = "google-new-burst-cause"
object_type = "limitation"
object_label = "cause of the new large bursts"
fact_id = "google-attribution-boundary"
+++
# Full-text review — Google Quantum AI and Collaborators, "Quantum error correction below the surface code threshold"

## Source identity [paper_fact]
Fact ID: google-source-identity
Source locator: Title page, arXiv identifier in page margin, and author list
PDF page: 1
Claim: The fixed source is the 27-page arXiv:2408.13687v1 artifact by Google Quantum AI and Collaborators, dated 27 August 2024 on the manuscript title page.

The arXiv record links the work to *Nature* 638, 920–926 (2025), DOI
`10.1038/s41586-024-08449-y`. This record fixes and reviews the arXiv v1 artifact, including its
embedded Supplementary Information, rather than substituting later publisher text.

## Selection scope [paper_fact]
Fact ID: google-selection-scope
Source locator: Abstract and Sec. IV, "Probing the ultra-low error regime with repetition codes"
PDF page: 4
Claim: In addition to demonstrating distance-5 and distance-7 surface-code memories, the source uses high-distance repetition codes to probe rare error structures that limit logical performance in an ultra-low-error regime.

The rare-event evidence comes from the repetition-code experiment. The surface-code experiments
answer separate questions about below-threshold scaling, break-even memory, error sensitivity, drift,
and real-time decoding.

## Repetition-code experiment [paper_fact]
Fact ID: google-repetition-code-experiment
Source locator: Main Sec. IV, second paragraph
PDF page: 4
Claim: The rare-event dataset comprises distance-29 bit- and phase-flip repetition-code experiments with 1,000 error-correction cycles per shot, 2 x 10^7 shots split evenly by basis, and 2 x 10^10 total QEC cycles acquired over 5.5 hours on the 72-qubit processor.

Lower odd distances are subsampled from the distance-29 data. Logical outcomes are decoded with
minimum-weight perfect matching for the distance-scaling result in Fig. 3a.

## Logical-rate conversion [paper_fact]
Fact ID: google-logical-rate-conversion
Source locator: SI Sec. VI.B, "Logical Error per Cycle From One Point"
PDF page: 23
Claim: The paper defines logical error per cycle from one measured endpoint as epsilon_d = [1 - (1 - 2 p_L)^(1/t)] / 2, where p_L is terminal logical error probability after t cycles under a binomial per-step logical-error model.

For the repetition-code data, `t = 1000`. The source notes that uncertainty becomes prominent at the
highest distances because few failures are observed and that the statistical floor is set by the
2 x 10^10 total cycles.

## Detector-burst display [paper_fact]
Fact ID: google-detector-burst-display
Source locator: Main Fig. 3d and caption
PDF page: 5
Claim: Figure 3d displays a large event through detector probabilities averaged over detector quartiles and ten-cycle time windows across three consecutive shots, with an exponential fit giving a 369 +/- 6 microsecond decay constant for the example.

The inset maps the detector probabilities averaged over the highlighted interval onto the repetition-code
qubit layout. The display therefore carries both temporal persistence and spatial localization.

## Rare-event patterns [paper_fact]
Fact ID: google-rare-event-patterns
Source locator: Main Sec. IV and SI Sec. V.A with Fig. S7
PDF page: 21
Claim: The repeated-QEC records contain two temporally persistent detector-event patterns: spatially grouped bursts with sharp onset and 400–700 microsecond decay over several shots, and single-detector events that remain at elevated firing probability for 1–2 ms.

For Fig. S7 the detector traces are smoothed with a Gaussian filter of sigma 2, and shot boundaries are
shown explicitly. The large bursts occur roughly once per hour, or once per 3 x 10^6 shots, in both
bit- and phase-flip experiments. The single-noisy-detector pattern also produces a high-distance error
about once per hour, with the affected detector varying between events.

## Logical-failure association [paper_fact]
Fact ID: google-logical-failure-association
Source locator: SI Sec. V.A, "Low Probability Events in the Repetition Code"
PDF page: 20
Claim: The spatially grouped bursts account for all observed distance-27 logical errors and half of the distance-21 to distance-25 errors, directly associating the observed temporal structures with high-distance repetition-code logical failures in this dataset.

The main text reports six large bursts over 2 x 10^10 cycles and states that they are responsible for
the highest-distance failures. This is an event–failure association in the measured record; no targeted
intervention on the new events is part of the experiment.

## Apparent logical floor [paper_fact]
Fact ID: google-apparent-logical-floor
Source locator: Main Sec. IV and Fig. 3a
PDF page: 5
Claim: Error suppression deviates from the fitted exponential for distances at least 15 and culminates in what the source calls an apparent logical-error-per-cycle floor near 10^-10, while no distance-29 errors are directly observed.

The authors state that the absence of distance-29 errors is likely due to the decoder randomly choosing
correctly on the few most damaging bursts. The floor is therefore presented as an apparent tail summary,
not as an exactly determined stationary asymptote.

## Prior-event distinction [paper_fact]
Fact ID: google-prior-event-distinction
Source locator: Main Sec. IV, paragraph continuing below Fig. 3
PDF page: 5
Claim: The new large bursts are distinguished from previously reported high-energy impact events by occurring about once per hour rather than once every few seconds and by decaying near 400 microseconds rather than over tens of milliseconds.

The Supplementary Information gives the previous quasiparticle-associated detection-burst recovery
time as 25–30 ms and the earlier event frequency as about once every ten seconds. The comparison does
not identify the new event mechanism.

## Candidate explanations for the smaller pattern [paper_fact]
Fact ID: google-candidate-smaller-event-causes
Source locator: Main Sec. IV, detector-pattern discussion
PDF page: 4
Claim: The source presents transient two-level-system motion near a qubit operating frequency and coupler excitation as possible, not discriminated, causes of the less-damaging one- or two-detector events.

The modal wording is part of the source's evidential boundary: neither explanation is selected by an
intervention or an independent microscopic measurement in this artifact.

## Attribution boundary [paper_fact]
Fact ID: google-attribution-boundary
Source locator: Main Sec. IV, paragraph continuing below Fig. 3
PDF page: 5
Claim: The source explicitly states that the cause of the new large bursts is not understood.

The paper attributes mitigation of the older high-energy-impact failures to gap-engineered Josephson
junctions, but it does not transfer that attribution to the new once-per-hour events.

## Leakage-specific comparison [paper_fact]
Fact ID: google-leakage-comparison
Source locator: SI Sec. IV.A.2.c, "Importance of DQLR in surface codes," and Fig. S5
PDF page: 18
Claim: In a separate surface-code simulation, leakage surviving for several QEC cycles produces time-correlated detection events and loss of large-distance suppression, while idealized data-qubit leakage removal restores exponential suppression.

This result concerns the declared leakage model and the with/without-DQLR comparison. The source does
not identify leakage as the origin of the distinct rare repetition-code events described in Sec. IV.

## Finite-event limitation [paper_fact]
Fact ID: google-finite-event-limitation
Source locator: Main Sec. IV, final paragraph before Sec. V
PDF page: 5
Claim: The large-burst conclusion is based on six observed events, and the source leaves their physical cause unresolved despite their dominance of the highest-distance failures.

The paper calls the floor apparent, reports zero observed distance-29 failures, and obtains its
per-cycle rate from the stated one-point binomial conversion rather than a direct stationary-tail
measurement.

## No microscopic or non-leakage attribution [literature_gap]
Fact ID: google-gap-microscopic-attribution
Source locator: Main Sec. IV, paragraph continuing below Fig. 3, and SI Sec. V.A
PDF page: 5
Claim: The source does not identify a microscopic carrier for the newly observed limiting events or establish that they form a non-leakage mechanism.
Gap scope: source_local

The distinct record signatures establish temporal structure without establishing whether a physical
degree of freedom persists through the QEC operations.

## No strict non-Markovianity test [literature_gap]
Fact ID: google-gap-nonmarkovianity-test
Source locator: Complete experimental and analytical scope, Main Secs. I–VI and SI Secs. I–VI
PDF page: 27
Claim: The source does not perform an operational quantum non-Markovianity witness, causal-break test, process-tensor reconstruction, or divisibility analysis for the rare events.
Gap scope: source_local

Observed detector persistence and a strict quantum non-Markovianity claim are therefore not equivalent
within this artifact.

## No surface-code rare-event transfer [literature_gap]
Fact ID: google-gap-surface-code-transfer
Source locator: Main Sec. IV repetition-code design and Sec. VI outlook
PDF page: 6
Claim: The source does not demonstrate that the repetition-code rare-event floor or its quantitative distance dependence transfers to the reported distance-5 or distance-7 surface-code memories.
Gap scope: source_local

The source states that identifying and mitigating the correlated-burst mechanism is necessary for
larger systems, but it does not report the same limiting-event analysis for the surface-code datasets.

## No memory-aware intervention benefit [literature_gap]
Fact ID: google-gap-memory-aware-benefit
Source locator: Main Secs. IV–V and SI Sec. III decoder descriptions
PDF page: 6
Claim: The source does not compare a memory-aware decoder or control policy against a memory-blind counterpart on the newly observed rare events.
Gap scope: source_local

Real-time and offline decoder comparisons address accuracy and latency under different decoder designs;
they do not isolate access to the rare-event history or target the new event mechanism.

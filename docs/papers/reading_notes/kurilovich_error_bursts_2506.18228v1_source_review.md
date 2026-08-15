+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2506.18228"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2506.18228v1"
source_artifact = "outputs/papers/2506.18228.pdf"
source_sha256 = "278f6adb6a48313d1ea21fb6f8775b106996ef373639b6c2e5078c8e9d10826c"
title = "Correlated Error Bursts in a Gap-Engineered Superconducting Qubit Array"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round2/KURILOVICH_ERROR_BURSTS_2506_18228_AUDIT_2026-08-05.md"
audit_packet_sha256 = "055f53beff2bbfc8610b8d2c3f0a05c9cf56c3b270f8d9bfe553dbca5fdc99c1"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/expand_observation_attribution"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]

[[relations]]
predicate = "measures"
object_id = "kurilovich-repetition-bursts"
object_type = "observable"
object_label = "cycle-resolved repetition-code detection bursts"
fact_id = "kurilovich-interleaved-qec-result"

[[relations]]
predicate = "derives"
object_id = "kurilovich-qp-frequency-shift"
object_type = "model"
object_label = "QP-associated reciprocal-recovery model"
fact_id = "kurilovich-qp-kinetic-fit"

[[relations]]
predicate = "uses"
object_id = "kurilovich-controlled-shift"
object_type = "method"
object_label = "controlled uniform frequency-shift injection"
fact_id = "kurilovich-injection-result"

[[relations]]
predicate = "supports"
object_id = "kurilovich-echo-mitigation"
object_type = "observable"
object_label = "detector-level echo mitigation"
fact_id = "kurilovich-control-benefit"

[[relations]]
predicate = "limits"
object_id = "kurilovich-logical-transfer-boundary"
object_type = "limitation"
object_label = "detection bursts rather than burst-conditioned logical errors"
fact_id = "kurilovich-detection-logical-boundary"
+++
# Full-text review — Kurilovich et al., "Correlated Error Bursts in a Gap-Engineered Superconducting Qubit Array"

## Source identity [paper_fact]
Fact ID: kurilovich-source-identity
Source locator: Title page and arXiv identifier in page margin
PDF page: 1
Claim: The fixed source is the 26-page arXiv:2506.18228v1 artifact by Vladislav D. Kurilovich and coauthors, dated 24 June 2025 on the manuscript title page.

The artifact contains the main text, Appendices A–H and embedded Supplementary Materials. The work
was subsequently published in *Physical Review X* 16, 021025 (2026), DOI
`10.1103/1bl4-b2f7`; all evidence locators below refer to the fixed arXiv v1 artifact.

## Selection scope [paper_fact]
Fact ID: kurilovich-selection-scope
Source locator: Abstract; Main Sec. I
PDF page: 1
Claim: The source studies spatially correlated phase-error bursts in a gap-engineered transmon array, develops a quasiparticle-based interpretation of their frequency-shift signature, connects them to repetition-code detector records and tests a circuit-level echo intervention.

Its repeated-QEC outputs are detection events and detection probability, not a newly measured logical
error rate.

## Continuous coherence protocol [paper_fact]
Fact ID: kurilovich-continuous-monitoring
Source locator: Main Sec. III
PDF page: 2
Claim: On each of 60 qubits, the coherence experiment repeats a Ramsey measurement, a spin-echo measurement and a T1 measurement every five microseconds, resets after each measurement and performs 800,000 repetitions per four-second dataset.

The source collected 1,800 such datasets for this experiment. This is a rapid coherence-monitoring
protocol, not an encoded QEC circuit.

## Persistence across qubit resets [paper_fact]
Fact ID: kurilovich-persistent-carrier
Source locator: Main Fig. 3 and Sec. IV.B
PDF page: 4
Claim: In the source's interpretation, a slowly decaying QP population near the Josephson junctions persists across the repeated tomography sequence and its qubit resets, producing frequency shifts that recover over roughly one millisecond.

This supports a distinction between resetting the measured transmon state and eliminating the inferred
physical condition. The QP density is inferred through a model rather than measured directly.

## Ramsey–echo–T1 separation [paper_fact]
Fact ID: kurilovich-timescale-separation
Source locator: Main Sec. III and Fig. 2
PDF page: 3
Claim: Selected bursts appear in Ramsey, spin-echo and T1 records, but Ramsey errors persist for roughly one millisecond whereas echo and T1 errors largely disappear after an initial interval on the order of ten microseconds.

The Ramsey component's suppression by spin echo supports a quasi-static frequency-shift
interpretation. Appendix D gives a more resolved `35 +/- 15 microseconds` duration for reliably fitted
large T1 bursts, so the main-text ten-microsecond value is an order-of-magnitude description.

## Tomographic frequency shifts [paper_fact]
Fact ID: kurilovich-frequency-shifts
Source locator: Main Sec. IV.A and Fig. 3
PDF page: 3
Claim: Time-resolved `R_X/R_Y` tomography finds spatially nonuniform frequency shifts in the MHz range that are negative on all qubits for every selected burst, with the displayed example reaching about `-2.7 MHz` at its epicentre.

The estimate averages ten consecutive measurement pairs over approximately 50 microseconds, which
the source treats as short compared with the millisecond-scale recovery.

## QP frequency-shift relation [paper_fact]
Fact ID: kurilovich-qp-shift-relation
Source locator: Main Sec. IV.B and Eq. (1)
PDF page: 4
Claim: The source relates normalized frequency shift to inferred QP density through `delta-f_q/f_q = -a x_qp`, with `a approximately 0.77` for its stated gap-engineered transmon parameters.

The detailed derivation assumes cold QPs predominantly on the low-gap side and operation near zero
flux bias for this simplified coefficient. The predicted negative sign is part of the attribution
argument.

## QP kinetic fit [paper_fact]
Fact ID: kurilovich-qp-kinetic-fit
Source locator: Main Sec. IV.B, Eqs. (2)–(3) and Fig. 3c
PDF page: 4
Claim: The QP-associated reciprocal-recovery model combines `dx_qp/dt = -r x_qp^2` with the frequency-shift relation, fits the displayed recovery better than an exponential comparator and yields an aggregate `r = 1/(88 +/- 12 ns)` across qubits and bursts.

This is consistency-based attribution to QP recombination. It is not a synchronized measurement of
the initiating external particle.

## Matched-filter detection boundary [paper_fact]
Fact ID: kurilovich-burst-selection
Source locator: Appendix B
PDF page: 9
Claim: The burst-selection procedure uses a 1.5-millisecond exponential matched filter on the array-summed Ramsey-error trace and chooses a threshold whose estimated false-positive rate is below about 2 percent.

The source says the procedure can miss smaller impacts and small events whose durations differ
substantially from one millisecond. Event counts therefore describe the selected class, not all
temporal anomalies or all radiation depositions.

## Tomography burst statistics [paper_fact]
Fact ID: kurilovich-burst-statistics
Source locator: Appendix C and Fig. 8
PDF page: 10
Claim: In 5.2 hours of tomography data, the analysis selects 265 bursts; the median selected burst affects 15 qubits and has a peak frequency-shift magnitude near 2 MHz.

Events affecting more than half of the 60-qubit array occur at the reported rate of roughly one per
22 minutes. These statistics inherit the matched-filter selection boundary.

## Relaxation-burst quantification [paper_fact]
Fact ID: kurilovich-relaxation-bursts
Source locator: Appendix D and Fig. 9
PDF page: 10
Claim: A faster relaxation protocol identifies 142 Ramsey-heralded events in 3.3 hours, with a median T1 burst size of nine qubits and a fitted duration of `35 +/- 15 microseconds` for sufficiently large bursts.

The duration fit is restricted to bursts affecting at least 12 qubits. The recovery is far shorter
than in the cited earlier non-gap-engineered device lineage but still spans many roughly microsecond
QEC cycles.

## Excitation-burst hierarchy [paper_fact]
Fact ID: kurilovich-excitation-bursts
Source locator: Appendix E and Fig. 10
PDF page: 11
Claim: Ground-state dwell measurements show correlated excitation bursts shorter than about five microseconds, spatially overlapping relaxation bursts and containing about half as many errors in the displayed event.

The source interprets the excitation/relaxation timescale hierarchy through different QP energy
thresholds during phonon-mediated cooling. It states that the small, rapidly recovering excitation
sample does not support detailed burst statistics.

## Interleaved repeated-QEC task [paper_fact]
Fact ID: kurilovich-interleaved-task
Source locator: Main Sec. V.A and Fig. 5a–b
PDF page: 5
Claim: The interleaved experiment runs an X-basis repetition code on one qubit region while one Ramsey and two T1 measurements run on an adjacent, disjoint monitor region, with both sequences synchronized to the 944-nanosecond QEC cycle.

A QEC detection is a change between consecutive measure-qubit outcomes. Simultaneity therefore does
not mean that the monitor and QEC records are measurements of identical qubits.

## Natural QEC burst result [paper_fact]
Fact ID: kurilovich-interleaved-qec-result
Source locator: Main Sec. V.A and Fig. 5c–d
PDF page: 6
Claim: Across eight hours, 105 selected events yield cycle-resolved repetition-code detection bursts that generally co-occur with Ramsey-error bursts and have similar durations, with each record usually exceeding the source's stated significance guide when the other is selected.

Events are identified when either the Ramsey or QEC matched-filter trace has a prominent peak.
Borderline cases are associated with bursts concentrated in only one of the two adjacent regions.

## Detection-versus-logical boundary [paper_fact]
Fact ID: kurilovich-detection-logical-boundary
Source locator: Main Sec. VI
PDF page: 7
Claim: The source presents correlated phase-error bursts as a plausible explanation for the repetition-code logical-error-rate floor reported in an earlier study, while its own QEC experiment measures detection bursts rather than burst-conditioned logical errors.

The earlier LER result and the present detector-level result must therefore remain separate evidence
objects.

## Controlled frequency-shift consequence [paper_fact]
Fact ID: kurilovich-injection-result
Source locator: Main Sec. V.B and Fig. 6b–c
PDF page: 6
Claim: Controlled uniform frequency-shift injection applies a `-1 MHz` step to all repetition-code qubits for 15 cycles and raises the original circuit's mean detection probability by 17 percentage points for approximately the injection duration.

The controlled shift is comparable in magnitude with the tomography values and establishes circuit
susceptibility. It does not recreate the natural event's initiating carrier or spatially nonuniform
shift field.

## Circuit control strategy [paper_fact]
Fact ID: kurilovich-control-operation
Source locator: Main Sec. V.B and Fig. 6a
PDF page: 6
Claim: Circuit (ii) recentres data-qubit dynamical decoupling to account for DQLR duration, while circuit (iii) also inserts an echo pulse between measure-qubit Hadamards to cancel coherent phase accumulation through the CZ interval.

These modifications change the physical schedule and gate content. They do not alter decoder access
to temporal history.

## Controlled mitigation result [paper_fact]
Fact ID: kurilovich-control-benefit
Source locator: Main Sec. V.B; Main Sec. VI
PDF page: 7
Claim: The detector-level echo mitigation reduces excess detection under an injected `-1 MHz` shift from 17 percentage points in circuit (i) to 2 points in circuit (iii), while the conclusion reports approximately 35 versus 5 points at `-2 MHz`.

The remaining response is attributed to frequency-detuned one-qubit gates. This is a detector-level
benefit under a controlled uniform shift, not a logical-error or decoder benefit.

## Natural-burst response after circuit modification [paper_fact]
Fact ID: kurilovich-natural-mitigation
Source locator: Main Sec. V.C and Fig. 6d
PDF page: 7
Claim: In the displayed natural event after the circuit-(iii) modification, the repetition-code detection burst is much shorter than the Ramsey tail and aligns more closely with the simultaneous T1 burst.

The main text and supplementary figure provide further selected traces, but the natural events in the
original and modified circuits are separately sampled rather than the same event replayed under both
circuits. No burst-conditioned logical metric is reported.

## Trajectory response model [paper_fact]
Fact ID: kurilovich-qec-response-model
Source locator: Appendix H.3
PDF page: 18
Claim: The injected-shift calculation samples quantum trajectories for circuits with three and five data qubits, includes phase accumulation during two-qubit gates and detuned one-qubit-gate errors, and neglects transmon levels above the computational subspace.

The source reports that the result is insensitive to the two tested system sizes. This model targets
the controlled uniform-shift response, not the generative dynamics of natural bursts.

## Response-model calibration boundary [paper_fact]
Fact ID: kurilovich-qec-model-calibration
Source locator: Appendix H.3 and Fig. 14
PDF page: 19
Claim: The authors call the response model parameter-free while setting a heuristic background bit-flip probability to reproduce the zero-shift detection count, after which the simulated curves agree with all three measured injection-response curves over the plotted range.

The background convention is an empirical calibration even though it is not treated as a free fit
parameter by the source. The appendix also accounts for the flux-shift sensitivity during two-qubit
gates.

## Box-like excluded event class [paper_fact]
Fact ID: kurilovich-box-event-boundary
Source locator: Appendix H.1 and Fig. 12
PDF page: 17
Claim: The analysis excludes 50–250-microsecond box-like events in which two neighbouring measure qubits abruptly approach unit detection probability; transient TLS interaction or leakage of the intervening data qubit are proposed as possible causes.

Neither alternative is established. This filtered class demonstrates that distinct temporal
anomalies in the same record need not share the QP-associated interpretation.

## Basis-variant evidence [paper_fact]
Fact ID: kurilovich-basis-variant
Source locator: Appendix H.2 and Fig. 13
PDF page: 18
Claim: A Z-basis repetition-code variant on the same device also shows detection bursts correlated with Ramsey errors, and adding an echo reduces its response to controlled frequency shifts.

The source attributes the Z-basis sensitivity primarily to phase accumulation on measure qubits. This
is a same-device repetition-code basis variant, not an independent transfer test.

## External-cause boundary [literature_gap]
Fact ID: kurilovich-gap-radiation-tag
Source locator: Appendix B impact-identification procedure
PDF page: 8
Claim: The source does not synchronously detect an external cosmic ray, gamma ray or deposited-particle event for each selected QP-associated burst.
Gap scope: source_local

Events are heralded from qubit-error traces. Comparisons with prior radiation work and an external
energy-deposition simulation support the paper's impact interpretation but do not create a per-event
particle tag.

## Natural-intervention comparator boundary [literature_gap]
Fact ID: kurilovich-gap-natural-comparator
Source locator: Main Sec. V.C; Main Sec. VI
PDF page: 7
Claim: The source does not replay the same natural event under the original and modified circuits or report a cost-normalized population-level comparison of burst-conditioned outcomes across those circuit variants.
Gap scope: source_local

The controlled uniform-shift sweep supplies the cleaner causal comparator; the natural-event traces
are separately sampled support.

## Logical-performance and transfer boundary [literature_gap]
Fact ID: kurilovich-gap-logical-transfer
Source locator: Main Sec. VI
PDF page: 7
Claim: The logical-performance and cross-code transfer boundary is that the source reports no matched logical-error-rate benefit and no transfer to a surface code, independent device or held-out processor.
Gap scope: source_local

The source calls the mechanism a plausible explanation for an earlier repetition-code LER floor and
explicitly cautions that its decoupling strategy may not apply directly to other codes.

## Decoder-benefit boundary [literature_gap]
Fact ID: kurilovich-gap-decoder
Source locator: Main Sec. V; Main Sec. VI
PDF page: 7
Claim: The source does not vary decoder access to burst history or compare a memory-aware decoder with a matched memory-blind decoder.
Gap scope: source_local

All reported mitigation comparisons alter the physical QEC circuit.

## Strict-memory-formalism boundary [literature_gap]
Fact ID: kurilovich-gap-nonmarkovianity
Source locator: Main Sec. VI
PDF page: 7
Claim: The source does not test CP divisibility, information backflow, process-tensor conditional independence or another formal criterion for strict quantum non-Markovianity.
Gap scope: source_local

It studies a persistent inferred physical condition and its multicycle detector signature without
equating those objects to a formal non-Markovianity measure.

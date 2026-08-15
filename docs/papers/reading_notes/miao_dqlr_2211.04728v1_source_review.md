+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2211.04728"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2211.04728v1"
source_artifact = "outputs/reading_packages/simulator_background_top10_2026-07-14/sources/2211.04728v1.pdf"
source_sha256 = "f82e81b7f62dd1ac5d14e27c4d4b6c0b0a81f5aae9e96b1f45973a48d8991e40"
title = "Overcoming leakage in scalable quantum error correction"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round2/MIAO_DQLR_2211_04728_AUDIT_2026-08-05.md"
audit_packet_sha256 = "82a2e8160b1a223a361573a4d049edca924d1e45c0d28d93f7ef7b7dbf71f91b"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/expand_observation_attribution"
admission_date = "2026-08-05"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

[[relations]]
predicate = "derives"
object_id = "miao-leakage-transport"
object_type = "model"
object_label = "leakage-transport resonances"
fact_id = "miao-cz-transport-mechanisms"

[[relations]]
predicate = "uses"
object_id = "miao-dqlr"
object_type = "method"
object_label = "LeakageISWAP"
fact_id = "miao-dqlr-operation"

[[relations]]
predicate = "measures"
object_id = "miao-long-time-detector-correlations"
object_type = "observable"
object_label = "same-stabilizer temporal matrix"
fact_id = "miao-correlation-observable"

[[relations]]
predicate = "supports"
object_id = "miao-dqlr-logical-performance"
object_type = "observable"
object_label = "terminal logical-error probability"
fact_id = "miao-surface-code-logical-result"

[[relations]]
predicate = "limits"
object_id = "miao-within-cycle-leakage"
object_type = "limitation"
object_label = "within-cycle leakage spread"
fact_id = "miao-within-cycle-residual"
+++
# Full-text review — Miao, McEwen et al., "Overcoming leakage in scalable quantum error correction"

## Source identity [paper_fact]
Fact ID: miao-source-identity
Source locator: Title page, arXiv identifier in page margin, and arXiv version record
PDF page: 1
Claim: The fixed source is the 17-page arXiv:2211.04728v1 artifact by Kevin C. Miao, Matt McEwen and coauthors, dated 10 November 2022 on the manuscript title page.

The arXiv record links the work to *Nature Physics* 19, 1780–1786 (2023), DOI
`10.1038/s41567-023-02226-w`. This record fixes the arXiv v1 main text and its embedded
Supplementary Information.

## Selection scope [paper_fact]
Fact ID: miao-selection-scope
Source locator: Abstract; main text opening summary and Sec. 3
PDF page: 1
Claim: The source characterizes long-lived transmon leakage in repeated QEC and compares no reset, measure-qubit multilevel reset, and all-qubit data-qubit leakage removal in distance-3 surface-code and distance-21 bit-flip-code experiments.

The work also uses distance-5 and distance-7 surface-code simulations to examine scaling below the
hardware regime studied experimentally.

## Repeated-QEC leakage persistence [paper_fact]
Fact ID: miao-leakage-persistence
Source locator: Main Sec. 1 and Fig. 1c
PDF page: 2
Claim: After preparing the central data transmon near 50% in `|2>`, the measured excess leakage in the distance-3 surface-code circuit decays with a fitted constant near 4.4 cycles and is transported to other qubits during circuit execution.

One surface-code cycle is stated to last approximately one microsecond. The source distinguishes the
observed circuit decay from the slower decay expected from the prepared qubit's `|2>` relaxation
alone.

## CZ transport mechanisms [paper_fact]
Fact ID: miao-cz-transport-mechanisms
Source locator: Main Sec. 1 and Fig. 2a–c; SI Sec. S1 and Fig. S1
PDF page: 3
Claim: For the Sycamore diabatic CZ, the source identifies `|30> <-> |12>` and `|31> <-> |22>` leakage-transport resonances and measures average relative population transport near 18% and 61%, respectively.

The intended `|20> <-> |11>` CZ rotation is calibrated to `2 pi`. The supplementary derivation gives
the mediated coupling for the `|30> <-> |12>` process and the corresponding sinusoidal transport
model.

## Leakage-conditioned CZ phase [paper_fact]
Fact ID: miao-leakage-conditioned-phase
Source locator: Main Sec. 1 and Fig. 2d–e; SI Fig. S2
PDF page: 3
Claim: A modified Ramsey experiment over 20 qubit pairs measures a phase shift near `0.65 pi` on the lower-frequency qubit when the higher-frequency CZ partner is prepared in `|2>`, instead of the intended computational-state phases near zero or `pi`.

This establishes a gate-level computational-error pathway conditioned on a prepared leakage state; it
does not by itself quantify a logical error.

## Removal-strategy comparators [paper_fact]
Fact ID: miao-removal-comparators
Source locator: Main Sec. 2
PDF page: 4
Claim: The experiments compare no added reset, multilevel reset of measure qubits after each measurement, and DQLR that adds data-qubit leakage removal after the measure-qubit reset.

The source presents these as three distinct repeated-QEC circuit strategies. It notes that MLR adds
data-qubit idle time and that the DQLR arm adds a two-qubit operation and a further reset.

## QEC comparator differences [paper_fact]
Fact ID: miao-qec-comparator-differences
Source locator: SI Sec. S2, No-reset and MLR/DQLR strategy descriptions
PDF page: 12
Claim: The three QEC arms do not have identical detector definitions, operations or duration: no reset compares time-next-neighbouring rather than time-neighbouring measurements, MLR adds a 160 ns reset operation, and DQLR adds a LeakageISWAP and second reset after MLR.

The source says the no-reset detector redefinition has an insignificant effect relative to the
studied leakage effects.

## DQLR operation [paper_fact]
Fact ID: miao-dqlr-operation
Source locator: Main Sec. 2; SI Sec. S2
PDF page: 4
Claim: DQLR first applies multilevel reset to all measure qubits, then applies a LeakageISWAP between paired measure and data qubits, and finally resets the measure qubits again so that data `|2>` population is transported to a qubit that is reset.

The LeakageISWAP acts in the `|11>`–`|20>` subspace. Its removal action depends on the preceding
measure-qubit reset preparing `|0>`.

## DQLR reset-failure pathway [paper_fact]
Fact ID: miao-dqlr-reset-dependence
Source locator: SI Sec. S2, paragraph beginning "For DQLR"
PDF page: 12
Claim: If the preceding measure-qubit reset leaves `|1>`, the LeakageISWAP can convert that reset error into data-qubit leakage, although the source reports that this pathway is sufficiently rare not to raise the measured data leakage population.

This is a physical/calibration dependency of the removal protocol rather than a decoder assumption.

## Steady-state leakage comparison [paper_fact]
Fact ID: miao-steady-leakage-result
Source locator: Main Fig. 3a–c and Sec. 2
PDF page: 4
Claim: Across 30 distance-3 surface-code cycles, no reset produces data and measure leakage approaching 5% and 3%, MLR holds measure leakage near `3 x 10^-4` but leaves data leakage above 1.5%, and DQLR stabilizes data leakage near `10^-3` and measure leakage below `10^-4`.

Moment-resolved measurements in cycles 25–30 show leakage produced during a cycle and then removed
by DQLR, with data leakage rising from about `10^-3` to about `5 x 10^-3` before removal.

## DQLR operation cost [paper_fact]
Fact ID: miao-dqlr-xeb-cost
Source locator: SI Sec. S2 and Fig. S3
PDF page: 12
Claim: Cross-entropy benchmarking on nine data–measure pairs reports mean DQLR XEB error below `2.5 x 10^-3` per cycle and no significant excess over idling for the same duration.

The source cautions that XEB counts leakage as an incoherent error, so leakage removal can make the
DQLR arm appear more favourable than an idle arm in which leakage accumulates.

## Bit-flip-code injection comparison [paper_fact]
Fact ID: miao-bit-flip-injection-result
Source locator: Main Fig. 4 and Sec. 3
PDF page: 5
Claim: In the distance-21 bit-flip code run for 60 cycles, injected leakage is far more damaging than matched plotted Pauli injection under no reset or MLR, whereas the two injection-response curves are much closer under DQLR.

The source uses `theta_L = 2 sin^-1(sqrt(2 P_L))` and
`theta_P = 2 sin^-1(sqrt(P_P))`: the factor of two is inside the leakage-population relation because
leakage injection acts only on population initially in `|1>`. The plotted comparison is not an
equality proof between the two channels.

## Bit-flip time-stability result [paper_fact]
Fact ID: miao-bit-flip-time-result
Source locator: SI Sec. S4 and Fig. S5
PDF page: 14
Claim: With 1% leakage injected per cycle, the distance-21 bit-flip code remains below `5 x 10^-3` logical-error probability through 60 cycles under DQLR, while MLR reaches about `10^-2` by 30 cycles.

The curves report logical-error probability after each displayed cycle count. The source notes early-cycle
boundary and sampling effects.

## Surface-code detection stability [paper_fact]
Fact ID: miao-surface-detection-result
Source locator: Main Fig. 5a and Sec. 3; SI Fig. S6
PDF page: 14
Claim: In the distance-3 surface-code experiment, average detection probability rises throughout the run with no reset, rises by about 2.5 percentage points during the first 15 cycles with MLR, and rapidly stabilizes under DQLR at about 18% for weight-4 and 11% for weight-2 stabilizers.

The source attributes the temporal stabilization to recurrent removal of leakage from all qubits.

## Surface-code logical result [paper_fact]
Fact ID: miao-surface-code-logical-result
Source locator: Main Fig. 5b and Sec. 3
PDF page: 6
Claim: For the distance-3 surface code after 15 cycles and across the tested leakage-injection range, DQLR has the lowest plotted terminal logical-error probability of the three removal strategies despite its additional operations and cycle time.

This result concerns a small hardware code close to threshold and does not establish asymptotic
error suppression.

## Below-threshold simulated comparison [paper_fact]
Fact ID: miao-distance-five-seven-simulation
Source locator: Main Fig. 5c and Sec. 3
PDF page: 6
Claim: In the declared distance-5 and distance-7 surface-code simulations, increasing injected leakage makes `1/Lambda_5/7` rise rapidly and nonlinearly under MLR but more slowly and approximately linearly under DQLR over the tested range.

The calculation uses a hypothetical below-threshold device rather than the experimental distance-3
hardware regime.

## Below-threshold simulation assumptions and fit [paper_fact]
Fact ID: miao-distance-five-seven-fit
Source locator: SI Sec. S6 and Table S1
PDF page: 15
Claim: The distance-5/7 simulation sets baseline intrinsic leakage to zero, includes leakage transport, leakage phase errors and removal parameters, and reports the DQLR fit `1/Lambda_5/7 approximately 111 P_L + 0.2` with `R^2 = 0.983`.

The fit's linearity is used by the source to motivate an effective uncorrelated-error description in
the tested simulated regime; it is not a hardware measurement.

## Correlation observable [paper_fact]
Fact ID: miao-correlation-observable
Source locator: SI Sec. S7, Eq. (S6)
PDF page: 15
Claim: The source averages detector-graph edge probabilities `p_ij` at fixed stabilizer coordinate to define a same-stabilizer temporal matrix `p-bar_(t,t')` over arbitrary cycle separations.

Within this detector-graph convention, separation-one edges are the ordinary timelike comparison and
larger separations expose non-local temporal structure.

## Nearest-neighbour correlation observable [paper_fact]
Fact ID: miao-nearest-neighbour-correlation-observable
Source locator: SI Sec. S7, Eq. (S7)
PDF page: 16
Claim: The source separately averages detector-graph edge probabilities over nearest-neighbour stabilizer pairs to characterize long-diagonal temporal correlations.

For separations greater than one cycle, the source says the remaining correlations predominantly
arise from leakage and crosstalk after excluding ordinary nearest-cycle CZ diagonal edges.

## Experimental correlation suppression [paper_fact]
Fact ID: miao-correlation-suppression
Source locator: SI Sec. S7 and Fig. S7
PDF page: 16
Claim: In cycles 19–29 of the distance-3 surface-code experiment, the same-stabilizer DQLR correlation magnitude is about `2 x 10^-3` at separation two and below 0.2% at larger separations through ten, whereas MLR remains above 0.1% at separation ten and no reset remains above 1% throughout the tested range.

The figure caption says DQLR magnitudes do not exceed `2 x 10^-3`, while the prose says they exceed
that value only at separation two; the rounded claim above preserves this source-level discrepancy.
The one-standard-deviation bars prevent resolving DQLR variations below `10^-3`. The
nearest-neighbour analysis shows the same ordering among the three strategies.

## Within-cycle residual [paper_fact]
Fact ID: miao-within-cycle-residual
Source locator: Main Sec. 2 closing paragraph and Sec. 3 discussion of simulation agreement
PDF page: 5
Claim: DQLR confines the measured leakage dynamics largely to one cycle, but the source retains within-cycle leakage spread and a small underestimation of injected-leakage logical error by simulation as unresolved limitations.

Removal between cycles therefore does not imply the absence of correlated error within a cycle.

## Phenomenological-fit boundary [paper_fact]
Fact ID: miao-fit-boundary
Source locator: SI Sec. S5, Eqs. (S1)–(S3)
PDF page: 14
Claim: The logical-error-per-cycle conversion and offset power law are introduced as phenomenological fit models, and the source explicitly assigns no physical meaning to the offset parameter `P_0`.

These fits describe the displayed data; they are not mechanism-identification equations.

## Time-dependent phenomenological fit [paper_fact]
Fact ID: miao-gompertz-fit-boundary
Source locator: SI Sec. S5, Eq. (S5)
PDF page: 15
Claim: The source uses a three-parameter Gompertz model as a phenomenological description of bit-flip-code logical error per cycle while leakage populations and boundary effects evolve with cycle number.

At large cycle number the model tends to a constant as leakage populations stabilize; the source
does not present it as a microscopic leakage equation.

## Strict-memory-formalism boundary [literature_gap]
Fact ID: miao-gap-nonmarkovianity
Source locator: Full-text scope, including main Secs. 1–4 and SI Secs. S1–S7
PDF page: 7
Claim: The source does not test CP divisibility, information backflow, a process-tensor memory witness, or another criterion for strict quantum non-Markovianity.
Gap scope: source_local

It studies a long-lived leakage state and multicycle detector structure without equating those objects
to a formal non-Markovianity measure.

## Decoder-benefit boundary [literature_gap]
Fact ID: miao-gap-decoder-benefit
Source locator: Main Sec. 3 and Figs. 4–5; SI Secs. S4–S7
PDF page: 6
Claim: The source does not vary decoder access to leakage history or compare a memory-aware decoder with a matched memory-blind decoder.
Gap scope: source_local

The manipulated factor is the physical leakage-removal strategy.

## Strictly matched QEC-comparator boundary [literature_gap]
Fact ID: miao-gap-strict-qec-comparator
Source locator: Main Secs. 2–3 and Figs. 3–5; SI Sec. S2 and Fig. S3
PDF page: 12
Claim: The source does not compare DQLR with a QEC arm matched in cycle duration, operations and detector definition; its equal-duration idle comparison is limited to the separate XEB experiment.
Gap scope: source_local

The code and hardware tasks are common across the intervention arms, but this is not a strict
one-factor QEC-record contrast.

## Robustness boundary [literature_gap]
Fact ID: miao-gap-robustness
Source locator: Main Sec. 3 and SI Secs. S2, S6
PDF page: 12
Claim: The source does not systematically vary leakage-model misspecification, reset calibration error, or decoder-model error while holding the repeated-QEC task fixed.
Gap scope: source_local

Its reported experiment–simulation difference and reset-failure pathway identify limitations but do
not constitute a robustness sweep.

## Transfer boundary [literature_gap]
Fact ID: miao-gap-transfer
Source locator: Abstract; main Secs. 2–4; SI Secs. S2–S7
PDF page: 7
Claim: The source does not transfer a fixed calibrated removal policy to an independently held-out processor, hardware platform, or code family.
Gap scope: source_local

The two hardware code experiments and two larger simulated distances establish breadth within the
study, not controlled transfer.

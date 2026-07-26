+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2607.17204"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2607.17204v1"
source_artifact = "docs/papers/2607.17204v1.pdf"
source_sha256 = "cb33dbc5eaddb400c0e04b63dfc9be199adfef2797e3133996b6aea32b0ed889"
title = "Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/LEAKAGE_FRAME_LITERATURE_CLOSURE_2026-07-26.md"
audit_packet_sha256 = "c8ee8d0157fc5f1bc9c9cb0e208518a3579e103611d8fcaf114d4d450c04982b"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_miyamura_source_review"
admission_date = "2026-07-26"
visually_checked_pages = [1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

[[relations]]
predicate = "defines"
object_id = "miyamura.direct-leakage-measurement"
object_type = "method"
object_label = "direct binary leakage measurement"
fact_id = "miyamura.mechanism"

[[relations]]
predicate = "measures"
object_id = "miyamura.binary-assignment"
object_type = "observable"
object_label = "balanced detection fidelity"
fact_id = "miyamura.assignment"

[[relations]]
predicate = "measures"
object_id = "miyamura.conditional-state-fidelity"
object_type = "observable"
object_label = "conditional average state fidelity"
fact_id = "miyamura.state-fidelity"

[[relations]]
predicate = "supports"
object_id = "miyamura.binary-projection"
object_type = "model"
object_label = "binary projection character"
fact_id = "miyamura.projection"

[[relations]]
predicate = "limits"
object_id = "miyamura.qec-projection-only"
object_type = "limitation"
object_label = "error-correction-regime projection"
fact_id = "miyamura.qec-projection"
+++
# Full-text review -- Miyamura et al., "Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon"

## Source identity [paper_fact]
Fact ID: miyamura.source
Source locator: PDF p. 1, title, author, date, and arXiv block
PDF page: 1
Claim: Takeaki Miyamura and coauthors report arXiv:2607.17204v1, a preprint on heralded leakage detection in a fixed-frequency transmon.

The title page is dated July 21, 2026 and the arXiv margin records July 19, 2026.

## Scientific scope [paper_fact]
Fact ID: miyamura.scope
Source locator: Abstract and final introduction paragraph
PDF page: 1
Claim: The source investigates a direct leakage measurement intended to distinguish the transmon leakage sector while retaining information within the computational subspace.

The experiment uses one transmon and its readout resonator rather than repeated stabilizer outcomes.

## Driven dispersive mechanism [paper_fact]
Fact ID: miyamura.mechanism
Source locator: Fig. 1 and accompanying text
PDF page: 2
Claim: The direct binary leakage measurement applies a near-resonant computational-transition Rabi drive during dispersive probing so the resonator responses of ground and first-excited states merge while the measured second-excited-state response remains distinct.

The second excited state is denoted f in the experiment.

## Dressed-noise frequency shift [paper_fact]
Fact ID: miyamura.noise-frequency
Source locator: Supplemental Sec. II.C, Eqs. (S6)-(S11)
PDF page: 10
Claim: In the two-level dressed-state treatment, the drive shifts computational-block photon-number-noise sensitivity from zero frequency to the Rabi frequency.

## Finite-anharmonicity clock condition [paper_fact]
Fact ID: miyamura.clock-condition
Source locator: Supplemental Eqs. (S13)-(S18) and paragraph following Eq. (S18)
PDF page: 11
Claim: In the three-level model, finite anharmonicity produces a longitudinal dressed-state number difference, and the leading-order clock condition chooses a small drive detuning so that delta N equals zero.

The source states that higher-order corrections are significant at the experimental operating point.

## Binary assignment performance [paper_fact]
Fact ID: miyamura.assignment
Source locator: Fig. 3 and Eq. (5)
PDF page: 4
Claim: For prepared ground, first-excited, and second-excited states, an eighty-nanosecond window gives false-flag rate 2.3(3) percent, undetected-leakage rate 3.5(2) percent, and balanced detection fidelity 97.1(3) percent.

The corresponding second-excited-state true-positive probability is 96.5 percent; it is not identical to the balanced metric.

## Detection-error decomposition [paper_fact]
Fact ID: miyamura.error-decomposition
Source locator: Supplemental Sec. III, Eqs. (S24)-(S25)
PDF page: 13
Claim: The binary assignment errors are decomposed into signal-separation errors and state transitions occurring before or after the classification decision.

The false-flag and undetected-leakage errors include separation and early-flip contributions; late flips occur after the classification decision.

## Detection-error budget [paper_fact]
Fact ID: miyamura.error-budget
Source locator: Supplemental Table III
PDF page: 12
Claim: The reported ge-to-f and f-to-ge separation errors are 2.1(2) and 1.9(1) percent, the corresponding early-flip errors are 0.2(2) and 1.6(1) percent, and the late-flip errors are 0.1(1) and 1.5(1) percent.

## Recovery gate [paper_fact]
Fact ID: miyamura.recovery
Source locator: Supplemental Sec. V
PDF page: 13
Claim: A calibrated Euler recovery gate approximately reverses the drive-induced rotation within the computational subspace after detection.

Its Z rotations are virtual control-reference updates, and its parameters are optimized across six cardinal input states.

## Conditional state fidelity [paper_fact]
Fact ID: miyamura.state-fidelity
Source locator: Fig. 4 and accompanying text
PDF page: 5
Claim: For a target equal mixture of computational and second-excited-state population, no-leakage post-selection gives conditional average state fidelity 92.9(5) percent over six cardinal states.

This fidelity characterizes the post-selected computational block rather than the binary classifier alone.

## Conditional process fidelity [paper_fact]
Fact ID: miyamura.process-fidelity
Source locator: Fig. 4d and accompanying text
PDF page: 5
Claim: The Pauli transfer matrix of the conditional detection process at target leakage population one half gives an average process fidelity of 93.5(5) percent.

## Residual back-action [paper_fact]
Fact ID: miyamura.backaction
Source locator: Fig. 4e and discussion
PDF page: 5
Claim: The reported conditional-infidelity curve approaches about 4.7 percent as the prepared leakage population tends to zero; the measured input range is 0.10 through 0.90.

The authors attribute the nonzero limit to residual measurement-induced dephasing under the Rabi drive.

## Binary projection character [paper_fact]
Fact ID: miyamura.projection
Source locator: Supplemental Sec. VII and Fig. S7
PDF page: 15
Claim: The binary projection character is supported by a coherent three-level input whose ground-first coherence is largely retained while ground-second and first-second coherences are strongly suppressed.

After selecting the no-leakage outcome, the reported fidelity to the computational plus state is 94.7(8) percent.

## Intended POVM [paper_fact]
Fact ID: miyamura.povm
Source locator: Supplemental Sec. VII, opening sentence
PDF page: 14
Claim: The idealized measurement is expected to have POVM elements given by the second-excited-state projector and its complement.

## Conditional-fidelity model [paper_fact]
Fact ID: miyamura.fidelity-model
Source locator: Supplemental Sec. VI, Table IV and Eqs. (S26)-(S28)
PDF page: 14
Claim: The conditional-fidelity model enumerates sixteen separation-and-transition pathways, of which rows 1, 2, 7, 8, 11, 12, 13, and 14 declare the no-leakage ge outcome and enter the conditional ensemble.

Its leading-order expression separates computational back-action from contamination by missed leakage.

## Conditional-path fidelity assignments [paper_fact]
Fact ID: miyamura.fidelity-paths
Source locator: Supplemental Table IV and text immediately below it
PDF page: 14
Claim: Among the eight declared-ge pathways, rows 2, 7, 11, and 14 receive zero fidelity; rows 8, 12, and 13 receive one-half; and row 1 receives the retained computational-state fidelity.

The pathways declared f are marked with dashes and do not belong to the conditional ensemble.

## Error-correction-regime projection [paper_fact]
Fact ID: miyamura.qec-projection
Source locator: Supplemental Sec. IX, opening paragraphs
PDF page: 16
Claim: The error-correction-regime projection assumes leakage population below about one percent and treats post-detection ge-to-f late flips as flagged in the subsequent detection cycle, so that contribution is not counted as an unheralded error.

It predicts device back-action under optimized filter parameters.

## Excess-noise prerequisite [paper_fact]
Fact ID: miyamura.excess-noise
Source locator: Supplemental Sec. IX.C, final paragraph
PDF page: 17
Claim: The measured driven measurement-induced dephasing is about three times the model prediction, its origin is unidentified, and its removal is a prerequisite for the projected performance.

The source suggests excess probe-associated noise as a possible cause without establishing it.

## Error-correction demonstration absent [literature_gap]
Fact ID: miyamura.gap-qec
Source locator: Abstract, main-text conclusion, and Supplemental Sec. IX
PDF page: 17
Claim: The source does not execute an error-correction circuit or decoder and reports no stabilizer detector record, logical error rate, or threshold.
Gap scope: source_local

Decoder use is motivation, and the quantitative error-correction discussion is a device-model projection.

## Stabilizer-frame analysis absent [literature_gap]
Fact ID: miyamura.gap-frame
Source locator: Full-text operation scope; local recovery-frame definition in Supplemental Sec. V
PDF page: 13
Claim: The source does not analyze a transversal data echo, effective stabilizer checks, a logical Pauli frame, or a trajectory-conditioned circuit-frame correction.
Gap scope: source_local

Its virtual Z reference updates calibrate the local recovery gate.

## Parity-string inference absent [literature_gap]
Fact ID: miyamura.gap-parity
Source locator: Introduction paragraph contrasting repeated-stabilizer inference with direct measurement
PDF page: 1
Claim: The source does not derive leakage information from a parity-outcome or detector sequence.
Gap scope: source_local

The demonstrated observable is an additional direct binary measurement outcome.

## Complete instrument characterization absent [literature_gap]
Fact ID: miyamura.gap-instrument
Source locator: Supplemental Sec. VII and Fig. S7
PDF page: 15
Claim: The source does not reconstruct the complete outcome-conditioned measurement instrument or bound repeated-measurement nondemolition behavior.
Gap scope: source_local

It provides state tomography for one coherent qutrit input.

## Higher-level assignment absent [literature_gap]
Fact ID: miyamura.gap-higher-levels
Source locator: Abstract and Fig. 1 discussion compared with Fig. 3 calibration
PDF page: 4
Claim: Although the source discusses the second and higher excited states, its reported assignment matrix and detection fidelity characterize prepared second-excited state only.
Gap scope: source_local

No separate assignment matrix is reported for higher transmon levels.

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2603.20127"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2603.20127v1"
source_artifact = "outputs/overview/literature/coverage_validation/analyzing_decoders/2603.20127v1.pdf"
source_sha256 = "cf38579a83b0b21d2bb9f1bf2ee41249259e68c502589ffec446856eb5aebe90"
title = "Analyzing Decoders for Quantum Error Correction"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/literature_expansion_round3/MOLAVI_DECODER_ROBUSTNESS_2603_20127_AUDIT_2026-08-05.md"
audit_packet_sha256 = "34468763c454d523aac89a1c4e9c4cfcac463e296c70f1e07a1189800d087b24"
admission_status = "source_only_reviewed"
admission_reviewer = "/root/validate_ziad"
admission_date = "2026-08-05"
visually_checked_pages = [1, 6, 7, 10, 11, 12, 13, 15, 17, 18, 20, 21, 24]

[[relations]]
predicate = "defines"
object_id = "molavi-symbolic-qec-program"
object_type = "model"
object_label = "symbolic QEC program"
fact_id = "molavi-symbolic-program"

[[relations]]
predicate = "defines"
object_id = "molavi-decoder-robustness"
object_type = "observable"
object_label = "maximum logical error rate"
fact_id = "molavi-robustness-definition"

[[relations]]
predicate = "uses"
object_id = "molavi-enumerative-polynomial-analysis"
object_type = "method"
object_label = "structured enumeration of error bitstrings"
fact_id = "molavi-computation"

[[relations]]
predicate = "limits"
object_id = "molavi-independent-error-scope"
object_type = "limitation"
object_label = "independent Bernoulli random variable"
fact_id = "molavi-independent-error-scope"
+++
# Full-text review — Molavi et al., “Analyzing Decoders for Quantum Error Correction”

## Source identity [paper_fact]
Fact ID: molavi-source-identity
Source locator: Title page and arXiv version stamp
PDF page: 1
Claim: The fixed source is the 29-page arXiv:2603.20127v1 preprint by Abtin Molavi, Feras Saad and Aws Albarghouthi, dated 20 March 2026.

The artifact includes the formal development, evaluation, related work, conclusion, proofs and
references.

## Study scope [paper_fact]
Fact ID: molavi-study-scope
Source locator: Abstract; Sec. 1
PDF page: 1
Claim: The source develops a systematic method for estimating decoder logical error rate and worst-case sensitivity to uncertain physical error probabilities for QEC programs represented in a Stim-like language.

The work is a formal and synthetic decoder-evaluation study, not a hardware experiment or a
temporal-memory inference study.

## QEC-program representation [paper_fact]
Fact ID: molavi-qec-program
Source locator: Sec. 4; Fig. 3
PDF page: 7
Claim: A QEC program is represented as a straight-line quantum circuit with reset, measurement, gate and probabilistic Pauli-error statements plus syndrome and logical-observable declarations.


## Stim-to-DEM implementation [paper_fact]
Fact ID: molavi-stim-dem
Source locator: Sec. 8, implementation paragraph, p. 17
PDF page: 17
Claim: The implemented analysis compiles Stim circuits to detector error models whose error events carry probabilities and deterministic effects on syndrome and logical-observable bits.

This compilation supplies the finite independent-event abstraction used by the evaluation; it does
not introduce a continuing carrier or correlated event draws.

## Independent error-operation scope [paper_fact]
Fact ID: molavi-independent-error-scope
Source locator: Sec. 5, first two paragraphs
PDF page: 11
Claim: Each error-channel statement is treated as an independent Bernoulli random variable, so the probability of an error bitstring factors into products of channel probabilities and complements.

The formalism demonstrated in the paper does not introduce correlated draws, a persistent carrier
or a hidden temporal state.

## Symbolic QEC program [paper_fact]
Fact ID: molavi-symbolic-program
Source locator: Sec. 4.2, “Symbolic qec programs”
PDF page: 10
Claim: A symbolic QEC program replaces fixed physical error probabilities by variables and maps each concrete assignment of those variables to a concrete QEC program.

## Accuracy definition [paper_fact]
Fact ID: molavi-accuracy-definition
Source locator: Sec. 3, Definition 3.1
PDF page: 6
Claim: Decoder accuracy is evaluated through logical error rate, defined as the probability that the decoder's predicted logical observable differs from the program's logical observable.

## Robustness definition [paper_fact]
Fact ID: molavi-robustness-definition
Source locator: Sec. 3, Definition 3.2
PDF page: 6
Claim: Decoder robustness is defined as the maximum logical error rate of a fixed decoder over a constrained set of concrete parameter assignments to a symbolic QEC program.

The demonstrated constraint sets are hyperrectangles over individual physical error rates.

## Polynomial reduction [paper_fact]
Fact ID: molavi-polynomial-reduction
Source locator: Theorems 5.4 and 5.5
PDF page: 11
Claim: The source reduces decoder accuracy to evaluation of an error polynomial and robustness to constrained maximization of that polynomial.

## Enumeration and sound bounds [paper_fact]
Fact ID: molavi-computation
Source locator: Sec. 6, Algorithm 1, p. 13
PDF page: 13
Claim: The analysis uses structured enumeration of error bitstrings to accumulate decoder-success and decoder-failure mass and construct sound lower and upper error-polynomial bounds for unexplored strings.

## Hyperrectangle optimization [paper_fact]
Fact ID: molavi-hyperrectangle-optimization
Source locator: Sec. 6.2, Algorithm 2 and Theorem 6.7, p. 15
PDF page: 15
Claim: For a hyperrectangle, the optimizer uses multilinearity and partial-derivative signs to fix certified coordinates and exhaustively searches the remaining vertices to obtain extrema of each explored-set bound polynomial.

This is exact for the declared finite rate box and polynomial bound, not for a correlated or
time-dependent uncertainty set.

## Accuracy-only sampling hybrid [paper_fact]
Fact ID: molavi-accuracy-sampling
Source locator: Sec. 7, Theorem 7.1, p. 17
PDF page: 17
Claim: For Accuracy, an optional conditional-sampling hybrid estimates the unexplored probability mass and constructs a Chernoff confidence interval, while the source does not use that step to make the robustness bounds probabilistic.

## Demonstrated QEC task [paper_fact]
Fact ID: molavi-qec-task
Source locator: Sec. 8, “qec program benchmarks”
PDF page: 18
Claim: The empirical evaluation uses rotated-surface-code memory circuits at distances 3, 5, 7 and 9 with round counts up to the distance under the independent `si1000` noise model at three scalar strengths.

## Decoder set [paper_fact]
Fact ID: molavi-decoder-set
Source locator: Sec. 8, “Decoders”
PDF page: 18
Claim: The evaluated decoder functions are PyMatching, BP+OSD and Relay-BP.

## Robustness protocol [paper_fact]
Fact ID: molavi-robustness-protocol
Source locator: Sec. 8.2, first paragraph
PDF page: 20
Claim: Each robustness benchmark allows every nominal Bernoulli channel parameter to vary independently between 0.9 and 1.1 times its nominal value.

This is a static rate-uncertainty set, not a temporal drift trajectory.

## Robustness result [paper_fact]
Fact ID: molavi-robustness-result
Source locator: Sec. 8.2; Fig. 11
PDF page: 21
Claim: Among the robustness configurations summarized in Fig. 11, the largest reported nominal-to-worst-case logical-error gap is 28.6 percent for Relay-BP, versus 21.6 percent for BP+OSD and 21.7 percent for PyMatching.

For the distance-3, three-round, `p=0.001` instance, the ranking of Relay-BP and BP+OSD differs
between nominal accuracy and worst-case robustness. The prose calls these “6 programs,” whereas the
figure shows seven labelled parameter groups and incomplete decoder convergence in several groups;
the note does not resolve that count.

## Robustness reach [paper_fact]
Fact ID: molavi-robustness-reach
Source locator: Sec. 8.2, paragraphs around Fig. 11
PDF page: 21
Claim: The largest robustness problem reported as meeting the source's finite-resource convergence criterion is a distance-3, three-round circuit containing 286 error-channel variables.

Larger accuracy benchmarks do not imply equally large robustness certification.

## Wrong-memory-law boundary [literature_gap]
Fact ID: molavi-gap-memory-law
Source locator: Secs. 3–6 and complete robustness specification
PDF page: 12
Claim: The source does not perturb or misspecify a continuing carrier, hidden-state transition, temporal kernel, history dependence, correlation topology or mixed memory mechanism.
Gap scope: source_local

Its positive robustness result is limited to independently bounded channel-rate uncertainty.

## Hardware and transfer boundary [literature_gap]
Fact ID: molavi-gap-hardware-transfer
Source locator: Complete evaluation scope in Sec. 8
PDF page: 18
Claim: The source does not evaluate experimental QEC records, online adaptation or frozen transfer across devices, code families or memory models.
Gap scope: source_local

## Future-scope boundary [paper_fact]
Fact ID: molavi-future-scope
Source locator: Sec. 10, Conclusion, p. 24
PDF page: 24
Claim: The source identifies robustness sets beyond hyperrectangles and decoder construction with robustness guarantees as future directions rather than completed demonstrations.

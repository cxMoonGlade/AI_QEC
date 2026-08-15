+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1905.12731"
source_version = "v1"
source_uri = "https://arxiv.org/abs/1905.12731v1"
source_artifact = "docs/papers/1905.12731v1.pdf"
source_sha256 = "b7f831dc66b329d583c892483160c937b773dec1cc2f52edf33b32e15d1b563d"
title = "Protecting quantum entanglement from qubit errors and leakage via repetitive parity measurements"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/LEAKAGE_FRAME_LITERATURE_CLOSURE_2026-07-26.md"
audit_packet_sha256 = "c8ee8d0157fc5f1bc9c9cb0e208518a3579e103611d8fcaf114d4d450c04982b"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_bultink_source_review"
admission_date = "2026-07-26"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

[[relations]]
predicate = "measures"
object_id = "bultink.repetitive-parity-record"
object_type = "observable"
object_label = "parity-outcome string"
fact_id = "bultink.leakage-pattern"

[[relations]]
predicate = "defines"
object_id = "bultink.data-leakage-syndrome"
object_type = "observable"
object_label = "data-leakage syndrome"
fact_id = "bultink.zz-syndrome"

[[relations]]
predicate = "defines"
object_id = "bultink.computational-likelihood"
object_type = "observable"
object_label = "computational-subspace likelihood"
fact_id = "bultink.hmm-posterior"

[[relations]]
predicate = "supports"
object_id = "bultink.echo-breaks-paralysis"
object_type = "method"
object_label = "echo pulse breaks leakage paralysis"
fact_id = "bultink.echo-break"

[[relations]]
predicate = "defines"
object_id = "bultink.effective-parity-check"
object_type = "model"
object_label = "effective N-minus-one-qubit parity check"
fact_id = "bultink.effective-check"

+++
# Full-text review -- Bultink et al., "Protecting quantum entanglement from qubit errors and leakage via repetitive parity measurements"

## Source identity [paper_fact]
Fact ID: bultink.source
Source locator: PDF artifact metadata and p. 1 title and author block
PDF page: 1
Claim: The persisted source is the thirteen-page arXiv:1905.12731v1 preprint by C. C. Bultink and coauthors, submitted on May 29, 2019.

Locators in this note refer only to the v1 artifact.

## Scientific scope [paper_fact]
Fact ID: bultink.scope
Source locator: Abstract and introduction, PDF p. 1
PDF page: 1
Claim: The source experimentally studies repeated ZZ checks and interleaved ZZ and XX checks on two data transmons and one ancilla, using parity outcomes to detect leakage with hidden Markov models.

It mitigates inferred leakage by post-selection and tracks ordinary qubit corrections with Pauli-frame updates.

## Pauli-frame update [paper_fact]
Fact ID: bultink.pfu
Source locator: Main text accompanying Fig. 1, PDF p. 2
PDF page: 2
Claim: When the first ancilla outcome is minus one, the protocol records a fixed Pauli-frame X update on the high-frequency data qubit instead of applying that correction in real time.

The update is incorporated into tomography when reconstructing the Bell state.

## Physical data echo [paper_fact]
Fact ID: bultink.echo-placement
Source locator: Fig. 1A caption and paragraph following the parity-assignment results, PDF p. 2
PDF page: 2
Claim: Echo pulses are applied to both data qubits halfway through the ancilla measurement to reduce intrinsic dephasing and cancel residual data-ancilla coupling.

The echo pulses are physical circuit operations and are distinct from the Pauli-frame update used in tomography.

## Repeated-ZZ leakage pattern [paper_fact]
Fact ID: bultink.leakage-pattern
Source locator: Main text following Fig. 2, paragraph beginning with leakage inference from the outcome string
PDF page: 3
Claim: Data-qubit leakage produces an apparent-error parity-outcome string with pairs of equal signs, exemplified by plus, plus, minus, minus, because the echo pulses act only on the unleaked data qubit.

## Leakage pattern is non-unique [paper_fact]
Fact ID: bultink.pattern-nonunique
Source locator: Main text following Fig. 2, final sentence of the leakage-pattern paragraph
PDF page: 3
Claim: Ordinary error combinations can produce the same paired-sign pattern, so the pattern is not an unambiguous leakage label.

## Hidden-state inference [paper_fact]
Fact ID: bultink.hmm-posterior
Source locator: Main text following Fig. 2, HMM definition paragraph
PDF page: 3
Claim: The hidden Markov model returns a computational-subspace likelihood from the observed parity-outcome string by alternating Markov evolution with Bayesian measurement updates.

Separate models are trained for ancilla leakage and data-qubit leakage.

## Repeated-ZZ temporal syndrome [paper_fact]
Fact ID: bultink.zz-syndrome
Source locator: Supplemental Sec. II.A, data-qubit leakage model
PDF page: 10
Claim: The repeated-ZZ data-leakage syndrome is defined as the product of ancilla outcomes two rounds apart, sD at round m equals MA at m times MA at m-minus-two.

An isolated data-qubit error gives one negative syndrome value, whereas an ancilla error gives two consecutive negative values in this representation.

## Interleaved temporal syndrome [paper_fact]
Fact ID: bultink.interleaved-syndrome
Source locator: Supplemental Sec. II.A, paragraph on interleaved ZZ and XX checks
PDF page: 10
Claim: For interleaved ZZ and XX checks, classical post-processing defines the data syndrome as the product of four consecutive ancilla outcomes.

This post-processing removes the intended alternation between the two check types before hidden-state inference.

## Random interleaved output [paper_fact]
Fact ID: bultink.random-interleaved
Source locator: Supplemental Sec. II.A, paragraph defining the seventeen-state model
PDF page: 10
Claim: In the interleaved experiment, data leakage makes the ancilla output entirely random with a model error probability of one half.

## Fitted interleaved leaked-state error [paper_fact]
Fact ID: bultink.random-interleaved-fit
Source locator: Supplemental Table S2, HZZ,XX-D data-error row
PDF page: 11
Claim: The fitted leaked-state data-error parameter for the interleaved hidden model is 0.489.

## Leakage-paralysis phase [paper_fact]
Fact ID: bultink.paralysis-phase
Source locator: Supplemental Sec. II.B, paragraph beginning with leakage paralysis
PDF page: 11
Claim: The source describes leakage paralysis when the relative phase accumulated between states |20> and |21> during a CZ is an integer multiple of pi.

At relative phase pi over two, the same paragraph says the ancilla outcomes are random.

## Effective parity check [paper_fact]
Fact ID: bultink.effective-check
Source locator: Supplemental Sec. II.B, paragraph beginning with an N-qubit parity check
PDF page: 11
Claim: A leaked site reduces an N-qubit stabilizer measurement to an effective N-minus-one-qubit parity check plus a fixed phase from the leaked interaction.

## Echo breaks paralysis [paper_fact]
Fact ID: bultink.echo-break
Source locator: Supplemental Sec. II.B, parenthetical sentence after the ZZ-and-XX effective-check example
PDF page: 11
Claim: In the repeated-ZZ experiment, the echo pulse breaks leakage paralysis by flipping the effective stabilizer of a leaked qubit on each round.

## Noncommuting effective measurements [paper_fact]
Fact ID: bultink.noncommuting
Source locator: Supplemental Sec. II.B, ZZ-and-XX effective-check example
PDF page: 11
Claim: Interleaved ZZ and XX checks reduce under one data leakage event to noncommuting Z and X measurements of the remaining data qubit, whose repeated measurement generates random results.

The source uses this as a second mechanism that breaks silent leakage.

## Larger-code detectability assertion [paper_fact]
Fact ID: bultink.detectability-assertion
Source locator: Supplemental Sec. II.B, paragraph ending the commutativity argument
PDF page: 11
Claim: The authors assert, to the best of their knowledge, that removing one data qubit breaks commutativity of at least two neighboring stabilizers in fully fault-tolerant stabilizer codes and therefore makes data leakage detectable.

## Scaling model [paper_fact]
Fact ID: bultink.scaling
Source locator: Supplemental Sec. II.B, likelihood model on PDF p. 12
PDF page: 12
Claim: Conditional on each neighboring ancilla flipping independently with probability p in the computational sector and one half in the leaked sector, the model's computational likelihood decays exponentially with the number of rounds.

## Short-event limitation [paper_fact]
Fact ID: bultink.short-events
Source locator: Supplemental Sec. II.B, paragraph following the likelihood equations
PDF page: 12
Claim: A leakage event much shorter than the hidden-model switching time need not be detectable and can be operationally indistinguishable from an ordinary error after rapid return to the computational subspace.

This limits the temporal resolution of the indirect estimator.

## Logical-qubit demonstration absent [literature_gap]
Fact ID: bultink.gap-logical
Source locator: Main-text conclusion, final paragraph on future work
PDF page: 4
Claim: The source contains no logical-qubit demonstration; extension to a seventeen-qubit surface code is stated as future work.
Gap scope: source_local

The demonstrated protected state is a two-data-qubit Bell state.

## Trajectory-conditioned frame absent [literature_gap]
Fact ID: bultink.gap-trajectory-frame
Source locator: Full-text review; main-text posterior/post-selection discussion on PDF pp. 3-4 and HMM construction in Supplemental Sec. II.A on pp. 9-10
PDF page: 10
Claim: The source does not define a trajectory-conditioned correction to a logical observable after a data qubit leaks and later returns.
Gap scope: source_local

Its leakage output is a posterior used for post-selection.

## Full leaked-subspace echo action absent [literature_gap]
Fact ID: bultink.gap-echo-unitary
Source locator: Full-text review; physical echo in Fig. 1A on p. 2, Supplemental Sec. I.C on p. 6 and Fig. S3 on p. 9, and operational explanation in Supplemental Sec. II.B on p. 11
PDF page: 11
Claim: The source does not specify the complete multilevel action or leaked-block relative phase of the physical data echo.
Gap scope: source_local

The operation is identified as an echo pulse through its circuit symbol and operational effect.

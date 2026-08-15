+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1805.11341"
source_version = "v3"
source_uri = "https://arxiv.org/abs/1805.11341v3"
source_artifact = "docs/papers/1805.11341v3.pdf"
source_sha256 = "fba541813b2e71bc1fb7c0f08588020bb7bfc539e1dc58bc7459963af7507a02"
title = "Quantum Markov Order"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "outputs/researchwrite/qec-memory-directed-research-report/manuscript_v0/source_audits/TARANTO_ET_AL_1805_11341V3_SOURCE_AUDIT_2026-08-06.md"
audit_packet_sha256 = "d537ba2786f26e5474f8605a2674068213022f37de3b011e36c1793f31183a7f"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-framework-notes-s3-2026-08-06"
admission_date = "2026-08-06"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8]

[[relations]]
predicate = "defines"
object_id = "taranto-classical-markov-order"
object_type = "concept"
object_label = "Markov order"
fact_id = "taranto1805-classical-markov-order"

[[relations]]
predicate = "defines"
object_id = "taranto-process-tensor-born-rule"
object_type = "method"
object_label = "process-tensor Choi operator"
fact_id = "taranto1805-process-tensor-born-rule"

[[relations]]
predicate = "defines"
object_id = "taranto-quantum-markov-order"
object_type = "concept"
object_label = "quantum Markov order"
fact_id = "taranto1805-quantum-markov-order"

[[relations]]
predicate = "supports"
object_id = "taranto-all-instruments-no-go"
object_type = "theorem"
object_label = "Theorem 4"
fact_id = "taranto1805-theorem-four"

[[relations]]
predicate = "defines"
object_id = "taranto-instrument-specific-order"
object_type = "concept"
object_label = "memory instrument sequence"
fact_id = "taranto1805-instrument-specific-order"

[[relations]]
predicate = "limits"
object_id = "taranto-quantum-cmi-memory-strength"
object_type = "limitation"
object_label = "quantum conditional mutual information"
fact_id = "taranto1805-proposition-five"
+++
# Full-text review — Taranto et al., “Quantum Markov Order”

## Source identity [paper_fact]
Fact ID: taranto1805-source-identity
Source locator: Title page, author block, date, and arXiv version stamp; journal identity supplied by DOI 10.1103/PhysRevLett.122.140401
PDF page: 1
Claim: The fixed source is the nine-page arXiv:1805.11341v3 artifact of Philip Taranto, Felix A. Pollock, Simon Milz, Marco Tomamichel, and Kavan Modi's article “Quantum Markov Order,” published as Physical Review Letters 122, 140401 (2019).

The reviewed object has SHA-256
`fba541813b2e71bc1fb7c0f08588020bb7bfc539e1dc58bc7459963af7507a02`.
Its DOI is `10.1103/PhysRevLett.122.140401`. All equation and page locators below refer to the
fixed arXiv PDF, which includes Appendices A--D.

## Selection scope [paper_fact]
Fact ID: taranto1805-selection-scope
Source locator: PDF page 1, Abstract and Introduction
PDF page: 1
Claim: The source asks how the classical notion of finite Markov order extends to quantum stochastic processes when the probing instruments and their disturbance are explicitly represented.

The study is formal and process-tensor based. It proves an all-instruments no-go result and then
defines an instrument-specific relaxation. It does not perform a repeated-QEC simulation or analyse
hardware syndrome records.

## Classical Markov order [paper_fact]
Fact ID: taranto1805-classical-markov-order
Source locator: Classical Markov Order, Definition 1 and Eq. (1)
PDF page: 2
Claim: Definition 1 states that a classical stochastic process has Markov order ell when the conditional law of any future realization is independent of the earlier history given the realization of the intervening ell-step memory block.

The paper segments the process into future \(F\), memory block \(M\), and history \(H\). The
condition must hold at every admissible boundary time, and order one is identified as the Markovian
special case.

## Classical conditional factorization [paper_fact]
Fact ID: taranto1805-classical-factorization
Source locator: Classical Markov Order, Eq. (2) and immediately following paragraph
PDF page: 2
Claim: Equation (1) implies that the joint future--history law conditioned on the memory realization factorizes, equivalently giving zero classical conditional mutual information between future and history given memory.

The factorization is conditional on a realization of the memory block. It is not a product of all
time marginals and therefore is not a fully cycle-factorized comparator.

## Long-range correlation under finite order [paper_fact]
Fact ID: taranto1805-overlapping-memory
Source locator: Classical Markov Order, paragraph following Eq. (2) and Fig. 1
PDF page: 2
Claim: Finite Markov order does not forbid unconditional correlations between times separated by more than ell because overlapping memory blocks can mediate those correlations.

The source distinguishes the length of history required for conditional prediction from the full
temporal correlation structure. This qualification prevents interpreting Eq. (2) as unconditional
temporal independence.

## Process-tensor spatiotemporal Born rule [paper_fact]
Fact ID: taranto1805-process-tensor-born-rule
Source locator: Quantum Stochastic Processes, Eq. (3); Appendix A, Eqs. (A2)--(A3)
PDF page: 3
Claim: Equation (3) represents a quantum stochastic process by a process-tensor Choi operator whose contraction with an instrument-sequence Choi operator gives the joint probability of that outcome sequence.

The process tensor contains the multi-time outcome probabilities available under all valid
instrument sequences. Appendix A states its positivity and causal trace constraints and explains
that the original convention includes a final system output, which the paper does not need for its
analysis.

## Quantum Markov order [paper_fact]
Fact ID: taranto1805-quantum-markov-order
Source locator: Quantum Markov Order, Definition 2 and Eq. (4)
PDF page: 3
Claim: Definition 2 assigns quantum Markov order ell with respect to a family of memory instruments when, for every admitted memory instrument and outcome and for all history and future instruments, the future statistics are independent of the earlier history conditioned on that memory intervention.

The memory instrument is explicitly part of the criterion. The history and future instruments are
universally quantified, so the definition is stronger than checking one fixed record-generation
scheme.

## Conditional process product structure [paper_fact]
Fact ID: taranto1805-conditional-process-product
Source locator: Quantum Markov Order, Eq. (5); Appendix B, Eqs. (B1)--(B5)
PDF page: 3
Claim: Equation (5) expresses quantum Markov order by requiring the conditional history--future process obtained after inserting each memory-instrument outcome to factor into a future-process operator and a history-process operator.

Appendix B derives the structure from Eq. (4) while leaving history and future instruments
arbitrary. It also notes that the conditional history factor need not satisfy the causality condition
of a proper process tensor because conditioning on the memory outcome postselects the history; its
sum over memory outcomes has the required tester normalization.

## Classical limit [paper_fact]
Fact ID: taranto1805-classical-limit
Source locator: Quantum Markov Order, Theorem 3 and proof
PDF page: 3
Claim: Theorem 3 proves that Definition 2 reduces to the classical Markov-order condition when a classical stochastic process is probed by any choice of sharp classical instruments.

The proof embeds the classical joint probability distribution diagonally in a process tensor and
uses rank-one orthogonal projectors. The qualification to sharp classical instruments is explicit.

## All-instruments finite-order theorem [paper_fact]
Fact ID: taranto1805-theorem-four
Source locator: Quantum Markov Order, Theorem 4; Appendix C, Lemma 6 and Eq. (C3)
PDF page: 3
Claim: Theorem 4 states that the only quantum processes having finite Markov order with respect to all possible instruments are Markovian processes.

Appendix C first shows that satisfying the conditional product requirement for every memory
instrument forces the memory subsystem to factor from the future or history. Imposing the condition
for every placement of the memory block yields the product process tensor
\(\bigotimes_k\Lambda_{k:k-1}\otimes\rho_0\). The paper therefore remarks that a generic
instrument sequence gives infinite order for a non-Markovian quantum process.

## Instrument-specific quantum Markov order [paper_fact]
Fact ID: taranto1805-instrument-specific-order
Source locator: Instrument-specific Quantum Markov Order, opening paragraphs and Fig. 2
PDF page: 4
Claim: The relaxed instrument-specific quantum Markov-order condition fixes the memory instrument sequence and requires every realization of that sequence to render arbitrary history and future statistics conditionally independent.

Only the memory intervention is fixed; the allowed history and future instruments remain arbitrary.
The source allows the decoupling instrument to vary across time and to contain temporally correlated
CP maps.

## Finite order with nonzero quantum CMI [paper_fact]
Fact ID: taranto1805-proposition-five
Source locator: Proposition 5 and proof; Appendix D, Eq. (D1) and Fig. 3
PDF page: 4
Claim: Proposition 5 establishes that a process can have finite instrument-specific quantum Markov order while the quantum conditional mutual information of its process tensor is nonzero.

Appendix D constructs a three-step qubit example. A specified nonorthogonal POVM on the memory
renders the conditional history and future product for every outcome, whereas generic alternative
instruments leave correlations. The source reports nonzero quantum CMI for the constructed process
and concludes that quantum CMI is a poor general memory-strength quantifier in this setting.

## Noisy-observation qualification [paper_fact]
Fact ID: taranto1805-noisy-observation
Source locator: Discussion following Theorem 4
PDF page: 4
Claim: The source states that noisy classical measurements can break the classical conditional product structure even for a Markovian process without creating intrinsic process memory.

The paper attributes this failure to historical information leaking into future observations through
measurement fuzziness. It uses this point to motivate explicit instrument dependence rather than to
label every observed dependence non-Markovian.

## No record-only quantum criterion [literature_gap]
Fact ID: taranto1805-gap-record-only-criterion
Source locator: Definition 2, Eqs. (4)--(5), and instrument-specific discussion
PDF page: 4
Claim: This source does not provide an instrument-independent quantum-memory criterion that can be evaluated from one fixed classical record law alone.
Gap scope: source_local

Its quantum definition quantifies over history and future instruments and specifies the memory
instrument. A classical record generated by one fixed instrument sequence is only one induced
stochastic process.

## No repeated-QEC demonstration [literature_gap]
Fact ID: taranto1805-gap-repeated-qec
Source locator: Complete source scope; QEC appears only in the forward-looking conclusion and cited references
PDF page: 5
Claim: This source does not simulate or measure repeated syndrome extraction, logical error, leakage, reset scheduling, or decoder performance.
Gap scope: source_local

The conclusion names error correction as an application area but supplies no QEC-facing
demonstration in this artifact.

## No universal quantum-CMI ordering [literature_gap]
Fact ID: taranto1805-gap-cmi-ordering
Source locator: Proposition 5 and proof
PDF page: 4
Claim: This source does not support ranking quantum memory strength universally by process-tensor quantum conditional mutual information.
Gap scope: source_local

The proof states that quantum CMI is not monotonic with respect to memory instruments, and the
constructed finite-order process has nonzero quantum CMI.

## No exact finite-order natural-law claim [literature_gap]
Fact ID: taranto1805-gap-natural-finite-order
Source locator: Conclusions, final paragraph on PDF p. 4 continuing to PDF p. 5
PDF page: 4
Claim: This source does not assert that non-Markovian processes in nature generically have strictly finite quantum Markov order.
Gap scope: source_local

The authors call strictly finite non-Markovian order unlikely in nature and describe finite-memory
numerical treatments as approximations tied to a selected instrument, including the identity
instrument in one common setting.

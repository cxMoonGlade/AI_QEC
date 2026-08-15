+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1907.12583"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1907.12583v2"
source_artifact = "docs/papers/1907.12583v2.pdf"
source_sha256 = "a1ed0e0fc88375f0fbaf5edc32dbab845ead31a9bf444feba469ed27a39f84d3"
title = "Non-Markovian memory strength bounds quantum process recoverability"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "outputs/researchwrite/qec-memory-directed-research-report/manuscript_v0/source_audits/taranto_pollock_modi_1907.12583v2_source_audit.md"
audit_packet_sha256 = "9393833efb1c95561a9f9b93ae73627b0f996ce2680f4a4ded8a184f3fa2285f"
admission_status = "draft_pending_review"
admission_reviewer = "codex-framework_notes_s2-semantic-pass-schema-blocked"
admission_date = "2026-08-06"
visually_checked_pages = [1, 3, 4, 5, 7, 8, 14]

[[relations]]
predicate = "defines"
object_id = "taranto-process-tensor-generalized-born-rule"
object_type = "concept"
object_label = "process-tensor generalized Born rule"
fact_id = "taranto-generalized-born-rule"

[[relations]]
predicate = "defines"
object_id = "taranto-instrument-relative-memory-strength"
object_type = "concept"
object_label = "instrument-relative memory strength"
fact_id = "taranto-memory-strength"

[[relations]]
predicate = "defines"
object_id = "taranto-recovered-process-ansatz"
object_type = "model"
object_label = "recovered process ansatz"
fact_id = "taranto-recovered-ansatz"

[[relations]]
predicate = "supports"
object_id = "taranto-instrument-span-observable-bound"
object_type = "theorem"
object_label = "instrument-span observable bound"
fact_id = "taranto-theorem-one"

[[relations]]
predicate = "supports"
object_id = "taranto-informationally-complete-process-bound"
object_type = "theorem"
object_label = "informationally-complete process bound"
fact_id = "taranto-theorem-three"

[[relations]]
predicate = "limits"
object_id = "taranto-restricted-instrument-span"
object_type = "limitation"
object_label = "restricted instrument span"
fact_id = "taranto-restricted-span"
+++
# Full-text review — Taranto, Pollock, and Modi, “Non-Markovian memory strength bounds quantum process recoverability”

## Source identity [paper_fact]
Fact ID: taranto-source-identity
Source locator: PDF title page and arXiv version line; journal metadata for DOI 10.1038/s41534-021-00481-4
PDF page: 1
Claim: The fixed source is arXiv:1907.12583v2 by Philip Taranto, Felix A. Pollock, and Kavan Modi, published as “Non-Markovian memory strength bounds quantum process recoverability” in npj Quantum Information 7, 149 (2021), DOI 10.1038/s41534-021-00481-4.

The PDF carries the visible arXiv version stamp 12 October 2021 and a manuscript
date of 13 October 2021.

## Selection scope [paper_fact]
Fact ID: taranto-selection-scope
Source locator: Abstract; Introduction opening, PDF p. 1; Results opening, PDF p. 3
PDF page: 1
Claim: The source defines an operational instrument-relative memory strength for quantum stochastic processes and relates it to observable-level or process-level recovery errors for a finite-memory ansatz.

The framework is generic to sequential quantum processes. Its case study is an
open qubit model, not a repeated-QEC experiment.

## Process-tensor generalized Born rule [paper_fact]
Fact ID: taranto-generalized-born-rule
Source locator: Background B, Eq. (5)
PDF page: 3
Claim: The process-tensor generalized Born rule computes the probability of an instrument-event sequence by contracting the transposed Choi operator of that sequence with the Choi process tensor.

Equation (5) states

\[
P_{n:1}(x_{n:1}\mid\mathcal J_{n:1})
=\operatorname{tr}[(O_{n:1}^{(x_{n:1})})^T\Upsilon_{n:1}].
\]

The surrounding text states that \(\Upsilon_{n:1}\) encodes the outcome
probabilities for all instrument choices.

## Conditional future--history process [paper_fact]
Fact ID: taranto-conditional-process
Source locator: Background B, Eq. (6) and following paragraph
PDF page: 3
Claim: Contracting a realized memory-instrument element with the memory slots of a process tensor yields the outcome-conditioned future--history process.

Equation (6) defines

\[
\widetilde\Upsilon_{FH}^{(x_M)}
=\operatorname{tr}_M[(O_M^{(x_M)})^T\Upsilon_{FMH}].
\]

The tilde records that postselection on a memory outcome can make this object
subnormalized and not itself a proper process tensor; summing over outcomes
yields a proper process tensor.

## Instrument-relative memory strength [paper_fact]
Fact ID: taranto-memory-strength
Source locator: Results A, Eqs. (7)--(9)
PDF page: 3
Claim: The instrument-relative memory strength \(\Theta(\mathcal J_M)\) is the memory-outcome average of measured future--history mutual information, maximized over the declared family of uncorrelated future and history instruments.

The conditioning instrument \(\mathcal J_M\) is part of the definition.
Equations (8)--(9) specify the measured conditional mutual information and the
corresponding outcome distribution.

## Recovered process ansatz [paper_fact]
Fact ID: taranto-recovered-ansatz
Source locator: Results A, Eq. (10) and first paragraph on PDF p. 4
PDF page: 3
Claim: The recovered process ansatz uses duals of the memory-instrument elements to reconstruct the process on their linear span while replacing each conditioned future--history object by the tensor product of its conditioned future and history marginals.

Equation (10) is

\[
\Lambda_{FMH}^{\mathcal J_M}
=\sum_{x_M}\Upsilon_F^{(x_M)}\otimes D_M^{(x_M)}
\otimes\widetilde\Upsilon_H^{(x_M)},
\]

where the duals obey
\(\operatorname{tr}[(D_M^{(x_M)})^T O_M^{(x'_M)}]
=\delta_{x_Mx'_M}\).

## Restricted instrument span [paper_fact]
Fact ID: taranto-restricted-span
Source locator: Results A, first paragraph on PDF p. 4
PDF page: 4
Claim: If the memory instrument is not informationally complete, the recovered object acts correctly only on the restricted instrument span and is not a full process tensor for arbitrary memory interventions.

The source denotes this restricted object with an underline and states that its
domain is the span of \(\mathcal J_M\). Correct statistics follow by linearity
only for multi-time observables whose memory-block support has the displayed
decomposition in that span.

## Instrument-span observable bound [paper_fact]
Fact ID: taranto-theorem-one
Source locator: Results A, Theorem 1 and Eq. (11); proof in Methods C, Eqs. (30)--(33)
PDF page: 4
Claim: The instrument-span observable bound in Theorem 1 limits the expectation-value error to \(|C|\sqrt{2\Theta(\mathcal J_M)}\) for a multi-time observable whose support on the memory block lies in the span of the memory-instrument elements.

The theorem does not assume a specific system--environment dynamics, but its
observable-domain hypothesis remains load-bearing. Equations (30)--(33) prove
the result using instrument relative entropy, Pinsker's inequality, an
instrument decomposition of \(C\), and Cauchy--Schwarz.

## Informationally complete process bound [paper_fact]
Fact ID: taranto-theorem-three
Source locator: Results A, Theorem 3 and Eq. (13); proof in Methods E, Eq. (34)
PDF page: 4
Claim: The informationally-complete process bound in Theorem 3 limits the generalized process diamond distance between the original and recovered processes to \(\sqrt{2\Theta(\mathcal J_M)}\).

Informational completeness makes the recovered object a full process tensor
and identifies the restricted instrument span with the full admitted
instrument set in the proof.

## Stationary iterative reach [paper_fact]
Fact ID: taranto-stationary-iterative-reach
Source locator: Results A, paragraph immediately before Theorem 1
PDF page: 4
Claim: The source states that repeated action of the recovery map can propagate the recovered ansatz arbitrarily far with fixed memory-length-dependent complexity when the process is stationary.

Stationarity belongs to this iterative construction; it is not a hypothesis of
the single-block expectation bound as stated in Theorem 1.

## Informational-completeness distinction [paper_fact]
Fact ID: taranto-informational-completeness-distinction
Source locator: Results A, paragraphs between Corollary 2 and Theorem 3
PDF page: 4
Claim: Small memory strength for an informationally complete memory instrument controls all instruments through Theorem 3, whereas a non-informationally-complete instrument supports only the restricted observable predictions guaranteed on its span.

The source therefore separates an instrument-relative restricted recovery
claim from a full process-distinguishability claim.

## Proxy-bound scaling limitation [paper_fact]
Fact ID: taranto-proxy-bound-scaling
Source locator: Appendix D, paragraph following Eq. (D6)
PDF page: 14
Claim: Replacing the optimized memory strength by the easier Choi-relative-entropy proxy yields a looser bound with a factor set by the future--history process dimension, which generally grows exponentially with the number of timesteps.

The proxy avoids the future/history instrument optimization but does not retain
the tightness of the main instrument-optimized bound.

## No repeated-QEC demonstration [literature_gap]
Fact ID: taranto-gap-repeated-qec
Source locator: Complete source scope, including the open-qubit case study in Results B and Appendix E
PDF page: 5
Claim: This source does not instantiate its recovery construction, expectation bound, or generalized diamond bound on a repeated quantum-error-correction circuit, syndrome record, decoder, or logical observable.
Gap scope: source_local

The paper mentions correlated error correction as a motivation and cites
adjacent work, but its own numerical demonstration is the declared
system--environment qubit model.

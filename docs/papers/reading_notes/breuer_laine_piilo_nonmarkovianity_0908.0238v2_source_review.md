+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:0908.0238"
source_version = "v2"
source_uri = "https://arxiv.org/abs/0908.0238v2"
source_artifact = "docs/papers/0908.0238v2.pdf"
source_sha256 = "9e05b98a5b6a902be4fa8d4d2662b7e9b7592d150ddef6bf74a8d6e9f9bf4553"
title = "Measure for the degree of non-Markovian behavior of quantum processes in open systems"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/BLP_0908_0238V2_NONMARKOVIAN_WITNESS_AUDIT_2026-07-29.md"
audit_packet_sha256 = "4151228066fc7e6e195c43debc3435dce7484b8169ab46352adfd356a2fa6b19"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-rereview-blp-mccloskey-round3-2026-07-29"
admission_date = "2026-07-29"
visually_checked_pages = [1, 2, 3, 4]

[[relations]]
predicate = "defines"
object_id = "blp-trace-distance"
object_type = "observable"
object_label = "trace distance"
fact_id = "blp-trace-distance"

[[relations]]
predicate = "defines"
object_id = "blp-trace-distance-rate"
object_type = "observable"
object_label = "trace-distance rate"
fact_id = "blp-positive-rate-witness"

[[relations]]
predicate = "limits"
object_id = "blp-fixed-pair-limit"
object_type = "limitation"
object_label = "one fixed pair"
fact_id = "blp-fixed-pair-lower-bound"
+++
# Full-text review — Breuer, Laine, and Piilo, “Measure for the degree of non-Markovian behavior of quantum processes in open systems”

## Source identity [paper_fact]
Fact ID: blp-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The reviewed fixed source is the four-page preprint arXiv:0908.0238v2 by Breuer, Laine, and Piilo.

The artifact visibly carries the arXiv version line `5 Jan 2010` and the
title-page line `Dated: October 26, 2018`. This source-only record preserves
both visible dates without explaining their discrepancy.

## Selection scope [paper_fact]
Fact ID: blp-selection-scope
Source locator: Abstract and opening construction, page 1
PDF page: 1
Claim: The source constructs a non-Markovianity measure from increases in the distinguishability of two reduced-system states evolving under one dynamical map.

## Trace-distance definition [paper_fact]
Fact ID: blp-trace-distance
Source locator: Eq. (1)
PDF page: 1
Claim: The source defines the trace distance as \(D(\rho_1,\rho_2)=\frac12\operatorname{tr}|\rho_1-\rho_2|\), with values between zero and one.

Here \(|A|=\sqrt{A^\dagger A}\).

## Trace-distance distinguishability [paper_fact]
Fact ID: blp-trace-distance-distinguishability
Source locator: Paragraph following Eq. (1)
PDF page: 1
Claim: The source interprets trace distance as the distinguishability of two quantum states in an optimal state-discrimination experiment.

## CPT contraction [paper_fact]
Fact ID: blp-cpt-contraction
Source locator: Eq. (2)
PDF page: 1
Claim: Every completely positive trace-preserving map \(\Phi\) contracts trace distance, \(D(\Phi\rho_1,\Phi\rho_2)\le D(\rho_1,\rho_2)\).

## Divisible-map monotonicity [paper_fact]
Fact ID: blp-divisible-monotonicity
Source locator: Eqs. (5) and (9) with surrounding derivation
PDF page: 2
Claim: For the source's divisible dynamics, the trace distance for every fixed pair of initial states is nonincreasing with time.

The intermediate map in Eq. (9) is itself completely positive and trace
preserving, which permits the contraction argument.

## Positive-rate witness [paper_fact]
Fact ID: blp-positive-rate-witness
Source locator: Eq. (10) and the following two paragraphs
PDF page: 2
Claim: The source defines the trace-distance rate \(\sigma(t,\rho_{1,2}(0))=\frac{d}{dt}D(\rho_1(t),\rho_2(t))\) and calls a process non-Markovian when this rate is positive for some time and some initial pair.

When \(\sigma>0\), the rate is interpreted as information flowing from the
environment back to the system.

## Optimized positive integral [paper_fact]
Fact ID: blp-integrated-measure
Source locator: Eq. (11)
PDF page: 2
Claim: The source defines \(\mathcal N(\Phi)\) by maximizing over all initial-state pairs the integral of the trace-distance rate over intervals where that rate is positive.

## Positive-interval endpoint sum [paper_fact]
Fact ID: blp-positive-interval-endpoint-sum
Source locator: Eq. (12)
PDF page: 3
Claim: The source rewrites the positive-rate integral as a sum of trace-distance differences between the endpoints of every interval where the trace-distance rate is positive.

## Finite-spin-bath oscillation [paper_fact]
Fact ID: blp-finite-spin-bath
Source locator: Eq. (14) and the central-spin discussion
PDF page: 4
Claim: In the source's finite central-spin example, trace distance oscillates periodically and is interpreted as repeated information exchange between the central spin and its spin bath.

## Complete-dynamics requirement [paper_fact]
Fact ID: blp-optimization-limit
Source locator: Concluding paragraph
PDF page: 4
Claim: Exact evaluation of the source's measure requires complete knowledge of the reduced dynamics.

## Fixed-pair lower-bound limitation [paper_fact]
Fact ID: blp-fixed-pair-lower-bound
Source locator: Concluding paragraphs
PDF page: 4
Claim: An observed positive trace-distance increase for one fixed pair supplies a non-Markovian signature and a lower bound on the optimized measure.

## Unsupported PEPS-bond implication [literature_gap]
Fact ID: blp-gap-peps-bond
Source locator: Complete-text review, pages 1–4
PDF page: 1
Claim: The source does not define a PEPS virtual-bond dimension.
Gap scope: source_local

## Unsupported truncation-error implication [literature_gap]
Fact ID: blp-gap-truncation-error
Source locator: Complete-text review, pages 1–4
PDF page: 1
Claim: The source does not define a tensor-network truncation error.
Gap scope: source_local

## Unsupported state-fidelity implication [literature_gap]
Fact ID: blp-gap-state-fidelity
Source locator: Complete-text review, pages 1–4
PDF page: 1
Claim: The source does not establish a whole-state fidelity diagnostic for an approximate tensor-network evolution.
Gap scope: source_local

## Unsupported timing implication [literature_gap]
Fact ID: blp-gap-runtime
Source locator: Complete-text review, pages 1–4
PDF page: 1
Claim: The source does not establish a tensor-network runtime metric.
Gap scope: source_local

## Unsupported monotonic-entanglement implication [literature_gap]
Fact ID: blp-gap-monotonic-entanglement
Source locator: Complete-text review, pages 1–4
PDF page: 1
Claim: The source does not establish monotonic entanglement growth with elapsed evolution time.
Gap scope: source_local

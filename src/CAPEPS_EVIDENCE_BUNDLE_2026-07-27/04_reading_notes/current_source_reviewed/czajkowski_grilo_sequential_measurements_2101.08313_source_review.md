+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2101.08313"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2101.08313v2"
source_artifact = "docs/papers/2101.08313v2.pdf"
source_sha256 = "29bfff3bc43db7e5159529ae7be85f87de4803589703fe3f8fa8790f547986ee"
title = "On-State Commutativity of Measurements and Joint Distributions of Their Outcomes"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/RESTRICTED_MCWF_F2_F3_PROJECT_FIT_AUDIT_2026-07-20.md"
audit_packet_sha256 = "321c10a1f152fe1baa183f297f2cddd4e3dbefeb3178d4b6fff7027cafbeb763"
admission_status = "source_only_reviewed"
admission_reviewer = "source_only_second_pass_2026_07_20"
admission_date = "2026-07-20"
visually_checked_pages = [1, 5, 7]

[[relations]]
predicate = "defines"
object_id = "selective-measurement-update"
object_type = "method"
object_label = "selective measurement update"
fact_id = "czajkowski-selective-update"

[[relations]]
predicate = "defines"
object_id = "ordered-projective-outcome-law"
object_type = "observable"
object_label = "ordered projective outcome law"
fact_id = "czajkowski-ordered-law"
+++
# Source review — Czajkowski and Grilo on sequential measurements

## Source identity [paper_fact]
Fact ID: czajkowski-source-identity
Source locator: Title page and abstract
PDF page: 1
Claim: The source is the sixteen-page arXiv:2101.08313v2 manuscript by Jan Czajkowski and Alex B. Grilo on outcome distributions from sequences of quantum measurements.

The abstract studies when measurement outcomes admit order-independent joint distributions and
emphasizes on-state permutability rather than unrestricted commutation.

## Selective update [paper_fact]
Fact ID: czajkowski-selective-update
Source locator: Sec. 2.2, Eq. (1)
PDF page: 5
Claim: A selective measurement update assigns outcome probability `Tr(Q_x rho)` and post-measurement state `A_x rho A_x^dagger/Tr(Q_x rho)` when `Q_x=A_x^dagger A_x`.

The source first defines the positive measurement operators and their normalization. The stated update
keeps the probability and the normalized conditional state as separate quantities.

## Ordered outcome law [paper_fact]
Fact ID: czajkowski-ordered-law
Source locator: Sec. 3.1, Eq. (9)
PDF page: 7
Claim: For projectors `A` followed by `B`, the ordered projective outcome law assigns probability `Tr(A B A rho)`, whereas the reversed order generally gives `Tr(B A B rho)`.

The difference is used to demonstrate that sequential independence is not automatic for quantum
measurements. The formula follows by multiplying the first-outcome probability by the conditional
probability after the first selective update.

## Order-independent limit [paper_fact]
Fact ID: czajkowski-order-limit
Source locator: Sec. 3.1, Property 8 and Eq. (10)
PDF page: 7
Claim: Order-independent sequential probabilities require an additional sequential-independence condition and are not implied by the measurement axioms alone.

The subsequent results connect such conditions to on-state permutation of the relevant measurement
operators.

## Scope limit [literature_gap]
Fact ID: czajkowski-gap-reset-dynamics
Source locator: Full-text scope established by Secs. 2–4
PDF page: 7
Claim: The source does not combine sequential measurements with Lindblad evolution, stochastic trajectories, or an explicit reset-to-fixed-state channel.
Gap scope: source_local

Its focus is the algebraic existence and consistency of joint distributions for measurement outcomes.

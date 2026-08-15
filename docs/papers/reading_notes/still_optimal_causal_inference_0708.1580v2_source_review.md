+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:0708.1580"
source_version = "v2"
source_uri = "https://arxiv.org/abs/0708.1580v2"
source_artifact = "docs/papers/0708.1580v2.pdf"
source_sha256 = "dd2495cf6606e57685bd2ed3cd40610c2e19fb8357adb4fe4a5daa9a5b17aff9"
title = "Optimal causal inference: Estimating stored information and approximating causal architecture"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "outputs/researchwrite/qec-memory-directed-research-report/manuscript_v0/source_audits/still_crutchfield_ellison_0708.1580v2_source_audit.md"
audit_packet_sha256 = "db848b9642d53edeebef0b884894c062bdccecd1893113af68081988665aa76a"
admission_status = "draft_pending_review"
admission_reviewer = "codex-framework_notes_s2-semantic-pass-schema-blocked"
admission_date = "2026-08-06"
visually_checked_pages = [1, 2, 3, 4, 5, 9, 12, 14]

[[relations]]
predicate = "defines"
object_id = "still-causal-state-predictive-equivalence"
object_type = "concept"
object_label = "causal-state predictive equivalence"
fact_id = "still-causal-state-equivalence"

[[relations]]
predicate = "limits"
object_id = "still-no-universal-distortion-function"
object_type = "limitation"
object_label = "no universal distortion function"
fact_id = "still-no-universal-distortion"

[[relations]]
predicate = "defines"
object_id = "still-optimal-causal-filtering-objective"
object_type = "method"
object_label = "optimal causal filtering objective"
fact_id = "still-ocf-objective"

[[relations]]
predicate = "derives"
object_id = "still-low-temperature-causal-state-recovery"
object_type = "theorem"
object_label = "low-temperature causal-state recovery"
fact_id = "still-ocf-theorem-one"
+++
# Full-text review — Still, Crutchfield, and Ellison, “Optimal causal inference”

## Source identity [paper_fact]
Fact ID: still-source-identity
Source locator: PDF title page and arXiv version line; journal metadata for DOI 10.1063/1.3489885
PDF page: 1
Claim: The fixed source is arXiv:0708.1580v2 by Susanne Still, James P. Crutchfield, and Christopher J. Ellison, published as “Optimal causal inference: Estimating stored information and approximating causal architecture” in Chaos 20, 037111 (2010), DOI 10.1063/1.3489885.

The PDF carries the visible arXiv version stamp 19 August 2010. The title page
also contains a later PDF compilation date; this note uses the pinned arXiv
version identity rather than treating that compilation date as the publication
date.

## Selection scope [paper_fact]
Fact ID: still-selection-scope
Source locator: Abstract and Sec. I
PDF page: 1
Claim: The source develops optimal causal filtering for approximate predictive models when process statistics are known and optimal causal estimation for the additional problem of finite-data fluctuations.

The source studies classical stochastic time series and asks how much of their
predictive organization a representation retains at a given model complexity.

## Classical process assumptions [paper_fact]
Fact ID: still-process-assumptions
Source locator: Sec. II, opening paragraph
PDF page: 2
Claim: The source assumes a stationary classical stochastic process over a bi-infinite sequence of discrete-valued random variables, partitioned into an infinite history and future.

Footnote [45] says the infinite-string notation stands for finite past and
future words with limits taken at appropriate points.

## Causal-state predictive equivalence [paper_fact]
Fact ID: still-causal-state-equivalence
Source locator: Sec. II, Eq. (1)
PDF page: 2
Claim: The causal-state predictive equivalence maps a history to the class of all histories having the same conditional distribution over the future.

Equation (1) defines

\[
\epsilon(\overleftarrow{x})=
\{\overleftarrow{x}' :
P(\overrightarrow{X}\mid\overleftarrow{x})
=P(\overrightarrow{X}\mid\overleftarrow{x}')\}.
\]

The resulting state is an equivalence class of observed histories, not a
microscopic physical state asserted by the source.

## State-conditioned future law [paper_fact]
Fact ID: still-state-conditioned-future
Source locator: Sec. II, Eqs. (3)--(4)
PDF page: 2
Claim: Assignment to a causal state is deterministic, and conditioning on that state reproduces the future distribution conditioned on any history in the state.

For every history satisfying \(\epsilon(\overleftarrow x)=\sigma\), Eq. (4)
gives
\(P(\overrightarrow X\mid\sigma)=
P(\overrightarrow X\mid\overleftarrow x)\).

## Predictive information and shielding [paper_fact]
Fact ID: still-predictive-information-shielding
Source locator: Sec. II, Eq. (5) and immediately following paragraph
PDF page: 2
Claim: The causal-state variable retains all mutual information shared by the past and future and renders the past and future conditionally independent.

The source writes \(I[S;\overrightarrow X]
=I[\overleftarrow X;\overrightarrow X]\) and then states the factorization
\(P(\overleftarrow X,\overrightarrow X\mid S)
=P(\overleftarrow X\mid S)P(\overrightarrow X\mid S)\).

## Minimal predictive complexity [paper_fact]
Fact ID: still-minimal-predictive-complexity
Source locator: Sec. II, Eq. (6) and final paragraph
PDF page: 2
Claim: Among equally predictive partitions, the causal-state partition has minimum state entropy and is the unique minimal sufficient statistic for predicting the time series under the stated process assumptions.

Equation (6) gives \(H[\widehat R]\geq H[S]\) for prescient rivals. The
source calls \(H[S]\) the statistical complexity.

## No universal distortion function [paper_fact]
Fact ID: still-no-universal-distortion
Source locator: Sec. III, first paragraph
PDF page: 3
Claim: The source states that there is no universal distortion function, so an application must specify what information is relevant; the information-bottleneck construction still requires the relevant variable to be chosen a priori.

For the stationary time-series problem treated in this paper, the future data
are selected as the relevant variable. This source-local choice does not define
a discrepancy for every modelling task.

## Optimal causal filtering objective [paper_fact]
Fact ID: still-ocf-objective
Source locator: Sec. III, Eq. (7) and following paragraph
PDF page: 3
Claim: The optimal causal filtering objective maximizes predictive information retained about the future minus a linear penalty on information retained about the past, and the source explicitly calls that linear trade-off an ad hoc assumption.

The optimized assignment is \(P(R\mid\overleftarrow X)\), and Eq. (7) is

\[
\max_{P(R\mid\overleftarrow X)}
\{I[R;\overrightarrow X]-\lambda I[\overleftarrow X;R]\}.
\]

Here \(\lambda\) controls the stated prediction--complexity balance.

## Optimal assignments and future morphs [paper_fact]
Fact ID: still-ocf-self-consistency
Source locator: Sec. III, Eqs. (8)--(10)
PDF page: 3
Claim: The stationary OCF equations assign histories to representation states with an exponential weight set by the KL divergence between the history-conditioned and representation-conditioned future distributions, coupled to self-consistent equations for the future morphs and state probabilities.

The assignment in Eq. (8), the representation-conditioned future law in
Eq. (9), and the marginal representation probability in Eq. (10) are solved
iteratively. The source interprets the divergence as the discrepancy between
the predicted and true future laws.

## Low-temperature causal-state recovery [paper_fact]
Fact ID: still-ocf-theorem-one
Source locator: Sec. IV, Theorem 1 and Eqs. (17)--(20)
PDF page: 4
Claim: The low-temperature causal-state recovery result in Theorem 1 proves that, with no restriction on the set of model states, the low-temperature limit of OCF recovers the causal-state partition.

The proof uses Eq. (17) to identify a causal-state future morph equal to the
history-conditioned morph, hence zero KL divergence in Eq. (18). Equations
(19)--(20) then identify the minimizing state and the deterministic optimal
assignment with \(\epsilon(\overleftarrow x)\).

## Zero-penalty nonuniqueness [paper_fact]
Fact ID: still-zero-penalty-nonuniqueness
Source locator: Sec. IV, paragraph following Eq. (24)
PDF page: 4
Claim: At zero complexity penalty, causal states and other prescient rival partitions are degenerate, so maximizing predictive information alone does not suffice to recover the causal-state partition.

The minimum-complexity condition is therefore load-bearing for the source's
uniqueness statement.

## Finite-word and finite-data limits [paper_fact]
Fact ID: still-finite-word-data-limits
Source locator: Sec. V opening, PDF p. 5; Sec. VI, Eqs. (25)--(27), PDF p. 9; note [45], PDF p. 14
PDF page: 5
Claim: The numerical examples replace the infinite history and future by finite words, while the finite-data correction in optimal causal estimation assumes a sufficiently large sample for a small-perturbation approximation.

The displayed applications therefore do not directly optimize over literal
infinite strings, and the correction in Eq. (25) is a regime-dependent
approximation rather than an exact finite-sample identity.

## No controlled or quantum extension [literature_gap]
Fact ID: still-gap-controlled-quantum-extension
Source locator: Complete source scope, with assumptions fixed in Sec. II and conclusions in Sec. VII
PDF page: 12
Claim: This source does not define causal states for controlled input--output histories, quantum instruments, process tensors, or nonstationary stochastic processes.
Gap scope: source_local

Any such extension requires another source or an explicitly marked adaptation;
it is not part of the theorem proved in this artifact.

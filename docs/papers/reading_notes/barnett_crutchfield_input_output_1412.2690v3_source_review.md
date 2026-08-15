+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1412.2690"
source_version = "v3"
source_uri = "https://arxiv.org/abs/1412.2690v3"
source_artifact = "docs/papers/1412.2690v3.pdf"
source_sha256 = "0386fec64e0c6da9b13dd93794dd29cd5965d3b018d9a8fa05524603f3b9815a"
title = "Computational Mechanics of Input-Output Processes: Structured Transformations and the epsilon-Transducer"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "outputs/researchwrite/qec-memory-directed-research-report/manuscript_v0/source_audits/BARNETT_CRUTCHFIELD_1412_2690V3_SOURCE_AUDIT_2026-08-06.md"
audit_packet_sha256 = "724210740f80ca22f264b7dc47df264ed82205b2f6ee2cf2a145aeee9020e32c"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-review-framework-notes-s3-2026-08-06"
admission_date = "2026-08-06"
visually_checked_pages = [1, 2, 6, 7, 12, 13, 14, 15, 16, 17, 18]

[[relations]]
predicate = "defines"
object_id = "barnett-crutchfield-channel-causal-equivalence"
object_type = "concept"
object_label = "channel causal-equivalence relation"
fact_id = "bc1412-causal-equivalence"

[[relations]]
predicate = "supports"
object_id = "barnett-crutchfield-causal-state-proxy"
object_type = "theorem"
object_label = "future output given future input"
fact_id = "bc1412-proxy-past"

[[relations]]
predicate = "supports"
object_id = "barnett-crutchfield-causal-shielding"
object_type = "theorem"
object_label = "causal shielding"
fact_id = "bc1412-causal-shielding"

[[relations]]
predicate = "supports"
object_id = "barnett-crutchfield-maximal-prescience"
object_type = "theorem"
object_label = "channel causal states"
fact_id = "bc1412-maximal-prescience"

[[relations]]
predicate = "supports"
object_id = "barnett-crutchfield-minimal-conditional-complexity"
object_type = "theorem"
object_label = "minimal conditional statistical complexity"
fact_id = "bc1412-minimality"

[[relations]]
predicate = "supports"
object_id = "barnett-crutchfield-unique-prescient-partition"
object_type = "theorem"
object_label = "prescient rival"
fact_id = "bc1412-uniqueness"
+++
# Full-text review — Barnett and Crutchfield, “Computational Mechanics of Input-Output Processes”

## Source identity [paper_fact]
Fact ID: bc1412-source-identity
Source locator: Title page, arXiv identifier and version stamp; journal identity supplied by DOI 10.1007/s10955-015-1327-5
PDF page: 1
Claim: The fixed source is the 30-page arXiv:1412.2690v3 artifact of Nix Barnett and James P. Crutchfield's article “Computational Mechanics of Input-Output Processes: Structured Transformations and the epsilon-Transducer,” published in the Journal of Statistical Physics.

The reviewed object has SHA-256
`0386fec64e0c6da9b13dd93794dd29cd5965d3b018d9a8fa05524603f3b9815a`.
Its DOI is `10.1007/s10955-015-1327-5`. The arXiv title page carries the v3 stamp and an
internal manuscript date; all equation and page locators below refer to this fixed arXiv PDF rather
than publisher pagination.

## Selection scope [paper_fact]
Fact ID: bc1412-selection-scope
Source locator: Sec. II.A, opening and stationarity/ergodicity restrictions; Sec. III, Definitions 2--4
PDF page: 2
Claim: The source develops predictive representations for discrete input--output processes under a stationary-channel assumption, a causal-channel assumption, and a primary restriction to ergodic processes and channels.

The process variables take values in finite or countable alphabets. Section II states that the
development considers stationary processes and primarily ergodic stationary processes. Section III
defines stationary, ergodic, and causal channels and states that stationarity and causality are
assumed thereafter unless noted. This is not a theorem about arbitrary nonstationary records.

## Channel as a conditional output process [paper_fact]
Fact ID: bc1412-channel-definition
Source locator: Sec. III, Definition 1 and Eq. (6)
PDF page: 6
Claim: Definition 1 represents a channel as a collection of output stochastic processes indexed by every bi-infinite input sequence, equivalently through output-word probabilities conditional on input sequences.

The channel is total on the admitted sequence space. When an input process is supplied, integrating
the conditional output process against the input distribution produces a joint input--output process
and hence an output process. The source distinguishes the channel from any one input process that
drives it.

## Channel causality [paper_fact]
Fact ID: bc1412-channel-causality
Source locator: Sec. III, Definition 4
PDF page: 7
Claim: Definition 4 calls a channel causal when an output word through a specified horizon is independent of input symbols occurring after that horizon once the available input past is specified.

The source labels this property anticipation-free. It also warns that a chosen assignment of
observables to input and output can violate causality and discusses a delay construction for finite
anticipation; the optimality results would then require modification.

## Channel causal-equivalence relation [paper_fact]
Fact ID: bc1412-causal-equivalence
Source locator: Sec. VI, Eq. (9) and following definition of the epsilon-map
PDF page: 12
Claim: Equation (9) defines the channel causal-equivalence relation by grouping two joint input--output pasts exactly when their complete future-output conditional distributions agree given the future input.

The equivalence classes partition allowed joint pasts and are called the channel causal states. The
epsilon-map sends a joint past to its equivalence class. The equality concerns complete future
morphs as conditional-law kernels over the future input, not only a one-step output probability, a
selected moment, or one selected future-input realization.

## Why future input is conditioned upon [paper_fact]
Fact ID: bc1412-future-input-conditioning
Source locator: Sec. VI, paragraph immediately following Definition 8
PDF page: 13
Claim: The source conditions causal equivalence on future input because a channel is defined by its output behavior given input; omitting that conditioning would require specifying an input process and would instead lead toward the global joint-process epsilon-machine.

This separates a channel representation from the state distribution induced by a particular input
process. The latter affects input-dependent statistical complexity but not the causal-equivalence
definition itself.

## Causal-state proxy property [paper_fact]
Fact ID: bc1412-proxy-past
Source locator: Sec. IX, Proposition 3 and proof
PDF page: 15
Claim: Proposition 3 proves that future output given future input is independent of the joint input--output past when the channel causal state is conditioned upon.

The proof uses two source-defined facts: causal states share future morphs with their member pasts,
and the causal state is a deterministic function of the past. The result is a predictive
sufficiency statement for the channel causal state; it is not a microscopic-state identification.

## Causal shielding [paper_fact]
Fact ID: bc1412-causal-shielding
Source locator: Sec. IX, Proposition 4 and proof
PDF page: 15
Claim: Proposition 4 proves causal shielding: conditional on future input and the current causal state, the joint distribution of past output and future output factorizes into its past-output and future-output factors.

The proof applies Proposition 3 to the future-output factor in the probability chain rule. The
factorization is conditional and therefore does not assert temporal independence without the
causal state and future input.

## Prescience definition [paper_fact]
Fact ID: bc1412-prescience-definition
Source locator: Sec. IX, Definition 9 and finite-future identity
PDF page: 16
Claim: Definition 9 quantifies the prescience of a rival partition by the conditional mutual information it shares with future output given future input.

Because semi-infinite entropies are typically infinite, the source rewrites the statement using a
limit of finite-future prediction uncertainties. Rival states are partitions of joint pasts, rather
than arbitrary hidden variables unrelated to the past.

## Maximal prescience [paper_fact]
Fact ID: bc1412-maximal-prescience
Source locator: Sec. IX, Theorem 1 and proof
PDF page: 16
Claim: Theorem 1 proves that channel causal states are as prescient as the full joint input--output past and at least as prescient as every rival partition of that past.

The proof first establishes the result for every finite output horizon using the data-processing
inequality and equality of the future morphs, then takes the infinite-future limit. The theorem also
states the finite-horizon equality explicitly.

## Prescient-rival refinement [paper_fact]
Fact ID: bc1412-refinement
Source locator: Sec. IX, Lemma 1 and Eqs. (11)--(12)
PDF page: 17
Claim: Lemma 1 proves that any prescient rival partition refines the causal-state partition almost everywhere.

The argument writes a rival future morph as a convex combination of causal-state future morphs and
uses concavity of Shannon entropy. Equality at full prescience is possible only when a rival state
lies within one causal state apart from a measure-zero set.

## Minimal conditional statistical complexity [paper_fact]
Fact ID: bc1412-minimality
Source locator: Sec. IX, Theorem 2 and Corollary 1
PDF page: 17
Claim: Theorem 2 proves that, for a specified input process, channel causal states have minimal conditional statistical complexity among all prescient rival partitions.

The refinement map makes the causal state a function of the prescient rival almost everywhere, so
the rival's state entropy cannot be smaller. The comparison is restricted to fully prescient rivals;
it is not a ranking of deliberately lossy predictors.

## Unique prescient minimal partition [paper_fact]
Fact ID: bc1412-uniqueness
Source locator: Sec. IX, Theorem 3 and proof
PDF page: 17
Claim: Theorem 3 proves that a prescient rival attaining the causal states' minimal conditional complexity for every input process is isomorphic to the causal-state partition almost everywhere.

The refinement map and equality of entropies imply a reverse map almost everywhere, so the two
equivalence relations coincide except on measure-zero sets. The quantifier over every input process
is part of the theorem statement.

## No nonstationary optimality theorem [literature_gap]
Fact ID: bc1412-gap-nonstationary
Source locator: Sec. II.A stationarity restriction and Sec. III assumption following Definition 4
PDF page: 7
Claim: This source does not prove the epsilon-transducer optimality theorems for arbitrary nonstationary input--output processes.
Gap scope: source_local

Time-dependent laws would require an additional construction or a restricted application. A cycle
index or calibration context is not introduced as a universal repair in this source.

## No quantum-instrument criterion [literature_gap]
Fact ID: bc1412-gap-quantum-instruments
Source locator: Complete source scope, especially Secs. III, VI, and IX
PDF page: 12
Claim: This source does not define quantum instruments, process tensors, or a criterion for strict quantum non-Markovianity.
Gap scope: source_local

The conditioning objects are classical input and output sequences. The paper does not supply a
bridge from classical predictive causal states to a retained quantum environment.

## No finite-state guarantee [literature_gap]
Fact ID: bc1412-gap-finite-state
Source locator: Sec. VI paragraph following Definition 8 and Sec. XIII
PDF page: 13
Claim: This source does not guarantee that every channel has a finite-state or even countable-state epsilon-transducer.
Gap scope: source_local

The text restricts graphical treatment to finite or countable state sets and later gives a channel
whose minimal unifilar epsilon-transducer has countably infinitely many states and infinite Markov
order.

## No proved history--generator equivalence [literature_gap]
Fact ID: bc1412-gap-history-generator-equivalence
Source locator: Sec. XI
PDF page: 18
Claim: This source does not prove equivalence of the history and generator specifications of an epsilon-transducer.
Gap scope: source_local

Section XI calls the equivalence likely by analogy with epsilon-machines and explicitly leaves its
proof to future work.

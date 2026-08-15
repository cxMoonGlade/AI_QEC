+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2507.11424"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2507.11424v2"
source_artifact = "outputs/papers/pepo_survey/2507.11424.pdf"
source_sha256 = "780b8fad4917a9a2031aff235a699999f47b95602922d6ddf912ef946912ce00"
title = "Simulating and Sampling from Quantum Circuits with 2D Tensor Networks"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/RUDOLPH_TINDALL_2507_11424_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "ee40eb662be32f1ba2c4064424ad6759405fe61483d939a2eef161700965cedc"
admission_status = "source_only_reviewed"
admission_reviewer = "codex-xhigh-source-review-2026-07-17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 3, 4, 5, 7, 8, 9, 11, 12, 13]

[[relations]]
predicate = "defines"
object_id = "terminal-tensor-network-sampling"
object_type = "method"
object_label = "terminal tensor-network sampling method"
fact_id = "fact.terminal-sampling-law"

[[relations]]
predicate = "defines"
object_id = "sample-probability-ratio"
object_type = "observable"
object_label = "sample probability ratio"
fact_id = "fact.probability-ratio"

[[relations]]
predicate = "defines"
object_id = "sample-kl-divergence"
object_type = "observable"
object_label = "sample KL divergence"
fact_id = "fact.sample-kld"

[[relations]]
predicate = "limits"
object_id = "finite-boundary-dimension-sampling"
object_type = "limitation"
object_label = "finite-boundary-dimension sampling"
fact_id = "fact.pathological-sampling-cost"
+++
# Full-text review — Rudolph and Tindall, “Simulating and Sampling from Quantum Circuits with 2D Tensor Networks”

## Source identity [paper_fact]
Fact ID: fact.source-identity
Source locator: Title page and arXiv version stamp, page 1
PDF page: 1
Claim: The source is the 14 September 2025 arXiv v2 preprint by Manuel S. Rudolph and Joseph Tindall on simulating unitary circuits and sampling final two-dimensional tensor-network states.

The PDF is dated 16 September 2025 and bears the arXiv:2507.11424v2 stamp dated 14 September
2025. It studies pure-state planar tensor-network ansätze matched to processor geometry, with a
generalized boundary-MPS contraction and sampling method.

## BP-conditioned gate truncation [paper_fact]
Fact ID: fact.gate-truncation
Source locator: Section II, Eq. (1), page 3
PDF page: 3
Claim: The two-site gate update truncates a BP-conditioned local SVD to state bond dimension chi and defines the discarded squared singular-value sum as an approximate gate error on loopy networks.

For an exact post-gate bond dimension `chi_prime`, Eq. (1) sums squared singular values from
`chi+1` through `chi_prime`. The equality to true gate infidelity is exact for a loop-free network
under the stated normalization, while the loopy-network expression is explicitly approximate. If no
singular value is discarded, the updated tensor network represents the post-gate state exactly.

## Approximate final-state fidelity [paper_fact]
Fact ID: fact.final-state-fidelity
Source locator: Section II, Eq. (2) and following paragraph, page 3
PDF page: 3
Claim: The product of per-gate retained weights is used as an approximate final-state fidelity rather than an exact loopy-network identity.

The paper defines `f_i=1-epsilon_i` and multiplies these terms over all circuit gates. Equation (2)
relates the product approximately to the squared overlap between the final tensor network and the
untruncated circuit state, and the accompanying text calls this a practical error metric rather than a
general exact bound.

## Generalized boundary-MPS contraction [paper_fact]
Fact ID: fact.boundary-mps-contraction
Source locator: Section II, boundary-MPS method, page 4
PDF page: 4
Claim: The generalized boundary-MPS method partitions any planar tensor network into a line and approximates successive MPS-MPO contractions with bond dimension R, becoming exact as R tends to infinity.

The network may be partitioned by columns, rows, or another ordering that forms a line of partitions.
A one-site variational fitting procedure compresses each partial contraction to an MPS of maximum
dimension `R`. The source distinguishes this contraction dimension from the state bond dimension
`chi`.

## Terminal sampling law [paper_fact]
Fact ID: fact.terminal-sampling-law
Source locator: Section II, sampling definitions and procedure, page 4
PDF page: 4
Claim: The terminal tensor-network sampling method draws a final computational-basis bitstring x from q(x), while p(x)=|<x|psi>|^2 is the terminal distribution encoded by the final tensor-network state.

The reverse pass contracts and caches approximations to the norm network using dimension `R_n`.
For every sample, a forward pass moves through the partitions and sites, forms conditional one-site
reduced density matrices, samples their projectors, and compresses the sampled amplitude network
with dimension `R_x`. Finite fitting errors generally make `q` differ from `p`.

## Sample probability ratio [paper_fact]
Fact ID: fact.probability-ratio
Source locator: Section II, Eq. (5), page 4
PDF page: 4
Claim: The sample probability ratio p(x)/q(x) has expectation under q equal to the norm of the represented tensor-network state.

Equation (5) expands the expectation as the sum of `p(x)` over all terminal bitstrings. The source
notes that this norm need not equal one after gate truncations. The ratio assesses individual
terminal samples and can also serve as an importance weight.

## Sample KL divergence [paper_fact]
Fact ID: fact.sample-kld
Source locator: Section II, Eq. (6), page 4
PDF page: 4
Claim: The sample KL divergence is defined as KLD(q,p)=E under q of log(q(x)/p(x)) for the terminal bitstring distributions.

The paper describes zero KLD as equality of the two distributions and values substantially below
one as typically indicating high-quality samples. The expectation is over bitstrings generated from
the finite-boundary-dimension sampler `q`.

## Separate terminal-probability contraction [paper_fact]
Fact ID: fact.separate-terminal-probability
Source locator: Section II, independent sample verification paragraph, page 4
PDF page: 4
Claim: The terminal probability p(x) can be evaluated after sampling by a separate boundary-MPS contraction of the amplitude network <x|psi>.

The numerical studies allow arbitrary sampling dimensions `R_x` and `R_n`, then recompute
`p(x)` with a boundary MPS of maximum dimension `2 chi`, which the authors report as sufficient for
their cases. Appendix Figure 7 also distinguishes this separate contraction from raising `R_x`
inside the sampler.

## LUCJ terminal-sampling result [paper_fact]
Fact ID: fact.lucj-sampling-result
Source locator: Section III, Figure 2 and accompanying text, page 5
PDF page: 5
Claim: For the studied LUCJ terminal states, the reported sample KLD reaches double-precision zero at R=50, while much smaller R suffices for the stated near-exact thresholds.

For the 52-qubit nitrogen circuit the paper reports KLD below about `10^-3` at `R=5`. For the
72-qubit 4Fe-4S circuit it reports KLD below about `10^-8` already at `R=1`. These are results for
the stated circuits and final tensor-network states, not a geometry-independent bound.

## Topology-dependent boundary dimension [paper_fact]
Fact ID: fact.topology-dependent-convergence
Source locator: Section III, Figure 4 and preceding discussion, page 7
PDF page: 7
Claim: Boundary-MPS convergence depends strongly on topology, with the tested 15-layer Willow state requiring about R=75 for converged local expectation values despite state bond dimension chi=20.

The heavy-hex results are nearly insensitive to `R` for the selected one-site observables, whereas
the Willow results require substantially larger contraction dimensions. The source associates this
difference with loop correlations and shows them through the primitive-loop BP diagnostic.

## Local observable versus full distribution [paper_fact]
Fact ID: fact.local-global-mismatch
Source locator: Section III, Figure 4 caption and discussion, page 7
PDF page: 7
Claim: The reported local expectation values can be accurate at sample KLD near 2 even though the full terminal distribution still differs from p.

The paper explicitly describes KLD as a global and potentially conservative sample-quality metric
for low-weight observables. Figure 4 compares selected single-site `Z` expectations from direct
contraction and from samples while the corresponding full-distribution discrepancy remains nonzero.

## GPU timing scope [paper_fact]
Fact ID: fact.gpu-timing-scope
Source locator: Section III, Figure 5 caption, page 8
PDF page: 8
Claim: The reported greater-than-35-fold GPU speedup is a 32-bit timing result for one 105-qubit Willow tensor network at chi=20 after 15 layers.

The comparison uses an Nvidia RTX A6000 and a multithreaded Intel Xeon 6244 Gold CPU for direct
norm contraction and terminal sample generation as boundary dimension changes. The 32-bit
statement appears in the Figure 5 timing caption; elsewhere the memory estimates for selected state
tensors explicitly use double-precision complex entries.

## Pathological sampling cost [paper_fact]
Fact ID: fact.pathological-sampling-cost
Source locator: Section IV, first paragraph on finite-dimensional pathological states, page 9
PDF page: 9
Claim: The source limits finite-boundary-dimension sampling by noting that some finite-dimensional tensor-network states require boundary dimension exponential in system size for perfect sampling.

The authors report no such signature in their tested locally generated circuit states and suggest a
connection to finite-speed information spreading. The statement nevertheless excludes a universal
claim that a modest `R` is always sufficient.

## Adaptive outcome sequences [literature_gap]
Fact ID: gap.adaptive-outcome-sequences
Source locator: Appendix, Figure 7 and complete sampling procedure, pages 11-12
PDF page: 11
Claim: The source does not define a joint sampling law for intermediate measurements, resets, or outcome-conditioned later operations.
Gap scope: source_local

Figure 7 begins with a final tensor-network state, precontracts its norm network, and then samples
all sites of one final computational-basis bitstring. The operation contains no mid-circuit
measurement update, reset map, adaptive gate selection, or temporal sequence of measurement rounds.

## Total-variation or logical-event guarantee [literature_gap]
Fact ID: gap.total-variation-logical-event
Source locator: Section II, Eqs. (5)-(6), and Section IV conclusion, pages 4 and 8-9
PDF page: 4
Claim: The source does not derive a total-variation bound or a logical-event error bound from terminal p/q ratios, sample KLD, local observables, or discarded singular values.
Gap scope: source_local

The source evaluates a terminal bitstring distribution and selected expectation values. It provides
no theorem converting its diagnostics into a uniform event-probability bound, and it does not study
an ordered multi-round measurement record or a derived logical event.

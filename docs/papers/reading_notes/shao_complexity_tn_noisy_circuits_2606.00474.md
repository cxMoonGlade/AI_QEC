+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2606.00474"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2606.00474v1"
source_artifact = "outputs/papers/pepo_survey/2606.00474v1.pdf"
source_sha256 = "d7722de0513b1aef061a66a43ea766492d4205674a522c72f880e0f497a237f8"
title = "Complexity of tensor network simulation for noisy quantum circuits"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/SHAO_2606_00474_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "20ac546a0ab6406553593b16edc4f41740844e2835f62b4b10cb8342c8a70274"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_peps_source_rebuild_xhigh_2026_07_17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5, 9, 10, 11, 13, 14, 15, 16, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

[[relations]]
predicate = "defines"
object_id = "squared-hilbert-schmidt-error-criteria"
object_type = "concept"
object_label = "squared Hilbert–Schmidt error criteria"
fact_id = "shao-error-criteria"

[[relations]]
predicate = "supports"
object_id = "oee-schmidt-rank-bounds"
object_type = "theorem"
object_label = "OEE-to-Schmidt-rank bounds"
fact_id = "shao-entropy-rank-bounds"

[[relations]]
predicate = "supports"
object_id = "depolarizing-oee-crossover"
object_type = "theorem"
object_label = "depolarizing OEE crossover"
fact_id = "shao-depolarizing-thresholds"

[[relations]]
predicate = "supports"
object_id = "whole-trajectory-prescribed-cut-approximation"
object_type = "theorem"
object_label = "whole-trajectory prescribed-cut approximation"
fact_id = "shao-whole-trajectory"

[[relations]]
predicate = "limits"
object_id = "cutwise-average-boundary-dimension"
object_type = "limitation"
object_label = "cutwise average boundary dimension"
fact_id = "shao-pepo-cutwise-scale"
+++
# Full-text review — Shao et al., “Complexity of tensor network simulation for noisy quantum circuits”

## Source identity [paper_fact]
Fact ID: shao-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The source is Shao, Zhao, Cheng, and Liu's arXiv:2606.00474v1 preprint “Complexity of tensor network simulation for noisy quantum circuits,” posted on 30 May 2026.

The title page lists affiliations at Tsinghua University and the Beijing Institute of Mathematical
Sciences and Applications. This record is pinned to the 48-page v1 artifact.

## Scientific scope [paper_fact]
Fact ID: shao-selection-scope
Source locator: Abstract, Introduction, and Table I
PDF page: 1
Claim: The source derives operator-entanglement and tensor-network rank bounds for noisy density-operator evolution under fixed product single-qubit depolarizing noise and two stronger-contraction classes of product single-qubit noise.

The results distinguish absolute from relative Hilbert–Schmidt approximation, one-dimensional MPO
statements from higher-dimensional cutwise PEPO scales, and average random-gate results from
worst-case arbitrary-gate results.

## Operator Schmidt entropies [paper_fact]
Fact ID: shao-oee-definitions
Source locator: Sec. II, Eqs. (1)–(4); Appendix A, Eqs. (A1)–(A4)
PDF page: 2
Claim: For an operator Schmidt decomposition `rho=sum_alpha lambda_alpha L_alpha tensor R_alpha`, the source defines unnormalized OEE as `-sum lambda_alpha^2 log_2 lambda_alpha^2` and normalized OEE by replacing each squared coefficient with `lambda_alpha^2/tr(rho^2)`.

If `t=tr(rho^2)`, the two entropies obey
`S_tilde_OE(rho)=S_OE(rho)/t+log_2(t)`. The normalized entropy is the entanglement
entropy of the normalized vectorized density operator.

## Squared Hilbert–Schmidt error criteria [paper_fact]
Fact ID: shao-error-criteria
Source locator: Appendix B, Eqs. (B2)–(B6)
PDF page: 10
Claim: The source's squared Hilbert–Schmidt error criteria are `||rho-rho_hat_chi||_2^2<=epsilon` for absolute accuracy and `||rho-rho_hat_chi||_2^2/||rho||_2^2<=delta` for relative accuracy, with the ordered Schmidt tail exactly equal to the squared error.

Absolute error is additive in the unnormalized operator and permits the zero-rank approximation when
`tr(rho^2)<=epsilon`. Relative error is the fraction of the remaining Hilbert–Schmidt weight in the
discarded tail; it is not defined as a ratio of unsquared norms.

## OEE-to-Schmidt-rank bounds [paper_fact]
Fact ID: shao-entropy-rank-bounds
Source locator: Appendix B, Theorems 4–5 and Eqs. (B7), (B13)
PDF page: 10
Claim: The OEE-to-Schmidt-rank bounds give a sufficient ordered-truncation rank `R_abs<=max{1,ceil((t-epsilon)2^(S_OE/epsilon))}` for `0<epsilon<t` and `R_rel<=max{1,ceil((1-delta)2^(S_tilde_OE/delta))}` for `0<delta<1`.

The proofs use the monotonicity of the ordered Schmidt weights and a contrapositive entropy bound.
These are sufficient rank bounds across one bipartition, with all tolerances fixed independently of
system size when polynomial scaling is inferred.

## Purity-controlled OEE bridge [paper_fact]
Fact ID: shao-purity-oee-bridge
Source locator: Appendix C, Theorem 6 and Eqs. (C15)–(C16)
PDF page: 13
Claim: Theorem 6 upper-bounds both unnormalized and normalized OEE by piecewise functions of subsystem dimensions and density-operator purity, thereby converting purity decay into operator-entanglement control.

The bound has separate regimes divided by the smaller-to-larger subsystem dimension ratio. The
source proves monotonicity and concavity properties of the resulting maximum-entropy functions in
Theorems 7 and 8.

## Depolarizing circuit model [paper_fact]
Fact ID: shao-depolarizing-model
Source locator: Sec. III, Eqs. (8)–(11); Appendix D, Eqs. (D1)–(D2)
PDF page: 2
Claim: The depolarizing model applies the identical product channel `D_lambda^tensor n` after every unitary layer, with `D_lambda(sigma)=(1-lambda)sigma+lambda I/2` and fixed `lambda`.

The final state is the unconditional density operator obtained by composing these noisy layers. The
unitaries are unrestricted for the geometry-independent entropy result; locality is added for the
whole-trajectory construction.

## Hypercontractive purity decay [paper_fact]
Fact ID: shao-purity-decay
Source locator: Appendix D, Lemma 9 and Eqs. (D3)–(D18)
PDF page: 24
Claim: Product-channel hypercontractivity and unitary invariance of Schatten norms give `tr(rho_L^2)<=2^(-n tanh(mu))` for pure input, where `mu=-L log(1-lambda)`.

The proof applies the product depolarizing hypercontractivity inequality backward through the layers.
The estimate is independent of gate geometry because every unitary preserves the required norms.

## Depolarizing OEE crossover [paper_fact]
Fact ID: shao-depolarizing-thresholds
Source locator: Main Theorem 1; Appendix D, Theorem 10 and Eqs. (D34)–(D55)
PDF page: 3
Claim: The depolarizing OEE crossover occurs after `O(1)` depth for `S_OE=O(log n)` and after `O(log n)` depth for `S_tilde_OE=O(log n)`, for fixed positive `lambda`, pure input, arbitrary intervening unitaries, and any fixed bipartition.

The explicit normalized-OEE proof chooses a depth proportional to
`(2 ln n-ln ln n)/[-2 ln(1-lambda)]`. The theorem is asymptotic in `n` for fixed noise strength.

## Sharp relative-depth lower scale [paper_fact]
Fact ID: shao-relative-sharpness
Source locator: Appendix D, Proposition 3 and Eqs. (D56)–(D80)
PDF page: 29
Claim: A product of Bell pairs across a balanced cut, evolved only by repeated product depolarization, retains super-logarithmic normalized OEE through a logarithmic-depth initial window, so no uniform normalized-OEE crossover can occur at `o(log n)` depth.

The construction uses identity unitary layers and computes the normalized operator-Schmidt
distribution exactly. This proves the scale of a uniform bound, not that every input or circuit is
hard until logarithmic depth.

## Whole-trajectory prescribed-cut approximation [paper_fact]
Fact ID: shao-whole-trajectory
Source locator: Main Proposition 1; Appendix D, Proposition 4 and Eqs. (D81)–(D82)
PDF page: 3
Claim: The whole-trajectory prescribed-cut approximation states that, for a one-dimensional bounded-range local circuit from `|0><0|^tensor n` with fixed product depolarizing noise, there exists a sequence `rho_hat_l` at every depth with polynomial bond dimension across one fixed cut and `||rho_l-rho_hat_l||_2^2<=epsilon||rho_l||_2^2`.

The local gates in each layer are disjoint and act on at most a constant number of consecutive
qubits. The cut and the fixed relative squared-error tolerance are chosen before the sequence is
constructed.

## Whole-trajectory construction [paper_fact]
Fact ID: shao-whole-trajectory-construction
Source locator: Appendix D, Eqs. (D84)–(D122)
PDF page: 31
Claim: The proof evolves exactly through an `O(log n)` initial segment and then alternates constant-length noisy blocks with best Hilbert–Schmidt rank truncation and an identity trace correction, using contraction of trace-zero errors to close an all-times induction.

At block endpoints the error is kept at `mu 2^(-n/2)` in Hilbert–Schmidt norm, and intermediate
states are obtained by exact evolution within a block. The discussion later says that a practical
scheme with certifiable accumulated-truncation-error control across a full simulation remains missing.

## General single-qubit contraction coefficient [paper_fact]
Fact ID: shao-general-noise-coefficient
Source locator: Sec. IV, Eqs. (15)–(16); Appendix E, Lemmas 11–12 and Eqs. (E1)–(E3)
PDF page: 3
Claim: After single-qubit pre- and post-unitary rotations, the source defines `c(N)=(t_X^2+t_Y^2+t_Z^2+D_X^2+D_Y^2+D_Z^2)/3` from the canonical Pauli-transfer parameters, with `c(N)<=1` and equality exactly for unitary channels.

The general-noise circuits apply the same channel independently to all sites after each
nearest-neighbor brickwall layer. Smaller `c` denotes stronger average contraction of Pauli
coefficients but is used with different additional assumptions in the two theorems.

## Average-case general-noise plateau [paper_fact]
Fact ID: shao-average-general-noise
Source locator: Main Theorem 2; Appendix E, Theorem 11 and Eqs. (E28)–(E38)
PDF page: 4
Claim: For independently drawn unitary 2-design two-qubit gates in a one-dimensional brickwall circuit and `c(N)<1/3`, unnormalized OEE is at most a constant at every layer with probability at least `1-4 L n [(1+3c)/2]^n`.

The appendix allows any initial density state in this average-case result. The probability estimate is
nontrivial when the displayed failure bound is below one and gives `1-L exp[-Omega(n)]` for
sufficiently large `n`.

## Worst-case general-noise bound [paper_fact]
Fact ID: shao-worst-general-noise
Source locator: Main Theorem 3; Appendix E, Theorem 13 and Eqs. (E69)–(E73)
PDF page: 4
Claim: For arbitrary nearest-neighbor two-qubit gate layers, a product input, and a single-qubit channel with a unique fixed point and `c(N)<1/48`, unnormalized OEE is `O(log n)` at every depth across a fixed cut.

For an arbitrary initial state, the same bound is established only after an `O(log n)` crossover.
The proof replaces the distant past by an auxiliary orbit and uses a Wasserstein-1 contraction bound;
it is an unnormalized-OEE result.

## Cutwise average boundary dimension [paper_fact]
Fact ID: shao-pepo-cutwise-scale
Source locator: Sec. V; Appendix F, opening paragraphs, Definition 2, and Eqs. (F1)–(F11)
PDF page: 4
Claim: The source defines the cutwise average boundary dimension as `chi_bar_partial(A)=R^(1/a(A))` for a target operator-Schmidt rank `R` across one prescribed PEPO cut with `a(A)` boundary edges.

This quantity records the boundary label capacity after coarse-graining the two sides. The appendix
explicitly says it does not construct local PEPO tensors realizing the Schmidt vectors, guarantee
simultaneous consistency across all cuts, or imply efficient contraction.

## Higher-dimensional scaling results [paper_fact]
Fact ID: shao-higher-dimensional-results
Source locator: Appendix F, Propositions 5–7, Corollary 6, and Theorem 14
PDF page: 46
Claim: Fixed-error entropy-to-rank bounds give polynomial cutwise average boundary dimensions at every depth for product depolarizing noise at absolute and relative squared-HS accuracy, and for general product noise with a unique fixed point and `c(N)<1/48` at absolute squared-HS accuracy.

The locality argument controls rank growth before the noise-induced crossover and the OEE bound after
it. The general-noise theorem assumes a bounded-degree interaction graph, disjoint two-qubit gates on
graph edges, a product input, and at most a constant times `a(A)` cut-crossing gates per layer.

## Stated limitations [paper_fact]
Fact ID: shao-stated-limitations
Source locator: Sec. VI, caveats and future-work paragraphs
PDF page: 5
Claim: The source states that the contraction thresholds may not be optimal, asymptotic prefactors may be large for weak noise or strict tolerances, the analysis is restricted to single-qubit noise, and long-range interactions and coherent noise remain open.

It also assumes i.i.d. depolarizing noise. The discussion distinguishes its full-density-operator
objective from few-observable tasks and says an implemented scheme that certifiably controls
accumulated truncation errors remains to be developed.

## Source-local unsupported adaptive measurement history [literature_gap]
Fact ID: shao-gap-adaptive-history
Source locator: Full-text circuit definitions in Secs. III–IV and Appendices D–F
PDF page: 1
Claim: This source does not establish an error or bond-dimension bound for adaptive measurements, feedback, stochastic branch trajectories, or a retained classical measurement history.
Gap scope: source_local

Every modeled layer consists of a unitary circuit layer followed by a fixed product channel. No
measurement instrument, outcome-conditioned map, reset, or classical register appears in the model.

## Source-local unsupported physical and simultaneous-all-cut certificate [literature_gap]
Fact ID: shao-gap-global-physical-certificate
Source locator: Proposition 4 and its proof; Appendix F opening caveat; Sec. VI
PDF page: 31
Claim: This source does not establish that the whole-trajectory approximants remain positive or that one constructed MPO or PEPO simultaneously realizes every cutwise rank and error bound.
Gap scope: source_local

The formal one-dimensional proposition fixes a cut, while the higher-dimensional appendix explicitly
separates a cutwise Schmidt-rank scale from local PEPO construction. The proof restores trace with an
identity correction but states no positivity theorem for the truncated approximant.

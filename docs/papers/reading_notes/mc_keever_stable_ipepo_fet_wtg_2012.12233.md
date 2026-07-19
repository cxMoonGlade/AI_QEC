+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2012.12233"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2012.12233v1"
source_artifact = "docs/papers/2012.12233v1.pdf"
source_sha256 = "c9d066eabc2cf1e4769f4d733737e0330a7882663a48894ed7f6073a0f502b48"
title = "Dynamics of two-dimensional open quantum lattice models with tensor networks"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/MCKEEVER_2012_12233_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "cc4003df2e92ddd5e23862feb35d2df47539d63908c36d89132efdd16f1d07c6"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_peps_record_round3_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [3, 4, 5, 8, 10, 11, 12, 13, 14]
+++
# Source review — Mc Keever and Szymańska

## Infinite PEPO representation [paper_fact]

Fact ID: fact.ipepo-representation
Source locator: Sec. II.B and Fig. 2(a)
PDF page: 3
Claim: The method represents the thermodynamic-limit density operator by a two-site-unit-cell infinite projected entangled-pair operator and vectorizes each pair of local bra and ket indices into one physical index of dimension `d^2`.

Each site tensor has four virtual indices of bond dimension `D`.  Separate trace and Hilbert--Schmidt effective environments are constructed by CTMRG for reduced-state evaluation and truncation optimization, respectively.

## PEPO positivity limitation [paper_fact]

Fact ID: fact.pepo-not-inherently-positive
Source locator: Sec. II.B, paragraph after Fig. 2(a)
PDF page: 3
Claim: The PEPO ansatz is not inherently positive, so not every tensor representation in the ansatz corresponds to a physical density operator.

The authors rely on positivity of the exact dynamical map and report that the reduced density matrices encountered in practice are usually physical; they do not impose an exact positivity-preserving parameterization on the compressed tensors.

## Trotterized enlarged-bond update [paper_fact]

Fact ID: fact.trotter-enlarged-bond
Source locator: Sec. II.C--D, Eqs. (3)--(8) and Fig. 2(b)--(f)
PDF page: 4
Claim: A first-order four-layer Trotter decomposition applies two-site Liouvillian maps to nearest-neighbour tensor pairs, after which an SVD produces an enlarged bond dimension `D'` that must be compressed back to `D`.

The pair map is evaluated with a Krylov-subspace method, and the displayed decomposition has local error of order `tau^2`.

## Alternative mixed-state fidelity [paper_fact]

Fact ID: fact.alternative-mixed-state-fidelity
Source locator: Sec. II.D, Eq. (9)
PDF page: 5
Claim: The Full Environment Truncation objective is the normalized Hilbert--Schmidt overlap `tr(rho phi) / sqrt(tr(rho^2) tr(phi^2))` between the untruncated and truncated represented operators.

The article identifies this as an alternative mixed-state fidelity and optimizes its square through a Rayleigh quotient; it is not the Uhlmann fidelity.

## Full Environment Truncation solve [paper_fact]

Fact ID: fact.fet-rayleigh-solve
Source locator: Appendix B--C and Figs. 8--9
PDF page: 12
Claim: FET contracts the enlarged two-site tensors with the Hilbert--Schmidt effective environment to form a fourth-rank bond environment and then alternates generalized-eigenvalue optimizations of the two isometries and the retained bond matrix.

For the Rayleigh quotient in `R`, the numerator matrix is an outer product and the maximizing vector can be written using a linear solve with the denominator matrix; the implementation instead permits full or iterative generalized eigensolvers for stability.

## Weighted Trace Gauge reuse [paper_fact]

Fact ID: fact.wtg-environment-reuse
Source locator: Sec. II.D, paragraph after Eq. (9)
PDF page: 5
Claim: After FET, the updated bond is transformed to Weighted Trace Gauge so that the preceding Hilbert--Schmidt environment can be recycled as the initial guess for the next CTMRG calculation.

The stated benefit is a reduction in the number of environment-renormalization iterations required at successive time steps.

## Simple-update comparator [paper_fact]

Fact ID: fact.simple-update-comparator
Source locator: Sec. II.D, final paragraph
PDF page: 5
Claim: The paper's simple-update comparator bypasses FET and WTG, retains the `D` largest post-SVD singular values, and uses coordinate-selection isometries that ignore the full environment.

The authors state that this choice is not generally optimal for their alternative-fidelity objective.

## Local trace-distance benchmark [paper_fact]

Fact ID: fact.local-trace-distance-benchmark
Source locator: Sec. III.B and Figs. 4--5
PDF page: 8
Claim: In the reported moderately damped dissipative-Ising benchmark, FET with WTG gives a nearest-neighbour reduced-density-matrix trace distance about one order of magnitude below simple update for bond dimensions greater than three.

The FET results improve systematically with increasing `D` in that benchmark, whereas the displayed simple-update results show only a small and non-systematic reduction.

## Localized exact-observable reference [paper_fact]

Fact ID: fact.localized-exact-reference
Source locator: Sec. III.A and Appendix D, Eq. (D1)
PDF page: 13
Claim: For the zero-transverse-field member of the dissipative-Ising family, the paper benchmarks local observables against an exact finite-support construction in which correlations remain localized.

An observable initially supported on a set `A` is evaluated by evolving a density operator on `A` together with the neighbouring set `B` selected by the two-local Liouvillian.

## Mixed-state cycle entropy [paper_fact]

Fact ID: fact.mixed-state-cycle-entropy
Source locator: Appendix E, Eq. (E1)
PDF page: 14
Claim: The mixed-state cycle entropy is the Shannon entropy of the normalized absolute eigenvalues of the bond environment contracted with two copies of the bond matrix.

The paper treats a value near zero as indicating negligible internal correlations and cites a working scale near `10^-3` above which direct WTG-coefficient truncation is not expected to be optimal in this algorithm.

## CTMRG leading cost [paper_fact]

Fact ID: fact.ctmrg-leading-cost
Source locator: Sec. IV, computational-complexity paragraph
PDF page: 11
Claim: The leading cost of the implemented CTMRG environment calculation is an SVD with scaling `O(chi_hs^3 D^6)`.

The authors identify environment recomputation at every time step as the principal computational contribution and suggest fixed-point or boundary-MPS environment solvers as possible accelerations.

## Global FET optimum [literature_gap]

Fact ID: gap.global-fet-optimum
Source locator: Sec. II.D, paragraph containing Eq. (9), and Appendix B--C
PDF page: 5
Claim: The paper does not prove that its alternating FET iterations find a global optimum of the joint truncation problem for arbitrary approximate environments.
Gap scope: source_local

The main text conditions the optimal-truncation statement on finding a global maximum, while the appendices specify alternating one-block Rayleigh-quotient solves.

## Compressed-representation positivity [literature_gap]

Fact ID: gap.compressed-representation-positivity
Source locator: Sec. II.B, positivity paragraph
PDF page: 3
Claim: The article does not provide a general certificate that every finite-bond compressed iPEPO encountered during the algorithm remains positive.
Gap scope: source_local

Physical reduced density matrices are reported as an empirical observation rather than guaranteed by the tensor parameterization.

## Sequential measurement law [literature_gap]

Fact ID: gap.sequential-measurement-law
Source locator: Sec. III.A--D and Figs. 3--6
PDF page: 10
Claim: The benchmarks do not establish an error bound for a joint sequence of conditional measurement outcomes generated from a finite-bond compressed state.
Gap scope: source_local

The reported validation surfaces are local or equal-time observables, reduced density matrices, internal alternative fidelity, cycle entropy, and convergence in tensor-network dimensions.

+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2508.00338"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2508.00338v2"
source_artifact = "outputs/papers/peps_foundation/2508.00338.pdf"
source_sha256 = "aee918b2bbaa345ad168cae8f341e51f70998b965b3997da6573aa6c0b912224"
title = "Truncating loopy tensor networks by zero-mode gauge fixing"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/SOKOLOV_DZIARMAGA_2508_00338_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "4d4f47f33a26dff844dbd088935932764933a758e2fa872fc5512e7ba53596d0"
admission_status = "source_only_reviewed"
admission_reviewer = "peps_carrier_source_round3_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5, 8, 10, 12, 13]

[[relations]]
predicate = "defines"
object_id = "zero-mode-gauge-freedom"
object_type = "method"
object_label = "zero-mode gauge freedom"
fact_id = "sokolov-exact-zero-mode-elimination"

[[relations]]
predicate = "measures"
object_id = "bond-loopiness-ratio"
object_type = "observable"
object_label = "loopiness ratio"
fact_id = "sokolov-loopiness-eat"
+++
# Full-text review — Sokolov, Zhang, and Dziarmaga, “Truncating loopy tensor networks by zero-mode gauge fixing”

## Source identity [paper_fact]
Fact ID: sokolov-source-identity
Source locator: Title page, author block, manuscript date, and arXiv version line
PDF page: 1
Claim: Ihor Sokolov, Yintai Zhang, and Jacek Dziarmaga authored this arXiv v2 preprint, whose manuscript is dated 28 July 2025 and whose arXiv version line is dated 4 November 2025.

The source introduces zero-mode truncation for loopy tensor networks and illustrates it with iPEPS and periodic-MPS calculations.

## Cut-state Gram metric [paper_fact]
Fact ID: sokolov-cut-state-gram
Source locator: Sec. II, Fig. 2(a), Eqs. (1)--(2)
PDF page: 2
Claim: Cutting one bond defines states `|psi_j>` whose Gram metric `g_ij=<psi_i|psi_j>` has a zero eigenvector exactly when those cut states have a linear dependence.

The tensor-network state is the sum of the cut states, and the Gram eigenvalues are ordered from largest to smallest.

## Exact zero-mode elimination [paper_fact]
Fact ID: sokolov-exact-zero-mode-elimination
Source locator: Sec. II, Eqs. (3)--(4)
PDF page: 3
Claim: The zero-mode gauge freedom with `z=-1/Z_D` removes the cut state corresponding to the largest-magnitude zero-vector component and reduces the bond dimension from `D` to `D-1` without changing the tensor-network state.

The coefficients multiplying the surviving cut states are absorbed into tensors adjacent to the opened bond.

## Compact near-zero objective [paper_fact]
Fact ID: sokolov-compact-nearzero-objective
Source locator: Sec. II, Eq. (5) and paragraph below
PDF page: 3
Claim: For a small nonzero compact-metric mode, applying the zero-mode elimination has leading represented-state norm-squared error `f=N_D/|Z_D|^2`.

The source therefore selects the mode with the smallest `f`, which need not be the mode with the smallest Gram eigenvalue alone.

## Pseudoinverse toy comparison [paper_fact]
Fact ID: sokolov-pseudoinverse-toy
Source locator: Sec. III, Eqs. (6)--(9)
PDF page: 3
Claim: In the displayed two-identical-state toy problem, the pseudoinverse returns a minimum-norm coefficient vector that keeps bond dimension two, whereas a homogeneous zero-mode shift gives an exact bond-dimension-one representation.

The comparison is an explicit singular two-state construction rather than a general convergence theorem for variational tensor updates.

## General matrix zero modes [paper_fact]
Fact ID: sokolov-general-matrix-zero-modes
Source locator: Sec. IV, Eqs. (10)--(17)
PDF page: 3
Claim: Opening both endpoints of a bond defines a `D^2×D^2` cut-state Gram metric whose matrix zero mode yields a singular update `I+zZ` and, after SVD factorization, a one-rank bond reduction.

For a diagonalizable zero mode the source chooses the inverse of its largest-magnitude eigenvalue for numerical stability and notes that the singularity persists for a general Jordan form.

## General near-zero objective [paper_fact]
Fact ID: sokolov-general-nearzero-objective
Source locator: Sec. IV, Eq. (19) and surrounding paragraphs
PDF page: 4
Claim: For an approximate matrix zero mode with Gram eigenvalue `N`, the leading represented-state norm-squared truncation objective is `f=N/|E_D|^2`.

The preferred mode minimizes this quotient rather than `N` alone, and the full metric is more expensive than the compact diagonal-subspace metric.

## Loopiness ratio and EAT factorization [paper_fact]
Fact ID: sokolov-loopiness-eat
Source locator: Sec. V, Eqs. (20)--(24) and Fig. 3
PDF page: 4
Claim: The loopiness ratio `l=lambda_2/lambda_1` measures the departure of the full cut-state metric from its leading left--right product approximation used by environment-assisted truncation.

The product is exact when the considered bond is the sole connection between the two sides; the EAT gauge diagonalizes the resulting left and right metric factors.

## Non-loopy reduction to EAT [paper_fact]
Fact ID: sokolov-nonloopy-eat-equivalence
Source locator: Sec. V, first paragraph on the non-loopy case
PDF page: 5
Claim: When the full metric factorizes exactly as the EAT product, zero-mode gauge truncation reduces to truncating the lowest EAT spectrum value and is therefore equivalent to EAT.

The source contrasts this exact product case with loopy metrics, for which general zero modes can remove correlations that EAT's product approximation does not represent.

## Gauge-field initialization evidence [paper_fact]
Fact ID: sokolov-gauge-field-initialization
Source locator: Sec. VIII, discussion of Figs. 8--10
PDF page: 8
Claim: In the reported `Z_2` gauge-field quench, ZMT3 gives the best tested initial and final local truncation errors, and its magnetization converges with bond dimension more quickly than the SVD-initialized evolution through `D=10`.

Unlike the Ising and Heisenberg examples, the final variational error in this example depends on the initialization.

## TRG switching threshold [paper_fact]
Fact ID: sokolov-trg-switching-threshold
Source locator: Sec. X, paragraphs defining ZMT1--ZMT3 and Fig. 14
PDF page: 10
Claim: In the TRG experiment, the threshold `delta` marks when sequential compression switches from the compact ZMT1 scheme to the matrix-mode ZMT2 or ZMT3 scheme while continuing to the same target bond dimension.

The threshold is introduced for this algorithmic switch; it is not stated as a universal physical-error tolerance.

## Initialization role [paper_fact]
Fact ID: sokolov-initialization-role
Source locator: Sec. XI, Conclusion
PDF page: 10
Claim: The source presents zero-mode truncation as an initialization followed by a separate variational optimization and reports generally better initial truncation errors than methods that ignore loopiness.

It identifies avoidance of poor local minima and fixed symmetry-sector sizes as reasons that initialization can affect the optimized result.

## Imperfect-mode correction [paper_fact]
Fact ID: sokolov-imperfect-mode-correction
Source locator: Appendix B, Eqs. (B8)--(B11)
PDF page: 12
Claim: For an imperfect general zero mode, `z=-1/E_D` gives `f_0=N/|E_D|^2`, while the appendix derives a corrected variational optimum that agrees with this expression only to leading order in small `N`.

Appendix C further perturbs the selected eigenmode for an `O(f^2)` improvement, at additional numerical cost.

## Approximate-metric exactness absent [literature_gap]
Fact ID: sokolov-gap-approximate-metric-exactness
Source locator: Secs. II--V, definitions of the cut-state metrics and EAT product approximation
PDF page: 4
Claim: This source does not prove that a null vector of an arbitrary approximate local environment is an exact null vector of the full cut-state Gram metric.
Gap scope: source_local

Exact state preservation follows from exact linear dependence of the cut states, whereas the EAT factorization is explicitly approximate for a loopy bond.

## Measurement-law certification absent [literature_gap]
Fact ID: sokolov-gap-measurement-law
Source locator: Sec. XI, Conclusion and stated benchmark scope
PDF page: 10
Claim: This source does not derive a bound from its local norm-squared truncation objectives or loopiness ratio to a multi-time measurement-outcome probability law.
Gap scope: source_local

The reported evidence consists of initial and final local truncation errors plus selected model observables after variational optimization.

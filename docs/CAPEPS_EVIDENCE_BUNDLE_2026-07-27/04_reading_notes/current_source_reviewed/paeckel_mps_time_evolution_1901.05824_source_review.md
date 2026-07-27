+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1901.05824"
source_version = "v3"
source_uri = "https://arxiv.org/abs/1901.05824v3"
source_artifact = "docs/papers/1901.05824v3.pdf"
source_sha256 = "1ce466ed9ec3091ee1a8548cf42a84551584cd5d6f13b0d32a418fcdc981fbb9"
title = "Time-evolution methods for matrix-product states"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/PAECKEL_1901_05824_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "97366fa6391b8c51f60fcf09d2812f5f15ca9981c12bc4f5cb7e63a69673289a"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_source_rebuild_xhigh_2026_07_17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 7, 8, 9, 18, 19, 47, 49, 50, 78]

[[relations]]
predicate = "defines"
object_id = "mps-mixed-canonical-cut"
object_type = "concept"
object_label = "mixed-canonical matrix-product-state cut"
fact_id = "paeckel-canonical-cut"

[[relations]]
predicate = "defines"
object_id = "direct-svd-discarded-weight"
object_type = "observable"
object_label = "direct-SVD discarded weight"
fact_id = "paeckel-direct-svd-error"

[[relations]]
predicate = "limits"
object_id = "sequential-svd-local-optimality"
object_type = "limitation"
object_label = "sequential cutwise SVD local optimality"
fact_id = "paeckel-sequential-svd-limit"

[[relations]]
predicate = "defines"
object_id = "tebd-error-decomposition"
object_type = "concept"
object_label = "TEBD time-step and truncation errors"
fact_id = "paeckel-tebd-error-separation"

[[relations]]
predicate = "defines"
object_id = "tdvp-error-decomposition"
object_type = "concept"
object_label = "TDVP error decomposition"
fact_id = "paeckel-tdvp-errors"
+++
# Full-text review — Paeckel et al., “Time-evolution methods for matrix-product states”

## Source identity [paper_fact]
Fact ID: paeckel-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The source is Paeckel et al.'s arXiv:1901.05824v3 review “Time-evolution methods for matrix-product states,” dated 14 November 2019.

The title page names Sebastian Paeckel, Thomas Köhler, Andreas Swoboda, Salvatore R. Manmana,
Ulrich Schollwöck, and Claudius Hubig. This record is pinned to the v3 arXiv artifact rather than
using an unversioned journal copy.

## Scientific scope [paper_fact]
Fact ID: paeckel-selection-scope
Source locator: Abstract and Sec. 1
PDF page: 1
Claim: The review compares methods that construct time-evolved matrix-product states for finite quantum systems under real- or imaginary-time Schrödinger evolution.

The compared families are TEBD, the MPO `W^I/W^II` construction, global and local Krylov methods,
and one- and two-site TDVP. The review's primary object is a time-evolved MPS, with examples drawn
from closed-system many-body dynamics.

## Mixed-canonical cut [paper_fact]
Fact ID: paeckel-canonical-cut
Source locator: Secs. 2.4–2.6.1, Eqs. (11)–(15) and Figs. 4–6
PDF page: 7
Claim: A mixed-canonical matrix-product-state cut supplies orthonormal effective bases on both sides of the selected bond, so the bond tensor can be treated as the coefficient matrix for that bipartition.

Left- and right-normalized tensors satisfy the identities in Eqs. (11)–(12). Placing the
orthogonality center at a bond yields the effective left and right bases used in Eq. (14), after which
the bond coefficient tensor admits the SVD in Eq. (15).

## Direct rank truncation [paper_fact]
Fact ID: paeckel-direct-svd-operation
Source locator: Sec. 2.6.1, Eqs. (15)–(16)
PDF page: 9
Claim: Direct rank truncation at one canonical matrix-product-state cut retains the largest singular values and removes the corresponding rows and columns of the singular-vector factors.

The source presents this as the approximation optimal for the selected bond while the other site
tensors are kept fixed. The retained dimension `m'` is therefore a local cut choice, not a statement
about a whole sweep.

## Direct-SVD discarded weight [paper_fact]
Fact ID: paeckel-direct-svd-error
Source locator: Sec. 2.6.1, Eq. (17) and the paragraph immediately following it
PDF page: 9
Claim: The direct-SVD approximation error at one canonical cut is the square root of the direct-SVD discarded weight, defined as the sum of the squared omitted singular values.

The source uses this local quantity to choose a retained bond dimension and gives an illustrative target
discarded weight. The equality is stated in the canonical-cut setting constructed immediately before
Eq. (17).

## Sequential-SVD limitation [paper_fact]
Fact ID: paeckel-sequential-svd-limit
Source locator: Sec. 2.6.1, final paragraph
PDF page: 9
Claim: Sequential cutwise SVD local optimality does not guarantee a globally optimal compressed matrix-product state when truncation errors are large.

A left-to-right sweep makes later truncations depend on earlier ones. The source says the resulting
asymmetry is usually negligible for small truncations, but recommends subsequent variational
optimization when truncation errors are large.

## Variational-compression failure mode [paper_fact]
Fact ID: paeckel-variational-compression-limit
Source locator: Sec. 2.6.2, opening paragraph before Eq. (18)
PDF page: 9
Claim: Variational matrix-product-state compression can converge slowly or become trapped in a globally suboptimal state when initialized from an unsuitable state.

The direct-SVD result is suggested as a practical initial state for the sweeping variational
optimization. The source does not promote the iterative procedure into a guaranteed global optimizer.

## TEBD error separation [paper_fact]
Fact ID: paeckel-tebd-error-separation
Source locator: Sec. 4.1.1, first and final paragraphs
PDF page: 18
Claim: TEBD time-step and truncation errors are distinct: the Trotter error is controlled by step size and decomposition order, while MPS truncation is controlled by discarded weight or bond dimension and can affect unitarity and conserved quantities.

For fixed total evolution time, the source gives first- and second-order global time-step scaling for
TEBD1 and TEBD2. It separately recommends increasing the MPS bond dimension to estimate convergence
against truncation error.

## TDVP finite-manifold mechanism [paper_fact]
Fact ID: paeckel-tdvp-manifold
Source locator: Secs. 6.2–6.2.1, Eqs. (158)–(166)
PDF page: 47
Claim: TDVP constrains evolution to a matrix-product-state manifold by projecting the Schrödinger equation into the state-dependent tangent space and solving a sequence of local forward- and backward-evolution equations.

The one-site variant fixes the bond dimension; the two-site variant evolves a merged tensor and then
splits it, allowing the bond dimension to change.

## TDVP error decomposition [paper_fact]
Fact ID: paeckel-tdvp-errors
Source locator: Sec. 6.2.2, complete error discussion
PDF page: 49
Claim: The TDVP error decomposition contains finite-manifold projection error, finite time-step error, two-site SVD truncation error, and inexact local-solver error.

The source states that these errors react differently to step-size refinement: more, smaller steps
reduce integrator and local-solver error but can accumulate more projection and truncation operations.
It therefore recommends balancing the controls rather than treating a smaller step as uniformly better.

## TDVP conservation limitation [paper_fact]
Fact ID: paeckel-tdvp-conservation-limit
Source locator: Secs. 6.2.1–6.2.2, paragraphs on norm and energy conservation
PDF page: 50
Claim: Exact norm and energy conservation in one-site TDVP does not remove the need to establish convergence in the matrix-product-state bond dimension.

One-site TDVP has no SVD truncation and conserves norm and energy inside its projected evolution, yet
the source warns that finite-manifold projection can still yield inadequate dynamics and that bond
dimension convergence must be checked.

## Quantum-trajectory probability gap [literature_gap]
Fact ID: paeckel-gap-trajectory-probability
Source locator: Full-text scope established by the abstract and Secs. 1–9
PDF page: 78
Claim: This source does not define a quantum-trajectory no-jump or jump probability law and does not connect MPS truncation loss to physical stochastic branch mass.
Gap scope: source_local

The reviewed evolution equation is the Schrödinger equation for finite-system MPS. Lindblad jump
operators, unnormalized no-jump candidates, trajectory weights, and branch-mass residuals are outside
the paper's developed mechanism.

## Measurement-record law gap [literature_gap]
Fact ID: paeckel-gap-measurement-record-law
Source locator: Full-text scope established by the abstract, Sec. 8 examples, and Sec. 9
PDF page: 78
Claim: This source does not derive a multi-time binary measurement-record distribution or a bound from local MPS discarded weight to such a distribution.
Gap scope: source_local

The worked observables include correlations, spectral functions, particle and energy diagnostics,
magnetization, symmetry, and related state quantities. No repeated-measurement event law or logical-bit
statistic is reconstructed.

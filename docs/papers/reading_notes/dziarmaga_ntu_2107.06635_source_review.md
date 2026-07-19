+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2107.06635"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2107.06635v1"
source_artifact = "docs/papers/2107.06635v1.pdf"
source_sha256 = "219ef54a195b5d43903fe3c6546f4f2195868c6291ff95b5b6c4b428ab0d906f"
title = "Time evolution of an infinite projected entangled pair state: a neighborhood tensor update"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/DZIARMAGA_2107_06635_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "e012e97531ba14a7ec26f99ca3cc5daf8139ac3364715d7bfafc454a3d23e91d"
admission_status = "source_only_reviewed"
admission_reviewer = "peps_carrier_source_round2_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 3, 4, 5, 8, 9]

[[relations]]
predicate = "defines"
object_id = "neighborhood-tensor-update"
object_type = "method"
object_label = "neighborhood tensor update"
fact_id = "dziarmaga-ntu-metric"
+++
# Full-text review — Dziarmaga, “Time evolution of an infinite projected entangled pair state: a neighborhood tensor update”

## Source identity [paper_fact]
Fact ID: dziarmaga-source-identity
Source locator: Title page and version line
PDF page: 1
Claim: Jacek Dziarmaga authored this July 2021 v1 article on neighborhood tensor update for iPEPS time evolution, published as Physical Review B 104, 094411.

The source studies real- and imaginary-time evolution and includes unitary-quench and thermal-state benchmarks.

## Update-environment hierarchy [paper_fact]
Fact ID: dziarmaga-update-hierarchy
Source locator: Secs. I--II and Sec. VI hierarchy
PDF page: 9
Claim: The source orders SVDU, SU, NTU, and FTU or FU by the increasing tensor environment included in the post-gate truncation objective.

Increasing environment size is associated with faster convergence in state bond dimension in the reported comparisons, at increased computational cost.

## Reduced post-gate tensors [paper_fact]
Fact ID: dziarmaga-reduced-tensors
Source locator: Sec. II, Fig. 2
PDF page: 3
Claim: After applying a two-site Trotter gate, QR decompositions isolate fixed isometries and reduced matrices whose product is singular-value truncated to the target bond dimension.

The source defines the reduced tensors after gate application and excludes physical and ancilla indices from them.

## Simple-update metric [paper_fact]
Fact ID: dziarmaga-su-metric
Source locator: Sec. II, Eq. (1)
PDF page: 3
Claim: Simple update replaces the unweighted Frobenius metric by a product metric formed from the six adjacent diagonal bond tensors around the updated pair.

The paper notes that the associated bond-tensor inversions are a potential caveat.

## Neighborhood tensor update metric [paper_fact]
Fact ID: dziarmaga-ntu-metric
Source locator: Sec. II, Figs. 3--4
PDF page: 4
Claim: Neighborhood tensor update contracts a finite nearest-neighbor double-layer cluster exactly to obtain a metric that is Hermitian and nonnegative to machine precision.

The finite cluster includes the two bonds parallel to the updated bond that connect the left and right sides of the neighborhood.

## NTU quadratic objective [paper_fact]
Fact ID: dziarmaga-ntu-quadratic-objective
Source locator: Sec. II, Eqs. (2)--(5) and Fig. 5
PDF page: 5
Claim: NTU minimizes the metric-weighted squared difference between exact and truncated reduced-matrix products by alternating pseudoinverse updates for the two factors until the error converges.

The pseudoinverse tolerance can be adjusted dynamically to reduce the declared quadratic error.

## Full-environment contrast [paper_fact]
Fact ID: dziarmaga-ftu-environment-limit
Source locator: Sec. II, paragraphs spanning Figs. 3--4
PDF page: 4
Claim: FTU uses a CTMRG approximation to the infinite tensor environment, and that approximate metric can lose Hermiticity and nonnegativity even though it captures longer-range correlations.

NTU's exactness refers to its finite neighborhood rather than to the infinite environment.

## Unitary-quench stopping diagnostic [paper_fact]
Fact ID: dziarmaga-quench-diagnostic
Source locator: Sec. III, Figs. 6--7
PDF page: 5
Claim: The reported quench simulations terminate non-FU curves when energy per site deviates by more than `0.01` from its initial value and compare magnetization and connected correlations across update methods.

The most challenging critical quench developed the longest reported correlation range and favored the larger FTU environment in the stated benchmark.

## Thermal-state comparison [paper_fact]
Fact ID: dziarmaga-thermal-comparison
Source locator: Sec. V, Figs. 9--12 and Tables I--II
PDF page: 8
Claim: For the studied thermal Ising states, converged NTU estimates approach FTU or FU benchmarks with higher required state bond dimension, while smaller-environment updates can drift as bond dimension grows.

The paper also observes that correlation length alone does not determine convergence quality because the nature of the correlations matters.

## Stochastic branch mass not treated [literature_gap]
Fact ID: dziarmaga-gap-stochastic-branch-mass
Source locator: Full-text scope; deterministic iPEPS evolution in Secs. II--V
PDF page: 5
Claim: This source does not define stochastic jump or selective-measurement branches whose raw norms carry physical outcome probabilities.
Gap scope: source_local

Its update errors compare deterministic tensor-network states after Trotter gates.

## Multi-time record law not treated [literature_gap]
Fact ID: dziarmaga-gap-record-law
Source locator: Full-text scope and Sec. VI conclusion
PDF page: 9
Claim: This source does not establish a joint multi-time measurement-record law or a bound from NTU quadratic error to such a law.
Gap scope: source_local

The observables are state magnetization, correlations, energy drift, and thermal critical estimates.

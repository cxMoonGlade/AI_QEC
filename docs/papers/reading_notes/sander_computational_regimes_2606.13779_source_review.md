+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2606.13779"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2606.13779v1"
source_artifact = "docs/papers/sander_computational_regimes_mps_trajectories_2606.13779.pdf"
source_sha256 = "3b9ffcb54971c3ff0ea11eb4c2a10e3401f50349dbe3face5a2e1e3e8d6d06b7"
title = "Computational regimes in matrix-product-state-based quantum trajectory simulations"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/SANDER_2606_13779_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "11b1c821d30071bdb1178b3454f29262dd6a5f423db363b48da9af4547619a10"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_record_round2_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [3, 4, 5, 6, 10, 11, 12]
+++
# Source review — Sander et al.

## Physical and numerical controls [paper_fact]

Fact ID: fact.physical-numerical-controls
Source locator: Sec. II.C, Eq. (6)
PDF page: 3
Claim: The dissipation rate is a physical parameter, the time step is a numerical resolution parameter, and their product is only an emergent per-step stochasticity measure.

The article states that equal products do not uniquely characterize trajectory behavior across different discretizations.

## Three trajectory cost channels [paper_fact]

Fact ID: fact.three-cost-channels
Source locator: Sec. III.A, Eqs. (8)--(10)
PDF page: 4
Claim: The cost model separates per-trajectory memory, per-trajectory evolution work, and the number of trajectories required for statistical accuracy.

Within the model, the first two scale with different powers of the matrix-product-state bond dimension, while sampling cost depends on trajectory-estimator variance.

## Bond and sampling inflation [paper_fact]

Fact ID: fact.inflation-factors
Source locator: Sec. III.B, Eq. (11)
PDF page: 4
Claim: Bond inflation `alpha` and sampling inflation `kappa` compare two physically equivalent unravelings under one fixed simulation scenario.

The article states that both ratios depend on the Hamiltonian, noise model, observable, target accuracy, discretization, and system size rather than on an unraveling alone.

## Hardware decision boundaries [paper_fact]

Fact ID: fact.hardware-boundaries
Source locator: Sec. III.C, Eqs. (12)--(17)
PDF page: 6
Claim: The model yields different unraveling decision boundaries in worker-limited and memory-limited large-ensemble regimes.

The boundaries are `kappa = alpha^3` and `kappa = alpha^5` under the paper's cubic evolution-cost and quadratic memory-cost assumptions.

## Exact-reference sampling comparison [paper_fact]

Fact ID: fact.exact-reference-sampling
Source locator: Sec. IV.D, Fig. 5
PDF page: 10
Claim: In a ten-site exact-reference benchmark, sampling inflation varies independently of bond inflation across noise strength and time-step choices.

The compared trajectory counts are selected to reach a fixed absolute error threshold for one central-bond correlator over the displayed evolution.

## Pilot trajectory-count protocol [paper_fact]

Fact ID: fact.pilot-count-protocol
Source locator: Sec. V.A, Eq. (21)
PDF page: 11
Claim: A pilot estimate of the trajectory standard deviation gives a central-limit trajectory-count estimate for a prescribed standard error.

The resulting ratio supplies the sampling-inflation input to the paper's hardware model within the same algorithmic regime.

## Calibrated runtime prediction [literature_gap]

Fact ID: gap.calibrated-runtime
Source locator: Sec. V.B, final scope paragraph
PDF page: 12
Claim: The resource model is not a calibrated absolute wall-clock predictor.
Gap scope: source_local

The article omits implementation-dependent prefactors from batching, scheduling, tensor kernels, linear-algebra backends, communication, and fixed overheads.

## Complete outcome-law error [literature_gap]

Fact ID: gap.complete-outcome-law
Source locator: Sec. VI, scope discussion
PDF page: 12
Claim: The paper does not convert bond or sampling inflation into an error bound for a complete sequential measurement-outcome law.
Gap scope: source_local

Its accuracy discussion uses time-step convergence, controlled truncation assumptions, selected observable errors, and standard errors of trajectory averages.

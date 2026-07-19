+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1405.3259"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1405.3259v2"
source_artifact = "docs/papers/1405.3259v2.pdf"
source_sha256 = "5d7e010293770b0c97ac9c0b88075710ceda3a68988da7933dd2130621d8269a"
title = "Algorithms for finite projected entangled pair states"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/LUBASCH_1405_3259_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "dfe5f0e507970465c9af1df3b688da513c028f70d9842365a29a31e0d6c107ea"
admission_status = "source_only_reviewed"
admission_reviewer = "peps_carrier_source_round2_dual_review"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 13]

[[relations]]
predicate = "defines"
object_id = "finite-open-boundary-peps"
object_type = "model"
object_label = "finite open-boundary PEPS"
fact_id = "lubasch-finite-open-peps"

[[relations]]
predicate = "limits"
object_id = "peps-identity-norm-gauge"
object_type = "limitation"
object_label = "identity norm matrix"
fact_id = "lubasch-peps-gauge-limit"
+++
# Full-text review — Lubasch, Cirac, and Bañuls, “Algorithms for finite projected entangled pair states”

## Source identity [paper_fact]
Fact ID: lubasch-source-identity
Source locator: Title page and publication metadata
PDF page: 1
Claim: Michael Lubasch, J. Ignacio Cirac, and Mari-Carmen Bañuls authored this v2 article on finite projected entangled-pair-state algorithms, published as Physical Review B 90, 064425 in 2014.

The pinned artifact is the September 2014 version and contains the main text, three appendices, and the reference list.

## Finite open-boundary PEPS [paper_fact]
Fact ID: lubasch-finite-open-peps
Source locator: Sec. II, PEPS definition and Fig. 1
PDF page: 2
Claim: The source studies a finite open-boundary PEPS on a square lattice, with one physical index per lattice site and virtual bond dimension `D`.

For a lattice of `N=L×L` sites, contraction of the local tensors defines a pure state, while the virtual dimension restricts the maximum block entropy through an area-law scaling.

## Alternating local update [paper_fact]
Fact ID: lubasch-als-update
Source locator: Sec. II, Eq. (1)
PDF page: 2
Claim: A real- or imaginary-time Trotter step is approximated by minimizing `|| |psi> - O|phi> ||^2` with alternating least squares, whose one-site update solves `N_l A_l = b_l`.

The norm matrix `N_l` comes from the candidate-state norm network with the selected ket and bra tensors removed, while `b_l` comes from the overlap with the gate-evolved input state.

## Boundary-MPO contraction control [paper_fact]
Fact ID: lubasch-boundary-mpo-control
Source locator: Sec. III.A, Fig. 2 and first paragraph after the figure
PDF page: 3
Claim: Row-by-row PEPS norm contraction approximates a growing boundary by a boundary MPO of independent bond dimension `D'`, which controls contraction accuracy separately from the PEPS state bond dimension `D`.

The stated leading cost is `O(d D^6 D'^2)+O(D^4 D'^3)`; for the typical scaling `D' proportional to D^2` quoted there, the overall cost is `O(D^10)`.

## Cluster error and correlation length [paper_fact]
Fact ID: lubasch-cluster-correlation-scale
Source locator: Sec. III.A.1, Fig. 4 and footnotes 53--55
PDF page: 4
Claim: For the reported 21×21 Ising PEPS, an exponential fit of local-observable cluster-contraction error gives a characteristic cluster size `delta_0` that approximately tracks the separately fitted correlation length `zeta`.

The fits use the specified points `delta=2,4` and `x=4,8`, and the authors warn that the near-critical curves become more polynomial so both fitted scales depend more strongly on those choices.

## Exact and approximate environment positivity [paper_fact]
Fact ID: lubasch-environment-positivity
Source locator: Sec. III.A.2, Fig. 5
PDF page: 5
Claim: Exact contraction of the PEPS norm network yields a Hermitian positive-semidefinite norm environment, whereas the general approximate boundary-MPO contraction need not preserve positivity.

This distinction motivates positive-environment approximations, but positivity is a property of the approximation class rather than a statement that the approximation equals the exact environment.

## Purification approximation tradeoff [paper_fact]
Fact ID: lubasch-purification-tradeoff
Source locator: Sec. III.A.2, Figs. 6--7 and concluding paragraphs
PDF page: 5
Claim: Representing the boundary as a purification MPO can enforce positivity, but optimizing a general purification introduces nonlinear local equations and was judged more costly than the general boundary-MPO contraction in the reported PEPS setting.

The source therefore returns to the general boundary-MPO contraction for its cluster and full contractions while identifying purification optimization as potentially useful in other settings.

## Reduced-tensor construction [paper_fact]
Fact ID: lubasch-reduced-tensor
Source locator: Sec. III.B.1, Figs. 9--10
PDF page: 6
Claim: QR and LQ decompositions isolate the gate-affected reduced tensors so that a two-site update can vary fewer parameters than a full-tensor update.

The reduced pair environment is built after contracting the unchanged tensor parts into the periodic boundary MPO.

## Positive repair of a reduced environment [paper_fact]
Fact ID: lubasch-positive-repair
Source locator: Sec. III.B.1, Fig. 10 and accompanying paragraph
PDF page: 6
Claim: The approximate reduced environment is first Hermitianized and then has negative eigenvalues clipped to zero to construct a positive-semidefinite approximant.

Writing the repaired matrix as `U Sigma_+ U^dagger` also supplies the square root used by the following gauge construction.

## PEPS identity-norm gauge limitation [paper_fact]
Fact ID: lubasch-peps-gauge-limit
Source locator: Sec. III.B.2, first three paragraphs
PDF page: 7
Claim: An open-boundary MPS can be gauged so that its local norm matrix is the identity, while a generic PEPS has no local gauge transformation that guarantees an identity norm matrix.

The proposed PEPS gauges instead derive from the approximate environment before the update and aim to improve conditioning while leaving the represented state unchanged.

## Conditioning evidence and caution [paper_fact]
Fact ID: lubasch-conditioning-caution
Source locator: Sec. III.B.2, Table I and paragraph below Table I
PDF page: 8
Claim: The reported gauge choices lower observed norm-matrix condition numbers and accelerate alternating-sweep convergence, but the source states that a large condition number alone does not imply low solution accuracy.

The numerical results establish behavior in the studied Ising and Heisenberg updates rather than a general convergence theorem.

## Pseudoinverse and deterministic normalization [paper_fact]
Fact ID: lubasch-pseudoinverse-normalization
Source locator: Sec. III.B.3, stability bullet list
PDF page: 9
Claim: The finite-PEPS update uses a cutoff pseudoinverse for the ill-conditioned positive subspace of `N_l` and normalizes the PEPS after each set of Trotter gates for numerical stability.

The tensors are additionally rescaled so that their largest absolute entries agree.

## Stochastic branch mass not treated [literature_gap]
Fact ID: lubasch-gap-stochastic-branch-mass
Source locator: Full-text scope; deterministic imaginary-time update in Secs. II--IV
PDF page: 2
Claim: This source does not define unnormalized stochastic branches whose norms encode physical jump or measurement probabilities.
Gap scope: source_local

Its normalization discussion applies to a deterministic PEPS time-evolution workflow.

## Multi-time record law not treated [literature_gap]
Fact ID: lubasch-gap-multitime-record-law
Source locator: Full-text scope and Sec. V conclusions
PDF page: 13
Claim: This source does not establish a joint multi-time measurement-record distribution or a bound from its local environment and update diagnostics to such a distribution.
Gap scope: source_local

The demonstrated observables are norm-contraction errors, energies, order parameters, spin correlations, and linear-solve diagnostics.

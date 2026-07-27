+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2110.12726"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2110.12726v2"
source_artifact = "docs/papers/2110.12726v2.pdf"
source_sha256 = "58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184"
title = "Variational methods for contracting projected entangled-pair states"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/VANDERSTRAETEN_2110_12726V2_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "4cd67341564d8f8354252331f68e07abc35fad557dccbc01c2c7b9ca1ed26046"
admission_status = "draft_pending_review"
admission_reviewer = "pending_fresh_independent_source_only_rereview_after_repair"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18]

[[relations]]
predicate = "supports"
object_id = "vanderstraeten-hermitian-transfer-variational-contraction"
object_type = "method"
object_label = "Hermitian transfer matrix"
fact_id = "vander2110-variational-objective"

[[relations]]
predicate = "uses"
object_id = "peps-environment-bond-dimension-chi"
object_type = "model"
object_label = "environment bond dimension"
fact_id = "vander2110-d-vs-chi"

[[relations]]
predicate = "supports"
object_id = "ctmrg-versus-boundary-mps-contraction"
object_type = "method"
object_label = "boundary-MPS and CTMRG environments"
fact_id = "vander2110-ctmrg-boundary-comparison"

[[relations]]
predicate = "limits"
object_id = "generic-multisite-vumps-convergence"
object_type = "limitation"
object_label = "multi-site VUMPS"
fact_id = "vander2110-multisite-instability"

[[relations]]
predicate = "limits"
object_id = "hermitian-peps-incommensurate-correlations"
object_type = "limitation"
object_label = "dominant incommensurate correlations"
fact_id = "vander2110-hermitian-incommensurate-limit"
+++
# Full-text review — Vanderstraeten et al., arXiv:2110.12726v2

## Source identity [paper_fact]
Fact ID: vander2110-source-identity
Source locator: PDF page 1, title, author block, abstract, and arXiv version line
PDF page: 1
Claim: The reviewed source is the 18-page arXiv:2110.12726v2 preprint “Variational methods for contracting projected entangled-pair states” by Vanderstraeten and seven coauthors, with a visible version stamp of 7 June 2022.

## Source selection scope [paper_fact]
Fact ID: vander2110-selection-scope
Source locator: PDF page 1, Abstract and Introduction
PDF page: 1
Claim: The source studies approximate contraction of infinite PEPS, identifies a subclass with an algorithm-independent variational formulation, compares CTMRG and VUMPS environments, and proposes a finite-window method for general correlation functions.

The abstract explicitly says infinite-PEPS norms and expectation values cannot
be computed exactly in the setting considered and require approximation
algorithms.

## PEPS virtual and environment bond dimensions [paper_fact]
Fact ID: vander2110-d-vs-chi
Source locator: PDF pages 1--2, Introduction and Sec. II, first two paragraphs
PDF page: 2
Claim: The source distinguishes the PEPS virtual bond dimension \(D\), which controls the PEPS variational state class, from the environment bond dimension \(\chi\), which controls the approximate contraction.

## CTMRG environment update [paper_fact]
Fact ID: vander2110-ctmrg-update
Source locator: PDF page 2, Sec. II, CTMRG paragraph and Eqs. (5)--(7)
PDF page: 2
Claim: In the reviewed CTMRG description, environment tensors are grown by absorbing a PEPS layer and their bond dimensions are then truncated back to \(\chi\), with different truncation prescriptions possible.

## Boundary-MPS contraction [paper_fact]
Fact ID: vander2110-boundary-mps
Source locator: PDF pages 2--3, Sec. II, Eqs. (8)--(12)
PDF page: 2
Claim: The boundary-MPS approach treats the PEPS row transfer matrix as an MPO and approximates its dominant left and right fixed points by MPSs whose bond dimension is \(\chi\), using methods such as VUMPS.

## Finite-environment ambiguity [paper_fact]
Fact ID: vander2110-finite-environment-ambiguity
Source locator: PDF page 3, final paragraph of Sec. II
PDF page: 3
Claim: The source states that different environment types and contraction algorithms can give different local expectation values at a fixed \(\chi\), and that it is not generally clear that they converge to the same result even as \(\chi\to\infty\).

## Hermitian transfer conditions [paper_fact]
Fact ID: vander2110-hermitian-transfer
Source locator: PDF pages 3--4, Sec. III, Eqs. (13)--(20)
PDF page: 3
Claim: The source gives reflection/time-reversal and more general local tensor conditions under which the PEPS transfer matrix, including stated larger-unit-cell constructions, is Hermitian.

These conditions define a subclass; the source does not assert that arbitrary
PEPS transfer matrices are Hermitian.

## Hermitian-subclass incommensurate-correlation limit [paper_fact]
Fact ID: vander2110-hermitian-incommensurate-limit
Source locator: PDF page 12, Discussion and Outlook, paragraphs beginning “Given the power of this subclass”
PDF page: 12
Claim: Because the Hermitian subclass has only real transfer-matrix eigenvalues, and the cited MPS setting relates those eigenvalues to dominant correlation wavevectors, the source expects ground states with dominant incommensurate correlations, including critical states with incommensurate filling, to be poorly described by the subclass.

This is an expected applicability limitation stated by the authors, not a
proved general no-go theorem for all such PEPS.

## Square-lattice scope [paper_fact]
Fact ID: vander2110-square-lattice-scope
Source locator: PDF page 12, Discussion and Outlook, paragraph beginning “In this paper we have only looked”
PDF page: 12
Claim: The source studies square-lattice PEPS only and leaves triangular, kagome, and more complicated PEPS unit-cell settings for future work.

## Variational free-energy objective [paper_fact]
Fact ID: vander2110-variational-objective
Source locator: PDF page 4, Sec. IV.A, Eqs. (21)--(30)
PDF page: 4
Claim: For a Hermitian transfer matrix, the source expresses the infinite-PEPS norm through its leading transfer eigenvalue, defines the per-site proxy \(f=-\log\lambda\), and characterizes the fixed-\(\chi\) boundary MPS by the variational objective in Eq. (25).

The objective is a norm/free-energy-density quantity, not the physical
Hamiltonian energy or a global state fidelity.

## VUMPS fixed-point equivalence [paper_fact]
Fact ID: vander2110-vumps-equivalence
Source locator: PDF pages 4--5, Eqs. (29)--(35)
PDF page: 5
Claim: Within the stated one-row Hermitian setting, the source derives that the zero-gradient conditions of the variational objective correspond to the VUMPS fixed-point equations for the boundary MPS.

## Two-row variational construction [paper_fact]
Fact ID: vander2110-two-row-construction
Source locator: PDF pages 5--6, Sec. IV.B, Eqs. (36)--(43)
PDF page: 5
Claim: For the stated Hermitian two-row transfer construction, the source gives a variational treatment using alternating boundary MPSs and derives the corresponding coupled fixed-point equations.

## Three-row variational breakdown [paper_fact]
Fact ID: vander2110-three-row-breakdown
Source locator: PDF page 6, Sec. IV.C, Eqs. (44)--(48), and Appendix B, Eqs. (B1)--(B4), PDF pages 15--16
PDF page: 6
Claim: For three or more transfer rows, the source states that the free-energy variational principle underlying the displayed multi-site VUMPS fixed-point equations can break down, even though a normalized-fidelity optimality interpretation remains available.

The numerical failure evidence is separately retained in the Appendix-B fact
below, including Figs. 9--10 on PDF page 18.

## Finite-window correlation algorithm [paper_fact]
Fact ID: vander2110-window-mps
Source locator: PDF pages 6--8, Sec. V, Eqs. (49)--(68), with the local perturbation and finite-window operation in Eqs. (58)--(68)
PDF page: 8
Claim: The source represents a local transfer-matrix perturbation by a finite-window MPS and repeatedly applies and variationally compresses the window through normalized-fidelity objectives to sum two-point and more general \(N\)-point correlation contributions.

## Finite-chi gradient caveat [paper_fact]
Fact ID: vander2110-finite-chi-gradient-caveat
Source locator: PDF page 8, Sec. V.B, Energy gradient paragraphs
PDF page: 8
Claim: The source says automatic differentiation can evaluate an energy gradient at fixed environment bond dimension \(\chi\), while its approximate summation construction becomes fully compatible with the energy gradient only in the infinite-\(\chi\) regime.

## Benchmark workload [paper_fact]
Fact ID: vander2110-benchmark-workload
Source locator: PDF page 9, Sec. VI opening paragraph
PDF page: 9
Claim: The reported contraction benchmarks use optimized, symmetry-constrained infinite PEPS with PEPS virtual bond dimension \(D=5\) for the square-lattice \(J_1\)-\(J_2\) model at \(J_2=0\) and \(J_2=1/2\).

## Displayed monotone quantity [paper_fact]
Fact ID: vander2110-monotone-free-energy
Source locator: PDF page 9, Fig. 1 and Sec. VI.A, first paragraph
PDF page: 9
Claim: In the displayed variational boundary-MPS calculations, the source reports that \(f=-\log\lambda\) decreases monotonically as \(\chi\) increases, with slower convergence for the frustrated workload.

This fact is limited to the displayed variational norm objective.

## Direct optimization versus VUMPS [paper_fact]
Fact ID: vander2110-direct-vumps-runtime
Source locator: PDF pages 9--10, Figs. 2--3 and Sec. VI.A
PDF page: 9
Claim: For the displayed workload and implementation, VUMPS converges faster initially, whereas direct nonlinear optimization gives faster late-stage convergence; the paper reports wall-time plots rather than an asymptotic complexity theorem.

## CTMRG and boundary-MPS comparison [paper_fact]
Fact ID: vander2110-ctmrg-boundary-comparison
Source locator: PDF page 10, Sec. VI.B and Fig. 4
PDF page: 10
Claim: On the two displayed \(J_1\)-\(J_2\) PEPS workloads, boundary-MPS and CTMRG environments approach the same plotted energy values at larger \(\chi\), with slightly different finite-\(\chi\) behavior.

The comparison uses no independent exact contraction at the largest \(\chi\).

## Structure-factor qualification [paper_fact]
Fact ID: vander2110-structure-factor-qualification
Source locator: PDF pages 10--11, Sec. VI.C and Figs. 5--6
PDF page: 11
Claim: The source reports that its window-MPS method is most accurate for the displayed structure factors, but explicitly notes that the summed structure factor is not itself variational and that too small \(\chi\) can prevent convergence to the correct displayed result as the window grows.

## Multi-site VUMPS instability [paper_fact]
Fact ID: vander2110-multisite-instability
Source locator: Appendix B, PDF pages 15--18, Eqs. (B1)--(B14) and Figs. 7--10
PDF page: 18
Claim: In the source's three-row two-dimensional Ising transfer-matrix example, multi-site VUMPS becomes unstable near the critical temperature while the normalized-fidelity power method converges; the observed instability window is reported as largely independent of \(\chi\) in size and slightly shifted with increasing \(\chi\).

## No generic exact contraction guarantee [literature_gap]
Fact ID: vander2110-gap-generic-exactness
Source locator: PDF page 1, Abstract and Introduction; PDF page 3, end of Sec. II
PDF page: 1
Claim: This source does not establish exact or uniformly certified contraction of arbitrary PEPS; its variational characterization requires the stated Hermitian transfer-matrix subclass and finite-\(\chi\) contractions remain approximate.
Gap scope: source_local

## No finite-chi observable certificate [literature_gap]
Fact ID: vander2110-gap-finite-chi-certificate
Source locator: PDF pages 8--11, finite-\(\chi\) gradient caveat and benchmark sections
PDF page: 8
Claim: This source does not give a universal a priori error bound that maps a chosen finite environment bond dimension \(\chi\) to certified error in energy, correlation functions, conditional fidelity, or any Record-law observable.
Gap scope: source_local

## No global state-fidelity result [literature_gap]
Fact ID: vander2110-gap-global-fidelity
Source locator: PDF page 11, Discussion and Outlook
PDF page: 11
Claim: This source does not reconstruct an approximate global PEPS state at finite \(\chi\), bound its trace distance or fidelity to an exact state, or analyze PEPS virtual-bond truncation after a circuit update.
Gap scope: source_local

## No finite syndrome-circuit backend [literature_gap]
Fact ID: vander2110-gap-finite-circuit
Source locator: PDF page 11, Discussion and Outlook
PDF page: 11
Claim: This source does not implement finite-lattice gate evolution, XZZX syndrome extraction, selective trajectory simulation, or a full-PEPS circuit baseline.
Gap scope: source_local

## No measurement--reset--Record law [literature_gap]
Fact ID: vander2110-gap-instrument
Source locator: PDF page 11, Discussion and documented full-text scope
PDF page: 11
Claim: This source does not define selective Born branches, reset maps, ordered raw-history or prefix masses, detector/observable Record folds, conditional fidelity, or Record total variation.
Gap scope: source_local

## No Clifford augmentation [literature_gap]
Fact ID: vander2110-gap-clifford
Source locator: PDF page 11, Discussion and documented full-text scope
PDF page: 11
Claim: This source does not provide a stabilizer tableau, Clifford frame, non-stabilizer residual split, GCAMPS, or CAPEPS construction.
Gap scope: source_local

## No matched CAPEPS resource benchmark [literature_gap]
Fact ID: vander2110-gap-matched-resources
Source locator: PDF pages 9--11, benchmark scope and Discussion
PDF page: 10
Claim: This source does not compare CAPEPS with full PEPS at matched accuracy using maximum PEPS virtual bond, environment bond, runtime, peak memory, throughput, and Record-law error.
Gap scope: source_local

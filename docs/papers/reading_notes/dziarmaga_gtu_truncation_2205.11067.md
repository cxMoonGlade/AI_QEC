+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2205.11067"
source_version = "v3"
source_uri = "https://arxiv.org/abs/2205.11067v3"
source_artifact = "outputs/papers/pepo_survey/2205.11067.pdf"
source_sha256 = "f4f15976158cf506b476c9eb17c4390e3fa186934a54aad8d3727ee49e05af7f"
title = "Time evolution of an infinite projected entangled pair state: a gradient tensor update in the tangent space"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/DZIARMAGA_GTU_2205_11067_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "ce3705b8afac1b6c47c4a043f7e80feebfe7a3552ff67d5cfc70ed65d6aebdb6"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_peps_source_rebuild_xhigh_2026_07_17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 4, 5, 7, 8, 9]

[[relations]]
predicate = "defines"
object_id = "gradient-tensor-update"
object_type = "method"
object_label = "gradient tensor update"
fact_id = "gtu-tangent-step"

[[relations]]
predicate = "defines"
object_id = "ipeps-gram-schmidt-metric"
object_type = "concept"
object_label = "iPEPS Gram-Schmidt metric"
fact_id = "gtu-metric-gradient"

[[relations]]
predicate = "defines"
object_id = "ipeps-overlap-per-site"
object_type = "observable"
object_label = "iPEPS overlap per site"
fact_id = "gtu-overlap-per-site"

[[relations]]
predicate = "uses"
object_id = "svdu-ntu-gtu-pipeline"
object_type = "method"
object_label = "SVDU-NTU-GTU pipeline"
fact_id = "gtu-three-stage-pipeline"

[[relations]]
predicate = "limits"
object_id = "finite-bond-quasiparticle-horizon"
object_type = "limitation"
object_label = "finite-bond quasiparticle horizon"
fact_id = "gtu-entanglement-limit"
+++
# Full-text review — Dziarmaga, “Time evolution of an infinite projected entangled pair state: a gradient tensor update in the tangent space”

## Source identity [paper_fact]
Fact ID: gtu-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The source is Jacek Dziarmaga's arXiv:2205.11067v3 preprint “Time evolution of an infinite projected entangled pair state: a gradient tensor update in the tangent space,” posted as v3 on 11 July 2022.

The title page is dated 23 May 2022 and identifies Jagiellonian University as the author's affiliation.
This record is pinned to the nine-page v3 artifact.

## Scientific scope [paper_fact]
Fact ID: gtu-selection-scope
Source locator: Abstract and Sec. I
PDF page: 1
Claim: The source develops gradient tensor update for truncating infinite pure-state iPEPS during Suzuki–Trotter unitary evolution and benchmarks it on the two-dimensional transverse-field Ising model.

The method is positioned after simple, full, and neighbourhood updates and seeks a more direct
optimization of the overlap between an enlarged-bond target and its reduced-bond approximation.

## Gate-enlarged iPEPS target [paper_fact]
Fact ID: gtu-enlarged-target
Source locator: Sec. II, opening paragraphs and Fig. 1
PDF page: 2
Claim: Applying a rank-`r` nearest-neighbor Trotter gate to the checkerboard iPEPS enlarges the updated bond from `D` to `rD`, defining an exact target `phi` that is approximated by a new `D`-bond iPEPS `psi`.

The candidate tensors `A''` and `B''` are optimized alternately until the target-candidate overlap
converges. The target and candidate remain separate tensor networks throughout this definition.

## Tangent-space variation [paper_fact]
Fact ID: gtu-tangent-variation
Source locator: Sec. II, Eqs. (1)–(2)
PDF page: 2
Claim: A tensor variation is projected orthogonally to the current iPEPS and inserted into a quadratic normalized cost for approximating the enlarged-bond target.

Index `mu` enumerates the elements of the varied tensor. The projector removes the component parallel
to `psi`, so the linearized state variation lies in the tangent space at the current candidate.

## Metric and gradient [paper_fact]
Fact ID: gtu-metric-gradient
Source locator: Sec. II, Eqs. (3)–(5)
PDF page: 2
Claim: The iPEPS Gram-Schmidt metric and overlap gradient determine the quadratic-cost minimizer through a pseudoinverse of the metric.

Equation (3) subtracts the state-parallel component from derivative overlaps. Equation (4) compares
target and candidate derivative contractions, and Eq. (5) applies the metric pseudoinverse to that
gradient.

## Near-convergence approximation [paper_fact]
Fact ID: gtu-near-convergence-assumption
Source locator: Sec. II, Eq. (4) and the following sentence
PDF page: 2
Claim: The simplified gradient expression assumes the target-candidate overlap is approximately equal to the candidate norm, an approximation stated to become accurate close to convergence.

The preceding line in Eq. (4) retains the prefactor that is dropped in the approximate equality. The
source therefore marks this step as an approximation rather than an identity valid at arbitrary distance.

## Line-search update [paper_fact]
Fact ID: gtu-tangent-step
Source locator: Sec. II, Eqs. (6)–(7)
PDF page: 2
Claim: Gradient tensor update follows the pseudoinverse direction along a real one-parameter line and accepts the line-search point that maximizes logarithmic overlap per site.

For small line parameter `x`, the constructed iPEPS agrees with the tangent-space variation to linear
order. The nonlinear acceptance objective is evaluated directly rather than relying solely on the
quadratic expansion.

## Overlap per site [paper_fact]
Fact ID: gtu-overlap-per-site
Source locator: Sec. II, Eqs. (7) and (9)
PDF page: 3
Claim: The iPEPS overlap per site is the thermodynamic-limit `N`th root of the normalized squared target-candidate overlap and is used to monitor each truncation stage.

The source states that this intensive quantity avoids the orthogonality catastrophe of the extensive
overlap and can be evaluated with tensor-network contraction methods.

## Three-stage initialization [paper_fact]
Fact ID: gtu-three-stage-pipeline
Source locator: Sec. II, Eq. (8), Fig. 2, and the surrounding paragraphs
PDF page: 3
Claim: The SVDU-NTU-GTU pipeline initializes gradient optimization with neighbourhood tensor update, itself initialized by direct SVD truncation, to reduce the risk of trapping in local minima.

SVDU minimizes the top-panel local difference, NTU optimizes a larger neighbourhood cluster, and GTU
then alternates the tangent-space updates. The overlap per site is evaluated after every stage.

## Connected-correlation environment metric [paper_fact]
Fact ID: gtu-connected-metric
Source locator: Sec. III, Eqs. (10)–(12) and Fig. 3
PDF page: 3
Claim: The tangent metric is expressed as a sum of connected derivative correlations and evaluated by CTMRG in the same manner as a connected correlation function.

Translation invariance reduces the first derivative to a reference-site contraction. Subtracting the
disconnected component makes each derivative orthogonal to the state, so the source says nonzero terms
in the metric sum occur within the represented correlation range.

## Reduced-tensor parameterization [paper_fact]
Fact ID: gtu-reduced-tensors
Source locator: Appendix A and Fig. 6
PDF page: 7
Claim: Fixed QR isometries reduce GTU's variational matrices and metric dimension from `D^4 d` to `D^2 d` before the optimized tensors are reconstructed.

The source constructs reduced matrices from the SVD of the contracted gate tensors. CTMRG contractions
for the metric become more compact by a factor `D^2` in this representation.

## Finite-bond entanglement limitation [paper_fact]
Fact ID: gtu-entanglement-limit
Source locator: Sec. IV, discussion before the quench results
PDF page: 4
Claim: The finite-bond quasiparticle horizon limits real-time iPEPS because linearly growing bipartite entanglement after a sudden quench would require bond dimension to grow exponentially with time.

The source therefore expects any fixed-bond tensor-network simulation eventually to fail and frames GTU
as improving the use of available bond dimension rather than overcoming that asymptotic limitation.

## Sudden-quench benchmark [paper_fact]
Fact ID: gtu-quench-benchmark
Source locator: Sec. IV and Fig. 4
PDF page: 4
Claim: In the two declared Ising quenches, GTU at `D=6` reaches somewhat longer time than FU or NTU at `D=8` at criticality and more than doubles the FU `D=8` evolution time for the quench to `2 h_c`.

The simulations use time step `dt=0.01` and the same second-order Suzuki–Trotter decomposition as the
comparators. A curve terminates when energy per site drifts by `0.01` or the overlap error crosses its
threshold.

## Kibble–Zurek benchmark [paper_fact]
Fact ID: gtu-kibble-zurek-benchmark
Source locator: Sec. V, Eqs. (14)–(16) and Fig. 5
PDF page: 5
Claim: In the `D=3` Kibble–Zurek benchmark, GTU reaches quench times three to four times longer than the cited NTU study, while the longest data approach exponent `0.37` rather than the asymptotic `0.386`.

The source reports truncation-induced oscillations at the longest `tau_Q=12.8` and says they become more
severe for still longer quenches.

## Stagewise truncation benchmark [paper_fact]
Fact ID: gtu-stagewise-error-reduction
Source locator: Appendix B and Figs. 7–8
PDF page: 8
Claim: For the reported quench data, NTU reduces `1-O` several-fold from SVDU and subsequent GTU supplies a further 20–30 percent reduction.

Figure 7 uses stopping thresholds `2e-6` for the `2 h_c` quench and `5e-6` for the critical quench. These
values are benchmark controls attached to the source's overlap-per-site diagnostic.

## Contraction-certificate gap [literature_gap]
Fact ID: gtu-gap-contraction-certificate
Source locator: Sec. III and Appendix A, complete CTMRG and reduced-tensor discussions
PDF page: 7
Claim: This source does not bound the error introduced by a finite CTMRG environment, the metric pseudoinverse, or the alternating nonlinear optimization.
Gap scope: source_local

The source specifies how to compute and reduce the metric and reports numerical benchmarks. It supplies
no theorem converting finite-environment or overlap-per-site error into a finite-state norm, trace distance,
or uniform observable certificate.

## Open-system and record-law gap [literature_gap]
Fact ID: gtu-gap-open-record-law
Source locator: Full-text scope established by the abstract, Secs. I–VI, and appendices
PDF page: 9
Claim: This source does not derive mixed-state open-system evolution, stochastic trajectory probabilities, or a repeated measurement-record law from GTU truncation.
Gap scope: source_local

The developed mechanism is unitary evolution of an infinite pure-state checkerboard iPEPS. Its outputs
are pure-state overlap per site, energy, magnetization, and excitation energy rather than branch weights or
multi-time measurement strings.

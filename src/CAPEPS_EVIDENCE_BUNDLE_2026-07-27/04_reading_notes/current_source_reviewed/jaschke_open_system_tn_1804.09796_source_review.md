+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1804.09796"
source_version = "v2"
source_uri = "https://arxiv.org/abs/1804.09796v2"
source_artifact = "docs/papers/1804.09796v2.pdf"
source_sha256 = "62e6b0ceb9fbce3da5f938968a728873b50953d87e1506f43e1358828714919f"
title = "One-dimensional many-body entangled open quantum systems with tensor network methods"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/JASCHKE_1804_09796_PROJECT_FIT_AUDIT_2026-07-17.md"
audit_packet_sha256 = "a152a9bc3cb72aa178cb165141908292fd62cfaa53e9104d97a626a678bf3dfe"
admission_status = "source_only_reviewed"
admission_reviewer = "mps_source_rebuild_xhigh_2026_07_17"
admission_date = "2026-07-17"
visually_checked_pages = [1, 2, 3, 10, 11, 12, 17, 19, 24]

[[relations]]
predicate = "defines"
object_id = "qt-effective-nonhermitian-hamiltonian"
object_type = "model"
object_label = "quantum-trajectory effective non-Hermitian Hamiltonian"
fact_id = "jaschke-effective-hamiltonian"

[[relations]]
predicate = "limits"
object_id = "solver-induced-norm-error"
object_type = "limitation"
object_label = "solver-induced norm error"
fact_id = "jaschke-solver-norm-caveat"

[[relations]]
predicate = "defines"
object_id = "qt-jump-channel-selection"
object_type = "method"
object_label = "quantum-trajectory jump-channel selection"
fact_id = "jaschke-jump-selection"

[[relations]]
predicate = "limits"
object_id = "nonlinear-trajectory-observable"
object_type = "limitation"
object_label = "nonlinear trajectory observable"
fact_id = "jaschke-nonlinear-observables"
+++
# Full-text review — Jaschke, Montangero, and Carr, “One-dimensional many-body entangled open quantum systems with tensor network methods”

## Source identity [paper_fact]
Fact ID: jaschke-source-identity
Source locator: Title page and arXiv version line
PDF page: 1
Claim: The source is Jaschke, Montangero, and Carr's arXiv:1804.09796v2 article “One-dimensional many-body entangled open quantum systems with tensor network methods,” dated 30 August 2018.

This record is pinned to the 24-page v2 arXiv artifact. The title page identifies the three authors and
frames the work as a comparison implemented in the Open Source Matrix Product States package.

## Scientific scope [paper_fact]
Fact ID: jaschke-selection-scope
Source locator: Abstract and Sec. I
PDF page: 2
Claim: The article gives a side-by-side technical and convergence comparison of quantum trajectories, matrix-product density operators, and locally purified tensor networks for one-dimensional Lindblad dynamics.

It treats transient time evolution rather than variational steady-state computation. The examples cover
finite-temperature Ising states, exciton transport with emission and dephasing, and a dephased
Bose–Hubbard double well.

## Lindblad approximation regime [paper_fact]
Fact ID: jaschke-lindblad-regime
Source locator: Secs. I–II, Eq. (1) and the paragraph following Eq. (2)
PDF page: 3
Claim: The source's Lindblad dynamics assumes the Born–Markov and secular approximations, including separated environment, system, and equilibration time scales.

The article presents the Lindblad equation as norm-, Hermiticity-, and positivity-preserving at the
density-operator level, while explicitly limiting its physical applicability to the stated weak-coupling
and reservoir assumptions.

## Open-system tensor-network representations [paper_fact]
Fact ID: jaschke-representations
Source locator: Secs. I–II, discussion after Eq. (2)
PDF page: 3
Claim: Quantum trajectories evolve pure-state MPS samples, whereas matrix-product density operators and locally purified tensor networks evolve representations of the full density operator.

A trajectory keeps the closed-system local physical dimension but introduces a sampling cost across
trajectories. The two density-operator routes carry different auxiliary dimensions and positivity
properties.

## Trajectory ensemble representation [paper_fact]
Fact ID: jaschke-trajectory-ensemble
Source locator: Sec. III.B, Eq. (24)
PDF page: 10
Claim: The quantum-trajectory method represents a mixed state as an ensemble sum of pure-state projectors.

This ensemble identity motivates evolving each realization as an MPS and reconstructing density-operator
quantities statistically rather than storing the full density matrix during every trajectory.

## Effective non-Hermitian Hamiltonian [paper_fact]
Fact ID: jaschke-effective-hamiltonian
Source locator: Sec. III.B, Eq. (25)
PDF page: 11
Claim: The quantum-trajectory effective non-Hermitian Hamiltonian is the system Hamiltonian minus one half of `i` times the sum of `L_nu^dagger L_nu`, and its norm loss is used to determine jump timing.

The source changes Hermitian Krylov–Lanczos steps to non-Hermitian Krylov–Arnoldi steps and requires
non-Hermitian matrix exponentiation for the affected time-evolution methods.

## Solver norm caveat [paper_fact]
Fact ID: jaschke-solver-norm-caveat
Source locator: Sec. III.B, paragraph immediately after Eq. (25)
PDF page: 11
Claim: Solver-induced norm error can contaminate the physical norm loss used for quantum-trajectory jump timing because the local Runge–Kutta method can enhance or prevent the loss caused by the effective Hamiltonian.

This is stated as an additional problem specific to that local integrator; the source does not provide a
post hoc correction that separates the two losses.

## Waiting-time jump trigger [paper_fact]
Fact ID: jaschke-waiting-time-trigger
Source locator: Sec. III.B, algorithm steps (i)–(iii)
PDF page: 12
Claim: The trajectory algorithm draws a uniform norm threshold, propagates under the effective Hamiltonian without renormalizing, and triggers a jump when the propagated-state norm falls below that threshold.

After each jump the state is normalized and the procedure restarts with a fresh threshold. If the norm
has not crossed the threshold, the unnormalized no-jump evolution continues.

## Jump-channel selection [paper_fact]
Fact ID: jaschke-jump-selection
Source locator: Sec. III.B, steps (a)–(c) and Fig. 3
PDF page: 12
Claim: Quantum-trajectory jump-channel selection normalizes the expectations `p_nu = <psi|L_nu^dagger L_nu|psi>`, samples one channel, applies its Lindblad operator, and then renormalizes the state.

The source calls the `p_nu` values unweighted probabilities and forms their conditional distribution by
dividing by their sum only after a jump has been triggered.

## Many-body string jump weights [paper_fact]
Fact ID: jaschke-string-jump-weights
Source locator: Sec. III.B, Fig. 3(b) and its caption
PDF page: 12
Claim: For a many-body string Lindblad term, evaluating its jump weight requires contracting every nonidentity local factor of the string with the matrix-product state before measuring the resulting norm.

Figure 3 contrasts this network with the single-site contraction. The article provides the contraction
pattern, not a finite-bond error theorem for applying such a string.

## Linear trajectory observables [paper_fact]
Fact ID: jaschke-linear-observables
Source locator: Sec. III.B, Eq. (26)
PDF page: 12
Claim: A density-operator observable linear in the state is estimated by an equal-weight average of its pure-state value over the simulated trajectories.

This averaging can be performed after trajectories finish and is compatible with the data-parallel
execution discussed by the source.

## Nonlinear observable limitation [paper_fact]
Fact ID: jaschke-nonlinear-observables
Source locator: Sec. III.B, Eq. (27) and the following paragraph
PDF page: 12
Claim: A nonlinear trajectory observable such as density-matrix purity is not the average of the corresponding pure-trajectory value and can require all pairwise trajectory contractions.

The pure-state purity of every trajectory equals one, while the reconstructed mixed-state purity does
not. The source notes that this prevents simple a posteriori averaging unless the trajectory states were
saved or synchronized at measurement time.

## Example-specific convergence separation [paper_fact]
Fact ID: jaschke-example-convergence
Source locator: Sec. IV.B, discussion of Fig. 6(b)–(d)
PDF page: 17
Claim: In the exciton example, the quantum-trajectory error at 500 trajectories is sampling-limited, whereas the compared MPDO and LPTN errors arise from tensor-network truncation and time decomposition.

The source states that more trajectories can improve the trajectory estimate according to the law of
large numbers. It also stresses that the resource ranking is example-dependent and affected by the low
bond dimension required by this particular model.

## Finite-bond trajectory-law gap [literature_gap]
Fact ID: jaschke-gap-finite-bond-trajectory-law
Source locator: Sec. III.B mechanism and Sec. IV convergence studies
PDF page: 19
Claim: This source does not prove that a finite-bond matrix-product trajectory preserves the untruncated no-jump and jump probability law.
Gap scope: source_local

The full-text convergence studies compare selected observables across methods, bond dimensions, exact
diagonalization, or analytical examples. They do not derive a probability-law bound from an MPS
truncation or projection diagnostic.

## Measurement-record law gap [literature_gap]
Fact ID: jaschke-gap-measurement-record-law
Source locator: Full-text scope established by the abstract, Secs. III–V, and appendices
PDF page: 24
Claim: This source does not define a repeated binary measurement-record law or connect trajectory and truncation errors to the distribution of such records.
Gap scope: source_local

The source measures physical observables such as particle number, moments, and center of mass. It does
not construct temporal detector events, logical bits, or a full law over multi-round measurement strings.

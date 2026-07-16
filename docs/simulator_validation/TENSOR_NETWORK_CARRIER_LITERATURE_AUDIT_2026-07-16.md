# Tensor-network carrier literature audit — 2026-07-16

## Decision and frozen question

This packet answers a narrower question than “which tensor-network library is best”:

> What mathematical object is represented and optimized by the restricted MPS and PEPS carriers, what
> objects are represented by the external implementations, and which truncation diagnostics can be
> transferred without silently replacing the declared multi-time output law by a state- or energy-level
> surrogate?

The load-bearing invariant is the joint detector/observable record distribution declared by
`docs/SIMULATOR.md`. State fidelity, local expectation values, ground-state energy, an environment
residual, and a single-cut discarded weight are auxiliary numerical diagnostics unless a separate bridge
to that joint record law has been established.

The decision alternatives were frozen before inspecting outcomes:

1. stochastic pure-state MPS trajectory versus deterministic MPDO or purification evolution;
2. finite open-boundary PEPS trajectory versus periodic thermodynamic-limit iPEPS;
3. state-update approximation versus approximate contraction used to read a Born probability;
4. local truncation metric versus an independently evaluated multi-time record distribution.

Kill condition: if the literature does not establish a local-truncation-to-sequential-record bound for the
actual finite qutrit trajectory, no local metric is allowed to authorize production pruning on its own.

## Source acquisition and integrity

The following primary sources were reviewed across the full text, with the load-bearing sections
close-read. Load-bearing equation pages were rendered from the PDF and visually checked against the
extracted text. SHA-256 binds every claim below to the local artifact.

| Source | Pinned artifact | SHA-256 | Visually checked PDF pages |
|---|---|---|---|
| Jaschke, Montangero, and Carr, *One-dimensional many-body entangled open quantum systems with tensor network methods* | `docs/papers/1804.09796v2.pdf` | `62e6b0ceb9fbce3da5f938968a728873b50953d87e1506f43e1358828714919f` | 3, 10, 11, 12 |
| Sander et al., *Large-scale stochastic simulation of open quantum systems* | `docs/papers/2501.17913v2.pdf` | `9c2b2f2584da0270ef740c5e9ef0b5bc5d2f0fa88326bd0b8b7f04d634dcd2b5` | 3, 8, 10, 11 |
| Paeckel et al., *Time-evolution methods for matrix-product states* | `docs/papers/1901.05824v3.pdf` | `1ce466ed9ec3091ee1a8548cf42a84551584cd5d6f13b0d32a418fcdc981fbb9` | 8, 9, 18, 19, 49, 50 |
| Lubasch, Cirac, and Bañuls, *Unifying projected entangled pair state contractions* | `docs/papers/1405.3259v2.pdf` | `5d7e010293770b0c97ac9c0b88075710ceda3a68988da7933dd2130621d8269a` | 2, 3, 5, 7, 9 |
| Evenbly, *Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops* | `docs/papers/1801.05390v2.pdf` | `a5578205d15a7c44a11e0508e400109393c555be243d8478c20f668f75997f40` | 2, 3, 5, 6, 11 |
| Dziarmaga, *Time evolution of an infinite projected entangled pair state: Neighborhood tensor update* | `docs/papers/2107.06635v1.pdf` | `219ef54a195b5d43903fe3c6546f4f2195868c6291ff95b5b6c4b428ab0d906f` | 3, 5, 9 |
| Naumann et al., *An introduction to infinite projected entangled-pair state methods for variational ground state simulations using automatic differentiation* | `docs/papers/naumann_ipeps_variational_lecture_notes_2024.pdf` | `9e34cadaa235c94efc03cf1b9bf795764b55a3c7a42e0168ee3949b283c66c45` | 3, 5, 6, 10, 11, 19, 33 |
| Rams et al., *YASTN: Yet another symmetric tensor networks* | `docs/papers/rams_yastn_scipost_codebases_52.pdf` | `44a7a77c86ec8f1f1298c12a6984717a6e5ed17ce66da2f9fa071270813a6c73` | 2, 4, 8, 9, 14 |

Search inclusion was mechanism-driven: an MPS canonical/truncation reference, open-system trajectory
references, a finite-PEPS environment reference, a closed-loop gauge/FET reference, an exact-cluster NTU
reference, and the publications describing variPEPS and YASTN. Discovery hits that merely benchmarked a
single observable or repeated one of these algorithms were not used as independent support.

## Source-only evidence ledger

### MPS state representation and truncation

| Fact | Exact source locator | What the source establishes | What it does not establish |
|---|---|---|---|
| OBC MPS canonical cut | Paeckel, Secs. 2.4–2.6, PDF pp. 7–9, Eqs. (13)–(18) | A mixed-canonical MPS exposes a cut matrix whose SVD gives the local best rank reduction; the squared Hilbert-space error is the sum of discarded singular-value squares. | A bound on a later adaptive or multi-time measurement record. |
| Sequential cut limitation | Paeckel, Sec. 2.6, PDF p. 9 after Eq. (18) | Each direct cut is locally optimal, while a sweep of successive cuts need not be globally optimal; variational compression can improve the whole-MPS approximation. | That summed discarded weights equal a global operational error. |
| Error taxonomy | Paeckel, Sec. 4.1.1, PDF pp. 18–19; Sec. 6.2.2, PDF pp. 49–50 | Time-step, projection, SVD truncation, and local-solver errors are distinct, and their accumulation depends on how often the operation is applied. | A universal threshold transferable between solvers or observables. |

### Open-system MPS objects and probability semantics

| Fact | Exact source locator | What the source establishes | What it does not establish |
|---|---|---|---|
| Three different open-system objects | Jaschke, Sec. II, PDF pp. 3–4, Eqs. (1)–(6) | Quantum trajectories carry stochastic pure states; MPDOs carry a vectorized density operator; locally purified networks carry a purification. | That their bond dimensions or truncation errors are interchangeable. |
| Quantum-jump branch mass | Jaschke, Sec. III.B, PDF pp. 10–12, Eqs. (24)–(27) | Non-Hermitian norm loss selects a jump and `p_nu = <psi|L_nu^dag L_nu|psi>` determines the jump channel before renormalization. | That normalized-state fidelity controls the lost branch norm. |
| Ensemble observable semantics | Jaschke, Sec. III.B, PDF p. 12, Eqs. (26)–(27) | Linear observables are recovered by averaging trajectories; nonlinear density-matrix quantities are not generally averages of their pure-trajectory counterparts. | A certificate for the full joint trajectory record. |
| TJM convergence domain | Sander, Secs. III–IV, PDF pp. 3–10, Eqs. (6)–(11), (42)–(45), Theorem 2 | The tensor-jump method combines MCWF sampling with MPS propagation; its displayed density convergence theorem assumes an MPS of full bond dimension and concerns a fixed-time density estimate. | A finite-bond theorem or sequential-record total-variation bound. |
| TJM finite-bond error | Sander, Sec. IV.C, PDF pp. 10–11, Eqs. (57)–(58) | Finite bond dimension introduces a projection error in addition to splitting and time-step errors. | A dimension-independent conversion of this projection error into record error. |

### PEPS environment, loops, and truncation

| Fact | Exact source locator | What the source establishes | What it does not establish |
|---|---|---|---|
| Finite PEPS object | Lubasch, Sec. II, PDF p. 2, Fig. 1 and Eq. (1) | The studied object is a finite `L x L` open-boundary pure PEPS; its update minimizes a Hilbert-space norm through local ALS equations. | A stochastic measurement trajectory or record law. |
| Independent environment approximation | Lubasch, Sec. III.A, PDF p. 3, Fig. 2 | Boundary-MPO contraction introduces an environment bond dimension independent of the PEPS state bond dimension. | That increasing only the state bond dimension controls contraction error. |
| Positivity and gauge limits | Lubasch, Sec. III.A.2 and III.B.2, PDF pp. 4–7 | The exact norm environment is Hermitian positive semidefinite; approximate contraction can lose positivity; an OBC MPS norm matrix can be gauged to identity whereas a PEPS norm matrix generally cannot. | That PSD repair recovers the exact environment or MPS canonical semantics. |
| Closed-loop no-go | Evenbly, Secs. II–IV, PDF pp. 2–5, Eqs. (1)–(11) | A non-bridge bond is described by a whole-network bond environment; two cyclic networks can represent the same physical state with different weighted-trace-gauge spectra. | That a PEPS bond spectrum is a physical Schmidt spectrum. |
| FET objective | Evenbly, Sec. V, PDF pp. 5–6, Eq. (12); Appendix C, PDF p. 11, Eq. (C1) | Full-environment truncation alternates isometries to maximize normalized overlap of the untruncated and truncated whole-network pure states, using the bond environment. | A guarantee of global convergence, branch-norm preservation, approximate-environment accuracy, or sequential-record accuracy. |
| Exact-cluster NTU | Dziarmaga, PDF pp. 3–5, Figs. 3–5 and Eqs. (2)–(5) | NTU minimizes a quadratic error in a nearest-neighbor cluster whose metric can be contracted exactly and is Hermitian positive semidefinite to machine precision. | Exact contraction of the infinite state, or an operational record certificate. |
| Environment hierarchy | Dziarmaga, Conclusion, PDF p. 9 | SVDU, SU, NTU, and FTU/FU use increasingly large environments and trade numerical cost against convergence with state bond dimension. | Monotonic improvement for every state or output law. |

### External-library scientific objects

| Fact | Exact source locator | What the source establishes | What it does not establish |
|---|---|---|---|
| variPEPS target | Naumann, Sec. 2, PDF p. 5, Eqs. (1)–(3) | A periodically repeated unit-cell iPEPS is optimized in the thermodynamic limit by minimizing ground-state energy with automatic differentiation. | Finite open-boundary trajectory evolution or selective measurements. |
| variPEPS environment | Naumann, Sec. 2.2.2, PDF p. 10, Eqs. (4)–(9) | CTMRG projectors truncate an approximate infinite-lattice environment to an environment bond dimension. | A truncation of the PEPS state bond carrying Schmidt semantics. |
| CTMRG heuristic boundary | Naumann, Sec. 2.8.2, PDF p. 19 | A discarded environment-spectrum norm is used as a heuristic; too small an environment bond can let optimization exploit contraction error and produce falsely low energies. | A universal safety threshold or record-law bound. |
| YASTN architecture | Rams, Sec. 2 and Fig. 2, PDF p. 4 | YASTN separates backend, Abelian-symmetric tensor, and high-level MPS/fPEPS algorithms. | That all high-level algorithms solve the same physical problem. |
| YASTN MPS and PEPS scope | Rams, Sec. 2.3, PDF p. 8 | The MPS layer covers finite MPS algorithms such as DMRG and TDVP; fPEPS covers finite and infinite square-lattice PEPS with NTU, cluster, and full-update methods. | Detector/syndrome generation or a multi-round instrument oracle. |
| YASTN CTM approximation | Rams, Fig. 3 and accompanying text, PDF p. 9 | CTM approximates an infinite iPEPS environment using an independently chosen environment bond dimension. | Exact finite-trajectory Born probabilities. |

## Cross-source conclusions

The following conclusions are closed by the sources above:

1. An MPS quantum trajectory, a vectorized density operator, a finite PEPS pure-state trajectory, and a
   periodic ground-state iPEPS are different mathematical objects even when all are implemented with tensor
   primitives.
2. An internal OBC MPS cut is a bridge and supports canonical Schmidt/SVD semantics. A typical PEPS bond
   lies in a closed loop and does not.
3. In a stochastic trajectory, an unnormalized state norm is probability mass. Compressing and then
   renormalizing can hide a probability error even when conditional-state fidelity looks good.
4. PEPS state-bond truncation and PEPS environment-contraction truncation are independent approximation
   layers and require independent convergence controls.
5. WTG, FET, NTU, CTMRG diagnostics, TDVP projection diagnostics, and SVD discarded weights are valid
   diagnostics for their declared mathematical targets, not automatically for a downstream multi-time
   output law.

## Literature gaps and disconfirmation surface

No included source proves any of the following:

- a local Schmidt discarded weight to adaptive multi-time record total-variation bound;
- a finite-bond MCWF projection-error to full trajectory-record bound;
- an approximate PEPS environment objective to true whole-state fidelity bound;
- normalized FET fidelity to unnormalized branch-probability preservation;
- a per-step PEPS update error to detector/observable joint-record error under repeated selective
  measurement and renormalization;
- a universal safe numerical threshold transferable from ground-state energy or local observables.

The strongest apparent counterexamples were checked rather than ignored:

- Sander Theorem 2 is explicitly full-bond and fixed-time; it does not close the finite-bond record bridge.
- Evenbly Eq. (12) is a whole-state normalized fidelity when the exact bond environment is available, but
  its scale invariance means it cannot by itself detect branch-mass distortion.
- Dziarmaga calls the NTU metric exact because the selected finite cluster contracts exactly, not because
  the complete infinite state or an operational record is exact.
- Naumann's environment-spectrum threshold is presented as a ground-state CTMRG heuristic and is paired
  with a warning about false low-energy optima.

## Closure verdict

`LITERATURE_ROLE_CLOSED`: the represented objects, optimization targets, MPS/PEPS structural difference,
and external-library relevance are source-closed.

`RECORD_BRIDGE_OPEN`: the local numerical metrics are not source-closed as certificates of the declared
sequential record law.

`CODE_BLOCKED`: this packet does not authorize enabling or tightening production pruning. A subsequent
preregistration must retain an independent exact full-record oracle and treat all local metrics as candidate
diagnostics until the record bridge is proved or empirically bounded inside a declared finite regime.

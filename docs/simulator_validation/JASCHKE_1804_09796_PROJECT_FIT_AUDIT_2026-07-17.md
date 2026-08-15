# Project-fit audit — Jaschke, Montangero, and Carr 1804.09796v2

Date: 2026-07-17
Source artifact: `docs/papers/1804.09796v2.pdf`
Source SHA-256: `62e6b0ceb9fbce3da5f938968a728873b50953d87e1506f43e1358828714919f`
Question: which quantum-trajectory and MPS statements support restricted QT/MCWF verification,
and which finite-bond branch-mass and detector-Record bridges remain absent?

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Lindblad and representation scope | Secs. I–II, Eqs. (1)–(3), PDF pp. 2–4 | The paper compares QT, MPDO, and LPTN routes for one-dimensional Lindblad dynamics and states their different state objects and scaling tradeoffs. | It does not claim one representation dominates all problems. | closed |
| QT no-jump and jump mechanism | Sec. III.B, Eqs. (24)–(25), algorithm on PDF pp. 10–12 | A pure state evolves without renormalization under a non-Hermitian effective Hamiltonian until its norm crosses a uniform threshold; a jump channel is selected from normalized `L_nu^dagger L_nu` expectations and the post-jump state is normalized. | It does not provide a finite-step all-candidate mass-residual test. | closed |
| Solver contamination of norm | Sec. III.B, paragraph after Eq. (25), PDF p. 11 | The local Runge–Kutta method does not itself conserve norm and can enhance or prevent the norm loss attributed to the effective Hamiltonian. | It does not give a correction theorem that recovers the physical waiting-time law from contaminated norm loss. | closed |
| Jump support | Sec. III.B, Fig. 3 and algorithm, PDF p. 12 | The implementation describes both local Lindblad operators and many-body string Lindblad terms when evaluating jump weights. | It does not provide a dense-to-MPO cutoff or finite-bond error analysis for those strings. | closed |
| Trajectory observables | Sec. III.B, Eqs. (26)–(27), PDF p. 12 | Linear observables are equal-weight trajectory averages, while nonlinear purity requires pairwise trajectory contractions and access to all trajectory states. | It does not establish detector-bit or logical-observable Record statistics. | closed |
| Finite-bond probability faithfulness | Secs. III.B and IV.B–IV.C, PDF pp. 10–19 | Benchmarks separate sampling, Trotter, and tensor-network truncation effects for selected observables and examples. | It gives no theorem that a finite-bond trajectory preserves raw no-jump/jump mass or the full trajectory law. | missing |
| Multi-round detector Record faithfulness | Full-text scope: abstract; Secs. I–V and appendices, PDF pp. 1–24 | The compared outputs are states and physical observables such as excitation number and center of mass. | It defines no schedule-sealed measurement layout, detector XOR fold, logical bit, Record total variation, or logical-error-rate bridge. | missing |

## Notation ledger

| source symbol | source meaning | domain or scope | fixed/variable |
|---|---|---|---|
| `rho` | density operator governed by the Lindblad equation | one-dimensional open many-body system | time-dependent |
| `H_eff` | `H - i/2 sum_nu L_nu^dagger L_nu` with `hbar=1` | QT no-jump evolution | model-defined |
| `r_N` | uniform random threshold in `(0,1)` | waiting-time jump trigger | resampled after a jump |
| `p_nu` | unweighted `L_nu^dagger L_nu` expectation | jump-channel selection | state-dependent |
| `N_QT` | number of simulated trajectories | ensemble estimator | user-controlled |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Lindblad equation | choose QT, MPDO, or LPTN representation | Markovian/Born–Markov/secular setting stated by the source | representation-specific tensor-network evolution problem | Secs. I–II, Eqs. (1)–(3), PDF pp. 2–4 | reproduced |
| normalized pure state and `r_N` | propagate under `H_eff` without renormalizing and measure the norm | numerical propagator represents the non-Hermitian evolution faithfully | no-jump continuation or a triggered jump | Sec. III.B, Eq. (25) and algorithm steps (i)–(iii), PDF pp. 11–12 | reproduced with declared solver caveat |
| triggered jump | compute `p_nu`, normalize over channels, draw `r_kappa`, apply `L_kappa`, renormalize | channel weights are finite and their sum is usable | next normalized trajectory state | Sec. III.B, steps (a)–(c), PDF p. 12 | reproduced |
| trajectory states | average per-trajectory values of a linear observable | equal trajectory weights | estimator of a linear density-matrix observable | Sec. III.B, Eq. (26), PDF p. 12 | reproduced |
| trajectory states | form all pairwise overlaps | all states remain available at measurement time | density-matrix purity estimator | Sec. III.B, Eq. (27), PDF p. 12 | reproduced |
| finite-bond jump trajectory | derive complete detector Record distribution | no measurement/Record construction is present | no source-supported output | full-text boundary, PDF pp. 1–24 | blocked |

## Project application

The source directly supports preserving unnormalized no-jump evolution until the physical jump decision
has been made and supports selecting the jump family from explicit nonnegative channel weights. It also
supports a hard separation between linear trajectory observables and nonlinear ensemble quantities.

Its most important project-facing warning is negative: numerical norm loss is not automatically physical
norm loss. A restricted MPS route therefore has to keep these objects distinct:

- raw physical candidate mass from uncapped no-jump/jump operations;
- numerical loss introduced by MPS projection, splitting, or an inexact local solver;
- normalization applied only after the physical branch has been selected;
- empirical trajectory-count normalization, which is not a substitute for raw-mass validation.

The paper's many-body string example supports the need to test nonlocal jump support, but it does not
specify the source-preserving dense-to-MPO decomposition or finite-bond acceptance policy required by the
current project. Its observable benchmarks do not close the detector Record bridge.

## Competing evidence and kill conditions

- Sander et al. 2501.17913v2 uses a different finite-step TJM construction: its jump probability is
  computed after the dissipative contraction and its main implementation is explicitly single-site.
  The two algorithms must not be silently conflated.
- Paeckel et al. 1901.05824v3 supplies the local SVD/TDVP truncation taxonomy but does not supply QT
  probability semantics.
- Kill a proposed implementation claim if the propagator is renormalized before the jump trigger, if
  numerical truncation loss is counted as physical jump probability, or if candidate weights are
  silently normalized without exposing their raw sum.
- Kill any Record-faithfulness claim based only on convergence of excitation number, center of mass,
  bond dimension, or a fixed trajectory count.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- QT branch mechanism row: closed
- solver-norm contamination row: closed
- nonlocal jump-weight row: closed at mechanism level
- finite-bond branch-law row: missing
- detector Record-faithfulness row: missing
- project disposition: `supports_QT_probability_semantics_with_solver_caveat`
- current gate effect: `RECORD_BRIDGE_OPEN`; `PRODUCTION_PRUNING_CODE_BLOCKED`

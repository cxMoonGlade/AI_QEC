# Project-fit audit — Paeckel et al. 1901.05824v3

Date: 2026-07-17
Source artifact: `docs/papers/1901.05824v3.pdf`
Source SHA-256: `1ce466ed9ec3091ee1a8548cf42a84551584cd5d6f13b0d32a418fcdc981fbb9`
Question: which claims in this MPS time-evolution review can support the restricted MPS
verification routes, and which branch-mass or Record-faithfulness bridges remain absent?

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Canonical cut and local rank reduction | Secs. 2.4–2.6.1, Eqs. (11)–(17), PDF pp. 7–9 | Mixed canonical form makes the cut bases orthonormal; a cut SVD keeps the largest singular values and defines discarded weight from the omitted singular values. | It does not identify this local quantity with trajectory probability loss or a global time-evolution error. | closed |
| Sequential truncation scope | Sec. 2.6.1, paragraph after Eq. (17), PDF p. 9 | Sequential cutwise SVDs are locally optimal and may fail to form the globally optimal compressed MPS when truncations are large. | It does not provide a composition theorem turning a sweep of local discarded weights into a global observable bound. | closed |
| TEBD error decomposition | Sec. 4.1.1, PDF pp. 18–19 | Trotter time-step error and mandatory state-truncation error are distinct; truncation affects unitarity and conserved quantities and is tested by bond-dimension convergence. | It does not cover non-Hermitian no-jump evolution or quantum-jump branch sampling. | closed |
| TDVP finite-manifold error decomposition | Sec. 6.2.2, PDF pp. 49–50 | Projection, splitting/time-step, two-site SVD truncation, and local-solver errors are distinct and respond differently to step-size refinement. | It does not prove that norm preservation or energy conservation implies state or observable accuracy. | closed |
| Physical branch-mass preservation | Full-text scope: abstract; Secs. 1, 3–6, 9; PDF pp. 1–78 | The review treats Schrödinger real/imaginary-time evolution of finite-system MPS. | It contains no quantum-trajectory probability ledger and no rule for separating numerical norm loss from physical branch probability. | missing |
| Multi-round detector Record faithfulness | Full-text scope: abstract; Secs. 1–9; PDF pp. 1–78 | The observables and examples are state expectation values, correlations, spectra, energy, symmetry, and related diagnostics. | It defines no detector-event layout, temporal XOR fold, logical-observable bit, Record distribution, total-variation bound, or logical-error-rate bound. | missing |

## Notation ledger

| source symbol | source meaning | domain or scope | fixed/variable |
|---|---|---|---|
| `m`, `m'` | original and reduced MPS bond dimensions | positive integer cut dimensions | variable |
| `S_{k,k}` | nonnegative singular values at one canonical cut | diagonal entries of the bond SVD | variable by state and cut |
| discarded weight | sum of squared singular values omitted beyond `m'` | one SVD at one cut | local diagnostic |
| `delta` | time step in the reviewed evolution methods | real- or imaginary-time integrator parameter | user-controlled |
| `P_T|psi` | tangent-space projector for TDVP | MPS manifold fixed by current state/bond structure | state-dependent |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| MPS and a selected bond | put the state in mixed canonical form | left and right effective bases are orthonormal | bond coefficient matrix whose singular values are Schmidt coefficients | Secs. 2.4–2.6.1, Eqs. (11)–(15), PDF pp. 7–9 | reproduced |
| bond coefficient matrix | SVD and retain the largest `m'` singular values | all other site tensors are fixed for this local problem | reduced-rank bond and local Hilbert-space approximation | Sec. 2.6.1, Eqs. (15)–(16), PDF p. 9 | reproduced |
| omitted singular values | square, sum, and take square root | canonical-cut SVD setting | local approximation error and discarded weight | Sec. 2.6.1, Eq. (17), PDF p. 9 | reproduced |
| Hamiltonian split into commuting groups | ordered or symmetric Trotter product followed by MPS compression | exponential of each group is computable | TEBD state update with separate time-step and truncation errors | Sec. 4.1, Eqs. (41)–(62); Sec. 4.1.1, PDF pp. 17–19 | reproduced |
| finite-bond MPS and Hamiltonian | project the TDSE into the MPS tangent space and integrate local forward/backward equations | declared one-site or two-site TDVP manifold | approximate evolved MPS with projection, integrator, truncation, and local-solver errors | Secs. 6.2.1–6.2.2, Eqs. (158)–(166), PDF pp. 47–50 | reproduced |
| local discarded weight | reinterpret as trajectory branch-mass residual or Record-law error | no such bridge appears in the source | no source-supported output | full-text boundary, PDF pp. 1–78 | blocked |

## Project application

The source supports the restricted project in three narrow ways.

1. A finite-bond two-site split may expose its actual kept bond and the squared omitted singular
   values as a **local numerical diagnostic** when the split is performed at an authenticated
   canonical cut.
2. Sequential split events must remain separately ledgered because local SVD optimality does not
   imply a globally optimal compressed trajectory.
3. Time-step, projection, SVD-truncation, and local-solver errors must not be merged into one score;
   convergence requires controls that can vary these sources independently.

The source does not authorize any of the following promotions:

- treating local discarded fraction as physical no-jump or jump probability;
- restoring a conditional-state norm and then claiming the pre-restoration loss was physical;
- summing local discarded weights and calling the result a global state-error theorem;
- using norm, energy, bond dimension, or local state fidelity alone to certify the complete
  multi-round detector Record law or logical-error rate.

Accordingly, this paper supports mechanics-level diagnostics and corruption falsifiers. It does not
close `RECORD_BRIDGE_OPEN` and cannot unblock production pruning.

## Competing evidence and kill conditions

- Sander et al. 2501.17913v2 supplies an MCWF/MPS construction and therefore owns physical jump
  probability statements that this closed-system review does not.
- Jaschke et al. 1804.09796v2 explicitly warns that a numerical integrator's own norm error can
  enhance or suppress the norm loss used for quantum-jump timing.
- Kill the proposed use if a project statement calls Eq. (17) a trajectory probability, a global
  sweep error, a Record-distribution error, or a logical-error-rate bound.
- Kill a finite-bond acceptance argument that cites exact 1TDVP norm/energy conservation without an
  independent state or observable comparison; the source itself warns that convergence in bond
  dimension remains necessary.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- canonical-cut/SVD row: closed
- evolution-error taxonomy row: closed
- physical branch-mass row: missing
- detector Record-faithfulness row: missing
- project disposition: `supports_local_MPS_mechanics_only`
- current gate effect: `RECORD_BRIDGE_OPEN`; `PRODUCTION_PRUNING_CODE_BLOCKED`

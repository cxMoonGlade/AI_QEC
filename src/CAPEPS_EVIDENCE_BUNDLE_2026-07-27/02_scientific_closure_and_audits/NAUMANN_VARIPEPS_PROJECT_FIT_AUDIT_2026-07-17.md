# Claim audit — variPEPS lecture notes and the current carrier question

## Status and decision

Retain Naumann et al., *An introduction to infinite projected entangled-pair state methods for
variational ground state simulations using automatic differentiation*, as an adjacent methods source
for CTMRG projectors, fixed-point differentiation, and environment-truncation diagnostics. It is not
a trajectory-carrier or finite-Record source and is not load-bearing for restricted MPS repair.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Variational target | Sec. 2, Eqs. (1)--(2), PDF p. 5 | The method minimizes iPEPS ground-state energy density using automatic differentiation through an approximate CTMRG contraction. | Finite `chi_E` does not by itself make the reported energy a strict variational upper bound. | closed |
| CTMRG projectors | Sec. 2.2.2, Eqs. (4)--(9), Figs. 7--10, PDF pp. 9--11 | SVD of an approximate lattice-environment matrix supplies projectors that reduce the enlarged environment bond back to `chi_E`. | The retained environment subspace is not a physical-state truncation theorem. | closed |
| Fixed-point condition | Secs. 2.2.3 and 2.5, Eqs. (10), (16)--(17), PDF pp. 12, 16 | Differentiation requires an actual element-wise CTMRG fixed point; convergence of only a singular spectrum can miss phase/sign fluctuations. | A fixed point does not imply exact contraction at finite `chi_E`. | closed |
| Truncation heuristic | Sec. 2.8.2, PDF p. 19 | The norm of discarded normalized environment singular values is a heuristic for increasing `chi_E`; an undersized environment can be exploited by optimization to produce artificially low energies. | The threshold is not a universal state- or Record-error bound. | closed |
| Project carrier question | Full-text scope and Sec. 5, PDF pp. 33--34 | The source reviews variational iPEPS ground-state optimization and benchmark lattices. | It does not define stochastic trajectories, selective measurements, detector Records, branch-mass ledgers, or finite-truncation Record bounds. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Periodic iPEPS tensor unit cell | Iterate directional CTMRG absorption and project enlarged bonds using an SVD-derived basis | A chosen finite `chi_E` adequately resolves the requested observables | Approximate fixed-point environment tensors | Sec. 2.2, Eqs. (4)--(9), PDF pp. 6--11 | complete |
| iPEPS, fixed-point environment, and local Hamiltonian | Evaluate energy and backpropagate through the fixed-point equation | Environment tensors converge element-wise and derivative sums/solves converge | Energy gradient for variational optimization | Secs. 2.3--2.5, Eqs. (16)--(17), PDF pp. 12--16 | complete |
| Normalized environment singular spectrum | Take the norm of discarded values and compare to a heuristic threshold | The heuristic is used only to decide whether to enlarge `chi_E` | Environment-resolution diagnostic | Sec. 2.8.2, PDF p. 19 | complete |

## Project application

- The source is useful for separating a PEPS state bond from an environment-contraction bond and for
  requiring true fixed-point checks when differentiating an iterative environment.
- Its discarded-environment-spectrum norm is explicitly a heuristic. It cannot be reused as a global
  state, trajectory, Record-TV, or LER guarantee.
- Because the method targets deterministic thermodynamic-limit ground states, it does not close any
  branch-mass or multi-round detector-record premise in the current simulator.

## Competing evidence and kill conditions

- Evenbly supplies the direct closed-loop FET objective; Dziarmaga supplies a finite-neighborhood
  time-evolution metric. Naumann's CTMRG projector diagnostic should not replace either.
- Kill any use that treats finite-`chi_E` convergence, an energy minimum, or a discarded-spectrum
  threshold as proof of trajectory or Record faithfulness.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned rows: four closed, one missing
- project fit: adjacent PEPS environment/AD reference; not load-bearing for current Record certification

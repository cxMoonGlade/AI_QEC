# Claim audit — Liao et al. Heisenberg PEPO and the Record-law boundary

## Status and decision

Retain Liao et al., *Simulation of IBM's kicked Ising experiment with Projected Entangled Pair
Operator*, as a direct source for Heisenberg-picture PEPO evolution and contraction of a fixed
observable on the 127-qubit heavy-hex kicked-Ising circuit. It also supplies useful empirical
bond-dimension convergence evidence and a separate, circuit-specific exact benchmark based on
Clifford expansion.

The source computes deterministic terminal expectation values for fixed unitary circuits. It does not
evolve a density operator, sample intermediate measurements, implement conditional reset or
feed-forward, or produce a joint multi-round outcome law. It therefore supports PEPO operator
mechanics but does not certify the project's density-matrix PEPO carrier or its adaptive `RecordBatch`
contract.

This audit changes no implementation and authorizes no carrier-status or faithfulness upgrade.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Circuit and target | Sec. II, Eqs. (1)--(3), PDF p. 2 | A fixed depth-`T` kicked-Ising unitary alternates Clifford `R_ZZ` layers with `R_X(theta_h)` layers, and the reported target is a terminal observable expectation. | It does not define stochastic measurement times, adaptive branches, reset, or a record schema. | closed |
| Heisenberg PEPO mechanics | Sec. III, Eqs. (4)--(5), PDF pp. 2--3 | The observable, rather than the state, is represented as a PEPO and contracted from the middle toward both temporal boundaries; simple update performs SVD compression and the remaining final network is contracted exactly. | The PEPO is not a density matrix or a general completely positive channel representation. | closed |
| Geometry and cost | Sec. III, PDF p. 3 | Heavy-hex locality avoids the long-range gates and SWAPs of a one-dimensional MPO; the stated step cost is `O(L chi^4)` and final exact contraction costs `O(chi^6)`. | These are method costs, not a trace-distance, state-fidelity, or Record-law error theorem. | closed |
| Exact shallow benchmark | Sec. IV A and Fig. 2, PDF pp. 3--4; Appendix, Eqs. (6)--(10), PDF pp. 6--7 | A separate Clifford expansion reduces the 5+1-step observables to exactly contractible networks and is used only as reference; PEPO `chi=184` agrees within double-precision rounding for the modified weight-17 observable. | The Clifford expansion is not invoked inside the PEPO calculation and is not a general oracle for arbitrary circuits. | closed |
| Deep-circuit convergence | Sec. IV B and Fig. 3, PDF pp. 4--5 | For the 20-step `Z_62` expectation, the displayed values vary monotonically with `chi` in the intermediate regime and are extrapolated with `b exp(-a/chi)`. | No proof establishes monotonicity for other observables, a rigorous extrapolation error bar, or convergence of an entire state or outcome law. | empirical |
| Strong-entanglement regime | Sec. IV B, PDF p. 4 | In the non-verifiable intermediate-angle regime, increasing `chi` moves PEPO farther from several competing results, and the paper says which method is more accurate cannot be determined. | Agreement, monotonicity, or a larger bond dimension does not establish ground truth there. | open |
| Adaptive Record law | Full-text operational scope and Sec. V, PDF pp. 1--5 | The numerical outputs are scalar terminal expectations for fixed observables after fixed unitary circuits. | No joint probability distribution for intermediate measurement outcomes, detector folds, observable bits, conditional gates, or resets is constructed or validated. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Product-state boundary, fixed heavy-hex circuit `U_T(theta_h)`, and fixed observable `O` | Rewrite the scalar as the Heisenberg expectation of `U_T^dagger O U_T` | Circuit contains only the specified `R_ZZ` and `R_X` layers | Three-dimensional contraction network with `O` at its temporal middle | Sec. II and Eqs. (1)--(5), PDF pp. 2--3 | closed |
| Original observable tensor | Apply a gate and its conjugate from the middle toward both boundaries | Heavy-hex PEPO layout follows the circuit's two-dimensional geometry | Updated observable PEPO after each layer | Sec. III, PDF p. 3 | closed |
| Updated observable PEPO | Compress virtual bonds by simple-update SVD truncations to cap `chi` | The selected `chi` is finite; discarded components are the approximation source identified by the paper | Approximate Heisenberg operator PEPO | Sec. III, PDF p. 3 | closed |
| Final PEPO and state boundaries | Contract the remaining tensor network without further approximate contraction | The final network has the structure and bond dimension assumed by the implementation | One deterministic scalar expectation value | Sec. III, PDF p. 3 | closed |
| 5+1-step target observables | Separately commute Clifford layers and expand non-Clifford rotations into Pauli strings | The source-specific circuit identities in the Appendix hold | Exact benchmark values for `W_10`, `W_17`, and modified `W_17` | Appendix, Eqs. (6)--(10), PDF pp. 6--7 | closed |
| 20-step `Z_62` results over finite `chi` | Fit the observed sequence to `b exp(-a/chi)` | Empirical fit form; no theorem or certified remainder | Extrapolated terminal expectation | Fig. 3 and caption, PDF p. 5 | empirical |
| Intermediate measurements and conditional operations | No operation is specified | Outside the paper's fixed-unitary terminal-observable problem | Joint adaptive Record law | Full-text scope | missing |

## Project application

The source is directly useful for a narrow mechanics question: a fixed local unitary circuit and a
fixed terminal observable can be reorganized as Heisenberg operator evolution on a geometry-matched
PEPO, with simple-update compression followed by scalar contraction. The Clifford-point `chi=1`
example and the shallow exact benchmark are good corruption falsifiers for an implementation of that
specific operator route.

The project carrier is materially different. `docs/SIMULATOR.md` defines the retained PEPO route as a
two-dimensional qutrit density-matrix carrier and judges carrier validity on the declared Record law.
Liao et al. do not propagate a density operator, a noise channel, or conditional measurement branches.
Their output is an expectation value, not an emitted binary detector/observable record distribution.
An adapter would need independent definitions and references for nonunitary channels, measurement
conditioning, reset, normalization of branch probabilities, and the complete multi-round Record
oracle.

The paper's empirical `chi` convergence cannot close that bridge. Even exact evaluation of one
terminal scalar at a Clifford point says nothing by itself about total variation over a multi-time
record support. In the strongest-entanglement regime the authors explicitly lack an exact answer, so
the extrapolated curve must remain a numerical estimate rather than an independent reference.

## Competing evidence and kill conditions

- `docs/SIMULATOR.md` states that PEPO is not the canonical record backend and lacks established
  finite-truncation full-record or d5/d7 faithfulness.
- Kill use as density-matrix propagation evidence if the evolved object is described as a state: the
  source evolves the observable in the Heisenberg picture and contracts a terminal scalar.
- Kill use as an adaptive-trajectory reference if the implementation contains mid-circuit
  measurements, reset, conditional gates, noise Kraus branches, or emitted detector records.
- Kill use of the 5+1 exact benchmark as a general oracle if the tested circuit or observable is not
  covered by the source's explicit Clifford-expansion identities.
- Kill a convergence certificate based only on monotonic finite-`chi` values or the fit
  `b exp(-a/chi)`; the paper supplies no general error theorem and identifies an unverifiable regime.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- Heisenberg-PEPO operation row: closed
- terminal-scalar contraction row: closed
- 5+1-step exact-reference row: closed for the specified observables
- 20-step extrapolation row: empirical
- density-matrix evolution row: missing
- adaptive multi-round Record-law row: missing

# Claim audit — Dziarmaga NTU and the PEPS environment boundary

## Status and decision

Retain Dziarmaga, *Time evolution of an infinite projected entangled pair state: a neighborhood
tensor update*, for the SVDU/SU/NTU/FTU environment hierarchy, the exactly contracted
nearest-neighbor metric, and its alternating reduced-matrix solve. The source is relevant to PEPS
time-evolution engineering and to distinguishing exact local metrics from approximate infinite
environments. It does not certify a finite-trajectory QEC Record or the current FET objective.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Update hierarchy | Secs. I--II and Sec. VI, PDF pp. 1--3, 9 | SVDU, SU, NTU, and FTU/FU use increasingly large environments for the post-gate truncation objective. | The hierarchy does not imply monotonic accuracy for every state or observable. | closed |
| Reduced tensors | Sec. II, Fig. 2, PDF p. 3 | QR decompositions isolate gate-affected reduced matrices while fixed isometries carry the remaining tensor structure. | This is not the same factorization or objective as FET. | closed |
| NTU metric | Sec. II, Figs. 3--5 and Eqs. (2)--(5), PDF pp. 3--5 | A nearest-neighbor double-layer cluster is contracted exactly to a Hermitian nonnegative metric, and two reduced matrices are optimized alternately in its quadratic error. | Exactness is limited to the declared finite cluster, not the infinite state environment. | closed |
| Infinite environment contrast | Sec. II, PDF pp. 3--4 | FTU uses a CTMRG infinite environment whose approximate construction can lose Hermiticity and nonnegativity. | The source does not prove every FTU realization unstable. | closed |
| Numerical regime | Secs. III--V, Figs. 6--12 and Tables I--II, PDF pp. 5--9 | The paper benchmarks quenches and thermal Ising states, with NTU often more stable than smaller-environment updates and converging more slowly in bond dimension than FTU/FU. | The reported magnetization/correlation/energy checks are not a detector-record comparison. | closed |
| Record bridge | Full-text scope and Sec. VI, PDF p. 9 | The observables are state magnetization, correlations, energy drift, and thermal critical estimates. | No stochastic selective-measurement law, branch probability, detector XOR record, Record TV, or LER bound is supplied. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Two neighboring iPEPS tensors and a Trotter gate | Apply the gate, QR-reduce the tensors, and SVD the product | Gate rank and target bond dimension are finite | Initial reduced matrices at the requested bond dimension | Sec. II, Fig. 2, PDF p. 3 | complete |
| Nearest-neighbor tensor cluster and reduced isometries | Contract the double-layer cluster exactly | The finite neighborhood is the intended metric support | Hermitian nonnegative metric `g` | Sec. II, Fig. 4, PDF p. 4 | complete |
| `g`, exact reduced product, and current two-factor approximation | Form the quadratic error and alternate pseudoinverse solves for the two factors | Pseudoinverse tolerance is adjusted to reduce the declared error | Updated reduced matrices and local quadratic error | Sec. II, Eqs. (2)--(5), Fig. 5, PDF pp. 4--5 | complete |

The replay closes a deterministic local update. It has no operation that produces or validates a
multi-time stochastic Record.

## Project application

- NTU is useful competing evidence for the environment choice: an exactly contracted finite
  neighborhood can provide a well-formed local quadratic metric without claiming an exact infinite
  environment.
- It does not replace Evenbly's FET source because the objectives differ: NTU minimizes a cluster
  quadratic difference after a Trotter gate, whereas FET maximizes normalized whole-network overlap
  for a selected bond.
- The source supports keeping local solver health, environment exactness, and downstream physical
  observables as separate gates.
- The QEC PEPS frontier still requires measurement/branch semantics and an independent Record-law
  oracle; none is present here.

## Competing evidence and kill conditions

- Evenbly is the direct source for normalized FET and closed-loop internal-correlation removal.
- Lubasch is the finite-PEPS source for approximate-environment positivity repair and gauge
  conditioning.
- Kill a claim that calls the NTU finite-cluster metric a full environment or that treats local
  nonnegative quadratic error as a Record bound.
- Kill a claim that transfers the Ising benchmark scales to QEC schedules without a separate model
  and observable bridge.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned rows: five closed, one missing
- project fit: supporting PEPS update/environment source, not the direct FET or Record-faithfulness source

# Claim audit — Evenbly closed-loop truncation and the PEPS carrier frontier

## Status and decision

Retain Evenbly, *Gauge fixing, canonical forms and optimal truncations in tensor networks with
closed loops*, for its definitions of a bond environment, weighted trace gauge (WTG), cycle entropy,
and the normalized full-environment truncation (FET) objective. It is directly relevant to the local
PEPS pruning mechanism and its non-degeneracy gate. It does not establish a stochastic trajectory
law, a detector/observable Record, or a bound from FET infidelity to complete Record distance.

This audit changes no implementation and authorizes no carrier-status or faithfulness upgrade.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Bond environment | Sec. II, Eq. (1), Fig. 1, PDF p. 2 | Contracting the norm network while leaving one bond and its conjugate open defines the bond environment; together with the bond matrix it recovers the state norm. | It does not make an approximate environment exact. | closed |
| Closed-loop gauge | Sec. III, Eqs. (2)--(8), Figs. 2--3, PDF pp. 3--4 | WTG makes the two boundary matrices proportional to identity and the bond matrix positive diagonal, subject to stated existence and uniqueness conditions. | WTG coefficients on a cyclic network need not be physical-state invariants. | closed |
| Internal correlations | Sec. IV, Eqs. (9)--(11), Fig. 4, PDF p. 5 | Two cyclic representations of the same state can carry different internal correlations; cycle entropy measures the normalized transfer-spectrum content and vanishes for a bridge realization. | A small nonzero cycle entropy is not supplied with a universal physical-error bound. | closed |
| FET target | Sec. V, Eq. (12), Fig. 5, PDF p. 6 | FET replaces one bond by a lower-rank factorization and maximizes normalized whole-network pure-state fidelity. | The objective is not a detector-record likelihood or trajectory probability. | closed |
| Alternating solve | Appendix C, Eq. (C1), Fig. 11, PDF p. 11 | Holding one factor fixed reduces the fidelity optimization to an analytic generalized-eigenvalue step followed by an SVD; the two sides alternate. | The paper reports empirical convergence but proves no global-convergence theorem. | closed |
| Demonstrated scale | Sec. V, Table I, PDF pp. 6--7 | For three critical-Ising partition-function networks, FET outperformed a cut-cycle Schmidt truncation and converged in fewer than twenty iterations. | The benchmark is not a QEC circuit, a trajectory PEPS, or a multi-round record. | closed |
| Record bridge | Full-text scope; Sec. VI, PDF p. 7 | The applications discussed are tensor optimization and tensor-network renormalization. | No selective measurement instrument, branch-mass ledger, temporal detector fold, logical observable, Record distribution, TV bound, or LER bound is defined. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Tensor-network state and selected internal bond | Contract the norm network with the selected bond open | The environment can be computed for the network under study | Bond environment `Upsilon` and bond matrix `sigma` | Sec. II, Eq. (1), Fig. 1, PDF p. 2 | complete |
| `Upsilon` and `sigma` | Build left/right boundary matrices, dominant transfer eigenoperators, square roots, and an SVD | Dominant eigenoperators have the required positive support; stated degeneracies are handled | WTG bond representation | Sec. III, Eqs. (2)--(8), Figs. 2--3, PDF pp. 3--4 | complete |
| WTG transfer spectrum | Normalize absolute eigenvalues and evaluate entropy | The selected spectrum is finite and normalizable | Cycle entropy | Sec. IV, Eq. (11), PDF p. 5 | complete |
| `Upsilon`, `sigma`, and target rank | Maximize normalized fidelity by alternating the two bond factors and re-SVDing | The supplied environment is the environment used by the objective; iteration reaches an accepted stationary point | Truncated bond and local infidelity `1-F` | Sec. V, Eq. (12), Appendix C, Eq. (C1), PDF pp. 6, 11 | complete |

No replay row emits or compares a QEC Record. Adding trajectory branching, measurement folding, or a
full-record error bound would be an unsupported transformation.

## Project application

- The FET objective is the primary source-level match for the PEPS environment-aware split candidate:
  it specifies what local rank reduction optimizes and makes explicit that the full bond environment is
  an input.
- WTG and cycle entropy are useful diagnostics for closed-loop redundancy, but the source itself shows
  that cyclic WTG coefficients need not be physical-state invariants. They cannot be promoted to Record
  evidence.
- The current all-noop/non-degeneracy RED result remains scientifically informative: an implementation
  that never accepts a rank-reducing write has not exercised the source operation, even if transaction,
  rollback, and RNG gates pass.
- Even when a rank-reducing FET write occurs, local normalized fidelity remains a state-level objective.
  The project still needs an independent bridge to multi-round detector/observable Record law.

## Competing evidence and kill conditions

- Lubasch et al. show that approximate PEPS environments may lose positivity and that PEPS does not
  inherit the OBC-MPS identity norm gauge. Those facts constrain how an approximate `Upsilon` may be
  interpreted.
- Dziarmaga's NTU supplies an exactly contracted finite-neighborhood quadratic metric, a different
  environment/objective choice from Evenbly's whole-network normalized fidelity.
- Kill the proposed use if the implementation substitutes local singular values, entropy equality, or a
  state-independent cutoff for the source's declared environment and fidelity objective.
- Kill any Record-faithfulness claim unless a separate primary result establishes the local-FET-to-Record
  bridge and an independent project oracle verifies it.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned rows: six closed, one missing
- project fit: load-bearing for local PEPS FET semantics; insufficient for Record or LER faithfulness
- downstream permission: documentation and local-mechanism validation only; production pruning and
  faithfulness claims remain blocked

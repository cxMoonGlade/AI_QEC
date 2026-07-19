# Claim audit — Acuaviva minimal canonical form and the PEPS carrier boundary

## Status and decision

Retain Acuaviva et al., *The minimal canonical form of a tensor network*, as a load-bearing source
for the existence and unitary uniqueness of a minimum-Frobenius-norm representative in a uniform
PEPS gauge-orbit closure, its virtual-marginal balance condition, and algorithms that approximate
that representative. The exact gauge and orbit-closure statements preserve finite contraction-graph
states. They do not turn local tensor Frobenius error, marginal imbalance, or the paper's proposed
bond-truncation heuristic into a finite-trajectory state- or Record-fidelity certificate.

This audit changes no implementation and authorizes no carrier-status or faithfulness upgrade.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Gauge action and physical state | Def. 4.3 and Lemma 4.4, PDF pp. 20--21 | A finite gauge transformation acts on paired virtual legs, and every tensor in the orbit closure gives the same PEPS on each finite arbitrary contraction graph. | It does not identify a finite-bond truncation with a gauge transformation or bound a stochastic measurement law after truncation. | closed |
| Minimal canonical form | Def. 4.6 and Thms. 4.7--4.8, PDF pp. 21--22 | The canonical representative minimizes local tensor Frobenius norm over the gauge-orbit closure, is unique up to unitary gauges, and is characterized by opposite virtual marginals agreeing up to transpose. | The minimized norm is not a many-body state distance, detector probability distance, or Record metric. | closed |
| Need for orbit closure | Prop. 4.18 and Examples 4.21--4.23, PDF pp. 29--32 | If a closed-orbit representative is reached only as a non-orbit limit, it must have a nontrivial one-parameter symmetry; the paper supplies both closed-orbit and genuinely non-closed examples. | Nontrivial continuous symmetry is not stated as a sufficient condition in general, and finite symmetry alone is not a universal carrier diagnostic. | closed |
| Approximation algorithms | Algorithm 1, Thm. 5.1, Cor. 5.3, Def. 5.4, and Cor. 5.16, PDF pp. 34--36 and 42--43 | First- and second-order gauge algorithms approximate the balance condition or a minimal representative under explicit non-null and finite-bit assumptions; the dimension constant is exponentially small for more than one spatial direction. | The algorithms do not reduce bond dimension, validate an approximate environment, or certify a post-truncation physical trajectory. | closed |
| Proposed PEPS truncation | Sec. 6 item 1, PDF pp. 43--44 | The authors propose canonicalize-then-truncate by leading virtual-marginal eigenvectors as follow-up work requiring numerical study. | No optimality theorem, state-error bound, or complete Record-law bound is proved for this PEPS truncation proposal. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Uniform PEPS tensor `T` with paired virtual directions | Apply `g_k` and `g_k^{-T}` on opposite virtual legs | Contractions pair the corresponding directions on a finite graph | Exactly unchanged contracted PEPS state | Def. 4.3 and Lemma 4.4, PDF pp. 20--21 | closed |
| Gauge-orbit closure of `T` | Minimize the local tensor Frobenius norm | Reductive gauge action and Kempf--Ness theory | `T_min`, unique up to `U(D_1) x ... x U(D_m)` | Def. 4.6 and Thm. 4.7, PDF p. 21 | closed |
| Candidate representative | Evaluate the norm derivative along Hermitian gauge directions | The tensor is treated as a vector and only virtual legs transform | Balance residual `rho_(k,1)-rho_(k,2)^T`; zero iff minimal canonical | Eq. (4.4) and Thm. 4.8, PDF p. 22 | closed |
| Non-canonical tensor with `T_min != 0` | Iterated exponential gauge updates using normalized marginal mismatch | Exact local tensor marginals and the theorem's step size | Finite gauge element meeting the balance tolerance | Algorithm 1 and Thm. 5.1, PDF pp. 34--35 | closed |
| Rational finite-bit tensor and target relative tensor error | Box-constrained Newton norm minimization plus approximation-error bridge | `T_min != 0`; complexity includes `gamma^{-1}` | Gauge representative within relative local Frobenius error `delta` of a minimal representative | Cor. 5.16, PDF pp. 42--43 | closed |
| Minimal canonical tensor | Keep virtual subspace of the largest `D'` marginal eigenvalues | Proposed future truncation; no proved PEPS guarantee | Lower-bond tensor candidate | Sec. 6 item 1, PDF p. 44 | missing |

## Project application

The source can support a gauge-balancing or conditioning pre-pass for the research PEPS carrier only
at the level it proves: exact gauge transformations preserve the represented finite contraction-graph
state, and the balance residual diagnoses distance from the minimum-norm orbit-closure representative.
The current carrier is a finite-trajectory, record-emitting construction rather than the paper's uniform
translation-invariant PEPS setting, so any adapter requires a separately proved mapping of its tensors,
boundaries, measurements, and approximate environments to the source objects.

The paper does not repair the current RED FET non-degeneracy gate. Its algorithms canonicalize by
invertible gauges; they do not authenticate rank reduction. Its `delta`, `epsilon`, and `zeta` errors are
local tensor or canonical-balance quantities, not `RecordBatch` metrics. Even exact preservation of an
unmeasured PEPS under a gauge step would not make a subsequent approximate truncation a complete
multi-round Record certificate. The project must retain an independent state/record reference and the
open local-FET-to-QEC-observable bridge.

## Competing evidence and kill conditions

- `docs/SIMULATOR.md` judges carrier validity on the declared record law, not local tensor norm,
  marginal balance, state fidelity, bond dimension, or a truncation objective alone.
- `docs/simulator_validation/PEPS_FET_VALIDATION.md` records zero authenticated rank-reducing FET
  write-backs at the strict gate; a gauge-only canonicalization cannot convert that all-noop result into
  a non-degenerate pruning pass.
- Kill use as a truncation theorem if the implementation drops directions after canonicalization: Sec. 6
  explicitly labels that step a proposal whose numerical and theoretical properties remain follow-up.
- Kill use as a universal orbit-closure detector if it treats continuous symmetry as sufficient: Prop. 4.18
  proves the stated necessity direction only.
- Kill use as a Record certificate if any argument replaces a detector/observable distributional oracle
  with local Frobenius distance or virtual-marginal imbalance.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- minimal-canonical theorem row: closed
- orbit-closure qualification row: closed
- approximation-algorithm row: closed
- PEPS truncation-guarantee row: missing
- state-to-Record fidelity row: missing

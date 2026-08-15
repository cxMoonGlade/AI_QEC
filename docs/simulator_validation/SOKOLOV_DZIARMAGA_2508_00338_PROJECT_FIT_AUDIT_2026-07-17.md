# Claim audit — Sokolov--Dziarmaga zero modes and the PEPS pruning boundary

## Status and decision

Retain Sokolov, Zhang, and Dziarmaga, *Truncating loopy tensor networks by zero-mode gauge fixing*,
as a direct source for exact cut-state linear-dependence removal, the approximate zero-mode
truncation objective, and loop-aware initialization. It is a candidate source for a PEPS rank-reduction
initializer, not a certification theorem: the source's Gram metrics and norm-squared truncation errors
do not establish complete QEC Record fidelity, and its numerical examples generally place ZMT before
a separate variational optimization.

This audit changes no implementation and authorizes no carrier-status or faithfulness upgrade.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Exact zero-mode gauge | Sec. II, Eqs. (1)--(4), PDF pp. 2--3 | A null vector of the cut-state Gram matrix is an exact linear dependence; choosing the largest component as the eliminated direction reduces `D` to `D-1` without changing the tensor-network state. | A null vector of an approximate or differently defined local environment is not thereby an exact null vector of the full cut-state Gram operator. | closed |
| Near-zero truncation objective | Secs. II and IV, Eqs. (5) and (19), PDF pp. 3--4; Apps. A--B, PDF pp. 11--12 | Treating a small nonzero mode as a zero mode incurs a represented-state norm-squared error whose leading objective depends on both the metric eigenvalue and the selected gauge eigenvector component/eigenvalue. | The objective is not a condition-number theorem, a probability-distance bound, or a detector/observable Record metric. | closed |
| Pseudoinverse comparison | Sec. III, Eqs. (6)--(9), PDF p. 3 | In a two-state rank-deficient toy problem, the pseudoinverse selects a minimum-norm coefficient vector that retains both redundant states, while a homogeneous zero-mode shift selects an exact rank-one representation. | The toy example does not prove that every pseudoinverse-based PEPS optimizer retains redundant bonds or that ZMT globally converges. | closed |
| General bond zero modes | Sec. IV, Eqs. (10)--(19), PDF pp. 3--4 | The full `D^2 x D^2` cut-state metric permits matrix zero modes; choosing `z=-1/E_D`, SVD-factorizing the singular update, and absorbing factors into the endpoints reduces the bond. | Diagonalizability/Jordan handling and a local rank reduction do not certify a complete trajectory or measurement process. | closed |
| Loopiness and EAT | Sec. V, Eqs. (20)--(24), PDF pp. 4--5 | The leading left--right product of the metric is exact for a non-loopy bond; `lambda_2/lambda_1` measures deviation, and ZMT reduces to EAT in that exact product case. | Loopiness is a bond-metric diagnostic, not a gauge-invariant physical entanglement observable or a Record-fidelity score. | closed |
| Initialization evidence | Sec. VIII and Figs. 8--10, PDF pp. 6--8; Sec. XI, PDF p. 10 | In the reported Z2-gauge example the final optimized error and magnetization depend strongly on initialization, with ZMT3 outperforming SVD through the tested bond dimensions. | The finite examples do not prove universal superiority, exact physical fidelity, or record-law correctness. | closed |
| Switching threshold | Sec. X and Fig. 14, PDF pp. 9--10 | In the TRG experiment, `delta` decides when the sequential scheme switches from ZMT1 to ZMT2/3 while compression continues to the target rank. | The threshold is not a universal acceptance tolerance or a certificate that retained directions contain all physical information. | closed |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Cut bond with states `|psi_j>` | Form Gram matrix `g_ij=<psi_i|psi_j>` and diagonalize it | The Gram contraction is the metric of the actual cut states | Metric eigenmodes and exact linear dependencies | Eqs. (1)--(2), PDF p. 2 | closed |
| Exact null vector `Z` | Permute so `|Z_D|` is maximal and choose `z=-1/Z_D` | `N_D=0` exactly | State-preserving elimination of one bond direction | Eqs. (3)--(4), PDF pp. 2--3 | closed |
| Small nonzero compact mode | Apply the same elimination approximately | Leading small-mode treatment; Appendix A gives the corrected optimum | Local represented-state error `f=N_D/|Z_D|^2` at the zero-mode choice | Eq. (5), PDF p. 3; Eqs. (A4)--(A6), PDF pp. 11--12 | closed |
| Full cut-state metric and matrix eigenmode `Z_ij` | Choose `z=-1/E_D`, SVD the singular update, and absorb factors into adjacent tensors | The selected eigenmode is usable; general Jordan form remains singular | One-rank bond reduction and general leading error `f=N/|E_D|^2` | Eqs. (10)--(19), PDF pp. 3--4 | closed |
| Matricized full metric | Retain the leading left--right singular product | Exact product only when the bond is the sole left--right connection | EAT gauge, spectrum, and loopiness ratio | Eqs. (20)--(24), PDF p. 4 | closed |
| ZMT-initialized tensors | Run a separate alternating variational optimization | Model- and implementation-specific benchmark settings | Final local truncation error and selected observables | Figs. 4--11 and Secs. VI--IX, PDF pp. 5--8 | closed |

## Project application

The exact Gram-null construction is directly relevant to authenticating a non-degenerate PEPS pruning
candidate: if the project can independently establish that its matrix is the full cut-state Gram matrix,
then an exact kernel vector supplies a state-preserving rank reduction instead of a pseudoinverse-selected
redundant representation. If the matrix is only a local or approximate environment, the source does not
license promotion of its numerical zero mode to an exact physical gauge direction.

For near-zero modes, `f=N/|E_D|^2` is a local represented-state norm-squared objective. It may rank
initializers and expose conditioning pathologies, but it cannot replace the strict mutation firewall, the
non-degeneracy gate, or an independent state/Record oracle. The TRG `delta` is a method-switch threshold,
not an acceptance threshold. ZMT may be evaluated as a separately preregistered initializer before the
existing variational solve; changing the objective or tolerance merely to obtain write-backs remains
disallowed.

## Competing evidence and kill conditions

- `docs/SIMULATOR.md` and `docs/simulator_validation/PEPS_FET_VALIDATION.md` require complete
  record-law evidence beyond local environment fidelity or truncation objectives; the current strict FET
  non-degeneracy gate is RED.
- Kill exact-state language if the implemented metric is not independently shown to equal the cut-state
  Gram matrix in Eqs. (1) or (11), or if a nonzero mode is described as an exact gauge symmetry.
- Kill a general anti-pseudoinverse claim: Sec. III is a specific two-state singular example, not a theorem
  about every ALS normal equation.
- Kill a universal-conditioning claim if it cites only `f`: the paper provides truncation-error formulas and
  empirical initialization results, not a condition-number or optimizer-convergence bound.
- Kill a Record certificate if the local norm-squared error, loopiness, or benchmark observable replaces an
  independent detector/observable distributional comparison.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- exact zero-mode rank-reduction row: closed
- near-zero truncation-objective row: closed
- conditioning-theorem row: missing
- initializer benchmark row: closed
- complete Record-fidelity row: missing

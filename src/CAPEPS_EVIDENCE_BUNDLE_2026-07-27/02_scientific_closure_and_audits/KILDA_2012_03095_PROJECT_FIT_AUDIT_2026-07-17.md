# Project-fit audit — Kilda et al., arXiv:2012.03095v2

Date: 2026-07-17

## Frozen question

Can Kilda et al.'s stability analysis support a finite-bond PEPO/PEPS carrier claim, a
positivity claim, or a complete multi-round detector-Record faithfulness claim?

The source object is `outputs/papers/pepo_survey/2012.03095.pdf`, SHA-256
`d750982bd052408459beb0a6b1ce2655dcac236273bbd6e65ec660e79cedd25b`, identified by
the PDF stamp as arXiv:2012.03095v2. The complete 21-page object was read. Load-bearing
pages 1, 3, 4, 6, 7, 8, 10, 11, and 15 were rendered and visually checked.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| iPEPO mechanism | Sec. 2, Eqs. (1)-(2), p. 3; App. A.2, p. 15 | The density operator is vectorized as an iPEPS and propagated by two-body Liouvillian gates; observables use trace contractions. | It does not define a trajectory, terminal sampling law, or detector Record. | closed |
| local truncation mechanism | App. A.1.1, steps 1-6, pp. 10-11 | SU conditions a two-site SVD on diagonal bond spectra and retains the largest `D` singular values without the full environment. | It does not give a global density-operator or observable error bound for this truncation. | closed |
| stationarity diagnostic | Sec. 2, Eq. (3), p. 4; App. A.2, p. 15 | `epsilon_Lambda` is the largest rescaled inter-step singular-spectrum change, and every directional bond spectrum must pass the stop threshold. | Spectrum stationarity is not stated to prove density-matrix positivity, accuracy, or uniqueness of the NESS. | closed |
| monotone improvement with bond dimension | Sec. 2.2, Fig. 6, pp. 6-8 | Convergence can disappear when `D` is increased; examples include convergence at `D=3,4` but not `D=5,6`, and at `D=12` but not `D=14,15`. | It does not identify a generally sufficient finite `D`. | contradicted |
| robustness to protocol changes | Sec. 2.1, Figs. 2-5, pp. 4-6 | The reported nonconvergence persists under smaller timesteps, varied initial states, and two adiabatic sweeps in the tested regime. | It does not prove instability for all models or all update algorithms. | closed |
| positivity preservation | App. A.2, p. 15; complete method/results scope | The source states trace normalization and the PEPO-to-PEPS vectorization. | It gives no Hermiticity, positive-semidefiniteness, complete-positivity, or negativity diagnostic for the truncated iPEPO. | missing |
| local truncation to full Record law | Secs. 2-3 and App. A, pp. 3-16 | The evaluated outputs are bond-spectrum stationarity and local observables of an infinite-lattice NESS. | It gives no repeated-measurement/reset semantics, detector XOR fold, Record distribution, total-variation bound, or logical-error-rate bound. | missing |

## Notation ledger

| symbol | source meaning | domain or status | locator |
|---|---|---|---|
| `rho` | density operator of the dissipative XYZ model | vectorized to `|rho>` for iPEPO evolution | Eq. (1), p. 3; App. A.2, p. 15 |
| `L_alpha` | two-body Liouvillian on direction `alpha` | `alpha` in `{U,R,D,L}` | App. A.2, p. 15 |
| `D` | iPEPS/iPEPO virtual bond dimension | retained singular-value count per updated bond | App. A.1.1, pp. 10-11 |
| `chi` | CTM environment bond dimension | controls approximate observable contraction, not SU time evolution | App. A.1.2, pp. 11-14 |
| `Lambda^[alpha]` | diagonal directional bond spectra in the Vidal-form ansatz | four spectra, all required to satisfy the stop rule | Fig. 7, p. 10; App. A.2, p. 15 |
| `epsilon_Lambda` | largest relative spectrum change divided by timestep | stationarity diagnostic, not an accuracy metric for a Record | Eq. (3), pp. 4 and 15 |
| `delta t` | real-time Liouvillian step | gradually reduced during a run | App. A.2, p. 15 |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Dissipative XYZ master equation | Split the nearest-neighbor Liouvillian into four directional two-body pieces. | First-order Trotterization; infinite square lattice with a two-site unit cell. | Directional propagators `exp(-delta t L_alpha)`. | Eqs. (1)-(2), p. 3; App. A.2, p. 15 | checked |
| PEPO density operator | Fuse bra and ket physical indices to form vectorized `|rho>`. | PEPO-to-PEPS reshaping. | iPEPS-shaped object evolved with the SU machinery. | App. A.2, p. 15 | checked |
| Two neighboring site tensors and external diagonal spectra | Absorb external spectra, factor the sites, apply the two-body propagator, and SVD the updated bond. | The surrounding environment is represented only by the local diagonal spectra. | Updated pair with only the largest `D` singular values retained. | App. A.1.1, steps 1-6, pp. 10-11 | checked |
| Updated directional spectra | Compare consecutive spectra using Eq. (3). | A steady state requires the criterion for every one of the four directions. | Stop or continue decision based on spectrum stationarity. | Eq. (3), p. 4; App. A.2, p. 15 | checked |
| Time-evolved iPEPO | Trace physical indices and contract the infinite network with CTM. | Approximate CTM environment is used only for observables. | Local magnetization and correlators. | Sec. 2, pp. 3-4; App. A.1.2-A.2, pp. 11-15 | checked |
| Protocol and bond-dimension sweeps | Compare `epsilon_Lambda` histories across timestep, initial condition, sweep path, and `D`. | Tested XYZ parameter regimes only. | Stable or persistently oscillatory numerical histories. | Figs. 2-6, pp. 4-7 | checked |

No replay step produces a sample path, a QEC measurement history, detector coordinates, or a
full outcome distribution. Filling any of those steps from project intuition would be an unsupported
transformation.

## Project application

The paper is directly useful as a negative control for the current PEPO/PEPS research-carrier
frontier:

- Increasing a virtual bond cap is not a monotonic scientific certificate. A sweep must be allowed
  to expose loss of convergence rather than treating larger `D` as automatically more faithful.
- The source's `epsilon_Lambda` is a stationarity diagnostic. It must not be renamed as a state,
  positivity, Record-TV, or LER error.
- The reported instability occurs in SU evolution before CTM observable contraction. This isolates
  the failure in that experiment, but does not prove that every PEPO instability is CTM-independent.
- The paper does not validate the current environment-aware PEPS/FET path. Its conclusion merely
  points to full-environment truncation as promising work reported elsewhere.
- The source provides no positivity check. The current project therefore still needs its own trace,
  Hermiticity, and negativity/PSD gates for density-operator carriers.
- The paper has no repeated measurement, reset, temporal detector folding, sampled branch mass, or
  complete Record law. It cannot close finite-truncation full-record faithfulness.

Under `docs/SIMULATOR.md`, these facts support fail-closed research-carrier diagnostics only. They
do not promote PEPO or PEPS to a canonical Record backend.

## Competing evidence and kill conditions

The source cites McKeever and Szymanska's full-environment truncation as improving iPEPO stability,
but it does not reproduce that method or prove a general stability theorem for it. Kilda et al. also
note that full update can itself have stability problems in some closed-system time evolutions.

The following uses are killed by the source boundary:

- claiming that a larger `D` necessarily improves an SU-iPEPO result;
- treating convergence of bond spectra as proof that the represented density operator is physical;
- transferring the XYZ-model instability as a theorem about every PEPO/PEPS algorithm;
- treating a stationary NESS observable as a complete multi-round detector-Record certificate;
- using the paper to select a project acceptance tolerance or resource cap.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- iPEPO mechanism: `closed`
- SU truncation/stationarity mechanism: `closed`
- monotone bond-dimension improvement: `contradicted`
- positivity preservation: `missing`
- finite-truncation-to-Record bridge: `missing`
- allowed downstream use: negative-control and scope evidence for research-carrier validation
- prohibited downstream use: PEPO/PEPS positivity, Record-TV, LER, or canonical-backend promotion

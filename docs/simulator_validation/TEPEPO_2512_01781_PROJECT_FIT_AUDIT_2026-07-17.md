# Project-fit audit — Dunham and Szymańska, arXiv:2512.01781v1

Date: 2026-07-17

## Frozen question

What does tePEPO establish about two-dimensional operator construction, long-range Lindblad
evolution, itrSU truncation, environment contraction, and benchmarks, and which local update
quantities must remain separate from an adaptive detector-Record accuracy claim?

The source object is `outputs/papers/2512.01781.pdf`, SHA-256
`f1dc03277dc371f0852c8601ba604b8f26fa02c859e895b096b881b427fee2fd`, identified by
the PDF stamp as arXiv:2512.01781v1 dated 1 December 2025. The complete 19-page object was read.
Load-bearing pages 1, 3-13, 16, 18, and 19 were rendered and visually checked.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| PEPO time-evolution operator | Sec. III, Eqs. (4)-(7), pp. 3-5 | A size-extensive cluster expansion and finite-signaling-agent rules construct a 2D tensor-network operator. | It does not prove that every generator has a compact FSA representation. | closed-with-scope |
| long-range representation | Sec. IV, Eqs. (9)-(13), pp. 6-7 | Radial power laws are fitted by sums of Gaussian separable profiles and applied as a sequence of `k_max` tePEPO factors. | The spatial fit, cluster expansion, Suzuki-Trotter split, and repeated truncations remain distinct errors. | closed-with-limitation |
| open-system vectorization | Sec. V.A-B, Eq. (14), pp. 7-8; App. C, pp. 17-18 | The density matrix is an iPEPO; vectorization produces an iPEPS-shaped object, and coherent/dissipative two-body terms become FSA rules in Liouville space. | The vectorized finite-`D` object is not shown to remain positive. | closed-with-limitation |
| itrSU mechanism | Sec. V.C, Eq. (15), pp. 8-9; App. D, p. 18 | Previous-step isometries truncate all non-target bonds, the remaining bond receives an SU SVD, and this is iterated until bond weights stabilize. | The rank-one bond-weight environment is still uncontrolled. | closed-with-limitation |
| environment contraction | Sec. V.D, p. 9; App. E, p. 19 | VUMPS boundary MPS and transfer fixed points approximate the trace environment for reduced density matrices and observables. | VUMPS does not make itrSU's local truncation environment exact and does not handle diagonal correlators in the stated construction. | closed-with-limitation |
| exact benchmark | Sec. VI.A.1, Figs. 5-6, pp. 9-10 | At `h=0` the long-range dissipative Ising model has an exact solution; increasing `k_max` generally improves results, while more factors can worsen early-time error through extra truncations. | The benchmark does not isolate a universal truncation-error law. | closed |
| nonexact benchmark | Sec. VI.A.2, Fig. 7, pp. 10-11 | At `h/gamma=0.5`, results require convergence checks in `D`; some low-`D` histories are unstable and `D=10` is smoother in the shown cases. | Agreement across selected `D` values is not an exact error certificate. | closed-with-limitation |
| Rydberg benchmark | Sec. VI.B, Figs. 8-11, pp. 10-13 | The method reports a dipolar-blockade crossover and late-time steady states, with unstable/unreliable early dynamics in stronger-interaction cases. | The late-time recovery is empirical and does not validate the unreliable early-time path. | closed-with-limitation |
| local update indicator | Eq. (15), pp. 8 and 13; App. D, p. 18 | The typeset Eq. (15) displays `delta^[i] < max_alpha ||lambda_alpha^[i]-lambda_alpha^[i-1]||`; the surrounding prose treats `delta` as the convergence measure, stops it below `epsilon_SU`, and later rescales it by the timestep for Fig. 11. | The apparent definition/inequality typo is not resolved in the source, and the indicator is not a state norm, positivity metric, observable error, branch-probability error, or Record distance. | closed-with-source-ambiguity |
| adaptive Record | Complete source scope, pp. 1-19 | The source computes deterministic density-operator evolution and reduced observables. | It contains no measurement instrument, adaptive control, reset, sampled branch, detector fold, complete Record distribution, TV bound, or LER bound. | missing |

## Notation ledger

| symbol | source meaning | domain or status | locator |
|---|---|---|---|
| `G` | generator written as sums of at-most-two-body and one-body terms | FSA-compatible class considered by the construction | Eq. (5), p. 4 |
| `W^I`, `W^II` | first-order size-extensive operator approximations | `W^II` additionally includes products whose supports intersect once | Sec. III.A-B, pp. 4-6 |
| `eta_h`, `eta_v` | horizontal and vertical tePEPO bond dimensions | determined by the FSA rule set | Tables I and III, pp. 4 and 6 |
| `k_max` | number of radial Gaussian basis components and tePEPO factors | increases operator resolution and number of apply/truncate steps | Eqs. (11)-(13), p. 7 |
| `D` | iPEPO state bond dimension | target bond dimension after each tePEPO application | Sec. V.A-C, pp. 7-8 |
| `lambda_alpha` | bond-weight matrix on bond `alpha` | rank-one environment surrogate used by SU/itrSU | Fig. 4 and Sec. V.C, p. 8 |
| `delta^[i]` | convergence quantity associated with the maximum bond-weight change | Eq. (15) is typeset as an inequality rather than a clean definition; it is rescaled by `Delta t` in Fig. 11 | Eq. (15), pp. 8 and 13 |
| `epsilon_SU` | itrSU stopping tolerance | chosen as `10^-8` in the reported simulations | pp. 8-9; App. D, p. 18 |
| `chi` | VUMPS boundary-MPS bond dimension | finite approximation to infinite trace environment | App. E, p. 19 |
| `S_alpha` | entropy of normalized bond weights | exact entanglement entropy only on an acyclic network; proxy here | Eq. (17), p. 10 |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Local generator terms | Encode accepted operator strings as nonzero FSA rules and apply the double-wrapping rule. | Generator belongs to the represented rule class; chosen `W^I` or `W^II` approximation. | A translationally invariant tePEPO operator. | Eqs. (5)-(7), Tables I-II, Algorithm 1, pp. 4-5 | checked |
| Radial power-law profile | Fit the profile on a finite disc by a weighted sum of separable Gaussian functions. | User-chosen fit disc, `k_max`, per-Gaussian exponential count, and tolerance. | `k_max` FSA-representable radial terms. | Eqs. (9)-(12), pp. 6-7 | checked |
| Fitted long-range generator | Apply `W^[1](tau)...W^[k_max](tau)` and truncate after each factor. | First-order size-extensive expansion and Suzuki-Trotter decomposition; `tau -> 0` limit stated. | Time-evolved iPEPO with `k_max` update/truncation pairs per step. | Eq. (13), pp. 7-8 | checked |
| GKSL density evolution | Vectorize coherent and dissipative terms into Liouville-space two-body products. | Markovian Lindblad equation; vectorization convention of Eq. (14). | FSA-compatible superoperator rules; a nonlocal two-site jump adds three channels in App. C. | Eq. (14), p. 8; Eqs. (C2)-(C8), pp. 17-18 | checked |
| Enlarged iPEPO after one tePEPO factor | Use prior isometries on all non-target bonds, run QR/SVD on the target pair, update the isometries and bond weight, and iterate. | Bond-weight rank-one environment approximates the surrounding network; pseudo-inverses are well behaved. | Each enlarged bond `D eta` is returned to `D`. | Sec. V.C, pp. 8-9; App. D, p. 18 | checked |
| Truncated infinite iPEPO | Contract traced rows with a VUMPS boundary MPS and left/right transfer fixed points. | Finite boundary dimension `chi`; stated geometry does not support diagonal correlators. | Reduced density matrices, local observables, and selected correlations. | Sec. V.D, p. 9; App. E, p. 19 | checked |
| Benchmark histories | Compare with an exact `h=0` Ising solution, then sweep `D` in nonexact Ising and Rydberg cases. | Model- and parameter-specific tests; convergence is empirical where no exact solution exists. | Magnetization, correlations, purity, bond entropy, and convergence histories. | Sec. VI, Figs. 5-11, pp. 9-13 | checked |

The replay closes the operator-construction and local-truncation path. It does not define a Kraus
instrument for measurements, sample or renormalize outcome branches, apply outcome-dependent
feedback, or emit a detector Record.

## Error decomposition required by the source

The paper itself exposes several separable approximations that must not be collapsed into one
“tePEPO error” number:

1. radial-profile fitting on the selected disc;
2. finite `W^I` or `W^II` cluster expansion;
3. Suzuki-Trotter splitting across `k_max` fitted components;
4. `k_max` repeated state truncations per timestep;
5. itrSU's uncontrolled rank-one environment;
6. finite state bond dimension `D`;
7. finite VUMPS boundary dimension `chi` for observables;
8. time-to-steady-state and local bond-weight stationarity.

The exact `h=0` benchmark measures the combined effect for one model and protocol. It is not a
general theorem that bounds any one component independently.

## Project application

tePEPO is directly relevant to the retained PEPO/PEPS research frontier because it reconstructs a
large two-dimensional operator and provides a concrete apply/truncate pipeline:

- FSA rules and Gaussian expansions are useful operator-level references for long-range two-body
  terms, including vectorized two-site Lindblad operators.
- itrSU is a concrete local truncation algorithm, but the paper explicitly retains the uncontrolled
  simple-update environment approximation. It is therefore a candidate research update, not an
  intrinsic fidelity certificate.
- The source's exact `h=0` Ising benchmark is useful as a model-specific corruption detector for an
  implementation of the paper's method.
- `delta^[i]`, `epsilon_SU`, bond entropy, agreement across selected `D`, and late-time stationarity
  are local or model-specific diagnostics. None controls branch probabilities after measurements.
- VUMPS supplies an observable environment, not a proof that state truncation was globally optimal.
  Its stated diagonal-correlation limitation also matters when importing observables with different
  lattice geometry.

For the project's adaptive simulator, the necessary missing bridge begins after density-operator
evolution: instrument insertion, outcome-conditioned state update and normalization, reset,
outcome-dependent scheduling, detector folding, and exact-vs-truncated complete Record comparison.
Until that bridge is independently implemented and tested, tePEPO cannot support a Record-TV or LER
claim.

Under `docs/SIMULATOR.md`, the paper supports a research-carrier operator/truncation path and
fail-closed diagnostics only. It does not promote PEPO/PEPS to a canonical Record backend.

## Competing evidence and kill conditions

The discussion states that itrSU is less robust than regular SU, still assumes the same uncontrolled
environment, and may benefit from full-update or loop-corrected environments. It also reports
correlation lengths of a few sites, beyond what bond weights alone capture.

The following uses are killed by the source boundary:

- treating Eq. (15) or `epsilon_SU=10^-8` as a physical-state accuracy tolerance;
- treating bond entropy as exact PEPO entanglement on the loopy square lattice;
- attributing early-time accuracy to runs that the paper labels unstable or unreliable;
- assuming increasing `k_max` or `D` improves every timestep monotonically;
- treating VUMPS observable convergence as proof of itrSU truncation accuracy;
- claiming positivity or complete positivity of the finite-`D` truncated representation;
- turning deterministic local-observable agreement into adaptive full-Record faithfulness;
- using model-specific benchmark values as project acceptance thresholds.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- tePEPO/FSA operator construction: `closed for the declared generator class`
- Gaussian long-range representation: `closed with fit and splitting choices exposed`
- itrSU operation: `closed with uncontrolled-environment limitation`
- exact benchmark: `closed for the stated h=0 model and protocol`
- positivity: `missing`
- adaptive measurement and Record semantics: `missing`
- finite-truncation-to-Record bridge: `missing`
- allowed downstream use: operator-level reference, local truncation prototype, and model-specific diagnostics
- prohibited downstream use: universal state-error, positivity, Record-TV, LER, or canonical-backend certificate

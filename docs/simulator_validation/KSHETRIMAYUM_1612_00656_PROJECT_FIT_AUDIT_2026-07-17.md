# Project-fit audit — Kshetrimayum, Weimer, and Orús, arXiv:1612.00656v4

Date: 2026-07-17

## Frozen question

What does the origin iPEPO paper actually establish about the carrier, simple-update evolution,
steady-state objective, and numerical diagnostics, and what cannot be promoted to a finite-truncation
or complete detector-Record faithfulness claim?

The source object is `outputs/papers/pepo_survey/1612.00656.pdf`, SHA-256
`5ed4469fceceb276cbb9a1769ec31a63a83e6e43720e60cf1eebcb8eeb66d538`, identified by
the PDF stamp as arXiv:1612.00656v4 dated 5 September 2017. The complete 12-page object,
including its supplementary notes, was read. Load-bearing pages 1, 2, 3, 4, 5, and 8-12 were
rendered and visually checked.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Markovian steady-state objective | Eqs. (1)-(2), pp. 1-2; Table I, p. 2 | A local GKSL generator is vectorized and real-time evolution is used to approach a zero-eigenvalue steady state. | It does not formulate a trajectory ensemble, detector stream, or adaptive measurement policy. | closed |
| iPEPO carrier | Fig. 1 and text, p. 2; Supp. Note 1, p. 8 | A PEPO represents the infinite-lattice density operator; vectorization fuses bra and ket into a PEPS physical leg of dimension `d^2`. | The finite-`D` representation does not guarantee positivity. | closed-with-limitation |
| simple-update mechanism | Supp. Eq. (3) and Fig. 2, pp. 8-9 | First-order Trotter gates are applied bondwise and an SVD retains the largest `D` singular values. | The truncation omits the full two-dimensional environment and has no global error bound. | closed-with-limitation |
| observable environment | Main text, p. 3; Supp. Note 3, pp. 8-10 | Local observables are evaluated with an approximate CTM environment. | CTM observable contraction does not repair the environment omitted during SU truncation. | closed-with-limitation |
| steady-state diagnostic | Main text, p. 3 | `Delta=<rho_s|L|rho_s>` and the negative-eigenvalue sum `epsilon_n` are monitored. | The paper explicitly says neither quantity characterizes distance to the steady state. | closed-negative |
| monotone improvement in `D` | Ising results, pp. 4-5 | The paper observes non-monotonic convergence with bond dimension near the transition and says it remains to be understood. | It gives no monotone finite-`D` convergence theorem or generally sufficient `D`. | contradicted |
| strong-dissipation regime | Carrier motivation, p. 2; Discussion, p. 5 | The algorithm relies on the hypothesis that a strong dissipative attractor reaches a steady state before operator entanglement becomes too large. | The hypothesis is not a theorem and weak-dissipation adiabatic continuation is suggested rather than certified. | bounded-hypothesis |
| positivity | Main text, pp. 2-3; Supp. Note 1, p. 8 | PEPO tensors can represent nonpositive operators, and reduced-state negativity is monitored numerically. | There is no positivity-preserving parametrization or proof that the global density operator is positive. | missing |
| finite truncation to complete Record law | Complete source scope, pp. 1-12 | The evaluated outputs are steady-state and local-observable diagnostics on infinite lattices. | There is no repeated measurement/reset semantics, adaptive branch update, joint Record distribution, TV bound, or LER bound. | missing |

## Notation ledger

| symbol | source meaning | domain or status | locator |
|---|---|---|---|
| `rho` | reduced density operator | represented as an infinite PEPO | Eq. (1), p. 1; Fig. 1, p. 2 |
| `L` / `L_#` | Liouvillian superoperator and its vectorized matrix | local nearest-neighbor decomposition is assumed for the update | Eqs. (1)-(2), pp. 1-2 |
| `|rho>_#` | vectorized density operator | PEPS-shaped object with physical dimension `d^2` | Eq. (2) and Fig. 1, pp. 1-2 |
| `D` | PEPO virtual bond dimension | number of singular values retained by SU | Fig. 1, p. 2; Supp. Fig. 2, p. 9 |
| `lambda_1,...,lambda_4` | positive diagonal bond-weight matrices | local Vidal-like environment surrogate | Supp. Figs. 1-3, pp. 8-9 |
| `Delta` | expectation of the vectorized Liouvillian in the approximate steady state | diagnostic, explicitly not a distance | p. 3 |
| `epsilon_n` | sum of negative eigenvalues of an `n`-site reduced density matrix | local nonpositivity diagnostic, explicitly not a distance | p. 3 |
| `chi` | CTM environment bond dimension | controls approximate local-observable contraction | p. 3; Supp. Notes 3-4, pp. 8-11 |
| `S_op` | entanglement entropy of the vectorized density operator | not mixed-state entanglement; bounded by `4 L log_2 D` for an `L x L` block | Supp. Eqs. (4)-(6), pp. 9-10 |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Local GKSL master equation | Vectorize the density operator and Liouvillian. | Time-independent, Markovian generator; nearest-neighbor locality for the stated update. | Linear evolution of a PEPS-shaped `|rho>_#`. | Eqs. (1)-(2), pp. 1-2 | checked |
| PEPO with bra and ket physical legs | Fuse the two physical legs at every site. | Infinite square lattice; two-site unit cell in the implementation. | iPEPS representation with physical dimension `d^2` and bond dimension `D`. | Fig. 1, p. 2; Supp. Note 1, p. 8 | checked |
| Vectorized state and two-site Liouvillian terms | Apply a first-order product of two-body gates. | Finite timestep; Trotter error is not independently bounded in the benchmarks. | Enlarged local bond before truncation. | Supp. Eq. (3), p. 8 | checked |
| Updated tensor pair and surrounding bond weights | Form the local tensor, SVD the updated bond, keep the largest `D` singular values, and reconstruct the pair. | Surrounding two-dimensional environment is replaced by local diagonal weights. | SU-truncated iPEPO tensors and updated bond weights. | Supp. Fig. 2 and text, pp. 8-9 | checked |
| Infinite iPEPO | Approximate its environment by directional CTM moves. | Finite environment dimension `chi`. | Local reduced density matrices and observables. | Supp. Note 3, Figs. 3-4, pp. 8-10 | checked |
| Approximate steady-state tensors | Evaluate `Delta`, local negativity sums, and convergence across `D`. | These are diagnostics, not certified distances. | Numerical plausibility checks and model-specific phase plots. | Main text, pp. 3-5 | checked |

No replay step emits a sampled branch, conditions a later quantum operation on an earlier outcome,
applies a reset, folds measurement bits into detectors, or compares complete outcome laws.

## Project application

This source establishes the historical iPEPO/SU substrate, but only as a research-carrier starting
point:

- It supplies the PEPO-to-vectorized-PEPS representation and the local real-time Liouvillian update.
- It makes the truncation boundary explicit: SU keeps the largest local singular values while
  ignoring the full two-dimensional environment.
- `Delta`, `epsilon_n`, bond spectra, operator entropy, and CTM convergence may be retained as
  internal diagnostics, each under its source meaning.
- None of those quantities is a distance between complete emitted Record laws. They therefore
  cannot substitute for exact-vs-truncated branch probabilities, Record TV, or logical-error-rate
  comparisons.
- The source does not preserve positivity by construction. Any project carrier needs independent
  trace, Hermiticity, and PSD/negativity gates rather than relying on the source's small reported
  local negativity.
- The paper's own non-monotonic `D` observation forbids treating a larger virtual bond cap as an
  automatic fidelity certificate.

Under `docs/SIMULATOR.md`, this is admissible mechanism and limitation evidence for the PEPO/PEPS
research frontier. It does not promote a finite-`D` iPEPO to a canonical Record backend.

## Later-source boundary

This audit deliberately does not import later results into the origin paper. In particular, this
source cannot by itself certify:

- the parameter-regime instability and non-monotone fixed-point histories later studied by Kilda
  et al.;
- full-environment truncation, weighted-trace-gauge, or their accuracy claims;
- tePEPO/FSA long-range operators or iterative simple update;
- any convergence, positivity, or full-Record guarantee for those later methods.

Those are distinct source objects. The origin paper may be cited as the iPEPO/SU starting point,
not as retrospective evidence for later corrections or extensions.

## Competing evidence and kill conditions

The following uses are killed by the source boundary:

- calling the strong-dissipation intuition a convergence theorem;
- interpreting a small `Delta` or `epsilon_n` as a norm bound to the exact steady state;
- claiming positivity of the finite-`D` PEPO;
- assuming monotone improvement with `D`;
- transferring the Ising or XYZ benchmark conclusions outside their tested models and parameters;
- treating local steady-state observables as a complete multi-round detector-Record certificate;
- attributing later FET, WTG, stability, or tePEPO results to this paper.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- iPEPO representation and SU operation: `closed`
- strong-dissipation applicability: `bounded hypothesis`
- monotone finite-`D` convergence: `contradicted by the paper's own observation`
- distance-to-steady-state certification: `explicitly absent`
- global positivity: `missing`
- finite-truncation-to-Record bridge: `missing`
- allowed downstream use: historical carrier mechanism, operation reconstruction, and fail-closed diagnostics
- prohibited downstream use: convergence theorem, positivity certificate, or Record-TV/LER promotion

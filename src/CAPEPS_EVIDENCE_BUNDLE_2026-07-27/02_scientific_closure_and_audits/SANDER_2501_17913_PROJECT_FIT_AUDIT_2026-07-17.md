# Project-fit audit — Sander et al. 2501.17913v2

Date: 2026-07-17
Source artifact: `docs/papers/2501.17913v2.pdf`
Source SHA-256: `9c2b2f2584da0270ef740c5e9ef0b5bc5d2f0fa88326bd0b8b7f04d634dcd2b5`
Question: does the tensor jump method close the restricted MCWF/MPS finite-bond branch-mass or
multi-round detector-Record faithfulness rows?

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| MCWF branch construction | Sec. II.B, Eqs. (2)–(13), PDF pp. 3–4 | Non-Hermitian evolution produces a norm deficit used as total jump probability; individual `L_m^dagger L_m` weights select the channel; normalized pure-state projectors recover the density operator in the ensemble/continuum limits. | It does not make an MPS truncation loss part of physical jump mass. | closed |
| TJM split evolution | Sec. III.A–III.B, Eqs. (14)–(28), Fig. 1, PDF pp. 4–5 | TJM combines dynamic TDVP, dissipative contraction, and a stochastic jump process using Strang splitting and a sampling MPS. | It does not claim arbitrary operator support or arbitrary non-Markovian noise. | closed |
| Dynamic finite-bond rule | Sec. III.C, Eqs. (29)–(37), PDF pp. 6–7 | Two-site TDVP grows bonds while below `chi_max`; one-site TDVP constrains evolution after the cap is reached, replacing truncation by projection error at capped bonds. | It does not prove the capped trajectory has the same branch law as the full-bond trajectory. | closed |
| Single-site dissipative factorization | Sec. III.D, Eqs. (38)–(40), PDF p. 7 | Exact sitewise dissipative contraction follows from the explicitly assumed single-site jump operators and commuting local factors and does not increase MPS bond dimension. | It does not establish this factorization for connected multi-site jump operators. | closed |
| TJM jump sampling | Sec. III.E, Eqs. (41)–(45), PDF pp. 7–8 | TJM takes `delta p = 1 - ||Phi^(i)||^2`, compares it with a uniform draw, computes channel probabilities from the dissipatively evolved MPS, applies one selected local jump, and normalizes afterward. | It does not specify a separate acceptance budget for a raw candidate-mass residual. | closed |
| Full-bond Monte Carlo convergence | Sec. IV.B, Theorem 2 and Eqs. (52)–(56), PDF p. 10; Appendix B, Theorem 7, PDF pp. 24–25 | The density estimator is unbiased and its standard deviation scales as `1/sqrt(N)` when each TJM trajectory is represented by an MPS of full bond dimension. | The theorem does not cover the dynamic finite-`chi_max` execution used for scaling. | closed with limiting hypothesis |
| Finite-bond error statement | Sec. IV.C, Eqs. (57)–(58), PDF pp. 10–11 | The finite-manifold method has Strang, TDVP time-step, and TDVP projection errors; the one-site projection is the best 2-norm approximation to the Hamiltonian action inside the chosen tangent space. | It does not bound density-matrix error, trajectory-law error, or detector-Record error from the projection error. | closed |
| Finite-bond empirical benchmark | Sec. V, Fig. 4, PDF pp. 11–12 | For the declared ten-site TFIM benchmark, trajectory count usually dominates the shown local-observable error, while bond dimension still controls localized features. | This finite example is not a theorem and does not establish size-independent finite-bond faithfulness. | closed |
| Multi-round detector Record faithfulness | Full-text scope: abstract; Secs. I–VIII and appendices, PDF pp. 1–25 | Outputs are density estimates and expectation values of physical observables at selected times. | The paper defines no schedule-sealed measurement layout, temporal detector XOR, logical bit, full Record distribution, total-variation bound, or logical-error-rate bridge. | missing |

## Notation ledger

| source symbol | source meaning | domain or scope | fixed/variable |
|---|---|---|---|
| `H_0` | Hermitian system Hamiltonian | Lindblad model | model-defined |
| `H_D` | `-i/2 sum_m gamma_m L_m^dagger L_m` | dissipative part of the effective Hamiltonian | model-defined |
| `delta p` | norm deficit used as total jump probability | one finite TJM/MCWF time step | state- and step-dependent |
| `Pi_m` | normalized probability of jump channel `m` | conditional on a jump | state-dependent |
| `Phi` | sampling MPS | reordered TJM evolution between queried physical states | trajectory-dependent |
| `chi_max` | dynamic TDVP bond cap | MPS execution parameter | user-controlled |
| `rho_N` | average of `N` pure-state projectors | fixed-time density estimator | random estimator |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Lindblad model and normalized state | evolve under the non-Hermitian effective Hamiltonian | first-order MCWF construction for Eqs. (6)–(11) | unnormalized candidate and norm-deficit jump probability | Sec. II.B, Eqs. (2)–(8), PDF p. 3 | reproduced |
| total jump probability and channel expectations | uniform jump/no-jump draw, then conditional channel draw | `delta p` is a valid probability and channel weights normalize | normalized next MCWF state | Sec. II.B, Eqs. (9)–(11), PDF pp. 3–4 | reproduced |
| sampling MPS | Strang-ordered dynamic TDVP and dissipative contraction | Markovian Lindblad model; Hamiltonian and dissipative pieces are split as declared | pre-jump TJM MPS | Sec. III.A–III.D, Eqs. (14)–(40), PDF pp. 4–7 | reproduced |
| pre-jump TJM MPS | compute norm deficit, sweep local jump weights, sample one channel, apply it, then normalize | every jump operator is single-site for the implemented factorization | next sampling MPS | Sec. III.E, Eqs. (41)–(45), PDF pp. 7–8 | reproduced |
| `N` independent full-bond trajectories | average pure-state projectors and apply variance calculation | each MPS has full bond dimension; sufficiently small time step in the appendix derivation | unbiased density estimator with `1/sqrt(N)` standard deviation | Theorem 2, PDF p. 10; Theorem 7, PDF pp. 24–25 | reproduced only under full-bond hypothesis |
| finite-`chi_max` trajectory | use full-bond convergence theorem unchanged | theorem hypothesis is violated | no source-supported finite-bond convergence conclusion | Theorem 2, PDF p. 10 versus Sec. III.C and IV.C, PDF pp. 6–7 and 10–11 | blocked |
| TJM physical observables | map to multi-round detector Record law | source supplies no measurement/Record construction | no source-supported output | full-text boundary, PDF pp. 1–25 | blocked |

## Project application

This is the closest of the three MPS sources to the restricted MCWF/MPS route. It supports:

- preserving raw norm through the no-jump candidate until the stochastic branch decision;
- selecting a jump channel from explicit `L_m^dagger L_m` weights and normalizing only afterward;
- distinguishing physical norm deficit from TDVP projection and time-step errors;
- keeping the single-site dissipative-factorization assumption explicit rather than silently extending
  it to connected multi-site supports;
- treating finite bond dimension as an additional approximation outside the paper's full-bond
  convergence theorem.

It does **not** close current acceptance. The project's connected three-to-five-site Hamiltonian clusters
are not the paper's single-site jump factorization, and the project must independently verify operator
support/order and source preservation. More importantly, neither the theorem nor Fig. 4 maps finite-bond
projection error to the full stochastic trajectory law, schedule-defined detector Record distribution, or
logical-error rate. A completed or normalized finite-bond run remains diagnostic unless an independent
Record oracle is registered.

## Competing evidence and kill conditions

- Jaschke et al. 1804.09796v2 describes a waiting-time QT algorithm and explicitly warns that a
  numerical solver can contaminate the norm used for jump timing; that warning limits any use of TJM
  norm deficit when finite-bond or local-solver errors are not separately controlled.
- Paeckel et al. 1901.05824v3 gives the local MPS truncation/error taxonomy and explicitly denies that
  a sequence of locally optimal SVDs must be globally optimal.
- Kill a finite-bond convergence claim that cites Theorem 2 or Theorem 7 without stating the full-bond
  hypothesis.
- Kill an extension of Eqs. (38)–(40) to connected multi-site jump operators without a new derivation;
  the exact factorization is sourced only for single-site jumps.
- Kill Record-faithfulness if evidence consists only of density-matrix unbiasedness at full bond,
  `1/sqrt(N)` Monte Carlo scaling, local-observable agreement, empirical normalization, or a fixed RNG
  seed.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- MCWF/TJM probability mechanism row: closed
- single-site dissipative factorization row: closed and scope-limited
- full-bond convergence row: closed only under its explicit hypothesis
- finite-bond trajectory-law row: missing
- detector Record-faithfulness row: missing
- project disposition: `directly_relevant_but_insufficient_for_finite_bond_Record_claims`
- current gate effect: `RECORD_BRIDGE_OPEN`; `PRODUCTION_PRUNING_CODE_BLOCKED`

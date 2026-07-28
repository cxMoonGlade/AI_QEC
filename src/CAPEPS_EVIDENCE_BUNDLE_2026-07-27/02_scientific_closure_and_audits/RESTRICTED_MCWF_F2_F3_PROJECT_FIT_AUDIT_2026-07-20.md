# Project-fit audit — restricted MCWF F2/F3 source packet

Date: 2026-07-20

## Source identities

| source | pinned artifact | SHA-256 | role |
|---|---|---|---|
| Oi and Schirmer, *Fundamental Speed Limits on Quantum Coherence and Correlation Decay* | `docs/papers/1109.0954v1.pdf` | `29fb809a2f661af434bda4197fb22f4e109c662282e52905e2f55e6b9eb06a8c` | diagonal pure-dephasing dissipator, coherence-rate convention, collapse-gauge invariance |
| Arsenijevic and Bankovic, *Microscopic derivation of the one qubit Kraus operators for amplitude and phase damping* | `docs/papers/1606.01145v1.pdf` | `32e3d12077bef0b1e6eb84f2f85f5bc35fc1fce6b5f9a3e58c625cf902ee0694` | microscopic finite-temperature down/up master equation and pure phase damping |
| Garner et al., *Exact and Efficient Stabilizer Simulation of Thermal-Relaxation Noise for Quantum Error Correction* | `docs/papers/2512.09189v1.pdf` | `c1be4a05112b90c3ec250cca2ffbe8bfce06b0fc443e9fc9b2c6bf63a0cb88e4` | independent finite-temperature convention, equilibrium population, and explicit reset channels |
| Czajkowski and Grilo, *On-State Commutativity of Measurements and Joint Distributions of Their Outcomes* | `docs/papers/2101.08313v2.pdf` | `29bfff3bc43db7e5159529ae7be85f87de4803589703fe3f8fa8790f547986ee` | selective measurement update and ordered joint-outcome law |
| Weissman et al., *Inequalities for the L1 Deviation of the Empirical Distribution* | `docs/papers/weissman_2003_l1_deviation.pdf` | `1e0a3f2904f6cde09ec34b8e87f69abf681fa75388e889112e00fabe4266203d` | one-sample finite-alphabet L1/TV concentration and union-bound structure |

The existing admitted Sander et al. source review remains the owner of the generic Lindblad-to-MCWF
ensemble bridge. This packet does not reopen the finite-bond or complete-Record claims that Sander et
al. leave unresolved.

## Assigned closure rows

| row | exact source location | source says | project consequence | status |
|---|---|---|---|---|
| Lindblad dissipator convention | Oi and Schirmer, Methods, Eqs. (6)–(7), PDF p. 4; Garner et al., Eqs. (1)–(2), PDF p. 3 | `D[L](rho)=L rho L† - 1/2{L†L,rho}`; scalar rate factors can be placed outside the dissipator. | Every fixture must declare whether a parameter is a generator coefficient or a collapse amplitude; the two must not be conflated. | closed |
| Pure-dephasing coherence rate | Oi and Schirmer, Eqs. (2)–(4), PDF p. 2 | For diagonal collapse entries, the off-diagonal density element decays as `exp(-Gamma_mn t)`, with `Gamma_mn` fixed by the diagonal-entry difference. | For `n=|1><1|`, `L=sqrt(2 gamma_phi)n` gives `Gamma_01=gamma_phi`; removing `sqrt(2)` gives `Gamma_01=gamma_phi/2`. | closed |
| Independent pure-dephasing convention | Garner et al., Eqs. (1)–(4), PDF p. 3; Arsenijevic and Bankovic, Eqs. (48), (56b)–(57), PDF pp. 12–13 | `(gamma_phi/2)D[sigma_z]` produces coherence decay `exp(-gamma_phi t)`; `r(sigma_z rho sigma_z-rho)` produces `exp(-2rt)`. | Since `D[sigma_z]=4D[n]`, `(gamma_phi/2)D[sigma_z]=D[sqrt(2 gamma_phi)n]`. The F2 normalization is independently cross-checked. | closed |
| Collapse gauge invariance | Oi and Schirmer, Eqs. (10)–(11), PDF p. 5 | Unitary mixing of collapse operators preserves the summed dissipator; adding an identity component changes only the effective Hamiltonian as stated. | In particular, `D[exp(i theta)L]=D[L]`. A global sign or phase is not a verdict-driving mutation. | closed |
| Finite-temperature down/up rates | Arsenijevic and Bankovic, Eq. (16), PDF p. 5; Garner et al., Eqs. (1)–(2), PDF p. 3 | A thermal qubit has downward coefficient `gamma(n_bar+1)` multiplying `D[sigma_-]` and upward coefficient `gamma n_bar` multiplying `D[sigma_+]`. | F3 must contain both families with independent hand-built matrices and independently declared rates. Removing, swapping, or misnormalizing `sigma_+` is physical. | closed |
| Detailed balance and equilibrium | Garner et al., Eqs. (10) and the text below Eq. (15), PDF p. 3; Arsenijevic and Bankovic, Eq. (17), PDF p. 5 | `n_bar=(exp(beta hbar omega)-1)^-1`; the equilibrium excited population is `n_bar/(1+2n_bar)`, and both generalized-amplitude-damping branches are present at finite temperature. | `gamma_up/gamma_down=n_bar/(n_bar+1)=exp(-beta hbar omega)`. The fixture may declare positive down/up rates directly, but if it also declares temperature they must satisfy this identity. | closed |
| Selective measurement update | Czajkowski and Grilo, Sec. 2.2, Eq. (1), PDF p. 5 | Outcome `x` has probability `Tr(Q_x rho)` and normalized post-measurement state `A_x rho A_x†/Tr(Q_x rho)`. | The dense worker must propagate unnormalized branch matrices and take their traces as branch probabilities; it must not renormalize before accumulating branch mass. | closed |
| Ordered joint law | Czajkowski and Grilo, Sec. 3.1, Eq. (9), PDF p. 7 | For projections `A` then `B`, the ordered probability is `Tr(A B A rho)` and the reversed order is generally different. | The `[X,Z,X,Z]` order is part of the neutral fixture and comparison identity. Reordering measurements is a valid corruption. | closed |
| Reset map | Garner et al., Sec. II.C, Eq. (22), PDF p. 5, and Sec. II.D, Eqs. (33)–(35), PDF pp. 7–8 | `R_|0>` and `R_|1>` are explicit channels that reset to the named stabilizer state. | The branch-local X reset is the CPTP map `R_0(tau)=|0><0| Tr(tau)` composed after the selective X instrument. Non-reset branches retain the selective state. | closed as an explicit design composition |
| Full-joint TV | Weissman et al., Sec. 1, Eq. (1), PDF p. 2; `docs/METRICS.md` | The source defines finite-alphabet L1 distance; the repository defines `TV=0.5 L1` over the joint support. | Joint TV and mechanism-directed marginal TV remain the registered standard statistics. | closed |
| Finite-sample radius | Weissman et al., Theorem 2.1, Eqs. (7)–(8), PDF p. 4, and proof Eqs. (14)–(16), PDF pp. 6–7 | For alphabet size `a`, an iid empirical law obeys an L1 tail bound with prefactor `2^a-2`; the proof is a union bound over nontrivial subsets. | The one-sample TV radius is `sqrt(log((2^a-2)/alpha_j)/(2n))`, capped at one. For two independent histograms, radii add by the triangle inequality. The comparison registry, not a literal denominator, supplies each Bonferroni `alpha_j`. | closed |

## Operation replay

### F2 generator

Let `n=diag(0,1)` and use the source dissipator convention. Oi and Schirmer Eq. (3b) gives

`Gamma_01 = 1/2 (|0|^2 + |sqrt(2 gamma_phi)|^2) = gamma_phi`.

Therefore `L_phi=sqrt(2 gamma_phi)n` leaves populations fixed and evolves the coherence as
`rho_01(t)=exp(-gamma_phi t)rho_01(0)`. The corruption `L_phi=sqrt(gamma_phi)n` gives
`exp(-gamma_phi t/2)` and is not gauge-equivalent to the target.

The independent cross-check is

`(gamma_phi/2)D[sigma_z] = 2 gamma_phi D[n] = D[sqrt(2 gamma_phi)n]`,

verified directly from the two dissipator definitions and the diagonal matrices.

### F3 generator

Let `sigma_-=|0><1|` and `sigma_+=|1><0|`. For positive `gamma` and `n_bar`, the sourced
thermal generator is

`gamma(n_bar+1)D[sigma_-] + gamma n_bar D[sigma_+]`.

The population equation is

`d rho_11/dt = -gamma(n_bar+1)rho_11 + gamma n_bar rho_00`,

so its stationary value is `rho_11=n_bar/(1+2n_bar)`. This makes the upward family observable:
starting from `|0>` no excitation is possible if `sigma_+` is absent, while the correct finite-temperature
fixture assigns positive excited-state mass. Swapping `sigma_+` and `sigma_-` reverses the directed
population flow and is not an unraveling gauge.

### Ordered measurement and reset

For each scheduled outcome `x`, the dense reference uses the unnormalized selective map
`M_x(tau)=P_x tau P_x`; its trace is the conditional branch mass. The next evolution consumes
`M_x(tau)` for non-reset measurements and `R_0(M_x(tau))=|0><0|Tr(M_x(tau))` for reset
measurements. Repeating this composition in schedule order produces the joint label law. The emitted
binary law is a deterministic marginal of the label law for the two-level fixtures.

### Statistical comparison

For a finite support of size `a`, Weissman Theorem 2.1 and `TV=L1/2` give

`Pr(TV(P_hat,P) >= r) <= (2^a-2) exp(-2 n r^2)`.

For comparison registry entry `j`, set `alpha_j=alpha_family/N_registry` and use the inverse radius.
For independent left/right samples, pass only if observed TV is no larger than the sum of their radii.
Deterministic dense-to-dense comparisons instead use the repository numerical threshold and do not
receive a sampling radius.

## Alternatives, invariants, and disconfirmation

- `sigma_z` and number-projector dephasing forms are equivalent only after their coefficients are
  transformed as above; identical parameter names do not make the raw collapse matrices identical.
- Collapse operators related by a common unit-modulus scalar produce the same dissipator. Such a
  change may exercise serialization but cannot falsify the physics.
- Generalized amplitude damping and the down/up Lindblad generator agree at channel level under the
  declared Markovian thermal assumptions. The fixture does not claim a microscopic bath calibration.
- Ordered X/Z measurement statistics are not replaceable by an unordered joint observable because the
  projectors do not generally commute on the evolving states.
- The Weissman bound assumes iid samples from a fixed finite-alphabet law. It does not authorize reuse
  across adaptively changed parameters or claim independence among marginal views built from the same
  shots; Bonferroni remains conservative under that dependence.

## Kill conditions

- Block F2 if the neutral fixture does not distinguish `sqrt(2 gamma_phi)n` from
  `sqrt(gamma_phi)n` on at least one registered observable.
- Block F3 if removing or swapping the upward collapse family survives all registered statistics.
- Block any temperature-labelled F3 fixture whose down/up ratio violates the declared detailed-balance
  identity, unless it is relabelled as independently driven rates rather than a thermal bath.
- Block the dense oracle if it imports or deserializes the compiled Carrier program, production operator
  builders, or production measurement/reset helpers.
- Block a comparison if its alpha allocation is not derived from the frozen registry cardinality.
- Block a claim that overall collapse sign or phase must change the result.
- Block any promotion from these two-qubit neutral fixtures to complete QEC Record faithfulness,
  finite-bond accuracy, calibrated hardware noise, or production readiness.

## Verdict

The source rows needed to preregister the F2 pure-dephasing and F3 finite-temperature fixtures are
closed. The closure is restricted to two-qubit Markovian neutral fixtures, ordered X/Z selective
measurement with an explicit reset channel, joint/marginal TV, and iid finite-sample comparison. It
does not close the finite-bond, full-QEC-Record, calibration, baseline-provenance, PEPS/FET, aggregate
acceptance, or release gates.

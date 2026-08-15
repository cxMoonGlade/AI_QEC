# Full-text review — Bergli, Galperin, Altshuler, “Decoherence in qubits due to low-frequency noise” (arXiv:0904.4597v1)

> **Provenance (2026-07-15): FULL-TEXT clean-room read.** Local PDF
> `outputs/reading_packages/simulator_background_top10_2026-07-14/sources/0904.4597v1.pdf`,
> SHA-256 `522d96cda526b04d036352551026be3b38f51635929ae761e54ecda25e0e495b`,
> 25 pages. The full extracted text was traversed; PDF pages 7, 10, and 13 were rendered and
> visually inspected for Eqs. (15), (34)–(35), and the independent-product statement before
> Eq. (39). This note contains paper facts and source-local gaps only. Application-specific
> inference is kept in a separate simulator claim packet.

## Metadata [paper]

- J. Bergli, Y. M. Galperin, and B. L. Altshuler.
- *New Journal of Physics* **11**, 025002 (2009), DOI
  `10.1088/1367-2630/11/2/025002`; arXiv:0904.4597v1, 29 April 2009.
- Review/theory article with exact classical two-state-fluctuator calculations.

## Executive summary [paper]

The paper treats qubit pure dephasing by classical two-state fluctuators. It fixes the symmetric
directional switching-rate convention, derives the exact single-fluctuator free-induction
coherence, and states that statistically independent fluctuator contributions multiply. It also
shows why a Gaussian approximation can fail for a strongly coupled fluctuator even at times longer
than its correlation time.

## Selection and coverage [ours]

Assigned rows: symmetric-RTN rate convention, exact free-induction characteristic function,
independent-product rule, and Gaussian failure regime. The paper does not supply a bridge from an
arbitrary endpoint sampler to a different driven, measured, or reset quantum process.

## Notation and source-location ledger [paper]

| symbol | domain and meaning | assumptions | source location |
|---|---|---|---|
| `chi(t)` | telegraph state in `{+1,-1}` | stationary symmetric process | Sec. 3.1, PDF p. 7 |
| `gamma_12`, `gamma_21` | directional transition rates | symmetric case sets both to `gamma` | Sec. 3.1, PDF pp. 6–7 |
| `C(t)` | `E[chi(t) chi(0)]` | symmetric RTN | Eq. (15), PDF p. 7 |
| `v` | magnitude of the longitudinal fluctuating field | pure dephasing/free induction | Secs. 2 and 3.2, PDF pp. 4, 9–10 |
| `phi` | phase accumulated from the longitudinal field | fixed initial phase, ensemble average | Eqs. (4), (29)–(34) |
| `m_+` | normalized transverse complex Bloch component | unbiased initial fluctuator for Eq. (35) | Eqs. (34)–(35), PDF p. 10 |
| `mu` | `sqrt(1-v^2/gamma^2)` | imaginary for `v>gamma` | Eq. (35), PDF p. 10 |

The paper's `gamma` is one directional jump rate. In the symmetric case the correlation decay rate
is `2 gamma`; silently treating `gamma` as the sum of both directional rates is a factor-of-two
error.

## Method and mechanism [paper]

For equal transition rates, the number of switches in time `t` is Poisson with mean `gamma t`.
Summing even and odd switch parities gives

```text
C(t) = E[chi(t) chi(0)] = exp(-2 gamma t).                    Eq. (15)
```

For a longitudinal field `v chi(t)`, the partial phase densities yield the telegraph equation.
After multiplying by `exp(i phi)` and integrating, the free-induction coherence satisfies

```text
L''(t) + 2 gamma L'(t) = -v^2 L(t),
L(0)=1, L'(0)=0.                                             Eq. (34)
```

Equation (35) is equivalently

```text
delta = sqrt(gamma^2-v^2)
L(t) = exp(-gamma t)
       [cosh(delta t) + (gamma/delta) sinh(delta t)].
```

For `v>gamma`, `delta=i omega` with `omega=sqrt(v^2-gamma^2)`, so

```text
L(t) = exp(-gamma t)
       [cos(omega t) + (gamma/omega) sin(omega t)].
```

At `v=gamma`, the continuous limit is `exp(-gamma t)(1+gamma t)`.

## Observable [paper]

The observable is the ensemble free-induction coherence `E[exp(i phi(t))]`, equivalently the
averaged normalized transverse Bloch component. PDF p. 13 explicitly says a single-qubit
decoherence experiment exposes this average, not the complete phase distribution of one noise
realization.

For statistically independent fluctuators, PDF p. 13 states

```text
L_total(t) = product_i L_i(t),
```

before introducing the logarithmic ensemble quantity in Eq. (39). The exact product applies to a
specified finite independent set; later Holtsmark and parameter-ensemble replacements are further
approximations and are not needed for that identity.

## Findings and failure regimes [paper]

- `v<gamma` is the weak-fluctuator regime; `v>gamma` is the strong regime.
- In the weak limit, the exact long-time decay approaches the Gaussian motional-narrowing rate.
- In the strong regime, the exact coherence is a damped oscillatory function. The Gaussian
  approximation misses the endpoint delta-function contribution to the phase distribution and can
  remain qualitatively wrong even for `t>1/gamma`.
- The same two-point correlation or power spectrum is therefore insufficient to determine
  non-Gaussian strong-fluctuator dephasing.

No numerical parameter used by a downstream implementation is measured or recommended by this
paper.

## Limitations and contrary evidence [paper]

The derivation assumes classical, stationary, symmetric, independent telegraph processes and
longitudinal pure dephasing. The paper separately treats echo protocols, parameter ensembles, and
microscopic fluctuator models, but does not derive an arbitrary control schedule, measurement/reset
instrument, leakage process, decoder, or record law. Its experimental review also says available
experiments were not conclusive about non-Gaussian behavior.

## Project kill conditions [ours]

Application is invalid if the implemented rate is not a directional rate, if fluctuators are not
independent, or if the observable is not the declared longitudinal free-induction coherence. A
matching endpoint autocorrelation alone does not establish an intra-step Hamiltonian or a bridge to
a different measured process.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| `gamma_12=gamma_21=gamma` | sum Poisson switch parity | symmetric stationary RTN | `C(t)=exp(-2 gamma t)` | Eq. (15), PDF p. 7 | matched |
| `v`, `gamma` | derive and solve the telegraph ODE | longitudinal free induction, unbiased initial state | exact `L(t)` | Eqs. (32)–(35), PDF pp. 9–10 | matched |
| independent phases | factor the joint characteristic function | statistical independence | `product_i L_i(t)` | text before Eq. (39), PDF p. 13 | matched |
| endpoint transition samples | infer an arbitrary intra-step quantum process | not supplied | process-specific dynamical map | no source location | missing |

## Relevance and trust [ours]

Use this paper only for the rate convention, exact single-RTN free-induction factor, finite
independent product, and their stated validity limits. Assigned rows have source-local status
`closed`; any bridge to a different production channel or record has source-local status `missing`.
No project-specific claim is stored in this literature note.

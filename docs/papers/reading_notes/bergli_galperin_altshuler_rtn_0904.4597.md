# Full-text review — Bergli, Galperin, Altshuler, “Decoherence in qubits due to low-frequency noise” (arXiv:0904.4597)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** arXiv v1 PDF downloaded from
> `https://arxiv.org/pdf/0904.4597`, SHA-256
> `522d96cda526b04d036352551026be3b38f51635929ae761e54ecda25e0e495b`, 25 pages; text
> extracted with `pdftotext -layout` for navigation. PDF pages 6, 9, and 12 were rendered and
> visually inspected for Eqs. (15), (35), and (39). Formula truth comes from the rendered PDF.

## Metadata [paper]

- J. Bergli, Y. M. Galperin, and B. L. Altshuler.
- *New Journal of Physics* **11**, 025002 (2009), DOI `10.1088/1367-2630/11/2/025002`;
  arXiv:0904.4597v1.
- Review/theory paper with exact single-fluctuator calculations.

## Executive summary [paper]

The paper models low-frequency noise using classical two-state fluctuators. For a symmetric random
telegraph process it fixes the rate convention, derives the exact non-Gaussian free-induction
coherence of one fluctuator, and shows how independent fluctuators combine multiplicatively. It
also explains why a Gaussian second-cumulant treatment fails when a fluctuator is strongly coupled.

## Selection + coverage [ours]

This is load-bearing for three rows in the finite-RTN audit: the per-direction switching-rate
convention, the exact one-RTN free-induction factor, and the product rule for independent RTNs. Wold
et al. (arXiv:1206.2174) independently restate the same formula using the total relaxation rate and
therefore serve as the convention cross-check. BLP and RHP, not this paper, ground the
non-Markovianity criteria.

## Notation + source-location ledger [paper]

| symbol | meaning and domain | assumptions | source location |
|---|---|---|---|
| `chi(t)` | telegraph state in `{+1,-1}` | stationary symmetric process | Sec. 2.3, PDF p. 6 |
| `gamma_12`, `gamma_21` | directional jump rates | symmetric case sets both to `gamma` | Sec. 2.3, PDF p. 6 |
| `C(t)` | `E[chi(t)chi(0)]` | symmetric RTN | Eq. (15), PDF p. 6 |
| `v` | longitudinal qubit–fluctuator coupling | pure free induction | Sec. 3.4, Eqs. (30)–(35), PDF pp. 9–10 |
| `mu` | `sqrt(1-v^2/gamma^2)` | imaginary when `v>gamma` | Eq. (35), PDF p. 9 |
| `<m_+(t)>` | normalized free-induction coherence | unbiased initial fluctuator | Eqs. (34)–(35), PDF p. 9 |

The paper's `gamma` is **not** the sum of two directional rates. It sets
`gamma_12=gamma_21=gamma`, so the total population relaxation rate is `2 gamma`.

## Method (deep) [paper]

For the symmetric process, the probability of `k` jumps in time `t` is Poisson with mean
`gamma t`. Alternating signs and summing the parity sectors gives

```text
C(t) = E[chi(t) chi(0)] = exp(-2 gamma t).                 (15)
```

For longitudinal free induction, the accumulated phase obeys `phi_dot=v chi(t)`. The probability
density for `phi` gives the exact ODE

```text
d^2<m_+>/dt^2 + 2 gamma d<m_+>/dt = -v^2 <m_+>,           (34)
<m_+>(0)=1,  d<m_+>/dt(0)=0.
```

Writing `delta=sqrt(gamma^2-v^2)`, Eq. (35) is equivalently

```text
L(t) = exp(-gamma t) [cosh(delta t) + (gamma/delta) sinh(delta t)].
```

For `v>gamma`, let `omega=sqrt(v^2-gamma^2)`; analytic continuation gives

```text
L(t) = exp(-gamma t) [cos(omega t) + (gamma/omega) sin(omega t)].
```

For statistically independent fluctuators, the accumulated phases add and their characteristic
functions factor:

```text
L_total(t) = product_i L_i(t),                            (39, preceding line)
K_m(t) = -sum_i log L_i(t).                              (39)
```

## The MECHANISM [paper]

Each fluctuator is a stationary symmetric continuous-time Markov chain. A jump in either direction
occurs with rate `gamma`; the qubit sees a longitudinal shift `+v` or `-v`. Strong coupling means
`v>gamma`, where the exact coherence is a damped oscillatory function rather than a Gaussian
monotone exponential.

## Mechanism mapping to QEC Twin [ours]

`RTNSource` uses the exact cycle-end transition probability
`p=(1-exp(-2 gamma_per_cycle))/2`, matching Eq. (15) at integer cycle boundaries. The
`OneOverFDriftSource` states are independent, so its declared latent process matches the product
premise. However, production code routes `z_radns` through `SourceCouplingConfig` into several
mechanism parameters; it does **not** directly declare the longitudinal Hamiltonian used above.
Treating `z_radns` as `v chi(t)` is therefore a separately named free-induction diagnostic lift, not
the production coupled QEC channel.

## The OBSERVABLE / metric [paper]

The paper's observable is the ensemble free-induction coherence `<m_+(t)>=E[exp(i phi(t))]` and,
for many independent fluctuators, its product. It is not syndrome-record TV/KL/NLL, a logical error
rate, or a process-tensor witness.

## Findings + numbers [paper]

- Weak `v << gamma`: Eq. (35) approaches the Gaussian motional-narrowing result.
- Strong `v > gamma`: the exact signal oscillates with angular frequency
  `sqrt(v^2-gamma^2)` under the envelope `exp(-gamma t)`.
- The Gaussian rate agrees only in the weak-coupling limit; the paper explicitly treats
  non-Gaussian effects as essential outside it.

No numerical parameter in `OneOverFDriftSource` is measured or recommended by this paper.

## Limitations [paper]

The derivation is free induction under longitudinal classical noise. It does not include QEC gates,
ancilla measurement/reset, leakage, source-to-mechanism fan-out, a decoder, or tensor-network
truncation. Independence is an assumption. Eq. (39) does not license replacing a production
instrument with the free-induction diagnostic.

## Contrary evidence and failure regimes [paper]

The Gaussian approximation is reliable only for weak individual couplings; matching the same
two-point covariance or PSD does not determine strong-RTN coherence. At `v=gamma` the displayed
`gamma/delta` form is evaluated by its limit `exp(-gamma t)(1+gamma t)`.

## Project kill conditions [ours]

Any claim that the Gaussian surrogate settles the finite-RTN diagnostic is killed if a default mode
has `v_i>gamma_i`. Any claim about the production QEC channel is killed unless the actual
source-to-channel mapping and ancilla instrument are included. A factor-of-two mismatch in the rate
convention also invalidates the transfer.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| `gamma_12=gamma_21=gamma` | sum jump parities | stationary symmetric RTN | `C(t)=exp(-2 gamma t)` | Eq. (15), PDF p. 6 | matched |
| `v, gamma` | solve Eq. (34) | unbiased initial state, longitudinal free induction | exact `L(t)` | Eq. (35), PDF p. 9 | matched |
| independent phases | factor characteristic function | statistical independence | `product_i L_i` | text before Eq. (39), PDF p. 12 | matched |
| project `z_radns` | identify it with longitudinal splitting | project diagnostic declaration, not paper | free-induction lift | no paper location | unsupported for production channel |

## Relevance to QEC Twin [ours]

Reuse the exact factor and product as a falsifier for the old Gaussian-surrogate conclusion. Do not
reuse the paper as evidence for the source defaults or as a bridge to a complete QEC record.

## How to use / trust + open questions [ours]

Full text and all load-bearing formula pages were visually checked. The paper closes the RTN
convention, single-factor, and independent-product rows. The source-to-production-channel and
channel-to-record rows remain missing.


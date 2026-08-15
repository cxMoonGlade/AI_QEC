# Full-text review — Wold, Brox, Galperin, Bergli, “Decoherence of a qubit due to a quantum fluctuator or to a classical telegraph noise” (arXiv:1206.2174)

> **Provenance (2026-07-13): FULL-TEXT read (精读).** arXiv v1 PDF downloaded from
> `https://arxiv.org/pdf/1206.2174`, SHA-256
> `53a3d7c7bde2a95decb8eb2f04d1e37e78bb4cbb619b9b4dd3b3c6cdfe1c6a72`, 7 pages; text
> extracted with `pdftotext -layout` for navigation. PDF pages 3 and 4 were rendered and visually
> inspected for Eqs. (9), (10), and (12).

## Metadata [paper]

- Henry J. Wold, Håkon Brox, Yuri M. Galperin, and Joakim Bergli.
- *Physical Review B* **86**, 205404 (2012), DOI `10.1103/PhysRevB.86.205404`;
  arXiv:1206.2174v1.
- Theory/numerical comparison of a damped quantum TLS with its classical-telegraph limit.

## Executive summary [paper]

The paper compares qubit decoherence from a quantum two-level fluctuator with classical random
telegraph noise. For the classical symmetric pure-dephasing limit it explicitly defines the total
relaxation rate as the sum of directional rates and restates the exact coherence formula. This makes
it an independent convention check on Bergli et al.'s per-direction `gamma` notation.

## Selection + coverage [ours]

This source closes the factor-of-two convention row and independently supports the exact
single-telegraph coherence formula. It does not establish the independent-product rule or the QEC
instrument bridge; Bergli et al. closes the former, while the latter remains missing.

## Notation + source-location ledger [paper]

| symbol | meaning and domain | assumptions | source location |
|---|---|---|---|
| `xi_+`, `xi_-` | classical fluctuator values with `xi_-=-xi_+` | symmetric amplitudes | Sec. III, PDF pp. 3–4 |
| `Gamma_-+`, `Gamma_+-` | directional transition rates | may be unequal | Sec. III, Eq. (9), PDF p. 3 |
| `Gamma` | `Gamma_-+ + Gamma_+-` | population relaxation rate | Eq. (10), PDF p. 4 |
| `D(t)` | qubit coherence decay factor | symmetric RTN, pure dephasing | Eq. (12), PDF p. 4 |
| `mu` | `sqrt(1-(2 xi/Gamma)^2)` | real in weak regime, imaginary in strong regime | Eq. (12), PDF p. 4 |

For symmetric switching `Gamma_-+=Gamma_+-=gamma`, hence `Gamma=2 gamma`. This is exactly the
conversion needed to compare Eq. (12) with Bergli et al. Eq. (35).

## Method (deep) [paper]

The classical fluctuator relaxes with

```text
Gamma = Gamma_-+ + Gamma_+-.                              (10)
```

For symmetric telegraph noise and pure dephasing,

```text
D(t) = exp(-Gamma t/2)/(2 mu)
       [(mu+1) exp(Gamma mu t/2) + (mu-1) exp(-Gamma mu t/2)],
mu = sqrt(1-(2 xi/Gamma)^2).                              (12)
```

Substituting `Gamma=2 gamma` and `xi=v` gives Bergli Eq. (35) term by term. For
`2 xi>Gamma`, analytic continuation produces the same damped oscillatory strong-RTN factor.

## The MECHANISM [paper]

The classical object is a two-state continuous-time Markov process with directional transition
rates. The paper obtains it as the overdamped classical limit of a quantum TLS, then compares the
qubit decoherence rates of the classical and quantum descriptions.

## Mechanism mapping to QEC Twin [ours]

The mapping `Gamma=2 gamma` verifies that `RTNSource.flip_probability` and the Bergli coherence
formula use compatible rate conventions. No part of this paper maps the repository's
`SourceCouplingConfig` fan-out to a longitudinal qubit Hamiltonian; that production bridge remains
unsupported.

## The OBSERVABLE / metric [paper]

`D(t)` in Eq. (12) is the qubit coherence-decay factor in the declared pure-dephasing model. The
paper also compares qubit–fluctuator mutual information, but neither quantity is a QEC syndrome
record metric or decoder LER.

## Findings + numbers [paper]

The relevant control parameter is coupling strength divided by fluctuator damping. The classical
approximation becomes accurate in the overdamped/weak-coupling regime studied by the authors. No
default value in the repository is measured or prescribed here.

## Limitations [paper]

Only a single fluctuator appears in Eq. (12). The paper does not prove a product formula for many
independent RTNs, analyze CP-divisibility, or include QEC gates and measurements. Its comparison
between quantum and classical TLS models cannot be promoted into a claim that either describes the
repository's physical hardware.

## Contrary evidence and failure regimes [paper]

The quantum TLS and classical telegraph descriptions can disagree when the qubit–TLS coupling is
not weak compared with TLS decoherence. Thus an RTN fit is not a universal substitute for a quantum
fluctuator model.

## Project kill conditions [ours]

If repository `gamma_per_cycle` were interpreted as the total rate `Gamma` rather than the
per-direction rate `gamma`, using it directly in Bergli Eq. (35) would be wrong by a factor of two.
The source code's endpoint autocorrelation `exp(-2 gamma lag)` and exact transition kernel rule out
that interpretation for the current class.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| directional rates | sum | classical two-state chain | `Gamma` | Eq. (10), PDF p. 4 | matched |
| symmetric rates | set each direction to `gamma` | high-temperature/symmetric RTN | `Gamma=2 gamma` | Eq. (9), PDF p. 3; Eq. (10), PDF p. 4 | matched |
| `Gamma, xi` | Eq. (12) substitution | pure dephasing | exact single-factor coherence | Eq. (12), PDF p. 4 | matched |
| project fan-out | infer production channel | not supplied | production reduced map | no paper location | unsupported |

## Relevance to QEC Twin [ours]

Use this paper as the second direct source for the rate conversion and exact single-factor formula.
Do not use it to claim that a classical RTN is a calibrated model of the Google hardware or that the
free-induction diagnostic equals the production QEC channel.

## How to use / trust + open questions [ours]

Full text and the equation page were visually checked. The convention and one-factor rows are
closed. Multi-RTN factorization is covered by Bergli et al.; production-channel and record bridges
remain missing.

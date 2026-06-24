# ADR 0004: Derivatives-Calibration Framing of the B Path — Ill-Posed Inverse Problem, Uncertainty Bands, and the B5 Deliverable

## Status

> ⚠ **RETIRED / EXPIRED (2026-06-22).** The quantitative-finance / derivatives-calibration
> *framing* adopted in this ADR is **retired as decorative** — an early-twin idea that carried
> no load-bearing method and no longer guides the project. The program's spine is now the
> **validated causal model** (the twin as a structural causal model; `do()` = Pearl
> intervention); see `CLAUDE.md` (Main line), `docs/TWIN.md`, and `docs/plan3.md`. This ADR is
> kept **unchanged** as a historical record: its still-valid *methodology* — calibration as an
> ill-posed inverse problem regularized toward a prior; observational ≠ interventional
> equivalence; counterfactuals never validated by fit alone; the bands / D1–D5 deliverable
> discipline — survives independently of the finance vocabulary.

Accepted (2026-06-05). Refines — does not overturn — ADR 0003's B5 deliverable.

## Context

ADR 0002 builds the counterfactual loop on a controlled toy first (B), and
ADR 0003 fixes the calibration objective (exact multi-context Born-rule
observation-NLL, not moment matching) and the deliverable (a
counterfactual-validity-vs-probe-richness curve plus negative controls).
B1–B4 are done: on the identifiable Pauli/Z-basis slice the label-free twin's
counterfactual `dLER` matches the controlled teacher to `~6e-9`. B5 — the
richness curve, the coherent slice, and the negative controls — is the open step.

The QEC label-free calibration problem `E ← syndrome stats` is **structurally the
derivatives-calibration inverse problem** `vol surface ← option prices`. This is
not a loose analogy; the two are the same ill-posed inverse problem, and the
quantitative-finance literature has 30 years of tooling for exactly the failure
modes B5 must measure. The mapping and its breakpoints are surveyed in
`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`; the load-bearing papers are cached in
`docs/papers/`. The binding facts imported:

- **Calibration is provably ill-posed** (Albani–Zubelli; Crépey). The fix is
  regularization toward a prior. So `CPTP-by-construction + locality +
  orbit-sharing` are not merely interpretability aids — they ARE the
  regularization operator that selects within the observational alias quotient.
- **Vanillas pin marginals, not dynamics.** Local-vol and stochastic-vol models
  reprice the same vanilla options yet give different forward-smile dynamics,
  hence different exotic prices and different hedge ratios `dV/dS` — the
  counterfactual. This is the finance instance of "observational equivalence ≠
  interventional equivalence," and it is exactly ADR 0003's Pauli-shadowing
  point: detector marginals + pairwise correlations (the QEC "vanillas") do not
  pin the coherent/non-Clifford structure the `ΔLER` knob depends on.
- **Model uncertainty has a coherent, computable measure** (Cont 2006; Avellaneda
  UVM / Black–Scholes–Barenblatt): the range of a quantity over the SET of models
  consistent with the calibration data. This is the rigorous, computable form of
  "alias-induced uncertainty bands on knob answers."
- **Counterfactuals are never validated by calibration fit alone** — finance
  validates hedges by P&L backtest, the realized counterfactual. This reinforces
  ADR 0002's "validate on controlled teacher" and bounds what C can ever claim.

## Decision

Adopt the derivatives-calibration framing and refine the B5 deliverable
accordingly. Five binding decisions:

**D1 — Regularization identity.** State and treat the physical priors (CPTP, locality,
known circuit) as the Tikhonov-style regularizer of an ill-posed inverse problem — they
shrink the variance/parameter space, **not** a genuine observational alias. The success
metric of any regularization-strength choice is out-of-sample (cross-context)
counterfactual validity, not in-sample fit. (The original orbit-sharing "A-vs-B
ablation" framing of this point — orbit-sharing as alias-shrinking — is **retired**:
probe richness, not parameter sharing, breaks the alias, ADR 0005.)

**D2 — B5 deliverable is "calibrate-on-`r ≤ k`, predict-held-out-`r`."** Replace
calibrate-and-evaluate-on-the-same-`r` with the finance calibrate-on-vanilla /
price-the-exotic protocol: calibrate the twin on contexts up to richness `k`,
then **predict** the held-out higher-`r` (coherent, phase-sensitive) observable
and the `do()`-`ΔLER`. The headline curve is prediction error vs calibration
richness `k`. This directly tests whether low-order probes extrapolate to the
high-order counterfactual — the precise place Pauli-shadowing is exposed.

**D3 — Report a band, not a point, and split the two uncertainties.** At each `r`,
characterize the calibration-consistent set `{E : NLL(E) ≤ NLL_min + slack}` and
report `[min, max] ΔLER` over it (Cont/UVM). The **band width vs `r`** is the
alias class shrinking under probe richness — the single most important plot.
Two uncertainties must be reported separately:

- *epistemic alias band* — range of `ΔLER` over the calibration-consistent CPTP
  set (the model set);
- *statistical estimation band* — spread of `ΔLER` under bootstrap resampling of
  the finite calibration shots (this is the `finite_sample` axis).

The UVM pointwise-extremize shortcut does NOT carry over: LER is not monotone in
the channel parameters (coherent interference + decoder non-monotonicity), so the
band must be extremized **numerically** over the CPTP-consistent set.

**D4 — Pre-register the negative-control failure mode.** The moment-matched
(DEM/Pauli) twin IS the local-volatility model. Pre-register the prediction:
it matches at low `r`, **fails specifically on the coherent slice** at high `r`,
AND gives a wrong `do()`-`ΔLER` even in regimes where its marginal fit is good.
A shuffled-channel twin must fail universally. Finance tells us in advance how
each control fails; B5 records whether it does.

**D5 — Identifiability gating before B5, with per-direction predictions.** Run the
two structural checks first and use them to predict the curve, not just observe
it: (a) the DEM anchor-feature condition (Moran) on the parity map `A`, listing
which mechanisms have ≥2 anchor bits; (b) the learnable-degrees-of-freedom ceiling
(arXiv:2601.22286) on `A`. Combined with the Girsanov decomposition — the
stochastic/Pauli part is the "quadratic variation" (identifiable from second-order
syndrome statistics), the coherent part is the "drift" (alias-invisible to
second-order, recoverable only with measure-distinguishing phase-sensitive probes)
— this yields a per-direction theoretical prediction for where `B_LER(r)` can and
cannot fall.

**Probe design (guidance, not gate).** Where a specific knob is the target, design
high-`r` probes as the *replicating portfolio* for the `do()`-relevant channel
subspace (the UVM static-hedging intuition: the right probe combination collapses
the band for that knob), rather than climbing richness blindly. Constrained by
what circuits are physically runnable — the probe ladder has a ceiling the option
market does not.

## Consequences

- B5's headline becomes two plots: prediction error vs calibration richness `k`
  (D2) and alias band width vs `r` (D3), with the estimation band (D3) overlaid.
  The earlier single `B_LER(r)` point curve is subsumed as the band's center.
- New compute: the band (D3) requires extremizing `ΔLER` over the
  calibration-consistent CPTP set at each `r` — a constrained optimization /
  sampling problem, heavier than the point recovery B4 already does.
- D5 is cheap and must run first; if a mechanism/direction is outside the
  learnable subspace or lacks anchors, a nonzero band there is expected, not a
  failure — the band is reporting honest non-identifiability, exactly ADR 0002's
  point.
- C (real Google data) inherits a hard boundary: there is no realized
  counterfactual on hardware, so calibration fit can never validate a knob there.
  The only available validation is cross-config transfer (d3→d5, X↔Z, set1→set2,
  72→105Q) = calibrate-on-liquid / test-on-illiquid, which finance flags as
  exactly where well-fitting models still fail. C must report cross-config
  counterfactual transfer error as headline and carry the controlled-system alias
  band (D3) forward as a prior on every Google knob answer.
- No claim boundary moves. This ADR changes how B5 is run and reported; it does
  not add a Google physical-mechanism, CPTP-learning, or counterfactual claim
  beyond the controlled small-scale loop.
- Falsification unchanged from ADR 0002: if the band (D3) does not shrink with `r`
  on the controlled teacher even with orbit-sharing (A), interventional validity
  is unrecoverable and that is a stop/redesign signal before any real-data work.

## References

Literature backing and per-paper relevance: `docs/papers/README.md`. Survey:
`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`. Prior decisions: ADR 0002 (build order),
ADR 0003 (B validation methodology). Object contract: `docs/TWIN.md`.

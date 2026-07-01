# Deep review — Gierjatowicz, Sabate-Vidales, Šiška, Szpruch & Žurič, Robust Pricing and Hedging via Neural SDEs

## Provenance

- **Source:** arXiv:2007.04154 (full PDF, open access), fetched 2026-06-30; also on SSRN (ID 3646241)
- **Reading method:** FULL-TEXT read (精读) of the arXiv PDF — Secs. 1-1.2 (model-uncertainty framing, neural-SDE definition, calibration, Girsanov change of measure) in full; later sections/experiments at result level
- **Status:** complete full-text close-read
- **Note:** This paper was NOT published in NeurIPS 2020 proceedings despite the filename convention. It is an arXiv + SSRN preprint only. The filename is a misnomer left for consistency.

> Deep reading note (academic-paper-review format; full read Secs. 1–1.2 incl. the model-
> uncertainty framing, the neural-SDE definition Eq. 1.1–1.2, the calibration objective, the
> Knightian-uncertainty price interval, and the P↔Q Girsanov change of measure Eq. 1.3;
> later sections/experiments at the result level). **Relevance to the twin** centerpiece —
> the closest finance analogue to the twin's intended shape, and the home of the Girsanov split.

## Metadata
- **Authors.** Patryk Gierjatowicz, Marc Sabate-Vidales, David Šiška, Lukasz Szpruch, Žan Žurič (Univ. Edinburgh; Vega Protocol; Alan Turing Institute; Imperial College London).
- **Venue / status.** arXiv:2007.04154 (Jul 2020).
- **Domain / type.** Mathematical finance / ML; **methods** (neural-SDE calibration + robust bounds) + numerical validation (local- & stochastic-vol).

## Executive summary
The paper calibrates a pricing model to liquid instruments **and quantifies model uncertainty** without committing to a hand-crafted parametric form, by making the model a **neural SDE**: keep the strong structural prior of an Itô SDE `dX_t^θ=b(t,X_t^θ,θ)dt+σ(t,X_t^θ,θ)dW_t` (Eq. 1.1) but let the **drift `b` and diffusion `σ` be overparametrized neural networks** — "let the data dictate the model *within* the SDE form." Splitting `X^θ=(S^θ,V^θ)` into traded assets `S` (a martingale ⇒ arbitrage-free) and non-traded `V` (Eq. 1.2), calibration solves `θ*=argmin Σ_i ℓ(E^{Q(θ)}[Φ_i], p(Φ_i))` — matching model prices to market prices of liquid derivatives `Φ_i`.

Because the model is **overparametrized**, *many* models are market-consistent (Knightian uncertainty): the set `M` of calibrated martingale measures. Rather than a fragile single price, the framework computes the **robust price interval `(inf_{Q∈M} E^Q[Ψ], sup_{Q∈M} E^Q[Ψ])`** for an exotic `Ψ`, via **martingale optimal transport** (whose dual yields the super/sub-hedging strategies); since an unconstrained `M` gives bounds too wide, more market data tightens them. Critically, the model extends **consistently to the real-world measure `P`** through a **Radon–Nikodym / Girsanov change of measure** `dP(θ)/dQ(θ)=exp(∫ζ dW + ½∫|ζ|²dt)` (Eq. 1.3) — adding a drift `ζ` (itself a network) — so that **a derivative price `Φ_i` and a real-world statistic `E^{P^market}[S_i]` are *the same kind of calibration target*** ("no distinction... bearing in mind that methodologically this leads to no loss of generality"). The neural SDE is explicitly framed as a **generative model** (GAN/VAE-adjacent) linked to causal optimal transport.

For the twin this is **the single closest finance analogue to its intended shape, and the home of the Girsanov split**: the neural-SDE drift/diffusion is the GKSL-generator / per-location CPTP channel parameterized by a (possibly amortized) network `f_ψ(c)`; the SDE structural prior is the CPTP-by-construction prior; "overparametrized ⇒ pool of consistent models ⇒ report an *interval*" is the alias band, here **constructed** (the `(inf,sup)` via martingale optimal transport is Cont's range *realized through a learned model* — the constructive D3 band); and **Eq. 1.3's `dP/dQ` Girsanov drift `ζ` is the third independent framing of the twin's `girsanov_split`** (alongside Kaufmann's off-diagonal PTM and Ivashkov's `t`-vs-`t²`), the change-of-measure the finance↔QEC isomorphism (ADR 0004) is built on.

## Contributions (claim → evidence → strength)
- **C1. Neural SDE: SDE form with NN drift/diffusion, calibrated by SGD (Eqs. 1.1–1.2).** *Evidence:* universal-approximation ⇒ `M^nsde(θ)` rich; martingale `S` ⇒ arbitrage-free. *Strength: strong.*
- **C2. Robust price/hedge interval over the calibrated set via martingale optimal transport.** `(inf,sup)E^Q[Ψ]`; dual ⇒ super/sub-hedges. *Strength: strong — the constructive uncertainty band.*
- **C3. Consistent P↔Q calibration via Girsanov (Eq. 1.3).** One framework for risk-neutral pricing + real-world stress-testing; price ≡ statistic as a target. *Strength: strong.*
- **C4. Efficient training + interval algorithms; local- & stochastic-vol validation.** *Strength: moderate-strong.*

## Method (deep)
- **Model.** `dX^θ=b dt+σ dW`, `b,σ` NNs (App. C); `X=(S,V)`, `dS=rS dt+σ^S dW` (martingale after discounting), `dV=b^V dt+σ^V dW`; `σ^S,σ^V` encode traded↔non-traded correlation.
- **Calibration (Q).** `θ*=argmin Σ_i ℓ(E^{Q(θ)}[Φ_i],p(Φ_i))`; `E^{Q(θ)}[Φ]=∫Φ(ω)L(X^θ)(dω)` (differentiable Monte-Carlo over SDE paths). Weight-clipping ⇒ existence/uniqueness (Krylov).
- **Robust bounds.** `M` = perfectly-calibrated measures; `(inf_{Q∈M},sup_{Q∈M})E^Q[Ψ]` via martingale optimal transport; dual = super/sub-hedging (Beiglböck); tighten with more instruments.
- **P↔Q.** `dP(θ)/dQ(θ)=exp(∫ζ dW+½∫|ζ|²dt)` (Eq. 1.3, Girsanov); `ζ` a network; match real-world stats (autocorrelation, realised variance, MGF). `E^{P(θ)}[S_i]=E^{Q(θ)}[S_i·dP/dQ]` ⇒ prices and statistics are one target class.

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | SDE prior keeps arbitrage-freeness; robust bounds rest on established MOT duality; Girsanov extension rigorous. |
| Novelty | **4** | Combines neural calibration + model *selection/uncertainty* (not just fitting a fixed model) — the interval-estimator focus is the distinctive step. |
| Reproducibility | **4** | Model + objectives + algorithms specified; reference repo (`robust_nsde`); numerical experiments. |
| Experimental design | **4** | Local- and stochastic-vol validation; robust bounds demonstrated; sampled (Monte-Carlo) forward. |
| Statistical rigor | **4** | Calibration + interval estimation; the bounds' tightness depends on the instrument set (acknowledged). |
| Scalability | **4** | Neural SDE + SGD scales; the forward is sampled (variance), not exact. |

## Strengths
- **S1 — strong prior on *form*, data picks the parameters (neural SDE).** Keeping the SDE structure (arbitrage-freeness, interpretable dynamics) while letting NNs fill the drift/diffusion is exactly the "structural prior + flexible parameterization" stance — neither black-box nor hand-crafted.
- **S2 — uncertainty as a *constructed* interval (C2).** Reporting `(inf,sup)E^Q[Ψ]` over the calibrated set — with super/sub-hedges from the dual — turns model uncertainty into an actionable, computable band, not just a warning.
- **S3 — P↔Q unification via Girsanov (Eq. 1.3).** One consistent model for pricing (Q) and real-world stress-testing (P), with prices and statistics as the same target class, is conceptually clean and operationally powerful.

## Weaknesses / limitations
- **W1 — sampled (Monte-Carlo) forward; overparametrized.** The differentiable forward is path-sampled (variance, cost); individual NN parameters carry no meaning (interpretability via the interval, not the weights).
- **W2 — bound tightness depends on the instrument set.** Unconstrained `M` ⇒ bounds too wide; the band is only as tight as the calibrating instruments (a data-richness statement).
- **W3 — calibration/robustness, not counterfactual validation.** Robust bounds are over *market-consistent* models; like all calibration, they do not certify an out-of-sample interventional truth without further structure.

## Relevance to the twin
This is **the constructive template for the twin's entire shape, and the finance home of the Girsanov split**:
1. **Neural-SDE = the (amortized) per-location CPTP channel; SDE prior = CPTP-by-construction.** Drift/diffusion-as-NNs is the GKSL generator parameterized by a network `f_ψ(c)`; the arbitrage-free SDE prior is the twin's CPTP/locality prior. "Strong prior on model *form*, data picks the parameters" is *verbatim* the twin's stance — this paper is its finance instantiation.
2. **Calibrate-to-instruments via a differentiable forward = the twin's exact-NLL calibration.** `θ*=argmin ℓ(E^{Q(θ)}[Φ_i],p(Φ_i))` is the twin's exact Born-rule NLL calibration to syndrome statistics; theirs is a *sampled* SDE forward, the twin's is the *exact enumerated density-matrix* forward (exact at small `d` — a strict advantage at the toy scale; their sampling is the scaling path).
3. **`(inf,sup)E^Q[Ψ]` = the constructive alias band; MOT = a band algorithm.** "Overparametrized ⇒ pool of consistent models ⇒ report an interval" is the twin's alias band over the calibration-consistent CPTP set. Their `(inf,sup)` is **Cont's `μ_Q` range realized through a learned model** — and the **martingale-optimal-transport dual (super/sub-hedging)** is a concrete *algorithm* for computing it. The twin's Tier-0/1 band is the *local* (closed-form/TRS-at-optimum) version; **training to the inf/sup objective is the global, constructive harden-stage band** — the natural amortized-stage upgrade. (This is the same uncertainty object as Nasr's worst-case counterfactual error and Heinze-Deml's effect bands — four notes, one band.)
4. **Eq. 1.3's `dP/dQ` Girsanov drift = the THIRD framing of `girsanov_split`, and the isomorphism's home.** The Radon–Nikodym `dP/dQ=exp(∫ζ dW+½∫|ζ|²dt)` *is* the change of measure that adds a coherent drift `ζ` — exactly the twin's coherent layer as a Girsanov drift over the stochastic (Pauli/quadratic-variation) base. Together with Kaufmann (off-diagonal PTM) and Ivashkov (`t` vs `t²`), the split now has **three independent derivations across three fields** — and *this* one is the literal content of the **finance↔QEC calibration isomorphism (ADR 0004)**: the finance Girsanov change-of-measure is the structure the twin's coherent recovery mirrors.
5. **"Price ≡ statistic" = the twin's "syndrome statistic ≡ ΔLER target."** Their methodological collapse of derivative prices and real-world statistics into one target class is the twin's stance that a syndrome marginal and a `do()`-ΔLER are both just functionals of the calibrated channel — and the P↔Q consistency is keeping the *generative* (teacher, P) and *decoder-facing* (Q) uses coherent. The amortized context map `f_ψ(c)` is the piece the twin has **deferred** (no scalability carrier, ADR 0005/0006); this paper is the **template for if/when it is built**.

## How to use / trust + open questions
- **Trust:** very high as the *constructive template* for the twin's shape and the *finance home of the Girsanov split / ADR-0004 isomorphism*; carry W1 (sampled forward — the twin's exact forward is better at small `d`) and W3 (calibration-robustness, not counterfactual).
- **Open questions for the project:** (i) Implement the twin's **`(inf,sup)`-over-the-calibrated-CPTP-set** band by training to an inf/sup ΔLER objective (the constructive harden-stage band) and compare to the local Tier-0/1 band — global-trained vs local-exact. (ii) Make the **Eq. 1.3 Girsanov `ζ` ↔ the twin's coherent drift** correspondence explicit in the ADR-0004 isomorphism doc, citing all three derivations (this paper, Kaufmann, Ivashkov). (iii) Use the **MOT-dual super/sub-hedge** as the conceptual model for "what bounds the worst-case ΔLER" (the hedge = the conservative decoder action). (iv) Treat this as the **`f_ψ(c)` amortization template** for the deferred scalable carrier — the explicit blueprint when the >50-qubit path is built.

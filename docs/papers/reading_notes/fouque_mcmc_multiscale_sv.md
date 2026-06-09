# Deep review — Molina, Han & Fouque, McMC Estimation of Multiscale Stochastic Volatility Models

> Deep reading note (academic-paper-review format; full read Secs. 1–2.2 incl. the
> exp-of-sum-of-OU model Eq. 2.1, the well-separated-timescale ordering, the Euler
> discretization, and the Bayesian/MCMC identifiability framing; Secs. 3–4 (simulation +
> FX) at the result level). **Relevance to the twin** centerpiece — the C-stage drift template.

## Metadata
- **Authors.** German Molina (SAMSI, NC); Chuan-Hsiang Han (National Tsing-Hua, Taiwan); Jean-Pierre Fouque (UC Santa Barbara).
- **Venue / status.** ≈2010 (working paper / proceedings).
- **Domain / type.** Mathematical finance / Bayesian econometrics; **methods** (MCMC estimator) + simulation + FX application.

## Executive summary
The paper estimates **stochastic-volatility (SV) models whose volatility is driven by several latent factors at well-separated time scales** — a *fast* mean-reverting factor + a *slow* one — from a **single univariate series**, the originality being the **identification of two factors at well-separated scales driving one series**. The model (Eq. 2.1): `dS_t=κS_t dt+σ_t S_t dW^{(0)}`, with **`log(σ_t²)=Σ_{j=1}^K F_t^{(j)}`** (log-variance = a *sum* of `K` Ornstein–Uhlenbeck factors), each `dF_t^{(j)}=α_j(μ_j−F_t^{(j)})dt+β_j dW^{(j)}` — `μ_j` long-run mean, `α_j` mean-reversion rate (time scale `1/α_j`), `β_j` "vol-of-vol." The scales are **well-separated and ordered** (`0<α_1<α_2` ⇒ factor 1 = slowest, factor 2 = fastest), with long-run variances `β_j²/2α_j` of the same order. After Euler discretization (Sec. 2.2: returns `y_{t_k}`, driving vols `h_{t_k}=F_{t_k}−μ`, AR coefficients `φ_j=1−α_jΔ`), the parameters **and the latent factor paths** are estimated by **Markov-Chain Monte Carlo (Bayesian)**, with priors regularizing the otherwise weakly-identified two-factor decomposition; model selection is handled informally via MCMC diagnostics (not Bayes factors / RJMCMC). The key finding: the **two-timescale factorization is recoverable by MCMC where method-of-moments struggled**, and **identifying the fast factor is what makes the slow factor's estimation accurate** (the factors are coupled in estimation). Two well-separated factors fit fat tails / long memory better than one; validated on simulated + FX data.

For the twin this is the **template for the `predict`/drift capability at the C (real-data) stage**: Google's `d3d5` "last 16 experiments run sequentially over 15 h" is exactly a **two-timescale** signal — a **slow** calibration drift across the window + **fast** per-shot statistical (shot-noise) fluctuation — and the **exp-of-sum-of-OU** structure maps onto the twin's channel-field parameters drifting slowly while fluctuating fast. The MCMC-over-latent-paths is the natural **drift-tracking/forecasting** carrier; and the paper's identifiability coupling (fast-factor identification required for slow-factor accuracy) is the finance statement of the twin's "**couple the two bands**" rule — the D3b shot-noise band (fast) and the slow drift must be **jointly** estimated, not separated post-hoc.

## Contributions (claim → evidence → strength)
- **C1. Two-timescale SV model: `log σ²` = sum of fast + slow OU factors (Eq. 2.1).** *Strength: strong (the structural object).* 
- **C2. MCMC/Bayesian estimation of parameters *and latent paths*, exploiting scale separation (Sec. 2).** Priors regularize the weakly-identified decomposition. *Strength: strong.*
- **C3. Recovery where method-of-moments fails; fast-factor ID enables slow-factor accuracy (Sec. 3).** *Strength: strong — the identifiability-coupling result.*
- **C4. FX application; two factors fit fat tails/long memory better than one (Sec. 4).** *Strength: moderate-strong.*

## Method (deep)
- **Model.** `dS=κS dt+σS dW^{(0)}`; `log σ²=Σ_j F^{(j)}`; `dF^{(j)}=α_j(μ_j−F^{(j)})dt+β_j dW^{(j)}`; scales `1/α_j` well-separated, ordered; `W` possibly correlated (FX: `ε⊥v`, `v`'s correlated, leverage rare).
- **Discretization.** Euler at `t_k=kΔ`; `y_{t_k}=(1/√Δ)(ΔS/S−κΔ)=σ_{t_k}ε_{t_k}`; `F^{(j)}_{t_k}−μ_j=φ_j(F^{(j)}_{t_{k-1}}−μ_j)+β_j√Δ v_{t_k}`, `φ_j=1−α_jΔ`.
- **Estimation.** MCMC (Gibbs/Metropolis) over `{α_j,μ_j,β_j}` and the latent `{F^{(j)}_{t_k}}`; priors on the parameters; scale separation + priors break the factor-decomposition weak-identifiability; diagnostics for `K=1` vs `K=2`.

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **4** | OU/SV model standard; MCMC estimation principled; identifiability handled via priors + scale separation (acknowledged weak ID). |
| Novelty | **4** | Identifying *two well-separated factors from a univariate series* via Bayesian MCMC is the distinctive step (vs method-of-moments). |
| Reproducibility | **3** | Model + discretization explicit; MCMC sampler details partly implicit; FX data application. |
| Experimental design | **4** | Simulation (recover known two-factor params) + real FX; `K=1` vs `K=2` comparison. |
| Statistical rigor | **4** | Bayesian posterior over params + paths; model selection only informal (diagnostics, not Bayes factors). |
| Scalability | **3** | Univariate single-series estimator; MCMC over latent paths is the cost. |

## Strengths
- **S1 — two well-separated scales from one series (Eq. 2.1).** Decomposing a single observed series into a slow + fast latent factor is exactly the structure of real drift-plus-noise data, and the well-separation is what makes it identifiable.
- **S2 — MCMC recovers what moments cannot, with priors as the regularizer.** Bayesian estimation of the weakly-identified decomposition (priors breaking the degeneracy) is the right tool, and outperforms method-of-moments.
- **S3 — the identifiability coupling (fast enables slow).** The finding that you must identify the fast factor to estimate the slow one accurately is a precise, transferable statement about *jointly* (not sequentially) estimating coupled scales.

## Weaknesses / limitations
- **W1 — univariate, single-series, low-dimensional.** The estimator is for one scalar series with `K≤2` factors; a high-dimensional state needs a different sampler.
- **W2 — weak identifiability; priors do heavy lifting.** The two-factor decomposition is weakly identified; the posterior depends on the priors (a regularization, not free information — cf. Albani/Cont).
- **W3 — model selection only informal.** `K=1` vs `K=2` is decided by MCMC diagnostics, not a principled Bayes-factor / RJMCMC procedure — a gap for "how many drift scales does the data have?"

## Relevance to the twin
This is the **`predict`/drift-axis template for the C (real-data) stage** — and the only paper in the set about *temporal* model estimation:
1. **Google's 15 h sequential `d3d5` data IS a two-timescale signal.** "The last 16 experiments run sequentially over 15 h" = a **slow** calibration drift across the window + **fast** per-shot statistical (shot-noise) fluctuation. The **exp-of-sum-of-OU** model (Eq. 2.1) maps directly: the twin's channel-field parameters (a coherent angle, an error rate) are the "log-variance" `log σ²` — a slow OU drift factor (the 15 h calibration wander) plus a fast factor (the per-shot noise). This gives the twin a *concrete generative model* for the drift it will face at C.
2. **MCMC-over-latent-paths = the drift-tracking/forecasting carrier (the `predict` capability).** Estimating the latent factor *paths* (not just parameters) is exactly what `predict` needs — forecast the slow component *before* it is fully observed, rather than fitting it post-hoc. This connects to the sequential-Monte-Carlo drift methods and is the natural home for the twin's drift forecaster.
3. **The identifiability coupling = the twin's "couple the two bands" rule.** The paper's result that **identifying the fast factor is required for accurate slow-factor estimation** is the finance statement of the B-hardening guidance ("couple the two bands via slack"): the twin's **D3b shot-noise band (fast)** and the **slow drift** must be estimated **jointly**, not separated post-hoc — fit the fast shot-noise wrong and the slow-drift estimate is biased. This is a specific, actionable modeling constraint for the `predict` axis.
4. **Priors regularize the weakly-identified decomposition (Cont/Albani again).** As in the finance-calibration notes, the two-factor decomposition is weakly identified and the *priors* break the degeneracy (W2) — adding no observational information, only *selecting* within the consistent set. The twin's CPTP/locality/smooth-drift priors play this role for the drift decomposition; the slow/fast separation is what the *data's timescale structure* provides.
5. **Strictly C-stage; what to *log and build*, not a B-path dependency.** The controlled B toy has no drift, so this is filed as the `predict`-axis template. The immediately actionable consequence: **log timestamped calibration windows** in any real-data ingestion so the slow component is recoverable, and treat the shot-noise (D3b) and the slow drift as the two separated, *coupled* scales. The exact univariate estimator does not transfer (the twin's state is a high-dimensional channel field) — the **two-timescale + jointly-estimated-coupled-scales principle** does.

## How to use / trust + open questions
- **Trust:** high as the *drift-axis modeling template* and the *coupled-scales identifiability lesson*; carry W1 (univariate — re-derive the sampler for the channel field) and W3 (no principled factor-count selection).
- **Open questions for the project:** (i) Model the twin's real-data channel parameters as an **exp-of-sum-of-(slow+fast)-factors** and fit by MCMC/SMC over latent paths — the concrete `predict` forecaster. (ii) Enforce **joint (coupled) estimation of the D3b shot-noise band and the slow drift** (the paper's fast-enables-slow lesson; the "couple the two bands" rule). (iii) **Log timestamped calibration windows** now, so the slow component is recoverable at C. (iv) Decide the **number of drift scales** in the Google data with a principled criterion (the paper's W3 gap) before committing to `K=2`.

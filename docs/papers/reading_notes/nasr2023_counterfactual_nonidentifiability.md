# Deep review — Nasr-Esfahany & Kıcıman, Counterfactual (Non-)identifiability of Learned Structural Causal Models

> Deep reading note (academic-paper-review format; full read Secs. 1–5 incl. the SCM/DSCM
> setup, the abduction-action-prediction procedure, the motivating counter-example Eqs. 1–2,
> and the identifiability/impossibility statements; Sec. 6 ambiguity method at the result level).
> **Relevance to the twin** centerpiece — this is the formal core of the project's central risk.

## Metadata
- **Authors.** Arash Nasr-Esfahany (MIT), Emre Kıcıman (Microsoft Research).
- **Venue / status.** arXiv:2301.09031 (Jan 2023).
- **Domain / type.** Causal inference / identifiability; **theoretical** (a positive theorem + an impossibility result) + a practical ambiguity-measurement method.

## Executive summary
The paper asks whether **counterfactuals** computed from a **Deep Structural Causal Model (DSCM)** — generation functions learned from *observational* data by fitting deep conditional generative models (NF/VAE/GAN, à la Pawlowski; Khemakhem's iVAE is cited as exactly this NF-for-SCM line) — can be trusted. An SCM `M=(U exogenous, V endogenous, f)` with `V_i=f_i(U_i,PA_i)`, Markovian (no hidden confounders); counterfactuals follow Pearl's three steps: **abduction** (infer the exogenous posterior `p_U(·|x)` from evidence), **action** (apply `do(X:=x')` with that posterior), **prediction** (read off `p_V(·|x)` in the modified SCM).

The result is an **impossibility**, made unforgettable by a one-line counter-example (Sec. 4, Eqs. 1–2):
> `T~Bern(0.5)`, `U~Unif(0,1)`. **Mechanism 1:** `Y¹=U` if `T=1`, `U−1` if `T=0`. **Mechanism 2:** `Y²=U` if `T=1`, `−U` if `T=0`. They have **identical observational distributions** `p_{Y|T}(y|t)` — so both are equally valid fits — **yet give different counterfactuals**: "had we done `t'=1`, given `Y=y` at `T=0`" yields `p_{Y¹}=δ(1+y)` vs `p_{Y²}=δ(−y)`.

Formally: counterfactuals **are** point-identified for **monotonic mechanisms with single-dimensional exogenous noise** (Thm. — the positive case), but for **general mechanisms with multi-dimensional exogenous noise** they are **NOT identified from observational data — even with known causal structure and no hidden confounding** (the impossibility, via the general counter-example). Parametric/functional-form assumptions are *unavoidable* to pin them. Since enumerating identifiability per assumption-set is cumbersome and *exact* identifiability may be too strong, Sec. 6 instead gives a **computational method to measure the counterfactual ambiguity (worst-case error)** of a learned DSCM — a go/no-go metric. Evaluation: negligible bounds for an identifiable SCM, informative error bounds for a non-identifiable synthetic one.

For the twin this is **the formal statement of the project's central risk** — observational adequacy ≠ interventional/counterfactual validity. The Y¹/Y² pair is the *exact template* of the twin's "`calib_kl≈0` at every probe richness, yet `do()`-ΔLER wrong" (the exotic error staying 0.57 while calibration is fit to `1e-8`): two channels with the same syndrome distribution and different `do()`-ΔLER. The non-identifiability lives in the **abduction step** (the exogenous posterior — the twin's coherent phase — is under-determined by the observational marginal); the positive theorem (monotonic + single-dim) is the identifiability the twin's **probe richness** must earn; and Sec. 6's worst-case error **is** the twin's alias band on ΔLER (Cont/UVM).

## Contributions (claim → evidence → strength)
- **C1. Positive: counterfactual identifiability for monotonic, single-dim-exogenous mechanisms (Thm. 1).** *Evidence:* constructive (the inverse exists). *Strength: strong — the boundary of the possible.*
- **C2. Impossibility: general multi-dim-exogenous mechanisms are counterfactually non-identified from observational data, even with known structure + no confounding (Sec. 5).** *Evidence:* the Y¹/Y² counter-example (Eqs. 1–2) + its generalization. *Strength: strong — the headline.*
- **C3. A computational worst-case-counterfactual-error (ambiguity) metric (Sec. 6).** *Evidence:* negligible bounds on an identifiable SCM, informative bounds on a non-identifiable one. *Strength: strong — turns the impossibility into a usable quantity.*

## Method (deep)
- **DSCM counterfactual.** Learn `f̂_θ(·,T)` per node from `p_{Y|T}`; abduction needs `p_{U|PA,V}(·|pa,y)` (the tractable-posterior requirement). The fit objective is *observational* (`p_{Y|T}`), which is precisely why the counterfactual (a function of the abduced posterior) is unconstrained off the observed distribution.
- **Why it fails.** Multiple `(f,p_U)` give the same `p_{Y|T}` but different abduction posteriors → different counterfactuals. Monotonic + single-dim `U` ⇒ the mechanism is invertible in `U` given `(T,Y)` ⇒ the posterior is a point mass ⇒ identifiable. Multi-dim/non-monotone ⇒ the posterior is a *set*, and the counterfactual depends on which element.
- **Ambiguity metric (Sec. 6).** Search over DSCMs consistent with the observational distribution (and the assumption set) for the spread in the counterfactual answer → worst-case error; large spread ⇒ DSCM not viable for that query/setting.

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | The counter-example is airtight; the monotonic/single-dim positive case is correct; the framing (known structure, no confounding) isolates the *functional-form* source of non-identifiability. |
| Novelty | **5** | Sharpens "counterfactuals need assumptions" into a precise DSCM impossibility + a measurable ambiguity metric — directly relevant to the deep-generative-causal wave. |
| Reproducibility | **4** | Counter-example fully explicit; the ambiguity method described; synthetic + adopted SCMs. |
| Experimental design | **4** | Identifiable + non-identifiable SCMs; the point is the theory, the experiments confirm the metric. |
| Statistical rigor | **4** | Worst-case bounds; the guarantees are about identifiability, not sampling. |
| Scalability | **3** | The ambiguity search is a computational object; scaling to high-dim DSCMs is not the focus. |

## Strengths
- **S1 — the Y¹/Y² counter-example (Eqs. 1–2).** Two mechanisms, *identical observational distribution*, *different counterfactual* — the cleanest possible proof that fitting the data distribution cannot certify a counterfactual. It is the whole argument in two lines.
- **S2 — isolates the source: functional form, not confounding.** By assuming known structure and no hidden confounders, the paper shows the non-identifiability is *intrinsic to the mechanism's exogenous dimensionality* — not fixable by more structure knowledge, only by parametric assumptions.
- **S3 — the ambiguity metric (Sec. 6).** Rather than demand exact identifiability, measuring the *worst-case counterfactual error* under the assumption set is the pragmatic, honest move — a go/no-go that a practitioner can actually compute.

## Weaknesses / limitations
- **W1 — Markovian, known-structure setting.** No hidden confounding and known DAG; real settings add those (the twin's controlled teacher, however, *also* removes confounding — so this is the matched setting, not a gap).
- **W2 — the ambiguity search is assumption-set-specific and can be expensive.** Measuring worst-case error requires searching the consistent-DSCM set; the bound is only as good as the assumption set and the search.
- **W3 — no domain-specific exploitation of interventional data.** It studies observational-only identifiability; settings *with* interventional access (the twin's `do()` on a teacher) can do strictly better — which is the twin's structural advantage, not the paper's concern.

## Relevance to the twin
This is **the theorem the entire B-first build order is organized around** — and the deep read makes the mapping exact:
1. **The Y¹/Y² counter-example IS the twin's central failure mode, and its moment-matched control is literally a Y².** The twin can fit syndrome distributions perfectly (`calib_kl≈0` at every probe richness) and still give the wrong `do()`-ΔLER — the measured "exotic error stays 0.57 while calibration is fit to `1e-8`." Nasr proves this is **generic, not a bug**. More: the twin's **moment-matched / Pauli-shadow negative control is a constructed `Y²` to the teacher's `Y¹`** — same observation, different counterfactual ΔLER — so the project's ~900×/1400× control failures are the *quantitative instance* of this impossibility. This paper is the citation for why those controls are *expected* to fail, not a modeling error.
2. **The non-identifiability lives in the abduction step = the coherent phase.** Abduction (infer the exogenous posterior `p_U(·|x)`) is the twin's `recover` of the latent coherent direction from the syndrome marginal; the impossibility says that posterior is a *set* (multi-dim `U`) unless the mechanism is monotonic/single-dim. The twin's "out-of-basis coherent error stays aliased until phase-sensitive probes enter" is exactly a multi-dim-exogenous abduction that probe richness collapses toward the single-dim (identifiable) case.
3. **Therefore counterfactual validity cannot come from calibration fit — only a controlled teacher certifies it (ADR 0002).** The B-first build order (validate `do()`-ΔLER against a teacher whose true mechanism is known) is the *operational response* to this theorem; the finance analogue is the P&L backtest, not the calibration residual. And the twin has an **advantage Nasr's setting lacks**: the controlled teacher supplies *ground-truth counterfactuals* at small scale, so the impossibility is **measurable** (certified on the toy), not only feared — the boundary it sets binds on real data (C), where no teacher exists.
4. **Sec. 6 worst-case counterfactual error = the twin's alias band on ΔLER (Cont/UVM).** When point identification fails, *report the bound*. Nasr's ambiguity metric and Cont's `μ_Q` model-uncertainty range and the twin's Tier-0 band are the **same object** viewed from causal-ID, finance, and QEC. The twin's CPTP/locality priors are the "parametric assumptions" Nasr says are *required* to narrow it — and (per the Albani note) they only *select* within the consistent set; they add no observational information.
5. **The positive theorem scopes what probe richness must achieve.** Monotonic + single-dim exogenous ⇒ identifiable. The twin's identifiability target (via `C_cal(r)`, the iVAE `L`-rank condition, the Ivashkov short-time resolution) is to drive the channel's effective abduction toward this single-dim/invertible regime — three literatures (causal-ID, nonlinear-ICA, open-system learning) naming the *same* sufficient condition.

## How to use / trust + open questions
- **Trust:** very high as the *formal justification* of the central risk and the B-first build order; its setting (Markovian, known structure, no confounding) is the *matched* controlled-teacher setting, so it transfers cleanly.
- **Open questions for the project:** (i) Construct the twin's explicit **Y¹/Y² pair** — two channels with provably identical syndrome distributions and different `do()`-ΔLER — as a *certificate* of the alias (the moment-matched control, stated as a Nasr counter-example). (ii) Compute the twin's **ambiguity metric** (worst-case ΔLER over the calibration-consistent channel set) and confirm it equals the Tier-0 band — unifying the three uncertainty objects. (iii) State the twin's **single-dim/monotonic analogue**: which probe-richness level makes the coherent abduction point-identified (cross-referencing iVAE condition (iv) and Ivashkov Result 3). (iv) Emphasize the twin's structural advantage (ground-truth counterfactuals from the teacher) as what lets it *certify* what Nasr can only *bound*.

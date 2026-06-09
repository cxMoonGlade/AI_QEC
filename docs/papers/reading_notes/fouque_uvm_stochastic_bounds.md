# Deep review — Fouque & Ning, Uncertain Volatility Models with Stochastic Bounds

> Deep reading note (academic-paper-review format; full read Secs. 1–2 incl. the BSB
> derivation, the convergence theorem, and the bang-bang/zero-set structure; Secs. 3–4
> proof + numerics at the result level). **Relevance to the twin** centerpiece.

## Metadata
- **Authors.** Jean-Pierre Fouque, Ning Ning (UC Santa Barbara).
- **Venue / status.** SIAM J. Financial Mathematics (≈2018); arXiv preprint.
- **Domain / type.** Quantitative finance / stochastic control; **theoretical** (asymptotic analysis + PDE).

## Executive summary
The paper computes the **worst-case (super-replicating) option price under an uncertain volatility band**, generalizing the band from constant to **slowly-varying stochastic bounds**. The worst-case price `P^δ(t,x,z)=e^{-r(T-t)}ess sup_{q∈[d,u]}E[h(X^δ_T)]` (Eq. 9) is the viscosity solution of a **Black–Scholes–Barenblatt (BSB) nonlinear PDE** (Eq. 11) whose inner supremum is **bang-bang on the sign of the gamma `∂²_xx P`**: `q=u` where the price is locally convex (`∂²_xx P>0`), `q=d` where concave. With the bounds driven by a **slow CIR process `Z_t`** (time-scale `δ`, Eq. 6), they prove the worst-case price converges to the constant-bound UVM price `P_0` at rate **√δ** (Thm. 2.5, via `E(X^δ−X^0)²≤C_0δ`), and build the first-order correction `P^δ=P_0+√δP_1+δP_2+⋯` (Eq. 12), reducing the 2-D fully-nonlinear BSB to a 1-D nonlinear PDE for `P_0` (Eq. 13) plus a linear PDE-with-source for `P_1`. The technical heart is that for **convex/concave payoffs** (vanilla calls/puts) the gamma keeps a fixed sign so the extremizer sits **at a band boundary** (`q*=u` or `d`) — the classic UVM shortcut — whereas for **general (e.g. butterfly) payoffs** the gamma changes sign on **zero-sets `S^0_{t,z}`** (Assumption 2.9) and the worst case is governed by those interior kinks.

For the twin this paper is the **rigorous source of the single most important caveat about the alias band**: the UVM "extremize at the boundary" shortcut is a **monotonicity/sign-of-gamma** trick. The twin's `ΔLER` is the **non-convex "butterfly" case** — its curvature in the channel parameters is indefinite — so its band extremum is **interior, not at a band edge**, and must be found **numerically** (the Tier-1 trust-region subproblem), exactly mirroring this paper's zero-set-of-gamma machinery.

## Contributions (claim → evidence → strength)
- **C1. Stochastic-bound UVM as a perturbation of constant-bound UVM (Thm. 2.5).** `P^δ→P_0` at rate `√δ`. *Evidence:* Prop. 2.1 (`E(X^δ−X^0)²≤C_0δ`) + Lipschitz `h` + Cauchy–Schwarz. *Strength: strong.*
- **C2. BSB PDE + perturbation expansion (Eq. 11–13).** Reduces 2-D fully-nonlinear → 1-D nonlinear (`P_0`) + linear-with-source (`P_1`). *Strength: strong (the computational payoff).* 
- **C3. Bang-bang structure / convex-vs-general dichotomy (Rmk. 2.4, Assn. 2.9).** Convex payoff ⇒ boundary extremizer; general payoff ⇒ gamma zero-sets drive the worst case. *Strength: strong — the conceptually load-bearing part.*

## Method (deep)
- **Model.** `α_t=q_t√Z_t`, `q_t∈[d,u]`; `Z_t` slow CIR (`dZ=δκ(θ−Z)dt+√δ√Z dW^Z`). `dX^δ=rX dt+q√Z X dW` (Eq. 7).
- **Worst case = BSB.** `∂_tP^δ+r(x∂_xP−P)+sup_{q∈[d,u]}{½q²zx²∂²_xxP+√δ(qρzx∂²_xzP)}+δ(½z∂²_zzP+κ(θ−z)∂_zP)=0` (Eq. 11). Leading order `∂_tP_0+sup_q{½q²zx²∂²_xxP_0}=0` (Eq. 13).
- **Bang-bang.** `sup_q ½q²(·)∂²_xxP_0` picks `q=u` if `∂²_xxP_0>0`, `q=d` if `<0`. For convex/concave `h`, sign is fixed → boundary (Rmk. 2.4). For general `h`, the zero-set `S^0_{t,z}={x:∂²_xxP_0=0}` and the sign-disagreement region `A^δ` within `√δ` of it (Eq. 14, Assn. 2.9) drive the correction.
- **Regularity.** Assn. 2.2 (`h∈C⁴`, bounded `h'`, polynomial `h^{(4)}`); Assn. 2.6/2.9 (uniform bounds; finite, separated gamma-zeros). Butterfly payoff violates `C⁴` → needs regularization (noted).

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | Rigorous viscosity-solution / asymptotic analysis; convergence theorem proven; assumptions explicit. |
| Novelty | **4** | UVM/BSB known (Avellaneda, Lyons); **new** = stochastic *slowly-varying* bounds + the `√δ` reduction. |
| Reproducibility | **5** | Self-contained PDE derivation + numerical illustration (Sec. 4). |
| Experimental design | **n/a (4)** | Numerical validation of the approximation (butterfly example). |
| Statistical rigor | **n/a** | PDE/analysis paper. |
| Scalability | **4** | The reduction to 1-D + linear is the scalability contribution; the gamma-zero-set bookkeeping is the practical cost. |

## Strengths
- **S1 — the convex-vs-general dichotomy is stated sharply (Rmk. 2.4 vs Assn. 2.9).** It makes explicit *exactly when* the boundary shortcut is valid (fixed-sign gamma) and *what replaces it* otherwise (zero-sets of gamma) — the transferable insight.
- **S2 — the `√δ` reduction (Eq. 12–13).** Turning a 2-D fully-nonlinear HJB into 1-D-nonlinear + linear-with-source is a clean, useful approximation with a proven rate.
- **S3 — honest regularity bookkeeping (Assn. 2.9, Rmk. 2.10).** Carefully tracking the `√δ`-neighborhoods of the gamma-kinks (and the loss of rate near non-smooth points) is exactly the rigor an extremization-over-a-set problem needs.

## Weaknesses / limitations
- **W1 — relies on smoothness + slow bounds.** `C⁴` payoff and *slowly-varying* (small-`δ`) bounds; fast-varying bounds or kinked payoffs (the actual butterfly) need regularization and lose the clean rate.
- **W2 — the boundary shortcut is special, not general.** The elegant `q*∈{d,u}` result is *only* for convex/concave payoffs; the general case is genuinely harder and only handled to first order.
- **W3 — single risky asset, single uncertain band.** A 1-D worst-case; high-dimensional model-uncertainty sets (the twin's CPTP set) are a different geometry.

## Relevance to the twin
This paper is the **rigorous origin of the twin's "don't use the UVM boundary shortcut" rule**, and it maps the twin's band tiers precisely:
1. **Worst-case-over-a-band = the alias band's upper/lower edge.** `P^δ=ess sup_{q∈[d,u]}E[h]` is Cont's `π̄` realized as a control problem; the twin's `max ΔLER` over `{E:NLL≤NLL_min+slack}` is the same object. The BSB PDE is the *dynamic* version; the twin's band is *static* (over a CPTP set at the calibration optimum), which is simpler.
2. **The sign-of-gamma bang-bang is the monotonicity trick the twin lacks.** UVM's clean `q*∈{d,u}` works because the worst case depends only on **sign(`∂²_xx P`)** (the gamma). The twin's analogue of gamma is the **curvature of `ΔLER` in the channel parameters** — and `ΔLER` is **non-monotone and non-convex** (coherent interference + decoder non-monotonicity), so its curvature `G=∇²ΔLER` is **indefinite**. Therefore the twin is in the **general/butterfly regime, never the convex-vanilla regime**: the band extremum is **interior**, not at a slack-boundary "edge," and must be found **numerically**. This is exactly why the band ladder is **Tier-1 TRS** (maximize an *indefinite* quadratic `ΔLER≈g·δ+½δᵀGδ` over the NLL ellipsoid `½δᵀHδ≤slack` — a trust-region subproblem with a global Moré–Sorensen solution) rather than a UVM-style endpoint pick.
3. **The gamma zero-sets ↔ where the twin's ΔLER curvature flips.** UVM's `S^0_{t,z}={∂²_xxP_0=0}` (the kinks that govern the general-payoff worst case) are the finance cousin of the **directions where `ΔLER`'s curvature changes sign** — the structure a faithful twin band must resolve, and the reason a naive "perturb the optimum" sampling (which sits near the interior, not the boundary kinks) systematically *under*estimates the band (the Tier-3 boundary-sampling-audit lesson).
4. **The `√δ` slow-bound perturbation ↔ slow calibration drift.** The slow CIR `Z_t` driving the bounds is the finance template for the **slowly-varying calibration bounds** over the Google 15 h window (the `predict`/drift axis) — the band's *bounds* themselves drift slowly while shot-noise fluctuates fast (the two-timescale picture shared with `fouque_mcmc`).

## How to use / trust + open questions
- **Trust:** high as the *theoretical justification* for numerical (TRS) extremization of the twin's band; it certifies that the boundary shortcut is invalid off convexity and shows the right machinery (zero-sets of curvature).
- **Open questions for the project:** (i) Confirm the twin's `ΔLER` Hessian `G` is **indefinite** on a coherent teacher (the "butterfly" diagnosis) — if it were definite, a boundary shortcut would exist and Tier-0 would suffice. (ii) Identify the twin's **gamma-zero-sets** (directions where `δᵀGδ` flips sign) — these are where Tier-0 (linear) and Tier-1 (TRS) bands diverge, i.e. the "how non-Gaussian is the band" diagnostic. (iii) Borrow the `√δ` slow-bound expansion as the drift model for a *time-varying* band over calibration windows (C-stage).

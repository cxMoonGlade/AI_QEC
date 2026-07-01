# Full-text review — Quanjun Lang & Jianfeng Lu, "Learning Memory Kernels in Generalized Langevin Equations" (arXiv:2402.11705)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF downloaded via
> `.claude/skills/theory-first/scripts/fetch_and_extract.py 2402.11705` →
> `outputs/papers/2402.11705.txt` (PyMuPDF, 31 pages / 64081 chars). All §/Eq/Fig refs from
> that text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.
> Published as SIAM J. Math. Data Sci. 8(1) 2026, DOI 10.1137/24M1651101 (arXiv v3, 21 May 2025).

## Metadata [paper]
- Authors: Quanjun Lang, Jianfeng Lu (Duke; supported NSF DMS-2309378; thanks Xiantao Li).
- Venue/status: arXiv:2402.11705v3 [stat.ML], 21 May 2025 → SIAM J. Math. Data Sci. 8(1) 2026, DOI 10.1137/24M1651101.
- Type: **Theory + numerics** (applied-math / stat.ML). Estimator with an a-priori error bound (two theorems) + synthetic-data numerical validation. No physical experiment.

## Executive summary [paper]
The Generalized Langevin Equation (GLE) coarse-grains fast bath DOF into a **memory kernel** γ(t)
(convolved with the past state) plus a **correlated noise** R(t) tied to γ by the
fluctuation–dissipation theorem. Learning γ from trajectory data is an ill-posed inverse problem:
γ solves a **first-kind Volterra equation** g = γ∗h whose convolution operator has zero spectrum ⇒
unbounded inverse. The paper's contribution is a **two-stage estimator with an a-priori guarantee**:
(1) a **regularized Prony method** estimates the correlation functions h (autocorrelation) and g
(force-correlation) as short sums of exponentials from noisy trajectory data; (2) a **regression over
a weighted Sobolev-norm (H¹) loss** with RKHS regularization recovers γ. The headline theoretical
result (Thm 4.1 coercivity + Thm 4.2 error bound): the **kernel L²(ρ) error is bounded, linearly, by
the estimation errors of the correlation functions** — `‖γ−γ̂‖²_{L²(ρ)} ≤ (2/m^{hε}_ω)(M^γ_ω‖h−hε‖²_{L²(ρ)} + ‖g−gε‖²_{H¹α(ρ)})`
— which is **strictly stronger than convergence-only**: it makes the ill-posed problem *well-posed*
in the exponentially-weighted space L²(ρ), ρ(t)=e^{−2ωt}. The Sobolev loss is what buys this; the two
"natural" losses (raw first-kind E₁, second-kind E₂) are shown to have **no** (E₁) or a **badly
ω-scaling** (E₂, m₂=O(ω²) as ω→0) coercivity constant.

## Method (deep) [paper]

### The model — GLE as a stochastic Volterra equation
One-dimensional, scalar (§2.1, Eq 2.1); mass m=1:
```
v′(t) = F(v(t)) − ∫₀ᵗ γ(t−s) v(s) ds + R(t)                                   (2.1)
```
- `v:[0,∞)→ℝ` velocity of a macroparticle; `γ:[0,∞)→ℝ` the memory kernel (continuous, integrable,
  **assumed exponential decay** |γ(t)|≤Ce^{−σt} for the theory);
- `R(t)` a **stationary zero-mean Gaussian process** obeying the **fluctuation–dissipation theorem** (Eq 2.2):
  ```
  ⟨R(t)R(s)⟩ = (1/β) γ(t−s)                                                    (2.2)
  ```
  β = inverse temperature. `⟨R(t)v(0)⟩=0` assumed. **This is the load-bearing FDT link: the noise
  covariance IS the kernel (scaled by 1/β) — the memory and the fluctuation are the same object.**

### Correlation-function relations (the observables the kernel must satisfy)
Multiply (2.1) by v(0), take expectations (Eq 2.3–2.5):
```
g(t) = ∫₀ᵗ γ(t−s) h(s) ds  = (γ∗h)(t)                                          (2.3)  ← first-kind Volterra
h(t) := ⟨v(t)v(0)⟩,   φ(t) := ⟨F(v(t))v(0)⟩                                     (2.4)
g(t) := ⟨v′(t)v(0)⟩ − ⟨F(v(t))v(0)⟩ = −h′(t) + φ(t)                            (2.5)
```
- `h` = autocorrelation of v (the two-time correlation), `g` = force-correlation function.
- **F=0 special case: g(t) = −h′(t)** (Eq 2.5); linear friction F(v)=−µv gives g=−h′+µh.
- Differentiating (2.3) → **second-kind** Volterra (Eq 2.6):
  ```
  g′(t) = (γ∗h′)(t) + h(0)γ(t)                                                  (2.6)
  ```
  Well-posed when h(0)≠0 (spectrum lower-bounded by h(0)); **this is what motivates including the
  derivative term in the loss.**
- Laplace domain (Lemma 2.3): `ĝ(z)=γ̂(z)ĥ(z)`, so formally `γ=L⁻¹[ĝ/ĥ]` — but **numerical inverse
  Laplace is severely unstable** (§2.3), so the paper avoids it except as a benchmark (θ_L).

### Stage 1 — regularized Prony estimation of h, g, φ (§3.2–3.3, Alg 1)
Prony models a correlation function as a sum of exponentials `h(t)≈Σ_k w_k e^{λ_k t}` (amplitudes w_k,
complex modes λ_k). From noisy discrete trajectory `v_l = v(t_l)+ξ_l` (Eq 3.1, ξ i.i.d. Gaussian σ_obs):
1. Estimate discrete autocorrelation `h_n = (1/(L−n)) Σ_{l} v_l v_{l+n}` (Eq 3.2, ergodic temporal
   average). **Drop h₀** (biased by σ_obs²; and h′(0)=0 for integrable-continuous kernel).
2. Solve the Prony linear system (Eq 3.3) for characteristic-polynomial coefficients a; find roots
   r_k via the **matrix-pencil method** (Hua–Sarkar, stability); this is **ill-conditioned** (Wilkinson
   polynomial) — but the goal is *nonparametric L²(ρ) approximation of h*, not exact modes.
3. **Regularizations that distinguish this from classic Prony:** (i) clip roots exceeding the decay
   threshold to enforce exponential decay (Eq 3.4: `r̃_k = r_k/(e^σ|r_k|)` if |r_k|≥e^{−σ}); (ii)
   augment multivalued log-branches (Remark 3.1); (iii) constrain **h′(0)=0** i.e. `Σ_k w_k λ_k = 0`
   (Eq 3.5); (iv) **RKHS (data-adaptive Tikhonov) regularization** on the amplitudes (Eq 3.6):
   ```
   w = argmin_{Σ w_k λ_k=0} ‖Zw − h‖² + λ ‖(ZZ⊤)† w‖²                          (3.6)
   ```
   λ chosen by the **L-curve method**. Output `h̃(t)=Σ_k w_k e^{λ_k t}`, and analytically
   `g̃ = −h̃′ = −Σ_k w_k λ_k e^{λ_k t}` (Eq 3.8; **derivatives from the Prony fit, not finite
   differences — the key accuracy win, Fig 1**). With force, φ estimated the same way (Eq 3.10):
   `g̃ = Σ w_k λ_k e^{λ_k t} + Σ w′_k e^{λ′_k t}`.

### Stage 2 — Sobolev-norm regression for γ (§3.4, Alg 2)
Loss (Eq 3.12), the crux:
```
E(θ) = ‖ g̃ − (θ∗h̃) ‖²_{H¹α(ρ)}                                                (3.12)
```
with the **exponentially-weighted Sobolev H¹ norm** (α₁,α₂>0, α₁+α₂=1):
```
‖f‖²_{H¹α(ρ)} = ∫₀^∞ ( α₁|f(t)|² + α₂|f′(t)|² ) dρ(t),    dρ(t)=e^{−2ωt}dt      (§3.4)
```
- `ω` = **weight/decay parameter** = "region of interest": large ω ⇒ estimate emphasised near t=0.
- The Sobolev (derivative) term is what supplies **coercivity** vs the plain L²(ρ) losses.
- Discretized in a basis {ψ_k} (cubic splines): `θ = Σ c_k ψ_k`, solve quadratic `c⊤Ac − 2b⊤c` with
  `A_ij=⟨ψ_i∗h̃, ψ_j∗h̃⟩_{H¹α(ρ)}`, `b_i=⟨ψ_i∗h̃, g̃⟩_{H¹α(ρ)}` (Eq 3.13), **again RKHS-regularized**
  (Eq 3.14): `c = argmin c⊤Ac − 2b⊤c + λ c⊤A†c`.
- **Optimal α (Remark 4.3):** α=(α₁,α₂) ∝ (α′₁,α′₂), α′₁=lim_{z→∞} z ĥε(z)=Σw_k=hε(0),
  α′₂=lim_{z→0} ĥε(z)=Σ w_k/(−λ_k)=∫₀^∞ hε(t)dt — balances the coercivity floor at z=0 and z=∞.

### The noise / FDT term
The correlated noise R is **not learned as a separate object** — it enters only through (2.2): the
kernel γ *is* the noise covariance (×1/β). In numerics R is synthesised via spectral representation
(Shinozuka–Deodatis, accelerated Hu–Schiehlen) and the fit is checked by comparing the estimated
noise autocorrelation to γ (Fig 1 panel 1, "verify the fluctuation-dissipation condition").

## The A-PRIORI BOUND (the reason to read this) [paper]

**Theorem 4.1 (coercivity, §4.1).** Under Assumption 1 (γ, θ, h, g, hε, gε and derivatives smooth with
exponential decay, parameter σ) and Assumption 2 (∃ω>0 with m^γ_ω,m^h_ω,m^{hε}_ω>0 and
M^γ_ω,M^h_ω,M^{hε}_ω<∞, where M/m are the sup/inf over the line z=ω+iτ of `α₁|f̂(z)|²+α₂|z f̂(z)|²`, Eq 4.1):
```
m^h_ω ‖θ−γ‖²_{L²(ρ)}  ≤  E(θ)  ≤  M^h_ω ‖θ−γ‖²_{L²(ρ)}                          (4.2)
```
⇒ **γ is identifiable by E in L²(ρ)**: E(θ)=0 ⟹ θ=γ in L²(ρ). Proof = Plancherel for Laplace transform
(Lemma 2.2): E(θ) = (1/2π)∫ (α₁|ĥ(z)|²+α₂|zĥ(z)|²)|f̂(z)|² dτ with f=θ−γ; bound the bracket by
Assumption 2.

**Theorem 4.2 (a-priori error bound, §4.1) — verbatim:**
1. **With the true h**, error in γ ≤ error in g alone:
   ```
   ‖γ − γ_{gε,h}‖²_{L²(ρ)}  ≤  (1/m^h_ω) ‖g − gε‖²_{H¹α(ρ)}
   ```
2. **With estimated hε and gε:**
   ```
   ‖γ − γ_{gε,hε}‖²_{L²(ρ)}  ≤  (2/m^{hε}_ω) ( M^γ_ω ‖h − hε‖²_{L²(ρ)}  +  ‖g − gε‖²_{H¹α(ρ)} )
   ```

**Exactly what it guarantees / what it requires:**
- The **kernel error is controlled — linearly — by the correlation-function estimation errors**
  (‖h−hε‖ in L²(ρ) and ‖g−gε‖ in the H¹ Sobolev norm), with an **explicit multiplicative constant**
  2/m^{hε}_ω (from coercivity) and M^γ_ω (kernel's own decay-weighted magnitude).
- **The constant is inversely proportional to the coercivity floor m^{hε}_ω** — so the guarantee is
  only useful if m^{hε}_ω is bounded away from 0. The whole point of the Sobolev loss + Prony hε is that
  **m^{hε}_ω stays away from 0 across ω** (numerically m^{hε}_ω=8.72×10⁻² at ω=0.05, "changes mildly
  with ω", §5.1/Fig 3–4), whereas the naive losses fail: **E₁ has m₁=0 (no bound exists)** and **E₂ has
  m₂=O(ω²) as ω→0 (blows up), Prop 4.2** — so E=α₁E₁+α₂E₂ is the *only* combination with a floor at
  neither 0 nor ∞.
- **Why stronger than convergence-only:** it is a *finite-sample, a-priori* (before-you-run, given the
  correlation-error budget) *well-posedness* statement, not an asymptotic "estimator → truth as data →∞".
  It says: reduce your correlation-function error by X, and your kernel error is provably ≤ const·X in a
  named norm. Convergence-only results give no rate and no computable constant. **The trajectory-level
  reconstruction error is thereby bounded by the kernel-estimation error weighted by the exponential
  decay measure ρ(t)=e^{−2ωt}** — the "decay function" the brief refers to is exactly ρ (large ω ⇒
  short-time-weighted certificate; small ω ⇒ long-time, but M^γ_ω and the error inflate).

## Scaling / scope [paper]
- **Strictly 1D scalar kernel, single scalar observable v.** §2.1 opening: *"we restrict the discussion
  to one dimension and leave the generalization to high dimensions for future work."* Conclusion §6 lists
  the multidimensional case (γ becomes a **matrix**, per-element analysis) as **future work — not done here.**
- **Temporal memory only.** γ is a function of a single time-lag t. **No spatial index, no lattice, no
  cross-site / spatially-correlated memory anywhere in scope.**
- **Kernel class the theory covers: exponential-decay** (Assumption 1; γ=Σ u_k e^{η_k t}, sum of
  possibly-complex-mode decaying exponentials, Re η_k<0 — includes **oscillatory-decaying / colored
  memory** via complex modes, e.g. §5.1 uses η with ±0.32i imaginary parts). **Power-law (long-memory)
  kernels are OUT of the theory** (Remark 5.1: "does not have exponential decay, our previous analysis
  does not hold") though the *algorithm* still runs empirically (Appendix A) — but with **no a-priori
  bound** there (branch cut on the negative real axis ⇒ M^γ_ω blows up as ω→0).
- **Data regime:** stationary ergodic ⇒ single-trajectory temporal averaging suffices; **non-stationary
  (nonlinear force / drift) ⇒ ensemble trajectories required** (Remark 2.1, §5.3), error ∝ M^{−1/2}
  Monte-Carlo in # trajectories M, **barely improves with trajectory length L** (Fig 7).

## What it CAN and CANNOT represent [paper → ours]
**CAN:** temporal, stationary, **colored** memory whose kernel is a finite sum of decaying (possibly
complex/oscillatory) exponentials — i.e. **Prony-representable colored noise with an exponential
envelope**. The complex-mode capability means **oscillatory / revival-bearing kernels are representable**
(the §5.1 example kernel itself oscillates). FDT-consistent noise is baked in by construction (2.2).

**CANNOT (without extension):** (a) **spatial correlation / 2D / multi-site** — 1D scalar only, matrix
extension is unwritten future work; (b) **true power-law / 1/f long-memory** with a rigorous bound —
the exponential-decay assumption fails, the bound voids (branch-cut, M^γ_ω→∞), only an empirical fit
survives (App A); (c) **non-Gaussian noise** — R is assumed stationary Gaussian; (d) anything where
`⟨R(t)v(0)⟩≠0` (the assumed decoupling).

## Findings + numbers [paper]
- **F=0 canonical run (§5.1):** true kernel γ=Σ₅ u_k e^{η_k t}, u=[0.3488,0.3488,0.3615,0.5300,0.3045],
  η with two complex-conjugate modes (−0.1631±0.3211i) + three real. L=2¹⁶, β=1, σ_obs=0.1, obs ratio
  r=70. At ω=0.05 (ρ=e^{−0.1t}), α=(0.9030,0.0970) from Remark 4.3: `‖h−h̃‖²_{L²(ρ)}=1.12×10⁻³`,
  `‖g−g̃‖²_{H¹α(ρ)}=2.37×10⁻³`, coercivity floor **m^{hε}_ω=8.72×10⁻²**, theoretical error upper bound
  **0.316**, which empirically controls the actual θ error.
- **Estimator ranking (Fig 2,4):** proposed θ (Sobolev E) **best**; θ_L (inverse-Laplace of Prony)
  comparable but its spectral function shows **false phase changes** (ILT ill-posedness); θ₁ (raw
  first-kind E₁) and θ₂ (second-kind E₂) worse; θ₁ error even **fails to decrease** as σ_obs→0 (E₁
  ill-posed).
- **ω dependence (§5.2, Fig 4):** m^{hε}_ω roughly flat in ω; 1/m₂ blows up as ω→0; an oracular optimal
  ω≈10^{0.6} exists (needs true γ — flagged as future work).
- **Non-stationary (§5.3, Fig 7):** error ∝ M^{−1/2} (Monte-Carlo), essentially flat in L. Confirms
  ensemble data is mandatory off-stationarity.
- **Exponential-kernel bound instance (App A):** γ=e^{−t}, quantitative L²(ρ) error bounds 0.0437
  (single long traj) and 0.0705 (ensemble short) — a worked, closed-form-validated a-priori certificate.

## Limitations [paper]
- 1D scalar only; matrix/multidim = future work.
- Bound requires **exponential decay** of γ, h, g (Assumption 1) and a **positive coercivity floor**
  m^{hε}_ω (Assumption 2) — both fail for power-law long memory.
- Requires **h(0)≠0** (well-posedness of the 2nd-kind form) and h′(0)=0 (integrable kernel).
- Noise **stationary Gaussian**, ⟨R(t)v(0)⟩=0.
- Optimal ω only known **oracularly** (needs true γ).
- Prony root-finding is intrinsically ill-conditioned (Wilkinson) — mitigated, not eliminated, by the
  nonparametric L²(ρ) goal + RKHS regularization.
- The bound is on the **kernel in L²(ρ)** (and via FDT, the noise covariance); the paper does **not**
  directly bound a downstream quantity like a coherence function |L(t)| — that is our inference.

## Relevance to qec_twin [ours]

**Context.** Our non-Markovian wedge (`project-nonmarkovian-wedge-must-be-coherence.md`,
`project-coupling-nonmarkovian-is-the-contribution.md`) rests on a **shared 1/f/TLS source** whose
*temporal* memory produces **CP-divisibility-breaking dephasing**, whose only unforgeable signature is a
**coherence revival** — |L(t)| non-monotone. We want to represent that temporal memory as a **learned
closure with a bounded error**, and the closure must **preserve the revival**.

**Mapping.** The GLE-with-memory is the classical analogue of an **exact-dephasing / pure-decoherence
non-Markovian master equation**: for pure dephasing by a Gaussian bath, the coherence is
`L(t)=exp(−∫∫ C(t₁−t₂) …)` with `C` the bath autocorrelation — and **C is exactly the FDT-linked noise
covariance (2.2) = the memory kernel γ (×1/β)**. So:
- γ(t) ↔ our **bath/dephasing memory kernel** (the 1/f/TLS autocorrelation).
- The two-stage estimator (Prony correlations → Sobolev regression) is a **candidate memory-closure
  learner** with a *computable* a-priori error certificate on γ in L²(ρ).
- **The a-priori bound is the piece we actually want:** it converts "we truncated the memory to a finite
  sum of modes" into a *bounded* statement — `‖γ−γ̂‖²_{L²(ρ)} ≤ (2/m^{hε}_ω)(M^γ_ω‖h−hε‖² + ‖g−gε‖²_{H¹})`
  — which is precisely the "bounded error" our anti-toy protocol (Rule III: declare + BOUND every
  simplification) demands of a closure. A finite-memory truncation with an *unbounded* error would be a STOP.

**Does the finite-mode truncation preserve a coherence revival (non-monotone |L(t)|)?** **[ours, plausible-YES with a caveat].**
A revival requires **oscillatory structure** in the memory (a spectral feature / non-monotone L). The
Prony class γ=Σ w_k e^{λ_k t} with **complex λ_k** carries exactly such oscillatory-decaying modes — the
paper's own §5.1 kernel oscillates (η=−0.16±0.32i). So the representation is *capable* of a revival, and
the L²(ρ) certificate bounds the error on the very object (γ=C) that generates |L(t)|. **Caveat / trade-off:**
(i) the a-priori bound is **weighted by ρ=e^{−2ωt}**, so it is a *short-time-weighted* certificate — a
**late-time revival at large t is down-weighted** (small ω needed to certify it, which *inflates* M^γ_ω
and the constant). The revival's certifiability therefore trades against ω. (ii) A revival driven by a
**power-law / 1/f tail** (motional-narrowing-boundary physics) sits in the regime where the **bound
voids** (Remark 5.1 / App A) — the algorithm still runs but with no certificate. So: **exponential-envelope
colored/TLS-Lorentzian memory ⇒ revival representable AND bounded; hard 1/f long-tail ⇒ revival maybe
representable but NOT bounded here.**

**What to REUSE / build.** No existing repo module does this (our carrier is MPS-MCWF forward, not a
kernel-inverse learner). If we pursue a learned temporal closure, this is the **method template**:
regularized-Prony on the bath autocorrelation + Sobolev-H¹ RKHS regression, with Thm 4.2 as the
declared-and-bounded-simplification certificate. It pairs with our coherence-probe observable (Ramsey/echo
|L(t)|), NOT the Z-syndrome stream (coherence-blind per `project-twin-axisA-gate-result.md`).

**CORRECTION it forces on us.** If we ever claim a memory-closure is "bounded", the bound must be **in a
named weighted norm with a positive coercivity floor** — a plain L²/MSE-convergence claim is the E₁/E₂
trap (m₁=0 / m₂=O(ω²)) the paper explicitly kills. And a bounded certificate is **only available in the
exponential-decay class** — for genuine 1/f we must down-scope the claim to "empirical fit, unbounded" or
bracket the tail (per `feedback-underdetermined-bracket-not-freeze.md`).

## INDEPENDENT-ORACLE-ability / validation route [ours]
- **Closed-form oracle exists** for the exponential class: γ=e^{−t} ⇒ h, g analytic ⇒ Thm 4.2 gives a
  *numeric* bound (0.0437 / 0.0705, App A) — a genuine **independent** check (closed form, not the
  estimator's own output). This satisfies FAITHFULNESS Rule I (independent ground truth ≠ parallel model).
- For our use: a **known TLS/Lorentzian bath** (single-TLS ⇒ Lorentzian spectrum ⇒ exponentially-decaying
  autocorrelation = exactly Prony-representable, one complex mode) gives a **closed-form γ and a
  closed-form |L(t)|** to certify both the kernel recovery *and* the preserved-revival claim against — no
  circular "our own qutip" oracle needed.
- **Positive control (must-fail):** feed a genuine 1/f power-law tail; the certificate must *refuse*
  (M^γ_ω→∞) — if a claimed bound stays finite there, the check is broken.

## How to use / trust + open questions [ours]
- **Trust:** FULL-TEXT read; all equations, both theorems, both propositions, and the scope statements
  read verbatim from the .txt. Figures not pixel-extracted (numbers taken from the text/captions, which
  state the key values). High confidence in the math; the numerics are synthetic-data only.
- **Verdict — is this the memory-closure piece for our temporal 1/f memory?** **Partially.** It is the
  right *methodology and the right kind of a-priori certificate* for a **temporal, scalar, colored
  (TLS/Lorentzian) memory closure** — and it plausibly preserves the coherence revival via complex Prony
  modes, with the certificate covering the exact object (γ=bath autocorrelation). **But it is 1D-scalar
  and exponential-decay-only**: it does **not** cover spatial correlation (our cross-qubit shared-source
  coupling — that's the matrix/multidim future work) and its **bound genuinely voids for true 1/f**
  (App A empirical only). So: adopt as the temporal-closure template for the *single-qubit dephasing /
  TLS-Lorentzian* wedge with a real bounded certificate; do **not** claim its bound for a 1/f tail or for
  the spatial-coupling piece.
- **Open questions:** (1) does our revival survive the ρ=e^{−2ωt} weighting at the physically relevant
  revival time (choose ω)? (2) can the TLS-bath Lorentzian autocorrelation be pushed to enough modes to
  approximate 1/f over our decoherence window while *keeping* a finite (if loose) bound — i.e. quantify
  the trade-off, don't just assert it? (3) the spatial/matrix extension (their §6 future work) is what our
  *shared-source cross-qubit* coupling actually needs — this paper does not provide it.

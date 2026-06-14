# CF-WR P2 (a)-basis — Seam-gluing Choi trace-distance residual leading-order derivation (G0 mean-field vs G1 Petz)

> This is the (a)-exact / (b)-band derivation basis for §5 P2 of `registration.md` (same directory) (reviewer-1 BLOCK-M2 requirement: P2 must not assert without a written derivation).
> Derived by the opus theory agent (2026-06-14), cross-referenced against local `composed.py` (G0 implementation), `D_package_derivations.md` (T-B non-unital membership), `metric_results.md` SEAM-TEST (measured G0 exponent 0.973), Fawzi–Renner 1410.0664 / JRSWW (PMC4841654).
> Epistemic legend: (a) exact; (b) derived prediction band; (c) heuristic. Each step is labeled; conjectural points are **bolded inline**.

## 0. Reviewer-2 binding corrections (override the corresponding body text, 2026-06-14)

The body is the working derivation; the following 5 items are **binding overrides** and take precedence:

- **[B-1] `c<1` is (b), not (a).** The "`c_{G1}<c_{G0}` strict inequality (a)" in §3.4/§4 is **downgraded to (b)**: `‖χ⁽¹⁾−Petz(χ⁽¹⁾)‖₁<‖χ⁽¹⁾‖₁` does not hold in general (trace norm is not aligned-subtractive; a rotated Petz can over-rotate and worsen some components; if χ⁽¹⁾ has no ρ_BC support then c=1). There is no theorem giving a `δ>0` lower bound. ⇒ **c<1 is a (b) bet, and is decoupled from G0 (not a G0 premise)**. c≥1 = finding.
- **[B-5] Bound constant changed to `√(I_nats)`.** Via Fuchs–van de Graaf: `F²≥2^(−I_bits)=e^(−I_nats)`, `T²≤1−F²≤1−e^(−I_nats)≤I_nats` ⇒ **`D_Choi^{G1} ≤ √(I_nats)=√(ln2·I_bits)`**. The `√(2ln2·I)` in the body/§3.1 **has an extra √2 and is void**.  τ_D should be recalculated accordingly.
- **[B-2] Perturbative coordinate uses signed asymmetry δ′=p10−p01 (two-sided).** The "first-derivative cancellation" from the quadratic nature of CMI holds only when λ=0 is an **interior minimum**; R−1 is one-sided (R≥1, AM–GM) and will land at an endpoint. Switching to δ′ (two-sided; I is even in δ′ ⇒ δ′=0 is an interior point) ⇒ I=O(δ′²) strictly. **Moreover this bound-scaling does not gate any criterion** (the actual residual is measured), and is not load-bearing.
- **[B-3] 2D: at-most-linear, not strictly linear.** The "disjoint support ⇒ ∝L" in §5 (R-2D) **does not hold for 2D shared-corner seams** (adjacent 2×2 windows share a corner qubit ⇒ supports intersect ⇒ trace norm is sub-additive). Revised to **monotone + O(L) upper bound (a), linearity as (b) center**.
- **[B-4] c_{G0} refined.** The G0 in `composed.py`, via conditional reduction, **captures the marginal-shift sector**; what is lost is only the **uncaptured connected part**: `c_{G0}=½‖χ⁽¹⁾_uncaptured-connected‖₁ ≤ ½‖χ⁽¹⁾‖₁`. Slope 1 is unchanged; 0.973<1 is recorded as within band [0.90,1.10] + O(λ²) admixture, not an exact confirmation.

## 1. Setup
- Object (a): J(E)=(I⊗E)|Ω⟩⟨Ω|; a single seam partitioned as **A—B—C** (B = overlap/buffer); gluing is a function only of the measured marginals {ρ_AB, ρ_BC}.
- Perturbation parameter (a): λ = amplitude of cross-seam correlations. Registered knob = **non-unital local CPTP** along the T-B curve (r=1.27e-2, R=5 member (p01,p10)=(6.7039e-3,0.120296)); **non-unital (p01≠p10) is what carries correlations**; unital symmetric point R=1). Coherent companion teacher U_φ=exp(−iφZ⊗Z) in the same frame, λ↦φ.
- Residual (a): D_Choi^G(λ)=½‖ρ(λ)−glue_G(ρ_AB,ρ_BC)‖₁.
- Correlation expansion (a): ρ(λ)=ρ⁽⁰⁾+λρ⁽¹⁾+λ²ρ⁽²⁾+…; marginals expanded similarly.
- **(S1, a) Key input**: non-unital ⇒ the first-order term ρ⁽¹⁾ contains **nonzero O(λ) A:C connected (cumulant) correlations** χ⁽¹⁾≠0. Proof: non-unital breaks parity/twirl symmetry, so the odd sector does not cancel at first order. (Contrast: unital-diagonal coupling twirls to Z⊗Z dephasing, connected correlations are even, first order cancels — T-A/unital pin.)

## 2. G0 (mean-field / conditional product) leading order
- G0 implementation (a, `composed.py:25–68`): **synchronized conditional product (mean-field)**, strip constrained to the product manifold; the seam acts as a conditional reduction onto the marginal averaged over the partner branch. **Connected A:C correlations are identically 0 (product constraint, all orders)**.
- Leading residual (a order / b coefficient): what G0 cannot represent is exactly the connected part χ. χ(λ)=λχ⁽¹⁾+O(λ²), χ⁽¹⁾≠0 (S1).
  **D_Choi^{G0}(λ)=c_{G0}·λ+O(λ²), c_{G0}=½‖χ⁽¹⁾‖₁>0 — linear, slope 1.**
- Consistent with K1 measurement (a, post-hoc): measured sandwich exponent **0.973**, k2ry 0.858 ≈ 1 — this derivation predicts slope 1, and explains why the old quadratic ansatz was falsified (it mistook the dropped terms for O(λ²) self-consistent error, missing that the product constraint drops the **first-order** connected correlations).
- Exception (C0, a): **unital-diagonal/twirled coupling ⇒ χ⁽¹⁾=0 ⇒ D_Choi^{G0}=O(λ²) (slope 2)**. In other words "order = parity of the leading connected correlation". Non-unital + un-twirled coherent ∈ O(λ) class.
- Mean-field self-consistency error (a): O(λ²), subleading.

## 3. G1 (Petz) leading order — crux
- Petz universal rotation map (a, JRSWW): R_{B→BC}(X_B)=∫dt β₀(t) ρ_BC^{(1+it)/2}(ρ_B^{−(1+it)/2}X_Bρ_B^{−(1−it)/2}⊗I_C)ρ_BC^{(1−it)/2}, **depends only on ρ_BC**.
- Bound (B1, a; constant per §0 [B-5]): D_Choi^{G1} ≤ √(I_nats)=√(ln2·I_bits) (Fuchs–van de Graaf; **not √(2ln2·I), which is void**).
- CMI second-order ⇒ bound linear (a): I(A:C|B)=κλ²+O(λ³) (non-negative + analytic + vanishes at Markov point ⇒ first derivative cancels ⇒ quadratic); hence √I∝λ, **the bound itself is linear**, and **a linear upper bound cannot determine whether the actual residual is λ or λ²**.
- First-order expansion (a): glue_{G1}(λ)=R⁽⁰⁾(ρ_AB⁽⁰⁾)+λ[R⁽⁰⁾(ρ_AB⁽¹⁾)+R⁽¹⁾(ρ_AB⁽⁰⁾)]+O(λ²); at the Markov point R⁽⁰⁾(ρ_AB⁽⁰⁾)=ρ⁽⁰⁾ (exact recovery). First-order residual Δ⁽¹⁾=ρ⁽¹⁾−[…].
  - Marginal-shift sector: Petz reproduces both measured shifts ρ_AB⁽¹⁾ and ρ_BC⁽¹⁾ ⇒ **Δ⁽¹⁾=0 in that sector**.
  - Connected part χ⁽¹⁾: **(P-cond, a iff)** Δ⁽¹⁾=0 (Petz cancels at first order ⇒ O(λ²)) **if and only if** χ⁽¹⁾ is carried by ρ_BC (B screens); otherwise the first-order residual survives (O(λ), smaller coefficient).
- Non-unital case (a structure / b coefficient): seam correlations are generated locally at the B–C interface within one round and transmitted to A via ρ_AB/ρ_BC ⇒ B-mediated. **However, non-unital causes [ρ_BC,ρ_B⊗I_C]≠0, which impedes the rotated Petz from exactly inverting at first order**, so **the first-order residual generally survives**:
  **D_Choi^{G1}=c_{G1}·λ+O(λ²), 0≤c_{G1}<c_{G0} strictly.**
- **§3.5 referee-proofing (a flag)**: a clean O(λ²) requires χ⁽¹⁾ to be exactly Petz-recoverable (first-order strict Markov), which **cannot be proven** for non-unital interfaces. Hence **no slope-difference is registered (G0=1, G1=2)**; only the **coefficient ratio** is registered.

## 4. FROZEN P2
- **P2.1 (a)**: D_Choi^{G0}=c_{G0}λ+O(λ²), slope **1** (band [0.90,1.10]; measured 0.973 retro-confirms). Unital/twirled ⇒ slope **2**.
- **P2.2 (b) registered discriminator**: D_Choi^{G1}=c_{G1}λ+O(λ²), **c≡c_{G1}/c_{G0}∈[0,1) strictly (a), directional bet c ≤ 0.5 (b)**. c≥1 falsifies (finding); c≈0 (G1 slope measured ≈2) = **bonus** confirmation of the stronger O(λ²) sub-hypothesis, not pre-assumed. Within-run comparison (same teacher/functional/grid, normalization cancels) ⇒ c is more robust than individual slopes alone.
- **P2.3 (a) pin**: at the unital point (p01=p10), c_{G0} and c_{G1} both → 0 at first order, residual O(λ²). Violation = build bug.

## 5. 2D seam-length L scaling (correction: linear in L, not √L)
- **(R-2D, a orthogonal support)**: local field ⇒ χ⁽¹⁾_ℓ supports of L interface cells are disjoint ⇒ trace norm is additive ⇒ **D_Choi∝L linear**.
- **Why L not √L (a)**: trace distance is the L₁ norm of an operator direct sum; contributions add by **amplitude** (not in quadrature); √L is the **fluctuation/variance** law and does not apply to the L₁ Choi residual. (Metric-dependent: if measuring fidelity or the standard error of a fluctuation functional, √L returns.)
- **Along-seam correlation case (b)**: still ∝L, coefficient absorbs ξ.
- **P2.4 (b)**: per-seam Choi residual **monotonically increasing, asymptotically linear in L** (exponent band [0.85,1.15], **not** [0.4,0.6]). Honest caveat: the exact-DM oracle suffices only for L∈{1,2,3}, so **only sign+monotone is measurable**; the L-exponent is direction-only (exponent miss = finding, does not falsify sign/monotone). **c (P2.2) is first-order independent of L ⇒ c<1 is a robust 2D-transferable criterion**; the L-law for the absolute residual is direction-only.

## 6. A referee flag
"CMI is second-order in λ" (§3.2) is **not explicitly stated** in Fawzi–Renner/JRSWW; this derivation obtains it rigorously from non-negativity + analyticity + vanishing at the Markov point — the registration must cite it as a **derived corollary**, not a verbatim paper claim.

## Sources
Fawzi–Renner CMP 340(2015), [1410.0664](https://arxiv.org/abs/1410.0664); Sutter–Fawzi–Renner Proc.R.Soc.A 472(2016), [PMC4841654](https://pmc.ncbi.nlm.nih.gov/articles/PMC4841654/); local `composed.py`, `D_package_derivations.md` §D5, `T1_requirements.md`, `metric_results.md` SEAM-TEST (measured 0.973/0.858, quadratic falsified, φ² cross-window quality ×8.7/×3).

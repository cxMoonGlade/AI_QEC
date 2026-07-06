# Class-1 notion-2 multi-time imprint — effect-size GO/NO-GO (predict-before-measure, minimal analytic)

**Status: PRE-REGISTRATION, 2026-07-06. Predictions written BEFORE the run; a miss is a finding, not a re-fit.**
Minimal, CPU-analytic go/no-go (Track 1 Step 1 of `HANDOFF_simulator_nonmarkovian_visibility_2026-07-04.md`, re-sited
to **Class-1**). It does NOT build the full Class-1 ancilla-axis architecture; it lands the **bandwidth** that decides
whether that build is worth it. If both guardrails land at feasible N → build the full run; if not → **honest cap
(G4-consistent), do not hard-build.**

## The question (binding)
Is the **Class-1** (ancilla/syndrome SPAM) multi-time imprint of the realistic 1/f source, on the **passive** dual-axis
syndrome record, **both**
- **(Guardrail A — feasible)** detectable above the sampling floor, `N_detect ≤ FEASIBLE_N = 1e6`; **and**
- **(Guardrail B — non-Markov-k-trivial)** distinguishable from a matched trivial **slow-RTN** (single-fluctuator,
  order-1 Markov) null at `N ≤ 1e6` — i.e. the 1/f multi-lag structure is not reducible to a slow drift?

## Object + observable (corrected, per the handoff — NOT the retracted G0-v2/G6)
- **Record:** the round-delta detector stream `D_{c,r} = m_{c,r-1} XOR m_{c,r}`. Under constant params (OFF arm) it is
  **exactly MA(1)**: `p_ij(lag1)=μ`, `p_ij(lag≥2)=0` EXACTLY (a-exact, `g6_null_feasibility_from_constants.py`).
- **Observable (fix A):** the **absolute lag≥2** direct correlation `p_ij(lag≥2)` (Spitz Eq.13,
  `qec_twin.hardware.pij.spitz_pij_exact`) and `RR_CORR` — read on the SHARED arm as an ABSOLUTE quantity. lag≥2 is
  the clean "pure memory" channel (off-arm structural zero).
- **Null (fix A, decisive):** **shared vs OFF** (structural zero), NOT shared-minus-markovian (the retracted
  exchangeable trap that forced the second-order `N∈[1.1e10,1.2e15]`).
- **Class-1 siting:** the 1/f source modulates the ancilla **readout** error `p_ro` (Class-1 SPAM), the very rate that
  sets the MA(1) instrument (`μ = p_ro + p_rs − 2 p_ro p_rs`). Modulation depth `s` = fractional shift of `p_ro` at 1σ
  of the (unit-variance-normalized) 1/f trajectory: `p_ro(r) = p_ro0·(1 + s·x_r)`. The lag≥2 delta-rate covariance
  then inherits the source lag≥2 autocov via the closed-form sensitivity `dq/dp_ro`, `q = 2μ(1−μ)`.

## Guardrail computations (closed form; committed constants)
- `p_ro0 = 1e-2`, `p_rs = 5e-3` (committed `SourceCouplingConfig`); `μ=0.0149`, off delta rate `q = 2μ(1−μ)=0.02936`.
- 1/f normalized autocov `C_x(l) = [Σ_k e^{−2γ_k l}] / [Σ_k 1]` over `OneOverFDriftSource` `γ_k = geomspace(0.005,0.5,8)`.
- **Guardrail A:** shared lag-l delta-rate cov `Cov(l) = (dq/dp_ro · p_ro0 · s)² · C_x(l)`; signal `p_ij(l) =
  spitz(q,q,q²+Cov(l))`; `N_detect_A = (Z·SE₁ / p_ij(2))²`, `Z=3`, `SE₁ = spitz_pij_delta_se(q,q,q²+Cov,1)`.
- **Guardrail B:** matched slow-RTN with `γ_RTN = −½ ln C_x(1)` (equal lag-1 autocorr); signal = the shared-arm
  `p_ij(l)` DIFFERENCE between the 1/f `C_x(l)` and the RTN `C_x(1)^l` at lag≥2; `N_detect_B` sizes that difference.
- **Sensitivity models (bracket — D1 is a user decision, declared class-(c), NOT truth):** (i) readout-only
  `dμ/dp_ro=1−2p_rs`; (ii) readout+reset-coherent (both SPAM rates track the source) ≈ 2× sensitivity.
- **Sweep:** `s ∈ {0.02,0.05,0.1,0.2,0.35,0.5}` (fractional 1/f readout drift at 1σ; superconducting readout
  assignment error is drift-prone O(10–50%), so this brackets realistic→aggressive). Report `N_detect` across it +
  the feasibility crossover `s*`.

## Epistemic-status declarations (`docs/METRICS.md`)
- **(a) exact:** off-arm `p_ij(lag≥2)=0` (MA(1) structural zero); the analytic 1/f autocov `C_x(l)=Σe^{−2γ_k l}/8`.
  **Self-check:** a from-scratch i.i.d.-bit + modulated-`p_ro` Monte-Carlo must reproduce the analytic lag-2 `p_ij`
  (zero-tolerance on the OFF structural zero; ≤3σ MC agreement on the shared signal) before the sweep is trusted.
- **(b) prediction bands (registered bets — a miss is a finding):**
  1. **Guardrail A / readout-only:** feasibility crossover `s* ≈ 0.5–0.65` ⇒ **NO-GO for plausible readout drift
     `s ≤ 0.3`** (`N_detect_A(s=0.2) ~ 1e7–1e8`).
  2. **Guardrail A / readout+reset-coherent:** `s* ≈ 0.25–0.35` ⇒ marginal-GO only at aggressive drift.
  3. **Guardrail B:** the 1/f-vs-matched-RTN lag≥2 gap is a small fraction (~few %) of the signal ⇒ `N_detect_B ≫
     N_detect_A` ⇒ **NOT separable at 1e6** (Guardrail B NO-GO) even where A is feasible.
  4. **Overall:** likely **honest cap** — the Class-1 SPAM route does not cleanly clear BOTH guardrails at feasible N
     for realistic drift; the imprint is either sub-floor (A) or Markov-k-trivial (B). (If A+B both land against
     prediction, that is the GO finding → build the full run.)
- **(c) gates:** `Z=3`; `FEASIBLE_N=1e6`; **honest-cap rule** — if the realistic bracket fails to clear BOTH A and B
  at `N_detect ≤ 1e6`, register the cap (G4-consistent registered STOP), do NOT hard-build the Class-1 architecture;
  the class-(c) `s`-bracket + the readout-only vs readout+reset sensitivity are D1 user decisions for any full build.

## Scope / discipline
Analytic, CPU, no GPU, no mainline-`src` change (docs/outputs normal flow). Reuses the committed source/coupling
constants + `spitz_pij_exact`/`spitz_pij_delta_se` + the MA(1) self-check scaffolding; DISCARDS the retracted
`record_N_sizing`. Simulator-internal legitimacy instrument, not a twin deliverable. Present the bandwidth to the user
before any full build (un-led design review still required for the build per handoff §5).

## RESULT (2026-07-06, `notion2_class1_gonogo.py`, GATE `CLASS1_GONOGO_CAP_A_SUBFLOOR`, sha `e191cb65`, exit 0)

**Method upgrade (a finding from the self-check):** the first-order analytic underestimated the lag-2 covariance by
~26% at `s=0.5` — the modulation `s·x` is not small (50% of `p_ro` at 1σ) and `E[D_r|x]=μ_{r-1}+μ_r−2μ_{r-1}μ_r`
depends on ADJACENT rounds (`x_{r-1}+x_r`), not a single `x_r`. Fixed by computing the lag≥2 covariance from the
EXACT conditional delta-rate `E[D_r|x]` over an MC of 1/f trajectories (conditional independence ⇒ no Bernoulli bit
noise ⇒ clean at 4e5 shots). Self-checks all green: 1/f sampler autocov lag1/2 = 0.810/0.698 (analytic 0.808/0.696);
OFF-arm lag2 cov = 4.6e-18 (structural zero); small-s (0.05) MC vs first-order agree to 0.9%.

**BANDWIDTH (N_detect at the delta-rate `q=0.0294`; s = fractional 1/f readout-drift at 1σ):**

| s | readout-only N_det_A | readout+reset N_det_A | N_det_B (1/f vs matched-RTN) |
|---|---|---|---|
| 0.10 | 1.1e9 | 2.2e8 | ~1e11 |
| 0.20 | 6.8e7 | 1.4e7 | ~3e10 |
| 0.35 | 7.4e6 | 1.5e6 | ~3e9 |
| 0.50 | 1.8e6 | **3.9e5** | 1.8e8 |

- **Guardrail A:** NEVER feasible (≤1e6) at realistic drift `s≤0.3`. readout-only stays sub-floor across the whole
  sweep (crossover `s*>0.5`); readout+reset reaches feasibility only at `s≈0.45` (feasible at `s=0.5`) — **beyond the
  realistic ceiling.**
- **Guardrail B:** `N_det_B ≈ 450–4500× N_det_A` everywhere — the 1/f-vs-matched-slow-RTN lag-2 shape gap is only
  ~6% of the source autocov (`C_x(2)=0.696` vs `C_x(1)²=0.653`) ⇒ **B NEVER lands.**

**VERDICT: HONEST CAP (G4-consistent registered STOP).** The Class-1 SPAM route's passive-record multi-time imprint
is (A) sub-1e6-floor for realistic readout drift AND (B) Markov-k-trivial (not separable from a slow-RTN) even where
detectable. **Do NOT hard-build the full Class-1 ancilla-axis architecture on this observable.**

**Registered-prediction adjudication (predict-before-measure, honest):** Pred-1 (readout-only NO-GO, `s*≈0.5–0.65`)
**CONFIRMED** (`s*>0.5`). Pred-2 (readout+reset `s*≈0.25–0.35`) **MISS → finding** (actual `s*≈0.45`, worse than
predicted — the adjacent-round + nonlinear structure I under-modeled in the prediction; recorded, not re-fit).
Pred-3 (Guardrail B fails, `N_B≫N_A`) **CONFIRMED**. Pred-4 (overall honest cap) **CONFIRMED.**

**What could still land (NOT this observable; for a future scope decision, not built):** (i) a JOINT multi-lag
discriminator (lags 2..R together, not a single lag-2) — modestly stronger but B's ~6% gap is intrinsic; (ii)
Class-2 (CZ depol) siting; (iii) a genuinely stronger source (Harper-Flammia ~2× LER regime) rather than mild 1/f;
(iv) a richer non-Gaussian source whose 1/f-vs-Markov gap is larger. D1 (the SPAM sensitivity anchor) remains a user
decision; this go/no-go used a declared class-(c) `s`-sweep.

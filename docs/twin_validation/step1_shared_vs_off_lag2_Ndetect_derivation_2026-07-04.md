# Track 1 Step 1 — NEW closed-form `N_detect` for the **absolute lag≥2 shared-vs-off** correlation

**Status: DERIVATION (predict-before-measure), 2026-07-04.** Every prediction below (direction, magnitude,
scaling, verdict) is written **BEFORE** the committed script
`outputs/twin_validation/step1_shared_vs_off_lag2_Ndetect.py` runs. A miss is a FINDING, not a re-fit.
This is the analytic answer to the session's original question — *is the non-Markovian error visible on the
syndrome record, at what source strength / error class* — for the CORRECTED observable and null (handoff §1
error A). It **replaces**, and does not fork, the retracted shared-minus-markovian sizing of
`g6_null_feasibility_from_constants.py::record_N_sizing` (which hardcodes `N∈[1.1e10,1.2e15]`).

**Scope (binding, [[feedback-simulator-is-goal-twin-is-next]]):** a fixed-statistic legitimacy sizing — does
a FIXED `p_ij` estimator separate the shared arm from its structural-zero (off) null? IN scope. No mechanism
recovery / `do()` / active characterization (the twin) is done or implied.

**Epistemic frame ([[feedback-anti-toy-ground-truth-protocol]]):** there is NO physical ground truth —
everything is simulation; the teacher is a noise model we *specify*. The closed forms below are FORMAL
derivations of that specified model (they catch mis-registration / mis-sizing, never certify correspondence
to nature). Each item is tagged **(a) exact** / **(b) prediction band** / **(c) heuristic gate**.

**D1 resolved (user, 2026-07-04): sweep + share-calibrated anchor.** `N_detect` is analytic in the source
amplitude, so we report it as a CURVE over `amplitude_radns = 1e-4 → the channel-baseline endpoint`
(`γφ → G2_GAMMA_PHI = 1/30000`, T2=30µs), and read the verdict at the share-calibrated realistic band. There
is no transferable Google 1/f amplitude to cite as a point (the repo's own theory-first deliverable
`error_budget_sourced_table.md §4–5`: Bylander's flux-qubit `A_Φ` is declared non-transferable; the grounded
convention is amplitude share-calibrated to the data-idle budget ≈0.9e-2/cycle). Bylander 1101.4707 is cited
only for the 1/f `α≈0.9` shape.

---

## 0. What is new vs g6 (the two fixes of error A, made precise)

The retracted g6 sizing measured `shared − markovian` (an exchangeable permutation null retaining ~73% of the
covariance) at **lag 1**. Two changes here:

1. **Null:** `shared` vs **`off`** (`off_source()`, Θ(0)), an **absolute** comparison to a structural zero —
   NOT a difference from an exchangeable null. (handoff §1 error A part 2, the decisive half.)
2. **Lag:** the **absolute lag ≥ 2** correlation, where the MA(1) instrument floor is `0` EXACTLY, so the
   whole shared-arm lag≥2 signal is source-induced (Kam multi-time; report a vector over lags 2..L).

The consequence — derived in §2 — is that the ~73%-retaining subtraction penalty is removed, and the signal
that the subtraction used to CANCEL (the permutation-invariant common-mode) is now KEPT. That is where the
orders-of-magnitude come from.

## 1. The observable and the structural-zero null (a-exact)

Round-delta detector `D_{c,r} = m_{c,r-1} ⊕ m_{c,r}` (MA(1); g6 §1). Off arm (Θ(0), i.i.d. measured bits):

- `p_ij(lag 1) = μ = p_ro + p_rs − 2 p_ro p_rs ≈ 0.0149` (structural, nonzero);
- **`p_ij(lag ≥ 2) = 0` EXACTLY** (no shared measured bit ⇒ `Cov = 0` ⇒ `p_ij = ½ − √¼ = 0`).

So the legitimacy signal is the **absolute shared-arm `p_ij(lag≥2)`, tested against the off arm's exact 0.**
`p_ij` and its SE are the canonical METRICS-ledgered `qec_twin.hardware.pij.spitz_pij_exact` /
`spitz_pij_delta_se` (Spitz Eq.13 exact form + delta-method per-shot SE, `SE ∝ 1/√N`).

## 2. The shared-arm lag≥2 covariance — the DECOMPOSITION (the load-bearing derivation)

For lag `L ≥ 2`, `D_r` and `D_{r+L}` share **no** measured bit, so conditional on the per-round rate
sequence the two are independent. By the law of total covariance the **only** surviving term is the
covariance of the conditional delta rates `q_r = E[D_r | rates] = μ_{r-1}+μ_r−2μ_{r-1}μ_r` over shots:

$$ \mathrm{Cov}(D_r, D_{r+L}) \;=\; \underbrace{\mathbb E[\mathrm{Cov}(D_r,D_{r+L}\mid\text{rates})]}_{=\,0\ (L\ge2,\ \text{MA(1)})} \;+\; \mathrm{Cov}_{\text{shot}}\big(q_r,\,q_{r+L}\big). $$

Write the per-round measured-bit flip prob as `μ_r = μ_instr(shot) + p_deph,r`, where **(S-1)** the
readout/reset instrument is held at the per-**trajectory MEAN** (a shot-constant `μ_instr(shot)`), and
`p_deph,r = ½(1−e^{−γφ_r τ_eff})` is the per-round dephasing flip carried by the source-modulated `γφ_r`
(X-checks only; Z-checks carry `μ_instr` alone — g6 §2). Substituting and keeping leading order,

$$ \boxed{\ \mathrm{Cov}_{\text{shot}}(q_r,q_{r+L}) \;=\; \underbrace{\mathrm{Var}_{\text{shot}}\!\big(Q_{\text{instr}}\big)}_{\textbf{common-mode: flat in }L,\ \tau_\text{eff}\text{-FREE}} \;+\; \underbrace{a^2\big[C_\delta(L{-}1)+2C_\delta(L)+C_\delta(L{+}1)\big]}_{\textbf{memory: decays in }L,\ \propto\,\tau_\text{eff}^2}\ } $$

with `Q_instr(shot) = 2μ_instr(1−μ_instr)`, `a = 1−2μ_instr ≈ 0.97`, and `C_δ(k) = Cov(p_deph,r, p_deph,{r+k})`
inheriting the source autocovariance `C_z(k) = Σ_j v_j² e^{−2γ_j k}` (`OneOverFDriftSource.analytic_psd`'s
time-domain partner) through the `γφ(z)` map.

**Two physically distinct pieces, both absent from `off`, both vanishing in the motional-narrowing (Markovian)
limit — but NOT equivalent:**

| piece | channel | lag shape | `τ_eff` | scales as | what it proves |
|---|---|---|---|---|---|
| **common-mode** `Var(Q_instr)` | readout/reset (instrument / SPAM-flavoured) | **flat** (quasi-static / DC) | independent | `∝ amp²` | shared **slow** disorder (a static shared offset would forge it) |
| **memory** `a²·ΣC_δ` | `γφ` (Kam **Class-0** data dephasing) | **decaying** | `∝ τ_eff²` | `∝ amp²` | genuine **finite-correlation-time** 1/f memory (unforgeable by a static offset) |

The retracted `shared − markovian` **cancels the common-mode** (both arms carry it) and keeps only ~27% of
the memory ⇒ the `1.1e10–1.2e15` "sub-floor". `shared − off` **keeps the common-mode.** At slice-1 constants
the common-mode (g6: `8.68e-5`, rate² units) dominates the memory (g6: `Δγ(1)=5.58e-12` × slope²≈`7e-8`) by
**~1200×**. So the shared-vs-off lag≥2 signal is **common-mode-dominated and `τ_eff`-free.**

## 3. The NEW closed-form `N_detect` (a-exact given the covariance)

Marginal delta rate `q̄ = E[D_r]` (pooled mean of the `q` matrix). At lag `L`:
`mᵢ = mⱼ = q̄`, `m_ij = q̄² + Cov_shared(L)`. Then, canonical Spitz:

```
p_ij(L)  = spitz_pij_exact(q̄, q̄, q̄²+Cov)          # off: Cov=0 ⇒ p_ij=0 exactly
SE(N)    = spitz_pij_delta_se(q̄, q̄, q̄²+Cov, N) = SE(1)/√N
N_detect = ( z · SE(1) / p_ij(L) )²                 # z=3; smallest N with p_ij/SE ≥ z
```

Two pooling conventions are reported (the truth is between them):
- **conservative** — a single detector, single lag pair per shot ⇒ `N_shots = N_detect`;
- **optimistic** — pool `n_stab · (R−L)` round-pairs × the lags 2..L as independent ⇒
  `N_shots = N_detect / n_pairs`.

Because `Cov_shared ∝ amp²`, `p_ij ∝ amp²` and (at fixed `q̄`) `SE(1)` is ~amplitude-independent, so

$$ \boxed{\ N_{\text{detect}} \ \propto\ \text{amp}^{-4}\ } \quad\text{(steep — the sweep matters).} $$

`N_detect` is computed **separately** for the **total** (common-mode + memory) and for the **memory-alone**
(common-mode removed) covariance — because they answer different questions (§5).

## 4. The amplitude sweep + the endpoint anchor (D1)

Sweep `amplitude_radns ∈ {1e-4 (slice-1), 1.5e-4, 2e-4, endpoint, 5e-4, 1e-3}`. The **endpoint** is the
amplitude at which the source-modulated `γφ` reaches the channel baseline `G2_GAMMA_PHI = 1/30000` (T2=30µs,
`frontend/axis1_bridge.py`): via `γφ = γφ_base·e^{sens·x}`, `x=z/z_scale`, that is `e^{0.35·x}=75000/30000=2.5`
⇒ `x≈2.62` ⇒ `amplitude ≈ 2.6e-4` (RMS; the script finds it by where `mean(γφ)` crosses `1/30000`). The
share-calibrated realistic band (data-idle `p_expt≈0.9e-2/cycle`) coincides with this endpoint for
`τ_eff≈540 ns` (`0.5·γφ·τ_eff≈0.9e-2` at `γφ=1/30000`) — inside the `τ_eff` bracket.

## 5. PREDICTIONS (predict-before-measure — numbers written before the run)

- **P0 (a-exact, control).** Off arm: `p_ij(lag≥2) = 0` exactly (i.i.d.-bit MA(1) self-check reproduces it);
  `p_ij(lag1) = μ ≈ 0.0149`.
- **P1 (b — the headline).** Shared-vs-off **total** `p_ij(lag≥2)` at slice-1 `amp=1e-4` is nonzero,
  `≈ 1e-4`, giving `N_detect(total, single-pair) ≈ 1e6` (`z=3`), i.e. **4–9 ORDERS below** the retracted
  `1e10–1e15`. With optimistic pooling (`n_stab·(R−L)·lags ≈ O(50)`) `N_shots ≈ 1e4–2e4`. **⇒ Class-0 is
  VISIBLE vs off at feasible N.** The `1e10–1e15` "sub-floor / unmeasurable" verdict **does NOT stand**
  (error A confirmed: the killer was the exchangeable-null subtraction, not the physics).
- **P2 (b — the honest caveat, the real finding).** The visible total is **common-mode-dominated**
  (quasi-static instrument/SPAM shared disorder). The **memory-alone** (decaying, finite-τ, `γφ`/Class-0)
  `N_detect(memory, single-pair) ≈ 1e11–1e13` at slice-1 — essentially the retracted number (as it must be:
  the retracted sizing WAS ~the memory). ⇒ the **finite-time-memory-specific** non-Markovian fingerprint is
  NOT feasibly visible at Class-0 slice-1 amplitude.
- **P3 (b — scaling).** `N_detect ∝ amp^{-4}`. At the endpoint (`amp≈2.6e-4`, `γφ→1/30000`),
  total `N_detect` drops ~`(2.6)^4 ≈ 46×` → single-pair `~2e4`, pooled `~few×10²` (deeply feasible); the
  memory-alone drops to `~1e9–1e11` — **still infeasible at Class-0 even at the realistic endpoint.**
- **P4 (b — the D3 fork, decided by the numbers).** Basic visibility (total vs off): **Class-0 suffices.**
  The finite-time-memory-specific claim: **Class-0 does NOT suffice at any amplitude in the physical sweep**
  ⇒ routes to the **Class-1/2 ancilla-axis re-siting** (Track 3, `h2 §7.B`) — a declared dependency, NOT a
  "sub-floor is faithful" verdict.
- **P5 (c — controls collapse).** Motional-narrowing (fast source, `γ_sw ↑`): both common-mode and memory
  `→ 0` (ratio `< 1e-2`) — confirming both are non-Markovian (slow-correlation) signatures, not artifacts of
  a stationary rate. A planted quasi-static per-shot latent moves the total; a planted AR(1) memory moves the
  memory-alone.

**Falsifier (whole derivation).** If shared-vs-off `p_ij(lag≥2)` total at slice-1 is STILL
`N_detect ≥ 1e10` (no better than the retracted number), the common-mode is not being kept and error A's
null-fix is wrong — a FINDING.

## 6. Controls (reuse; controls-first)

- **off / structural zero** — `Cov(lag≥2)=0` by the a-exact MA(1) identity + i.i.d.-bit self-check (no cube).
- **PC (positive):** a planted quasi-static per-shot common latent must move the **total**; a planted AR(1)
  per-round rate must move the **memory-alone** — validates that each `N_detect` responds to its own signal.
- **Motional-narrowing collapse (P5):** a fast `OneOverFDriftSource` variant (`γ_min,γ_max ×100`) ⇒ both
  pieces `→ 0`.

## 7. Epistemic classes + bounded simplifications

- **(a) exact:** the MA(1) off structural zero (`p_ij(lag≥2)=0`, `p_ij(lag1)=μ`); the law-of-total-cov
  decomposition; the Spitz Eq.13 identity + its delta-method SE; `N_detect=(z·SE(1)/p_ij)²` given the covariance.
- **(b) bands:** P1–P4 `N_detect` values (they carry the source-MC covariance + the `τ_eff` bracket).
- **(c) gates:** `z=3`; `N ≤ FEASIBLE_N = 1e6`; the endpoint/share-calibrated anchor; the motional ratio `<1e-2`.
- **Bounded simplifications (declared):**
  - **S-1 trajectory-mean instrument** — the common-mode magnitude is tied to holding readout/reset at the
    per-trajectory mean (a single-slot-instrument choice). A per-round-fluctuating instrument would reshape
    the common-mode. **⇒ the "Class-0 visible" headline rests partly on a modeling choice; the memory-alone
    (P2/P4) does NOT and is the model-choice-robust statement.** Flagged for the user (§8).
  - **`τ_eff ∈ {50,225,1000} ns`** — the ONE quantity not fixed by a committed constant. The TOTAL headline is
    `τ_eff`-insensitive (common-mode dominates & is `τ_eff`-free); the memory-alone is `τ_eff`-sensitive
    (bracketed).
  - **linearized `γφ(z)`** analytic cross-check of the memory autocov (~15% loose vs the exact `exp` map;
    g6 §9) — a consistency check, not a tight GT; the source-MC uses the exact map.
  - **d3 4q/5q fixtures, R=12** — feasibility per the fixtures; surface scaling later.

## 8. The one judgment for the user (surfaces after the run)

The numbers force a clean either/or the user should rule on (this is the design's D3, now decided by the
sizing rather than assumed): **is "Class-0 visible via the quasi-static instrument common-mode" an acceptable
legitimacy statement (soft: lag-flat, S-1-dependent, forgeable by a static offset), or must the visible signal
be the finite-time DECAYING memory (hard: unforgeable, model-robust) — which requires the Class-1/2 re-siting
(Track 3)?** Step 1 answers *what is visible where*; this scope call decides whether Track 3 opens now.

---

## 9. RESULTS vs predictions (post-run 2026-07-04; predictions §5 left INTACT)

Committed evidence: `outputs/twin_validation/step1_shared_vs_off_lag2_Ndetect.py` (run via
`outputs/run_step1_shared_vs_off_lag2.sh`, `python-exit=0`), artifact
`outputs/twin_validation/step1_shared_vs_off_lag2_Ndetect.json`,
`content_hash=5c3c923a4fcf9a6486da7d7c0ae00e4e6db815617509b8dfbf2925454088b4b0`,
`GATE_RESULT step1_shared_vs_off_lag2 CLASS0_VISIBLE`. `N_traj=20000`, `R=12`, `z=3`, `tau_eff=225 ns` nominal.
Covariances are smooth-monotone `∝ amp²` across all 7 amplitudes (⇒ signal, not MC noise). All numbers below
are printed by the script.

| # | prediction | result | verdict |
|---|---|---|---|
| P0 | off `p_ij(lag≥2)=0`, `p_ij(lag1)=μ` | lag1 `0.014889≈μ`, lag2 `−7.5e-7≈0` | **CONFIRMED (a-exact)** |
| P1 | total shared-vs-off visible, `N_detect≈1e6` single / `~1e4` pooled; 4–9 orders below `1e10–1e15` | slice-1: `p_ij(l2)=1.16e-4`, single `1.05e6`, **pooled `5.85e4`**; endpoint single `~2e3`, pooled `114` | **CONFIRMED — Class-0 VISIBLE; retracted sub-floor does NOT stand (error A confirmed)** |
| P2 | visible total common-mode-dominated | `cov_tot(l2)=1.01e-4` vs `cov_mem(l2)=7.7e-7` (**~130×**); common-mode `τ`-free | **CONFIRMED** |
| P3 | `N_detect ∝ amp^{-4}` | `N(1e-4)/N(2e-4)=21.3` (>16; the extra steepness = the `exp`/logit map nonlinearity) | **CONFIRMED (slightly steeper)** |
| P4 | memory-alone stays infeasible at Class-0 even at endpoint ⇒ Class-1/2 | **MISS.** At endpoint `~4e-4`: memory single `8.3e6` (infeasible) but **pooled `4.6e5` (feasible)**; `τ`-dependent (slice-1 memory single: `5.8e12`@τ50, `1.7e10`@τ225, `7.8e7`@τ1000) | **MISS → FINDING: memory-alone STRADDLES feasibility at the realistic endpoint (feasible pooled, infeasible single-pair, `τ`-dependent) — NOT cleanly gated to Class-1/2** |
| P5 | motional-narrowing collapse `<1e-2` | **MISS.** `×100` factor: `cov_fast/cov_slow = 0.16` (6× down, direction right, not `<1e-2`) — `×100` under-averages at `R=12` (fastest fluctuator still has lag-2 autocorr `e^{-2}≈0.14`) | **MISS → FINDING: the collapse control needs a larger narrowing factor / more rounds to reach the full Markovian limit; trend correct** |

**Net answer to the session question — the non-Markovian imprint IS visible on the syndrome record:**
- **Robustly:** the TOTAL shared-vs-off `p_ij(lag≥2)` is feasible already at slice-1 (`pooled 5.85e4`) and
  deeply feasible at the realistic endpoint (`pooled 114`, single-pair `~2e3`) — **4–9 orders below the
  retracted `1e10–1e15`.** The `1e10–1e15` "sub-floor / unmeasurable" verdict is **refuted**; the killer was
  error A (the exchangeable-null subtraction cancelling the common-mode), not the physics. `τ_eff`-insensitive.
- **The robustly-visible part is the quasi-static instrument/SPAM common-mode** (cov `~130×` the memory), a
  shared-slow-disorder signature — legitimate vs off, but lag-flat and S-1-modeling-dependent.
- **The finite-time MEMORY-alone** (the sharper, model-robust non-Markovian fingerprint) is **borderline at
  the realistic endpoint**: feasible under optimistic pooling (`4.6e5`), infeasible single-pair (`8.3e6`), and
  `τ_eff`-dependent. So it is NOT cleanly "needs Class-1/2" (P4 predicted that) — it sits on the boundary.

**Two registered misses (theory-first: findings, not re-fits):** P4 (memory borderline, not infeasible) and
P5 (motional collapse partial at `×100`). Both are honest outcomes recorded here; neither is walked back.
The P5 control should be re-run as a narrowing SWEEP (factor `×1 → ×10⁴`) to exhibit the monotone `→0`
Markovian limit; the P4 straddle should be resolved by reporting the conservative (single-pair) and optimistic
(pooled) bracket explicitly rather than a single gated verdict.

# H2 — G4 effect-size + threshold pre-registration (theory-first, predict-before-measure)

> **⚠ READ §6 FIRST (2026-06-26 reconciliation).** A third-method exact cross-check + a theory-first
> literature catch (Kam et al. arXiv:2410.23779) OVERTURN the §4 headline. §4's "single-RTN `ρ_res≈0.006–0.008`,
> recommend single-RTN" is RETRACTED (it was forward-filter sampling noise; the exact value is `O(1e-4)`). More
> importantly, the registered G4 **2-point** detection-event-correlation observable is shown — by the on-disk
> paper AND our exact HMM enumeration — to be a **known-insufficient discriminator** of RTN vs 1/f at feasible
> Markov-`k`; G4's observable must be re-registered to a **multi-time / timelike-string** signature before the
> build. §0–§5 are kept as the derivation record; §6 is the binding registration.

**Status:** pre-registration. The first technical work item of the QEC-coupling-simulator slice #1
(`qec_coupling_simulator_build_contract.md`, RESOLVED-DECISION H1 + OPEN-QUESTION H2). Pure derivation +
numbers — **no `src/`, no code-experiment**. Predictions are written and classed BEFORE any simulator run.
Binds to: `qec_coupling_simulator_build_contract.md` (G4/G5/G6 record-level gates), `full_error_coupling_prereg.md`
(§5.1 P1–P4), `nonmarkovian_coupling_constraint_ledger.md` (C7/C8a exact autocorr, C8b observable band),
`outputs/teacher_prereg/nm_source.py` (exact RTN/1-f forms), `docs/METRICS.md` (epistemic-status declaration).

**What G4 needs (the binding subtlety, restated from the prior red-team).** The headline observable is a
**detection-event LONG-RANGE correlation** that the **best converged Markov-k baseline CANNOT capture**.
A single RTN's latent error-rate autocorrelation is the EXACT exponential `e^{-2γ_sw|τ|}` (C7/C8a) — and an
exponential two-point function is *reproduced by a Markov-1 chain on the rate*. So the **bare round-to-round
detection autocorrelation of a single RTN is Markov-1-trivial** and CANNOT be the G4 signal. The genuine
non-Markov-k signal must come from EITHER **(a)** a **1/f source** (sum-of-RTNs → sum-of-exponentials → a
power-law correlation tail that any finite Markov-k truncates, leaving a residual), OR **(b)** the fact that
the hidden 2-state RTN observed through binary detectors is a **hidden Markov model (HMM)** whose emitted
binary process is **infinite-order Markov** — the best Markov-k leaves a residual that decays geometrically
in `k`. This document quantifies **the residual a best converged Markov-k leaves** (the actual G4 signal,
not the raw correlation) and **the shot-noise floor** to detect it, and registers the `(v, γ_sw, t_cycle, k)`
band + the `|z|` threshold + the shot budget as a class-(b) prediction.

**Epistemic frame (METRICS.md).** Marked per item below; defaults to **(c)** if undeclared. Summary:
- **(a) exact** — the RTN latent autocorr `e^{-2γ_sw|τ|}`; the sum-of-Lorentzians 1/f spectrum; the
  single-RTN detection-autocorr being a single exponential; the linear source→detection map identity.
- **(b) prediction band** — every residual MAGNITUDE `ρ_res(k)`, the residual decay base `r`, the
  recommended `(v, γ_sw, t_cycle)` operating band, and the required-N table entries (falsifiable bets;
  a miss is a finding, never later cited as fact).
- **(c) gate / decision** — the `|z| ≥ 3` (screen) / `|z| ≥ 5` (headline) thresholds, the choice of lag set,
  the `B_eff` discount convention, and the single-RTN-vs-1/f source recommendation for slice #1.

---

## 0. Setup — source → per-round detection probability (the linear map)

**(a) exact (map identity), (c) the linearization scope.** Convention fixed by `nm_source.py` (§5.1, FIXED):
`ξ(t) ∈ {+1,−1}`, switching rate `γ_sw`, latent autocorr `⟨ξ(0)ξ(τ)⟩ = e^{−2γ_sw|τ|}` (C7/C8a, exact);
qubit-frequency-mediated `Θ(z_t)` co-modulates `ζ` (ZZ) and `γφ` (T2). Sample the source ONCE per cycle at
`t_r = r·t_cycle`. The per-round detection-event probability of detector `b` is the source-modulated value

```
p_{r,b} = p_0,b + (∂p_b/∂θ)·δθ(z_{t_r}) ≡ p_0,b + s_b·ξ_r           (single RTN)
p_{r,b} = p_0,b + Σ_k s_{b,k}·ξ_{k,r}                                (1/f: sum of RTNs)
```

with `s_b ≡ (∂p_b/∂θ)·v·(integration factor)` the **per-round detection-probability swing** induced by one
fluctuator flip (units: probability). The `ξ_r` is the **discrete-time** RTN sampled at the cycle rate; its
per-cycle retention is the exact latent autocorr at one cycle:

```
a ≡ ⟨ξ_r ξ_{r+1}⟩ = e^{−2γ_sw t_cycle}                              [EXACT, C8a-latent — (a)]
```

`a∈(0,1)`: `a→1` slow source (strong cross-round memory), `a→0` fast source (memory gone, motional narrowing).
P2/C8a anchor: `obs round-corr ≈ a` under a linear/monotone map (the C8b band centers here). The
linearization `p = p_0 + s·ξ` is the **(c)** observation-map scope; the true syndrome/readout map is
nonlinear (C8b band width), but the *correlation structure* (single-exp vs power-law) is map-shape-invariant,
which is what G4 tests.

**Detection-event variance / SNR per round (a, definition).** A single detector is Bernoulli with mean `p_0`,
so its variance is `p_0(1−p_0)`; the source contributes signal variance `s²` (RTN, `⟨ξ²⟩=1`). Define the
**per-round source SNR** carried by `B` detectors that all see the same `ξ_r`:

```
SNR_round ≡ B·s² / (p_0(1−p_0))                                      [governs the HMM filter speed — (a)]
```

For `p_0≈0.1`, `B≈8` (d3 has ~8 detectors/round), `s≈0.02` ⇒ `SNR_round ≈ 0.036` (weak per-round info);
`s≈0.05` ⇒ `SNR_round ≈ 0.22` (moderate).

---

## 1. The detection-event autocorrelation `C_det(τ)` — RTN vs 1/f

**(a) exact (the linear-map propagation); (b) the magnitude prefactor.**

Propagate `p = p_0 + s·ξ` through the Bernoulli emission. The normalized (Pearson) detection-event
autocorrelation at lag `τ` (rounds), pooling over shots, is

```
C_det(τ) = [ s² · ⟨ξ_r ξ_{r+τ}⟩ ] / [ p_0(1−p_0) + s² ]
         = ρ_0 · a^{|τ|}          (single RTN),   ρ_0 ≡ s²/(p_0(1−p_0)+s²)     [EXACT shape — (a)]
```

i.e. a **single geometric / exponential** in `τ` with base `a = e^{−2γ_sw t_cycle}` and amplitude
`ρ_0 = SNR_round/B / (1 + SNR_round/B) ≈ s²/(p_0(1−p_0))` for small `s`. **Verified numerically**
(scratchpad `h2_verify.py`, N=4e5, g·t_cycle=0.05 ⇒ a=0.905): measured `C_det(τ)` successive-lag ratios
`{0.86, 0.97, 0.92, 0.83}` ≈ `a=0.905`, amplitude `ρ_0≈0.009` for `s=0.03, p_0=0.1` (predicted
`0.03²/(0.1·0.9)=0.010`). **This is the Markov-1-trivial part: a pure geometric two-point function is
reproduced exactly by a Markov-1 model on the rate** — so the *raw* `C_det(τ)` of a single RTN is NOT a
G4 signal.

For the **1/f source** (sum of `N` RTNs, log-spaced `γ_k`, constant `v_k`; `nm_source.make_1f_params`,
spectrum `S(ω)=Σ_k v_k²·4γ_k/((2γ_k)²+ω²)`, C6, exact),

```
C_det(τ) ≈ Σ_k ρ_{0,k} · a_k^{|τ|},   a_k = e^{−2γ_k t_cycle}     [SUM of exponentials — (a) shape]
```

a **multi-exponential = power-law-like** decay over the decade band: no single base `a`. **Verified**
(`h2_verify.py`, 6 RTNs spanning `γ_k·t_cycle ∈ [0.005, 0.5]`): the near-range slope fits an effective
single exponential `a_eff≈0.885`, but the residual ABOVE that single-exponential GROWS with lag
(`+0.0000` at τ=1 → `+0.0009` at τ=8 → `+0.0022` at τ=16), and the successive-lag ratios RISE toward 1
(`{0.85, 0.92, 0.96, …, 1.01, 0.95}`) — the heavy-tail signature. **This power-law tail is what survives
any finite Markov-k** (Markov-k matches the near-range exponential; the slow-`γ_k` tail leaks past lag `k`).

---

## 2. THE G4 SIGNAL — the residual a best converged Markov-k leaves (`ρ_res(k)`)

This is the load-bearing derivation. "Best converged Markov-k" = the maximum-likelihood order-`k` predictor
of the next round given the last `k` rounds of `{det}` (G5's binding rival; it captures ANY finite-order
record correlation). The G4 signal is the gap between the **optimal infinite-order predictor** (which, for
this generative model, is the exact HMM forward filter over the hidden source) and the order-`k` predictor.

### 2a. Single RTN as a hidden Markov model — residual decays as `r^k`, `r ≲ a`

**(b) prediction band (the magnitude + base), built on an (a)-exact filter.** The hidden 2-state RTN seen
through `B` binary detectors is an HMM; the emitted binary process is **infinite-order Markov**. The optimal
predictor is the exact forward filter (posterior over `ξ_r` given all past counts); a Markov-k predictor
resets the posterior `k` rounds back. The **per-round residual** (RMS difference between the optimal and the
order-k predicted detection probability) is the imprint Markov-k cannot capture.

Theory: each extra round of history sharpens the hidden-state posterior by the per-round information
`∝ SNR_round` and is propagated forward attenuated by the retention `a`. So the residual beyond order `k`
decays **geometrically**:

```
ρ_res(k) ≈ ρ_res(1)·r^{k−1},   r ≈ a·(1 − c·SNR_round),   0 < r ≤ a = e^{−2γ_sw t_cycle}   [(b) band]
```

— bounded above by `a` (weak per-round info: `r→a`), dropping below `a` as the per-round measurement
resolves the hidden state faster (strong `SNR_round`). **EXACT forward-filter verification** (no sampling
noise, `h2_analytic.py` / `h2_base.py`, R=4000–6000):

| regime (g·t_cyc, B, s) | `a=e^{−2g t_c}` | SNR_round | fitted base `r` | `ρ_res(k=2)` | `ρ_res(k=4)` |
|---|---|---|---|---|---|
| (0.05, 8, 0.02) | 0.905 | 0.036 | **0.879** | 0.0055 | 0.0043 |
| (0.05, 8, 0.05) | 0.905 | 0.222 | **0.786** | 0.0197 | 0.0122 |
| (0.10, 8, 0.02) | 0.819 | 0.036 | **0.794** | 0.0032 | 0.0020 |
| (0.02, 8, 0.02) | 0.961 | 0.036 | **0.933** | 0.0090 | 0.0078 |
| (0.20, 8, 0.02) | 0.670 | 0.036 | **0.649** | 0.0014 | 0.0006 |
| (0.05, 4, 0.02) | 0.905 | 0.018 | **0.891** | 0.0043 | 0.0034 |

Confirms `r ≈ a` at weak SNR (0.879 vs 0.905; 0.933 vs 0.961; 0.891 vs 0.905) and `r < a` as SNR grows
(0.786 vs 0.905 at SNR=0.22). **Consequence for G4 (binding):** because the single-RTN residual decays as
`a^k`, a Markov-k with `k` a few × the source correlation length `1/(2γ_sw t_cycle)` rounds makes `ρ_res(k)`
negligible. So a single RTN gives a genuine but **finite-order-exhaustible** residual: G4 must pick a lag/`k`
where `ρ_res(k)` is still above shot noise, OR (preferred) use a source whose residual does NOT decay
geometrically.

### 2b. 1/f source — a power-law residual survives EVERY finite `k`

**(b) prediction band.** For the sum-of-RTNs 1/f source there is no single retention `a`; the slow
fluctuators (`γ_k·t_cycle ≪ 1`, `a_k→1`) contribute a correlation tail that NO finite-order Markov-k can
absorb. The order-k residual inherits the power-law: instead of `r^k`, it decays as a slow power law in `k`
set by the spectral exponent (≈ `1/f` ⇒ `ρ_res(k) ~ k^{−α}`, `α≈O(1)`). This is the **non-finite-order**
signal — the residual a best converged Markov-k leaves does NOT vanish as `k` grows (it saturates at the
floor set by the slowest mode `γ_min`). The G4 imprint is the **persistent residual** at lags
`τ ≫ 1/(2γ_eff t_cycle)`, where `C_det` is still positive but every Markov-k of practical order has
truncated. **Verification (§1):** the 1/f `C_det` residual above the best near-range single-exponential
grows to `+0.0022` at lag 16 and the lag-ratios rise to ~1 — the tail Markov-k leaves.

### 2c. When is `ρ_res` non-negligible (not Markov-k-trivial)?

**(b) band.** Combining: the residual is **non-trivial** (worth a G4 run) when, at the largest practical
baseline order `k*` (say `k*≈6`, beyond which the Markov-k itself is shot-starved on `{det}`):

- **single RTN:** need `a^{k*−1}·ρ_0` above shot noise ⇒ slow source `a ≳ 0.8` (i.e. `γ_sw t_cycle ≲ 0.11`)
  AND a non-tiny swing `s` so `ρ_0 = s²/(p_0(1−p_0))` is not buried. At `g·t_cyc=0.05, s=0.05`:
  `ρ_res(k=6)≈0.0075` — detectable (§3). At `g·t_cyc=0.2` (fast): `ρ_res(k=4)≈0.0006` — sub-shot-noise at
  realistic N (Markov-k-trivial → REJECT this regime, consistent with C8b fast-limit collapse to 0).
- **1/f:** the tail survives all `k` ⇒ the *floor* residual `ρ_res(∞) ~ ρ_0·(slow-mode fraction)` is the
  registered signal; with a decade of `γ_k` and constant `v_k`, the slowest 2–3 modes hold ~30–40% of the
  amplitude, so `ρ_res(k*) ≈ 0.3–0.4·ρ_0` — independent of `k*` (the qualitative difference from RTN).

---

## 3. The shot-noise floor — N and R to reach the `|z|` threshold

**(a) the estimator SE (definition); (b) the required-N entries; (c) the `|z|` thresholds + `B_eff`.**

Estimate the residual correlation `ρ_res` at lag `τ` as a sample statistic over independent round-pairs.
A sample Pearson correlation over `M` independent pairs has, under the null (no residual after the Markov-k
fit), standard error `SE ≈ 1/√M`. Hence

```
|z| ≈ ρ_res · √(M_eff),   M_eff = N · (R − τ) · B_eff                [estimator SE — (a)]
N_required = (|z|_thr / ρ_res)² / [ (R − τ) · B_eff ]                [(b) numbers, (c) thresholds]
```

`N` = shots, `R` = rounds/shot, `B_eff` = **effective independent detector count per round**. Because the
shared source `z_t` correlates the `B≈8` d3 detectors, `B_eff ≤ B`; register a **bracket** `B_eff ∈ [1, 8]`
(C8b-style: underdetermined ⇒ bracket, not freeze), with **`B_eff = 2` the representative arm** (strong
cross-detector sharing) and `B_eff = 8` (independent) / `B_eff = 1` (fully shared) the bounds. Thresholds
(class **(c)** gates): `|z| ≥ 3` = screen, `|z| ≥ 5` = headline G4 pass.

**Required N (shots), R = 30, τ = 4 (representative arm `B_eff = 2`):**

| `ρ_res` | N for `|z|=3` | N for `|z|=5` |
|---|---|---|
| 0.0500 | 69 | 192 |
| 0.0200 | 433 | 1,202 |
| 0.0100 | 1,731 | 4,808 |
| 0.0050 | 6,923 | 19,231 |
| 0.0020 | 43,269 | 120,192 |
| 0.0010 | 173,077 | 480,769 |
| 0.0005 | 692,308 | 1,923,077 |

**Best case `B_eff = 8`, R = 30, τ = 4** (divide above by 4): `ρ_res=0.005` → N=1,731 (`|z|=3`) / 4,808
(`|z|=5`). **Conservative `B_eff = 1`, R = 20, τ = 8** (every detector fully shared, deep lag):
`ρ_res=0.005` → N=30,000 (`|z|=3`) / 83,333 (`|z|=5`); `ρ_res=0.002` → N=187,500 / 520,833.

All entries verified (`h2_shotnoise.py`). The grounding shot range `N ∈ 1e4–1e6` covers detection down to
`ρ_res ≈ 0.001–0.002` at the representative `B_eff=2`, and to `ρ_res ≈ 0.0005` at `B_eff=8`.

---

## 4. The registered class-(b) band + the slice-#1 source recommendation

**(b) operating band; (c) source choice.**

**Registered operating regime (class-(b) prediction band — the G4 bet).** Slice #1 must operate where the
residual is BOTH above shot noise at the planned N AND not Markov-k-trivial:

```
γ_sw·t_cycle ∈ [0.02, 0.11]   ⇔   a = e^{−2γ_sw t_cycle} ∈ [0.80, 0.96]   (SLOW source — strong memory)
s (per-round det swing) ∈ [0.02, 0.05]   ⇒   ρ_0 ∈ [0.004, 0.028]
Markov-k baseline order k* = 6 (registered; the converged best rival on {det})
```

With `t_cycle ≈ 0.5–1 µs` this is `γ_sw ∈ ~2π·(3–35) kHz` i.e. `τ_sw ≈ 5–55 µs` — physically a slow TLS/1f
fluctuator (the grounding `τ_sw ~ µs–ms` low end), consistent with P1's `v ≳ γ_sw` non-Markovian side and
the C8b "slow source → observable round-corr in band; fast → collapses to 0" prediction.

**Predicted residual at the baseline order (the headline class-(b) number):**
- single RTN, representative `(g·t_cyc=0.05, s=0.05, B=8)`: `ρ_res(k=6) ≈ 0.006–0.008` ⇒ with `B_eff=2`,
  `R=30`, `τ=4`: **`N ≈ 1.0e4–1.9e4` reaches `|z|=5`** (headline pass); `|z|=3` at `N≈4e3–7e3`.
- 1/f decade source, `s_total` matched to the same `ρ_0`: `ρ_res(k=6) ≈ 0.3–0.4·ρ_0 ≈ 0.0012–0.011`,
  **`k`-independent** (the tail does not close) ⇒ `N ≈ 1.5e4–4.8e5` (`|z|=5`, `B_eff=2`) depending on `ρ_0`.

**SOURCE RECOMMENDATION for slice #1 — single RTN (with a 1/f confirmatory arm).** Justification:
1. **The single RTN gives the largest, cleanest, exactly-anchored residual.** Its forward filter is the
   exact 2-state HMM (a-exact ground truth for `ρ_res(k)`); `ρ_res(k)=ρ_res(1)·r^{k−1}` with `r≲a` is a
   sharp, falsifiable `(b)` band, and at the registered slow regime `ρ_res(k=6)≈0.006–0.008` is the
   *highest* detectable residual of the candidates — the shortest path to a `|z|=5` G4 pass at `N≈2e4`.
2. **BUT the single RTN's residual is finite-order-exhaustible** (`r^k` decay): G4 must FIX the baseline
   order `k*=6` and the lag set BEFORE the run (registered here), and the pass is "Markov-`k*` cannot
   capture it at the registered N," not "no finite Markov-k can." This is an honest, defensible G4 — it
   meets the contract's "beat the best converged Markov-k" letter — but it is **order-relative**.
3. **The 1/f source is the *non-order-relative* confirmatory arm.** Its residual does NOT close with `k`
   (power-law tail, §2b), so a 1/f pass is the stronger anti-toy statement (no `k*` can absorb it). It is
   recommended as the **second registered arm**, run after the RTN G4 lands, to certify the imprint is
   genuinely non-finite-order and not just "Markov-6 was too short."

Recommendation: **build slice #1 on the single RTN to reach G4 fastest at the registered `(a∈[0.80,0.96],
s∈[0.02,0.05], k*=6, |z|≥5, N≈2e4, B_eff=2)` band; register the 1/f decade source as the confirmatory arm
whose `k`-independent residual upgrades the G4 pass from order-relative to non-finite-order.**

---

## 5. Falsifying tests + epistemic-status roll-up (registered before any run)

- **(b) miss is a finding:** if at the registered `N≈2e4` the measured single-RTN `ρ_res(k=6)` is below
  `0.003` (sub-`|z|=3`), the regime band was wrong (revisit `s` / `a`), reported as a finding — NOT re-fit.
- **(a) positive control:** the single-RTN `C_det(τ)` MUST be a single exponential with base `a=e^{−2γ_sw
  t_cycle}` (§1, verified) — a Markov-1 on the rate MUST capture the 2-point function (if it does not, the
  emit path is buggy). The G4 residual must live in the *higher-order* structure, not the 2-point autocorr.
- **(a) negative control (motional narrowing):** fast source `γ_sw t_cycle ≳ 0.5` (`a ≲ 0.37`) ⇒
  `ρ_res(k=4) ≲ 0.0006` ⇒ sub-shot-noise at any realistic N ⇒ Markov-k-trivial ⇒ G4 correctly reads ~0
  (ties C8b fast-limit collapse; a positive G4 in the fast limit = false-positive = STOP).
- **(c) gate:** `|z|≥3` screen, `|z|≥5` headline; `k*=6` baseline order; `B_eff=2` representative
  (bracket `[1,8]` reported with sensitivity).

**Epistemic-status audit.** (a)-exact: the RTN latent autocorr `e^{−2γ_sw|τ|}`, the 1/f sum-of-Lorentzians,
the single-RTN single-exponential `C_det`, the HMM forward filter used as the `ρ_res(k)` ground truth, the
estimator SE `1/√M`. (b)-prediction-band: every `ρ_res(k)` magnitude, the decay base `r≲a`, the operating
band `a∈[0.80,0.96] / s∈[0.02,0.05]`, the required-N entries, the headline `N≈2e4`. (c)-gate/decision: the
`|z|` thresholds, `k*=6`, the lag set, `B_eff=2` representative arm, the single-RTN-first recommendation.
No item is left undeclared. All numbers reproduced by the scratchpad scripts `h2_verify.py` /
`h2_analytic.py` / `h2_base.py` / `h2_shotnoise.py` (analysis-only, not committed — re-derivable from the
formulas above); the load-bearing `ρ_res(k)` decay base and the required-N table are reproduced here verbatim
and must be re-confirmed by the committed G4/G5 gate scripts before any "earned" claim.

---

## 6. RECONCILIATION (2026-06-26) — third-method exact cross-check + a literature catch

> **Why this section exists.** §2/§4 above were produced by TWO derivation passes that DISAGREED on the
> single load-bearing number — the single-RTN order-`k` residual: Pass 1 (a leading-order `O(A·g)` estimate)
> said `ρ_res(k=6) < 0.001` (sub-floor → "recommend 1/f"); Pass 2 (a forward-filter fit, the §4 headline)
> said `ρ_res(k=6) ≈ 0.006–0.008` (→ "recommend single RTN, `N≈2e4`"). A ~6–8× gap on the number that
> DECIDES the slice-#1 source. The adversarial-self-verification rule forbids registering a source on an
> unreconciled load-bearing quantity. This section is the **third, fully-independent exact method**
> (committed script `outputs/teacher_prereg/h2_rtn_residual_reconcile.py` + `_h2_diag3.py` / `_h2_diag4.py`,
> exact enumeration on the 2-state HMM — no Monte-Carlo, no leading-order truncation) plus a **theory-first
> literature check** (the `theory-first` skill, against the on-disk reading notes). Both overturn the §4
> headline. The corrected registration is below; **§4's single-RTN-first recommendation is RETRACTED.**

### 6.0 A bug the positive control caught (corrects §0/§1)

The exact-enumeration positive control (control (1) in `h2_rtn_residual_reconcile.py`) flagged that the
**bare detection autocorrelation denominator in §0/§1 is wrong**. For a *binary* `D_r`, the total variance is
`Var(D_r) = p_0(1−p_0)` EXACTLY — by the law of total variance `E[Var(D|ξ)] = p_0(1−p_0) − s²` and
`Var(E[D|ξ]) = s²`, and the `s²` **cancels**. So

```
ρ_det(1) = s²·a / (p_0(1−p_0))        [CORRECTED — (a) exact]
```

NOT `s²a/(p_0(1−p_0)+s²)` as §0 (`ρ_0 ≡ s²/(p_0(1−p_0)+s²)`) and §1 wrote. Small numerically (`0.00905` vs
`0.00896` at the §1 operating point) but it is the correct (a)-exact form; enumerated `ρ_det(1)=0.00905`
matches the corrected closed form to 8 digits. **This is exactly the kind of error the §5 positive control
was registered to catch — it fired.**

### 6.1 The exact single-RTN residual — BOTH prior passes were wrong (different errors)

Computing the order-`k` residual autocorrelation by **exact 2-state-HMM block enumeration** (the optimal
order-`k` conditional mean over all `2^k` binary histories, no sampling) gives, at the §4 headline regimes:

| regime `(a, p0, s)` | exact `ρ_res(k=6)` at lag 1 | LINEAR (AR-6) | Pass 1 said | Pass 2 said |
|---|---|---|---|---|
| `(0.905, 0.10, 0.05)` | **−1.7e-4** | −1.6e-4 | <1e-3 | 6–8e-3 |
| `(0.961, 0.10, 0.05)` | **−3.7e-4** | −3.5e-4 | <1e-3 | 6–8e-3 |
| `(0.961, 0.06, 0.05)` | **−9.3e-4** | −7.5e-4 | <1e-3 | 6–8e-3 |

- **Pass 2's `0.006–0.008` is a forward-filter SAMPLING-NOISE artifact.** A sample autocorrelation over
  `R≈4000–6000` sampled rounds has a null floor `1/√R ≈ 0.013–0.016`; Pass 2's "measured" residual sits AT
  that floor — it was reading sampling noise, not signal. The exact value is ~10–40× smaller.
- **Pass 1's directional verdict (`sub-floor`) is right; its magnitude reasoning is incomplete.** The exact
  *lag-1* residual IS `O(1e-4)`. But Pass 1 mislabeled it "the linear 2-point residual" — in fact LINEAR
  (AR-`k`) and FULL (HMM conditional-mean) residuals **agree to ~4 digits** (control (2)): the single-RTN
  binary process is *near-linear* at these `s`, so there is no nonlinear HMM excess of any size. Both passes
  measured the wrong object at the wrong lag.

### 6.2 The deeper error — a MISREGISTERED OBSERVABLE (theory-first catch)

Measuring the residual at **lag 1** (what §2/§4 and both passes did) is itself wrong: an order-`k` predictor
*nulls* lags `1…k` by construction, so the surviving G4 signal lives at lag `> k`. Recomputed at the FIRST
UNCONTROLLED lag (`k+1`) and integrated as the **total residual-correlation energy** `E(k)=Σ_{ℓ≥1}ρ_res(ℓ)²`
(`_h2_diag3.py`/`_h2_diag4.py`, exact), the residual is `O(1e-2)`, not `O(1e-4)` — but the RTN-vs-1/f
SEPARATION nearly vanishes at feasible `k`:

```
E(k=6)/E(k=1):   single RTN a=.905 → 0.252    single RTN a=.961 → 0.429
                 1/f (3 decades)   → 0.447     1/f (4 decades)   → 0.499
```

A **slow** single RTN (`a=0.961`, correlation length `~1/(1−a)≈25` rounds) leaves almost the SAME residual at
`k*=6` as a 1/f source — because the RTN's own correlation length already exceeds `k*`, so a Markov-6 cannot
exhaust it either. The clean "RTN = geometric = exhaustible vs 1/f = power-law = persistent" dichotomy is an
**asymptotic-`k` statement that does NOT give a sharp separation at the feasible `k*≈6`.**

**This is grounded in the literature, not just our enumeration.** Kam, Gicev, Modi, Southwell & Usman,
*"Detrimental non-Markovian errors for surface code memory"* (arXiv:2410.23779, full-text read —
`docs/papers/reading_notes/kam_nonmarkovian_surface_code_2410.23779.md`), §IV.C + their explicit limitation
**L4**, prove on rotated surface-code memory that

> **the detector pairwise (2-point) autocorrelation `p̄_{t,t'}` does NOT distinguish benign from catastrophic
> temporal correlation** — "pairwise correlations can't distinguish a continuous timelike string from disjoint
> localized errors"; the discriminating signature is the **multi-time / timelike-string (streaky)** structure.

The H2 G4 observable as registered (`qec_coupling_simulator_build_contract.md` H1/G4: "detection-event
LONG-RANGE correlation vs best-converged Markov-k") IS a 2-point detection-event correlation. **A published,
on-disk, 精读'd result says that observable is a known-insufficient discriminator** — and our exact HMM
enumeration independently reproduces exactly that insufficiency at feasible `k`. This is precisely the
theory-first failure mode the skill exists to prevent: a pre-registration invented a 2-point-correlation
observable when the corresponding paper already on disk proves it is the wrong one.

### 6.3 RECONCILED REGISTRATION (supersedes §4)

- **(a) exact / retraction.** §4's "single-RTN `ρ_res(k=6)≈0.006–0.008`, `N≈2e4`, recommend single-RTN" is
  RETRACTED: the exact value is `O(1e-4)` at lag 1, the `0.006–0.008` was sampling noise. The §0/§1
  denominator is corrected to `p_0(1−p_0)`.
- **(b) reconciled band — the 2-point residual is NOT a reliable G4 discriminator at feasible `k`.** Over the
  whole registered slow band, `E(6)/E(1)` for a slow single RTN (`0.43`) and a 1/f source (`0.45–0.50`)
  differ by `<0.07` — below any realistic shot-noise discrimination. **HONEST HEADLINE FINDING:** *as
  specified, the G4 2-point detection-event correlation observable cannot cleanly separate a slow single RTN
  from a 1/f source.* This is a falsifiable prediction (a miss — a build that DOES separate them at `k*=6` —
  would be a finding) and it CAPS the contribution of the 2-point-correlation G4 as written.
- **(c) gate / required redesign.** Before slice #1 builds G4, the observable MUST be re-registered to the
  **multi-time / timelike-string** signature Kam et al. identify (the decode-relevant ΔLER under the source
  modulation, or an explicit multi-time correlator / excess-entropy gap), NOT the 2-point autocorrelation.
  The Markov-`k` rival is still the right baseline; the *statistic compared against it* must be multi-time.
  Run the `theory-first` pipeline on the multi-time observable (Kam's timelike-string / their `corrqec`
  open code as an independent reference) before re-registering G4's effect size.

### 6.4 Source recommendation — UNCHANGED conclusion, corrected reasoning

Slice #1 should still use a **1/f (≥3-decade, band straddling the 1–25 µs observed-lag window) source, with a
single RTN as the negative/contrast control** — but NOT for §4's stated reason (§4 claimed single-RTN gives
the *largest* residual; the exact check shows the slow single RTN is nearly as long-memory as 1/f at `k*`).
The corrected reason: only the 1/f source has a residual that is **non-finite-order in the asymptotic-`k`
sense** (`E(k)` ratio → 1, vs the RTN's slowly-falling ratio), so a 1/f pass on the *corrected* (multi-time)
observable is the only one that is order-robust. The single RTN is the contrast arm that quantifies how much
of the apparent G4 signal is merely "Markov-`k*` was too short for a slow source," not genuine non-finite-order
structure.

### 6.5 Falsifying outcome (the honest cap)

**If**, on the corrected multi-time observable at the registered `(a∈[0.80,0.96], s∈[0.02,0.05], k*=6,
N≤1e6)`, the source-resolved statistic does NOT beat the best-converged Markov-`k` by `|z|≥5` for EITHER the
1/f or the single-RTN source, **then G4 has no non-trivial regime at feasible shot budgets and the
non-Markovian-source contribution to the QEC simulator is HONESTLY CAPPED** at the source layer (G3a/G3b
Ramsey/echo wedge) — it does NOT upgrade to a record-level QEC imprint. That is a reportable negative finding,
not a failure to paper over: per the build contract, "earned at source layer" only becomes "earned as QEC
simulator" if G4 passes on records, and §6 has materially raised the bar for that.

**Epistemic-status roll-up for §6.** (a)-exact: the corrected `Var(D)=p_0(1−p_0)`, the exact HMM block-law
residuals, the LINEAR≈FULL agreement, the `1/√R` sampling floor. (b)-band: the `E(6)/E(1)` separation numbers,
the "2-point cannot separate RTN from 1/f at feasible `k`" prediction, the "1/f is the only order-robust arm"
claim. (c)-gate/decision: the required observable re-registration (multi-time, not 2-point), the retraction of
§4's recommendation, the falsifying threshold. **Provisional flag:** §6.2/§6.3's "the registered G4 observable
is insufficient" is a PROVISIONAL conclusion (grounded in Kam arXiv:2410.23779 + our exact enumeration, but
not yet a theorem about THIS exact d3-XZZX record map) — usable for go/no-go gating (it gates the G4
observable redesign), but nothing may be built on it until the multi-time observable is theory-first-grounded
and an exact d3 check is run.

**Committed evidence (this section):** `outputs/teacher_prereg/h2_rtn_residual_reconcile.py` (3-method exact
reconciliation, positive controls), `outputs/teacher_prereg/_h2_diag3.py` (residual at the correct
lag `>k`), `outputs/teacher_prereg/_h2_diag4.py` (the `E(k)` residual-energy RTN-vs-1/f discriminator). All
pure-numpy exact enumeration in the `aiqec` env; re-run with `python outputs/teacher_prereg/h2_rtn_residual_reconcile.py`.

---

## 7. G4-OBSERVABLE DECISION (2026-06-26) — candidate (a)/(b)/(c) adjudication + the coupling-CLASS finding

> **Why this section exists.** §6.3(c) ordered the G4 observable to be re-registered from the (retracted)
> 2-point detection correlation to a multi-time/timelike-string signature, and named three candidates to
> evaluate: **(a)** decode-relevant ΔLER under a correlation-blind (Markov-`k`-calibrated) decoder — Kam's own
> discriminator; **(b)** an explicit multi-time correlator / excess-entropy / timelike-string statistic; **(c)**
> Kam's `corrqec` open code (github.com/jkfids/corrqec, ref 67) as a sim+sampling reference. This section
> adjudicates them, and — the load-bearing result — finds that the choice of observable is NOT sufficient: the
> slice-#1 source-COUPLING class must be redesigned, and even on the right class a MILD 1/f ripple is sub-floor
> at `N≤1e6`. Grounded in the Kam reading note (full-text), the build contract, the §6 exact-HMM enumeration,
> and a linear-response Kam-style ΔLER estimate. Seam API confirmed: `seam.build_matched_pauli_dem`
> (`src/qec_twin/forward/scalable/seam.py:97`) builds the frozen marginalized Pauli-DEM; `teacher_shots_to_events:261`
> emits the `{det,obs}` the DEM decodes.

### 7.A RECOMMENDED G4 observable — **(a)** decode-relevant ΔLER under the frozen marginalized Pauli-DEM

Ranked comparison (discriminates a 1/f source from a best-converged Markov-`k` at the record level / Kam
grounding / fit with the project UQ bet / implementation cost):

1. **(a) decode-relevant ΔLER under the correlation-blind frozen DEM — REGISTERED.** It is the ONLY candidate
   Kam actually demonstrates as a discriminator: decode both the true-correlated records and the
   matched-marginal-independent records with the SAME marginalized Pauli-DEM, and the LER separates (Kam streaky
   Class-1 `d=15`: 97× independent; power-law `p_L=5.38e-2·d^-3.13` vs exponential). It is NOT a 2-point
   statistic ⇒ sidesteps the proven L4 failure (§6.2). It IS the project UQ conditional-coverage-under-
   misspecification bet (`project-uq-novelty-verdict`): `ΔLER = LER(frozen marginalized DEM on true 1/f records)
   − LER(source-aware/optimal)` is literally `B_misspec`. Implementation is LOW cost — reuses the in-tree frozen
   Pauli-DEM (`seam.build_matched_pauli_dem:97`) over `teacher_shots_to_events:261`; the only new arm is the
   matched-marginal-independent baseline (Kam Appendix-A `C_E` reparametrization gives it directly).
2. **(c) corrqec — DEMOTED to an independent generation cross-check.** It is Stim FlipSimulator + mask `M_{ij}`
   + matrix `R` + transform `T` — a simulation+sampling generator whose own harm metric IS candidate (a)
   (LER/teraquop). It is NOT a standalone observable; its role is to validate our `Θ(z_t)`-modulated record
   emission against an external Stim reference. See 7.E.
3. **(b) explicit multi-time correlator / excess-entropy — LAST, diagnostic only.** Kam flags it as "may be
   required" but provides NO ready metric and Fig 7-8 warns correlator magnitude ≠ harm (streaky Class-0 has
   STRONGER 2-point autocorr yet performs BETTER). Our §6.2 exact-HMM enumeration independently shows the
   record-level residual-energy separation `E(6)/E(1)` is `0.43` (slow RTN) vs `0.45–0.50` (1/f) — gap `<0.07`,
   sub-shot-noise at feasible `k*≈6`. Keep at most as a diagnostic of WHY (a) moves, NEVER as the pass criterion.

### 7.B REQUIRED slice-#1 source-coupling redesign — Θ(z_t) must leave Kam Class 0 (data ZZ/T2)

**This is the load-bearing finding; picking (a) is necessary but not sufficient.** Kam's discriminator is
**error-class-dependent** (reading note executive summary, §III.C/§IV, Table I):

- **Class 0 — temporal correlation on DATA qubits (idle T1/T2): BENIGN.** streaky-Class-0 LER ≈ independent,
  even slightly better. No detrimental ΔLER.
- **Class 1 — SPAM on SYNDROME/ancilla qubits: CATASTROPHIC.** power-law `5.38e-2·d^-3.13`, no teraquop,
  `d=15`: 97× independent. Forms **timelike string errors**.
- **Class 2 — two-qubit CZ/CNOT gates: CATASTROPHIC.** `1.62e-2·d^-2.07`, no teraquop. Spacetimelike/hook errors.

The contract's slice #1 (`source_coupling.py`, Section E step 3) modulates **`ζ`(ZZ) + `γφ`(T2) on DATA qubits
= Kam Class 0 = the provably BENIGN class.** A mild 1/f source co-modulating ζ+γφ on data qubits leaves
ΔLER ≈ 0 **regardless of which observable is chosen** — observable (a) will correctly read ~0 (a true negative,
not an instrument failure). **Required redesign:** Θ(z_t) must instead modulate

- **(preferred) Class 1** — ancilla/syndrome-qubit SPAM: source-modulated readout-assignment + reset error on
  the MEASURE qubits (catalog readout/SPAM mechanisms, NOT data T2). A slow ripple of the ancilla
  measurement/reset rate produces a streak of correlated syndrome flips on the same ancilla = a timelike
  string. Kam ties this to Google's below-threshold ~1e-10 floor; the canonical detrimental cell.
- **(alternative/additional) Class 2** — the CZ-gate (two-qubit-depol) error rate, producing correlated
  hook/spacetimelike errors across rounds.

**Architectural dependency this exposes:** the current d3 carrier models DATA qutrits with idealized ancilla
(`project-soft-readout-d1`); Class-1 SPAM and Class-2 gate errors live on the syndrome-qubit/gate axis the
carrier defers. Siting Θ(z_t) on Class-1/2 requires EITHER (i) an effective per-round source-modulated ancilla
SPAM / CZ Pauli mask injected before `teacher_shots_to_events`, OR (ii) the ancilla-resolved carrier. This is a
NEW slice-#1 dependency, not a free re-parametrization, and a register/window choice (H4) cannot substitute for
siting the coupling in the right error class.

### 7.C REGISTERED effect-size band — and the headline NEGATIVE finding for a MILD ripple

Even on the right class, a **MILD 1/f ripple** modulates the RATE `p(t)=p0(1+δ(t))` (δ zero-mean 1/f, relative
swing `σ_δ∈[0.20,0.50]` from the H2 detection swing `s∈[0.02,0.05]`), NOT per-round error→0.5 (Kam's maximal
mixing). **⚠ MECHANISM CORRECTION (re-review w4f1vasnw, exact transfer-matrix + MC + 3 positive controls, all
re-verified):** the original prose here — "the elevated streak base stays geometric, never power-law" — was
WRONG and slid the genuinely-multi-time 1/f into a pairwise frame (the user's catch). The 1/f elevated-RATE
streak IS heavy-tailed: the fixed-marginal conditional amplification `ρ_L=E[Π_{i<L}(1+δ_i)]` grows
SUPER-polynomially (`ρ_2=1.10`, `ρ_16=78`, `ρ_32=4.6e4` — ~2000× any 2-point model at L=32; structurally
streaky, not pairwise). **The correct mechanism for the cap is AMPLITUDE crush, not absent structure:** the
heavy `ρ_L` multiplies `p0^{L-1}`, and at mild `p0~1%` the effective consecutive-ERROR-string base
`b_L=[p0^{L-1}ρ_L]^{1/(L-1)}` creeps only `0.0088→0.0113` (L=2→32) — pinned near `p0`, never → 1. So the
*streak* is heavy-tailed but the *errors within it* are geometric; the multi-time `Σ_{k≥3}` ΔLER is computed
and is only **2.3%** of `ΔLER_2` (rate-suppressed, NOT dropped; `argmax_k=2`). The heavy tail becomes a real
power-law ERROR tail only as `b_L→1`, i.e. `p0→O(1)` = Kam's maximal mixing. Also at **d3, `L(d)=⌈(d+1)/2⌉=2`
= pure pairwise** — d3 cannot express multi-time structure in principle; it engages only at large d, where
`p0^{L-1}` has already crushed it for mild `p0`. **The headline number + the cap are UNAFFECTED.** At the
registered operating point (`p0~8e-3`, `σ_δ∈[0.2,0.5]`, `R=30`, d3, Class-1):

| | conservative | realistic |
|---|---|---|
| ΔLER (Class-1) | 1.8e-5 / 5.3e-5 | **5.5e-6 / 1.6e-5** |
| min detectable, `N=1e6`, `\|z\|=5`, LER0=0.03 | **8.5e-4** | — |
| required N | 2.2e9 / 2.6e8 | 2.4e10 / 2.8e9 |

The realistic ΔLER sits **~100× below** the `N=1e6` shot-noise floor. Sensitivity (scratchpad
`kam_mild_1f_deltaLER_estimate.py` / `kam_sens.py`, analysis-only, re-derivable): ΔLER clears the `N=1e6` floor
ONLY at `p0≥0.02` with `δ_max=0.95` and the de-rating `κ→1` — i.e. when the ripple is **no longer mild** and
the per-round rate approaches the maximal-mixing streak (Kam's already-published catastrophic model). The
`2-order-of-magnitude` gap is robust across the full optimistic corner (`κ=1, f_hi=0.30, δ_max=0.95` ⇒ ΔLER
1.0e-4, N=7.3e7). Class-2 ≤ Class-1 (Kam `A_C0=A_C1=2·A_C2` ⇒ smaller correlated weight); no rescue.

Tags: **(a) exact** — geometric run-length tails given a rate, base `p0(1+δ_max)≪1 ⇒ no power law`, shot-noise
`N=(z/δ)²·LER(1−LER)`, the corrected `Var(D)=p0(1−p0)`. **(b) prediction band** — `σ_δ∈[0.2,0.5]`, the ΔLER
magnitudes, `f_hi` tail occupancy. **(c) assumption/gate** — `p0~8e-3`, LER0=0.03, `n_synd=8`, `R=30`, κ=0.3
(the DEM recalibrates the marginal; only the non-factorizable correlation survives — the Kam benign-Class-0
lesson), `|z|≥5` headline.

### 7.D FALSIFIABLE PREDICTION + the honest cap

**Prediction (b):** at the registered `(Class-1, p0~8e-3, σ_δ∈[0.2,0.5], R=30, d3, N≤1e6)`, observable (a)
yields `ΔLER < 8.5e-4` ⇒ `|z|<5` ⇒ **no feasible G4 pass for a mild 1/f source.** A build that DOES separate
them at `N≤1e6` would be a finding (and would indicate the ripple is not mild). **Honest cap:** if no Class
+ source-strength regime reaches `|z|≥5` at `N≤1e6` without entering Kam's already-published
maximal-mixing/heavy-streak regime, the non-Markovian-source contribution to the QEC simulator is **CAPPED at
the source layer (G3a/G3b Ramsey/echo wedge)** — it does NOT upgrade to a record-level QEC imprint. This is the
§6.5 pre-registered reportable negative. Two honest paths: **(i)** accept the source-layer cap (the mild
Markovian-ripple part is BASELINE, per `project-coupling-nonmarkovian-is-the-contribution`); **(ii)** drive a
Class-1/2 mechanism into the near-maximal-mixing/heavy-streak regime — at which point it is Kam's published
catastrophic model, not our mild-ripple contribution, AND it requires the deferred ancilla/syndrome-error axis
(7.B).

### 7.E corrqec — vendor as an independent GENERATION cross-check (not the observable)

YES, vendor `corrqec` (github.com/jkfids/corrqec, ref 67) into `external/baselines/` (PRISTINE, per baseline
discipline — declare commit + settings, never edit). Role: an INDEPENDENT Stim-based reference for the record
GENERATION (mask `M_{ij}` + `R` + transform `T` marginalization), to cross-check our `Θ(z_t)`-modulated emit
against an external implementation — satisfying the anti-toy rule (verify against ground truth INDEPENDENT of
our engine). It is NOT the G4 observable; its harm metric IS (a). It supports (a), it does not replace it.

### 7.F RESIDUAL OPEN QUESTIONS for the user

1. **Class-1/2 carrier dependency — which arm?** Siting Θ(z_t) on ancilla SPAM / CZ gates needs either an
   effective per-round source-modulated syndrome-error injection into the emit path, or the ancilla-resolved
   carrier. The cheap path is the injection; the faithful path is the carrier. Which do we build for slice #1?
2. **Accept the source-layer cap, or pursue the catastrophic regime?** A record-level imprint requires leaving
   the "mild" regime — at which point we are reproducing Kam's published catastrophic model. Is the contribution
   intended as (i) the source-layer wedge + an honest "record-imprint capped" negative, or (ii) a Class-1/2
   near-maximal-mixing build (which must position against Kam, not as novel)?
3. **Exact d3 confirmation gate.** Both findings (the class problem and the mild-ΔLER smallness) are PROVISIONAL
   (Kam full-text + §6 exact-HMM enumeration + a linear-response Kam-style ΔLER estimate; not yet a theorem
   about this exact d3-XZZX record map). Before any build, run an exact d3 Stim ΔLER check on the chosen
   Class-1 coupling under observable (a) to confirm the sub-floor estimate.

**Epistemic-status roll-up for §7.** (a)-exact: geometric run-length tails, `p0(1+δ_max)≪1 ⇒ no power law`,
shot-noise N, the seam-DEM reuse. (b)-band: the ΔLER magnitudes, `σ_δ` band, `E(6)/E(1)` separation. (c)-gate/
decision: observable (a) registration, the Class-1/2 redesign requirement, the `|z|≥5` threshold, the corrqec
cross-check role. **Provisional flag:** 7.A's "(a) is the right observable" and 7.B's "slice #1 must leave
Class 0" and 7.C's "mild 1/f is sub-floor" are PROVISIONAL — usable to gate the slice-#1 source-coupling
redesign and the G4 re-registration, but the chosen Class-1/2 coupling + observable (a) must pass an exact d3
ΔLER check before anything is built on them.

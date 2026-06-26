# WS2 — ⑤ Spatial crosstalk + Temporal correlation + Drift — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION v2 (LITERATURE-GROUNDED), 2026-06-25. Supersedes the v1 draft (which invented an
`exp(-iφ Z⊗Z)` model + a `spatial_corr` observable from scratch — the user's "先找对应论文才是 theory-first"
correction). Every mechanism + observable + predicted behavior below is anchored to a DOWNLOADED +
FULL-TEXT-READ (精读) paper with a committed reading note, OR to existing in-repo grounded code. Predictions
are written BEFORE the build. User scope (2026-06-25): **⑤a + ⑤b-correlation + ⑤b-drift**, all three; then a
grounded pre-reg → user confirmation → code.

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)
| sub-axis | mechanism paper | observable paper | reading note | in-repo code |
|---|---|---|---|---|
| ⑤a spatial crosstalk | **Harper 2605.29514** (coherent ZZ `e^{iθZ⊗Z}`, θ=J_ZZ·t_g≈1e-3) | **Bravyi 1710.02270** (`P_L=2Σ_s p(s)|sinθ_s|` avg diamond-norm; twirl-underestimate) | `harper_..._2605.29514.md`, `correcting_coherent_errors_surface_1710.02270.md` | `mechanisms/teachers.py:zz_coupling_kraus` + `correlated_dephasing_kraus` (HARDEN H2, validated) |
| ⑤b temporal correlation | **Kam 2410.23779** (pairwise/streaky, by class; streaky-SYNDROME detrimental) | Kam (LER-degradation; §IV.C: 2-point autocorr INSUFFICIENT) | `kam_nonmarkovian_surface_code_2410.23779.md` | — (effective syndrome-flip injection; new) |
| ⑤b drift | **Bhardwaj 2511.09491** (`g(t)=g0+Σ g_m sin ω_m t`, Eq 12-13) | Bhardwaj (static-DEM LER penalty `Δ`, Eq 15; recoverability) | `bhardwaj_drifting_noise_estimation_2511.09491.md` | — (round-indexed rate in `round_pre`; new) |

Cross-cutting: ⑤a crosstalk + the misspecification BAND are ALREADY validated in HARDEN **H2** (rep-code,
2026-06-09): a FACTORIZED/iid-Pauli learner cannot represent the 2-body ZZ → its ΔLER band is OVERCONFIDENT
(`B_misspec`, the "third band"). WS2 brings ⑤ to the **d3-XZZX carrier + the full mix**, reusing the H2
mechanism + B_misspec concept.

## 1. The mechanisms (theory-first, literature-anchored; reuse where it exists)
### ⑤a SPATIAL crosstalk (two-qutrit)
- **Coherent ZZ (primary, Harper).** `U_φ = exp(-iφ Z⊗Z) = diag(e^{-iφ},e^{iφ},e^{iφ},e^{-iφ})` on
  **CZ-adjacent data pairs** (derived from the parsed XZZX schedule — the data pairs sharing an ancilla /
  a CZ layer). REUSE `zz_coupling_kraus(φ)`. φ DECLARED + SWEPT: grounded `φ≈1e-3` (Harper J_ZZ·t_g) up to
  the H2 regime `φ∈[0.05,0.15]` (a larger, more-visible bracket; report the band).
- **Stochastic comparator (Harper PTA).** `{cosφ·I₄, sinφ·Z⊗Z}` (Pauli-twirl, rate `sin²φ`). REUSE
  `correlated_dephasing_kraus(φ)`. The "same-PTA, different-coherent-distribution" pair (Harper §V.B) is the
  optional distribution-matters control.

### ⑤b TEMPORAL correlation (Kam) — effective syndrome injection
- **Streaky multi-time** (the detrimental structure) on **SYNDROME readout** (Class 1) — the per-round
  emitted syndrome bit experiences a temporally-correlated flip: a streak of length-`t` (decaying poly
  `A q/t^n` or exp `A q/n^t`) of guaranteed syndrome-bit flips. + **pairwise two-time** (benign control).
- **Implementation (declared simplification — carrier has idealized ancilla):** an EFFECTIVE
  syndrome-bit-flip mask `M` (Kam's Stim-FlipSimulator construction: `R`→`O`→`T`, the streaky/pairwise
  transformation) applied to the EMITTED syndrome bits, NOT a full ancilla simulation. q, n, A DECLARED +
  SWEPT (Kam's q≈1e-3, A_C1, n≥2). Marginals FIXED via Kam App A (`p'=C_E·p`, `C_E=2` for the bit-flip
  syndrome channel) so correlated vs marginalized-independent match per-(s,t).

### ⑤b DRIFT (Bhardwaj) — round-indexed rate
- A per-round time-varying Pauli RATE `g(r) = g0 + Σ_m g_m sin(ω_m r)` (Eq 12-13) on the data-qutrit
  channel (the composite leak / a depol), via `round_pre(eng, r)`. g0, g_m, ω_m DECLARED + SWEPT
  (Bhardwaj's regime: g0~0.1, g_m~0.05, low-freq `N/m>1e3`; multi-frequency). Distinct from ⑤b-correlation:
  drift = time-varying MARGINAL; correlation = structure at FIXED marginal.

## 2. Predicted observables (class (b) bands; LITERATURE-ANCHORED + the corrections)
### ⑤a
- **Coherent ZZ → EXCESS-LER / twirl-underestimate** (Bravyi `P_L`; Harper "coherence raises sub-threshold
  LER"): the iid-Pauli (PTA) learner UNDERESTIMATES the coherent crosstalk's LER; the H2 `B_misspec` (the
  factorized learner's wrong ΔLER + overconfident band) is the decode-relevant signature. The coherent ZZ
  is ~SYNDROME-TWIRLED (`project-coherence-not-identifiable-syndrome-only`) → the signal is in the LER, NOT
  the spatial syndrome correlation. **[corrects v1, which put `spatial_corr` as the coherent observable.]**
- **Stochastic (PTA) → `spatial_corr`** (same-round cross-detector covariance): the correlated stochastic
  Z⊗Z fires the two stabs sharing the pair together; the iid learner factorizes ⇒ misses it. PREDICTION:
  `spatial_corr>0` for the stab pair sharing the crosstalk pair, ≈0 otherwise + iid foil ≡0 + crosstalk-off ≡0.

### ⑤b-correlation
- **LER-DEGRADATION** under streaky-SYNDROME correlation: slower-than-exponential / (at high q)
  non-monotonic LER suppression vs the matched-marginal independent model (Kam Figs 3-6, Table I — streaky
  Class 1 `~d^{-3}`, no teraquop). The misspecification = the marginalized-DEM (iid) decoder's ΔLER under
  the correlation. PAIRWISE / Class-0(data) = the BENIGN controls (Kam: ~exponential, robust).
- **NOT the 2-point round-to-round detector autocorrelation** (Kam §IV.C PROVES it cannot distinguish
  benign vs catastrophic — `¯p_{t,t'}` does not track severity). **[corrects v1's "long-lag RR_CORR".]**

### ⑤b-drift
- **Static-DEM LER PENALTY `Δ = ϵ_static_L/ϵ_drift-aware_L − 1`** (Bhardwaj Eq 15): a static (time-averaged,
  g1=0) DEM decoder has higher LER than a drift-aware DEM; the static learner is misspecified. + the drift
  is RECOVERABLE from syndromes (window estimation tracks `g(r)`). NOT a 2-point correlation.

## 3. Exact DM ground truth (non-circular)
- **⑤a NEW two-site DM apply** `QutritDM.apply_channel_2site(kraus(9,9), i, j)` (the two-site
  superoperator, no dense embed; general non-adjacent (i,j)) — VALIDATED independently vs a from-scratch
  dense 2-site embed (`<1e-12`) + CPTP + the product-channel reduction (the foundational capability, B1).
  Then `record_oracle` with the ZZ EDGE on a CZ-adjacent pair, on an **OVERLAPPING-stab valid sub-code**
  (2 intact stabs SHARING the crosstalk data pair → nonzero `spatial_corr` for the PTA arm; the coherent
  arm's `P_L`/excess-LER via the logical readout). DM-vs-carrier Gate-4 (1/√N convergent).
- **⑤b-correlation:** the effective streaky syndrome-flip mask is a CLASSICAL post-process on emitted
  syndrome bits → apply the SAME mask to the DM `record_oracle`-emitted bits AND the carrier-emitted bits ⇒
  the LER + moments cross-check is exact (identical classical mask both sides; not circular — DM vs MCWF are
  different objects). LER (offset-removed) via `record_oracle.flip_rate`. Fixed-marginal (App A) on both.
- **⑤b-drift:** the round-indexed rate `g(r)` is known truth → `record_oracle`/carrier produce the drifting
  record exactly (`round_pre` with `g(r)`); the static-vs-true LER is recomputable. NO new GT machinery
  beyond a round-indexed rate.
- **Controls:** iid foil (`spatial_corr≡0`); crosstalk-OFF / correlation-OFF / drift-OFF (the matched
  null); corrupt-stab (geometry teeth); marginalized-independent (Kam's matched-marginal control).

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)
- φ / q / g(r)-spectrum SWEPT (never frozen); the crosstalk pairs derived from the schedule.
- the two-site apply is NEW (validated §3); the overlapping-stab sub-code is the spatial-cert register
  (feasible ~6-qutrit; full-9q spatial is carrier-only, DM-for-anchor/MCWF-for-scale).
- **⑤b-correlation EFFECTIVE syndrome-flip injection** (NOT a full ancilla sim — the carrier's idealized
  ancilla; `project-soft-readout-d1`): a declared (c)-class scope choice; faithful to Kam's own
  FlipSimulator syndrome-error method, but NOT the ancilla-resolved circuit. Bound = the difference vs an
  ancilla-resolved sim is out of scope (declared, not silently assumed equal).
- ⑤b-drift: the RECOVER method (window estimation, Bhardwaj) is the PREDICT axis — WS2 ⑤b-drift = the
  teacher MECHANISM + the static-DEM-penalty observable; the recover/band-validation is the predict-axis build.
- per-round-lumped siting inherited (WS1 b3-S1); the 2-point RR_CORR is a known-INSUFFICIENT summary (Kam).

## 5. Epistemic status (METRICS.md ladder)
- **(a) exact:** the two-site-apply validation; the DM record/moment identities; the fixed-marginal algebra
  (Kam App A `C_E`); the drift's known-truth LER.
- **(b) bands:** ⑤a excess-LER/`P_L` + `spatial_corr`; ⑤b-correlation LER-degradation; ⑤b-drift static-DEM
  penalty `Δ`. A miss is a finding.
- **(c) gates:** the MC bands; the iid-foil / off / corrupt-stab / marginalized-independent controls.
- Verdict "⑤ certified" stays **PROVISIONAL** (convergence + independent oracles; reportable, nothing built on).

## 6. Build org (≥3 disjoint builders + un-led reviewer; long runs orchestrator-driven)
- **B1 (foundational, mainline):** `QutritDM.apply_channel_2site` + the independent validation (vs dense
  embed + CPTP + product reduction) + a `tests/` test. Commit-gated.
- **B2 (teachers, outputs/):** ⑤a coherent-ZZ + PTA crosstalk on CZ-adjacent pairs (reuse
  `zz_coupling_kraus`/`correlated_dephasing_kraus`) + the carrier two-site apply + the OVERLAPPING-stab
  sub-code finder; ⑤b-correlation effective streaky/pairwise syndrome-flip (Kam `R/O/T`, fixed-marginal App A);
  ⑤b-drift round-indexed `g(r)` (Bhardwaj Eq 12-13).
- **B3 (certification, outputs/):** ⑤a (`spatial_corr` + excess-LER/`B_misspec`, DM-vs-carrier on the
  overlapping sub-code); ⑤b-correlation (LER-degradation, fixed-marginal correlated-vs-independent; NOT the
  2-point RR_CORR); ⑤b-drift (static-DEM LER penalty `Δ`); the controls.
- **Reviewer:** un-led (stage problem + goal + artifacts only).
GPU-only; scripted-execution; mainline commit-gated; theory-first (this pre-reg) lands before any code.

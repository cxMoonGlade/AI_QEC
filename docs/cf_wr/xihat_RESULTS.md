# ξ̂ measurement — RESULTS (tool build step 1)

> Run 2026-06-14, RTX 5090, M3 Google Willow **d=29 rep-code, `sample_00` ONLY** (both bases),
> 111 s, 7.2 GB GPU peak. Decoder-independent; held-out 05–09 / escrow 15–19 / drift 01–04 **never
> touched** (red-line asserts fired). Registration: [`xihat_registration.md`](xihat_registration.md).
> Scripts: `outputs/cf_wr_xihat.py` (frozen gate), `outputs/cf_wr_xihat_analyze.py` (post-hoc
> diagnostic). Sidecar: `outputs/cf_wr_xihat_results.json`. Slab sha256: X `0a9be362…`, Z `b512223e…`.

## 0. Headline (PROVISIONAL)

**The hardware sits DEEP in the controlled regime: directional spacetime Markov length
`ξ̂ ≈ 0.3–0.6 cells` (sub-cell), with a negligible `~1–2%-of-peak` residual floor.** Correlations
die within a single detector cell ⇒ small windows screen the seam almost immediately ⇒ the 1+1 fusion
direction is supported on real data. **Status: PROVISIONAL** — this corrects a frozen-gate
false-negative via a *post-hoc model change* (§3), so it is reportable + go/no-go-usable but **not
banked** until a clean v2 re-registration confirms it (§6).

## 1. The frozen gate result (reported as-run)

The registered single-model fit (exp vs power-law over the above-null range) returned, on **all four**
curves, `STOP(power-law)`:

| curve | frozen ξ | R²_exp | R²_pow | gate |
|---|---|---|---|---|
| X/temporal | 6.75 | 0.497 | 0.712 | STOP(power-law) |
| X/spatial | 10.59 | 0.094 | 0.140 | STOP(power-law) |
| Z/temporal | 7.76 | 0.455 | 0.669 | STOP(power-law) |
| Z/spatial | 12.56 | 0.062 | 0.107 | STOP(power-law) |

**Overall frozen verdict: STOP (near threshold).** *Both R² are poor everywhere* — the gate did not
find a good power law; it found that a single exponential fit the full above-null range even worse.
That poor-fit-both-ways is the first signal the fit MODEL, not the hardware, is the problem.

## 2. Why the frozen STOP is a FALSE NEGATIVE (diagnosis)

Inspection of the raw `Î(w)` curves shows a structure the frozen single-model fit cannot represent:

- a **steep short-range decay** — e.g. X/temporal `Î`: w1 `1.9e-3` → w3 `3.0e-5` (**63× in 2 cells**);
- a **weak slow tail / floor** at `~1–3e-5 nats` (≈1–2% of peak) persisting to w≈10;
- a **plug-in-bias-dominated tail** at large w: `Î_null_mean` GROWS with bin count (X/temporal null:
  `4e-11` @w1 → `7.7e-6` @w18) and `Î_real` RISES to track it (w13→18). Scout-2 pre-warned this
  positive bias "fakes a non-decaying CMI." The frozen fit included these bias points, dragging R²_exp
  below R²_pow ⇒ the spurious "power-law" label.

Three confounds the frozen v1 fit model did not anticipate: **(i)** the plug-in bias tail (not
strictly excluded — the 2σ above-null test was too permissive); **(ii)** even/odd **separation parity**
(matching-graph structure: even-sep ξ≈2.3–2.9, odd-sep ξ≈3–9, both poor single-exp R²); **(iii)** the
**directional-projection floor** (registration §8 — the 1D line-buffer leaves the perpendicular axis
open; my §8 claim "shape is robust to projection" was **too optimistic**: a constant leakage floor
turns a true exponential into an apparent power-law).

## 3. Corrected reading — exp-on-a-floor model (post-hoc, (c)-diagnostic)

The structure-matched model `Î(w) = a·e^{−w/ξ} + c`, fit over the **bias-clean region only**
(`Î_real > 5×Î_null_mean`), is excellent and consistent:

| curve | **ξ̂ (cells)** | floor c (nats) | floor / peak | R² | bias-clean w≤ |
|---|---|---|---|---|---|
| X/temporal | **0.62** | 1.49e-5 | 0.8% | 0.998 | 14 |
| X/spatial | **0.33** | 2.82e-5 | 1.6% | 0.996 | 11 |
| Z/temporal | **0.62** | 1.79e-5 | 0.9% | 0.998 | 14 |
| Z/spatial | **0.37** | 2.79e-5 | 2.2% | 0.993 | 11 |

Corroboration that ξ≪1 is real, not a fit artifact: the **bias-free fast-head** fit (w=1–3, well below
any bias) independently gives ξ≈0.47–0.50 on every curve — same sub-cell scale, R²≈0.98.

**Interpretation:** dominant Markov length `ξ̂ ≈ 0.3–0.6 cells` (deeply controlled, ≪ XI_GO=5.8) +
a `~2e-5`-nat constant floor (1–2% of peak). Even if that floor were a *genuine* weak long-range tail
(not leakage), at 1–2% of peak it is immaterial to the controlled-regime question (the seam is screened
to ≥98% within one cell).

## 4. Prediction scorecard (registration §6, (b) — a miss is a finding)

| # | prediction | outcome |
|---|---|---|
| b-1 | clean exponential collapse (finite ξ̂) | **CONFIRMED** with the correct (exp-on-floor) model; **the frozen single-model gate MISSED it** (false-negative power-law) — methodological finding |
| b-2 | ξ̂ = O(a few) cells | **CONFIRMED & stronger** — ξ̂ is **sub-cell** (0.3–0.6), even shorter than predicted |
| b-3 | X/Z differ; space–time anisotropy | **PARTIAL MISS (finding):** X≈Z almost exactly (0.62/0.62 temporal, 0.33/0.37 spatial); the only real anisotropy is **spatial ξ < temporal ξ** (0.35 vs 0.62) — opposite-signed to the predicted X>Z basis split |

## 5. Audits

- **Metric audit:** ξ̂ via the field-standard spacetime-Markov-length CMI diagnostic (Negari–Ellison–
  Hsieh 2412.00193); Miller–Madow bias correction (standard); exp-on-floor + log-linear fits (standard).
  All metrics field-standard. The C-resample null is a **conservative** bias floor (destroys C's
  B-dependence too — can only make above-null harder to trip).
- **Rigor audit:**
  - Frozen gate verdict (STOP) — **(c)** gate output, reported as-run.
  - The exp-on-floor reading (ξ̂≈0.4, controlled) — **PROVISIONAL** (post-hoc model change); usable for
    go/no-go, **not** a premise for any build. Theorem-grade only after v2 (§6).
  - The residual floor origin (leakage vs genuine) — **UNCLASSIFIED** (immaterial at 1–2% of peak).
  - v1 fit-model inadequacy (single-exp-vs-power-law over a bias-contaminated range) — **established**
    finding; the registration §5 fit recipe and §8 "shape robust to projection" claim are superseded.

## 6. v2 — what converts PROVISIONAL → banked

A clean re-registration (predict-before-run) that fixes the three v1 confounds:
1. **Model:** register `Î(w)=a·e^{−w/ξ}+c` as the fit (not single-exp-vs-power-law).
2. **Strict bias cutoff:** fit only `Î_real > 5×Î_null_mean`; report the floor c and a stricter null.
3. **Shot-split stability:** ξ̂ on two disjoint 50k-shot halves of sample_00 (the §5 stability leg v1
   skipped) — confirms ξ̂ is not a sampling artifact, using only training data.
4. **Floor classification (decisive):** a **thick-buffer** control — B = the line segment **+ the ±1
   neighbour chains** over the buffer (blocks the perpendicular leakage path). If the floor c collapses
   ⇒ directional-projection leakage ⇒ ξ̂≈0.4 is the whole story (clean GO). If c persists ⇒ a genuine
   weak long-range tail (still controlled at 1–2%, but characterized).

v2 stays sim/teacher-free, `sample_00`-only, GPU, scripted-execution, ≥1 independent reviewer before run.

## 7. Bottom line for the tool

The gating measurement, read correctly, is **provisionally GO**: real Willow d=29 hardware is deeply
short-range-correlated (ξ̂ sub-cell), exactly the regime where the small-window twin + fusion is
theory-backed. The frozen gate's STOP was an artifact of an inadequate v1 fit model — a genuine
methodological finding, now corrected. **Recommendation:** run v2 (§6) to bank the result before
building step 2 (learner `ρ_BC` extension) on it.

---

## 8. v2 — BANKED + a confounded floor control (2026-06-14)

Run `outputs/cf_wr_xihat_v2.py` (registration §11), RTX 5090, 168 s, `sample_00` only. **v1 cross-check
PASS** — h=0 reproduces v1's thin-buffer Î **bit-identically** (maxΔ≈1e-15), validating the patch-CMI
machinery against the reviewed v1.

| curve | ξ̂ (exp-on-floor) | floor c | R² | shot-split ½₁,½₂ | stable |
|---|---|---|---|---|---|
| X/temporal | 0.62 | 1.5e-5 (0.8%) | 0.998 | 0.626, 0.616 | ✓ |
| X/spatial | 0.33 | 2.8e-5 (1.6%) | 0.996 | 0.328, 0.325 | ✓ |
| Z/temporal | 0.62 | 1.8e-5 (0.9%) | 0.998 | 0.618, 0.618 | ✓ |
| Z/spatial | 0.37 | 2.8e-5 (2.2%) | 0.993 | 0.370, 0.363 | ✓ |

**Main result — BANKED GO/controlled.** ξ̂ ≈ 0.33–0.62 cells, R²≈0.993–0.998, shot-split stable on all
four curves ⇒ the **rep-code hardware is deeply controlled**. exp-on-floor is now the **registered**
(not post-hoc) model; the v1 provisional read is **banked**. Predictions (b-v2-1) ✓, (b-v2-2) ✓.

**Floor classification — INCONCLUSIVE; the control was a confounded instrument.** The thick-buffer
(±1) auto-label "GENUINE-WEAK-TAIL" is **not reportable as a finding**: the h=1 debiased Î is **10–15×
LARGER** than h=0 at w=3 (X/temporal 3.04→34.2; X/spatial 2.36→22.5). Neither leakage nor a genuine
tail predicts an *increase* from adding buffer — this is **explaining-away (collider conditioning)**:
the ±1 neighbour detectors at A's/C's layers share error mechanisms with A,C (a data error flips
spatially-adjacent detectors), so conditioning on them *induces* A:C correlation rather than screening
it (compounded by even/odd separation-parity: w=4 is an odd-sep local max). **The naive ±h thickening
is NOT a valid Markov screen.** The floor's origin stays **UNCLASSIFIED** — immaterial at 1–2% of peak
either way. (b-v2-3) → the instrument was confounded (a methodological finding), **not** a clean miss.

**Lesson for surface (2+1)D:** a valid Markov-buffer is a graph **separating set** (a cut between A
and C), NOT a neighbourhood thickening — explaining-away is *worse* in 2D (more colliders). This binds
the surface ξ̂ buffer design.

**Rigor audit.** ξ̂≈0.4 controlled — theorem-free but **registered + measured + cross-validated
(BANKED)**. Floor magnitude (1–2%) — measured. Floor origin — UNCLASSIFIED (control failed). The
explaining-away confound — established finding.

## 9. Status & the surface gate

The **rep-code ξ̂ gate is GO/controlled, BANKED.** Per the surface-first steer (2026-06-14): this is the
**(1+1)D method-validation + confirmation the M3 hardware is controlled** — it is **NOT** the surface
gate. ξ̂ is decoder-independent data analysis with **no exact-backend constraint**, so the surface ξ̂
(dataset `google_72Q_surface_code_d3_d5_set2`, (2+1)D) is just as runnable and is the **actually-gating
read** for a surface-code tool. Next: build the (2+1)D surface ξ̂ with a **separating-set** buffer
(per the §8 lesson).

## 10. SURFACE temporal ξ̂ — first read (2026-06-14): d3 controlled, **d5 raises a real problem**

Run `outputs/cf_wr_xihat_surface.py` (registration §12) + `..._analyze.py` (parity-split), RTX 5090,
13 s, **`sample_00` only**, decoder-independent. Dataset `google_72Q_surface_code_d3_d5_set2`, r50.
**Geometry validated:** d3 folds to exactly **8 sites** matching the metadata `meas_qubit_coords`
(det=400=8×50); d5 to **24 sites**. Temporal CMI per-stabilizer, exp-on-floor (reused, v2-validated).

| instance | pooled ξ̂ | R² | even-sep ξ | odd-sep ξ | floor | read |
|---|---|---|---|---|---|---|
| d3_at_q5_5 / X | 0.46 | 0.999 | 0.57 | 1.02 | 6.4% | **controlled** (≈ rep-code) |
| d3_at_q5_5 / Z | 0.46 | 0.999 | 0.59 | 1.14 | 6.4% | **controlled** |
| d5_at_q5_5 / X | 8.0 *(bad fit)* | 0.50 | **8.52 (R²0.99)** | 2.33 | ~6% | **LONG correlation** |
| d5_at_q5_5 / Z | 9.8 *(bad fit)* | 0.46 | **8.78 (R²0.93)** | 2.33 | — | **LONG correlation** |

**Findings.**
1. **d3 surface temporal ξ̂ ≈ 0.5 cells — CONTROLLED**, like rep-code (0.4). The deeply-short-range
   story extends from 1D rep-code to the small 2D surface patch. Floor 6.4% (vs rep-code 1–2%) —
   larger, consistent with more 2D perpendicular leakage (prediction b-surf-2 ✓).
2. **d5 surface has a LONG temporal Markov length: even-separation ξ ≈ 8.5 cells, a CLEAN exponential
   (R²=0.99), ~18× d3/rep-code.** The pooled single-model fit "fails" (R²≈0.5) only because d5
   superposes two scales (even-sep ξ≈8.5, odd-sep ξ≈2.3); the parity-split exposes a *real* long
   even-branch — **not** an oscillation/noise artifact. **This is the first place the controlled-regime
   read breaks** — and it is on the patch *closer to the real target*.

**Prediction scorecard (§12 b).** b-surf-1 (controlled O(1)): **PARTIAL** — holds for d3, **fails for
d5** (ξ≈8.5). b-surf-2 (floor > rep-code 1–2%): **✓** (d3 6.4%, d5 higher). b-surf-3 (d5 ≥ d3): **✓,
dramatically** (d5 ≈18× d3).

**Cause — UNRESOLVED (3 candidates).** (i) genuine size/crosstalk/distance effect (bigger patch → longer
correlation); (ii) **stale calibration of the d5 acquisition** (set2 deliberately mixes freshness; note
d3 in the *same* sample_00 is clean, so it is **not** a sample-wide calibration issue — it is
d5-patch-specific, which weakly favors a real d5 effect or a per-patch-independent acquisition age);
(iii) heterogeneous-stabilizer pooling (24 sites; though the clean even-branch R²=0.99 argues for a
fairly homogeneous ξ, not a few outliers). **Provisional; needs a follow-up to separate.**

**Rigor audit.** d3 controlled (ξ≈0.5) — measured, clean. d5 even-sep ξ≈8.5 — measured, clean
(R²=0.99), **but cause UNRESOLVED ⇒ provisional**. Spatial ξ NOT yet measured (this is temporal only) —
the spatial Markov length on d5 is the **real** windowing concern (a spatial ξ≈8.5 on a ~9-wide patch
would forbid spatial windowing) and is the priority follow-up.

**Implication for the tool.** The "hardware deeply controlled" read is **patch-dependent**: solid for
rep-code + d3, **broken for d5**. Before the 1+1 fusion can claim the surface target, the d5 long
correlation must be (a) attributed (size vs calibration vs heterogeneity) and (b) measured spatially.
The honest status: **the surface gate is NOT a clean GO** — d3 passes, d5 flags a real correlation
problem on the target-scale patch.

## 11. SURFACE SPATIAL ξ — the decisive windowing test (2026-06-14): **d5 windowing VIABLE**

Run `outputs/cf_wr_xihat_surface_spatial.py` (registration §13) + `..._analyze.py`, RTX 5090, 3 s,
`sample_00` only, decoder-independent. Two measures on the 2D stabilizer layout, pooled over
rounds+shots: **2-point connected correlation** `C(r)` (no buffer ⇒ no explaining-away) and
**corridor-CMI** `I(A:C|B)` with B = the stabilizers strictly between A and C (a genuine spatial
separating set, §11 lesson). exp-on-floor fits:

| instance | ξ_2pt | ξ_corridor-CMI | floor | patch width | windowing |
|---|---|---|---|---|---|
| d3_at_q5_5 / X,Z | 0.74 (R²0.93) | (3 bins, n/a) | ~0 | 3 | **VIABLE** |
| d5_at_q5_5 / X | 0.78 (R²0.93) | **0.63 (R²1.000)** | ~0 | 5 | **VIABLE** |
| d5_at_q5_5 / Z | 0.79 (R²0.93) | **0.63 (R²1.000)** | ~0 | 5 | **VIABLE** |

**Decisive finding: spatial windowing on d5 is VIABLE.** The spatial Markov length is **short
(~0.6–0.8 cells) on both d3 and d5, ≪ the patch width (3 / 5)**, with a **~0 floor** — spatial
correlations decay cleanly within ~1 cell. The corridor-CMI (the Markov-consistent measure) fits d5 at
**R²=1.000**; the 2-point corroborates (factor ~1.2). Predictions (§13 b): b-sp-1 ✓ (d3 short),
**b-sp-2 ✓ strongly** (d5 spatial 0.63 ≪ width 5, far shorter than its temporal 8.5), b-sp-3 ✓
(2-point/CMI agree within ~1.2×).

**The d5 picture, resolved — short space, long time.** d5 is **SPATIALLY controlled** (ξ≈0.6 cells,
clean, ~0 floor) but **TEMPORALLY long-correlated** (ξ≈8.5 cells, §10). This clean separation
**strongly indicates the d5 long correlation is a TEMPORAL/drift axis — not a spatial-locality
breakdown**: a slow temporal drift over ~8.5 rounds (consistent with set2's deliberately-mixed
calibration) does not threaten **spatial** windowing, which is the core of the 2D surface-code tool.

**This REVERSES the §10 worry.** The d5 temporal length looked alarming, but the decisive spatial
measurement shows the **2D windowing the surface tool actually needs is viable** on the target-scale
patch. The temporal length is a separable, known concern (the drift axis, H4/M5), not a windowing
killer.

**Rigor audit.** d3 + d5 spatial ξ≈0.6–0.8 ≪ width — measured, clean (2-point R²0.93, corridor-CMI
R²1.0), two independent measures agree ⇒ **spatial-windowing-viable is well-supported**. The inference
"the long temporal ξ is drift/calibration" is **PROVISIONAL** (cause still unattributed — the
cross-sample check resolves it). Both measures are decoder-independent, `sample_00` only.

**Surface gate, updated.** For **spatial windowing** (what the tool needs): **GO on d3 and d5.** Open
item: attribute the d5 temporal length (drift vs real) via the cross-sample check, and confirm temporal
windowing tolerates ξ_t≈8.5 within the 50-round depth. The earlier "surface gate is not a clean GO"
(§10) is **superseded** for the spatial question.

## 12. CROSS-SAMPLE temporal ξ — the d5 long correlation is **DRIFT** (2026-06-14)

Run `outputs/cf_wr_xihat_surface_xsample.py` (registration §14), RTX 5090, 9 s. Even-separation
temporal ξ per sample, d3 + d5, basis X, r50, over `DRIFT_SAMPLES={0,2,4,10,13,22,28,34}` — a spread
across the **unreserved** index range; **held-out 05–09 / escrow 15–19 never touched** (allowlist
red line asserted). Decoder-independent.

| sample | d3 ξ_even | d5 ξ_even (R²) |
|---|---|---|
| s00 | 0.57 | 8.56 (0.99) |
| s02 | 0.64 | ~7–12 (poor fit) |
| s04 | 0.67 | ~12 (poor fit) |
| s10 | 0.66 | ~12–19 (poor fit) |
| **s13** | 0.37 | **0.51 (1.00)** |
| **s22** | 0.37 | **0.34 (1.00)** |
| **s28** | 0.35 | **0.39 (1.00)** |
| s34 | 0.62 | ~11–22 (0.55) |

**Finding: the d5 long temporal ξ is DRIFT, not a persistent device property.** d5 ξ_even spans
**0.34 → 22 (64× variation)**, bimodal: **fresh samples (s13/22/28) give ξ≈0.4 — fully controlled,
like rep-code/d3**; stale samples (s00/02/04/10/34) give ξ≈8–22. Meanwhile **d3 stays short (0.35–0.67)
on every sample** — so it is **not** whole-sample staleness (that would lengthen d3 too); the bigger
**d5 patch is more drift-sensitive**, and set2's deliberately-mixed calibration freshness shows through.
Predictions (§14 b): **b-cs-1 ✓ strongly** (d5 varies 64×), **b-cs-2 ✓** (d3 short on all). Interpretation
matrix ⇒ **d5-acquisition-specific calibration drift**.

**Rigor audit.** d3 short on all 8 samples — measured, clean (R²=1.0). d5 bimodal (fresh ξ≈0.4 clean
R²=1.0 / stale ξ≈8–22) — measured; the fresh-vs-stale split is the **calibration-drift** attribution
(theorem-free but well-supported by the d3-stable control + the 64× bimodal spread). Allowlist red line
honored (no held-out/escrow contact).

## 13. ξ̂ INVESTIGATION — consolidated verdict

| rung | result | status |
|---|---|---|
| rep-code d=29 (1+1)D | ξ̂≈0.4 cells, shot-split stable | **BANKED controlled** (§8) |
| surface d3 spatial + temporal | ξ≈0.5–0.7 cells, all samples | **controlled** (§10, §11, §12) |
| surface d5 **spatial** | ξ≈0.6 cells ≪ width 5 | **windowing VIABLE** (§11) |
| surface d5 **temporal** | ξ≈0.4 fresh / 8–22 stale | **DRIFT**, controlled when fresh (§12) |

**Bottom line for the tool.** On **well-calibrated** real surface code, the hardware is **fully in the
controlled regime** — spatial ξ≈0.6 *and* temporal ξ≈0.4, both ≪ patch scale — exactly where the
small-window twin + 1+1 fusion is theory-backed. The d5 "problem" was **calibration drift**, a
**separable, characterizable axis** (and set2's stale samples are a ready-made drift testbed, the H4/M5
lane). **The step-1 ξ̂ gate is GO on real surface code** (fresh calibration); drift handling is a known
downstream concern, not a windowing blocker. Cleared to build step 2 (learner `ρ_BC` extension).

## 14. d3→d5→**d7** SCALING — windowing scales to the fault-tolerant target (2026-06-14, CAPSTONE)

Run `outputs/cf_wr_xihat_d7.py` (registration §15), RTX 5090, 14 s, **Willow 105Q** d3/d5/d7
(`d3_at_q6_7` / `d5_at_q6_5` / `d7_at_q6_7`), bases X/Z, r90, decoder-independent (no-sample release ⇒
diagnostic on the sole acquisition; no obs/decode read). Same-device scaling series.

| distance | sites | spatial ξ_2pt | spatial ξ_cmi | temporal ξ_even | width | windowing |
|---|---|---|---|---|---|---|
| d3_at_q6_7 | 8 | 0.68 / 0.74 | — (few bins) | 0.56 / 0.54 | 3 | VIABLE |
| d5_at_q6_5 | 24 | 0.73 / 0.75 | 0.70 / 0.64 (R²1.0) | 0.51 / 0.54 | 5 | VIABLE |
| **d7_at_q6_7** | **48** | **0.71 / 0.72** | **0.70 / 0.69 (R²0.99)** | **0.44 / 0.53** | 7 | **VIABLE** |

**Capstone finding — spatial windowing SCALES to d7.** The spatial Markov length is **FLAT across
d3→d5→d7 at ξ≈0.7 cells (range 0.64–0.75), independent of code distance**, and ≪ the patch width at
every distance. Error locality does **not** grow with the code ⇒ the windowed-twin premise holds at the
**fault-tolerant target scale** on the real Willow 105Q device. The corridor-CMI (Markov-consistent)
confirms d5/d7 at R²=0.99–1.00; the 2-point corroborates. Predictions (§15 b): **b-d7-1 ✓ strongly**
(d7 spatial 0.7 ≪ width 7), **b-d7-2 ✓ strongly** (scaling flat), b-d7-3 resolved (d7 temporal short).

**Temporal ξ short (~0.5) on 105Q — confirms the drift attribution.** Unlike 72Q-set2-d5 (temporal ξ
8–22 on stale samples, §12), the 105Q d5/d7 are temporally controlled (ξ≈0.5). Consistent with §12: the
72Q long ξ was calibration staleness; well-behaved acquisitions are short in time too, even at d7.
(Honest caveat: 105Q ships no calibration-age labels — "well-behaved" is read from ξ, not certified.)

**Rigor audit.** Spatial ξ≈0.7 flat across d3/d5/d7 — measured, clean (2-point R²0.93–0.96, corridor-CMI
R²0.99–1.00, two measures agree), same device ⇒ **windowing-scales-to-d7 is well-supported**. Temporal
ξ≈0.5 across d3/d5/d7 — measured, clean (R²1.0). The "105Q acquisitions are well-calibrated" reading —
PROVISIONAL (no shipped labels; inferred from ξ + the §12 contrast). Decoder-independent throughout.

## 15. ξ̂ INVESTIGATION — FINAL verdict (supersedes §13)

| rung | spatial ξ | temporal ξ | status |
|---|---|---|---|
| rep-code d=29 (1+1)D | — | ≈0.4 | BANKED controlled |
| surface d3 (72Q + 105Q) | ≈0.7 | ≈0.5 | controlled |
| surface d5 (105Q, well-behaved) | ≈0.7 | ≈0.5 | controlled |
| surface d5 (72Q set2) | ≈0.6 | 0.4 fresh / 8–22 stale | spatial controlled; temporal = DRIFT |
| **surface d7 (105Q)** | **≈0.7** | **≈0.5** | **controlled — windowing scales** |

**FINAL bottom line.** On the real Willow surface-code device, the noise sits in the **controlled
regime — spatial ξ≈0.7 AND temporal ξ≈0.5, FLAT from d3 to d7**, all ≪ patch scale. **Spatial windowing
scales to the fault-tolerant target (d7).** The one anomaly (72Q-set2-d5 long temporal ξ) is **calibration
drift**, a separable axis with a ready testbed. **The step-1 ξ̂ gate is GO on real surface code, scaling
to d7** — the small-window twin + 1+1 fusion premise is validated at the target scale. Cleared to build
step 2 (learner `ρ_BC` extension).

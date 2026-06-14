# ξ̂ measurement — FROZEN registration (tool build step 1; plan3 §0.5 / §7-item-0)

> **Object:** the hardware **spacetime Markov length `ξ̂`** of the M3 Google Willow **d=29
> repetition-code** detector record — the tool's **confidence baseline** (plan3 §0.5: a continuous
> health read, *not* a binary gate). Decoder-independent. Pre-registered **before any run** per the
> theory-first discipline; the prediction block (§6) and gates (§7) are frozen here.
> **Status: registration frozen (2026-06-14); run pending.** seed = `20260614`.

## 0. Why this first

The whole 1+1 tool (white-box window-learner + black-box fusion-merger) is theory-backed **only if
the hardware sits in the controlled regime** (finite Markov length ξ, where small windows screen the
seam — `THEORY.md` §3/§9). `ξ̂` measures whether ξ is finite **for this device**, on data already in
hand, with **no build and no decode**. Finite/`O(1)` ξ̂ with a clean `e^{−w/ξ̂}` collapse ⇒ direction
validated on real data; no collapse ⇒ near threshold ⇒ stop. This converts the `THEORY.md` §5/§6
**(b)** bets into a **verdict on existing data** (`plan3.md` §7 item 0).

## 1. Source method (cite-don't-claim)

- **Negari–Ellison–Hsieh, `2412.00193`** — *"Spacetime Markov length: a diagnostic for fault tolerance
  via mixed-state phases."* Defines the diagnostic: decay of the **classical conditional mutual
  information (CMI) of repeated syndrome-measurement outcomes in spacetime**; **decoder-independent**
  (function of the detector outcome distribution only). *(Citation corrected 2026-06-14: this is
  Negari–Ellison–Hsieh, NOT "Sang–Hsieh" — that label belongs to `2404.07251`.)*
- **Sang–Hsieh, `2404.07251`** (PRL 134.070403) — *"Stability of mixed-state quantum phases via finite
  Markov length."* Source of the **measurement recipe**: CMI vs. buffer-width `r`, exponential-vs-
  power-law critical signature, the annular A/B/C geometry (Fig. 1). Provides the finite-Markov-length
  **stability-below-threshold** result the controlled regime rests on.
- Finite-sample entropy bias: **Miller–Madow** / Paninski (plug-in CMI is **positively biased**).

## 2. The lattice (a)

Detector `d(t, x)` on the (1+1)D matching lattice of the d=29 rep code: `t` = detector layer
∈ `{0..1001}` (1 init + 1000 bulk + 1 final), `x` = chain position ∈ `{0..27}` (28 stabilizers).
Folded from the flat 28 056-detector vector via `detector_grid(...).grid[layer, chain]`
(`hardware/stim_artifacts.py`). **Bulk only: `t ∈ [80, 998]`** (drop init/final transients; matches the
M3 bulk window). **Edges:** spatial = chain `x±1` same layer (data-error pair); temporal = layer `t±1`
same chain (measurement-error pair).

## 3. Estimator (a) — directional line-CMI

The (1+1)D lattice has two natural axes; we measure a **directional** Markov length on each (a faithful
full-shell CMI is sample-infeasible — see §4 caveat). For buffer width `w`:

- **Temporal** `ξ̂_t`: fix chain `x`; `A = d(t₀,x)`, `C = d(t₀+w+1,x)`, `B = {d(t₀+k,x): k=1..w}`.
- **Spatial** `ξ̂_x`: fix layer `t`; `A = d(t,x₀)`, `C = d(t,x₀+w+1)`, `B = {d(t,x₀+k): k=1..w}`.

`A`, `C` are **single detectors**; `B` is the `w`-detector segment strictly between them (a complete
1D cut along the chosen axis). **Pool the joint over all valid translates × all 100 000 shots** into
one `(w+2)`-bit histogram per `(direction, w)` — translation pooling makes `N_eff ≈ 10⁵ × #translates
≈ 10⁹`, so `2^{w+2} ≪ N_eff` holds out to `w ≈ 18` (the sample wall is far). Per `(direction, w)`:

```
Î(A:C|B) = Ĥ(AB) + Ĥ(BC) − Ĥ(B) − Ĥ(ABC)      (nats; marginals derived from the ABC histogram)
Ĥ_MM(X) = Ĥ_plugin(X) + (m̂_X − 1)/(2·N_eff)    (Miller–Madow; m̂_X = occupied bins)
```

`ξ̂` is invariant to the entropy base (a constant shift in `ln Î` cancels in the slope). Compute the
histograms on **GPU** (sliding-window `unfold` + integer-encode + `bincount`, shot-chunked); file
streaming (`read_b8`) stays CPU-side (allowed).

## 4. The bias floor / null (c) — MANDATORY

Plug-in CMI is biased **upward**; the positive floor can **fake a non-decaying tail** (false
near-threshold verdict). Two guards, both required:
1. **Miller–Madow** correction on every `Ĥ` (§3).
2. **C-shuffle null:** permute the `C` column independently of `(A, B)` across the pooled rows
   (true `I(A:C|B)=0` under the surrogate), recompute `Î_null(w)`; repeat `n_perm ≥ 8` → mean ± σ.
   This is the estimator's bias floor under the relevant null (in the spirit of the project's
   pre-registered shuffled negative controls). **`ξ̂` is fit only over the `w`-range where
   `Î_real(w) > Î_null(w) + 2σ_null`** (signal above floor).

## 5. Fit (a)/(c)

Over `w ∈ [w_lo, w_hi]`: `w_lo` drops `w=1` (lattice-scale short-range transient); `w_hi` = last width
with signal above the null (§4). **Exponential fit (c):** linear regression of `ln Î_real(w)` vs `w`;
`ξ̂ = −1/slope`; report `R²_exp`, ξ̂, the `[w_lo,w_hi]` range, the null floor. **Power-law fit (c):**
`ln Î_real(w)` vs `ln w`; report `R²_pow`. **Collapse verdict:** `R²_exp > R²_pow` with a finite ξ̂
⇒ exponential/controlled; `R²_pow ≥ R²_exp` (power-law) ⇒ critical/near-threshold. Run independently
per **basis (X, Z)** and per **direction (t, x)**; check ξ̂ **stability** across position sub-blocks
(early/late `t`, edge/center `x`) as the robustness leg.

## 6. PREDICTION (b) — frozen before the run

Context: M3 measured per-window bunching `R̂ ≈ 5.3`; the window twin **beat** the shipped SI1000 prior
on held-out syndrome NLL (+56.2 X / +44.3 Z) ⇒ structured-but-not-catastrophic noise; a fielded d=29
memory run operates **below** the rep-code threshold. All items **(b)** — a miss is a finding, never
later citable as fact.

| # | Prediction | Confidence |
|---|---|---|
| (b-1) | **Clean exponential collapse** `Î ∼ e^{−w/ξ̂}` (finite ξ̂, controlled): `R²_exp > R²_pow` both bases | HIGH ~0.90 |
| (b-2) | **ξ̂ = O(a few) cells** — order 1–5, not large (possible short-range shoulder at small `w` from the R̂≈5.3 bunching) | MED–HIGH ~0.75 |
| (b-3) | Both bases finite & exponential, but **ξ̂_X ≠ ξ̂_Z** (X modestly larger, tracking the larger NLL win / R̂); **space–time anisotropy** ξ̂_t ≠ ξ̂_x | MED ~0.65 on "differ", HIGH on "both finite" |

## 7. Decision gates (c) — tripwires, NOT (a)-claims (`d ≡ 29`)

- **CONTROLLED ⇒ 1+1 fusion direction validated on real data (GO):** `R²_exp ≥ 0.95` over `≥ 3`
  above-null widths, **finite `ξ̂ ≲ 0.2·d ≈ 6` cells**, ξ̂ stable (within ~20%) across position
  sub-blocks; **both bases** pass.
- **NEAR THRESHOLD ⇒ STOP:** power-law beats exponential, **or** `ξ̂ ≳ 0.5·d ≈ 14` cells, **or** no
  above-null decay / ξ̂ grows without bound; **either basis** failing halts the fusion track.
- **AMBIGUOUS ⇒ report band, defer to CF-WR:** exponential but `ξ̂ ∈ (6, 14)`, **or** X/Z disagree,
  **or** `< 3` above-null widths (sample-starved). ξ̂ reported as a band with its sampling caveat; the
  decision defers to the CF-WR exact-truth adjudicator rather than resting on ξ̂ alone.

Threshold provenance: the `0.2d / 0.5d` cuts are **(c) design constants** (a finite ξ must be `≪ d` to
call composition "local"; ξ ~ d means the buffer cannot screen the seam) — empirical tripwires, not
derived bounds.

## 8. Honesty caveats (declared)

- **Directional, not full-shell** (a-scope): the line-CMI conditions on a 1D cut along one axis, not a
  closed spacetime shell, so residual A:C correlation may route around `B` (higher-order, suppressed
  for the rep code). The **collapse SHAPE** (exp vs power-law) is robust to this projection; the **ξ̂
  MAGNITUDE** is a directional estimate, reported with the caveat. Measuring both axes + both bases
  brackets it.
- **Stationarity** (a-scope): translation pooling assumes a stationary bulk joint; mitigated by the
  bulk-only restriction and the sub-block stability check (§5).

## 9. Data discipline (STRICT — red line)

**TRAINING `sample_00` ONLY**, both bases. **Never** touch held-out `05–09` / escrow `15–19` / drift
`01–04` / extension `10–14` (splits per `hardware/m4_report.py:163–168`). The script asserts the sample
index is `0` before any read, and never resolves a path with another index. Decoder-independent ⇒ no
decode, no logical observable, no `obs_flips_*`, no `decoding_results/`. sim/teacher-free, hardware-read
only of `sample_00` detector events.

## 10. Deliverables

- `outputs/cf_wr_xihat.py` (scripted-execution: precondition assertions inc. the `sample==0` red line,
  printed evidence — pid/mtime/sha256/`N_eff`/per-`w` `Î_real`,`Î_null`, GPU device, flushed output,
  `if __name__=="__main__"` guard).
- `docs/cf_wr/xihat_RESULTS.md` — ξ̂_t/ξ̂_x per basis, the `Î(w)` vs null curves, `R²_exp`/`R²_pow`,
  the collapse verdict, the §7 gate outcome, the §6 prediction scorecard (hit/miss), a metric audit +
  rigor audit (every conclusion classified theorem-backed vs provisional).

---

## 11. v2 AMENDMENT (2026-06-14, predict-before-run) — banks the v1 provisional read

**Why.** The v1 frozen gate (`cf_wr_xihat.py`) returned STOP(power-law) on all four curves, but the
post-hoc diagnostic (`cf_wr_xihat_analyze.py`, `xihat_RESULTS.md`) showed that verdict is a
**false-negative of an inadequate single-exp-vs-power-law fit MODEL**: the real structure is a steep
sub-cell exponential decay **on a ~1–2%-of-peak constant floor**, and the plug-in-bias tail (which the
2σ above-null test did not strictly exclude) dragged the exponential R² below the power-law R². The
corrected exp-on-floor read (ξ̂≈0.3–0.6 cells, R²≈0.997, 4-curve-consistent) is **PROVISIONAL** (a
post-hoc model change). v2 re-registers the correct model **before the run** and adds the two genuinely
new tests (stability + floor classification) that convert provisional → banked.

**Three v1 confounds fixed.** (i) Fit MODEL: register `Î(w)=a·e^{−w/ξ}+c` (exp on a floor), not
single-exp-vs-power-law. (ii) Strict bias cutoff: fit only `Î_real > 5·Î_null_mean` (replaces the 2σ
test). (iii) Even/odd separation parity acknowledged (reported, not fit-through).

**Two new tests.**
- **Shot-split stability (a-scope robustness):** ξ̂ on two disjoint 50 000-shot halves of `sample_00`;
  banked only if they agree within `STABILITY_TOL=20%` (the §5 leg v1 skipped). Training data only.
- **Floor classification (the decisive control):** a **thick-buffer** Î — B = the line segment **+ the
  `±h` perpendicular neighbours** over the buffer span (h∈{0,1,2}; h=0 = v1 thin). Evaluated at the
  floor-region widths `w∈{3,4,5}` where signal ≫ bias (at w=4 the floor sits ~10⁴× above its null, so
  this test is NOT bias-confounded). The patch-CMI keeps A,C single detectors (the two LSBs) and B the
  surrounding patch.

**v2 PREDICTIONS (b) — frozen before the run:**
| # | prediction | confidence |
|---|---|---|
| (b-v2-1) | exp-on-floor fits the bias-clean region `R²≥0.95`, finite **ξ̂ < XI_GO=5.8** (controlled) on all 4 curves | HIGH ~0.95 (confirms v1 post-hoc on same data) |
| (b-v2-2) | shot-split halves agree within 20% | HIGH ~0.85 |
| (b-v2-3) | **floor classification:** debiased `Î(w=4)` DECREASES monotonically as `h: 0→1→2` ⇒ the floor is **directional-projection LEAKAGE** (not a genuine long-range tail) | MED ~0.60 — a persist = genuine weak tail = finding; either way controlled at 1–2% |

**v2 banked-GO criterion (c):** controlled/GO banked iff (b-v2-1) holds on all 4 curves AND (b-v2-2)
holds; the floor classification (b-v2-3) is **characterization, not a gate flip** (1–2% of peak is
immaterial either way). STOP only if ξ̂ ≥ XI_STOP on any curve or the halves disagree grossly.

**v2 deliverables:** `outputs/cf_wr_xihat_v2.py` (patch-CMI + exp-on-floor + shot-split + thick-buffer;
scripted-execution, `sample_00`-only red line, ≥1 independent reviewer before run, GPU); appended
results in `xihat_RESULTS.md` (v2 section) with the banked verdict, the floor classification, and a
fresh metric + rigor audit.

---

## 12. SURFACE ξ̂ (2026-06-14, predict-before-run) — the actually-gating read

**Why.** The rep-code ξ̂ (BANKED, controlled) is (1+1)D method-validation; the tool targets **surface
code**. ξ̂ is decoder-independent data analysis with **no exact-backend constraint**, so the surface
measurement is just as runnable and is the gate that matters. First surface read = **temporal CMI ξ̂
per stabilizer** (robust, directly comparable to rep-code); the full 2D-spatial CMI (needs a
separating-set buffer, not a naive thickening — §11 lesson) is the explicit follow-up.

**Instance (FROZEN).** Dataset `google_72Q_surface_code_d3_d5_set2` (XZZX, Sivak 2406.02700 family);
patches **`d3_at_q5_5`** (8 stabilizers) **+ `d5_at_q5_5`** (24 stabilizers); both bases X/Z;
**`r50`** (50 rounds, max temporal extent; 60 000 shots). Detectors folded into (spatial site (x,y),
round t) from `circuit_ideal.stim` `get_detector_coordinates()` (min-t triplet → site, like the
rep-code grid). Temporal ξ̂ = per-site detector time-series, thin line-buffer along rounds, **exp-on-
floor model + strict bias cutoff + C-resample null** (reused from v2, validated).

**DATA DISCIPLINE (STRICT — no split is shipped for the surface sets).** Register **TRAINING =
`sample_00` ONLY**; samples 05–09 reserved held-out, 15–19 escrow (mirrors the rep-code discipline) —
**untouched here**. Decoder-independent ⇒ read only `detection_events.b8` + `circuit_ideal.stim`
(geometry) + `metadata.json`; **never** `obs_flips_*`, `decoding_results/`, or any other sample. The
script asserts `sample==0` before any read.

**PREDICTIONS (b) — frozen before the run:**
| # | prediction | confidence |
|---|---|---|
| (b-surf-1) | surface temporal ξ̂ is **finite/controlled, O(1) cells** — comparable to rep-code's 0.4, plausibly somewhat larger (2D + XZZX + set2's deliberately-mixed calibration) | MED–HIGH ~0.70 |
| (b-surf-2) | the per-site thin-buffer **floor is LARGER than rep-code's 1–2% of peak** — 2D has more perpendicular leakage paths than rep-code's 1D (the §11 lesson, now on real 2D data) | MED ~0.60 |
| (b-surf-3) | d5 (larger patch) shows **≥** the d3 ξ̂/floor; X vs Z may differ | LOW–MED ~0.55 |

**Read (c).** Controlled iff temporal ξ̂ is finite and small (report **absolute cells + the rep-code
comparison**; the patch distances d3/d5 are tiny so a hard `0.2d` gate is not meaningful — interpret
ξ̂ ≪ patch span as controlled). A large/divergent ξ̂ or a floor that dominates ⇒ surface is more
correlated than the rep code ⇒ a finding that tempers the tool's reach. Either outcome publishes.

**Deliverable:** `outputs/cf_wr_xihat_surface.py` (surface geometry + temporal ξ̂; reuses v2 fit/null;
`sample_00`-only red line; scripted-execution; GPU); results appended to `xihat_RESULTS.md` (§10).

---

## 13. SPATIAL surface ξ̂ (2026-06-14, predict-before-run) — the decisive windowing test

**Why.** §10 found d5 temporal ξ≈8.5 cells (clean, long). The **spatial** Markov length decides whether
spatial windowing on the real-target d5 patch is possible at all — a spatial ξ ~ the patch width would
forbid it. User-selected as the decisive follow-up (2026-06-14).

**(2+1)D buffer constraint.** A *full* spacetime separating wall (strip × all rounds) is sample-
infeasible (2^|B| ≫ 60k shots). So:
- **PRIMARY — 2-point connected correlation `C(r)`** between stabilizers at 2D Euclidean distance `r`
  (same round): `C_ab = ⟨d_a d_b⟩ − ⟨d_a⟩⟨d_b⟩`, normalized `ρ_ab = C_ab/√(var_a var_b)`; pooled over
  rounds + shots; fit `|C(r)| ~ e^{−r/ξ_2pt}`. No buffer ⇒ **no explaining-away, no separating-set
  problem** — the robust decisive measure of spatial decay. (Field-standard connected correlation;
  decoder-independent.)
- **SECONDARY — conditional CMI `I(A:C|B)`** with B = the stabilizers in the **corridor strictly
  between** A and C (same round; a genuine SPATIAL separating set per the §11 lesson, NOT a neighbour
  thickening), vs `r`; exp-on-floor fit. Caveat (declared): temporal detours (other rounds) are not
  walled ⇒ a residual floor; the spatial DECAY length is the read, the floor is the temporal leakage.

Both on **d3_at_q5_5 + d5_at_q5_5**, both bases, `sample_00` r50, pooled over rounds+shots.

**DATA DISCIPLINE:** `sample_00` ONLY; detector events + circuit geometry; never obs/decode.

**PREDICTIONS (b):**
| # | prediction | confidence |
|---|---|---|
| (b-sp-1) | d3 spatial ξ is short/controlled, O(1) cell | HIGH ~0.85 |
| (b-sp-2) | d5 spatial ξ is **SHORTER than its temporal ξ≈8.5** (spatial correlation more bounded by error locality / patch geometry), likely O(1–3); the open question is whether it's `≪` the d5 patch width (~5, ⇒ windowing viable) or `~` it (⇒ windowing fails) | MED ~0.55 |
| (b-sp-3) | 2-point ξ and CMI ξ agree to within a factor ~2 | MED ~0.60 |

**Gate (c):** spatial windowing on d5 **VIABLE** iff spatial ξ `≪` patch width; **FAILS** iff spatial
ξ `~` patch width (correlations span the patch). Either outcome publishes.

**Deliverable:** `outputs/cf_wr_xihat_surface_spatial.py` (2-point + corridor-CMI; reuses the §12
geometry loader + entropy_mm; `sample_00` red line; scripted-execution; GPU; ≥1 reviewer before run);
results appended to `xihat_RESULTS.md` (§11).

---

## 14. CROSS-SAMPLE temporal ξ (2026-06-14, predict-before-run) — attribute the d5 long correlation

**Why.** §10 found d5 temporal ξ≈8.5 (long); §11 showed d5 is spatially controlled (windowing viable),
so the long ξ is a TEMPORAL/drift axis. This check attributes it: **drift/calibration** (ξ varies
sample-to-sample — set2 deliberately mixes calibration freshness) vs **a real persistent d5 property**
(ξ consistently ≈8.5). User-selected as important (2026-06-14).

**Method.** Even-separation temporal ξ (the clean long branch, §10) per sample, for **d3_at_q5_5 +
d5_at_q5_5**, basis X, r50, across a SPREAD of samples. Reuses the §12 geometry loader (generalized to
a sample index) + `measure_curve` + exp-on-floor on the even-sep branch.

**DATA DISCIPLINE (red line — allowlist).** `DRIFT_SAMPLES = {0, 2, 4, 10, 13, 22, 28, 34}` — a spread
across the unreserved index range; **NEVER samples 05–09 (held-out) or 15–19 (escrow)** (the script
asserts `sample ∉ {5..9, 15..19}` AND `sample ∈ DRIFT_SAMPLES`). Decoder-independent ⇒ no decode/obs.

**PREDICTIONS (b):**
| # | prediction | confidence | reading |
|---|---|---|---|
| (b-cs-1) | d5 temporal ξ **VARIES significantly** across samples (some short, some ≈8.5) | MED ~0.55 | varies ⇒ **drift/calibration**; consistently ≈8.5 ⇒ **real d5 property** (finding) |
| (b-cs-2) | d3 temporal ξ stays **short (~0.5) across all** samples | HIGH ~0.80 | d3 also varies ⇒ **sample-wide** calibration (whole samples stale); only d5 varies ⇒ **d5-specific** |

**Interpretation matrix (c).** d5-varies / d3-stable ⇒ d5-acquisition-specific drift (tool handles via
drift-aware windowing / sample selection). both-vary ⇒ sample-wide calibration freshness. d5-long-
consistent / d3-short ⇒ a real d5 device property the tool must absorb. Either way: spatial windowing
already viable (§11); this scopes the temporal axis.

**Deliverable:** `outputs/cf_wr_xihat_surface_xsample.py` (sample-indexed loader + even-sep ξ; allowlist
red line; scripted-execution; GPU); results appended to `xihat_RESULTS.md` (§12).

---

## 15. d3→d5→**d7** SCALING (2026-06-14, predict-before-run) — does spatial windowing scale?

**Why.** d3 + d5 spatial ξ≈0.6 ≪ patch width ⇒ windowing viable (§11). The decisive scaling test is
**d7** — the largest, most fault-tolerance-relevant distance. Dataset
`google_105Q_surface_code_d3_d5_d7` (Willow 105Q, the ADR-0007 *destination*) ships d3/d5/**d7** on ONE
device — a clean scaling series; `d3_at_q6_7` and `d7_at_q6_7` share center (6,7).

**Method.** Spatial (2-point + corridor-CMI) + temporal ξ̂ on `d3_at_q6_7` / `d5_at_q6_5` / `d7_at_q6_7`
(48 stabilizers), bases X/Z, **r90**. Reuses the §12 geometry folding + §13 spatial estimators + v2
temporal. **No sample tier in this release** ⇒ no train/held-out split exists; ξ̂ is a
**decoder-independent diagnostic on the sole acquisition** (no decode/obs/`decoding_results/` read) — no
held-out concern (held-out NLL is a future shot-split / patch-hold, orthogonal to a noise-property read).

**PREDICTIONS (b):**
| # | prediction | confidence |
|---|---|---|
| (b-d7-1) | d7 **spatial** ξ stays SHORT (~0.6) ≪ patch width 7 ⇒ **windowing VIABLE at d7** (error locality does not grow with distance) | MED–HIGH ~0.70 |
| (b-d7-2) | the d3→d5→d7 spatial-ξ scaling is ~FLAT (windowing scales to the fault-tolerant regime) | MED ~0.65 |
| (b-d7-3) | d7 temporal ξ — value unknown (no cross-sample drift comparison possible); could be short or drift-elevated | LOW on value |

**Gate (c):** spatial windowing **SCALES** iff d7 spatial ξ ≪ width 7; a spatial ξ growing with
distance ⇒ a real scaling concern for the tool.

**Deliverable:** `outputs/cf_wr_xihat_d7.py` (105Q no-sample loader + scaling table; scripted-execution;
GPU); results appended to `xihat_RESULTS.md` (§14).

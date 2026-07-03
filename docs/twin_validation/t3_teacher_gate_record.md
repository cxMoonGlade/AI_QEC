# T-#3 record — P1/P2 teacher-recovery gate PASSED (2026-07-03)

**Prereg:** `t3_bochner_estimator_prereg.md` (ef99910, committed before code). Script:
`outputs/t3_teacher_validation.py`; logs `outputs/logs/t3_teacher_validation{,_v2,_v3}.log`.

## Gate results (final, v3)

- **P1a (exact tier, n=3 chain, R=3, frozen-true dressings):**
  - Forward map ≡ verified graded engine at truth: **max|gap| = 4.44e-16** over the 9-moment
    set (order-1 interior+boundary, same-check lag-1, cross-check lag-0 ×2, cross-check lag-1)
    — the closed-form T-B moment laws (dressing powers, window bookkeeping, uniform interior
    coefficients) are exactly right on the chain machine.
  - Functional recovery (V_q^total + C(Δq,Δt) over the fitted windows): **max|ΔΣ| = 1.37e-14**
    (gate ≤ 1e-6), residual 2.2e-16.
- **P1b (sampled tier, n=5 chain, R=6, INDEPENDENT state-vector Born sampler, p_M per-check +
  p_Z π-flips, 2e5 shots × 3 seeds; η_κ and β fitted):** *[⚠ SUPERSEDED — the η/β split was the
  A-T3-1 root-cause defect (exact ridge); these numbers are the v3 band-containment result the
  review overturned; binding results = v4/v5 sections below]* functional recovery within 3×
  parametric-bootstrap bands, **all seeds — worst z = 1.47 / 1.16 / 1.02**; sampler-vs-formula
  truth max-z 2.64/1.35/2.43 (normal for a 20-moment max statistic); η̂ errors ≤ 0.004,
  β̂ errors ≤ 0.0046 and seed-varying (healthy).
- **P2 (structural):** reported kernel PSD by construction (min eig +5.8e-2; D ≥ 0 + Bochner
  sum of PSD stationary kernels — the constraint is in the parametrization, not a projection).

## Implementation notes (documented, gate criteria unchanged)

- v1→v2 fix: the dressing nuisances were initially parametrized through a SATURATED sigmoid —
  the optimizer froze them at initialization (β̂ error identical 0.0045 across all seeds = the
  init offset; bootstrap refits froze identically ⇒ bands collapsed ⇒ spurious z = 4.2/6.9
  failures on 2/3 seeds) and burned max_nfev on the ridge (950–1180 s/seed). Fix = direct
  bounded parametrization (trf, x_scale='jac'): β moves, fits converge in seconds.
  **Lesson (generalizes): never put a bounded nuisance through a sigmoid near saturation —
  bound it natively; a constant cross-seed error = a frozen parameter.**
- v2→v3 fix: bounded-trf default tolerances stopped the exact tier at resid 2.2e-6 (recovery
  1.9e-4); tightened xtol/ftol/gtol to machine scale → 1.37e-14.

## Status + next
> **⚠ SUPERSEDED — see "SUPERSEDED IN PART" and "v4 FINAL" below, then the v5 section (the
> binding state). The "unlocked" below is the PRE-REVIEW v3 claim, retracted and later
> re-established under the amended gate.**

Per prereg §6: **hardware moment extraction unlocked** — next scripts (fresh session):
`outputs/t3_hw_moments.py` (streaming b8 extraction, X basis samples 00–04, bulk layers
100–900, interior checks; DUAL-ROUTE agreement gate vs the in-repo Spitz-exact pij module
before any fit) → `outputs/t3_fit_real.py` (P3 physicality contrast / P4 held-out prediction /
P5 drift, all bands pre-registered in the prereg). R2-lite claim boundaries + A8 binding.
Un-led review of the estimator rides with the T-#3 results before reliance.

## SUPERSEDED IN PART — 4-way un-led review verdict (2026-07-03; A-T3-1 filed)

A 4-way un-led review (2× Fable: L2 derivations, estimator statistics; 2× Opus: compliance,
code) returned **SOUND-WITH-FIXES on all fronts** and one exact root-cause finding that
SUPERSEDES this record's headline reading:

- **What stands (independently re-verified by two reviewers):** forward map ≡ graded engine at
  machine eps over the whole (d,w) region for every covered moment kind; all bit/vec conventions
  consistent; parity projectors commute exactly (sequential = simultaneous measurement); the
  Born sampler unbiased at 1e6 shots; bit-identical reruns; no gate-criteria drift v1→v3;
  η_κ genuinely identified (err ≈ 0.003); gross forward-map errors caught at z = 51.
- **What does NOT stand as previously worded:** the P1b PASS certified BAND-CONTAINMENT, not
  accuracy — the implementation's undeclared η/β split created an EXACT flat direction
  (uniform-V ↔ β; Jacobian rank 11/12), the committed P1a pass relied on (unregistered)
  frozen-at-truth dressings, bands were ~2× inflated by an independent-Gaussian redraw model,
  and the acceptance region contained the zero-correlation straw. Correlation functionals
  carried band-masked bias up to +108%. "Hardware extraction unlocked" is RETRACTED pending the
  A-T3-1 v4 gate (single-η nuisance as registered, fitted-dressing exact tier on
  ridge-invariant functionals, covariance-correct percentile bands with independent seeds,
  ztruth/χ²/straw-null gates, lag-2 engine coverage, R=10 lag-1..8 sampled coverage).
- **Wording corrections:** the prereg (ef99910) was committed before the runs; the script/logs
  are outputs/ LOCAL audit artifacts (outputs/ deliberately gitignored — repo policy); the
  earlier "script committed ef99910" phrasing here was wrong. P1a = (a)-exact; P1b = (b)-band
  (the prereg's composite "(a)" label is corrected in A-T3-1). "Validated at the identifiability
  boundary" is narrowed per A-T3-1 §9.
- **L2 doc findings** (4 MAJOR, all accepted) are filed as A-L2-1 in
  `l2_imitator_and_transfer_map_derivation.md` — kernel-matching replaces TCL2-matching for the
  M3 null; differencing demoted to containment + measured additivity; P4 regime-conditioned
  (retains magnitude-level q-vs-L2a power at N̄=0 — an M3 gain); [H,Π_z]=0 +
  classification-only-noise hypotheses stated.

## v4 FINAL — ALL GATES PASS (2026-07-03; logs `t3_teacher_validation_v4{,b,c}.log`;
hardware extraction RE-UNLOCKED under the amended gate)

Three-iteration trail, every amendment committed BEFORE its rerun, no criterion level lowered:
- **v4 run 1 (N=2e5):** all accuracy gates green; **G-STRAW failed 2/3** (2.32/2.82) — the new
  power control correctly reported that 2e5 teacher shots cannot 3σ-exclude the zero-correlation
  straw. Addendum 1: teacher N aligned to the hardware-subset equivalent 5e5.
- **v4 run 2 (N=5e5):** STRAW fixed 3/3 (5.91/3.27/4.30); **seed-27 coverage failed marginally
  (3.51)** — the honest covariance-correct bands now RESOLVE the estimator's finite-sample
  curvature bias (cross-seed-consistent |bias| ~1.1–1.7e-2 with χ² in-band = parameter-map bias,
  not misfit). Addendum 2: bootstrap bias-corrected point estimate + BASIC bootstrap CI
  (recentering, not widening; hardware estimator inherits both).
- **v4 run 3 (FINAL): ALL PASS.** P1a fitted-dressing exact tier ≤1e-14 (C entries 1.0e-14,
  V-differences 8.2e-16, μ 5.6e-16, d-offset ≡ δz to 1.2e-14; forward map ≡ engine 3.3e-16 over
  12 moments INCLUDING the lag-2/μ² kind). P1b 3/3 seeds basic-CI coverage (worst std-z
  2.75/2.24/3.26, bias-corrected worst |bias| 1.1–1.4e-2 printed); G-ztruth 2.54/1.38/2.82 ≤ 4;
  G-χ² 27.1/6.6/25.7 vs dof 18; **G-STRAW 5.91/3.27/4.30 > 3** (the gate has certified power at
  hardware statistics); μ̂ errors ≤ 0.0032.
- **Carried caveats (honest):** seed-27's most curvature-exposed functional sits at std-z 3.26
  (inside the basic CI = the registered criterion; first-order bias correction only) — hardware
  runs inherit the bias correction AND print per-functional coverage detail; the d-level carries
  the DECLARED +δz p_Z-absorption offset (V-levels gauge-shifted; V-differences and all C
  entries clean); teacher power is conservative vs hardware's additional ~800-layer pooling.

**Next: `outputs/t3_hw_moments.py`** (dual-route Spitz gate — load-bearing per R2 probe C) →
`t3_fit_real.py` per the pinned P3/P4/P5 (grid, splits, seeds all fixed in A-T3-1 §8).

## v5 FINAL VERDICT — GATE FAILED; AMENDMENT BUDGET EXHAUSTED; STOP (2026-07-03;
log `t3_teacher_validation_v5.log`; the BINDING state of T-#3)

Under the pre-committed addendum-3 criterion (fresh seeds {37,47,57}, joint rank-matched
Mahalanobis coverage at 99.7%, 2000 covariance-correct draws, both intervals + pileup
reported):

- **P1a exact tier: PASS unchanged** (forward map ≡ engine 3.3e-16; C/V-diff/μ recovery
  ≤ 1.2e-14; p_Z-absorption identity exact) — the forward model and identifiability stand
  (review-PROVEN, rank 11/11).
- **P1b: seed 37 PASS (T=16.83), seed 57 PASS (T=8.53; 0/18 interval misses), seed 47 FAIL
  (T=46.28 > χ²₇@99.7% = 21.85).** Diagnostics on the failing realization: w-pileup 28.3%
  (vs 0.9%/0.1%), BOTH interval types miss 10/18 functionals, worst |f_corr − truth| = 6.29e-2
  (~2× the largest C truth) — while χ² = 8.9 (in-band; the moment fit is FINE) and μ̂/d-offset
  errors stay at 8e-4/3.3e-3. G-ztruth and G-STRAW pass on all seeds (straw T 35.1/30.4/26.1 —
  the gate has power; the sampler matches the formula).
- **The FINDING (registered miss, per the epistemic rules a reportable result, never later
  citable as "validated"):** the Bochner-constrained estimator at the pinned two-component grid
  has a data-realization-dependent fragility — when the sampled moments pull the fit into the
  w ≥ 0 boundary (pileup regime), the KERNEL-sector point estimates acquire errors invisible at
  the moment level (in-band χ²) and both bootstrap interval types under-cover. Frequency at
  hardware-equivalent statistics: 1/3 fresh seeds. This is exactly the weak-direction/boundary
  mechanism the round-3 review (R5 F2) diagnosed on the v4b data.
- **Consequence (per the pre-committed amendment budget): STOP.** No further criterion edits.
  Hardware extraction stays LOCKED. The estimator/moment-set DESIGN must change before any new
  gate registration (candidate axes for the next prereg round, NOT decided here: r-position
  pooling per moment class — the hardware fit pools ~800 bulk layers, a fundamentally richer
  statistic than the teacher's single-position moments; grid/parametrization redesign away from
  the boundary-degenerate w₀/w₁-split direction; boundary-aware inference). A NEW registered
  gate (fresh prereg section, fresh seeds) is required after the redesign.

## v6 R-POOL — ALL GATES PASS, ALL THREE REGISTERED BETS PASS (2026-07-03; run completed
2026-07-02T23:04:39 PT; log `t3_teacher_validation_v6.log`; hardware extraction UNLOCKED per
the R-POOL registration — the BINDING state of T-#3)

Registration: prereg section "REDESIGN REGISTRATION R-POOL — the v6 gate" (7f608f3, committed
BEFORE any v6 code; **ZERO-amendment budget — no criterion was touched, no rerun was needed:
one run, one verdict**). Script `outputs/t3_teacher_validation_v6.py` = the v5 machinery
line-by-line with ONLY the registered redesign (per-shot class statistic = mean of (1−2·parity)
over the pinned admissible r-positions, position counts asserted against the pinned table;
R = 12; FRESH seeds {67, 77, 87}; N = 5e5; 2000 draws; redraw streams 3000+seed; [−1,1] range
assert). Runner `outputs/run_t3_teacher_validation_v6.sh` (pipefail + PIPESTATUS captured
in-log: `python-exit=0`; rationale documented in the runner — the PowerShell→wsl.exe quote
chain pre-expands `$?` through an outer bash layer, so exit evidence must live in a script).

- **P1a exact tier: PASS unchanged** (forward map ≡ engine 3.33e-16 over 12 moments incl.
  lag-2; C entries 1.00e-14; V-differences 8.19e-16; μ 5.55e-16; d-offset ≡ δz to 1.20e-14).
- **P1b joint rank-matched Mahalanobis coverage: 3/3 PASS** — T = 5.57 / 4.65 / 6.70 vs
  χ²₇@99.7% = 21.85 (seeds 67 / 77 / 87).
- **G-ztruth 1.76 / 2.05 / 1.50 ≤ 4. G-χ² 2.7 / 1.0 / 1.5 vs dof 18, band ±24** — in-band;
  χ² sits LOW because pooled classes are strongly positively cross-correlated under the
  diagonal weighting (expected for the pooled statistic; the χ² tripwire is (c)-class).
- **G-STRAW 711.9 / 714.3 / 793.0 > χ²₂@99.7% = 11.83** — pooling multiplied the joint
  zero-kernel exclusion power ~25× (v5: 26.1–35.1).
- **Registered bets — item by item, all PASS:**
  - **b1 PASS** (pooled-SE shrink ≥ 1.8× on the 12 same-lag ℓ≤3 classes, all seeds): per-seed
    min gain **2.08 / 2.07 / 2.07**; per-class gains ℓ=1 ≈ 2.36–2.40, ℓ=2 ≈ 2.10–2.14,
    ℓ=3 ≈ 2.07–2.11 (context: o1 ≈ 2.96–3.03, xdist ≈ 2.76–2.89, x1 ≈ 2.59–2.62; out-of-scope
    ℓ=5 ≈ 2.1, ℓ=8 ≈ 1.6 — the 3-position class, as anticipated at registration).
  - **b2 PASS** (w-pileup < 5% on ALL seeds): **0.0% / 0.0% / 0.0%** over 2000 draws/seed
    (0 events ⇒ rule-of-three 95% upper bound ≈ 0.15%/seed). The v5 failure MECHANISM
    (moment noise reaching the w ≥ 0 boundary along the weak w₀/w₁ direction) is removed at
    pooled statistics, not merely made rarer.
  - **b3 PASS** (≡ the gate): coverage 3/3 + straw 3/3.
- **Diagnostics:** per-functional interval misses **0/18 percentile AND 0/18 basic on every
  seed**; worst |f_corr − truth| = 6.05e-3 / 7.46e-3 / 3.88e-3 (v5 failing realization:
  6.29e-2); μ̂ errors ≤ 4e-4; d-offset spread ≤ 1.1e-3 vs δz = 1.40e-2. P2 (reported): min
  eig +6.19e-2, PSD by construction. Runtime 801 s (no boundary-slowed fits — v5 took 1461 s).

**Power content of this PASS (addendum-3 item 7 wording, binding):** exact-tier identity +
identifiability + JOINT functional-vector consistency at 99.7% + joint zero-kernel exclusion,
at the pooled-statistic power; it does NOT certify per-functional accuracy beyond the reported
intervals. **Carried caveats:** V-LEVELS remain gauge-shifted by the declared +δz p_Z
absorption (hardware claims stay V-difference + C-entry only); teacher power remains
conservative vs hardware (~800 pooled bulk layers vs the teacher's ≤ 11 positions); the v5
registered finding (single-position boundary-pileup fragility at ~1/3 realizations) STANDS as
a finding about the single-position statistic — v6 changed the statistic under a new
registration, never the criterion.

**Next (hardware, per prereg §6):** `outputs/t3_hw_moments.py` — streaming b8 extraction
(X basis, samples 00–04 fit / 00–09 for P5, bulk layers 100–900), **DUAL-ROUTE agreement gate
vs the in-repo Spitz-exact pij module — zero-tolerance, BLOCKING** (load-bearing per R2 probe
C: it is the only protection absolute round/layer indexing gets) → `outputs/t3_fit_real.py`
(P3/P4/P5 exactly as pinned in A-T3-1 §8 + addendum 3 item 6). Un-led review of the T-#3
results before any reliance (standing rule).

## HARDWARE EXTRACTION PASS + FIT RUN TERMINATED PER MISSION RE-SCOPE (2026-07-03)

**Extraction (`outputs/t3_hw_moments.py`, log `t3_hw_moments.log`, 931 s, python-exit=0):
DUAL-ROUTE GATE PASS, integer-exact.** X basis, samples 00–09 validated (structure integers +
metadata); detector grid 1002×28 from `metadata_qubit_order`, sha-identical across all 10
samples. 634 pooled classes (384 fit: o1 28 / same ℓ1–8 224 / xdist j1–3 78 / x1± 54;
held-out: same ℓ9–16 224 / order-3 interior-κ 26), bulk layers 100–900, per-class pinned
position counts asserted. Route A (slice-XOR) == route B (UNMODIFIED M1-validated pij module)
on 249 overlap columns, **max|A−B| = 0 on every sample**; route A == route B′ (flat-gather
integer-parity, different arithmetic path) on **all 634 columns, max|A−B′| = 0** (full
sample_00). S2 reporting: bulk detection fraction ≈ 5.0–5.2%, per-layer relative spread
2.2–3.0% (≈ 20× the per-layer binomial SE — real, bounded non-stationarity; declared (c)).
Cache `outputs/_t3_moments_x00_09.npz` (37.8 MB; fit_even/odd n = 250 000 each; per-sample
n = 100 000; P3 memberships + seeds persisted).

**Fit run (`outputs/t3_fit_real.py`, log `t3_fit_real.log`): TERMINATED mid-P5 (after sample
00) on 2026-07-03 by user decision under the RE-SCOPED mission** (HANDOFF §0: hardware data =
simulator-validation target only; the real-data estimator demonstration is a downstream
milestone gated by simulator validation). Termination was scope-driven, NOT results-driven.
Results npz intentionally not written (end-of-run write); the log is the audit artifact.
**Nothing below is citable as a registered P3/P4/P5 outcome; all [PROVISIONAL] reporting:**
- Implementation gates GREEN: vectorized forward ≡ reference loop 2.78e-16 (634 kinds);
  batched-FD vs scipy-FD Jacobian routes land on the identical minimum (Δθ 2.3e-8).
- **χ² = 716 307.5 vs dof 312** on the even-half fit: the pooled moment precision (~4e-5)
  resolves a ~0.1%-relative model-class miss at 20–40σ per moment. Misspecification-direction
  language (S1/R2-lite); bootstrap intervals are sampling-only, conditional on the model class.
- **P3-style finding (the run's genuine product):** the unconstrained baseline's feasibility
  violations sit at 7.55% (N=1e3, > the registered 5%) but stay at **7.29% up to n = 2.5e5 —
  ~28/384 window blocks are PERSISTENTLY infeasible** for the Gaussian-dephasing class (the
  dressing-free r̂ = m_same/o1² ≥ 1 feasibility theorem fails on-data): the device's detector
  moments genuinely leave the model class in a specific direction. This characterization (plus
  the moment tables) is the retained **simulator-target asset** under the new mission.
- Bootstrap w-pileup ≈ 58% on all 3 streams (most of the 15 grid components at w = 0 on real
  data); fitted temporal kernel is ω=π-dominated (alternating-sign C(0,ℓ)); C-functional signs
  carry the re-signing-gauge caveat (canonicalization never implemented — R2 scope note).
- ⚠ **P4 IMPLEMENTATION DEVIATION (found in self-review, disclosed):** the unconstrained arm's
  kernel was pooled across κ (stationary-kernel baseline) instead of the pinned per-moment
  ("moment-wise") inversion of A-T3-1 §8(ii) — the printed P4 ratios (0.001 in-class / 0.138
  unfitted) reflect that deviation and are NOT the registered comparison. Any future rerun must
  fix the baseline to per-κ moment-wise inversion first. P5: 1/10 samples only, no drift claims.

**Standing state of T-#3 under the re-scoped mission:** the CURRENT-phase deliverable —
identifiability structure (p_Z-absorption gauge, ridge rank 11/11, R-POOL pooling correctness
+ the v6 joint-coverage machinery) — is ESTABLISHED by the v4→v6 chain and its review rounds;
the hardware estimator demo is PARKED (downstream, gated by simulator validation). Un-led
review of the v6 chain + extraction gate before M3 reliance (standing rule).

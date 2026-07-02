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
  p_Z π-flips, 2e5 shots × 3 seeds; η_κ and β fitted):** functional recovery within 3×
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

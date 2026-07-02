# Pre-registration — T-#3: Bochner-constrained spatiotemporal kernel estimation from real
QEC detector records (2026-07-02)

**The Branch-B "theory + hardware artifact" deliverable** (HANDOFF_math_spine §3 T-#3;
adjudication #3.1 [PROVISIONAL] no-owner: physicality-CONSTRAINED estimation × QEC-record data).
Committed BEFORE any estimator code is written or any fit is read (A4/commit-before-run).
A8 SCOPE: estimation of noise-model structure, NEVER decoding — no decoder in the validity
chain; LER appears nowhere.

## 0. What is already grounded (checked; no reinvention)

- **Forward model = the review-cleared T-B/T-#2 laws** (`tb_ident_gauge_theorem_record.md`,
  `t2_silent_floor_record.md`, both SOUND-WITH-FIXES + fixes applied): for the weight-2-check
  chain machine, order-1 detector marginals obey the hypercube/cosh law
  E[(−1)^{D_{κ,r}}] = (1−2p_M)²(1−2p_Z)^{2}·e^{−(V_q+V_{q'})/2}cosh(C_{qq'}); order-2 same/cross
  window moments obey the cosh-factorized window laws; windows are exactly local (probe
  calculus); identifiability boundary = the re-signing gauge group (sign content only via loop
  invariants); detector moments are exactly stationary in the bulk.
- **Data**: `google_72Q_repetition_code_d29` (note read in full — mandatory pre-read done):
  d=29 chain, 57q, X/Z bases × 100 sequential samples × 1e5 shots × 1000 cycles; 28×1002
  detectors/shot; b8 ingestion + Spitz-Eq.13-exact p_ij + detection fractions already built and
  M1-validated (`src/qec_twin/hardware/`). X-basis memory = phase-flip protection = the theorem
  machine class (X-type checks, Z-noise-visible) up to circuit-level noise beyond the model class
  (declared, §5).
- **Baselines (pristine, recommended settings)**: Spitz Eq. 13 exact p_ij (in-repo, ledgered,
  pre-registered pair classes); Blume-Kohout/Young 2504.14643 (note in-repo) and Bhardwaj
  2511.09491 (note in-repo) as the operational-estimator literature anchors — all UNCONSTRAINED;
  Takou 2606.11496 noted from the Brave cross-check (abstract-verified operational, no
  constraint) — cited as landscape, not run. von Lüpke: physicality EMERGENT (Huber), not
  constrained — the corrected record stands (adjudication correction 2).
- **Bochner's theorem** (standard): a stationary kernel is PSD ⇔ it is the Fourier transform of
  a nonnegative spectral measure. Operationalized here as the constraint-in-the-estimator.
- **Claim restrictions (R2-lite, ADR 0007 — binding)**: NO mechanism attribution on hardware
  (the fitted kernel is a MODEL of detector-moment structure; residuals are misspecification
  directions); no do()/counterfactual claims; prediction-calibration language only.

## 1. Mechanism / method (ANCHORED)

**Estimand.** A Gaussian-dephasing-equivalent spatiotemporal covariance model for the bulk
detector stream: per-data-qubit leg variances V_q plus a stationary cross-leg kernel
C(Δq, Δt) over the chain, on a declared window class (spatial reach |Δq| ≤ 4, temporal lag
|Δt| ≤ 8 — set by the order-1/2 moment set actually fitted; beyond-window structure is NOT
estimated). Dressing nuisances: per-check effective assignment/background factor η_κ =
(1−2p_M,κ)²(1−2p_Z)² absorbed as one multiplicative nuisance per check (identifiable from the
lag-∞ factorization limit).

**The Bochner constraint (the contribution).** Parametrize the stationary part literally by
Bochner: C(Δq, Δt) = Σ_k w_k cos(ω_k·Δt) g_k(Δq) with **w_k ≥ 0** on a declared
frequency/spatial-profile grid (g_k = declared nonneg-definite spatial profiles: delta,
exponential-decay family). Every iterate of the estimator is a valid PSD kernel BY
CONSTRUCTION — physicality is a hard constraint, not an emergent property. (Plus V_q ≥ 0,
η_κ ∈ (0,1].)

**Fit.** Weighted least squares on the registered moment set (order-1 detector marginals +
order-2 pair moments in the pre-registered pij pair classes: same-check lag 1..8, spatial
neighbors |Δq| ≤ 4 at lag 0..2), weights = shot-bootstrap SEs; NNLS/projected-gradient on
(w, V, η). The forward map is the T-B closed forms — evaluation is exact per candidate kernel
(no simulation in the loop).

## 2. Observable (the RIGHT ones — not invented)

All ledgered: detection-event fractions (hardware ledger), Spitz p_ij pair classes (ledger),
held-out moment prediction error (the composite/held-out-NLL family, applied at the moment
level with bootstrap SEs). Every fitted and held-out moment is a detector-record statistic —
decoder-free (A8).

## 3. Predicted behavior (falsifiable) + epistemic classes

- **P1 (a)-exact, teacher validation (Rule I gate — runs FIRST):** on the verified graded
  engine (the T-B/T-#2 Machine, n=3..5 chain, R=3..4) with KNOWN Σ drawn INSIDE the model
  class: the constrained estimator recovers all gauge-invariant fitted-window functionals
  within 3× the moment-SE-propagated bands, and the recovery is exact (≤1e-6) in the
  noiseless-moment limit. Sign content: only loop invariants recovered (per T-B); the reported
  representative is canonicalized (declared gauge fixing: nonneg nearest-neighbor row).
  FALSIFIER: any gauge-invariant functional outside 3σ at exact moments ⇒ estimator bug, STOP.
- **P2 (a)-structural:** the constrained estimate is PSD at every iterate incl. the reported
  one (machine-checkable, zero tolerance).
- **P3 (b)-band, the physicality contrast:** on finite-shot subsamples (N_shots ladder
  1e3/1e4/1e5), the UNCONSTRAINED plug-in inversion of the same moment set (the operational
  baseline: invert the cosh/window laws moment-by-moment, Spitz-style) produces
  physicality violations (negative implied variances, non-PSD window blocks, |implied
  correlation| > 1 — the Chen-feasible-region logic) at a rate that GROWS as N_shots drops,
  while the constrained estimator's violation rate is identically 0. Registered band: at
  N=1e3, violation rate of the unconstrained baseline > 5% of window blocks on real data
  (⚠ rung-3-flagged decision metric: "violation rate"; the standard scoring is P4).
- **P4 (b)-band, held-out prediction:** fit on half the shots of a declared sample subset
  (X basis, samples 00–04, bulk layers 100–900), predict held-out-half moments: the
  constrained estimator's weighted residual on FITTED-CLASS moments ∈ [0.8, 1.5]× the
  unconstrained baseline's (physicality costs little in-class); on UNFITTED moments (lag
  9–16 same-check; the order-3 same-check triple) the constrained estimator predicts better
  or equal (band: ratio ≤ 1.0 +0.3/−0.5) — the constraint acts as physical regularization.
  Both outcomes reportable; a large in-class LOSS (>1.5×) is a model-class misspecification
  finding (misspecification-direction language, R2-lite).
- **P5 (b)-direction, drift axis:** re-fit per sequential sample (00–09): fitted kernel
  parameters move smoothly (sample-to-sample change < the cross-sample band) — direction-only;
  magnitude reported.

## 4. Independent ground truth (Rule I, non-circular)

1. Teacher instance (P1): KNOWN Σ on the verified engine — the engine itself was certified
   against an independent state-vector MC route (S6/S7, review finding 1 closed), so the
   teacher chain is not self-referential.
2. The real-data moment inputs are computed by TWO routes: the in-repo Spitz-exact pij module
   (M1-validated) and an independent direct XOR-counting pass in the new script; must agree
   bit-derived-exactly before any fit.
3. The unconstrained baseline inversion is scored by the SAME held-out moments — no shared
   fitting machinery with the constrained estimator beyond the moment inputs.
4. Anti-circular: the estimator is NEVER validated against its own fitted moments; held-out
   splits declared here (§3 P4) before any fit.

## 5. Bounded simplifications (Rule III; unbounded ⇒ STOP)

| # | Simplification | Class | Bound / handling |
|---|---|---|---|
| S1 | Gaussian-dephasing-equivalent model class for real circuit noise | (c) declared model class | NOT claimed as mechanism (R2-lite); adequacy SCORED by P4 held-out residuals; residual = misspecification direction |
| S2 | Stationarity over bulk layers 100–900 | (c) | detector-marginal flatness checked (detection_stats layer profile) before pooling; deviation printed |
| S3 | Window truncation (|Δq| ≤ 4, |Δt| ≤ 8) | (c) | beyond-window content not estimated; lag-9–16 moments reported as held-out only |
| S4 | One multiplicative dressing nuisance per check | (c) | absorbs p_M/p_Z/boundary effects; degeneracy with V_q resolved by the lag-factorization limit; sensitivity: refit with η frozen at the detection-fraction plug-in |
| S5 | Fit = weighted LS on moments (not full-record NLL) | (c) | composite-likelihood family (ledgered); Godambe-style SE caveat carried; NLL upgrade = future work |
| S6 | X basis, samples 00–04 (+00–09 for P5) only | (c) | declared subset; Z basis + full corpus = replication axis, not this prereg |

## 6. Build plan (scripted-execution discipline)

1. `outputs/t3_teacher_validation.py` — P1/P2 on the graded engine (CPU exact algebra,
   tier-0 precedent). GATES before any hardware touch.
2. `outputs/t3_hw_moments.py` — streaming moment extraction (b8 chunked reader; CPU
   file-streaming per the GPU-rule carve-out), dual-route agreement gate (§4.2), bootstrap SEs;
   caches `outputs/_t3_moments_*.npz`.
3. `outputs/t3_fit_real.py` — constrained fit + unconstrained baseline + P3/P4/P5 scoring;
   all registered numbers printed before results (house style).
4. Every run: asserts, printed evidence, flushed, `__main__` guard; ≥3 seeds where stochastic
   (bootstrap/subsample draws); one compute job at a time.

## 7. Verdict (pre-code) + claim boundaries

Provisional until P1 gates pass and the hardware runs are scored against §3. The headline
claim class if P3/P4 land: "a physicality-guaranteed (Bochner-constrained) spatiotemporal
kernel estimator for QEC detector records, validated on known-truth teachers at the
identifiability boundary given by the T-B gauge theorem, demonstrated on real Google d29
repetition-code records against the field-standard unconstrained baselines" — a METHOD +
hardware-artifact claim. Explicitly NOT claimed: device mechanism attribution ("the device's
noise IS this kernel"), any decoding improvement, any do()/counterfactual statement, Born/CPTP
learning on hardware. [PROVISIONAL] positioning per the adjudication stands; un-led review
before any reliance on the results.

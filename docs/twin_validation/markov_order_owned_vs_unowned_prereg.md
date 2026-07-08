# Pre-registration — §3b follow-up: is the surviving cross-round memory OWNED (Markov-k) or UNOWNED (beyond)?

> **POST-RUN AMENDMENT (2026-07-01) — see §8.** Two independent reviewer panels audited the run. Code = NO
> bug. Two actions: (1) **NMAX=4 Fock-truncation bug** (found INDEPENDENTLY by in-house R4 + external codex) →
> re-run at **NMAX=8** (converged; λ=0.04 flagged). (2) **"UNOWNED" rescoped** to "beyond finite-order
> **classical** Markov on the record" — a bounded-bond process-tensor / HMM (arXiv:2412.13739, untested) would
> own it. Converged conclusion HOLDS + strengthened. The "UNOWNED" language in §2–§7 below is the original
> pre-registration wording; read it under the §8 rescope.

**Date 2026-07-01. Theory-first (literature-anchored), pre-code.** §3b established the pseudomode's
non-Markovian memory SURVIVES the mid-round measurement (Outcome A) but is SHORT-RANGE. Short-range
temporal correlation is capturable by a finite-order Markov model, so **"survives" ≠ "unowned."** This
experiment decides it: does the multi-round measurement RECORD carry structure a best-fit **Markov-k**
model cannot reproduce (UNOWNED — the genuine multi-round contribution) or not (OWNED — QMCtwin
single-round + a Markov-k patch suffices)? Classes: **(a) exact**, **(b) band**, **(c) gate**.

## 0. What is already grounded (checked; no reinvention)
- **The observable is multi-time, NOT the 2-point autocorrelation.** Kam et al. arXiv:2410.23779 §IV.C /
  L4 (`docs/papers/reading_notes/kam_nonmarkovian_surface_code_2410.23779.md`, 精读) PROVE the pairwise
  detector autocorrelation `p̄_{t,t'}` does not distinguish benign (pairwise/two-time) from catastrophic
  (streaky/multi-time) temporal correlation — "multi-time characterization is needed." **§3b's connected
  cross-round autocorrelation is exactly that insufficient 2-point statistic** ⇒ this test must use a
  multi-time statistic (the joint-vs-Markov comparison on multi-round histories, Kam's named metric).
- **Kam's fixed-marginal methodology = the right control.** Kam compares correlated vs a model matched on
  the marginals, differing ONLY in structure (Appendix A). The temporal analog here: compare the record
  vs a best-fit **Markov-k** model matched on the k-step transition statistics — the record and the
  baseline share all order-≤k statistics and differ only in the beyond-k structure.
- **Standard metric (forced ladder, rung-2 field-standard).** Testing the ORDER of a stochastic record is
  textbook: the likelihood-ratio / G² test for Markov-chain order (Anderson & Goodman 1957, *Ann. Math.
  Statist.* 28:89) and its information-theoretic equal, the conditional mutual information
  `I(mᵣ ; mᵣ₋₂ | mᵣ₋₁)` = 0 iff Markov-1 (Cover & Thomas). `G² = 2N ln2 · CMIbits`, so they are the SAME
  statistic — one gives a χ² p-value, the other an effect size in bits. Related to the ledgered
  source/channel non-Markovianity (BLP N=0.11, D_Choi=0.20, `docs/METRICS.md`) but at the RECORD layer.
- **Machinery (reuse §3b):** 1 qubit + 1 certified underdamped relaxation mode (Pilot 3/4), prep|e⟩ →
  evolve(dt) → Born-measure qubit → collapse (qubit projected, mode untouched), R rounds, over shots. The
  record is EXACT density-matrix (64-dim), no trajectory approximation.

## 1. Mechanism / regime knob (ANCHORED)
The bath is a Lorentzian of width `λ` at the qubit frequency ⇒ bath correlation time `τ_B ~ 1/λ`. **Narrow
`λ` = long memory = strongly non-Markovian (vacuum-Rabi revivals, underdamped `g > λ/2`); wide `λ` = white
= Markovian (`λ ≫ g`).** The record's Markov ORDER is controlled by how many rounds fit inside the mode's
memory (`~ τ_B/dt`). We SWEEP `λ` (fixed `g=0.42`, `dt=2.5`, matching the certified block) across the
overdamped→underdamped crossover to trace **owned → unowned**.

## 2. Observable (the RIGHT one — Kam-grounded, multi-time)
- **Primary:** `I(mᵣ ; mᵣ₋₂ | mᵣ₋₁)` (bits) and its Anderson–Goodman **G² p-value** (Markov-1 vs Markov-2,
  df=2) — the beyond-Markov-1 multi-time structure. **Second rung:** `I(mᵣ ; mᵣ₋₃ | mᵣ₋₁, mᵣ₋₂)` (beyond
  Markov-2). Estimated on the STATIONARY window (post-transient), pooled over rounds and shots.
- **Reported-but-flagged:** the §3b 2-point connected autocorrelation (lag 1–4) — carried for continuity,
  explicitly labelled Kam-insufficient (NOT the discriminator).

## 3. Predicted behavior (falsifiable) + epistemic classes
- **(a) EXACT:** Markov-1 ⟹ `I(mᵣ;mᵣ₋₂|mᵣ₋₁)=0` (definitional); the round-reset control ⟹ i.i.d. record
  (Markov-0); the G² null is asymptotically χ²(df) (theorem).
- **(b) BAND:** as `λ` decreases (non-Markovian regime) the record shows `CMI > 0` / G² rejects Markov-1 —
  a beyond-Markov-1 multi-time structure the best-fit Markov-1 cannot reproduce. **Falsifier:** if at ALL
  swept `λ` the record does NOT exceed the estimator bias floor (G² fails to reject), the surviving memory
  is Markov-k-OWNED ⇒ the multi-round contribution collapses to single-round + a Markov patch (a real,
  reportable finding — the honest-negative outcome).
- **(c) GATE:** `p < 0.05` rejection; `CMI > floor + 3σ`; plateau tolerance for the stationary window.

## 4. Independent ground-truth (Rule I, non-circular)
The record IS the exact 64-dim density-matrix evolution (no simulator approximation to certify) — so the
anti-circularity lives in the ESTIMATOR controls, of known order:
- **Bias-floor / null control:** a synthetic TRUE Markov-1 sequence sampled from the record's own fitted
  1-step transition matrix, same N, same window ⇒ its measured CMI = the finite-sample bias floor; its G²
  must NOT systematically reject (validates the χ² calibration). The pseudomode must exceed this.
- **Power / positive control:** a synthetic TRUE Markov-2 sequence (fitted 2-step transitions) ⇒ G² MUST
  reject Markov-1 and CMI must be recovered above floor (proves the instrument is not inert — anti-vacuous).
- **Order-2 rung calibration amendment (2026-07-01, pre-amendment-code):** if claiming beyond-Markov-2,
  the Markov-2-vs-Markov-3 statistic must also be calibrated: a synthetic TRUE Markov-2 sequence MUST NOT
  reject Markov-2, and a synthetic TRUE Markov-3 sequence MUST reject Markov-2. Until this pair passes,
  `CMI2` is reported as a provisional effect-size only; it is not a contribution premise.
- **Round-reset i.i.d. control (§3b):** Markov-0; lag-1 autocorr ≈ 0 (else a metric bug, as §3b caught).

## 5. Bounded simplifications (Rule III)
- **(c) Fock truncation** `nmax=4` — bounded (Pilot 3/4: nmax=3 gave ~1e-7 vs analytic).
- **(c) minimal 1-qubit + 1-mode instance** — the isolated temporal-order question (§3b); the full code
  layer (data+ancilla+modes) is (B)-full, deferred (`B_syndrome_shot_bridge_prereg.md`).
- **(a→verify) stationary window** — the "prep|e⟩ each round" protocol has a transient (§3b mean drifted
  0.31→0.13); a Markov fit to non-stationary data would mis-read drift as memory. MUST verify the per-round
  mean has plateaued (flat within shot-noise) and restrict to that window; controls share the window.

## 6. Build plan (outputs/ first; committed script)
`outputs/pilotB_markov_order_owned_vs_unowned.py`: reuse the §3b certified block; batched-over-shots exact
DM (64-dim; the project's measured CPU-default small-launch-bound regime — GPU would be launch-bound on the
sequential round loop, per `forward/kernels/README.md` d3 policy); sweep `λ`; on the stationary window fit
Markov-0/1/2, compute the CMI ladder + G² p-values + known-order controls at both tested rungs
(Markov-1-vs-2 and Markov-2-vs-3); print the owned→unowned crossover vs `λ`. Precondition asserts +
printed evidence + flushed. Reviewer before any contribution claim.

## 7. Verdict (provisional, pre-code)
Method GROUNDED: the multi-time observable (Kam, replacing §3b's insufficient 2-point stat), the
fixed-marginal-analog control (best-fit Markov-k), and the standard order test (Anderson–Goodman G² / CMI)
all exist and I can OPERATE them on the exact-DM record. The load-bearing OPEN question — whether the
surviving memory is beyond-Markov-k (UNOWNED) or Markov-k (OWNED), and at which bath regime it crosses over
— is what the run decides. PROVISIONAL until measured; a null (owned at all λ) is a genuine finding.

## 8. Results + post-run amendments (2026-07-01, post-run + two-panel adversarial review)

**Two independent reviewer panels — in-house 5-agent + external (codex / DeepSeek / GLM) — audited the run.
Code verdict: NO bug.** The G²/CMI estimator, df (2/4), the CMI↔G² identity, the Lindblad propagator, the
vec convention (vs independent qutip mesolve), the projection, and the known-order controls are all
independently validated. Two findings required action:

**(1) NMAX=4 Fock-truncation bug — found INDEPENDENTLY by in-house R4 AND external codex.** Repeatedly
injecting |e⟩ each round pumps the mode into the top Fock level at narrow bath (top-level pop 0.65 @ λ=0.04);
the NMAX=4 record statistics are cutoff-corrupted. Fix: **NMAX=8** (Hilbert dim 16) + a committed
NMAX-convergence diagnostic (λ=0.15: CMI1 4.1e-4→1.04e-3→1.08e-3 across NMAX 4/6/8, converged by NMAX≥6;
λ=0.04: 5.6e-4→2.4e-4→3.1e-5, still falling ⇒ **flagged, magnitude NOT converged at dim≤16, verdict robust**).
The verdict survives convergence at every swept λ; the earlier NMAX=4 magnitudes were wrong (λ=0.15 *under*
2.6×, λ=0.04 *over* 13×).

**(2) "UNOWNED" rescoped — in-house R5 + external codex.** The test beats a best-fit finite-order CLASSICAL
Markov chain on the record. A qubit+persistent-mode is a hidden-Markov / continuous-latent process, so a
bounded-bond **PROCESS-TENSOR / HMM** (e.g. the PT decoders `arXiv:2412.13739` / `2603.05474` — untested)
WOULD own it. Honest claim = **"beyond finite-order CLASSICAL Markov on the record,"** NOT "unowned by any
cheap model." **QMCtwin is a MASTER-EQUATION simulator (not "factorized")**; the residual gap is specifically
the **persistent shared non-Markovian SOURCE across rounds** (QMCtwin's explicit future work). Non-trivial
content = survival-through-measurement + the crossover location. **Decode-relevance is a SEPARATE deferred
layer and, per Kam 2410.23779, CANNOT be inferred from the record's temporal statistics** (a beyond-Markov
record can be decode-BENIGN).

**(3) Corrected "why genuine" argument (R4).** Sharp λ-dependence ALONE does NOT prove memory — Fock
truncation error and equilibration time are also λ-dependent. The evidence is: **NMAX-convergence + record
exceeds the bias floor 2-3 orders + the memoryless mode-reset arm is flat (Markov-0) + drift-matched null
survival.**

**Converged result (NMAX=8, hardened floor + Pearson lag).** Crossover classical-Markov-owned → beyond at
**λ≈0.30 (g/λ≈1.4, fixed dt=2.5)**; **beyond classical Markov-2 across the whole non-Markovian regime
λ≤0.30**; CMI1 peaks at λ=0.15 (~1.05e-3, non-monotonic); λ=0.04 verdict robust (p=4e-28) but magnitude
flagged. All four instrument controls + the i.i.d. null pass.

**Two MEDIUM hardenings (cross-reviewer consensus; main line unaffected).** `lag_autocorr` → Pearson
correlation (was raw autocovariance ⇒ the 3/√N null threshold was mis-scaled ~4× for binary p≈0.5);
`floorCMI` → 30-realization mean (was a single high-variance draw, CV≈1). Neither changes any verdict.

**(4) SEED-ROBUSTNESS — the single-seed run made a soft boundary look sharp (`outputs/pilotB_markov_seed_
robustness.py`).** The hardened re-run was BIT-IDENTICAL on the main line (physics on `rng`; hardenings on the
separate `ctrl_rng` + deterministic `lag`) ⇒ a REPRODUCIBILITY check, NOT sampling robustness. Re-running with
3 INDEPENDENT physics seeds (CMI1 scatters 2–91% — genuinely not bit-identical): **robust core = λ≤0.15
UNANIMOUSLY beyond-Markov-2** (peak λ=0.15 CMI1=1.1e-3, 2.4% scatter — rock solid); **soft boundary = the
owned→beyond crossover is NOT a sharp point** — at 30k shots λ=0.6 flips owned↔>M1 and λ=0.30 flips >M2↔>M1
across seeds. ⇒ **CORRECTED claim: robustly beyond-Markov-2 for λ≤0.15; the crossover is a SOFT transition
(λ~0.3–0.6), verdict power/seed-sensitive there.** The earlier "sharp crossover at λ≈0.30 / beyond-M2 across
ALL λ≤0.30" overclaimed the boundary (single-seed artifact). Caveat: the seed run used 30k shots (half
production) so part of the boundary fragility is reduced power (at 60k the main run had λ=0.30/λ=0.6 on the
significant side); a full-power (60k) multi-seed boundary run resolves whether the crossover sharpens or is
genuinely soft. LESSON: a fixed-seed re-run cannot test sampling robustness — vary the seed.

**(4-RESOLVED) Full-power boundary (60k shots, 4 seeds).** The 30k fragility was mostly REDUCED POWER, not a
genuine soft boundary. At full power the picture is a clean MONOTONE STAIRCASE (record order rises as the bath
narrows): **owned (λ≥0.6, g/λ≤0.7) → beyond-Markov-1 (λ≈0.45, g/λ≈0.9) → beyond-Markov-2 (λ≤0.30, g/λ≥1.4;
peak λ=0.15)**, with two localized crossovers (owned→>M1 at λ≈0.5; >M1→>M2 at λ≈0.35). **λ=0.6 (owned) and
λ=0.30 (>M2) are now seed-STABLE across 4 seeds** — the earlier flips were power. The ONLY marginal point is
**λ=0.35, which IS the >M1/>M2 transition edge** (marginal by nature — a verdict flip *at* a continuous
boundary locates it, it does not destabilize the conclusion). **FINAL robust claim: beyond-Markov-2 for
λ≤0.30 (strong for λ≤0.15); beyond-Markov-1 for λ≈0.45; owned for λ≥0.6.** Physically coherent (narrower
bath = longer memory = higher record order). λ=0.04 magnitude still NMAX-flagged (verdict robust).

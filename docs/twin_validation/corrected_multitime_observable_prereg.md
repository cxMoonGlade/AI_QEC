# Corrected multi-time observable — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-07-04. Predictions written BEFORE the run; a miss is a finding, not a re-fit.

**Why this doc exists.** The user retracted (2026-07-04, errors A/B/C) the matched-marginal-difference line
(G0-v2 two-point TV; G6 shared−independent; the G0-quantum `W12 = quantum − classical`). This prereg is the
**revert-to-correct** spec: it fixes the OBSERVABLE and the SOURCE and points every quantitative claim at the
already-grounded, already-run machinery, so no new engine is built ([[feedback-reuse-scaffolding-rag-first]]).
It **supersedes** the G0-v2 FAIL / G6 sub-floor / G0-quantum "GO-CORNER-ONLY" verdicts, which were measured on
the wrong observable ([[feedback-simulator-is-goal-twin-is-next]], REGRESSION WATCH).

Scope: **SIMULATOR record-char faithfulness instrument** (does the passive syndrome record carry the SPECIFIED
non-Markovian memory, distinguishable from a genuinely-Markov null) — NOT twin recovery / active QNS /
`do()` characterization, which the reading confirms is a *distinct access class* (§2, giarmatzi/White/montanalopez).

---

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / claim | mechanism paper | observable paper | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| classical 1/f = notion-2 multi-time memory (NOT CP-div breaking) | RHP 0911.4270 / BLP 0908.0238 (CP-div = reduced-map) | milz 1907.05807 (Kolmogorov Markov-order) | reading_notes/milz_when_nonmarkovian_process_classical_1907.05807.md | `OneOverFDriftSource`; `cpdiv_passive_record_check.py` |
| 2-point is INSUFFICIENT; multi-time streak is the signature | Kam 2410.23779 (Class-0/1/2 siting) | Kam 2410.23779 §IV.C | reading_notes/kam_nonmarkovian_surface_code_2410.23779.md | — |
| the RIGHT record observable = absolute multi-time ORDER test (record's departure from a genuinely-Markov-order-k GENERATIVE null); a discriminability instrument, NOT a recovery learner | — | Anderson–Goodman G²/CMI (order test); milz Kolmogorov Eq.9 | markov_order_owned_vs_unowned_prereg.md | `outputs/pilotB_markov_order_owned_vs_unowned.py` (CMI/G² ladder, 2e-10 re-impl match, χ² FPR≈0.05) |
| non-forgeable core = 1/f power-law tail beyond ANY finite Markov-k | h2 §2b (sum-of-RTNs → power-law `C(τ)`) | h2 §caveat (`E(k)` residual-energy) | h2_effectsize_g4_prereg.md | `outputs/teacher_prereg/_h2_diag4.py` (`E(k)` discriminator) |
| REALISTIC source strength (error B) | Harper-Flammia 2303.00780 (Sycamore ~0.136 avg; leakage/crosstalk; ~2× LER) | — | reading_notes/harper_flammia_learning_correlated_39q_2303.00780.md | — |
| passive record ≠ full process tensor (Υ needs ACTIVE causal breaks ⇒ twin, OUT); memory = literal correlation / distance-to-closest-Markov, NOT a 2nd-order residual (anti-error-A, tomography side) | White-Pollock 2106.11722 §IIC restricted-PT (passive ⇒ INFER not measure) + Eq.11 (necessary+sufficient NM measure) | giarmatzi 2308.00750 (measure-and-prepare causal breaks); montanalopez 2511.16772 (designed W-layer) | reading_notes/{white_pollock_process_tensor_tomography_2106.11722, giarmatzi_multitime_process_tomography_superconducting_2308.00750, montanalopez_nonmarkovian_learning_manybody_2511.16772}.md | — |
| quantum coherent imprint = 2nd-order (−8κ²), commutator sector only | Prop IW-1 (involuntary_w_check) | tn_decoders 2412.13739 (HS coherence-blind vs CD) | reading_notes/tn_decoders_process_tensor_nonmarkovian_2412.13739.md | `outputs/twin_validation/involuntary_w_check_v2.py` |
| ORDER of the classical memory = 2nd-order in κ (retires error C's "first-order"); observable must be a DIRECT multi-time witness (RB-blind spots exist) | Quiroz 2412.16092 (filter-function χ=∫SF, linear in PSD=2nd moment); Dong 2502.05408 (non-Gaussian ⇒ ≥3rd-order polyspectra, active-only) | Srivastava 2510.13051 (CCC RB r~O(δ²); Z⊗Z RB-blind Thm5 ⇒ observable-choice is load-bearing) | reading_notes/{quiroz_sparse_nonmarkovian_noise_modeling, srivastava_rb_blindspots_2510.13051, dong_nongaussian_digital_qns_2502.05408}.md | — |

## 1. The mechanism(s) (anchored; reuse where it exists)

- **Source (error B fix — REALISTIC, not the weak slice).** The classical multi-time memory carrier is the
  microscopic 1/f bath `OneOverFDriftSource` (8 weak RTNs → Gaussian, sum-of-exponentials → power-law
  `C(τ)=Σ_k v_k² e^{−2γ_k τ}`, h2 §2b). **Swept, not frozen:** per-qubit error-rate modulation set to the
  Harper-Flammia regime (avg ≈ 0.10–0.14, arXiv:2303.00780 Fig 3), NOT slice-1's γφ~1e-5 (≈6 orders below the
  readout/reset instrument, error B). Contrast arm: a single slow **RTN** (`RTNSource`) at matched correlation
  length — the h2 §caveat "slow RTN is nearly as long-memory as 1/f at feasible k" arm.
- **Siting (anchored, Kam 2410.23779).** Sweep the coupled qubit across **Class-0 (data, T2 — BENIGN
  control), Class-1 (syndrome/ancilla SPAM — CATASTROPHIC, the target), Class-2 (CZ)**. Class-1 is the
  decode-consequential, strongly-visible axis; Class-0 is the negative/benign control.
- **Carrier — CLASSICAL rate-modulation (corrected 2026-07-05; the earlier "GKSL / mode carries memory"
  language was wrongly inherited from the QUANTUM pseudomode pilot).** For a CLASSICAL 1/f source the memory
  lives in the classical LATENT trajectory ξ(t), NOT a quantum mode. Faithful model (grounded
  `cpdiv_passive_record_check.py`, [[project-cpdiv-notion-hierarchy-passive-record]]): `ξ_r = z_r/amplitude`,
  per-round bit-flip rate `p_r = clip(p₀(1+κ·ξ_r))`, CPTP bit-flip channel `(1−p_r)ρ + p_r XρX` on the coupled
  qubit (X, the error the Z-parity check detects), syndrome-extract (CX→ancilla) → Born-measure ancilla →
  collapse → reset, R rounds × shots. Exact per-round DM; NO quantum mode, NO GKSL idle-evolution. Reuse the
  small (d0,d1,a) exact-DM record path (markov_order / detector_layer carrier structure). Class-1 = source
  couples the ancilla; Class-0 = source couples a data qubit. Few-qubit exact-DM bounded; NO new engine.

## 2. Predicted observables (class (b) bands; ANCHORED — the RIGHT one, not invented)

**Primary observable = the record's ABSOLUTE multi-time Markov-order structure, vs a genuinely Markov-order-k
null.** Reuse the two-panel-validated CMI/G² ladder verbatim — a SIMULATOR-INTERNAL discriminability
instrument (does the record carry the specified beyond-Markov memory), NOT a recovery/characterization step.
**⚠ Scope guard ([[feedback-simulator-is-goal-twin-is-next]]): the observable is the order STATISTIC (the
record's exact multi-time log-likelihood-RATIO vs a fixed genuinely-Markov-order-k GENERATIVE null / its CMI).
It is NOT an "NLL learner" — no θ is fit/recovered from the record (recovery = twin, out of scope; STOP-trigger).**
At d5/r25 scale, where direct enumeration of `p(m₁..m_R)` is infeasible, the record likelihood under the
order-k null may be evaluated by an exact TN / partition-function kernel (the computation `dMLE` 2602.19722
uses) — used ONLY to score the record's departure from the Markov null, never to estimate noise parameters.

- `I(mᵣ ; mᵣ₋₂ | mᵣ₋₁)` (bits) + Anderson–Goodman `G²` p-value (Markov-1 vs Markov-2), then the order-2 rung
  `I(mᵣ ; mᵣ₋₃ | mᵣ₋₁,mᵣ₋₂)`; the **`E(k)=Σ_{ℓ≥1} ρ_res(ℓ)²`** residual-energy at the FIRST UNCONTROLLED lag
  (`>k`) for the 1/f-vs-RTN order-relative separation.
- **Predicted bands (falsifiable):**
  - **(b1)** REALISTIC 1/f on **Class-1** → `CMI > floor+3σ`, `G²` rejects Markov-1 at the Harper-Flammia rate.
    **⚠ CORRECTED (registered MISS, 2026-07-05 — do NOT silently re-fit).** The prior b1 predicted the effect
    is "FIRST-order in the coupling, FAR more visible than the −8κ² wedge." That is FALSE and is recorded as a
    miss. Verified 3 ways: (i) our derivation `Cov(M_r,M_s)=p₀²κ²Cov(ξ_r,ξ_s)` (2nd-order; the κ¹ marginal term
    vanishes since E[ξ]=0), CMI `~O(κ⁴)`; (ii) reviewer empirical (lag-1 corr 0.0285 ≈ formula 0.032; CMI1~κ⁴);
    (iii) LITERATURE — the classical dephasing memory is 2nd-order in the field: filter-function
    `χ=∫S(ω)F(ω)dω` linear in the PSD=2nd moment (Quiroz 2412.16092 Eq29-30); CCC RB `r~2δ²/3=O(δ²)`
    (Srivastava 2510.13051); non-Gaussianity only adds ≥3rd-order polyspectra needing active control
    (Dong 2502.05408). **What STANDS:** the signal is ABSOLUTE / directly measurable in the record's own
    multi-time structure (no matched-marginal subtraction) — the anti-error-A property. The advantage over the
    `−8κ²` coherent wedge (also 2nd-order) is **absolute-vs-difference-after-cancellation, NOT order-in-κ**;
    the "far more visible" claim is retired as an order-argument and is only defensible as absolute-vs-difference.
    Corrected prediction: at REALISTIC coupling (p₀≈0.10–0.14, κ≈O(0.5)) the 2nd/4th-order signal is DETECTABLE
    (smoke: p~1e-32 at N=6000), but N_detect grows as κ⁻⁴ toward weak coupling — a registered feasibility band.
    **Falsifier:** if at realistic strength Class-1 does not exceed the bias floor, the notion-2 legitimacy
    signal is sub-feasible on the passive record (a finding).
  - **(b2)** **Class-0 (data) BENIGN** (Kam): CMI ≈ Class-1 in raw magnitude possible, but decode-benign —
    reported, not the headline; the Class-1 vs Class-0 contrast is the siting law check.
  - **(b3, the honest limit)** 1/f-vs-RTN `E(k)` separation is **weak at feasible k*≈6** (h2 §caveat): the
    non-forgeable Level-3 statement ("no finite-k reproduces the 1/f power-law tail") is asymptotic-k; predict
    the `E(k)` ratio → 1 for 1/f and slowly-falling for the slow RTN, but NOT a sharp feasible-k separation.
- **INSUFFICIENT statistics — declared, NOT the headline (error A trip-wire):**
  - the **2-point** detector autocorrelation / 2-point TV (Kam §IV.C proves it cannot distinguish benign from
    catastrophic) — carried only as a Kam-insufficient reference;
  - **any `X − matched-marginal-null` point difference** (G0-v2, G6, W12): cancels the first-order classical
    memory, forces 2nd order. **Any such difference appearing as the discriminator is error A — reject it.**
    The null is a genuinely-Markov-**order-k generative** model tested by an **absolute** order statistic
    (empirical-p / likelihood-ratio), NOT a marginal-matched subtraction.

## 3. Independent ground truth (non-circular)

- **Record = exact DM** (few-qubit + few-ancilla + mode, ≤ the exact-DM bound) — no simulator approximation to
  certify; anti-circularity lives in the ESTIMATOR controls (Rule I):
  - **bias-floor / null control:** synthetic TRUE Markov-1 from the record's own fitted 1-step transition →
    its CMI = finite-sample bias floor; `G²` must NOT systematically reject (χ² calibration, FPR≈0.05 — already
    shown 2e-10 re-impl match). The record must EXCEED this.
  - **power / positive control:** synthetic TRUE Markov-2 → `G²` MUST reject Markov-1 (instrument not inert).
  - **order-2 calibration:** TRUE-Markov-2 must not reject Markov-2; TRUE-Markov-3 must reject Markov-2.
  - **memoryless arm (mode-reset / wide-λ):** Markov-0, flat — the collapse is real, not an artifact.
- **Carrier GT (corrected for the classical carrier; the mesolve/independent-boson checks were quantum-mode
  oracles, N/A here).** The per-round map is the closed-form CPTP bit-flip channel `(1−p)ρ+pXρX` — checked
  trace-/Hermiticity-/PSD-preserving and ancilla `P(a=1)→(1−p)` vs its analytic value (an independent
  closed form, NOT an engine oracle). And the record cross-round covariance is checked against the ANALYTIC
  `Cov(M_r,M_s)=p₀²κ²Cov(ξ_r,ξ_s)` derived above (independent of the record generator).
- **Srivastava blind-spot control (NEW, 2510.13051 Thm 5).** Classical temporal correlations can be INVISIBLE
  to the wrong observable (Z⊗Z → RB-blind). Register that our observable is NOT blind for the used siting: the
  memoryless arm (flat) + the Class-0/1 contrast + a positive-control arm where the injected memory is known —
  the CMI/G² witness must fire where memory is present and stay flat where it is not.
- **Detector layer `D_t = M_{t-1}⊕M_t` is OUT of the validity chain** ([[feedback-simulator-not-decoder]]);
  if computed at all it needs the Markov-k SURROGATE null (Burke–Rosenblatt/collider artifact,
  detector_layer_cmi_bridge §8) — but decode-relevance / ΔLER is the deferred decoder layer, not simulator legitimacy.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **(c) few-qubit + few-ancilla exact-DM instance**, not full d=3 — the temporal-order question is fully
  exercised on one stabilizer's time series; d≥3 spatial correction is a separate stage (MCWF/MPS carrier,
  certified vs this exact-DM). HARD: full-d3 dense-DM Liouvillian is OOM-forbidden.
- **(c) Fock truncation `nmax`** — bounded by the NMAX-convergence diagnostic (markov_order §8: converged by
  nmax≥6 for λ=0.15; the narrow-bath λ=0.04 magnitude is flagged NOT-converged at dim≤16, verdict robust).
- **(b3→bound) feasible-k separation** — the 1/f-vs-RTN `E(k)` separation is bounded weak at k*≈6 (h2 §caveat,
  exact `_h2_diag4.py`); the Level-3 claim is asymptotic-k and must be reported with this bound, never as a
  sharp feasible-k discriminator.
- **(c) ideal CNOTs / ancilla reset** — error sited by the arm; gate/reset (Class-2) errors are a deferred axis.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** Gaussian 1/f is CP-DIVISIBLE (`γ=½∫C≥0`, RHP=BLP=0) ⇒ legitimacy is notion-2 NOT notion-1;
  Kam 2-point-insufficiency; `CMI=0 ⟺ Markov-1`; `G² = 2N ln2 · CMIbits`; `G²` null ~ χ²(df); the record's
  exact multi-time log-likelihood under a fixed order-k null = a TN/partition-function contraction (the order-
  test scoring kernel — a computation, NOT parameter recovery); Prop IW-1 quadratic (coherent imprint 2nd-order,
  commutator sector only).
- **(b) bands:** (b1) Class-1 realistic-source `N_detect` / CMI magnitude; (b2) Class-0-vs-Class-1 siting
  contrast; (b3) the `E(k)` 1/f-vs-RTN separation shape. A miss is a finding, never later citable as fact.
- **(c) gates/design:** siting Class-1/2; forgeability Level-1 (beat memoryless, weak) → Level-3 (power-law
  tail, the genuine unforgeable statement, asymptotic-k); `p<0.05` order rejection; `CMI>floor+3σ`; drift
  (cross-shot, Bhardwaj 2511.09491) vs within-shot correlation split; error-A trip-wire (no matched-marginal
  difference as discriminator).
- **Provisional (NOT built-upon):** "notion-1 CP-div breaking is twirled out of the passive record" (grounded
  by Watkins-Quiroz block-diagonality + White-Pollock passive-inference + the committed C4 check, not a
  theorem in our setting); the novelty-gap claim (§below) — now UPGRADED (giarmatzi/tn_decoders/montanalopez
  full-read this session), remaining provisional only on keeling/dong/spam_robust/vonlüpke/kattemolle/facets/layden.

## 6. Novelty gap (deliverable c — upgraded, still scoped)

No paper lands "**microscopic classical 1/f bath non-Markovianity certified on the PASSIVE stabilizer syndrome
record**" as a simulator record-char instrument: milz (Kolmogorov, not on QEC — the bridge is ours);
Watkins-Quiroz (state-level, no record); noise_adapted (quantum AD, recovery not passive record); ziyad
(emergent, not injected); Kam (phenomenological masks, not a microscopic bath + not the classicality
connection); Zheng/dMLE (Pauli learnability/estimation, not the survive+certify faithfulness question);
White/giarmatzi/montanalopez (the full process-tensor Υ is **ACTIVE** — designed control + causal breaks / a
W-layer — the twin/QNS pole, explicitly the opposite of a fixed passive stabilizer schedule). The conjunction
(classical multi-time Kolmogorov/order memory × passive fixed stabilizer record × simulator legitimacy
instrument × realistic source) has NO owner — consistent with the held B.1/#3.1 no-owner verdicts.

## 7. Build org (heavy ⇒ ≥3 disjoint-ownership builders + an un-led reviewer)

- Reuse `outputs/pilotB_markov_order_owned_vs_unowned.py` (CMI/G² ladder + controls) + the dense Axis-1
  carrier (ancilla + SPAM). Builders: A = realistic-source modulation on the Class-1 carrier; B = the CMI/`E(k)`
  ladder + controls on the produced records; C = the RTN contrast arm + siting sweep. Un-led reviewer given the
  stage problem + goal + artifacts ONLY. GPU where it pays (the sequential round loop is CPU-default small-launch-
  bound per `forward/kernels/README.md`); NO concurrent GPU jobs; scripted-execution; mainline changes commit-gated.

## 8. Post-run results (2026-07-05) — Stage-1 instrument PASS

`outputs/twin_validation/corrected_multitime_observable_run.py` (FULL: N=200k, R=120, window=104, KF=30;
`python-exit=0`, elapsed 725s; evidence `..._evidence.json` sha256 `2560478e…` + sidecar). Built via workflow
(3 scouts → builder → un-led reviewer), reviewer's 3 majors + 3 minors resolved, prereg reconciled to the
grounded physics, re-smoked, then run. **GATE_RESULT: instrument=PASS** (controls_all_pass, memoryless_ok).

**Headline — the passive record carries the classical 1/f multi-time memory, distinguishable from a Markov
null at feasible N + REALISTIC coupling.** All four arms are beyond-Markov-2 with p(M1vM2)=p(M2vM3)=0:

| arm/siting | rate | CMI1 (bits) | floor1 | CMI1/floor | CMI2 | lag1 |
|---|---|---|---|---|---|---|
| 1/f / Class-0 (data) | 0.497 | 5.84e-4 | 7.4e-8 | ~7900× | 4.06e-4 | 0.80 |
| 1/f / Class-1 (ancilla) | 0.101 | 4.32e-4 | 7.0e-8 | ~6200× | 3.23e-4 | 0.029 |
| slow-RTN / Class-0 | 0.494 | 1.02e-3 | 5.6e-8 | ~18000× | 9.57e-4 | 0.80 |
| slow-RTN / Class-1 | 0.100 | 9.86e-4 | 7.6e-8 | ~13000× | 9.07e-4 | 0.039 |

**Controls (all fire, anti-vacuous):** bias-floor reject_frac 0.000–0.067 (~FPR, non-systematic); power
(true-M2→rejects M1) p=0; order-2 calibration reject_frac 0.033–0.067; order-2 power (true-M3→rejects M2) p=0.
**Memoryless arm** (time-shuffled 1/f, matched marginal, no cross-round memory): lag1 2.0e-4 (< 6.7e-3),
CMI1 3.6e-8 (≈ floor), p=0.602 → Markov-0 flat. So the memory signal (4e-4) is ~10⁴× the memoryless baseline.

**b1 (verified, corrected):** the Class-1 CMI1 signal is real and huge (6200× floor, p=0) at realistic p₀=0.10.
The **κ-scaling diagnostic → log-log slope 3.72** (predicted ~4): the signal is 2nd-order in the covariance /
~4th-order in CMI, **ABSOLUTE** (no matched-marginal subtraction) but higher-order — error C's "first-order"
is **empirically retired** (a registered miss; two-method cross-verification: derivation κ⁴ + empirical 3.72).

**b2 (finding):** Class-0 (data) raw CMI1 (5.84e-4) EXCEEDS Class-1 (ancilla, 4.32e-4) — the naive
Kam "ancilla-catastrophic" ordering INVERTS at the raw-record level, because a data bit-flip PERSISTS
(re-flips the parity every round until corrected, lag1~0.8 streaky) while the ancilla flip is reset each
round. Reported, NOT a decode-relevance claim (Kam: cannot be read off the record; the decoder layer is
deferred, out of the validity chain).

**b3 (as pre-registered, the honest limit):** E(k*=6)/E(1) = 0.166 (1/f) vs 0.110 (slow-RTN) — the 1/f-vs-RTN
separation is WEAK at feasible k. So what is demonstrated is **beyond-Markov-2** (Level-1/2, forgeable by a
larger-order Markov); the **non-forgeable Level-3** (1/f power-law beyond ANY finite-order Markov) is
asymptotic-k and NOT cleanly separated from a slow-RTN forger at k*≈6 — exactly the h2 §caveat band.

**Verdict.** notion-2 (classical multi-time record memory) is a LEGITIMATE, anti-toy simulator feature: the
coupling's specified memory leaves a record signature distinguishable from a genuinely-Markov-order-k
generative null at feasible N, realistic coupling, measured with the RIGHT (absolute multi-time / error-A-clean)
observable, all controls firing. Scoped honestly: beyond-Markov-2 (not Level-3-at-feasible-k); 2nd/4th-order
in κ but feasible; b2 siting inverts at the raw-record level (decode-relevance deferred). PROVISIONAL until
(optional) seed-robustness (≥3 physics seeds) + the production dense-carrier port; nothing built on it yet.

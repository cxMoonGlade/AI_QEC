# Validated noise digital-twin on known-truth simulators — DESIGN SKELETON

**Status: DESIGN SKELETON — for review BEFORE any code** (prevent-toy pre-draft,
`feedback-prevent-toy-from-the-start`). This is *not* a build. No `src/qec_twin/` change until
(i) this skeleton is reviewed and accepted, (ii) the effect-size / non-triviality gate (§3) is shown
plausibly met from scratch, and (iii) the targeted method-research (§5) has returned. It supersedes the
leakage-decoding direction, which was scoped largely OWNED (`docs/nonpauli_teacher/
leakage_decoding_scoping_result.md`).

Scope decision (user, 2026-06-22): **SIMULATOR-ONLY.** We do not claim real-hardware counterfactual
validation — see §0 for why this is the enabling scope, not a retreat.

---

## Provenance — what established the target (so this doc is self-contained)

1. **Leakage-decoding scoped largely OWNED** (`leakage_decoding_scoping_result.md`, 2026-06-22): over the
   *deployed* surface-code frontier (DQLR/LRU + corrMatch + RL prior), leakage's decodable LER headroom
   is largely owned/capped (Miao Fig 5c: DQLR decorrelates leakage to Pauli-like). ⇒ the program's
   contribution is **not** "beat the frontier LER via leakage-aware decoding."
2. **Landscape deep-research** (105-agent, 3-vote adversarial; `tasks/wh2t3mm75.output`) **+ a targeted
   follow-up** (4 primary-source agents + direct reads of arXiv 2201.09866 / 2603.11018 / 2605.00980):
   "digital twin" is a live 2026 term in QC, but everywhere it appears the substance is a *forward
   point-estimate emulator*. The verified unowned seam is in §0.

---

## 0. The real question + the verified contribution

**Real question (one sentence).** On a controlled simulator where the *true* noise channel is KNOWN, can
a teacher–learner noise twin recover the noise model, report HONEST uncertainty bands, and answer a
counterfactual `do()` — and be **validated** to do so *correctly* in the HARD regimes (model
misspecification, non-identifiability, finite data) — a thing no one has shown precisely because it
requires the known truth that real hardware lacks?

**Contribution — CANDIDATE, conflict-proof framing (must still pass §3).** The unowned seam is *not*:
- **lower LER** — OWNED (dMLE 30.6% rep / 8.1% surface on real Google data; corrMatch + RL-prior).
- **"quantify noise-model uncertainty" per se** — partially OWNED at small scale: GST confidence
  regions; single-transmon Bayesian posteriors (LLNL 2306.13747); IBM's deployed sparse Pauli-Lindblad
  reports bootstrap std on *measured fidelities* (direct read of 2201.09866 — *not clearly* on the
  learned coefficients λ themselves).
- **the counterfactual predict-then-verify idea** — OWNED at the *physical-gate / analytic-model* level
  (IQM 2603.11018: predicts gate-error change with **no free fit parameters**, verifies on a 49-qubit
  device).

It **IS**: an **integrated, validated-against-known-truth twin of a QEC noise field** — calibrated bands
+ a counterfactual leg, *demonstrated correct in the hard regimes*. No quantum work does the combination;
even general-statistics SBI lacks the "misspecification-aware coverage **+** counterfactual validation
against known truth" pairing ("Coverage is not enough", 2605.00980). **Unowned because it needs known
truth → simulator-only is the enabling scope.**

**Counterfactual is CORE, not dropped — HAVE ≠ CLAIM.** Counterfactual `do()` is a *core* twin capability
(`TWIN.md` "manipulate") that we implement regardless of novelty — it is **Axis D** and the `do()` ladder
(§2.2), central to the design. Listing "the predict-then-verify idea" as OWNED above means only that we
cannot *claim it as our invention* (IQM does it at the physical-gate / analytic-model level); it does NOT
mean we skip it. Our version — a counterfactual ΔLER prediction with an *honest band*, from a *learned*
model, *validated against the teacher's known true ΔLER under misspecification* — is broader than the
physical-gate point-prediction others have, and is itself the unowned contribution.

**Spine — the twin IS a validated causal model.** The object is a structural causal model (SCM): the
circuit / DEM is the causal graph, each mechanism `E_q` is a structural equation, and `do()` is Pearl's
intervention operator (TWIN.md's do()-discipline — *channel-level, parameterization-independent* — is
exactly causal-intervention rigor, not parameter-poking). The program then asks the three causal
questions and **validates each against known truth**: **recovery** (estimate the SCM), **identifiability**
(which interventional effects are recoverable from observational syndrome data — Axis B; Flammia/Wagner is
the quantum instance), and **counterfactual** (`do()` → ΔLER, validated vs the teacher's true effect, even
under a *misspecified* structural model — Axes A × D). Casting **and validating** a quantum-noise twin as
a causal model is verified-novel, and lets us reuse mature causal-inference theory (do-calculus,
identifiability, transportability, effect-estimation under misspecification). (The earlier finance↔QEC
analogy is dropped as decorative — user, 2026-06-22; it carried no load-bearing method.)

---

## 1. The object (reuse `TWIN.md`)

The twin is exactly `TWIN.md`'s object — `p(y|c) = Tr[M_y · C_E(c)(ρ0)]`, `C_E(c)=∏_q(E_q∘G_q)`,
`E_q ∈ CPTP` — with the four capabilities: **recover** (label-free Born-NLL calibration of the channel
field `E`) → **understand** (alias/uncertainty bands) → **manipulate** (`do()` → ΔLER under a frozen
decoder) → **predict** (drift). The isolation contract holds: the learner consumes only observations;
teacher ground-truth is evaluator-only.

**What is NEW here is not the object but the VALIDATION BATTERY (§2):** every band and every `do()`
output is *checked against the teacher's known truth* in a deliberately hard regime. The teacher is a
faithful, certified simulator (the leakage carrier, already certified to the d3 density-matrix oracle) —
so "validated against truth" is not "validated against a toy."

---

## 2. The validation battery — four hard-regime axes (= the verified gap, operationalized)

The four axes are the verified gap's (a)/(b)/(c)/(d), made into falsifiable tests.

| Axis | Tests (the falsifiable question) | Reused method (do not reinvent) | OPEN method-question → §5 | Class |
|---|---|---|---|---|
| **A — Misspecification** | Pauli/Markovian learner × a **misspecified teacher** (light coherent-error first; leakage carrier opt-in — §2.1): when the truth is *outside* the learner's model class, do the bands stay honest? does the `do()` keep the right **sign/direction**? | Q-posterior (Frazier 2302.06031) / fractional posteriors; **KL-pseudo-true** as the band's target; PFSR (2603.18457) / leakage-TN (2308.08186) as alternate truth generators | concrete construction of a misspecification-robust band on a noise-channel NLL; which pseudo-true target coverage is measured against; any QEC precedent | (b) bands |
| **B — Non-identifiability** | construct directions the data cannot fix (gauge / cut-space; coherence-from-binary-syndromes) with known truth → show the band **widens on exactly the unidentifiable subspace** (neither over-confident nor vacuously wide) | Flammia/Wagner "learnability of Pauli noise" cycle/cut-space (2206.06362; Wagner 2209.09267 logical channel from syndrome) as the **analytic target**; CPTP bracket; probe-richness ladder (`TWIN.md`) | how to map learnable/unlearnable onto *our* channel-field parametrization; a **directional** coverage test that the band aligns with the unlearnable subspace | (a) target / (b) band |
| **C — Finite-shot coverage** | at realistic finite syndrome counts, do the credible/confidence intervals **cover the truth at the stated rate — at the FIXED teacher truth**, not merely prior-averaged? | SBC / TARP (prior-averaged baseline) → **"Coverage is not enough" (2605.00980)** → conditional coverage at fixed truth; conformal prediction (finite-sample) | the exact conditional-coverage-at-fixed-truth protocol for our setting; whether conformal yields channel-parameter intervals; how to **certify non-triviality** (escape exact-inverse) | (b) band / (c) gate |
| **D — Counterfactual `do()`** | the twin predicts ΔLER (with a band) under a channel-level `do()` (e.g. remove leakage; weaken a mechanism) → compare to the teacher's **true** ΔLER (recomputable on the sim). Does the band cover it? Under misspecification? | `TWIN.md` `do()` discipline (Tier-0 `E_i→I`, Tier-1 `(1-a)I+aE`; frozen decoder; ΔLER metric); teacher = ground truth | how to propagate the model posterior/band **through the frozen decoder** into a ΔLER band; which `do()` set is decisive + realistic; any precedent for **interventional** coverage (beyond observational SBC) | (b) band |

A genuine twin passes the battery; a toy fails at least one axis (and must fail *loudly*).

### 2.1 The teacher ladder (qutrit / leakage is an EXPLICIT opt-in)

The misspecification teacher (Axis A) is engaged in a ladder, light → heavy:
- **First teacher — light, qubit-level, analytically tractable (recommended: coherent over-rotation).** A
  Pauli/stochastic Markovian learner *naturally* mis-models a coherent rotation; the true channel and true
  ΔLER are known in closed form; and it ties directly to the coherence-not-identifiable-from-binary
  finding (Axis B; `project-coherence-not-identifiable-syndrome-only`). Alternatives: a T1/T2
  (amplitude+phase damping) teacher, or a known correlated-Pauli teacher.
- **Leakage carrier (qutrit) — EXPLICIT opt-in only** (user, 2026-06-22): the qutrit leakage carrier is
  the *heavy* teacher, engaged only when the leakage misspecification axis is explicitly enabled, never by
  default. Rationale: get the validation battery clean, cheap, and clear on a light teacher first;
  escalate to the certified carrier for the leakage axis once the battery is trusted.

### 2.2 The Axis-D `do()` ladder (each has a recomputable true ΔLER on the teacher)

Channel-level interventions only (Tier-0 `E_M→I`, Tier-1 `(1-a)I+aE`), easy → hard, plus controls; the
frozen decoder is held fixed across all of them (ΔLER is decoder-relative):

| `do()` | what it validates | regime | use it serves |
|---|---|---|---|
| **D1 ablate** `E_M→I` | mechanism attribution ("if M were gone") | range-edge | co-design |
| **D2 attenuation curve** `(1-a)I+aE`, a∈[0,1] | the **response function** (sign + slope + shape), not a point | in-distribution | co-design / understand |
| **D3 amplify / extrapolate** a>1 | honest **out-of-distribution** prediction → bands MUST widen | hard / OOD | drift / risk |
| **D4 per-location** ablate/attenuate M on qubit q / worst CZ | **localization** ("which to fix") | medium | co-design |
| **D5 misspecified-mechanism `do()`** (on the learner's wrong image of M) | does the ΔLER band **cover the true ΔLER despite the wrong model**? | decisive | **the thesis (A × D)** |
| **D6 negative control** (`do()` on identity / a gauge-unobservable) | band **covers 0** / no hallucinated effect | decisive control | anti-toy (eliminative) |

**Most decisive for the thesis: D5** (coverage under misspecification) **+ D6** (eliminative negative
control). D2 is the most informative "does it actually understand the mechanism." D1/D4 serve co-design;
D3 serves drift/risk.

---

## 3. Non-triviality gate (prevent-toy — settle BEFORE any build)

**The killer toy = exact-inverse** (`project-perfect-results-exact-inverse-artifact`): a well-specified +
identifiable + (near-)infinite-shot setup makes recovery a trivial numerical inversion (the old
`calib_KL ≈ 1e-12` "perfect"). It proves nothing. **The design MUST live in a non-trivial regime:
misspecified (A) OR underdetermined (B) OR finite-shot (C).**

**Effect-size first (from-scratch estimate, before build).** Show that:
- (a) the Pauli-vs-leakage misspecification is **non-negligible in a decode-relevant sense** — evidence
  already in hand: ⑦ `ΔF = F_leak − F_bg > 0` (8/8 exact, z→7.69); the certified carrier;
- (b) the unidentifiable directions are **real** — coherence-from-binary ≈ 2% of the NLL gain
  (`project-coherence-not-identifiable-syndrome-only`); gauge/cut-space (Flammia/Wagner);
- (c) finite-shot uncertainty is **material** at realistic syndrome counts.

**Discriminating signatures (multiple, not one number — adversarial-self-verification A1 lesson):**
does coverage hold *at the fixed teacher truth*? does the band widen on *exactly* the unlearnable
subspace? does the `do()` band cover the true ΔLER and **degrade gracefully (not silently)** as
misspecification worsens? Build only if the from-scratch estimate says these are plausibly demonstrable.

---

## 4. Independent ground truth + constraint ledger (faithfulness, fixed up front)

Per `feedback-anti-toy-ground-truth-protocol` (three mandatory rules):
- **(I) Independent ground truth:** the teacher's KNOWN channel + its *recomputable* true ΔLER / drift —
  independent of the learner (truth never fed to the learner). NOT a check against the engine's own
  oracle. The carrier teacher is itself certified against the from-scratch DM oracle.
- **(II) Constraint ledger** — physical/statistical theorems the twin must satisfy, each with a falsifying
  test: CPTP (positivity/trace); Born-rule NLL; identifiability boundary (Flammia/Wagner cycle vs cut
  space); coverage definitions (frequentist + conditional-at-fixed-truth); the misspecification target
  (KL-pseudo-true).
- **(III) Declare + bound every simplification:** the carrier's idealized ancilla (per-round soft-syndrome /
  spatial transport excluded — Phase-1b); the `do()` tiers; the band approximation (Laplace / posterior
  sampling / conformal); the finite R and shot grids. Unbounded simplification ⇒ STOP.

---

## 5. The pinned research questions (→ the targeted methods deep-read; 4 clusters, one agent each)

1. **(A)** The concrete recipe for an **honest band under misspecification** on a noise-channel NLL —
   Q-posterior / generalized (fractional) posterior / KL-pseudo-true: exact construction, the pseudo-true
   target coverage is measured against, and any QEC/quantum precedent.
2. **(B)** How to map the Flammia/Wagner **learnable/unlearnable (cycle/cut) decomposition onto our
   channel-field parametrization**, and a **directional coverage test** certifying the band widens on
   exactly the unlearnable subspace.
3. **(C)** The exact **conditional-coverage-at-fixed-truth protocol** (vs prior-averaged SBC/TARP) for our
   setting; whether conformal prediction gives finite-sample *channel-parameter* intervals; and how to
   **certify non-triviality** (a positive control that the exact-inverse regime is escaped).
4. **(D)** **Interventional / counterfactual coverage** — propagating a model posterior **through a frozen
   decoder** into a ΔLER band, and any precedent for validating *interventional* predictions against known
   truth (beyond observational SBC).
5. **(cross)** Any **end-to-end protocol / benchmark** for "validate a UQ model against synthetic known
   truth in the hard regimes" we should mirror so the result is field-recognizable.
6. **(causal)** Which **causal-inference tools** should a quantum-noise *causal* twin reuse —
   do-calculus, causal identifiability / transportability, causal-effect estimation under model
   misspecification — and is there any precedent for framing **and validating** device noise as a
   structural causal model (vs the hard-coded forward emulators we found)?

---

## 5.5 Method decisions (targeted methods research returned 2026-06-22; 5 primary-source agents)

Concrete method per axis (the §5 questions are answered):

- **Axis A band (misspecification):** the **Q-posterior** (Frazier et al., arXiv:2302.06031) — a score-based posterior whose credible sets carry the **sandwich (Godambe) covariance** `H⁻¹VH⁻¹` *by construction*, giving correct frequentist coverage of the **KL-pseudo-true** parameter `θ⋆ = argmin KL(truth‖model)` under misspecification AND in small samples, using only first derivatives (we already autodiff the channel NLL), no tuning constant. Target = `θ⋆` computed **directly from the known teacher** (anti-circular). Subtleties: reparametrize off the CPTP boundary (logit rates) where `θ⋆` pins a rate at 0; estimate `V` at the right unit of independence (per-shot vs cluster-robust for cross-round correlation). Cross-check = Müller plug-in sandwich; power/fractional posterior only as an isotropic scan (calibrate via GPC, NOT SafeBayes — SafeBayes ≠ coverage). **No quantum precedent** applies robust-covariance/pseudo-true to noise recovery (GST "wildcard" 2012.12231 budgets misspecification in *observation* space — complementary, not this).
- **Axis B (identifiability → directional bands):** the unidentifiable subspace has a **constructive analytic basis** — cycle space (learnable) vs **cut space (unlearnable SPAM gauge, `2^n−c` DOF; Chen-Flammia 2206.06362)** for sequence data; the **logical channel `P_L` = coset-sum marginal** (identifiable iff *correctable*; Wagner 2209.09267) for syndrome-only data; **coherence is a third, separate bracket axis**. A **structural ansatz shrinks the gauge** to `𝒬⁻¹(T∩Im𝒬)` (2410.03906) — the lever that *earns* identifiability. Directional test (all must agree): Fisher-null = analytic cut space; profile-likelihood flat-to-physical-boundary on gauge (= the bracket width); posterior-contraction ≈1 learnable / ≈0 gauge; **directional coverage at fixed truth**.
- **Axis C (coverage):** mirror the **"Coverage is not enough" (2605.00980) fixed-truth protocol** — `N≈1000` datasets at a FIXED teacher `θ*`, report the across-realization posterior-shape battery (mean/SD/68-95 widths/skew/kurtosis) + per-realization KL & Wasserstein — NOT prior-averaged SBC/TARP (which pass while miscalibrated at a fixed truth). Local diagnostic = **L-C2ST (2306.03580)**; finite-sample *parameter* coverage under misspecification via **CP4SBI/LoCart (2508.17077)** (plain conformal covers outputs only, marginally). **Non-triviality positive control (escape exact-inverse, 3 levers):** width `∝1/√S` (not ~0 at realistic shots `S`); under misspecification the estimate is biased but bands widen & still cover; under underdetermination the band reverts to PRIOR width (a broken engine reporting a tight band there fails loudly). Benchmark scaffold to mirror = **sbibm** (C2ST metric, sim-budget sweep).
- **Axis D (counterfactual coverage) — interventional coverage is ITSELF a GAP:** SBC certifies the parameter posterior, NOT the `do()`-band. Build **"interventional SBC"** (draw `θ~prior`, apply `do()`, recompute the **true** ΔLER on the teacher, infer the band, test that the rank of true ΔLER is uniform) + **conditional coverage at fixed `(θ, do())`**. Band recipe: **paired MC over the posterior → frozen decode → ΔLER** (PAIR the `do()` draws — common-mode cancels); **delta-method / `decision_pushforward` gradient** as the cheap cross-check (but MWPM ΔLER is piecewise-constant in DEM logits → under-covers across decision boundaries; use MC for the band); **failure-spectrum transform** (Beverland 2511.15177) for the below-threshold tail (Pauli-only ansatz → validate vs exact enumeration for a coherent teacher). Our **re-runnable teacher sidesteps** the unobserved-counterfactual problem that forces weighted/DR conformal (Lei-Candès 2006.06138) elsewhere → we check coverage **directly**.

**⚠ EXTEND existing in-repo work — do NOT duplicate.** The research surfaced that the repo ALREADY has a counterfactual-validation harness: **`docs/cf_wr/`** (THEORY.md + registration.md) — `E_do = knob_dler_error` = `|ΔLER_glue(do) − ΔLER_true(do)|` as a **co-primary AND-gate** vs the frozen teacher, `D_Choi`, the `decision_pushforward`/`V_do` gradient, pre-registered (b) bands; plus `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` and reading notes (Kobori-Todo Bayesian noise params 2406.08981, fail-fast 2511.15177, Nasr counterfactual-non-identifiability, learnable-logical-noise 2601.22286). This IS Axis D partly built. The new design must **extend cf_wr by adding the coverage / interventional-SBC / identifiability-band layers it lacks**, not restart. [ACTION: read `docs/cf_wr/` before finalizing the build plan.]

## 5.6 Precedents to cite + honest novelty positioning
- The **integrated** object (noise-as-SCM + channel-`do()` + ΔLER + validated-vs-known-truth teacher) is **novel as a synthesis**, but every *component* has prior art → the contribution is **the synthesis + the validation loop**, NOT "we invented causal modeling of quantum noise." (Position carefully or a referee reads overclaim.)
- Cite prominently + distinguish: **Giarmatzi-Costa** quantum causal *discovery* of a process (npj QI 2018, arXiv:1704.00800 — closest *quantum*; discovers process structure, not a phenomenological noise SCM scored by ΔLER) and **DTCF** "Digital Twin Counterfactual Framework" (arXiv:2604.01325 — closest *method*: a twin validated by a hierarchical counterfactual regime, but **classical**, zero quantum). We are their **unoccupied QEC intersection**.
- The **empty triple** (learned noise posterior × `do()`-ΔLER × validated coverage band) is our slot; closest partials = Xiao-Gullans 2601.21472 (logical predict-verify, no Δ / no band), ACES 2502.21044 (LER vs sim-truth, shot-noise band, no Δ), IQM 2603.11018 (physical-gate Δ+verify, not logical / not learned).
- **Counterfactual ≠ interventional:** do-calculus / ID-algorithm (Shpitser-Pearl) / doubly-robust are level-2; the hard coherent-**abduction** is level-3 (Nasr non-identifiability, in-repo) → resolved **only** by controlled-teacher validation = the load-bearing novelty (the program's b-validity, ADR 0002). **Transportability** (Bareinboim-Pearl selection diagrams / S-nodes) is the formal object for the d3→d5/d7 + toy→Google generalization, and coincides with the program's existing `ξ̂` Markov-length gate.

## 6. Epistemic status (METRICS.md declaration)

- **(a) exact** — the cited theorems/definitions only: Flammia/Wagner learnability; CPTP; Born-rule NLL;
  the coverage definitions; KL-pseudo-true as the misspecified-target definition. These are the only items
  usable as a derivation basis.
- **(b) prediction bands** (registered falsifiable bets; a miss is a finding): the four battery claims —
  bands cover under misspecification (A); band widens on the unlearnable subspace (B); finite-shot
  conditional coverage holds (C); the `do()` band covers the true ΔLER (D).
- **(c) gates** (go/no-go only): the non-triviality gate (§3); the effect-size bar; the build-iff decision.
- The **CONTRIBUTION** claim (§0) is **PROVISIONAL** (a candidate) until §3 (effect-size) and §5 (method
  research) clear. Nothing is built on it as a premise before then.

---

## 7. What this IS / is NOT

- **IS:** a design skeleton + a research-framing doc. It defines the validation methodology and the
  simulator-only scope. The leakage carrier is **reused** as the misspecification teacher, not re-derived.
- **IS NOT:** a build (gated on §3 + §5); a real-hardware claim (simulator-only by design); a new carrier;
  an LER-beating claim (owned). It does not assume the contribution — §3 can still kill it (e.g. if the
  misspecification effect is negligible, or coverage is trivially achievable = exact-inverse).

---

## 8. Current status + build roadmap (consolidated 2026-06-23)

**Scope (confirmed, user 2026-06-23):** simulator-only, a **scientifically-correct, known-truth
surface-code TEACHER** (we control the noise ⇒ ground truth). NOT the real Google XZZX data now —
real data is the **Phase 5 future external-validation rung** (indispensable eventually, not the current
build). Matches the sim-only scope (§0); removes any data-ingestion dependency now.

**Relationship to CF-WR (Paper-2):** the twin's composition/counterfactual substrate already exists as
CF-WR (Choi object, `E_do`/`D_Choi`, sim-only `do()` discipline, theory-first/scripted-execution,
ξ̂-GO-on-d7). We **align to CF-WR in format/framework**, but **reuse its CODE only after step-by-step
省察 vs independent ground truth** (user 2026-06-23). twin = CF-WR substrate + the NEW honest-uncertainty
UQ layer (Axes A–D as *validated* capabilities). Definitions/metrics align to CF-WR; the UQ regime
(misspecified/finite-shot) is new and NOT covered by CF-WR's exact-window (a)-theorems.

**Code 省察 inventory (2026-06-23):**
- USABLE (merge, verified): `forward/cptp_channel.py` (apply_kraus / choi_matrix [gauge-invariance
  proven] / Stinespring CPTP learner / **PTM = independent non-Pauli oracle**);
  `forward/exact/circuit_sim.py` (zero_state / apply_unitary / measure_parity_enumerate +
  **rx/ry/amplitude_damping = the coherent-teacher primitives**); `knobs/intervention.py`
  (do_remove/do_weaken [convex-mix CPTP verified] / `B_LER`=`E_do` [non-vacuous, guarded by
  |ΔLER|≥5×floor] / differentiable_ler); `cf_wr_geom.py` (distance independently re-verified — but a
  ONE-SIDED Z-plaquette toy; for surface we move to a real CSS/XZZX geometry).
- AVOID: `recover_channel`'s full-rank + IC + exact-action default (= exact-inverse toy).
- REPAIR (necessary): the CF-WR teacher is **classical** (bit-flip Markov; φ unimplemented) ⇒ build a
  genuinely non-Pauli teacher from the verified primitives.
- UNBUILT: the 2D `D_Choi`/`E_do` scoring (CF-WR windows/glue/score, pending).

**§3 Axis-A gate RESULT (`outputs/twin_uq_axisA_gate.py`, reviewer-verified):** multi-round coherent
`rx(θ)` IS observable misspecification, growing with R (machinery sound: KL(R=1)=0 analytic, R-growth
coherence-specific, fair Pauli fit, stim-validated). **BUT ~99.75% of the signal is in the TERMINAL DATA
READOUT — the binary syndrome STREAM is coherence-blind even multi-round** (3rd hit on
coherence-not-identifiable-from-binary; `project-twin-axisA-gate-result`).

**Observation surface (decided, user 2026-06-23):** **syndrome stream + transversal data readout** — the
standard memory record, realistic, and what a faithful twin must model (not the artificially-blind
syndrome-only stream). Extensible to **multi-basis transversal readouts** (Z reads X-coherence, X reads
Z-coherence) = the probe-richness ladder for full coherence sensitivity. Caveat: on real d3 coherence is
empirically small (~2% NLL); large at higher coherence / more rounds / near threshold.

**Substrate (decided):** a **scientifically-correct d=3 surface/XZZX teacher** on the sim (9 data, 2^9
exact single-round; multi-round via the carrier — d3-surface 8-check multi-round branch enumeration
explodes as 2^(8R), exactly the carrier's job), NOT the rep-code toy. **Axis-A teacher:** coherent
over-rotation made observable via the data-readout surface, known truth (optionally a syndrome-observable
correlated-Pauli mechanism as a second Axis-A teacher).

### Build roadmap (Phase 0–5)
| Phase | Deliverable | Status |
|---|---|---|
| **0 (now)** | scientifically-correct d3 surface teacher (known truth) + syndrome+transversal-data observation surface + **hardened §3 gate** (fold in the incoherent control + the syndrome-vs-data chain-rule split) confirming Axis-A observable & non-trivial | teacher forward partly exists (exact backend + carrier); gate exists, re-target |
| **1 (RECOVER + Axis-A band)** | misspecified Born-NLL learner on the surface teacher + **Q-posterior honest band**, validated to cover the KL-pseudo-true under misspecification (conditional coverage at fixed truth) | calibration exists (rep-code); Q-posterior + validation battery NEW |
| **2 (Axis-B + Axis-C)** | identifiability-directional bands (cycle/cut-space + Wagner mapping + band-widens-on-unidentifiable test) + finite-shot conditional coverage + non-triviality controls | NEW; recipes concrete |
| **3 (Axis-D)** | `do()`→ΔLER band on the surface teacher, validated vs the teacher's true ΔLER (extend `E_do` to 2D + the band) | `E_do` exists (rep-code); extend + band |
| **4 (predict/drift + integration)** | drift/predict axis + four-capability integration | least-developed |
| **5 (FUTURE: real-data validation)** | point the validated twin at real XZZX data + transportability caveat | future rung (user: indispensable, later) |

**Honest distance:** the little plan = **Phase 0** (substrate + GO). The **core, unowned, publishable
twin = Phases 1–3** (recover + honest band + validated counterfactual, on the controlled surface teacher,
in the hard regimes) ≈ 3 focused build+validate+review cycles. Full four-capability twin = +Phase 4;
real-device validation = Phase 5 (future). The UQ layer (1–3) is the bulk + the novel content — well
defined, methods research-de-risked, each Phase prevent-toy-gated.

## References (verified primary sources)

- dMLE (LER bar): arXiv 2602.19722. Sparse Pauli-Lindblad (deployed, UQ on fidelities): 2201.09866 /
  2311.15408. Learnability/gauge: 2206.06362, Wagner 2209.09267. Misspecification-robust Bayes:
  Frazier 2302.06031. Coverage pitfall: 2605.00980. Counterfactual at physical layer (owned): 2603.11018.
  Non-Pauli/leakage truth generators: PFSR 2603.18457, leakage-TN 2308.08186, QMCtwin 2606.19848.
  Calibration-twin baselines: 2504.08313, 2603.14607, 2605.30676.
- Internal: `docs/TWIN.md`, ADR 0004 (finance↔QEC), ADR 0008 (carrier), `leakage_decoding_scoping_result.md`,
  memory `project-digital-twin-noise-landscape`.

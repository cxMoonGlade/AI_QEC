# The Twin — Plan 3: The Small-Window Twin and its Composition Limit

Redirected mainline for **the twin** (`qec_twin`), 2026-06-14. Division of labor unchanged:
[`docs/TWIN.md`](TWIN.md) is the **object contract**; the [ADR spine](adr/) records
**decisions**; [`PLAN.md`](PLAN.md) is the whole-project **path** (B→HARDEN→C);
[`plan2.md`](plan2.md) is the decision-regret extension. **This file narrows the project's
*identity and headline* to its validated strength — the small (≤15q) exact-backend window
twin — and the one open problem — composition** — and **explicitly retires** the ambitions
that were falsified, scooped, or W1/scale-blocked. It moves nothing inside the claim
boundary; it chooses *which* validated work becomes the contribution.

**How to read it.** Items are **STRICT** (non-negotiable) or **FLEXIBLE** (chosen later).
The two problem-gates in §3–§4 are each a **triple — physical / mathematical / aim↔object
— plus a falsification signal**, in the `plan2.md` style. §1 is the explicit retire-list;
nothing retired may be silently re-pursued.

---

## 0. Thesis (one paragraph)

The twin's **validated strength is the small exact-backend window**: it recovers
(label-free exact Born-NLL), manipulates (`do()`→ΔLER, controlled), and predicts on
windows, and on **real Willow d=29 rep-code it beats the shipped SI1000 prior on held-out
syndrome NLL** (M3, +56.2 X / +44.3 Z nats/shot/window). The **one open problem is
composition**: how to stitch small-window twins into a faithful global representation.
Plan 3 makes the contribution the **honest characterization of this** — (1) *where small
coherent-window twins recover faithfully on real data*, and (2) *where and how they compose
into the whole, on GPU, against exact ground truth and real data* — **not** a beat-SOTA
model and **not** a novel training technique (both retired in §1). The contribution that
survives every prior-art search — **the coherent channel slot + the validated `do()`
counterfactual + the honest negative** — is given a concrete, defensible identity here.


## 0.5 Tool-first reorientation (2026-06-14, owner) — NEAR-TERM PRIORITY

**Build the TOOL, not the paper.** The paper's certified characterization (§1–§6 below) is **deferred,
not dropped**; the near-term deliverable is a working, scalable, calibrated QEC-noise digital twin. The
theory (`THEORY.md`, P2/P3/P4) is repurposed as the tool's **calibration + confidence machinery**, not a
set of claims to freeze.

**The architecture — "1+1":**
- **Component A — recover-learner (white-box, exists).** Per-window CPTP Born-NLL fit, M3-validated on
  real data. Small extension: also emit the overlap/seam marginals `ρ_BC` the merger needs.
- **Component B — fusion-merger (black-box, new).** A GNN amortizing the **constructive shallow-circuit
  covering** (2604.01197's (k+1)-layer local-recovery schedule), outputting the **full composed channel
  field** with honest uncertainty bands. Black-box is fine — **trust comes from calibration, not
  self-certification** (ADR 0008: a learned surrogate has no exactness class, so it never carries an (a)
  premise; it carries a calibrated band instead).

**Calibration + confidence machinery (the theory, repurposed — NOT certify-or-abstain):**
- **Petz bound `√(I_nats)` = the CERTIFICATE** where Petz is feasible (small/controlled cases).
- **Exact truth (CF-WR) = the VALIDATION HARNESS** — CF-WR's new role: calibrate the GNN-merger against
  Petz/exact-truth, not deliver the paper's headline verdict.
- **Honest uncertainty bands = the OUTPUT** — the tool gives "answer ± calibrated band," *not*
  certify-or-abstain (the project's own bands style; rigor lives in the band, §1.3 PLAN.md).
- **`ξ̂` (hardware Markov length) = the CONFIDENCE indicator** — high below threshold, degrading-with-warning
  near it; a continuous health read, *not* a binary gate.
- **Engine layering:** constructive rule (2604.01197 covering / GNN amortization) → certificate (Petz bound)
  → uncertainty (band) → confidence (ξ̂). Petz is the *certificate*, not the *engine* (it is optimal-but-
  expensive and does not scale; the constructive covering does).

**What the tool delivers:** the four capabilities (recover / understand / manipulate (controlled) /
predict) on the **full composed channel field** — calibrated, GPU-scalable (GNN amortization), with honest
bands and a `ξ̂` confidence read.

**Build order (near-term):**
1. **`ξ̂` measurement** — the tool's confidence baseline; cheap; M3 d=29 syndrome record (**training
   samples only — never held-out 05–09 / escrow 15–19**); spacetime-Markov-length diagnostic (2412.00193).
2. **learner extension** — emit `ρ_BC` overlap marginals.
3. **fusion engine v0** — the constructive covering + a first GNN amortization; calibrated on CF-WR exact
   truth vs Petz; outputs full channel + bands.
4. **pipeline on real surface data** — learner → fusion → global channel + bands; global held-out NLL vs
   shipped baselines (set2 d3).

**Discipline (relaxed for the tool, still honest):** validation-via-bands (not freeze/abstain); GPU-only
model compute; scripted-execution; baselines pristine; isolation contract; honest uncertainty. The
paper-certified core (Petz / sufficient-functional / ξ̂-below-threshold) stays available as a subset when
the paper track resumes.

---

## 1. The contribution (the wedge, given an identity) — PAPER TRACK (deferred per §0.5)

**Headline (STRICT):** *the small-window coherent twin + its composition limit, characterized
against exact ground truth and real hardware.* This is a **characterization + honest-negative**
contribution, not a beat-SOTA claim — and characterization with measured limits is far less
scoopable than "a better number," because a competitor cannot take "we exactly measured where
it works and where it breaks."

**Delta vs prior art (cite, never claim):**
| Prior art | What it owns | Our delta |
|---|---|---|
| Windowed/modular decoding (Skoric, Tan, Cain) | composes *decode decisions* | we compose a *coherent channel field*, not decode decisions |
| TN contraction (BSV, dMLE 2602.19722) | Pauli windowing by bond dimension | we carry a *coherent slot* the Pauli TN structurally cannot (T-B theorem) |
| Markov-length/CMI, BP, quantum BP (Hsieh, Kuwahara, Leifer-Poulin) | the composition *theory/tool* | we *apply* it to a coherent-channel twin and *measure the threshold* against exact truth |
| dMLE / Ahmed 2208.00812 / SparseMAP / Berthet / 2601.00242 | the training/diff machinery | adopted as cited tools; not our claim |

---

## 2. Problem 1 — small windows on REAL data (validate the strength)

**STRICT:** the small-window twin must be validated on **real quantum data, not just the toy**.

- **BANKED:** **M3** — real Willow d=29 rep-code, window twin beats shipped SI1000 on held-out
  syndrome NLL (+56.2 X / +44.3 Z, one-sided 99%). The 1D-rep-code real-data win exists.
- **REMAINING — R2-lite-b (surface extension):** validate the window twin on **real
  surface-code d3 windows** — dataset **set2** (`google_72Q_surface_code_d3_d5_set2`), the only
  release shipping **pij + uninformative + RL × 3 decoders** as baselines. Score **held-out
  per-shot syndrome NLL** vs the shipped baselines on the d3 plaquette/boundary windows;
  isolate coherent-structure recovery where the data permits (flag where randomized-compiling
  twirls it away). FLEXIBLE: which d3 patches / round levels, fixed at pre-registration.

**Gate P1 (triple + falsification):**
- *Physical:* the window twin is the exact Born-NLL on real surface syndromes (not moments).
- *Mathematical:* held-out NLL beats the shipped baseline at a declared significance, on
  identical held-out splits, with bootstrap CI.
- *Aim↔object:* recover validated on real **2D surface** windows, not only 1D rep-code.
- *Falsification:* **no NLL win on surface d3** ⇒ the small-window strength does **not** extend
  from 1D to 2D — a reportable finding (the strength is rep-code-specific), not a hidden failure.

---

## 3. Problem 2 — composition into the whole, on GPU

**STRICT:** composition is validated against **exact ground truth AND real data**, and the
realization is **GPU**. STRICT: composition preserves CPTP + the Born interface (no format that
drops the coherent slot — the M4 lesson).

**Three composition arms** (scored together against exact truth):
- **G0 — mean-field / conditional-product** (baseline; the K1/M4 naive rule, suspected artifact).
- **G1 — Petz rotated-recovery** (the **exact ground-truth-correct anchor**; expensive).
- **G-graph — graph-model composition** (the **scalable GPU realization**, per the graph
  intuition): a **factor-graph / MRF over windows+seams with belief propagation**
  (Leifer-Poulin **quantum BP** for the coherent case), and/or a **GNN learned-BP anchored to
  G1**. Batched message passing → **GPU-native, sparse, scalable**; ties to the vendored
  graphical-model baselines (`pgmpy`, `pomegranate`, `coniii`, `GGLasso`); **higher-order
  factors can host the M4 bunching** the independent-edge DEM cannot.

**Validation, two anchors:**
- **Controlled (exact truth):** **CF-WR** (`docs/cf_wr/`, frozen) — the 12q exact toy; G0 vs G1
  vs **G-graph** against the exact per-seam reduced Choi blocks; the threshold **ξ\*** (where
  composition breaks vs bunching R̂), the GO/NO-GO routing, the Petz-vs-mean-field coefficient.
  *(CF-WR's registration gains G-graph as a third arm; see §4 note.)*
- **Real data:** compose the **surface-d3 window twins (Problem 1)** via the CF-WR-validated rule
  into a global representation; score **global held-out NLL** (does composition help globally
  vs single-window / vs shipped baselines).

**GPU (STRICT):** exact backend (static-Kraus CUDA graphs) + Petz (GPU linalg) + graph-BP/GNN
(batched) + dMLE-TN bulk — all GPU; M3 proved the 84-fit/22-min GPU path. CPU only for the
ratified decode evaluator.

**Gate P2 (triple + falsification):**
- *Physical:* composition preserves CPTP and the Born interface; the coherent slot survives the
  composition (no DEM-format collapse).
- *Mathematical:* composed global Choi/NLL within the per-seam `√(I_nats)` bound vs exact (CF-WR);
  **G-graph ≈ G1 where valid**, on GPU, at lower cost.
- *Aim↔object:* windows compose into the whole, **characterized by ξ\*** (works up to ξ\*, breaks
  beyond).
- *Falsification:* **even G1/G-graph fails at the hardware correlation regime (R̂≈5.3)** ⇒
  composition has a **PROVISIONAL ceiling at this ξ** — the M4 root promoted toward a
  theorem-grade negative (NOT a hidden failure; the registered NO-GO branch).

**Coherent caveat (STRICT, declared):** classical graph models (MRF/BP) are clean for the
**Pauli** case; the **coherent** case needs **quantum BP** (approximate, no loopy-convergence
guarantee on the QEC Tanner graph). Where quantum BP cannot certify, **abstain-flag** rather than
assert (the H2/K1 discipline). The graph framing inherits the coherent-slot risk; it does not
remove it.

### Theoretical backing — the composition limit is HIGH (pre-run theory gate, 2026-06-14)

A multi-agent theory push settled the composition limit for both sectors; full derivations in
`docs/cf_wr/{P2_derivation, P3_coherent_CMI_prefactor, P4_sufficient_functional}.md`. **All borrowed
theorems cite-don't-claim** (§1 table).

- **Diagonal/classical — (a)-exact, limit = decodability threshold.** Commuting/classical Gibbs ⇒ CMI
  is *strictly zero* past the interaction range (Brown–Poulin 1206.0755) ⇒ **exact reconstruction with a
  CONSTANT buffer `w ≥ R₀`** in the bulk; the `ξ·log(L/ε)` factor survives only in the thin critical
  window near `p_c`.
- **Coherent/perturbative — controlled below threshold, (a)-core + (b)-macroscopic.** A weak coherent
  edge `φ` on a classical-Markov bulk keeps `I(A:C|B)=κφ²` with a **local — not `exp(Θ(|A|+|C|))` —
  prefactor** (rides the classical Markov screening; numerically airtight: κ flat under a 6-order global-floor
  collapse). **The CONCLUSION is PRIOR ART** (Sang–Hsieh 2404.07251 + Zhang–Gopalakrishnan 2511.01976
  finite-Markov-length stability — cite, never claim); **our narrow delta is the explicit Kubo–Mori
  coefficient `κ`** (P3: (a) leading coefficient, (b)-conditional macroscopic escape, two named gaps C1/C2).
  Operating point `φ∈{0..0.15}@R̂≈5.3` is *inside* the controlled regime — a falsifiable (b) CF-WR tests.
- **★ The operational TARGET is the SUFFICIENT FUNCTIONAL, not the full state (P4 — the genuine new
  contribution).** Composing `V_NLL ∪ V_do` (NLL-/decode-sufficient directions) gives a **strictly higher
  limit `ξ*_func ≥ ξ*_full`** ((a)-structure: projection is a contraction; (b)-magnitude = what the
  E_do/D_Choi gate measures) and **keeps the coherent wedge** (NLL sees bunching, M3). Trap: `V_do`-only
  forfeits the wedge to windowed decoding if MWPM is coherent-blind (M4, (b)/provisional). Four-leg
  separation: full state = **certificate** (P2/P3) · reduced functional = **target** (P4) · reduced Choi
  blocks = **representation** (amendment 1) · local generators = **recovery object** (already-escaping,
  Ivashkov 2603.05492).

**Scope caveat (STRICT).** The published shallow-circuit guarantee (2604.01197, Hu et al., 2026) covers the
**trivial phase only** — the escape applies to the **per-window shallow noise-channel-field state**, NOT the
macroscopic below-threshold code state. **All controlled bounds collapse at the decodability transition
(ξ→∞)** — the project's predicted R̂∈{5–8} crash. The limit being "= the threshold" is the *maximum
attainable* (above it is physically unreconstructable, not a rule deficiency).

**The decisive empirical gate — `ξ̂` (do FIRST, cheap, uses existing M3 data).** Measure the hardware Markov
length `ξ̂` from the M3 d=29 repeated-syndrome record via the spacetime-Markov-length diagnostic
(Negari–Ellison–Hsieh 2412.00193, decoder-independent). Finite/O(1) `ξ̂` with a clean `e^{−w/ξ̂}` collapse ⇒ the
hardware sits in the controlled regime ⇒ the whole direction is validated on real data **before any build**;
no collapse ⇒ near threshold ⇒ stop. This converts the theory `(b)` into a verdict on existing data.

---

## 4. Both outcomes publish (no white-run branch)

| | GO / positive | NO-GO / negative |
|---|---|---|
| **Problem 1** | window twin beats baselines on real surface d3 (strength extends to 2D) | no win on surface (strength is rep-code-specific) — a finding |
| **Problem 2** | windows compose to a faithful global twin up to ξ\*, GPU-feasible — the carrier path | composition ceiling at ξ (M4's root) — a theorem-grade negative |

Both are **characterization + honest negative** — reportable, go/no-go-usable, and **less
scoopable than a SOTA claim**. The project's value does not hinge on a positive.

---

## 5. Epistemic + execution discipline (inherited, STRICT)

- **Epistemic status** on every quantitative item: **(a)** exact / **(b)** prediction band
  (miss = finding) / **(c)** gate. Provisional conclusions are reportable but build nothing.
- **Theory-first:** predicted direction/scaling/threshold written before every run.
- **Frozen decoder for *scoring*** (the `do()` discipline); a differentiable/soft decoder, if
  used, is a *training* tool only (train-soft / eval-hard), never a scoring change.
- **GPU-only model compute**; scripted-execution (assertions + printed evidence + spawn guard);
  **baselines pristine**; isolation contract (learner sees only observations).
- **Real-data rung:** held-out split declared and used **once**; sim/teacher-only for the
  controlled (CF-WR) lane; no hardware `do()` (§1.4).
- **Cite-don't-claim** the borrowed tools (§2 table); the metric ladder ([METRICS.md](METRICS.md))
  governs every score.

---

## 6. The evidence chain (nothing wasted)

Plan 3 reuses every prior milestone as one continuous argument, not scattered results:

> **B-path** (window counterfactual validated against teacher truth) → **M3** (window NLL win on
> real hardware) → **M4** (naive independent-edge composition fails to transfer = the negative)
> → **CF-WR** (principled composition — G0/G1/**G-graph** — judged against exact 12q truth) →
> **ADR 0008** (carrier) → **R2-lite-b + real-data composition** (the strength + the gluing on
> real surface data) → **Plan 3** = the characterization that ties them into one defensible,
> unscoopable contribution: *the small-window coherent twin and its composition limit.*

---

## 7. Immediate execution order

0. **`ξ̂` gate (do FIRST — cheap, decisive, uses existing M3 data):** measure the hardware Markov
   length via the spacetime-Markov-length diagnostic (Negari–Ellison–Hsieh 2412.00193) on the M3 d=29
   repeated-syndrome record; finite/O(1) `ξ̂` with `e^{−w/ξ̂}` collapse validates the whole direction
   on real data before any build (the theory `(b)`→verdict step, §3 Theoretical backing).
1. **Finish CF-WR** (controlled composition characterization) — teacher (φ co-primary) →
   windows → glue (now G0/G1/**G-graph**) → score; GO/NO-GO on the 12q exact truth.
2. **Add G-graph to the CF-WR registration** as the third composition arm (factor-graph BP /
   GNN learned-BP anchored to G1), scored against exact truth alongside G0/G1 — a documented
   pre-run amendment.
3. **R2-lite-b** (Problem 1 surface extension): set2 d3 window-twin held-out NLL vs shipped
   pij/uninformative/RL.
4. **Real-data composition** (Problem 2 real side): compose the set2 d3 window twins via the
   CF-WR-validated rule; global held-out NLL.

All on GPU; all theory-first pre-registered; both outcomes publish.

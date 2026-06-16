# The Twin — Plan 3: The Small-Window Twin and its Composition Limit

Redirected mainline for **the twin** (`qec_twin`), 2026-06-14. Division of labor unchanged:
[`docs/TWIN.md`](TWIN.md) is the **object contract**; the [ADR spine](adr/) records
**decisions**; the archived [`PLAN.md`](_archive/PLAN.md) is the whole-project **path** (B→HARDEN→C);
the archived [`plan2.md`](_archive/plan2.md) is the decision-regret extension. **This file narrows the project's
*identity and headline* to its validated strength — the small (≤15q) exact-backend window
twin — and the one open problem — composition** — and **explicitly retires** the ambitions
that were falsified, scooped, or W1/scale-blocked. It moves nothing inside the claim
boundary; it chooses *which* validated work becomes the contribution.

**Live front (2026-06-14):** the **real Google Willow XZZX `d7_at_q6_7` window-covering coherent channel
field**; the `ξ̂` gate is **BANKED GO** (real surface d3→d7), so the build is cleared. §0.5 carries the
reorientation + converged design decisions; §7 carries the build order.

**How to read it.** Items are **STRICT** (non-negotiable) or **FLEXIBLE** (chosen later).
The two problem-gates in §3–§4 are each a **triple — physical / mathematical / aim↔object
— plus a falsification signal**, in the `plan2.md` style. §1 is the explicit retire-list;
nothing retired may be silently re-pursued.

---

## 0. Thesis (one paragraph)

The twin's **validated strength is the small exact-backend window**: it recovers
(label-free exact Born-NLL), manipulates (`do()`→ΔLER, controlled), and predicts on
windows, and on **real Willow d=29 rep-code it beats the shipped SI1000 prior on held-out
syndrome NLL** (M3, +56.2 X / +44.3 Z nats/shot/window); the windowing premise is now **confirmed on
the real surface device** (`ξ̂` spatial ≈ 0.7 / temporal ≈ 0.5, flat d3→d7, BANKED GO). The **one open
problem is composition**: how to stitch small-window twins into a faithful global representation.
Plan 3 makes the contribution the **honest characterization of this** — (1) *where small
coherent-window twins recover faithfully on real data*, and (2) *where and how they compose
into the whole, on GPU, against exact ground truth and real data* — **not** a beat-SOTA
model and **not** a novel training technique (both retired in §1). The contribution that
survives every prior-art search — **the coherent channel slot + the validated `do()`
counterfactual + the honest negative** — is given a concrete, defensible identity here.


## 0.5 Tool-first reorientation + the live front (2026-06-14) — NEAR-TERM PRIORITY

**Build the TOOL, not the paper.** The paper's certified characterization (§1–§6) is **deferred, not
dropped**; the near-term deliverable is a working, scalable, calibrated QEC-noise digital twin. The theory
(`THEORY.md`, P2/P3/P4) is repurposed as the tool's **calibration + confidence machinery**, not a set of
claims to freeze.

**The live front is the real XZZX surface code.** The mainline target is the **window-covering coherent
channel field on the real Google Willow XZZX `d7_at_q6_7` patch**
(`docs/whitebox/window_covering_architecture.md`, `surface_recover_registration.md`). The `ξ̂` confidence gate
is **BANKED GO** — hardware spatial `ξ ≈ 0.7`, temporal `ξ ≈ 0.5`, flat across d3/d5/d7 on Willow 105Q,
both ≪ patch width (`xihat_RESULTS.md` §14–§15) — so the window build is cleared on real data at the
fault-tolerant target before any window is built. M3 (d=29 rep-code NLL win) and the CF-WR 12q toy are
**banked evidence**, not the live build.

### 0.5.1 The four corrections (STRICT, load-bearing)

Bound every step below; none may be silently relaxed.

1. **Adjacency = circuit-derived, never geometric.** Which data qubits couple — carry 2q mechanisms,
   define the covering — is fixed by the circuit's 2q gates + error-propagation lightcone + crosstalk,
   captured by the **DEM**, never by coordinate distance. (The real d7 circuit is nearest-neighbour, so
   geometry ≈ circuit here, but that is a coincidence to be *proven*, not assumed.)
2. **Never collapse to Pauli.** The density matrix is carried precisely to host **coherent non-Pauli /
   non-Clifford** channels (RZZ, parasitic couplings, over-rotation). Collapsing to a "Pauli rate" =
   reverting to the DEM = the M4 failure mode = the whole point lost. The model **always represents
   coherence**; identifiability constrains what may be *claimed* (a band), never what may be *represented*.
   The mechanism dictionary is **coherent-non-Pauli-first**.
3. **Mechanism selection = identifiability-driven, not hand-picked.** No "core set." The full ≤2q catalog
   is an **overcomplete dictionary** (the hypothesis space); the identifiable subset is fixed by the
   **data** (Fisher rank / probe richness) and reported as identified vs aliased + band. Earned, never
   assumed (the alias-quotient discipline, ADR 0005).
4. **Residual ≠ mechanism-correct — two independent gaps.** (a) model-class gap (held-out residual /
   `B_misspec`): can the model fit the observations; (b) identifiability/alias gap: a zero residual can
   still leave mechanisms aliased. A small residual does **not** prove the mechanism is right. **Report
   both axes** — held-out observational sufficiency (NLL) + alias structure (Fisher rank + per-mechanism
   alias band). Unseparable ⇒ report the alias class, never a false attribution. Mechanism *separation* is
   scored only on a **controlled teacher** (with ground truth); real data reports only sufficiency + alias
   bands, never mechanism ground truth.

### 0.5.2 The window covering (construction + verified facts) — STRICT geometry

Detail: `docs/whitebox/window_covering_architecture.md`. Plan-level facts:

- **Model = a field of window channels.** Each window = the radius-1 ball in the share-a-stabilizer graph
  = the **3×3 data block (≤9 data qubits)**; one window per data qubit ⇒ a **complete covering** (every
  connected weight-≤t configuration is native to ≥1 window; t = ⌊(d−1)/2⌋ = 3 at d7). Each window is a
  multi-qubit CPTP map on its ≤9-qubit density matrix (2^≤9, exact backend).
- **Window ⟺ d3-patch.** The dataset ships its patches nested on one 105Q device; an interior d7 window is
  exactly a d3-patch footprint — **verified**: the d7 window centred at data (6,7) has data == the
  standalone `d3_at_q6_7` patch `data_qubit_coords`, exactly. The **nine shipped d3 patches are nine
  real-hardware window twins** (9 locations × 2 bases × round levels), each with its own circuit + data.
- **Verified circuit facts** (real `d7_at_q6_7` `circuit_ideal.stim`): `num_qubits = 101` = 49 data + 48
  measure + 4 idle boundary ancilla; device is 105Q (4 device qubits unused). Roles are read from the
  circuit (`M` = measure, sweep-CX init = data), never from coordinates.

### 0.5.3 The architecture — "1+1"

- **Component A — recover-learner (white-box).** Per-window CPTP Born-NLL fit (M3-validated machinery,
  `calibration/hardware_nll.py`), extended to the multi-qubit window channel; emits the recovered channel +
  the overlap/seam marginals `ρ_BC` the merger needs.
- **Component B — fusion-merger (black-box, new, deferred).** A GNN amortizing the covering's bounded
  consistency-merge (2604.01197's (k+1)-layer local-recovery schedule on the trivial-phase channel field),
  outputting the full composed field with honest bands. Black-box trust comes from **calibration, not
  self-certification** (ADR 0008: a learned surrogate has no exactness class, so it carries a calibrated
  band, never an (a) premise). Long-range (graph-distance >1, disconnected) correlations the windows
  structurally cannot see are the GNN's job; their budget is measured in step-1 (§7).

### 0.5.4 White-box recovery methodology

- **Parameters live on the FIELD, indexed by support-tuple** (1q@data, 2q@circuit-adjacent pairs,
  3q@connected triples — 3q deferred-but-ready). Each mechanism has one canonical home window ⇒
  **deduplicated by construction**; the 49 overlapping windows are evaluation units, shared parameters
  tied (not duplicated).
- **Per-window stabilizer taxonomy (STRICT three-way):** **full-in** (support ⊆ the 9 window data),
  **seam/cross-boundary** (support intersects the window but reaches outside — *not* d3 boundary checks),
  **external** (support disjoint). An interior d7 window has only **~4 full-in** weight-4 plaquettes (not
  8) + ~8 seam stabilizers.
- **The seam is load-bearing for recovery, not only for chains.** The full-in observations (~4 detectors)
  are underdetermined for the window's mechanism dictionary, so fully recovering even within-window
  mechanisms requires the seam stabilizers (which couple neighbours). This is *why* cross-window
  composition is the hard core.
- **d3-first build path. CURRENT ACTIVE SCOPE (2026-06-15): rung 3a only — the d3 single-window
  white-box; rung 3b (d7 seam-coupled) and step-4 cross-window composition are DEFERRED (trigger-gated,
  not dropped — re-open when d3 recovery + the coherence-survival measurement justify the seam).** Rung
  3a: recover on the **nine real d3 patches** (full 8-stabilizer observation, no seam) — the clean
  real-data recovery + identifiability rung. Rung 3b: the 40 d7-interior windows (full-in underdetermined
  ⇒ seam-coupled joint estimation). (d3-run vs d7-run are separate acquisitions; per **D2** each scale is
  fit from its OWN data — only the dictionary/identifiability *structure* is portable, absolute values
  are drift-affected and reported separately.)
- **Forward (D3).** Multi-round window-local coherent spacetime marginal. **Runtime forward = dense
  ≤13q surface-block ancilla-projector Born likelihood**, fit by a **block-marginal composite
  likelihood** (`ℓ(θ) = Σ_j log P_θ(σ_{T_j})`): evolve data + block ancilla (9 data + ≤4 ancilla,
  ≤13q) through the faithful round to the pre-measure state, enumerate the ≤4 ancilla projectors +
  readout flip, record `P_θ(σ_{T_j})` per block. The dense `WindowChannel` is the engine and
  correctness oracle. The full d3 faithful register (17q = 275 GB) is never run whole; blocks stay
  ≤13q, GPU-feasible. (The 9q data-register + per-stabilizer instrument approach was tried and
  falsified — retired.) Detail: `docs/whitebox/d3_whitebox_recover_design.md`.

### 0.5.5 Representation invariants (STRICT)

- **Source of truth = coherent Kraus / Stinespring** (mechanism-strength parameterization): CPTP /
  non-Pauli / non-Clifford **by construction**. The model body is always this.
- **PTM / Choi = derived lenses** computed from the Kraus model (interconvertible by reshuffle):
  composition (PTM product), CP check (Choi PSD), TP check (PTM first row), and the **coherence budget =
  PTM off-diagonal mass = exactly what a Pauli/DEM export discards** (band-tracked, itself a reportable
  result).
- **Never diagonal-truncate the PTM in the model** — that is the Pauli twirl = DEM = the forbidden
  collapse (correction 2); diagonal-truncation appears only as the lossy downstream export to a Pauli
  decoder. PTM off-diagonal mass above threshold (when mechanisms are coherent) is a **checkable red-line
  assertion** that coherence was not silently twirled.

### 0.5.6 The seam-confirmation gate (deferred to a measurement)

Whether the white-box must *confirm* coherent composition at the seam — vs leaving the seam to the GNN +
held-out NLL — is **gated on a measurement**, because syndrome-NLL cannot by itself certify coherence (the
coherent channel is aliased with Pauli at the syndrome-statistics level; two-gap, correction 4). Sequence:
(1) bank per-window white-box recovery on the real d3 patches (no seam); (2) measure the **coherence
budget** (PTM off-diagonal mass on recovered windows — does coherence survive real multi-round data?);
(3) only if coherence is non-negligible **and** claimed → build a white-box seam **certificate** (CPTP +
`ρ_BC`-consistency + cross-seam PTM off-diagonal) as the GNN's anchor; else leave the seam to GNN + NLL
(Pauli-level). External evidence locates the coherent value in the **correlated / cross-window** regime
(Darmawan 2403.08706: local small-θ coherence → Pauli-adapted near-optimal; Harper 2605.29514: coherent
crosstalk raises LER) — so the coherence-survival measurement targets cross-seam / correlated coherence,
not local within-window coherence.

### 0.5.7 Carrier candidates (ADR 0008) — three by decomposition axis

Beyond the ≤14q exact-density-matrix window wall, the scalable coherence-preserving **forward** has three
candidate engines, each scaling on a different sparsity resource:
- **exact-window** (ours) — scales on **short correlation length** (ξ ≈ 0.7, *measured*); exact within
  window, seam at the boundary.
- **stabilizer-TN** (Harper 2605.29514) — scales on **sparse magic** (few/weak non-Clifford insertions);
  whole-code, exact within stabilizer rank; forward-only (no learning).
- **tensornet-mps** (CUDA-Q / cuTensorNet) — scales on **low entanglement** (bond dimension); pure-state +
  trajectory only (no mixed-state/MPDO, no autodiff through truncation); needs a bond-dimension pilot on a
  2D coherent patch before adoption.

Which holds is empirical (which sparsity the real noise has) — to be measured, not assumed. **CUDA-Q is
closed for the window forward** (verified, CUDA-Q 0.14 / cuQuantum 26.03): no GPU exact-density-matrix
*circuit* backend (only CPU `density-matrix-cpu`); no differentiation w.r.t. channel-strength parameters on
the matching backend; the GPU path (`cudaq.dynamics` / cuDensityMat) is Lindblad-only with **no
coherent-Kraus slot** and no mid-circuit measure/reset (another instance of the ADR 0008 "no coherent
slot" pattern). The existing differentiable GPU torch density-matrix backend (`forward/exact` +
`cptp_channel` + `kernels`, M3 CUDA graphs) wins for the window. `cudaq-qec` decoders are potential
evaluator/baselines only.

### 0.5.8 Calibration + confidence machinery (the theory, repurposed — NOT certify-or-abstain)

- **Petz bound `√(I_nats)` = the CERTIFICATE** where Petz is feasible (small/controlled cases).
- **Exact truth (CF-WR) = the VALIDATION HARNESS** — calibrate the GNN-merger against Petz/exact-truth,
  not deliver the paper's headline verdict.
- **Honest uncertainty bands = the OUTPUT** — "answer ± calibrated band," *not* certify-or-abstain (rigor
  lives in the band, §1.3 PLAN.md).
- **`ξ̂` (hardware Markov length) = the CONFIDENCE indicator — BANKED GO** on real d3→d7 (above); a
  continuous health read, high below threshold, degrading-with-warning near it.
- **Engine layering:** constructive covering / GNN amortization → certificate (Petz bound) → uncertainty
  (band) → confidence (ξ̂). Petz is the *certificate*, not the *engine* (optimal-but-expensive, does not
  scale; the covering does).

**What the tool delivers:** the four capabilities (recover / understand / manipulate (controlled) /
predict) on the **full composed channel field** — calibrated, GPU-scalable, with honest bands and a `ξ̂`
confidence read.

**Discipline (relaxed for the tool, still honest):** validation-via-bands (not freeze/abstain); GPU-only
model compute; scripted-execution; baselines pristine; isolation contract; honest uncertainty; plus the
four corrections (§0.5.1) and representation invariants (§0.5.5). Build order: §7. The paper-certified core
(Petz / sufficient-functional / ξ̂) stays available as a subset when the paper track resumes.

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
| Coherent-crosstalk simulation (Harper 2605.29514) | hybrid stabilizer-TN *forward* sim (magic-rank decomposition, whole-code) | we *learn* a coherent window field from real syndromes (inverse, not forward); spatial covering, not magic-rank |
| Decoder adaptation to local noise (Darmawan 2403.08706) | near-optimal TN decoder + selective mischaracterization, *local* noise only | we carry *correlated* (bunching) coherent structure his locality excludes; we learn the model, not adapt a decoder to a known one |

---

## 2. Problem 1 — small windows on REAL data (validate the strength)

**STRICT:** the small-window twin must be validated on **real quantum data, not just the toy**.

- **BANKED:** **M3** — real Willow d=29 rep-code, window twin beats shipped SI1000 on held-out
  syndrome NLL (+56.2 X / +44.3 Z, one-sided 99%). The 1D-rep-code real-data win exists.
- **LIVE — real XZZX windows (105Q d3/d7):** validate the window twin on the **real Google Willow
  XZZX patches** (`google_105Q_surface_code_d3_d5_d7`). Rung 3a: the **nine shipped d3 patches** (full
  8-stabilizer observation = nine real-hardware window twins, both bases, round levels) — clean held-out
  per-shot syndrome NLL + Fisher identifiability, no seam. Rung 3b: the d7-interior windows (full-in
  underdetermined ⇒ seam-coupled). Score held-out NLL; report coherent structure as observational
  sufficiency + alias band (correction 4), never mechanism attribution on real data. Baselines: the
  shipped SI1000 / RL / Harmony / Libra arms (evaluator-only). FLEXIBLE: which d3 patches / round levels,
  fixed at pre-registration. (set2 72Q d3 remains a secondary rung with its pij/uninformative arms.)
  Detail: `window_covering_architecture.md`, `surface_recover_registration.md`.

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

**The decisive empirical gate — `ξ̂` — RESOLVED, BANKED GO (2026-06-14).** Measured via the
spacetime-Markov-length diagnostic (Negari–Ellison–Hsieh 2412.00193, decoder-independent), first on the M3
d=29 rep-code (temporal `ξ ≈ 0.4`) and then on the **real surface device**: spatial `ξ ≈ 0.7`, temporal
`ξ ≈ 0.5`, **flat across d3/d5/d7** on Willow 105Q, all ≪ patch width, clean `e^{−w/ξ}`-on-floor collapse
(`docs/cf_wr/xihat_RESULTS.md` §14–§15). The hardware sits in the controlled regime; windowing scales to
the fault-tolerant target ⇒ the whole direction is validated on real data **before the window build**. The
one anomaly (72Q-set2-d5 long temporal `ξ`) is calibration drift (separable axis). The theory `(b)` is now
a real-data verdict: **GO**.

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
- **The four corrections (STRICT, §0.5.1):** circuit-derived adjacency; never collapse to Pauli;
  identifiability-driven mechanism selection (overcomplete dictionary + Fisher); residual ≠
  mechanism-correct (two-gap reporting).
- **Representation invariants (STRICT, §0.5.5):** Kraus/Stinespring source-of-truth (CPTP/non-Pauli/
  non-Clifford by construction); PTM/Choi derived lenses; PTM off-diagonal = coherence budget = what the
  Pauli/DEM export discards; never diagonal-truncate the PTM in the model.

---

## 6. The evidence chain (nothing wasted)

Plan 3 reuses every prior milestone as one continuous argument, not scattered results:

> **B-path** (window counterfactual validated against teacher truth) → **M3** (window NLL win on
> real hardware) → **M4** (naive independent-edge composition fails to transfer = the negative) →
> **`ξ̂` BANKED GO** (real surface d3→d7 controlled, windowing scales) → **window covering** (real XZZX
> d7, circuit-derived, window ⟺ d3-patch) → **`WindowChannel`** (coherent non-Pauli dictionary + PTM
> coherence budget) → **single-window recover** (real d3 patches first) → **CF-WR / seam** (principled
> composition — G0/G1/**G-graph** — against exact 12q truth, gated on the coherence-survival measurement)
> → **ADR 0008** (carrier) → **Plan 3** = the characterization that ties them into one defensible,
> unscoopable contribution: *the small-window coherent twin and its composition limit.*

---

## 7. Immediate execution order (build order, on the real XZZX d7 covering)

All on GPU; all theory-first pre-registered (predictions written before each run); both outcomes publish.
Detail: `docs/whitebox/window_covering_architecture.md`.

**0. `ξ̂` gate — DONE (BANKED GO).** Real surface d3→d7 controlled (§0.5, §3); build cleared.

**1. Covering schedule (step-1, `outputs/`, non-mainline).** Build the covering from the **parsed circuit /
DEM**, not geometry (correction 1): circuit roles (data/measure/ancilla) from the `M`/sweep-CX
instructions; stabilizer supports from the CZ gates; share-a-stabilizer adjacency → 3×3 windows; multi-body
completeness (connected weight-≤3 ⊆ windows); window-membership cross-check vs the nine shipped d3 patches;
full-in/seam/external stabilizer classification; multi-body DEM lightcone = the measured long-range budget
(a gate input, not a band); mechanism slot inventory (1q/2q/3q candidate placements = the overcomplete
dictionary dimension feeding step-3 Fisher). Theory-first predictions registered before the run.

**2. `WindowChannel` (step-2, MAINLINE — requires full user confirmation before commit).** The overcomplete
coherent non-Pauli / non-Clifford mechanism dictionary (torch port of `forward/channels.py` builders),
arity-general composition/embedding (1q/2q/3q slots; true-3q deferred-but-ready), `ρ_BC` extraction, the PTM
coherence-budget output (§0.5.5), CPTP self-checks. Suggested placement: `forward/mechanisms_torch.py` +
`forward/window_channel.py`.

**3. Single-window recover (step-3).** Rung 3a: fit the dictionary on the nine real d3 patches (full
observation) → held-out syndrome NLL sufficiency + Fisher identifiability + per-mechanism alias band
(two-gap, correction 4); mechanism *separation* validated only on a controlled teacher. Rung 3b: d7-interior
windows via seam-coupled estimation. Measure the coherence budget (PTM off-diagonal) → feeds the
seam-confirmation gate (§0.5.6).

**4. Composition / seam (step-4, gated).** White-box Petz / `ρ_BC` anchor (G1) + black-box GNN (G-graph),
bounded by the covering, calibrated against CF-WR exact truth; built only if the coherence-survival
measurement justifies a white-box seam certificate (§0.5.6). Long-range (disconnected) correlations = the
GNN's measured budget from step-1.

The CF-WR controlled lane (G0/G1/G-graph on the 12q exact toy) and the carrier study (ADR 0008, §0.5.7)
proceed in parallel as the validation harness, not the live front.

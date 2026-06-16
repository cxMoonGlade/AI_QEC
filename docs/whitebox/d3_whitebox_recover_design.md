# d3 white-box recover — design + pre-registration

> **Status: DESIGN DRAFT v5 (theory-first, 2026-06-15). Not built; no results.** v5 re-threads the
> objective from the unconditional stationary state `ρ_ss(θ)` to the **syndrome-conditioned multi-round
> detector-record likelihood on real device data** `detection_events.b8` (§2.0) — the v4 `ρ_ss(θ)` object
> is **degenerate for the unital SI1000 prior** (`ρ_ss = I/16` exactly, θ-independent ⇒ `rank(H)=1`;
> GPU-reproduced + independently reviewed, now the negative control). v4 re-threaded from a 3×3 (9-data)
> single-window white-box to a 2×2 (4-data) faithful window + black-box composition from d3 (the
> 9-data+ancilla register is infeasible on 32 GB — §0). v2 integrated an adversarial-review pass — see
> the changelog. The doc states the object, the forward, the recover objective, the identifiability +
> coherence metrics, the validation, and the pre-registered predictions **before any code runs**.
> Mainline code lands only through the commit-gate after the registered checks pass.
>
> **The d3 forward** is the **syndrome-conditioned multi-round detector-record likelihood** on the 6q
> 2×2 window (4 data + 2 full-in ancilla = 6q at d3; ≤6q across all scales, never 8q — measured,
> `outputs/covering_2x2.py`): from the real reset boundary, propagate the `R = 90` rounds with the
> **recorded** ancilla outcomes (per round: noisy gates → project ancilla on the record → renormalize →
> reset), accumulating `log P_θ(record)` — fit by a **composite (per-2×2-window) likelihood** over the
> 2×2 covering, on the **real non-unital device data** `detection_events.b8`. (The unconditional
> syndrome-AVERAGED stationary state `ρ_ss(θ)` is retired as the input — it is the unital-SI1000
> negative control, §2.0.)
> Earlier forward attempts were retired — the 9q per-stabilizer instrument, and the deterministic
> Clifford-frame MPDO carrier (Spike A,
> [`stabilizer_tn_carrier_design.md`](stabilizer_tn_carrier_design.md) §5.2); the tensor-network
> carrier is now a deferred **d5/d7 scaling** study, not the d3 forward.
>
> Scope tags: **(a)** exact (theorem/identity/zero-tolerance — only class usable as a premise);
> **(b)** prediction band (falsifiable; a miss is a finding, never later citable as fact);
> **(c)** heuristic gate/decision rule. Companions: [`README.md`](README.md),
> [`window_covering_RESULTS.md`](window_covering_RESULTS.md) (step-1 facts),
> [`stabilizer_tn_carrier_design.md`](stabilizer_tn_carrier_design.md) (Spike A + the trajectory
> carrier), [`../papers/reading_notes/darmawan_decoder_adaptation_local_noise_2403.08706.md`](../papers/reading_notes/darmawan_decoder_adaptation_local_noise_2403.08706.md)
> (digest-tier) + [`../papers/reading_notes/harper_nonclifford_crosstalk_surface_2605.29514.md`](../papers/reading_notes/harper_nonclifford_crosstalk_surface_2605.29514.md).

## 0. Scope — the white-box half of the grey-box, a small faithful 2×2 window at all distances

**The product is a GREY-BOX** = a **white-box** within-window CPTP channel field (physically
parameterised, interpretable, coherence-preserving, banded) **+** a **black-box** GNN fusion-merger
for the cross-window / long-range structure (calibrated, banded).

- **White-box scope = a small faithful 2×2 window — 4 data + its full-in stabilizer(s) — at ALL
  distances.** The ancilla is **carried through the entangled CZ phase** (faithful, not traced out
  before measurement). The measured register is **4 data + 2 full-in ancilla = 6q at d3** (≤6q across
  all scales, never 8q — measured, `outputs/covering_2x2.py`), trivially feasible on the dense oracle.
  This is the white-box unit at d3, d5, and d7 alike — distance never enlarges the white-box.
- **Black-box scope = the scalable composer, ACTIVE FROM d3.** The black-box (GNN) composes the
  overlapping 2×2 windows **via cross-window data-consistency over shared data (overlap ≤4) + the
  long-range/cross-window correlations (residual budget)**; **no seam-only stabilizers exist at the
  2×2 scale** — every stabilizer is full-in ≥1 window (d3 8/8, d5 24/24, d7 48/48; (a)-exact,
  `outputs/covering_2x2.py`). It engages **from d3** (was deferred to d7): even at d3 the code is
  covered by multiple overlapping 2×2 windows, and composing them via cross-window data-consistency
  over shared data is the black-box's job. Distance grows through the black-box, not the white-box.

**The simple reason to KEEP the ancilla in the window — the only rationale retained:** the
syndrome-extraction ancilla **cannot be eliminated**. The noise lives on the data⊗ancilla **entangled
state before measurement**, so a data-only effective field would lose the physics (it becomes a toy).
But carrying the ancilla makes the full d3 round 9 data + 8 ancilla = 13–17 q, **too big for the 32 GB
GPU** — **15q is measured-infeasible: the 2-matrix memory wall** (one 17 GB density matrix plus the
apply's second copy exceeds 32 GB). So the faithful white-box window is **2×2 (4 data + 2 full-in
ancilla = 6q at d3; ≤6q all scales, never 8q — measured, `outputs/covering_2x2.py`; trivially
feasible)**, and the black-box composes the windows from d3.

- **This doc = the d3 step.** Goal: **maximise the recovery of the within-window ≤2q mechanism field
  and quantify its identifiability**, on real d3 syndrome data, in each faithful 2×2 window. **Recover-
  scoped** — no decode / `do()` claim (the M4 "coherence does not transfer to MWPM" finding is window-
  local and would bite a d3 decode claim). **Long-range bunching is explicitly OUT OF SCOPE for the
  white-box** (it is provably outside any single-window model — §2.3 — and is the black-box's job,
  active from d3).

## 1. Object

A **field of ≤2q coherent-capable CPTP mechanisms** on the **2×2 window's 4 data qubits** — the
overcomplete dictionary (1q + 2q; 3q ready-but-off) of `docs/error_mechanisms.md`, each a
θ-parameterised Kraus/Stinespring channel
([`mechanisms_torch.py`](../../src/qec_twin/forward/mechanisms_torch.py)), **coherence-preserving by
construction (never twirled to Pauli)**. Fit to the window's own data (D2).

**Output form — black-box-ready** (the black-box is active from d3): per 2×2 window, (i) the recovered
θ field as a per-window CPTP channel object; (ii) its reduced marginals / `ρ_BC` overlap interface
(`WindowChannel.rho_bc` already exists — real, not vaporware; the cross-window anchor the black-box
composes on); (iii) the identifiability ledger (§4).

## 2. Forward — the syndrome-conditioned multi-round detector-record likelihood on real device data, fit by a composite likelihood

### 2.0 The objective is the syndrome-conditioned multi-round detector-record likelihood (the root — everything rests on this)

Real syndrome data is a **multi-round detector record**: each shot is the sequence of recorded ancilla
outcomes over `R = 90` rounds. The recover objective is the **likelihood of that recorded trajectory**,
`P_θ(record)` — the field-standard QEC calibration object (the dMLE / detector-correlation / `p_ij`
lineage; the M3 held-out syndrome-NLL; the object AlphaQubit and dMLE both score on), evaluated on the
**real device data** `detection_events.b8`. It is **not** the syndrome-AVERAGED, record-discarded
single-round channel.

**Why conditioned-and-multi-round, and why on the REAL (non-unital) data — the v4 root was degenerate
(GPU-reproduced + independently reviewed negative control).** v4 made the input the unconditional
**stationary state of the syndrome-AVERAGED round** `ρ_ss(θ) = fixed point of N_θ`, `N_θ(ρ) = Σ_s E_s(ρ)`.
That object is **degenerate, and the degeneracy is now an (a)-exact result**: for the **unital SI1000
prior**, every placed mechanism (rz, rzz, depol2, pauli_x) is unital, the ideal Cliffords are unital, and
ancilla reset-measure-trace composes to a unital data map, so **`N_θ(I/16) = I/16` for all θ ⇒
`ρ_ss = I/16` exactly and θ-independent** (`‖ρ_ss − I/16‖₁ = 7e-15`, stable under θ+=0.3; the fixed point
is *unique* — two seeds converge; `outputs/w2x2_window_rho_ss.py`). Then `dρ_ss/dθ = 0`, the syndrome
marginal is uniform, and the composite Fisher **collapses to `rank(H) = 1/28`** (a 12-order eigenvalue
gap; the lone surviving direction is the symmetric rzz on the weight-2 stabilizer's two CZ legs —
`outputs/w2x2_forward_fisher.py`).

This is a **unitality** problem, **not merely an averaging one** — and the distinction is load-bearing:
**conditioning alone does not rescue it** (a *single-round conditioned* forward at the physical input is
also rank-1 under unital noise). The information is restored by **two** ingredients, both absent from the
unconditional-stationary SI1000 object:
- **(a) Non-unitality of the real device channel.** Device noise (T1 / amplitude damping + leakage) is
  **non-unital**; the SI1000 `.stim` ships only `DEPOLARIZE1/2 + X_ERROR` (all unital) — it is a unital
  *simulation*, not the device. Non-unital noise pulls the fixed point off `I/16` (`dρ_ss/dθ ≠ 0`,
  non-uniform marginal — an amp_damp probe lifts `rank 1 → 2`). So the fit runs on `detection_events.b8`;
  the unital SI1000 collapse stays as a **negative control with teeth**.
- **(b) Genuine multi-round temporal structure.** The detector record carries the across-round
  transition/correlation structure (the `p_ij` are detector–detector correlations *across* rounds —
  Spitz 1712.02360) that a single-round marginal cannot.

**The coherent slot — the white-box's whole differentiation — is identifiable only here.** Coherent
rotations (RZZ/RXX) are **unital** ⇒ invisible to *any* stationary state (`I/16` regardless of θ). They
leave identifiable signatures only in the **multi-round conditioned record** (coherent error accumulates
across rounds — the standard short-time k-order lineage: Ivashkov 2603.05492, coherent 2nd-order vs
dissipator 1st-order). So the conditioned multi-round record is not a refinement of the v4 object — it is
the **only** object in which the white-box's coherent content is identifiable at all.

**The forward — the load-bearing cost, pre-registered.** `P_θ(record)` is computed by **R sequential
record-conditioned collapses** from the real reset boundary `|+⟩⁴_data ⊗ |0⟩²_anc` (X-basis; `|0⟩⁴` for
Z): per round, noisy gates → **project** the ancilla onto its recorded outcome → renormalize by
`Tr[P_{σ_t} ρ_t]` → reset ancilla, accumulating `log P_θ(record) = Σ_t log Tr[P_{σ_t} ρ_t]` in the **log
domain** (the per-round renormalization makes the likelihood a product over rounds; log-accumulate to
control vanishing/exploding gradients across 90 rounds). This is **materially more expensive than the
retired power iteration** — R=90 sequential differentiable 6q collapses per shot — and is pre-registered
as such (§8). **Boundary rounds are distinct:** the first (prep) and last (final data-readout) rounds are
*not* the bulk round and are modeled separately (a single time-homogeneous round misfits the boundary).
The `p = 0.005` readout flip is in the per-round record model.

**Scope discipline (provisional-conclusion rule).** `rank(H) = 1/28` is a **(b)-measurement on the
unital SI1000 prior**, never a theorem that the stationary objective is universally bad or that the
conditioned forward is universally superior — it is the unital *teacher* that is degenerate. On real
non-unital data the conditioned multi-round record is the non-degenerate, field-standard objective; that
superiority is itself to be measured (§8), not assumed.

**Dependency — the load-bearing consequence.** This conditioned multi-round likelihood is the **common
prerequisite** for every §11 certificate: held-out NLL, Fisher/Godambe identifiability (`rank(H)` depends
on the conditioned forward **and** the nominal θ — §4), and the coherence budget are all computed on
`P_θ(record)`. **Until it is built + the rank-lift confirmed, the three certificates are empty shells.**
Its build + the unital-negative-control / non-unital-and-multi-round-lift confirmation is the first build
step (sub-component #0, §9) and is pre-registered in §8.

### 2.1 The forward is UNBUILT and is the core component (not "reuse")

The full d3 round is 9 data + 8 ancilla = **13–17 q** — too big for the 32 GB GPU (**15q is
measured-infeasible: the 2-matrix memory wall, one 17 GB density matrix plus the apply's second copy >
32 GB**; §0). So the faithful window is the **2×2 (4 data + 2 full-in ancilla = 6q at d3; ≤6q all
scales, never 8q — measured, `outputs/covering_2x2.py`)**, trivially feasible on the dense oracle.
**The object we need — an exact, differentiable syndrome likelihood `P_θ(σ)` on the 6q 2×2 window
(d3) — exists in NO current module** and is the hardest thing to build (review BLOCKER 1):
- `calibration/hardware_nll.py` (the "M3 machinery") is **hardwired to the 1D repetition code**
  (`WINDOW_DISTANCE = 5`, `measure_parity_enumerate` = data-register Z-parity, **no ancilla**, a
  rep-code detector convolution). It is a **structural template only — not reusable code** for a
  weight-4 mixed XZZX stabilizer (ancilla + 4-CZ chain + interleaved `Y/H/X`).
- `forward/window_channel.py` `apply()` measures via `_measure_dephase_kraus` — a **non-selective,
  record-discarded CPTP map**; it has **no syndrome distribution at all** (its docstring defers the
  per-shot projector to "step-3").

**Construction (the build) — two layers.** **(i) The single-round projector core** evolves the 2×2
window — 4 data + 2 ancilla reset to |0⟩ — through one faithful round on the dense oracle to the
pre-measure state (the Spike-A `peak_state` path), then **enumerates the ancilla measurement(s) as
computational-basis projectors + reset, in faithful circuit order** (`circuit_sim.project_qubit` /
`measure_qubit_enumerate`), giving the Born outcome probabilities over the window syndromes. This core
**already exists and is verified** (A == B, TV `< 1e-10`; §7 (a)) — it is the per-round building block.
**(ii) The genuinely NEW build is the R-round record-conditioned chain** (§2.0): from the real reset
boundary, run `R = 90` rounds where each round **conditions** on the *recorded* ancilla outcome (project
→ renormalize by `Tr[P_{σ_t} ρ_t]` → reset), accumulating `log P_θ(record)` in the log domain, with the
**boundary rounds (prep / final readout) modeled distinctly** from the bulk and the `p = 0.005` readout
flip in the per-round model. The inter-round reset is what makes rounds non-independent, so this chain is
**not** a product of single-round marginals — it is the new object. Differentiable in θ by autograd
(complex128, GPU). This is **sub-component #0/#2 of the build (§9) — the core, not glue.**

**The verified single-round CORE (re-pointed to the 2×2 window).** The A-vs-B agreement is already
established — two independent constructions of the window's single-round Born map agree to machine
precision (**A == B, TV `< 1e-10`**, the §7 (a) gate + regression pin). At 6q (d3; ≤6q all scales —
measured, `outputs/covering_2x2.py`) this core runs directly on the dense oracle. It is the per-round
building block; the R-round record-conditioned chain (§2.0) that calls it `R = 90` times — with the
inter-round reset/renormalization — is the new, unbuilt object, and is where the cost and the
gradient-stability work live.

### 2.2 The composite (per-2×2-window) likelihood + the deterministic fit

Cover the code by a set of **overlapping 2×2 windows** `{W_j}`, `W_j` = (4 data + `T_j` = its full-in
stabilizer(s), ≤9 q), where **every ≤2q mechanism's footprint is co-covered by ≥1 window** (a covering
*design* constraint — §10). The recover objective is the composite log-likelihood

  `ℓ(θ) = Σ_j log P_θ(σ_{T_j})`   over held-out shots,   **with equal weights `w_j ≡ 1`**

(the standard all-windows composite likelihood — a consistent M-estimator; overlap is absorbed into the
Godambe variability matrix §4, not into ad-hoc weights — review MINOR 4).

**Why deterministic for the FIT, trajectory for VALIDATION (the clean division).** The composite gives
an **exact, autograd, zero-variance** `∂ℓ/∂θ` (once the §2.1 forward is built — these gradient/Fisher
exactness claims are **(b)-predictions about the unbuilt forward, gated behind sub-component #2, not
(a)-facts about existing code** — review MINOR 5). A pure-state trajectory would give a sampling
gradient — clean (pathwise) for coherent θ but high-variance (score-function) for the non-unital
`p = sigmoid(θ)` strengths — so it is the wrong tool for the *fit*. But the trajectory **is** the right
tool for *validation* (§7): a forward-only trajectory of the **recovered** model (no gradient ⇒
sampling variance is harmless) reproduces the full within-window joint, including the within-window R̂.

### 2.3 What the composite captures, and what it provably does not (review MAJOR 2, settled)

- **Captures: within-2×2 (full-in-stabilizer) correlation** — each `P_θ(σ_{T_j})` is the exact *joint*
  of its window stabilizer(s), so ≤2q correlated/coherent mechanisms whose footprint sits inside one
  2×2 window are seen.
- **Does NOT capture: cross-2×2 / long-range joint correlation.** A product of exactly-fit per-window
  marginals has **R̂ = 1 across windows by construction**; a single 2×2 window bounds only its own
  footprint, not *multi-shot* over-dispersion spanning windows. So the **long-range bunching — the M4
  ~40 % differentiator — is structurally outside the composite, for the same reason it is outside the
  independent-edges DEM.** This is **settled (direction), not open** — and it is **by design the
  grey-box boundary**: cross-2×2 / long-range structure is the **black-box's** job, **active from d3**.
  The white-box owns the within-2×2 structure only.
- **The within-2×2 emergent R̂** (the over-dispersion of a window's stabilizer(s), produced by the
  recovered ≤2q mechanisms acting jointly) is *not* in the composite *forward*, but **is** a
  consequence of the recovered *model* — validated by the trajectory forward (§7). If the ≤2q
  dictionary cannot reproduce it, that is a reported finding (turn on 3q, or it is cross-window).

## 3. Recover objective + metrics (field-standard, via `docs/METRICS.md`)

**Metric audit done up front (2026-06-15, `METRICS.md` "d3 white-box recover metrics" section).** Per
the forced ladder: REUSED ledger rows — held-out syndrome NLL, KL/TV, Choi/trace distance,
Fisher-information rank, detection-event fraction, DEM p_ij (within-2×2 2-body), round-repeat
bunching ratio R̂ (⚠ rung-3, the within-window R̂ here); NEW rows — composite (per-2×2-window)
likelihood (Lindsay 1988; Varin-Reid-Firth 2011), composite-likelihood Godambe bands (Godambe 1960),
**coherence budget = Pauli-twirl distance `½‖J(E)−J(T(E))‖₁` + unitarity** (Wallman 2015; rung-2
field-standard, switched 2026-06-15 from the rung-3 off-diagonal-PTM-mass proxy — it reuses `D_Choi`).
Verification note: the A-vs-B cross-check reports **TV `½‖A−B‖₁`** (standard distribution distance) +
`max|A−B|` (L∞) as a strict machine-agreement diagnostic; distribution comparisons always use NLL/KL/TV.

Per 2×2 window over the covering, **shot-sliced** train / held-out / escrow (no sample layer ⇒ disjoint
shot ranges). Conventions carried.

1. **FIT:** held-out **composite syndrome NLL** (nats/shot/window, paired bootstrap, one-sided) — clean
   deterministic gradient.
2. **VALIDATE structure:** the recovered model reproduces the measured detection fraction, within-2×2
   2-/3-body cumulants, **and the within-window R̂** (the last via the trajectory forward §7).
3. **Identifiability** (§4) — the centerpiece.
4. **Coherence budget** (§5).

## 4. Identifiability — composite Fisher + Godambe bands (the goal = maximise recovery)

"Maximise within-window recovery" = **identify as many ≤2q mechanisms as the data allows, report the
aliased ones honestly.** The deterministic forward gives the **composite sensitivity (Godambe `H`)**

  `H(θ) = Σ_j Σ_σ P_θ(σ_{T_j}) [∂_θ log P_θ(σ_{T_j})][∂_θ log P_θ(σ_{T_j})]^T`,

exact by autograd — where `P_θ(σ_{T_j})` is the **conditioned multi-round detector-record** likelihood
(§2.0) on real data, so `H` is taken **at the nominal θ on `detection_events.b8`**, and `∂_θ` carries the
R-round propagation sensitivity (the across-round build-up the unconditional stationary state drops).
`rank(H)` = identified directions; `null(H)` = the **aliased class** (reported, never a false
attribution). `rank(H)` is therefore only defined once §2.0 is in — it depends on **both** the conditioned
multi-round forward and the nominal θ. On the **unital SI1000 prior** it collapses to `rank(H)=1` (the
§2.0 negative control); the real-data lift is the §8 prediction.

**A 2×2 window earns limited per-window rank — most identifiability now comes from the black-box.** A
2×2 window carries exactly 2 full-in ancilla (d3; ≤2 per window at all scales — (a)-exact,
`outputs/covering_2x2.py`), so the **per-window identifiability ceiling = 2 syndrome bits/window (d3)**
(open item #1 quantified). A **single window's `rank(H)` is low** and many mechanisms are aliased
within it (§10 item 1). Identifiability is recovered by the **black-box composing the OVERLAPPING 2×2
windows via cross-window data-consistency over shared data** (active from d3): a mechanism aliased
inside one window is constrained by its co-covering neighbours. So the per-window Godambe ledger is a
**conservative per-window floor**; the composed (cross-window) identifiability is where most of the
recovery is earned, and is the black-box's responsibility from d3 on.

**Two corrections from the review (MAJOR 3):**
- **Bands use the Godambe sandwich `G = H J⁻¹ H`, not `H⁻¹`** (a pseudo-likelihood loses efficiency;
  `H⁻¹` mis-sizes the bands). `J` (the inter-window variability matrix) is estimated by block-bootstrap;
  until `J` is in, alias **band widths are tagged (c)-heuristic**, the rank/null structure is the
  load-bearing read.
- **`rank(H_composite) ≤ rank(H_joint)`** (marginalising only collapses directions). So the composite
  **under-states** identifiability — a *conservative* sufficiency lower bound: a mechanism it calls
  "aliased" may be jointly identifiable. Report the ledger as conservative; the §7 trajectory
  cross-check on a feasible reduced case bounds the gap (an extrapolation at full d3, tagged as such).

## 5. Coherence budget = the Darmawan test (literature-grounded)

The model **always represents coherence** (Kraus/Stinespring, never twirl — red-line); its *value* at
d3 is expected **small**:
- **Darmawan (PRA 2025, digest-tier):** for **local** coherent noise a **Pauli-adapted decoder is
  near-optimal** (~5 % gap at θ=0.125π — *qualitative*, re-check the PDF before any citation; the
  hardware θ is far smaller still).
- **Harper (full-text):** coherent **crosstalk** raises LER — but that is the **correlated /
  cross-window** regime, not local within-window.
- **Our M4:** the Pauli-DEM's ~40 % decode penalty is from the **bunching / correlation**, not local
  coherence magnitude — reconciling with Darmawan's locality boundary.

**Prediction (b):** the recovered **within-window coherence budget — the standard Pauli-twirl distance
`½‖J(E) − J(T(E))‖₁`** (the Choi trace distance to the channel's Pauli-twirl `T(E)` = the coherence a
Pauli/DEM export discards; reuses `D_Choi`), **plus the unitarity `u(E)`** (Wallman et al. 2015) — is
**small** (near-Pauli at hardware θ). Measure it: small ⇒ confirms the coherent value is cross-window
(the black-box's regime, active from d3); non-negligible ⇒ a finding. A measured (b) result, never a
premise; the papers are secondary/digest-tier evidence (framing only, never an (a)/(b) basis). (The
model itself is never twirled — the twirl is only this metric's reference channel.)

## 6. Baselines (pristine, recommended settings)

Run comprehensively at their own defaults, declaring version/commit + settings, never editing baseline
code: the shipped **SI1000 prior**; the **independent-edges Pauli-DEM** (the M4 baseline — beaten on
within-2×2 held-out NLL + out-structured on within-2×2 2-/3-body); **dMLE** (`external/baselines/
DMLE-QEC`, closest prior art). **NOT claimed by the white-box:** beating the Pauli-DEM on the
*long-range* bunching (that is the black-box, active from d3).

## 7. Validation

- **(a) per-2×2 exactness** — each `P_θ(σ_{T_j})` from the §2.1 forward matches an **independent
  brute-force** Born computation (zero shared code) to **total-variation distance `< 1e-10`** (with
  `max|·|` L∞ as a strict diagnostic), and sums to 1 (a build gate + regression pin).
- **(b) composite-vs-joint gap** — a **trajectory full-joint NLL** (a *different method* from the
  composite ⇒ a genuine ≥2-method cross-check on the load-bearing fit) vs the composite, on a feasible
  reduced case; report the θ gap as the composite's (b) band (an extrapolation at full d3 — tagged).
- **(b) within-window R̂** — the **recovered model**, run as a forward-only **trajectory**, reproduces
  the measured within-window over-dispersion within a band; a miss ⇒ the ≤2q dictionary is insufficient
  (3q / cross-window) — a finding, not a silent gap.
- **(b) structure-residual** — detection + within-2×2 2-/3-body cumulants reproduced.
- **Positive controls (teeth):** a **twirled** model fails the coherence-budget + structure checks; a
  **single-window (under-covering)** fit shows a rank-deficient `H` the full covering repairs; a
  **mis-specified** mechanism set raises the held-out NLL. A check that cannot fail is dead.

## 8. Pre-registration — predictions BEFORE the runs (theory-first)

- **(a)** **The unital-SI1000 degeneracy (negative control, GPU-reproduced + reviewed).** For the unital
  SI1000 prior, `ρ_ss = I/16` exactly and θ-independent (`‖ρ_ss − I/16‖₁ = 7e-15`, stable under θ+=0.3)
  ⇒ `dρ_ss/dθ = 0` ⇒ the unconditional-stationary composite Fisher collapses to **`rank(H) = 1/28`**
  (`outputs/w2x2_window_rho_ss.py` / `w2x2_forward_fisher.py`). Every placed SI1000 mechanism is unital
  (defect ≤ 9e-16) — the (a)-exact reason.
- **(a)** **Conditioning alone is insufficient under unital noise:** a *single-round conditioned* forward
  at the physical input is also `rank(H) = 1` (the lift is not from conditioning per se).
- **(b)** **The lift (the prediction to test).** On real non-unital `detection_events.b8`, the
  **conditioned multi-round** detector-record Fisher has `rank(H) > 1`, with the lift attributable to
  **(a)** non-unitality (an amp_damp teacher moves `ρ_ss` off `I/16` and lifts `rank 1 → 2`) **and**
  **(b)** multi-round temporal structure (R rounds vs one). Cross-checked by **two methods** (autograd vs
  finite-difference); the **unital-stationary case = negative control**, the **non-unital multi-round
  case = positive control**. Exact rank numbers (b).
- **(a)** §2.1 forward exact per 2×2 window (**TV `< 1e-10`** vs the independent brute-force; `P_θ(σ)` sums to 1).
- **(b)** `H` identifies the dominant ≤2q mechanisms; a **predicted aliased subset** (named before the
  run from the observation structure); reported **conservatively** (composite under-states; per-window
  rank is limited — §4 — so the predicted aliased subset is large and the black-box composition closes most of it).
- **(b)** within-window **Pauli-twirl distance + unitarity small** (Darmawan; below a pre-registered
  threshold); non-negligible ⇒ finding.
- **(b)** the white-box **beats the independent-edges Pauli-DEM on within-2×2 held-out NLL** and
  **reproduces the within-window structure incl. R̂** (via the trajectory validation). **The
  long-range bunching is NOT claimed by the white-box** (out of scope; the black-box, active from d3).
- **(c)** gates: adopt the recovered field per 2×2 window iff the (a) check passes, the
  structure-residual (incl. within-window R̂) closes within band, and the conservative `H` ledger is reported.

## 9. Build plan (heavy → ≥3 agents + realtime reviewer + per-window GPU verification)

**Per distance:** d3 = the 2×2 white-box (per-window faithful recover, 6q (d3; ≤6q all scales,
never 8q — measured, `outputs/covering_2x2.py`), the conditioned multi-round detector-record forward +
Fisher) **+ the black-box composition (active from d3)**; **d5/d7 = the same**
(2×2 white-box + black-box), with distance scaling carried by the **black-box**, never by enlarging the
white-box. The 13q/15q sub-components are dropped (infeasible — §0).

Decomposed into small independently-verifiable sub-components; each built by an agent with a realtime
reviewer auditing on landing; the **orchestrator verifies each piece against an independent oracle on
GPU before the next** — incremental review+verify, never one solo dump. **Sub-component #2 is the core
new build, NOT glue.**

| # | Sub-component | Independent verification before proceeding |
|---|---|---|
| 0 | **conditioned multi-round detector-record likelihood (ROOT, §2.0)** — R-round record-conditioned forward on the 6q 2×2 window (project→renormalize→reset per round, log-domain accumulation, boundary rounds distinct), on real `detection_events.b8`; differentiable in θ | the unital-SI1000 **negative control reproduces `rank(H)=1`**; the real-data conditioned **multi-round** Fisher lifts `rank(H)>1` (non-unitality + multi-round); autograd-vs-finite-diff |
| 1 | **2×2 covering** — real d3 code → overlapping 2×2 (4-data + 2 full-in ancilla = 6q at d3; ≤6q all scales, never 8q — measured, `outputs/covering_2x2.py`) windows co-covering every mechanism footprint; **no seam-only stabilizers — every stabilizer is full-in ≥1 window (d3 8/8, d5 24/24, d7 48/48, (a)-exact)** (**footprint-feasibility here; Fisher-optimal only after #0 + #4**) | counts vs `window_covering_RESULTS`; every mechanism ∈ ≥1 window; full-in check passes |
| 2 | **single-round projector core** — evolve to pre-measure (Spike-A `peak_state`) + ancilla-projector enumeration + reset (faithful order) → the per-round window Born map (the building block the #0 R-round chain calls) | vs an **independent brute-force** Born computation `< 1e-10` (the A==B core, re-pointed); `Σ_σ P = 1`; finite-difference grad |
| 3 | **composite ℓ(θ) + deterministic fit** — `w_j≡1`; GPU LBFGS/Adam | gradient finite-diff; convergence on a controlled teacher |
| 4 | **Godambe Fisher + identifiability** — `H`, block-bootstrap `J`, sandwich bands; rank/null ledger (per-window rank limited — most identifiability from #7) | rank on a controlled teacher (known identifiable/aliased) |
| 5 | **trajectory validation forward** — forward-only (no grad) of the recovered model → within-window R̂ + the composite-vs-joint cross-check | within-window R̂ on a teacher; ≥2-method agreement |
| 6 | **metrics + baselines + controls** — NLL, structure-residual, coherence budget; SI1000/Pauli-DEM/dMLE; the §7 positive controls | the positive controls fail loudly |
| 7 | **black-box composition (from d3, §10 item 2)** — GNN composing the overlapping 2×2 windows via cross-window data-consistency over shared data (overlap ≤4) + the long-range/cross-window correlations (residual budget); **no seam-only stabilizers** (all full-in, (a)-exact); the cross-window identifiability + long-range residual. **To be specified/built** (engages at d3, was deferred to d7) | composed identifiability ≥ per-window floor (> 2 syndrome bits/window); cross-window R̂ on a teacher |

**Mainline commit-gate:** recover code under `src/qec_twin/` lands only after the (a) check passes +
the structure-residual closes + **full user confirmation**. GPU-only (cuda/complex128, env activated
so the fused kernel loads); scripted-execution (committed `outputs/` scripts, asserts, printed
evidence, flush, `__main__` guard); theory-first (predictions before every run); metric + rigor audit
at close.

## 10. Open items (settle in the build, honestly)

1. **Per-2×2 identifiability + the tunable window size.** A 2×2 window carries exactly 2 full-in ancilla
   (d3; measured, `outputs/covering_2x2.py`) ⇒ **per-window identifiability ceiling = 2 syndrome
   bits/window (d3)** ⇒ **low per-window `rank(H)`** ⇒ much of the identifiability must come from the
   **black-box composing OVERLAPPING 2×2 windows via cross-window data-consistency over shared data**
   (§4). To settle: measure the per-2×2 `rank(H)` (after #0 + #4) and quantify **how much
   identifiability is left to the black-box**. The **window size is tunable** — 2×2 vs the **largest
   faithful window that still fits 32 GB** (e.g. 2×3 ≈ 9q) — chosen by **feasibility + Fisher rank**
   (a bigger faithful window raises per-window rank but costs register size; pick the sweet spot under
   the memory wall, §0). This is the experiment-design (probe-richness) lever, gated by §2.0 (`rank(H)`
   needs the conditioned multi-round forward + the nominal θ on real data).
2. **Black-box-at-d3 spec.** The black-box (GNN composition) now **engages at d3** (was deferred to d7):
   it composes the overlapping 2×2 windows **via cross-window data-consistency over shared data (overlap
   ≤4) + the long-range/cross-window correlations (residual budget)**; there are **no seam-only
   stabilizers at the 2×2 scale** (every stabilizer is full-in ≥1 window — d3 8/8, d5 24/24, d7 48/48;
   (a)-exact, `outputs/covering_2x2.py`). It earns the cross-window identifiability and models the
   long-range residual the white-box provably cannot close (§2.3, §11.4). **To be specified and built**
   (sub-component #7, §9) — the d3 white-box states exactly what it hands over (§11.4); the composition
   architecture (cross-window data-consistency over shared data + residual budget) is the open spec.
3. **The composite-vs-joint gap** — the trajectory cross-check (§7) bounds it on a reduced case;
   extrapolation at full d3 is flagged.
4. **Does the ≤2q dictionary reproduce the within-window R̂?** — validated by the trajectory; a miss
   ⇒ 3q-on / cross-window finding (correction 4: model-class gap reported, not hidden).
5. **Multi-round objective — SETTLED (§2.0, re-settled v5).** Picked: the **syndrome-conditioned
   multi-round detector-record** likelihood on real `detection_events.b8` (R-round record-conditioned
   propagation from the reset boundary, differentiable, log-domain), **replacing** the v4
   unconditional-stationary `ρ_ss(θ)` (degenerate for the unital SI1000 prior — `ρ_ss=I/16`, `rank(H)=1`;
   now the negative control). The `p = 0.005` readout flip is in the per-round model; boundary rounds are
   modeled distinctly. Remaining = the **build + the rank-lift confirmation** (sub-component #0, §9;
   pre-registered §8) — the run, not the choice.

## 11. White-box performance certification + the black-box interface (under the standard metrics)

How the §3 standard metrics **certify the white-box's performance** and **hand calibrated information to
the black-box (active from d3)** — the two deliverables the grey-box needs from the d3 step.

### 11.1 What "white-box performance" is on real data (no truth ⇒ certify, don't claim recovery)

Real d3 data has **no ground-truth channel** (correction 4: mechanism *separation* is scored only on a
controlled teacher, never claimed from real data). So "performance" is **three standard certificates**,
not a recovery-vs-truth error:

**Prerequisite (the root, §2.0): the three certificates all presuppose the correct objective — the
syndrome-conditioned multi-round detector-record likelihood on real data.** Held-out NLL, Fisher/Godambe,
and the coherence budget are each computed on `P_θ(record)`; on the wrong objective — the unconditional
syndrome-averaged stationary state, degenerate for the unital prior (`rank(H)=1`) — they are empty shells.
So §2.0 (built + the rank-lift confirmed as sub-component #0) gates everything below.

1. **Observational adequacy** — the held-out **composite syndrome NLL** beats the baselines (SI1000
   prior, independent-edges Pauli-DEM, dMLE) on identical held-out shots (paired bootstrap, one-sided),
   AND the **structure-residual** (detection fraction; within-2×2 2-body p_ij; 3-body cumulant) closes
   within a band ⇒ an observationally-better, structurally-faithful within-window generative model.
2. **Identifiability** — the **composite Fisher `H` + Godambe-band** ledger: the **identified subset**
   (`rank(H)`, tight band) ∪ the **aliased class** (`null(H)`, reported). **Performance is guaranteed
   ONLY for the identified subset** — the Fisher/Godambe IS the performance bound (which mechanisms, how
   tight); aliased ones are reported, never claimed.
3. **Coherence** — the **Pauli-twirl distance + unitarity** per window: the coherent content carried
   (band-tracked), the technical differentiation from the Pauli-DEM.

Honest guarantee: *observationally-better + structurally-faithful + identified-subset-with-bands +
coherence-preserved* — never "recovered the true mechanisms."

### 11.2 Method validation on a controlled teacher (the only truth leg)

Before trusting the recover on real data, validate the METHOD on a **synthetic d3 teacher** (a known
≤2q mechanism field): generate syndromes, recover, and check under the standard metrics —
- recovery error `|θ̂ − θ_true|` lies within the **Godambe band** (band **coverage** = the ledgered
  `prediction.drift.coverage_frequency`);
- the **Fisher-predicted identified set** matches the teacher's identifiable directions (the aliased
  ones are genuinely unrecoverable, not a fit failure);
- the composite **NLL → 0** on the 2×2 windows (the recovered model matches the teacher's joint).

This certifies the fit is **unbiased**, the **bands are honest** (coverage), and the **Fisher is
correct** — the guarantee real data cannot give. Mechanism *separation* is scored ONLY here.

### 11.3 Maximising the certified performance (the design levers)

Performance is *maximised*, not assumed, by the **experiment-design** choices scored by the same
metrics — but in a **strict order gated by §2.0**, because `rank(H)` depends on the conditioned
multi-round forward and the nominal θ on real data:
- **Before §2.0 (no conditioned forward yet):** the **2×2 covering** (§2.2/§10 item 1) can only be chosen
  for **footprint feasibility** — every ≤2q mechanism footprint co-covered by ≥1 6q (d3; ≤6q all scales —
  measured, `outputs/covering_2x2.py`) 2×2 window. `rank(H)` is not yet computable, so a
  *Fisher-optimal* covering is impossible at this stage.
- **After §2.0 + §4 (the conditioned forward + composite `H` available):** the covering becomes **Fisher-optimal** —
  chosen to **maximise `rank(H)`** (the identified set) at the nominal θ; the **window size** is tuned
  here too (2×2 vs the largest faithful window under the 32 GB wall, §10 item 1); probe-richness (round
  structure / basis) chosen to shrink the Godambe bands and raise the NLL win.

This is the ADR-0005 probe-richness / alias-quotient discipline — more identified DOF + tighter bands =
more performance, *earned* (and only earnable once the conditioned multi-round forward is in). Note
per-window rank is limited (§4): the largest performance lever is the **black-box composing the
overlapping windows**, active from d3.

### 11.4 The white-box → black-box interface (calibrated, residual-annotated, coherence-preserving)

The white-box hands the black-box (the GNN fusion-merger, **active from d3**) FOUR things, all under the
standard metrics — this is what makes the grey-box **calibrated, complete, and coherence-preserving**:

1. **Per-window recovered CPTP channel `θ` + Godambe bands** — point + uncertainty per mechanism ⇒ the
   black-box **weights each window-channel by its band** (trusts tight-band mechanisms, down-weights
   wide-band/aliased ones): a *calibrated* fusion, not over-trusting the white-box.
2. **Overlap / seam marginals `ρ_BC`** — the reduced window-overlap states = the **cross-window
   consistency anchor** the merger composes on (plan3 §0.5.3); **consumed from d3** (the overlapping 2×2
   windows are stitched at d3), via the existing output FORM (`WindowChannel.rho_bc` exists).
3. **The residual = the black-box's explicit budget** — the structure the white-box **provably cannot
   close** (the **long-range bunching R̂** and **cross-2×2 correlations**, §2.3), quantified by the
   **un-closed structure-residual + the long-range R̂**. This is the GNN's modelling target (plan3 §7's
   long-range/GNN budget): the white-box states exactly *what is left for the black-box*, so coverage is
   complete and honest.
4. **The coherence budget (Pauli-twirl distance) per window** — so the black-box's fusion **preserves
   coherence** (never twirls); the coherent content the white-box carries is passed through.

**The grey-box guarantee, assembled:** the black-box trusts the white-box *by the band* (1), composes
*on the overlap anchor* (2), models *the residual the white-box flagged* (3), and *preserves coherence*
(4) ⇒ a full-code channel field calibrated end-to-end (white-box identified-subset + bands; black-box
residual + bands) — exactly the project-goal differentiation (calibrated DEM + bands + CPTP).

## Changelog

- **2026-06-15 v4 → v5 (objective re-thread: unconditional-stationary `ρ_ss(θ)` → conditioned
  multi-round detector-record likelihood on real data).** The v4 root §2.0 — the forward evaluated on the
  unconditional **stationary state of the syndrome-AVERAGED round** `ρ_ss(θ)` — was found **degenerate for
  the unital SI1000 prior**, GPU-reproduced and independently reviewed: every placed SI1000 mechanism is
  unital (defect ≤ 9e-16) ⇒ `N_θ(I/16)=I/16` ⇒ **`ρ_ss = I/16` exactly, θ-independent** (`‖·‖₁=7e-15`;
  unique fixed point) ⇒ `dρ_ss/dθ=0` ⇒ the composite Fisher **collapses to `rank(H)=1/28`**
  (`outputs/w2x2_window_rho_ss.py`, `w2x2_forward_fisher.py`). An independent adversarial reviewer
  confirmed the degeneracy **and corrected the fix reasoning**: it is a **unitality** problem, not an
  averaging one — *conditioning alone does not rescue it* (a single-round conditioned forward is also
  rank-1 under unital noise). The objective is therefore re-threaded to the **syndrome-conditioned
  multi-round detector-record likelihood** `P_θ(record)` on the **real non-unital device data**
  `detection_events.b8` (the field-standard dMLE / detector-correlation / `p_ij` / M3-NLL object), the lift
  coming from **(a) non-unitality** (moves `ρ_ss` off `I/16`; an amp_damp probe lifts `rank 1→2`) +
  **(b) genuine multi-round** temporal structure. Coherent mechanisms (RZZ/RXX — unital) are invisible to
  any stationary state and identifiable **only** in the conditioned multi-round record. The forward is now
  **R sequential record-conditioned collapses** (project→renormalize→reset per round, log-domain
  accumulation, boundary rounds prep/readout modeled distinctly) — materially more expensive than the
  retired power iteration, pre-registered (§8). Re-threaded the header, §2 title, §2.0, §2.1 (the
  single-round core exists/verified; the R-round chain is the new build), §4, §8 (the unital negative
  control + the non-unital/multi-round lift prediction), §9 (#0/#2), §10 item 5, §11.1, §11.3. The v4
  `ρ_ss(θ)` machinery is kept only as the **negative control with teeth**. **Scope:** `rank(H)=1/28` is a
  (b)-measurement on the unital SI1000 prior, never a premise that the conditioned forward is universally
  superior — that superiority is to be measured.
- **2026-06-15 v3 → v4 (3×3 → 2×2 pivot; black-box from d3).** Re-threaded the white-box from a 3×3
  (9-data) single-window unit to a **2×2 (4-data) faithful window + its full-in stabilizer(s)**, with
  the ancilla **carried** through the entangled CZ phase; measured register = **4 data + 2 full-in ancilla
  = 6q at d3 (≤6q all scales, never 8q — `outputs/covering_2x2.py`)**. **Why:** the syndrome ancilla
  is irreducible (the noise lives on the data⊗ancilla entangled state before measurement; a data-only
  field is a toy), but 9 data + ancilla = 13–17q is too big for 32 GB — **15q is measured-infeasible
  (the 2-matrix memory wall, one 17 GB density matrix + the apply's second copy > 32 GB)**. The
  **black-box (GNN) now engages from d3** (was deferred to d7): it composes the overlapping 2×2 windows
  **via cross-window data-consistency over shared data (overlap ≤4) + the long-range/cross-window
  correlations (residual budget)**; **no seam-only stabilizers exist at the 2×2 scale** (every
  stabilizer is full-in ≥1 window — d3 8/8, d5 24/24, d7 48/48; (a)-exact, `outputs/covering_2x2.py`);
  and earns most of the identifiability (per-2×2 identifiability ceiling = **2 syndrome bits/window
  (d3)** — (a)-exact). **`ρ_ss(θ)` is now the EXACT global stationary fixed point of the 2×2 round at
  6q (d3; ≤6q all scales).** **Deleted the 3×3-infeasibility machinery:** the per-block family
  `{ρ_ss^(j)}`, Form A/B/C, the 17q/15q streaming, the composite-round-of-blocks, and the input-state
  gap. **Kept:** the two ruled-out inputs (`|+⟩⁹` via `⟨XZZX⟩ = 0`; θ-independent `ρ_code` drops
  `dρ_ss/dθ`), the Fisher collapse/restore positive control, and the verified forward core (A == B,
  TV `< 1e-16`) — all re-pointed to the 2×2 window. Added §10 new open items: per-2×2 identifiability
  (ceiling 2 syndrome bits/window) + tunable window size (2×2 vs the largest faithful window ≈2×3 that
  fits 32 GB, by feasibility + Fisher rank), and the black-box-at-d3 spec (sub-component #7, §9).
- **2026-06-15 v2 → v3 (stationary-likelihood re-thread).** Promoted the **stationary multi-round
  likelihood `ρ_ss(θ)`** from an §10 open item (item 4) to the **foundational §2.0** — the root every §11
  certificate rests on. Ruled out both wrong inputs: the t=0 boundary `|+⟩⁹` (uniform syndrome,
  rank-deficient Fisher — `⟨XZZX⟩ = 0` exact) and the θ-independent ideal `ρ_code` (drops the accumulated
  coherent sensitivity `dρ_ss/dθ`). Settled §10 item 4 (stationary block-law on `ρ_ss(θ)`, power-iterated,
  differentiable); added the Fisher confirmation to §8 + **sub-component #0** to §9; threaded the
  `ρ_ss(θ)`-and-nominal-θ dependence into §4; split §11.3 covering into pre-`ρ_ss` footprint-feasibility
  vs post-`ρ_ss` Fisher-optimal; added the §11.1 stationary-likelihood prerequisite. Removed the retired
  9q-instrument 14.4 % citation from the header (the derivation file is deleted; the carrier doc holds
  the Spike A finding).
- **2026-06-15 v1 → v2 (adversarial review integrated).** **BLOCKER:** v1 mislabeled the forward as
  "reuse the M3 machinery + dense oracle"; in fact `hardware_nll.py` is rep-code-only and
  `WindowChannel` has no syndrome distribution — so the forward is a **new surface-block
  ancilla-projector Born likelihood** (§2.1), the core build, not glue. **MAJOR (settled):** the
  long-range bunching is **provably outside** any block-marginal composite (R̂=1 across exactly-fit
  marginals) — scoped to the **d7 black-box**; d3 owns within-window structure, with the within-window
  R̂ validated by a trajectory forward of the recovered model (§2.3, §7). **MAJOR:** identifiability
  bands use the **Godambe sandwich**, not `H⁻¹`, and `rank(H_composite) ≤ rank(H_joint)` ⇒ the alias
  ledger is **conservative** (§4). **MINOR:** `w_j ≡ 1` fixed (§2.2); the exact-gradient/Fisher claims
  gated behind the unbuilt forward as (b)-predictions (§2.2); Darmawan numbers kept qualitative (§5).

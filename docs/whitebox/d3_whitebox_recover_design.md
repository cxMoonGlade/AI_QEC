# d3 white-box recover — design + pre-registration

> **Status: DESIGN DRAFT v3 (theory-first, 2026-06-15). Not built; no results.** v3 re-threads the
> theory around the **stationary multi-round likelihood `ρ_ss(θ)`** (§2.0) as the root that every
> performance certificate rests on (v2 integrated an adversarial-review pass — see the changelog).
> States the object, the forward, the recover objective, the identifiability + coherence metrics, the
> validation, and the pre-registered predictions **before any code runs**. Mainline code lands only
> through the commit-gate after the registered checks pass.
>
> **The d3 forward** is a **surface-block ancilla-projector Born likelihood** evaluated on the dense
> oracle over the **stationary state `ρ_ss(θ)`** (§2.0), fit by a **composite (block-marginal)
> likelihood**. Earlier forward attempts were retired — the 9q per-stabilizer instrument, and the
> deterministic Clifford-frame MPDO carrier (Spike A,
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

## 0. Scope — the white-box half of the grey-box, fixed single-window

**The product is a GREY-BOX** = a **white-box** within-window CPTP channel field (physically
parameterised, interpretable, coherence-preserving, banded) **+** a **black-box** GNN fusion-merger
for the cross-window / long-range structure (calibrated, banded). Build order (user-set 2026-06-15):
**d3 white-box → d7 black-box → d5 validate.**

- **White-box scope = single window, FIXED** — not "extended" to d5/d7. A d7-interior window is the
  same 3×3 unit as a d3 patch (footprint verified equal); distance grows by adding the **black-box**,
  never by enlarging the white-box.
- **d3 = the cleanest single-window recover:** the nine standalone `d3_at_q*` patches are fully
  observed, 8 full-in stabilizers, **no seam**. (A d7-interior window has only ~4 full-in + ~8 seam
  ⇒ underdetermined ⇒ needs the seam = the black-box. `window_covering_RESULTS` finding 2.)
- **This doc = the d3 step.** Goal: **maximise the recovery of the within-window ≤2q mechanism field
  and quantify its identifiability**, on real d3 syndrome data. **Recover-scoped** — no decode /
  `do()` claim (the M4 "coherence does not transfer to MWPM" finding is window-local and would bite a
  d3 decode claim). **Long-range bunching is explicitly OUT OF SCOPE at d3** (it is provably outside
  any single-window model — §2.3 — and is the d7 black-box's job).

## 1. Object

A **field of ≤2q coherent-capable CPTP mechanisms** on the window's 9 data qubits — the overcomplete
dictionary (1q + 2q; 3q ready-but-off) of `docs/error_mechanisms.md`, each a θ-parameterised
Kraus/Stinespring channel ([`mechanisms_torch.py`](../../src/qec_twin/forward/mechanisms_torch.py)),
**coherence-preserving by construction (never twirled to Pauli)**. Fit to the patch's own data (D2).

**Output form — black-box-ready** (forward-looking; no seam at d3): per window, (i) the recovered θ
field as a per-window CPTP channel object; (ii) its reduced marginals / `ρ_BC` overlap interface
(`WindowChannel.rho_bc` already exists — real, not vaporware; unused at d3, consumed by the d7
black-box); (iii) the identifiability ledger (§4).

## 2. Forward — the stationary likelihood `ρ_ss(θ)`, a surface-block Born likelihood, fit by a composite likelihood

### 2.0 The objective is the stationary multi-round likelihood (the root — everything rests on this)

Real syndrome data is **multi-round** (`rounds = 90`): the data state entering an interior round is the
**stationary fixed point of the noisy round**, not a freshly-prepared state. The recover's likelihood is
therefore evaluated on the **θ-dependent stationary state**

  `ρ_ss(θ) = fixed point of N_θ`,  where `N_θ(ρ) = Σ_s E_s(ρ)` is the per-round **syndrome-averaged**
  data channel (one faithful round on ≤13q: ancilla reset → noisy gates → measurement instrument,
  ancilla traced out); **unique for `θ > 0`** (primitive `N_θ` — a §8 (b) prediction, not assumed).

so the composite likelihood (§2.2) is `P_θ(σ_{T_j} | ρ_ss(θ))` — a **bilevel / self-consistent**
objective (each θ-evaluation solves the fixed point inside).

**Why the stationary state is the root, not a detail — the two wrong inputs, ruled out:**
- **(a, exact) the t=0 boundary product `|+⟩⁹`** (the patch's X-basis prep) is **not** a codeword: a
  mixed XZZX stabilizer has `⟨X_a Z_b Z_c X_d⟩_{|+⟩⁹} = (+1)(0)(0)(+1) = 0` exactly (`⟨+|Z|+⟩ = 0`,
  product factorises) ⇒ the noiseless syndrome is uniform (50/50) ⇒ the Fisher information about θ is
  **rank-deficient** (most mechanisms unidentifiable). Feeding the steady round this boundary state is
  the mismatch (a steady round fed a t=0 boundary state) — and is exactly what the POC did.
- **the θ-independent ideal code state `ρ_code = Π_code / 2^k`** (`Π_code = ∏_i (I+S_i)/2`, all
  stabilizers +1 ⇒ silent baseline) is only `lim_{θ→0⁺} ρ_ss(θ)`, the θ→0 reference (at θ = 0 the noiseless round's fixed point is
  non-unique). Using it **drops the
  accumulated coherent sensitivity**: the total derivative
  `dP/dθ = ∂P/∂θ|_{ρ_ss} + (∂P/∂ρ)(dρ_ss/dθ)` loses its **second term** — exactly the **cross-round
  build-up of coherent error** the white-box exists to recover. (For pure stochastic-Pauli noise the
  term is negligible and `ρ_code` would suffice; for the coherent / non-unital CPTP that is the
  white-box's point, it is not optional.)

**Feasibility + differentiability.** `ρ_ss(θ)` is found by **power iteration** `ρ_{k+1} = N_θ(ρ_k)`
(each step one ≤13q round; the data state is `2^9`; the dense `N_θ` superoperator `2^18 × 2^18 ≈ 1.1 TB`
is **never formed**), and is **differentiable** in θ by implicit differentiation (or a few unrolled
steps). This is the **steady-state block-law** form of the multi-round objective (§10 item 4; vs the per-round
chain); the `p = 0.005` readout convolution is already in the forward. The syndrome-**conditioned**
(trajectory) variant is for §7 validation, not the composite fit.

**Dependency — the load-bearing consequence.** `ρ_ss(θ)` is the **common prerequisite** for every §11
certificate: held-out NLL, Fisher/Godambe identifiability (`rank(H)` depends on `ρ_ss(θ)` **and** the
nominal θ — §4), and the coherence budget are all computed on this likelihood. **Until the stationary
likelihood is defined + verified, the three certificates are empty shells.** Its confirmation is the
first build step (sub-component #0, §9) and is pre-registered in §8: the composite Fisher `rank(H)`
**collapses** at `|+⟩⁹` and is **restored** at `ρ_ss(θ)` (the positive control).

### 2.1 The forward is UNBUILT and is the core component (not "reuse")

The full d3 round is 9 data + 8 ancilla = **17 q** (`4^17 × 16 B ≈ 275 GB`, infeasible). The dense
oracle is exact at **≤13 q** (9 data + ≤4 ancilla). **The object we need — an exact, differentiable
syndrome likelihood `P_θ(σ)` on a ≤13q surface block — exists in NO current module** and is the
hardest thing to build (review BLOCKER 1):
- `calibration/hardware_nll.py` (the "M3 machinery") is **hardwired to the 1D repetition code**
  (`WINDOW_DISTANCE = 5`, `measure_parity_enumerate` = data-register Z-parity, **no ancilla**, a
  rep-code detector convolution). It is a **structural template only — not reusable code** for a
  weight-4 mixed XZZX stabilizer (ancilla + 4-CZ chain + interleaved `Y/H/X`).
- `forward/window_channel.py` `apply()` measures via `_measure_dephase_kraus` — a **non-selective,
  record-discarded CPTP map**; it has **no syndrome distribution at all** (its docstring defers the
  per-shot projector to "step-3").

**Construction (the build).** Evolve the block input — the data in the stationary state `ρ_ss(θ)`
(§2.0), the block ancilla reset to |0⟩ — through the faithful round on the dense oracle to the
pre-measure state (the Spike-A `peak_state` path is reusable here), then **enumerate the
block's ≤4 ancilla measurements as computational-basis projectors + reset, in faithful circuit order**
(reusing `circuit_sim.project_qubit` / `measure_qubit_enumerate` — the existing branch primitives),
recording the Born outcome probabilities ⇒ `P_θ(σ_{T_j})` over the `≤2^{|T_j|}` block syndromes per
round; then a **surface-specific multi-round detector / readout convolution** (the `p = 0.005`
readout flip; built new, the rep-code convolution is only a template). Differentiable in θ by autograd
(complex128, GPU). This is **sub-component #2 of the build (§9) — the core, not glue.**

### 2.2 The composite (block-marginal) likelihood + the deterministic fit

Cover the 8 stabilizers by a set of **blocks** `{B_j}`, `B_j` = (9 data + `T_j ⊆ stabilizers`,
`|T_j| ≤ 4`, ≤13 q), where **every ≤2q mechanism's footprint is co-covered by ≥1 block** (a covering
*design* constraint — §10.1; the detector-weight ceiling ≤4 bounds a single error's footprint but
does **not** by itself guarantee a single ≤4-stab block contains it — the covering must be chosen so).
The recover objective is the composite log-likelihood

  `ℓ(θ) = Σ_j log P_θ(σ_{T_j})`   over held-out shots,   **with equal weights `w_j ≡ 1`**

(the standard all-blocks composite likelihood — a consistent M-estimator; overlap is absorbed into the
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

- **Captures: within-block (≤4-stabilizer) correlation** — each `P_θ(σ_{T_j})` is the exact *joint* of
  its ≤4 stabilizers, so ≤2q correlated/coherent mechanisms with a ≤4-detector footprint are seen.
- **Does NOT capture: long-range (>4-stab / cross-window) joint correlation.** A product of
  exactly-fit block marginals has **R̂ = 1 across blocks by construction**; the detector-weight
  ceiling bounds *single-error* footprints, not *multi-shot* over-dispersion. So the **long-range
  bunching — the M4 ~40 % differentiator — is structurally outside the composite, for the same reason
  it is outside the independent-edges DEM.** This is **settled (direction), not open** — and it is
  **by design the grey-box boundary**: long-range bunching is the **d7 black-box's** job. The d3
  white-box owns the within-window structure only.
- **The within-window emergent R̂** (the aggregate over-dispersion of the 8 d3 stabilizers, produced
  by the recovered ≤2q mechanisms acting jointly) is *not* in the composite *forward*, but **is** a
  consequence of the recovered *model* — validated by the trajectory forward (§7). If the ≤2q
  dictionary cannot reproduce it, that is a reported finding (turn on 3q, or it is cross-window).

## 3. Recover objective + metrics (field-standard, via `docs/METRICS.md`)

**Metric audit done up front (2026-06-15, `METRICS.md` "d3 white-box recover metrics" section).** Per
the forced ladder: REUSED ledger rows — held-out syndrome NLL, KL/TV, Choi/trace distance,
Fisher-information rank, detection-event fraction, DEM p_ij (within-block 2-body), round-repeat
bunching ratio R̂ (⚠ rung-3, the within-window R̂ here); NEW rows — composite (block-marginal)
likelihood (Lindsay 1988; Varin-Reid-Firth 2011), composite-likelihood Godambe bands (Godambe 1960),
**coherence budget = Pauli-twirl distance `½‖J(E)−J(T(E))‖₁` + unitarity** (Wallman 2015; rung-2
field-standard, switched 2026-06-15 from the rung-3 off-diagonal-PTM-mass proxy — it reuses `D_Choi`).
Verification note: the A-vs-B cross-check reports **TV `½‖A−B‖₁`** (standard distribution distance) +
`max|A−B|` (L∞) as a strict machine-agreement diagnostic; distribution comparisons always use NLL/KL/TV.

Per patch (nine `d3_at_q*`), **shot-sliced** train / held-out / escrow (no sample layer ⇒ disjoint
shot ranges). Conventions carried.

1. **FIT:** held-out **composite syndrome NLL** (nats/shot/block, paired bootstrap, one-sided) — clean
   deterministic gradient.
2. **VALIDATE structure:** the recovered model reproduces the measured detection fraction, within-block
   2-/3-body cumulants, **and the within-window R̂** (the last via the trajectory forward §7).
3. **Identifiability** (§4) — the centerpiece.
4. **Coherence budget** (§5).

## 4. Identifiability — composite Fisher + Godambe bands (the goal = maximise recovery)

"Maximise within-window recovery" = **identify as many ≤2q mechanisms as the data allows, report the
aliased ones honestly.** The deterministic forward gives the **composite sensitivity (Godambe `H`)**

  `H(θ) = Σ_j Σ_σ P_θ(σ_{T_j}) [∂_θ log P_θ(σ_{T_j})][∂_θ log P_θ(σ_{T_j})]^T`,

exact by autograd — where `P_θ(σ_{T_j}) ≡ P_θ(σ_{T_j} | ρ_ss(θ))` (§2.0), so `H` is taken **at the
stationary state and the nominal θ**, and `∂_θ` carries the implicit `dρ_ss/dθ` (the accumulated
coherent term). `rank(H)` = identified directions; `null(H)` = the **aliased class** (reported, never a
false attribution). `rank(H)` is therefore only defined once §2.0 is in — it depends on **both** `ρ_ss(θ)`
and the nominal θ. **Two corrections from the review (MAJOR 3):**
- **Bands use the Godambe sandwich `G = H J⁻¹ H`, not `H⁻¹`** (a pseudo-likelihood loses efficiency;
  `H⁻¹` mis-sizes the bands). `J` (the inter-block variability matrix) is estimated by block-bootstrap;
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
(d7); non-negligible ⇒ a finding. A measured (b) result, never a premise; the papers are
secondary/digest-tier evidence (framing only, never an (a)/(b) basis). (The model itself is never
twirled — the twirl is only this metric's reference channel.)

## 6. Baselines (pristine, recommended settings)

Run comprehensively at their own defaults, declaring version/commit + settings, never editing baseline
code: the shipped **SI1000 prior**; the **independent-edges Pauli-DEM** (the M4 baseline — beaten on
within-block held-out NLL + out-structured on within-block 2-/3-body); **dMLE** (`external/baselines/
DMLE-QEC`, closest prior art). **NOT claimed at d3:** beating the Pauli-DEM on the *long-range*
bunching (that is d7).

## 7. Validation

- **(a) per-block exactness** — each `P_θ(σ_{T_j})` from the §2.1 forward matches an **independent
  brute-force** Born computation (zero shared code) to **total-variation distance `< 1e-10`** (with
  `max|·|` L∞ as a strict diagnostic), and sums to 1 (a build gate + regression pin).
- **(b) composite-vs-joint gap** — a **trajectory full-joint NLL** (a *different method* from the
  composite ⇒ a genuine ≥2-method cross-check on the load-bearing fit) vs the composite, on a feasible
  reduced case; report the θ gap as the composite's (b) band (an extrapolation at full d3 — tagged).
- **(b) within-window R̂** — the **recovered model**, run as a forward-only **trajectory**, reproduces
  the measured within-window over-dispersion within a band; a miss ⇒ the ≤2q dictionary is insufficient
  (3q / cross-window) — a finding, not a silent gap.
- **(b) structure-residual** — detection + within-block 2-/3-body cumulants reproduced.
- **Positive controls (teeth):** a **twirled** model fails the coherence-budget + structure checks; a
  **single-block (under-covering)** fit shows a rank-deficient `H` the full covering repairs; a
  **mis-specified** mechanism set raises the held-out NLL. A check that cannot fail is dead.

## 8. Pre-registration — predictions BEFORE the runs (theory-first)

- **(a)** `⟨X_a Z_b Z_c X_d⟩_{|+⟩⁹} = 0` exactly (the t=0 boundary state's mixed-XZZX syndrome is uniform
  ⇒ uninformative) — the only (a)-grade claim here.
- **(b)** the syndrome-averaged round channel `N_θ` is **primitive for θ > 0** ⇒ a **unique stationary
  state `ρ_ss(θ)`** that power iteration reaches (`N_θ(ρ_ss) = ρ_ss` to `< 1e-10`); existence/uniqueness
  + convergence are predictions about `N_θ`, measured not assumed.
- **(b)** the **Fisher confirmation (§2.0):** the composite `rank(H)` is **rank-deficient at the `|+⟩⁹`
  boundary** and **restored at `ρ_ss(θ)`** (nominal θ = SI1000 prior), with `tr H` / the smallest
  informative eigenvalue orders larger at `ρ_ss(θ)`. Cross-checked by **two methods** (autograd vs
  finite-difference Jacobian); `ρ_ss(θ)` = positive control, `|+⟩⁹` = negative. Exact rank numbers (b).
- **(a)** §2.1 forward exact per block (**TV `< 1e-10`** vs the independent brute-force; `P_θ(σ)` sums to 1).
- **(b)** `H` identifies the dominant ≤2q mechanisms; a **predicted aliased subset** (named before the
  run from the observation structure); reported **conservatively** (composite under-states).
- **(b)** within-window **Pauli-twirl distance + unitarity small** (Darmawan; below a pre-registered
  threshold); non-negligible ⇒ finding.
- **(b)** the white-box **beats the independent-edges Pauli-DEM on within-block held-out NLL** and
  **reproduces the within-window structure incl. R̂** (via the trajectory validation). **The
  long-range bunching is NOT claimed at d3** (out of scope; d7 black-box).
- **(c)** gates: adopt the recovered field per patch iff the (a) check passes, the structure-residual
  (incl. within-window R̂) closes within band, and the conservative `H` ledger is reported.

## 9. Build plan (heavy → ≥3 agents + realtime reviewer + per-block GPU verification)

Decomposed into small independently-verifiable sub-components; each built by an agent with a realtime
reviewer auditing on landing; the **orchestrator verifies each piece against an independent oracle on
GPU before the next** — incremental review+verify, never one solo dump. **Sub-component #2 is the core
new build, NOT glue.**

| # | Sub-component | Independent verification before proceeding |
|---|---|---|
| 0 | **stationary likelihood `ρ_ss(θ)` (ROOT, §2.0)** — syndrome-averaged round channel `N_θ`; power-iteration fixed point on ≤13q (no dense superoperator); implicit-diff gradient; the Fisher confirmation | `N_θ(ρ_ss)=ρ_ss` `< 1e-10`; autograd-vs-finite-diff Fisher; positive control (`rank(H)` collapses at `|+⟩⁹`, restored at `ρ_ss(θ)`) |
| 1 | **block covering** — real d3 patch → ≤4-stab ≤13q blocks co-covering every mechanism footprint (**footprint-feasibility here; Fisher-optimal only after #0 + #4**) | counts vs `window_covering_RESULTS`; every mechanism ∈ ≥1 block |
| 2 | **surface-block Born likelihood (CORE)** — evolve to pre-measure (Spike-A `peak_state`) + ancilla-projector enumeration + reset (faithful order) + surface multi-round readout convolution → `P_θ(σ_{T_j})`, differentiable | vs an **independent brute-force** Born computation `< 1e-10`; `Σ_σ P = 1`; finite-difference grad |
| 3 | **composite ℓ(θ) + deterministic fit** — `w_j≡1`; GPU LBFGS/Adam | gradient finite-diff; convergence on a controlled teacher |
| 4 | **Godambe Fisher + identifiability** — `H`, block-bootstrap `J`, sandwich bands; rank/null ledger | rank on a controlled teacher (known identifiable/aliased) |
| 5 | **trajectory validation forward** — forward-only (no grad) of the recovered model → within-window R̂ + the composite-vs-joint cross-check | within-window R̂ on a teacher; ≥2-method agreement |
| 6 | **metrics + baselines + controls** — NLL, structure-residual, coherence budget; SI1000/Pauli-DEM/dMLE; the §7 positive controls | the positive controls fail loudly |

**Mainline commit-gate:** recover code under `src/qec_twin/` lands only after the (a) check passes +
the structure-residual closes + **full user confirmation**. GPU-only (cuda/complex128, env activated
so the fused kernel loads); scripted-execution (committed `outputs/` scripts, asserts, printed
evidence, flush, `__main__` guard); theory-first (predictions before every run); metric + rigor audit
at close.

## 10. Open items (settle in the build, honestly)

1. **The block covering** — choose blocks that **co-cover every mechanism footprint**
   (footprint-feasibility, available now); a **Fisher-optimal** covering (maximise `rank(H)`) is only
   possible after `ρ_ss(θ)` + the composite `H` are in (sub-components #0 + #4) — the §11.3 split. An
   experiment-design (probe-richness) question.
2. **The composite-vs-joint gap** — the trajectory cross-check (§7) bounds it on a reduced case;
   extrapolation at full d3 is flagged.
3. **Does the ≤2q dictionary reproduce the within-window R̂?** — validated by the trajectory; a miss
   ⇒ 3q-on / cross-window finding (correction 4: model-class gap reported, not hidden).
4. **Multi-round objective — SETTLED (§2.0).** Picked: the **stationary block-law** likelihood on
   `ρ_ss(θ)` (the syndrome-averaged fixed point, power-iterated on ≤13q, differentiable), over the
   per-round chain; the `p = 0.005` readout convolution is in the forward. Remaining = the **build +
   Fisher confirmation** (sub-component #0, §9; pre-registered §8) — the run, not the choice.

## 11. White-box performance certification + the black-box interface (under the standard metrics)

How the §3 standard metrics **certify the white-box's performance** and **hand calibrated information to
the d7 black-box** — the two deliverables the grey-box needs from the d3 step.

### 11.1 What "white-box performance" is on real data (no truth ⇒ certify, don't claim recovery)

Real d3 data has **no ground-truth channel** (correction 4: mechanism *separation* is scored only on a
controlled teacher, never claimed from real data). So "performance" is **three standard certificates**,
not a recovery-vs-truth error:

**Prerequisite (the root, §2.0): the three certificates all presuppose the correct stationary likelihood
`ρ_ss(θ)`.** Held-out NLL, Fisher/Godambe, and the coherence budget are each computed on
`P_θ(· | ρ_ss(θ))`; on the wrong input — the `|+⟩⁹` boundary, or the θ-independent `ρ_code` — they are
empty shells (rank-deficient Fisher / dropped coherent sensitivity). So §2.0 (built + Fisher-confirmed as
sub-component #0) gates everything below.

1. **Observational adequacy** — the held-out **composite syndrome NLL** beats the baselines (SI1000
   prior, independent-edges Pauli-DEM, dMLE) on identical held-out shots (paired bootstrap, one-sided),
   AND the **structure-residual** (detection fraction; within-block 2-body p_ij; 3-body cumulant) closes
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
- the composite **NLL → 0** on the blocks (the recovered model matches the teacher's joint).

This certifies the fit is **unbiased**, the **bands are honest** (coverage), and the **Fisher is
correct** — the guarantee real data cannot give. Mechanism *separation* is scored ONLY here.

### 11.3 Maximising the certified performance (the design levers)

Performance is *maximised*, not assumed, by the **experiment-design** choices scored by the same
metrics — but in a **strict order gated by §2.0**, because `rank(H)` depends on `ρ_ss(θ)` and the nominal
θ:
- **Before §2.0 (no `ρ_ss(θ)` yet):** the **block covering** (§2.2/§10.1) can only be chosen for
  **footprint feasibility** — every ≤2q mechanism footprint co-covered by ≥1 ≤4-stab ≤13q block.
  `rank(H)` is not yet computable, so a *Fisher-optimal* covering is impossible at this stage.
- **After §2.0 + §4 (`ρ_ss(θ)` + composite `H` available):** the covering becomes **Fisher-optimal** —
  chosen to **maximise `rank(H)`** (the identified set) at the nominal θ; probe-richness (round structure
  / basis) chosen to shrink the Godambe bands and raise the NLL win.

This is the ADR-0005 probe-richness / alias-quotient discipline — more identified DOF + tighter bands =
more performance, *earned* (and only earnable once the stationary likelihood is in).

### 11.4 The white-box → black-box interface (calibrated, residual-annotated, coherence-preserving)

The white-box hands the d7 black-box (the GNN fusion-merger) FOUR things, all under the standard
metrics — this is what makes the grey-box **calibrated, complete, and coherence-preserving**:

1. **Per-window recovered CPTP channel `θ` + Godambe bands** — point + uncertainty per mechanism ⇒ the
   black-box **weights each window-channel by its band** (trusts tight-band mechanisms, down-weights
   wide-band/aliased ones): a *calibrated* fusion, not over-trusting the white-box.
2. **Overlap / seam marginals `ρ_BC`** — the reduced window-overlap states = the **cross-window
   consistency anchor** the merger composes on (plan3 §0.5.3); unused at d3, but the output FORM
   provides them so d7 plugs in without re-work (`WindowChannel.rho_bc` exists).
3. **The residual = the black-box's explicit budget** — the structure the white-box **provably cannot
   close** (the **long-range bunching R̂** and **>4-stabilizer correlations**, §2.3), quantified by the
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

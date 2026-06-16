# Stabilizer–tensor-network carrier for d5/d7 — deferred scaling study

> **Status: DEFERRED / TRIGGER-GATED SCALING STUDY (theory-first, 2026-06-15). Not built; no
> results.** This is a forward-looking design draft for a scalable, coherence-preserving white-box
> forward at **d5/d7**, where even the ≤13q dense sub-systems blow up. It is **not the d3 forward**:
> the d3 white-box forward is settled and uses **no tensor-network carrier** (see below). The carrier
> study opens with the d5/d7 rung and is never dropped (project sequencing discipline); it is recorded
> here so the construction, the engine-reuse verdict, the measured Spike-A feasibility finding, and the
> open design question are not lost between now and that rung.
>
> **The d3 forward is the dense surface-block Born likelihood, not this carrier.** At d3 the recover
> forward is a dense ≤13q surface-block ancilla-projector Born likelihood `P_θ(σ)`, fit by a
> block-marginal composite likelihood, evaluated on the dense `WindowChannel` engine
> ([`../../src/qec_twin/forward/window_channel.py`](../../src/qec_twin/forward/window_channel.py)) —
> see [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) (the LIVE d3 design). The
> carrier exists only for d5/d7, where the per-window blocks exceed dense feasibility.
>
> This doc states the construction, the genuine design decisions, the build decomposition, and the
> equivalence pre-registration (standard metrics + independent oracle + bands + positive controls)
> **before any code runs**, per the project's theory-first discipline. It has passed one
> adversarial-review pass (2026-06-15, findings integrated — see the changelog at the end). Any
> mainline code lands only through the commit-gate after the registered equivalence checks pass, and
> only once the d5/d7 rung is open.
>
> Scope tags (project convention): **(a)** exact (theorem / identity / zero-tolerance — the only class
> usable as a downstream premise); **(b)** prediction band (a falsifiable bet; a miss is a finding,
> never later citable as fact); **(c)** heuristic gate / decision rule. Method tags: **[paper]** =
> stated in Harper arXiv:2605.29514; **[twin]** = our application / inference.
>
> Companions: [`README.md`](README.md), [`window_covering_RESULTS.md`](window_covering_RESULTS.md)
> (step-1 circuit facts), [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) (the LIVE
> d3 recover design — the dense forward, no carrier),
> [`../papers/reading_notes/harper_nonclifford_crosstalk_surface_2605.29514.md`](../papers/reading_notes/harper_nonclifford_crosstalk_surface_2605.29514.md)
> (the full-text Harper review = the method basis), [`../plan3.md`](../plan3.md) §0.5.7 (carrier
> candidates), ADR 0008 (carrier study).

## 0. Why this carrier exists — and why only at d5/d7

### 0.1 The dense-register wall (the forcing function), re-scoped

A white-box forward must evolve the **real XZZX syndrome-extraction round** (data + stabilizer
ancilla, parsed from the real circuit — `window_covering_RESULTS.md` §3.1) while **preserving
coherence** (the density matrix carries non-Pauli / non-Clifford channels; never twirl to Pauli).
A faithful data+ancilla register as a dense density matrix scales as `4^n × 16 B`, which sets a hard
qubit ceiling. The dense oracle is exact at **≤13q** (`4^13 × 16 B ≈ 1.07 GB`, well within a 32 GB
GPU); it becomes infeasible well before the full faithful registers of the larger codes.

Where this wall bites decides where the carrier is needed:

- **At d3 the dense ≤13q block oracle suffices — no carrier.** The d3 white-box forward is a
  **dense surface-block ancilla-projector Born likelihood**: the 8 stabilizers are covered by ≤13q
  blocks (9 data + ≤4 ancilla), each block's exact joint syndrome distribution `P_θ(σ_{T_j})` is
  computed on the dense `WindowChannel` engine, and the fit is a block-marginal composite likelihood.
  Every quantity stays within the ≤13q dense ceiling, so a scalable carrier is **not needed at d3**.
  (The full 17q d3 round, `4^17 × 16 B ≈ 275 GB`, is never materialised — the composite likelihood
  works on the ≤13q blocks instead. See [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md).)
- **At d5/d7 the blocks/windows exceed dense feasibility — a carrier is needed.** A d5 round is
  ~25 data + 24 ancilla ≈ 49 q and a d7 round ~49 + 48 ≈ 97 q; even the per-window sub-systems and the
  cross-window/seam structure push past the ≤13q dense ceiling. A dense density matrix is infeasible
  there, so a **scalable, coherence-preserving carrier** is required to represent the faithful round.
  This carrier study is that path, deferred until the d5/d7 rung opens.

This is the wall the carrier dissolves **at d5/d7** — the regime the dense oracle cannot reach.

### 0.2 Engine-reuse verdict — build it ourselves (investigation 2026-06-15)

No existing engine is reusable as a **differentiable** stabilizer-TN carrier:

| Candidate | Open-source? | Differentiable? | Mixed-state / CPTP? |
|---|---|---|---|
| **GCAMPS** (Harper, ref 21; arXiv:2511.06672) | **No confirmed release** — the code-availability link resolves to `events555/sdim`, a *different* pure-Clifford qudit tableau tool | No | Pure-state only |
| **Nakhl STN + magic** (ref 22; PRL 134, 190602 / arXiv:2411.12482) | **No public code** ("data on reasonable request") | No | Pure-state only |
| **Masot-Llima & García-Sáez** (ref 23; PRL 133, 230601 / arXiv:2403.08724) | Yes (`bsc-quantic/stabilizer-TN`) | **No** (Qiskit-Clifford + quimb, notebook-grade) | Pure-state only |

All three are pure-state, non-differentiable **forward** benchmarking tools — neither the gradients
the twin's NLL fit needs nor the mixed-state CPTP a coherence-aware carrier needs. The `aiqec` env
already ships the building blocks: **torch 2.12.0+cu130 (CUDA on), stim 1.16.0, pymatching 2.4.0**,
plus **quimb / cotengra / opt_einsum / autoray** (differentiable-MPS substrate); no jax /
tensornetwork / qiskit; `cuquantum.cutensornet` binding is broken (not needed for the torch route).

**Decision (c):** implement the carrier in-house — **Clifford frame via `stim`, differentiable MPDO
in `torch` (complex128, CUDA)** — reusing the project's θ-differentiable Kraus dictionary
([`mechanisms_torch.py`](../../src/qec_twin/forward/mechanisms_torch.py)) and diagnostics
([`window_diagnostics.py`](../../src/qec_twin/forward/window_diagnostics.py)). Masot-Llima's repo is
read as an **algorithm reference** for the tableau↔TN update rules, never a dependency.

### 0.3 Hardware + runtime budget (user constraints, 2026-06-15)

**GPU 32 GB, RAM 60 GB; a test should run in hours, not weeks.** These bound the design hard:
- **The dense oracle ceiling is ≤13q** (`4^13 × 16 B ≈ 1.07 GB`, well within 32 GB) — the d3 blocks,
  progressive d3/d5 sub-systems (§3), and a d7-interior 13q window are reachable; full d5/d7 faithful
  registers are not. This ceiling is exactly why the carrier is a d5/d7 study: below it the dense path
  (the d3 forward) suffices; above it a carrier is forced.
- **Never materialise a dense d5/d7 round** — the faithful registers (≈49q at d5, ≈97q at d7) exceed
  both GPU and host RAM as dense density matrices. The carrier's transient per-round footprint must
  stay bond-bounded (MPDO) or per-shot-bounded (trajectory), never expand to a dense register.
- **Runtime budget = hours.** Each registered run (pilot, equivalence checks, fits) is scoped to hours
  on one GPU; anything that would take days/weeks signals a wrong representation and is out of scope.
- **From-scratch build.** The carrier is a new build, not a patch of the dense `window_channel`; the
  dense `WindowChannel` survives as the ≤13q oracle (and is the d3 forward's engine — but at d3 there
  is no carrier to patch).

The representation fork (§2.1) is decided on *scaling* feasibility at d5/d7 — the regime where the
dense oracle cannot follow. As recorded below, **Spike A measured Option B (deterministic
Clifford-frame MPDO) non-viable** (the framed bond is large and grows with d), so **Option A
(pure-state trajectory) is the open candidate for d5/d7**; the whole carrier question stays deferred
with the d5/d7 rung.

## 1. The construction (faithful to Harper; tagged)

**Harper's representation (Eq 7) [paper]:** `|ψ⟩ = C |MPS⟩`, with `C` a Clifford operator (tableau)
and `|MPS⟩` a matrix product state. Update rules:
- **Clifford gate `G`** [paper]: `G C|MPS⟩ = C'|MPS⟩` — the Gottesman–Knill tableau update, `poly(n)`.
  The MPS is untouched.
- **Non-Clifford / general operator `U`** [paper]: expand in Paulis `U = Σ_i c_i P_i`, commute through
  `C`: `U|ψ⟩ = Σ_i c_i P_i C|MPS⟩ = C Σ_i c_i (C† P_i C)|MPS⟩ = C|MPS'⟩`. Because `C` is Clifford,
  each `C† P_i C` is a Pauli (Gottesman–Knill), so a **sum of Paulis acts on the MPS**. A physically
  local insertion can become higher-weight on the MPS (`C` delocalises it) — this is the entanglement
  the bond dimension carries.
- **Measurement / reset** [paper → twin]: a sum of Paulis commuted through `C` and applied to the
  MPS; the ancilla measurement collapses to a Pauli outcome in the tableau [paper], with Born
  probability and post-state determined jointly by the tableau and the MPS overlap [twin inference].
  Mid-circuit measure+reset (the syndrome extraction) is native to the formalism; **reset is
  non-unitary** (measure + conditional reset, not a Clifford unitary) and is exact only under
  perfect, leakage-free reset — imperfect reset / leakage (the `leakage`/`thermal` mechanisms, M34)
  is a real (b) residual, not assumed away. The interaction-picture treatment of *interleaved*
  mid-circuit measurements (§2.1) is a build-phase item to verify, not assert.

**QEC interpretation [paper → twin]:** `C` is the **ideal Clifford operator implementing the XZZX
code** (at the d5/d7 distance the carrier targets) — the entire fixed syndrome-extraction skeleton
(the interleaved `Y/H/X` data gates, the CZ layers, reset, measure; all Clifford). Non-Clifford /
noise insertions do **not** change `C`; the **tensor network carries the θ-parameterised error that
perturbs the ideal Clifford state**. `C = ideal code / TN = error` *is* the white-box structure:
held-out syndrome likelihood is read from the TN, while `C` stays the fixed code skeleton. §2.1 lifts
this pure-state picture to the mixed state the twin needs.

## 2. The three differences from Harper — the genuine design work

Harper is **forward-only, pure-state, coherent-unitary noise + sampled stochastic Pauli, scored by
Monte-Carlo LER**. The twin needs three things Harper does not provide; these are the design content.
All of it is for the **d5/d7** regime — at d3 the dense block oracle already gives an exact,
differentiable likelihood with no carrier.

### 2.1 Mixed-state CPTP, not coherent-unitary-only [twin]

Our dictionary ([`mechanisms_torch.py`](../../src/qec_twin/forward/mechanisms_torch.py)) has three
kinds of mechanism: **coherent unitary** (`rz`, `rzz`, spectator `rzz`, `rxx`, `cphase`, `two_pauli_*`,
… — `U(θ)=e^{-iθG/2}`), **stochastic Pauli** (`pauli_x/y/z`, `depol2`, `phase_damp` = stochastic `Z`),
and **non-unital non-Pauli CPTP** (`amp_damp`, `thermal`, `leakage`, `corr_relax`, and
`custom_nonpauli` = amp-damp dressed with a fixed coherent rotation — simultaneously coherent and
non-unital, the trickiest case).

**Theory — every mechanism is carriable [twin], tag (a):** any Kraus operator `K` expands in the
Pauli basis `K = Σ_P c_P P` (the Paulis span `M_{2^n}` — exact); each `C† P C` is a Pauli
(Gottesman–Knill — exact); hence **any Kraus, unital or not, Clifford or not, acts on the TN as a sum
of Paulis through `C`**. So `amp_damp` (`K0 = diag(1,√(1-γ)) = ½(1+√(1-γ))I + ½(1-√(1-γ))Z`,
`K1 = √γ|0⟩⟨1| = ½√γ(X+iY)`) is as carriable as a coherent `rzz`. This is a (a)-exact identity, not a
new result. It says nothing about *cost* — see the fork below.

**The representation fork (the key decision) [twin]** — a CPTP map is a *sum over Kraus branches*, not
a single operator, so *how the mixture is carried* decides exactness, differentiability, and cost.
The fork is settled toward Option A by Spike A (§5.2); both are recorded here so the trade-off is
explicit when the d5/d7 rung opens:

- **Option A — pure-state trajectory (Harper-faithful) — the open d5/d7 candidate.** Per shot, keep a
  pure `C_k|MPS_k⟩`: sample which Kraus fires (prob `‖K_i|ψ⟩‖²`), absorb Pauli/Clifford Kraus into the
  tableau `C` (free), apply the coherent insertion to the MPS, bond-truncate, Born-measure the
  syndrome; the mixed state is the Monte-Carlo average over shots. **Keeps Harper's full benefit**
  (pure stabilizer state ⇒ tableau `O(n²)` + small pure-state `χ`): per shot the stochastic noise is
  sampled (one Pauli-error pattern, absorbed into the tableau) and the ancilla collapse at
  measurement, so the per-shot MPS carries only the weak coherent perturbation. **Costs:** equivalence
  to a density-matrix oracle is **statistical** (CLT, `O(1/√N)`); the fit objective `P_θ(syndrome)` is
  sampled, so its gradient is noisy and needs a score-function / pathwise estimator — **the principal
  open design question for the carrier** (§7.1).
- **Option B — Clifford-frame MPDO — MEASURED NON-VIABLE (Spike A, §5.2).** Carry the mixed state `ρ̃`
  directly as a matrix-product density operator in the **interaction picture of the ideal Clifford
  circuit**: `ρ̃ = U_C† ρ U_C`, so the ideal gates are absorbed into a frame (the tableau tracks the
  Clifford-conjugation of each noise location, `O(n²)`; ideal gates are *free*) and only the noise —
  Clifford-conjugated, hence still a Pauli-basis CPTP map but possibly delocalised — acts on `ρ̃`.
  **Every channel applies deterministically and additively** (the MPDO holds the full mixture, so a
  CPTP map grows the bond by ≤ its Kraus rank and is then SVD-re-compressed — *no* multiplicative
  branch blow-up), and `P_θ(syndrome)` is an **exact, differentiable** contraction — the property that
  made it attractive for the fit. **The single controlled approximation is the bond `χ_ρ̃`** (the
  mixed-state Schmidt rank of the noise correlations), **exact at full bond** (= the dense ρ, on the
  feasible ≤13q sub-systems — §5). **However, Spike A measured the framed bond at a real 13q d3
  sub-system to be 162 — only ~3× below the un-framed 512, noise-mixedness-dominated, and growing with
  d (§5.2). So the deterministic MPDO does not scale favorably**, which is why Option A is the open
  candidate at d5/d7.

**Status of the fork [twin], tag (c):** Option B's deterministic, differentiable likelihood was the
attractive property, but its **mixed-state bond is too large** (Spike A: 162 at a 13q d3 sub-system,
dominated by the irreducible noise mixedness, growing with d — the Clifford frame removes the ideal
coherent entanglement but not the noise mixedness). **Option A (pure-state trajectory) is therefore
the open candidate for d5/d7** — it is scaling-favorable (the per-shot MPS carries only the weak
coherent perturbation), at the cost of a **sampling-based fit gradient** that must be re-derived
(§7.1). The whole fork is **deferred with the d5/d7 rung**: it is decided on the d5/d7 scaling
question, not at d3 (where the dense oracle removes the need for any carrier).

### 2.2 Differentiability — the open design problem [twin]

- **θ-smooth amplitudes.** Reuse [`mechanisms_torch.py`](../../src/qec_twin/forward/mechanisms_torch.py):
  coherent `cos/sin` in θ, stochastic / non-unital `p = sigmoid(θ)`. The Pauli-expansion coefficients
  `c_P(θ)` are smooth. **Banked pitfall (handoff #9):** `θ = 0` is a *degenerate* init for non-unital
  mechanisms (`sigmoid(0) = 0.5` = strong noise), not "no noise"; **initialise non-unital θ at the
  SI1000 prior** (small p), coherent θ at 0 (= identity).
- **Differentiable contraction** — torch autograd through the carrier contraction (complex128, CUDA).
- **The fit gradient under the trajectory (Option A) is the principal open question [twin], tag
  (b)/(c).** With Option A the fit objective `P_θ(syndrome)` is sampled, so its gradient is noisy and
  needs a **score-function / pathwise estimator** — this is the carrier's central unresolved design
  item (§7.1), reopened by Spike A's pivot away from the deterministic MPDO. (Under the abandoned
  Option B the analogous hard part was the differentiable truncated SVD at the discard boundary; that
  difficulty is moot now that the deterministic MPDO is non-viable, but the *truncation itself*
  remains in any MPS-bond representation of the trajectory's coherent part.)
- **Banked pitfall (handoff #8):** computing a channel's superoperator / Choi by probing with a
  non-Hermitian operator basis must **not** pass through the `apply_kraus`/`apply` `hermitianize`
  tail (it symmetrises and destroys the superoperator); diagnostic paths must use the linear
  (no-hermitianize) evolution.

### 2.3 Inverse / fit [twin]

Fit θ to **held-out per-shot syndrome NLL** (field-standard, nats/shot/window, paired bootstrap,
one-sided), on the real d5/d7 patches, each from its own shot-sliced data. Coherence is preserved
end-to-end (the carrier's non-Clifford content *is* the coherence budget; never twirled in the model —
only the downstream Pauli-decoder export diagonalises). Report held-out NLL + Fisher-rank
identifiability (identified vs aliased + per-mechanism alias band) + the PTM off-diagonal coherence
budget. The gradient estimator for the sampled trajectory objective (§2.2, §7.1) is the open piece.

## 3. Layered feasibility (honest) — the carrier is for d5/d7

| Rung | Register | Dense ρ | Carrier role |
|---|---|---|---|
| **d3** (white-box, settled) | 9 data + ≤4 anc per block = **≤13 q** | ✅ ≤1 GB | **no carrier** — the dense surface-block Born likelihood is the forward ([`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md)); the full 17q round is never materialised (composite likelihood works on ≤13q blocks) |
| **d5** (intermediate, deferred) | ~25 data + 24 anc ≈ **49 q** | ❌ | **carrier needed** (trajectory, Option A) — beyond the dense ceiling; rely on per-shot sampling + a measured convergence band |
| **d7** (black-box, deferred) | ~49 + 48 ≈ **97 q** | ❌ | **carrier needed** (trajectory, Option A), plus the seam (out of scope here) |

**Honest scope [twin]:** the carrier's value is purely **scaling** — it appears at **d5/d7**, where the
faithful round exceeds the ≤13q dense ceiling. At d3 there is no carrier: the dense block oracle gives
the exact, differentiable likelihood the recover needs. The bond / variance envelope for the d5/d7
regime (coherent `θ ≈ 10⁻³`, depol `p ≈ 0.01`) is a **(b) prediction to be measured by a pilot at
that rung**, never assumed — and Spike A's finding (§5.2) already warns that the *deterministic*
mixed-state bond is large, which is what motivates the trajectory route. Harper's "over-truncation
lowers LER ⇒ LER is a lower bound" caution [paper L3] applies only if we later score %ΔLER under a
frozen decoder; it does not bind the held-out-NLL recover validation.

## 4. The independent oracle

The oracle is the **dense density-matrix faithful circuit** — the existing `WindowChannel`
([`window_channel.py`](../../src/qec_twin/forward/window_channel.py), GPU-only complex128) on the
feasible **≤13q sub-systems** (the d3 blocks, the progressive d3/d5 faithful sub-sets, and a
d7-interior 13q window). It computes the **exact** ρ and syndrome distribution there, applying each
CPTP map additively to the density matrix (no branch enumeration), which is why it stays feasible.
The carrier is validated against this oracle on the ≤13q sub-systems before any extrapolation to the
full d5/d7 round (where no dense oracle exists — the reason the carrier is needed at all).

**Independence is load-bearing (banked lesson):** an "independent" check that reuses the module's own
kernels proves only self-consistency. The carrier's oracle comparison must share **zero code** with
the carrier: the carrier path is `stim` tableau (Clifford frame) + torch trajectory/MPS contraction;
the oracle path is the dense `apply_channel_local` density-matrix evolution. Neither may call the
other's core. The oracle is built from the load-bearing source (the parsed real circuit), not from the
carrier's representation.

## 5. Equivalence verification — PRE-REGISTRATION (theory-first; bands written before the run)

All scores via the `docs/METRICS.md` ladder (carry each convention); on **real patches** at the
≤13q sub-systems where the dense oracle is feasible, then extrapolated (with measured bands) to the
full d5/d7 round; **GPU-only**.

**Metrics (field-standard):**
- **Data-state ρ:** **trace distance** `½‖ρ_carrier − ρ_oracle‖₁` (the headline equivalence number).
- **Syndrome distribution:** **KL divergence** + **total-variation distance** (never trust the
  syndrome marginal alone — the masking lesson; ρ trace distance is co-required).
- **Channel:** **Choi fidelity** / diamond-norm distance on the 1q/2q reduced channels where feasible.
- **Coherence budget:** PTM off-diagonal Frobenius mass match (`window_diagnostics.coherence_budget`)
  — proof coherence is not silently twirled.
- **Held-out fit:** per-shot syndrome **NLL** (nats/shot/window, paired bootstrap).

**Registered checks + bands:**
- **(a) EXACT — zero-tolerance `< 1e-10`** vs the dense ρ oracle, on the systems where the dense ρ is
  feasible: the **10q one-stabilizer** sub-circuit, the **≤13q circuit-order sub-set**, and the
  **d7-interior 13q window**. Data trace distance **and** syndrome TV/KL **and** Choi fidelity **and**
  coherence-budget all match to `< 1e-10`. *The construction is an exact identity (Pauli-completeness +
  Clifford conjugation), so the carrier must reproduce the dense ρ on the feasible sub-systems.*
- **(b) statistical convergence (the trajectory / scaling claim):** the Monte-Carlo syndrome estimate
  vs the oracle decays as `O(1/√N)` (CLT band) on the ≤13q sub-systems; the bond `χ` of the per-shot
  MPS carrying the coherent perturbation, and the held-out-NLL gap vs the full result, are measured at
  the d5/d7 rung and reported as curves — **predictions to be measured, not assumed**.

**Positive controls (each (a) check must have teeth — a check that can't fail is dead):** a
deliberately-broken carrier must **exceed** the band —
1. **dropped Clifford conjugation** (omit the `C† P C` sign/permutation) → wrong syndrome;
2. **twirled carrier** (diagonal-truncate the PTM / drop the coherent insertions) → coherence budget
   collapses, ρ trace distance blows up.
Each control is asserted alive (its metric > band) before the real checks are trusted.

**Decision rule (c):** adopt the carrier as the d5/d7 white-box forward **iff** all (a) checks pass
`< 1e-10` on the ≤13q sub-systems **and** the (b) convergence shows a feasible per-shot cost for the
full d5/d7 round. Else fall back to the ADR 0008 **C1 composed architecture**.

**Prediction (written before any run) [twin]:** the (a) checks PASS at `< 1e-10` (the construction is
an exact identity: Pauli-completeness + Clifford conjugation); under Option A the statistical
convergence holds at `O(1/√N)` and the per-shot MPS bond stays modest at the d5/d7 noise level (to be
measured); the positive controls FAIL loudly. A miss on any (a) check is a code/derivation bug (a
finding), not a physical result.

### 5.1 Verify-first spikes — the de-risk (BEFORE the build)

Per the verify-first lesson (a cheap probe before a big rebuild) and theory-first (predict before the
run), spikes run before any mainline build — committed `outputs/` scripts (non-mainline), GPU,
hours-scale.

**Spike A — feasibility (decided the representation fork).** The MPDO route is only viable if the
mixed-state bond `χ_ρ̃` stays small. The spike measured it on the *exact* object (a feasible real d3
sub-system, ≤13q, dense): compute `ρ̃ = U_C† ρ U_C` (the ideal Clifford `U_C` from `stim`; `ρ` from
the dense oracle) and the **Schmidt spectrum of `vec(ρ̃)`** across the spatial cut → the `χ_ρ̃` for a
`< 1e-6` truncation error, compared to the un-framed `vec(ρ)` bond. Uses only the oracle + `stim` +
SVD (a measurement of the exact object — no carrier implementation, no independence concern).
**Result: §5.2 — the Option-B bond is too large; the fork pivots to Option A.**

**Spike B — logic (independent-implementation correctness), pending at the d5/d7 rung.** A minimal POC
validates the genuinely-new construction — the **Clifford-frame interaction picture with interleaved
mid-circuit measurements and non-unital CPTP**, in the chosen (trajectory) representation — against an
independent dense oracle before any mainline build, on a real sub-circuit with **two adjacent
stabilizers that share data** (so the interleaved CZ order is load-bearing), at SI1000-prior strengths
(small θ ≠ 0; never the `θ = 0` degenerate point). Metrics: data-ρ trace distance, syndrome KL/TV,
coherence budget, all `< 1e-10` (a, zero-tolerance), with the dropped-conjugation and twirl positive
controls asserted alive. **Gate (c):** the full ≥3-agent mainline build (§6) starts only if the POC
passes; a fail sends the construction back to derivation (or to the ADR 0008 C1 fallback).

### 5.2 Spike A — RESULT (2026-06-15): FINDING — the Option-B MPDO bond is too large

Run: `outputs/spikeA_integrate.py` (orchestrator) wiring the three reviewed builders
(`spikeA_oracle_round` / `spikeA_ideal_unitary` / `spikeA_bond_metric`), on the **real `d3_at_q6_7`
13q sub-system** (9 data + the 4 weight-4 stabilizers' ancilla, support-union = all 9 data),
SI1000-prior θ (coherent `rzz`/`rz` θ=1e-3; `depol2` p=1e-2; `pauli_x` p=1e-3), GPU / complex128 /
`no_grad`, on the fused subsystem-Kraus kernel. Bond = operator-Schmidt rank of `vec(ρ)` per spatial
cut (small-side Gram; **cross-checked at the max-bond cut by a `gesvd` SVD — agree, max Δ = 1.2e-9**).
The build surfaced + fixed three integration bugs (autograd-graph OOM → `no_grad`; the >25-dim reshape
at n=13 → block-grouped; cusolver SVD failure on lopsided cuts → Gram); the fused kernel needed the
env activated so `ninja` is on PATH (`outputs/kernel_env_fix.sh`, `run_spikeA.sh`).

Measured bond profile (χ at 1e-6 relative-Frobenius truncation; register order = 9 data then 4 ancilla):

| cut | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| un-framed `ρ_peak` | 4 | 12 | 30 | 66 | 191 | 334 | 512 | 384 | 256 | 64 | 16 | 4 |
| **framed `ρ̃`** | 4 | 10 | 23 | 44 | 83 | 97 | 142 | **162** | 152 | 55 | 16 | 4 |

- **MAX framed bond = 162** (cut 8) vs MAX un-framed = 512 — the Clifford frame reduces the bond only
  **~3.2× at the peak** (up to 3.6× at cut 7), **not** orders of magnitude.
- **162 is NOT modest** — ≈5× Harper's pure-state `χ_max = 32` (at d=9), and this is a d3 sub-system
  with only **4 of 8** ancilla (the full d3 / d5 / d7 bond is strictly larger). It is 4.0% of the
  4^6 = 4096 balanced-cut ceiling, so the state is not full-rank, but the absolute bond is high.
- The framed bond is **dominated by the stochastic-noise mixedness** (≈ the count of significant
  Pauli-error patterns from the 16 `depol2` channels at p=1e-2), which grows with the number of noise
  locations ⇒ the bond follows an area law in the cut and grows with d. The Clifford frame removes the
  ideal-code *coherent* entanglement but **cannot remove the irreducible noise mixedness**.
- The **post-round 9-data state** (ancilla traced out) has bond only **32** — the blow-up is the
  TRANSIENT mid-round ancilla entanglement (the 162 peak), not the final 9-data object.

**Prediction outcome — (b) MISS = FINDING (not citable as fact).** The registered §5.1 prediction was
"framed `χ_ρ̃` ≪ un-framed AND modest." It missed (only ~3× reduction; 162 not modest): the
**deterministic Clifford-frame MPDO (Option B) does not scale favorably** for the real mixed-state
noise. This is exactly the §2.1 / §7.1 risk the spike was built to settle, settled negatively.

**Decision (c) — Option A (pure-state trajectory) is the open d5/d7 candidate (pending user steer).**
The pure-state **trajectory** (Harper-faithful) is the scaling-favorable path: per shot the stochastic
noise is *sampled* (one Pauli-error pattern, absorbed into the Clifford tableau) and the ancilla
*collapse* at measurement, so the per-shot MPS carries only the weak coherent perturbation (θ=1e-3) →
a small Harper-scale bond; the mixed state is recovered by averaging over shots. The cost A pays — a
**sampling-based fit gradient** and statistical (sampling) equivalence to the oracle — is now the
principal open design question (§7.1: the inverse-fit objective must be re-derived for the trajectory).

**Caveats (honest).** The 162 is for the register ordering (9 data then 4 ancilla); a 2D-aware
ordering might lower the constant but not the area-law scaling. Measured at p=1e-2 (SI1000 prior);
lower noise ⇒ smaller bond. A 4-ancilla sub-system ⇒ a lower bound on the full-d3 bond — and the
d5/d7 bonds are strictly larger still, reinforcing the trajectory route. The cross-check covers
numerical robustness, and the metric's selftest controls (product/Bell/n=13) cover correctness; the
bond magnitude is trustworthy.

## 6. Build decomposition (heavy → ≥3 agents + realtime reviewer + per-block GPU verification)

Per the heavy-task discipline, when the d5/d7 rung opens the carrier is decomposed into small
**independently-verifiable sub-components**, each built by an agent with a **realtime reviewer**
auditing it against this registration the moment it lands, and the **orchestrator verifying each block
against the independent oracle on GPU before the next block starts** — incremental review+verify, never
one solo dump.

| # | Sub-component | Independent verification before proceeding |
|---|---|---|
| 1 | **Clifford-frame engine** — parse the real d5/d7 circuit → `stim` tableau; the ideal-circuit frame `U_C` + the per-location Clifford conjugation `C† P C`; reset/measure in the frame | stim cross-check; reproduce a noiseless syndrome exactly |
| 2 | **noise → Pauli-sum → trajectory** — Pauli-expand each `mechanisms_torch` Kraus; Clifford-conjugate; per-shot sample the stochastic branch into the tableau, apply the coherent insertion to the MPS | 1q/2q reduced channel vs dense `apply_channel_local` (independent), `< 1e-10` (averaged) |
| 3 | **differentiable trajectory likelihood** — torch MPS contraction + bond truncation + the sampled-objective gradient estimator (§7.1) | finite-difference / variance-reduced gradient check; CLT convergence to the dense ρ at small n |
| 4 | **syndrome Born-likelihood** — `P_θ(observed syndrome)` via the frame projectors + trajectory averaging; interleaved mid-circuit measurement handled in-frame | vs dense oracle syndrome distribution (the (a)/CLT check) |
| 5 | **equivalence harness** — the independent dense oracle + the §5 metrics + positive controls | the positive controls fail loudly |

**Mainline commit-gate:** carrier code under `src/qec_twin/forward/` lands only after the (a) checks
pass **and** full user confirmation (the mainline commit-gate), and only once the d5/d7 rung is open.
Docs (this file) follow the normal flow. GPU-only model compute throughout (no `device="cpu"`, no
cuda-if-available fallback); scripted-execution for every run (committed script under `outputs/`,
precondition asserts, printed evidence, flushed output, `__main__` guard for any multiprocessing).

## 7. Open questions (to settle by pilot / derivation at the d5/d7 rung — not assumed)

1. **The sampled-trajectory fit gradient (Option A) — the principal open design question.** With the
   deterministic MPDO (Option B) measured non-viable (§5.2), the carrier is a pure-state trajectory,
   whose fit objective `P_θ(syndrome)` is sampled. The **score-function / pathwise gradient estimator**
   (and its variance reduction) for the held-out-NLL fit must be derived and validated before any
   mainline build. *Principal user-steering item.*
2. **Per-shot MPS bond / variance envelope** for the d5/d7 regime `(θ ≈ 10⁻³, p ≈ 0.01)` — measure (b)
   at the rung; Spike A's finding bounds the *deterministic* bond from below, but the trajectory's
   per-shot bond (weak coherent perturbation only) is the relevant unmeasured quantity.
3. **Bond-truncation gradient stability in the trajectory MPS** — the truncated SVD on the per-shot
   coherent MPS is non-smooth at the discard boundary; validate by finite-difference; only the ≤13q
   oracle checks are lossless.
4. **Interleaved mid-circuit measurement in the Clifford frame** — the interaction-picture treatment
   of the syndrome measurements (and non-unitary reset) when the per-shot state carries coherence;
   correct in Harper's pure-Clifford ancilla, to be derived + verified for the trajectory before
   scaling.

## 8. Discipline carried forward (unweakened)

GPU-only model compute; coherence preserved end-to-end (the carrier's non-Clifford content = the
coherence budget; never twirl in the model); circuit-derived adjacency; theory-first (predictions
before every run); standard metrics via the METRICS.md ladder (including internal equivalence checks);
independent oracle (zero shared code); positive control on every check; scripted-execution; mainline
commit-gate; plain reporting (no "validated / machine-exact" inflation of a draft or a pilot).

## Changelog

- **2026-06-15 v1 → v2 (adversarial review integrated).** v1 proposed Option B as an *explicit
  low-rank pure-state ensemble* claimed "machine-exact, no truncation" at ≤13q. Review found this a
  **blocker**: a pure-state ensemble multiplies Kraus branches across noise locations
  (16-Kraus `DEPOLARIZE2` per CZ ⇒ `16^{#CZ}` ≈ `10^{14–28}` branches at ≤13q), the exact blow-up the
  predecessor rejected. **Fix:** Option B was reframed as a **Clifford-frame MPDO** (mixed state
  carried directly; CPTP additive; single bond axis `χ_ρ̃`; full bond = dense ρ at ≤13q). Consequent
  fixes: `custom_nonpauli` added to the non-unital list; the measurement sentence re-tagged
  [paper → twin]; leakage-free-reset (a)-conditioning carried over; interleaved-measurement-in-frame
  added as an open question.
- **2026-06-15 v2 → v3 (hardware constraints + Spike A).** GPU 32 GB / RAM 60 GB / hours-not-weeks
  integrated as first-class constraints. Added the verify-first spikes; **Spike A ran and measured the
  framed MPDO bond = 162 at a 13q d3 sub-system (cross-checked by gesvd, max Δ = 1.2e-9) — a (b) MISS:
  Option B (deterministic Clifford-frame MPDO) is non-viable**, pivoting toward Option A (pure-state
  trajectory) with a sampling-based fit gradient as the new open question (§5.2).
- **2026-06-15 v3 → v4 (re-scope to a deferred d5/d7 scaling study).**
  - **Re-scoped the carrier to a deferred / trigger-gated d5/d7 scaling study** — it is *not* the d3
    forward. Re-titled and reframed the status, intro, and §0.1/§0.3 around where the dense-register
    wall actually bites: ≤13q dense is feasible (d3), the carrier is needed only where the faithful
    round exceeds that ceiling (d5/d7).
  - **Recorded that the d3 forward is the dense surface-block ancilla-projector Born likelihood** (fit
    by a block-marginal composite likelihood on the dense `WindowChannel`, no tensor-network carrier),
    linking to [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) as the LIVE d3 design.
  - **Resolved the Option-B lock contradiction** — removed all "Option B LOCKED for d3 / d3 active
    scope" assertions and the standalone "⚠ OVERTURNED" patch banner; folded its content into a single
    coherent narrative: Option B is measured non-viable by Spike A (bond 162), Option A (trajectory)
    is the open d5/d7 candidate, the whole fork is deferred with the d5/d7 rung.
  - **Deleted the falsified 9q measurement-instrument content** (the §0.2 instrument-failure framing
    and the per-stabilizer-factorisation positive control) and **removed all four links to
    `window_instrument_derivation.md`** — that derivation file has been removed from the repo.
  - **Re-scoped §3 feasibility** so the d3 row is served by the dense oracle (no carrier) and the
    carrier's feasibility story is d5/d7; re-scoped §2's differentiability/inverse and §5–§7 to d5/d7.

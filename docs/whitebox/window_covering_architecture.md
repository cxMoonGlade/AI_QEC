# Window-covering noise-model architecture (real XZZX)

> Design spine for the white-box noise model on the real Google XZZX surface code, fit to real hardware
> syndrome data. A design record, not a claim of results.

## Decisions

1. **Model = a FIELD of WINDOW channels.** Each channel = one window's noise, a multi-qubit CPTP map on
   the window's data qubits. This replaces the per-qubit factorized field (one independent single-qubit
   channel per data qubit), which structurally cannot carry correlated multi-qubit noise. **Runtime
   forward (D3):** the forward is the **dense ≤13q surface-block ancilla-projector Born likelihood**,
   fit by a **block-marginal composite likelihood**; the dense `WindowChannel` is the engine/oracle
   — see Multi-round forward below and [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md).

2. **Window content = a weight-≤t MECHANISM composition** from the catalog (`docs/error_mechanisms.md`,
   M0–M34; operators in `forward/channels.py`): the correlated/coherent mechanisms (M8 RZZ, M9 2q-depol,
   M10 RXX/RYY, M11 spectator crosstalk, M12 correlated relaxation, M21 conditional phase, M22–M33
   parasitic couplings) placed by local support, plus the 1q set, on the window's density matrix.
   Parameters = mechanism strengths (≈ linear in the window's gate count, not a dense 2^(2w)-dim Choi),
   so the channel is tractable, identifiability-friendly, and carries the **coherent slot** natively
   (density-matrix / Stinespring; coherent + non-Pauli + non-Clifford representable).

3. **Window = the 3×3 block around each data qubit.** Scale = the code's correction limit
   `t = ⌊(d-1)/2⌋` (d=7 → t=3): the twin only needs to model noise up to the correctable weight; beyond
   `t` the code fails regardless. The block is the radius-`⌊t/2⌋` = 1 ball in the **share-a-stabilizer
   graph** — two data qubits are adjacent iff some stabilizer's support contains both. A weight-4
   plaquette covers a 2×2 data block, so each data qubit is adjacent to all eight grid-neighbours
   (orthogonal **and** diagonal); the radius-1 ball is therefore the **3×3 block = ≤9 data qubits**
   (9 interior, fewer at the boundary). Within the ≤~15-qubit exact-backend wall.

4. **Cross-boundary error chains — handled by a COMPLETE COVERING.** One 3×3 window centered on every
   data qubit ⇒ **every connected weight-≤t configuration is native to ≥1 window**: a connected ≤t set
   has a member within graph-distance `⌊t/2⌋` = 1 of all its members (e.g. a 3-chain's middle qubit), so
   the whole set sits in that member's 3×3 window. (2604.01197's (k+1)-layer constructive covering,
   applied to the trivial-phase **noise-channel field** — its valid scope.) Fusion is then a **bounded
   consistency-merge** over overlapping windows, not an unbounded reconstruction of cross-boundary
   chains. Bigger windows do not remove cross-boundary chains (there is always a boundary); a complete
   covering does. The schedule is generated from the **parsed stabilizer supports** of the real circuit
   (build-order step 1). The covering choice is **footprint-feasibility** until `ρ_ss(θ)` and the
   composite Fisher `H` are in hand, then **Fisher-optimal** (maximise `rank(H)` at the nominal θ) —
   see [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) §11.3.

5. **Fusion = white-box recover + BLACK-BOX GNN composition.** Recover fits each window channel; the GNN
   composes them over the covering. The GNN is a **first-class tool** (the scalable GPU realization of
   the composition); the covering gives it a bounded, testable problem (consistency-merge), calibrated
   against the Petz / exact-truth anchor (CF-WR). Its output is a calibrated band, never a premise.

6. **Coherence preserved END-TO-END.** Each window channel carries coherence natively (density matrix);
   the composition must preserve it (CPTP + coherent structure — the CF-WR composition-limit theory).
   The twin does **not** twirl down to Pauli. Pauli/DEM appears only as a **lossy downstream export**
   when feeding a Pauli decoder (e.g. an MWPM LER evaluation), a property of *that decoder*, band-
   tracked, never the twin's representation — and that residual (what a Pauli decoder discards) is itself
   a reportable result. RECOVER + validation are syndrome-NLL, hence decoder-independent, so the whole
   fit+validate loop preserves coherence.

7. **The hard core = coherent cross-window composition (the seam).** Stitching adjacent windows' coherent
   CPTP channels into one globally consistent, CPTP, coherence-preserving field is the
   CF-WR / Petz / `ρ_BC` problem. The covering downgrades it from unbounded reconstruction to a bounded
   consistency-merge, but it stays the hardest link. The architecture in one line: **fidelity** = native
   coherence inside each window; **correctness** = the covering makes the fusion bounded and verifiable.

## Multi-round forward (D3: dense ≤13q surface-block ancilla-projector Born likelihood)

The window channel is single-round; real data is multi-round on a measured, evolving state. The forward
fits the coherent window channels to real multi-round detector data via **window-local coherent
spacetime marginals**.

**Runtime forward (D3).** The forward is the **dense ≤13q surface-block ancilla-projector Born
likelihood**: evolve the data + block ancilla (9 data + ≤4 ancilla, ≤13q) through the faithful round
on the dense oracle to the pre-measure state, enumerate the ≤4 ancilla measurements as
computational-basis projectors + reset in faithful circuit order, record `P_θ(σ_{T_j})` per block;
fit by the **block-marginal composite likelihood** `ℓ(θ) = Σ_j log P_θ(σ_{T_j})` over held-out
shots. The dense `WindowChannel` is the engine and correctness oracle. The full d3 faithful register
(17q = 275 GB) is never run whole; blocks stay ≤13q, GPU-feasible on the 5090. (A 9q data-register +
per-stabilizer measurement instrument approach was tried and falsified — retired. See
[`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) for the full design.) The register
size and cost are measured on the real data, not assumed.

**Input state — `ρ_ss(θ)`, not the t=0 boundary.** The forward is evaluated on the **θ-dependent
stationary state `ρ_ss(θ) = fixed point of N_θ`**, the syndrome-averaged data channel for one noisy
round, found by power iteration on ≤13q and differentiable in θ. Two inputs are ruled out: the t=0
boundary `|+⟩⁹` is not a codeword (its mixed-XZZX syndrome expectation is exactly zero ⇒ the syndrome
is uniform ⇒ the Fisher is rank-deficient, most mechanisms unidentifiable), and the θ-independent ideal
`ρ_code` drops the accumulated coherent sensitivity `dρ_ss/dθ` (the cross-round build-up of coherent
error that the white-box exists to recover). See [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md)
§2.0 for the derivation.

## Scale mapping — d3 → d7 → d5 (D1)

The white-box / black-box split maps to the dataset's three distance rungs, but the execution order is
**d3 → d7 → d5**: first certify the clean single-window white-box, then attack the real seam at d7, then
use d5 as the intermediate-scale validation / interpolation rung.

| Rung | Distance | Dataset object | Description | Build step |
|---|---|---|---|---|
| White-box capability | **d=3** | 9 standalone `d3_at_q*` patches (`d3_at_q2_7, q4_5, q4_9, q6_3, q6_7, q6_11, q8_5, q8_9, q10_7`) | 9 data + 8 XZZX stabilizers, all internal, no seam, fully observed = clean single-window twins. step-1 a7/b6 verified all nine. Fit reports held-out syndrome NLL + identifiability (Fisher rank) + per-mechanism alias band. | step-3 |
| Black-box capability | **d=7** | `d7_at_q6_7` (49 windows + real seam) | The black-box (GNN + Petz) composes per-window channels into a globally consistent, coherence-preserving field; validated by held-out syndrome NLL and %ΔLER under a frozen decoder. | step-4 |
| Intermediate validation | **d=5** | 4 patches | Post-d7 sanity / interpolation rung; structural checks (20/20 cross-check) confirmed same facts hold. | step-5 (after d7) |

This realises Decision 5 (white-box recover + black-box GNN composition) and build order step-3/4
with d5 retained as a post-d7 validation rung rather than a gate before d7.

## Own-data-per-scale principle (D2)

Each scale fits its white-box from its **own** data; no cross-scale parameter transfer occurs:

- d3 white-box is fit on d3 syndrome data.
- d7 per-window white-box fit uses d7's own data (through the seam).
- The black-box **composes** already-fitted window channels — it does not import d3 parameters into
  d7.

Rationale: `d3_at_q6_7` and the d7 `(6,7)` interior window are the same physical qubits (step-1 a7:
exact coord match), but they are **different hardware runs** (different `.stim`, different syndrome
data, different crosstalk neighbourhood). Fitting each scale from its own data avoids an unproven
assumption that internal mechanisms transfer across d3/d7 context, and keeps d7-failure attribution
clean (black-box composition error, not white-box transfer error).

## Build order

1. **Covering schedule** — from the parsed stabilizer supports of the real circuit: the 3×3 windows
   centered on each data qubit + the computational completeness check.
2. **`WindowChannel`** — the multi-qubit mechanism-composed CPTP channel + reduced-block / `ρ_BC`
   extraction.
3. **Single-window recover on real XZZX** — fit the window channel to the 9 standalone d3 patches
   (fully-observed window twins, no seam).
4. **Composition** — white-box Petz anchor + black-box GNN, bounded by the covering; validated on
   d7 (49 windows + real seam).
5. **d5 validation** — rerun the own-data-per-scale checks on d5 as the intermediate-scale sanity /
   interpolation rung after d7.

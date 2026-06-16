# Real XZZX d3 surface noise model — registration

> The white-box noise model on the real Google XZZX **d3** surface code, fit to real hardware syndrome
> data. The code is XZZX (8/8 mixed stabilizers), parsed from the real circuit.
>
> **Scope (decision brief 2026-06-15, D1).** d3 is the first rung for **both** white-box and
> black-box: the dataset ships **nine standalone `d3_at_q*` patches** —
> `d3_at_q2_7, q4_5, q4_9, q6_3, q6_7, q6_11, q8_5, q8_9, q10_7` — each covered by overlapping
> **2×2 (4 data) windows**. Ancilla cannot be eliminated: noise lives on the data⊗ancilla entangled
> state before measurement. **Measured register: 4 data + 2 full-in ancilla = 6q per window (d3;
> ≤6q across all scales, never 8q — (a)-exact, `outputs/covering_2x2.py`). No seam-only stabilizers
> exist at the 2×2 scale** (every stabilizer is full-in ≥1 window — d3 8/8; (a)-exact). Per-window
> identifiability ceiling = **2 syndrome bits/window (d3)**. Each 2×2 window is fit faithfully (6q),
> then the black-box GNN composes them via cross-window data-consistency into the d3 patch from this
> rung. Cross-patch composition extension is the **d=7** rung (49 windows + real seam); **d=5**
> (4 patches) is the post-d7 intermediate-scale validation / interpolation rung — out of scope for
> this registration.

## 1. Geometry — parsed from the real circuit

Read the stabilizers + logical from each standalone d3 patch's `circuit_ideal.stim` (the nine shipped 105Q `d3_at_q*` patches above, e.g. `d3_at_q6_7`): 9 data qubits; 8 mixed XZZX
stabilizers (bulk weight-4 `X-Z-Z-X`, boundary weight-2 mixed); logical from `OBSERVABLE_INCLUDE`.
d3 = 9 data = 2⁹ fits the exact backend; the stabilizers are Hermitian / square-to-I / mutually
commuting (verified). Each d3 patch is **covered by overlapping 2×2 windows**: each weight-4 plaquette
defines one 2×2 window (4 data + 2 full-in ancilla = 6q — measured, `outputs/covering_2x2.py`), and
the overlapping windows together tile the full 9-data patch. **No seam-only stabilizers exist at the
2×2 scale**: every stabilizer is full-in ≥1 window (d3 8/8 — (a)-exact, `outputs/covering_2x2.py`);
the black-box's job is cross-window data-consistency over shared data (overlap ≤4) + the long-range
residual, not seam-stabilizer absorption.

## 2. Measured structure — the model target

The motivating measured structure to date is from a **different device** — real **72Q** set2
`d3_at_q5_5/X/r15` sample_00 ([`surface_recover_RESULTS.md`](../_archive/surface_recover_RESULTS.md), **legacy
reference**): device vs SI1000 — detection 2.4×, edge-pij 3.6×, 3-body cumulant 2× — showing an
independent-edges model is insufficient (the model must carry correlations + the higher magnitude). The
analogous structure on the **105Q** d3 patches is the **first step-3 re-measurement** (to confirm this
on the live front; the 72Q numbers are not assumed to transfer across devices). **Each patch is fit from its OWN data** (D2): no cross-scale
transfer — the d3 white-box is fit on d3 syndrome data, and the d7 per-window white-box (black-box
scope) is fit on d7's own data through the seam; the black-box only composes already-fitted window
channels, it does not import d3 parameters into d7.

## 3. The model — window-channel field over the mechanism catalog

A field of window channels ([`window_covering_architecture.md`](window_covering_architecture.md)):
each window = a weight-≤t composition of catalog mechanisms (M0–M34, including the correlated/coherent
M8/M9/M10/M11/M12/M21/M22–M33) on the window's density matrix, strengths fit to the real syndrome data.
The taxonomy is `docs/error_mechanisms.md`; the channel operators are built differentiably (torch) so
strengths can be fit by gradient. Coherence is preserved end-to-end — the model does not reduce to a
Pauli channel.

**Runtime forward = syndrome-conditioned multi-round detector-record likelihood (6q 2×2 window: 4 data
+ 2 full-in ancilla = 6q at d3; ≤6q all scales, never 8q — measured, `outputs/covering_2x2.py`), fit by
a composite likelihood on real `detection_events.b8` (D3).** From the real reset boundary, the forward
propagates `R = 90` rounds on the dense `WindowChannel` oracle with the **recorded** ancilla outcomes
(per round: noisy gates → project the ancilla on its recorded outcome → renormalize → reset, in faithful
circuit order; the verified single-round projector core called R times), accumulating `log P_θ(record)`
per window in the log domain (boundary rounds prep/readout modeled distinctly). The unconditional
**stationary state `ρ_ss(θ)`** is **retired as the input** — it is degenerate for the unital SI1000
prior (`ρ_ss = I/16`, `rank(H)=1`) and kept only as the negative control; the lift comes from the
device's non-unitality + the multi-round structure (see
[`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) §2.0). The recover objective is the
composite log-likelihood `ℓ(θ) = Σ_j log P_θ(record_j)` (equal weights, held-out shots). d7 cross-window
is deferred. (A 9q data-register + per-stabilizer measurement instrument approach was tried and
retired.)

**The dense `WindowChannel` is the engine and correctness oracle.** The already-drafted faithful
`WindowChannel` (generic over window data + ancilla; supports any 2×2 window directly) implements the
forward and serves as the correctness oracle (independent brute-force Born computation,
TV `< 1e-10` gate). GPU-only model compute throughout (no `device="cpu"`, no cuda-if-available
fallback); coherence preserved end-to-end, never reduced to a Pauli twirl. See
[`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) for the full forward spec, composite
likelihood, Godambe bands, and §11 certification/black-box interface.

## 4. Validation — real data, no synthetic ground truth

Held-out per-shot syndrome **NLL** (field-standard: nats/shot/window, paired bootstrap, one-sided) + the
**structure-residual** check (reproduce the measured detection / 2-body / 3-body), reported **per patch**
across the nine standalone d3 patches, plus identifiability (Fisher rank → identified vs aliased + a
per-mechanism alias band). There is no exact "recovery vs teacher" on real data; claims are
observation-fit + residual structure, with honest bands. Per-block exactness is validated against the
dense `WindowChannel` oracle (TV `< 1e-10`, independent brute-force Born computation) before any real-data
run — see [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) §7.

## 5. Discipline

Real data; the 105Q d3 release has **no sample layer**, so train / held-out / escrow are gated by
**shot-slicing** (disjoint shot ranges), not sample ids; decoder-independent for the
structure read; shipped `decoding_results/` priors are evaluator/baseline-only, never learner input.
GPU; scripted-execution. Plain reporting.

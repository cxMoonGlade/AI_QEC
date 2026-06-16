# Real XZZX d3 surface noise model — registration

> The white-box noise model on the real Google XZZX **d3** surface code, fit to real hardware syndrome
> data. The code is XZZX (8/8 mixed stabilizers), parsed from the real circuit.
>
> **Scope (decision brief 2026-06-15, D1).** d3 is the **white-box** rung: the dataset ships **nine
> standalone `d3_at_q*` patches** — `d3_at_q2_7, q4_5, q4_9, q6_3, q6_7, q6_11, q8_5, q8_9, q10_7` —
> each 9 data + 8 full-in XZZX stabilizers, no seam, fully observed = a clean single-window twin. The
> white-box is fit and reported across these nine patches (plural). Cross-window / seam composition is
> the **black-box** capability (validation rung d7, 49 windows + real seam). The execution order is
> **d3 → d7 → d5**: d5 (4 patches) is retained as the post-d7 intermediate-scale validation /
> interpolation rung, not a prerequisite for the d7 seam — out of scope for this registration.

## 1. Geometry — parsed from the real circuit

Read the stabilizers + logical from each standalone d3 patch's `circuit_ideal.stim` (the nine shipped 105Q `d3_at_q*` patches above, e.g. `d3_at_q6_7`): 9 data qubits; 8 mixed XZZX
stabilizers (bulk weight-4 `X-Z-Z-X`, boundary weight-2 mixed); logical from `OBSERVABLE_INCLUDE`.
d3 = 9 data = 2⁹ fits the exact backend; the stabilizers are Hermitian / square-to-I / mutually
commuting (verified). Each patch's 8 stabilizers are **all internal** (full-in, no seam), so a d3
patch is exactly a standalone fully-observed 3×3 window twin
([`window_covering_RESULTS.md`](window_covering_RESULTS.md) §3.1: each d7 interior window centred on a
d3 centre has data exactly equal to that standalone d3 patch — a7 exact, b6 9/9).

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

**Runtime forward = dense ≤13q surface-block ancilla-projector Born likelihood, fit by a
block-marginal composite likelihood (D3).** The forward evolves 9 data + ≤4 ancilla (≤13q) through
the faithful round on the dense `WindowChannel` oracle to the pre-measure state, enumerates the ≤4
ancilla measurements as computational-basis projectors + reset in faithful circuit order, and records
the Born outcome probabilities `P_θ(σ_{T_j})` per block. The data input is the **stationary state
`ρ_ss(θ)`** (the θ-dependent fixed point of the noisy round; not the t=0 boundary `|+⟩⁹` — see
[`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) §2.0). The recover objective is the
composite
log-likelihood `ℓ(θ) = Σ_j log P_θ(σ_{T_j})` (block-marginal, equal weights, held-out shots). The
full d3 faithful register (17q = `4^17 × 16 B = 275 GB`) is never run whole; the oracle operates on
blocks of ≤13q (9 data + ≤4 ancilla), GPU-feasible on the 5090. d7 cross-window is deferred. (A 9q data-register + per-stabilizer measurement instrument approach was
tried and retired.)

**The dense `WindowChannel` is the engine and correctness oracle.** The already-drafted faithful
`WindowChannel` (generic over window data + ancilla) implements the forward and serves as the
correctness oracle (independent brute-force Born computation, TV `< 1e-10` gate). GPU-only model
compute throughout (no `device="cpu"`, no cuda-if-available fallback); coherence preserved
end-to-end, never reduced to a Pauli twirl. See [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md)
for the full forward spec, composite likelihood, Godambe bands, and §11 certification/black-box
interface.

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

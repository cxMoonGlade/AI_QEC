# Real XZZX d3 surface noise model — registration

> The white-box noise model on the real Google XZZX **d3** surface code, fit to real hardware syndrome
> data. The code is XZZX (8/8 mixed stabilizers), parsed from the real circuit.
>
> **Scope (decision brief 2026-06-15, D1).** d3 is the **white-box** rung: the dataset ships **nine
> standalone `d3_at_q*` patches** — `d3_at_q2_7, q4_5, q4_9, q6_3, q6_7, q6_11, q8_5, q8_9, q10_7` —
> each 9 data + 8 full-in XZZX stabilizers, no seam, fully observed = a clean single-window twin. The
> white-box is fit and reported across these nine patches (plural). Cross-window / seam composition is
> the **black-box** capability (validation rung d7, 49 windows + real seam) with d5 (4 patches) as the
> d3→d7 intermediate rung — out of scope for this registration.

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
`d3_at_q5_5/X/r15` sample_00 ([`surface_recover_RESULTS.md`](surface_recover_RESULTS.md), **legacy
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

**Runtime register = 9q data + per-stabilizer measurement instrument (D3).** The white-box object is a
CPTP map on the window's **9 data qubits**; the register the forward materialises is **9 qubits**
(`ρ_data`, `4^9 × 16 B = 4.2 MB`), NOT data+ancilla. Syndromes come from **per-stabilizer measurement
instruments**, not an explicit ancilla register: each internal stabilizer's local sub-circuit (ancilla
init |0> → CZ chain to its ≤4 data with the CZ noise mechanisms → ancilla measure with readout flip
`p = 0.005` → reset) is reduced by tracing out the ancilla to a quantum instrument `{Ẽ_s}` on the
stabilizer's data support; the within-window syndrome is read out by applying these instruments in
faithful circuit order on the shared 9q register. The full derivation, epistemic tags, and the three
caveats are in [`window_instrument_derivation.md`](window_instrument_derivation.md).

**The faithful explicit-ancilla circuit is the ORACLE, not the runtime object.** The full d3 faithful
register would be **17 qubits** (9 data + 8 ancilla) = `4^17 × 16 B = 275 GB` — infeasible on any single
GPU (`4^8 = 65536×` the 9q object), so it is never run whole. The oracle is the **same d3 patch run as a
progressive faithful sub-system** (9 data + 1 ancilla = 10q per stabilizer; 9 data + k≤4 ancilla ≤ 13q
for circuit-order sub-sets; the full 17q is established by decomposition, not run — see
[`window_instrument_derivation.md`](window_instrument_derivation.md) §5). d7 cross-window is deferred.
The already-drafted faithful `WindowChannel` (generic over window data + ancilla) is the oracle engine,
not the runtime representation.

**Equivalence status — PENDING (D5).** The 9q instrument is a DERIVATION + PREDICTION. The
per-stabilizer ancilla trace is exact **only** under perfect, leakage-free ancilla reset; the
**end-to-end equivalence** of the 9q instruments (in faithful circuit order) to the faithful d3
data+ancilla evolution (its 17q register, checked via the feasible ≤13q sub-systems) — for both the
internal syndrome distribution and the data-state evolution — is
a **(b) prediction, NOT yet numerically confirmed** against the oracle. The 9q representation is adopted
as the runtime object only on passing a pre-registered residual band (syndrome KL/TV + data trace
distance) against the oracle; otherwise the faithful circuit is kept, or the model falls back to the
ADR 0008 C1 composed architecture. Mainline code for the 9q instrument lands after the equivalence is
validated, through the commit-gate. GPU-only model compute throughout (no `device="cpu"`, no
cuda-if-available fallback); the approximation/scope is stated explicitly, never reduced to a Pauli
twirl.

## 4. Validation — real data, no synthetic ground truth

Held-out per-shot syndrome **NLL** (field-standard: nats/shot/window, paired bootstrap, one-sided) + the
**structure-residual** check (reproduce the measured detection / 2-body / 3-body), reported **per patch**
across the nine standalone d3 patches, plus identifiability (Fisher rank → identified vs aliased + a
per-mechanism alias band). There is no exact "recovery vs teacher" on real data; claims are
observation-fit + residual structure, with honest bands. (The equivalence of the 9q-instrument runtime
to the faithful oracle is a separate, pending check — see §3 and
[`window_instrument_derivation.md`](window_instrument_derivation.md) §5 — not part of this real-data
validation.)

## 5. Discipline

Real data; the 105Q d3 release has **no sample layer**, so train / held-out / escrow are gated by
**shot-slicing** (disjoint shot ranges), not sample ids; decoder-independent for the
structure read; shipped `decoding_results/` priors are evaluator/baseline-only, never learner input.
GPU; scripted-execution. Plain reporting.

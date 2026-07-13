# White-box model — the window-channel field (overview + plan)

> **Historical research-line router (audited 2026-07-13).** This document describes the earlier
> window-field program and still contains retired paths/stage language. It is not the binding
> current simulator status and does not establish that a real-hardware coherent field was recovered.
> Use [`../SIMULATOR.md`](../SIMULATOR.md), [`../METRICS.md`](../METRICS.md),
> [`../../CONTEXT.md`](../../CONTEXT.md), and ADRs 0008–0011 for current claim boundaries.

> The white-box noise model on the **real Google Willow XZZX surface code**: a calibrated,
> coherence-preserving **CPTP window-channel field**, recovered from real hardware syndrome data.
> This folder holds the white-box docs; the CF-WR composition/seam theory and the `ξ̂` investigation
> stay in [`../cf_wr/`](../cf_wr/). The historical `plan3.md` / `TWIN.md` links formerly shown
> here no longer exist; the current binding object contract is [`../SIMULATOR.md`](../SIMULATOR.md).
>
> **Scale / execution structure (D1):** the active order is **d3 → d7 → d5**. The white-box is a
> **2×2 (4 data) faithful window** at every distance; ancilla cannot be eliminated because noise lives
> on the data⊗ancilla entangled state before measurement. **Measured register: 4 data + 2 full-in
> ancilla = 6q at d3 (≤6q across all scales, never 8q — (a)-exact, `outputs/covering_2x2.py`).** The
> **black-box GNN composes overlapping 2×2 windows via cross-window data-consistency over shared data
> (overlap ≤4) + the long-range/cross-window correlations (residual budget)** from d3 onward — **no
> seam-only stabilizers at the 2×2 scale** (every stabilizer is full-in ≥1 window — d3 8/8, d5 24/24,
> d7 48/48; (a)-exact, `outputs/covering_2x2.py`). The d=3 rung runs both the per-window white-box fit
> (per-window identifiability ceiling = 2 syndrome bits/window (d3)) and the first black-box
> composition; **d=7** validates composition at scale (49 windows + real seam); **d=5** (4 patches) is
> the post-d7 intermediate-scale validation / sanity rung. Each scale fits its white-box from its
> **own** data — no cross-scale parameter transfer (D2). **Current active scope (2026-06-15): the
> d3 white-box + black-box composition (step-3/4); d7 seam extension is trigger-gated, not dropped.**

## What it is (model type)

A **white-box, physically-parameterised, locally-exact, coherence-preserving generative noise model**
of the device — fit to passive syndrome observations by Born-rule maximum likelihood on the
**syndrome-conditioned multi-round detector-record likelihood** on the real device data (the R-round
record-conditioned forward; see [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) §2.0);
structured as a
tied **field of local CPTP window-channel factors** over a circuit-derived covering of **2×2 (4 data)
faithful windows** (4 data + 2 full-in ancilla = 6q at d3; ≤6q across all scales, never 8q — measured,
`outputs/covering_2x2.py`); **partially identifiable** (recovered up to the observational alias class,
with honest bands; per-window identifiability ceiling = 2 syndrome bits/window at d3). It is a
**coherent generalisation of the DEM** (DEM = the diagonal-PTM / Pauli special case), reached by the
**inverse** problem (data → model), unlike forward simulators or decoders. With `do()` (deferred) it
becomes a **structural causal model** of the error mechanisms.

## Documents (this folder)

| Doc | Role |
|---|---|
| [`window_covering_architecture.md`](window_covering_architecture.md) | design spine — the window covering + 1+1 (white-box recover + black-box GNN) |
| [`window_covering_RESULTS.md`](window_covering_RESULTS.md) | **step-1 evidence** — circuit-derived covering on real d7 (VERDICT PASS) + 20/20 cross-check |
| [`window_channel_spec.md`](window_channel_spec.md) | **step-2 build spec** — `WindowChannel` (dictionary + object + tests; locked decisions + §10 interface contract) |
| [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) | **THE live d3 white-box recover design** — forward + composite likelihood + Godambe bands + §11 certification/black-box interface |
| [`stabilizer_tn_carrier_design.md`](stabilizer_tn_carrier_design.md) | **d5/d7 carrier scaling study, deferred** — Option B non-viable per Spike A; Option A the open candidate |
| [`surface_recover_registration.md`](surface_recover_registration.md) | the white-box recover registration (real XZZX) |
| [`surface_recover_RESULTS.md`](../_archive/surface_recover_RESULTS.md) | measured structure (device vs SI1000) the model must carry |

Related, in [`../cf_wr/`](../cf_wr/): `xihat_RESULTS.md` (the `ξ̂` gate — BANKED GO, real d3→d7),
`THEORY.md` + `P2/P3/P4` (CF-WR composition/seam theory), `registration.md`.

## The four corrections (load-bearing)

1. **Adjacency = circuit-derived, never geometric** — which data couple is fixed by the circuit's 2q
   gates + lightcone, captured by the DEM (the d7 NN-coincidence is proven, not assumed).
2. **Never collapse to Pauli** — the density matrix carries coherent non-Pauli/non-Clifford channels;
   collapsing to a Pauli rate = the DEM = the M4 failure mode. The model always *represents* coherence.
3. **Mechanism selection = identifiability-driven** — the full ≤2q catalog is an overcomplete
   dictionary; the identifiable subset is data-determined (Fisher rank), reported as identified vs
   aliased + band.
4. **Residual ≠ mechanism-correct** — two independent gaps (model-class fit vs identifiability/alias);
   report both axes; mechanism *separation* is scored only on a controlled teacher, never on real data.

## Locked decisions (step-2)

- **Composition = strict circuit gate-order** (window-local faithful noisy circuit, not abstract).
- **complex128 on GPU** (GPU-only for all model compute — no `device="cpu"`, no `cuda-if-available`
  fallback).
- **Dictionary = full 1q + full 2q (overcomplete); 3q ready-but-OFF** (residual-triggered).
- **Runtime forward (D3):** the runtime forward is the **syndrome-conditioned multi-round
  detector-record likelihood** on the 6q 2×2 window (4 data + 2 full-in ancilla = 6q at d3; ≤6q across
  all scales, never 8q — measured, `outputs/covering_2x2.py`) — from the real reset boundary, propagate
  `R = 90` rounds with the recorded ancilla outcomes (per round: noisy gates → project on the record →
  renormalize → reset; the single-round projector core called R times), accumulating `log P_θ(record)`
  in the log domain; fit by a **composite likelihood** over windows on the real non-unital
  `detection_events.b8`. The dense `WindowChannel` is the engine and correctness oracle. (The
  unconditional stationary `ρ_ss(θ)` is degenerate for the unital SI1000 prior — `rank(H)=1` — and is
  kept only as the negative control; the 9q data-register + per-stabilizer instrument approach was tried
  and retired.) See [`d3_whitebox_recover_design.md`](d3_whitebox_recover_design.md) for the full forward
  spec, composite likelihood, Godambe bands, and §11 certification/black-box interface.
- **GPU-only (HARD)** — all model compute (6q forward / instruments / gradients) on cuda; no
  `device="cpu"`, no `cuda-if-available` fallback.

## Build order + status

| Step | What | Status |
|---|---|---|
| 1 | covering schedule (circuit-derived) | **DONE** — VERDICT PASS, committed; 20/20 cross-check (d5/d7 × X/Z × 5 rounds) |
| 2 | faithful `WindowChannel` oracle engine (GPU) | **DONE (oracle drafted)** — GPU-only + register bound implemented and tested (Run A: 15 passed, 1 skipped); faithful oracle code drafted, **mainline commit deferred** (lands with step-3). The runtime forward is the **conditioned multi-round detector-record likelihood** on the 6q (d3; ≤6q all scales, never 8q — measured, `outputs/covering_2x2.py`) 2×2 window, fit by a **composite likelihood** on real `detection_events.b8`; `WindowChannel` is the engine/oracle. (The 9q data-register + per-stabilizer instrument approach was falsified and is retired.) |
| 3 | white-box recover on real XZZX — **d3 2×2 windows** (D1) | next — starts from the **conditioned multi-round detector-record root** (sub-component #0; the unconditional `ρ_ss(θ)` is degenerate for the unital prior — negative control); fit the 2×2 window channel (6q faithful, d3; per-window identifiability ceiling = 2 syndrome bits/window) to each d3 patch; each patch fit uses its own d3 data (D2); report held-out syndrome NLL + Fisher rank + alias band |
| 4 | black-box composition — **d3 first, then d7** (D1) | from d3: GNN composes overlapping 2×2 windows **via cross-window data-consistency over shared data (overlap ≤4) + long-range/cross-window correlations (residual budget)**; **no seam-only stabilizers** (every stabilizer is full-in ≥1 window — (a)-exact, `outputs/covering_2x2.py`); coherence-survival gate — CF-WR / Petz / GNN; d7 extends composition at scale; each rung uses its own data (D2); composes already-fitted window channels, does not import d3 params |
| 5 | intermediate-scale validation — **d5** (D1) | after d7; uses d5's own data (D2) as the post-d7 sanity / interpolation rung, not a prerequisite for entering d7 |

## Representation invariants

Source of truth = coherent **Kraus/Stinespring** (CPTP/non-Pauli/non-Clifford by construction).
**PTM/Choi = derived lenses**; **PTM off-diagonal mass = coherence budget = what the Pauli/DEM export
discards** (band-tracked). **Never diagonal-truncate the PTM in the model** (that is the forbidden
twirl); diagonal-truncation is only the downstream Pauli-decoder export.

## Lessons banked (memory)

- **Adversarial self-verification** — correct numbers ≠ correct method; cross-verify gate-input
  quantities with ≥2 independent methods + a positive control (broken checks must fail loudly).
- **GPU-only** — any `device="cpu"` in model compute → cuda immediately; bound the register (memory),
  never CPU-dodge; no `cuda if available else cpu` fallback.
- **Scripted-execution** + **theory-first** (predictions before every run).

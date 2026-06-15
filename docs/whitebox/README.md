# White-box model — the window-channel field (overview + plan)

> The white-box noise model on the **real Google Willow XZZX surface code**: a calibrated,
> coherence-preserving **CPTP window-channel field**, recovered from real hardware syndrome data.
> This folder holds the white-box docs; the CF-WR composition/seam theory and the `ξ̂` investigation
> stay in [`../cf_wr/`](../cf_wr/). Whole-project live front: [`../plan3.md`](../plan3.md). Binding
> object contract: [`../TWIN.md`](../TWIN.md).
>
> **Scale structure (D1):** the white-box **validation rung is d=3** (9 standalone `d3_at_q*`
> patches — 9 data + 8 stabilizers, no seam, fully observed = clean single-window twins); **d=5**
> (4 patches) is the intermediate rung; black-box composition / seam is validated on **d=7**
> (49 windows + real seam). Each scale fits its white-box from its **own** data — no cross-scale
> parameter transfer (D2).

## What it is (model type)

A **white-box, physically-parameterised, locally-exact, coherence-preserving generative noise model**
of the device — fit to passive syndrome observations by Born-rule maximum likelihood; structured as a
tied **field of local CPTP window-channel factors** over a circuit-derived covering; **partially
identifiable** (recovered up to the observational alias class, with honest bands). It is a **coherent
generalisation of the DEM** (DEM = the diagonal-PTM / Pauli special case), reached by the **inverse**
problem (data → model), unlike forward simulators or decoders. With `do()` (deferred) it becomes a
**structural causal model** of the error mechanisms.

## Documents (this folder)

| Doc | Role |
|---|---|
| [`window_covering_architecture.md`](window_covering_architecture.md) | design spine — the window covering + 1+1 (white-box recover + black-box GNN) |
| [`window_covering_RESULTS.md`](window_covering_RESULTS.md) | **step-1 evidence** — circuit-derived covering on real d7 (VERDICT PASS) + 20/20 cross-check |
| [`window_channel_spec.md`](window_channel_spec.md) | **step-2 build spec** — `WindowChannel` (dictionary + object + tests; locked decisions + §10 interface contract) |
| [`window_instrument_derivation.md`](window_instrument_derivation.md) | **step-2 representation derivation** — the 9q data register + per-stabilizer measurement instrument (D3); equivalence proposition (PENDING) + caveats + oracle-validation plan |
| [`surface_recover_registration.md`](surface_recover_registration.md) | the white-box recover registration (real XZZX) |
| [`surface_recover_RESULTS.md`](surface_recover_RESULTS.md) | measured structure (device vs SI1000) the model must carry |

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
- **Register representation (D3 redirect):** the runtime white-box object is a **9q data register**
  (`ρ_data`, `4^9 × 16 B = 4.2 MB`) + **per-stabilizer measurement instruments** (ancilla traced out
  analytically). The oracle is the **same d3 patch run as a progressive faithful sub-system** (9 data
  + 1 ancilla = 10q per stabilizer; 9 data + k≤4 ancilla ≤ 13q for circuit-order sub-sets); the full
  d3 faithful register (17q = `4^17 × 16 B ≈ 275 GB`, 65536× the 9q object) is never run whole — that
  cost is why the runtime cannot be the faithful register. (d7 cross-window, 13q = 1.07 GB / 256×, is
  deferred.) The 9q instrument's equivalence to the oracle is **PENDING numerical validation**
  (epistemic (b) prediction; see
  [`window_instrument_derivation.md`](window_instrument_derivation.md) for construction + caveats).
- **GPU-only (HARD)** — all model compute (9q forward / instruments / gradients) on cuda; no
  `device="cpu"`, no `cuda-if-available` fallback.

## Build order + status

| Step | What | Status |
|---|---|---|
| 1 | covering schedule (circuit-derived) | **DONE** — VERDICT PASS, committed; 20/20 cross-check (d5/d7 × X/Z × 5 rounds) |
| 2 | faithful `WindowChannel` oracle engine (GPU) | **DONE (oracle drafted)** — GPU-only + register bound implemented and tested (Run A: 15 passed, 1 skipped); faithful oracle code drafted, **mainline commit deferred** (lands with the 9q instrument). Redirect (D3): the runtime object is the **9q instrument**; the faithful circuit is the **oracle**, run on the **d3 patch as a progressive sub-system** (10q per stabilizer / ≤13q sub-sets; full 17q never run whole). Equivalence PENDING numerical validation |
| 3 | white-box recover on real XZZX — **d3-first** (D1) | next — fit the window channel to the 9 standalone d3 patches (9 data + 8 stabilizers, no seam, fully observed = clean window twins); each patch fit uses its own d3 data (D2); report held-out syndrome NLL + Fisher rank + alias band; then d5 intermediate rung |
| 4 | black-box composition / seam — **d7** (D1) | gated on step-3 d3/d5 recovery; coherence-survival gate — CF-WR / Petz / GNN; each d7 window fit uses d7's own data (D2); composes already-fitted window channels, does not import d3 params |

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

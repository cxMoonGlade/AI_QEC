# Window covering — RESULTS (architecture build step 1)

> Run 2026-06-14, real Google **Willow XZZX `d7_at_q6_7` / X / r90** (`QEC_TWIN_HW_DATA`).
> **Circuit-derived** covering (correction 1): adjacency, stabilizer supports, and the
> error-propagation lightcone are parsed from the real `circuit_ideal.stim` 2q gates + the
> SI1000 DEM — never from coordinate distance. Decoder-independent; the covering reads only the
> circuit + the noise model (DEM), **no observed syndrome shots** ⇒ held-out / escrow untouched
> by construction. Scripts (`outputs/`, gitignored): `window_covering.py` (the covering + scorecard),
> `dem_weight_probe.py` / `dem_weight_verify.py` / `inject_debug.py` (the weight-ceiling
> verification). Sidecar: `outputs/window_covering_results.json`.
> Registration / spec: [`window_covering_architecture.md`](window_covering_architecture.md),
> [`surface_recover_registration.md`](surface_recover_registration.md). VERDICT: **PASS**.
>
> **Superseded for the live architecture (2026-06-15):** this is the step-1 RESULTS for the original
> **3×3 (9-data) covering**. The white-box window is now **2×2 (4 data)** — see `outputs/covering_2x2.py`
> (per-window 6q; **0 seam-only stabilizers** at the 2×2 scale, refuting b5's ~8-seam 3×3 finding). The
> circuit-structure facts here (footprint equality, adjacency, the 20/20 cross-check) carry over; the
> 3×3-window-specific bands (e.g. b5 seam counts) are the 3×3 framing. Kept as the 3×3 step-1 audit record.

## 0. What this is

The covering schedule for the window-channel field on the real d7 patch: one 3×3-data window per
data qubit, built from the **share-a-stabilizer graph derived from the circuit's CZ gates** (not
geometry), proven complete for connected weight-≤t configurations, with the SI1000 DEM lightcone
measured as the long-range/GNN budget. This replaces the earlier geometry-proxy script
(`SUPP_DIST=1.5` data–measure distance), which gave the same numbers **by coincidence** (the real
d7 circuit is nearest-neighbour) but encoded the wrong method.

## 1. Method — everything from the parsed circuit

- **Roles** from the circuit, not coordinates: ancilla = qubits measured every round (`M`); data =
  qubits sweep-CX-initialised and measured once at the end. Coordinates are used **only** as
  identity labels, cross-checked for exact set-equality against `metadata.json`.
- **Stabilizer supports** = the data qubits each measure qubit is CZ-coupled to, accumulated over
  the 4 CZ layers × 90 rounds (deduped).
- **Adjacency** = share-a-stabilizer (two data qubits adjacent iff they co-occur in some support);
  **window** = the radius-⌊t/2⌋=1 ball = the 3×3 data block (≤9 data).
- **DEM lightcone** = each SI1000 DEM error's detector set projected to measure-qubit `(x,y)` (time
  collapsed); an error is *window-native* iff its implicated stabilizers lie inside one window's
  stabilizer set (full-in ∪ seam).

## 2. Scorecard (theory-first; a = exact/hard-assert, b = prediction-band, c = gate)

| ID | tag | predicted → measured | status | claim |
|---|---|---|---|---|
| a1 | exact | 101 = 48+49+4 → 101 = 48+49+4 | EXACT-OK | 48 measure / 49 data / 4 idle ancilla; sweep-init == data |
| a2 | exact | 0 → 0 | EXACT-OK | every CZ pair = 1 measure + 1 data |
| a3 | exact | equal → equal | EXACT-OK | circuit data/measure coords == metadata (exact) |
| a4 | exact | {2,4} → {2,4} | EXACT-OK | stabilizer support weights ∈ {2,4} |
| a5 | exact | 0 → 0 | EXACT-OK | 0 uncovered connected weight-≤3 (1/2/3-body) configs |
| a6 | exact | ≤9 → 9 | EXACT-OK | window size ≤ 9 (≤ backend wall) |
| a7 | exact | True → True | EXACT-OK | window(6,7) data == `d3_at_q6_7` data (exact) |
| b1 | band | equal → 156 vs 156 | PASS | circuit adjacency == geometry adjacency (NN coincidence) |
| b2w | band | {2:12,4:36} → {2:12,4:36} | PASS | 12 weight-2 boundary + 36 weight-4 bulk |
| b2d | band | 8 → 8 | PASS | interior share-a-stabilizer degree == 8 |
| b4 | band | 49 / ~25 → 49 / 25 | PASS | ~49 windows, ~25 size-9 interior |
| b5 | band | ~4 / ~8 → 4.8 / 9.6 | PASS | interior window ~4 full-in + ~8 seam stabilizers |
| b6 | band | 9 → 9 | PASS | all 9 shipped d3 centres match their d7 window |
| b3 | band | 0 → 0 | PASS | every DEM error spatially window-native (non-containable = long-range budget) |
| c1 | gate | PASS → PASS | PASS | complete ∧ fits-wall ∧ 0 non-containable |

**15 claims, 0 findings (band misses), VERDICT = PASS.** Window-size distribution `{4:4, 6:20, 9:25}`
(4 corner / 20 edge / 25 interior windows); connected configs `{1:49, 2:156, 3:624}`.

## 3. Findings worth recording

1. **The covering interior windows ARE the shipped d3 patches — verified, all nine.** The d7 window
   centred at every shipped d3-patch centre has data exactly equal to that standalone d3 patch's
   `data_qubit_coords` (9/9, including the boundary-adjacent `q2_7` / `q10_7`). The dataset therefore
   ships **nine real-hardware fully-observed window twins** (9 locations × 2 bases × round levels) —
   the clean recovery rung (3a) for step-3.
2. **The seam is load-bearing for recovery, not only for cross-boundary chains.** An interior d7
   window has only **~4.8 full-in** stabilizers (the inner weight-4 plaquettes) + ~9.6 seam
   stabilizers — far fewer clean checks than a standalone d3's 8. So the full-in observations are
   underdetermined for the window's mechanism dictionary; fully recovering even within-window
   mechanisms requires the seam (which couples neighbours). "full-in ≠ d3 boundary checks."
3. **The SI1000 DEM is heavily multi-body, but caps at detector-weight 4 and is fully window-native.**
   Raw detector-weight distribution `{1:1472, 2:21124, 3:14508, 4:42073}` — weight-4 is 53%, weight-2
   only 27%; a pairwise-only treatment would miss most of the structure. Yet **all 79177 error terms
   are window-native** (b3: 0 non-containable; max spatial diameter 3.162 ≤ window). The 3×3 covering
   captures the complete SI1000 lightcone. The SI1000 long-range/GNN budget is **0 terms**; real
   hardware long-range is bounded separately by `ξ̂ ≈ 0.7` ([`xihat_RESULTS.md`](../cf_wr/xihat_RESULTS.md)).

## 4. The detector-weight ceiling — triple-verified (max = 4, zero ≥ 5)

The claim "no DEM error flips ≥ 5 detectors" was confirmed by three independent methods, after a
methodological bug was caught and fixed:

| method | path | max detector-weight | weight ≥ 5 |
|---|---|---|---|
| M1 | `detector_error_model(decompose_errors=False)` hyperedge count (0 repeated-detector ⇒ XOR == union, no collapse) | 4 | 0 |
| M2 | `explain_detector_error_model_errors` — independent count + physical fault provenance (0 errors with no circuit fault) | 4 | 0 |
| M3 | from-scratch `*_ERROR(1.0)` injection into the noiseless circuit + detector sampling (no DEM) | 4 (data), 2 (ancilla) | 0 |

The shipped Google `correlated_matching_decoder_with_si1000_prior/error_model.dem` is bit-identical
to M1 (same distribution, same example), a fourth independent angle. **Physics:** a persistent data
Pauli flips one onset detector per affected stabilizer, so X/Z (≤2 anticommuting checks) → ≤2 and Y
(≤4 checks in the XZZX bulk) → ≤4; M2 traced a weight-4 example to the Y-component of a
`DEPOLARIZE2` fault on the CZ pair 5[1,7]–10[2,7]. **Methodological catch (recorded in
`inject_debug.py`):** `compile_detector_sampler` absorbs a deterministic Pauli *gate* into the
intended-circuit reference (footprint 0); fault injection must use a Pauli *error channel*
(`X_ERROR(1.0)`) — this will recur in the step-2/3 teacher / CPTP self-checks.

## 5. Mechanism slot inventory (input to step-2 / step-3)

FIELD overcomplete dictionary, canonical-home deduped: **1q = 49** (data), **2q = 156**
(circuit-adjacent pairs), **3q = 624** (connected triples; deferred-but-ready). This is the
hypothesis-space dimension that step-3's Fisher-rank identifiability analysis consumes. The DEM
weight ceiling (≤4 detectors, ≤2q faults) shows the SI1000 observable structure does **not** force
>2q mechanisms; 3q slots stay deferred until a real-data residual demands them.

## 6. Rigor audit

- **Exact (theorem/identity grade, hard-asserted, zero tolerance):** a1–a7 — role partition, CZ-pair
  structure, coord identity, support weights, multi-body completeness, window size, the (6,7)↔d3
  identity. a5 (completeness) is the covering theorem applied to the **circuit-derived** adjacency.
- **Prediction bands (measured, all PASS):** b1 (NN coincidence), b2 (degree / weight split), b4
  (window counts), b5 (stabilizer taxonomy), b6 (d3 cross-check), b3 (lightcone containment).
- **Measured gate input:** b3's non-containable count (0) is the c1 gate input and the long-range
  budget, not a free band. The detector-weight ceiling (4) is measured, triple-verified.
- **Honest scope:** all DEM statements are **SI1000-model-side** (≤2q faults → ≤4-detector
  footprints, fully window-native). Real-hardware crosstalk beyond SI1000 is **not** covered here;
  it is surfaced later by the recover residual + Fisher alias structure (correction 4) and bounded
  spatially by `ξ̂` — never assumed away.

## 7. Status & next

**Step-1 PASS.** The covering is circuit-derived, complete for connected weight-≤3, window ⟺
d3-patch verified, and the SI1000 lightcone is fully window-native with a 0-term long-range budget.
Cleared to **step-2 `WindowChannel`** (mainline; the overcomplete coherent non-Pauli/non-Clifford
mechanism dictionary + arity-general composition + `ρ_BC` + PTM coherence budget + CPTP self-checks),
which consumes the slot inventory (§5) and feeds step-3 single-window recover on the nine real d3
window twins (§3.1).

## 8. Cross-check — structural facts are distance/basis/rounds-invariant (20 sets)

To confirm the §2–§4 facts are not specific to d7/X/r90, the structural checks were swept over **20
sets = {d5_at_q6_5, d7_at_q6_7} × {X, Z} × {r10, r50, r90, r150, r250}**
(`outputs/covering_xcheck_sweep.py`, reusing the validated step-1 functions; sidecar
`covering_xcheck_sweep_results.json`). **20/20 PASS.** Invariant across all 20:

- **max DEM detector-weight = 4, zero weight ≥ 5** (the XZZX-bulk check-degree ceiling).
- **all noise generators ≤ 2q** — checked directly on the noisy circuit's noise instructions; the
  only ops present are `DEPOLARIZE1` (1q idle), `DEPOLARIZE2` (2q CZ), `M(p)` (measurement flip),
  `X_ERROR` (reset). No 3q+ generator at any distance/basis/round.
- **covering complete** (0 uncovered connected weight-≤t), **every DEM error window-native**
  (non-containable = 0), **support weights ∈ {2,4}**, **interior degree = 8**.

Distance-dependent counts (structure scales, facts hold): d5 = 54 qubits (25 data + 24 measure + 5
idle ancilla), d7 = 101 (49 + 48 + 4); 3×3 windows (size ≤ 9) at both. Error-term counts scale with
rounds (d7 r10 8137 → r250 221257); X vs Z differ by 2 terms (a small basis asymmetry) with
identical structure. **Conclusion: the step-1 facts are structural (XZZX bulk + SI1000 ≤2q noise),
not instance-specific.**

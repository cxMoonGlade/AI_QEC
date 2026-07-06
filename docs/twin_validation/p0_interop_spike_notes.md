# P0 interop spike — results (2026-07-06) — GATE P0_INTEROP_ROUNDTRIP: PASS

**Claim established:** an emitted coupled-teacher record round-trips through the standard QEC stack —
`CoupledCycleTeacher.emit → {det,obs} → Spitz-pij DEM → stim.DetectorErrorModel → PyMatching decode`, with the ideal
Stim circuit exported in layout-identical detector order. Product-spec P0
(`conjunction_tool_product_spec_2026-07-06.md`) check satisfied. Evidence: committed script
`outputs/twin_validation/p0_interop_spike.py` (content_hash `9518f7d9…6db8c2e`, git HEAD `447abf4`, log
`outputs/twin_validation/logs/p0_interop_spike.log`, result json `outputs/twin_validation/p0_interop_spike_result.json`,
`python-exit=0`). Versions (baseline discipline): torch 2.12.0+cu130, stim 1.16.0, pymatching 2.4.0 (default
settings), RTX 5090.

## What landed (src, pending mainline-commit confirmation)
- `src/error_coupling_simulator/frontend/interop.py` (NEW): `records_to_dem` (marginals + Spitz Eq. 13 exact pairwise
  p_ij → matchable DEM: floored pair edges + exact odd-parity boundary residuals + DECLARED geometry L0 rule),
  `decode_records` (PyMatching adaptor, logical_index-safe), `insert_op_after_tick` (probability-1-error injection for
  independent wiring checks).
- `src/error_coupling_simulator/teachers/coupled_cycle.py`: `export_stim_circuit()` (ideal-geometry Stim export,
  layout-identity asserted vs the emitted det/obs surface; emit's C-3 payload untouched) + the
  `default_coupled_code_spec_d3_repz` fixture (d3 bit-flip rep code, M(R)=2R+3 — same enumeration cost as 5q).
- `tests/test_p0_interop.py` (12 tests, CPU-only) — incl. planted-parameter positive control sized to falsify the
  exact boundary identity vs its first-order approximation (gap 1.44e-2 ≫ 4e-3 tol), and the injection wiring tests.
- `outputs/` (local): spike script + runner + artifacts per arm (`circuit_ideal.stim`, `detector_error_model.dem`,
  `detection_events.b8`, `obs_flips_actual/predicted.b8` — sha256s in the log/json).

## Pre-run adversarial review (3-lens un-led panel + per-finding adversarial verification): 11 confirmed, all fixed
The load-bearing catch — **the v1 armB L0 rule was wrong** (critical, 2/2 confirms): it attached L0 to all
`delta:z12:*` boundaries on the geometric argument "an in-round X on q2 fires delta:z12:round{r} and flips obs". The
geometry is true (P1b injection confirms the mapping) but **that fault class has probability 0 under slice-1 noise**
(no data-X mechanism: gamma_phi/zeta Z-diagonal record-dead, gamma_1 inert on |0…0⟩, gamma_up baseline 0), while the
actual dominant `delta:*:round1` boundary class is the **round-0 ancilla reset/readout flip (~1.49e-2, does NOT flip
obs; the layout has no round-0 anchor detector)**. v1 would have made MWPM predict a false logical on every isolated
delta:z12:round1 event → LER_dec > LER_raw → gate FAIL misrecorded as a physics finding. **Corrected rule:
L0 = {final:z12} only — the L0 rule is a reduction of the RECORD's fault mix, not of the code geometry.**
Other fixes: stim frame semantics (detector samples are relative to the noiseless-WITH-GATES reference ⇒ wiring
injection must use `X_ERROR(1.0)`, never a deterministic `X` gate — a plain gate never fires a detector);
`decode_records` logical_index parameterized (was hardcoded col 0); pij SE convention (iid shots) now DECLARED and
carried in the DEM diagnostics (anti-conservative for clustered emits, S-1/C-11; bound at P1); noiseless all-zero
check demoted to smoke (vacuous for all-Z fixtures); prereg constants corrected (readout_flip_base_p=1e-2,
reset 5e-3); planted-test tolerances tightened to be discriminating; the d3_repz record-dead declaration got a
run-time falsifier (P5).

## Registered predictions vs outcomes
| pred | class | registered | outcome |
|---|---|---|---|
| P1 | a | layout asserts + noiseless zero (smoke for all-Z) | PASS both arms |
| P1b | a | 6 injection cases → exact detector columns + obs | 6/6 exact PASS (incl. armA disconnection witness: obs=1, zero detectors) |
| P2 | b | armB MWPM beats predict-0 baseline, cluster-z ≥ 3 | **LER 0.01175 → 0.00065, improvement 0.01110 ± 0.00062, z = 18.0** PASS |
| P3 | b | armA vacuous decode: pred ≡ 0, LER_dec = LER_raw | PASS (0.01050 = 0.01050; wiring sanity only, not record evidence) |
| P5 | b | armB delta rates within ±20% of 2p̄(1−p̄)=0.0294 | rates 0.0326–0.0338, max dev 15.3% PASS (positive offset consistent with pooled Jensen inflation of the logit-modulated instrument — not yet separately bounded, P1 item) |
| P4 | c | ~0.27 s/manifest (b603a81 bench) | **1.14–1.26 s/manifest** at this config (R=4, 11 measurement keys) — 4.2–4.7× the bench; soft-warn recorded. The honest current cost number for envelope math: ~1.2 s per trajectory-manifest, VRAM peak 0.11 GiB |

## Declared reductions / caveats (carried with the artifact)
- The DEM is a **two-point edge-factorized reduction** (structurally blind to hyperedges — same caveat as
  `spitz_pij_exact`); the faithful coupled/non-Pauli content lives in `{det,obs}`, the DEM is the decoder-facing
  hand-off.
- **L0 attachment is a declared class-(c) geometry rule over the slice-1 fault mix**, not estimated from records;
  P1 (faithfulness table) bounds it.
- **pij SE convention = iid shots**, declared anti-conservative for clustered emits (cluster_size recorded in the DEM
  diagnostics); the decode z-gate itself used cluster-robust SEs.
- armB exercises interop + decode on **instrument noise only** (all-Z geometry ⇒ gamma_phi record-dead, P5-checked);
  **no coupling-visibility claim is made by P0** — the coupling-visible geometry (X-check-bearing fixture) is the P3
  killer-demo job.

## Next
1. **P1 faithfulness table** — mechanism × oracle × bound × d for the current mechanisms (incl. bounding the L0 rule
   and the clustered-SE deviation vs the exact record law).
2. **Residual ② d3-conjunction cost run** (own prereg, GPU go-ahead) — envelope-number validation; use the honest
   ~1.2 s/manifest figure above for the qubit-dense part of the estimate.
3. P3 killer demo geometry: a fixture whose source-coupled mechanism is record-ALIVE and decode-relevant
   (X-check-bearing, cf. the 5q x0 chain) — the P0 pipeline (export → records_to_dem → PyMatching) is reusable as-is.

Residual ① (full-Quiroz leakage question) was resolved the same day — see
`conjunction_ownership_duediligence_2026-07-06.md` §"Residual check ① RESOLVED" (no leakage anywhere in Quiroz's
model; qubits-only TLS extension; no QEC records; no released tool).

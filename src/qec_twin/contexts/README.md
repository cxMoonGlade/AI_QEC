# contexts — circuit/probe contexts + the probe-richness ladder

The calibration contexts `C_cal(r)`, `r = 0..4` (the probe-richness ladder), and
the probe definitions that induce them. **Probe diversity — not parameter-tying —
is the demonstrated cure for the observational alias quotient** (ADR 0005).

- `ladder.py` — the `C_cal(r)` ladder + held-out exotic (phase-sensitive) contexts
  and the H2 held-out sandwich eval (`eval:R4-k2`; no new rungs — the crosstalk
  probes ARE the existing r=2/r=4 levels).
- `probe_catalog.py`, `probe_contract.py`, `overlay_contract.py` — probe
  definitions and contracts.
- `seam_strip.py` — ADR 0008 C3 seam-test instrument (registration item 1, as
  adjudicated by SEAM-TEST PRE-RUN AMENDMENT 1): the DISJOINT two-window
  rep-code `SeamStrip` — windows share the seam DATA pair across the seam (one
  qubit each side), NO check is measured on it; extraction = per-window checks
  only; production windows (3, 4) → 7 data / 12 instrument qubits (2D−2
  accounting), envelope ≤ 13 enforced; frozen declared tiling `TILING_FAMILY`
  = `"two-window-v1"` (the carrier's `StripSpec.tiling` — one shared
  instrument). The H2 ladder + held-out seam evals reused at the strip data
  count, the D8 equal-treatment `ObservationTeacher` surface, and `oracle_law`
  (`forward/exact` primitives ONLY; evaluator-side, never a carrier input)
  returning a `SeamStripLaw` whose record layout is exactly the carrier's
  `split_strip_record` convention and whose `observations()` is the declared
  scored `StripObservations` family (amendment ruling 2).

**Boundary.** Defines the contexts the model calibrates and validates over.
Consumed by `calibration` and `audit`. Spec: `docs/TWIN.md`, ADR 0003.

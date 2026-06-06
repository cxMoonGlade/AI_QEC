# contexts — circuit/probe contexts + the probe-richness ladder

The calibration contexts `C_cal(r)`, `r = 0..4` (the probe-richness ladder), and
the probe definitions that induce them. **Probe diversity — not parameter-tying —
is the demonstrated cure for the observational alias quotient** (ADR 0009).

- `ladder.py` — the `C_cal(r)` ladder + held-out exotic (phase-sensitive) contexts.
- `probe_catalog.py`, `probe_contract.py`, `overlay_contract.py` — probe
  definitions and contracts.

**Boundary.** Defines the contexts the model calibrates and validates over.
Consumed by `calibration` and `audit`. Spec: `docs/TWIN.md`, ADR 0007.

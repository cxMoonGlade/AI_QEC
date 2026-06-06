# mechanisms — noise-mechanism definitions + controlled teachers

The catalog of physical noise mechanisms and the controlled teachers used as
counterfactual ground truth.

- `catalog.py` — mechanism-ID → CPTP / readout channel definitions (taxonomy in
  `docs/error_mechanisms.md`).
- `profiles.py` — mechanism weight / strength profiles.
- `teachers.py` — controlled teachers for the B-path (e.g. a coherent
  over-rotation rep-code teacher) whose true channels and true `do() → ΔLER` are
  KNOWN — the only counterfactual ground truth.

**Boundary.** Defines mechanisms/teachers; does not calibrate or intervene.
Channels are realized via `forward`. Spec: `docs/TWIN.md`.

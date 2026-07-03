# error_coupling_simulator

The standalone, independently-releasable **coupling-error QEC teacher simulator** — consolidating
code previously scattered across `qec_twin` (tracked) and `outputs/` (gitignored scratch) into one
package. Auto-discovered by setuptools (`packages.find where=["src"]`) ⇒ importable as
`import error_coupling_simulator`.

## Why this package exists
The simulator is the deliverable we intend to **release independently**. Keeping its code in one
cohesive package (rather than scattered across `qec_twin.forward` / `.mechanisms` / `.simulator` /
`.audit.certify` + gitignored `outputs/teacher_prereg`) gives it a clean boundary, a stable public
API, and a releasable unit. Migration plan + phase order: `docs/error_coupling_simulator_MIGRATION.md`.

## Boundary / disciplines (binding)
- **No physical ground truth.** A teacher = a noise model we SPECIFY; oracles (QuTiP / closed forms)
  are FORMAL bug-catchers, never "validated vs reality." Product = LER; metrics are instruments.
- **Isolation.** This is teacher/evaluator-side. The label-free learner path must NOT import it.
- **GPU-first** for model compute (no `cuda if available else cpu`); `NUMERICAL_ZERO = 1e-12` only
  for float floors.

## Layout (target — built PHASED; see MIGRATION.md)
- `source/` — Axis-2 memory-ful sources + the coherence-wedge observable. **[P1 — landed]**
- `oracles/` — independent QuTiP-derived channel primitives. **[P1 — in progress]**
- `carrier/` — forward propagation (channels, cptp, joint-Lindbladian, kernels, exact DM). [P2]
- `mechanisms/`, `teachers/` — mechanism primitives + the controlled teachers. [P3/P5]
- `frontend/` — CircuitIR / CodeSpec / compiler / schedule / carriers / emit (from `simulator/`). [P5]
- `certify/`, `decode/` — the cert/anchor seam + frozen decoder-facing bits. [P4]
- `quantum_bath/` — the P2 target: pseudomode-enlarged GKSL (extracted from the pilot scripts). [P6]

## Status
**MIGRATION IN PROGRESS.** Only `source/` (the homeless nm_* wedge machinery) is re-homed. The
`outputs/` scratch copies are the FROZEN legacy; this package is canonical going forward. Public API
not yet frozen — import submodules directly.

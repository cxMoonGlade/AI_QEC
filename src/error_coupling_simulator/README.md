# error_coupling_simulator

The standalone, independently-releasable **specified-noise QEC simulator**. It applies declared
coupling, leakage, and memoryful noise processes to a QEC circuit and emits the multi-time syndrome
record. Code previously scattered across `qec_twin` and local experiment scripts has been
consolidated behind this package boundary. It is auto-discovered by setuptools
(`packages.find where=["src"]`) and importable as `import error_coupling_simulator`.

## Why this package exists
The simulator is the deliverable we intend to **release independently**. Keeping its code in one
cohesive package (rather than scattered across `qec_twin.forward` / `.mechanisms` / `.simulator` /
`.audit.certify` + gitignored `outputs/teacher_prereg`) gives it a clean boundary, a stable public
API, and a releasable unit. Migration plan + phase order: `docs/error_coupling_simulator_MIGRATION.md`.

## Boundary / disciplines (binding)
- **No physical ground truth.** A noise process is a model we SPECIFY; oracles (QuTiP / closed forms)
  are FORMAL bug-catchers, never "validated vs reality." Product = the full record; LER and other
  metrics are instruments on it.
- **Isolation.** This is teacher/evaluator-side. The label-free learner path must NOT import it.
- **GPU-first** for model compute (no `cuda if available else cpu`); `NUMERICAL_ZERO = 1e-12` only
  for float floors.

## Layout

- `source/` — Axis-2 finite-RTN / 1/f-like sources and source-to-mechanism coupling.
- `carrier/` — exact DM, joint-Lindbladian channels, CUDA kernels, archived DM-PEPO, and the active
  single-wire 2D-PEPS carrier.
- `mechanisms/`, `noise_processes/` — mechanism primitives and controlled generative processes.
- `frontend/` — CircuitIR / CodeSpec / compiler / schedule / carrier execution / artifact emission.
- `certify/` — evaluator-only anchor and certification seam.
- `quantum_bath/` — feasibility-only pseudomode-enlarged GKSL research carrier; not the product
  mainline and not a passive-record quantum-memory certificate.

## Status
**Core consolidation landed; release boundary still in progress.** Source, carrier, mechanisms,
noise processes, frontend, certification, and the retained quantum-bath research slice now live in
this package; old `qec_twin` paths remain compatibility shims where still needed. The public API and
separate-distribution boundary are not yet frozen.

The scientific frontier is the full-`d x d` single-wire 2D-PEPS trajectory carrier. Its d3
state-level spike is implemented, but finite-truncation fidelity of the complete multi-round record
is still open. The doubled-wire DM-PEPO is archived, and d5/d7 distributional results remain
provisional. Binding status and claim boundaries live in `docs/SIMULATOR.md`, `CLAUDE.md`, and ADR
0011; this README must not be used to promote a carrier or a synthetic parameter set beyond them.

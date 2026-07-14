# Architecture

`error_coupling_simulator` is a GPU-first project targeting faithful simulation of QEC error mechanisms.
Binding spec: `docs/SIMULATOR.md`. Read an owning module's `README.md` when present; several
top-level packages do not yet have one. This map is documentation, not import structure. The
machine-readable service boundary is `docs/service_status.json`; the generated `docs/CODE_MAP.md`
reverse-classifies every installed Python module as a service owner or explicit support module and
renders the complete service flow.

## Module map (`src/error_coupling_simulator/`)

### Noise specification — what a noise process is built from

| module | role |
|---|---|
| `source/` | **CORE** Axis-2 **notion-2** classical stochastic record-memory: replayable finite-RTN timelines (including the finite-band 1/f approximation), `Theta(z_t)` mechanism-parameter fan-out, and matched-marginal controls. `PhaseBurstSource` and `TemporalStormSPPSource` are separately catalogued RESEARCH timeline primitives; they are not accepted by the turnkey `CoupledCycleNoiseProcess`. This is not the separate `quantum_bath/` research surface and carries no CP-divisibility claim. |
| `mechanisms/` | mechanism primitives + `catalog` + `seam_teachers`; the non-Pauli families **leakage / drift / crosstalk / burst** (see `docs/error_mechanisms.md`) |
| `noise_processes/` | controlled **generative noise processes** (`coupled_cycle`), with evaluator-only truth |
| `quantum_bath/` | feasibility-only pseudomode-enlarged GKSL research carrier; formal bug-catcher, not the product mainline |

### Carrier — the forward engine (`carrier/`)

| module | role |
|---|---|
| `carrier/` (top) | Axis-1 `joint_lindbladian` assembler + `cptp_channel` (the CPTP Stinespring channel object) + `channels` |
| `carrier/exact/` | density-matrix backend — **⚠ FEASIBILITY-ONLY** (roughly 15 qubits by memory; current qutrit d3 oracle is 9 sites at ~5.77 GiB) — the **certification ORACLE** (`qutrit_dm`, `circuit_sim`) |
| `carrier/kernels/` | three scoped native families: exact-qubit fused Kraus support (`accel.py`), generic dense-qudit MCWF ops, and fused-d3 within-cycle trajectory ops. A directory-level “fused owns all kernels” claim is incorrect. |
| `carrier/peps/` | **ACTIVE** — the full-`d×d` 2D-PEPS trajectory carrier + FET truncation frontier (ADR 0011) |
| `carrier/pepo/` | **CLOSED** — the doubled-wire DM-PEPO carrier |

### Product + certification

| module | role |
|---|---|
| `frontend/` | CircuitIR / CodeSpec / compiler / Axis-1 schedule / Stim execution → `Simulator.run(...)`; exact small-N Axis-1 joint-L state/record execution; generic dense-qudit MCWF plus workload adapters; and shipped restricted Axis-1 1D MCWF/MPS and QT/MPS verification executors. Those MPS paths are finite-step/fail-closed, not production-scalable or universal full-record backends. The default Stim artifact bundle contains `.stim`, raw `.dem`, actual `.b8`, summaries, and a manifest; external PyMatching prediction artifacts are opt-in and every artifact has a fail-closed `representability` class. |
| `certify/` | score a noise process's records vs **INDEPENDENT** formal anchors (anti-circular) → an epistemic ledger with non-optional negative controls. Bayes-floor/headroom analysis is downstream legacy analysis, not a service here. |
| `numerics.py` | `NUMERICAL_ZERO` floor |

`src/qec_twin/` is a repository-local pointer to the pre-consolidation tree: outward import shims
and the still-used RAG (`qec_twin.rag`). The distributed package has no executable inward import
from it: PEPS scheduling, the experiment facade, and the frontend decoder are package-local.
PyMatching itself remains an explicit optional external dependency.

## Flow

The generated, entrypoint-checked complete diagram is in `docs/CODE_MAP.md`. At scientific level the
implemented routes remain distinct:

```text
Stim product:  CircuitIR/CodeSpec → Stim-expressible noise → canonical records + .stim/.dem/.b8
               (decoder-free default; optional external prediction artifacts)

Axis-1/2:      finite RTN / finite-band 1/f timeline → Theta(z_t) → CoupledCycleNoiseProcess
               → exact small-N Axis-1 joint-L carrier → canonical fixed-horizon record + controls
Reduced path:  caller SourceTimeline + explicit projection rules → reduced Stim-Pauli records
XZZX path:     external XZZX schedule + RunSpec → within-cycle host → fused d3 / 2D PEPS
Other paths:   reusable channel algebra → exact qubit/qutrit/ququart or generic qudit MCWF;
               quantum-bath suite → research distributions/nulls/witnesses (not RecordBatch)

Target only:   shared source → qutrit XZZX carrier → correctly folded full record → certification
               (OPEN / CODE_BLOCKED; not an integrated production flow)
```

## Carrier ladder / backend boundary (critical)

`carrier/exact` (density matrix) is `2^n×2^n` / `3^n×3^n` → **feasibility-only**; qubit and
qutrit ceilings differ sharply (current qutrit d3 is 9 sites at ~5.77 GiB). The target is the d5/d7
rotated surface code (49q / 97q). The installed intermediate route is the restricted Axis-1 1D
MCWF/MPS and QT/MPS execution under `frontend/`; it is useful verification execution but explicitly
does not claim production scaling or universal full-record completion. The old XZZX thin-strip
driver remains under `legacy/` and is not distributed. The full-code route is **2D PEPS full
`d×d`**. A 1D MPS can require `χ=2^{Θ(d)}` across a full-square cut in the
worst/project-estimate regime (amended ADR 0010/0011).
Record faithfulness is the **open truncation acceptance criterion** (gate on the full syndrome
record, never on the carrier bond alone); coherent-tail deletion and the deterministic WTG solver
replacement are suspended by the 2026-07-13 closure.
The channel object (`carrier/cptp_channel`) + the record contract are backend-agnostic, so the
swap is a backend replacement, not a rewrite. Detail: `docs/SIMULATOR.md` +
`carrier/peps/README.md`.

# Architecture

`error_coupling_simulator` is a GPU-first project targeting faithful simulation of QEC error mechanisms.
Binding spec: `docs/SIMULATOR.md`. Read an owning module's `README.md` when present; several
top-level packages do not yet have one. This map is documentation, not import structure; the
generated complete inventory is `docs/CODE_MAP.md`.

## Module map (`src/error_coupling_simulator/`)

### Noise specification — what a noise process is built from

| module | role |
|---|---|
| `source/` | Axis-2 **notion-2** classical multi-time sources (1/f bath, RTN) conditioning per-round rates + the coherence-wedge observable |
| `mechanisms/` | mechanism primitives + `catalog` + `seam_teachers`; the non-Pauli families **leakage / drift / crosstalk / burst** (see `docs/error_mechanisms.md`) |
| `noise_processes/` | controlled **generative noise processes** (`coupled_cycle`), with evaluator-only truth |
| `quantum_bath/` | feasibility-only pseudomode-enlarged GKSL research carrier; formal bug-catcher, not the product mainline |

### Carrier — the forward engine (`carrier/`)

| module | role |
|---|---|
| `carrier/` (top) | Axis-1 `joint_lindbladian` assembler + `cptp_channel` (the CPTP Stinespring channel object) + `channels` |
| `carrier/exact/` | density-matrix backend — **⚠ FEASIBILITY-ONLY** (roughly 15 qubits by memory; current qutrit d3 oracle is 9 sites at ~5.77 GiB) — the **certification ORACLE** (`qutrit_dm`, `circuit_sim`) |
| `carrier/kernels/` | fused CUDA/C++ kernels (loader `carrier/accel.py`, auto-routed on CUDA tensors) |
| `carrier/peps/` | **ACTIVE** — the full-`d×d` 2D-PEPS trajectory carrier + FET truncation frontier (ADR 0011) |
| `carrier/pepo/` | **CLOSED** — the doubled-wire DM-PEPO carrier |

### Product + certification

| module | role |
|---|---|
| `frontend/` | CircuitIR / CodeSpec / compiler / schedule / Stim execution → `Simulator.run(...)`; the default artifact bundle contains `.stim`, raw `.dem`, actual `.b8`, summaries, and a manifest, while the product record is the actual detector/observable `.b8` exposed as `RecordBatch`; external PyMatching prediction artifacts are opt-in and every artifact has a fail-closed `representability` class |
| `certify/` | score a noise process's records vs **INDEPENDENT** formal anchors (anti-circular) → an epistemic ledger with non-optional negative controls |
| `numerics.py` | `NUMERICAL_ZERO` floor |

`src/qec_twin/` is a repository-local pointer to the pre-consolidation tree: outward import shims
and the still-used RAG (`qec_twin.rag`). The distributed package has no executable inward import
from it: PEPS scheduling, the experiment facade, and the frontend decoder are package-local.
PyMatching itself remains an explicit optional external dependency.

## Flow

Current implementation has two disconnected scientific branches, plus a separate Stim product path:

```text
Stim product:  CircuitIR/CodeSpec → Stim-expressible noise → .stim/.dem/actual .b8
               (decoder-free default; optional external prediction artifacts)

Charter A:     RTN/1f source → partial dense-qubit lowering → small-N fixed-horizon record
Charter B:     static qutrit channel → legacy MPS/PEPS paths → internal raw syndrome bytes
               → package-local temporal-detector RecordBatch

Target only:   shared source → qutrit XZZX carrier → correctly folded full record → certification
               (OPEN / CODE_BLOCKED; not an integrated production flow)
```

## Carrier ladder / backend boundary (critical)

`carrier/exact` (density matrix) is `2^n×2^n` / `3^n×3^n` → **feasibility-only**; qubit and
qutrit ceilings differ sharply (current qutrit d3 is 9 sites at ~5.77 GiB). The target is the d5/d7
rotated surface code (49q / 97q), so the proposed scaling route is **MPS MCWF thin-strip**
(`quimb`; bounded χ only under fixed width/depth/noise/accuracy) → **2D PEPS full `d×d`**. A 1D
MPS can require `χ=2^{Θ(d)}` across a full-square cut in the worst/project-estimate regime
(ADR 0010/0011).
Record faithfulness is the **open truncation acceptance criterion** (gate on the full syndrome
record, never on the carrier bond alone); coherent-tail deletion and the deterministic WTG solver
replacement are suspended by the 2026-07-13 closure.
The channel object (`carrier/cptp_channel`) + the record contract are backend-agnostic, so the
swap is a backend replacement, not a rewrite. Detail: `docs/SIMULATOR.md` +
`carrier/peps/README.md`.

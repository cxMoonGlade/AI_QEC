# Architecture

`error_coupling_simulator` is a faithful, GPU-first simulator of QEC error mechanisms.
Binding spec: `docs/SIMULATOR.md`. **Every module under `src/error_coupling_simulator/`
carries a `README.md`** that bounds its scope; read it before adding code there. This map is
documentation, not import structure; the generated inventory is `docs/CODE_MAP.md`.

## Module map (`src/error_coupling_simulator/`)

### Noise specification — what a noise process is built from

| module | role |
|---|---|
| `source/` | Axis-2 **notion-2** classical multi-time sources (1/f bath, RTN) conditioning per-round rates + the coherence-wedge observable |
| `oracles/` | independent QuTiP-derived channel primitives — FORMAL bug-catchers, evaluator-only |
| `mechanisms/` | mechanism primitives + `catalog` + `seam_teachers`; the non-Pauli families **leakage / drift / crosstalk / burst** (see `docs/error_mechanisms.md`) |
| `teachers/` | the controlled **noise processes** (`coupled_cycle`) — rename to `noise_processes/` pending |

### Carrier — the forward engine (`carrier/`)

| module | role |
|---|---|
| `carrier/` (top) | Axis-1 `joint_lindbladian` assembler + `cptp_channel` (the CPTP Stinespring channel object) + `channels` |
| `carrier/exact/` | density-matrix backend — **⚠ FEASIBILITY-ONLY** (≤~15q) — the **certification ORACLE** (`qutrit_dm`, `circuit_sim`) |
| `carrier/kernels/` | fused CUDA/C++ kernels (loader `carrier/accel.py`, auto-routed on CUDA tensors) |
| `carrier/peps/` | **ACTIVE** — the full-`d×d` 2D-PEPS trajectory carrier + FET truncation frontier (ADR 0011) |
| `carrier/pepo/` | **CLOSED** — the doubled-wire DM-PEPO carrier |

### Product + certification

| module | role |
|---|---|
| `frontend/` | CircuitIR / CodeSpec / compiler / schedule / carriers / emit → `Simulator.run(...)`; emits `.stim` / `.dem` / `.b8` / manifest, each with a fail-closed `representability` class |
| `certify/` | score a noise process's records vs **INDEPENDENT** anchors (anti-circular) → an epistemic ledger with non-optional negative controls |
| `numerics.py` | `NUMERICAL_ZERO` floor |

`src/qec_twin/` is the pre-consolidation package: import shims + the still-used RAG
(`qec_twin.rag`) and R2 decoder (`qec_twin.hardware.m4_decode`), being pulled out of `src/`
into an archive with symlinks kept at the old import paths.

## Flow

```
noise process (mechanisms + Axis-2 source)
  → frontend    CircuitIR / CodeSpec → schedule → Simulator.run(...)
  → carrier     forward evolution: exact DM (oracle) → MPS thin-strip → 2D PEPS (full d×d)
  → record      per-round {detector bits, observable flips}  (.b8 / .dem)
  → certify     score vs INDEPENDENT anchors → epistemic ledger (evaluator-only)
```

## Carrier ladder / backend boundary (critical)

`carrier/exact` (density matrix) is `2^n×2^n` / `3^n×3^n` → **feasibility-only** (≤~15q; the
certification oracle). The target is the d5/d7 rotated surface code (49q / 97q), so the
forward scales through: **MPS MCWF thin-strip** (`quimb`; χ constant in d) → **2D PEPS full
`d×d`** — a 1D MPS is geometry-incompatible with the full square (`χ~2^{2d}`; ADR 0010/0011).
Record faithfulness is the **open truncation acceptance criterion** (gate on the full syndrome
record, never on the carrier bond alone); coherent-tail deletion and the deterministic WTG solver
replacement are suspended by the 2026-07-13 closure.
The channel object (`carrier/cptp_channel`) + the record contract are backend-agnostic, so the
swap is a backend replacement, not a rewrite. Detail: `docs/SIMULATOR.md` +
`carrier/peps/README.md`.

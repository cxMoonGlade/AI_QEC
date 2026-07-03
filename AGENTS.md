# Agent Notes (thin router)

**`CLAUDE.md` (repo root) is the authoritative, current guidance — read it first.** This file is a
deliberately thin router. It does **not** duplicate the main line, module map, reserved notation,
numerical-floor policy, or the metric / epistemic-status / theory-first / baseline / claim
disciplines — those all live in `CLAUDE.md` (kept current) and per-module `README.md`s, and would
drift the moment they were copied here.

> **Retired framing (do not reintroduce):** earlier versions of this file led with a finance↔QEC
> "calibration / risk system" analogy and a four-capabilities (recover / understand / manipulate /
> predict) main line. That framing is **retired** — ADR 0004 is decorative, not guiding (per
> `CLAUDE.md`, 2026-06-22). The live main line is the coupling-error QEC simulator / validated
> causal twin; see `CLAUDE.md` "Main line" + `docs/TWIN.md`.

## Where things live (router)

- **`CLAUDE.md`** — main line, commands, architecture, code conventions, key reference docs. Start here.
- **`CONTEXT.md`** — glossary + claim boundaries.
- **`docs/ARCHITECTURE.md`** + each module's **`README.md`** — full module map; read the owning
  module's README before adding code there (do not add flat modules under `src/qec_twin/`).
- **`docs/TWIN.md`** — binding twin spec (object contract, the four capabilities, reserved notation).
- **`docs/METRICS.md`** — metric ledger + the forced standard-metric ladder (dated values in
  `docs/metric_results.md`); **`docs/FAITHFULNESS_PROTOCOL.md`** — the anti-toy protocol.
- **`docs/plan3.md`** — live operative roadmap; `docs/_archive/PLAN.md` + `plan2.md` — historical.
- **`docs/adr/`** — durable decisions (spine 0001 → 0010).
- **`docs/.datasets/`** — reading notes for the four local Google QEC datasets (a mandatory
  derivation input before touching any hardware data).
- **`docs/papers/`** — local PDF cache of load-bearing references (check before web-searching).
- **`docs/teacher_learner.md`** — teacher / learner roles + the isolation contract.
- **`<memory>/MEMORY.md`** — the working-rules + project-state index (loaded each session).

## Operational gotcha not in CLAUDE.md — CUDA visibility

Wrappers (`/usr/bin/time`, Conda `--no-capture-output`) can make Torch report no CUDA/NVML even
though the GPU is healthy — do **not** treat CUDA-invisibility in one session as a real failure:
verify in-process (`time.perf_counter()` for benchmarks), and check whether a low-utilization
workload is launch-bound or CPU-preprocessing-bound (window/cache build, `.b8` load, Stim/DEM
parse) before concluding the GPU path is broken. Do **not** set `PYTHONPATH="$PWD/src"` (it
interferes with PyTorch CUDA/NVML discovery; the editable install + `pyproject` `pythonpath=["src"]`
already put `qec_twin` on the path).

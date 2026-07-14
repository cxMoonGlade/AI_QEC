# Agent Notes (thin router)

**`CLAUDE.md` (repo root) is the authoritative, current guidance — read it first,** and
**`docs/SIMULATOR.md` is the binding spec.** This file is a deliberately thin router. It does
**not** duplicate the main line, module map, notation, numerical-floor policy, or the metric /
epistemic-status / theory-first / faithfulness / baseline disciplines — those live in `CLAUDE.md`
(kept current), `docs/SIMULATOR.md`, and per-module `README.md`s, and would drift the moment they
were copied here.

## Where things live (router)

- **`docs/SIMULATOR.md`** — the **binding spec**: object contract, boundary, carrier ladder,
  disciplines. Read first.
- **`CLAUDE.md`** — main line, commands, architecture, code conventions, key reference docs.
- **`CONTEXT.md`** — glossary + claim boundaries.
- **`docs/ARCHITECTURE.md`** + each module's **`README.md`** — full module map; read the owning
  module's README before adding code there (do not add flat modules under `src/error_coupling_simulator/`).
- **`docs/METRICS.md`** — metric ledger + the forced standard-metric ladder;
  **`docs/FAITHFULNESS_PROTOCOL.md`** — the anti-toy protocol.
- **`docs/NUMERICAL_PROVENANCE.md`** — value-level paper/data/design provenance and the
  cross-paper-composite boundary; read before a claim-bearing run.
- **`docs/twin_validation/HANDOFF_simulator_scientific_formula_audit_2026-07-14.md`** — current
  sequential, read-only audit contract for every simulator formula and exact primary source.
- **`docs/nonpauli_teacher/`** — the live PEPS/FET carrier line + handoffs (current work).
- **`docs/adr/`** — simulator decisions 0008, amended 0010, and 0011; ADR 0009 is downstream
  inference/decoder research, not a simulator-product decision.
- **`docs/.datasets/`** — reading notes for the local Google QEC datasets (a mandatory derivation
  input before touching any hardware data).
- **`docs/papers/`** — local PDF cache of load-bearing references (+ the RAG index; check before web-searching).
- **`tests/CODEBOOK.md`** — the L0/L1/L2 test/coverage harness index (read before touching a test batch).
- **`<memory>/MEMORY.md`** — the working-rules + project-state index (loaded each session).

## Local reference tooling (the basis of the `theory-first` / `theory-fix` skills)

- **RAG:** `python -m qec_twin.rag.store --query "<q>"` (~2230 chunks over `docs/papers/reading_notes/`)
- **KG:** `python outputs/knowledge_graph/kg_query.py` · **Code map:** `docs/CODE_MAP.md`

## Operational gotcha not in CLAUDE.md — CUDA visibility

Wrappers (`/usr/bin/time`, Conda `--no-capture-output`) can make Torch report no CUDA/NVML even
though the GPU is healthy — do **not** treat CUDA-invisibility in one session as a real failure:
verify in-process (`time.perf_counter()` for benchmarks), and check whether a low-utilization
workload is launch-bound or CPU-preprocessing-bound (window/cache build, `.b8` load, Stim/DEM
parse) before concluding the GPU path is broken. Do **not** set `PYTHONPATH="$PWD/src"` (it
interferes with PyTorch CUDA/NVML discovery; the editable install + `pyproject` `pythonpath=["src"]`
already put `error_coupling_simulator` on the path).

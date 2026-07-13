# error_coupling_simulator

A **faithful, GPU-first simulator of QEC error mechanisms** — coupling, leakage, and other
non-Pauli / memory-ful noise. It takes a QEC circuit (a rotated surface code; **XZZX** is the
first target) plus a **specified noise process**, and produces the **multi-time syndrome
record** (per-round detector bits + logical-observable flips, emitted as Stim-compatible
`.b8` / `.dem`). It is a standalone, independently-releasable package.

The deliverable is the simulator; its product is the record (and the LER read off it under a
frozen decoder). Metrics are **instruments** on the record, never the object.

**Binding spec: [`docs/SIMULATOR.md`](docs/SIMULATOR.md)** — object contract, boundary,
carrier ladder, and disciplines. Read it first.

## What it models

- **Two noise axes.** *Axis-1* — within-substep joint-Lindbladian coupling (ZZ crosstalk,
  T1/T2, thermal, fSim residual, readout dephasing, leakage Hamiltonians). *Axis-2* —
  **notion-2** classical multi-time record memory (a shared classical source `z_t`/`ξ(t)`,
  1/f bath or RTN, modulating per-round rates → a beyond-Markov record signature).
- **Non-Pauli mechanisms** (span both axes): **leakage, drift, crosstalk, burst** — coherence
  / structure a Pauli-rate vector cannot carry, and **not DEM-reducible**.
- **No physical ground truth.** A noise process is a model we specify; the QuTiP / closed-form
  / exact-DM oracles are FORMAL bug-catchers, never a correspondence-to-reality claim.

## Current state

The live frontier is the **full-`d×d` 2D-PEPS trajectory carrier** and its **record-faithful
truncation** (ADR 0011). A 1D MPS is geometry-incompatible with the full surface code (`χ ~
2^{2d}`), so the full-code carrier is a single-wire 2D PEPS pure-state MCWF trajectory; the
open problem is replacing the unreliable FET/ALS truncator with the deterministic
Evenbly-2018 closed-loop gauge-fix (WTG). Working notes: `docs/nonpauli_teacher/`.

Every d5/d7 distributional claim is PROVISIONAL (no external oracle exists above the d3
exact-DM referee).

## Substrate

- **Forward carrier ladder** (`error_coupling_simulator.carrier`): exact density matrix
  (`carrier/exact`, ≤~15q — the certification oracle) → MPS MCWF thin-strip (`quimb`,
  χ constant in d) → **2D PEPS full `d×d`** (`carrier/peps`). The Axis-1 joint-Lindbladian
  assembler + CPTP channel object + fused CUDA kernels also live under `carrier/`.
- **Frontend** (`error_coupling_simulator.frontend`): `CodeSpec → CircuitIR`, imported Stim
  circuits, and hand-built circuits all feed one `Simulator.run(...)` surface emitting
  `.stim` / `.dem` / `.b8` / manifest artifacts; every artifact declares a `representability`
  class and fails closed.
- **Certification** (`error_coupling_simulator.certify`): scores a noise process's records
  against INDEPENDENT anchors (anti-circular) → an epistemic ledger with non-optional
  negative controls.

## Install

Python `>=3.10`. From the repository root, using the GPU `aiqec` environment:

```bash
conda run -n aiqec python -m pip install -e .
```

Do not set `PYTHONPATH="$PWD/src"`; use the editable install (`pyproject` `pythonpath=["src"]`
already puts `error_coupling_simulator` on the path).

## Use

```bash
conda run -n aiqec python -m pytest -q tests/                        # run the suite (ALWAYS scope to tests/)
python tests/harness/gate.py     tests/_support/<batch>_targets.json # L0+L1 coverage gate
python tests/harness/mutation.py tests/_support/<batch>_targets.json # L2 mutation gate
```

The simulator is driven through the library (`error_coupling_simulator.frontend.Simulator`
over the `carrier/` backends) and its `tests/`, which double as the executable spec — see
`tests/CODEBOOK.md` for the coverage harness.

## Docs

- [`docs/SIMULATOR.md`](docs/SIMULATOR.md) — **binding spec (read first)**.
- [`CLAUDE.md`](CLAUDE.md) — main line, commands, architecture, code conventions.
- [`CONTEXT.md`](CONTEXT.md) — glossary and claim boundaries.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module map; `docs/CODE_MAP.md` — generated inventory.
- [`docs/METRICS.md`](docs/METRICS.md) + [`docs/FAITHFULNESS_PROTOCOL.md`](docs/FAITHFULNESS_PROTOCOL.md) — metric ladder + anti-toy protocol.
- `docs/adr/` — live decisions (0008 → 0011).

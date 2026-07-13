# error_coupling_simulator

A **GPU-first project targeting faithful simulation of QEC error mechanisms** — coupling, leakage, and other
non-Pauli / memory-ful noise. It takes a QEC circuit (a rotated surface code; **XZZX** is the
first target) plus a **specified noise process**, and produces the **multi-time syndrome
record** (per-round detector bits + logical-observable flips, emitted as `.b8` shot data or an
equivalent joint law). A `.dem` is an optional decoder-facing reduction, not a record. The active
package is directly importable, but its independent-release boundary is not complete while legacy
`qec_twin` imports and entry points remain.

The deliverable is the simulator; its product is the record (and the LER read off it under a
frozen decoder). Metrics are **instruments** on the record, never the object.

**Binding spec: [`docs/SIMULATOR.md`](docs/SIMULATOR.md)** — object contract, boundary,
carrier ladder, and disciplines. Read it first.

## What it models

- **Two noise axes.** *Axis-1* — within-substep joint-Lindbladian coupling (ZZ crosstalk,
  T1/T2, thermal, fSim residual, readout dephasing, leakage Hamiltonians). *Axis-2* —
  **notion-2** classical multi-time record memory (a shared classical source `z_t`/`ξ(t)`,
  1/f bath or RTN, modulating per-round rates; the current evidence is for one frozen
  fixed-horizon record policy, not a generic causal process family).
- **Non-Pauli mechanisms** (span both axes): **leakage, drift, crosstalk, burst** — coherence
  / structure a fixed nonnegative Pauli-rate vector cannot carry; **not in general
  exactly/losslessly representable by a fixed nonnegative Pauli DEM**. Special reductions can
  exist for a declared channel/schedule/instrument.
- **No physical ground truth.** A noise process is a model we specify; the QuTiP / closed-form
  / exact-DM oracles are FORMAL bug-catchers, never a correspondence-to-reality claim.

## Current state

The live frontier is the **full-`d×d` 2D-PEPS trajectory carrier** and its **record-faithful
truncation** (ADR 0011). A 1D MPS can require `χ=2^{Θ(d)}` across a full-square cut in the
worst/project-estimate regime, so the full-code candidate is a single-wire 2D PEPS pure-state
MCWF trajectory; the
open problems are separate: diagnose the current FET/ALS implementation, and establish a
quantitative bridge from finite PEPS truncation to the complete multi-round record. A deterministic
WTG replacement and coherent-tail deletion are **not authorized** by the current literature closure.
Working notes: `docs/nonpauli_teacher/`.

The production bridge is also **open / `CODE_BLOCKED`**: the source-conditioned dense-qubit process
and the static data-qutrit XZZX process are disconnected implementation islands, not one validated
`RTN → leakage → record` object. See
`docs/twin_validation/production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md`.

Every d5/d7 distributional claim is PROVISIONAL (no external oracle exists above the d3
exact-DM referee).

## Substrate

- **Forward carrier ladder** (`error_coupling_simulator.carrier`): exact density matrix
  (`carrier/exact`; qubit memory ceiling is around 15 sites, while the current qutrit d3 oracle is
  9 sites at about 5.77 GiB) → MPS MCWF thin-strip (`quimb`; bounded χ is conditional on fixed
  width/depth/noise/accuracy) → **2D PEPS full `d×d`** (`carrier/peps`). The Axis-1 joint-Lindbladian
  assembler + CPTP channel object + fused CUDA kernels also live under `carrier/`.
- **Frontend** (`error_coupling_simulator.frontend`): `CodeSpec → CircuitIR`, imported Stim
  circuits, and hand-built circuits all feed one `Simulator.run(...)` surface emitting
  `.stim` / `.b8` / optional `.dem` / manifest artifacts; every artifact declares a `representability`
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

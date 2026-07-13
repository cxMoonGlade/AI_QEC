# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Main line

`error_coupling_simulator` builds **a faithful, GPU-first simulator of QEC error
mechanisms** — coupling, leakage, and other non-Pauli / memory-ful noise. It takes a QEC
circuit (rotated surface code / **XZZX**) plus a **specified noise process** and produces
the **multi-time syndrome RECORD** (`.b8` / `.dem`); metrics are instruments on the record,
never the object. **Binding spec: `docs/SIMULATOR.md`** (object contract, boundary, carrier
ladder, disciplines — read it first).

Active package: **`src/error_coupling_simulator/`** (importable directly). The live frontier
is the **full-`d×d` 2D-PEPS trajectory carrier** and its **record-faithful truncation**
(ADR 0011; the FET/ALS → Evenbly-WTG solver problem). Working line: `docs/nonpauli_teacher/`.
Two noise axes: **Axis-1** within-substep joint-Lindbladian coupling; **Axis-2** notion-2
classical multi-time record memory. Non-Pauli spans both: **leakage / drift / crosstalk /
burst**.

## Commands

```bash
conda run -n aiqec python -m pip install -e .                # install (editable)
conda run -n aiqec python -m pytest -q tests/               # full suite (ALWAYS scope to tests/)
conda run -n aiqec python -m pytest -q tests/test_<name>.py::test_fn  # single test
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available())"  # CUDA check
python tests/harness/gate.py     tests/_support/<batch>_targets.json  # L0+L1 coverage gate
python tests/harness/mutation.py tests/_support/<batch>_targets.json  # L2 mutation gate
```

Always scope pytest to `tests/` — bare `pytest` from the repo root recurses into `external/`
(gitignored vendored baselines, not part of the package). The editable install +
`pyproject.toml`'s `pythonpath=["src"]` already put `error_coupling_simulator` on the path;
do not set `PYTHONPATH`. The test suite + **`tests/CODEBOOK.md`** (the L0/L1/L2 coverage
harness) double as the executable spec — read the matching test first to see a capability
end-to-end.

**Local reference tooling** (RAG + KG are the basis of the `theory-first` / `theory-fix` skills):
- RAG (literature search): `python -m qec_twin.rag.store --query "<q>"` (~2230 chunks over `docs/papers/reading_notes/`)
- KG (knowledge graph): `python outputs/knowledge_graph/kg_query.py`
- Code map: `docs/CODE_MAP.md` (regenerate `python tools/gen_code_map.py`)

## Architecture

GPU-first; target workstation ≥ RTX 5090 CUDA (CPU-only results are not evidence of a
GPU-path failure). **Every module under `src/error_coupling_simulator/` has a `README.md`
bounding it**; full map in `docs/ARCHITECTURE.md` + `docs/CODE_MAP.md`.

```
src/error_coupling_simulator/
  source/       Axis-2 notion-2 classical multi-time sources (1/f bath, RTN) + wedge observable
  oracles/      independent QuTiP-derived channel primitives (FORMAL bug-catchers, evaluator-only)
  carrier/      forward propagation:
                joint_lindbladian (Axis-1 assembler) + cptp_channel + channels + kernels/ (CUDA)
                exact/     density matrix ⚠ feasibility-only ≤~15q — the CERTIFICATION ORACLE
                peps/      ACTIVE — the full-d×d 2D-PEPS carrier + FET truncation frontier
                pepo/      CLOSED — doubled-wire DM-PEPO
  mechanisms/   mechanism primitives + catalog + seam_teachers  (non-Pauli: leakage/drift/crosstalk/burst)
  teachers/     the controlled noise processes (coupled_cycle)  (→ noise_processes/, rename pending)
  frontend/     CircuitIR / CodeSpec / compiler / schedule / carriers / emit → Simulator.run(...)
  certify/      certification seam: score a noise process vs INDEPENDENT anchors (anti-circular)
  numerics.py   NUMERICAL_ZERO floor
```

`src/qec_twin/` holds pre-consolidation code as import shims plus the still-used RAG
(`qec_twin.rag`) and R2 decoder (`qec_twin.hardware.m4_decode`); it is being pulled out of
`src/` into an archive, with symlinks kept at the old import paths.

**Carrier ladder / backend boundary:** exact DM (≤~15q, the oracle) → MPS MCWF thin-strip
(`quimb`; χ constant in d) → **2D PEPS full `d×d`** (the active carrier — a 1D MPS is
geometry-incompatible for the full square, `χ~2^{2d}`). Truncation is **record-faithful**
(ADR 0011): gate on the syndrome record, never on the carrier bond / state fidelity. The
channel object stays backend-agnostic, so swapping the carrier is not a rewrite. Detail:
`docs/SIMULATOR.md` + `carrier/peps/README.md`.

**CUDA kernels:** `src/error_coupling_simulator/carrier/kernels/` (fused subsystem-Kraus
apply; loader `carrier/accel.py`, auto-routed on CUDA tensors, CPU fallback,
`QEC_TWIN_NO_KERNELS=1` disables; correctness oracle `tests/test_kernels_fused_kraus.py`).

### Isolation contract

The noise process's ground truth — source trajectory `z_t`, the channel field, per-substep
mechanism params — is **evaluator-only** (reachable via `.truth` / `CertReport.truth`) and
is **never** in the emitted record payload. `certify/` reads it to SCORE against independent
anchors; nothing downstream of the record may see it.

## Code conventions

- **Numerical floor:** use `error_coupling_simulator.numerics.NUMERICAL_ZERO == 1e-12` for
  floating floors/thresholds. Do not replace structural zeros (Pauli entries, bit values,
  integer indices, counts, exact algebraic identities).
- **Module placement:** new code → the module that owns it (each README defines its scope).
  Do not add flat modules under `src/error_coupling_simulator/`.
- **do() discipline:** a knob is a channel-level, parameterization-independent transform,
  scored by ΔLER under a frozen decoder — never an edit of a mechanism-native parameter.
- **Claim discipline:** controlled, small-scale, exact. Report honest bands; never assume
  identifiability that probe richness did not earn. Every d5/d7 distributional claim is
  PROVISIONAL until (impossibly) an external oracle exists.
- **Theory-first discipline:** the mathematics/physics derivation precedes every code
  experiment — the predicted outcome (direction, scaling, threshold) is written down before
  the run; experiments verify derived predictions, never explore-then-rationalize.
- **Metric discipline:** score every quantitative claim with a field-standard metric via
  `docs/METRICS.md`. Its ladder is forced — ledger metric → frontier-literature research →
  explicitly flagged project-defined; never a silent non-standard stand-in.
- **Baseline discipline:** `external/baselines/` holds vendored upstream repos in PRISTINE
  state. Never modify baseline code — minimal adaptors/helpers only, living in OUR tree.
  Declare each baseline's version/commit and settings alongside its numbers.
- **Epistemic-status discipline:** every pre-registration declares each quantitative item as
  **(a) exact** (theorem/identity/zero-tolerance — the only class allowed as a premise),
  **(b) prediction band** (a registered falsifiable bet; a miss is a finding), or
  **(c) heuristic gate/decision rule** (thresholds/conventions — go/no-go gating ONLY,
  never a premise). Undeclared ⇒ defaults to (c). Provisional conclusions are reportable and
  usable for go/no-go gating, but NOTHING may be built on them.
- **Scripted-execution discipline (HARD CONSTRAINT):** every code run — process control,
  audits, surgeries, baseline probes, benches, ad-hoc analysis — MUST be a committed script
  file carrying (a) precondition assertions, (b) printed evidence of effects, (c) flushed
  output, (d) an `if __name__ == "__main__"` guard whenever it touches multiprocessing. The
  only inline-shell exception is trivial read-only inspection that runs no project logic.
- **Faithfulness protocol (anti-toy, HARD CONSTRAINT):** every load-bearing faithfulness
  claim follows `docs/FAITHFULNESS_PROTOCOL.md` — (I) verify against ground truth INDEPENDENT
  of the implementation; (II) a constraint ledger of physical theorems + a falsifying test
  each, written BEFORE building; (III) declare + BOUND every simplification (unbounded ⇒
  STOP). Slow is fast — front-loaded rigor ≪ the 10× debug later.

## Notation (`docs/SIMULATOR.md` is the full contract)

`A` DEM parity map (never an assignment matrix); `E` the CPTP channel field;
`lambda_j = logit(p_j)` (never `ell_j`); `m` logical observable (never `o`); `z_t` / `ξ(t)`
the shared Axis-2 classical source trajectory; **notion-1/-2/-3** the memory taxonomy
(CP-div-breaking quantum / classical multi-time record / quantum-bath). A **noise process** =
a specified noise model that emits records (evaluator-only truth); a **DEM** = its
decoder-facing detector-error-model reduction, never the object.

## Key reference documents

- `docs/SIMULATOR.md` — **binding spec: object contract, boundary, carrier ladder,
  disciplines. READ FIRST.**
- `docs/METRICS.md` — metric ledger + the forced standard-metric ladder (governs every score).
- `docs/FAITHFULNESS_PROTOCOL.md` — the anti-toy faithfulness protocol.
- `docs/nonpauli_teacher/` — the live PEPS/FET carrier line + handoffs (current work).
- `docs/ARCHITECTURE.md` — full module map (+ per-module READMEs); `docs/CODE_MAP.md` —
  generated `src/` inventory.
- `docs/adr/` — live decisions: 0008 (scalable-carrier charter) → 0009 (Bayes-TN posterior
  spine) → 0010 (non-Pauli leakage MCWF-MPS carrier) → 0011 (record-faithful truncation on
  the 2D PEPS carrier).
- Local tooling: RAG (`python -m qec_twin.rag.store`), KG (`outputs/knowledge_graph/`),
  `docs/CODE_MAP.md`, `tests/CODEBOOK.md`.
- `CONTEXT.md` — glossary and claim boundaries; `AGENTS.md` — doc routing + working rules;
  `docs/error_coupling_simulator_MIGRATION.md` — how the package was consolidated.

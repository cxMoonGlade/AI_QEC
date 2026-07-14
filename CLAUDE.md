# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Main line

`error_coupling_simulator` builds toward **a faithful, GPU-first simulator of QEC error
mechanisms** — coupling, leakage, and other non-Pauli / memory-ful noise. It takes a QEC
circuit (rotated surface code / **XZZX**) plus a **specified noise process** and produces
the **multi-time syndrome RECORD** (`.b8` shot data / joint shot law); a `.dem` is an optional
decoder-facing reduction, not the record itself. Metrics are instruments on the record, never
the object. **Binding spec: `docs/SIMULATOR.md`** (object contract, boundary, carrier
ladder, disciplines — read it first).

Active package: **`src/error_coupling_simulator/`** (importable directly). The live frontier
is the **full-`d×d` 2D-PEPS trajectory carrier** and the still-open certification of its
record faithfulness (ADR 0011). The deterministic FET/ALS → WTG replacement and coherent-tail
deletion are suspended by the 2026-07-13 literature closure. Working line: `docs/nonpauli_teacher/`.
Two noise axes: **Axis-1** within-substep joint-Lindbladian coupling; **Axis-2** notion-2
classical multi-time record memory. Non-Pauli spans both: **leakage / drift / crosstalk /
burst**.

**Current production-bridge gate (2026-07-13): OPEN / `CODE_BLOCKED`.** The implemented
source-conditioned dense-qubit process (Charter A) and the static data-qutrit XZZX process
(Charter B) are two disconnected implementation islands; the old
`RTN → ten-field Θ → quarter-slice leakage → XZZX record` object does not exist. No recorded
published source closes either complete bridge, so neither supports preregistration or new
claim-bearing experiment code. Binding audit:
`docs/twin_validation/production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md`.

**Current live verification (2026-07-13): targeted backend checks pass; no monolithic simulator
acceptance result is claimed.** The fresh, non-cloned `ecs`
Conda environment is bootstrapped by `environment-ecs.yml`, exact-synced from `uv.lock`, and
checked against `core-environment-cu130.lock` by `scripts/verify_core_environment.py`: Python
3.12.13, Torch 2.12.0+cu130, QuTiP 5.3.0, qutip-cuQuantum 0.3.1, quimb 1.14.0, and
Hypothesis 6.156.1. CUDA-Q is intentionally
absent from `ecs`; the independent noiseless-Grover adapter remains in the retained `aiqec`
environment and must run in its own process. The old
eight-test qutip-cuQuantum read-only-`_dims` cluster is repaired
(`test_simulator_qutip_cuquantum_backend.py`: 4 passed; Axis-1 qutip-cuQuantum slice: 14 passed,
1 skipped). The former `KL=8.158934e-8 > 1e-8` item came from the retired HARDEN-H2
factorized-learner regression, not from an `error_coupling_simulator` carrier or record gate; those
learner tests are no longer part of the active test tree. The historical
CUDA-Q + fused same-process pair remains a known native teardown incompatibility (`2 passed`, then
`free(): invalid pointer`, exit 134), but it is no longer a canonical `ecs` execution topology.
After separation, the `ecs` CUDA-Q-file + fused-oracle collection exits 0 (`1 passed, 1 skipped`),
while the isolated `aiqec` CUDA-Q suite passes (`3 passed`).

The simulator P0 contract batch passes in `ecs` (`156 passed, 6 skipped`; skips are the explicit
PyMatching `[hw]` paths), and the same batch passes with `[hw]` in `aiqec` (`162 passed`).
The Stim frontend is record-first in the core environment: `decoder=None` is the default, so actual
detector/observable records and `RecordBatch` no longer require PyMatching; explicit
`decoder="pymatching"` preserves the frozen optional reduction. Record-only runs retain
non-graphlike DEM hyperedges instead of forcing PyMatching-oriented graphlike decomposition.
The focused Stim/frontend CPU slice passes in canonical `ecs` (`89 passed, 12 skipped`; every
skip is an explicit `[hw]` decoder test) and with `[hw]` in `aiqec` (`101 passed`).
The active PEPS packed-record path now folds raw round-major syndromes into temporal detectors;
Stim results, Axis-1 record samples, and PEPS expose the package-local `RecordBatch`. The exact-DM
anchor fails closed for unsupported `R>=2` joint-law requests. The active fused within-cycle
SV-MC path has the fail-closed precision policy
`optimization -> c64 / screening_only` and
`final|certification -> c128 / c128_candidate`; c128 remains a candidate until the owning
scientific gates pass. A c64 artifact never becomes evidence: any candidate conclusion requires a
separate frozen c128 replay. PEPS and MPS remain c128-only. WG channels, codestates, composition,
and CPTP checks are built in c128; only the already-checked complex execution tables are cast for a
c64 optimization run. The fused-SV ABI registry passes 100% statement/branch coverage and an
honestly-accounted 90.28% mutation gate (780 killed / 23 survived / 61 no-tests over 864); real
one-shot c64 and c128 CUDA ABI smokes both launch and exit cleanly. No scientific tolerance or FET
setting was changed.

## Commands

```bash
conda env create -f environment-ecs.yml                       # first creation only
conda run -n ecs python scripts/sync_core_environment.py      # locked deps + editable checkout
conda run -n ecs python scripts/configure_core_environment.py # bind CUDA/JIT provider
conda run -n ecs python scripts/verify_core_environment.py
conda run -n ecs python -m pytest -q tests/                   # repository regression; not scientific certification
conda run -n ecs python -m pytest -q tests/test_<name>.py::test_fn  # single test
conda run -n ecs python -c "import torch; print(torch.cuda.is_available())"  # CUDA check
conda run -n aiqec python -m pytest -q tests/test_simulator_cudaq_grover.py  # isolated CUDA-Q
python tests/harness/gate.py     tests/_support/<batch>_targets.json  # L0+L1 coverage gate
python tests/harness/mutation.py tests/_support/<batch>_targets.json  # L2 mutation gate
```

`environment-ecs.yml` locks the Conda bootstrap; `uv.lock` is the consumed transitive repository
lock; `core-environment-cu130.lock` is the human-auditable direct-pin compatibility contract.
The core lock includes active PEPS/test dependencies (`quimb`, `hypothesis`) but deliberately omits
the optional PyMatching `[hw]` extra and CUDA-Q; the default Stim record path needs neither.
The old `aiqec` environment is retained as the isolated CUDA-Q execution target and as rollback
evidence; it is not the canonical coupled-simulator environment. The ignored historical
`requirements.lock.txt` is not a restore input.
Use the sync wrapper, not bare `uv sync`: Conda does not set `VIRTUAL_ENV`, so a bare command can
silently target the stale repo-local `.venv` instead of `ecs`.

`pytest tests/` is a repository-wide engineering regression surface. It includes retained
decoder/data and migration seams, so its aggregate result is **not** a simulator-faithfulness or
scientific acceptance gate. Simulator claims are gated at the owning subsystem via the registered
targets in `tests/CODEBOOK.md`. `pyproject.toml` constrains default collection to `tests/` and excludes
`legacy/`, `external/`, `outputs/`, and local environments. The editable install +
`pyproject.toml`'s `pythonpath=["src"]` already put `error_coupling_simulator` on the path;
do not set `PYTHONPATH`. The test suite + **`tests/CODEBOOK.md`** (the L0/L1/L2 coverage
harness) double as the executable spec — read the matching test first to see a capability
end-to-end.

**Local reference tooling** (RAG + KG are the basis of the `theory-first` / `theory-fix` skills):
- RAG (literature search): `python -m qec_twin.rag.store --query "<q>"` (~2400 chunks over `docs/papers/reading_notes/`; rebuild after note changes)
- KG (knowledge graph): `python outputs/knowledge_graph/kg_query.py`
- Code map: `docs/CODE_MAP.md` (regenerate `python tools/gen_code_map.py`)

## Architecture

GPU-first; target workstation ≥ RTX 5090 CUDA (CPU-only results are not evidence of a
GPU-path failure). Read an owning module's `README.md` when present; not every top-level package
currently has one, so the complete inventory is `docs/ARCHITECTURE.md` + `docs/CODE_MAP.md`.

```
src/error_coupling_simulator/
  source/       Axis-2 notion-2 classical multi-time sources (1/f bath, RTN) + wedge observable
  carrier/      forward propagation:
                joint_lindbladian (Axis-1 assembler) + cptp_channel + channels + kernels/ (CUDA)
                exact/     dense DM ⚠ feasibility-only: ~15 qubits by memory; current qutrit d3=9 sites (~5.77 GiB)
                peps/      ACTIVE — the full-d×d 2D-PEPS carrier + FET truncation frontier
                pepo/      CLOSED — doubled-wire DM-PEPO
  mechanisms/   mechanism primitives + catalog + seam_teachers  (non-Pauli: leakage/drift/crosstalk/burst)
  noise_processes/  controlled generative processes (coupled_cycle; evaluator-only truth)
  quantum_bath/ feasibility-only pseudomode-enlarged GKSL research carrier
  frontend/     CircuitIR / CodeSpec / compiler / schedule / carriers / emit → Simulator.run(...)
  certify/      certification seam + independent formal anchors (anti-circular, evaluator-only)
  numerics.py   NUMERICAL_ZERO floor
```

`src/qec_twin/` points at the repository-local pre-consolidation tree: outward import shims plus
the still-used RAG (`qec_twin.rag`). The active package has no executable inward import from that
tree; PEPS scheduling, the experiment facade, and the R2 decoder wrapper are package-local. The
decoder imports optional
external PyMatching only when decoding is requested. Setuptools explicitly allowlists only
`error_coupling_simulator` and its subpackages; built wheel/source archives contain no `qec_twin`
package or legacy console entry point. The real release gate builds an sdist, rebuilds the wheel
from it, installs into an isolated target with `qec_twin` imports blocked, and runs the core record
smoke. Google circuit/schedule files and ququart Kraus data are explicit caller inputs, not package
code dependencies.

**Carrier ladder / backend boundary:** exact DM (qubits and qutrits have different ceilings; the
current qutrit d3 oracle is 9 sites) → MPS MCWF thin-strip (`quimb`; bounded χ is only a target at
fixed strip width/depth/noise regime/accuracy) → **2D PEPS full `d×d`** (the active carrier — a
1D MPS can require `χ=2^{Θ(d)}` across a square-code cut in the worst/project-estimate regime).
**Record faithfulness is the open
acceptance criterion**, not an established property (ADR 0011): gate on the full syndrome
record, never on the carrier bond / state fidelity alone. The
channel object stays backend-agnostic, so swapping the carrier is not a rewrite. Detail:
`docs/SIMULATOR.md` + `carrier/peps/README.md`.

**CUDA kernels:** `src/error_coupling_simulator/carrier/kernels/` contains two distinct families.
The c128 fused subsystem-Kraus apply is loaded through `carrier/accel.py`, auto-routed on CUDA
tensors, and retains its CPU/reference fallback. The GPU-only `sv_traj_d3_wc` fused within-cycle
SV-MC kernel is loaded through `carrier/kernels/sv_traj_d3_loader.py`, has separate c64/c128
compiled ABIs, and has no CPU compute fallback. `QEC_TWIN_NO_KERNELS=1` disables JIT loading; it
does not authorize a different scientific execution path.

### Isolation contract

The noise process's ground truth — source trajectory `z_t`, the channel field, per-substep
mechanism params — is **evaluator-only** (reachable via `.truth` / `CertReport.truth`) and
is **never** in the emitted record payload. `certify/` reads it to SCORE against independent
anchors; nothing downstream of the record may see it.

## Code conventions

- **Numerical floor:** use `error_coupling_simulator.numerics.NUMERICAL_ZERO == 1e-12` for
  floating floors/thresholds. Do not replace structural zeros (Pauli entries, bit values,
  integer indices, counts, exact algebraic identities).
- **Precision-purpose discipline:** only `FusedWithinCycleSampler` / `sv_traj_d3_wc` may use c64,
  and only for `run_purpose="optimization"` (`screening_only`). Final/certification uses c128 and
  remains `c128_candidate` until its owning gates pass. PEPS/MPS are c128-only. Construct and
  certify WG channels/codestates in c128, then cast only execution tables; never tune a tolerance
  or FET setting merely to admit c64.
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
- **Numerical-provenance discipline:** before a claim-bearing run, classify every value and
  freeze its exact source locator, units/scope, and transformation chain per
  `docs/NUMERICAL_PROVENANCE.md`. A paper equation grounds a form, not the chosen amplitude;
  cross-paper/device tuples are composite benchmarks, and project/numerical gates cannot support
  a hardware-realism claim.
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
  STOP); (IV) freeze value-level numerical provenance before the run. Slow is fast —
  front-loaded rigor ≪ the 10× debug later.

## Notation (`docs/SIMULATOR.md` is the full contract)

`A` DEM parity map (never an assignment matrix); `E` the CPTP channel field;
`lambda_j = logit(p_j)` (never `ell_j`); `m` logical observable (never `o`); `z_t` / `ξ(t)`
the shared Axis-2 classical source trajectory; **notion-1/-2/-3** are non-exclusive object labels
(reduced-map divisibility/backflow / observed-record memory-order / process-tensor memory carrier),
not a quantum-strength ladder. A **noise process** =
a specified noise model that emits records (evaluator-only truth); a **DEM** = its
decoder-facing detector-error-model reduction, never the object.

## Key reference documents

- `docs/SIMULATOR.md` — **binding spec: object contract, boundary, carrier ladder,
  disciplines. READ FIRST.**
- `docs/METRICS.md` — metric ledger + the forced standard-metric ladder (governs every score).
- `docs/FAITHFULNESS_PROTOCOL.md` — the anti-toy faithfulness protocol.
- `docs/NUMERICAL_PROVENANCE.md` — value-level source ledger and the one-source/two-source /
  cross-device compatibility rule.
- `docs/twin_validation/HANDOFF_literature_closure_and_status_2026-07-13.md` — current
  cross-session resume record; begin here after reading this file and the binding spec.
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

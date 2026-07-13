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

**Current live verification (2026-07-13): NOT full-suite green.**
`conda run -n aiqec python -m pytest -q tests/` produced `2560 passed, 169 skipped,
9 failed, 56 warnings`, then exited 139 after a segmentation fault. Eight failures are one
`qutip 5.3.0` / repo-local `qutip-cuquantum` read-only-`_dims` compatibility cluster; the ninth
is a reproducible H2 crosstalk gate miss (`KL=8.158934e-8 > 1e-8`). Treat the post-summary
native crash as separately unresolved, not automatically benign. Exact commands, reruns, and
claim implications are frozen in the binding audit's §5.4.

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

`src/qec_twin/` holds pre-consolidation code as import shims plus the still-used RAG
(`qec_twin.rag`) and R2 decoder (`qec_twin.hardware.m4_decode`); it is being pulled out of
`src/` into an archive, with symlinks kept at the old import paths.

**Carrier ladder / backend boundary:** exact DM (qubits and qutrits have different ceilings; the
current qutrit d3 oracle is 9 sites) → MPS MCWF thin-strip (`quimb`; bounded χ is only a target at
fixed strip width/depth/noise regime/accuracy) → **2D PEPS full `d×d`** (the active carrier — a
1D MPS can require `χ=2^{Θ(d)}` across a square-code cut in the worst/project-estimate regime).
**Record faithfulness is the open
acceptance criterion**, not an established property (ADR 0011): gate on the full syndrome
record, never on the carrier bond / state fidelity alone. The
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

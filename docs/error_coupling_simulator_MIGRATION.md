# MIGRATION PLAN — standalone `error_coupling_simulator` package

**Decision (user, 2026-07-03):** consolidate the coupling-error QEC simulator — code currently
scattered across `src/qec_twin/` (tracked) AND `outputs/` (gitignored scratch) — into a **single
standalone top-level package** `src/error_coupling_simulator/`, so it can be **released
independently**. Full consolidation, done **PHASED with tests green at every step**. The gitignored
`outputs/` scratch copies are **copied into the package (canonical) and then FROZEN** (left in place,
unmaintained; the package is the single source of truth going forward).

**Prime directive: 慢就是快 — no bugs.** Every move is verified before the next. The technique that
makes a big move safe is a **compatibility shim**: move the code to its new home, leave a thin
re-export at the OLD `qec_twin` path (`from error_coupling_simulator.X import *`), so every existing
importer (tests, other src) keeps working unchanged; verify the suite green; migrate importers to the
new path in a later pass; remove the shim last. No big-bang.

---

## Dependency boundary (measured 2026-07-03, `grep` over the seed set)

The simulator seed (`simulator/*`, `mechanisms/{coupled_teachers,source_coupling,source_process,
axis1_primitives,qutrit_teachers}`, `forward/joint_lindbladian`, `audit/certify/*`) depends on these
qec_twin core modules — this is what the standalone package must ABSORB:

- **forward/**: `channels`, `cptp_channel`, `exact/circuit_sim`, `exact/qutrit_dm`,
  `joint_lindbladian`, `kernels`
- **mechanisms/**: `axis1_primitives`, `qutrit_teachers`, `source_coupling`, `source_process`
  (+ `coupled_teachers`, `seam_teachers`, `catalog` as needed)
- **audit/certify/**: all of it — `core`, `facade`, `types`, `anchors/{closed_form,controls,
  dm_oracle,stim_clifford}`. **Clean: certify has NO back-edge to simulator/mechanisms (verified).**
- **hardware**: `m4_decode`, `b8_io` (decoder-facing)
- **numerics** (the `NUMERICAL_ZERO` floor)
- **simulator/**: all ~50 modules (193 internal imports — highly cohesive)

Plus the **homeless `outputs/` primitives** (no `src/` home today; only in gitignored scratch):
- `nm_source`, `nm_divisibility`, `nm_wedge` (the memory-ful source + RHP/BLP CP-divisibility +
  coherence-wedge — the P2 wedge observable). **All self-contained (no qec_twin import).**
- `qutip_single_qubit_channels`, `qutip_twoqubit_channels`, `qutip_cz_leakage_channel`
  (self-contained), `qutip_opensystem_channels` (**has 1 qec_twin import — resolve on move**),
  `qutip_teacher_source` (≈ `source_coupling` — CONSOLIDATE, do not triplicate).
- the pseudomode-embedding physics inside `coupled_pseudomode_pilot_v1_n2.py` + `quantum_bath_m2_*`
  (P2 quantum bath — must be EXTRACTED from the run scripts, not file-moved).

**Consolidation traps (do NOT create duplicates):** `mechanisms/source_process.py` already
productionizes `nm_source`; `mechanisms/source_coupling.py` already productionizes
`qutip_teacher_source`. In the package these become ONE `source/` layer — reconcile, don't copy a
third time.

**Packaging:** `pyproject.toml` uses `packages.find where=["src"]`, so `src/error_coupling_simulator/`
with an `__init__.py` is auto-discovered + importable as `error_coupling_simulator` immediately — no
pyproject change to be importable. A true separate DISTRIBUTABLE (own `pyproject`, `qec_twin` no
longer a dep) is the FINAL phase, only after the boundary is clean.

---

## Target skeleton

```
src/error_coupling_simulator/
  __init__.py            public API (release entry point)
  README.md              what this is + the release/isolation boundary
  numerics.py            <- qec_twin.numerics (leaf)
  source/                Axis-2 memory-ful sources + the wedge observable
    nonmarkovian.py      <- nm_source
    divisibility.py      <- nm_divisibility (RHP/BLP)
    wedge.py             <- nm_wedge
    process.py           <- mechanisms/source_process   (consolidate w/ nonmarkovian)
    coupling.py          <- mechanisms/source_coupling   (consolidate w/ teacher_source)
  oracles/               independent QuTiP-derived {H,c} primitives (evaluator-only)
    single_qubit.py two_qubit.py leakage.py opensystem.py teacher_source.py
  carrier/               forward propagation
    channels.py cptp_channel.py joint_lindbladian.py kernels/ exact/{circuit_sim,qutrit_dm}.py
  mechanisms/            axis1_primitives.py qutrit_teachers.py catalog.py seam_teachers.py
  teachers/
    coupled_cycle.py     <- mechanisms/coupled_teachers (CoupledCycleTeacher)
  frontend/              <- simulator/* (CircuitIR/CodeSpec/compiler/schedule/carriers/emit)
  certify/               <- audit/certify/* (record schema, Anchor/Control, scoring)
  decode/                <- hardware/{m4_decode,b8_io} (frozen decoder-facing bits)
  quantum_bath/          P2 target: pseudomode-enlarged GKSL (EXTRACT from pilot scripts)
```

---

## Phase order (leaves first; shim every move; suite green each step; H6 confirm each commit)

- **P1 — skeleton + homeless self-contained primitives (ZERO existing-src disruption).** Create the
  package + `numerics.py` + `source/{nonmarkovian,divisibility,wedge}` + `oracles/{single_qubit,
  two_qubit,leakage,opensystem}`. These are copied from scratch (frozen after), intra-cluster imports
  made package-relative, `opensystem`'s one qec_twin dep resolved. Verify: package imports clean; a
  fresh package-level GT smoke reproduces the scratch gtcheck numbers (independent-GT, not the scratch
  copy). No `src/qec_twin` file touched.
- **P2 — carrier leaves (numerics already in P1) + forward.** Move `forward/{channels,cptp_channel,
  exact/circuit_sim,exact/qutrit_dm,joint_lindbladian,kernels}` → `carrier/`, leave shims at the old
  `qec_twin.forward.*` paths. `tests/test_joint_lindbladian.py` + the gates must stay green via the
  shim.
- **P3 — mechanisms** (`axis1_primitives,qutrit_teachers,catalog,seam_teachers,source_process,
  source_coupling` → `source/`+`mechanisms/`+`oracles/teacher_source`; consolidate the source dupes),
  shims at old paths. `tests/test_source_*` green.
- **P4 — certify + decode** (`audit/certify/*` → `certify/`; `hardware/{m4_decode,b8_io}` → `decode/`),
  shims. `tests/test_certify` green.
- **P5 — frontend + teacher** (`simulator/*` → `frontend/`; `coupled_teachers` → `teachers/`), shims.
  `tests/test_simulator_*` + `tests/test_coupled_cycle_teacher` green.
- **P6 — quantum_bath extraction** (pull the pseudomode-embedding core out of the pilot run scripts
  into `quantum_bath/`; the run scripts stay in scratch, frozen).
- **P7 — flip + de-shim** (migrate all importers to the new package paths, remove the shims, run the
  FULL suite). Optional P8 — split to a separate distributable with its own `pyproject`.

**Verification per phase:** `python -m py_compile` → package import smoke → the affected `tests/`
subset → (at phase end) full `tests/` regression, via committed runners (pipefail + tee +
python-exit). Isolation held: the learner path (`calibration/`, `hardware/` learner side) must not
import the teacher/oracle package. GPU serial. Every `src/**` commit is H6-user-confirmed.

**Scratch policy:** `outputs/` copies are COPIED in, then FROZEN (not edited, not deleted this pass;
they are gitignored/unmaintained). `docs/CODE_MAP.md` + `docs/code_status.json` `_local_index` mark
them legacy once the package copy is canonical.

# MIGRATION PLAN — standalone `error_coupling_simulator` package

> **Current closure (2026-07-14):** this file preserves HOW the package was consolidated, but its
> old inward-dependency and learner/twin framing is superseded. The active distribution imports no
> `qec_twin` runtime module. Old `qec_twin` import paths remain only as outward repository shims;
> `qec_twin.rag` remains repository-only literature tooling. Neither is shipped. Binding framing:
> `docs/SIMULATOR.md`.

**Decision (user, 2026-07-03):** consolidate the coupling-error QEC simulator — code currently
scattered across `src/qec_twin/` (tracked) AND `outputs/` (gitignored scratch) — into a **single
standalone top-level package** `src/error_coupling_simulator/`, so it can be **released
independently**. Full consolidation, done **PHASED with tests green at every step**. Selected
gitignored `outputs/` *code primitives* were copied into the package and made canonical. Scratch
data/evidence files are not package assets: in particular, ququart transport now takes an explicit
caller-supplied Kraus `.npz` path.

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

Plus the **homeless `outputs/` primitives** (no `src/` home in the 2026-07-03 inventory; only in
gitignored scratch):
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

**ARCHITECTURE DECISION (user, 2026-07-03) — "the package owns the physics core."** A dependency
scan showed the moved forward substrate is SHARED, not simulator-exclusive:
`cptp_channel` (audit+calibration+contexts+hardware — it is literally the learner-side CPTP kernel),
`channels`/`catalog` (contexts=learner probe ladder), `exact.circuit_sim` (contexts+hardware),
`exact.qutrit_dm` (audit). The user ratified: **keep this shared forward PHYSICS CORE inside
`error_coupling_simulator`; `qec_twin` (the pre-consolidation package: calibration, contexts, audit,
hardware) depends on it via the shims.** So the package = **forward physics core + the coupling
simulator**; the remaining `qec_twin` tree is now a repository-only set of outward compatibility
shims plus retained RAG/R2 research surfaces, not a simulator runtime dependency or distribution
member.

**CURRENT SCOPE REFINEMENT (2026-07-14):** the R2 real-data ingestion and RAG trees remain
repo-local compatibility/research surfaces, not simulator runtime. The active frontend owns a
small package-local decoder adapter; record emission does not require a decoder, and external
PyMatching is imported only when explicitly requested. Decoder output and LER remain instruments,
never simulator-validity evidence. The evaluator-side certification seam, schedule/WG host,
experiment facade, record types, and decoder adapter are package-local. Retained old import paths
point outward to these owners; the owners never import those shims.

**Packaging:** `pyproject.toml` now uses an exact setuptools allowlist for
`error_coupling_simulator` and its subpackages. `MANIFEST.in` applies the same source-archive
allowlist even when an old `SOURCES.txt` exists. Wheel and sdist therefore publish neither
`qec_twin` nor its former console entry point. Release acceptance is the real-checkout
sdist → wheel → isolated-target install gate in `tests/test_distribution_boundary.py`, with
the repository root and `src/` removed from import resolution for package import and core smokes.
That gate also rejects leaked repository-only scratch assets; editable installation is not release
evidence. Core runtime requires Python ≥3.11 and declares SciPy directly.

**External-input / plugin boundary:** Google r01/r10 `.stim` + metadata files are explicit external
circuit/geometry/schedule inputs, not bundled package data and not a source of noise parameters.
The ququart adapter requires an explicit Kraus `.npz` input and has no repository-scratch default.
CUDA-Q remains a public `cudaq-grover` optional plugin, but is deliberately absent from canonical
`ecs`; it runs in the retained `aiqec` environment and a separate process from fused kernels.

---

## Historical target skeleton (2026-07-03)

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
- **P4 — certify ONLY** (`audit/certify/*` → `certify/`), shims. `decode/` DROPPED (see SCOPE
  REFINEMENT — the decoder + R2 hardware stay in qec_twin; gates import decode_dem cross-package).
  `tests/test_certify` green.

**HISTORICAL STATUS RECORD: P1 ✅ (6ddfcb5), P2 ✅ (9d6b70c/384ada4/6354a51), P3 ✅ (2cb8cdd), P4 ✅ (03662d2).
SCREENING ✅ — "keep the package lean" pass: removed the 7 unused scratch-origin modules
(source/nm_* + oracles/*, no tracked importer — re-home at P6) and split cptp_channel (the learner
recovery loop recover_channel/IC → `qec_twin/calibration/cptp_recovery.py`; shared DM ops +
StinespringChannel + PTM stay in carrier). P5 ✅ (P5a `1f64a69` teachers.py, P5b `87d1297`
frontend, P5c `286880b` coupled_cycle). At that checkpoint P6 + P7 were deferred; their current
disposition is recorded below. Handoff: `HANDOFF_refactor_2026-07-03.md`.**
- **P5 — frontend + teacher ✅ DONE.** `simulator/*` (45 files) → `frontend/` (pkgutil sys.modules-alias
  shim); `mechanisms/coupled_teachers` → `teachers/coupled_cycle.py`; `mechanisms/teachers.py` (B5 Kraus
  builders, physics-core) → `mechanisms/teachers.py` (fixed the last package→qec_twin back-edge in
  seam_teachers). `mechanisms/profiles.py` STAYS (learner-only — sole consumer is contexts/probe_catalog;
  screening rule d). All shims serve qec_twin. Verified: import-smoke same-object (all 3 phases) +
  targeted pytest (85 + 345 + 24 passed) + full-suite regression at EXACT baseline parity —
  1019 passed / 49 skipped / 6 failed both before and after, the 6 reds identical (5 pre-existing
  test_simulator_source_projection metadata_guard + 1 test_window_channel GPU-mem-contention flake,
  both unrelated to the refactor). Zero new failures; behaviorally a pure relocation.
- **P6 — quantum_bath extraction: LATER LANDED.** The bounded pseudomode-enlarged GKSL research
  carrier now lives under `error_coupling_simulator/quantum_bath`; unused scratch oracle/wedge
  modules remain local-only until an active consumer justifies them.
- **P7 — package flip / distribution de-shim: COMPLETE; repository shim deletion deferred.**
  Active simulator modules and public examples use `error_coupling_simulator`; no package runtime
  module imports `qec_twin`. The old repository paths remain as outward compatibility shims for
  retained consumers, but exact wheel/sdist allowlists exclude them. Removing every old shim and
  converting every retained repository test is repository cleanup, not a prerequisite for the
  independently installable simulator distribution.

**Verification per phase:** `python -m py_compile` → package import smoke → the affected `tests/`
subset → (at phase end) full `tests/` regression, via committed runners (pipefail + tee +
python-exit). Isolation held: the learner path (`calibration/`, `hardware/` learner side) must not
import the teacher/oracle package. GPU serial. Every `src/**` commit is H6-user-confirmed.

**Scratch policy:** selected reusable *code* copied from `outputs/` is canonical only in the package;
the old copy stays frozen and unmaintained. Scratch data, generated evidence, Google circuit inputs,
and ququart Kraus files are not copied into the distribution. `docs/CODE_MAP.md` +
`docs/code_status.json` `_local_index` mark retained local-only material explicitly.

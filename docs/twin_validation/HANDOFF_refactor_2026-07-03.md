# HANDOFF — error_coupling_simulator refactor (P5–P7), 2026-07-03

**Self-contained. Read this + `docs/error_coupling_simulator_MIGRATION.md` (the spec) + `CLAUDE.md`.**
The refactor consolidates the coupling-error QEC simulator into a standalone package
`src/error_coupling_simulator/`. P1–P4 are done + committed; this hands off P5–P7.

## 0. The decision that governs scope (user-ratified 2026-07-03)

**The package owns the forward PHYSICS CORE + the simulator; `qec_twin` (learner/twin app:
calibration, contexts, audit, hardware) depends on it via shims.** The shared forward substrate
(cptp_channel/channels/catalog/exact DM) is used by both sides and STAYS in the package (do NOT
revert). **The decoder + R2 real-data hardware do NOT move** (`hardware/m4_decode`, `b8_io`,
`dataset`, `m1_report`, `stim_artifacts` — evaluator/real-data side, "SIMULATOR ≠ decoder"); the
package imports `decode_dem` cross-package from `qec_twin.hardware.m4_decode` when a gate needs it.
Naming caveat: the package now owns the general physics core, so `error_coupling_simulator` is a
slightly narrow name — rename is cheap, deferred; don't block on it.

## 1. Where it is (all committed, branch Dev-F)

| phase | commit | what moved into `error_coupling_simulator/` |
|---|---|---|
| P1 | `6ddfcb5` | `source/{nonmarkovian,divisibility,wedge}` + `oracles/{single_qubit,two_qubit,leakage,opensystem}` (from gitignored `outputs/` scratch — COPY+freeze, not move) |
| P2 | `9d6b70c` `384ada4` `6354a51` | `carrier/{joint_lindbladian,cptp_channel,channels,accel,kernels/,exact/{circuit_sim,qutrit_dm}}` + `numerics.py` |
| P3 | `2cb8cdd` | `source/{process,coupling}` + `mechanisms/{catalog,axis1_primitives,qutrit_teachers,seam_teachers}` |
| P4 | `03662d2` | `certify/{core,types,facade,anchors/*}` |
| decision | `074abc1` | migration-doc: the ratified scope above |
| screening | `f34a5a5` | REMOVED 7 unused scratch modules (source/nm_* + oracles/* — no importer, re-home at P6); SPLIT cptp_channel (learner recovery loop → `qec_twin/calibration/cptp_recovery.py`; shared DM ops/StinespringChannel/PTM stay) |

**Lean package now** = `carrier/{accel,channels,cptp_channel,joint_lindbladian,exact/*,kernels/*}` +
`certify/{...}` + `mechanisms/{axis1_primitives,catalog,qutrit_teachers,seam_teachers}` + `numerics` +
`source/{coupling,process}`. **`qec_twin` is untouched except**: each moved module's old path is a thin
SHIM (re-export redirect), AND the screening added `qec_twin/calibration/cptp_recovery.py` (the learner
recovery loop split out of cptp_channel). No duplicated implementation in tracked src.

**SCREENING DISCIPLINE (apply to every P5+ candidate, ratified 2026-07-03):** before moving a module in,
grep who imports it. (a) simulator/frontend/teacher/gate-needed → move. (b) SHARED forward physics core
(cptp DM ops / channels / catalog / exact — used by learner too) → already in the package, STAYS (the
"package owns the physics core" decision). (c) learner-ONLY functions mixed into a shared file → SPLIT
them back to `qec_twin` (like cptp's recover_channel). (d) NO current simulator importer (unused/future
machinery) → do NOT pull it in. Keep the package to exactly what the simulator needs.

## 2. The proven recipe (every move followed it — no bugs)

1. `cp` the file(s) into the package (byte-identical; NEVER retype — zero transcription error).
2. Rewrite ONLY the import lines to package-relative (`..numerics`, `..carrier.channels`,
   `...carrier.exact.qutrit_dm` — count the dots by the module's depth). Cross-package deps on
   NOT-yet-moved qec_twin modules stay absolute (e.g. seam_teachers → `qec_twin.mechanisms.teachers`).
3. Replace the OLD path with a **SHIM**:
   - single module → `from error_coupling_simulator.X import mod as _m; globals().update({k:v for k,v
     in vars(_m).items() if not k.startswith("__")}); del _m` (mirrors the namespace incl. underscore
     names).
   - SUBPACKAGE (kernels, certify) → keep the old dir's `__init__.py` as a shim that
     `sys.modules`-aliases every submodule consumers import (see `qec_twin/forward/kernels/__init__.py`
     + `qec_twin/audit/certify/__init__.py` for the exact pattern); DELETE the moved submodule files.
4. VERIFY (GPU, **env bin on PATH** — see §3): `py_compile`; import smoke (new path AND shim give the
   SAME object, both `from X import sub` and `import X.sub` forms); run the affected `tests/`.
5. Update `docs/code_status.json` (add the new package entry; remove the now-orphaned qec_twin one if
   it became a shim-only pkg), regenerate `python tools/gen_code_map.py` (drift check must be clean),
   commit with the verification evidence in the message. **H6: user confirms each src commit** — but
   the user has been ratifying the refactor commits as it proceeds.

## 3. Environment (CRITICAL — cost us a diagnostic cycle)

The `aiqec` env is COMPLETE — nothing to install (ninja 1.13 / nvcc 13.1 / g++ 13.3 / torch
2.12+cu130 all present). But you MUST run with the env bin on PATH or torch's `cpp_extension` can't
find the `ninja` binary and the CUDA-kernel tests fail with a MISLEADING "Ninja is required":
`conda run -n aiqec python …` (the CLAUDE.md canonical way), or explicitly:
`wsl.exe -d ubuntu-f -- bash -c "cd /home/cx/Document/AI_QEC/AI_QEC && PATH=/home/cx/miniconda3/envs/aiqec/bin:/usr/local/cuda/bin:/usr/bin:/bin python -m pytest …"`.
`outputs/run_coupled_teacher_round_tests.sh` was fixed to export this PATH. wsl-trap reminders:
`$PATH`/`$?` pre-expand in the PowerShell→wsl outer bash — use explicit paths, and put multi-line
python in a script file (parens in inline `python -c` break the outer shell).

## 4. Remaining phases

- **P5 — frontend + teacher: ✅ DONE (P5a `1f64a69`, P5b `87d1297`, P5c `286880b`).** Executed exactly
  as the recipe prescribes.
  - **P5a** `mechanisms/teachers.py` (B5 Kraus/field builders — physics-core, used by seam_teachers AND
    the learner) → `error_coupling_simulator/mechanisms/teachers.py`; `seam_teachers` now imports the
    in-package `.teachers` (REMOVED the last package→qec_twin back-edge). 85 targeted tests green.
  - **P5b** `simulator/*` (45 files) → `frontend/`. One cp + import-line-scoped sed; a census guard
    proved the sed touched only import lines (256 `qec_twin.simulator` occurrences → 83 after, 0 on
    import lines; the 83 remaining are the `"qec_twin.simulator.*.v1"` schema STRING TAGS, preserved
    byte-exact). Old `qec_twin.simulator` is a **pkgutil shim** that `sys.modules`-aliases all 44
    frontend submodules + re-exports the public API. `qec_twin.hardware` (b8_io/m4_decode) stays
    absolute (decoder-facing, not moved). 345 tests green (only the 5 pre-existing source_projection
    reds remain — see §5). README.md moved with the code.
  - **P5c** `mechanisms/coupled_teachers.py` → `teachers/coupled_cycle.py` (+ `teachers/__init__`
    public API). Fully package-internal (`..mechanisms`/`..source`/`..frontend`). 24 tests green; the
    g4 gate imports cleanly through the shims.
  - **`mechanisms/profiles.py` STAYED** in qec_twin — learner-only (sole consumer: `contexts/probe_catalog`;
    no simulator/teacher/gate importer). Screening rule (d): do not pull learner-only code into the package.
  - Verification: import-smoke (new-path ↔ shim same-object, both `from X import sub` and `import X.sub`
    forms) + targeted pytest per phase + a full-suite regression at EXACT baseline parity (1019 passed /
    49 skipped / 6 failed both before and after; the 6 reds identical — 5 metadata_guard source_projection
    + 1 window_channel GPU-mem flake, both unrelated). CODE_MAP drift clean
    after each commit; `code_status.json` updated (frontend + teachers added, qec_twin/simulator entry
    removed, qec_twin/mechanisms → shim-layer).
- **P6 — quantum_bath extraction: DEFERRED (not done — intentional).** The pseudomode-embedding physics
  still lives inside the local-only pilot scripts (`outputs/coupled_pseudomode_pilot_v1_n2.py`,
  `outputs/quantum_bath_m2_dual_arm.py`), the future machine for the not-yet-built quantum-bath teacher.
  Extracting it now would pull unused code in (violates the "keep the package lean" SCREENING DISCIPLINE,
  rule d). Re-home it — with the P1-removed `nm_*`/`oracles` primitives — WHEN the quantum-bath teacher
  is built and wires them.
- **P7 — flip + de-shim + optional split: STANDING USER DECISION (not started).** Migrating all importers
  to the package paths + removing the shims is a whole-tree sweep; keep-shims vs de-shim is a deliberate
  call reserved for the user. NOTE the two pre-existing P2/P3 package→qec_twin back-edges still routed via
  shims (`carrier/channels.py` → `qec_twin.mechanisms.catalog`; `carrier/exact/circuit_sim.py` →
  `qec_twin.forward.accel`) — clean these in P7. Optional P8 — split to a separate distributable with its
  own `pyproject` (only once the qec_twin↔package boundary is clean; the package still imports
  `qec_twin.hardware` for the decoder).

## 5. Pointers / open items

- `docs/error_coupling_simulator_MIGRATION.md` — the spec (skeleton, phase order, the decision).
- `docs/CODE_MAP.md` (+ `tools/gen_code_map.py`, `docs/code_status.json`) — the current inventory;
  covers the whole `src/` tree. READ IT before re-exploring; regenerate after every move.
- **Pre-existing bug (NOT the refactor):** 5 `tests/test_simulator_source_projection.py` fail —
  `metadata_guard` rejects a `source_timeline` key in learner-visible CircuitIR metadata
  (`noise_spec.py:693`). Chip `task_cdfd94dc` is fixing it in a SEPARATE session. Ignore for the
  refactor (it fails identically without the refactor).
- The paused CoupledCycleTeacher mainline (G0-v2 / G6 re-registration) is on hold until the codebase
  is up (`HANDOFF_coupled_teacher_round_2026-07-03.md`); the Track A/B in-place prompts are VOID (the
  simulator code has moved). Resume the mainline in the NEW package layout after the refactor.
- Scratch verify scripts: `outputs/_verify_p{2_kernels,3,4}.py` (gitignored) — the import-smoke pattern
  to copy for P5.

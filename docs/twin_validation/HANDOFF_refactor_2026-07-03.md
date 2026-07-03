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

**`qec_twin` is untouched except each moved module's old path is now a thin SHIM** (re-export
redirect). No duplicated implementation in tracked src (P1's outputs/ copies are the only dup, and
that's gitignored frozen legacy).

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

- **P5 — frontend + teacher (the BIG one).** `simulator/*` (~50 modules, 193 internal imports — highly
  cohesive, move as ONE batch) → `frontend/`; `mechanisms/coupled_teachers` → `teachers/`; also move
  `mechanisms/teachers.py` (seam_teachers depends on it cross-package) + `mechanisms/profiles.py` if
  in scope. FIRST do a full dependency grounding like P2–P4 (grep each simulator module's
  `from qec_twin.*` imports + who imports `qec_twin.simulator.*`), and a shared-vs-exclusive check
  (simulator is the frontend — expect exclusive, but VERIFY no learner/contexts consumes it). Then one
  big cp + relative-import sweep (sed on the COPIES only, verify-grep after) + a subpackage shim that
  sys.modules-aliases the ~50 submodules. Verify with `test_simulator_*` (many) + the gates.
  ⚠ Watch: `simulator/*` imports the moved carrier/mechanisms/certify — those are now package-relative
  targets (`..carrier`, `..mechanisms`, `..certify`), NOT `qec_twin.*`.
- **P6 — quantum_bath extraction.** The pseudomode-embedding physics lives INSIDE run scripts
  (`outputs/coupled_pseudomode_pilot_v1_n2.py`, `outputs/quantum_bath_m2_dual_arm.py`) — EXTRACT the
  reusable core into `quantum_bath/`, don't file-move. Local-only scripts stay frozen.
- **P7 — flip + de-shim + optional split.** Migrate importers to the package paths, delete the shims,
  run the FULL suite, then (optional) split to a separate distributable with its own `pyproject`
  (only after the qec_twin↔package boundary is clean; the package will still `import qec_twin.hardware`
  for the decoder unless that's addressed).

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

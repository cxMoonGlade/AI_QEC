# HANDOFF — the quantum-bath record teacher (Option 3), 2026-07-03

> **HISTORICAL CLAIM FRAME SUPERSEDED, 2026-07-13.** The explicit-bath carrier may remain a
> simulation target, but reduced-map coherence revival/CP-indivisibility is not an unforgeable
> quantum-origin certificate and does not automatically reach `{det,obs}`. Any quantum-memory claim
> needs the declared process/instrument access and a separately closed bridge. Current authority:
> [`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md).

**Self-contained. Read this + `docs/twin_validation/nonmarkovian_memory_carrier_scope.md` (the BINDING
scope) + `CLAUDE.md` + the memory index.** This hands off the build of the **record-level quantum-bath
teacher** — the coupling simulator's declared FINAL TARGET — as a first-class package teacher alongside
`CoupledCycleTeacher`. Written at the close of the `error_coupling_simulator` P5 migration; the codebase
is now in the NEW package layout (see §2). The user chose this (Option 3) explicitly over packaging the
channel-level pilots as-is.

## 0. Mission + epistemic frame (BINDING — do not weaken in language or claims)

- **Goal.** Build a `QuantumBathTeacher` (pseudomode-enlarged GKSL) that **emits faithful surface-code
  `{det,obs}` records** driven by an explicit quantum memory (bath), conforming to the package's
  `ControlledTeacher` contract — the quantum analogue of the classical `CoupledCycleTeacher`. The
  classical teacher **IS AND CAN ONLY BE SCAFFOLDING**; the quantum GKSL bath is THE target, and the
  classical teacher becomes the quantum carrier's **control arm** (matched-marginal ablation).
- **Epistemic frame (user, 2026-07-03).** There is **NO ground truth** — everything is **simulation**.
  The teacher is a noise model we **specify** (we set ζ, γφ, the bath spectral density). QuTiP /
  independent-boson closed forms / `mcsolve` are **FORMAL oracles** (independent reference computations
  of the same specified model; they catch implementation bugs, never certify correspondence to nature).
  Gates certify (a) the simulator computes the specified enlarged-GKSL model correctly and (b) records
  carry that model's structure — NEVER "records = nature." **LER is the PRODUCT**; `1−F_e`/RHP/BLP/TV
  are internal **instruments**. Decoder/DEM/LER stay OUT of the validity chain.
- **Historical target framing, now narrowed.** Round correlation, reduced-map revival, and process-memory
  origin are different observables. Coherence revival / CP-indivisibility may be a useful declared-map
  diagnostic, but is not an unforgeable quantum-origin signature and does not transfer to the record without
  an instrument bridge. No generic “non-Markovian simulator” claim may ride on either carrier alone.

## 1. THE ENTRY STEP IS A PREREG, NOT CODE (theory-first, hard gate)

`nonmarkovian_memory_carrier_scope.md` §3 fixes the object + the 5 gates but **licenses no code**. The
first deliverable of this round is a **full theory-first prereg** (run the `theory-first` skill: literature
pass → close-read → registered falsifiable bands with epistemic classes), which MUST register:

1. **Wedge = coherence revival on the source-layer probe** (RHP/BLP > 0 with onset at the registered
   coupling point; Markovian control reads 0). Machinery: `nm_divisibility.rhp_measure`/`blp_measure` +
   the wedge harness (currently `outputs/teacher_prereg/nm_*.py` — see §4 shim/re-home).
2. **Motional-narrowing collapse control (hard):** the wedge → 0 in the fast-bath limit — the criterion
   that kills a mislabeled classical imitator.
3. **Classical-imitator null:** a matched-BCF classical-field twin must NOT reproduce the discriminator;
   the discriminator must live where **Prop IW-1** permits passive records to see it (records are EVEN in
   the commutator sector ⇒ expected home = outcome-resolved cross moments / conditional statistics, NOT
   first-order marginals — the observability calculus is a **registered derivation duty**, not an assumption).
4. **Independent oracles:** independent-boson closed form + JC/`mcsolve` — never the carrier's own path.
5. **Cost gate:** dense window⊗mode DM cost declared up front (dim `2^n · d_mode` per branch); the
   over-cap route (MCWF/MPS arm or window+seam) named BEFORE build, fail-closed otherwise.

Plus the §4 open questions: mode count / spectral bracket (Gao TLS; Dutta–Horn 1/f vs near-resonant TLS),
attachment point (data-idle T1 sub-share vs CZ-adjacent), and the **MANDATORY G0-quantum record-level
effect-size gate** (how much source-layer revival survives into `{det,obs}` at feasible N — the classical
round's G0 lesson binds: first-moment sizing under-sizes second-moment record statistics).

## 2. Current state (grounded 2026-07-03, POST-migration package layout)

**What EXISTS (reusable):**
- **The propagator is already built + G2-certified.** The enlarged (window⊗mode) dynamics is again GKSL,
  so it is propagated by `error_coupling_simulator.carrier.joint_lindbladian.assemble_substep_channel`
  with NO new engine. The new work = the **mode register + the interaction grounding**, not a propagator.
- **The embedding+oracle template:** coupled-pseudomode pilot v1 (`outputs/coupled_pseudomode_pilot_v1_n2.py`)
  — collective pure dephasing embedding GPU-certified vs the independent-boson closed form to 2.5e-8.
  Memory [[project-coupled-pseudomode-pilot-v1]]. **Read its scope caveats verbatim** (in its docstring):
  N=1 single Lorentzian = the OLD decoupled pseudomode, NOT the paper's dense-coupled contribution;
  Ŝ=σz (exactly-solvable independent-boson) sidesteps the non-commuting dynamics the construction is FOR;
  "exact CPTP GKSL" is exact only un-truncated (Fock n_max = a (c)-class simplification, measured not
  assumed); the oracle's independence is method-level WITHIN the Gaussian regime (telegraph-1/f is a
  shared blind spot); the |01⟩⟨10| DFS protection is a Δs=0 tautology. **These caveats must survive into
  the teacher's claim — do not launder them.**
- **The M1/M2 grounding:** `quantum_bath_m2_dual_arm.py` (1 qubit + 1 pseudomode vs matched-classical
  imitator; D_matched floors, KMS/unitality checks) + `quantum_bath_slot_prereg.md`. Memory
  [[project-quantum-bath-m1-m2]] (M2 v3 cleared; CGF probe → Branch B). The classical arm here is the
  seed of the teacher's **classical-imitator control**.
- **The record-teacher template + interface:** `error_coupling_simulator.teachers.coupled_cycle.CoupledCycleTeacher`
  is the shape to mirror. The certify contract is `error_coupling_simulator.certify.types`:
  - `ControlledTeacher` (Protocol): `sched` (parsed XZZX geometry), `truth` (evaluator-only params/Kraus),
    `emit(regime, *, m, N, seed) -> {det,obs,packed}`, `channels()` (per-CZ CPTP field).
  - `DMReplayable`: `dm_round_callbacks(device)` — the DM-oracle anchor replays the SAME mechanism on the
    density matrix (cross-construction check, not a check vs the engine's own oracle).
  - `CliffordSliceable`: `emit_clifford_slice(...)` — stim reproduces a Pauli slice of the geometry
    (implementation-independent wiring check).
  - Certify via `error_coupling_simulator.certify.certify_teacher`.
- **Control arms pattern:** `CoupledCycleTeacher.markovian_baseline()` / `.off_source()` — the quantum
  teacher's controls are the **classical-imitator** (matched-BCF classical field) + **motional-narrowing**
  + **off**.

**What is MISSING (the build):**
- No quantum-bath teacher class exists anywhere (verified: `grep -rn "class .*Bath.*Teacher"` = none).
- The pilots produce **channels/coherence/Choi at n=2, NOT records** (detector/observable/.b8 count ≈ 0).
- The hard core: **bridge the pseudomode bath dynamics to per-round record emission at surface-code
  scale.** The classical teacher does source `z_t` → Θ fan-out → per-round `Axis1PrimitiveParams` → dense
  emitter. The quantum version must carry the **bath state across rounds** (the memory is IN the enlarged
  register, not a classical parameter), which is exactly the "scalable-COUPLED error = open problem"
  ([[project-scalable-coupled-error-open-problem]]): the coupling-keeping carrier is the contribution AND
  the cost. The §2/§5 cost gate + over-cap route (MCWF/MPS or window+seam) decide feasibility.

## 3. The build target (what "结入 teacher" concretely means)

A `QuantumBathTeacher` (name TBD) that:
1. Builds the **enlarged register** window ⊗ (1..M pseudomodes) + the interaction `H_int` grounded from a
   declared spectral density (the prereg's bracket), and propagates it with the existing
   `assemble_substep_channel` — the reduced window dynamics breaks CP-divisibility.
2. Conforms to `ControlledTeacher` (+ ideally `DMReplayable` + `CliffordSliceable`): `sched`/`truth`/
   `emit`/`channels`, so `certify_teacher` scores it against the DM-oracle / stim-Clifford / closed-form
   anchors — the anti-circular certification the package already provides.
3. `emit()` produces surface-code `{det,obs}` records driven by the bath (the memory carried across rounds).
4. Provides the control arms: **classical-imitator** (matched-BCF classical field — the M2 dual-arm's
   classical arm, and/or the classical `CoupledCycleTeacher` at matched marginals = the natural G6 upgrade),
   **motional-narrowing**, **off**.
5. Passes the 5 registered gates (§1) + the record-level G0-quantum effect-size gate.

## 4. Staging — "先结入 teacher, 外面有 shim, 测试通过后 re-home" (user directive, mapped to reality)

The pilot SCRIPTS are self-contained, but the record-teacher's GATES consume the source-layer machinery
that P1-screening removed from the package (it had no consumer THEN; now this teacher IS the consumer):
- `outputs/teacher_prereg/nm_source.py` (memory-ful 1/f source), `nm_divisibility.py` (RHP/BLP
  CP-divisibility detector — the wedge gate G1), `nm_wedge.py` (coherence-envelope observable), + the
  qutip oracles (`qutip_*channels.py`, `qutip_opensystem_channels.py`) for independent certification.

**Staging:** (a) build the teacher in the package (`teachers/quantum_bath.py` or a `quantum_bath/`
subpackage); (b) reach the still-external `nm_*`/oracle machinery via a **temporary import shim** (a
package module that inserts `outputs/teacher_prereg` on `sys.path` and re-exports — clearly marked INTERIM,
because a tracked package importing gitignored `outputs/` is NOT self-contained/releasable); (c) get the
teacher + its gate suite GREEN; (d) THEN **re-home** `nm_*` + oracles + the pseudomode-embedding core into
the package (`quantum_bath/` + `source/` + `oracles/`) and delete the interim shim — this is the deferred
**MIGRATION P6** (`error_coupling_simulator_MIGRATION.md`; `code_status.json` `_local_index` marks these
FUTURE-P6). Update CODE_MAP + `code_status.json` at re-home.

## 5. Disciplines (standing; do not skip)

- **Theory-first:** the prereg (§1) precedes ALL code; predict-before-measure; a criterion changed after
  seeing data is unregisterable (amendment budget: one per gate, then STOP + finding). [[feedback-theory-first-and-sequencing]]
- **Faithfulness protocol** (`docs/FAITHFULNESS_PROTOCOL.md`): constraint ledger + INDEPENDENT ground-truth
  check + bounded-simplification list, by the builder, BEFORE "done"; then a from-scratch adversarial
  red-team. Every load-bearing quantity cross-verified ≥2 independent methods + positive control. The
  root cause of every toy = circular verification — the oracle must be independent of the engine.
  [[feedback-anti-toy-ground-truth-protocol]], [[feedback-prevent-toy-from-the-start]], [[feedback-toy-generators-audit]].
- **≥3 disjoint-ownership builders + un-led reviewer** before any heavy run; reviewers get problem+goal+
  artifact ONLY (no diagnosis/expected answers). [[feedback-heavy-tasks-multi-agent]], [[feedback-reviewer-no-leading]].
- **GPU serial, no concurrent GPU jobs; fan-out = READ-ONLY.** Model compute stays on GPU (no CPU
  fallback). [[feedback-gpu-only-execution]], [[feedback-no-concurrent-gpu-jobs]].
- **Standard metrics** via `METRICS.md` ladder (D_Choi/1−F_e/RHP/BLP conventions carried with numbers);
  baselines pristine at recommended settings. **Scripted-execution:** every run = committed runner
  (pipefail + tee + `python-exit`), multi-line python in a file (the wsl outer-shell pre-expands `$`).
- **H6:** every `src/**` + `tests/**` change is user-confirmed before commit.
- **Sequencing/trigger:** `nonmarkovian_memory_carrier_scope.md` §4 gates this round on the **classical
  `CoupledCycleTeacher` round landing green** (currently PAUSED — its G6 §5 re-registration WIP is
  checkpointed at commit `ac06a09`; resume it in the NEW package layout: `teachers/coupled_cycle.py` +
  `docs/twin_validation/gates/`). The theory-first prereg (no-GPU) MAY start in parallel; the teacher
  BUILD should wait for the classical gates. Confirm with the user which order.

## 6. Pointers (all in the POST-migration layout)

- Binding scope: `docs/twin_validation/nonmarkovian_memory_carrier_scope.md`.
- Pilot spec + M2 slot: `docs/twin_validation/coupled_pseudomode_pilot_prereg.md`,
  `docs/twin_validation/quantum_bath_slot_prereg.md`, `HANDOFF_coupling_simulator_2026-07-02.md` §3
  (the 1q+1-mode → stabilizer-unit build path).
- Local-only physics (gitignored `outputs/`, re-run to confirm — not assumed):
  `coupled_pseudomode_pilot_v1_n2.py`, `quantum_bath_m2_dual_arm.py`, `cgf_probe_v1.py`,
  `involuntary_w_check_v{1,2}.py`; `outputs/teacher_prereg/nm_*.py` + `qutip_*.py`.
- Package (canonical): `carrier/joint_lindbladian.py` (the propagator), `teachers/coupled_cycle.py`
  (template + control arm), `certify/{types,facade,core,anchors}` (the certification seam),
  `mechanisms/{axis1_primitives,seam_teachers}`, `source/{process,coupling}`.
- Memory: [[project-quantum-bath-m1-m2]], [[project-coupled-pseudomode-pilot-v1]],
  [[project-nonmarkovian-wedge-must-be-coherence]], [[project-scalable-coupled-error-open-problem]],
  [[project-coupling-nonmarkovian-is-the-contribution]], [[project-qec-coupling-simulator-contract]].
- `docs/CODE_MAP.md` (read before re-exploring; regenerate after any src change).

## 7. Environment (CRITICAL)

`aiqec` conda env is COMPLETE (ninja/nvcc/g++/torch 2.12+cu130, RTX 5090). Run with the env bin on PATH or
torch can't find `ninja` (misleading kernel-test failure): `conda run -n aiqec python …` or explicit
`wsl.exe -d ubuntu-f -- bash -c "cd /home/cx/Document/AI_QEC/AI_QEC && PATH=/home/cx/miniconda3/envs/aiqec/bin:/usr/local/cuda/bin:/usr/bin:/bin python …"`. wsl outer-bash PRE-EXPANDS `$PATH`/`$?`/`$VAR` — use explicit paths, put multi-line python in a script file, and NEVER `pgrep -f <string>` where `<string>` is in the poller's own command line (it matches itself → infinite loop). **The full pytest suite exits 134/139 from a benign torch/cuda teardown crash AFTER the `N passed` summary prints — parse the summary line, not the exit code** (see [[wsl-exit-code-quote-chain]]). Scope pytest to `tests/`.

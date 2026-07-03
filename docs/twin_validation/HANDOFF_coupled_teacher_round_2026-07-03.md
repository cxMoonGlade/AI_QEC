# HANDOFF — CoupledCycleTeacher round (2026-07-03, session close)

**Self-contained. Read this + `CLAUDE.md` + the memory index (esp. [[feedback-code-map-anti-forgetting]],
[[feedback-simulator-not-decoder]], [[feedback-anti-toy-ground-truth-protocol]]).** The scratchpad of
the session that wrote this is gone; everything load-bearing is inlined below or in the repo.

## 0. Mission + epistemic frame (binding)

- **Priority (user-ratified):** BUILD the coupling-error QEC simulator. The **classical 1/f shared-source
  slice (`CoupledCycleTeacher`) IS AND CAN ONLY BE SCAFFOLDING**; the **quantum GKSL bath is THE FINAL
  TARGET** (near-resonant TLS / pseudomode-enlarged GKSL — the M1/M2 line + the coupled-pseudomode pilot).
  Scope for the target round: `nonmarkovian_memory_carrier_scope.md` (committed).
- **Epistemic frame (do NOT violate in language or claims):** there is **NO ground truth** — everything is
  **simulation**. The teacher is a noise model we **specify** (we set ζ, γφ, the source). QuTiP / closed
  forms are **FORMAL oracles** (independent reference computations of the same specified model; they catch
  implementation bugs, never certify correspondence to physical reality). The `.truth` API = "the params we
  put in," not physical truth. Certification claims read "computes the specified model correctly + records
  carry its structure + not-a-toy," never "validated vs truth." Physical correspondence only at phase C.
- **LER is the simulator's PRODUCT** (records → decoder → logical-error-rate); `1−F_e`/TV/Spitz-p_ij/NLL are
  internal **instruments**. Consistent with the standing rule: decoder/DEM/LER stays OUT of the VALIDITY
  chain (G4's ΔLER is report-only, never gates).

## 1. What is committed (branch Dev-F, this session)

| SHA | what |
|---|---|
| `76941a8` | tools/gen_code_map.py + docs/CODE_MAP.md + docs/code_status.json (drift-proof code inventory); AGENTS.md → thin router |
| `3f35735` | round prereg + record gates G4–G8 (AUTHORED, **G6 BLOCKED**) + NM-carrier scope doc |
| `83af1ea` | src: `params_for_substep` injection into the dense record emitter (Builder 1) + test |
| `6ee7a30` | src: `CoupledCycleTeacher` (Builder 2) + test (24) + README entries |

**All src/tests are REVIEWED (un-led) but UNRUN on GPU** (py_compile-clean only). First new-session action
validates them. NOT committed (gitignored `outputs/`, local-only, same machine): the G0-v2 script + all
runners (below). NOT committed (deliberately — pre-existing, not this session's work): a batch of prior-session
docs/notes + `.venv`/`METRICS.md` changes left dirty in the tree; do not sweep them into a commit blindly.

**New code (from `docs/CODE_MAP.md` — regenerate with `python tools/gen_code_map.py` after any src change):**
- `forward/joint_lindbladian.py` — Axis-1 within-substep assembler (G2-certified; already committed earlier).
- `mechanisms/coupled_teachers.py::CoupledCycleTeacher` — the slice-1 teacher.
- `mechanisms/source_coupling.py` + `source_process.py` — Axis-2 memory-ful source + Θ fan-out (committed earlier).
- `simulator/axis1_record_evidence.py` — dense `{det,obs}` emitter (now with `params_for_substep`).

## 2. The build state (one paragraph)

The classical slice is BUILT: one memory-ful 1/f source `z_t` → Θ fan-out → per-round `Axis1PrimitiveParams`
→ sealed dense emitter → R-round `{det,obs}`, with `.markovian_baseline()` / `.off_source()` control arms,
isolation (payload = `{det,obs}` only), and the compiler-seal assert. G2 (channel-level joint-L fidelity) is
certified. The **record-level gate suite (G4–G8) is authored but the G6 ablation gate is BLOCKED** because its
registered statistics are mis-modeled for a CORRECT teacher (see §4). Nothing has run on GPU yet.

## 3. THE TWO PARALLEL TRACKS (what you asked for)

Both run on the same machine; **GPU work is SERIAL (no concurrent GPU jobs)** — Track A owns the GPU, Track B
is theory/authoring (no GPU) until it needs a run.

### Track A — RUN G0-v2 (RUN-CLEARED; owns the GPU first)
```bash
bash outputs/run_g0_v2.sh            # pipefail + tee outputs/logs/g0_v2.log + python-exit into the log
```
Produces `outputs/twin_validation/g0_v2_effectsize.json`: `{verdict, per-R rows, β, chosen:{fixture,R_star,
N_star,...}}`. This is the pre-build effect-size gate; its `chosen` triple was meant to seed the gate config.
**F3 CAVEAT (binding):** G0-v2 measures TV with the all-zero instrument on two static points; the teacher
emits with base flips ~1.5e-2 + a trajectory mixture, so the emitted-record TV is smaller / noise floor
higher. **N\* under-sizes even mean-level tests and is FIRST-moment TV sizing — it must NOT be handed to the
second-moment G6 statistics** without the §4 re-derivation. So G0-v2's own run is valid (report its verdict),
but its N\* is an input to fix, not a final constant.

### Track B — FIX G6 (theory-first re-registration; no GPU until the re-run)
The reviewer proved (pre-run, from committed constants) that G6 §5 as-registered **cannot behave as registered
on a correct teacher**. Re-derive the correct null model + statistics, then **RE-REGISTER prereg §5 BEFORE any
gate run** (post-run criterion changes are unregisterable — theory-first discipline). The structural
re-derivation (F1) is independent of Track A; only the N-sizing joins Track A's output. Also fix F2 (a
commit-gated src change) and F4/F6 (teacher). Details in §4.

**Join point:** Track B's re-derived statistics + Track A's (F3-corrected) N give the runnable G6; then
`bash outputs/run_gates_suite.sh` (G2-fresh → G4 → G5 → G6 → G7 → g8_runner.json).

## 4. Reviewer findings (un-led review, 2026-07-03) — the fix list

**3 MAJOR (block the gate suite), 5 MINOR, 10 NOTE.** RUN-CLEARED: emitter seam + its test, teacher + its
tests (for the test run), READMEs, `_gate_common.py`, `g7_isolation.py`, G0-v2 (own measurement, F3 caveat),
config template, runners. BLOCKED: `g6_ablation.py`, the suite `run_gates.py`, and prereg §5 registration.

- **F1 (MAJOR) — G6's registered record-stats are structurally mis-modeled.** On a *correct* teacher:
  (a) adjacent round-delta detectors **share a measurement** → the delta stream is **MA(1)**, so i.i.d.
  instrument flips (p≈0.0149, the teacher's own closed form) give Spitz p̂_ij(lag 1)≈0.015 in **every arm
  incl. `off`** — prereg §5.4 "Off S1/S2 ≈ 0 exactly" is FALSE, and C4/C3's markov-flat clauses fail at any
  usable N. (b) the **trajectory-mean instrument adds a per-shot common-rate covariance ≈8e-5** in shared
  AND markovian arms (permutation-invariant), ~4 orders above the γφ memory signal — S-1's bound doesn't
  cover it. (c) the **per-field permutation null is EXCHANGEABLE, not independent** — at R=12 the markovian
  arm retains ≈74% of the shared arm's lag-1 param covariance (100% at R=2), so C3's two clauses are jointly
  unsatisfiable. (d) the intended per-round-γφ **second-moment** signal (~1e-8) needs **N ≳ 7e9** even
  noiseless — 4+ orders above the 1e6 cap; N\* is first-moment TV sizing misapplied. P1's pipeline null draws
  i.i.d. *delta* bits (the wrong null) so the self-falsification pair misses all of this. **⇒ Re-derive the
  MA(1)-correct null + a statistic whose signal is feasible at N≤1e6 (or honestly report the coupling is
  sub-detectable on records at feasible N — a FAITHFUL property per H2, not a failure), then re-register §5.**
- **F2 (MAJOR) — the registered 4q fixture is unconstructible through the config seam.** `construct_teacher`
  does `factory(**teacher_kwargs)` from JSON, but the 4q variant needs a `code_spec_builder` (a callable),
  and the only 4q CodeSpec lives inside the gitignored G0 script; the 5q fixture is registered as
  never-qualifying (§1.5). Fix: expose a 4q CodeSpec builder in `mechanisms/coupled_teachers.py` (or
  `simulator/axis1_codespec_runner.py`) reachable by name — a **commit-gated src change** — or re-scope the
  registered fixture.
- **F3 (MAJOR-ish) — N\* channel mismatch** (see Track A caveat). Derive a gate-specific power (or a G0-v2b
  that measures TV through the actual emit channel) before using N\* for §2–§6.
- **F4 (MINOR)** G6-C1 inspects 1 trajectory vs the registered ≥min(N,256) (teacher truth surfaces one
  trajectory's per-cycle params; `_TRUTH_PARAMS_SAMPLE_TRAJECTORIES=1`) → a ~2e-4 constant-trajectory
  false-FAIL risk; widening the truth sample is a src knob.
- **F5 (MINOR)** P-G4-4's vendored-corrqec branch is unimplemented (DEFERRED even with a root supplied).
  corrqec IS now vendored locally: `external/baselines/corrqec` @ `a62e765614b5db51620467b51695b66fd14749e3`
  (pristine, gitignored). Wire `--corrqec-root`/config `corrqec_root` to it, scoped to the Pauli/temporal-mask
  layer ONLY (contract §H, anti-circular; NEVER compare to our own generator).
- **F6 (MINOR)** the teacher docstring's C-9 ("permutation destroys alignment") + S-1 instrument-bound claims
  are inaccurate (the source of the §5.4 error) — revise WITH the §5 re-registration.
- **F7 (MINOR)** G7 truth-scramble is near-vacuous for this teacher yet classed GENUINE; + a live `_last_emit`
  reference sits in `truth` (tighten).
- **F8 (MINOR)** G5 comparator z's omit the shared-arm variance (√2 overstated).

## 5. Run commands (all via committed runners; `outputs/` is gitignored/local-only)

```bash
bash outputs/run_g0_v2.sh                              # Track A: the effect-size gate (GPU)
bash outputs/run_coupled_teacher_round_tests.sh        # targeted test set (emitter-override + teacher + jointL + source_*)
bash outputs/run_coupled_teacher_round_tests.sh --full # full regression (for the H6 commit gate)
bash outputs/run_gates_suite.sh                        # AFTER §5 re-registration + 4q seam + N basis
```
Every runner: `set -o pipefail`, tees to `outputs/logs/`, appends `python-exit=${PIPESTATUS[0]}` into the log
(the wsl.exe outer-bash pre-expands `$?` — always read the tee'd python-exit, never the shell's `$?`).
Python: `/home/cx/miniconda3/envs/aiqec/bin/python` (RTX 5090, torch 2.12+cu130, cuda True).

## 6. Disciplines (standing; do not skip)

- **H6 commit gate:** every `src/qec_twin/**` + `tests/**` change needs explicit user confirmation before
  commit. docs/tools/outputs = normal flow. The F2 4q-seam fix is a src change ⇒ H6-gated.
- **Theory-first:** re-register §5 (predict-before-measure) BEFORE running G6; a criterion changed after
  seeing realized data is unregisterable. Amendment budget: one per gate, then STOP + finding.
- **≥3 disjoint builders + un-led reviewer** before any heavy run; reviewers get problem+goal+artifact only.
- **GPU serial, no concurrent GPU jobs; fan-out = READ-ONLY.** Faithfulness three-piece on every load-bearing
  model. Standard metrics via METRICS.md. **Regenerate `docs/CODE_MAP.md` after any src change; read it before
  re-exploring the codebase.**
- **NOT this round:** T-M3 prereg (queued), the real-data estimator demo (PARKED), paper-phase
  novelty/positioning (build > novelty).

## 7. Pointers

- `docs/twin_validation/coupled_teacher_round_gates_prereg.md` — the registration to REVISE (§5).
- `docs/twin_validation/coupled_cycle_teacher_design.md` — the round SPEC (Path A, §3 emit constraints, §6b red-team).
- `docs/twin_validation/nonmarkovian_memory_carrier_scope.md` — the quantum-bath target scope (next round).
- `docs/CODE_MAP.md` (+ `tools/gen_code_map.py`, `docs/code_status.json`) — the current code inventory.
- `docs/twin_validation/qec_coupling_simulator_build_contract.md` §C (gate evidence objects) + §H (corrqec scope).
- `external/baselines/corrqec` @ a62e7656 — the G4 external reference (Pauli-layer only).

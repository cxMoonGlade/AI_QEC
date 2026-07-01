# PHASE 3.0 HANDOFF — Axis-1 coupled teacher (+ the M12 / exact-step episode)

Date 2026-06-30. Entry point for a fresh session. This is a **point-in-time map, NOT live truth.**

## 0. How to use this doc (illusion-resilience preamble — READ FIRST)

This session was repeatedly corrected for being illusion-prone (assembling claims from search snippets /
tool summaries; nearly fabricating a citation; jumping to a solution before defining the problem). Do not
repeat that. Binding rules for consuming this handoff:

1. **Tags on every load-bearing claim** — `[VERIFIED]` = I ran it / saw the printed evidence THIS session;
   `[CODE]` = code-verified at the cited `file:line`; `[PRIOR]` = from earlier-session work, **re-verify
   before building on it**; `[REASONED]` = inference, not measured.
2. **Code is truth, this doc drifts.** Before acting on any claim, read the cited source / re-run the named
   cert and read its printed evidence. `outputs/` is **gitignored / local-only** — those certs must be
   **re-run**, not assumed.
3. **The hard-won rule** (memory `feedback-define-problem-from-repo-first`): define the problem from the
   actual repo FIRST; do not jump to a solution or ground it in literature before you know where the
   problem bites in the code. Snippet/summary assembly is hallucination. Test "it works" with a committed
   run; never assert it.
4. Honor the standing disciplines (memory `MEMORY.md`): scripted-execution (every code run is a committed
   script with asserts + printed evidence + `__main__` guard); GPU-only + **no concurrent GPU jobs**;
   anti-toy ground-truth (independent GT, never a parallel model); commit-gate (below); standard metrics;
   don't lead the reviewer.

## 1. The goal

- **Mainline** (`CLAUDE.md`, `docs/TWIN.md`): the twin — a validated causal model of QEC error mechanisms.
- **Immediate mandate** (user): the simulator's **correct, complete Axis-1 error-mechanism COUPLING**
  (the within-substep joint Lindbladian), physically correct, each mechanism ≥2-DIRECT-physical-grounded.
- **Active task ("Phase 3.0", task #13):** build the **`CoupledCycleTeacher`** — the keystone
  `ControlledTeacher` integration object that emits real `{det,obs}` records carrying the coupling, at the
  Axis-1↔Axis-2 boundary (one shared 1/f source → Θ fan-out → per-cycle mechanism params → records).

## 2. Working-tree state `[VERIFIED 2026-06-30 via git]`

- Branch `Dev-F`. Latest commits are early Axis-1 *ledger* commits only (m6/m20/m22/m28/m29/m32).
- **The entire Axis-1 rebuild + M12 Phase-B + the review remediation is UNCOMMITTED** (commit-gated; staged
  for user review). Do not commit `src/qec_twin/**` or `tests/**` without explicit user confirmation;
  `docs/**` + `outputs/**` follow normal flow.
  - Modified src (commit-gated): `simulator/axis1_mcwf_mps_execution.py` (carrier surgery [COH_* removal] +
    M12 Phase-B 2-site joint-collapse seam + the mass-residual guardrail + `TWO_SITE_COLLAPSE_FAMILIES`
    preflight), `simulator/axis1_qt_mps_execution.py` (COH_* fail-closed), `mechanisms/axis1_primitives.py`.
  - Modified tests (commit-gated): `tests/test_simulator_axis1_schedule.py` (2 seepage tests carry
    `mass_residual_budget=None`).
  - Deleted (cut mechanisms, uncommitted): `tests/test_m28_*`, `tests/test_m32_*`.
  - Untracked: the new Axis-1 docs + tests (`tests/test_m12_phaseB_seam.py`, `test_m10_*`, `test_m23_*`).
  - `outputs/` is gitignored → all certs + the 5-model review dirs are **local-only; re-run to verify**.
- When committing, split ≥3 logical commits (carrier surgery + cut-test deletions / M12 Phase-B seam /
  M12 5-model review remediation).

## 3. What has been done

### 3a. Axis-1 mechanism rebuild `[PRIOR — re-run the certs before relying]`
- 15 KEPT under the ≥2-DIRECT-physical gate: M4/M5/M24 (collapse), M6/M7/M20 (1q coherent over-rotation),
  M8/M22/M23/M10/M29 (2q coherent parasitic), M11 (crosstalk), M12 (correlated relaxation), M17 (reset
  bias), M21/M34 (leakage). 9 CUT: M15/M18/M19/M27/M28/M30/M31/M32/M33. Each kept mechanism has a
  theory-first prereg + derivation + executable cert. Capstone: `docs/twin_validation/axis1_rebuild_completion_audit.md`.
- **Within-substep coupling (联动) certified** `[PRIOR/local]`: `outputs/twin_validation/cert_axis1_full_coupling.py`
  claims joint == from-scratch scipy Liouvillian to 2.4e-15 + a pairwise effect-size table.
  Status doc: `docs/twin_validation/axis1_coupling_status.md`.

### 3b. M12 Phase-B (2-site joint-collapse trajectory seam) + 5-model review remediation `[VERIFIED this session]`
- The seam (in `axis1_mcwf_mps_execution.py`): `_joint_collapse_operator` (CORR_RELAX = collective Dicke
  `√γ(σ⁻⊗I+I⊗σ⁻)`), `_joint_nojump_first_order_kraus`, the `len(support)==2` branch in
  `_sample_joint_jump_or_nojump`, + `CORR_RELAX` in the collapse allow-list.
- 5-model review at `outputs/twin_validation/m12_phaseB_review/` → 6 findings remediated:
  1. **mass-residual guardrail** `_first_order_mass_residual_blocks` + `mass_residual_budget` (default 0.1,
     `None` disables) — a deterministic pre-flight that fail-closes the manifest when the first-order
     no-jump step is grossly non-CPTP (`¼·dt_micro²·(Σ‖c†c‖_op)² > budget`); reports the required
     `microstep_count`. **(c)-class tripwire.**
  2. `TWO_SITE_COLLAPSE_FAMILIES` support-arity preflight.
  3. F3 wrong-relative-sign falsifier added to `cert_m12_phaseB_trajectory.py`.
  4. leaked-partner embed declared+bounded (M12 BUILD prereg §8).
  5. `tests/test_m12_phaseB_seam.py` — 11 tests **[VERIFIED 11/11 pass]**.
  6. §9 post-hoc-downgrade correction + {C_s,C_a} matched-coupling reconciliation (M12 docs).
- PT4 closure: `cert_m12_phaseB_convergence.py` (ensemble→Phase-A channel, first-order convergence) **[VERIFIED ALL PASS]**.
- Regression under the default guardrail: **446 passed, 1 skipped** `[VERIFIED — outputs/.../r_regression_postfix.log]`.

### 3c. The exact-step MCWF episode — created, reviewed, then DELETED `[VERIFIED]`
- I proposed an "exact-step MCWF" upgrade (exact no-jump `exp(−½c†c dt)` + `p_jump = 1−p0`), wrote a
  prereg + grounding note, ran a 5-model review. The review caught a **real physics error** (P3 claimed
  `1−F_e ≤ 5e-2` at m=1 — wrong; the exact-step fixes *mass*, not single-coarse-step *dynamics*) and I
  **nearly fabricated a citation** (assumed "Riesch & Jirauschek" from my query; the paper arXiv:1803.08589
  is **Kornyik & Vukics**).
- A **problem-definition re-assessment** (§3d) then showed the exact-step is **non-urgent**. The prereg +
  grounding note were **DELETED** (user instruction). The review dir `outputs/twin_validation/exact_step_mcwf_review/`
  remains as the evidence trail (incl. `verify_pt5.py`, the script that proved the P3 error).
- This is the source of the binding lesson in §0.

### 3d. Problem definition (why the "nightmare" is not what it looked like) `[CODE-VERIFIED]`
The first-order mass-blow-up ("mass → 2.0 at γ·dt~1"):
- is **NOT on the default path** — `simulator/axis1_carrier_execution.py:50,82,186`: default
  `execution_backend_contract = "dense_jointL_probe"` = exact dense joint-L (`assemble_substep_channel`,
  one `expm`), small-N, **fails closed** over-cap. No first-order, no nightmare.
- lives ONLY in the **explicit opt-in** `mcwf_mps_state_record` path (over-cap / leakage).
- appears ONLY at **artificial** `γ·dt ~ 1` (physical T1/T2/leakage × real dt ⇒ `γ·dt ~ 1e-4…1e-2`); the
  budget (§3b.1) guards that regime.
- is **NOT inherent to MPS+MCWF** — correct MCWF (QuTiP `mcsolve`, in-repo oracle) has no blow-up; it's the
  project's first-order fixed-microstep *choice* for the scalable carrier.
⇒ The exact-step is a non-urgent hardening of a non-default path, not a Phase-3.0 blocker.

### 3e. MCWF usability test `[VERIFIED ALL PASS]`
- `outputs/twin_validation/cert_mcwf_usability_leakage.py`: the MCWF path IS usable for the qutrit-leakage
  case the dense default refuses — runs at physical rates, **emits `{det,obs}`** (`detector_records` +
  `logical_observable_records`), leakage real (|2⟩ represented + seepage occurs), feasible (400 traj /
  4.4 s), budget silent at physical rates / fires at artificial.

## 4. The pipeline — how it is actually built `[CODE-VERIFIED]`

Three Axis-1 carrier execution paths (dispatcher `simulator/axis1_carrier_execution.py`, selected by
`execution_backend_contract`); see `simulator/README.md` for the authoritative map:
1. **`dense_jointL_probe` (DEFAULT)** — exact dense joint-Lindblad channel; small-N; fails closed over-cap.
2. **`mcwf_mps_state_record` (opt-in)** — first-order fixed-microstep MCWF on a quimb/torch MPS; over-cap /
   leakage; the mass-residual guardrail lives here (`simulator/axis1_mcwf_mps_execution.py`).
3. **`qutip_cuquantum_*`** — QuTiP `mcsolve`/`mesolve` oracle (the modern exact method), small systems.

Supporting seams the `CoupledCycleTeacher` will reuse:
- **Dense `{det,obs}` emission:** `simulator/axis1_record_evidence.py` —
  `axis1_measurement_record_evidence_manifest(schedule, device="cuda")` → exact detector + logical-observable
  records via the schedule's XOR wiring; `write_axis1_measurement_record_samples(schedule, out_dir, shots=,
  seed=)` → `.b8`.
- **Θ source fan-out (Axis-2):** `mechanisms/source_coupling.py` — `source_to_params(z_t)` /
  `trajectory_to_params(z_traj)` → `CoupledMechanismParams` (`zz_zeta_radns`, `gamma_phi_per_ns`/`tphi_ns`,
  `detuning_radns`, `drive_omega_radns`, …); `independent_baseline_trajectory_to_params(...)` is the
  ready-made `markovian_baseline()` negative control.
- **Protocol:** `ControlledTeacher` at `audit/certify/types.py:278` (`sched`/`truth`/`emit(regime,*,m,N,seed)`
  /`channels()`); `Regime` dataclass nearby. Adapter pattern to mirror: `outputs/teacher_prereg/certify_dm_anchor_check.py`
  (`Teacher23`).
- **Schedule construction:** `simulator.CircuitBuilder` + `Axis1LocalLindbladContextSpec` +
  `circuit_ir_to_substep_schedule` (see `cert_mcwf_usability_leakage.py` for a worked qutrit-leakage build,
  and `tests/test_simulator_axis1_schedule.py` for many more).

## 5. The gap + how to make it up

### Phase 3.0 keystone: `mechanisms/coupled_teachers.py::CoupledCycleTeacher` — **DOES NOT EXIST yet** `[VERIFIED absent]`
Grounded design (slice #1 = dense, no leakage; per `qec_coupling_simulator_build_contract.md` Section E):
- `emit(regime, *, m, N, seed)`: source trajectory `z_t` → `trajectory_to_params` → per-cycle
  `CoupledMechanismParams` → build the small d3-window R-round schedule(s) carrying those params
  (`Axis1LocalLindbladContextSpec` + static-ZZ + detector/obs wiring) → run `axis1_record_evidence` (dense
  exact) → concatenate to R-round `{det,obs}`.
- `truth` = evaluator-only `{source, params}`; `channels()` = per-substep CPTP field; `markovian_baseline()`
  = `independent_baseline_trajectory_to_params` (G6 negative control).
- **OPEN design detail — ground it BEFORE writing, do NOT guess:** how per-cycle-varying source params flow
  into a **multi-round** schedule + the record fold (one R-round schedule vs R single-cycle schedules
  concatenated). Read an existing multi-round `CodeSpec → SubstepSchedule → axis1_record_evidence` example
  (the `axis1_codespec_runner` and its test, per `simulator/README.md` `[verify it exists]`).
- **Acceptance:** the 8 gates G1–G8 in `qec_coupling_simulator_build_contract.md` (Section C) on the Section E
  vertical slice. G2 (within-substep joint-L fidelity, ZZ×T2 exact-zero control + DR×ZZ band) is ALREADY
  certified at the channel level by `cert_axis1_full_coupling.py`; the slice adds G1 (real schedule), G4/G6
  (record faithfulness — corrqec scoped to the Pauli layer ONLY, never the analog joint-L), G7 (isolation).
  **Build the shortest path to "G2 + faithful record plumbing" first.**
- **Discipline:** design-first; commit-gated (staged); M3-scale ⇒ multi-builder + separate-lane reviewer;
  GPU serial; cert it (usability + a `markovian_baseline`-vs-shared separation check via
  `cross_mechanism_correlation`).
- **Caveat (binding, H2 finding):** the non-Markovian novelty is capped at the source layer — the slice is
  "faithful forward infrastructure," not a record-level discrimination headline. The unforgeable
  non-Markovian signature is coherence revival (CP-divisibility breaking), not classical round-correlation.

### Broader "complete Axis-1" gap (after the keystone) `[REASONED, from the §-by-§ assessment]`
1. **Frontend emission for the cert-only mechanisms** — CORR_RELAX (M12), M11 crosstalk, the 2q-coherent
   parasitic XX/YY/ZX, M17 reset-bias are driven by hand-built term dicts, not schedule-emitted. (Confirm
   which of the 15 flow through `Axis1LocalLindbladContextSpec`/`declare_*` vs are cert-only — a quick
   inventory; T1/T2/T1_UP/static-ZZ/leakage already emit `[CODE: axis1_context.py]`.)
2. **The leakage/qutrit arm (slice #2)** — MCWF path, verified usable (§3e); but d3-**scale** feasibility
   (MPS bond / memory) is **NOT tested** (the open empirical risk; cf. Sander et al. arXiv:2606.13779).
3. **Gates G4–G8 on real records; the milestone metric + rigor audits** (METRICS.md ladder; classify every
   conclusion theorem-backed vs provisional).

## 6. Key files (verified paths)

- `CLAUDE.md`, `docs/TWIN.md`, `docs/METRICS.md`, `docs/FAITHFULNESS_PROTOCOL.md`, `docs/plan3.md` — binding context.
- `docs/twin_validation/qec_coupling_simulator_build_contract.md` — the Phase-3.0 build contract (Section E slice, G1–G8).
- `docs/twin_validation/axis1_coupling_status.md` — within-substep coupling status + effect-size table.
- `docs/twin_validation/axis1_rebuild_completion_audit.md` — the Axis-1 rebuild capstone.
- `docs/twin_validation/m12_correlated_2q_relaxation_BUILD_prereg.md` — M12 Phase-B seam design (+ §9 status).
- `src/qec_twin/simulator/README.md` — authoritative pipeline map.
- `src/qec_twin/simulator/axis1_mcwf_mps_execution.py` — the MCWF carrier (seam + guardrail).
- `src/qec_twin/simulator/axis1_record_evidence.py` — dense `{det,obs}` emission.
- `src/qec_twin/mechanisms/source_coupling.py` — Θ fan-out.
- `src/qec_twin/audit/certify/types.py:278` — `ControlledTeacher` protocol.
- `outputs/twin_validation/cert_axis1_full_coupling.py`, `cert_m12_phaseB_{trajectory,convergence,secondary}.py`,
  `cert_mcwf_usability_leakage.py` — the certs to **re-run** (local-only).
- `<memory>/MEMORY.md` — the working-rules index (illusion-resilience disciplines).

## 7. Immediate next action

Ground the §5 OPEN design detail (multi-round schedule + record fold) by reading the existing
`CodeSpec → schedule → axis1_record_evidence` example, then write `CoupledCycleTeacher` design-first and
build it (commit-gated/staged, with a cert). Do NOT start by writing code — start by reading the example
and confirming the per-cycle-params flow. Slow is fast.

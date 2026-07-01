# DESIGN — `CoupledCycleTeacher` (Phase 3.0 keystone, slice #1 dense / no-leakage)

**Date 2026-06-30. Status: design-first draft, pre-build, commit-gated.** Binds to
`qec_coupling_simulator_build_contract.md` (gates G1–G8, Section C) and `PHASE3_HANDOFF.md`
(as-built pipeline). Author pass only; a separate-lane reviewer evaluates this BEFORE any
`src/qec_twin/**` is written. Every load-bearing claim below is tagged `[CODE file:line]` =
verified in source this session, or `[CONTRACT]` = from the build contract, or `[OPEN]` =
a build-time detail a builder must confirm/resolve.

## 0. What this builds, in one sentence

`mechanisms/coupled_teachers.py::CoupledCycleTeacher` — the evaluator-only `ControlledTeacher`
that turns ONE shared 1/f source trajectory into per-cycle coupled mechanism params (Θ fan-out)
and emits real R-round `{det,obs}` records carrying the within-substep coupling (Axis-1) and the
cross-cycle source memory (Axis-2), so the records drop into `certify_cells` + Anchor/Control
unchanged.

## 1. Grounded as-built reality (supersedes parts of the 2026-06-26 contract)

The contract predates the current pipeline. Verified this session:

- **`mechanisms/source_coupling.py` EXISTS and is complete** `[CODE source_coupling.py:217,229,240]`
  — `source_to_params`, `trajectory_to_params(z_traj) -> tuple[CoupledMechanismParams,...]`
  (one bundle per cycle), `independent_baseline_trajectory_to_params(...,seed=)` (the G6 negative
  control), `cross_mechanism_correlation` (the G6 statistic). Contract called this "NEW" — it is DONE.
- **The Axis-1 joint-L assembler EXISTS** — `qec_twin.forward.joint_lindbladian.assemble_substep_channel`
  is the assembler the dense record path already calls `[CODE axis1_record_evidence.py:557–561]`; G2 is
  certified at the channel level (`cert_axis1_full_coupling.py`, handoff §3a). Contract called it "NEW."
- **Emit seam = the dense `axis1_record_evidence` path, NOT `WindowChannel`.** The handoff names
  `axis1_measurement_record_evidence_manifest` as the dense `{det,obs}` emission the teacher reuses
  (handoff §4); slice #1 = dense, no leakage. The contract Section-E `WindowChannel` per-shot language
  is superseded by this as-built dense path. `[CODE axis1_record_evidence.py:173]`
- **Only `coupled_teachers.py::CoupledCycleTeacher` remains absent.** `[VERIFIED absent — glob]`

So the keystone is: wire the existing Θ fan-out + existing assembler/dense-emitter into a
`ControlledTeacher`, adding the ONE missing capability (below).

## 2. The OPEN design detail, resolved from the repo

The handoff flagged: "how per-cycle-varying source params flow into a multi-round schedule + the
record fold (one R-round schedule vs R single-cycle schedules concatenated)." Grounding the actual
emit path resolves it:

1. **State continuity across rounds already works — within ONE schedule's run.** `_enumerate_measurement_records`
   threads `rho` through every substep of every round in one pass `[CODE axis1_record_evidence.py:505,513]`;
   cross-round detectors are native XOR wiring inside that one schedule `[CODE …:636–645]`.
2. **The ONLY missing capability is per-round param variation.** The loop reads ONE schedule-global
   `Axis1LocalLindbladContextSpec` once before the loop `[CODE axis1_record_evidence.py:503 →
   axis1_channel_evidence.py:518,524]`; the schedule stores a single context dict, not a per-round one
   `[CODE analog_schedule.py:353]`. Uniform params across rounds ⇒ NO cross-cycle correlation ⇒ no coupling
   to emit. **Per-cycle variation is essential, not optional.**
3. **Round index is RECOVERABLE but NOT from a populated field** `[CORRECTED by reviewer 2026-06-30]`.
   The author draft wrongly claimed `SubstepOperation.round_index` exists at `analog_schedule.py:257`.
   Truth: line 257 is `AnalogSubstepIR.round_index`, NOT `SubstepOperation`, and it is **hardcoded `None`
   in both constructors** (`_make_substep:871`, `_make_barrier_substep:899`) — never populated. Round
   structure survives ONLY via (a) per-round `barrier` substeps (each round ends with `builder.tick()`,
   `compiler.py:69`) and (b) measurement-key prefixes `round{r}:{check}` (`record_layout.py:195`). So
   per-round params must be keyed off a DERIVED round index (barrier count or key prefix), or an injected
   callable — never the dead `round_index` field.

⇒ The "one R-round schedule vs R concatenated" binary is false. **One real R-round XZZX schedule**
(native detectors + state threading reused), with **per-round param resolution** added to the dense
emitter, is the clean answer.

**DECISION (reviewer-adjudicated 2026-06-30): Path A-corrected, via an injected callable.** Reviewer
grounded the choice independently and recommended Path A over Path B (Path B re-implements seal-audited
state-threading and re-derives the cross-round detector fold by hand → key-namespace collision /
branch-mass loss / frame-mismatch seam bugs the faithfulness protocol forbids), with the specific
mechanism corrected:

- **Path A-corrected (BUILD THIS).** Inject an OPTIONAL
  `params_for_substep: Callable[[substep], Axis1PrimitiveParams] | None` into
  `_enumerate_measurement_records` (threaded from `axis1_measurement_record_evidence_manifest`). When
  present, resolve `params` per selection by calling it instead of reading the one global
  `params` at `[CODE axis1_record_evidence.py:503]`. The callable — owned by the teacher — derives the
  round index from a POPULATED signal (barrier count or `round{r}:` key prefix), NOT the dead
  `round_index` field, and returns that round's `Axis1PrimitiveParams`. **No `SubstepSchedule` schema/
  hash/seal change; native cross-round detectors + state threading reused; default `None` = byte-identical
  regression (verify via the existing `content_hash` freeze guard).** Blast radius: `axis1_record_evidence.py`
  signature + the resolver in `axis1_channel_evidence.py` (+ `axis1_state_evidence.py` only if a per-cycle
  state manifest is wanted). Strictly more flexible than a dict-keyed-by-round override and keeps the
  emitter agnostic to HOW round index is derived.
- **Path B — REJECTED for slice #1** (reviewer Q4: re-implements the seal-audited single pass outside its
  audit; the divergence modes are silent and bypass the freeze guard).

**`[OPEN-1] — RESOLVED to a blocker, now a build task.** The round index is NOT in a populated field
(see §2.3). The callable MUST derive it from barrier-count or measurement-key prefix; a builder writes a
positive control asserting `params` actually differ across rounds for a non-constant trajectory (else the
silent uniform-params toy, red-team R1 below). Off-by-one at the terminal round (which drops its Y-echo)
must be tested on a known 2-round schedule.

## 3. The emit is an OUTER Monte-Carlo over source trajectories

The coupling's observable signature (G6) is cross-cycle correlation in records, which exists only
because one shot's R rounds share a memory-ful `z_t`. So emit is structurally:

```
emit(regime, m, N, seed):
    for each shot s in 1..N (or batched by shared trajectory):
        z_traj  = source.sample(R rounds, seed_s)                 # Axis-2 memory-ful 1/f draw
        params  = trajectory_to_params(z_traj, cfg)               # [CODE source_coupling.py:229] R bundles
        ctx_by_round = { r: coupled_params_to_context(params[r]) } # §4 mapping
        dist    = axis1_measurement_record_evidence_manifest(      # dense exact, per-round ctx (Path A-min)
                      S_Rround, device="cuda",
                      round_context_overrides=ctx_by_round,
                      instrument_spec=coupled_params_to_instrument(params))   # §4
        (det_s, obs_s) = sample_one(dist.record/detector/observable, rng_s)   # Born sample one record
    return {"det": (N,B) uint8, "obs": (N,) uint8}                 # the seam surface [CONTRACT §B-1]
```

Outer MC over trajectories (per-shot redraw); inner exact conditional `P(det,obs | z_traj)` from the
dense path. `[OPEN-2]` batching: shots sharing one `z_traj` can sample from one inner distribution
(cheaper); the design defaults to one trajectory per shot for a clean cross-cycle signal, with batching
as a perf knob a builder may add behind a flag (declare it; it changes the correlation structure if mis-set).

**Three hard constraints on `emit` `[reviewer-added 2026-06-30]`:**
1. **Memory-ful source (NOT `source_coupling`).** `source_coupling.trajectory_to_params` only FANS OUT a
   given `z_traj`; it does not generate it. `z_traj` MUST come from a memory-ful 1/f / RTN generator
   (autocorrelation `≈ e^{-2γ_sw t_cycle}` across cycles) — else G6's cross-cycle correlation is spurious
   (a shared within-cycle latent, not memory; per memory `project-coupling-nonmarkovian-is-the-contribution`,
   concurrent-Markovian coupling is BASELINE-only / echo-removable). Source generator is a build `[OPEN]`:
   confirm which `nm_source`/equivalent sampler is the slice-1 1/f source.
2. **`emit` returns `{det,obs}` ONLY.** The dense manifest carries `applied_steps` with full channel-
   assembly metadata (`[CODE axis1_record_evidence.py:555–569]`: num_kraus, ideal-control names, dt) — a
   G7 isolation leak if returned. `emit` must project to exactly `{"det","obs"}` (optionally `marg`); all
   mechanism structure goes to `truth` only.
3. **Seal assertion at the emit seam.** `_validate_record_evidence_schedule` does NOT enforce
   `require_compiler_schedule_seal` (`[CODE axis1_record_evidence.py:1091]` — only the ≤8q + channel-
   evidence checks). So a hand-built (non-compiler) schedule could emit records that falsely claim "real
   circuit" (G1). `emit` MUST assert the schedule carries a valid compiler seal
   (`has_valid_compiler_schedule_seal`) and that schedule construction stays inside
   `compile_code_spec_to_substep_schedule` — never reconstruct substeps by hand.

## 4. Θ(z_t) → dense slice-1 homes (and what is DEFERRED, bounded)

`CoupledMechanismParams` fields `[CODE source_coupling.py:161–204]` mapped to dense-path homes
(`Axis1LocalLindbladContextSpec` `[CODE axis1_context.py:26–47]` + `Axis1ReadoutResetInstrumentSpec`
`[CODE axis1_record_evidence.py:98–112]`):

| param field | slice-1 home | status |
|---|---|---|
| `zz_zeta_radns` | context `zeta_rad_per_ns` (or per-edge static-ZZ calibration) | **HOMED** — the G2 ZZ axis |
| `gamma_phi_per_ns` / `tphi_ns` | context `gamma_phi_per_ns` | **HOMED** — the G2 T2 axis |
| `readout_flip_p` | instrument `readout_p0_to_1`/`readout_p1_to_0` | **HOMED** (per-round caveat below) |
| `reset_flip_p` | instrument `reset_flip_probability` | **HOMED** (per-round caveat below) |
| `detuning_radns` | no dense home (coherent Z over-rotation = COH_RZ, **CUT** handoff §3a) | **DEFER** |
| `drive_omega_radns` | no dense home (1q over-rotation = COH_RX, **CUT**) | **DEFER** |
| `spillover_cx` | coherent spillover is d3-GATED / Pauli-layer (corrqec scope) | **DEFER** |
| `cz_depol_p` | CZ depolarizing = Pauli-layer (contract: corrqec Pauli-layer ONLY) | **DEFER** |

**Bounded-simplification declaration (faithfulness protocol III):** slice-1 dense coupling rides on
**`zeta × gamma_phi`** (the ZZ×T2 cross-term — already G2-certified at the channel level) plus
readout/reset via the instrument. The four DEFERRED fields map to mechanisms cut in the Axis-1 rebuild
or scoped to the Pauli layer; they are NOT silently dropped — the teacher records them in `truth` with
class (c) and emits them in later slices. **`[OPEN-3]` — ELEVATED to PRE-BUILD ANTI-TOY GATE G0
(reviewer + CLAUDE.md "PREVENT toy from the start").** Because readout/reset are held at trajectory-mean,
`zeta×gamma_phi` is the ONLY per-round record channel in slice-1. If its record-level imprint is
sub-shot-noise at feasible N, G6 "passes" on a flat-vs-flat collapse with NO real signal (red-team R2).
So BEFORE any src is frozen, a committed GPU script measures the `zeta×gamma_phi` record-level effect
size (exact TV distance between the record distributions at two representative per-cycle `(zeta,gamma_phi)`
points + the N to detect it above shot noise). **PASS ⇒ build the slice as scoped. FAIL (sub-noise) ⇒
re-open scope** (restore a deferred field / reconsider the register) — do NOT build the full teacher on a
toy channel.

**Per-round caveat for the instrument:** `Axis1ReadoutResetInstrumentSpec` is also a single per-run
spec `[CODE axis1_record_evidence.py:177]`. Per-round-varying readout/reset has the SAME single-slot
limitation as the context. **RESOLVED (user 2026-06-30): slice-1 holds readout/reset at the
trajectory-mean** — a declared class-(c) simplification recorded in `truth`; per-round readout/reset is a
later-slice extension. This keeps the slice-1 coupling signal on `zeta × gamma_phi` and avoids a second
per-round seam to cert.

## 5. The `ControlledTeacher` surface to implement

Protocol `[CODE audit/certify/types.py:278–299]`:
- `sched` (property) → the parsed real d3 XZZX `SubstepSchedule` (R rounds, interior r10).
- `truth` (property, dict) → evaluator-only: full per-shot `{z_t}` (seed-keyed), per-cycle
  `CoupledMechanismParams.to_manifest()`, the per-round context/instrument, the per-substep channel
  field, coupling_mode. Returned ONLY via `CertReport.truth`, never to the learner (G7).
- `emit(regime, *, m, N, seed)` → `{"det":(N,B)uint8,"obs":(N,)uint8}` per §3.
- `channels()` → the per-substep composite CPTP field (reuse the assembler output the dense path
  already builds).
- `markovian_baseline()` → identical pipeline but `independent_baseline_trajectory_to_params(...,seed=)`
  `[CODE source_coupling.py:240]` (same one-field marginals, broken same-cycle coupling) — the G6
  negative control.

`Regime` is in `audit/certify` `[CODE audit/certify/__init__.py:22]`; adapter pattern to mirror =
`outputs/teacher_prereg/certify_dm_anchor_check.py::Teacher23` (handoff §4). Optional `DMReplayable` /
`CliffordSliceable` (`types.py:302,319`) are later-slice cert anchors, not slice-1 required.

## 6. Acceptance — which gates this slice exercises `[CONTRACT §C, §E]`

- **G1** real schedule — parsed XZZX r10, all 12 checklist items (the slice uses the real circuit).
- **G2 (headline)** — ALREADY certified at channel level (`cert_axis1_full_coupling.py`); the slice
  adds nothing to G2 but must not regress it (ZZ×T2 exact-zero two-witness + DR×ZZ band).
- **G4 (faithfulness)** — emitted records cross-checked vs an INDEPENDENT reference, scoped to the
  Pauli/temporal-mask layer ONLY (corrqec; contract §H anti-circular caveat); decode-relevant ΔLER
  reported with class (sub-floor for mild 1/f = faithful property).
- **G6** — shared-source vs `markovian_baseline()` cross-mechanism/cross-cycle structure difference
  ON RECORDS, OFF-source → collapse. The anti-toy core of Axis-2.
- **G7** — learner payload keys ⊆ `{det,obs,marg}`; records invariant to latent-label scramble.
- **G8** — one committed tracked runner under `docs/twin_validation/gates/`.

Slice cert (handoff §5): a usability cert (emits real `{det,obs}` at physical rates, feasible) + a
`markovian_baseline`-vs-shared separation check via `cross_mechanism_correlation`. Build the shortest
path to "G2-preserved + faithful record plumbing (G1/G4/G6/G7) + G8 runner" first.

## 6b. Toy red-team (reviewer 2026-06-30) — the slice must survive these

- **R1 — dead override → uniform params → fake G6.** A round-index lookup off the dead `round_index`
  field falls back to uniform params; records carry no cross-cycle signal yet plumbing "works"; G6 reads
  flat-vs-flat ≈0 and a careless reader scores "off-source collapses to 0" PASS. Mitigation: positive
  control asserting `params[r]` differ across r AND shared-source corr is NON-zero before checking the
  collapse. (Owned with `[OPEN-1]`.)
- **R2 — G6 collapse passes for want of a signal.** If `zeta×gamma_phi`'s record imprint is sub-noise at
  N, shared and independent both read ≈0 → "collapse" satisfied with nothing to collapse. Mitigation:
  gate G0 (§4) measures the effect size FIRST.
- **R3 — real but Markovian/echo-removable correlation.** i.i.d.-per-round `z_traj` gives within-cycle
  shared-latent correlation, not memory → G6 cross-cycle corr spurious. Mitigation: memory-ful source
  (§3 constraint 1).
- **R4 — isolation leak via the rich manifest.** `emit` returning the manifest leaks mechanism structure
  (G7). Mitigation: §3 constraint 2 (`{det,obs}` only).
- **R5 — seal bypass on the record path.** Non-compiler schedule emits records claiming "real circuit"
  (G1) without the seal. Mitigation: §3 constraint 3 (seal assertion; construct only via the compiler).
- **R6 — batching flattens/inflates the signal.** Mis-set `[OPEN-2]` batching makes cross-shot corr a
  sampling artifact. Mitigation: default one trajectory per shot; declare any batching.

## 7. Build plan (heavy-task discipline: disjoint owners + separate-lane reviewer)

Commit-gated (`src/qec_twin/**` + `tests/**` need explicit user confirmation; `docs/` + `outputs/`
normal). GPU serial, no concurrent GPU jobs.

- **G0 (PRE-BUILD ANTI-TOY GATE) — RAN 2026-06-30, VERDICT = FAIL (scope re-opened).**
  `outputs/twin_validation/g0_zeta_gammaphi_effectsize.py` (GPU, dense emitter unchanged, exact
  `record_probabilities`, 5q 2-round fixture). Representative per-cycle `(zeta,gamma_phi)` delta (from
  `source_to_params` at z=±1e-4) → record **TV = 5.77e-4 → N≈2.7e7** to clear shot noise (≫1e6 feasibility);
  ±3σ → TV=2.02e-3 → N≈2.2e6 (still ≫1e6). **The cross-term is `gamma_phi`-only:** zeta-only TV = **4.3e-11**
  (static-ZZ is record-flat under a realistic 1/f source — the per-cycle detuning shift is ~1e4× below the
  base detuning, so `zeta` varies only ±1e-9). Positive controls PASS (zero-delta TV=0; zeta at G2 magnitude
  → TV=3e-3, instrument live). **Faithful finding, not a bug** — coherent/static ZZ leaves ~no record imprint
  (cf. `project-twin-axisA-gate-result`, `project-coherence-not-identifiable-syndrome-only`); the Axis-1
  ZZ×T2 cross-term is correctly a CHANNEL-level result (G2), and the record-level (Axis-2) carrier is
  source-modulated `gamma_phi` across cycles — which at 2 rounds + trajectory-mean readout/reset is itself
  sub-feasible-N. **⇒ Slice scope RE-OPENED before build (see §9). Do NOT build the teacher on this scope.**
- **Builder 1 — per-round param plumbing (Path A-corrected, §2).** Inject `params_for_substep` callable
  into `_enumerate_measurement_records` (+ resolver in `axis1_channel_evidence.py`; +`axis1_state_evidence`
  if in scope). Round index DERIVED (barrier-count / key-prefix), NOT the dead field. Default `None` =
  byte-identical regression (verify via `content_hash` freeze guard). Owns `[OPEN-1]`, terminal-round
  off-by-one test.
- **Builder 2 — `CoupledCycleTeacher` (§5).** `ControlledTeacher` impl; memory-ful source → `trajectory_to_params`
  → `params_for_substep`; `emit` MC loop returning `{det,obs}` ONLY + seal assertion;
  `truth`/`channels`/`markovian_baseline`. Owns the §3 constraints.
- **Builder 3 — certs + G-gate runner.** Usability cert + `markovian_baseline`-vs-shared separation
  (via `cross_mechanism_correlation`) + tracked `docs/twin_validation/gates/` runner. Owns `[OPEN-2]`.
- **Code reviewer (separate lane, neutral brief).** Adversarial red-team of R1–R6 + isolation on the
  BUILT code, BEFORE any GPU cert run.

Sequencing: **G0 first** (gates the build). Then Builder 1 (Builder 2/3 have A/B-independent surface and
can author in parallel — authoring is non-GPU; GPU certs run serially after the code review).

## 8. Immediate next step

Run G0 (the pre-build anti-toy effect-size gate). If it passes, build Builders 1–3 with the code-reviewer
pass before any GPU cert, staged/uncommitted for user confirmation. Slow is fast.

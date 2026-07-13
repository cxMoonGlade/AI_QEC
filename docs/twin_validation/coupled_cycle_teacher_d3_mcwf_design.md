# DESIGN — `CoupledCycleTeacher` through the d3 (q17) MCWF path

> ⛔ **DO NOT BUILD AS WRITTEN — 3-agent review FAILED this design (2026-06-30).** Fatal findings:
> The line below saying `zeta` is “record-DEAD at any distance” is additionally retracted by the
> 2026-07-13 literature/numerical-provenance audit; its `~1e-11` result is local to one frozen model.
> (1) **§4 observable is a RETIRED strawman** — cross-cycle detector correlation was killed by the parent
> contract (H2/Kam L4: Markov-k-capturable, syndrome-coherence-blind); it also *squares* the real first-order
> `gamma_phi` signal. Must use the contract's **decode-relevant ΔLER + corrqec cross-check** (§6 named it,
> §4 contradicted it). (2) **§3/§8 batching is a multi-week custom-engine REWRITE, not a feature** — quimb MPS
> has no batch axis and trajectories diverge at the first measurement (round 1 of 10), so batching barely
> helps; it's algorithm-bound not memory-bound. (3) **Feasibility is answerable by THEORY now** — `gamma_phi`
> record TV ~linear in rounds: N≈2.7e7 (2 rounds) → ~1e6 (r10) → ~2.7e5 (~20 rounds), so d3 softens
> sub-feasibility ~25× *for `gamma_phi` only*; **`zeta` is record-DEAD at any distance** (basis-diagonal,
> ±1e-9 swing → ~1e-11 TV). (4) **Certs S3 circular** (serial-vs-batched = same engine; real GT = the exact
> 2^17 Lindblad DM). (5) **Round-index derivation has a silent bug** (barriers are per-tick not per-round;
> the round prefix is absent on the CZ/idle substeps that need injection). (6) **Rates are ungrounded**
> class-(c) constants with a ~90× internal `zeta` inconsistency (G2 0.37 MHz vs source-derived 0.004 MHz).
> See the consolidated verdict in the session notes. This doc is retained as the failed-design record.

**Date 2026-06-30. Status: REVIEW-FAILED draft (see banner). STOP for user review before any GPU run or build.** Successor to
`coupled_cycle_teacher_design.md` (the dense/small-window design), retargeted to the now-working d3 MCWF
carrier (commits `1fa0e82` auto-route, `9ea4722` mcwf-d3 measurement). Tags: `[CODE file:line]` verified
this session; `[OPEN]` a build-time detail; `[RISK]` a feasibility/scope risk.

## 0. What changed since the dense design

The dense `CoupledCycleTeacher` slice was capped at ≤8 qubits (small window). Two things now enable the
REAL target (full d3 = q17):
1. **VRAM auto-route** (`execution_backend_contract="auto"`) routes q17 dense→MCWF safely (no OOM).
2. **MCWF runs the full d3 XZZX end-to-end** — the multi-record mixed-X/Z terminal measurement is
   machine-precision certified (2.2e-16, `cert_xmeas_machine_precision.py`).

So the teacher can now emit REAL d3 `{det,obs}` records — IF the per-cycle coupled params can flow into
the MCWF path AND the record-level coupling signal is feasible at d3. Both are open (below).

## 1. Grounded: the MCWF per-round injection point

The MCWF path reads params **schedule-global**, exactly like the dense emitter:
`axis1_carrier_program_manifest` calls `_axis1_primitive_params_for_schedule(schedule)` ONCE
`[CODE axis1_carrier_program.py:286 → :996-1003]` (reads the single `axis1_local_lindblad_context`) and
bakes those rates into EVERY substep's term coefficients (`sqrt(2·params.gamma_phi_per_ns)` etc.,
`[CODE …:543-561]`). The MCWF microstep consumes `substep["terms"]` `[CODE axis1_mcwf_mps_execution.py:855]`.
So **uniform params across all rounds** — no cross-cycle variation, hence no Axis-2 coupling — unless
injected.

**Injection (Path-A-corrected, MCWF parallel):** add an OPTIONAL
`params_for_substep: Callable[[substep], Axis1PrimitiveParams] | None` to `axis1_carrier_program_manifest`
(threaded to the term-lowering that currently reads the one global `params`). When present, resolve params
per substep by its DERIVED round index (barrier-count or `round{r}:` measurement-key prefix — the
`round_index` field is hardcoded `None` here too, same dead-field finding as the dense side). Default
`None` = schedule-global = byte-identical regression. Blast radius: `axis1_carrier_program.py` term-lowering
+ the MCWF execution entry that calls it. Commit-gated. `[OPEN-1]` confirm the term-lowering is the single
choke point (no other path re-reads global params for the coefficients).

## 2. Emit structure — TWO stochastic layers (the key new subtlety)

The dense emit was: outer-MC over source trajectories, inner = EXACT conditional record distribution. MCWF
adds a second stochastic layer: **MCWF itself samples Lindblad trajectories.** So:

```
emit(regime, m, N, seed):
  for shot s (or batch sharing one z_traj):
    z_traj  = memoryful_source.sample(R rounds, seed_s)          # Axis-2 (1/f/RTN, e^{-2γ t} memory)
    params  = trajectory_to_params(z_traj)                        # R CoupledMechanismParams
    p4s     = build_params_for_substep(schedule, params)         # §1 resolver, round-derived
    mcwf    = axis1_carrier_execution(schedule_d3, backend="auto",# → MCWF (q17), per-round params
                 params_for_substep=p4s, options={max_bond, trajectory_count, seed_s})
    (det_s, obs_s) = sample_one(mcwf.record_execution)           # {det,obs} ONLY (G7)
  return {"det":(N,B), "obs":(N,)}
```

**The two-layer question `[OPEN-2]`:** the Axis-2 coupling lives in `z_traj` (shared across a shot's R
rounds); the MCWF Lindblad-trajectory sampling is the *dynamics given params*. Options: (a) one MCWF
trajectory per shot, each with its own `z_traj` — the cross-cycle correlation rides in the per-shot params;
(b) many MCWF trajectories per `z_traj` to get the conditional record distribution, then sample. (a) is the
natural "each shot is one physical run"; (b) is cleaner statistically but multiplies cost. Ground which is
faithful before building — (a) is the physical shot, likely correct.

## 3. Feasibility — cost is an IMPLEMENTATION artifact (batching), not a fundamental limit

**Corrected 2026-06-30 (user):** the serial ~150 s/traj is NOT a fundamental cap.
- **`[COST-1] Serial trajectories → batch them.** `_execute_sampled_mcwf_program` loops
  `for trajectory_index in range(ntraj)` with a fresh `state = initial.copy()` each
  `[CODE axis1_mcwf_mps_execution.py:394-397]` — trajectories are INDEPENDENT quantum-jump unravelings
  (embarrassingly parallel). A trajectory/ensemble BATCH axis on the MPS tensors (apply the deterministic
  gates once across the batch; per-trajectory jump sampling on divergent states) amortizes the cost to
  ~one run for T trajectories, modulo bond×batch memory. This is a real but tractable carrier feature (the
  ENABLER for the d3 record-level slice), NOT a rewrite. `[BUILD]`
- **`[COST-2] 2^(measured) record table → sparse sampled records.** The output builds
  `_measurement_records(25)` = all 2^25 possible records `[VERIFIED triage]`; for T sampled trajectories
  there are ≤T distinct records. Emit the sampled records SPARSELY (bitstring rows + counts), not the full
  exponential table. Also implementation, not fundamental. `[BUILD]`
- **`[COST-3] Low-bond numerical fragility (measured, a caveat not a blocker).** bond=16 CRASHED with an
  inf/nan/negative probability in the jump-sampling multinomial `[VERIFIED triage]` — aggressive truncation
  breaks positivity (cf. `feedback-carrier-transition-numerical-traps`). So batching must run at the STABLE
  bond (~48) and/or the sampler needs a positivity guard (clamp+renormalize before `multinomial`) — a small
  hardening. The batch memory at bond ~48 × T sets the achievable T per run. `[BUILD/hardening]`

⇒ With batched trajectories + sparse records, the d3 record-level statistic IS feasible; the serial-timing
"infeasible" reading was an artifact of the current impl. **The genuine gate reverts to the SIGNAL question**
(§4): does per-cycle coupling leave an above-noise record signal? — now measurable at feasible T.

- **H2 cap (still binding):** the mild-1/f record-level imprint may still be *capped at the source layer*
  (a faithful property, not a failure). The Axis-1 coupling headline stays G2 (channel-level, certified);
  a sub-floor record signal is honest, not a bug. But feasibility no longer PRE-empts the measurement.

## 4. G0-at-d3 gate (PRE-BUILD, prevent-toy) — the first concrete step

Before building the teacher, an `outputs/` script (no committed src) that:
1. Prototypes `params_for_substep` (in-script; or a minimal src spike behind the default-None flag).
2. Runs the d3 MCWF with per-cycle-VARYING vs UNIFORM (`markovian_baseline`) coupled params.
3. Measures the record-level coupling signal — cross-cycle detector correlation / TV(shared vs independent
   source) — and the shots-to-detect vs the FEASIBLE shot budget (bounded by MCWF cost).
4. **PASS** (above-noise signal at feasible N) ⇒ build the full `CoupledCycleTeacher`.
   **FAIL** (sub-feasible) ⇒ record-level teacher deferred/re-scoped; coupling stays G2 channel-level +
   the teacher emits faithful records without a record-level discrimination claim (honest, per H2).

`[OPEN-3]` the feasible-N budget: how many q17 MCWF runs are practical serially? This sets the whole
viability. Estimate from the L6 timing before committing.

## 5. `CoupledCycleTeacher` object (if G0-at-d3 passes) — `ControlledTeacher` impl

Per the protocol `[CODE audit/certify/types.py:278]`: `sched` (real d3 XZZX), `truth` (evaluator-only:
per-shot `z_traj`, per-cycle `CoupledMechanismParams`, per-substep field), `emit` (§2, `{det,obs}` only +
compiler-seal assert — the G1/G7 constraints from the dense design carry over), `channels`,
`markovian_baseline` (`independent_baseline_trajectory_to_params`, G6 control). Memory-ful source is a
build `[OPEN-4]` (which `nm_source` sampler; source_coupling only fans out).

## 6. Acceptance (G-gates) `[CONTRACT §C]`
- **G0-at-d3** (§4) — pre-build feasibility, gates everything.
- **G1** real d3 XZZX schedule (q17, r10 interior); emit asserts the compiler seal.
- **G2** — ALREADY certified channel-level (`cert_axis1_full_coupling`); the teacher must not regress it.
- **G4/G6** — record faithfulness / ablation, RE-FRAMED as faithfulness (H2 cap): shared vs
  `markovian_baseline` structure difference on records + OFF-source collapse; magnitude reported with class
  (sub-floor is faithful, not a fail).
- **G7** — `{det,obs}`-only payload; latent-scramble invariance.
- **G8** — one tracked runner.

## 7. Build plan (heavy-task discipline; only after G0-at-d3 + user go)
- Builder 1 — the MCWF `params_for_substep` injection (§1), default-None regression-safe.
- Builder 2 — `CoupledCycleTeacher` (§5) + memory-ful source wiring.
- Builder 3 — certs + G-gate runner.
- Separate-lane reviewer before any GPU cert. GPU serial. Commit-gated / staged.

## 8. Recommendation to the user (revised — cost is addressable)

The physics path parallels the already-validated dense design, and cost is NOT a fundamental blocker (§3):
serial trajectories + the 2^N record table are implementation artifacts that **batched MCWF + sparse
records** fix. So the build sequence is:
1. **`[BUILD-A]` Batched MCWF trajectories + sparse sampled-record output** (the cost enabler; run at the
   stable bond ~48 + a positivity guard on the jump-sampling multinomial). Commit-gated; correctness-critical
   (batched MCWF must reproduce the serial per-trajectory distribution — cert vs the serial path).
2. **`[BUILD-B]` Per-round `params_for_substep` injection** (§1) into the carrier program.
3. **G0-at-d3 (signal)** — now measurable at feasible T: per-cycle-varying vs uniform (`markovian_baseline`)
   record-level signal vs shot noise.
4. **`[BUILD-C]` `CoupledCycleTeacher`** if the signal clears; else channel-level (G2) + faithful-emission
   only, honestly (H2).

BUILD-A (batched MCWF) is the biggest piece and the highest-leverage (it also speeds every future d3+
MCWF run). It is a real feature — a trajectory batch axis on the quimb/torch MPS with per-trajectory jump
divergence + bond-per-batch management — but not a rewrite. Recommend: build BUILD-A with a serial-vs-batched
equivalence cert (independent-GT: the batched record distribution must match the serial one), then B, then
the G0-at-d3 signal measurement, then decide on the teacher.

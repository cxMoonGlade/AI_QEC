# Test CODEBOOK — the ECS test/coverage harness at a glance

Plain index of how testing works in `error_coupling_simulator`. Read this before touching a test
batch. Knobs live in **`tests/harness_config.json`** (one visible place). The harness lives WITH the
tests in **`tests/harness/`** (Python — proc/gpu_pool/gate/mutation).

## The idea (the full-coverage program)
Every CPU-pure public unit of the release package gets THREE layers of test, each necessary:
- **L0 structural** — 100% statement + 100% branch per unit (coverage.py). Proves every line ran.
- **L1 property** — Hypothesis faithfulness invariants (CPTP, unit-trace, C∈[0,1], CMI≥0, …). Proves
  behavior over thousands of generated inputs, not one hand-picked case.
- **L2 mutation** — mutmut kill-rate ≥ bar. Proves the asserts DISCRIMINATE (a 100%-covered test with
  a vacuous assert leaves a surviving mutant → red). This is the anti-vacuity layer.
GPU/quimb-bound + expensive-dynamics units get the LIGHTER treatment: structural + a hand KILLER +
their independent-referee equivalence gate (L2 is impractical there — see the timeout note below).

## How to run a batch
```
python tests/harness/gate.py     tests/_support/<batch>_targets.json    # L0+L1 coverage gate
python tests/harness/mutation.py tests/_support/<batch>_targets.json    # L2 mutation gate
```
Each is registry-driven. The gate prints per-unit stmt/branch + PASS/FAIL; mutation prints
`kill_rate` + a survivors JSON. (Legacy `.sh` runners in `outputs/twin_validation/` are being
retired in favour of these.)

## Knobs — `tests/harness_config.json` (ENV-overridable; registry `harness` block overrides per-batch)
| knob | default | env | what |
|---|---|---|---|
| `mutation_gate.kill_rate_bar` | 0.90 | `ECS_MUT_BAR` | min mutmut kill-rate to PASS |
| `mutation_gate.jobs` | all cores | `MUTMUT_JOBS` | mutation parallelism |
| `mutation_gate.timeout_multiplier` | 15 | `ECS_MUT_TIMEOUT_MULT` | mutmut per-mutant timeout = (est+const)×mult. **RAISE for expensive-dynamics batches** so slow-but-finite mutants complete + get killed |
| `mutation_gate.timeout_constant` | 1 | `ECS_MUT_TIMEOUT_CONST` | added to est test time before ×mult |
| `mutation_gate.skip_slow` | true | `STAGE_D_SKIP_SLOW` | skip `@skipif(STAGE_D_SKIP_SLOW)` slow physics pins UNDER MUTATION (gate still runs them) |
| `gpu_pool.pool_size` | auto | `ECS_GPUS` | # GPUs; N → N parallel GPU jobs (each pinned) |
| `coverage_gate.hypothesis_seed` | 0 | — | pinned → deterministic green |

## A registry (`tests/_support/<batch>_targets.json`)
The source of truth for a batch. Keys: `reconcile_modules` (the src files), `covered_by_test_files`,
`canonical_units` (must bijection with `units[]`), `units[]` `{module,qualname,target,exemptions}`,
`out_of_scope` `{qualname:{class,reason,covered_by}}`, optional `requires_gpu`, optional `harness`
override block. The AST audit derives each unit's line set by qualname (no stale line ranges),
reconciles EVERY public unit (registered OR out_of_scope), and refuses a false `gpu_bound` claim on a
torch-less module.

## Conventions (the rules that keep tests honest)
- **faithfulness API** `tests/_support/faithfulness.py`: `assert_discriminates(prop, real, wrong)`
  (KILLER-as-a-method), `assert_pins(actual, independent_recompute)` (pin the VALUE vs an INDEPENDENT
  reimplementation — cures the `sum-of-abs≥0` tautology), `assert_raises_exact(exc, msg, call)` (trip a
  raising guard with the EXACT message — kills the XX-wrap/case/`None` message mutants a substring
  `pytest.raises(match=)` leaves surviving; 9 batches re-rolled a private `_raises_exact` before this),
  structural `assert_cptp/unitary/density/…`.
- **canonical INPUT fixtures** `tests/_support/fixtures.py`: `canonical_rep_code_spec` /
  `canonical_mixed_code_spec` / `canonical_circuit_ir` / `canonical_sealed_schedule` /
  `canonical_stim_circuit` — deterministic VALID inputs to FEED units under test (INPUTS, not
  references — an independent recompute that referees a module's OWN output stays LOCAL). Import these
  instead of re-deriving a rep-code CodeSpec / CircuitIR / compiled SubstepSchedule / stim circuit per batch.
- **DEFENSIVE-ASSERT / dead branch**: an unreachable guard is covered by (extract `_assert_*` seam +
  trip it) + (property proving the legit path). NEVER exempt a branch as "unreachable" without probing
  float underflow / invalid inputs first (the gksl finding).
- **Convergence**: NEVER pin a physical value at an unconverged numerical parameter (n_gh/nmax/bond).
  Converge first, or pin only implementation-consistency (module==independent recompute) and say so.
- **out_of_scope** is for genuine GPU/quimb-bound or retracted units only; a gpu_bound claim is refused
  unless the module imports torch/quimb.
- **slow tests**: mark a slow PHYSICS-convergence pin `@pytest.mark.skipif(os.environ.get("STAGE_D_SKIP_SLOW")=="1")`
  (gate runs it, mutation skips it). For a slow test that IS the discriminator, do NOT skip — RAISE
  `timeout_multiplier` in the batch's registry `harness` block instead.

## Batch registry (status)
| registry | modules | test file | units | L0 | L2 kill | status |
|---|---|---|---|---|---|---|
| `wave2_6_coverage_targets` | frontend/experiments, forward/scalable/{sv_sampler,mps_forward}, _support/fixtures | test_experiments/shotset/mps_seams_units + _support selftest | 19 | 100/100 | 95.4% | committed |
| `stage_d_coverage_targets` | quantum_bath/observables | test_quantum_bath_observables_units | 7 | 100/100 | 90.6% | committed (39caa28) |
| `stage_d_carrier_targets` | quantum_bath/carrier | test_quantum_bath_carrier_units | 9 | 100/100 | 97.3% | committed |
| `stage_d_gksl_crowjoynt_targets` | quantum_bath/{gksl,crow_joynt} | test_quantum_bath_gksl_crowjoynt_units | 8 | 100/100 | 95.7% | committed |
| `stage_d_groundtruth_nulls_targets` | quantum_bath/{ground_truth,nulls} | test_quantum_bath_groundtruth_nulls_units | 12 | 100/100 | 92.7% | committed |
| `stage_d_memwitness_targets` | quantum_bath/memory_witness | test_quantum_bath_memwitness_units | 4 | 100/100 | 91.7% | committed |
| `stage_d_certify_core_targets` | certify/{core,facade,types} | test_certify_core_units | 25 | 100/100 | 94.5% | committed |
| `stage_d_certify_anchors_targets` | certify/anchors/{closed_form,controls,dm_oracle,stim_clifford} | test_certify_anchors_units | 17 (+1 gpu oos) | 100/100 | 92.7% | committed |
| `stage_d_interop_targets` | frontend/interop | test_interop_units | 3 | 100/100 | 95.2% | committed |
| `stage_d_axis1_evidence_guard_targets` | frontend/axis1_evidence_guard | test_axis1_evidence_guard_units | 3 | 100/100 | 97.7% | committed |
| `stage_d_seam_teachers_targets` | mechanisms/seam_teachers | test_seam_teachers_units | 11 | 100/100 | 99.1% | committed |
| `stage_d_axis1_runners_targets` | frontend/{axis1_codespec_runner,axis1_g2_runner} | test_axis1_runners_units | 8 | 100/100 | 98.0% | committed (513d4de) |
| `stage_d_coupled_cycle_targets` | teachers/coupled_cycle | test_coupled_cycle_units | 17 (+1 gpu oos) | 100/100 | 96.4% | committed (9639e75) |
| `stage_d_source_process_targets` | source/process | test_source_process_units | 33 | 100/100 | 95.7% | committed (a3812ea) + norm-cleanup |
| `stage_d_source_coupling_targets` | source/coupling | test_source_coupling_units | 20 | 100/100 | 98.5% | committed (3684974) + norm-cleanup |
| `stage_d_carrier_channels_targets` | carrier/channels | test_carrier_channels_units | 33 | 100/100 | 96.8% | committed (3fcc8b4) + norm-cleanup + `__post_init__` contract |
| `stage_d_noise_spec_targets` | frontend/noise_spec | test_noise_spec_units | 25 | 100/100 | 96.3% | committed (854d848) |
| `stage_d_circuit_ir_targets` | frontend/circuit_ir | test_circuit_ir_units | 23 | 100/100 | 95.6% | committed (4f7cac8) + norm-cleanup |
| `stage_d_record_layout_targets` | frontend/record_layout | test_record_layout_units | 14 | 100/100 | 100.0% | committed (2b1ca53) |
| `stage_d_code_spec_targets` | frontend/code_spec | test_code_spec_units | 17 | 100/100 | 93.9% | committed (286f878) |
| `stage_d_analog_schedule_targets` | frontend/analog_schedule | test_analog_schedule_units | 17 | 100/100 | 96.1% | committed (f38439a) + axis-2 guard (9db34a7) |
| `stage_d_axis1_selection_targets` | frontend/axis1_selection | test_axis1_selection_units | 15 | 100/100 | 97.8% | committed (7ca896d) + `.upper()` de-dup |
| `stage_d_record_schema_targets` | frontend/record_schema | test_record_schema_units | 10 | 100/100 | 100.0% | pending commit |

**Milestone:** `quantum_bath` (40 units, 7 modules) + `certify` (42 units, 7 modules; `DMOracleAnchor.answer`
is the sole GPU `out_of_scope`) are covered at L0 100/100 + L2 ≥0.90. The quantum_bath entropic/negativity-
backflow WITNESSES were RETRACTED + RETIRED 2026-07-07 (→ `retired/`). certify's mutation gaps were the
value-discrimination lesson: the builders hit 100% coverage at ~0.75 kill, a fix pass added ledger/boundary
value-pins → 0.945/0.927 (residuals are empirically-verified equivalents). The **D6–D10 CPU-pure tier is
complete**: interop (0.952), axis1_evidence_guard (0.977), seam_teachers (0.991), axis1_runners (0.980),
coupled_cycle (0.964; the `CoupledCycleTeacher.emit` GPU MC-sampler is the sole `out_of_scope`, mirroring
certify_anchors' `DMOracleAnchor.answer`). **D11 opens Tier-2** (low-coverage, large-surface CPU-pure):
`source/process.py` (33 units incl. 5 `__post_init__`, kill 0.957, 0 exemptions; the `from_fixed_marginal`
`pi1>=1.0` guard — provably dead because `_validate_probability(allow_zero=False)` already rejects `>=1.0`,
initially carried as an audit-validated `defensive_assert` exemption — was REMOVED as a redundant-validation
cleanup, retiring that exemption + its dead-init sibling `_layout_coordinates` `np.zeros((n,0))`).
`source/coupling.py` (D12, 20 units, kill 0.985, 0 exemptions). `carrier/channels.py` (D13, 33 units incl. the
new `MechanismSpec.__post_init__` construction-contract validation, the quantum-channel library, kill 0.968)
— this batch is the cautionary tale for **adversarial residual review**:
authoritative-verify caught TWO real gaps the builder had mis-classified as "equivalent" (12 mutants), both the
same failure mode — a default arg / branch-into-a-raising-guard whose reachability was ASSERTED, not PROBED.
(1) `canonical_single_qubit_axis(default=…)` is live when `value=None`, reachable via an explicit-None param on
an unvalidated `MechanismSpec`; (2) the M13 `channel_axis != operation_axis` raise was tested only via the
explicit `error_axis` route, never the `channel_axis` fallback route. LESSON (now standing): before calling a
default-arg / default-branch mutant "equivalent", PROBE a reachable input (explicit-None value / absent-key
no-fallback); and a raising validation guard must be tripped through EVERY input route that reaches it (100%
branch coverage of the guard ≠ every routing into it exercised). FOLLOW-UP (`__post_init__` construction
contract, +1 unit → 33): `MechanismSpec` now validates at construction (non-empty id, positive num_qubits,
`Mapping` params, and present axis params `operation_axis`/`error_axis`/`channel_axis`/`axis` non-None + a valid
rotation axis), so the finding-(1) explicit-None route is now REJECTED at construction. That makes the non-M14
`mechanism_operation_axis` and M13 `mechanism_error_axis` `default=` args genuinely DEAD (their fallback chains
bottom out at a validated axis / the instruction default, never None) — 4 mutants reclassified killable→equivalent
(76→80 survivors, 0.9676→0.9659). The M14 op-axis `default="rx"` stays killable via the still-unconstrained
`params['instruction']` None route. (`__post_init__`, like `audit_dict`, is a class method → not mutated by mutmut
here, so it carries no L2 mutants; its correctness is pinned by 100% L0/L1 branch coverage + exact-message asserts.)
Next: frontend IR/schema/stim clusters,
`mechanisms`, `numerics` as D14–D20. Full work-list: `docs/twin_validation/l3_release_package_unit_inventory.md`.

## Offloading heavy mutation (spark)
Very expensive-dynamics batches can offload the full mutation to the `ssh spark` compute node
(minimal venv `~/ecs_mut_env`, no torch — conftest guards it), with `timeout_multiplier` raised so
the slow-but-finite mutants run to COMPLETION and are KILLED — never masked as timeouts (a timeout
counts as not-killed; the 2026-07-07 memwitness lesson: at 15× timeout 123 real survivors hid as
timeouts). Invoke the same `tests/harness/mutation.py <registry>` there. NB memwitness, after the
entropic-witness retirement, is CPU-cheap enough to mutate LOCALLY (0.917 kill on the 4 live units).

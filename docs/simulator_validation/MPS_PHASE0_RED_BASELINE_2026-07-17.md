# Restricted MPS Phase 0 RED baseline — 2026-07-17

## Status

Disposition: **expected RED; first tracer frozen; no `src/**` change**.

Repository source baseline: `HEAD 29cf949`. This packet instantiates Phase 0 of
[`MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md`](MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md).
It does not authorize or contain a source fix. The scientific dispositions remain
`RECORD_BRIDGE_OPEN` and `PRODUCTION_PRUNING_CODE_BLOCKED`; PEPS/FET is unchanged.

Phase 0 uses vertical tracer bullets. It does not add the remaining defect tests while the first
behavior is RED, because doing so would create a horizontal test-only slice detached from each source
repair.

## MPS-002 public-entry tracer

The tracer calls the public
`axis1_mcwf_mps_state_record_execution_manifest(...)` entry point with the smallest current public
over-cap static-union fixture:

- six qubits, because the dense Axis-1 cluster cap is five;
- declared static-ZZ edge `(0, 5)` so all six sites remain in one visible union;
- local T1 rate `gamma_1_per_ns=0.05` over `dt=20 ns`;
- initial state `|111111>`;
- one trajectory, seed 11, one microstep;
- `mass_residual_budget=None`.

A five-qubit negative control is dense-checkable and is rejected by the dense oracle, so it cannot
reproduce the over-cap acceptance defect.

### Independent expected value

Each of the six T1 jump candidates has raw mass `dt * gamma = 1`. The first-order no-jump candidate
has squared norm

```text
(1 - gamma*dt/2)^(2*6) = (1/2)^12 = 1/4096.
```

Therefore the independently expected candidate-mass residual is

```text
abs(6 + 1/4096 - 1) = 5 + 1/4096 = 5.000244140625.
```

### Observed public behavior

| Field | Expected | Observed at `29cf949` |
|---|---:|---:|
| runtime `probability_mass_residual_max` | `5.000244140625` | `5.000244140567044` |
| record-frequency `total_probability_residual` | `0.0` | `0.0` |
| top-level verdict | `fail` | `pass` |
| `passed` | false | true |
| restricted acceptance | false | true |

The independent numerical assertion passes within `1e-9`. The test fails only when it reaches
`assert manifest["verdict"] == "fail"`. This isolates the error: empirical record-count
normalization is green even though MCWF candidate probability mass is grossly invalid.

Durable tracer:
[`tests/test_collective_decay_finite_step_guard.py`](../../tests/test_collective_decay_finite_step_guard.py).

## Strict owner registry

[`restricted_mps_coverage_targets.json`](../../tests/_support/restricted_mps_coverage_targets.json)
reconciles five registered restricted-MPS source owners plus the current MCWF certification support
module. It contains 13 public units, requires GPU execution, sets statement and branch targets to
100%, and contains no exemptions.

The support module `axis1_mcwf_dense_certification.py` is not relabeled as a service owner by this
registry. Formal ownership movement remains a later phase.

### Measured coverage baseline

The focused registry execution completed `240 passed, 1 skipped, 1 failed`; the only pytest failure
was the MPS-002 tracer. Scoring the emitted coverage JSON independently produced four fully covered
units and nine honest RED units:

| Public unit | Statement | Branch |
|---|---:|---:|
| `normalize_mps_max_bond` | 100% | 100% |
| `axis1_mcwf_mps_state_record_contract_manifest` | 100% | 100% |
| `axis1_qt_mps_state_record_contract_manifest` | 100% | 100% |
| `axis1_qt_mps_restricted_evidence_bundle_manifest` | 100% | 100% |
| `apply_capped_two_site_unitary` | 88.24% | 70.00% |
| `commit_mps_candidate_` | 76.67% | 71.43% |
| `axis1_mcwf_mps_state_record_execution_manifest` | 95.00% | 83.33% |
| `axis1_qt_mps_restricted_execution_manifest` | 86.67% | 75.00% |
| `axis1_qt_mps_bond_sweep_manifest` | 92.86% | 50.00% |
| `axis1_qt_mps_trajectory_seed_sweep_manifest` | 84.21% | 50.00% |
| `axis1_qt_mps_resource_probe_manifest` | 90.48% | 50.00% |
| `dense_jointL_record_certification` | 72.22% | 50.00% |
| `restricted_acceptance_policy` | 96.15% | 90.00% |

Mutation status is `NOT_RUN_SAFETY_BLOCK`, not pass or fail. These six modules total thousands of
lines, and the current GPU-aware mutation harness leases one GPU without forcing a single mutmut
worker. The only authorized future invocation is explicit serial execution with `--jobs 1`; mutation
will not be launched while the first behavior and coverage gate are RED.

## Reproduction commands

```bash
conda run -n ecs python -m pytest -q \
  tests/test_collective_decay_finite_step_guard.py::test_mcwf_overcap_none_budget_cannot_pass_restricted_acceptance

conda run -n ecs python tests/harness/gate.py \
  tests/_support/restricted_mps_coverage_targets.json

conda run -n ecs python tests/harness/coverage_audit.py \
  --registry tests/_support/restricted_mps_coverage_targets.json \
  outputs/simulator_validation/logs/restricted_mps_coverage_targets_coverage.json
```

Evidence outputs:

- `outputs/simulator_validation/logs/restricted_mps_coverage_targets_gate.log`;
- `outputs/simulator_validation/logs/restricted_mps_coverage_targets_coverage.json`.

The dynamic service plan still expands successfully, and `tools/gen_code_map.py --check` passes for
27 registered services. No intentionally RED test is promoted as a passing service certification.

## Provenance

| Bound file | SHA-256 |
|---|---|
| `src/error_coupling_simulator/frontend/_mps_actual_split.py` | `af20bad15c7e4f98445be450bfd8ec2143923c08e931f003e73d551ce0e3e602` |
| `src/error_coupling_simulator/frontend/axis1_mcwf_mps_contract.py` | `67c1a74c14e95953e4067de21c9171553a0e6a6a6da4f0f22dc6ba60311b2ae3` |
| `src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py` | `b681f580b99233f3c8d05c6bfc934cb65ee35fafdce72e1bb02c6c62863bcc85` |
| `src/error_coupling_simulator/frontend/axis1_qt_mps_contract.py` | `0ef010786a8ffb7e3a787c5f3b73d7fe79af80e227adff1cc5c32af81c220ba5` |
| `src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py` | `392d033f35d1e35ef4a83ccc71cc20f74ee28e60d0912c883cb8d16ba8a71ceb` |
| `src/error_coupling_simulator/frontend/axis1_mcwf_dense_certification.py` | `e4d2c2d48b60ae4c2da4ce3b0451f6cf1edfb80cda788244ed426dbf3ac7a87b` |
| `tests/_support/restricted_mps_coverage_targets.json` | `3c99651bd56ea94a5da095646c5ea8c60411ad4f402d8e9e4c860947bd5ca642` |
| `tests/test_collective_decay_finite_step_guard.py` | `6d0e7b3b5bdf50b08f9c56e8206a4893d1cd520ba6ce3d173b29322469c9bae2` |

## Next gate

The next vertical slice is Phase 1 for `MPS-002` only. It requires a separately reviewed and
confirmed `src/**` diff. The repair must distinguish:

- `mass_residual_budget=None`: execution may remain available for convergence diagnostics, but cannot
  produce restricted `pass`;
- NaN or Inf budget: reject before execution;
- finite runtime residual above the declared budget: reject regardless of Record normalization or
  dense-oracle availability.

The not-yet-durable MPS-003 counterexamples remain queued behind this RED-to-GREEN slice.

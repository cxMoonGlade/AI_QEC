# Restricted MPS Phase 1A false-green firewall — 2026-07-17

## Status

Disposition: **MPS-002 GREEN at the focused public and policy gates; Phase 1 and the full repair
program remain open**.

Repository baseline is `HEAD 29cf949`. The Phase 1A worktree is intentionally uncommitted while this
diff is reviewed. This packet implements only the MPS-002 vertical slice from
[`MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md`](MPS_REPAIR_AND_CONSOLIDATION_PLAN_V3_2026-07-17.md).
It does not claim that MPS-003, MPS-014, the strict coverage gate, the full service aggregate, or any
production-pruning gate is green. PEPS/FET is unchanged.

The reviewed `src/**` scope is exactly:

- `src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py`;
- `src/error_coupling_simulator/frontend/axis1_mcwf_dense_certification.py`;
- `src/error_coupling_simulator/frontend/README.md`.

No external baseline repository was modified. The repository-owned YASTN adapter and its test live
outside `src/**`.

## Violated invariant and repair

The Phase 0 tracer proved that empirical Record-count normalization could be zero while the raw MCWF
candidate mass was grossly invalid. Before this repair, `mass_residual_budget=None` also disabled the
preflight guard, and a dense-oracle-over-cap path could turn that execution into a positive restricted
acceptance.

For the frozen six-site fixture,

```text
initial state                 = |111111>
gamma_1 * dt                 = 1
each of six jump masses      = 1
no-jump mass                 = (1 - gamma_1*dt/2)^(2*6) = 1/4096
raw candidate mass           = 6 + 1/4096 = 6.000244140625
candidate-mass residual      = abs(raw candidate mass - 1)
                             = 5 + 1/4096 = 5.000244140625
```

The runtime value remains `5.000244140567044`, within `5.8e-11` of the independent value. The repair
does not hide or renormalize it; it makes the value mandatory acceptance evidence.

### Before/after behavior

| Case | Before `29cf949` | Phase 1A behavior |
|---|---|---|
| six sites, residual `5.000244...`, `mass_residual_budget=None` | completed and restricted `pass` | completed diagnostic; `not_evaluated`; verdict `fail` |
| finite budget, runtime residual above budget | Record normalization could still support a pass path | `rejected`; verdict `fail`; runtime residual and budget remain separate ledger fields |
| finite budget, runtime residual within budget, dense oracle over cap | positive over-cap fallback could accept | completed diagnostic; certification `unavailable`; verdict `fail` |
| NaN or `+/-Inf` budget | nonfinite bypass/coercion surface | rejected before device execution with `ValueError` |
| missing runtime candidate-mass evidence | policy could omit the physical mass check | mandatory-key failure; cannot certify |

### Frozen state machine

| Execution | Certification | Verdict | Diagnostic only | Meaning |
|---|---|---|---|---|
| blocked | `not_evaluated` | `fail` | false | input, support, or preflight blocked execution |
| completed | `rejected` | `fail` | false | mandatory evidence was present and failed |
| completed | `not_evaluated` | `fail` | true | `mass_residual_budget=None` convergence diagnostic |
| completed | `unavailable` | `fail` | true | execution succeeded but the required independent oracle was unavailable |
| completed | `accepted` | `pass` | false | every mandatory runtime, dense, seed, and requested truncation gate passed |

`pass` remains equivalent to `accepted_for_restricted_execution=true`. Record-frequency
`total_probability_residual` and runtime raw-candidate `probability_mass_residual_max` now have
different names, fields, and acceptance roles.

## Source and schema changes

- Normalize `mass_residual_budget` before device acquisition or execution. `None` remains an explicit
  diagnostic request; bool, negative, and nonfinite values are invalid.
- Make `execution["jump_sampling"]["probability_mass_residual_max"]` mandatory in restricted
  certification and require it to be finite, nonnegative, and within the declared finite budget.
- Remove the positive over-cap dense-oracle fallback. Record-count normalization is never an
  independent physical oracle.
- Separate `execution_status`, `certification_status`, and `diagnostic_only` at the top level and in
  the policy payload.
- Bump the MCWF execution schema from `v1` to `v2` and the restricted acceptance policy schema to
  `v4`, including blocked manifests.
- Skip the expensive dense certification for an explicit `None`-budget convergence diagnostic,
  because that path is incapable of acceptance by construction.

The last item is a correctness-preserving early exit, not the performance-optimization phase: its
semantic state is frozen by public tests, and no accepted path is skipped.

## Independent and external numerical evidence

### Hand reconstruction

The hand calculation above is independent of both the production carrier and external libraries. It
is asserted by the public-entry regression with absolute tolerance `1e-9`.

### YASTN product-MPS comparator

The repository-owned neutral adapter
[`run_yastn_mcwf_mass_comparison.py`](../../scripts/external_baselines/run_yastn_mcwf_mass_comparison.py)
ran in `ecs-baseline-yastn` against pristine clone commit
`595bd802ba0753a187b4bf7fd5c6d5007c0170d0`, YASTN
`1.6.2.dev384+g595bd802b`.

| YASTN quantity | Observed |
|---|---:|
| initial MPS norm squared | `1.0` |
| no-jump MPS norm squared | `0.000244140625` |
| six jump MPS norms squared | six times `1.0` |
| raw candidate mass | `6.000244140625` |
| candidate-mass residual | `5.000244140625` |
| every state bond dimension | `1` |
| omitted-jump corruption | detected |

Artifact:
[`yastn_mcwf_candidate_mass/report.json`](../../outputs/simulator_validation/diagnostics/yastn_mcwf_candidate_mass/report.json),
SHA-256 `6b9bab8a194123818b2d01e0f7a76048648ede5afdfd45241bf619103e9862fe`.

This excludes truncation as an explanation for the residual and independently confirms the raw mass
arithmetic. It does **not** certify our trajectory sampling, schedule, Record law, or acceptance
policy.

### Qiskit Aer MPS comparator

The committed neutral Aer adapter was rerun in fresh `ecs-baseline-aer` worker processes against
pristine clone `837c3ef3c39248aae936580360c22224dcefb265`, with Qiskit Aer `0.17.2` and Qiskit
`2.5.0`. All 15 rows and the gate-corruption falsifier passed.

For `mixed_entangling_6`, full-rank Aer agrees with the independent dense state at fidelity `1.0`,
while fixed caps demonstrate that a small bond cap is not intrinsically safe:

| Policy | Fidelity to dense | Aer discarded-weight sum |
|---|---:|---:|
| full rank | `1.0` | `0.0` |
| cap 1 | `0.1652338530840565` | `1.363733...` |
| cap 2 | `0.3718982761325503` | `0.7677819...` |

Artifact:
[`aer_mps_comparison/report.json`](../../outputs/simulator_validation/diagnostics/aer_mps_comparison/report.json),
exact-byte SHA-256 `3b4544786cdf1b513e47d89005e2dbab217737d8043caa1ef3005646ba111377`.

Aer checks state evolution and finite-bond damage on neutral unitary circuits. It does **not** check
MCWF candidate mass or our Record semantics.

### Quimb actual-split diagnostic

The canonical current-source replay was deliberately not bypassed. It refused the uncommitted source
diff with:

```text
RuntimeError: nontrivial diagnostic requires committed clean binding files;
git status is 'M src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py'
```

Therefore the retained Quimb result is historical wiring evidence only. A source-bound current replay
is pending a reviewed clean checkpoint; this is a provenance gate, not a numerical failure.

## Verification

Focused registered regression command:

```bash
conda run -n ecs python -m pytest -q \
  tests/test_axis1_mcwf_dense_certification.py \
  tests/test_collective_decay_finite_step_guard.py \
  tests/test_mps_actual_split_helper.py \
  tests/test_simulator_axis1_schedule.py
```

Result: **247 passed, 1 skipped, 27 warnings in 12.52 s**.

The YASTN adapter contract test adds **1 passed in 0.08 s**. `python -m compileall` for both changed
Python source files passed. `git diff --check` passed. `python tools/gen_code_map.py --check` reports
27 valid services and current input hash `117e2041dca0...`.

The strict restricted-MPS coverage gate remains intentionally RED:

- 13 canonical units and 13 registered units;
- no missing unit, stray registration, or exemption error;
- 9 units below the frozen 100% statement/branch target;
- changed MCWF public execution: `95.35%` statement / `85.71%` branch;
- changed restricted acceptance policy: `92.77%` statement / `85.71%` branch.

This is recorded as remaining work, not lowered or relabeled as green. Critical mutation testing also
remains safety-blocked until correctness and coverage reach their declared gate.

The attempted 73-item fresh-process service aggregate was interrupted externally before it could
write `summary.json`; it has no aggregate verdict and cannot be resumed. Fifty completed logs were
green, one long PEPO log was still empty at interruption, and 22 GPU items had not started. A clean
full rerun is deferred until the MPS correctness phases stabilize. The current aggregate also retains
the separately declared PEPS/FET scientific RED; MPS work must introduce no additional failure.

## Bound file hashes

| File | SHA-256 |
|---|---|
| `axis1_mcwf_mps_execution.py` | `2c903aa2402e497b6fda581118c7ad5b630ff1e85e0b1c82b9b07a61ff68b067` |
| `axis1_mcwf_dense_certification.py` | `b5c187e53e46f2435a7ff5e9a398aa643d9608934a8828a40633b2cdfb3f8c76` |
| frontend `README.md` | `fb31a85ca30081ca2e6d39e2bccb92095f7e778c52889b6364359ab2037a4378` |
| YASTN adapter | `a036c93692448c9ff5a5f34951be36de66511227c64315c8907bd539beaf112b` |
| YASTN adapter test | `6851a1eccd309d15124ac6913949be5ecce5e85a13f725a4b0b03c329391f499` |
| restricted-MPS registry | `3c99651bd56ea94a5da095646c5ea8c60411ad4f402d8e9e4c860947bd5ca642` |

## Next gate

Phase 1B is MPS-003 plus the early fail-closed half of MPS-014. Before its source change, durable RED
tests must cover every NaN/Inf/bool/missing/negative/equality edge in the dense, seed, bond,
truncation, and resource gates. The QT resource budget must be checked before exponential outcome or
Record allocation. Performance profiling and general optimization remain prohibited until all
correctness phases and independent numerical equivalence gates are green.

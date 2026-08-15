# Restricted MPS Phase 1A false-green firewall — 2026-07-17

## Status

Disposition: **MPS-002 GREEN at the focused public and policy gates; Phase 1 and the full repair
program remain open**.

Repository baseline was `HEAD 29cf949`; the source-fix checkpoint is
`22b7150cc49bbcf8d6e03d23be72461791935ff5` and the external-baseline hardening checkpoint is
`56b0aaa72c4a6c91673346e4179ea0b86e012bca`. This packet implements only the MPS-002 vertical slice from
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

## Numerical evidence by epistemic role

The evidence classes below are intentionally distinct. The hand reconstruction is an independent
reference; YASTN and Qiskit Aer are isolated external comparators; Quimb is the repository's
production tensor backend and is retained only as source-bound backend-wiring evidence.

| Evidence | Executes repository MPS code | Independent numerical role |
|---|---:|---|
| hand reconstruction | no | raw candidate-mass oracle for the frozen fixture |
| isolated YASTN | no | external MPO-on-product-MPS candidate-mass comparator |
| isolated Qiskit Aer | no | external entangling-MPS and explicit-cap comparator against dense |
| pinned Quimb backend diagnostic | no repository helper; yes production dependency | backend wiring only; not external |

No row currently performs the later required three-leg comparison of repository helper, external
implementation, and independently formulated dense oracle on the same fixture.

### Independent reference: hand reconstruction

The hand calculation above is independent of both the production carrier and external libraries. It
is asserted by the public-entry regression with absolute tolerance `1e-9`.

### Isolated external comparator: YASTN product-MPS

The committed repository-owned neutral adapter
[`run_yastn_mcwf_mass_comparison.py`](../../scripts/external_baselines/run_yastn_mcwf_mass_comparison.py)
ran in `ecs-baseline-yastn`. The installed YASTN distribution is VCS-bound by its
`direct_url.json` to frozen pristine clone commit
`595bd802ba0753a187b4bf7fd5c6d5007c0170d0`, and reports version
`1.6.2.dev384+g595bd802b`. `PYTHONPATH` was absent, the project package was not importable or imported,
and neither the project root nor the external clone root was present on resolved nonempty `sys.path`.
Before numerical construction, the adapter verified all 104 hashed `RECORD` entries, compared all 93
clone/installation-corresponding Python files bidirectionally, and obtained the same source-tree
manifest SHA-256
`9284cee945d91ae30f557d7f5e7675dea7c8d780a7870bb0576eef09abfe950b`.
The only installed-only Python file is the allowlisted vcs-versioning output `yastn/_version.py`; its
version, short commit, and `RECORD`-bound SHA-256 were checked explicitly.

The comparator constructs `K0` and each T1 jump as public YASTN MPOs and applies them to the initial
MPS; it does not preconstruct the expected answer state.

| YASTN quantity | Observed |
|---|---:|
| initial MPS norm squared | `1.0` |
| no-jump MPS norm squared | `0.000244140625` |
| six jump MPS norms squared | six times `1.0` |
| raw candidate mass | `6.000244140625` |
| candidate-mass residual | `5.000244140625` |
| every state bond dimension | `1` |
| wrong `sm()` jump-operator corruption | detected |

Artifact:
[`yastn_mcwf_candidate_mass/report.json`](../../outputs/simulator_validation/diagnostics/yastn_mcwf_candidate_mass/report.json),
exact-byte SHA-256 `a92e2ca63dbc1608b977c961e9506e0df99a65c1ea67abb991bdf774371222a9`.
An independent second invocation was byte-identical.

This excludes truncation as an explanation for the residual and independently confirms the raw mass
arithmetic for this bond-one product-state fixture. It does **not** test entangling MPS truncation or
certify our trajectory sampling, schedule, Record law, or acceptance policy.

### Isolated external comparator: Qiskit Aer MPS

The committed neutral Aer adapter ran fresh `ecs-baseline-aer` worker processes using the installed
Qiskit Aer `0.17.2` distribution and Qiskit `2.5.0`. The artifact captures the installed
distribution's `RECORD` hash, selected Python-wrapper and native-controller hashes, and import
location. A separate pristine clone at
`837c3ef3c39248aae936580360c22224dcefb265` is retained only as a source reference; the artifact
explicitly does not claim that the installed distribution came from or is cryptographically bound to
that clone. The repository orchestrator launched all 15 rows in separate worker processes; all workers
returned zero, avoided timeout, verified process-group cleanup, and reported one identical runtime
fingerprint. All numerical checks and the gate-corruption falsifier passed.

For `mixed_entangling_6`, full-rank Aer agrees with the independent dense state at fidelity `1.0`,
while fixed caps demonstrate that a small bond cap is not intrinsically safe:

| Policy | Fidelity to dense | Aer discarded-weight sum |
|---|---:|---:|
| full rank | `1.0` | `0.0` |
| cap 1 | `0.1652338530840565` | `1.363733...` |
| cap 2 | `0.3718982761325503` | `0.7677819...` |

Artifact:
[`aer_mps_comparison/report.json`](../../outputs/simulator_validation/diagnostics/aer_mps_comparison/report.json),
exact-byte SHA-256 `2c8913ab6e42bead87fcd66fc57a630d8da07fb8c4319f62a29a03cbba5f16f9`;
internal content SHA-256 `688efa5d471ee96f32a6dfc690d7037928e7205bc7161186f1561c60fefcb1fb`.
An independent second orchestration was byte-identical.

Aer checks its own state evolution and finite-bond damage against the independent dense oracle on
neutral unitary circuits. It does **not** execute or bind our repaired MPS source, and therefore is a
scope-limited external comparator rather than numerical validation of the Phase 1A repair. The later
external-validation phase must add a current-clean-source third leg on the same neutral fixtures.

### Quimb backend `auto-mps` wiring diagnostic — not an external baseline

Before the checkpoint, the canonical replay correctly refused an uncommitted declared binding. After
checkpoint `22b7150`, the pinned Quimb 1.14.0 high-level
`MatrixProductState.gate_(..., contract="auto-mps")` path ran in a fresh CUDA worker with every
declared diagnostic binding committed and clean; worker cleanup and the diagnostic-scope verdict
passed. Quimb is the backend used by this repository, so this run is not an independent external
comparison. It also does not call the repository-owned
`_mps_actual_split.apply_capped_two_site_unitary` helper used by the current finite-bond production
seams.

| Fixture | Actual Quimb splits | Dense cut count | Fidelity |
|---|---:|---:|---:|
| nonadjacent CNOT, cap 1 | `7` | `4` | `0.5000000000000001` |
| nonadjacent CNOT, exact cap 8 | `7` | `4` | `1.0` |

Artifact:
[`mps_actual_split/result.json`](../../outputs/simulator_validation/diagnostics/mps_actual_split/result.json),
exact-byte SHA-256 `5364b1152aac769e3c50ce5bf2ccdb590c2cd432827b20a5f71e0e03ab46ad79`;
fixture artifact SHA-256 `b05369763a99a2de6bf0b825e975e41ef08641970cc6dd292b261f022bf7c2ac`.

For these frozen one-operation 4–6-qubit fixtures only, the artifact establishes that the pinned
high-level Quimb auto-swap path makes seven rank-revealing split calls for the distance-four CNOT,
whereas a dense post-gate Schmidt summary contains four spatial cuts, and it reports the stated
fidelities against an independently formulated NumPy dense target. This is backend-wiring evidence.
It does not establish equivalence with the repository-owned finite-bond production helper, a global
truncation-error bound, MCWF probability-mass correctness, or Record-law fidelity.

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

The Aer and YASTN adapter contract tests add **13 passed, 1 skipped in 0.12 s**. `python -m compileall`
for the changed Python source files passed. `git diff --check` passed. The command
`python tools/gen_code_map.py --check` reports 27 valid services and current input hash
`117e2041dca0...`.

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
| YASTN adapter | `9baff8293075b3d7d709490c0ced4d2eecdb700f915a88406e42f20f1a4f0ad3` |
| YASTN adapter test | `df240d1a4817ca60a79a73b4597466042081f7a0611a45b09cd620bd76577b54` |
| Aer orchestrator | `829ff609256401d7ae6f56f1b5cd1e5797dee57447180a38a01dc6ade05b0dae` |
| Aer protocol | `5ceb84dca6270296528916063c956a2132c0c0db5a0f61eda18af7e976ca7f27` |
| Aer worker | `fdae382d4e90dd1111cfa43258b7aa66fc069d6bc5ae2b6402324209dbc7f858` |
| Aer adapter test | `b94aef298a02f5e1495110f41070b611486c8e8c13dfd43d5e723804f6ac8f2b` |
| restricted-MPS registry | `3c99651bd56ea94a5da095646c5ea8c60411ad4f402d8e9e4c860947bd5ca642` |

## Next gate

Phase 1B is MPS-003 plus the early fail-closed half of MPS-014. Before its source change, durable RED
tests must cover every NaN/Inf/bool/missing/negative/equality edge in the dense, seed, bond,
truncation, and resource gates. The QT resource budget must be checked before exponential outcome or
Record allocation. Performance profiling and general optimization remain prohibited until all
correctness phases and independent numerical equivalence gates are green.

# Test codebook

This file describes the current executable test boundary for
`error_coupling_simulator`. The binding product contract is `docs/SIMULATOR.md`; the
machine-readable service/acceptance inventory is `docs/service_status.json`.

## Test surfaces

- `pytest tests/` is the repository engineering regression suite. Passing it does not by itself
  establish scientific faithfulness.
- `python tests/harness/service_acceptance.py` runs every unique acceptance file declared by a
  current service. Each file gets a fresh process.
- `python tests/harness/service_acceptance.py --list` prints the immutable lane, environment, and
  file plan without running project code.
- `python tools/gen_code_map.py --check` validates service owners, public entry points, acceptance
  paths, dependency declarations, execution lanes, reverse module coverage, and the absence of
  executable imports or patch targets into the retired product namespace.

Service acceptance uses three non-overlapping resource lanes:

- `cpu_light`: bounded subprocess concurrency.
- `cpu_exclusive`: serial host execution for memory- or BLAS-heavy tests.
- `gpu_serial`: serial execution under the cross-process GPU lease.

The default environment is `ecs`. Tests for an explicitly isolated optional runtime use the
per-file environment override declared in the service catalog.

`test_finite_rtn_free_induction_diagnostic.py` is a CPU-exclusive research diagnostic for the
current finite-RTN source owner. Its post-result contract is in
`docs/simulator_validation/finite_rtn_free_induction_diagnostic_contract_2026-07-15.md`; a pass does
not assign CP-divisibility or BLP status to the production QEC channel or record.

`test_literature_tools.py` protects developer-tooling trust boundaries rather than a simulator
service. Its falsifiers cover explicit-manifest admission, source-PDF and audit-packet hashes,
one-fact locators and checked pages, empty-corpus refusal, project-inference injection, stale live
corpora, and corrupted RAG/KG text, claims, counts, hashes, IDs, relationships, statistics, and
endpoints. Trusted build/query paths have no artifact-verification bypass.

## Coverage and mutation registries

Current registries are the JSON files matching `tests/_support/*_targets.json`. A registry names:

- `reconcile_modules`: exact installed modules owned by the batch.
- `covered_by_test_files`: exact executable test files.
- `canonical_units`: public units that must match `units` one-to-one.
- `units`: per-unit statement/branch targets and any explicit exemptions.
- `out_of_scope`: bounded units that cannot run in that registry's execution topology.
- optional `requires_gpu` and local harness overrides.

Run one registry with:

```bash
python tests/harness/gate.py tests/_support/<batch>_targets.json
python tests/harness/mutation.py tests/_support/<batch>_targets.json
```

The coverage audit derives line and branch sets from the current AST. It fails on missing modules,
missing test files, duplicate units, stale qualified names, unclassified public units, or an
unsupported exemption. JSON registries are configuration, not measured test records; measured
results must be regenerated from the current checkout.

## Test disciplines

- Structural coverage executes every reachable statement and branch; it does not prove that an
  assertion discriminates correct from corrupted behavior.
- Property tests exercise physical and data-contract invariants across generated inputs.
- Mutation tests verify that assertions reject meaningful code perturbations. Timeouts and
  `no_tests` outcomes remain non-killed and never improve the score.
- Independent-reference checks must reconstruct the expected value without calling the
  implementation path being checked.
- A corruption falsifier must demonstrate that the test fails for an intentionally wrong physical
  operation, record fold, state, or probability rule.
- Structural zeros remain exact. Numerical floors may not manufacture physical probability mass.
- GPU-only and optional-dependency tests use explicit markers with a concrete reason. A scientific
  failure must never be converted into a skip.
- Current tests import `error_coupling_simulator` directly. Detection of retired symbols is
  fail-closed and spells the forbidden token from string fragments so the retired vocabulary is not
  reintroduced as an active source token.

## Shared support

- `tests/_support/faithfulness.py` provides discriminating, pinning, exact-error, and physical-state
  assertions.
- `tests/_support/fixtures.py` provides deterministic valid inputs and explicit precondition/control
  helpers. Shared inputs are not independent references.
- `tests/harness/proc.py` supervises process groups and log capture.
- `tests/harness/gpu_pool.py` owns cross-process GPU admission.
- `tests/harness/coverage_audit.py`, `gate.py`, and `mutation.py` enforce registry contracts.
- `tests/harness_config.json` owns execution and gate settings.

## Before changing a test batch

1. Read the owning source module and its required owner README.
2. Read the matching registry and every listed test file.
3. Confirm the service catalog still assigns the module and test to the intended current service.
4. Add or update the smallest independent counterexample before weakening a tolerance or guard.
5. Run the focused tests, the registry gate when applicable, the service-plan validation, and then
   the repository suite before claiming completion.

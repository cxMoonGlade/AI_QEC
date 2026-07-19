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

- `cpu_light`: CUDA-hidden, one-thread children with at most four concurrent subprocesses, further
  bounded by CPU count and `MemAvailable`.
- `cpu_exclusive`: CUDA-hidden serial host execution for memory-heavy tests.
- `gpu_serial`: serial fresh-process execution under exactly one cross-process GPU lease; CPU
  concurrency is never inherited.

The default environment is `ecs`. Tests for an explicitly isolated optional runtime use the
per-file environment override declared in the service catalog. The two external MPS adapters also
declare their nested `ecs-baseline-aer` and `ecs-baseline-yastn` environments. Every acceptance child
removes `PYTHONPATH` and disables user-site imports. Checkpoint policy binds the resolved Conda
executable and path-bound Conda/pip metadata for all direct and nested environments.

The stable acceptance checkpoint is bound to the repository input snapshot, lane-major semantic
plan, stop/timeout/CPU policy, parent runtime switches, Python import isolation, and runtime
fingerprints. Each resumable row also authenticates its task identity, deterministic log name and
log hash, terminal pytest return code, and process-group cleanup. Only a contiguous prefix is reused;
corruption or provenance drift fails before task or GPU-lease admission. Timeouts, worker errors,
missing cleanup, and non-pytest/native-fatal exits are not resumable. Summary publication is atomic,
and a terminal summary can reconcile a checkpoint left behind in the post-publication crash window.

`test_finite_rtn_free_induction_diagnostic.py` is a CPU-exclusive research diagnostic for the
current finite-RTN source owner. Its post-result contract is in
`docs/simulator_validation/finite_rtn_free_induction_diagnostic_contract_2026-07-15.md`; a pass does
not assign CP-divisibility or BLP status to the production QEC channel or record.

`test_literature_tools.py` protects developer-tooling trust boundaries rather than a simulator
service. Its falsifiers cover explicit-manifest admission, source-PDF and audit-packet hashes,
one-fact locators and checked pages, empty-corpus refusal, project-inference injection, stale live
corpora, and corrupted RAG/KG text, claims, counts, hashes, IDs, relationships, statistics, and
endpoints. Trusted build/query paths have no artifact-verification bypass.

`test_external_aer_mps_comparison.py` and
`test_external_yastn_mcwf_mass_comparison.py` protect repository-owned neutral adapters for isolated,
external baselines. Both run in isolated environments. YASTN is source/commit-bound to its pristine
clone. Aer records installed-wheel provenance and separately verifies a pristine reference clone,
but does not claim wheel-to-clone identity. Aer checks independent dense/unitary state evolution and
finite-bond damage; YASTN checks the frozen product-MPS MCWF candidate-mass arithmetic and an
omitted-jump falsifier. Canonical service acceptance supplies exact file-local opt-in flags, so both
test files run their isolated external subprocess rather than only helper contracts. Neither
external library is a QEC Record-law or restricted-acceptance oracle.
`test_mps_three_leg_comparator.py` separately checks repository actual splits and Quimb public
wiring against independent dense NumPy state math; the Quimb leg is not an independent scientific
oracle.

`test_restricted_mps_benchmark.py` protects an engineering-only five-workload instrument. A benchmark
row passes only when its exact public outcome matches the catalog: QT exact, QT sampled, and capped
MCWF must remain accepted; lossy QT cap one must remain rejected; true-over-cap mixed-dimensional
MCWF must remain unavailable. Thus instrument `passed=true` is not safe-pruning evidence. CUDA peak
statistics are reset before each invocation, but the reported value is the absolute allocator peak
and includes allocations retained after warmup; it is not an invocation delta. RSS is the cumulative
process high-water within each fresh workload worker.

## Coverage and mutation registries

Current registries are the JSON files matching `tests/_support/*_targets.json`. A registry names:

- `reconcile_modules`: exact installed modules owned by the batch.
- `covered_by_test_files`: exact executable test files.
- `canonical_units`: named units that must match `units` one-to-one. These are normally public
  units; a private authentication helper may be included only when it is deliberately registered
  and directly tested.
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

`restricted_mps_coverage_targets.json` reconciles twelve modules and registers 51 canonical units:
48 public units plus three private Record-payload authentication helpers. Every unit has 100%
statement and branch coverage with no exemptions. The authoritative
mutation topology is `restricted_mps_mutation_suite.json`: seven CPU-only mechanics/schema modules
run through stock mutmut with exactly four workers and CUDA hidden, then five ordered, single-module
GPU execution/certification shards run one after another. Every GPU shard has `jobs=4`, acquires
one lease, runs four concurrent fresh clean-control replicas for admission, and then uses fixed waves
of at most four fresh pytest processes on that pinned device. GPU shards never overlap; worker
overlap is confined to one shard and one wave. The generated mutant/support tree has all write bits
removed for the worker phase and its exact modes are restored afterward; any write-bit, path, or
symlink violation fails the batch. If an abrupt process or host exit leaves that real symlink-free
tree read-only, the next startup makes only its directories owner-deletable and removes the whole
disposable tree before regeneration; a root/internal symlink or surviving path fails closed.
The two module sets are disjoint and their exact union is the coverage registry. Run the complete
gate as:

```bash
python tests/harness/mutation.py tests/_support/restricted_mps_mutation_suite.json
```

The GPU lane may never inherit CPU-lane parallelism: each fresh child fixes its host thread pools at
one and all children share the shard's single pinned GPU lease. Every clean replica and each tested
mutant must emit an authenticated, identity-bound pytest-completion sentinel. A GPU mutant timeout
is killed and resumable only when that sentinel proves pytest exit code 1, no host/CUDA resource
exhaustion is present, and process-group cleanup is verified. Clean-control and CPU timeouts, crashes,
missing or inconsistent sentinels, `no_tests`, resource exhaustion, unverified cleanup, and every
other suspicious status are not killed mutants. The suite snapshots source, tests, configuration,
and copied support inputs and
serializes whole-suite result publication so concurrent invocations cannot reuse a stale PASS. A GPU
interruption retains only an authenticated contiguous prefix bound to the input snapshot, generated
semantic AST catalog, mutant/test plan, execution and timeout policy, Conda/Python runtime
fingerprint, sanitized child environment, leased GPU slot/UUID/driver identity, and each worker's
deterministic log name and SHA-256. External pytest addopts/plugins/xdist state is removed before
launch. Workers may finish out of order, but only the coordinator writes a contiguous prefix in plan
order; a non-resumable result cancels current-wave siblings and admits no later wave. The first
completed non-resumable outcome is the reported trigger, rather than a lower-index sibling canceled
after that trigger. Automatic timeouts scale the single-worker dynamic budget by `jobs` to cover
in-wave CUDA startup and runtime contention; an explicit timeout remains literal. Resume always
regenerates the plan, reauthenticates every retained worker log, and reruns all clean-admission
replicas. Fresh plans use schema v3, completion sentinels use schema v2, and GPU checkpoints use
schema v4. The machine semantic catalog and annotation-only disposition manifest use v2; batch and
suite result artifacts use v3. Direct batches statically reject stale or malformed disposition
manifests before setup mutation or mutant generation. Direct batches and the outer suite share one
lock order, so aggregate publication and
checkpoint retirement cannot delete a same-tag direct run's state. A checkpoint is removed only
after the aggregate result is atomically published. Before checkpoint admission, each completed
worker log and its directory are `fsync`-durable and its digest is computed from the same open inode;
checkpoint/terminal JSON publication uses temp-file flush plus `fsync`, atomic replacement, and a
post-replace directory `fsync`. Durability errors propagate as non-resumable failures. In
the CPU lane, a null raw mutmut exit code is canonical `not_checked` and causes the incomplete suite
to fail; it is never scored as suspicious or killed.

Only the machine AST classifier may remove a mutant from the semantic denominator, and only for the
exact non-contractual exception-prose class. Human review rows are authenticated annotations: they
cannot alter kind, criticality, denominator membership, or pass/fail. Raw, semantic, and
machine-excluded counts conserve exactly for every canonical status. Suite merge requires complete
v3 score fields and status domains, strict raw aliases, identity-bound critical evidence, matching
configured bars, and count-derived module rates and verdicts; injected fields, forged summaries, and
legacy child artifacts fail closed.

GPU mutation preparation holds the same single GPU lease used by the clean control and mutant
workers. This is required because the exact mutant/test association run collects GPU-gated tests,
which fail closed when CUDA is hidden. Plan regeneration and checkpoint validation therefore run
under the pinned `CUDA_VISIBLE_DEVICES`/`ECS_GPU_SLOT` environment before any retained status is
credited. No second shard or separately leased GPU task may overlap that lease; only the shard's
bounded fresh child wave may share the pinned device.

`test_mps_phase1b_fail_closed.py` is the CPU-only GREEN regression firewall for the Phase 1B
false-green repair slice. It corrupts numerical evidence, mandatory truncation fields, MCWF
certification identities and empirical count/probability bindings, Carrier child-state tuples,
resource probes, and the QT Record-materialization budget while replacing CUDA, Record enumeration,
and MPS execution with must-not-run sentinels. The restricted MPS source slice must keep these
falsifiers passing. It also corrupts the direct MCWF policy booleans and raw-payload serialization;
the direct manifest must reject non-boolean state and nonfinite JSON before emitting a content hash.

`test_mps_quimb_cutoff_static_gate.py` is the package-wide negative gate for the Quimb default-cutoff
defect class. Every decomposition call that can truncate a tensor network must carry a named
`cutoff=...` argument at the call site; the scanner self-test proves that deleting the keyword is
detected. It remains part of canonical service/release acceptance but is deliberately excluded from
both mutmut test selections: a mutmut trampoline source file contains every dormant generated
cutoff-removal candidate at once, so a raw AST scan cannot identify the active mutant and would make
the clean stats control fail before any mutant runs. The scanner's own synthetic deletion falsifier
and the normal-source service gate retain this defect-class protection. Numerical and wiring tests
remain in mutation selection. Raw-source scanners embedded in otherwise behavioral test files carry
the registered `mutation_trampoline_incompatible` marker. The generated mutmut selection excludes
that marker during stats, clean-control, and per-mutant association, while ordinary pytest, coverage,
and service acceptance continue to execute those architecture gates against normal source. This is
test-topology isolation only; it does not exempt any production mutant or lower the semantic score.
`test_mps_three_leg_comparator.py` protects the MPS-016 dense
NumPy/SVD, repository actual-split, and Quimb public-wiring reconciliation, including
swapped-topology and norm corruption falsifiers. The Quimb leg is wiring evidence only, not an
independent scientific oracle.

`test_mps_uncapped_nonlocal.py` is the MPS-001 numerical and transactionality gate. Its independent
NumPy construction freezes a weak connected three-site unitary that Quimb 1.14 `auto-mps` loses in
the hidden dense-to-MPO split. It checks the explicit-zero-cutoff replacement, source immutability,
norm and unitary corruption, ordered support, numerical-only resource boundaries, preallocation
failure, and the reachable frontend route. It does not turn the mechanics helper into a scientific
carrier or certify a complete Record law.

`test_mps_capped_uncapped_mutation_firewall.py` is a pure-CPU mutation discriminator for the shared
capped/uncapped mechanics. It pins numerical preflight boundaries, strict backend/dtype/finite
validation, both explicit zero-cutoff Quimb layers, complete split kwargs, discarded-weight
identities, kept-bond evidence, swap ordering/index rewrites, and the rule that caller context cannot
overwrite authoritative split-event fields. It asserts machine behavior and exception types, not
human exception prose.

`test_axis1_record_layout.py` is the CPU-only Phase-3 schema gate. It checks immutable schedule
parsing, the hand-written LSB-first Record domain and XOR projection, every schema-corruption branch,
and a static prohibition on late key/target registration inside the two MPS executors. It also
directly registers and corrupts `_validate_axis1_projected_record_payload`,
`_require_exact_text_list`, and `_require_exact_binary_record_matrix`; these are the three named
private authentication units in the 51-unit registry.
`test_mps_phase3_record_layout.py` is the GPU behavior gate for MPS-004/005/012/013. It requires each
Adapter to parse the sealed layout exactly once, exercises QT two-boundary Records, MCWF grouped
per-target reset masks, sampled-reset metadata, and the two structured MCWF evolution blockers.

`test_mps_mcwf_measurement_semantics.py` protects conditioned X/Z state evolution, sparse sampled
support, and the independently reconstructed dense level oracle. Its hand-typed excitation channel
forces a positive Born branch below `NUMERICAL_ZERO`; scale-invariant reset tests require every
finite positive reset trace to normalize, while zero and non-finite trace corruptions must fail.
These are structural-probability and oracle-integrity checks, not tolerance or calibration claims.

`test_mps_phase4a_probability_and_norm.py` is the CPU Phase-4A gate for MPS-006/007/011. It checks
Decimal-reconstructed tiny T1/T2 probabilities, exact structural zero versus positive-subnormal
behavior, immutable and unnormalized raw candidate mass, raw-index/RNG preservation, QT/MCWF
mass-completeness failure, and post-mutation norm validation across reset routes.
`test_mps_phase4b_configuration_support_and_bond.py` is the CPU Phase-4B gate for
MPS-008/009/010. It checks lossless public-control validation at direct, aggregate,
resource-probe, and Carrier boundaries before CUDA or child execution; separate QT/MCWF coherent
support decisions and structured QT blockers; and exact-bond sufficient dimensions against a
hand-written cut-product oracle. The finalized hostile matrix includes the QT and MCWF standalone
contracts, MCWF dense certification, Carrier auto-routing, and legal index-protocol counter-fixtures.
The hostile behavior matrix is GREEN in its focused checks. No static pytest count is authoritative:
the measured result must be regenerated from the current checkout and its exact command/report.

The most recent measured restricted-MPS coverage gate is GREEN at 51/51 canonical units, each with
statement and branch coverage 1.0. It must be regenerated after any relevant source, test, registry,
or contract change. Coverage remains structural evidence only; the corruption falsifiers,
independent dense references, external comparisons, and mutation gate remain separate requirements.

## Test disciplines

- Structural coverage executes every reachable statement and branch; it does not prove that an
  assertion discriminates correct from corrupted behavior.
- Property tests exercise physical and data-contract invariants across generated inputs.
- Mutation tests verify that assertions reject meaningful code perturbations. Only the authenticated,
  resource-clean GPU mutant timeout defined above is a terminal kill; every other timeout and every
  `no_tests` outcome remain non-killed and never improve the score.
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

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
per-file environment override declared in the service catalog. The external comparison adapters
declare their nested `ecs-baseline-aer`, `ecs-baseline-yastn`, and `ecs-baseline-qutip`
environments. Every acceptance child removes `PYTHONPATH` and disables user-site imports. Checkpoint
policy binds the resolved Conda
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

`test_external_aer_mps_comparison.py`, `test_external_yastn_mcwf_mass_comparison.py`, and
`test_external_qutip_mcwf_xz_comparison.py` protect repository-owned neutral adapters for isolated,
external baselines. All three run in isolated environments. YASTN is source/commit-bound to its
pristine clone. QuTiP binds pristine commit/tree metadata, checks selected installed solver sources
against that clone, and records the full installed-distribution identity; this is not a claim that
the entire installed tree is reproducibly rebuilt from the clone. Aer records installed-wheel
provenance and separately verifies a pristine
reference clone, but does not claim wheel-to-clone identity. Aer checks independent dense/unitary
state evolution and finite-bond damage; YASTN checks the frozen product-MPS MCWF candidate-mass
arithmetic and an omitted-jump falsifier. QuTiP runs actual continuous-time CPU MCWF trajectories for
a frozen two-qubit T1 fixture, independently samples ordered X/Z projectors and reset instruments,
and compares its label/binary histograms with public GPU direct and Carrier MCWF under a conservative
six-way Bonferroni allocation: three joint Record views and three directed X-after marginals. The
fixture fixes survival to `s=0.25`; both the deterministic final-Z-bit corruption and the
`sqrt(s) -> s` X-coherence mutation must exceed their registered radius and force failure. The
retained v2 worker report binds its pristine source commit/tree, installed-distribution content hash,
Python/NumPy/SciPy versions, explicit QuTiP integrator controls, worker/protocol hashes, observed
state/probability dtypes, and canonical content hash. The project side recursively validates its exact
shape and recomputes the fixture, runtime, solver, histogram, reset, statistical, and verdict
invariants. Strict JSON and raw-type checks reject duplicate/non-finite values and coercible Record
bits/counts, while an immutable transport envelope separately binds stdout/stderr/return code and a
construction-time raw JSON byte identity that must decode to the embedded payload. The launch strips
all `CONDA_*`/`_CE_*` and loader/toolkit/venv markers, with worker-side rejection of leakage. Both CLI targets invalidate stale
output before computation and use file-plus-directory `fsync` publication; a failed post-replace
directory sync removes the destination. The service snapshot includes all three pristine external clones, so clone drift
or same-tree HEAD drift invalidates a resumable checkpoint before admission. Its runtime identity also
hashes every installed NumPy/SciPy/QuTiP file in `ecs-baseline-qutip`, so package-tree drift cannot
reuse an old PASS. The nested worker inherits the comparator's supervisor-owned process group rather
than creating a private session. Canonical service acceptance
supplies exact file-local opt-in flags, so all three test files run their isolated external
subprocess rather than only helper contracts. The QuTiP fixture is finite-sample and covers only two
qubits and two measurement boundaries; none of these external libraries establishes a complete QEC
Record law, qutrit/leakage semantics, scalable execution, production readiness, or the internal
restricted-acceptance verdict.
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

`restricted_mps_coverage_targets.json` reconciles thirteen modules and registers 59 canonical units:
53 public units plus three private Record-payload authentication helpers. Every unit has 100%
statement and branch coverage with no exemptions. The authoritative
mutation topology is `restricted_mps_mutation_suite.json`: seven CPU-only mechanics/schema modules
run through stock mutmut with exactly four workers and CUDA hidden, then five ordered GPU
execution/certification shards run one after another. The first four GPU shards own one module each;
GPU05 owns both evaluator certification and its isolated NumPy operator-reference module. Every GPU
shard has `jobs=4`, acquires
one lease, runs four concurrent fresh clean-control replicas for admission, and then uses fixed waves
of at most four fresh pytest processes on that pinned device. GPU shards never overlap; worker
overlap is confined to one shard and one wave. The generated mutant/support tree has all write bits
removed for the worker phase and its exact modes are restored afterward; any write-bit, path, or
symlink violation fails the batch. If an abrupt process or host exit leaves that real symlink-free
tree read-only, the next startup makes only its directories owner-deletable and removes the whole
disposable tree before regeneration; a root/internal symlink or surviving path fails closed.
All six batch module sets are pairwise disjoint and their exact union is the coverage registry. Run the complete
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
falsifiers passing. It also requires canonical no-measurement Records to remain non-metric
`unavailable`, corrupts the direct MCWF policy booleans and raw-payload serialization;
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
private authentication units in the 59-unit registry.
`test_mps_phase3_record_layout.py` is the GPU behavior gate for MPS-004/005/012/013. It requires each
Adapter to parse the sealed layout exactly once, exercises QT two-boundary Records, MCWF grouped
per-target reset masks, the public mixed-X/Z ordered keys/targets/bases/reset contract, the X-reset
`|+>` law across a later measurement boundary, sampled-reset metadata, and the two structured MCWF
evolution blockers.

`test_mps_mcwf_measurement_semantics.py` protects conditioned X/Z state evolution, sparse sampled
support, and the independently reconstructed dense declared-basis projector oracle. Its standalone
RX/MX law requires exact structural-zero support without dropping a separately hand-typed physical
Born branch below `NUMERICAL_ZERO`; scale-invariant reset tests require every finite positive reset
trace to normalize, while zero and non-finite trace corruptions must fail. The zero-frequency firewall
also proves it reaches the intended positive-count rule after all ordered metadata is valid. These are
structural-probability and oracle-integrity checks, not tolerance or calibration claims.

`test_mcwf_operator_reference.py` exhaustively compares all 51 production Hamiltonian and seven
collapse families with a certifier-local NumPy/Pauli inventory, verifies exact multilevel
structural-zero padding, rejects unknown/wrong-arity terms, statically prohibits production/Torch/
Stim imports in the reference module, and exercises the joint `CORR_RELAX` oracle/carrier-window
route. That family is covered only after it is already present in an internal sealed Carrier program;
no public source/schedule compiler lowering currently emits it. The literature source-closure reset
remains OPEN, so this is implementation-definition evidence only.
`test_collective_decay_finite_step_guard.py` separately binds the MCWF mass preflight to the
sampler's sequential no-jump product. Its two-independent-T1 counterexample kills the obsolete
single-sum bound, checks the corrected operator-norm bound dominates the directly computed raw-mass
residual, requires the defensive preflight to report no finite count at zero budget, and requires the
public MCWF seam to reject zero before CUDA.
`test_axis1_mcwf_dense_certification.py` additionally requires production term builders to be called
once, group gates to be derived from those exact frozen tensors, and the mass preflight and trajectory
to consume the same artifact inventory. It independently reconstructs connected grouping and group
gates with SciPy `expm`, checks exact structural zeros, fires stateful-builder TOCTOU and
state-insensitive wrong-grouping corruptions, and authenticates the public v2 packet's complete
substep/term/group coverage, program/artifact hashes, the reference/certifier/carrier-operator sources,
the transitive ideal-control-generator and selection-family sources, and post-execution integrity.
The packet tests require the certifier to recompute the canonical artifact hash from the inspected
matrices and metadata; an unrelated but well-formed digest is rejected.
It also includes zero-builder falsifiers for Hamiltonian and
collapse sources, including outcome-insensitive `CTRL_Z` and dark-state `T2`, plus an identity
substituted for the Torch X-basis rotation and a damaged production level-to-bit mapping. The last
case covers qubit Z and multilevel X/Z leakage with readout `b=0`:
the declared-basis label TV can remain zero while the emitted-binary TV forces rejection. The dense
reference must reject all of them. A public no-measurement direct/Carrier pair must execute the
state path while remaining unavailable for positive certification; the removed normalized-candidate
Choi helper surface cannot be reintroduced. `test_mps_actual_split_helper.py` additionally binds a
public five-qubit `symmetric_hamiltonian_first_order_collapse` execution to ordered half-pass indices
`[0, 1]`, half-step durations, and
complete occurrence aggregation. `test_mps_phase6_evaluator_metric_binding.py` rejects reordered
bases/reset masks before policy or dense certification even when the multiset is unchanged.
`test_mps_carrier_child_authentication.py` rejects reordered-and-rehashed direct and auto-routed
Record summaries, rechecks Record width/count/probability and XOR projections, verifies honest
ordered measurement/readout-policy forwarding, requires sorted unique normalized histograms and canonical blocked summaries,
binds caller options/state/policy/direct-v8 provenance through the auto-router, and rejects unknown
or evaluator-only fields recursively at every public Carrier summary seam, including both component
values of the joint label/binary certification. It also recomputes the frozen-dynamics authority from
sealed inputs and, for accepted seeded evidence, independently replays direct MCWF and exact-binds its
hash, Record summary, and policy. A self-consistent alternate histogram is therefore rejected even when
its shape, counts, probabilities, policy, and outer hashes are internally valid. Forced Carrier,
auto-to-MCWF, grouped-Record, and public-direct tests require exactly one Carrier-program compilation per
parent call and require every private execution/dynamics consumer to receive the identical precompiled
dictionary. Exact schedule-manifest, program-content, and backend identities are checked before CUDA and
again across selector, replay, Record materialization, publication, and return checkpoints. The accepted
seeded auto path still performs an independent trajectory replay, but it reuses the sealed Carrier program;
this does not cover auto-to-dense, dynamics-artifact recompilation, concurrent mutation, or
mutate-consume-restore atomicity. The file also exercises a real public auto-routed MCWF child with ordered
X/Z measurements. Together with the direct and Carrier tests, this establishes public X/Z
availability for the restricted MCWF slice; it does not establish production scalability or a complete
QEC Record backend.

`test_mcwf_carrier_record_output_units.py` is the CPU contract for the bounded
Carrier-to-`RecordBatch`/`.b8` adapter. It requires exact integer-count expansion in canonical grouped
support order with no second draw, immutable `uint8` detector/observable rows, completed evidence
accepted for restricted execution only, sealed mixed-X/Z XOR
projection without `s_to_det`, explicit loss of original trajectory order, the
`mcwf_mps_record_sample_summary.v1` content-hashed manifest, little-endian `.b8`, and cleanup of only
an unpublished private stage on pre-rename rejection. Its allocation tripwire proves the conservative
`4 * N * (D + O)` byte guard fires before
CUDA or output allocation through public parameter `max_record_array_payload_bytes` (default constant
`AXIS1_MCWF_MPS_RECORD_MAX_ARRAY_PAYLOAD_BYTES == 512 MiB`). The test pins this as an incremental
NumPy Record-array payload bound only, covering preallocated `uint8` rows plus current `RecordBatch`
binary-validation/freezing temporaries and excluding Carrier/Python support, canonical JSON,
array/allocator overhead, build/publication provenance, and process RSS. A separate public preflight
test drives `max_record_support_cells` below the static histogram/layout cell estimate and proves that
independent guard also fires before MCWF/CUDA. No-`np.repeat` and aggregate-projection tripwires protect
the bounded fill and streaming strict-order/row-wise-XOR validation.
Its corruption table rejects malformed counts/probabilities/support order, duplicated rows, wrong
projections, evaluator-only truth, unaccepted evidence, and a rehashed self-consistent forged law. The
private binding is tested only as same-call consistency across Carrier/direct/policy/Record-law hashes;
it is not asserted as cryptographic authenticity or replay protection. Detector-only and
observable-only fixtures pin legitimate zero-width sides and optional `.b8` omission, while the
double-zero case remains rejected.
The v1 manifest contract pins the exact evaluator-truth-free
`axis1_mcwf_mps_carrier_execution.json` and binds its file SHA-256, schema, internal content hash,
`contains_carrier_program_summary=true`, and explicit
restricted-policy/Record-execution/Carrier-program-summary locators. It separately pins the
complete sealed, evaluator-truth-free `axis1_mcwf_mps_carrier_program.json`, its file SHA-256/schema/
internal content hash and `contains_complete_sealed_program=true`, plus the metric/gate
`program_evidence_locator` and public result's `carrier_program_evidence` path. It also binds the sealed layout,
optional `.b8` names/widths/hashes, run seed/dtypes, and the sealed build/source/environment/runtime
identities. Tests pin the source's resolved import origin, equality to the package-import/module-import
disk digests at every validation checkpoint, and `claims_runtime_code_object_attestation=false`; they do
not claim continuous immutability between checkpoints. Source or package-tree drift fails before MCWF.
Git provenance requires a full 40/64-hex `git rev-parse HEAD` and fails closed if unavailable or invalid.
Required Torch/Quimb/SciPy distribution versions also fail
closed before execution when unavailable. The environment lock is asserted as hash-bound only, with
`authoritative_lock_conformance_checked=false` and `claims_reproducible_environment=false`; GPU
provenance names `torch.version.cuda` as the PyTorch build CUDA version and leaves the loaded runtime
`not_attested`.
At every seal/revalidation checkpoint, each required staged artifact must be opened through the stage
fd with `O_NOFOLLOW|O_NONBLOCK`, remain a regular file, and be sealed by
`st_dev`/`st_ino`/`st_mode`/`st_size`/`st_mtime_ns`/`st_ctime_ns`/non-null 64-hex SHA-256. Hashing and
file fsync must use that same artifact fd. JSON files are compared to canonical-payload
expected hashes; `.b8` files are compared to chunked hashes of the in-memory binary Record rows. The
manifest is written last and is itself added to the exact whitelist. Missing or symlinked required
files, post-hash tampering, and extra/evaluator-truth files are RED. The exact set is revalidated after
stage-directory fsync and again before rename, then rechecked through the retained stage fd after rename
and after parent fsync. Exact manifest-key assertions require
`staging_directory_fsync_required_before_rename=true`,
`staging_directory_fsync_success_attested_in_bundle=false`,
`staged_artifact_set_policy=exact_regular_files_bound_by_st_dev_st_ino_st_mode_st_size_st_mtime_ns_st_ctime_ns_sha256`,
`artifact_file_fsync_required_at_each_seal_checkpoint=true`,
`artifact_file_fsync_success_attested_in_bundle=false`,
`staged_artifact_set_revalidation_required_after_stage_fsync=true`,
`staged_artifact_set_revalidation_success_attested_in_bundle=false`,
`published_artifact_set_recheck_after_rename_required=true`,
`published_artifact_set_recheck_after_rename_success_attested_in_bundle=false`,
`published_artifact_set_recheck_after_parent_fsync_required=true`, and
`published_artifact_set_recheck_after_parent_fsync_success_attested_in_bundle=false`.
After the post-parent-fsync full artifact recheck, tests require sealed-identity revalidation, a
metadata-only exact-set recheck, a final destination-inode recheck, and then the path-visible parent
check. Exact fields are `sealed_identity_revalidation_required_after_execution=true`,
`sealed_identity_revalidation_required_before_atomic_rename=true`,
`sealed_identity_revalidation_required_after_final_artifact_recheck=true`,
`sealed_identity_revalidation_success_attested_in_bundle=false`,
`published_destination_identity_recheck_after_final_artifact_recheck_required=true`, and
`published_destination_identity_recheck_after_final_artifact_recheck_success_attested_in_bundle=false`.
Publication freezes an absolute lexical destination, so a later cwd change cannot retarget it.
Preflight requires the target parent to pre-exist, opens and holds its directory fd, seals its
`st_dev`/`st_ino`, and exercises both sacrificial collision-preservation and successful
`RENAME_NOREPLACE` legs on the actual target filesystem before MCWF. Missing
parent/lock/primitive/probe tests fail before execution; post-execution drift tests cover parent
replacement, environment-lock mutation, and fresh build/source/runtime identity changes. The same seal
must pass again after staging fsync immediately before rename. Stage creation/I/O/removal, rename, and
parent fsync are exercised relative to the held parent/stage fds. Adversarial injections require the
destination inode to equal the sealed stage immediately after rename and again after parent fsync, then
require the path-visible parent to retain its sealed identity. Manifest assertions pin
`prepared_for_atomic_publication`, the passed target-FS probe, required-but-not-self-attested identity
checks, and false rename, destination-identity, artifact-recheck, and parent-fsync success fields.
Manifest-last, unpublished
stage cleanup, concurrent-destination preservation, and stage-entry substitution tests are also pinned.
If the no-replace wrapper completes the rename and then raises, the writer must detect and preserve the
published sealed stage while propagating the exception. Any later destination-identity, parent-identity,
or parent-fsync failure likewise preserves the published directory, raises, and makes no published-path
cleanup attempt. Successful writer return is the only durability confirmation; the bundle never
self-attests those post-manifest steps. Unpublished-stage cleanup is an ownership-bounded, best-effort
attempt rather than a durability claim; cleanup errors may leave the private stage behind while the
original failure propagates.
`test_mcwf_carrier_record_output_gpu.py` runs the same public surface against a real completed and
accepted CUDA MCWF Carrier child with mixed X/Z measurements, checks that the child keeps
`claims_b8_artifact=false` while the writer summary owns `true`, and requires a no-measurement run to
fail without artifacts. These tests establish only the bounded grouped canonical Record interface.
They do not recover original trajectory order or establish DEM/decoder integration, faithfulness,
calibration, production scalability, or a complete QEC Record law.

`test_axis1_mcwf_convergence.py` is the restricted MCWF X/Z Record-law convergence gate, not an
Axis-1 channel gate. A hand-written scalar recurrence over the byte-pinned two-qubit T1 fixture fixes
joint/Z and X-after TV at `m=10,20,40,80`, requires monotone approximate bias halving on that grid,
and preserves the final Z column as an exact structural zero. Its public GPU leg runs `m=40`,
`n=2048`, seed `19073` and compares the empirical ordered `[X,Z,X,Z]` Record with the finite-step law
under one-sample Weissman radii. Helper-level `0.5 -> 1` no-jump and `dt/m -> dt` corruptions are power
checks; only the canonical semantic mutation suite may claim the corresponding production mutants
are killed. The file makes no global convergence-order, linear-channel, Choi/CPTP, calibration,
scalability, or production claim.

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

The restricted-MPS coverage gate registers 59 canonical units and requires every unit to reach statement
and branch coverage 1.0 with no exemption. The 2026-07-19 release-retained clean-HEAD log path is
`outputs/simulator_validation/logs/mcwf_restricted_mps_coverage_clean_head_20260719.log`; a PASS there is
historical and was invalidated by later MCWF Carrier-program and QuTiP-v3 commits. A new retained log is
current only when generated after the final source/test/catalog/contract commit; any later relevant change
makes it stale. The gate intentionally does not publish a static pytest count. Coverage
remains structural evidence only; the corruption falsifiers,
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

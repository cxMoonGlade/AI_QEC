# Architecture

The binding product boundary is `docs/SIMULATOR.md`. This file is a human-readable map; the exact
machine-readable inventory is `docs/service_status.json`, and `docs/CODE_MAP.md` is generated from
that inventory plus the installed source tree.

`carrier/mps` is an execution-mechanics library for restricted verification routes. It makes
no state-, Record-, or LER-faithfulness claim and is not a registered scientific Carrier.
PEPS remains the trajectory-carrier frontier, and PEPO remains the retained research Carrier.

## Package map

| owner | role | current boundary |
|---|---|---|
| `source/` | finite-RTN sources, replayable timelines, source-to-parameter mapping, matched controls | classical latent-source models; no reduced-map verdict |
| `mechanisms/axis1_primitives.py` | local drive, coupling, relaxation, excitation, dephasing, readout-dephasing, and fSim residual lowering | two-qubit local windows; channel assembly belongs to `carrier/` |
| `mechanisms/qutrit_leakage.py` | qutrit leakage channel, Kraus conversion, diagnostics, and process factories | bounded synthetic parameters unless complete provenance is supplied |
| `mechanisms/cz_leakage.py` | explicit multi-level CZ Hamiltonian/channel derivation and tracked-subspace transport | explicit parameter or channel input; no repository scratch discovery |
| `noise_processes/` | controlled generative processes with evaluator-only truth | emits declared records; no hidden-truth leakage |
| `carrier/joint_lindbladian.py` | one-generator-per-substep channel assembly and exact connected-component factorization | GPU complex128 |
| `carrier/cptp_channel.py` | backend-neutral CPTP channel object | channel representation, not a record backend |
| `carrier/records.py`, `record_fold.py` | common record types, packed layout, raw-syndrome/detector conversion | binary, versioned, immutable, temporal-detector semantics |
| `carrier/exact/` | bounded qubit/qutrit density-matrix routes | implementation references; not scaling paths |
| `carrier/kernels/` | scoped native CUDA acceleration | optional loading; scientific fallback rules remain explicit |
| `carrier/mps/` | bounded MPS execution mechanics for restricted verification routes | not a registered scientific carrier; explicit-zero-cutoff uncapped nonlocal unitaries only within fixed numerical resource guards |
| `carrier/pepo/` | two-dimensional density-matrix PEPO | retained `RESEARCH`; not canonical record output |
| `carrier/peps/` | single-wire two-dimensional PEPS trajectories | `RESEARCH`; full-record truncation faithfulness open |
| `frontend/` | circuit IR, code specs, compiler, schedules, bounded executors, artifact emission, optional DEM/decoder reduction | one record contract, multiple explicit execution routes |
| `frontend/axis1_carrier_execution.py` | validated Carrier aggregation plus the bounded MCWF grouped `RecordBatch`/`.b8` output wrapper | canonical X/Z detector/observable records only for completed measured MCWF evidence accepted for restricted execution; no original trajectory order, DEM, decoder, or scaling promotion |
| `frontend/axis1_record_layout.py` | immutable schedule-derived measurement/Record schema shared by restricted QT/MPS and MCWF/MPS Adapters | frontend schema owner, not a carrier or an independent physical oracle |
| `certify/` | evaluator-only scoring against independent references; `axis1_mps.py` owns restricted-MPS dense References, metrics, and final acceptance | formal implementation evidence, not hardware truth; execution mechanics do not self-certify |
| `quantum_bath/` | bounded pseudomode-enlarged GKSL comparisons | feasibility-only `RESEARCH`; not production |
| `numerics.py` | shared float64 scaled arithmetic and comparison threshold | recovers representable final values; rejects nonrepresentable nonzero values instead of replacing structural endpoints |

## Implemented flow

```text
Stim route
  CodeSpec / CircuitIR / imported Stim circuit
    -> compile and explicit Stim-representable noise
    -> detector/observable RecordBatch + .stim/.dem/.b8/manifest
    -> optional external decoder output

Dense coupled route
  replayable finite-RTN timeline
    -> explicit source-to-parameter mapping
    -> per-round local primitive parameters
    -> sealed substep schedule
    -> dense joint-Lindbladian record execution
    -> RecordBatch + evaluator-only truth held separately

Restricted MPS verification route
  sealed Axis-1 schedule
    -> immutable schedule-derived Record layout
    -> route-specific QT/MPS or MCWF/MPS state operations
    -> QT exact: full binary support
       QT sampled: sequential conditional binary outcomes + observed-support histogram
    -> precomputed XOR projection
    -> evaluator-side comparison and acceptance in certify/axis1_mps.py
    -> restricted execution/evidence manifest
    -> completed measured MCWF accepted for restricted execution only: same-call-bound exact-count expansion in grouped support order
       -> canonical detector/observable RecordBatch
       -> Carrier execution JSON + complete sealed-program JSON + optional detection_events.b8/obs_flips_actual.b8 + v1 sample summary

Leakage research routes
  external XZZX schedule + explicit qutrit channel/run specification
    -> exact bounded reference, PEPO, fused within-cycle, or PEPS owner
    -> owner-specific output and current record adapter where supported
```

There is no current arrow from the finite-RTN process into the qutrit XZZX leakage carrier. A diagram
or document must not draw that missing edge as implemented.

## Carrier boundary

- Exact density matrices provide bounded references and hit exponential memory limits.
- Restricted Axis-1 MCWF/MPS and QT/MPS executors are current verification routes, not universal
  full-record backends and not registered scientific carriers. They are execution mechanics for a
  bounded validation route. In particular, true-over-cap backend completion without an independent
  Record comparator remains a diagnostic `fail`; under-cap sampled evidence is governed by its
  separate registered restricted-acceptance policy. Their shared frontend Record-layout owner parses
  only compiler-sealed public schedule facts; each Adapter retains its own state operations and
  support preflight, and dense certification remains a separate `certify/axis1_mps.py`
  comparison path. Binary measurement records are the visible Record surface. Pre-readout multilevel
  trajectories and jump-family counts live only under the explicitly evaluator-only diagnostics
  namespace and are not downstream estimator inputs. QT sampled measurement conditions one binary
  site at a time and emits only lexicographically sorted observed outcomes; zero-frequency rows are
  omitted. QT exact execution retains full binary support. Exact and sampled preflight bounds are
  respectively `2**measurement_width` and
  `min(2**measurement_width, trajectory_count)`, and both fail closed before CUDA. Seed and dense
  comparisons align the union of Record supports with missing probabilities set to zero. This
  changes RNG draw order, so old per-trajectory bit identity is not an Interface requirement.
- For MCWF, a forced Carrier, auto-to-MCWF, grouped-Record, or public-direct parent call compiles one sealed
  Carrier program and passes that same dictionary through its private child/dynamics path. Exact
  schedule-manifest, program-content, and backend identities are checked before CUDA and at later
  consumption/publication checkpoints. Seeded replay may independently rebuild dynamics artifacts;
  auto-to-dense and concurrent transient mutation are outside this compile-once claim.
- The MCWF Carrier child remains an evidence manifest and reports `claims_b8_artifact=false`. The
  public `axis1_mcwf_mps_record_batch(...)` and
  `write_axis1_mcwf_mps_record_samples(...)` wrappers own the bounded canonical output seam. They
  validate a completed measured child accepted for restricted execution, require a compiler-sealed
  X/Z XOR projection, and expand its
  sorted unique histogram by exact counts without another sampling draw. The result is exchangeable
  grouped output; the original trajectory order is explicitly unavailable. Projected detector rows
  never pass through raw-syndrome `s_to_det`. A private same-call consistency binding rechecks the
  direct child, Carrier, policy, and Record-law hashes without seeded replay; it is neither a
  cryptographic authenticity boundary nor a replay boundary. The materializer streams strict-order
  and row-wise sealed-XOR checks and canonical hashes without an aggregate projection or support-sized
  `np.repeat` buffer. Before CUDA, `max_record_support_cells` independently caps the static
  histogram/layout cell estimate. The separate `max_record_array_payload_bytes` guard, whose default
  is `AXIS1_MCWF_MPS_RECORD_MAX_ARRAY_PAYLOAD_BYTES == 512 MiB`, bounds only the incremental NumPy
  Record-array payload at `4 * N * (D + O)` bytes: preallocated `uint8` rows plus current
  `RecordBatch` validation/freezing temporaries. It excludes Carrier/Python support, canonical JSON,
  array/allocator overhead, build/publication provenance, and whole-process RSS.
  The writer freezes an absolute lexical destination and requires a fresh destination under an
  already-existing parent. Before MCWF it opens and holds the parent directory fd, seals its
  `st_dev`/`st_ino`, environment-lock path/hash, freshly recomputed build/package-tree identity,
  required full 40/64-hex Git HEAD,
  source hash, and environment/runtime identity, and a sacrificial probe relative to that fd on the
  actual target filesystem must pass both collision and successful
  `renameat2(..., RENAME_NOREPLACE)` cases. The disk package tree/source must still equal their
  package-import/module-import-time disk digests at each validation checkpoint, and source provenance
  includes the resolved import origin. This does not prove continuous disk immutability between
  checkpoints or attest runtime Python code objects/monkeypatches. Required Torch, Quimb, and SciPy
  distribution versions must exist. The environment lock is hash-bound only, with
  `authoritative_lock_conformance_checked=false` and `claims_reproducible_environment=false`. Runtime
  provenance labels `torch.version.cuda` as the PyTorch build CUDA version and leaves the loaded CUDA
  runtime `not_attested`. It revalidates the complete seal after MCWF and after staging fsync. Stage
  creation/I/O/removal, final rename, and parent fsync remain anchored to the held parent/stage fds. The
  destination entry must match the sealed stage inode immediately after rename and again after parent
  fsync; the pathname-parent identity is then rechecked before return. It writes the exact
  evaluator-truth-free `axis1_mcwf_mps_carrier_execution.json`; its artifact entry binds file SHA-256,
  schema, internal content hash, `contains_carrier_program_summary=true`, and explicit
  restricted-policy, Record-execution, and Carrier-program-summary locators. It separately writes
  the complete sealed, evaluator-truth-free
  `axis1_mcwf_mps_carrier_program.json`; its artifact entry binds file SHA-256, schema, internal
  content hash, and `contains_complete_sealed_program=true`, and
  `metric_and_gate_policy.program_evidence_locator` points to that file.
  Detector-only or observable-only `.b8` output is valid and the zero-width side is omitted; only the
  double-zero case fails. At every seal/revalidation checkpoint, each declared staged file is opened
  via the stage fd with `O_NOFOLLOW|O_NONBLOCK`, required to
  be regular, and sealed by
  `st_dev`/`st_ino`/`st_mode`/`st_size`/`st_mtime_ns`/`st_ctime_ns`/SHA-256; hashing and file fsync use
  that same open artifact fd. Canonical JSON payloads and chunked
  in-memory `.b8` rows provide independent expected hashes. The manifest is written last and then joins
  the exact whitelist; missing, symlinked, substituted, extra, or evaluator-truth files fail closed.
  File and stage-directory fsync are required. The exact set is revalidated after stage fsync and just
  before rename, then rechecked through the still-open stage fd after rename and after parent fsync.
  After the final full artifact recheck, sealed build/source/environment/runtime identity is revalidated,
  a metadata-only exact-set check runs, the destination inode is checked again, and only then is the
  path-visible parent identity checked for return.
  That pre-rename manifest is only `prepared_for_atomic_publication`: it records the target-FS probe and
  first post-execution seal check, declares
  `staged_artifact_set_policy=exact_regular_files_bound_by_st_dev_st_ino_st_mode_st_size_st_mtime_ns_st_ctime_ns_sha256`
  and `artifact_file_fsync_required_at_each_seal_checkpoint=true`. It also declares
  `sealed_identity_revalidation_required_after_execution=true`,
  `sealed_identity_revalidation_required_before_atomic_rename=true`,
  `sealed_identity_revalidation_required_after_final_artifact_recheck=true`, and
  `published_destination_identity_recheck_after_final_artifact_recheck_required=true`, while all
  corresponding success attestations, artifact/stage/parent-fsync success, rename success, and earlier
  destination-inode success remain false. Successful writer return is the only durability confirmation.
  If the no-replace wrapper performs the rename and then raises, the
  writer detects the sealed stage at the destination, preserves it, and propagates the exception. A
  parent-fd fsync, destination-inode, or final pathname identity failure after rename also preserves the
  published directory and propagates the error; no published-path cleanup is attempted. Only still-owned
  unpublished staging is eligible for best-effort cleanup, which may leave a private stage behind if
  cleanup itself fails. The v1 content hash
  also binds layout names/XOR columns, any optional `.b8`
  names/widths/hashes, run configuration, seed/dtypes, package-tree/Git/source and environment-lock
  identity including the resolved import origin, GPU name/UUID/compute capability, NVIDIA driver,
  PyTorch build CUDA version, explicit loaded-runtime `not_attested` status, and publication
  status/protocol. Missing parent/lock, failed target-FS probe, sealed-identity drift, no-measurement,
  blocked, noncanonical, over-budget, incomplete, or unaccepted evidence fails closed.
  The v1 sample
  summary preserves execution/certification/diagnostic/acceptance status and owns
  `claims_b8_artifact=true`; it claims neither DEM/decoder integration, complete-QEC behavior, nor
  production scalability.
- PEPO is retained for current density-matrix research and exact bounded comparisons.
- PEPS is the full-geometry trajectory frontier; its strict-target FET entropy equality currently
  follows an all-identity fallback, so the non-degeneracy gate is RED and finite-truncation record
  faithfulness is unclosed.

Carrier swaps preserve the channel and record contracts only where the owner explicitly implements
those contracts. No local state or truncation metric alone establishes record equivalence.

## External boundaries

- Google d3 circuit/geometry/schedule files are caller inputs, not package data or noise calibration.
- PyMatching is an optional downstream decoder dependency.
- CUDA-Q is an isolated plugin workload executed in a separate environment and process.
- Aer, YASTN, and QuTiP comparison legs execute in isolated environments. YASTN is source/commit-bound
  to its pristine clone. QuTiP binds pristine commit/tree metadata, checks selected installed solver
  sources against that clone, and records the complete installed-distribution content identity; it
  does not claim a reproducible full installed-tree build from the clone. Aer records the installed
  wheel provenance and separately
  verifies a pristine reference clone, but does not claim wheel-to-clone identity. Aer is a
  finite-circuit state/truncation comparator; YASTN is a product-MPS raw candidate-mass comparator;
  QuTiP is a fixed two-qubit continuous-time MCWF X/Z measurement/reset comparator with joint-Record
  and directed X-after statistical gates. Its exact-field v2 worker artifact remains immutable inside
  a v1 transport envelope; the project-side v3 comparison additionally persists the finite-step
  recurrence, public `m=40` direct/Carrier sample gates, corruption controls, and canonical outer hash.
  The project side recomputes its semantic gates, rejects duplicate/non-finite
  JSON, sanitizes inherited environment markers, and uses stale-safe file-plus-directory-`fsync`
  publication. Quimb's three-leg comparison is wiring evidence against
  the same dependency. None establishes a complete QEC Record law, trajectory-by-trajectory
  equivalence, qutrit/leakage behavior, scalability, or the restricted-acceptance verdict.
- Explicit serialized channel files are derived caches, not automatically scientific data.
- Distribution artifacts include only the current package and shipped documentation inventory.

## Execution topology

The service supervisor owns a three-lane fresh-process plan: bounded CPU concurrency, serial
host-heavy CPU execution, and serial GPU execution under a cross-process lock. The parent does not
import CUDA runtimes. Process-group cleanup, fail-closed GPU admission, single-writer aggregation,
and atomic summaries are architectural requirements, not test-runner conveniences.

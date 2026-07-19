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
  a transport envelope; the project side recomputes its semantic gates, rejects duplicate/non-finite
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

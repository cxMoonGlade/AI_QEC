# Architecture

The binding product boundary is `docs/SIMULATOR.md`. This file is a human-readable map; the exact
machine-readable inventory is `docs/service_status.json`, and `docs/CODE_MAP.md` is generated from
that inventory plus the installed source tree.

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
| `carrier/pepo/` | two-dimensional density-matrix PEPO | retained `RESEARCH`; not canonical record output |
| `carrier/peps/` | single-wire two-dimensional PEPS trajectories | `RESEARCH`; full-record truncation faithfulness open |
| `frontend/` | circuit IR, code specs, compiler, schedules, bounded executors, artifact emission, optional DEM/decoder reduction | one record contract, multiple explicit execution routes |
| `certify/` | evaluator-only scoring against independent references | formal implementation evidence, not hardware truth |
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
  full-record backends.
- PEPO is retained for current density-matrix research and exact bounded comparisons.
- PEPS is the full-geometry trajectory frontier; its current FET entropy invariant fails and its
  finite-truncation record faithfulness is unclosed.

Carrier swaps preserve the channel and record contracts only where the owner explicitly implements
those contracts. No local state or truncation metric alone establishes record equivalence.

## External boundaries

- Google d3 circuit/geometry/schedule files are caller inputs, not package data or noise calibration.
- PyMatching is an optional downstream decoder dependency.
- CUDA-Q is an isolated plugin workload executed in a separate environment and process.
- Explicit serialized channel files are derived caches, not automatically scientific data.
- Distribution artifacts include only the current package and shipped documentation inventory.

## Execution topology

The service supervisor owns a three-lane fresh-process plan: bounded CPU concurrency, serial
host-heavy CPU execution, and serial GPU execution under a cross-process lock. The parent does not
import CUDA runtimes. Process-group cleanup, fail-closed GPU admission, single-writer aggregation,
and atomic summaries are architectural requirements, not test-runner conveniences.

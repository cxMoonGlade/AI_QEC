# Simulator CUDA-QX frontend-only design pre-registration

**Status:** read-only frontend/circuit-construction extraction from local
vendored CUDA-QX: `external/baselines/cudaqx`. Do not edit the vendored
baseline. This document is intentionally **not** an error-model preregistration.

## Scope Correction

CUDA-QX is used here only as a reference for **frontend construction**:

- how a QEC code object exposes geometry, qubit roles, and logical-operation facts;
- how logical/stabilizer operations are named and checked;
- how a memory-circuit experiment is assembled from a code and an operation;
- how shot records are shaped and returned.

CUDA-QX error construction is **not adopted** for this simulator. In particular,
the following are explicitly out of scope for this frontend study:

- CUDA-QX `NoiseModel` design;
- CUDA-QX DEM/MSM error-construction internals;
- CUDA-QX `error_ids`;
- tensor-network decoder correlated priors;
- any CUDA-QX coupling semantics.

Our coupled-error model remains governed by the existing Axis-1 / Axis-2
contract:

- **Axis 1:** instantaneous joint-channel / joint-Lindbladian coupling;
- **Axis 2:** explicit shared source trajectories and fan-out over time.

## Load-Bearing Local References

- `external/baselines/cudaqx/libs/qec/include/cudaq/qec/code.h`
  - `operation` enum: `stabilizer_round`, `prep0`, `prep1`, `prepp`, `prepm`,
    logical gates.
  - `code` interface: data/ancilla counts and operation declarations. Matrix
    getters were observed but are explicitly not adopted as our simulator API.
- `external/baselines/cudaqx/libs/qec/include/cudaq/qec/experiments.h`
  - `sample_memory_circuit(code, operation, numShots, numRounds, ...)` shape.
- `external/baselines/cudaqx/libs/qec/lib/experiments.cpp`
  - early checks for missing prep/stabilizer operations;
  - memory-circuit result shaping into syndrome rows and data rows.
- `external/baselines/cudaqx/docs/sphinx/examples/qec/python/custom_repetition_code_fine_grain_noise.py`
  - Python-side custom code registration pattern and operation encodings.

## Extracted Frontend Rules

### F-CUDAQX-1. Code Object Is A Construction Input

CUDA-QX `code` exposes code-owned static facts and operation kernels; experiment
helpers consume the code. The code object does not own the simulator run loop.

**Binding for us:** keep `CodeSpec` and XZZX constructors as construction inputs.
`Simulator.run(...)` remains code-agnostic.

### F-CUDAQX-2. Operations Are Named And Checked

CUDA-QX names operations (`prep0`, `prep1`, `prepp`, `prepm`,
`stabilizer_round`, logical gates) and rejects an experiment if the requested
operation is missing.

**Binding for us:** add a small frontend schedule/operation contract before
expanding XZZX:

```
OperationSpec("prep0")
OperationSpec("stabilizer_round")
OperationSpec("final_readout")
ScheduleTemplate([...])
```

The compiler must fail early if a `CodeSpec` lacks what the schedule needs.

### F-CUDAQX-3. Parity And Observable Matrices Are Not The Simulator API

CUDA-QX exposes `get_parity_x`, `get_parity_z`, `get_parity`, and
`get_observables_x/z`. This is frontend structure, not hidden noise truth.

**Correction:** do not translate this into a public matrix-algebra surface for
`qec_twin.simulator`. For this simulator, the public frontend surface is circuit
construction, schedule/record layout, artifact emission, and record loading.
Stabilizer-code algebra can remain private validation inside a `CodeSpec`
compiler, but it must not become the simulator ontology.

### F-CUDAQX-4. Memory-Circuit Records Have A Stable Shape

CUDA-QX `sample_memory_circuit` returns syndrome rows and final data rows. Its
implementation separates first-round bare syndrome measurements from later
round-to-round flips.

**Binding for us:** formalize our own `RecordLayout` before adding richer XZZX:

```
round_measurements[shot, round, check]
detectors[shot, detector]
final_data[shot, data_qubit]
observables[shot, logical]
```

Current `.b8` artifacts remain the serialized detector/observable surface, but
the compiler should preserve the structured layout in metadata or a sidecar
schema.

### F-CUDAQX-5. Custom Codes Register Operations, Not Simulator Branches

CUDA-QX's Python custom-code example registers operation encodings on a code
class. The simulator does not special-case that code.

**Binding for us:** XZZX should become one registered `CodeSpec` / schedule
constructor among several. A user-defined code should be able to provide the
same frontend facts and compile through the same path.

## Implemented Frontend-Only Slice

Implemented in `qec_twin.simulator` only, still untracked until the user decides
the frontend is ready to track:

1. `operation.py`
   - `OperationSpec` and `OperationSet`;
   - allowed operations: `prep0`, `prep1`, `prep_plus`, `prep_minus`,
     `stabilizer_round`, `final_readout`;
   - CUDA-QX-style aliases `prepp` / `prepm`;
   - schedule requirement checks, with evaluator/error metadata keys rejected.

2. `schedule.py`
   - `ScheduleTemplate`;
   - fixed `repeated_memory_v1` template;
   - explicit final-readout policy and detector policy;
   - same-name policy drift is rejected so the manifest cannot claim one
     schedule while the compiler emits another.

3. `record_layout.py`
   - structured record layout for round/check/final-data/logical records;
   - mapping from layout names to `CircuitIR` measurement keys and `.b8`
     detector/observable order;
   - final-readout basis conflicts fail directly at the layout layer.

4. Tests
   - CUDA-QX-inspired custom repetition code compiles without special casing;
   - XZZX smoke still compiles through the same schedule interface;
   - missing operation/schedule requirements fail before artifacts are written;
   - record-layout order matches `CircuitIR`, persisted `manifest.json`, and
     `.b8` detector/observable order;
   - non-XZZX mixed-basis smoke compiles through the same frontend path.

## Explicit Non-Goals

- Do not integrate CUDA-QX as a runtime dependency.
- Do not modify `external/baselines/cudaqx`.
- Do not import CUDA-QX noise construction.
- Do not import CUDA-QX DEM/MSM/error-ID construction as our coupling model.
- Do not change Axis-1 / Axis-2 coupling semantics based on CUDA-QX.

## Open Frontend Questions

1. Should `RecordLayout` be written as JSON sidecar now, or only embedded in
   `manifest.json` until the frontend is tracked?
2. Should the next real-code target be a CUDA-QX-style custom repetition code
   smoke, or a shipped/standard XZZX Stim/circuit wrapper?
3. Should operation names remain strict strings, or become an enum only after
   the public API stabilizes?

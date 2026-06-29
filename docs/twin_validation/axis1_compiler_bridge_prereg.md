# Axis-1 compiler bridge preregistration

Date: 2026-06-28

Status: theory-first preregistration plus implementation ledger. Sections 1-14
record the pre-run contract; section 15 records the 2026-06-28 implementation
slice that followed it. This document does not claim that the coupled QEC
teacher is implemented.

Bound sources:

- `CONTEXT.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/METRICS.md`
- `docs/twin_validation/qec_coupling_simulator_build_contract.md`
- `docs/twin_validation/h3_h5_dt_g2band_prereg.md`
- `docs/twin_validation/simulator_architecture_prereg.md`
- `src/qec_twin/forward/joint_lindbladian.py`
- `tests/test_joint_lindbladian.py`
- `src/qec_twin/simulator/README.md`
- `src/qec_twin/simulator/circuit_ir.py`
- `src/qec_twin/simulator/compiler.py`
- `src/qec_twin/simulator/code_spec.py`
- `src/qec_twin/simulator/noise_spec.py`

Epistemic classes follow `docs/METRICS.md`:

- (a) exact: theorem, identity, or mechanically checked invariant.
- (b) prediction band: falsifiable quantitative expectation.
- (c) heuristic gate or design constant: gating/prior only, never a premise for a
  physics conclusion.

## 1. Current earned repo state

The current implementation has an Axis-1 primitive, but not an Axis-1 QEC
compiler bridge.

Earned:

- `qec_twin.forward.joint_lindbladian` builds a Liouvillian from a list of
  Hamiltonian terms and collapse operators, exponentiates one joint generator
  for a positive `dt`, converts the result to Kraus evidence, and exposes
  composed-vs-joint diagnostics. The primitive is intentionally GPU-first.
- `tests/test_joint_lindbladian.py` checks the primitive against independent
  QuTiP/scipy oracle construction, including G2 exact-zero and nonzero
  composed-vs-joint witnesses. This is evidence about the primitive, not about a
  full QEC simulator.
- `docs/METRICS.md` now contains the G2 metric row: composed-vs-joint channel
  infidelity, using process/entanglement infidelity between trace-normalized
  Choi states. The exact-zero witness includes Liouvillian commutator and
  superoperator distance thresholds.
- `docs/twin_validation/h3_h5_dt_g2band_prereg.md` fixes the initial dt bracket
  and G2 expectations for `ZZ x T2` exact-zero and `DR x ZZ` nonzero rows.
- `qec_twin.simulator` already owns the QEC frontend: `CodeSpec`, `CircuitIR`,
  `compile_code_spec`, Stim artifacts, `.dem`, `.b8`, and decoder plumbing.
  This frontend currently emits a Stim-compatible circuit/record object, not an
  analog schedule.
- `noise_spec.py` supports frontend Pauli noise and
  `SourceStimPauliProjectionSpec`. The source projection is a reduced Pauli
  projection for Stim artifacts and is not Axis-1 analog coupling.

Not earned at preregistration time; now partially implemented by section 15:

- Compiler-generated `SubstepSchedule` exists for `CircuitIR` and `CodeSpec`
  inputs. It remains `representability="analog_schedule_metadata_only"`.
- `CircuitIR`/`CodeSpec` operations can be lowered to public substep metadata:
  active/idle qubits, duration brackets, measurement/reset boundaries, record
  refs, and provenance. They do not carry hidden `H`, `c`, Kraus, PTM, channel,
  or source truth.
- A narrow Axis-1 G2 bridge consumes compiler-generated schedules and calls
  `joint_lindbladian` diagnostics for the preregistered two-row gate only.

Still not earned:

- No full analog record emission, qutrit/leakage integration, or full-error
  coupled QEC teacher is claimed.
- Axis-2 shared-source and memoryful-noise files are present, but this
  preregistration is read-only with respect to Axis-2.

## 2. Why a minimal compiler seam comes first

The next slice must not be a hand-written G2 demo. It must prove that an actual
frontend circuit can produce the analog substep rows consumed by Axis-1.

The seam is:

```text
CodeSpec / CircuitIR
  -> SubstepSchedule / AnalogSubstepIR
  -> mechanism primitive selection
  -> H_list, c_list per substep
  -> joint_lindbladian
  -> channel evidence / G2 frontend gate
```

Reasons:

1. `CircuitIR` and Stim `TICK` express record/order structure. They do not carry
   physical duration, active analog mechanisms, or idle windows by themselves.
2. Axis-1 coupling is a within-substep claim: the correct object is
   `exp((sum_i L_i) dt)` for the mechanisms active in the same physical
   substep. Sequential `E1 o E2` inside the substep is the negative control.
3. Composition across substeps is allowed. The forbidden move is composing
   mechanism channels inside one substep when those mechanisms are simultaneous.
4. The bridge needs provenance. A G2 frontend gate must be able to reject
   hand-written fake substeps unless the test explicitly declares an oracle unit.
5. A minimal seam lets the project later attach richer compilers or hardware
   schedules without rewriting the physics primitive.

## 3. External design patterns surveyed

This survey uses mature frameworks for IR/schedule/frontend lessons only. Their
noise models are not adopted as this project's Axis-1 error-coupling semantics.

### Stim

Relevant pattern:

- Stim is the best fit for this repo's existing QEC artifact path: Clifford
  circuits, measurement records, detectors, observables, `.dem`, and fast
  detector sampling.
- `TICK` is a layer/time-advance annotation. The Stim documentation states that
  it has no simulation effect, but is useful to tools that transform or visualize
  circuits and need same-time-step structure, including noise/crosstalk tooling.
- `DETECTOR` and `OBSERVABLE_INCLUDE` are record-map annotations. They are
  essential for the artifact/decoder side but are not analog dynamics.

Adopt:

- Keep Stim as the mature QEC artifact and record compiler/backend.
- Use `TICK` as a structural boundary input to the schedule extractor.
- Preserve detector/observable record mapping through the schedule manifest.

Do not adopt:

- Do not treat Stim `TICK` as a physical `dt`.
- Do not treat a Stim Pauli/noise circuit or `.dem` as analog joint-L truth.
- Do not encode Axis-1 coupling by inserting local Stim error channels.

Source: Stim gates reference,
<https://github.com/quantumlib/Stim/blob/main/doc/gates.md>.

### Cirq

Relevant pattern:

- Cirq represents a circuit as ordered `Moment`s; a `Moment` contains operations
  acting during one abstract time slice and on disjoint qubit sets.
- Cirq explicitly warns that a `Moment` need not equal real hardware or simulator
  scheduling, though it can be used that way.
- Insert strategies show a useful separation between operation generation and
  moment placement.

Adopt:

- Use the Cirq-style conceptual rule: one substep/moment has a set of operations
  with no conflicting qubit support, plus an explicit policy for operations that
  share qubits.
- Treat moment/substep grouping as schedule metadata, not physics by itself.

Do not adopt:

- Do not make Cirq the immediate source of record truth, because the repo already
  needs Stim detector/observable artifacts.
- Do not adopt Cirq's default noise insertion semantics for Axis-1.

Sources:

- Cirq circuit construction,
  <https://quantumai.google/cirq/build/circuits>.
- Cirq `Moment` reference,
  <https://quantumai.google/reference/python/cirq/Moment>.

### Qiskit transpiler and Aer

Relevant pattern:

- Qiskit's `Target` combines backend instruction support, connectivity, timing
  information, `dt`, alignment constraints, and instruction properties.
- `InstructionDurations` and scheduler passes provide a mature separation
  between circuit DAG order and scheduled start/stop times.
- ASAP and ALAP scheduling are explicit policies. `PadDelay` fills idle windows
  with delay instructions.
- Qiskit Aer's `NoiseModel` demonstrates gate/qubit-specific noise hooks and
  duration-aware thermal relaxation examples.
- Aer also documents that non-local qubit quantum errors are outside
  `NoiseModel` and should be handled by a custom transpiler pass.

Adopt:

- Use a duration-policy table that is separate from the logical circuit.
- Make idle windows explicit, not implicit.
- Carry backend/device timing provenance in the schedule manifest.
- Keep the door open for Qiskit-style importers by making `SubstepSchedule` a
  data contract rather than a Stim-only object.

Do not adopt:

- Do not use Qiskit Aer's local gate noise objects as Axis-1 joint-L semantics.
- Do not require Qiskit as the first implementation dependency unless a future
  slice needs hardware-target transpilation that Stim/CircuitIR cannot express.
- Do not treat delay padding as physical evidence unless its duration source is
  recorded and epistemically classified.

Sources:

- Qiskit `Target`,
  <https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.Target>.
- Qiskit `InstructionDurations`,
  <https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.InstructionDurations>.
- Qiskit `ASAPScheduleAnalysis`,
  <https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.passes.ASAPScheduleAnalysis>.
- Qiskit `ALAPScheduleAnalysis`,
  <https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.passes.ALAPScheduleAnalysis>.
- Qiskit `PadDelay`,
  <https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.passes.PadDelay>.
- Qiskit Aer noise tutorial,
  <https://qiskit.github.io/qiskit-aer/tutorials/3_building_noise_models.html>.

### QuTiP and qutip-qip

Relevant pattern:

- QuTiP `mesolve` uses Hamiltonians and collapse operators to simulate Lindblad
  master-equation dynamics.
- qutip-qip demonstrates a gate-to-pulse compiler: circuit gates are decomposed
  into native gates, mapped to pulse-level controls, scheduled, then run through
  open-system solvers.
- qutip-qip separates model/Hamiltonian definitions, gate compiler,
  scheduler, pulse representation, and noise attachment.

Adopt:

- Use QuTiP/scipy as independent oracle/reference tooling for small cases.
- Mirror the separation between schedule metadata, mechanism-to-Hamiltonian
  lowering, and open-system evolution.

Do not adopt:

- Do not replace the canonical G2 primitive with qutip-qip.
- Do not depend on qutip-qip pulse compiler output shape in the first bridge,
  because the repo's QEC record and detector artifact path is Stim-based.

Sources:

- QuTiP Lindblad solver,
  <https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html>.
- qutip-qip pulse-level circuit simulation,
  <https://qutip-qip.readthedocs.io/en/stable/qip-processor.html>.

### PennyLane and CUDA-Q/CUDA-QX

Relevant pattern:

- PennyLane's `QuantumScript`/tape split is a useful reminder that immutable
  operation-plus-measurement IR can be separated from queuing/user syntax.
- Local CUDA-QX notes already classify CUDA-QX as a read-only frontend reference
  for operation naming and memory-circuit shape; it is not adopted as an
  Axis-1 runtime compiler in this slice.

Adopt:

- Prefer immutable, serializable schedule data.
- Keep backend adapters behind explicit representability tags.

Do not adopt:

- Do not adopt PennyLane or CUDA-Q noise/runtime semantics for Axis-1.

Source:

- PennyLane tape/`QuantumScript`,
  <https://docs.pennylane.ai/en/stable/code/qml_tape.html>.

## 4. Architecture decision for this slice

Decision D1: use mature frameworks at the boundaries, not as a substitute for the
Axis-1 semantics.

- The first mature compiler/backend remains Stim for QEC artifacts and detector
  record mapping.
- The new schedule seam follows mature framework patterns:
  - Stim for `TICK`, detector, observable, and QEC artifact provenance.
  - Cirq-style moments for same-substep operation grouping.
  - Qiskit-style duration tables, delay/idle explicitness, and backend timing
    provenance.
  - QuTiP-style `H` plus `c_ops` oracle vocabulary.
- The schedule contract must be adapter-friendly. Later importers may accept
  Stim circuits, Cirq circuits, or Qiskit scheduled DAGs, but the Axis-1 bridge
  consumes only `SubstepSchedule`.

Decision D2: the first implementation must be minimal and real.

- Minimal: it does not implement a full analog compiler, full record emission, or
  leakage/qutrit physics.
- Real: it must derive substeps from `CircuitIR`/`CodeSpec` provenance, not from
  handwritten G2 rows.

Decision D3: the bridge does not own mechanism truth.

- `SubstepSchedule` names operation/time/support facts.
- A mechanism primitive library maps a substep plus parameter set into lifted
  `H_list` and `c_list`.
- `joint_lindbladian` remains the primitive that actually exponentiates the
  joint generator.

## 5. Minimal data contracts

These are preregistered fields for the next implementation. Names may change
slightly during code review, but the information content should not disappear.

### `SubstepSchedule`

Required fields:

- `schema_version`: schedule schema version. (c)
- `source_kind`: one of `code_spec_compiler`, `circuit_ir`, `stim_circuit`,
  `cirq_circuit`, `qiskit_scheduled_dag`, or `oracle_unit`. The first production
  path should be `code_spec_compiler` or `circuit_ir`; `oracle_unit` is allowed
  only inside tests that explicitly declare an oracle. (c)
- `source_hash`: stable hash of the input `CodeSpec`, `CircuitIR`, or imported
  circuit. (c)
- `schedule_template`: e.g. `repeated_memory_v1` for the current compiler. (c)
- `num_qubits`: number of computational qubits in the schedule. (a when derived
  from validated IR)
- `qubit_roles`: data/ancilla/other role metadata, if known. (c)
- `qubit_coords`: geometry coordinates, if known. Coordinate presence has no
  physics effect by itself. (c)
- `substeps`: ordered tuple of `AnalogSubstepIR`. (a as a data ordering
  invariant)
- `record_layout_ref`: optional pointer/hash to detector/observable layout and
  measurement record manifest. (c)
- `duration_policy`: identifier and bracket table used to fill `dt_ns`. (c)
- `representability`: must include `analog_schedule_metadata_only` until an
  analog teacher carrier exists. (c)
- `visibility`: schedule construction metadata is learner-public only if it is
  part of declared public circuit/device metadata; exact mechanism primitives,
  true channel labels, and teacher IDs remain evaluator-only. (c)

### `AnalogSubstepIR`

Required fields:

- `substep_id`: stable schedule-local ID. (a as a data invariant)
- `round_index`: optional QEC round index. (c)
- `tick_index`: structural tick/layer index from `CircuitIR`/Stim if present.
  (c)
- `order_index`: total order within the schedule. (a)
- `kind`: one of `reset`, `one_qubit_gate`, `two_qubit_gate`, `idle`,
  `measurement`, `barrier`, or `mixed`. (c)
- `operations`: tuple of public operation records with `name`, `targets`,
  optional `basis`, public parameters, and source operation ID. (a/c)
- `active_qubits`: qubits touched by operations in this substep. (a when derived
  mechanically)
- `idle_qubits`: qubits in the schedule support but not active during this
  positive-duration substep. (a when duration/support are defined; c otherwise)
- `participants`: pair/group support for two-qubit or higher-arity operations.
  First slice supports arity 1 and 2 only; arity > 2 must fail closed. (c)
- `dt_ns_nominal`: nominal duration in nanoseconds, if positive. (c)
- `dt_ns_bracket`: bracket `(lo, hi)` in nanoseconds. (c)
- `dt_source`: source label such as `h3_h5_v1`, `backend_target`, or
  `imported_schedule`. (c)
- `mechanism_slots`: allowed mechanism selectors, not actual `H`/`c_ops`
  payloads. Example selectors: `drive`, `zz_spectator`, `t1`, `t2`, `readout`.
  (c)
- `measurement_keys`: record-boundary keys for measurement/reset substeps. These
  preserve mapping but do not imply analog outcome emission. (c)
- `window_support`: local Hilbert-space support to which mechanisms will later be
  lifted. (c)
- `generated_by_compiler`: must be true for frontend G2 gates. (a as a data
  invariant)

Forbidden fields:

- Exact channel matrices, PTMs, Kraus operators, oracle teacher IDs, or
  evaluator-only source timelines.
- Precomputed composed-vs-joint metrics.
- Axis-2 source values.

## 6. dt source and bracket strategy

The initial duration policy reuses
`docs/twin_validation/h3_h5_dt_g2band_prereg.md`.

Duration brackets:

- 1q gate: `[20, 30] ns`, nominal `25 ns`. (c)
- 2q/CZ-like gate: `[25, 45] ns`, nominal `30 ns`. (c)
- Idle: `[0, 300] ns`, schedule-dependent. (c)
- Readout: `[100, 1000] ns`. (c)
- Reset: `[100, 500] ns`. (c)

Rules:

1. A substep with `dt_ns_nominal <= 0` must not call
   `joint_lindbladian`; it is a structural boundary only. (a)
2. A positive-duration substep must record its bracket and source. (c)
3. G2 reports must sweep the bracket, not only the nominal point. (c)
4. The existing `DR x ZZ` physical area-preserving prediction band is reused:
   `1 - F_e in [6e-4, 3e-3]` under the declared H3/H5 setup. (b)
5. The existing fixed-drive diagnostic band is reused:
   `1 - F_e in [4e-4, 4e-3]` under the declared diagnostic setup. (b)
6. The `ZZ x T2` exact-zero row remains exact only when the Liouvillian
   commutator and superoperator distance witnesses pass the ledger thresholds:
   commutator <= `1e-12`, superoperator distance <= `1e-10`. The thresholds are
   numerical gates, not new physics constants. (a/c)

## 7. Initial handling by operation kind

### One-qubit gates

Initial handling:

- One-qubit operations form `one_qubit_gate` substeps.
- The mechanism mapper may attach drive Hamiltonian slots to targets and idle or
  spectator slots to non-target support qubits only if `dt > 0`.
- Multiple one-qubit operations can share one substep only when their target sets
  are disjoint.

Claim boundary:

- A one-qubit gate row is schedule metadata until the mechanism mapper lowers it
  to `H_list` and `c_list`.

### Two-qubit gates

Initial handling:

- Two-qubit operations form `two_qubit_gate` substeps.
- Bundled two-qubit layers are represented as multiple pair participants in one
  substep if the pairs are disjoint.
- Unsupported overlapping pairs in the same substep must fail closed or be split
  by an explicit scheduling policy.

Claim boundary:

- A `CX` in the current compiler must not be silently relabeled as a `CZ`.
  Gate-family tags and mechanism mapping must be explicit.

### Idle

Initial handling:

- Idle qubits are derived from `all schedule-support qubits - active_qubits` for
  each positive-duration substep.
- Idle-only substeps may be emitted only when the schedule or duration policy
  declares a positive idle duration.

Claim boundary:

- Current frontend `NoiseBuilder.during_idle` is Pauli Stim-noise insertion at
  explicit `TICK`; it is useful as a placement reference but is not analog idle
  dynamics.

### Measurement

Initial handling:

- Measurement substeps preserve measurement keys and record mapping.
- First slice treats measurement as a boundary unless a readout mechanism slot is
  explicitly selected and bracketed.

Claim boundary:

- No full analog measurement record emission is claimed in this slice.

### Reset

Initial handling:

- Reset substeps preserve the boundary and target set.
- First slice treats reset as structural unless a reset mechanism slot is
  explicitly selected and bracketed.

Claim boundary:

- Reset channel physics is not required for the first G2 frontend gate.

### Multi-qubit gates beyond arity 2

Initial handling:

- Arity > 2 must fail closed in the first slice.
- Later support may lower a higher-arity operation into declared native substeps,
  but the lowering must be recorded in the schedule provenance.

## 8. Axis-1 bridge contract

The bridge consumes `SubstepSchedule` and mechanism primitives. It does not own
frontend circuit construction and does not own metric definitions.

Required algorithm:

```text
for substep in schedule.substeps:
    if substep.dt_ns_nominal <= 0:
        record structural boundary only
        continue

    selected = mechanism_library.select(substep, params)

    H_list = []
    c_list = []
    for primitive in selected:
        lifted = primitive.lift_to(substep.window_support)
        H_list.extend(lifted.H_terms)
        c_list.extend(lifted.c_ops)

    channel = assemble_substep_channel(
        H_list=H_list,
        c_list=c_list,
        dt=substep.dt_ns_nominal,
        device="cuda",
    )

    emit channel evidence and, when requested, G2 diagnostics
```

Required Axis-1 invariant:

```text
L_substep = -i[sum_j H_j, .] + sum_k D[c_k]
E_substep = exp(L_substep dt)
```

Sequential composition inside a substep is forbidden unless the test is a
negative control:

```text
E_bad = exp(L_2 dt) exp(L_1 dt)
```

Composition across different substeps is allowed:

```text
E_cycle = E_substep_N ... E_substep_2 E_substep_1
```

Visibility:

- The schedule may be public construction metadata.
- Mechanism parameters, exact generated channels, teacher labels, and oracle
  primitive IDs are evaluator-only unless explicitly declared public.

Axis-2:

- The bridge does not consume `SourceTimeline`, source fan-out, or
  `SourceStimPauliProjectionSpec` in this slice.

## 9. G2 frontend gate

The frontend G2 gate reuses the existing G2 metric. It must not introduce a new
project-defined metric when the ledgered metric already exists.

Input requirements:

- `SubstepSchedule.generated_by_compiler == true`.
- Non-oracle `source_kind` must be `code_spec_compiler`, `circuit_ir`, or a
  declared external importer.
- `source_hash` must be present.
- Each tested row must identify the source substep and source operation IDs.

Output rows:

- `substep_id`
- `source_kind`
- `source_hash`
- `kind`
- `operations`
- `dt_ns_nominal`
- `dt_ns_bracket`
- `mechanism_pair`
- `liouvillian_commutator_norm`
- `superop_distance`
- `one_minus_F_e`
- `expected_class`: exact-zero, prediction-band, or negative-control fail
- `epistemic_class`: (a), (b), or (c)

Required rows for the first gate:

- `ZZ x T2` exact-zero row: commutator and superoperator distance witnesses must
  satisfy the existing thresholds. (a/c)
- `DR x ZZ` nonzero row: must land in the existing H3/H5 band under the declared
  area-preserving setup. (b)
- Sequential-composition negative control: replacing joint-L with within-substep
  sequential composition must be caught on the `DR x ZZ` row. (a/c)
- dt sweep row: repeat the nonzero row at bracket endpoints and nominal point.
  (b/c)
- provenance row: prove that the substep came from compiler output, not a
  handwritten metric fixture. (a/c)

## 10. Anti-toy acceptance tests

The next implementation should not be accepted unless these tests are present or
explicitly waived.

1. `ZZ x T2` exact-zero:
   - Build the row from a compiler-generated substep.
   - Verify Liouvillian commutator <= `1e-12` and superoperator distance <=
     `1e-10`. (a/c)

2. `DR x ZZ` nonzero:
   - Build the row from a compiler-generated substep.
   - Check the H3/H5 `1 - F_e` prediction band under the declared setup. (b)

3. Bad sequential composition caught:
   - Run a negative-control bridge that composes mechanism channels within one
     substep.
   - It must fail the `DR x ZZ` G2 row or produce a distinguishable diagnostic.
     (a/c)

4. dt sweep:
   - Evaluate low, nominal, and high dt values from the bracket.
   - Record physical area-preserving and fixed-drive diagnostic modes when both
     are enabled. (b/c)

5. Compiler-generated substep, not hand-written fake:
   - The test must start from `CodeSpec` or `CircuitIR`.
   - The frontend gate must reject a structurally similar schedule with missing
     `source_hash` or `generated_by_compiler == false`. (a/c)

6. Idle detection:
   - For a known circuit layer with an active gate on one support qubit and no
     operation on another, the latter appears in `idle_qubits` only for a
     positive-duration substep. (a/c)

7. Measurement/reset boundary:
   - A measurement or reset boundary preserves record keys/targets and does not
     pretend to emit analog measurement outcomes. (a/c)

8. Multi-pair layer:
   - A disjoint two-qubit layer is represented as one substep with multiple pair
     participants or an explicitly recorded split policy.
   - Overlapping pairs fail closed. (a/c)

9. Axis-2 guard:
   - A `SourceStimPauliProjectionSpec` or `SourceTimeline` artifact cannot
     satisfy the Axis-1 G2 representability check. (a/c)

## 11. Open risks, blockers, and decisions

### R1. Mature compiler choice

The user preference is to prioritize mature open-source framework support. This
preregistration does that at the boundary by keeping Stim/PyMatching as the
first mature QEC artifact stack and by designing `SubstepSchedule` as an adapter
target for Cirq/Qiskit importers.

Decision still needed:

- Whether the first code slice should add only `CircuitIR -> SubstepSchedule`, or
  also add a read-only Stim importer path that preserves `TICK`/record
  provenance.

Recommended first slice:

- Add `CircuitIR -> SubstepSchedule` first, because the repo already owns
  `CodeSpec -> CircuitIR -> Stim artifacts`. Add Stim import after the data
  contract is stable.

### R2. Current compiler gate family

`compile_code_spec` currently emits a simple parity-check schedule using `CX` and
basis rotations. The build contract discusses a CZ-like schedule for the G2
slice.

Decision still needed:

- Use current `CX` compiler output for generic schedule-provenance tests, then
  add an explicit CZ-capable schedule template for the G2 mechanism rows; or
- Add a hand-authored `CircuitIR` fixture with CZ operations only as an oracle
  schedule test.

Recommended first slice:

- Do not silently map `CX` to `CZ`. Start with generic schedule extraction tests
  from current compiler output, then add a declared CZ template or importer for
  G2.

### R3. dt is not in Stim/CircuitIR

Stim `TICK` and current `CircuitIR` ticks are structural. They do not supply
physical durations.

Decision still needed:

- Whether duration policy lives in `simulator` as schedule metadata or in
  `mechanisms` as backend/device metadata.

Recommended first slice:

- Store only the selected policy ID and bracketed `dt` values in
  `SubstepSchedule`; let mechanism lowering own physical parameters.

### R4. Measurement/reset analog physics

Readout and reset brackets exist, but first G2 does not require full analog
readout/reset dynamics.

Decision still needed:

- Whether first bridge should skip measurement/reset channel lowering or include
  placeholder mechanism slots.

Recommended first slice:

- Preserve boundaries and record keys only. Require explicit opt-in before
  lowering measurement/reset mechanisms.

### R5. Local Hilbert window lifting

The bridge must lift mechanism primitives onto a local support before calling
`joint_lindbladian`. Incorrect lifting could create false coupling or miss
spectators.

Decision still needed:

- Minimal window rule for the first G2 row: target pair only, target plus one
  spectator, or operation-local support plus all declared idle participants.

Recommended first slice:

- Use the smallest support required by the G2 row and record `window_support`
  explicitly. Do not infer all-to-all spectators.

### R6. GPU availability

`joint_lindbladian` is CUDA-gated, and the project policy is GPU-first for
serious simulator/compiler execution. Any test that runs a circuit, schedule
bridge, artifact/compiler path, or G2 row must have CUDA visibility from the
`aiqec` environment.

Decision still needed:

- Whether CI has a GPU lane for this gate or whether these tests are run only on
  the workstation/GPU lane until CI GPU coverage exists.

Recommended first slice:

- Do not add CPU-only circuit/schedule-bridge tests. Pure schema/type/static
  checks may exist as code-review or lint support, but they must not be counted
  as acceptance tests for this slice unless wrapped in the same GPU-gated test
  lane. Mark circuit, compiler, schedule-bridge, and G2 tests with CUDA
  requirements and run them on the workstation/GPU lane.

## 12. Non-scope for this round

Explicit exclusions:

- No Axis-2 extension.
- No `SourceTimeline` fan-out semantics.
- No reduced Pauli source projection as Axis-1 evidence.
- No full analog measurement record emission.
- No qutrit/leakage integration.
- No claim that the full coupled QEC teacher is complete.
- No new metric outside the `docs/METRICS.md` ledger.
- No replacement of the existing Stim artifact path.
- No broad compiler rewrite.

## 13. Next implementation slice

Slice A: schedule seam only.

1. Add immutable schedule dataclasses in the simulator responsibility area:
   `SubstepSchedule`, `AnalogSubstepIR`, and a duration-policy value object.
2. Add a `CircuitIR -> SubstepSchedule` extractor:
   - groups operations by tick/layer,
   - splits or rejects overlapping operations,
   - records active/idle qubits,
   - preserves measurement/reset boundaries,
   - attaches H3/H5 bracketed duration metadata,
   - stores source hash and provenance.
3. Add GPU-gated anti-toy tests for provenance, idle detection,
   reset/measurement boundary retention, overlapping-pair failure, and Axis-2
   representability guard whenever they execute the compiler/schedule bridge.
   Do not add CPU-only pytest acceptance tests for this slice.

Slice B: Axis-1 G2 bridge.

1. Add a small mechanism-mapper registry for the two preregistered rows:
   `ZZ x T2` and `DR x ZZ`.
2. Lift selected primitives to the declared local support.
3. Call `joint_lindbladian` once per positive-duration substep.
4. Emit G2 rows using the existing metric ledger and H3/H5 brackets.
5. Add CUDA-gated tests for exact-zero, nonzero band, dt sweep, and bad
   sequential-composition negative control.

Slice C: mature-framework importer hardening.

1. Add read-only Stim importer support for `TICK`, detector, observable, and
   coordinate provenance if the in-repo `CircuitIR` extractor is stable.
   Implemented for the schedule-safe Stim subset on 2026-06-28. (c)
2. Consider Cirq or Qiskit scheduled-DAG import only if a concrete hardware
   schedule source requires it.

## 14. Anti-toy review recommendation

Before writing the Axis-1 bridge, open a multi-lane anti-toy review:

- Lane 1: compiler provenance and schedule semantics.
- Lane 2: physics correctness of joint-L versus within-substep composition.
- Lane 3: metric/claim discipline against `docs/METRICS.md`.
- Lane 4: Axis-2 isolation and source-projection non-contamination.

The review should happen after Slice A and before Slice B, because Slice A is the
point where fake hand-written rows can accidentally enter the system.

## 15. Implementation note — Slice B first gate

Date: 2026-06-28

Slice B added the minimal frontend G2 bridge:

- `SubstepSchedule -> axis1_g2_frontend_gate(...)`
- `write_axis1_g2_evidence(...) -> g2_jointL.json`
- supported rows: `ZZ x T2` and `DR x ZZ`
- supported purpose: G2 evidence rows only, not full analog record emission

Anti-toy review resolution:

- The build-contract first gate's one-qubit substep is the contextual row
  `DR + ZZ + T2 + T1`, not the H-only diagnostic `DR + ZZ`.
- The H-only row exposed a useful diagnostic finding at the lower part of the
  one-qubit dt bracket, but it is not the canonical frontend G2 row because it
  omits always-active Markovian context declared in the build contract.
- The implemented bridge therefore reports `mechanism_pair=("DR", "ZZ")` with
  `context_mechanisms=("T2", "T1")`.

Observed result:

- `ZZ x T2` exact-zero rows pass the registered structural and channel-level
  witnesses across the CZ duration sweep. (a/c)
- `DR x ZZ` rows are clearly nonzero by Liouvillian commutator and superoperator
  distance. (a/c)
- The contextual `DR + ZZ + T2 + T1` rows pass the registered `DR x ZZ`
  `[6e-4, 3e-3]` exact-channel band over the one-qubit dt sweep. (b/c)
- `g2_jointL.json` carries `verdict`, `content_hash`, `measured_on`, metric
  convention, and per-row contract aliases (`pair_ij`, `substep`,
  `commutator_fro`, `witness`, `value`, `predicted_band`, `in_band`, `class`).
  It also carries source operation IDs, operation records, `dt_ns_nominal`, a
  headline `epistemic_class`, and a machine-readable `epistemic_classes`
  breakdown. It is not a `.stim/.dem/.b8` simulator-run artifact. (c)
- The folded anti-toy details include exact-zero control, a broken-assembler
  negative control, physical/fixed-drive bands, Hamiltonian-only power-law
  diagnostics, zeta scaling, and full-context `DR + ZZ + T2 + T1` slope
  findings. The coherent `DR x ZZ` power law remains the gated component; the
  full-context slope is reported as a finding/diagnostic, not silently used as
  the same theorem-grade object. These are gate diagnostics, not new metrics.
  (a/b/c as declared per row)
- `qec_twin.simulator.axis1_g2_runner` builds the fixed `CircuitIR ->`
  `SubstepSchedule` fixture, writes `g2_jointL.json`, and writes
  `g2_jointL.freeze.json` only when no freeze exists. If a freeze exists, the
  runner validates it instead of silently refreshing it; intentional evidence
  updates require `--refresh-freeze`. The freeze validates both evidence-file
  sha256 and manifest `content_hash`; it is an artifact-drift guard only. (a/c)
- The post-implementation anti-toy review closed additional holes: mixed CX/CZ
  layers now associate CZ evidence with the CZ operation's own targets; the G2
  drive row requires an idle spectator on an explicitly declared static-ZZ
  metadata pair; common Axis-2 source metadata keys are rejected before schedule
  extraction; MR boundaries retain both readout and reset slots; the G2 evidence
  writer refuses stale simulator-run artifact directories; and GPU-gated
  acceptance tests fail rather than skip when CUDA is absent. (a/c)
- The bridge now derives a narrow `Axis1MechanismSelectionPlan` from schedule
  metadata before primitive lowering. Active CZ operations supply same-substep
  CZ/ZZ carrier rows and the G2 exact-zero diagnostic row; persistent static-ZZ
  couplings come only from public `axis1_static_zz_couplings` schedule metadata,
  not from CZ history. A one-qubit drive with an idle spectator on a declared
  static-ZZ pair selects the contextual `DR + ZZ + T2 + T1` row; primitive
  Hamiltonian/collapse payloads are introduced only afterward through
  `qec_twin.mechanisms.axis1_primitives` before calling
  `forward.joint_lindbladian`. Rows include the lowered primitive manifest, and
  the evidence manifest includes the selection plan. This is still a local
  two-qubit G2 registry and selector, not a complete hardware mechanism library.
  General schedule-driven mechanism selection remains future work. Current
  guards reject CZ-history static-pair inference, non-drive one-qubit gates as
  DR rows, CX-only static-pair substitution, tampered drive mechanism slots,
  non-Stim stale simulator artifacts such as measurement/count/state files, and
  direction loss in active/spectator DR selections. (c)
- Slice I separates the G2 diagnostic drive primitive from generic frontend-gate
  semantics. `DR` remains the preregistered G2 witness primitive only. Generic
  schedule evidence now lowers supported frontend controls
  `C_XYZ/C_ZYX/H/H_XY/H_XZ/S/S_DAG/SQRT_X/SQRT_X_DAG/SQRT_Y/SQRT_Y_DAG/SQRT_Z/SQRT_Z_DAG/X/Y/Z`,
  `CZ`, and ordered `CX` into exact `CTRL_*` Hamiltonian representatives, then
  combines those controls with the selected Markovian/static-ZZ/readout primitives in one
  `assemble_substep_channel(...)` call. The evidence manifests record
  `ideal_controls` separately from `lowered_mechanisms`, so the control
  representative is not mistaken for a noise primitive and the primitive
  registry is not mistaken for a frontend unitary library. `CX` preserves
  control-target order and is not silently relabeled as `CZ` or static `ZZ`.
  (a/c)
- Compiler provenance is now guarded by both `generated_by_compiler` flags and a
  builder-owned in-process schedule seal. The seal is created only by
  `circuit_ir_to_substep_schedule(...)` /
  `compile_code_spec_to_substep_schedule(...)`, is validated before the G2 bridge
  runs, and is reported in `g2_jointL.json` as schema/validity metadata without a
  public digest. A public `SubstepSchedule(...)` clone with `generated_by_compiler
  == true` no longer satisfies the bridge. This is public-API hardening, not a
  cryptographic cross-process attestation scheme. (a/c)
- Reserved schedule `source_kind` values are now protected at the public
  `CircuitIR` extractor boundary: ordinary callers can only produce
  `source_kind="circuit_ir"` there, while `code_spec_compiler` and `stim_circuit`
  are set only by their compiler/importer wrappers. This prevents a sealed
  CircuitIR schedule from silently posing as an imported Stim or CodeSpec
  schedule. (a/c)
- Slice C added joint-channel carrier evidence:
  `axis1_substep_channel_evidence_manifest(...)` /
  `write_axis1_substep_channel_evidence(...)` consume the same sealed schedule
  and schedule-derived selections, lower supported frontend control terms plus
  `ZZ/T2/T1/T1_UP/T2_B/T1_B/T1_UP_B/RD/RD_B/FSIM_SWAP/FSIM_PHASE`
  primitives, and call
  `forward.joint_lindbladian.assemble_substep_channel` to produce per-row
  channel-carrier summaries. The artifact records the joint-generator form,
  dimension, Kraus count, TP residual, provenance, separate `ideal_controls`,
  and lowered mechanism manifests, but deliberately omits Kraus stacks, Choi
  matrices, and superoperator matrices. It is not record emission or a
  learner-visible channel truth dump. (a/c)
- Primitive lowering now routes through `Axis1PrimitiveRegistry` /
  `default_axis1_primitive_registry()` with registry id
  `axis1_two_qubit_local_primitives_v1`. The G2 and channel-evidence manifests
  record this registry metadata and declare that the registry manifest contains
  no operator payload. The registry now supports the current local two-qubit
  window primitives `DR`, `ZZ`, `T2`, `T1`, computational-subspace
  finite-temperature excitation `T1_UP`, spectator/qubit-B Markovian context
  `T2_B`, `T1_B`, `T1_UP_B`, readout dephasing `RD/RD_B`, and optional
  computational-subspace fSim residual Hamiltonians `FSIM_SWAP/FSIM_PHASE`.
  Ideal frontend controls are lowered by `qec_twin.simulator.axis1_ideal_controls`,
  not by the primitive registry. This is a real lowering contract for the
  current local window, not a complete hardware mechanism library. (c)
- Union-support cluster lowering honors explicitly selected computational-subspace
  finite-temperature excitation primitives `T1_UP/T1_UP_B` by embedding local
  `sigma+` collapse operators in the same joint-L generator. The public
  `Axis1LocalLindbladContextSpec` now carries this context through
  `CircuitBuilder`, `CodeSpec`, and explicit Stim-importer sidecars; it is
  folded into schedule source hashes when present and remains metadata-only
  with no H/c/Kraus/PTM payload. Default schedule-derived selectors still use
  zero-up thermal context unless this public spec explicitly selects the
  primitive and supplies `gamma_up_per_ns`. This is not leakage/qutrit
  integration and not a claim of a complete thermal-relaxation library. (a/c)
- Channel evidence now uses the generic
  `axis1_schedule_joint_channel_selector_v1` plan rather than the G2-only
  selector. It emits schedule-derived joint-channel rows for supported
  one-qubit frontend-control substeps, explicit-duration idle pair/cluster
  substeps, explicit-duration readout pair/cluster substeps, active CZ,
  declared-static-ZZ substeps, supported two-qubit frontend-control substeps,
  and selected <=5q union-support spectator or declared-static-ZZ clusters.
  The G2 metric gate remains separately limited to
  the preregistered exact-zero and prediction rows. (c)
- Channel evidence now carries a `coverage` ledger listing selected substeps,
  omitted substeps with reasons, and participant-window coverage for each
  positive-duration substep. Omitted barrier/measurement/reset/unsupported
  substeps are explicit and are not claimed covered by Axis-1 joint-channel
  evidence. The same ledger reports whether expected public participant windows
  are fully covered, so a row-level pass cannot be mistaken for full-schedule or
  full-substep coverage. (a/c)
- Slice D adds selected-channel state evidence:
  `axis1_state_evolution_evidence_manifest(...)` /
  `write_axis1_state_evolution_evidence(...)` consume the same sealed schedule,
  reuse `axis1_schedule_joint_channel_selector_v1`, assemble each selected
  joint-L channel on CUDA, and apply selected channels in schedule order to an
  exact small-N GPU density matrix initialized at all-zero. Same-substep
  selected windows are supported only when their qubit supports are disjoint;
  they are recorded as one commuting parallel layer, while overlapping selected
  windows fail closed. The artifact records final Z-basis probabilities, trace
  residual, applied layer/substep ledger, coverage, and provenance. It
  intentionally declares no logical gate semantics, no full-schedule operation
  semantics, no analog record emission, no Axis-2 source projection, and no
  leakage/qutrit integration. (a/c)
- Slice E adds measurement-record evidence:
  `axis1_measurement_record_evidence_manifest(...)` /
  `write_axis1_measurement_record_evidence(...)` consume a sealed exact small-N
  schedule, apply the selected joint-L channels on CUDA with the same disjoint
  parallel-layer semantics, and then enumerate exact Pauli-basis measurement
  branches using the schedule measurement keys. X/Y measurements are implemented
  by exact basis rotation before Z-branch enumeration and rotation back
  afterward. The artifact records measurement records, detector/logical records
  derived from public XOR wiring,
  probabilities, total-probability residual, applied substep ledger, coverage,
  and provenance. It does not write `.b8`, decoder outputs, source timelines,
  or channel payload arrays. (a/c)
- Slice E2 adds ideal standalone reset-boundary support inside record evidence:
  reset substeps are applied as a nonselective Z reset-to-zero instrument with
  no measurement key and are recorded in `reset_steps`. This is not a noisy
  reset mechanism and does not claim reset assignment bias or reset-induced
  leakage. (a/c)
- Slice E3 adds ideal Pauli-basis measurement/reset support for the record path:
  `MX/MY/MRX/MRY` use exact single-qubit basis rotations around the existing
  Z-branch enumerator, and `RX/RY` standalone resets use the same exact
  nonselective reset-to-plus-eigenstate semantics. This is a basis-boundary
  instrument only; it does not implement noisy assignment, MIST, leakage, or
  reset infidelity. (a/c)
- Slice F adds sampled `.b8` record carriers:
  `write_axis1_measurement_record_samples(...)` samples the exact Axis-1 record
  distribution with `torch.multinomial` on CUDA and writes
  `detection_events.b8`, `obs_flips_actual.b8`, the exact record evidence JSON,
  and `axis1_sample_summary.json`. It intentionally does not write `.stim`,
  `.dem`, or decoder outputs because the selected joint-L records are not a
  Stim-Pauli/DEM model. (a/c)
- Slice G adds explicit-duration idle lowering:
  `CircuitBuilder.idle(..., duration_ns=...)` is preserved in
  `SubstepSchedule` as a positive-duration idle substep with
  `dt_source="explicit_circuit_idle_duration"`. The generic selector lowers
  even-sized idle supports into disjoint idle-pair joint channels using
  `T2/T1/T2_B/T1_B`. Bracket-only idles keep `dt_ns_nominal=None` and remain
  metadata only; no default idle duration is silently invented. (a/c)
- Slice H is preregistered for explicit-duration readout pre-measurement
  lowering: `CircuitBuilder.measure(..., duration_ns=...)` may be preserved as a
  positive-duration measurement substep. Before the projective measurement
  branch, the generic selector may lower even-sized measured supports into
  disjoint readout-pair joint channels using measurement-induced dephasing
  (`RD/RD_B`) plus `T1/T2/T1_B/T2_B`. This is grounded as the readout-window
  dephasing part of the readout literature, especially Heinsoo 1801.07904
  (readout crosstalk = assignment correlations plus measurement-induced
  dephasing) and Xiong 2509.11822 / Fechant 2505.00674 (modern readout
  dephasing/MIST magnitudes). This slice explicitly does **not** implement
  classical assignment flips, correlated assignment crosstalk, MIST/leakage, or
  reset dynamics; those remain separate instrument/leakage prereg items. (a/c)
- A read-only Stim importer now exists:
  `stim_circuit_to_substep_schedule(...)` preserves `TICK`, `QUBIT_COORDS`,
  measurement records, `DETECTOR`, and `OBSERVABLE_INCLUDE` metadata by
  converting the supported Stim subset into the same sealed `SubstepSchedule`
  contract. Imported Stim schedules expose the sealed public schedule and active
  CZ exact-zero selection, but they do not run the full two-row G2 gate unless a
  public static-ZZ metadata source is available; CZ history alone is not
  promoted to persistent coupling truth. Embedded Stim noise instructions are
  rejected because they are frontend Pauli/record-carrier noise, not Axis-1
  joint-L dynamics. The importer is now directly tested for every supported
  two-qubit frontend control in the generic Axis-1 bridge, not only for
  `CircuitBuilder` inputs. This remains schedule/control metadata, not a
  Stim-Pauli error model. (a/c)
- Slice J adds a compiler-generated CodeSpec record-evidence gate:
  `qec_twin.simulator.axis1_codespec_runner` builds the fixed mixed-basis
  `CodeSpec`, compiles it through `compile_code_spec_to_substep_schedule(...)`,
  runs `write_axis1_measurement_record_evidence(...)`, and writes
  `axis1_measurement_records.freeze.json`. This gate is deliberately not a
  hand-written H/CZ fixture: the evidence has
  `source_kind="code_spec_compiler"`, mixed Pauli measurements, `record_count=128`,
  and `applied_channel_count=8`. After Slice N, its coverage ledger reports
  `full_positive_duration_coverage=true` because multi-spectator one-qubit
  drive substeps are lowered as one union-support cluster channel rather than
  one selected representative spectator pair.
  The freeze validates evidence sha256, content hash, source hash, record count,
  measurement-key count, detector/logical counts, applied-channel count,
  measurement basis, coverage, and primitive-registry id. It is still record
  carrier evidence, not `.dem`, decoder integration, Axis-2, or a full analog
  hardware mechanism library. (a/c)
- Slice K adds a frontend-control oracle anti-toy gate:
  `test_axis1_ideal_control_lowering_matches_unitary_oracle_on_gpu` lowers every
  supported one-qubit frontend control plus every supported two-qubit frontend
  control, assembles the pure-control channel on CUDA through
  `assemble_substep_channel(...)`, and compares its action on every matrix dyad
  against the corresponding ideal unitary channel. One-qubit Clifford matrices
  are taken from Stim's tableau unitary API; `CZ/CX` keep explicit ordered
  matrices to avoid default evidence drift, while other supported two-qubit
  Clifford controls use a GPU principal-log Hamiltonian representative derived
  from the Stim tableau unitary. The tolerance
  `5e-8` is a numerical oracle tolerance for Stim's float table values and
  complex128 channel assembly, not a physics error budget. (a/c)
- Slice L preregisters a minimal noisy readout/reset instrument:
  `RD/RD_B` remain the readout-window dephasing primitives and are still lowered
  only through explicit positive-duration measurement substeps into
  `forward.joint_lindbladian.assemble_substep_channel(...)`. Classical readout
  assignment error is a separate reported-record instrument applied after ideal
  branch enumeration and before public detector/observable XOR projection.
  Reset infidelity is a preparation-channel instrument applied immediately after
  standalone reset substeps and after `MR/MRX/MRY/MRZ` ideal reset. Neither
  instrument is represented as Axis-2 source projection, and neither is claimed
  to be a GKSL joint generator. Literature boundary: Marton-Asboth 2303.04672
  uses phenomenological readout flips in 3D syndrome decoding; Heinsoo
  1801.07904 separates readout crosstalk into assignment correlations and
  measurement-induced dephasing; Xiong 2509.11822 updates modern protected
  readout-crosstalk magnitudes to cross-fidelity about `0.02%` (b), residual
  photon `nbar ~= 5e-4` (b), and also flags readout-induced leakage/MIST near
  `0.08%` per `100 ns` (b). Slice L adopts only the qubit assignment/reset
  instrument form now. It does not implement MIST/leakage, qutrit integration,
  DEM emission, decoder integration, or hardware-calibrated readout parameters.
  Any test probabilities such as `0.1`, `0.2`, or `0.25` are heuristic gates
  chosen to make exact record-distribution changes visible in tiny GPU fixtures,
  not hardware estimates. (a/b/c)
- Slice M preregisters participant-window coverage honesty:
  coverage must not count a positive-duration substep as fully covered merely
  because at least one selected local or union-support window exists. For one-qubit
  drive substeps, the minimal expected local-window footprint is every
  active-idle pair visible in the public schedule; for two-qubit gates it is the
  scheduled pair list; for explicit idle/readout substeps it is the declared
  consecutive disjoint pair partition. The existing selected-channel carrier can
  still run on supported windows, but the coverage ledger must expose selected,
  missing, and extra participants per positive-duration substep and set
  `full_positive_duration_coverage=false` when any expected participant window
  is missing. This is a claim-honesty correction, not a physics result. (a/c)
- Slice N preregisters one-qubit drive cluster lowering:
  when a one-qubit drive substep has one active qubit and multiple idle
  spectators, the correct Axis-1 carrier is one union-support joint generator
  over `(active, all visible idle spectators)`, not sequential pair channels
  sharing the active qubit. The ideal one-qubit control Hamiltonian is embedded
  on the active local factor; local `T1/T2` collapse operators are embedded on
  every local factor in the union support; then
  `forward.joint_lindbladian.assemble_substep_channel(...)` is called once for
  that support. This is exact GKSL algebra for the declared local Markovian
  context (a), while the rates remain heuristic gates (c). It deliberately does
  not add multi-qubit dissipative mechanisms, leakage/qutrits, Axis-2 source
  memory, or DEM/decoder integration. Anti-toy requirement: a 3-qubit
  `H(active)` fixture with two idle spectators must emit one dimension-8
  cluster row, full participant-window coverage, and record evidence that
  applies a single joint channel before measurement. The dense
  Choi-eigendecomposition carrier now keeps every positive Choi eigenvalue by
  default instead of pruning positive weights below `NUMERICAL_ZERO`. In the
  5-qubit CodeSpec cluster audit this removes dropped-mass warnings, improves
  the maximum trace-preservation residual to `8.216e-15`, and raises the maximum
  Kraus rank to `636`; the rank growth is a dense-carrier cost diagnostic, not
  a ledgered physical metric. (a/c)
- Slice O preregisters single-active static-ZZ cluster lowering:
  cached notes on ZZ/crosstalk anchor the form as a cross-Kerr/static-ZZ
  Hamiltonian term in the same circuit time window, not a Pauli/DEM edge and
  not an Axis-2 source process. Pettersson Fors et al. 2408.15402 define the
  effective two-level conditional-phase form `phi = integral zeta(t) dt`;
  Harper et al. 2605.29514 use coherent ZZ crosstalk during surface-code
  syndrome extraction and show the Pauli-twirl is not a sufficient statistic
  for sub-threshold coherent behavior; Sarovar et al. 1908.09855 give the
  locality/independence violation framing and the coherent `O(epsilon^2)`
  detectability caveat. For one active one-qubit drive with multiple visible
  idle spectators, at least one declared static-ZZ metadata pair inside the visible
  active+idle support, the frontend must emit one
  `one_qubit_drive_zz_cluster_joint_channel` over
  `(active, all visible idle spectators)` with explicit `coupling_edges`, then
  lower every listed static-ZZ edge in that support as an embedded Hamiltonian term in the same
  `forward.joint_lindbladian.assemble_substep_channel(...)` call as the ideal
  one-qubit control and local `T1/T2` context. This is exact GKSL algebra for
  the declared finite support and single substep (a); the default rates remain
  heuristic gates inherited from the G2 evidence carrier (c), and the hardware
  residual-ZZ magnitude brackets in the literature are not claimed by these
  tiny tests. Anti-toy requirement: a compiler-generated circuit that declares
  `(active,s1)` and `(active,s2)` static-ZZ pairs via public schedule metadata
  and later drives `active` with both spectators idle must produce one dimension-8
  cluster row, two lowered ZZ Hamiltonian records, full participant-window
  coverage, and state/record evidence with no same-substep overlapping pair
  failure. A sequential pair substitute is considered caught if it emits
  same-substep overlapping pair rows for the same finite-support mechanism
  component. (a/c)
- Slice P preregisters the selection-partition seam:
  channel/state/record evidence must all consume the same schedule-ordered
  `Axis1SelectionLayer` partition rather than separately implementing overlap
  checks. Each layer is one substep and must be either qubit-disjoint parallel
  windows or a single union-support window; overlapping selected supports fail
  closed before channel carrier evidence, state evolution, or record emission.
  Artifacts now include `selection_partition` with layer order, participants,
  row kinds, and a disjointness flag. This is a schedule/evidence invariant
  (a), not a ledgered physical metric; the row TP residual thresholds remain heuristic
  gates (c). Anti-toy requirements: true disjoint parallel windows report one
  layer with `window_count=2`; static-ZZ cluster channel/state/record artifacts
  expose the identical partition ledger; and a selector bug that emits two
  overlapping rows for one physical component is rejected before channel,
  state, or record evidence can treat it as same-substep sequential
  composition. (a/c)
- Slice Q preregisters multi-active one-qubit drive cluster lowering:
  when a one-qubit-gate substep has multiple active one-qubit frontend controls,
  visible idle spectators, and no declared static-ZZ edge inside the visible support, the
  selector emits one `multi_one_qubit_drive_cluster_joint_channel` over
  `(all active qubits, all visible idle spectators)`. The bridge lowers one
  exact `CTRL_*` Hamiltonian representative per active local factor and local
  `T1/T2` collapse operators on every local factor, then calls
  `forward.joint_lindbladian.assemble_substep_channel(...)` once for the union
  support. This
  is exact finite-support GKSL algebra for the declared local Markovian context
  (a), while the default rates remain heuristic gates (c). Anti-toy
  requirements: a compiler-generated 4-qubit `H(0,2)` fixture with spectators
  `1,3` and no static-ZZ pair must emit one dimension-16 multi-active row with
  two `CTRL_H` controls, active `T2/T1` records on both active local factors,
  spectator `T2_B/T1_B` records on both idle local factors, full
  participant-window coverage, and identical channel/state/record
  `selection_partition` ledgers. Static-ZZ edges inside the same support are
  handled by Slice R rather than by this no-static row. (a/c)
- Slice R preregisters full visible-support static-ZZ drive cluster lowering
  for one-qubit-gate substeps:
  for any supported one-qubit-gate substep, the selector now collects every
  declared static-ZZ metadata pair whose two endpoints lie inside the visible
  active+idle support. If at least one such edge exists and the support has
  more than two qubits, it emits one union-support static-ZZ cluster row:
  `one_qubit_drive_zz_cluster_joint_channel` for a single active control or
  `multi_one_qubit_drive_zz_cluster_joint_channel` for multiple active
  controls. The bridge lowers one exact `CTRL_*` Hamiltonian per active local
  factor, every declared static-ZZ edge in that support as an embedded `ZZ`
  Hamiltonian, and local `T1/T2` collapse operators on every local factor, then
  calls `forward.joint_lindbladian.assemble_substep_channel(...)` once. This
  covers active-idle, active-active, and idle-idle declared static-ZZ edges
  inside the substep support. This is exact finite-support GKSL algebra for the
  declared local Markovian/static-ZZ context (a); the rates and duration table
  remain heuristic gates (c). Anti-toy requirements:
  `declare_static_zz_couplings([(0,1),(1,2)]); CZ(0,1); CZ(1,2); H(0,2)`
  must produce one dimension-8
  `multi_one_qubit_drive_zz_cluster_joint_channel` with two `CTRL_H` controls,
  two `ZZ` Hamiltonian records, active `T2/T1` on both active local factors,
  and spectator `T2_B/T1_B`;
  `declare_static_zz_couplings([(1,2)]); CZ(1,2); H(0)` must include the
  idle-idle spectator `ZZ` edge in the single-active cluster rather than
  dropping it.
  Neither fixture may be represented as fake same-substep sequential pair
  channels. (a/c)
- Slice S preregisters active-only one-qubit substep lowering:
  a positive-duration one-qubit frontend substep no longer requires an idle
  spectator to enter Axis-1 evidence. A single active qubit with no idle
  spectator emits `one_qubit_drive_local_joint_channel` over that qubit; a
  multi-active no-idle layer emits
  `multi_one_qubit_drive_local_joint_channel` over the active support; and a
  multi-active layer with declared static-ZZ metadata edges inside the active support
  emits `multi_one_qubit_drive_zz_cluster_joint_channel`. These rows lower
  exact `CTRL_*` Hamiltonian representatives plus local `T1/T2` collapse
  operators, and any declared active-active `ZZ` Hamiltonian edges, into one
  `forward.joint_lindbladian.assemble_substep_channel(...)` call. The coverage
  ledger now distinguishes uncovered `unpaired_qubits` from
  `covered_unpaired_qubits`, so active-only positive-duration substeps can be
  marked fully covered without pretending they had active-idle participant
  pairs. This is exact finite-support GKSL algebra for the declared local
  context (a); rates and duration remain heuristic gates (c). Anti-toy
  requirements: `H(0)` on a one-qubit circuit must emit a dimension-2 local
  row and exact record evidence; `H(0,1)` must emit one dimension-4
  multi-control local row, not two sequential one-qubit rows; and
  `declare_static_zz_couplings([(0,1)]); CZ(0,1); H(0,1)` must emit one
  active-support static-ZZ cluster with two controls and one `ZZ` Hamiltonian
  record. (a/c)
- Slice T preregisters two-qubit frontend-control cluster lowering:
  a positive-duration supported two-qubit frontend-control substep with visible
  idle spectators, declared active-pair static-ZZ edges on non-CZ controls, or
  declared cross-window static-ZZ edges and local support size at most 5 qubits can emit one
  `two_qubit_control_cluster_joint_channel` or
  `two_qubit_control_zz_cluster_joint_channel` over the active+idle support.
  The ideal two-qubit control Hamiltonian is embedded into the union support,
  target-pair ordering is preserved, declared static-ZZ
  edges inside the support are lowered as `ZZ` Hamiltonian terms, and active
  plus spectator `T1/T2` collapse operators enter the same
  `forward.joint_lindbladian.assemble_substep_channel(...)` call. The dense
  Choi carrier now has a GPU-only SVD fallback when Hermitian `eigh` fails to
  converge on highly degenerate PSD Choi matrices; this is a numerical carrier
  guard (c), not a new physics claim. The support limit remains a heuristic
  dense-carrier gate (c), not a physics bound. This is exact finite-support
  GKSL algebra for the selected <=5q Markovian context (a); rates, duration,
  and support-size gate remain heuristic (c). Anti-toy requirements:
  `CZ(0,1)` on a 3-qubit circuit must include idle spectator 2 in a
  dimension-8 static-ZZ cluster; `CX(1,0)` must preserve ordered local support
  `[control,target]=[1,0]` inside the 3-qubit cluster; the 5-qubit CodeSpec
  `CX` spectator windows must emit true union-support cluster rows with full
  positive-duration coverage, not pair-only rows; and a same-substep non-CZ
  two-qubit layer (`SWAP` on disjoint target pairs) must appear as one parallel
  disjoint-window layer in channel/state/record evidence, not as a
  sequential-composition story. (a/c)
- Slice U preregisters explicit idle union-support cluster lowering:
  a positive-duration explicit `idle(...)` substep with visible support size at
  most 5 qubits can emit one `idle_cluster_joint_channel` over the idle
  support, instead of being forced into consecutive fake pair rows. If declared
  static-ZZ metadata edges lie inside that idle support, the selector emits
  `idle_zz_cluster_joint_channel`, records `coupling_edges`, lowers every
  declared static-ZZ edge as an embedded `ZZ` Hamiltonian, lowers local `T1/T2`
  collapse operators on every idle local factor, and calls
  `forward.joint_lindbladian.assemble_substep_channel(...)` once for the union
  support. The support limit remains a heuristic dense-carrier gate (c), not a
  physics bound. This is exact finite-support GKSL algebra for the selected
  <=5q explicit-idle Markovian/static-ZZ context (a); rates and duration remain
  heuristic gates (c). Anti-toy requirements: `idle(0,1,2, duration=75ns)`
  must emit one dimension-8 `idle_cluster_joint_channel` with full
  positive-duration coverage and exact record evidence;
  `declare_static_zz_couplings([(0,1)]); CZ(0,1); idle(0,1,2, duration=75ns)`
  must emit an `idle_zz_cluster_joint_channel` containing the declared `[0,1]`
  edge, not a sequential pair composition. In Slice U itself,
  readout odd-support handling remains pair-prefix plus leftover coverage-gap
  reporting; Slice V below adds <=5q readout union-support cluster lowering.
  (a/c)
- Slice V preregisters explicit Z-readout union-support cluster lowering:
  a positive-duration Z-basis measurement/readout substep with visible support
  size at most 5 qubits can emit one `readout_cluster_joint_channel` over the
  measured+idle support, except for the legacy two-measured-qubit/no-spectator
  case that remains a `readout_pair_joint_channel`. If declared static-ZZ metadata
  edges lie inside the measured+idle support, the selector emits
  `readout_zz_cluster_joint_channel`, records `coupling_edges`, lowers every
  declared static-ZZ edge as an embedded `ZZ` Hamiltonian, lowers `RD`
  collapse records only on measured qubits, lowers local `T1/T2` context on
  measured qubits and background `T1_B/T2_B` on idle spectators, and calls
  `forward.joint_lindbladian.assemble_substep_channel(...)` once before the
  ordinary projective measurement branch. This is readout-window joint-L
  evidence, not classical assignment noise, not reset infidelity, and not
  `.dem` output. The support limit remains a heuristic dense-carrier gate (c),
  not a physics bound. This is exact finite-support GKSL algebra for the
  selected <=5q readout-window Markovian/static-ZZ context (a); rates and
  duration remain heuristic gates (c). Anti-toy requirements:
  `measure(0,1,2, duration=250ns)` must emit one dimension-8
  `readout_cluster_joint_channel` with three `RD` records and exact record
  evidence;
  `declare_static_zz_couplings([(0,1)]); CZ(0,1); measure(0,1,2, duration=250ns)`
  must emit `readout_zz_cluster_joint_channel` containing the declared `[0,1]` edge;
  and a 7-qubit explicit readout must fail closed through selected disjoint
  pair-prefix rows plus a reported leftover coverage gap rather than claiming
  full dense readout support. (a/c)
- Slice W preregisters schedule-order coverage ledger normalization:
  `coverage.selected_substep_ids` must be emitted in compiler schedule order,
  not in selector-category construction order. This changes only evidence JSON
  ordering and artifact identity hashes for fixtures where a later substep is
  selected by an earlier selector category; it does not change selected rows,
  joint-generator assembly, channels, record probabilities, or physics claims.
  The ordering rule is exact schedule-metadata semantics (a); the hashes remain
  artifact identity checks, not physics conclusions (a/c).
- Slice X preregisters explicit static-ZZ metadata hardening:
  persistent static-ZZ couplings are public device/schedule metadata carried as
  `axis1_static_zz_couplings` on `CircuitIR` and normalized into
  `SubstepSchedule.static_zz_couplings`. Active `CZ` history is not promoted into
  static coupling truth. Unsupported over-cap windows with declared static-ZZ
  edges fail closed instead of falling back to pair rows that drop
  `coupling_edges`; top-level channel/state/record `passed` also requires
  `coverage.full_positive_duration_coverage=true`, not merely row-local numeric
  pass flags. Evidence writers reject forbidden or non-local filenames so
  `g2_jointL`, channel, state, and record evidence cannot masquerade as
  `.stim/.dem/.b8` or stale simulator artifacts. These are schedule/evidence
  contract guards (a/c), not new physical metrics.
- Slice Y preregisters CodeSpec static-ZZ metadata propagation:
  `Axis1StaticZZDeviceSpec(...).to_metadata()` and the equivalent
  `CodeSpec.metadata["axis1_static_zz_couplings"]` wire shape are now treated as
  public schedule/device metadata and promoted by `compile_code_spec(...)`
  through `CircuitBuilder.declare_static_zz_couplings(...)` into top-level
  `CircuitIR` metadata before `compile_code_spec_to_substep_schedule(...)`
  extracts the schedule. One shared normalizer validates endpoints and duplicate
  edges at the typed helper, builder, compiler, and schedule-extraction seams, so
  invalid CodeSpec static-ZZ declarations fail before lowering. Anti-toy
  requirement: a compiler-generated `CodeSpec` schedule with declared static-ZZ
  edge `(0,1)` must emit `source_kind="code_spec_compiler"`,
  `SubstepSchedule.static_zz_couplings=((0,1),)`, a schedule-derived
  static-ZZ cluster selection, and channel evidence assembled by one
  `single_joint_generator_expm` row rather than a hand-written fake schedule.
  This is public metadata plumbing (a/c), not evaluator mechanism truth, not
  Axis-2 source projection, and not hardware residual-ZZ calibration.
- Slice Z preregisters the anti-toy review hardening pass:
  same-substep active two-qubit layers with declared cross-window static-ZZ
  edges now lower as one `two_qubit_control_zz_cluster_joint_channel` instead of
  disjoint pair rows that would drop `coupling_edges`; if such a static cluster
  is above the dense local support cap, it fails closed through the coverage
  gate. The independent joint-L oracle test file now fails collection when CUDA
  or oracle dependencies are missing, rather than producing skip-green release
  evidence. G2 and CodeSpec evidence runners return a nonzero process status
  when their manifest `passed` flag is false. Evidence filename and dirty-dir
  guards are case-insensitive, channel freeze validation requires a local
  evidence filename, and raw public `CircuitIR.metadata["noise_projection"]`
  no longer authorizes source-embedded noise gates. State-evolution evidence now
  has a freeze/validate guard matching G2/channel/record artifact identity
  checks. The read-only Stim importer now accepts explicit public
  `static_zz_couplings` sidecar metadata, includes that sidecar in the schedule
  source hash, and still refuses to infer static-ZZ truth from `CZ` history.
  These are API/release-gate guards (a/c), not new physical metrics.
- Generated evidence path:
  `outputs/twin_validation/axis1_g2_frontend/g2_jointL.json`.
  Freeze path:
  `outputs/twin_validation/axis1_g2_frontend/g2_jointL.freeze.json`.
  Exact manifest content hash:
  `7aedf420770c4665829edfaa7a893d690cfd2441db68cf80585e7ea68298dc5f`.
  Exact file sha256:
  `f4139f614ffd817ee8a1f5b3322fd95e408bf2c86b87a0af6a835a418d54def9`.
  Exact freeze-file sha256:
  `714ff0639e1ffdc990f654112f2545a21c19b9df8157f91bc733603172f1439e`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated channel-evidence path:
  `outputs/twin_validation/axis1_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `e1c2c68f94d45a6e39b2d0f8f6985dd0eeea7559608bba66925d64b94d865cad`.
  Exact file sha256:
  `c43d0e496297beaa5dea8bf8c065e80709e8477449bdb92b78de892a23d7eaa7`.
  Exact freeze-file sha256:
  `2fe2d7a8f39e00452d7cc4b5cdf94aeecda6ff2f2e14f07308fc227144f9e902`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated selected-channel state-evidence path:
  `outputs/twin_validation/axis1_state_evidence/axis1_state_evolution.json`.
  Freeze path:
  `outputs/twin_validation/axis1_state_evidence/axis1_state_evolution.freeze.json`.
  Exact manifest content hash:
  `5da98f5fa87d8aa2001f9fe68dfebe17b367eddad6c82face5d43f1f629441b4`.
  Exact file sha256:
  `a41edb6d31db08f230850f7cee548758d2c25a933d8fa59abae9089bcdd53719`.
  Exact freeze-file sha256:
  `19115a79bde379d01811b6bf671385250b363f371b3923b930ba7a6a586f4bda`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated measurement-record evidence path:
  `outputs/twin_validation/axis1_record_evidence/axis1_measurement_records.json`.
  Exact manifest content hash:
  `218a90c8adfc316996f54837e64b7acc94b38302406995de5aeedc35aa9c87fe`.
  Exact file sha256:
  `ab78897f5849b95f3bd9e0d7d7867ee0408483422e0d5d1a812f97cfa80e368e`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated parallel-window anti-toy evidence path:
  `outputs/twin_validation/axis1_parallel_window_evidence/axis1_measurement_records.json`.
  Exact manifest content hash:
  `687cba0e45197715c7e53ae9aa3c553c1fa5a6378243c9238b4a62ecb06fdc3f`.
  Exact file sha256:
  `41978f62cf0e3f180c3b60f50e1d24d74707bef590261998ce19c3ea6672893d`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated active-only single-qubit channel-evidence path:
  `outputs/twin_validation/axis1_active_only_single_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_active_only_single_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `661b8f64da2169405b2b0cc08e6d0db983913f46643b3a46858873fd219a4fb8`.
  Exact file sha256:
  `434be3901cb2a252ba823c19f1a0386210dc2d060221e6230138b0714e28709f`.
  Exact freeze-file sha256:
  `bfb8a351f9b35049b0f83caa78a6cbf223979606e982925937d2e40023dd6e9c`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated active-only single-qubit record-evidence path:
  `outputs/twin_validation/axis1_active_only_single_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_active_only_single_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `2b2edff3dbe0ab89abcbe7e16b63eab61c2ee3dd7db4938a0b98a0ca50adad50`.
  Exact file sha256:
  `c9b58292110ebeac9e353b18419aee80272e9767a5a95d9a7f3e320c9a4cde87`.
  Exact freeze-file sha256:
  `3fa5822e1a4141a03276471d67bab4f4e02463df3d8631c45756582dcd1ac94f`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated active-only multi-qubit channel-evidence path:
  `outputs/twin_validation/axis1_active_only_multi_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_active_only_multi_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `e3621e1047a3d7203e257eb34a3cd544683fddba9e6ed6b98c3c9847215c03c5`.
  Exact file sha256:
  `4912c87af81a028203555987a9e2e1ecfd3a7f508652210d6147566e62a42eb5`.
  Exact freeze-file sha256:
  `8062a55d52dab7226cd0da0fee2bddca1d1f1a8383af117ddc9ab63ec45a1123`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated active-only multi-qubit record-evidence path:
  `outputs/twin_validation/axis1_active_only_multi_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_active_only_multi_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `1d28f460d715f859357d2c7b1b815475e6337fc96c713b31ecd7e4698d0e582d`.
  Exact file sha256:
  `a6859664ff8e3d506d8babd4d36515c56842975d8a8aae9324e05a7626ffa6ad`.
  Exact freeze-file sha256:
  `ee24deaafbf78da79a77d2fdd86b4252b4379b200af504121b0498c9e18a4244`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated active-only static-ZZ channel-evidence path:
  `outputs/twin_validation/axis1_active_only_static_zz_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_active_only_static_zz_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `e41430682d6a4dc7275ee6266e271c18a6dd67a87fa58a8dcb5f4636d18240cb`.
  Exact file sha256:
  `ed2a6a6e1195420cbffb6b69988e94ddad7001fa91fb30120b56afa1155fe1c1`.
  Exact freeze-file sha256:
  `cdcb7e5e247bb0451ad1df4dda0fb7b3181ebe9184682b8c3e9f268cdd497d09`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated active-only static-ZZ record-evidence path:
  `outputs/twin_validation/axis1_active_only_static_zz_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_active_only_static_zz_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `1d1b2a2bd41ae11238a04f3e9d4bbdaa7b8d9215855a61b8d43d4f6ec926ade1`.
  Exact file sha256:
  `68854eba618168fd76f5e068c14e945e085c087f8025332afdd061c1d9f1be3f`.
  Exact freeze-file sha256:
  `29a1eae15fb3f0f81113886a85890900ed40221ad07ca31fd7631b892b3748e6`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated multi-active drive-cluster channel-evidence path:
  `outputs/twin_validation/axis1_multi_active_drive_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_multi_active_drive_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `6b540419ac17af8dc29bd32288bc641d760daf2e9ada3bee4e1ee2ea0a3d7035`.
  Exact file sha256:
  `e1510ed81295910f4ab160256d11600239905c0f8d900e405cf29f71ee0ee912`.
  Exact freeze-file sha256:
  `f5333727266167a917198f5905875a073ddcb9448329c6e9e34a14518a5e72cf`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated multi-active drive-cluster record-evidence path:
  `outputs/twin_validation/axis1_multi_active_drive_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_multi_active_drive_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `bab137f1fe22564efcfccdfcbebe60247c40ebe14df4ae359f027170dc6402c2`.
  Exact file sha256:
  `d77b85b05a87cb9b48f73be5265a797a85d6a55637063b1130ddf2750ae4d7ac`.
  Exact freeze-file sha256:
  `42a13e5bde3e920736e11370fde15923e522a8534fc2c72219765817357c5716`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated multi-active static-ZZ cluster channel-evidence path:
  `outputs/twin_validation/axis1_multi_active_static_zz_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_multi_active_static_zz_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `41e1c8775e09f346469227b1adaac2f19ca1d35f8e993c2aaa968c119887dc11`.
  Exact file sha256:
  `580f94e7cd505622059371795e1e53793ed16aac9f1c1302b8586082678b5426`.
  Exact freeze-file sha256:
  `f70c7daa590f1337c1519d2896b27e6fd813c38877ab59e13b0330ada7e6ae00`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated multi-active static-ZZ cluster record-evidence path:
  `outputs/twin_validation/axis1_multi_active_static_zz_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_multi_active_static_zz_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `37dec53096e2e8dc6ab96ea35d792614a0a2d628f13c6e738ec195f19a9e581c`.
  Exact file sha256:
  `021c267b60d9fd19626c07b6012c9d75e1385f0a335d8a8632eaa716b764d6f2`.
  Exact freeze-file sha256:
  `1c86edafebf0af10e1627aff43d3669d180841ed768fe57033395b993bf9edbb`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated idle-idle static-ZZ cluster channel-evidence path:
  `outputs/twin_validation/axis1_idle_idle_static_zz_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_idle_idle_static_zz_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `96558cecdaa659b14c979e02c1a304ac49cded73d0570a502056eb99425a81a3`.
  Exact file sha256:
  `76850cc58b6286589b8ec05d708b0eed407788450fe28f0f06afa396e768424b`.
  Exact freeze-file sha256:
  `4f29fcd7fa4606a001ba30e7619ad08abcf38ca248e64283dc085ec0030cb41f`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated idle-idle static-ZZ cluster record-evidence path:
  `outputs/twin_validation/axis1_idle_idle_static_zz_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_idle_idle_static_zz_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `44816433de346a7576078734cb76a0469688f242c42ad7a970313617b7b37c2d`.
  Exact file sha256:
  `13fa5a710c8f0789c6825a9d8359fcd341e59ccb3657317ee625c8e233d861c3`.
  Exact freeze-file sha256:
  `e49206a7eeb7e44b00f3a84bc30b6e49a739c74345053b79bc394fa004798582`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated static-ZZ cluster anti-toy evidence path:
  `outputs/twin_validation/axis1_static_zz_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_static_zz_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `43a21de4b74acd339c2dca3580cd09580c85415ad7e1d840f218807ad3ad7618`.
  Exact file sha256:
  `672592a267ff4112b43731f6cc81351e30692b518b022d1d86446922b8448757`.
  Exact freeze-file sha256:
  `89e9c50278d55d8d8a4c00f1162ee792699e29c4f9e591901bee6c841c62808d`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated static-ZZ cluster channel-evidence path:
  `outputs/twin_validation/axis1_static_zz_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_static_zz_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `9dd427509a38cf4fdc57c01c922d1839f15e67d42ee19543322d7a6c9ce7c102`.
  Exact file sha256:
  `1a7788c60ef45bbc1107d8ec9fa59c2ac48b9c5b96757719c260f708ed17ede1`.
  Exact freeze-file sha256:
  `6c1beddbfcd6b0a20794b2a869f6196c168320da3e12a15bc510485822b11c66`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated two-qubit CZ spectator-cluster channel-evidence path:
  `outputs/twin_validation/axis1_two_qubit_cz_spectator_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_two_qubit_cz_spectator_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `6cdd357afab575966d3397211b581f02bb74a09c2a37d892ba6f34438f017882`.
  Exact file sha256:
  `39c5186499d8a9ce4ab10e4a35a7ae6890e24cabb8478293de6069a57d3a9b5b`.
  Exact freeze-file sha256:
  `fe5851dc730b5e1cda12717187752dbe9aeff3cf504959fec20f746dc3e18a58`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated two-qubit CZ spectator-cluster record-evidence path:
  `outputs/twin_validation/axis1_two_qubit_cz_spectator_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_two_qubit_cz_spectator_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `722da3adffa45ca3afccb887d9718323e805a1217aecea4fb68d82256056845b`.
  Exact file sha256:
  `aeedeef5e5f2fcbe301dc52b20f6d71f7a5d5ce9c4afd305270f2e538ce3b6d7`.
  Exact freeze-file sha256:
  `6f2c50d0c1dec6370370896226627a04229ce0632753535d1d9fafeb4f10a4e0`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated two-qubit CX spectator-cluster channel-evidence path:
  `outputs/twin_validation/axis1_two_qubit_cx_spectator_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_two_qubit_cx_spectator_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `c988781ec56d575edb31a7fd15231ebf6f2c84d5a772895f3a3302afb03d2b30`.
  Exact file sha256:
  `4207d2c8571d581bcb0cb76402d3474286da66c78e99cf36f769dfb65d4797e2`.
  Exact freeze-file sha256:
  `a56734033cba51d619e16cb659f761c1271980e68b29945a1ac8d5f15888ddfa`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated two-qubit CX spectator-cluster record-evidence path:
  `outputs/twin_validation/axis1_two_qubit_cx_spectator_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_two_qubit_cx_spectator_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `695841f47516ac85a13d2c622e4c82532569fca24c5111ecbe7f6e6e48560bee`.
  Exact file sha256:
  `bac389f1985079bed11cae08009bf3f6d4ca94b7e9866bb86b184ad2dc26995a`.
  Exact freeze-file sha256:
  `3407b1ccd80ed5d8353904cba0eaaa9384ec9d475aa2e4c5237585491f0aeed7`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-idle cluster channel-evidence path:
  `outputs/twin_validation/axis1_explicit_idle_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_idle_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `435ae4436759d17617dae9c371e7da67eab522454236a65089703b7266021b03`.
  Exact file sha256:
  `286edd399f7c7630c5c6fc2df584b92d4748ae0c5dbaeeca6184092b5bb0697d`.
  Exact freeze-file sha256:
  `2144d9ee60a0eb32ac4f4e230d64305755058f19f380d07c12c8e781c299e64d`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-idle cluster record-evidence path:
  `outputs/twin_validation/axis1_explicit_idle_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_idle_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `be83a0540e1179076d685e5ed7cab35a0f24b8e1950d4128696d95b8b3c257d4`.
  Exact file sha256:
  `6c63c1da6e06947e2db6adb46c09b48d83b76c07deba8c13ae89b9001c0da0a9`.
  Exact freeze-file sha256:
  `023cb2f9e2064aa3b48104162c9c4c19754d8ce92fc5faa2efe26c559a09e41e`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-idle static-ZZ cluster channel-evidence path:
  `outputs/twin_validation/axis1_explicit_idle_static_zz_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_idle_static_zz_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `ad6e617a78bf26f456305c78f40fd3a44e0cc44fa85d0abcc0dc7bf7295228db`.
  Exact file sha256:
  `1c149a3b54d7f3236ba564ff3819b84d2a0edef42904a3206f32c94d515a542d`.
  Exact freeze-file sha256:
  `19528a8e76d41b3af2bd0c5e1c91944791afe972d66e6222a2576735e6fab79c`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-idle static-ZZ cluster record-evidence path:
  `outputs/twin_validation/axis1_explicit_idle_static_zz_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_idle_static_zz_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `110a2bd2d0c29d10434a096888af96127d6655b2969a45e49016d3f43e0034f2`.
  Exact file sha256:
  `31967401134e7d9b0d25c16c5f1c02574a69ab96d1430435794c31ce339c0c80`.
  Exact freeze-file sha256:
  `0858ecfa3e51d5e94c25f799370804e4798fc387aeae386ab7ee1901fe1e8845`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-readout cluster channel-evidence path:
  `outputs/twin_validation/axis1_explicit_readout_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_readout_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `1f1f708c7df38800ba7e5c87c6b7425893dac94210fec44e72a14442465aa29b`.
  Exact file sha256:
  `1f06276319d8d3eebef18eda0a8e1bfbfe19ce737eae03ae33c27fabdcd11284`.
  Exact freeze-file sha256:
  `7d364b8db94f4b7b053c76b0dadb3c053125cf516bd5a206514046f4d2b92d8e`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-readout cluster record-evidence path:
  `outputs/twin_validation/axis1_explicit_readout_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_readout_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `34dd27779852e953dab8aa96ff8614fffa86db0689a68b04b1842a5d865beaad`.
  Exact file sha256:
  `d4c8b6ec4d880306f7119068c16106629a8178fc0885addd7fe635b1036741f7`.
  Exact freeze-file sha256:
  `60b0094346821b3a3f8c4b09c9b8a98aae318174458928b8137e156a5fc57422`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-readout static-ZZ cluster channel-evidence path:
  `outputs/twin_validation/axis1_explicit_readout_static_zz_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_readout_static_zz_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `5370f7598d74ac54451569d043825c4d95003b5678248876141ada01f20085d1`.
  Exact file sha256:
  `726bf922f2cc2d2ab6e7dcf09ece9119b9e1c45abc8143883701b6de508edd3a`.
  Exact freeze-file sha256:
  `3a425fbc6f41193f0a4f2543fcc1b9d226d633d702c44d2b8ecf275ff0c3e112`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-readout static-ZZ cluster record-evidence path:
  `outputs/twin_validation/axis1_explicit_readout_static_zz_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_explicit_readout_static_zz_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `ec34d52303604de4de2f6f4a2194543dbd781a927707a40bbed7cf7246079c38`.
  Exact file sha256:
  `98b6853960f79ac34a6bbd54498ccd8ef13b04c51012e1e925e1722629e649d9`.
  Exact freeze-file sha256:
  `5f78f5f26d1bf1a24e6788924953195db91db3e712645e293e9fae1b67afcd47`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-idle anti-toy evidence path:
  `outputs/twin_validation/axis1_explicit_idle_evidence/axis1_measurement_records.json`.
  Exact manifest content hash:
  `8f8eda06c4c904750723aaacccd12b810c04b905abbacafa3becac86de688b47`.
  Exact file sha256:
  `8755cacaeca412ff1794aeb27ba7458805f5de1cf24f76a8ff15ac051898da39`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated explicit-readout anti-toy evidence path:
  `outputs/twin_validation/axis1_explicit_readout_evidence/axis1_measurement_records.json`.
  Exact manifest content hash:
  `ad0407a49e1c51dbf54a34d77d4d150ec69b457effae62508d30d426ae18a073`.
  Exact file sha256:
  `8489941c6fbb6f12590e3afbf09daa76df5c3f79b5fe47ffb7fd7c6df715a337`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated reset-boundary anti-toy evidence path:
  `outputs/twin_validation/axis1_reset_boundary_evidence/axis1_measurement_records.json`.
  Exact manifest content hash:
  `a7d825a4dbcecbe8437be8b87a2c7015b3de9900feea16642cff34ff5de9497a`.
  Exact file sha256:
  `f297259a8586207f64e5b268eec0c0d4465c7d008ae055cc5f9c0cce8b20a996`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated CodeSpec compiler anti-toy evidence path:
  `outputs/twin_validation/axis1_codespec_record_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_codespec_record_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `f43318e8da306dc83f67b972cd618e5e4418cad872a116786e8f4a943274af36`.
  Exact file sha256:
  `f5b1b635cda1e862ecdbdb5aea89683e818a12e329b96162d650e432af6b9ffc`.
  Exact freeze-file sha256:
  `b5c4cd8d384b5094b15ca57575d3b8f85ef02b16f393883226f1e4e55f4a31e7`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated noisy readout/reset instrument evidence path:
  `outputs/twin_validation/axis1_readout_reset_instrument_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_readout_reset_instrument_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `7ddfc477606ce23e417e74a49de04941ef605fcef76bcef986423a15135e18b8`.
  Exact file sha256:
  `e87938adb839888b9461e50a76c3e0be7bf8f5c658fce473c52c350bfcc6b0ba`.
  Exact freeze-file sha256:
  `69626a7064e7464583be623caf724ef8aaece9edc4aecef75b26616960ab93bf`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Generated sampled `.b8` record-carrier path:
  `outputs/twin_validation/axis1_b8_record_samples/`.
  Exact sample-summary content hash:
  `9639c6f19d43c5bf4040f37fe397152d511863c943be57b6bb67d4f17092c74a`.
  Exact sample-summary file sha256:
  `4ede9d3098a4a44f4d7d9c59c612ea11c836349731d01373c99a7d5fd74e65c1`.
  Exact `detection_events.b8` sha256:
  `d0d8585e34d53000f3a5727ff5e8a2dc73f4a2b3affd536dcffa64f87eaf7275`.
  Exact `obs_flips_actual.b8` sha256:
  `5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)

Interpretation:

- The G2 bridge implementation still gates the build-contract contextual
  `DR x ZZ` row instead of silently reducing the row to an H-only diagnostic.
- Generic schedule evidence now uses exact frontend `CTRL_*` control terms plus
  selected local primitives in one joint generator; `DR` is no longer used as a
  generic stand-in for an ideal frontend gate.

Commands verified on the GPU lane:

```bash
python -m py_compile \
  src/qec_twin/simulator/circuit_ir.py \
  src/qec_twin/simulator/axis1_selection.py \
  src/qec_twin/simulator/axis1_channel_evidence.py \
  src/qec_twin/simulator/axis1_record_evidence.py \
  src/qec_twin/simulator/axis1_state_evidence.py \
  src/qec_twin/simulator/axis1_ideal_controls.py \
  src/qec_twin/simulator/axis1_bridge.py \
  src/qec_twin/simulator/axis1_g2_runner.py \
  src/qec_twin/simulator/analog_schedule.py \
  src/qec_twin/mechanisms/axis1_primitives.py \
  src/qec_twin/simulator/__init__.py \
  tests/test_simulator_axis1_schedule.py

conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py tests/test_joint_lindbladian.py

conda run -n aiqec python -m qec_twin.simulator.axis1_g2_runner \
  --out-dir outputs/twin_validation/axis1_g2_frontend --refresh-freeze

conda run -n aiqec python -m qec_twin.simulator.axis1_g2_runner \
  --validate-freeze outputs/twin_validation/axis1_g2_frontend/g2_jointL.freeze.json

conda run -n aiqec python -c "from qec_twin.simulator.axis1_g2_runner import build_axis1_g2_frontend_schedule; from qec_twin.simulator import write_axis1_substep_channel_evidence; r=write_axis1_substep_channel_evidence(build_axis1_g2_frontend_schedule(), 'outputs/twin_validation/axis1_channel_evidence'); print(r.content_hash)"

conda run -n aiqec python -c "from qec_twin.simulator import freeze_axis1_substep_channel_evidence, validate_axis1_substep_channel_freeze; f=freeze_axis1_substep_channel_evidence('outputs/twin_validation/axis1_channel_evidence/axis1_substep_channels.json', overwrite=True); print(validate_axis1_substep_channel_freeze(f.freeze_path)['evidence_sha256'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator.axis1_g2_runner import build_axis1_g2_frontend_schedule; from qec_twin.simulator import freeze_axis1_state_evolution_evidence, validate_axis1_state_evolution_freeze, write_axis1_state_evolution_evidence; from qec_twin.simulator.artifacts import file_sha256; r=write_axis1_state_evolution_evidence(build_axis1_g2_frontend_schedule(), Path('outputs/twin_validation/axis1_state_evidence')); f=freeze_axis1_state_evolution_evidence(r.state_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.state_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_state_evolution_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=2); b.h(0); b.tick(); b.cz((0,1)); b.tick(); b.measure((0,1), key=('m0','m1')); b.detector('d0', xor=('m0','m1')); b.observable('logical0', xor=('m1',), index=0); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_record_evidence')); print(r.content_hash); print(file_sha256(r.record_evidence))"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=4); b.cz((0,1,2,3)); b.tick(); b.measure((0,1,2,3), key=('m0','m1','m2','m3')); b.detector('d01', xor=('m0','m1')); b.detector('d23', xor=('m2','m3')); b.observable('logical3', xor=('m3',), index=0); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_parallel_window_evidence')); print(r.content_hash); print(file_sha256(r.record_evidence))"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_substep_channel_evidence, validate_axis1_substep_channel_freeze, write_axis1_substep_channel_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=4); b.h((0,2)); b.measure((0,1,2,3), key=('m0','m1','m2','m3')); r=write_axis1_substep_channel_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_multi_active_drive_cluster_channel_evidence')); f=freeze_axis1_substep_channel_evidence(r.channel_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.channel_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_substep_channel_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_measurement_record_evidence, validate_axis1_measurement_record_freeze, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=4); b.h((0,2)); b.measure((0,1,2,3), key=('m0','m1','m2','m3')); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_multi_active_drive_cluster_evidence')); f=freeze_axis1_measurement_record_evidence(r.record_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.record_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_measurement_record_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_substep_channel_evidence, validate_axis1_substep_channel_freeze, write_axis1_substep_channel_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=3); b.declare_static_zz_couplings(((0,1),(1,2))); b.cz((0,1)); b.tick(); b.cz((1,2)); b.tick(); b.h((0,2)); b.measure((0,1,2), key=('m0','m1','m2')); r=write_axis1_substep_channel_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_multi_active_static_zz_cluster_channel_evidence')); f=freeze_axis1_substep_channel_evidence(r.channel_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.channel_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_substep_channel_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_measurement_record_evidence, validate_axis1_measurement_record_freeze, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=3); b.declare_static_zz_couplings(((0,1),(1,2))); b.cz((0,1)); b.tick(); b.cz((1,2)); b.tick(); b.h((0,2)); b.measure((0,1,2), key=('m0','m1','m2')); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_multi_active_static_zz_cluster_evidence')); f=freeze_axis1_measurement_record_evidence(r.record_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.record_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_measurement_record_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_substep_channel_evidence, validate_axis1_substep_channel_freeze, write_axis1_substep_channel_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=3); b.declare_static_zz_couplings(((1,2),)); b.cz((1,2)); b.tick(); b.h(0); b.measure((0,1,2), key=('m0','m1','m2')); r=write_axis1_substep_channel_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_idle_idle_static_zz_cluster_channel_evidence')); f=freeze_axis1_substep_channel_evidence(r.channel_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.channel_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_substep_channel_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_measurement_record_evidence, validate_axis1_measurement_record_freeze, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=3); b.declare_static_zz_couplings(((1,2),)); b.cz((1,2)); b.tick(); b.h(0); b.measure((0,1,2), key=('m0','m1','m2')); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_idle_idle_static_zz_cluster_evidence')); f=freeze_axis1_measurement_record_evidence(r.record_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.record_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_measurement_record_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_measurement_record_evidence, validate_axis1_measurement_record_freeze, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=3); b.declare_static_zz_couplings(((0,1),(0,2))); b.cz((0,1)); b.tick(); b.cz((0,2)); b.tick(); b.h(0); b.measure((0,1,2), key=('m0','m1','m2')); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_static_zz_cluster_evidence')); f=freeze_axis1_measurement_record_evidence(r.record_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.record_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_measurement_record_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_substep_channel_evidence, validate_axis1_substep_channel_freeze, write_axis1_substep_channel_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=3); b.declare_static_zz_couplings(((0,1),(0,2))); b.cz((0,1)); b.tick(); b.cz((0,2)); b.tick(); b.h(0); b.measure((0,1,2), key=('m0','m1','m2')); r=write_axis1_substep_channel_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_static_zz_cluster_channel_evidence')); f=freeze_axis1_substep_channel_evidence(r.channel_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.channel_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_substep_channel_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, write_axis1_measurement_record_samples; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=2); b.h(0); b.tick(); b.cz((0,1)); b.tick(); b.measure((0,1), key=('m0','m1')); b.detector('d0', xor=('m0','m1')); b.observable('logical0', xor=('m1',), index=0); r=write_axis1_measurement_record_samples(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_b8_record_samples'), shots=256, seed=20260628); print(r.sample_manifest['content_hash']); print(file_sha256(r.sample_summary)); print(file_sha256(r.detection_events)); print(file_sha256(r.obs_flips_actual))"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=2); b.idle((0,1), duration_ns=75.0); b.measure((0,1), key=('m0','m1')); b.detector('d0', xor=('m0','m1')); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_explicit_idle_evidence')); print(r.content_hash); print(file_sha256(r.record_evidence))"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=2); b.measure((0,1), key=('m0','m1'), duration_ns=250.0); b.detector('d0', xor=('m0','m1')); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_explicit_readout_evidence')); print(r.content_hash); print(file_sha256(r.record_evidence))"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import CircuitBuilder, circuit_ir_to_substep_schedule, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=2); b.reset(0); b.measure((0,1), key=('m0','m1'), duration_ns=250.0); b.detector('d0', xor=('m0','m1')); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_reset_boundary_evidence')); print(r.content_hash); print(file_sha256(r.record_evidence))"

conda run -n aiqec python -c "from pathlib import Path; from qec_twin.simulator import Axis1ReadoutResetInstrumentSpec, CircuitBuilder, circuit_ir_to_substep_schedule, freeze_axis1_measurement_record_evidence, validate_axis1_measurement_record_freeze, write_axis1_measurement_record_evidence; from qec_twin.simulator.artifacts import file_sha256; b=CircuitBuilder(num_qubits=2); b.reset(0); b.h(0); b.measure((0,1), key=('m0','m1'), duration_ns=250.0); b.detector('d0', xor=('m0','m1')); spec=Axis1ReadoutResetInstrumentSpec(readout_p0_to_1=0.1, readout_p1_to_0=0.2, readout_pair_flip_probability=0.25, reset_flip_probability=0.1); r=write_axis1_measurement_record_evidence(circuit_ir_to_substep_schedule(b.build()), Path('outputs/twin_validation/axis1_readout_reset_instrument_evidence'), instrument_spec=spec); f=freeze_axis1_measurement_record_evidence(r.record_evidence, overwrite=True); print(r.content_hash); print(file_sha256(r.record_evidence)); print(file_sha256(f.freeze_path)); print(validate_axis1_measurement_record_freeze(f.freeze_path)['pass'])"

conda run -n aiqec python -m qec_twin.simulator.axis1_codespec_runner \
  --out-dir outputs/twin_validation/axis1_codespec_record_evidence --refresh-freeze

conda run -n aiqec python -m qec_twin.simulator.axis1_codespec_runner \
  --validate-freeze outputs/twin_validation/axis1_codespec_record_evidence/axis1_measurement_records.freeze.json

conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py tests/test_joint_lindbladian.py
# latest targeted result: 101 passed in 48.20s, no numerical Choi truncation warnings (a/c)
```

Remaining blockers before calling Axis-1 "complete":

- A complete hardware mechanism registry/lowering library is still not
  implemented. The bridge now has a registry contract for the current local
  two-qubit `DR/ZZ/T2/T1/T1_UP/T2_B/T1_B/T1_UP_B/RD/RD_B/FSIM_SWAP/FSIM_PHASE`
  primitives plus exact frontend
  `CTRL_*` controls for
  `C_XYZ/C_ZYX/H/H_XY/H_XZ/S/S_DAG/SQRT_X/SQRT_X_DAG/SQRT_Y/SQRT_Y_DAG/SQRT_Z/SQRT_Z_DAG/X/Y/Z`
  and `CX/CY/CZ/ISWAP/ISWAP_DAG/SQRT_XX/SQRT_XX_DAG/SQRT_YY/SQRT_YY_DAG/SQRT_ZZ/SQRT_ZZ_DAG/SWAP/XCX/XCY/XCZ/YCX/YCY/YCZ`,
  plus public `Axis1LocalLindbladContextSpec` rate overrides, optional
  computational-subspace `T1_UP/T1_UP_B` selection, and optional active-pair
  computational-subspace fSim residual selection. It is still not a complete
  hardware mechanism library and supports only the currently selected
  active-only one-qubit drive rows, one-qubit drive clusters, multi-active
  one-qubit drive clusters without declared static-ZZ edges, one-qubit drive
  static-ZZ clusters over declared edges inside the visible support, two-qubit
  control spectator clusters up to 5 local qubits, explicit-duration idle
  pair/cluster rows up to 5 local qubits, explicit-duration readout
  pair/cluster rows up to 5 local qubits, active CZ, declared static-ZZ, and
  supported two-qubit frontend-control windows.
- Compiler provenance now has a builder-owned in-process seal, but it is not a
  cryptographic cross-process or hostile-interpreter attestation scheme.
- Active `CZ` generic rows already carry a same-substep local `ZZ` primitive.
  When public static-ZZ metadata also declares that same active pair, the row now
  records that edge in `coupling_edges` as provenance for the same local carrier
  and deliberately does not lower a second `ZZ` Hamiltonian term. This resolves
  the provenance ambiguity without changing the joint-L physics object. (a/c)
- Full substep channel evidence for arbitrary scheduled operations is not
  emitted. Current channel evidence is schedule-derived and no longer G2-only,
  but is still limited to supported active-only one-qubit drive rows,
  one-qubit drive clusters, visible-support static-ZZ drive clusters,
  multi-active no-static one-qubit drive clusters, two-qubit control spectator
  clusters up to 5 local qubits, explicit-duration idle pair/cluster rows up
  to 5 local qubits, explicit-duration readout pair/cluster rows up to 5 local
  qubits, active CZ, declared static-ZZ, and supported two-qubit frontend-control
  substeps.
- Record generation exists only for the current exact small-N selected-channel
  / Pauli-basis measurement slice with disjoint parallel windows,
  active-only local one-qubit rows, one-qubit drive union-support clusters,
  multi-active no-static clusters, visible-support static-ZZ drive clusters,
  two-qubit control spectator clusters up to 5 local qubits, and
  explicit-duration idle/readout pair/cluster rows up to 5 local qubits. It writes JSON measurement,
  detector, logical-observable evidence and sampled `.b8` detector/logical
  carriers only; it is not `.dem` output or decoder integration.
- Selected union-support rows are still dense local carriers capped at 5 local
  qubits in this slice. Supports above the dense gate must fail closed through
  supported disjoint local windows plus explicit coverage gaps, or wait for the
  future scalable backend.
- A mature external importer beyond in-repo `CircuitIR`/`CodeSpec` and the
  current supported Stim subset is still pending.

# Axis-1 Scalable Carrier Prereg

Date: 2026-06-28

Status: theory-first preregistration for the next Axis-1 implementation slice.
This document does not claim that the full coupled QEC teacher is complete.

Epistemic convention: quantitative statements below are tagged as `(a) exact`,
`(b) prediction band`, or `(c) heuristic gate / decision rule`. Artifact hashes,
file identity, test outcomes, and backend smoke results are not metrics. Any scored
quantity must first go through `docs/METRICS.md`.

## Current Repo State

- Dense Axis-1 channel evidence exists in
  `src/qec_twin/forward/joint_lindbladian.py`: one same-substep joint generator,
  one `expm(L_substep * dt)`, dense Choi/Kraus evidence, and G2 composed-vs-joint
  channel rows. This remains the canonical small-window G2 backend. (a)
- The compiler/schedule seam exists:
  `CircuitIR` / `CodeSpec` -> `SubstepSchedule` / `AnalogSubstepIR` ->
  mechanism selection -> `H_list,c_list` -> `joint_lindbladian`. (a)
- Axis-1 mechanism support now includes local `T1/T2`, thermal-up variants,
  `DR/RD`, static `ZZ`, computational-subspace fSim residual primitives, ideal
  frontend controls, public context rate overrides, and public per-edge
  static-ZZ calibration sidecars. This is still not a complete hardware
  mechanism library. (a/c)
- The present dense selection path intentionally caps local union-support rows at
  `5` qubits. Rows above that cap fail closed; they are not silently converted
  into Pauli/GF(2) or sequential-composition approximations. (a/c)
- Existing `forward/scalable` contains a composed-carrier arm and a qutrit
  MCWF-on-MPS leakage carrier. It does not yet contain an Axis-1
  computational-subspace GKSL state/record carrier for over-cap substeps. (a)

## Why This Slice Comes Next

The dense joint-L path is the right object for G2 because G2 asks for channel
evidence: superoperators, Choi states, Kraus stacks, and process-fidelity rows
under the existing metric ledger. A scalable carrier has a different shape. It
can evolve states or sample records for larger schedules, but it should not be
presented as a dense channel/Choi replacement. (a)

Therefore the next implementation slice should add a carrier seam before any
large-code claim:

```text
SubstepSchedule
  + Axis1MechanismSelection rows
  + public context/calibration metadata
  -> Axis1CarrierProgram
  -> GPU state/record carrier
  -> evidence rows cross-checked against dense joint-L on tiny schedules
```

This prevents two failure modes: silently dropping over-cap coupling edges, and
pretending that a Pauli/DEM schedule is an analog joint-L simulator. (a/c)

## Grounding Ledger

| sub-axis | source | reading note / link | use here | class |
|---|---|---|---|---|
| Dense small-window joint-L | `src/qec_twin/forward/joint_lindbladian.py`, `tests/test_joint_lindbladian.py` | in-repo implementation and QuTiP/scipy oracle tests | canonical G2/channel backend | (a) |
| Axis-1 compiler seam | `docs/twin_validation/axis1_compiler_bridge_prereg.md` | in-repo prereg/evidence | schedule and mechanism-lowering contract | (a/c) |
| Open-system TN taxonomy | Jaschke, Montangero & Carr, arXiv:1804.09796 | `docs/papers/reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | QT/MPS vs MPDO vs LPTN decision | (a/c) |
| Positivity-preserving density TN | Werner et al., arXiv:1412.5746 | `docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md` | later LPTN density carrier and bounded-simplification language | (a/c) |
| QEC leakage MPS trajectory carrier | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md` | QEC record-producing MPS trajectory precedent | (a/c) |
| QEC master-equation simulator prior art | Shen et al., QMCtwin arXiv:2606.19848 | `docs/papers/reading_notes/qmctwin_master_equation_digital_twin_2606.19848.md` | scale/prior-art boundary for two-level ME simulators | (a/c) |
| QuTiP master-equation semantics | QuTiP 5.3 docs | https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html | `H + c_ops` reference/oracle language | (a/c) |
| QuTiP Monte Carlo semantics | QuTiP 5.3 docs | https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-monte.html | trajectory semantics reference | (a/c) |
| qutip-cuquantum backend shape | qutip-cuquantum docs | https://qutip-cuquantum.readthedocs.io/en/latest/solver.html and `/data.html` | optional GPU probe, not G2 replacement | (a/c) |

## Adopt / Do Not Adopt

Adopt now:

- Add a **carrier interface** that consumes schedule-derived Axis-1 mechanism
  selections and emits state/record evidence. It must preserve the rule that all
  simultaneous Hamiltonian and collapse terms in a substep are assembled as one
  joint generator or one faithful stochastic unraveling of that generator. (a)
- Use a **GPU quantum-trajectory/MPS path** as the first scalable candidate. QEC
  record emission is naturally per-shot/per-trajectory, and the repo already has
  GPU MPS trajectory infrastructure for leakage. This first carrier is for
  state/record evidence, not G2 dense channel evidence. (c)
- Keep `forward.joint_lindbladian` as the small-window oracle for exact final
  density matrices and G2 rows. Tiny schedules must compare the scalable carrier
  against this dense backend before over-cap evidence is accepted. (a/c)
- Keep qutip-cuquantum as an optional GPU **probe/oracle adapter** for
  tensor-structured `H + c_ops` state evolution. Its own docs emphasize preserving
  tensor structure and warn that dense conversion destroys that structure. (a/c)

Do not adopt now:

- Do not replace G2 with qutip-cuquantum. G2 is a dense channel-evidence gate;
  qutip-cuquantum is useful when the state/operator object remains tensor
  structured. (a/c)
- Do not add a Pauli/GF(2) approximation for over-cap Axis-1 analog coupling
  rows. DEM/Stim artifacts can remain schedule/record carriers only. (a)
- Do not add Axis-2 source timelines in this slice. Source fan-out may later
  parameterize Axis-1 terms, but that is not the same as an Axis-1 carrier. (a)
- Do not integrate qutrit/leakage into the computational-subspace Axis-1 carrier
  here. Leakage has its own existing MPS path and needs a separate prereg if it is
  merged with this Axis-1 bridge. (a/c)
- Do not claim large-code coupled simulation from a tiny carrier adapter. The
  first slice only earns an over-cap route plus dense-oracle agreement where the
  dense oracle is feasible. (c)

## Minimal New Data Structures

These are proposed interfaces, not implemented code in this prereg.

`Axis1CarrierTerm`:

- `kind`: `hamiltonian`, `collapse`, `instrument`, or `measurement_boundary`.
  (a/c)
- `support`: schedule qubit ids, with a local carrier ordering. (a)
- `operator_family`: existing primitive/control id, not a serialized dense truth
  payload. (a)
- `coefficient`: scalar coefficient after applying public context/calibration
  metadata and `dt`. (a/c)
- `provenance`: schedule row id, operation id, primitive id, coupling edge if
  applicable, and public metadata source. (a/c)

`Axis1CarrierProgram`:

- `num_qubits`, `site_order`, `initial_state_spec`. (a/c)
- Ordered substep programs with `dt_ns`, `dt_source`, `dt_bracket_ns`,
  `active_qubits`, `idle_qubits`, `measurement_keys`, and carrier terms. (a)
- `record_map`: measurement key -> detector/observable carriers from the
  existing schedule; no `.dem` claim. (a)
- `backend_contract`: `dense_oracle`, `qt_mps_state_record`, or
  `qutip_cuquantum_probe`, with `gpu_required=true` for circuit/carrier runs.
  (a/c)
- `approximation_book`: Trotter split, trajectory sampling, MPS truncation, and
  ordering notes. These are verification gates/risks, not metrics. (c)

## dt and Bracket Policy

- `dt_ns` is inherited from `AnalogSubstepIR`: explicit operation duration if
  present, otherwise the registered frontend/default duration source. (a)
- Hamiltonian residual angles remain area-preserving: coefficient equals angle
  divided by `dt_ns`. (a)
- Collapse rates are lowered through the same public context/rate fields already
  used by dense Axis-1 evidence. (a/c)
- `dt_bracket_ns` travels with the carrier program so later sweeps can reuse the
  existing G2 bracket discipline. Any new scored quantity from a sweep must first
  be added through `docs/METRICS.md`; until then the sweep is only a verification
  gate. (a/c)
- A scalable carrier may use internal micro-steps or local Trotter layers only if
  the approximation is declared in `approximation_book`. It may not silently
  replace the substep joint generator by sequential `E1 o E2` semantics. (a/c)

## Initial Handling By Operation Type

- One-qubit and two-qubit gates: lower ideal controls plus selected Axis-1 error
  primitives into the same substep program. Active-pair static-ZZ provenance must
  not create a duplicate ZZ term. (a)
- Idle: include explicit idle rows and selected static-ZZ spectator clusters.
  Bracket-only idles do not become hidden analog evolution unless schedule
  metadata declares them as selected substeps. (a/c)
- Measurement: emit record-boundary operations and supported readout dephasing /
  readout-instrument terms. Record evidence is not a `.dem`. (a)
- Reset: remain a boundary/instrument operation in this slice. Do not model reset
  as an unregistered GKSL lowering. (a/c)
- Multi-qubit gates above the dense cap: fail closed until the carrier program can
  represent all support and all selected coupling edges. Over-cap rows must not be
  reduced to a hand-written fake schedule. (a/c)

## Axis-1 Bridge Semantics

For dense support, the bridge still calls:

```python
assemble_substep_channel(H_list, c_list, dt_ns, device="cuda")
```

For scalable support, the bridge should build an `Axis1CarrierProgram` from the
same selected terms. The first production candidate should implement a
quantum-trajectory/MPS unraveling of the same `H,c_ops` object, on GPU, and emit
state/record evidence with explicit approximation accounting. (a/c)

The bridge must preserve same-substep joint semantics. A test that compares
joint-L against a deliberately sequential composition remains a negative control;
the sequential path is never the implementation reference. (a)

## G2 Reuse

G2 remains exactly the existing composed-vs-joint channel gate from
`docs/twin_validation/h3_h5_dt_g2band_prereg.md` and
`forward.joint_lindbladian`. The scalable carrier may reuse G2 only as a
small-window oracle comparison:

- Build a compiler-generated schedule whose selected support is within the dense
  limit. (a)
- Lower the same schedule to dense channel evidence and to the carrier program.
  (a)
- Compare the carrier's final state/record distribution to dense joint-L output
  under predeclared verification gates. These gates are not new metrics. (c)
- For over-cap schedules, the carrier emits state/record evidence only; it does
  not emit dense G2 channel rows. (a/c)

## Verification Gates

All circuit/carrier execution in this slice is GPU-only. If CUDA is unavailable,
the carrier tests fail closed or are not accepted as release evidence; they do
not fall back to CPU circuit simulation. Documentation lint and source scans may
run without GPU because they do not execute circuit/carrier physics. (a/c)

Anti-toy gates for the implementation slice:

- **Compiler-generated over-cap row:** construct a real `CircuitIR`/`CodeSpec`
  schedule whose selected Axis-1 visible support exceeds the dense cap and whose
  public static-ZZ edges are all accounted for in the carrier program. No
  hand-written fake substep is accepted. (a/c)
- **Tiny dense oracle:** for a schedule within dense support, compare final state
  and record probabilities against `joint_lindbladian` output from the same
  selected terms. The tolerance is a verification gate, not a metric. (c)
- **Bad sequential composition caught:** keep a positive case where
  `exp((L_a + L_b) dt)` and `exp(L_b dt) exp(L_a dt)` disagree, and require the
  carrier path to follow the joint generator/unraveling. (a/b)
- **dt sweep:** reuse the existing G2 bracket logic on dense windows to check
  expected power-law/zero cases, without adding a new metric. (a/b/c)
- **ZZ x T2 exact-zero and DR x ZZ nonzero:** retain the existing G2 anti-toy
  pairings as dense oracle checks for the carrier seam. (a/b)
- **No edge drop:** every declared coupling edge selected into a row must appear
  in carrier provenance or the build fails. (a)
- **No `.dem` overclaim:** sampled records may be packed for downstream
  experiments, but no Stim-Pauli DEM/decoder claim is made from analog joint-L
  records. (a)

## Open Risks / Blockers

- QT/MPS adds trajectory sampling and MPS truncation risks. These are acceptable
  only as declared approximation books and dense-oracle agreement gates, not as a
  replacement for exact channel evidence. (c)
- A 2D surface-code snake ordering can turn local spatial couplings into longer
  MPS-range operations and grow bond dimension. The first implementation should
  demonstrate an over-cap schedule but not claim full `d=5` or `d=7` production
  readiness. (c)
- LPTN is theoretically cleaner for positivity-preserving density evolution but
  requires new infrastructure. It should be a later backend unless QT/MPS
  trajectory evidence is insufficient. (c)
- qutip-cuquantum can preserve tensor structure through `CuOperator`/`CuState`,
  but dense conversion materializes the full matrix and destroys the advantage.
  Use it as a probe, not as a channel-evidence backend. (a/c)
- The exact interface between `Axis1CarrierProgram` and existing leakage
  `mps_forward.py` needs design review. Reusing infrastructure is good; mixing
  leakage/qutrit semantics into this computational-subspace slice is not. (c)
- Any future accuracy, performance, or decoder-impact number must be registered
  through `docs/METRICS.md` before being treated as a scored result. (a)

## Recommended Implementation Slice

1. Add `Axis1CarrierProgram` construction from existing compiler-generated
   `SubstepSchedule` and `Axis1MechanismSelection` rows, without changing dense
   channel evidence. **Implemented for program/provenance IR:
   `axis1_carrier_program_manifest(...)` emits within-cap
   `dense_oracle_available` rows and over-cap public static-ZZ
   `scalable_required` rows. It also emits a structured
   `axis1_carrier_approximation_book.v1` ledger for trajectory sampling, MPS
   truncation, Trotter/product-formula status, record branching, site ordering,
   and dense-oracle certification. It does not execute a scalable backend.**
   (a/c)
2. Add a GPU-only carrier execution seam for computational-subspace two-level
   state/record evidence, initially limited to schedules that can also be
   checked by dense joint-L. **Implemented as
   `axis1_carrier_execution_manifest(...)` with
   `execution_backend_contract="dense_jointL_probe"`: it consumes the carrier
   program and executes the dense-checkable route through existing joint-L
   state/record evidence. This is not the QT/MPS over-cap backend.** (a/c)
3. Add the over-cap routing guard: a selected row above the dense cap must route
   to the carrier program or fail closed with explicit provenance; it must not be
   silently skipped. **Implemented for static-ZZ over-cap idle/readout routes
   with public edge/calibration provenance. Carrier execution now fails closed on
   these rows with `requires_scalable_backend_extension`; no dense pair fallback
   or sequential channel substitution is accepted.** (a/c)
4. Add the production-carrier contract surface before backend execution.
   **Implemented as `axis1_qt_mps_state_record_contract_manifest(...)`: it
   consumes the `qt_mps_state_record` carrier program, carries the structured
   approximation book, certifies dense-checkable schedules through
   `dense_jointL_probe`, and fails closed on `scalable_required` rows until the
   real GPU trajectory/MPS backend is implemented. It does not execute MPS and
   does not claim production scalable evidence.** (a/c)
5. Run the anti-toy gates above before refreshing any artifact freeze. Hashes, if
   refreshed, are artifact identity only. **Targeted carrier program/execution
   tests are GPU-gated and currently do not refresh artifact freezes.** (a/c)
6. Add a backend-lowering probe before solver execution. **Implemented as
   `axis1_qutip_cuquantum_probe_manifest(...)`: it consumes the carrier program
   and lowers over-cap static-ZZ/readout rows into symbolic qutip-cuquantum
   `CuOperator` summaries. It does not call a solver and does not execute
   state/record evolution.** (a/c)
6. Add restricted solver probes without record claims. **Implemented as
   `axis1_qutip_cuquantum_state_probe_manifest(...)` for an explicit slow
   density-state `mesolve` gate and
   `axis1_qutip_cuquantum_trajectory_probe_manifest(...)` for the faster
   `mcsolve` trajectory candidate seam. Both are restricted to carrier-program
   rows with no measurement boundary and neither is a production QT/MPS backend
   claim.** (a/c)
7. Add a restricted record probe for sequential over-cap Z measurement boundaries.
   **Implemented as `axis1_qutip_cuquantum_record_probe_manifest(...)`: it
   supports idle substeps, supported one-qubit frontend-control substeps, and
   one or more sequential Z measurement substeps, including partial-register
   readout, projects public detector / logical XOR wiring, and emits no `.b8`,
   DEM, decoder output, or production scalable-backend claim.** (a/c)

## Implementation Evidence - Program Seam

Implemented files:

- `src/qec_twin/simulator/axis1_carrier_program.py`
- `src/qec_twin/simulator/axis1_carrier_execution.py`
- `src/qec_twin/simulator/axis1_qutip_cuquantum_probe.py`
- `src/qec_twin/simulator/__init__.py`
- `tests/test_simulator_axis1_schedule.py`
- `src/qec_twin/simulator/README.md`

The implemented object is only a carrier-program IR. It records backend contract,
GPU requirement, site order, selected dense-oracle-available rows, over-cap
scalable-required rows, static-ZZ edge/calibration provenance, local Markovian
term families, public local Lindblad context terms such as thermal excitation,
measurement boundaries, and the structured approximation book required before a
production trajectory/MPS backend can execute these rows. It sets
`claims_dense_channel_evidence=false`, `claims_dem_decoder_semantics=false`, and
`claims_axis2_source_timeline=false`. It does not run an MPS/QT backend and does
not produce state/record samples. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'carrier_program'
```

Expected use: this command must complete successfully before extending the seam
into an executable carrier backend. The outcome is a verification gate over the
program seam, not a metric. (a/c)

## Implementation Evidence - Dense Probe Execution Seam

`axis1_carrier_execution_manifest(...)` consumes the carrier program and executes
the default dense-checkable route by reusing the existing GPU joint-L
`axis1_state_evolution_evidence_manifest(...)` and
`axis1_measurement_record_evidence_manifest(...)` paths. The execution contract
is `dense_jointL_probe`; this is not a QT/MPS backend and not an over-cap
scalable carrier claim. For any program containing `scalable_required` rows, the
execution manifest returns a failed verification gate with
`blocked_reason="requires_scalable_backend_extension"` and no state/record
execution payload. It sets `claims_dense_channel_evidence=false`,
`claims_dem_decoder_semantics=false`, `claims_axis2_source_timeline=false`, and
`claims_scalable_backend_completed=false`. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'carrier_execution'
```

Expected use: this command validates the dense execution seam and the explicitly
selected restricted over-cap carrier seams. Passing rows are still verification
gates, not production scalable backend evidence. (a/c)

`axis1_carrier_execution_manifest(..., execution_backend_contract="qt_mps_state_record")`
now delegates to `axis1_qt_mps_restricted_execution_manifest(...)` and embeds the
restricted QT/MPS acceptance policy in the carrier execution manifest. It sets
`claims_qt_mps_backend_execution=true`, but keeps
`claims_exact_joint_lindblad_generator=false`,
`claims_dense_channel_evidence=false`,
`claims_production_scalable_backend=false`, and
`claims_scalable_backend_completed=false`. (a/c)

QT/MPS carrier execution also accepts an explicit `execution_backend_options`
dictionary for declared backend knobs (`max_bond`, `max_branches`,
`microstep_count`, `finite_step_order`, finite-bond candidate gates,
`trajectory_count`, `rng_seed`, and `dense_oracle_certification`). Unknown keys
fail closed, and non-QT/MPS execution contracts reject backend options. These are
backend configuration gates, not scored quantities. (a/c)

## Implementation Evidence - Restricted qutip-cuQuantum Carrier Execution

`axis1_carrier_execution_manifest(..., execution_backend_contract="qutip_cuquantum_restricted_state_record_probe")`
now connects the already preregistered qutip-cuquantum trajectory/record probes
to the carrier execution seam. It consumes `Axis1CarrierProgram` rows with
`backend_contract="qutip_cuquantum_probe"` and can execute supported
`scalable_required` rows instead of only failing closed. The covered slice is
still restricted: no production QT/MPS backend execution, no dense channel
evidence, no `.b8`, no DEM/decoder semantics, and no Axis-2 source timeline.
It sets `claims_qutip_cuquantum_execution=true`,
`claims_qt_mps_backend_execution=false`,
`claims_production_scalable_backend=false`, and
`claims_scalable_backend_completed=false`. (a/c)

Anti-toy gates:

- Over-cap static-ZZ idle row: the qutip backend executes the
  `scalable_required` carrier row and reports the `ZZ` Hamiltonian families in
  the applied substep ledger. (a/c)
- Over-cap `H(0)` plus Z readout: the backend executes the one-qubit-control row
  and measurement boundary through the same carrier execution entrypoint; the
  record branch table must expose the `CTRL_H`/`ZZ` Hamiltonian families and the
  expected `m0` half/half branch weights while non-driven readout bits remain
  unexcited. This is a verification gate, not a metric. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'carrier_execution'
```

Expected use: this command validates both the default dense execution seam and
the explicit restricted qutip-cuquantum over-cap execution adapter. It is not
evidence of the future QT/MPS production backend. (a/c)

## Implementation Evidence - QT/MPS Contract Surface

`axis1_qt_mps_state_record_contract_manifest(...)` consumes the same
`Axis1CarrierProgram` with `backend_contract="qt_mps_state_record"`, validates
the structured approximation book, and exposes the manifest surface the future
GPU trajectory/MPS backend must satisfy. Within-cap schedules are certified by
delegating to `axis1_carrier_execution_manifest(...)`; over-cap
`scalable_required` schedules fail closed with
`blocked_reason="qt_mps_backend_not_implemented_for_scalable_required"`. It sets
`claims_qt_mps_backend_execution=false`,
`claims_production_scalable_backend=false`,
`claims_dense_channel_evidence=false`, `claims_dem_decoder_semantics=false`, and
`claims_axis2_source_timeline=false`. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'qt_mps_contract'
```

Expected use: this command validates the backend contract surface and the
over-cap fail-closed boundary. The outcome is a verification gate, not a metric.
(a/c)

Expected use: this command must complete successfully before wiring a real
QT/MPS over-cap carrier. The outcome is a verification gate over the execution
seam, not a metric. (a/c)

## Implementation Evidence - Restricted QT/MPS Execution Slice

`axis1_qt_mps_restricted_execution_manifest(...)` is the first executable
quimb/torch-CUDA MPS adapter behind the `qt_mps_state_record` carrier program.
It currently supports Hamiltonian/control terms, including supported compiler
two-qubit frontend controls, local product-channel collapse branches for
`T1/T1_UP/T2/RD`, and Z-record rows. It can execute over-cap static-ZZ /
frontend-control readout fixtures through an MPS state rather than the
qutip-cuquantum solver; the anti-toy local-collapse gate checks that a frontend
`H` followed by local `T1` shifts the Z-readout population by the declared
amplitude-damping channel formula. This is still a deliberate boundary: the
full production QT/MPS carrier still needs a finite-step policy for the summed
Lindbladian plus production-grade trajectory/error-control hardening. (a/c)

The restricted path declares
`hamiltonian_evolution_policy="operator_family_order_product_formula"`,
`collapse_evolution_policy="local_product_channel_branching"`, and
`exact_joint_generator_claim=false`. It also exposes `microstep_count>=1` and a
finite-step order: `first_order` maps to
`operator_family_product_formula_v1`, while `strang_second_order` maps to
`strang_hamiltonian_collapse_product_formula_v1`. Both split each public schedule
substep into equal internal microsteps. Product-formula execution is an
approximation gate, not dense joint-L channel evidence and not a replacement for
`forward.joint_lindbladian` on small windows. (a/c)

For dense-checkable schedules with measurement records, the restricted MPS
manifest now runs an exact dense joint-L record certification by comparing its
record branch probabilities with
`axis1_measurement_record_evidence_manifest(...)`. The comparison reports
`comparison_outcome_is_metric=false`; the tolerance is a verification gate, not
a new scored quantity. For over-cap schedules, this certification is not
executed because dense rows are not allowed to replace `scalable_required`
carrier rows. (a/c)

The restricted MPS manifest also supports seeded sampled trajectories via
`trajectory_count` and `rng_seed`, using `torch.Generator(cuda)`. Sampled runs
emit `record_counts` and empirical record frequencies and deliberately skip
dense exact-probability certification with
`comparison_outcome_is_metric=false`. This is a trajectory-execution contract,
not a new metric and not exact dense channel evidence. The policy ledger accepts
sampled execution evidence only when `rng_seed` is explicit; default seed zero is
a deterministic execution fallback, not accepted sampled evidence. (a/c)

`axis1_qt_mps_trajectory_seed_sweep_manifest(...)` now runs the same
compiler-generated schedule across explicit distinct seeds with a declared
`trajectory_count`. It has two separate acceptance flags:
`accepted_as_restricted_seed_sweep_evidence` for caller-declared empirical
frequency-spread gates, and `accepted_as_dense_calibrated_trajectory_evidence`
for dense-checkable schedules whose empirical frequencies also pass a
caller-declared dense joint-L record-probability gate. Over-cap schedules report
dense calibration as unavailable. These gates are not metrics, confidence
intervals, exact probability claims, or production error bounds. (a/c)

`axis1_qt_mps_restricted_evidence_bundle_manifest(...)` combines the finite-bond
convergence sweep and sampled seed sweep for one schedule. It is a review-facing
gate aggregation with separate restricted and dense-calibrated acceptance flags.
It still keeps `accepted_as_production_error_bound=false`,
`accepted_for_production_scalable_backend=false`, and
`comparison_outcome_is_metric=false`. (a/c)

`axis1_qt_mps_resource_probe_manifest(...)` wraps that bundle with actual
`torch.cuda` peak allocated/reserved memory reporting. It is designed for heavy
resource smoke gates such as a caller-declared 30 GiB target, but it does not
allocate padding tensors. If the real QT/MPS workload only reserves a few GiB, a
30 GiB gate fails and records the shortfall. This is a resource gate, not a
scientific metric or production scalability proof. (c)

The finite-step policy now has an anti-toy convergence gate: a compiler-produced
within-cap `H + T1` substep keeps exact dense record certification enabled and
shows the dense joint-L record difference decreasing as `microstep_count`
increases from 1 to 2 to 4. The difference is a verification gate only, with
`comparison_outcome_is_metric=false`; the backend still reports
`claims_exact_joint_lindblad_generator=false`. (a/c)

The same fixture also exercises `finite_step_order="strang_second_order"`: the
symmetric Hamiltonian/collapse split reduces the dense-record difference relative
to the first-order split at fixed microstep count in the registered GPU gate. This
does not upgrade the backend to exact joint-L or add a scored quantity. (c)

The MPS manifest also carries a truncation ledger. With `max_bond=None`, no
explicit MPS truncation is requested and the ledger is complete with zero
discarded weight. With finite `max_bond`, the restricted slice records a CUDA
shadow-state Schmidt-tail ledger before each supported two-site
Hamiltonian/control gate. This is an approximation risk ledger, not a metric and
not a production error bound. Optional caller-declared
`worst_cut_discarded_weight_gate` and `total_discarded_weight_gate` values are
finite-bond candidate gates only; even if they pass, the manifest keeps
`accepted_as_production_error_bound=false`. The ledger also reports the
conservative qubit-MPS exact-bond sufficient cap `2**ceil(n_sites/2)`;
at-or-above-cap is exact representability bookkeeping, not production error
control. (a/c)

`axis1_qt_mps_bond_sweep_manifest(...)` now runs the same compiler-generated
schedule at declared finite `max_bond` values and compares exact-enumeration
record probabilities against the largest-bond run as an internal convergence
gate. For dense-checkable record schedules, the largest-bond reference must also
pass dense joint-L record certification before the sweep is accepted. A `[1, 2]`
Bell/CZ sweep catches under-bonding; a `[2, 4]` sweep passes because both bonds
are at/above the two-qubit exact-sufficient cap and the reference passes dense
certification. A noncommuting `H + T1` first-order product-formula sweep is
rejected even when internally converged because the reference fails dense
certification. This is a convergence gate, not a metric or production error
bound. (a/c)

The restricted MPS manifest now centralizes the above finite-step, trajectory,
over-cap, and finite-bond decisions in
`restricted_acceptance_policy`. The block may accept a run as restricted
execution evidence, exact dense-probability evidence for dense-checkable exact
enumeration, or sampled execution evidence for empirical trajectories with an
explicit seed. It always keeps
`accepted_for_production_scalable_backend=false`. The policy block is a ledger
of gates, not a new metric. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'qt_mps_restricted_execution'
```

Expected use: this command validates the first executable MPS carrier slice,
including local collapse product-channel branching, supported two-qubit control
execution, finite-bond risk ledgering, and seeded sampled trajectories. It is
not evidence that the production QT/MPS backend is complete, and it introduces
no new metric. (a/c)

## Implementation Evidence - qutip-cuQuantum Symbolic Lowering Probe

`axis1_qutip_cuquantum_probe_manifest(...)` consumes
`Axis1CarrierProgram` rows using `backend_contract="qutip_cuquantum_probe"` and
builds symbolic qutip-cuquantum `CuOperator` summaries for Hamiltonian and
collapse terms. It pins over-cap term lowering without solving the master
equation. The manifest sets `claims_state_execution=false`,
`claims_record_execution=false`, `claims_dense_channel_evidence=false`,
`claims_dem_decoder_semantics=false`, and
`claims_axis2_source_timeline=false`. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'qutip_cuquantum_probe'
```

Expected use: this command must complete successfully before any qutip-cuquantum
solver or QT/MPS carrier is allowed to consume over-cap program rows. The outcome
is a verification gate over backend lowering, not a metric. (a/c)

## Implementation Evidence - Restricted qutip-cuQuantum Solver Probes

`axis1_qutip_cuquantum_state_probe_manifest(...)` calls qutip-cuquantum
`mesolve` only for carrier-program rows with no measurement boundary. It is an
explicit slow gate and is skipped in the default test path unless
`AIQEC_RUN_QUTIP_STATE_PROBE=1` is set. It emits final Z-basis probabilities
from the resulting density state but no density-matrix payload, records, `.b8`,
DEM, decoder output, or dense channel evidence. (a/c)

`axis1_qutip_cuquantum_trajectory_probe_manifest(...)` calls qutip-cuquantum
`mcsolve` for the same no-boundary carrier-program slice and emits final
single-trajectory Z-basis probabilities. It is a candidate seam toward a future
trajectory/MPS carrier; it is not density-state evidence, not record execution,
and not a production scalable backend. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'qutip_cuquantum_trajectory_probe or qutip_cuquantum_state_probe'
```

Expected use: the default command validates the fast trajectory probe plus
state-probe fail-closed guards; the density-state solver execution itself is a
separate explicit slow gate. These outcomes are verification gates, not metrics.
(a/c)

## Implementation Evidence - Restricted qutip-cuQuantum Record Probe

`axis1_qutip_cuquantum_record_probe_manifest(...)` runs the restricted
qutip-cuquantum trajectory probe through idle substeps, supported one-qubit
frontend-control substeps, and one or more sequential Z measurement boundaries,
including partial-register readout, and derives detector/logical records only
from public schedule XOR wiring. It is the first over-cap record-boundary seam,
not full analog record emission. The anti-toy gate includes a compiler-generated
`H(0)` followed by over-cap Z readout: the carrier row must expose `CTRL_H` and
the resulting record distribution must put half the probability on each `m0`
branch while other readout bits stay unexcited. It sets
`claims_b8_artifact=false`, `claims_decoder_integration=false`,
`claims_dense_channel_evidence=false`, `claims_axis2_source_timeline=false`, and
`claims_production_scalable_backend=false`. (a/c)

Targeted GPU-gated test command:

```bash
conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'qutip_cuquantum_record_probe'
```

Expected use: this command must complete successfully before extending the
record probe beyond restricted sequential Z measurement boundaries. The outcome
is a verification gate, not a metric. (a/c)

## Scope Boundary

This prereg does not do Axis-2, source timelines, full analog record emission,
leakage/qutrit integration, full `d=5`/`d=7` surface-code production, or new
metric registration. It only registers the next Axis-1 carrier seam needed
before over-cap joint-L schedules can be treated as non-toy state/record
evidence. (a/c)

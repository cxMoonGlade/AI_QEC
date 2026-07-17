Standalone user-facing simulator frontend.

This package owns circuit/code construction, Stim-compatible artifact export,
`.b8` record output, manifest schemas, and decoder plumbing. Carrier evolution
lives in the sibling `error_coupling_simulator.carrier` package; specified
mechanisms and evaluator-only process truth live in
`error_coupling_simulator.mechanisms` and `.noise_processes`.

Distribution/runtime boundary:

- Frontend runtime ownership is package-local and independent of repository-only tooling.
- Google r01/r10 `.stim` + metadata files are explicit external circuit/geometry/schedule inputs,
  not bundled assets or sources of noise parameters. Ququart transport derives its channel from
  explicit package-owned `CZParams`, or accepts an in-memory channel / explicit serialized cache;
  repository scratch is not a default and Kraus is not classified as external data.
- CUDA-Q Grover is an optional plugin surface. Install/run its `cudaq-grover` extra only in the
  retained `aiqec` environment and a separate process; canonical `ecs` deliberately excludes it.
- Release acceptance builds the real sdist, builds and installs its wheel into an isolated target,
  removes the checkout from import resolution, and runs import/core smokes. Editable-install tests
  do not establish this boundary.

Current slice:

- `CircuitIR` and `CircuitBuilder` for small user-defined detector circuits.
- `CodeSpec`, `XZZXCodeSpec`, and `compile_code_spec(...)` for compiling a
  small 3x3 checkerboard XZZX compiler smoke into ordinary `CircuitIR`.
- Explicit frontend construction structure: `OperationSpec`/`OperationSet`,
  `ScheduleTemplate`, and `RecordLayout`.
- Axis-1 compiler/schedule seam:
  `SubstepSchedule` / `AnalogSubstepIR` plus
  `CircuitIR -> SubstepSchedule`, `CodeSpec -> SubstepSchedule`, and read-only
  `stim.Circuit -> SubstepSchedule` extractors.
  This is public schedule metadata only: it records substep grouping, duration
  brackets, idle/active qubits, measurement/reset boundaries, and provenance for
  a later `carrier.joint_lindbladian` bridge. It does not contain Hamiltonians,
  collapse operators, channels, Kraus/PTM data, source timelines, or evaluator
  mechanism truth. Extractor-produced schedules carry a builder-owned in-process
  compiler seal; public `SubstepSchedule(...)` construction does not satisfy
  frontend Axis-1 gates by itself.
  The Stim importer preserves `TICK`, `QUBIT_COORDS`, `DETECTOR`, and
  `OBSERVABLE_INCLUDE` metadata for schedule provenance, but rejects embedded
  Stim noise instructions because those are record-carrier Pauli noise, not
  analog joint-L dynamics. Reserved schedule source kinds such as
  `code_spec_compiler` and `stim_circuit` are set only by their wrappers; public
  `CircuitIR` extraction cannot claim those source kinds.
  `stim_circuit_to_substep_schedule(..., static_zz_couplings=...,
  static_zz_calibrations=...)` accepts the same public static-ZZ device sidecar
  as the CodeSpec/CircuitIR path and folds it into the schedule source hash;
  Stim `CZ` history is still not promoted into persistent static-coupling truth.
  A `CodeSpec` may carry public static-ZZ device/schedule edges using
  `Axis1StaticZZDeviceSpec(...).to_metadata()` or the equivalent
  `metadata["axis1_static_zz_couplings"]` shape. It may also carry optional
  public per-edge `metadata["axis1_static_zz_calibrations"]` records with
  `zeta_rad_per_ns`; every calibration must reference an already declared edge.
  The compiler validates them through
  `CircuitBuilder.declare_static_zz_couplings(...)` and promotes them to
  top-level `CircuitIR` metadata before schedule extraction. These edges and
  calibrations are schedule metadata for Axis-1 lowering, not evaluator
  mechanism truth, Hamiltonian/operator payload, or Axis-2 source state.
  A `CodeSpec`, `CircuitBuilder`, or Stim schedule importer may also carry
  public local Markovian context with `Axis1LocalLindbladContextSpec`, including
  explicit computational-subspace thermal excitation selection
  (`gamma_up_per_ns`) and optional active-pair computational-subspace fSim
  residual Hamiltonian selection (`fsim_delta_theta_rad`,
  `fsim_delta_phi_rad`). This metadata selects/parameterizes local Axis-1
  primitive lowering and is folded into source hashes when present; it is not
  Stim-Pauli noise, not a serialized channel payload, not leakage/qutrit
  integration, and not Axis-2 source truth.
- Explicit idle durations: `CircuitBuilder.idle(..., duration_ns=...)` records a
  positive idle duration in the schedule as
  `dt_source="explicit_circuit_idle_duration"`. Only explicit-duration idle
  substeps are selected for Axis-1 idle joint channels; bracket-only idles remain
  metadata and are not silently assigned a default `dt`.
- Explicit readout durations: `CircuitBuilder.measure(..., duration_ns=...)`
  records a positive measurement/readout window as
  `dt_source="explicit_circuit_measurement_duration"`. The current Axis-1 bridge
  lowers this window only as pre-measurement readout dephasing plus T1/T2 context
  (`RD/RD_B/T1/T2`), then performs the ordinary projective measurement branch.
  Classical assignment flips, correlated assignment crosstalk, and reset
  infidelity are separate record/preparation instruments, not joint-L
  primitives. MIST/leakage remains out of scope.
- Minimal Axis-1 joint-channel comparison: `joint_channel_comparison_gate(...)` consumes a
  compiler-generated `SubstepSchedule`, derives the narrow
  `Axis1MechanismSelectionPlan` for the registered `ZZ x T2` and contextual
  `DR x ZZ` rows, lowers those selections, and calls
  `carrier.joint_lindbladian` diagnostics to emit comparison evidence rows. The
  `DR x ZZ` row uses the declared one-qubit substep context
  `DR + ZZ + T2 + T1` while reporting the `DR x ZZ` commutator as the nonzero
  witness. Lowering is routed through the minimal
  `error_coupling_simulator.mechanisms.axis1_primitives` registry for the current local
  two-qubit-window
  `DR/ZZ/T2/T1/T1_UP/T2_B/T1_B/T1_UP_B/RD/RD_B/FSIM_SWAP/FSIM_PHASE`
  primitives, though this comparison
  harness uses only the registered DR/ZZ/T1/T2 subset; manifests record the
  registry id and declare that registry metadata contains no operator payload.
  It is a gate harness, not record emission or full coupled-process execution.
  `write_joint_channel_comparison_evidence(...)` writes
  `joint_channel_comparison.json`
  with a content hash and PASS/FAIL verdict. The reproducible command
  `python -m error_coupling_simulator.frontend.joint_channel_comparison_runner --out-dir ...`
  builds the fixed compiler-generated fixture, writes
  `joint_channel_comparison.json`, and by default writes
  `joint_channel_comparison.freeze.json` only when no freeze exists. If a freeze exists,
  the runner validates it instead of silently refreshing it. Use
  `--refresh-freeze` only for an intentional evidence-schema or value update;
  `--validate-freeze` recomputes the evidence file sha256 and manifest content
  hash.
- Axis-1 joint-channel evidence: `axis1_substep_channel_evidence_manifest(...)`
  and `write_axis1_substep_channel_evidence(...)` consume the same sealed
  compiler schedule and the generic
  `axis1_schedule_joint_channel_selector_v1` selection plan, lower supported
  one-qubit frontend controls
  (`C_XYZ/C_ZYX/H/H_XY/H_XZ/S/S_DAG/SQRT_X/SQRT_X_DAG/SQRT_Y/SQRT_Y_DAG/SQRT_Z/SQRT_Z_DAG/X/Y/Z`),
  explicit-duration idle pair/cluster windows, explicit-duration readout
  pair/cluster windows, active CZ, declared static-ZZ, and supported two-qubit
  frontend controls
  (`CX/CY/CZ/ISWAP/ISWAP_DAG/SQRT_XX/SQRT_XX_DAG/SQRT_YY/SQRT_YY_DAG/SQRT_ZZ/SQRT_ZZ_DAG/SWAP/XCX/XCY/XCZ/YCX/YCY/YCZ`)
  including spectator clusters up to 5 local qubits. Generic frontend gates are
  lowered as exact `CTRL_*`
  control Hamiltonian representatives and recorded in `ideal_controls`; local
  noise/coupling mechanisms are recorded separately in `lowered_mechanisms`.
  Active-only one-qubit substeps are lowered as local or active-support
  joint-L carriers, so a positive-duration frontend gate no longer needs an
  idle spectator to be represented. A single-active one-qubit drive with
  multiple idle spectators is lowered as one union-support cluster window. A
  same-substep multi-active one-qubit layer with visible idle spectators and no
  declared static-ZZ edge inside the visible support is also lowered as one
  union-support cluster window, with one `CTRL_*` Hamiltonian per active local
  factor. Static-ZZ cluster rows record `coupling_edges` and embed those ZZ
  Hamiltonian terms in the same joint generator as the ideal controls and local
  T1/T2 context; if public per-edge static-ZZ calibrations are present, those
  coefficients override the global `zeta_rad_per_ns` only for the matching
  edges. Supported two-qubit frontend-control substeps with visible
  idle spectators, active-pair declared static-ZZ edges on non-CZ controls, or
  declared cross-window static-ZZ edges inside the same active layer are
  similarly lowered as one union-support joint channel when the selected local
  support is at most 5 qubits; target-pair ordering is preserved inside that
  local support. Static edges that would otherwise be dropped by disjoint pair
  rows force union-support lowering or fail closed through coverage when over
  cap. The dense Choi carrier stays GPU-only and uses an SVD fallback when
  Hermitian eigensolve fails to converge on highly degenerate PSD Choi matrices.
  Explicit-duration idle substeps are selected as a two-qubit idle-pair row
  when the support is exactly two qubits with no declared static-ZZ edge, and
  as one idle union-support row for other visible supports up to 5 qubits. If a
  declared static-ZZ edge lies inside the idle support, the row records
  `coupling_edges` and embeds those ZZ Hamiltonian terms with the idle T1/T2
  context in the same joint generator. Union-support lowering also honors
  explicitly selected computational-subspace finite-temperature excitation
  primitives `T1_UP/T1_UP_B` through public
  `Axis1LocalLindbladContextSpec`; default selector rows do not infer those
  rates from frontend circuits. Two-qubit frontend-control rows also honor
  explicitly selected computational-subspace fSim residual Hamiltonian
  primitives `FSIM_SWAP/FSIM_PHASE` on the active pair; default selector rows do
  not infer residual fSim from frontend gate names. Explicit-duration Z readout
  windows use the same
  support gate: ordinary two-qubit measured windows keep the pair row, while
  one-qubit, odd/multi-qubit, spectator, and declared static-ZZ readout windows
  up to 5 local qubits are lowered as one union-support joint channel before
  the projective measurement branch. `RD` collapse records are added only on
  measured qubits; idle spectators receive background `T1/T2` context.
  Readout supports above the dense gate still fall back to selected disjoint
  pair windows and report leftover measured qubits as coverage gaps.
  `DR` remains a joint-vs-composed diagnostic primitive and is not used as a generic ideal-gate
  stand-in. The bridge then calls
  `error_coupling_simulator.carrier.joint_lindbladian.assemble_substep_channel` to produce
  carrier evidence rows. The artifact reports joint-generator semantics,
  dimension, Kraus count, TP residual, provenance, ideal controls, and lowered
  mechanism manifests; it deliberately does not serialize Kraus stacks, Choi
  matrices, or superoperator matrices.
  `freeze_axis1_substep_channel_evidence(...)` writes a
  drift guard for that evidence file, mirroring the joint-channel comparison freeze behavior. The
  manifest carries a coverage ledger listing selected and omitted substeps so
  unsupported barriers/readout/reset/operation kinds are never silently claimed;
  `full_positive_duration_coverage=false` means the rows passed only for the
  selected supported substeps. It also carries a shared `selection_partition`
  ledger: channel/state/record evidence all consume the same schedule-ordered
  substep layers, and same-substep selected supports must be qubit-disjoint
  unless represented as one union-support window.
- Axis-1 selected-channel state evidence:
  `axis1_state_evolution_evidence_manifest(...)` and
  `write_axis1_state_evolution_evidence(...)` take the same generic selection
  plan, assemble each selected joint-L channel on the GPU, and apply the
  selected channels in schedule order to an exact small-N density matrix
  initialized at all-zero. Same-substep selected windows are supported when
  their qubit supports are disjoint, and one-qubit drive substeps with multiple
  idle spectators can be represented by a single union-support cluster window,
  including active-only local rows, multi-active no-static rows, and static-ZZ
  cluster rows over all declared static edges inside the visible support.
  Two-qubit control spectator clusters are supported for selected local support
  size up to 5 qubits. They are recorded as one selected layer, while
  overlapping selected windows fail closed. Cluster
  supports larger than the native fused local-Kraus
  kernel target limit use the dense Torch/CUDA embedding fallback, not a CPU
  path. The artifact records
  the applied layer/substep ledger, the shared `selection_partition`, final
  Z-basis probabilities, trace residual, coverage, frontend ideal controls where
  present, and provenance. It requires CUDA and declares no logical code semantics, no full-schedule operation
  semantics, no analog record emission, no Axis-2 source projection, and no
  leakage/qutrit integration. `freeze_axis1_state_evolution_evidence(...)`
  guards this JSON evidence identity with the same file-hash/content-hash style
  used by the joint-channel comparison, channel, and record evidence artifacts.
- Axis-1 measurement-record evidence:
  `axis1_measurement_record_evidence_manifest(...)` and
  `write_axis1_measurement_record_evidence(...)` extend the exact small-N
  carrier by enumerating exact Pauli-basis measurement branches after selected
  joint-L channels. X/Y measurement and reset boundaries use exact basis
  rotations around the Z-branch enumerator. By default this path is exact/ideal
  at the reported-record boundary. Passing `Axis1ReadoutResetInstrumentSpec`
  explicitly adds a classical reported-record assignment map
  (`p(0->1)`, `p(1->0)`, and same-operation adjacent-pair both-flip crosstalk)
  plus a post-reset preparation flip after standalone reset and `MR*` reset.
  Those instrument probabilities are heuristic unless separately grounded; the
  application of the declared stochastic map is exact. They are not Hamiltonian
  or collapse-operator primitives, not Axis-2 source projection, and not
  MIST/leakage/qutrit modeling. The artifact records measurement keys,
  measurement records, detector/logical records derived from public XOR wiring,
  record probabilities, total-probability residual, selected-channel application
  ledger, the shared `selection_partition`, reset/instrument ledgers, frontend
  ideal controls where present, coverage, and provenance. It does not write
  `.b8`, decoder artifacts, source timelines, or channel payload arrays.
  `freeze_axis1_measurement_record_evidence(...)` writes a drift guard for this
  JSON record evidence, and
  `python -m error_coupling_simulator.frontend.axis1_codespec_runner --out-dir ...` builds the
  fixed mixed-basis `CodeSpec -> SubstepSchedule -> Axis-1 record evidence`
  fixture with `source_kind="code_spec_compiler"` and a matching freeze
  manifest. One-qubit drive substeps with multiple idle spectators are lowered
  as one union-support cluster channel, so coverage is reported over all visible
  active-idle participant windows instead of by substep id alone. Multi-active
  no-static layers expose one `CTRL_*` entry per active local factor; static-ZZ
  cluster rows additionally expose the public `coupling_edges` used for
  Hamiltonian lowering. The 5-qubit CodeSpec `CX` spectator windows are covered
  by true union-support cluster rows, not pair-only selected rows.
- Axis-1 carrier execution seam:
  `axis1_carrier_execution_manifest(...)` consumes the
  `axis1_carrier_program_manifest(...)` program. Its default execution backend
  contract is `dense_jointL_probe`, which executes only the
  `dense_oracle_available` route through the already registered GPU joint-L
  state/record evidence and fails closed on `scalable_required` rows with
  `blocked_reason="requires_scalable_backend_extension"`. Passing
  `execution_backend_contract="qt_mps_state_record"` runs the restricted
  quimb/torch-CUDA QT/MPS state/record backend for supported over-cap rows and
  embeds its `restricted_acceptance_policy` in the carrier execution manifest.
  QT/MPS backend knobs are passed explicitly via `execution_backend_options`
  (`max_bond`, `max_branches`, `microstep_count`, `finite_step_order`,
  finite-bond gates, `trajectory_count`, `rng_seed`, and
  `dense_oracle_certification`). Unknown keys fail closed. The
  `mcwf_mps_state_record` path accepts `local_dims`, `initial_levels`,
  `leaked_readout_b`, `max_bond`, `microstep_count`, `finite_step_order`,
  finite-bond gates, `trajectory_count`, and `rng_seed`; other execution
  contracts reject backend options. On both MPS paths, `max_bond` is either
  `None` or a strictly positive
  integral value. Booleans, floats, strings, zero, and negative values are
  rejected rather than narrowed with `int(...)`.
  Passing
  `execution_backend_contract="qutip_cuquantum_restricted_state_record_probe"`
  runs the restricted qutip-cuquantum trajectory/record probes for supported
  over-cap rows, including static-ZZ idle and one-qubit-control plus Z-readout
  rows. These restricted GPU backends are executable evidence, but they are still
  not the production scalable carrier. Passing
  `execution_backend_contract="mcwf_mps_state_record"` runs the first
  fixed-microstep MCWF-over-MPS slice for declared `local_dims`, including
  qutrit/ququart carrier states, first-slice one-site qutrit leakage families
  (`LEAK_EXCHANGE_12`, `LEAK_SEEP_21`, `LEAK_HEAT_12`), and first-slice
  compiler-generated two-site leakage-transport Hamiltonians
  (`LEAK_EXCHANGE_11_02`, `LEAK_MOBILITY_12_21`,
  `LEAK_TRANSPORT_30_12`, `LEAK_TRANSPORT_31_22`) plus diagonal conditional
  leaked-neighbor phase Hamiltonians (`LEAK_COND_PHASE_LEFT2_RIGHTZ`,
  `LEAK_COND_PHASE_LEFTZ_RIGHT2`) when supplied through public Axis-1
  instantaneous context. Supported same-support Hamiltonian terms are summed
  and matrix-exponentiated per microstep; collapse/no-jump handling remains the
  declared finite-step MCWF approximation. Mixed or multilevel `max_bond`
  requests still fail closed until a mixed-dimension finite-bond ledger is
  implemented; leakage-removal/DQLR protocol semantics, leakage-aware `.dem`
  integration, and production-scale error control remain unfinished.
  The path does not fall back to dense, qutip-cuquantum, or restricted QT/MPS
  execution.
  All contracts declare no dense
  channel-evidence artifact, no DEM or decoder semantics, no Axis-2 source
  timeline, and no completed scalable backend claim. Their hashes are evidence
  identity only, not metrics.
- Dense computational-subspace Axis-1 evidence refuses schedules carrying
  public qutrit leakage context instead of silently dropping those terms. Such
  schedules must route through `mcwf_mps_state_record` with declared
  `local_dims >= 3`. The separate
  `axis1_qutrit_leakage_oracle_certification_manifest(...)` verifies the
  one-site qutrit leakage lowering against `leakage_channel_super`; it is a
  certification gate, not the default dense evidence path and not a serialized
  channel payload.
- Axis-1 MCWF/MPS contract seam:
  `axis1_mcwf_mps_state_record_contract_manifest(...)` consumes the same
  carrier program with `backend_contract="mcwf_mps_state_record"` and declares
  the combined architecture: MCWF owns the same-substep trajectory unraveling of
  the summed `H_list` and `c_list`, while MPS owns the pure-state carrier
  representation. The contract is dimension-polymorphic through public backend
  config `local_dims`, so qubit, qutrit, ququart, and mixed local dimensions are
  carrier-level cases rather than different MCWF logics. This is a contract-only
  surface: no trajectory execution, no dense channel payload, no `.b8/.dem`
  decoder semantics, no Axis-2 source timeline, and no production scalable
  backend claim.
- Axis-1 MCWF/MPS execution:
  `axis1_mcwf_mps_state_record_execution_manifest(...)` is the first executable
  backend slice behind `mcwf_mps_state_record`. It executes sampled
  fixed-microstep quantum-jump MCWF trajectories stored as quimb/torch-CUDA MPS
  states with declared `local_dims` and optional `initial_levels`. Existing
  computational-subspace Hamiltonian/collapse families are lifted into
  multilevel sites while non-computational levels remain represented in the
  carrier. The first registered one-site qutrit leakage families are
  `LEAK_EXCHANGE_12` (`|1><2| + |2><1|`), `LEAK_SEEP_21` (`|1><2|`), and
  `LEAK_HEAT_12` (`|2><1|`). The first registered two-site transport families
  are Hamiltonian exchange blocks on ordered frontend two-qubit operation
  targets: `LEAK_EXCHANGE_11_02`, `LEAK_MOBILITY_12_21`,
  `LEAK_TRANSPORT_30_12`, and `LEAK_TRANSPORT_31_22`. They require declared
  qutrit/ququart local levels and fail closed when `local_dims` cannot
  represent the referenced level. Within each MCWF microstep, supported
  Hamiltonian terms on the same support are summed and applied as one
  `exp(-i sum(H_j) dt_micro)` matrix exponential, so same-support
  `CTRL_*`/`ZZ`/leakage Hamiltonians are not sequentialized. Collapse
  terms still compete jointly per microstep as jump candidates from the same
  compiler-generated substep; Hamiltonian-vs-collapse splitting is a finite-step
  MCWF approximation, not exact dense joint-L channel evidence. Measurement records are
  accumulated across all measurement substeps, and multilevel `MR*` reset maps
  the measured local level back to the requested computational reset state. The
  manifest requires explicit CUDA RNG provenance for accepted sampled evidence,
  records jump/no-jump diagnostics, multilevel readout policy, and MPS
  truncation ledgers. Restricted acceptance also requires a finite declared
  `mass_residual_budget`, a finite nonnegative runtime candidate-mass residual
  within that budget, and an executed independent dense certification that
  passes its gross gate. Passing `mass_residual_budget=None` executes only a
  convergence diagnostic, skips dense certification, and returns
  `execution_status="completed"`, `certification_status="not_evaluated"`,
  `diagnostic_only=true`, and verdict `fail`. An over-cap run whose independent
  oracle is unavailable similarly cannot use Record-frequency normalization as
  positive evidence. The manifest keeps
  `claims_exact_joint_lindblad_generator=false`,
  `claims_dense_channel_evidence=false`,
  `claims_axis2_source_timeline=false`, and
  `claims_production_scalable_backend=false`.
- Axis-1 QT/MPS production-carrier contract seam:
  `axis1_qt_mps_state_record_contract_manifest(...)` consumes the same
  carrier program with `backend_contract="qt_mps_state_record"`, carries the
  structured approximation book, certifies dense-checkable schedules through
  `dense_jointL_probe`, and fails closed on `scalable_required` rows with
  `blocked_reason="qt_mps_backend_not_implemented_for_scalable_required"`.
  It is the backend contract surface for the existing computational-subspace
  QT/MPS line; it does not execute that backend and does not claim production
  scalable evidence.
- Axis-1 restricted QT/MPS execution:
  `axis1_qt_mps_restricted_execution_manifest(...)` is the first executable
  quimb/torch-CUDA computational-subspace MPS slice for carrier programs with
  `backend_contract="qt_mps_state_record"`. It supports Hamiltonian/control
  terms, including supported compiler two-qubit frontend controls, local
  product-channel collapse branches (`T1/T1_UP/T2/RD`), and Z-record rows,
  including over-cap static-ZZ and frontend-control readout fixtures.
  Unsupported collapse or control families fail closed. The path declares an
  operator-family-order product formula and local product-channel branching; it
  is not the full `mcwf_mps_state_record` carrier and must not be cited as
  strict continuous-time MCWF evidence.
  It exposes `microstep_count` for equal-duration internal microsteps and
  `finite_step_order` for either `first_order` or
  `strang_second_order` Hamiltonian/collapse splitting. It does not claim exact
  joint-generator channel evidence, DEM/decoder semantics, Axis-2 source
  timelines, or production scalable backend completion. For
  dense-checkable schedules with measurement records it can also run an exact
  dense joint-L record certification against
  `axis1_measurement_record_evidence_manifest(...)`; that comparison is a
  verification gate and explicitly not a metric. It also has an optional seeded
  sampled-trajectory mode (`trajectory_count`, `rng_seed`) using
  `torch.Generator(cuda)`; sampled record frequencies are empirical execution
  evidence and are not dense-certified exact probabilities. The restricted
  acceptance policy requires an explicit `rng_seed` before sampled trajectories
  are accepted as sampled execution evidence; an omitted seed may still execute
  with the documented default-zero policy but is not accepted by the policy
  ledger. `axis1_qt_mps_trajectory_seed_sweep_manifest(...)` runs the same
  compiler-generated schedule across explicit distinct seeds, compares empirical
  record-frequency spread under a caller-declared gate, and optionally compares
  dense-checkable schedules against dense joint-L record probabilities under a
  separate caller-declared gate. These are verification gates, not metrics,
  confidence intervals, or production error bounds. When
  `max_bond=None`, the MPS manifest carries a complete no-explicit-truncation
  ledger with zero discarded weight. Finite `max_bond` routes supported
  two-site Hamiltonian/control unitaries through a Quimb-1.14-pinned auto-swap
  adapter and records every actual SVD split (forward swaps, operator split,
  and reverse swaps). Each discarded fraction is relative to that split's
  pre-split weight. Exact-branch aggregation weights each path-local sum by its
  incoming branch probability. Sampled aggregation sums per trajectory and
  divides by the declared `trajectory_count`, so trajectories with no
  truncation event contribute zero. Every gate occurrence separately authenticates
  complete sampled-trajectory coverage or contiguous exact branches with unit
  incoming mass; incomplete occurrence coverage makes both the ledger and restricted
  acceptance fail closed. These aggregates are local heuristic risk ledgers, not
  metrics or global state/record error bounds. Deterministic unitary
  evolution restores the pre-gate norm after recording raw loss; Kraus/jump
  branch operators remain uncapped because their raw norm is a physical branch
  probability, which is kept separate from truncation evidence. Capped
  multi-site MCWF clusters fail closed until they gain the same ledger. The
  ledger reports a conservative
  `exact_bond_dimension_sufficient=2**ceil(n_sites/2)` for qubit-MPS
  representability; being at/above that cap is exact-bond bookkeeping, not a
  production logical-error bound. Optional caller-declared
  `worst_cut_discarded_weight_gate` / `total_discarded_weight_gate` values are
  finite-bond candidate gates only. Once a capped run records actual loss, at
  both gates must be explicit and pass before restricted acceptance; a
  complete capped run with zero truncating operations is recorded as observed
  lossless and needs no loss gate. Passing these gates can accept restricted
  execution evidence, but never becomes a production trace-norm bound. The
  manifest centralizes these decisions in
  `restricted_acceptance_policy`: dense-window certification, sampled empirical
  trajectory status, over-cap dense-fallback refusal, and finite-bond risk-ledger
  status are policy gates, not scored metrics or production scalable completion.
  `axis1_qt_mps_bond_sweep_manifest(...)` runs the same compiler-generated
  schedule at multiple finite `max_bond` values and compares record probabilities
  against the largest-bond run as an internal convergence gate. For
  dense-checkable schedules, the largest-bond reference must also pass dense
  joint-L record certification before the sweep is accepted as restricted
  convergence evidence. The sweep is not a metric, not dense channel evidence,
  and not a production error bound.
- Axis-1 qutip-cuquantum symbolic lowering probe:
  `axis1_qutip_cuquantum_probe_manifest(...)` consumes the same carrier program
  with `backend_contract="qutip_cuquantum_probe"` and lowers Hamiltonian/collapse
  terms into qutip-cuquantum `CuOperator` summaries. It does not call
  `mesolve`/`mcsolve`, does not execute state or record evolution, and does not
  serialize dense operator/channel payloads. Its purpose is to pin backend
  lowering for over-cap rows before a real QT/MPS state/record carrier is
  attached.
- Axis-1 qutip-cuquantum execution probes:
  `axis1_qutip_cuquantum_state_probe_manifest(...)` is a restricted density
  `mesolve` state probe for carrier-program rows with no measurement boundary.
  It is intentionally behind an explicit slow-test gate and is not part of the
  regular release evidence path. `axis1_qutip_cuquantum_trajectory_probe_manifest(...)`
  is the faster restricted `mcsolve` trajectory probe for the same no-boundary
  slice. Both probes emit final Z-basis probability summaries only; neither
  emits measurement records, `.b8`, `.dem`, decoder output, dense channel
  payloads, or any production scalable-backend claim.
- Axis-1 qutip-cuquantum restricted record probe:
  `axis1_qutip_cuquantum_record_probe_manifest(...)` extends the trajectory
  probe through idle substeps, one-qubit frontend-control substeps, and one or
  more sequential Z measurement boundaries, including partial-register readout,
  with public detector / logical XOR wiring. It emits branch tables for that
  restricted trajectory endpoint, but still writes no `.b8`, no `.dem`, no
  decoder output, and no production scalable-backend claim.
- Axis-1 sampled record carriers:
  `write_axis1_measurement_record_samples(...)` samples the exact Axis-1 record
  distribution, including an explicitly supplied readout/reset instrument when
  present, with `torch.multinomial` on CUDA and writes
  `detection_events.b8`, `obs_flips_actual.b8`, the exact record evidence JSON,
  and `axis1_sample_summary.json`. It intentionally does not write `.stim`,
  `.dem`, or decoder outputs because the underlying joint-L records are not a
  Stim-Pauli/DEM model.
- Source adapters: `CircuitIRSource`, `StimCircuitSource`, and direct
  `CompiledCircuit` entry into `Simulator.run(...)`.
- `RecordSchema` and manifest guards for detector/observable bit widths,
  ideal/noisy schema equality, and evaluator-only sidecar visibility.
- Stim export/import helpers.
- Stim-compatible Pauli/depolarizing noise insertion through both the global
  gate-class `StimPauliNoiseSpec` and the location-aware `NoiseBuilder`.
  `NoiseBuilder` supports insertion after one gate occurrence, after a gate
  type, after all gates, before measurement types, and during scheduled idles at
  `TICK` boundaries.
- The default artifact bundle contains `.stim`, `.dem`, actual
  detector/observable `.b8`, sample-summary, theory-prediction, and a manifest.
  Only the actual detector/observable `.b8` (or its `RecordBatch` view) is the
  product record; the other files are circuit, reduction, summary, or provenance
  artifacts.
  `decoder=None` records prediction/decoder artifacts as deliberately omitted;
  `decoder="pymatching"` additionally writes predicted-observable `.b8` and a
  decoder-result artifact. The default `.dem` preserves non-graphlike hyperedges;
  graphlike decomposition is requested only by the explicit PyMatching path and
  is declared in the manifest.
- Axis-2 `SourceTimeline` sidecars can be attached to `Simulator.run(...)` as
  evaluator-only truth. The run writes exact replayable `source_timeline.npz`
  plus `source_timeline_binding.json`; the manifest declares whether the source
  cycle axis is bound to QEC rounds or only to an external acquisition cycle.
  These sidecars are not applied to Stim records or DEMs.
- `SourceStimPauliProjectionSpec` is the first executable source-conditioned
  frontend carrier. It projects a `SourceTimeline` into cycle-indexed
  Stim-Pauli probabilities such as `X_ERROR(p_t)`, `DEPOLARIZE1(p_t)`, or
  `DEPOLARIZE2(p_t)`, then writes normal `.stim`, `.dem`, and `.b8` artifacts.
  Projection cycles are bound to discrete `CircuitIR` `TICK` indices; cycle 0 is
  before the first `TICK`. The public noise manifest is a sanitized reduced
  summary. Payload keys, mapping parameters, per-event projected probabilities,
  and exact source arrays stay in evaluator-only sidecars. The manifest declares
  `representability="reduced_pauli_projection_not_analog_truth"`; this is useful
  for record-path plumbing and reduced comparators, not a claim of coherent
  joint-Lindbladian/leakage fidelity.
- Opt-in frozen evaluator-side decode through package-local `frontend.decoder`,
  selected with `decoder="pymatching"` and backed by the optional external
  PyMatching 2.4.0 wheel (`[hw]` extra); no decoder is bundled or required for
  record emission.
- CUDA-Q noiseless Grover adapter for non-Clifford algorithm circuits.
- Exact qutrit/ququart adapters for small multi-level leakage smoke runs:
  `simulate_qutrit_leakage(...)` (`|2>` single-site qutrit leakage) and
  `simulate_ququart_transport_smoke(...)` (`|3>`-faithful two-site CZ transport).
- Generic dense qutrit MCWF backend: `DenseQutritMcwfBackend` owns batched
  qutrit state trajectories, site matrices, multi-controlled computational
  phase gates, Kraus-branch sampling, and final qutrit/Born measurement.
  `CompiledMcwfProgram` is the generic op-stream contract between workload
  adapters and executors. `DenseQutritMcwfExecutor` is the full Python/Torch-GPU
  reference executor, while `NativeOpStreamMcwfExecutor` runs the cached hot
  subset (`H`, `X`, `phase=-1`, one Kraus family over selected sites) through a
  native CUDA op-stream runner. Its lowering exactly coalesces adjacent
  unique-site `X` gates into one qutrit-lifted permutation kernel; this is a
  launch-count optimization only and leaves leaked `|2>` levels inert.
  `GraphCapturedMcwfExecutor` is the default
  cached-subset executor: it CUDA-graph captures a fixed program/batch/Kraus
  shape and refreshes both random draws and same-shape Kraus values before each
  replay, so graph capture does not freeze stochastic branches or leakage
  parameters. `simulate_mcwf_qutrit_grover_leakage(...)` compiles Grover into
  that op stream; it is only the Grover workload adapter on top of the backend.
  The mainline is project-native finite-Kraus MCWF:
  fused CUDA kernels accelerate common 1/2/3-qubit gates, multi-controlled
  phase, one-site Kraus branch sampling, all-sites one-Kraus-family sampling,
  cached op-stream execution, and the experimental `BlockTrajectoryMcwfExecutor`
  when available; the Torch-GPU path remains the reference implementation.
  `BlockTrajectoryMcwfExecutor` maps one CUDA block to one full trajectory and
  is useful as a correctness-backed device-side experiment, but it is not the
  default 12-qutrit path because large dense statevectors need more grid
  parallelism. Programs containing arbitrary 1/2/3-qubit unitary ops currently
  use the dense executor until the native op-stream learns that table format.
- qutip-cuquantum adapter probes: local qutrit collapse operators are constructed
  as symbolic `CuOperator(..., mode=site, hilbert_dims=(3,)*n)` terms. This path
  is a safety/oracle integration seam for continuous `H + c_ops` MCWF, not the
  production 12-qutrit gate-level Grover carrier.
- d3 XZZX experiment presets (`experiments.py`): the product facade over the
  external Google `d3_at_q6_7` circuit inputs and the within-cycle leakage carriers.
  `load_xzzx_d3(...)` parses the r01 geometry (`verify=True`) and, by default,
  attaches the r10 interior within-cycle streams (the explicit
  r01-geometry + r10-streams provenance split). The dataset root resolves as
  `dataset_root` argument > `ECS_D3_DATA_ROOT` env var > the external user-data default; a
  missing root or file raises `FileNotFoundError` naming the path — never a
  silent fallback to the default root. `ExperimentPreset` is a frozen,
  registered configuration (a *preset*) with NO silent physics defaults; the
  two theta conventions are DISTINCT registered presets:
  `PRESET_LEAK_THETA_0P30` (raw angle, `theta_rad=0.30`) and
  `PRESET_LEAKAGE_RATE_5E3` (`theta` solved to `leakage_rate = 5e-3` via
  `solve_exchange_angle_for_leakage_rate`). `run_spec_from_preset(...)` builds the engine
  `RunSpec` with explicit `n_shots`/`n_rounds`/`seed`, and
  `leak_slice_table(...)` returns the per-CZ `exp(L/4)` Kraus table through
  package-local `WithinCycleScheduleHost.build_within_cycle_leak` (its embedded CPTP `< 1e-12` and
  composition `< 1e-12` preconditions stay asserted inside the facade path).

Representability boundary:

- `representability="stim_pauli"` means Clifford/stabilizer circuit artifacts
  plus Stim-representable Pauli noise only.
- `noise["type"]="stim_pauli_source_projection"` means source-conditioned
  probabilities were actually inserted into the noisy Stim circuit and can
  change `.dem` / `.b8` outputs. It is still a reduced Pauli projection; exact
  source payloads and per-event projected probabilities remain evaluator-only
  sidecars. Site-indexed source payloads are split into per-target one-qubit
  noise instructions, or per-pair `DEPOLARIZE2` instructions for two-qubit
  depolarization, so bundled operations do not silently average away a local
  footprint.
- `.stim` and `.dem` are not analog joint-Lindbladian truth, leakage truth, or
  shared-source non-Markovian truth.
- Zero-width detector/observable classes are omitted in the manifest instead of
  written as unreadable 0-byte `.b8` files.
- The current XZZX constructor is a DEM-compatible compiler/schedule smoke: it
  exercises mixed-basis checks, repeated syndrome deltas, final data closure
  detectors, and one deterministic non-stabilizer-span observable. It is not a
  certified distance-3 memory, hardware schedule, or analog coupling process.
- The current compiler schedule requires one compatible final measurement basis
  per data qubit for closure/readout. More general stabilizer-code closure
  strategies are future compiler work.
- Record-layout helpers are frontend artifact facts. They do not import or
  imply the Axis-1/Axis-2 coupled error model.
- `representability="analog_schedule_metadata_only"` means a compiler-generated
  schedule seam for later Axis-1 lowering. It is not an analog simulator result.
  Pre-noised Stim/Pauli/source-projected circuits are rejected by the schedule
  extractor because source projection and Pauli insertion are not joint-L
  dynamics. Read-only imported Stim circuits are accepted only when their
  instructions can be represented as public schedule/record metadata; embedded
  Stim noise is rejected. Public `noise_projection` metadata is a manifest fact,
  not an authorization token for raw source-embedded noise gates; simulator noise
  passes attach noise instructions through the internal noise-projection path.
- `joint_channel_comparison_gate(...)` remains limited to the registered two-row
  joint-vs-composed comparison
  slice. Its `Axis1MechanismSelectionPlan` is schedule-derived metadata only:
  active CZ operations supply the exact-zero diagnostic row, persistent
  static-ZZ couplings come only from public `axis1_static_zz_couplings`
  schedule metadata, drive gates with idle spectators select contextual DR rows
  only when that static metadata is present, and primitive Hamiltonian/collapse
  payloads are introduced only after selection by
  `error_coupling_simulator.mechanisms.axis1_primitives`. It refuses oracle schedules, requires
  a valid compiler-owned schedule seal plus compiler-generated substeps, and
  never consumes `SourceTimeline` or source-projection sidecars.
- `joint_channel_comparison.json` is an evidence artifact, not a simulator run artifact. It
  must not create `.stim`, `.dem`, `.b8`, decoder, source, or leakage files.
- `joint_channel_comparison.freeze.json` is a hash guard for that evidence artifact. It does
  not certify a full analog simulator run; it only detects drift in the frozen
  frontend joint-channel comparison file. A normal runner invocation does not bless drift by
  overwriting an existing freeze.
- `representability="axis1_joint_channel_evidence_no_record_emission"` means the
  Axis-1 bridge assembled joint-channel carriers from schedule-derived
  selections. It is not analog record emission, not a decoder artifact, and not
  a public channel payload dump. Generic frontend `CTRL_*` controls and
  selected local primitive mechanisms enter the same joint generator before
  exponentiation. Its freeze file guards only this evidence artifact identity.
- `representability="axis1_scalable_carrier_program_metadata_no_channel_payload"`
  means `axis1_carrier_program_manifest(...)` emitted a program/provenance IR
  for a future GPU state/record carrier. Within the dense support cap, rows are
  marked `dense_oracle_available` and remain checked by the dense
  `joint_lindbladian` channel-evidence path. Over the cap, public static-ZZ
  union-support substeps are marked `scalable_required` with every declared edge,
  calibration source, local Markovian term family, public local Lindblad context
  term such as thermal excitation, frontend ideal-control Hamiltonian where the
  over-cap substep is a supported gate row, measurement boundary, and the
  structured approximation book required by the future trajectory/MPS production
  backend. This is not an executed MPS/trajectory backend, not dense Choi/Kraus
  evidence, not `.dem` semantics, and not Axis-2 source truth.
- `representability="axis1_qt_mps_state_record_contract_no_backend_execution"`
  means the future `qt_mps_state_record` backend contract was checked against
  the carrier program and approximation book. Dense-checkable schedules are
  certified through the existing dense joint-L execution seam; over-cap
  `scalable_required` rows fail closed until the actual GPU trajectory/MPS
  backend exists. It is not MPS execution, not `.dem`, and not decoder
  integration.
- `representability="axis1_mcwf_mps_state_record_contract_no_backend_execution"`
  means the future `mcwf_mps_state_record` backend contract was checked against
  the carrier program and approximation book. It declares MCWF trajectory
  semantics over a per-site MPS pure-state carrier and carries public
  `local_dims` for qubit/qutrit/ququart or mixed-dimension runs. It is not
  trajectory execution, not restricted QT/MPS product-channel execution, not
  dense channel evidence, not `.dem`, and not decoder integration.
- `representability="axis1_carrier_execution_mcwf_mps_fixed_microstep_or_fail_closed"`
  is the carrier-execution wrapper class for `mcwf_mps_state_record`. In the
  first slice it delegates to fixed-microstep MCWF/MPS execution when
  supported, and otherwise fails closed after returning the MCWF/MPS contract
  surface. It performs no dense, qutip-cuquantum, or restricted QT/MPS fallback.
- `representability="axis1_mcwf_mps_fixed_microstep_local_dims_state_record"` means
  `axis1_mcwf_mps_state_record_execution_manifest(...)` executed sampled
  fixed-microstep MCWF trajectories on a local-dimension MPS carrier. Execution
  completion is distinct from certification: diagnostic-only and oracle-unavailable
  runs retain their state/Record payload but have verdict `fail`. Runtime MCWF
  candidate-mass residual and empirical Record-frequency normalization are separate
  fields and neither substitutes for the other. It is state/record execution evidence
  only: not exact joint-L channel evidence, not
  exact continuous-time leakage-channel evidence, not `.dem`, not decoder
  integration, and not production scalable completion.
- `representability="axis1_one_site_qutrit_leakage_dense_oracle_certification_no_payload"`
  means `axis1_qutrit_leakage_oracle_certification_manifest(...)` compared the
  compiler-carrier `LEAK_*` one-site qutrit generator against
  `leakage_channel_super` after explicit per-ns-to-dimensionless `dt`
  conversion. It is a verification gate only: not a metric, not a channel
  payload, not DEM/decoder integration, and not production scalable completion.
- `representability="axis1_two_site_leakage_hamiltonian_dense_oracle_certification_no_payload"`
  means `axis1_two_site_leakage_hamiltonian_certification_manifest(...)`
  compared the MCWF/MPS same-support two-site Hamiltonian group against an
  independently constructed dense matrix exponential over declared qutrit or
  ququart `local_dims`. It certifies first-slice transport and conditional phase
  Hamiltonian lowering only: not a metric, not dense channel evidence, not a
  channel payload, not DEM/decoder integration, and not production scalable
  completion.
- `representability="axis1_qt_mps_restricted_control_hamiltonian_z_record_product_channel"`
  means a quimb/torch-CUDA MPS execution adapter consumed the carrier program for
  the restricted Hamiltonian/control / local-collapse-product-channel /
  Z-record slice.
  It is MPS execution, but not the full production QT/MPS carrier: exact
  summed-generator Lindblad evolution, dense channel evidence, DEM/decoder
  integration, and Axis-2 source timelines are not claimed. Its finite-bond
  ledger records per-operation actual Quimb SVD splits. Exact branches use
  incoming-branch-probability weighting, while sampled runs average over the
  explicit trajectory count including zero-event paths. The result remains a
  local heuristic risk ledger, not a metric, a global error bound, or a branch
  probability; sampled trajectory mode emits empirical record frequencies, not
  dense-certified exact probabilities.
- `representability="axis1_qt_mps_restricted_seeded_trajectory_sweep"` means a
  restricted QT/MPS sampled-trajectory seed sweep ran the same compiler-generated
  schedule with explicit distinct seeds. It may accept restricted empirical
  seed-sweep evidence and, separately, dense-calibrated trajectory evidence for
  dense-checkable schedules. It is not a metric, not a confidence interval, not
  exact dense channel evidence, and not a production scalable backend.
- `representability="axis1_qt_mps_restricted_bond_and_seed_sweep_bundle"` means a
  reviewer-facing restricted QT/MPS evidence bundle combined finite-bond
  convergence evidence and sampled-trajectory seed-sweep evidence for the same
  compiler-generated schedule. The bundle separates restricted evidence from
  dense-calibrated evidence and still claims no production error bound, no metric,
  and no production scalable backend.
- `representability="axis1_qt_mps_resource_probe_actual_execution_no_padding"`
  means a restricted QT/MPS evidence bundle was executed while recording actual
  `torch.cuda` peak allocated/reserved memory. The probe never pads tensors to
  hit a memory target: an unreached 30 GiB-style gate fails as a resource smoke
  gate. It is not a scientific metric and not production scalable evidence.
- `representability="axis1_carrier_execution_qt_mps_restricted_no_production_scalable"`
  means `axis1_carrier_execution_manifest(...)` executed the explicit
  `qt_mps_state_record` backend contract by delegating to the restricted
  quimb/torch-CUDA QT/MPS manifest. It is carrier-seam state/record evidence for
  the supported restricted slice, not exact joint-L channel evidence, not `.dem`,
  not decoder integration, and not a production scalable backend.
- `representability="axis1_carrier_execution_qutip_cuquantum_restricted_no_production_scalable"`
  means `axis1_carrier_execution_manifest(...)` executed the explicit
  `qutip_cuquantum_restricted_state_record_probe` backend contract. It consumes
  the carrier program and delegates to the restricted qutip-cuquantum trajectory
  or record probe; it is executable over-cap state/record evidence for the
  supported slice, not QT/MPS backend execution, not dense channel evidence, not
  `.dem`, not decoder integration, and not a production scalable backend.
- `representability="axis1_qutip_cuquantum_symbolic_lowering_probe_no_state_record_execution"`
  means `axis1_qutip_cuquantum_probe_manifest(...)` lowered carrier-program
  terms into symbolic qutip-cuquantum `CuOperator` summaries. It is a backend
  lowering probe only: no solver call, no state/record execution, no dense
  channel evidence, no `.dem`, and no Axis-2 source timeline.
- `representability="axis1_qutip_cuquantum_state_probe_restricted_no_record_execution"`
  means qutip-cuquantum `mesolve` was used as a restricted density state probe
  for carrier-program rows with no measurement boundary. It is a slow explicit
  gate, not a production carrier and not dense channel evidence.
- `representability="axis1_qutip_cuquantum_trajectory_probe_no_record_execution"`
  means qutip-cuquantum `mcsolve` was used as a restricted single-trajectory
  probe for carrier-program rows with no measurement boundary. It is a candidate
  seam toward a future trajectory/MPS carrier, not record emission and not a
  production scalable backend.
- `representability="axis1_qutip_cuquantum_record_probe_restricted_no_b8_no_decoder"`
  means qutip-cuquantum `mcsolve` was followed by restricted Z-basis branch
  enumeration for idle / one-qubit-control / measurement carrier-program rows,
  including partial-register readout and public XOR record projection. It is not
  `.b8` artifact emission, not DEM, not decoder integration, and not a
  production scalable backend.
- `representability="axis1_selected_joint_channel_state_evidence_no_record_emission"`
  means selected local or union-support joint channels were applied to a small-N
  density matrix, but no measurements or records were emitted.
- `representability="axis1_selected_joint_channel_record_evidence_no_b8_or_decoder"`
  means selected local or union-support joint channels plus Pauli-basis
  measurement branch enumeration produced measurement, detector, and
  logical-observable JSON records when the schedule carries public XOR wiring.
  It is not `.b8`, a decoder artifact, or full-schedule operation semantics.
- `axis1_measurement_records.freeze.json` is a hash guard for Axis-1 record
  evidence. The CodeSpec runner uses it to freeze the compiler-generated mixed
  X/Z record fixture; it does not certify `.dem`/decoder integration or Axis-2.
- `representability="axis1_jointL_record_samples_b8_no_dem_no_decoder"` means
  `.b8` detector/logical sample carriers were sampled from the exact Axis-1
  record distribution. It is still not a `.dem`, not decoder integration, and
  not a Stim-Pauli model.
- `representability="axis1_jointL_source_coupled_record_samples_evaluator_truth"`
  is the `noise_processes.coupled_cycle.CoupledCycleNoiseProcess` emit class: R-round
  `{det,obs}` records sampled from the exact Axis-1 record distribution under a
  shared memory-ful source (`OneOverFDriftSource`/`RTNSource`) fanned out per QEC
  cycle into per-round `Axis1PrimitiveParams` via the injected
  `params_for_substep` callback. The source trajectory, `Theta(z_t)` params, and
  per-substep channel field are evaluator-only truth (reachable via `.truth` /
  `CertReport.truth`, never in the emitted payload). It is still not a `.dem`,
  not decoder integration, and not a Stim-Pauli model; the non-Markovian content
  is classical parameter memory under the
  [current memory claim classes](../../../CONTEXT.md#memory-claim-classes), not a
  CP-divisibility-breaking quantum-memory claim.
- Future analog/source/leakage backends must attach evaluator-only truth
  sidecars and declare a distinct representability class in the manifest.
- `source_binding` in the frontend manifest is an evaluator-side alignment
  contract. If a `CodeSpec`-compiled circuit is used, the default binding is
  `cycle_binding="qec_round"` and `SourceTimeline.n_cycles` must match the
  compiled code rounds. Hand-built/Stim sources default to
  `cycle_binding="external_cycle"`. This is replay/faithfulness infrastructure,
  not backend lowering. `SourceStimPauliProjectionSpec` is the exception: because
  it actually lowers a reduced source projection into Stim records, it requires
  `cycle_binding="circuit_tick"` and writes the projection audit into
  `source_timeline_binding.json`.
- `representability="cudaq_statevector_noiseless"` is for noiseless algorithm
  circuits such as Grover. It writes state/count artifacts, not `.stim`, `.dem`,
  detector records, or decoder results.
- `representability="exact_qutrit_density_matrix_leakage"` is the in-house
  `QutritDM` carrier on `{|0>,|1>,|2>}`. It writes qutrit density/probability
  artifacts, not decoder records.
- `representability="exact_ququart_density_matrix_transport"` is the in-house
  `QuquartDM` carrier on `{|0>,|1>,|2>,|3>}` using the QuTiP-derived two-site
  CZ transport Kraus. It is resource-capped small-register evidence, not a full
  9-data-register production path.
- Scaling leakage beyond exact density matrices routes to the package-local MCWF/MPS
  carrier surfaces. MCWF is a sampling carrier, not the
  non-Markovian claim: Axis-2 non-Markovianity still requires an explicit shared
  source history `z_t` that conditions many mechanism parameters across cycles.
- `representability="dense_qutrit_statevector_mcwf_leakage"` is a trajectory
  carrier/backend class. It outputs final measured bit counts plus raw qutrit
  outcome counts and leakage summaries; it is not a `.stim/.dem/.b8` decoder path.
  Workload adapters such as Grover must call `DenseQutritMcwfBackend` rather than
  implementing trajectory sampling themselves. The Grover adapter uses the
  standard gate-level sequence `X`-mask -> multi-controlled phase -> unmask for
  the oracle, and `H/X/multi-controlled-phase/X/H` for the diffuser; it must not
  shortcut by directly flipping the marked basis amplitude.
- qutip-cuquantum `mcsolve` consumes continuous-time Hamiltonian/collapse
  operators. It is not a drop-in finite-Kraus branch sampler and is not currently
  registered as the 12-qutrit Grover carrier. The safe adapter intentionally
  refuses 12-qutrit `mcsolve` production runs; 12q Grover+leakage routes through
  `DenseQutritMcwfBackend`. Do not build 12q local collapse operators via
  `qutip.tensor([...])`: that expands a full `3**12 x 3**12` operator. Use the
  local symbolic `CuOperator` factory instead.

Design target:

`CodeSpec -> CircuitIR`, imported Stim circuits, and hand-built `CircuitIR` all
feed the same `Simulator.run(...)` artifact surface. XZZX is the first target
code spec, not a hard-coded simulator core.

Noiseless quickstart:

```python
from error_coupling_simulator.frontend import (
    XZZXCodeSpec,
    compile_code_spec,
    simulate_noiseless,
)

spec = XZZXCodeSpec(layout_size=3, rounds=2).to_code_spec()
circuit = compile_code_spec(spec)
result = simulate_noiseless(
    circuit,
    shots=1024,
    out_dir="outputs/simulator/noiseless_xzzx",
    seed=0,
)

detections = result.load_detection_events()
observables = result.load_observable_flips()
print(result.paths.manifest)
print(detections.shape, observables.shape)
```

This writes the same standard artifact set as noisy runs, with
`manifest["noise"] is None`. The default is record-only (`decoder=None`) and
does not require PyMatching; pass `decoder="pymatching"` explicitly to add
prediction and decoder-summary artifacts. The noisy/ideal Stim artifacts must
be identical in this mode; `run_noiseless(...)` rejects pre-noised `StimCircuitSource` or
`CompiledCircuit` inputs whose ideal/noisy circuit pair already differs. Use
`Simulator(source).run(noise=None, ...)` when the source itself intentionally
carries a pre-noised circuit pair. Future coupled-error backends attach below
the same product surface.

Hand-built circuit + targeted noise quickstart:

```python
from error_coupling_simulator.frontend import CircuitBuilder, Noise, Simulator

builder = CircuitBuilder(num_qubits=3)
builder.h(0)
builder.cz((0, 1))
builder.tick()
builder.x(2)
builder.idle(1)
builder.tick()
builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
builder.detector("d0", xor=("m0",))
builder.observable("logical0", xor=("m0",), index=0)
circuit = builder.build()

noise = (
    Noise.targeted()
    .after_gate(0, "X_ERROR", 0.001)           # first user gate occurrence
    .after_gate_type("CZ", "DEPOLARIZE", 0.01) # auto -> DEPOLARIZE2
    .after_all_gates("Z_ERROR", 0.0005)
    .during_idle("DEPOLARIZE", 0.002)          # auto idle qubits at TICK
    .before_measurement("X_ERROR", 0.01)
    .build()
)

result = Simulator(circuit).run(
    shots=1024,
    noise=noise,
    out_dir="outputs/simulator/targeted_noise",
    seed=7,
)
print(result.manifest["noise"]["matched_counts"])
print(result.paths.circuit_noisy_pauli)
```

This path writes `.stim`, `.dem`, actual `.b8` records, summaries, and a
manifest. Decoder output is opt-in via `decoder="pymatching"`; the default run
does not import or call PyMatching. `error_coupling_simulator.frontend.noise` is
intentionally limited to Stim-representable Pauli noise.
Gate and measurement `target_filter` arguments are exact instruction-target
tuple filters; they never override where the inserted noise lands. To address
one pair/qubit inside a bundled instruction, split that source instruction
first. Idle noise is inserted only at explicit `TICK` boundaries, so a terminal
idle interval needs a trailing `builder.tick()`.
Leakage, analog joint-L coupling, and shared-source non-Markovian noise attach
through backend-specific truth sidecars / carriers, not by laundering them into
this Pauli insertion layer.

d3 XZZX experiment-preset quickstart:

```python
from pathlib import Path

from error_coupling_simulator.frontend.experiments import (
    PRESET_LEAKAGE_RATE_5E3,
    leak_slice_table,
    load_xzzx_d3,
    run_spec_from_preset,
)
from error_coupling_simulator.carrier import FusedWithinCycleSampler

# External input: r01 geometry + r10 interior streams. These files are not in the wheel.
google_root = Path("/path/to/google_qec_data")
sched = load_xzzx_d3(dataset_root=google_root)
screening_spec = run_spec_from_preset(
    PRESET_LEAKAGE_RATE_5E3,
    n_shots=1024,
    n_rounds=2,
    seed=0,
    run_purpose="optimization",  # c64; fused within-cycle SV-MC only; screening_only
    dataset_root=google_root,
)
final_spec = run_spec_from_preset(
    PRESET_LEAKAGE_RATE_5E3,
    n_shots=1024,
    n_rounds=2,
    seed=0,
    run_purpose="final",         # c128; c128_candidate, not an automatic pass
    dataset_root=google_root,
)
leak_c128 = leak_slice_table(
    PRESET_LEAKAGE_RATE_5E3, device="cuda")  # c128 construction + CPTP check

sampler = FusedWithinCycleSampler("cuda")
screening_batch = sampler.sample(screening_spec, schedule=sched)  # executes c64
# After freezing the chosen point, replay separately; do not promote screening_batch.
final_batch = sampler.sample(final_spec, schedule=sched)            # executes c128
```

Only `FusedWithinCycleSampler` / `sv_traj_d3_wc` may execute `screening_spec` in c64.
PEPS and MPS remain c128-only and reject c64 run metadata. The declared qutrit leakage channel, codestate,
composition checks, and CPTP checks remain c128; the fused sampler casts only the checked complex
execution tables for optimization. A c64 artifact never becomes evidence: replay the frozen run
as a separate c128 final/certification candidate and then apply the owning scientific gates.
Presets are frozen registered configurations — new knob combinations are new named presets,
never edits of an existing one. This precision policy does not change tolerance or FET settings.

CUDA-Q Grover quickstart:

```python
from error_coupling_simulator.frontend import simulate_cudaq_grover_noiseless

result = simulate_cudaq_grover_noiseless(
    num_qubits=12,
    marked_state="111111111111",
    shots=1024,
    seed=42,
    out_dir="outputs/simulator/grover12_cudaq_noiseless",
)

print(result.iterations)
print(result.marked_probability)
print(result.marked_counts, "/", result.shots)
print(result.top_outcomes(3))
```

Run this adapter only in the dedicated `aiqec` CUDA-Q plugin environment and a
separate process; do not install or execute it beside the fused extension in
canonical `ecs`. It uses CUDA-Q's current target (on this workstation:
NVIDIA/cuStateVec when available). It writes `statevector.npy`, `probabilities.npy`,
`measurement_counts.json`, `theory_prediction.json`, and `manifest.json`.

Multi-level leakage quickstarts:

```python
from error_coupling_simulator.frontend import (
    simulate_qutrit_leakage,
    simulate_ququart_transport_smoke,
)
from error_coupling_simulator.mechanisms import CZParams

q2 = simulate_qutrit_leakage(
    num_qutrits=3,
    initial_levels="111",
    cycles=1,
    shots=1024,
    out_dir="outputs/simulator/qutrit_leakage3",
)
print(q2.total_leaked_population)
print(q2.top_outcomes(4))

q3 = simulate_ququart_transport_smoke(
    num_ququarts=2,
    initial_levels="12",
    shots=1024,
    cz_params=CZParams(),
    out_dir="outputs/simulator/ququart_transport2",
)
print(q3.outcome_probability("30"))
print(q3.top_outcomes(4))
```

Both paths use project-owned carriers under `carrier/exact`; both write
multi-level probability/count artifacts and a manifest, not `.stim`, `.dem`,
`.b8`, or decoder results. The CZ constructor is package-owned and QuTiP/CPU;
the resulting Kraus representation is consumed by `QuquartDM`. A supplied NPZ
is an optional derived cache or caller injection; there is no fallback to
repository `outputs/`.

MCWF backend + Grover leakage workload quickstart:

```python
from error_coupling_simulator.frontend import simulate_mcwf_qutrit_grover_leakage

result = simulate_mcwf_qutrit_grover_leakage(
    num_qubits=12,
    marked_state="111111111111",
    shots=16,
    seed=123,
    batch_size=2,
    use_fused_kernels=True,
    out_dir="outputs/simulator/grover12_mcwf_leakage",
)

print(result.iterations)
print(result.mean_pre_readout_marked_probability)
print(result.marked_fraction)
print(result.mean_final_leaked_sites)
print(result.top_outcomes(4))
print(result.top_qutrit_outcomes(4))
```

This writes `measurement_counts.json`, `qutrit_outcome_counts.json`,
`leakage_by_site.json`, `trajectory_summary.json`, `theory_prediction.json`, and
`manifest.json`. The measurement is trajectory/Born sampled from the final
qutrit state; final `|2>` levels are also reported before being mapped through
the leaked-readout bias into binary counts. The manifest declares
`algorithm="single_solution_grover_gate_level"` and records the oracle/diffuser
realization.

The reusable backend can also be used directly by future circuit/schedule
adapters, or through the generic compiled-program surface:

```python
from error_coupling_simulator.frontend import CompiledMcwfProgram
from error_coupling_simulator.frontend.mcwf_program import h, kraus_all_sites

program = CompiledMcwfProgram(
    num_qutrits=3,
    operations=(
        h(0),
        h(1),
        h(2),
        kraus_all_sites("qutrit_leakage", range(3)),
    ),
)
print(program.summary())
```

The lower-level backend remains available for oracle-style tests:

```python
import torch

from error_coupling_simulator.frontend import DenseQutritMcwfBackend
from error_coupling_simulator.frontend.mcwf_backend import CDTYPE

backend = DenseQutritMcwfBackend(num_qutrits=2, seed=7)
psi = backend.basis_state(batch_size=32, initial_levels="11")
swap_12 = torch.zeros((3, 3), dtype=CDTYPE, device=backend.device)
swap_12[0, 0] = 1
swap_12[1, 2] = 1
swap_12[2, 1] = 1
psi = backend.apply_kraus_all_sites(psi, swap_12.unsqueeze(0))
measurement = backend.sample_measurements(psi, leaked_readout_b=1.0)
print(measurement.qutrit_counts)
```

qutip-cuquantum local-operator safety probe:

```python
from error_coupling_simulator.frontend import qutip_cuquantum_symbolic_collapse_summary

summary = qutip_cuquantum_symbolic_collapse_summary(num_qutrits=12, site=0)
assert summary.collapse_data_type == "CuOperator"
assert summary.cdc_data_type == "CuOperator"
```

The corresponding `mcsolve` smoke is deliberately capped to small registers:

```python
from error_coupling_simulator.frontend import probe_qutip_cuquantum_local_mcwf

probe = probe_qutip_cuquantum_local_mcwf(num_qutrits=2, ntraj=1)
print(probe.method, probe.end_condition)
```

# Axis-1 Completion Review

Date: 2026-06-28

This is a review checkpoint for the Axis-1 compiler/schedule/joint-L bridge. It
is not a declaration that the full coupled QEC teacher is complete.

## Current Evidence

- `SubstepSchedule` / `AnalogSubstepIR` now carries compiler-derived public
  schedule metadata, duration brackets, static-ZZ metadata, and optional public
  local Lindblad context. It is not an analog simulator result. (a/c)
- Generic Axis-1 channel/state/record evidence lowers supported frontend
  controls and local primitives into one `assemble_substep_channel(...)` call per
  selected local or union-support window. This is the Axis-1 joint-generator
  semantics; it is not sequential `E1 o E2`. (a)
- Supported one-qubit controls are
  `C_XYZ/C_ZYX/H/H_XY/H_XZ/S/S_DAG/SQRT_X/SQRT_X_DAG/SQRT_Y/SQRT_Y_DAG/SQRT_Z/SQRT_Z_DAG/X/Y/Z`.
  Supported two-qubit controls are
  `CX/CY/CZ/ISWAP/ISWAP_DAG/SQRT_XX/SQRT_XX_DAG/SQRT_YY/SQRT_YY_DAG/SQRT_ZZ/SQRT_ZZ_DAG/SWAP/XCX/XCY/XCZ/YCX/YCY/YCZ`.
  (a/c)
- Public `Axis1LocalLindbladContextSpec` can select computational-subspace
  finite-temperature excitation (`T1_UP/T1_UP_B`), request active-pair
  computational-subspace fSim residual Hamiltonian primitives
  (`FSIM_SWAP/FSIM_PHASE`), request first-slice one-site qutrit leakage
  families (`LEAK_EXCHANGE_12`, `LEAK_SEEP_21`, `LEAK_HEAT_12`) for carrier
  execution, and override local rates. It is not Axis-2 source truth and not a
  serialized channel payload. (a/c)
- Public static-ZZ calibration metadata can now carry optional per-edge
  `zeta_rad_per_ns` values through `CircuitIR`, `CodeSpec`, and Stim sidecar
  schedule extraction. Channel/state/record evidence lowers calibrated edges
  with edge-specific coefficients while uncalibrated schedules still fall back
  to the global `Axis1PrimitiveParams.zeta_rad_per_ns`. This is public
  calibration metadata, not Axis-2 source truth and not hidden teacher truth.
  (a/c)
- `Axis1CarrierProgram` and `axis1_carrier_execution_manifest(...)` now provide
  a program/execution seam. The execution contract is `dense_jointL_probe`: it
  consumes the carrier program and executes only dense-checkable routes through
  existing GPU joint-L state/record evidence. Programs containing
  `scalable_required` rows fail closed with an explicit backend-extension
  blocker. This is not a QT/MPS backend and not a scalable-over-cap completion
  claim. (a/c)
- The same execution seam also exposes an explicit
  `qt_mps_state_record` contract for the restricted quimb/torch-CUDA MPS backend.
  It delegates to `axis1_qt_mps_restricted_execution_manifest(...)`, embeds the
  restricted acceptance policy, and keeps
  `claims_production_scalable_backend=false`. This is restricted carrier-seam
  execution, not production QT/MPS completion. (a/c)
- The same execution seam also exposes an explicit
  `qutip_cuquantum_restricted_state_record_probe` contract for supported
  over-cap rows. It executes through the restricted qutip-cuquantum trajectory
  or record probes and keeps `claims_qt_mps_backend_execution=false` and
  `claims_production_scalable_backend=false`. This is executable over-cap probe
  evidence, not production QT/MPS completion. (a/c)
- `axis1_qt_mps_restricted_execution_manifest(...)` is the first executable
  quimb/torch-CUDA MPS slice behind `qt_mps_state_record`. It supports
  Hamiltonian/control terms, including supported compiler two-qubit frontend
  controls, local product-channel collapse branches for `T1/T1_UP/T2/RD`, and
  Z-record execution. It is MPS execution, but not exact summed-generator
  Lindblad evolution and not production scalable completion. (a/c)
- `DenseQuditMcwfBackend` now exists as a GPU-only dense MCWF correctness core
  with per-site `local_dims`, covering qubit, qutrit, ququart, and mixed local
  Hilbert dimensions at the carrier-operation level. It is not yet wired as the
  production Axis-1 schedule executor. (a/c)
- `axis1_mcwf_mps_state_record_contract_manifest(...)` exposes the
  `mcwf_mps_state_record` contract surface. It records the intended architecture
  split: MCWF owns same-substep trajectory semantics for the summed
  `H_list`/`c_list`, while MPS owns the pure-state carrier representation and
  `local_dims` owns qubit/qutrit/ququart dimensionality. (a/c)
- `axis1_mcwf_mps_state_record_execution_manifest(...)` now executes the first
  fixed-microstep MCWF/MPS slice over declared `local_dims`. It samples
  quantum-jump trajectories on a quimb/torch-CUDA MPS carrier, with at most one
  collapse jump per microstep chosen from the same substep collapse list.
  Qutrit/ququart local dimensions are represented at the carrier level for the
  existing computational-subspace families, the measurement policy, and the
  first registered one-site qutrit leakage families. It is not sequential
  finite-channel composition, not exact dense joint-L channel evidence, and not
  production scalable completion. Multilevel finite-bond
  requests fail closed with
  `blocked_reason="mcwf_mps_multilevel_finite_bond_ledger_not_implemented"`.
  (a/c)
- The MCWF/MPS record path now accumulates measurement keys across multiple
  measurement substeps and supports multilevel `MR*` reset by mapping the sampled
  measured level to the requested computational reset state. This is still a
  local record-boundary execution surface, not `.b8/.dem` decoder integration.
  (a/c)
- Dense computational-subspace channel/state/record evidence now refuses public
  qutrit leakage context instead of silently ignoring it. The accepted first
  leakage route is `mcwf_mps_state_record` with declared multilevel
  `local_dims`. A separate one-site dense qutrit certification manifest now
  compares carrier `LEAK_*` lowering against `leakage_channel_super` after
  explicit `dt` conversion; it is a verification gate, not a default dense
  evidence route and not a metric. (a/c)
- Dense-checkable restricted MPS record schedules now carry an exact dense
  joint-L record certification against `axis1_measurement_record_evidence_manifest(...)`.
  The comparison is a verification gate, not a metric, and over-cap rows still
  do not use dense certification as a fallback. The MPS manifest also carries a
  complete no-explicit-truncation ledger when `max_bond=None`; finite `max_bond`
  runs carry a CUDA shadow-state Schmidt-tail ledger for supported two-site
  Hamiltonian/control gates. This is still a restricted risk ledger, not a
  production error bound. Optional caller-declared discarded-weight gates can now
  accept/reject finite-bond candidate evidence, but still keep
  `accepted_as_production_error_bound=false`. The ledger also marks whether a
  finite `max_bond` is at/above the conservative exact-bond sufficient cap for
  the qubit MPS; this is exact representability bookkeeping, not production
  error control. (a/c)
- Restricted MPS bond sweeps now run the same compiler-generated schedule at
  multiple finite `max_bond` values and compare record probabilities against the
  largest-bond run as a convergence gate. For dense-checkable record schedules,
  the largest-bond reference must also pass dense joint-L record certification
  before the sweep is accepted as restricted convergence evidence. This catches
  under-bonding in the Bell/CZ fixture and rejects self-consistent but
  finite-step-wrong noncommuting references, but remains a gate rather than a
  metric or production error bound. (a/c)
- Restricted MPS sampled trajectories now use an explicit `trajectory_count` /
  `rng_seed` contract with `torch.Generator(cuda)`. Sampled record frequencies
  skip exact dense-probability certification and are not metrics. The restricted
  acceptance policy accepts sampled execution evidence only when the seed was
  explicitly supplied; default seed zero is execution provenance, not acceptance.
  (a/c)
- Restricted MPS seed sweeps now run sampled trajectories across explicit
  distinct seeds and expose separate flags for restricted empirical seed-sweep
  evidence and dense-calibrated trajectory evidence. The sweep gates are
  verification gates, not metrics, not confidence intervals, and not production
  error bounds. (a/c)
- Restricted MPS evidence bundles now aggregate finite-bond convergence and
  trajectory seed-sweep gates for the same compiler-generated schedule. The
  bundle is a review surface with separate restricted and dense-calibrated flags;
  it remains non-production and introduces no metric. (a/c)
- Restricted MPS resource probes now wrap the bundle with actual `torch.cuda`
  peak allocated/reserved memory reporting. They do not pad memory to satisfy a
  target; unreached heavy targets fail as resource gates. This explains why the
  current small correctness batches can occupy only a few GiB without pretending
  to be 30 GiB production workloads. (c)
- Restricted MPS finite-step execution now exposes
  `microstep_count` and `finite_step_order`. `first_order` uses
  `operator_family_product_formula_v1`; `strang_second_order` uses
  `strang_hamiltonian_collapse_product_formula_v1`. A within-cap noncommuting
  `H + T1` gate shows reduced dense-record difference when the split is refined,
  while still keeping no exact-generator claim. (a/c)
- Restricted MPS execution now emits `restricted_acceptance_policy`, centralizing
  finite-step, dense-window, sampled-trajectory, over-cap dense-fallback, and
  finite-bond risk-ledger decisions. The block can accept restricted execution
  evidence or explicitly seeded sampled execution evidence, and the manifest's
  top-level `passed` / `verdict` now follows that acceptance policy rather than
  mere backend execution. It still reports
  `accepted_for_production_scalable_backend=false` and introduces no metric. (a/c)
- `axis1_qutip_cuquantum_probe_manifest(...)` now lowers carrier-program
  Hamiltonian/collapse terms into symbolic qutip-cuquantum `CuOperator`
  summaries. This is a backend-lowering probe only; it makes no state/record
  execution claim and does not call a solver. (a/c)
- Restricted qutip-cuquantum solver probes now exist for no-boundary state /
  trajectory execution and for idle substeps plus one or more sequential Z
  readout boundaries, including partial-register readout. They are probes, not a
  production QT/MPS backend; the record probe emits no `.b8`, DEM, or decoder
  output. (a/c)
- GPU targeted validation commands completed successfully for
  `tests/test_simulator_axis1_schedule.py tests/test_joint_lindbladian.py` and
  adjacent compiler/frontend checks. This is a verification gate, not a scored
  metric. Default G2 and CodeSpec evidence runners pass after intentional
  artifact-schema identity refresh; freeze/ledger validation should be rerun
  whenever the evidence ledger is edited. (a/c)

## Review Findings

1. **Blocker: mechanism library is still deliberately narrow.**
   Current primitives are
   `DR/ZZ/T2/T1/T1_UP/T2_B/T1_B/T1_UP_B/RD/RD_B/FSIM_SWAP/FSIM_PHASE` plus
   exact frontend `CTRL_*` representatives in the dense computational-subspace
   bridge, and `LEAK_EXCHANGE_12/LEAK_SEEP_21/LEAK_HEAT_12` in the
   MCWF/MPS carrier path. This covers the present schedule bridge and first
   one-site leakage increment, not a complete hardware mechanism library. (a/c)

2. **Blocker: over-cap execution still needs a real production scalable carrier.**
   Static-ZZ over-cap idle/readout rows are now represented in
   `Axis1CarrierProgram`; the explicit qutip-cuquantum restricted backend and the
   explicit `qt_mps_state_record` restricted backend can both be selected through
   `axis1_carrier_execution_manifest(...)` for their supported over-cap slices.
   The QT/MPS path emits a centralized restricted acceptance policy, and the
   `mcwf_mps_state_record` path now executes a first fixed-microstep MCWF/MPS
   local-dimension slice. It includes first-slice one-site qutrit leakage and
   first-slice compiler-generated two-site qutrit/ququart transport plus
   conditional leaked-neighbor phase Hamiltonians.
   Supported Hamiltonian terms on the same support are now summed inside each
   MCWF microstep before one matrix exponential, so same-support transport/control
   Hamiltonians are not sequentialized.
   Completing Axis-1 at surface-code scale still needs production-grade
   trajectory semantics, finite-step error control, mixed-dimension finite-bond
   error control, leakage-removal protocol semantics, and dense record/channel
   certification beyond the first two-site Hamiltonian-block gate before
   claiming large-code coupled simulation. (c)

3. **Blocker: leakage/qutrit/ququart are started, not complete.**
   Axis-1 includes same-substep leakage Hamiltonians/collapse operators and
   leakage-aware measurement/reset boundaries when they are represented in the
   current substep generator. The dense qudit MCWF carrier proves the carrier can
   handle local dimensions beyond two, and exact qutrit/ququart smoke paths
   exist elsewhere in the repo. The carrier/MPS path now lowers the first
   one-site qutrit leakage families from public Axis-1 context and certifies
   their one-site dense qutrit channel semantics. It also lowers and executes
   first-slice two-site leakage-transport Hamiltonians
   (`LEAK_EXCHANGE_11_02`, `LEAK_MOBILITY_12_21`,
   `LEAK_TRANSPORT_30_12`, `LEAK_TRANSPORT_31_22`) and diagonal conditional
   leaked-neighbor phase Hamiltonians from compiler-generated
   two-qubit substeps. Leakage-removal/DQLR protocol semantics, two-site dense
   record/channel certification, and a complete
   leakage-aware record-boundary policy remain unfinished. Leakage persistence
   or shared source history still belongs to Axis-2. (a/c)

4. **Resolved: active `CZ` plus declared static-ZZ provenance.**
   Active `CZ` generic rows already carry a same-substep local `ZZ` primitive.
   If public static-ZZ metadata also declares that active pair, the selection row
   now records the pair in `coupling_edges` as provenance for the same local
   carrier and does not lower a second `ZZ` Hamiltonian term. This is a
   provenance-only choice, not a new Axis-1 mechanism. (a/c)

5. **Resolved for current scope: per-edge static-ZZ calibration sidecar.**
   `axis1_static_zz_calibrations` is a public optional table constrained to the
   already-declared `axis1_static_zz_couplings` edge set. It changes schedule
   source identity when present and lowers distinct `ZZ` Hamiltonian
   coefficients per edge in selected joint-L windows. It does not carry
   Hamiltonian matrices, Kraus/PTM payloads, source timelines, or evaluator-only
   mechanism truth. (a/c)

6. **Resolved: dense Choi reconstruction warning policy.**
   The public joint-L assembly now keeps every positive Choi eigenvalue by
   default instead of pruning positive weights below `NUMERICAL_ZERO`. The GPU
   audit is treated as a verification gate over reconstruction behavior, not as
   a ledgered physical metric. (a/c)

7. **Scope boundary: record evidence is not DEM/decoder integration.**
   Axis-1 record evidence and sampled `.b8` carriers exist, but no `.dem` or
   decoder artifact is claimed for joint-L records because they are not a
   Stim-Pauli model. (a/c)

## Theory-First Grounding For Next Slice

Cached notes already cover the next mechanism/scaling choices:

- Ivashkov et al. 2603.05492: GKSL learner object, short-time Hamiltonian
  versus dissipator separation, and locality/dual-graph scaling.
- Pettersson Fors et al. 2408.15402: residual static-ZZ form, conditional phase,
  and modern magnitude bracket.
- Foxen et al. 2001.08343: fSim two-qubit coherent control family and calibrated
  residual-coherence boundary.
- Marton and Asboth 2303.04672: coherent plus readout surface-code metrics and
  3D readout structure.
- Jaschke, Montangero, and Carr 1804.09796 plus Werner et al. 1412.5746:
  open-system tensor-network carrier taxonomy, quantum trajectories, MPDO/LPTN
  tradeoffs, and positivity-preserving locally-purified density evolution.
- Manabe, Suzuki, and Darmawan 2308.08186: QEC record-producing qutrit-MPS
  trajectory precedent for non-Pauli leakage simulation; useful carrier shape
  for the Axis-1 leakage/MPS-MCWF integration slice.
- Existing leakage notes should be used for the Axis-1 multilevel mechanism
  integration, while the cross-time leakage-persistence/source-history process
  remains Axis-2. The current computational-subspace slice does not close that
  integration. (a/c)

## Recommended Next Slices

1. Pre-register the finite-step policy for the restricted QT/MPS carrier before
   expanding code again. The policy must state how product formulas approximate
   the summed substep generator, which dense windows certify it, and why the
   backend is not forbidden sequential channel composition. (a/c)
2. Harden seeded sampled trajectories into an acceptance policy: RNG provenance,
   trajectory-count declarations, ensemble semantics, and when empirical record
   frequencies may be emitted without dense exact-probability certification.
   (a/c)
3. Harden the finite-bond shadow-tail ledger into a production error-control
   policy. The current ledger is useful risk evidence, but not a production
   error bound. Any scored quantity must first go through `docs/METRICS.md`.
   (c)
4. Harden the fixed-microstep `mcwf_mps_state_record` backend against dense
   within-cap noncommuting fixtures and seed-sweep evidence. The current slice
   executes real sampled MCWF/MPS trajectories, but its finite-step policy is not
   a production error bound. (a/c)
5. Continue the leakage slice: leakage-removal/DQLR protocol semantics,
   leaked-readout/reset boundary policy, dense record/channel certification
   beyond the first two-site Hamiltonian-block gate, and MCWF/MPS seed-sweep
   gates. This is Axis-1 only for instantaneous substep terms; source-driven
   leakage persistence or burst histories remain Axis-2. (a/c)

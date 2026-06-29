# Axis-1 Over-Cap Backend Readiness Review

Date: 2026-06-28

This is a review checkpoint for the transition from `dense_jointL_probe` to a
real over-cap Axis-1 carrier. It is not a declaration that Axis-1 is complete.
No new metric is introduced here; scored quantities still require
`docs/METRICS.md`.

## Current Implemented Seam

- `Axis1CarrierProgram` records schedule-derived dense-checkable and over-cap
  carrier rows, including public static-ZZ edge/calibration provenance,
  Markovian local terms, thermal-excitation context terms, dt brackets, and
  measurement boundaries. It is a program/provenance IR, not a simulator result.
  (a/c)
- `axis1_carrier_execution_manifest(...)` consumes that program and executes
  `dense_oracle_available` rows via the existing GPU joint-L state/record
  evidence under the default `dense_jointL_probe` contract. Programs with
  `scalable_required` rows still fail closed under that default contract. (a/c)
- The explicit `qutip_cuquantum_restricted_state_record_probe` carrier-execution
  contract executes the currently supported over-cap probe slice through
  qutip-cuquantum trajectory/record probes. It remains a probe, not the
  production carrier. (a/c)
- The explicit `qt_mps_state_record` carrier-execution contract now delegates to
  the restricted quimb/torch-CUDA MPS backend and exposes its
  `restricted_acceptance_policy` through the carrier seam. QT/MPS backend knobs
  are explicit `execution_backend_options`; unknown keys fail closed and
  non-QT/MPS carrier contracts reject backend options. It remains restricted
  execution evidence, not production scalable completion. (a/c)
- `axis1_qt_mps_restricted_execution_manifest(...)` is the first executable
  quimb/torch-CUDA MPS slice for `qt_mps_state_record`, restricted to
  supported Hamiltonian/control terms, local product-channel collapse branches,
  Z-record rows, finite-bond shadow-tail ledgering, and seeded sampled
  trajectories. It does not claim exact summed-Lindbladian evolution. (a/c)

## Backend Review

- Existing `forward/scalable/mps_forward.py` is a GPU `quimb` MPS trajectory
  carrier for qutrit leakage. Reusable patterns: CUDA enforcement, site ordering,
  truncation ledger, trajectory record emission, and the explicit statement of
  approximation books. Non-reusable part: leakage/qutrit physics and Wood-Gambetta
  mechanism semantics. (a/c)
- Existing `simulator/qutip_cuquantum_backend.py` is intentionally a probe. Local
  and two-site `CuOperator` construction can preserve symbolic tensor structure,
  but solver probes may still trigger dense conversion internally. Therefore
  qutip-cuquantum should first be used as backend-lowering and restricted solver
  probes, not as the production over-cap carrier. (a/c)
- Cached theory notes support two different future carriers:
  `werner_positive_tensor_network_open_systems_1412.5746.md` supports a
  positivity-preserving LPTN density carrier; `leakage_tensor_network_simulation_2308.08186.md`
  supports a pure-state trajectory MPS carrier shape for QEC record emission.
  Neither note authorizes treating a trajectory/Trotter carrier as exact dense
  channel evidence. (a/c)

## Current Execution Ladder

The implemented ladder is now:

```text
SubstepSchedule
  -> Axis1CarrierProgram
  -> dense_jointL_probe for dense_oracle_available rows
  -> qutip-cuquantum restricted execution for supported probe rows
  -> restricted quimb/torch-CUDA QT/MPS execution for H/control/local-collapse/Z-record rows
```

Acceptance gates:

- Each backend consumes compiler-generated `Axis1CarrierProgram` rows, not
  re-infer couplings from a Pauli/GF(2) artifact. (a)
- Over-cap static-ZZ idle/readout rows must carry every declared public edge and
  every supported local Markovian/context term in backend provenance. (a/c)
- qutip execution must keep `claims_qt_mps_backend_execution=false`; restricted
  QT/MPS execution must keep `claims_exact_joint_lindblad_generator=false` until
  its finite-step policy is certified against the summed generator. (a)
- No backend here may claim dense channel evidence, DEM/decoder semantics,
  Axis-2 source timelines, or production scalable completion. (a)
- Dense-checkable restricted MPS record schedules must carry exact dense joint-L
  record certification with `comparison_outcome_is_metric=false`; over-cap rows
  must not use dense certification as a fallback. (a/c)
- Finite-step restricted MPS runs must declare `microstep_count` and
  `finite_step_order`. `first_order` maps to
  `operator_family_product_formula_v1`; `strang_second_order` maps to
  `strang_hamiltonian_collapse_product_formula_v1`. Noncommuting within-cap
  `H + T1` rows are expected to show reduced dense-record difference when the
  split is refined, but this is a verification gate, not a metric or
  exact-generator claim. (a/c)
- Sampled restricted MPS trajectories must use an explicit CUDA RNG seed policy
  and must skip exact dense-probability certification; empirical record
  frequencies are execution evidence, not a metric. The restricted acceptance
  policy accepts sampled execution evidence only when `rng_seed` is explicit.
  (a/c)
- Seed-sweep restricted MPS trajectories must keep empirical seed-spread evidence
  separate from dense-calibrated trajectory evidence. Over-cap seed sweeps may
  report restricted empirical evidence, but dense calibration remains unavailable
  and production scalable acceptance remains false. (a/c)
- Restricted evidence bundles may aggregate finite-bond and seed-sweep gates, but
  remain review surfaces only: no production error bound, no production scalable
  backend, and no metric. (a/c)
- Resource probes may set heavy CUDA-memory gates over the same restricted
  bundle. They report actual peak allocated/reserved memory only and fail if a
  target is not reached; they never satisfy heavy gates by padding memory. (c)
- `max_bond=None` runs carry a complete no-explicit-truncation ledger with zero
  discarded weight. Finite `max_bond` runs now carry a CUDA shadow-state
  Schmidt-tail ledger for supported two-site Hamiltonian/control gates. This is
  still a restricted risk ledger, not a production error bound. Caller-declared
  discarded-weight gates may accept finite-bond candidate evidence, but remain
  heuristic policy gates with `comparison_outcome_is_metric=false`. At-or-above
  the conservative exact-bond sufficient cap is representability bookkeeping, not
  production error control. (a/c)
- Bond sweeps are now available as restricted convergence gates over multiple
  finite `max_bond` values. They compare record probabilities to the largest-bond
  run; for dense-checkable record schedules, that reference must also pass dense
  joint-L record certification before the sweep is accepted as restricted
  convergence evidence. They can catch under-bonding and reject self-consistent
  but finite-step-wrong references, but they are not production trace-norm or LER
  error bounds. (a/c)
- Restricted MPS manifests now emit `restricted_acceptance_policy`, a single
  policy ledger for finite-step, dense-window, sampled-trajectory, over-cap, and
  finite-bond decisions. It can accept restricted execution evidence but keeps
  `accepted_for_production_scalable_backend=false`. This is not a metric. (a/c)

## Next Implementation Slice

The next slice is production trajectory/error-control hardening for the QT/MPS carrier:

- promote the restricted trajectory sampling and RNG policy into a production
  acceptance policy with declared ensemble semantics;
- harden the finite-bond ledger into a production error-control policy before
  any production scalable backend claim; the current discarded-weight gates are
  candidate gates, not the production bound. (a/c)

## Open Decisions

- Production carrier family: pure-state trajectory MPS first, or LPTN/MPDO
  density carrier first. The current codebase favors trajectory/MPS reuse, but
  density positivity is cleaner for exact Markovian state evidence. (c)
- How to certify noncommuting local dissipation plus ZZ coupling at over-cap
  scale without silently becoming sequential channel composition. Any product
  formula must be declared as an approximation to the joint generator, not as
  exact `joint_lindbladian` channel evidence. (a/c)
- How to choose the QT/MPS micro-step policy for nonzero jumps so it remains a
  declared approximation to the summed generator rather than forbidden
  sequential channel composition. (a/c)

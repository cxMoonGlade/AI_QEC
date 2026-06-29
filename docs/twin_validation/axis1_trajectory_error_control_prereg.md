# Axis-1 Trajectory And Finite-Bond Error-Control Prereg

Date: 2026-06-29

Status: theory-first prereg for the next Axis-1 QT/MPS hardening slice. This
document does not claim Axis-1 completion and does not introduce a new metric.
Any scored quantity still requires `docs/METRICS.md`.

## Current Evidence

- Dense Axis-1 evidence remains the small-window oracle:
  `forward.joint_lindbladian.assemble_substep_channel(...)`, one summed
  same-substep generator and one `exp(L dt)`. (a)
- Restricted QT/MPS execution now emits `restricted_acceptance_policy`, including
  finite-step, sampled-trajectory, over-cap dense-fallback, and finite-bond
  decisions. It still keeps `accepted_for_production_scalable_backend=false`.
  (a/c)
- Sampled QT/MPS trajectories require explicit `rng_seed` before being accepted
  as sampled execution evidence. They are not exact dense-probability evidence.
  (a/c)
- Finite `max_bond` currently records a CUDA shadow-state Schmidt-tail ledger for
  supported two-site Hamiltonian/control gates. This is a risk ledger, not a
  production error bound. (a/c)

## Grounding Ledger

| decision surface | source | project note / code | use here | class |
|---|---|---|---|---|
| QT/MPS trajectory semantics | Jaschke, Montangero & Carr, arXiv:1804.09796 | `docs/papers/reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | pure-state trajectories carry sampling error and bond-truncation error; ensemble quantities are not single-trajectory quantities | (a/c) |
| QEC record-producing MPS trajectory | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md` | Kraus sampling, measurement-record production, dynamic-bond truncation threshold, and discarded-weight monitoring | (a/c) |
| Positivity-preserving density bound | Werner et al., arXiv:1412.5746 | `docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md` | LPTN has a stated trace-norm certificate; this is the deferred density-carrier path, not the current pure-state QT/MPS path | (a/c) |
| Metric discipline | `docs/METRICS.md` | metric ledger | trajectory uncertainty and discarded-weight policies are gates/ledgers here, not scored quantities | (a) |

## Policy To Implement

- `restricted_acceptance_policy.trajectory` must distinguish execution,
  empirical sampled evidence, and exact dense-probability evidence. Explicit
  `rng_seed` is required for sampled evidence acceptance. (a/c)
- `restricted_acceptance_policy.mps_truncation` must distinguish three states:
  no explicit truncation requested, finite-bond risk ledger recorded, and
  finite-bond candidate gate evaluated. (a/c)
- The policy may report a conservative exact-bond sufficient cap
  `2**ceil(n_sites/2)` for the computational-subspace qubit MPS. If `max_bond`
  is absent, or finite and at/above that cap, the representation is accepted as
  exact-bond-sufficient for that schedule size. This is representability
  bookkeeping, not production error control. (a)
- A bond-sweep manifest may run the same compiler-generated schedule at a
  declared increasing list of finite `max_bond` values, use the largest bond as
  an internal reference, and report the maximum record-probability difference
  across smaller bonds. This is a convergence policy gate, not a metric and not a
  density trace-norm certificate. (c)
- For dense-checkable schedules with measurement records, the largest-bond
  reference run in a bond sweep must also pass dense joint-L record certification
  before the sweep can be accepted as restricted convergence evidence. For
  over-cap schedules the reference dense certification is unavailable by design;
  the sweep may still report convergence diagnostics, but must not be accepted as
  dense-calibrated convergence evidence or production evidence. (a/c)
- A sampled-trajectory seed-sweep manifest may run the same compiler-generated
  schedule with a declared `trajectory_count` and at least two distinct explicit
  `rng_seed` values. It may compare empirical record frequencies across seeds
  under a caller-declared spread gate. This is an empirical verification gate, not
  a confidence interval, not a metric, and not an exact probability claim. (c)
- Dense-checkable sampled seed sweeps may separately compare empirical record
  frequencies against dense joint-L record probabilities under a caller-declared
  dense-frequency gate. That produces
  `accepted_as_dense_calibrated_trajectory_evidence`, separate from
  `accepted_as_restricted_seed_sweep_evidence`. Over-cap schedules must report
  dense calibration as unavailable and must not use dense fallback rows. (a/c)
- A restricted evidence bundle may combine finite-bond convergence evidence and
  trajectory seed-sweep evidence for the same compiler-generated schedule. The
  bundle has separate restricted and dense-calibrated acceptance flags and must
  keep `accepted_as_production_error_bound=false` and
  `accepted_for_production_scalable_backend=false`. It is a review aggregation
  surface over gates, not a new metric. (a/c)
- A resource probe may wrap the same restricted QT/MPS evidence bundle and report
  actual CUDA peak allocated/reserved memory from the real execution only. It
  must not allocate padding tensors to satisfy a memory target. A caller-declared
  memory gate such as a 30 GiB target is a resource smoke gate: if the workload
  does not reach it, the probe fails instead of pretending the backend is
  saturated. This is not a scientific metric. (c)
- A finite-bond candidate gate may compare `worst_cut_discarded_weight` and
  `discarded_weight_sum` against caller-declared gate values, but the result is
  only a heuristic gate with epistemic class (c). It must not be used as a
  production trace-norm error bound or a metric. (c)
- If a gate is provided and fails, the manifest may still report execution, but
  `restricted_acceptance_policy.accepted_for_restricted_execution` must be false
  because the declared approximation-risk policy was violated. (c)
- If a gate is provided and passes, the manifest may report
  `accepted_as_finite_bond_candidate=true`, but must keep
  `accepted_as_production_error_bound=false` and
  `accepted_for_production_scalable_backend=false`. (c)
- The restricted QT/MPS manifest's top-level `passed` / `verdict` must follow
  `restricted_acceptance_policy.accepted_for_restricted_execution`, not mere
  backend execution. Dense certification disabled by the caller, an implicit RNG
  seed for sampled trajectories, or a failed finite-bond candidate gate must fail
  top-level acceptance even if the backend emitted records. (a/c)
- Execution knobs that bound state-space growth must fail closed before backend
  execution: `max_branches` must be positive, and finite `max_bond` must be
  positive. This is an input contract gate, not a scored quantity. (a)
- The code must keep `max_bond=None` as the only current zero-truncation policy.
  Dynamic-chi truncation tolerance, LPTN trace-norm certificates, leakage/qutrit
  integration, DEM/decoder integration, and Axis-2 source timelines remain out of
  this slice. (a)

## Anti-Toy Predictions

- **Finite-bond failure gate:** the existing Bell/CZ finite-`max_bond` fixture has
  nonzero discarded weight. If a caller declares a stricter finite-bond gate than
  the observed ledger, the restricted acceptance policy must reject restricted
  execution evidence while preserving the execution ledger. This is a gate, not a
  metric. (c)
- **Finite-bond candidate gate:** if a caller declares a looser finite-bond gate
  than the observed ledger, the policy may mark finite-bond candidate acceptance
  true, but must still reject production error-bound and production scalable
  claims. (c)
- **Exact-bond sufficiency gate:** a two-qubit Bell/CZ fixture with `max_bond=2`
  should be marked at/above the conservative exact-bond sufficient cap and carry
  zero discarded weight, while the same fixture with `max_bond=1` must be marked
  below the cap. This is exact representability bookkeeping, not a metric. (a)
- **Bond-sweep convergence gate:** a compiler-generated Bell/CZ fixture swept
  over `[1, 2]` should detect the finite-bond approximation gap, while `[2, 4]`
  should pass a tight convergence gate because both are at/above the conservative
  exact-bond sufficient cap for two qubits. This is a gate, not a metric. (c)
- **Reference dense-calibration gate:** a noncommuting `H + T1` fixture whose
  product-formula reference fails dense joint-L certification must fail the
  bond-sweep acceptance even if a bond comparison is internally converged. This
  prevents self-consistent but wrong finite-step sweeps. (a/c)
- **No metric laundering:** every finite-bond gate field must carry
  `comparison_outcome_is_metric=false` and `epistemic_class="c"`. (a/c)
- **No execution/acceptance laundering:** dense-checkable exact runs with
  `dense_oracle_certification=false`, and sampled runs without an explicit
  `rng_seed`, must emit records but fail top-level restricted acceptance. (a/c)
- **Trajectory seed-sweep gates:** deterministic records with explicit distinct
  seeds should pass both seed-spread and dense-frequency gates up to numerical
  floor; a one-shot `H` readout fixture may pass restricted seed-spread acceptance
  while failing dense-calibrated trajectory evidence under a tight
  dense-frequency gate. Over-cap seed sweeps may pass restricted empirical
  evidence but must keep dense calibration unavailable and production false. (c)
- **Bundle gate:** a deterministic dense-checkable bundle should pass restricted
  and dense-calibrated flags, while an under-bonded Bell/CZ bundle must fail if
  the finite-bond convergence gate fails even when the trajectory seed sweep
  passes. (c)
- **Resource gate:** a low target should pass while an intentionally unreachable
  target should fail with `peak_reserved_gib_below_gate`, proving the probe is not
  padding memory to pass resource gates. (c)
- **No density-bound overclaim:** pure-state QT/MPS finite-bond gates must not cite
  Werner's LPTN trace-norm theorem as already implemented. LPTN remains a separate
  future carrier. (a)

## Open Risks / Decisions

- Production-grade error control likely needs either dynamic-chi convergence
  sweeps plus problem-specific acceptance, or an LPTN/MPDO density carrier with a
  stated norm certificate. The current fixed-`max_bond` gate is not enough. (c)
- Trajectory ensemble uncertainty remains an empirical sampling issue. Seed sweeps
  are reproducible empirical gates only. Adding a confidence interval or
  decoder-level finite-sample claim would require the `docs/METRICS.md` ladder
  first. (a/c)
- Surface-code 2D-to-MPS ordering can turn local layout edges into long MPS-range
  gates. Site ordering and long-range MPO cost remain production backend
  decisions. (c)

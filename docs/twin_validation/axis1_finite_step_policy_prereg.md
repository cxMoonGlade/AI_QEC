# Axis-1 Finite-Step Policy Prereg

Date: 2026-06-28

Status: theory-first prereg before hardening the restricted QT/MPS carrier into
a production Axis-1 carrier. This document does not claim Axis-1 completion and
does not introduce a new metric. Any scored quantity still requires
`docs/METRICS.md`.

## Current Evidence

- Dense Axis-1 evidence remains
  `forward.joint_lindbladian.assemble_substep_channel(...)`: one same-substep
  joint generator `exp(L dt)` from the selected `H_list,c_list`. This is the
  exact small-window oracle. (a)
- `axis1_qt_mps_restricted_execution_manifest(...)` is now an executable
  quimb/torch-CUDA computational-subspace MPS carrier for supported
  Hamiltonian/control terms, local product-channel collapse branches, Z records,
  seeded sampled trajectories, and finite-bond shadow-tail ledgers. It still
  declares `claims_exact_joint_lindblad_generator=false` and
  `claims_production_scalable_backend=false`. (a/c)
- A within-cap `H + T1` substep is a noncommuting case: a single large
  product-formula step can disagree with the dense joint-L record oracle. The
  comparison is a verification gate, not a metric. (c)

## Grounding Ledger

| decision surface | source | project note / code | use here | class |
|---|---|---|---|---|
| Same-substep GKSL target | Jaschke, Montangero & Carr, arXiv:1804.09796 | `docs/papers/reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | target Lindblad equation, QT carrier, and warning that `L=A+B` cannot be split into independent Lindblad terms without changing cross terms | (a/c) |
| Product-formula scaling language | Jaschke et al. arXiv:1804.09796; Werner et al. arXiv:1412.5746 | reading notes above | second-order TEBD examples give local `O(dt^3)` / fixed-time `O(dt^2)` scaling for their stated split formulas; our current first restricted policy is only a declared product-formula gate until certified | (a/c) |
| Positivity-preserving density alternative | Werner et al., arXiv:1412.5746 | `docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md` | LPTN gives stronger density trace-norm bound language, but is deferred infrastructure | (a/c) |
| QEC trajectory carrier precedent | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md` | per-shot MPS trajectory, Kraus sampling, measurement records, and truncation ledger shape | (a/c) |

## Policy To Implement

The restricted QT/MPS carrier must expose an explicit finite-step policy:

- `finite_step_policy` is derived from `finite_step_order`: `first_order` maps to
  `operator_family_product_formula_v1`, while `strang_second_order` maps to
  `strang_hamiltonian_collapse_product_formula_v1`. Both apply supported
  Hamiltonian/control terms and local product-channel collapse branches inside
  each schedule substep using a declared operator-family order. This is a
  product-formula approximation to the summed substep generator, not exact
  joint-L channel evidence. (a/c)
- `microstep_count >= 1`. Each schedule substep of duration `dt` is internally
  split into `microstep_count` equal microsteps of duration `dt/microstep_count`.
  Measurement projection remains at the public measurement boundary after the
  substep evolution. (a/c)
- `finite_step_order` may be either `first_order` or `strang_second_order`.
  `first_order` applies Hamiltonian/control evolution then product-channel
  collapse branches in each microstep. `strang_second_order` applies a
  Hamiltonian/control half step, then product-channel collapse branches, then a
  Hamiltonian/control half step. This mirrors the second-order split language in
  the open-system tensor-network literature, but remains a declared
  approximation until dense-window certification supports it. (a/c)
- Dense-checkable exact-enumeration runs must compare record probabilities
  against `axis1_measurement_record_evidence_manifest(...)` when records exist.
  The reported dense-record difference and gate threshold are verification gates
  only and must keep `comparison_outcome_is_metric=false`. (c)
- Sampled trajectory runs emit empirical record frequencies and must skip exact
  dense-probability certification. A sampled run may be accepted as restricted
  sampled execution evidence only when `trajectory_count` is declared and
  `rng_seed` is explicit; defaulting to seed zero may execute but is not accepted
  by the policy ledger. (a/c)
- Finite `max_bond` keeps the CUDA shadow-state Schmidt-tail risk ledger. This
  is not a production error bound and not a metric. (c)
- The execution manifest must carry a single
  `restricted_acceptance_policy` block. It records whether the run is accepted as
  restricted execution evidence, why it is not accepted as production scalable
  backend completion, the finite-step order and dense-window certification
  status, trajectory semantics, over-cap dense-fallback policy, and finite-bond
  ledger status. This is a policy ledger, not a score. (a/c)
- Dense-checkable exact-enumeration runs are accepted as restricted finite-step
  evidence only when dense record certification executes and passes. Over-cap
  exact-enumeration runs may be accepted as restricted execution evidence without
  dense fallback, but must report
  `accepted_for_production_scalable_backend=false`. Sampled trajectory runs,
  including over-cap sampled runs, may be accepted as sampled execution evidence
  when the seed is explicit, but not as exact dense-probability evidence. Finite
  `max_bond` with nonzero discarded weight must report no production
  error-control acceptance. (a/c)

## Anti-Toy Predictions

- **Noncommuting convergence gate:** for a compiler-generated within-cap substep
  containing a frontend Hamiltonian control plus local `T1`, increasing
  `microstep_count` should reduce the dense joint-L record difference relative to
  `microstep_count=1`. This is a falsifiable implementation gate, not a metric.
  (c)
- **Symmetric split gate:** on the same noncommuting `H + T1` window,
  `finite_step_order="strang_second_order"` at fixed microstep count should not
  be worse than the first-order split and should reduce the difference in the
  registered fixture. This is a verification gate, not a metric. (c)
- **No exact overclaim:** even if the dense-record difference decreases, the
  manifest must keep `claims_exact_joint_lindblad_generator=false` and
  `claims_dense_channel_evidence=false`. (a)
- **No sampled laundering:** sampled trajectories must not pass exact dense
  probability certification; they are empirical trajectory evidence. Runs without
  an explicit `rng_seed` must not be accepted as sampled evidence. (a/c)
- **Policy centralization gate:** the manifest must expose exactly where
  finite-step, trajectory, over-cap, and finite-bond decisions live, with
  `comparison_outcome_is_metric=false` on every dense-window comparison. (a/c)
- **No Axis-2 leakage:** this policy does not add source timelines, memoryful
  noise, leakage/qutrit physics, `.dem`, or decoder semantics. (a)

## Open Risks

- A first-order operator-family split may converge slowly for strongly
  noncommuting terms. The restricted Strang option reduces the registered
  within-cap difference, but production acceptance still needs an explicit
  finite-step policy and error-control rule. (c)
- Current local collapse branches are exact finite-time product channels for
  supported one-site families, but their interleaving with Hamiltonian terms is
  still a product-formula approximation to the summed GKSL generator. (a/c)
- Dense record certification is only available for within-cap schedules; over-cap
  rows need policy evidence from local windows plus risk ledgers, not dense
  channel fallback. (a/c)

## MCWF/MPS Hamiltonian-Aggregation Update

Preregistration update, 2026-06-28, before changing
`axis1_mcwf_mps_state_record_execution_manifest(...)`.

Motivation: the MCWF/MPS path currently applies Hamiltonian terms in
operator-family order within each microstep. That is honest product-formula
evidence, but it leaves an avoidable Axis-1 gap: Hamiltonian terms on the same
support can be summed exactly for the microstep as
`U = exp(-i (sum_j H_j) dt_micro)`. Collapse/no-jump evolution remains a
finite-step MCWF approximation and is not made exact by this change. (a/c)

Policy update:

- For each MCWF/MPS microstep, group supported Hamiltonian terms by exact support
  tuple and apply one matrix exponential per group:
  `exp(-i sum_j H_j dt_micro)`. (a)
- Supported one-site groups include ideal one-qubit controls and
  `LEAK_EXCHANGE_12`. Supported two-site groups include ideal two-qubit
  controls, `ZZ/FSIM_PHASE`, and the first two-site leakage-transport families
  (`LEAK_EXCHANGE_11_02`, `LEAK_MOBILITY_12_21`,
  `LEAK_TRANSPORT_30_12`, `LEAK_TRANSPORT_31_22`). (a/c)
- The grouping is by public carrier support and family metadata only; no
  evaluator channel, Kraus, PTM, source timeline, or hidden teacher truth is
  introduced. (a)
- The manifest should update `hamiltonian_evolution_policy` and
  `finite_step_policy`: Hamiltonian substeps are summed per support, while
  Hamiltonian-vs-collapse splitting remains first-order or Strang according to
  `finite_step_order`. It must keep
  `claims_exact_joint_lindblad_generator=false`,
  `claims_dense_channel_evidence=false`, and
  `comparison_outcome_is_metric=false`. (a)

Anti-toy gates:

- A compiler-generated two-qubit substep containing `CTRL_CZ` plus public
  `LEAK_EXCHANGE_11_02` should evolve `|11>` according to the summed Hamiltonian
  block, not sequential `CZ` then leakage exchange. This is observable by
  comparing the measured `|02>` probability against a direct `torch.linalg.matrix_exp`
  reference on the ordered qutrit pair. (a/c)
- A qutrit/ququart dimension mismatch still fails closed before execution. (a)
- Same-substep collapse terms still use joint jump competition after the
  Hamiltonian group step; this update must not turn collapse operators into
  sequential finite channels. (a/c)
- No METRICS ledger change and no new scored quantity. (a)

Implementation update:

- `axis1_mcwf_mps_state_record_execution_manifest(...)` now groups supported
  Hamiltonian terms by exact support inside each microstep and applies one
  `torch.linalg.matrix_exp(-i sum(H_j) dt_micro)` per group. (a/c)
- The manifest reports
  `hamiltonian_evolution_policy="same_support_hamiltonian_sum_matrix_exp"` and
  finite-step names
  `same_support_hamiltonian_sum_first_order_mcwf_split_v1` or
  `same_support_hamiltonian_sum_strang_mcwf_split_v1`. (a/c)
- Tests include a compiler-generated `CTRL_CZ + LEAK_EXCHANGE_11_02` qutrit
  substep and compare the grouped gate against a direct dense
  `torch.linalg.matrix_exp` reference, while also checking it differs from the
  old sequential `CZ`-then-leakage product. (a/c)
- The update does not change collapse/no-jump MCWF approximation status,
  production acceptance, Axis-2 scope, DEM/decoder integration, or
  `docs/METRICS.md`. (a)

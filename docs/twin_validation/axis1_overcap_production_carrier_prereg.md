# Axis-1 Over-Cap Production Carrier Prereg

Date: 2026-06-28

Status: theory-first review gate before implementing a production over-cap
Axis-1 carrier. This document does not claim that Axis-1 is complete and does
not introduce a new metric. Any scored quantity still requires `docs/METRICS.md`.

## Current State

- Dense Axis-1 evidence is already owned by
  `src/qec_twin/forward/joint_lindbladian.py`: same-substep `H_list,c_list`,
  one joint Liouvillian, one `expm(L dt)`, and dense G2/channel evidence. This
  remains the exact small-window oracle. (a)
- `Axis1CarrierProgram` now routes compiler-generated schedules into
  `dense_oracle_available` and `scalable_required` rows. It is program/provenance
  IR, not a backend execution result. (a/c)
- `axis1_carrier_execution_manifest(...)` defaults to the dense-checkable
  `dense_jointL_probe` path and still fails closed on `scalable_required` rows
  under that contract. It also exposes an explicit
  `qutip_cuquantum_restricted_state_record_probe` backend contract that can
  execute the currently supported over-cap static-ZZ idle and one-qubit-control
  plus Z-readout rows. This is executable probe evidence, not QT/MPS production
  scalable backend evidence. (a/c)
- qutip-cuquantum probes now cover symbolic lowering, restricted no-boundary
  state/trajectory execution, and restricted sequential Z measurement boundaries
  with idle dynamics plus supported one-qubit frontend-control Hamiltonians.
  They are probes, not production scalable backend evidence. (a/c)
- `axis1_qt_mps_restricted_execution_manifest(...)` is now the first executable
  quimb/torch-CUDA MPS slice behind `qt_mps_state_record`. It supports
  Hamiltonian/control terms, including supported compiler two-qubit frontend
  controls, local product-channel collapse branches for `T1/T1_UP/T2/RD`, and
  Z-record execution. This is MPS execution, not exact summed-Lindbladian
  evolution and not full production scalable backend completion. (a/c)

## Grounding Ledger

| decision surface | source | project note / code | use here | class |
|---|---|---|---|---|
| Same-substep GKSL semantics | Jaschke, Montangero & Carr, arXiv:1804.09796 | `docs/papers/reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | QT/MPDO/LPTN taxonomy and warning against splitting `L=A+B` into independent Lindblad terms | (a/c) |
| Positivity-preserving density carrier | Werner et al., arXiv:1412.5746 | `docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md` | LPTN `rho=X X^dag`, Trotter/compression trace-norm bound language | (a/c) |
| QEC record-producing MPS trajectory precedent | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md` | per-shot MPS trajectory with measurement records and truncation ledger shape | (a/c) |
| Existing project MPS trajectory infrastructure | `src/qec_twin/forward/scalable/mps_forward.py`, `src/qec_twin/simulator/mcwf_executor.py` | code | reusable GPU trajectory/executor patterns; qutrit leakage physics is not reused for this slice | (a/c) |
| qutip-cuquantum backend shape | `docs/twin_validation/qutip_family_master_equation_backend_review.md`, `src/qec_twin/simulator/qutip_cuquantum_backend.py` | review/code | probe/oracle adapter, not dense G2 or production carrier | (a/c) |

## Review Findings

1. **Production Axis-1 cannot be a Pauli/DEM fallback.** Over-cap rows must
   consume `Axis1CarrierProgram` terms and preserve same-substep joint-generator
   semantics. A Stim/DEM record model is a different representability class. (a)

2. **qutip-cuquantum is useful but not sufficient as the production contract.**
   It is a good `H + c_ops` probe and can exercise tensor-structured state
   evolution, but current evidence includes dense-conversion warnings and no
   project-owned record packing, truncation ledger, or large-code approximation
   book. (a/c)

3. **QT/MPS is the first production candidate, not the final density answer.**
   Quantum trajectories align naturally with QEC shot records and existing GPU
   trajectory infrastructure. The ensemble approximates density evolution only
   through sampling; single trajectories are not dense channel evidence. (a/c)

4. **LPTN remains the cleaner density-carrier option.** Werner et al. give the
   positivity-preserving `rho=X X^dag` representation and a Trotter/compression
   trace-norm bound. That is stronger for density evidence but requires new
   infrastructure, so it is deferred unless QT/MPS cannot support the needed
   record carrier. (a/c)

5. **The next backend must carry an approximation book.** At minimum: trajectory
   sampling, any Trotter/product-formula split, MPS truncation/discarded weight,
   site ordering, and record-branch sampling/packing. These are verification
   gates and risk ledgers, not new metrics. (c)

## Production Carrier Contract

The first production carrier should expose:

- `backend_contract="qt_mps_state_record"` and `gpu_required=true`. (a/c)
- Input: compiler-sealed `SubstepSchedule` plus `Axis1CarrierProgram`; no
  re-inference from Pauli artifacts, source timelines, or hidden teacher labels.
  (a)
- Per-substep lowering: all selected Hamiltonian and collapse terms in a substep
  enter one stochastic unraveling of the summed GKSL generator. If a Trotter
  layer is used internally, it must be declared as an approximation to the joint
  generator, not as exact joint-L evidence. (a/c)
- Output: state/record evidence and optional sampled record carriers. It must not
  emit dense Choi/G2 rows for over-cap schedules, `.dem` semantics, decoder
  results, Axis-2 source truth, or leakage/qutrit claims. (a)
- Approximation book: trajectory count / RNG policy, local time-step or solver
  policy, MPS site ordering, truncation ledger, and dense-oracle comparison
  coverage where feasible. (c)

## Acceptance Gates For The Next Code Slice

- **Compiler-generated schedule:** the test fixture must be produced through
  `CircuitIR` or `CodeSpec`, not by hand-writing carrier rows. (a)
- **Over-cap route preserved:** a real support larger than the dense local cap
  must produce `scalable_required` carrier rows with every public static-ZZ edge
  and local Markovian/context term present in provenance. (a/c)
- **Dense oracle pin:** the same backend interface must run a within-cap schedule
  and compare final state/record evidence against the existing dense joint-L
  state/record path. The comparison is a verification gate, not a metric. (c)
- **Sequential-composition negative control:** keep a case where
  `exp((L_a+L_b)dt)` disagrees with `exp(L_b dt) exp(L_a dt)` and require the
  production carrier manifest to declare how it represents the summed generator.
  (a/c)
- **No `.dem` overclaim:** any record carrier emitted from analog joint-L records
  must declare no DEM/decoder semantics unless a separate, registered reduction
  is introduced later. (a)
- **GPU-only execution:** circuit/carrier physics must not fall back to CPU-only
  tests. If CUDA is invisible, the run is not release evidence. (a)

## Recommended Next Implementation Slice

Add the production-carrier manifest skeleton before the heavy backend:

```text
Axis1CarrierProgram
  -> Axis1ProductionCarrierContract manifest
  -> fail-closed execution for scalable_required rows
  -> dense-oracle-compatible execution for dense_oracle_available rows
  -> declared approximation_book fields
```

This is intentionally a contract-and-ledger slice. It should not yet claim
large-code simulation. **Implemented in two layers:
`Axis1CarrierProgram` now emits `axis1_carrier_approximation_book.v1`, and
`axis1_qt_mps_state_record_contract_manifest(...)` validates that contract,
delegates within-cap schedules to dense joint-L certification, and fails closed
on `scalable_required` rows. This is still not QT/MPS backend execution.** Next,
implement the first GPU trajectory/MPS execution path behind it and certify
against dense joint-L on small schedules before accepting over-cap record
evidence. (a/c)

**Current increment:** the first restricted GPU MPS execution slice now exists
for Hamiltonian/control / local product-channel collapse / Z-record rows,
including a restricted CUDA shadow-state finite-bond ledger and seeded sampled
trajectory mode. The finite-step policy now exposes
`microstep_count` plus `finite_step_order`, with `first_order` and
`strang_second_order` options, and has a within-cap noncommuting `H + T1`
verification gate. It now emits `restricted_acceptance_policy`, which centralizes
finite-step, dense-window, sampled-trajectory, over-cap, and finite-bond
decisions while keeping `accepted_for_production_scalable_backend=false`. Sampled
over-cap runs may be accepted as restricted sampled execution evidence only with
an explicit `rng_seed`; they remain empirical record evidence, not exact
dense-probability evidence. Optional finite-bond discarded-weight gates are now
restricted candidate gates, not production error bounds. Exact-bond sufficient
caps are representability bookkeeping for the current schedule size, not a
large-code production claim. Bond-sweep convergence gates now catch under-bonding
and require dense joint-L reference certification for dense-checkable record
schedules before acceptance, without claiming a trace-norm or LER error bound.
The next production-carrier slice is no longer another contract surface; it must
harden trajectory plus finite-bond error control before any full Axis-1
production-carrier claim. (a/c)

## Open Risks

- A pure-state trajectory carrier gives record samples naturally, but density
  observables require ensemble convergence; do not cite a single trajectory as
  density evidence. (a/c)
- Long-range edges from a 2D layout mapped to an MPS chain can inflate bond
  dimension. Site ordering must be a declared backend choice. (c)
- Trotter splitting can accidentally become forbidden sequential composition.
  Product formulas are allowed only as declared approximations to the summed
  generator, with dense-window checks. (a/c)
- Reusing qutrit leakage infrastructure is helpful for GPU trajectory patterns,
  but computational-subspace Axis-1 must not silently import leakage/qutrit
  physics. (a/c)

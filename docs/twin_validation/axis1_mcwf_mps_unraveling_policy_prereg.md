# Axis-1 MCWF/MPS Unraveling Policy Prereg

Status: theory-first preregistration, 2026-06-29. This document is written
before implementing the real `mcwf_mps_state_record` backend. It introduces no
new metric and does not claim Axis-1 completion.

## 0. Grounding Ledger

| sub-axis | mechanism / carrier paper | observable / certification paper | reading note | in-repo code to reuse |
|---|---|---|---|---|
| Same-substep MCWF semantics | Jaschke, Montangero & Carr, arXiv:1804.09796 | same | `docs/papers/reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | `src/qec_twin/simulator/axis1_mcwf_mps_contract.py` |
| Positivity-preserving density alternative | Werner et al., arXiv:1412.5746 | trace-norm bound theorem for LPTN, not adopted as a metric here | `docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md` | deferred; dense oracle remains `forward.joint_lindbladian` |
| QEC record-producing qutrit MPS trajectory precedent | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | QEC syndrome/logical record emission and SVD truncation ledger shape | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md` | `src/qec_twin/simulator/mcwf_backend.py`, `src/qec_twin/forward/kernels/qutrit_mcwf_ops.cu` |
| Leakage dimensionality and rates | Wood & Gambetta, arXiv:1704.03081 | `L1`, `L2`, coherence-of-leakage definitions; metrics governed by `docs/METRICS.md` | `docs/papers/reading_notes/wood_gambetta_leakage_characterization_1704.03081.md` | `src/qec_twin/mechanisms/qutrit_teachers.py`, `src/qec_twin/simulator/qutrit_leakage.py` |
| Qubit master-equation Axis-1 concurrent simulator precedent | QMCtwin, arXiv:2606.19848 | concurrent master-equation simulator shape, but no leakage/qutrit completion | `docs/papers/reading_notes/qmctwin_master_equation_digital_twin_2606.19848.md` | `src/qec_twin/forward/joint_lindbladian.py` |

All numbers in this prereg are epistemic-classed. Paper-local numbers such as
Manabe-Suzuki-Darmawan SVD tolerances `1e-6` and `1e-4` are paper facts, not
adopted project gates. (a)

## 1. Mechanism / Carrier Target

The target backend contract is `mcwf_mps_state_record`. It is not a new noise
metric and not a new physics source. It is the scalable Axis-1 state/record
carrier for a compiler-generated `Axis1CarrierProgram`. (a/c)

For each positive-duration substep, the backend consumes the substep's summed
Hamiltonian and collapse lists:

```text
H_sub = sum_i H_i
c_sub = {c_k}
H_eff = H_sub - i/2 sum_k c_k^dag c_k
```

The MCWF trajectory state evolves as a pure state. Jump/no-jump sampling and
measurement/reset boundaries produce per-shot records. The MPS stores that pure
state; MCWF is the trajectory semantics, MPS is the representation. (a)

The same local-dimension machinery must support:

- `local_dims=(2, ...)` for computational-subspace qubit schedules; (a)
- `local_dims=(3, ...)` for qutrit leakage/seepage states; (a/c)
- `local_dims=(4, ...)` or mixed local dimensions for ququart/general-qudit
  leakage-transport manifolds. (a/c)

The current `qt_mps_state_record` restricted backend is not this target. It uses
operator-family product formulas and local product-channel branches; it remains
useful evidence, but it must not be relabeled as strict continuous-time MCWF.
(a)

## 2. Finite-Step Policy To Preregister Before Code

The first executable `mcwf_mps_state_record` slice should declare one of these
policies explicitly in the manifest. (c)

1. **Fixed-microstep MCWF policy.**
   Each substep is divided into `microstep_count` equal slices. Within a
   microstep, the backend applies a declared product formula for `H_eff` and
   jump sampling. This is a finite-step approximation to the summed generator,
   not exact `exp(L dt)` channel evidence. Global exactness is not claimed. (c)

2. **Adaptive event-time MCWF policy.**
   For time-independent local `H_sub,c_sub` inside one substep, sample jump time
   from the non-Hermitian norm loss and propagate until the event or substep end.
   This is closer to continuous-time MCWF but still needs MPS product-formula and
   truncation ledgers for noncommuting/nonlocal terms. (c)

3. **Finite-Kraus trajectory policy.**
   For leakage channels already registered as finite CPTP Kraus maps, sample a
   Kraus branch by Born probability. This is a valid pure-state trajectory for
   the finite channel, but it is not automatically the same object as a
   continuous-time MCWF unraveling of a declared GKSL generator. The manifest must
   name it separately. (a/c)

Initial implementation recommendation: start with fixed-microstep MCWF for
qubit `H,c` rows, plus finite-Kraus trajectory support only for explicitly
registered leakage channels. Keep both policies separate in the approximation
book. (c)

## 3. Required Manifest Fields

Every executable `mcwf_mps_state_record` manifest must include:

- `backend_contract="mcwf_mps_state_record"`; (a)
- `gpu_required=true`; (a)
- `local_dims`, `site_order`, and local-dimension source; (a/c)
- `trajectory_count`, `rng_seed`, `rng_backend`, and whether the seed was
  explicit; (a/c)
- `unraveling_policy`, `microstep_count`, and finite-step order if used; (c)
- `mps_truncation_ledger` with max bond, discarded weights, and whether
  truncation occurred; (c)
- `same_substep_generator_policy` stating that `H_list,c_list` are consumed as
  one substep problem, not sequential channel composition; (a)
- `claims_exact_joint_lindblad_generator=false` unless a separate theorem-grade
  exactness proof exists; (a)
- `claims_dense_channel_evidence=false`, `claims_dem_decoder_semantics=false`,
  `claims_axis2_source_timeline=false`, and
  `claims_production_scalable_backend=false` until the production gate is
  separately passed. (a)

## 4. Observable / Evidence Surface

This backend emits state/record evidence, not dense channel evidence. (a)

Allowed verification surfaces:

- exact deterministic cases, e.g. zero-rate or deterministic reset/measurement,
  compared bit-for-bit or probability-exactly against dense oracle records; (a)
- dense-window record probability comparison against
  `axis1_measurement_record_evidence_manifest(...)` for qubit rows within the
  dense cap; this is a verification gate, not a metric; (a/c)
- seed-sweep empirical frequency stability for sampled trajectories; this is a
  policy gate, not a confidence interval or metric; (c)
- finite-step convergence sweep over `microstep_count` and finite-step order;
  this is a policy gate unless registered in `docs/METRICS.md`; (c)
- finite-bond convergence/truncation ledger; not a production error bound until
  a separate theorem or registered metric supports that claim. (c)

For leakage/qutrit/ququart integration, the evidence surface must additionally
show that leaked levels are represented in the carrier state and are not
projected back into the computational subspace except by an explicitly declared
measurement/reset/leakage-removal operation. (a/c)

## 5. Anti-Toy Tests

The first backend slice is not acceptable unless these tests are present:

- compiler-generated `Axis1CarrierProgram` rows drive the backend; no hand-written
  fake schedule as the only proof. (a)
- `ZZ x T2` exact-zero and `DR x ZZ` nonzero G2 remain grounded in the existing
  dense `joint_lindbladian` metric/gate; the MCWF backend may certify against
  them but must not replace the G2 definition. (a/c)
- a bad sequential-composition implementation is caught by a dense-window
  noncommuting fixture. (a/c)
- `microstep_count` or adaptive-step refinement changes finite-step residual in
  the predicted direction; the result is a gate, not a metric. (c)
- seed-sweep requires explicit distinct CUDA RNG seeds for sampled acceptance.
  (a/c)
- MPS truncation ledger catches deliberately under-bonded record differences.
  (c)
- qubit, qutrit, ququart, and mixed `local_dims` smoke tests run on CUDA and show
  no computational-subspace projection by the carrier. (a/c)
- measurement/reset boundaries remain boundary rows and are not silently dropped.
  (a)

## 6. Scope Boundary

In scope for Axis-1:

- instantaneous same-substep leakage, crosstalk, coherent residuals, thermal
  excitation, readout dephasing, and externally supplied drift/burst parameter
  snapshots; (a/c)
- multilevel Hilbert spaces when the current substep generator requires them;
  (a/c)
- measurement/reset boundary handling for records. (a/c)

Out of scope for this backend slice:

- Axis-2 source timelines, fan-out histories, cross-cycle latent drift/burst
  processes, and leakage persistence sources; (a/c)
- `.dem`/decoder semantics for joint-L records; (a)
- new scored metrics or modifications to `docs/METRICS.md`; (a)
- production scalable completion. (a)

## 7. Open Decisions / Blockers

- Choose fixed-microstep versus adaptive event-time MCWF for the first real
  `mcwf_mps_state_record` backend. (c)
- Decide whether leakage enters first as finite-Kraus trajectory channels,
  continuous-time qutrit Lindblad `H,c` terms, or both under separate policy
  labels. (c)
- Define how public `local_dims` are supplied without leaking evaluator-only
  mechanism truth into frontend schedule metadata. (c)
- Decide the first leakage validation object before adding any leakage score;
  Wood-Gambetta `L1/L2/C_L` are field-standard definitions, but any project
  acceptance number still goes through `docs/METRICS.md`. (a/c)
- Run an un-led anti-toy review before claiming anything beyond contract and
  restricted evidence. (c)

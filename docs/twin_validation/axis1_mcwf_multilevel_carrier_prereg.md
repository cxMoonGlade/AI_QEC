# Axis-1 MCWF Multilevel Carrier Prereg

Status: theory-first preregistration for the Axis-1 MCWF carrier slice. This
document does not claim Axis-1 completion and does not introduce a new metric.

## Current State

- Axis-1 schedule, carrier-program, dense joint-L evidence, restricted QT/MPS
  execution, and qutip-cuquantum probes already consume compiler-generated
  `SubstepSchedule` rows. (a/c)
- `DenseQutritMcwfBackend` is already a batched GPU trajectory backend, but its
  public contract is qutrit-specific and Grover/leakage-oriented. (a)
- Exact qutrit and ququart density-matrix smoke paths exist for Wood-Gambetta
  leakage and CZ leakage transport, but they are small-register exact oracles,
  not scalable trajectory carriers. (a)

## Scope Correction

MCWF is a Hilbert-space trajectory method, not a computational-subspace-only
method. The Axis-1 MCWF carrier must therefore support local Hilbert dimensions:

- qubit: `local_dims=(2, ...)` for computational-subspace Lindblad controls; (a)
- qutrit: `local_dims=(3, ...)` for native `|2>` leakage/seepage; (a)
- ququart / general qudit: `local_dims=(4, ...)` or mixed local dimensions for
  transport/leakage manifolds that cannot be represented by a qutrit. (a/c)

The current restricted QT/MPS qubit slice remains useful, but it is not the full
MCWF architecture. (a)

## Literature Anchors

- QMCtwin (`2606.19848`) demonstrates same-round master-equation simulation of
  concurrent two-level coherent/dissipative/ZZ mechanisms, but explicitly does
  not include leakage/qutrits and has no independent exact oracle at operating
  scale. It is a prior-art baseline for qubit-level Axis-1 concurrent Markovian
  coupling, not a leakage-complete carrier. (a/c)
- Wood-Gambetta leakage characterization (`1704.03081`) defines `L1`, `L2`, and
  coherence-of-leakage, and establishes why leakage needs an enlarged Hilbert
  space rather than a Pauli/DEM substitute. (a)
- Manabe-Suzuki-Darmawan leakage TN simulation (`2308.08186`) simulates QEC
  leakage with qutrit MPS trajectories using local Kraus sampling and projective
  measurements; it is the nearest architecture template for scalable leakage
  MCWF/MPS. (a/c)
- Sarovar et al. crosstalk detection (`1908.09855`) defines crosstalk as
  locality/independence violation and grounds conditional-MI/TVD witnesses. It
  motivates operation-conditioned Axis-1 crosstalk terms, while metric use still
  stays governed by `docs/METRICS.md`. (a/c)

## Axis-1 vs Axis-2 Boundary

Axis-1 owns instantaneous same-substep joint dynamics:

- leakage Hamiltonians/collapse operators active inside a substep; (a/c)
- same-substep crosstalk, including static ZZ, drive spillover, readout
  crosstalk/dephasing, and correlated local collapse; (a/c)
- burst/drift parameter snapshots if the values are externally supplied for the
  current substep. (c)

Axis-2 owns cross-time memory:

- shared source timelines, fan-out, latent drift processes, burst event histories,
  leakage persistence sources, and any cross-cycle source correlation. (a/c)

Thus drift and burst are not excluded from Axis-1; their instantaneous parameter
values may feed the Axis-1 generator. The stochastic process that generated those
values remains Axis-2. (a/c)

## Minimal Dense-Qudit MCWF Carrier Fields

The next implementation slice should add a small, generic GPU carrier with:

- `local_dims`: tuple of per-site Hilbert dimensions; (a)
- `dim`: product of `local_dims`; (a)
- `basis_state(batch_size, levels)`: batched pure trajectory initialization; (a)
- `apply_operator(psi, operator, sites)`: local unitary or non-unitary operator on
  arbitrary site dimensions; (a/c)
- `apply_kraus(psi, kraus, sites)`: MCWF Kraus sampling by Born probability; (a/c)
- `measure_sites(psi, sites)`: computational-basis projective measurement and
  state collapse; (a/c)
- manifest fields declaring `gpu_required=true`,
  `accepted_for_production_scalable_backend=false`, and
  `comparison_outcome_is_metric=false`. (a/c)

This dense carrier is not the final scalable MPS carrier. It is a correctness and
interface slice proving that MCWF is dimension-polymorphic before tying it to the
Axis-1 carrier program. (c)

## Anti-Toy Tests

- qubit: Hadamard on `(2,)` produces `0/1` probabilities near `1/2`. (a)
- qutrit: a `|1><->|2>` unitary or Kraus family moves population into level `2`
  without any computational-subspace projection. (a/c)
- ququart: a local or two-site operator acts on dimension `4` levels and preserves
  normalization when unitary. (a/c)
- batch: increasing `batch_size` increases the resident state tensor shape, unlike
  the sequential QT/MPS seed loop. This is a resource smoke gate, not a metric. (c)
- claim scan: no production scalable backend claim, no dense-channel evidence
  claim, no new metric, no Axis-2 source-timeline claim. (a/c)

## Open Decisions

- Whether the production scalable multilevel carrier is qutrit-MPS first,
  dimension-polymorphic qudit-MPS first, or hybrid dense-window MCWF plus
  qutrit-MPS. (c)
- How to express mixed local dimensions in `Axis1CarrierProgram` without leaking
  evaluator-only mechanism truth into frontend schedule metadata. (c)
- Which leakage observable becomes the first ledgered validation surface; any new
  scored quantity must go through `docs/METRICS.md`. (c)

## Implementation Update: Contract And First Execution Slice

The first post-prereg slices have landed a contract surface and an executable
local-dimension MCWF/MPS slice behind `mcwf_mps_state_record`. This is still not
Axis-1 completion and introduces no new scored quantity. (a/c)

- `qt_mps_state_record` remains the restricted computational-subspace MPS line:
  useful GPU execution evidence, but currently product-channel / product-formula
  trajectory semantics rather than strict continuous-time MCWF. (a)
- `mcwf_mps_state_record` is the combined carrier contract: MCWF owns the
  same-substep trajectory unraveling of the summed `H_list` and `c_list`; MPS
  owns the pure-state representation; `local_dims` owns qubit/qutrit/ququart or
  mixed local Hilbert-space dimensions. (a/c)
- `axis1_carrier_execution_manifest(...,
  execution_backend_contract="mcwf_mps_state_record")` now delegates to
  `axis1_mcwf_mps_state_record_execution_manifest(...)` for the first
  fixed-microstep slice. Existing computational-subspace Hamiltonian/collapse
  families are lifted into declared `local_dims`, and measurement can preserve
  level records while emitting binary records through the declared leaked-readout
  policy. (a/c)
- Public Axis-1 instantaneous context now lowers the first one-site qutrit
  leakage families into the MCWF/MPS carrier path:
  `LEAK_EXCHANGE_12`, `LEAK_SEEP_21`, and `LEAK_HEAT_12`. These are current
  substep generator terms, not Axis-2 source timelines. (a/c)
- A later preregistered first transport slice also lowers compiler-generated
  two-site qutrit/ququart leakage-transport Hamiltonian families into the same
  MCWF/MPS carrier path:
  `LEAK_EXCHANGE_11_02`, `LEAK_MOBILITY_12_21`,
  `LEAK_TRANSPORT_30_12`, and `LEAK_TRANSPORT_31_22`. They require declared
  local levels through `local_dims` and fail closed when a qubit/qutrit
  declaration cannot represent the referenced level. This is sampled execution
  evidence, not dense exact channel evidence and not DQLR. (a/c)
- The same transport slice now lowers diagonal conditional leaked-neighbor phase
  Hamiltonians (`LEAK_COND_PHASE_LEFT2_RIGHTZ`,
  `LEAK_COND_PHASE_LEFTZ_RIGHT2`) from compiler-generated two-qubit substeps.
  They are grouped with other supported Hamiltonian terms on the same support
  before the microstep matrix exponential. This is not a Pauli/DEM projection,
  not a metric, and not a hardware-calibrated magnitude claim. (a/c)
- The MCWF/MPS path now sums supported Hamiltonian terms on the same support
  inside each microstep before applying a matrix exponential. This fixes the
  avoidable same-support sequential-Hamiltonian artifact for combinations such
  as `CTRL_CZ + LEAK_EXCHANGE_11_02`; Hamiltonian-vs-collapse splitting remains
  a finite-step MCWF approximation. (a/c)
- `axis1_qutrit_leakage_oracle_certification_manifest(...)` certifies that
  one-site qutrit `LEAK_*` lowering matches `leakage_channel_super` after
  explicit `dt` conversion. It is a dense oracle check for this first leakage
  slice, not a production carrier, not a metric, and not a serialized channel
  payload. (a/c)
- `axis1_two_site_leakage_hamiltonian_certification_manifest(...)` certifies
  first-slice two-site transport and conditional phase Hamiltonian lowering
  against an independent dense matrix exponential over declared local
  dimensions. It checks the same-support Hamiltonian block, not full record
  emission or collapse/no-jump MCWF error. (a/c)
- Mixed/qutrit/ququart finite-bond runs still fail closed until the
  mixed-dimension truncation ledger is implemented. Leakage-removal/DQLR
  protocol semantics, leakage-aware DEM/decoder integration, two-site dense
  record/channel certification, and production error-control policy are still
  unfinished. (c)
- This update adds no scored quantity and does not change `docs/METRICS.md`. (a)

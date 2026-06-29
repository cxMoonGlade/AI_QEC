# Axis-1 Leakage Transport And Removal Primitive Prereg

Status: theory-first preregistration, 2026-06-28. This document is written
before adding any two-site leakage-transport or leakage-removal primitive to
the Axis-1 frontend carrier. It does not claim Axis-1 completion, does not
modify `docs/METRICS.md`, and does not introduce a new scored quantity.

## 0. Current Repo State

- The Axis-1 frontend seam exists:
  `CircuitIR / CodeSpec -> SubstepSchedule / AnalogSubstepIR ->
  Axis1CarrierProgram -> MCWF/MPS execution or dense oracle evidence`. (a/c)
- One-site qutrit Wood-Gambetta-style leakage is already represented in public
  Axis-1 context and lowered to carrier terms:
  `LEAK_EXCHANGE_12`, `LEAK_SEEP_21`, and `LEAK_HEAT_12`. Dense
  computational-subspace channel evidence refuses to ignore those terms; the
  MCWF/MPS path executes them with declared `local_dims`. (a/c)
- The MCWF/MPS carrier is dimension-polymorphic in contract and first execution
  slice: qubit, qutrit, ququart, and mixed local dimensions are represented by
  `local_dims`. Finite-bond multilevel runs still fail closed until the
  discarded-weight ledger exists. (a/c)
- First-slice two-site leakage transport and conditional leaked-neighbor phase
  are now represented in the MCWF/MPS carrier through public instantaneous
  Axis-1 context. Leakage-removal/DQLR strategy semantics remain open. Existing
  Path-B transport notes and exact `QutritDM`/`QuquartDM` oracles are useful
  references, not a completed Axis-1 bridge. (a/c)

## 1. Grounding Ledger

| sub-item | source | local note / code | what is reused here | epistemic class |
|---|---|---|---|---|
| Leakage/seepage rates and coherent leakage | Wood & Gambetta, arXiv:1704.03081 | `docs/papers/reading_notes/wood_gambetta_leakage_characterization_1704.03081.md`; `src/qec_twin/forward/channels.py` | one-site qutrit leakage already built; `L1/L2/C_L` remain diagnostics unless METRICS admits them | (a/c) |
| Hardware leakage spread and removal phenomenology | McEwen et al., arXiv:2102.06131 | `docs/papers/reading_notes/mcewen_removing_leakage_correlated_2102.06131.md` | leakage persistence, reset/removal boundary, `pij` correlation as literature observable, not a new repo metric | (b/c) |
| DQLR and Sycamore transport numbers | Miao/McEwen et al., arXiv:2211.04728 | `docs/papers/reading_notes/miao_overcoming_leakage_scalable_2211.04728.md` | transport families, leaked-neighbor phase, removal null control; source note correction says use `g_eff = -2 sqrt(3) g^2 / eta`, not the stale `sqrt(2)g` body text | (b/c) |
| Implementable qutrit/ququart CZ-leakage channel and low-leakage gap | Varbanov et al., arXiv:2002.07119 | `docs/papers/reading_notes/varbanov_leakage_detection_surface_2002.07119.md`; `docs/twin_validation/leakage_transport_pathB_prereg.md` | qutrit `|11><->|02|`, conditional leaked phases, `|12><->|21|` mobility, ququart `|3>` enhancement | (a/b/c) |
| Scalable leakage simulation route | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md`; `src/qec_twin/simulator/axis1_mcwf_mps_execution.py` | MCWF trajectory semantics with MPS pure-state carrier and local physical dimension 3+ | (a/c) |

External identity checks used for this preregistration: arXiv pages for
2211.04728, 2002.07119, and 2308.08186 were re-opened on 2026-06-28. Detailed
equations and numbers are taken from the repo's committed full-text notes, not
from abstracts.

## 2. Axis Boundary

Axis-1 owns only the instantaneous generator terms inside one compiler substep:

- two-site Hamiltonian exchange or conditional phase active during the current
  two-qubit substep; (a/c)
- a current substep removal/control primitive if it is encoded as an
  instantaneous operator on the declared Hilbert space; (c)
- drift, burst, or calibration snapshots when their values are already supplied
  as current public parameters. (c)

Axis-2 owns the history:

- leakage persistence as a source process across cycles; (a/c)
- stochastic DQLR scheduling histories, reset failures, latent burst processes,
  and time-correlated drift that generates future Axis-1 parameter values. (a/c)

Therefore this slice may lower current two-site leakage Hamiltonians into
`H_list` for MCWF/MPS. It must not claim that a full DQLR/removal strategy or
cross-cycle leakage-memory process has been implemented.

## 3. Mechanism Families To Introduce

The first implementation slice should add carrier-level two-site Hamiltonian
families only. These are the smallest non-toy transport primitives because they
operate on the actual qutrit/ququart Hilbert space and are consumed in the same
MCWF substep as `ZZ`, `T1/T2`, controls, and one-site leakage.

### 3.1 Qutrit Arm

- `LEAK_EXCHANGE_11_02`: Hamiltonian
  `omega_11_02 (|11><02| + |02><11|)` on an ordered two-site support. This is
  the qutrit Varbanov leakage-source exchange associated with a CZ. The support
  order is public frontend operation order; orientation is a declared
  provenance field, not hidden evaluator truth. (a/c)
- `LEAK_MOBILITY_12_21`: Hamiltonian
  `omega_12_21 (|12><21| + |21><12|)`. This is the qutrit mobility arm; in the
  low-leakage regime its logical impact is predicted to be second-order in the
  leaked population. (b/c)
- Conditional leaked-neighbor phase is registered as a separate first-class
  Hamiltonian family:
  `LEAK_COND_PHASE_LEFT2_RIGHTZ` applies a computational `Z` Hamiltonian on the
  right site conditioned on the ordered left site being in level `2`;
  `LEAK_COND_PHASE_LEFTZ_RIGHT2` applies the reverse orientation. These are
  diagonal two-site Hamiltonian terms, not Pauli/DEM projections. (b/c)

### 3.2 Ququart Arm

The ququart arm is needed when the mechanism uses level `|3>`. The carrier
should allow these terms only when the declared local dimensions support the
referenced levels:

- `LEAK_TRANSPORT_30_12`: Hamiltonian
  `omega_30_12 (|30><12| + |12><30|)`. (b/c)
- `LEAK_TRANSPORT_31_22`: Hamiltonian
  `omega_31_22 (|31><22| + |22><31|)`. (b/c)
- `LEAK_SUPER_12_03`: Hamiltonian
  `omega_12_03 (|12><03| + |03><12|)`. (b/c)
- `LEAK_TRANSPORT_03_21`: Hamiltonian
  `omega_03_21 (|03><21| + |21><03|)`. (b/c)

These are not Pauli/GF(2) schedules and not DEM-level rate tweaks. They are
ordinary Hilbert-space Hamiltonian terms that MCWF/MPS can apply to a pure-state
trajectory.

## 4. `dt` And Unit Policy

- Carrier coefficients are instantaneous angular rates in rad/ns. The executed
  microstep angle is `theta = omega_rad_per_ns * dt_micro_ns`. (a)
- If a literature number is a per-gate population transport fraction `P_t`, it
  must be converted before use:
  `theta = asin(sqrt(P_t))` for a two-level exchange block, then
  `omega_rad_per_ns = theta / dt_gate_ns`. This conversion is exact for the
  ideal two-state exchange block, while the selected `P_t` value is a prediction
  band / hardware-specific parameter. (a/b/c)
- Conditional phase context fields are `Z` Hamiltonian coefficients in rad/ns.
  For `LEAK_COND_PHASE_LEFT2_RIGHTZ`, the right-site `|0>` and `|1>` levels get
  `+omega` and `-omega` while the left site is in `|2>`, so a quoted relative
  leaked-neighbor phase `phi_rel` over one gate converts as
  `omega_rad_per_ns = phi_rel / (2 * dt_gate_ns)`. The same convention applies
  to the reverse orientation. The conversion is exact for this diagonal block;
  the selected `phi_rel` is literature/device parameter evidence, not a metric.
  (a/b/c)
- No per-cycle dimensionless parameter may be silently reused as a per-ns rate.
  A wrong-unit negative control should remain part of certification when dense
  tiny-window checks are added. (a/c)

## 5. Initial Treatment Of Removal

DQLR / multi-level reset is a protocol, not a single generic noise rate. Initial
Axis-1 treatment:

- a measurement/reset boundary may map leaked levels back to computational reset
  targets only through declared reset/instrument policy; (a/c)
- a future `LEAKAGE_ISWAP_REMOVAL` primitive may be represented as a two-site
  Hamiltonian on `|20><11| + h.c.` or the appropriate device-specific subspace
  only when the corresponding operation appears in the schedule; (c)
- current code must not claim full leakage removal, full DQLR, or
  leakage-removal null-control completion. (a)

The first transport slice can therefore include `LEAK_EXCHANGE_11_02` and
ququart transport Hamiltonians without claiming DQLR.

## 6. Observable And Metric Boundary

No new metric is introduced here. All quantities below are verification gates or
prediction bands:

- support/dimension validation: exact program validation gate; (a)
- norm preservation for Hamiltonian-only two-level exchange: exact unitary
  sanity gate within numerical tolerance; (a/c)
- seeded MCWF/MPS level-record behavior: heuristic execution gate; (c)
- literature transport fractions, leaked-neighbor phase, and DQLR null-control
  behavior: prediction bands unless later registered in `docs/METRICS.md`; (b/c)
- Wood-Gambetta `L1/L2/C_L`: field-standard diagnostics in literature, but not
  scored by this repo until the METRICS ladder admits their use. (a/c)

Any future headline score must go through `docs/METRICS.md`. This prereg can
only support code-correctness and anti-toy acceptance, not a new scientific
metric.

## 7. Anti-Toy Tests For The First Code Slice

The first implementation should satisfy all of these before any broader claim:

- A compiler-generated two-qubit substep with public Axis-1 leakage-transport
  context emits `LEAK_EXCHANGE_11_02` and/or `LEAK_MOBILITY_12_21` carrier terms.
  A hand-written fake schedule is not sufficient evidence. (a/c)
- A qutrit MCWF/MPS run starting from `|11>` under `LEAK_EXCHANGE_11_02` can
  produce level record `[0, 2]` after measurement, without projecting the carrier
  back to the computational subspace. (c)
- The same term on `local_dims=(2,2)` fails closed with a dimension error rather
  than silently dropping the transport term. (a)
- A ququart transport term such as `LEAK_TRANSPORT_30_12` is accepted only when
  the required local level `3` exists, and fails closed on qutrit-only dims. (a)
- A same-substep qutrit transport + one-site leakage + `T1/T2/ZZ` manifest shows
  the terms in one carrier substep; it must not route transport as a sequential
  finite-channel composition. (a/c)
- Claim scans must find no statement that this slice completes Axis-1, completes
  DQLR/removal, emits dense exact channel evidence for over-cap MCWF/MPS runs, or
  changes METRICS. (a)

## 8. Open Risks And Decisions

- Orientation: literature transport channels are device/gate-orientation
  dependent. The first slice may use frontend operation target order as public
  orientation, but any hardware-faithful claim needs an explicit orientation
  calibration. (c)
- Conditional phase: first-slice diagonal conditional phase is now implemented
  with ordered frontend orientation. A hardware-faithful magnitude/orientation
  claim still needs explicit calibration or a preregistered fixture parameter.
  (c)
- Ququart cost: ququart dense or exact-DM oracles are small-window only. MCWF/MPS
  can represent ququart local dimensions, but finite-bond production error
  control is still not complete. (a/c)
- Removal semantics: full DQLR is a schedule/protocol feature, not just an
  operator family. It should get a separate prereg before implementation. (c)
- Metric admission: do not add `L1/L2/C_L`, `pij`, detector-rise, or transport
  fraction scores to project results until `docs/METRICS.md` explicitly permits
  the convention. (a)

## 9. Implementation Update

Landed after this preregistration:

- `Axis1LocalLindbladContextSpec` now carries public instantaneous two-site
  leakage-transport rates:
  `leak_exchange_11_02_rad_per_ns`, `leak_mobility_12_21_rad_per_ns`,
  `leak_transport_30_12_rad_per_ns`, and
  `leak_transport_31_22_rad_per_ns`. They are metadata only: no operator
  payload, no serialized channel, and no Axis-2 source timeline. (a/c)
- `Axis1CarrierProgram` emits `LEAK_EXCHANGE_11_02`,
  `LEAK_MOBILITY_12_21`, `LEAK_TRANSPORT_30_12`, and
  `LEAK_TRANSPORT_31_22` only from compiler-generated two-qubit substeps, using
  ordered frontend operation targets as the public orientation policy. (a/c)
- `axis1_mcwf_mps_state_record_execution_manifest(...)` executes those families
  as two-site Hamiltonian exchange blocks in the fixed-microstep MCWF/MPS path.
  Qutrit/ququart level requirements are checked against `local_dims`; qubit or
  qutrit-only declarations fail closed when a referenced level is absent. (a/c)
- The MCWF/MPS path now sums same-support Hamiltonian terms before applying the
  microstep unitary. Thus a transport term in the same compiler substep as
  `CTRL_CZ` is executed as `exp(-i(H_CTRL_CZ + H_transport)dt_micro)`, not as
  sequential `CZ` then transport. (a/c)
- Anti-toy tests cover compiler-generated carrier lowering, qutrit
  `|11> -> |02>` level-record evidence, qubit-dimension fail-closed behavior,
  ququart `|12> -> |30>` transport with qutrit-only rejection, and conditional
  phase lowering/grouping through a compiler-generated two-qubit substep. These
  are verification gates, not metrics. (a/c)
- `axis1_two_site_leakage_hamiltonian_certification_manifest(...)` now certifies
  first-slice two-site transport and conditional phase Hamiltonian lowering by
  comparing the MCWF/MPS same-support Hamiltonian group against an independently
  constructed dense two-site matrix exponential over declared qutrit/ququart
  `local_dims`. It also carries a wrong-unit negative control for treating
  public per-ns leakage rates as dimensionless angles. This is a verification
  gate, not dense channel evidence, not a channel payload, and not a metric.
  (a/c)

Still not implemented:

- leakage-removal/DQLR protocol semantics;
- dense two-site record/channel certification beyond the Hamiltonian-block gate;
- finite-bond multilevel production error control;
- any METRICS-ledger score for leakage transport or removal. (c)

Conditional-phase implementation update:

- `Axis1LocalLindbladContextSpec` now also carries
  `leak_cond_phase_left2_right_z_rad_per_ns` and
  `leak_cond_phase_left_z_right2_rad_per_ns` as public instantaneous Axis-1
  context fields. (a/c)
- `Axis1CarrierProgram` emits `LEAK_COND_PHASE_LEFT2_RIGHTZ` and
  `LEAK_COND_PHASE_LEFTZ_RIGHT2` on compiler-generated two-qubit operation
  supports. The ordered-support orientation is public provenance. (a/c)
- The MCWF/MPS path executes them as diagonal two-site Hamiltonian terms inside
  the same support-group matrix exponential as controls, ZZ, and transport.
  This is still sampled finite-step execution evidence, not a metric and not a
  dense channel payload. (a/c)

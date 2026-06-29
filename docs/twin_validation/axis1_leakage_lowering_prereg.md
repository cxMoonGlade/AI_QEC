# Axis-1 Leakage Lowering Into MCWF/MPS Prereg

Status: theory-first preregistration plus first implementation ledger,
2026-06-28. The preregistration was written before adding registered leakage
mechanism lowering to the Axis-1 carrier. It does not claim Axis-1 completion
and does not add a metric.

## 0. Grounding Ledger

| sub-axis / mechanism | mechanism paper | observable / simulator paper | reading note | in-repo code to reuse |
|---|---|---|---|---|
| qutrit leakage, seepage, coherent leakage | Wood & Gambetta, arXiv:1704.03081 | Wood & Gambetta `L1`, `L2`, `C_L`; METRICS ledger decision still required before scored use | `docs/papers/reading_notes/wood_gambetta_leakage_characterization_1704.03081.md` | `src/qec_twin/forward/channels.py:leakage_kraus`, `leakage_channel_super`; `src/qec_twin/mechanisms/qutrit_teachers.py:wg_rates`, `coherence_of_leakage` |
| qutrit MPS trajectory carrier | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | qutrit MPS pure-state trajectories, Kraus sampling, measurement record production, discarded-weight policy | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md` | `src/qec_twin/simulator/axis1_mcwf_mps_execution.py`, `src/qec_twin/simulator/mcwf_backend.py` |
| hardware leakage rates and transport | McEwen et al., arXiv:2102.06131; Miao/McEwen et al., arXiv:2211.04728 | detector tails, `pij` correlations, transport/phase phenomenology; not this slice's scored surface | `docs/papers/reading_notes/mcewen_removing_leakage_correlated_2102.06131.md`, `docs/papers/reading_notes/miao_overcoming_leakage_scalable_2211.04728.md` | `src/qec_twin/forward/scalable/sv_sampler.py:leak_slice_kraus_torch` |

## 1. Current State

- `mcwf_mps_state_record` now executes fixed-microstep MCWF/MPS trajectories
  over declared `local_dims`, including qutrit/ququart carrier states. Existing
  computational-subspace families are lifted into multilevel sites. (a/c)
- The implementation now lowers one-site qutrit Wood-Gambetta-style exchange,
  seepage, and heating into the MCWF/MPS carrier path via public Axis-1
  instantaneous context. A later preregistered first slice also lowers
  compiler-generated two-site qutrit/ququart leakage-transport and conditional
  leaked-neighbor phase Hamiltonian families into the same MCWF/MPS path.
  Leakage-removal/DQLR protocol semantics are not yet implemented. (a/c)
- Multilevel finite-bond runs fail closed until a mixed-dimension discarded-weight
  ledger exists. (a/c)

## 2. Mechanism To Lower

The first registered Axis-1 leakage family should be the one-site qutrit
Wood-Gambetta generator already used by the repo's qutrit teachers:

- Hamiltonian exchange:
  `H_leak = omega_12_rad_per_ns (|1><2| + |2><1|)` on a qutrit site. (a/c)
- Seepage collapse:
  `c_seep = sqrt(g_seep_per_ns) |1><2|`. (a/c)
- Heating/leakage collapse:
  `c_heat = sqrt(g_heat_per_ns) |2><1|`. (a/c)

The repo's existing `leakage_kraus(theta, g_seep, g_heat)` parameterizes the
unit-time channel by `theta`, `g_seep`, and `g_heat`. The Axis-1 lowering must
not silently reinterpret those dimensionless per-cycle values as per-ns rates.
The source of any conversion must be explicit: either a declared substep rate
already in per-ns units, or a preregistered fractional-cycle policy. (a/c)

Candidate carrier family names for implementation:

- `LEAK_EXCHANGE_12` — Hamiltonian, coefficient in rad/ns; (c)
- `LEAK_SEEP_21` — collapse, coefficient `sqrt(rate_per_ns)`; (c)
- `LEAK_HEAT_12` — collapse, coefficient `sqrt(rate_per_ns)`. (c)

These families are Axis-1 only when the values are the instantaneous generator
terms for the current substep. A stochastic process that generates the values
across cycles remains Axis-2. (a/c)

## 3. Observable And Metric Boundary

Wood-Gambetta `L1`, `L2`, and `C_L` are the field-standard leakage diagnostics
for qutrit leakage. However, they are not yet in this repo's `docs/METRICS.md`
ledger. Therefore this implementation slice may use them only as mechanism
diagnostics or exact-code cross-checks unless and until the ledger is extended by
the METRICS ladder. (a)

The first implementation tests should remain verification gates, not new scores:

- matrix lowering identity against the registered qutrit algebra; (a)
- exact one-site dense qutrit channel comparison against
  `leakage_channel_super` for a tiny fixture; (a/c)
- sampled MCWF/MPS level-record smoke with explicit `rng_seed`; (c)
- no production, decoder, DEM, Axis-2, or exact continuous-time MCWF claim. (a)

## 4. Independent Ground Truth

Non-circular ground truth for the first slice:

- For operator lowering: closed-form qutrit matrices
  `|1><2| + |2><1|`, `|1><2|`, and `|2><1|`. (a)
- For channel semantics: `src/qec_twin/forward/channels.py:leakage_channel_super`
  and `leakage_kraus`, which already encode the Wood-Gambetta Lindbladian
  algebra. (a/c)
- For trajectory record behavior: deterministic level-preservation and seeded
  sampled trajectory gates on compiler-generated schedules. These are execution
  gates, not metrics. (c)

## 5. Bounded Simplifications

- Fixed-microstep MCWF is a finite-step approximation, not exact continuous-time
  unraveling. (c)
- A finite-Kraus Wood-Gambetta channel must not be inserted sequentially beside
  other same-substep mechanisms and then called exact Axis-1 joint-L evidence.
  Same-substep leakage must lower to `H_list`/`c_list` when combined with other
  Axis-1 generator terms. (a)
- Leakage persistence across cycles, burst histories, source-driven drift, and
  transport histories are Axis-2 unless their current substep values are supplied
  as instantaneous Axis-1 parameters. (a/c)
- First slice may omit two-site transport and conditional leaked-neighbor phase;
  that omission must be explicit and cannot support a hardware-complete leakage
  claim. (c)

## 6. Anti-Toy Tests For The Next Code Slice

- Compiler-generated qutrit schedule plus leakage context emits carrier terms
  `LEAK_EXCHANGE_12`, `LEAK_SEEP_21`, and/or `LEAK_HEAT_12`; handwritten fake
  schedules remain rejected by existing seal gates. (a/c)
- A one-qutrit `|1>` initial state with exchange-only leakage produces nonzero
  observed `level_records=[2]` under seeded MCWF/MPS sampling, without projecting
  the state back to the qubit subspace. (c)
- A `|2>` initial state with seepage-only collapse can return `level_records=[1]`
  under seeded MCWF/MPS sampling. (c)
- A same-substep schedule containing leakage plus `T1/T2/RD/ZZ` consumes all
  collapse candidates through the joint MCWF jump competition path, not through
  sequential finite-channel composition. (a/c)
- Mixed `local_dims` with finite `max_bond` continues to fail closed until the
  mixed-dimension truncation ledger exists. (a)

## 7. Decisions Needed Before Coding

- Public leakage parameters currently live in `Axis1LocalLindbladContextSpec` as
  instantaneous Axis-1 generator parameters:
  `leak_exchange_12_rad_per_ns`, `leak_seep_21_per_ns`, and
  `leak_heat_12_per_ns`. This is public context metadata only; it is not a
  serialized operator payload and not an Axis-2 source history. (a/c)
- Whether to add Wood-Gambetta `L1`, `L2`, and `C_L` to `docs/METRICS.md` before
  reporting any leakage-specific scored quantity. (c)
- Whether first transport support is deferred or represented as a separate
  two-site qutrit/ququart family grounded in Miao/McEwen. (c)

## 8. Implementation Ledger

Landed after preregistration:

- `Axis1CarrierProgram` emits `LEAK_EXCHANGE_12`, `LEAK_SEEP_21`, and
  `LEAK_HEAT_12` terms from compiler-generated schedules carrying public
  Axis-1 context. The provenance marks the values as public instantaneous
  context, not Axis-2 source truth. (a/c)
- `axis1_mcwf_mps_state_record_execution_manifest(...)` consumes those families
  in the fixed-microstep MCWF/MPS path. `LEAK_EXCHANGE_12` acts as a one-site
  qutrit Hamiltonian on levels `1` and `2`; `LEAK_SEEP_21` and
  `LEAK_HEAT_12` are collapse operators in the same joint jump competition as
  other same-substep collapse terms. (a/c)
- Tests cover compiler-generated qutrit leakage term emission, qutrit exchange
  level-record behavior, qutrit seepage jump behavior, and preservation of the
  mixed-dimension finite-bond fail-closed policy. They also assert that dense
  computational-subspace evidence refuses leakage context instead of silently
  dropping qutrit terms. These are verification gates, not scored metrics.
  (a/c)
- `axis1_qutrit_leakage_oracle_certification_manifest(...)` now compares the
  one-site carrier `LEAK_*` qutrit generator against
  `leakage_channel_super(theta, g_seep, g_heat)`, with explicit conversion from
  per-ns Axis-1 parameters to dimensionless oracle parameters
  `theta = omega_12 * dt_ns`, `g_seep = rate_seep * dt_ns`, and
  `g_heat = rate_heat * dt_ns`. It also carries a wrong-unit negative control.
  This is a verification gate, not a metric or channel payload. (a/c)
- The MCWF/MPS record path now has an anti-toy repeated-boundary test:
  a leaked qutrit measured with `MR` records the leaked level/readout bit,
  resets into the computational state, and a second measurement receives its own
  measurement key and post-reset level. This is record-boundary execution
  evidence, not DEM/decoder integration. (a/c)
- After `axis1_leakage_transport_removal_prereg.md`, `Axis1CarrierProgram`
  also emits the first two-site leakage-transport and conditional
  leaked-neighbor phase Hamiltonian families from compiler-generated two-qubit
  substeps carrying public Axis-1 context:
  `LEAK_EXCHANGE_11_02`, `LEAK_MOBILITY_12_21`,
  `LEAK_TRANSPORT_30_12`, `LEAK_TRANSPORT_31_22`,
  `LEAK_COND_PHASE_LEFT2_RIGHTZ`, and `LEAK_COND_PHASE_LEFTZ_RIGHT2`. The
  MCWF/MPS executor applies transport terms as ordered two-level exchange
  blocks and conditional phase terms as diagonal two-site Hamiltonians over
  declared qutrit/ququart `local_dims`; dimension mismatches fail closed. This
  is sampled level-record execution evidence only, not dense channel evidence,
  not DQLR, and not a metric. (a/c)
- `axis1_two_site_leakage_hamiltonian_certification_manifest(...)` now compares
  those first-slice two-site Hamiltonian groups against an independently
  constructed dense qutrit/ququart matrix exponential, with a wrong-unit
  negative control. This certifies Hamiltonian-block lowering only; it is not
  record evidence, channel payload, DQLR, or a metric. (a/c)

Still open:

- leakage-removal/DQLR protocol semantics;
- dense record/channel certification beyond the two-site Hamiltonian-block gate;
- leakage-aware reset/readout policy beyond the declared leaked-readout binary
  mapping;
- finite-bond mixed-dimension error-control policy;
- any Wood-Gambetta `L1/L2/C_L` scored use, which still requires a
  `docs/METRICS.md` ledger decision. (c)

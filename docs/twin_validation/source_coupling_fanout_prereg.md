# Source Coupling Fan-Out Preregistration

> **Historical implementation preregistration; superseded as a production bridge status
> (2026-07-13).** The old `src/qec_twin/...` path and the single ten-field fan-out described below
> are not the current package contract. The live code has separate source/fan-out components and
> carrier objects, but the source-to-full-record production bridge remains `OPEN / CODE_BLOCKED`.
> Use
> [`production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md`](production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md)
> and [`../SIMULATOR.md`](../SIMULATOR.md) for the current A/B split and claim boundary. The
> parameter values below remain project design choices unless independently sourced.

**Status:** implementation prereg for `src/qec_twin/mechanisms/source_coupling.py`.
This is the Axis-2 parameter fan-out layer `Theta(z_t)` from the coupling
simulator contract. It is not a record-level G4/G6 result by itself.

This document is not a fresh literature review. It is an implementation binding
for theory-first material already prepared in this project.

## Grounding Inputs

- `docs/twin_validation/full_error_coupling_prereg.md` §0, §0.1, §5:
  the owned coupling is an explicit memoryful source, not a sum of non-negative
  Markovian Lindblad rates; one latent draw must feed every affected parameter
  map, and the independent-per-mechanism baseline must collapse correlation.
- `docs/twin_validation/nonmarkovian_coupling_constraint_ledger.md` C1-C10:
  RTN/1/f source physics, motional narrowing, CP-divisibility, fair baseline,
  and source-vs-record claim boundaries.
- `docs/twin_validation/qec_coupling_simulator_build_contract.md` §B-3 and §E:
  `Theta(z_t)` must be a physical fan-out into multiple mechanism parameters,
  including slice-1 qubit-window hooks and the G6 shared-vs-independent control.
- `docs/twin_validation/h2_effectsize_g4_prereg.md` §7.B:
  data-qubit ZZ/T2 drift alone is Kam Class 0 and record-benign; therefore this
  fan-out must also preserve Class-1 SPAM and Class-2 CZ hooks for the later
  record-faithfulness slice.
- `docs/papers/reading_notes/kam_nonmarkovian_surface_code_2410.23779.md`:
  multi-time Class-1/2 streak structure is the load-bearing record-level
  hazard; 2-point correlations alone are insufficient.
- `docs/papers/reading_notes/bhardwaj_drifting_noise_estimation_2511.09491.md`:
  rate drift is a separate, carrier-implementable time-dependent marginal-rate
  axis; its decode-relevant observable is static-DEM LER penalty / recovery of
  `p(t)`, not a pairwise round-correlation claim.
- `outputs/teacher_prereg/qutip_teacher_source.py`: reusable formula pattern for
  `_phi_to_J`, `_B_to_gamma_burst`, and rate-to-physical-parameter maps. The
  package implementation copies only the pure formula pattern into `src/`; it
  does not import from `outputs/`.

## Object

Input: one explicit source draw `z_t`, interpreted as a frequency-like drift
sample in rad/ns from the validated RTN/1/f source layer.

Output: a mechanism-parameter bundle for the same cycle/substep. The same draw
feeds multiple parameters:

| output field | map | class |
|---|---|---|
| `zz_phi_rad`, `zz_zeta_radns` | static-ZZ Duffing formula with fixed `J`, recomputing zeta at `Delta + z_t` | (a) formula, (c) constants |
| `detuning_radns` | additive frequency detuning `base + z_t` | (a) algebra |
| `gamma_phi_per_ns`, `tphi_ns` | positive log-rate modulation of pure-dephasing rate | (c) design |
| `drive_omega_radns` | positive log-rate modulation of drive amplitude | (c) design |
| `spillover_cx` | logit probability modulation | (c) design |
| `readout_flip_p`, `reset_flip_p` | logit probability modulation for Class-1 SPAM hooks | (c) design |
| `cz_depol_p` | logit probability modulation for Class-2 gate hook | (c) design |

The exact static-ZZ formulas are the same closed-form family used by the
existing qutip-source adaptor pattern:

`zeta = 2 J^2 [1/(Delta-alpha) - 1/(Delta+alpha)]`,
`phi = zeta * t_gate / 4`.

The log-rate/logit maps are declared design maps. They are monotone, preserve
positive rates and probability bounds, and are not claimed as calibrated
hardware laws.

## Controls

1. `trajectory_to_params(z_t)` is the shared-source path: every mechanism field
   at cycle `t` is conditioned on the same `z_t`.
2. `independent_baseline_trajectory_to_params(z_t, seed)` preserves each field's
   marginal source draws but independently permutes draws per field. This is the
   G6-style negative control: cross-mechanism same-cycle correlation should
   collapse while one-field marginals remain unchanged.

## Anti-Laundering Boundary

This layer emits evaluator-side parameter bundles only. It does not write
`.stim`, `.dem`, or learner-visible records. Stim/Pauli frontend noise remains
in `qec_twin.simulator.noise`; analog/leakage/source truth remains sidecar or
backend-owned.

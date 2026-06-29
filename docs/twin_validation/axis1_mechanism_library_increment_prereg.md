# Axis-1 Mechanism Library Increment Prereg

Date: 2026-06-28

Status: preregistration plus implementation evidence for the first Axis-1
mechanism-library increment. This is not a claim that the full coupled QEC
teacher is complete.

## Current Repo State

- Axis-1 schedule/bridge exists:
  `CircuitIR` / `CodeSpec` -> `SubstepSchedule` / `AnalogSubstepIR` ->
  schedule-derived mechanism selections -> one
  `forward.joint_lindbladian.assemble_substep_channel(...)` call per selected
  local or union-support window. (a)
- The current primitive library is intentionally narrow:
  `DR/ZZ/T2/T1/T1_UP/T2_B/T1_B/T1_UP_B/RD/RD_B/FSIM_SWAP/FSIM_PHASE`, plus
  exact ideal frontend `CTRL_*` Hamiltonians for supported one- and two-qubit
  gates. (a/c)
- Public `Axis1LocalLindbladContextSpec` can override local Markovian rates,
  select computational-subspace thermal excitation, and request
  computational-subspace fSim residual Hamiltonian primitives. It is public
  context, not Axis-2 source truth and not a serialized channel payload. (a/c)
- Static-ZZ metadata is public schedule metadata. The selection plan records
  declared active-pair static-ZZ provenance without lowering a second active `ZZ`
  term. (a/c)
- Dense Choi reconstruction now keeps every positive Choi eigenvalue by default.
  The 5-qubit CodeSpec audit has no dropped-mass warnings, maximum TP residual
  `8.216e-15`, and maximum Kraus rank `636`; this is a dense-carrier cost
  diagnostic, not a ledgered physical metric. (a/c)

## Literature Grounding

- Foxen et al., arXiv:2001.08343, cached note
  `docs/papers/reading_notes/foxen_fsim_twoqubit_gateset_2001.08343.md`:
  fSim is the two-qubit model with swap angle `theta` and conditional phase
  `phi`; calibrated coherent residual is purity-limited and small, while leakage
  is the dominant fSim error. (a/c)
- Pettersson Fors et al., arXiv:2408.15402, cached note
  `docs/papers/reading_notes/pettersson_fors_zz_coupling_comprehensive_2408.15402.md`:
  residual ZZ is a cross-Kerr/conditional-phase Hamiltonian with
  `phi = integral zeta(t) dt`; modern residual brackets are far below strong-ZZ
  / near-CZ probes. (a/b/c)
- Heinsoo et al., arXiv:1801.07904, cached note
  `docs/papers/reading_notes/heinsoo_multiplexed_readout_crosstalk_1801.07904.md`:
  readout crosstalk is classical correlated assignment plus measurement-induced
  dephasing, with protected simultaneous-vs-individual readout error within
  about 1 percent on that device. (b/c)
- Bravyi et al., arXiv:1710.02270, and Marton-Asboth, arXiv:2303.04672, cached
  notes define the coherent logical-error metric ladder: Bravyi `P_L` for pure
  coherent rotations, Marton-Asboth max-infidelity as the preferred coherent +
  readout surface metric. These are surface-code metrics, not current small
  Axis-1 artifact evidence. (a/c)
- Sarovar et al., arXiv:1908.09855, cached note grounds the crosstalk taxonomy
  and conditional-independence/CMI observable; coherent crosstalk can be
  syndrome-suppressed while incoherent readout/detection crosstalk is directly
  visible as a record moment. (a/b/c)

## Adopt / Do Not Adopt

Adopt:

- Add fSim coherent residual as an optional active-pair Axis-1 Hamiltonian
  primitive family. In the computational subspace, use
  `H_swap = |01><10| + |10><01|` and `H_phase = |11><11| = n_a n_b`, with
  coefficients `delta_theta_rad / dt` and `delta_phi_rad / dt`. This reproduces
  the fSim residual unitary `exp(-i delta_theta H_swap) exp(-i delta_phi n_a n_b)`
  because the two generators commute on the computational two-qubit subspace. (a)
- Keep residual static-ZZ as the existing `ZZ` Hamiltonian form and use public
  context `zeta_rad_per_ns` for magnitude policy. Modern residual values are
  prediction-band/context choices, not exact constants. (a/b/c)
- Keep measurement-induced readout dephasing as `RD/RD_B` in the joint-L readout
  window. Keep correlated readout assignment as a classical record/instrument
  layer (`Axis1ReadoutResetInstrumentSpec`), not as an analog Lindblad term. (a/c)

Do not adopt in this slice:

- No qutrit/leakage fSim `|11> <-> |02>` integration. Foxen says leakage is
  dominant, but this computational-subspace Axis-1 slice must not silently claim
  leakage. (a/c)
- No Axis-2 source/memory expansion. Context rate overrides remain public
  Markovian context, not source truth. (a)
- No DEM/decoder claim for joint-L records. `.b8` sample carriers remain
  record-carrier artifacts without `.dem` semantics. (a/c)
- No large-surface coherent logical metric claim from this small local slice.
  Bravyi/Marton metrics define future surface validation, not current local
  channel evidence. (a/c)

## Implemented Minimal Fields

`Axis1LocalLindbladContextSpec` now includes:

- `include_fsim_residual: bool = False` (c)
- `fsim_delta_theta_rad: float = 0.0` (c)
- `fsim_delta_phi_rad: float = 0.0` (c)

`Axis1PrimitiveParams` now includes:

- `fsim_delta_theta_rad`
- `fsim_delta_phi_rad`

Extend primitive registry:

- `FSIM_SWAP`: Hamiltonian, support `(0, 1)`,
  coefficient `fsim_delta_theta_rad / dt_ns`. (a/c)
- `FSIM_PHASE`: Hamiltonian, support `(0, 1)`,
  coefficient `fsim_delta_phi_rad / dt_ns`. (a/c)

The default context must keep these disabled/zero so existing schedules do not
claim fSim residual unless public metadata requests it. (a)

## dt / Bracket Policy

- The fSim residual coefficients are area-preserving: coefficient is residual
  angle divided by the selected substep duration. (a)
- The active pair uses the same `dt_ns_nominal` / `dt_ns_bracket` as the frontend
  two-qubit gate substep. (a)
- Registered magnitude bands:
  - fSim coherent residual: bounded-negligible after calibration, class (c)
    gate, with residual magnitudes swept rather than frozen. Foxen's inferred
    coherent residual around `7e-5` is an inference from error minus purity, not
    a theorem. (c)
  - static-ZZ modern residual: `zeta` / `phi` brackets are prediction bands from
    Pettersson Fors plus modern residual measurements; old strong-ZZ probes must
    be labeled amplified/fixed-coupling, not residual default. (b/c)
  - readout crosstalk assignment: bracketed around protected sub-percent to
    ~1 percent record-level pair-correlation gates; not a Lindblad rate. (b/c)

## Initial Handling By Substep Type

- Two-qubit gate:
  - If `include_fsim_residual` is true and the row is an active-pair two-qubit
    control row, append `FSIM_SWAP` and/or `FSIM_PHASE` to the active pair's
    local primitive bundle. (a/c)
  - Keep ideal frontend control separate as `CTRL_*`. Residual fSim is an error
    primitive, not the ideal gate. (a)
- One-qubit gate:
  - No fSim residual. Static-ZZ spectator clusters and local `T1/T2` remain as
    currently implemented. (a)
- Idle:
  - No fSim residual. Static-ZZ and local `T1/T2` remain. (a)
- Measurement/readout:
  - `RD/RD_B` remain analog dephasing primitives.
  - Classical correlated assignment remains in the record/instrument layer. (a)
- Reset:
  - Reset remains a boundary/instrument operation, not a GKSL lowering in this
    slice. (a/c)

## Axis-1 Bridge Call

The bridge must still lower all selected ideal controls plus selected local
primitives into one `H_list, c_list` for the substep and call:

```python
assemble_substep_channel(H_list, c_list, dt_ns, device="cuda")
```

No implementation may replace this with sequential `E_ideal o E_fsim o E_T1`.
The fSim residual is specifically an Axis-1 same-substep Hamiltonian term in the
joint generator. (a)

## Anti-Toy Tests

Implemented before accepting this slice:

- GPU-only visibility gate: fail collection or fail test if CUDA is unavailable;
  no CPU-only circuit acceptance. (a)
- Exact fSim residual unitary oracle: with only `FSIM_SWAP/FSIM_PHASE` and no
  collapse operators, the assembled channel action matches the closed-form
  computational-subspace fSim residual matrix for at least two nonzero
  `(delta_theta, delta_phi)` settings. (a)
- Default-zero invariance: default schedules do not emit fSim residual primitive
  rows and do not change frozen default G2/CodeSpec hashes except when the
  implementation intentionally changes manifest schema. (a/c)
- Context positive control: a compiler-generated two-qubit substep with public
  fSim residual context emits `FSIM_SWAP` and/or `FSIM_PHASE` in
  `lowered_mechanisms`, and the row still contains one joint-L assembly summary.
  (a/c)
- Bad composition caught: a direct comparison against sequential composition
  of `FSIM_SWAP x T2` disagrees at a registered nonzero case; the joint-L path
  is the reference. (a/b)
- Readout boundary guard: correlated readout assignment tests must live in
  record/instrument evidence and must not appear as `H_list/c_list` analog
  primitives. (a)

## Implementation Evidence

- GPU tests:
  `conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py tests/test_joint_lindbladian.py`
  -> `101 passed in 48.20s`. This is a GPU-gated test result, not a CPU-only
  release basis. (a/c)
- fSim residual positive-control channel artifact:
  `outputs/twin_validation/axis1_fsim_residual_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_fsim_residual_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `1059321eabca0cf3576a0d8320688baa9034294650acfd71d18d064d0b21e904`.
  Exact file sha256:
  `ea91b66e7b5866a86ec64baf161c59c788780d08e8d8ae4797f867db275bfa20`.
  Exact freeze-file sha256:
  `23303275e4b68d477e59f03af30bf98c14e350aeacccf2814f5738a5b3fbadd5`.
  These hashes are artifact identity checks, not physics conclusions. (a/c)
- Default G2/CodeSpec hashes were intentionally refreshed because the primitive
  registry manifest now advertises `FSIM_SWAP/FSIM_PHASE`; default selector rows
  still do not emit fSim residual primitives unless public fSim context requests
  them. (a/c)

## Open Risks / Decisions

- Mechanism scope: fSim residual covers computational-subspace coherent residual
  only; leakage-dominant fSim physics remains out of scope. (a/c)
- Magnitude policy: realistic residual fSim and residual static-ZZ may be too
  small for small local anti-toy artifacts unless amplified positive controls are
  explicitly labeled. (b/c)
- Record observables: readout pairwise correlation is a record-level observable;
  any scored quantitative claim about it must first go through
  `docs/METRICS.md`. (c)
- Dense carrier: fSim residual adds Hamiltonian terms but does not solve the
  5-local-qubit dense support cap. Scalable-carrier research remains a separate
  blocker. (c)

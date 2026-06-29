# Axis-1 Static-ZZ Edge Calibration Prereg

Date: 2026-06-28

Status: preregistration for the next Axis-1 mechanism-library increment. This
is not a claim that the full coupled QEC teacher is complete.

## Motivation

The current Axis-1 bridge represents declared static-ZZ support with public
`axis1_static_zz_couplings` edge metadata and a single global
`zeta_rad_per_ns` value inherited from `Axis1LocalLindbladContextSpec` or the G2
default. That is adequate for the G2 witness and early anti-toy rows, but it is
not yet realistic enough for nonuniform device calibration: actual residual ZZ
is an edge-level cross-Kerr quantity, not one scalar shared by every pair. (a/c)

The minimal increment is to keep the existing edge-set metadata and add an
optional public per-edge calibration sidecar. The schedule still carries public
metadata only; it does not serialize Hamiltonian matrices, Kraus matrices, PTMs,
or evaluator-only mechanism truth. (a)

## Literature Grounding

- Pettersson Fors et al., arXiv:2408.15402, Eq.3/Eq.6: static ZZ is a
  cross-Kerr / conditional-phase Hamiltonian with
  `phi_zeta = integral zeta(t) dt`. The form is exact for the computational
  two-level projection; the magnitude is device- and edge-dependent. (a/b)
- The same note registers modern tunable-coupler residual-ZZ magnitudes as a
  prediction band: residual `zeta` near the coupler-off point can be far below
  older fixed-coupler / strong-ZZ probes. Do not bake one default magnitude into
  all edges. (b/c)
- Kubo et al., arXiv:2402.05361, gives a contrasting STC-class residual-ZZ
  magnitude reference and reinforces that the effective angle depends on the
  integration time and architecture. It is not a Google-specific calibration.
  (b/c)

## Adopted Design

- Add public metadata key `axis1_static_zz_calibrations`. The value is a list of
  records, each with:
  - `edge: [i, j]` (a)
  - `zeta_rad_per_ns: float >= 0` (b/c)
  - optional `epistemic_class: "b" | "c"`; undeclared defaults to `"c"`. (c)
- Keep `axis1_static_zz_couplings` as the canonical public edge set. A
  calibration record must reference an already declared edge and must not create
  new coupling support. (a)
- Add `Axis1StaticZZDeviceSpec(..., zeta_rad_per_ns_by_edge=...)` as a typed
  convenience API; `CircuitBuilder.declare_static_zz_couplings(...)` should
  accept the same optional map. (a/c)
- `SubstepSchedule` should expose both `static_zz_couplings` and
  `static_zz_calibrations` in its manifest and source hash. (a)
- Axis-1 lowering should use the calibrated `zeta_rad_per_ns` for each declared
  edge when present; otherwise it falls back to `Axis1PrimitiveParams.zeta_rad_per_ns`.
  (a/c)

## Non-Adopted Design

- Do not put Hamiltonian matrices or channel payloads in schedule metadata. (a)
- Do not infer residual-ZZ magnitudes from `CZ` history. Active `CZ` provenance
  remains provenance for the same local carrier, not a second static term. (a)
- Do not introduce Axis-2 source/memory coupling. A calibration sidecar is a
  public per-edge parameter table, not a source timeline. (a)
- Do not solve the dense support cap in this slice. Edge-specific coefficients
  improve mechanism realism but do not make large union-support carriers
  scalable. (c)

## Anti-Toy Tests

- Public metadata shape: `Axis1StaticZZDeviceSpec` emits edge-set metadata plus
  per-edge calibration metadata, with no operator/channel/source payload. (a)
- Fail closed: calibration for an undeclared edge, duplicate edge, negative
  zeta, non-finite zeta, or invalid epistemic class raises. (a)
- Schedule plumbing: `CircuitIR` / `CodeSpec` / Stim sidecar metadata reaches
  `SubstepSchedule.static_zz_calibrations` and changes source hash when changed.
  (a/c)
- Channel lowering: a compiler-generated static-ZZ cluster row with two edges
  lowers two `ZZ` Hamiltonian records with distinct coefficients matching the
  public edge table. (a)
- Default invariance: schedules without `axis1_static_zz_calibrations` keep the
  previous global-zeta behavior. Any frozen artifact hash drift caused by schema
  metadata must be explicit and ledgered. (a/c)

## Implementation Evidence

- GPU tests:
  `conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py -k 'static_zz or calibration'`
  -> `17 passed, 73 deselected in 15.45s`. This is a GPU-gated
  schedule/channel/state/record test result, not a CPU-only circuit release
  basis. (a/c)
- Full targeted Axis-1 + joint-L oracle tests:
  `conda run -n aiqec python -m pytest -q tests/test_simulator_axis1_schedule.py tests/test_joint_lindbladian.py`
  -> `101 passed in 48.20s`. This is a regression gate over the Axis-1
  compiler bridge and independent joint-L oracle tests, not a claim that the
  full coupled QEC teacher is complete. (a/c)
- Adjacent frontend/CodeSpec/noise-module tests:
  `conda run -n aiqec python -m pytest -q tests/test_simulator_codespec.py tests/test_simulator_frontend.py tests/test_simulator_noise_module.py`
  -> `53 passed in 1.07s`. These are compiler/metadata/frontend checks, not
  CPU-only circuit simulation evidence. (a/c)
- Calibrated static-ZZ cluster channel artifact:
  `outputs/twin_validation/axis1_static_zz_calibrated_cluster_channel_evidence/axis1_substep_channels.json`.
  Freeze path:
  `outputs/twin_validation/axis1_static_zz_calibrated_cluster_channel_evidence/axis1_substep_channels.freeze.json`.
  Exact manifest content hash:
  `dd9a5f01fd9ba1f3bc986836d1106786bf16057459c26b3406334881f61897de`.
  Exact file sha256:
  `985af4e171c58666d7e084a0d9189e54834ff1d1d55d5b22ed75280622ebeadf`.
  Exact freeze-file sha256:
  `79b4f34ac96a5abb4c7fcb2e0f8f5dbf17a930d9b75b807004a87288447beb4c`.
  This artifact is a compiler-generated row whose two lowered `ZZ`
  Hamiltonian records carry distinct public edge coefficients
  `1.25e-3` and `2.5e-3`; the hashes are artifact identity checks, not
  physics conclusions. (a/c)
- Calibrated static-ZZ cluster record artifact:
  `outputs/twin_validation/axis1_static_zz_calibrated_cluster_evidence/axis1_measurement_records.json`.
  Freeze path:
  `outputs/twin_validation/axis1_static_zz_calibrated_cluster_evidence/axis1_measurement_records.freeze.json`.
  Exact manifest content hash:
  `f3304191397439c662466359d32e7017818384dae9d9182816bc2b1da46136fa`.
  Exact file sha256:
  `145365d86e6d344748b63cd9daa87eb096e489f2db03b603aea99af6babdc64c`.
  Exact freeze-file sha256:
  `156747533380b8d578ab9178ebcf2aea5216e3bfe80253671da078b59b4f93e2`.
  This record evidence confirms the same calibrated schedule path is consumed
  by the selected-channel record enumerator; it still emits no DEM or decoder
  artifact. (a/c)

## Open Risks

- Edge-level calibration is still a Markovian constant over the substep; it does
  not represent time-dependent `zeta(t)` pulses inside a gate. Time-dependent
  integrals would require a richer analog pulse schedule. (b/c)
- A public calibration value may be learned/estimated from hardware but is not
  automatically evaluator truth. Claim wording must distinguish public
  calibration metadata from hidden teacher parameters. (a/c)
- This increment still depends on the dense local carrier for union-support
  rows. The 5-local-qubit cap remains the main scale blocker. (c)

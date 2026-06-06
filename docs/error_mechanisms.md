# Physical Error Mechanisms

This note is the canonical mechanism taxonomy for the surviving mechanism catalog
(`qec_twin.primitives.mechanism_catalog` / `mechanism_profiles`) — the salvage
kept for the twin's hardening step. It combines the implemented PHYS/PHYC mechanism
IDs with the larger controlled-gate error library we want the twin to grow into.
(The teacher-generation program that once consumed this catalog was retired and
removed — ADR 0005.)

For claim boundaries, use `CONTEXT.md` first: the implemented package is still
a fixed-context DEM/Bernoulli research stack. The long-horizon target is the
twin's four capabilities — recover / understand / manipulate / predict (ADR 0005).
CPTP/GKSL structure is one constraint mechanism, not the whole claim.

Physicality boundary: the catalog entries below are implemented as unitary
channels, Kraus channels, or classical readout assignment matrices. Enabling a
mechanism ID selects that implementation. The current learner does not yet
learn arbitrary CPTP/GKSL channels by construction.

## Evidence Sources

The implemented list below is deliberately conservative: every public mechanism
has a distinct implemented channel/readout object or distinct implemented
context role. The source taxonomy was cross-checked against:

- IBM Quantum Learning on multi-qubit error propagation and correlated CNOT
  faults:
  <https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction/fault-tolerant-quantum-computing/controlling-error-propagation>
- IBM Quantum documentation on noise-model families, including Pauli,
  depolarizing, coherent-unitary, Kraus, amplitude/phase damping, thermal
  relaxation, and readout errors:
  <https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models>
- Stim's stabilizer/Pauli-noise scope, useful as a boundary for why physical
  Born-local teachers need non-Pauli channel paths:
  <https://github.com/quantumlib/Stim>
- Crosstalk as correlated/nonlocal processor error:
  <https://quantum-journal.org/papers/q-2020-09-11-321/>
- Controlled-phase spectator coherent errors:
  <https://arxiv.org/abs/2005.05914>
- Parasitic coherent two-qubit gates:
  <https://arxiv.org/abs/2111.04669>
- Leakage outside the computational subspace:
  <https://arxiv.org/html/2406.04083v1>
- Three-qubit gate error/resource issues:
  <https://arxiv.org/abs/1707.00012>
- Silicon-spin Toffoli-style gates under charge noise and crosstalk:
  <https://arxiv.org/abs/2305.13132>

The Qiskit Aer source is cited as a public noise-taxonomy reference only. The
repo direction is literal full-circuit CUDA-Q plus native math diagnostics, not
Qiskit Aer or CUDA-QEC memory-circuit shortcuts.

## Controlled-Gate Noise Model

For an ideal controlled or entangling gate `U_g`, model the noisy
implementation as:

```text
rho -> E_g(U_g rho U_g^dagger)
```

where `E_g` is a gate-specific error channel. In a decoder-facing Pauli/DEM
approximation, `E_g` may become stochastic Pauli faults. In a physical teacher,
`E_g` may include coherent unitary errors, Kraus noise, relaxation/dephasing,
thermal excitation, leakage surrogates, drift, and crosstalk.

Two- and multi-qubit gates need their own error family because they can
propagate pre-existing local faults and can create correlated faults directly.
This is why the implemented catalog separates local stochastic Pauli,
two-qubit depolarizing, coherent RZZ, parasitic two-qubit Hamiltonians,
conditional phase, correlated relaxation, and spectator crosstalk.

## Label Scheme

New controlled-catalog runs use two public semantic label namespaces:

- `F0`-`Fn`: flat, atomic visible-effect targets. These may be used as exact
  controlled-catalog evaluator clusters when the surface supports them.
- `M0`-`Mn`: non-flat mechanism/family targets. These require family plus
  context-relative dimension recovery, not a single flat cluster claim.

The historical `M0`-`M34` IDs remain implementation-stable
`legacy_catalog_id` values so old configs, artifacts, and tests can still load.
They must not be interpreted as the public semantic label namespace.

## Implemented Catalog

Status: implemented in `src/qec_twin/primitives/mechanism_catalog.py` and
channelized in `src/qec_twin/primitives/channels.py`.

The IDs are priority ordered by expected practical frequency/importance for
near-term hardware-style experiments. This order defines the mechanism sets.

| Legacy ID | Public label | Name | Implemented object | Physical family |
| --- | --- | --- | --- | --- |
| M0 | M0 | `local_stochastic_pauli_gate_error` | 1q stochastic Pauli Kraus channel with X/Y/Z rates | local Pauli/process noise |
| M1 | M1 | `readout_0_to_1_bias` | asymmetric assignment matrix | readout/SPAM |
| M2 | M2 | `readout_1_to_0_bias` | asymmetric assignment matrix | readout/SPAM |
| M3 | M3 | `readout_symmetric_assignment_noise` | symmetric assignment matrix | readout/SPAM |
| M4 | F0 | `amplitude_damping_gate_error` | 1q amplitude-damping Kraus channel | T1-like relaxation |
| M5 | F1 | `idle_dephasing_or_relaxation_error` | 1q idle Z/phase-noise Kraus channel | idle T2/T1 surrogate |
| M6 | F2 | `coherent_rx_overrotation` | 1q `RX(epsilon)` coherent unitary | coherent control error |
| M7 | F3 | `coherent_rz_overrotation` | 1q `RZ(epsilon)` coherent unitary | coherent phase/control error |
| M8 | F4 | `coherent_rzz_overrotation` | 2q `RZZ(epsilon)` coherent unitary | entangling-angle error |
| M9 | M4 | `two_qubit_depolarizing_after_rzz` | 2q depolarizing Kraus channel over 15 non-identity Paulis | coarse correlated Pauli noise |
| M10 | M5 | `coherent_rxx_ryy_perturbation` | composed `RXX(eps_x)` and `RYY(eps_y)` unitary | parasitic XX/YY coupling |
| M11 | M6 | `spectator_crosstalk_rz_or_zz` | spectator overlay family, not a flat mutually exclusive mechanism | spectator crosstalk |
| M12 | F5 | `correlated_two_qubit_relaxation` | 2q non-unital correlated relaxation Kraus channel | correlated relaxation |
| M13 | M7 | `drifted_coherent_overrotation` | context-varying 1q coherent overrotation represented as a random-unitary drift overlay on the declared operation axis | slow calibration drift |
| M14 | M8 | `operation_dependent_error` | 1q coherent error generator attached to a visible operation axis; default `operation_axis=rx`, `error_axis=rz` | operation-context error |
| M15 | M9 | `hard_non_pauli_kraus_gate_error` | non-Pauli custom Kraus channel | hard non-Pauli CPTP stress case |
| M16 | M10 | `measurement_context_bias` | context-shaped readout assignment matrix | context-conditioned readout |
| M17 | F6 | `reset_to_1_bias` | reset-to-state Kraus channel | reset/preparation bias |
| M18 | M11 | `prep_axis_or_reset_asymmetry_bias` | prep/reset coherent asymmetry unitary | preparation-axis bias |
| M19 | M12 | `weak_type4_ptm_mixing` | weak mixed Pauli/coherent Kraus channel | weak non-Pauli PTM mixing |
| M20 | F7 | `coherent_ry_overrotation` | 1q `RY(epsilon)` coherent unitary | coherent Y-axis control error |
| M21 | F8 | `conditional_phase_branch_error` | 2q controlled-phase branch unitary | conditional phase error |
| M22 | F9 | `coherent_cxx_parasitic_coupling` | 2q `exp(-i epsilon XX/2)` unitary | parasitic XX coupling |
| M23 | F10 | `coherent_cyy_parasitic_coupling` | 2q `exp(-i epsilon YY/2)` unitary | parasitic YY coupling |
| M24 | F11 | `thermal_excitation_gate_error` | 1q excitation Kraus channel | finite-temperature/T1-up error |
| M25 | F12 | `stochastic_bit_flip_gate_error` | 1q X-only stochastic Pauli channel | bit-flip process noise |
| M26 | F13 | `stochastic_y_gate_error` | 1q Y-only stochastic Pauli channel | Y-axis process noise |
| M27 | M13 | `coherent_h_axis_overrotation` | 1q rotation about normalized X+Z axis | diagonal control-axis error |
| M28 | F14 | `coherent_xy_parasitic_coupling` | 2q `exp(-i epsilon XY/2)` unitary | parasitic mixed coupling |
| M29 | F15 | `coherent_zx_parasitic_coupling` | 2q `exp(-i epsilon ZX/2)` unitary | cross-resonance-like ZX residue |
| M30 | F16 | `coherent_zy_parasitic_coupling` | 2q `exp(-i epsilon ZY/2)` unitary | mixed ZY residue |
| M31 | F17 | `coherent_xz_parasitic_coupling` | 2q `exp(-i epsilon XZ/2)` unitary | mixed XZ residue |
| M32 | F18 | `coherent_yz_parasitic_coupling` | 2q `exp(-i epsilon YZ/2)` unitary | mixed YZ residue |
| M33 | F19 | `coherent_yx_parasitic_coupling` | 2q `exp(-i epsilon YX/2)` unitary | mixed YX residue |
| M34 | M14 | `leakage_relaxation_surrogate` | computational-subspace leakage-relaxation surrogate Kraus channel | leakage surrogate |

## Contract-Role Audit

The legacy `M0`-`M34` IDs are implemented catalog leaves, but they are not all
the same semantic kind. Stage 3/S5 should distinguish:

- `leaf_exact_effect_supported`: the current controlled teacher can still emit
  and audit this implementation leaf when the assignment is already correct.
- `primary_flat_cluster_target`: the implementation leaf maps to a public
  `F*` label. Some `F*` leaves are still surface-conditional on the current
  Z/X-visible Stage 3/S5 surface and must be claimed through dimension/property
  recovery until a stronger probe exposes the flat exact split.
- public `M*` labels: non-flat family/dimension targets.

The current audit is pinned in
`qec_twin.primitives.mechanism_catalog.MECHANISM_CONTRACTS`.

| Role | Legacy IDs | Public labels | S3/S5 interpretation |
| --- | --- | --- | --- |
| Primary flat cluster targets | M4, M5, M6, M7, M8, M12, M17, M20, M21, M22, M23, M24, M25, M26, M28, M29, M30, M31, M32, M33 | F0-F19 | Exact `F*` clusters are acceptable controlled-catalog evaluator targets only when the current visible surface declares flat-exact claims allowed; otherwise S5 requires dimension/property recovery. |
| Surface-conditional flat targets | M6, M22, M23 | F2, F9, F10 | These remain public `F*` leaves, but current Z/X-visible Stage 3/S5 evidence does not claim flat-exact separation. M6/M13 diagnostics run inside the M6/M13/M18/M27 targeted set; M22/M23 diagnostics run inside the M6/M13/M22/M23 targeted set and need an axis-sensitive quadrature probe for flat XX-vs-YY separation. |
| Aggregate or direction-slice families | M0, M1, M2, M3 | M0-M3 | Prefer family plus axis/direction/mixture recovery over treating the broad leaf as an atomic physical mechanism. |
| Coarse or coherent mixture families | M9, M10, M27 | M4, M5, M13 | Do not interpret a single flat cluster as full mechanism recovery unless the Pauli/axis mixture dimensions are also audited. |
| Context- or operation-conditioned families | M13, M14, M16, M18 | M7, M8, M10, M11 | Recover base family plus operation/context, location, and strength dimensions; exact-label recall alone is not enough. |
| Surrogate or stress families | M15, M19, M34 | M9, M12, M14 | Useful controlled stress leaves, but not standalone physical mechanism claims. |
| Overlay family | M11 | M6 | Must be handled as `base_mechanism + spectator_overlay(...)`, not as a flat exact mechanism. |

This audit does not remove existing IDs. It narrows the claim: legacy exact-ID
metrics are evaluator-only diagnostics, public `F*` labels are the flat
cluster targets, and public `M*` labels require family/dimension recovery.

## Mechanism Sets

Because we found 35 distinct implementable mechanisms, set C remains the top
25 rather than being reduced to 20.

```text
set_A: legacy M0-M9      top 10 frequency/importance mechanisms
set_B: legacy M0-M14     top 15 frequency/importance mechanisms
set_C: legacy M0-M24     top 25 frequency/importance mechanisms
set_D: legacy M0-M34     all implemented mechanisms
allM:  legacy M0-M34     alias for set_D
```

`allM` and `set_D` are intentionally the same current legacy-ID universe.
Future labels should extend the public F/M mapping, not silently overload
existing legacy IDs.

## Weighted Profiles

Balanced profiles test identifiability under equal support. Weighted profiles
test robustness under realistic-ish QEC exposure imbalance.

Current weighted profiles are resolved from
`src/qec_twin/primitives/mechanism_profiles.py`, which imports the current
legacy M0-M34 catalog names from `mechanism_catalog.py`. Do not hand-maintain
stale legacy-ID parameter blocks in YAML.

```text
weighted_realistic_v1:
  exposure-weighted superconducting-QEC synthetic prior over legacy M0-M34

weighted_discovery_floor_v1:
  same prior, but with a support floor so rare/high-impact mechanisms remain visible
```

These profiles are not hardware-calibrated mechanism frequency distributions.
They encode synthetic support for controlled stress tests:

```text
mechanism_weight[M]
  ~= circuit_exposure[M]
   * hardware_family_prior[M]
   * severity_or_discovery_importance[M]
```

## Stage 2E.1 Born-Local Scope

Born-local samples exact local probabilities:

```text
rho_probe -> ideal local operation/context -> mechanism channel/readout -> POVM
```

Current Stage 2E.1 support is all implemented legacy mechanisms except legacy
M11:

```text
supported:   legacy M0-M10, M12-M34
unsupported: legacy M11 / public M6 spectator_crosstalk_rz_or_zz
```

Legacy M11 / public M6 is a spectator-crosstalk overlay family, not a
standalone mechanism class. Use it as:

```text
observed_effect =
  base_mechanism
  + spectator_overlay(victim, aggressor, axis, timing, strength)
```

It remains outside Born-local until the spectator contract states:

```text
base_mechanism: RZZ, RZ, readout_bias, reset_bias, idle, leakage-like, ...
spectator_overlay_present
victim_relative_location
aggressor_relative_location
coupling_axis: RZ, ZZ, readout_bias, reset_bias, ...
timing_context: same_cycle, prev_cycle, shot_block_drift, ...
strength
```

## Renumbering Map

Historical M0-M19 artifacts remain valid as historical evidence, but new runs
use the legacy M0-M34 catalog plus the public F/M labels above. The
compatibility layer maps old config keys when it detects pre-M0-M34 mechanism
parameter blocks.

| Pre-M0-M34 ID | Current legacy ID | Public label | Current name |
| --- | --- | --- | --- |
| old M0 | M0 | M0 | `local_stochastic_pauli_gate_error` |
| old M1 | M8 | F4 | `coherent_rzz_overrotation` |
| old M2 | M6 | F2 | `coherent_rx_overrotation` |
| old M3 | M7 | F3 | `coherent_rz_overrotation` |
| old M4 | M4 | F0 | `amplitude_damping_gate_error` |
| old M5 | M15 | M9 | `hard_non_pauli_kraus_gate_error` |
| old M6 | M9 | M4 | `two_qubit_depolarizing_after_rzz` |
| old M7 | M10 | M5 | `coherent_rxx_ryy_perturbation` |
| old M8 | M11 | M6 | `spectator_crosstalk_rz_or_zz` |
| old M9 | M12 | F5 | `correlated_two_qubit_relaxation` |
| old M10 | M13 | M7 | `drifted_coherent_overrotation` |
| old M11 | M5 | F1 | `idle_dephasing_or_relaxation_error` |
| old M12 | M14 | M8 | `operation_dependent_error` |
| old M13 | M1 | M1 | `readout_0_to_1_bias` |
| old M14 | M2 | M2 | `readout_1_to_0_bias` |
| old M15 | M3 | M3 | `readout_symmetric_assignment_noise` |
| old M16 | M16 | M10 | `measurement_context_bias` |
| old M17 | M17 | F6 | `reset_to_1_bias` |
| old M18 | M18 | M11 | `prep_axis_or_reset_asymmetry_bias` |
| old M19 | M19 | M12 | `weak_type4_ptm_mixing` |

## Effective Local Depth

For a depth-`d` local circuit, the exact local object is the composed channel:

```text
Phi_eff = Phi_d o ... o Phi_2 o Phi_1
p(outcome) = Tr[POVM * Phi_eff(rho_probe)]
```

The current Born-local thin slice intentionally uses effective depth 1 for
explainability. Configured `circuit_depth` is preserved as artifact provenance;
it is not hidden channel stacking.

Repeated same-axis coherent terms collapse by angle addition, for example:

```text
RZZ(epsilon)^d = RZZ(d * epsilon)
```

Noncommuting terms, such as a one-qubit X/Y error inside an RZZ stack, must
preserve layer order and be composed exactly. Readout confusion applies once at
the final POVM. Reset/preparation applies only where the visible schedule says
it applies.

## Two-Qubit Gate Families

The implemented 2q catalog covers a useful subset of the mature two-qubit
library:

| Family | Meaning | Implemented legacy IDs |
| --- | --- | --- |
| G2_LOCAL_PAULI | one participant receives a local Pauli fault | M0 plus M25/M26 as 1q channels |
| G2_CORRELATED_PAULI | two participants receive a joint Pauli fault | future grouped Pauli extension |
| G2_DEPOLARIZING | coarse two-qubit depolarizing approximation | M9 |
| G2_COHERENT_ZZ_PHASE | entangling angle or conditional phase error | M8, M21 |
| G2_PARASITIC_COUPLING | unwanted two-qubit Hamiltonian term | M10, M22-M23, M28-M33 |
| G2_T1_T2_DURING_GATE | relaxation/dephasing during the pulse | M4, M5, M12, M24 |
| G2_LEAKAGE | state leaves computational subspace | M34 surrogate |
| G2_SPECTATOR_CROSSTALK | nearby idle/active qubit changes the gate | legacy M11 / public M6 overlay contract |
| G2_SLOW_DRIFT | parameter changes over time/location | legacy M13 / public M7 |

The 2q Pauli basis has `4^2 - 1 = 15` non-identity errors:

```text
XI, YI, ZI, IX, IY, IZ,
XX, XY, XZ, YX, YY, YZ, ZX, ZY, ZZ
```

For discovery, `DEPOLARIZE2(p)` is too coarse by itself. Keep local Pauli,
correlated Pauli, coherent phase, parasitic coupling, leakage, and
spectator/crosstalk mechanisms separate.

## Three-Qubit Controlled-Gate Families

For direct Toffoli, CCNOT, and CCZ gates, the Pauli basis has
`4^3 - 1 = 63` non-identity errors:

```text
weight-1: 3 * 3 = 9
weight-2: C(3, 2) * 3^2 = 27
weight-3: 3^3 = 27
```

Do not model all 63 independently at first. Group them:

| Family | Meaning | Examples |
| --- | --- | --- |
| G3_WEIGHT1_PAULI | one qubit hit during a 3q gate | `XII`, `IZI` |
| G3_WEIGHT2_PAULI | pairwise correlated error inside the 3q gate | `ZZI`, `IXX`, `ZIX` |
| G3_WEIGHT3_PAULI | true high-weight correlated fault | `ZZZ`, `XXX`, `XYZ` |
| G3_CCZ_PHASE_OVERROTATION | wrong conditional phase on `111` | over/under-rotated CCZ phase |
| G3_TOFFOLI_BRANCH_ERROR | target flips too much or too little on control branch `11` | imperfect CCNOT target rotation |
| G3_FALSE_BRANCH_ACTIVATION | target rotates on non-target branches | unwanted action on `101`, `011`, etc. |
| G3_PAIRWISE_PARASITIC_COUPLING | 2-body residue inside intended 3-body gate | `Z1Z2`, `Z2Z3`, `X2X3` |
| G3_LEAKAGE_CASCADE | leaked qubit corrupts other participants | leaked ancilla/control spreads error |
| G3_CONTEXT_CROSSTALK | external spectator or pulse affects the 3q gate | context-dependent phase/noise |

These are not public F/M labels yet. Add them only after a probe family and a
learner-visible observable family exist.

## Adoption Rules

1. Public `F*` labels are flat atomic visible-effect targets.
2. Public `M*` labels are non-flat mechanism/family targets and require
   dimension recovery.
3. Add public labels only when the local teacher, PHYC2 features, and docs can
   explain the difference without oracle-only templates.
4. Keep `allM` as the implemented legacy-ID universe.
5. Treat historical M0-M19 artifacts as pre-renumbering evidence unless their
   teacher config explicitly records the current legacy M0-M34 catalog.

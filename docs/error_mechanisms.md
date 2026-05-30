# Physical Error Mechanisms

This note is the canonical mechanism taxonomy for the SCOPE-Static physical
teacher work. It combines the implemented PHYS/PHYC mechanism IDs with the
larger controlled-gate error library we want SCOPE-Twin to grow into.

For claim boundaries, use `CONTEXT.md` first: the implemented package is still
a fixed-context SCOPE-Static research stack. The long-horizon target is the
six-axis physical generation problem. CPTP/GKSL structure is one constraint
mechanism, not the whole claim.

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

## Implemented Catalog

Status: implemented in `src/scope_static/physical/mechanism_catalog.py` and
channelized in `src/scope_static/physical/channels.py`.

The IDs are priority ordered by expected practical frequency/importance for
near-term hardware-style experiments. This order defines the mechanism sets.

| ID | Name | Implemented object | Physical family |
| --- | --- | --- | --- |
| M0 | `local_stochastic_pauli_gate_error` | 1q stochastic Pauli Kraus channel with X/Y/Z rates | local Pauli/process noise |
| M1 | `readout_0_to_1_bias` | asymmetric assignment matrix | readout/SPAM |
| M2 | `readout_1_to_0_bias` | asymmetric assignment matrix | readout/SPAM |
| M3 | `readout_symmetric_assignment_noise` | symmetric assignment matrix | readout/SPAM |
| M4 | `amplitude_damping_gate_error` | 1q amplitude-damping Kraus channel | T1-like relaxation |
| M5 | `idle_dephasing_or_relaxation_error` | 1q idle Z/phase-noise Kraus channel | idle T2/T1 surrogate |
| M6 | `coherent_rx_overrotation` | 1q `RX(epsilon)` coherent unitary | coherent control error |
| M7 | `coherent_rz_overrotation` | 1q `RZ(epsilon)` coherent unitary | coherent phase/control error |
| M8 | `coherent_rzz_overrotation` | 2q `RZZ(epsilon)` coherent unitary | entangling-angle error |
| M9 | `two_qubit_depolarizing_after_rzz` | 2q depolarizing Kraus channel over 15 non-identity Paulis | coarse correlated Pauli noise |
| M10 | `coherent_rxx_ryy_perturbation` | composed `RXX(eps_x)` and `RYY(eps_y)` unitary | parasitic XX/YY coupling |
| M11 | `spectator_crosstalk_rz_or_zz` | explicit spectator placeholder, currently outside Born-local | spectator crosstalk |
| M12 | `correlated_two_qubit_relaxation` | 2q non-unital correlated relaxation Kraus channel | correlated relaxation |
| M13 | `drifted_coherent_overrotation` | context-varying 1q coherent overrotation on the declared operation axis | slow calibration drift |
| M14 | `operation_dependent_error` | 1q coherent error generator attached to a visible operation axis; default `operation_axis=rx`, `error_axis=rz` | operation-context error |
| M15 | `hard_non_pauli_kraus_gate_error` | non-Pauli custom Kraus channel | hard non-Pauli CPTP stress case |
| M16 | `measurement_context_bias` | context-shaped readout assignment matrix | context-conditioned readout |
| M17 | `reset_to_1_bias` | reset-to-state Kraus channel | reset/preparation bias |
| M18 | `prep_axis_or_reset_asymmetry_bias` | prep/reset coherent asymmetry unitary | preparation-axis bias |
| M19 | `weak_type4_ptm_mixing` | weak mixed Pauli/coherent Kraus channel | weak non-Pauli PTM mixing |
| M20 | `coherent_ry_overrotation` | 1q `RY(epsilon)` coherent unitary | coherent Y-axis control error |
| M21 | `conditional_phase_branch_error` | 2q controlled-phase branch unitary | conditional phase error |
| M22 | `coherent_cxx_parasitic_coupling` | 2q `exp(-i epsilon XX/2)` unitary | parasitic XX coupling |
| M23 | `coherent_cyy_parasitic_coupling` | 2q `exp(-i epsilon YY/2)` unitary | parasitic YY coupling |
| M24 | `thermal_excitation_gate_error` | 1q excitation Kraus channel | finite-temperature/T1-up error |
| M25 | `stochastic_bit_flip_gate_error` | 1q X-only stochastic Pauli channel | bit-flip process noise |
| M26 | `stochastic_y_gate_error` | 1q Y-only stochastic Pauli channel | Y-axis process noise |
| M27 | `coherent_h_axis_overrotation` | 1q rotation about normalized X+Z axis | diagonal control-axis error |
| M28 | `coherent_xy_parasitic_coupling` | 2q `exp(-i epsilon XY/2)` unitary | parasitic mixed coupling |
| M29 | `coherent_zx_parasitic_coupling` | 2q `exp(-i epsilon ZX/2)` unitary | cross-resonance-like ZX residue |
| M30 | `coherent_zy_parasitic_coupling` | 2q `exp(-i epsilon ZY/2)` unitary | mixed ZY residue |
| M31 | `coherent_xz_parasitic_coupling` | 2q `exp(-i epsilon XZ/2)` unitary | mixed XZ residue |
| M32 | `coherent_yz_parasitic_coupling` | 2q `exp(-i epsilon YZ/2)` unitary | mixed YZ residue |
| M33 | `coherent_yx_parasitic_coupling` | 2q `exp(-i epsilon YX/2)` unitary | mixed YX residue |
| M34 | `leakage_relaxation_surrogate` | computational-subspace leakage-relaxation surrogate Kraus channel | leakage surrogate |

## Mechanism Sets

Because we found 35 distinct implementable mechanisms, set C remains the top
25 rather than being reduced to 20.

```text
set_A: M0-M9      top 10 frequency/importance mechanisms
set_B: M0-M14     top 15 frequency/importance mechanisms
set_C: M0-M24     top 25 frequency/importance mechanisms
set_D: M0-M34     all implemented mechanisms
allM:  M0-M34     alias for set_D
```

`allM` and `set_D` are intentionally the same current universe. Future labels
should extend `set_D/allM`, not silently overload existing IDs.

## Stage 2E.1 Born-Local Scope

Born-local samples exact local probabilities:

```text
rho_probe -> ideal local operation/context -> mechanism channel/readout -> POVM
```

Current Stage 2E.1 support is all implemented mechanisms except M11:

```text
supported:   M0-M10, M12-M34
unsupported: M11 spectator_crosstalk_rz_or_zz
```

M11 remains outside Born-local until the spectator contract states:

```text
victim qubit
aggressor operation or edge
observable support: RZ-on-victim, ZZ-on-pair, XX/YY-like parasitic term, or other
timing relation to the active gate layer
```

## Renumbering Map

Historical M0-M19 artifacts remain valid as historical evidence, but new runs
use the M0-M34 catalog above. The compatibility layer maps old config keys when
it detects legacy mechanism parameter blocks.

| Legacy ID | Current ID | Current name |
| --- | --- | --- |
| old M0 | M0 | `local_stochastic_pauli_gate_error` |
| old M1 | M8 | `coherent_rzz_overrotation` |
| old M2 | M6 | `coherent_rx_overrotation` |
| old M3 | M7 | `coherent_rz_overrotation` |
| old M4 | M4 | `amplitude_damping_gate_error` |
| old M5 | M15 | `hard_non_pauli_kraus_gate_error` |
| old M6 | M9 | `two_qubit_depolarizing_after_rzz` |
| old M7 | M10 | `coherent_rxx_ryy_perturbation` |
| old M8 | M11 | `spectator_crosstalk_rz_or_zz` |
| old M9 | M12 | `correlated_two_qubit_relaxation` |
| old M10 | M13 | `drifted_coherent_overrotation` |
| old M11 | M5 | `idle_dephasing_or_relaxation_error` |
| old M12 | M14 | `operation_dependent_error` |
| old M13 | M1 | `readout_0_to_1_bias` |
| old M14 | M2 | `readout_1_to_0_bias` |
| old M15 | M3 | `readout_symmetric_assignment_noise` |
| old M16 | M16 | `measurement_context_bias` |
| old M17 | M17 | `reset_to_1_bias` |
| old M18 | M18 | `prep_axis_or_reset_asymmetry_bias` |
| old M19 | M19 | `weak_type4_ptm_mixing` |

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

| Family | Meaning | Implemented IDs |
| --- | --- | --- |
| G2_LOCAL_PAULI | one participant receives a local Pauli fault | M0 plus M25/M26 as 1q channels |
| G2_CORRELATED_PAULI | two participants receive a joint Pauli fault | future grouped Pauli extension |
| G2_DEPOLARIZING | coarse two-qubit depolarizing approximation | M9 |
| G2_COHERENT_ZZ_PHASE | entangling angle or conditional phase error | M8, M21 |
| G2_PARASITIC_COUPLING | unwanted two-qubit Hamiltonian term | M10, M22-M23, M28-M33 |
| G2_T1_T2_DURING_GATE | relaxation/dephasing during the pulse | M4, M5, M12, M24 |
| G2_LEAKAGE | state leaves computational subspace | M34 surrogate |
| G2_SPECTATOR_CROSSTALK | nearby idle/active qubit changes the gate | M11 placeholder |
| G2_SLOW_DRIFT | parameter changes over time/location | M13 |

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

These are not public `M*` labels yet. Add them only after a probe family and a
learner-visible observable family exist.

## Adoption Rules

1. Public `M*` labels must map to implemented, distinct channel/readout/context
   objects.
2. Add public labels only when the local teacher, PHYC2 features, and docs can
   explain the difference without oracle-only templates.
3. Keep `allM` as all implemented mechanisms.
4. Treat historical M0-M19 artifacts as pre-renumbering evidence unless their
   teacher config explicitly records the new M0-M34 catalog.

# Domain context

This repository develops `error_coupling_simulator`, a GPU-first specified-noise simulator for QEC
circuits. The binding contract is `docs/SIMULATOR.md`.

## Terms

- **Specified noise process** — a declared generative model applied to a circuit or schedule. It is
  not fitted physical ground truth. Its hidden trajectory and channel field are evaluator-only.
- **Record** — temporal detector bits plus logical-observable flips across rounds. It is the product.
  Raw stabilizer outcomes are a distinct diagnostic coordinate and require the declared temporal XOR
  fold before they are called detectors.
- **DEM** — an optional decoder-facing Pauli reduction of a record-generating process. It is not the
  process or the record.
- **Carrier** — the forward engine that propagates the declared process and emits or supports a
  record. Current carriers have distinct support and evidence boundaries.
- **Reference oracle** — an independent closed form, raw artifact, exact-density route, or
  from-scratch reconstruction used to catch implementation errors. It is not physical truth.
- **Controlled fixture** — a synthetic, explicitly parameterized input used to exercise a formula or
  falsifier. Fixture values do not become measured parameters.
- **Downstream estimator** — decoder, calibration, model-selection, parameter-recovery, or
  identifiability logic consuming records. It is outside the simulator product.
- **Axis-1** — within-substep joint-Lindbladian evolution: all declared local Hamiltonian and collapse
  terms for a substep enter one generator before propagation.
- **Axis-2** — a replayable classical latent timeline mapped into per-round process parameters. The
  current finite-RTN route is a record-memory model, not a microscopic bath or reduced-map verdict.
- **Leakage** — population or coherence outside the computational subspace. Current bounded owners
  include qutrit leakage and explicit multi-level CZ transport.
- **Record faithfulness** — agreement of the declared detector/observable record law with an
  independent reference within a frozen band. Bond, state, entropy, or local environment agreement
  alone is insufficient.

## Current implementation boundary

The frontend Stim route, dense Axis-1 route, finite-RTN source process, restricted one-dimensional MPS
verification routes, qutrit/ququart channels, exact bounded references, PEPO, PEPS, certification, and
quantum-bath research surface are separate registered services.

The density-matrix PEPO and single-wire PEPS are retained research carriers. PEPO is not the canonical
record backend. PEPS full-record finite-truncation faithfulness is open, and its current FET
entropy equality is all-noop at the registered strict target: zero rank-reducing writes make the
non-degeneracy gate RED. See `docs/simulator_validation/PEPO_VALIDATION.md` and
`docs/simulator_validation/PEPS_FET_VALIDATION.md`.

The source-conditioned dense-qubit process and static data-qutrit XZZX leakage process are not one
integrated product. Their missing bridge is an implementation fact. No field-wide literature-gap
claim is inferred from that absence.

## Memory claim classes

These are non-exclusive properties of different objects:

- **record memory** — dependence/order in a fixed observed record law;
- **reduced-map divisibility or distinguishability backflow** — a property or witness of a declared
  family of system maps;
- **process-tensor/environment memory** — a multi-time causal object requiring a declared instrument
  or intervention family.

One class does not transfer to another without an explicit bridge. A stochastic source alone is not a
dynamical map. A passive record statistic does not identify a quantum environmental origin.

## Claim boundary

- No specified process is physical ground truth.
- No paper equation supplies an implemented amplitude unless the exact value and transformation chain
  are separately grounded.
- Cross-paper/device tuples are composite benchmarks, not calibrated device cells.
- PTM off-diagonal structure is basis-specific non-Pauli structure, not a standalone coherent-cause
  certificate.
- Structural zeros remain zero; numerical floors are not probability mass.
- Every d5/d7 distributional claim is provisional and cannot be used as a scientific premise.
- No local carrier statistic substitutes for a complete record-law comparison.
- No unsupported schema, compatibility path, or historical output is current evidence.

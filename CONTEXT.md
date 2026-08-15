# Domain context

This repository develops `error_coupling_simulator` (ECS), a backend-agnostic classical evaluator
for caller-declared quantum-error processes interleaved with quantum error-correction (QEC)
programs. The binding product contract is `docs/SIMULATOR.md`; capabilities and assurance are
defined separately in `docs/CAPABILITY_MODEL.md` and `docs/FAITHFULNESS_PROTOCOL.md`.

## Canonical terms

- **QEC program** — the declared operations, measurements, resets, timing where relevant, classical
  controls, and detector/logical-observable parity definitions.
- **Declared error process** — the generative error model applied to the QEC program. It may contain
  coherent, stochastic, spatially correlated, temporally correlated, classical-latent, or explicitly
  declared quantum-memory components. It is not fitted physical ground truth.
- **Private process state** — a latent variable, trajectory, channel field, or memory checkpoint used
  to generate the declared process. It is evaluator-only and is not part of the public `Record`.
- **Raw measurement coordinate** — the chronological measurement outputs consumed by a declared
  Record layout. It is distinct from detector events.
- **Record layout** — the frozen ordered XOR incidence that maps measurement columns to detector and
  logical-observable rows. The adjacent-round syndrome fold is one layout profile, not a universal
  definition.
- **Record** — the ordered binary detector vector followed by the ordered logical-observable vector.
- **Record law** — the joint probability law of the `Record` under the declared QEC program, error
  process, and shot contract. It is the mathematical product semantics.
- **Record interface** — samples, Record/prefix scores, named functionals, structured-law queries, or
  complete enumeration exposing the Record law within a backend's capability.
- **Backend** — an implementation that validates, compiles, executes, or queries a supported slice.
  Hardware and numerical representation are backend choices rather than product definitions.
- **Carrier** — a backend component that propagates the declared process. The name alone carries no
  state-, Record-, metric-, scaling-, or assurance claim.
- **Capability** — what a backend can return, such as sampling or scoring. It is not evidence that
  the result is correct.
- **Support envelope** — the exact semantic predicate covering a backend's operations, dimensions,
  instruments, memory, shot semantics, Record layout, numerical guarantees, and exclusions.
- **Assurance claim** — the scoped statement permitted by an evidence packet: execution, family,
  run, metric, complete-law, or scientific-generalization assurance.
- **Reference oracle** — an independent exact calculation, raw artifact, closed form, or from-scratch
  reconstruction used to catch implementation errors. It is not physical truth.
- **Controlled fixture** — a synthetic, explicitly parameterized input used to exercise a formula or
  falsifier. Fixture values do not become measured parameters.
- **DEM** — an optional decoder-facing Pauli reduction of a Record-generating process. It is not the
  process or the Record law.
- **Downstream estimator** — decoder, calibration, model-selection, parameter-recovery,
  identifiability, or decoder-headroom logic consuming Records. It is outside the simulator product.

## Memory claim classes

These are non-exclusive properties of different objects:

- **Record memory** — temporal dependence or order in a fixed observed Record law;
- **reduced-map divisibility or distinguishability backflow** — a property or witness of a declared
  family of reduced system maps;
- **process-tensor or environment memory** — a multi-time causal object requiring a declared
  intervention family.

One class does not transfer to another without an explicit bridge. A classical latent source alone
is not a reduced dynamical map. Passive Record statistics do not identify a quantum environmental
origin. “Non-Markovian” must therefore name the object and access model to which it refers.

## Numerical and evidence distinctions

- `ALGEBRAIC_EXACT`, `UNTRUNCATED_FLOATING`, `CERTIFIED_NUMERIC`, bounded approximation, and
  unbounded research approximation are different guarantees.
- A zero coefficient cutoff does not certify floating roundoff, time discretization, or the Record
  law.
- Structural zeros remain exact; numerical floors are never probability mass.
- A local tensor, bond, entropy, active-rank, treewidth, fidelity, or discarded-weight diagnostic
  does not substitute for a named Record-functional or full-law bound.
- `CORE/RESEARCH` describes current service placement, not capability or correctness.
- `PASS/FAIL/UNANCHORED` is a plan verdict; `CODE_BLOCKED` is a scoped workflow authorization.

## Current implementation boundary

The exact live services, owners, entry points, dependencies, output forms, and exclusions are in
`docs/service_status.json`; `docs/ARCHITECTURE.md` is the human-readable map. Those documents describe
the current implementation and may contain route-specific limitations. They do not narrow the
backend-neutral product charter.

The 2026-08-03 no-cutoff target-lowering plan validated static neutral, pair,
dynamic-ADD-relation, and retained-boundary tensor-network definitions for its frozen cells. It
executed no target solver and supplied no target-size full Record law. Its historical `CODE_BLOCKED`
field remains unchanged; the current assurance mapping is recorded in
`docs/simulator_validation/PRODUCT_BOUNDARY_V2_MIGRATION_2026-08-04.md`.

## Claim boundary

- No declared process is physical ground truth.
- ECS models error processes, not microscopic open-system dynamics by default.
- A paper equation supplies neither an implemented mechanism nor a numerical amplitude without a
  verified transformation chain.
- Cross-paper or cross-device tuples are composite benchmarks, not calibrated device cells.
- PTM off-diagonal structure is basis-specific non-Pauli structure, not a standalone coherent-cause
  certificate.
- No metric, backend, distance, round count, or memory class transfers beyond its explicit support
  and assurance scope.
- No unsupported schema, silent reduction, compatibility fallback, or historical output is current
  evidence for a new claim.

# Capability and support contract

This document defines how an `error_coupling_simulator` (ECS) backend states what it can execute and
what it returned. It supplements the product semantics in `docs/SIMULATOR.md`; it is not a
correctness certificate and it does not claim that the logical manifests below already exist as one
installed serialization schema.

Current services may expose equivalent facts across `docs/service_status.json` and owner-specific
manifests. Every new or materially changed backend must provide the complete logical objects below
before it can be promoted beyond an experimental owner. A future artifact schema may serialize these
objects without changing their semantics.

## Functional capabilities

Capabilities are independent declarations. A backend must not claim a capability merely because it
implements another one.

| Capability | Required behavior |
|---|---|
| `VALIDATE_COMPILE` | Validate the declared QEC program, error process, Record layout, and shot contract; emit a bound neutral or backend program. |
| `SAMPLE` | Draw from the supported Record law under the declared shot contract. |
| `SCORE_RECORD` | Return the probability or log probability of a complete Record. |
| `SCORE_PREFIX` | Return a normalized prefix probability or the conditional probability of the next declared Record coordinate, with the conditioning prefix explicit. |
| `EVALUATE_FUNCTIONAL` | Return one preregistered Record functional with a named metric and guarantee. |
| `STRUCTURED_LAW` | Return a normalized, queryable representation of the joint Record law; dense materialization is not required. |
| `ENUMERATE_LAW` | Return every finite-support Record and its probability in canonical order. |

`STRUCTURED_LAW` must document its supported queries and exact normalization semantics. A tensor
network, decision diagram, factor graph, recurrence, or autoregressive sampler is not a structured
law merely because it is an internal representation.

## Semantic support envelope

Each backend publishes a support envelope containing at least:

- local dimensions and qubit/qudit ordering;
- supported operation, measurement, and reset instruments;
- measurement bases, readout mappings, classical controls, and feedback;
- supported error-map classes and maximum spatial support;
- supported coherent, stochastic, classical-latent, and quantum-memory forms;
- within-shot memory dimension, initialization, and transition semantics;
- cross-shot process-instance and transition semantics;
- supported detector/observable Record layouts;
- supported capabilities and numerical guarantees;
- resource guards and preflight ceilings;
- explicit reductions, exclusions, and unsupported constructs;
- owner, version, source identity, and evidence references.

An envelope is a semantic predicate, not prose such as “general non-Markovian support.” Unknown
operator families, feedback, memory transitions, dimensions, or Record layouts are
`UNKNOWN_SEMANTICS` or `UNSUPPORTED_SEMANTICS`; they are never ignored.

`CORE`, `OPTIONAL`, `RESEARCH`, and `ISOLATED_PLUGIN` describe current service placement. They do not
encode capability, exactness, family qualification, or scientific assurance.

## Record layout

The neutral layout freezes chronological measurement columns and explicit parity incidence before
execution:

```text
measurement_columns = [
  {ordinal, key, boundary, target, basis, readout_mapping, reset_mode}, ...
]

detector_rows = [
  {ordinal, name, columns, constant, coordinates}, ...
]

observable_rows = [
  {ordinal, name, columns, constant}, ...
]
```

Every `columns` list contains chronological measurement ordinals and denotes XOR over those columns.
The layout identity includes row order, constants, keys, bases, targets, reset modes, and all parity
operands. A backend may fill measurement outcomes but may not discover, reorder, or mutate the
layout from those outcomes.

The consecutive-check helper

```text
d[0,j] = s[0,j]
d[r,j] = s[r,j] XOR s[r-1,j]
```

is valid only when the layout explicitly selects that profile and declares the initial reference.
Final-closure detectors, nonadjacent parity checks, and Stim `DETECTOR` rows use the same general
incidence representation rather than a different Record type.

## Shot and acquisition contract

A Record law must state whether it concerns one shot, independent repeated shots, or an ordered
multi-shot acquisition. The support envelope and each execution bind:

```text
law_scope = SINGLE_SHOT_JOINT
          | INDEPENDENT_REPLICATE_BATCH
          | ORDERED_BATCH_JOINT

process_instance_scope = PER_SHOT | PER_BATCH | ACQUISITION
shot_boundary_transition = RESET | HOLD | ADVANCE_DECLARED
output_representation = RECORD_SEQUENCE
                      | CANONICAL_SUPPORT_GROUPED
                      | HISTOGRAM
                      | LAW_QUERY_ONLY
sample_order = EXECUTION_ORDER | NOT_PRESERVED | NOT_APPLICABLE
shot_ordinal_start, shot_count, acquisition_id
predecessor_or_continuation_identity
```

The following rules are binding:

- Memory that is held or advanced across shots requires `ORDERED_BATCH_JOINT`, `RECORD_SEQUENCE`,
  and `EXECUTION_ORDER` unless a separate proof authorizes a declared reduction.
- `INDEPENDENT_REPLICATE_BATCH` requires a per-shot process instance, a reset boundary, and no
  reused latent draw, advancing timeline, or carried memory.
- Canonically grouped output and histograms are permitted only for a compatible independent-
  replicate law or a separately proved reduction. The result must state that original sample order
  was not preserved.
- Acquisition chunks require continuous shot ordinals and an authenticated predecessor or
  continuation identity.
- A private memory checkpoint may bind continuation internally but remains evaluator-only; its
  contents never enter the public Record.
- “Shared across shots” is insufficient by itself. A declaration must distinguish one reused latent
  draw, one advancing timeline, and dynamically carried memory.

## Numerical guarantee and error ledger

Functional capability and numerical guarantee are orthogonal. The allowed guarantee classes are:

| Guarantee | Meaning |
|---|---|
| `ALGEBRAIC_EXACT` | The declared finite object is evaluated in an exact algebra with exact structural zeros. |
| `UNTRUNCATED_FLOATING` | No coefficient, branch, support, state, or bond cutoff is applied; floating and time-discretization error remain as declared. |
| `CERTIFIED_NUMERIC` | Numerical error on the requested output object has a rigorous enclosure or bound. |
| `BOUNDED_APPROXIMATION` | A declared approximation has a rigorous bound on one named output object or metric. |
| `UNBOUNDED_APPROXIMATION_RESEARCH` | The backend executes, but at least one approximation affecting the target lacks a valid output-level bound. |

Every run has separate ledger entries for `reduction`, `time_discretization`, `arithmetic`,
`truncation`, and `sampling`. Each entry is one of:

- `EXACT_ZERO`;
- `CERTIFIED_BOUND`, with metric, value, and derivation/reference;
- `HEURISTIC_OBSERVATION`, which cannot support a certification claim;
- `UNAVAILABLE`, with a reason.

Sampling uncertainty concerns an empirical estimate. It does not bound bias in the generator.
Local discarded weight, state fidelity, residual norm, bond dimension, active rank, or numerical
cutoff cannot populate a Record-law bound without a proved composition bridge.

## Three logical manifests

The three objects below must remain distinct even if a concrete format stores them in one bundle.

### Capability manifest

The static backend declaration contains:

```text
schema and producer identity
functional capabilities
semantic support envelope
Record and shot modes
supported numerical guarantees
resource guards
family-evidence owners
canonical content identity
```

It states what the backend promises to decide before seeing a particular result. It contains no
claim that a requested instance is supported or completed.

### Support decision

The pre-execution decision binds:

```text
request, QEC-program, error-process, Record-layout, and shot-contract identities
requested capability and numerical guarantee
matched capability-manifest identity
decision
explicit reductions and rejected fallbacks
reason codes
canonical content identity
```

The decision is exactly one of:

- `SUPPORTED`;
- `INVALID_INPUT`;
- `UNSUPPORTED_SEMANTICS`;
- `UNKNOWN_SEMANTICS`;
- `RESOURCE_BLOCKED_PREFLIGHT`.

A resource guard cannot be used to report unsupported semantics, and unsupported semantics cannot be
hidden as a resource failure. Pauli projection, time discretization, memory reset, output marginal,
or guarantee downgrade is legal only as an explicit new request with a new identity.

### Execution manifest

The post-execution object binds:

```text
support-decision identity
execution status
backend program and implementation identities
Record-layout and shot-contract identities
Record artifacts or law-query surface
numerical guarantee and complete error ledger
run-attestation and assurance references
seed, precision, environment, resource, and publication provenance
canonical content identity
```

Execution status distinguishes at least `COMPLETED`, `CENSORED_RESOURCE`, and `FAILED`. A censored
run may retain diagnostics but may not carry a partial correctness or completed-Record claim.

## Conformance falsifiers

At minimum, a capability implementation must reject or detect:

- a modified detector operand, constant, row order, or layout hash;
- non-binary Record input before dtype narrowing;
- an omitted or changed shot-boundary transition;
- a stateful acquisition relabelled as independent shots;
- canonically grouped rows relabelled as execution-order-preserving;
- an undeclared Pauli projection, time discretization, cutoff, or backend fallback;
- a resource-censored execution carrying completed Record output;
- latent variables or memory-checkpoint contents entering a public manifest;
- a claimed numerical guarantee whose ledger has an unavailable or heuristic load-bearing term.

Passing these falsifiers establishes contract discrimination only. Scientific assurance is governed
by `docs/FAITHFULNESS_PROTOCOL.md`.

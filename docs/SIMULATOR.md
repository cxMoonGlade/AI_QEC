# Simulator contract

This file is the binding product and scientific boundary for
`error_coupling_simulator` (ECS). It defines the stable simulated object and the claims that may be
made about it. It does not select a numerical representation, hardware target, code family, or
current implementation route.

The supporting contracts are:

- `docs/CAPABILITY_MODEL.md` for backend capabilities, semantic support, shot scope, and numerical
  guarantee declarations;
- `docs/FAITHFULNESS_PROTOCOL.md` for assurance claims and their evidence;
- `docs/METRICS.md` for registered quantities and epistemic classes;
- `docs/NUMERICAL_PROVENANCE.md` for value provenance;
- `docs/service_status.json` for the current implementation inventory.

When a dated validation packet uses an older policy, its result remains historical evidence for the
frozen experiment. It does not override this contract or automatically govern a new backend.

## Product charter

ECS classically evaluates a caller-declared quantum-error process interleaved with a quantum
error-correction (QEC) program. The declared process may contain spatial correlations, temporal
correlations, coherent persistence, classical latent memory, or explicitly declared quantum memory.
ECS models the error process at the program boundary; it does not require, infer, or claim a
microscopic open-system model.

A request contains three semantic inputs:

1. a QEC program, including operations, measurements, resets, timing where relevant, and declared
   detector and logical-observable definitions;
2. a declared error process, including its initial private-memory state and its within-shot and
   cross-shot transition semantics;
3. a requested capability and numerical guarantee.

The mathematical target is the induced joint law of the declared detector/observable `Record`.
A backend may expose this target through samples, probability queries, named Record functionals, a
structured law, or complete enumeration. It need not materialize the exponentially large probability
mass function unless complete enumeration was requested and accepted.

Every result must identify the request, support decision, backend, numerical guarantee, evidence
scope, and excluded claims. Unsupported semantics, unknown semantics, invalid input, and resource
exhaustion are different outcomes and must not be collapsed into a silent fallback.

## Record semantics

Let `m=(m_0,...,m_{n-1})` be the chronological binary measurement columns visible to the declared
Record layout. A detector or observable row is an explicitly declared parity function

```text
r_i = constant_i XOR XOR(m_j for j in columns_i).
```

The row order, constants, measurement operands, detector coordinates, and observable identifiers are
part of the QEC program and are frozen before execution. A backend may not infer them from sampled
outcomes. A multilevel measurement must first declare its readout/instrument mapping into the binary
coordinate consumed by the Record layout; hidden level labels remain a distinct evaluator-side
object.

The familiar repeated-check convention

```text
d[0,j] = s[0,j]
d[r,j] = s[r,j] XOR s[r-1,j]  for r >= 1
```

is one supported layout profile with an all-zero initial reference. It is not the universal detector
definition. Stim `DETECTOR` declarations and compiler-sealed XOR-incidence rows are equally direct
instances of the general parity contract.

The semantic `Record` is the ordered detector vector followed by the ordered logical-observable
vector. `carrier.records.RecordBatch`, `PackedShotBatch`, and little-endian `.b8` are current concrete
materializations; none is the only permissible representation of the law.

Raw measurements, latent variables, channel fields, trajectories, memory checkpoints, and mechanism
parameters are not part of the public `Record`. They may appear only on an explicitly evaluator-only
surface and must never enter downstream estimator input or public Record artifacts.

Structural probability zeros remain exact. A numerical floor, pruning threshold, pseudocount, or
underflow repair may not create probability mass. Invalid states, non-probability payloads, and
non-binary Record inputs fail closed before dtype narrowing.

## Capabilities and support

Capabilities describe what a backend can return; they do not certify that the result is correct. The
normative capability set and support decision are defined in `docs/CAPABILITY_MODEL.md`. In summary,
a backend may independently support:

- validation and compilation;
- Record sampling;
- Record or prefix scoring;
- a named Record functional;
- a normalized structured law;
- complete finite-support enumeration.

No capability is inferred from `CORE`, `OPTIONAL`, `RESEARCH`, a GPU implementation, or successful
execution. Every backend publishes a semantic support envelope covering at least its operation set,
local dimensions, measurement/reset behavior, feedback, error-map classes, spatial arity,
within-shot memory, cross-shot memory, Record layouts, and numerical guarantees.

A reduction is a new declared request, not a fallback. Pauli twirling, a detector error model (DEM),
time discretization, memory reset, coefficient pruning, branch pruning, or a backend substitution
must be caller-visible and must change the bound request identity.

If process memory persists or advances across shots, the requested object is an ordered batch law.
It cannot be represented as independent rows or a canonically grouped histogram unless an explicit
derivation establishes that reduction for the requested observable.

## Numerical guarantees

Every execution separates the following sources of error:

- model or representation reduction;
- time discretization;
- floating or exact arithmetic;
- state, coefficient, branch, bond, or support truncation;
- finite-sample uncertainty.

“Exact” is never an unqualified label. The allowed guarantee vocabulary distinguishes algebraically
exact execution, untruncated floating execution, certified numerical execution, bounded
approximation, and unbounded research approximation. A zero coefficient cutoff does not remove
roundoff or time-discretization error; a local discarded weight does not bound the Record law.

An approximation may support a claim only for the object covered by its bound. A global
detector/observable Record-law bound can support a full-law claim. A bound on one registered Record
functional can support only that functional. A local state, tensor, entropy, bond, active-rank,
treewidth, or residual diagnostic cannot be promoted to either claim without a proved bridge.

Resource guards may return a censored or unavailable result. They are not approximation parameters
and cannot turn partial execution into a partially correct Record.

## Assurance boundary

`docs/FAITHFULNESS_PROTOCOL.md` separates execution facts from scientific claims. Its assurance
classes are orthogonal rather than an automatic promotion ladder:

- `EXECUTION_ATTESTED` states what ran and what artifact was produced;
- `FAMILY_QUALIFIED` qualifies a backend within a frozen semantic envelope;
- `RUN_WITHIN_QUALIFIED_SCOPE` binds one run to that envelope;
- `METRIC_CERTIFIED` supports one named Record functional and band;
- `FULL_RECORD_LAW_CERTIFIED` supports the complete joint law within a declared bound;
- `SCIENTIFIC_GENERALIZATION_SUPPORTED` supports a separate cross-instance scientific claim.

Complete joint-Record total variation is the registered complete-law metric whose bound controls
every bounded Record functional. It is not a universal prerequisite for writing, executing, or
family-qualifying a sampler. A family may be qualified through independent lowering and primitive
checks, compositional closure, small complete Record laws, and corruption-sensitive temporal
controls. That evidence does not become a target-size full-law certificate.

A faithful operational-sampling claim for the declared process requires a qualified family, a
per-run support match, and a Record-law-level bound for every approximation affecting the sampled
Record distribution. A bound on one named functional is insufficient. An unbounded approximate
backend may remain an explicitly labelled research executor, but it cannot claim faithful sampling
of the original declared process.

`CODE_BLOCKED` is a workflow authorization recorded by a particular plan, not an assurance class.
A historical `CODE_BLOCKED` result remains binding for that frozen plan and artifact. The absence of
a target-size full-law oracle does not, by itself, prohibit a new experimental owner; the new owner
must instead freeze its capability contract, support envelope, independent small references,
composition proof obligation, and falsifiers before implementation. The completed compositional
argument is required for family qualification. Repository rules still require explicit user
confirmation before any `src/**` phase.

## Out of scope

ECS does not:

- infer an unknown device model, memory mechanism, or non-Markovianity from observed records;
- treat a declared process, paper parameter, or synthetic fixture as physical ground truth;
- simulate a microscopic bath by default;
- make calibration, parameter recovery, model selection, identifiability, or decoder-headroom a
  simulator service;
- make a decoder or DEM the simulated object;
- transfer record-memory evidence to reduced-map divisibility or process-tensor memory without an
  explicit bridge.

A DEM and decoder output may be explicit downstream products. State, channel, tensor, and latent
diagnostics may support implementation or certification, but they do not replace the declared Record
object.

## Current implementation and authority

Current services, owners, entry points, dependencies, outputs, support exclusions, and acceptance
files are machine-readable in `docs/service_status.json` and summarized in
`docs/ARCHITECTURE.md`. Route-specific contracts live in their owning module READMEs. Current
metrics, numerical defaults, and validation results live in their dedicated ledgers and dated
packets; they are not part of this stable product charter.

The package owns one runtime namespace, `error_coupling_simulator`. Unsupported artifact schemas are
rejected without compatibility fallback. External circuits, optional decoder inputs, explicit
derived-channel caches, and isolated plugins remain caller-declared boundaries rather than hidden
repository dependencies.

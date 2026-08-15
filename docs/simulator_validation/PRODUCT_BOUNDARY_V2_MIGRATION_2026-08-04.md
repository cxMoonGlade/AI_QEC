# Product-boundary v2 migration — 2026-08-04

Status: **DOCUMENTATION DECISION RECORDED; NO RUNTIME OR `src/**` CHANGE**.

## Decision

Retain the scientific object and remove implementation-history coupling from the product charter.
ECS remains a classical evaluator of a caller-declared quantum-error process interleaved with a QEC
program, with the detector/observable Record law as its mathematical semantics. The v2 contract is
backend-neutral and separates:

1. product semantics;
2. functional capability and semantic support;
3. numerical guarantee and error ledger;
4. assurance claim;
5. current implementation status and workflow authorization.

The contract does not expand ECS into a general microscopic open-system simulator. It permits an
explicit private-memory error model without claiming that the model is a physical bath or that
non-Markovianity was inferred from passive records.

## Why the previous contract was changed

At parent HEAD `9d04961e839e252c18f19b51f6b6a550c6da135b`, the previous
`docs/SIMULATOR.md` had SHA-256
`c6dad2415699b92e44b8116d8aa8a5e9b940f2f6c132e022326984769d45f689`. It combined a short product
definition with hundreds of lines of MPS, PEPS, PEPO, GCAMPS, GPU, publication, mutation, and current
validation state. Three consequences followed:

- “GPU-first” and route names acted as product requirements rather than implementation choices;
- one adjacent-round syndrome fold was written as the universal detector definition;
- execution, backend qualification, metric evidence, complete Record-law certification, and
  workflow permission were treated as one gate.

The last coupling created a circular development rule: a target-size complete-law oracle was treated
as a prerequisite for an experimental scalable owner even though such an oracle is often the object
the owner is meant to replace.

## Stable invariants retained

- The caller declares the QEC program and error process.
- The semantic target is the detector/logical-observable Record law.
- Private process state never enters the public Record or downstream estimator input.
- Structural probability zeros remain exact.
- Unsupported semantics and silent reductions fail closed.
- A DEM, decoder, calibration, model selection, and device inference remain outside or downstream.
- Local state or representation diagnostics do not become Record evidence without a proved bridge.
- Independent references, corruption falsifiers, and numerical provenance remain mandatory for the
  assurance claim that uses them.

## v1-to-v2 mapping

| Previous coupled question | v2 owner |
|---|---|
| What is simulated? | `docs/SIMULATOR.md` |
| What can this backend return and on which semantics? | `docs/CAPABILITY_MODEL.md` |
| What was executed? | `EXECUTION_ATTESTED` plus the execution manifest |
| Is this backend qualified for a family? | `FAMILY_QUALIFIED(scope)` |
| Is one Record functional certified? | `METRIC_CERTIFIED(metric, regime, band)` |
| Is the complete joint law certified? | `FULL_RECORD_LAW_CERTIFIED(metric, bound)` |
| May a frozen plan change code? | plan-local workflow authorization, separate from assurance |
| Which routes exist today? | `docs/service_status.json`, module READMEs, and validation packets |

Metric epistemic class `(a)/(b)/(c)`, numerical provenance kind, certification verdict, service
status, and assurance claim remain orthogonal. None strengthens another automatically.

## Historical no-cutoff overlay

The 2026-08-03 target-lowering result remains byte-for-byte historical evidence. Its frozen plan
validated and attested 32 static neutral/pair/ADD-relation/TN programs and executed no target solver
or route metric. Its recorded `solver_permission=CODE_BLOCKED` remains correct for that
preregistration and does not change.

For current planning, the same evidence maps to:

| Assurance claim | Current disposition | Evidence boundary |
|---|---|---|
| `EXECUTION_ATTESTED` | `ESTABLISHED` | Static lowering artifacts and independent receipts only. |
| `FAMILY_QUALIFIED` | `NOT_ESTABLISHED` | Static definitions exist; no target owner or compositional family proof was executed. |
| `RUN_WITHIN_QUALIFIED_SCOPE` | `NOT_APPLICABLE` | No target owner ran. |
| `METRIC_CERTIFIED` | `NOT_ESTABLISHED` | No target route metric ran. |
| `FULL_RECORD_LAW_CERTIFIED` | `UNANCHORED` | No eligible complete-law reference or global bound exists for the target cells. |
| `SCIENTIFIC_GENERALIZATION_SUPPORTED` | `NOT_ELIGIBLE` | No target execution or cross-instance result exists. |

This mapping neither promotes a route nor fills a missing metric. It removes only the inference
“Complete-law certification is unavailable, therefore no experimental owner may be built.”

## Development and promotion rule

A new experimental owner may be proposed after freezing its capability/support contract, neutral
lowering, independent small reference, composition proof obligation, and falsifiers. It does not
require a completed family proof or target-size complete-law oracle before implementation.

A faithful operational-sampling claim for the original declared process requires family
qualification, a per-run scope match, and a Record-law-level bound for every approximation affecting
the sampled Record distribution. A metric-only bound is insufficient. A named scientific functional
requires metric-specific certification. A statement about the complete law requires a global law
bound. Cross-distance, asymptotic, device, or mechanism conclusions require a separate
generalization packet.

This decision changes no installed service and grants no `src/**` authorization. Existing routes
retain their current local evidence and exclusions until they are explicitly mapped and qualified
under the v2 contracts.

## Known source-documentation debt

Package-local prose in `src/error_coupling_simulator/README.md`,
`src/error_coupling_simulator/carrier/kernels/README.md`, and several source docstrings still records
the v1 GPU-first or consecutive-fold wording. It is not current product authority; the generated
`docs/CODE_MAP.md` may faithfully surface that stale prose until a separately authorized `src/**`
documentation phase updates it. Distribution metadata now uses the root `README.md`, so the
published project description follows the v2 boundary without rewriting runtime sources in this
decision.

The project execution skill at `.agents/skills/project-engine-ecs/SKILL.md` also retains v1
route-frontier examples. Its own authority order puts `docs/SIMULATOR.md` first, so those examples do
not override v2, but they should be rewritten in a separate skill-maintenance phase to remove the
remaining planning bias.

## Document placement

- The stable charter is intentionally short and route-neutral.
- Capability and support semantics live in `docs/CAPABILITY_MODEL.md`.
- Assurance and evidence live in `docs/FAITHFULNESS_PROTOCOL.md`.
- Metrics and value provenance retain their existing ledgers.
- Current implementations remain in `docs/service_status.json`, `docs/ARCHITECTURE.md`, module
  READMEs, and `tests/CODEBOOK.md`.
- Dated preregistrations and results remain immutable historical packets.

The next clean research session should treat the v2 charter and capability/assurance contracts as
design constraints, and treat current route histories only as evidence about inspected candidates.

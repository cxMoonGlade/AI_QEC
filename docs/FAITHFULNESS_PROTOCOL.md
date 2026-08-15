# Faithfulness and assurance protocol

This protocol governs claims that an `error_coupling_simulator` (ECS) backend realizes a declared
error-to-Record object or a named functional of that object. It separates execution facts, reusable
family qualification, instance-specific metric certification, complete-law certification, and
scientific generalization.

`docs/SIMULATOR.md` defines the product. `docs/CAPABILITY_MODEL.md` defines capabilities and support.
`docs/METRICS.md` defines registered quantities. `docs/NUMERICAL_PROVENANCE.md` defines where values
come from and what physical interpretation they may support.

## Orthogonal classifications

The following classifications answer different questions and must not be substituted for one
another:

| Classification | Question answered |
|---|---|
| capability | What operation or query can the backend perform? |
| assurance claim | What correctness or scientific statement is supported? |
| metric epistemic class `(a)/(b)/(c)` | Is a registered value exact, a prediction-band result, or a heuristic gate? |
| numerical provenance kind | Where did a value come from and what physical interpretation is allowed? |
| certification-plan verdict | What happened when one frozen evidence plan ran? |
| workflow authorization such as `CODE_BLOCKED` | What implementation action did that plan permit at that time? |

An exact class-(a) static artifact may still lack family qualification. A paper-measured parameter
does not certify a sampler. A `PASS` has meaning only with the object, metric, regime, and plan that
produced it.

## Assurance claims

These claims are orthogonal scopes, not an automatic promotion ladder.

| Claim | Permitted statement | Minimum evidence |
|---|---|---|
| `EXECUTION_ATTESTED` | A bound request was executed by a named implementation and produced schema-valid artifacts. | Input/program/backend identities, support decision, runtime invariants, output schema, truth firewall, numerical ledger, and provenance. |
| `FAMILY_QUALIFIED(scope)` | A backend realizes a frozen semantic family within a declared grammar, mechanism, precision, and horizon. | Independent primitive and lowering checks, compositional closure or induction, small complete Record fixtures, temporal-memory controls, and corruption falsifiers. |
| `RUN_WITHIN_QUALIFIED_SCOPE` | This run matches a qualified family scope and introduced no undeclared change or approximation. | Per-run scope match, translation validation, execution ledger, and all required run invariants. |
| `METRIC_CERTIFIED(metric, regime, band)` | One named Record functional satisfies its registered comparison or bound. | A metric-matched independent reference or rigorous bound, preregistered band, and discriminating controls. |
| `FULL_RECORD_LAW_CERTIFIED(metric, bound)` | The complete detector/observable joint law satisfies the declared global bound. | An independent complete law or a compositional proof with a certified global Record-law error bound. |
| `SCIENTIFIC_GENERALIZATION_SUPPORTED(scope)` | A result generalizes across a stated distance, horizon, device, or mechanism family. | Separate literature closure, preregistration, cross-instance evidence, uncertainty treatment, and rival explanations. |

`EXECUTION_ATTESTED`, `FAMILY_QUALIFIED`, and `RUN_WITHIN_QUALIFIED_SCOPE` do not imply
`METRIC_CERTIFIED` or `FULL_RECORD_LAW_CERTIFIED`. Metric certification covers only the named
functional and does not transfer to another functional. Complete-law certification is the only
general route here for transferring a total-variation bound to every bounded Record functional.
Scientific generalization is a separate argument rather than a reward for accumulating other
labels.

## Family qualification without target-size enumeration

A sampler may be family-qualified without enumerating the target-size probability mass function
when all of the following are available:

1. an evaluator-truth-free neutral program and an independently reconstructed source-to-event
   lowering;
2. independent checks of every supported conditional instrument, error update, measurement, reset,
   and Record-parity primitive;
3. a closure or induction argument showing that those primitives compose within the frozen grammar;
4. small complete Record-law fixtures, including structural zeros and non-degenerate persistent-
   versus-IID temporal controls;
5. a support predicate binding operation set, dimensions, memory, precision, horizon, and shot
   semantics;
6. per-run translation validation, normalization, provenance, and corruption-sensitive controls.

This route can establish `FAMILY_QUALIFIED` and `RUN_WITHIN_QUALIFIED_SCOPE`. It does not establish
a target-instance `FULL_RECORD_LAW_CERTIFIED` claim unless the composition argument also supplies a
certified global Record-law bound, including numerical error.

## Required gate for family, metric, and complete-law claims

### Freeze the object and coordinate

Name the QEC program, declared error process, backend, support envelope, Record coordinate, shot
contract, precision, capability, metric where applicable, and supported horizon. Do not compare raw
measurements with detector events, a DEM with an analog process, an unordered histogram with an
ordered acquisition, or a state quantity with a Record-law claim.

### Use an independent reference or derivation

The evidence must be capable of failing differently from the implementation under test. Accepted
forms include:

- an exact or separately formulated density-matrix calculation;
- a raw caller-supplied program with independently checked semantics;
- a closed-form identity derived from a verified primary source;
- a from-scratch reconstruction sharing neither the production lowering nor the suspected
  simplification;
- for `FAMILY_QUALIFIED`, independent lowering and per-event instruments plus a complete
  compositional argument.

Agreement with an implementation's own helper, cache, compiler payload, or reformatted output is a
regression check. It is not independent evidence.

If no eligible independent reference, derivation, or rigorous bound exists for a requested
`METRIC_CERTIFIED` or `FULL_RECORD_LAW_CERTIFIED` claim, that claim is `UNANCHORED`. This does not
negate an independently established execution, family, or run-scope claim.

### Require discriminating falsifiers

Every load-bearing invariant needs a deliberate corruption that the gate rejects while the unchanged
positive path passes. The corruption must change the claimed object. Inert controls, skipped controls,
and allowlisted failures do not close a claim.

Falsifiers must cover, where applicable, source lowering, operator sign/support/order, persistent
versus resampled memory, measurement/reset instruments, Record incidence, structural zeros, shot
order, approximation ledgers, and evaluator-truth isolation.

### Declare and bound simplifications

Every projection, factorization, finite-step approximation, precision change, fitted contraction,
truncation, or reduced representation declares:

- what object it changes;
- where and when it is applied;
- the output metric it is claimed to control;
- a rigorous bound or an independent paired comparison in the claimed regime.

A simplification with neither a valid bound nor an eligible independent paired comparison on the
named output cannot support faithful sampling of the original declared process or the corresponding
metric/complete-law claim. It may remain an `UNBOUNDED_APPROXIMATION_RESEARCH` execution. A bound
that closes one named functional can support only that `METRIC_CERTIFIED` claim; it does not repair
the complete Record law. Resource caps and local tensor objectives remain implementation diagnostics
unless a proved bridge connects them to the named Record metric.

### Freeze numerical provenance

Every claim-bearing value follows `docs/NUMERICAL_PROVENANCE.md`: source kind, exact locator, units,
scope, and transformation chain. Literature equations justify a form, not an uncited amplitude.
Project defaults, floating tolerances, clean artifacts, and resource limits are not evidence of
hardware realism or sampler correctness.

## Operational eligibility

The following are distinct decisions:

- Experimental-owner development may begin after a neutral lowering, capability/support contract,
  independent small owner, composition proof obligation, and preregistered falsifiers are frozen.
  It does not require a completed family proof or target-size complete-law oracle.
- A faithful operational-sampling claim for the declared process requires `FAMILY_QUALIFIED` plus
  `RUN_WITHIN_QUALIFIED_SCOPE`, plus a Record-law-level bound for every approximation affecting the
  sampled Record distribution. A metric-only bound is insufficient.
- Certification of a particular logical-error rate, correlation, or other Record functional
  requires the matching `METRIC_CERTIFIED` claim.
- A statement that the entire joint Record law is within a global distance requires
  `FULL_RECORD_LAW_CERTIFIED`.
- Cross-distance, cross-round, asymptotic, hardware, or physical-origin statements require
  `SCIENTIFIC_GENERALIZATION_SUPPORTED`.

Repository implementation authorization remains separate. In particular, every `src/**` phase
still requires explicit user confirmation and a reviewed phase diff.

## Certification-plan verdicts

Existing runtime verdicts remain plan-local outcomes:

- `PASS` — every required exact row and control in the named plan passed;
- `PASS*` — exact rows and controls passed while sampled comparisons detected no discrepancy at the
  registered plan; this is not proof of the sampler law;
- `FINDING` — a registered prediction or comparison missed its band;
- `FAIL` — an exact invariant failed or a required control was inert;
- `UNANCHORED` — the requested claim lacks a feasible independent reference;
- `CONTROL` — an explicit falsifier row, never a positive result.

A verdict maps to an assurance claim only when its evidence packet explicitly names that claim and
meets its requirements. Backend cost, reference infeasibility, plausible output, or schema-valid
execution cannot upgrade a verdict.

## Historical policy and non-retroactivity

Historical preregistrations, results, hashes, and `solver_permission` fields are immutable evidence.
Their `CODE_BLOCKED` value continues to describe the action permitted by that frozen plan under the
then-current policy. Under this contract it does not become a product-wide assurance label or a
permanent ban on another experimental owner.

For the 2026-08-03 no-cutoff target-lowering result, the non-retroactive claim/disposition mapping is
recorded in `docs/simulator_validation/PRODUCT_BOUNDARY_V2_MIGRATION_2026-08-04.md`. It does not
rewrite the result artifact, populate a missing architecture metric, select a route, or authorize
`src/**` work.

## Evidence packets

Evidence is reusable only at its declared scope.

An execution/run-attestation packet contains the bound request and program, support decision,
backend and implementation identities, complete numerical ledger, runtime invariants, Record
artifacts, provenance, and exclusions.

A family-qualification packet additionally contains the frozen semantic envelope, independent
lowering and primitive references, composition argument, complete small-law fixtures, temporal and
structural controls, versioned support predicate, and corruption results.

A metric/complete-law packet additionally contains the exact metric, regime, comparison band or
bound, independent reference and independence argument, raw values, uncertainty treatment, and
claim-specific verdict. A scientific-generalization packet separately contains the literature
closure, preregistration, cross-instance design, rival explanations, and generalization boundary.

Missing items stop only the claim that requires them. Test success proves the object named by the
test; it does not automatically certify another backend, distance, horizon, device, metric, or the
complete Record law.

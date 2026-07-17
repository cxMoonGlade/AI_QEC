# Restricted MPS repair and consolidation plan v3 — 2026-07-17

## Status and authority

Status: **proposed implementation plan; no `src/**` change is authorized by this document**.

Baseline: repository `HEAD 29cf949` on 2026-07-17. This document promotes and replaces the two
unversioned 2026-07-16 scratchpad plans. It contains no `qec_twin` code, owner, compatibility path,
or defect identifier. It is self-contained: no identifier depends on those scratchpads or on an
unregistered K/M ledger.

Binding authority remains:

- [`docs/SIMULATOR.md`](../SIMULATOR.md), especially the Record contract and restricted MPS scope;
- [`CONTEXT.md`](../../CONTEXT.md), especially Carrier, Record, Reference oracle, and Record
  faithfulness;
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) and
  [`docs/service_status.json`](../service_status.json) for current ownership;
- [`docs/FAITHFULNESS_PROTOCOL.md`](../FAITHFULNESS_PROTOCOL.md),
  [`docs/NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md), and
  [`docs/METRICS.md`](../METRICS.md) for evidence and numerical claims.

Retained evidence inputs, which do not override those contracts, are:

- [`TENSOR_NETWORK_TRUNCATION_DIFFERENTIAL_AUDIT_2026-07-16.md`](TENSOR_NETWORK_TRUNCATION_DIFFERENTIAL_AUDIT_2026-07-16.md);
- [`TENSOR_NETWORK_CARRIER_ROLE_AND_IMPROVEMENT_ROUTE_2026-07-16.md`](TENSOR_NETWORK_CARRIER_ROLE_AND_IMPROVEMENT_ROUTE_2026-07-16.md);
- [`TENSOR_NETWORK_TRUNCATION_REPAIR_VALIDATION_2026-07-16.md`](TENSOR_NETWORK_TRUNCATION_REPAIR_VALIDATION_2026-07-16.md);
- [`TENSOR_NETWORK_CARRIER_LITERATURE_AUDIT_2026-07-16.md`](TENSOR_NETWORK_CARRIER_LITERATURE_AUDIT_2026-07-16.md).

The current scientific disposition remains:

- `RECORD_BRIDGE_OPEN`;
- `PRODUCTION_PRUNING_CODE_BLOCKED`;
- restricted QT/MPS and MCWF/MPS are verification routes, not production full-record backends;
- `max_bond=None` remains the default, so this plan does not claim that production pruning already
  exists;
- PEPS/FET is outside this plan and its RED scientific gates remain RED.

Every phase that changes `src/**` requires a separate user confirmation and a reviewed phase diff.

## 1. Frozen architectural decision

Consolidate the shared MPS **Carrier mechanics**, not the two scientific evolution laws.

QT/MPS and MCWF/MPS are two real evolution Adapters at a real Seam:

| Property | QT/MPS Adapter | MCWF/MPS Adapter |
|---|---|---|
| Scientific object | finite-step product-channel branch enumeration or sampling | finite-step quantum-jump pure-state trajectory |
| Hamiltonian rule | declared term-order product formula | connected-support Hamiltonians grouped before exponentiation |
| Collapse rule | sequential Kraus branching | joint jump/no-jump candidate competition |
| State space | current qubit-only restricted route | current d=2/3/4 and leakage route |
| Record sampling | exact branches or sampled branches | sampled trajectories |
| Law-specific diagnostic | branch-count and product-formula limits | preflight/runtime mass residual and finite-step limits |

Their substep loops, Hamiltonian grouping, Kraus/jump selection, RNG event order, support preflight,
occurrence inventory, and acceptance policy must remain explicit in their respective Adapters. No
shared Module may silently grant QT multilevel support or convert MCWF into term-order evolution.

There will be no `axis1_mps_chassis.py`, no route-mode god Module, and no runtime defect-compatibility
switch. The target ownership is:

| Responsibility | Target owner | Must not own |
|---|---|---|
| Quimb-backed MPS state, copy/commit, norm, projection, unitary application, and raw split events | a README-owned `carrier/mps/` Module | Axis-1 operator-family policy, manifest verdicts, dense certification |
| Actual finite-bond two-site split implementation | internal Quimb implementation in `carrier/mps/`; preserve the current authenticated algorithm | arbitrary multi-site evolution or acceptance policy |
| QT product-channel control flow and QT manifest | QT frontend Adapter | MCWF mass-residual policy or multilevel support |
| MCWF quantum-jump control flow and MCWF manifest | MCWF frontend Adapter | QT exact-branch semantics |
| Schedule-derived immutable measurement layout and temporal XOR construction | the shared Axis-1 Record owner, outside the MPS numerical Module | MPS state mutation or trajectory-dependent schema discovery |
| Raw truncation-event validation and law-neutral aggregation primitives | `carrier/mps/` | route-specific occurrence definitions or final acceptance |
| Dense Reference oracle, metric evaluation, and restricted acceptance | `certify/` | Carrier mutation or self-certification |
| Public routing and final manifest composition | `frontend/` | duplicated MPS tensor algebra |

Required dependency direction:

```text
frontend QT/MCWF Adapters ──> shared Record owner
             │
             └──────────────> carrier/mps

certify ──> immutable raw execution evidence + independent references
frontend ──> certify result when composing a final evidence manifest
```

`carrier/mps` must not import `frontend` or `certify`. MCWF must not import private QT symbols, and QT
must not import private MCWF symbols. A line-count target is not an architectural acceptance gate;
Depth, Locality, dependency direction, and falsifier coverage are.

## 2. Acceptance state machine

Execution completion and scientific certification are orthogonal facts. The repaired manifest family
must expose both and may bump schema versions when the fields or semantics change. Diagnostic scope is
a separate boolean/disposition; it is not a third passing verdict.

| Execution status | Certification status | Top-level verdict | Diagnostic only | Meaning |
|---|---|---|---|---|
| blocked or failed | `not_evaluated` or `unavailable` | `fail` | false | invalid input, unsupported schedule, preflight failure, or execution failure |
| completed | `rejected` | `fail` | false | execution produced evidence but a required gate failed |
| completed | `not_evaluated` or `unavailable` | `fail` | true | useful diagnostic payload that cannot certify restricted execution |
| completed | `accepted` | `pass` | false | all mandatory restricted gates and required independent checks passed |

Hard rules:

- `pass` is equivalent to `accepted_for_restricted_execution=true`; every other state has verdict
  `fail`.
- `mass_residual_budget=None` is convergence-diagnostic-only. It is marked diagnostic-only, never
  yields `pass`, and has certification status `not_evaluated`.
- NaN, Inf, bool-as-number, missing mandatory evidence fields, negative probabilities, nonfinite
  state norms, and nonfinite gate values fail closed.
- An over-cap execution without an independent Record oracle may complete, but its certification is
  `unavailable`, its verdict is `fail`, and it is marked diagnostic-only; empirical count
  normalization cannot certify it.
- Preflight mass bound, runtime raw candidate mass, runtime mass residual, empirical count
  normalization, and truncation loss remain separate fields with separate semantics.
- `accepted_for_production_scalable_backend` remains false throughout this plan.

## 3. Self-contained defect and gate registry

The identifiers below are local to the current restricted MPS plan and use the `MPS-` prefix to avoid
collision with retired or unrelated project ledgers. Phase 0 must convert every confirmed item into a
versioned test or committed diagnostic before its source fix is accepted.

| ID | Owner/route | Severity | Confirmed defect or missing gate | Required durable gate | Planned phase |
|---|---|---:|---|---|---:|
| `MPS-001` | MCWF connected >=3-site cluster application | blocker | the reachable MCWF `auto-mps` nonlocal decomposition can inherit an internal nonzero cutoff and silently delete a weak term while the route reports no requested truncation | hand-constructed dense operator/state reference; weak 3-site MCWF cluster; resource-cap falsifier; support/order corruption test; package-wide static negative gate requiring every Quimb decomposition call to carry an explicit named `cutoff=` argument | 0, 2 |
| `MPS-002` | MCWF certification | blocker | `mass_residual_budget=None` or NaN can bypass preflight, and over-cap acceptance can ignore runtime mass residual | 9-qubit over-cap `None`/NaN fixtures; runtime residual must prevent `pass`; state-machine assertions | 0, 1 |
| `MPS-003` | shared numerical gates/certification | blocker | bond/seed/dense/resource gates accept NaN/Inf; missing truncation-ledger keys can default to a passing zero | NaN, Inf, bool, missing-key, negative, and equality-edge falsifiers for every gate family | 0, 1 |
| `MPS-004` | QT sampled Record path | blocker | only the first measurement boundary is registered while later outcome bits are appended | schedule-derived two-boundary layout with hand-written keys/targets/XOR; independent dense Record comparison | 0, 3 |
| `MPS-005` | MCWF Record/reset policy | high | merged multi-record measurement substeps with reset can silently skip reset | compiler-reachable double-MR controlled fixture; structured fail-closed or explicitly supported behavior | 0, 3 |
| `MPS-006` | shared probability primitives, route policies separate | high | hard-coded `1e-15` cuts turn legal positive physical mass into undeclared structural zero; `1-exp(-x)` can create a false endpoint | tiny-positive branch fixtures; `expm1` endpoint checks; exact-zero versus representability falsifier; dropped-mass absence check | 0, 4 |
| `MPS-007` | MCWF reset/measurement mutation | high | zero or nonfinite post-operation norm can propagate without a loud failure | exact-zero, tiny-positive, NaN, and Inf norm fixtures; finite/representability policy pinned | 0, 4 |
| `MPS-008` | route configuration | high | integer/real controls are narrowed before validation | bool/float/string/non-integral property table for every public MPS control | 0, 4 |
| `MPS-009` | QT support preflight | high | `COH_*` can pass QT preflight and fail later although MCWF legitimately supports those families | QT structured blocker fixture plus MCWF supported-family counter-fixture | 0, 4 |
| `MPS-010` | exact-bond sufficiency helper | low | odd-site qubit bound uses `ceil(n/2)` and over-blocks valid exact representations | exhaustive small local-dimension cut-product reference | 0, 4 |
| `MPS-011` | sampling primitive with route-specific policy | high | candidate probabilities are silently renormalized without exposing/validating raw total mass | finite/nonnegative candidate property tests; QT Kraus, projective measurement, and MCWF jump semantics tested separately | 0, 4 |
| `MPS-012` | QT sampled metadata | low | reset substeps can be mislabeled in `applied_substeps` | exact expected metadata fixture | 0, 3 |
| `MPS-013` | MCWF preflight | high | reset substeps containing dynamics can silently omit evolution; missing `dt` can surface as an unstructured runtime error | compiler/program controlled fixtures for both cases; structured blocker | 0, 3 |
| `MPS-014` | QT sampled resource safety | high | per-boundary and final record enumeration is exponential and lacks an early fail-closed resource guard | small declared measurement budget; over-budget no-allocation falsifier; later distribution-equivalent linear sampler | 0, 1 guard; 7 algorithm |
| `MPS-015` | test ownership | prerequisite | current MPS execution/contract/certification Modules have no dedicated coverage/mutation registry | registry reconciliation and measured pre-change coverage/mutation baseline | 0 |
| `MPS-016` | independent regression gates | prerequisite | MCWF finite-bond manifest, actual-split wiring, and fine-grained norm-reconciliation corruption gates are incomplete | independent bounded dense/SVD reconstruction plus swapped-topology and norm corruption falsifiers; adapter-versus-Quimb retained and labeled wiring-only | 0 |
| `MPS-017` | ownership and documentation cleanup | cleanup | dead gate builders, stale “backend not implemented” contract text, kept-dimension/rank ambiguity, and evaluator-only wording remain | reference scan, public-entry inventory, documentation assertions, generated map check | 5, 6 |

The optional emission of full singular-value spectra is not part of the repair. It changes payload size
and schema and requires a separate need and provenance decision.

## 4. Evidence discipline

### 4.1 Independent references

| Claim being checked | Required independent evidence | Evidence that is useful but not independent |
|---|---|---|
| nonlocal/multisite gate application | hand-typed dense operator, independently lifted site order, dense state evolution, corrupted support/order falsifier | calling the same production gate builder; Quimb against its own wrapper |
| actual finite-bond split and truncation event | independent dense/SVD reconstruction on a bounded tensor plus deliberately corrupted discarded weight | adapter-versus-Quimb comparison, which checks wiring only |
| Record layout and XOR law | hand-written expected schedule layout and detector/observable fold; bounded dense Record oracle | QT exact versus QT sampled after they share the layout Module |
| sampled distribution | declared standard distance/confidence rule against exact bounded probabilities | same-seed bitwise equality after changing RNG draw order |
| acceptance policy | corruption falsifier for every mandatory field/gate and explicit state-machine table | a normalized empirical count histogram |

No test may call the implementation path it is intended to reconstruct. Differential external
libraries remain comparators, not physical truth.

### 4.2 Characterization and golden policy

- Characterization fixtures freeze only healthy, deterministic, contract-bearing fields.
- No known fail-open behavior, malformed Record, error string, or broken manifest is promoted into a
  new Module through a quirk switch.
- RED falsifiers preserve the violated invariant, not byte-for-byte failure signatures.
- Resource/timing fields are excluded from deterministic golden projections.
- Manifest hashes may be pinned only after the semantic projection and schema are frozen.
- Mutation score is a test-sensitivity instrument. Acceptance requires no surviving critical
  corruption, not merely a nondecreasing aggregate percentage after the denominator changes.

## 5. Phased implementation

Each phase is a separately reviewed vertical slice. A phase that introduces or moves a Module updates
its README, `docs/service_status.json`, generated `docs/CODE_MAP.md`, and the matching test registry in
the same diff. The canonical fresh-process acceptance plan is always expanded from the current catalog;
no historical file count is a target.

### Phase 0 — durable RED/green evidence and ownership baseline (`src/**` unchanged)

1. Add a dedicated restricted-MPS coverage/mutation registry covering the two execution Adapters, two
   contract Modules, actual-split implementation, and certification owner.
2. Commit the confirmed counterexamples for `MPS-001` through `MPS-014`. A RED checkpoint is explicitly
   non-merge-ready and records the exact violated invariant.
3. Add an AST-based package-wide negative gate for `MPS-001` over
   `src/error_coupling_simulator/**/*.py`. Every Quimb operation that can decompose or compress a
   tensor network must carry a named `cutoff=...` argument at the call site. Positional cutoff values,
   `**kwargs`-only propagation, wrapper defaults, global configuration, and inheritance of Quimb's
   internal default all fail the scan. The scanner maintains an explicit registry of decomposition
   APIs and decomposition-triggering `gate`/`gate_` contract modes, and fails closed on an unresolved
   dynamic mode rather than silently excluding it. Non-decomposing one-site `contract=True` calls are
   outside this gate. A scanner self-test must prove that removing `cutoff=` from a representative call
   turns the gate RED.
4. Add the currently missing green gates in `MPS-016` before moving their implementation:
   MCWF finite-bond manifest wiring, independent bounded dense/SVD actual-split reconstruction,
   swapped-topology and fine-grained norm corruption falsifiers, and an adapter-versus-Quimb wiring
   comparison that is explicitly not an independent scientific oracle.
5. Freeze healthy semantic projections across QT exact, QT sampled, and MCWF sampled fixtures. Do not
   freeze known-broken outputs.
6. Record measured per-Module coverage, branch coverage, killed/surviving critical mutations, current
   source hash, environment lock, and the dynamically expanded fresh-process acceptance plan.

Exit: every registry owner is reconciled; every confirmed defect has a durable falsifier; all existing
healthy tests remain green; RED tests are itemized and attributable.

### Phase 1 — false-green firewall and early resource safety

Scope: `MPS-002`, `MPS-003`, and the fail-closed guard half of `MPS-014`.

1. Implement the frozen execution/acceptance state machine.
2. Validate every numerical gate and mandatory evidence field before comparison.
3. Make runtime MCWF raw mass/residual mandatory input to restricted acceptance.
4. Reject NaN/Inf budgets and make `None` diagnostic-only.
5. Add a declared QT measurement/record materialization budget checked before exponential allocation.
6. Retire true-over-cap restricted acceptance. Execution evidence may still be emitted, but when no
   independent Record oracle is available it must end in `certification_status="unavailable"`,
   `verdict="fail"`, `diagnostic_only=true`, and both restricted-acceptance flags false. The QT child
   manifest and the enclosing Carrier manifest must agree.

This is an intentional public behavior tightening, not an incidental test fallout:

| Surface | Before Phase 1 | Required Phase 1 behavior | Deliberately affected assertions/consumers |
|---|---|---|---|
| QT true-over-cap execution with no independent Record oracle | a completed backend run could set `accepted_as_restricted_overcap_execution=true`, `accepted_for_restricted_execution=true`, and `verdict="pass"` | retain execution and diagnostic evidence, but set both acceptance flags false, certification `unavailable`, diagnostic-only true, and verdict `fail` | `test_axis1_qt_mps_restricted_execution_records_over_cap_h_readout_zero_collapse` must change from pass/true to fail/false |
| Carrier wrapping that QT result | the child pass propagated to a top-level Carrier pass | the top-level Carrier verdict must remain fail; completion must not be promoted into certification | `test_axis1_carrier_execution_qt_mps_backend_records_over_cap_h_readout` and consumers of the top-level `passed` field must change deliberately |
| MCWF true-over-cap execution with no independent Record oracle | already diagnostic-only/fail in the retained fixtures | remain diagnostic-only/fail and use the same state-machine meaning; no new acceptance alias | existing MCWF over-cap diagnostic fixtures remain negative controls |

Any schema version or content hash affected by this semantic change must be bumped or regenerated in
the same phase. Consumers must use `accepted_for_restricted_execution`; backend completion and empirical
normalization are not substitute acceptance signals.

Exit: no NaN/Inf/missing-key/override path can produce `pass`; over-budget QT sampled work fails before
allocation; the enumerated over-cap tests and consumers have changed deliberately rather than being
silently accommodated; affected schemas and provenance are updated deliberately.

### Phase 2 — MCWF uncapped nonlocal reference integrity

Scope: `MPS-001`.

1. Introduce the smallest README-owned Quimb Carrier Module needed for an uncapped nonlocal application;
   do not broaden the authenticated finite-bond two-site actual-split implementation.
2. Fix only the confirmed, reachable MCWF connected >=3-site cluster path. Keep a QT nonadjacent
   two-site fixture as a shared-mechanics regression, not as a second reproduction of `MPS-001`.
3. Use explicit no-requested-truncation decompositions, candidate mutation, finite/norm checks, and
   transactional commit.
4. Make every package Quimb decomposition call satisfy the Phase 0 named `cutoff=` static gate. The
   route-specific numerical tests separately prove whether that explicit cutoff means requested
   no-truncation or a declared truncation policy; the static gate alone is not a correctness oracle.
5. Freeze a pre-allocation support/Hilbert/tensor resource cap. Above the cap, fail closed rather than
   constructing an exponential dense blob.
6. Validate against the independent dense fixtures and corruption falsifiers from Phase 0.

Exit: the weak-term counterexample agrees with the independent complex128 reference within the frozen
band; microstep refinement no longer deletes the term; over-cap work fails before allocation; no result
is called mathematically exact beyond the declared numerical meaning.

### Phase 3 — schedule-derived Record layout and route-specific Record correctness

Scope: `MPS-004`, `MPS-005`, `MPS-012`, and `MPS-013`.

1. Parse measurement keys, targets, widths, reset declarations, and detector/observable XOR layout once
   from the sealed schedule before any trajectory begins.
2. Make the parsed layout immutable. Trajectories may fill outcomes but may not register or mutate the
   Record schema.
3. Keep QT and MCWF measurement state operations and support preflight in their own Adapters.
4. Fix or structurally block multi-record reset cases and dynamics-bearing reset/measurement substeps.
5. Validate the Record law against hand-written expected layouts and an independent bounded oracle, not
   only QT exact versus QT sampled.

Exit: multi-boundary QT sampled Records, temporal XOR, reset metadata, and MCWF reset policy pass their
independent falsifiers; no Record schema depends on `trajectory_index == 0`.

### Phase 4 — probability, configuration, and route support hygiene

Scope: `MPS-006` through `MPS-011`.

1. Centralize only law-neutral finite/nonnegative/raw-mass validation. Keep QT Kraus/measurement and MCWF
   jump residual policies in their respective Adapters.
2. Remove undeclared positive-probability pruning. Exact structural zero, underflow/nonrepresentability,
   and an invalid negative/nonfinite value remain distinct outcomes.
3. Apply the `expm1` and endpoint correction in the same phase as removal of the masking cutoff.
4. Validate integer and real controls before narrowing; reject bool and numeric strings where not part of
   the declared Interface.
5. Resolve QT-only `COH_*` preflight without removing MCWF support.
6. Correct exact-bond sufficiency from cut products and document the representational meaning.

Exit: all probability-mass and input-contract falsifiers pass; no common helper decides a route-specific
acceptance policy; behavior and provenance changes are enumerated.

### Phase 5 — consolidate already-correct Carrier mechanics

Scope: ownership consolidation plus the implementation part of `MPS-017`.

1. Move the authenticated Quimb state/split mechanics into the README-owned `carrier/mps/` Module without
   changing their now-green semantics.
2. Move raw truncation event validation and law-neutral aggregation primitives only after both Adapters'
   occurrence falsifiers are green.
3. Delete MCWF imports of private QT symbols. Do not replace them with route-mode flags.
4. Delete the old private implementations in the same phase; add no aliases or forwarding shims.
5. Retain QT and MCWF substep loops, occurrence definitions, RNG order, support policy, and manifests in
   their respective Adapters.
6. Add the following explicit disclaimer, with equivalent unambiguous wording, to
   `carrier/mps/README.md`, `docs/ARCHITECTURE.md`, and `docs/SIMULATOR.md`:

   > `carrier/mps` is an execution-mechanics library for restricted verification routes. It makes no
   > state-, Record-, or LER-faithfulness claim and is not a registered scientific Carrier. PEPS
   > remains the trajectory-carrier frontier, and PEPO remains the retained research Carrier.

   A documentation assertion must require all three declarations, and `docs/service_status.json` must
   not register `carrier/mps` as a third scientific Carrier merely because the implementation receives
   a dedicated directory.

Exit: dependency-direction checks pass; no cross-route private imports remain; no defect-ID or route-mode
switch exists; public behavior is verified at the Adapter Interfaces; all three non-scientific-carrier
declarations are present and the service registry introduces no third scientific Carrier.

### Phase 6 — certification ownership and public Interface cleanup

Scope: certification movement and the remaining `MPS-017` items.

1. Make `certify/` consume immutable raw evidence and own dense references, scientific metrics, and final
   restricted acceptance.
2. Reconcile the two contract-only Modules with the fact that executable routes now exist. Keep a public
   entry only when it still has a current contract role; otherwise perform a documented hard cut with no
   compatibility reader.
3. Keep route-specific schema families, but bump versions for changed fields or semantics.
4. Remove dead builders and stale wording; document kept dimension versus numerical rank and evaluator-only
   multilevel diagnostics.
5. Re-run public-entry scans, coverage/mutation registries, package build, generated map checks, and the
   current fresh-process acceptance plan.

Exit: execution does not self-certify; every remaining public Interface has a current owner and falsifier;
no stale “backend not implemented” claim remains.

### Phase 7 — sampled scalability after correctness

Scope: the algorithmic half of `MPS-014`; no scientific claim upgrade.

1. Replace QT joint outcome-table materialization with a distribution-equivalent conditional sampler.
2. Preserve the Phase 1 resource guard even after linearization.
3. Compare against exact bounded probabilities using the frozen standard distance/confidence rule. Do not
   require old per-trajectory bit equality when RNG draw order changes.
4. Treat MCWF environment-cache optimization, batching, canonical-center control, and a future native MPS
   implementation as separate benchmark-driven proposals.

Exit: bounded distributions agree within the preregistered statistical band; large declared workloads
either run within the resource contract or fail closed; no performance result is promoted to Record
faithfulness.

## 6. Per-phase review and verification contract

For every `src/**` phase:

1. Show the RED falsifier and independent expected result before the implementation diff.
2. Obtain explicit user confirmation for the scoped source files.
3. Apply the smallest vertical change; unrelated cleanup waits.
4. Show the complete phase diff and behavior-change table.
5. Run focused tests, the affected coverage/mutation registry, package/build checks, and the current
   fresh-process acceptance plan in the required isolated topology.
6. Record exact source hash, environment/lock identity, commands, outputs, and remaining RED scientific
   claims.

A phase is not accepted merely because aggregate pytest, coverage, mutation percentage, state fidelity,
or count normalization is green. The phase-specific independent falsifier and Interface contract must be
green.

## 7. Explicit non-goals

This plan does not:

- implement or choose a production pruning threshold;
- turn local discarded weight into a global state-distance, Record-TV, or LER bound;
- establish d5/d7 Record faithfulness;
- add `.b8`, `.dem`, decoder, or Axis-2 integration to the restricted MPS routes;
- upgrade first-order MCWF or the current Strang label into a general finite-step theorem;
- cap Kraus/no-jump/jump operators before their raw norm is read as physical branch mass;
- add multilevel finite-bond support without a separate design and independent reference;
- rewrite SVD, canonicalization, or tensor algebra from raw Torch;
- change PEPS/FET implementation or scientific gates;
- add singular-value spectra or other optional payload features during repair.

The future production-pruning program remains gated by an independent bridge from local truncation events
to the complete adaptive multi-round Record law.

## 8. Next authorized action

Phase 0 evidence work remains incomplete until the package-wide cutoff scanner and the full `MPS-016`
three-leg gate are committed. Separately, the user confirmed the Phase 1B source scope on 2026-07-17;
implementation may proceed only in the following five files while that slice is active:

- `src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py`;
- `src/error_coupling_simulator/frontend/axis1_mcwf_dense_certification.py`;
- `src/error_coupling_simulator/frontend/axis1_carrier_execution.py`;
- `src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py`, limited to blocked-policy schema
  synchronization and no algorithm change; and
- `src/error_coupling_simulator/frontend/README.md`.

Every later phase and any expansion beyond these files still requires a new file-scoped confirmation.

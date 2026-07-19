# Restricted MPS Phase 3 — Record layout and reset policy — GREEN — 2026-07-17

> Historical phase snapshot. Schema identities, owner paths, registry counts, and remaining-work
> statements below describe this phase at review time; current identities and phase status live in
> `docs/SIMULATOR.md`, the frontend owning README, and the consolidation plan.

## Disposition

Disposition: **MPS-004, MPS-005, MPS-012, and MPS-013 are GREEN inside the restricted
execution contract**.

This phase repairs Record-schema discovery and reset/control-flow defects. It does not register MPS
as a scientific Carrier, make the restricted manifests canonical Record output, or establish
finite-truncation Record/LER faithfulness.

## Reproduced RED behavior

The Phase-3 GPU falsifier file was written before the production repair. Its first run reported
**6 failed in 0.75 s**:

1. **MPS-004:** QT sampled execution registered only the first measurement boundary, appended later
   outcome bits, and failed while resolving the `round1` Record key.
2. **MPS-005, merged double MR:** the observed MCWF level Record remained `(1, 1, 1, 1)` instead of
   the hand-written `(1, 1, 0, 0)` point mass.
3. **MPS-005, mixed reset mask:** the observed Record again remained `(1, 1, 1, 1)` instead of
   `(1, 1, 0, 1)`.
4. **MPS-012:** a QT sampled reset row was mislabeled as product-formula evolution and lacked its
   sampled boundary policy.
5. **MPS-013, reset plus dynamics:** MCWF support preflight returned no blocker, so the reset branch
   silently omitted declared evolution.
6. **MPS-013, dynamics without duration:** MCWF support preflight returned no blocker, leaving a
   downstream unstructured `float(None)` failure.

The old dense level comparison was not an independent defense for MPS-005: it shared the same
all-or-nothing reset interpretation, so Carrier and comparator could agree on the wrong Record.

## Repair

`frontend/axis1_record_layout.py` is the sole schedule-derived Record-layout owner for the two
restricted MPS Adapters. It calls `require_compiler_schedule_seal(...)` and parses the schedule once
before CUDA acquisition or trajectory execution. Its tuple-only frozen objects contain:

- every measurement boundary and operation;
- ordered keys, targets, bases, and per-target reset flags;
- boundary-global slices; and
- detector and logical-observable XOR columns resolved against globally unique keys.

It rejects key/target width drift, empty or duplicate keys, repeated/out-of-range targets, empty
measurement substeps, malformed `record_layout_ref` fields, unknown XOR keys, and sealed-reference
drift. `materialize_binary_records(...)` and `project_axis1_xor_records(...)` then enforce exact
binary Record width and use only the precomputed columns.

QT exact and sampled routes consume the same immutable layout. Sampled trajectories fill outcomes
for every temporal boundary and cannot register schema. QT sampled reset rows now declare
`finite_step_policy="boundary_only_no_generator_evolution"` and
`reset_boundary_policy="sampled_pauli_reset_internal_outcome_no_record"` without product-formula
fields.

MCWF consumes the same public schedule facts but retains route-specific state evolution. Grouped
measurement substeps apply reset by target and basis according to the immutable mask. The dense
level comparator independently reconstructs operation records and per-target reset branches; it
does not import the MCWF reset helper. Preflight now reports:

- `mcwf_mps_reset_substep_contains_evolution_terms` for reset plus evolution; and
- `mcwf_mps_evolution_terms_require_positive_dt_ns` for evolution with missing, nonfinite, or
  nonpositive duration.

## Intentional behavior and schema changes

| Surface | Previous behavior | Current behavior |
|---|---|---|
| QT sampled multi-boundary Record | schema came from the first sampled boundary; later bits could disagree | all boundaries come from one sealed immutable layout; each outcome width is checked |
| QT sampled reset metadata | reset could be labeled product-formula evolution | sampled boundary-only reset policy, no dynamics fields |
| MCWF grouped MR | multiple operation records could skip reset entirely | reset is applied per declared target and operation mask |
| Dense level comparator | shared the all-or-nothing reset defect | independently reconstructs each operation and reset branch |
| MCWF reset plus evolution | reset ran and silently omitted dynamics | structured unsupported-substep diagnostic |
| MCWF evolution without positive `dt_ns` | unstructured runtime failure was reachable | structured unsupported-substep diagnostic before execution |
| Direct QT/MCWF manifest identity | execution schemas v2 | execution schemas v3; no v2 fallback |

The shared layout schema is
`error_coupling_simulator.frontend.axis1_schedule_record_layout.v1`. Sweep, bundle, resource, and
acceptance-policy schemas were not upgraded merely because their direct-execution child changed.

## Independent and regression evidence

The Phase-3 tests report **21 passed**:

- `tests/test_axis1_record_layout.py` supplies CPU-only hand-written Record-domain/XOR expectations,
  immutable-schema and corruption checks, and a static ban on late key/target registration; and
- `tests/test_mps_phase3_record_layout.py` supplies the two-boundary QT Record law, two MCWF
  per-target reset masks, reset metadata, both structured blockers, and an exactly-once parser gate
  for each Adapter.

The broader focused restricted-MPS group reports **460 passed, 1 skipped**. The complete Axis-1
schedule suite reports **179 passed, 1 skipped, 27 warnings**. The MCWF backend/convergence/Grover
group reports **27 passed** and retains the expected first-order and Strang refinement behavior.

The strict coverage registry reconciles all 21 declared public units with no missing or stray unit
and no exemption error. All six newly registered layout units are at 100% statement and branch
coverage. The overall registry is deliberately still RED:

```text
COVERAGE-AUDIT: FAIL
units=21, under_target=9, missing_canonical=0, stray_registered=0, exemption_errors=0
```

Those nine under-target units are retained debt; targets were not lowered and no exemption was
added to manufacture a GREEN release gate.

## Isolated external baselines

The external replays were run through the committed neutral adapters, not by importing external
source into the `ecs` process.

YASTN command:

```bash
conda run -n ecs-baseline-yastn python \
  scripts/external_baselines/run_yastn_mcwf_mass_comparison.py \
  --output /tmp/phase3_yastn_mcwf_mass_report.json
```

The report passes, binds environment `ecs-baseline-yastn` to pristine clone commit
`595bd802ba0753a187b4bf7fd5c6d5007c0170d0`, obtains candidate mass
`6.000244140625`, and detects the wrong-jump corruption. Its exact output-file SHA-256 is
`b6f17d3134eab7fdced7b1e981aef0721aa02456266979a902d6a81a7c00aa9f`.

Aer command:

```bash
conda run -n ecs python \
  scripts/external_baselines/run_aer_mps_comparison.py \
  --output /tmp/phase3_aer_mps_report.json \
  --scratch-root /tmp/phase3_aer_mps_workers \
  --timeout-seconds 120
```

The orchestrator launches 15 separate `ecs-baseline-aer` worker processes. All checks and both gate
corruption falsifiers pass. The pristine source reference is commit
`837c3ef3c39248aae936580360c22224dcefb265`; the adapter does not claim that the installed Aer wheel
was built from that clone. The exact output-file SHA-256 is
`6d8143ba96a0a0607556a314db7185cfa0e413eb29ccaea801bf14758d353440`.

Aer checks unitary-MPS state/truncation behavior and YASTN checks product-MPS candidate mass. Neither
is a QEC trajectory-law, schedule-layout, reset-policy, or complete Record oracle. The Phase-3
load-bearing expectations are therefore hand-written schedule/Record and reset point masses.

## Bound source and falsifier hashes

```text
5815ea5839cbd41a12e2d213603d8b0cf7892974a62d9e68fad257f227753e6b  frontend/axis1_record_layout.py
faa3350778ed1b7eba2a30ee7ea75983a4f8734b883f3ba3d41110d1173c79b1  frontend/axis1_qt_mps_execution.py
ff5f3e4cf72cd20120438a764ad7521bf149a293837b3ecda975f63d2bb8f30c  frontend/axis1_mcwf_mps_execution.py
622412a85e77cac4290cbf442721a7524c2fb8984db739548a48965e61fde895  frontend/axis1_mcwf_dense_certification.py
e989d09be4d8fc75153256be5c786846dee1b163c083b6de5b75da437482f423  tests/test_axis1_record_layout.py
d5a6c4877f7408a4ee11fa2f72efe28eaf8412d0187e1a224721409a94b77182  tests/test_mps_phase3_record_layout.py
```

## Remaining work

Phase 4 remains RED and covers `MPS-006` through `MPS-011`: probability-mass semantics,
finite/nonnegative and integer-control validation, QT-only route support, and exact-bond
sufficiency. Performance and memory optimization remain deferred until those correctness contracts
and the later consolidation phases are green; any optimization must replay the independent and
external baselines before acceptance.

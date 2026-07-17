# Restricted MPS Phase 1B RED firewall — 2026-07-17

## Status

This is a test-only, deliberately RED checkpoint for `MPS-003` and the fail-closed guard half of
`MPS-014`. Production `src/**` is unchanged. The starting repository checkpoint is
`103c465655b37e797e709cd97f9d97f6f294bf59`.

The CPU-only command

```bash
conda run -n ecs python -m pytest -q tests/test_mps_phase1b_fail_closed.py --tb=short
```

reported `103 failed, 11 passed` after independent review of the test contract. The passing cases
freeze already-correct negative-value rejection and inclusive numerical gate boundaries. The
failures are intentional counterexamples and must not be skipped or excluded.

## Confirmed false-green classes

- QT and MCWF acceptance can admit malformed normalization evidence, including negative values,
  `-Inf`, and boolean values.
- Verdict-driving dense-certification and seed-evidence fields are truth-value coerced instead of
  requiring exact booleans and declared integer seeds.
- Mandatory truncation-ledger fields default to passing values; malformed discarded weights can be
  ignored when no optional threshold is declared.
- Nonfinite or nonpositive free-VRAM probes can select dense execution or lack an explicit invalid
  resource reason.
- Convergence, seed-spread, dense-frequency, and CUDA-memory gates accept bool or nonfinite values,
  or validate them only after delegated execution/CUDA has begun.
- QT exact and sampled paths have no declared Record-materialization budget. A six-bit fixture can
  reach CUDA and later construct `2**6` outcomes before any such resource gate exists.
- The carrier wrapper and CUDA resource probe allow the same budget check to be bypassed because
  they touch CUDA before validating the delegated workload.

The no-allocation falsifiers replace CUDA acquisition, Record enumeration, exact execution, and
sampled MPS execution with must-not-run sentinels. Budget `63` must reject a six-bit Record domain
before all sentinels; budgets `64` and `65` must pass preflight and reach only the CUDA sentinel.
A second fixture splits those six bits across two three-bit boundaries so an implementation that
checks only the largest individual boundary cannot pass.

## External-comparator boundary

The retained external execution and provenance audit is in
[`MPS_PHASE1A_FALSE_GREEN_FIREWALL_2026-07-17.md`](MPS_PHASE1A_FALSE_GREEN_FIREWALL_2026-07-17.md).
Aer is an independently installed entangling/cap comparator, YASTN is an independently installed
product-MPS candidate-mass comparator, and Quimb high-level execution is a same-backend wiring
comparator. None of them is an oracle for malformed acceptance evidence or pre-allocation resource
ordering, so this phase requires corruption falsifiers rather than a fabricated external verdict.

## Proposed reviewed source slice

No source edit is authorized by this document. The smallest complete Phase 1B source review is:

1. `src/error_coupling_simulator/frontend/axis1_qt_mps_execution.py` — strict shared truncation
   evidence, QT acceptance gates, and a CPU Record-materialization preflight propagated through all
   QT sweep/bundle/probe surfaces before CUDA.
2. `src/error_coupling_simulator/frontend/axis1_mcwf_dense_certification.py` — strict MCWF
   normalization, verdict, and seed evidence at the restricted acceptance seam.
3. `src/error_coupling_simulator/frontend/axis1_carrier_execution.py` — fail-closed free-VRAM
   routing, QT budget allowlisting, and removal of the carrier's pre-validation CUDA touch.
4. `src/error_coupling_simulator/frontend/axis1_mcwf_mps_execution.py` — synchronize only the
   blocked acceptance-policy schema with the active policy; no execution-algorithm change.
5. `src/error_coupling_simulator/frontend/README.md` — the changed Interface, state-machine,
   resource-budget, and schema semantics.

Accompanying changes may update the dedicated test, test registry, service catalog, generated code
map, and this report. General route-control narrowing, probability primitives, Record-layout repair,
and performance work remain in their later planned phases.

## Required post-fix evidence

- The complete Phase 1B test file turns green without weakening any counterexample.
- Existing equality boundaries remain inclusive and next-float-above cases fail.
- Budget `63` causes zero CUDA, Record-enumeration, and MPS-execution calls in direct, carrier, and
  resource-probe paths.
- Focused QT/MCWF/carrier suites and the registered coverage gate are rerun.
- Aer and YASTN remain byte-reproducible in their isolated environments; Quimb remains labeled
  same-backend wiring-only.
- Performance optimization does not begin until this correctness slice and its independent
  comparators are green.

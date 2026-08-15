# Restricted MPS Phase 1B false-green firewall — GREEN — 2026-07-17

## Status

Disposition: **GREEN for the Phase 1 fail-closed state/schema/evidence firewall; later MPS repair
phases remain open**. The working tree is based on `HEAD f0d52b3`; this packet does not claim a new
commit. PEPS/PEPO scientific implementations are outside this diff.

The reviewed behavior now enforces one rule at every direct and Carrier boundary: backend completion
is not certification. `pass` is equivalent to restricted acceptance, unsupported or malformed
states fail before promotion, and production-scalable acceptance remains false.

## Closed false-green classes

- MCWF numerical budgets, runtime observations, count/probability bindings, metric identities,
  provenance, and JSON hashes reject missing, nonfinite, negative, boolean-as-number, or inconsistent
  values.
- Direct MCWF policy v5 is sampled-only and binds its trajectory mode to the actual execution
  payload. Missing or forged trajectory evidence cannot cross the endpoint.
- QT direct, bond-sweep, seed-sweep, bundle, and resource manifests pin their v2 schemas, state,
  evidence tier, and actual trajectory mode.
- Carrier MCWF/QT wrappers bind nested state, schema, blocker, production claim, policy mode, and
  actual child execution mode; a self-consistent forged policy no longer suffices.
- `claims_qt_mps_backend_execution` now equals `qt_mps_backend_executed`: false for blocked children,
  true for completed children, and checked again at the Carrier boundary.
- True-over-cap QT execution without an independent Record oracle, and no-measurement QT execution
  without a registered state/channel comparator, retain diagnostic evidence but end in
  `certification_status="unavailable"`, restricted acceptance false, and verdict `fail`.
- The canonical no-measurement Record is exactly one empty row with unit probability; falsy values of
  the wrong type are rejected.

## Durable gates

- `tests/test_mps_phase1b_fail_closed.py`: **343 passed**. Every new trajectory/claim binding was
  demonstrated RED before the minimal GREEN repair.
- `tests/test_mps_quimb_cutoff_static_gate.py`: the package-wide decomposition scanner requires a
  named `cutoff=` at every registered Quimb split/decomposition call and contains deletion
  self-falsifiers.
- `tests/test_mps_three_leg_comparator.py`: independent NumPy/SVD, repository actual-split, and Quimb
  public wiring legs reconcile on the bounded two-site fixtures; topology, norm, and ledger
  corruptions are detected. Quimb remains wiring evidence, not an independent scientific oracle.

## Verification

The final focused Phase 1/2 group reported **443 passed, 1 skipped**. The complete Axis-1 schedule
file reported **179 passed, 1 skipped**; the MCWF backend/convergence/Grover group reported
**27 passed**. `py_compile`, `git diff --check`, and the generated code-map check pass.

The isolated external comparators were rerun without `PYTHONPATH` or project imports:

- YASTN candidate-mass comparator: PASS, exact-byte SHA-256
  `b6f17d3134eab7fdced7b1e981aef0721aa02456266979a902d6a81a7c00aa9f`;
- Aer MPS comparator: 15 fresh worker processes, PASS, exact-byte SHA-256
  `6d8143ba96a0a0607556a314db7185cfa0e413eb29ccaea801bf14758d353440`.

Both artifacts are byte-identical to the earlier independent replays. The frozen Aer and YASTN
clones remain pristine. These comparators retain their declared limited roles and do not certify the
QEC Record law.

## Remaining boundary

This report does not close schedule-derived multi-boundary Record layout, MCWF reset policy,
finite-step exponential stability, remaining public input narrowing, full coverage/mutation, or
performance optimization. Those remain separate correctness-first phases in the V3 plan.

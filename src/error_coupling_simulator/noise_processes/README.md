# noise_processes

## Ownership

This package owns controlled generative processes that bind declared source timelines to current
carrier execution.

## Boundary

Process truth and per-cycle mechanism parameters remain evaluator-only. A process emits the declared
record product and controls; it does not expose hidden labels to downstream estimators.

## Entry points

`CoupledCycleNoiseProcess`, the current default code specifications, round-map helpers, and explicit
matched-marginal and source-off controls are exported from `coupled_cycle.py`.

## Acceptance

See `tests/test_coupled_cycle_noise_process_records.py`, `tests/test_coupled_cycle_units.py`, and
`tests/test_coupled_cycle_interop.py`. The complete owner map is `docs/service_status.json` and
generated `docs/CODE_MAP.md`.

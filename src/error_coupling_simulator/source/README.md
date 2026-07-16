# source

## Ownership

This package owns replayable classical source timelines and the explicit map from a source draw to
same-cycle specified-process parameters.

## Boundary

Source arrays and latent state are evaluator-side truth. A timeline alone is not a quantum-memory
claim and does not become a record service until an explicit current process consumes it.

## Entry points

Current entry points are `SourceTimeline`, `RTNSource`, `OneOverFDriftSource`, `PhaseBurstSource`,
`TemporalStormSPPSource`, and `source_to_params`.

## Acceptance

See `tests/test_source_process.py`, `tests/test_source_process_units.py`,
`tests/test_source_coupling_units.py`, and `tests/test_finite_rtn_free_induction_diagnostic.py`.
The complete owner map is `docs/service_status.json` and generated `docs/CODE_MAP.md`.

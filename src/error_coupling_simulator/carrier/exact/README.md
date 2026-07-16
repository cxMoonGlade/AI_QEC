# carrier/exact

## Ownership

This package owns bounded exact density-matrix state evolution and measurement enumeration for
qubit, qutrit, and ququart implementation references.

## Boundary

These are small-register exact oracles and feasibility carriers. They do not establish hardware
truth or production-scale record faithfulness.

## Entry points

`circuit_sim.py` exposes `zero_state`, `apply_channel_local`, `measure_qubit_enumerate`, and
`parity_marginal_one`. `qutrit_dm.py` exposes `QutritDM` and `QuquartDM`.

## Acceptance

See `tests/test_diff_circuit_forward.py`, `tests/test_qutrit_dm_memlean.py`,
`tests/test_qutrit_dm_measurement_semantics.py`, and `tests/test_qutrit_dm_two_site_channel.py`.
The complete owner map is `docs/service_status.json` and generated `docs/CODE_MAP.md`.

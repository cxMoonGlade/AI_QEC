# mechanisms

## Ownership

This package owns the current explicitly named physical-operation primitives used by specified
noise processes.

## Boundary

Mechanism modules construct or lower declared operations. They do not own source timelines,
records, or downstream estimators. The implementation map is
[`docs/error_mechanisms.md`](../../../docs/error_mechanisms.md); this README does not duplicate it.

## Entry points

Current entry points include `lower_two_qubit_axis1_primitives`, `build_cz_channel`, and the qutrit
leakage channel/process functions exported by `qutrit_leakage.py`.

## Acceptance

See `tests/test_joint_lindbladian.py`, `tests/test_cz_leakage_mechanism_units.py`, and
`tests/test_qutrit_leakage_units.py`. The complete owner map is `docs/service_status.json` and
generated `docs/CODE_MAP.md`.

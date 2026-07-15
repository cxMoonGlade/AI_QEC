# Shared test support

This directory contains test-only fixtures, adversarial assertions, per-owner
coverage registries, and their self-tests. Production modules must not import it.

Reference implementations with an independence requirement stay local to the test
that uses them. Centralizing such a reference with the implementation under test
would make a shared defect capable of passing both sides of a comparison.

The reusable helpers are:

- `require_precondition`: fails loudly when a falsifier would be vacuous.
- `assert_control_trips`: proves a deliberately corrupted input is rejected.
- `assert_with_margin`: rejects threshold checks that pass only at numerical noise.
- `random_cptp_kraus` and `random_density_matrix`: validated random fixtures.
- `load_outputs_module`: loads a committed current-run script for a focused test.

Each `stage_d_*_targets.json` file is a current-owner unit/branch-coverage registry
consumed by `tests/harness/gate.py`. A registry must enumerate every public unit in
its declared modules or state an explicit, test-backed reason for exclusion.

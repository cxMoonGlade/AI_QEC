# PEPO validation status

Status: **retained research carrier; implementation checks current; record faithfulness open**.

## Current owner

The two-dimensional qutrit density-matrix PEPO is owned by:

- `src/error_coupling_simulator/carrier/pepo/layout.py`
- `src/error_coupling_simulator/carrier/pepo/dynamics.py`
- `src/error_coupling_simulator/carrier/pepo/sampler.py`

It is registered as `pepo_density_matrix_carrier` with status `RESEARCH` in
`docs/service_status.json`. Its current entry points construct a PEPO codestate and evaluate a
terminal-observable probability. Selective per-stabilizer record sampling is not a current entry
point.

## Current executable evidence

The service registry binds ten current acceptance files:

- `tests/test_pepo_host_seam.py`
- `tests/test_pepo_density_layout_guards.py`
- `tests/test_pepo_density_state.py`
- `tests/test_pepo_density_token_ops.py`
- `tests/test_pepo_density_stabilizer.py`
- `tests/test_pepo_density_killers.py`
- `tests/test_pepo_density_observables.py`
- `tests/test_pepo_density_nonselective_round.py`
- `tests/test_pepo_density_ntu_precut.py`
- `tests/test_pepo_density_compressed_caps.py`

The Phase-3 cleanup gate ran all ten files in fresh processes and recorded ten passes. The
high-memory reference and PEPO processes were separated so their CUDA/native lifetimes do not
overlap. Exact-density comparisons are implementation checks for the frozen d3 cases; they do not
validate a physical device or establish scalable full-record accuracy.

## What is and is not established

Established for the registered cases:

- current package ownership and absence of a retired runtime dependency;
- d3 layout, local tensor algebra, nonselective-round, truncation, negativity, and contraction
  invariants covered by the listed tests;
- process-isolated execution under the current service harness.

Not established:

- a canonical multi-round detector/observable record backend;
- finite-truncation preservation of the full record law;
- d5/d7 distributional correctness or production scaling;
- correspondence to a hardware device.

No old output or pre-cleanup contract is current evidence. New claim-bearing PEPO evidence must be
generated from the current source and tests, bind source/test/input/environment hashes, and use the
current artifact schema.

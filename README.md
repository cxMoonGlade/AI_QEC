# error_coupling_simulator

A GPU-first specified-noise simulator for quantum error-correction circuits. It applies a declared
noise process to a circuit or schedule and produces the multi-time temporal detector/observable
record. A `.dem` is an optional decoder-facing reduction, not the simulated object.

The runtime and distribution namespace is `error_coupling_simulator`. External circuits, optional
decoder inputs, explicit derived-channel caches, and the isolated CUDA-Q adapter are declared
boundaries.

Read [`docs/SIMULATOR.md`](docs/SIMULATOR.md) first; it is the binding product and scientific
contract.

## Current surface

- Stim-representable circuit compilation and decoder-free record emission.
- Within-substep joint-Lindbladian channels on bounded dense routes.
- Replayable finite-RTN source timelines with explicit parameter mapping and matched controls.
- Restricted one-dimensional MPS verification executors.
- Qutrit leakage and explicit multi-level CZ transport channels.
- Bounded exact-density references.
- Retained density-matrix PEPO and single-wire PEPS research carriers.
- Evaluator-only formal certification and bounded quantum-bath research models.

The source-conditioned dense-qubit process and the static qutrit XZZX leakage process are separate
routes; there is no current integrated source-driven qutrit XZZX product.

PEPO is retained as a tested research carrier but is not the canonical record backend. PEPS
full-record finite-truncation faithfulness is open. Its current FET end-to-end entropy gate fails at
`0.10860941571062639` versus an independent GF(2) reference of `2.0` with tolerance `1e-4`.

## Install for development

```bash
conda env create -f environment-ecs.yml
conda run -n ecs python scripts/sync_core_environment.py
conda run -n ecs python scripts/configure_core_environment.py
conda run -n ecs python scripts/verify_core_environment.py
```

Python 3.11 or newer is required. `uv.lock` supplies the transitive repository lock and
`core-environment-cu130.lock` records the direct GPU compatibility contract. PyMatching is optional;
the default record path is decoder-free. CUDA-Q runs separately in the `aiqec` environment.

Do not set `PYTHONPATH="$PWD/src"`; use the editable install configured by the environment scripts.

## Verify

```bash
python tests/harness/service_acceptance.py
conda run -n ecs python -m pytest -q tests/
conda run -n aiqec python -m pytest -q tests/test_simulator_cudaq_grover.py
python tools/gen_code_map.py --check
```

The service gate runs each acceptance file in a fresh process across bounded CPU, serial host-heavy,
and serial GPU lanes. The parent imports no CUDA runtime, and only the GPU lane holds the
cross-process GPU lock. Repository-wide pytest is an engineering regression surface, not a
scientific certification claim.

## Documentation

- [`docs/SIMULATOR.md`](docs/SIMULATOR.md) — binding contract.
- [`CONTEXT.md`](CONTEXT.md) — glossary and claim boundary.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — architecture summary.
- [`docs/service_status.json`](docs/service_status.json) and
  [`docs/CODE_MAP.md`](docs/CODE_MAP.md) — exact service and source inventory.
- [`tests/CODEBOOK.md`](tests/CODEBOOK.md) — executable test/coverage map.
- [`docs/METRICS.md`](docs/METRICS.md),
  [`docs/FAITHFULNESS_PROTOCOL.md`](docs/FAITHFULNESS_PROTOCOL.md), and
  [`docs/NUMERICAL_PROVENANCE.md`](docs/NUMERICAL_PROVENANCE.md) — scientific disciplines.
- [`docs/simulator_validation/`](docs/simulator_validation/) — current cleanup and carrier status.

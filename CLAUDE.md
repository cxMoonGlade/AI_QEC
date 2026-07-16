# Repository guidance

Read `docs/SIMULATOR.md` first. It is the binding product and scientific contract.

## Main line

`error_coupling_simulator` is a GPU-first specified-noise simulator for QEC circuits. A caller
supplies a circuit or schedule plus a declared noise process; the product is the multi-time temporal
detector/observable record. A `.dem` is an optional decoder-facing reduction, not the simulated
object. Metrics are instruments on the record.

The only runtime package is `src/error_coupling_simulator/`. Exact installed ownership, service
status, entry points, acceptance files, and the complete flow are defined by
`docs/service_status.json` and generated into `docs/CODE_MAP.md`.

The current carrier frontier is the single-wire two-dimensional PEPS research route. The
density-matrix PEPO is also retained as a tested research carrier. Neither has established
finite-truncation full-record or d5/d7 faithfulness. The current PEPS/FET scientific gate fails at
non-degeneracy: at strict `eps_fid=1e-8`, the entropy equality passes only because all FET
cuts take the identity fallback and zero rank-reducing write-backs occur. Do not weaken the target or
hide this all-noop RED.

The classical finite-RTN source process and the static qutrit XZZX leakage process are separate
implemented routes. Do not describe an integrated source-driven qutrit XZZX record product as
current.

## Commands

```bash
conda env create -f environment-ecs.yml
conda run -n ecs python scripts/sync_core_environment.py
conda run -n ecs python scripts/configure_core_environment.py
conda run -n ecs python scripts/verify_core_environment.py

python tests/harness/service_acceptance.py
conda run -n ecs python -m pytest -q tests/
conda run -n ecs python -m pytest -q tests/test_name.py::test_name
conda run -n aiqec python -m pytest -q tests/test_simulator_cudaq_grover.py

python tests/harness/gate.py tests/_support/<batch>_targets.json
python tests/harness/mutation.py tests/_support/<batch>_targets.json
python tools/gen_code_map.py --check

python tools/literature_rag.py audit
python tools/literature_rag.py query "<mechanism or observable>" --top-k 12
python tools/literature_kg.py stats
python tools/literature_kg.py concept "<concept>"
```

`environment-ecs.yml` is the Conda bootstrap, `uv.lock` is the transitive repository lock, and
`core-environment-cu130.lock` is the direct compatibility ledger. Use the sync wrapper rather than a
bare `uv sync`; the wrapper explicitly targets the Conda environment. Do not set
`PYTHONPATH="$PWD/src"`.

CUDA-Q is intentionally outside the canonical `ecs` process and runs in the retained `aiqec`
environment. PyMatching is optional; the default record path is decoder-free.

The literature tools build from live `error_coupling_simulator.literature.note.v1` records. RAG
returns only `paper_fact`; KG relationships require exact source locators and zero dangling
endpoints. Neither tool reads quarantined vector/graph caches. Retrieval is discovery only; reopen
the primary source before using a load-bearing claim.

## Acceptance execution

The service supervisor runs one acceptance file per fresh exec process. The parent imports no
Torch/CUDA runtime. Resource lanes are:

- bounded `cpu_light`, capped by configured jobs and `MemAvailable`;
- serial `cpu_exclusive` for host-memory/BLAS-heavy work;
- serial `gpu_serial`, with the cross-process GPU lock held only for this phase.

Each child exit releases its native/CUDA lifetime. Process-group cleanup is verified before a result
can pass. Plans are immutable, result aggregation has one writer, and summaries are atomic. Do not
replace this topology with one long-lived pytest process: it is not an equivalent native-lifetime
gate.

`pytest tests/` is an engineering regression surface, not a scientific certification claim.
Scientific acceptance is subsystem-owned and listed in `tests/CODEBOOK.md` and the service catalog.

## Architecture

```text
src/error_coupling_simulator/
  source/           replayable finite-RTN timelines and explicit source-to-parameter mapping
  mechanisms/       local Axis-1 primitives, qutrit leakage, and explicit CZ transport
  noise_processes/  controlled generative record processes
  carrier/
    exact/           bounded density-matrix references
    kernels/         scoped native CUDA acceleration
    pepo/            retained density-matrix PEPO research carrier
    peps/            single-wire PEPS research frontier
    records.py       common record objects and packed layout
    record_fold.py   raw-syndrome to temporal-detector conversion
  frontend/         circuit IR, compiler, schedules, bounded executors, artifact emission
  certify/          evaluator-only reference-oracle scoring
  quantum_bath/     feasibility-only research models
  numerics.py       shared float64 representability and comparison policy
```

Read the owning module README before changing a module. Do not add flat modules at the package root.

## Code and scientific rules

- Validate original values before narrowing dtypes. Copy externally owned arrays when required and
  make immutable record payloads read-only.
- Preserve structural zeros. `NUMERICAL_ZERO == 1e-12` is for floating thresholds only; the
  shared scaled-arithmetic helpers reject nonrepresentable nonzero results instead of manufacturing
  structural endpoints.
- A PTM off-diagonal entry means basis-specific non-Pauli structure; it does not identify a coherent
  cause without another argument.
- Qutrit leakage channels, codestates, channel composition, and CPTP checks are complex128. PEPO,
  PEPS, and the restricted MPS routes are complex128-only. Only the fused within-cycle sampler may use
  complex64, and only for optimization labeled `screening_only`.
- Evaluator-only source trajectories, channel fields, and mechanism parameters never enter the
  emitted record or downstream estimator input.
- Every claim-bearing value follows `docs/NUMERICAL_PROVENANCE.md`; every score follows
  `docs/METRICS.md`; every faithfulness claim follows `docs/FAITHFULNESS_PROTOCOL.md`.
- Every retained scientific claim needs a physical name, formula, implementation owner, current
  falsifier, and exact primary-source or complete-derivation locator. A missing item is a gap.
- External baseline repositories are pristine. Adaptors live in this repository, not in vendored
  upstream code.
- Every `src/**` change requires explicit user confirmation and a reviewed phase diff.
- Every nontrivial execution is a committed script with preconditions, printed evidence, flushed
  output, and a `__main__` guard when multiprocessing is involved. Inline shell is for trivial
  read-only inspection only.

Current artifact schemas use `error_coupling_simulator.<owner>.<artifact>.vN` and reject unsupported
versions without fallback.

## Runtime and test-surface environment

The package and direct test surface use `ECS_DISABLE_NATIVE_KERNELS`,
`ECS_FORCE_UNFACTORIZED_AXIS1`, `ECS_D3_DATA_ROOT`, and test-only `ECS_D3_MASK`.

## Harness-only environment

Fresh-process acceptance and mutation orchestration use `ECS_GPU_SLOT`,
`ECS_MUTATION_SKIP_SLOW`, `ECS_ACCEPTANCE_CPU_JOBS`, `ECS_ACCEPTANCE_TIMEOUT`,
`ECS_MUT_TIMEOUT_CONST`, `ECS_MUT_TIMEOUT_MULT`, `ECS_GPUS`, and `ECS_MUT_BAR`. These keys configure
the harness; they are not simulator runtime inputs.

## Current authority

- `docs/SIMULATOR.md` — binding product and scientific boundary.
- `CONTEXT.md` — glossary and claim classes.
- `docs/ARCHITECTURE.md` — module and flow summary.
- `docs/service_status.json` + `docs/CODE_MAP.md` — exact current inventory.
- `tests/CODEBOOK.md` — executable acceptance/coverage map.
- `docs/METRICS.md`, `docs/FAITHFULNESS_PROTOCOL.md`, `docs/NUMERICAL_PROVENANCE.md` — scientific
  disciplines.
- `docs/simulator_validation/` — current cleanup and retained-carrier evidence/status.

The pre-cleanup formula ledger, old project narratives, old outputs, and current local retrieval
caches are not scientific authority. Until the literature reset closes, return load-bearing claims
to primary papers and exact equation/figure/table locators.

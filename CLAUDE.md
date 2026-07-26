# Repository guidance

Read `docs/SIMULATOR.md` first. It is the binding product and scientific contract.

## Main line

`error_coupling_simulator` is a GPU-first specified-noise simulator for QEC circuits. A caller
supplies a circuit or schedule plus a declared noise process; the product is the multi-time temporal
detector/observable record. A `.dem` is an optional decoder-facing reduction, not the simulated
object. Metrics are instruments on the record.

The only runtime package is `src/error_coupling_simulator/`. Exact installed ownership, service
status, entry points, acceptance files, and the complete flow are defined by
`docs/service_status.json` and generated into `docs/CODE_MAP.md`. Read the owning module README
before changing a module, and do not add flat modules at the package root.

**This file holds only what always binds.** What is true *right now* — the current stage, what to
read first, what is in flight, what has been superseded — lives in `docs/READING_ORDER.md`. Read it
at the start of a session; it is short by design.

## Current authority

Answer the question with the surface that owns it. Grepping `src/` to find out what exists, or
inferring from module structure what is claimed, is the slow path and it has produced wrong answers.

| question | read this first |
|---|---|
| what may be claimed at all; the product boundary | `docs/SIMULATOR.md` (wins every conflict), `CONTEXT.md` for the glossary and claim classes |
| what a service claims, and what it explicitly does **not** | `docs/service_status.json` — the per-service `note` and the `excluded_surfaces` dispositions |
| what modules and services exist, who owns what, the flow | `docs/CODE_MAP.md`, `docs/ARCHITECTURE.md` |
| what is executable acceptance versus regression | `tests/CODEBOOK.md` |
| whether a number may be claim-bearing | `docs/METRICS.md`, `docs/FAITHFULNESS_PROTOCOL.md`, `docs/NUMERICAL_PROVENANCE.md` |
| what the literature says | `tools/literature_rag.py query`, `tools/literature_kg.py concept` — then `audit` before treating the answer as coverage |
| what matters at the current stage; what is in flight | `docs/READING_ORDER.md` |

`service_status.json` is the claim boundary, and a service `note` usually answers a scope question
outright: the `restricted_axis1_1d_mps` note states in its first sentence that `carrier/mps` "makes
no state-, Record-, or LER-faithfulness claim and is not a registered scientific Carrier". Read it
before writing any scope, status, or completion sentence.

Keep these honest rather than assuming they are: `python tools/gen_code_map.py --check` and
`python scripts/rebuild_current_corpus_manifest.py --check`.

The pre-cleanup formula ledger, old project narratives, old outputs, and current local retrieval
caches are not scientific authority. Until the literature reset closes, return load-bearing claims
to primary papers and exact equation/figure/table locators.

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
python tests/harness/mutation.py tests/_support/restricted_mps_mutation_suite.json
python tools/gen_code_map.py --check

python scripts/external_baselines/build_itensor_baseline_environment.py
python scripts/external_baselines/build_mps_baseline_environment_locks.py
ECS_RUN_ITENSOR_MPS_COMPARISON=1 conda run -n ecs python -m pytest -q tests/test_external_itensor_mps_comparison.py

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
endpoints. Neither tool reads quarantined vector/graph caches.

**Local absence is not a gap.** The admitted corpus is a small, topically skewed subset of the
notes on disk, so a "nobody has done this" conclusion drawn from local retrieval describes this
corpus, not the field. Before any gap or novelty claim: search externally with `anysearch`, fetch
the primary source into `docs/papers/` with `deep-read-paper`'s `fetch_and_extract.py` (run it
under `ecs`; the system Python has no pypdf), and write the reading note. Snippets and abstracts
never settle a row, and a repository is only evidence of prior art if it was searched for, not if
it happened to be cloned. This rule is written because a local-only survey once concluded "no
external precedent" for an effect published in arXiv:2002.07119 and demonstrated on d3 Surface-17.

`docs/papers/CURRENT_CORPUS.toml` is what `query` and the KG actually read, so an audited-valid note
missing from it answers nothing. Keep the two equal with
`python scripts/rebuild_current_corpus_manifest.py` (`--check` reports drift without writing).

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
  A locator must **resolve in the named artifact**: open it and check the section exists, that the
  source uses the term you attribute to it, and that it says what you cite it for. Nothing in the
  test surface checks this, and a `src/` docstring once cited "McEwen 2102.06131 §3.2/§3.4" for a
  "DD echo" in a paper that is numbered I–V, never uses the word echo, and describes X gates for
  relaxation depolarization rather than leakage.
- External baseline repositories are pristine. Adaptors live in this repository, not in vendored
  upstream code. Each isolated baseline environment has a committed root lock
  (`baseline-environment-{aer,yastn,qutip,itensor}-linux-64.lock.json`); rebuild and leg
  instructions are in `docs/external_baselines/BASELINE_ENVIRONMENTS.md`. Bind a source
  install by `git+file://<clone>@<commit>`, never a bare directory path, which records
  `dir_info` and binds nothing. Check clone cleanliness with
  `git status --porcelain --untracked-files=all --ignored`: a directory install writes
  gitignored build artefacts that the ordinary status hides.
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

## Agent skills

Installed under `.claude/skills/`, which `.gitignore` excludes via `.*/`. They do not travel with a
clone and no lock records them, so this section is their only durable record. The ordering binds
whether or not the files are present.

`theory-first` runs **before** any new mechanism, observable, metric, forward model, prediction, or
experiment; only a closed evidence packet plus a passing preregistration permits code. `theory-fix`
runs **during or after** results, before a result becomes a premise for a definition, design, or a
new run. `project-engine-ecs` routes work here: engineering repairs direct, `theory-first` first for
new scientific mechanism or fixture code, evaluator truth isolated, semantic mutation last.

Composed by those and callable alone: `zoom-out`, `close-literature`, `anysearch`,
`deep-read-paper`, `preregister-claim`, `stress-test-claim`. Engineering: `tdd`, `diagnose`,
`codebase-cleanup`, `improve-codebase-architecture`, `neat-freak`, `collaborative-workspace`,
`grill-me`, `grill-with-docs`, `to-prd`, `to-issues`, `caveman`. `contract-build/` and
`theory-first-workspace/` hold no skill file.

### Issue tracker

Issues and PRDs live as local Markdown under `.scratch/<feature-slug>/`. See
`docs/agents/issue-tracker.md`.

### Triage labels

The tracker uses the five default workflow states. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository rooted at `CONTEXT.md`. See `docs/agents/domain.md`.

# Agent notes

`docs/SIMULATOR.md` is the binding product and scientific contract. Read it first. `CLAUDE.md` is
the current repository workflow and command guide.

## Routing

- `CONTEXT.md` — glossary and claim boundaries.
- `docs/CAPABILITY_MODEL.md` — backend capability, support, Record-layout, shot-memory, and numerical
  guarantee contract.
- `docs/ARCHITECTURE.md` — human-readable package and flow map.
- `docs/service_status.json` — exact machine-readable services, owners, entry points, and acceptance.
- `docs/CODE_MAP.md` — generated complete source/service inventory.
- owning `src/error_coupling_simulator/**/README.md` — module-local contract.
- `tests/CODEBOOK.md` — current test, coverage, and mutation map.
- `docs/METRICS.md` — metric definitions and epistemic classes.
- `docs/FAITHFULNESS_PROTOCOL.md` — assurance claims, independent-reference, and falsifier
  requirements.
- `docs/NUMERICAL_PROVENANCE.md` — value-level evidence rules.
- `docs/papers/README.md` + `docs/papers/CONCEPT_INDEX.md` — source-cache boundary and generated
  source-located discovery index.
- `docs/simulator_validation/` — current cleanup and retained-carrier status.

Do not treat the pre-cleanup formula ledger, old output verdicts, old project documents, or current
literature retrieval caches as authority. Until the literature reset closes, inspect primary papers
directly and record exact equation/figure/table locators. Project inference belongs in a separate
claim or audit packet.

Local literature discovery uses `python tools/literature_rag.py query "<query>"` and
`python tools/literature_kg.py concept "<concept>"`. These tools accept only current-schema
`paper_fact` records. A hit routes the reader back to a source and exact locator; it is not evidence
by itself.

## Operating rules

- Read the owning module README before adding code; do not add flat modules at the package root.
- Any `src/**` change needs explicit user confirmation and a reviewed phase diff.
- Preserve structural zeros; floating numerical thresholds use the shared numerical constant.
- Never expose evaluator-only process truth to emitted records or downstream estimators.
- Keep external baseline repositories pristine; adaptors belong in this repository.
- Use the fresh-process service supervisor for aggregate acceptance. Do not merge native/GPU service
  files into one long-lived process.
- Do not set `PYTHONPATH`; the editable install and pytest configuration already expose the package.
- Current environment variables are `ECS_DISABLE_NATIVE_KERNELS`,
  `ECS_FORCE_UNFACTORIZED_AXIS1`, `ECS_D3_DATA_ROOT`, and test-only `ECS_D3_MASK`.

## CUDA visibility

Wrappers can occasionally make CUDA/NVML appear unavailable even when the device is healthy. Verify
in process before diagnosing a GPU failure. For low-utilization workloads, distinguish kernel time
from host preprocessing, data loading, and circuit parsing.

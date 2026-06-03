# Agent Notes

Use `CONTEXT.md` first for glossary and claim boundaries, then route to the
stage-specific docs:

- `docs/SCOPE_STATIC_MVP.md`: Stage 1 known-orbit DEM fault-logit MVP.
- `docs/SCOPE_STATIC_DISC.md`: Stage 2 static discovery plan.
- `docs/ARCHITECTURE.md`: current code architecture and module map.
- `docs/RUNBOOK.md`: install, test, GPU, and experiment commands.
- `docs/STAGE2_ROADMAP.md`: closed Stage 2 validation record.
- `docs/STAGE3_ROADMAP.md`: active Stage 3 mechanism-structure discovery plan.
- `docs/STAGE4_ROADMAP.md`: S4 bridge-survival, neural pretrain, and
  frozen-transfer gates.
- `docs/STAGE5_ROADMAP.md`: S5 context-relative mechanism-effect audits.
- `docs/error_mechanisms.md`: physical-error mechanism taxonomy and adoption map.
- `docs/SCOPE_TWIN.md`: full SCOPE-Twin notation and future object contract.
- `docs/adr/`: durable architecture and milestone-gating decisions.

## Current Scope

The implemented package is `scope_static`. It is a fixed-context DEM/Bernoulli
research stack, not a CPTP/GKSL physical-channel learner.

Stage 1 DEM/Bernoulli implementation modules live under `scope_static.dem`.
Google Set1 adapters live under `scope_static.google`. The root package should
stay a narrow public re-export surface plus shared utilities such as
`scope_static.numerics`; do not add new flat Stage 1, discovery, likelihood,
window, Google, or local-mechanism implementation modules directly under
`src/scope_static/`.

Experiment command wrappers should be grouped by experiment family. Stage 3
wrappers live under `scope_static.experiments.stage3`; Willow/Google hardware-data
wrappers live under `scope_static.experiments.willow_data`; QEC noise catalog/S2D wrappers live
under `scope_static.experiments.qec_noise_catalog`; Stage 1/Stage 2 DEM wrappers live
under `scope_static.experiments.static`; Stage 4 bridge/transfer wrappers live
under `scope_static.experiments.stage4`. Do not add new flat `run_stage3*`,
`run_stage4*`, `run_google*`, `run_static*`, `run_phyc*`, `run_layer*`, or
`run_s2d*` modules under `scope_static.experiments`.

The project-level problem is the six-axis physical generation problem: prove
that a physically constrained generation model holds simultaneously in
generation fidelity, interpretability, decoder utility, cross-context
generalization, drift prediction, and identifiability. CPTP/GKSL structure is a
constraint mechanism, not the full claim by itself.

Stage 1 learns fault logits over a canonicalized detector error model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
```

Keep notation aligned with `docs/SCOPE_TWIN.md`:

- `A` is the DEM parity map.
- `e in {0,1}^M` is the latent effective-fault vector.
- `y in {0,1}^B` is the observed detector/logical bit vector.
- `lambda_j` is the Stage 1 fault logit.
- `omega(j)` is a known orbit assignment.
- `S` or `Pi` is a learned Stage 2 discovery assignment.
- Do not use `o` for orbit or observable.
- Do not use `ell_j` for logits.

## Numerical Floor Policy

Use `scope_static.numerics.NUMERICAL_ZERO == 1e-12` for floating numerical
floors, simulation thresholds, probability floors, and leftover/complement
probabilities that would otherwise become exact `0.0`. This value is chosen to
survive square/cube operations in GPU float32. `NUMERICAL_FLOOR` exists only as
a descriptive alias. Do not replace structural zeros: Pauli/operator matrix
entries, bit values, integer indices, counts, labels, array sizes,
empty-artifact metrics, and exact algebraic identities must remain exact zeros
where required.

## GPU-First Execution

Treat this repository as a GPU-heavy QEC research program. Assume the target
workstation has a CUDA device, at least RTX 5090 class, even if the current
agent sandbox/session cannot see it. For any serious training, likelihood,
local-window, Google-data, or large ablation workflow, prefer native GPU
execution and accelerate with CUDA/PyTorch/C++ extensions as much as the code
path permits.

Before long runs, verify CUDA visibility from the `aiqec` environment. Failure
to see CUDA in one agent/session is an environment visibility problem to
diagnose, not evidence that the project should fall back to CPU-first design:

```bash
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

When running GPU commands through Codex, make sure the exact command prefix is
approved to run outside the sandbox. Wrappers such as `/usr/bin/time` or Conda's
`--no-capture-output` can otherwise execute inside the sandbox and make Torch
report no CUDA/NVML even though the workstation GPU is healthy. Prefer in-process
`time.perf_counter()` wall-clock reporting for benchmark metrics, or request an
approval for the wrapped command before treating CUDA invisibility as a real
runtime failure.

For current Google real-data work, the mainline Stage 3 closeout path is the V2
public syndrome-response surface. Build it through the public cache and
aggregate cache so the frozen learner-visible matrix is not coupled to repeated
Google source parsing:

```bash
scope-google-s3-visible-cache-v2 --config configs/scope_static/google_s3_visible_cache_v2.yaml
scope-google-s3-visible-aggregate-v2 --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
scope-google-s3-visible-adapter-v2 --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

The cache and aggregate configs support `num_workers`; current configs use 8
workers and emit per-block wall-clock timing. If a console script is missing
after code changes, reinstall the editable package with
`conda run -n aiqec python -m pip install -e .` or run the module entrypoint.

The old Google DEM/static predictive runner is archived as a historical
diagnostic, not a mainline Google path. The V1 fixed-window adapter remains for
regression comparison only; do not use it as the current Google evidence path.

If GPU utilization is low, do not assume the GPU path is broken. First check
whether the workload is launch-bound or CPU-preprocessing-bound: local exact
windows with small `max_window_bits` can finish in short CUDA bursts, while
window/cache construction, `.b8` loading, Stim/DEM parsing, and cross-sample
bookkeeping may still dominate CPU time. When improving performance, prioritize
moving repeated preprocessing and cache construction out of Python loops, reusing
prepared GPU caches across models/samples, and adding native CUDA/C++ kernels for
hot paths.

## Commands

Install:

```bash
conda run -n aiqec python -m pip install -e .
```

Test:

```bash
conda run -n aiqec python -m pytest -q
```

Run MVP05 smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.run --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

Run MVP05 full:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.run --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Run Catalog Pipeline facade:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.catalog_pipeline \
  --config configs/scope_static/d3_r1_S2D_PHYS_cudaq.yaml \
  --run-local-inverse auto
```

Run S2D.11 typed learner and S2D.11b calibration audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.s2d11b_m1_gate_branch_grouped_calibration_audit \
  --config configs/scope_static/s2d11b_m1_gate_branch_grouped_calibration_audit.yaml
```

Run current Layer1.P medium contract teacher and Stage 3/5 chain:

```bash
conda run -n aiqec python -m scope_static.experiments.qec_noise_catalog.data_preparation_teacher \
  --config configs/scope_static/s5_medium_hard_allM_contract_teacher_20q_depth20_g20.yaml

conda run -n aiqec python -m scope_static.experiments.qec_noise_catalog.teacher_physicality_audit \
  --config configs/scope_static/teacher_physicality_audit.yaml

conda run -n aiqec python -m scope_static.experiments.stage3.protocol_freeze \
  --config configs/scope_static/stage3a_protocol_freeze.yaml

conda run -n aiqec python -m scope_static.experiments.stage3.observability_ceiling \
  --config configs/scope_static/stage3a5_observability_ceiling.yaml

conda run -n aiqec python -m scope_static.experiments.stage3.discovery_model \
  --config configs/scope_static/stage3b1_discovery_model.yaml

conda run -n aiqec python -m scope_static.experiments.stage5.property_recovery \
  --config configs/scope_static/stage5b1_property_recovery.yaml
```

Do not use `PYTHONPATH="$PWD/src"` for normal runs on this WSL/CUDA setup. The
package should be installed editable; setting `PYTHONPATH` can interfere with
PyTorch CUDA/NVML discovery.

## Evidence Discipline

Stage 1 evidence must include seed-aware summaries, graph/window audits,
compression accounting, and baseline comparisons against `local`, `dmle_qec`,
`hard_orbit`, and `soft_feature_orbit`.

Soft residual claims require nonzero centered within-orbit feature rank.
Compression claims require explicit parameter audits.

Stage 2 discovery should begin with synthetic teachers and report ARI/NMI before
using Google repetition-code or surface-code data as external empirical
validation.

## Current Catalog Milestone Boundary

The catalog pipeline uses responsibility-named packages. `PHYC1`, `PHYC2`, and
`PHYC3` remain legacy artifact aliases in existing paths, schemas, and tests.

```text
scope_static.primitives
  low-level channel, PTM, probe, CPTP/POVM, density-sim, and preflight support

scope_static.data_preparation
  legacy alias PHYC1; generates mechanism records, probe schedules,
  sampled observations, teacher config, and sampling audits

scope_static.teacher
  legacy alias PHYC2; verifies teacher/catalog self-distinguishment with
  BA, min recall, ARI, and NMI gates

scope_static.learner
  legacy alias PHYC3; consumes learner-visible grouped predictions, not
  teacher-self predictions, and reports classification plus generated
  noise/error quality including channel distance, NLL, and MAE

scope_static.mechanism_observability
  S2D local inverse, typed SPAM/gate features, generator-space calibration,
  M1 calibration, and RZZ probe adapters

scope_static.mechanism_discovery
  Stage 3/4 latent assignment, alias-ceiling, prototype, generator, transfer,
  Google-unit source expansion, robustness artifacts, and S5 effect audits
```

Do not rebuild a broad `scope_static.physical` package. New workflow code should
live in the responsibility package that owns it; new primitive math/sampling
support should live in `scope_static.primitives`.

Variant labels describe the teacher source, not a change in the PHYC meaning:

```text
separability_v2:
  engineered local-observable stress teacher

Born-local:
  exact local Born-rule diagnostic, effective depth one

full-circuit-cudaq:
  required Stage 2E mainline: literal n-qubit noisy circuits at gate depth d
```

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.
Stage 3B/3C/3D must consume frozen visible features, evaluator-only labels,
teacher paths, and JSON artifacts through `scope_static.mechanism_discovery.artifacts`.
Public Stage 3 run functions are exported from `scope_static.mechanism_discovery`;
do not add new flat Stage 3 modules, rebuild visible features from
`oracle_mechanisms.json`, or import private helpers from sibling stages.

Stage 4 remains artifact-contract-first. S4.6 Google-unit source expansion may
use Google visible data only through the declared design split to construct
source modes, then must report transfer only on heldout Google rows. Robustness
closeout requires paired bootstrap, seed/split repeat, stronger statistical
controls including the visible-surface dMLE-style marginal MLE baseline, and
mechanism/source-structure ablations. It still may claim only visible
syndrome-response replay/source-transfer evidence, not true Google physical
mechanism recovery, Google public F/M label recovery, Google legacy catalog-ID
recovery, Born-rule physical generation, or CPTP/GKSL channel learning.

Stage 5 extends recovered mechanism/family structure with context-relative
effect audits: common action location inside each context and
context-normalized visible strength. S5 artifacts are evaluator-only
interpretation outputs. They must not feed learner training or model selection
and must not claim true Google physical mechanism recovery, Google public F/M
label recovery, Google legacy catalog-ID recovery, or CPTP/GKSL parameter
learning.

The `separability_v2` allM artifacts are strong Stage 2 separability evidence,
not a Born-rule physical baseline. Older PHYC2/PHYC3 artifacts are compatibility
evidence and must not be cited as the current Stage 3/5 claim path unless their
source audits are rechecked and the claim is explicitly Stage 2. The current
controlled Stage 3/5 path starts from the Layer1.P medium contract teacher,
runs the blocking physicality audit, freezes the Stage 3 visible protocol, and
uses S5 property heads only as evaluator-side interpretation. Legacy M11 /
public M6 spectator crosstalk RZ/ZZ remains a contract-sensitive overlay
mechanism; do not collapse it into a local Born diagnostic when making
full-circuit claims.

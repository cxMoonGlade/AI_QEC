# SCOPE-Static Toolbox

`scope-static` is a pre-release toolbox for physical-mechanism QEC experiments.
It is organized as reusable tools rather than a single end-to-end claim.

## Program Surface: 2+1

1. **Generate teacher-declared noisy QEC observations.** Data preparation creates
   sampled observations from a declared physical mechanism set in a controlled
   catalog. Users control enabled mechanism IDs, parameters, shot count, probe
   schedule, circuit depth, and instance counts through YAML. The enabled
   mechanisms use catalog unitary/Kraus/readout definitions.

2. **Learn and replay visible noise.** Learner learns from the
   learner-visible observation surface and reports whether predicted mechanisms
   can replay similar visible noisy observation distributions, scored by channel
   distance, NLL, population CE, and MAE. This is a no-leakage recovery/replay
   claim under the current protocol, not unsupervised hidden-partition
   inference.

3. **The +1: discover the latent mechanism quotient.** Stage 3 removes direct
   mechanism-label supervision and asks whether SCOPE-Discovery can learn the
   latent mechanism structure, assignments, prototypes, and observational alias
   classes from visible observations alone.

## Command Surface

| command | responsibility | purpose |
| --- | --- | --- |
| `scope-static-toolbox` | manifest | Print the toolbox manifest and public catalog stage map. |
| `scope-data-preparation-teacher` | data preparation | Generate a first-class physical-process teacher with pre-sampling CPTP/POVM checks and post-sampling physicality audit. |
| `scope-catalog-teacher` | catalog teacher | Generate controlled-catalog teacher artifacts through the compatibility command. |
| `teacher-distinguishment` | teacher | Verify that the declared teacher/catalog can self-distinguish generated mechanisms. |
| `learner-acceptance` | learner | Select the accepted learner source and report classification, channel-distance, NLL, and MAE quality. |
| `scope-stage3a-freeze` | Stage 3A: Dataset And Protocol Freeze | Freeze visible schema, split manifest, batch/context protocol, assignment unit, and forbidden-feature audit before discovery training. |
| `scope-stage3a5-ceiling` | Stage 3A.5: Observability And Alias Ceiling | Compute pairwise visible distances, oracle-visible alias classes, exact-label ceiling, and quotient-label ceiling before discovery training. |
| `scope-stage3b0-baselines` | Stage 3B.0: Non-Learned Clustering Baselines | Run visible-only k-means/GMM baselines and null controls with evaluator-only exact-label and quotient-label scoring. |
| `scope-stage3b1-discovery` | Stage 3B.1: First Discovery Model | Train a visible-only prototype-mixture discovery model with learned diagonal covariance and evaluator-only exact/quotient scoring. |

Historical artifact folders may still use `PHYC1/PHYC2/PHYC3` names for
compatibility. Public-facing code should use `data_preparation`,
`teacher`, and `learner`.

## Physicality Boundary

Layer1.P physicality comes from implemented catalog mechanisms validated before
sampling as unitary channels, Kraus channels, or classical readout assignment
matrices, then checked again by a post-sampling physicality audit. Learner
inherits catalog physicality only when it predicts/reuses a catalog mechanism;
visible empirical replay is a visible-distribution model, not by itself a
learned CPTP channel.

The toolbox does not yet claim arbitrary CPTP/GKSL channel learning by
construction. See `docs/PHYSICALITY.md`.

## Install

Use any Python `>=3.10` environment. From the repo root:

```bash
python -m pip install -e .
```

## Quick Checks

Print the toolbox manifest:

```bash
scope-static-toolbox
```

Machine-readable manifest:

```bash
scope-static-toolbox --json
```

Run the current canonical learner acceptance artifact:

```bash
learner-acceptance \
  --config configs/scope_static/learner_acceptance.yaml
```

Equivalent module form:

```bash
python -m scope_static.experiments.qec_noise_catalog.learner_acceptance \
  --config configs/scope_static/learner_acceptance.yaml
```

Generate a user-defined noisy mechanism dataset:

```bash
scope-data-preparation-teacher \
  --config configs/scope_static/layer1_user_defined_mechanisms.yaml \
  --output-dir outputs/scope_static/user_defined_data_preparation_demo/DataPreparation_teacher
```

## Data Products

Data preparation produces:

- `oracle_mechanisms.json`
- `observations.npz`
- `teacher_config.json`
- `sampling_audit.json`
- `active_probe_manifest.json`

Data preparation also emits:

- `layer1p_pre_sampling_contract.json`, checking the local mechanism process
  contract before sampling;
- `layer1p_teacher_contract.json`, summarizing the accepted physical teacher;
- `cptp_guardrail_audit.json`, checking complete-positivity representation
  class, declared channel dimension, unitarity, Kraus trace preservation,
  readout stochasticity, and parameter validity for every enabled mechanism
  record.
- `Layer1_teacher_physicality_audit/`, the legacy-named post-sampling blocking audit.

Teacher produces:

- teacher self-distinguishment metrics;
- BA, ARI, NMI, and min-recall gates;
- coverage and no-learner-prediction audits.

Learner produces:

- Z/X visible feature schema and deterministic visible ceiling;
- no-leakage learner predictions;
- multi-context distributional head metrics;
- protocol-validity and leakage audits;
- channel/readout prototype quality;
- visible-generation Gaussian NLL, population cross entropy, and MAE.

Stage 3 discovery scaffolding produces:

- Stage 3A protocol-freeze artifacts;
- Stage 3A.5 observability ceiling and oracle alias classes;
- Stage 3B.0 non-learned assignment matrices, baseline metrics, controls,
  quotient metrics, and model-selection leakage audits.
- Stage 3B.1 learned assignment matrix, visible prototypes, covariance
  parameters, heldout visible-generation metrics, and label-leakage audits.

## Current Pre-Release Boundary

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner models
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone.

The toolbox does not yet claim real-hardware ground-truth mechanism recovery,
arbitrary CPTP/GKSL channel learning by construction, complete SCOPE-Twin
physical generation, decoder utility, drift prediction, or cross-context
generalization.

Roadmaps:

- `docs/STAGE2_ROADMAP.md`: closed Stage 2 validation record.
- `docs/STAGE3_ROADMAP.md`: active Stage 3 discovery plan.

# SCOPE-Static Toolbox

`scope-static` is a pre-release toolbox for physical-mechanism QEC experiments.
It is organized as reusable tools rather than a single end-to-end claim.

## Program Surface: 2+1

1. **Generate teacher-declared noisy QEC observations.** Layer 1 prepares
   sampled observations from a declared physical mechanism set in a controlled
   catalog. Users control enabled mechanism IDs, parameters, shot count, probe
   schedule, circuit depth, and instance counts through YAML. The enabled
   mechanisms use catalog unitary/Kraus/readout definitions.

2. **Learn and replay visible noise.** Layer 3 learns from the
   learner-visible observation surface and reports whether predicted mechanisms
   can replay similar visible noisy observation distributions, scored by channel
   distance, NLL, population CE, and MAE. This is a no-leakage recovery/replay
   claim under the current protocol, not unsupervised hidden-partition
   inference.

3. **The +1: discover the latent mechanism quotient.** Stage 3 removes direct
   mechanism-label supervision and asks whether SCOPE-Discovery can learn the
   latent mechanism structure, assignments, prototypes, and observational alias
   classes from visible observations alone.

## Tool Layers

| command | layer | purpose |
| --- | --- | --- |
| `scope-static-toolbox` | manifest | Print the toolbox manifest and public Layer map. |
| `scope-layer1-prep` | Layer 1: Data Preparation (Prep) | Generate mechanism records, probe schedules, sampled observations, and sampling audits. |
| `scope-layer2-teacher` | Layer 2: Teacher Self-Distinguishment (Teacher) | Verify that the declared teacher/catalog can self-distinguish generated mechanisms. |
| `scope-layer3-canonical` | Layer 3: Learner Classification and Noise Generation (Learner) | Select the accepted learner source and report classification, channel-distance, NLL, and MAE quality. |

Historical modules and artifact folders still use `PHYC1/PHYC2/PHYC3` names for
compatibility. Public-facing reports should use Layer 1/2/3 names.

## Physicality Boundary

Layer 1 physicality comes from the implemented catalog mechanisms: unitary
channels, Kraus channels, and classical readout assignment matrices. Layer 3
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

Run the current canonical Layer 3 acceptance artifact:

```bash
scope-layer3-canonical \
  --config configs/scope_static/layer3_canonical_acceptance.yaml
```

Equivalent module form:

```bash
python -m scope_static.experiments.run_layer3_canonical_acceptance \
  --config configs/scope_static/layer3_canonical_acceptance.yaml
```

Generate a user-defined noisy mechanism dataset:

```bash
scope-layer1-prep \
  --config configs/scope_static/layer1_user_defined_mechanisms.yaml \
  --output-dir outputs/scope_static/user_defined_layer1_demo/S2D_PHYC1_teacher
```

## Data Products

Layer 1 produces:

- `oracle_mechanisms.json`
- `observations.npz`
- `teacher_config.json`
- `sampling_audit.json`
- `active_probe_manifest.json`

Layer 1 also emits:

- `cptp_guardrail_audit.json`, checking complete-positivity representation
  class, declared channel dimension, unitarity, Kraus trace preservation,
  readout stochasticity, and parameter validity for every enabled mechanism
  record.

Layer 2 produces:

- teacher self-distinguishment metrics;
- BA, ARI, NMI, and min-recall gates;
- coverage and no-learner-prediction audits.

Layer 3 produces:

- Z/X visible feature schema and deterministic visible ceiling;
- no-leakage learner predictions;
- multi-context distributional head metrics;
- protocol-validity and leakage audits;
- channel/readout prototype quality;
- visible-generation Gaussian NLL, population cross entropy, and MAE.

## Current Pre-Release Boundary

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train Layer 3 learners
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

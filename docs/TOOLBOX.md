# SCOPE-Static Toolbox

`scope-static` is a pre-release toolbox for physical-mechanism QEC experiments.
It is organized as reusable tools rather than a single end-to-end claim.

## Program Surface: 2+1

1. **Generate noisy data.** Layer 1 prepares sampled noisy data from a declared
   physical mechanism set. Users control enabled mechanism IDs, parameters,
   shot count, probe schedule, circuit depth, and instance counts through YAML.

2. **Learn and replay visible noise.** Layer 3 learns from the
   learner-visible observation surface and reports whether predicted mechanisms
   can generate similar visible noisy data, scored by channel distance, NLL,
   population CE, and MAE.

3. **The +1: discover the mechanism cause.** Stage 3 removes direct
   mechanism-label supervision and asks whether SCOPE-Discovery can recover the
   latent mechanism structure, assignments, and prototypes that caused the
   noisy observations.

## Tool Layers

| command | layer | purpose |
| --- | --- | --- |
| `scope-static-toolbox` | manifest | Print the toolbox manifest and public Layer map. |
| `scope-layer1-prep` | Layer 1: Data Preparation (Prep) | Generate mechanism records, probe schedules, sampled observations, and sampling audits. |
| `scope-layer2-teacher` | Layer 2: Teacher Self-Distinguishment (Teacher) | Verify that the declared teacher/catalog can self-distinguish generated mechanisms. |
| `scope-layer3-canonical` | Layer 3: Learner Classification and Noise Generation (Learner) | Select the accepted learner source and report classification, channel-distance, NLL, and MAE quality. |

Historical modules and artifact folders still use `PHYC1/PHYC2/PHYC3` names for
compatibility. Public-facing reports should use Layer 1/2/3 names.

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

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.

The toolbox does not yet claim real-hardware ground-truth mechanism recovery,
complete SCOPE-Twin physical generation, decoder utility, drift prediction, or
cross-context generalization.

Roadmaps:

- `docs/STAGE2_ROADMAP.md`: closed Stage 2 validation record.
- `docs/STAGE3_ROADMAP.md`: active Stage 3 discovery plan.

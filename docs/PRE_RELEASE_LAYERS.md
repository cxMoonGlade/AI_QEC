# Pre-Release Layer Stack

This document is the public-facing view of the physical-mechanism recovery
toolbox. Historical code and older artifacts may still use `PHYC1`, `PHYC2`,
and `PHYC3`; the public layer names below are canonical for pre-release
reporting.

## Layer Names

```text
Layer 1: Data Preparation (Prep)
  legacy alias: PHYC1

Layer 2: Teacher Self-Distinguishment (Teacher)
  legacy alias: PHYC2

Layer 3: Learner Classification and Noise Generation (Learner)
  legacy alias: PHYC3
```

## What Each Layer Generates

| layer | role | generated data |
| --- | --- | --- |
| Layer 1: Prep | Builds the declared physical-mechanism dataset. | Mechanism catalog records, probe schedules, sampled observations, teacher config, sampling audit, active probe manifest. |
| Layer 2: Teacher | Tests whether the declared teacher/catalog can self-distinguish every generated mechanism. | Teacher self predictions, BA/ARI/NMI/min-recall gates, coverage audits, explicit confirmation that no learner grouped predictions are emitted. |
| Layer 3: Learner | Tests no-leakage recovery from learner-visible observations and scores generated noise/error quality. | Z/X visible feature schema, deterministic visible ceiling, learner predictions, Gaussian distributional head metrics, protocol-validity audit, channel/readout prototype quality, visible-generation NLL and MAE. |

Layer 3 is not allowed to consume Layer 2 teacher-self predictions, oracle
channel matrices, teacher-self embeddings, hidden prototype vectors, hidden
mechanism IDs as features, or physical-family labels as features.

## Public Program Surface

The pre-release toolbox should be read as two supported capabilities plus one
active research object:

1. Layer 1 generates noisy data from user-enabled physical mechanisms.
2. Layer 3 learns from learner-visible observations and generates similar
   reproducible visible noisy data.
3. Stage 3 asks which latent mechanism caused the noise, without direct
   mechanism-label supervision.

## Physicality Boundary

Layer 1 noisy-data generation uses implemented catalog definitions: unitary
channels, Kraus channels, and classical readout assignment matrices. Enabling a
mechanism ID selects that definition and its parameters.

Layer 3 generated-noise claims have two meanings:

- catalog-mechanism replay inherits the selected catalog mechanism definition;
- empirical visible replay is a visible-distribution model and is not by itself
  a learned CPTP channel.

Layer 1 emits `cptp_guardrail_audit.json` for per-run physicality audits.

## Toolbox Commands

```bash
scope-static-toolbox
scope-layer1-prep
scope-layer2-teacher
scope-layer3-canonical
```

See `docs/TOOLBOX.md` for install and command examples.

## Current Pre-Release Evidence

The current canonical Layer 3 artifact is:

```text
outputs/scope_static/PHYC3_canonical_quality_acceptance/
```

It selects `phyc3c_distributional_gaussian_likelihood_head` as the canonical
learner prediction source. It rejects Layer 2 teacher-self predictions, legacy
Layer 2 grouped predictions, and the old-surface Layer 3a baseline as canonical
learner evidence.

Current canonical metrics:

```text
Layer 2 teacher self:
  BA / ARI / NMI / min recall = 1.0

Layer 3b visible repair:
  deterministic visible ceiling BA / ARI / NMI = 1.0
  visible conflicts after = 0

Layer 3c accepted learner:
  protocol = multi_context_batch
  BA / ARI / NMI / min recall / M13 recall = 1.0
  incompatible predictions = 0

Layer 3 canonical quality:
  quality records = 1050
  classification accuracy = 1.0
  mean predicted channel distance = 5.64e-05
  max predicted channel distance = 0.00373
```

Current visible-generation metrics from the accepted Layer 3 learner:

```text
visible Gaussian NLL        = 0.226681 nats / selected feature
oracle-label Gaussian NLL   = 0.226681
global-null Gaussian NLL    = 1.418941
NLL lift over global null   = 1.192259

population CE               = 0.252314 nats / probe distribution
population CE null lift     = 0.665166

raw visible-feature MAE     = 4.888e-06
population MAE              = 5.121e-06
expectation MAE             = 7.170e-06
```

Because the accepted learner predicts every held-out batch correctly in this
artifact, its predicted-label generator matches the oracle-label comparator.
The oracle comparator is evaluator-only and is not used as a learner input.

## Stage Boundary

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.

See `docs/STAGE2_ROADMAP.md` for the closed Stage 2 record and
`docs/STAGE3_ROADMAP.md` for the active discovery roadmap.

## Public Claim Boundary

Valid pre-release claims:

- the implemented M0-M34 physical mechanism catalog can generate layered
  physical-oracle artifacts from unitary/Kraus/readout definitions;
- the Layer 2 teacher self-distinguishment gate can verify catalog
  distinguishability;
- the Layer 3 learner can recover mechanisms from a strict no-leakage Z/X
  visible observation surface under the accepted multi-context protocol;
- the accepted Layer 3 learner can generate/scored visible error distributions
  with NLL and MAE close to the oracle comparator on the current artifact.

Not claimed yet:

- real-hardware ground-truth mechanism recovery;
- arbitrary CPTP/GKSL channel learning by construction;
- a complete SCOPE-Twin physical-generation model;
- decoder utility, drift prediction, or cross-context generalization as
  completed axes;
- Stage 3 unsupervised latent discovery success before its own ARI/NMI,
  prototype, and heldout-generation audits run.

# Catalog Pipeline

This document is the public-facing view of the controlled physical-mechanism
catalog toolbox. Historical artifacts may still use `PHYC1`, `PHYC2`, and
`PHYC3`; current code uses responsibility-named packages. Current controlled
Stage 3/5 evidence starts from the Layer1.P medium contract teacher plus
blocking physicality/protocol-freeze audits; PHYC2/PHYC3 teacher-learner
artifacts are Stage 2 compatibility evidence unless explicitly cited as such.

## Responsibilities

| package | legacy alias | role | generated data |
| --- | --- | --- | --- |
| `scope_static.data_preparation` | `PHYC1` | Build the declared physical-mechanism dataset. | Mechanism records, probe schedules, sampled observations, teacher config, sampling audit, active probe manifest. |
| `scope_static.teacher` | `PHYC2` | Test whether the declared teacher/catalog can self-distinguish every generated mechanism. | Teacher-self metrics, BA/ARI/NMI/min-recall gates, coverage audits, no-learner-prediction confirmation. |
| `scope_static.learner` | `PHYC3` | Test no-leakage recovery from learner-visible observations and score generated noise/error quality. | Visible feature schema, deterministic visible ceiling, learner predictions, distributional head metrics, protocol audits, channel/readout prototype quality, visible-generation NLL and MAE. |

Learner is not allowed to consume teacher-self predictions, oracle
channel matrices, teacher-self embeddings, hidden prototype vectors, mechanism
IDs as features, or physical-family labels as features.

## Program Surface

The pre-release toolbox has two supported capabilities plus one active research
object:

1. Data preparation generates teacher-declared noisy QEC observations from a
   controlled physical-mechanism catalog.
2. Learner learns from learner-visible observations and replays
   similar visible noisy observation distributions under no-leakage controls.
3. Stage 3 asks whether the latent mechanism quotient can be inferred from
   visible observations alone, without direct mechanism-label supervision.
4. Stage 5 audits context-relative location and strength recovery from fixed
   Stage 3 assignments; it is evaluator-side interpretation, not learner input.

## Physicality Boundary

Data-preparation generation uses implemented catalog definitions: unitary
channels, Kraus channels, and classical readout assignment matrices. Enabling a
mechanism ID selects that definition and its parameters. The teacher validates
the local CPTP/POVM process contract before sampling and runs a blocking
post-sampling physicality audit before accepting the artifact.

Learner generated-noise claims have two meanings:

- catalog-mechanism replay inherits the selected catalog mechanism definition;
- empirical visible replay is a visible-distribution model and is not by itself
  a learned CPTP channel.

## Commands

```bash
scope-static-toolbox
scope-data-preparation-teacher
scope-catalog-teacher
teacher-distinguishment
learner-acceptance
```

See `docs/TOOLBOX.md` for install and command examples.

## Stage Boundary

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner
models that recover and replay learner-visible noisy observation distributions
without oracle leakage.

Stage 3 is the next claim boundary: remove direct mechanism-label supervision
and test whether latent mechanism structure can be inferred from visible
observations alone.

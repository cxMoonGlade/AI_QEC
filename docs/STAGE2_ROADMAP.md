# Stage 2 Roadmap: Closed Record

Stage 2 is closed as the validation stage for the physical mechanism catalog
and the no-leakage visible recovery protocol.

Closure date: 2026-05-29.

## Scope

Stage 2 kept the Stage 1 fixed DEM/Bernoulli object:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

It then added synthetic discovery, physical-oracle teacher generation, teacher
self-distinguishment, and no-leakage visible learner.

## Closed Outcome

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner models
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone.

## What Stage 2 Proved

- The implemented physical catalog uses stable legacy `M0-M34` mechanism IDs;
  current semantic labels are public `F*` flat targets and public `M*`
  non-flat targets.
- Data-preparation mechanism definitions are catalog unitary/Kraus/readout objects, not
  arbitrary learned CPTP/GKSL channels.
- The public catalog pipeline is responsibility named:

  ```text
  data_preparation: Data Preparation (Prep)
  teacher: Teacher Self-Distinguishment (Teacher)
  learner: Learner Classification and Noise Generation (Learner)
  ```

- Teacher self-distinguishment can verify catalog separability.
- Z/X visible repair raised the learner-visible surface with a strict Z/X-only probe
  suite.
- The distributional learner head established an accepted multi-context learner head on that visible
  surface.
- Canonical learner quality consumes PHYC3c predictions only.
- Learner quality reports classification, incompatible predictions,
  channel/readout prototype distance, NLL, CE, and MAE.

## What Stage 2 Did Not Claim

- Unsupervised latent mechanism-structure discovery.
- Real-hardware ground-truth mechanism recovery.
- Arbitrary CPTP/GKSL channel learning by construction.
- Complete SCOPE-Twin physical generation.
- Completed decoder utility, cross-context generalization, or drift prediction
  axes.

Those are Stage 3 or later claims.

## Frozen Stage 2 Evidence Paths

Primary public evidence:

```text
outputs/scope_static/PHYC3_canonical_quality_acceptance/
```

Canonical source:

```text
phyc3c_distributional_gaussian_likelihood_head
```

Current public layer docs:

```text
docs/CATALOG_PIPELINE.md
docs/TOOLBOX.md
docs/SCOPE_STATIC_DISC.md
```

Superseded Stage 2 learner-limit, RZZ probe-design, and Born-local support code
has been promoted into the responsibility-named packages where it is still part
of the tested contract, or removed from the active tree otherwise.

## Stage 2 Artifact Rules

Teacher artifacts are teacher/catalog self-distinguishability evidence only.
They must not be cited as learner predictions.

Learner artifacts are no-leakage learner evidence only when their provenance
shows a learner source. Canonical learner quality rejects teacher-self
predictions and old-surface baseline predictions as canonical sources.

Evaluator-only labels, exact channels, PTMs, teacher self embeddings, and
mechanism IDs may be used for audits. They must not enter learner inputs.

## Handoff To Stage 3

Stage 3 starts from the Stage 2 visible observation surface and removes direct
mechanism-label supervision. The active roadmap is `docs/STAGE3_ROADMAP.md`.

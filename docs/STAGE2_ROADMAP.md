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
self-distinguishment, and no-leakage visible learner validation.

## Closed Outcome

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.

## What Stage 2 Proved

- The implemented physical catalog uses stable `M0-M34` mechanism IDs.
- The public physical stack is Layer 1/2/3:

  ```text
  Layer 1: Data Preparation (Prep)
  Layer 2: Teacher Self-Distinguishment (Teacher)
  Layer 3: Learner Classification and Noise Generation (Learner)
  ```

- Layer 2 teacher self-distinguishment can verify catalog separability.
- Layer 3b repaired the learner-visible surface with a strict Z/X-only probe
  suite.
- Layer 3c established an accepted multi-context learner head on that visible
  surface.
- Canonical Layer 3 quality consumes PHYC3c predictions only.
- Layer 3 quality reports classification, incompatible predictions,
  channel/readout prototype distance, NLL, CE, and MAE.

## What Stage 2 Did Not Claim

- Unsupervised latent mechanism-structure discovery.
- Real-hardware ground-truth mechanism recovery.
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
docs/PRE_RELEASE_LAYERS.md
docs/TOOLBOX.md
docs/SCOPE_STATIC_DISC.md
```

## Stage 2 Artifact Rules

Layer 2 artifacts are teacher/catalog self-distinguishability evidence only.
They must not be cited as learner predictions.

Layer 3 artifacts are no-leakage learner evidence only when their provenance
shows a Layer 3 learner source. Canonical Layer 3 rejects teacher-self
predictions and old-surface baseline predictions as canonical sources.

Evaluator-only labels, exact channels, PTMs, teacher self embeddings, and
mechanism IDs may be used for audits. They must not enter learner inputs.

## Handoff To Stage 3

Stage 3 starts from the Stage 2 visible observation surface and removes direct
mechanism-label supervision. The active roadmap is `docs/STAGE3_ROADMAP.md`.

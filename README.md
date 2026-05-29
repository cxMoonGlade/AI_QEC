# SCOPE-Static

`scope-static` is a pre-release toolbox for QEC noise-learning experiments.
It provides fixed-context DEM/Bernoulli learning tools and a layered
physical-mechanism validation stack.

The long-term target is the six-axis physical generation problem: a model must
be faithful as a generator, interpretable, useful to decoders, transferable
across contexts, predictive under drift, and identifiable. CPTP/GKSL structure
is one constraint mechanism, not the claim by itself.

## What It Can Do

- Prepare canonical DEM/Bernoulli data:

  ```text
  e_j ~ Bernoulli(p_j)
  y = A e mod 2
  lambda_j = logit(p_j)
  ```

- Train and compare fixed-context fault-logit models.
- Run synthetic SCOPE-Discovery audits with evaluator-only ARI/NMI.
- Generate physical-mechanism probe data through the public layer stack:

  ```text
  Layer 1: Data Preparation (Prep)
  Layer 2: Teacher Self-Distinguishment (Teacher)
  Layer 3: Learner Classification and Noise Generation (Learner)
  ```

- Audit no-leakage learner recovery from Z/X visible observations.
- Score generated visible noise/error quality with channel distance, NLL, CE,
  and MAE diagnostics.

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.

## Install

Python `>=3.10` is required. From the repository root:

```bash
conda run -n aiqec python -m pip install -e .
```

Do not set `PYTHONPATH="$PWD/src"` for normal WSL/CUDA runs. Use the editable
install.

## Brief Use

Print the toolbox manifest:

```bash
conda run -n aiqec scope-static-toolbox
```

Run the current canonical Layer 3 acceptance artifact:

```bash
conda run -n aiqec scope-layer3-canonical \
  --config configs/scope_static/layer3_canonical_acceptance.yaml
```

Run tests:

```bash
conda run -n aiqec python -m pytest -q
```

Outputs are written under `outputs/scope_static/` and `outputs/google_static/`.

## Docs

- `CONTEXT.md`: glossary and claim boundaries.
- `docs/TOOLBOX.md`: toolbox commands and data products.
- `docs/RUNBOOK.md`: supported functions and command recipes.
- `docs/ARCHITECTURE.md`: architecture and module map.
- `docs/STAGE2_ROADMAP.md`: closed Stage 2 record.
- `docs/STAGE3_ROADMAP.md`: active Stage 3 discovery roadmap.

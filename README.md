# SCOPE-Static

`scope-static` is a pre-release toolbox for QEC noise-learning experiments.
It provides fixed-context DEM/Bernoulli learning tools and a layered
physical-mechanism validation stack.

The long-term target is the six-axis physical generation problem: a model must
be faithful as a generator, interpretable, useful to decoders, transferable
across contexts, predictive under drift, and identifiable. CPTP/GKSL structure
is one constraint mechanism, not the claim by itself.

Physicality boundary: Layer 1 generates noisy data from implemented
unitary/Kraus/readout mechanism definitions. The current learner recovers
mechanisms and visible noisy behavior; it does not yet learn an arbitrary
CPTP/GKSL channel family by construction. See `docs/PHYSICALITY.md`.

## What It Can Do: 2+1 Surface

`scope-static` exposes two toolbox capabilities plus one active discovery
object.

1. Generate noisy data from user-defined physical mechanisms.
   Users choose enabled mechanism IDs, mechanism parameters, shot count, probe
   schedule, circuit depth, and mechanism instance counts. Layer 1 writes
   sampled observations and the manifests needed to reproduce them.

2. Learn from the learner-visible surface and generate similar reproducible
   noisy data.
   Layer 3 consumes only declared visible probe observations, predicts
   mechanism structure under no-leakage guardrails, and scores generated visible
   noise with channel-distance, NLL, CE, and MAE diagnostics.

3. The "+1": distinguish which mechanism caused the noise.
   This is the Stage 3 research object: remove direct mechanism-label
   supervision and test whether SCOPE-Discovery can recover latent mechanism
   structure, assignments, and prototypes from learner-visible observations.

The fixed DEM/Bernoulli object remains:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

The physical layer stack is:

```text
Layer 1: Data Preparation (Prep)
Layer 2: Teacher Self-Distinguishment (Teacher)
Layer 3: Learner Classification and Noise Generation (Learner)
```

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.

## Install

Python `>=3.10` is required. Use any environment manager you prefer. From the
repository root:

```bash
python -m pip install -e .
```

Optional isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

If you use Conda, create or activate your own environment first, then run the
same `python -m pip install -e .` command. Do not set `PYTHONPATH="$PWD/src"`
for normal runs; use the editable install.

## Brief Use

Print the toolbox manifest:

```bash
scope-static-toolbox
```

Run the current canonical Layer 3 acceptance artifact:

```bash
scope-layer3-canonical \
  --config configs/scope_static/layer3_canonical_acceptance.yaml
```

Run tests:

```bash
python -m pytest -q
```

Generate a small user-defined noisy mechanism dataset:

```bash
scope-layer1-prep \
  --config configs/scope_static/layer1_user_defined_mechanisms.yaml \
  --output-dir outputs/scope_static/user_defined_layer1_demo/S2D_PHYC1_teacher
```

Full-circuit physical generation requires a CUDA-Q-capable environment. The
config file is the public maintenance surface for changing enabled mechanisms
and their parameters.

Outputs are written under `outputs/scope_static/` and `outputs/google_static/`.

## Docs

- `CONTEXT.md`: glossary and claim boundaries.
- `docs/TOOLBOX.md`: toolbox commands and data products.
- `docs/PHYSICALITY.md`: CPTP/readout implementation and claim boundary.
- `docs/RUNBOOK.md`: supported functions and command recipes.
- `docs/ARCHITECTURE.md`: architecture and module map.
- `docs/STAGE2_ROADMAP.md`: closed Stage 2 record.
- `docs/STAGE3_ROADMAP.md`: active Stage 3 discovery roadmap.

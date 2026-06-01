# SCOPE-Static

`scope-static` is a pre-release toolbox for QEC noise-learning experiments.
It provides fixed-context DEM/Bernoulli learning tools and a controlled-catalog
QEC noise pipeline.

The long-term target is the six-axis physical generation problem: a model must
be faithful as a generator, interpretable, useful to decoders, transferable
across contexts, predictive under drift, and identifiable. CPTP/GKSL structure
is one constraint mechanism, not the claim by itself.

Physicality boundary: data preparation generates teacher-declared noisy QEC
observations from implemented catalog unitary/Kraus/readout mechanism
definitions. The current learner recovers and replays visible noisy observation
distributions under the declared protocol; it does not yet learn an arbitrary
CPTP/GKSL channel family by construction. See `docs/PHYSICALITY.md`.

## What It Can Do: 2+1 Surface

`scope-static` exposes two toolbox capabilities plus one active discovery
object.

1. Generate teacher-declared noisy QEC observations.
   Users choose enabled mechanism IDs, mechanism parameters, shot count, probe
   schedule, circuit depth, and mechanism instance counts. Data preparation writes
   sampled observations and the manifests needed to reproduce them from the
   controlled mechanism catalog.

2. Learn from the learner-visible surface and replay similar reproducible
   visible noisy observations.
   Learner consumes only declared visible probe observations and approved
   visible features, then scores recovery/replay with channel-distance, NLL, CE,
   and MAE diagnostics. This proves that the visible surface contains enough
   signal for no-leakage recovery/replay under the current protocol; it does not
   prove unsupervised hidden-partition inference.

3. The "+1": discover the latent mechanism quotient.
   This is the Stage 3 research object: remove direct mechanism-label
   supervision and test whether SCOPE-Discovery can recover latent mechanism
   structure, assignments, prototypes, and observational alias classes from
   learner-visible observations alone.

The fixed DEM/Bernoulli object remains:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

The catalog validation responsibilities are:

```text
data_preparation: Data Preparation (Prep)
teacher: Teacher Self-Distinguishment (Teacher)
learner: Learner Classification and Noise Generation (Learner)
```

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner models
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone.

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

Run the current canonical learner acceptance artifact:

```bash
learner-acceptance \
  --config configs/scope_static/learner_acceptance.yaml
```

Run tests:

```bash
python -m pytest -q
```

Generate a small user-defined noisy mechanism dataset:

```bash
scope-data-preparation-teacher \
  --config configs/scope_static/layer1_user_defined_mechanisms.yaml \
  --output-dir outputs/scope_static/user_defined_data_preparation_demo/DataPreparation_teacher
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


+====================================================================+
   ⠀⠀⠀⠀⠀⠀⢀⣤⣶⣶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⢀⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⢰⣿⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⣠⣾⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⢀⣾⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠶⠋⠉⠙⠻⣶⣦⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⢸⡿⠟⠁⠀⢸⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠞⠁⠀⠀⠀⠀⢠⣿⣿⣿⣿⣷⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⢈⡇⠀⠀⠀⠈⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠁⠀⠀⠀⠀⠀⢀⣸⣿⣿⣿⣿⣿⡿⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⣼⠀⠀⠀⠀⠀⠸⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠋⠀⠀⠀⠀⠀⠀⠀⣤⠞⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⣧⠀⠀⠀⠀⠀⠀⠹⣆⠀⠀⠀⠀⢀⣀⣠⣤⣤⣤⣞⠁⠀⠀⠀⠀⠀⠀⠀⣰⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⢻⠀⠀⠀⠀⠀⠀⠀⠹⣦⣠⠶⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠸⡇⠀⠀⠀⠀⠀⠀⠐⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⠀⠀⠐⢦⣰⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⣯⣽⣽⢦⡀⠀⠙⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠈⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⣿⡆⣿⣘⡇⠀⠀⠈⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠘⣆⠀⠀⠀⠀⣴⠒⣆⠀⠀⠀⠀⠀⠀⠀⠘⣧⣏⢻⣾⣛⠇⢀⢠⢄⡀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⣿⠀⠀⠀⢰⢿⡟⣿⣇⠀⠀⠀⠀⠀⠀⠀⠈⠿⠟⠋⠁⣔⣙⣳⢿⣿⡀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⣿⠀⠀⣀⢸⡘⣿⢛⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣗⣴⡢⣵⡀⡄⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⣿⢀⣾⠄⠵⡷⠯⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣀⢀⣾⣟⢈⡡⢶⠃⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⢸⣼⣋⣑⣚⡾⣷⣄⡀⠀⢀⣴⡿⢿⣶⣤⣴⡿⠉⠛⠿⠋⠈⠚⠐⠋⣼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠘⣧⢷⡡⢴⠋⠈⠻⢿⣶⡿⠋⠀⠀⠀⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⡼⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⠴⣶⡄
   ⠀⠀⠀⠀⠘⢷⣉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⠶⠛⠉⠁⠀⢸⠃⢻
   ⠀⠀⠀⠀⠀⠀⠙⠳⢧⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢧⠀⠀⠀⠀⠀⠀⠀⠀⣠⡴⠚⠉⠀⣀⣠⠄⠀⠀⢰⠀⢸
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⣛⠶⠒⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣇⠀⠀⠀⠀⢀⣴⠞⠁⣠⡴⠞⣋⣥⠤⠀⠀⠀⠈⢃⣼
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢣⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡄⠀⠀⠀⠸⡇⠀⠀⠀⠀⠉⢁⣀⣠⡤⠴⠶⠒⠛⠃
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣧⠀⠀⠀⢀⣿⠀⠀⠀⡖⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠃⠀⠀⠀⠀⢰⣿⠀⠀⠀⣰⣷⠀⠀⠀⠀⠀⠀⢸⡄⢠⡞⠋⠀⠀⠀⣀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⣿⡟⠀⠀⠀⣿⡟⠀⠀⠀⠀⠀⠀⠈⣇⠘⣧⠀⢰⡞⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⡾⠁⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠙⠁⠀⠀⠀⠀⠀⠀⠀⢻⢀⣼⠃⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⣀⣤⠴⠞⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠿⣵⡞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⣀⡴⠞⠋⠁⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠳⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠙⣳⠶⠒⠒⠒⢲⡞⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⢀⣠⡀⠀⠀⠀⢀⡟⠉⠙⠒⠶⡶⠦⠤⠤⠽⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠓⠒⠒⠚⠛⣟⣠⣤⠴⠖⡞⠋⡩⠷⣤⡀⣀⡤⢾⡋⠀⣀⣵⡄⠀⣼⠉⠉⠉⠑⠒⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠀⠀⠈⠙⠉⠀⠀⠉⠚⠁⠀⠙⠳⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
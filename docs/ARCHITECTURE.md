# Architecture

`scope_static` is a fixed-context QEC research package. Its implemented core is
the DEM/Bernoulli parity model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

The physical-mechanism catalog work is organized by responsibility, not by
generic "physical" layers.

## Package Map

```text
src/scope_static/
  dem/                     Stage 1 DEM/Bernoulli implementation
  google/                  Google Set1 adapters and proxy partitions
  backend/                 channel, PTM, probe, CPTP/POVM, and preflight support
  data_preparation/        controlled-catalog teacher generation
  teacher/                teacher self-distinguishment and visible-surface helpers
  learner/                no-leakage learner recovery and visible replay quality
  mechanism_observability/ S2D observability, calibration, and typed learner audits
  mechanism_discovery/     Stage 3 latent mechanism discovery artifacts and models
  catalog_pipeline/       controlled-catalog orchestration
  experiments/             thin CLI/config wrappers grouped by experiment family
  archive/                 historical research-stage modules with compatibility wrappers
  cuda/                    C++/CUDA exact DEM/window kernels
```

`backend` is intentionally low level. It contains physical and mathematical
support code: mechanism catalog definitions, unitary/Kraus/readout channels,
PTM fingerprints, local Born-rule utilities, CPTP/POVM audits, CUDA-Q preflight,
and probe-catalog helpers. It does not own the catalog workflows.

## Catalog Workflow

The current pre-release catalog validation flow is:

```text
mechanism catalog + enabled mechanism set
-> data_preparation: probe schedule, mechanism records, sampled observations
-> teacher: teacher/catalog self-distinguishability
-> learner: no-leakage learner recovery and visible-generation quality
-> mechanism_discovery: unsupervised latent quotient discovery
```

Legacy artifact aliases remain:

```text
PHYC1 -> data_preparation
PHYC2 -> teacher
PHYC3 -> learner
```

The code should use the responsibility packages above. New code should not add
flat modules under `src/scope_static/` or rebuild a broad `physical` package.

## Experiments

`scope_static.experiments` contains runnable wrappers only:

```text
experiments/static/            DEM and Stage 2 static-discovery commands
experiments/google/            Google Set1 commands and CUDA comparisons
experiments/qec_noise_catalog/ catalog teacher, validation, observability commands
experiments/stage3/            Stage 3A through Stage 3D commands
```

Preferred console scripts:

```text
scope-static-toolbox
scope-catalog-teacher
scope-data-preparation-teacher
teacher-distinguishment
learner-acceptance
scope-stage3a-freeze
scope-stage3a5-ceiling
scope-stage3b0-baselines
scope-stage3b1-discovery
scope-stage3c-generator
scope-stage3d1-assignment-shuffle
scope-teacher-physicality-audit
```

## Claim Boundary

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner
models that recover and replay learner-visible noisy observation distributions
without oracle leakage.

Stage 3 is the next claim boundary: remove direct mechanism-label supervision
and test whether latent mechanism structure can be inferred from visible
observations alone.

## Physicality Boundary

The data-preparation teacher samples observations from catalog mechanisms whose
underlying local modules are audited as unitary channels, Kraus channels,
classical stochastic readout maps embedded into POVMs, or related valid
instruments. The data themselves are not CPTP; CPTP/POVM validity is a property
of the generating process.

The current learner is not an arbitrary CPTP/GKSL channel learner by
construction.

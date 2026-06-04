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
  google/                  Google readers, inventory, and S3 visible surfaces/cache
  primitives/              channel, PTM, probe, CPTP/POVM, and preflight support
  data_preparation/        Layer1 preprocessing - teacher generator
  teacher/                Layer 2 teacher self-audit and visible-surface helpers
  learner/                Layer 3 learner recovery and visible replay quality
  mechanism_observability/ S2D observability, calibration, and typed learner audits
  mechanism_discovery/     Stage 3/4 discovery, Stage 5 property recovery, bridge, transfer, and robustness artifacts
  catalog_pipeline/       controlled-catalog orchestration
  experiments/             thin CLI/config wrappers grouped by experiment family
  cuda/                    C++/CUDA exact DEM/window kernels
```

`primitives` is intentionally low level. It contains physical and mathematical
support code: mechanism catalog definitions, unitary/Kraus/readout channels,
PTM fingerprints, local Born-rule utilities, CPTP/POVM audits, CUDA-Q preflight,
and probe-catalog helpers. It does not own catalog workflows, and it is not a
CUDA execution backend.

## Catalog Workflow

The current pre-release catalog validation flow is:

```text
mechanism catalog + enabled mechanism set
-> data_preparation: Layer1 preprocessing - teacher generator
-> teacher: Layer 2 teacher/catalog self-audit
-> learner: Layer 3 no-leakage recovery and visible-generation quality
-> mechanism_discovery: unsupervised latent quotient discovery
```

The current controlled Stage 3/5 route starts from the Layer1 preprocessing -
teacher generator, freezes a learner-visible Stage 3A protocol, audits
observability, trains S3B1 visible-only assignments, optionally promotes an
S3D4b visible-only postmerge assignment source, then runs S5B1
context-relative property recovery.

The code should use the responsibility packages above. New code should not add
flat modules under `src/scope_static/` or rebuild a broad `physical` package.

## Experiments

`scope_static.experiments` contains runnable wrappers only:

```text
experiments/static/            DEM and Stage 2 static-discovery commands
experiments/willow_data/       Google/Willow inventory, GPU diagnostics, S3 cache, and visible adapters
experiments/qec_noise_catalog/ catalog teacher, validation, observability commands
experiments/stage3/            Stage 3A through Stage 3D commands
experiments/stage4/            S4 bridge, source, transfer, and Google-unit commands
experiments/stage5/            S5 context-relative property-recovery commands
```

Preferred console scripts:

```text
scope-static-toolbox
scope-data-preparation-teacher
scope-stage3a-freeze
scope-stage3a5-ceiling
scope-stage3b0-baselines
scope-stage3b1-discovery
scope-stage3c-generator
scope-stage3d1-assignment-shuffle
scope-stage3d2-feature-scramble
scope-stage3d3-context-shuffle
scope-stage3d4-k-stress
scope-stage3d4b-overcomplete-merge-prune
scope-stage3-abc-observability-diagnostic
scope-stage4-synthetic-freeze
scope-stage4-source-ceiling
scope-stage4-source-pretrain
scope-stage4-support-audit
scope-stage4-assignment-geometry
scope-stage4-google-unit-source-expansion
scope-stage4-google-transfer
scope-stage4-transfer-diagnostics
scope-stage5b1-property-recovery
scope-stage5b1b-conditional-property-recovery
scope-google-s3-visible-cache-v2
scope-google-s3-visible-aggregate-v2
scope-google-s3-visible-adapter-v2
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

The current Google real-data Stage 3 closeout path is V2 public
syndrome-response replay: source Google files are reduced to a public cache,
then an aggregate cache, then frozen Stage 3A visible features. It supports a
no-oracle external replay claim over raw syndrome-response blocks, not true
hardware mechanism recovery.

Stage 4 extends the same artifact discipline. S4.6 builds a Google-unit
synthetic source surface from controlled-catalog mixtures and Google design-split
visible modes, then reports transfer only on heldout Google rows. Robustness
closeout is an audit layer, not a physical-channel claim.

## Physicality Boundary

Layer1 preprocessing - teacher generator samples observations from catalog
mechanisms whose underlying local modules are audited as unitary channels,
Kraus channels, classical stochastic readout maps embedded into POVMs, or
related valid instruments. The data themselves are not CPTP; CPTP/POVM
validity is a property of the generating process.

The current learner is not an arbitrary CPTP/GKSL channel learner by
construction.

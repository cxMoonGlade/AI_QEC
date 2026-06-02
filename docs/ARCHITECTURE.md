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
  data_preparation/        controlled-catalog teacher generation
  teacher/                teacher self-distinguishment and visible-surface helpers
  learner/                no-leakage learner recovery and visible replay quality
  mechanism_observability/ S2D observability, calibration, and typed learner audits
  mechanism_discovery/     Stage 3/4 discovery, bridge, transfer, and robustness artifacts
  catalog_pipeline/       controlled-catalog orchestration
  experiments/             thin CLI/config wrappers grouped by experiment family
  archive/                 historical research-stage modules with compatibility wrappers
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
experiments/willow_data/       Google/Willow inventory, GPU diagnostics, S3 cache, and visible adapters
experiments/qec_noise_catalog/ catalog teacher, validation, observability commands
experiments/stage3/            Stage 3A through Stage 3D commands
experiments/stage4/            S4 bridge, source, transfer, and Google-unit commands
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
scope-stage4-synthetic-freeze
scope-stage4-source-ceiling
scope-stage4-source-pretrain
scope-stage4-support-audit
scope-stage4-assignment-geometry
scope-stage4-google-unit-source-expansion
scope-stage4-google-transfer
scope-stage4-transfer-diagnostics
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

The data-preparation teacher samples observations from catalog mechanisms whose
underlying local modules are audited as unitary channels, Kraus channels,
classical stochastic readout maps embedded into POVMs, or related valid
instruments. The data themselves are not CPTP; CPTP/POVM validity is a property
of the generating process.

The current learner is not an arbitrary CPTP/GKSL channel learner by
construction.

+----------------------------------------------------------------------+<br>
|                            I CHOOSE YOU!                             |<br>
|                                                                      |<br>
|             @@@@@                                                    |<br>
|            @@@@#*                                              ..    |<br>
|           .#####.                        ....@@@@@:         .*###.   |<br>
|           *#####                 ..**#######@@@@@@:       *#######   |<br>
|          .#####* ........  ..**#############@@@@:      .*#########*  |<br>
|          *################################*::        *#############. |<br>
|          *###########/@@\###########**...          .*################|<br>
|         *###########|@@@|#######*               *###################.|<br>
|        ./@@|#########\@@/#ooo#####.            *###################*.|<br>
|        #|@@|#############oooooo###.         .*##################*.   |<br>
|       oo###*oooooo######oooooo####*        *###############*.        |<br>
|      ooo####oo    #######ooo#######.        *##########*..           |<br>
|       oo#####*.   ##################.        .*######.               |<br>
|        .#######**####################*         .#####*               |<br>
|         .#############################.:       .*#####.              |<br>
|  ..**##################################**   .*######**.              |<br>
| .#########################################* .*####.                  |<br>
| .##########################################*: .***.:                 |<br>
|   ..**######################################**  :   :                |<br>
|             ...*##############################*                      |<br>
|                 ###############################*::                   |<br>
|                 *###############################:                    |<br>
|                 .###############################                     |<br>
|                  *#############################.                     |<br>
|                   .#########**.....***########*                      |<br>
|                     ..**###               .####                      |<br>
|                         *##                .*##.                     |<br>
|                                               .                      |<br>
|                                                                      |<br>
|                               PIKACHU!                               |<br>
+----------------------------------------------------------------------+<br>

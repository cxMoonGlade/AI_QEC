# SCOPE-Static

`scope-static` is a QEC noise-learning research package. Its near-term goal is
to build a **digital twin by discovery mechanism**: learn compact,
auditable latent structure from QEC observations, then use that structure for
generation, interpretation, transfer, drift, and decoder-facing tests.

The package currently has three working surfaces:

1. fixed-context DEM/Bernoulli learning;
2. a controlled physical-mechanism catalog pipeline;
3. Stage 3 no-oracle visible-structure discovery and replay, including a real
   Google hardware-data V2 visible surface.

## Current Capabilities

### DEM/Bernoulli QEC Learning

The fixed-context object is implemented and tested:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

The code can build DEM parity maps, canonicalize fault mechanisms, train
fault-logit models, run local-window likelihood objectives, compare against
baselines, and report evidence records with compression, likelihood, and
window-plan audits.

### Controlled Physical-Mechanism Catalog

The catalog pipeline can generate teacher-declared noisy QEC observations from
enabled mechanisms and record the manifests needed to reproduce the run. The
mechanism catalog includes unitary, Kraus, and readout-style mechanisms with
CPTP/POVM/readout guardrail audits on the generating modules.

The public responsibilities are:

```text
data_preparation: Data Preparation (Prep)
teacher: Teacher Self-Distinguishment (Teacher)
learner: Learner Classification and Noise Generation (Learner)
```

The already-run Stage 2 evidence supports this bounded claim: the system can
generate controlled catalog observations, verify teacher/catalog separability,
and train no-leakage learners that recover and replay learner-visible noisy
observation distributions under the declared protocol.

### Stage 3 Discovery And Replay

Stage 3 removes direct mechanism-label supervision. The learner path consumes
only frozen visible features and approved public metadata. Evaluator-only labels,
channels, PTMs, Kraus matrices, teacher IDs, and oracle prototypes stay outside
the learner path.

The implemented Stage 3 stack can:

- freeze learner-visible feature matrices and split manifests;
- compute observability and alias-ceiling artifacts for controlled catalog data;
- train visible-only prototype-mixture assignments `Pi[j,k]`;
- run visible-generation replay with global-null, mean-only, oracle-comparator
  when labels exist, assignment-shuffle, feature-scramble, context-shuffle,
  K-stress, and public-stratified-null controls;
- report raw-target-only, full-target, and block-normalized S3C scores so
  metadata cannot silently dominate the headline.

For Google hardware data, the current mainline path is V2:

```text
source Google files
-> public precompute cache
-> aggregate cache
-> frozen V2 visible_features.npy
-> S3B1 visible-only assignments
-> S3C raw syndrome-response replay and controls
```

The V2 surface uses public syndrome-response signatures:

```text
raw__marginal
raw__spatial_corr
raw__temporal_corr
raw__logical_coupling
raw__stability
meta__public_geometry
```

The current Stage 3 Google closeout supports a specific result: V2 raw
syndrome-response replay beats global/mean-only, assignment-shuffle,
feature-scramble, and public-stratified-null controls under no-oracle rules.

### Stage 4 Bridge And Google-Unit Source Work

Stage 4 is artifact-contract-first. The code now covers S4.0 through S4.6:
bridge freeze, source ceiling, source pretrain, support/assignment diagnostics,
frozen transfer, and Google-unit source expansion.

S4.6 writes a Stage-3A-compatible source freeze at the
`synthetic_public_syndrome_response_signature` unit plus split-clean transfer,
control, and robustness-closeout audits. Robust-positive evidence still requires
a completed S4.6 rerun whose closeout artifacts pass.

## Current Limits

The package does not currently provide:

- a learner that directly parameterizes and optimizes arbitrary CPTP/GKSL
  channel families;
- a validated decoder-utility win from the discovered latent structure;
- a validated drift-prediction result on heldout future calibration periods;
- a validated cross-dataset transfer result across the four Google datasets;
- a closed robust-positive S4.6 evidence claim until the paired-bootstrap,
  repeat, stronger-control, and ablation closeout artifacts pass on the intended
  heldout Google run;
- a neural S4 model accepted as the main scientific claim; current S4 neural
  work remains gated by bridge-surface survival and source/Google transfer
  controls;
- true mechanism-label ARI/NMI on Google hardware data, because the Google
  artifacts used here provide observations, circuits, metadata, and decoder
  products rather than hidden physical mechanism labels;
- a claim that the metadata-inclusive `full_target` score alone measures
  syndrome-response learning. The current headline for Google V2 is
  `raw_target_only` plus block-normalized reporting and controls.

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

Build the current Google S3 V2 visible surface:

```bash
scope-google-s3-visible-cache-v2 --config configs/scope_static/google_s3_visible_cache_v2.yaml
scope-google-s3-visible-aggregate-v2 --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
scope-google-s3-visible-adapter-v2 --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

The cache and aggregate configs support `num_workers`; the current defaults use
8 workers and write block-level wall-clock timing into their manifests.

Then run the Stage 3 learner/generator stages against the frozen V2 artifact:

```bash
scope-stage3b1-discovery \
  --stage3a-dir outputs/google_static/google_s3_visible_surface_v2/S3A_protocol_freeze \
  --output-dir outputs/google_static/google_s3_visible_surface_v2/S3B1_raw_multiview_k4_8_16_32 \
  --evaluator-mode no_oracle_labels \
  --k-values 4,8,16,32 \
  --learner-input-profile raw_multiview_only

scope-stage3c-generator \
  --stage3a-dir outputs/google_static/google_s3_visible_surface_v2/S3A_protocol_freeze \
  --stage3b1-dir outputs/google_static/google_s3_visible_surface_v2/S3B1_raw_multiview_k4_8_16_32 \
  --output-dir outputs/google_static/google_s3_visible_surface_v2/S3C_raw_multiview_k4_8_16_32 \
  --evaluator-mode no_oracle_labels \
  --assignment-shuffle-seeds 0,1,2,3,4 \
  --feature-scramble-seeds 0,1,2,3,4
```

Outputs are written under `outputs/scope_static/` and `outputs/google_static/`.

Run the S4.6 Google-unit source expansion after the Google V2 freeze and S4.5
assignment/support diagnostics exist:

```bash
scope-stage4-google-unit-source-expansion \
  --config configs/scope_static/stage4_google_unit_source_expansion_v1.yaml
```

If console scripts are unavailable because the editable install is stale, rerun
`python -m pip install -e .` or use the module entrypoint:

```bash
python -m scope_static.experiments.stage4.google_unit_source_expansion \
  --config configs/scope_static/stage4_google_unit_source_expansion_v1.yaml
```

## Docs

- `CONTEXT.md`: glossary and claim boundaries.
- `docs/TOOLBOX.md`: toolbox commands and data products.
- `docs/PHYSICALITY.md`: CPTP/readout implementation and claim boundary.
- `docs/RUNBOOK.md`: supported functions and command recipes.
- `docs/ARCHITECTURE.md`: architecture and module map.
- `docs/STAGE2_ROADMAP.md`: closed Stage 2 record.
- `docs/STAGE3_ROADMAP.md`: Stage 3 discovery roadmap and Google V2 closeout
  boundary.
- `docs/STAGE4_ROADMAP.md`: S4 bridge-survival, neural pretrain, and
  frozen-transfer gates.


+====================================================================+ <br>
   ⠀⠀⠀⠀⠀⠀⢀⣤⣶⣶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀        <br>
   ⠀⠀⠀⠀⢀⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀        <br>
   ⠀⠀⠀⢰⣿⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀        <br>
   ⠀⠀⣠⣾⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀        <br>
   ⢀⣾⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠶⠋⠉⠙⠻⣶⣦⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⢸⡿⠟⠁⠀⢸⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠞⠁⠀⠀⠀⠀⢠⣿⣿⣿⣿⣷⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⢈⡇⠀⠀⠀⠈⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠁⠀⠀⠀⠀⠀⢀⣸⣿⣿⣿⣿⣿⡿⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⣼⠀⠀⠀⠀⠀⠸⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠋⠀⠀⠀⠀⠀⠀⠀⣤⠞⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀        <br>
   ⣧⠀⠀⠀⠀⠀⠀⠹⣆⠀⠀⠀⠀⢀⣀⣠⣤⣤⣤⣞⠁⠀⠀⠀⠀⠀⠀⠀⣰⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       <br>
   ⢻⠀⠀⠀⠀⠀⠀⠀⠹⣦⣠⠶⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       <br>
   ⠸⡇⠀⠀⠀⠀⠀⠀⠐⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⠀⠀⠐⢦⣰⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       <br>
   ⠀⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⣯⣽⣽⢦⡀⠀⠙⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       <br>
   ⠀⠈⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⣿⡆⣿⣘⡇⠀⠀⠈⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       <br>
   ⠀⠀⠘⣆⠀⠀⠀⠀⣴⠒⣆⠀⠀⠀⠀⠀⠀⠀⠘⣧⣏⢻⣾⣛⠇⢀⢠⢄⡀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⠀⠀⠀⣿⠀⠀⠀⢰⢿⡟⣿⣇⠀⠀⠀⠀⠀⠀⠀⠈⠿⠟⠋⠁⣔⣙⣳⢿⣿⡀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⠀⠀⠀⣿⠀⠀⣀⢸⡘⣿⢛⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣗⣴⡢⣵⡀⡄⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⠀⠀⠀⣿⢀⣾⠄⠵⡷⠯⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣀⢀⣾⣟⢈⡡⢶⠃⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀     <br>
   ⠀⠀⠀⢸⣼⣋⣑⣚⡾⣷⣄⡀⠀⢀⣴⡿⢿⣶⣤⣴⡿⠉⠛⠿⠋⠈⠚⠐⠋⣼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    <br>
   ⠀⠀⠀⠘⣧⢷⡡⢴⠋⠈⠻⢿⣶⡿⠋⠀⠀⠀⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⡼⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⠴⣶⡄     <br>
   ⠀⠀⠀⠀⠘⢷⣉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⠶⠛⠉⠁⠀⢸⠃⢻      <br>
   ⠀⠀⠀⠀⠀⠀⠙⠳⢧⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢧⠀⠀⠀⠀⠀⠀⠀⠀⣠⡴⠚⠉⠀⣀⣠⠄⠀⠀⢰⠀⢸      <br>
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⣛⠶⠒⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣇⠀⠀⠀⠀⢀⣴⠞⠁⣠⡴⠞⣋⣥⠤⠀⠀⠀⠈⢃⣼     <br>
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢣⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡄⠀⠀⠀⠸⡇⠀⠀⠀⠀⠉⢁⣀⣠⡤⠴⠶⠒⠛⠃     <br>
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣧⠀⠀⠀⢀⣿⠀⠀⠀⡖⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀       <br>
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠃⠀⠀⠀⠀⢰⣿⠀⠀⠀⣰⣷⠀⠀⠀⠀⠀⠀⢸⡄⢠⡞⠋⠀⠀⠀⣀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⣿⡟⠀⠀⠀⣿⡟⠀⠀⠀⠀⠀⠀⠈⣇⠘⣧⠀⢰⡞⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀     <br>
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⡾⠁⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠙⠁⠀⠀⠀⠀⠀⠀⠀⢻⢀⣼⠃⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      <br>
   ⠀⠀⠀⠀⠀⣀⣤⠴⠞⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠿⣵⡞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       <br>
   ⠀⣀⡴⠞⠋⠁⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠳⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       <br>
   ⠀⠙⣳⠶⠒⠒⠒⢲⡞⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⢀⣠⡀⠀⠀⠀⢀⡟⠉⠙⠒⠶⡶⠦⠤⠤⠽⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    <br>
   ⠀⠀⠓⠒⠒⠚⠛⣟⣠⣤⠴⠖⡞⠋⡩⠷⣤⡀⣀⡤⢾⡋⠀⣀⣵⡄⠀⣼⠉⠉⠉⠑⠒⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   <br>
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠀⠀⠈⠙⠉⠀⠀⠉⠚⠁⠀⠙⠳⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀           <br>

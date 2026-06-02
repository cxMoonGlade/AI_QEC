# Runbook

This runbook lists supported functions and reproducible commands. Use
`CONTEXT.md` for terminology and `docs/ARCHITECTURE.md` for system structure.

## Environment

Use any Python `>=3.10` environment. From the repo root:

```bash
python -m pip install -e .
```

Do not use `PYTHONPATH="$PWD/src"` for normal runs. The editable install is the
supported path.

The commands below use this workstation's development environment name
(`aiqec`) where GPU access matters. In another environment, replace
`conda run -n aiqec python` with your active environment's `python`, and replace
`conda run -n aiqec <command>` with `<command>` after activation.

Check CUDA before serious training, likelihood, Google, or physical-oracle runs:

```bash
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

If CUDA is unavailable in one shell, diagnose the environment before changing
experiment design.

## Function: Inspect Toolbox

```bash
conda run -n aiqec scope-static-toolbox
conda run -n aiqec scope-static-toolbox --json
```

## Function: Run Tests

Full suite:

```bash
conda run -n aiqec python -m pytest -q
```

Focused physical-layer/toolbox suite:

```bash
conda run -n aiqec python -m pytest -q \
  tests/test_toolbox_packaging.py \
  tests/test_phyc2_sampled_observation_separability.py \
  tests/test_phyc3_sampled_quantum_error_quality.py \
  tests/test_phyc3b_zx_visible_probe_suite.py \
  tests/test_phyc3c_gaussian_likelihood.py \
  tests/test_phyc3c_validation.py \
  tests/test_phyc3_canonical_acceptance.py
```

## Function: Train Stage 1 DEM Models

Smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.run \
  --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

Full local-window sweep:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.run \
  --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Supported outputs include metrics JSON, graph audits, window audits,
compression accounting, model records, and heldout likelihood summaries.

## Function: Run Stage 2 Static Discovery

Direct free-assignment discovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.discovery \
  --config configs/scope_static/d3_r1_STAGE2A_full.yaml
```

Summarize Stage 2A:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.stage2a0_summary \
  --metrics outputs/scope_static/STAGE2A_full/metrics.json
```

Passive identifiability audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.identifiability \
  --config configs/scope_static/d3_r1_STAGE2A_DISC10_passive_audit.yaml
```

Robust local-inverse discovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.disc16b_robustness \
  --config configs/scope_static/d3_r1_STAGE2C_DISC16b_robustness.yaml
```

Supported outputs include evaluator-only ARI/NMI, quotient recovery metrics,
active prototype counts, collapse flags, and label-use audits.

## Function: Build Google S3 V2 Visible Surface

```bash
scope-google-s3-visible-cache-v2 --config configs/scope_static/google_s3_visible_cache_v2.yaml
scope-google-s3-visible-aggregate-v2 --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
scope-google-s3-visible-adapter-v2 --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

Google data has no true hidden mechanism labels. The current mainline Google
path is a real-data adapter that freezes learner-visible Stage 3 artifacts from
public syndrome-response signatures.

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.willow_data.s3_visible_cache_v2 \
  --config configs/scope_static/google_s3_visible_cache_v2.yaml
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.willow_data.s3_visible_aggregate_v2 \
  --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.willow_data.s3_visible_adapter_v2 \
  --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

This path reads Google detection events and observable flips into a public
precompute cache, builds aggregate syndrome-response summaries, and writes
Stage 3A-compatible frozen visible artifacts:

```text
outputs/google_static/google_s3_visible_surface_v2_cache/precompute_cache/
  cache_manifest.json
  source_file_manifest.json
  contexts/cache_context_*.npz

outputs/google_static/google_s3_visible_surface_v2_cache/precompute_cache/aggregates/
  aggregate_manifest.json
  aggregate_context_*.npz

outputs/google_static/google_s3_visible_surface_v2/S3A_protocol_freeze/
  visible_features.npy
  visible_feature_schema.json
  forbidden_feature_audit.json
  split_manifest.json
  adequacy_report.json
  aggregate_cache_manifest.json
  metrics.json
```

Current cache and aggregate configs use `num_workers: 8`. Their manifests report
`parallelism`, `wallclock_by_block_seconds`, `wallclock_table`,
`slowest_block`, and `total_wallclock_seconds`.

## Function: Run Stage 4 Bridge And Transfer

Stage 4 wrappers are console scripts after an editable install. If a script is
missing, rerun `conda run -n aiqec python -m pip install -e .` or use the module
entrypoint.

```bash
conda run -n aiqec scope-stage4-synthetic-freeze \
  --config configs/scope_static/stage4_synthetic_google_surface_v1.yaml

conda run -n aiqec scope-stage4-source-ceiling \
  --config configs/scope_static/stage4_source_ceiling_v1.yaml

conda run -n aiqec scope-stage4-source-pretrain \
  --config configs/scope_static/stage4_source_pretrain_v1.yaml

conda run -n aiqec scope-stage4-google-unit-source-expansion \
  --config configs/scope_static/stage4_google_unit_source_expansion_v1.yaml
```

Equivalent S4.6 module command:

```bash
conda run -n aiqec python -m scope_static.experiments.stage4.google_unit_source_expansion \
  --config configs/scope_static/stage4_google_unit_source_expansion_v1.yaml
```

S4.6 writes the synthetic source freeze under `S3A_protocol_freeze/` and keeps
downstream diagnostics in the parent run directory. Robustness closeout artifacts:

```text
paired_bootstrap_report.json
seed_split_repeat_report.json
stronger_statistical_controls_report.json
mechanism_source_structure_ablation_report.json
robustness_closeout_report.json
```

Historical Google DEM-proxy diagnostics are archived under
`docs/archive/google_gdisc15.md`.

## Function: Generate Physical-Mechanism Data

Use this function when you want noisy data from explicitly enabled mechanisms.
The maintainable interface is YAML:

```yaml
s2d_physical:
  mechanism_set: allM
  mechanism_weight_profile: weighted_realistic_v1
```

Use `weighted_discovery_floor_v1` when rare/high-impact mechanisms should keep
a minimum support floor. These are synthetic exposure-weighted support profiles,
not hardware-calibrated frequency distributions.

The full template is
`configs/scope_static/layer1_user_defined_mechanisms.yaml`.

Small user-defined Layer1.P run:

```bash
scope-data-preparation-teacher \
  --config configs/scope_static/layer1_user_defined_mechanisms.yaml \
  --output-dir outputs/scope_static/user_defined_data_preparation_demo/DataPreparation_teacher
```

Catalog Pipeline facade:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.catalog_pipeline \
  --config configs/scope_static/d3_r1_S2D_PHYS_cudaq.yaml \
  --run-local-inverse auto
```

Layer1.P full-circuit CUDA-Q teacher:

```bash
conda run -n aiqec scope-data-preparation-teacher \
  --config configs/scope_static/data_preparation_teacher.yaml
```

Layer1.P produces mechanism records, probe schedules, sampled observations,
teacher config, sampling audits, active probe manifests, a pre-sampling
physical-process contract, and a post-sampling physicality audit. The older
`scope-catalog-teacher` command remains as a compatibility alias, but it now routes
through Layer1.P.

Layer1.P teacher generation:

```bash
conda run -n aiqec scope-data-preparation-teacher \
  --config configs/scope_static/data_preparation_teacher.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.qec_noise_catalog.data_preparation_teacher \
  --config configs/scope_static/data_preparation_teacher.yaml
```

Layer1.P is the first-class physical-process teacher. It validates the declared
local CPTP/POVM mechanism contract before sampling, runs full-circuit CUDA-Q
Born-rule sampling, then runs the post-sampling physicality audit as a blocking
gate. It writes `layer1p_pre_sampling_contract.json`,
`layer1p_teacher_contract.json`, `full_circuit_cudaq_summary.json`, and
`Layer1_teacher_physicality_audit/`.

Layer1.P teacher physicality audit only:

```bash
conda run -n aiqec scope-teacher-physicality-audit \
  --config configs/scope_static/teacher_physicality_audit.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.qec_noise_catalog.teacher_physicality_audit \
  --config configs/scope_static/teacher_physicality_audit.yaml
```

This post-hoc audit checks the teacher's generating maps, not the data as
`CPTP`. It checks local unitary/Kraus channels through Choi/TP/random-state
tests, readout maps as stochastic matrices embedded into POVMs, reset/prep
surrogates, leakage-surrogate bookkeeping, and empirical circuit output
normalization. It writes a `Layer1_teacher_physicality_audit/` artifact bundle
and is run automatically by the Layer1.P teacher generator.

### Full-Circuit g30 Timing Reference

The current full-circuit g30 run shows that the dominant cost is CUDA-Q
sampling inside the data-preparation teacher. The teacher artifact records explicit
wall-clock fields; Stage 3 stage timings below use artifact end-time deltas and
should be treated as approximate upper bounds.

Instrumented data-preparation teacher wall clock:

| Participant | Wall clock | Share |
| --- | ---: | ---: |
| CUDA-Q sampling | 3501.79s = 58m 21.8s | 83.88% |
| Observation materialization | 628.58s = 10m 28.6s | 15.06% |
| Other run overhead | 29.95s | 0.72% |
| Checkpoint writes | 10.00s | 0.24% |
| Readout postprocess | 2.98s | 0.07% |
| Circuit/mechanism assembly | 1.61s | 0.04% |
| **Teacher total** | **4174.91s = 1h 9m 34.9s** | **100%** |

Teacher run details:

```text
completed probe circuits: 8640
resumed/skipped probes:   691
new sampled probes:       7949
sampling sec / new probe: 0.4405s
teacher sec / probe:      0.4832s
```

Pipeline participant timing:

| Stage | Wall clock / interval |
| --- | ---: |
| S2D_PHYS0 preflight | 2.09s |
| S2D_PHYC1 full-circuit teacher resumed | 4174.91s = 1h 9m 34.9s |
| S3A protocol freeze | ~51.3s |
| S3A.5 observability ceiling | ~13.8s |
| S3B.0 baselines | ~67.7s |
| S3B.1 discovery model | ~281.3s = 4m 41.3s |

Practical bottleneck order:

```text
1. CUDA-Q sampling
2. observation/materialization writeout
3. S3B.1 candidate/model sweep
```

## Function: Audit Teacher Self-Distinguishment

Teacher balanced audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.teacher_distinguishment \
  --contract balanced \
  --teacher-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/DataPreparation_teacher \
  --output-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC2_balanced_teacher_self_distinguishment
```

Teacher tests teacher/catalog self-distinguishability. It is not a learner
success claim and must not emit canonical learner predictions.

## Function: Run No-Leakage Learner Recovery

Learner legacy no-leakage recovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.learner_recovery \
  --contract balanced \
  --teacher-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/DataPreparation_teacher \
  --output-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC3_no_leakage_learner_recovery
```

Learner quality from learner predictions:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.learner_quality \
  --teacher-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/DataPreparation_teacher \
  --prediction-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC3_no_leakage_learner_recovery \
  --output-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC3_no_leakage_learner_quality
```

Learner consumes learner-visible sampled observations. Forbidden learner inputs
include mechanism IDs, family labels, teacher self embeddings, exact channel
matrices, exact PTMs, oracle prototypes, and hidden parameters.

Learner generated-noise language must distinguish two cases: catalog-mechanism
replay inherits the catalog mechanism definition, while empirical visible replay
is a visible-distribution model and is not by itself a learned CPTP channel.

## Function: Run Canonical Learner Acceptance

```bash
conda run -n aiqec learner-acceptance \
  --config configs/scope_static/learner_acceptance.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.qec_noise_catalog.learner_acceptance \
  --config configs/scope_static/learner_acceptance.yaml
```

The canonical resolver selects `phyc3c_distributional_gaussian_likelihood_head`
only after teacher, visible repair, distributional learner, and
validation gates pass. It rejects teacher-self predictions, legacy grouped
predictions, and the old visible-surface baseline as canonical learner evidence.

## Function: Run Stage 3A Protocol Freeze

```bash
conda run -n aiqec scope-stage3a-freeze \
  --config configs/scope_static/stage3a_protocol_freeze.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.protocol_freeze \
  --config configs/scope_static/stage3a_protocol_freeze.yaml
```

Stage 3A writes `visible_feature_schema.json`, `forbidden_feature_audit.json`,
`operation_context_public_audit.json`, `split_manifest.json`,
`probe_schedule_manifest.json`, `batch_context_schema.json`, and
`assignment_unit.json`. It does not train a discovery model and does not compute
the Stage 3A.5 observability ceiling. The frozen visible feature matrix includes
Z/X sampled-observation features, derived visible summaries, and learner-visible
operation/instruction context metadata. That context is restricted to a fixed
public instruction alphabet and must not encode mechanism ID, record ID,
location ID, qubits, circuit ID, or slot ID.

## Function: Run Stage 3A.5 Observability Ceiling

```bash
conda run -n aiqec scope-stage3a5-ceiling \
  --config configs/scope_static/stage3a5_observability_ceiling.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.observability_ceiling \
  --config configs/scope_static/stage3a5_observability_ceiling.yaml
```

Stage 3A.5 consumes the frozen Stage 3A artifacts and writes
`observability_ceiling.json`, `oracle_alias_classes.json`,
`pairwise_visible_distance_matrix.json`, `evaluator_only_label_metrics.json`,
and `quotient_metrics.json`. It is evaluator-only and does not train a
discovery model.

## Function: Run Stage 3B.0 Non-Learned Clustering Baselines

```bash
conda run -n aiqec scope-stage3b0-baselines \
  --config configs/scope_static/stage3b0_baselines.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.baselines \
  --config configs/scope_static/stage3b0_baselines.yaml
```

Stage 3B.0 consumes the frozen Stage 3A and Stage 3A.5 artifacts, then runs
visible-only k-means, diagonal/full-covariance GMM baselines, global-null
controls, and mean-only controls. It writes `learned_assignments.npy`,
`baseline_assignments.npz`, `baseline_results.json`,
`evaluator_only_label_metrics.json`, `quotient_metrics.json`, `controls.json`,
and `model_selection_audit.json`. Mechanism and quotient labels are used only
after fitting for evaluator-only ARI/NMI/BA/min-recall reports.

## Function: Run Stage 3B.1 First Discovery Model

```bash
conda run -n aiqec scope-stage3b1-discovery \
  --config configs/scope_static/stage3b1_discovery_model.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.discovery_model \
  --config configs/scope_static/stage3b1_discovery_model.yaml
```

Stage 3B.1 consumes Stage 3A and Stage 3A.5, trains a visible-only
prototype-mixture discovery model with learned diagonal covariance, selects the
declared K mode using validation visible NLL plus a visible-only complexity
penalty over a declared capped set of Stage 3A validation folds. The default
structured objective applies `operation_context_weight: 2.0` to the
learner-visible operation-context block; this uses no mechanism labels. It uses
the declared first-run iteration budget from config and writes
`learned_assignments.npy`, `learned_prototypes.json`,
`learned_covariances.npy`, `model_parameters.npz`,
`prototype_generation_metrics.json`, `evaluator_only_label_metrics.json`,
`quotient_metrics.json`, `assignment_hardening_audit.json`, and
`model_selection_audit.json`. Mechanism labels, quotient labels, channels,
teacher IDs, and oracle prototypes are withheld from fitting and model
selection.

## Function: Run Stage 3C Prototype And Generator Learning

```bash
conda run -n aiqec scope-stage3c-generator \
  --config configs/scope_static/stage3c_generator_learning.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.generator_learning \
  --config configs/scope_static/stage3c_generator_learning.yaml
```

Stage 3C consumes Stage 3A, Stage 3A.5, and Stage 3B.1. It fits fold-local
visible generators from frozen `visible_features.npy` and B1
`learned_assignments.npy`, then scores heldout validation+test rows against
global-null and mean-only baselines. The primary likelihood metric is positive
`categorical_population_nll` over raw visible outcome groups; Gaussian density
NLL is retained as a secondary continuous-density diagnostic. It writes
`prototype_generation_metrics.json`, `predicted_assignment_metrics.json`,
`oracle_assignment_comparator_metrics.json`, `global_null_metrics.json`,
`mean_only_baseline_metrics.json`, `leakage_audit.json`, and
`acceptance_audit.json`. Oracle-label prototypes are evaluator-only
comparators; they are not used for predicted-assignment fitting or model
selection.

For controlled-catalog runs, Stage 3C also emits the current S5 artifact:
`s5_context_relative_mechanism_effect_audit.json`. It reports evaluator-only
family/exact-mechanism effect location and strength using context-relative
location and context-normalized visible strength. The compatibility alias
`soft_family_strength_location_audit.json` is written with the same payload.

## Function: Run Stage 3D.1 Assignment-Shuffle Generator Audit

```bash
conda run -n aiqec scope-stage3d1-assignment-shuffle \
  --config configs/scope_static/stage3d1_assignment_shuffle_audit.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.assignment_shuffle_audit \
  --config configs/scope_static/stage3d1_assignment_shuffle_audit.yaml
```

Stage 3D.1 keeps frozen Stage 3A visible features fixed, shuffles only Stage
3B.1 discovered assignment rows, refits/evaluates the Stage 3C generator, and
expects `categorical_population_nll` plus replay metrics to collapse toward
global-null. It writes `assignment_shuffle_metrics.json`,
`shuffled_assignment_metrics_summary.json`, `shuffle_runs.json`,
`s3c_consistency_audit.json`, `leakage_audit.json`, and
`acceptance_audit.json`.

## Function: Run Stage 3D.2 Feature-Scramble Audit

```bash
conda run -n aiqec scope-stage3d2-feature-scramble \
  --config configs/scope_static/stage3d2_feature_scramble_audit.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.feature_scramble_audit \
  --config configs/scope_static/stage3d2_feature_scramble_audit.yaml
```

Stage 3D.2 keeps the Stage 3B.1 discovered assignment matrix fixed, row-scrambles
the frozen Stage 3A visible feature matrix, refits/evaluates the Stage 3C
generator, and expects `categorical_population_nll` plus replay metrics to
collapse toward global-null. It writes `feature_scramble_metrics.json`,
`scrambled_feature_metrics_summary.json`, `feature_scramble_runs.json`,
`s3c_consistency_audit.json`, `leakage_audit.json`, and
`acceptance_audit.json`.

## Function: Run Stage 3D.3 Context-Shuffle Audit

```bash
conda run -n aiqec scope-stage3d3-context-shuffle \
  --config configs/scope_static/stage3d3_context_shuffle_audit.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.context_shuffle_audit \
  --config configs/scope_static/stage3d3_context_shuffle_audit.yaml
```

Stage 3D.3 keeps frozen Stage 3A visible features and Stage 3B.1 assignments
fixed, row-shuffles only the protocol-only `context_group` labels, rebuilds the
grouped folds, and refits/evaluates the Stage 3C generator. For the current
context-free selected B1 model, this is a split-protocol audit: shuffled
pseudo-context folds should remain meaningful, and the original grouped-context
split should not be artificially easier. It writes
`context_shuffle_metrics.json`, `context_shuffled_metrics_summary.json`,
`context_shuffle_runs.json`, `context_protocol_audit.json`,
`selected_context_usage_audit.json`, `s3c_consistency_audit.json`,
`leakage_audit.json`, and `acceptance_audit.json`.

## Function: Run Stage 3D.4 K-Stress Audit

```bash
conda run -n aiqec scope-stage3d4-k-stress \
  --config configs/scope_static/stage3d4_k_stress_audit.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.k_stress_audit \
  --config configs/scope_static/stage3d4_k_stress_audit.yaml
```

Stage 3D.4 reruns visible-only prototype discovery at fixed undercomplete,
exact, and overcomplete K settings. K values may use catalog cardinality and
Stage 3A.5 quotient count, but mechanism labels are used only after fitting for
evaluator metrics. Passing means exact/overcomplete K preserve mechanism or
quotient recovery and heldout visible replay, while undercomplete K degrades
recovery as expected. It uses the same declared operation-context feature
weighting as Stage 3B.1. It writes `k_stress_plan.json`,
`k_stress_results.json`, `k_stress_summary.json`, `model_summaries.json`,
`learned_assignments_by_k.npz`, `leakage_audit.json`, and
`acceptance_audit.json`.

## Function: Run Stage 3D.4b Overcomplete Merge/Prune Audit

```bash
conda run -n aiqec scope-stage3d4b-overcomplete-merge-prune \
  --config configs/scope_static/stage3d4b_overcomplete_merge_prune_audit.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.stage3.overcomplete_merge_prune_audit \
  --config configs/scope_static/stage3d4b_overcomplete_merge_prune_audit.yaml
```

Stage 3D.4b consumes the overcomplete assignment matrix from Stage 3D.4,
prunes inactive clusters, keeps macro clusters separate, and merges only
declared assignment microclusters into one visible-only tail-submode family.
The merge rule uses assignments and learner-visible feature summaries only;
mechanism labels are loaded after the merge map is fixed for evaluator scoring.
It writes `merge_prune_plan.json`, `overcomplete_cluster_summary.json`,
`merge_map.json`, `postmerge_metrics.json`, `postmerge_assignments.npy`,
`leakage_audit.json`, and `acceptance_audit.json`.
Use `--assignment-key fixed_oracle_count` to run the same audit as an exact-K
boundary test.

## Function: Run Active Physical-Observability Audits

Local Pauli-Lindblad observability:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.s2d9_local_pauli_lindblad_observability \
  --config configs/scope_static/s2d9_local_pauli_lindblad_observability.yaml
```

Generator invariant calibration:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.s2d10b_generator_invariant_calibration \
  --config configs/scope_static/s2d10b_generator_invariant_calibration.yaml
```

Typed gate/readout/prep invariant learner:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml
```

Calibration-only audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.qec_noise_catalog.s2d11b_m1_gate_branch_grouped_calibration_audit \
  --config configs/scope_static/s2d11b_m1_gate_branch_grouped_calibration_audit.yaml
```

These functions support probe-design and observability analysis. They are not a
replacement for canonical learner acceptance.

## Output Discipline

Promote artifact files, not terminal output. Serious runs should write metrics
JSON, compact summaries, config manifests, leakage or label-use audits, and
the relevant graph/window/probe/prototype audits.
